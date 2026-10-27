"""Badanie 1: sezonowość w ciągu doby. Dla każdego okna [od, od+len) godzin UTC: średni ruch (pips) od open świecy `od`
do close świecy `od+len-1`, osobno 2012–2017 (odkrycie) i 2018–2022 (potwierdzenie)."""
from load import *
rows = []
for p, df in all_pairs().items():
    df = df[df.index.dayofweek < 5]
    day = df.index.floor("D")
    for a in range(0, 22):
        for L in (1, 2, 3, 4, 6, 8, 10, 12):
            b = a + L - 1
            if b > 21:
                continue
            o = df.open[df.index.hour == a]; o.index = o.index.floor("D")
            c = df.close[df.index.hour == b]; c.index = c.index.floor("D")
            r = ((c - o).dropna() / PIP[p])
            r = r[r.abs() < 500]
            for name, part in (("A", r[r.index.year <= 2017]), ("B", r[r.index.year >= 2018])):
                rows.append(dict(pair=p, a=a, L=L, part=name, mean=part.mean(), t=part.mean() / (part.std() / np.sqrt(len(part))), n=len(part)))
res = pd.DataFrame(rows).pivot_table(index=["pair", "a", "L"], columns="part", values=["mean", "t"]).reset_index()
res.columns = ["pair", "a", "L", "mA", "mB", "tA", "tB"]
res["spread"] = res.pair.map(SPREAD)
res.to_csv("r1.csv", index=False)
ok = res[(np.sign(res.mA) == np.sign(res.mB)) & (res.tA.abs() > 2.5) & (res.tB.abs() > 2) & (res.mB.abs() > res.spread * 1.5)]
print(ok.sort_values("tA", key=abs, ascending=False).round(2).to_string())
