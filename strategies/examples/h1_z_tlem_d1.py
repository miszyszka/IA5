HYPOTHESIS = """Strategia H1 z tłem dziennym (D-058): kierunek bierzemy z 20 lat świec dziennych — SMA200 na D1 (zamiast SMA200
z H1, która zjada 40% krótkiej próby H1) — a wejście z godzinowego powrotu: RSI(14) H1 przebija 30 od dołu w trendzie
wzrostowym D1 (cena dnia zamknęła się nad dzienną SMA200), lustrzanie short. Dzień d jest widoczny dopiero po jego zamknięciu."""

PARAMS = {"rsi_level": [30, 35]}


def signals(df, p, ind):
    d1 = ind.d1(df)                                   # świece dzienne tej pary, tylko zamknięte dni
    if d1 is None:
        return pd.Series(0, index=df.index, dtype="int8")   # bez D1 (np. kontrola bez danych dziennych) — brak sygnałów
    above = (d1.close > ind.sma(d1.close, 200))       # liczone na D1…
    up = ind.d1_to_h1(df, above).fillna(False).astype(bool)   # …i przeniesione na H1 bez look-ahead
    rsi = ind.rsi(df.close, 14)
    long_ = up & ind.cross_above(rsi, p["rsi_level"])
    short = ~up & ind.d1_to_h1(df, above).notna() & ind.cross_below(rsi, 100 - p["rsi_level"])
    return long_.astype("int8") - short.astype("int8")
