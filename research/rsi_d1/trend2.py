"""Cofnięcie RSI w trendzie 6-miesięcznym: siatka mała, ocena osobno w A (≤2011) i B (2012–2019-05). OOS nie liczony."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import engine
from ia5 import indicators as ind
from ia5.config import PAIRS

D = {f.stem: pd.read_parquet(f) for f in sorted(Path(__import__("os").environ.get("D1", "d1_fixed")).glob("*.parquet"))}
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
SHOW_OOS = "--oos" in sys.argv
PRE = {}
for pair, df in D.items():
    s = df.close
    a = ind.adx(df, 14)
    PRE[pair] = {"P": engine.prepare(df), "c": s.to_numpy(), "rsi14": ind.rsi(s, 14).to_numpy(), "rsi5": ind.rsi(s, 5).to_numpy(),
                 "sma200": ind.sma(s, 200).to_numpy(), "atr": ind.atr(df, 14).to_numpy(),
                 "di": (a.plus_di - a.minus_di).to_numpy(), "rng": (df.high - df.low).to_numpy(),
                 "ts": df.ts.to_numpy()}


def entries2(x, kind, mom, par, rng_cut):
    """kind: pb = cofnięcie RSI14 do strefy par=(lo,hi) w trendzie (stan); rsi_up = RSI14 przebija par w górę w trendzie;
    trend = pierwszy dzień, gdy warunek trendu staje się prawdziwy."""
    c, r = x["c"], x["rsi14"]
    m = np.r_[np.full(mom, np.nan), c[mom:] - c[:-mom]]
    with np.errstate(invalid="ignore"):
        up = (m > 0) & (c > x["sma200"])
        dn = (m < 0) & (c < x["sma200"])
        if kind == "pb":
            lo, hi = par
            L, S = up & (r < hi) & (r >= lo), dn & (r > 100 - hi) & (r <= 100 - lo)
        elif kind == "rsi_up":
            pr = np.r_[np.nan, r[:-1]]
            L, S = up & (r > par) & (pr <= par), dn & (r < 100 - par) & (pr >= 100 - par)
        else:
            pu, pd_ = np.r_[False, up[:-1]], np.r_[False, dn[:-1]]
            L, S = up & ~pu, dn & ~pd_
        if rng_cut is not None:
            calm = x["rng"] < rng_cut * x["atr"]
            L &= calm
            S &= calm
    return (L.astype(int) - S.astype(int))


def entries(x, mom, lo, hi, mode, di_cut, rng_cut):
    c, r = x["c"], x["rsi14"]
    m = np.r_[np.full(mom, np.nan), c[mom:] - c[:-mom]]
    with np.errstate(invalid="ignore"):
        up = (m > 0) & (c > x["sma200"])
        dn = (m < 0) & (c < x["sma200"])
        zl = (r < hi) & (r >= lo)
        zs = (r > 100 - hi) & (r <= 100 - lo)
        if mode == "zdarzenie":                 # pierwszy dzień w strefie cofnięcia
            pl = np.r_[False, zl[:-1]]
            ps = np.r_[False, zs[:-1]]
            zl, zs = zl & ~pl, zs & ~ps
        L, S = up & zl, dn & zs
        if di_cut is not None:                   # odetnij, gdy DI mocno przeciw trendowi (trend się łamie)
            L &= x["di"] > -di_cut
            S &= x["di"] < di_cut
        if rng_cut is not None:                  # odetnij dzień-szok (zakres > k × ATR)
            calm = x["rng"] < rng_cut * x["atr"]
            L &= calm
            S &= calm
    return (L.astype(int) - S.astype(int))


def evaluate(sig_by_pair, ex, pyr):
    rows = []
    for pair, sig in sig_by_pair.items():
        x = PRE[pair]
        P = x["P"]
        ent = engine.find_entries(P, sig)
        ent = ent[~ent.atr14.isna()].reset_index(drop=True)
        if ent.empty:
            continue
        i = ent.signal_i.to_numpy()
        d = ent.dir.to_numpy()
        kind, a, cap = ex[:3]
        e2 = ent.copy()
        if kind == "trail":
            res = engine.simulate(P, e2, engine.Exit("trail", n=14, sl=a, trail=ex[3], cap=cap), pair)
        else:
            e2["tp_px"] = np.nan
            e2["sl_px"] = x["c"][i] - d * a * x["atr"][i] if kind == "sl" else np.nan
            res = engine.simulate(P, e2, engine.Exit("level", cap=cap), pair)
        xi = res.exit_i.to_numpy(float).copy()
        xi[engine.data_cancel(P, i, ent.entry_i.to_numpy(), xi)] = np.nan
        keep = engine.no_overlap(ent.entry_i.to_numpy(), xi, d, pyr)
        pip = PAIRS[pair].pip
        net = res.pips_gross.to_numpy() - PAIRS[pair].spread_pips - 0.5 * np.nan_to_num(res.nights.to_numpy())
        ret = net * pip / ent.entry_px.to_numpy()
        rows.append(pd.DataFrame({"pair": pair, "ts": ent.entry_ts.to_numpy()[keep], "xts": res.exit_ts.to_numpy()[keep],
                                  "ret": ret[keep], "r": (net / (x["atr"][i] / pip))[keep],
                                  "w": np.clip(0.006 / (x["atr"][i] / x["c"][i]), 0.25, 4)[keep]}))
    return pd.concat(rows) if rows else pd.DataFrame()


def stats(t, vol=False):
    if vol and len(t):
        t = t.assign(ret=t.ret * t.w / t.w.mean())
    if len(t) < 10:
        return {"n": len(t)}
    mon = pd.to_datetime(t.xts, unit="s").dt.to_period("M")
    ms = t.groupby(mon).ret.sum()
    ms = ms.reindex(pd.period_range(ms.index.min(), ms.index.max(), freq="M"), fill_value=0)
    q = ms.groupby(ms.index.asfreq("Q")).sum()
    y = ms.groupby(ms.index.year).sum()
    pp = t.groupby("pair").ret.sum()
    return {"n": len(t), "n/r": round(len(t) / max(len(y), 1), 1), "r": round(t.r.mean(), 3),
            "sh": round(ms.mean() / ms.std() * np.sqrt(12), 2), "kw+": round((q > 0).mean(), 2), "lata+": round((y > 0).mean(), 2),
            "pary+": int((pp > 0).sum()), "sum%": round(100 * ms.sum(), 1)}


grid = [("pb", m, p, rc) for m in (120, 250) for p in ((30, 45), (35, 50)) for rc in (None, 1.5)]
grid += [("rsi_up", m, p, rc) for m in (120, 250) for p in (55, 60, 65) for rc in (None, 1.5)]
grid += [("trend", m, 0, None) for m in (60, 120, 250)]
exits = [("czas", 0, 20), ("czas", 0, 40), ("czas", 0, 60), ("sl", 3, 40), ("trail", 2, 120, 3), ("trail", 3, 120, 4),
         ("trail", 3, 240, 5)]
out = []
for (kind, mom, par, rc) in grid:
    sigs = {p: entries2(x, kind, mom, par, rc) for p, x in PRE.items()}
    for ex in exits:
        t = evaluate(sigs, ex, 1)
        if t.empty:
            continue
        for vol in (False, True):
            A = stats(t[t.ts < CUT_A], vol)
            B = stats(t[(t.ts >= CUT_A) & (t.ts < CUT_IS)], vol)
            row = {"wejście": kind, "mom": mom, "par": str(par), "rng": rc, "wyjście": "/".join(map(str, ex)), "waga_zm": vol,
                   **{f"A_{k}": v for k, v in A.items()}, **{f"B_{k}": v for k, v in B.items()}}
            if SHOW_OOS:
                row.update({f"O_{k}": v for k, v in stats(t[t.ts >= CUT_IS], vol).items()})
            out.append(row)
res = pd.DataFrame(out)
res.to_csv("trend2" + ("_oos" if SHOW_OOS else "") + ".csv", index=False)
pd.set_option("display.width", 260)
res["min_sh"] = res[["A_sh", "B_sh"]].min(axis=1)
print(len(res))
print(res.sort_values("min_sh", ascending=False).head(35).to_string())
