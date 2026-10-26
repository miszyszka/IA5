HYPOTHESIS = """Wybicie z kanału N świec zapoczątkowuje ruch w kierunku wybicia (podążanie za trendem)."""

PARAMS = {"n": [20, 55]}


def signals(df, p, ind):
    ch = ind.donchian(df, p["n"])
    upper, lower = ch.upper.shift(1), ch.lower.shift(1)   # kanał do POPRZEDNIEJ świecy — bieżąca go przebija
    long_ = ind.cross_above(df.close, upper)
    short = ind.cross_below(df.close, lower)
    return long_.astype("int8") - short.astype("int8")    # +1 long, −1 short
