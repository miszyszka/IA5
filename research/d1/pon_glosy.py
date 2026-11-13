import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import itertools
import pandas as pd
import comp
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 90)
M = [("mom", 2, 0.75), ("mom", 3, 0.75), ("mom", 5, 0.5), ("rsi", 5, 30), ("boll", 20, 1.5), ("rsi", 2, 20), ("boll", 10, 1.0)]
rows = []
for ms, mn, sk, calm in itertools.product((M[:5], M[:4], M, M[1:5], [M[1], M[2], M[4]]), (1, 2, 3), (False, True), (None, 2.0)):
    if mn > len(ms):
        continue
    cfg = {"pon": dict(ms=ms, min=mn, skala=sk, calm=calm, dni=1, w=1.0), "zm": 0.006}
    r = comp.row(f"{len(ms)} miar {[m[0]+str(m[1]) for m in ms]} min{mn} skala{int(sk)} calm{calm}", comp.trades(cfg, 1))
    rows.append(r)
R = pd.DataFrame(rows)
print(R.sort_values("min_sh", ascending=False)[["cfg", "A_n/r", "A_r", "A_sh", "A_lata+", "A_kw+", "B_n/r", "B_r", "B_sh", "B_lata+", "B_kw+", "min_sh"]].head(25).to_string(index=False))
print(R.min_sh.describe().round(2).to_dict())
