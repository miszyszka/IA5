# Raport strategii: RSI 2

Run `20261112-165323` · silnik 0.13.0 · kod `05a4838aae5707ab` · dane `b50e2d6c1f25d7e9`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 4.03 |
| percentyl benchmarku ≥ 95 | ✔ | 99.70 |
| PBO < 0,3 | ✔ | 0.16 |
| DSR ≥ 0,95 | ✘ | 0.76 |
| dodatni przy spreadzie ×1,5 | ✔ | 4.56 |

## Hipoteza

Jak w wersji 1: w wyraźnym trendzie H1 gwałtowny ruch przeciw trendowi, w którym RSI14 przebija 70
(trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada, po której cena cofa się o ok. 1,5 ATR.
Wersja 2 (po wyniku wersji 1 na Yahoo — OOS tej wersji nie jest czysty, prób łącznie 1 + 24):
1) Największe straty wersji 1 to nie przesady, tylko SZOKI informacyjne (np. 1.08.2025 13:00 UTC, dane z rynku pracy
   USA): jedna świeca o zakresie kilku ATR to nowa cena, a nie przesada — filtr „szok” pomija taki epizod.
2) Seria RSI zamyka stratę dopiero po 6 godzinach; w tym czasie cena potrafiła odejść o 100+ pipsów — stop cenowy
   2 / 3 × ATR ucina ten ogon (wariant bez stopu zostaje do porównania).
3) Więcej wejść: łagodniejszy próg „wyraźnego trendu” (0,15 ATR) i krótsza średnia (EMA100).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-12; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-10, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 5 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 24** (8 wejścia × 3 wyjść).

