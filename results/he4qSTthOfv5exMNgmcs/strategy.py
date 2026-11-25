TIMEFRAME = "D1"   # świece dzienne: sygnał codziennie na zamknięciu dnia, wejście na open następnego

HYPOTHESIS = """Mały TP i ogromny SL: cena często dochodzi do bliskiego celu w kierunku długiego trendu, a daleki stop
rzadko pada. Kierunek z długiej EMA: tryb „trend” — EMA rośnie → long, spada → short; tryb „hamowanie” — spadek EMA
zwalnia → long, wzrost EMA zwalnia → short (wejście przed zawróceniem). Wysoki win rate jest tu pewny — pytanie, czy rzadkie
duże straty na SL go nie zjadają."""

# mode: "trend" = kierunek EMA; "hamowanie" = zmiana tempa EMA (spadek hamuje → long, wzrost hamuje → short)
PARAMS = {"mode": ["trend", "hamowanie"], "ema": [100, 200], "k": [5, 20]}   # k = ile dni wstecz mierzymy nachylenie

# mały TP, ogromny SL (w ATR14 dziennym), limit 60 dni (B7); jedna pozycja na parę — nowe wejście następnego dnia po wyjściu
EXITS = [{"kind": "atr", "n": 14, "tp": tp, "sl": sl, "cap": 60} for tp in (0.3, 0.5, 1.0) for sl in (3.0, 5.0, 10.0)]


def signals(df, p, ind):
    e = ind.ema(df.close, p["ema"])
    slope = e - e.shift(p["k"])                      # nachylenie EMA z k dni
    if p["mode"] == "trend":
        long_, short = slope > 0, slope < 0
    else:
        prev = slope.shift(p["k"])                   # nachylenie k dni wcześniej
        long_ = (slope < 0) & (slope > prev)         # spada, ale wolniej — spadek hamuje
        short = (slope > 0) & (slope < prev)         # rośnie, ale wolniej — wzrost hamuje
    return long_.astype("int8") - short.astype("int8")