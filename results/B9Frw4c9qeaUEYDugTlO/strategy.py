TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który spadł o 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę: parytet siły
nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs z powrotem.
Tylko long, BEZ DŹWIGNI: jedna pozycja naraz w całym portfelu (wszystkie 8 par), wartość pozycji = cały kapitał (1× kapitał,
nie 30×). Wejście w dniu, w którym cena po raz pierwszy spada o 5% poniżej średniej (zdarzenie, nie stan); sygnały w czasie,
gdy pozycja jest otwarta, przepadają. Wyjście tylko wtedy, gdy cena dobije do poziomu średniej z dnia otwarcia transakcji
(stała cena celu, nie ruchoma średnia); bez stop lossa i bez limitu czasu. Cała dostępna historia D1 (średnia 3-letnia
potrzebuje ok. 3 lat rozgrzewki). Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant, żadnych parametrów.
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # wejście, gdy cena jest 5% poniżej średniej

# BEZ DŹWIGNI: silnik liczy nominał = 30 × depozyt, więc depozyt 100/30 % kapitału daje nominał = 100% kapitału (1×).
# Jedna pozycja naraz w całym portfelu (MAX_PAIRS = 1, bez PYRAMID) — inaczej kilka pozycji naraz byłoby dźwignią.
SIZING = [100 / 30]
MAX_PAIRS = 1
PAIR_RANK = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "AUDUSD", "USDCHF", "USDCAD", "EURJPY"]   # tylko przy sygnałach tego samego dnia: kolejność z tabeli spreadów (bez wyników)
EXITS = [{"kind": "level", "cap": 0}]     # TP = średnia z dnia sygnału (levels), bez SL i BEZ limitu czasu (D-061)


def levels(df, p, ind):
    """Cel = średnia z 756 dni policzona na świecy sygnału (cena z momentu otwarcia transakcji, nie ruchoma). Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    below = ((df.close / sma - 1.0) <= -BAND).to_numpy()          # NaN w rozgrzewce → False
    out = np.zeros(len(below))
    out[1:] = (below[1:] & ~below[:-1]).astype(float)             # zdarzenie: pierwszy dzień poniżej −5%
    return out