# Stocks — badanie metody rebalansowania (wersja 3)

Policzone 2026-11-22 · 4,374 konfiguracji · werdykt 🔴 2/5

## Dane i model

- Spółki (14): MU 6.0%, MSFT 14.0%, AAPL 10.0%, MO 6.0%, CVX 6.0%, JPM 6.0%, PM 6.0%, JNJ 6.0%, AMZN 12.0%, MMM 4.0%, NVDA 4.0%, SO 4.0%, GOOGL 10.0%, O 6.0%
- Pominięte (brak danych): —; odrzucone przez Apps Script: —
- Kapitał 12,300 USD · pasmo ±20% udziału docelowego · koszt 0.10% od strony transakcji
- Świece dzienne Yahoo od 2010-01-01 (ceny po splitach, dywidendy z dniem bez prawa), czyszczenie wersja 2
- Ocena na zamknięciu dnia sesji przed wtorkiem, wykonanie na otwarciu wtorku (święto → następny dzień sesji); spółka gra po roku notowań
- Odcinki: 2011-01-04 → IS do 2022-11-29 (621 tyg.) → OOS do 2026-11-17 (207 tyg.)
- Wybór: najwyższy IR tygodniowej nadwyżki nad stałym podziałem (co tydzień do celu), tylko na IS

## Zwycięzca

**obsunięcie od szczytu 252 dni · ranking · całe pasmo · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału** (`dd252|rank|full|s1|trend|h0.25`)

| odcinek | CAGR % | nadwyżka % r. | IR nadwyżki | Sharpe | maks. spadek % | obrót % r. |
|---|---|---|---|---|---|---|
| IS | +20.06 | +0.49 | 0.58 | 1.04 | -25.8 | 50 |
| OOS | +31.61 | +0.17 | 0.19 | 1.99 | -12.2 | 76 |
| stały podział IS | +19.48 | +0.00 | — | 1.01 | -26.6 | 110 |
| stały podział OOS | +31.39 | +0.00 | — | 1.99 | -12.1 | 136 |
| kup i trzymaj IS | +19.53 | +0.04 | — | 0.85 | -38.0 | 0 |
| kup i trzymaj OOS | +45.71 | +10.90 | — | 1.33 | -27.8 | 0 |

## Walidacja

| test | wynik | próg | |
|---|---|---|---|
| Nadwyżka nad stałym podziałem na OOS (% rocznie) | 0.17 | > 0 | ✓ |
| Percentyl wobec losowych przesunięć (OOS) | 78.80 | ≥ 95 | ✗ |
| Deflated Sharpe (IS, wszystkie próby) | 0.13 | ≥ 0.95 | ✗ |
| PBO (CSCV, cała historia) | 0.47 | < 0.3 | ✗ |
| Nadwyżka OOS przy koszcie × 2 (% rocznie) | 0.23 | > 0 | ✓ |

Bootstrap nadwyżki OOS: -0.72 … 1.24% rocznie. Mediana losowych przesunięć OOS: -0.12%. Konfiguracji z dodatnią nadwyżką OOS: 47% (mediana -0.02% r.).

## Najlepsze w rodzinach ocen (wybór po IS)

| ocena | IR IS | IR OOS | nadwyżka OOS % r. | konfiguracji z OOS > 0 |
|---|---|---|---|---|
| obsunięcie od szczytu 252 dni | 0.58 | 0.19 | +0.17 | 78% |
| odchylenie od średniej 120 dni (z) | 0.54 | 0.33 | +0.40 | 67% |
| odległość od średniej 200 dni | 0.50 | -0.10 | -0.11 | 30% |
| wynik 756 dni wobec reszty + wynik 21 dni wobec reszty | 0.49 | -0.68 | -0.83 | 38% |
| odległość od średniej 20 dni | 0.48 | 0.64 | +0.64 | 28% |
| RSI 14 | 0.48 | 0.22 | +0.21 | 40% |
| obsunięcie od szczytu 252 dni + wynik 21 dni wobec reszty | 0.47 | -0.12 | -0.18 | 51% |
| odchylenie od średniej 60 dni (z) | 0.47 | -0.26 | -0.25 | 67% |
| odchylenie od średniej 250 dni (z) | 0.45 | 0.06 | +0.06 | 69% |
| wynik 63 dni wobec reszty | 0.45 | -0.31 | -0.35 | 20% |
| wynik 21 dni wobec reszty | 0.44 | -0.40 | -0.44 | 20% |
| odchylenie od średniej 20 dni (z) | 0.40 | -0.48 | -0.56 | 38% |
| RSI 5 | 0.37 | -0.08 | -0.04 | 39% |
| wynik 5 dni wobec reszty | 0.37 | 0.14 | +0.15 | 22% |
| wynik 126 dni wobec reszty | 0.36 | 0.51 | +0.62 | 39% |
| odległość od średniej 100 dni | 0.36 | -0.26 | -0.27 | 20% |
| odległość od średniej 50 dni + obsunięcie od szczytu 126 dni | 0.35 | 0.51 | +0.55 | 48% |
| RSI 30 | 0.34 | 0.37 | +0.37 | 54% |
| obsunięcie od szczytu 126 dni | 0.30 | 0.08 | +0.10 | 72% |
| odległość od średniej 50 dni | 0.28 | 0.21 | +0.26 | 24% |
| obsunięcie od szczytu 63 dni | 0.28 | 0.01 | +0.01 | 69% |
| wynik 756 dni wobec reszty | 0.28 | -0.08 | -0.05 | 52% |
| wynik 252 dni wobec reszty | 0.25 | 0.34 | +0.20 | 36% |
| obsunięcie od szczytu 504 dni + RSI 14 | 0.24 | 0.63 | +0.72 | 87% |
| odchylenie od średniej 60 dni (z) + wynik 252 dni wobec reszty | 0.21 | -0.03 | -0.04 | 52% |
| odległość od średniej 200 dni + wynik 5 dni wobec reszty | 0.20 | 0.22 | +0.24 | 23% |
| obsunięcie od szczytu 504 dni | 0.17 | -0.11 | -0.07 | 91% |

