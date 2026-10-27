# Raport strategii: RSI 70/30 w silnym trendzie

Run `20261027-172058` · silnik 0.4.0 · kod `fbf7758d38a524b0` · dane `366110eecfd32a09`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -1.32 |
| percentyl benchmarku ≥ 95 | ✘ | 65.50 |
| PBO < 0,3 | ✘ | 0.61 |
| DSR ≥ 0,95 | ✘ | 0.01 |
| dodatni przy spreadzie ×1,5 | ✔ | 0.51 |

## Hipoteza

W silnym trendzie H1 krótkie, gwałtowne ruchy przeciw trendowi (RSI14 przebija 70 przy trendzie
spadkowym albo 30 przy wzrostowym) to chwilowa przesada: płynność wraca do kierunku głównego trendu
i cena cofa się w jego stronę w ciągu kilku-kilkunastu godzin.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); zamknięcie najpóźniej o 23:00 czasu polskiego (powód `23:00`). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 275/282 mies. zatwierdzonych, 8 świec uzupełnionych (luki ≤ 3 h), 8 długich luk (3629 h). Transakcja nachodząca na długą lukę albo na świecę uzupełnioną jest anulowana.

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 699** (3 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 27 (otwarta pozycja w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 1098 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), 0.0 transakcji anulowanych przez lukę w danych lub świecę uzupełnioną (D-031).

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 12 świecach | slope_atr=1.0 | 117 | 0.12 | 1.62 | 51.3 | 34 | -0.11 | -1.32 |
| 2 | ATR5 TP 0.75× SL 0.5× max 24 | slope_atr=1.0 | 134 | 0.11 | 1.43 | 48.5 | 40 | -0.03 | 0.72 |
| 3 | ATR5 TP 0.75× SL 0.5× max 72 | slope_atr=1.0 | 134 | 0.11 | 1.43 | 48.5 | 40 | -0.03 | 0.72 |
| 4 | ATR5 TP 0.75× SL 0.5× max 120 | slope_atr=1.0 | 134 | 0.11 | 1.43 | 48.5 | 40 | -0.03 | 0.72 |
| 5 | ATR14 TP 0.75× SL 0.5× max 24 | slope_atr=1.0 | 134 | 0.10 | 1.39 | 48.5 | 40 | 0.02 | 0.61 |
| 6 | ATR14 TP 0.75× SL 0.5× max 72 | slope_atr=1.0 | 134 | 0.10 | 1.39 | 48.5 | 40 | 0.02 | 0.61 |
| 7 | ATR14 TP 0.75× SL 0.5× max 120 | slope_atr=1.0 | 134 | 0.10 | 1.39 | 48.5 | 40 | 0.02 | 0.61 |
| 8 | cena przez SMA20, SL 1×ATR14, max 120 | slope_atr=1.0 | 134 | 0.10 | 2.19 | 56.0 | 40 | 0.07 | 1.45 |
| 9 | ATR5 TP 0.75× SL 1× max 24 | slope_atr=1.0 | 130 | 0.09 | 2.04 | 65.4 | 38 | -0.16 | -0.88 |
| 10 | ATR5 TP 0.75× SL 1× max 72 | slope_atr=1.0 | 130 | 0.09 | 2.04 | 65.4 | 38 | -0.16 | -0.88 |

## Najlepszy wariant IS: po 12 świecach (slope_atr=1.0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 151 | 1.0 | 144.4 | 50.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 5 | -16.1 | -80.5 | 20.0 |
| 2004 | 4 | -48.7 | -194.6 | 0.0 |
| 2005 | 7 | 8.3 | 57.8 | 42.9 |
| 2006 | 10 | 7.6 | 75.6 | 70.0 |
| 2007 | 6 | -4.0 | -24.3 | 50.0 |
| 2008 | 4 | -96.4 | -385.7 | 0.0 |
| 2009 | 5 | -9.0 | -44.9 | 60.0 |
| 2010 | 5 | 28.6 | 143.1 | 80.0 |
| 2011 | 8 | 0.6 | 5.1 | 62.5 |
| 2012 | 7 | 1.5 | 10.1 | 57.1 |
| 2013 | 4 | 59.8 | 239.1 | 75.0 |
| 2014 | 4 | 10.1 | 40.5 | 75.0 |
| 2015 | 11 | 48.4 | 532.1 | 90.9 |
| 2016 | 11 | -8.8 | -96.3 | 45.5 |
| 2017 | 2 | 1.8 | 3.7 | 50.0 |
| 2018 | 7 | -10.1 | -70.9 | 28.6 |
| 2019 | 11 | -9.2 | -100.8 | 27.3 |
| 2020 | 6 | 13.3 | 80.1 | 50.0 |
| 2021 | 8 | -9.1 | -72.6 | 37.5 |
| 2022 | 3 | 7.1 | 21.3 | 66.7 |
| 2023 | 4 | 11.5 | 45.8 | 75.0 |
| 2024 | 9 | 7.9 | 70.7 | 55.6 |
| 2025 | 8 | -10.9 | -87.5 | 25.0 |
| 2026 | 2 | -11.3 | -22.6 | 50.0 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 117 | 1.6 | 189.2 | 51.3 |
| OOS | 34 | -1.3 | -44.8 | 47.1 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 233 | 2.3 | 0.1 | -8.3 | 0.06 | 0 |
| 10.0% | 10 406 | 4.1 | 0.2 | -16.0 | 0.06 | 0 |
| 15.0% | 10 516 | 5.2 | 0.2 | -23.2 | 0.06 | 0 |
| 20.0% | 10 562 | 5.6 | 0.2 | -29.9 | 0.06 | 0 |
| 30.0% | 10 458 | 4.6 | 0.2 | -42.0 | 0.06 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 0.96 pips/transakcję, percentyl **65.5** (losowe: 5%=-7.90, mediana=-0.91, 95%=6.43).

- **Deflated Sharpe Ratio**: 0.014 (Sharpe na transakcję 0.040, próg przy 699 próbach 0.241).

- **PBO** (CSCV, 16 bloków, 699 wariantów): 0.612 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 104 transakcji, śr. -0.20 pips, -0.11 R.

- **Bootstrap 95%** średnich pipsów: całość [-7.77; 9.74], OOS [-10.95; 7.88].

- **Spread**: ×1 0.96, ×1,5 0.51, ×2 0.06, faktyczny 1.25 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """W silnym trendzie H1 krótkie, gwałtowne ruchy przeciw trendowi (RSI14 przebija 70 przy trendzie
spadkowym albo 30 przy wzrostowym) to chwilowa przesada: płynność wraca do kierunku głównego trendu
i cena cofa się w jego stronę w ciągu kilku-kilkunastu godzin."""

# slope_atr: jak bardzo musi się zmienić SMA200 w ciągu 20 godzin (w jednostkach ATR14), żeby trend był „wyraźny”
PARAMS = {"slope_atr": [0.25, 0.5, 1.0]}


def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    atr = ind.atr(df, 14)
    slope = (sma200 - sma200.shift(20)) / atr          # nachylenie trendu w ATR na 20 świec
    trend_up = slope > p["slope_atr"]                   # wyraźnie rośnie
    trend_down = slope < -p["slope_atr"]                # wyraźnie spada; pomiędzy = płasko, nic nie robimy
    rsi = ind.rsi(df.close, 14)
    long_ = trend_up & ind.cross_below(rsi, 30)         # przesada w dół w trendzie wzrostowym → kupno
    short = trend_down & ind.cross_above(rsi, 70)       # przesada w górę w trendzie spadkowym → sprzedaż
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
