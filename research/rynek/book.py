"""Księga: kilka małych, różnych przewag razem — poniedziałkowy powrót (H1), odwrócenie w Azji (H1), seria wyprzedania w trendzie (D1).
Wszystko na niezależnych danych brokera 2013–2022. Każda strategia przeskalowana do tej samej zmienności miesięcznej."""
import os
import sys
from pathlib import Path

import lib
import numpy as np
import pandas as pd

sys.argv = ["x", "ej"]
import ev
import s5_monday as S

# --- dzienne świece z danych brokera w formacie d1_ready (do serii wyprzedania)
out = Path("ej_d1"); out.mkdir(exist_ok=True)
for p in lib.PAIRS:
    h = lib.add_time(lib.load_ej(p)); g = h.groupby("londay")
    d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "n": g.size()})
    d = d[(d.index.dayofweek < 5) & (d.n >= 12)]
    ts = lib.epoch(pd.DatetimeIndex(d.index).tz_localize("Europe/London"))
    pd.DataFrame({"ts": ts, "open": d.open.to_numpy(), "high": d.high.to_numpy(), "low": d.low.to_numpy(), "close": d.close.to_numpy(),
                  "filled": False, "gap_before": 0, "close_ts": ts + 86400}).to_parquet(out / f"{p}.parquet", index=False)
os.environ["D1"] = "ej_d1"
sys.path.insert(0, "../rsi_d1")
src = open("../rsi_d1/streak.py").read()
src = src[:src.index("specs=list(")]
ns = {"__name__": "streak_lib"}
cwd = os.getcwd()
exec(compile(src, "streak.py", "exec"), ns)
v2 = ns["run"]((5, 25, 2, 2.0), (3, 0), 3, "stała")
v2 = pd.DataFrame({"t": pd.to_datetime(v2.xts, unit="s", utc=True), "ret": v2.ret.to_numpy()})

F = ev.frames("ej")
def price(pair, t):
    return F[pair].open.reindex(t).to_numpy()
E = S.events(1, 20); S.TRIG["x"] = lambda Fr: (Fr.rsi2 > 85).astype(int) - (Fr.rsi2 < 15).astype(int)
E = S.events(1, 20); s = -E["x"].fillna(0); m = s != 0
mon = E[m].assign(net=(s * E.gross)[m] - E.pair[m].map(lib.SPREAD))
mon["ret"] = np.concatenate([g.net.to_numpy() * lib.PIP[p] / price(p, g.t) for p, g in mon.groupby("pair", sort=False)]) if False else 0.0
for p, g in mon.groupby("pair"):
    mon.loc[g.index, "ret"] = g.net.to_numpy() * lib.PIP[p] / price(p, pd.DatetimeIndex(g.t))
def asia(d, p):
    v = (d.close - d.close.shift(4)) / (d.atr * 2)
    return (-np.sign(v).where(v.abs() > 0.5, 0)).where(d.h_lon.shift(-1) == 0, 0)
A, _ = ev.study("", asia, hs=(8,), show=False)
A["t"] = pd.to_datetime(A.fxday).dt.tz_localize("UTC")
A["ret"] = A.n8 * A.pair.map(lib.PIP) / A.pair.map({p: F[p].close.median() for p in lib.PAIRS})

def monthly(x):
    s = x.groupby(x.t.dt.tz_convert(None).dt.to_period("M")).ret.sum()
    return s
idx = pd.period_range("2013-01", "2022-02", freq="M")
M = pd.DataFrame({"poniedziałek": monthly(mon), "azja": monthly(A), "seria_D1": monthly(v2)}).reindex(idx).fillna(0)
Z = M / M.std()
Z["księga (3 razem)"] = Z.mean(axis=1) / Z.mean(axis=1).std()
Z["księga bez Azji"] = Z[["poniedziałek", "seria_D1"]].mean(axis=1) / Z[["poniedziałek", "seria_D1"]].mean(axis=1).std()
def st(s):
    q = s.groupby(s.index.asfreq("Q")).sum(); y = s.groupby(s.index.year).sum(); c = s.cumsum()
    return {"Sharpe": round(s.mean() / s.std() * np.sqrt(12), 2), "mies.+": f"{(s > 0).mean():.0%}", "kw.+": f"{(q > 0).mean():.0%}",
            "lata+": f"{(y > 0).sum()}/{len(y)}", "najgł. obsunięcie (w mies. zmiennościach)": round((c - c.cummax()).min(), 1),
            "najdłużej pod wodą (mies.)": int(pd.Series((c < c.cummax()).astype(int)).groupby((c >= c.cummax()).cumsum()).sum().max())}
pd.set_option("display.width", 220)
print(pd.DataFrame({k: st(Z[k]) for k in Z}).T.to_string())
print("korelacje miesięczne:\n", M.corr().round(2).to_string())
print("transakcji rocznie:", {"poniedziałek": round(len(mon) / 9.2), "azja": round(len(A) / 9.2), "seria_D1": round(len(v2[(v2.t >= "2013") ]) / 9.2)})
Z.to_csv("out/book_monthly.csv")
