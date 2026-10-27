HYPOTHESIS = """Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu. Przegrywamy często, ale mało (stop w ATR), wygrywamy rzadko, ale dużo —
przewaga jest w asymetrii, nie w trafności. Wersja ze stopem kroczącym: zysk nie jest ograniczony przez TP
ani przez limit świec, a stop przesuwa się za ceną, więc trend „sam” decyduje o wyjściu."""

HOURS = False   # okno godzin jako parametr „sesja”

PARAMS = {
    "kanal": [120, 240],                    # wybicie maksimum/minimum z 120 lub 240 poprzednich świec H1 (~5 / ~10 dni)
    "filtr_d1": [False, True],              # trend dzienny: zamknięcie D1 nad EMA50(D1) i EMA50 rośnie (short lustrzanie)
    "sesja": ["wszystkie", "7-20 UTC"],
}

# Stop kroczący (D-035): stop początkowy w ATR, potem podąża za najwyższym high (long) / najniższym low (short)
# w odległości trail × ATR14; bez TP — zysk rośnie, dopóki trend trwa; do 20 dni (480 świec)
EXITS = [{"kind": "trail", "n": 14, "sl": sl, "trail": tr, "cap": 480}
         for sl in (1.5, 3.0) for tr in (2.0, 3.0, 4.0)]


def d1_trend(df, ind):
    """Trend D1 bez look-ahead: tylko zamknięte dni (shift(1)), przeniesione na H1."""
    d1 = df.close.resample("1D").last().dropna()
    e = ind.ema(d1, 50)
    up = ((d1 > e) & ind.rising(e, 5)).shift(1)
    down = ((d1 < e) & ind.falling(e, 5)).shift(1)
    to_h1 = lambda s: s.reindex(df.index, method="ffill").fillna(False).astype(bool)  # noqa: E731
    return to_h1(up), to_h1(down)


def signals(df, p, ind):
    n = p["kanal"]
    top = ind.highest(df.high, n).shift(1)       # maksimum n POPRZEDNICH świec (bez bieżącej)
    bottom = ind.lowest(df.low, n).shift(1)
    long_ = ind.cross_above(df.close, top)        # pierwsze zamknięcie nad kanałem
    short = ind.cross_below(df.close, bottom)

    if p["filtr_d1"]:
        up, down = d1_trend(df, ind)
        long_, short = long_ & up, short & down

    if p["sesja"] != "wszystkie":
        h = ind.hour(df)
        ok = (h >= 7) & (h < 20)
        long_, short = long_ & ok, short & ok

    return long_.astype("int8") - short.astype("int8")
