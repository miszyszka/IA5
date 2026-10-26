HYPOTHESIS = """Gdy długoterminowy trend jest wzrostowy (SMA200 rośnie), głębokie krótkoterminowe
wyprzedanie (RSI14 spada poniżej progu) jest chwilowe i cena wraca w górę."""

PARAMS = {
    "rsi_level": [30, 35, 40],   # „RSI spadło poniżej X" — każdy próg to osobny wariant wejścia
    "slope_bars": [5, 20],       # „SMA200 rosnąca" = SMA200 dziś > SMA200 sprzed N świec
}

def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    rising = sma200 > sma200.shift(p["slope_bars"])        # interpretacja „rosnąca"
    crossed = ind.cross_below(rsi, p["rsi_level"])          # przecięcie w dół, nie sam stan „poniżej"
    return (rising & crossed).astype("int8")                # +1 = long, tylko longi
