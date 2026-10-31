# Raport strategii: Strategia 5

Run `20261031-101603` · silnik 0.7.0 · kod `9322b9d60f8d5553` · dane `51eede8f48c7f380`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -0.81 |
| percentyl benchmarku ≥ 95 | ✔ | 97.30 |
| PBO < 0,3 | ✔ | 0.11 |
| DSR ≥ 0,95 | ✘ | 0.05 |
| dodatni przy spreadzie ×1,5 | ✘ | -0.22 |

## Hipoteza

Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na Dukascopy 2003–2026 — innym źródle i dłuższym okresie.

## Dane i model wykonania

- Pary: EURUSD, USDJPY; świece H1 od 2003-05-04 do 2026-09-30; źródło: dukascopy.

- In-sample do 2020-11-23, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 281/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 3 przerw w dostępie do danych (93 h); USDJPY: 141/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 16 przerw w dostępie do danych (40147 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 18** (3 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 6 wejść w rozgrzewce ATR, 13 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 1.6 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 50× SL 2× max 8 | start=8 | 7 447 | 0.01 | 0.57 | 43.9 | 1 688 | -0.04 | -0.81 |
| 2 | ATR14 TP 50× SL 2× max 6 | start=8 | 7 448 | 0.01 | 0.23 | 46.4 | 1 688 | -0.03 | -0.62 |
| 3 | ATR14 TP 50× SL 2× max 8 | start=7 | 7 456 | 0.00 | 0.04 | 44.7 | 1 693 | -0.03 | -0.59 |
| 4 | po 6 świecach | start=7 | 7 456 | -0.00 | 0.01 | 49.2 | 1 693 | 0.01 | 0.16 |
| 5 | ATR14 TP 50× SL 2× max 6 | start=7 | 7 456 | -0.00 | -0.10 | 46.9 | 1 693 | -0.02 | -0.49 |
| 6 | po 8 świecach | start=8 | 7 444 | -0.00 | 0.17 | 50.0 | 1 688 | -0.07 | -0.76 |
| 7 | ATR14 TP 50× SL 2× max 4 | start=8 | 7 448 | -0.01 | -0.10 | 48.2 | 1 688 | -0.06 | -1.23 |
| 8 | ATR14 TP 50× SL 2× max 8 | start=6 | 7 458 | -0.01 | -0.47 | 44.8 | 1 693 | -0.01 | -0.49 |
| 9 | ATR14 TP 50× SL 2× max 6 | start=6 | 7 458 | -0.01 | -0.45 | 46.6 | 1 693 | -0.04 | -1.08 |
| 10 | po 6 świecach | start=6 | 7 458 | -0.02 | -0.17 | 48.6 | 1 693 | -0.08 | -0.95 |

## Najlepszy wariant IS: ATR14 TP 50× SL 2× max 8 (start=8)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 6081 | 1.4 | 8 495.7 | 43.3 |
| USDJPY | 3054 | -1.8 | -5 616.4 | 43.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 342 | -0.8 | -289.4 | 48.2 |
| 2004 | 522 | 1.1 | 590.8 | 46.7 |
| 2005 | 499 | 2.5 | 1 245.7 | 46.1 |
| 2006 | 497 | -2.4 | -1 171.0 | 40.6 |
| 2007 | 522 | -1.9 | -1 000.5 | 41.4 |
| 2008 | 524 | 0.8 | 407.3 | 43.3 |
| 2009 | 522 | -1.4 | -726.4 | 44.3 |
| 2010 | 522 | 4.9 | 2 540.5 | 48.7 |
| 2011 | 345 | 2.4 | 844.2 | 45.8 |
| 2012 | 282 | 1.0 | 286.9 | 41.8 |
| 2013 | 326 | -0.3 | -112.9 | 41.1 |
| 2014 | 408 | 1.4 | 551.5 | 41.4 |
| 2015 | 475 | 1.7 | 809.5 | 45.1 |
| 2016 | 476 | -0.5 | -251.0 | 42.4 |
| 2017 | 412 | -0.3 | -132.4 | 44.2 |
| 2018 | 282 | 1.8 | 518.6 | 45.0 |
| 2019 | 258 | -0.1 | -28.4 | 41.1 |
| 2020 | 282 | -0.1 | -33.3 | 39.0 |
| 2021 | 407 | -1.1 | -432.7 | 40.0 |
| 2022 | 260 | -1.1 | -293.3 | 41.5 |
| 2023 | 259 | 1.8 | 463.9 | 41.7 |
| 2024 | 260 | -0.2 | -53.2 | 36.9 |
| 2025 | 259 | -2.7 | -702.9 | 41.3 |
| 2026 | 194 | -0.8 | -152.2 | 44.8 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 7447 | 0.6 | 4 249.1 | 43.9 |
| OOS | 1688 | -0.8 | -1 369.8 | 40.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 9 878 | -1.2 | -0.1 | -40.8 | 0.04 | 0 |
| 10.0% | 7 703 | -23.0 | -1.1 | -67.6 | 0.04 | 0 |
| 15.0% | 4 752 | -52.5 | -3.1 | -83.7 | 0.04 | 0 |
| 20.0% | 2 323 | -76.8 | -6.0 | -92.4 | 0.04 | 0 |
| 30.0% | 278 | -97.2 | -14.2 | -98.7 | 0.04 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 0.32 pips/transakcję, percentyl **97.3** (losowe: 5%=-1.23, mediana=-0.55, 95%=0.16).

- **Deflated Sharpe Ratio**: 0.050 (Sharpe na transakcję 0.009, próg przy 18 próbach 0.028).

- **PBO** (CSCV, 16 bloków, 18 wariantów): 0.106 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 4655 transakcji, śr. -0.07 pips, -0.01 R.

- **Bootstrap 95%** średnich pipsów: całość [-0.55; 1.20], OOS [-2.24; 0.69].

- **Spread**: ×1 0.32, ×1,5 -0.22, ×2 -0.75, faktyczny 1.81 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na Dukascopy 2003–2026 — innym źródle i dłuższym okresie."""

PARAMS = {
    "start": [6, 7, 8],      # godzina wejścia w czasie Londynu (z czasem letnim); 7:00 = otwarcie Londynu
}

# Wyjście po 4, 6 albo 8 godzinach; każde także z awaryjnym stopem 2×ATR14 (TP tak daleko, że w praktyce go nie ma)
EXITS = (
    [{"kind": "time", "n": n, "cap": n} for n in (4, 6, 8)]
    + [{"kind": "atr", "n": 14, "tp": 50.0, "sl": 2.0, "cap": n} for n in (4, 6, 8)]
)


def signals(df, p, ind):
    london = df.index.tz_convert("Europe/London")
    weekday = london.dayofweek < 5
    # sygnał na zamknięciu świecy start−1 → wejście na open świecy o godzinie start (czas Londynu)
    sig = weekday & (london.hour == p["start"] - 1)
    return -sig.astype("int8")              # short EUR/USD

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
