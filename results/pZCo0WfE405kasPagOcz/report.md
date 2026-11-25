# Raport strategii: Alma v.1

Run `20261125-175214` · silnik 0.14.0 · kod `2c5c9615bcc13551` · dane `ce28743967d8ba47`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -40.60 |
| percentyl benchmarku ≥ 95 | ✘ | 43.30 |
| PBO < 0,3 | ✘ | 0.69 |
| DSR ≥ 0,95 | ✘ | 0.09 |
| dodatni przy spreadzie ×1,5 | ✘ | -2.48 |

## Hipoteza

Dlaczego ta strategia ma działać — 1–3 zdania, spisane PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-25; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-20, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS. OOS tego okresu widziało już 3 wersji kodu strategii i 10 kandydatów eksploracji; ta strategia: 1 wersji.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 466** (2 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 8 (limit otwartych pozycji w parze), 0.2 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 311 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.3 (przerwa w dostępie do danych), 2.3 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 120 świecach | rsi_level=25 | 56 | 0.97 | 12.98 | 57.1 | 21 | -2.60 | -40.60 |
| 2 | po 12 świecach | rsi_level=25 | 60 | 0.26 | 3.65 | 50.0 | 24 | 0.01 | 3.19 |
| 3 | po 16 świecach | rsi_level=25 | 60 | 0.24 | 1.82 | 55.0 | 24 | 0.02 | 0.88 |
| 4 | po 4 świecach | rsi_level=25 | 63 | 0.24 | 2.60 | 54.0 | 26 | -0.45 | -8.60 |
| 5 | po 96 świecach | rsi_level=25 | 56 | 0.19 | -0.15 | 55.4 | 22 | -1.24 | -26.61 |
| 6 | ATR5 TP 3× SL 2× max 120 | rsi_level=25 | 61 | 0.14 | 2.64 | 47.5 | 26 | 0.08 | -4.08 |
| 7 | ATR5 TP 3× SL 2× max 72 | rsi_level=25 | 61 | 0.14 | 3.63 | 47.5 | 26 | 0.04 | -6.32 |
| 8 | RSI do 50, SL 3×ATR14, max 120 | rsi_level=25 | 59 | 0.13 | 4.19 | 64.4 | 25 | 0.04 | -2.51 |
| 9 | ATR14 TP 4× SL 2× max 120 | rsi_level=25 | 63 | 0.13 | 3.76 | 39.7 | 26 | -0.04 | -4.53 |
| 10 | ATR5 TP 4× SL 2× max 120 | rsi_level=25 | 61 | 0.12 | 4.60 | 39.3 | 25 | -0.04 | -6.84 |

## Najlepszy wariant IS: po 120 świecach (rsi_level=25)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 9 | 4.1 | 37.3 | 44.4 |
| EURGBP | 6 | -5.8 | -34.8 | 66.7 |
| EURJPY | 13 | 21.8 | 283.4 | 69.2 |
| EURUSD | 4 | 4.2 | 16.7 | 50.0 |
| GBPUSD | 14 | -20.5 | -287.5 | 35.7 |
| USDCAD | 6 | 17.6 | 105.5 | 50.0 |
| USDCHF | 12 | 18.0 | 215.7 | 50.0 |
| USDJPY | 13 | -35.5 | -461.9 | 61.5 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 1 | -124.7 | -124.7 | 0.0 |
| 2025 | 43 | 25.0 | 1 075.4 | 60.5 |
| 2026 | 33 | -32.6 | -1 076.3 | 45.5 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 56 | 13.0 | 727.1 | 57.1 |
| OOS | 21 | -40.6 | -852.7 | 42.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 9 955 | -0.4 | -0.2 | -12.4 | -15.4 | 0.02 | 0 |
| 10.0% | 9 681 | -3.2 | -1.7 | -23.6 | -30.1 | 0.01 | 0 |
| 15.0% | 9 194 | -8.1 | -4.3 | -33.9 | -44.0 | 0.00 | 0 |
| 20.0% | 8 523 | -14.8 | -8.0 | -43.3 | -57.1 | -0.01 | 0 |
| 30.0% | 7 612 | -23.9 | -13.3 | -58.1 | -65.6 | 0.05 | 5 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-13): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **77**, otwarte: **0** (razem 77).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 77 | 7 | 7 | 7 | 7 | 8 | -1.6 | -126 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 77 | 7 | 7 | 7 | 7 | 8 | -1.6 | -126 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| GBPUSD | long | 2024-12-13 | 2024-12-20 | 7 | 120 | zamknięta | czas | -124.7 |
| USDCAD | long | 2025-01-06 | 2025-01-13 | 7 | 120 | zamknięta | czas | 107.8 |
| USDCHF | long | 2025-01-06 | 2025-01-13 | 7 | 120 | zamknięta | czas | 146.9 |
| USDCAD | long | 2025-01-20 | 2025-01-27 | 7 | 120 | zamknięta | czas | 64.8 |
| EURJPY | long | 2025-01-30 | 2025-02-06 | 7 | 120 | zamknięta | czas | -283.2 |
| AUDUSD | long | 2025-02-12 | 2025-02-19 | 7 | 120 | zamknięta | czas | 105.2 |
| EURJPY | long | 2025-02-20 | 2025-02-27 | 7 | 120 | zamknięta | czas | 42.6 |
| EURJPY | long | 2025-03-20 | 2025-03-27 | 7 | 120 | zamknięta | czas | 207.7 |
| EURGBP | long | 2025-04-15 | 2025-04-22 | 7 | 120 | zamknięta | czas | 21.0 |
| GBPUSD | long | 2025-04-30 | 2025-05-07 | 7 | 120 | zamknięta | czas | 23.4 |
| EURJPY | long | 2025-05-06 | 2025-05-13 | 7 | 120 | zamknięta | czas | 226.4 |
| USDJPY | long | 2025-05-14 | 2025-05-21 | 7 | 120 | zamknięta | czas | -260.0 |
| USDCHF | long | 2025-05-14 | 2025-05-21 | 7 | 120 | zamknięta | czas | -85.7 |
| EURGBP | long | 2025-06-24 | 2025-07-01 | 7 | 120 | zamknięta | czas | 49.0 |
| USDJPY | long | 2025-06-26 | 2025-07-03 | 7 | 120 | zamknięta | czas | -22.5 |
| USDCAD | long | 2025-06-26 | 2025-07-03 | 7 | 120 | zamknięta | czas | -60.7 |
| GBPUSD | long | 2025-07-02 | 2025-07-09 | 7 | 120 | zamknięta | czas | -16.7 |
| AUDUSD | long | 2025-07-07 | 2025-07-14 | 7 | 120 | zamknięta | czas | 56.0 |
| GBPUSD | long | 2025-07-25 | 2025-08-01 | 7 | 120 | zamknięta | czas | -181.6 |
| EURUSD | long | 2025-07-28 | 2025-08-04 | 7 | 120 | zamknięta | czas | -111.7 |
| AUDUSD | long | 2025-07-28 | 2025-08-04 | 7 | 120 | zamknięta | czas | -45.0 |
| EURGBP | long | 2025-07-28 | 2025-08-04 | 7 | 120 | zamknięta | czas | 23.1 |
| USDJPY | long | 2025-08-01 | 2025-08-08 | 7 | 120 | zamknięta | czas | -83.5 |
| EURGBP | long | 2025-08-12 | 2025-08-19 | 7 | 120 | zamknięta | czas | 19.3 |
| EURJPY | long | 2025-08-14 | 2025-08-21 | 7 | 120 | zamknięta | czas | 26.9 |
| AUDUSD | long | 2025-08-14 | 2025-08-21 | 7 | 120 | zamknięta | czas | -74.2 |
| AUDUSD | long | 2025-09-02 | 2025-09-09 | 7 | 120 | zamknięta | czas | 112.9 |
| GBPUSD | long | 2025-09-02 | 2025-09-09 | 7 | 120 | zamknięta | czas | 180.8 |
| EURUSD | long | 2025-09-02 | 2025-09-09 | 7 | 120 | zamknięta | czas | 105.7 |
| USDJPY | long | 2025-09-05 | 2025-09-12 | 7 | 120 | zamknięta | czas | 35.5 |
| EURJPY | long | 2025-09-09 | 2025-09-16 | 7 | 120 | zamknięta | czas | 120.5 |
| AUDUSD | long | 2025-09-18 | 2025-09-25 | 7 | 120 | zamknięta | czas | -23.1 |
| EURUSD | long | 2025-09-24 | 2025-10-01 | 7 | 120 | zamknięta | czas | -18.8 |
| USDJPY | long | 2025-09-29 | 2025-10-06 | 7 | 120 | zamknięta | czas | 178.5 |
| EURJPY | long | 2025-09-29 | 2025-10-06 | 7 | 120 | zamknięta | czas | 113.5 |
| EURGBP | long | 2025-10-01 | 2025-10-08 | 7 | 120 | zamknięta | czas | -37.2 |
| GBPUSD | long | 2025-10-22 | 2025-10-29 | 7 | 120 | zamknięta | czas | -108.0 |
| AUDUSD | long | 2025-11-04 | 2025-11-11 | 7 | 120 | zamknięta | czas | 31.0 |
| EURJPY | long | 2025-11-04 | 2025-11-11 | 7 | 120 | zamknięta | czas | 195.8 |
| USDCAD | long | 2025-11-07 | 2025-11-14 | 7 | 120 | zamknięta | czas | -42.0 |
| USDCHF | long | 2025-11-11 | 2025-11-18 | 7 | 120 | zamknięta | czas | -10.4 |
| USDCHF | long | 2025-12-01 | 2025-12-08 | 7 | 120 | zamknięta | czas | 60.2 |
| GBPUSD | long | 2025-12-17 | 2025-12-24 | 7 | 120 | zamknięta | czas | 198.0 |
| USDJPY | long | 2025-12-23 | 2025-12-31 | 8 | 120 | zamknięta | czas | 87.4 |
| GBPUSD | long | 2025-12-31 | 2026-01-08 | 8 | 120 | zamknięta | czas | 14.4 |
| USDCHF | long | 2026-02-09 | 2026-02-16 | 7 | 120 | zamknięta | czas | -29.0 |
| USDCAD | long | 2026-02-09 | 2026-02-16 | 7 | 120 | zamknięta | czas | 45.9 |
| USDJPY | long | 2026-02-09 | 2026-02-16 | 7 | 120 | zamknięta | czas | -213.8 |
| EURJPY | long | 2026-02-10 | 2026-02-17 | 7 | 120 | zamknięta | czas | -229.6 |
| USDCHF | long | 2026-02-27 | 2026-03-06 | 7 | 120 | zamknięta | czas | 87.7 |
| EURJPY | long | 2026-03-03 | 2026-03-10 | 7 | 120 | zamknięta | czas | 64.9 |
| USDJPY | long | 2026-03-19 | 2026-03-26 | 7 | 120 | zamknięta | czas | 142.3 |
| EURJPY | long | 2026-03-30 | 2026-04-06 | 7 | 120 | zamknięta | czas | 77.3 |
| USDCHF | long | 2026-04-01 | 2026-04-08 | 7 | 120 | zamknięta | czas | -26.8 |
| GBPUSD | long | 2026-05-12 | 2026-05-19 | 7 | 120 | zamknięta | czas | -111.2 |
| AUDUSD | long | 2026-05-15 | 2026-05-22 | 7 | 120 | zamknięta | czas | -45.8 |
| USDCHF | long | 2026-05-25 | 2026-06-01 | 7 | 120 | zamknięta | czas | -0.7 |
| USDJPY | long | 2026-07-02 | 2026-07-09 | 7 | 120 | zamknięta | czas | 56.3 |
| USDCHF | long | 2026-07-02 | 2026-07-09 | 7 | 120 | zamknięta | czas | 32.0 |
| GBPUSD | long | 2026-07-21 | 2026-07-28 | 7 | 120 | zamknięta | czas | -77.2 |
| EURJPY | long | 2026-07-30 | 2026-08-06 | 7 | 120 | zamknięta | czas | -156.0 |
| USDCHF | long | 2026-07-30 | 2026-08-06 | 7 | 120 | zamknięta | czas | 63.3 |
| USDCHF | long | 2026-08-17 | 2026-08-24 | 7 | 120 | zamknięta | czas | -61.2 |
| USDJPY | long | 2026-08-19 | 2026-08-26 | 7 | 120 | zamknięta | czas | 80.2 |
| GBPUSD | long | 2026-08-27 | 2026-09-03 | 7 | 120 | zamknięta | czas | -81.6 |
| USDJPY | long | 2026-09-02 | 2026-09-09 | 7 | 120 | zamknięta | czas | -504.1 |
| USDCAD | long | 2026-09-03 | 2026-09-10 | 7 | 120 | zamknięta | czas | -10.3 |
| USDCHF | long | 2026-09-03 | 2026-09-10 | 7 | 120 | zamknięta | czas | 39.4 |
| AUDUSD | long | 2026-09-10 | 2026-09-17 | 7 | 120 | zamknięta | czas | -79.5 |
| USDJPY | long | 2026-09-25 | 2026-10-02 | 7 | 120 | zamknięta | czas | 13.5 |
| EURJPY | long | 2026-09-25 | 2026-10-02 | 7 | 120 | zamknięta | czas | -123.4 |
| EURGBP | long | 2026-09-28 | 2026-10-05 | 7 | 120 | zamknięta | czas | -110.0 |
| GBPUSD | long | 2026-10-07 | 2026-10-14 | 7 | 120 | zamknięta | czas | -47.7 |
| USDJPY | long | 2026-10-13 | 2026-10-20 | 7 | 120 | zamknięta | czas | 28.3 |
| EURUSD | long | 2026-10-27 | 2026-11-03 | 7 | 120 | zamknięta | czas | 41.5 |
| GBPUSD | long | 2026-10-28 | 2026-11-04 | 7 | 120 | zamknięta | czas | 210.6 |
| GBPUSD | long | 2026-11-06 | 2026-11-13 | 7 | 120 | zamknięta | czas | -166.0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.63 pips/transakcję, percentyl **43.3** (losowe: 5%=-22.31, mediana=0.53, 95%=24.51).

