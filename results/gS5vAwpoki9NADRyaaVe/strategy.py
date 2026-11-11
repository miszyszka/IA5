TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który odjechał o co najmniej 5% od swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Cena ≥ 5% poniżej średniej = long, ≥ 5% powyżej = short (lustrzanie). Jedno wejście na tydzień (co najmniej
5 dni handlu od poprzedniego w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop
lossa i bez limitu czasu. Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant: żadnych parametrów, jedno wyjście.
START = "2016-11-11"      # ostatnie 10 lat (stała data — sygnały wcześniejsze są wyzerowane)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)

PYRAMID = 10              # maksimum silnika: do 10 pozycji naraz w parze (w jednym kierunku)
SIZING = [1]              # zawsze 1% kapitału jako depozyt
EXITS = [{"kind": "level", "cap": 0}]     # TP = średnia (levels), bez SL i BEZ limitu czasu (D-061): zamknięcie tylko na średniej


def levels(df, p, ind):
    """Zamknięcie na przecięciu średniej: cel = średnia z 756 dni policzona na świecy sygnału. Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    dev = (df.close / sma - 1.0).to_numpy()
    live = (df.index >= pd.Timestamp(START, tz="UTC")) & np.isfinite(dev)
    below = live & (dev <= -BAND)     # long
    above = live & (dev >= BAND)      # short
    out = np.zeros(len(dev))
    last = -10**9                     # tylko z przeszłości: najwyżej jedno wejście na GAP_DAYS dni
    for t in range(len(dev)):
        if t - last < GAP_DAYS:
            continue
        if below[t]:
            out[t], last = 1.0, t
        elif above[t]:
            out[t], last = -1.0, t
    return out