- Pominięte sygnały, średnio na wariant: 2 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 25.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=3.0 | 362 | 0.40 | 6.03 | 71.8 | 126 | 0.35 | 5.14 |
| 2 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 445 | 0.39 | 5.85 | 71.0 | 158 | 0.19 | 4.03 |
| 3 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=0 | 260 | 0.35 | 6.15 | 70.4 | 92 | 0.43 | 8.49 |
| 4 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=3.0 | 217 | 0.32 | 5.41 | 70.0 | 78 | 0.39 | 7.23 |
| 5 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=0 | 206 | 0.32 | 5.30 | 68.9 | 73 | -0.02 | 4.27 |
| 6 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 285 | 0.28 | 4.20 | 69.8 | 105 | -0.19 | 0.61 |
| 7 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=3.0 | 151 | 0.26 | 5.45 | 67.5 | 45 | 0.56 | 5.82 |
| 8 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=3.0 | 212 | 0.25 | 4.06 | 69.3 | 64 | 0.22 | 2.05 |
| 9 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 286 | 0.04 | 0.87 | 58.7 | 105 | -0.08 | -1.44 |
| 10 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 455 | 0.03 | 0.69 | 58.0 | 159 | 0.07 | 2.28 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (ema=200, nachylenie=0.15, szok=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 57 | 9.6 | 547.8 | 96.5 |
| EURGBP | 71 | 0.0 | 3.2 | 56.3 |
| EURJPY | 80 | 7.8 | 624.8 | 68.8 |
| EURUSD | 76 | 6.3 | 482.6 | 75.0 |
| GBPUSD | 78 | 4.9 | 381.5 | 76.9 |
| USDCAD | 67 | -0.4 | -29.7 | 53.7 |
| USDCHF | 62 | 11.6 | 717.1 | 83.9 |
| USDJPY | 112 | 4.6 | 513.0 | 63.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 61 | 2.3 | 138.6 | 65.6 |
| 2025 | 309 | 5.9 | 1 835.6 | 69.3 |
| 2026 | 233 | 5.4 | 1 265.9 | 73.8 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 445 | 5.9 | 2 604.0 | 71.0 |
| OOS | 158 | 4.0 | 636.1 | 69.6 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 21 225 | 112.3 | 45.9 | -10.0 | -15.7 | 1.79 | 5 |
| 10.0% | 31 099 | 211.0 | 76.7 | -16.6 | -29.4 | 1.68 | 71 |
| 15.0% | 27 683 | 176.8 | 66.7 | -23.8 | -31.8 | 1.29 | 166 |
| 20.0% | 22 759 | 127.6 | 51.1 | -28.9 | -35.6 | 0.98 | 241 |
| 30.0% | 15 490 | 54.9 | 24.6 | -37.3 | -46.4 | 0.58 | 338 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-06): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **603**, otwarte: **0** (razem 603).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 603 | 0 | 0 | 1 | 2 | 7 | 5.4 | 3 240 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 603 | 0 | 0 | 1 | 2 | 7 | 5.4 | 3 240 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| AUDUSD | long | 2024-11-08 | 2024-11-15 | 7 | 120 | zamknięta | czas | -138.5 |
| AUDUSD | long | 2024-11-08 | 2024-11-11 | 2 | 6 | zamknięta | TP | 20.4 |
| EURGBP | short | 2024-11-12 | 2024-11-12 | 0 | 5 | zamknięta | seria RSI | -23.3 |
| EURGBP | short | 2024-11-12 | 2024-11-12 | 0 | 4 | zamknięta | seria RSI | -11.8 |
| EURGBP | short | 2024-11-12 | 2024-11-12 | 0 | 3 | zamknięta | seria RSI | -5.7 |
| EURGBP | short | 2024-11-12 | 2024-11-12 | 0 | 2 | zamknięta | seria RSI | -5.2 |
| USDJPY | long | 2024-11-15 | 2024-11-18 | 3 | 18 | zamknięta | TP | 55.5 |
| USDJPY | long | 2024-11-15 | 2024-11-18 | 2 | 6 | zamknięta | TP | 56.0 |
| USDJPY | long | 2024-11-15 | 2024-11-18 | 2 | 4 | zamknięta | TP | 56.7 |
| AUDUSD | short | 2024-11-18 | 2024-11-19 | 1 | 16 | zamknięta | TP | 16.0 |
| USDCAD | long | 2024-11-18 | 2024-11-19 | 1 | 29 | zamknięta | seria RSI | -57.1 |
| AUDUSD | short | 2024-11-18 | 2024-11-19 | 1 | 15 | zamknięta | TP | 15.6 |
| USDCAD | long | 2024-11-18 | 2024-11-19 | 1 | 15 | zamknięta | TP | 26.5 |
| USDCHF | long | 2024-11-18 | 2024-11-20 | 2 | 37 | zamknięta | TP | 15.4 |
| AUDUSD | short | 2024-11-18 | 2024-11-19 | 0 | 12 | zamknięta | TP | 14.1 |
| USDCHF | long | 2024-11-18 | 2024-11-19 | 1 | 21 | zamknięta | TP | 14.8 |
| AUDUSD | short | 2024-11-18 | 2024-11-19 | 0 | 11 | zamknięta | TP | 13.4 |
| GBPUSD | short | 2024-11-27 | 2024-11-27 | 0 | 7 | zamknięta | seria RSI | -62.3 |
| GBPUSD | short | 2024-11-27 | 2024-11-27 | 0 | 5 | zamknięta | seria RSI | -47.4 |
| GBPUSD | short | 2024-11-27 | 2024-11-27 | 0 | 2 | zamknięta | TP | 23.7 |
| USDJPY | short | 2024-12-04 | 2024-12-04 | 0 | 5 | zamknięta | TP | 46.5 |
| USDJPY | short | 2024-12-04 | 2024-12-04 | 0 | 4 | zamknięta | TP | 46.1 |
| EURJPY | short | 2024-12-04 | 2024-12-04 | 0 | 4 | zamknięta | TP | 48.3 |
| USDCAD | long | 2024-12-05 | 2024-12-05 | 0 | 4 | zamknięta | TP | 16.8 |
| EURGBP | short | 2024-12-05 | 2024-12-06 | 0 | 12 | zamknięta | TP | 8.3 |
| USDJPY | short | 2024-12-09 | 2024-12-09 | 0 | 5 | zamknięta | seria RSI | -58.3 |
| AUDUSD | short | 2024-12-09 | 2024-12-09 | 0 | 6 | zamknięta | TP | 18.2 |
| USDJPY | short | 2024-12-09 | 2024-12-09 | 0 | 4 | zamknięta | seria RSI | -46.9 |
| EURGBP | short | 2024-12-12 | 2024-12-12 | 0 | 8 | zamknięta | TP | 10.5 |
| USDJPY | long | 2024-12-17 | 2024-12-18 | 0 | 8 | zamknięta | TP | 31.7 |
| USDJPY | long | 2024-12-17 | 2024-12-18 | 0 | 7 | zamknięta | TP | 31.3 |
| EURJPY | long | 2024-12-17 | 2024-12-18 | 0 | 6 | zamknięta | TP | 37.6 |
| EURJPY | long | 2024-12-17 | 2024-12-18 | 0 | 5 | zamknięta | TP | 36.0 |
| EURJPY | long | 2024-12-18 | 2024-12-19 | 0 | 7 | zamknięta | TP | 39.8 |
| EURJPY | long | 2024-12-18 | 2024-12-19 | 0 | 6 | zamknięta | TP | 44.1 |
| USDCHF | long | 2024-12-20 | 2024-12-23 | 3 | 22 | zamknięta | TP | 18.4 |
| USDCHF | long | 2024-12-20 | 2024-12-23 | 3 | 15 | zamknięta | TP | 21.4 |
| USDCHF | long | 2024-12-20 | 2024-12-23 | 3 | 12 | zamknięta | TP | 21.1 |
| USDCHF | long | 2024-12-20 | 2024-12-23 | 2 | 11 | zamknięta | TP | 21.2 |
| EURUSD | short | 2024-12-20 | 2024-12-23 | 2 | 10 | zamknięta | TP | 23.8 |
| USDCHF | long | 2024-12-20 | 2024-12-23 | 2 | 10 | zamknięta | TP | 20.5 |
| EURJPY | long | 2024-12-30 | 2024-12-31 | 1 | 16 | zamknięta | seria RSI | -81.8 |
| USDJPY | long | 2024-12-30 | 2024-12-31 | 1 | 15 | zamknięta | seria RSI | -86.8 |
| EURJPY | long | 2024-12-30 | 2024-12-31 | 1 | 15 | zamknięta | seria RSI | -51.4 |
| USDJPY | long | 2024-12-30 | 2024-12-31 | 0 | 11 | zamknięta | seria RSI | -75.6 |
| USDJPY | long | 2024-12-30 | 2024-12-31 | 0 | 9 | zamknięta | seria RSI | -60.5 |
| USDJPY | long | 2024-12-31 | 2024-12-31 | 0 | 5 | zamknięta | seria RSI | -47.8 |
| USDJPY | long | 2024-12-31 | 2024-12-31 | 0 | 4 | zamknięta | seria RSI | -22.4 |
| EURJPY | short | 2025-01-06 | 2025-01-10 | 4 | 107 | zamknięta | TP | 36.7 |
| EURJPY | short | 2025-01-06 | 2025-01-10 | 4 | 106 | zamknięta | TP | 35.7 |
| EURUSD | short | 2025-01-06 | 2025-01-08 | 2 | 47 | zamknięta | TP | 17.3 |
| EURUSD | short | 2025-01-14 | 2025-01-15 | 1 | 25 | zamknięta | TP | 24.3 |
| EURUSD | short | 2025-01-14 | 2025-01-15 | 1 | 22 | zamknięta | TP | 23.4 |
| EURUSD | short | 2025-01-14 | 2025-01-15 | 1 | 20 | zamknięta | TP | 21.9 |
| EURUSD | short | 2025-01-14 | 2025-01-15 | 1 | 19 | zamknięta | TP | 21.1 |
| USDCHF | long | 2025-01-14 | 2025-01-15 | 1 | 19 | zamknięta | TP | 17.4 |
| EURJPY | short | 2025-01-20 | 2025-01-20 | 0 | 5 | zamknięta | seria RSI | -64.6 |
| EURJPY | short | 2025-01-20 | 2025-01-20 | 0 | 4 | zamknięta | seria RSI | -50.7 |
| GBPUSD | short | 2025-01-20 | 2025-01-20 | 0 | 4 | zamknięta | TP | 33.2 |
| EURGBP | long | 2025-01-23 | 2025-01-24 | 0 | 12 | zamknięta | TP | 8.2 |
| EURGBP | long | 2025-01-23 | 2025-01-24 | 0 | 11 | zamknięta | TP | 7.9 |
| EURGBP | long | 2025-01-23 | 2025-01-24 | 0 | 10 | zamknięta | TP | 7.7 |
| USDCAD | long | 2025-02-03 | 2025-02-10 | 7 | 120 | zamknięta | czas | -100.1 |
| USDCAD | long | 2025-02-03 | 2025-02-11 | 7 | 120 | zamknięta | czas | -73.8 |
| GBPUSD | long | 2025-02-06 | 2025-02-06 | 0 | 5 | zamknięta | seria RSI | -65.3 |
| EURGBP | short | 2025-02-06 | 2025-02-07 | 1 | 30 | zamknięta | TP | 9.0 |
| GBPUSD | long | 2025-02-06 | 2025-02-06 | 0 | 4 | zamknięta | seria RSI | -45.5 |
| EURGBP | short | 2025-02-06 | 2025-02-07 | 1 | 24 | zamknięta | TP | 9.9 |
| EURJPY | short | 2025-02-11 | 2025-02-11 | 0 | 5 | zamknięta | seria RSI | -43.4 |
| EURUSD | short | 2025-02-11 | 2025-02-11 | 0 | 5 | zamknięta | seria RSI | -40.7 |
| USDJPY | short | 2025-02-12 | 2025-02-12 | 0 | 5 | zamknięta | seria RSI | -36.7 |
| USDJPY | short | 2025-02-12 | 2025-02-12 | 0 | 4 | zamknięta | seria RSI | -8.2 |
| EURUSD | long | 2025-02-19 | 2025-02-19 | 0 | 4 | zamknięta | TP | 12.7 |
| USDCAD | short | 2025-02-19 | 2025-02-20 | 1 | 15 | zamknięta | TP | 23.3 |
| USDCAD | short | 2025-02-19 | 2025-02-20 | 0 | 12 | zamknięta | TP | 23.0 |
| AUDUSD | long | 2025-02-21 | 2025-02-24 | 2 | 3 | zamknięta | TP | 12.7 |
| GBPUSD | long | 2025-02-27 | 2025-03-03 | 4 | 39 | zamknięta | TP | 23.0 |
| AUDUSD | short | 2025-03-04 | 2025-03-05 | 0 | 5 | zamknięta | TP | 20.9 |
| AUDUSD | long | 2025-03-19 | 2025-03-19 | 0 | 11 | zamknięta | TP | 11.2 |
| AUDUSD | long | 2025-03-19 | 2025-03-19 | 0 | 10 | zamknięta | TP | 12.0 |
| EURJPY | long | 2025-03-20 | 2025-03-20 | 0 | 12 | zamknięta | seria RSI | -69.8 |
| EURUSD | long | 2025-03-20 | 2025-03-20 | 0 | 5 | zamknięta | seria RSI | -23.2 |
| USDCHF | short | 2025-03-20 | 2025-03-20 | 0 | 5 | zamknięta | seria RSI | -18.0 |
| EURUSD | long | 2025-03-20 | 2025-03-20 | 0 | 4 | zamknięta | seria RSI | -20.9 |
| USDCHF | short | 2025-03-20 | 2025-03-20 | 0 | 4 | zamknięta | seria RSI | -16.3 |
| EURJPY | long | 2025-03-25 | 2025-03-26 | 0 | 11 | zamknięta | TP | 36.4 |
| EURGBP | short | 2025-03-28 | 2025-03-31 | 3 | 14 | zamknięta | TP | 11.6 |
| EURGBP | long | 2025-04-15 | 2025-04-15 | 0 | 5 | zamknięta | seria RSI | -21.9 |
| EURGBP | long | 2025-04-15 | 2025-04-15 | 0 | 4 | zamknięta | seria RSI | -10.6 |
| USDCAD | short | 2025-04-15 | 2025-04-16 | 0 | 13 | zamknięta | TP | 42.7 |
| USDCHF | short | 2025-04-22 | 2025-04-29 | 7 | 120 | zamknięta | czas | -66.1 |
| EURUSD | long | 2025-04-22 | 2025-04-23 | 0 | 4 | zamknięta | TP | 34.9 |
| GBPUSD | long | 2025-04-22 | 2025-04-23 | 0 | 4 | zamknięta | TP | 26.6 |
| USDCHF | short | 2025-04-22 | 2025-04-23 | 0 | 12 | zamknięta | TP | 37.0 |
| USDJPY | short | 2025-04-22 | 2025-04-23 | 0 | 4 | zamknięta | TP | 53.3 |
| USDCAD | short | 2025-04-23 | 2025-04-24 | 1 | 15 | zamknięta | TP | 37.0 |
| AUDUSD | long | 2025-05-07 | 2025-05-08 | 0 | 6 | zamknięta | TP | 20.1 |
| AUDUSD | long | 2025-05-07 | 2025-05-08 | 0 | 4 | zamknięta | TP | 19.6 |
| GBPUSD | short | 2025-05-13 | 2025-05-13 | 0 | 5 | zamknięta | seria RSI | -27.3 |
| GBPUSD | short | 2025-05-13 | 2025-05-13 | 0 | 4 | zamknięta | seria RSI | -10.7 |
| EURUSD | short | 2025-05-13 | 2025-05-16 | 3 | 68 | zamknięta | TP | 23.6 |
| EURUSD | short | 2025-05-13 | 2025-05-14 | 1 | 25 | zamknięta | TP | 22.7 |
| EURUSD | short | 2025-05-13 | 2025-05-14 | 1 | 22 | zamknięta | TP | 21.0 |
| EURUSD | short | 2025-05-13 | 2025-05-14 | 1 | 20 | zamknięta | TP | 20.3 |
| EURUSD | short | 2025-05-14 | 2025-05-14 | 0 | 9 | zamknięta | TP | 20.1 |
| USDCHF | long | 2025-05-14 | 2025-05-14 | 0 | 5 | zamknięta | TP | 22.1 |
| USDJPY | long | 2025-05-14 | 2025-05-14 | 0 | 8 | zamknięta | TP | 44.0 |
| USDJPY | long | 2025-05-15 | 2025-05-15 | 0 | 5 | zamknięta | TP | 46.9 |
| AUDUSD | long | 2025-05-27 | 2025-06-02 | 6 | 88 | zamknięta | TP | 16.4 |
| EURUSD | long | 2025-05-27 | 2025-05-27 | 0 | 5 | zamknięta | TP | 19.7 |
| USDCHF | short | 2025-05-27 | 2025-05-29 | 2 | 56 | zamknięta | TP | 19.6 |
| USDJPY | short | 2025-05-27 | 2025-05-27 | 0 | 5 | zamknięta | seria RSI | -29.5 |
| USDJPY | short | 2025-05-27 | 2025-05-27 | 0 | 4 | zamknięta | seria RSI | -16.9 |
| USDCHF | short | 2025-05-27 | 2025-05-29 | 2 | 52 | zamknięta | TP | 20.0 |
| USDCAD | short | 2025-05-27 | 2025-05-28 | 0 | 12 | zamknięta | seria RSI | -41.0 |
| USDCAD | short | 2025-05-27 | 2025-05-28 | 0 | 5 | zamknięta | TP | 21.6 |
| USDCAD | short | 2025-05-28 | 2025-05-28 | 0 | 5 | zamknięta | seria RSI | -15.3 |
| USDCAD | short | 2025-05-28 | 2025-05-28 | 0 | 4 | zamknięta | seria RSI | -11.0 |
| EURGBP | short | 2025-05-29 | 2025-05-29 | 0 | 5 | zamknięta | seria RSI | -15.7 |
| EURGBP | short | 2025-05-29 | 2025-05-29 | 0 | 4 | zamknięta | seria RSI | -10.3 |
| EURJPY | long | 2025-05-30 | 2025-05-30 | 0 | 10 | zamknięta | TP | 31.8 |
| USDCHF | short | 2025-06-03 | 2025-06-04 | 1 | 24 | zamknięta | TP | 19.7 |
| USDCHF | short | 2025-06-03 | 2025-06-04 | 1 | 23 | zamknięta | TP | 20.0 |
| EURGBP | long | 2025-06-03 | 2025-06-03 | 0 | 5 | zamknięta | seria RSI | -10.8 |
| EURGBP | long | 2025-06-03 | 2025-06-03 | 0 | 4 | zamknięta | seria RSI | -1.7 |
| USDCHF | short | 2025-06-03 | 2025-06-04 | 1 | 17 | zamknięta | TP | 21.1 |
| USDJPY | short | 2025-06-03 | 2025-06-04 | 1 | 21 | zamknięta | TP | 38.6 |
| USDJPY | short | 2025-06-03 | 2025-06-04 | 1 | 20 | zamknięta | TP | 38.3 |
| EURUSD | long | 2025-06-06 | 2025-06-09 | 2 | 10 | zamknięta | TP | 23.0 |
| EURUSD | long | 2025-06-17 | 2025-06-17 | 0 | 5 | zamknięta | seria RSI | -6.2 |
| USDCAD | short | 2025-06-17 | 2025-06-17 | 0 | 5 | zamknięta | seria RSI | -58.8 |
| EURUSD | long | 2025-06-17 | 2025-06-17 | 0 | 4 | zamknięta | seria RSI | -0.9 |
| USDCAD | short | 2025-06-17 | 2025-06-17 | 0 | 4 | zamknięta | seria RSI | -44.9 |
| USDJPY | long | 2025-06-24 | 2025-06-25 | 1 | 33 | zamknięta | TP | 42.6 |
| USDJPY | long | 2025-06-24 | 2025-06-25 | 1 | 29 | zamknięta | TP | 40.8 |
| USDJPY | long | 2025-06-24 | 2025-06-25 | 1 | 27 | zamknięta | TP | 40.8 |
| EURGBP | long | 2025-06-24 | 2025-06-27 | 3 | 77 | zamknięta | TP | 10.1 |
| EURGBP | long | 2025-06-24 | 2025-06-25 | 1 | 16 | zamknięta | TP | 10.9 |
| EURGBP | long | 2025-06-24 | 2025-06-25 | 1 | 14 | zamknięta | TP | 11.3 |
| GBPUSD | long | 2025-07-02 | 2025-07-04 | 2 | 42 | zamknięta | TP | 23.1 |
| GBPUSD | long | 2025-07-02 | 2025-07-02 | 0 | 5 | zamknięta | TP | 29.7 |
| EURUSD | long | 2025-07-07 | 2025-07-07 | 0 | 6 | zamknięta | TP | 16.0 |
| EURGBP | long | 2025-07-07 | 2025-07-08 | 1 | 19 | zamknięta | TP | 9.5 |
| EURGBP | long | 2025-07-07 | 2025-07-07 | 0 | 7 | zamknięta | TP | 9.9 |
| EURGBP | long | 2025-07-07 | 2025-07-07 | 0 | 6 | zamknięta | TP | 10.8 |
| USDJPY | long | 2025-07-16 | 2025-07-17 | 0 | 7 | zamknięta | TP | 55.3 |
| AUDUSD | short | 2025-07-18 | 2025-07-18 | 0 | 4 | zamknięta | TP | 10.6 |
| EURUSD | short | 2025-07-18 | 2025-07-18 | 0 | 4 | zamknięta | TP | 16.6 |
| USDCHF | long | 2025-07-18 | 2025-07-18 | 0 | 5 | zamknięta | TP | 14.4 |
| GBPUSD | short | 2025-07-21 | 2025-07-25 | 4 | 94 | zamknięta | TP | 18.7 |
| USDJPY | long | 2025-07-21 | 2025-07-21 | 0 | 5 | zamknięta | seria RSI | -39.7 |
| GBPUSD | short | 2025-07-21 | 2025-07-25 | 4 | 93 | zamknięta | TP | 18.3 |
| USDJPY | long | 2025-07-21 | 2025-07-21 | 0 | 4 | zamknięta | seria RSI | -34.5 |
| EURUSD | long | 2025-07-28 | 2025-07-28 | 0 | 5 | zamknięta | seria RSI | -17.2 |
| EURGBP | long | 2025-07-28 | 2025-07-28 | 0 | 5 | zamknięta | seria RSI | -20.2 |
| EURGBP | long | 2025-07-28 | 2025-07-28 | 0 | 4 | zamknięta | seria RSI | -9.8 |
| EURJPY | short | 2025-07-31 | 2025-08-01 | 1 | 19 | zamknięta | TP | 47.7 |
| EURUSD | short | 2025-08-01 | 2025-08-06 | 5 | 80 | zamknięta | seria RSI | -112.8 |
| USDCHF | long | 2025-08-01 | 2025-08-04 | 3 | 18 | zamknięta | TP | 29.3 |
| USDJPY | long | 2025-08-01 | 2025-08-01 | 0 | 5 | zamknięta | seria RSI | -77.0 |
| EURUSD | short | 2025-08-01 | 2025-08-01 | 0 | 4 | zamknięta | TP | 39.6 |
| USDCAD | long | 2025-08-01 | 2025-08-01 | 0 | 5 | zamknięta | TP | 33.1 |
| USDCHF | long | 2025-08-01 | 2025-08-01 | 0 | 4 | zamknięta | TP | 30.0 |
| USDJPY | long | 2025-08-01 | 2025-08-01 | 0 | 4 | zamknięta | seria RSI | -27.0 |
| EURUSD | short | 2025-08-01 | 2025-08-06 | 5 | 73 | zamknięta | seria RSI | -94.1 |
| EURUSD | short | 2025-08-03 | 2025-08-05 | 1 | 33 | zamknięta | TP | 41.9 |
| EURUSD | short | 2025-08-04 | 2025-08-05 | 1 | 30 | zamknięta | TP | 40.0 |
| EURJPY | short | 2025-08-05 | 2025-08-06 | 1 | 25 | zamknięta | seria RSI | -64.2 |
| EURJPY | short | 2025-08-05 | 2025-08-06 | 1 | 24 | zamknięta | seria RSI | -62.6 |
| EURJPY | short | 2025-08-06 | 2025-08-06 | 0 | 9 | zamknięta | seria RSI | -46.4 |
| EURJPY | short | 2025-08-06 | 2025-08-06 | 0 | 8 | zamknięta | seria RSI | -28.9 |
| EURJPY | short | 2025-08-06 | 2025-08-06 | 0 | 7 | zamknięta | seria RSI | -24.2 |
| EURGBP | long | 2025-08-07 | 2025-08-07 | 0 | 5 | zamknięta | seria RSI | -17.3 |
| EURGBP | long | 2025-08-07 | 2025-08-07 | 0 | 4 | zamknięta | seria RSI | -17.0 |
| EURUSD | long | 2025-08-11 | 2025-08-11 | 0 | 6 | zamknięta | TP | 19.5 |
| EURJPY | long | 2025-08-14 | 2025-08-14 | 0 | 5 | zamknięta | seria RSI | -42.7 |
| EURJPY | long | 2025-08-14 | 2025-08-14 | 0 | 4 | zamknięta | seria RSI | -22.2 |
| AUDUSD | long | 2025-08-14 | 2025-08-15 | 1 | 25 | zamknięta | TP | 13.1 |
| AUDUSD | long | 2025-08-14 | 2025-08-15 | 1 | 17 | zamknięta | TP | 13.5 |
| EURGBP | short | 2025-08-15 | 2025-08-15 | 0 | 6 | zamknięta | TP | 8.3 |
| GBPUSD | long | 2025-08-18 | 2025-08-22 | 4 | 95 | zamknięta | TP | 16.3 |
| GBPUSD | long | 2025-08-18 | 2025-08-25 | 7 | 120 | zamknięta | czas | -74.3 |
| GBPUSD | long | 2025-08-19 | 2025-08-19 | 0 | 5 | zamknięta | TP | 15.4 |
| AUDUSD | short | 2025-08-22 | 2025-08-22 | 0 | 5 | zamknięta | seria RSI | 4.6 |
| EURUSD | short | 2025-08-22 | 2025-08-22 | 0 | 5 | zamknięta | seria RSI | -3.6 |
| USDCAD | long | 2025-08-22 | 2025-08-25 | 3 | 27 | zamknięta | TP | 24.7 |
| USDJPY | long | 2025-08-22 | 2025-08-25 | 2 | 7 | zamknięta | TP | 42.4 |
| USDJPY | long | 2025-08-22 | 2025-08-25 | 2 | 6 | zamknięta | TP | 42.8 |
| USDCAD | long | 2025-08-22 | 2025-08-25 | 3 | 25 | zamknięta | TP | 25.2 |
| USDJPY | long | 2025-08-22 | 2025-08-25 | 2 | 5 | zamknięta | TP | 41.9 |
| USDCAD | long | 2025-08-22 | 2025-08-25 | 3 | 23 | zamknięta | TP | 25.6 |
| USDJPY | long | 2025-08-22 | 2025-08-25 | 2 | 4 | zamknięta | TP | 40.5 |
| EURUSD | long | 2025-09-02 | 2025-09-02 | 0 | 7 | zamknięta | TP | 17.8 |
| USDCHF | short | 2025-09-02 | 2025-09-02 | 0 | 7 | zamknięta | TP | 11.9 |
| USDCHF | short | 2025-09-02 | 2025-09-02 | 0 | 6 | zamknięta | TP | 12.2 |
| EURUSD | long | 2025-09-02 | 2025-09-02 | 0 | 5 | zamknięta | TP | 19.4 |
| USDCHF | short | 2025-09-02 | 2025-09-02 | 0 | 5 | zamknięta | TP | 13.0 |
| EURJPY | long | 2025-09-09 | 2025-09-10 | 1 | 30 | zamknięta | TP | 33.2 |
| EURJPY | long | 2025-09-09 | 2025-09-09 | 0 | 5 | zamknięta | TP | 33.0 |
| EURJPY | long | 2025-09-09 | 2025-09-09 | 0 | 4 | zamknięta | TP | 32.7 |
| AUDUSD | long | 2025-09-18 | 2025-09-18 | 0 | 9 | zamknięta | TP | 13.6 |
| GBPUSD | long | 2025-09-18 | 2025-09-19 | 1 | 22 | zamknięta | seria RSI | -76.9 |
| GBPUSD | long | 2025-09-18 | 2025-09-19 | 1 | 20 | zamknięta | seria RSI | -76.4 |
| USDJPY | long | 2025-09-29 | 2025-09-30 | 1 | 32 | zamknięta | seria RSI | -93.1 |
| GBPUSD | short | 2025-09-29 | 2025-10-02 | 4 | 84 | zamknięta | TP | 15.6 |
| USDJPY | long | 2025-09-29 | 2025-09-30 | 1 | 31 | zamknięta | seria RSI | -92.5 |
| EURUSD | short | 2025-09-29 | 2025-09-29 | 0 | 4 | zamknięta | TP | 13.9 |
| GBPUSD | short | 2025-09-29 | 2025-09-29 | 0 | 10 | zamknięta | TP | 15.8 |
| GBPUSD | short | 2025-09-29 | 2025-09-29 | 0 | 9 | zamknięta | TP | 15.2 |
| USDJPY | long | 2025-09-29 | 2025-09-30 | 1 | 29 | zamknięta | seria RSI | -76.7 |
| EURJPY | long | 2025-09-29 | 2025-09-29 | 0 | 5 | zamknięta | TP | 22.5 |
| USDJPY | long | 2025-09-29 | 2025-09-30 | 1 | 27 | zamknięta | seria RSI | -56.7 |
| EURJPY | long | 2025-09-29 | 2025-09-29 | 0 | 4 | zamknięta | TP | 23.5 |
| USDJPY | long | 2025-09-29 | 2025-09-30 | 1 | 22 | zamknięta | seria RSI | -59.2 |
| AUDUSD | long | 2025-10-02 | 2025-10-02 | 0 | 6 | zamknięta | TP | 10.3 |
| EURJPY | long | 2025-10-10 | 2025-10-10 | 0 | 5 | zamknięta | TP | 32.4 |
| USDJPY | long | 2025-10-10 | 2025-10-13 | 2 | 11 | zamknięta | TP | 43.5 |
| EURJPY | long | 2025-10-10 | 2025-10-13 | 2 | 2 | zamknięta | TP | 37.3 |
| USDJPY | long | 2025-10-10 | 2025-10-13 | 2 | 2 | zamknięta | TP | 43.3 |
| EURJPY | long | 2025-10-12 | 2025-10-13 | 0 | 9 | zamknięta | TP | 40.1 |
| USDCHF | long | 2025-10-12 | 2025-10-13 | 0 | 13 | zamknięta | TP | 19.1 |
| USDJPY | long | 2025-10-12 | 2025-10-13 | 0 | 10 | zamknięta | TP | 46.6 |
| EURGBP | short | 2025-10-14 | 2025-10-15 | 1 | 24 | zamknięta | TP | 10.6 |
| USDJPY | long | 2025-10-15 | 2025-10-15 | 0 | 7 | zamknięta | TP | 33.1 |
| EURJPY | long | 2025-10-28 | 2025-10-28 | 0 | 7 | zamknięta | TP | 30.2 |
| USDCAD | short | 2025-10-30 | 2025-10-31 | 1 | 24 | zamknięta | seria RSI | -33.8 |
| USDJPY | long | 2025-11-04 | 2025-11-05 | 1 | 32 | zamknięta | TP | 23.7 |
| USDJPY | long | 2025-11-04 | 2025-11-05 | 1 | 31 | zamknięta | TP | 25.2 |
| USDJPY | long | 2025-11-04 | 2025-11-05 | 1 | 30 | zamknięta | TP | 26.5 |
| USDJPY | long | 2025-11-04 | 2025-11-05 | 1 | 25 | zamknięta | TP | 29.7 |
| USDJPY | long | 2025-11-04 | 2025-11-05 | 0 | 11 | zamknięta | TP | 30.0 |
| GBPUSD | short | 2025-11-06 | 2025-11-13 | 7 | 120 | zamknięta | czas | -81.1 |
| GBPUSD | short | 2025-11-06 | 2025-11-07 | 1 | 14 | zamknięta | TP | 23.8 |
| GBPUSD | short | 2025-11-06 | 2025-11-07 | 0 | 12 | zamknięta | TP | 22.2 |
| GBPUSD | short | 2025-11-06 | 2025-11-07 | 0 | 11 | zamknięta | TP | 21.1 |
| USDCAD | long | 2025-11-07 | 2025-11-10 | 2 | 9 | zamknięta | seria RSI | -22.9 |
| USDCHF | long | 2025-11-07 | 2025-11-07 | 0 | 6 | zamknięta | TP | 12.5 |
| USDCAD | long | 2025-11-07 | 2025-11-10 | 2 | 5 | zamknięta | seria RSI | -12.5 |
| USDCAD | long | 2025-11-07 | 2025-11-10 | 2 | 4 | zamknięta | seria RSI | -5.0 |
| USDCAD | long | 2025-11-07 | 2025-11-10 | 2 | 3 | zamknięta | seria RSI | 2.4 |
| USDCAD | long | 2025-11-07 | 2025-11-10 | 2 | 2 | zamknięta | seria RSI | 12.0 |
| AUDUSD | short | 2025-11-10 | 2025-11-14 | 4 | 105 | zamknięta | TP | 12.6 |
| USDCAD | short | 2025-11-13 | 2025-11-14 | 1 | 19 | zamknięta | TP | 19.2 |
| EURJPY | long | 2025-11-21 | 2025-11-24 | 3 | 13 | zamknięta | TP | 47.1 |
| USDJPY | long | 2025-11-25 | 2025-11-26 | 1 | 17 | zamknięta | TP | 32.0 |
| USDJPY | long | 2025-12-10 | 2025-12-17 | 7 | 120 | zamknięta | czas | -36.4 |
| EURJPY | long | 2025-12-15 | 2025-12-15 | 0 | 7 | zamknięta | TP | 27.1 |
| EURUSD | long | 2025-12-17 | 2025-12-17 | 0 | 4 | zamknięta | TP | 16.3 |
| GBPUSD | long | 2025-12-17 | 2025-12-17 | 0 | 6 | zamknięta | TP | 23.6 |
| USDJPY | long | 2025-12-23 | 2025-12-23 | 0 | 5 | zamknięta | seria RSI | -36.0 |
| USDJPY | long | 2025-12-23 | 2025-12-23 | 0 | 4 | zamknięta | seria RSI | -25.2 |
| EURJPY | long | 2025-12-23 | 2025-12-23 | 0 | 6 | zamknięta | TP | 33.9 |
| EURGBP | short | 2026-01-07 | 2026-01-12 | 5 | 76 | zamknięta | TP | 8.2 |
| EURGBP | short | 2026-01-07 | 2026-01-09 | 2 | 45 | zamknięta | TP | 8.3 |
| EURGBP | short | 2026-01-07 | 2026-01-09 | 2 | 42 | zamknięta | TP | 7.6 |
| AUDUSD | long | 2026-01-08 | 2026-01-12 | 4 | 48 | zamknięta | TP | 9.4 |
| AUDUSD | long | 2026-01-08 | 2026-01-12 | 4 | 47 | zamknięta | TP | 9.1 |
| AUDUSD | long | 2026-01-08 | 2026-01-12 | 4 | 38 | zamknięta | TP | 9.6 |
| EURGBP | short | 2026-01-08 | 2026-01-08 | 0 | 5 | zamknięta | TP | 6.6 |
| EURUSD | short | 2026-01-12 | 2026-01-12 | 0 | 10 | zamknięta | TP | 15.5 |
| EURUSD | short | 2026-01-12 | 2026-01-12 | 0 | 9 | zamknięta | TP | 16.0 |
| EURJPY | long | 2026-01-14 | 2026-01-20 | 6 | 86 | zamknięta | TP | 35.4 |
| USDJPY | long | 2026-01-14 | 2026-01-14 | 0 | 6 | zamknięta | TP | 36.2 |
| EURJPY | long | 2026-01-14 | 2026-01-20 | 6 | 85 | zamknięta | TP | 35.9 |
| USDJPY | long | 2026-01-14 | 2026-01-14 | 0 | 4 | zamknięta | TP | 36.9 |
| EURJPY | long | 2026-01-14 | 2026-01-14 | 0 | 5 | zamknięta | TP | 35.4 |
| USDCHF | long | 2026-01-19 | 2026-01-19 | 0 | 9 | zamknięta | TP | 15.2 |
| EURJPY | long | 2026-01-23 | 2026-01-26 | 2 | 5 | zamknięta | seria RSI | -77.6 |
| EURJPY | long | 2026-01-23 | 2026-01-26 | 2 | 4 | zamknięta | seria RSI | -51.0 |
| EURJPY | long | 2026-01-23 | 2026-01-26 | 2 | 3 | zamknięta | seria RSI | -49.5 |
| USDJPY | long | 2026-02-09 | 2026-02-11 | 2 | 40 | zamknięta | seria RSI | -290.9 |
| USDCHF | short | 2026-02-11 | 2026-02-12 | 1 | 19 | zamknięta | TP | 23.8 |
| EURJPY | short | 2026-02-18 | 2026-02-18 | 0 | 5 | zamknięta | TP | 31.7 |
| EURUSD | short | 2026-02-23 | 2026-02-23 | 0 | 8 | zamknięta | TP | 23.4 |
| USDJPY | long | 2026-02-23 | 2026-02-23 | 0 | 7 | zamknięta | TP | 47.2 |
| EURGBP | short | 2026-03-13 | 2026-03-13 | 0 | 4 | zamknięta | TP | 9.4 |
| USDJPY | long | 2026-03-19 | 2026-03-19 | 0 | 5 | zamknięta | seria RSI | -54.1 |
| EURUSD | short | 2026-03-19 | 2026-03-19 | 0 | 5 | zamknięta | seria RSI | -23.7 |
| EURUSD | short | 2026-03-19 | 2026-03-19 | 0 | 4 | zamknięta | seria RSI | 3.1 |
| EURUSD | short | 2026-03-31 | 2026-03-31 | 0 | 9 | zamknięta | seria RSI | -26.2 |
| EURUSD | short | 2026-03-31 | 2026-03-31 | 0 | 5 | zamknięta | seria RSI | -19.6 |
| EURUSD | short | 2026-03-31 | 2026-03-31 | 0 | 4 | zamknięta | seria RSI | -15.6 |
| USDCHF | long | 2026-04-01 | 2026-04-02 | 1 | 17 | zamknięta | TP | 21.1 |
| USDCHF | long | 2026-04-01 | 2026-04-02 | 1 | 16 | zamknięta | TP | 20.8 |
| USDCHF | long | 2026-04-01 | 2026-04-01 | 0 | 8 | zamknięta | TP | 20.5 |
| USDCAD | long | 2026-04-06 | 2026-04-07 | 0 | 12 | zamknięta | TP | 17.4 |
| USDCAD | short | 2026-04-13 | 2026-04-13 | 0 | 8 | zamknięta | TP | 22.7 |
| EURJPY | long | 2026-04-17 | 2026-04-20 | 2 | 7 | zamknięta | TP | 32.9 |
| USDCAD | short | 2026-04-28 | 2026-04-29 | 1 | 26 | zamknięta | TP | 22.6 |
| USDCHF | long | 2026-04-30 | 2026-04-30 | 0 | 5 | zamknięta | seria RSI | -31.4 |
| USDCHF | long | 2026-04-30 | 2026-04-30 | 0 | 4 | zamknięta | seria RSI | -27.8 |
| USDCAD | short | 2026-05-04 | 2026-05-04 | 0 | 4 | zamknięta | TP | 15.7 |
| USDJPY | short | 2026-05-05 | 2026-05-06 | 1 | 17 | zamknięta | TP | 29.9 |
| USDJPY | short | 2026-05-05 | 2026-05-06 | 1 | 16 | zamknięta | TP | 29.9 |
| USDJPY | short | 2026-05-05 | 2026-05-06 | 1 | 15 | zamknięta | TP | 29.1 |
| EURJPY | short | 2026-05-05 | 2026-05-06 | 1 | 14 | zamknięta | TP | 30.7 |
| EURJPY | short | 2026-05-05 | 2026-05-06 | 0 | 13 | zamknięta | TP | 29.8 |
| EURJPY | short | 2026-05-05 | 2026-05-06 | 0 | 12 | zamknięta | TP | 29.0 |
| EURJPY | short | 2026-05-05 | 2026-05-06 | 0 | 11 | zamknięta | TP | 27.9 |
| USDJPY | short | 2026-05-05 | 2026-05-06 | 0 | 6 | zamknięta | TP | 26.8 |
| USDJPY | short | 2026-05-05 | 2026-05-05 | 0 | 4 | zamknięta | TP | 25.7 |
| AUDUSD | long | 2026-05-07 | 2026-05-08 | 0 | 13 | zamknięta | TP | 14.6 |
| AUDUSD | long | 2026-05-07 | 2026-05-08 | 0 | 7 | zamknięta | TP | 15.1 |
| AUDUSD | long | 2026-05-07 | 2026-05-08 | 0 | 5 | zamknięta | TP | 14.6 |
| EURGBP | long | 2026-05-18 | 2026-05-18 | 0 | 5 | zamknięta | seria RSI | -9.5 |
| EURGBP | long | 2026-05-18 | 2026-05-18 | 0 | 4 | zamknięta | seria RSI | -4.7 |
| GBPUSD | short | 2026-05-20 | 2026-05-21 | 1 | 20 | zamknięta | TP | 25.2 |
| GBPUSD | short | 2026-05-20 | 2026-05-21 | 0 | 13 | zamknięta | TP | 24.1 |
| GBPUSD | long | 2026-05-26 | 2026-05-29 | 3 | 72 | zamknięta | TP | 13.7 |
| EURGBP | short | 2026-05-26 | 2026-05-27 | 1 | 19 | zamknięta | seria RSI | -13.1 |
| GBPUSD | long | 2026-05-26 | 2026-05-26 | 0 | 5 | zamknięta | TP | 14.3 |
| EURGBP | short | 2026-05-26 | 2026-05-27 | 1 | 18 | zamknięta | seria RSI | -13.2 |
| EURGBP | short | 2026-05-26 | 2026-05-27 | 1 | 17 | zamknięta | seria RSI | -13.1 |
| EURGBP | short | 2026-05-26 | 2026-05-27 | 1 | 16 | zamknięta | seria RSI | -11.4 |
| USDCAD | long | 2026-05-28 | 2026-05-28 | 0 | 5 | zamknięta | seria RSI | -8.8 |
| USDCAD | long | 2026-05-28 | 2026-05-28 | 0 | 4 | zamknięta | seria RSI | -3.0 |
| EURUSD | short | 2026-06-05 | 2026-06-05 | 0 | 4 | zamknięta | TP | 8.8 |
| EURJPY | long | 2026-06-05 | 2026-06-05 | 0 | 5 | zamknięta | seria RSI | -78.8 |
| EURJPY | long | 2026-06-05 | 2026-06-05 | 0 | 4 | zamknięta | seria RSI | -72.6 |
| GBPUSD | short | 2026-06-09 | 2026-06-09 | 0 | 5 | zamknięta | TP | 16.4 |
| EURJPY | short | 2026-06-09 | 2026-06-09 | 0 | 4 | zamknięta | TP | 20.1 |
| GBPUSD | short | 2026-06-09 | 2026-06-09 | 0 | 4 | zamknięta | TP | 16.3 |
| USDJPY | long | 2026-06-11 | 2026-06-12 | 0 | 7 | zamknięta | TP | 17.2 |
| AUDUSD | short | 2026-06-11 | 2026-06-12 | 0 | 10 | zamknięta | TP | 17.9 |
| AUDUSD | short | 2026-06-11 | 2026-06-12 | 0 | 11 | zamknięta | TP | 17.3 |
| USDCHF | long | 2026-06-11 | 2026-06-12 | 0 | 8 | zamknięta | TP | 20.0 |
| USDCAD | long | 2026-06-25 | 2026-06-29 | 4 | 45 | zamknięta | TP | 23.3 |
| USDJPY | long | 2026-07-02 | 2026-07-06 | 4 | 46 | zamknięta | TP | 27.5 |
| USDJPY | long | 2026-07-02 | 2026-07-06 | 4 | 40 | zamknięta | TP | 31.7 |
| USDJPY | long | 2026-07-10 | 2026-07-10 | 0 | 5 | zamknięta | seria RSI | -48.6 |
| EURJPY | long | 2026-07-10 | 2026-07-10 | 0 | 5 | zamknięta | seria RSI | -28.1 |
| USDJPY | long | 2026-07-10 | 2026-07-10 | 0 | 4 | zamknięta | seria RSI | -17.5 |
| EURJPY | long | 2026-07-10 | 2026-07-10 | 0 | 4 | zamknięta | seria RSI | -13.7 |
| EURUSD | short | 2026-07-15 | 2026-07-15 | 0 | 4 | zamknięta | seria RSI | -42.9 |
| USDCHF | long | 2026-07-15 | 2026-07-15 | 0 | 5 | zamknięta | seria RSI | -24.3 |
| USDCHF | long | 2026-07-15 | 2026-07-15 | 0 | 4 | zamknięta | seria RSI | -17.3 |
| EURGBP | short | 2026-07-17 | 2026-07-17 | 0 | 5 | zamknięta | TP | 6.5 |
| USDCAD | short | 2026-07-20 | 2026-07-27 | 7 | 120 | zamknięta | czas | -62.4 |
| USDCAD | short | 2026-07-20 | 2026-07-27 | 7 | 120 | zamknięta | czas | -59.5 |
| USDCAD | short | 2026-07-20 | 2026-07-27 | 7 | 120 | zamknięta | czas | -56.1 |
| USDCAD | short | 2026-07-20 | 2026-07-21 | 0 | 10 | zamknięta | TP | 19.9 |
| EURGBP | short | 2026-07-21 | 2026-07-28 | 7 | 120 | zamknięta | czas | -33.5 |
| EURGBP | short | 2026-07-21 | 2026-07-21 | 0 | 9 | zamknięta | TP | 8.1 |
| EURGBP | short | 2026-07-21 | 2026-07-21 | 0 | 8 | zamknięta | TP | 9.1 |
| EURGBP | short | 2026-07-21 | 2026-07-21 | 0 | 7 | zamknięta | TP | 9.6 |
| EURGBP | short | 2026-07-21 | 2026-07-21 | 0 | 6 | zamknięta | TP | 9.3 |
| GBPUSD | short | 2026-07-29 | 2026-07-30 | 0 | 10 | zamknięta | TP | 23.6 |
| EURGBP | long | 2026-08-06 | 2026-08-07 | 1 | 19 | zamknięta | TP | 4.7 |
| USDJPY | short | 2026-08-06 | 2026-08-07 | 1 | 22 | zamknięta | TP | 21.3 |
| EURGBP | long | 2026-08-06 | 2026-08-07 | 1 | 17 | zamknięta | TP | 5.0 |
| USDJPY | short | 2026-08-06 | 2026-08-07 | 1 | 21 | zamknięta | TP | 22.5 |
| EURGBP | long | 2026-08-06 | 2026-08-06 | 0 | 5 | zamknięta | TP | 4.9 |
| EURJPY | short | 2026-08-06 | 2026-08-07 | 0 | 9 | zamknięta | TP | 24.0 |
| USDJPY | short | 2026-08-06 | 2026-08-07 | 0 | 9 | zamknięta | TP | 24.4 |
| USDJPY | short | 2026-08-06 | 2026-08-07 | 1 | 15 | zamknięta | TP | 22.4 |
| USDJPY | short | 2026-08-10 | 2026-08-10 | 0 | 10 | zamknięta | seria RSI | -32.1 |
| USDJPY | short | 2026-08-10 | 2026-08-10 | 0 | 9 | zamknięta | seria RSI | -24.7 |
| USDCAD | short | 2026-08-18 | 2026-08-19 | 0 | 10 | zamknięta | TP | 18.2 |
| USDCAD | short | 2026-08-18 | 2026-08-18 | 0 | 4 | zamknięta | TP | 18.1 |
| AUDUSD | long | 2026-08-19 | 2026-08-19 | 0 | 12 | zamknięta | TP | 7.2 |
| AUDUSD | long | 2026-08-19 | 2026-08-19 | 0 | 9 | zamknięta | TP | 7.5 |
| AUDUSD | long | 2026-08-19 | 2026-08-19 | 0 | 8 | zamknięta | TP | 7.5 |
| USDCAD | short | 2026-08-24 | 2026-08-24 | 0 | 5 | zamknięta | seria RSI | -25.1 |
| USDCAD | short | 2026-08-24 | 2026-08-24 | 0 | 4 | zamknięta | seria RSI | -8.6 |
| GBPUSD | long | 2026-08-26 | 2026-08-30 | 4 | 55 | zamknięta | seria RSI | -67.1 |
| GBPUSD | long | 2026-08-26 | 2026-08-30 | 4 | 54 | zamknięta | seria RSI | -52.6 |
| AUDUSD | long | 2026-08-28 | 2026-09-01 | 3 | 31 | zamknięta | TP | 10.7 |
| AUDUSD | long | 2026-08-28 | 2026-09-01 | 3 | 30 | zamknięta | TP | 10.7 |
| AUDUSD | long | 2026-08-28 | 2026-08-31 | 2 | 8 | zamknięta | TP | 10.3 |
| AUDUSD | long | 2026-08-28 | 2026-09-01 | 3 | 28 | zamknięta | TP | 9.7 |
| USDCAD | long | 2026-09-02 | 2026-09-02 | 0 | 5 | zamknięta | seria RSI | -9.2 |
| USDCAD | long | 2026-09-02 | 2026-09-02 | 0 | 4 | zamknięta | seria RSI | -14.4 |
| USDCHF | long | 2026-09-03 | 2026-09-04 | 1 | 29 | zamknięta | TP | 14.3 |
| USDCHF | long | 2026-09-03 | 2026-09-04 | 1 | 28 | zamknięta | TP | 14.4 |
| USDCHF | long | 2026-09-03 | 2026-09-04 | 1 | 25 | zamknięta | TP | 14.7 |
| GBPUSD | short | 2026-09-03 | 2026-09-04 | 1 | 21 | zamknięta | TP | 18.2 |
| AUDUSD | long | 2026-09-10 | 2026-09-10 | 0 | 5 | zamknięta | seria RSI | -27.5 |
| AUDUSD | long | 2026-09-10 | 2026-09-10 | 0 | 4 | zamknięta | seria RSI | 0.4 |
| EURJPY | short | 2026-09-16 | 2026-09-16 | 0 | 7 | zamknięta | TP | 30.1 |
| EURJPY | short | 2026-09-16 | 2026-09-16 | 0 | 6 | zamknięta | TP | 29.7 |
| USDJPY | long | 2026-09-25 | 2026-09-25 | 0 | 5 | zamknięta | seria RSI | -40.4 |
| USDJPY | long | 2026-09-25 | 2026-09-25 | 0 | 4 | zamknięta | seria RSI | -32.4 |
| EURGBP | long | 2026-09-28 | 2026-09-28 | 0 | 5 | zamknięta | seria RSI | -16.4 |
| EURGBP | long | 2026-09-28 | 2026-09-28 | 0 | 4 | zamknięta | seria RSI | -6.0 |
| GBPUSD | short | 2026-09-30 | 2026-10-01 | 1 | 18 | zamknięta | TP | 17.2 |
| GBPUSD | short | 2026-09-30 | 2026-09-30 | 0 | 7 | zamknięta | TP | 17.5 |
| GBPUSD | short | 2026-09-30 | 2026-09-30 | 0 | 5 | zamknięta | TP | 18.3 |
| EURJPY | short | 2026-10-06 | 2026-10-07 | 1 | 19 | zamknięta | TP | 35.4 |
| USDCAD | long | 2026-10-06 | 2026-10-07 | 1 | 18 | zamknięta | TP | 23.7 |
| USDCAD | long | 2026-10-06 | 2026-10-07 | 0 | 12 | zamknięta | TP | 22.3 |
| USDCAD | long | 2026-10-13 | 2026-10-13 | 0 | 5 | zamknięta | seria RSI | -18.8 |
| USDCAD | long | 2026-10-13 | 2026-10-13 | 0 | 4 | zamknięta | seria RSI | 0.2 |
| GBPUSD | long | 2026-10-14 | 2026-10-14 | 0 | 5 | zamknięta | seria RSI | -33.7 |
| GBPUSD | long | 2026-10-14 | 2026-10-14 | 0 | 4 | zamknięta | seria RSI | -0.5 |
| GBPUSD | long | 2026-10-26 | 2026-10-29 | 3 | 79 | zamknięta | TP | 13.9 |
| GBPUSD | long | 2026-10-26 | 2026-10-29 | 3 | 78 | zamknięta | TP | 13.7 |
| USDCAD | short | 2026-10-27 | 2026-10-28 | 1 | 17 | zamknięta | TP | 18.6 |
| USDCAD | short | 2026-10-27 | 2026-10-28 | 1 | 17 | zamknięta | TP | 18.1 |
| GBPUSD | long | 2026-11-06 | 2026-11-06 | 0 | 5 | zamknięta | seria RSI | -19.5 |
| GBPUSD | long | 2026-11-06 | 2026-11-06 | 0 | 4 | zamknięta | seria RSI | -4.7 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 603); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 5.37 pips/transakcję, percentyl **99.7** (losowe: 5%=-4.98, mediana=-0.98, 95%=2.68).

