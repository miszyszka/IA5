import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import itertools, sys
import pandas as pd
import comp
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
MS = [("mom", 2, 0.75), ("mom", 3, 0.75), ("mom", 5, 0.5), ("rsi", 5, 30), ("boll", 20, 1.5)]
PON = dict(ms=MS, min=2, skala=False, calm=None, dni=1, w=1.0)
TR = dict(rsi=(5, 25), od=2, sma=200, calm=1.5, dni=3, w=0.5, bez_pon=False)
MI = dict(m=("mom", 10, 0.0), trend=200, ile=2, dni=2, calm=None, bez_pon=True, w=0.5)
BASE = {"pon": PON, "trend": TR, "mies": MI, "zm": 0.006}
rows = []
def add(nm, cfg, pyr=3):
    rows.append(comp.row(nm, comp.trades(cfg, pyr)))
add("baza", BASE)
add("bez skalowania zmiennością", {**BASE, "zm": None})
for sl in (1.5, 2.0, 3.0):
    add(f"SL {sl} ATR", {**BASE, "sl": sl})
for tp in (0.5, 1.0, 1.5):
    add(f"TP {tp} ATR", {**BASE, "tp": tp})
add("TP 1 + SL 2", {**BASE, "tp": 1.0, "sl": 2.0})
for mn in (1, 3):
    add(f"pon min głosów {mn}", {**BASE, "pon": {**PON, "min": mn}})
add("pon skala głosami", {**BASE, "pon": {**PON, "skala": True}})
add("pon calm 2", {**BASE, "pon": {**PON, "calm": 2.0}})
add("trend od 3", {**BASE, "trend": {**TR, "od": 3}})
add("trend 4 dni", {**BASE, "trend": {**TR, "dni": 4}})
add("trend bez pon", {**BASE, "trend": {**TR, "bez_pon": True}})
add("mies trend 50", {**BASE, "mies": {**MI, "trend": 50}})
add("mies bez trendu", {**BASE, "mies": {**MI, "trend": None}})
add("mies także pon", {**BASE, "mies": {**MI, "bez_pon": False}})
R = pd.DataFrame(rows)
c = ["cfg", "A_n/r", "A_r", "A_sh", "A_lata+", "A_kw+", "A_dd/rok", "B_n/r", "B_r", "B_sh", "B_lata+", "B_kw+", "B_dd/rok", "min_sh"]
print(R[c].to_string(index=False))
