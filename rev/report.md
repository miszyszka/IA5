# REV — badanie metody (REV_VERSION 2, czyszczenie 1)

## Hipoteza i metoda

Kapitał w złotówkach rozkładany co wtorek 08:00 (cena: zamknięcie poniedziałku) na koszyki walut proporcjonalnie do oceny przeceny lub trendu, limit 50% na koszyk (waluta, blok o sztywnym kursie, PLN), pasmo 2 p.p., bez kosztów. Ceny względem łańcuchowego koszyka wszystkich koszyków (PLN też jest oceniany). Przecena = odchylenie od własnego trendu liniowego z 3/5 lat (ochrona przed pułapką inflacji), trend = zmiana z 3 mies. albo z roku bez ostatniego miesiąca; kombinacje = ½·z(przecena) + ½·z(trend 3 mies.). Nakładki (D-065): zawór złotówkowy 26/52 tyg. i hamulec zmienności (PLN 75%, gdy złoty się umacnia albo kursy mocno skaczą), „nie sprzedawaj na stracie”. Zwycięzca wybrany tylko na IS: najwyższy Sharpe tygodniowych zwrotów kapitału w PLN.

## Dane

- Koszyki (9): AUD, CHF, EUR, GBP, JPY, NZD, SGD, USD, PLN
- Bloki: USD (+HKD); EUR (+DKK)
- Odrzucone przy przyjęciu: THB (Yahoo nie ma kursu THBPLN=X), SAR (Yahoo nie ma kursu SARPLN=X), TRY (Yahoo nie zwraca notowań), CAD (Yahoo nie zwraca notowań), ILS (Yahoo nie zwraca notowań), SEK (Yahoo nie zwraca notowań), HUF (Yahoo nie ma kursu HUFPLN=X), RON (Yahoo nie ma kursu RONPLN=X), NOK (Yahoo nie zwraca notowań), MXN (Yahoo nie ma kursu MXNPLN=X), ZAR (Yahoo nie zwraca notowań), QAR (Yahoo nie ma kursu QARPLN=X), AED (Yahoo nie ma kursu AEDPLN=X), CZK (Yahoo nie zwraca notowań)
- Źródło: Yahoo `{WALUTA}PLN=X`, D1; warstwa czyszczenia tylko zamknięć (wyskoki, przeskalowania, powtórzenia).

## Odcinki

| Odcinek | Od | Do | Tygodnie |
|---|---|---|---|
| IS | 2010-07-20 | 2022-10-11 | 639 |
| OOS | po 2022-10-11 | 2026-11-10 | 213 |
| Na żywo | po 2026-11-10 | — | — |

Otwarcia OOS REV: 2.

## Warianty (61) — od najwyższego Sharpe na IS

