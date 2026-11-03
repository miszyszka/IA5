# Głębokie poszukiwanie (D-044) — siatka „gigant”

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY · świece H1 Yahoo po czyszczeniu · silnik 0.8.0 · 74.8 min.
- IS-A (odkrycie): 2024-10-28 – 2025-10-31; IS-B (potwierdzenie): do 2026-05-03; OOS: 2026-05-03 – 2026-11-03.
- **Przetestowane konfiguracje: 3,124,224** (jedna konfiguracja = te same zasady na wszystkich parach); z ≥ 60 transakcji w IS-A i ≥ 30 w IS-B: 598,718.
- Próg odkrycia po FDR 5%: żadna konfiguracja go nie przeszła — najlepsza musiałaby mieć t IS-A ≥ 5.23, najlepsza ma 4.55; odkrytych: 0; potwierdzonych w IS-B: 0; wszystkie bramki IS (też ≥ 5/8 par na plusie i płaskowyż): **0**.
- Ranking i wybór wyłącznie na IS (W1). Liczba konfiguracji otwartych na OOS ustalona przed liczeniem: **20**.

> OOS tych danych otwierano już 1 raz(y) (ten raz wliczony) — każde kolejne spojrzenie obniża jego wartość jako testu.

## Test zerowy: to samo poszukiwanie na danych bez przewagi

- 30 przebiegów na świecach odbitych losowo (zostaje zmienność, znika kierunek). Najlepszy wynik IS (min t IS-A, t IS-B) prawdziwych danych: **2.91**; w przebiegach zerowych: mediana 2.49, max 3.39.
- Przebiegi zerowe z wynikiem ≥ prawdziwego: **2 z 30** (p ≈ 0.10). Duża liczba = najlepsza konfiguracja nie odróżnia się od szczęścia.
- Konfiguracje ze wszystkimi bramkami IS: prawdziwe dane 0, zerowe 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.

## Wynik na OOS (wszystkie wybrane, także przegrane)

- Dodatnich na OOS: **5 z 20** (gdyby to był czysty przypadek: P(≥ 5) = 0.994; konfiguracje są ze sobą skorelowane, więc ta liczba jest optymistyczna).
- Średnio na OOS: -0.348 R na transakcję vs +0.920 R (gorsza z połówek IS) — spadek z IS do OOS to typowa miara przeuczenia.
- Korelacja rangi IS z wynikiem OOS: -0.14 (ujemna = ranking IS nic nie przewiduje).
- Deflated Sharpe najlepszej konfiguracji IS: **0.388** przy 598,718 próbach (Sharpe na transakcję 0.383, próg szczęścia 0.407).

