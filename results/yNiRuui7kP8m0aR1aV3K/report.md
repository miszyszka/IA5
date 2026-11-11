# Raport strategii: D4 v2

Run `20261111-220654` · silnik 0.13.0 · kod `a1509190cd142b7b` · dane `3197cf8521901cb3`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 3 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 481.68 |
| percentyl benchmarku ≥ 95 | ✔ | 98.30 |
| PBO < 0,3 | ✘ | 0.71 |
| DSR ≥ 0,95 | ✘ | 0.11 |
| dodatni przy spreadzie ×1,5 | ✔ | 39.24 |

## Hipoteza

Kurs, który spadł o co najmniej 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Tylko long (cena ≥ 5% poniżej średniej). Jedno wejście na tydzień (co najmniej 5 dni handlu od poprzedniego
w tej parze), do 3 pozycji naraz w parze. Cel = poziom średniej z dnia sygnału (stała cena), bez limitu czasu.
Wersja z zarządzaniem ryzykiem: STOP LOSS poniżej wejścia na odległość równą ułamkowi drogi do celu (0,5 / 0,75 / 1,0 ×
droga do średniej), więc z góry znany stosunek zysku do straty, a pozycja nie wisi latami na stracie. Każda pozycja
ma tę samą stratę przy stopie: ok. 0,5% kapitału (waga pozycji = 0,5% ÷ odległość do stopu), niezależnie od tego, jak
głęboko kurs jest pod średnią. Wszystko jak w wersji bez stopu, tylko ryzyko jest ograniczone i równe w każdej
transakcji. Cała dostępna historia D1 (ok. 27 lat sygnałów), żeby próba IS (ranking) i OOS (ostatnie 25%) miały dość transakcji.
Hipoteza zapisana PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 3 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 1%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 3** (3 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 1,939 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 49.3 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, bez limitu czasu | sl_gap=0.75 | 179 | -0.10 | -88.28 | 39.7 | 52 | 0.67 | 481.68 |
| 2 | poziomy TP/SL ze strategii, bez limitu czasu | sl_gap=1.0 | 158 | -0.10 | -94.95 | 44.3 | 30 | 0.76 | 621.49 |
| 3 | poziomy TP/SL ze strategii, bez limitu czasu | sl_gap=0.5 | 242 | -0.13 | -74.99 | 30.6 | 63 | 0.75 | 402.36 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, bez limitu czasu (sl_gap=0.75)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 33 | -48.6 | -1 602.9 | 42.4 |
| EURGBP | 18 | 229.4 | 4 128.6 | 55.6 |
| EURJPY | 16 | 109.1 | 1 744.9 | 43.8 |
| EURUSD | 42 | 264.2 | 11 094.7 | 54.8 |
| GBPUSD | 32 | -618.7 | -19 797.0 | 31.2 |
| USDCAD | 22 | 343.4 | 7 554.3 | 59.1 |
| USDCHF | 32 | -8.0 | -255.0 | 37.5 |
| USDJPY | 36 | 177.1 | 6 377.1 | 52.8 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2001 | 3 | 1 793.8 | 5 381.4 | 100.0 |
| 2003 | 1 | -328.5 | -328.5 | 0.0 |
| 2004 | 2 | -750.9 | -1 501.8 | 0.0 |
| 2005 | 3 | 1 373.7 | 4 121.2 | 100.0 |
| 2007 | 7 | -746.9 | -5 228.1 | 0.0 |
| 2008 | 29 | -104.2 | -3 020.7 | 31.0 |
| 2009 | 17 | 91.1 | 1 548.4 | 64.7 |
| 2010 | 15 | 363.3 | 5 448.8 | 46.7 |
| 2011 | 17 | -826.8 | -14 055.3 | 17.6 |
| 2012 | 12 | -1 143.7 | -13 724.8 | 0.0 |
| 2013 | 16 | 837.1 | 13 393.6 | 81.2 |
| 2014 | 5 | 326.7 | 1 633.3 | 60.0 |
| 2015 | 13 | -629.4 | -8 182.7 | 0.0 |
| 2016 | 18 | -218.4 | -3 930.6 | 33.3 |
| 2017 | 5 | 1 413.7 | 7 068.6 | 100.0 |
| 2018 | 4 | 687.5 | 2 749.8 | 100.0 |
| 2020 | 18 | 115.6 | 2 079.9 | 66.7 |
| 2021 | 4 | 316.8 | 1 267.1 | 75.0 |
| 2022 | 19 | -308.1 | -5 854.4 | 36.8 |
| 2023 | 9 | 1 270.7 | 11 436.0 | 77.8 |
| 2024 | 5 | 251.7 | 1 258.3 | 60.0 |
| 2025 | 3 | 1 450.3 | 4 351.0 | 100.0 |
| 2026 | 6 | 555.7 | 3 334.2 | 100.0 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 179 | -88.3 | -15 802.7 | 39.7 |
| OOS | 52 | 481.7 | 25 047.4 | 71.2 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 10 769 | 7.7 | 0.3 | -15.3 | -21.0 | 0.10 | 0 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-11): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **228**, otwarte: **3** (razem 231).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 228 | 1 | 139 | 314 | 821 | 5 346 | 33.5 | 7 641 |
| OTWARTE na koniec danych | 3 | 5 571 | 5 578 | 5 578 | 5 584 | 5 585 | 534.4 | 1 603 |
| wszystkie | 231 | 1 | 143 | 382 | 949 | 5 585 | 40.0 | 9 245 |

