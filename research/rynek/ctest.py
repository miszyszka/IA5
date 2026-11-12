import sys; sys.argv = ['x', 'yh']
import ev
import lib
import numpy as np
import pandas as pd
import s5_monday as S

pd.set_option("display.width", 200)
S.TRIG = {f"rsi2 {a}/{100-a}": (lambda a: (lambda F: (F.rsi2 > 100 - a).astype(int) - (F.rsi2 < a).astype(int)))(a) for a in (10, 15, 20)}
print("1. PONIEDZIAŁEK (C = Yahoo H1 2024-10..2026-11): netto pips (n, śr., t tygodniowe)")
for hold in (12, 20, 30):
    E = S.events(1, hold)
    print(f"   trzymanie {hold} h:", {nm[5:]: S.stat(E, nm).get('C') for nm in S.TRIG})
E = S.events(1, 20); nm = "rsi2 15/85"; s = -E[nm].fillna(0); m = s != 0
X = E[m].assign(net=(s * E.gross)[m] - E.pair[m].map(lib.SPREAD), d=s[m])
print("   15/85, 20 h: long/short", X.groupby("d").net.agg(["size", "mean"]).round(1).to_dict("index"), "| pary +:", int((X.groupby("pair").net.mean() > 0).sum()), "/ 8 | spread×2:", round((X.net - X.pair.map(lib.SPREAD)).mean(), 2))
q = X.groupby(X.t.dt.to_period("Q")).net.sum()
print("   kwartały na plusie:", int((q > 0).sum()), "/", len(q), "| suma pips:", round(X.net.sum()))
X.to_parquet("out/mon_C.parquet")

def asia(k, thr, eh=0):
    def f(d, p):
        v = (d.close - d.close.shift(k)) / (d.atr * np.sqrt(k))
        return (-np.sign(v).where(v.abs() > thr, 0)).where(d.h_lon.shift(-1) == eh, 0)
    return f
E2, S2 = ev.study("", asia(4, 0.5), src="yh", hs=(4, 8), show=False)
print("2. AZJA k=4 thr=0.5:", {k: round(v, 2) for k, v in S2["C"].items()})
import fixlib

fixlib.SRC = "yh"
E3, S3 = ev.study("", fixlib.sig(4, 0.5, (1, 1)), src="yh", hs=(1, 2, 4), show=False)
print("3. FIXING ostatni dzień k=4 thr=0.5:", {k: round(v, 2) for k, v in S3["C"].items()})
