"""Skaner strukturalny na świecach dziennych: wyzwalacz × zgodność z trendem × filtr × horyzont (dni). Wynik w ATR14 netto
(spread + 0,5 pipsa za noc). Statystyka z miesięcznych sum. Użycie: python d1scan.py yahoo|ej"""
import sys

import lib
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "yahoo"
HS = (1, 2, 3, 5, 10, 20)
CUT_A = pd.Timestamp("2012-01-01"); CUT_IS = pd.Timestamp("2019-05-10")


def load_all():
    D = {}
    for p in lib.PAIRS:
        if SRC == "yahoo":
            d = pd.read_parquet(__import__("os").path.join(__import__("os").environ.get("D1_FIXED", "../rsi_d1/d1_fixed"), f"{p}.parquet"))
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


def build():
    D = load_all()
    idx = sorted(set.union(*[set(d.index) for d in D.values()]))
    idx = pd.DatetimeIndex(idx)
    C = pd.DataFrame({p: np.log(D[p].close).reindex(idx).ffill(limit=3) for p in lib.PAIRS})
    V = pd.read_csv(lib.HERE / "vix.csv", parse_dates=["DATE"]).set_index("DATE")["CLOSE"]
    vx = V.reindex(V.index.union(idx)).ffill().reindex(idx)
    vchg = vx.pct_change()
    out = {}
    for p in lib.PAIRS:
        d = D[p].copy()
        o, h, l, c = d.open, d.high, d.low, d.close
        a = lib.atr(d, 14)
        b, q = p[:3], p[3:]
        T = {}
        for k in (1, 2, 3, 5, 10, 20, 60, 120, 250):
            v = (c - c.shift(k)) / (a * np.sqrt(k))
            T[f"mom{k}"] = np.sign(v)
            T[f"mom{k}_duzy"] = np.sign(v).where(v.abs() > 1.0, 0)
        st = streak(c.diff())
        for n in (2, 3, 4):
            T[f"seria{n}"] = np.sign(st).where(st.abs() >= n, 0)
        for n, lv in ((2, 10), (5, 25), (14, 30)):
            r = rsi(c, n)
            T[f"rsi{n}"] = (r > 100 - lv).astype(int) - (r < lv).astype(int)
        for n in (20, 60, 250):
            hh, ll = h.rolling(n).max(), l.rolling(n).min()
            pos = (c - ll) / (hh - ll) - 0.5
            T[f"skraj{n}"] = np.sign(pos).where(pos.abs() > 0.4, 0)
        for n in (20, 50, 200):
            T[f"sma{n}"] = np.sign(c - c.rolling(n).mean())
        for n in (20, 55):
            T[f"wybicie{n}"] = (c > h.rolling(n).max().shift(1)).astype(int) - (c < l.rolling(n).min().shift(1)).astype(int)
        rng = (h - l).replace(0, np.nan)
        clv = (c - l) / rng
        lw, uw = (np.minimum(o, c) - l) / rng, (h - np.maximum(o, c)) / rng
        T["pin"] = ((lw > 0.6) & (clv > 0.6)).astype(int) - ((uw > 0.6) & (clv < 0.4)).astype(int)
        body = c - o
        T["objecie"] = ((body > 0) & (c > np.maximum(o, c).shift(1)) & (o < np.minimum(o, c).shift(1))).astype(int) - \
                       ((body < 0) & (c < np.minimum(o, c).shift(1)) & (o > np.maximum(o, c).shift(1))).astype(int)
        T["duza_swieca"] = np.sign(body).where(rng > 1.5 * a, 0)
        T["zamkniecie_skraj"] = (clv > 0.85).astype(int) - (clv < 0.15).astype(int)
        T["falszywe_wybicie"] = ((l < l.rolling(10).min().shift(1)) & (c > l.rolling(10).min().shift(1))).astype(int) - \
                                ((h > h.rolling(10).max().shift(1)) & (c < h.rolling(10).max().shift(1))).astype(int)
        Cx = C.reindex(d.index)
        for k in (1, 5, 20, 60):
            R = Cx - Cx.shift(k)
            usd = (-R["EURUSD"] + R["USDJPY"] - R["GBPUSD"] - R["AUDUSD"] + R["USDCHF"] + R["USDCAD"]) / 6
            s = {"USD": usd * 6 / 7}
            s["EUR"], s["GBP"], s["AUD"] = R["EURUSD"] + s["USD"], R["GBPUSD"] + s["USD"], R["AUDUSD"] + s["USD"]
            s["JPY"], s["CHF"], s["CAD"] = s["USD"] - R["USDJPY"], s["USD"] - R["USDCHF"], s["USD"] - R["USDCAD"]
            S = pd.DataFrame(s); S = S.sub(S.mean(axis=1), axis=0)
            rank = S.rank(axis=1)
            T[f"dolar{k}"] = T[f"wlasny{k}"] = pd.Series(0, index=d.index)
            if "USD" in (b, q):
                sgn = 1 if b == "USD" else -1
                other = q if b == "USD" else b
                T[f"dolar{k}"] = np.sign(S["USD"]) * sgn
                T[f"wlasny{k}"] = -np.sign(S[other] - S.drop(columns=["USD", other]).mean(axis=1)) * sgn
            T[f"skrajna_para{k}"] = ((rank[b] >= 6) & (rank[q] <= 2)).astype(int) - ((rank[b] <= 2) & (rank[q] >= 6)).astype(int)
            if k == 1:
                crowd = pd.concat([np.sign(R["USDJPY"]), np.sign(R["USDCHF"]), np.sign(R["USDCAD"]), -np.sign(R["EURUSD"]),
                                   -np.sign(R["GBPUSD"]), -np.sign(R["AUDUSD"])], axis=1).sum(axis=1).abs()
        for cc in ["USD", "EUR", "JPY", "GBP", "AUD", "CHF", "CAD"]:
            T[f"kup_{cc}"] = pd.Series((1 if b == cc else -1 if q == cc else 0), index=d.index)
        T = pd.DataFrame(T).fillna(0).astype(np.int8)
        tr = np.sign(c - c.rolling(200).mean()).fillna(0)
        M = {"brak": pd.Series(True, index=d.index)}
        vr = a / lib.atr(d, 100)
        M["zm_wysoka"], M["zm_niska"] = vr > 1.2, vr < 0.85
        nxt = pd.Series(d.index, index=d.index).shift(-1)
        dow = nxt.dt.dayofweek
        for i, nm in enumerate(["pon", "wt", "sr", "czw", "pt"]):
            M[f"wejscie_{nm}"] = dow == i
        cal = pd.Series(pd.bdate_range(d.index[0] - pd.Timedelta(days=40), d.index[-1] + pd.Timedelta(days=40)))
        rke = dict(zip(cal, cal.groupby(cal.dt.to_period("M")).rank(ascending=False)))
        rkb = dict(zip(cal, cal.groupby(cal.dt.to_period("M")).rank()))
        M["koniec_mies"] = nxt.map(rke) <= 2
        M["poczatek_mies"] = nxt.map(rkb) <= 3
        vxp, vcp = vx.reindex(d.index), vchg.reindex(d.index)
        M["vix_wysoki"], M["vix_niski"], M["vix_skok"], M["vix_spadek"] = vxp > 22, vxp < 14, vcp > 0.08, vcp < -0.06
        cr = crowd.reindex(d.index)
        M["dzien_dolarowy"], M["dzien_wlasny"] = cr >= 6, cr <= 2
        M = pd.DataFrame(M).fillna(False)
        pip = lib.PIP[p]
        e = o.shift(-1)
        G = {}
        gc = (d.gap_before > 0).cumsum()
        for h_ in HS:
            g = (c.shift(-h_) - e) / a
            g[(gc.shift(-h_) - gc) > 0] = np.nan
            g[(pd.Series(d.index, index=d.index).shift(-h_) - nxt).dt.days > h_ * 1.5 + 4] = np.nan
            G[h_] = g.clip(-6, 6)
        G = pd.DataFrame(G)
        cost = pd.DataFrame({h_: (lib.SPREAD[p] + 0.5 * h_) * pip / a for h_ in HS})
        per = np.where(d.index < CUT_A, "A", np.where(d.index < CUT_IS, "B", "O")) if SRC == "yahoo" else np.where(d.index < pd.Timestamp("2017-07-01"), "A", "B")
        month = (d.index.year - 1990) * 12 + d.index.month
        ok = a.notna() & (np.arange(len(d)) > 260)
        out[p] = (T[ok], tr[ok], M[ok], G[ok], cost[ok], per[ok.to_numpy()], month[ok.to_numpy()])
    return out


