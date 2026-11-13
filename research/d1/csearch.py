"""Siatki składników strategii składanej, liczone silnikiem (comp.trades) — tylko odcinki A i B (IS). Użycie: python csearch.py pon|mies|trend"""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import itertools
import sys
from multiprocessing import Pool

import pandas as pd

import comp

WHICH = sys.argv[1]
ZM = 0.006


def grid():
    if WHICH == "pon":
        ms = [("mom", k, t) for k in (1, 2, 3, 5) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
        ms += [("rsi", 2, l) for l in (5, 10, 15, 20, 30)] + [("rsi", 3, l) for l in (10, 15, 20, 25)] + [("rsi", 5, l) for l in (20, 25, 30, 40)]
        ms += [("boll", n, z) for n in (10, 20) for z in (0.5, 1.0, 1.5)]
        for m, calm, dni in itertools.product(ms, (None, 1.25, 1.5, 2.0), (1, 2)):
            yield {"pon": dict(m=m, calm=calm, dni=dni, w=1.0), "zm": ZM}, 1
    elif WHICH == "mies":
        ms = [("mom", k, t) for k in (5, 10, 15, 20) for t in (0.0, 0.25, 0.5, 1.0)] + [("boll", 20, z) for z in (0.5, 1.0, 1.5)]
        ms += [("rsi", 14, 40), ("rsi", 14, 45), ("rsi", 5, 30), ("rsi", 5, 40)]
        for m, tr, ile, dni, calm, bp in itertools.product(ms, (None, 20, 50, 200), (1, 2, 3), (1, 2, 3), (None, 1.5), (False, True)):
            yield {"mies": dict(m=m, trend=tr, ile=ile, dni=dni, calm=calm, bez_pon=bp, w=1.0), "zm": ZM}, 3
    else:
        rs = [(2, 10), (2, 15), (3, 15), (3, 20), (5, 20), (5, 25), (5, 30), (14, 35), (14, 40)]
        for r, od, sma, calm, dni, bp, pyr in itertools.product(rs, (1, 2, 3), (100, 200), (None, 1.5, 2.0), (2, 3, 4, 5), (False, True), (1, 3)):
            yield {"trend": dict(rsi=r, od=od, sma=sma, calm=calm, dni=dni, bez_pon=bp, w=1.0), "zm": ZM}, pyr


def one(job):
    cfg, pyr = job
    r = comp.row(str({k: v for k, v in cfg[WHICH].items() if k != "w"}), comp.trades(cfg, pyr))
    r["pyr"] = pyr
    r.update({f"p_{k}": str(v) for k, v in cfg[WHICH].items()})
    return r


if __name__ == "__main__":
    jobs = list(grid())
    print(WHICH, len(jobs), flush=True)
    with Pool(2) as pool:
        rows = pool.map(one, jobs, chunksize=20)
    pd.DataFrame(rows).to_parquet(paths.DATA / "out" / f"cs_{WHICH}.parquet", index=False)
    print("gotowe", len(rows))