| Wariant | Sharpe IS | CAGR IS % | Nadwyżka IS % r. | Sharpe OOS | CAGR OOS % | Nadwyżka OOS % r. | Wzrost 52 tyg. OOS % | Maks. spadek OOS % | PLN 75% (% tyg.) |
|---|---|---|---|---|---|---|---|---|---|
| V5-P+Z52 Przecena 5 lat, proporcjonalnie + zawór złotówkowy 12 mies. **(zwycięzca)** | 0.44 | +3.17 | +1.24 | -0.12 | -0.35 | +2.79 | 21 | -6.7 | 43 |
| V5-P+H Przecena 5 lat, proporcjonalnie + hamulec zmienności | 0.41 | +3.37 | +1.44 | -0.29 | -1.86 | +1.23 | 37 | -16.6 | 6 |
| V5-P Przecena 5 lat, proporcjonalnie | 0.41 | +3.41 | +1.48 | -0.24 | -1.57 | +1.52 | 39 | -15.6 | 0 |
| V5-R+Z52 Przecena 5 lat, ranking + zawór złotówkowy 12 mies. | 0.40 | +2.92 | +1.00 | -0.15 | -0.44 | +2.69 | 20 | -7.2 | 43 |
| V5-P+S Przecena 5 lat, proporcjonalnie + nie sprzedawaj na stracie | 0.37 | +2.96 | +1.03 | -0.48 | -3.07 | -0.03 | 22 | -20.3 | 0 |
| V5-R+H Przecena 5 lat, ranking + hamulec zmienności | 0.37 | +3.05 | +1.12 | -0.37 | -2.39 | +0.68 | 29 | -18.2 | 6 |
| V3-P+Z52 Przecena 3 lata, proporcjonalnie + zawór złotówkowy 12 mies. | 0.37 | +2.59 | +0.67 | 0.02 | +0.06 | +3.21 | 37 | -4.7 | 43 |
| V5-R+S Przecena 5 lat, ranking + nie sprzedawaj na stracie | 0.36 | +2.82 | +0.90 | -0.31 | -1.77 | +1.32 | 40 | -15.4 | 0 |
| V5-R Przecena 5 lat, ranking | 0.35 | +3.03 | +1.11 | -0.33 | -2.14 | +0.93 | 30 | -17.3 | 0 |
| V3-R+S Przecena 3 lata, ranking + nie sprzedawaj na stracie | 0.34 | +2.63 | +0.72 | -0.18 | -1.05 | +2.06 | 37 | -12.9 | 0 |
| V3-R+Z52 Przecena 3 lata, ranking + zawór złotówkowy 12 mies. | 0.32 | +2.30 | +0.39 | 0.02 | +0.07 | +3.22 | 30 | -4.7 | 43 |
| V3-P+H Przecena 3 lata, proporcjonalnie + hamulec zmienności | 0.32 | +2.59 | +0.67 | -0.05 | -0.31 | +2.82 | 58 | -13.0 | 6 |
| V3-P Przecena 3 lata, proporcjonalnie | 0.30 | +2.53 | +0.61 | -0.04 | -0.27 | +2.87 | 59 | -12.9 | 0 |
| V5-P+Z26 Przecena 5 lat, proporcjonalnie + zawór złotówkowy 6 mies. | 0.29 | +1.88 | -0.02 | -0.33 | -0.94 | +2.17 | 17 | -8.4 | 47 |
| V3-R+H Przecena 3 lata, ranking + hamulec zmienności | 0.28 | +2.25 | +0.35 | -0.03 | -0.19 | +2.95 | 57 | -12.2 | 6 |
| M12-R+S Trend 12 mies., ranking + nie sprzedawaj na stracie | 0.28 | +2.48 | +0.57 | -0.64 | -3.09 | -0.05 | 20 | -19.2 | 0 |
| M12-R+Z52 Trend 12 mies., ranking + zawór złotówkowy 12 mies. | 0.28 | +2.39 | +0.47 | -0.56 | -1.77 | +1.31 | 12 | -11.2 | 43 |
| M12-P+S Trend 12 mies., proporcjonalnie + nie sprzedawaj na stracie | 0.28 | +2.46 | +0.55 | -0.63 | -3.27 | -0.23 | 20 | -19.9 | 0 |
| V3-P+S Przecena 3 lata, proporcjonalnie + nie sprzedawaj na stracie | 0.27 | +2.28 | +0.37 | -0.44 | -2.75 | +0.31 | 31 | -18.9 | 0 |
| M12-R Trend 12 mies., ranking | 0.27 | +2.50 | +0.58 | -0.84 | -3.76 | -0.73 | 16 | -19.4 | 0 |
| V3-R Przecena 3 lata, ranking | 0.26 | +2.16 | +0.25 | -0.03 | -0.19 | +2.95 | 57 | -12.2 | 0 |
| M12-P Trend 12 mies., proporcjonalnie | 0.25 | +2.35 | +0.44 | -0.85 | -3.91 | -0.89 | 17 | -19.9 | 0 |
| M12-R+H Trend 12 mies., ranking + hamulec zmienności | 0.25 | +2.13 | +0.23 | -0.82 | -3.64 | -0.61 | 16 | -19.0 | 6 |
| V5M3-R+S Tania i przestała tanieć (5 lat), ranking + nie sprzedawaj na stracie | 0.25 | +2.05 | +0.15 | -0.53 | -2.96 | +0.09 | 16 | -18.4 | 0 |
| V5-R+Z26 Przecena 5 lat, ranking + zawór złotówkowy 6 mies. | 0.25 | +1.67 | -0.23 | -0.34 | -0.99 | +2.12 | 19 | -9.0 | 47 |
| M12-P+H Trend 12 mies., proporcjonalnie + hamulec zmienności | 0.24 | +2.05 | +0.14 | -0.83 | -3.79 | -0.77 | 17 | -19.5 | 6 |
| M12-P+Z52 Trend 12 mies., proporcjonalnie + zawór złotówkowy 12 mies. | 0.23 | +2.02 | +0.11 | -0.55 | -1.76 | +1.33 | 16 | -11.1 | 43 |
| V3M3-P+H Tania i przestała tanieć (3 lata), proporcjonalnie + hamulec zmienności | 0.23 | +1.86 | -0.04 | -0.42 | -2.35 | +0.72 | 38 | -16.6 | 6 |
| V5M3-P+H Tania i przestała tanieć (5 lat), proporcjonalnie + hamulec zmienności | 0.21 | +1.74 | -0.16 | -0.50 | -3.07 | -0.02 | 22 | -18.0 | 6 |
| V5M3-P Tania i przestała tanieć (5 lat), proporcjonalnie | 0.20 | +1.73 | -0.17 | -0.48 | -3.00 | +0.05 | 23 | -17.7 | 0 |
| V5M3-P+Z52 Tania i przestała tanieć (5 lat), proporcjonalnie + zawór złotówkowy 12 mies. | 0.20 | +1.55 | -0.35 | -0.36 | -1.08 | +2.03 | 10 | -8.8 | 43 |
| V5M3-P+S Tania i przestała tanieć (5 lat), proporcjonalnie + nie sprzedawaj na stracie | 0.20 | +1.76 | -0.14 | -0.55 | -3.26 | -0.22 | 16 | -19.9 | 0 |
| V3M3-P+Z52 Tania i przestała tanieć (3 lata), proporcjonalnie + zawór złotówkowy 12 mies. | 0.19 | +1.41 | -0.48 | -0.31 | -0.95 | +2.16 | 23 | -8.3 | 43 |
| V3M3-P+S Tania i przestała tanieć (3 lata), proporcjonalnie + nie sprzedawaj na stracie | 0.19 | +1.62 | -0.27 | -0.55 | -3.20 | -0.16 | 14 | -17.7 | 0 |
| V3M3-P Tania i przestała tanieć (3 lata), proporcjonalnie | 0.18 | +1.52 | -0.37 | -0.43 | -2.44 | +0.62 | 39 | -16.9 | 0 |
| V3M3-R+H Tania i przestała tanieć (3 lata), ranking + hamulec zmienności | 0.18 | +1.45 | -0.44 | -0.43 | -2.38 | +0.68 | 40 | -16.3 | 6 |
| V5M3-R+H Tania i przestała tanieć (5 lat), ranking + hamulec zmienności | 0.18 | +1.47 | -0.43 | -0.52 | -3.18 | -0.13 | 22 | -18.6 | 6 |
| V5M3-R+Z52 Tania i przestała tanieć (5 lat), ranking + zawór złotówkowy 12 mies. | 0.18 | +1.34 | -0.55 | -0.37 | -1.12 | +1.99 | 11 | -8.8 | 43 |
| V3M3-R+S Tania i przestała tanieć (3 lata), ranking + nie sprzedawaj na stracie | 0.17 | +1.54 | -0.36 | -0.46 | -2.52 | +0.54 | 18 | -16.6 | 0 |
| V5M3-R Tania i przestała tanieć (5 lat), ranking | 0.17 | +1.42 | -0.47 | -0.50 | -3.08 | -0.04 | 22 | -18.3 | 0 |
| SW Przełącznik (co 13 tygodni najlepszy z 3 lat) | 0.16 | +1.16 | -0.73 | -0.50 | -1.77 | +1.32 | 21 | -13.3 | 31 |
| V3-P+Z26 Przecena 3 lata, proporcjonalnie + zawór złotówkowy 6 mies. | 0.14 | +0.88 | -1.01 | -0.11 | -0.28 | +2.86 | 29 | -5.8 | 47 |
| V3M3-R+Z52 Tania i przestała tanieć (3 lata), ranking + zawór złotówkowy 12 mies. | 0.14 | +1.01 | -0.88 | -0.29 | -0.89 | +2.23 | 23 | -8.1 | 43 |
| V3M3-R Tania i przestała tanieć (3 lata), ranking | 0.13 | +1.06 | -0.83 | -0.45 | -2.50 | +0.56 | 40 | -16.7 | 0 |
| V3-R+Z26 Przecena 3 lata, ranking + zawór złotówkowy 6 mies. | 0.10 | +0.63 | -1.25 | -0.13 | -0.33 | +2.80 | 23 | -6.1 | 47 |
| M3-P+S Trend 3 mies., proporcjonalnie + nie sprzedawaj na stracie | 0.08 | +0.70 | -1.18 | -0.73 | -3.96 | -0.94 | 16 | -22.2 | 0 |
| M3-R+S Trend 3 mies., ranking + nie sprzedawaj na stracie | 0.06 | +0.53 | -1.35 | -0.65 | -3.58 | -0.55 | 17 | -20.4 | 0 |
| M3-R+H Trend 3 mies., ranking + hamulec zmienności | 0.05 | +0.44 | -1.43 | -0.86 | -4.49 | -1.49 | 20 | -22.9 | 6 |
| V5M3-P+Z26 Tania i przestała tanieć (5 lat), proporcjonalnie + zawór złotówkowy 6 mies. | 0.05 | +0.36 | -1.52 | -0.46 | -1.35 | +1.75 | 10 | -11.1 | 47 |
| M3-R Trend 3 mies., ranking | 0.05 | +0.43 | -1.44 | -0.90 | -4.74 | -1.74 | 20 | -23.7 | 0 |
| M3-R+Z52 Trend 3 mies., ranking + zawór złotówkowy 12 mies. | 0.05 | +0.39 | -1.48 | -0.85 | -2.81 | +0.24 | 13 | -14.5 | 43 |
| M3-P+H Trend 3 mies., proporcjonalnie + hamulec zmienności | 0.03 | +0.27 | -1.60 | -0.92 | -4.84 | -1.85 | 20 | -23.7 | 6 |
| M3-P Trend 3 mies., proporcjonalnie | 0.03 | +0.26 | -1.61 | -0.96 | -5.14 | -2.16 | 20 | -24.7 | 0 |
| M3-P+Z52 Trend 3 mies., proporcjonalnie + zawór złotówkowy 12 mies. | 0.03 | +0.22 | -1.65 | -0.88 | -2.86 | +0.19 | 12 | -14.5 | 43 |
| M12-R+Z26 Trend 12 mies., ranking + zawór złotówkowy 6 mies. | 0.02 | +0.18 | -1.69 | -0.80 | -2.34 | +0.73 | 11 | -13.9 | 47 |
| V5M3-R+Z26 Tania i przestała tanieć (5 lat), ranking + zawór złotówkowy 6 mies. | 0.01 | +0.08 | -1.79 | -0.49 | -1.41 | +1.69 | 14 | -11.2 | 47 |
| M12-P+Z26 Trend 12 mies., proporcjonalnie + zawór złotówkowy 6 mies. | 0.00 | +0.03 | -1.84 | -0.75 | -2.28 | +0.79 | 17 | -13.7 | 47 |
| V3M3-P+Z26 Tania i przestała tanieć (3 lata), proporcjonalnie + zawór złotówkowy 6 mies. | -0.02 | -0.10 | -1.97 | -0.40 | -1.01 | +2.10 | 20 | -9.1 | 47 |
| V3M3-R+Z26 Tania i przestała tanieć (3 lata), ranking + zawór złotówkowy 6 mies. | -0.07 | -0.48 | -2.34 | -0.36 | -0.92 | +2.20 | 20 | -8.8 | 47 |
| M3-R+Z26 Trend 3 mies., ranking + zawór złotówkowy 6 mies. | -0.13 | -1.03 | -2.87 | -0.92 | -2.99 | +0.06 | 11 | -15.6 | 47 |
| M3-P+Z26 Trend 3 mies., proporcjonalnie + zawór złotówkowy 6 mies. | -0.15 | -1.15 | -2.99 | -0.95 | -3.11 | -0.06 | 9 | -16.0 | 47 |

