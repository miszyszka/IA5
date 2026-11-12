"""Skaner hipotez strukturalnych na H1: reguła = wyzwalacz (kierunek) × filtr × godzina wejścia (Londyn) × horyzont.
Wszystkie pary razem; statystyka z tygodniowych sum pipsów. A = odkrycie, B = potwierdzenie (albo C = Yahoo).
Użycie: python scan.py ej|yh"""
import sys

import lib
import numpy as np
import pandas as pd

SRC = sys.argv[1] if len(sys.argv) > 1 else "ej"
ENTRY_H = (0, 1, 3, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 19)
HS = (1, 2, 4, 8, 24, 72)
CCY = ["USD", "EUR", "JPY", "GBP", "AUD", "CHF", "CAD"]


def vix_known():
    v = pd.read_csv(lib.HERE / "vix.csv", parse_dates=["DATE"]).set_index("DATE")["CLOSE"]
    return pd.DataFrame({"vix": v, "vix_chg": v.pct_change(), "vix_ma": v / v.rolling(20).mean() - 1})


def build():
    F = {p: lib.add_time(lib.load(SRC, p)) for p in lib.PAIRS}
    # wspólna siatka czasu → siła walut
    idx = sorted(set.intersection(*[set(d.index) for d in F.values()]))
    idx = pd.DatetimeIndex(idx)
    C = pd.DataFrame({p: np.log(F[p].close.reindex(idx)) for p in lib.PAIRS})
    V = vix_known()
    out = {}
    for p in lib.PAIRS:
        d = F[p].reindex(idx).copy()
        pip = lib.PIP[p]
        a = lib.atr(d, 24)
        d["atr"] = a
        o, c, h, l = d.open, d.close, d.high, d.low
        T = {}
        for k in (1, 4, 8, 24, 48, 120, 240, 480):
            v = (c - c.shift(k)) / (a * np.sqrt(k))
            T[f"mom{k}"] = np.sign(v)
            T[f"mom{k}_duzy"] = np.sign(v).where(v.abs() > 1.0, 0)
        # sesje (czas Londynu), wartości znane po ich zakończeniu
        lonh = d.h_lon
        def sess(a_, b_):
            m = lonh.between(a_, b_ - 1)
            g = d[m].groupby("londay")
            r = (g.close.last() - g.open.first())
            s = pd.Series(r.reindex(d.londay).to_numpy(), index=d.index)
            return np.sign(s).where(lonh >= b_, 0)         # tylko po zakończeniu sesji, tego samego dnia
        T["sesja_azja"], T["sesja_lon_rano"], T["sesja_ny_rano"] = sess(0, 7), sess(7, 12), sess(12, 16)
        g = d.groupby("fxday")
        dayo, dayc = g.open.first(), g.close.last()
        prev = (dayc - dayo).shift(1)
        T["wczoraj"] = np.sign(pd.Series(prev.reindex(d.fxday).to_numpy(), index=d.index))
        T["od_otwarcia_dnia"] = np.sign(c - pd.Series(dayo.reindex(d.fxday).to_numpy(), index=d.index))
        wk = d.fxday.dt.to_period("W-SUN")
        wo = d.groupby(wk).open.first()
        T["od_otwarcia_tyg"] = np.sign(c - pd.Series(wo.reindex(wk).to_numpy(), index=d.index))
        for n in (24, 120, 480):
            hh, ll = h.rolling(n).max(), l.rolling(n).min()
            pos = (c - ll) / (hh - ll) - 0.5
            T[f"skraj{n}"] = np.sign(pos).where(pos.abs() > 0.4, 0)
        dh = g.high.cummax(); dl = g.low.cummin()
        adr = (g.high.max() - g.low.min()).rolling(20).mean().shift(1)
        used = (dh - dl) / pd.Series(adr.reindex(d.fxday).to_numpy(), index=d.index)
        T["zakres_wyczerpany"] = T["od_otwarcia_dnia"].where(used > 1.0, 0)
        br = (c - o) / a
        T["szok"] = np.sign(br).where(br.abs() > 2.5, 0)
        # siła walut: USD względem koszyka 6 walut; własny ruch waluty nie-USD
        b, q = p[:3], p[3:]
        for k in (4, 24, 120, 480):
            R = C - C.shift(k)
            usd = (-R["EURUSD"] + R["USDJPY"] - R["GBPUSD"] - R["AUDUSD"] + R["USDCHF"] + R["USDCAD"]) / 6   # > 0: dolar się umacnia
            s = {"USD": usd * 6 / 7}
            s["EUR"], s["GBP"], s["AUD"] = R["EURUSD"] + s["USD"], R["GBPUSD"] + s["USD"], R["AUDUSD"] + s["USD"]
            s["JPY"], s["CHF"], s["CAD"] = s["USD"] - R["USDJPY"], s["USD"] - R["USDCHF"], s["USD"] - R["USDCAD"]
            S = pd.DataFrame(s)
            S = S.sub(S.mean(axis=1), axis=0)
            rank = S.rank(axis=1)
            T[f"dolar{k}"] = T[f"wlasny{k}"] = pd.Series(0, index=d.index)
            if "USD" in (b, q):
                sgn = 1 if b == "USD" else -1
                other = q if b == "USD" else b
                T[f"dolar{k}"] = np.sign(S["USD"]) * sgn                       # kierunek pary zgodny z ruchem dolara
                T[f"wlasny{k}"] = -np.sign(S[other] - (S.drop(columns=["USD", other]).mean(axis=1))) * sgn   # ruch waluty nie-USD wobec reszty
            T[f"skrajna_para{k}"] = ((rank[b] >= 6) & (rank[q] <= 2)).astype(int) - ((rank[b] <= 2) & (rank[q] >= 6)).astype(int)
        for cc in CCY:                                                          # stały kierunek: kup walutę cc
            T[f"kup_{cc}"] = pd.Series((1 if b == cc else -1 if q == cc else 0), index=d.index)
        T = pd.DataFrame(T).fillna(0).astype(np.int8)
        # filtry
        M = {"brak": pd.Series(True, index=d.index)}
        vr = a / lib.atr(d, 480)
        M["zmiennosc_wysoka"], M["zmiennosc_niska"] = vr > 1.3, vr < 0.8
        tr = np.sign(c - c.rolling(480).mean())
        M["trend_w_gore"], M["trend_w_dol"] = tr > 0, tr < 0
        M["pon"], M["pt"], M["wt_czw"] = d.dow == 0, d.dow == 4, d.dow.between(1, 3)
        days = pd.Series(sorted(d.fxday.unique()))
        per = days.dt.to_period("M")
        rk_end = days.groupby(per).rank(ascending=False)
        rk_beg = days.groupby(per).rank()
        me = dict(zip(days, rk_end)); mb = dict(zip(days, rk_beg))
        M["koniec_mies"] = d.fxday.map(me) <= 2
        M["ostatni_dzien"] = d.fxday.map(me) == 1
        M["poczatek_mies"] = d.fxday.map(mb) <= 2
        dom = d.index.tz_convert("Asia/Tokyo").day
        M["gotobi"] = pd.Series(np.isin(dom, [5, 10, 15, 20, 25, 30]), index=d.index)
        M["nfp"] = (d.dow == 4) & (d.fxday.dt.day <= 7)
        vk = V.reindex(pd.DatetimeIndex(days)).ffill()
        vk = V.shift(1).reindex(V.index.union(pd.DatetimeIndex(days))).ffill().reindex(pd.DatetimeIndex(days))   # VIX z poprzedniej sesji USA
        vx = d.fxday.map(dict(zip(days, vk.vix.to_numpy()))); vc = d.fxday.map(dict(zip(days, vk.vix_chg.to_numpy())))
        M["vix_wysoki"], M["vix_niski"] = vx > 20, vx < 14
        M["vix_skok"], M["vix_spadek"] = vc > 0.07, vc < -0.05
        usd24 = (C - C.shift(24))
        ud = ((-usd24["EURUSD"] + usd24["USDJPY"] - usd24["GBPUSD"] - usd24["AUDUSD"] + usd24["USDCHF"] + usd24["USDCAD"]) / 6).abs()
        thr = ud.rolling(480 * 3).quantile(0.75)
        M["dzien_dolarowy"], M["dzien_spokojny"] = ud > thr, ud < ud.rolling(480 * 3).quantile(0.4)
        M = pd.DataFrame(M).fillna(False)
        # wyniki: wejście open t+1, wyjście close t+h; zamknięcie w godzinie rolowania (16–17 NY) zastąpione ostatnim czystym
        cx = c.where(~d.h_ny.isin([16, 17])).ffill()
        e = o.shift(-1)
        G = pd.DataFrame({h_: (cx.shift(-h_) - e) / pip for h_ in HS})
        ts = pd.Series(lib.epoch(idx), index=idx)
        for h_ in HS:
            G.loc[(ts.shift(-h_) - ts.shift(-1)) > (h_ + 60) * 3600, h_] = np.nan
        if "gap_before" in d:
            gc = (d.gap_before.fillna(0) > 0).cumsum()
            for h_ in HS:
                G.loc[(gc.shift(-h_) - gc) > 0, h_] = np.nan
        d["entry_h"] = d.h_lon.shift(-1)
        d["week"] = (d.fxday.shift(-1) - pd.Timestamp("2012-01-01")).dt.days // 7
        out[p] = (d, T, M, G)
    return out


