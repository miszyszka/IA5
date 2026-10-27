HYPOTHESIS = """W wyraźnym trendzie (EMA200 na H1 i EMA50 na H4) skrajny ruch przeciw trendowi (RSI14 za 70/30)
zwykle się wyczerpuje — ale wejście w chwili przebicia łapie też te ruchy, które są początkiem odwrócenia trendu
i dają największe straty. Czekamy więc na dowód wyczerpania: RSI wraca zza poziomu, a świeca zamyka się
w kierunku trendu. Każda pozycja ma stop cenowy w ATR, więc pojedyncza pomyłka kosztuje z góry znaną kwotę."""

import numpy as np

HOURS = False   # okno godzin sterowane parametrem „sesja” — żeby porównać obie wersje w jednym liczeniu

PARAMS = {
    "wejscie": ["przebicie", "powrot"],     # przebicie = jak dotąd (RSI wchodzi za poziom); powrot = RSI wraca zza poziomu
    "poziom": [70, 75],                     # short za 70/75, long za 30/25
    "nachylenie": [0.15, 0.3],              # zmiana EMA200 na 10 świec, w ATR14 — siła trendu H1
    "h4": [False, True],                    # dodatkowo trend H4 (EMA50 rośnie/spada na 3 zamkniętych świecach H4)
    "sesja": ["wszystkie", "7-20 UTC"],      # wejścia tylko w sesji europejskiej i amerykańskiej
}

# Wyjścia — każde ze stopem cenowym (największe straty poprzedniej wersji to brak SL: do −332 pipsów).
EXITS = (
    [{"kind": "atr", "n": 14, "tp": tp, "sl": sl, "cap": cap}
     for tp in (1.0, 1.5, 2.0, 3.0) for sl in (1.0, 1.5, 2.0, 3.0) for cap in (48, 120)]
    + [{"kind": "rsi_streak", "n": 14, "tp": tp, "sl": sl, "run": 6, "level": 70, "cap": 120}
       for tp in (1.5, 2.0) for sl in (1.5, 2.0)]
    + [{"kind": "rsi50", "n": 14, "sl": sl, "cap": 48} for sl in (1.0, 1.5, 2.0)]
)


def signals(df, p, ind):
    atr = ind.atr(df, 14)
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / atr
    up = slope > p["nachylenie"]
    down = slope < -p["nachylenie"]

    if p["h4"]:
        # H4 bez look-ahead: tylko zamknięte świece H4 (shift(1)), przeniesione na H1
        h4 = df.close.resample("4h").last().dropna()
        e4 = ind.ema(h4, 50)
        h4_up = ind.rising(e4, 3).shift(1).reindex(df.index, method="ffill").fillna(False).astype(bool)
        h4_down = ind.falling(e4, 3).shift(1).reindex(df.index, method="ffill").fillna(False).astype(bool)
        up, down = up & h4_up, down & h4_down

    rsi = ind.rsi(df.close, 14)
    hi, lo = p["poziom"], 100 - p["poziom"]
    # przesada w trendzie: RSI wchodzi za poziom, gdy trend jest wyraźny (trend sprawdzany w tej świecy)
    setup_short = ind.cross_above(rsi, hi) & down
    setup_long = ind.cross_below(rsi, lo) & up
    if p["wejscie"] == "przebicie":
        short, long_ = setup_short, setup_long
    else:
        # dowód wyczerpania: w ciągu 12 świec od przesady RSI wraca zza poziomu,
        # a świeca powrotu zamyka się w kierunku trendu
        recent_s = setup_short.astype(int).rolling(12, min_periods=1).max().shift(1).fillna(0) > 0
        recent_l = setup_long.astype(int).rolling(12, min_periods=1).max().shift(1).fillna(0) > 0
        short = ind.cross_below(rsi, hi) & (df.close < df.open) & recent_s
        long_ = ind.cross_above(rsi, lo) & (df.close > df.open) & recent_l

    if p["sesja"] != "wszystkie":
        h = ind.hour(df)
        ok = (h >= 7) & (h < 20)
        short, long_ = short & ok, long_ & ok

    return long_.astype("int8") - short.astype("int8")