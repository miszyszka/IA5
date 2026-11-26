"""D-075: świece tygodniowe (TIMEFRAME = "W1") i wykonanie sygnału dziennego na świecach godzinowych (EXECUTE = "H1").

W1 — budowane w locie z data/d1_ready (te same dane, ta sama warstwa czyszczenia, D-058/D-068):
  tydzień = poniedziałek–piątek wg dnia w Londynie; ts = otwarcie pierwszego dnia, close_ts = zamknięcie ostatniego,
  open/close = pierwszy/ostatni dzień, high/low = max/min; gap_before = przerwa w danych przed którymkolwiek dniem
  tygodnia albo brak całego tygodnia (B12 — transakcja przez nią anulowana). Sygnał na zamknięciu tygodnia (piątek),
  wejście na open następnego (poniedziałek, B1).

EXECUTE = "H1" (tylko przy TIMEFRAME = "D1"):
  sygnał liczony na zamknięciu dnia d (D1, cała historia), wejście na open pierwszej świecy H1 dnia handlu po d,
  która otwiera się o ENTRY_HOUR czasu polskiego (domyślnie 8:00 — po rolowaniu, gdy spready są już wąskie);
  wyjścia (EXITS, `bars` z levels()) liczone na świecach H1. Liczenie obejmuje więc tylko okres świec H1 (~2 lata).
  Bez look-ahead: świeca wejścia otwiera się po zamknięciu dnia sygnału (ts ≥ close_ts).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import TRADING_TZ

D1_TZ = "Europe/London"
MAX_WAIT_H = 4 * 24   # najdalej tyle godzin od zamknięcia dnia sygnału szukamy świecy wejścia (weekend + święto)


def to_weekly(d: pd.DataFrame) -> pd.DataFrame:
    """Świece dzienne (format d1_ready: ts, open, high, low, close, close_ts, gap_before…) → tygodniowe."""
    if d.empty:
        return d.copy()
    d = d.sort_values("ts").reset_index(drop=True)
    day = pd.to_datetime(d["ts"].to_numpy(np.int64) + 12 * 3600, unit="s", utc=True).tz_convert(D1_TZ).normalize()
    week = (day - pd.to_timedelta(day.dayofweek, unit="D")).tz_localize(None)
    g = d.groupby(week.to_numpy(), sort=True)
    out = pd.DataFrame({
        "ts": g["ts"].first(), "open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
        "close": g["close"].last(),
        "close_ts": g["close_ts"].last() if "close_ts" in d else g["ts"].last() + 86400,
    })
    gap = g["gap_before"].max() if "gap_before" in d else pd.Series(0, index=out.index)
    wk = pd.to_datetime(out.index)
    missing = np.r_[0, (np.diff(wk.to_numpy()).astype("timedelta64[D]").astype(int) > 7).astype(int)]
    out["gap_before"] = ((gap.to_numpy() > 0) | (missing > 0)).astype(np.int64)
    return out.reset_index(drop=True).astype({"ts": np.int64, "close_ts": np.int64})


def load(tf: str, h1_dir: Path, d1_dir: Path | None) -> dict[str, pd.DataFrame]:
    """Dane do liczenia dla interwału strategii: H1 (h1_ready), D1 (d1_ready) albo W1 (z d1_ready)."""
    folder = Path(h1_dir) if tf == "H1" else Path(d1_dir)
    out = {f.stem: pd.read_parquet(f) for f in sorted(folder.glob("*.parquet"))}
    if tf == "W1":
        out = {p: to_weekly(df) for p, df in out.items()}
    return out


def entry_bar_index(h1_ts: np.ndarray, close_ts: np.ndarray, hour: int) -> np.ndarray:
    """Dla każdego zamknięcia dnia sygnału: indeks pierwszej świecy H1 z ts ≥ close_ts otwartej o `hour` czasu polskiego
    (najdalej MAX_WAIT_H godzin później); brak = −1."""
    h1_ts = np.asarray(h1_ts, np.int64)
    loc_h = pd.to_datetime(h1_ts, unit="s", utc=True).tz_convert(TRADING_TZ).hour.to_numpy()
    ok = np.flatnonzero(loc_h == hour)            # świece o godzinie wejścia, rosnąco
    out = np.full(len(close_ts), -1, np.int64)
    if not len(ok):
        return out
    pos = np.searchsorted(h1_ts[ok], np.asarray(close_ts, np.int64), side="left")
    has = pos < len(ok)
    cand = ok[np.minimum(pos, len(ok) - 1)]
    near = has & (h1_ts[cand] - np.asarray(close_ts, np.int64) <= MAX_WAIT_H * 3600)
    out[near] = cand[near]
    return out


def execute_on_h1(sig: pd.DataFrame, d1: dict[str, pd.DataFrame], h1: dict[str, pd.DataFrame], hour: int) -> tuple[pd.DataFrame, dict]:
    """Sygnały D1 (param_id, pair, i, sig, tp, sl, bars — i = indeks dnia) → sygnały na świecach H1: i = świeca PRZED
    świecą wejścia (B1: wejście na open następnej). Dni bez świecy wejścia w danych H1 są pomijane i liczone."""
    rows, lost = [], {"przed_h1": 0, "brak_swiecy": 0}
    for pair, g in sig.groupby("pair"):
        if pair not in h1 or pair not in d1:
            lost["brak_swiecy"] += len(g)
            continue
        d, h = d1[pair], h1[pair]
        cts = d["close_ts"].to_numpy(np.int64)[g["i"].to_numpy(int)]
        before = cts < int(h["ts"].iloc[0])
        e = entry_bar_index(h["ts"].to_numpy(np.int64), cts, hour)
        good = (e >= 1) & ~before
        lost["przed_h1"] += int(before.sum())
        lost["brak_swiecy"] += int((~good & ~before).sum())
        k = g[good].copy()
        k["i"] = e[good] - 1
        k["d1_i"] = g["i"].to_numpy(int)[good]
        rows.append(k)
    out = pd.concat(rows, ignore_index=True) if rows else sig.iloc[0:0].copy()
    out = out.drop_duplicates(subset=["param_id", "pair", "i"], keep="last")   # dwa dni sygnału → ta sama świeca (święto)
    return out.reset_index(drop=True), lost
