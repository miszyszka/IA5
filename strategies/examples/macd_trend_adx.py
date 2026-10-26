HYPOTHESIS = """Przecięcie MACD z linią sygnału w kierunku trendu SMA100, przy silnym trendzie (ADX),
łapie kontynuację ruchu."""

PARAMS = {"adx_min": [20, 30]}


def signals(df, p, ind):
    m = ind.macd(df.close, 12, 26, 9)
    sma = ind.sma(df.close, 100)
    strong = ind.adx(df, 14).adx > p["adx_min"]
    long_ = ind.cross_above(m["macd"], m["signal"]) & (df.close > sma) & strong
    short = ind.cross_below(m["macd"], m["signal"]) & (df.close < sma) & strong
    return long_.astype("int8") - short.astype("int8")
