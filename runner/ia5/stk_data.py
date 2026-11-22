"""Stocks (D-071) — świece dzienne spółek: warstwa czyszczenia, panel dzienny i tygodniowy rozkład decyzji.

Surowa kopia (data/yahoo_stk/{TICKER}.parquet): ts (północ dnia sesji w Nowym Jorku), open, high, low, close, div, split —
tak jak zapisał Apps Script (ceny Yahoo po splitach, dywidendy w dniu bez prawa). Warstwa czyszczenia (CLEAN_STK_VERSION):
- świeca z ceną ≤ 0 albo zduplikowanym dniem odrzucona; weekend odrzucony;
- wyskok: |zmiana| > 50% w jeden dzień i powrót ≥ 80% następnego dnia → dzień zastąpiony zamknięciem poprzedniego (oznaczony);
- split, którego Yahoo nie przeliczył wstecz (otwarcie dnia splitu ≈ poprzednie zamknięcie ÷ mnożnik) → ceny i dywidendy
  sprzed splitu przeskalowane (liczone w opisie);
- dywidenda z dnia bez świecy → do najbliższego następnego dnia sesji.
Surowa kopia zostaje nietknięta (D4).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .stk_config import CLEAN_STK_VERSION, DATA_FROM, MIN_HISTORY_DAYS, TZ

RAW_COLS = ["ts", "open", "high", "low", "close", "div", "split"]
COLS = ["ts", "day", "open", "high", "low", "close", "div", "spike"]
SPIKE_MOVE = 0.5
SPIKE_REVERT = 0.8
SPLIT_TOL = 0.15


def day_str(ts, tz: str = TZ) -> np.ndarray:
    return pd.to_datetime(np.asarray(ts, "int64"), unit="s", utc=True).tz_convert(tz).strftime("%Y-%m-%d").to_numpy()


def midnight_ts(days, tz: str = TZ) -> np.ndarray:
    """Północ dnia 'RRRR-MM-DD' w strefie tz jako epoch (s)."""
    d = pd.DatetimeIndex(pd.to_datetime(pd.Series(np.asarray(days, dtype=str)))).tz_localize(tz)
    return d.tz_convert("UTC").as_unit("s").asi8.astype("int64")


def empty_raw() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="int64" if c == "ts" else "float64") for c in RAW_COLS})


def clean_stk(raw: pd.DataFrame, tz: str = TZ) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    for c in RAW_COLS:
        if c not in df:
            df[c] = 0.0 if c == "div" else (1.0 if c == "split" else np.nan)
    df = df.sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    df["day"] = day_str(df["ts"], tz)   # Yahoo stempluje spółki otwarciem sesji (09:30); starsze wpisy bywają o północy — ten sam dzień
    wd = pd.to_datetime(df["day"]).dt.weekday.to_numpy()
    div_all = df[["ts", "day", "div"]][df["div"].fillna(0) > 0].copy()
    split_all = df[["ts", "day", "split"]][(df["split"].fillna(1) > 0) & (df["split"].fillna(1) != 1)].copy()
    px = df[["open", "high", "low", "close"]].to_numpy(float)
    bad = ~np.all(np.isfinite(px) & (px > 0), axis=1)
    off = wd >= 5
    dup = df["day"].duplicated(keep="last").to_numpy()
    keep = ~(bad | off | dup)
    out = df.loc[keep, ["ts", "day", "open", "high", "low", "close"]].reset_index(drop=True)
    out["ts"] = midnight_ts(out["day"], tz) if len(out) else out["ts"]   # znacznik do liczenia = północ dnia sesji w NY
    info = {"version": CLEAN_STK_VERSION, "tz": tz, "raw_bars": int(len(df)), "rejected": int(bad.sum()), "off_session": int(off.sum()),
            "duplicates": int(dup.sum()), "spikes": 0, "rescaled": [], "dividends": 0, "splits": int(len(split_all))}
    # dywidendy na dzień sesji (ten sam albo najbliższy następny)
    dv = np.zeros(len(out))
    if len(div_all) and len(out):
        pos = np.searchsorted(out["day"].to_numpy(), div_all["day"].to_numpy(), side="left")
        ok = pos < len(out)
        np.add.at(dv, pos[ok], div_all["div"].to_numpy(float)[ok])
        info["dividends"] = int(ok.sum())
    out["div"] = dv
    # split nieprzeliczony wstecz → przeskalowanie wszystkiego przed dniem splitu
    for _, s in split_all.iterrows():
        r = float(s["split"])
        i = int(np.searchsorted(out["day"].to_numpy(), s["day"], side="left"))
        if i <= 0 or i >= len(out):
            continue
        jump = out["open"].iloc[i] / out["close"].iloc[i - 1]
        if abs(jump * r - 1) < SPLIT_TOL and abs(r - 1) > 2 * SPLIT_TOL:
            for c in ("open", "high", "low", "close", "div"):
                out.loc[: i - 1, c] = out.loc[: i - 1, c] / r
            info["rescaled"].append([str(s["day"]), r])
    # wyskok jednego dnia z powrotem
    c = out["close"].to_numpy(float)
    spike = np.zeros(len(out), bool)
    if len(c) >= 3:
        r1 = c[1:-1] / c[:-2] - 1
        r2 = c[2:] / c[1:-1] - 1
        hit = (np.abs(r1) > SPIKE_MOVE) & (np.sign(r1) != np.sign(r2)) & (np.abs(np.log1p(r2)) >= SPIKE_REVERT * np.abs(np.log1p(r1)))
        idx = np.flatnonzero(hit) + 1
        for i in idx:
            p = out.at[i - 1, "close"]
            out.loc[i, ["open", "high", "low", "close"]] = [p, p, p, p]
            spike[i] = True
    out["spike"] = spike
    info["spikes"] = int(spike.sum())
    info["bars"] = int(len(out))
    if len(out):
        info["first_day"], info["last_day"] = str(out["day"].iloc[0]), str(out["day"].iloc[-1])
    out["ts"] = out["ts"].astype("int64")
    return out[COLS], info


def build_stk(raw_map: dict[str, pd.DataFrame], out_dir: Path, tz: str = TZ, log=print) -> dict:
    """data/stk_ready/{TICKER}.parquet + .json; przebudowa tylko, gdy zmieniły się surowe świece albo wersja czyszczenia.
    Spółki spoza raw_map znikają z katalogu (to kopia pochodna, nie dane)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    names = set(raw_map)
    for f in list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.json")):
        if f.stem not in names:
            f.unlink()
    out = {}
    for t, raw in sorted(raw_map.items()):
        jf, pf = out_dir / f"{t}.json", out_dir / f"{t}.parquet"
        h = hashlib.sha256(f"stk:{CLEAN_STK_VERSION}:{tz}".encode())
        if raw is not None and len(raw):
            r = raw.reindex(columns=RAW_COLS)
            h.update(pd.util.hash_pandas_object(r.reset_index(drop=True), index=False).values.tobytes())
        sig = h.hexdigest()[:16]
        try:
            old = json.loads(jf.read_text())
        except (FileNotFoundError, ValueError):
            old = {}
        if old.get("sig") == sig and pf.exists():
            out[t] = {**old, "rebuilt": False}
            continue
        if raw is None or not len(raw):
            pf.unlink(missing_ok=True)
            continue
        df, info = clean_stk(raw, tz)
        tmp = pf.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(pf)
        info = {**info, "source": "yahoo", "series": "stk", "sig": sig, "at": int(time.time())}
        jf.write_text(json.dumps(info))
        out[t] = {**info, "rebuilt": True}
        log(f"  Spółka {t} do liczenia: {info['bars']:,} dni {info.get('first_day', '')} – {info.get('last_day', '')} · "
            f"dywidendy {info['dividends']} · splity {info['splits']} (przeliczone tu {len(info['rescaled'])}) · wyskoki {info['spikes']}")
    return out


