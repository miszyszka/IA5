HYPOTHESIS = """Po gwałtownym spadku EUR/USD w 10 świecach rynek jest wyprzedany: sprzedający kończą, a pierwsza zielona
świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long."""

PARAMS = {
    "drop_pips": [50, 80, 100, 150],   # spadek zamknięć z 10 świec przed zieloną świecą
}


def signals(df, p, ind):
    if df.attrs.get("pair") != "EURUSD":
        return (df.close * 0).astype("int8")      # tylko EUR/USD
    pip = 0.0001
    drop = df.close.shift(1) - df.close.shift(11)  # 10 świec zakończonych tuż przed bieżącą
    green = df.close > df.open
    first_green = green & ~green.shift(1, fill_value=False)
    return (first_green & (drop <= -p["drop_pips"] * pip)).astype("int8")   # +1 = long