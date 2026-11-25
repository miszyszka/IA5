TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """ALMA (Arnaud Legoux, 2009) waży ceny krzywą Gaussa przesuniętą ku najnowszym świecom, więc zawraca
wcześniej niż SMA o podobnej długości i mniej szarpie niż EMA. Jeśli trendy na parach FX trwają tygodniami, to wcześniejsze
wykrycie zwrotu średniej (albo przejścia ceny przez średnią) zostawia większą część ruchu niż spóźniona SMA.
Ryzyko: trzy pokrętła (długość, offset, sigma) i każde to kompromis — offset 0,99 szybki, ale nerwowy (dużo fałszywych
zwrotów), 0,5 gładki, ale spóźniony. Startujemy od ustawień domyślnych 9 · 0,85 · 6 i obok sprawdzamy krańce offsetu."""

# 2 długości × 3 offsety × 2 sposoby wejścia = 12 wariantów wejścia; sigma stała = 6 (domyślna)
PARAMS = {
    "n": [9, 21],                  # 9 = domyślna, 21 = wolniejsza (porównywalna z SMA 20)
    "offset": [0.5, 0.85, 0.99],   # gładka / domyślna / szybka
    "mode": ["zwrot", "przeciecie"],
}
SIGMA = 6


def signals(df, p, ind):
    a = ind.alma(df.close, p["n"], p["offset"], SIGMA)
    if p["mode"] == "zwrot":
        # ALMA zmienia kierunek: wczoraj spadała (albo stała), dziś rośnie → long; lustrzanie short
        up = (a > a.shift(1)).astype(int)
        down = (a < a.shift(1)).astype(int)
        long_ = (up == 1) & (up.shift(1) == 0) & a.shift(2).notna()
        short = (down == 1) & (down.shift(1) == 0) & a.shift(2).notna()
    else:
        # zamknięcie dnia przechodzi przez ALMA
        long_ = ind.cross_above(df.close, a)
        short = ind.cross_below(df.close, a)
    return long_.astype("int8") - short.astype("int8")
