# Raport strategii: Strategia 1 - dokładanie

Run `20261027-175920` · silnik 0.6.0 · kod `c6e6048042a2deef` · dane `5d2ac9e95dedc57f`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -6.19 |
| percentyl benchmarku ≥ 95 | ✘ | 91.90 |
| PBO < 0,3 | ✘ | — |
| DSR ≥ 0,95 | ✘ | — |
| dodatni przy spreadzie ×1,5 | ✔ | 2.61 |

## Hipoteza

W wyraźnym trendzie H1 (EMA200 zmienia się o więcej niż 0,25 ATR14 na 10 świec) gwałtowny ruch
przeciw trendowi, w którym RSI14 przebija 70 (trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada:
płynność wraca do kierunku trendu i cena cofa się o ok. 1,5 ATR. Im głębsza przesada, tym większa oczekiwana
korekta — stąd dokładanie z rosnącą wagą. Gdy przesada trwa 6 godzin, to już nie przesada, tylko zmiana trendu.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Dokładanie (D-034): do 5 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 276/282 mies. zatwierdzonych, 8 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 6 przerw w dostępie do danych (3147 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 5 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | — | 407 | 0.29 | 6.72 | 69.8 | 161 | -0.49 | -6.19 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 568 | 3.1 | 1 738.1 | 65.8 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 26 | 20.4 | 530.8 | 80.8 |
| 2004 | 14 | 11.3 | 158.6 | 64.3 |
| 2005 | 22 | 1.8 | 40.6 | 72.7 |
| 2006 | 20 | 15.2 | 304.0 | 90.0 |
| 2007 | 19 | 2.5 | 47.0 | 63.2 |
| 2008 | 26 | 12.8 | 332.4 | 46.2 |
| 2009 | 24 | 9.7 | 233.0 | 66.7 |
| 2010 | 22 | 12.9 | 283.7 | 81.8 |
| 2011 | 25 | 7.2 | 179.7 | 72.0 |
| 2012 | 41 | 0.9 | 35.5 | 58.5 |
| 2013 | 20 | -18.7 | -374.8 | 70.0 |
| 2014 | 27 | 2.4 | 64.8 | 63.0 |
| 2015 | 21 | 37.9 | 795.9 | 100.0 |
| 2016 | 25 | -4.8 | -119.2 | 52.0 |
| 2017 | 13 | 13.9 | 180.1 | 92.3 |
| 2018 | 19 | 3.7 | 69.4 | 78.9 |
| 2019 | 28 | -8.2 | -229.0 | 60.7 |
| 2020 | 17 | 14.8 | 250.8 | 76.5 |
| 2021 | 25 | -8.3 | -206.6 | 32.0 |
| 2022 | 29 | -20.3 | -589.6 | 48.3 |
| 2023 | 32 | -9.7 | -311.3 | 53.1 |
| 2024 | 43 | -1.9 | -81.3 | 58.1 |
| 2025 | 23 | 2.8 | 64.4 | 78.3 |
| 2026 | 7 | 11.3 | 79.3 | 85.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 407 | 6.7 | 2 735.3 | 69.8 |
| OOS | 161 | -6.2 | -997.2 | 55.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 13 630 | 36.3 | 1.4 | -25.5 | 0.20 | 0 |
| 10.0% | 15 408 | 54.1 | 1.9 | -45.3 | 0.17 | 11 |
| 15.0% | 15 675 | 56.7 | 2.0 | -60.7 | 0.16 | 61 |
| 20.0% | 18 185 | 81.8 | 2.6 | -67.5 | 0.19 | 112 |
| 30.0% | 10 366 | 3.7 | 0.2 | -82.3 | 0.12 | 196 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 3.06 pips/transakcję, percentyl **91.9** (losowe: 5%=-5.88, mediana=-0.64, 95%=3.92).

- **Deflated Sharpe Ratio**: — (Sharpe na transakcję —, próg przy 1 próbach —).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 344 transakcji, śr. -0.79 pips, -0.13 R.

- **Bootstrap 95%** średnich pipsów: całość [-0.72; 6.93], OOS [-12.50; -0.14].

- **Spread**: ×1 3.06, ×1,5 2.61, ×2 2.16, faktyczny 3.31 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """W wyraźnym trendzie H1 (EMA200 zmienia się o więcej niż 0,25 ATR14 na 10 świec) gwałtowny ruch
przeciw trendowi, w którym RSI14 przebija 70 (trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada:
płynność wraca do kierunku trendu i cena cofa się o ok. 1,5 ATR. Im głębsza przesada, tym większa oczekiwana
korekta — stąd dokładanie z rosnącą wagą. Gdy przesada trwa 6 godzin, to już nie przesada, tylko zmiana trendu."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 (= 100 − 70)
RUN = 6             # tyle zamknięć z rzędu za poziomem = pomyłka → zamknięcie wszystkiego (wyjście rsi_streak)
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin (B11 wyłączone dla tej strategii)
EXITS = [
    # TP 1,5 × ATR14 od ceny wejścia (ATR ze świecy sygnału); seria 6 zamknięć RSI za 70/30 → wyjście na open
    # następnej świecy; limit 120 świec. Bez SL cenowego — rolę stopu pełni seria RSI.
    {"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120},
]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)       # nachylenie EMA200 na 10 świec, w ATR14
    up = (slope > 0.25).to_numpy()                          # wyraźnie rośnie
    down = (slope < -0.25).to_numpy()                       # wyraźnie spada
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record = 0, 0, 0, 0.0
    for t in range(1, len(r)):
        x, prev = r[t], r[t - 1]
        if np.isnan(x) or np.isnan(prev):
            side = 0
            continue
        if side != 0:
            beyond = x > LEVEL if side < 0 else x < 100 - LEVEL
            if beyond:                                      # przesada trwa: ta sama „seria”
                streak += 1
                deeper = x > record if side < 0 else x < record
                # dokładamy, gdy RSI pobije rekord z ostatniego wejścia; nie w 6. świecy serii (wtedy wszystko się zamyka)
                if deeper and count < MAX_POS and streak < RUN:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec wybicia
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record = -1, 1, 1, x
            out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record = 1, 1, 1, x
            out[t] = weight(100 - LEVEL - x)
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
