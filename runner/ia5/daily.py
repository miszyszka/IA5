"""Świece dzienne (D1) Yahoo — kalendarz, kontrola jakości (D-053).

D1 to druga seria tego samego źródła (Yahoo, D7): Apps Script → Firestore `candles_d1/{PARA}_{RRRR}` → kopia na Macu
`data/yahoo_d1/{PARA}.parquet` (kolumny ts, open, high, low, close; surowa, niezmieniana — D4).

Znacznik świecy = czas otwarcia (D1): Yahoo kwotuje dzień FX od północy w strefie giełdy (dla par `=X` to
Europe/London), więc ts świecy dnia d = północ d w Londynie (zimą 00:00 UTC, latem 23:00 UTC dnia poprzedniego).
Świeca dnia d jest zamknięta, gdy w Londynie zaczął się dzień d+1 (+60 s, jak D2).

Silnik, skaner, las i inwestorzy nadal liczą wyłącznie na H1 — D1 jest na razie tylko przechowywana, sprawdzana
i publikowana (D-053). Zgłasza, niczego nie naprawia (D5).
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


def d1_flags(df: pd.DataFrame, tz: str = D1_TZ) -> dict:
    """Liczniki na świecach D1. Twarde błędy: ohlc, cena ≤ 0, czas nie o północy, dwa wpisy na ten sam dzień.
    Informacyjne (typowe dla starej historii Yahoo): świece w weekend/święto, płaskie (O=H=L=C), brakujące dni robocze."""
    empty = {"bars": 0, "ohlc": 0, "price": 0, "offgrid": 0, "dup_days": 0, "weekend": 0, "flat": 0,
             "missing": 0, "missing_list": [], "first_day": None, "last_day": None}
    if df is None or df.empty:
        return empty
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    loc = local_dt(df["ts"], tz)
    days = np.asarray(loc.strftime("%Y-%m-%d"))
    midnight = (loc.hour == 0) & (loc.minute == 0) & (loc.second == 0)
    wk = np.array([not is_expected_day(date.fromisoformat(d)) for d in days])
    uniq = sorted(set(days[midnight]))
    miss = missing_days(uniq)
    return {
        "bars": int(len(df)),
        "ohlc": int(((h < np.maximum(o, c) - 1e-12) | (lo > np.minimum(o, c) + 1e-12)).sum()),
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
