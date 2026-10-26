# Raport strategii: DEMO · SMA200 rośnie + RSI poniżej progu

Run `20261026-152110` · silnik 0.0.1 · kod `e7358eef8dfb6cc3` · dane `94c50fcf4885a784`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 13.23 |
| percentyl benchmarku ≥ 95 | ✘ | 49.50 |
| PBO < 0,3 | ✔ | 0.15 |
| DSR ≥ 0,95 | ✘ | 0.35 |
| dodatni przy spreadzie ×1,5 | ✔ | 13.96 |

## Hipoteza

Gdy długoterminowy trend jest wzrostowy (SMA200 rośnie), głębokie krótkoterminowe
wyprzedanie (RSI14 spada poniżej progu) jest chwilowe i cena wraca w górę.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2017-04-19 do 2018-02-07; źródło: DEMO: przykładowe świece EUR/USD H1 2017–2018 z pakietu backtesting.py (nie Twoja baza).

- In-sample do 2017-11-26, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale. TP i SL w tej samej świecy: przyjęty SL (brak danych M1).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Kapitał 10,000 USD, dźwignia 1:5, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1398** (6 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 19 (otwarta pozycja w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 48 świecach | rsi_level=40, slope_bars=20 | 30 | 1.75 | 14.88 | 53.3 | 12 | 0.87 | 13.22 |
| 2 | po 36 świecach | rsi_level=40, slope_bars=20 | 36 | 1.54 | 14.23 | 55.6 | 15 | 0.88 | 12.29 |
| 3 | po 36 świecach | rsi_level=40, slope_bars=5 | 32 | 1.53 | 14.98 | 56.2 | 15 | 0.88 | 12.29 |
| 4 | po 24 świecach | rsi_level=40, slope_bars=5 | 37 | 1.34 | 13.39 | 54.1 | 16 | 0.53 | 8.47 |
| 5 | po 16 świecach | rsi_level=40, slope_bars=5 | 48 | 1.21 | 13.31 | 58.3 | 20 | 0.90 | 15.07 |
| 6 | po 24 świecach | rsi_level=40, slope_bars=20 | 42 | 1.12 | 10.63 | 52.4 | 16 | 0.53 | 8.47 |
| 7 | po 16 świecach | rsi_level=40, slope_bars=20 | 52 | 1.09 | 11.68 | 57.7 | 21 | 0.74 | 12.78 |
| 8 | po 12 świecach | rsi_level=40, slope_bars=5 | 50 | 1.06 | 10.63 | 50.0 | 23 | 0.94 | 16.03 |
| 9 | po 12 świecach | rsi_level=40, slope_bars=20 | 55 | 0.99 | 9.87 | 52.7 | 24 | 0.88 | 15.01 |
| 10 | po 16 świecach | rsi_level=35, slope_bars=20 | 30 | 0.83 | 10.67 | 60.0 | 8 | -0.43 | -4.10 |

## Najlepszy wariant IS: po 48 świecach (rsi_level=40, slope_bars=20)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 42 | 14.4 | 605.1 | 57.1 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2017 | 34 | 12.4 | 421.4 | 52.9 |
| 2018 | 8 | 23.0 | 183.7 | 75.0 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 30 | 14.9 | 446.4 | 53.3 |
| OOS | 12 | 13.2 | 158.7 | 66.7 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 132 | 1.3 | 1.7 | -0.7 | 1.23 | 0 |
| 10.0% | 10 265 | 2.7 | 3.5 | -1.3 | 1.23 | 0 |
| 15.0% | 10 399 | 4.0 | 5.2 | -2.0 | 1.23 | 0 |
| 20.0% | 10 533 | 5.3 | 7.0 | -2.7 | 1.23 | 0 |
| 30.0% | 10 803 | 8.0 | 10.6 | -4.0 | 1.23 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 14.41 pips/transakcję, percentyl **49.5** (losowe: 5%=-4.34, mediana=14.60, 95%=34.34).

- **Deflated Sharpe Ratio**: 0.346 (Sharpe na transakcję 0.263, próg przy 799 próbach 0.319).

- **PBO** (CSCV, 16 bloków, 959 wariantów): 0.145 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 32 transakcji, śr. 8.05 pips, 0.78 R.

- **Bootstrap 95%** średnich pipsów: całość [-6.11; 37.38], OOS [-21.49; 46.53].

- **Spread**: ×1 14.41, ×1,5 13.96, ×2 13.51 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Gdy długoterminowy trend jest wzrostowy (SMA200 rośnie), głębokie krótkoterminowe
wyprzedanie (RSI14 spada poniżej progu) jest chwilowe i cena wraca w górę."""

PARAMS = {
    "rsi_level": [30, 35, 40],   # „RSI spadło poniżej X" — każdy próg to osobny wariant wejścia
    "slope_bars": [5, 20],       # „SMA200 rosnąca" = SMA200 dziś > SMA200 sprzed N świec
}

def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    rising = sma200 > sma200.shift(p["slope_bars"])        # interpretacja „rosnąca"
    crossed = ind.cross_below(rsi, p["rsi_level"])          # przecięcie w dół, nie sam stan „poniżej"
    return (rising & crossed).astype("int8")                # +1 = long, tylko longi

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
