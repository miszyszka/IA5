"""Księga na okresie C (Yahoo 2024-11..2026-10), wagi = odwrotność zmienności z okresu badania (bez podglądania C)."""
import os
import sys

import lib
import numpy as np
import pandas as pd

sys.argv = ["x", "yh"]
import ev

F = ev.frames("yh")
mon = pd.read_parquet("out/mon_C.parquet")
mon["ret"] = 0.0
for p, g in mon.groupby("pair"):
    mon.loc[g.index, "ret"] = g.net.to_numpy() * lib.PIP[p] / F[p].open.reindex(pd.DatetimeIndex(g.t)).to_numpy()
def asia(d, p):
    v = (d.close - d.close.shift(4)) / (d.atr * 2)
    return (-np.sign(v).where(v.abs() > 0.5, 0)).where(d.h_lon.shift(-1) == 0, 0)
A, _ = ev.study("", asia, src="yh", hs=(8,), show=False)
A["t"] = pd.to_datetime(A.fxday).dt.tz_localize("UTC")
A["ret"] = A.n8 * A.pair.map(lib.PIP) / A.pair.map({p: F[p].close.median() for p in lib.PAIRS})
os.environ["D1"] = __import__("os").environ.get("D1_FIXED", "../rsi_d1/d1_fixed")
src = open("../rsi_d1/streak.py").read(); src = src[:src.index("specs=list(")]
ns = {"__name__": "streak_lib"}; sys.path.insert(0, "../rsi_d1"); exec(compile(src, "streak.py", "exec"), ns)
v2 = ns["run"]((5, 25, 2, 2.0), (3, 0), 3, "stała")
v2 = pd.DataFrame({"t": pd.to_datetime(v2.xts, unit="s", utc=True), "ret": v2.ret.to_numpy()})
idx = pd.period_range("2024-11", "2026-10", freq="M")
mo = lambda x: x.groupby(x.t.dt.tz_convert(None).dt.to_period("M")).ret.sum()
M = pd.DataFrame({"poniedziałek": mo(mon), "azja": mo(A), "seria_D1": mo(v2)}).reindex(idx).fillna(0)
sd = {"poniedziałek": 0.02242, "azja": 0.02685, "seria_D1": 0.04187}       # z okresu badania 2013–2022 (book.py)
Z = M / pd.Series(sd)
Z["księga (3 razem)"] = Z.mean(axis=1)
Z["księga bez Azji"] = Z[["poniedziałek", "seria_D1"]].mean(axis=1)
def st(s):
    q = s.groupby(s.index.asfreq("Q")).sum(); c = s.cumsum()
    return {"Sharpe": round(s.mean() / s.std() * np.sqrt(12), 2), "mies.+": f"{(s > 0).mean():.0%}", "kw.+": f"{(q > 0).sum()}/{len(q)}",
            "suma (w mies. zmiennościach)": round(s.sum(), 1), "najgł. obsunięcie": round((c - c.cummax()).min(), 1)}
pd.set_option("display.width", 200)
print(pd.DataFrame({k: st(Z[k]) for k in Z}).T.to_string())
print("korelacje:", M.corr().round(2).to_dict())
