# Raport strategii: RSI D1

Run `20261112-165248` · silnik 0.13.0 · kod `f2d04115aa37ffe9` · dane `c9068b7a34535dbe`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -12.04 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✔ | 0.14 |
| DSR ≥ 0,95 | ✔ | 1.00 |
| dodatni przy spreadzie ×1,5 | ✔ | 9.91 |

## Hipoteza

Na świecach dziennych par FX trend trwa miesiącami, a krótkie wyprzedanie w trendzie wzrostowym (i wykupienie
w spadkowym) zwykle się cofa w ciągu kilku dni. Kupujemy, gdy RSI spada pod próg, ale tylko gdy cena jest nad rosnącą SMA200
(sprzedajemy lustrzanie pod opadającą SMA200). Bez filtra trendu czysty powrót RSI na D1 po spreadzie nie zarabia — to
sprawdziło poszukiwanie (research/rsi_d1/README.md). Wersje różnią się progiem RSI, wyjściem (po X dniach na zamknięciu,
TP/SL w ATR, stop pod dołkiem) i stawką: stała, rosnąca z kolejną świecą wyprzedania, z liczbą otwartych pozycji, z głębokością RSI.
Konfiguracje wybrane wyłącznie na IS (przed 2019-05); wynik OOS badania jest w raporcie poszukiwania.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-11; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 3 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 1%, 2%, 3%, 5%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 36** (12 wejścia × 3 wyjść).