Pozycje otwarte mają w tabeli poniżej status OTWARTA; ich wynik jest niezrealizowany (suma 1 603 pips netto).

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDJPY | long | 1999-11-18 | 2001-03-16 | 484 | 344 | zamknięta | TP | 1 670.4 |
| USDJPY | long | 1999-11-25 | 2001-03-16 | 477 | 339 | zamknięta | TP | 1 752.8 |
| USDJPY | long | 1999-12-02 | 2001-03-16 | 470 | 334 | zamknięta | TP | 1 958.1 |
| USDJPY | long | 2003-09-21 | 2003-10-10 | 19 | 15 | zamknięta | SL | -328.5 |
| USDJPY | long | 2003-09-28 | 2004-03-31 | 185 | 131 | zamknięta | SL | -701.8 |
| USDJPY | long | 2003-10-05 | 2004-11-20 | 411 | 292 | zamknięta | SL | -800.0 |
| USDJPY | long | 2003-10-12 | 2005-12-06 | 785 | 556 | zamknięta | TP | 1 284.6 |
| USDJPY | long | 2004-04-06 | 2005-11-29 | 601 | 426 | zamknięta | TP | 1 399.6 |
| USDJPY | long | 2004-11-26 | 2005-11-03 | 342 | 242 | zamknięta | TP | 1 437.1 |
| USDCAD | long | 2006-08-21 | 2007-09-14 | 389 | 276 | zamknięta | SL | -885.5 |
| USDCAD | long | 2006-08-28 | 2007-09-18 | 386 | 273 | zamknięta | SL | -928.4 |
| USDCAD | long | 2006-09-04 | 2007-09-19 | 380 | 269 | zamknięta | SL | -947.5 |
| USDCAD | long | 2007-09-16 | 2007-11-07 | 51 | 37 | zamknięta | SL | -1 005.2 |
| USDCHF | long | 2007-09-20 | 2007-11-10 | 50 | 36 | zamknięta | SL | -490.1 |
| USDCAD | long | 2007-09-23 | 2008-10-10 | 383 | 267 | zamknięta | TP | 1 604.9 |
| USDCHF | long | 2007-09-27 | 2007-11-09 | 42 | 30 | zamknięta | SL | -475.6 |
| USDCAD | long | 2007-09-30 | 2008-10-10 | 376 | 262 | zamknięta | TP | 1 644.3 |
| USDCHF | long | 2007-10-18 | 2007-11-10 | 22 | 16 | zamknięta | SL | -495.9 |
| USDCHF | long | 2007-11-09 | 2008-03-01 | 113 | 77 | zamknięta | SL | -817.2 |
| USDCAD | long | 2007-11-12 | 2008-10-09 | 333 | 231 | zamknięta | TP | 2 032.1 |
| USDCHF | long | 2007-11-16 | 2008-03-04 | 109 | 73 | zamknięta | SL | -892.9 |
| USDJPY | long | 2007-11-22 | 2008-03-04 | 103 | 66 | zamknięta | SL | -529.4 |
| USDCHF | long | 2007-11-23 | 2008-03-15 | 113 | 77 | zamknięta | SL | -1 006.5 |
| USDJPY | long | 2008-01-07 | 2008-03-01 | 54 | 38 | zamknięta | SL | -471.1 |
| USDJPY | long | 2008-01-14 | 2008-03-01 | 47 | 33 | zamknięta | SL | -446.8 |
| USDCHF | long | 2008-03-06 | 2008-11-22 | 261 | 184 | zamknięta | TP | 1 924.2 |
| USDCHF | long | 2008-03-13 | 2008-11-22 | 254 | 179 | zamknięta | TP | 2 125.4 |
| USDCHF | long | 2008-03-20 | 2008-11-21 | 246 | 173 | zamknięta | TP | 2 293.9 |
| GBPUSD | long | 2008-09-01 | 2008-10-10 | 39 | 29 | zamknięta | SL | -921.6 |
| USDJPY | long | 2008-09-01 | 2008-10-06 | 35 | 25 | zamknięta | SL | -485.8 |
| GBPUSD | long | 2008-09-08 | 2008-10-22 | 44 | 30 | zamknięta | SL | -1 152.0 |
| USDJPY | long | 2008-09-08 | 2008-10-06 | 28 | 20 | zamknięta | SL | -479.3 |
| GBPUSD | long | 2008-09-15 | 2008-10-09 | 24 | 18 | zamknięta | SL | -872.8 |
| USDJPY | long | 2008-09-15 | 2008-10-23 | 38 | 28 | zamknięta | SL | -768.9 |
| EURJPY | long | 2008-10-02 | 2008-10-06 | 4 | 2 | zamknięta | SL | -660.4 |
| USDJPY | long | 2008-10-06 | 2008-10-24 | 18 | 14 | zamknięta | SL | -941.7 |
| EURJPY | long | 2008-10-09 | 2008-10-24 | 15 | 10 | zamknięta | SL | -1 409.2 |
| USDJPY | long | 2008-10-13 | 2008-10-24 | 11 | 9 | zamknięta | SL | -906.2 |
| GBPUSD | long | 2008-10-14 | 2008-10-23 | 9 | 6 | zamknięta | SL | -1 295.4 |
| EURJPY | long | 2008-10-19 | 2008-10-24 | 5 | 5 | zamknięta | SL | -1 273.2 |
| EURUSD | long | 2008-10-22 | 2008-12-09 | 47 | 33 | zamknięta | TP | 725.1 |
| GBPUSD | long | 2008-10-22 | 2009-01-21 | 90 | 62 | zamknięta | SL | -2 205.7 |
| EURJPY | long | 2008-10-27 | 2023-06-16 | 5 346 | 3 608 | zamknięta | TP | 3 541.4 |
| USDJPY | long | 2008-10-28 | 2011-07-29 | 1 005 | 700 | zamknięta | SL | -1 577.4 |
| GBPUSD | long | 2008-10-30 | 2009-01-21 | 83 | 57 | zamknięta | SL | -2 064.4 |
| EURUSD | long | 2008-10-31 | 2008-12-09 | 39 | 27 | zamknięta | TP | 666.8 |
| EURJPY | long | 2008-11-03 | 2011-09-22 | 1 054 | 726 | zamknięta | SL | -2 247.4 |
| USDJPY | long | 2008-11-04 | 2008-12-18 | 44 | 31 | zamknięta | SL | -1 121.8 |
| GBPUSD | long | 2008-11-06 | 2012-01-28 | 1 178 | 812 | zamknięta | SL | -2 455.1 |
| EURUSD | long | 2008-11-07 | 2008-12-09 | 32 | 22 | zamknięta | TP | 858.6 |
| EURJPY | long | 2008-11-10 | 2011-09-22 | 1 047 | 721 | zamknięta | SL | -2 380.3 |
| USDJPY | long | 2008-11-11 | 2009-11-27 | 381 | 268 | zamknięta | SL | -1 194.4 |
| USDCHF | long | 2008-12-17 | 2008-12-18 | 1 | 1 | zamknięta | SL | -443.8 |
| USDCHF | long | 2008-12-24 | 2009-02-19 | 57 | 39 | zamknięta | TP | 900.0 |
| USDCHF | long | 2009-01-02 | 2009-02-11 | 40 | 28 | zamknięta | TP | 1 118.5 |
| USDJPY | long | 2009-01-05 | 2011-08-19 | 957 | 669 | zamknięta | SL | -1 593.1 |
| USDCHF | long | 2009-01-09 | 2009-02-11 | 33 | 23 | zamknięta | TP | 811.4 |
| EURUSD | long | 2009-01-21 | 2009-03-20 | 58 | 41 | zamknięta | TP | 760.2 |
| GBPUSD | long | 2009-01-26 | 2012-01-28 | 1 097 | 757 | zamknięta | SL | -3 709.1 |
| EURUSD | long | 2009-01-30 | 2009-03-20 | 49 | 34 | zamknięta | TP | 715.7 |
| GBPUSD | long | 2009-02-02 | 2012-01-28 | 1 090 | 752 | zamknięta | SL | -3 084.4 |
| EURUSD | long | 2009-02-06 | 2009-03-20 | 42 | 29 | zamknięta | TP | 868.8 |
| EURUSD | long | 2009-04-20 | 2009-05-20 | 30 | 22 | zamknięta | TP | 798.6 |
| AUDUSD | long | 2009-04-26 | 2009-06-01 | 36 | 26 | zamknięta | TP | 907.4 |
| EURUSD | long | 2009-04-27 | 2009-05-20 | 23 | 17 | zamknięta | TP | 707.7 |
| AUDUSD | long | 2009-05-03 | 2009-06-01 | 29 | 21 | zamknięta | TP | 740.8 |
| AUDUSD | long | 2009-05-10 | 2009-06-01 | 22 | 16 | zamknięta | TP | 400.4 |
| USDCHF | long | 2009-05-20 | 2009-09-08 | 111 | 72 | zamknięta | SL | -546.9 |
| USDCHF | long | 2009-05-27 | 2009-09-09 | 105 | 68 | zamknięta | SL | -512.9 |
| USDCHF | long | 2009-06-03 | 2009-10-22 | 141 | 89 | zamknięta | SL | -656.9 |
| USDCHF | long | 2009-09-15 | 2010-05-17 | 244 | 167 | zamknięta | TP | 1 112.0 |
| USDCHF | long | 2009-09-23 | 2010-05-17 | 236 | 162 | zamknięta | TP | 1 119.7 |
| USDCAD | long | 2009-10-11 | 2010-04-07 | 178 | 126 | zamknięta | SL | -364.9 |
| USDCAD | long | 2009-10-18 | 2011-01-04 | 442 | 311 | zamknięta | SL | -379.3 |
| USDCHF | long | 2009-10-28 | 2010-05-17 | 202 | 142 | zamknięta | TP | 1 151.9 |
| USDJPY | long | 2009-12-16 | 2011-07-27 | 589 | 407 | zamknięta | SL | -1 189.1 |
| USDCAD | long | 2010-01-07 | 2011-01-13 | 371 | 262 | zamknięta | SL | -449.8 |
| EURUSD | long | 2010-03-25 | 2010-05-06 | 43 | 31 | zamknięta | SL | -608.8 |
| EURUSD | long | 2010-04-06 | 2010-05-05 | 29 | 21 | zamknięta | SL | -557.5 |
| USDCAD | long | 2010-04-11 | 2010-05-25 | 44 | 32 | zamknięta | TP | 782.8 |
| EURUSD | long | 2010-04-20 | 2010-05-05 | 15 | 11 | zamknięta | SL | -536.9 |
| EURUSD | long | 2010-05-11 | 2010-10-15 | 157 | 111 | zamknięta | TP | 1 505.9 |
| EURUSD | long | 2010-05-18 | 2010-10-15 | 150 | 106 | zamknięta | TP | 1 947.2 |
| EURUSD | long | 2010-05-25 | 2010-10-15 | 143 | 101 | zamknięta | TP | 1 779.2 |
| USDCAD | long | 2010-06-20 | 2011-03-01 | 253 | 177 | zamknięta | SL | -429.0 |
| USDCHF | long | 2010-07-29 | 2010-09-14 | 47 | 32 | zamknięta | SL | -416.0 |
| USDCHF | long | 2010-08-10 | 2010-09-14 | 35 | 25 | zamknięta | SL | -515.6 |
| USDCHF | long | 2010-08-22 | 2010-09-22 | 31 | 23 | zamknięta | SL | -472.3 |
| USDCHF | long | 2010-09-19 | 2010-10-06 | 17 | 13 | zamknięta | SL | -478.1 |
| USDCHF | long | 2010-09-26 | 2011-03-18 | 172 | 122 | zamknięta | SL | -815.9 |
| USDCHF | long | 2010-10-03 | 2011-03-18 | 165 | 117 | zamknięta | SL | -730.9 |
| USDCHF | long | 2010-10-10 | 2011-04-25 | 197 | 138 | zamknięta | SL | -843.1 |
| EURUSD | long | 2010-11-30 | 2011-03-05 | 95 | 62 | zamknięta | TP | 902.5 |
| EURUSD | long | 2010-12-08 | 2011-03-05 | 87 | 56 | zamknięta | TP | 744.0 |
| EURUSD | long | 2010-12-17 | 2011-03-05 | 78 | 49 | zamknięta | TP | 738.2 |
| USDCAD | long | 2011-01-06 | 2014-01-09 | 1 099 | 764 | zamknięta | TP | 833.9 |
| USDCAD | long | 2011-01-13 | 2014-01-09 | 1 092 | 759 | zamknięta | TP | 934.4 |
| USDCAD | long | 2011-03-04 | 2014-01-09 | 1 042 | 724 | zamknięta | TP | 1 067.4 |
| USDCHF | long | 2011-03-23 | 2011-07-29 | 129 | 92 | zamknięta | SL | -1 160.0 |
| USDCHF | long | 2011-03-29 | 2011-07-25 | 118 | 83 | zamknięta | SL | -1 117.6 |
| USDCHF | long | 2011-04-27 | 2011-08-10 | 105 | 75 | zamknięta | SL | -1 527.3 |
| USDCHF | long | 2011-07-27 | 2026-11-11 | 5 585 | 3 862 | OTWARTA | otwarta | 179.7 |
| USDJPY | long | 2011-08-01 | 2013-01-26 | 543 | 369 | zamknięta | TP | 1 284.6 |
| USDCHF | long | 2011-08-03 | 2026-11-11 | 5 578 | 3 857 | OTWARTA | otwarta | 488.3 |
| USDJPY | long | 2011-08-08 | 2013-01-19 | 529 | 360 | zamknięta | TP | 1 247.3 |
| USDCHF | long | 2011-08-10 | 2026-11-11 | 5 571 | 3 852 | OTWARTA | otwarta | 935.3 |
| USDJPY | long | 2011-08-22 | 2013-01-19 | 515 | 350 | zamknięta | TP | 1 279.3 |
| EURJPY | long | 2011-09-29 | 2013-01-26 | 484 | 325 | zamknięta | TP | 1 690.3 |
| EURJPY | long | 2011-10-06 | 2013-01-26 | 477 | 320 | zamknięta | TP | 1 789.9 |
| EURUSD | long | 2011-12-15 | 2012-01-28 | 44 | 32 | zamknięta | SL | -492.3 |
| EURUSD | long | 2011-12-30 | 2012-01-28 | 29 | 21 | zamknięta | SL | -610.7 |
| EURUSD | long | 2012-01-06 | 2012-01-28 | 22 | 16 | zamknięta | SL | -439.1 |
| EURGBP | long | 2012-01-10 | 2012-07-10 | 183 | 128 | zamknięta | SL | -352.6 |
| EURGBP | long | 2012-01-17 | 2012-07-06 | 172 | 121 | zamknięta | SL | -334.0 |
| EURGBP | long | 2012-04-19 | 2012-07-16 | 88 | 60 | zamknięta | SL | -340.8 |
| EURUSD | long | 2012-05-07 | 2012-05-30 | 23 | 17 | zamknięta | SL | -641.2 |
| EURUSD | long | 2012-05-14 | 2012-06-01 | 18 | 14 | zamknięta | SL | -532.9 |
| EURUSD | long | 2012-05-21 | 2012-07-23 | 63 | 45 | zamknięta | SL | -732.6 |
| EURUSD | long | 2012-06-04 | 2013-02-02 | 242 | 171 | zamknięta | TP | 1 165.2 |
| EURUSD | long | 2012-06-11 | 2013-02-02 | 235 | 166 | zamknięta | TP | 1 187.1 |
| EURGBP | long | 2012-07-09 | 2013-01-31 | 205 | 144 | zamknięta | TP | 665.2 |
| EURGBP | long | 2012-07-16 | 2013-01-31 | 198 | 139 | zamknięta | TP | 743.4 |
| EURGBP | long | 2012-07-23 | 2013-01-31 | 191 | 134 | zamknięta | TP | 774.6 |
| EURUSD | long | 2012-07-23 | 2013-02-02 | 193 | 136 | zamknięta | TP | 1 480.0 |
| GBPUSD | long | 2013-03-12 | 2013-09-11 | 184 | 131 | zamknięta | TP | 877.2 |
| AUDUSD | long | 2013-05-29 | 2013-06-24 | 26 | 18 | zamknięta | SL | -471.1 |
| AUDUSD | long | 2013-06-06 | 2013-07-05 | 29 | 21 | zamknięta | SL | -507.4 |
| AUDUSD | long | 2013-06-13 | 2013-08-01 | 49 | 33 | zamknięta | SL | -678.0 |
| AUDUSD | long | 2013-06-27 | 2014-11-06 | 496 | 341 | zamknięta | SL | -642.7 |
| GBPUSD | long | 2013-07-08 | 2013-09-12 | 66 | 47 | zamknięta | TP | 866.0 |
| AUDUSD | long | 2013-07-11 | 2014-11-06 | 482 | 331 | zamknięta | SL | -559.7 |
| AUDUSD | long | 2013-08-05 | 2015-01-24 | 536 | 369 | zamknięta | SL | -956.0 |
| EURGBP | long | 2014-07-17 | 2015-01-24 | 190 | 132 | zamknięta | SL | -347.2 |
| EURGBP | long | 2014-07-24 | 2015-01-23 | 182 | 126 | zamknięta | SL | -343.0 |
| EURGBP | long | 2014-09-21 | 2015-01-24 | 124 | 86 | zamknięta | SL | -329.1 |
| EURUSD | long | 2014-11-04 | 2015-01-06 | 63 | 40 | zamknięta | SL | -538.6 |
| AUDUSD | long | 2014-11-10 | 2015-02-04 | 86 | 58 | zamknięta | SL | -989.0 |
| EURUSD | long | 2014-11-11 | 2015-01-06 | 56 | 35 | zamknięta | SL | -506.3 |
| AUDUSD | long | 2014-11-17 | 2015-01-24 | 68 | 46 | zamknięta | SL | -834.7 |
| EURUSD | long | 2014-11-25 | 2015-01-09 | 45 | 30 | zamknięta | SL | -659.1 |
| GBPUSD | long | 2015-01-08 | 2016-01-13 | 370 | 253 | zamknięta | SL | -616.9 |
| EURUSD | long | 2015-01-09 | 2015-03-07 | 57 | 39 | zamknięta | SL | -937.6 |
| GBPUSD | long | 2015-01-15 | 2016-01-08 | 358 | 245 | zamknięta | SL | -684.1 |
| EURUSD | long | 2015-01-16 | 2015-03-11 | 54 | 36 | zamknięta | SL | -865.3 |
| GBPUSD | long | 2015-01-22 | 2016-01-13 | 356 | 243 | zamknięta | SL | -634.2 |
| EURUSD | long | 2015-01-23 | 2016-12-16 | 693 | 471 | zamknięta | SL | -864.3 |
| EURGBP | long | 2015-01-29 | 2015-07-17 | 170 | 119 | zamknięta | SL | -510.1 |
| AUDUSD | long | 2015-01-30 | 2020-02-22 | 1 849 | 1 268 | zamknięta | SL | -1 196.4 |
| EURGBP | long | 2015-02-05 | 2015-03-12 | 35 | 25 | zamknięta | SL | -366.7 |
| AUDUSD | long | 2015-02-06 | 2020-03-10 | 1 859 | 1 273 | zamknięta | SL | -1 431.6 |
| EURGBP | long | 2015-02-12 | 2016-06-24 | 499 | 352 | zamknięta | TP | 773.3 |
| AUDUSD | long | 2015-02-13 | 2020-03-13 | 1 855 | 1 271 | zamknięta | SL | -1 439.7 |
| EURGBP | long | 2015-03-12 | 2016-06-24 | 471 | 332 | zamknięta | TP | 1 102.5 |
| EURUSD | long | 2015-05-06 | 2022-09-05 | 2 679 | 1 846 | zamknięta | SL | -1 457.2 |
| EURUSD | long | 2015-05-13 | 2022-08-22 | 2 658 | 1 831 | zamknięta | SL | -1 395.7 |
| EURGBP | long | 2015-07-20 | 2016-04-06 | 261 | 185 | zamknięta | TP | 1 105.9 |
| GBPUSD | long | 2016-01-12 | 2016-06-24 | 165 | 117 | zamknięta | SL | -975.8 |
| GBPUSD | long | 2016-01-19 | 2016-06-27 | 161 | 113 | zamknięta | SL | -1 115.7 |
| EURJPY | long | 2016-01-22 | 2016-03-02 | 40 | 27 | zamknięta | SL | -576.0 |
| GBPUSD | long | 2016-01-26 | 2016-07-05 | 162 | 114 | zamknięta | SL | -1 122.5 |
| EURJPY | long | 2016-02-12 | 2016-02-25 | 13 | 9 | zamknięta | SL | -464.6 |
| EURJPY | long | 2016-02-26 | 2016-06-24 | 120 | 83 | zamknięta | SL | -970.4 |
| EURJPY | long | 2016-03-04 | 2016-06-24 | 113 | 78 | zamknięta | SL | -964.7 |
| USDJPY | long | 2016-06-20 | 2016-06-24 | 4 | 4 | zamknięta | SL | -336.9 |
| USDJPY | long | 2016-06-27 | 2016-11-19 | 144 | 101 | zamknięta | TP | 853.6 |
| EURJPY | long | 2016-06-29 | 2017-09-22 | 450 | 304 | zamknięta | TP | 2 010.6 |
| GBPUSD | long | 2016-06-29 | 2020-03-20 | 1 359 | 944 | zamknięta | SL | -1 846.5 |
| USDJPY | long | 2016-07-04 | 2016-11-19 | 137 | 96 | zamknięta | TP | 779.2 |
| EURJPY | long | 2016-07-06 | 2017-09-22 | 443 | 299 | zamknięta | TP | 2 207.2 |
| GBPUSD | long | 2016-07-06 | 2022-09-23 | 2 270 | 1 570 | zamknięta | SL | -1 961.8 |
| USDJPY | long | 2016-07-11 | 2016-11-19 | 130 | 91 | zamknięta | TP | 781.0 |
| GBPUSD | long | 2016-07-13 | 2020-03-20 | 1 345 | 934 | zamknięta | SL | -1 591.1 |
| EURUSD | long | 2016-12-22 | 2017-08-03 | 225 | 155 | zamknięta | TP | 1 458.8 |
| USDCAD | long | 2017-09-10 | 2017-10-27 | 47 | 35 | zamknięta | TP | 714.8 |
| USDCAD | long | 2017-09-17 | 2017-10-27 | 40 | 30 | zamknięta | TP | 677.3 |
| USDCAD | long | 2018-01-30 | 2018-03-16 | 45 | 33 | zamknięta | TP | 679.6 |
| USDJPY | long | 2018-02-15 | 2018-10-01 | 229 | 150 | zamknięta | TP | 719.2 |
| USDJPY | long | 2018-02-22 | 2018-10-01 | 222 | 145 | zamknięta | TP | 606.6 |
| USDJPY | long | 2018-03-02 | 2018-09-28 | 211 | 139 | zamknięta | TP | 744.4 |
| EURJPY | long | 2019-08-04 | 2020-08-06 | 368 | 247 | zamknięta | TP | 711.3 |
| EURJPY | long | 2019-08-11 | 2020-08-06 | 361 | 242 | zamknięta | TP | 740.4 |
| EURGBP | long | 2019-12-16 | 2020-03-12 | 87 | 58 | zamknięta | TP | 464.7 |
| EURUSD | long | 2020-02-14 | 2020-03-10 | 25 | 16 | zamknięta | TP | 609.6 |
| EURGBP | long | 2020-02-17 | 2020-03-12 | 24 | 17 | zamknięta | TP | 484.0 |
| AUDUSD | long | 2020-02-28 | 2020-03-19 | 20 | 13 | zamknięta | SL | -626.3 |
| USDJPY | long | 2020-03-10 | 2020-03-21 | 11 | 8 | zamknięta | TP | 732.6 |
| AUDUSD | long | 2020-03-16 | 2020-08-28 | 166 | 119 | zamknięta | TP | 1 138.3 |
| AUDUSD | long | 2020-03-23 | 2020-08-28 | 159 | 114 | zamknięta | TP | 1 550.8 |
| EURUSD | long | 2020-03-23 | 2020-07-21 | 121 | 81 | zamknięta | TP | 780.4 |
| GBPUSD | long | 2020-03-25 | 2020-07-30 | 128 | 85 | zamknięta | TP | 1 249.5 |
| AUDUSD | long | 2020-03-29 | 2020-08-28 | 152 | 109 | zamknięta | TP | 1 123.0 |
| GBPUSD | long | 2020-03-31 | 2020-07-30 | 121 | 80 | zamknięta | TP | 627.0 |
| USDJPY | long | 2020-11-09 | 2021-03-16 | 127 | 86 | zamknięta | TP | 608.9 |
| USDJPY | long | 2020-12-17 | 2021-03-10 | 83 | 57 | zamknięta | TP | 561.1 |
| USDJPY | long | 2020-12-24 | 2021-03-10 | 76 | 52 | zamknięta | TP | 548.8 |
| USDCAD | long | 2021-02-26 | 2022-07-14 | 504 | 352 | zamknięta | TP | 600.9 |
| USDCAD | long | 2021-03-15 | 2021-05-18 | 65 | 47 | zamknięta | SL | -451.6 |
| USDCAD | long | 2021-03-22 | 2022-07-14 | 480 | 336 | zamknięta | TP | 688.4 |
| USDCAD | long | 2021-05-24 | 2022-07-14 | 416 | 290 | zamknięta | TP | 1 134.7 |
| EURGBP | long | 2022-03-07 | 2022-09-16 | 194 | 139 | zamknięta | TP | 500.4 |
| EURUSD | long | 2022-03-08 | 2022-05-12 | 66 | 47 | zamknięta | SL | -451.2 |
| EURGBP | long | 2022-04-17 | 2022-09-16 | 152 | 109 | zamknięta | TP | 438.2 |
| GBPUSD | long | 2022-05-08 | 2022-07-14 | 67 | 48 | zamknięta | SL | -556.3 |
| EURUSD | long | 2022-05-15 | 2022-09-28 | 136 | 97 | zamknięta | SL | -828.8 |
| GBPUSD | long | 2022-05-15 | 2022-09-05 | 113 | 80 | zamknięta | SL | -784.5 |
| AUDUSD | long | 2022-07-07 | 2022-09-26 | 81 | 57 | zamknięta | SL | -334.2 |
| AUDUSD | long | 2022-07-14 | 2022-09-28 | 76 | 54 | zamknięta | SL | -333.3 |
| GBPUSD | long | 2022-07-19 | 2022-09-23 | 66 | 48 | zamknięta | SL | -937.5 |
| EURUSD | long | 2022-08-22 | 2025-04-11 | 963 | 671 | zamknięta | TP | 1 438.0 |
| EURUSD | long | 2022-09-05 | 2025-04-11 | 949 | 661 | zamknięta | TP | 1 411.0 |
| GBPUSD | long | 2022-09-06 | 2022-09-26 | 20 | 14 | zamknięta | SL | -1 104.7 |
| AUDUSD | long | 2022-09-07 | 2022-09-28 | 21 | 15 | zamknięta | SL | -334.3 |
| GBPUSD | long | 2022-09-27 | 2023-07-13 | 289 | 206 | zamknięta | TP | 2 359.2 |
| AUDUSD | long | 2022-09-28 | 2022-10-10 | 12 | 8 | zamknięta | TP | 636.1 |
| EURUSD | long | 2022-10-03 | 2025-04-11 | 921 | 641 | zamknięta | TP | 1 501.9 |
| GBPUSD | long | 2022-10-04 | 2023-07-13 | 282 | 201 | zamknięta | TP | 1 628.4 |
| AUDUSD | long | 2022-10-05 | 2022-10-10 | 5 | 3 | zamknięta | TP | 626.3 |
| GBPUSD | long | 2022-10-11 | 2023-07-13 | 275 | 196 | zamknięta | TP | 2 104.0 |
| AUDUSD | long | 2022-10-12 | 2023-01-27 | 106 | 76 | zamknięta | TP | 859.2 |
| AUDUSD | long | 2022-10-19 | 2023-01-27 | 99 | 71 | zamknięta | TP | 869.8 |
| AUDUSD | long | 2022-10-26 | 2023-01-27 | 92 | 66 | zamknięta | TP | 637.2 |
| AUDUSD | long | 2023-02-28 | 2023-08-16 | 170 | 119 | zamknięta | SL | -302.6 |
| AUDUSD | long | 2023-03-07 | 2023-05-31 | 86 | 61 | zamknięta | SL | -260.5 |
| AUDUSD | long | 2023-03-14 | 2024-12-20 | 647 | 445 | zamknięta | SL | -452.7 |
| AUDUSD | long | 2023-06-06 | 2024-12-20 | 562 | 385 | zamknięta | SL | -472.8 |
| AUDUSD | long | 2023-08-21 | 2026-02-12 | 905 | 615 | zamknięta | TP | 715.0 |
| GBPUSD | long | 2023-09-25 | 2024-07-11 | 290 | 202 | zamknięta | TP | 704.0 |
| GBPUSD | long | 2023-10-02 | 2024-07-11 | 283 | 197 | zamknięta | TP | 824.4 |
| GBPUSD | long | 2023-10-09 | 2024-07-11 | 276 | 192 | zamknięta | TP | 655.3 |
| AUDUSD | long | 2024-12-26 | 2026-01-07 | 377 | 254 | zamknięta | TP | 489.1 |
| AUDUSD | long | 2025-01-03 | 2026-01-07 | 369 | 249 | zamknięta | TP | 526.7 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 40.02 pips/transakcję, percentyl **98.3** (losowe: 5%=-209.71, mediana=-100.72, 95%=1.81).

