from load import *
df = load("EURUSD"); df = df[df.index.dayofweek < 5]
loc = df.index.tz_convert("Europe/London")
d = df.assign(h=loc.hour, day=loc.normalize())
def win(a, L):
    o = d[d.h == a].set_index("day").open; c = d[d.h == a + L - 1].set_index("day").close
    return ((c - o) / 1e-4).dropna()
print("== EURUSD short: netto pips/dzień (czas Londynu), połowa A ≤2017 | B ≥2018")
rows = []
for a in range(3, 11):
    row = {}
    for L in (2, 3, 4, 5, 6, 8):
        r = -win(a, L) - 0.9
        row[L] = f"{r[r.index.year<=2017].mean():+.1f}|{r[r.index.year>=2018].mean():+.1f}"
    rows.append(pd.Series(row, name=f"{a}:00"))
print(pd.DataFrame(rows).to_string())
r = -win(7, 6) - 0.9
asia = win(0, 7)
x = pd.DataFrame({"r": r, "asia": asia}).dropna()
x["q"] = pd.qcut(x.asia, 5, labels=False)
print("== wg ruchu EURUSD w Azji 00–07 Londyn (kwintyle, 0 = najmocniejszy spadek)")
print(x.groupby("q").agg(asia=("asia", "mean"), wynik=("r", "mean"), n=("r", "size")).round(2))
prev = (d.groupby("day").close.last().diff() / 1e-4).shift(1)
x["prev"] = prev.reindex(x.index)
x["pq"] = pd.qcut(x.prev, 5, labels=False)
print("== wg zmiany poprzedniego dnia"); print(x.groupby("pq").agg(prev=("prev", "mean"), wynik=("r", "mean")).round(2))
atr = (d.high - d.low).rolling(24 * 20).mean() / 1e-4
a7 = atr[d.h == 7]; a7.index = d.day[d.h == 7]
x["vol"] = a7.reindex(x.index); x["vq"] = pd.qcut(x.vol, 4, labels=False)
print("== wg zmienności (śr. zakres świecy z 20 dni)"); print(x.groupby("vq").agg(vol=("vol", "mean"), wynik=("r", "mean")).round(2))
print("== miesiąc"); print(x.r.groupby(x.index.month).mean().round(2).to_dict())
print("== dzień tyg."); print(x.r.groupby(x.index.dayofweek).mean().round(2).to_dict())
