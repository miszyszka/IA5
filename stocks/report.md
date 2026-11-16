# Stocks — badanie metody rebalansowania (wersja 1)

Policzone 2026-11-16 · 4,374 konfiguracji · werdykt 🔴 0/5

## Dane i model

- Spółki (5): MU 14.3%, MSFT 33.3%, AAPL 23.8%, MO 14.3%, CVX 14.3%
- Pominięte (brak danych): JPM, PM, JNJ, AMZN, MMM, NVDA, SO, GOOGL, O; odrzucone przez Apps Script: —
- Kapitał 12,300 USD · pasmo ±20% udziału docelowego · koszt 0.10% od strony transakcji
- Świece dzienne Yahoo (ceny po splitach, dywidendy z dniem bez prawa), czyszczenie wersja 1
- Ocena na zamknięciu dnia sesji przed wtorkiem, wykonanie na otwarciu wtorku (święto → następny dzień sesji); spółka gra po roku notowań
- Odcinki: 1987-03-17 → IS do 2016-12-13 (1551 tyg.) → OOS do 2026-11-10 (517 tyg.)
- Wybór: najwyższy IR tygodniowej nadwyżki nad stałym podziałem (co tydzień do celu), tylko na IS

## Zwycięzca

**wynik 5 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · bez filtra · próg 10% udziału** (`rel5|zs|half|s1|none|h0.1`)

| odcinek | CAGR % | nadwyżka % r. | IR nadwyżki | Sharpe | maks. spadek % | obrót % r. |
|---|---|---|---|---|---|---|
| IS | +22.97 | +0.48 | 0.57 | 0.80 | -47.1 | 190 |
| OOS | +27.25 | -0.38 | -0.62 | 1.23 | -28.3 | 121 |
| stały podział IS | +22.38 | +0.00 | — | 0.78 | -47.7 | 149 |
| stały podział OOS | +27.73 | +0.00 | — | 1.25 | -28.5 | 121 |
| kup i trzymaj IS | +18.75 | -2.97 | — | 0.59 | -62.5 | 0 |
| kup i trzymaj OOS | +25.84 | -1.48 | — | 1.05 | -30.3 | 0 |

## Walidacja

| test | wynik | próg | |
|---|---|---|---|
| Nadwyżka nad stałym podziałem na OOS (% rocznie) | -0.38 | > 0 | ✗ |
| Percentyl wobec losowych przesunięć (OOS) | 20.80 | ≥ 95 | ✗ |
| Deflated Sharpe (IS, wszystkie próby) | 0.35 | ≥ 0.95 | ✗ |
| PBO (CSCV, cała historia) | 0.34 | < 0.3 | ✗ |
| Nadwyżka OOS przy koszcie × 2 (% rocznie) | -0.38 | > 0 | ✗ |

Bootstrap nadwyżki OOS: -0.70 … -0.06% rocznie. Mediana losowych przesunięć OOS: -0.13%. Konfiguracji z dodatnią nadwyżką OOS: 29% (mediana -0.18% r.).

## Najlepsze w rodzinach ocen (wybór po IS)

