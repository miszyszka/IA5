# Raport strategii: RSI - Dzienne v.1

Run `20261112-203852` · silnik 0.13.0 · kod `39524d12265c9ee1` · dane `c9068b7a34535dbe`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 9.67 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✘ | 0.62 |
| DSR ≥ 0,95 | ✔ | 1.00 |
| dodatni przy spreadzie ×1,5 | ✔ | 14.77 |

## Hipoteza

Wersja 2 strategii RSI na D1, z diagnozy stratnych i zyskownych wejść wersji 1 (research/rsi_d1/README.md).
Straty łączyło: pierwszy dzień wyprzedania (spadek często trwa dalej), dzień-szok z bardzo szerokim zakresem i głęboki krach
przeciw trendowi. Zyski łączyło: trend 200-dniowy po stronie transakcji i KOLEJNY dzień wyprzedania z rzędu — sprzedający
się wyczerpują, a trend wraca w 3–4 dni. Wzmacniamy to: wejście dopiero od 2. (albo 3.) dnia z rzędu z RSI za progiem,
nad SMA200 (short lustrzanie pod), bez dni-szoków; wyjście po 3–5 dniach na zamknięciu. Konfiguracje wybrane na IS:
odporne w obu połowach IS (1996–2011, 2012–2019) i na obu wersjach zamknięć D1 Yahoo (zob. D-068 — zamknięcia D1 Yahoo).

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

