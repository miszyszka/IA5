import pandas as pd
import s5_monday as S

S.TRIG = {f"rsi2 {a}/{100-a}": (lambda a: (lambda F: (F.rsi2 > 100 - a).astype(int) - (F.rsi2 < a).astype(int)))(a) for a in (5, 10, 15, 20, 25, 30)}
rows = []
for eh in (0, 1, 2):
    for hold in (6, 12, 20, 30, 44):
        E = S.events(eh, hold)
        for nm in S.TRIG:
            st = S.stat(E, nm)
            rows.append({"wejście": eh, "h": hold, "próg": nm[5:], **{f"{p}_{k}": v for p, x in st.items() for k, v in zip(("n", "netto", "t"), x)}})
R = pd.DataFrame(rows)
R.to_csv(f"out/s5b_{S.SRC}.csv", index=False)
pd.set_option("display.width", 200)
if S.SRC == "ej":
    R["min_t"] = R[["A_t", "B_t"]].min(axis=1)
    print(R[R.wejście == 1].to_string(index=False))
    print("średnie min_t wg godziny wejścia:", R.groupby("wejście").min_t.mean().round(2).to_dict(), " wg trzymania:", R.groupby("h").min_t.mean().round(2).to_dict())
else:
    print(R[R.wejście == 1].to_string(index=False))
