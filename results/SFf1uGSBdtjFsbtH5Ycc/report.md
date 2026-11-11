# Raport strategii: d1

Run `20261111-100235` · silnik 0.11.0 · kod `4d2581768eb31d00` · dane `3197cf8521901cb3`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 2 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 0.97 |
| percentyl benchmarku ≥ 95 | ✘ | 93.20 |
| PBO < 0,3 | ✘ | 0.40 |
| DSR ≥ 0,95 | ✘ | 0.20 |
| dodatni przy spreadzie ×1,5 | ✔ | 38.25 |

## Hipoteza

Na świecach dziennych krótkoterminowe przewartościowanie w kierunku trendu wraca do średniej: po 2–3 dniach
silnej korekty (RSI z 2 dni na dnie skali) cena w długim trendzie zwykle odbija, bo korekta to dla trendu szum, a nie zmiana
kierunku. To dzienny odpowiednik żywej strategii „RSI 2” z H1, ale na ok. 20 latach zamiast 2 — H1 miała za krótką próbę
(OOS 6 miesięcy), a tu OOS to ok. 5 lat i wiele reżimów rynku.
Wejście (zdarzenie, nie stan): RSI(2) przebija od góry poziom `rsi_level` (5/10/15), gdy zamknięcie jest nad SMA trendu
(100 albo 200 dni) — long; lustrzanie short: RSI(2) przebija od dołu 100 − poziom, gdy zamknięcie jest pod SMA.
Wyjścia z domyślnej siatki silnika w dniach (ATR dzienny). Do sprawdzenia przy walidacji: koszt nocy (D-054) i to, czy wynik
nie pochodzi wyłącznie z wariantów bez stopu — poprzednia wersja na H1 oblała DSR właśnie przez brak stopu.
Zapisane PRZED liczeniem; 6 wariantów wejścia.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1398** (6 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 546 (limit otwartych pozycji w parze), 4.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 4.2 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 72 świecach | rsi_level=15, trend=100 | 396 | 0.52 | 55.62 | 49.5 | 172 | 0.01 | 0.97 |
| 2 | po 72 świecach | rsi_level=5, trend=200 | 293 | 0.51 | 44.31 | 54.3 | 131 | 0.14 | 12.57 |
| 3 | po 48 świecach | rsi_level=5, trend=100 | 340 | 0.48 | 62.65 | 55.3 | 166 | 0.11 | 1.13 |
| 4 | po 120 świecach | rsi_level=5, trend=100 | 196 | 0.48 | 63.62 | 52.6 | 88 | 0.67 | 71.65 |
| 5 | po 72 świecach | rsi_level=5, trend=100 | 277 | 0.47 | 62.84 | 51.6 | 123 | -0.37 | -22.34 |
| 6 | po 72 świecach | rsi_level=10, trend=100 | 368 | 0.39 | 48.70 | 52.4 | 163 | -0.43 | -36.94 |
| 7 | po 96 świecach | rsi_level=10, trend=100 | 286 | 0.38 | 32.66 | 50.3 | 127 | -0.65 | -50.57 |
| 8 | po 96 świecach | rsi_level=15, trend=100 | 307 | 0.37 | 22.54 | 51.5 | 133 | -1.01 | -81.80 |
| 9 | po 36 świecach | rsi_level=10, trend=100 | 603 | 0.35 | 41.17 | 50.7 | 268 | 0.06 | 23.55 |
| 10 | po 48 świecach | rsi_level=10, trend=100 | 500 | 0.31 | 38.73 | 54.0 | 219 | -0.12 | -4.83 |

## Najlepszy wariant IS: po 72 świecach (rsi_level=15, trend=100)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 61 | 15.4 | 938.5 | 45.9 |
| EURGBP | 84 | 16.2 | 1 358.2 | 45.2 |
| EURJPY | 68 | 48.5 | 3 294.9 | 50.0 |
| EURUSD | 66 | 105.7 | 6 975.8 | 50.0 |
| GBPUSD | 68 | 130.0 | 8 840.0 | 55.9 |
| USDCAD | 69 | 19.9 | 1 370.4 | 49.3 |
| USDCHF | 68 | -30.0 | -2 039.8 | 44.1 |
| USDJPY | 84 | 17.3 | 1 457.1 | 52.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 1997 | 1 | -493.4 | -493.4 | 0.0 |
| 1998 | 4 | 129.3 | 517.4 | 75.0 |
| 1999 | 3 | -630.5 | -1 891.5 | 33.3 |
| 2000 | 6 | -82.4 | -494.3 | 50.0 |
| 2001 | 7 | -30.5 | -213.7 | 42.9 |
| 2002 | 6 | 42.3 | 253.7 | 16.7 |
| 2003 | 8 | -3.9 | -31.1 | 37.5 |
| 2004 | 18 | -112.7 | -2 029.1 | 38.9 |
| 2005 | 22 | 99.5 | 2 188.2 | 50.0 |
| 2006 | 20 | 74.5 | 1 489.3 | 50.0 |
| 2007 | 26 | 91.9 | 2 390.0 | 53.8 |
| 2008 | 22 | 538.2 | 11 840.9 | 63.6 |
| 2009 | 24 | 280.0 | 6 719.7 | 54.2 |
| 2010 | 24 | 22.5 | 539.7 | 45.8 |
| 2011 | 24 | 70.9 | 1 702.1 | 66.7 |
| 2012 | 24 | -229.4 | -5 505.9 | 29.2 |
| 2013 | 23 | 166.0 | 3 817.9 | 56.5 |
| 2014 | 25 | -58.5 | -1 463.7 | 44.0 |
| 2015 | 22 | 71.8 | 1 580.5 | 50.0 |
| 2016 | 27 | 105.7 | 2 855.2 | 55.6 |
| 2017 | 23 | -24.4 | -560.6 | 39.1 |
| 2018 | 25 | -33.7 | -841.4 | 56.0 |
| 2019 | 23 | -43.5 | -999.5 | 47.8 |
| 2020 | 23 | 14.6 | 335.0 | 52.2 |
| 2021 | 23 | 85.2 | 1 959.3 | 60.9 |
| 2022 | 23 | 235.8 | 5 422.3 | 65.2 |
| 2023 | 24 | -34.0 | -817.2 | 45.8 |
| 2024 | 27 | -159.7 | -4 311.5 | 22.2 |
| 2025 | 21 | -98.3 | -2 063.3 | 47.6 |
| 2026 | 20 | 15.0 | 300.0 | 50.0 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 396 | 55.6 | 22 027.5 | 49.5 |
| OOS | 172 | 1.0 | 167.7 | 48.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 14 244 | 42.4 | 1.2 | -82.2 | -92.2 | 0.16 | 0 |
| 10.0% | -6 068 | -160.7 | -100.0 | -106.8 | -172.2 | 0.21 | 343 |
| 15.0% | -5 359 | -153.6 | -100.0 | -113.1 | -194.9 | 0.22 | 375 |
| 20.0% | -190 | -101.9 | -100.0 | -100.9 | -134.3 | 0.19 | 464 |
| 30.0% | -7 715 | -177.2 | -100.0 | -130.5 | -201.5 | 0.06 | 563 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 39.08 pips/transakcję, percentyl **93.2** (losowe: 5%=-35.52, mediana=2.28, 95%=43.15).

- **Deflated Sharpe Ratio**: 0.204 (Sharpe na transakcję 0.092, próg przy 1398 próbach 0.133).

- **PBO** (CSCV, 16 bloków, 1398 wariantów): 0.400 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 327 transakcji, śr. -59.84 pips, -0.66 R.

- **Bootstrap 95%** średnich pipsów: całość [-7.23; 83.28], OOS [-60.42; 61.27].

- **Spread**: ×1 39.08, ×1,5 38.25, ×2 37.43 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 103.5 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -12.69, 1 pips: -64.45 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """Na świecach dziennych krótkoterminowe przewartościowanie w kierunku trendu wraca do średniej: po 2–3 dniach
silnej korekty (RSI z 2 dni na dnie skali) cena w długim trendzie zwykle odbija, bo korekta to dla trendu szum, a nie zmiana
kierunku. To dzienny odpowiednik żywej strategii „RSI 2” z H1, ale na ok. 20 latach zamiast 2 — H1 miała za krótką próbę
(OOS 6 miesięcy), a tu OOS to ok. 5 lat i wiele reżimów rynku.
Wejście (zdarzenie, nie stan): RSI(2) przebija od góry poziom `rsi_level` (5/10/15), gdy zamknięcie jest nad SMA trendu
(100 albo 200 dni) — long; lustrzanie short: RSI(2) przebija od dołu 100 − poziom, gdy zamknięcie jest pod SMA.
Wyjścia z domyślnej siatki silnika w dniach (ATR dzienny). Do sprawdzenia przy walidacji: koszt nocy (D-054) i to, czy wynik
nie pochodzi wyłącznie z wariantów bez stopu — poprzednia wersja na H1 oblała DSR właśnie przez brak stopu.
Zapisane PRZED liczeniem; 6 wariantów wejścia."""

PARAMS = {"rsi_level": [5, 10, 15], "trend": [100, 200]}


def signals(df, p, ind):
    sma = ind.sma(df.close, p["trend"])
    rsi = ind.rsi(df.close, 2)
    long_ = (df.close > sma) & ind.cross_below(rsi, p["rsi_level"])
    short = (df.close < sma) & ind.cross_above(rsi, 100 - p["rsi_level"])
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
