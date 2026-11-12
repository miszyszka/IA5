"""Poniedziałkowe odwrócenie: para rozciągnięta na zamknięciu piątku (16:00 NY) wraca w poniedziałek.
Sygnał z dziennych zamknięć liczonych z H1 o 16:00 NY. Wejście poniedziałek X:00 Londynu, wyjście Y godzin później."""
import sys

import lib
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "ej"
pd.set_option("display.width", 250)

def rsi(s, n):
    dlt = s.diff()
    up = dlt.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-dlt.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    return 100 - 100 / (1 + up / dn)

def prep(p):
    d = lib.add_time(lib.load(SRC, p))
    ny = d.index.tz_convert("America/New_York")
    d["nyday"] = ny.normalize().tz_localize(None)
    dc = d[d.h_ny <= 15].groupby("nyday").close.last()          # zamknięcie dnia = 16:00 NY (przed rolowaniem)
    dh, dl = d.groupby("nyday").high.max(), d.groupby("nyday").low.min()
    dc = dc[dc.index.dayofweek < 5]
    D = pd.DataFrame({"c": dc, "h": dh.reindex(dc.index), "l": dl.reindex(dc.index)})
    pc = D.c.shift(1)
    tr = np.maximum(D.h - D.l, np.maximum((D.h - pc).abs(), (D.l - pc).abs()))
    D["atr"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    D["rsi2"], D["rsi5"] = rsi(D.c, 2), rsi(D.c, 5)
    for k in (1, 2, 3, 5):
        D[f"mom{k}"] = (D.c - D.c.shift(k)) / (D.atr * np.sqrt(k))
    hh, ll = D.h.rolling(20).max(), D.l.rolling(20).min()
    D["pos20"] = (D.c - ll) / (hh - ll) - 0.5
    D["sma200"] = np.sign(D.c - D.c.rolling(200).mean())
    return d, D[D.index.dayofweek == 4]                           # piątki

TRIG = {
    "rsi2 10/90": lambda F: (F.rsi2 > 90).astype(int) - (F.rsi2 < 10).astype(int),
    "rsi2 20/80": lambda F: (F.rsi2 > 80).astype(int) - (F.rsi2 < 20).astype(int),
    "rsi2 35/65": lambda F: (F.rsi2 > 65).astype(int) - (F.rsi2 < 35).astype(int),
    "rsi5 25/75": lambda F: (F.rsi5 > 75).astype(int) - (F.rsi5 < 25).astype(int),
    "mom2>1": lambda F: np.sign(F.mom2).where(F.mom2.abs() > 1, 0),
    "mom3>0.5": lambda F: np.sign(F.mom3).where(F.mom3.abs() > 0.5, 0),
    "mom5>0.5": lambda F: np.sign(F.mom5).where(F.mom5.abs() > 0.5, 0),
    "mom3 znak": lambda F: np.sign(F.mom3),
    "piątek mom1>0.7": lambda F: np.sign(F.mom1).where(F.mom1.abs() > 0.7, 0),
    "skraj20": lambda F: np.sign(F.pos20).where(F.pos20.abs() > 0.4, 0),
}

def events(entry_h, hold):
    rows = []
    for p in lib.PAIRS:
        d, F = prep(p)
        lon = d.index.tz_convert("Europe/London")
        mon = np.flatnonzero(np.asarray(lon.dayofweek == 0) & (d.h_lon.to_numpy() == entry_h))
        ts = lib.epoch(d.index)
        o, c = d.open.to_numpy(), d.close.to_numpy()
        j = mon + hold - 1
        ok = j < len(d)
        mon, j = mon[ok], j[ok]
        ok = (ts[j] - ts[mon]) == (hold - 1) * 3600
        mon, j = mon[ok], j[ok]
        fri = pd.DatetimeIndex(lon[mon].tz_localize(None).normalize()) - pd.Timedelta(days=3)
        Tg = pd.DataFrame({nm: fn(F) for nm, fn in TRIG.items()})
        Tg["trend"], Tg["atr"] = F.sma200, F.atr / lib.PIP[p]
        X = Tg.reindex(fri).reset_index(drop=True)
        X["pair"], X["t"], X["gross"] = p, d.index[mon], (c[j] - o[mon]) / lib.PIP[p]
        rows.append(X.dropna(subset=["atr"]))
    E = pd.concat(rows, ignore_index=True)
    E["per"] = np.where(E.t < lib.CUT_AB, "A", "B") if SRC == "ej" else "C"
    return E


def stat(E, nm):
    out = {}
    for per, g in E.groupby("per"):
        s = -g[nm].fillna(0)                         # przeciw rozciągnięciu
        m = s != 0
        pn = (s * g.gross)[m] - g.pair[m].map(lib.SPREAD)
        wk = pn.groupby(g.t[m].dt.strftime("%G-%V")).sum()
        out[per] = (int(m.sum()), round(pn.mean(), 2), round(lib.tstat(wk), 1))
    return out

if __name__ == "__main__":
    for entry_h, hold in ((0, 21), (1, 20), (3, 18), (7, 9), (7, 14), (8, 13), (0, 45)):
        E = events(entry_h, hold)
        print(f"\nwejście pon {entry_h}:00 Londyn, trzymanie {hold} h — netto pips (n, śr., t tygodniowe)")
        for nm in TRIG:
            print(f"  {nm:<16}", stat(E, nm))