| # IS | konfiguracja | bramki IS | n A | R A | t A | n B | R B | t B | płaskowyż | n OOS | R OOS | t OOS | pips OOS | pary + OOS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | bollinger(n=20, k=3.0) przeciw sygnałowi · sesja 13-17 · long → po 96 świecach | ✗ | 76 | +2.087 | 3.0 | 41 | +3.127 | 2.9 | 67% | 44 | -1.250 | -1.1 | -10.5 | 4/8 |
| 2 | rsi(n=5, lvl=20) przeciw sygnałowi · sesja 07-10 · wt-czw · short → ATR14 TP 0.75× SL 3× max 120 | ✗ | 102 | +0.101 | 2.9 | 37 | +0.135 | 2.8 | 33% | 53 | -0.185 | -2.4 | -7.3 | 3/8 |
| 3 | impuls(k=1, th=1.5) za sygnałem · sesja 07-10 · long → po 8 świecach | ✗ | 79 | +0.898 | 3.0 | 35 | +1.160 | 2.7 | 60% | 28 | +0.567 | 1.4 | +7.2 | 6/7 |
| 4 | macd(f=5, w=35, s=5) za sygnałem · przeciw_ema200 · sesja 07-10 → po 48 świecach | ✗ | 284 | +0.889 | 2.7 | 144 | +1.081 | 2.7 | 60% | 130 | -0.611 | -1.3 | -4.7 | 1/8 |
| 5 | duza(x=2.5) przeciw sygnałowi · przeciw_ema200 · sesja 13-17 → po 48 świecach | ✗ | 104 | +1.218 | 2.6 | 30 | +2.016 | 2.9 | 67% | 59 | -0.152 | -0.2 | -10.1 | 5/8 |
| 6 | impuls(k=6, th=1.0) za sygnałem · przeciw_ema200 → po 48 świecach | ✗ | 211 | +0.944 | 2.8 | 99 | +1.337 | 2.6 | 80% | 97 | -0.502 | -0.8 | -4.1 | 4/8 |
| 7 | impuls(k=3, th=1.0) przeciw sygnałowi · przeciw_ema200 · ruch · sesja 13-17 → ATR14 TP 1.5× SL 2× max 120 | ✗ | 68 | +0.245 | 2.6 | 32 | +0.478 | 4.6 | 57% | 43 | +0.046 | 0.4 | +2.0 | 5/8 |
| 8 | duza(x=1.5) za sygnałem · sesja 07-10 → po 8 świecach | ✗ | 216 | +0.513 | 2.7 | 87 | +0.689 | 2.5 | 75% | 79 | +0.443 | 1.8 | +6.2 | 7/8 |
| 9 | wstega(s=3,5,8,13,21) za sygnałem · przeciw_ema200 · long → po 96 świecach | ✗ | 159 | +1.407 | 2.5 | 65 | +1.731 | 2.7 | 67% | 69 | -0.157 | -0.2 | +6.9 | 4/8 |
| 10 | macd(f=5, w=26, s=9) za sygnałem · przeciw_ema200 · ruch → po 12 świecach | ✗ | 71 | +0.625 | 2.5 | 50 | +1.233 | 2.5 | 80% | 43 | +0.144 | 0.4 | -13.1 | 5/7 |
| 11 | rsi(n=14, lvl=30) przeciw sygnałowi · sesja 10-13 · wt-czw → ATR14 TP 1.5× SL 2× max 120 | ✗ | 105 | +0.189 | 2.4 | 53 | +0.283 | 2.8 | 67% | 41 | -0.103 | -0.7 | -2.9 | 5/8 |
| 12 | bollinger(n=50, k=2.0) przeciw sygnałowi · zgodny_sma480 · sesja 13-17 · long → po 4 świecach | ✗ | 80 | +0.593 | 3.7 | 46 | +0.600 | 2.4 | 80% | 29 | -1.689 | -2.6 | -25.1 | 0/8 |
| 13 | macd(f=12, w=26, s=5) za sygnałem · przeciw_ema200 · ruch → po 12 świecach | ✗ | 62 | +0.670 | 2.4 | 44 | +1.345 | 2.4 | 60% | 34 | -0.098 | -0.2 | -11.6 | 3/7 |
| 14 | bollinger(n=50, k=2.0) za sygnałem · przeciw_ema200 → po 48 świecach | ✗ | 91 | +1.206 | 2.4 | 64 | +1.430 | 2.5 | 80% | 55 | -0.230 | -0.3 | -5.0 | 3/8 |
| 15 | duza(x=1.5) przeciw sygnałowi · przeciw_ema200 · sesja 10-13 · long → po 48 świecach | ✗ | 99 | +1.501 | 2.9 | 48 | +1.547 | 2.3 | 75% | 56 | -0.745 | -0.7 | -8.0 | 2/7 |
| 16 | rsi(n=3, lvl=10) przeciw sygnałowi · przeciw_ema200 → po 48 świecach | ✗ | 312 | +0.671 | 2.4 | 143 | +0.856 | 2.2 | 83% | 142 | -0.171 | -0.4 | -0.9 | 3/8 |
| 17 | donchian(n=12) za sygnałem · przeciw_ema200 · sesja 13-17 · wt-czw · long → po 96 świecach | ✗ | 62 | +1.859 | 2.2 | 36 | +2.069 | 2.4 | 50% | 27 | -0.564 | -0.5 | +1.3 | 4/8 |
| 18 | przeciecie(typ=ema, f=5, w=50) za sygnałem · przeciw_ema200 · sesja 10-13 → po 48 świecach | ✗ | 122 | +1.024 | 2.1 | 56 | +1.191 | 2.4 | 60% | 60 | +0.600 | 0.8 | +5.2 | 4/8 |
| 19 | seria(n=4) przeciw sygnałowi · zgodny_sma480 · sesja 13-17 → po 2 świecach | ✗ | 191 | +0.228 | 2.2 | 93 | +0.261 | 2.1 | 33% | 69 | -0.200 | -0.9 | -2.7 | 3/8 |
| 20 | donchian(n=24) przeciw sygnałowi · przeciw_ema200 · sesja 13-17 · wt-czw · long → po 96 świecach | ✗ | 130 | +1.523 | 2.4 | 56 | +1.538 | 2.1 | 100% | 61 | -2.103 | -2.3 | -32.8 | 2/8 |

## Jak to czytać

- Przy tylu próbach najlepszy wynik IS jest w dużej mierze szczęściem — dlatego liczy się OOS całej listy, a nie najlepszy wiersz.
- Jeżeli żadna konfiguracja nie przeszła bramek IS, a OOS listy jest bliski zera — w tej przestrzeni reguł nie ma przewagi, która przetrwa koszty. To też wynik.
- Wybieranie spośród tych K tej, która wyszła najlepiej na OOS, łamie W1: OOS staje się kolejnym IS. Wygenerowana strategia bierze konfiguracje po kolejności IS, nie OOS.
- Następny krok: `strategy.py` z tego katalogu do dashboardu (benchmark losowy, PBO, walk-forward, spread ×1,5), potem zamrożenie i forward test (W4) — jedyny naprawdę czysty test.