HYPOTHESIS = """FX-POWRÓT v2 (pomysł z 20.10.2026, reguły z IA4 sekcja 7b). Po gwałtownym impulsie w górę (zamknięcie ≥ 2 × ATR100
wyżej niż poprzednie) kurs często cofa się w stronę ceny sprzed impulsu. Pierwsza czerwona świeca w ciągu 3 świec
po impulsie pokazuje, że kupujący się wyczerpali — short z celem w połowie drogi od szczytu do bazy, bez stopu,
limit 60 świec.
Różnice wobec oryginału (ograniczenia IA5): 8 par zamiast 10; warunek „open wejścia ≥ baza + 0,5 ATR” sprawdzany na
zamknięciu świecy sygnału (open następnej nie jest znany w chwili sygnału); TP jako poziom ceny P − ½(P − B) silnik
na razie nie obsługuje — wyjścia przybliżone przez TP w wielokrotnościach ATR14 (patrz EXITS)."""

import numpy as np

HOURS = False   # okno z reguł strategii: świeca sygnału zaczyna się 07–16 UTC (zamiast okna 07–17 czasu polskiego)

# Bez SL (jak w oryginale), limit 60 świec. Wariant „czas” = trzymanie do 60. świecy; warianty ATR = przybliżenie
# celu „połowa drogi powrotu” (impuls ≥ 2 × ATR100 ≈ 3–4 × ATR14, połowa drogi ≈ 1–2 × ATR14).
EXITS = [{"kind": "time", "n": 60, "cap": 60}] + [{"kind": "atr", "n": 14, "tp": tp, "cap": 60} for tp in (1.0, 1.5, 2.0, 3.0)]

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