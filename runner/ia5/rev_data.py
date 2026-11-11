"""REV (D-063) — kursy walut do PLN: warstwa czyszczenia (tylko zamknięcia, R0) i serie decyzji.

Surowa kopia `data/yahoo_pln/{WALUTA}.parquet` (ts, open, high, low, close; ts = północ w strefie Yahoo, D7a) zostaje
nietknięta (D4). Do liczenia `clean_pln` buduje serię zamknięć:
  1. tylko dni robocze (pn–pt bez 25.12 i 1.01);
  2. zamknięcie ≤ 0 albo nieskończone → odrzucone; zły OHLC nie odrzuca świecy (REV nie używa high/low);
  3. zamknięcie równe poprzedniemu → brak notowania (Yahoo powtarza starą cenę);
  4. zmiana skali o 10^k (k = ±1, ±2, ±2%), która się utrzymuje → historia przed nią przeskalowana (D-060: naprawa);
  5. `big` = ruch > SPIKE_SIGMA · σ względem poprzedniego zamknięcia bez wyskoku (σ = 1,4826 · mediana |zwrotów| z 60 dni) —
     zależy tylko od przeszłości, więc działa tak samo w historii i na żywo (bezpiecznik dnia decyzji);
     `spike` = `big` cofnięty następnego dnia w ≥ 80% (wiadomo dopiero dzień później).
Uwaga: punkt 4 korzysta z dnia po skoku, ale tylko mnoży całą wcześniejszą historię przez stałą — oceny (logarytmy,
różnice) i wagi się nie zmieniają; skok w dniu decyzji i tak łapie `big`.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from .daily import D1_TZ, close_ts, day_of, is_expected_day
from .rev_config import (
    BASE,
    CLEAN_PLN_VERSION,
    DECISION_HOUR,
    DECISION_TZ,
    DECISION_WEEKDAY,
    MAX_STALE_WD,
    SCALE_TOL,
    SPIKE_MAD_DAYS,
    SPIKE_REVERT,
    SPIKE_SIGMA,
)

COLS = ["ts", "close", "close_ts", "day", "spike", "big"]
_HOLI = np.array([f"{y}-{md}" for y in range(1970, 2101) for md in ("01-01", "12-25")], dtype="datetime64[D]")
_ORIGIN = np.datetime64("1970-01-01", "D")
MIN_SIGMA_N = 20


def _wd_ord(days) -> np.ndarray:
    """Numer dnia roboczego (pn–pt bez 25.12 i 1.01) od 1970 — różnica dwóch numerów = liczba dni roboczych między nimi."""
    d = np.asarray(days, dtype="datetime64[D]")
    return np.busday_count(_ORIGIN, d, holidays=_HOLI)


def _warsaw_day(ts) -> np.ndarray:
    return np.asarray(pd.to_datetime(np.asarray(ts, "int64"), unit="s", utc=True).tz_convert(DECISION_TZ)
                      .strftime("%Y-%m-%d"), dtype="datetime64[D]")


def stale_wd(price_day, decision) -> np.ndarray | int:
    """1 + liczba dni roboczych ściśle między dniem ceny a dniem decyzji (poniedziałek przed wtorkiem → 1, poprzedni wtorek → 5)."""
    pdays = np.asarray(price_day, dtype="datetime64[D]")
    ddays = _warsaw_day(np.atleast_1d(decision))
    out = 1 + (_wd_ord(ddays) - _wd_ord(pdays + np.timedelta64(1, "D")))
    out = np.maximum(out, 0)
    return int(out[0]) if np.ndim(price_day) == 0 and np.ndim(decision) == 0 else out


def decision_times(from_ts: int, to_ts: int) -> np.ndarray:
    """Wszystkie wtorki 08:00 Europe/Warsaw (R2) w [from_ts, to_ts], jako epoch w sekundach."""
    a = pd.Timestamp(int(from_ts), unit="s", tz="UTC").tz_convert(DECISION_TZ).normalize().tz_localize(None)
    b = pd.Timestamp(int(to_ts), unit="s", tz="UTC").tz_convert(DECISION_TZ).normalize().tz_localize(None)
    d = pd.date_range(a - pd.Timedelta(days=1), b + pd.Timedelta(days=1), freq="D")
    d = d[d.weekday == DECISION_WEEKDAY] + pd.Timedelta(hours=DECISION_HOUR)
    ts = (d.tz_localize(DECISION_TZ).tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
    ts = np.asarray(ts, dtype="int64")
    return ts[(ts >= from_ts) & (ts <= to_ts)]


def next_decision(ts: int) -> int:
    """Najbliższy wtorek 08:00 czasu polskiego ≥ ts."""
    return int(decision_times(int(ts), int(ts) + 8 * 86400)[0])


def clean_pln(raw: pd.DataFrame | None, tz: str = D1_TZ) -> tuple[pd.DataFrame, dict]:
    info = {"version": CLEAN_PLN_VERSION, "tz": tz, "bars": 0, "rejected": 0, "offday": 0, "repeated": 0, "spikes": 0,
            "big": 0, "rescaled": []}
    if raw is None or raw.empty:
        return pd.DataFrame(columns=COLS), info
    df = raw[["ts", "close"]].sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    days = day_of(df["ts"].to_numpy(), tz)
    wk = np.array([is_expected_day(date.fromisoformat(str(d))) for d in days])
    info["offday"] = int((~wk).sum())
    df, days = df[wk].reset_index(drop=True), days[wk]
    c = df["close"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        ok = np.isfinite(c) & (c > 0)
    info["rejected"] = int((~ok).sum())
    df, days, c = df[ok].reset_index(drop=True), days[ok], c[ok]
    if len(c):
        rep = np.r_[False, c[1:] == c[:-1]]
        info["repeated"] = int(rep.sum())
        df, days, c = df[~rep].reset_index(drop=True), days[~rep], c[~rep]
    c = c.copy()
    tol = np.log1p(SCALE_TOL)
    for i in range(1, len(c) - 1):          # zmiana skali, która się utrzymuje następnego dnia
        q = np.log(c[i] / c[i - 1])
        for k in (1, -1, 2, -2):
            if abs(q - k * np.log(10)) < tol and abs(np.log(c[i + 1] / c[i])) < 0.5 * np.log(10):
                c[:i] *= 10.0 ** k
                info["rescaled"].append([int(df["ts"].iloc[i]), float(10.0 ** k)])
                break
    n = len(c)
    big = np.zeros(n, bool)
    spike = np.zeros(n, bool)
    r = np.full(n, np.nan)
    window: list[float] = []
    prev = 0
    for i in range(1, n):
        j = i - 1                            # najpierw rozstrzygamy, czy poprzedni dzień był wyskokiem (wiadomo dopiero teraz)
        if big[j]:
            back = np.log(c[i] / c[j])
            spike[j] = np.sign(back) != np.sign(r[j]) and abs(back) >= SPIKE_REVERT * abs(r[j])
        if j > 0 and not spike[j] and np.isfinite(r[j]):
            window.append(abs(r[j]))
        if not spike[j]:
            prev = j
        r[i] = np.log(c[i] / c[prev])
        w = window[-SPIKE_MAD_DAYS:]
        if len(w) >= MIN_SIGMA_N:
            sigma = 1.4826 * float(np.median(w))
            big[i] = sigma > 0 and abs(r[i]) > SPIKE_SIGMA * sigma
    out = pd.DataFrame({"ts": df["ts"].to_numpy("int64"), "close": c, "close_ts": close_ts(df["ts"].to_numpy("int64"), tz),
                        "day": [str(d) for d in days], "spike": spike, "big": big})
    info.update({"bars": int(n), "spikes": int(spike.sum()), "big": int(big.sum())})
    if n:
        info.update({"from": int(out["ts"].iloc[0]), "to": int(out["ts"].iloc[-1]), "first_day": out["day"].iloc[0],
                     "last_day": out["day"].iloc[-1]})
    return out, info


def weekly_panel(ready: dict[str, pd.DataFrame], baskets: list[str], times: np.ndarray,
                 exec_lag_days: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ceny decyzji: dla każdego wtorku t zamknięcie ostatniej świecy z close_ts ≤ t (exec_lag_days=1: następnej świecy —
    test opóźnienia). NaN, gdy cena starsza niż MAX_STALE_WD dni roboczych albo świeca ma `big` (bezpiecznik R0).
    Zwraca (prices, price_ts); PLN = 1."""
    times = np.asarray(times, dtype="int64")
    prices = pd.DataFrame(np.nan, index=times, columns=list(baskets))
    pts = pd.DataFrame(np.nan, index=times, columns=list(baskets))
    for b in baskets:
        if b == BASE:
            prices[b] = 1.0
            pts[b] = times.astype(float)
            continue
        df = ready.get(b)
        if df is None or df.empty:
            continue
        cts = df["close_ts"].to_numpy("int64")
        idx = np.searchsorted(cts, times, side="right") - 1 + int(exec_lag_days)
        ok = (idx >= 0) & (idx < len(df))
        ii = np.clip(idx, 0, len(df) - 1)
        day = np.asarray(df["day"].to_numpy(), dtype="datetime64[D]")[ii]
        st = np.atleast_1d(stale_wd(day, times))
        ok &= st <= MAX_STALE_WD + int(exec_lag_days)
        ok &= ~df["big"].to_numpy(bool)[ii]
        prices[b] = np.where(ok, df["close"].to_numpy(float)[ii], np.nan)
        pts[b] = np.where(ok, df["ts"].to_numpy("int64")[ii].astype(float), np.nan)
    return prices, pts


