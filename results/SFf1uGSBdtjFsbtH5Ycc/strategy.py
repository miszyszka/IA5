TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """Na świecach dziennych krótkoterminowe przewartościowanie w kierunku trendu wraca do średniej: po 2–3 dniach
silnej korekty (RSI z 2 dni na dnie skali) cena w długim trendzie zwykle odbija, bo korekta to dla trendu szum, a nie zmiana
kierunku. To dzienny odpowiednik żywej strategii „RSI 2” z H1, ale na ok. 20 latach zamiast 2 — H1 miała za krótką próbę
(OOS 6 miesięcy), a tu OOS to ok. 5 lat i wiele reżimów rynku.
Wejście (zdarzenie, nie stan): RSI(2) przebija od góry poziom `rsi_level` (5/10/15), gdy zamknięcie jest nad SMA trendu
(100 albo 200 dni) — long; lustrzanie short: RSI(2) przebija od dołu 100 − poziom, gdy zamknięcie jest pod SMA.
Wyjścia z domyślnej siatki silnika w dniach (ATR dzienny). Do sprawdzenia przy walidacji: koszt nocy (D-054) i to, czy wynik
nie pochodzi wyłącznie z wariantów bez stopu — poprzednia wersja na H1 oblała DSR właśnie przez brak stopu.
Zapisane PRZED liczeniem; 6 wariantów wejścia."""

PARAMS = {"rsi_level": [5, 10, 15], "trend": [100, 200]}


def signals(df, p, ind):
    sma = ind.sma(df.close, p["trend"])
    rsi = ind.rsi(df.close, 2)
    long_ = (df.close > sma) & ind.cross_below(rsi, p["rsi_level"])
    short = (df.close < sma) & ind.cross_above(rsi, 100 - p["rsi_level"])
    return long_.astype("int8") - short.astype("int8")