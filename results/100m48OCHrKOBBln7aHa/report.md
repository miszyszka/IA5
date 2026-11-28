# Raport strategii: zasięg wybicie

Run `20261128-085035` · silnik 0.15.0 · kod `7a812e4320d184bf` · dane `dd966aefc12b8a46`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -0.06 |
| percentyl benchmarku ≥ 95 | ✘ | 76.40 |
| PBO < 0,3 | ✘ | 0.97 |
| DSR ≥ 0,95 | ✘ | 0.42 |
| dodatni przy spreadzie ×1,5 | ✘ | -0.33 |

## Hipoteza

Wybicie z ściśnięcia z celem dopasowanym do prognozy zasięgu (D-076, zakładka Zasięg).
Kierunku nie przewidujemy — przewidujemy, JAK DALEKO rynek może dojść: zmienność skupia się w czasie i wraca do średniej,
więc zasięg najbliższych 3 dni da się prognozować (model HAR na dziennych zakresach, ind.range_forecast). Gdy na H1 rynek
stoi w wąskim pudełku z 24 godzin (wysokość w dolnych 20% z ostatnich 500 godzin), zlecenia stoją po obu stronach i to
wybicie wybiera kierunek: zamknięcie godziny nad pudełkiem = long, pod nim = short. Stop za drugą stroną pudełka
(gdy cel byłby wtedy nieosiągalny — w połowie pudełka), cel = 2 / 3 / 4 × stop. Wejście tylko wtedy, gdy cel mieści się
w prognozowanym zasięgu 3 dni — inaczej TP 3 × SL i tak zwykle by nie padł. Płatnik: uczestnicy, których stopy i zlecenia
stoją tuż za granicą konsolidacji, a po wybiciu muszą gonić cenę.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-27; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-21, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS. OOS tego okresu widziało już 4 wersji kodu strategii i 15 kandydatów eksploracji; ta strategia: 1 wersji.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

- Zasady portfela: bez limitu walut, hamulca i celu zmienności.

## Skala przeszukiwania

