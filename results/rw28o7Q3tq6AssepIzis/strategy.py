HYPOTHESIS = """Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu; zysk daje kilka dużych ruchów, nie trafność. Wersja 5b: stop początkowy i stop
kroczący w skali DNIA (ok. 2–3 dzienne ATR), bo trend trwający tygodnie musi przetrwać zwykłe wahania w ciągu
dnia — w wersji 5 stop 2–4 × ATR godzinowego (0,3–0,7 dziennego zakresu) zamykał pozycję po medianie 18 h.
Uwaga: zmiana stopu powstała po obejrzeniu wyniku wersji 5 na całej historii (także OOS) — OOS tej wersji nie jest
czysty; liczba prób łącznie z wersją 5: 96. Rozstrzyga forward test po zamrożeniu (W4)."""

HOURS = False   # okno godzin jako parametr „sesja” (jak w wersji 5)

PARAMS = {
    "kanal": [120, 240],                    # wybicie maksimum/minimum z 120 lub 240 poprzednich świec H1 (~5 / ~10 dni)
    "filtr_d1": [False, True],              # trend dzienny: zamknięcie D1 nad EMA50(D1) i EMA50 rośnie (short lustrzanie)
    "sesja": ["wszystkie", "7-20 UTC"],
}

# Stop kroczący (D-035) w skali dziennej: na danych Yahoo ATR dzienny ≈ 5–6 × ATR14 godzinowego, więc
# stop początkowy 10 / 15 × ATR14(H1) ≈ 2 / 2,5–3 dzienne ATR, stop kroczący 10 / 15 / 20 × ATR14(H1) ≈ 2 / 3 / 4 dzienne ATR.
# Bez TP; do 20 dni (480 świec).
EXITS = [{"kind": "trail", "n": 14, "sl": sl, "trail": tr, "cap": 480}
         for sl in (10.0, 15.0) for tr in (10.0, 15.0, 20.0)]


def d1_trend(df, ind):
    """Trend D1 bez look-ahead: tylko zamknięte dni robocze (shift(1)), przeniesione na H1.

    Niedzielne otwarcie tygodnia (1–3 świece) nie jest osobnym dniem — w wersji 5 robiło z niego „dzień” D1
    i skracało EMA50 do ok. 9 tygodni. Świece z niedzieli mają ten sam stan co piątek (bez ryzyka look-ahead).
    """
    d1 = df.close.resample("1D").last().dropna()
    d1 = d1[d1.index.dayofweek < 5]
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