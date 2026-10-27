"""Badanie 2: dolar w porannej sesji europejskiej. Kierunek „long USD”: EURUSD/GBPUSD/AUDUSD short, USDJPY/USDCHF/USDCAD long.
Okno w czasie Londynu (07:00–13:00 lokalnie) vs stałe UTC; rozbicie na lata, dni tygodnia i ruch w sesji azjatyckiej."""
from load import *
USD_SIGN = {"EURUSD": -1, "GBPUSD": -1, "AUDUSD": -1, "USDJPY": 1, "USDCHF": 1, "USDCAD": 1}

def window(df, start, length, tz):
    loc = df.index.tz_convert(tz)
    d = df.copy(); d["h"] = loc.hour; d["day"] = loc.floor("D") if False else loc.normalize()
    o = d[d.h == start].set_index("day").open
    c = d[d.h == start + length - 1].set_index("day").close
    return (c - o).dropna()

data = all_pairs()
out = {}
for tz, start in (("UTC", 6), ("Europe/London", 7)):
    per = {}
    for p, s in USD_SIGN.items():
        df = data[p]; df = df[df.index.dayofweek < 5]
        r = window(df, start, 6, tz) * s / PIP[p] - SPREAD[p]
        per[p] = r
    t = pd.DataFrame(per)
    out[tz] = t
    print(f"== okno {start}:00–{start+6}:00 {tz}, netto po spreadzie, pips/dzień")
    print(t.groupby(t.index.year).mean().round(2).assign(koszyk=lambda x: x.mean(axis=1).round(2)).to_string())
    b = t.mean(axis=1)
    print("koszyk: śr", round(b.mean(), 2), "t", round(b.mean() / b.std() * np.sqrt(b.count()), 2), "dni", b.count())
t = out["Europe/London"]
print("== dzień tygodnia (koszyk)"); print(t.mean(axis=1).groupby(t.index.dayofweek).agg(["mean", "count"]).round(2))
