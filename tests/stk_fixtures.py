"""Syntetyczne świece spółek do testów Stocks (D-071): dni sesji NY, dywidendy, opcjonalnie powrót do średniej."""
from __future__ import annotations

import numpy as np
import pandas as pd
from ia5.stk_config import TZ


def ny_midnights(start: str, end: str) -> tuple[np.ndarray, np.ndarray]:
    days = pd.bdate_range(start, end)
    days = days[~((days.month == 12) & (days.day == 25)) & ~((days.month == 1) & (days.day == 1))]
    ts = pd.DatetimeIndex(days).tz_localize(TZ).tz_convert("UTC").as_unit("s").asi8
    return ts.astype("int64"), days.strftime("%Y-%m-%d").to_numpy()


def raw_stock(seed: int, start: str = "1995-01-02", end: str = "2026-11-13", revert: float = 0.0, common=None,
              div_every: int = 63, div_yield: float = 0.005) -> pd.DataFrame:
    """Surowa kopia (jak Apps Script): ts, open, high, low, close, div, split. revert > 0 = cena wraca do ścieżki trendu."""
    rng = np.random.default_rng(seed)
    ts, _ = ny_midnights(start, end)
    n = len(ts)
    eps = rng.normal(0.0003, 0.015, n)
    if common is not None:
        eps = eps + common[-n:]
    lg = np.zeros(n)
    trend = np.cumsum(np.full(n, 0.0003))
    for i in range(1, n):
        lg[i] = lg[i - 1] + eps[i] - revert * (lg[i - 1] - trend[i - 1])
    close = 30 * np.exp(lg)
    op = close * np.exp(rng.normal(0, 0.004, n))
    hi = np.maximum(op, close) * (1 + np.abs(rng.normal(0, 0.005, n)))
    lo = np.minimum(op, close) * (1 - np.abs(rng.normal(0, 0.005, n)))
    div = np.zeros(n)
    div[div_every::div_every] = close[div_every::div_every] * div_yield
    return pd.DataFrame({"ts": ts, "open": op, "high": hi, "low": lo, "close": close, "div": div, "split": 1.0})


def universe(n: int = 8, revert: float = 0.0, late: dict | None = None, end: str = "2026-11-13") -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(99)
    ts, _ = ny_midnights("1995-01-02", end)
    common = rng.normal(0, 0.008, len(ts))
    out = {}
    for j in range(n):
        start = (late or {}).get(j, "1995-01-02")
        out[f"T{j}"] = raw_stock(j, start=start, end=end, revert=revert, common=common)
    return out
