# Raport strategii: nowa

Run `20261125-181555` · silnik 0.14.0 · kod `475194a31f9b7769` · dane `02cdfcd25d7e5788`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -0.76 |
| percentyl benchmarku ≥ 95 | ✘ | 85.00 |
| PBO < 0,3 | ✔ | 0.25 |
| DSR ≥ 0,95 | ✘ | 0.03 |
| dodatni przy spreadzie ×1,5 | ✘ | -0.06 |

## Hipoteza

Na EUR/USD kierunek krótkiego impetu może przenosić się na następny dzień: jeśli RSI albo EMA rośnie,
kolejny dzień częściej jest wzrostowy, jeśli spada — spadkowy. Codziennie jedna transakcja na 24 h (open dnia → zamknięcie
dnia), kierunek z jednego wskaźnika: RSI(n) rosnące → long, malejące → short; albo EMA(n) rosnąca → long, malejąca → short.
„Rośnie” = wartość dziś wyższa niż k dni temu. Silnik liczy wszystkie kombinacje n × k na tych samych zasadach wyjścia;
wybór najlepszej tylko po IS, a kara za liczbę prób jest w DSR.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-24; źródło: yahoo.

- In-sample do 2019-05-19, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS. OOS tego okresu widziało już 3 wersji kodu strategii i 5 kandydatów eksploracji; ta strategia: 1 wersji.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 149, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 118, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 56** (56 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 159 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 3.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 1 świecach | cfg=55 | 3 688 | 0.01 | 0.98 | 50.6 | 1 896 | -0.01 | -0.76 |
| 2 | po 1 świecach | cfg=54 | 3 690 | 0.01 | 0.83 | 50.5 | 1 896 | -0.01 | -0.51 |
| 3 | po 1 świecach | cfg=53 | 3 691 | 0.01 | 0.62 | 50.2 | 1 896 | -0.00 | -0.24 |
| 4 | po 1 świecach | cfg=42 | 3 860 | 0.00 | -0.27 | 49.2 | 1 896 | -0.01 | -0.50 |
| 5 | po 1 świecach | cfg=52 | 3 692 | 0.00 | -1.42 | 50.0 | 1 896 | -0.01 | -0.49 |
| 6 | po 1 świecach | cfg=49 | 3 791 | 0.00 | -1.27 | 49.3 | 1 896 | -0.01 | -0.30 |
| 7 | po 1 świecach | cfg=43 | 3 858 | -0.00 | -0.38 | 49.4 | 1 896 | -0.01 | -0.26 |
| 8 | po 1 świecach | cfg=51 | 3 788 | -0.00 | -0.75 | 49.6 | 1 896 | -0.01 | -0.66 |
| 9 | po 1 świecach | cfg=50 | 3 790 | -0.00 | -1.01 | 49.0 | 1 896 | -0.01 | -0.46 |
| 10 | po 1 świecach | cfg=41 | 3 861 | -0.00 | -1.33 | 48.9 | 1 896 | -0.01 | -0.58 |

## Najlepszy wariant IS: po 1 świecach (cfg=55)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 5584 | 0.4 | 2 183.6 | 49.8 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2004 | 74 | 16.3 | 1 203.2 | 63.5 |
| 2005 | 257 | -0.6 | -143.5 | 48.6 |
| 2006 | 258 | -1.7 | -431.0 | 48.4 |
| 2007 | 253 | 4.5 | 1 144.4 | 54.2 |
| 2008 | 238 | 6.0 | 1 417.7 | 55.0 |
| 2009 | 246 | 2.8 | 691.7 | 52.8 |
| 2010 | 254 | -1.2 | -306.6 | 47.6 |
| 2011 | 251 | -0.0 | -6.8 | 49.8 |
| 2012 | 257 | -2.0 | -514.7 | 50.2 |
| 2013 | 253 | 0.0 | 2.3 | 51.0 |
| 2014 | 249 | 1.3 | 326.4 | 50.6 |
| 2015 | 244 | 3.0 | 743.9 | 50.8 |
| 2016 | 253 | -5.2 | -1 323.6 | 45.8 |
| 2017 | 250 | 1.3 | 322.4 | 52.0 |
| 2018 | 253 | 1.4 | 349.7 | 48.6 |
| 2019 | 255 | -1.2 | -315.7 | 46.3 |
| 2020 | 247 | -0.2 | -46.0 | 49.8 |
| 2021 | 256 | -1.0 | -245.5 | 51.2 |
| 2022 | 257 | 3.0 | 768.0 | 51.4 |
| 2023 | 254 | -0.2 | -55.6 | 48.8 |
| 2024 | 253 | -3.4 | -858.3 | 40.3 |
| 2025 | 246 | 0.0 | 9.2 | 52.0 |
| 2026 | 226 | -2.4 | -547.9 | 46.5 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 3688 | 1.0 | 3 625.5 | 50.6 |
| OOS | 1896 | -0.8 | -1 441.9 | 48.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 8 387 | -16.1 | -0.8 | -49.3 | -49.4 | 0.03 | 0 |
| 10.0% | 3 758 | -62.4 | -4.3 | -83.6 | -83.6 | 0.03 | 0 |
| 15.0% | 745 | -92.5 | -11.0 | -97.1 | -97.1 | 0.03 | 0 |
| 20.0% | 2 | -100.0 | -31.9 | -100.0 | -100.0 | 0.03 | 0 |
| 30.0% | -362 | -103.6 | -100.0 | -101.7 | -101.7 | 0.27 | 4563 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-25): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **5584**, otwarte: **0** (razem 5584).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 5584 | 1 | 1 | 1 | 1 | 1 | 0.4 | 2 184 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 5584 | 1 | 1 | 1 | 1 | 1 | 0.4 | 2 184 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| EURUSD | short | 2004-09-15 | 2004-09-16 | 1 | 1 | zamknięta | czas | -32.9 |
| EURUSD | short | 2004-09-16 | 2004-09-17 | 1 | 1 | zamknięta | czas | 13.2 |
| EURUSD | short | 2004-09-19 | 2004-09-20 | 1 | 1 | zamknięta | czas | 2.1 |
| EURUSD | short | 2004-09-20 | 2004-09-21 | 1 | 1 | zamknięta | czas | -157.9 |
| EURUSD | short | 2004-09-21 | 2004-09-22 | 1 | 1 | zamknięta | czas | 62.0 |
| EURUSD | short | 2004-09-22 | 2004-09-23 | 1 | 1 | zamknięta | czas | -6.9 |
| EURUSD | short | 2004-09-23 | 2004-09-24 | 1 | 1 | zamknięta | czas | -14.9 |
| EURUSD | long | 2004-09-26 | 2004-09-27 | 1 | 1 | zamknięta | czas | 20.0 |
| EURUSD | long | 2004-09-27 | 2004-09-28 | 1 | 1 | zamknięta | czas | 11.2 |
| EURUSD | long | 2004-09-28 | 2004-09-29 | 1 | 1 | zamknięta | czas | 18.1 |
| EURUSD | long | 2004-09-29 | 2004-09-30 | 1 | 1 | zamknięta | czas | 96.1 |
| EURUSD | long | 2004-09-30 | 2004-10-01 | 1 | 1 | zamknięta | czas | -33.9 |
| EURUSD | long | 2004-10-03 | 2004-10-04 | 1 | 1 | zamknięta | czas | -111.9 |
| EURUSD | long | 2004-10-04 | 2004-10-05 | 1 | 1 | zamknięta | czas | 24.1 |
| EURUSD | long | 2004-10-05 | 2004-10-06 | 1 | 1 | zamknięta | czas | -34.9 |
| EURUSD | long | 2004-10-06 | 2004-10-07 | 1 | 1 | zamknięta | czas | 19.0 |
| EURUSD | long | 2004-10-07 | 2004-10-08 | 1 | 1 | zamknięta | czas | 109.2 |
| EURUSD | long | 2004-10-10 | 2004-10-11 | 1 | 1 | zamknięta | czas | -28.9 |
| EURUSD | long | 2004-10-11 | 2004-10-12 | 1 | 1 | zamknięta | czas | -63.9 |
| EURUSD | long | 2004-10-12 | 2004-10-13 | 1 | 1 | zamknięta | czas | 26.0 |
| EURUSD | long | 2004-10-13 | 2004-10-14 | 1 | 1 | zamknięta | czas | 42.1 |
| EURUSD | long | 2004-10-14 | 2004-10-15 | 1 | 1 | zamknięta | czas | 91.1 |
| EURUSD | long | 2004-10-17 | 2004-10-18 | 1 | 1 | zamknięta | czas | 4.1 |
| EURUSD | long | 2004-10-18 | 2004-10-19 | 1 | 1 | zamknięta | czas | 23.2 |
| EURUSD | long | 2004-10-19 | 2004-10-20 | 1 | 1 | zamknięta | czas | 67.1 |
| EURUSD | long | 2004-10-20 | 2004-10-21 | 1 | 1 | zamknięta | czas | 40.1 |
| EURUSD | long | 2004-10-21 | 2004-10-22 | 1 | 1 | zamknięta | czas | 108.0 |
| EURUSD | long | 2004-10-24 | 2004-10-25 | 1 | 1 | zamknięta | czas | 79.2 |
| EURUSD | long | 2004-10-25 | 2004-10-26 | 1 | 1 | zamknięta | czas | -45.9 |
| EURUSD | long | 2004-10-26 | 2004-10-27 | 1 | 1 | zamknięta | czas | -59.9 |
| EURUSD | long | 2004-10-28 | 2004-10-29 | 1 | 1 | zamknięta | czas | 119.2 |
| EURUSD | long | 2004-11-01 | 2004-11-02 | 1 | 1 | zamknięta | czas | -82.0 |
| EURUSD | long | 2004-11-02 | 2004-11-03 | 1 | 1 | zamknięta | czas | -28.9 |
| EURUSD | long | 2004-11-03 | 2004-11-04 | 1 | 1 | zamknięta | czas | 102.2 |
| EURUSD | long | 2004-11-04 | 2004-11-05 | 1 | 1 | zamknięta | czas | 50.1 |
| EURUSD | long | 2004-11-05 | 2004-11-06 | 1 | 1 | zamknięta | czas | 93.1 |
| EURUSD | long | 2004-11-09 | 2004-11-10 | 1 | 1 | zamknięta | czas | -10.9 |
| EURUSD | long | 2004-11-10 | 2004-11-11 | 1 | 1 | zamknięta | czas | -17.0 |
| EURUSD | long | 2004-11-11 | 2004-11-12 | 1 | 1 | zamknięta | czas | 23.2 |
| EURUSD | long | 2004-11-12 | 2004-11-13 | 1 | 1 | zamknięta | czas | 81.1 |
| EURUSD | long | 2004-11-15 | 2004-11-16 | 1 | 1 | zamknięta | czas | -54.0 |
| EURUSD | long | 2004-11-16 | 2004-11-17 | 1 | 1 | zamknięta | czas | 23.1 |
| EURUSD | long | 2004-11-17 | 2004-11-18 | 1 | 1 | zamknięta | czas | 76.2 |
| EURUSD | long | 2004-11-18 | 2004-11-19 | 1 | 1 | zamknięta | czas | -90.9 |
| EURUSD | long | 2004-11-19 | 2004-11-20 | 1 | 1 | zamknięta | czas | 77.0 |
| EURUSD | long | 2004-11-22 | 2004-11-23 | 1 | 1 | zamknięta | czas | 15.2 |
| EURUSD | long | 2004-11-23 | 2004-11-24 | 1 | 1 | zamknięta | czas | 57.0 |
| EURUSD | long | 2004-11-24 | 2004-11-25 | 1 | 1 | zamknięta | czas | 80.1 |
| EURUSD | long | 2004-11-25 | 2004-11-26 | 1 | 1 | zamknięta | czas | 75.1 |
| EURUSD | long | 2004-11-26 | 2004-11-27 | 1 | 1 | zamknięta | czas | 14.1 |
| EURUSD | long | 2004-11-29 | 2004-11-30 | 1 | 1 | zamknięta | czas | -9.9 |
| EURUSD | long | 2004-11-30 | 2004-12-01 | 1 | 1 | zamknięta | czas | 34.2 |
| EURUSD | long | 2004-12-01 | 2004-12-02 | 1 | 1 | zamknięta | czas | 49.0 |
| EURUSD | long | 2004-12-02 | 2004-12-03 | 1 | 1 | zamknięta | czas | -85.9 |
| EURUSD | long | 2004-12-03 | 2004-12-04 | 1 | 1 | zamknięta | czas | 186.2 |
| EURUSD | long | 2004-12-06 | 2004-12-07 | 1 | 1 | zamknięta | czas | -56.0 |
| EURUSD | long | 2004-12-07 | 2004-12-08 | 1 | 1 | zamknięta | czas | 37.1 |
| EURUSD | long | 2004-12-08 | 2004-12-09 | 1 | 1 | zamknięta | czas | -87.8 |
| EURUSD | long | 2004-12-09 | 2004-12-10 | 1 | 1 | zamknięta | czas | -44.9 |
| EURUSD | long | 2004-12-10 | 2004-12-11 | 1 | 1 | zamknięta | czas | -79.9 |
| EURUSD | long | 2004-12-13 | 2004-12-14 | 1 | 1 | zamknięta | czas | 97.2 |
| EURUSD | long | 2004-12-14 | 2004-12-15 | 1 | 1 | zamknięta | czas | -14.0 |
| EURUSD | long | 2004-12-15 | 2004-12-16 | 1 | 1 | zamknięta | czas | 93.1 |
| EURUSD | long | 2004-12-16 | 2004-12-17 | 1 | 1 | zamknięta | czas | -148.9 |
| EURUSD | long | 2004-12-17 | 2004-12-18 | 1 | 1 | zamknięta | czas | 56.1 |
| EURUSD | long | 2004-12-20 | 2004-12-21 | 1 | 1 | zamknięta | czas | 82.2 |
| EURUSD | long | 2004-12-21 | 2004-12-22 | 1 | 1 | zamknięta | czas | -26.0 |
| EURUSD | long | 2004-12-22 | 2004-12-23 | 1 | 1 | zamknięta | czas | 21.1 |
| EURUSD | long | 2004-12-23 | 2004-12-24 | 1 | 1 | zamknięta | czas | 122.2 |
| EURUSD | long | 2004-12-24 | 2004-12-25 | 1 | 1 | zamknięta | czas | 13.0 |
| EURUSD | long | 2004-12-27 | 2004-12-28 | 1 | 1 | zamknięta | czas | 93.1 |
| EURUSD | long | 2004-12-28 | 2004-12-29 | 1 | 1 | zamknięta | czas | -27.8 |
| EURUSD | long | 2004-12-29 | 2004-12-30 | 1 | 1 | zamknięta | czas | 10.0 |
| EURUSD | long | 2004-12-30 | 2004-12-31 | 1 | 1 | zamknięta | czas | 23.0 |
| EURUSD | long | 2004-12-31 | 2005-01-01 | 1 | 1 | zamknięta | czas | -49.8 |
| EURUSD | long | 2005-01-03 | 2005-01-04 | 1 | 1 | zamknięta | czas | -111.9 |
| EURUSD | long | 2005-01-04 | 2005-01-05 | 1 | 1 | zamknięta | czas | -187.9 |
| EURUSD | long | 2005-01-05 | 2005-01-06 | 1 | 1 | zamknięta | czas | -5.0 |
| EURUSD | long | 2005-01-06 | 2005-01-07 | 1 | 1 | zamknięta | czas | -97.9 |
| EURUSD | long | 2005-01-07 | 2005-01-08 | 1 | 1 | zamknięta | czas | -106.9 |
| EURUSD | long | 2005-01-10 | 2005-01-11 | 1 | 1 | zamknięta | czas | 37.2 |
| EURUSD | long | 2005-01-11 | 2005-01-12 | 1 | 1 | zamknięta | czas | -0.9 |
| EURUSD | long | 2005-01-12 | 2005-01-13 | 1 | 1 | zamknięta | czas | 144.1 |
| EURUSD | long | 2005-01-13 | 2005-01-14 | 1 | 1 | zamknięta | czas | -48.0 |
| EURUSD | long | 2005-01-14 | 2005-01-15 | 1 | 1 | zamknięta | czas | -112.9 |
| EURUSD | long | 2005-01-17 | 2005-01-18 | 1 | 1 | zamknięta | czas | -51.8 |
| EURUSD | long | 2005-01-18 | 2005-01-19 | 1 | 1 | zamknięta | czas | -32.0 |
| EURUSD | long | 2005-01-19 | 2005-01-20 | 1 | 1 | zamknięta | czas | -16.8 |
| EURUSD | long | 2005-01-20 | 2005-01-21 | 1 | 1 | zamknięta | czas | -41.0 |
| EURUSD | long | 2005-01-21 | 2005-01-22 | 1 | 1 | zamknięta | czas | 79.2 |
| EURUSD | long | 2005-01-24 | 2005-01-25 | 1 | 1 | zamknięta | czas | -4.0 |
| EURUSD | long | 2005-01-25 | 2005-01-26 | 1 | 1 | zamknięta | czas | -67.9 |
| EURUSD | long | 2005-01-26 | 2005-01-27 | 1 | 1 | zamknięta | czas | 106.2 |
| EURUSD | long | 2005-01-27 | 2005-01-28 | 1 | 1 | zamknięta | czas | -36.9 |
| EURUSD | long | 2005-01-28 | 2005-01-29 | 1 | 1 | zamknięta | czas | -19.9 |
| EURUSD | long | 2005-01-31 | 2005-02-01 | 1 | 1 | zamknięta | czas | 25.1 |
| EURUSD | long | 2005-02-01 | 2005-02-02 | 1 | 1 | zamknięta | czas | 0.1 |
| EURUSD | long | 2005-02-02 | 2005-02-03 | 1 | 1 | zamknięta | czas | -17.1 |
| EURUSD | long | 2005-02-03 | 2005-02-04 | 1 | 1 | zamknięta | czas | -64.8 |
| EURUSD | long | 2005-02-04 | 2005-02-05 | 1 | 1 | zamknięta | czas | -116.0 |
| EURUSD | long | 2005-02-07 | 2005-02-08 | 1 | 1 | zamknięta | czas | -92.8 |
| EURUSD | long | 2005-02-08 | 2005-02-09 | 1 | 1 | zamknięta | czas | 3.0 |
| EURUSD | long | 2005-02-09 | 2005-02-10 | 1 | 1 | zamknięta | czas | 41.1 |
| EURUSD | long | 2005-02-10 | 2005-02-11 | 1 | 1 | zamknięta | czas | 67.1 |
| EURUSD | long | 2005-02-11 | 2005-02-12 | 1 | 1 | zamknięta | czas | 10.1 |
| EURUSD | long | 2005-02-14 | 2005-02-15 | 1 | 1 | zamknięta | czas | 82.2 |
| EURUSD | long | 2005-02-15 | 2005-02-16 | 1 | 1 | zamknięta | czas | 41.1 |
| EURUSD | long | 2005-02-16 | 2005-02-17 | 1 | 1 | zamknięta | czas | 10.1 |
| EURUSD | long | 2005-02-17 | 2005-02-18 | 1 | 1 | zamknięta | czas | 49.0 |
| EURUSD | long | 2005-02-18 | 2005-02-19 | 1 | 1 | zamknięta | czas | -3.8 |
| EURUSD | long | 2005-02-21 | 2005-02-22 | 1 | 1 | zamknięta | czas | -7.9 |
| EURUSD | long | 2005-02-22 | 2005-02-23 | 1 | 1 | zamknięta | czas | 192.1 |
| EURUSD | long | 2005-02-23 | 2005-02-24 | 1 | 1 | zamknięta | czas | -56.9 |
| EURUSD | long | 2005-02-24 | 2005-02-25 | 1 | 1 | zamknięta | czas | -18.0 |
| EURUSD | long | 2005-02-25 | 2005-02-26 | 1 | 1 | zamknięta | czas | 68.1 |
| EURUSD | long | 2005-02-28 | 2005-03-01 | 1 | 1 | zamknięta | czas | -35.9 |
| EURUSD | long | 2005-03-01 | 2005-03-02 | 1 | 1 | zamknięta | czas | -47.9 |
| EURUSD | long | 2005-03-02 | 2005-03-03 | 1 | 1 | zamknięta | czas | -34.8 |
| EURUSD | long | 2005-03-03 | 2005-03-04 | 1 | 1 | zamknięta | czas | -32.9 |
| EURUSD | long | 2005-03-04 | 2005-03-05 | 1 | 1 | zamknięta | czas | 127.1 |
| EURUSD | long | 2005-03-07 | 2005-03-08 | 1 | 1 | zamknięta | czas | -13.8 |
| EURUSD | long | 2005-03-08 | 2005-03-09 | 1 | 1 | zamknięta | czas | 127.1 |
| EURUSD | long | 2005-03-09 | 2005-03-10 | 1 | 1 | zamknięta | czas | 28.0 |
| EURUSD | long | 2005-03-10 | 2005-03-11 | 1 | 1 | zamknięta | czas | 58.2 |
| EURUSD | long | 2005-03-11 | 2005-03-12 | 1 | 1 | zamknięta | czas | 36.0 |
| EURUSD | long | 2005-03-14 | 2005-03-15 | 1 | 1 | zamknięta | czas | -107.0 |
| EURUSD | long | 2005-03-15 | 2005-03-16 | 1 | 1 | zamknięta | czas | -56.8 |
| EURUSD | long | 2005-03-16 | 2005-03-17 | 1 | 1 | zamknięta | czas | 100.0 |
| EURUSD | long | 2005-03-17 | 2005-03-18 | 1 | 1 | zamknięta | czas | -34.8 |
| EURUSD | long | 2005-03-18 | 2005-03-19 | 1 | 1 | zamknięta | czas | -61.0 |
| EURUSD | long | 2005-03-21 | 2005-03-22 | 1 | 1 | zamknięta | czas | -154.9 |
| EURUSD | long | 2005-03-22 | 2005-03-23 | 1 | 1 | zamknięta | czas | -88.9 |
| EURUSD | long | 2005-03-23 | 2005-03-24 | 1 | 1 | zamknięta | czas | -85.8 |
| EURUSD | long | 2005-03-24 | 2005-03-25 | 1 | 1 | zamknięta | czas | -60.0 |
| EURUSD | long | 2005-03-25 | 2005-03-26 | 1 | 1 | zamknięta | czas | 24.2 |
| EURUSD | long | 2005-03-27 | 2005-03-28 | 1 | 1 | zamknięta | czas | -63.9 |
| EURUSD | long | 2005-03-28 | 2005-03-29 | 1 | 1 | zamknięta | czas | 42.0 |
| EURUSD | long | 2005-03-29 | 2005-03-30 | 1 | 1 | zamknięta | czas | -22.8 |
| EURUSD | long | 2005-03-30 | 2005-03-31 | 1 | 1 | zamknięta | czas | 51.0 |
| EURUSD | long | 2005-03-31 | 2005-04-01 | 1 | 1 | zamknięta | czas | -71.8 |
| EURUSD | long | 2005-04-03 | 2005-04-04 | 1 | 1 | zamknięta | czas | -49.0 |
| EURUSD | long | 2005-04-04 | 2005-04-05 | 1 | 1 | zamknięta | czas | 8.0 |
| EURUSD | long | 2005-04-05 | 2005-04-06 | 1 | 1 | zamknięta | czas | 11.2 |
| EURUSD | long | 2005-04-06 | 2005-04-07 | 1 | 1 | zamknięta | czas | -21.9 |
| EURUSD | short | 2005-04-07 | 2005-04-08 | 1 | 1 | zamknięta | czas | -73.0 |
| EURUSD | long | 2005-04-10 | 2005-04-11 | 1 | 1 | zamknięta | czas | 49.0 |
| EURUSD | long | 2005-04-11 | 2005-04-12 | 1 | 1 | zamknięta | czas | -55.9 |
| EURUSD | long | 2005-04-12 | 2005-04-13 | 1 | 1 | zamknięta | czas | -3.9 |
| EURUSD | long | 2005-04-13 | 2005-04-14 | 1 | 1 | zamknięta | czas | -119.0 |
| EURUSD | long | 2005-04-14 | 2005-04-15 | 1 | 1 | zamknięta | czas | 117.2 |
| EURUSD | long | 2005-04-17 | 2005-04-18 | 1 | 1 | zamknięta | czas | 104.0 |
| EURUSD | long | 2005-04-18 | 2005-04-19 | 1 | 1 | zamknięta | czas | 46.2 |
| EURUSD | long | 2005-04-19 | 2005-04-20 | 1 | 1 | zamknięta | czas | 24.1 |
| EURUSD | long | 2005-04-20 | 2005-04-21 | 1 | 1 | zamknięta | czas | -41.9 |
| EURUSD | long | 2005-04-21 | 2005-04-22 | 1 | 1 | zamknięta | czas | 6.1 |
| EURUSD | long | 2005-04-24 | 2005-04-25 | 1 | 1 | zamknięta | czas | -62.0 |
| EURUSD | long | 2005-04-25 | 2005-04-26 | 1 | 1 | zamknięta | czas | -11.9 |
| EURUSD | long | 2005-04-26 | 2005-04-27 | 1 | 1 | zamknięta | czas | -61.8 |
| EURUSD | long | 2005-04-27 | 2005-04-28 | 1 | 1 | zamknięta | czas | -18.9 |
| EURUSD | long | 2005-04-28 | 2005-04-29 | 1 | 1 | zamknięta | czas | -43.9 |
| EURUSD | long | 2005-05-01 | 2005-05-02 | 1 | 1 | zamknięta | czas | -14.0 |
| EURUSD | long | 2005-05-02 | 2005-05-03 | 1 | 1 | zamknięta | czas | 37.0 |
| EURUSD | long | 2005-05-03 | 2005-05-04 | 1 | 1 | zamknięta | czas | 62.2 |
| EURUSD | long | 2005-05-04 | 2005-05-05 | 1 | 1 | zamknięta | czas | 4.1 |
| EURUSD | long | 2005-05-05 | 2005-05-06 | 1 | 1 | zamknięta | czas | -136.9 |
| EURUSD | long | 2005-05-08 | 2005-05-09 | 1 | 1 | zamknięta | czas | 36.0 |
| EURUSD | long | 2005-05-09 | 2005-05-10 | 1 | 1 | zamknięta | czas | 29.1 |
| EURUSD | long | 2005-05-10 | 2005-05-11 | 1 | 1 | zamknięta | czas | -73.9 |
| EURUSD | short | 2005-05-11 | 2005-05-12 | 1 | 1 | zamknięta | czas | 135.1 |
| EURUSD | short | 2005-05-12 | 2005-05-13 | 1 | 1 | zamknięta | czas | 70.1 |
| EURUSD | short | 2005-05-15 | 2005-05-16 | 1 | 1 | zamknięta | czas | -33.9 |
| EURUSD | short | 2005-05-16 | 2005-05-17 | 1 | 1 | zamknięta | czas | 36.1 |
| EURUSD | short | 2005-05-17 | 2005-05-18 | 1 | 1 | zamknięta | czas | -77.8 |
| EURUSD | short | 2005-05-18 | 2005-05-19 | 1 | 1 | zamknięta | czas | 39.0 |
| EURUSD | short | 2005-05-19 | 2005-05-20 | 1 | 1 | zamknięta | czas | 84.1 |
| EURUSD | short | 2005-05-22 | 2005-05-23 | 1 | 1 | zamknięta | czas | -17.0 |
| EURUSD | short | 2005-05-23 | 2005-05-24 | 1 | 1 | zamknięta | czas | 1.2 |
| EURUSD | short | 2005-05-24 | 2005-05-25 | 1 | 1 | zamknięta | czas | -31.9 |
| EURUSD | short | 2005-05-25 | 2005-05-26 | 1 | 1 | zamknięta | czas | 86.1 |
| EURUSD | short | 2005-05-26 | 2005-05-27 | 1 | 1 | zamknięta | czas | -16.9 |
| EURUSD | short | 2005-05-29 | 2005-05-30 | 1 | 1 | zamknięta | czas | 42.1 |
| EURUSD | short | 2005-05-30 | 2005-05-31 | 1 | 1 | zamknięta | czas | 174.2 |
| EURUSD | short | 2005-05-31 | 2005-06-01 | 1 | 1 | zamknięta | czas | 110.1 |
| EURUSD | short | 2005-06-01 | 2005-06-02 | 1 | 1 | zamknięta | czas | -71.8 |
| EURUSD | short | 2005-06-02 | 2005-06-03 | 1 | 1 | zamknięta | czas | 38.0 |
| EURUSD | short | 2005-06-05 | 2005-06-06 | 1 | 1 | zamknięta | czas | -29.8 |
| EURUSD | short | 2005-06-06 | 2005-06-07 | 1 | 1 | zamknięta | czas | -20.9 |
| EURUSD | short | 2005-06-07 | 2005-06-08 | 1 | 1 | zamknięta | czas | 40.1 |
| EURUSD | short | 2005-06-08 | 2005-06-09 | 1 | 1 | zamknięta | czas | 8.1 |
| EURUSD | short | 2005-06-09 | 2005-06-10 | 1 | 1 | zamknięta | czas | 112.2 |
| EURUSD | short | 2005-06-12 | 2005-06-13 | 1 | 1 | zamknięta | czas | -1.9 |
| EURUSD | short | 2005-06-14 | 2005-06-15 | 1 | 1 | zamknięta | czas | -99.9 |
| EURUSD | short | 2005-06-15 | 2005-06-16 | 1 | 1 | zamknięta | czas | 26.1 |
| EURUSD | short | 2005-06-16 | 2005-06-17 | 1 | 1 | zamknięta | czas | -100.8 |
| EURUSD | short | 2005-06-19 | 2005-06-20 | 1 | 1 | zamknięta | czas | 46.1 |
| EURUSD | short | 2005-06-20 | 2005-06-21 | 1 | 1 | zamknięta | czas | -24.0 |
| EURUSD | short | 2005-06-21 | 2005-06-22 | 1 | 1 | zamknięta | czas | 53.1 |
| EURUSD | short | 2005-06-22 | 2005-06-23 | 1 | 1 | zamknięta | czas | 88.2 |
| EURUSD | short | 2005-06-23 | 2005-06-24 | 1 | 1 | zamknięta | czas | -79.0 |
| EURUSD | short | 2005-06-26 | 2005-06-27 | 1 | 1 | zamknięta | czas | -52.9 |
| EURUSD | short | 2005-06-27 | 2005-06-28 | 1 | 1 | zamknięta | czas | 94.2 |
| EURUSD | short | 2005-06-28 | 2005-06-29 | 1 | 1 | zamknięta | czas | -32.0 |
| EURUSD | short | 2005-06-29 | 2005-06-30 | 1 | 1 | zamknięta | czas | 8.2 |
| EURUSD | short | 2005-06-30 | 2005-07-01 | 1 | 1 | zamknięta | czas | 175.1 |
| EURUSD | short | 2005-07-03 | 2005-07-04 | 1 | 1 | zamknięta | czas | 2.1 |
| EURUSD | short | 2005-07-04 | 2005-07-05 | 1 | 1 | zamknięta | czas | -20.9 |
| EURUSD | short | 2005-07-05 | 2005-07-06 | 1 | 1 | zamknięta | czas | -0.9 |
| EURUSD | short | 2005-07-06 | 2005-07-07 | 1 | 1 | zamknięta | czas | -15.9 |
| EURUSD | short | 2005-07-07 | 2005-07-08 | 1 | 1 | zamknięta | czas | -27.9 |
| EURUSD | short | 2005-07-10 | 2005-07-11 | 1 | 1 | zamknięta | czas | -97.8 |
| EURUSD | short | 2005-07-11 | 2005-07-12 | 1 | 1 | zamknięta | czas | -164.9 |
| EURUSD | short | 2005-07-12 | 2005-07-13 | 1 | 1 | zamknięta | czas | 154.1 |
| EURUSD | short | 2005-07-13 | 2005-07-14 | 1 | 1 | zamknięta | czas | -17.8 |
| EURUSD | short | 2005-07-14 | 2005-07-15 | 1 | 1 | zamknięta | czas | 55.0 |
| EURUSD | short | 2005-07-17 | 2005-07-18 | 1 | 1 | zamknięta | czas | -16.9 |
| EURUSD | short | 2005-07-18 | 2005-07-19 | 1 | 1 | zamknięta | czas | 24.0 |
| EURUSD | short | 2005-07-19 | 2005-07-20 | 1 | 1 | zamknięta | czas | -129.9 |
| EURUSD | short | 2005-07-20 | 2005-07-21 | 1 | 1 | zamknięta | czas | -3.9 |
| EURUSD | short | 2005-07-21 | 2005-07-22 | 1 | 1 | zamknięta | czas | 109.2 |
| EURUSD | short | 2005-07-24 | 2005-07-25 | 1 | 1 | zamknięta | czas | -11.9 |
| EURUSD | short | 2005-07-25 | 2005-07-26 | 1 | 1 | zamknięta | czas | 43.2 |
| EURUSD | short | 2005-07-26 | 2005-07-27 | 1 | 1 | zamknięta | czas | -50.9 |
| EURUSD | short | 2005-07-27 | 2005-07-28 | 1 | 1 | zamknięta | czas | -64.0 |
| EURUSD | short | 2005-07-28 | 2005-07-29 | 1 | 1 | zamknięta | czas | 7.2 |
| EURUSD | short | 2005-07-31 | 2005-08-01 | 1 | 1 | zamknięta | czas | -61.9 |
| EURUSD | short | 2005-08-01 | 2005-08-02 | 1 | 1 | zamknięta | czas | -7.9 |
| EURUSD | short | 2005-08-02 | 2005-08-03 | 1 | 1 | zamknięta | czas | -145.9 |
| EURUSD | short | 2005-08-03 | 2005-08-04 | 1 | 1 | zamknięta | czas | -49.9 |
| EURUSD | short | 2005-08-04 | 2005-08-05 | 1 | 1 | zamknięta | czas | 47.1 |
| EURUSD | short | 2005-08-07 | 2005-08-08 | 1 | 1 | zamknięta | czas | -16.9 |
| EURUSD | short | 2005-08-08 | 2005-08-09 | 1 | 1 | zamknięta | czas | -24.9 |
| EURUSD | short | 2005-08-09 | 2005-08-10 | 1 | 1 | zamknięta | czas | -10.9 |
| EURUSD | short | 2005-08-10 | 2005-08-11 | 1 | 1 | zamknięta | czas | -84.9 |
| EURUSD | short | 2005-08-11 | 2005-08-12 | 1 | 1 | zamknięta | czas | 16.0 |
| EURUSD | short | 2005-08-14 | 2005-08-15 | 1 | 1 | zamknięta | czas | 83.2 |
| EURUSD | short | 2005-08-15 | 2005-08-16 | 1 | 1 | zamknięta | czas | 19.1 |
| EURUSD | short | 2005-08-16 | 2005-08-17 | 1 | 1 | zamknięta | czas | 71.0 |
| EURUSD | short | 2005-08-17 | 2005-08-18 | 1 | 1 | zamknięta | czas | 94.2 |
| EURUSD | short | 2005-08-18 | 2005-08-19 | 1 | 1 | zamknięta | czas | 13.0 |
| EURUSD | short | 2005-08-21 | 2005-08-22 | 1 | 1 | zamknięta | czas | -63.9 |
| EURUSD | short | 2005-08-22 | 2005-08-23 | 1 | 1 | zamknięta | czas | -3.0 |
| EURUSD | short | 2005-08-23 | 2005-08-24 | 1 | 1 | zamknięta | czas | -39.8 |
| EURUSD | short | 2005-08-24 | 2005-08-25 | 1 | 1 | zamknięta | czas | -30.9 |
| EURUSD | short | 2005-08-25 | 2005-08-26 | 1 | 1 | zamknięta | czas | -3.9 |
| EURUSD | short | 2005-08-28 | 2005-08-29 | 1 | 1 | zamknięta | czas | 69.1 |
| EURUSD | short | 2005-08-29 | 2005-08-30 | 1 | 1 | zamknięta | czas | 19.1 |
| EURUSD | short | 2005-08-30 | 2005-08-31 | 1 | 1 | zamknięta | czas | -123.0 |
| EURUSD | short | 2005-08-31 | 2005-09-01 | 1 | 1 | zamknięta | czas | -152.8 |
| EURUSD | short | 2005-09-01 | 2005-09-02 | 1 | 1 | zamknięta | czas | -49.9 |
| EURUSD | short | 2005-09-04 | 2005-09-05 | 1 | 1 | zamknięta | czas | 11.2 |
| EURUSD | short | 2005-09-05 | 2005-09-06 | 1 | 1 | zamknięta | czas | 68.1 |
| EURUSD | short | 2005-09-06 | 2005-09-07 | 1 | 1 | zamknięta | czas | 41.0 |
| EURUSD | short | 2005-09-07 | 2005-09-08 | 1 | 1 | zamknięta | czas | 20.2 |
| EURUSD | short | 2005-09-08 | 2005-09-09 | 1 | 1 | zamknięta | czas | -8.0 |
| EURUSD | short | 2005-09-11 | 2005-09-12 | 1 | 1 | zamknięta | czas | 111.1 |
| EURUSD | short | 2005-09-12 | 2005-09-13 | 1 | 1 | zamknięta | czas | 12.1 |
| EURUSD | short | 2005-09-13 | 2005-09-14 | 1 | 1 | zamknięta | czas | -2.0 |
| EURUSD | short | 2005-09-14 | 2005-09-15 | 1 | 1 | zamknięta | czas | 41.2 |
| EURUSD | short | 2005-09-15 | 2005-09-16 | 1 | 1 | zamknięta | czas | 81.0 |
| EURUSD | short | 2005-09-18 | 2005-09-19 | 1 | 1 | zamknięta | czas | 14.1 |
| EURUSD | short | 2005-09-19 | 2005-09-20 | 1 | 1 | zamknięta | czas | 19.1 |
| EURUSD | short | 2005-09-21 | 2005-09-22 | 1 | 1 | zamknięta | czas | 11.1 |
| EURUSD | short | 2005-09-22 | 2005-09-23 | 1 | 1 | zamknięta | czas | 128.0 |
| EURUSD | short | 2005-09-25 | 2005-09-26 | 1 | 1 | zamknięta | czas | -48.8 |
| EURUSD | short | 2005-09-26 | 2005-09-27 | 1 | 1 | zamknięta | czas | 55.1 |
| EURUSD | short | 2005-09-27 | 2005-09-28 | 1 | 1 | zamknięta | czas | -45.0 |
| EURUSD | short | 2005-09-28 | 2005-09-29 | 1 | 1 | zamknięta | czas | 41.1 |
| EURUSD | short | 2005-09-29 | 2005-09-30 | 1 | 1 | zamknięta | czas | -1.9 |
| EURUSD | short | 2005-10-02 | 2005-10-03 | 1 | 1 | zamknięta | czas | 106.1 |
| EURUSD | short | 2005-10-03 | 2005-10-04 | 1 | 1 | zamknięta | czas | -5.9 |
| EURUSD | short | 2005-10-05 | 2005-10-06 | 1 | 1 | zamknięta | czas | -159.9 |
| EURUSD | short | 2005-10-06 | 2005-10-07 | 1 | 1 | zamknięta | czas | 52.0 |
| EURUSD | short | 2005-10-09 | 2005-10-10 | 1 | 1 | zamknięta | czas | 62.2 |
| EURUSD | short | 2005-10-10 | 2005-10-11 | 1 | 1 | zamknięta | czas | 68.1 |
| EURUSD | short | 2005-10-11 | 2005-10-12 | 1 | 1 | zamknięta | czas | -42.0 |
| EURUSD | short | 2005-10-12 | 2005-10-13 | 1 | 1 | zamknięta | czas | 7.0 |
| EURUSD | short | 2005-10-13 | 2005-10-14 | 1 | 1 | zamknięta | czas | -53.8 |
| EURUSD | short | 2005-10-16 | 2005-10-17 | 1 | 1 | zamknięta | czas | 56.1 |
| EURUSD | short | 2005-10-17 | 2005-10-18 | 1 | 1 | zamknięta | czas | 59.7 |
| EURUSD | short | 2005-10-18 | 2005-10-19 | 1 | 1 | zamknięta | czas | -19.5 |
| EURUSD | short | 2005-10-19 | 2005-10-20 | 1 | 1 | zamknięta | czas | -48.8 |
| EURUSD | short | 2005-10-20 | 2005-10-21 | 1 | 1 | zamknięta | czas | 73.0 |
| EURUSD | short | 2005-10-23 | 2005-10-24 | 1 | 1 | zamknięta | czas | -31.9 |
| EURUSD | short | 2005-10-24 | 2005-10-25 | 1 | 1 | zamknięta | czas | -135.8 |
| EURUSD | short | 2005-10-25 | 2005-10-26 | 1 | 1 | zamknięta | czas | 52.0 |
| EURUSD | short | 2005-10-26 | 2005-10-27 | 1 | 1 | zamknięta | czas | -88.8 |
| EURUSD | short | 2005-10-27 | 2005-10-28 | 1 | 1 | zamknięta | czas | 80.0 |
| EURUSD | short | 2005-10-31 | 2005-11-01 | 1 | 1 | zamknięta | czas | 75.2 |
| EURUSD | short | 2005-11-01 | 2005-11-02 | 1 | 1 | zamknięta | czas | -34.9 |
| EURUSD | short | 2005-11-02 | 2005-11-03 | 1 | 1 | zamknięta | czas | -44.9 |
| EURUSD | short | 2005-11-03 | 2005-11-04 | 1 | 1 | zamknięta | czas | 119.0 |
| EURUSD | short | 2005-11-04 | 2005-11-05 | 1 | 1 | zamknięta | czas | 139.2 |
| EURUSD | short | 2005-11-07 | 2005-11-08 | 1 | 1 | zamknięta | czas | 16.1 |
| EURUSD | short | 2005-11-08 | 2005-11-09 | 1 | 1 | zamknięta | czas | 20.1 |
| EURUSD | short | 2005-11-09 | 2005-11-10 | 1 | 1 | zamknięta | czas | -6.9 |
| EURUSD | short | 2005-11-10 | 2005-11-11 | 1 | 1 | zamknięta | czas | 99.0 |
| EURUSD | short | 2005-11-11 | 2005-11-12 | 1 | 1 | zamknięta | czas | -61.9 |
| EURUSD | short | 2005-11-14 | 2005-11-15 | 1 | 1 | zamknięta | czas | 43.1 |
| EURUSD | short | 2005-11-15 | 2005-11-16 | 1 | 1 | zamknięta | czas | -40.0 |
| EURUSD | short | 2005-11-16 | 2005-11-17 | 1 | 1 | zamknięta | czas | 49.1 |
| EURUSD | short | 2005-11-17 | 2005-11-18 | 1 | 1 | zamknięta | czas | -68.8 |
| EURUSD | short | 2005-11-18 | 2005-11-19 | 1 | 1 | zamknięta | czas | -26.9 |
| EURUSD | short | 2005-11-21 | 2005-11-22 | 1 | 1 | zamknięta | czas | 38.1 |
| EURUSD | short | 2005-11-22 | 2005-11-23 | 1 | 1 | zamknięta | czas | -77.4 |
| EURUSD | short | 2005-11-23 | 2005-11-24 | 1 | 1 | zamknięta | czas | 1.6 |
| EURUSD | short | 2005-11-24 | 2005-11-25 | 1 | 1 | zamknięta | czas | 29.6 |
| EURUSD | short | 2005-11-25 | 2005-11-26 | 1 | 1 | zamknięta | czas | 69.6 |
| EURUSD | short | 2005-11-28 | 2005-11-29 | 1 | 1 | zamknięta | czas | -141.9 |
| EURUSD | short | 2005-11-29 | 2005-11-30 | 1 | 1 | zamknięta | czas | 81.1 |
| EURUSD | short | 2005-12-01 | 2005-12-02 | 1 | 1 | zamknięta | czas | 56.0 |
| EURUSD | short | 2005-12-02 | 2005-12-03 | 1 | 1 | zamknięta | czas | 21.1 |
| EURUSD | short | 2005-12-05 | 2005-12-06 | 1 | 1 | zamknięta | czas | -66.4 |
| EURUSD | short | 2005-12-06 | 2005-12-07 | 1 | 1 | zamknięta | czas | -13.8 |
| EURUSD | short | 2005-12-07 | 2005-12-08 | 1 | 1 | zamknięta | czas | 78.6 |
| EURUSD | short | 2005-12-08 | 2005-12-09 | 1 | 1 | zamknięta | czas | -100.9 |
| EURUSD | short | 2005-12-09 | 2005-12-10 | 1 | 1 | zamknięta | czas | 23.1 |
| EURUSD | short | 2005-12-12 | 2005-12-13 | 1 | 1 | zamknięta | czas | -157.9 |
| EURUSD | short | 2005-12-13 | 2005-12-14 | 1 | 1 | zamknięta | czas | 2.1 |
| EURUSD | short | 2005-12-14 | 2005-12-15 | 1 | 1 | zamknięta | czas | -32.0 |
| EURUSD | short | 2005-12-15 | 2005-12-16 | 1 | 1 | zamknięta | czas | 11.1 |
| EURUSD | short | 2005-12-16 | 2005-12-17 | 1 | 1 | zamknięta | czas | -68.9 |
| EURUSD | short | 2005-12-19 | 2005-12-20 | 1 | 1 | zamknięta | czas | 27.1 |
| EURUSD | short | 2005-12-20 | 2005-12-21 | 1 | 1 | zamknięta | czas | 129.0 |
| EURUSD | short | 2005-12-21 | 2005-12-22 | 1 | 1 | zamknięta | czas | 46.2 |
| EURUSD | short | 2005-12-22 | 2005-12-23 | 1 | 1 | zamknięta | czas | -42.9 |
| EURUSD | short | 2005-12-23 | 2005-12-24 | 1 | 1 | zamknięta | czas | 10.1 |
| EURUSD | short | 2005-12-26 | 2005-12-27 | 1 | 1 | zamknięta | czas | 24.1 |
| EURUSD | short | 2005-12-27 | 2005-12-28 | 1 | 1 | zamknięta | czas | -18.9 |
| EURUSD | short | 2005-12-28 | 2005-12-29 | 1 | 1 | zamknięta | czas | 5.0 |
| EURUSD | short | 2005-12-29 | 2005-12-30 | 1 | 1 | zamknięta | czas | -0.9 |
| EURUSD | short | 2005-12-30 | 2005-12-31 | 1 | 1 | zamknięta | czas | 6.1 |
| EURUSD | short | 2006-01-02 | 2006-01-03 | 1 | 1 | zamknięta | czas | 24.1 |
| EURUSD | short | 2006-01-03 | 2006-01-04 | 1 | 1 | zamknięta | czas | -214.9 |
| EURUSD | short | 2006-01-04 | 2006-01-05 | 1 | 1 | zamknięta | czas | -84.0 |
| EURUSD | short | 2006-01-05 | 2006-01-06 | 1 | 1 | zamknięta | czas | 8.0 |
| EURUSD | short | 2006-01-06 | 2006-01-07 | 1 | 1 | zamknięta | czas | -35.9 |
| EURUSD | short | 2006-01-09 | 2006-01-10 | 1 | 1 | zamknięta | czas | 64.2 |
| EURUSD | short | 2006-01-10 | 2006-01-11 | 1 | 1 | zamknięta | czas | 10.0 |
| EURUSD | short | 2006-01-11 | 2006-01-12 | 1 | 1 | zamknięta | czas | -76.9 |
| EURUSD | short | 2006-01-12 | 2006-01-13 | 1 | 1 | zamknięta | czas | 99.1 |
| EURUSD | short | 2006-01-13 | 2006-01-14 | 1 | 1 | zamknięta | czas | -125.8 |
| EURUSD | short | 2006-01-16 | 2006-01-17 | 1 | 1 | zamknięta | czas | 47.2 |
| EURUSD | short | 2006-01-17 | 2006-01-18 | 1 | 1 | zamknięta | czas | 7.0 |
| EURUSD | short | 2006-01-18 | 2006-01-19 | 1 | 1 | zamknięta | czas | 1.2 |
| EURUSD | short | 2006-01-19 | 2006-01-20 | 1 | 1 | zamknięta | czas | 16.1 |
| EURUSD | short | 2006-01-20 | 2006-01-21 | 1 | 1 | zamknięta | czas | -78.9 |
| EURUSD | short | 2006-01-23 | 2006-01-24 | 1 | 1 | zamknięta | czas | -137.0 |
| EURUSD | short | 2006-01-24 | 2006-01-25 | 1 | 1 | zamknięta | czas | 37.1 |
| EURUSD | long | 2006-01-25 | 2006-01-26 | 1 | 1 | zamknięta | czas | -20.9 |
| EURUSD | long | 2006-01-26 | 2006-01-27 | 1 | 1 | zamknięta | czas | -31.0 |
| EURUSD | long | 2006-01-27 | 2006-01-28 | 1 | 1 | zamknięta | czas | -110.9 |
| EURUSD | long | 2006-01-30 | 2006-01-31 | 1 | 1 | zamknięta | czas | -20.8 |
| EURUSD | long | 2006-01-31 | 2006-02-01 | 1 | 1 | zamknięta | czas | 62.1 |
| EURUSD | short | 2006-02-01 | 2006-02-02 | 1 | 1 | zamknięta | czas | 82.2 |
| EURUSD | short | 2006-02-02 | 2006-02-03 | 1 | 1 | zamknięta | czas | -19.0 |
| EURUSD | short | 2006-02-03 | 2006-02-04 | 1 | 1 | zamknięta | czas | 52.2 |
| EURUSD | short | 2006-02-06 | 2006-02-07 | 1 | 1 | zamknięta | czas | 69.0 |
| EURUSD | short | 2006-02-07 | 2006-02-08 | 1 | 1 | zamknięta | czas | -31.9 |
| EURUSD | short | 2006-02-08 | 2006-02-09 | 1 | 1 | zamknięta | czas | 25.1 |
| EURUSD | short | 2006-02-09 | 2006-02-10 | 1 | 1 | zamknięta | czas | -35.9 |
| EURUSD | short | 2006-02-10 | 2006-02-11 | 1 | 1 | zamknięta | czas | 99.2 |
| EURUSD | short | 2006-02-13 | 2006-02-14 | 1 | 1 | zamknięta | czas | -12.0 |
| EURUSD | short | 2006-02-14 | 2006-02-15 | 1 | 1 | zamknięta | czas | -4.9 |
| EURUSD | short | 2006-02-15 | 2006-02-16 | 1 | 1 | zamknięta | czas | 33.1 |
| EURUSD | short | 2006-02-16 | 2006-02-17 | 1 | 1 | zamknięta | czas | -26.9 |
| EURUSD | short | 2006-02-17 | 2006-02-18 | 1 | 1 | zamknięta | czas | -42.3 |
| EURUSD | short | 2006-02-20 | 2006-02-21 | 1 | 1 | zamknięta | czas | 13.5 |
| EURUSD | short | 2006-02-21 | 2006-02-22 | 1 | 1 | zamknięta | czas | 14.2 |
| EURUSD | short | 2006-02-22 | 2006-02-23 | 1 | 1 | zamknięta | czas | 6.1 |
| EURUSD | short | 2006-02-23 | 2006-02-24 | 1 | 1 | zamknięta | czas | -12.0 |
| EURUSD | short | 2006-02-24 | 2006-02-25 | 1 | 1 | zamknięta | czas | 79.2 |
| EURUSD | short | 2006-02-27 | 2006-02-28 | 1 | 1 | zamknięta | czas | -6.0 |
| EURUSD | short | 2006-02-28 | 2006-03-01 | 1 | 1 | zamknięta | czas | -80.9 |
| EURUSD | short | 2006-03-01 | 2006-03-02 | 1 | 1 | zamknięta | czas | 9.6 |
| EURUSD | short | 2006-03-02 | 2006-03-03 | 1 | 1 | zamknięta | czas | -119.4 |
| EURUSD | short | 2006-03-03 | 2006-03-04 | 1 | 1 | zamknięta | czas | -50.4 |
| EURUSD | short | 2006-03-06 | 2006-03-07 | 1 | 1 | zamknięta | czas | 65.6 |
| EURUSD | short | 2006-03-07 | 2006-03-08 | 1 | 1 | zamknięta | czas | 127.0 |
| EURUSD | short | 2006-03-08 | 2006-03-09 | 1 | 1 | zamknięta | czas | -36.9 |
| EURUSD | short | 2006-03-09 | 2006-03-10 | 1 | 1 | zamknięta | czas | 26.2 |
| EURUSD | short | 2006-03-10 | 2006-03-11 | 1 | 1 | zamknięta | czas | -22.9 |
| EURUSD | short | 2006-03-13 | 2006-03-14 | 1 | 1 | zamknięta | czas | -45.0 |
| EURUSD | short | 2006-03-14 | 2006-03-15 | 1 | 1 | zamknięta | czas | -50.9 |
| EURUSD | short | 2006-03-15 | 2006-03-16 | 1 | 1 | zamknięta | czas | -55.9 |
| EURUSD | short | 2006-03-16 | 2006-03-17 | 1 | 1 | zamknięta | czas | -104.8 |
| EURUSD | short | 2006-03-17 | 2006-03-18 | 1 | 1 | zamknięta | czas | -5.9 |
| EURUSD | short | 2006-03-20 | 2006-03-21 | 1 | 1 | zamknięta | czas | 22.1 |
| EURUSD | short | 2006-03-21 | 2006-03-22 | 1 | 1 | zamknięta | czas | 51.2 |
| EURUSD | long | 2006-03-22 | 2006-03-23 | 1 | 1 | zamknięta | czas | -25.9 |
| EURUSD | long | 2006-03-23 | 2006-03-24 | 1 | 1 | zamknięta | czas | -113.8 |
| EURUSD | short | 2006-03-24 | 2006-03-25 | 1 | 1 | zamknięta | czas | -65.8 |
| EURUSD | short | 2006-03-26 | 2006-03-27 | 1 | 1 | zamknięta | czas | 17.0 |
| EURUSD | short | 2006-03-27 | 2006-03-28 | 1 | 1 | zamknięta | czas | 5.2 |
| EURUSD | short | 2006-03-28 | 2006-03-29 | 1 | 1 | zamknięta | czas | -21.8 |
| EURUSD | short | 2006-03-29 | 2006-03-30 | 1 | 1 | zamknięta | czas | -138.9 |
| EURUSD | short | 2006-03-30 | 2006-03-31 | 1 | 1 | zamknięta | czas | 46.0 |
| EURUSD | short | 2006-04-02 | 2006-04-03 | 1 | 1 | zamknięta | czas | -16.8 |
| EURUSD | short | 2006-04-03 | 2006-04-04 | 1 | 1 | zamknięta | czas | -125.0 |
| EURUSD | long | 2006-04-04 | 2006-04-05 | 1 | 1 | zamknięta | czas | 24.1 |
| EURUSD | long | 2006-04-05 | 2006-04-06 | 1 | 1 | zamknięta | czas | -72.0 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 5584); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 0.39 pips/transakcję, percentyl **85.0** (losowe: 5%=-2.80, mediana=-0.83, 95%=1.14).

