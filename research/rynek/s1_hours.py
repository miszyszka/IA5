"""Sezonowość godzinowa: średni zwrot świecy H1 (pips) wg godziny w Londynie / Tokio / NY; A = 2012-11..2017-06, B = 2017-07..2022-03."""
import lib
import numpy as np
import pandas as pd

pd.set_option('display.width', 250)
out = []
for p in lib.PAIRS:
    d = lib.add_time(lib.load_ej(p))
    d["r"] = (d.close - d.open) / lib.PIP[p]
    d["per"] = np.where(d.index < lib.CUT_AB, "A", "B")
    for zone in ("h_lon", "h_tk", "h_ny"):
        g = d.groupby([zone, "per"]).r.agg(["mean", lib.tstat]).unstack()
        for h in g.index:
            out.append({"pair": p, "zone": zone, "h": h, "A": g.loc[h, ("mean", "A")], "B": g.loc[h, ("mean", "B")],
                        "tA": g.loc[h, ("tstat", "A")], "tB": g.loc[h, ("tstat", "B")]})
r = pd.DataFrame(out)
r.to_csv("out/s1_hours.csv", index=False)
sig = r[(np.sign(r.A) == np.sign(r.B)) & (r.tA.abs() > 2) & (r.tB.abs() > 2)]
print("hipotez:", len(r), " zgodnych z |t|>2 w obu połowach:", len(sig), " (losowo oczekiwane ≈", round(len(r) * 0.0455 * 0.0455 / 2, 1), ")")
print(sig.round(2).sort_values(["zone", "h", "pair"]).to_string())
