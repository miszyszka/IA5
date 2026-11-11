# REV — badanie metody (REV_VERSION 2, czyszczenie 1)

## Hipoteza i metoda

Kapitał w złotówkach rozkładany co wtorek 08:00 (cena: zamknięcie poniedziałku) na koszyki walut proporcjonalnie do oceny przeceny lub trendu, limit 50% na koszyk (waluta, blok o sztywnym kursie, PLN), pasmo 2 p.p., bez kosztów. Ceny względem łańcuchowego koszyka wszystkich koszyków (PLN też jest oceniany). Przecena = odchylenie od własnego trendu liniowego z 3/5 lat (ochrona przed pułapką inflacji), trend = zmiana z 3 mies. albo z roku bez ostatniego miesiąca; kombinacje = ½·z(przecena) + ½·z(trend 3 mies.). Nakładki (D-065): zawór złotówkowy 26/52 tyg. i hamulec zmienności (PLN 75%, gdy złoty się umacnia albo kursy mocno skaczą), „nie sprzedawaj na stracie”. Zwycięzca wybrany tylko na IS: najwyższy Sharpe tygodniowych zwrotów kapitału w PLN.

## Dane

- Koszyki (16): AUD, CAD, CHF, CZK, EUR, GBP, HUF, JPY, MXN, NOK, NZD, SEK, TRY, USD, ZAR, PLN
- Bloki: USD (+HKD); EUR (+DKK)
- Odrzucone przy przyjęciu: QAR (historia od 2016-03-01 — krótsza niż 10 lat), SAR (ostatni kurs 2026-10-02 — Yahoo przestało notować)
- Źródło: Yahoo `{WALUTA}PLN=X`, D1; warstwa czyszczenia tylko zamknięć (wyskoki, przeskalowania, powtórzenia).

## Odcinki

| Odcinek | Od | Do | Tygodnie |
|---|---|---|---|
| IS | 2008-12-30 | 2022-04-19 | 695 |
| OOS | po 2022-04-19 | 2026-09-29 | 232 |
| Na żywo | po 2026-09-29 | — | — |

Otwarcia OOS REV: 1.

## Warianty (61) — od najwyższego Sharpe na IS