- Pominięte sygnały, średnio na wariant: 460 (limit otwartych pozycji w parze), 2.7 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 2.3 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, max 10 | cfg=11 | 650 | 0.41 | 18.51 | 35.1 | 222 | -0.14 | -12.04 |
| 2 | poziomy TP/SL ze strategii, max 5 | cfg=11 | 657 | 0.38 | 15.72 | 37.4 | 227 | -0.02 | 3.86 |
| 3 | poziomy TP/SL ze strategii, max 10 | cfg=5 | 1 224 | 0.24 | 26.60 | 55.4 | 543 | 0.11 | 1.83 |
| 4 | poziomy TP/SL ze strategii, max 10 | cfg=1 | 1 302 | 0.23 | 26.06 | 55.7 | 593 | 0.11 | 2.73 |
| 5 | poziomy TP/SL ze strategii, max 10 | cfg=6 | 1 302 | 0.23 | 26.06 | 55.7 | 593 | 0.11 | 2.73 |
| 6 | poziomy TP/SL ze strategii, max 10 | cfg=7 | 1 302 | 0.23 | 26.06 | 55.7 | 593 | 0.11 | 2.73 |
| 7 | poziomy TP/SL ze strategii, max 10 | cfg=8 | 1 302 | 0.23 | 26.06 | 55.7 | 593 | 0.11 | 2.73 |
| 8 | poziomy TP/SL ze strategii, max 10 | cfg=0 | 1 813 | 0.20 | 24.52 | 54.3 | 809 | 0.02 | -2.17 |
| 9 | poziomy TP/SL ze strategii, max 10 | cfg=4 | 1 587 | 0.19 | 20.54 | 44.2 | 656 | 0.06 | 1.58 |
| 10 | poziomy TP/SL ze strategii, max 3 | cfg=11 | 679 | 0.18 | 10.76 | 41.2 | 233 | -0.08 | 2.87 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, max 10 (cfg=11)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 83 | 22.0 | 1 828.6 | 44.6 |
| EURGBP | 96 | 7.1 | 677.0 | 37.5 |
| EURJPY | 117 | 36.3 | 4 249.6 | 44.4 |
| EURUSD | 106 | 23.3 | 2 474.2 | 35.8 |
| GBPUSD | 96 | 5.5 | 526.1 | 27.1 |
| USDCAD | 99 | -6.6 | -648.8 | 32.3 |
| USDCHF | 102 | -3.6 | -371.4 | 28.4 |
| USDJPY | 173 | 3.6 | 621.3 | 30.6 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 1998 | 8 | -41.5 | -332.2 | 12.5 |
| 1999 | 7 | 56.6 | 396.2 | 28.6 |
| 2000 | 12 | -18.2 | -218.4 | 8.3 |
| 2001 | 4 | -85.2 | -340.9 | 0.0 |
| 2002 | 23 | 29.7 | 682.6 | 17.4 |
| 2003 | 8 | -9.2 | -73.4 | 25.0 |
| 2004 | 20 | -7.6 | -152.7 | 20.0 |
| 2005 | 49 | 82.4 | 4 036.2 | 36.7 |
| 2006 | 25 | 29.8 | 744.4 | 36.0 |
| 2007 | 25 | 70.8 | 1 771.0 | 40.0 |
| 2008 | 18 | -64.6 | -1 162.6 | 33.3 |
| 2009 | 75 | 56.1 | 4 206.9 | 38.7 |
| 2010 | 60 | 13.9 | 835.9 | 30.0 |
| 2011 | 17 | 36.2 | 615.9 | 58.8 |
| 2012 | 34 | 9.4 | 319.4 | 47.1 |
| 2013 | 32 | 25.5 | 815.4 | 40.6 |
| 2014 | 51 | 2.2 | 114.6 | 27.5 |
| 2015 | 58 | -13.4 | -779.9 | 34.5 |
| 2016 | 45 | 3.7 | 165.5 | 31.1 |
| 2017 | 39 | 10.6 | 413.1 | 56.4 |
| 2018 | 35 | -13.7 | -478.7 | 31.4 |
| 2019 | 29 | 9.3 | 271.1 | 34.5 |
| 2020 | 22 | 32.3 | 711.0 | 50.0 |
| 2021 | 33 | -3.1 | -101.3 | 42.4 |
| 2022 | 27 | -10.4 | -280.6 | 44.4 |
| 2023 | 40 | -35.0 | -1 401.9 | 20.0 |
| 2024 | 32 | -38.6 | -1 235.3 | 18.8 |
| 2025 | 17 | -0.9 | -15.9 | 35.3 |
| 2026 | 27 | -6.2 | -168.7 | 44.4 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 650 | 18.5 | 12 030.1 | 35.1 |
| OOS | 222 | -12.0 | -2 673.5 | 33.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 12 702 | 27.0 | 0.8 | -8.2 | -8.5 | 0.28 | 0 |
| 2.0% | 15 740 | 57.4 | 1.6 | -15.8 | -16.3 | 0.28 | 0 |
| 3.0% | 19 037 | 90.4 | 2.3 | -22.9 | -23.6 | 0.28 | 0 |
| 5.0% | 25 938 | 159.4 | 3.4 | -35.7 | -36.7 | 0.27 | 0 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-09-30): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **872**, otwarte: **0** (razem 872).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 872 | 1 | 2 | 4 | 12 | 19 | 10.7 | 9 357 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 872 | 1 | 2 | 4 | 12 | 19 | 10.7 | 9 357 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDJPY | long | 1998-01-28 | 1998-02-05 | 8 | 6 | zamknięta | SL | -94.4 |
| USDJPY | long | 1998-01-29 | 1998-01-31 | 2 | 2 | zamknięta | TP | 260.6 |
| USDJPY | long | 1998-02-06 | 1998-02-13 | 7 | 5 | zamknięta | SL | -80.4 |
| USDJPY | long | 1998-02-11 | 1998-02-13 | 2 | 2 | zamknięta | SL | -53.4 |
| USDJPY | long | 1998-09-01 | 1998-09-03 | 2 | 2 | zamknięta | SL | -246.4 |
| USDJPY | short | 1999-02-23 | 1999-03-05 | 10 | 8 | zamknięta | SL | -150.4 |
| USDJPY | short | 1999-02-24 | 1999-03-05 | 9 | 7 | zamknięta | SL | -175.4 |
| USDJPY | short | 1999-02-25 | 1999-03-05 | 8 | 6 | zamknięta | SL | -118.4 |
| USDJPY | short | 1999-03-05 | 1999-03-16 | 11 | 7 | zamknięta | TP | 496.6 |
| USDJPY | short | 1999-03-08 | 1999-03-12 | 4 | 4 | zamknięta | TP | 398.6 |
| USDJPY | short | 2000-01-14 | 2000-01-18 | 4 | 2 | zamknięta | TP | 178.6 |
| USDJPY | short | 2000-02-03 | 2000-02-09 | 6 | 4 | zamknięta | SL | -100.4 |
| USDJPY | short | 2000-02-09 | 2000-02-12 | 3 | 3 | zamknięta | SL | -29.4 |
| USDJPY | short | 2000-02-16 | 2000-02-18 | 2 | 2 | zamknięta | SL | -71.4 |
| USDJPY | long | 2001-08-15 | 2001-08-29 | 14 | 10 | zamknięta | SL | -82.4 |
| USDJPY | long | 2001-08-16 | 2001-08-29 | 13 | 9 | zamknięta | SL | -118.4 |
| USDJPY | long | 2001-08-19 | 2001-08-29 | 10 | 8 | zamknięta | SL | -128.4 |
| USDJPY | long | 2002-03-08 | 2002-03-22 | 14 | 10 | zamknięta | czas | 442.6 |
| USDJPY | long | 2002-03-11 | 2002-03-23 | 12 | 10 | zamknięta | czas | 466.6 |
| USDJPY | long | 2002-03-12 | 2002-03-23 | 11 | 9 | zamknięta | TP | 450.6 |
| USDJPY | long | 2002-04-29 | 2002-05-01 | 2 | 2 | zamknięta | SL | -52.4 |
| USDJPY | long | 2002-05-05 | 2002-05-07 | 2 | 2 | zamknięta | SL | -20.4 |
| EURGBP | long | 2002-07-31 | 2002-08-07 | 7 | 5 | zamknięta | SL | -11.7 |
| EURGBP | long | 2002-09-15 | 2002-09-27 | 12 | 10 | zamknięta | czas | 13.3 |
| USDJPY | short | 2002-09-17 | 2002-09-20 | 3 | 3 | zamknięta | SL | -144.4 |
| USDJPY | short | 2002-09-23 | 2002-10-07 | 14 | 10 | zamknięta | SL | -31.4 |
| USDJPY | short | 2002-09-24 | 2002-10-07 | 13 | 9 | zamknięta | SL | -83.4 |
| EURGBP | long | 2003-06-26 | 2003-07-03 | 7 | 5 | zamknięta | SL | -28.7 |
| EURGBP | long | 2003-08-24 | 2003-08-28 | 4 | 4 | zamknięta | SL | -21.7 |
| EURGBP | long | 2003-08-25 | 2003-08-28 | 3 | 3 | zamknięta | SL | -21.7 |
| EURJPY | short | 2003-12-03 | 2003-12-11 | 8 | 6 | zamknięta | SL | -88.1 |
| USDJPY | short | 2004-02-24 | 2004-02-27 | 3 | 3 | zamknięta | SL | -109.4 |
| USDJPY | short | 2004-02-25 | 2004-02-27 | 2 | 2 | zamknięta | SL | -117.4 |
| USDJPY | short | 2004-02-27 | 2004-03-03 | 5 | 3 | zamknięta | SL | -27.4 |
| USDJPY | short | 2004-03-01 | 2004-03-03 | 2 | 2 | zamknięta | SL | -72.4 |
| USDJPY | short | 2004-03-09 | 2004-03-17 | 8 | 6 | zamknięta | TP | 244.6 |
| USDJPY | short | 2004-03-10 | 2004-03-16 | 6 | 4 | zamknięta | TP | 146.6 |
| USDJPY | short | 2004-03-11 | 2004-03-16 | 5 | 3 | zamknięta | TP | 86.6 |
| USDCAD | short | 2004-12-15 | 2004-12-23 | 8 | 6 | zamknięta | SL | -28.0 |
| EURGBP | long | 2004-12-20 | 2004-12-22 | 2 | 2 | zamknięta | TP | 78.3 |
| USDCHF | short | 2005-01-10 | 2005-01-19 | 9 | 7 | zamknięta | SL | -49.9 |
| EURUSD | long | 2005-01-21 | 2005-02-04 | 14 | 10 | zamknięta | czas | 9.2 |
| USDCAD | short | 2005-02-08 | 2005-02-15 | 7 | 5 | zamknięta | TP | 240.0 |
| USDCHF | short | 2005-02-08 | 2005-02-17 | 9 | 7 | zamknięta | TP | 377.1 |
| EURUSD | long | 2005-02-09 | 2005-02-23 | 14 | 10 | zamknięta | TP | 325.1 |
| USDCHF | short | 2005-02-09 | 2005-02-17 | 8 | 6 | zamknięta | TP | 347.1 |
| EURUSD | long | 2005-02-10 | 2005-02-16 | 6 | 4 | zamknięta | TP | 227.1 |
| USDCHF | short | 2005-02-10 | 2005-02-16 | 6 | 4 | zamknięta | TP | 235.1 |
| GBPUSD | long | 2005-03-24 | 2005-03-28 | 5 | 3 | zamknięta | SL | -45.5 |
| GBPUSD | long | 2005-03-25 | 2005-03-28 | 4 | 2 | zamknięta | SL | -18.6 |
| EURUSD | long | 2005-03-28 | 2005-04-04 | 7 | 5 | zamknięta | SL | -34.9 |
| GBPUSD | long | 2005-03-28 | 2005-04-11 | 14 | 10 | zamknięta | czas | 236.3 |
| USDCAD | short | 2005-04-18 | 2005-04-27 | 9 | 7 | zamknięta | SL | -23.0 |
| EURGBP | short | 2005-07-11 | 2005-07-13 | 2 | 2 | zamknięta | SL | -33.7 |
| EURGBP | short | 2005-07-14 | 2005-07-18 | 4 | 2 | zamknięta | SL | -35.7 |
| EURUSD | short | 2005-08-14 | 2005-08-16 | 2 | 2 | zamknięta | TP | 133.2 |
| GBPUSD | short | 2005-08-14 | 2005-08-26 | 12 | 10 | zamknięta | czas | 147.6 |
| USDCHF | long | 2005-08-14 | 2005-08-18 | 4 | 4 | zamknięta | TP | 212.1 |
| GBPUSD | short | 2005-08-15 | 2005-08-29 | 14 | 10 | zamknięta | czas | 129.5 |
| EURUSD | short | 2005-09-04 | 2005-09-16 | 12 | 10 | zamknięta | czas | 299.1 |
| EURUSD | short | 2005-09-05 | 2005-09-19 | 14 | 10 | zamknięta | TP | 350.1 |
| GBPUSD | short | 2005-09-05 | 2005-09-19 | 14 | 10 | zamknięta | czas | 398.5 |
| USDCHF | long | 2005-09-05 | 2005-09-19 | 14 | 10 | zamknięta | TP | 408.1 |
| GBPUSD | short | 2005-09-06 | 2005-09-20 | 14 | 10 | zamknięta | czas | 431.7 |
| GBPUSD | short | 2005-09-07 | 2005-09-19 | 12 | 8 | zamknięta | TP | 357.5 |
| USDJPY | long | 2005-12-20 | 2006-01-04 | 15 | 10 | zamknięta | czas | -9.4 |
| EURJPY | long | 2005-12-27 | 2006-01-05 | 9 | 7 | zamknięta | TP | 196.9 |
| EURUSD | short | 2006-01-05 | 2006-01-07 | 2 | 2 | zamknięta | SL | -28.8 |
| USDCHF | long | 2006-01-05 | 2006-01-07 | 2 | 2 | zamknięta | SL | -35.9 |
| EURUSD | short | 2006-01-09 | 2006-01-21 | 12 | 10 | zamknięta | czas | 3.1 |
| USDCHF | long | 2006-01-09 | 2006-01-21 | 12 | 10 | zamknięta | czas | 57.1 |
| USDJPY | long | 2006-01-10 | 2006-01-13 | 3 | 3 | zamknięta | SL | -78.4 |
| USDJPY | long | 2006-01-11 | 2006-01-13 | 2 | 2 | zamknięta | SL | -70.4 |
| EURJPY | long | 2006-02-28 | 2006-03-11 | 11 | 9 | zamknięta | TP | 395.4 |
| USDCAD | short | 2006-03-27 | 2006-03-29 | 2 | 2 | zamknięta | SL | -45.0 |
| USDJPY | short | 2006-06-13 | 2006-06-19 | 6 | 4 | zamknięta | SL | -18.4 |
| USDCAD | short | 2006-07-24 | 2006-07-31 | 7 | 5 | zamknięta | TP | 148.0 |
| USDCHF | short | 2006-09-17 | 2006-09-22 | 5 | 5 | zamknięta | TP | 172.1 |
| EURUSD | long | 2006-10-11 | 2006-10-13 | 2 | 2 | zamknięta | SL | -20.0 |
| EURUSD | long | 2006-10-15 | 2006-10-19 | 4 | 4 | zamknięta | TP | 108.1 |
| EURJPY | long | 2007-03-06 | 2007-03-20 | 14 | 10 | zamknięta | czas | 528.9 |
| GBPUSD | long | 2007-03-06 | 2007-03-20 | 14 | 10 | zamknięta | czas | 256.4 |
| EURUSD | long | 2007-06-13 | 2007-06-27 | 14 | 10 | zamknięta | czas | 144.0 |
| EURUSD | long | 2007-06-14 | 2007-06-19 | 5 | 3 | zamknięta | TP | 115.1 |
| EURUSD | long | 2007-08-16 | 2007-08-31 | 15 | 10 | zamknięta | TP | 283.2 |
| GBPUSD | long | 2007-08-19 | 2007-08-31 | 12 | 10 | zamknięta | czas | 383.3 |
| GBPUSD | long | 2007-08-21 | 2007-08-23 | 2 | 2 | zamknięta | TP | 164.6 |
| USDCAD | short | 2007-12-06 | 2007-12-14 | 8 | 6 | zamknięta | SL | -98.0 |
| EURUSD | long | 2007-12-21 | 2008-01-01 | 11 | 6 | zamknięta | TP | 399.1 |
| USDCHF | short | 2007-12-21 | 2007-12-29 | 8 | 5 | zamknięta | TP | 278.1 |
| USDCHF | short | 2007-12-26 | 2007-12-28 | 2 | 2 | zamknięta | TP | 106.1 |
| USDCAD | short | 2008-01-18 | 2008-01-23 | 5 | 2 | zamknięta | SL | -62.1 |
| USDCAD | short | 2008-01-23 | 2008-01-25 | 2 | 2 | zamknięta | TP | 148.0 |
| USDJPY | short | 2008-04-08 | 2008-04-10 | 2 | 2 | zamknięta | TP | 133.6 |
| USDCHF | short | 2008-05-04 | 2008-05-08 | 4 | 4 | zamknięta | SL | -50.9 |
| USDCHF | short | 2008-05-05 | 2008-05-08 | 3 | 3 | zamknięta | SL | -71.9 |
| USDCHF | long | 2008-12-22 | 2008-12-30 | 8 | 5 | zamknięta | SL | -600.9 |
| USDCHF | long | 2008-12-23 | 2008-12-30 | 7 | 4 | zamknięta | SL | -509.9 |
| USDCHF | long | 2008-12-24 | 2008-12-30 | 6 | 3 | zamknięta | SL | -450.9 |
| AUDUSD | short | 2009-01-07 | 2009-01-13 | 6 | 4 | zamknięta | TP | 341.9 |
| USDJPY | short | 2009-02-20 | 2009-02-24 | 4 | 2 | zamknięta | SL | -40.4 |
| USDJPY | short | 2009-02-27 | 2009-03-05 | 6 | 4 | zamknięta | SL | -41.9 |
| USDJPY | short | 2009-03-02 | 2009-03-05 | 3 | 3 | zamknięta | SL | -150.7 |
| USDJPY | short | 2009-03-03 | 2009-03-05 | 2 | 2 | zamknięta | SL | -164.7 |
| USDJPY | short | 2009-03-09 | 2009-03-13 | 4 | 4 | zamknięta | TP | 136.3 |
| USDJPY | short | 2009-03-10 | 2009-03-13 | 3 | 3 | zamknięta | TP | 234.8 |
| USDJPY | short | 2009-03-11 | 2009-03-13 | 2 | 2 | zamknięta | TP | 221.1 |
| USDJPY | short | 2009-03-18 | 2009-03-20 | 2 | 2 | zamknięta | TP | 308.6 |
| AUDUSD | short | 2009-03-20 | 2009-03-24 | 4 | 2 | zamknięta | SL | -60.0 |
| EURUSD | short | 2009-03-20 | 2009-04-02 | 14 | 10 | zamknięta | czas | 196.2 |
| EURUSD | short | 2009-03-23 | 2009-04-03 | 12 | 10 | zamknięta | czas | 138.3 |
| EURUSD | short | 2009-03-24 | 2009-04-06 | 14 | 10 | zamknięta | czas | 210.3 |
| AUDUSD | short | 2009-03-25 | 2009-04-02 | 9 | 7 | zamknięta | SL | -101.9 |
| EURJPY | short | 2009-03-25 | 2009-03-30 | 6 | 4 | zamknięta | TP | 444.9 |
| AUDUSD | short | 2009-03-26 | 2009-04-02 | 8 | 6 | zamknięta | SL | -103.4 |
| EURJPY | short | 2009-03-26 | 2009-03-30 | 5 | 3 | zamknięta | TP | 453.6 |
| AUDUSD | short | 2009-03-27 | 2009-03-30 | 4 | 2 | zamknięta | TP | 163.4 |
| EURJPY | short | 2009-03-27 | 2009-03-30 | 4 | 2 | zamknięta | TP | 441.9 |
| AUDUSD | short | 2009-04-05 | 2009-04-13 | 8 | 6 | zamknięta | SL | -58.7 |
| AUDUSD | short | 2009-04-06 | 2009-04-13 | 7 | 5 | zamknięta | SL | -111.8 |
| EURJPY | short | 2009-04-06 | 2009-04-20 | 14 | 10 | zamknięta | TP | 677.3 |
| AUDUSD | short | 2009-04-07 | 2009-04-13 | 6 | 4 | zamknięta | SL | -107.7 |
| AUDUSD | short | 2009-04-13 | 2009-04-20 | 7 | 5 | zamknięta | TP | 267.7 |
| AUDUSD | short | 2009-04-14 | 2009-04-20 | 6 | 4 | zamknięta | TP | 197.4 |
| AUDUSD | short | 2009-04-15 | 2009-04-20 | 5 | 3 | zamknięta | TP | 209.2 |
| EURGBP | long | 2009-04-15 | 2009-04-29 | 14 | 10 | zamknięta | czas | 164.3 |
| EURGBP | long | 2009-04-16 | 2009-04-24 | 8 | 6 | zamknięta | TP | 183.3 |
| EURGBP | long | 2009-04-19 | 2009-04-24 | 5 | 5 | zamknięta | TP | 204.3 |
| GBPUSD | short | 2009-05-10 | 2009-05-12 | 2 | 2 | zamknięta | SL | -49.3 |
| EURGBP | long | 2009-05-27 | 2009-06-01 | 5 | 3 | zamknięta | SL | -15.7 |
| EURJPY | long | 2009-07-08 | 2009-07-22 | 14 | 10 | zamknięta | czas | 411.4 |
| EURGBP | short | 2009-08-30 | 2009-09-14 | 15 | 10 | zamknięta | SL | -22.7 |
| EURGBP | short | 2009-08-31 | 2009-09-04 | 4 | 4 | zamknięta | TP | 91.3 |
| GBPUSD | long | 2009-09-28 | 2009-10-12 | 14 | 8 | zamknięta | SL | -164.9 |
| EURJPY | long | 2009-10-01 | 2009-10-15 | 14 | 9 | zamknięta | TP | 317.9 |
| USDCHF | short | 2009-12-18 | 2010-01-05 | 18 | 10 | zamknięta | czas | 172.1 |
| USDCHF | short | 2009-12-21 | 2009-12-30 | 9 | 6 | zamknięta | TP | 106.1 |
| USDCHF | short | 2009-12-22 | 2009-12-30 | 8 | 5 | zamknięta | TP | 138.1 |
| EURUSD | long | 2009-12-23 | 2010-01-08 | 16 | 10 | zamknięta | czas | 61.4 |
| GBPUSD | long | 2009-12-23 | 2009-12-30 | 7 | 4 | zamknięta | SL | -47.8 |
| EURUSD | long | 2009-12-24 | 2010-01-09 | 16 | 10 | zamknięta | czas | 73.3 |
| GBPUSD | long | 2009-12-24 | 2009-12-30 | 6 | 3 | zamknięta | SL | -41.7 |
| EURUSD | long | 2009-12-30 | 2010-01-06 | 7 | 4 | zamknięta | TP | 107.2 |
| USDJPY | short | 2010-01-08 | 2010-01-13 | 5 | 3 | zamknięta | TP | 214.2 |
| USDCHF | short | 2010-02-01 | 2010-02-05 | 4 | 4 | zamknięta | SL | -27.9 |
| USDCHF | short | 2010-02-02 | 2010-02-05 | 3 | 3 | zamknięta | SL | -64.9 |
| AUDUSD | long | 2010-02-08 | 2010-02-17 | 9 | 7 | zamknięta | TP | 266.6 |
| AUDUSD | long | 2010-02-09 | 2010-02-17 | 8 | 6 | zamknięta | TP | 289.8 |
| EURJPY | short | 2010-04-04 | 2010-04-08 | 4 | 4 | zamknięta | TP | 350.9 |
| EURJPY | short | 2010-04-05 | 2010-04-08 | 3 | 3 | zamknięta | TP | 307.9 |
| USDCHF | long | 2010-06-21 | 2010-06-24 | 3 | 3 | zamknięta | SL | -100.2 |
| GBPUSD | short | 2010-07-15 | 2010-07-26 | 11 | 7 | zamknięta | SL | -29.0 |
| EURUSD | short | 2010-07-20 | 2010-07-27 | 7 | 5 | zamknięta | SL | -134.4 |
| EURUSD | short | 2010-07-29 | 2010-08-02 | 4 | 2 | zamknięta | SL | -31.4 |
| EURUSD | short | 2010-08-03 | 2010-08-06 | 3 | 3 | zamknięta | SL | -36.0 |
| EURUSD | short | 2010-08-08 | 2010-08-11 | 3 | 3 | zamknięta | TP | 227.4 |
| EURGBP | short | 2010-09-22 | 2010-09-28 | 6 | 4 | zamknięta | SL | -18.7 |
| EURGBP | short | 2010-09-23 | 2010-09-28 | 5 | 3 | zamknięta | SL | -83.7 |
| USDJPY | short | 2010-11-30 | 2010-12-04 | 4 | 4 | zamknięta | TP | 142.7 |
| GBPUSD | long | 2010-12-01 | 2010-12-11 | 10 | 8 | zamknięta | TP | 265.6 |
| USDJPY | short | 2010-12-01 | 2010-12-04 | 3 | 3 | zamknięta | TP | 86.2 |
| GBPUSD | long | 2010-12-24 | 2010-12-29 | 5 | 3 | zamknięta | SL | -69.4 |
| AUDUSD | long | 2011-03-18 | 2011-03-23 | 5 | 3 | zamknięta | TP | 277.5 |
| EURJPY | long | 2011-05-16 | 2011-05-19 | 3 | 3 | zamknięta | TP | 243.8 |
| EURUSD | long | 2011-05-16 | 2011-05-23 | 7 | 5 | zamknięta | SL | -108.1 |
| EURUSD | long | 2011-07-13 | 2011-07-21 | 8 | 6 | zamknięta | TP | 143.9 |
| USDCHF | short | 2011-09-13 | 2011-09-21 | 8 | 6 | zamknięta | SL | -124.5 |
| USDCHF | short | 2011-09-14 | 2011-09-21 | 7 | 5 | zamknięta | SL | -164.9 |
| USDCHF | short | 2011-09-15 | 2011-09-21 | 6 | 4 | zamknięta | SL | -219.5 |
| USDJPY | short | 2011-11-02 | 2011-11-16 | 14 | 10 | zamknięta | czas | 118.7 |
| USDJPY | short | 2011-11-03 | 2011-11-17 | 14 | 10 | zamknięta | czas | 105.0 |
| GBPUSD | short | 2012-02-03 | 2012-02-08 | 5 | 3 | zamknięta | SL | -56.6 |
| GBPUSD | short | 2012-02-09 | 2012-02-15 | 6 | 4 | zamknięta | TP | 78.4 |
| EURJPY | short | 2012-02-13 | 2012-02-16 | 3 | 2 | zamknięta | SL | -33.8 |
| EURGBP | short | 2012-02-27 | 2012-03-03 | 5 | 5 | zamknięta | TP | 160.2 |
| EURJPY | short | 2012-02-28 | 2012-03-13 | 14 | 10 | zamknięta | czas | -21.1 |
| USDJPY | long | 2012-05-21 | 2012-05-30 | 9 | 7 | zamknięta | SL | -38.5 |
| USDJPY | long | 2012-06-03 | 2012-06-15 | 12 | 10 | zamknięta | czas | 134.5 |
| EURGBP | short | 2012-09-16 | 2012-09-24 | 8 | 6 | zamknięta | TP | 113.3 |
| EURGBP | short | 2012-09-17 | 2012-09-24 | 7 | 5 | zamknięta | TP | 100.3 |
| EURGBP | short | 2012-09-18 | 2012-09-24 | 6 | 4 | zamknięta | TP | 56.3 |
| EURGBP | short | 2012-10-09 | 2012-10-16 | 7 | 5 | zamknięta | SL | -64.7 |
| EURUSD | long | 2013-02-27 | 2013-03-02 | 3 | 3 | zamknięta | SL | -50.2 |
| USDCHF | short | 2013-03-04 | 2013-03-07 | 3 | 3 | zamknięta | SL | -41.3 |
| EURUSD | long | 2013-03-05 | 2013-03-09 | 4 | 4 | zamknięta | SL | -66.3 |
| USDCAD | long | 2013-05-01 | 2013-05-07 | 6 | 4 | zamknięta | SL | -26.0 |
| USDCAD | long | 2013-05-02 | 2013-05-07 | 5 | 3 | zamknięta | SL | -61.0 |
| GBPUSD | short | 2013-06-13 | 2013-06-17 | 4 | 2 | zamknięta | SL | -18.3 |
| USDJPY | long | 2013-06-13 | 2013-06-27 | 14 | 10 | zamknięta | czas | 224.2 |
| USDJPY | long | 2013-06-16 | 2013-06-28 | 12 | 10 | zamknięta | TP | 499.7 |
| USDJPY | long | 2013-06-17 | 2013-06-28 | 11 | 9 | zamknięta | TP | 426.9 |
| AUDUSD | short | 2013-09-19 | 2013-10-07 | 18 | 10 | zamknięta | czas | 1.0 |
| USDCAD | long | 2013-09-19 | 2013-10-02 | 13 | 9 | zamknięta | TP | 77.5 |
| AUDUSD | short | 2013-09-22 | 2013-09-30 | 8 | 5 | zamknięta | TP | 109.2 |
| AUDUSD | short | 2013-10-23 | 2013-10-30 | 6 | 4 | zamknięta | TP | 114.0 |
| AUDUSD | short | 2013-10-24 | 2013-10-29 | 4 | 2 | zamknięta | TP | 42.5 |
| EURUSD | long | 2013-11-12 | 2013-11-26 | 14 | 9 | zamknięta | TP | 137.3 |
| EURJPY | long | 2014-02-06 | 2014-02-20 | 14 | 10 | zamknięta | czas | 346.6 |
| USDJPY | long | 2014-02-06 | 2014-02-25 | 19 | 10 | zamknięta | czas | 103.7 |
| EURJPY | long | 2014-02-07 | 2014-02-12 | 5 | 3 | zamknięta | TP | 125.3 |
| USDCAD | long | 2014-04-10 | 2014-04-22 | 12 | 8 | zamknięta | TP | 103.0 |
| USDCAD | long | 2014-05-11 | 2014-05-23 | 12 | 10 | zamknięta | czas | -7.7 |
| USDCHF | short | 2014-05-19 | 2014-05-23 | 4 | 4 | zamknięta | SL | -40.9 |
| USDCHF | short | 2014-05-20 | 2014-05-23 | 3 | 3 | zamknięta | SL | -43.7 |
| EURJPY | long | 2014-05-21 | 2014-05-29 | 8 | 5 | zamknięta | SL | -67.3 |
| EURJPY | long | 2014-05-22 | 2014-05-29 | 7 | 4 | zamknięta | SL | -84.6 |
| USDCHF | short | 2014-05-28 | 2014-06-03 | 6 | 4 | zamknięta | SL | -10.1 |
| EURJPY | long | 2014-05-29 | 2014-06-03 | 5 | 3 | zamknięta | TP | 100.6 |
| GBPUSD | long | 2014-08-04 | 2014-08-08 | 4 | 4 | zamknięta | SL | -53.4 |
| GBPUSD | long | 2014-08-05 | 2014-08-08 | 3 | 3 | zamknięta | SL | -65.1 |
| GBPUSD | long | 2014-08-14 | 2014-08-19 | 5 | 3 | zamknięta | SL | -26.8 |
| EURGBP | short | 2014-10-16 | 2014-10-31 | 14 | 10 | zamknięta | czas | 61.1 |
| EURGBP | short | 2014-11-20 | 2014-12-04 | 14 | 10 | zamknięta | czas | 82.3 |
| EURGBP | short | 2014-11-21 | 2014-12-04 | 13 | 9 | zamknięta | TP | 109.7 |
| USDCAD | long | 2015-04-19 | 2015-04-27 | 8 | 6 | zamknięta | SL | -120.0 |
| USDCAD | long | 2015-04-20 | 2015-04-27 | 7 | 5 | zamknięta | SL | -138.0 |
| USDCAD | long | 2015-04-21 | 2015-04-27 | 6 | 4 | zamknięta | SL | -180.0 |
| AUDUSD | short | 2015-04-29 | 2015-05-13 | 14 | 10 | zamknięta | SL | -82.4 |
| USDCAD | long | 2015-04-29 | 2015-05-06 | 7 | 5 | zamknięta | SL | -65.6 |
| AUDUSD | short | 2015-04-30 | 2015-05-13 | 13 | 9 | zamknięta | SL | -178.4 |
| GBPUSD | short | 2015-04-30 | 2015-05-08 | 8 | 6 | zamknięta | SL | -140.0 |
| EURJPY | short | 2015-05-03 | 2015-05-06 | 3 | 3 | zamknięta | SL | -83.8 |
| EURUSD | short | 2015-05-03 | 2015-05-06 | 3 | 3 | zamknięta | SL | -99.7 |
| USDCAD | long | 2015-05-03 | 2015-05-06 | 3 | 3 | zamknięta | SL | -209.5 |
| EURJPY | short | 2015-05-07 | 2015-05-14 | 7 | 5 | zamknięta | SL | -136.3 |
| EURUSD | short | 2015-05-07 | 2015-05-14 | 7 | 5 | zamknięta | SL | -146.4 |
| USDCAD | long | 2015-05-07 | 2015-05-13 | 6 | 4 | zamknięta | SL | -165.6 |
| EURJPY | short | 2015-05-10 | 2015-05-14 | 4 | 4 | zamknięta | SL | -185.3 |
| AUDUSD | short | 2015-05-14 | 2015-05-22 | 8 | 6 | zamknięta | TP | 215.2 |
| USDCAD | long | 2015-05-14 | 2015-05-19 | 5 | 2 | zamknięta | TP | 158.3 |
| EURJPY | short | 2015-05-18 | 2015-05-22 | 4 | 4 | zamknięta | TP | 200.0 |
| GBPUSD | short | 2015-05-19 | 2015-05-27 | 8 | 5 | zamknięta | TP | 58.5 |
| EURUSD | short | 2015-08-24 | 2015-09-07 | 14 | 10 | zamknięta | czas | 429.5 |
| USDJPY | long | 2015-08-24 | 2015-09-08 | 15 | 10 | zamknięta | czas | 55.7 |
| EURGBP | short | 2015-08-25 | 2015-09-08 | 14 | 10 | zamknięta | czas | 51.5 |
| EURGBP | short | 2015-08-26 | 2015-09-09 | 14 | 10 | zamknięta | czas | 47.6 |
| EURGBP | short | 2015-08-27 | 2015-09-10 | 14 | 10 | zamknięta | czas | -9.7 |
| USDJPY | long | 2015-08-27 | 2015-09-10 | 14 | 10 | zamknięta | czas | -71.8 |
| AUDUSD | short | 2015-10-12 | 2015-10-28 | 15 | 10 | zamknięta | czas | 93.7 |
| USDCAD | long | 2015-10-12 | 2015-10-15 | 3 | 3 | zamknięta | SL | -111.0 |
| AUDUSD | short | 2015-10-13 | 2015-10-29 | 15 | 10 | zamknięta | TP | 72.2 |
| USDCAD | long | 2015-10-18 | 2015-10-21 | 3 | 3 | zamknięta | TP | 160.0 |
| EURJPY | short | 2016-02-03 | 2016-02-12 | 9 | 6 | zamknięta | TP | 257.6 |
| USDCHF | long | 2016-02-12 | 2016-02-23 | 11 | 7 | zamknięta | TP | 258.7 |
| USDCHF | long | 2016-02-15 | 2016-02-23 | 8 | 6 | zamknięta | TP | 189.0 |
| EURGBP | long | 2016-04-27 | 2016-05-03 | 6 | 4 | zamknięta | TP | 105.3 |
| AUDUSD | long | 2016-05-10 | 2016-05-13 | 3 | 3 | zamknięta | SL | -73.3 |
| AUDUSD | long | 2016-05-15 | 2016-05-18 | 3 | 3 | zamknięta | SL | -18.1 |
| EURGBP | long | 2016-05-19 | 2016-05-24 | 5 | 3 | zamknięta | SL | -24.8 |
| EURGBP | long | 2016-05-25 | 2016-06-01 | 7 | 5 | zamknięta | TP | 160.5 |
| EURGBP | long | 2016-05-26 | 2016-06-01 | 6 | 4 | zamknięta | TP | 119.9 |
| USDCAD | short | 2016-07-26 | 2016-07-29 | 3 | 3 | zamknięta | TP | 158.8 |
| USDJPY | short | 2016-10-31 | 2016-11-03 | 3 | 3 | zamknięta | TP | 83.3 |
| EURGBP | long | 2016-11-14 | 2016-11-19 | 5 | 5 | zamknięta | SL | -47.8 |
| EURGBP | long | 2016-11-15 | 2016-11-19 | 4 | 4 | zamknięta | SL | -28.0 |
| EURGBP | long | 2016-11-16 | 2016-11-19 | 3 | 3 | zamknięta | SL | -56.3 |
| EURGBP | long | 2016-11-25 | 2016-12-02 | 7 | 4 | zamknięta | SL | -21.0 |
| EURGBP | long | 2016-11-28 | 2016-12-02 | 4 | 3 | zamknięta | SL | -40.3 |
| EURGBP | long | 2016-12-02 | 2016-12-06 | 4 | 2 | zamknięta | SL | -126.2 |
| EURGBP | long | 2016-12-06 | 2016-12-20 | 14 | 10 | zamknięta | czas | -88.9 |
| USDCAD | long | 2017-01-13 | 2017-01-18 | 5 | 3 | zamknięta | SL | -121.6 |
| USDCHF | long | 2017-02-03 | 2017-02-11 | 8 | 6 | zamknięta | TP | 117.1 |
| EURJPY | long | 2017-02-28 | 2017-03-03 | 3 | 3 | zamknięta | TP | 98.1 |
| USDJPY | long | 2017-03-24 | 2017-03-27 | 4 | 2 | zamknięta | SL | -46.3 |
| USDJPY | long | 2017-03-27 | 2017-04-10 | 14 | 10 | zamknięta | czas | 46.4 |
| USDJPY | long | 2017-03-28 | 2017-03-31 | 3 | 3 | zamknięta | TP | 55.2 |
| USDCAD | long | 2017-05-25 | 2017-06-08 | 14 | 10 | zamknięta | czas | 24.5 |
| EURGBP | long | 2017-09-17 | 2017-09-25 | 8 | 6 | zamknięta | SL | -17.0 |
| EURGBP | long | 2017-09-18 | 2017-09-25 | 7 | 5 | zamknięta | SL | -74.1 |
| EURGBP | long | 2017-09-19 | 2017-09-25 | 6 | 4 | zamknięta | SL | -99.1 |
| EURGBP | long | 2017-09-27 | 2017-10-03 | 6 | 4 | zamknięta | TP | 102.0 |
| EURGBP | long | 2017-09-28 | 2017-10-03 | 5 | 3 | zamknięta | TP | 99.7 |
| AUDUSD | long | 2017-10-08 | 2017-10-13 | 5 | 5 | zamknięta | TP | 94.4 |
| AUDUSD | long | 2017-10-09 | 2017-10-13 | 4 | 4 | zamknięta | TP | 113.8 |
| AUDUSD | long | 2017-10-10 | 2017-10-13 | 3 | 3 | zamknięta | TP | 87.8 |
| USDCAD | short | 2017-10-30 | 2017-11-14 | 15 | 10 | zamknięta | czas | 133.2 |
| USDCAD | short | 2017-10-31 | 2017-11-15 | 15 | 10 | zamknięta | czas | 88.3 |
| USDCAD | short | 2017-11-01 | 2017-11-16 | 15 | 10 | zamknięta | czas | 154.8 |
| EURJPY | long | 2018-02-26 | 2018-03-01 | 3 | 3 | zamknięta | SL | -62.2 |
| GBPUSD | long | 2018-05-10 | 2018-05-15 | 5 | 3 | zamknięta | SL | -64.1 |
| USDJPY | short | 2018-05-10 | 2018-05-15 | 5 | 3 | zamknięta | SL | -53.7 |
| GBPUSD | long | 2018-05-15 | 2018-05-22 | 7 | 4 | zamknięta | SL | -73.1 |
| EURJPY | short | 2018-07-17 | 2018-07-25 | 8 | 5 | zamknięta | TP | 197.5 |
| EURJPY | short | 2018-07-18 | 2018-07-23 | 5 | 3 | zamknięta | TP | 143.7 |
| EURJPY | short | 2018-08-30 | 2018-09-04 | 5 | 3 | zamknięta | TP | 97.5 |
| GBPUSD | short | 2018-09-23 | 2018-09-28 | 5 | 5 | zamknięta | TP | 21.0 |
| USDJPY | long | 2018-12-26 | 2018-12-29 | 3 | 3 | zamknięta | SL | -17.8 |
| USDCAD | long | 2019-02-05 | 2019-02-09 | 4 | 3 | zamknięta | TP | 164.1 |
| USDCAD | long | 2019-02-06 | 2019-02-09 | 3 | 2 | zamknięta | TP | 154.1 |
| EURJPY | short | 2019-03-05 | 2019-03-08 | 3 | 3 | zamknięta | TP | 133.2 |
| EURUSD | short | 2019-06-10 | 2019-06-14 | 4 | 4 | zamknięta | TP | 93.6 |
| USDCAD | long | 2019-06-11 | 2019-06-18 | 7 | 5 | zamknięta | TP | 148.0 |
| USDCAD | short | 2019-08-07 | 2019-08-21 | 14 | 10 | zamknięta | czas | -4.2 |
| EURJPY | short | 2019-10-17 | 2019-10-21 | 4 | 2 | zamknięta | SL | -55.1 |
| EURJPY | short | 2019-10-21 | 2019-11-01 | 10 | 8 | zamknięta | SL | -36.9 |
| EURUSD | short | 2019-10-21 | 2019-11-05 | 14 | 10 | zamknięta | czas | -15.5 |
| EURJPY | short | 2019-10-22 | 2019-11-01 | 9 | 7 | zamknięta | SL | -75.7 |
| EURUSD | short | 2019-10-22 | 2019-11-06 | 14 | 10 | zamknięta | czas | 0.2 |
| EURJPY | short | 2019-10-23 | 2019-11-01 | 8 | 6 | zamknięta | SL | -57.0 |
| EURJPY | short | 2019-11-01 | 2019-11-08 | 7 | 5 | zamknięta | TP | 15.9 |
| AUDUSD | short | 2019-11-05 | 2019-11-15 | 10 | 8 | zamknięta | TP | 73.8 |
| EURGBP | short | 2020-03-05 | 2020-03-10 | 5 | 3 | zamknięta | SL | -92.7 |
| AUDUSD | short | 2020-04-30 | 2020-05-15 | 15 | 10 | zamknięta | czas | 23.0 |
| EURGBP | long | 2020-09-03 | 2020-09-07 | 4 | 2 | zamknięta | TP | 45.1 |
| EURJPY | long | 2020-09-23 | 2020-09-28 | 5 | 3 | zamknięta | SL | -32.7 |
| EURJPY | long | 2020-09-24 | 2020-09-28 | 4 | 2 | zamknięta | SL | -56.7 |
| AUDUSD | long | 2020-09-27 | 2020-10-09 | 12 | 10 | zamknięta | czas | 133.1 |
| AUDUSD | long | 2020-09-28 | 2020-10-09 | 11 | 9 | zamknięta | TP | 139.1 |
| USDCHF | short | 2020-09-28 | 2020-10-06 | 8 | 6 | zamknięta | TP | 97.3 |
| EURJPY | long | 2020-11-02 | 2020-11-10 | 8 | 6 | zamknięta | TP | 239.6 |
| EURJPY | long | 2020-11-03 | 2020-11-10 | 7 | 5 | zamknięta | TP | 230.8 |
| EURJPY | long | 2020-11-04 | 2020-11-10 | 6 | 4 | zamknięta | TP | 102.6 |
| EURUSD | long | 2021-02-08 | 2021-02-11 | 3 | 3 | zamknięta | TP | 85.8 |
| USDCHF | short | 2021-02-08 | 2021-02-11 | 3 | 3 | zamknięta | TP | 82.3 |
| USDCHF | short | 2021-02-26 | 2021-03-02 | 4 | 2 | zamknięta | SL | -42.0 |
| EURUSD | long | 2021-03-10 | 2021-03-24 | 14 | 10 | zamknięta | czas | 35.4 |
| EURUSD | long | 2021-03-11 | 2021-03-25 | 14 | 10 | zamknięta | SL | -92.2 |
| AUDUSD | long | 2021-06-20 | 2021-07-01 | 11 | 8 | zamknięta | SL | -24.4 |
| EURJPY | long | 2021-06-21 | 2021-07-05 | 14 | 10 | zamknięta | czas | 24.8 |
| GBPUSD | long | 2021-06-21 | 2021-07-01 | 10 | 8 | zamknięta | SL | -137.4 |
| USDCAD | short | 2021-06-21 | 2021-07-05 | 14 | 10 | zamknięta | czas | 38.8 |
| GBPUSD | long | 2021-07-04 | 2021-07-16 | 12 | 10 | zamknięta | czas | -1.1 |
| EURJPY | long | 2021-07-11 | 2021-07-15 | 4 | 4 | zamknięta | SL | -91.6 |
| USDCAD | short | 2021-07-12 | 2021-07-16 | 4 | 4 | zamknięta | SL | -139.5 |
| USDCAD | short | 2021-07-19 | 2021-07-29 | 10 | 8 | zamknięta | TP | 305.7 |
| EURJPY | long | 2021-07-20 | 2021-07-29 | 9 | 7 | zamknięta | TP | 87.7 |
| AUDUSD | short | 2021-10-21 | 2021-10-28 | 7 | 5 | zamknięta | SL | -83.6 |
| GBPUSD | short | 2022-01-14 | 2022-01-25 | 11 | 7 | zamknięta | TP | 182.0 |
| GBPUSD | short | 2022-01-17 | 2022-01-25 | 8 | 6 | zamknięta | TP | 137.9 |
| GBPUSD | short | 2022-01-18 | 2022-01-22 | 4 | 4 | zamknięta | TP | 83.7 |
| USDCHF | long | 2022-08-02 | 2022-08-10 | 8 | 6 | zamknięta | SL | -116.3 |
| USDJPY | long | 2022-08-02 | 2022-08-16 | 14 | 10 | zamknięta | czas | -25.0 |
| EURJPY | long | 2022-08-03 | 2022-08-17 | 14 | 10 | zamknięta | czas | 48.9 |
| USDCHF | long | 2022-08-11 | 2022-08-22 | 11 | 7 | zamknięta | TP | 233.8 |
| EURUSD | short | 2022-11-16 | 2022-11-29 | 13 | 9 | zamknięta | SL | -118.5 |
| USDJPY | long | 2022-11-16 | 2022-11-29 | 13 | 9 | zamknięta | SL | -117.0 |
| AUDUSD | short | 2022-11-17 | 2022-12-01 | 14 | 10 | zamknięta | czas | 53.7 |
| EURUSD | short | 2022-11-17 | 2022-11-29 | 12 | 8 | zamknięta | SL | -81.4 |
| USDJPY | long | 2022-11-17 | 2022-11-29 | 12 | 8 | zamknięta | SL | -152.7 |
| EURUSD | short | 2022-11-18 | 2022-11-29 | 11 | 7 | zamknięta | SL | -114.7 |
| USDJPY | long | 2022-11-18 | 2022-11-29 | 11 | 7 | zamknięta | SL | -261.7 |
| GBPUSD | short | 2022-11-25 | 2022-12-02 | 7 | 5 | zamknięta | SL | -45.5 |
| GBPUSD | short | 2022-11-28 | 2022-12-02 | 4 | 4 | zamknięta | SL | -95.2 |
| USDJPY | long | 2022-12-05 | 2022-12-17 | 12 | 10 | zamknięta | czas | 326.2 |
| USDJPY | long | 2022-12-06 | 2022-12-20 | 14 | 10 | zamknięta | czas | 2.4 |
| EURUSD | long | 2023-02-28 | 2023-03-08 | 8 | 6 | zamknięta | TP | 83.5 |
| USDJPY | short | 2023-03-03 | 2023-03-09 | 6 | 4 | zamknięta | SL | -70.0 |
| USDJPY | short | 2023-03-06 | 2023-03-09 | 3 | 3 | zamknięta | SL | -153.5 |
| USDCAD | long | 2023-04-04 | 2023-04-13 | 9 | 7 | zamknięta | SL | -30.0 |
| USDCAD | long | 2023-04-05 | 2023-04-13 | 8 | 6 | zamknięta | SL | -46.3 |
| USDJPY | long | 2023-07-16 | 2023-07-28 | 12 | 10 | zamknięta | czas | 16.8 |
| USDCAD | short | 2023-08-13 | 2023-08-16 | 3 | 3 | zamknięta | SL | -63.0 |
| GBPUSD | long | 2023-08-28 | 2023-09-05 | 8 | 6 | zamknięta | SL | -65.7 |
| GBPUSD | long | 2023-09-07 | 2023-09-13 | 6 | 4 | zamknięta | SL | -28.4 |
| GBPUSD | long | 2023-09-10 | 2023-09-13 | 3 | 3 | zamknięta | SL | -41.9 |
| USDCHF | short | 2023-09-10 | 2023-09-13 | 3 | 3 | zamknięta | SL | -24.3 |
| USDCHF | short | 2023-09-21 | 2023-09-25 | 4 | 2 | zamknięta | SL | -34.8 |
| EURGBP | short | 2023-09-27 | 2023-10-11 | 14 | 10 | zamknięta | TP | 27.3 |
| AUDUSD | short | 2023-11-07 | 2023-11-16 | 9 | 7 | zamknięta | SL | -37.3 |
| EURJPY | long | 2023-12-11 | 2023-12-23 | 12 | 10 | zamknięta | czas | 21.0 |
| USDJPY | long | 2023-12-11 | 2023-12-15 | 4 | 4 | zamknięta | SL | -247.4 |
| EURJPY | long | 2023-12-12 | 2023-12-27 | 15 | 10 | zamknięta | czas | -56.6 |
| EURJPY | long | 2023-12-15 | 2023-12-20 | 5 | 3 | zamknięta | TP | 123.3 |
| USDJPY | long | 2023-12-15 | 2023-12-29 | 14 | 9 | zamknięta | SL | -124.9 |
| USDJPY | long | 2023-12-18 | 2023-12-29 | 11 | 8 | zamknięta | SL | -128.3 |
| USDJPY | long | 2023-12-19 | 2023-12-29 | 10 | 7 | zamknięta | SL | -169.2 |
| USDJPY | long | 2024-03-12 | 2024-03-20 | 8 | 6 | zamknięta | TP | 382.0 |
| USDJPY | long | 2024-03-13 | 2024-03-20 | 7 | 5 | zamknięta | TP | 290.9 |
| USDCHF | long | 2024-06-04 | 2024-06-07 | 3 | 3 | zamknięta | SL | -7.4 |
| USDCHF | long | 2024-06-09 | 2024-06-18 | 9 | 7 | zamknięta | SL | -81.9 |
| USDJPY | long | 2024-07-18 | 2024-07-24 | 6 | 4 | zamknięta | SL | -166.7 |
| AUDUSD | long | 2024-07-25 | 2024-07-31 | 6 | 4 | zamknięta | SL | -24.7 |
| EURJPY | long | 2024-07-25 | 2024-07-31 | 6 | 4 | zamknięta | SL | -192.9 |
| USDJPY | long | 2024-07-25 | 2024-07-31 | 6 | 4 | zamknięta | SL | -174.4 |
| EURJPY | long | 2024-07-28 | 2024-07-31 | 3 | 3 | zamknięta | SL | -245.7 |
| USDJPY | long | 2024-07-28 | 2024-07-31 | 3 | 3 | zamknięta | SL | -218.6 |
| EURGBP | short | 2024-08-05 | 2024-08-08 | 3 | 3 | zamknięta | SL | -57.7 |
| USDJPY | short | 2024-10-10 | 2024-10-14 | 4 | 2 | zamknięta | SL | -84.0 |
| USDJPY | short | 2024-10-14 | 2024-10-17 | 3 | 3 | zamknięta | SL | -29.3 |
| GBPUSD | long | 2024-10-24 | 2024-11-01 | 7 | 5 | zamknięta | SL | -63.3 |
| USDCHF | short | 2024-11-08 | 2024-11-12 | 4 | 2 | zamknięta | SL | -48.3 |
| USDCAD | long | 2025-04-06 | 2025-04-10 | 4 | 4 | zamknięta | SL | -215.5 |
| USDJPY | short | 2025-07-17 | 2025-07-31 | 14 | 10 | zamknięta | SL | -79.8 |
| EURUSD | long | 2025-08-03 | 2025-08-15 | 12 | 10 | zamknięta | czas | 63.8 |
| GBPUSD | long | 2025-08-03 | 2025-08-08 | 5 | 5 | zamknięta | TP | 159.6 |
| USDCAD | short | 2025-08-03 | 2025-08-15 | 12 | 10 | zamknięta | czas | -36.8 |
| USDCAD | short | 2025-08-24 | 2025-08-28 | 4 | 4 | zamknięta | TP | 44.2 |
| USDCAD | short | 2025-09-28 | 2025-10-02 | 4 | 4 | zamknięta | SL | -21.5 |
| USDCAD | short | 2025-09-29 | 2025-10-02 | 3 | 3 | zamknięta | SL | -43.5 |
| USDCAD | short | 2025-10-05 | 2025-10-09 | 4 | 4 | zamknięta | SL | -22.4 |
| USDCAD | short | 2025-10-06 | 2025-10-09 | 3 | 3 | zamknięta | SL | -41.4 |
| EURUSD | long | 2025-11-06 | 2025-11-14 | 8 | 6 | zamknięta | TP | 137.0 |
| USDCHF | short | 2025-11-06 | 2025-11-13 | 7 | 4 | zamknięta | TP | 119.9 |
| EURGBP | long | 2026-01-07 | 2026-01-21 | 14 | 10 | zamknięta | czas | 14.9 |
| EURGBP | long | 2026-01-08 | 2026-01-22 | 14 | 10 | zamknięta | TP | 67.8 |
| EURGBP | long | 2026-01-14 | 2026-01-21 | 7 | 5 | zamknięta | TP | 17.8 |
| USDJPY | long | 2026-01-29 | 2026-02-13 | 15 | 10 | zamknięta | SL | -80.8 |
| USDJPY | long | 2026-01-30 | 2026-02-13 | 14 | 9 | zamknięta | SL | -83.1 |
| AUDUSD | long | 2026-06-11 | 2026-06-24 | 13 | 8 | zamknięta | SL | -129.5 |
| USDJPY | long | 2026-08-05 | 2026-08-20 | 15 | 10 | zamknięta | czas | 59.8 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 872); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 10.73 pips/transakcję, percentyl **100.0** (losowe: 5%=-6.51, mediana=-0.98, 95%=4.55).

