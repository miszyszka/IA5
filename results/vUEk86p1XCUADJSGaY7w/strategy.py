HYPOTHESIS = """W wyraźnym trendzie H1 (EMA200 zmienia się o więcej niż 0,25 ATR14 na 10 świec) gwałtowny ruch
przeciw trendowi, w którym RSI14 przebija 70 (trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada:
płynność wraca do kierunku trendu i cena cofa się o ok. 1,5 ATR. Im głębsza przesada, tym większa oczekiwana
korekta — stąd dokładanie z rosnącą wagą. Gdy przesada trwa 6 godzin, to już nie przesada, tylko zmiana trendu."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 (= 100 − 70)
RUN = 6             # tyle zamknięć z rzędu za poziomem = pomyłka → zamknięcie wszystkiego (wyjście rsi_streak)
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin (B11 wyłączone dla tej strategii)
EXITS = [
    # TP 1,5 × ATR14 od ceny wejścia (ATR ze świecy sygnału); seria 6 zamknięć RSI za 70/30 → wyjście na open
    # następnej świecy; limit 120 świec. Bez SL cenowego — rolę stopu pełni seria RSI.
    {"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120},
]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)       # nachylenie EMA200 na 10 świec, w ATR14
    up = (slope > 0.25).to_numpy()                          # wyraźnie rośnie
    down = (slope < -0.25).to_numpy()                       # wyraźnie spada
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record = 0, 0, 0, 0.0
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
                # dokładamy, gdy RSI pobije rekord z ostatniego wejścia; nie w 6. świecy serii (wtedy wszystko się zamyka)
                if deeper and count < MAX_POS and streak < RUN:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec wybicia
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record = -1, 1, 1, x
            out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record = 1, 1, 1, x
            out[t] = weight(100 - LEVEL - x)
    return out