TIMEFRAME = "D1"

HYPOTHESIS = """Kurs walutowy, który odjechał daleko od swojej średniej z ok. 3 lat (756 dni handlu), ma tendencję wracać
w stronę tej średniej: parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale
w skali lat ciągną kurs z powrotem. Cena poniżej średniej = long, powyżej = short (lustrzanie, więc jednostronny dryf
pary nie udaje przewagi). Odchylenie mierzymy trzema sposobami (w %, w ATR14 dziennym, w odchyleniach standardowych
ceny z 756 dni), każdym na 4 progach; wchodzimy trzema sposobami (pierwszy dzień przekroczenia / co najwyżej jedna
pozycja na tydzień dopóki odchylenie trwa — piramidowanie / jak poprzednie, ale tylko w dniu, gdy cena zawraca
w stronę średniej). Bez stop lossa: pozycję zamyka powrót do średniej, TP w ATR albo upływ czasu (20–480 dni).
Hipoteza zapisana PRZED liczeniem."""

# Rodzaj odchylenia × próg (indeks 0–3 w THR) × sposób wejścia = 3 × 4 × 3 = 36 wariantów wejścia.
PARAMS = {"dev": ["pct", "atr", "z"], "level": [0, 1, 2, 3], "entry": ["cross", "weekly", "turn"]}
THR = {"pct": (5.0, 8.0, 12.0, 16.0),      # % odległości ceny od SMA756
       "atr": (6.0, 10.0, 14.0, 18.0),     # odległość w ATR14 dziennych
       "z": (1.0, 1.5, 2.0, 2.5)}          # odchylenia standardowe ceny z 756 dni
MEAN_DAYS = 756                             # ok. 3 lata handlu (3 × 252)
GAP_DAYS = 5                                # „weekly”/„turn”: najwyżej jedno wejście na 5 dni handlu

# Piramidowanie: do 10 pozycji naraz w parze, jeden kierunek (D-034); mały depozyt na pozycję, bo nie ma stop lossa.
PYRAMID = 10
SIZING = [1, 2, 5]

# Wyjścia BEZ stop lossa (B7: każde ma limit czasu): czas, TP w ATR14 (sl = 0), powrót do średniej (levels).
EXITS = (
    [{"kind": "time", "n": n, "cap": n} for n in (20, 60, 120, 240, 480)]
    + [{"kind": "atr", "n": 14, "tp": tp, "sl": 0.0, "cap": 480} for tp in (4.0, 8.0, 16.0)]
    + [{"kind": "level", "cap": 480}]
)


def deviation(df, kind, ind):
    """Znak: ujemne = cena poniżej średniej z 756 dni. Tylko zamknięte świece (rolling, bez przyszłości)."""
    sma = ind.sma(df.close, MEAN_DAYS)
    if kind == "pct":
        return (df.close / sma - 1.0) * 100.0
    if kind == "atr":
        return (df.close - sma) / ind.atr(df, 14)
    return (df.close - sma) / df.close.rolling(MEAN_DAYS).std()


def levels(df, p, ind):
    """Cel = powrót do średniej z 756 dni, policzonej na świecy sygnału (long: powyżej ceny, short: poniżej). Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    thr = THR[p["dev"]][p["level"]]
    x = deviation(df, p["dev"], ind).to_numpy()
    c = df.close.to_numpy()
    n = len(x)
    ok = np.isfinite(x)
    below = ok & (x <= -thr)          # long
    above = ok & (x >= thr)           # short
    out = np.zeros(n)
    if p["entry"] == "cross":         # zdarzenie: pierwszy dzień po wyjściu odchylenia za próg
        out[1:] = np.where(below[1:] & ~below[:-1], 1.0, 0.0) - np.where(above[1:] & ~above[:-1], 1.0, 0.0)
        return out
    last = -10**9                     # „weekly” / „turn”: stan, ale najwyżej jedno wejście na GAP_DAYS dni (tylko z przeszłości)
    for t in range(1, n):
        if t - last < GAP_DAYS:
            continue
        if below[t] and (p["entry"] == "weekly" or c[t] > c[t - 1]):
            out[t], last = 1.0, t
        elif above[t] and (p["entry"] == "weekly" or c[t] < c[t - 1]):
            out[t], last = -1.0, t
    return out