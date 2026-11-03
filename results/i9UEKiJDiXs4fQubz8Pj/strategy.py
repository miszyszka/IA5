HYPOTHESIS = """Wersja 2 strategii „simple” (wersja 1: tylko EUR/USD, spadek 50–150 pipsów z 10 świec, 8 transakcji OOS).
Po gwałtownym spadku rynek jest wyprzedany: sprzedający kończą, a zielona świeca pokazuje powrót kupujących —
oczekujemy krótkiego odbicia na long. To samo dotyczy każdej pary, więc spadek mierzymy w jednostkach zmienności
pary (ATR14 · √N), a nie w pipsach: 50 pipsów na EUR/USD to coś innego niż 50 pipsów na EUR/GBP czy USD/JPY.
Sprawdzamy: krótsze i dłuższe okno spadku, mniejszy i większy spadek, wejście po pierwszej albo po drugiej zielonej."""

PARAMS = {
    "okno": [10, 20],           # ile świec obejmuje spadek przed zieloną świecą
    "spadek": [1.0, 1.35, 1.7],  # spadek ≥ tyle × ATR14 · √okno (EUR/USD, okno 10: ok. 37 / 50 / 63 pipsy)
    "zielona": [1, 2],          # wejście po pierwszej zielonej albo po drugiej zielonej z rzędu
}


def signals(df, p, ind):
    n, k, g = p["okno"], p["spadek"], p["zielona"]
    green = df.close > df.open
    if g == 1:
        trigger = green & ~green.shift(1, fill_value=False)                      # pierwsza zielona po czerwonej
    else:
        trigger = green & green.shift(1, fill_value=False) & ~green.shift(2, fill_value=False)   # druga zielona z rzędu
    ref = g                                     # ostatnia świeca przed pierwszą zieloną
    drop = df.close.shift(ref) - df.close.shift(ref + n)
    atr = ind.atr(df, 14).shift(ref)
    deep = drop <= -k * atr * (n ** 0.5)
    return (trigger & deep).astype("int8")      # +1 = long, wszystkie pary