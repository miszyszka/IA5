HYPOTHESIS = """Wersja porównawcza do „RSI 70/30 w silnym trendzie — dokładanie”: te same wejścia (pierwsze przebicie
RSI14 70/30 przeciw wyraźnemu trendowi EMA200) i te same wyjścia, ale jedna pozycja na parę i stała stawka.
Różnica w wynikach pokaże, ile wnosi (albo kosztuje) dokładanie."""

HOURS = False       # D-034: bez okna godzin, jak wersja z dokładaniem
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": 6, "level": 70, "cap": 120}]


def signals(df, p, ind):
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)
    rsi = ind.rsi(df.close, 14)
    short = (slope < -0.25) & ind.cross_above(rsi, 70)
    long_ = (slope > 0.25) & ind.cross_below(rsi, 30)
    return long_.astype("int8") - short.astype("int8")