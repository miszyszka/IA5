"""Ocena konfiguracji strategii składanej silnikiem IA5 (find_entries + simulate z limitem dni na wejście, B8/B12) na d1_v2.
Odcinki: A < 2012, B 2012–2019-05-09 (oba = IS silnika); O (OOS) tylko z --oos, po zamrożeniu projektu."""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from ia5 import engine
from ia5 import indicators as ind
from ia5.config import PAIRS

import skl

D1 = paths.DATA / "d1_v2"
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
import os
SRC = os.environ.get("SRC", "yahoo")
if SRC == "yahoo":
    RAW = {f.stem: pd.read_parquet(f) for f in sorted(D1.glob("*.parquet"))}
else:                                                   # niezależne dane brokera: dni londyńskie złożone z H1 (2012-11…2022-03)
    import glib
    from ia5.daily import close_ts
    RAW = {}
    for p_, d_ in glib.load("ej").items():
        ts_ = (d_.index.tz_localize("Europe/London").tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
        r_ = pd.DataFrame({"ts": np.asarray(ts_, "int64"), "open": d_.open.to_numpy(), "high": d_.high.to_numpy(), "low": d_.low.to_numpy(),
                           "close": d_.close.to_numpy(), "filled": False, "gap_before": 0})
        r_["close_ts"] = close_ts(r_["ts"].to_numpy(), "Europe/London")
        RAW[p_] = r_
    CUT_A = pd.Timestamp("2017-07-01", tz="UTC").timestamp()
    CUT_IS = pd.Timestamp("2030-01-01", tz="UTC").timestamp()
DF = {p: r.set_index(pd.to_datetime(r["ts"], unit="s", utc=True))[["open", "high", "low", "close"]] for p, r in RAW.items()}
PRE = {p: engine.prepare(r) for p, r in RAW.items()}
NIGHT = 0.5                                             # stres: 0,5 pipsa za noc (model silnika: swap 0)


def trades(cfg, pyr=1, pairs=None):
    rows = []
    for pair in (pairs or DF):
        sig, bars, tp, sl = skl.build(DF[pair], cfg, ind)
        P = PRE[pair]
        ent = engine.find_entries(P, sig)
        ent = ent[~ent.atr14.isna()].reset_index(drop=True)
        if ent.empty:
            continue
        i = ent.signal_i.to_numpy()
        ent["max_bars"] = bars[i]
        ent["tp_px"], ent["sl_px"] = tp[i], sl[i]
        res = engine.simulate(P, ent, engine.Exit("level", cap=int(max(bars.max(), 1))), pair)
        xi = res.exit_i.to_numpy(float).copy()
        xi[engine.data_cancel(P, i, ent.entry_i.to_numpy(), xi)] = np.nan
        keep = engine.no_overlap(ent.entry_i.to_numpy(), xi, ent.dir.to_numpy(), pyr)
        c = PAIRS[pair]
        net = res.pips_gross.to_numpy() - c.spread_pips - NIGHT * np.nan_to_num(res.nights.to_numpy())
        w = ent.weight.to_numpy()
        rows.append(pd.DataFrame({"pair": pair, "ts": ent.entry_ts.to_numpy(), "xts": res.exit_ts.to_numpy(), "w": w, "bars": res.bars.to_numpy(),
                                  "ret": w * net * c.pip / ent.entry_px.to_numpy(), "r": net * c.pip / ent.atr14.to_numpy(),
                                  "gross": res.pips_gross.to_numpy(), "net": net})[keep])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["pair", "ts", "xts", "w", "ret", "r"])


def stats(t):
    if len(t) < 30:
        return {"n": len(t)}
    mon = pd.to_datetime(t.xts, unit="s").dt.to_period("M")
    ms = t.groupby(mon).ret.sum()
    ms = ms.reindex(pd.period_range(ms.index.min(), ms.index.max(), freq="M"), fill_value=0)
    q = ms.groupby(ms.index.asfreq("Q")).sum()
    y = ms.groupby(ms.index.year).sum()
    cum = ms.cumsum()
    yrs = len(ms) / 12
    return {"n": len(t), "n/r": round(len(t) / yrs), "r": round(t.r.mean(), 3), "sh": round(ms.mean() / ms.std() * np.sqrt(12), 2),
            "kw+": round((q > 0).mean(), 2), "lata+": round((y > 0).mean(), 2), "pary+": int((t.groupby("pair").ret.sum() > 0).sum()),
            "dd/rok": round((cum - cum.cummax()).min() / (ms.sum() / yrs), 2) if ms.sum() > 0 else np.nan,
            "%/rok": round(100 * ms.sum() / yrs, 2)}


def split(t, oos=False):
    out = {"A": stats(t[t.ts < CUT_A]), "B": stats(t[(t.ts >= CUT_A) & (t.ts < CUT_IS)])}
    if oos:
        out["O"] = stats(t[t.ts >= CUT_IS])
    return out


def row(name, t, oos=False):
    r = {"cfg": name}
    for k, s in split(t, oos).items():
        r.update({f"{k}_{a}": b for a, b in s.items()})
    r["min_sh"] = min(r.get("A_sh", -9), r.get("B_sh", -9))
    return r
