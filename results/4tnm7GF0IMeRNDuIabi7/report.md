# Raport strategii: RSI 2

Run `20261031-111911` · silnik 0.8.0 · kod `05a4838aae5707ab` · dane `fca2a7086f281a13`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 6.78 |
| percentyl benchmarku ≥ 95 | ✔ | 99.80 |
| PBO < 0,3 | ✔ | 0.03 |
| DSR ≥ 0,95 | ✘ | 0.59 |
| dodatni przy spreadzie ×1,5 | ✔ | 5.00 |

## Hipoteza

Jak w wersji 1: w wyraźnym trendzie H1 gwałtowny ruch przeciw trendowi, w którym RSI14 przebija 70
(trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada, po której cena cofa się o ok. 1,5 ATR.
Wersja 2 (po wyniku wersji 1 na Yahoo — OOS tej wersji nie jest czysty, prób łącznie 1 + 24):
1) Największe straty wersji 1 to nie przesady, tylko SZOKI informacyjne (np. 1.08.2025 13:00 UTC, dane z rynku pracy
   USA): jedna świeca o zakresie kilku ATR to nowa cena, a nie przesada — filtr „szok” pomija taki epizod.
2) Seria RSI zamyka stratę dopiero po 6 godzinach; w tym czasie cena potrafiła odejść o 100+ pipsów — stop cenowy
   2 / 3 × ATR ucina ten ogon (wariant bez stopu zostaje do porównania).
3) Więcej wejść: łagodniejszy próg „wyraźnego trendu” (0,15 ATR) i krótsza średnia (EMA100).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-10-30; źródło: yahoo.

- In-sample do 2026-04-30, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Dokładanie (D-034): do 5 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 24** (8 wejścia × 3 wyjść).

- Pominięte sygnały, średnio na wariant: 1 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.5 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 435 | 0.36 | 5.45 | 70.3 | 164 | 0.46 | 6.78 |
| 2 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=3.0 | 352 | 0.36 | 5.54 | 71.0 | 139 | 0.52 | 7.64 |
| 3 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=0 | 250 | 0.29 | 5.44 | 69.2 | 108 | 0.54 | 9.72 |
| 4 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=3.0 | 207 | 0.26 | 4.52 | 68.6 | 97 | 0.44 | 8.22 |
| 5 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=0 | 194 | 0.25 | 4.11 | 67.0 | 72 | 0.70 | 9.33 |
| 6 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 273 | 0.23 | 3.51 | 68.5 | 102 | 0.38 | 5.11 |
| 7 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=3.0 | 201 | 0.19 | 3.18 | 67.7 | 73 | 0.41 | 5.36 |
| 8 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=3.0 | 139 | 0.16 | 3.82 | 64.7 | 55 | 0.61 | 7.55 |
| 9 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 274 | 0.02 | 0.59 | 57.7 | 102 | 0.05 | 0.62 |
| 10 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 445 | 0.02 | 0.53 | 57.5 | 165 | 0.15 | 4.08 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (ema=200, nachylenie=0.15, szok=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 57 | 9.5 | 541.2 | 96.5 |
| EURGBP | 70 | 0.2 | 16.7 | 57.1 |
| EURJPY | 81 | 8.0 | 644.3 | 69.1 |
| EURUSD | 76 | 7.3 | 553.5 | 76.3 |
| GBPUSD | 75 | 5.8 | 432.7 | 78.7 |
| USDCAD | 68 | 0.4 | 29.4 | 54.4 |
| USDCHF | 60 | 12.8 | 765.2 | 86.7 |
| USDJPY | 112 | 4.5 | 500.1 | 63.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 61 | 2.3 | 138.6 | 65.6 |
| 2025 | 309 | 5.9 | 1 835.6 | 69.3 |
| 2026 | 229 | 6.6 | 1 508.8 | 76.0 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 435 | 5.5 | 2 370.9 | 70.3 |
| OOS | 164 | 6.8 | 1 112.2 | 74.4 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 22 604 | 126.0 | 51.2 | -10.0 | 1.95 | 5 |
| 10.0% | 35 471 | 254.7 | 90.1 | -16.6 | 1.87 | 68 |
| 15.0% | 31 241 | 212.4 | 78.2 | -23.8 | 1.44 | 167 |
| 20.0% | 26 441 | 164.4 | 63.8 | -28.9 | 1.13 | 239 |
| 30.0% | 17 288 | 72.9 | 32.0 | -37.3 | 0.67 | 339 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 5.81 pips/transakcję, percentyl **99.8** (losowe: 5%=-4.85, mediana=-0.93, 95%=2.93).

- **Deflated Sharpe Ratio**: 0.588 (Sharpe na transakcję 0.208, próg przy 24 próbach 0.195).

- **PBO** (CSCV, 16 bloków, 24 wariantów): 0.026 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 333 transakcji, śr. 7.58 pips, 0.52 R.

- **Bootstrap 95%** średnich pipsów: całość [3.20; 8.38], OOS [3.14; 10.08].

- **Spread**: ×1 5.81, ×1,5 5.00, ×2 4.19 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Jak w wersji 1: w wyraźnym trendzie H1 gwałtowny ruch przeciw trendowi, w którym RSI14 przebija 70
(trend spadkowy) albo 30 (trend wzrostowy), to chwilowa przesada, po której cena cofa się o ok. 1,5 ATR.
Wersja 2 (po wyniku wersji 1 na Yahoo — OOS tej wersji nie jest czysty, prób łącznie 1 + 24):
1) Największe straty wersji 1 to nie przesady, tylko SZOKI informacyjne (np. 1.08.2025 13:00 UTC, dane z rynku pracy
   USA): jedna świeca o zakresie kilku ATR to nowa cena, a nie przesada — filtr „szok” pomija taki epizod.