- **Przetestowane warianty: 3** (3 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 337 (limit otwartych pozycji w parze), 4.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 3379 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 168.3 (przerwa w dostępie do danych), 3.3 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, max 72 | tp=4 | 358 | 0.01 | 0.65 | 25.7 | 118 | 0.09 | -0.06 |
| 2 | poziomy TP/SL ze strategii, max 72 | tp=2 | 491 | -0.01 | -0.21 | 39.9 | 148 | 0.14 | 2.03 |
| 3 | poziomy TP/SL ze strategii, max 72 | tp=3 | 493 | -0.05 | -0.74 | 29.0 | 147 | 0.01 | -0.80 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, max 72 (tp=4)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 75 | -7.4 | -555.6 | 16.0 |
| EURGBP | 42 | -1.9 | -78.6 | 26.2 |
| EURJPY | 52 | 7.9 | 413.2 | 28.8 |
| EURUSD | 63 | 6.4 | 402.9 | 33.3 |
| GBPUSD | 68 | 5.7 | 387.6 | 33.8 |
| USDCAD | 37 | 5.1 | 189.5 | 32.4 |
| USDCHF | 65 | -2.9 | -189.8 | 23.1 |
| USDJPY | 74 | -4.6 | -343.0 | 23.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 21 | -20.5 | -430.5 | 14.3 |
| 2025 | 252 | 4.1 | 1 030.8 | 27.8 |
| 2026 | 203 | -1.8 | -374.1 | 26.1 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 358 | 0.7 | 233.4 | 25.7 |
| OOS | 118 | -0.1 | -7.3 | 28.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) | pominięte (limit walut) | pominięte (hamulec) |
|---|---|---|---|---|---|---|---|---|---|
| 5.0% | 9 350 | -6.5 | -3.3 | -17.5 | -17.5 | -0.18 | 0 | 0 | 0 |
| 10.0% | 8 524 | -14.8 | -7.7 | -32.0 | -32.2 | -0.19 | 0 | 0 | 0 |
| 15.0% | 7 679 | -23.2 | -12.4 | -44.1 | -44.3 | -0.18 | 4 | 0 | 0 |
| 20.0% | 7 175 | -28.2 | -15.3 | -53.1 | -53.3 | -0.12 | 18 | 0 | 0 |
| 30.0% | 5 387 | -46.1 | -26.7 | -66.9 | -67.1 | -0.16 | 66 | 0 | 0 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-27): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **476**, otwarte: **0** (razem 476).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 476 | 0 | 1 | 1 | 4 | 6 | 0.5 | 226 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 476 | 0 | 1 | 1 | 4 | 6 | 0.5 | 226 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| EURUSD | long | 2024-11-29 | 2024-11-29 | 0 | 3 | zamknięta | SL | -28.8 |
| USDCAD | long | 2024-11-29 | 2024-11-29 | 0 | 2 | zamknięta | SL | -30.8 |
| USDJPY | short | 2024-12-06 | 2024-12-09 | 3 | 16 | zamknięta | SL | -58.0 |
| EURGBP | short | 2024-12-09 | 2024-12-11 | 2 | 56 | zamknięta | TP | 48.4 |
| GBPUSD | short | 2024-12-11 | 2024-12-11 | 0 | 3 | zamknięta | SL | -29.1 |
| GBPUSD | short | 2024-12-12 | 2024-12-17 | 5 | 72 | zamknięta | czas | 35.3 |
| USDCHF | short | 2024-12-16 | 2024-12-16 | 0 | 7 | zamknięta | SL | -23.7 |
| USDCAD | long | 2024-12-16 | 2024-12-16 | 0 | 3 | zamknięta | SL | -29.8 |
| USDJPY | long | 2024-12-16 | 2024-12-17 | 1 | 26 | zamknięta | SL | -48.2 |
| AUDUSD | short | 2024-12-17 | 2024-12-18 | 2 | 35 | zamknięta | TP | 68.7 |
| USDJPY | short | 2024-12-17 | 2024-12-18 | 1 | 26 | zamknięta | SL | -52.1 |
| GBPUSD | long | 2024-12-24 | 2024-12-24 | 0 | 4 | zamknięta | SL | -24.0 |
| EURJPY | long | 2024-12-26 | 2024-12-30 | 4 | 49 | zamknięta | SL | -49.6 |
| USDJPY | long | 2024-12-26 | 2024-12-30 | 4 | 49 | zamknięta | SL | -35.0 |
| GBPUSD | short | 2024-12-26 | 2024-12-27 | 1 | 23 | zamknięta | SL | -28.9 |
| AUDUSD | short | 2024-12-26 | 2024-12-30 | 4 | 35 | zamknięta | SL | -18.2 |
| EURUSD | long | 2024-12-27 | 2024-12-30 | 3 | 19 | zamknięta | SL | -28.1 |
| GBPUSD | long | 2024-12-27 | 2024-12-30 | 3 | 26 | zamknięta | SL | -31.7 |
| USDCAD | short | 2024-12-27 | 2024-12-27 | 0 | 2 | zamknięta | SL | -20.5 |
| EURGBP | short | 2024-12-27 | 2025-01-02 | 6 | 69 | zamknięta | SL | -15.3 |
| USDCHF | long | 2024-12-30 | 2024-12-30 | 0 | 2 | zamknięta | SL | -23.3 |
| EURUSD | long | 2024-12-30 | 2024-12-30 | 0 | 2 | zamknięta | SL | -23.2 |
| EURGBP | long | 2025-01-06 | 2025-01-06 | 0 | 11 | zamknięta | SL | -15.8 |
| USDJPY | short | 2025-01-09 | 2025-01-09 | 0 | 6 | zamknięta | SL | -42.3 |
| USDCAD | long | 2025-01-10 | 2025-01-10 | 0 | 8 | zamknięta | SL | -28.4 |
| EURUSD | short | 2025-01-10 | 2025-01-10 | 0 | 2 | zamknięta | SL | -20.0 |
| AUDUSD | short | 2025-01-10 | 2025-01-13 | 4 | 35 | zamknięta | SL | -14.4 |
| USDCHF | long | 2025-01-10 | 2025-01-13 | 3 | 29 | zamknięta | TP | 59.9 |
| USDCAD | long | 2025-01-17 | 2025-01-17 | 0 | 6 | zamknięta | SL | -27.3 |
| USDJPY | short | 2025-01-29 | 2025-01-29 | 0 | 6 | zamknięta | SL | -51.6 |
| EURJPY | short | 2025-01-29 | 2025-02-03 | 5 | 64 | zamknięta | TP | 192.0 |
| AUDUSD | short | 2025-01-29 | 2025-01-30 | 1 | 15 | zamknięta | SL | -17.3 |
| EURUSD | short | 2025-01-29 | 2025-01-30 | 1 | 28 | zamknięta | SL | -25.4 |
| EURUSD | short | 2025-02-06 | 2025-02-11 | 5 | 72 | zamknięta | czas | 60.2 |
| AUDUSD | short | 2025-02-06 | 2025-02-06 | 0 | 7 | zamknięta | SL | -21.7 |
| USDCHF | long | 2025-02-07 | 2025-02-07 | 0 | 7 | zamknięta | SL | -22.8 |
| USDCHF | long | 2025-02-11 | 2025-02-12 | 1 | 23 | zamknięta | SL | -16.3 |
| EURJPY | long | 2025-02-11 | 2025-02-12 | 1 | 17 | zamknięta | TP | 200.8 |
| USDJPY | long | 2025-02-11 | 2025-02-12 | 1 | 26 | zamknięta | TP | 171.5 |
| EURUSD | long | 2025-02-11 | 2025-02-12 | 1 | 27 | zamknięta | TP | 88.5 |
| USDCHF | short | 2025-02-12 | 2025-02-12 | 0 | 4 | zamknięta | SL | -21.4 |
| EURGBP | long | 2025-02-12 | 2025-02-13 | 1 | 17 | zamknięta | SL | -14.7 |
| USDCAD | long | 2025-02-17 | 2025-02-20 | 3 | 72 | zamknięta | czas | 21.4 |
| USDCHF | long | 2025-02-18 | 2025-02-18 | 0 | 2 | zamknięta | SL | -21.7 |
| EURJPY | short | 2025-02-18 | 2025-02-18 | 0 | 8 | zamknięta | SL | -44.1 |
| EURUSD | short | 2025-02-18 | 2025-02-20 | 2 | 50 | zamknięta | SL | -27.7 |
| AUDUSD | long | 2025-02-19 | 2025-02-19 | 0 | 5 | zamknięta | SL | -13.6 |
| USDCHF | short | 2025-02-20 | 2025-02-25 | 5 | 72 | zamknięta | TP | 68.2 |
| GBPUSD | long | 2025-02-20 | 2025-02-25 | 5 | 72 | zamknięta | czas | 39.7 |
| EURUSD | long | 2025-02-25 | 2025-02-27 | 2 | 40 | zamknięta | SL | -21.8 |
| GBPUSD | long | 2025-02-25 | 2025-02-27 | 2 | 49 | zamknięta | SL | -28.3 |
| AUDUSD | short | 2025-02-26 | 2025-02-27 | 1 | 34 | zamknięta | TP | 77.4 |
| USDCHF | short | 2025-03-03 | 2025-03-04 | 1 | 20 | zamknięta | TP | 81.6 |
| GBPUSD | long | 2025-03-07 | 2025-03-10 | 3 | 21 | zamknięta | SL | -28.6 |
| USDJPY | long | 2025-03-11 | 2025-03-11 | 0 | 7 | zamknięta | SL | -54.4 |
| EURUSD | short | 2025-03-13 | 2025-03-14 | 1 | 28 | zamknięta | SL | -29.4 |
| AUDUSD | long | 2025-03-14 | 2025-03-17 | 3 | 30 | zamknięta | TP | 72.8 |
| GBPUSD | long | 2025-03-17 | 2025-03-20 | 3 | 72 | zamknięta | czas | -1.8 |
| USDCHF | short | 2025-03-17 | 2025-03-20 | 3 | 72 | zamknięta | czas | 4.0 |
| EURUSD | long | 2025-03-17 | 2025-03-19 | 2 | 41 | zamknięta | SL | -29.4 |
| EURGBP | long | 2025-03-18 | 2025-03-18 | 0 | 8 | zamknięta | SL | -14.4 |
| USDCAD | long | 2025-03-19 | 2025-03-24 | 5 | 72 | zamknięta | czas | -2.2 |
| EURJPY | long | 2025-03-21 | 2025-03-21 | 0 | 7 | zamknięta | SL | -64.0 |
| USDCHF | short | 2025-03-21 | 2025-03-21 | 0 | 4 | zamknięta | SL | -23.5 |
| USDCHF | short | 2025-03-25 | 2025-03-26 | 0 | 12 | zamknięta | SL | -22.9 |
| EURUSD | short | 2025-03-26 | 2025-03-27 | 1 | 26 | zamknięta | SL | -29.5 |
| EURJPY | long | 2025-03-26 | 2025-03-26 | 0 | 3 | zamknięta | SL | -45.3 |
| USDJPY | long | 2025-03-27 | 2025-03-28 | 1 | 20 | zamknięta | SL | -51.8 |
| EURUSD | long | 2025-03-28 | 2025-03-31 | 3 | 22 | zamknięta | SL | -33.6 |
| EURUSD | long | 2025-04-02 | 2025-04-02 | 0 | 8 | zamknięta | TP | 89.0 |
| EURJPY | short | 2025-04-15 | 2025-04-17 | 2 | 47 | zamknięta | SL | -58.0 |
| EURJPY | long | 2025-04-21 | 2025-04-21 | 0 | 7 | zamknięta | SL | -44.6 |
| AUDUSD | short | 2025-04-22 | 2025-04-23 | 1 | 21 | zamknięta | SL | -21.9 |
| EURJPY | long | 2025-04-25 | 2025-04-28 | 4 | 36 | zamknięta | SL | -54.0 |
| EURGBP | short | 2025-04-28 | 2025-04-30 | 2 | 53 | zamknięta | SL | -20.5 |
| GBPUSD | long | 2025-04-28 | 2025-05-01 | 3 | 64 | zamknięta | SL | -38.7 |
| AUDUSD | long | 2025-04-28 | 2025-04-29 | 1 | 25 | zamknięta | SL | -21.2 |
| USDJPY | short | 2025-04-28 | 2025-05-01 | 3 | 62 | zamknięta | SL | -51.9 |
| USDCHF | long | 2025-05-01 | 2025-05-02 | 1 | 28 | zamknięta | SL | -35.2 |
| USDCHF | short | 2025-05-05 | 2025-05-06 | 0 | 12 | zamknięta | SL | -32.7 |
| USDJPY | short | 2025-05-06 | 2025-05-07 | 2 | 37 | zamknięta | SL | -66.4 |
| USDCHF | long | 2025-05-06 | 2025-05-06 | 0 | 4 | zamknięta | SL | -32.3 |
| EURJPY | long | 2025-05-08 | 2025-05-12 | 4 | 47 | zamknięta | TP | 136.2 |
| EURUSD | long | 2025-05-13 | 2025-05-16 | 3 | 72 | zamknięta | czas | 65.2 |
| GBPUSD | long | 2025-05-16 | 2025-05-16 | 0 | 6 | zamknięta | SL | -27.0 |
| USDCAD | short | 2025-05-19 | 2025-05-20 | 1 | 15 | zamknięta | SL | -29.5 |
| USDCHF | short | 2025-05-20 | 2025-05-20 | 0 | 5 | zamknięta | SL | -26.9 |
| AUDUSD | short | 2025-05-22 | 2025-05-23 | 1 | 22 | zamknięta | SL | -27.4 |
| EURUSD | short | 2025-05-22 | 2025-05-23 | 1 | 22 | zamknięta | SL | -34.9 |
| USDCHF | long | 2025-05-22 | 2025-05-23 | 1 | 25 | zamknięta | SL | -25.0 |
| GBPUSD | long | 2025-05-23 | 2025-05-26 | 3 | 19 | zamknięta | TP | 125.2 |
| EURUSD | short | 2025-05-27 | 2025-05-29 | 2 | 41 | zamknięta | TP | 108.1 |
| EURGBP | short | 2025-05-27 | 2025-05-28 | 1 | 28 | zamknięta | SL | -13.6 |
| EURGBP | long | 2025-05-28 | 2025-05-28 | 0 | 4 | zamknięta | SL | -14.0 |
| AUDUSD | short | 2025-05-28 | 2025-05-29 | 1 | 19 | zamknięta | SL | -24.5 |
| USDJPY | long | 2025-05-28 | 2025-05-29 | 1 | 24 | zamknięta | SL | -59.2 |
| AUDUSD | long | 2025-05-29 | 2025-05-30 | 0 | 13 | zamknięta | SL | -29.4 |
| AUDUSD | short | 2025-05-30 | 2025-05-30 | 0 | 9 | zamknięta | SL | -24.3 |
| EURUSD | short | 2025-05-30 | 2025-05-30 | 0 | 4 | zamknięta | SL | -39.6 |
| USDCHF | short | 2025-06-02 | 2025-06-03 | 1 | 31 | zamknięta | SL | -25.2 |
| EURUSD | short | 2025-06-03 | 2025-06-04 | 1 | 28 | zamknięta | SL | -30.9 |
| EURGBP | short | 2025-06-03 | 2025-06-05 | 2 | 49 | zamknięta | SL | -13.2 |
| USDJPY | long | 2025-06-03 | 2025-06-04 | 1 | 28 | zamknięta | SL | -61.5 |
| AUDUSD | long | 2025-06-04 | 2025-06-09 | 5 | 72 | zamknięta | czas | 27.1 |
| USDCAD | long | 2025-06-06 | 2025-06-11 | 5 | 72 | zamknięta | czas | -3.2 |
| USDCHF | short | 2025-06-09 | 2025-06-09 | 0 | 6 | zamknięta | SL | -27.5 |
| AUDUSD | long | 2025-06-10 | 2025-06-11 | 0 | 12 | zamknięta | SL | -22.1 |
| EURJPY | long | 2025-06-11 | 2025-06-12 | 1 | 20 | zamknięta | SL | -53.6 |
| EURUSD | long | 2025-06-11 | 2025-06-12 | 1 | 23 | zamknięta | TP | 139.2 |
| USDJPY | short | 2025-06-16 | 2025-06-16 | 0 | 4 | zamknięta | SL | -50.6 |
| USDJPY | long | 2025-06-19 | 2025-06-23 | 4 | 47 | zamknięta | TP | 217.9 |
| EURJPY | long | 2025-06-19 | 2025-06-23 | 4 | 41 | zamknięta | TP | 178.8 |
| USDJPY | long | 2025-06-25 | 2025-06-26 | 1 | 15 | zamknięta | SL | -54.9 |
| AUDUSD | short | 2025-06-27 | 2025-06-30 | 3 | 14 | zamknięta | SL | -22.0 |
| AUDUSD | short | 2025-07-02 | 2025-07-02 | 0 | 10 | zamknięta | SL | -17.9 |
| EURJPY | long | 2025-07-07 | 2025-07-09 | 2 | 45 | zamknięta | TP | 165.3 |
| GBPUSD | short | 2025-07-07 | 2025-07-10 | 3 | 72 | zamknięta | czas | 10.7 |
| USDJPY | long | 2025-07-07 | 2025-07-08 | 1 | 33 | zamknięta | TP | 186.7 |
| EURUSD | short | 2025-07-07 | 2025-07-10 | 3 | 72 | zamknięta | czas | 22.6 |
| USDCHF | long | 2025-07-07 | 2025-07-09 | 2 | 61 | zamknięta | SL | -27.6 |
| USDCAD | long | 2025-07-09 | 2025-07-10 | 1 | 20 | zamknięta | SL | -29.6 |
| USDJPY | short | 2025-07-09 | 2025-07-11 | 2 | 36 | zamknięta | SL | -37.6 |
| GBPUSD | short | 2025-07-10 | 2025-07-15 | 5 | 71 | zamknięta | TP | 140.6 |
| EURUSD | short | 2025-07-10 | 2025-07-15 | 5 | 72 | zamknięta | czas | 73.9 |
| USDJPY | long | 2025-07-15 | 2025-07-16 | 1 | 28 | zamknięta | SL | -38.5 |
| USDCAD | short | 2025-07-18 | 2025-07-22 | 4 | 54 | zamknięta | TP | 109.3 |
| AUDUSD | short | 2025-07-22 | 2025-07-22 | 0 | 5 | zamknięta | SL | -18.7 |
| USDCHF | short | 2025-07-22 | 2025-07-25 | 3 | 72 | zamknięta | czas | -6.8 |
| USDJPY | long | 2025-07-24 | 2025-07-29 | 5 | 71 | zamknięta | TP | 198.3 |
| AUDUSD | short | 2025-07-28 | 2025-07-30 | 2 | 54 | zamknięta | TP | 80.1 |
| GBPUSD | long | 2025-07-30 | 2025-07-30 | 0 | 4 | zamknięta | SL | -30.1 |
| USDCHF | long | 2025-08-01 | 2025-08-01 | 0 | 5 | zamknięta | SL | -19.6 |
| EURUSD | short | 2025-08-05 | 2025-08-05 | 0 | 10 | zamknięta | SL | -26.3 |
| AUDUSD | short | 2025-08-05 | 2025-08-05 | 0 | 5 | zamknięta | SL | -20.3 |
| EURGBP | short | 2025-08-05 | 2025-08-05 | 0 | 5 | zamknięta | SL | -18.8 |
| GBPUSD | long | 2025-08-06 | 2025-08-07 | 1 | 25 | zamknięta | TP | 109.7 |
| AUDUSD | long | 2025-08-07 | 2025-08-07 | 0 | 10 | zamknięta | SL | -18.6 |
| USDJPY | long | 2025-08-08 | 2025-08-13 | 5 | 72 | zamknięta | czas | -25.2 |
| GBPUSD | long | 2025-08-11 | 2025-08-11 | 0 | 6 | zamknięta | SL | -29.4 |
| USDCHF | long | 2025-08-11 | 2025-08-12 | 1 | 30 | zamknięta | SL | -21.8 |
| AUDUSD | short | 2025-08-11 | 2025-08-12 | 1 | 15 | zamknięta | SL | -12.0 |
| EURUSD | short | 2025-08-11 | 2025-08-12 | 1 | 25 | zamknięta | SL | -24.0 |
| AUDUSD | short | 2025-08-12 | 2025-08-12 | 0 | 9 | zamknięta | SL | -16.8 |
| EURUSD | long | 2025-08-12 | 2025-08-15 | 3 | 72 | zamknięta | czas | 53.6 |
| USDCAD | long | 2025-08-14 | 2025-08-19 | 5 | 72 | zamknięta | czas | 55.6 |
| GBPUSD | short | 2025-08-14 | 2025-08-19 | 5 | 72 | zamknięta | czas | 47.2 |
| EURGBP | long | 2025-08-15 | 2025-08-20 | 5 | 72 | zamknięta | czas | 4.8 |
| AUDUSD | long | 2025-08-15 | 2025-08-18 | 3 | 23 | zamknięta | SL | -22.1 |
| USDCHF | long | 2025-08-18 | 2025-08-19 | 1 | 23 | zamknięta | SL | -15.6 |
| USDCHF | short | 2025-08-19 | 2025-08-19 | 0 | 5 | zamknięta | SL | -20.2 |
| EURJPY | long | 2025-08-21 | 2025-08-25 | 4 | 56 | zamknięta | SL | -41.7 |
| USDJPY | long | 2025-08-21 | 2025-08-22 | 1 | 29 | zamknięta | SL | -43.1 |
| USDCAD | long | 2025-08-21 | 2025-08-22 | 1 | 27 | zamknięta | SL | -21.0 |
| EURUSD | short | 2025-08-21 | 2025-08-22 | 1 | 25 | zamknięta | SL | -32.1 |
| USDJPY | long | 2025-08-27 | 2025-08-27 | 0 | 12 | zamknięta | SL | -45.1 |
| AUDUSD | short | 2025-08-27 | 2025-08-27 | 0 | 7 | zamknięta | SL | -19.4 |
| EURGBP | long | 2025-08-28 | 2025-09-02 | 5 | 67 | zamknięta | TP | 47.4 |
| GBPUSD | short | 2025-08-29 | 2025-08-29 | 0 | 6 | zamknięta | SL | -30.7 |
| USDCAD | long | 2025-09-04 | 2025-09-05 | 1 | 25 | zamknięta | SL | -21.1 |
| EURUSD | long | 2025-09-05 | 2025-09-09 | 4 | 42 | zamknięta | TP | 99.7 |
| GBPUSD | long | 2025-09-05 | 2025-09-09 | 4 | 40 | zamknięta | TP | 95.7 |
| USDCHF | short | 2025-09-05 | 2025-09-05 | 0 | 8 | zamknięta | TP | 71.0 |
| GBPUSD | short | 2025-09-11 | 2025-09-11 | 0 | 7 | zamknięta | SL | -24.2 |
| USDCHF | long | 2025-09-11 | 2025-09-11 | 0 | 6 | zamknięta | SL | -21.1 |
| USDJPY | long | 2025-09-11 | 2025-09-11 | 0 | 6 | zamknięta | SL | -36.7 |
| EURJPY | long | 2025-09-12 | 2025-09-17 | 5 | 72 | zamknięta | czas | 17.4 |
| GBPUSD | long | 2025-09-15 | 2025-09-17 | 2 | 59 | zamknięta | TP | 127.0 |
| USDCHF | short | 2025-09-15 | 2025-09-16 | 1 | 28 | zamknięta | TP | 62.5 |
| EURUSD | long | 2025-09-15 | 2025-09-16 | 1 | 30 | zamknięta | TP | 102.3 |
| USDCAD | short | 2025-09-15 | 2025-09-16 | 1 | 25 | zamknięta | TP | 77.2 |
| USDJPY | short | 2025-09-16 | 2025-09-17 | 2 | 38 | zamknięta | TP | 119.2 |
| EURGBP | long | 2025-09-16 | 2025-09-18 | 2 | 60 | zamknięta | TP | 43.1 |
| EURJPY | short | 2025-09-17 | 2025-09-17 | 0 | 9 | zamknięta | SL | -30.6 |
| USDCHF | short | 2025-09-22 | 2025-09-24 | 2 | 54 | zamknięta | SL | -20.3 |
| GBPUSD | long | 2025-09-22 | 2025-09-24 | 2 | 44 | zamknięta | SL | -27.7 |
| USDJPY | short | 2025-09-23 | 2025-09-23 | 0 | 4 | zamknięta | SL | -31.6 |
| AUDUSD | long | 2025-09-23 | 2025-09-24 | 1 | 16 | zamknięta | SL | -16.9 |
| EURJPY | long | 2025-09-24 | 2025-09-29 | 5 | 72 | zamknięta | czas | -18.2 |
| USDJPY | long | 2025-09-24 | 2025-09-25 | 1 | 31 | zamknięta | TP | 136.4 |
| GBPUSD | short | 2025-09-25 | 2025-09-29 | 4 | 43 | zamknięta | SL | -28.6 |
| EURGBP | short | 2025-09-26 | 2025-09-29 | 3 | 24 | zamknięta | SL | -11.4 |
| USDJPY | short | 2025-09-30 | 2025-10-01 | 1 | 27 | zamknięta | TP | 126.5 |
| EURUSD | long | 2025-09-30 | 2025-09-30 | 0 | 5 | zamknięta | SL | -25.7 |
| AUDUSD | short | 2025-10-02 | 2025-10-03 | 1 | 26 | zamknięta | SL | -20.9 |
| AUDUSD | long | 2025-10-06 | 2025-10-07 | 1 | 16 | zamknięta | SL | -15.7 |
| GBPUSD | short | 2025-10-17 | 2025-10-20 | 3 | 12 | zamknięta | SL | -32.8 |
| EURUSD | short | 2025-10-21 | 2025-10-24 | 3 | 72 | zamknięta | czas | 18.0 |
| AUDUSD | long | 2025-10-23 | 2025-10-24 | 1 | 24 | zamknięta | SL | -17.1 |
| USDJPY | long | 2025-10-24 | 2025-10-24 | 0 | 7 | zamknięta | SL | -35.1 |
| EURGBP | long | 2025-10-28 | 2025-10-28 | 0 | 7 | zamknięta | TP | 43.2 |
| USDCHF | long | 2025-10-31 | 2025-11-05 | 5 | 68 | zamknięta | TP | 68.5 |
| EURJPY | short | 2025-10-31 | 2025-11-04 | 4 | 46 | zamknięta | TP | 169.7 |
| EURUSD | short | 2025-10-31 | 2025-11-05 | 5 | 72 | zamknięta | czas | 56.1 |
| AUDUSD | long | 2025-11-03 | 2025-11-03 | 0 | 5 | zamknięta | SL | -15.6 |
| AUDUSD | short | 2025-11-03 | 2025-11-06 | 3 | 72 | zamknięta | czas | 48.7 |
| EURGBP | long | 2025-11-04 | 2025-11-07 | 3 | 72 | zamknięta | czas | 0.1 |
| USDCAD | long | 2025-11-04 | 2025-11-07 | 3 | 71 | zamknięta | SL | -24.5 |
| EURUSD | long | 2025-11-06 | 2025-11-11 | 5 | 72 | zamknięta | czas | 51.0 |
| USDJPY | short | 2025-11-06 | 2025-11-10 | 4 | 34 | zamknięta | SL | -45.9 |
| USDCHF | short | 2025-11-07 | 2025-11-10 | 2 | 9 | zamknięta | SL | -20.3 |
| USDCAD | long | 2025-11-11 | 2025-11-11 | 0 | 7 | zamknięta | SL | -24.0 |
| USDCHF | short | 2025-11-11 | 2025-11-13 | 2 | 49 | zamknięta | TP | 74.6 |
| USDJPY | short | 2025-11-11 | 2025-11-12 | 0 | 11 | zamknięta | SL | -43.4 |
| AUDUSD | long | 2025-11-12 | 2025-11-13 | 1 | 34 | zamknięta | SL | -13.0 |
| EURJPY | long | 2025-11-13 | 2025-11-14 | 1 | 29 | zamknięta | SL | -39.8 |
| USDJPY | long | 2025-11-18 | 2025-11-19 | 1 | 33 | zamknięta | TP | 153.9 |
| EURJPY | long | 2025-11-18 | 2025-11-19 | 1 | 34 | zamknięta | TP | 123.2 |
| GBPUSD | short | 2025-11-18 | 2025-11-18 | 0 | 4 | zamknięta | SL | -31.7 |
| GBPUSD | short | 2025-11-19 | 2025-11-24 | 5 | 72 | zamknięta | czas | 28.9 |
| GBPUSD | long | 2025-11-25 | 2025-11-25 | 0 | 11 | zamknięta | TP | 81.6 |
| USDJPY | short | 2025-11-25 | 2025-11-28 | 3 | 72 | zamknięta | czas | 11.5 |
| USDCHF | long | 2025-11-25 | 2025-11-25 | 0 | 5 | zamknięta | SL | -19.3 |
| AUDUSD | short | 2025-11-28 | 2025-11-28 | 0 | 5 | zamknięta | SL | -8.1 |
| EURUSD | short | 2025-11-28 | 2025-11-28 | 0 | 7 | zamknięta | SL | -21.0 |
| GBPUSD | short | 2025-11-28 | 2025-11-28 | 0 | 7 | zamknięta | SL | -31.7 |
| USDCHF | long | 2025-11-28 | 2025-11-28 | 0 | 4 | zamknięta | SL | -14.1 |
| EURGBP | long | 2025-12-01 | 2025-12-03 | 2 | 56 | zamknięta | SL | -15.4 |
| EURJPY | long | 2025-12-02 | 2025-12-04 | 2 | 53 | zamknięta | SL | -39.0 |
| AUDUSD | long | 2025-12-05 | 2025-12-10 | 5 | 72 | zamknięta | czas | 24.3 |
| EURJPY | long | 2025-12-05 | 2025-12-09 | 4 | 50 | zamknięta | TP | 145.8 |
| USDCHF | long | 2025-12-08 | 2025-12-10 | 2 | 45 | zamknięta | SL | -18.6 |
| USDJPY | long | 2025-12-08 | 2025-12-11 | 3 | 72 | zamknięta | czas | 16.5 |
| GBPUSD | long | 2025-12-09 | 2025-12-09 | 0 | 4 | zamknięta | SL | -21.9 |
| GBPUSD | long | 2025-12-10 | 2025-12-11 | 1 | 25 | zamknięta | TP | 88.0 |
| EURUSD | long | 2025-12-15 | 2025-12-17 | 2 | 40 | zamknięta | SL | -20.2 |
| USDJPY | short | 2025-12-16 | 2025-12-17 | 1 | 16 | zamknięta | SL | -44.9 |
| USDJPY | long | 2025-12-18 | 2025-12-18 | 0 | 7 | zamknięta | SL | -41.7 |
| AUDUSD | short | 2025-12-19 | 2025-12-19 | 0 | 7 | zamknięta | SL | -15.1 |
| USDCHF | short | 2025-12-22 | 2025-12-23 | 1 | 27 | zamknięta | TP | 63.7 |
| EURUSD | long | 2025-12-22 | 2025-12-26 | 4 | 72 | zamknięta | czas | 47.6 |
| EURGBP | short | 2025-12-23 | 2025-12-23 | 0 | 10 | zamknięta | SL | -14.8 |
| GBPUSD | short | 2025-12-26 | 2025-12-26 | 0 | 6 | zamknięta | SL | -29.2 |
| AUDUSD | short | 2025-12-26 | 2025-12-26 | 0 | 4 | zamknięta | SL | -12.3 |
| EURJPY | long | 2025-12-31 | 2026-01-05 | 5 | 36 | zamknięta | SL | -31.1 |
| USDCHF | long | 2026-01-08 | 2026-01-12 | 4 | 45 | zamknięta | SL | -18.2 |
| USDJPY | long | 2026-01-08 | 2026-01-09 | 1 | 25 | zamknięta | TP | 115.8 |
| AUDUSD | short | 2026-01-09 | 2026-01-09 | 0 | 6 | zamknięta | SL | -13.1 |
| GBPUSD | short | 2026-01-09 | 2026-01-09 | 0 | 5 | zamknięta | SL | -18.6 |
| EURUSD | short | 2026-01-09 | 2026-01-12 | 2 | 8 | zamknięta | SL | -22.6 |
| USDCHF | long | 2026-01-13 | 2026-01-16 | 3 | 72 | zamknięta | czas | 32.2 |
| EURUSD | short | 2026-01-15 | 2026-01-19 | 4 | 55 | zamknięta | SL | -17.9 |
| GBPUSD | short | 2026-01-15 | 2026-01-20 | 5 | 65 | zamknięta | SL | -23.6 |
| EURJPY | short | 2026-01-15 | 2026-01-20 | 5 | 62 | zamknięta | SL | -36.7 |
| AUDUSD | long | 2026-01-21 | 2026-01-22 | 1 | 32 | zamknięta | TP | 66.9 |
| EURJPY | long | 2026-02-03 | 2026-02-04 | 1 | 18 | zamknięta | TP | 98.7 |
| USDJPY | long | 2026-02-03 | 2026-02-06 | 3 | 72 | zamknięta | czas | 116.3 |
| EURJPY | long | 2026-02-05 | 2026-02-05 | 0 | 6 | zamknięta | SL | -40.2 |
| EURGBP | long | 2026-02-17 | 2026-02-17 | 0 | 8 | zamknięta | TP | 29.4 |
| USDJPY | short | 2026-02-17 | 2026-02-17 | 0 | 8 | zamknięta | SL | -43.7 |
| EURUSD | short | 2026-02-17 | 2026-02-17 | 1 | 14 | zamknięta | SL | -20.6 |
| AUDUSD | short | 2026-02-17 | 2026-02-17 | 0 | 4 | zamknięta | SL | -24.9 |
| USDCHF | long | 2026-02-17 | 2026-02-17 | 0 | 9 | zamknięta | SL | -18.9 |
| USDCHF | long | 2026-02-19 | 2026-02-23 | 4 | 36 | zamknięta | SL | -22.3 |
| EURJPY | long | 2026-02-20 | 2026-02-23 | 3 | 14 | zamknięta | SL | -51.0 |
| GBPUSD | long | 2026-02-20 | 2026-02-25 | 5 | 72 | zamknięta | czas | 44.1 |
| AUDUSD | short | 2026-02-24 | 2026-02-24 | 0 | 5 | zamknięta | SL | -20.4 |
| EURUSD | long | 2026-02-25 | 2026-02-25 | 0 | 5 | zamknięta | SL | -21.1 |
| USDCHF | short | 2026-02-27 | 2026-03-02 | 3 | 18 | zamknięta | SL | -21.8 |
| EURJPY | short | 2026-03-12 | 2026-03-13 | 2 | 37 | zamknięta | TP | 112.6 |
| USDCAD | long | 2026-03-12 | 2026-03-13 | 1 | 21 | zamknięta | TP | 67.5 |
| EURGBP | long | 2026-03-13 | 2026-03-16 | 3 | 20 | zamknięta | SL | -11.2 |
| AUDUSD | long | 2026-03-17 | 2026-03-18 | 1 | 24 | zamknięta | SL | -35.1 |
| USDJPY | short | 2026-03-18 | 2026-03-18 | 0 | 6 | zamknięta | SL | -42.4 |
| EURJPY | long | 2026-03-18 | 2026-03-18 | 0 | 9 | zamknięta | SL | -33.8 |
| USDCHF | long | 2026-03-18 | 2026-03-19 | 1 | 31 | zamknięta | SL | -25.6 |
| GBPUSD | short | 2026-03-26 | 2026-03-30 | 4 | 52 | zamknięta | TP | 149.2 |
| EURUSD | short | 2026-03-27 | 2026-03-27 | 0 | 8 | zamknięta | SL | -24.2 |
| USDJPY | long | 2026-03-27 | 2026-03-30 | 3 | 22 | zamknięta | SL | -38.5 |
| USDCAD | long | 2026-03-27 | 2026-04-01 | 5 | 72 | zamknięta | czas | 25.8 |
| AUDUSD | short | 2026-03-30 | 2026-03-31 | 1 | 22 | zamknięta | SL | -29.7 |
| USDCAD | long | 2026-04-03 | 2026-04-06 | 3 | 17 | zamknięta | SL | -26.8 |
| GBPUSD | long | 2026-04-06 | 2026-04-07 | 1 | 19 | zamknięta | SL | -44.1 |
| USDJPY | short | 2026-04-06 | 2026-04-06 | 0 | 7 | zamknięta | SL | -28.4 |
| USDCAD | short | 2026-04-06 | 2026-04-08 | 2 | 36 | zamknięta | TP | 77.7 |
| EURJPY | long | 2026-04-07 | 2026-04-09 | 2 | 52 | zamknięta | TP | 121.9 |
| EURUSD | long | 2026-04-07 | 2026-04-08 | 1 | 15 | zamknięta | TP | 108.6 |
| USDCHF | long | 2026-04-07 | 2026-04-07 | 0 | 6 | zamknięta | SL | -22.4 |
| USDCAD | short | 2026-04-09 | 2026-04-13 | 3 | 33 | zamknięta | SL | -41.3 |
| EURUSD | long | 2026-04-10 | 2026-04-13 | 2 | 8 | zamknięta | SL | -55.7 |
| EURGBP | short | 2026-04-14 | 2026-04-16 | 2 | 51 | zamknięta | SL | -12.8 |
| USDCHF | long | 2026-04-15 | 2026-04-16 | 1 | 16 | zamknięta | SL | -21.1 |
| EURJPY | long | 2026-04-15 | 2026-04-16 | 1 | 15 | zamknięta | SL | -27.4 |
| USDJPY | long | 2026-04-15 | 2026-04-15 | 0 | 4 | zamknięta | SL | -26.9 |
| GBPUSD | short | 2026-04-16 | 2026-04-17 | 1 | 27 | zamknięta | SL | -31.6 |
| USDCHF | long | 2026-04-16 | 2026-04-17 | 1 | 27 | zamknięta | SL | -23.9 |
| EURUSD | short | 2026-04-16 | 2026-04-17 | 1 | 23 | zamknięta | SL | -27.4 |
| EURJPY | long | 2026-04-17 | 2026-04-17 | 0 | 5 | zamknięta | SL | -36.6 |
| USDJPY | long | 2026-04-21 | 2026-04-24 | 3 | 72 | zamknięta | czas | 62.8 |
| EURJPY | short | 2026-04-22 | 2026-04-27 | 5 | 72 | zamknięta | czas | -12.4 |
| EURUSD | short | 2026-04-28 | 2026-04-30 | 2 | 57 | zamknięta | SL | -27.1 |
| GBPUSD | short | 2026-04-28 | 2026-04-30 | 2 | 57 | zamknięta | SL | -35.4 |
| AUDUSD | short | 2026-04-29 | 2026-04-30 | 1 | 29 | zamknięta | SL | -20.5 |
| USDJPY | long | 2026-04-29 | 2026-04-30 | 1 | 23 | zamknięta | SL | -24.9 |
| AUDUSD | long | 2026-05-11 | 2026-05-12 | 0 | 11 | zamknięta | SL | -19.3 |
| EURUSD | short | 2026-05-12 | 2026-05-15 | 3 | 65 | zamknięta | TP | 87.7 |
| EURJPY | short | 2026-05-13 | 2026-05-18 | 5 | 72 | zamknięta | czas | -16.6 |
| USDJPY | long | 2026-05-13 | 2026-05-14 | 1 | 30 | zamknięta | SL | -45.5 |
| AUDUSD | long | 2026-05-13 | 2026-05-14 | 1 | 27 | zamknięta | SL | -19.2 |
| USDCAD | long | 2026-05-14 | 2026-05-19 | 5 | 72 | zamknięta | czas | 41.5 |
| EURUSD | short | 2026-05-19 | 2026-05-22 | 3 | 72 | zamknięta | czas | 14.0 |
| USDCHF | long | 2026-05-19 | 2026-05-22 | 3 | 72 | zamknięta | czas | -8.6 |
| EURJPY | short | 2026-05-19 | 2026-05-22 | 3 | 72 | zamknięta | czas | 15.5 |
| EURUSD | short | 2026-05-26 | 2026-05-27 | 1 | 25 | zamknięta | SL | -25.3 |
| USDJPY | long | 2026-05-26 | 2026-05-29 | 3 | 72 | zamknięta | czas | 9.4 |
| EURJPY | long | 2026-05-26 | 2026-05-28 | 2 | 44 | zamknięta | SL | -31.0 |
| GBPUSD | short | 2026-05-26 | 2026-05-29 | 3 | 72 | zamknięta | czas | 20.2 |
| AUDUSD | short | 2026-05-27 | 2026-05-28 | 1 | 34 | zamknięta | SL | -21.5 |
| USDCAD | long | 2026-05-27 | 2026-05-28 | 1 | 31 | zamknięta | SL | -16.0 |
| EURGBP | long | 2026-05-29 | 2026-05-29 | 0 | 4 | zamknięta | SL | -10.1 |
| USDJPY | long | 2026-06-02 | 2026-06-03 | 1 | 19 | zamknięta | SL | -19.4 |
| GBPUSD | short | 2026-06-03 | 2026-06-05 | 2 | 52 | zamknięta | SL | -17.8 |
| AUDUSD | short | 2026-06-03 | 2026-06-03 | 0 | 4 | zamknięta | SL | -17.9 |
| AUDUSD | short | 2026-06-03 | 2026-06-05 | 2 | 50 | zamknięta | TP | 68.3 |
| EURJPY | long | 2026-06-04 | 2026-06-05 | 1 | 28 | zamknięta | SL | -32.4 |
| EURUSD | long | 2026-06-04 | 2026-06-04 | 0 | 11 | zamknięta | SL | -18.4 |
| EURGBP | long | 2026-06-11 | 2026-06-11 | 0 | 5 | zamknięta | SL | -10.4 |
| EURGBP | long | 2026-06-17 | 2026-06-17 | 0 | 5 | zamknięta | SL | -9.7 |
| USDJPY | short | 2026-06-17 | 2026-06-17 | 0 | 7 | zamknięta | SL | -16.4 |
| AUDUSD | short | 2026-06-22 | 2026-06-22 | 0 | 4 | zamknięta | SL | -17.2 |
| USDJPY | long | 2026-06-25 | 2026-06-25 | 0 | 7 | zamknięta | SL | -19.6 |
| USDJPY | long | 2026-06-29 | 2026-06-30 | 1 | 30 | zamknięta | TP | 76.0 |
| GBPUSD | long | 2026-06-29 | 2026-07-02 | 3 | 67 | zamknięta | TP | 86.0 |
| USDCAD | long | 2026-06-29 | 2026-06-30 | 1 | 32 | zamknięta | SL | -24.0 |
| EURUSD | short | 2026-07-06 | 2026-07-06 | 1 | 16 | zamknięta | SL | -21.8 |
| GBPUSD | short | 2026-07-06 | 2026-07-06 | 0 | 10 | zamknięta | SL | -23.3 |
| EURGBP | short | 2026-07-06 | 2026-07-08 | 2 | 56 | zamknięta | TP | 28.9 |
| EURJPY | long | 2026-07-08 | 2026-07-10 | 2 | 45 | zamknięta | SL | -31.5 |
| AUDUSD | long | 2026-07-15 | 2026-07-17 | 2 | 47 | zamknięta | SL | -15.8 |
| EURGBP | short | 2026-07-15 | 2026-07-15 | 0 | 5 | zamknięta | TP | 39.2 |
| GBPUSD | long | 2026-07-15 | 2026-07-15 | 0 | 5 | zamknięta | TP | 58.4 |
| USDCAD | short | 2026-07-15 | 2026-07-17 | 2 | 54 | zamknięta | TP | 61.0 |
| EURUSD | long | 2026-07-15 | 2026-07-20 | 5 | 72 | zamknięta | czas | -11.3 |
| USDJPY | short | 2026-07-15 | 2026-07-16 | 1 | 26 | zamknięta | SL | -27.1 |
| USDCHF | short | 2026-07-15 | 2026-07-20 | 5 | 71 | zamknięta | SL | -20.9 |
| EURJPY | short | 2026-07-17 | 2026-07-17 | 0 | 5 | zamknięta | SL | -32.5 |
| USDCHF | long | 2026-07-21 | 2026-07-24 | 3 | 71 | zamknięta | TP | 64.3 |
| GBPUSD | short | 2026-07-23 | 2026-07-28 | 5 | 69 | zamknięta | TP | 73.1 |
| USDJPY | long | 2026-07-28 | 2026-07-28 | 0 | 6 | zamknięta | SL | -21.7 |
| GBPUSD | long | 2026-08-05 | 2026-08-07 | 2 | 51 | zamknięta | SL | -27.5 |
| AUDUSD | short | 2026-08-06 | 2026-08-07 | 1 | 29 | zamknięta | SL | -16.6 |
| AUDUSD | short | 2026-08-11 | 2026-08-11 | 0 | 7 | zamknięta | SL | -16.6 |
| EURUSD | short | 2026-08-11 | 2026-08-12 | 1 | 30 | zamknięta | SL | -15.6 |
| AUDUSD | long | 2026-08-11 | 2026-08-13 | 2 | 37 | zamknięta | SL | -15.9 |
| USDCHF | long | 2026-08-12 | 2026-08-12 | 0 | 5 | zamknięta | SL | -15.4 |
| EURGBP | short | 2026-08-12 | 2026-08-12 | 0 | 5 | zamknięta | SL | -9.8 |
| AUDUSD | long | 2026-08-14 | 2026-08-17 | 3 | 22 | zamknięta | TP | 44.1 |
| EURUSD | long | 2026-08-14 | 2026-08-19 | 5 | 72 | zamknięta | czas | 54.1 |
| GBPUSD | long | 2026-08-14 | 2026-08-19 | 5 | 72 | zamknięta | czas | 41.2 |
| EURGBP | long | 2026-08-17 | 2026-08-17 | 0 | 9 | zamknięta | SL | -8.7 |
| USDCHF | short | 2026-08-19 | 2026-08-19 | 0 | 7 | zamknięta | TP | 47.8 |
| EURGBP | long | 2026-08-19 | 2026-08-19 | 0 | 4 | zamknięta | SL | -7.7 |
| EURUSD | short | 2026-08-25 | 2026-08-25 | 0 | 4 | zamknięta | SL | -17.2 |
| USDJPY | long | 2026-08-25 | 2026-08-25 | 0 | 7 | zamknięta | SL | -29.2 |
| EURJPY | long | 2026-08-25 | 2026-08-26 | 1 | 18 | zamknięta | SL | -30.7 |
| GBPUSD | short | 2026-08-26 | 2026-08-28 | 2 | 52 | zamknięta | TP | 75.9 |
| EURUSD | short | 2026-08-26 | 2026-08-28 | 2 | 52 | zamknięta | TP | 59.1 |
| USDJPY | long | 2026-08-26 | 2026-08-31 | 5 | 72 | zamknięta | czas | 33.9 |
| AUDUSD | long | 2026-08-27 | 2026-08-28 | 1 | 25 | zamknięta | SL | -15.6 |
| USDCAD | short | 2026-08-27 | 2026-08-28 | 1 | 25 | zamknięta | SL | -21.5 |
| EURJPY | long | 2026-08-28 | 2026-08-28 | 0 | 5 | zamknięta | SL | -23.6 |
| USDJPY | long | 2026-09-01 | 2026-09-02 | 1 | 24 | zamknięta | SL | -26.2 |
| EURJPY | short | 2026-09-02 | 2026-09-02 | 0 | 9 | zamknięta | TP | 87.4 |
| GBPUSD | long | 2026-09-08 | 2026-09-08 | 0 | 4 | zamknięta | SL | -17.4 |
| GBPUSD | short | 2026-09-10 | 2026-09-15 | 5 | 72 | zamknięta | czas | 34.8 |
| USDCAD | long | 2026-09-16 | 2026-09-21 | 5 | 66 | zamknięta | TP | 77.5 |
| AUDUSD | long | 2026-09-21 | 2026-09-21 | 0 | 12 | zamknięta | SL | -13.6 |
| USDCAD | long | 2026-09-24 | 2026-09-29 | 5 | 64 | zamknięta | TP | 72.2 |
| GBPUSD | long | 2026-09-25 | 2026-09-29 | 4 | 45 | zamknięta | SL | -22.4 |
| USDCHF | long | 2026-09-28 | 2026-10-01 | 3 | 72 | zamknięta | czas | 60.0 |
| AUDUSD | long | 2026-10-06 | 2026-10-07 | 1 | 23 | zamknięta | SL | -19.4 |
| GBPUSD | long | 2026-10-12 | 2026-10-12 | 0 | 5 | zamknięta | SL | -25.3 |
| USDJPY | long | 2026-10-12 | 2026-10-13 | 1 | 19 | zamknięta | SL | -24.5 |
| GBPUSD | long | 2026-10-13 | 2026-10-14 | 1 | 26 | zamknięta | SL | -22.2 |
| AUDUSD | long | 2026-10-13 | 2026-10-14 | 1 | 26 | zamknięta | SL | -17.5 |
| USDCHF | short | 2026-10-13 | 2026-10-14 | 1 | 20 | zamknięta | SL | -18.0 |
| EURGBP | short | 2026-10-14 | 2026-10-14 | 0 | 6 | zamknięta | SL | -8.8 |
| USDCHF | long | 2026-10-14 | 2026-10-14 | 0 | 6 | zamknięta | TP | 49.0 |
| USDJPY | long | 2026-10-19 | 2026-10-20 | 1 | 24 | zamknięta | SL | -35.0 |
| AUDUSD | long | 2026-10-20 | 2026-10-23 | 3 | 72 | zamknięta | czas | 23.8 |
| EURUSD | short | 2026-10-22 | 2026-10-27 | 5 | 72 | zamknięta | czas | 61.7 |
| GBPUSD | short | 2026-10-22 | 2026-10-22 | 0 | 6 | zamknięta | SL | -22.9 |
| AUDUSD | long | 2026-10-23 | 2026-10-26 | 3 | 22 | zamknięta | SL | -15.5 |
| GBPUSD | short | 2026-10-26 | 2026-10-28 | 2 | 48 | zamknięta | TP | 80.3 |
| AUDUSD | short | 2026-10-26 | 2026-10-27 | 0 | 13 | zamknięta | SL | -14.1 |
| EURJPY | short | 2026-10-27 | 2026-10-28 | 1 | 29 | zamknięta | SL | -41.7 |
| AUDUSD | long | 2026-10-27 | 2026-10-29 | 2 | 47 | zamknięta | SL | -18.5 |
| USDJPY | long | 2026-10-28 | 2026-10-28 | 0 | 6 | zamknięta | SL | -26.5 |
| EURJPY | long | 2026-10-28 | 2026-10-29 | 1 | 16 | zamknięta | SL | -38.5 |
| EURGBP | short | 2026-10-29 | 2026-10-30 | 1 | 30 | zamknięta | TP | 32.7 |
| USDJPY | long | 2026-11-03 | 2026-11-04 | 1 | 16 | zamknięta | SL | -31.2 |
| EURGBP | long | 2026-11-09 | 2026-11-12 | 3 | 72 | zamknięta | czas | 8.2 |
| EURJPY | long | 2026-11-09 | 2026-11-12 | 3 | 72 | zamknięta | czas | 1.4 |
| USDJPY | long | 2026-11-10 | 2026-11-11 | 1 | 26 | zamknięta | TP | 105.4 |
| GBPUSD | short | 2026-11-12 | 2026-11-17 | 5 | 72 | zamknięta | czas | 28.4 |
| USDCHF | long | 2026-11-12 | 2026-11-16 | 4 | 41 | zamknięta | TP | 63.0 |
| USDJPY | short | 2026-11-17 | 2026-11-17 | 0 | 8 | zamknięta | SL | -31.6 |
| USDJPY | long | 2026-11-19 | 2026-11-20 | 1 | 17 | zamknięta | SL | -33.9 |
| EURUSD | long | 2026-11-19 | 2026-11-19 | 0 | 11 | zamknięta | SL | -20.2 |
| USDCHF | short | 2026-11-20 | 2026-11-23 | 3 | 28 | zamknięta | SL | -19.5 |
| EURJPY | long | 2026-11-27 | 2026-11-27 | 0 | 8 | zamknięta | SL | -29.0 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 476); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 0.48 pips/transakcję, percentyl **76.4** (losowe: 5%=-6.74, mediana=-1.87, 95%=3.52).