| Wariant | Sharpe IS | CAGR IS % | Nadwyżka IS % r. | Sharpe OOS | CAGR OOS % | Nadwyżka OOS % r. | Wzrost 52 tyg. OOS % | Maks. spadek OOS % | PLN 75% (% tyg.) |
|---|---|---|---|---|---|---|---|---|---|
| V5M3-R+Z26 Tania i przestała tanieć (5 lat), ranking + zawór złotówkowy 6 mies. **(zwycięzca)** | 0.44 | +0.74 | +2.41 | -0.93 | -1.18 | +1.19 | 16 | -6.4 | 78 |
| V3M3-R Tania i przestała tanieć (3 lata), ranking | 0.40 | +1.27 | +2.94 | 0.20 | +0.60 | +3.01 | 62 | -6.6 | 0 |
| V5M3-P+Z26 Tania i przestała tanieć (5 lat), proporcjonalnie + zawór złotówkowy 6 mies. | 0.40 | +0.71 | +2.37 | -0.75 | -0.98 | +1.39 | 22 | -5.8 | 78 |
| V3M3-R+H Tania i przestała tanieć (3 lata), ranking + hamulec zmienności | 0.39 | +1.22 | +2.89 | 0.17 | +0.51 | +2.91 | 57 | -7.0 | 1 |
| V3M3-R+Z26 Tania i przestała tanieć (3 lata), ranking + zawór złotówkowy 6 mies. | 0.39 | +0.64 | +2.30 | -0.39 | -0.44 | +1.94 | 32 | -4.2 | 78 |
| V3M3-P+Z26 Tania i przestała tanieć (3 lata), proporcjonalnie + zawór złotówkowy 6 mies. | 0.30 | +0.53 | +2.19 | -0.28 | -0.36 | +2.03 | 33 | -4.4 | 78 |
| V3M3-R+Z52 Tania i przestała tanieć (3 lata), ranking + zawór złotówkowy 12 mies. | 0.29 | +0.43 | +2.09 | -0.29 | -0.22 | +2.17 | 54 | -2.3 | 86 |
| V5M3-P Tania i przestała tanieć (5 lat), proporcjonalnie | 0.27 | +0.86 | +2.53 | -0.09 | -0.27 | +2.12 | 64 | -8.2 | 0 |
| V5M3-P+H Tania i przestała tanieć (5 lat), proporcjonalnie + hamulec zmienności | 0.27 | +0.85 | +2.52 | -0.13 | -0.39 | +1.99 | 59 | -8.4 | 1 |
| V5M3-R Tania i przestała tanieć (5 lat), ranking | 0.22 | +0.68 | +2.34 | -0.22 | -0.64 | +1.74 | 49 | -8.4 | 0 |
| V3M3-P Tania i przestała tanieć (3 lata), proporcjonalnie | 0.21 | +0.72 | +2.39 | 0.10 | +0.31 | +2.71 | 56 | -8.1 | 0 |
| V5M3-R+H Tania i przestała tanieć (5 lat), ranking + hamulec zmienności | 0.21 | +0.66 | +2.32 | -0.24 | -0.68 | +1.70 | 48 | -8.6 | 1 |
| M3-P+Z26 Trend 3 mies., proporcjonalnie + zawór złotówkowy 6 mies. | 0.20 | +0.36 | +2.02 | -0.17 | -0.22 | +2.17 | 41 | -2.8 | 78 |
| V5M3-P+Z52 Tania i przestała tanieć (5 lat), proporcjonalnie + zawór złotówkowy 12 mies. | 0.19 | +0.29 | +1.95 | -0.15 | -0.12 | +2.28 | 57 | -2.0 | 86 |
| V3M3-P+H Tania i przestała tanieć (3 lata), proporcjonalnie + hamulec zmienności | 0.19 | +0.64 | +2.30 | 0.09 | +0.29 | +2.69 | 57 | -8.2 | 1 |
| V3M3-P+Z52 Tania i przestała tanieć (3 lata), proporcjonalnie + zawór złotówkowy 12 mies. | 0.17 | +0.24 | +1.90 | -0.60 | -0.41 | +1.98 | 22 | -2.9 | 86 |
| V5M3-R+Z52 Tania i przestała tanieć (5 lat), ranking + zawór złotówkowy 12 mies. | 0.12 | +0.18 | +1.83 | -0.08 | -0.06 | +2.34 | 63 | -2.1 | 86 |
| M3-R+Z26 Trend 3 mies., ranking + zawór złotówkowy 6 mies. | 0.10 | +0.16 | +1.82 | -0.36 | -0.43 | +1.95 | 21 | -2.9 | 78 |
| M3-P+Z52 Trend 3 mies., proporcjonalnie + zawór złotówkowy 12 mies. | 0.05 | +0.08 | +1.73 | -0.36 | -0.27 | +2.12 | 47 | -2.1 | 86 |
| M3-R+Z52 Trend 3 mies., ranking + zawór złotówkowy 12 mies. | 0.03 | +0.04 | +1.69 | -0.17 | -0.13 | +2.26 | 44 | -2.0 | 86 |
| M12-R+S Trend 12 mies., ranking + nie sprzedawaj na stracie | -0.03 | -0.07 | +1.58 | -0.14 | -0.33 | +2.05 | 52 | -7.0 | 0 |
| M12-P+S Trend 12 mies., proporcjonalnie + nie sprzedawaj na stracie | -0.07 | -0.16 | +1.49 | -0.29 | -0.60 | +1.79 | 47 | -5.7 | 0 |
| M3-P+H Trend 3 mies., proporcjonalnie + hamulec zmienności | -0.08 | -0.26 | +1.39 | -0.02 | -0.07 | +2.33 | 51 | -6.5 | 1 |
| M3-P Trend 3 mies., proporcjonalnie | -0.09 | -0.30 | +1.35 | -0.02 | -0.06 | +2.33 | 51 | -6.5 | 0 |
| M3-R+H Trend 3 mies., ranking + hamulec zmienności | -0.10 | -0.31 | +1.33 | -0.07 | -0.18 | +2.21 | 46 | -6.7 | 1 |
| M3-R Trend 3 mies., ranking | -0.11 | -0.33 | +1.32 | -0.07 | -0.19 | +2.21 | 46 | -6.7 | 0 |
| M12-R+Z26 Trend 12 mies., ranking + zawór złotówkowy 6 mies. | -0.12 | -0.20 | +1.45 | -0.21 | -0.22 | +2.17 | 48 | -2.5 | 78 |
| V3-P+Z26 Przecena 3 lata, proporcjonalnie + zawór złotówkowy 6 mies. | -0.12 | -0.20 | +1.45 | -1.83 | -2.38 | -0.04 | 1 | -10.3 | 78 |
| V3-P Przecena 3 lata, proporcjonalnie | -0.15 | -0.50 | +1.15 | -1.30 | -4.07 | -1.77 | 11 | -17.6 | 0 |
| V5-P+Z26 Przecena 5 lat, proporcjonalnie + zawór złotówkowy 6 mies. | -0.15 | -0.26 | +1.39 | -1.91 | -2.90 | -0.58 | 0 | -12.7 | 78 |
| M12-P+Z26 Trend 12 mies., proporcjonalnie + zawór złotówkowy 6 mies. | -0.15 | -0.26 | +1.39 | -0.33 | -0.34 | +2.05 | 50 | -2.6 | 78 |
| V5M3-R+S Tania i przestała tanieć (5 lat), ranking + nie sprzedawaj na stracie | -0.15 | -0.39 | +1.25 | -0.91 | -2.07 | +0.27 | 17 | -11.2 | 0 |
| V5-R+Z26 Przecena 5 lat, ranking + zawór złotówkowy 6 mies. | -0.15 | -0.25 | +1.40 | -1.83 | -2.49 | -0.16 | 0 | -10.8 | 78 |
| V3-P+H Przecena 3 lata, proporcjonalnie + hamulec zmienności | -0.16 | -0.52 | +1.12 | -1.26 | -3.93 | -1.63 | 11 | -17.1 | 1 |
| V5M3-P+S Tania i przestała tanieć (5 lat), proporcjonalnie + nie sprzedawaj na stracie | -0.16 | -0.43 | +1.22 | -0.70 | -1.72 | +0.63 | 25 | -10.0 | 0 |
| V3-R+Z26 Przecena 3 lata, ranking + zawór złotówkowy 6 mies. | -0.17 | -0.28 | +1.37 | -1.59 | -1.97 | +0.38 | 1 | -8.9 | 78 |
| V5-P+Z52 Przecena 5 lat, proporcjonalnie + zawór złotówkowy 12 mies. | -0.19 | -0.29 | +1.36 | -1.19 | -0.89 | +1.48 | 11 | -4.9 | 86 |
| V5-R+Z52 Przecena 5 lat, ranking + zawór złotówkowy 12 mies. | -0.19 | -0.29 | +1.36 | -1.66 | -1.15 | +1.21 | 1 | -5.3 | 86 |
| V3-P+Z52 Przecena 3 lata, proporcjonalnie + zawór złotówkowy 12 mies. | -0.21 | -0.32 | +1.33 | -1.30 | -1.05 | +1.32 | 12 | -5.0 | 86 |
| V3-R Przecena 3 lata, ranking | -0.22 | -0.70 | +0.94 | -1.14 | -3.28 | -0.96 | 12 | -14.2 | 0 |
| V3-R+H Przecena 3 lata, ranking + hamulec zmienności | -0.23 | -0.74 | +0.90 | -1.12 | -3.24 | -0.92 | 13 | -14.1 | 1 |
| M12-P+H Trend 12 mies., proporcjonalnie + hamulec zmienności | -0.24 | -0.68 | +0.96 | -0.40 | -1.03 | +1.34 | 38 | -7.7 | 1 |
| M12-R+H Trend 12 mies., ranking + hamulec zmienności | -0.26 | -0.72 | +0.92 | -0.27 | -0.74 | +1.64 | 46 | -6.6 | 1 |
| M12-P Trend 12 mies., proporcjonalnie | -0.26 | -0.75 | +0.89 | -0.45 | -1.15 | +1.22 | 35 | -7.9 | 0 |
| V3-R+Z52 Przecena 3 lata, ranking + zawór złotówkowy 12 mies. | -0.26 | -0.39 | +1.25 | -1.20 | -0.85 | +1.53 | 9 | -4.2 | 86 |
| M12-P+Z52 Trend 12 mies., proporcjonalnie + zawór złotówkowy 12 mies. | -0.28 | -0.42 | +1.22 | -0.61 | -0.42 | +1.96 | 36 | -2.4 | 86 |
| M12-R Trend 12 mies., ranking | -0.29 | -0.83 | +0.81 | -0.29 | -0.78 | +1.59 | 46 | -6.8 | 0 |
| SW Przełącznik (co 13 tygodni najlepszy z 3 lat) | -0.33 | -0.83 | +0.81 | -0.04 | -0.10 | +2.29 | 54 | -7.0 | 22 |
| V3M3-R+S Tania i przestała tanieć (3 lata), ranking + nie sprzedawaj na stracie | -0.35 | -0.91 | +0.73 | -0.31 | -0.72 | +1.66 | 32 | -7.8 | 0 |
| V5-P+H Przecena 5 lat, proporcjonalnie + hamulec zmienności | -0.35 | -1.18 | +0.45 | -1.50 | -4.51 | -2.23 | 0 | -20.1 | 1 |
| V3M3-P+S Tania i przestała tanieć (3 lata), proporcjonalnie + nie sprzedawaj na stracie | -0.37 | -0.96 | +0.68 | -0.26 | -0.59 | +1.79 | 38 | -5.9 | 0 |
| V5-P Przecena 5 lat, proporcjonalnie | -0.38 | -1.26 | +0.38 | -1.53 | -4.63 | -2.34 | 0 | -20.5 | 0 |
| M3-P+S Trend 3 mies., proporcjonalnie + nie sprzedawaj na stracie | -0.38 | -0.88 | +0.76 | -0.41 | -0.87 | +1.50 | 39 | -6.2 | 0 |
| M12-R+Z52 Trend 12 mies., ranking + zawór złotówkowy 12 mies. | -0.42 | -0.60 | +1.04 | -0.60 | -0.46 | +1.93 | 28 | -2.7 | 86 |
| V5-R+H Przecena 5 lat, ranking + hamulec zmienności | -0.45 | -1.40 | +0.23 | -1.53 | -4.23 | -1.93 | 0 | -19.2 | 1 |
| M3-R+S Trend 3 mies., ranking + nie sprzedawaj na stracie | -0.46 | -1.06 | +0.57 | -0.27 | -0.58 | +1.80 | 44 | -4.1 | 0 |
| V5-R Przecena 5 lat, ranking | -0.46 | -1.44 | +0.19 | -1.52 | -4.20 | -1.90 | 0 | -19.0 | 0 |
| V5-R+S Przecena 5 lat, ranking + nie sprzedawaj na stracie | -0.88 | -2.68 | -1.07 | -0.71 | -2.32 | +0.02 | 9 | -13.5 | 0 |
| V5-P+S Przecena 5 lat, proporcjonalnie + nie sprzedawaj na stracie | -1.03 | -3.54 | -1.95 | -1.32 | -4.71 | -2.42 | 14 | -21.2 | 0 |
| V3-P+S Przecena 3 lata, proporcjonalnie + nie sprzedawaj na stracie | -1.05 | -3.44 | -1.84 | -1.22 | -3.96 | -1.66 | 27 | -18.9 | 0 |
| V3-R+S Przecena 3 lata, ranking + nie sprzedawaj na stracie | -1.08 | -3.15 | -1.55 | -1.83 | -5.00 | -2.73 | 0 | -22.0 | 0 |