2) Seria RSI zamyka stratę dopiero po 6 godzinach; w tym czasie cena potrafiła odejść o 100+ pipsów — stop cenowy
   2 / 3 × ATR ucina ten ogon (wariant bez stopu zostaje do porównania).
3) Więcej wejść: łagodniejszy próg „wyraźnego trendu” (0,15 ATR) i krótsza średnia (EMA100)."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin, jak w wersji 1

PARAMS = {
    "ema": [100, 200],              # średnia trendu
    "nachylenie": [0.15, 0.25],     # „wyraźny trend”: zmiana EMA na 10 świec > tyle × ATR14 (wersja 1: 0,25)
    "szok": [0, 3.0],               # 0 = bez filtra; 3.0 = pomiń epizod, gdy świeca przebicia ma zakres > 3 × ATR14
}

# TP 1,5 × ATR14; seria 6 zamknięć RSI za 70/30 → wyjście na open następnej; limit 120 świec;
# stop cenowy: brak (jak wersja 1) / 2 / 3 × ATR14 od ceny wejścia
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120, **({"sl": sl} if sl else {})}
         for sl in (0, 2.0, 3.0)]


def weight(dist):
    """Waga pozycji: 1 + (odległość RSI od progu) / 5, maksymalnie 3 (jak w wersji 1)."""
    return min(3.0, 1.0 + dist / 5.0)


def signals(df, p, ind):
    ema = ind.ema(df.close, p["ema"])
    atr = ind.atr(df, 14)
    slope = (ema - ema.shift(10)) / atr                     # nachylenie EMA na 10 świec, w ATR14
    up = (slope > p["nachylenie"]).to_numpy()
    down = (slope < -p["nachylenie"]).to_numpy()
    rng = ((df.high - df.low) / atr.shift(1)).to_numpy()    # zakres świecy względem ATR sprzed niej
    shock = rng > p["szok"] if p["szok"] else np.zeros(len(df), bool)
    r = ind.rsi(df.close, 14).to_numpy()
    out = np.zeros(len(r))
    side, streak, count, record, skip = 0, 0, 0, 0.0, False
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
                if deeper and count < MAX_POS and streak < RUN and not skip:
                    count += 1
                    record = x
                    out[t] = side * weight(abs(x - (LEVEL if side < 0 else 100 - LEVEL)))
                continue
            side = 0                                        # RSI wrócił za próg — koniec epizodu
        if down[t] and x > LEVEL and prev <= LEVEL:          # przebicie 70 w trendzie spadkowym → short
            side, streak, count, record, skip = -1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = -weight(x - LEVEL)
        elif up[t] and x < 100 - LEVEL and prev >= 100 - LEVEL:  # przebicie 30 w trendzie wzrostowym → long
            side, streak, count, record, skip = 1, 1, 1, x, bool(shock[t])
            if not skip:
                out[t] = weight(100 - LEVEL - x)
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
