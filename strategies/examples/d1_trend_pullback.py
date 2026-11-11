TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """Na świecach dziennych trend utrzymuje się tygodniami, a korekta do średniej w trendzie bywa dobrym wejściem.
Wejście: SMA50 nad SMA200 (trend wzrostowy) i cena po korekcie — RSI(14) na dziennych przebija od dołu 40 (koniec korekty).
Lustrzanie short. Wyjścia z domyślnej siatki silnika liczonej w dniach (ATR dzienny). Spread na D1 to ułamek dziennego ATR,
więc kosztowo jest tu więcej miejsca na przewagę niż na H1; próba 8 par × 20 lat obejmuje wiele reżimów rynku."""

PARAMS = {"rsi_level": [35, 40], "fast": [50]}


def signals(df, p, ind):
    fast, slow = ind.sma(df.close, p["fast"]), ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    long_ = (fast > slow) & ind.cross_above(rsi, p["rsi_level"])
    short = (fast < slow) & ind.cross_below(rsi, 100 - p["rsi_level"])
    return long_.astype("int8") - short.astype("int8")
