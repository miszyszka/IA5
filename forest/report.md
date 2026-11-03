# FOREST (D-048) — las df61836bede1

- Silnik 0.8.0 · FOREST 1.0 · dane do 2026-11-03 · świece H1 Yahoo po czyszczeniu, 8 par.
- KUCIE 2024-10-28 – 2025-10-31; MAPY do 2026-05-03; OOS do 2026-11-03; LIVE później.
- Kandydaci: 300,000, po bramkach kucia 48,324, wybrani 1000 (limit |ρ| ≤ 0.6, rodzina ≤ 25%).
- Różnorodność: N_eff 60.9, średnia |ρ| 0.089, p95 0.264. Rodziny: {'sezonowość': 45, 'międzyrynkowe': 187, 'momentum': 246, 'zmienność': 80, 'kalendarz': 62, 'trend': 250, 'odwrócenie': 86, 'struktura': 44}.
- Parametry ustalone przed liczeniem, niedobierane: K = 151, min. map = 1000, z ≥ 1.0 (księga B). Depozyt 5% kapitału, dźwignia 30:1.

## Wnioski

- [bad] Inwestorzy na świecach, których nie widzieli (OOS): średnia trafność 49,43% (na danych bez przewagi 49,73%). Przewaga wymaga wyraźnie ponad 50%.
- [bad] Demokracja (OOS): −0,05 pipsa brutto na transakcję (t −0,1), −1,70 netto, wygrane 46,0%.
- [bad] Czy mapy przewidują wynik (OOS): korelacja rang z i wyniku +0,021, p = 0,135. Na razie brak dowodu, że mapy coś przewidują.
- [warn] Mapy kontra demokracja (OOS): −1,35 vs −1,70 pipsa netto na transakcję (928 vs 2064 transakcji).
- [warn] Reputacja kontra demokracja (OOS): −1,59 vs −1,70 pipsa netto na transakcję (2077 vs 2064 transakcji).
- [ok] Różnorodność: 1000 inwestorów to około 61 niezależnych głosów (średnia |korelacja| 0,089).

## Księgi

| księga | odcinek | transakcje | wygrane % | brutto | netto | t netto | t brutto | wynik USD |
|---|---|---|---|---|---|---|---|---|
| A Demokracja | MAPY | 2051 | 46.7 | 0.74 | -0.91 | -1.51 | 1.23 | -2976.98 |
| A Demokracja | OOS | 2064 | 46.0 | -0.05 | -1.7 | -2.96 | -0.09 | -2908.1 |
| B Mapy | MAPY | 786 | 44.9 | -0.83 | -2.49 | -2.7 | -0.9 | -2194.28 |
| B Mapy | OOS | 928 | 47.2 | 0.31 | -1.35 | -1.73 | 0.39 | -1179.82 |
| C Reputacja | MAPY | 2062 | 46.3 | -0.43 | -2.08 | -3.46 | -0.72 | -4429.98 |
| C Reputacja | OOS | 2077 | 48.0 | 0.06 | -1.59 | -2.78 | 0.11 | -2155.34 |

| księga | kapitał | wynik % | maks. obsunięcie % | zamknięte | otwarte | anulowane |
|---|---|---|---|---|---|---|
| A Demokracja | 4114.92 | -58.85 | -58.99 | 4115 | 0 | 3 |
| B Mapy | 6625.9 | -33.74 | -35.87 | 1714 | 0 | 9 |
| C Reputacja | 3414.69 | -65.85 | -66.08 | 4139 | 0 | 3 |

## Inwestorzy na świecach niewidzianych przy kuciu

| odcinek | decyzje | średnia trafność h=1…5 | p95 | ponad 50% | ponad 51% |
|---|---|---|---|---|---|
| MAPY | 10216 | [49.17, 49.39, 49.71, 49.82, 49.82] | [50.03, 50.53, 50.97, 51.15, 51.3] | 256 | 10 |
| OOS | 10277 | [48.97, 49.15, 49.61, 49.7, 49.71] | [50.05, 50.58, 51.28, 51.46, 51.59] | 260 | 42 |

### Test zerowy: to samo na danych bez przewagi (nasiono 1000)