def load_stk(folder: Path, names=None) -> dict[str, pd.DataFrame]:
    out = {}
    for pf in sorted(Path(folder).glob("*.parquet")):
        if names is not None and pf.stem not in names:
            continue
        df = pd.read_parquet(pf)
        try:
            df.attrs["info"] = json.loads(pf.with_suffix(".json").read_text())
        except (FileNotFoundError, ValueError):
            df.attrs["info"] = {}
        out[pf.stem] = df
    return out


# ---------- panel dzienny ----------

class Panel:
    """Wspólny kalendarz dni sesji wszystkich spółek. Tablice (dni × spółki): open, close (NaN = brak świecy), div,
    tr (indeks całkowitego zwrotu: zamknięcie + dywidenda, ffill w życiu spółki), has (świeca jest), age (liczba świec do dnia)."""

    def __init__(self, ready: dict[str, pd.DataFrame], tickers: list[str]):
        self.tickers = list(tickers)
        frames = {t: f for t in self.tickers if t in ready and len(f := ready[t][ready[t]["day"] >= DATA_FROM])}   # tylko od 2010
        days = sorted(set().union(*[set(f["day"]) for f in frames.values()])) if frames else []
        self.days = np.array(days, dtype="U10")
        self.ts = np.zeros(len(days), "int64")
        n, m = len(days), len(self.tickers)
        self.open = np.full((n, m), np.nan)
        self.close = np.full((n, m), np.nan)
        self.div = np.zeros((n, m))
        pos = {d: i for i, d in enumerate(days)}
        for j, t in enumerate(self.tickers):
            f = frames.get(t)
            if f is None:
                continue
            ii = np.array([pos[d] for d in f["day"]], dtype=int)
            self.open[ii, j] = f["open"].to_numpy(float)
            self.close[ii, j] = f["close"].to_numpy(float)
            self.div[ii, j] = f["div"].to_numpy(float)
            self.ts[ii] = f["ts"].to_numpy("int64")
        self.has = np.isfinite(self.close)
        self.age = np.cumsum(self.has, axis=0)
        cf = pd.DataFrame(self.close).ffill().to_numpy()
        prev = np.vstack([np.full((1, m), np.nan), cf[:-1]])
        g = np.where(self.has & np.isfinite(prev), (self.close + self.div) / prev, 1.0)
        g = np.where(np.isfinite(g) & (g > 0), g, 1.0)
        tr = np.cumprod(g, axis=0)
        self.tr = np.where(self.age > 0, tr, np.nan)
        self.cfill = cf
        self.weekday = pd.to_datetime(pd.Series(self.days)).dt.weekday.to_numpy() if n else np.zeros(0, int)
        iso = pd.to_datetime(pd.Series(self.days)).dt.isocalendar() if n else None
        self.week = (iso["year"].to_numpy() * 100 + iso["week"].to_numpy()) if n else np.zeros(0, int)


