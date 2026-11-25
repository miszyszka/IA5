# Raport strategii: codzienna

Run `20261125-182413` · silnik 0.14.0 · kod `b9a365c12f52bd73` · dane `02cdfcd25d7e5788`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -12.41 |
| percentyl benchmarku ≥ 95 | ✘ | 33.20 |
| PBO < 0,3 | ✘ | 0.43 |
| DSR ≥ 0,95 | ✘ | 0.06 |
| dodatni przy spreadzie ×1,5 | ✘ | -1.45 |

## Hipoteza

Mały TP i ogromny SL: cena często dochodzi do bliskiego celu w kierunku długiego trendu, a daleki stop
rzadko pada. Kierunek z długiej EMA: tryb „trend” — EMA rośnie → long, spada → short; tryb „hamowanie” — spadek EMA
zwalnia → long, wzrost EMA zwalnia → short (wejście przed zawróceniem). Wysoki win rate jest tu pewny — pytanie, czy rzadkie
duże straty na SL go nie zjadają.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-24; źródło: yahoo.

- In-sample do 2019-05-19, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS. OOS tego okresu widziało już 4 wersji kodu strategii i 5 kandydatów eksploracji; ta strategia: 1 wersji.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 149, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 118, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 72** (8 wejścia × 9 wyjść).

- Pominięte sygnały, średnio na wariant: 27,681 (limit otwartych pozycji w parze), 26.3 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 47.8 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1× SL 5× max 60 | mode=trend, ema=100, k=20 | 2 808 | 0.01 | 4.73 | 83.0 | 1 276 | -0.03 | -12.41 |
| 2 | ATR14 TP 1× SL 10× max 60 | mode=trend, ema=100, k=20 | 2 005 | -0.00 | -0.39 | 84.0 | 921 | 0.00 | 3.35 |
| 3 | ATR14 TP 1× SL 10× max 60 | mode=trend, ema=200, k=5 | 1 954 | -0.00 | -2.21 | 83.9 | 913 | 0.01 | 7.66 |
| 4 | ATR14 TP 1× SL 5× max 60 | mode=trend, ema=200, k=20 | 2 691 | -0.00 | 0.19 | 82.3 | 1 287 | -0.02 | -7.89 |
| 5 | ATR14 TP 0.3× SL 10× max 60 | mode=trend, ema=200, k=20 | 5 241 | -0.00 | -2.55 | 94.8 | 2 472 | -0.00 | -3.32 |
| 6 | ATR14 TP 0.5× SL 10× max 60 | mode=trend, ema=200, k=20 | 3 511 | -0.00 | -2.40 | 91.5 | 1 699 | -0.00 | 0.22 |
| 7 | ATR14 TP 0.5× SL 5× max 60 | mode=trend, ema=100, k=20 | 5 027 | -0.00 | -1.30 | 90.4 | 2 272 | -0.01 | -4.09 |
| 8 | ATR14 TP 1× SL 10× max 60 | mode=trend, ema=100, k=5 | 1 974 | -0.00 | -3.40 | 83.6 | 897 | -0.01 | -5.53 |
| 9 | ATR14 TP 0.3× SL 10× max 60 | mode=trend, ema=200, k=5 | 5 228 | -0.00 | -2.94 | 94.7 | 2 417 | -0.00 | -2.67 |
| 10 | ATR14 TP 0.3× SL 10× max 60 | mode=trend, ema=100, k=5 | 5 377 | -0.00 | -3.01 | 94.8 | 2 364 | -0.00 | -4.67 |