- średnia CV kucia: prawdziwe 3.91, zerowe 3.05; najlepszy kandydat: prawdziwe 7.47, zerowe 5.24; po bramkach: prawdziwe 48,324, zerowe 25,090.
- MAPY: trafność [49.19, 49.72, 49.92, 49.88, 49.89], ponad 51%: 14.
- OOS: trafność [49.09, 49.83, 49.89, 49.88, 49.94], ponad 51%: 2.
- księga A MAPY: 2048 transakcji, brutto 0.36, netto -1.29.
- księga A OOS: 2061 transakcji, brutto 0.08, netto -1.57.
- księga B MAPY: 592 transakcji, brutto 0.93, netto -0.71.
- księga B OOS: 693 transakcji, brutto -0.3, netto -1.95.
- księga C MAPY: 2048 transakcji, brutto 0.36, netto -1.29.
- księga C OOS: 2061 transakcji, brutto 0.71, netto -0.94.
- mapy MAPY: ρ -0.0053, p 0.6782.
- mapy OOS: ρ -0.0073, p 0.5127.

## Co znaczy głos — MAPY (wszystkie decyzje, wirtualnie)

Razem: {'n': 10184, 'win': 47.4, 'gross': 0.71, 'net': -0.94, 't': -3.47, 't_gross': 2.62}
Uczenie: {'z_vs_wynik': {'n': 9152, 'rho': -0.0281, 'p': 0.0625}, 'przewaga_vs_wynik': {'n': 10184, 'rho': 0.0037, 'p': 0.8111}, 'g_map_vs_wynik': {'n': 9152, 'rho': -0.0191, 'p': 0.2429}}

### przewaga głosów

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 5% | 1625 | 46.0 | 0.22 | -1.43 | -2.0 |
| 5–10% | 1557 | 46.6 | 1.03 | -0.62 | -0.9 |
| 10–20% | 2846 | 49.0 | 1.38 | -0.27 | -0.54 |
| 20–30% | 2085 | 47.1 | 0.23 | -1.43 | -2.43 |
| ≥ 30% | 2071 | 47.4 | 0.42 | -1.22 | -2.02 |

### z podobnych map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 1798 | 48.4 | 1.38 | -0.28 | -0.43 |
| −2…−1 | 1945 | 49.2 | 1.08 | -0.57 | -0.84 |
| −1…0 | 2300 | 48.2 | 1.62 | -0.02 | -0.03 |
| 0…1 | 1884 | 46.1 | 0.1 | -1.54 | -2.48 |
| 1…2 | 941 | 45.7 | -0.37 | -2.04 | -2.45 |
| z ≥ 2 | 284 | 38.7 | -3.72 | -5.42 | -4.02 |

### najlepszy z (księga B, jej horyzont)

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 973 | 45.8 | 0.92 | -0.75 | -1.18 |
| −2…−1 | 1827 | 45.9 | -0.39 | -2.04 | -3.71 |
| −1…0 | 2551 | 47.7 | 1.64 | 0.01 | 0.02 |
| 0…1 | 2242 | 46.8 | 1.03 | -0.62 | -1.17 |
| 1…2 | 1162 | 46.0 | 0.1 | -1.56 | -2.25 |
| z ≥ 2 | 398 | 37.4 | -4.52 | -6.21 | -4.78 |

### dopasowanie do map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 65% | 2128 | 45.3 | -0.76 | -2.38 | -4.48 |
| 65–70% | 4378 | 47.0 | 0.93 | -0.73 | -1.79 |
| 70–75% | 2218 | 50.3 | 1.8 | 0.14 | 0.2 |
| ≥ 75% | 428 | 48.4 | 1.48 | -0.19 | -0.14 |

### horyzont

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| 1 św. | 0 | None | None | None | None |
| 2 św. | 0 | None | None | None | None |
| 3 św. | 2 | 100.0 | 19.66 | 17.91 | 1.54 |
| 4 św. | 19 | 36.8 | 1.41 | -0.33 | -0.12 |
| 5 św. | 10163 | 47.4 | 0.71 | -0.94 | -3.48 |

### kierunek

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| long | 5806 | 48.3 | 0.72 | -0.94 | -2.66 |
| short | 4378 | 46.3 | 0.7 | -0.94 | -2.23 |

### para

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| AUDUSD | 1273 | 46.2 | 0.43 | -1.27 | -2.39 |
| EURGBP | 1273 | 44.8 | 0.69 | -1.01 | -2.98 |
| EURJPY | 1273 | 51.5 | 4.5 | 2.4 | 2.17 |
| EURUSD | 1273 | 51.0 | -0.35 | -1.25 | -2.03 |
| GBPUSD | 1273 | 50.1 | 0.5 | -1.0 | -1.19 |
| USDCAD | 1273 | 41.8 | -2.2 | -4.2 | -6.67 |
| USDCHF | 1273 | 42.1 | -1.45 | -3.35 | -6.18 |
| USDJPY | 1273 | 51.9 | 3.58 | 2.18 | 1.94 |