def schedule(p: Panel) -> tuple[np.ndarray, np.ndarray]:
    """Tygodnie decyzji: wykonanie = pierwszy dzień sesji tygodnia od wtorku (wtorek; w święto środa…), ocena = poprzedni
    dzień sesji. Zwraca (indeksy dni oceny, indeksy dni wykonania)."""
    sig, exe = [], []
    seen = set()
    for i in range(1, len(p.days)):
        w = int(p.week[i])
        if w in seen or p.weekday[i] < 1:
            continue
        seen.add(w)
        sig.append(i - 1)
        exe.append(i)
    return np.array(sig, int), np.array(exe, int)


def period_growth(p: Panel, exe: np.ndarray) -> np.ndarray:
    """Mnożnik wartości każdej spółki od otwarcia dnia wykonania k do otwarcia dnia k+1 (z dywidendami z dni (k, k+1]).
    Ostatni wiersz = NaN (okres trwa). Brak ceny → 1 (wartość bez zmian)."""
    o = np.where(np.isfinite(p.open), p.open, p.cfill)
    cdiv = np.cumsum(p.div, axis=0)
    out = np.full((len(exe), len(p.tickers)), np.nan)
    for k in range(len(exe) - 1):
        a, b = exe[k], exe[k + 1]
        d = cdiv[b] - cdiv[a]
        g = (o[b] + d) / o[a]
        out[k] = np.where(np.isfinite(g) & (g > 0), g, 1.0)
    return out


def eligible(p: Panel, sig: np.ndarray) -> np.ndarray:
    """Spółka gra w tygodniu, gdy w dniu oceny ma ≥ MIN_HISTORY_DAYS świec i notowanie z ostatnich 10 dni sesji."""
    recent = np.zeros_like(p.has)
    run = np.full(len(p.tickers), -10**9)
    for i in range(len(p.days)):
        run = np.where(p.has[i], i, run)
        recent[i] = (i - run) <= 10
    return (p.age[sig] >= MIN_HISTORY_DAYS) & recent[sig]


def tradeable(p: Panel, exe: np.ndarray) -> np.ndarray:
    return p.has[exe]


# ---------- kalendarz giełdy USA (tylko do oczekiwań „który dzień powinien już być”; dane i tak rozstrzygają) ----------

def _easter(y: int):
    from datetime import date

    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month = (h + m - 7 * n + 114) // 31
    return date(y, month, (h + m - 7 * n + 114) % 31 + 1)


def nyse_holidays(y: int) -> set:
    from datetime import date, timedelta

    def nth(month, wd, k):          # k-ty dzień tygodnia wd w miesiącu (k = -1: ostatni)
        if k > 0:
            d = date(y, month, 1)
            d += timedelta(days=(wd - d.weekday()) % 7)
            return d + timedelta(weeks=k - 1)
        d = date(y + (month == 12), month % 12 + 1, 1) - timedelta(days=1)
        return d - timedelta(days=(d.weekday() - wd) % 7)

    def obs(d):                      # sobota → piątek, niedziela → poniedziałek
        return d - timedelta(days=1) if d.weekday() == 5 else d + timedelta(days=1) if d.weekday() == 6 else d

    out = {nth(1, 0, 3), nth(2, 0, 3), _easter(y) - timedelta(days=2), nth(5, 0, -1), obs(date(y, 7, 4)), nth(9, 0, 1),
           nth(11, 3, 4), obs(date(y, 12, 25))}
    ny = date(y, 1, 1)
    if ny.weekday() != 5:
        out.add(obs(ny))
    if y >= 2022:
        out.add(obs(date(y, 6, 19)))
    return out


def is_session_day(d) -> bool:
    return d.weekday() < 5 and d not in nyse_holidays(d.year)


def last_session_before(d):
    """Ostatni dzień sesji przed dniem d (datetime.date)."""
    from datetime import timedelta

    x = d - timedelta(days=1)
    while not is_session_day(x):
        x -= timedelta(days=1)
    return x
