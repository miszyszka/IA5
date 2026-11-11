# Raport strategii: Powrót

Run `20261111-141715` · silnik 0.13.0 · kod `12864a1b4312df32` · dane `ae473b72007eaefa`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 9.75 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✔ | 0.16 |
| DSR ≥ 0,95 | ✘ | 0.68 |
| dodatni przy spreadzie ×1,5 | ✔ | 9.79 |

## Hipoteza

FX-POWRÓT v2 (pomysł z 20.10.2026, reguły z IA4 sekcja 7b). Po gwałtownym impulsie w górę (zamknięcie ≥ 2 × ATR100
wyżej niż poprzednie) kurs często cofa się w stronę ceny sprzed impulsu. Pierwsza czerwona świeca w ciągu 3 świec
po impulsie pokazuje, że kupujący się wyczerpali — short z celem w połowie drogi od szczytu do bazy, bez stopu,
limit 60 świec.
Różnice wobec oryginału (ograniczenia IA5): 8 par zamiast 10; warunek „open wejścia ≥ baza + 0,5 ATR” sprawdzany na
zamknięciu świecy sygnału (open następnej nie jest znany w chwili sygnału); TP jako poziom ceny P − ½(P − B) silnik
na razie nie obsługuje — wyjścia przybliżone przez TP w wielokrotnościach ATR14 (patrz EXITS).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-11; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 5** (1 wejścia × 5 wyjść).

- Pominięte sygnały, średnio na wariant: 32 (limit otwartych pozycji w parze), 2.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 5.0 (przerwa w dostępie do danych), 1.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1.5× SL 0× max 60 | — | 207 | 0.53 | 10.86 | 83.6 | 76 | 0.48 | 9.75 |
| 2 | ATR14 TP 1× SL 0× max 60 | — | 213 | 0.46 | 9.15 | 91.5 | 79 | 0.51 | 9.30 |
| 3 | ATR14 TP 2× SL 0× max 60 | — | 197 | 0.11 | 5.06 | 72.1 | 74 | 0.44 | 10.12 |
| 4 | po 60 świecach | — | 179 | -0.18 | -1.88 | 45.8 | 64 | 0.17 | 10.26 |
| 5 | ATR14 TP 3× SL 0× max 60 | — | 190 | -0.21 | -1.12 | 55.3 | 71 | 0.25 | 10.12 |

