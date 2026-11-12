"""Odwrócenie w Azji: ruch z popołudnia w Nowym Jorku (ostatnie k godzin przed północą w Londynie) cofa się do otwarcia Londynu."""
import sys

import ev
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "ej"

def sig(k, thr, eh=0):
    def f(d, p):
        v = (d.close - d.close.shift(k)) / (d.atr * np.sqrt(k))
        s = -np.sign(v).where(v.abs() > thr, 0)
        return s.where(d.h_lon.shift(-1) == eh, 0)
    return f

rows = []
for k in (2, 4, 6, 8):
    for thr in (0, 0.5, 0.75, 1.0):
        E, S = ev.study(f"k={k} thr={thr}", sig(k, thr), src=SRC, hs=(2, 4, 8, 10), show=False)
        for per, r in S.items():
            rows.append({"k": k, "thr": thr, "per": per, "n": r["n"], **{f"h{h}": round(r[f"m{h}"], 2) for h in (2, 4, 8, 10)}, "t8": round(r["t8"], 1)})
R = pd.DataFrame(rows)
print("netto pips (po spreadzie) wg okresu:")
print(R.pivot(index=["k", "thr"], columns="per", values=["n", "h4", "h8", "h10", "t8"]).to_string())
# wybrany środek siatki: szczegóły
E, S = ev.study("k=4 thr=0.5", sig(4, 0.5), src=SRC, hs=(8,), show=False)
E["rok"] = pd.to_datetime(E.fxday).dt.year
print("\nk=4 thr=0.5 h=8: long/short:", E.groupby(["per", "dir"]).n8.agg(["size", "mean"]).round(2).to_dict("index"))
print("wg pary:", E.groupby("pair").n8.mean().round(2).to_dict())
print("wg roku:", E.groupby("rok").n8.agg(["size", "mean"]).round(1).T.to_string())
