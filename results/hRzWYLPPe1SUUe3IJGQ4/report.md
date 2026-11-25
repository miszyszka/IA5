# Raport strategii: Alma v.1

Run `20261125-175255` · silnik 0.14.0 · kod `50e8d899b65f8d05` · dane `02cdfcd25d7e5788`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 24.35 |
| percentyl benchmarku ≥ 95 | ✔ | 97.20 |
| PBO < 0,3 | ✔ | 0.09 |
| DSR ≥ 0,95 | ✘ | 0.56 |
| dodatni przy spreadzie ×1,5 | ✔ | 55.21 |

## Hipoteza

ALMA (Arnaud Legoux, 2009) waży ceny krzywą Gaussa przesuniętą ku najnowszym świecom, więc zawraca
wcześniej niż SMA o podobnej długości i mniej szarpie niż EMA. Jeśli trendy na parach FX trwają tygodniami, to wcześniejsze
wykrycie zwrotu średniej zostawia większą część ruchu niż spóźniona SMA. Pojedyncze „mignięcia” kierunku to szum,
więc liczy się tylko zwrot po ruchu, który trwał co najmniej kilka dni. Ryzyko: trzy pokrętła (długość, offset, sigma)
i każde to kompromis — offset 0,99 szybki, ale nerwowy, 0,5 gładki, ale spóźniony. Start od domyślnych 9 · 0,85 · 6.
Wersja 2: mniej wariantów i bez trybu „przecięcie” — wersja 1 dała 444 MB transakcji, a GitHub przyjmuje do 100 MB.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-24; źródło: yahoo.