## Najlepszy wariant IS: ATR14 TP 1.5× SL 0× max 60 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 40 | 6.5 | 260.4 | 82.5 |
| EURGBP | 43 | 3.2 | 136.9 | 79.1 |
| EURJPY | 24 | 18.7 | 448.8 | 87.5 |
| EURUSD | 56 | 7.2 | 401.4 | 82.1 |
| GBPUSD | 57 | 14.3 | 815.6 | 86.0 |
| USDCAD | 12 | 8.5 | 101.6 | 83.3 |
| USDCHF | 27 | 4.7 | 127.5 | 81.5 |
| USDJPY | 24 | 29.0 | 696.9 | 91.7 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 20 | 18.3 | 366.7 | 85.0 |
| 2025 | 145 | 9.3 | 1 354.6 | 81.4 |
| 2026 | 118 | 10.7 | 1 267.8 | 86.4 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 207 | 10.9 | 2 248.0 | 83.6 |
| OOS | 76 | 9.8 | 741.1 | 84.2 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 14 312 | 43.1 | 19.4 | -6.6 | -7.7 | 2.17 | 0 |
| 10.0% | 20 284 | 102.8 | 41.8 | -13.1 | -15.4 | 2.17 | 0 |
| 15.0% | 28 457 | 184.6 | 67.6 | -19.5 | -23.0 | 2.16 | 0 |
| 20.0% | 39 495 | 294.9 | 97.0 | -25.9 | -30.6 | 2.16 | 0 |
| 30.0% | 59 260 | 492.6 | 140.7 | -38.3 | -45.6 | 1.98 | 13 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-11): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **283**, otwarte: **0** (razem 283).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 283 | 0 | 1 | 1 | 4 | 6 | 10.6 | 2 989 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 283 | 0 | 1 | 1 | 4 | 6 | 10.6 | 2 989 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDCHF | short | 2024-11-01 | 2024-11-01 | 0 | 4 | zamknięta | TP | 15.8 |
| GBPUSD | short | 2024-11-01 | 2024-11-01 | 0 | 3 | zamknięta | TP | 26.3 |
| USDCHF | short | 2024-11-01 | 2024-11-04 | 2 | 6 | zamknięta | TP | 21.1 |
| AUDUSD | short | 2024-11-06 | 2024-11-06 | 0 | 2 | zamknięta | TP | 28.7 |
| GBPUSD | short | 2024-11-06 | 2024-11-06 | 0 | 2 | zamknięta | TP | 43.5 |
| GBPUSD | short | 2024-11-14 | 2024-11-14 | 0 | 4 | zamknięta | TP | 28.0 |
| EURGBP | short | 2024-11-18 | 2024-11-18 | 0 | 2 | zamknięta | TP | 11.9 |
| USDCHF | short | 2024-11-22 | 2024-11-25 | 2 | 7 | zamknięta | TP | 24.6 |
| EURGBP | short | 2024-11-25 | 2024-11-27 | 2 | 60 | zamknięta | czas | 1.6 |
| USDJPY | short | 2024-11-25 | 2024-11-26 | 0 | 11 | zamknięta | TP | 51.2 |
| EURUSD | short | 2024-11-27 | 2024-12-02 | 4 | 58 | zamknięta | TP | 25.8 |
| EURUSD | short | 2024-12-04 | 2024-12-09 | 5 | 60 | zamknięta | czas | -17.6 |
| EURJPY | short | 2024-12-05 | 2024-12-05 | 0 | 2 | zamknięta | TP | 50.2 |
| EURJPY | short | 2024-12-11 | 2024-12-11 | 0 | 4 | zamknięta | TP | 52.2 |
| USDJPY | short | 2024-12-11 | 2024-12-11 | 0 | 3 | zamknięta | TP | 47.6 |
| USDCHF | short | 2024-12-12 | 2024-12-17 | 5 | 60 | zamknięta | czas | -76.4 |
| EURGBP | short | 2024-12-13 | 2024-12-16 | 3 | 28 | zamknięta | TP | 11.9 |
| GBPUSD | short | 2024-12-16 | 2024-12-18 | 2 | 51 | zamknięta | TP | 21.5 |
| EURGBP | short | 2024-12-19 | 2024-12-24 | 5 | 60 | zamknięta | czas | -28.2 |
| GBPUSD | short | 2024-12-20 | 2024-12-23 | 3 | 20 | zamknięta | TP | 27.0 |
| USDJPY | short | 2024-12-31 | 2025-01-06 | 6 | 60 | zamknięta | czas | -93.5 |
| AUDUSD | short | 2025-01-06 | 2025-01-07 | 2 | 35 | zamknięta | TP | 14.2 |
| EURUSD | short | 2025-01-06 | 2025-01-06 | 0 | 2 | zamknięta | TP | 29.9 |
| GBPUSD | short | 2025-01-06 | 2025-01-06 | 0 | 2 | zamknięta | TP | 27.3 |
| EURGBP | short | 2025-01-09 | 2025-01-09 | 0 | 5 | zamknięta | TP | 15.1 |
| EURGBP | short | 2025-01-14 | 2025-01-15 | 2 | 36 | zamknięta | TP | 14.0 |
| AUDUSD | short | 2025-01-15 | 2025-01-15 | 0 | 2 | zamknięta | TP | 18.1 |
| EURUSD | short | 2025-01-15 | 2025-01-15 | 0 | 2 | zamknięta | TP | 22.4 |
| GBPUSD | short | 2025-01-15 | 2025-01-15 | 0 | 2 | zamknięta | TP | 36.0 |
| EURGBP | short | 2025-01-17 | 2025-01-21 | 5 | 60 | zamknięta | czas | 4.4 |
| AUDUSD | short | 2025-01-17 | 2025-01-22 | 5 | 60 | zamknięta | czas | -49.5 |
| EURUSD | short | 2025-01-20 | 2025-01-20 | 0 | 2 | zamknięta | TP | 30.1 |
| GBPUSD | short | 2025-01-20 | 2025-01-21 | 0 | 9 | zamknięta | TP | 37.6 |
| EURUSD | short | 2025-01-24 | 2025-01-24 | 0 | 3 | zamknięta | TP | 21.8 |
| EURUSD | short | 2025-01-24 | 2025-01-24 | 0 | 4 | zamknięta | TP | 23.4 |
| AUDUSD | short | 2025-02-03 | 2025-02-06 | 2 | 60 | zamknięta | czas | -86.0 |
| EURGBP | short | 2025-02-06 | 2025-02-06 | 0 | 2 | zamknięta | TP | 14.2 |
| AUDUSD | short | 2025-02-13 | 2025-02-13 | 0 | 2 | zamknięta | TP | 16.9 |
| EURUSD | short | 2025-02-13 | 2025-02-13 | 0 | 2 | zamknięta | TP | 26.6 |
| USDCAD | short | 2025-02-27 | 2025-03-03 | 4 | 47 | zamknięta | TP | 36.1 |
| EURJPY | short | 2025-03-03 | 2025-03-03 | 0 | 5 | zamknięta | TP | 63.2 |
| EURUSD | short | 2025-03-04 | 2025-03-06 | 2 | 60 | zamknięta | czas | -276.5 |
| EURGBP | short | 2025-03-04 | 2025-03-04 | 0 | 1 | zamknięta | TP | 10.5 |
| EURGBP | short | 2025-03-05 | 2025-03-10 | 5 | 60 | zamknięta | czas | -62.0 |
| GBPUSD | short | 2025-03-05 | 2025-03-10 | 5 | 60 | zamknięta | czas | -54.8 |
| EURUSD | short | 2025-03-10 | 2025-03-13 | 2 | 60 | zamknięta | czas | -36.4 |
| EURUSD | short | 2025-03-14 | 2025-03-14 | 0 | 2 | zamknięta | TP | 23.5 |
| EURGBP | short | 2025-03-14 | 2025-03-14 | 0 | 1 | zamknięta | TP | 13.0 |
| USDCHF | short | 2025-03-20 | 2025-03-21 | 1 | 25 | zamknięta | TP | 20.0 |
| EURGBP | short | 2025-03-26 | 2025-03-26 | 0 | 8 | zamknięta | TP | 10.7 |
| USDCHF | short | 2025-03-31 | 2025-04-01 | 1 | 18 | zamknięta | TP | 17.9 |
| AUDUSD | short | 2025-04-01 | 2025-04-02 | 1 | 29 | zamknięta | TP | 15.7 |
| EURJPY | short | 2025-04-02 | 2025-04-02 | 0 | 4 | zamknięta | TP | 47.0 |
| EURUSD | short | 2025-04-02 | 2025-04-02 | 0 | 4 | zamknięta | TP | 21.4 |
| EURUSD | short | 2025-04-03 | 2025-04-04 | 1 | 34 | zamknięta | TP | 40.6 |
| AUDUSD | short | 2025-04-03 | 2025-04-04 | 1 | 16 | zamknięta | TP | 28.1 |
| USDCHF | short | 2025-04-08 | 2025-04-08 | 0 | 2 | zamknięta | TP | 40.5 |
| EURGBP | short | 2025-04-09 | 2025-04-09 | 0 | 4 | zamknięta | TP | 25.8 |
| EURUSD | short | 2025-04-11 | 2025-04-11 | 0 | 7 | zamknięta | TP | 70.4 |
| USDJPY | short | 2025-04-23 | 2025-04-28 | 5 | 60 | zamknięta | czas | -70.2 |
| AUDUSD | short | 2025-04-30 | 2025-05-01 | 1 | 22 | zamknięta | TP | 19.0 |
| EURJPY | short | 2025-05-01 | 2025-05-05 | 4 | 54 | zamknięta | TP | 44.6 |
| USDCHF | short | 2025-05-01 | 2025-05-01 | 0 | 5 | zamknięta | TP | 27.6 |
| USDJPY | short | 2025-05-01 | 2025-05-02 | 1 | 16 | zamknięta | TP | 52.5 |
| EURGBP | short | 2025-05-02 | 2025-05-02 | 0 | 3 | zamknięta | TP | 15.1 |
| EURUSD | short | 2025-05-02 | 2025-05-02 | 0 | 1 | zamknięta | TP | 31.9 |
| GBPUSD | short | 2025-05-06 | 2025-05-06 | 0 | 2 | zamknięta | TP | 27.1 |
| GBPUSD | short | 2025-05-08 | 2025-05-08 | 0 | 3 | zamknięta | TP | 37.6 |
| USDCAD | short | 2025-05-12 | 2025-05-13 | 2 | 38 | zamknięta | TP | 29.9 |
| USDCHF | short | 2025-05-12 | 2025-05-14 | 2 | 47 | zamknięta | TP | 34.3 |
| USDJPY | short | 2025-05-12 | 2025-05-14 | 2 | 41 | zamknięta | TP | 60.9 |
| GBPUSD | short | 2025-05-19 | 2025-05-19 | 0 | 4 | zamknięta | TP | 25.7 |
| EURJPY | short | 2025-05-27 | 2025-05-29 | 2 | 60 | zamknięta | czas | -84.1 |
| EURUSD | short | 2025-05-29 | 2025-05-30 | 1 | 24 | zamknięta | TP | 30.3 |
| GBPUSD | short | 2025-05-29 | 2025-05-30 | 1 | 17 | zamknięta | TP | 26.3 |
| AUDUSD | short | 2025-05-30 | 2025-06-04 | 5 | 60 | zamknięta | czas | -25.6 |
| EURJPY | short | 2025-05-30 | 2025-06-02 | 2 | 7 | zamknięta | TP | 39.6 |
| EURUSD | short | 2025-05-30 | 2025-06-04 | 5 | 60 | zamknięta | czas | -17.7 |
| EURUSD | short | 2025-06-04 | 2025-06-06 | 2 | 47 | zamknięta | TP | 21.5 |
| GBPUSD | short | 2025-06-04 | 2025-06-05 | 0 | 11 | zamknięta | TP | 24.9 |
| EURJPY | short | 2025-06-11 | 2025-06-11 | 0 | 4 | zamknięta | TP | 33.8 |
| EURGBP | short | 2025-06-12 | 2025-06-12 | 0 | 13 | zamknięta | TP | 11.7 |
| EURGBP | short | 2025-06-27 | 2025-07-02 | 5 | 60 | zamknięta | czas | -39.9 |
| EURGBP | short | 2025-07-02 | 2025-07-02 | 0 | 6 | zamknięta | TP | 18.3 |
| USDJPY | short | 2025-07-03 | 2025-07-04 | 1 | 16 | zamknięta | TP | 41.9 |
| GBPUSD | short | 2025-07-03 | 2025-07-07 | 4 | 38 | zamknięta | TP | 33.3 |
| EURJPY | short | 2025-07-03 | 2025-07-04 | 0 | 12 | zamknięta | TP | 34.1 |
| EURGBP | short | 2025-07-11 | 2025-07-15 | 4 | 60 | zamknięta | czas | -36.0 |
| EURJPY | short | 2025-07-14 | 2025-07-16 | 2 | 60 | zamknięta | czas | 2.1 |
| USDCHF | short | 2025-07-15 | 2025-07-16 | 1 | 24 | zamknięta | TP | 16.4 |
| USDJPY | short | 2025-07-15 | 2025-07-16 | 1 | 23 | zamknięta | TP | 34.5 |
| EURUSD | short | 2025-07-21 | 2025-07-22 | 1 | 21 | zamknięta | TP | 18.2 |
| EURUSD | short | 2025-07-24 | 2025-07-24 | 0 | 7 | zamknięta | TP | 20.7 |
| EURGBP | short | 2025-07-25 | 2025-07-28 | 3 | 22 | zamknięta | TP | 10.5 |
| USDCHF | short | 2025-07-30 | 2025-08-01 | 2 | 46 | zamknięta | TP | 19.6 |
| USDJPY | short | 2025-07-30 | 2025-07-30 | 0 | 4 | zamknięta | TP | 36.3 |
| USDJPY | short | 2025-07-31 | 2025-08-01 | 1 | 26 | zamknięta | TP | 45.5 |
| EURUSD | short | 2025-07-31 | 2025-08-01 | 1 | 18 | zamknięta | TP | 28.6 |
| GBPUSD | short | 2025-07-31 | 2025-08-01 | 1 | 17 | zamknięta | TP | 31.0 |
| AUDUSD | short | 2025-08-01 | 2025-08-01 | 0 | 4 | zamknięta | TP | 19.9 |
| GBPUSD | short | 2025-08-01 | 2025-08-01 | 0 | 4 | zamknięta | TP | 40.3 |
| EURUSD | short | 2025-08-01 | 2025-08-06 | 5 | 60 | zamknięta | czas | -30.4 |
| EURGBP | short | 2025-08-01 | 2025-08-04 | 3 | 20 | zamknięta | TP | 14.6 |
| GBPUSD | short | 2025-08-13 | 2025-08-14 | 1 | 27 | zamknięta | TP | 19.6 |
| EURJPY | short | 2025-08-20 | 2025-08-20 | 0 | 6 | zamknięta | TP | 34.7 |
| EURUSD | short | 2025-08-20 | 2025-08-21 | 1 | 17 | zamknięta | TP | 17.2 |
| EURJPY | short | 2025-08-21 | 2025-08-25 | 4 | 57 | zamknięta | TP | 29.8 |
| EURUSD | short | 2025-08-21 | 2025-08-21 | 0 | 5 | zamknięta | TP | 17.0 |
| AUDUSD | short | 2025-08-22 | 2025-08-27 | 5 | 60 | zamknięta | czas | -1.3 |
| EURGBP | short | 2025-08-22 | 2025-08-25 | 3 | 23 | zamknięta | TP | 11.5 |
| EURUSD | short | 2025-08-22 | 2025-08-25 | 3 | 17 | zamknięta | TP | 26.7 |
| EURUSD | short | 2025-08-29 | 2025-09-02 | 4 | 38 | zamknięta | TP | 18.0 |
| GBPUSD | short | 2025-08-29 | 2025-09-02 | 4 | 38 | zamknięta | TP | 19.9 |
| EURGBP | short | 2025-09-02 | 2025-09-04 | 2 | 48 | zamknięta | TP | 13.6 |
| USDCAD | short | 2025-09-02 | 2025-09-04 | 2 | 60 | zamknięta | czas | -50.7 |
| USDJPY | short | 2025-09-02 | 2025-09-02 | 0 | 6 | zamknięta | TP | 34.8 |
| GBPUSD | short | 2025-09-02 | 2025-09-03 | 1 | 17 | zamknięta | TP | 36.8 |
| AUDUSD | short | 2025-09-02 | 2025-09-05 | 2 | 60 | zamknięta | czas | -16.6 |
| EURUSD | short | 2025-09-02 | 2025-09-03 | 0 | 10 | zamknięta | TP | 26.1 |
| GBPUSD | short | 2025-09-03 | 2025-09-08 | 5 | 60 | zamknięta | czas | -87.6 |
| EURUSD | short | 2025-09-05 | 2025-09-05 | 0 | 5 | zamknięta | TP | 23.8 |
| USDCAD | short | 2025-09-05 | 2025-09-08 | 3 | 20 | zamknięta | TP | 26.2 |
| AUDUSD | short | 2025-09-10 | 2025-09-10 | 0 | 5 | zamknięta | TP | 12.0 |
| EURUSD | short | 2025-09-11 | 2025-09-12 | 1 | 22 | zamknięta | TP | 20.0 |
| USDJPY | short | 2025-09-12 | 2025-09-15 | 3 | 15 | zamknięta | TP | 27.7 |
| EURGBP | short | 2025-09-16 | 2025-09-17 | 1 | 29 | zamknięta | TP | 9.7 |
| EURUSD | short | 2025-09-16 | 2025-09-17 | 1 | 27 | zamknięta | TP | 19.2 |
| AUDUSD | short | 2025-09-18 | 2025-09-18 | 0 | 5 | zamknięta | TP | 14.4 |
| EURUSD | short | 2025-09-18 | 2025-09-18 | 0 | 4 | zamknięta | TP | 25.2 |
| USDCHF | short | 2025-09-18 | 2025-09-18 | 0 | 7 | zamknięta | TP | 20.2 |
| USDJPY | short | 2025-09-18 | 2025-09-19 | 0 | 13 | zamknięta | TP | 39.5 |
| EURGBP | short | 2025-09-19 | 2025-09-23 | 5 | 60 | zamknięta | czas | -24.2 |
| USDCHF | short | 2025-09-25 | 2025-09-29 | 3 | 32 | zamknięta | TP | 15.6 |
| GBPUSD | short | 2025-10-01 | 2025-10-01 | 0 | 1 | zamknięta | TP | 24.8 |
| EURJPY | short | 2025-10-06 | 2025-10-08 | 2 | 60 | zamknięta | czas | -207.7 |
| EURGBP | short | 2025-10-07 | 2025-10-07 | 0 | 2 | zamknięta | TP | 10.5 |
| GBPUSD | short | 2025-10-10 | 2025-10-14 | 4 | 36 | zamknięta | TP | 28.1 |
| EURGBP | short | 2025-10-14 | 2025-10-15 | 1 | 23 | zamknięta | TP | 11.1 |
| EURGBP | short | 2025-10-22 | 2025-10-22 | 0 | 3 | zamknięta | TP | 10.9 |
| EURGBP | short | 2025-10-23 | 2025-10-28 | 5 | 60 | zamknięta | czas | -13.9 |
| GBPUSD | short | 2025-10-24 | 2025-10-24 | 0 | 1 | zamknięta | TP | 21.7 |
| AUDUSD | short | 2025-10-27 | 2025-10-29 | 2 | 60 | zamknięta | czas | -15.1 |
| EURGBP | short | 2025-10-28 | 2025-10-31 | 2 | 60 | zamknięta | czas | -15.9 |
| EURUSD | short | 2025-10-30 | 2025-10-31 | 1 | 23 | zamknięta | TP | 23.4 |
| USDCAD | short | 2025-11-06 | 2025-11-06 | 0 | 2 | zamknięta | TP | 19.6 |
| EURGBP | short | 2025-11-07 | 2025-11-07 | 0 | 4 | zamknięta | TP | 9.4 |
| EURGBP | short | 2025-11-11 | 2025-11-13 | 2 | 60 | zamknięta | czas | -19.7 |
| EURUSD | short | 2025-11-11 | 2025-11-11 | 0 | 6 | zamknięta | TP | 15.4 |
| GBPUSD | short | 2025-11-11 | 2025-11-11 | 0 | 6 | zamknięta | TP | 23.1 |
| EURUSD | short | 2025-11-12 | 2025-11-17 | 4 | 60 | zamknięta | czas | -10.3 |
| GBPUSD | short | 2025-11-12 | 2025-11-13 | 1 | 15 | zamknięta | TP | 23.6 |
| AUDUSD | short | 2025-11-13 | 2025-11-13 | 0 | 3 | zamknięta | TP | 9.9 |
| GBPUSD | short | 2025-11-13 | 2025-11-14 | 0 | 10 | zamknięta | TP | 24.9 |
| GBPUSD | short | 2025-11-14 | 2025-11-14 | 0 | 2 | zamknięta | TP | 33.4 |
| GBPUSD | short | 2025-11-20 | 2025-11-20 | 0 | 2 | zamknięta | TP | 25.4 |
| GBPUSD | short | 2025-11-21 | 2025-11-26 | 5 | 60 | zamknięta | czas | -114.3 |
| EURUSD | short | 2025-11-26 | 2025-11-28 | 2 | 40 | zamknięta | TP | 20.8 |
| AUDUSD | short | 2025-11-28 | 2025-12-01 | 2 | 9 | zamknięta | TP | 8.6 |
| EURUSD | short | 2025-11-28 | 2025-12-03 | 5 | 60 | zamknięta | czas | -45.5 |
| USDJPY | short | 2025-12-09 | 2025-12-10 | 1 | 22 | zamknięta | TP | 30.6 |
| EURJPY | short | 2025-12-11 | 2025-12-15 | 4 | 36 | zamknięta | TP | 33.7 |
| EURGBP | short | 2025-12-17 | 2025-12-17 | 0 | 6 | zamknięta | TP | 13.1 |
| GBPUSD | short | 2025-12-17 | 2025-12-18 | 1 | 16 | zamknięta | TP | 26.0 |
| AUDUSD | short | 2025-12-18 | 2025-12-18 | 0 | 1 | zamknięta | TP | 10.1 |
| GBPUSD | short | 2025-12-18 | 2025-12-18 | 0 | 1 | zamknięta | TP | 25.7 |
| USDJPY | short | 2026-01-09 | 2026-01-12 | 2 | 8 | zamknięta | TP | 31.9 |
| EURJPY | short | 2026-01-20 | 2026-01-22 | 2 | 60 | zamknięta | czas | -126.7 |
| GBPUSD | short | 2026-01-20 | 2026-01-20 | 0 | 3 | zamknięta | TP | 19.2 |
| EURGBP | short | 2026-01-20 | 2026-01-22 | 2 | 44 | zamknięta | TP | 13.4 |
| AUDUSD | short | 2026-01-21 | 2026-01-21 | 0 | 2 | zamknięta | TP | 11.3 |
| EURGBP | short | 2026-01-22 | 2026-01-22 | 0 | 3 | zamknięta | TP | 12.5 |
| AUDUSD | short | 2026-01-26 | 2026-01-26 | 0 | 6 | zamknięta | TP | 14.3 |
| EURUSD | short | 2026-01-26 | 2026-01-27 | 1 | 16 | zamknięta | TP | 24.9 |
| GBPUSD | short | 2026-01-26 | 2026-01-27 | 1 | 16 | zamknięta | TP | 25.4 |
| EURUSD | short | 2026-01-27 | 2026-01-30 | 2 | 60 | zamknięta | czas | 6.2 |
| AUDUSD | short | 2026-02-03 | 2026-02-03 | 0 | 1 | zamknięta | TP | 20.8 |
| GBPUSD | short | 2026-02-03 | 2026-02-03 | 0 | 3 | zamknięta | TP | 21.8 |
| EURGBP | short | 2026-02-05 | 2026-02-05 | 0 | 6 | zamknięta | TP | 17.9 |
| AUDUSD | short | 2026-02-20 | 2026-02-23 | 3 | 18 | zamknięta | TP | 18.8 |
| EURJPY | short | 2026-02-24 | 2026-02-25 | 1 | 18 | zamknięta | TP | 43.0 |
| USDJPY | short | 2026-02-24 | 2026-02-25 | 1 | 18 | zamknięta | TP | 44.9 |
| AUDUSD | short | 2026-02-27 | 2026-03-02 | 2 | 6 | zamknięta | TP | 15.8 |
| USDCHF | short | 2026-03-02 | 2026-03-05 | 2 | 60 | zamknięta | czas | -18.2 |
| USDCHF | short | 2026-03-18 | 2026-03-19 | 1 | 30 | zamknięta | TP | 14.2 |
| USDJPY | short | 2026-03-18 | 2026-03-19 | 1 | 18 | zamknięta | TP | 28.1 |
| EURJPY | short | 2026-03-19 | 2026-03-19 | 0 | 3 | zamknięta | TP | 39.3 |
| GBPUSD | short | 2026-03-19 | 2026-03-20 | 1 | 23 | zamknięta | TP | 34.8 |
| EURGBP | short | 2026-03-20 | 2026-03-20 | 0 | 2 | zamknięta | TP | 12.9 |
| EURUSD | short | 2026-03-23 | 2026-03-26 | 2 | 60 | zamknięta | czas | 28.6 |
| GBPUSD | short | 2026-03-23 | 2026-03-24 | 1 | 28 | zamknięta | TP | 54.6 |
| AUDUSD | short | 2026-03-31 | 2026-03-31 | 0 | 2 | zamknięta | TP | 18.0 |
| EURUSD | short | 2026-03-31 | 2026-04-03 | 2 | 60 | zamknięta | czas | -15.5 |
| USDCHF | short | 2026-03-31 | 2026-03-31 | 0 | 1 | zamknięta | TP | 19.1 |
| EURGBP | short | 2026-03-31 | 2026-04-01 | 1 | 18 | zamknięta | TP | 15.1 |
| AUDUSD | short | 2026-04-01 | 2026-04-02 | 1 | 18 | zamknięta | TP | 20.6 |
| EURUSD | short | 2026-04-06 | 2026-04-06 | 0 | 7 | zamknięta | TP | 15.8 |
| GBPUSD | short | 2026-04-06 | 2026-04-06 | 0 | 7 | zamknięta | TP | 18.6 |
| AUDUSD | short | 2026-04-07 | 2026-04-07 | 0 | 1 | zamknięta | TP | 12.2 |
| EURUSD | short | 2026-04-07 | 2026-04-09 | 2 | 60 | zamknięta | czas | -139.0 |
| GBPUSD | short | 2026-04-07 | 2026-04-07 | 0 | 1 | zamknięta | TP | 21.6 |
| EURUSD | short | 2026-04-17 | 2026-04-17 | 0 | 1 | zamknięta | TP | 15.5 |
| GBPUSD | short | 2026-04-17 | 2026-04-17 | 0 | 3 | zamknięta | TP | 23.0 |
| AUDUSD | short | 2026-04-17 | 2026-04-17 | 0 | 1 | zamknięta | TP | 13.6 |
| USDCHF | short | 2026-04-28 | 2026-04-30 | 2 | 49 | zamknięta | TP | 13.5 |
| GBPUSD | short | 2026-05-06 | 2026-05-06 | 0 | 4 | zamknięta | TP | 21.1 |
| EURUSD | short | 2026-05-06 | 2026-05-06 | 0 | 2 | zamknięta | TP | 20.8 |
| USDCAD | short | 2026-05-08 | 2026-05-11 | 3 | 16 | zamknięta | TP | 23.2 |
| GBPUSD | short | 2026-05-13 | 2026-05-14 | 1 | 23 | zamknięta | TP | 22.2 |
| GBPUSD | short | 2026-05-18 | 2026-05-20 | 2 | 60 | zamknięta | czas | -84.2 |
| AUDUSD | short | 2026-05-18 | 2026-05-18 | 0 | 2 | zamknięta | TP | 16.7 |
| AUDUSD | short | 2026-05-20 | 2026-05-21 | 0 | 10 | zamknięta | TP | 16.6 |
| USDCHF | short | 2026-05-25 | 2026-05-28 | 2 | 60 | zamknięta | czas | -56.9 |
| GBPUSD | short | 2026-05-29 | 2026-06-01 | 2 | 6 | zamknięta | TP | 19.3 |
| EURUSD | short | 2026-05-29 | 2026-06-01 | 2 | 5 | zamknięta | TP | 16.3 |
| USDCHF | short | 2026-06-01 | 2026-06-01 | 0 | 7 | zamknięta | TP | 15.5 |
| USDJPY | short | 2026-06-01 | 2026-06-01 | 0 | 1 | zamknięta | TP | 12.3 |
| USDJPY | short | 2026-06-05 | 2026-06-08 | 3 | 17 | zamknięta | TP | 18.2 |
| EURGBP | short | 2026-06-18 | 2026-06-18 | 0 | 2 | zamknięta | TP | 7.7 |
| GBPUSD | short | 2026-06-19 | 2026-06-22 | 2 | 11 | zamknięta | TP | 24.7 |
| EURJPY | short | 2026-06-26 | 2026-06-26 | 0 | 1 | zamknięta | TP | 29.0 |
| EURUSD | short | 2026-06-26 | 2026-06-26 | 0 | 1 | zamknięta | TP | 18.5 |
| AUDUSD | short | 2026-06-30 | 2026-07-01 | 0 | 10 | zamknięta | TP | 12.4 |
| EURJPY | short | 2026-06-30 | 2026-07-01 | 1 | 18 | zamknięta | TP | 34.2 |
| GBPUSD | short | 2026-06-30 | 2026-07-01 | 0 | 12 | zamknięta | TP | 21.3 |
| EURUSD | short | 2026-07-01 | 2026-07-01 | 0 | 6 | zamknięta | TP | 19.1 |
| AUDUSD | short | 2026-07-02 | 2026-07-02 | 0 | 2 | zamknięta | TP | 9.8 |
| GBPUSD | short | 2026-07-02 | 2026-07-02 | 0 | 2 | zamknięta | TP | 20.5 |
| EURUSD | short | 2026-07-02 | 2026-07-02 | 0 | 6 | zamknięta | TP | 21.4 |
| AUDUSD | short | 2026-07-02 | 2026-07-02 | 0 | 5 | zamknięta | TP | 16.7 |
| GBPUSD | short | 2026-07-02 | 2026-07-06 | 4 | 38 | zamknięta | TP | 29.6 |
| AUDUSD | short | 2026-07-15 | 2026-07-15 | 0 | 3 | zamknięta | TP | 1.7 |
| EURUSD | short | 2026-07-15 | 2026-07-17 | 2 | 43 | zamknięta | TP | 4.8 |
| USDCHF | short | 2026-07-16 | 2026-07-17 | 1 | 19 | zamknięta | TP | 11.4 |
| EURGBP | short | 2026-07-20 | 2026-07-20 | 0 | 5 | zamknięta | TP | 7.4 |
| USDJPY | short | 2026-07-23 | 2026-07-24 | 1 | 17 | zamknięta | TP | 20.1 |
| USDCHF | short | 2026-07-27 | 2026-07-29 | 2 | 50 | zamknięta | TP | 14.3 |
| EURGBP | short | 2026-07-28 | 2026-07-30 | 2 | 54 | zamknięta | TP | 8.0 |
| EURJPY | short | 2026-07-28 | 2026-07-29 | 0 | 13 | zamknięta | TP | 19.3 |
| AUDUSD | short | 2026-07-28 | 2026-07-28 | 0 | 6 | zamknięta | TP | 9.5 |
| EURUSD | short | 2026-07-28 | 2026-07-28 | 0 | 5 | zamknięta | TP | 13.2 |
| GBPUSD | short | 2026-07-30 | 2026-08-04 | 5 | 60 | zamknięta | czas | -40.7 |
| AUDUSD | short | 2026-07-30 | 2026-08-03 | 4 | 45 | zamknięta | TP | 17.6 |
| EURJPY | short | 2026-07-31 | 2026-07-31 | 0 | 3 | zamknięta | TP | 91.1 |
| USDJPY | short | 2026-07-31 | 2026-07-31 | 0 | 4 | zamknięta | TP | 93.7 |
| USDCHF | short | 2026-08-06 | 2026-08-07 | 1 | 17 | zamknięta | TP | 15.0 |
| EURUSD | short | 2026-08-07 | 2026-08-10 | 3 | 26 | zamknięta | TP | 13.2 |
| GBPUSD | short | 2026-08-07 | 2026-08-12 | 5 | 60 | zamknięta | czas | -17.9 |
| AUDUSD | short | 2026-08-12 | 2026-08-12 | 0 | 1 | zamknięta | TP | 8.0 |
| GBPUSD | short | 2026-08-19 | 2026-08-24 | 5 | 60 | zamknięta | czas | -38.6 |
| EURGBP | short | 2026-08-31 | 2026-09-02 | 2 | 60 | zamknięta | czas | -29.4 |
| USDCHF | short | 2026-09-01 | 2026-09-03 | 2 | 39 | zamknięta | TP | 12.4 |
| AUDUSD | short | 2026-09-02 | 2026-09-07 | 5 | 60 | zamknięta | czas | -38.9 |
| GBPUSD | short | 2026-09-02 | 2026-09-02 | 0 | 5 | zamknięta | TP | 17.4 |
| USDCAD | short | 2026-09-04 | 2026-09-04 | 0 | 6 | zamknięta | TP | 27.1 |
| EURUSD | short | 2026-09-09 | 2026-09-09 | 0 | 3 | zamknięta | TP | 10.7 |
| USDCHF | short | 2026-09-09 | 2026-09-14 | 5 | 60 | zamknięta | czas | -91.9 |
| EURUSD | short | 2026-09-10 | 2026-09-10 | 0 | 4 | zamknięta | TP | 14.0 |
| USDCAD | short | 2026-09-14 | 2026-09-14 | 0 | 2 | zamknięta | TP | 21.4 |
| EURUSD | short | 2026-09-17 | 2026-09-18 | 1 | 21 | zamknięta | TP | 14.3 |
| EURGBP | short | 2026-09-17 | 2026-09-17 | 0 | 5 | zamknięta | TP | 10.4 |
| EURJPY | short | 2026-09-18 | 2026-09-18 | 0 | 4 | zamknięta | TP | 56.0 |
| USDJPY | short | 2026-09-18 | 2026-09-18 | 0 | 4 | zamknięta | TP | 51.0 |
| USDCHF | short | 2026-09-24 | 2026-09-29 | 5 | 60 | zamknięta | czas | -48.4 |
| EURJPY | short | 2026-09-28 | 2026-09-29 | 1 | 16 | zamknięta | TP | 41.2 |
| GBPUSD | short | 2026-10-01 | 2026-10-01 | 0 | 3 | zamknięta | TP | 24.7 |
| AUDUSD | short | 2026-10-02 | 2026-10-02 | 0 | 1 | zamknięta | TP | 12.8 |
| EURJPY | short | 2026-10-02 | 2026-10-05 | 2 | 9 | zamknięta | TP | 49.2 |
| EURUSD | short | 2026-10-06 | 2026-10-07 | 1 | 21 | zamknięta | TP | 18.9 |
| GBPUSD | short | 2026-10-06 | 2026-10-07 | 1 | 14 | zamknięta | TP | 18.7 |
| USDCAD | short | 2026-10-09 | 2026-10-12 | 3 | 15 | zamknięta | TP | 25.2 |
| USDCAD | short | 2026-10-14 | 2026-10-14 | 0 | 3 | zamknięta | TP | 25.7 |
| USDJPY | short | 2026-10-14 | 2026-10-14 | 0 | 3 | zamknięta | TP | 21.7 |
| USDCHF | short | 2026-10-14 | 2026-10-14 | 0 | 2 | zamknięta | TP | 13.5 |
| EURGBP | short | 2026-10-14 | 2026-10-15 | 1 | 27 | zamknięta | TP | 7.8 |
| USDJPY | short | 2026-10-15 | 2026-10-16 | 1 | 21 | zamknięta | TP | 35.9 |
| GBPUSD | short | 2026-10-16 | 2026-10-16 | 0 | 1 | zamknięta | TP | 20.2 |
| EURUSD | short | 2026-10-19 | 2026-10-21 | 2 | 60 | zamknięta | czas | -26.1 |
| GBPUSD | short | 2026-10-20 | 2026-10-21 | 1 | 16 | zamknięta | TP | 20.2 |
| USDCAD | short | 2026-10-26 | 2026-10-26 | 0 | 2 | zamknięta | TP | 21.2 |
| GBPUSD | short | 2026-10-29 | 2026-11-03 | 5 | 60 | zamknięta | czas | -51.6 |
| AUDUSD | short | 2026-11-02 | 2026-11-02 | 0 | 3 | zamknięta | TP | 10.6 |
| USDCAD | short | 2026-11-06 | 2026-11-11 | 5 | 60 | zamknięta | czas | -103.3 |
| USDCHF | short | 2026-11-09 | 2026-11-09 | 0 | 3 | zamknięta | TP | 16.8 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 10.56 pips/transakcję, percentyl **100.0** (losowe: 5%=-6.89, mediana=-1.86, 95%=2.84).

