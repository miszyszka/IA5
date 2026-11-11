# REV — badanie metody (REV_VERSION 1, czyszczenie 1)

## Hipoteza i metoda

Kapitał w złotówkach rozkładany co wtorek 08:00 (cena: zamknięcie poniedziałku) na koszyki walut proporcjonalnie do oceny przeceny lub trendu, limit 50% na koszyk (waluta, blok o sztywnym kursie, PLN), pasmo 2 p.p., bez kosztów. Ceny względem łańcuchowego koszyka wszystkich koszyków (PLN też jest oceniany). Przecena = odchylenie od własnego trendu liniowego z 3/5 lat (ochrona przed pułapką inflacji), trend = zmiana z 3 mies. albo z roku bez ostatniego miesiąca; kombinacje = ½·z(przecena) + ½·z(trend 3 mies.). Zwycięzca wybrany tylko na IS (IR nadwyżki).

## Dane

- Koszyki (9): AUD, CHF, EUR, GBP, JPY, NZD, SGD, USD, PLN
- Bloki: USD (+HKD); EUR (+DKK)
- Odrzucone przy przyjęciu: ILS (Yahoo nie zwraca notowań), TRY (Yahoo nie zwraca notowań), CAD (Yahoo nie zwraca notowań), ZAR (Yahoo nie zwraca notowań), NOK (Yahoo nie zwraca notowań), CZK (Yahoo nie zwraca notowań), SEK (Yahoo nie zwraca notowań)
- Źródło: Yahoo `{WALUTA}PLN=X`, D1; warstwa czyszczenia tylko zamknięć (wyskoki, przeskalowania, powtórzenia).

## Odcinki

| Odcinek | Od | Do | Tygodnie |
|---|---|---|---|
| IS | 2010-07-20 | 2022-10-11 | 639 |
| OOS | po 2022-10-11 | 2026-11-10 | 213 |
| Na żywo | po 2026-11-10 | — | — |

Otwarcia OOS REV: 1.

## Warianty (13)

| Wariant | IR IS | Nadwyżka IS % r. | CAGR IS % | IR OOS | Nadwyżka OOS % r. | CAGR OOS % | Wzrost 52 tyg. OOS % | Lepszy od równego OOS % | Maks. spadek OOS % |
|---|---|---|---|---|---|---|---|---|---|
| V3-P Przecena 3 lata, proporcjonalnie | 0.15 | +0.61 | +2.53 | 1.07 | +2.87 | -0.27 | 59 | 96 | -12.9 |
| V3-R Przecena 3 lata, ranking | 0.06 | +0.25 | +2.16 | 1.08 | +2.95 | -0.19 | 57 | 100 | -12.2 |
| V5-P Przecena 5 lat, proporcjonalnie **(zwycięzca)** | 0.36 | +1.48 | +3.41 | 0.54 | +1.52 | -1.57 | 39 | 76 | -15.6 |
| V5-R Przecena 5 lat, ranking | 0.27 | +1.11 | +3.03 | 0.32 | +0.93 | -2.14 | 30 | 61 | -17.3 |
| M3-P Trend 3 mies., proporcjonalnie | -0.41 | -1.61 | +0.26 | -0.86 | -2.16 | -5.14 | 20 | 32 | -24.7 |
| M3-R Trend 3 mies., ranking | -0.39 | -1.44 | +0.43 | -0.70 | -1.74 | -4.74 | 20 | 37 | -23.7 |
| M12-P Trend 12 mies., proporcjonalnie | 0.12 | +0.44 | +2.35 | -0.35 | -0.89 | -3.91 | 17 | 55 | -19.9 |
| M12-R Trend 12 mies., ranking | 0.16 | +0.58 | +2.50 | -0.30 | -0.73 | -3.76 | 16 | 54 | -19.4 |
| V3M3-P Tania i przestała tanieć (3 lata), proporcjonalnie | -0.10 | -0.37 | +1.52 | 0.26 | +0.62 | -2.44 | 39 | 48 | -16.9 |
| V3M3-R Tania i przestała tanieć (3 lata), ranking | -0.24 | -0.83 | +1.06 | 0.24 | +0.56 | -2.50 | 40 | 45 | -16.7 |
| V5M3-P Tania i przestała tanieć (5 lat), proporcjonalnie | -0.04 | -0.17 | +1.73 | 0.02 | +0.05 | -3.00 | 23 | 50 | -17.7 |
| V5M3-R Tania i przestała tanieć (5 lat), ranking | -0.13 | -0.47 | +1.42 | -0.02 | -0.04 | -3.08 | 22 | 57 | -18.3 |
| SW Przełącznik (co 13 tygodni najlepszy z 3 lat) | 0.14 | +0.45 | +2.37 | -0.49 | -1.29 | -4.29 | 26 | 64 | -22.3 |

