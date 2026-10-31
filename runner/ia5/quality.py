"""Kontrola jakości danych (D5). Zgłasza, niczego nie naprawia."""
import numpy as np
import pandas as pd

from .config import PAIRS
from .session import H, is_expected_bar


def bar_flags(h1: pd.DataFrame) -> dict:
    """Liczniki naruszeń na świecach H1 (kolumny ts, open, high, low, close)."""
    if h1.empty:
        return {"ohlc": 0, "price": 0, "ts": 0, "gaps": 0, "gap_list": []}
    o, h, lo, c = (h1[k].to_numpy() for k in ("open", "high", "low", "close"))
    ts = h1["ts"].to_numpy()
    gaps = []
    for a, b in zip(ts[:-1], ts[1:]):
        if b - a > H:
            missing = [t for t in range(int(a) + H, int(b), H) if is_expected_bar(t)]
            if missing:
                gaps.append((int(missing[0]), len(missing)))
    return {
        "ohlc": int(((h < np.maximum(o, c) - 1e-12) | (lo > np.minimum(o, c) + 1e-12)).sum()),
        "price": int((np.minimum.reduce([o, h, lo, c]) <= 0).sum()),
        "ts": int((ts % H != 0).sum()),
        "gaps": len(gaps),
        "gap_list": gaps[:20],
    }


def cross_check(h1: dict[str, pd.DataFrame]) -> dict:
    """Trójkąty: EURJPY vs EURUSD×USDJPY, EURGBP vs EURUSD÷GBPUSD. Odchyłki zamknięć w pipsach."""
    def joined(*pairs):
        dfs = [h1[p][["ts", "close"]].rename(columns={"close": p}) for p in pairs if p in h1]
        if len(dfs) < len(pairs):
            return None
        out = dfs[0]
        for d in dfs[1:]:
            out = out.merge(d, on="ts")
        return out

    res = {}
    j = joined("EURUSD", "USDJPY", "EURJPY")
    if j is not None and len(j):
        dev = (j["EURJPY"] - j["EURUSD"] * j["USDJPY"]).abs() / PAIRS["EURJPY"].pip
        res["EURJPY"] = {"median": float(dev.median()), "p99": float(dev.quantile(0.99)), "n": len(j)}
    j = joined("EURUSD", "GBPUSD", "EURGBP")
    if j is not None and len(j):
        dev = (j["EURGBP"] - j["EURUSD"] / j["GBPUSD"]).abs() / PAIRS["EURGBP"].pip
        res["EURGBP"] = {"median": float(dev.median()), "p99": float(dev.quantile(0.99)), "n": len(j)}
    return res
