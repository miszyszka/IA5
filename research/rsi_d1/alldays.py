"""Każdy dzień, każda para: cechy i przyszły zwrot w ATR (long). Analiza lustrzana: cechy × kierunek."""
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import indicators as ind
from ia5.config import PAIRS

D = {f.stem: pd.read_parquet(f) for f in sorted(Path(__import__("os").environ.get("D1", "d1_fixed")).glob("*.parquet"))}
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp(); CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
fr = []
for pair, df in D.items():
    s = df.close; o = df.open.to_numpy(); c = s.to_numpy(); n = len(df)
    atr = ind.atr(df, 14).to_numpy()
    f = pd.DataFrame({"pair": pair, "ts": df.ts, "atr": atr})
    for k in (2, 5, 14): f[f"rsi{k}"] = ind.rsi(s, k).to_numpy()
    for k in (5, 20, 60, 120, 250): f[f"mom{k}"] = (s - s.shift(k)).to_numpy() / atr
    f["trend200"] = (s - ind.sma(s, 200)).to_numpy() / atr
    f["dist20"] = (s - ind.sma(s, 20)).to_numpy() / atr
    a = ind.adx(df, 14); f["di"] = (a.plus_di - a.minus_di).to_numpy(); f["adx"] = a.adx.to_numpy()
    sp = PAIRS[pair].spread_pips * PAIRS[pair].pip
    gapc = np.r_[0, np.cumsum(df.gap_before.to_numpy() > 0)]
    for k in (1, 3, 5, 10, 20):
        e = np.r_[o[1:], np.nan]                                    # open t+1
        x = np.r_[c[k:], np.full(k, np.nan)]                        # close t+k
        r = (x - e) / atr
        ok = np.zeros(n, bool); ii = np.arange(n); m = ii + k < n
        ok[m] = gapc[np.minimum(ii[m] + k + 1, n)] - gapc[ii[m] + 1] == 0
        f[f"f{k}"] = np.where(ok, r, np.nan); f[f"sp{k}"] = sp / atr
    fr.append(f.iloc[250:])
t = pd.concat(fr, ignore_index=True)
t["period"] = np.where(t.ts < CUT_A, "A", np.where(t.ts < CUT_IS, "B", "OOS"))
t.to_parquet("alldays.parquet", index=False); print(t.groupby("period").size())
