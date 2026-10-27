HYPOTHESIS = """W silnym trendzie H1 krótkie, gwałtowne ruchy przeciw trendowi (RSI14 przebija 70 przy trendzie
spadkowym albo 30 przy wzrostowym) to chwilowa przesada: płynność wraca do kierunku głównego trendu
i cena cofa się w jego stronę w ciągu kilku-kilkunastu godzin."""

# slope_atr: jak bardzo musi się zmienić SMA200 w ciągu 20 godzin (w jednostkach ATR14), żeby trend był „wyraźny”
PARAMS = {"slope_atr": [0.25, 0.5, 1.0]}


def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    atr = ind.atr(df, 14)
    slope = (sma200 - sma200.shift(20)) / atr          # nachylenie trendu w ATR na 20 świec
    trend_up = slope > p["slope_atr"]                   # wyraźnie rośnie
    trend_down = slope < -p["slope_atr"]                # wyraźnie spada; pomiędzy = płasko, nic nie robimy
    rsi = ind.rsi(df.close, 14)
    long_ = trend_up & ind.cross_below(rsi, 30)         # przesada w dół w trendzie wzrostowym → kupno
    short = trend_down & ind.cross_above(rsi, 70)       # przesada w górę w trendzie spadkowym → sprzedaż
    return long_.astype("int8") - short.astype("int8")