## Walidacja

| Test | Wynik | Próg | ✓ |
|---|---|---|---|
| Nadwyżka nad równym podziałem na OOS (% rocznie) | 1.19 | > 0 | ✓ |
| Percentyl wobec losowych podziałów (OOS) | 90.00 | ≥ 95 | ✗ |
| DSR (IS, Sharpe w PLN, wszystkie próby) | 0.09 | ≥ 0.95 | ✗ |
| PBO (CSCV, całość) | 0.08 | < 0.3 | ✓ |
| Nadwyżka przy wymianie dzień później (OOS, % rocznie) | 1.22 | > 0 | ✓ |

- Losowe podziały: 50 ścieżek, nadwyżka OOS % r. p5 / p50 / p95: -1.39 / -0.09 / +1.80.
- Bootstrap blokowy (8 tyg.) 95% nadwyżki OOS % r.: -0.54 … +2.75 (231 tyg.).
- Maks. spadek z wyceny dziennej (cały okres): zwycięzca -6.8%, równy podział -28.5%.
- Zmian koszyka rocznie (zwycięzca): 140.

## Werdykt

🟡 3/5 — zwycięzca: V5M3-R+Z26 (Tania i przestała tanieć (5 lat), ranking + zawór złotówkowy 6 mies.), zamrożony 2026-09-30, hash kodu `7298fefc2bb5c9a3`.

