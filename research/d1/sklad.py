import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import itertools, sys
import pandas as pd
import comp
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
MS = [("mom", 2, 0.75), ("mom", 3, 0.75), ("mom", 5, 0.5), ("rsi", 5, 30), ("boll", 20, 1.5)]
PON = dict(ms=MS, min=2, skala=False, calm=None, dni=1, w=1.0)
TR = dict(rsi=(5, 25), od=2, sma=200, calm=1.5, dni=3, w=1.0, bez_pon=False)
MI = dict(m=("mom", 10, 0.0), trend=200, ile=2, dni=2, calm=None, bez_pon=True, w=1.0)
rows = []
def add(nm, cfg, pyr):
    rows.append(comp.row(nm, comp.trades({**cfg, "zm": 0.006}, pyr)))
add("pon", {"pon": PON}, 1)
add("trend", {"trend": TR}, 3)
add("mies", {"mies": MI}, 3)
for wt, wm, pyr in itertools.product((0, 0.5, 1.0, 1.5), (0, 0.5, 1.0), (1, 2, 3)):
    if wt == 0 and wm == 0:
        continue
    cfg = {"pon": PON}
    if wt: cfg["trend"] = {**TR, "w": wt}
    if wm: cfg["mies"] = {**MI, "w": wm}
    add(f"pon1 + trend{wt} + mies{wm} pyr{pyr}", cfg, pyr)
R = pd.DataFrame(rows)
c = ["cfg", "A_n/r", "A_r", "A_sh", "A_lata+", "A_kw+", "A_dd/rok", "B_n/r", "B_r", "B_sh", "B_lata+", "B_kw+", "B_dd/rok", "min_sh"]
print(R[c].to_string(index=False))
