HYPOTHESIS = """Dlaczego ta strategia ma działać — 1–3 zdania, spisane PRZED liczeniem."""

PARAMS = {
    "rsi_level": [25, 30],    # każda wartość = osobny wariant wejścia
}

# TIMEFRAME = "D1"     # świece dzienne (cała historia Yahoo) zamiast H1 — D-058; tło D1 w strategii H1: ind.d1(df), ind.d1_to_h1(df, x)

def signals(df, p, ind):
    # df: świece H1 jednej pary (open, high, low, close), indeks = czas otwarcia UTC
    # zwróć +1 (long) / -1 (short) / 0 na świecy, której ZAMKNIĘCIE daje sygnał
    rsi = ind.rsi(df.close, 14)
    trend = ind.rising(ind.sma(df.close, 200), 5)
    return (trend & ind.cross_below(rsi, p["rsi_level"])).astype("int8")