- In-sample do 2019-05-19, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS. OOS tego okresu widziało już 2 wersji kodu strategii; ta strategia: 1 wersji.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 149, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 118, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 699** (3 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 1,495 (limit otwartych pozycji w parze), 4.0 (brak danych do wyjścia); 2 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 7.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 120 świecach | cfg=2 | 266 | 0.79 | 69.14 | 56.0 | 110 | 0.72 | 24.35 |
| 2 | po 120 świecach | cfg=0 | 273 | 0.37 | -6.00 | 51.6 | 115 | 1.14 | 55.76 |
| 3 | po 96 świecach | cfg=2 | 325 | 0.22 | 12.11 | 49.5 | 136 | -1.07 | -91.32 |
| 4 | po 96 świecach | cfg=1 | 322 | 0.19 | -2.12 | 52.2 | 136 | 0.26 | 7.14 |
| 5 | po 72 świecach | cfg=1 | 423 | 0.16 | 2.36 | 53.2 | 180 | 0.28 | 28.99 |
| 6 | po 96 świecach | cfg=0 | 337 | 0.14 | 16.38 | 46.6 | 143 | -0.06 | -38.05 |
| 7 | po 72 świecach | cfg=2 | 426 | 0.11 | 15.57 | 53.1 | 184 | -0.21 | -9.01 |
| 8 | po 48 świecach | cfg=0 | 649 | 0.08 | 0.69 | 49.2 | 283 | -0.36 | -44.15 |
| 9 | po 36 świecach | cfg=0 | 835 | 0.06 | 11.84 | 52.6 | 367 | 0.05 | -4.78 |
| 10 | sygnał przeciwny, SL 1×ATR14, max 120 | cfg=2 | 1 830 | 0.05 | 4.78 | 34.6 | 847 | -0.13 | -13.18 |

## Najlepszy wariant IS: po 120 świecach (cfg=2)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 40 | -80.3 | -3 212.3 | 45.0 |
| EURGBP | 56 | 26.0 | 1 455.3 | 64.3 |
| EURJPY | 45 | -107.4 | -4 833.9 | 46.7 |
| EURUSD | 45 | 15.6 | 700.0 | 53.3 |
| GBPUSD | 44 | 271.9 | 11 961.8 | 63.6 |
| USDCAD | 46 | 188.1 | 8 652.6 | 65.2 |
| USDCHF | 45 | 68.9 | 3 099.4 | 51.1 |
| USDJPY | 55 | 59.0 | 3 247.1 | 45.5 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 1997 | 1 | 1 175.6 | 1 175.6 | 100.0 |
| 1998 | 2 | 177.6 | 355.2 | 50.0 |
| 1999 | 3 | 340.8 | 1 022.5 | 33.3 |
| 2000 | 4 | 89.2 | 356.8 | 75.0 |
| 2001 | 4 | -255.3 | -1 021.2 | 50.0 |
| 2002 | 4 | -250.6 | -1 002.2 | 25.0 |
| 2003 | 6 | 256.2 | 1 537.0 | 83.3 |
| 2004 | 11 | 245.4 | 2 699.9 | 63.6 |
| 2005 | 15 | 7.6 | 113.5 | 46.7 |
| 2006 | 17 | 118.3 | 2 011.4 | 64.7 |
| 2007 | 15 | -33.7 | -505.0 | 46.7 |
| 2008 | 12 | 14.7 | 175.9 | 58.3 |
| 2009 | 15 | -400.3 | -6 005.2 | 46.7 |
| 2010 | 17 | 374.6 | 6 368.5 | 70.6 |
| 2011 | 17 | -17.6 | -298.5 | 35.3 |
| 2012 | 15 | 178.7 | 2 680.6 | 66.7 |
| 2013 | 15 | -132.3 | -1 984.4 | 46.7 |
| 2014 | 17 | 222.6 | 3 783.4 | 64.7 |
| 2015 | 15 | -127.7 | -1 915.9 | 60.0 |
| 2016 | 16 | 229.3 | 3 669.2 | 62.5 |
| 2017 | 14 | 129.7 | 1 816.0 | 50.0 |
| 2018 | 16 | 95.6 | 1 528.8 | 50.0 |
| 2019 | 16 | 116.4 | 1 863.0 | 62.5 |
| 2020 | 15 | 173.2 | 2 597.4 | 60.0 |
| 2021 | 17 | -9.9 | -168.7 | 47.1 |
| 2022 | 16 | -142.7 | -2 282.5 | 43.8 |
| 2023 | 16 | -118.2 | -1 890.5 | 31.2 |
| 2024 | 16 | 57.3 | 916.0 | 62.5 |
| 2025 | 15 | 296.5 | 4 447.2 | 73.3 |
| 2026 | 14 | -69.6 | -974.1 | 35.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 266 | 69.1 | 18 391.1 | 56.0 |
| OOS | 110 | 24.4 | 2 678.9 | 50.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | -4 972 | -149.7 | -100.0 | -119.7 | -195.4 | -0.27 | 273 |
| 10.0% | -45 047 | -550.5 | -100.0 | -195.6 | -355.9 | 0.04 | 277 |
| 15.0% | -140 281 | -1 502.8 | -100.0 | -277.7 | -410.3 | 0.35 | 293 |
| 20.0% | -156 676 | -1 666.8 | -100.0 | -259.9 | -352.6 | 0.26 | 307 |
| 30.0% | -96 574 | -1 065.7 | -100.0 | -374.6 | -523.0 | 0.23 | 326 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-18): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **376**, otwarte: **0** (razem 376).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 376 | 166 | 172 | 173 | 179 | 190 | 56.0 | 21 070 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 376 | 166 | 172 | 173 | 179 | 190 | 56.0 | 21 070 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDJPY | long | 1997-06-02 | 1997-12-03 | 183 | 120 | zamknięta | czas | 1 175.6 |
| USDJPY | short | 1997-12-18 | 1998-06-05 | 170 | 120 | zamknięta | czas | -1 318.4 |
| USDJPY | short | 1998-06-17 | 1998-12-03 | 168 | 120 | zamknięta | czas | 1 673.6 |
| USDJPY | short | 1998-12-03 | 1999-05-21 | 170 | 120 | zamknięta | czas | -423.4 |
| EURGBP | long | 1999-02-11 | 1999-07-28 | 168 | 120 | zamknięta | czas | -294.7 |
| USDJPY | short | 1999-05-25 | 1999-11-10 | 168 | 120 | zamknięta | czas | 1 740.6 |
| EURGBP | short | 1999-07-29 | 2000-01-14 | 168 | 120 | zamknięta | czas | 395.3 |
| USDJPY | short | 1999-11-11 | 2000-04-26 | 168 | 120 | zamknięta | czas | -159.4 |
| EURGBP | long | 2000-02-03 | 2000-07-19 | 168 | 120 | zamknięta | czas | 102.3 |
| USDJPY | short | 2000-05-11 | 2000-10-26 | 168 | 120 | zamknięta | czas | 18.6 |
| EURGBP | long | 2000-07-26 | 2001-01-13 | 170 | 120 | zamknięta | czas | 195.3 |
| USDJPY | short | 2000-11-02 | 2001-04-20 | 170 | 120 | zamknięta | czas | -1 339.4 |
| EURGBP | short | 2001-01-24 | 2001-07-10 | 168 | 120 | zamknięta | czas | 312.3 |
| USDJPY | long | 2001-04-26 | 2001-10-11 | 168 | 120 | zamknięta | czas | -189.4 |
| EURGBP | short | 2001-07-30 | 2002-01-17 | 170 | 120 | zamknięta | czas | -24.7 |
| USDJPY | short | 2001-10-30 | 2002-04-17 | 170 | 120 | zamknięta | czas | -880.4 |
| EURGBP | long | 2002-01-23 | 2002-07-09 | 168 | 120 | zamknięta | czas | 206.3 |
| USDJPY | long | 2002-05-07 | 2002-10-22 | 168 | 120 | zamknięta | czas | -303.4 |
| EURGBP | long | 2002-07-16 | 2003-01-03 | 170 | 120 | zamknięta | czas | 72.3 |
| USDJPY | short | 2002-10-23 | 2003-04-11 | 170 | 120 | zamknięta | czas | 388.6 |
| EURGBP | short | 2003-01-06 | 2003-06-20 | 166 | 120 | zamknięta | czas | -503.7 |
| EURJPY | long | 2003-03-03 | 2003-08-15 | 166 | 120 | zamknięta | czas | 665.9 |
| USDJPY | short | 2003-04-16 | 2003-10-01 | 168 | 120 | zamknięta | czas | 826.6 |
| EURGBP | long | 2003-06-30 | 2003-12-16 | 168 | 120 | zamknięta | czas | 87.3 |
| EURJPY | long | 2003-09-04 | 2004-02-24 | 172 | 120 | zamknięta | czas | 830.9 |
| USDJPY | long | 2003-10-16 | 2004-04-05 | 172 | 120 | zamknięta | czas | -468.4 |
| USDCAD | long | 2003-10-30 | 2004-04-16 | 170 | 120 | zamknięta | czas | 326.0 |
| USDCHF | short | 2003-11-13 | 2004-04-30 | 170 | 120 | zamknięta | czas | 552.1 |
| EURUSD | short | 2004-01-15 | 2004-07-01 | 169 | 120 | zamknięta | czas | 493.0 |
| GBPUSD | short | 2004-01-16 | 2004-07-01 | 168 | 120 | zamknięta | czas | 47.3 |
| EURGBP | long | 2004-01-28 | 2004-07-14 | 169 | 120 | zamknięta | czas | -245.7 |
| EURJPY | short | 2004-03-02 | 2004-08-16 | 168 | 120 | zamknięta | czas | -82.1 |
| USDJPY | long | 2004-04-06 | 2004-09-21 | 168 | 120 | zamknięta | czas | 400.6 |
| USDCHF | long | 2004-05-09 | 2004-10-22 | 166 | 120 | zamknięta | czas | -953.9 |
| USDCAD | short | 2004-05-19 | 2004-11-06 | 170 | 120 | zamknięta | czas | 1 800.0 |
| EURUSD | short | 2004-07-15 | 2005-01-04 | 172 | 120 | zamknięta | czas | -1 112.9 |
| GBPUSD | short | 2004-07-20 | 2005-01-07 | 170 | 120 | zamknięta | czas | -240.4 |
| EURGBP | long | 2004-07-21 | 2005-01-07 | 169 | 120 | zamknięta | czas | 359.3 |
| EURJPY | short | 2004-08-18 | 2005-02-05 | 170 | 120 | zamknięta | czas | 85.9 |
| USDJPY | short | 2004-09-30 | 2005-03-22 | 172 | 120 | zamknięta | czas | 485.6 |
| USDCAD | long | 2004-11-16 | 2005-05-04 | 170 | 120 | zamknięta | czas | 447.0 |
| USDCHF | long | 2004-12-03 | 2005-05-19 | 168 | 120 | zamknięta | czas | 695.1 |
| EURUSD | short | 2005-01-04 | 2005-06-21 | 169 | 120 | zamknięta | czas | 1 295.1 |
| GBPUSD | long | 2005-01-13 | 2005-06-30 | 169 | 120 | zamknięta | czas | -1 006.3 |
| EURGBP | long | 2005-01-18 | 2005-07-04 | 168 | 120 | zamknięta | czas | -262.7 |
| EURJPY | short | 2005-02-07 | 2005-07-27 | 171 | 120 | zamknięta | czas | -164.1 |
| USDJPY | short | 2005-04-11 | 2005-09-27 | 169 | 120 | zamknięta | czas | -553.4 |
| USDCAD | short | 2005-05-04 | 2005-10-20 | 169 | 120 | zamknięta | czas | 691.0 |
| USDCHF | short | 2005-06-21 | 2005-12-10 | 171 | 120 | zamknięta | czas | -385.9 |
| EURUSD | long | 2005-07-11 | 2005-12-30 | 171 | 120 | zamknięta | czas | -219.8 |
| GBPUSD | long | 2005-07-12 | 2006-01-03 | 174 | 120 | zamknięta | czas | -580.3 |
| EURGBP | short | 2005-07-25 | 2006-01-12 | 170 | 120 | zamknięta | czas | 35.3 |
| EURJPY | short | 2005-08-11 | 2006-01-31 | 172 | 120 | zamknięta | czas | -537.1 |
| USDJPY | short | 2005-10-06 | 2006-03-27 | 172 | 120 | zamknięta | czas | -341.4 |
| USDCAD | short | 2005-11-18 | 2006-05-05 | 169 | 120 | zamknięta | czas | 824.0 |
| USDCHF | long | 2005-12-21 | 2006-06-06 | 168 | 120 | zamknięta | czas | -908.9 |
| EURUSD | long | 2006-01-04 | 2006-06-20 | 168 | 120 | zamknięta | czas | 558.2 |
| GBPUSD | long | 2006-01-04 | 2006-06-22 | 170 | 120 | zamknięta | czas | 805.4 |
| EURGBP | long | 2006-01-19 | 2006-07-05 | 168 | 120 | zamknięta | czas | 64.3 |
| EURJPY | short | 2006-02-08 | 2006-07-26 | 169 | 120 | zamknięta | czas | -675.6 |
| USDJPY | short | 2006-04-04 | 2006-09-19 | 168 | 120 | zamknięta | czas | -19.4 |
| USDCAD | long | 2006-05-14 | 2006-10-27 | 166 | 120 | zamknięta | czas | 111.0 |
| EURUSD | long | 2006-06-21 | 2006-12-08 | 169 | 120 | zamknięta | czas | 624.2 |
| AUDUSD | long | 2006-06-29 | 2006-12-15 | 168 | 120 | zamknięta | czas | 440.9 |
| USDCHF | short | 2006-06-29 | 2006-12-16 | 169 | 120 | zamknięta | czas | 156.1 |
| GBPUSD | long | 2006-07-02 | 2006-12-20 | 170 | 120 | zamknięta | czas | 1 236.6 |
| EURGBP | short | 2006-07-09 | 2006-12-23 | 166 | 120 | zamknięta | czas | 218.3 |
| EURJPY | short | 2006-07-27 | 2007-01-17 | 173 | 120 | zamknięta | czas | -910.1 |
| USDJPY | short | 2006-09-20 | 2007-03-13 | 173 | 120 | zamknięta | czas | -14.4 |
| USDCAD | long | 2006-11-02 | 2007-04-20 | 170 | 120 | zamknięta | czas | -101.0 |
| EURUSD | short | 2006-12-11 | 2007-05-30 | 171 | 120 | zamknięta | czas | -249.0 |
| AUDUSD | long | 2006-12-21 | 2007-06-08 | 170 | 120 | zamknięta | czas | 575.7 |
| EURGBP | long | 2007-01-02 | 2007-06-18 | 168 | 120 | zamknięta | czas | 30.3 |
| USDCHF | short | 2007-01-02 | 2007-06-18 | 168 | 120 | zamknięta | czas | -250.9 |
| GBPUSD | long | 2007-01-15 | 2007-07-02 | 169 | 120 | zamknięta | czas | 572.5 |
| EURJPY | short | 2007-01-29 | 2007-07-16 | 169 | 120 | zamknięta | czas | -1 084.1 |
| USDJPY | short | 2007-03-28 | 2007-09-14 | 170 | 120 | zamknięta | czas | 163.6 |
| USDCAD | long | 2007-05-10 | 2007-10-26 | 169 | 120 | zamknięta | czas | -1 504.0 |
| EURUSD | long | 2007-05-31 | 2007-11-20 | 172 | 120 | zamknięta | czas | 1 211.0 |
| AUDUSD | short | 2007-06-14 | 2007-12-04 | 172 | 120 | zamknięta | czas | -451.9 |
| USDCHF | short | 2007-06-20 | 2007-12-08 | 170 | 120 | zamknięta | czas | 1 099.1 |
| EURGBP | long | 2007-07-01 | 2007-12-18 | 169 | 120 | zamknięta | czas | 408.3 |
| EURJPY | short | 2007-07-22 | 2008-01-10 | 171 | 120 | zamknięta | czas | 673.9 |
| USDJPY | long | 2007-09-16 | 2008-03-13 | 178 | 120 | zamknięta | czas | -1 369.4 |
| USDCAD | long | 2007-11-12 | 2008-05-06 | 177 | 120 | zamknięta | czas | 576.0 |
| EURUSD | short | 2007-11-30 | 2008-05-23 | 176 | 120 | zamknięta | czas | -1 010.2 |
| AUDUSD | long | 2007-12-26 | 2008-06-16 | 174 | 120 | zamknięta | czas | 707.4 |
| USDCHF | short | 2007-12-28 | 2008-06-17 | 173 | 120 | zamknięta | czas | 989.1 |
| EURJPY | long | 2008-01-11 | 2008-07-02 | 174 | 120 | zamknięta | czas | 586.9 |
| EURGBP | short | 2008-01-17 | 2008-07-07 | 173 | 120 | zamknięta | czas | -484.2 |
| GBPUSD | short | 2008-02-04 | 2008-07-23 | 171 | 120 | zamknięta | czas | -323.4 |
| USDCAD | long | 2008-05-27 | 2008-11-14 | 170 | 120 | zamknięta | czas | 2 184.0 |
| AUDUSD | long | 2008-06-18 | 2008-12-05 | 169 | 120 | zamknięta | czas | -3 029.2 |
| USDCHF | long | 2008-07-07 | 2008-12-23 | 168 | 120 | zamknięta | czas | 675.1 |
| EURGBP | short | 2008-07-15 | 2009-01-01 | 169 | 120 | zamknięta | czas | -1 575.7 |
| USDJPY | short | 2008-08-31 | 2009-02-19 | 171 | 120 | zamknięta | czas | 1 479.5 |
| EURUSD | long | 2008-09-07 | 2009-02-26 | 171 | 120 | zamknięta | czas | -2 329.9 |
| GBPUSD | long | 2008-09-14 | 2009-03-06 | 172 | 120 | zamknięta | czas | -3 851.2 |
| EURJPY | long | 2008-09-21 | 2009-03-13 | 172 | 120 | zamknięta | czas | -2 895.1 |
| USDCAD | short | 2008-11-25 | 2009-05-13 | 170 | 120 | zamknięta | czas | 592.0 |
| AUDUSD | short | 2008-12-24 | 2009-06-11 | 170 | 120 | zamknięta | czas | -1 412.1 |
| EURGBP | short | 2009-01-06 | 2009-06-22 | 168 | 120 | zamknięta | czas | 782.3 |
| USDCHF | long | 2009-01-06 | 2009-06-23 | 169 | 120 | zamknięta | czas | -418.9 |
| EURUSD | long | 2009-03-09 | 2009-08-28 | 173 | 120 | zamknięta | czas | 1 620.1 |
| USDJPY | short | 2009-03-12 | 2009-08-26 | 168 | 120 | zamknięta | czas | 371.3 |
| GBPUSD | long | 2009-03-17 | 2009-09-09 | 177 | 120 | zamknięta | czas | 2 588.5 |
| EURJPY | short | 2009-03-29 | 2009-09-23 | 178 | 120 | zamknięta | czas | -358.3 |
| USDCAD | long | 2009-05-13 | 2009-10-31 | 170 | 120 | zamknięta | czas | -920.0 |
| EURGBP | long | 2009-06-23 | 2009-12-19 | 178 | 120 | zamknięta | czas | 322.3 |
| AUDUSD | short | 2009-07-02 | 2010-01-07 | 188 | 120 | zamknięta | czas | -1 275.8 |
| USDCHF | short | 2009-07-09 | 2010-01-15 | 189 | 120 | zamknięta | czas | 594.1 |
| EURUSD | short | 2009-08-31 | 2010-02-27 | 179 | 120 | zamknięta | czas | 576.5 |
| GBPUSD | short | 2009-09-16 | 2010-03-16 | 180 | 120 | zamknięta | czas | 1 403.7 |
| USDJPY | long | 2009-09-20 | 2010-03-11 | 171 | 120 | zamknięta | czas | -153.4 |
| EURJPY | short | 2009-09-23 | 2010-03-19 | 176 | 120 | zamknięta | czas | 1 063.5 |
| USDCAD | short | 2009-11-05 | 2010-04-23 | 170 | 120 | zamknięta | czas | 642.0 |
| EURGBP | long | 2009-12-24 | 2010-06-11 | 170 | 120 | zamknięta | czas | -652.7 |
| USDCHF | long | 2010-01-18 | 2010-07-02 | 166 | 120 | zamknięta | czas | 371.1 |
| AUDUSD | short | 2010-01-20 | 2010-07-07 | 169 | 120 | zamknięta | czas | 587.9 |
| EURUSD | long | 2010-03-01 | 2010-08-16 | 169 | 120 | zamknięta | czas | -830.9 |
| EURJPY | short | 2010-03-19 | 2010-09-06 | 172 | 120 | zamknięta | czas | 1 489.0 |
| USDJPY | short | 2010-03-23 | 2010-09-07 | 169 | 120 | zamknięta | czas | 656.6 |
| GBPUSD | long | 2010-03-30 | 2010-09-20 | 174 | 120 | zamknięta | czas | 475.7 |
| USDCAD | long | 2010-04-27 | 2010-10-13 | 169 | 120 | zamknięta | czas | -131.5 |
| EURGBP | long | 2010-06-13 | 2010-12-01 | 170 | 120 | zamknięta | czas | 15.3 |
| AUDUSD | long | 2010-07-07 | 2010-12-30 | 175 | 120 | zamknięta | czas | 1 537.4 |
| USDCHF | long | 2010-07-19 | 2011-01-07 | 171 | 120 | zamknięta | czas | -892.6 |
| EURUSD | long | 2010-08-29 | 2011-02-25 | 179 | 120 | zamknięta | czas | 1 068.2 |
| USDJPY | long | 2010-09-12 | 2011-03-05 | 173 | 120 | zamknięta | czas | -199.8 |
| EURJPY | short | 2010-10-10 | 2011-03-30 | 171 | 120 | zamknięta | czas | -308.3 |
| GBPUSD | short | 2010-10-12 | 2011-03-31 | 170 | 120 | zamknięta | czas | -222.9 |
| USDCAD | long | 2010-10-17 | 2011-04-06 | 171 | 120 | zamknięta | czas | -530.0 |
| EURGBP | long | 2010-12-03 | 2011-05-24 | 173 | 120 | zamknięta | czas | 234.3 |
| AUDUSD | short | 2011-01-05 | 2011-07-01 | 178 | 120 | zamknięta | czas | -703.6 |
| USDCHF | short | 2011-01-20 | 2011-07-07 | 169 | 120 | zamknięta | czas | 1 109.9 |
| USDJPY | long | 2011-03-07 | 2011-08-29 | 176 | 120 | zamknięta | czas | -541.7 |
| EURUSD | short | 2011-03-11 | 2011-08-30 | 173 | 120 | zamknięta | czas | -632.5 |
| GBPUSD | long | 2011-04-03 | 2011-09-21 | 171 | 120 | zamknięta | czas | -613.4 |
| EURJPY | short | 2011-04-13 | 2011-10-07 | 177 | 120 | zamknięta | czas | 1 820.9 |
| USDCAD | long | 2011-04-13 | 2011-10-04 | 174 | 120 | zamknięta | czas | 912.1 |
| EURGBP | long | 2011-05-31 | 2011-11-17 | 169 | 120 | zamknięta | czas | -207.7 |
| USDCHF | short | 2011-07-10 | 2011-12-27 | 169 | 120 | zamknięta | czas | -1 001.9 |
| AUDUSD | short | 2011-07-11 | 2011-12-31 | 172 | 120 | zamknięta | czas | 410.6 |
| EURUSD | short | 2011-08-31 | 2012-02-21 | 173 | 120 | zamknięta | czas | 1 169.3 |
| USDJPY | short | 2011-09-13 | 2012-03-07 | 175 | 120 | zamknięta | czas | -370.4 |
| USDCAD | short | 2011-10-06 | 2012-03-27 | 173 | 120 | zamknięta | czas | 423.0 |
| EURJPY | long | 2011-10-10 | 2012-04-02 | 175 | 120 | zamknięta | czas | 613.7 |
| GBPUSD | long | 2011-10-11 | 2012-03-28 | 169 | 120 | zamknięta | czas | 303.0 |
| EURGBP | long | 2011-11-21 | 2012-05-09 | 171 | 120 | zamknięta | czas | -567.8 |
| USDCHF | long | 2011-12-29 | 2012-06-25 | 180 | 120 | zamknięta | czas | 169.3 |
| AUDUSD | short | 2012-01-09 | 2012-06-28 | 172 | 120 | zamknięta | czas | 168.1 |
| EURUSD | short | 2012-03-02 | 2012-08-17 | 169 | 120 | zamknięta | czas | 984.6 |
| USDJPY | short | 2012-03-07 | 2012-08-30 | 177 | 120 | zamknięta | czas | 207.7 |
| GBPUSD | short | 2012-04-03 | 2012-09-20 | 170 | 120 | zamknięta | czas | -318.4 |
| EURJPY | long | 2012-04-18 | 2012-10-15 | 180 | 120 | zamknięta | czas | -451.4 |
| USDCAD | long | 2012-05-02 | 2012-10-19 | 170 | 120 | zamknięta | czas | 74.0 |
| EURGBP | long | 2012-05-17 | 2012-11-06 | 172 | 120 | zamknięta | czas | -38.7 |
| USDCHF | short | 2012-07-01 | 2012-12-18 | 169 | 120 | zamknięta | czas | 314.6 |
| AUDUSD | short | 2012-07-10 | 2013-01-04 | 177 | 120 | zamknięta | czas | -264.7 |
| USDJPY | long | 2012-09-06 | 2013-03-06 | 180 | 120 | zamknięta | czas | 1 436.6 |
| EURUSD | short | 2012-09-23 | 2013-03-15 | 172 | 120 | zamknięta | czas | -44.3 |
| GBPUSD | short | 2012-09-25 | 2013-03-15 | 170 | 120 | zamknięta | czas | 1 102.5 |
| EURJPY | short | 2012-10-29 | 2013-04-24 | 178 | 120 | zamknięta | czas | -2 638.2 |
| USDCAD | short | 2012-11-05 | 2013-04-24 | 171 | 120 | zamknięta | czas | -297.0 |
| EURGBP | long | 2012-11-14 | 2013-05-03 | 171 | 120 | zamknięta | czas | 415.6 |
| AUDUSD | long | 2013-01-04 | 2013-06-24 | 172 | 120 | zamknięta | czas | -1 190.8 |
| USDCHF | long | 2013-01-04 | 2013-06-21 | 169 | 120 | zamknięta | czas | 79.9 |
| GBPUSD | long | 2013-03-15 | 2013-08-30 | 169 | 120 | zamknięta | czas | 427.7 |
| USDJPY | short | 2013-03-18 | 2013-09-09 | 176 | 120 | zamknięta | czas | -482.6 |
| EURUSD | long | 2013-03-25 | 2013-09-09 | 169 | 120 | zamknięta | czas | 230.8 |
| USDCAD | short | 2013-04-25 | 2013-10-17 | 175 | 120 | zamknięta | czas | -99.0 |
| EURJPY | short | 2013-04-28 | 2013-10-25 | 180 | 120 | zamknięta | czas | -716.3 |
| EURGBP | long | 2013-05-08 | 2013-10-23 | 168 | 120 | zamknięta | czas | 55.3 |
| AUDUSD | long | 2013-07-09 | 2014-01-08 | 182 | 120 | zamknięta | czas | -249.1 |
| USDCHF | short | 2013-07-10 | 2014-01-01 | 174 | 120 | zamknięta | czas | 520.4 |
| GBPUSD | long | 2013-09-03 | 2014-02-25 | 174 | 120 | zamknięta | czas | 1 093.0 |
| EURUSD | long | 2013-09-09 | 2014-03-05 | 176 | 120 | zamknięta | czas | 486.2 |
| USDJPY | long | 2013-10-14 | 2014-04-22 | 190 | 120 | zamknięta | czas | 396.6 |
| USDCAD | long | 2013-10-23 | 2014-04-14 | 173 | 120 | zamknięta | czas | 587.6 |
| EURGBP | short | 2013-11-01 | 2014-04-23 | 174 | 120 | zamknięta | czas | 230.4 |
| EURJPY | short | 2013-11-01 | 2014-05-02 | 183 | 120 | zamknięta | czas | -828.0 |
| USDCHF | short | 2014-01-14 | 2014-07-01 | 169 | 120 | zamknięta | czas | 117.6 |
| AUDUSD | long | 2014-01-31 | 2014-07-18 | 169 | 120 | zamknięta | czas | 597.5 |
| EURUSD | short | 2014-03-20 | 2014-09-04 | 169 | 120 | zamknięta | czas | 887.1 |
| GBPUSD | long | 2014-03-27 | 2014-09-11 | 169 | 120 | zamknięta | czas | -330.5 |
| USDCAD | long | 2014-04-14 | 2014-09-30 | 169 | 120 | zamknięta | czas | 236.3 |
| USDJPY | short | 2014-04-24 | 2014-10-20 | 179 | 120 | zamknięta | czas | -461.4 |
| EURGBP | long | 2014-04-27 | 2014-10-10 | 166 | 120 | zamknięta | czas | -381.7 |
| EURJPY | short | 2014-05-06 | 2014-11-05 | 182 | 120 | zamknięta | czas | -31.5 |
| USDCHF | long | 2014-07-03 | 2014-12-25 | 174 | 120 | zamknięta | czas | 912.8 |
| AUDUSD | long | 2014-07-20 | 2015-01-13 | 176 | 120 | zamknięta | czas | -1 243.6 |
| EURUSD | long | 2014-09-16 | 2015-03-20 | 184 | 120 | zamknięta | czas | -2 287.3 |
| GBPUSD | long | 2014-09-16 | 2015-03-11 | 175 | 120 | zamknięta | czas | -1 191.9 |
| USDCAD | short | 2014-10-08 | 2015-04-03 | 177 | 120 | zamknięta | czas | -1 375.0 |
| EURGBP | short | 2014-10-20 | 2015-04-14 | 176 | 120 | zamknięta | czas | 710.5 |
| USDJPY | long | 2014-10-21 | 2015-04-24 | 185 | 120 | zamknięta | czas | 1 189.0 |
| EURJPY | short | 2014-12-11 | 2015-06-04 | 176 | 120 | zamknięta | czas | 743.2 |
| USDCHF | short | 2015-01-16 | 2015-07-06 | 172 | 120 | zamknięta | czas | -890.1 |
| AUDUSD | short | 2015-01-21 | 2015-07-13 | 174 | 120 | zamknięta | czas | 768.8 |
| GBPUSD | long | 2015-03-23 | 2015-09-11 | 173 | 120 | zamknięta | czas | 500.4 |
| EURUSD | short | 2015-03-31 | 2015-09-22 | 175 | 120 | zamknięta | czas | -381.9 |
| USDCAD | long | 2015-04-09 | 2015-09-28 | 172 | 120 | zamknięta | czas | 814.0 |
| EURGBP | long | 2015-04-29 | 2015-10-16 | 170 | 120 | zamknięta | czas | 153.3 |
| USDJPY | long | 2015-05-04 | 2015-11-03 | 182 | 120 | zamknięta | czas | 68.3 |
| EURJPY | short | 2015-06-11 | 2015-12-04 | 175 | 120 | zamknięta | czas | 506.4 |
| USDCHF | short | 2015-07-16 | 2016-01-09 | 176 | 120 | zamknięta | czas | -365.4 |
| AUDUSD | long | 2015-07-21 | 2016-01-09 | 171 | 120 | zamknięta | czas | -488.3 |
| GBPUSD | short | 2015-09-15 | 2016-03-08 | 174 | 120 | zamknięta | czas | 1 082.3 |
| EURUSD | long | 2015-09-28 | 2016-03-26 | 179 | 120 | zamknięta | czas | -74.5 |
| USDCAD | short | 2015-10-01 | 2016-03-24 | 174 | 120 | zamknięta | czas | 33.9 |
| USDJPY | short | 2015-11-16 | 2016-05-12 | 179 | 120 | zamknięta | czas | 1 316.5 |
| EURGBP | long | 2015-11-25 | 2016-05-12 | 170 | 120 | zamknięta | czas | 814.7 |
| EURJPY | short | 2015-12-14 | 2016-06-07 | 177 | 120 | zamknięta | czas | 1 094.0 |
| AUDUSD | long | 2016-01-22 | 2016-07-11 | 172 | 120 | zamknięta | czas | 519.8 |
| USDCHF | short | 2016-02-04 | 2016-07-21 | 169 | 120 | zamknięta | czas | 201.1 |
| GBPUSD | short | 2016-03-16 | 2016-09-02 | 171 | 120 | zamknięta | czas | 862.5 |
| USDCAD | long | 2016-03-24 | 2016-09-14 | 175 | 120 | zamknięta | czas | -16.4 |
| EURUSD | short | 2016-04-13 | 2016-10-04 | 174 | 120 | zamknięta | czas | 68.4 |
| EURGBP | short | 2016-05-12 | 2016-11-03 | 174 | 120 | zamknięta | czas | -1 143.9 |
| USDJPY | short | 2016-06-05 | 2016-11-24 | 171 | 120 | zamknięta | czas | -583.1 |
| EURJPY | long | 2016-06-23 | 2016-12-13 | 172 | 120 | zamknięta | czas | 347.6 |
| AUDUSD | short | 2016-07-19 | 2017-01-11 | 175 | 120 | zamknięta | czas | 147.5 |
| USDCHF | short | 2016-07-27 | 2017-01-14 | 170 | 120 | zamknięta | czas | -255.9 |
| GBPUSD | short | 2016-09-11 | 2017-03-03 | 172 | 120 | zamknięta | czas | 995.4 |
| USDCAD | long | 2016-09-14 | 2017-03-07 | 173 | 120 | zamknięta | czas | 205.2 |
| EURUSD | long | 2016-11-02 | 2017-04-25 | 175 | 120 | zamknięta | czas | -131.9 |
| EURGBP | short | 2016-11-04 | 2017-04-25 | 173 | 120 | zamknięta | czas | 387.3 |
| EURJPY | short | 2016-12-20 | 2017-06-20 | 183 | 120 | zamknięta | czas | -224.7 |
| AUDUSD | short | 2017-01-27 | 2017-07-18 | 173 | 120 | zamknięta | czas | -389.4 |
| USDCHF | long | 2017-02-08 | 2017-07-31 | 174 | 120 | zamknięta | czas | -306.6 |
| GBPUSD | long | 2017-03-16 | 2017-09-05 | 174 | 120 | zamknięta | czas | 756.4 |
| USDCAD | short | 2017-03-16 | 2017-09-06 | 175 | 120 | zamknięta | czas | 1 057.3 |
| EURGBP | long | 2017-05-04 | 2017-10-25 | 174 | 120 | zamknięta | czas | 409.4 |
| EURUSD | short | 2017-05-09 | 2017-10-31 | 174 | 120 | zamknięta | czas | -763.8 |
| USDJPY | short | 2017-05-16 | 2017-11-15 | 182 | 120 | zamknięta | czas | -70.2 |
| EURJPY | short | 2017-07-16 | 2018-01-18 | 185 | 120 | zamknięta | czas | -664.9 |
| AUDUSD | short | 2017-08-02 | 2018-01-27 | 177 | 120 | zamknięta | czas | -161.6 |
| USDCHF | short | 2017-08-09 | 2018-02-03 | 177 | 120 | zamknięta | czas | 320.7 |
| USDCAD | long | 2017-09-17 | 2018-03-10 | 173 | 120 | zamknięta | czas | 612.1 |
| GBPUSD | short | 2017-09-26 | 2018-03-20 | 174 | 120 | zamknięta | czas | -583.4 |
| EURGBP | long | 2017-11-03 | 2018-04-24 | 173 | 120 | zamknięta | czas | -190.7 |
| EURUSD | long | 2017-11-10 | 2018-05-02 | 174 | 120 | zamknięta | czas | 305.6 |
| USDJPY | long | 2017-12-01 | 2018-06-05 | 187 | 120 | zamknięta | czas | -269.6 |
| EURJPY | short | 2018-01-25 | 2018-07-19 | 176 | 120 | zamknięta | czas | 450.6 |
| AUDUSD | short | 2018-02-02 | 2018-07-27 | 176 | 120 | zamknięta | czas | 639.2 |
| USDCHF | long | 2018-02-07 | 2018-07-25 | 169 | 120 | zamknięta | czas | 545.7 |
| USDCAD | short | 2018-03-12 | 2018-08-29 | 171 | 120 | zamknięta | czas | -93.0 |
| GBPUSD | short | 2018-03-28 | 2018-09-14 | 170 | 120 | zamknięta | czas | 1 012.0 |
| EURGBP | short | 2018-04-26 | 2018-10-15 | 172 | 120 | zamknięta | czas | -107.6 |
| EURUSD | long | 2018-05-13 | 2018-11-01 | 171 | 120 | zamknięta | czas | -638.6 |
| USDJPY | long | 2018-06-05 | 2018-12-01 | 178 | 120 | zamknięta | czas | 352.4 |
| EURJPY | short | 2018-07-22 | 2019-01-15 | 176 | 120 | zamknięta | czas | 618.7 |
| USDCHF | long | 2018-08-02 | 2019-01-24 | 174 | 120 | zamknięta | czas | -12.7 |
| AUDUSD | long | 2018-08-20 | 2019-02-12 | 175 | 120 | zamknięta | czas | -273.8 |
| USDCAD | long | 2018-09-03 | 2019-03-02 | 179 | 120 | zamknięta | czas | 186.1 |
| GBPUSD | short | 2018-09-23 | 2019-03-15 | 172 | 120 | zamknięta | czas | -177.9 |
| EURGBP | short | 2018-11-05 | 2019-04-29 | 176 | 120 | zamknięta | czas | 114.3 |
| EURUSD | long | 2018-11-05 | 2019-04-25 | 172 | 120 | zamknięta | czas | -260.9 |
| USDJPY | short | 2018-12-05 | 2019-06-07 | 185 | 120 | zamknięta | czas | 423.6 |
| USDCHF | short | 2019-01-28 | 2019-07-19 | 173 | 120 | zamknięta | czas | 96.7 |
| EURJPY | short | 2019-02-05 | 2019-08-02 | 179 | 120 | zamknięta | czas | 737.9 |
| AUDUSD | long | 2019-02-18 | 2019-08-09 | 173 | 120 | zamknięta | czas | -365.3 |
| USDCAD | long | 2019-03-04 | 2019-08-23 | 173 | 120 | zamknięta | czas | 25.9 |
| GBPUSD | short | 2019-03-22 | 2019-09-09 | 172 | 120 | zamknięta | czas | 782.3 |
| EURUSD | long | 2019-04-30 | 2019-10-17 | 170 | 120 | zamknięta | czas | -92.0 |
| EURGBP | long | 2019-05-08 | 2019-10-29 | 173 | 120 | zamknięta | czas | 26.0 |
| USDJPY | long | 2019-06-11 | 2019-12-05 | 176 | 120 | zamknięta | czas | 34.0 |
| USDCHF | long | 2019-07-25 | 2020-01-22 | 180 | 120 | zamknięta | czas | -223.1 |
| AUDUSD | long | 2019-08-13 | 2020-02-13 | 183 | 120 | zamknięta | czas | -85.4 |
| EURJPY | long | 2019-08-21 | 2020-02-14 | 176 | 120 | zamknięta | czas | 78.5 |
| USDCAD | short | 2019-08-26 | 2020-02-21 | 178 | 120 | zamknięta | czas | -9.5 |
| GBPUSD | short | 2019-09-23 | 2020-03-14 | 172 | 120 | zamknięta | czas | 33.8 |
| EURUSD | short | 2019-10-28 | 2020-04-21 | 177 | 120 | zamknięta | czas | 226.4 |
| EURGBP | long | 2019-10-30 | 2020-04-22 | 176 | 120 | zamknięta | czas | 131.6 |
| USDCHF | long | 2020-01-22 | 2020-07-15 | 176 | 120 | zamknięta | czas | -250.8 |
| EURJPY | long | 2020-02-20 | 2020-08-20 | 183 | 120 | zamknięta | czas | 519.5 |
| USDCAD | long | 2020-02-25 | 2020-08-17 | 175 | 120 | zamknięta | czas | -69.4 |
| AUDUSD | long | 2020-03-06 | 2020-08-21 | 169 | 120 | zamknięta | czas | 540.9 |
| USDJPY | long | 2020-03-17 | 2020-09-09 | 177 | 120 | zamknięta | czas | -3.5 |
| GBPUSD | long | 2020-03-27 | 2020-09-22 | 180 | 120 | zamknięta | czas | 548.7 |
| EURUSD | long | 2020-04-29 | 2020-10-27 | 180 | 120 | zamknięta | czas | 931.9 |
| EURGBP | long | 2020-05-03 | 2020-10-21 | 171 | 120 | zamknięta | czas | 227.7 |
| USDCHF | long | 2020-07-15 | 2021-01-07 | 175 | 120 | zamknięta | czas | -660.7 |
| EURJPY | short | 2020-08-20 | 2021-02-13 | 176 | 120 | zamknięta | czas | -192.7 |
| AUDUSD | short | 2020-08-23 | 2021-02-18 | 178 | 120 | zamknięta | czas | -599.8 |
| USDCAD | long | 2020-09-08 | 2021-03-03 | 175 | 120 | zamknięta | czas | -604.4 |
| USDJPY | long | 2020-09-23 | 2021-03-25 | 182 | 120 | zamknięta | czas | 344.5 |
| GBPUSD | long | 2020-09-28 | 2021-03-24 | 176 | 120 | zamknięta | czas | 861.9 |
| EURUSD | short | 2020-10-28 | 2021-04-19 | 174 | 120 | zamknięta | czas | -263.1 |
| EURGBP | long | 2020-11-05 | 2021-04-27 | 174 | 120 | zamknięta | czas | -356.8 |
| USDCHF | long | 2021-01-08 | 2021-06-25 | 169 | 120 | zamknięta | czas | 311.9 |
| AUDUSD | short | 2021-03-01 | 2021-08-19 | 172 | 120 | zamknięta | czas | 604.0 |
| USDCAD | short | 2021-03-10 | 2021-08-31 | 175 | 120 | zamknięta | czas | 28.6 |
| EURJPY | short | 2021-03-22 | 2021-09-15 | 178 | 120 | zamknięta | czas | 8.7 |
| GBPUSD | long | 2021-03-31 | 2021-09-20 | 173 | 120 | zamknięta | czas | -129.6 |
| USDJPY | short | 2021-04-06 | 2021-09-30 | 177 | 120 | zamknięta | czas | -169.5 |
| EURUSD | short | 2021-05-02 | 2021-10-15 | 166 | 120 | zamknięta | czas | 429.6 |
| EURGBP | short | 2021-05-03 | 2021-10-20 | 170 | 120 | zamknięta | czas | 243.5 |
| USDCHF | short | 2021-07-08 | 2021-12-28 | 172 | 120 | zamknięta | czas | -24.8 |
| AUDUSD | long | 2021-08-29 | 2022-02-18 | 172 | 120 | zamknięta | czas | -132.5 |
| USDCAD | long | 2021-09-07 | 2022-02-25 | 170 | 120 | zamknięta | czas | 158.4 |
| EURJPY | long | 2021-09-23 | 2022-03-17 | 174 | 120 | zamknięta | czas | 148.5 |
| GBPUSD | long | 2021-10-04 | 2022-03-26 | 172 | 120 | zamknięta | czas | -432.2 |
| USDJPY | short | 2021-10-24 | 2022-04-15 | 173 | 120 | zamknięta | czas | -1 299.4 |
| EURUSD | short | 2021-10-26 | 2022-04-15 | 171 | 120 | zamknięta | czas | 782.1 |
| EURGBP | long | 2021-10-27 | 2022-04-14 | 169 | 120 | zamknięta | czas | -172.6 |
| USDCHF | long | 2022-01-04 | 2022-06-21 | 169 | 120 | zamknięta | czas | 475.3 |
| AUDUSD | short | 2022-02-25 | 2022-08-22 | 179 | 120 | zamknięta | czas | 279.8 |
| USDCAD | short | 2022-03-01 | 2022-08-16 | 169 | 120 | zamknięta | czas | -182.4 |
| GBPUSD | short | 2022-03-28 | 2022-09-16 | 172 | 120 | zamknięta | czas | 1 662.1 |
| EURJPY | short | 2022-04-06 | 2022-09-29 | 176 | 120 | zamknięta | czas | -715.4 |
| EURUSD | long | 2022-04-20 | 2022-10-07 | 170 | 120 | zamknięta | czas | -1 115.8 |
| EURGBP | long | 2022-04-21 | 2022-10-07 | 169 | 120 | zamknięta | czas | 450.0 |
| USDJPY | short | 2022-04-26 | 2022-10-26 | 183 | 120 | zamknięta | czas | -1 888.2 |
| USDCHF | long | 2022-07-04 | 2022-12-23 | 171 | 120 | zamknięta | czas | -300.2 |
| AUDUSD | long | 2022-08-25 | 2023-02-11 | 169 | 120 | zamknięta | czas | -52.2 |
| USDCAD | short | 2022-08-25 | 2023-02-17 | 175 | 120 | zamknięta | czas | -537.4 |
| EURJPY | long | 2022-09-29 | 2023-03-27 | 179 | 120 | zamknięta | czas | -16.5 |
| GBPUSD | long | 2022-09-29 | 2023-03-17 | 168 | 120 | zamknięta | czas | 948.5 |
| EURUSD | short | 2022-10-09 | 2023-03-27 | 169 | 120 | zamknięta | czas | -1 073.0 |
| EURGBP | long | 2022-10-11 | 2023-03-31 | 171 | 120 | zamknięta | czas | -53.7 |
| USDJPY | long | 2022-11-22 | 2023-05-11 | 171 | 120 | zamknięta | czas | -761.4 |
| USDCHF | long | 2022-12-23 | 2023-06-12 | 172 | 120 | zamknięta | czas | -228.9 |
| AUDUSD | long | 2023-03-15 | 2023-09-01 | 171 | 120 | zamknięta | czas | -237.9 |
| USDCAD | short | 2023-03-15 | 2023-09-01 | 171 | 120 | zamknięta | czas | 92.4 |
| EURUSD | short | 2023-04-02 | 2023-09-20 | 171 | 120 | zamknięta | czas | 149.4 |
| EURJPY | short | 2023-04-05 | 2023-09-28 | 176 | 120 | zamknięta | czas | -1 503.2 |
| GBPUSD | short | 2023-04-10 | 2023-09-27 | 170 | 120 | zamknięta | czas | 256.4 |
| EURGBP | long | 2023-04-11 | 2023-09-27 | 169 | 120 | zamknięta | czas | -126.8 |
| USDJPY | long | 2023-05-14 | 2023-11-10 | 179 | 120 | zamknięta | czas | 1 551.3 |
| USDCHF | long | 2023-06-28 | 2023-12-19 | 173 | 120 | zamknięta | czas | -297.4 |
| AUDUSD | short | 2023-09-05 | 2024-03-01 | 177 | 120 | zamknięta | czas | -124.7 |
| USDCAD | short | 2023-09-11 | 2024-03-02 | 172 | 120 | zamknięta | czas | 24.3 |
| EURGBP | short | 2023-09-28 | 2024-03-20 | 173 | 120 | zamknięta | czas | 112.1 |
| EURUSD | long | 2023-10-05 | 2024-03-29 | 175 | 120 | zamknięta | czas | 246.9 |
| GBPUSD | long | 2023-10-05 | 2024-03-28 | 174 | 120 | zamknięta | czas | 426.9 |
| EURJPY | short | 2023-10-30 | 2024-04-25 | 179 | 120 | zamknięta | czas | -878.3 |
| USDJPY | short | 2023-11-15 | 2024-05-10 | 178 | 120 | zamknięta | czas | -534.7 |
| USDCHF | long | 2024-01-05 | 2024-06-21 | 169 | 120 | zamknięta | czas | 439.1 |
| AUDUSD | long | 2024-03-07 | 2024-08-30 | 177 | 120 | zamknięta | czas | 200.0 |
| USDCAD | short | 2024-03-07 | 2024-08-23 | 170 | 120 | zamknięta | czas | 2.7 |
| EURGBP | short | 2024-03-29 | 2024-09-13 | 169 | 120 | zamknięta | czas | 105.5 |
| EURUSD | long | 2024-04-03 | 2024-09-20 | 170 | 120 | zamknięta | czas | 321.6 |
| GBPUSD | long | 2024-04-03 | 2024-09-23 | 173 | 120 | zamknięta | czas | 694.3 |
| EURJPY | short | 2024-05-02 | 2024-10-25 | 176 | 120 | zamknięta | czas | -92.9 |
| USDJPY | short | 2024-05-15 | 2024-11-07 | 175 | 120 | zamknięta | czas | -4.0 |
| USDCHF | long | 2024-06-23 | 2024-12-14 | 173 | 120 | zamknięta | czas | -22.8 |
| AUDUSD | short | 2024-09-03 | 2025-02-25 | 174 | 120 | zamknięta | czas | 373.3 |
| USDCAD | long | 2024-09-03 | 2025-02-28 | 177 | 120 | zamknięta | czas | 899.7 |
| EURUSD | short | 2024-09-30 | 2025-03-26 | 176 | 120 | zamknięta | czas | 345.9 |
| GBPUSD | short | 2024-10-01 | 2025-03-26 | 175 | 120 | zamknięta | czas | 328.8 |
| EURGBP | long | 2024-10-03 | 2025-03-26 | 173 | 120 | zamknięta | czas | -73.6 |
| EURJPY | short | 2024-11-08 | 2025-05-09 | 183 | 120 | zamknięta | czas | 180.9 |
| USDJPY | short | 2024-11-25 | 2025-05-27 | 184 | 120 | zamknięta | czas | 994.3 |
| USDCHF | short | 2025-01-17 | 2025-07-14 | 179 | 120 | zamknięta | czas | 1 130.8 |
| AUDUSD | short | 2025-02-25 | 2025-08-20 | 177 | 120 | zamknięta | czas | -98.0 |
| USDCAD | short | 2025-03-06 | 2025-08-26 | 174 | 120 | zamknięta | czas | 503.2 |
| EURGBP | long | 2025-03-31 | 2025-09-19 | 172 | 120 | zamknięta | czas | 345.2 |
| GBPUSD | long | 2025-04-02 | 2025-09-29 | 180 | 120 | zamknięta | czas | 387.9 |
| EURUSD | short | 2025-04-30 | 2025-10-21 | 174 | 120 | zamknięta | czas | -279.6 |
| EURJPY | short | 2025-05-15 | 2025-11-13 | 181 | 120 | zamknięta | czas | -1 639.1 |
| USDJPY | long | 2025-05-28 | 2025-11-26 | 181 | 120 | zamknięta | czas | 1 047.5 |
| USDCHF | short | 2025-07-21 | 2026-01-15 | 177 | 120 | zamknięta | czas | -18.3 |
| AUDUSD | long | 2025-08-25 | 2026-02-19 | 177 | 120 | zamknięta | czas | 562.7 |
| USDCAD | short | 2025-08-26 | 2026-02-18 | 175 | 120 | zamknięta | czas | 193.8 |
| EURGBP | short | 2025-10-01 | 2026-03-25 | 174 | 120 | zamknięta | czas | 45.9 |
| GBPUSD | long | 2025-10-01 | 2026-03-25 | 174 | 120 | zamknięta | czas | -62.2 |
| EURUSD | long | 2025-11-10 | 2026-05-04 | 176 | 120 | zamknięta | czas | 137.7 |
| USDJPY | short | 2025-11-28 | 2026-05-27 | 181 | 120 | zamknięta | czas | -322.9 |
| EURJPY | short | 2025-12-02 | 2026-05-27 | 177 | 120 | zamknięta | czas | -491.1 |
| USDCHF | short | 2026-01-20 | 2026-07-07 | 169 | 120 | zamknięta | czas | -107.5 |
| AUDUSD | short | 2026-02-19 | 2026-08-18 | 181 | 120 | zamknięta | czas | -44.3 |
| USDCAD | short | 2026-03-02 | 2026-08-19 | 171 | 120 | zamknięta | czas | -141.0 |
| GBPUSD | short | 2026-03-27 | 2026-09-14 | 172 | 120 | zamknięta | czas | -170.6 |
| EURGBP | short | 2026-04-08 | 2026-09-25 | 170 | 120 | zamknięta | czas | 101.6 |
| EURUSD | long | 2026-05-28 | 2026-11-18 | 173 | 120 | zamknięta | czas | -658.0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 56.04 pips/transakcję, percentyl **97.2** (losowe: 5%=-75.34, mediana=-14.46, 95%=43.45).