- **Deflated Sharpe Ratio**: 0.756 (Sharpe na transakcję 0.227, próg przy 24 próbach 0.185).

- **PBO** (CSCV, 16 bloków, 24 wariantów): 0.160 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 300 transakcji, śr. 6.49 pips, 0.49 R.

- **Bootstrap 95%** średnich pipsów: całość [2.65; 8.02], OOS [0.41; 7.53].

- **Spread**: ×1 5.37, ×1,5 4.56, ×2 3.75 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 0.8 nocy na transakcję, 40% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 4.97, 1 pips: 4.57 pips/transakcję.

## Forward test od zamrożenia (W4, D-056)

- Zamrożona 2026-10-31; oceniany wariant: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (zamrożony, nie ranking); oczekiwanie sprzed zamrożenia: 5.43 pips / 0.34 R na transakcję (599 transakcji).
- **Forward: 4 transakcji, śr. -2.72 pips (-0.22 R), suma -11 pips, win 50%, t = -0.44; bootstrap 95% [—; —].**
- Odchylenie od oczekiwania: z = -0.51 (|z| ≥ 2 = forward nie wygląda jak backtest; przy małym n liczba ta jest głównie szumem — potrzeba setek transakcji, żeby odróżnić +3 pipsy od zera).

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Jak w wersji 1: w wyraźnym trendzie H1 gwałtowny ruch przeciw trendowi, w którym RSI14 przebija 70
(trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada, po której cena cofa się o ok. 1,5 ATR.
Wersja 2 (po wyniku wersji 1 na Yahoo — OOS tej wersji nie jest czysty, prób łącznie 1 + 24):
1) Największe straty wersji 1 to nie przesady, tylko SZOKI informacyjne (np. 1.08.2025 13:00 UTC, dane z rynku pracy
   USA): jedna świeca o zakresie kilku ATR to nowa cena, a nie przesada — filtr „szok” pomija taki epizod.