def run():
    B = build()
    tn, mn = list(B["EURUSD"][0].columns), list(B["EURUSD"][2].columns)
    modes = ("wszystkie", "z_trendem", "pod_trend")
    ncol = len(tn) * len(modes) * len(mn)
    nm = 12 * 40
    rows = []
    for h in HS:
        acc, cnt, cst = np.zeros((nm, ncol)), np.zeros((nm, ncol)), np.zeros((nm, ncol))
        pers = np.full(nm, "", dtype=object)
        for p, (T, tr, M, G, cost, per, month) in B.items():
            Tm = T.to_numpy().astype(float)
            trv = tr.to_numpy()[:, None]
            T3 = np.concatenate([Tm, np.where(Tm * trv > 0, Tm, 0), np.where(Tm * trv < 0, Tm, 0)], axis=1)
            SM = (T3[:, :, None] * M.to_numpy()[:, None, :]).reshape(len(T3), -1)
            g, k = G[h].to_numpy(), cost[h].to_numpy()
            ok = ~np.isnan(g)
            np.add.at(acc, month[ok], SM[ok] * g[ok, None])
            np.add.at(cnt, month[ok], np.abs(SM[ok]))
            np.add.at(cst, month[ok], np.abs(SM[ok]) * k[ok, None])
            pers[month[ok]] = per[ok]
        for pr in sorted(set(pers) - {""}):
            sel = pers == pr
            X, N, K = acc[sel], cnt[sel], cst[sel]
            n = N.sum(axis=0)
            t = X.mean(axis=0) / X.std(axis=0, ddof=1) * np.sqrt(len(X))
            gross, cc = X.sum(axis=0) / np.maximum(n, 1), K.sum(axis=0) / np.maximum(n, 1)
            for j in range(ncol):
                ti, rest = divmod(j, len(modes) * len(mn))
                # kolejność kolumn: [tryb][wyzwalacz][filtr]
            names = [(modes[mi], tn[ti], mn[fi]) for mi in range(len(modes)) for ti in range(len(tn)) for fi in range(len(mn))]
            for j, (mo, tt, ff) in enumerate(names):
                rows.append((h, tt, mo, ff, pr, n[j], gross[j], cc[j], t[j]))
    R = pd.DataFrame(rows, columns=["h", "wyzw", "tryb", "filtr", "per", "n", "brutto", "koszt", "t"])
    R.to_parquet(f"out/d1scan_{SRC}.parquet", index=False)
    print(len(R), R.groupby("per").size().to_dict())


if __name__ == "__main__":
    run()
