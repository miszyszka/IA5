# Raport strategii: Powrót v2 jedna para

Run `20261103-160806` · silnik 0.8.0 · kod `192c321e916e8334` · dane `d2e0931ceff35b9d`

## Werdykt: 🟢 ZIELONY — wszystkie testy zaliczone

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 10.37 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✔ | 0.98 |
| dodatni przy spreadzie ×1,5 | ✔ | 9.76 |

## Hipoteza

Część Powrót strategii łączonej „RSI 2 + Powrót” (D-050). Reguły FX-POWRÓT v2 bez zmian (impuls ≥ 2 × ATR100,
pierwsza czerwona w ciągu 3 świec, short, bez stopu, max 60 świec, jedna pozycja na parę). Wyjście: TP 1,5 × ATR14 —
najlepsze w IS spośród przybliżeń celu „połowa drogi”. Nowe: naraz otwarta jest najwyżej JEDNA para; gdy kilka par daje
sygnał na tej samej świecy, wygrywa para z najwyższym średnim zyskiem w IS (PAIR_RANK, liczone 2026-11-03 na IS).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 19 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 6.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1.5× SL 0× max 60 | — | 202 | 0.51 | 10.60 | 83.2 | 74 | 0.48 | 10.37 |

## Najlepszy wariant IS: ATR14 TP 1.5× SL 0× max 60 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 39 | 6.4 | 249.2 | 82.1 |
| EURGBP | 43 | 3.2 | 137.0 | 79.1 |
| EURJPY | 24 | 16.1 | 386.6 | 83.3 |
| EURUSD | 54 | 7.1 | 383.6 | 81.5 |
| GBPUSD | 55 | 14.0 | 771.7 | 85.5 |
| USDCAD | 11 | 18.6 | 204.9 | 90.9 |
| USDCHF | 25 | 4.0 | 99.3 | 80.0 |
| USDJPY | 25 | 27.0 | 675.4 | 88.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 20 | 18.3 | 366.7 | 85.0 |
| 2025 | 145 | 9.3 | 1 354.6 | 81.4 |
| 2026 | 111 | 10.7 | 1 186.3 | 84.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 202 | 10.6 | 2 140.3 | 83.2 |
| OOS | 74 | 10.4 | 767.4 | 82.4 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 14 160 | 41.6 | 19.0 | -6.6 | 2.14 | 0 |
| 10.0% | 19 858 | 98.6 | 40.8 | -13.1 | 2.14 | 0 |
| 15.0% | 27 571 | 175.7 | 65.9 | -19.5 | 2.13 | 0 |
| 20.0% | 37 875 | 278.7 | 94.4 | -25.9 | 2.13 | 0 |
| 30.0% | 56 921 | 469.2 | 138.2 | -38.3 | 1.97 | 11 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 10.54 pips/transakcję, percentyl **100.0** (losowe: 5%=-6.88, mediana=-1.77, 95%=2.99).

- **Deflated Sharpe Ratio**: 0.977 (Sharpe na transakcję 0.212, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 170 transakcji, śr. 9.03 pips, 0.50 R.

- **Bootstrap 95%** średnich pipsów: całość [6.06; 14.96], OOS [3.47; 17.25].

- **Spread**: ×1 10.54, ×1,5 9.76, ×2 8.99 pips/transakcję.

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
