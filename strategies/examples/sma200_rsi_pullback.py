HYPOTHESIS = """Gdy długoterminowy trend jest wzrostowy (SMA200 rośnie), głębokie krótkoterminowe
wyprzedanie (RSI14 spada poniżej progu) jest chwilowe i cena wraca w górę."""

PARAMS = {
    "rsi_level": [25, 30, 35],   # „RSI spadło poniżej X”
    "slope_bars": [5, 20],       # „SMA200 rośnie” = SMA200 teraz > SMA200 sprzed N świec
}


def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    trend_up = ind.rising(sma200, p["slope_bars"])
    oversold = ind.cross_below(rsi, p["rsi_level"])      # zdarzenie: przecięcie w dół, nie stan „poniżej”
    return (trend_up & oversold).astype("int8")          # +1 = long