2) Seria RSI zamyka stratę dopiero po 6 godzinach; w tym czasie cena potrafiła odejść o 100+ pipsów — stop cenowy
   2 / 3 × ATR ucina ten ogon (wariant bez stopu zostaje do porównania).
3) Więcej wejść: łagodniejszy próg „wyraźnego trendu” (0,15 ATR) i krótsza średnia (EMA100)."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin, jak w wersji 1

PARAMS = {
    "ema": [100, 200],              # średnia trendu
    "nachylenie": [0.15, 0.25],     # „wyraźny trend”: zmiana EMA na 10 świec > tyle × ATR14 (wersja 1: 0,25)
    "szok": [0, 3.0],               # 0 = bez filtra; 3.0 = pomiń epizod, gdy świeca przebicia ma zakres > 3 × ATR14
}

# TP 1,5 × ATR14; seria 6 zamknięć RSI za 70/30 → wyjście na open następnej; limit 120 świec;
# stop cenowy: brak (jak wersja 1) / 2 / 3 × ATR14 od ceny wejścia
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120, **({"sl": sl} if sl else {})}
         for sl in (0, 2.0, 3.0)]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3 (jak w wersji 1)."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, p["ema"])
    atr = ind.atr(df, 14)
    slope = (ema - ema.shift(10)) / atr                     # nachylenie EMA na 10 świec, w ATR14
    up = (slope > p["nachylenie"]).to_numpy()
    down = (slope < -p["nachylenie"]).to_numpy()
    rng = ((df.high - df.low) / atr.shift(1)).to_numpy()    # zakres świecy względem ATR sprzed niej
    shock = rng > p["szok"] if p["szok"] else np.zeros(len(df), bool)
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record, skip = 0, 0, 0, 0.0, False
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
                if deeper and count < MAX_POS and streak < RUN and not skip:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec epizodu
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record, skip = -1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record, skip = 1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = weight(100 - LEVEL - x)
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
