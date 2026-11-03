# Raport strategii: H4

Run `20261103-175633` · silnik 0.9.0 · kod `0ab6ebb0f314c2a2` · dane `e76fc4183c4b5596`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -3.76 |
| percentyl benchmarku ≥ 95 | ✘ | 46.00 |
| PBO < 0,3 | ✘ | 0.70 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -2.51 |

## Hipoteza

Cena po jednej stronie wszystkich głównych średnich na H1, H4 i D1 oznacza zgodny trend krótko- i średnioterminowy
oraz brak bliskiego wsparcia lub oporu ze średnich, więc ruch ma wolną drogę. Wejście zgodne z tym trendem,
przy pierwszym pełnym ułożeniu albo na otwarciu Nowego Jorku, ma mieć przewagę nad wejściem losowym.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 932** (4 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 125 (limit otwartych pozycji w parze), 1.9 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 2523 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 4.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 12 świecach | mode=ny, d1_max=200 | 369 | 0.07 | -0.09 | 53.4 | 281 | -0.44 | -3.76 |
| 2 | po 8 świecach | mode=ny, d1_max=200 | 376 | 0.06 | 0.26 | 50.8 | 281 | -0.39 | -4.32 |
| 3 | po 36 świecach | mode=start, d1_max=100 | 566 | 0.02 | 0.24 | 49.6 | 254 | -0.28 | -3.28 |
| 4 | po 3 świecach | mode=ny, d1_max=200 | 377 | 0.02 | -1.22 | 50.4 | 286 | -0.28 | -2.64 |
| 5 | po 48 świecach | mode=start, d1_max=100 | 499 | 0.02 | 2.45 | 48.3 | 220 | -0.75 | -9.76 |
| 6 | cena przez SMA20, SL 2×ATR14, max 120 | mode=ny, d1_max=100 | 604 | 0.02 | -0.42 | 35.8 | 288 | -0.17 | -4.76 |
| 7 | po 16 świecach | mode=ny, d1_max=200 | 371 | 0.01 | -0.99 | 53.1 | 281 | -0.50 | -4.62 |
| 8 | po 12 świecach | mode=ny, d1_max=100 | 673 | 0.00 | -1.06 | 52.6 | 322 | -0.41 | -4.06 |
| 9 | ATR5 TP 3× SL 1.5× max 72 | mode=ny, d1_max=100 | 614 | 0.00 | -1.37 | 36.5 | 285 | -0.23 | -3.96 |
| 10 | cena przez SMA20, SL 3×ATR14, max 120 | mode=ny, d1_max=100 | 600 | 0.00 | -0.75 | 36.7 | 287 | -0.11 | -4.34 |

## Najlepszy wariant IS: po 12 świecach (mode=ny, d1_max=200)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 75 | 0.1 | 8.3 | 58.7 |
| EURGBP | 84 | -0.5 | -39.8 | 46.4 |
| EURJPY | 105 | -0.8 | -79.2 | 49.5 |
| EURUSD | 78 | -3.2 | -245.8 | 46.2 |
| GBPUSD | 75 | -3.3 | -249.2 | 44.0 |
| USDCAD | 83 | -1.5 | -126.0 | 50.6 |
| USDCHF | 66 | -3.0 | -197.2 | 47.0 |
| USDJPY | 84 | -1.9 | -163.7 | 51.2 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2025 | 209 | -1.1 | -219.6 | 54.5 |
| 2026 | 441 | -2.0 | -873.0 | 46.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 369 | -0.1 | -34.8 | 53.4 |
| OOS | 281 | -3.8 | -1 057.8 | 43.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 8 619 | -13.8 | -10.8 | -20.8 | -0.71 | 0 |
| 10.0% | 7 281 | -27.2 | -21.6 | -38.0 | -0.71 | 0 |
| 15.0% | 6 108 | -38.9 | -31.5 | -51.4 | -0.69 | 1 |
| 20.0% | 4 980 | -50.2 | -41.4 | -62.7 | -0.70 | 11 |
| 30.0% | 3 765 | -62.3 | -52.7 | -68.8 | -0.77 | 100 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.68 pips/transakcję, percentyl **46.0** (losowe: 5%=-4.40, mediana=-1.53, 95%=1.25).

- **Deflated Sharpe Ratio**: 0.000 (Sharpe na transakcję 0.030, próg przy 932 próbach 0.285).

- **PBO** (CSCV, 16 bloków, 932 wariantów): 0.698 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 516 transakcji, śr. -2.75 pips, -0.16 R.

- **Bootstrap 95%** średnich pipsów: całość [-4.32; 1.20], OOS [-7.74; 0.72].

- **Spread**: ×1 -1.68, ×1,5 -2.51, ×2 -3.35 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Cena po jednej stronie wszystkich głównych średnich na H1, H4 i D1 oznacza zgodny trend krótko- i średnioterminowy
oraz brak bliskiego wsparcia lub oporu ze średnich, więc ruch ma wolną drogę. Wejście zgodne z tym trendem,
przy pierwszym pełnym ułożeniu albo na otwarciu Nowego Jorku, ma mieć przewagę nad wejściem losowym."""

PARAMS = {
    "mode": ["start", "ny"],   # start = pierwsza świeca pełnego ułożenia; ny = stan trwa przed otwarciem Nowego Jorku
    "d1_max": [100, 200],      # najdłuższa średnia D1: 200 zjada ok. 40% krótkiej historii
}


def _tf(close, rule, n, ind):
    """SMA z zamkniętych świec wyższego interwału, przeniesiona na H1 bez look-ahead."""
    x = close.resample(rule).last().dropna()
    return ind.sma(x, n).shift(1).reindex(close.index, method="ffill")


def signals(df, p, ind):
    c = df.close
    lines = [ind.sma(c, n) for n in (20, 50, 100, 200)]
    lines += [_tf(c, "4h", n, ind) for n in (20, 50, 100, 200)]
    lines += [_tf(c, "1D", n, ind) for n in (20, 50, 100, 200) if n <= p["d1_max"]]
    m = pd.concat(lines, axis=1)
    ready = m.notna().all(axis=1)
    up = (c > m.max(axis=1)) & ready
    dn = (c < m.min(axis=1)) & ready
    if p["mode"] == "start":
        go_up = up & ~up.shift(1, fill_value=False)
        go_dn = dn & ~dn.shift(1, fill_value=False)
    else:
        ny = np.asarray(df.index.tz_convert("America/New_York").hour) == 7   # świeca kończy się o 8:00 w Nowym Jorku
        go_up, go_dn = up & ny, dn & ny
    return go_up.astype("int8") - go_dn.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
