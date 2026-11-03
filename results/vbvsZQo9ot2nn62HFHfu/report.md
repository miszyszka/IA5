# Raport strategii: power of 3

Run `20261103-180304` · silnik 0.9.0 · kod `21262dcf279024e7` · dane `e76fc4183c4b5596`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -1.79 |
| percentyl benchmarku ≥ 95 | ✘ | 70.90 |
| PBO < 0,3 | ✘ | 0.30 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -2.41 |

## Hipoteza

Power of 3 / „knot świecy 4H” (wg filmu: akumulacja → manipulacja → dystrybucja). Gdy dzienny kierunek jest
wzrostowy, nowa świeca 4H zwykle najpierw robi dolny knot (fałszywy ruch w dół, który zbiera płynność pod ważnym
dołkiem), a potem zamyka się wysoko. Wchodzimy long, gdy w pierwszych godzinach nowej świecy 4H cena zebrała dołek
(poprzedniej świecy 4H albo ostatnich 24 h), a świeca H1 zamyka się z powrotem nad nim (zmiana kierunku). Lustrzanie short.
Różnice (ograniczenia IA5): tylko H1 (autor wchodzi na 1 min po luce FVG i „zmianie stanu dostawy”); stop „pod dołkiem
świecy 4H” i cel przybliżone przez ATR14 albo wyjście na koniec świecy 4H (2–4 świece H1).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 24** (4 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 139 (limit otwartych pozycji w parze), 0.4 (brak danych do wyjścia); 13 wejść w rozgrzewce ATR, 11657 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 3.7 (przerwa w dostępie do danych), 0.2 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 2× SL 1× max 24 | bias=dzien, dolek=4h | 2 086 | -0.13 | -1.52 | 33.7 | 649 | -0.19 | -1.79 |
| 2 | ATR14 TP 2× SL 1× max 24 | bias=dzien, dolek=24h | 586 | -0.13 | -2.29 | 33.6 | 205 | -0.11 | -1.15 |
| 3 | ATR14 TP 2× SL 1× max 24 | bias=brak, dolek=24h | 1 635 | -0.14 | -1.86 | 33.5 | 524 | -0.17 | -1.77 |
| 4 | ATR14 TP 1.5× SL 1× max 24 | bias=dzien, dolek=4h | 2 142 | -0.14 | -1.77 | 39.6 | 660 | -0.23 | -2.44 |
| 5 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, dolek=24h | 1 647 | -0.15 | -2.01 | 39.3 | 530 | -0.19 | -1.98 |
| 6 | ATR14 TP 1× SL 1× max 24 | bias=brak, dolek=24h | 1 656 | -0.15 | -1.87 | 49.1 | 534 | -0.19 | -1.44 |
| 7 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, dolek=4h | 3 666 | -0.15 | -1.90 | 39.2 | 1 176 | -0.27 | -3.05 |
| 8 | ATR14 TP 2× SL 1× max 24 | bias=brak, dolek=4h | 3 472 | -0.15 | -1.85 | 32.9 | 1 119 | -0.29 | -3.23 |
| 9 | ATR14 TP 1.5× SL 1× max 24 | bias=dzien, dolek=24h | 590 | -0.16 | -2.37 | 39.0 | 205 | -0.15 | -1.44 |
| 10 | ATR14 TP 1× SL 1× max 24 | bias=brak, dolek=4h | 3 861 | -0.16 | -1.98 | 48.7 | 1 248 | -0.26 | -2.75 |

## Najlepszy wariant IS: ATR14 TP 2× SL 1× max 24 (bias=dzien, dolek=4h)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 311 | -0.6 | -199.2 | 36.3 |
| EURGBP | 369 | -1.8 | -650.0 | 33.9 |
| EURJPY | 306 | -1.7 | -513.9 | 33.7 |
| EURUSD | 323 | -0.4 | -134.9 | 34.7 |
| GBPUSD | 359 | -2.5 | -896.7 | 30.4 |
| USDCAD | 388 | -0.7 | -271.7 | 35.8 |
| USDCHF | 363 | -2.1 | -765.4 | 32.5 |
| USDJPY | 316 | -2.9 | -902.7 | 32.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 237 | -1.8 | -417.4 | 33.8 |
| 2025 | 1394 | -1.9 | -2 650.3 | 32.6 |
| 2026 | 1104 | -1.1 | -1 266.7 | 34.9 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 2086 | -1.5 | -3 174.1 | 33.7 |
| OOS | 649 | -1.8 | -1 160.4 | 33.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 5 454 | -45.5 | -26.0 | -47.7 | -1.79 | 0 |
| 10.0% | 2 866 | -71.3 | -46.2 | -73.6 | -1.79 | 0 |
| 15.0% | 1 487 | -85.1 | -61.2 | -86.8 | -1.79 | 11 |
| 20.0% | 785 | -92.2 | -71.8 | -93.3 | -1.88 | 125 |
| 30.0% | 318 | -96.8 | -82.0 | -97.2 | -1.89 | 464 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.58 pips/transakcję, percentyl **70.9** (losowe: 5%=-2.60, mediana=-1.84, 95%=-1.14).

- **Deflated Sharpe Ratio**: 0.000 (Sharpe na transakcję -0.090, próg przy 24 próbach 0.046).

- **PBO** (CSCV, 16 bloków, 24 wariantów): 0.304 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 1154 transakcji, śr. -2.04 pips, -0.19 R.

- **Bootstrap 95%** średnich pipsów: całość [-2.51; -0.73], OOS [-3.24; -0.38].

- **Spread**: ×1 -1.58, ×1,5 -2.41, ×2 -3.24 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.59% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Power of 3 / „knot świecy 4H” (wg filmu: akumulacja → manipulacja → dystrybucja). Gdy dzienny kierunek jest
wzrostowy, nowa świeca 4H zwykle najpierw robi dolny knot (fałszywy ruch w dół, który zbiera płynność pod ważnym
dołkiem), a potem zamyka się wysoko. Wchodzimy long, gdy w pierwszych godzinach nowej świecy 4H cena zebrała dołek
(poprzedniej świecy 4H albo ostatnich 24 h), a świeca H1 zamyka się z powrotem nad nim (zmiana kierunku). Lustrzanie short.
Różnice (ograniczenia IA5): tylko H1 (autor wchodzi na 1 min po luce FVG i „zmianie stanu dostawy”); stop „pod dołkiem
świecy 4H” i cel przybliżone przez ATR14 albo wyjście na koniec świecy 4H (2–4 świece H1)."""

import numpy as np
import pandas as pd

PARAMS = {
    "bias": ["dzien", "brak"],          # dzien: wczorajsza świeca dzienna wzrostowa → tylko long (spadkowa → short)
    "dolek": ["4h", "24h"],             # zebrany poziom: dołek/szczyt poprzedniej świecy 4H albo ostatnich 24 h
}

# koniec świecy 4H (po 2–4 h) albo TP/SL w ATR14 (stop pod dołkiem ≈ 1 ATR)
EXITS = [{"kind": "time", "n": n, "cap": n} for n in (2, 3, 4)] + \
        [{"kind": "atr", "n": 14, "tp": tp, "sl": 1.0, "cap": 24} for tp in (1.0, 1.5, 2.0)]


def signals(df, p, ind):
    h, lo, o, c = df.high, df.low, df.open, df.close
    blk = df.index.floor("4h")                       # świece 4H od 00:00 UTC
    pos = ((df.index - blk) / pd.Timedelta(hours=1)).astype(int)
    g = pd.Series(blk, index=df.index)
    blk_low = lo.groupby(g).cummin()                 # dołek bieżącej świecy 4H do tej godziny
    blk_high = h.groupby(g).cummax()
    if p["dolek"] == "4h":
        b4h = h.groupby(g).max().shift(1)
        b4l = lo.groupby(g).min().shift(1)
        lvl_lo = b4l.reindex(blk).set_axis(df.index)  # poprzednia, zamknięta świeca 4H
        lvl_hi = b4h.reindex(blk).set_axis(df.index)
    else:
        lvl_lo = lo.shift(1).rolling(24).min().where(pos == 0).ffill()
        lvl_hi = h.shift(1).rolling(24).max().where(pos == 0).ffill()
    early = pos <= 2                                  # pierwsze 3 godziny świecy 4H
    bull = early & (blk_low < lvl_lo) & (c > lvl_lo) & (c > o)
    bear = early & (blk_high > lvl_hi) & (c < lvl_hi) & (c < o)
    if p["bias"] == "dzien":
        day = df.index.floor("D")
        dg = pd.Series(day, index=df.index)
        d_up = (c.groupby(dg).last() > o.groupby(dg).first()).shift(1)
        up = d_up.reindex(day).set_axis(df.index).fillna(False).astype(bool)
        dn = (~up) & d_up.reindex(day).set_axis(df.index).notna()
        bull &= up
        bear &= dn
    s = bull.astype("int8") - bear.astype("int8")
    first = (s != 0).astype(int).groupby(g).cumsum() == 1   # jeden sygnał na świecę 4H
    return s.where(first & (s != 0), 0).astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
