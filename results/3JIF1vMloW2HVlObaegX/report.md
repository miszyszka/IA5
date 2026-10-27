# Raport strategii: Strategia 2 (jedna pozycja)

Run `20261027-175940` · silnik 0.6.0 · kod `cca483791d82ca77` · dane `5d2ac9e95dedc57f`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -8.15 |
| percentyl benchmarku ≥ 95 | ✘ | 74.90 |
| PBO < 0,3 | ✘ | — |
| DSR ≥ 0,95 | ✘ | — |
| dodatni przy spreadzie ×1,5 | ✔ | 1.79 |

## Hipoteza

Wersja porównawcza do „RSI 70/30 w silnym trendzie — dokładanie”: te same wejścia (pierwsze przebicie
RSI14 70/30 przeciw wyraźnemu trendowi EMA200) i te same wyjścia, ale jedna pozycja na parę i stała stawka.
Różnica w wynikach pokaże, ile wnosi (albo kosztuje) dokładanie.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 276/282 mies. zatwierdzonych, 8 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 6 przerw w dostępie do danych (3147 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 29 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | — | 209 | 0.23 | 5.87 | 73.2 | 73 | -0.51 | -8.15 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 282 | 2.2 | 630.7 | 70.6 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 13 | 23.2 | 302.1 | 84.6 |
| 2004 | 8 | 16.9 | 135.3 | 75.0 |
| 2005 | 12 | -14.6 | -175.5 | 66.7 |
| 2006 | 11 | 5.6 | 61.2 | 81.8 |
| 2007 | 9 | -7.5 | -67.5 | 55.6 |
| 2008 | 13 | 27.4 | 356.8 | 69.2 |
| 2009 | 10 | 3.2 | 31.5 | 70.0 |
| 2010 | 11 | -9.3 | -102.0 | 72.7 |
| 2011 | 12 | 9.0 | 107.6 | 75.0 |
| 2012 | 19 | 4.1 | 78.5 | 68.4 |
| 2013 | 11 | -8.5 | -93.4 | 72.7 |
| 2014 | 13 | 3.7 | 48.3 | 69.2 |
| 2015 | 14 | 37.1 | 519.6 | 100.0 |
| 2016 | 11 | -0.4 | -3.9 | 63.6 |
| 2017 | 9 | 11.6 | 104.5 | 88.9 |
| 2018 | 12 | 2.4 | 29.2 | 75.0 |
| 2019 | 14 | -14.6 | -204.6 | 57.1 |
| 2020 | 8 | 15.3 | 122.6 | 75.0 |
| 2021 | 11 | -4.4 | -47.9 | 63.6 |
| 2022 | 12 | -33.3 | -399.4 | 41.7 |
| 2023 | 12 | -9.4 | -113.4 | 50.0 |
| 2024 | 20 | -2.3 | -46.7 | 70.0 |
| 2025 | 11 | -6.1 | -67.1 | 72.7 |
| 2026 | 6 | 9.1 | 54.7 | 83.3 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 209 | 5.9 | 1 226.0 | 73.2 |
| OOS | 73 | -8.2 | -595.3 | 63.0 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 712 | 7.1 | 0.3 | -10.4 | 0.12 | 0 |
| 10.0% | 11 329 | 13.3 | 0.5 | -20.1 | 0.12 | 0 |
| 15.0% | 11 825 | 18.2 | 0.7 | -29.0 | 0.12 | 0 |
| 20.0% | 12 174 | 21.7 | 0.9 | -37.1 | 0.12 | 0 |
| 30.0% | 12 360 | 23.6 | 0.9 | -51.4 | 0.12 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 2.24 pips/transakcję, percentyl **74.9** (losowe: 5%=-8.55, mediana=-0.91, 95%=6.11).

- **Deflated Sharpe Ratio**: — (Sharpe na transakcję —, próg przy 1 próbach —).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 171 transakcji, śr. -0.15 pips, -0.08 R.

- **Bootstrap 95%** średnich pipsów: całość [-4.38; 8.31], OOS [-19.84; 1.80].

- **Spread**: ×1 2.24, ×1,5 1.79, ×2 1.34, faktyczny 2.49 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Wersja porównawcza do „RSI 70/30 w silnym trendzie — dokładanie”: te same wejścia (pierwsze przebicie
RSI14 70/30 przeciw wyraźnemu trendowi EMA200) i te same wyjścia, ale jedna pozycja na parę i stała stawka.
Różnica w wynikach pokaże, ile wnosi (albo kosztuje) dokładanie."""

HOURS = False       # D-034: bez okna godzin, jak wersja z dokładaniem
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": 6, "level": 70, "cap": 120}]


def signals(df, p, ind):
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)
    rsi = ind.rsi(df.close, 14)
    short = (slope < -0.25) & ind.cross_above(rsi, 70)
    long_ = (slope > 0.25) & ind.cross_below(rsi, 30)
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
