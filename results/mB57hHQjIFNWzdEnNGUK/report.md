# Raport strategii: Gigant

Run `20261103-112354` · silnik 0.8.0 · kod `95df832624b0f8bd` · dane `ba7e470247ae9087`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -10.54 |
| percentyl benchmarku ≥ 95 | ✔ | 99.60 |
| PBO < 0,3 | ✔ | 0.18 |
| DSR ≥ 0,95 | ✘ | 0.65 |
| dodatni przy spreadzie ×1,5 | ✔ | 21.73 |

## Hipoteza

Konfiguracje wybrane przez ia5 search (D-044, przebieg 20261103-100928) z 3 124 224 przetestowanych, wyłącznie na IS (IS-A + IS-B).
Hipoteza: reguły, które przeszły FDR, potwierdzenie i płaskowyż na 8 parach, mają przewagę ponad koszty.
Uwaga: OOS był już raz otwarty przez poszukiwanie; DSR w karcie liczy tylko warianty tej strategii,
nie wszystkie próby poszukiwania — rozstrzyga forward test po zamrożeniu (W4).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 84** (12 wejścia × 7 wyjść).

- Pominięte sygnały, średnio na wariant: 32 (limit otwartych pozycji w parze), 0.7 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 2.4 (przerwa w dostępie do danych), 0.3 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 96 świecach | cfg=0 | 117 | 2.45 | 35.00 | 64.1 | 44 | -1.25 | -10.54 |
| 2 | po 96 świecach | cfg=4 | 113 | 2.37 | 40.44 | 65.5 | 51 | -0.37 | -15.80 |
| 3 | po 96 świecach | cfg=2 | 93 | 1.53 | 22.71 | 66.7 | 24 | 0.12 | -8.26 |
| 4 | po 96 świecach | cfg=8 | 224 | 1.50 | 20.74 | 60.7 | 69 | -0.16 | 6.86 |
| 5 | po 48 świecach | cfg=2 | 104 | 1.49 | 22.53 | 61.5 | 25 | -0.86 | -9.88 |
| 6 | po 48 świecach | cfg=4 | 134 | 1.40 | 26.78 | 60.4 | 59 | -0.15 | -10.06 |
| 7 | po 96 świecach | cfg=3 | 343 | 1.19 | 13.86 | 56.6 | 102 | -1.96 | -15.81 |
| 8 | po 48 świecach | cfg=7 | 265 | 1.12 | 17.50 | 55.1 | 71 | 0.76 | 4.32 |
| 9 | po 48 świecach | cfg=0 | 133 | 1.09 | 17.60 | 59.4 | 50 | -0.67 | -6.83 |
| 10 | po 48 świecach | cfg=5 | 310 | 1.07 | 20.17 | 56.8 | 97 | -0.50 | -4.15 |

## Najlepszy wariant IS: po 96 świecach (cfg=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 18 | 15.1 | 271.5 | 61.1 |
| EURGBP | 26 | -2.7 | -70.0 | 42.3 |
| EURJPY | 14 | 68.8 | 963.5 | 71.4 |
| EURUSD | 23 | 36.1 | 829.9 | 56.5 |
| GBPUSD | 21 | 11.8 | 247.2 | 52.4 |
| USDCAD | 23 | 6.4 | 148.2 | 56.5 |
| USDCHF | 22 | 27.0 | 593.6 | 72.7 |
| USDJPY | 14 | 46.2 | 646.8 | 71.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 12 | 49.0 | 587.8 | 75.0 |
| 2025 | 80 | 33.2 | 2 654.5 | 60.0 |
| 2026 | 69 | 5.6 | 388.3 | 55.1 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 117 | 35.0 | 4 094.5 | 64.1 |
| OOS | 44 | -10.5 | -463.8 | 45.5 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 15 776 | 57.8 | 25.6 | -12.5 | 1.36 | 0 |
| 10.0% | 24 008 | 140.1 | 54.9 | -23.8 | 1.37 | 0 |
| 15.0% | 36 599 | 266.0 | 91.2 | -34.0 | 1.41 | 1 |
| 20.0% | 50 122 | 401.2 | 123.7 | -43.5 | 1.38 | 5 |
| 30.0% | 79 755 | 697.5 | 182.2 | -59.8 | 1.42 | 27 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 22.55 pips/transakcję, percentyl **99.6** (losowe: 5%=-13.72, mediana=0.47, 95%=14.13).

- **Deflated Sharpe Ratio**: 0.648 (Sharpe na transakcję 0.383, próg przy 84 próbach 0.350).

- **PBO** (CSCV, 16 bloków, 84 wariantów): 0.180 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 102 transakcji, śr. 14.79 pips, 0.87 R.

- **Bootstrap 95%** średnich pipsów: całość [7.41; 38.60], OOS [-45.42; 22.45].

- **Spread**: ×1 22.55, ×1,5 21.73, ×2 20.91 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

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

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