def run():
    B = build()
    tn, mn = list(B["EURUSD"][1].columns), list(B["EURUSD"][2].columns)
    weeks = np.arange(0, 800)
    rows = []
    for eh in ENTRY_H:
        acc = {h: np.zeros((len(weeks), len(tn) * len(mn))) for h in HS}
        cnt = {h: np.zeros((len(weeks), len(tn) * len(mn))) for h in HS}
        cost = {h: np.zeros((len(weeks), len(tn) * len(mn))) for h in HS}
        for p, (d, T, M, G) in B.items():
            m = (d.entry_h == eh).to_numpy() & d.week.notna().to_numpy()
            Tm, Mm, Gm, wk = T.to_numpy()[m].astype(float), M.to_numpy()[m], G.to_numpy()[m], d.week.to_numpy()[m].astype(int)
            SM = (Tm[:, :, None] * Mm[:, None, :]).reshape(len(Tm), -1)
            for j, h in enumerate(HS):
                g = Gm[:, j]
                ok = ~np.isnan(g) & (wk >= 0) & (wk < len(weeks))
                X = SM[ok] * g[ok, None]
                A_ = np.abs(SM[ok])
                np.add.at(acc[h], wk[ok], X)
                np.add.at(cnt[h], wk[ok], A_)
                np.add.at(cost[h], wk[ok], A_ * lib.SPREAD[p])
        wstart = pd.Timestamp("2012-01-01", tz="UTC") + pd.to_timedelta(weeks * 7, unit="D")
        for h in HS:
            for per, sel in (("A", wstart < lib.CUT_AB), ("B", wstart >= lib.CUT_AB)) if SRC == "ej" else (("C", np.ones(len(weeks), bool)),):
                X, N, K = acc[h][sel], cnt[h][sel], cost[h][sel]
                live = N.sum(axis=1) > 0
                X, N, K = X[live], N[live], K[live]
                n = N.sum(axis=0)
                mu = X.mean(axis=0); sd = X.std(axis=0, ddof=1)
                t = mu / sd * np.sqrt(len(X))
                gross = X.sum(axis=0) / np.maximum(n, 1)
                sp = K.sum(axis=0) / np.maximum(n, 1)
                for k in range(len(n)):
                    rows.append((eh, h, tn[k // len(mn)], mn[k % len(mn)], per, n[k], gross[k], sp[k], t[k]))
    R = pd.DataFrame(rows, columns=["godz", "h", "wyzw", "filtr", "per", "n", "brutto", "spread", "t"])
    R.to_parquet(f"out/scan_{SRC}.parquet", index=False)
    print(len(R), "wierszy;", R.groupby("per").size().to_dict())


if __name__ == "__main__":
    run()