- **Deflated Sharpe Ratio**: 0.557 (Sharpe na transakcję 0.088, próg przy 699 próbach 0.079).

- **PBO** (CSCV, 16 bloków, 699 wariantów): 0.085 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 332 transakcji, śr. 24.17 pips, 0.34 R.

- **Bootstrap 95%** średnich pipsów: całość [-21.90; 130.54], OOS [-80.39; 130.18].

- **Spread**: ×1 56.04, ×1,5 55.21, ×2 54.39 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 173.1 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -30.51, 1 pips: -117.07 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058)

HYPOTHESIS = """ALMA (Arnaud Legoux, 2009) waży ceny krzywą Gaussa przesuniętą ku najnowszym świecom, więc zawraca
wcześniej niż SMA o podobnej długości i mniej szarpie niż EMA. Jeśli trendy na parach FX trwają tygodniami, to wcześniejsze
wykrycie zwrotu średniej zostawia większą część ruchu niż spóźniona SMA. Pojedyncze „mignięcia” kierunku to szum,
więc liczy się tylko zwrot po ruchu, który trwał co najmniej kilka dni. Ryzyko: trzy pokrętła (długość, offset, sigma)
i każde to kompromis — offset 0,99 szybki, ale nerwowy, 0,5 gładki, ale spóźniony. Start od domyślnych 9 · 0,85 · 6.
Wersja 2: mniej wariantów i bez trybu „przecięcie” — wersja 1 dała 444 MB transakcji, a GitHub przyjmuje do 100 MB."""

# n = długość, offset, sigma, min = ile dni ALMA musiała iść w starą stronę, żeby zwrot się liczył
CONFIGS = [
    {"n": 9, "offset": 0.85, "sigma": 6, "min": 3},    # ustawienia domyślne
    {"n": 21, "offset": 0.85, "sigma": 6, "min": 3},   # wolniejsza, porównywalna z SMA 20
    {"n": 21, "offset": 0.99, "sigma": 6, "min": 5},   # szybka (nerwowa), więc ostrzejsze potwierdzenie
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    a = ind.alma(df.close, c["n"], c["offset"], c["sigma"])
    d = a.diff()
    side = (d > 0).astype(int) - (d < 0).astype(int)          # +1 rośnie, -1 spada, 0 stoi / rozgrzewka
    run = side.groupby((side != side.shift()).cumsum()).cumcount() + 1   # ile dni z rzędu w tym kierunku
    prev_side, prev_run = side.shift(1), run.shift(1)
    long_ = (side == 1) & (prev_side == -1) & (prev_run >= c["min"])
    short = (side == -1) & (prev_side == 1) & (prev_run >= c["min"])
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
