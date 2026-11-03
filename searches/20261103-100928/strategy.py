HYPOTHESIS = """Konfiguracje wybrane przez ia5 search (D-044, przebieg 20261103-100928) z 3 124 224 przetestowanych, wyłącznie na IS (IS-A + IS-B).
Hipoteza: reguły, które przeszły FDR, potwierdzenie i płaskowyż na 8 parach, mają przewagę ponad koszty.
Uwaga: OOS był już raz otwarty przez poszukiwanie; DSR w karcie liczy tylko warianty tej strategii,
nie wszystkie próby poszukiwania — rozstrzyga forward test po zamrożeniu (W4)."""

CONFIGS = [
    {"trig": "bollinger", "kw": {"n": 20, "k": 3.0}, "tryb": -1, "trend": "brak", "zmiennosc": "brak", "sesja": "13-17", "dni": "pn-pt", "kierunek": "long"},   # po 96 świecach
    {"trig": "rsi", "kw": {"n": 5, "lvl": 20}, "tryb": -1, "trend": "brak", "zmiennosc": "brak", "sesja": "07-10", "dni": "wt-czw", "kierunek": "short"},   # ATR14 TP 0.75× SL 3× max 120
    {"trig": "impuls", "kw": {"k": 1, "th": 1.5}, "tryb": 1, "trend": "brak", "zmiennosc": "brak", "sesja": "07-10", "dni": "pn-pt", "kierunek": "long"},   # po 8 świecach
    {"trig": "macd", "kw": {"f": 5, "w": 35, "s": 5}, "tryb": 1, "trend": "przeciw_ema200", "zmiennosc": "brak", "sesja": "07-10", "dni": "pn-pt", "kierunek": "oba"},   # po 48 świecach
    {"trig": "duza", "kw": {"x": 2.5}, "tryb": -1, "trend": "przeciw_ema200", "zmiennosc": "brak", "sesja": "13-17", "dni": "pn-pt", "kierunek": "oba"},   # po 48 świecach
    {"trig": "impuls", "kw": {"k": 6, "th": 1.0}, "tryb": 1, "trend": "przeciw_ema200", "zmiennosc": "brak", "sesja": "07-17", "dni": "pn-pt", "kierunek": "oba"},   # po 48 świecach
    {"trig": "impuls", "kw": {"k": 3, "th": 1.0}, "tryb": -1, "trend": "przeciw_ema200", "zmiennosc": "ruch", "sesja": "13-17", "dni": "pn-pt", "kierunek": "oba"},   # ATR14 TP 1.5× SL 2× max 120
    {"trig": "duza", "kw": {"x": 1.5}, "tryb": 1, "trend": "brak", "zmiennosc": "brak", "sesja": "07-10", "dni": "pn-pt", "kierunek": "oba"},   # po 8 świecach
    {"trig": "wstega", "kw": {"s": "3,5,8,13,21"}, "tryb": 1, "trend": "przeciw_ema200", "zmiennosc": "brak", "sesja": "07-17", "dni": "pn-pt", "kierunek": "long"},   # po 96 świecach
    {"trig": "macd", "kw": {"f": 5, "w": 26, "s": 9}, "tryb": 1, "trend": "przeciw_ema200", "zmiennosc": "ruch", "sesja": "07-17", "dni": "pn-pt", "kierunek": "oba"},   # po 12 świecach
    {"trig": "rsi", "kw": {"n": 14, "lvl": 30}, "tryb": -1, "trend": "brak", "zmiennosc": "brak", "sesja": "10-13", "dni": "wt-czw", "kierunek": "oba"},   # ATR14 TP 1.5× SL 2× max 120
    {"trig": "bollinger", "kw": {"n": 50, "k": 2.0}, "tryb": -1, "trend": "zgodny_sma480", "zmiennosc": "brak", "sesja": "13-17", "dni": "pn-pt", "kierunek": "long"},   # po 4 świecach
]

PARAMS = {"cfg": list(range(len(CONFIGS)))}

# wyjścia wybranych konfiguracji (silnik liczy każdą konfigurację z każdym z nich)
EXITS = [
    {"kind": "time", "n": 96, "cap": 96},
    {"kind": "atr", "n": 14, "tp": 0.75, "sl": 3, "cap": 120},
    {"kind": "time", "n": 8, "cap": 8},
    {"kind": "time", "n": 48, "cap": 48},
    {"kind": "atr", "n": 14, "tp": 1.5, "sl": 2, "cap": 120},
    {"kind": "time", "n": 12, "cap": 12},
    {"kind": "time", "n": 4, "cap": 4},
]

# >>> REGUŁY
import math