| ocena | IR IS | IR OOS | nadwyżka OOS % r. | konfiguracji z OOS > 0 |
|---|---|---|---|---|
| wynik 5 dni wobec reszty | 0.57 | -0.62 | -0.38 | 35% |
| odchylenie od średniej 120 dni (z) | 0.50 | 0.68 | +1.29 | 30% |
| obsunięcie od szczytu 126 dni | 0.47 | -0.11 | -0.08 | 27% |
| RSI 14 | 0.44 | -0.11 | -0.08 | 20% |
| odchylenie od średniej 20 dni (z) | 0.42 | -0.06 | -0.11 | 38% |
| RSI 5 | 0.42 | -0.29 | -0.46 | 28% |
| odchylenie od średniej 60 dni (z) + wynik 252 dni wobec reszty | 0.41 | 0.32 | +0.72 | 28% |
| odchylenie od średniej 60 dni (z) | 0.40 | 0.10 | +0.17 | 28% |
| wynik 63 dni wobec reszty | 0.39 | 0.17 | +0.30 | 19% |
| obsunięcie od szczytu 63 dni | 0.37 | -0.22 | -0.39 | 38% |
| odległość od średniej 100 dni | 0.36 | 0.25 | +0.37 | 20% |
| RSI 30 | 0.35 | 0.04 | +0.08 | 22% |
| obsunięcie od szczytu 504 dni | 0.33 | -0.14 | -0.13 | 38% |
| odległość od średniej 200 dni | 0.33 | 0.21 | +0.35 | 12% |
| odchylenie od średniej 250 dni (z) | 0.32 | 0.33 | +0.25 | 25% |
| obsunięcie od szczytu 252 dni | 0.32 | -0.51 | -0.42 | 23% |
| wynik 21 dni wobec reszty | 0.31 | 0.05 | +0.09 | 29% |
| obsunięcie od szczytu 252 dni + wynik 21 dni wobec reszty | 0.29 | 0.21 | +0.35 | 19% |
| odległość od średniej 50 dni + obsunięcie od szczytu 126 dni | 0.29 | -0.60 | -0.98 | 26% |
| obsunięcie od szczytu 504 dni + RSI 14 | 0.29 | 0.18 | +0.13 | 29% |
| odległość od średniej 20 dni | 0.28 | 0.21 | +0.18 | 36% |
| odległość od średniej 50 dni | 0.27 | -0.01 | -0.01 | 21% |
| odległość od średniej 200 dni + wynik 5 dni wobec reszty | 0.25 | 0.37 | +0.57 | 22% |
| wynik 756 dni wobec reszty + wynik 21 dni wobec reszty | 0.25 | 0.35 | +0.28 | 51% |
| wynik 252 dni wobec reszty | 0.23 | 0.67 | +1.50 | 18% |
| wynik 126 dni wobec reszty | 0.23 | -0.13 | -0.12 | 16% |
| wynik 756 dni wobec reszty | 0.19 | 0.45 | +1.02 | 88% |

## Top 25 po IS

| # | konfiguracja | IR IS | IR OOS | nadwyżka OOS % r. |
|---|---|---|---|---|
| 1 | wynik 5 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · bez filtra · próg 10% udziału | 0.57 | -0.62 | -0.38 |
| 2 | wynik 5 dni wobec reszty · z-score · tylko skrajne · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 10% udziału | 0.51 | -0.26 | -0.20 |
| 3 | odchylenie od średniej 120 dni (z) · ranking · pół pasma · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.50 | 0.68 | +1.29 |
| 4 | obsunięcie od szczytu 126 dni · ranking · pół pasma · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 10% udziału | 0.47 | -0.11 | -0.08 |
| 5 | RSI 14 · ranking · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 10% udziału | 0.44 | -0.11 | -0.08 |
| 6 | odchylenie od średniej 20 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.42 | -0.06 | -0.11 |
| 7 | RSI 5 · z-score · tylko skrajne · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału | 0.42 | -0.29 | -0.46 |
| 8 | odchylenie od średniej 60 dni (z) + wynik 252 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · bez spadających noży · próg 25% udziału | 0.41 | 0.32 | +0.72 |
| 9 | odchylenie od średniej 60 dni (z) · ranking · pół pasma · ocena z tygodnia · bez spadających noży · próg 25% udziału | 0.40 | 0.10 | +0.17 |
| 10 | wynik 63 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału | 0.39 | 0.17 | +0.30 |
| 11 | wynik 5 dni wobec reszty · z-score · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 10% udziału | 0.37 | 0.15 | +0.10 |
| 12 | obsunięcie od szczytu 63 dni · z-score · tylko skrajne · ocena z tygodnia · bez spadających noży · próg 25% udziału | 0.37 | -0.22 | -0.39 |
| 13 | odchylenie od średniej 120 dni (z) · z-score · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 10% udziału | 0.37 | -0.12 | -0.09 |
| 14 | odległość od średniej 100 dni · ranking · pół pasma · ocena z tygodnia · bez filtra · próg 25% udziału | 0.36 | 0.25 | +0.37 |
| 15 | odchylenie od średniej 120 dni (z) · ranking / zmienność · całe pasmo · ocena z tygodnia · bez spadających noży · próg 25% udziału | 0.36 | 0.15 | +0.23 |
| 16 | obsunięcie od szczytu 63 dni · z-score · pół pasma · średnia z 4 tygodni · bez filtra · próg 10% udziału | 0.36 | 0.17 | +0.13 |
| 17 | odchylenie od średniej 120 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 10% udziału | 0.35 | 0.05 | +0.06 |
| 18 | RSI 30 · z-score · całe pasmo · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.35 | 0.04 | +0.08 |
| 19 | RSI 30 · z-score · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 10% udziału | 0.34 | 0.33 | +0.21 |
| 20 | obsunięcie od szczytu 504 dni · z-score · pół pasma · średnia z 4 tygodni · bez filtra · próg 10% udziału | 0.33 | -0.14 | -0.13 |
| 21 | odchylenie od średniej 20 dni (z) · ranking / zmienność · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 10% udziału | 0.33 | -0.33 | -0.24 |
| 22 | odchylenie od średniej 120 dni (z) · ranking / zmienność · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 10% udziału | 0.33 | 0.11 | +0.09 |
| 23 | odchylenie od średniej 20 dni (z) · ranking · tylko skrajne · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.33 | -0.03 | -0.04 |
| 24 | odległość od średniej 200 dni · ranking · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału | 0.33 | 0.21 | +0.35 |
| 25 | odchylenie od średniej 250 dni (z) · ranking / zmienność · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 10% udziału | 0.32 | 0.33 | +0.25 |

