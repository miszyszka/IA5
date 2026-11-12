"""Ocena konfiguracji strategii dokładnie silnikiem IA5 (sandbox + engine.run), metryki stabilności TYLKO na IS.
Użycie: python eval_cfg.py strategia.py d1_ready [--oos]"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from ia5.backtest import exits_from
from ia5.engine import run
from ia5.portfolio import trade_returns
from ia5.sandbox import run_strategy_code

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
pd.set_option("display.max_colwidth", 60)

code = Path(sys.argv[1]).read_text()
d1 = Path(sys.argv[2]).resolve()
show_oos = "--oos" in sys.argv
sig, meta = run_strategy_code(code, d1, d1_dir=d1)
assert not meta["lookahead"], meta["lookahead"][:3]
assert not meta.get("errors"), meta.get("errors")
D = {f.stem: pd.read_parquet(f) for f in sorted(d1.glob("*.parquet"))}
signals, levels = {}, {}
for pid in range(len(meta["params"])):
    for pair, df in D.items():
        arr = np.zeros(len(df), np.float32)
        part = sig[(sig.param_id == pid) & (sig.pair == pair)]
        arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
        signals[(pid, pair)] = arr
        lv = np.full((len(df), 2), np.nan)
        lv[part["i"].to_numpy(int), 0] = part["tp"].to_numpy(float)
        lv[part["i"].to_numpy(int), 1] = part["sl"].to_numpy(float)
        levels[(pid, pair)] = lv
exits = exits_from(meta.get("exits"))
res = run(D, signals, meta["params"], exits=exits, hours=False, pyramid=int(meta.get("pyramid") or 1), levels=levels)
out = res["outcomes"].join(res["entries"].set_index("entry_id")[["weight", "entry_px", "entry_ts"]], on="entry_id")
out["ret"] = trade_returns(out) * out["weight"]
pip = out["pair"].map({"USDJPY": 0.01, "EURJPY": 0.01}).fillna(0.0001)
out["ret_n"] = out["ret"] - 0.5 * out["nights"] * pip / out["entry_px"] * out["weight"]   # stres: 0,5 pipsa za noc
out["month"] = pd.to_datetime(out["exit_ts"], unit="s").dt.to_period("M")


CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()


def stats(g, sample):
    if sample == "A":
        g = g[(g["sample"] == "IS") & (g.entry_ts < CUT_A)]
    elif sample == "B":
        g = g[(g["sample"] == "IS") & (g.entry_ts >= CUT_A)]
    else:
        g = g[g["sample"] == sample]
    if g.empty:
        return {}
    first, last = g.month.min(), g.month.max()
    ms = g.groupby("month").ret_n.sum().reindex(pd.period_range(first, last, freq="M"), fill_value=0)
    q = ms.groupby(ms.index.asfreq("Q")).sum()
    y = ms.groupby(ms.index.year).sum()
    cum = ms.cumsum()
    pp = g.groupby("pair").ret_n.sum()
    return {"n": len(g), "n/rok": len(g) / max(len(y), 1), "suma": ms.sum() / g.weight.mean(), "sharpe_m": ms.mean() / ms.std() * np.sqrt(12),
            "mies+": (ms[ms != 0] > 0).mean(), "kw+": (q > 0).mean(), "lata+": (y > 0).mean(),
            "dd": (cum - cum.cummax()).min() / g.weight.mean(), "pary+": int((pp > 0).sum()), "exp_r": g.r_net.mean()}


rows = []
for vid, g in out.groupby("variant_id"):
    v = res["variants"].set_index("variant_id").loc[vid]
    r = {"v": vid, "cfg": v["params"]["cfg"], "cap": v["x_cap"], **{f"A_{k}": x for k, x in stats(g, "A").items()},
         **{f"B_{k}": x for k, x in stats(g, "B").items()}}
    if show_oos:
        r.update({f"OOS_{k}": x for k, x in stats(g, "OOS").items()})
    rows.append(r)
t = pd.DataFrame(rows)
print(t.round(3).to_string())
print("granica IS/OOS:", pd.to_datetime(res["cutoff"], unit="s"), "pominięte:", res["skipped"])
t.to_csv(Path(sys.argv[1]).stem + "_" + d1.name + ("_oos" if show_oos else "_is") + ".csv", index=False)
