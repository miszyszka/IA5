import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058); wejście na open następnego dnia (rano)

HYPOTHESIS = """Na świecach dziennych par FX trend trwa miesiącami, a krótkie wyprzedanie w trendzie wzrostowym (i wykupienie
w spadkowym) zwykle się cofa w ciągu kilku dni. Kupujemy, gdy RSI spada pod próg, ale tylko gdy cena jest nad rosnącą SMA200
(sprzedajemy lustrzanie pod opadającą SMA200). Bez filtra trendu czysty powrót RSI na D1 po spreadzie nie zarabia — to
sprawdziło poszukiwanie (research/rsi_d1/README.md). Wersje różnią się progiem RSI, wyjściem (po X dniach na zamknięciu,
TP/SL w ATR, stop pod dołkiem) i stawką: stała, rosnąca z kolejną świecą wyprzedania, z liczbą otwartych pozycji, z głębokością RSI.
Konfiguracje wybrane wyłącznie na IS (przed 2019-05); wynik OOS badania jest w raporcie poszukiwania."""

# Każda konfiguracja = jedna wersja strategii (wariant wejścia); × 3 limity czasu z EXITS.
#   rsi:   reguły (okres RSI, próg wyprzedania); wykupienie = 100 − próg; kilka reguł = sygnał, gdy spełniona dowolna
#   tryb:  "stan" — sygnał w każdej świecy za progiem (z PYRAMID dokładanie pozycji); "zdarzenie" — pierwsza świeca za progiem
#   trend: "sma200_rosnie" — long tylko nad SMA200, która rośnie od 20 dni (short lustrzanie); "sma200" — tylko cena vs SMA200
#   tp/sl: None = bez poziomu (wyjście tylko po limicie dni, na zamknięciu); ("atr", k) = k × ATR14 od zamknięcia dnia sygnału;
#          ("dolek", k, b) = SL pod najniższym low k dni − b × ATR14; ("r", m) = TP w m × odległości do SL
#   waga:  "stala" 1; "seria" = która z kolei świeca za progiem (1, 2, 3+); "otwarte" = 1 + sygnały w tym kierunku w 5 poprzednich
#          dniach (≈ liczba otwartych pozycji), najwyżej 3; "glebokosc" = 0,5 + 2 × głębokość RSI za progiem (0,5–2,5)
CONFIGS = [
    # 0 = wybór po IS (stabilność: najwięcej zyskownych kwartałów i lat przy największej liczbie transakcji)
    {"rsi": ((3, 15), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((3, 15), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 3), "sl": ("atr", 1.5), "waga": "otwarte"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": ("atr", 1.5), "waga": "seria"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 3), "sl": ("atr", 1), "waga": "seria"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "stala"},   # 6 = stała stawka, do porównania z 1, 7, 8
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "otwarte"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "glebokosc"},
    {"rsi": ((5, 25),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 1.5), "sl": ("atr", 1), "waga": "otwarte"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("r", 2), "sl": ("dolek", 5, 0.5), "waga": "seria"},
    {"rsi": ((14, 35),), "tryb": "stan", "trend": "sma200", "tp": ("szczyt", 5), "sl": ("dolek", 5, 0), "waga": "stala"},
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

PYRAMID = 3   # do 3 pozycji naraz w parze, tylko w jednym kierunku (dokładanie, D-034)
EXITS = [{"kind": "level", "cap": c} for c in (3, 5, 10)]   # wyjście po 3 / 5 / 10 dniach na zamknięciu, chyba że wcześniej TP/SL
# Stawka bazowa (% kapitału jako depozyt, × 30 nominału) — mniejsza niż domyślne 5–30%, bo waga mnoży ją do 3×,
# PYRAMID dokłada do 3 pozycji w parze, a 8 par z USD porusza się razem: przy 5% obsunięcie IS przekracza 90%.
SIZING = [1, 2, 3, 5]


def _streak(mask):
    """Która z kolei świeca w serii True (0 poza serią)."""
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def _setup(df, c, ind, full=True):
    """Kierunek sygnału (+1 long / −1 short / 0) i cechy do stawki — tylko z zamkniętych świec."""
    close = df.close
    n = len(df)
    lo, hi = np.zeros(n, bool), np.zeros(n, bool)
    zone_lo, zone_hi = np.zeros(n, bool), np.zeros(n, bool)
    depth_lo, depth_hi = np.zeros(n), np.zeros(n)
    for period, level in c["rsi"]:
        rs = ind.rsi(close, period)
        r = np.array(rs, dtype=float)
        ok = ~np.isnan(r)
        with np.errstate(invalid="ignore"):
            a, b = ok & (r < level), ok & (r > 100 - level)
        zone_lo |= a
        zone_hi |= b
        depth_lo = np.where(a, np.fmax(depth_lo, (level - r) / level), depth_lo)
        depth_hi = np.where(b, np.fmax(depth_hi, (r - (100 - level)) / level), depth_hi)
        if c["tryb"] == "zdarzenie":
            a = ind.cross_below(rs, level).to_numpy(bool) & ok
            b = ind.cross_above(rs, 100 - level).to_numpy(bool) & ok
        lo |= a
        hi |= b
    s200 = ind.sma(close, 200)
    up, dn = np.array(close > s200, dtype=bool), np.array(close < s200, dtype=bool)
    if c["trend"] == "sma200_rosnie":
        up &= ind.rising(s200, 20).to_numpy(bool)
        dn &= ind.falling(s200, 20).to_numpy(bool)
    direction = (lo & up).astype(int) - (hi & dn).astype(int)
    if not full:
        return direction, None, None, None
    streak = np.where(direction > 0, _streak(zone_lo), np.where(direction < 0, _streak(zone_hi), 0))
    depth = np.where(direction > 0, depth_lo, np.where(direction < 0, depth_hi, 0.0))
    past = np.r_[0, np.cumsum(direction > 0)][:-1], np.r_[0, np.cumsum(direction < 0)][:-1]   # do świecy t−1
    up_n = past[0] - np.r_[np.zeros(5, np.int64), past[0]][:n]                               # sygnały long w t−5 … t−1
    dn_n = past[1] - np.r_[np.zeros(5, np.int64), past[1]][:n]
    recent = np.where(direction > 0, up_n, np.where(direction < 0, dn_n, 0))
    return direction, streak, depth, recent


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    direction, streak, depth, recent = _setup(df, c, ind)
    if c["waga"] == "seria":
        w = np.clip(streak, 1, 3).astype(float)
    elif c["waga"] == "otwarte":
        w = np.clip(1 + recent, 1, 3).astype(float)
    elif c["waga"] == "glebokosc":
        w = np.clip(0.5 + 2 * depth, 0.5, 2.5)
    else:
        w = np.ones(len(df))
    return pd.Series(np.where(direction != 0, direction * w, 0.0), index=df.index)


def levels(df, p, ind):
    c = CONFIGS[p["cfg"]]
    sl = pd.Series(np.nan, index=df.index)
    tp = pd.Series(np.nan, index=df.index)
    if c["sl"] is None and c["tp"] is None:   # wyjście tylko po limicie dni (na zamknięciu)
        return pd.DataFrame({"tp": tp, "sl": sl})
    direction, *_ = _setup(df, c, ind, full=False)
    d = pd.Series(np.where(direction != 0, direction, np.nan), index=df.index)   # poziomy tylko na świecach sygnału
    atr = ind.atr(df, 14)
    close = df.close
    if c["sl"] is not None:
        if c["sl"][0] == "atr":
            sl = close - d * c["sl"][1] * atr
        else:                                  # ("dolek", k, b): pod najniższym low k dni (long) / nad najwyższym high (short)
            k, b = c["sl"][1], c["sl"][2]
            sl = (ind.lowest(df.low, k) - b * atr).where(d > 0, ind.highest(df.high, k) + b * atr).where(d.notna())
    if c["tp"] is not None:
        if c["tp"][0] == "atr":
            tp = close + d * c["tp"][1] * atr
        elif c["tp"][0] == "r":
            tp = close + c["tp"][1] * (close - sl)
        else:                                  # ("szczyt", k): najwyższe high k dni (long) / najniższe low (short)
            k = c["tp"][1]
            tp = ind.highest(df.high, k).where(d > 0, ind.lowest(df.low, k)).where(d.notna())
    return pd.DataFrame({"tp": tp, "sl": sl})