- **Deflated Sharpe Ratio**: 0.997 (Sharpe na transakcję 0.111, próg przy 36 próbach 0.034).

- **PBO** (CSCV, 16 bloków, 36 wariantów): 0.138 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 619 transakcji, śr. -0.21 pips, 0.02 R.

- **Bootstrap 95%** średnich pipsów: całość [2.77; 19.07], OOS [-23.98; 0.21].

- **Spread**: ×1 10.73, ×1,5 9.91, ×2 9.10 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.23% transakcji.

- **Noce (swap pominięty, O5)**: średnio 4.2 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 8.65, 1 pips: 6.58 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058); wejście na open następnego dnia (rano)

HYPOTHESIS = """Na świecach dziennych par FX trend trwa miesiącami, a krótkie wyprzedanie w trendzie wzrostowym (i wykupienie
w spadkowym) zwykle się cofa w ciągu kilku dni. Kupujemy, gdy RSI spada pod próg, ale tylko gdy cena jest nad rosnącą SMA200
(sprzedajemy lustrzanie pod opadającą SMA200). Bez filtra trendu czysty powrót RSI na D1 po spreadzie nie zarabia — to
sprawdziło poszukiwanie (research/rsi_d1/README.md). Wersje różnią się progiem RSI, wyjściem (po X dniach na zamknięciu,
TP/SL w ATR, stop pod dołkiem) i stawką: stała, rosnąca z kolejną świecą wyprzedania, z liczbą otwartych pozycji, z głębokością RSI.
Konfiguracje wybrane wyłącznie na IS (przed 2019-05); wynik OOS badania jest w raporcie poszukiwania."""

