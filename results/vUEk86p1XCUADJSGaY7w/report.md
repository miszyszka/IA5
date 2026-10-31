# Raport strategii: RSI w wyraźnym trendzie

Run `20261031-105543` · silnik 0.8.0 · kod `c6e6048042a2deef` · dane `fca2a7086f281a13`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 3 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 9.72 |
| percentyl benchmarku ≥ 95 | ✔ | 99.70 |
| PBO < 0,3 | ✘ | — |
| DSR ≥ 0,95 | ✘ | — |
| dodatni przy spreadzie ×1,5 | ✔ | 5.91 |

## Hipoteza

W wyraźnym trendzie H1 (EMA200 zmienia się o więcej niż 0,25 ATR14 na 10 świec) gwałtowny ruch
przeciw trendowi, w którym RSI14 przebija 70 (trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada:
płynność wraca do kierunku trendu i cena cofa się o ok. 1,5 ATR. Im głębsza przesada, tym większa oczekiwana
korekta — stąd dokładanie z rosnącą wagą. Gdy przesada trwa 6 godzin, to już nie przesada, tylko zmiana trendu.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-10-30; źródło: yahoo.

- In-sample do 2026-04-30, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Dokładanie (D-034): do 5 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 6 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 1.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | — | 250 | 0.29 | 5.44 | 69.2 | 108 | 0.54 | 9.72 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 29 | 11.8 | 342.4 | 96.6 |
| EURGBP | 52 | -0.5 | -25.9 | 53.8 |
| EURJPY | 48 | 8.6 | 412.5 | 68.8 |
| EURUSD | 32 | 10.3 | 329.2 | 84.4 |
| GBPUSD | 53 | 6.3 | 331.4 | 79.2 |
| USDCAD | 38 | -0.0 | -0.8 | 55.3 |
| USDCHF | 35 | 8.7 | 305.6 | 77.1 |
| USDJPY | 71 | 10.1 | 714.6 | 71.8 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 33 | -0.1 | -3.9 | 63.6 |
| 2025 | 181 | 3.9 | 714.0 | 66.3 |
| 2026 | 144 | 11.8 | 1 698.8 | 80.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 250 | 5.4 | 1 359.4 | 69.2 |
| OOS | 108 | 9.7 | 1 049.5 | 77.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 16 660 | 66.6 | 29.7 | -8.5 | 1.70 | 2 |
| 10.0% | 22 902 | 129.0 | 52.6 | -17.2 | 1.65 | 29 |
| 15.0% | 22 346 | 123.5 | 50.7 | -19.7 | 1.37 | 81 |
| 20.0% | 22 698 | 127.0 | 51.9 | -24.8 | 1.24 | 124 |
| 30.0% | 22 681 | 126.8 | 51.9 | -27.0 | 1.18 | 188 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 6.73 pips/transakcję, percentyl **99.7** (losowe: 5%=-6.78, mediana=-1.06, 95%=4.08).

- **Deflated Sharpe Ratio**: — (Sharpe na transakcję —, próg przy 1 próbach —).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 192 transakcji, śr. 10.65 pips, 0.59 R.

- **Bootstrap 95%** średnich pipsów: całość [3.62; 9.57], OOS [5.22; 13.46].

- **Spread**: ×1 6.73, ×1,5 5.91, ×2 5.08 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """W wyraźnym trendzie H1 (EMA200 zmienia się o więcej niż 0,25 ATR14 na 10 świec) gwałtowny ruch
przeciw trendowi, w którym RSI14 przebija 70 (trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada:
płynność wraca do kierunku trendu i cena cofa się o ok. 1,5 ATR. Im głębsza przesada, tym większa oczekiwana
korekta — stąd dokładanie z rosnącą wagą. Gdy przesada trwa 6 godzin, to już nie przesada, tylko zmiana trendu."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 (= 100 − 70)
RUN = 6             # tyle zamknięć z rzędu za poziomem = pomyłka → zamknięcie wszystkiego (wyjście rsi_streak)
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin (B11 wyłączone dla tej strategii)
EXITS = [
    # TP 1,5 × ATR14 od ceny wejścia (ATR ze świecy sygnału); seria 6 zamknięć RSI za 70/30 → wyjście na open
    # następnej świecy; limit 120 świec. Bez SL cenowego — rolę stopu pełni seria RSI.
    {"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120},
]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / ind.atr(df, 14)       # nachylenie EMA200 na 10 świec, w ATR14
    up = (slope > 0.25).to_numpy()                          # wyraźnie rośnie
    down = (slope < -0.25).to_numpy()                       # wyraźnie spada
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record = 0, 0, 0, 0.0
    for t in range(1, len(r)):
        x, prev = r[t], r[t - 1]
        if np.isnan(x) or np.isnan(prev):
            side = 0
            continue
        if side != 0:
            beyond = x > LEVEL if side < 0 else x < 100 - LEVEL
            if beyond:                                      # przesada trwa: ta sama „seria”
                streak += 1
                deeper = x > record if side < 0 else x < record
                # dokładamy, gdy RSI pobije rekord z ostatniego wejścia; nie w 6. świecy serii (wtedy wszystko się zamyka)
                if deeper and count < MAX_POS and streak < RUN:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec wybicia
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record = -1, 1, 1, x
            out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record = 1, 1, 1, x
            out[t] = weight(100 - LEVEL - x)
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
