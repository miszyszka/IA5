HYPOTHESIS = """Część Powrót strategii łączonej „RSI 2 + Powrót” (D-050). Reguły FX-POWRÓT v2 bez zmian (impuls ≥ 2 × ATR100,
pierwsza czerwona w ciągu 3 świec, short, bez stopu, max 60 świec, jedna pozycja na parę). Wyjście: TP 1,5 × ATR14 —
najlepsze w IS spośród przybliżeń celu „połowa drogi”. Nowe: naraz otwarta jest najwyżej JEDNA para; gdy kilka par daje
sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS (PAIR_RANK, liczone 2026-11-03 na IS)."""

import numpy as np

HOURS = False   # okno z reguł strategii: świeca sygnału zaczyna się 07–16 UTC (zamiast okna 07–17 czasu polskiego)

MAX_PAIRS = 1   # D-050: najwyżej jedna para z otwartą pozycją naraz
# ranking par: średni zysk w IS (pipsy na transakcję, wyjście TP 1,5 × ATR14), od najlepszej
PAIR_RANK = ["USDJPY", "GBPUSD", "USDCHF", "USDCAD", "EURJPY", "EURUSD", "AUDUSD", "EURGBP"]

EXITS = [{"kind": "atr", "n": 14, "tp": 1.5, "cap": 60}]   # TP 1,5 × ATR14, bez SL, max 60 świec

SPREAD = {"EURUSD": 0.9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7, "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0,
          "EURJPY": 2.1}


def signals(df, p, ind):
    pair = df.attrs.get("pair", "")
    pip = 0.01 if "JPY" in pair else 0.0001
    spread = SPREAD.get(pair, 2.0) * pip
    o, h, c = df.open.to_numpy(), df.high.to_numpy(), df.close.to_numpy()
    atr = ind.atr(df, 100).shift(1).to_numpy()          # ATR100 sprzed świecy
    hour = df.index.hour.to_numpy()                      # UTC
    n = len(c)
    out = np.zeros(n, np.int8)
    base, peak, last_imp, active = 0.0, 0.0, -1, False
    for t in range(1, n):
        a = atr[t]
        if np.isnan(a):
            continue
        if c[t] - c[t - 1] >= 2 * a:                     # świeca impulsu
            if not active:
                active, base, peak = True, c[t - 1], h[t]
            peak = max(peak, h[t])
            last_imp = t
            continue
        if not active:
            continue
        peak = max(peak, h[t])
        if c[t] <= base or t - last_imp > 3:             # impuls wygasł
            active = False
            continue
        if c[t] < o[t] and 7 <= hour[t] <= 16:           # pierwsza czerwona w ciągu 3 świec
            tp = peak - 0.5 * (peak - base)
            if c[t] >= base + 0.5 * a and c[t] - tp >= max(spread, 0.1 * a):
                out[t] = -1
            active = False                               # tylko pierwsza czerwona
    return out