## Najlepszy wariant IS: ATR14 TP 1× SL 5× max 60 (mode=trend, ema=100, k=20)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 455 | -5.5 | -2 505.1 | 80.7 |
| EURGBP | 547 | -5.0 | -2 714.1 | 80.6 |
| EURJPY | 497 | -0.4 | -213.7 | 81.7 |
| EURUSD | 485 | 3.6 | 1 757.1 | 83.3 |
| GBPUSD | 481 | -2.8 | -1 368.1 | 81.7 |
| USDCAD | 496 | 8.6 | 4 268.6 | 84.3 |
| USDCHF | 485 | -1.7 | -823.0 | 82.5 |
| USDJPY | 638 | -1.5 | -955.9 | 82.6 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 1997 | 10 | 50.4 | 503.9 | 90.0 |
| 1998 | 24 | -26.8 | -642.3 | 79.2 |
| 1999 | 28 | 12.8 | 357.1 | 85.7 |
| 2000 | 40 | 33.1 | 1 323.8 | 90.0 |
| 2001 | 43 | 12.3 | 528.9 | 81.4 |
| 2002 | 39 | 15.0 | 586.9 | 82.1 |
| 2003 | 48 | 20.9 | 1 001.0 | 85.4 |
| 2004 | 110 | -10.2 | -1 118.8 | 79.1 |
| 2005 | 152 | 5.2 | 787.8 | 84.9 |
| 2006 | 123 | -2.5 | -303.5 | 81.3 |
| 2007 | 216 | 8.6 | 1 853.4 | 84.3 |
| 2008 | 202 | 55.5 | 11 202.7 | 86.6 |
| 2009 | 148 | -28.3 | -4 195.0 | 78.4 |
| 2010 | 154 | -3.8 | -584.0 | 81.8 |
| 2011 | 184 | 15.0 | 2 764.0 | 85.3 |
| 2012 | 159 | -24.0 | -3 819.0 | 78.6 |
| 2013 | 187 | 4.6 | 867.5 | 84.0 |
| 2014 | 189 | 10.0 | 1 880.8 | 85.7 |
| 2015 | 163 | -5.7 | -931.7 | 83.4 |
| 2016 | 200 | 30.1 | 6 020.6 | 86.5 |
| 2017 | 167 | -6.1 | -1 010.8 | 82.0 |
| 2018 | 165 | -12.6 | -2 081.8 | 79.4 |
| 2019 | 147 | -21.7 | -3 187.5 | 78.2 |
| 2020 | 178 | -3.9 | -693.1 | 81.5 |
| 2021 | 162 | -6.2 | -1 007.7 | 80.9 |
| 2022 | 196 | -6.9 | -1 344.8 | 82.1 |
| 2023 | 165 | -29.4 | -4 858.3 | 75.2 |
| 2024 | 172 | -24.0 | -4 128.8 | 79.1 |
| 2025 | 138 | -11.3 | -1 565.1 | 79.7 |
| 2026 | 175 | -4.3 | -760.3 | 82.9 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 2808 | 4.7 | 13 287.1 | 83.0 |
| OOS | 1276 | -12.4 | -15 841.3 | 80.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 75 | -99.2 | -15.3 | -99.9 | -124.7 | -0.17 | 0 |
| 10.0% | -6 878 | -168.8 | -100.0 | -121.7 | -198.9 | 0.25 | 3057 |
| 15.0% | -1 291 | -112.9 | -100.0 | -104.3 | -109.0 | 0.35 | 3238 |
| 20.0% | -74 | -100.7 | -100.0 | -100.3 | -106.9 | 0.16 | 3376 |
| 30.0% | -1 | -100.0 | -100.0 | -100.0 | -101.2 | 0.10 | 3855 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-24): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **4084**, otwarte: **0** (razem 4084).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 4084 | 1 | 8 | 17 | 47 | 94 | -0.6 | -2 554 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 4084 | 1 | 8 | 17 | 47 | 94 | -0.6 | -2 554 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDJPY | long | 1997-05-28 | 1997-07-29 | 62 | 33 | zamknięta | TP | 188.1 |
| USDJPY | short | 1998-10-18 | 1999-01-08 | 81 | 57 | zamknięta | TP | 365.9 |
| USDJPY | short | 1999-02-18 | 1999-05-12 | 84 | 60 | zamknięta | czas | -230.4 |
| EURGBP | short | 1999-07-19 | 1999-09-09 | 52 | 38 | zamknięta | TP | 56.4 |
| USDJPY | short | 1999-09-15 | 1999-11-27 | 72 | 52 | zamknięta | TP | 178.2 |
| EURGBP | short | 1999-09-27 | 1999-11-27 | 60 | 44 | zamknięta | TP | 66.0 |
| USDJPY | short | 1999-12-01 | 2000-02-03 | 64 | 46 | zamknięta | SL | -687.8 |
| USDJPY | long | 2000-03-02 | 2000-05-01 | 61 | 43 | zamknięta | TP | 146.0 |
| EURGBP | short | 2000-05-23 | 2000-08-03 | 72 | 52 | zamknięta | TP | 89.6 |
| USDJPY | long | 2000-06-01 | 2000-08-24 | 84 | 60 | zamknięta | czas | -170.4 |
| EURGBP | long | 2001-01-08 | 2001-03-30 | 82 | 60 | zamknięta | czas | -187.7 |
| USDJPY | long | 2001-01-16 | 2001-03-09 | 52 | 38 | zamknięta | TP | 111.0 |
| USDJPY | long | 2001-04-01 | 2001-05-31 | 60 | 44 | zamknięta | SL | -756.3 |
| EURGBP | long | 2001-04-03 | 2001-06-26 | 84 | 60 | zamknięta | czas | -166.7 |
| EURGBP | long | 2001-09-19 | 2001-12-13 | 84 | 60 | zamknięta | czas | -106.7 |
| USDJPY | short | 2001-09-20 | 2001-11-23 | 63 | 45 | zamknięta | SL | -712.4 |
| EURGBP | short | 2002-02-01 | 2002-04-25 | 84 | 60 | zamknięta | czas | -83.7 |
| USDJPY | long | 2002-03-25 | 2002-05-17 | 54 | 40 | zamknięta | SL | -658.8 |
| EURGBP | long | 2002-06-06 | 2002-07-29 | 53 | 37 | zamknięta | SL | -220.9 |
| USDJPY | short | 2002-07-15 | 2002-09-13 | 60 | 44 | zamknięta | SL | -597.0 |
| EURGBP | long | 2002-08-11 | 2002-11-02 | 82 | 60 | zamknięta | czas | -5.7 |
| USDJPY | short | 2002-09-15 | 2002-11-09 | 54 | 40 | zamknięta | TP | 129.5 |
| USDJPY | long | 2002-12-24 | 2003-02-12 | 50 | 34 | zamknięta | TP | 116.5 |
| USDJPY | short | 2003-05-19 | 2003-08-11 | 84 | 60 | zamknięta | czas | -144.4 |
| EURGBP | long | 2003-07-20 | 2003-10-10 | 82 | 60 | zamknięta | czas | -33.7 |
| EURGBP | long | 2003-10-12 | 2004-01-07 | 86 | 60 | zamknięta | czas | -107.7 |
| USDJPY | short | 2003-10-12 | 2003-12-09 | 57 | 41 | zamknięta | TP | 102.6 |
| USDCHF | short | 2004-03-19 | 2004-06-04 | 78 | 56 | zamknięta | TP | 175.5 |
| EURGBP | short | 2004-04-06 | 2004-06-30 | 85 | 60 | zamknięta | czas | -114.7 |
| USDJPY | short | 2004-04-14 | 2004-06-24 | 71 | 51 | zamknięta | TP | 124.1 |
| EURJPY | short | 2004-04-29 | 2004-07-22 | 84 | 60 | zamknięta | czas | -304.1 |
| USDCAD | long | 2004-05-10 | 2004-06-30 | 51 | 36 | zamknięta | SL | -583.6 |
| GBPUSD | short | 2004-05-18 | 2004-07-07 | 50 | 36 | zamknięta | SL | -878.3 |
| EURUSD | short | 2004-05-19 | 2004-08-11 | 84 | 60 | zamknięta | czas | -218.9 |
| USDJPY | short | 2004-06-29 | 2004-09-21 | 84 | 60 | zamknięta | czas | -158.4 |
| USDCAD | long | 2004-06-30 | 2004-09-22 | 84 | 60 | zamknięta | czas | -505.0 |
| USDCHF | short | 2004-07-11 | 2004-10-01 | 82 | 60 | zamknięta | czas | -279.9 |
| EURJPY | long | 2004-08-15 | 2004-11-09 | 85 | 60 | zamknięta | czas | -50.1 |
| EURUSD | short | 2004-08-24 | 2004-10-20 | 57 | 41 | zamknięta | SL | -493.4 |
| USDJPY | short | 2004-11-29 | 2005-01-15 | 47 | 35 | zamknięta | TP | 86.7 |
| USDCAD | short | 2004-12-31 | 2005-03-26 | 85 | 60 | zamknięta | czas | -138.0 |
| EURUSD | long | 2005-01-13 | 2005-03-10 | 56 | 40 | zamknięta | TP | 119.7 |
| USDCHF | short | 2005-01-13 | 2005-03-11 | 57 | 41 | zamknięta | TP | 125.9 |
| USDJPY | short | 2005-01-17 | 2005-03-28 | 71 | 50 | zamknięta | SL | -530.0 |
| EURJPY | short | 2005-02-17 | 2005-05-02 | 75 | 51 | zamknięta | TP | 104.9 |
| EURGBP | long | 2005-03-31 | 2005-05-27 | 57 | 41 | zamknięta | TP | 36.4 |
| USDCHF | long | 2005-07-03 | 2005-09-01 | 60 | 43 | zamknięta | SL | -554.2 |
| USDJPY | long | 2005-07-19 | 2005-09-05 | 48 | 34 | zamknięta | SL | -402.5 |
| EURJPY | short | 2005-07-21 | 2005-10-17 | 88 | 60 | zamknięta | czas | -401.1 |
| EURGBP | long | 2005-08-16 | 2005-10-07 | 52 | 37 | zamknięta | TP | 40.7 |
| USDCAD | short | 2005-09-19 | 2005-12-03 | 74 | 53 | zamknięta | TP | 98.9 |
| EURUSD | short | 2005-11-11 | 2006-01-24 | 74 | 51 | zamknięta | SL | -520.0 |
| USDCHF | long | 2005-11-15 | 2006-01-24 | 70 | 50 | zamknięta | SL | -602.3 |
| GBPUSD | short | 2005-11-17 | 2006-01-24 | 68 | 47 | zamknięta | SL | -691.8 |
| EURGBP | short | 2005-12-12 | 2006-03-04 | 82 | 60 | zamknięta | czas | -138.7 |
| EURUSD | long | 2006-01-24 | 2006-04-17 | 84 | 60 | zamknięta | czas | -52.9 |
| GBPUSD | long | 2006-02-01 | 2006-04-19 | 78 | 56 | zamknięta | TP | 134.2 |
| USDJPY | long | 2006-02-03 | 2006-04-28 | 85 | 60 | zamknięta | czas | -479.4 |
| USDCHF | long | 2006-02-27 | 2006-04-18 | 51 | 37 | zamknięta | SL | -482.4 |
| USDCAD | short | 2006-05-09 | 2006-07-24 | 76 | 54 | zamknięta | SL | -450.3 |
| EURUSD | long | 2006-05-14 | 2006-08-04 | 82 | 60 | zamknięta | czas | -90.0 |
| USDCHF | short | 2006-05-14 | 2006-07-19 | 66 | 48 | zamknięta | SL | -645.2 |
| GBPUSD | long | 2006-05-17 | 2006-08-04 | 79 | 56 | zamknięta | TP | 160.6 |
| EURGBP | short | 2006-06-12 | 2006-08-03 | 52 | 38 | zamknięta | TP | 33.0 |
| USDJPY | long | 2006-07-17 | 2006-09-12 | 57 | 41 | zamknięta | TP | 97.0 |
| USDCAD | long | 2006-07-31 | 2006-10-17 | 78 | 56 | zamknięta | TP | 87.2 |
| USDCHF | short | 2006-08-01 | 2006-10-25 | 85 | 60 | zamknięta | czas | -375.9 |
| EURUSD | long | 2006-08-06 | 2006-10-31 | 85 | 60 | zamknięta | czas | -165.9 |
| GBPUSD | long | 2006-08-06 | 2006-11-01 | 86 | 60 | zamknięta | czas | 6.5 |
| EURGBP | short | 2006-08-08 | 2006-09-26 | 49 | 35 | zamknięta | TP | 30.8 |
| EURJPY | long | 2006-08-30 | 2006-11-10 | 71 | 51 | zamknięta | TP | 81.4 |
| EURGBP | short | 2006-09-26 | 2006-12-09 | 73 | 53 | zamknięta | SL | -148.1 |
| GBPUSD | long | 2006-12-04 | 2007-03-01 | 87 | 60 | zamknięta | czas | -179.0 |
| USDCHF | short | 2007-01-09 | 2007-02-28 | 50 | 36 | zamknięta | TP | 91.7 |
| USDCAD | long | 2007-01-23 | 2007-04-11 | 79 | 57 | zamknięta | SL | -366.4 |
| EURGBP | short | 2007-02-26 | 2007-05-18 | 82 | 60 | zamknięta | czas | -138.7 |
| USDCHF | short | 2007-03-19 | 2007-06-08 | 82 | 60 | zamknięta | czas | -302.9 |
| AUDUSD | long | 2007-04-15 | 2007-06-06 | 52 | 38 | zamknięta | TP | 57.6 |
| GBPUSD | long | 2007-04-17 | 2007-07-03 | 77 | 55 | zamknięta | TP | 111.8 |
| EURUSD | long | 2007-04-25 | 2007-06-12 | 48 | 34 | zamknięta | SL | -317.9 |
| EURGBP | long | 2007-05-20 | 2007-07-24 | 65 | 47 | zamknięta | SL | -151.3 |
| EURGBP | short | 2007-07-24 | 2007-09-12 | 50 | 35 | zamknięta | SL | -137.5 |
| USDJPY | short | 2007-08-19 | 2007-11-08 | 80 | 57 | zamknięta | TP | 149.1 |
| EURJPY | short | 2007-08-29 | 2007-11-23 | 85 | 60 | zamknięta | czas | -278.1 |
| AUDUSD | long | 2007-11-14 | 2008-02-12 | 90 | 60 | zamknięta | czas | 42.2 |
| USDCAD | short | 2007-12-27 | 2008-03-22 | 86 | 60 | zamknięta | czas | -457.0 |
| EURJPY | short | 2008-01-21 | 2008-04-15 | 86 | 60 | zamknięta | czas | -756.1 |
| EURGBP | long | 2008-03-18 | 2008-06-11 | 86 | 60 | zamknięta | czas | 36.3 |
| USDJPY | short | 2008-04-10 | 2008-07-07 | 88 | 60 | zamknięta | czas | -752.4 |
| USDCAD | long | 2008-04-14 | 2008-06-10 | 57 | 40 | zamknięta | TP | 104.4 |
| EURUSD | long | 2008-04-22 | 2008-07-17 | 86 | 60 | zamknięta | czas | -128.9 |
| GBPUSD | short | 2008-05-07 | 2008-07-31 | 85 | 60 | zamknięta | czas | -297.7 |
| AUDUSD | long | 2008-05-20 | 2008-07-11 | 52 | 37 | zamknięta | TP | 103.5 |
| EURGBP | long | 2008-07-10 | 2008-08-28 | 49 | 35 | zamknięta | TP | 53.8 |
| AUDUSD | short | 2008-10-27 | 2009-01-21 | 86 | 60 | zamknięta | czas | -282.7 |
| EURJPY | short | 2008-10-28 | 2009-01-23 | 87 | 60 | zamknięta | czas | 32.0 |
| USDCAD | long | 2008-11-21 | 2009-02-17 | 88 | 60 | zamknięta | czas | -530.0 |
| EURUSD | short | 2008-12-09 | 2009-03-06 | 87 | 60 | zamknięta | czas | 365.2 |
| USDJPY | short | 2008-12-18 | 2009-03-14 | 86 | 60 | zamknięta | czas | -1 077.4 |
| EURGBP | long | 2009-01-23 | 2009-04-16 | 84 | 60 | zamknięta | czas | -538.7 |
| EURJPY | short | 2009-01-26 | 2009-03-19 | 52 | 38 | zamknięta | SL | -1 496.5 |
| GBPUSD | short | 2009-01-26 | 2009-04-17 | 82 | 60 | zamknięta | czas | -1 184.6 |
| AUDUSD | short | 2009-02-03 | 2009-04-02 | 59 | 43 | zamknięta | SL | -801.8 |
| USDCAD | long | 2009-03-03 | 2009-04-30 | 59 | 43 | zamknięta | SL | -982.9 |
| USDCHF | long | 2009-03-30 | 2009-06-22 | 84 | 60 | zamknięta | czas | -650.9 |
| EURJPY | long | 2009-04-06 | 2009-06-03 | 58 | 42 | zamknięta | TP | 261.4 |
| USDJPY | long | 2009-04-06 | 2009-06-29 | 84 | 60 | zamknięta | czas | -472.0 |
| EURGBP | long | 2009-04-22 | 2009-06-22 | 61 | 43 | zamknięta | SL | -558.2 |
| USDCAD | short | 2009-05-31 | 2009-07-31 | 61 | 45 | zamknięta | TP | 165.5 |
| EURUSD | long | 2009-06-02 | 2009-09-01 | 91 | 60 | zamknięta | czas | -34.2 |
| EURJPY | long | 2009-06-07 | 2009-09-07 | 92 | 60 | zamknięta | czas | -389.3 |
| AUDUSD | long | 2009-06-11 | 2009-08-03 | 53 | 35 | zamknięta | TP | 163.6 |
| EURGBP | short | 2009-06-22 | 2009-09-17 | 87 | 57 | zamknięta | SL | -484.7 |
| USDCHF | short | 2009-06-23 | 2009-09-07 | 76 | 47 | zamknięta | TP | 148.1 |
| USDJPY | short | 2009-07-08 | 2009-09-11 | 65 | 46 | zamknięta | TP | 117.2 |
| USDCAD | short | 2009-08-02 | 2009-10-07 | 66 | 46 | zamknięta | TP | 108.1 |
| GBPUSD | long | 2009-08-03 | 2009-09-23 | 51 | 30 | zamknięta | SL | -838.9 |
| EURGBP | long | 2009-10-27 | 2010-01-16 | 81 | 57 | zamknięta | SL | -297.6 |
| USDCAD | short | 2009-11-11 | 2009-12-30 | 49 | 34 | zamknięta | TP | 118.6 |
| EURJPY | short | 2009-11-27 | 2010-01-28 | 62 | 42 | zamknięta | TP | 169.7 |
| USDJPY | short | 2009-12-09 | 2010-03-05 | 86 | 60 | zamknięta | czas | -80.3 |
| USDCAD | short | 2010-01-07 | 2010-03-13 | 65 | 47 | zamknięta | TP | 107.8 |
| USDCHF | long | 2010-02-19 | 2010-05-04 | 75 | 53 | zamknięta | TP | 106.2 |
| AUDUSD | short | 2010-02-26 | 2010-05-17 | 81 | 57 | zamknięta | TP | 118.0 |
| EURJPY | short | 2010-02-26 | 2010-05-06 | 70 | 50 | zamknięta | TP | 175.1 |
| GBPUSD | short | 2010-03-02 | 2010-05-06 | 66 | 48 | zamknięta | TP | 168.2 |
| USDCAD | short | 2010-05-10 | 2010-08-03 | 85 | 60 | zamknięta | czas | 5.0 |
| USDJPY | long | 2010-05-10 | 2010-07-16 | 67 | 49 | zamknięta | SL | -659.2 |
| GBPUSD | short | 2010-05-19 | 2010-07-26 | 68 | 47 | zamknięta | SL | -1 058.4 |
| AUDUSD | short | 2010-05-20 | 2010-07-22 | 63 | 44 | zamknięta | SL | -756.4 |
| EURJPY | short | 2010-06-07 | 2010-08-24 | 78 | 54 | zamknięta | TP | 265.7 |
| EURGBP | short | 2010-06-28 | 2010-09-22 | 86 | 60 | zamknięta | SL | -433.4 |
| USDCHF | long | 2010-06-28 | 2010-08-25 | 58 | 40 | zamknięta | SL | -619.7 |
| GBPUSD | long | 2010-08-02 | 2010-10-14 | 73 | 51 | zamknięta | TP | 157.9 |
| USDCAD | short | 2010-08-05 | 2010-10-13 | 69 | 49 | zamknięta | TP | 108.6 |
| USDCAD | short | 2010-10-13 | 2011-01-01 | 79 | 55 | zamknięta | TP | 94.3 |
| USDCHF | short | 2010-10-14 | 2010-12-02 | 48 | 34 | zamknięta | SL | -525.5 |
| AUDUSD | long | 2010-11-05 | 2011-02-03 | 90 | 60 | zamknięta | czas | -41.8 |
| EURGBP | long | 2010-11-22 | 2011-01-27 | 66 | 47 | zamknięta | TP | 76.8 |
| EURUSD | long | 2010-11-24 | 2011-01-22 | 59 | 38 | zamknięta | TP | 163.8 |
| USDCHF | short | 2010-12-31 | 2011-02-25 | 56 | 38 | zamknięta | TP | 98.5 |
| USDJPY | short | 2011-01-03 | 2011-03-17 | 73 | 49 | zamknięta | TP | 60.5 |
| AUDUSD | long | 2011-02-03 | 2011-03-25 | 50 | 34 | zamknięta | TP | 101.4 |
| GBPUSD | long | 2011-02-03 | 2011-03-23 | 48 | 34 | zamknięta | TP | 156.6 |
| USDJPY | long | 2011-04-17 | 2011-07-13 | 87 | 59 | zamknięta | SL | -405.8 |
| USDCAD | short | 2011-04-27 | 2011-06-16 | 50 | 35 | zamknięta | SL | -354.4 |
| GBPUSD | long | 2011-04-28 | 2011-06-23 | 56 | 39 | zamknięta | SL | -604.7 |
| AUDUSD | long | 2011-05-01 | 2011-06-27 | 57 | 40 | zamknięta | SL | -534.1 |
| EURJPY | long | 2011-05-19 | 2011-08-01 | 74 | 49 | zamknięta | SL | -789.0 |
| GBPUSD | short | 2011-07-19 | 2011-09-06 | 49 | 35 | zamknięta | TP | 127.3 |
| EURUSD | long | 2011-07-21 | 2011-09-09 | 50 | 36 | zamknięta | SL | -800.5 |
| EURGBP | long | 2011-07-26 | 2011-10-18 | 84 | 60 | zamknięta | czas | -89.1 |
| USDJPY | short | 2011-08-10 | 2011-10-25 | 76 | 54 | zamknięta | TP | 81.5 |
| GBPUSD | long | 2011-09-06 | 2011-10-28 | 52 | 36 | zamknięta | TP | 138.8 |
| USDCHF | short | 2011-09-08 | 2011-12-03 | 85 | 60 | zamknięta | czas | -456.9 |
| USDJPY | short | 2011-11-21 | 2012-01-31 | 71 | 48 | zamknięta | TP | 49.6 |
| AUDUSD | short | 2011-11-24 | 2012-01-24 | 61 | 41 | zamknięta | SL | -801.3 |
| USDCAD | long | 2011-11-28 | 2012-02-21 | 85 | 60 | zamknięta | czas | -465.9 |
| USDCHF | long | 2011-12-15 | 2012-02-25 | 72 | 49 | zamknięta | SL | -530.6 |
| EURGBP | short | 2012-01-06 | 2012-03-30 | 85 | 60 | zamknięta | czas | -91.5 |
| EURUSD | short | 2012-01-30 | 2012-04-23 | 85 | 60 | zamknięta | czas | 52.9 |
| GBPUSD | short | 2012-01-30 | 2012-04-20 | 82 | 60 | zamknięta | czas | -409.9 |
| AUDUSD | long | 2012-02-08 | 2012-04-04 | 57 | 40 | zamknięta | SL | -514.3 |
| USDCAD | short | 2012-03-01 | 2012-04-26 | 57 | 41 | zamknięta | TP | 59.1 |
| USDCHF | short | 2012-03-02 | 2012-05-16 | 76 | 51 | zamknięta | SL | -397.8 |
| EURGBP | short | 2012-05-14 | 2012-07-09 | 56 | 39 | zamknięta | TP | 44.1 |
| USDCAD | short | 2012-05-17 | 2012-07-05 | 49 | 35 | zamknięta | TP | 68.7 |
| EURJPY | short | 2012-06-03 | 2012-07-23 | 50 | 32 | zamknięta | TP | 111.6 |
| GBPUSD | short | 2012-06-03 | 2012-08-22 | 80 | 58 | zamknięta | SL | -502.6 |
| USDJPY | short | 2012-06-03 | 2012-08-30 | 88 | 60 | zamknięta | czas | -48.0 |
| EURGBP | short | 2012-07-23 | 2012-09-14 | 53 | 39 | zamknięta | SL | -235.6 |
| EURJPY | short | 2012-07-23 | 2012-09-14 | 53 | 38 | zamknięta | SL | -614.4 |
| AUDUSD | long | 2012-08-05 | 2012-10-31 | 86 | 60 | zamknięta | czas | -198.1 |
| EURUSD | short | 2012-09-09 | 2012-11-10 | 61 | 45 | zamknięta | TP | 96.2 |
| USDCHF | long | 2012-09-09 | 2012-12-01 | 82 | 60 | zamknięta | czas | -181.0 |
| GBPUSD | long | 2012-09-16 | 2012-12-08 | 82 | 60 | zamknięta | czas | -191.4 |
| EURGBP | short | 2012-09-25 | 2012-12-20 | 85 | 60 | zamknięta | czas | -165.7 |
| AUDUSD | short | 2012-10-31 | 2013-01-29 | 90 | 60 | zamknięta | czas | -62.2 |
| USDCAD | long | 2012-11-28 | 2013-01-24 | 57 | 38 | zamknięta | TP | 43.6 |
| EURJPY | long | 2013-02-04 | 2013-04-08 | 64 | 46 | zamknięta | TP | 176.5 |
| EURUSD | long | 2013-02-26 | 2013-04-16 | 50 | 35 | zamknięta | TP | 106.4 |
| USDCAD | long | 2013-03-07 | 2013-05-07 | 62 | 44 | zamknięta | SL | -277.1 |
| EURGBP | long | 2013-03-08 | 2013-05-31 | 85 | 60 | zamknięta | czas | -179.2 |
| EURJPY | long | 2013-05-12 | 2013-08-08 | 88 | 60 | zamknięta | czas | -274.7 |
| USDCAD | long | 2013-07-02 | 2013-09-27 | 87 | 60 | zamknięta | czas | -237.9 |
| USDJPY | long | 2013-07-02 | 2013-10-01 | 91 | 60 | zamknięta | czas | -283.9 |
| EURUSD | short | 2013-07-14 | 2013-10-03 | 81 | 59 | zamknięta | SL | -574.6 |
| AUDUSD | short | 2013-08-01 | 2013-10-17 | 77 | 49 | zamknięta | SL | -663.3 |
| EURGBP | long | 2013-08-28 | 2013-11-08 | 71 | 51 | zamknięta | SL | -258.1 |
| EURJPY | long | 2013-09-19 | 2013-11-22 | 63 | 39 | zamknięta | TP | 107.0 |
| GBPUSD | long | 2013-10-01 | 2013-11-28 | 57 | 39 | zamknięta | TP | 91.0 |
| USDCHF | short | 2013-10-23 | 2013-12-11 | 48 | 32 | zamknięta | TP | 63.4 |
| USDCHF | short | 2013-12-11 | 2014-03-01 | 80 | 56 | zamknięta | TP | 56.0 |
| EURUSD | long | 2013-12-30 | 2014-03-07 | 67 | 47 | zamknięta | TP | 73.1 |
| EURGBP | short | 2014-01-23 | 2014-04-16 | 84 | 60 | zamknięta | czas | -49.9 |
| USDCAD | long | 2014-01-30 | 2014-03-21 | 50 | 36 | zamknięta | TP | 71.9 |
| GBPUSD | long | 2014-02-17 | 2014-04-30 | 73 | 53 | zamknięta | TP | 94.9 |
| EURJPY | long | 2014-03-07 | 2014-05-30 | 85 | 60 | zamknięta | czas | -402.5 |
| USDCHF | short | 2014-03-14 | 2014-06-05 | 84 | 60 | zamknięta | SL | -263.8 |
| EURUSD | long | 2014-03-18 | 2014-06-05 | 80 | 58 | zamknięta | SL | -361.5 |
| USDJPY | long | 2014-04-02 | 2014-07-01 | 90 | 60 | zamknięta | czas | -229.1 |
| AUDUSD | long | 2014-04-10 | 2014-07-01 | 82 | 57 | zamknięta | TP | 64.6 |
| USDCAD | long | 2014-04-22 | 2014-06-20 | 59 | 43 | zamknięta | SL | -267.7 |
| AUDUSD | long | 2014-07-01 | 2014-09-09 | 70 | 50 | zamknięta | SL | -260.9 |
| EURGBP | short | 2014-07-23 | 2014-09-10 | 49 | 35 | zamknięta | SL | -159.2 |
| EURGBP | short | 2014-11-03 | 2015-01-01 | 59 | 40 | zamknięta | TP | 41.7 |
| USDJPY | long | 2014-12-24 | 2015-03-11 | 77 | 49 | zamknięta | TP | 124.4 |
| EURJPY | long | 2015-01-21 | 2015-03-11 | 49 | 33 | zamknięta | SL | -710.6 |
| GBPUSD | short | 2015-01-23 | 2015-03-17 | 53 | 35 | zamknięta | TP | 112.1 |
| USDCHF | short | 2015-01-27 | 2015-04-20 | 84 | 60 | zamknięta | czas | -542.9 |
| USDJPY | long | 2015-03-11 | 2015-05-27 | 78 | 49 | zamknięta | TP | 84.1 |
| EURUSD | short | 2015-03-12 | 2015-04-29 | 49 | 33 | zamknięta | SL | -555.0 |
| EURJPY | short | 2015-04-30 | 2015-07-27 | 88 | 60 | zamknięta | czas | -276.4 |
| USDCHF | short | 2015-05-06 | 2015-08-04 | 90 | 59 | zamknięta | SL | -591.2 |
| EURGBP | short | 2015-05-25 | 2015-07-15 | 51 | 35 | zamknięta | TP | 67.9 |
| EURUSD | short | 2015-05-27 | 2015-08-24 | 89 | 58 | zamknięta | SL | -623.2 |
| USDJPY | long | 2015-06-08 | 2015-08-24 | 77 | 52 | zamknięta | SL | -476.5 |
| GBPUSD | long | 2015-06-18 | 2015-09-07 | 81 | 56 | zamknięta | SL | -700.2 |
| EURUSD | short | 2015-08-30 | 2015-10-23 | 54 | 39 | zamknięta | TP | 136.0 |
| USDJPY | long | 2015-08-30 | 2015-11-07 | 68 | 48 | zamknięta | TP | 113.0 |
| USDCHF | long | 2015-09-03 | 2015-10-28 | 54 | 36 | zamknięta | TP | 103.0 |
| AUDUSD | short | 2015-09-06 | 2015-12-01 | 85 | 60 | zamknięta | czas | -298.7 |
| EURJPY | long | 2015-09-10 | 2015-11-26 | 76 | 51 | zamknięta | SL | -614.3 |
| USDCAD | long | 2015-09-24 | 2015-12-08 | 74 | 52 | zamknięta | TP | 102.6 |
| GBPUSD | short | 2015-09-30 | 2015-12-01 | 61 | 41 | zamknięta | TP | 106.5 |
| EURUSD | long | 2015-10-26 | 2016-01-27 | 93 | 60 | zamknięta | czas | -157.3 |
| USDJPY | long | 2015-11-17 | 2016-01-05 | 49 | 32 | zamknięta | SL | -367.2 |
| EURUSD | long | 2016-02-11 | 2016-03-31 | 50 | 36 | zamknięta | TP | 104.7 |
| GBPUSD | short | 2016-02-25 | 2016-04-29 | 65 | 46 | zamknięta | SL | -709.5 |
| USDCHF | long | 2016-03-11 | 2016-05-27 | 78 | 56 | zamknięta | TP | 92.4 |
| EURUSD | long | 2016-05-03 | 2016-06-24 | 52 | 38 | zamknięta | SL | -448.7 |
| USDCAD | short | 2016-06-08 | 2016-09-01 | 85 | 60 | zamknięta | czas | -408.9 |
| AUDUSD | short | 2016-06-16 | 2016-09-13 | 89 | 60 | zamknięta | czas | -76.8 |
| EURJPY | short | 2016-06-26 | 2016-09-19 | 85 | 60 | zamknięta | czas | -109.3 |
| GBPUSD | short | 2016-07-06 | 2016-09-29 | 85 | 60 | zamknięta | czas | -49.4 |
| EURUSD | short | 2016-08-07 | 2016-10-12 | 66 | 46 | zamknięta | TP | 74.8 |
| EURGBP | long | 2016-08-15 | 2016-10-04 | 50 | 35 | zamknięta | TP | 86.3 |
| USDJPY | short | 2016-08-16 | 2016-11-11 | 86 | 59 | zamknięta | SL | -577.0 |
| USDCHF | short | 2016-09-06 | 2016-11-10 | 64 | 46 | zamknięta | TP | 69.0 |
| EURJPY | short | 2016-09-21 | 2016-11-17 | 56 | 40 | zamknięta | SL | -511.4 |
| USDCAD | long | 2016-11-15 | 2017-01-13 | 59 | 43 | zamknięta | SL | -461.5 |
| EURGBP | long | 2016-11-18 | 2017-01-10 | 53 | 35 | zamknięta | TP | 85.9 |
| EURJPY | long | 2016-12-16 | 2017-03-18 | 92 | 60 | zamknięta | czas | -220.0 |
| EURUSD | short | 2016-12-16 | 2017-03-16 | 90 | 60 | zamknięta | czas | -321.1 |
| USDJPY | long | 2016-12-16 | 2017-02-07 | 53 | 33 | zamknięta | SL | -640.2 |
| AUDUSD | short | 2017-01-19 | 2017-04-13 | 85 | 60 | zamknięta | czas | -57.4 |
| EURGBP | long | 2017-01-20 | 2017-03-14 | 53 | 36 | zamknięta | TP | 79.6 |
| AUDUSD | long | 2017-04-13 | 2017-06-14 | 62 | 44 | zamknięta | TP | 47.7 |
| EURGBP | short | 2017-05-22 | 2017-07-12 | 51 | 35 | zamknięta | SL | -283.1 |
| EURJPY | long | 2017-07-11 | 2017-08-30 | 50 | 35 | zamknięta | TP | 95.6 |
| EURUSD | long | 2017-09-07 | 2017-10-27 | 50 | 34 | zamknięta | SL | -430.7 |
| EURGBP | long | 2017-09-12 | 2017-12-07 | 85 | 60 | zamknięta | czas | -194.7 |
| EURJPY | long | 2017-09-24 | 2017-12-28 | 94 | 60 | zamknięta | czas | 62.2 |
| USDCAD | short | 2017-10-22 | 2017-12-30 | 68 | 47 | zamknięta | TP | 80.0 |
| USDJPY | long | 2017-10-22 | 2018-01-18 | 87 | 55 | zamknięta | SL | -372.3 |
| AUDUSD | long | 2017-10-25 | 2017-12-28 | 63 | 42 | zamknięta | TP | 54.1 |
| USDCHF | long | 2017-10-26 | 2018-01-16 | 81 | 52 | zamknięta | SL | -342.0 |
| EURGBP | short | 2017-12-08 | 2018-03-06 | 88 | 60 | zamknięta | czas | -180.4 |
| GBPUSD | long | 2018-02-02 | 2018-04-27 | 85 | 60 | zamknięta | czas | -498.7 |
| AUDUSD | long | 2018-02-15 | 2018-04-26 | 71 | 47 | zamknięta | SL | -362.7 |
| EURJPY | long | 2018-02-15 | 2018-05-14 | 89 | 60 | zamknięta | czas | -198.4 |
| USDCHF | short | 2018-02-16 | 2018-04-05 | 49 | 35 | zamknięta | SL | -397.3 |
| EURUSD | long | 2018-02-19 | 2018-05-07 | 78 | 55 | zamknięta | SL | -501.5 |
| EURGBP | short | 2018-04-12 | 2018-06-29 | 78 | 56 | zamknięta | SL | -220.9 |
| USDJPY | short | 2018-04-23 | 2018-07-13 | 81 | 53 | zamknięta | SL | -392.1 |
| USDCHF | long | 2018-05-06 | 2018-07-13 | 68 | 49 | zamknięta | TP | 52.5 |
| EURUSD | short | 2018-05-29 | 2018-08-10 | 73 | 50 | zamknięta | TP | 83.5 |
| USDCAD | long | 2018-06-20 | 2018-09-14 | 86 | 60 | zamknięta | czas | -264.9 |
| USDJPY | long | 2018-07-18 | 2018-09-28 | 72 | 48 | zamknięta | TP | 62.6 |
| USDCHF | short | 2018-10-11 | 2018-12-28 | 77 | 53 | zamknięta | TP | 51.7 |
| EURUSD | short | 2018-11-13 | 2019-02-08 | 87 | 60 | zamknięta | czas | -116.7 |
| EURJPY | short | 2019-01-03 | 2019-03-01 | 57 | 38 | zamknięta | SL | -519.5 |
| USDJPY | short | 2019-01-03 | 2019-03-01 | 57 | 38 | zamknięta | SL | -383.9 |
| USDCHF | short | 2019-01-18 | 2019-04-15 | 88 | 60 | zamknięta | czas | -100.1 |
| GBPUSD | long | 2019-02-27 | 2019-05-17 | 80 | 55 | zamknięta | SL | -486.3 |
| EURGBP | short | 2019-02-28 | 2019-05-22 | 84 | 56 | zamknięta | SL | -290.4 |
| AUDUSD | short | 2019-03-07 | 2019-05-03 | 58 | 41 | zamknięta | TP | 54.0 |
| USDCAD | long | 2019-03-07 | 2019-05-29 | 84 | 56 | zamknięta | TP | 76.0 |
| EURUSD | short | 2019-03-08 | 2019-04-25 | 49 | 35 | zamknięta | TP | 57.1 |
| EURUSD | short | 2019-04-25 | 2019-06-21 | 57 | 40 | zamknięta | SL | -240.9 |
| EURGBP | short | 2019-05-22 | 2019-07-17 | 56 | 40 | zamknięta | SL | -242.8 |
| EURJPY | short | 2019-06-02 | 2019-07-25 | 53 | 36 | zamknięta | TP | 63.8 |
| USDCHF | short | 2019-06-25 | 2019-08-12 | 48 | 34 | zamknięta | TP | 60.6 |
| EURUSD | long | 2019-07-01 | 2019-09-02 | 63 | 44 | zamknięta | SL | -297.0 |
| USDJPY | short | 2019-08-05 | 2019-10-15 | 71 | 47 | zamknięta | SL | -315.2 |
| USDCHF | short | 2019-08-12 | 2019-10-01 | 50 | 32 | zamknięta | SL | -301.4 |
| EURUSD | short | 2019-10-01 | 2019-12-27 | 86 | 60 | zamknięta | czas | -166.7 |
| USDCHF | long | 2019-10-02 | 2019-12-31 | 89 | 60 | zamknięta | czas | -283.2 |
| GBPUSD | short | 2019-10-13 | 2019-12-10 | 57 | 39 | zamknięta | SL | -566.1 |
| EURJPY | long | 2019-12-13 | 2020-02-14 | 63 | 43 | zamknięta | SL | -300.9 |
| GBPUSD | long | 2020-01-02 | 2020-03-13 | 71 | 51 | zamknięta | SL | -533.9 |
| USDJPY | short | 2020-03-17 | 2020-06-12 | 88 | 60 | zamknięta | czas | -106.2 |
| USDCAD | long | 2020-03-20 | 2020-05-27 | 69 | 47 | zamknięta | SL | -759.7 |
| EURUSD | long | 2020-03-27 | 2020-06-02 | 68 | 45 | zamknięta | TP | 138.6 |
| EURGBP | long | 2020-03-30 | 2020-06-19 | 81 | 55 | zamknięta | TP | 146.4 |
| USDCHF | short | 2020-03-30 | 2020-06-09 | 71 | 48 | zamknięta | TP | 112.0 |
| GBPUSD | short | 2020-05-18 | 2020-07-28 | 71 | 48 | zamknięta | SL | -687.7 |
| USDCAD | long | 2020-05-27 | 2020-08-18 | 83 | 57 | zamknięta | SL | -583.2 |
| EURUSD | short | 2020-06-02 | 2020-07-22 | 50 | 33 | zamknięta | SL | -393.9 |
| EURGBP | long | 2020-06-29 | 2020-09-10 | 73 | 52 | zamknięta | TP | 65.7 |
| USDJPY | short | 2020-07-30 | 2020-09-21 | 53 | 35 | zamknięta | TP | 59.4 |
| EURUSD | long | 2020-08-18 | 2020-11-13 | 86 | 60 | zamknięta | czas | -142.9 |
| USDCHF | short | 2020-08-18 | 2020-11-12 | 85 | 60 | zamknięta | czas | -140.8 |
| EURJPY | long | 2020-09-01 | 2020-12-01 | 90 | 60 | zamknięta | czas | -170.6 |
| USDCAD | short | 2020-09-01 | 2020-11-10 | 69 | 46 | zamknięta | TP | 75.5 |
| EURGBP | long | 2020-09-10 | 2020-11-12 | 62 | 44 | zamknięta | SL | -350.2 |
| EURGBP | long | 2020-12-22 | 2021-02-17 | 57 | 38 | zamknięta | SL | -398.1 |
| AUDUSD | long | 2021-03-19 | 2021-05-07 | 50 | 35 | zamknięta | TP | 77.4 |
| EURGBP | short | 2021-04-01 | 2021-06-28 | 88 | 60 | zamknięta | czas | -83.2 |
| EURUSD | short | 2021-04-20 | 2021-06-17 | 58 | 42 | zamknięta | TP | 58.5 |
| USDCHF | long | 2021-04-26 | 2021-06-18 | 53 | 38 | zamknięta | TP | 50.6 |
| EURUSD | long | 2021-06-17 | 2021-09-09 | 84 | 60 | zamknięta | czas | -90.6 |
| GBPUSD | long | 2021-06-21 | 2021-09-15 | 86 | 60 | zamknięta | czas | -77.7 |
| AUDUSD | long | 2021-06-23 | 2021-08-18 | 56 | 39 | zamknięta | SL | -330.8 |
| EURJPY | long | 2021-06-23 | 2021-08-17 | 55 | 37 | zamknięta | SL | -385.9 |
| USDCHF | long | 2021-07-20 | 2021-09-16 | 58 | 41 | zamknięta | TP | 51.3 |
| USDJPY | long | 2021-08-08 | 2021-09-27 | 50 | 34 | zamknięta | TP | 54.2 |
| EURGBP | short | 2021-08-10 | 2021-09-29 | 50 | 36 | zamknięta | SL | -184.5 |
| EURJPY | short | 2021-08-17 | 2021-10-11 | 55 | 38 | zamknięta | SL | -292.1 |
| GBPUSD | short | 2021-09-29 | 2021-11-25 | 56 | 37 | zamknięta | TP | 86.0 |
| USDCHF | long | 2021-09-29 | 2021-12-24 | 85 | 60 | zamknięta | czas | -157.7 |
| EURJPY | long | 2021-11-15 | 2022-01-05 | 51 | 37 | zamknięta | TP | 73.3 |
| USDJPY | long | 2021-11-17 | 2022-01-05 | 49 | 34 | zamknięta | TP | 59.5 |
| EURGBP | short | 2021-11-18 | 2022-01-05 | 48 | 34 | zamknięta | TP | 42.2 |
| EURUSD | short | 2021-11-26 | 2022-01-28 | 63 | 43 | zamknięta | TP | 61.3 |
| USDJPY | long | 2022-01-05 | 2022-03-12 | 66 | 47 | zamknięta | TP | 52.8 |
| USDCHF | short | 2022-01-13 | 2022-04-06 | 84 | 60 | zamknięta | czas | -190.9 |
| AUDUSD | long | 2022-05-04 | 2022-07-01 | 58 | 39 | zamknięta | SL | -456.6 |
| EURUSD | short | 2022-05-12 | 2022-07-05 | 54 | 38 | zamknięta | TP | 91.5 |
| EURJPY | long | 2022-06-08 | 2022-07-28 | 50 | 34 | zamknięta | SL | -719.3 |
| AUDUSD | short | 2022-07-11 | 2022-09-21 | 72 | 52 | zamknięta | TP | 85.2 |
| USDCAD | long | 2022-07-14 | 2022-09-15 | 63 | 44 | zamknięta | TP | 101.0 |
| EURJPY | short | 2022-08-29 | 2022-10-17 | 49 | 34 | zamknięta | SL | -711.3 |
| EURGBP | long | 2022-09-28 | 2022-12-24 | 86 | 60 | zamknięta | czas | -169.5 |
| AUDUSD | short | 2022-10-10 | 2023-01-03 | 84 | 60 | zamknięta | czas | -512.5 |
| USDCAD | long | 2022-10-16 | 2023-01-11 | 86 | 60 | zamknięta | czas | -424.1 |
| EURJPY | long | 2022-10-25 | 2022-12-21 | 56 | 37 | zamknięta | SL | -792.4 |
| EURUSD | short | 2022-11-11 | 2023-01-13 | 63 | 44 | zamknięta | SL | -602.1 |
| GBPUSD | short | 2022-11-14 | 2023-02-04 | 82 | 60 | zamknięta | czas | -248.6 |
| USDCHF | long | 2022-11-22 | 2023-02-16 | 86 | 60 | zamknięta | czas | -352.6 |
| EURJPY | long | 2022-12-29 | 2023-02-22 | 55 | 37 | zamknięta | TP | 156.6 |
| USDJPY | short | 2023-01-17 | 2023-03-08 | 50 | 34 | zamknięta | SL | -885.9 |
| EURGBP | long | 2023-02-03 | 2023-04-28 | 85 | 60 | zamknięta | czas | -154.5 |
| USDJPY | short | 2023-03-26 | 2023-05-23 | 58 | 42 | zamknięta | SL | -794.3 |
| EURUSD | long | 2023-04-13 | 2023-07-07 | 85 | 60 | zamknięta | czas | -85.8 |
| USDCHF | short | 2023-04-13 | 2023-07-07 | 85 | 60 | zamknięta | czas | -0.9 |
| EURGBP | short | 2023-07-11 | 2023-10-03 | 84 | 60 | zamknięta | czas | -156.9 |
| USDCHF | short | 2023-07-13 | 2023-09-06 | 55 | 37 | zamknięta | SL | -340.1 |
| AUDUSD | long | 2023-08-02 | 2023-10-26 | 85 | 60 | zamknięta | czas | -210.7 |
| GBPUSD | long | 2023-08-03 | 2023-09-25 | 53 | 36 | zamknięta | SL | -498.9 |
| USDCAD | short | 2023-08-08 | 2023-10-27 | 80 | 57 | zamknięta | SL | -418.7 |
| EURJPY | long | 2023-08-10 | 2023-11-01 | 82 | 57 | zamknięta | TP | 142.0 |
| EURUSD | short | 2023-09-27 | 2023-11-15 | 48 | 34 | zamknięta | SL | -317.3 |
| GBPUSD | short | 2023-11-17 | 2024-02-15 | 90 | 60 | zamknięta | czas | -154.0 |
| EURJPY | short | 2024-01-08 | 2024-04-08 | 92 | 60 | zamknięta | czas | -660.3 |
| USDCAD | short | 2024-02-05 | 2024-04-16 | 72 | 52 | zamknięta | SL | -344.3 |
| USDCHF | short | 2024-02-09 | 2024-03-28 | 48 | 34 | zamknięta | SL | -311.4 |
| EURGBP | short | 2024-02-14 | 2024-05-07 | 84 | 60 | zamknięta | czas | -96.8 |
| USDCAD | long | 2024-04-16 | 2024-07-10 | 85 | 60 | zamknięta | czas | -203.6 |
| USDJPY | long | 2024-04-30 | 2024-06-20 | 51 | 37 | zamknięta | TP | 115.9 |
| GBPUSD | short | 2024-05-09 | 2024-07-11 | 63 | 43 | zamknięta | SL | -358.2 |
| AUDUSD | long | 2024-05-15 | 2024-07-08 | 54 | 37 | zamknięta | TP | 50.2 |
| EURJPY | long | 2024-07-31 | 2024-10-24 | 85 | 57 | zamknięta | TP | 174.0 |
| EURGBP | long | 2024-08-25 | 2024-11-12 | 78 | 56 | zamknięta | SL | -194.0 |
| USDCHF | short | 2024-09-08 | 2024-11-07 | 59 | 43 | zamknięta | SL | -320.1 |
| USDJPY | short | 2024-10-09 | 2025-01-08 | 90 | 55 | zamknięta | SL | -913.6 |
| USDCHF | long | 2025-01-13 | 2025-03-06 | 52 | 37 | zamknięta | SL | -297.2 |
| EURUSD | short | 2025-01-14 | 2025-03-06 | 51 | 36 | zamknięta | SL | -389.2 |
| GBPUSD | short | 2025-01-14 | 2025-03-05 | 50 | 36 | zamknięta | SL | -524.1 |
| AUDUSD | short | 2025-02-04 | 2025-04-04 | 60 | 43 | zamknięta | TP | 53.4 |
| USDCAD | long | 2025-02-04 | 2025-04-11 | 67 | 49 | zamknięta | SL | -550.4 |
| EURJPY | short | 2025-03-03 | 2025-05-12 | 71 | 48 | zamknięta | SL | -778.4 |
| EURGBP | long | 2025-04-13 | 2025-07-09 | 87 | 60 | zamknięta | czas | -42.8 |
| AUDUSD | short | 2025-04-16 | 2025-07-16 | 91 | 60 | zamknięta | czas | -160.8 |
| USDCHF | short | 2025-04-22 | 2025-06-12 | 51 | 35 | zamknięta | TP | 114.3 |
| USDJPY | short | 2025-04-22 | 2025-07-22 | 91 | 60 | zamknięta | czas | -402.9 |
| USDCAD | short | 2025-06-15 | 2025-08-22 | 68 | 50 | zamknięta | SL | -330.3 |
| EURUSD | long | 2025-06-30 | 2025-09-17 | 79 | 57 | zamknięta | TP | 82.6 |
| USDCHF | short | 2025-06-30 | 2025-09-16 | 78 | 55 | zamknięta | TP | 61.6 |
| USDJPY | short | 2025-07-22 | 2025-10-20 | 90 | 60 | zamknięta | czas | -397.2 |
| AUDUSD | long | 2025-07-24 | 2025-09-11 | 49 | 35 | zamknięta | TP | 49.2 |
| EURGBP | long | 2025-07-27 | 2025-10-17 | 82 | 60 | zamknięta | czas | -71.3 |
| EURJPY | long | 2025-07-27 | 2025-09-25 | 60 | 40 | zamknięta | TP | 105.4 |
| GBPUSD | long | 2025-08-13 | 2025-10-31 | 78 | 53 | zamknięta | SL | -429.9 |
| AUDUSD | long | 2025-09-11 | 2025-11-22 | 71 | 49 | zamknięta | SL | -240.5 |
| USDCHF | short | 2025-09-16 | 2025-12-13 | 87 | 60 | zamknięta | czas | -96.9 |
| EURUSD | long | 2025-09-17 | 2025-11-05 | 48 | 32 | zamknięta | SL | -351.8 |
| EURGBP | long | 2025-11-17 | 2026-01-07 | 51 | 34 | zamknięta | SL | -174.0 |
| USDJPY | long | 2025-11-20 | 2026-01-13 | 54 | 32 | zamknięta | TP | 105.6 |
| USDCHF | short | 2026-01-28 | 2026-03-28 | 59 | 43 | zamknięta | SL | -331.1 |
| USDCAD | short | 2026-01-30 | 2026-03-26 | 55 | 38 | zamknięta | SL | -315.7 |
| AUDUSD | long | 2026-02-12 | 2026-04-16 | 64 | 44 | zamknięta | TP | 63.1 |
| EURGBP | long | 2026-03-02 | 2026-05-22 | 82 | 60 | zamknięta | czas | -134.0 |
| USDCHF | long | 2026-04-02 | 2026-06-18 | 77 | 55 | zamknięta | TP | 58.3 |
| AUDUSD | long | 2026-05-06 | 2026-06-24 | 49 | 31 | zamknięta | SL | -319.1 |
| GBPUSD | long | 2026-05-25 | 2026-08-18 | 85 | 60 | zamknięta | czas | 37.0 |
| EURUSD | short | 2026-06-23 | 2026-08-19 | 57 | 40 | zamknięta | SL | -294.5 |
| AUDUSD | short | 2026-07-05 | 2026-08-26 | 52 | 34 | zamknięta | SL | -245.5 |
| EURGBP | short | 2026-07-15 | 2026-09-25 | 72 | 51 | zamknięta | SL | -139.1 |
| USDJPY | short | 2026-09-07 | 2026-11-12 | 65 | 45 | zamknięta | SL | -600.6 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 4084); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -0.63 pips/transakcję, percentyl **33.2** (losowe: 5%=-5.12, mediana=1.18, 95%=6.69).

