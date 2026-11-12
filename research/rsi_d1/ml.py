"""Czy cokolwiek w cechach dnia przewiduje zwrot 1–10 dni na D1? Uczenie na A (≤2011), sprawdzenie na B (2012–2019-05).
Lustrzane uzupełnienie: każdy dzień także jako short (cechy kierunkowe ze zmienionym znakiem) — model nie może nauczyć się dryfu."""
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import indicators as ind
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

D = {f.stem: pd.read_parquet(f) for f in sorted(Path(__import__("os").environ.get("D1", "d1_fixed")).glob("*.parquet"))}
CUT_A = pd.Timestamp("2012-01-01", tz="UTC").timestamp()
CUT_IS = pd.Timestamp("2019-05-09 18:00", tz="UTC").timestamp()
fr = []
for pair, df in D.items():
    s, o, h, l = df.close, df.open, df.high, df.low
    atr = ind.atr(df, 14)
    f = pd.DataFrame({"pair": pair, "ts": df.ts.to_numpy()})
    for k in (2, 5, 14):
        f[f"rsi{k}"] = (ind.rsi(s, k) - 50).to_numpy()            # kierunkowe: znak = strona
    for k in (1, 3, 5, 10, 20, 60, 120, 250):
        f[f"mom{k}"] = ((s - s.shift(k)) / atr).to_numpy()
    for k in (20, 50, 200):
        f[f"dsma{k}"] = ((s - ind.sma(s, k)) / atr).to_numpy()
    a = ind.adx(df, 14)
    f["di"] = (a.plus_di - a.minus_di).to_numpy()
    f["adx"] = a.adx.to_numpy()                                    # bezkierunkowe
    f["volr"] = (atr / ind.atr(df, 100)).to_numpy()
    f["rng"] = ((h - l) / atr).to_numpy()
    f["clv"] = (((s - l) / (h - l)).fillna(0.5) - 0.5).to_numpy()  # kierunkowe
    f["body"] = ((s - o) / atr).to_numpy()
    f["gap"] = ((o - s.shift(1)) / atr).to_numpy()
    hh, ll = ind.highest(h, 250), ind.lowest(l, 250)
    f["pos250"] = ((s - ll) / (hh - ll) - 0.5).to_numpy()
    f["dow"] = pd.to_datetime(df.ts.shift(-1), unit="s").dt.dayofweek.to_numpy()  # dzień wejścia
    f["dom"] = pd.to_datetime(df.ts.shift(-1), unit="s").dt.day.to_numpy()
    c = s.to_numpy()
    e = np.r_[o.to_numpy()[1:], np.nan]
    gapc = np.r_[0, np.cumsum(df.gap_before.to_numpy() > 0)]
    n = len(df)
    for k in (1, 3, 5, 10):
        x = np.r_[c[k:], np.full(k, np.nan)]
        r = (x - e) / atr.to_numpy()
        ii = np.arange(n)
        ok = (ii + k < n) & (gapc[np.minimum(ii + k + 1, n)] - gapc[np.minimum(ii + 1, n)] == 0)
        f[f"y{k}"] = np.where(ok, np.clip(r, -5, 5), np.nan)
    fr.append(f.iloc[250:])
t = pd.concat(fr, ignore_index=True).dropna()
t["period"] = np.where(t.ts < CUT_A, "A", np.where(t.ts < CUT_IS, "B", "OOS"))
DIRF = [c for c in t.columns if c.startswith(("rsi", "mom", "dsma")) or c in ("di", "clv", "body", "gap", "pos250")]
NEUF = ["adx", "volr", "rng", "dow", "dom"]
FEAT = DIRF + NEUF


def mirror(x):
    m = x.copy()
    m[DIRF] = -m[DIRF]
    for k in (1, 3, 5, 10):
        m[f"y{k}"] = -m[f"y{k}"]
    return pd.concat([x, m], ignore_index=True)


A, B = t[t.period == "A"], t[t.period == "B"]
Am = mirror(A)
for k in (1, 3, 5, 10):
    for name, model in (("ridge", Ridge(alpha=100.0)),
                        ("gbm", HistGradientBoostingRegressor(max_depth=3, learning_rate=0.03, max_iter=300, min_samples_leaf=400,
                                                              l2_regularization=10.0))):
        model.fit(Am[FEAT], Am[f"y{k}"])
        p = model.predict(B[FEAT])
        ic = spearmanr(p, B[f"y{k}"]).statistic
        # handel: kierunek = znak prognozy, tylko 20% najsilniejszych prognoz; zwrot w ATR minus ~0,03 ATR spreadu
        thr = np.quantile(np.abs(p), 0.8)
        sel = np.abs(p) >= thr
        pnl = np.sign(p[sel]) * B[f"y{k}"].to_numpy()[sel] - 0.03
        print(f"y{k} {name}: IC na B {ic:+.4f}; top20%: n={sel.sum()} śr. {pnl.mean():+.4f} ATR, t={pnl.mean() / pnl.std() * np.sqrt(sel.sum() / k):+.2f}")
        if name == "ridge":
            co = pd.Series(model.coef_, index=FEAT)
            print("   najważniejsze (ridge, standaryzacja przybliżona):",
                  (co * Am[FEAT].std()).sort_values(key=abs, ascending=False).head(8).round(4).to_dict())
t.to_parquet("ml_feats.parquet", index=False)