## Top 25 po IS

| # | konfiguracja | IR IS | IR OOS | nadwyżka OOS % r. |
|---|---|---|---|---|
| 1 | obsunięcie od szczytu 252 dni · ranking · całe pasmo · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału | 0.58 | 0.19 | +0.17 |
| 2 | odchylenie od średniej 120 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.54 | 0.33 | +0.40 |
| 3 | odchylenie od średniej 120 dni (z) · z-score · pół pasma · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.54 | -0.19 | -0.23 |
| 4 | odległość od średniej 200 dni · ranking / zmienność · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.50 | -0.10 | -0.11 |
| 5 | wynik 756 dni wobec reszty + wynik 21 dni wobec reszty · ranking · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.49 | -0.68 | -0.83 |
| 6 | odległość od średniej 20 dni · ranking · pół pasma · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.48 | 0.64 | +0.64 |
| 7 | RSI 14 · ranking / zmienność · tylko skrajne · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.48 | 0.22 | +0.21 |
| 8 | obsunięcie od szczytu 252 dni + wynik 21 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · bez filtra · próg 25% udziału | 0.47 | -0.12 | -0.18 |
| 9 | odchylenie od średniej 60 dni (z) · ranking / zmienność · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.47 | -0.26 | -0.25 |
| 10 | odchylenie od średniej 250 dni (z) · z-score · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.45 | 0.06 | +0.06 |
| 11 | wynik 63 dni wobec reszty · ranking · pół pasma · ocena z tygodnia · dokładanie tylko w trendzie · próg 25% udziału | 0.45 | -0.31 | -0.35 |
| 12 | odchylenie od średniej 250 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.45 | 0.94 | +1.15 |
| 13 | wynik 21 dni wobec reszty · z-score · tylko skrajne · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.44 | -0.40 | -0.44 |
| 14 | obsunięcie od szczytu 252 dni · ranking · pół pasma · ocena z tygodnia · bez spadających noży · próg 25% udziału | 0.44 | -0.04 | -0.04 |
| 15 | odległość od średniej 20 dni · ranking / zmienność · pół pasma · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.42 | 0.00 | +0.01 |
| 16 | odchylenie od średniej 60 dni (z) · ranking / zmienność · pół pasma · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.41 | -0.14 | -0.17 |
| 17 | odchylenie od średniej 20 dni (z) · ranking · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.40 | -0.48 | -0.56 |
| 18 | odchylenie od średniej 250 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.39 | 0.48 | +0.55 |
| 19 | wynik 756 dni wobec reszty + wynik 21 dni wobec reszty · z-score · pół pasma · ocena z tygodnia · bez filtra · próg 10% udziału | 0.39 | -0.33 | -0.14 |
| 20 | odchylenie od średniej 120 dni (z) · ranking / zmienność · całe pasmo · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.39 | 0.12 | +0.15 |
| 21 | odchylenie od średniej 20 dni (z) · ranking · pół pasma · średnia z 4 tygodni · dokładanie tylko w trendzie · próg 25% udziału | 0.39 | -0.14 | -0.18 |
| 22 | odległość od średniej 200 dni · ranking / zmienność · pół pasma · średnia z 4 tygodni · bez filtra · próg 25% udziału | 0.38 | 0.21 | +0.20 |
| 23 | odległość od średniej 20 dni · ranking / zmienność · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 25% udziału | 0.37 | 0.97 | +1.04 |
| 24 | RSI 5 · z-score · pół pasma · średnia z 4 tygodni · bez spadających noży · próg 10% udziału | 0.37 | -0.08 | -0.04 |
| 25 | wynik 5 dni wobec reszty · ranking · pół pasma · ocena z tygodnia · bez filtra · próg 25% udziału | 0.37 | 0.14 | +0.15 |

## Lata (wynik %)

| rok | metoda | stały podział | kup i trzymaj |
|---|---|---|---|
| 2011 | +8.8 | +8.4 | +6.3 |
| 2012 | +18.7 | +18.1 | +17.0 |
| 2013 | +37.6 | +37.1 | +34.5 |
| 2014 | +14.9 | +15.7 | +15.8 |
| 2015 | +18.7 | +18.2 | +15.5 |
| 2016 | +28.3 | +27.2 | +26.8 |
| 2017 | +37.7 | +36.3 | +41.7 |
| 2018 | -1.7 | -2.8 | -4.2 |
| 2019 | +43.8 | +44.4 | +48.0 |
| 2020 | +28.1 | +27.1 | +47.3 |
| 2021 | +37.9 | +38.3 | +49.5 |
| 2022 | -19.0 | -20.3 | -36.1 |
| 2023 | +35.0 | +35.4 | +82.8 |
| 2024 | +37.0 | +35.1 | +97.1 |
| 2025 | +31.9 | +33.2 | +26.5 |
| 2026 | +25.3 | +24.7 | +3.0 |

## Znane ograniczenia

- Dane tylko z Yahoo: brak spółek, które zniknęły z giełdy (lista dzisiejszych spółek = błąd przetrwania, zawyża wszystkie warianty po równo).
- Backtest liczy udziały ciągłe; portfel na żywo — całe akcje (reszta w gotówce).
- Bez podatków; koszt stały 0,10% strony. Dywidendy reinwestowane przy następnym rebalansie.
- Każde ponowne liczenie (nowe udziały, nowe spółki) otwiera OOS jeszcze raz — liczba otwarć w dzienniku OOS.