## Walidacja

| Test | Wynik | Próg | ✓ |
|---|---|---|---|
| Nadwyżka nad równym podziałem na OOS (% rocznie) | 2.79 | > 0 | ✓ |
| Percentyl wobec losowych podziałów (OOS) | 100.00 | ≥ 95 | ✓ |
| DSR (IS, Sharpe w PLN, wszystkie próby) | 0.67 | ≥ 0.95 | ✗ |
| PBO (CSCV, całość) | 0.34 | < 0.3 | ✗ |
| Nadwyżka przy wymianie dzień później (OOS, % rocznie) | 2.58 | > 0 | ✓ |

- Losowe podziały: 1000 ścieżek, nadwyżka OOS % r. p5 / p50 / p95: -1.30 / +0.04 / +1.31.
- Bootstrap blokowy (8 tyg.) 95% nadwyżki OOS % r.: -0.62 … +5.80 (212 tyg.).
- Maks. spadek z wyceny dziennej (cały okres): zwycięzca -12.2%, równy podział -21.4%.
- Zmian koszyka rocznie (zwycięzca): 134.

## Werdykt

🟡 3/5 — zwycięzca: V5-P+Z52 (Przecena 5 lat, proporcjonalnie + zawór złotówkowy 12 mies.), zamrożony 2026-11-11, hash kodu `7298fefc2bb5c9a3`.

