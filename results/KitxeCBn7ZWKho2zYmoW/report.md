# Raport strategii: D5

Run `20261112-222602` · silnik 0.13.0 · kod `77f49dd4e5bc80fd` · dane `31bac05a73648ddf`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -0.29 |
| percentyl benchmarku ≥ 95 | ✔ | 98.80 |
| PBO < 0,3 | ✘ | 0.42 |
| DSR ≥ 0,95 | ✘ | 0.69 |
| dodatni przy spreadzie ×1,5 | ✔ | 6.08 |

## Hipoteza

Poniedziałkowy powrót. Przed weekendem rynek pozbywa się ryzyka: kto jest po złej stronie ruchu, zamyka pozycje
do piątkowego zamknięcia i dopycha kurs dalej, niż uzasadniają to informacje. W poniedziałek ten wymuszony ruch się cofa.
Wejście: para rozciągnięta na zamknięciu piątku (RSI2 dziennych zamknięć z 16:00 w Nowym Jorku poniżej progu → kupno,
powyżej 100 − próg → sprzedaż), wejście w poniedziałek o 01:00 czasu Londynu (rynek w Tokio już otwarty), wyjście po czasie.
Efekt znaleziony na danych niezależnych od danych IA5 (świece dzienne 2003–2019 i świece godzinowe brokera 2012–2022);
w inne dni tygodnia go nie ma. Lista wariantów ustalona przed pierwszym policzeniem na świecach Yahoo H1 (research/rynek/).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-12; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-10, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 9** (3 wejścia × 3 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.2 (przerwa w dostępie do danych), 2.4 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 30 świecach | prog=15 | 218 | 0.41 | 9.59 | 51.8 | 81 | -0.11 | -0.29 |
| 2 | po 30 świecach | prog=20 | 282 | 0.41 | 9.72 | 52.1 | 100 | -0.05 | -1.42 |
| 3 | po 30 świecach | prog=10 | 159 | 0.30 | 7.67 | 48.4 | 59 | -0.05 | -0.12 |
| 4 | po 20 świecach | prog=20 | 282 | 0.15 | 4.24 | 51.8 | 100 | 0.13 | 0.31 |
| 5 | po 20 świecach | prog=15 | 218 | 0.15 | 3.26 | 51.8 | 81 | 0.06 | 0.63 |
| 6 | po 12 świecach | prog=15 | 218 | -0.01 | -0.45 | 51.8 | 81 | -0.14 | -2.37 |
| 7 | po 20 świecach | prog=10 | 159 | -0.02 | -0.25 | 50.3 | 59 | 0.11 | -0.14 |
| 8 | po 12 świecach | prog=20 | 282 | -0.03 | 0.15 | 51.8 | 100 | -0.12 | -2.88 |
| 9 | po 12 świecach | prog=10 | 159 | -0.11 | -1.66 | 52.2 | 59 | 0.04 | -2.40 |

## Najlepszy wariant IS: po 30 świecach (prog=15)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 28 | 7.9 | 220.8 | 50.0 |
| EURGBP | 40 | -3.8 | -153.9 | 32.5 |
| EURJPY | 38 | 18.8 | 715.5 | 50.0 |
| EURUSD | 37 | 6.0 | 221.1 | 59.5 |
| GBPUSD | 38 | 6.1 | 232.4 | 57.9 |
| USDCAD | 53 | 8.0 | 425.7 | 54.7 |
| USDCHF | 36 | -3.8 | -135.9 | 50.0 |
| USDJPY | 29 | 18.7 | 542.2 | 55.2 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 28 | 7.5 | 211.2 | 46.4 |
| 2025 | 139 | 12.7 | 1 762.4 | 54.0 |
| 2026 | 132 | 0.7 | 94.4 | 49.2 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 218 | 9.6 | 2 091.1 | 51.8 |
| OOS | 81 | -0.3 | -23.1 | 49.4 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 12 281 | 22.8 | 10.7 | -9.3 | -10.2 | 0.85 | 0 |
| 10.0% | 14 762 | 47.6 | 21.3 | -17.9 | -19.5 | 0.85 | 0 |
| 15.0% | 17 314 | 73.1 | 31.3 | -26.7 | -28.5 | 0.86 | 10 |
| 20.0% | 18 651 | 86.5 | 36.2 | -35.8 | -37.8 | 0.81 | 21 |
| 30.0% | 14 400 | 44.0 | 19.8 | -48.1 | -50.5 | 0.52 | 79 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-10): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **299**, otwarte: **0** (razem 299).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 299 | 1 | 1 | 1 | 1 | 1 | 6.9 | 2 068 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 299 | 1 | 1 | 1 | 1 | 1 | 6.9 | 2 068 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDCAD | short | 2024-11-04 | 2024-11-05 | 1 | 30 | zamknięta | czas | 21.0 |
| EURGBP | long | 2024-11-11 | 2024-11-12 | 1 | 30 | zamknięta | czas | -8.9 |
| EURJPY | long | 2024-11-11 | 2024-11-12 | 1 | 30 | zamknięta | czas | -60.7 |
| EURJPY | long | 2024-11-18 | 2024-11-19 | 1 | 30 | zamknięta | czas | 91.0 |
| EURUSD | long | 2024-11-18 | 2024-11-19 | 1 | 30 | zamknięta | czas | 46.1 |
| GBPUSD | long | 2024-11-18 | 2024-11-19 | 1 | 30 | zamknięta | czas | 37.3 |
| USDCAD | short | 2024-11-18 | 2024-11-19 | 1 | 30 | zamknięta | czas | 58.9 |
| EURGBP | long | 2024-11-25 | 2024-11-26 | 1 | 30 | zamknięta | czas | 26.8 |
| EURJPY | long | 2024-11-25 | 2024-11-26 | 1 | 30 | zamknięta | czas | -26.3 |
| EURUSD | long | 2024-11-25 | 2024-11-26 | 1 | 30 | zamknięta | czas | -6.4 |
| GBPUSD | long | 2024-11-25 | 2024-11-26 | 1 | 30 | zamknięta | czas | -50.0 |
| USDCHF | short | 2024-11-25 | 2024-11-26 | 1 | 30 | zamknięta | czas | 30.4 |
| AUDUSD | short | 2024-12-02 | 2024-12-03 | 1 | 30 | zamknięta | czas | 23.2 |
| EURGBP | long | 2024-12-02 | 2024-12-03 | 1 | 30 | zamknięta | czas | -11.0 |
| EURJPY | long | 2024-12-02 | 2024-12-03 | 1 | 30 | zamknięta | czas | -84.3 |
| GBPUSD | short | 2024-12-02 | 2024-12-03 | 1 | 30 | zamknięta | czas | 43.3 |
| USDJPY | long | 2024-12-02 | 2024-12-03 | 1 | 30 | zamknięta | czas | -10.8 |
| AUDUSD | long | 2024-12-09 | 2024-12-10 | 1 | 30 | zamknięta | czas | 2.8 |
| USDCAD | short | 2024-12-09 | 2024-12-10 | 1 | 30 | zamknięta | czas | -15.5 |
| AUDUSD | long | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | -18.3 |
| EURGBP | short | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | 36.8 |
| EURJPY | short | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | -18.6 |
| GBPUSD | long | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | 38.8 |
| USDCAD | short | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | -41.4 |
| USDCHF | short | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | -42.1 |
| USDJPY | short | 2024-12-16 | 2024-12-17 | 1 | 30 | zamknięta | czas | -34.0 |
| AUDUSD | long | 2024-12-30 | 2024-12-31 | 1 | 30 | zamknięta | czas | -18.0 |
| EURJPY | short | 2024-12-30 | 2024-12-31 | 1 | 30 | zamknięta | czas | 201.1 |
| USDCAD | short | 2025-01-06 | 2025-01-07 | 1 | 30 | zamknięta | czas | 110.2 |
| AUDUSD | long | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | 34.7 |
| EURGBP | short | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | -1.8 |
| EURJPY | long | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | -17.5 |
| EURUSD | long | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | 8.6 |
| GBPUSD | long | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | 10.0 |
| USDCAD | short | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | 45.8 |
| USDCHF | short | 2025-01-13 | 2025-01-14 | 1 | 30 | zamknięta | czas | 13.4 |
| USDCAD | short | 2025-01-20 | 2025-01-21 | 1 | 30 | zamknięta | czas | 21.0 |
| AUDUSD | short | 2025-01-27 | 2025-01-28 | 1 | 30 | zamknięta | czas | 42.8 |
| EURGBP | long | 2025-01-27 | 2025-01-28 | 1 | 30 | zamknięta | czas | -20.0 |
| EURUSD | short | 2025-01-27 | 2025-01-28 | 1 | 30 | zamknięta | czas | 34.1 |
| GBPUSD | short | 2025-01-27 | 2025-01-28 | 1 | 30 | zamknięta | czas | 13.1 |
| AUDUSD | long | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | 79.2 |
| EURGBP | long | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | -30.7 |
| EURUSD | long | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | 74.0 |
| GBPUSD | long | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | 133.0 |
| USDCAD | short | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | 275.2 |
| USDCHF | short | 2025-02-03 | 2025-02-04 | 1 | 30 | zamknięta | czas | 38.1 |
| EURJPY | long | 2025-02-10 | 2025-02-11 | 1 | 30 | zamknięta | czas | -5.5 |
| USDCAD | long | 2025-02-10 | 2025-02-11 | 1 | 30 | zamknięta | czas | -4.7 |
| USDJPY | long | 2025-02-10 | 2025-02-11 | 1 | 30 | zamknięta | czas | 3.2 |
| AUDUSD | short | 2025-02-17 | 2025-02-18 | 1 | 30 | zamknięta | czas | -3.2 |
| EURUSD | short | 2025-02-17 | 2025-02-18 | 1 | 30 | zamknięta | czas | 28.8 |
| GBPUSD | short | 2025-02-17 | 2025-02-18 | 1 | 30 | zamknięta | czas | -18.6 |
| USDCAD | long | 2025-02-17 | 2025-02-18 | 1 | 30 | zamknięta | czas | 20.1 |
| USDCHF | long | 2025-02-17 | 2025-02-18 | 1 | 30 | zamknięta | czas | 23.2 |
| EURJPY | long | 2025-02-24 | 2025-02-25 | 1 | 30 | zamknięta | czas | 45.4 |
| USDCHF | long | 2025-02-24 | 2025-02-25 | 1 | 30 | zamknięta | czas | 4.0 |
| USDJPY | long | 2025-02-24 | 2025-02-25 | 1 | 30 | zamknięta | czas | 82.2 |
| AUDUSD | long | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | -8.7 |
| EURGBP | long | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | -3.7 |
| EURUSD | long | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | 74.5 |
| GBPUSD | long | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | 94.0 |
| USDCAD | short | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | -39.4 |
| USDCHF | short | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | 64.5 |
| USDJPY | short | 2025-03-03 | 2025-03-04 | 1 | 30 | zamknięta | czas | 99.5 |
| EURGBP | short | 2025-03-10 | 2025-03-11 | 1 | 30 | zamknięta | czas | -24.4 |
| EURUSD | short | 2025-03-10 | 2025-03-11 | 1 | 30 | zamknięta | czas | 7.4 |
| GBPUSD | short | 2025-03-10 | 2025-03-11 | 1 | 30 | zamknięta | czas | 45.7 |
| USDCHF | long | 2025-03-10 | 2025-03-11 | 1 | 30 | zamknięta | czas | 29.4 |
| USDCHF | short | 2025-03-17 | 2025-03-18 | 1 | 30 | zamknięta | czas | 33.4 |
| AUDUSD | long | 2025-03-24 | 2025-03-25 | 1 | 30 | zamknięta | czas | -7.4 |
| EURUSD | long | 2025-03-24 | 2025-03-25 | 1 | 30 | zamknięta | czas | -44.2 |
| GBPUSD | long | 2025-03-24 | 2025-03-25 | 1 | 30 | zamknięta | czas | -21.5 |
| AUDUSD | long | 2025-04-07 | 2025-04-08 | 1 | 30 | zamknięta | czas | 79.9 |
| EURGBP | short | 2025-04-07 | 2025-04-08 | 1 | 30 | zamknięta | czas | -74.7 |
| AUDUSD | short | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -45.3 |
| EURGBP | short | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | 70.9 |
| EURJPY | short | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | 56.0 |
| EURUSD | short | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -7.3 |
| GBPUSD | short | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -117.6 |
| USDCAD | long | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -5.1 |
| USDCHF | long | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -17.3 |
| USDJPY | long | 2025-04-14 | 2025-04-15 | 1 | 30 | zamknięta | czas | -63.4 |
| GBPUSD | short | 2025-04-21 | 2025-04-22 | 1 | 30 | zamknięta | czas | -99.6 |
| EURGBP | long | 2025-04-28 | 2025-04-29 | 1 | 30 | zamknięta | czas | -45.8 |
| EURJPY | short | 2025-04-28 | 2025-04-29 | 1 | 30 | zamknięta | czas | 98.9 |
| EURGBP | long | 2025-05-12 | 2025-05-13 | 1 | 30 | zamknięta | czas | -36.0 |
| USDCAD | short | 2025-05-12 | 2025-05-13 | 1 | 30 | zamknięta | czas | -36.5 |
| USDCHF | short | 2025-05-12 | 2025-05-13 | 1 | 30 | zamknięta | czas | -92.7 |
| EURGBP | long | 2025-05-19 | 2025-05-20 | 1 | 30 | zamknięta | czas | 2.8 |
| EURJPY | long | 2025-05-19 | 2025-05-20 | 1 | 30 | zamknięta | czas | -3.3 |
| EURJPY | long | 2025-05-26 | 2025-05-27 | 1 | 30 | zamknięta | czas | 52.7 |
| GBPUSD | short | 2025-05-26 | 2025-05-27 | 1 | 30 | zamknięta | czas | -15.3 |
| USDCAD | long | 2025-05-26 | 2025-05-27 | 1 | 30 | zamknięta | czas | 2.4 |
| USDCHF | long | 2025-05-26 | 2025-05-27 | 1 | 30 | zamknięta | czas | -9.1 |
| USDJPY | long | 2025-05-26 | 2025-05-27 | 1 | 30 | zamknięta | czas | 42.1 |
| EURGBP | short | 2025-06-02 | 2025-06-03 | 1 | 30 | zamknięta | czas | -18.2 |
| USDCAD | long | 2025-06-02 | 2025-06-03 | 1 | 30 | zamknięta | czas | 3.1 |
| EURJPY | short | 2025-06-09 | 2025-06-10 | 1 | 30 | zamknięta | czas | 15.2 |
| EURGBP | short | 2025-06-16 | 2025-06-17 | 1 | 30 | zamknięta | czas | -4.2 |
| EURJPY | short | 2025-06-16 | 2025-06-17 | 1 | 30 | zamknięta | czas | -42.6 |
| USDCAD | long | 2025-06-16 | 2025-06-17 | 1 | 30 | zamknięta | czas | -7.7 |
| USDCHF | long | 2025-06-16 | 2025-06-17 | 1 | 30 | zamknięta | czas | 11.2 |
| EURJPY | short | 2025-06-23 | 2025-06-24 | 1 | 30 | zamknięta | czas | -59.7 |
| USDCAD | short | 2025-06-23 | 2025-06-24 | 1 | 30 | zamknięta | czas | 20.8 |
| USDJPY | short | 2025-06-23 | 2025-06-24 | 1 | 30 | zamknięta | czas | 88.8 |
| EURUSD | short | 2025-06-30 | 2025-07-01 | 1 | 30 | zamknięta | czas | -59.0 |
| USDCHF | long | 2025-06-30 | 2025-07-01 | 1 | 30 | zamknięta | czas | -64.8 |
| EURGBP | short | 2025-07-14 | 2025-07-15 | 1 | 30 | zamknięta | czas | -40.1 |
| EURUSD | long | 2025-07-14 | 2025-07-15 | 1 | 30 | zamknięta | czas | 0.5 |
| GBPUSD | long | 2025-07-14 | 2025-07-15 | 1 | 30 | zamknięta | czas | -59.0 |
| USDJPY | short | 2025-07-14 | 2025-07-15 | 1 | 30 | zamknięta | czas | -29.1 |
| EURGBP | short | 2025-07-28 | 2025-07-29 | 1 | 30 | zamknięta | czas | 72.3 |
| EURJPY | short | 2025-07-28 | 2025-07-29 | 1 | 30 | zamknięta | czas | 206.1 |
| EURGBP | short | 2025-08-04 | 2025-08-05 | 1 | 30 | zamknięta | czas | 17.2 |
| AUDUSD | short | 2025-08-11 | 2025-08-12 | 1 | 30 | zamknięta | czas | 17.2 |
| EURJPY | short | 2025-08-11 | 2025-08-12 | 1 | 30 | zamknięta | czas | -31.4 |
| GBPUSD | short | 2025-08-11 | 2025-08-12 | 1 | 30 | zamknięta | czas | 16.7 |
| USDCAD | short | 2025-08-18 | 2025-08-19 | 1 | 30 | zamknięta | czas | 5.0 |
| AUDUSD | short | 2025-09-01 | 2025-09-02 | 1 | 30 | zamknięta | czas | 5.6 |
| EURJPY | short | 2025-09-01 | 2025-09-02 | 1 | 30 | zamknięta | czas | -101.4 |
| USDCAD | long | 2025-09-01 | 2025-09-02 | 1 | 30 | zamknięta | czas | 16.8 |
| USDCHF | long | 2025-09-01 | 2025-09-02 | 1 | 30 | zamknięta | czas | 8.7 |
| USDCAD | short | 2025-09-08 | 2025-09-09 | 1 | 30 | zamknięta | czas | 39.0 |
| USDCHF | long | 2025-09-08 | 2025-09-09 | 1 | 30 | zamknięta | czas | -76.3 |
| AUDUSD | long | 2025-09-22 | 2025-09-23 | 1 | 30 | zamknięta | czas | -2.6 |
| EURGBP | short | 2025-09-22 | 2025-09-23 | 1 | 30 | zamknięta | czas | -18.8 |
| GBPUSD | long | 2025-09-22 | 2025-09-23 | 1 | 30 | zamknięta | czas | 44.7 |
| EURJPY | short | 2025-09-29 | 2025-09-30 | 1 | 30 | zamknięta | czas | 87.5 |
| AUDUSD | long | 2025-10-13 | 2025-10-14 | 1 | 30 | zamknięta | czas | -32.4 |
| EURJPY | long | 2025-10-20 | 2025-10-21 | 1 | 30 | zamknięta | czas | 18.2 |
| GBPUSD | short | 2025-10-20 | 2025-10-21 | 1 | 30 | zamknięta | czas | 49.5 |
| USDCHF | long | 2025-10-20 | 2025-10-21 | 1 | 30 | zamknięta | czas | -3.8 |
| EURGBP | short | 2025-10-27 | 2025-10-28 | 1 | 30 | zamknięta | czas | 1.5 |
| EURJPY | short | 2025-10-27 | 2025-10-28 | 1 | 30 | zamknięta | czas | 67.3 |
| GBPUSD | long | 2025-10-27 | 2025-10-28 | 1 | 30 | zamknięta | czas | 28.6 |
| USDJPY | short | 2025-10-27 | 2025-10-28 | 1 | 30 | zamknięta | czas | 85.9 |
| EURUSD | long | 2025-11-03 | 2025-11-04 | 1 | 30 | zamknięta | czas | -3.6 |
| GBPUSD | long | 2025-11-03 | 2025-11-04 | 1 | 30 | zamknięta | czas | -11.3 |
| USDCAD | short | 2025-11-03 | 2025-11-04 | 1 | 30 | zamknięta | czas | -46.3 |
| USDCHF | short | 2025-11-03 | 2025-11-04 | 1 | 30 | zamknięta | czas | -27.7 |
| USDJPY | short | 2025-11-03 | 2025-11-04 | 1 | 30 | zamknięta | czas | 53.5 |
| EURUSD | short | 2025-11-10 | 2025-11-11 | 1 | 30 | zamknięta | czas | -0.9 |
| EURGBP | long | 2025-11-24 | 2025-11-25 | 1 | 30 | zamknięta | czas | -3.3 |
| EURUSD | long | 2025-11-24 | 2025-11-25 | 1 | 30 | zamknięta | czas | 11.0 |
| USDCHF | short | 2025-11-24 | 2025-11-25 | 1 | 30 | zamknięta | czas | -7.6 |
| AUDUSD | short | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | -15.0 |
| EURGBP | long | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | 19.0 |
| EURUSD | short | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | -7.6 |
| GBPUSD | short | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | 21.8 |
| USDCAD | long | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | 20.6 |
| USDCHF | long | 2025-12-01 | 2025-12-02 | 1 | 30 | zamknięta | czas | 9.5 |
| AUDUSD | short | 2025-12-08 | 2025-12-09 | 1 | 30 | zamknięta | czas | -4.3 |
| EURGBP | long | 2025-12-08 | 2025-12-09 | 1 | 30 | zamknięta | czas | -5.3 |
| USDCAD | long | 2025-12-08 | 2025-12-09 | 1 | 30 | zamknięta | czas | 27.3 |
| EURGBP | short | 2025-12-15 | 2025-12-16 | 1 | 30 | zamknięta | czas | -14.2 |
| EURJPY | short | 2025-12-15 | 2025-12-16 | 1 | 30 | zamknięta | czas | 90.2 |
| EURUSD | short | 2025-12-15 | 2025-12-16 | 1 | 30 | zamknięta | czas | -20.2 |
| USDCAD | long | 2025-12-15 | 2025-12-16 | 1 | 30 | zamknięta | czas | -1.0 |
| EURJPY | short | 2025-12-22 | 2025-12-23 | 1 | 30 | zamknięta | czas | 85.1 |
| EURUSD | long | 2025-12-22 | 2025-12-23 | 1 | 30 | zamknięta | czas | 52.9 |
| USDCAD | short | 2025-12-22 | 2025-12-23 | 1 | 30 | zamknięta | czas | 53.8 |
| USDJPY | short | 2025-12-22 | 2025-12-23 | 1 | 30 | zamknięta | czas | 142.6 |
| AUDUSD | short | 2025-12-29 | 2025-12-30 | 1 | 30 | zamknięta | czas | -3.1 |
| EURGBP | long | 2025-12-29 | 2025-12-30 | 1 | 30 | zamknięta | czas | -7.8 |
| GBPUSD | short | 2025-12-29 | 2025-12-30 | 1 | 30 | zamknięta | czas | -9.9 |
| USDCAD | long | 2025-12-29 | 2025-12-30 | 1 | 30 | zamknięta | czas | 14.4 |
| EURGBP | long | 2026-01-05 | 2026-01-06 | 1 | 30 | zamknięta | czas | -50.5 |
| EURUSD | long | 2026-01-05 | 2026-01-06 | 1 | 30 | zamknięta | czas | 32.1 |
| USDCAD | short | 2026-01-05 | 2026-01-06 | 1 | 30 | zamknięta | czas | -12.8 |
| USDCHF | short | 2026-01-05 | 2026-01-06 | 1 | 30 | zamknięta | czas | 14.2 |
| USDJPY | short | 2026-01-05 | 2026-01-06 | 1 | 30 | zamknięta | czas | 76.7 |
| EURUSD | long | 2026-01-12 | 2026-01-13 | 1 | 30 | zamknięta | czas | -7.7 |
| GBPUSD | long | 2026-01-12 | 2026-01-13 | 1 | 30 | zamknięta | czas | 34.7 |
| USDCAD | short | 2026-01-12 | 2026-01-13 | 1 | 30 | zamknięta | czas | 13.0 |
| USDCHF | short | 2026-01-12 | 2026-01-13 | 1 | 30 | zamknięta | czas | -3.7 |
| USDJPY | short | 2026-01-12 | 2026-01-13 | 1 | 30 | zamknięta | czas | -119.8 |
| EURJPY | long | 2026-01-19 | 2026-01-20 | 1 | 30 | zamknięta | czas | 164.9 |
| EURUSD | long | 2026-01-19 | 2026-01-20 | 1 | 30 | zamknięta | czas | 37.1 |
| USDCAD | short | 2026-01-19 | 2026-01-20 | 1 | 30 | zamknięta | czas | 34.1 |
| AUDUSD | short | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | 1.2 |
| EURGBP | long | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | -3.3 |
| EURUSD | short | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | -9.4 |
| GBPUSD | short | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | -13.1 |
| USDCAD | long | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | 44.4 |
| USDCHF | long | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | 0.0 |
| USDJPY | long | 2026-01-26 | 2026-01-27 | 1 | 30 | zamknięta | czas | -32.2 |
| EURJPY | short | 2026-02-09 | 2026-02-10 | 1 | 30 | zamknięta | czas | 59.3 |
| USDJPY | short | 2026-02-09 | 2026-02-10 | 1 | 30 | zamknięta | czas | 145.1 |
| USDJPY | long | 2026-02-16 | 2026-02-17 | 1 | 30 | zamknięta | czas | -15.3 |
| EURJPY | short | 2026-02-23 | 2026-02-24 | 1 | 30 | zamknięta | czas | -32.1 |
| USDJPY | short | 2026-02-23 | 2026-02-24 | 1 | 30 | zamknięta | czas | -92.8 |
| EURGBP | short | 2026-03-02 | 2026-03-03 | 1 | 30 | zamknięta | czas | 32.8 |
| USDCAD | long | 2026-03-02 | 2026-03-03 | 1 | 30 | zamknięta | czas | 17.2 |
| USDCHF | long | 2026-03-02 | 2026-03-03 | 1 | 30 | zamknięta | czas | 121.5 |
| EURGBP | long | 2026-03-09 | 2026-03-10 | 1 | 30 | zamknięta | czas | -12.9 |
| USDCAD | long | 2026-03-09 | 2026-03-10 | 1 | 30 | zamknięta | czas | -28.4 |
| AUDUSD | long | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | 53.3 |
| EURJPY | long | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | 46.8 |
| EURUSD | long | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | 25.4 |
| GBPUSD | long | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | 24.7 |
| USDCAD | short | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | 11.0 |
| USDCHF | short | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | -0.4 |
| USDJPY | short | 2026-03-16 | 2026-03-17 | 1 | 30 | zamknięta | czas | -5.6 |
| EURGBP | short | 2026-03-23 | 2026-03-24 | 1 | 30 | zamknięta | czas | 22.6 |
| AUDUSD | long | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | -2.5 |
| EURGBP | short | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | -3.0 |
| EURUSD | long | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | -29.9 |
| GBPUSD | long | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | -39.7 |
| USDCAD | short | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | -30.3 |
| USDCHF | short | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | 5.7 |
| USDJPY | short | 2026-03-30 | 2026-03-31 | 1 | 30 | zamknięta | czas | 60.1 |
| EURJPY | short | 2026-04-13 | 2026-04-14 | 1 | 30 | zamknięta | czas | -80.2 |
| EURUSD | short | 2026-04-13 | 2026-04-14 | 1 | 30 | zamknięta | czas | -88.9 |
| GBPUSD | short | 2026-04-13 | 2026-04-14 | 1 | 30 | zamknięta | czas | -123.0 |
| USDCHF | long | 2026-04-13 | 2026-04-14 | 1 | 30 | zamknięta | czas | -95.4 |
| EURJPY | long | 2026-04-20 | 2026-04-21 | 1 | 30 | zamknięta | czas | 31.1 |
| USDCAD | long | 2026-04-20 | 2026-04-21 | 1 | 30 | zamknięta | czas | -58.7 |
| EURUSD | short | 2026-05-11 | 2026-05-12 | 1 | 30 | zamknięta | czas | 4.6 |
| USDCAD | short | 2026-05-11 | 2026-05-12 | 1 | 30 | zamknięta | czas | -5.8 |
| AUDUSD | long | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 0.8 |
| EURGBP | short | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 48.9 |
| EURJPY | long | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 61.4 |
| EURUSD | long | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 26.2 |
| GBPUSD | long | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 104.8 |
| USDCAD | short | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 13.3 |
| USDCHF | short | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | 16.7 |
| USDJPY | short | 2026-05-18 | 2026-05-19 | 1 | 30 | zamknięta | czas | -16.7 |
| EURGBP | long | 2026-05-25 | 2026-05-26 | 1 | 30 | zamknięta | czas | -8.2 |
| USDCAD | short | 2026-05-25 | 2026-05-26 | 1 | 30 | zamknięta | czas | -13.5 |
| USDJPY | short | 2026-05-25 | 2026-05-26 | 1 | 30 | zamknięta | czas | -8.7 |
| EURJPY | short | 2026-06-01 | 2026-06-02 | 1 | 30 | zamknięta | czas | -27.8 |
| EURUSD | short | 2026-06-01 | 2026-06-02 | 1 | 30 | zamknięta | czas | 11.3 |
| USDCHF | long | 2026-06-01 | 2026-06-02 | 1 | 30 | zamknięta | czas | 42.7 |
| AUDUSD | long | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 13.7 |
| EURJPY | long | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 12.3 |
| EURUSD | long | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 20.4 |
| GBPUSD | long | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 24.5 |
| USDCAD | short | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 6.3 |
| USDJPY | short | 2026-06-08 | 2026-06-09 | 1 | 30 | zamknięta | czas | 16.9 |
| USDCAD | short | 2026-06-15 | 2026-06-16 | 1 | 30 | zamknięta | czas | -52.9 |
| USDCAD | short | 2026-06-22 | 2026-06-23 | 1 | 30 | zamknięta | czas | -1.6 |
| USDCHF | short | 2026-06-22 | 2026-06-23 | 1 | 30 | zamknięta | czas | -10.3 |
| EURGBP | long | 2026-07-06 | 2026-07-07 | 1 | 30 | zamknięta | czas | -26.6 |
| GBPUSD | short | 2026-07-06 | 2026-07-07 | 1 | 30 | zamknięta | czas | -33.7 |
| USDCAD | long | 2026-07-20 | 2026-07-21 | 1 | 30 | zamknięta | czas | 49.7 |
| EURUSD | long | 2026-07-27 | 2026-07-28 | 1 | 30 | zamknięta | czas | -30.7 |
| GBPUSD | long | 2026-07-27 | 2026-07-28 | 1 | 30 | zamknięta | czas | -66.1 |
| USDCHF | short | 2026-07-27 | 2026-07-28 | 1 | 30 | zamknięta | czas | -32.9 |
| USDJPY | short | 2026-07-27 | 2026-07-28 | 1 | 30 | zamknięta | czas | -13.1 |
| EURJPY | long | 2026-08-03 | 2026-08-04 | 1 | 30 | zamknięta | czas | -44.8 |
| EURUSD | short | 2026-08-03 | 2026-08-04 | 1 | 30 | zamknięta | czas | 32.3 |
| GBPUSD | short | 2026-08-03 | 2026-08-04 | 1 | 30 | zamknięta | czas | 63.0 |
| USDJPY | long | 2026-08-03 | 2026-08-04 | 1 | 30 | zamknięta | czas | 10.2 |
| GBPUSD | short | 2026-08-10 | 2026-08-11 | 1 | 30 | zamknięta | czas | -22.5 |
| USDCAD | long | 2026-08-10 | 2026-08-11 | 1 | 30 | zamknięta | czas | -29.2 |
| AUDUSD | short | 2026-08-17 | 2026-08-18 | 1 | 30 | zamknięta | czas | -13.3 |
| EURJPY | short | 2026-08-17 | 2026-08-18 | 1 | 30 | zamknięta | czas | -51.3 |
| EURUSD | short | 2026-08-17 | 2026-08-18 | 1 | 30 | zamknięta | czas | 1.8 |
| GBPUSD | short | 2026-08-17 | 2026-08-18 | 1 | 30 | zamknięta | czas | 10.8 |
| USDCAD | long | 2026-08-17 | 2026-08-18 | 1 | 30 | zamknięta | czas | -1.9 |
| AUDUSD | short | 2026-08-24 | 2026-08-25 | 1 | 30 | zamknięta | czas | 22.4 |
| EURUSD | short | 2026-08-24 | 2026-08-25 | 1 | 30 | zamknięta | czas | 29.1 |
| GBPUSD | short | 2026-08-24 | 2026-08-25 | 1 | 30 | zamknięta | czas | 29.9 |
| USDCAD | long | 2026-08-24 | 2026-08-25 | 1 | 30 | zamknięta | czas | 65.4 |
| EURUSD | long | 2026-08-31 | 2026-09-01 | 1 | 30 | zamknięta | czas | 17.9 |
| GBPUSD | long | 2026-08-31 | 2026-09-01 | 1 | 30 | zamknięta | czas | 4.7 |
| USDCHF | short | 2026-08-31 | 2026-09-01 | 1 | 30 | zamknięta | czas | -6.6 |
| USDJPY | short | 2026-08-31 | 2026-09-01 | 1 | 30 | zamknięta | czas | 22.6 |
| AUDUSD | short | 2026-09-07 | 2026-09-08 | 1 | 30 | zamknięta | czas | -12.6 |
| EURUSD | long | 2026-09-14 | 2026-09-15 | 1 | 30 | zamknięta | czas | -59.8 |
| USDCAD | short | 2026-09-14 | 2026-09-15 | 1 | 30 | zamknięta | czas | -45.5 |
| USDCHF | short | 2026-09-14 | 2026-09-15 | 1 | 30 | zamknięta | czas | -18.2 |
| EURJPY | short | 2026-09-21 | 2026-09-22 | 1 | 30 | zamknięta | czas | -44.3 |
| USDCAD | short | 2026-09-21 | 2026-09-22 | 1 | 30 | zamknięta | czas | -34.3 |
| USDJPY | short | 2026-09-21 | 2026-09-22 | 1 | 30 | zamknięta | czas | -48.6 |
| USDCAD | short | 2026-09-28 | 2026-09-29 | 1 | 30 | zamknięta | czas | -34.3 |
| USDCHF | short | 2026-09-28 | 2026-09-29 | 1 | 30 | zamknięta | czas | -35.9 |
| EURGBP | long | 2026-10-05 | 2026-10-06 | 1 | 30 | zamknięta | czas | -14.1 |
| EURJPY | long | 2026-10-05 | 2026-10-06 | 1 | 30 | zamknięta | czas | -29.2 |
| USDCAD | short | 2026-10-05 | 2026-10-06 | 1 | 30 | zamknięta | czas | -16.1 |
| EURGBP | long | 2026-10-12 | 2026-10-13 | 1 | 30 | zamknięta | czas | -13.9 |
| EURGBP | long | 2026-10-19 | 2026-10-20 | 1 | 30 | zamknięta | czas | 3.0 |
| USDCAD | long | 2026-10-19 | 2026-10-20 | 1 | 30 | zamknięta | czas | -42.6 |
| USDCHF | long | 2026-10-19 | 2026-10-20 | 1 | 30 | zamknięta | czas | 14.1 |
| USDJPY | long | 2026-10-19 | 2026-10-20 | 1 | 30 | zamknięta | czas | 35.7 |
| EURGBP | long | 2026-10-26 | 2026-10-27 | 1 | 30 | zamknięta | czas | -8.8 |
| EURJPY | long | 2026-10-26 | 2026-10-27 | 1 | 30 | zamknięta | czas | -14.0 |
| EURUSD | long | 2026-10-26 | 2026-10-27 | 1 | 30 | zamknięta | czas | -57.3 |
| USDCAD | long | 2026-10-26 | 2026-10-27 | 1 | 30 | zamknięta | czas | 17.8 |
| USDJPY | long | 2026-10-26 | 2026-10-27 | 1 | 30 | zamknięta | czas | 67.2 |
| EURGBP | long | 2026-11-02 | 2026-11-03 | 1 | 30 | zamknięta | czas | 1.7 |
| GBPUSD | short | 2026-11-02 | 2026-11-03 | 1 | 30 | zamknięta | czas | -23.1 |
| USDCAD | long | 2026-11-02 | 2026-11-03 | 1 | 30 | zamknięta | czas | 1.9 |
| USDCHF | long | 2026-11-02 | 2026-11-03 | 1 | 30 | zamknięta | czas | -71.8 |
| AUDUSD | long | 2026-11-09 | 2026-11-10 | 1 | 30 | zamknięta | czas | 30.7 |
| EURUSD | long | 2026-11-09 | 2026-11-10 | 1 | 30 | zamknięta | czas | 78.0 |
| GBPUSD | long | 2026-11-09 | 2026-11-10 | 1 | 30 | zamknięta | czas | 82.8 |
| USDCAD | short | 2026-11-09 | 2026-11-10 | 1 | 30 | zamknięta | czas | 1.7 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 6.92 pips/transakcję, percentyl **98.8** (losowe: 5%=-7.34, mediana=-1.65, 95%=4.04).

