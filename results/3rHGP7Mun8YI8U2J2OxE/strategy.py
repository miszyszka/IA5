HYPOTHESIS = """Gdy pięć średnich EMA układa się w trend (5 > 10 > 15 > 25 > 40) i cena jest po właściwej
stronie EMA200, impet trendu zwykle trwa. Wejście na pierwszej świecy spełnienia warunku pozwala
złapać początek ruchu, a nie jego środek. Wyjście przy zamknięciu za EMA40 wypuszcza zysk,
gdy struktura trendu się rozpada."""

# Brak PARAMS: strategia ma stałe parametry z opisu. Dopisanie PARAMS zwiększyłoby liczbę prób (W2).


def signals(df, p, ind):
    c = df["close"]
    e5 = ind.ema(c, 5)
    e10 = ind.ema(c, 10)
    e15 = ind.ema(c, 15)
    e25 = ind.ema(c, 25)
    e40 = ind.ema(c, 40)
    e200 = ind.ema(c, 200)

    ribbon_up = (e5 > e10) & (e10 > e15) & (e15 > e25) & (e25 > e40)
    ribbon_dn = (e5 < e10) & (e10 < e15) & (e15 < e25) & (e25 < e40)

    bull = ribbon_up & (c > e200)
    bear = ribbon_dn & (c < e200)

    # Zdarzenie: warunek spełniony teraz, a na poprzedniej świecy nie był spełniony
    bull_start = bull & ~bull.shift(1, fill_value=False)
    bear_start = bear & ~bear.shift(1, fill_value=False)

    return bull_start.astype("int8") - bear_start.astype("int8")