# Każda konfiguracja = jedna wersja strategii (wariant wejścia); × 3 limity czasu z EXITS.
#   rsi:   reguły (okres RSI, próg wyprzedania); wykupienie = 100 − próg; kilka reguł = sygnał, gdy spełniona dowolna
#   tryb:  "stan" — sygnał w każdej świecy za progiem (z PYRAMID dokładanie pozycji); "zdarzenie" — pierwsza świeca za progiem
#   trend: "sma200_rosnie" — long tylko nad SMA200, która rośnie od 20 dni (short lustrzanie); "sma200" — tylko cena vs SMA200
#   tp/sl: None = bez poziomu (wyjście tylko po limicie dni, na zamknięciu); ("atr", k) = k × ATR14 od zamknięcia dnia sygnału;
#          ("dolek", k, b) = SL pod najniższym low k dni − b × ATR14; ("r", m) = TP w m × odległości do SL
#   waga:  "stala" 1; "seria" = która z kolei świeca za progiem (1, 2, 3+); "otwarte" = 1 + sygnały w tym kierunku w 5 poprzednich
#          dniach (≈ liczba otwartych pozycji), najwyżej 3; "glebokosc" = 0,5 + 2 × głębokość RSI za progiem (0,5–2,5)
CONFIGS = [
    # 0 = wybór po IS (stabilność: najwięcej zyskownych kwartałów i lat przy największej liczbie transakcji)
    {"rsi": ((3, 15), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((3, 15), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 3), "sl": ("atr", 1.5), "waga": "otwarte"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": ("atr", 1.5), "waga": "seria"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 3), "sl": ("atr", 1), "waga": "seria"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "seria"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "stala"},   # 6 = stała stawka, do porównania z 1, 7, 8
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "otwarte"},
    {"rsi": ((5, 20), (14, 40)), "tryb": "stan", "trend": "sma200_rosnie", "tp": None, "sl": None, "waga": "glebokosc"},
    {"rsi": ((5, 25),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("atr", 1.5), "sl": ("atr", 1), "waga": "otwarte"},
    {"rsi": ((14, 40),), "tryb": "stan", "trend": "sma200_rosnie", "tp": ("r", 2), "sl": ("dolek", 5, 0.5), "waga": "seria"},
    {"rsi": ((14, 35),), "tryb": "stan", "trend": "sma200", "tp": ("szczyt", 5), "sl": ("dolek", 5, 0), "waga": "stala"},
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

PYRAMID = 3   # do 3 pozycji naraz w parze, tylko w jednym kierunku (dokładanie, D-034)
EXITS = [{"kind": "level", "cap": c} for c in (3, 5, 10)]   # wyjście po 3 / 5 / 10 dniach na zamknięciu, chyba że wcześniej TP/SL
# Stawka bazowa (% kapitału jako depozyt, × 30 nominału) — mniejsza niż domyślne 5–30%, bo waga mnoży ją do 3×,
# PYRAMID dokłada do 3 pozycji w parze, a 8 par z USD porusza się razem: przy 5% obsunięcie IS przekracza 90%.
SIZING = [1, 2, 3, 5]


def _streak(mask):
    """Która z kolei świeca w serii True (0 poza serią)."""
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def _setup(df, c, ind, full=True):
    """Kierunek sygnału (+1 long / −1 short / 0) i cechy do stawki — tylko z zamkniętych świec."""
    close = df.close
    n = len(df)
    lo, hi = np.zeros(n, bool), np.zeros(n, bool)
    zone_lo, zone_hi = np.zeros(n, bool), np.zeros(n, bool)
    depth_lo, depth_hi = np.zeros(n), np.zeros(n)
    for period, level in c["rsi"]:
        rs = ind.rsi(close, period)
        r = np.array(rs, dtype=float)
        ok = ~np.isnan(r)
        with np.errstate(invalid="ignore"):
            a, b = ok & (r < level), ok & (r > 100 - level)
        zone_lo |= a
        zone_hi |= b
        depth_lo = np.where(a, np.fmax(depth_lo, (level - r) / level), depth_lo)
        depth_hi = np.where(b, np.fmax(depth_hi, (r - (100 - level)) / level), depth_hi)
        if c["tryb"] == "zdarzenie":
            a = ind.cross_below(rs, level).to_numpy(bool) & ok
            b = ind.cross_above(rs, 100 - level).to_numpy(bool) & ok
        lo |= a
        hi |= b
    s200 = ind.sma(close, 200)
    up, dn = np.array(close > s200, dtype=bool), np.array(close < s200, dtype=bool)
    if c["trend"] == "sma200_rosnie":
        up &= ind.rising(s200, 20).to_numpy(bool)
        dn &= ind.falling(s200, 20).to_numpy(bool)
    direction = (lo & up).astype(int) - (hi & dn).astype(int)
    if not full:
        return direction, None, None, None
    streak = np.where(direction > 0, _streak(zone_lo), np.where(direction < 0, _streak(zone_hi), 0))
    depth = np.where(direction > 0, depth_lo, np.where(direction < 0, depth_hi, 0.0))
    past = np.r_[0, np.cumsum(direction > 0)][:-1], np.r_[0, np.cumsum(direction < 0)][:-1]   # do świecy t−1
    up_n = past[0] - np.r_[np.zeros(5, np.int64), past[0]][:n]                               # sygnały long w t−5 … t−1
    dn_n = past[1] - np.r_[np.zeros(5, np.int64), past[1]][:n]
    recent = np.where(direction > 0, up_n, np.where(direction < 0, dn_n, 0))
    return direction, streak, depth, recent


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    direction, streak, depth, recent = _setup(df, c, ind)
    if c["waga"] == "seria":
        w = np.clip(streak, 1, 3).astype(float)
    elif c["waga"] == "otwarte":
        w = np.clip(1 + recent, 1, 3).astype(float)
    elif c["waga"] == "glebokosc":
        w = np.clip(0.5 + 2 * depth, 0.5, 2.5)
    else:
        w = np.ones(len(df))
    return pd.Series(np.where(direction != 0, direction * w, 0.0), index=df.index)


def levels(df, p, ind):
    c = CONFIGS[p["cfg"]]
    sl = pd.Series(np.nan, index=df.index)
    tp = pd.Series(np.nan, index=df.index)
    if c["sl"] is None and c["tp"] is None:   # wyjście tylko po limicie dni (na zamknięciu)
        return pd.DataFrame({"tp": tp, "sl": sl})
    direction, *_ = _setup(df, c, ind, full=False)
    d = pd.Series(np.where(direction != 0, direction, np.nan), index=df.index)   # poziomy tylko na świecach sygnału
    atr = ind.atr(df, 14)
    close = df.close
    if c["sl"] is not None:
        if c["sl"][0] == "atr":
            sl = close - d * c["sl"][1] * atr
        else:                                  # ("dolek", k, b): pod najniższym low k dni (long) / nad najwyższym high (short)
            k, b = c["sl"][1], c["sl"][2]
            sl = (ind.lowest(df.low, k) - b * atr).where(d > 0, ind.highest(df.high, k) + b * atr).where(d.notna())
    if c["tp"] is not None:
        if c["tp"][0] == "atr":
            tp = close + d * c["tp"][1] * atr
        elif c["tp"][0] == "r":
            tp = close + c["tp"][1] * (close - sl)
        else:                                  # ("szczyt", k): najwyższe high k dni (long) / najniższe low (short)
            k = c["tp"][1]
            tp = ind.highest(df.high, k).where(d > 0, ind.lowest(df.low, k)).where(d.notna())
    return pd.DataFrame({"tp": tp, "sl": sl})

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