- **Deflated Sharpe Ratio**: 0.688 (Sharpe na transakcję 0.137, próg przy 9 próbach 0.104).

- **PBO** (CSCV, 16 bloków, 9 wariantów): 0.424 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 198 transakcji, śr. 3.84 pips, 0.18 R.

- **Bootstrap 95%** średnich pipsów: całość [1.48; 12.44], OOS [-7.97; 7.55].

- **Spread**: ×1 6.92, ×1,5 6.08, ×2 5.24 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 1.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 6.42, 1 pips: 5.92 pips/transakcję.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

import numpy as np
import pandas as pd

HYPOTHESIS = """Poniedziałkowy powrót. Przed weekendem rynek pozbywa się ryzyka: kto jest po złej stronie ruchu, zamyka pozycje
do piątkowego zamknięcia i dopycha kurs dalej, niż uzasadniają to informacje. W poniedziałek ten wymuszony ruch się cofa.
Wejście: para rozciągnięta na zamknięciu piątku (RSI2 dziennych zamknięć z 16:00 w Nowym Jorku poniżej progu → kupno,
powyżej 100 − próg → sprzedaż), wejście w poniedziałek o 01:00 czasu Londynu (rynek w Tokio już otwarty), wyjście po czasie.
Efekt znaleziony na danych niezależnych od danych IA5 (świece dzienne 2003–2019 i świece godzinowe brokera 2012–2022);
w inne dni tygodnia go nie ma. Lista wariantów ustalona przed pierwszym policzeniem na świecach Yahoo H1 (research/rynek/)."""

