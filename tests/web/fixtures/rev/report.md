# REV — badanie metody (REV_VERSION 1, czyszczenie 1)

## Hipoteza i metoda

Kapitał w złotówkach rozkładany co wtorek 08:00 (cena: zamknięcie poniedziałku) na koszyki walut proporcjonalnie do oceny przeceny lub trendu, limit 50% na koszyk (waluta, blok o sztywnym kursie, PLN), pasmo 2 p.p., bez kosztów. Ceny względem łańcuchowego koszyka wszystkich koszyków (PLN też jest oceniany). Przecena = odchylenie od własnego trendu liniowego z 3/5 lat (ochrona przed pułapką inflacji), trend = zmiana z 3 mies. albo z roku bez ostatniego miesiąca; kombinacje = ½·z(przecena) + ½·z(trend 3 mies.). Zwycięzca wybrany tylko na IS (IR nadwyżki).

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

## Warianty (13)

| Wariant | IR IS | Nadwyżka IS % r. | CAGR IS % | IR OOS | Nadwyżka OOS % r. | CAGR OOS % | Wzrost 52 tyg. OOS % | Lepszy od równego OOS % | Maks. spadek OOS % |
|---|---|---|---|---|---|---|---|---|---|
| V3-P Przecena 3 lata, proporcjonalnie | 0.46 | +1.15 | -0.50 | -0.70 | -1.77 | -4.07 | 11 | 36 | -17.6 |
| V3-R Przecena 3 lata, ranking | 0.41 | +0.94 | -0.70 | -0.43 | -0.96 | -3.28 | 12 | 45 | -14.2 |
| V5-P Przecena 5 lat, proporcjonalnie | 0.14 | +0.38 | -1.26 | -0.93 | -2.34 | -4.63 | 0 | 32 | -20.5 |
| V5-R Przecena 5 lat, ranking | 0.08 | +0.19 | -1.44 | -0.88 | -1.90 | -4.20 | 0 | 24 | -19.0 |
| M3-P Trend 3 mies., proporcjonalnie | 0.50 | +1.35 | -0.30 | 1.02 | +2.33 | -0.06 | 51 | 97 | -6.5 |
| M3-R Trend 3 mies., ranking | 0.53 | +1.32 | -0.33 | 0.99 | +2.21 | -0.19 | 46 | 93 | -6.7 |
| M12-P Trend 12 mies., proporcjonalnie | 0.36 | +0.89 | -0.75 | 0.59 | +1.22 | -1.15 | 35 | 76 | -7.9 |
| M12-R Trend 12 mies., ranking | 0.35 | +0.81 | -0.83 | 0.68 | +1.59 | -0.78 | 46 | 93 | -6.8 |
| V3M3-P Tania i przestała tanieć (3 lata), proporcjonalnie | 0.87 | +2.39 | +0.72 | 1.07 | +2.71 | +0.31 | 56 | 86 | -8.1 |
| V3M3-R Tania i przestała tanieć (3 lata), ranking **(zwycięzca)** | 1.19 | +2.94 | +1.27 | 1.22 | +3.01 | +0.60 | 62 | 89 | -6.6 |
| V5M3-P Tania i przestała tanieć (5 lat), proporcjonalnie | 0.97 | +2.53 | +0.86 | 0.81 | +2.12 | -0.27 | 64 | 84 | -8.2 |
| V5M3-R Tania i przestała tanieć (5 lat), ranking | 0.96 | +2.34 | +0.68 | 0.72 | +1.74 | -0.64 | 49 | 77 | -8.4 |
| SW Przełącznik (co 13 tygodni najlepszy z 3 lat) | 0.43 | +0.97 | -0.67 | 1.10 | +2.70 | +0.30 | 62 | 90 | -6.6 |

## Walidacja