- **Deflated Sharpe Ratio**: 0.113 (Sharpe na transakcję -0.084, próg przy 3 próbach 0.009).

- **PBO** (CSCV, 16 bloków, 3 wariantów): 0.708 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 154 transakcji, śr. 134.92 pips, 0.17 R.

- **Bootstrap 95%** średnich pipsów: całość [-104.49; 180.31], OOS [277.33; 689.20].

- **Spread**: ×1 40.02, ×1,5 39.24, ×2 38.46 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 382.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -150.98, 1 pips: -341.98 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

- **Pozycje otwarte (D-061, wyjście bez limitu czasu):** 13 z 724 transakcji (1.8%) nie zamknęło się do końca danych — liczone po ostatnim close jako wynik niezrealizowany; średnio 421.39 pips netto na pozycję. Wynik realny zależy od tego, czy cena jeszcze wróci do poziomu; nie ma stopu, więc przegrywająca pozycja trwa.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który spadł o co najmniej 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Tylko long (cena ≥ 5% poniżej średniej). Jedno wejście na tydzień (co najmniej 5 dni handlu od poprzedniego
w tej parze), do 3 pozycji naraz w parze. Cel = poziom średniej z dnia sygnału (stała cena), bez limitu czasu.
Wersja z zarządzaniem ryzykiem: STOP LOSS poniżej wejścia na odległość równą ułamkowi drogi do celu (0,5 / 0,75 / 1,0 ×
droga do średniej), więc z góry znany stosunek zysku do straty, a pozycja nie wisi latami na stracie. Każda pozycja
ma tę samą stratę przy stopie: ok. 0,5% kapitału (waga pozycji = 0,5% ÷ odległość do stopu), niezależnie od tego, jak
głęboko kurs jest pod średnią. Wszystko jak w wersji bez stopu, tylko ryzyko jest ograniczone i równe w każdej
transakcji. Cała dostępna historia D1 (ok. 27 lat sygnałów), żeby próba IS (ranking) i OOS (ostatnie 25%) miały dość transakcji.
Hipoteza zapisana PRZED liczeniem."""

# Jedyny parametr: odległość stopu jako ułamek drogi do celu (średniej).
PARAMS = {"sl_gap": [0.5, 0.75, 1.0]}
START = None              # cała historia; żeby liczyć tylko ostatnie 10 lat, wpisz START = "2016-11-11" (wtedy IS ma mało transakcji)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)
RISK = 0.005              # strata przy stopie = 0,5% kapitału na pozycję

PYRAMID = 3               # do 3 pozycji naraz w parze (najgorszy przypadek: 8 par × 3 × 0,5% = 12% kapitału)
SIZING = [1]              # waga 1,0 = depozyt 1% kapitału = nominał 30% kapitału; waga sygnału skaluje to do RISK
EXITS = [{"kind": "level", "cap": 0}]     # TP i SL ze strategii (levels), bez limitu czasu (D-061)


def levels(df, p, ind):
    """TP = średnia z 756 dni z dnia sygnału. SL = cena sygnału minus sl_gap × (droga do średniej)."""
    sma = ind.sma(df.close, MEAN_DAYS)
    return pd.DataFrame({"tp": sma, "sl": df.close - p["sl_gap"] * (sma - df.close)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    dev = (df.close / sma - 1.0).to_numpy()
    live = np.isfinite(dev) if START is None else (df.index >= pd.Timestamp(START, tz="UTC")) & np.isfinite(dev)
    below = live & (dev <= -BAND)
    # waga: strata przy stopie ≈ 0,3 (nominał na wagę 1) × waga × odległość do stopu (w ułamku ceny) = RISK
    stop_dist = p["sl_gap"] * (sma / df.close - 1.0).to_numpy()
    weight = np.clip(RISK / (0.3 * np.where(stop_dist > 0, stop_dist, np.nan)), 0.1, 10.0)
    out = np.zeros(len(dev))
    last = -10**9                     # tylko z przeszłości: najwyżej jedno wejście na GAP_DAYS dni
    for t in range(len(dev)):
        if t - last < GAP_DAYS:
            continue
        if below[t] and np.isfinite(weight[t]):
            out[t], last = weight[t], t
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
