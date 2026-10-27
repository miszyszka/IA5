# Raport strategii: Strategia 4

Run `20261027-183217` · silnik 0.7.0 · kod `72c5bb26bb5578fd` · dane `f8d8bc72a0207c72`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -7.72 |
| percentyl benchmarku ≥ 95 | ✘ | 94.80 |
| PBO < 0,3 | ✘ | 0.38 |
| DSR ≥ 0,95 | ✘ | 0.66 |
| dodatni przy spreadzie ×1,5 | ✔ | 6.87 |

## Hipoteza

Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu. Przegrywamy często, ale mało (stop w ATR), wygrywamy rzadko, ale dużo —
przewaga jest w asymetrii, nie w trafności.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 282/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 3 przerw w dostępie do danych (93 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 96** (8 wejścia × 12 wyjść).

- Pominięte sygnały, średnio na wariant: 1,207 (limit otwartych pozycji w parze), 0.7 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 2.8 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | sygnał przeciwny, SL 2×ATR14, max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 643 | 0.28 | 13.23 | 21.0 | 253 | -0.28 | -7.72 |
| 2 | sygnał przeciwny, SL 2×ATR14, max 480 | kanal=120, filtr_d1=False, sesja=wszystkie | 754 | 0.19 | 7.05 | 19.8 | 293 | -0.26 | -7.32 |
| 3 | ATR14 TP 6× SL 1.5× max 120 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 716 | 0.14 | 4.54 | 25.0 | 255 | -0.05 | 0.01 |
| 4 | sygnał przeciwny, SL 2×ATR14, max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 414 | 0.14 | 6.54 | 11.6 | 139 | -0.10 | -0.03 |
| 5 | sygnał przeciwny, SL 2×ATR14, max 480 | kanal=240, filtr_d1=True, sesja=7-20 UTC | 351 | 0.14 | 5.49 | 12.5 | 121 | -0.03 | 1.29 |
| 6 | sygnał przeciwny, SL 3×ATR14, max 480 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 393 | 0.14 | 10.12 | 20.6 | 163 | -0.25 | -10.00 |
| 7 | sygnał przeciwny, SL 3×ATR14, max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 564 | 0.13 | 9.50 | 25.9 | 218 | -0.24 | -11.38 |
| 8 | ATR14 TP 6× SL 1.5× max 120 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 827 | 0.13 | 3.45 | 24.8 | 328 | -0.17 | -3.35 |
| 9 | ATR14 TP 6× SL 1.5× max 480 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 820 | 0.13 | 3.03 | 23.4 | 329 | -0.19 | -3.65 |
| 10 | ATR14 TP 6× SL 1.5× max 120 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 1 211 | 0.12 | 3.83 | 24.4 | 445 | -0.14 | -3.03 |

## Najlepszy wariant IS: sygnał przeciwny, SL 2×ATR14, max 480 (kanal=120, filtr_d1=False, sesja=7-20 UTC)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 896 | 7.3 | 6 554.7 | 19.5 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 15 | 92.6 | 1 389.3 | 46.7 |
| 2004 | 40 | -1.7 | -69.3 | 17.5 |
| 2005 | 38 | 8.3 | 316.7 | 26.3 |
| 2006 | 37 | -0.8 | -28.7 | 18.9 |
| 2007 | 36 | 8.0 | 287.8 | 25.0 |
| 2008 | 33 | 85.9 | 2 833.8 | 24.2 |
| 2009 | 35 | 3.7 | 129.4 | 20.0 |
| 2010 | 29 | 79.0 | 2 291.8 | 31.0 |
| 2011 | 33 | 13.9 | 460.0 | 24.2 |
| 2012 | 33 | 19.8 | 654.1 | 21.2 |
| 2013 | 29 | 5.0 | 145.3 | 27.6 |
| 2014 | 36 | -6.8 | -243.3 | 11.1 |
| 2015 | 31 | 44.4 | 1 377.0 | 25.8 |
| 2016 | 41 | -12.1 | -497.1 | 14.6 |
| 2017 | 42 | -1.5 | -63.9 | 19.0 |
| 2018 | 45 | -3.7 | -164.3 | 17.8 |
| 2019 | 48 | -13.9 | -664.9 | 14.6 |
| 2020 | 44 | 6.7 | 292.9 | 15.9 |
| 2021 | 35 | 5.9 | 206.3 | 20.0 |
| 2022 | 41 | -10.0 | -410.1 | 17.1 |
| 2023 | 51 | -11.5 | -588.5 | 13.7 |
| 2024 | 45 | -1.7 | -77.0 | 17.8 |
| 2025 | 45 | -18.3 | -822.6 | 11.1 |
| 2026 | 34 | -5.9 | -200.1 | 17.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 643 | 13.2 | 8 508.6 | 21.0 |
| OOS | 253 | -7.7 | -1 953.9 | 15.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 17 728 | 77.3 | 2.5 | -37.1 | 0.24 | 0 |
| 10.0% | 25 378 | 153.8 | 4.0 | -61.9 | 0.24 | 0 |
| 15.0% | 30 074 | 200.7 | 4.8 | -77.8 | 0.24 | 0 |
| 20.0% | 30 080 | 200.8 | 4.8 | -87.4 | 0.24 | 0 |
| 30.0% | 19 193 | 91.9 | 2.8 | -96.4 | 0.24 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 7.32 pips/transakcję, percentyl **94.8** (losowe: 5%=-7.18, mediana=-0.49, 95%=7.58).

- **Deflated Sharpe Ratio**: 0.659 (Sharpe na transakcję 0.080, próg przy 96 próbach 0.067).

- **PBO** (CSCV, 16 bloków, 96 wariantów): 0.380 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 576 transakcji, śr. -3.17 pips, -0.11 R.

- **Bootstrap 95%** średnich pipsów: całość [-1.87; 16.57], OOS [-15.52; 1.29].

- **Spread**: ×1 7.32, ×1,5 6.87, ×2 6.42, faktyczny 7.63 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu. Przegrywamy często, ale mało (stop w ATR), wygrywamy rzadko, ale dużo —
przewaga jest w asymetrii, nie w trafności."""

HOURS = False   # okno godzin jako parametr „sesja”

PARAMS = {
    "kanal": [120, 240],                    # wybicie maksimum/minimum z 120 lub 240 poprzednich świec H1 (~5 / ~10 dni)
    "filtr_d1": [False, True],              # trend dzienny: zamknięcie D1 nad EMA50(D1) i EMA50 rośnie (short lustrzanie)
    "sesja": ["wszystkie", "7-20 UTC"],
}

# Wyjścia dopasowane do trendu: duże TP albo wyjście, gdy trend się kończy; zawsze stop w ATR; do 20 dni (480 świec)
EXITS = (
    [{"kind": "atr", "n": 14, "tp": tp, "sl": sl, "cap": cap}
     for tp in (3.0, 6.0) for sl in (1.5, 3.0) for cap in (120, 480)]
    + [{"kind": "sma", "n": 14, "sl": sl, "cap": 480} for sl in (2.0, 3.0)]        # zamknięcie po złej stronie SMA20
    + [{"kind": "opposite", "n": 14, "sl": sl, "cap": 480} for sl in (2.0, 3.0)]   # wybicie w przeciwną stronę
)


def d1_trend(df, ind):
    """Trend D1 bez look-ahead: tylko zamknięte dni (shift(1)), przeniesione na H1."""
    d1 = df.close.resample("1D").last().dropna()
    e = ind.ema(d1, 50)
    up = ((d1 > e) & ind.rising(e, 5)).shift(1)
    down = ((d1 < e) & ind.falling(e, 5)).shift(1)
    to_h1 = lambda s: s.reindex(df.index, method="ffill").fillna(False).astype(bool)  # noqa: E731
    return to_h1(up), to_h1(down)


def signals(df, p, ind):
    n = p["kanal"]
    top = ind.highest(df.high, n).shift(1)       # maksimum n POPRZEDNICH świec (bez bieżącej)
    bottom = ind.lowest(df.low, n).shift(1)
    long_ = ind.cross_above(df.close, top)        # pierwsze zamknięcie nad kanałem
    short = ind.cross_below(df.close, bottom)

    if p["filtr_d1"]:
        up, down = d1_trend(df, ind)
        long_, short = long_ & up, short & down

    if p["sesja"] != "wszystkie":
        h = ind.hour(df)
        ok = (h >= 7) & (h < 20)
        long_, short = long_ & ok, short & ok

    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