## Co znaczy głos — OOS (wszystkie decyzje, wirtualnie)

Razem: {'n': 10243, 'win': 45.9, 'gross': -0.08, 'net': -1.73, 't': -6.92, 't_gross': -0.3}
Uczenie: {'z_vs_wynik': {'n': 10243, 'rho': 0.0211, 'p': 0.1349}, 'przewaga_vs_wynik': {'n': 10243, 'rho': 0.0159, 'p': 0.3718}, 'g_map_vs_wynik': {'n': 10243, 'rho': 0.012, 'p': 0.4413}}

### przewaga głosów

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 5% | 1462 | 45.2 | -0.34 | -1.98 | -3.12 |
| 5–10% | 1476 | 47.8 | 0.35 | -1.29 | -1.76 |
| 10–20% | 2937 | 44.6 | -0.99 | -2.63 | -5.52 |
| 20–30% | 2241 | 46.1 | 0.64 | -1.01 | -1.83 |
| ≥ 30% | 2127 | 46.7 | 0.32 | -1.36 | -2.87 |

### z podobnych map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 2024 | 44.8 | 0.09 | -1.56 | -3.29 |
| −2…−1 | 2225 | 43.9 | -0.72 | -2.37 | -4.81 |
| −1…0 | 2713 | 46.8 | 0.62 | -1.01 | -2.03 |
| 0…1 | 1964 | 46.7 | -0.58 | -2.24 | -3.21 |
| 1…2 | 983 | 47.0 | 0.02 | -1.64 | -2.24 |
| z ≥ 2 | 334 | 50.9 | 0.21 | -1.48 | -1.17 |

### najlepszy z (księga B, jej horyzont)

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 1023 | 39.3 | -0.44 | -2.09 | -4.33 |
| −2…−1 | 2025 | 42.5 | -0.16 | -1.81 | -4.3 |
| −1…0 | 2968 | 43.9 | 0.08 | -1.57 | -3.71 |
| 0…1 | 2502 | 45.3 | -0.71 | -2.36 | -4.86 |
| 1…2 | 1299 | 47.3 | 0.13 | -1.53 | -2.36 |
| z ≥ 2 | 447 | 49.4 | 0.9 | -0.8 | -0.78 |

### dopasowanie do map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 65% | 449 | 46.8 | 0.16 | -1.41 | -1.37 |
| 65–70% | 4383 | 45.0 | -0.68 | -2.31 | -6.16 |
| 70–75% | 3845 | 46.9 | 0.58 | -1.09 | -2.58 |
| ≥ 75% | 1566 | 45.8 | -0.06 | -1.74 | -2.79 |

### horyzont

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| 1 św. | 0 | None | None | None | None |
| 2 św. | 0 | None | None | None | None |
| 3 św. | 2 | 50.0 | 1.8 | 0.35 | 0.04 |
| 4 św. | 14 | 21.4 | -10.03 | -11.76 | -1.9 |
| 5 św. | 10227 | 46.0 | -0.06 | -1.71 | -6.86 |

### kierunek

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| long | 6171 | 47.7 | -0.35 | -2.01 | -6.55 |
| short | 4072 | 43.2 | 0.34 | -1.3 | -3.08 |

### para

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| AUDUSD | 1280 | 43.9 | -0.19 | -1.89 | -4.43 |
| EURGBP | 1281 | 38.5 | -0.63 | -2.33 | -8.97 |
| EURJPY | 1281 | 44.5 | -2.14 | -4.24 | -3.82 |
| EURUSD | 1281 | 46.8 | -0.84 | -1.74 | -3.18 |
| GBPUSD | 1281 | 45.7 | -0.93 | -2.43 | -3.41 |
| USDCAD | 1279 | 46.1 | -0.43 | -2.43 | -4.33 |
| USDCHF | 1279 | 51.4 | 1.57 | -0.33 | -0.65 |
| USDJPY | 1281 | 50.4 | 3.0 | 1.6 | 1.52 |

## Co znaczy głos — RAZEM (wszystkie decyzje, wirtualnie)

