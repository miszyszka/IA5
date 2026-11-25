TIMEFRAME = "D1"   # świece dzienne Yahoo (D-058): wejście na open dnia, wyjście na zamknięciu tego dnia = 24 h

HYPOTHESIS = """Na EUR/USD kierunek krótkiego impetu może przenosić się na następny dzień: jeśli RSI albo EMA rośnie,
kolejny dzień częściej jest wzrostowy, jeśli spada — spadkowy. Codziennie jedna transakcja na 24 h (open dnia → zamknięcie
dnia), kierunek z jednego wskaźnika: RSI(n) rosnące → long, malejące → short; albo EMA(n) rosnąca → long, malejąca → short.
„Rośnie” = wartość dziś wyższa niż k dni temu. Silnik liczy wszystkie kombinacje n × k na tych samych zasadach wyjścia;
wybór najlepszej tylko po IS, a kara za liczbę prób jest w DSR."""

EXITS = [{"kind": "time", "n": 1, "cap": 1}]   # wyjście na zamknięciu dnia wejścia — dokładnie 24 h (życzenie Michała)
EXPLORE = False   # eksploracja zmienia wyjścia i filtruje dni — tu reguła jest stała: codziennie, 24 h

RSI_N = [2, 3, 5, 7, 9, 14, 21]
EMA_N = [5, 10, 20, 30, 50, 100, 200]
K = [1, 2, 3, 5]                               # „rośnie” = dziś wyżej niż k dni temu
CONFIGS = [("rsi", n, k) for n in RSI_N for k in K] + [("ema", n, k) for n in EMA_N for k in K]
PARAMS = {"cfg": list(range(len(CONFIGS)))}    # 28 wersji RSI + 28 wersji EMA = 56


def signals(df, p, ind):
    if df.attrs.get("pair") != "EURUSD":       # tylko EUR/USD
        return pd.Series(0, index=df.index, dtype="int8")
    kind, n, k = CONFIGS[p["cfg"]]
    x = ind.rsi(df.close, n) if kind == "rsi" else ind.ema(df.close, n)
    up, down = ind.rising(x, k), ind.falling(x, k)   # codziennie jedno z dwóch (poza rzadkim „bez zmiany”)
    return up.astype("int8") - down.astype("int8")
