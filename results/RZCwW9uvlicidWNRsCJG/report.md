# Raport strategii: RSI jedna para

Run `20261105-205721` · silnik 0.9.0 · kod `261e758df7f609bd` · dane `b1d6df1e00064526`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 3 z 4 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 4.05 |
| percentyl benchmarku ≥ 95 | ✘ | 93.10 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✔ | 0.99 |
| dodatni przy spreadzie ×1,5 | ✔ | 3.19 |

## Hipoteza

Część RSI strategii łączonej „RSI 2 + Powrót” (D-050). Logika RSI 2 bez zmian (RSI14 przebija 70/30 przeciw
wyraźnemu trendowi H1 = chwilowa przesada; dokładanie do 5 pozycji w jednej parze; wyjście TP 1,5 × ATR14 albo seria
6 zamknięć RSI za 70/30, bez stopu, max 120 świec), wariant #12 — najlepszy w IS wersji 2 (EMA200, nachylenie 0,15,
bez filtra szoku). Nowe: naraz otwarta jest najwyżej JEDNA para (seria dokładania w niej to jedna „transakcja”);
gdy kilka par daje sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS wersji 2 (PAIR_RANK).
OOS nie jest czysty (wariant i ranking z danych, na których oglądano wersję 2).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-05; źródło: yahoo.

- In-sample do 2026-05-05, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

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
| 1 | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | ema=200, nachylenie=0.15, szok=0 | 250 | 0.33 | 4.00 | 71.2 | 104 | 0.27 | 4.05 |

## Najlepszy wariant IS: TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 (ema=200, nachylenie=0.15, szok=0)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 34 | 7.6 | 257.5 | 94.1 |
| EURGBP | 37 | 1.2 | 45.7 | 62.2 |
| EURJPY | 56 | 1.5 | 81.8 | 60.7 |
| EURUSD | 34 | 9.1 | 310.5 | 76.5 |
| GBPUSD | 50 | 1.8 | 90.0 | 74.0 |
| USDCAD | 32 | -4.2 | -135.9 | 53.1 |
| USDCHF | 41 | 13.5 | 551.9 | 90.2 |
| USDJPY | 70 | 3.1 | 220.0 | 64.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 41 | 6.4 | 262.0 | 75.6 |
| 2025 | 165 | 4.6 | 760.5 | 69.7 |
| 2026 | 148 | 2.7 | 399.1 | 70.9 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 250 | 4.0 | 1 000.4 | 71.2 |
| OOS | 104 | 4.0 | 421.2 | 70.2 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 15 363 | 53.6 | 24.3 | -6.8 | 1.52 | 0 |
| 10.0% | 22 497 | 125.0 | 50.9 | -13.5 | 1.49 | 3 |
| 15.0% | 25 571 | 155.7 | 61.0 | -19.8 | 1.31 | 32 |
| 20.0% | 24 097 | 141.0 | 56.2 | -22.2 | 1.11 | 70 |
| 30.0% | 18 697 | 87.0 | 37.4 | -30.2 | 0.75 | 124 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 4.02 pips/transakcję, percentyl **93.1** (losowe: 5%=-6.57, mediana=-0.72, 95%=4.52).

- **Deflated Sharpe Ratio**: 0.987 (Sharpe na transakcję 0.175, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 200 transakcji, śr. 2.84 pips, 0.26 R.

- **Bootstrap 95%** średnich pipsów: całość [0.31; 7.41], OOS [-1.15; 8.65].

- **Spread**: ×1 4.02, ×1,5 3.19, ×2 2.37 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Część RSI strategii łączonej „RSI 2 + Powrót” (D-050). Logika RSI 2 bez zmian (RSI14 przebija 70/30 przeciw
wyraźnemu trendowi H1 = chwilowa przesada; dokładanie do 5 pozycji w jednej parze; wyjście TP 1,5 × ATR14 albo seria
6 zamknięć RSI za 70/30, bez stopu, max 120 świec), wariant #12 — najlepszy w IS wersji 2 (EMA200, nachylenie 0,15,
bez filtra szoku). Nowe: naraz otwarta jest najwyżej JEDNA para (seria dokładania w niej to jedna „transakcja”);
gdy kilka par daje sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS wersji 2 (PAIR_RANK).
OOS nie jest czysty (wariant i ranking z danych, na których oglądano wersję 2)."""

import numpy as np

LEVEL = 70          # short: RSI > 70; long: RSI < 30 — ten sam poziom co w wyjściu „seria RSI”
RUN = 6             # 6 zamknięć RSI z rzędu za poziomem = pomyłka → zamknięcie wszystkiego
MAX_POS = 5

PYRAMID = MAX_POS   # D-034: do 5 pozycji naraz w parze, tylko w jednym kierunku
HOURS = False       # D-034: bez okna godzin, jak w wersji 1

PARAMS = {"ema": [200], "nachylenie": [0.15], "szok": [0]}   # wariant #12 wersji 2

MAX_PAIRS = 1   # D-050: najwyżej jedna para z otwartymi pozycjami naraz
# ranking par: średni zysk w IS wersji 2 (pipsy na transakcję), od najlepszej
PAIR_RANK = ["USDCHF", "AUDUSD", "EURJPY", "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "EURGBP"]

# TP 1,5 × ATR14; seria 6 zamknięć RSI za 70/30 → wyjście na open następnej; limit 120 świec; bez stopu (#12)
EXITS = [{"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": RUN, "level": LEVEL, "cap": 120}]


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
