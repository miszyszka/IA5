"""Wzmocnij / utnij: powrót RSI w trendzie na poprawionych zamknięciach D1. Wybór po min(Sharpe A, Sharpe B) — oba odcinki IS.
Użycie: python refine.py <katalog d1> [--oos]"""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import engine
from ia5 import indicators as ind
from ia5.config import PAIRS

DATA = Path(sys.argv[1])
SHOW_OOS = "--oos" in sys.argv
D = {f.stem: pd.read_parquet(f) for f in sorted(DATA.glob("*.parquet"))}
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
PRE = {}
for pair, df in D.items():
    s = df.close
    a = ind.adx(df, 14)
    PRE[pair] = {"P": engine.prepare(df), "c": s.to_numpy(), "sma200": ind.sma(s, 200).to_numpy(),
                 "rsi": {k: ind.rsi(s, k).to_numpy() for k in (3, 5, 14)}, "atr": ind.atr(df, 14).to_numpy(),
                 "di": (a.plus_di - a.minus_di).to_numpy(), "rng": (df.high - df.low).to_numpy()}


def streak(m):
    m = m.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def entries(x, trend, trig, floor14, rng_cut, di_cut):
    c = x["c"]
    with np.errstate(invalid="ignore"):
        if trend == "sma200":
            up, dn = c > x["sma200"], c < x["sma200"]
        else:                                           # momentum k dni + strona SMA200
            k = int(trend[3:])
            m = np.r_[np.full(k, np.nan), c[k:] - c[:-k]]
            up, dn = (m > 0) & (c > x["sma200"]), (m < 0) & (c < x["sma200"])
        n_, lvl = trig
        r = x["rsi"][n_]
        L, S = up & (r < lvl), dn & (r > 100 - lvl)
        if floor14 is not None:                         # utnij krach: RSI14 nie niżej niż floor14
            L &= x["rsi"][14] >= floor14
            S &= x["rsi"][14] <= 100 - floor14
        if rng_cut is not None:                         # utnij dzień-szok
            calm = x["rng"] < rng_cut * x["atr"]
            L &= calm
            S &= calm
        if di_cut is not None:                          # utnij, gdy DI mocno przeciw trendowi
            L &= x["di"] > -di_cut
            S &= x["di"] < di_cut
    sig = L.astype(int) - S.astype(int)
    zl = up & (r < lvl)
    zs = dn & (r > 100 - lvl)
    st = np.where(sig > 0, streak(zl), np.where(sig < 0, streak(zs), 0))
    return sig, st


def run(spec, ex, pyr, weight):
    trend, trig, fl, rc, dc = spec
    rows = []
    for pair, x in PRE.items():
        sig, st = entries(x, trend, trig, fl, rc, dc)
        P = x["P"]
        ent = engine.find_entries(P, sig)
        ent = ent[~ent.atr14.isna()].reset_index(drop=True)
        if ent.empty:
            continue
        i = ent.signal_i.to_numpy()
        d = ent.dir.to_numpy()
        e2 = ent.copy()
        e2["tp_px"] = x["c"][i] + d * ex[2] * x["atr"][i] if ex[2] else np.nan
        e2["sl_px"] = x["c"][i] - d * ex[1] * x["atr"][i] if ex[1] else np.nan
        res = engine.simulate(P, e2, engine.Exit("level", cap=ex[0]), pair)
        xi = res.exit_i.to_numpy(float).copy()
        xi[engine.data_cancel(P, i, ent.entry_i.to_numpy(), xi)] = np.nan
        keep = engine.no_overlap(ent.entry_i.to_numpy(), xi, d, pyr)
        pip = PAIRS[pair].pip
        net = res.pips_gross.to_numpy() - PAIRS[pair].spread_pips - 0.5 * np.nan_to_num(res.nights.to_numpy())
        w = np.clip(st[i], 1, 3).astype(float) if weight == "seria" else np.ones(len(i))
        rows.append(pd.DataFrame({"pair": pair, "ts": ent.entry_ts.to_numpy()[keep], "xts": res.exit_ts.to_numpy()[keep],
                                  "ret": (w * net * pip / ent.entry_px.to_numpy())[keep],
                                  "r": (net / (x["atr"][i] / pip))[keep], "w": w[keep]}))
    return pd.concat(rows) if rows else pd.DataFrame()


def stats(t):
    if len(t) < 20:
        return {"n": len(t)}
    t = t.assign(ret=t.ret / t.w.mean())
    mon = pd.to_datetime(t.xts, unit="s").dt.to_period("M")
    ms = t.groupby(mon).ret.sum()
    ms = ms.reindex(pd.period_range(ms.index.min(), ms.index.max(), freq="M"), fill_value=0)
    q = ms.groupby(ms.index.asfreq("Q")).sum()
    y = ms.groupby(ms.index.year).sum()
    cum = ms.cumsum()
    pp = t.groupby("pair").ret.sum()
    return {"n": len(t), "n/r": round(len(t) / max(len(y), 1)), "r": round(t.r.mean(), 3),
            "sh": round(ms.mean() / ms.std() * np.sqrt(12), 2), "kw+": round((q > 0).mean(), 2), "lata+": round((y > 0).mean(), 2),
            "pary+": int((pp > 0).sum()), "dd%": round(100 * (cum - cum.cummax()).min(), 1), "sum%": round(100 * ms.sum(), 1)}


if __name__ == "__main__":
    specs = list(itertools.product(("sma200", "mom60", "mom120"), ((3, 15), (5, 20), (5, 25), (14, 40)), (None, 30),
                                   (None, 1.5), (None, 20)))
    exits = [(3, 0, 0), (5, 0, 0), (5, 1.5, 0), (5, 2, 2), (10, 2, 0)]
    out = []
    for spec in specs:
        for ex in exits:
            for pyr, wt in ((1, "stała"), (3, "seria")):
                t = run(spec, ex, pyr, wt)
                if t.empty:
                    continue
                row = {"trend": spec[0], "wyzw": f"RSI{spec[1][0]}<{spec[1][1]}", "dno14": spec[2], "zakres": spec[3], "di": spec[4],
                       "wyj": f"{ex[0]}d SL{ex[1]} TP{ex[2]}", "pyr": pyr, "waga": wt}
                for nm, m in (("A", t.ts < CUT_A), ("B", (t.ts >= CUT_A) & (t.ts < CUT_IS))):
                    row.update({f"{nm}_{k}": v for k, v in stats(t[m]).items()})
                if SHOW_OOS:
                    row.update({f"O_{k}": v for k, v in stats(t[t.ts >= CUT_IS]).items()})
                out.append(row)
    res = pd.DataFrame(out)
    res["min_sh"] = res[["A_sh", "B_sh"]].min(axis=1)
    res.to_csv(f"refine_{DATA.name}" + ("_oos" if SHOW_OOS else "") + ".csv", index=False)
    pd.set_option("display.width", 280)
    cols = [c for c in res.columns if not c.startswith("O_")]
    print(len(res))
    print(res[(res.A_n >= 200) & (res.B_n >= 150)].sort_values("min_sh", ascending=False)[cols].head(30).to_string())
