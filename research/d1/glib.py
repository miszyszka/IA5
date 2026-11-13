"""Wspólne dla rundy D1 (D-070): świece dzienne (Yahoo po naprawie zamknięć D-068 albo niezależne dane brokera złożone z H1),
cechy pary z własnych świec, zwroty netto w ATR dla wyjścia po h dniach na zamknięciu, statystyka z miesięcznych sum."""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import lib

HS = (1, 2, 3, 4, 5, 10)
CUT_A, CUT_IS = pd.Timestamp("2012-01-01"), pd.Timestamp("2019-05-10")
EJ_CUT = pd.Timestamp("2017-07-01")
D1_DIR = paths.DATA / "d1_v2"
NM = 12 * 40


def load(src):
    D = {}
    for p in lib.PAIRS:
        if src == "yahoo":
            d = pd.read_parquet(D1_DIR / f"{p}.parquet")
            d.index = pd.to_datetime(d.ts, unit="s", utc=True).dt.tz_convert("Europe/London").dt.normalize().dt.tz_localize(None)
        else:
            h = lib.add_time(lib.load_ej(p))
            g = h.groupby("londay")
            d = pd.DataFrame({"open": g.open.first(), "high": g.high.max(), "low": g.low.min(), "close": g.close.last(), "n": g.size()})
            d = d[(d.index.dayofweek < 5) & (d.n >= 12)]
            d["gap_before"] = 0
        D[p] = d[["open", "high", "low", "close", "gap_before"]]
    return D


def rsi(s, n):
    dlt = s.diff()
    up = dlt.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-dlt.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)


def streak(x):
    s = np.sign(x).fillna(0)
    grp = (s != s.shift()).cumsum()
    return s * (s.groupby(grp).cumcount() + 1)


def sgn(v, thr=0.0):
    """Znak rozciągnięcia: +1 gdy v > thr, −1 gdy v < −thr."""
    return ((v > thr).astype(np.int8) - (v < -thr).astype(np.int8)).fillna(0).astype(np.int8)


