# Raport strategii: Strategia 5

Run `20261027-184719` · silnik 0.7.0 · kod `9322b9d60f8d5553` · dane `f8d8bc72a0207c72`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 0.70 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✔ | 0.07 |
| DSR ≥ 0,95 | ✘ | 0.60 |
| dodatni przy spreadzie ×1,5 | ✔ | 1.22 |

## Hipoteza

Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na Dukascopy 2003–2026 — innym źródle i dłuższym okresie.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 282/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 3 przerw w dostępie do danych (93 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 18** (3 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 3 wejść w rozgrzewce ATR, 10 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 0.8 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 6 świecach | start=7 | 4 585 | 0.11 | 2.00 | 52.1 | 1 524 | 0.07 | 0.70 |
| 2 | po 8 świecach | start=8 | 4 577 | 0.08 | 1.71 | 51.5 | 1 520 | -0.04 | -0.53 |
| 3 | po 4 świecach | start=8 | 4 579 | 0.07 | 1.33 | 51.6 | 1 520 | -0.08 | -0.92 |
| 4 | po 6 świecach | start=6 | 4 586 | 0.06 | 1.17 | 51.2 | 1 524 | -0.04 | -0.58 |
| 5 | po 6 świecach | start=8 | 4 579 | 0.06 | 1.28 | 51.3 | 1 520 | -0.04 | -0.52 |
| 6 | po 8 świecach | start=7 | 4 585 | 0.06 | 1.14 | 51.2 | 1 524 | -0.06 | -0.75 |
| 7 | po 8 świecach | start=6 | 4 586 | 0.06 | 1.11 | 50.9 | 1 524 | -0.00 | -0.19 |
| 8 | ATR14 TP 50× SL 2× max 8 | start=8 | 4 579 | 0.05 | 2.08 | 44.0 | 1 520 | -0.02 | -0.58 |
| 9 | ATR14 TP 50× SL 2× max 6 | start=8 | 4 579 | 0.04 | 1.68 | 47.4 | 1 520 | -0.01 | -0.30 |
| 10 | ATR14 TP 50× SL 2× max 6 | start=7 | 4 585 | 0.04 | 1.43 | 48.7 | 1 524 | 0.01 | 0.03 |

## Najlepszy wariant IS: po 6 świecach (start=7)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 6109 | 1.7 | 10 220.5 | 51.9 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 172 | 2.5 | 436.8 | 51.2 |
| 2004 | 261 | -0.2 | -56.5 | 52.9 |
| 2005 | 260 | 1.6 | 404.5 | 51.9 |
| 2006 | 260 | 2.4 | 617.3 | 55.8 |
| 2007 | 261 | 2.8 | 723.9 | 52.5 |
| 2008 | 262 | 2.9 | 751.4 | 50.0 |
| 2009 | 261 | -0.0 | -4.7 | 49.8 |
| 2010 | 261 | 2.2 | 574.8 | 53.3 |
| 2011 | 260 | -0.5 | -136.6 | 49.2 |
| 2012 | 261 | 3.0 | 771.3 | 51.7 |
| 2013 | 260 | 1.3 | 339.5 | 50.0 |
| 2014 | 260 | 2.9 | 749.4 | 50.0 |
| 2015 | 260 | 4.7 | 1 232.9 | 53.1 |
| 2016 | 260 | 2.9 | 754.0 | 51.9 |
| 2017 | 260 | 2.9 | 753.2 | 55.0 |
| 2018 | 260 | 2.6 | 669.5 | 54.2 |
| 2019 | 259 | 1.6 | 411.5 | 53.3 |
| 2020 | 261 | 0.6 | 149.3 | 52.1 |
| 2021 | 257 | 1.3 | 337.2 | 49.8 |
| 2022 | 260 | 1.2 | 315.0 | 50.4 |
| 2023 | 260 | 0.9 | 243.2 | 53.1 |
| 2024 | 261 | 1.0 | 270.4 | 49.0 |
| 2025 | 260 | -0.4 | -100.6 | 53.8 |
| 2026 | 212 | 0.1 | 13.6 | 52.4 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 4585 | 2.0 | 9 157.3 | 52.1 |
| OOS | 1524 | 0.7 | 1 063.2 | 51.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 32 184 | 221.8 | 5.1 | -12.4 | 0.59 | 0 |
| 10.0% | 90 977 | 809.8 | 9.9 | -23.9 | 0.59 | 0 |
| 15.0% | 225 950 | 2 159.5 | 14.2 | -34.3 | 0.59 | 0 |
| 20.0% | 493 170 | 4 831.7 | 18.1 | -44.6 | 0.59 | 0 |
| 30.0% | 1 595 454 | 15 854.5 | 24.1 | -64.8 | 0.59 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 1.67 pips/transakcję, percentyl **100.0** (losowe: 5%=-1.15, mediana=-0.22, 95%=0.66).

- **Deflated Sharpe Ratio**: 0.597 (Sharpe na transakcję 0.051, próg przy 18 próbach 0.047).

- **PBO** (CSCV, 16 bloków, 18 wariantów): 0.069 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 3657 transakcji, śr. 1.19 pips, 0.09 R.

- **Bootstrap 95%** średnich pipsów: całość [0.68; 2.61], OOS [-0.66; 2.07].

- **Spread**: ×1 1.67, ×1,5 1.22, ×2 0.77, faktyczny 1.92 pips/transakcję.

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
