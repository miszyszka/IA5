HYPOTHESIS = """Jak w wersji 1: w wyraźnym trendzie H1 gwałtowny ruch przeciw trendowi, w którym RSI14 przebija 70
(trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada, po której cena cofa się o ok. 1,5 ATR.
Wersja 2 (po wyniku wersji 1 na Yahoo — OOS tej wersji nie jest czysty, prób łącznie 1 + 24):
1) Największe straty wersji 1 to nie przesady, tylko SZOKI informacyjne (np. 1.08.2025 13:00 UTC, dane z rynku pracy
   USA): jedna świeca o zakresie kilku ATR to nowa cena, a nie przesada — filtr „szok” pomija taki epizod.
2) Seria RSI zamyka stratę dopiero po 6 godzinach; w tym czasie cena potrafiła odejść o 100+ pipsów — stop cenowy
   2 / 3 × ATR ucina ten ogon (wariant bez stopu zostaje do porównania).
3) Więcej wejść: łagodniejszy próg „wyraźnego trendu” (0,15 ATR) i krótsza średnia (EMA100)."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin, jak w wersji 1

PARAMS = {
    "ema": [100, 200],              # średnia trendu
    "nachylenie": [0.15, 0.25],     # „wyraźny trend”: zmiana EMA na 10 świec > tyle × ATR14 (wersja 1: 0,25)
    "szok": [0, 3.0],               # 0 = bez filtra; 3.0 = pomiń epizod, gdy świeca przebicia ma zakres > 3 × ATR14
}

# TP 1,5 × ATR14; seria 6 zamknięć RSI za 70/30 → wyjście na open następnej; limit 120 świec;
# stop cenowy: brak (jak wersja 1) / 2 / 3 × ATR14 od ceny wejścia
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120, **({"sl": sl} if sl else {})}
         for sl in (0, 2.0, 3.0)]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3 (jak w wersji 1)."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, p["ema"])
    atr = ind.atr(df, 14)
    slope = (ema - ema.shift(10)) / atr                     # nachylenie EMA na 10 świec, w ATR14
    up = (slope > p["nachylenie"]).to_numpy()
    down = (slope < -p["nachylenie"]).to_numpy()
    rng = ((df.high - df.low) / atr.shift(1)).to_numpy()    # zakres świecy względem ATR sprzed niej
    shock = rng > p["szok"] if p["szok"] else np.zeros(len(df), bool)
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record, skip = 0, 0, 0, 0.0, False
    for t in range(1, len(r)):
        x, prev = r[t], r[t - 1]
        if np.isnan(x) or np.isnan(prev):
            side = 0
            continue
        if side != 0:
            beyond = x > LEVEL if side < 0 else x < 100 - LEVEL
            if beyond:                                      # przesada trwa: ta sama „seria”
                streak += 1
                deeper = x > record if side < 0 else x < record
                if deeper and count < MAX_POS and streak < RUN and not skip:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec epizodu
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record, skip = -1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record, skip = 1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = weight(100 - LEVEL - x)
    return out