import numpy as np
import pandas as pd


def _start(cond):
    """Pierwsza świeca, w której warunek jest spełniony (zdarzenie zamiast stanu)."""
    c = pd.Series(np.asarray(cond, dtype=bool))
    return (c & ~c.shift(1, fill_value=False)).to_numpy()


def _ev(up, dn):
    return np.asarray(up, dtype=bool).astype(np.int8) - np.asarray(dn, dtype=bool).astype(np.int8)


def t_wstega(df, ind, s):
    """Wstęga EMA (np. 5,10,15,25,40) układa się od najszybszej do najwolniejszej — początek ułożenia."""
    n = [int(x) for x in str(s).split(",")]
    m = [ind.ema(df["close"], k).to_numpy() for k in n]
    up = np.ones(len(df), bool)
    dn = np.ones(len(df), bool)
    for a, b in zip(m[:-1], m[1:]):
        up &= a > b
        dn &= a < b
    return _ev(_start(up), _start(dn))


def t_przeciecie(df, ind, typ, f, w):
    """Szybka średnia przecina wolną."""
    avg = ind.ema if typ == "ema" else ind.sma
    a, b = avg(df["close"], int(f)), avg(df["close"], int(w))
    return _ev(ind.cross_above(a, b), ind.cross_below(a, b))


def t_rsi(df, ind, n, lvl):
    """RSI wychodzi ze strefy skrajnej: w górę przez lvl (+1), w dół przez 100 − lvl (−1)."""
    r = ind.rsi(df["close"], int(n))
    return _ev(ind.cross_above(r, float(lvl)), ind.cross_below(r, 100.0 - float(lvl)))


def t_donchian(df, ind, n):
    """Zamknięcie ponad maksimum / pod minimum n POPRZEDNICH świec."""
    hi = ind.highest(df["high"], int(n)).shift(1)
    lo = ind.lowest(df["low"], int(n)).shift(1)
    return _ev(ind.cross_above(df["close"], hi), ind.cross_below(df["close"], lo))


def t_bollinger(df, ind, n, k):
    """Zamknięcie wychodzi poza wstęgę Bollingera."""
    b = ind.bollinger(df["close"], int(n), float(k))
    return _ev(ind.cross_above(df["close"], b["upper"]), ind.cross_below(df["close"], b["lower"]))


def t_impuls(df, ind, k, th):
    """Ruch z k świec w jednostkach ATR14·√k przekracza próg th."""
    k = int(k)
    mv = (df["close"] - df["close"].shift(k)) / (ind.atr(df, 14) * math.sqrt(k))
    return _ev(ind.cross_above(mv, float(th)), ind.cross_below(mv, -float(th)))


def t_azja(df, ind, bufor):
    """Wybicie zakresu nocy (świece przed 07:00 czasu polskiego tego samego dnia) o bufor × ATR14."""
    pl = df.index.tz_convert("Europe/Warsaw")
    day = pd.Series(pl.normalize(), index=df.index)
    night = pd.Series(pl.hour < 7, index=df.index)
    hi = df["high"].where(night).groupby(day).cummax().groupby(day).ffill()
    lo = df["low"].where(night).groupby(day).cummin().groupby(day).ffill()
    a = ind.atr(df, 14) * float(bufor)
    up = ind.cross_above(df["close"], hi + a) & ~night
    dn = ind.cross_below(df["close"], lo - a) & ~night
    return _ev(up, dn)


def t_wczoraj(df, ind, bufor):
    """Wybicie wczorajszego maksimum / minimum (dni UTC) o bufor × ATR14."""
    day = df.index.floor("D")
    hi = df["high"].groupby(day).max().shift(1).reindex(day).set_axis(df.index)
    lo = df["low"].groupby(day).min().shift(1).reindex(day).set_axis(df.index)
    a = ind.atr(df, 14) * float(bufor)
    return _ev(ind.cross_above(df["close"], hi + a), ind.cross_below(df["close"], lo - a))


def t_scisk(df, ind, x, n):
    """Wybicie z ciszy: ATR5/ATR50 na poprzedniej świecy < x, zamknięcie poza zakresem n poprzednich świec."""
    quiet = ((ind.atr(df, 5) / ind.atr(df, 50)) < float(x)).shift(1, fill_value=False)
    hi = ind.highest(df["high"], int(n)).shift(1)
    lo = ind.lowest(df["low"], int(n)).shift(1)
    return _ev(ind.cross_above(df["close"], hi) & quiet, ind.cross_below(df["close"], lo) & quiet)