- **Deflated Sharpe Ratio**: 0.419 (Sharpe na transakcję 0.003, próg przy 3 próbach 0.014).

- **PBO** (CSCV, 16 bloków, 3 wariantów): 0.969 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 338 transakcji, śr. -0.61 pips, -0.04 R.

- **Bootstrap 95%** średnich pipsów: całość [-3.83; 5.45], OOS [-6.35; 6.44].

- **Spread**: ×1 0.48, ×1,5 -0.33, ×2 -1.14 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 1.4 nocy na transakcję, 60% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -0.24, 1 pips: -0.96 pips/transakcję.

- **Korelacja z innymi strategiami** (D-075, tygodniowe sumy R najlepszego wariantu, min. 26 wspólnych tygodni): 5 X EMA +0.37, Alma v.1 +0.20, d1 +0.18, RSI jedna para +0.16, Combined 1 +0.15, RSI w wyraźnym trendzie +0.14, clean average +0.14, H4 +0.14. Niska (|r| < 0,3) = dobry składnik księgi.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Swapy: tabela 0 (O5: swapy = 0, tabela niewypełniona) (D-075; przy 0 — pominięte, O5). Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

import numpy as np
import pandas as pd

HYPOTHESIS = """Wybicie z ściśnięcia z celem dopasowanym do prognozy zasięgu (D-076, zakładka Zasięg).
Kierunku nie przewidujemy — przewidujemy, JAK DALEKO rynek może dojść: zmienność skupia się w czasie i wraca do średniej,
więc zasięg najbliższych 3 dni da się prognozować (model HAR na dziennych zakresach, ind.range_forecast). Gdy na H1 rynek
stoi w wąskim pudełku z 24 godzin (wysokość w dolnych 20% z ostatnich 500 godzin), zlecenia stoją po obu stronach i to
wybicie wybiera kierunek: zamknięcie godziny nad pudełkiem = long, pod nim = short. Stop za drugą stroną pudełka
(gdy cel byłby wtedy nieosiągalny — w połowie pudełka), cel = 2 / 3 / 4 × stop. Wejście tylko wtedy, gdy cel mieści się
w prognozowanym zasięgu 3 dni — inaczej TP 3 × SL i tak zwykle by nie padł. Płatnik: uczestnicy, których stopy i zlecenia
stoją tuż za granicą konsolidacji, a po wybiciu muszą gonić cenę."""