- **Deflated Sharpe Ratio**: 0.681 (Sharpe na transakcję 0.223, próg przy 5 próbach 0.172).

- **PBO** (CSCV, 16 bloków, 5 wariantów): 0.162 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 172 transakcji, śr. 8.91 pips, 0.52 R.

- **Bootstrap 95%** średnich pipsów: całość [5.88; 14.82], OOS [2.33; 17.14].

- **Spread**: ×1 10.56, ×1,5 9.79, ×2 9.02 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 1.6 nocy na transakcję, 64% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 9.78, 1 pips: 9.00 pips/transakcję.

## Forward test od zamrożenia (W4, D-056)

- Zamrożona 2026-11-10; oceniany wariant: ATR14 TP 1.5× SL 0× max 60 (zamrożony, nie ranking); oczekiwanie sprzed zamrożenia: 10.56 pips / 0.52 R na transakcję (283 transakcji).
- Jeszcze żadnej transakcji od zamrożenia.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """FX-POWRÓT v2 (pomysł z 20.10.2026, reguły z IA4 sekcja 7b). Po gwałtownym impulsie w górę (zamknięcie ≥ 2 × ATR100
wyżej niż poprzednie) kurs często cofa się w stronę ceny sprzed impulsu. Pierwsza czerwona świeca w ciągu 3 świec
po impulsie pokazuje, że kupujący się wyczerpali — short z celem w połowie drogi od szczytu do bazy, bez stopu,
limit 60 świec.
Różnice wobec oryginału (ograniczenia IA5): 8 par zamiast 10; warunek „open wejścia ≥ baza + 0,5 ATR” sprawdzany na
zamknięciu świecy sygnału (open następnej nie jest znany w chwili sygnału); TP jako poziom ceny P − ½(P − B) silnik
na razie nie obsługuje — wyjścia przybliżone przez TP w wielokrotnościach ATR14 (patrz EXITS)."""