- Pominięte sygnały, średnio na wariant: 71 (limit otwartych pozycji w parze), 0.4 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, max 4 | cfg=0 | 902 | 0.15 | 18.05 | 55.1 | 375 | 0.10 | 9.67 |
| 2 | poziomy TP/SL ze strategii, max 4 | cfg=3 | 902 | 0.15 | 18.05 | 55.1 | 375 | 0.10 | 9.67 |
| 3 | poziomy TP/SL ze strategii, max 4 | cfg=1 | 914 | 0.15 | 17.60 | 55.0 | 376 | 0.10 | 10.17 |
| 4 | poziomy TP/SL ze strategii, max 5 | cfg=0 | 864 | 0.15 | 18.92 | 54.1 | 359 | 0.11 | 11.94 |
| 5 | poziomy TP/SL ze strategii, max 5 | cfg=3 | 864 | 0.15 | 18.92 | 54.1 | 359 | 0.11 | 11.94 |
| 6 | poziomy TP/SL ze strategii, max 4 | cfg=8 | 776 | 0.15 | 16.69 | 53.2 | 339 | 0.10 | 11.34 |
| 7 | poziomy TP/SL ze strategii, max 5 | cfg=1 | 875 | 0.15 | 18.62 | 53.9 | 360 | 0.11 | 11.72 |
| 8 | poziomy TP/SL ze strategii, max 4 | cfg=2 | 877 | 0.15 | 16.99 | 54.8 | 366 | 0.11 | 11.89 |
| 9 | poziomy TP/SL ze strategii, max 4 | cfg=7 | 751 | 0.15 | 16.14 | 53.1 | 333 | 0.09 | 10.83 |
| 10 | poziomy TP/SL ze strategii, max 5 | cfg=2 | 844 | 0.14 | 18.18 | 53.8 | 352 | 0.12 | 13.62 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, max 4 (cfg=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 118 | 19.7 | 2 321.8 | 56.8 |
| EURGBP | 150 | 19.8 | 2 971.5 | 54.0 |
| EURJPY | 142 | -0.0 | -5.3 | 51.4 |
| EURUSD | 154 | 2.0 | 302.4 | 56.5 |
| GBPUSD | 161 | 42.7 | 6 876.3 | 58.4 |
| USDCAD | 181 | 17.9 | 3 236.5 | 52.5 |
| USDCHF | 174 | 2.8 | 478.5 | 51.1 |
| USDJPY | 197 | 18.9 | 3 725.8 | 55.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 1998 | 8 | -15.2 | -121.2 | 62.5 |
| 1999 | 8 | 33.6 | 268.8 | 50.0 |
| 2000 | 13 | -12.9 | -167.7 | 38.5 |
| 2001 | 8 | -1.8 | -14.5 | 75.0 |
| 2002 | 20 | 11.8 | 235.2 | 75.0 |
| 2003 | 16 | 48.6 | 778.4 | 75.0 |
| 2004 | 27 | -18.9 | -509.0 | 40.7 |
| 2005 | 88 | 32.4 | 2 850.8 | 64.8 |
| 2006 | 48 | 51.4 | 2 468.8 | 66.7 |
| 2007 | 34 | 69.2 | 2 351.3 | 76.5 |
| 2008 | 38 | 81.4 | 3 092.0 | 71.1 |
| 2009 | 78 | 7.9 | 612.5 | 55.1 |
| 2010 | 66 | -7.6 | -499.5 | 42.4 |
| 2011 | 41 | -8.6 | -351.6 | 48.8 |
| 2012 | 46 | -26.1 | -1 199.5 | 37.0 |
| 2013 | 57 | -4.6 | -259.6 | 45.6 |
| 2014 | 63 | 9.0 | 564.2 | 39.7 |
| 2015 | 59 | 5.7 | 333.6 | 55.9 |
| 2016 | 78 | 71.9 | 5 605.2 | 62.8 |
| 2017 | 54 | 2.6 | 140.0 | 46.3 |
| 2018 | 42 | -10.0 | -420.4 | 54.8 |
| 2019 | 45 | 7.2 | 324.4 | 51.1 |
| 2020 | 50 | 26.7 | 1 335.2 | 64.0 |
| 2021 | 48 | 17.1 | 819.3 | 58.3 |
| 2022 | 50 | 72.1 | 3 606.6 | 78.0 |
| 2023 | 53 | -25.7 | -1 363.7 | 30.2 |
| 2024 | 48 | -69.1 | -3 315.9 | 29.2 |
| 2025 | 44 | 36.3 | 1 599.1 | 68.2 |
| 2026 | 47 | 24.4 | 1 144.7 | 51.1 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 902 | 18.1 | 16 283.0 | 55.1 |
| OOS | 375 | 9.7 | 3 624.5 | 52.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 16 778 | 67.8 | 1.8 | -9.5 | -13.0 | 0.56 | 0 |
| 2.0% | 27 005 | 170.0 | 3.5 | -18.3 | -25.3 | 0.55 | 0 |
| 3.0% | 41 705 | 317.1 | 5.1 | -27.1 | -37.0 | 0.54 | 0 |
| 5.0% | 87 751 | 777.5 | 7.8 | -45.5 | -58.6 | 0.52 | 0 |

### Czas trwania transakcji i pozycje otwarte (D-062)

Dni = dni kalendarzowe od wejścia (open świecy) do wyjścia. Pozycja **OTWARTA** nie zamknęła się do końca danych (2026-11-04): jej „wyjście” to wycena po ostatnim close, a dni liczą się do tej daty. Zamknięte: **1277**, otwarte: **0** (razem 1277).

| grupa | transakcje | min | mediana | średnia | p90 | max | śr. pips netto | suma pips netto |
|---|---|---|---|---|---|---|---|---|
| zamknięte | 1277 | 4 | 6 | 5 | 6 | 8 | 15.6 | 19 908 |
| OTWARTE na koniec danych | 0 | — | — | — | — | — | — | — |
| wszystkie | 1277 | 4 | 6 | 5 | 6 | 8 | 15.6 | 19 908 |

| para | kier. | wejście | wyjście / stan na | dni | dni handlu | status | powód | pips netto |
|---|---|---|---|---|---|---|---|---|
| USDJPY | long | 1998-01-22 | 1998-01-28 | 6 | 4 | zamknięta | czas | -201.4 |
| USDJPY | long | 1998-01-23 | 1998-01-29 | 6 | 4 | zamknięta | czas | -247.4 |
| USDJPY | long | 1998-01-29 | 1998-02-04 | 6 | 4 | zamknięta | czas | 70.6 |
| USDJPY | long | 1998-02-06 | 1998-02-12 | 6 | 4 | zamknięta | czas | 4.6 |
| USDJPY | short | 1998-11-11 | 1998-11-17 | 6 | 4 | zamknięta | czas | 156.6 |
| USDJPY | short | 1998-11-12 | 1998-11-18 | 6 | 4 | zamknięta | czas | 77.6 |
| USDJPY | short | 1998-11-13 | 1998-11-19 | 6 | 4 | zamknięta | czas | -26.4 |
| USDJPY | short | 1999-02-18 | 1999-02-24 | 6 | 4 | zamknięta | czas | -209.4 |
| USDJPY | short | 1999-02-19 | 1999-02-25 | 6 | 4 | zamknięta | czas | -171.4 |
| USDJPY | short | 1999-02-24 | 1999-03-02 | 6 | 4 | zamknięta | czas | 102.6 |
| USDJPY | short | 1999-02-25 | 1999-03-03 | 6 | 4 | zamknięta | czas | 141.6 |
| USDJPY | short | 1999-03-30 | 1999-04-05 | 6 | 4 | zamknięta | czas | -129.4 |
| USDJPY | short | 2000-01-12 | 2000-01-18 | 6 | 4 | zamknięta | czas | 110.6 |
| USDJPY | short | 2000-02-03 | 2000-02-09 | 6 | 4 | zamknięta | czas | -136.4 |
| USDJPY | short | 2000-02-09 | 2000-02-15 | 6 | 4 | zamknięta | czas | 55.6 |
| EURGBP | short | 2000-02-24 | 2000-03-01 | 6 | 4 | zamknięta | czas | 131.3 |
| USDJPY | long | 2000-08-24 | 2000-08-30 | 6 | 4 | zamknięta | czas | -26.4 |
| EURGBP | short | 2000-11-03 | 2000-11-09 | 6 | 4 | zamknięta | czas | -69.7 |
| USDJPY | long | 2001-05-24 | 2001-05-30 | 6 | 4 | zamknięta | czas | 34.6 |
| EURGBP | short | 2001-07-18 | 2001-07-24 | 6 | 4 | zamknięta | czas | 3.3 |
| USDJPY | long | 2001-08-16 | 2001-08-22 | 6 | 4 | zamknięta | czas | 17.6 |
| USDJPY | short | 2001-10-02 | 2001-10-08 | 6 | 4 | zamknięta | czas | 81.6 |
| USDJPY | short | 2001-10-03 | 2001-10-09 | 6 | 4 | zamknięta | czas | 38.6 |
| USDJPY | short | 2001-10-04 | 2001-10-10 | 6 | 4 | zamknięta | czas | 22.6 |
| USDJPY | long | 2002-04-10 | 2002-04-16 | 6 | 4 | zamknięta | czas | 42.6 |
| USDJPY | long | 2002-04-25 | 2002-05-01 | 6 | 4 | zamknięta | czas | -149.4 |
| EURGBP | long | 2002-07-24 | 2002-07-30 | 6 | 4 | zamknięta | czas | -87.7 |
| EURGBP | long | 2002-07-30 | 2002-08-05 | 6 | 4 | zamknięta | czas | 27.3 |
| USDJPY | short | 2002-07-30 | 2002-08-05 | 6 | 4 | zamknięta | czas | 61.6 |
| EURGBP | long | 2002-07-31 | 2002-08-06 | 6 | 4 | zamknięta | czas | 26.3 |
| EURGBP | long | 2002-09-10 | 2002-09-16 | 6 | 4 | zamknięta | czas | 18.3 |
| EURGBP | long | 2002-09-11 | 2002-09-17 | 6 | 4 | zamknięta | czas | 36.3 |
| USDJPY | short | 2002-09-17 | 2002-09-23 | 6 | 4 | zamknięta | czas | -182.4 |
| USDJPY | short | 2002-11-21 | 2002-11-27 | 6 | 4 | zamknięta | czas | 121.6 |
| USDJPY | short | 2002-11-22 | 2002-11-28 | 6 | 4 | zamknięta | czas | 28.6 |
| USDJPY | short | 2003-03-21 | 2003-03-27 | 6 | 4 | zamknięta | czas | 31.6 |
| EURGBP | long | 2003-06-24 | 2003-06-30 | 6 | 4 | zamknięta | czas | 41.3 |
| EURGBP | long | 2003-06-25 | 2003-07-01 | 6 | 4 | zamknięta | czas | 55.3 |
| EURGBP | long | 2003-06-26 | 2003-07-02 | 6 | 4 | zamknięta | czas | 24.3 |
| EURGBP | long | 2003-08-21 | 2003-08-27 | 6 | 4 | zamknięta | czas | -5.7 |
| EURJPY | short | 2003-11-20 | 2003-11-26 | 6 | 4 | zamknięta | czas | 88.9 |
| EURJPY | short | 2003-11-21 | 2003-11-27 | 6 | 4 | zamknięta | czas | -32.1 |
| USDJPY | short | 2004-02-20 | 2004-02-26 | 6 | 4 | zamknięta | czas | -204.4 |
| USDJPY | short | 2004-02-27 | 2004-03-04 | 6 | 4 | zamknięta | czas | -58.4 |
| USDJPY | short | 2004-03-04 | 2004-03-10 | 6 | 4 | zamknięta | czas | -135.4 |
| USDJPY | short | 2004-03-05 | 2004-03-11 | 6 | 4 | zamknięta | czas | 33.6 |
| EURGBP | short | 2004-03-11 | 2004-03-17 | 6 | 4 | zamknięta | czas | 15.3 |
| EURGBP | short | 2004-03-12 | 2004-03-18 | 6 | 4 | zamknięta | czas | 86.3 |
| USDJPY | short | 2004-04-22 | 2004-04-28 | 6 | 4 | zamknięta | czas | -61.4 |
| USDCAD | long | 2004-06-30 | 2004-07-06 | 6 | 4 | zamknięta | czas | -68.0 |
| USDCAD | long | 2004-07-01 | 2004-07-07 | 6 | 4 | zamknięta | czas | -100.0 |
| EURGBP | short | 2004-08-10 | 2004-08-16 | 6 | 4 | zamknięta | czas | -21.7 |
| EURGBP | short | 2004-08-18 | 2004-08-24 | 6 | 4 | zamknięta | czas | 19.3 |
| USDJPY | long | 2004-08-19 | 2004-08-25 | 6 | 4 | zamknięta | czas | 71.6 |
| EURGBP | long | 2004-12-02 | 2004-12-08 | 6 | 4 | zamknięta | czas | -1.7 |
| EURGBP | long | 2004-12-03 | 2004-12-09 | 6 | 4 | zamknięta | czas | -6.7 |
| USDCAD | short | 2004-12-09 | 2004-12-15 | 6 | 4 | zamknięta | czas | -218.0 |
| USDCAD | short | 2004-12-10 | 2004-12-16 | 6 | 4 | zamknięta | czas | -35.0 |
| USDCAD | short | 2004-12-15 | 2004-12-21 | 6 | 4 | zamknięta | czas | 81.0 |
| EURUSD | long | 2005-01-06 | 2005-01-12 | 6 | 4 | zamknięta | czas | -162.9 |
| GBPUSD | long | 2005-01-06 | 2005-01-12 | 6 | 4 | zamknięta | czas | -72.4 |
| USDCHF | short | 2005-01-06 | 2005-01-12 | 6 | 4 | zamknięta | czas | -153.9 |
| EURUSD | long | 2005-01-07 | 2005-01-13 | 6 | 4 | zamknięta | czas | 73.0 |
| GBPUSD | long | 2005-01-07 | 2005-01-13 | 6 | 4 | zamknięta | czas | 139.7 |
| USDCHF | short | 2005-01-07 | 2005-01-13 | 6 | 4 | zamknięta | czas | 62.1 |
| EURGBP | long | 2005-01-12 | 2005-01-18 | 6 | 4 | zamknięta | czas | 43.3 |
| EURJPY | long | 2005-01-12 | 2005-01-18 | 6 | 4 | zamknięta | czas | -222.1 |
| EURUSD | long | 2005-01-12 | 2005-01-18 | 6 | 4 | zamknięta | czas | -63.9 |
| USDCHF | short | 2005-01-12 | 2005-01-18 | 6 | 4 | zamknięta | czas | -21.9 |
| EURJPY | long | 2005-01-13 | 2005-01-19 | 6 | 4 | zamknięta | czas | -268.1 |
| EURUSD | long | 2005-01-21 | 2005-01-27 | 6 | 4 | zamknięta | czas | 115.2 |
| EURUSD | long | 2005-02-09 | 2005-02-15 | 6 | 4 | zamknięta | czas | 204.2 |
| GBPUSD | long | 2005-02-09 | 2005-02-15 | 6 | 4 | zamknięta | czas | 331.2 |
| USDCHF | short | 2005-02-09 | 2005-02-15 | 6 | 4 | zamknięta | czas | 228.1 |
| USDJPY | short | 2005-02-10 | 2005-02-16 | 6 | 4 | zamknięta | czas | 104.6 |
| USDJPY | short | 2005-02-11 | 2005-02-17 | 6 | 4 | zamknięta | czas | 32.6 |
| GBPUSD | long | 2005-03-23 | 2005-03-28 | 6 | 4 | zamknięta | czas | -193.6 |
| EURUSD | long | 2005-03-24 | 2005-03-29 | 6 | 4 | zamknięta | czas | -55.0 |
| GBPUSD | long | 2005-03-24 | 2005-03-29 | 6 | 4 | zamknięta | czas | 45.5 |
| USDCHF | short | 2005-03-24 | 2005-03-29 | 6 | 4 | zamknięta | czas | -42.9 |
| EURJPY | long | 2005-03-25 | 2005-03-30 | 6 | 4 | zamknięta | czas | 121.9 |
| EURUSD | long | 2005-03-25 | 2005-03-30 | 6 | 4 | zamknięta | czas | -18.8 |
| GBPUSD | long | 2005-03-25 | 2005-03-30 | 6 | 4 | zamknięta | czas | 90.4 |
| USDCHF | short | 2005-03-25 | 2005-03-30 | 6 | 4 | zamknięta | czas | 22.1 |
| USDJPY | short | 2005-03-25 | 2005-03-30 | 6 | 4 | zamknięta | czas | -112.4 |
| USDCAD | short | 2005-04-12 | 2005-04-18 | 6 | 4 | zamknięta | czas | -89.0 |
| USDCAD | short | 2005-04-13 | 2005-04-19 | 6 | 4 | zamknięta | czas | 2.0 |
| USDCAD | long | 2005-06-16 | 2005-06-22 | 6 | 4 | zamknięta | czas | -12.0 |
| EURGBP | short | 2005-07-05 | 2005-07-11 | 6 | 4 | zamknięta | czas | -83.7 |
| EURGBP | short | 2005-07-07 | 2005-07-13 | 6 | 4 | zamknięta | czas | 3.3 |
| EURGBP | short | 2005-07-12 | 2005-07-18 | 6 | 4 | zamknięta | czas | -19.7 |
| EURJPY | short | 2005-07-12 | 2005-07-19 | 7 | 4 | zamknięta | czas | -15.1 |
| EURUSD | short | 2005-08-04 | 2005-08-10 | 6 | 4 | zamknięta | czas | -2.0 |
| GBPUSD | short | 2005-08-04 | 2005-08-10 | 6 | 4 | zamknięta | czas | -154.4 |
| USDCHF | long | 2005-08-04 | 2005-08-10 | 6 | 4 | zamknięta | czas | -15.9 |
| GBPUSD | short | 2005-08-09 | 2005-08-15 | 6 | 4 | zamknięta | czas | -220.5 |
| EURUSD | short | 2005-08-10 | 2005-08-16 | 6 | 4 | zamknięta | czas | 36.1 |
| GBPUSD | short | 2005-08-10 | 2005-08-16 | 6 | 4 | zamknięta | czas | -128.6 |
| USDCHF | long | 2005-08-10 | 2005-08-16 | 6 | 4 | zamknięta | czas | 0.1 |
| EURUSD | short | 2005-08-11 | 2005-08-17 | 6 | 4 | zamknięta | czas | 192.0 |
| GBPUSD | short | 2005-08-11 | 2005-08-17 | 6 | 4 | zamknięta | czas | 58.8 |
| USDCHF | long | 2005-08-11 | 2005-08-17 | 6 | 4 | zamknięta | czas | 162.1 |
| GBPUSD | short | 2005-08-16 | 2005-08-22 | 6 | 4 | zamknięta | czas | 76.4 |
| GBPUSD | short | 2005-09-06 | 2005-09-12 | 6 | 4 | zamknięta | czas | 198.6 |
| EURGBP | short | 2005-09-29 | 2005-10-05 | 6 | 4 | zamknięta | czas | 42.3 |
| GBPUSD | short | 2005-12-14 | 2005-12-20 | 6 | 4 | zamknięta | czas | 74.3 |
| GBPUSD | short | 2005-12-15 | 2005-12-21 | 6 | 4 | zamknięta | czas | 147.6 |
| USDJPY | long | 2005-12-16 | 2005-12-22 | 6 | 4 | zamknięta | czas | 115.6 |
| USDCAD | short | 2005-12-21 | 2005-12-27 | 6 | 4 | zamknięta | czas | 48.0 |
| EURUSD | short | 2006-01-05 | 2006-01-11 | 6 | 4 | zamknięta | czas | 49.1 |
| USDCHF | long | 2006-01-05 | 2006-01-11 | 6 | 4 | zamknięta | czas | 33.1 |
| EURUSD | short | 2006-01-06 | 2006-01-12 | 6 | 4 | zamknięta | czas | -34.8 |
| USDCHF | long | 2006-01-06 | 2006-01-12 | 6 | 4 | zamknięta | czas | -28.9 |
| USDJPY | long | 2006-01-11 | 2006-01-17 | 6 | 4 | zamknięta | czas | 65.6 |
| USDJPY | long | 2006-01-12 | 2006-01-18 | 6 | 4 | zamknięta | czas | 131.1 |
| USDJPY | long | 2006-03-01 | 2006-03-07 | 6 | 4 | zamknięta | czas | 179.6 |
| USDCAD | short | 2006-03-10 | 2006-03-16 | 6 | 4 | zamknięta | czas | 64.0 |
| USDCAD | short | 2006-03-23 | 2006-03-28 | 6 | 4 | zamknięta | czas | -42.0 |
| USDCAD | short | 2006-03-24 | 2006-03-29 | 6 | 4 | zamknięta | czas | -72.0 |
| USDCAD | short | 2006-03-28 | 2006-04-03 | 6 | 4 | zamknięta | czas | -23.0 |
| USDCAD | short | 2006-03-29 | 2006-04-04 | 6 | 4 | zamknięta | czas | 86.0 |
| EURGBP | long | 2006-05-03 | 2006-05-09 | 6 | 4 | zamknięta | czas | -27.2 |
| EURGBP | long | 2006-05-04 | 2006-05-10 | 6 | 4 | zamknięta | czas | 1.3 |
| EURUSD | long | 2006-06-13 | 2006-06-19 | 6 | 4 | zamknięta | czas | 33.2 |
| USDJPY | short | 2006-06-13 | 2006-06-19 | 6 | 4 | zamknięta | czas | -15.4 |
| GBPUSD | long | 2006-06-28 | 2006-07-04 | 6 | 4 | zamknięta | czas | 268.5 |
| USDCAD | short | 2006-07-12 | 2006-07-18 | 6 | 4 | zamknięta | czas | -25.0 |
| EURUSD | long | 2006-07-18 | 2006-07-24 | 6 | 4 | zamknięta | czas | 121.1 |
| USDCHF | short | 2006-07-18 | 2006-07-24 | 6 | 4 | zamknięta | czas | 55.1 |
| USDCHF | short | 2006-09-13 | 2006-09-19 | 6 | 4 | zamknięta | czas | -19.9 |
| USDCHF | short | 2006-09-14 | 2006-09-20 | 6 | 4 | zamknięta | czas | 13.1 |
| USDCAD | short | 2006-09-20 | 2006-09-26 | 6 | 4 | zamknięta | czas | 145.0 |
| EURUSD | long | 2006-10-10 | 2006-10-16 | 6 | 4 | zamknięta | czas | 8.2 |
| EURUSD | long | 2006-10-11 | 2006-10-17 | 6 | 4 | zamknięta | czas | 19.1 |
| GBPUSD | long | 2006-10-11 | 2006-10-17 | 6 | 4 | zamknięta | czas | 168.3 |
| EURGBP | short | 2006-11-16 | 2006-11-22 | 6 | 4 | zamknięta | czas | 22.3 |
| USDCAD | long | 2006-11-29 | 2006-12-05 | 6 | 4 | zamknięta | czas | 105.0 |
| USDCAD | long | 2007-03-22 | 2007-03-27 | 6 | 4 | zamknięta | czas | 0.0 |
| USDCAD | long | 2007-03-23 | 2007-03-28 | 6 | 4 | zamknięta | czas | 12.1 |
| USDCHF | short | 2007-05-22 | 2007-05-28 | 6 | 4 | zamknięta | czas | 8.7 |
| EURGBP | long | 2007-05-24 | 2007-05-30 | 6 | 4 | zamknięta | czas | 30.3 |
| EURUSD | long | 2007-06-12 | 2007-06-18 | 6 | 4 | zamknięta | czas | 109.1 |
| EURUSD | long | 2007-06-13 | 2007-06-19 | 6 | 4 | zamknięta | czas | 113.1 |
| EURJPY | long | 2007-07-25 | 2007-07-31 | 6 | 4 | zamknięta | czas | -339.1 |
| USDCAD | short | 2007-07-31 | 2007-08-06 | 6 | 4 | zamknięta | czas | 150.6 |
| AUDUSD | long | 2007-08-14 | 2007-08-20 | 6 | 4 | zamknięta | czas | -283.5 |
| AUDUSD | long | 2007-08-15 | 2007-08-21 | 6 | 4 | zamknięta | czas | -198.1 |
| EURUSD | long | 2007-08-15 | 2007-08-22 | 7 | 4 | zamknięta | czas | 122.1 |
| GBPUSD | long | 2007-08-15 | 2007-08-21 | 6 | 4 | zamknięta | czas | -67.2 |
| EURUSD | long | 2007-08-16 | 2007-08-23 | 7 | 4 | zamknięta | czas | 129.1 |
| GBPUSD | long | 2007-08-16 | 2007-08-22 | 6 | 4 | zamknięta | czas | 95.5 |
| USDCHF | short | 2007-08-16 | 2007-08-22 | 6 | 4 | zamknięta | czas | 103.1 |
| USDCAD | short | 2007-12-06 | 2007-12-12 | 6 | 4 | zamknięta | czas | -5.0 |
| GBPUSD | long | 2007-12-07 | 2007-12-13 | 6 | 4 | zamknięta | czas | 169.4 |
| EURUSD | long | 2007-12-19 | 2007-12-25 | 6 | 4 | zamknięta | czas | -23.9 |
| USDCHF | short | 2007-12-19 | 2007-12-25 | 6 | 4 | zamknięta | czas | -53.9 |
| EURUSD | long | 2007-12-20 | 2007-12-27 | 7 | 4 | zamknięta | czas | 103.1 |
| USDCHF | short | 2007-12-20 | 2007-12-27 | 7 | 4 | zamknięta | czas | 33.1 |
| EURUSD | long | 2007-12-21 | 2007-12-28 | 7 | 4 | zamknięta | czas | 280.0 |
| USDCHF | short | 2007-12-26 | 2008-01-01 | 6 | 4 | zamknięta | czas | 264.1 |
| USDJPY | short | 2007-12-26 | 2008-01-01 | 6 | 4 | zamknięta | czas | 252.6 |
| USDJPY | short | 2007-12-27 | 2008-01-03 | 7 | 4 | zamknięta | czas | 494.3 |
| USDCAD | short | 2008-01-18 | 2008-01-25 | 7 | 4 | zamknięta | czas | 252.0 |
| USDCAD | short | 2008-01-23 | 2008-01-29 | 6 | 4 | zamknięta | czas | 226.0 |
| EURJPY | short | 2008-02-21 | 2008-02-27 | 6 | 4 | zamknięta | czas | -200.1 |
| EURJPY | short | 2008-02-22 | 2008-02-28 | 6 | 4 | zamknięta | czas | -173.1 |
| EURJPY | short | 2008-02-27 | 2008-03-04 | 6 | 4 | zamknięta | czas | 361.9 |
| EURJPY | short | 2008-02-28 | 2008-03-05 | 6 | 4 | zamknięta | czas | 358.4 |
| EURUSD | long | 2008-06-04 | 2008-06-10 | 6 | 4 | zamknięta | czas | 29.2 |
| GBPUSD | short | 2008-07-01 | 2008-07-07 | 6 | 4 | zamknięta | czas | 180.6 |
| GBPUSD | short | 2008-07-02 | 2008-07-08 | 6 | 4 | zamknięta | czas | 239.4 |
| USDCAD | long | 2008-07-16 | 2008-07-22 | 6 | 4 | zamknięta | czas | 59.0 |
| AUDUSD | long | 2008-07-30 | 2008-08-05 | 6 | 4 | zamknięta | czas | -270.0 |
| AUDUSD | long | 2008-07-31 | 2008-08-06 | 6 | 4 | zamknięta | czas | -284.3 |
| USDCHF | short | 2008-08-06 | 2008-08-12 | 6 | 4 | zamknięta | czas | -289.9 |
| USDCHF | short | 2008-08-07 | 2008-08-13 | 6 | 4 | zamknięta | czas | -239.9 |
| EURGBP | long | 2008-09-16 | 2008-09-22 | 6 | 4 | zamknięta | czas | 37.3 |
| EURGBP | long | 2008-09-17 | 2008-09-23 | 6 | 4 | zamknięta | czas | 21.3 |
| GBPUSD | short | 2008-09-23 | 2008-09-29 | 6 | 4 | zamknięta | czas | 543.6 |
| USDCAD | long | 2008-09-23 | 2008-09-29 | 6 | 4 | zamknięta | czas | 124.0 |
| EURJPY | short | 2008-12-17 | 2008-12-23 | 6 | 4 | zamknięta | czas | -111.1 |
| AUDUSD | short | 2008-12-18 | 2008-12-24 | 6 | 4 | zamknięta | czas | 250.7 |
| EURJPY | short | 2008-12-18 | 2008-12-24 | 6 | 4 | zamknięta | czas | -87.7 |
| USDCAD | long | 2008-12-18 | 2008-12-24 | 6 | 4 | zamknięta | czas | 262.0 |
| EURJPY | short | 2008-12-19 | 2008-12-25 | 6 | 4 | zamknięta | czas | 117.9 |
| AUDUSD | short | 2009-01-07 | 2009-01-13 | 6 | 4 | zamknięta | czas | 402.9 |
| USDCAD | long | 2009-01-07 | 2009-01-13 | 6 | 4 | zamknięta | czas | 318.0 |
| USDJPY | short | 2009-02-20 | 2009-02-26 | 6 | 4 | zamknięta | czas | -336.4 |
| USDJPY | short | 2009-02-25 | 2009-03-03 | 6 | 4 | zamknięta | czas | -50.8 |
| EURJPY | short | 2009-02-26 | 2009-03-04 | 6 | 4 | zamknięta | czas | 36.3 |
| USDJPY | short | 2009-02-26 | 2009-03-04 | 6 | 4 | zamknięta | czas | -113.9 |
| EURJPY | short | 2009-02-27 | 2009-03-05 | 6 | 4 | zamknięta | czas | -6.4 |
| USDJPY | short | 2009-02-27 | 2009-03-05 | 6 | 4 | zamknięta | czas | -70.8 |
| USDJPY | short | 2009-03-05 | 2009-03-11 | 6 | 4 | zamknięta | czas | 22.6 |
| EURUSD | short | 2009-03-18 | 2009-03-24 | 6 | 4 | zamknięta | czas | -587.3 |
| AUDUSD | short | 2009-03-19 | 2009-03-25 | 6 | 4 | zamknięta | czas | -207.5 |
| EURJPY | short | 2009-03-19 | 2009-03-25 | 6 | 4 | zamknięta | czas | -256.3 |
| AUDUSD | short | 2009-03-20 | 2009-03-26 | 6 | 4 | zamknięta | czas | -109.9 |
| EURUSD | short | 2009-03-20 | 2009-03-26 | 6 | 4 | zamknięta | czas | 86.1 |
| GBPUSD | short | 2009-03-20 | 2009-03-26 | 6 | 4 | zamknięta | czas | -55.1 |
| USDCAD | long | 2009-03-20 | 2009-03-26 | 6 | 4 | zamknięta | czas | -111.0 |
| USDCHF | long | 2009-03-20 | 2009-03-26 | 6 | 4 | zamknięta | czas | -14.9 |
| AUDUSD | short | 2009-03-25 | 2009-03-30 | 6 | 4 | zamknięta | czas | 191.4 |
| EURJPY | short | 2009-03-25 | 2009-03-30 | 6 | 4 | zamknięta | czas | 408.1 |
| GBPUSD | short | 2009-03-25 | 2009-03-30 | 6 | 4 | zamknięta | czas | 458.2 |
| AUDUSD | short | 2009-03-26 | 2009-03-31 | 6 | 4 | zamknięta | czas | 71.8 |
| EURJPY | short | 2009-03-26 | 2009-03-31 | 6 | 4 | zamknięta | czas | 160.6 |
| AUDUSD | short | 2009-03-27 | 2009-04-01 | 6 | 4 | zamknięta | czas | 28.2 |
| EURGBP | long | 2009-04-08 | 2009-04-14 | 6 | 4 | zamknięta | czas | -119.7 |
| EURGBP | long | 2009-04-09 | 2009-04-15 | 6 | 4 | zamknięta | czas | -150.7 |
| EURGBP | long | 2009-04-15 | 2009-04-21 | 6 | 4 | zamknięta | czas | 5.3 |
| GBPUSD | short | 2009-04-15 | 2009-04-21 | 6 | 4 | zamknięta | czas | 333.5 |
| USDCAD | long | 2009-04-15 | 2009-04-21 | 6 | 4 | zamknięta | czas | 328.0 |
| EURGBP | long | 2009-04-16 | 2009-04-22 | 6 | 4 | zamknięta | czas | 139.3 |
| GBPUSD | short | 2009-05-05 | 2009-05-11 | 6 | 4 | zamknięta | czas | -66.7 |
| GBPUSD | short | 2009-05-06 | 2009-05-12 | 6 | 4 | zamknięta | czas | -122.0 |
| EURJPY | long | 2009-06-17 | 2009-06-23 | 6 | 4 | zamknięta | czas | 43.9 |
| USDCAD | short | 2009-06-23 | 2009-06-29 | 6 | 4 | zamknięta | czas | -57.0 |
| USDCAD | short | 2009-06-24 | 2009-06-30 | 6 | 4 | zamknięta | czas | -71.0 |
| USDCAD | short | 2009-06-25 | 2009-07-01 | 6 | 4 | zamknięta | czas | 61.0 |
| USDCAD | short | 2009-06-30 | 2009-07-06 | 6 | 4 | zamknięta | czas | 16.0 |
| GBPUSD | long | 2009-07-08 | 2009-07-14 | 6 | 4 | zamknięta | czas | 261.3 |
| EURGBP | short | 2009-08-25 | 2009-09-01 | 7 | 4 | zamknięta | czas | -38.7 |
| EURGBP | short | 2009-08-26 | 2009-09-02 | 7 | 4 | zamknięta | czas | 49.3 |
| EURGBP | short | 2009-09-01 | 2009-09-07 | 6 | 4 | zamknięta | czas | 0.3 |
| EURJPY | long | 2009-09-02 | 2009-09-09 | 7 | 4 | zamknięta | czas | 184.9 |
| GBPUSD | long | 2009-09-28 | 2009-10-05 | 7 | 4 | zamknięta | czas | -23.4 |
| USDCHF | short | 2009-12-10 | 2009-12-16 | 6 | 4 | zamknięta | czas | -142.9 |
| USDCHF | short | 2009-12-11 | 2009-12-17 | 6 | 4 | zamknięta | czas | -130.9 |
| EURGBP | long | 2009-12-17 | 2009-12-23 | 6 | 4 | zamknięta | czas | 27.3 |
| EURUSD | long | 2009-12-17 | 2009-12-23 | 6 | 4 | zamknięta | czas | -270.9 |
| USDCHF | short | 2009-12-17 | 2009-12-23 | 6 | 4 | zamknięta | czas | -94.9 |
| EURUSD | long | 2009-12-18 | 2009-12-24 | 6 | 4 | zamknięta | czas | -10.8 |
| USDCHF | short | 2009-12-18 | 2009-12-24 | 6 | 4 | zamknięta | czas | 73.1 |
| AUDUSD | long | 2009-12-23 | 2009-12-30 | 7 | 4 | zamknięta | czas | 167.6 |
| EURUSD | long | 2009-12-23 | 2009-12-30 | 7 | 4 | zamknięta | czas | 86.4 |
| GBPUSD | long | 2009-12-23 | 2009-12-30 | 7 | 4 | zamknięta | czas | -71.6 |
| USDJPY | short | 2009-12-23 | 2009-12-30 | 7 | 4 | zamknięta | czas | -18.4 |
| GBPUSD | long | 2009-12-24 | 2009-12-31 | 7 | 4 | zamknięta | czas | 106.3 |
| USDJPY | short | 2009-12-24 | 2009-12-31 | 7 | 4 | zamknięta | czas | -83.4 |
| USDJPY | short | 2009-12-31 | 2010-01-07 | 7 | 4 | zamknięta | czas | 6.0 |
| USDCAD | short | 2010-01-27 | 2010-02-02 | 6 | 4 | zamknięta | czas | 1.0 |
| USDCAD | short | 2010-01-28 | 2010-02-03 | 6 | 4 | zamknięta | czas | 63.2 |
| USDCHF | short | 2010-01-28 | 2010-02-03 | 6 | 4 | zamknięta | czas | -50.9 |
| AUDUSD | long | 2010-01-29 | 2010-02-04 | 6 | 4 | zamknięta | czas | -117.6 |
| USDCHF | short | 2010-01-29 | 2010-02-04 | 6 | 4 | zamknięta | czas | -64.9 |
| AUDUSD | long | 2010-02-05 | 2010-02-11 | 6 | 4 | zamknięta | czas | 81.3 |
| USDJPY | short | 2010-02-19 | 2010-02-25 | 6 | 4 | zamknięta | czas | 162.1 |
| EURJPY | short | 2010-04-01 | 2010-04-07 | 6 | 4 | zamknięta | czas | 293.8 |
| GBPUSD | short | 2010-04-15 | 2010-04-21 | 6 | 4 | zamknięta | czas | 51.2 |
| USDCHF | long | 2010-06-16 | 2010-06-22 | 6 | 4 | zamknięta | czas | -233.2 |
| USDCHF | long | 2010-06-17 | 2010-06-23 | 6 | 4 | zamknięta | czas | -72.9 |
| USDCHF | long | 2010-06-22 | 2010-06-28 | 6 | 4 | zamknięta | czas | -204.9 |
| USDCHF | long | 2010-06-23 | 2010-06-29 | 6 | 4 | zamknięta | czas | -227.5 |
| USDCHF | long | 2010-06-24 | 2010-06-30 | 6 | 4 | zamknięta | czas | -240.9 |
| GBPUSD | short | 2010-06-28 | 2010-07-05 | 7 | 4 | zamknięta | czas | -36.5 |
| USDCHF | long | 2010-06-29 | 2010-07-05 | 6 | 4 | zamknięta | czas | -179.9 |
| USDCHF | long | 2010-06-30 | 2010-07-06 | 6 | 4 | zamknięta | czas | -183.4 |
| EURUSD | short | 2010-07-07 | 2010-07-13 | 6 | 4 | zamknięta | czas | -87.7 |
| EURUSD | short | 2010-07-08 | 2010-07-14 | 6 | 4 | zamknięta | czas | -49.4 |
| EURUSD | short | 2010-08-03 | 2010-08-09 | 6 | 4 | zamknięta | czas | -60.6 |
| EURUSD | short | 2010-08-04 | 2010-08-10 | 6 | 4 | zamknięta | czas | -69.9 |
| EURGBP | short | 2010-09-07 | 2010-09-13 | 6 | 4 | zamknięta | czas | -14.1 |
| EURUSD | short | 2010-09-16 | 2010-09-22 | 6 | 4 | zamknięta | czas | -182.7 |
| EURJPY | short | 2010-09-21 | 2010-09-27 | 6 | 4 | zamknięta | czas | -84.3 |
| EURGBP | short | 2010-09-23 | 2010-09-29 | 6 | 4 | zamknięta | czas | -93.7 |
| EURJPY | short | 2010-09-23 | 2010-09-29 | 6 | 4 | zamknięta | czas | -131.8 |
| EURGBP | long | 2010-11-11 | 2010-11-17 | 6 | 4 | zamknięta | czas | -83.0 |
| USDJPY | short | 2010-11-17 | 2010-11-23 | 6 | 4 | zamknięta | czas | -13.2 |
| AUDUSD | long | 2010-11-18 | 2010-11-24 | 6 | 4 | zamknięta | czas | 47.7 |
| USDJPY | short | 2010-11-23 | 2010-11-30 | 7 | 4 | zamknięta | czas | -85.4 |
| AUDUSD | long | 2010-12-01 | 2010-12-07 | 6 | 4 | zamknięta | czas | 322.9 |
| GBPUSD | long | 2010-12-01 | 2010-12-07 | 6 | 4 | zamknięta | czas | 194.9 |
| USDJPY | short | 2010-12-01 | 2010-12-07 | 6 | 4 | zamknięta | czas | 87.2 |
| AUDUSD | long | 2010-12-02 | 2010-12-08 | 6 | 4 | zamknięta | czas | 226.5 |
| GBPUSD | long | 2010-12-02 | 2010-12-08 | 6 | 4 | zamknięta | czas | 96.6 |
| GBPUSD | long | 2010-12-24 | 2010-12-30 | 6 | 4 | zamknięta | czas | -89.7 |
| USDJPY | short | 2011-02-16 | 2011-02-22 | 6 | 4 | zamknięta | czas | 62.6 |
| USDJPY | short | 2011-02-17 | 2011-02-23 | 6 | 4 | zamknięta | czas | 53.3 |
| USDCAD | short | 2011-03-18 | 2011-03-24 | 6 | 4 | zamknięta | czas | 22.4 |
| EURJPY | long | 2011-05-10 | 2011-05-16 | 6 | 4 | zamknięta | czas | -300.1 |
| EURUSD | long | 2011-05-10 | 2011-05-16 | 6 | 4 | zamknięta | czas | -334.0 |
| GBPUSD | long | 2011-05-17 | 2011-05-23 | 6 | 4 | zamknięta | czas | -39.4 |
| USDJPY | short | 2011-05-25 | 2011-05-31 | 6 | 4 | zamknięta | czas | 112.6 |
| USDJPY | short | 2011-05-26 | 2011-06-01 | 6 | 4 | zamknięta | czas | -19.0 |
| AUDUSD | long | 2011-06-28 | 2011-07-04 | 6 | 4 | zamknięta | czas | 238.1 |
| EURGBP | long | 2011-07-13 | 2011-07-19 | 6 | 4 | zamknięta | czas | -16.2 |
| EURUSD | long | 2011-07-13 | 2011-07-19 | 6 | 4 | zamknięta | czas | -118.2 |
| EURGBP | long | 2011-08-02 | 2011-08-08 | 6 | 4 | zamknięta | czas | -4.7 |
| EURGBP | long | 2011-08-03 | 2011-08-09 | 6 | 4 | zamknięta | czas | -49.7 |
| USDCHF | short | 2011-08-30 | 2011-09-05 | 6 | 4 | zamknięta | czas | 290.1 |
| USDCHF | short | 2011-08-31 | 2011-09-06 | 6 | 4 | zamknięta | czas | 207.2 |
| EURUSD | long | 2011-09-06 | 2011-09-12 | 6 | 4 | zamknięta | czas | -403.9 |
| EURUSD | long | 2011-09-07 | 2011-09-13 | 6 | 4 | zamknięta | czas | -424.5 |
| USDCHF | short | 2011-09-08 | 2011-09-14 | 6 | 4 | zamknięta | czas | -55.9 |
| USDCHF | short | 2011-09-14 | 2011-09-20 | 6 | 4 | zamknięta | czas | -101.3 |
| GBPUSD | short | 2011-10-25 | 2011-11-01 | 6 | 4 | zamknięta | czas | -115.4 |
| GBPUSD | short | 2011-10-26 | 2011-11-02 | 6 | 4 | zamknięta | czas | -124.9 |
| USDCHF | long | 2011-10-26 | 2011-11-02 | 6 | 4 | zamknięta | czas | -49.9 |
| USDJPY | short | 2011-11-03 | 2011-11-09 | 6 | 4 | zamknięta | czas | 3.3 |
| USDJPY | short | 2011-11-04 | 2011-11-10 | 6 | 4 | zamknięta | czas | 30.8 |
| USDJPY | short | 2011-11-30 | 2011-12-06 | 6 | 4 | zamknięta | czas | -12.5 |
| USDJPY | short | 2011-12-01 | 2011-12-07 | 6 | 4 | zamknięta | czas | -26.3 |
| USDCAD | long | 2011-12-09 | 2011-12-15 | 6 | 4 | zamknięta | czas | 117.0 |
| AUDUSD | short | 2012-01-06 | 2012-01-12 | 6 | 4 | zamknięta | czas | -47.7 |
| GBPUSD | short | 2012-01-26 | 2012-02-01 | 6 | 4 | zamknięta | czas | -50.7 |
| EURJPY | short | 2012-01-27 | 2012-02-02 | 6 | 4 | zamknięta | czas | 162.7 |
| GBPUSD | short | 2012-01-27 | 2012-02-02 | 6 | 4 | zamknięta | czas | -87.2 |
| USDJPY | short | 2012-01-27 | 2012-02-02 | 6 | 4 | zamknięta | czas | 117.9 |
| GBPUSD | short | 2012-02-01 | 2012-02-07 | 6 | 4 | zamknięta | czas | -96.1 |
| USDCHF | long | 2012-02-01 | 2012-02-07 | 6 | 4 | zamknięta | czas | 16.1 |
| GBPUSD | short | 2012-02-02 | 2012-02-08 | 6 | 4 | zamknięta | czas | 33.6 |
| GBPUSD | short | 2012-02-08 | 2012-02-14 | 6 | 4 | zamknięta | czas | 109.6 |
| EURJPY | short | 2012-02-15 | 2012-02-21 | 6 | 4 | zamknięta | czas | -262.1 |
| EURJPY | short | 2012-02-16 | 2012-02-23 | 7 | 4 | zamknięta | czas | -329.2 |
| EURJPY | short | 2012-02-22 | 2012-02-29 | 7 | 4 | zamknięta | czas | -215.6 |
| EURJPY | short | 2012-02-23 | 2012-03-01 | 7 | 4 | zamknięta | czas | -209.6 |
| EURJPY | short | 2012-02-24 | 2012-03-02 | 7 | 4 | zamknięta | czas | -140.0 |
| USDCHF | long | 2012-02-29 | 2012-03-06 | 6 | 4 | zamknięta | czas | 203.6 |
| USDCHF | long | 2012-03-01 | 2012-03-07 | 6 | 4 | zamknięta | czas | 69.5 |
| USDCAD | short | 2012-05-10 | 2012-05-16 | 6 | 4 | zamknięta | czas | -40.6 |
| GBPUSD | long | 2012-05-17 | 2012-05-23 | 6 | 4 | zamknięta | czas | -25.9 |
| AUDUSD | short | 2012-06-19 | 2012-06-26 | 7 | 4 | zamknięta | czas | 164.1 |
| AUDUSD | short | 2012-06-21 | 2012-06-27 | 6 | 4 | zamknięta | czas | -6.7 |
| AUDUSD | short | 2012-07-03 | 2012-07-09 | 6 | 4 | zamknięta | czas | 87.5 |
| EURUSD | short | 2012-08-23 | 2012-08-29 | 6 | 4 | zamknięta | czas | -12.0 |
| USDCHF | long | 2012-08-23 | 2012-08-29 | 6 | 4 | zamknięta | czas | -8.9 |
| EURUSD | short | 2012-09-11 | 2012-09-17 | 6 | 4 | zamknięta | czas | -265.6 |
| USDCHF | long | 2012-09-11 | 2012-09-17 | 6 | 4 | zamknięta | czas | -128.5 |
| EURGBP | short | 2012-09-13 | 2012-09-19 | 6 | 4 | zamknięta | czas | 10.3 |
| EURGBP | short | 2012-10-09 | 2012-10-15 | 6 | 4 | zamknięta | czas | -18.3 |
| USDJPY | short | 2012-10-17 | 2012-10-24 | 7 | 4 | zamknięta | czas | -78.4 |
| USDJPY | short | 2012-10-18 | 2012-10-25 | 7 | 4 | zamknięta | czas | -53.6 |
| GBPUSD | long | 2012-11-14 | 2012-11-20 | 6 | 4 | zamknięta | czas | 28.8 |
| GBPUSD | long | 2012-11-15 | 2012-11-21 | 6 | 4 | zamknięta | czas | 53.4 |
| AUDUSD | long | 2012-12-27 | 2013-01-04 | 8 | 4 | zamknięta | czas | 125.7 |
| AUDUSD | long | 2012-12-28 | 2013-01-05 | 8 | 4 | zamknięta | czas | 82.3 |
| AUDUSD | long | 2012-12-31 | 2013-01-08 | 8 | 4 | zamknięta | czas | 101.3 |
| USDCAD | short | 2013-01-23 | 2013-01-29 | 6 | 4 | zamknięta | czas | -160.6 |
| EURUSD | long | 2013-02-27 | 2013-03-05 | 6 | 4 | zamknięta | czas | -53.3 |
| USDCHF | short | 2013-02-27 | 2013-03-05 | 6 | 4 | zamknięta | czas | -106.1 |
| EURUSD | long | 2013-02-28 | 2013-03-06 | 6 | 4 | zamknięta | czas | -115.8 |
| USDCHF | short | 2013-03-06 | 2013-03-12 | 6 | 4 | zamknięta | czas | -113.9 |
| USDCHF | short | 2013-03-07 | 2013-03-13 | 6 | 4 | zamknięta | czas | 0.8 |
| USDCAD | long | 2013-03-29 | 2013-04-03 | 6 | 4 | zamknięta | czas | -18.1 |
| USDCAD | long | 2013-04-04 | 2013-04-10 | 6 | 4 | zamknięta | czas | 28.6 |
| USDCAD | long | 2013-05-01 | 2013-05-07 | 6 | 4 | zamknięta | czas | -7.0 |
| GBPUSD | short | 2013-05-02 | 2013-05-08 | 6 | 4 | zamknięta | czas | 56.2 |
| USDCAD | long | 2013-05-02 | 2013-05-08 | 6 | 4 | zamknięta | czas | -59.0 |
| USDCAD | long | 2013-05-09 | 2013-05-15 | 6 | 4 | zamknięta | czas | 110.0 |
| USDJPY | long | 2013-06-13 | 2013-06-19 | 6 | 4 | zamknięta | czas | -1.1 |
| GBPUSD | short | 2013-07-24 | 2013-07-30 | 6 | 4 | zamknięta | czas | -34.8 |
| EURJPY | long | 2014-02-04 | 2014-02-11 | 7 | 4 | zamknięta | czas | 281.4 |
| EURJPY | long | 2014-05-22 | 2014-05-29 | 7 | 4 | zamknięta | czas | -71.6 |
| GBPUSD | short | 2015-05-13 | 2015-05-20 | 7 | 4 | zamknięta | czas | 220.5 |
| GBPUSD | long | 2015-08-31 | 2015-09-07 | 7 | 4 | zamknięta | czas | -165.5 |
| AUDUSD | short | 2015-10-12 | 2015-10-19 | 7 | 4 | zamknięta | czas | 84.7 |
| EURJPY | short | 2016-03-31 | 2016-04-07 | 7 | 4 | zamknięta | czas | 288.5 |
| GBPUSD | short | 2016-04-27 | 2016-05-04 | 7 | 4 | zamknięta | czas | -11.2 |
| USDCAD | short | 2016-05-23 | 2016-05-30 | 7 | 4 | zamknięta | czas | 99.0 |
| USDCAD | short | 2016-05-24 | 2016-05-31 | 7 | 4 | zamknięta | czas | 86.0 |
| EURJPY | short | 2016-11-24 | 2016-12-01 | 7 | 4 | zamknięta | czas | -113.2 |
| EURJPY | short | 2016-11-25 | 2016-12-02 | 7 | 4 | zamknięta | czas | -187.6 |
| USDCAD | short | 2017-10-31 | 2017-11-07 | 7 | 4 | zamknięta | czas | 65.0 |
| USDCAD | short | 2017-11-01 | 2017-11-08 | 7 | 4 | zamknięta | czas | 176.2 |
| EURJPY | short | 2018-07-18 | 2018-07-25 | 7 | 4 | zamknięta | czas | 135.9 |
| EURGBP | long | 2018-09-19 | 2018-09-26 | 7 | 4 | zamknięta | czas | 38.5 |
| USDCAD | long | 2019-02-05 | 2019-02-12 | 7 | 4 | zamknięta | czas | 158.0 |
| USDJPY | short | 2019-02-15 | 2019-02-22 | 7 | 4 | zamknięta | czas | -24.0 |
| USDCHF | short | 2019-09-03 | 2019-09-10 | 7 | 4 | zamknięta | czas | -57.2 |
| USDJPY | short | 2019-09-12 | 2019-09-19 | 7 | 4 | zamknięta | czas | -26.1 |
| AUDUSD | short | 2019-10-23 | 2019-10-31 | 7 | 4 | zamknięta | czas | -7.3 |
| USDCHF | short | 2020-03-26 | 2020-04-01 | 7 | 4 | zamknięta | czas | 146.8 |
| USDCAD | long | 2020-05-28 | 2020-06-04 | 7 | 4 | zamknięta | czas | -284.0 |
| GBPUSD | short | 2020-06-03 | 2020-06-10 | 7 | 4 | zamknięta | czas | -138.3 |
| GBPUSD | short | 2020-06-04 | 2020-06-11 | 7 | 4 | zamknięta | czas | -109.3 |
| EURGBP | long | 2020-09-03 | 2020-09-10 | 7 | 4 | zamknięta | czas | 151.6 |
| EURGBP | short | 2021-07-21 | 2021-07-28 | 7 | 4 | zamknięta | czas | 83.9 |
| AUDUSD | short | 2022-03-07 | 2022-03-15 | 8 | 4 | zamknięta | czas | 93.9 |
| EURJPY | long | 2022-07-07 | 2022-07-14 | 7 | 4 | zamknięta | czas | -13.0 |
| USDCAD | long | 2023-11-29 | 2023-12-06 | 7 | 4 | zamknięta | czas | -26.0 |
| USDCAD | long | 2023-11-30 | 2023-12-07 | 7 | 4 | zamknięta | czas | -1.2 |
| EURJPY | long | 2024-03-13 | 2024-03-20 | 7 | 4 | zamknięta | czas | 86.1 |
| EURJPY | long | 2024-07-31 | 2024-08-07 | 7 | 4 | zamknięta | czas | -396.1 |
| EURJPY | short | 2024-12-18 | 2024-12-25 | 7 | 4 | zamknięta | czas | -229.1 |
| EURJPY | short | 2024-12-24 | 2024-12-31 | 7 | 4 | zamknięta | czas | -125.9 |
| EURJPY | short | 2024-12-27 | 2025-01-03 | 7 | 4 | zamknięta | czas | 117.8 |
| USDJPY | short | 2025-07-15 | 2025-07-22 | 7 | 4 | zamknięta | czas | 133.8 |
| USDCHF | short | 2025-11-05 | 2025-11-12 | 7 | 4 | zamknięta | czas | 49.8 |
| USDCHF | short | 2025-11-06 | 2025-11-13 | 7 | 4 | zamknięta | czas | 92.1 |
| USDCHF | short | 2025-11-07 | 2025-11-14 | 7 | 4 | zamknięta | czas | 78.9 |
| USDCAD | short | 2026-01-09 | 2026-01-16 | 7 | 4 | zamknięta | czas | -22.2 |
| USDJPY | long | 2026-01-30 | 2026-02-06 | 7 | 4 | zamknięta | czas | 375.6 |
| AUDUSD | long | 2026-03-31 | 2026-04-07 | 7 | 4 | zamknięta | czas | -2.2 |
| EURJPY | long | 2026-05-05 | 2026-05-12 | 7 | 4 | zamknięta | czas | 47.3 |
| USDCAD | short | 2026-05-18 | 2026-05-25 | 7 | 4 | zamknięta | czas | -66.8 |
| USDCAD | short | 2026-05-26 | 2026-06-02 | 7 | 4 | zamknięta | czas | -36.5 |
| USDCAD | short | 2026-05-27 | 2026-06-03 | 7 | 4 | zamknięta | czas | -4.2 |
| USDCAD | long | 2026-08-18 | 2026-08-25 | 7 | 4 | zamknięta | czas | -60.2 |
| USDCAD | long | 2026-10-28 | 2026-11-04 | 7 | 4 | zamknięta | czas | -68.4 |

Tabela pokazuje wszystkie otwarte i najdłuższe zamknięte (400 z 1277); pełna lista: trades.parquet i tabela transakcji w dashboardzie (kolumny „dni” i „status”).

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 15.59 pips/transakcję, percentyl **100.0** (losowe: 5%=-7.99, mediana=-1.53, 95%=4.72).

- **Deflated Sharpe Ratio**: 0.995 (Sharpe na transakcję 0.124, próg przy 36 próbach 0.039).

- **PBO** (CSCV, 16 bloków, 36 wariantów): 0.619 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 425 transakcji, śr. 1.26 pips, 0.04 R.

- **Bootstrap 95%** średnich pipsów: całość [8.06; 22.98], OOS [-1.37; 19.58].

- **Spread**: ×1 15.59, ×1,5 14.77, ×2 13.94 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 5.3 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 12.95, 1 pips: 10.30 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo (D-058); wejście na open następnego dnia, wyjście po X dniach

HYPOTHESIS = """Wersja 2 strategii RSI na D1, z diagnozy stratnych i zyskownych wejść wersji 1 (research/rsi_d1/README.md).
Straty łączyło: pierwszy dzień wyprzedania (spadek często trwa dalej), dzień-szok z bardzo szerokim zakresem i głęboki krach
przeciw trendowi. Zyski łączyło: trend 200-dniowy po stronie transakcji i KOLEJNY dzień wyprzedania z rzędu — sprzedający
się wyczerpują, a trend wraca w 3–4 dni. Wzmacniamy to: wejście dopiero od 2. (albo 3.) dnia z rzędu z RSI za progiem,
nad SMA200 (short lustrzanie pod), bez dni-szoków; wyjście po 3–5 dniach na zamknięciu. Konfiguracje wybrane na IS:
odporne w obu połowach IS (1996–2011, 2012–2019) i na obu wersjach zamknięć D1 Yahoo (zob. D-068 — zamknięcia D1 Yahoo)."""

# Każda konfiguracja = jedna wersja (wariant wejścia) × 3 limity dni z EXITS.
#   rsi:    (okres, próg wyprzedania); wykupienie = 100 − próg
#   od:     od którego dnia z rzędu za progiem (i po stronie trendu) wchodzimy: 1 = od pierwszego, 2 = od drugiego, …
#   zakres: pomiń dzień-szok, gdy (high − low) dnia sygnału ≥ zakres × ATR14; None = bez cięcia
#   sl:     None albo k × ATR14 od zamknięcia dnia sygnału
#   waga:   "stala" 1; "seria" = 1 w dniu „od”, 2 dzień później, 3 od trzeciego (dokładanie przy przedłużonym wyprzedaniu)
CONFIGS = [
    # 0 = wybór po IS: najbardziej odporna (min. Sharpe z 4 prób: 2 połowy IS × 2 wersje zamknięć D1)
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": None, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": None, "waga": "seria"},
    {"rsi": (5, 25), "od": 1, "zakres": 1.5, "sl": None, "waga": "seria"},   # 4 = od pierwszego dnia (więcej transakcji)
    {"rsi": (5, 25), "od": 3, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (5, 20), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (3, 15), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (3, 15), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (2, 15), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (2, 15), "od": 3, "zakres": 1.5, "sl": 2.0, "waga": "seria"},
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": 2.0, "waga": "stala"},
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

PYRAMID = 3   # do 3 pozycji naraz w parze, jeden kierunek — kolejne dni wyprzedania dokładają (D-034)
EXITS = [{"kind": "level", "cap": c} for c in (3, 4, 5)]   # wyjście po 3 / 4 / 5 dniach na zamknięciu (albo wcześniej na SL)
# Stawka bazowa (% kapitału jako depozyt, × 30 nominału): do 3 pozycji w parze × 8 par z USD poruszających się razem.
SIZING = [1, 2, 3, 5]


def _streak(mask):
    """Która z kolei świeca w serii True (0 poza serią)."""
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def _setup(df, c, ind):
    close = df.close
    period, level = c["rsi"]
    r = np.array(ind.rsi(close, period), dtype=float)
    s200 = np.array(ind.sma(close, 200), dtype=float)
    px = np.array(close, dtype=float)
    with np.errstate(invalid="ignore"):
        zone_lo = (px > s200) & (r < level)            # wyprzedanie w trendzie wzrostowym
        zone_hi = (px < s200) & (r > 100 - level)      # wykupienie w trendzie spadkowym
    st_lo, st_hi = _streak(zone_lo), _streak(zone_hi)
    long_ = zone_lo & (st_lo >= c["od"])
    short = zone_hi & (st_hi >= c["od"])
    if c["zakres"] is not None:
        atr = np.array(ind.atr(df, 14), dtype=float)
        with np.errstate(invalid="ignore"):
            calm = np.array(df.high - df.low, dtype=float) < c["zakres"] * atr
        long_ &= calm
        short &= calm
    direction = long_.astype(int) - short.astype(int)
    streak = np.where(direction > 0, st_lo, np.where(direction < 0, st_hi, 0))
    return direction, streak


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    direction, streak = _setup(df, c, ind)
    w = np.clip(streak - c["od"] + 1, 1, 3).astype(float) if c["waga"] == "seria" else np.ones(len(df))
    return pd.Series(np.where(direction != 0, direction * w, 0.0), index=df.index)


def levels(df, p, ind):
    c = CONFIGS[p["cfg"]]
    tp = pd.Series(np.nan, index=df.index)
    sl = pd.Series(np.nan, index=df.index)
    if c["sl"] is None:                       # wyjście tylko po limicie dni (na zamknięciu)
        return pd.DataFrame({"tp": tp, "sl": sl})
    direction, _ = _setup(df, c, ind)
    d = pd.Series(np.where(direction != 0, direction, np.nan), index=df.index)
    sl = df.close - d * c["sl"] * ind.atr(df, 14)
    return pd.DataFrame({"tp": tp, "sl": sl})

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