class Pair:
    """Cechy jednej pary. Wszystko liczone na zamknięciu dnia i (znane przed wejściem na open dnia i+1)."""

    def __init__(self, p, d, src):
        self.p, self.d = p, d
        o, h, l, c = d.open, d.high, d.low, d.close
        self.a = a = lib.atr(d, 14)
        self.c = c
        day = pd.Series(d.index, index=d.index)
        nxt = day.shift(-1)
        self.dow = nxt.dt.dayofweek                                      # dzień tygodnia WEJŚCIA
        cal = pd.Series(pd.bdate_range(d.index[0] - pd.Timedelta(days=40), d.index[-1] + pd.Timedelta(days=40)))
        self.from_end = nxt.map(dict(zip(cal, cal.groupby(cal.dt.to_period("M")).rank(ascending=False))))   # 1 = ostatni dzień roboczy
        self.from_start = nxt.map(dict(zip(cal, cal.groupby(cal.dt.to_period("M")).rank())))
        self.vr = a / lib.atr(d, 100)
        self.sma = {n: c.rolling(n).mean() for n in (20, 50, 100, 200)}
        self.rng = (h - l) / a
        pip = lib.PIP[p]
        e = o.shift(-1)
        gc = (d.gap_before > 0).cumsum()
        G = {}
        for h_ in HS:
            g = (c.shift(-h_) - e) / a
            g[(gc.shift(-h_) - gc) > 0] = np.nan
            g[(day.shift(-h_) - nxt).dt.days > h_ * 1.5 + 4] = np.nan
            G[h_] = g.clip(-6, 6)
        self.G = pd.DataFrame(G)
        self.cost = pd.DataFrame({h_: (lib.SPREAD[p] + 0.5 * h_) * pip / a for h_ in HS})
        if src == "yahoo":
            self.per = np.where(d.index < CUT_A, "A", np.where(d.index < CUT_IS, "B", "O"))
        else:
            self.per = np.where(d.index < EJ_CUT, "EA", "EB")
        self.month = np.asarray((d.index.year - 1990) * 12 + d.index.month)
        self.ok = (a.notna() & (np.arange(len(d)) > 260)).to_numpy()
        self._wk = day.dt.to_period("W-FRI")
        self._mo = day.dt.to_period("M")

    # ---- rozciągnięcia (znak = kierunek dotychczasowego ruchu) ----
    def week(self, k):
        d, c = self.d, self.c
        wopen = d.open.groupby(self._wk).transform("first")
        return sgn((c - wopen) / self.a, k)

    def weekpos(self, q):
        d = self.d
        wh, wl = d.high.groupby(self._wk).cummax(), d.low.groupby(self._wk).cummin()
        return sgn((self.c - wl) / (wh - wl).replace(0, np.nan) - 0.5, q - 0.5)

    def month_move(self, k):
        mopen = self.d.open.groupby(self._mo).transform("first")
        return sgn((self.c - mopen) / self.a, k)

    def rsi(self, n, lv):
        return sgn(rsi(self.c, n) - 50, 50 - lv)

    def boll(self, n, z):
        c = self.c
        return sgn((c - c.rolling(n).mean()) / c.rolling(n).std(), z)

    def mom(self, k, thr):
        c = self.c
        return sgn((c - c.shift(k)) / (self.a * np.sqrt(k)), thr)

    def edge(self, n, q=0.9):
        d = self.d
        hh, ll = d.high.rolling(n).max(), d.low.rolling(n).min()
        return sgn((self.c - ll) / (hh - ll) - 0.5, q - 0.5)

    def run(self, n):
        st = streak(self.c.diff())
        return sgn(st, n - 0.5)

    def kelt(self, k, span=20):
        c = self.c
        return sgn((c - c.ewm(span=span, adjust=False).mean()) / self.a, k)

    def rsi_run(self, n, lv, day_):
        r = rsi(self.c, n)
        lo, hi = (r < lv), (r > 100 - lv)
        sl = lo.groupby((~lo).cumsum()).cumsum()
        sh = hi.groupby((~hi).cumsum()).cumsum()
        return ((hi & (sh >= day_)).astype(np.int8) - (lo & (sl >= day_)).astype(np.int8)).astype(np.int8)

    def trend(self, kind):
        c = self.c
        if kind.startswith("sma"):
            return np.sign(c - self.sma[int(kind[3:])]).fillna(0)
        k = int(kind[3:])
        return np.sign(c - c.shift(k)).fillna(0)


def build(src):
    D = load(src)
    return {p: Pair(p, D[p], src) for p in lib.PAIRS}


class Acc:
    """Suma miesięczna (ATR netto), liczba i koszt — dla wielu reguł naraz."""

    def __init__(self):
        self.x, self.n, self.per = np.zeros(NM), np.zeros(NM), np.full(NM, "", dtype=object)

    def add(self, P, t, h, w=None):
        """t: kierunek transakcji (−1/0/+1) na dniu sygnału; w: waga (domyślnie 1)."""
        t = np.asarray(t, float)
        g, k = P.G[h].to_numpy(), P.cost[h].to_numpy()
        m = P.ok & (t != 0) & ~np.isnan(g)
        if not m.any():
            return
        ww = np.ones(m.sum()) if w is None else np.asarray(w, float)[m]
        self.x += np.bincount(P.month[m], ww * (t[m] * g[m] - k[m]), NM)
        self.n += np.bincount(P.month[m], np.ones(m.sum()), NM)
        self.per[P.month[P.ok]] = P.per[P.ok]

    def stats(self):
        out = {}
        for pr in sorted(set(self.per) - {""}):
            s = self.per == pr
            x, n = self.x[s], self.n[s].sum()
            if n < 30 or x.std() == 0:
                out[pr] = dict(n=int(n))
                continue
            yrs = x[: len(x) // 12 * 12].reshape(-1, 12).sum(axis=1) if len(x) >= 12 else np.array([x.sum()])
            cum = np.cumsum(x)
            out[pr] = dict(n=int(n), net=x.sum() / n, t=x.mean() / x.std(ddof=1) * np.sqrt(len(x)),
                           sh=x.mean() / x.std(ddof=1) * np.sqrt(12), lata=float((yrs > 0).mean()),
                           dd=float((cum - np.maximum.accumulate(cum)).min()), suma=float(x.sum()))
        return out