def t_macd(df, ind, f, w, s):
    """Histogram MACD zmienia znak."""
    h = ind.macd(df["close"], int(f), int(w), int(s))["hist"]
    return _ev(ind.cross_above(h, 0.0), ind.cross_below(h, 0.0))


def t_stoch(df, ind, k, lvl):
    """Stochastyk %K wychodzi ze strefy skrajnej (w górę przez lvl, w dół przez 100 − lvl)."""
    st = ind.stoch(df, int(k), 3, 3)["k"]
    return _ev(ind.cross_above(st, float(lvl)), ind.cross_below(st, 100.0 - float(lvl)))


def t_seria(df, ind, n):
    """n zamknięć z rzędu wyżej (+1) / niżej (−1) niż poprzednie — w świecy, w której seria osiąga n."""
    d = df["close"].diff()
    up = (d > 0).astype(int).rolling(int(n)).sum()
    dn = (d < 0).astype(int).rolling(int(n)).sum()
    return _ev(ind.cross_above(up, int(n) - 0.5), ind.cross_above(dn, int(n) - 0.5))


def t_duza(df, ind, x):
    """Świeca o korpusie większym niż x × ATR14 z poprzedniej świecy (w kierunku korpusu)."""
    body = df["close"] - df["open"]
    a = ind.atr(df, 14).shift(1) * float(x)
    return _ev(body > a, body < -a)


TRIGGERS = {
    "wstega": t_wstega, "przeciecie": t_przeciecie, "rsi": t_rsi, "donchian": t_donchian, "bollinger": t_bollinger,
    "impuls": t_impuls, "azja": t_azja, "wczoraj": t_wczoraj, "scisk": t_scisk, "macd": t_macd, "stoch": t_stoch,
    "seria": t_seria, "duza": t_duza,
}

# Filtry: liczone w świecy sygnału t tylko z przeszłości; godzina i dzień — świecy wejścia (t+1), czasu polskiego.
TREND = {"brak": None, "zgodny_ema200": ("ema200", 1), "zgodny_sma480": ("sma480", 1), "przeciw_ema200": ("ema200", -1)}
ZMIENNOSC = {"brak": None, "cisza": (0.0, 0.8), "ruch": (1.2, 1e9)}
SESJA = {"07-17": (7, 17), "07-10": (7, 10), "10-13": (10, 13), "13-17": (13, 17)}
DNI = {"pn-pt": (0, 1, 2, 3, 4), "wt-czw": (1, 2, 3)}
KIERUNEK = {"oba": 0, "long": 1, "short": -1}


def features(df, ind):
    """Cechy świec potrzebne filtrom (jedna tablica na cechę)."""
    c = df["close"]
    nxt = (df.index + pd.Timedelta(hours=1)).tz_convert("Europe/Warsaw")
    return {
        "ema200": np.sign((c - ind.ema(c, 200)).to_numpy()),
        "sma480": np.sign((c - ind.sma(c, 480)).to_numpy()),
        "vol": (ind.atr(df, 14) / ind.atr(df, 100)).to_numpy(),
        "hour": np.asarray(nxt.hour),
        "wd": np.asarray(nxt.dayofweek),
    }


def filter_mask(F, i, d, trend, zmiennosc, sesja, dni, kierunek):
    """Które sygnały (świece i, kierunki d) przechodzą przez filtry."""
    i = np.asarray(i)
    d = np.asarray(d)
    m = np.ones(len(i), bool)
    t = TREND[trend]
    if t is not None:
        m &= F[t[0]][i] * t[1] == d
    v = ZMIENNOSC[zmiennosc]
    if v is not None:
        x = F["vol"][i]
        m &= (x >= v[0]) & (x < v[1])
    a, b = SESJA[sesja]
    m &= (F["hour"][i] >= a) & (F["hour"][i] < b)
    m &= np.isin(F["wd"][i], DNI[dni])
    k = KIERUNEK[kierunek]
    if k != 0:
        m &= d == k
    return m


def config_signal(df, ind, cfg):
    """Sygnał jednej konfiguracji: wyzwalacz × tryb, potem filtry."""
    s = TRIGGERS[cfg["trig"]](df, ind, **cfg["kw"]).astype(np.int8) * int(cfg["tryb"])
    i = np.flatnonzero(s)
    m = filter_mask(features(df, ind), i, s[i], cfg["trend"], cfg["zmiennosc"], cfg["sesja"], cfg["dni"], cfg["kierunek"])
    out = np.zeros(len(s), np.int8)
    out[i[m]] = s[i[m]]
    return out
# <<< KONIEC REGUŁ


def signals(df, p, ind):
    return config_signal(df, ind, CONFIGS[p["cfg"]])
