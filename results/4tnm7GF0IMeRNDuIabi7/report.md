# Raport strategii: RSI 2

Run `20261111-105038` · silnik 0.12.0 · kod `05a4838aae5707ab` · dane `db2f1a8ea4dc4ce5`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 4.03 |
| percentyl benchmarku ≥ 95 | ✔ | 99.60 |
| PBO < 0,3 | ✔ | 0.15 |
| DSR ≥ 0,95 | ✘ | 0.76 |
| dodatni przy spreadzie ×1,5 | ✔ | 4.56 |

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

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-11; źródło: yahoo; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058.

- In-sample do 2026-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 5 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 101 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 103 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 102 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 104 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 105 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 24** (8 wejścia × 3 wyjść).

- Pominięte sygnały, średnio na wariant: 2 (limit otwartych pozycji w parze), 0.4 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 25.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=3.0 | 362 | 0.40 | 6.03 | 71.8 | 126 | 0.35 | 5.14 |
| 2 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 445 | 0.39 | 5.85 | 71.0 | 158 | 0.19 | 4.03 |
| 3 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=0 | 260 | 0.35 | 6.15 | 70.4 | 92 | 0.43 | 8.49 |
| 4 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.25, szok=3.0 | 217 | 0.32 | 5.41 | 70.0 | 78 | 0.39 | 7.23 |
| 5 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=0 | 206 | 0.32 | 5.30 | 68.9 | 73 | -0.02 | 4.27 |
| 6 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 285 | 0.28 | 4.20 | 69.8 | 103 | -0.08 | 2.04 |
| 7 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.25, szok=3.0 | 151 | 0.26 | 5.45 | 67.5 | 45 | 0.56 | 5.82 |
| 8 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=3.0 | 212 | 0.25 | 4.06 | 69.3 | 62 | 0.41 | 4.48 |
| 9 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=100, nachylenie=0.15, szok=0 | 286 | 0.04 | 0.87 | 58.7 | 104 | -0.08 | -1.19 |
| 10 | TP 1.5×ATR14, SL 2×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 455 | 0.03 | 0.69 | 58.0 | 159 | 0.07 | 2.28 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (ema=200, nachylenie=0.15, szok=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 57 | 9.6 | 547.8 | 96.5 |
| EURGBP | 71 | 0.0 | 3.2 | 56.3 |
| EURJPY | 80 | 7.8 | 624.8 | 68.8 |
| EURUSD | 76 | 6.3 | 482.6 | 75.0 |
| GBPUSD | 78 | 4.9 | 381.5 | 76.9 |
| USDCAD | 67 | -0.4 | -29.7 | 53.7 |
| USDCHF | 62 | 11.6 | 717.1 | 83.9 |
| USDJPY | 112 | 4.6 | 513.0 | 63.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 61 | 2.3 | 138.6 | 65.6 |
| 2025 | 309 | 5.9 | 1 835.6 | 69.3 |
| 2026 | 233 | 5.4 | 1 265.9 | 73.8 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 445 | 5.9 | 2 604.0 | 71.0 |
| OOS | 158 | 4.0 | 636.1 | 69.6 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 5.0% | 21 225 | 112.3 | 45.9 | -10.0 | -15.7 | 1.79 | 5 |
| 10.0% | 31 099 | 211.0 | 76.7 | -16.6 | -29.4 | 1.68 | 71 |
| 15.0% | 27 683 | 176.8 | 66.7 | -23.8 | -31.8 | 1.29 | 166 |
| 20.0% | 22 759 | 127.6 | 51.1 | -28.9 | -35.6 | 0.98 | 241 |
| 30.0% | 15 490 | 54.9 | 24.6 | -37.3 | -46.4 | 0.58 | 338 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 5.37 pips/transakcję, percentyl **99.6** (losowe: 5%=-4.90, mediana=-0.92, 95%=3.00).

- **Deflated Sharpe Ratio**: 0.756 (Sharpe na transakcję 0.227, próg przy 24 próbach 0.185).

- **PBO** (CSCV, 16 bloków, 24 wariantów): 0.151 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 300 transakcji, śr. 6.49 pips, 0.49 R.

- **Bootstrap 95%** średnich pipsów: całość [2.65; 8.02], OOS [0.41; 7.53].

- **Spread**: ×1 5.37, ×1,5 4.56, ×2 3.75 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 0.8 nocy na transakcję, 40% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 4.97, 1 pips: 4.57 pips/transakcję.

## Forward test od zamrożenia (W4, D-056)

- Zamrożona 2026-10-31; oceniany wariant: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (zamrożony, nie ranking); oczekiwanie sprzed zamrożenia: 5.43 pips / 0.34 R na transakcję (599 transakcji).
- **Forward: 4 transakcji, śr. -2.72 pips (-0.22 R), suma -11 pips, win 50%, t = -0.44; bootstrap 95% [—; —].**
- Odchylenie od oczekiwania: z = -0.51 (|z| ≥ 2 = forward nie wygląda jak backtest; przy małym n liczba ta jest głównie szumem — potrzeba setek transakcji, żeby odróżnić +3 pipsy od zera).

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
