TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który spadł o co najmniej 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Tylko long (cena ≥ 5% poniżej średniej). Jedno wejście na tydzień (co najmniej 5 dni handlu od poprzedniego
w tej parze), do 3 pozycji naraz w parze. Cel = poziom średniej z dnia sygnału (stała cena), bez limitu czasu.
Wersja z zarządzaniem ryzykiem: STOP LOSS poniżej wejścia na odległość równą ułamkowi drogi do celu (0,5 / 0,75 / 1,0 ×
droga do średniej), więc z góry znany stosunek zysku do straty, a pozycja nie wisi latami na stracie. Każda pozycja
ma tę samą stratę przy stopie: ok. 0,5% kapitału (waga pozycji = 0,5% ÷ odległość do stopu), niezależnie od tego, jak
głęboko kurs jest pod średnią. Wszystko jak w wersji bez stopu, tylko ryzyko jest ograniczone i równe w każdej
transakcji. Cała dostępna historia D1 (ok. 27 lat sygnałów), żeby próba IS (ranking) i OOS (ostatnie 25%) miały dość transakcji.
Hipoteza zapisana PRZED liczeniem."""

# Jedyny parametr: odległość stopu jako ułamek drogi do celu (średniej).
PARAMS = {"sl_gap": [0.5, 0.75, 1.0]}
START = None              # cała historia; żeby liczyć tylko ostatnie 10 lat, wpisz START = "2016-11-11" (wtedy IS ma mało transakcji)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)
RISK = 0.005              # strata przy stopie = 0,5% kapitału na pozycję

PYRAMID = 3               # do 3 pozycji naraz w parze (najgorszy przypadek: 8 par × 3 × 0,5% = 12% kapitału)
SIZING = [1]              # waga 1,0 = depozyt 1% kapitału = nominał 30% kapitału; waga sygnału skaluje to do RISK
EXITS = [{"kind": "level", "cap": 0}]     # TP i SL ze strategii (levels), bez limitu czasu (D-061)


def levels(df, p, ind):
    """TP = średnia z 756 dni z dnia sygnału. SL = cena sygnału minus sl_gap × (droga do średniej)."""
    sma = ind.sma(df.close, MEAN_DAYS)
    return pd.DataFrame({"tp": sma, "sl": df.close - p["sl_gap"] * (sma - df.close)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    dev = (df.close / sma - 1.0).to_numpy()
    live = np.isfinite(dev) if START is None else (df.index >= pd.Timestamp(START, tz="UTC")) & np.isfinite(dev)
    below = live & (dev <= -BAND)
    # waga: strata przy stopie ≈ 0,3 (nominał na wagę 1) × waga × odległość do stopu (w ułamku ceny) = RISK
    stop_dist = p["sl_gap"] * (sma / df.close - 1.0).to_numpy()
    weight = np.clip(RISK / (0.3 * np.where(stop_dist > 0, stop_dist, np.nan)), 0.1, 10.0)
    out = np.zeros(len(dev))
    last = -10**9                     # tylko z przeszłości: najwyżej jedno wejście na GAP_DAYS dni
    for t in range(len(dev)):
        if t - last < GAP_DAYS:
            continue
        if below[t] and np.isfinite(weight[t]):
            out[t], last = weight[t], t
    return out