"""Siatka składników na świecach dziennych: rozciągnięcie × trend × dzień wejścia × zmienność × liczba dni.
Każda reguła liczona osobno w A (≤2011), B (2012–2019-05) na Yahoo i w EA, EB na niezależnych danych brokera.
Odcinek O (OOS, po 2019-05-09) jest liczony do pliku, ale NIE jest czytany przed zamrożeniem projektu.
Użycie: python grid.py yahoo|ej"""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import itertools
import sys

import numpy as np
import pandas as pd

import glib

SRC = sys.argv[1]
B = glib.build(SRC)

TRIG = {}
for k in (0.0, 0.5, 1.0, 1.5, 2.0):
    TRIG[f"tydzien>{k}"] = lambda P, k=k: P.week(k)
for q in (0.7, 0.85):
    TRIG[f"tydzien_skraj{q}"] = lambda P, q=q: P.weekpos(q)
for n, lvs in ((2, (5, 10, 20, 30)), (3, (10, 15, 25)), (5, (20, 25, 30, 40)), (14, (30, 40))):
    for lv in lvs:
        TRIG[f"rsi{n}<{lv}"] = lambda P, n=n, lv=lv: P.rsi(n, lv)
for n, z in itertools.product((10, 20), (0.5, 1.0, 1.5, 2.0)):
    TRIG[f"boll{n}>{z}"] = lambda P, n=n, z=z: P.boll(n, z)
for k, thr in itertools.product((1, 2, 3, 5, 10, 20), (0.0, 0.5, 1.0, 1.5)):
    TRIG[f"mom{k}>{thr}"] = lambda P, k=k, thr=thr: P.mom(k, thr)
for n in (5, 10, 20, 60):
    TRIG[f"skraj{n}"] = lambda P, n=n: P.edge(n)
for n in (2, 3, 4):
    TRIG[f"seria{n}"] = lambda P, n=n: P.run(n)
for k in (1.0, 1.5, 2.0):
    TRIG[f"kelt>{k}"] = lambda P, k=k: P.kelt(k)
for k in (1.0, 2.0, 3.0):
    TRIG[f"miesiac>{k}"] = lambda P, k=k: P.month_move(k)
for n, lv, dd in ((5, 25, 2), (5, 25, 3), (5, 30, 2), (3, 15, 2), (2, 10, 2)):
    TRIG[f"rsi{n}<{lv}_dzien{dd}"] = lambda P, n=n, lv=lv, dd=dd: P.rsi_run(n, lv, dd)

TREND = ("brak", "sma200+", "sma200-", "sma50+", "sma50-", "mom120+", "mom120-")       # + ruch zgodny z trendem, − przeciw
DAYS = {"każdy": lambda P: np.ones(len(P.d), bool), "nie_pon": lambda P: (P.dow != 0).to_numpy()}
for i, nm in enumerate(("pon", "wt", "sr", "czw", "pt")):
    DAYS[nm] = lambda P, i=i: (P.dow == i).to_numpy()
for k in (1, 2, 3):
    DAYS[f"koniec{k}"] = lambda P, k=k: (P.from_end <= k).to_numpy()
    DAYS[f"poczatek{k}"] = lambda P, k=k: (P.from_start <= k).to_numpy()
VOL = {"brak": lambda P: np.ones(len(P.d), bool), "wysoka": lambda P: (P.vr > 1.2).to_numpy(), "niska": lambda P: (P.vr < 0.85).to_numpy(),
       "spokojny_dzien": lambda P: (P.rng < 1.5).to_numpy(), "szok": lambda P: (P.rng >= 1.5).to_numpy()}

rows = []
dn_, vn_ = list(DAYS), list(VOL)
NF, NH = len(dn_) * len(vn_), len(glib.HS)
PRE = {}
for p, P in B.items():
    ok = P.ok
    M = np.stack([DAYS[a](P) & VOL[b](P) for a in dn_ for b in vn_], axis=1)[ok].astype(np.float32)
    G = P.G.to_numpy()[ok]
    V = (~np.isnan(G)).astype(np.float32)
    mon = P.month[ok]
    st = np.flatnonzero(np.r_[True, mon[1:] != mon[:-1]])
    PRE[p] = dict(ok=ok, M=M, G=np.nan_to_num(G).astype(np.float32), V=V, K=(np.nan_to_num(P.cost.to_numpy()[ok]) * V).astype(np.float32),
                  st=st, mid=mon[st], per=P.per[ok][st])
pers = np.full(glib.NM, "", dtype=object)
for x in PRE.values():
    pers[x["mid"]] = x["per"]
names = [(a, b, h) for a in dn_ for b in vn_ for h in glib.HS]
for ti, (tn, tf) in enumerate(TRIG.items()):
    base = {p: tf(P).to_numpy().astype(np.float32) for p, P in B.items()}
    for tr in TREND:
        X, N = np.zeros((glib.NM, NF * NH), np.float32), np.zeros((glib.NM, NF * NH), np.float32)
        for p, P in B.items():
            x = PRE[p]
            t = base[p]
            if tr != "brak":
                s = P.trend(tr[:-1]).to_numpy()
                t = np.where(t * s * (1 if tr[-1] == "+" else -1) > 0, t, 0).astype(np.float32)
            t = -t[x["ok"]]                                           # transakcja PRZECIW rozciągnięciu; znak wyniku mówi resztę
            A = t[:, None] * x["M"]
            pnl = (A[:, :, None] * x["G"][:, None, :] - np.abs(A)[:, :, None] * x["K"][:, None, :]).reshape(len(t), -1)
            cnt = (np.abs(A)[:, :, None] * x["V"][:, None, :]).reshape(len(t), -1)
            X[x["mid"]] += np.add.reduceat(pnl, x["st"], axis=0)
            N[x["mid"]] += np.add.reduceat(cnt, x["st"], axis=0)
        for pr in sorted(set(pers) - {""}):
            sel = pers == pr
            x_, n = X[sel].astype(float), N[sel].sum(axis=0)
            sd = x_.std(axis=0, ddof=1)
            with np.errstate(invalid="ignore", divide="ignore"):
                t_ = x_.mean(axis=0) / sd * np.sqrt(len(x_))
                net = x_.sum(axis=0) / n
            ny = len(x_) // 12
            lata = (x_[: ny * 12].reshape(ny, 12, -1).sum(axis=1) > 0).mean(axis=0) if ny else np.full(x_.shape[1], np.nan)
            cum = np.cumsum(x_, axis=0)
            dd = (cum - np.maximum.accumulate(cum, axis=0)).min(axis=0)
            for j, (a, b, h) in enumerate(names):
                rows.append((tn, tr, a, b, h, pr, n[j], net[j], t_[j], t_[j] / np.sqrt(len(x_) / 12), lata[j], dd[j]))
    print(ti + 1, len(TRIG), tn, len(rows), flush=True)
R = pd.DataFrame(rows, columns=["wyzw", "trend", "dzien", "zm", "h", "per", "n", "net", "t", "sh", "lata", "dd"])
R.to_parquet(paths.DATA / "out" / f"grid_{SRC}.parquet", index=False)
print("reguł:", len(R) // R.per.nunique(), "wierszy:", len(R))
