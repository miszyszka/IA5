"""Fixing londyński 16:00: ruch przed fixingiem cofa się po nim — najmocniej w końcu miesiąca (przepływy funduszy)."""
import sys

import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "ej"

def month_rank(d):
    days = pd.Series(sorted(d.fxday.unique()))
    cal = pd.bdate_range(days.iloc[0] - pd.Timedelta(days=40), days.iloc[-1] + pd.Timedelta(days=40))   # kalendarz, nie dane
    cs = pd.Series(cal)
    rk = cs.groupby(cs.dt.to_period("M")).rank(ascending=False)
    return d.fxday.map(dict(zip(cal, rk)))

def sig(k, thr, last, eh=16):
    def f(d, p):
        v = (d.close - d.close.shift(k)) / (d.atr * np.sqrt(k))
        s = -np.sign(v).where(v.abs() > thr, 0)
        s = s.where(d.h_lon.shift(-1) == eh, 0)
        if last:
            rk = month_rank(d)
            s = s.where((rk >= last[0]) & (rk <= last[1]), 0)
        return s
    return f

