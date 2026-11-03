HYPOTHESIS = """„simple” na wszystkich 8 parach (wersja 1: tylko EUR/USD, najlepszy wariant IS: spadek 50 pipsów,
wyjście TP 1 × ATR14, SL 0,5 × ATR14, max 24 świece). Po gwałtownym spadku z 10 świec rynek jest wyprzedany:
sprzedający kończą, a pierwsza zielona świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long.
Ta sama reguła i to samo wyjście, bez zmian — tylko więcej par. Spadek w pipsach danej pary (JPY: 0,01)."""

PARAMS = {"drop_pips": [50]}   # jak najlepszy wariant wersji 1

EXITS = [{"kind": "atr", "n": 14, "tp": 1.0, "sl": 0.5, "cap": 24}]   # TP 1 × ATR14, SL 0,5 × ATR14, max 24 świece


def signals(df, p, ind):
    pip = 0.01 if "JPY" in df.attrs.get("pair", "") else 0.0001
    drop = df.close.shift(1) - df.close.shift(11)  # 10 świec zakończonych tuż przed bieżącą
    green = df.close > df.open
    first_green = green & ~green.shift(1, fill_value=False)
    return (first_green & (drop <= -p["drop_pips"] * pip)).astype("int8")   # +1 = long, wszystkie pary