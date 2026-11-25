TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """ALMA (Arnaud Legoux, 2009) waży ceny krzywą Gaussa przesuniętą ku najnowszym świecom, więc zawraca
wcześniej niż SMA o podobnej długości i mniej szarpie niż EMA. Jeśli trendy na parach FX trwają tygodniami, to wcześniejsze
wykrycie zwrotu średniej zostawia większą część ruchu niż spóźniona SMA. Pojedyncze „mignięcia” kierunku to szum,
więc liczy się tylko zwrot po ruchu, który trwał co najmniej kilka dni. Ryzyko: trzy pokrętła (długość, offset, sigma)
i każde to kompromis — offset 0,99 szybki, ale nerwowy, 0,5 gładki, ale spóźniony. Start od domyślnych 9 · 0,85 · 6.
Wersja 2: mniej wariantów i bez trybu „przecięcie” — wersja 1 dała 444 MB transakcji, a GitHub przyjmuje do 100 MB."""

# n = długość, offset, sigma, min = ile dni ALMA musiała iść w starą stronę, żeby zwrot się liczył
CONFIGS = [
    {"n": 9, "offset": 0.85, "sigma": 6, "min": 3},    # ustawienia domyślne
    {"n": 21, "offset": 0.85, "sigma": 6, "min": 3},   # wolniejsza, porównywalna z SMA 20
    {"n": 21, "offset": 0.99, "sigma": 6, "min": 5},   # szybka (nerwowa), więc ostrzejsze potwierdzenie
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    a = ind.alma(df.close, c["n"], c["offset"], c["sigma"])
    d = a.diff()
    side = (d > 0).astype(int) - (d < 0).astype(int)          # +1 rośnie, -1 spada, 0 stoi / rozgrzewka
    run = side.groupby((side != side.shift()).cumsum()).cumcount() + 1   # ile dni z rzędu w tym kierunku
    prev_side, prev_run = side.shift(1), run.shift(1)
    long_ = (side == 1) & (prev_side == -1) & (prev_run >= c["min"])
    short = (side == -1) & (prev_side == 1) & (prev_run >= c["min"])
    return long_.astype("int8") - short.astype("int8")