- **Deflated Sharpe Ratio**: 0.056 (Sharpe na transakcję 0.021, próg przy 72 próbach 0.052).

- **PBO** (CSCV, 16 bloków, 72 wariantów): 0.430 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 3028 transakcji, śr. -4.91 pips, -0.01 R.

- **Bootstrap 95%** średnich pipsów: całość [-7.50; 6.16], OOS [-23.49; -0.98].

- **Spread**: ×1 -0.63, ×1,5 -1.45, ×2 -2.27 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.05% transakcji.

- **Noce (swap pominięty, O5)**: średnio 16.5 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -8.88, 1 pips: -17.14 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"   # świece dzienne: sygnał codziennie na zamknięciu dnia, wejście na open następnego

HYPOTHESIS = """Mały TP i ogromny SL: cena często dochodzi do bliskiego celu w kierunku długiego trendu, a daleki stop
rzadko pada. Kierunek z długiej EMA: tryb „trend” — EMA rośnie → long, spada → short; tryb „hamowanie” — spadek EMA
zwalnia → long, wzrost EMA zwalnia → short (wejście przed zawróceniem). Wysoki win rate jest tu pewny — pytanie, czy rzadkie
duże straty na SL go nie zjadają."""

# mode: "trend" = kierunek EMA; "hamowanie" = zmiana tempa EMA (spadek hamuje → long, wzrost hamuje → short)
PARAMS = {"mode": ["trend", "hamowanie"], "ema": [100, 200], "k": [5, 20]}   # k = ile dni wstecz mierzymy nachylenie

