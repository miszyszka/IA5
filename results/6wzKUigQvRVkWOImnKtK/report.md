# Raport strategii: D4

Run `20261111-113756` · silnik 0.13.0 · kod `eacbc8e0c92d8c83` · dane `3197cf8521901cb3`

## Werdykt: 🟢 ZIELONY — wszystkie testy zaliczone

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 516.07 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✔ | 1.00 |
| dodatni przy spreadzie ×1,5 | ✔ | 648.31 |

## Hipoteza

Kurs, który spadł o co najmniej 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Tylko long (cena ≥ 5% poniżej średniej). Jedno wejście na tydzień (co najmniej 5 dni handlu od poprzedniego
w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop lossa i bez limitu czasu.
Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 10 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 1%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 468 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 2.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, bez limitu czasu | — | 64 | 8.31 | 846.63 | 100.0 | 95 | 5.64 | 516.07 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, bez limitu czasu (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 47 | 511.7 | 24 052.2 | 100.0 |
| EURGBP | 4 | 471.8 | 1 887.3 | 100.0 |
| EURJPY | 20 | 923.8 | 18 475.3 | 100.0 |
| EURUSD | 28 | 951.7 | 26 647.5 | 100.0 |
| GBPUSD | 10 | 1 006.9 | 10 069.1 | 100.0 |
| USDCAD | 13 | 770.0 | 10 010.2 | 100.0 |
| USDCHF | 23 | 118.4 | 2 724.2 | 56.5 |
| USDJPY | 14 | 667.5 | 9 345.3 | 100.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2017 | 32 | 999.7 | 31 990.0 | 100.0 |
| 2018 | 12 | 669.3 | 8 031.4 | 100.0 |
| 2020 | 32 | 592.6 | 18 961.7 | 100.0 |
| 2021 | 4 | 572.2 | 2 288.8 | 100.0 |
| 2022 | 29 | 642.9 | 18 644.1 | 100.0 |
| 2023 | 10 | 577.1 | 5 771.3 | 100.0 |
| 2025 | 10 | 839.3 | 8 393.3 | 100.0 |
| 2026 | 30 | 304.3 | 9 130.4 | 66.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 64 | 846.6 | 54 184.4 | 100.0 |
| OOS | 95 | 516.1 | 49 026.7 | 89.5 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 97 717 | 877.2 | 25.6 | -13.5 | -95.7 | 1.18 | 0 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-11): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **139**, otwarte: **20** (razem 159).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 139 | 5 | 268 | 393 | 1 046 | 1 093 | 708.6 | 98 495 |
| OTWARTE na koniec danych | 20 | 1 063 | 2 400 | 2 387 | 3 636 | 3 649 | 235.8 | 4 716 |
| wszystkie | 159 | 5 | 309 | 644 | 1 169 | 3 649 | 649.1 | 103 211 |

Pozycje otwarte mają w tabeli poniżej status OTWARTA; ich wynik jest niezrealizowany (suma 4 716 pips netto).

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| AUDUSD | long | 2016-11-14 | 2017-09-08 | 299 | 211 | zamknięta | TP | 518.4 |
| EURJPY | long | 2016-11-14 | 2017-09-18 | 309 | 204 | zamknięta | TP | 1 663.7 |
| EURUSD | long | 2016-11-14 | 2017-08-29 | 289 | 200 | zamknięta | TP | 1 164.8 |
| GBPUSD | long | 2016-11-14 | 2026-11-11 | 3 649 | 2 528 | OTWARTA | otwarta | 863.2 |
| AUDUSD | long | 2016-11-21 | 2017-07-27 | 249 | 176 | zamknięta | TP | 733.7 |
| EURJPY | long | 2016-11-21 | 2017-09-18 | 302 | 199 | zamknięta | TP | 1 477.7 |
| GBPUSD | long | 2016-11-21 | 2026-11-11 | 3 642 | 2 523 | OTWARTA | otwarta | 1 117.4 |
| EURUSD | long | 2016-11-22 | 2017-08-28 | 280 | 194 | zamknięta | TP | 1 332.3 |
| AUDUSD | long | 2016-11-28 | 2017-07-27 | 242 | 171 | zamknięta | TP | 605.4 |
| EURJPY | long | 2016-11-28 | 2017-09-18 | 295 | 194 | zamknięta | TP | 1 256.0 |
| GBPUSD | long | 2016-11-28 | 2026-11-11 | 3 635 | 2 518 | OTWARTA | otwarta | 957.4 |
| EURUSD | long | 2016-11-29 | 2017-08-28 | 273 | 189 | zamknięta | TP | 1 331.7 |
| AUDUSD | long | 2016-12-05 | 2017-07-27 | 235 | 166 | zamknięta | TP | 597.3 |
| GBPUSD | long | 2016-12-05 | 2026-11-11 | 3 628 | 2 513 | OTWARTA | otwarta | 770.8 |
| EURJPY | long | 2016-12-06 | 2017-09-18 | 287 | 189 | zamknięta | TP | 949.2 |
| EURUSD | long | 2016-12-06 | 2017-08-28 | 266 | 184 | zamknięta | TP | 1 174.9 |
| AUDUSD | long | 2016-12-12 | 2017-07-27 | 228 | 161 | zamknięta | TP | 577.3 |
| GBPUSD | long | 2016-12-12 | 2026-11-11 | 3 621 | 2 508 | OTWARTA | otwarta | 847.4 |
| EURJPY | long | 2016-12-13 | 2017-09-13 | 275 | 182 | zamknięta | TP | 956.0 |
| EURUSD | long | 2016-12-13 | 2017-08-28 | 259 | 179 | zamknięta | TP | 1 272.0 |
| AUDUSD | long | 2016-12-19 | 2017-07-27 | 221 | 156 | zamknięta | TP | 724.6 |
| GBPUSD | long | 2016-12-19 | 2026-11-11 | 3 614 | 2 503 | OTWARTA | otwarta | 951.2 |
| EURJPY | long | 2016-12-20 | 2017-09-13 | 268 | 177 | zamknięta | TP | 1 005.8 |
| EURUSD | long | 2016-12-20 | 2017-08-28 | 252 | 174 | zamknięta | TP | 1 490.0 |
| AUDUSD | long | 2016-12-26 | 2017-07-27 | 214 | 151 | zamknięta | TP | 828.4 |
| GBPUSD | long | 2016-12-26 | 2026-11-11 | 3 607 | 2 498 | OTWARTA | otwarta | 1 150.7 |
| EURJPY | long | 2016-12-27 | 2017-09-13 | 261 | 172 | zamknięta | TP | 920.1 |
| EURUSD | long | 2016-12-27 | 2017-08-03 | 220 | 152 | zamknięta | TP | 1 417.8 |
| AUDUSD | long | 2017-01-02 | 2017-07-27 | 207 | 146 | zamknięta | TP | 784.3 |
| GBPUSD | long | 2017-01-02 | 2026-11-11 | 3 600 | 2 493 | OTWARTA | otwarta | 1 091.2 |
| EURJPY | long | 2017-01-03 | 2017-08-30 | 240 | 158 | zamknięta | TP | 875.0 |
| EURUSD | long | 2017-01-04 | 2017-08-02 | 211 | 146 | zamknięta | TP | 1 433.6 |
| AUDUSD | long | 2017-01-09 | 2017-07-20 | 193 | 136 | zamknięta | TP | 670.2 |
| GBPUSD | long | 2017-01-10 | 2026-11-11 | 3 592 | 2 488 | OTWARTA | otwarta | 1 268.9 |
| EURJPY | long | 2017-01-11 | 2017-08-30 | 232 | 153 | zamknięta | TP | 921.3 |
| EURUSD | long | 2017-01-11 | 2017-08-01 | 203 | 140 | zamknięta | TP | 1 276.9 |
| AUDUSD | long | 2017-01-16 | 2017-07-20 | 186 | 131 | zamknięta | TP | 471.3 |
| EURJPY | long | 2017-01-18 | 2017-08-02 | 197 | 129 | zamknięta | TP | 1 055.9 |
| EURUSD | long | 2017-01-18 | 2017-07-31 | 195 | 134 | zamknięta | TP | 1 112.4 |
| GBPUSD | long | 2017-01-18 | 2026-11-11 | 3 584 | 2 483 | OTWARTA | otwarta | 1 050.8 |
| USDCAD | long | 2017-09-10 | 2017-10-27 | 47 | 35 | zamknięta | TP | 714.8 |
| USDCAD | long | 2017-09-17 | 2017-10-27 | 40 | 30 | zamknięta | TP | 677.3 |
| USDCAD | long | 2018-01-30 | 2018-03-16 | 45 | 33 | zamknięta | TP | 679.6 |
| USDCHF | long | 2018-02-05 | 2018-04-24 | 79 | 57 | zamknięta | TP | 466.6 |
| USDJPY | long | 2018-02-15 | 2018-10-01 | 229 | 150 | zamknięta | TP | 719.2 |
| USDCHF | long | 2018-02-16 | 2018-04-24 | 68 | 48 | zamknięta | TP | 561.3 |
| USDJPY | long | 2018-02-22 | 2018-10-01 | 222 | 145 | zamknięta | TP | 606.6 |
| USDJPY | long | 2018-03-02 | 2018-09-28 | 211 | 139 | zamknięta | TP | 744.4 |
| USDJPY | long | 2018-03-09 | 2018-09-28 | 204 | 134 | zamknięta | TP | 714.0 |
| USDJPY | long | 2018-03-19 | 2018-09-28 | 194 | 129 | zamknięta | TP | 749.8 |
| USDJPY | long | 2018-03-25 | 2018-09-28 | 187 | 124 | zamknięta | TP | 855.0 |
| USDJPY | long | 2018-04-01 | 2018-09-27 | 179 | 118 | zamknięta | TP | 698.3 |
| USDJPY | long | 2018-04-08 | 2018-09-27 | 172 | 113 | zamknięta | TP | 627.0 |
| USDJPY | long | 2018-04-17 | 2018-07-19 | 93 | 61 | zamknięta | TP | 609.6 |
| AUDUSD | long | 2018-09-10 | 2020-12-11 | 822 | 560 | zamknięta | TP | 415.5 |
| AUDUSD | long | 2018-09-17 | 2020-12-11 | 815 | 555 | zamknięta | TP | 380.0 |
| AUDUSD | long | 2018-10-04 | 2020-12-12 | 799 | 543 | zamknięta | TP | 446.8 |
| AUDUSD | long | 2018-10-11 | 2020-12-12 | 792 | 538 | zamknięta | TP | 402.6 |
| AUDUSD | long | 2018-10-18 | 2020-12-12 | 785 | 533 | zamknięta | TP | 430.3 |
| AUDUSD | long | 2018-10-25 | 2020-12-11 | 777 | 527 | zamknięta | TP | 445.4 |
| AUDUSD | long | 2018-11-02 | 2020-12-11 | 770 | 522 | zamknięta | TP | 319.9 |
| AUDUSD | long | 2018-12-21 | 2020-12-12 | 722 | 489 | zamknięta | TP | 408.8 |
| AUDUSD | long | 2018-12-31 | 2020-12-12 | 712 | 484 | zamknięta | TP | 482.4 |
| AUDUSD | long | 2019-01-09 | 2020-12-11 | 702 | 478 | zamknięta | TP | 362.1 |
| EURJPY | long | 2019-08-04 | 2020-08-06 | 368 | 247 | zamknięta | TP | 711.3 |
| EURJPY | long | 2019-08-11 | 2020-08-06 | 361 | 242 | zamknięta | TP | 740.4 |
| EURJPY | long | 2019-08-19 | 2020-08-12 | 359 | 240 | zamknięta | TP | 744.9 |
| EURJPY | long | 2019-08-27 | 2020-08-12 | 351 | 235 | zamknięta | TP | 828.7 |
| EURJPY | long | 2019-09-04 | 2020-08-12 | 343 | 230 | zamknięta | TP | 821.7 |
| EURJPY | long | 2019-09-11 | 2020-08-12 | 336 | 225 | zamknięta | TP | 663.9 |
| EURJPY | long | 2019-09-22 | 2020-08-12 | 325 | 218 | zamknięta | TP | 704.3 |
| EURJPY | long | 2019-09-29 | 2020-08-12 | 318 | 213 | zamknięta | TP | 759.0 |
| EURJPY | long | 2019-10-06 | 2020-08-12 | 311 | 208 | zamknięta | TP | 844.0 |
| EURJPY | long | 2019-11-18 | 2020-08-12 | 269 | 180 | zamknięta | TP | 576.6 |
| EURGBP | long | 2019-12-16 | 2020-03-12 | 87 | 58 | zamknięta | TP | 464.7 |
| EURUSD | long | 2020-02-14 | 2020-03-10 | 25 | 16 | zamknięta | TP | 609.6 |
| EURGBP | long | 2020-02-17 | 2020-03-12 | 24 | 17 | zamknięta | TP | 484.0 |
| EURUSD | long | 2020-02-24 | 2020-03-10 | 15 | 11 | zamknięta | TP | 618.4 |
| USDCHF | long | 2020-03-10 | 2020-03-20 | 10 | 8 | zamknięta | TP | 544.1 |
| USDJPY | long | 2020-03-10 | 2020-03-21 | 11 | 8 | zamknięta | TP | 732.6 |
| EURUSD | long | 2020-03-23 | 2020-07-21 | 121 | 81 | zamknięta | TP | 780.4 |
| EURUSD | long | 2020-04-05 | 2020-07-21 | 107 | 72 | zamknięta | TP | 661.5 |
| EURUSD | long | 2020-04-19 | 2020-07-21 | 93 | 62 | zamknięta | TP | 606.8 |
| EURUSD | long | 2020-04-26 | 2020-07-21 | 86 | 57 | zamknięta | TP | 649.2 |
| EURUSD | long | 2020-05-06 | 2020-07-21 | 76 | 50 | zamknięta | TP | 671.8 |
| EURUSD | long | 2020-05-13 | 2020-07-21 | 69 | 45 | zamknięta | TP | 650.0 |
| USDCHF | long | 2020-07-23 | 2022-05-04 | 650 | 456 | zamknięta | TP | 544.7 |
| USDCHF | long | 2020-07-30 | 2022-05-04 | 643 | 451 | zamknięta | TP | 710.4 |
| USDCHF | long | 2020-08-09 | 2022-05-04 | 633 | 446 | zamknięta | TP | 666.4 |
| USDCHF | long | 2020-08-17 | 2022-05-03 | 624 | 440 | zamknięta | TP | 723.6 |
| USDCHF | long | 2020-08-24 | 2022-05-03 | 617 | 435 | zamknięta | TP | 665.9 |
| USDCHF | long | 2020-08-31 | 2022-05-02 | 609 | 429 | zamknięta | TP | 742.0 |
| USDCHF | long | 2020-09-07 | 2022-05-02 | 602 | 424 | zamknięta | TP | 613.6 |
| USDCHF | long | 2020-09-15 | 2022-05-02 | 594 | 419 | zamknięta | TP | 687.6 |
| USDCHF | long | 2020-09-22 | 2022-05-02 | 587 | 414 | zamknięta | TP | 575.7 |
| USDCHF | long | 2020-09-29 | 2022-05-02 | 580 | 409 | zamknięta | TP | 575.2 |
| USDJPY | long | 2020-11-09 | 2021-03-16 | 127 | 86 | zamknięta | TP | 608.9 |
| USDJPY | long | 2020-12-17 | 2021-03-10 | 83 | 57 | zamknięta | TP | 561.1 |
| USDJPY | long | 2020-12-24 | 2021-03-10 | 76 | 52 | zamknięta | TP | 548.8 |
| USDJPY | long | 2021-01-04 | 2021-03-10 | 65 | 47 | zamknięta | TP | 570.1 |
| USDCAD | long | 2021-02-26 | 2022-07-14 | 504 | 352 | zamknięta | TP | 600.9 |
| USDCAD | long | 2021-03-15 | 2022-07-14 | 487 | 341 | zamknięta | TP | 744.2 |
| USDCAD | long | 2021-03-22 | 2022-07-14 | 480 | 336 | zamknięta | TP | 688.4 |
| USDCAD | long | 2021-04-04 | 2022-07-14 | 466 | 326 | zamknięta | TP | 637.7 |
| USDCAD | long | 2021-04-12 | 2022-07-14 | 458 | 320 | zamknięta | TP | 639.7 |
| USDCAD | long | 2021-04-19 | 2022-07-14 | 451 | 315 | zamknięta | TP | 676.5 |
| USDCAD | long | 2021-04-26 | 2022-07-14 | 444 | 310 | zamknięta | TP | 802.3 |
| USDCAD | long | 2021-05-03 | 2022-07-14 | 437 | 305 | zamknięta | TP | 919.8 |
| USDCAD | long | 2021-05-10 | 2022-07-14 | 430 | 300 | zamknięta | TP | 1 102.3 |
| USDCAD | long | 2021-05-17 | 2022-07-14 | 423 | 295 | zamknięta | TP | 1 126.7 |
| EURGBP | long | 2022-03-07 | 2022-09-16 | 194 | 139 | zamknięta | TP | 500.4 |
| EURUSD | long | 2022-04-14 | 2025-04-11 | 1 093 | 761 | zamknięta | TP | 648.4 |
| EURGBP | long | 2022-04-17 | 2022-09-16 | 152 | 109 | zamknięta | TP | 438.2 |
| EURUSD | long | 2022-04-21 | 2025-04-11 | 1 086 | 756 | zamknięta | TP | 631.3 |
| EURUSD | long | 2022-05-01 | 2025-04-11 | 1 076 | 751 | zamknięta | TP | 927.5 |
| EURUSD | long | 2022-05-08 | 2025-04-11 | 1 069 | 746 | zamknięta | TP | 927.0 |
| EURUSD | long | 2022-05-15 | 2025-04-11 | 1 062 | 741 | zamknięta | TP | 1 053.9 |
| EURUSD | long | 2022-05-22 | 2025-04-11 | 1 055 | 736 | zamknięta | TP | 880.1 |
| EURUSD | long | 2022-05-29 | 2025-04-11 | 1 048 | 731 | zamknięta | TP | 715.2 |
| EURUSD | long | 2022-06-05 | 2025-04-11 | 1 041 | 726 | zamknięta | TP | 717.5 |
| EURUSD | long | 2022-06-12 | 2025-04-11 | 1 034 | 721 | zamknięta | TP | 949.4 |
| EURUSD | long | 2022-06-19 | 2025-04-11 | 1 027 | 716 | zamknięta | TP | 943.0 |
| AUDUSD | long | 2022-07-07 | 2022-10-10 | 95 | 67 | zamknięta | TP | 294.7 |
| AUDUSD | long | 2022-07-14 | 2022-10-10 | 88 | 62 | zamknięta | TP | 387.7 |
| AUDUSD | long | 2022-09-07 | 2022-10-10 | 33 | 23 | zamknięta | TP | 392.0 |
| AUDUSD | long | 2022-09-14 | 2022-10-10 | 26 | 18 | zamknięta | TP | 392.1 |
| AUDUSD | long | 2022-09-21 | 2022-10-10 | 19 | 13 | zamknięta | TP | 533.1 |
| AUDUSD | long | 2022-09-28 | 2022-10-10 | 12 | 8 | zamknięta | TP | 636.1 |
| AUDUSD | long | 2022-10-05 | 2022-10-10 | 5 | 3 | zamknięta | TP | 626.3 |
| AUDUSD | long | 2022-10-12 | 2023-01-27 | 106 | 76 | zamknięta | TP | 859.2 |
| AUDUSD | long | 2022-10-19 | 2023-01-27 | 99 | 71 | zamknięta | TP | 869.8 |
| AUDUSD | long | 2022-10-26 | 2023-01-27 | 92 | 66 | zamknięta | TP | 637.2 |
| AUDUSD | long | 2022-11-03 | 2023-01-27 | 85 | 61 | zamknięta | TP | 789.5 |
| AUDUSD | long | 2022-11-10 | 2023-01-27 | 78 | 56 | zamknięta | TP | 690.9 |
| AUDUSD | long | 2022-11-18 | 2023-01-27 | 70 | 50 | zamknięta | TP | 434.0 |
| AUDUSD | long | 2022-11-25 | 2023-01-27 | 63 | 45 | zamknięta | TP | 356.6 |
| AUDUSD | long | 2022-12-07 | 2023-01-27 | 51 | 37 | zamknięta | TP | 422.9 |
| AUDUSD | long | 2022-12-14 | 2023-01-27 | 44 | 32 | zamknięta | TP | 279.0 |
| AUDUSD | long | 2022-12-21 | 2023-01-27 | 37 | 27 | zamknięta | TP | 432.2 |
| AUDUSD | long | 2023-02-28 | 2026-02-12 | 1 080 | 737 | zamknięta | TP | 382.5 |
| AUDUSD | long | 2023-03-07 | 2026-02-12 | 1 073 | 732 | zamknięta | TP | 393.6 |
| AUDUSD | long | 2023-03-14 | 2026-02-12 | 1 066 | 727 | zamknięta | TP | 467.8 |
| AUDUSD | long | 2023-03-21 | 2026-02-12 | 1 059 | 722 | zamknięta | TP | 413.1 |
| AUDUSD | long | 2023-03-27 | 2026-02-13 | 1 053 | 718 | zamknięta | TP | 475.6 |
| AUDUSD | long | 2023-04-03 | 2026-02-13 | 1 046 | 713 | zamknięta | TP | 351.1 |
| AUDUSD | long | 2023-04-10 | 2026-02-13 | 1 039 | 708 | zamknięta | TP | 495.5 |
| AUDUSD | long | 2023-04-17 | 2026-03-11 | 1 058 | 720 | zamknięta | TP | 445.7 |
| AUDUSD | long | 2023-04-25 | 2026-03-11 | 1 050 | 715 | zamknięta | TP | 512.2 |
| AUDUSD | long | 2023-05-02 | 2026-03-11 | 1 043 | 710 | zamknięta | TP | 477.1 |
| USDCHF | long | 2023-07-12 | 2026-11-11 | 1 217 | 835 | OTWARTA | otwarta | -472.8 |
| USDCHF | long | 2023-07-19 | 2026-11-11 | 1 210 | 830 | OTWARTA | otwarta | -386.2 |
| USDCHF | long | 2023-07-27 | 2026-11-11 | 1 202 | 825 | OTWARTA | otwarta | -495.2 |
| USDCHF | long | 2023-08-06 | 2026-11-11 | 1 192 | 820 | OTWARTA | otwarta | -548.2 |
| USDCHF | long | 2023-08-13 | 2026-11-11 | 1 185 | 815 | OTWARTA | otwarta | -572.9 |
| USDCHF | long | 2023-08-20 | 2026-11-11 | 1 178 | 810 | OTWARTA | otwarta | -629.4 |
| USDCHF | long | 2023-08-31 | 2026-11-11 | 1 167 | 801 | OTWARTA | otwarta | -638.7 |
| USDCHF | long | 2023-11-30 | 2026-11-11 | 1 077 | 738 | OTWARTA | otwarta | -539.9 |
| USDCHF | long | 2023-12-07 | 2026-11-11 | 1 070 | 733 | OTWARTA | otwarta | -553.1 |
| USDCHF | long | 2023-12-14 | 2026-11-11 | 1 063 | 728 | OTWARTA | otwarta | -516.4 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 649.13 pips/transakcję, percentyl **100.0** (losowe: 5%=-87.93, mediana=75.55, 95%=251.07).

- **Deflated Sharpe Ratio**: 1.000 (Sharpe na transakcję 3.348, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 89 transakcji, śr. 500.18 pips, 5.40 R.

- **Bootstrap 95%** średnich pipsów: całość [583.84; 713.54], OOS [432.38; 593.81].

- **Spread**: ×1 649.13, ×1,5 648.31, ×2 647.50 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 644.2 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 327.02, 1 pips: 4.92 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

- **Pozycje otwarte (D-061, wyjście bez limitu czasu):** 20 z 159 transakcji (12.6%) nie zamknęło się do końca danych — liczone po ostatnim close jako wynik niezrealizowany; średnio 235.82 pips netto na pozycję. Wynik realny zależy od tego, czy cena jeszcze wróci do poziomu; nie ma stopu, więc przegrywająca pozycja trwa.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który spadł o co najmniej 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Tylko long (cena ≥ 5% poniżej średniej). Jedno wejście na tydzień (co najmniej 5 dni handlu od poprzedniego
w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop lossa i bez limitu czasu.
Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant: żadnych parametrów, jedno wyjście.
START = "2016-11-11"      # ostatnie 10 lat (stała data — sygnały wcześniejsze są wyzerowane)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)

PYRAMID = 10              # maksimum silnika: do 10 pozycji naraz w parze (w jednym kierunku)
SIZING = [1]              # zawsze 1% kapitału jako depozyt
EXITS = [{"kind": "level", "cap": 0}]     # TP = średnia (levels), bez SL i BEZ limitu czasu (D-061): zamknięcie tylko na średniej


def levels(df, p, ind):
    """Zamknięcie na przecięciu średniej: cel = średnia z 756 dni policzona na świecy sygnału. Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    dev = (df.close / sma - 1.0).to_numpy()
    live = (df.index >= pd.Timestamp(START, tz="UTC")) & np.isfinite(dev)
    below = live & (dev <= -BAND)     # tylko long
    out = np.zeros(len(dev))
    last = -10**9                     # tylko z przeszłości: najwyżej jedno wejście na GAP_DAYS dni
    for t in range(len(dev)):
        if t - last < GAP_DAYS:
            continue
        if below[t]:
            out[t], last = 1.0, t
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
