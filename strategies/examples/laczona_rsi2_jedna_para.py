HYPOTHESIS = """Część RSI strategii łączonej „RSI 2 + Powrót” (D-050). Logika RSI 2 bez zmian (RSI14 przebija 70/30 przeciw
wyraźnemu trendowi H1 = chwilowa przesada; dokładanie do 5 pozycji w jednej parze; wyjście TP 1,5 × ATR14 albo seria
6 zamknięć RSI za 70/30, bez stopu, max 120 świec), wariant #12 — najlepszy w IS wersji 2 (EMA200, nachylenie 0,15,
bez filtra szoku). Nowe: naraz otwarta jest najwyżej JEDNA para (seria dokładania w niej to jedna „transakcja”);
gdy kilka par daje sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS wersji 2 (PAIR_RANK).
OOS nie jest czysty (wariant i ranking z danych, na których oglądano wersję 2)."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin, jak w wersji 1

PARAMS = {"ema": [200], "nachylenie": [0.15], "szok": [0]}   # wariant #12 wersji 2

MAX_PAIRS = 1   # D-050: najwyżej jedna para z otwartymi pozycjami naraz
# ranking par: średni zysk w IS wersji 2 (pipsy na transakcję), od najlepszej
PAIR_RANK = ["USDCHF", "AUDUSD", "EURJPY", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "EURGBP"]

# TP 1,5 × ATR14; seria 6 zamknięć RSI za 70/30 → wyjście na open następnej; limit 120 świec; bez stopu (#12)
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120}]


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
