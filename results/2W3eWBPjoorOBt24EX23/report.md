# Raport strategii: RSI 3

Run `20261103-131828` · silnik 0.8.0 · kod `1121bed6c1d843d5` · dane `2e94d23547d8dd53`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -53.33 |
| percentyl benchmarku ≥ 95 | ✘ | 35.70 |
| PBO < 0,3 | ✘ | 0.52 |
| DSR ≥ 0,95 | ✘ | 0.13 |
| dodatni przy spreadzie ×1,5 | ✘ | -3.81 |

## Hipoteza

Dlaczego ta strategia ma działać — 1–3 zdania, spisane PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 466** (2 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 8 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 294 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 120 świecach | rsi_level=25 | 53 | 1.37 | 17.93 | 60.4 | 22 | -4.26 | -53.33 |
| 2 | po 96 świecach | rsi_level=25 | 53 | 0.70 | 6.19 | 58.5 | 24 | -2.00 | -32.62 |
| 3 | po 12 świecach | rsi_level=25 | 57 | 0.40 | 4.97 | 50.9 | 24 | 0.19 | 6.76 |
| 4 | po 16 świecach | rsi_level=25 | 57 | 0.39 | 3.06 | 56.1 | 24 | -0.03 | 0.62 |
| 5 | po 36 świecach | rsi_level=25 | 53 | 0.37 | 0.04 | 64.2 | 24 | -0.34 | -17.80 |
| 6 | po 4 świecach | rsi_level=25 | 60 | 0.36 | 3.94 | 56.7 | 25 | -0.43 | -7.61 |
| 7 | po 24 świecach | rsi_level=25 | 56 | 0.23 | -0.92 | 57.1 | 24 | -0.32 | -13.18 |
| 8 | ATR5 TP 4× SL 3× max 120 | rsi_level=25 | 55 | 0.21 | 14.86 | 52.7 | 24 | -0.11 | -17.50 |
| 9 | ATR5 TP 3× SL 2× max 120 | rsi_level=25 | 58 | 0.21 | 4.27 | 50.0 | 25 | -0.08 | -9.49 |
| 10 | po 6 świecach | rsi_level=25 | 58 | 0.20 | 0.80 | 56.9 | 25 | -0.39 | -6.22 |

## Najlepszy wariant IS: po 120 świecach (rsi_level=25)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 9 | 4.1 | 37.3 | 44.4 |
| EURGBP | 6 | -5.8 | -34.8 | 66.7 |
| EURJPY | 13 | 21.8 | 283.4 | 69.2 |
| EURUSD | 5 | -20.5 | -102.3 | 40.0 |
| GBPUSD | 13 | -19.1 | -248.9 | 38.5 |
| USDCAD | 5 | 11.9 | 59.6 | 40.0 |
| USDCHF | 11 | 22.2 | 244.7 | 54.5 |
| USDJPY | 13 | -35.5 | -461.9 | 61.5 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 1 | -124.7 | -124.7 | 0.0 |
| 2025 | 43 | 25.0 | 1 075.4 | 60.5 |
| 2026 | 31 | -37.9 | -1 173.7 | 45.2 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 53 | 17.9 | 950.3 | 60.4 |
| OOS | 22 | -53.3 | -1 173.2 | 36.4 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 9 854 | -1.5 | -0.8 | -13.8 | -0.02 | 0 |
| 10.0% | 9 494 | -5.1 | -2.7 | -26.0 | -0.03 | 0 |
| 15.0% | 8 941 | -10.6 | -5.8 | -36.9 | -0.04 | 0 |
| 20.0% | 8 226 | -17.7 | -9.8 | -46.6 | -0.05 | 0 |
| 30.0% | 6 321 | -36.8 | -21.6 | -63.0 | -0.08 | 4 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -2.97 pips/transakcję, percentyl **35.7** (losowe: 5%=-25.26, mediana=3.21, 95%=27.61).

- **Deflated Sharpe Ratio**: 0.130 (Sharpe na transakcję 0.215, próg przy 466 próbach 0.376).

- **PBO** (CSCV, 16 bloków, 466 wariantów): 0.521 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 81 transakcji, śr. -13.70 pips, -0.91 R.

- **Bootstrap 95%** średnich pipsów: całość [-30.34; 24.59], OOS [-106.19; -9.84].

- **Spread**: ×1 -2.97, ×1,5 -3.81, ×2 -4.65 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

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