## Lata (wynik %)

| rok | metoda | stały podział | kup i trzymaj |
|---|---|---|---|
| 1987 | +44.4 | +44.0 | +40.4 |
| 1988 | +3.2 | +2.8 | +0.3 |
| 1989 | +27.6 | +27.0 | +21.3 |
| 1990 | +42.7 | +39.5 | +40.4 |
| 1991 | +71.9 | +69.7 | +87.5 |
| 1992 | +8.8 | +9.3 | +7.6 |
| 1993 | +1.3 | +1.8 | +4.0 |
| 1994 | +48.0 | +46.7 | +62.9 |
| 1995 | +34.9 | +36.3 | +55.3 |
| 1996 | +18.5 | +18.4 | +39.4 |
| 1997 | +22.6 | +22.7 | +37.1 |
| 1998 | +101.1 | +97.1 | +105.3 |
| 1999 | +56.6 | +52.7 | +54.9 |
| 2000 | -30.9 | -32.1 | -52.3 |
| 2001 | +35.8 | +35.2 | +34.0 |
| 2002 | -26.8 | -27.0 | -25.1 |
| 2003 | +30.8 | +31.9 | +8.1 |
| 2004 | +39.2 | +38.8 | +7.2 |
| 2005 | +33.4 | +32.8 | +5.1 |
| 2006 | +21.0 | +20.1 | +15.8 |
| 2007 | +28.4 | +29.3 | +22.9 |
| 2008 | -35.0 | -35.9 | -40.3 |
| 2009 | +80.6 | +79.7 | +57.7 |
| 2010 | +12.5 | +12.8 | +3.2 |
| 2011 | +10.5 | +10.7 | +5.2 |
| 2012 | +15.4 | +14.8 | +13.2 |
| 2013 | +43.4 | +41.8 | +29.5 |
| 2014 | +34.4 | +33.1 | +33.6 |
| 2015 | -2.4 | -2.1 | +11.9 |
| 2016 | +26.6 | +26.5 | +18.4 |
| 2017 | +41.2 | +40.5 | +37.9 |
| 2018 | -5.1 | -4.8 | +5.4 |
| 2019 | +56.4 | +57.6 | +63.1 |
| 2020 | +29.9 | +30.1 | +41.4 |
| 2021 | +44.2 | +45.2 | +50.4 |
| 2022 | -17.1 | -16.5 | -26.3 |
| 2023 | +34.4 | +34.7 | +50.0 |
| 2024 | +24.1 | +25.3 | +19.4 |
| 2025 | +35.0 | +34.5 | +15.5 |
| 2026 | +46.3 | +47.2 | +26.2 |

## Znane ograniczenia

- Dane tylko z Yahoo: brak spółek, które zniknęły z giełdy (lista dzisiejszych spółek = błąd przetrwania, zawyża wszystkie warianty po równo).
- Backtest liczy udziały ciągłe; portfel na żywo — całe akcje (reszta w gotówce).
- Bez podatków; koszt stały 0,10% strony. Dywidendy reinwestowane przy następnym rebalansie.
- Każde ponowne liczenie (nowe udziały, nowe spółki) otwiera OOS jeszcze raz — liczba otwarć w dzienniku OOS.
