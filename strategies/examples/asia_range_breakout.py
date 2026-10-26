HYPOTHESIS = """Zakres sesji azjatyckiej (00–07 UTC) wyznacza poziomy, których wybicie w sesji
europejskiej (07–12 UTC) zapoczątkowuje ruch dnia."""

PARAMS = {"min_range_atr": [0.5, 1.0]}

import pandas as pd


def signals(df, p, ind):
    h = ind.hour(df)
    day = df.index.floor("D")
    asia = h < 7
    # Maksimum/minimum Azji NARASTAJĄCO w ciągu dnia (cummax), potem przeniesione na resztę dnia.
    # Zwykłe groupby(day).transform("max") wziąłoby świece z przyszłości → look-ahead.
    a_hi = df.high.where(asia).groupby(day).cummax().groupby(day).ffill()
    a_lo = df.low.where(asia).groupby(day).cummin().groupby(day).ffill()
    wide = (a_hi - a_lo) > p["min_range_atr"] * ind.atr(df, 14)
    london = (h >= 7) & (h < 13)
    long_ = ind.cross_above(df.close, a_hi) & london & wide
    short = ind.cross_below(df.close, a_lo) & london & wide
    return long_.astype("int8") - short.astype("int8")
