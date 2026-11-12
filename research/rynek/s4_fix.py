"""Siatka dla fixingu londyńskiego (funkcje w fixlib.py). Użycie: python s4_fix.py ej|yh"""

import ev
import fixlib
import pandas as pd
from fixlib import sig

SRC = fixlib.SRC
rows = []
for last in (None, (1, 1), (1, 2), (1, 3), (2, 3), (4, 8)):
    for k in (1, 2, 4):
        for thr in (0, 0.5, 1.0):
            E, S = ev.study("", sig(k, thr, last), src=SRC, hs=(1, 2, 4), show=False)
            for per, r in S.items():
                rows.append({"dni_od_konca": str(last), "k": k, "thr": thr, "per": per, "n": r["n"], "h1": round(r["m1"], 2), "h2": round(r["m2"], 2), "h4": round(r["m4"], 2), "t2": round(r["t2"], 1)})
R = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print("netto pips po spreadzie:")
print(R.pivot(index=["dni_od_konca", "k", "thr"], columns="per", values=["n", "h1", "h2", "h4", "t2"]).to_string())
E, S = ev.study("", sig(4, 0.5, (1, 2)), src=SRC, hs=(2,), show=False)
E["rok"] = pd.to_datetime(E.fxday).dt.year
print("\nk=4 thr=0.5 ostatnie 2 dni h=2: long/short:", E.groupby(["per", "dir"]).n2.agg(["size", "mean"]).round(2).to_dict("index"))
print("wg pary:", E.groupby("pair").n2.mean().round(2).to_dict())
print("wg roku:", E.groupby("rok").n2.agg(["size", "mean"]).round(1).T.to_string())