- **Deflated Sharpe Ratio**: 0.030 (Sharpe na transakcję 0.014, próg przy 56 próbach 0.045).

- **PBO** (CSCV, 16 bloków, 56 wariantów): 0.247 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 3459 transakcji, śr. -0.37 pips, -0.00 R.

- **Bootstrap 95%** średnich pipsów: całość [-1.97; 2.82], OOS [-3.01; 1.38].

- **Spread**: ×1 0.39, ×1,5 -0.06, ×2 -0.51 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 1.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -0.11, 1 pips: -0.61 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"   # świece dzienne Yahoo (D-058): wejście na open dnia, wyjście na zamknięciu tego dnia = 24 h

HYPOTHESIS = """Na EUR/USD kierunek krótkiego impetu może przenosić się na następny dzień: jeśli RSI albo EMA rośnie,
kolejny dzień częściej jest wzrostowy, jeśli spada — spadkowy. Codziennie jedna transakcja na 24 h (open dnia → zamknięcie
dnia), kierunek z jednego wskaźnika: RSI(n) rosnące → long, malejące → short; albo EMA(n) rosnąca → long, malejąca → short.
„Rośnie” = wartość dziś wyższa niż k dni temu. Silnik liczy wszystkie kombinacje n × k na tych samych zasadach wyjścia;
wybór najlepszej tylko po IS, a kara za liczbę prób jest w DSR."""