- **Deflated Sharpe Ratio**: 0.093 (Sharpe na transakcję 0.153, próg przy 466 próbach 0.333).

- **PBO** (CSCV, 16 bloków, 466 wariantów): 0.692 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 66 transakcji, śr. -19.60 pips, -1.63 R.

- **Bootstrap 95%** średnich pipsów: całość [-30.82; 25.62], OOS [-106.95; 13.40].

- **Spread**: ×1 -1.63, ×1,5 -2.48, ×2 -3.32 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 7.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -5.14, 1 pips: -8.66 pips/transakcję.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Dlaczego ta strategia ma działać — 1–3 zdania, spisane PRZED liczeniem."""

PARAMS = {
    "rsi_level": [25, 30],    # każda wartość = osobny wariant wejścia
}

# TIMEFRAME = "D1"     # świece dzienne (cała historia Yahoo) zamiast H1 — D-058; tło D1 w strategii H1: ind.d1(df), ind.d1_to_h1(df, x)

def signals(df, p, ind):
    # df: świece H1 jednej pary (open, high, low, close), indeks = czas otwarcia UTC
    # zwróć +1 (long) / -1 (short) / 0 na świecy, której ZAMKNIĘCIE daje sygnał
    rsi = ind.rsi(df.close, 14)
    trend = ind.rising(ind.sma(df.close, 200), 5)
    return (trend & ind.cross_below(rsi, p["rsi_level"])).astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