def daily_panel(ready: dict[str, pd.DataFrame], baskets: list[str], from_ts: int | None = None,
                to_ts: int | None = None) -> pd.DataFrame:
    """Wycena dzień po dniu: indeks = close_ts dni roboczych (suma po walutach). Świeca `big` → wartość z dnia poprzedniego;
    brak świecy → ostatnia wartość, gdy nie starsza niż MAX_STALE_WD dni roboczych; PLN = 1."""
    frames = {b: ready[b] for b in baskets if b != BASE and ready.get(b) is not None and len(ready[b])}
    if not frames:
        return pd.DataFrame(columns=list(baskets), dtype=float)
    idx = np.unique(np.concatenate([f["close_ts"].to_numpy("int64") for f in frames.values()]))
    if from_ts is not None:
        idx = idx[idx >= from_ts]
    if to_ts is not None:
        idx = idx[idx <= to_ts]
    target_day = np.asarray(pd.to_datetime(idx - 1, unit="s", utc=True).tz_convert(D1_TZ).strftime("%Y-%m-%d"),
                            dtype="datetime64[D]")
    out = pd.DataFrame(index=idx, columns=list(baskets), dtype=float)
    for b in baskets:
        if b == BASE:
            out[b] = 1.0
            continue
        f = frames.get(b)
        if f is None:
            continue
        good = f[~f["big"].to_numpy(bool)]
        cts = good["close_ts"].to_numpy("int64")
        pos = np.searchsorted(cts, idx, side="right") - 1
        ok = pos >= 0
        pp = np.clip(pos, 0, max(len(good) - 1, 0))
        src_day = np.asarray(good["day"].to_numpy(), dtype="datetime64[D]")[pp] if len(good) else target_day
        lag = _wd_ord(target_day) - _wd_ord(src_day)
        ok &= lag <= MAX_STALE_WD
        out[b] = np.where(ok, good["close"].to_numpy(float)[pp] if len(good) else np.nan, np.nan)
    return out
