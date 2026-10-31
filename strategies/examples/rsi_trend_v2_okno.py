HYPOTHESIS = """Ten sam wariant co najlepszy w „RSI 2” (EMA200, nachylenie 0,15 ATR, bez filtra szoku, bez stopu cenowego),
policzony w oknie handlu 07:00–17:00 czasu polskiego (B11), gdy spready są najniższe. To sprawdzian kosztów,
nie nowa optymalizacja: jeśli przewaga zostaje w oknie, nie wynika z wejść w nocy i przy rolowaniu (22–01),
gdzie realny spread jest wielokrotnie większy niż w tabeli. Wariant wybrany po obejrzeniu wyników — prób łącznie 26."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5
EMA = 200
SLOPE = 0.15        # „wyraźny trend”: zmiana EMA200 na 10 świec > 0,15 × ATR14

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
# HOURS nie ustawione → domyślne okno 07:00–17:00 czasu polskiego (B11); wyjście o dowolnej porze

EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120}]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, EMA)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)
    up = (slope > SLOPE).to_numpy()
    down = (slope < -SLOPE).to_numpy()
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
                if deeper and count < MAX_POS and streak < RUN:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec epizodu
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record = -1, 1, 1, x
            out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record = 1, 1, 1, x
            out[t] = weight(100 - LEVEL - x)
    return out