## Walidacja

| Test | Wynik | Próg | ✓ |
|---|---|---|---|
| Nadwyżka nad równym podziałem na OOS (% rocznie) | 1.52 | > 0 | ✓ |
| Percentyl wobec losowych podziałów (OOS) | 96.80 | ≥ 95 | ✓ |
| DSR (IS, 13 prób) | 0.43 | ≥ 0.95 | ✗ |
| PBO (CSCV, całość) | 0.29 | < 0.3 | ✓ |
| Nadwyżka przy wymianie dzień później (OOS, % rocznie) | 1.19 | > 0 | ✓ |

- Losowe podziały: 1000 ścieżek, nadwyżka OOS % r. p5 / p50 / p95: -1.30 / +0.04 / +1.31.
- Bootstrap blokowy (8 tyg.) 95% nadwyżki OOS % r.: -1.10 … +3.70 (212 tyg.).
- Maks. spadek z wyceny dziennej (cały okres): zwycięzca -21.9%, równy podział -21.4%.
- Zmian koszyka rocznie (zwycięzca): 168.

## Werdykt

🟡 4/5 — zwycięzca: V5-P (Przecena 5 lat, proporcjonalnie), zamrożony 2026-11-11, hash kodu `3e1696e13a3fbcd6`.

## Lata

| Rok | Zwycięzca % | Równy podział % |
|---|---|---|
| 2010 | +0.6 | -0.1 |
| 2011 | +19.9 | +14.2 |
| 2012 | -6.0 | -7.7 |
| 2013 | -11.5 | -3.7 |
| 2014 | +9.6 | +7.1 |
| 2015 | +9.9 | +3.7 |
| 2016 | +0.5 | +3.8 |
| 2017 | -9.2 | -10.0 |
| 2018 | +10.8 | +3.6 |
| 2019 | +4.4 | +1.5 |
| 2020 | +8.2 | +3.8 |
| 2021 | +4.8 | +3.4 |
| 2022 | +4.2 | +2.2 |
| 2023 | -8.5 | -7.8 |
| 2024 | +1.3 | -0.8 |
| 2025 | -6.2 | -6.6 |
| 2026 | +8.0 | +7.4 |

## Średnie udziały i wkład koszyków (zwycięzca, cały okres)

| Koszyk | Średni udział % | Wkład p.p. (log) |
|---|---|---|
| JPY | 14.6 | -1.5 |
| AUD | 13.8 | -0.5 |
| NZD | 12.5 | +3.3 |
| SGD | 11.5 | +13.6 |
| USD | 11.2 | +12.8 |
| CHF | 10.6 | +10.3 |
| EUR | 10.1 | -1.1 |
| PLN | 9.9 | +0.0 |
| GBP | 6.0 | -5.0 |

## Ograniczenia

- Wymiana po zamknięciu poniedziałku, a Michał wymienia we wtorek ok. 08:00 — test opóźnienia o dzień wyżej.
- Bez odsetek od sald, spreadów i opłat (R3) — waluty z wysoką stopą wyglądają gorzej niż na lokacie.
- Jedno źródło: Yahoo; rzadsze kursy mają gorszą historię; ok. 20 koszyków i kilkanaście lat to mała próba.
- Bloki o sztywnym kursie traktowane jak kotwica — pęknięcie kursu wykrywa kontrola zdrowia, nie badanie.

## Pytania do recenzenta

1. Czy przewaga zwycięzcy na IS ma sensowną przyczynę ekonomiczną, czy to szczęście wśród 13 prób?
2. Czy wynik nie stoi na jednej walucie lub jednym roku (tabele lat i wkładu)?
3. Czy wynik przetrwa wymianę dzień później i inne pasmo?