EXITS = [{"kind": "time", "n": 1, "cap": 1}]   # wyjście na zamknięciu dnia wejścia — dokładnie 24 h (życzenie Michała)
EXPLORE = False   # eksploracja zmienia wyjścia i filtruje dni — tu reguła jest stała: codziennie, 24 h

RSI_N = [2, 3, 5, 7, 9, 14, 21]
EMA_N = [5, 10, 20, 30, 50, 100, 200]
K = [1, 2, 3, 5]                               # „rośnie” = dziś wyżej niż k dni temu
CONFIGS = [("rsi", n, k) for n in RSI_N for k in K] + [("ema", n, k) for n in EMA_N for k in K]
PARAMS = {"cfg": list(range(len(CONFIGS)))}    # 28 wersji RSI + 28 wersji EMA = 56


def signals(df, p, ind):
    if df.attrs.get("pair") != "EURUSD":       # tylko EUR/USD
        return pd.Series(0, index=df.index, dtype="int8")
    kind, n, k = CONFIGS[p["cfg"]]
    x = ind.rsi(df.close, n) if kind == "rsi" else ind.ema(df.close, n)
    up, down = ind.rising(x, k), ind.falling(x, k)   # codziennie jedno z dwóch (poza rzadkim „bez zmiany”)
    return up.astype("int8") - down.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
