HYPOTHESIS = """W konsolidacji (słaby trend wg ADX) zamknięcie poza wstęgą Bollingera to przesada,
która wraca do średniej."""

PARAMS = {"k": [2.0, 2.5], "adx_max": [20, 25]}


def signals(df, p, ind):
    bb = ind.bollinger(df.close, 20, p["k"])
    calm = ind.adx(df, 14).adx < p["adx_max"]
    long_ = ind.cross_below(df.close, bb.lower) & calm
    short = ind.cross_above(df.close, bb.upper) & calm
    return long_.astype("int8") - short.astype("int8")