PARAMS = {"prog": [10, 15, 20]}          # RSI2 < próg → long; RSI2 > 100 − próg → short
EXITS = [{"kind": "time", "n": n, "cap": n} for n in (12, 20, 30)]   # wyjście po 12 / 20 / 30 godzinach od wejścia
HOURS = False                             # wejście o 01:00 Londynu (02:00 czasu polskiego) — poza oknem 07–17 (B11)


def signals(df, p, ind):
    ny = df.index.tz_convert("America/New_York")
    lon = df.index.tz_convert("Europe/London")
    # dzienne zamknięcie = ostatnia świeca przed 16:00 w Nowym Jorku (przed godziną rolowania), dni pon–pt
    sesja = np.asarray((ny.hour <= 15) & (ny.dayofweek < 5))
    dzien = ny.normalize().tz_localize(None)
    zamkniecia = df.close[sesja].groupby(dzien[sesja]).last()
    rsi = ind.rsi(zamkniecia, 2)
    piatki = rsi[rsi.index.dayofweek == 4]
    # świeca sygnału: poniedziałek 00:00 Londynu (wejście na open świecy 01:00); piątek = 3 dni wcześniej
    sygnal = np.asarray((lon.dayofweek == 0) & (lon.hour == 0))
    piatek = lon.normalize().tz_localize(None) - pd.Timedelta(days=3)
    r = pd.Series(piatki.reindex(piatek).to_numpy(), index=df.index)
    long_ = sygnal & (r < p["prog"])
    short = sygnal & (r > 100 - p["prog"])
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