## Lata

| Rok | Zwycięzca % | Równy podział % |
|---|---|---|
| 2010 | +0.6 | -0.1 |
| 2011 | +15.6 | +14.2 |
| 2012 | -4.0 | -7.7 |
| 2013 | -4.4 | -3.7 |
| 2014 | +5.1 | +7.1 |
| 2015 | +10.0 | +3.7 |
| 2016 | +2.3 | +3.8 |
| 2017 | -4.1 | -10.0 |
| 2018 | +2.7 | +3.6 |
| 2019 | +2.8 | +1.5 |
| 2020 | +4.8 | +3.8 |
| 2021 | +4.9 | +3.4 |
| 2022 | +4.2 | +2.2 |
| 2023 | -1.9 | -7.8 |
| 2024 | -0.6 | -0.8 |
| 2025 | -1.8 | -6.6 |
| 2026 | +3.2 | +7.4 |

## Średnie udziały i wkład koszyków (zwycięzca, cały okres)

| Koszyk | Średni udział % | Wkład p.p. (log) |
|---|---|---|
| PLN | 41.4 | +0.0 |
| EUR | 9.6 | -1.4 |
| JPY | 9.1 | +5.3 |
| AUD | 7.8 | +4.9 |
| NZD | 7.4 | +3.7 |
| CHF | 7.1 | +8.6 |
| SGD | 6.6 | +9.1 |
| USD | 5.7 | +7.5 |
| GBP | 5.2 | -3.4 |

## Ograniczenia

- Wymiana po zamknięciu poniedziałku, a Michał wymienia we wtorek ok. 08:00 — test opóźnienia o dzień wyżej.
- Bez odsetek od sald, spreadów i opłat (R3) — waluty z wysoką stopą wyglądają gorzej niż na lokacie.
- Jedno źródło: Yahoo; rzadsze kursy mają gorszą historię; ok. 20 koszyków i kilkanaście lat to mała próba.
- Bloki o sztywnym kursie traktowane jak kotwica — pęknięcie kursu wykrywa kontrola zdrowia, nie badanie.

## Pytania do recenzenta

1. Czy przewaga zwycięzcy na IS ma sensowną przyczynę ekonomiczną, czy to szczęście wśród wszystkich prób?
2. Czy wynik nie stoi na jednej walucie lub jednym roku (tabele lat i wkładu)?
3. Czy wynik przetrwa wymianę dzień później i inne pasmo?
