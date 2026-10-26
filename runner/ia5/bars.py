"""Budowa świec H1 z M1 bid/ask (D7, B3)."""
import numpy as np
import pandas as pd

H1_COLS = ["ts", "open", "high", "low", "close", "bid_close", "ask_close", "spread_avg", "minutes"]


def m1_to_h1(m1: pd.DataFrame) -> pd.DataFrame:
    """Mid = (bid + ask) / 2 dla każdej minuty, potem agregacja do pełnych godzin UTC.

    Minuty bez wolumenu po obu stronach (Dukascopy wypełnia nimi przerwy) są pomijane;
    godzina bez żadnej aktywnej minuty nie tworzy świecy.
    """
    if m1.empty:
        return pd.DataFrame(columns=H1_COLS)
    df = m1[(m1["bv"] > 0) | (m1["av"] > 0)].copy()
    if df.empty:
        return pd.DataFrame(columns=H1_COLS)
    for f in "ohlc":
        df[f] = (df["b" + f] + df["a" + f]) / 2
    df["spr"] = df["ac"] - df["bc"]
    df["hour"] = (df["ts"] // 3600) * 3600
    g = df.sort_values("ts").groupby("hour", sort=True)
    out = pd.DataFrame({
        "open": g["o"].first(),
        "high": g["h"].max(),
        "low": g["l"].min(),
        "close": g["c"].last(),
        "bid_close": g["bc"].last(),
        "ask_close": g["ac"].last(),
        "spread_avg": g["spr"].mean(),
        "minutes": g["o"].size().astype("int16"),
    })
    out.index.name = "ts"
    out = out.reset_index()
    out["ts"] = out["ts"].astype("int64")
    return out[H1_COLS].astype({c: np.float64 for c in H1_COLS if c not in ("ts", "minutes")})