PARAMS = {"tp": [2, 3, 4]}     # TP = tyle × odległość do SL (3 = reguła Michała, 2 i 4 — porównanie)
BOX, REF, PCT = 24, 500, 20    # pudełko z 24 godzin; ściśnięte = wysokość w dolnych 20% z ostatnich 500 godzin
H = 3                          # prognoza zasięgu na 3 najbliższe dni
EXITS = [{"kind": "level", "cap": 72}]   # TP i SL z levels(); najwyżej 72 godziny (horyzont prognozy)


def _ksiega(df, p, ind):
    """Kierunek (+1/−1/0) i ceny SL/TP na zamknięciu świecy sygnału."""
    n = len(df)
    zero = np.zeros(n)
    d = ind.d1(df)
    if d is None or len(d) < 300:
        return zero, np.full(n, np.nan), np.full(n, np.nan)
    zasieg = ind.d1_to_h1(df, ind.range_forecast(d, H)["mid"]).to_numpy(float)   # prognoza 3 dni, znana od zamknięcia dnia
    sq = ind.squeeze(df, BOX, REF)
    up, lo, pct = (sq[k].shift(1).to_numpy(float) for k in ("upper", "lower", "pct"))   # pudełko SPRZED świecy wybicia
    c = df["close"].to_numpy(float)
    m = float(p["tp"])
    with np.errstate(invalid="ignore"):
        scisk = pct <= PCT
        dlugi = scisk & (c > up)
        krotki = scisk & (c < lo)
        srodek = (up + lo) / 2
        sl = np.where(dlugi, lo, np.where(krotki, up, np.nan))
        # stop za drugą stroną; gdy cel byłby poza prognozą zasięgu — stop w połowie pudełka
        za_daleko = m * np.abs(c - sl) > zasieg
        sl = np.where(za_daleko, srodek, sl)
        ryzyko = np.abs(c - sl)
        ok = (dlugi | krotki) & (ryzyko > 0) & (m * ryzyko <= zasieg)
    kier = np.where(ok, np.where(dlugi, 1, -1), 0)
    tp = np.where(ok, c + kier * m * ryzyko, np.nan)
    return kier, np.where(ok, sl, np.nan), tp


