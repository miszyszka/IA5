HYPOTHESIS = """Wersja 3 „RSI 2”: to samo co wersja 2 (RSI14 przebija 70/30 przeciw wyraźnemu trendowi H1 = chwilowa
przesada, cena cofa się o ok. 1,5 ATR; dokładanie do 5 pozycji, wyjście TP 1,5 ATR albo seria RSI), ale BEZ USD/CAD
i EUR/GBP. Powód: to pary z najwyższym spreadem względem zwykłego ruchu godzinowego (EUR/GBP: spread 1,7 pipsa przy
ATR14 ok. 7 pipsów; USD/CAD: 2,0 pipsa) — cofnięcie o 1,5 ATR zostawia tam najmniej po kosztach; w wersji 2 obie były
najsłabsze także w IS (średnio +0,9 i +1,9 pipsa na transakcję wobec +5–12 na pozostałych).
Uwaga: pary wybrane po obejrzeniu wyników wersji 2, także OOS — OOS tej wersji nie jest czysty (prób łącznie 1 + 24 + 24);
rozstrzyga forward test."""

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


SKIP_PAIRS = ("USDCAD", "EURGBP")   # wersja 3: te pary pomijamy


def signals(df, p, ind):
    if df.attrs.get("pair") in SKIP_PAIRS:
        return np.zeros(len(df))
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