import numpy as np

HOURS = False   # okno z reguł strategii: świeca sygnału zaczyna się 07–16 UTC (zamiast okna 07–17 czasu polskiego)

# Bez SL (jak w oryginale), limit 60 świec. Wariant „czas” = trzymanie do 60. świecy; warianty ATR = przybliżenie
# celu „połowa drogi powrotu” (impuls ≥ 2 × ATR100 ≈ 3–4 × ATR14, połowa drogi ≈ 1–2 × ATR14).
EXITS = [{"kind": "time", "n": 60, "cap": 60}] + [{"kind": "atr", "n": 14, "tp": tp, "cap": 60} for tp in (1.0, 1.5, 2.0, 3.0)]

SPREAD = {"EURUSD": 0.9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7, "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0,
          "EURJPY": 2.1}


def signals(df, p, ind):
    pair = df.attrs.get("pair", "")
    pip = 0.01 if "JPY" in pair else 0.0001
    spread = SPREAD.get(pair, 2.0) * pip
    o, h, c = df.open.to_numpy(), df.high.to_numpy(), df.close.to_numpy()
    atr = ind.atr(df, 100).shift(1).to_numpy()          # ATR100 sprzed świecy
    hour = df.index.hour.to_numpy()                      # UTC
    n = len(c)
    out = np.zeros(n, np.int8)
    base, peak, last_imp, active = 0.0, 0.0, -1, False
    for t in range(1, n):
        a = atr[t]
        if np.isnan(a):
            continue
        if c[t] - c[t - 1] >= 2 * a:                     # świeca impulsu
            if not active:
                active, base, peak = True, c[t - 1], h[t]
            peak = max(peak, h[t])
            last_imp = t
            continue
        if not active:
            continue
        peak = max(peak, h[t])
        if c[t] <= base or t - last_imp > 3:             # impuls wygasł
            active = False
            continue
        if c[t] < o[t] and 7 <= hour[t] <= 16:           # pierwsza czerwona w ciągu 3 świec
            tp = peak - 0.5 * (peak - base)
            if c[t] >= base + 0.5 * a and c[t] - tp >= max(spread, 0.1 * a):
                out[t] = -1
            active = False                               # tylko pierwsza czerwona
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