def signals(df, p, ind):
    kier, _, _ = _ksiega(df, p, ind)
    return pd.Series(kier, index=df.index).astype("int8")


def levels(df, p, ind):
    _, sl, tp = _ksiega(df, p, ind)
    return pd.DataFrame({"tp": tp, "sl": sl}, index=df.index)

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?

## Eksploracja Maca (D-072)

Mac sprawdził 53 odmian (18 rodzajów). 5 kandydatów otwartych na OOS — żaden nie przetrwał.

Rodzaje odmian: adx_silny, adx_slaby, cofniecie20, odwrocony, odwrocony+przeciw200, odwrocony+trend50, odwrocony+tylko_long, oryginal, przeciw200, przeciw200+tylko_long, siatka, trend200, trend50, tylko_long, tylko_long+trend50, tylko_short, zmiennosc_niska, zmiennosc_wysoka. Prób (wariantów) łącznie: 53. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): poziomy TP/SL ze strategii, max 72, {'tp': 2} — IS 491 trans., śr. R -0.010, ocena -0.008; OOS 148 trans., śr. R +0.135.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | odwrócony sygnał + tylko przeciw trendowi SMA200 {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 331 | +4.351 | 134 | +2.455 | +18.68 | +1.000 | 0 | — | nie przetrwała OOS |
| 2 | odwrócony sygnał {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 507 | +4.104 | 175 | +2.387 | +18.52 | +1.000 | 0 | — | nie przetrwała OOS |
| 3 | odwrócony sygnał + tylko long {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 242 | +3.954 | 63 | +2.142 | +17.46 | +1.000 | 0 | — | nie przetrwała OOS |
| 4 | tylko przeciw trendowi SMA200 + tylko long {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 61 | +0.101 | 7 | -1.115 | -18.89 | +0.000 | 85 | — | za mało transakcji OOS |
| 5 | tylko przeciw trendowi SMA200 {'tp': 2} | poziomy TP/SL ze strategii, max 72 | 192 | +0.057 | 48 | -0.174 | -5.06 | +0.000 | 93 | — | nie przetrwała OOS |

