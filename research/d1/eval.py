"""Ocena strategii dokładnie silnikiem IA5 (sandbox + engine.run) na danych D1. Bez --oos pokazuje tylko IS (połowy A, B).
Użycie: python eval.py strategia.py katalog_d1 [--oos]"""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ia5.backtest import exits_from
from ia5.engine import run
from ia5.portfolio import trade_returns
from ia5.sandbox import run_strategy_code

pd.set_option("display.width", 250)
code = Path(sys.argv[1]).read_text()
d1 = Path(sys.argv[2]).resolve()
show_oos = "--oos" in sys.argv
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
sig, meta = run_strategy_code(code, d1, d1_dir=d1)
assert not meta["lookahead"], meta["lookahead"][:3]
D = {f.stem: pd.read_parquet(f) for f in sorted(d1.glob("*.parquet"))}
signals, levels = {}, {}
for pid in range(len(meta["params"])):
    for pair, df in D.items():
        arr = np.zeros(len(df), np.float32)
        part = sig[(sig.param_id == pid) & (sig.pair == pair)]
        arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
        signals[(pid, pair)] = arr
        lv = np.full((len(df), 3), np.nan)
        for k, col in enumerate(("tp", "sl", "bars")):
            lv[part["i"].to_numpy(int), k] = part[col].to_numpy(float)
        levels[(pid, pair)] = lv
res = run(D, signals, meta["params"], exits=exits_from(meta.get("exits")), hours=False, pyramid=int(meta.get("pyramid") or 1), levels=levels)
out = res["outcomes"].join(res["entries"].set_index("entry_id")[["weight", "entry_px", "entry_ts", "atr14"]], on="entry_id")
pip = out["pair"].map({"USDJPY": 0.01, "EURJPY": 0.01}).fillna(0.0001)
out["ret"] = (trade_returns(out) - 0.5 * out["nights"] * pip / out["entry_px"]) * out["weight"]      # stres: 0,5 pipsa za noc
out["ratr"] = (out["pips_net"] - 0.5 * out["nights"]) * pip / out["atr14"]
out["month"] = pd.to_datetime(out["exit_ts"], unit="s").dt.to_period("M")
out["per"] = np.where(out.entry_ts < CUT_A, "A", np.where(out["sample"] == "IS", "B", "O"))


def stats(g):
    if len(g) < 30:
        return {"n": len(g)}
    ms = g.groupby("month").ret.sum().reindex(pd.period_range(g.month.min(), g.month.max(), freq="M"), fill_value=0)
    q, y = ms.groupby(ms.index.asfreq("Q")).sum(), ms.groupby(ms.index.year).sum()
    cum = ms.cumsum()
    yrs = len(ms) / 12
    return {"n": len(g), "n/r": round(len(g) / yrs), "ATR": round(g.ratr.mean(), 3), "pips": round((g.pips_net - 0.5 * g.nights).mean(), 2),
            "sh": round(ms.mean() / ms.std() * np.sqrt(12), 2), "mies+": round((ms[ms != 0] > 0).mean(), 2), "kw+": round((q > 0).mean(), 2),
            "lata+": round((y > 0).mean(), 2), "pary+": int((g.groupby("pair").ret.sum() > 0).sum()),
            "dd/rok": round((cum - cum.cummax()).min() / (ms.sum() / yrs), 2) if ms.sum() > 0 else np.nan}


rows = []
for vid, g in out.groupby("variant_id"):
    for pr in ("A", "B", "IS") + (("O",) if show_oos else ()):
        gg = g[g["sample"] == "IS"] if pr == "IS" else g[g.per == pr]
        rows.append({"cfg": res["variants"].set_index("variant_id").loc[vid]["params"]["cfg"], "odc": pr, **stats(gg)})
t = pd.DataFrame(rows)
print(t.to_string(index=False))
print("granica IS/OOS:", pd.to_datetime(res["cutoff"], unit="s"), "| pominięte:", res["skipped"])
out.to_parquet(paths.DATA / "out" / f"eval_{Path(sys.argv[1]).stem}_{d1.name}.parquet", index=False)