| Test | Wynik | Próg | ✓ |
|---|---|---|---|
| Nadwyżka nad równym podziałem na OOS (% rocznie) | 3.01 | > 0 | ✓ |
| Percentyl wobec losowych podziałów (OOS) | 100.00 | ≥ 95 | ✓ |
| DSR (IS, 13 prób) | 0.99 | ≥ 0.95 | ✓ |
| PBO (CSCV, całość) | 0.04 | < 0.3 | ✓ |
| Nadwyżka przy wymianie dzień później (OOS, % rocznie) | 2.35 | > 0 | ✓ |

- Losowe podziały: 50 ścieżek, nadwyżka OOS % r. p5 / p50 / p95: -1.39 / -0.09 / +1.80.
- Bootstrap blokowy (8 tyg.) 95% nadwyżki OOS % r.: +0.74 … +5.16 (231 tyg.).
- Maks. spadek z wyceny dziennej (cały okres): zwycięzca -10.0%, równy podział -28.5%.
- Zmian koszyka rocznie (zwycięzca): 295.

## Werdykt

🟢 5/5 — zwycięzca: V3M3-R (Tania i przestała tanieć (3 lata), ranking), zamrożony 2026-09-30, hash kodu `45571efe01ad64b1`.

## Lata

| Rok | Zwycięzca % | Równy podział % |
|---|---|---|
| 2008 | +0.2 | +0.1 |
| 2009 | +5.4 | -1.4 |
| 2010 | -2.4 | -3.3 |
| 2011 | +0.3 | -0.5 |
| 2012 | +3.9 | +2.2 |
| 2013 | +3.4 | -1.3 |
| 2014 | -5.7 | -6.7 |
| 2015 | +1.3 | +0.4 |
| 2016 | -0.2 | -0.0 |
| 2017 | +3.3 | -2.4 |
| 2018 | -1.7 | -4.5 |
| 2019 | -0.2 | -2.6 |
| 2020 | +3.9 | -1.1 |
| 2021 | +5.4 | +0.9 |
| 2022 | +2.3 | -3.9 |
| 2023 | +5.2 | -0.8 |
| 2024 | +1.3 | -0.3 |
| 2025 | -2.1 | -4.3 |
| 2026 | -3.2 | -2.1 |

## Średnie udziały i wkład koszyków (zwycięzca, cały okres)

| Koszyk | Średni udział % | Wkład p.p. (log) |
|---|---|---|
| PLN | 9.6 | +0.0 |
| CZK | 9.4 | +8.6 |
| CAD | 8.9 | +2.3 |
| CHF | 7.7 | +2.1 |
| ZAR | 6.8 | +3.4 |
| USD | 6.7 | +4.9 |
| GBP | 6.7 | -1.2 |
| AUD | 6.4 | -0.2 |
| NOK | 6.3 | -1.0 |
| EUR | 6.3 | -0.5 |
| JPY | 6.0 | -1.2 |
| MXN | 5.6 | +0.0 |
| SEK | 5.5 | -0.0 |
| HUF | 4.5 | -0.9 |
| NZD | 3.5 | -0.7 |
| TRY | 0.1 | -0.6 |

## Ograniczenia

- Wymiana po zamknięciu poniedziałku, a Michał wymienia we wtorek ok. 08:00 — test opóźnienia o dzień wyżej.
- Bez odsetek od sald, spreadów i opłat (R3) — waluty z wysoką stopą wyglądają gorzej niż na lokacie.
- Jedno źródło: Yahoo; rzadsze kursy mają gorszą historię; ok. 20 koszyków i kilkanaście lat to mała próba.
- Bloki o sztywnym kursie traktowane jak kotwica — pęknięcie kursu wykrywa kontrola zdrowia, nie badanie.

## Pytania do recenzenta

1. Czy przewaga zwycięzcy na IS ma sensowną przyczynę ekonomiczną, czy to szczęście wśród 13 prób?
2. Czy wynik nie stoi na jednej walucie lub jednym roku (tabele lat i wkładu)?
3. Czy wynik przetrwa wymianę dzień później i inne pasmo?
