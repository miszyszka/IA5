# Raport strategii: 5 X EMA

Run `20261103-074924` · silnik 0.8.0 · kod `1ef709fd7cc133b6` · dane `0af6c4ca31a03f4d`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -1.71 |
| percentyl benchmarku ≥ 95 | ✘ | 40.20 |
| PBO < 0,3 | ✘ | 0.43 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -2.75 |

## Hipoteza

Gdy pięć średnich EMA układa się w trend (5 > 10 > 15 > 25 > 40) i cena jest po właściwej
stronie EMA200, impet trendu zwykle trwa. Wejście na pierwszej świecy spełnienia warunku pozwala
złapać początek ruchu, a nie jego środek. Wyjście przy zamknięciu za EMA40 wypuszcza zysk,
gdy struktura trendu się rozpada.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 233** (1 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 246 (limit otwartych pozycji w parze), 0.9 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 2394 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 5.7 (przerwa w dostępie do danych), 1.1 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | cena przez SMA20, SL 3×ATR14, max 120 | — | 1 632 | -0.04 | -1.99 | 28.8 | 504 | -0.03 | -1.71 |
| 2 | RSI do 50, SL 3×ATR14, max 120 | — | 1 710 | -0.04 | -1.58 | 42.3 | 524 | -0.07 | -2.62 |
| 3 | ATR5 TP 0.5× SL 3× max 24 | — | 1 601 | -0.05 | -1.52 | 84.1 | 493 | -0.07 | -2.03 |
| 4 | ATR5 TP 0.75× SL 3× max 120 | — | 1 512 | -0.05 | -1.06 | 79.8 | 468 | -0.05 | -1.32 |
| 5 | ATR14 TP 0.75× SL 3× max 72 | — | 1 532 | -0.05 | -1.31 | 79.8 | 472 | -0.05 | -1.61 |
| 6 | ATR14 TP 0.75× SL 3× max 120 | — | 1 532 | -0.05 | -1.32 | 79.8 | 472 | -0.05 | -1.67 |
| 7 | ATR5 TP 0.75× SL 3× max 72 | — | 1 515 | -0.05 | -1.09 | 79.7 | 472 | -0.05 | -1.33 |
| 8 | ATR5 TP 0.5× SL 3× max 72 | — | 1 583 | -0.05 | -1.63 | 85.4 | 487 | -0.07 | -2.30 |
| 9 | ATR5 TP 0.5× SL 3× max 120 | — | 1 582 | -0.05 | -1.68 | 85.4 | 484 | -0.07 | -2.35 |
| 10 | ATR14 TP 0.75× SL 3× max 24 | — | 1 552 | -0.05 | -1.34 | 77.8 | 477 | -0.06 | -1.70 |

## Najlepszy wariant IS: cena przez SMA20, SL 3×ATR14, max 120 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 256 | -2.7 | -695.7 | 27.7 |
| EURGBP | 307 | -1.6 | -505.9 | 28.3 |
| EURJPY | 266 | -9.8 | -2 597.9 | 25.6 |
| EURUSD | 272 | -0.2 | -41.6 | 29.8 |
| GBPUSD | 269 | 2.2 | 604.7 | 29.4 |
| USDCAD | 251 | -1.6 | -403.6 | 29.9 |
| USDCHF | 271 | -1.2 | -334.6 | 28.0 |
| USDJPY | 244 | -0.6 | -139.1 | 31.6 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 161 | -2.7 | -428.4 | 31.7 |
| 2025 | 1094 | -1.6 | -1 754.2 | 29.0 |
| 2026 | 881 | -2.2 | -1 931.3 | 27.9 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 1632 | -2.0 | -3 253.2 | 28.8 |
| OOS | 504 | -1.7 | -860.7 | 28.6 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 5 657 | -43.4 | -24.9 | -46.4 | -1.08 | 0 |
| 10.0% | 2 937 | -70.6 | -46.0 | -73.6 | -1.09 | 0 |
| 15.0% | 1 558 | -84.4 | -60.8 | -86.7 | -1.03 | 16 |
| 20.0% | 958 | -90.4 | -69.3 | -92.2 | -1.06 | 154 |
| 30.0% | 703 | -93.0 | -73.7 | -94.6 | -0.79 | 503 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.93 pips/transakcję, percentyl **40.2** (losowe: 5%=-2.80, mediana=-1.79, 95%=-0.71).

- **Deflated Sharpe Ratio**: 0.000 (Sharpe na transakcję -0.048, próg przy 233 próbach 0.210).

- **PBO** (CSCV, 16 bloków, 233 wariantów): 0.428 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 1247 transakcji, śr. -2.24 pips, -0.09 R.

- **Bootstrap 95%** średnich pipsów: całość [-3.53; -0.18], OOS [-4.88; 1.77].

- **Spread**: ×1 -1.93, ×1,5 -2.75, ×2 -3.58 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Gdy pięć średnich EMA układa się w trend (5 > 10 > 15 > 25 > 40) i cena jest po właściwej
stronie EMA200, impet trendu zwykle trwa. Wejście na pierwszej świecy spełnienia warunku pozwala
złapać początek ruchu, a nie jego środek. Wyjście przy zamknięciu za EMA40 wypuszcza zysk,
gdy struktura trendu się rozpada."""

# Brak PARAMS: strategia ma stałe parametry z opisu. Dopisanie PARAMS zwiększyłoby liczbę prób (W2).


def signals(df, p, ind):
    c = df["close"]
    e5 = ind.ema(c, 5)
    e10 = ind.ema(c, 10)
    e15 = ind.ema(c, 15)
    e25 = ind.ema(c, 25)
    e40 = ind.ema(c, 40)
    e200 = ind.ema(c, 200)

    ribbon_up = (e5 > e10) & (e10 > e15) & (e15 > e25) & (e25 > e40)
    ribbon_dn = (e5 < e10) & (e10 < e15) & (e15 < e25) & (e25 < e40)

    bull = ribbon_up & (c > e200)
    bear = ribbon_dn & (c < e200)

    # Zdarzenie: warunek spełniony teraz, a na poprzedniej świecy nie był spełniony
    bull_start = bull & ~bull.shift(1, fill_value=False)
    bear_start = bear & ~bear.shift(1, fill_value=False)

    return bull_start.astype("int8") - bear_start.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
