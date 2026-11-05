# Raport strategii: Powrót v2 jedna para

Run `20261105-205712` · silnik 0.9.0 · kod `192c321e916e8334` · dane `b1d6df1e00064526`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 3 z 4 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 3.06 |
| percentyl benchmarku ≥ 95 | ✔ | 96.90 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✘ | 0.81 |
| dodatni przy spreadzie ×1,5 | ✔ | 4.41 |

## Hipoteza

Część Powrót strategii łączonej „RSI 2 + Powrót” (D-050). Reguły FX-POWRÓT v2 bez zmian (impuls ≥ 2 × ATR100,
pierwsza czerwona w ciągu 3 świec, short, bez stopu, max 60 świec, jedna pozycja na parę). Wyjście: TP 1,5 × ATR14 —
najlepsze w IS spośród przybliżeń celu „połowa drogi”. Nowe: naraz otwarta jest najwyżej JEDNA para; gdy kilka par daje
sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS (PAIR_RANK, liczone 2026-11-03 na IS).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-05; źródło: yahoo.

- In-sample do 2026-05-05, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 13 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 6.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1.5× SL 0× max 60 | — | 110 | 0.29 | 5.99 | 80.0 | 42 | -0.01 | 3.06 |

## Najlepszy wariant IS: ATR14 TP 1.5× SL 0× max 60 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 10 | 4.8 | 48.3 | 90.0 |
| EURGBP | 27 | 0.8 | 21.4 | 70.4 |
| EURJPY | 11 | -19.2 | -211.6 | 63.6 |
| EURUSD | 26 | 2.2 | 57.1 | 76.9 |
| GBPUSD | 36 | 9.7 | 347.6 | 80.6 |
| USDCAD | 7 | 24.8 | 173.8 | 100.0 |
| USDCHF | 17 | -3.4 | -58.1 | 70.6 |
| USDJPY | 18 | 22.7 | 409.3 | 88.9 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 12 | 8.0 | 96.3 | 75.0 |
| 2025 | 80 | 4.8 | 386.4 | 80.0 |
| 2026 | 60 | 5.1 | 305.2 | 76.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 110 | 6.0 | 659.4 | 80.0 |
| OOS | 42 | 3.1 | 128.5 | 73.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 873 | 8.7 | 4.3 | -6.3 | 0.66 | 0 |
| 10.0% | 11 758 | 17.6 | 8.4 | -12.5 | 0.66 | 0 |
| 15.0% | 12 643 | 26.4 | 12.4 | -18.4 | 0.65 | 0 |
| 20.0% | 13 516 | 35.2 | 16.2 | -24.2 | 0.65 | 0 |
| 30.0% | 15 160 | 51.6 | 23.1 | -35.2 | 0.65 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 5.18 pips/transakcję, percentyl **96.9** (losowe: 5%=-8.98, mediana=-1.83, 95%=4.74).

- **Deflated Sharpe Ratio**: 0.815 (Sharpe na transakcję 0.105, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 93 transakcji, śr. 4.05 pips, 0.19 R.

- **Bootstrap 95%** średnich pipsów: całość [-2.63; 12.07], OOS [-7.32; 12.40].

- **Spread**: ×1 5.18, ×1,5 4.41, ×2 3.64 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Część Powrót strategii łączonej „RSI 2 + Powrót” (D-050). Reguły FX-POWRÓT v2 bez zmian (impuls ≥ 2 × ATR100,
pierwsza czerwona w ciągu 3 świec, short, bez stopu, max 60 świec, jedna pozycja na parę). Wyjście: TP 1,5 × ATR14 —
najlepsze w IS spośród przybliżeń celu „połowa drogi”. Nowe: naraz otwarta jest najwyżej JEDNA para; gdy kilka par daje
sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS (PAIR_RANK, liczone 2026-11-03 na IS)."""

import numpy as np

HOURS = False   # okno z reguł strategii: świeca sygnału zaczyna się 07–16 UTC (zamiast okna 07–17 czasu polskiego)

MAX_PAIRS = 1   # D-050: najwyżej jedna para z otwartą pozycją naraz
# ranking par: średni zysk w IS (pipsy na transakcję, wyjście TP 1,5 × ATR14), od najlepszej
PAIR_RANK = ["USDJPY", "GBPUSD", "USDCHF", "USDCAD", "EURJPY", "EURUSD", "AUDUSD", "EURGBP"]

EXITS = [{"kind": "atr", "n": 14, "tp": 1.5, "cap": 60}]   # TP 1,5 × ATR14, bez SL, max 60 świec

SPREAD = {"EURUSD": 0.9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7, "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0,
          "EURJPY": 2.1}


def signals(df, p, ind):
    pair = df.attrs.get("pair", "")
    pip = 0.01 if "JPY" in pair else 0.0001
    spread = SPREAD.get(pair, 2.0) * pip
    o, h, c = df.open.to_numpy(), df.high.to_numpy(), df.close.to_numpy()
    atr = ind.atr(df, 100).shift(1).to_numpy()          # ATR100 sprzed świecy
    hour = df.index.hour.to_numpy()                      # UTC
    n = len(c)
    out = np.zeros(n, np.int8)
    base, peak, last_imp, active = 0.0, 0.0, -1, False
    for t in range(1, n):
        a = atr[t]
        if np.isnan(a):
            continue
        if c[t] - c[t - 1] >= 2 * a:                     # świeca impulsu
            if not active:
                active, base, peak = True, c[t - 1], h[t]
            peak = max(peak, h[t])
            last_imp = t
            continue
        if not active:
            continue
        peak = max(peak, h[t])
        if c[t] <= base or t - last_imp > 3:             # impuls wygasł
            active = False
            continue
        if c[t] < o[t] and 7 <= hour[t] <= 16:           # pierwsza czerwona w ciągu 3 świec
            tp = peak - 0.5 * (peak - base)
            if c[t] >= base + 0.5 * a and c[t] - tp >= max(spread, 0.1 * a):
                out[t] = -1
            active = False                               # tylko pierwsza czerwona
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
