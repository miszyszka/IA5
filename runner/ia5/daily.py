"""Świece dzienne (D1) Yahoo — kalendarz, kontrola jakości (D-053).

D1 to druga seria tego samego źródła (Yahoo, D7): Apps Script → Firestore `candles_d1/{PARA}_{RRRR}` → kopia na Macu
`data/yahoo_d1/{PARA}.parquet` (kolumny ts, open, high, low, close; surowa, niezmieniana — D4).

Znacznik świecy = czas otwarcia (D1): Yahoo kwotuje dzień FX od północy w strefie giełdy (dla par `=X` to
Europe/London), więc ts świecy dnia d = północ d w Londynie (zimą 00:00 UTC, latem 23:00 UTC dnia poprzedniego).
Świeca dnia d jest zamknięta, gdy w Londynie zaczął się dzień d+1 (+60 s, jak D2).

Silnik i inwestorzy liczą na D1 przez `clean_d1` (D-058); skaner, `ia5 search` i las — tylko na H1.
Kontrola zgłasza, niczego nie naprawia (D5).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

D1_TZ = "Europe/London"          # strefa dnia Yahoo dla par FX (meta.exchangeTimezoneName); Apps Script zapisuje ją w status
HOLIDAYS = {(12, 25), (1, 1)}    # dni bez oczekiwanej świecy (D-028); jeśli Yahoo ją ma — zostaje w surowej kopii
COLS = ["ts", "open", "high", "low", "close"]


def local_dt(ts, tz: str = D1_TZ) -> pd.DatetimeIndex:
    return pd.to_datetime(np.asarray(ts, dtype="int64"), unit="s", utc=True).tz_convert(tz)


def day_of(ts, tz: str = D1_TZ) -> np.ndarray:
    """Dzień kalendarzowy świecy (w strefie Yahoo) jako 'RRRR-MM-DD'."""
    return np.asarray(local_dt(ts, tz).strftime("%Y-%m-%d"))


def is_expected_day(d: date) -> bool:
    return d.weekday() < 5 and (d.month, d.day) not in HOLIDAYS


def expected_day(now: int, tz: str = D1_TZ) -> str:
    """Najnowszy dzień, którego zamkniętej świecy D1 oczekujemy: ostatni dzień roboczy przed dzisiejszym (w strefie Yahoo).
    Ta sama logika jest w Apps Script (expectedDayD1_)."""
    today = datetime.fromtimestamp(now - 60, timezone.utc).astimezone(ZoneInfo(tz)).date()
    d = today - timedelta(days=1)
    while not is_expected_day(d):
        d -= timedelta(days=1)
    return d.isoformat()


def missing_days(days: list[str], until: str | None = None) -> list[str]:
    """Oczekiwane dni robocze bez świecy między pierwszą świecą a `until` (domyślnie ostatnią świecą)."""
    if not days:
        return []
    have = set(days)
    d, end = date.fromisoformat(min(days)), date.fromisoformat(until or max(days))
    out = []
    while d <= end:
        if is_expected_day(d) and d.isoformat() not in have:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def days_behind(last_day: str, exp: str) -> int:
    """Ile oczekiwanych dni roboczych po `last_day` do `exp` włącznie nie ma jeszcze świecy (0 = aktualne)."""
    d, end, n = date.fromisoformat(last_day) + timedelta(days=1), date.fromisoformat(exp), 0
    while d <= end:
        n += is_expected_day(d)
        d += timedelta(days=1)
    return n


BIG_OHLC_PIPS = 20   # D-059: naruszenie OHLC większe niż tyle pipsów = „duże” (reszta to drobny szum Yahoo, ok. 83% ≤ 3 pipsy)
RECENT_DAYS = 30     # D-059: „świeże” = z ostatnich 30 dni kalendarzowych danej pary


def d1_flags(df: pd.DataFrame, tz: str = D1_TZ, pip: float = 0.0001) -> dict:
    """Liczniki na świecach D1. Twarde błędy: cena ≤ 0, czas nie o północy, dwa wpisy na ten sam dzień.
    OHLC (high < max(O,C) albo low > min(O,C)): `ohlc` = wszystkie, `ohlc_big` = większe niż BIG_OHLC_PIPS pipsów,
    `ohlc_big_recent` = duże z ostatnich RECENT_DAYS dni, `ohlc_max_pips` = największe (D-059: Yahoo robi to stale, ok. 2%).
    Informacyjne (typowe dla starej historii Yahoo): świece w weekend/święto, płaskie (O=H=L=C), brakujące dni robocze."""
    empty = {"bars": 0, "ohlc": 0, "ohlc_big": 0, "ohlc_big_recent": 0, "ohlc_max_pips": 0.0, "price": 0, "offgrid": 0,
             "dup_days": 0, "weekend": 0, "flat": 0, "missing": 0, "missing_list": [], "first_day": None, "last_day": None}
    if df is None or df.empty:
        return empty
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    loc = local_dt(df["ts"], tz)
    days = np.asarray(loc.strftime("%Y-%m-%d"))
    midnight = (loc.hour == 0) & (loc.minute == 0) & (loc.second == 0)
    wk = np.array([not is_expected_day(date.fromisoformat(d)) for d in days])
    uniq = sorted(set(days[midnight]))
    miss = missing_days(uniq)
    with np.errstate(invalid="ignore"):
        viol = np.maximum(np.maximum(o, c) - h, lo - np.minimum(o, c)) / pip      # rozmiar naruszenia OHLC w pipsach
    is_ohlc = (h < np.maximum(o, c) - 1e-12) | (lo > np.minimum(o, c) + 1e-12)
    big = is_ohlc & (viol > BIG_OHLC_PIPS)
    last_ts = int(df["ts"].max())
    recent = np.asarray(df["ts"], dtype="int64") > last_ts - RECENT_DAYS * 86400
    return {
        "bars": int(len(df)),
        "ohlc": int(is_ohlc.sum()),
        "ohlc_big": int(big.sum()),
        "ohlc_big_recent": int((big & recent).sum()),
        "ohlc_max_pips": float(viol[is_ohlc].max()) if is_ohlc.any() else 0.0,
        "price": int((np.minimum.reduce([o, h, lo, c]) <= 0).sum()),
        "offgrid": int((~midnight).sum()),
        "dup_days": int(len(days) - len(set(days))),
        "weekend": int(wk.sum()),
        "flat": int(((o == h) & (h == lo) & (lo == c)).sum()),
        "missing": len(miss),
        "missing_list": miss[-20:],
        "first_day": str(days.min()),
        "last_day": str(days.max()),
    }


def merge(old: pd.DataFrame | None, new: pd.DataFrame, years: list[str] | None, tz: str = D1_TZ) -> pd.DataFrame:
    """Kopia lokalna + doczytane lata z Firestore. Doczytane lata zastępują stare W CAŁOŚCI (kopia = Firestore),
    pozostałe lata zostają z kopii."""
    if old is None or old.empty or years is None:
        df = new
    else:
        keep = old[~pd.Series(day_of(old["ts"], tz)).str[:4].isin(years).to_numpy()]
        df = pd.concat([keep, new])
    df = df[COLS].drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
    df["ts"] = df["ts"].astype("int64")
    return df


def years_to_read(last_ts: int, now: int, tz: str = D1_TZ) -> list[str]:
    """Lata od roku ostatniej świecy kopii (bez dziury po przerwie Maca) do bieżącego."""
    y0 = int(day_of([last_ts], tz)[0][:4])
    y1 = datetime.fromtimestamp(now, timezone.utc).astimezone(ZoneInfo(tz)).year
    return [str(y) for y in range(y0, y1 + 1)]


# ---------- warstwa czyszczenia D1 do liczenia (D-058) ----------

CLEAN_D1_VERSION = "2"   # 2: zamknięcie dnia z H1 albo z open następnego dnia (D-068)
H1_CLOSE_FROM = 20       # D-068: świeca H1 otwarta od tej godziny (Londyn) może być zamknięciem dnia
GAP_DAYS = 3        # ≥ 3 kolejne brakujące dni robocze = przerwa w danych (B12); 1–2 dni to zwykle święto, którego Yahoo nie ma
DAY = 86400


def close_ts(ts, tz: str = D1_TZ) -> np.ndarray:
    """Czas zamknięcia świecy D1 = północ NASTĘPNEGO dnia kalendarzowego w strefie Yahoo (dokładnie, z czasem letnim)."""
    loc = local_dt(ts, tz)
    nxt = (loc.tz_localize(None).normalize() + pd.Timedelta(days=1)).tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward")
    epoch = pd.Timestamp("1970-01-01", tz="UTC")
    sec = ((nxt.tz_convert("UTC") - epoch) // pd.Timedelta(seconds=1)).to_numpy()
    out = np.asarray(ts, dtype="int64") + DAY          # zapasowo +24 h (niejednoznaczna północ — nie zdarza się w Londynie)
    ok = ~pd.isna(sec)
    out[ok] = np.asarray(sec, dtype=float)[ok].astype("int64")
    return out


def h1_day_closes(h1: pd.DataFrame | None, tz: str = D1_TZ) -> pd.Series:
    """D-068: zamknięcie dnia z H1 — close ostatniej świecy H1 dnia w strefie tz, jeśli otwarta od H1_CLOSE_FROM:00
    (piątek kończy się ok. 21–22; dzień ze skróconą sesją nie ma tu zamknięcia). Indeks: ts północy dnia (jak świece D1)."""
    if h1 is None or len(h1) == 0:
        return pd.Series(dtype=float)
    x = h1[["ts", "close"]].sort_values("ts").drop_duplicates("ts", keep="last")
    x = x[np.isfinite(x["close"].to_numpy(float)) & (x["close"].to_numpy(float) > 0)]
    loc = local_dt(x["ts"], tz)
    day = loc.tz_localize(None).normalize()
    last = pd.DataFrame({"day": day, "hour": loc.hour, "close": x["close"].to_numpy(float)}).groupby("day").last()
    last = last[last["hour"] >= H1_CLOSE_FROM]
    mid = pd.DatetimeIndex(last.index).tz_localize(tz, ambiguous="NaT", nonexistent="shift_forward")
    ok = ~mid.isna()
    sec = ((mid[ok].tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)).to_numpy("int64")
    return pd.Series(last["close"].to_numpy()[ok], index=sec)


def fix_close(out: pd.DataFrame, days, h1: pd.DataFrame | None, tz: str) -> dict:
    """D-068: Yahoo od ok. 2011 podaje dla par FX close ≈ open tego samego dnia. Prawdziwe zamknięcie dnia t to
    (2) close ostatniej świecy H1 dnia, gdy H1 jest, inaczej (1) open następnego oczekiwanego dnia handlu (także piątek →
    poniedziałek), gdy ten dzień jest w danych; w pozostałych przypadkach zostaje (0) close z Yahoo. Kolumna close_src mówi,
    skąd jest zamknięcie; high/low są rozszerzane o nowe zamknięcie. Zmienia `out` w miejscu, zwraca liczniki."""
    n = len(out)
    c = out["close"].to_numpy(float).copy()
    src = np.zeros(n, np.int8)
    o = out["open"].to_numpy(float)
    for i in range(n - 1):
        d = date.fromisoformat(days[i]) + timedelta(days=1)
        while not is_expected_day(d):
            d += timedelta(days=1)
        if days[i + 1] == d.isoformat():
            c[i], src[i] = o[i + 1], 1
    hc = h1_day_closes(h1, tz)
    if len(hc):
        v = hc.reindex(out["ts"].to_numpy()).to_numpy()
        m = ~np.isnan(v)
        c[m], src[m] = v[m], 2
    out["close"] = c
    out["high"] = np.maximum(out["high"].to_numpy(float), c)
    out["low"] = np.minimum(out["low"].to_numpy(float), c)
    out["close_src"] = src
    return {"close_yahoo": int((src == 0).sum()), "close_next_open": int((src == 1).sum()), "close_h1": int((src == 2).sum())}


def clean_d1(raw: pd.DataFrame, tz: str = D1_TZ, h1: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    """Świece D1 do liczenia (D8 dla D1): odrzucone = łamiące D5 (OHLC, cena ≤ 0, czas nie o północy, dwa wpisy na dzień);
    poza sesją = weekend/święto (stara historia Yahoo) i świece płaskie O=H=L=C (brak notowań, powtórzona cena).
    Brakujące dni robocze: < GAP_DAYS z rzędu → nic (dzień bez świecy jak weekend); ≥ GAP_DAYS → gap_before = liczba dni
    (B12: transakcje przez przerwę anulowane). Bez uzupełniania (filled zawsze False) — doba to za dużo, żeby interpolować.
    Zamknięcie dnia (D-068, wersja 2): z H1 albo z open następnego dnia — patrz fix_close; `h1` = surowe świece H1 pary.
    Kolumny jak w h1_ready: ts, open, high, low, close, filled, gap_before + close_ts (koniec dnia w UTC) + close_src."""
    info = {"version": CLEAN_D1_VERSION, "tz": tz, "bars": 0, "rejected": 0, "rejected_ts": [], "off_session": 0, "flat": 0,
            "filled": 0, "gaps": [], "gap_hours": 0, "gap_days": 0, "missing_days": 0, "closed_hours": 0}
    cols = COLS + ["filled", "gap_before", "close_ts", "close_src"]
    if raw is None or raw.empty:
        return pd.DataFrame(columns=cols), info
    df = raw[COLS].sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    loc = local_dt(df["ts"], tz)
    with np.errstate(invalid="ignore"):
        bad = ~np.isfinite(np.c_[o, h, lo, c]).all(axis=1)
        bad |= np.minimum.reduce([o, h, lo, c]) <= 0
        bad |= (h < np.maximum(o, c) - 1e-12) | (lo > np.minimum(o, c) + 1e-12)
    offgrid = ~np.asarray((loc.hour == 0) & (loc.minute == 0) & (loc.second == 0))
    days = np.asarray(loc.strftime("%Y-%m-%d"))
    dup = pd.Series(np.where(offgrid, "", days)).duplicated(keep="last").to_numpy() & ~offgrid   # dwa wpisy o północy tego samego dnia
    bad |= offgrid | dup
    if bad.any():
        info["rejected"] = int(bad.sum())
        info["rejected_ts"] = [int(t) for t in df["ts"].to_numpy()[bad][:50]]
        df, days = df[~bad].reset_index(drop=True), days[~bad]
        o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    wk = np.array([not is_expected_day(date.fromisoformat(d)) for d in days]) if len(days) else np.zeros(0, bool)
    flat = (o == h) & (h == lo) & (lo == c)
    off = wk | flat
    if off.any():
        info["off_session"], info["flat"] = int(wk.sum()), int(flat.sum())
        df, days = df[~off].reset_index(drop=True), days[~off]
    if df.empty:
        return pd.DataFrame(columns=cols), info
    # przerwy: serie kolejnych brakujących dni roboczych między dwiema świecami
    have = {d: i for i, d in enumerate(days)}
    gap_before = np.zeros(len(df), np.int64)
    d, end, run, missing = date.fromisoformat(days[0]), date.fromisoformat(days[-1]), 0, 0
    while d <= end:
        key = d.isoformat()
        if key in have:
            if run >= GAP_DAYS:
                i = have[key]
                gap_before[i] = run
                info["gaps"].append([int(df["ts"].iloc[i - 1]), int(df["ts"].iloc[i]), run])
                info["gap_days"] += run
            run = 0
        elif is_expected_day(d):
            run += 1
            missing += 1
        d += timedelta(days=1)
    out = df.copy()
    out["ts"] = out["ts"].astype("int64")
    out["filled"] = False
    out["gap_before"] = gap_before
    out["close_ts"] = close_ts(out["ts"].to_numpy(), tz)
    info.update(fix_close(out, days, h1, tz))   # D-068: zamknięcie dnia (po wykryciu przerw — te zależą tylko od dat)
    info.update({"bars": int(len(out)), "missing_days": int(missing), "gap_hours": int(info["gap_days"] * 24),
                 "from": int(out["ts"].iloc[0]), "to": int(out["ts"].iloc[-1])})
    return out, info
