"""Diagnoza: każda świeca wyprzedania/wykupienia jako obserwacja, cechy w chwili sygnału, wynik po k dniach w ATR14.
Okresy: A = do 2011-12-31 (odkrycie), B = 2012-01-01..2019-05-09 (potwierdzenie), OOS = później (NIE używany tutaj)."""
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import indicators as ind
from ia5.config import PAIRS

D = {f.stem: pd.read_parquet(f) for f in sorted(Path(__import__("os").environ.get("D1", "d1_fixed")).glob("*.parquet"))}
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
USD_BASE = {"USDJPY": -1, "USDCHF": -1, "USDCAD": -1, "EURUSD": 1, "GBPUSD": 1, "AUDUSD": 1}  # +1: long pary = short USD

rows = []
for pair, df in D.items():
    o, h, l, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    s = df.close
    n = len(df)
    atr = ind.atr(df, 14).to_numpy()
    atr100 = ind.atr(df, 100).to_numpy()
    r2, r5, r14 = (ind.rsi(s, k).to_numpy() for k in (2, 5, 14))
    sma20, sma50, sma200 = (ind.sma(s, k).to_numpy() for k in (20, 50, 200))
    adx = ind.adx(df, 14)
    hi250, lo250 = ind.highest(df.high, 250).to_numpy(), ind.lowest(df.low, 250).to_numpy()
    hi20, lo20 = ind.highest(df.high, 20).to_numpy(), ind.lowest(df.low, 20).to_numpy()
    gap = df.gap_before.to_numpy()
    spread = PAIRS[pair].spread_pips * PAIRS[pair].pip
    with np.errstate(invalid="ignore"):
        lo_sig = (r2 < 15) | (r5 < 25) | (r14 < 40)
        hi_sig = (r2 > 85) | (r5 > 75) | (r14 > 60)
    for d, sig in ((1, lo_sig), (-1, hi_sig)):
        idx = np.flatnonzero(sig)
        idx = idx[(idx >= 250) & (idx + 11 < n)]
        for i in idx:
            if gap[i + 1: i + 12].any():
                continue
            a = atr[i]
            e = o[i + 1]
            fw = {f"ret{k}": (d * (c[i + k] - e) - spread) / a for k in (1, 2, 3, 5, 7, 10)}
            rng = h[i] - l[i]
            clv = (c[i] - l[i]) / rng if rng > 0 else 0.5          # gdzie zamknął dzień: 0 dołek, 1 szczyt
            # cechy „w kierunku transakcji” (d × …): dodatnie = po stronie transakcji
            rows.append({
                "pair": pair, "dir": d, "ts": df.ts.iloc[i], "i": i,
                "r2": r2[i] if d > 0 else 100 - r2[i], "r5": r5[i] if d > 0 else 100 - r5[i],
                "r14": r14[i] if d > 0 else 100 - r14[i],
                "trend200": d * (c[i] - sma200[i]) / a,                       # > 0 = cena po stronie trendu
                "slope200": d * (sma200[i] - sma200[i - 20]) / a,            # nachylenie SMA200 w ATR / 20 dni
                "trend50_200": d * (sma50[i] - sma200[i]) / a,
                "dist20": d * (c[i] - sma20[i]) / a,                          # < 0 = cofnięcie pod SMA20
                "mom5": d * (c[i] - c[i - 5]) / a, "mom20": d * (c[i] - c[i - 20]) / a,
                "mom60": d * (c[i] - c[i - 60]) / a, "mom120": d * (c[i] - c[i - 120]) / a,
                "volr": a / atr100[i],                                        # ATR14 / ATR100: zmienność teraz vs zwykła
                "rangeatr": rng / a, "clv": clv if d > 0 else 1 - clv,        # 1 = zamknięcie przy szczycie dnia (dla long)
                "body": d * (c[i] - o[i]) / a,                                # < 0 = świeca przeciw transakcji
                "adx": adx["adx"].iloc[i], "di": d * (adx["plus_di"].iloc[i] - adx["minus_di"].iloc[i]),
                "pos250": ((c[i] - lo250[i]) / (hi250[i] - lo250[i])) if d > 0 else ((hi250[i] - c[i]) / (hi250[i] - lo250[i])),
                "pos20": ((c[i] - lo20[i]) / (hi20[i] - lo20[i])) if d > 0 else ((hi20[i] - c[i]) / (hi20[i] - lo20[i])),
                "dow": pd.Timestamp(df.ts.iloc[i + 1], unit="s").dayofweek, "month": pd.Timestamp(df.ts.iloc[i], unit="s").month,
                "usd": USD_BASE.get(pair, 0) * d,                             # +1 = transakcja przeciw USD
                "mae5": (e - l[i + 1:i + 6].min()) / a if d > 0 else (h[i + 1:i + 6].max() - e) / a,
                "mfe5": (h[i + 1:i + 6].max() - e) / a if d > 0 else (e - l[i + 1:i + 6].min()) / a,
                **fw,
            })
t = pd.DataFrame(rows)
t["period"] = np.where(t.ts < CUT_A, "A", np.where(t.ts < CUT_IS, "B", "OOS"))
t["date"] = pd.to_datetime(t.ts, unit="s").dt.normalize()
# ile par ma tego dnia sygnał w tę samą stronę względem USD (szok dolarowy vs ruch własny pary)
usd_day = t[t.usd != 0].groupby(["date", "usd"]).size().rename("usd_crowd")
t = t.join(usd_day, on=["date", "usd"])
t["usd_crowd"] = t.usd_crowd.fillna(0)
t.to_parquet("diag.parquet", index=False)
print(t.groupby("period").size(), t.columns.tolist())