Razem: {'n': 20427, 'win': 46.7, 'gross': 0.32, 'net': -1.33, 't': -7.25, 't_gross': 1.72}
Uczenie: {'z_vs_wynik': {'n': 19395, 'rho': -0.0034, 'p': 0.7456}, 'przewaga_vs_wynik': {'n': 20427, 'rho': 0.0094, 'p': 0.3948}, 'g_map_vs_wynik': {'n': 19395, 'rho': -0.0038, 'p': 0.7511}}

### przewaga głosów

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 5% | 3087 | 45.6 | -0.05 | -1.69 | -3.51 |
| 5–10% | 3033 | 47.2 | 0.7 | -0.95 | -1.88 |
| 10–20% | 5783 | 46.8 | 0.18 | -1.47 | -4.25 |
| 20–30% | 4326 | 46.5 | 0.44 | -1.21 | -3.02 |
| ≥ 30% | 4198 | 47.0 | 0.37 | -1.29 | -3.37 |

### z podobnych map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 3822 | 46.5 | 0.7 | -0.96 | -2.45 |
| −2…−1 | 4170 | 46.4 | 0.12 | -1.53 | -3.72 |
| −1…0 | 5013 | 47.5 | 1.08 | -0.56 | -1.43 |
| 0…1 | 3848 | 46.4 | -0.25 | -1.9 | -4.05 |
| 1…2 | 1924 | 46.4 | -0.17 | -1.83 | -3.33 |
| z ≥ 2 | 618 | 45.3 | -1.6 | -3.29 | -3.56 |

### najlepszy z (księga B, jej horyzont)

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| z < −2 | 1996 | 42.5 | 0.22 | -1.44 | -3.63 |
| −2…−1 | 3852 | 44.1 | -0.27 | -1.92 | -5.61 |
| −1…0 | 5519 | 45.7 | 0.8 | -0.84 | -2.53 |
| 0…1 | 4744 | 46.0 | 0.11 | -1.53 | -4.29 |
| 1…2 | 2461 | 46.7 | 0.12 | -1.55 | -3.27 |
| z ≥ 2 | 845 | 43.8 | -1.66 | -3.35 | -4.08 |

### dopasowanie do map

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| < 65% | 2577 | 45.6 | -0.6 | -2.21 | -4.67 |
| 65–70% | 8761 | 46.0 | 0.13 | -1.52 | -5.49 |
| 70–75% | 6063 | 48.1 | 1.03 | -0.64 | -1.74 |
| ≥ 75% | 1994 | 46.4 | 0.27 | -1.41 | -2.46 |

### horyzont

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| 1 św. | 0 | None | None | None | None |
| 2 św. | 0 | None | None | None | None |
| 3 św. | 4 | 75.0 | 10.73 | 9.13 | 1.18 |
| 4 św. | 33 | 30.3 | -3.44 | -5.18 | -1.63 |
| 5 św. | 20390 | 46.7 | 0.32 | -1.33 | -7.21 |

### kierunek

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| long | 11977 | 48.0 | 0.17 | -1.49 | -6.38 |
| short | 8450 | 44.8 | 0.53 | -1.11 | -3.74 |

### para

| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |
|---|---|---|---|---|---|
| AUDUSD | 2553 | 45.0 | 0.12 | -1.58 | -4.64 |
| EURGBP | 2554 | 41.6 | 0.02 | -1.68 | -7.83 |
| EURJPY | 2554 | 48.0 | 1.17 | -0.93 | -1.19 |
| EURUSD | 2554 | 48.9 | -0.6 | -1.5 | -3.63 |
| GBPUSD | 2554 | 47.9 | -0.22 | -1.72 | -3.11 |
| USDCAD | 2552 | 44.0 | -1.31 | -3.31 | -7.85 |
| USDCHF | 2552 | 46.8 | 0.06 | -1.84 | -4.93 |
| USDJPY | 2554 | 51.1 | 3.29 | 1.89 | 2.45 |

## Jak to czytać

- Wynik MAPY to część IS (W1), OOS to ostatnie 25% historii, LIVE to nowe świece. Rozstrzyga LIVE.
- Księga A jest grupą kontrolną: handluje zawsze, więc pokazuje pełny koszt spreadu. Mapy mają sens tylko wtedy, gdy B albo C biją A poza próbą.
- t liczone na transakcji zakłada ich niezależność; decyzje na kolejnych świecach i parach są zależne, więc prawdziwa pewność jest niższa. p przy mapach pochodzi z obrotów w czasie i ten problem omija.
- Nie dobieraj K, progu z ani okresu do wyniku OOS. Każda taka zmiana robi z OOS kolejne IS.