# mały TP, ogromny SL (w ATR14 dziennym), limit 60 dni (B7); jedna pozycja na parę — nowe wejście następnego dnia po wyjściu
EXITS = [{"kind": "atr", "n": 14, "tp": tp, "sl": sl, "cap": 60} for tp in (0.3, 0.5, 1.0) for sl in (3.0, 5.0, 10.0)]


def signals(df, p, ind):
    e = ind.ema(df.close, p["ema"])
    slope = e - e.shift(p["k"])                      # nachylenie EMA z k dni
    if p["mode"] == "trend":
        long_, short = slope > 0, slope < 0
    else:
        prev = slope.shift(p["k"])                   # nachylenie k dni wcześniej
        long_ = (slope < 0) & (slope > prev)         # spada, ale wolniej — spadek hamuje
        short = (slope > 0) & (slope < prev)         # rośnie, ale wolniej — wzrost hamuje
    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?

## Eksploracja Maca (D-072)

Mac sprawdził 1,004 odmian (22 rodzajów). 1 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_silny+cofniecie20, adx_silny+trend200, adx_silny+zmiennosc_wysoka, adx_slaby, cofniecie20, cofniecie20+trend200, cofniecie20+zmiennosc_wysoka, odwrocony, oryginal, potwierdzenie, przeciw200, siatka, trail, trend200, trend50, tylko_long, tylko_short, wybicie20, zmiennosc_niska, zmiennosc_wysoka, zmiennosc_wysoka+trend200. Prób (wariantów) łącznie: 1,004. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): ATR14 TP 1× SL 5× max 60, {'mode': 'trend', 'ema': 100, 'k': 20} — IS 2808 trans., śr. R +0.009, ocena +0.013; OOS 1276 trans., śr. R -0.030.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | tylko przy silnym trendzie (ADX14 > 25) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 715 | +0.112 | 285 | -0.002 | -6.38 | +0.636 | 98 | akcje nie potwierdzają | nie przetrwała OOS |
| 2 | tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) + tylko przy podwyższonej zmienności (ATR14 > ATR100) {'mode': 'trend', 'ema': 100, 'k': 5} | ATR14 TP 0.3× SL 10× max 60 | 1568 | +0.068 | 710 | -0.003 | -5.03 | +0.286 | 100 | akcje nie potwierdzają | nie przetrwała OOS |
| 3 | tylko przy silnym trendzie (ADX14 > 25) {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1413 | +0.051 | 594 | -0.006 | -3.78 | +0.084 | 92 | akcje nie potwierdzają | nie przetrwała OOS |
| 4 | tylko przy silnym trendzie (ADX14 > 25) + tylko z trendem SMA200 {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1377 | +0.044 | 576 | -0.011 | -8.57 | +0.036 | 82 | akcje nie potwierdzają | nie przetrwała OOS |
| 5 | tylko przy podwyższonej zmienności (ATR14 > ATR100) + tylko z trendem SMA200 {'mode': 'trend', 'ema': 200, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1092 | +0.041 | 524 | +0.004 | +2.44 | +0.059 | 94 | akcje nie potwierdzają | dodatnia w OOS, ale nie przechodzi wszystkich testów |

### OOS na akcjach (pilotaż, poza werdyktem)

| wersja | spółki | transakcje | śr. % netto | śr. R | long % | short % | percentyl losowych | spółki na plusie | werdykt |
|---|---|---|---|---|---|---|---|---|---|
| oryginał | 14/14 | 5216 | -0.354 | -0.031 | +0.180 | -1.793 | 0 | 2/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) | 14/14 | 1238 | +0.032 | -0.006 | +0.466 | -0.914 | 49 | 7/14 | akcje nie potwierdzają |
| tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) + tylko przy podwyższonej zmienności (ATR14 > ATR100) | 14/14 | 3424 | -0.128 | -0.008 | +0.034 | -0.503 | 50 | 3/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) | 14/14 | 2632 | -0.232 | -0.008 | +0.455 | -2.275 | 0 | 5/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) + tylko z trendem SMA200 | 14/14 | 2565 | -0.153 | -0.005 | +0.471 | -2.033 | 0 | 5/14 | akcje nie potwierdzają |
| tylko przy podwyższonej zmienności (ATR14 > ATR100) + tylko z trendem SMA200 | 14/14 | 2662 | +0.116 | +0.006 | +0.638 | -2.039 | 1 | 8/14 | akcje nie potwierdzają |

