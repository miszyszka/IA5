HYPOTHESIS = """Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na świecach Yahoo — innym źródle i okresie, którego badanie nie widziało."""

PARAMS = {
    "start": [6, 7, 8],      # godzina wejścia w czasie Londynu (z czasem letnim); 7:00 = otwarcie Londynu
}

# Wyjście po 4, 6 albo 8 godzinach; każde także z awaryjnym stopem 2×ATR14 (TP tak daleko, że w praktyce go nie ma)
EXITS = (
    [{"kind": "time", "n": n, "cap": n} for n in (4, 6, 8)]
    + [{"kind": "atr", "n": 14, "tp": 50.0, "sl": 2.0, "cap": n} for n in (4, 6, 8)]
)


def signals(df, p, ind):
    london = df.index.tz_convert("Europe/London")
    weekday = london.dayofweek < 5
    # sygnał na zamknięciu świecy start−1 → wejście na open świecy o godzinie start (czas Londynu)
    sig = weekday & (london.hour == p["start"] - 1)
    return -sig.astype("int8")              # short EUR/USD