## Lata

| Rok | Zwycięzca % | Równy podział % |
|---|---|---|
| 2008 | +0.0 | +0.1 |
| 2009 | +2.5 | -1.4 |
| 2010 | +1.7 | -3.3 |
| 2011 | -1.4 | -0.5 |
| 2012 | +3.9 | +2.2 |
| 2013 | +0.8 | -1.3 |
| 2014 | -2.8 | -6.7 |
| 2015 | +0.8 | +0.4 |
| 2016 | +0.4 | -0.0 |
| 2017 | -0.2 | -2.4 |
| 2018 | -1.2 | -4.5 |
| 2019 | +0.6 | -2.6 |
| 2020 | +1.7 | -1.1 |
| 2021 | +2.7 | +0.9 |
| 2022 | +0.2 | -3.9 |
| 2023 | +0.6 | -0.8 |
| 2024 | -4.1 | -0.3 |
| 2025 | -1.0 | -4.3 |
| 2026 | -0.6 | -2.1 |

## Średnie udziały i wkład koszyków (zwycięzca, cały okres)

| Koszyk | Średni udział % | Wkład p.p. (log) |
|---|---|---|
| PLN | 59.1 | +0.0 |
| CZK | 5.0 | +1.1 |
| CAD | 3.4 | +3.5 |
| EUR | 3.2 | -0.1 |
| ZAR | 3.2 | +0.1 |
| CHF | 3.1 | +4.1 |
| JPY | 3.0 | -0.1 |
| GBP | 3.0 | -2.5 |
| MXN | 2.8 | +0.2 |
| NOK | 2.8 | +0.0 |
| USD | 2.8 | -1.0 |
| SEK | 2.4 | -0.1 |
| AUD | 2.3 | +0.7 |
| HUF | 2.0 | -0.2 |
| NZD | 1.8 | -3.0 |
| TRY | 0.1 | -0.2 |

## Ograniczenia

- Wymiana po zamknięciu poniedziałku, a Michał wymienia we wtorek ok. 08:00 — test opóźnienia o dzień wyżej.
- Bez odsetek od sald, spreadów i opłat (R3) — waluty z wysoką stopą wyglądają gorzej niż na lokacie.
- Jedno źródło: Yahoo; rzadsze kursy mają gorszą historię; ok. 20 koszyków i kilkanaście lat to mała próba.
- Bloki o sztywnym kursie traktowane jak kotwica — pęknięcie kursu wykrywa kontrola zdrowia, nie badanie.

## Pytania do recenzenta

1. Czy przewaga zwycięzcy na IS ma sensowną przyczynę ekonomiczną, czy to szczęście wśród wszystkich prób?
2. Czy wynik nie stoi na jednej walucie lub jednym roku (tabele lat i wkładu)?
3. Czy wynik przetrwa wymianę dzień później i inne pasmo?
