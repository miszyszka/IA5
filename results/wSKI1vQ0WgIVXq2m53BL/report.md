# Raport strategii: Powrót

Run `20261110-165551` · silnik 0.9.0 · kod `12864a1b4312df32` · dane `7025157b616c8c9b`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 4 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 9.98 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✔ | 0.14 |
| DSR ≥ 0,95 | ✘ | 0.65 |
| dodatni przy spreadzie ×1,5 | ✔ | 9.79 |

## Hipoteza

FX-POWRÓT v2 (pomysł z 20.10.2026, reguły z IA4 sekcja 7b). Po gwałtownym impulsie w górę (zamknięcie ≥ 2 × ATR100
wyżej niż poprzednie) kurs często cofa się w stronę ceny sprzed impulsu. Pierwsza czerwona świeca w ciągu 3 świec
po impulsie pokazuje, że kupujący się wyczerpali — short z celem w połowie drogi od szczytu do bazy, bez stopu,
limit 60 świec.
Różnice wobec oryginału (ograniczenia IA5): 8 par zamiast 10; warunek „open wejścia ≥ baza + 0,5 ATR” sprawdzany na
zamknięciu świecy sygnału (open następnej nie jest znany w chwili sygnału); TP jako poziom ceny P − ½(P − B) silnik
na razie nie obsługuje — wyjścia przybliżone przez TP w wielokrotnościach ATR14 (patrz EXITS).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-10; źródło: yahoo.

- In-sample do 2026-05-08, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 5** (1 wejścia × 5 wyjść).

- Pominięte sygnały, średnio na wariant: 32 (limit otwartych pozycji w parze), 2.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 6.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1.5× SL 0× max 60 | — | 205 | 0.53 | 10.76 | 83.4 | 72 | 0.45 | 9.98 |
| 2 | ATR14 TP 1× SL 0× max 60 | — | 211 | 0.46 | 9.11 | 91.5 | 75 | 0.46 | 8.74 |
| 3 | ATR14 TP 2× SL 0× max 60 | — | 195 | 0.09 | 4.82 | 71.8 | 70 | 0.37 | 10.06 |
| 4 | ATR14 TP 3× SL 0× max 60 | — | 188 | -0.24 | -1.60 | 54.8 | 67 | 0.40 | 12.27 |
| 5 | po 60 świecach | — | 177 | -0.27 | -3.18 | 45.2 | 60 | 0.11 | 8.12 |

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
| USDCHF | 26 | 4.5 | 116.1 | 80.8 |
| USDJPY | 25 | 27.0 | 675.4 | 88.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 20 | 18.3 | 366.7 | 85.0 |
| 2025 | 145 | 9.3 | 1 354.6 | 81.4 |
| 2026 | 112 | 10.7 | 1 203.2 | 84.8 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 205 | 10.8 | 2 205.8 | 83.4 |
| OOS | 72 | 10.0 | 718.8 | 81.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 14 204 | 42.0 | 19.0 | -6.6 | 2.15 | 0 |
| 10.0% | 19 981 | 99.8 | 40.8 | -13.1 | 2.14 | 0 |
| 15.0% | 27 825 | 178.3 | 65.9 | -19.5 | 2.14 | 0 |
| 20.0% | 38 341 | 283.4 | 94.4 | -25.9 | 2.13 | 0 |
| 30.0% | 57 972 | 479.7 | 138.5 | -38.3 | 1.98 | 11 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 10.56 pips/transakcję, percentyl **100.0** (losowe: 5%=-7.14, mediana=-1.96, 95%=2.72).

- **Deflated Sharpe Ratio**: 0.651 (Sharpe na transakcję 0.218, próg przy 5 próbach 0.177).

- **PBO** (CSCV, 16 bloków, 5 wariantów): 0.141 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 166 transakcji, śr. 8.85 pips, 0.49 R.

- **Bootstrap 95%** średnich pipsów: całość [5.90; 14.92], OOS [2.84; 16.91].

- **Spread**: ×1 10.56, ×1,5 9.79, ×2 9.02 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """FX-POWRÓT v2 (pomysł z 20.10.2026, reguły z IA4 sekcja 7b). Po gwałtownym impulsie w górę (zamknięcie ≥ 2 × ATR100
wyżej niż poprzednie) kurs często cofa się w stronę ceny sprzed impulsu. Pierwsza czerwona świeca w ciągu 3 świec
po impulsie pokazuje, że kupujący się wyczerpali — short z celem w połowie drogi od szczytu do bazy, bez stopu,
limit 60 świec.
Różnice wobec oryginału (ograniczenia IA5): 8 par zamiast 10; warunek „open wejścia ≥ baza + 0,5 ATR” sprawdzany na
zamknięciu świecy sygnału (open następnej nie jest znany w chwili sygnału); TP jako poziom ceny P − ½(P − B) silnik
na razie nie obsługuje — wyjścia przybliżone przez TP w wielokrotnościach ATR14 (patrz EXITS)."""

import numpy as np

HOURS = False   # okno z reguł strategii: świeca sygnału zaczyna się 07–16 UTC (zamiast okna 07–17 czasu polskiego)

# Bez SL (jak w oryginale), limit 60 świec. Wariant „czas” = trzymanie do 60. świecy; warianty ATR = przybliżenie
# celu „połowa drogi powrotu” (impuls ≥ 2 × ATR100 ≈ 3–4 × ATR14, połowa drogi ≈ 1–2 × ATR14).
EXITS = [{"kind": "time", "n": 60, "cap": 60}] + [{"kind": "atr", "n": 14, "tp": tp, "cap": 60} for tp in (1.0, 1.5, 2.0, 3.0)]

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
