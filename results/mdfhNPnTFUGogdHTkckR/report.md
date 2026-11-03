# Raport strategii: CRT v2

Run `20261103-173854` · silnik 0.9.0 · kod `1440fa7858118076` · dane `e76fc4183c4b5596`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -1.77 |
| percentyl benchmarku ≥ 95 | ✘ | 62.30 |
| PBO < 0,3 | ✘ | 0.31 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -2.29 |

## Hipoteza

CRT (Candle Range Theory, „Nitro Trades”), przeniesione na H1 i FX. Świeca 1 wyznacza zakres (high–low).
Świeca 2 wybija jego dołek (zbiera zlecenia kupujących), ale zamyka się z powrotem w zakresie — sprzedający nie
mieli siły. Świeca 3 wybija szczyt świecy 2: potwierdzenie, że rynek „dowozi” zlecenia na drugą stronę zakresu,
do szczytu świecy 1. Lustrzanie dla short. Autor: cel = przeciwny koniec zakresu świecy 1, stop tak, by zysk/ryzyko
= 1,5, sesja Nowy Jork 9:30–12:00 ET, tylko pierwszy układ dnia, kierunek zgodny z ostatnim zebraniem płynności H1.
Różnice (ograniczenia IA5): tylko H1 (bez 15/30 min i bez „rebreak” na 1 min); wejście na open świecy po zamknięciu
świecy 3 ponad szczytem świecy 2 (silnik nie zna zleceń stop w trakcie świecy); cel i stop jako wielokrotności ATR14
w proporcji 1,5 : 1 zamiast poziomów ceny (silnik nie przyjmuje TP/SL z sygnału).
Wersja 2 (po 🔴 wersji 1): filtr odległości od SMA200 (≈ 8 dni H1). Pomysł Michała: „poszarpany rynek” autora to u nas
cena przy długiej średniej — handlujemy tylko blisko niej (|zamknięcie − SMA200| ≤ 1 × ATR14). Dla porównania wariant
odwrotny (daleko: ≥ 3 × ATR14) i bez filtra. OOS nie jest czysty (filtr dodany po obejrzeniu wersji 1).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 48** (12 wejścia × 4 wyjść).

- Pominięte sygnały, średnio na wariant: 4 (limit otwartych pozycji w parze), 0.3 (brak danych do wyjścia); 10 wejść w rozgrzewce ATR, 18406 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 2.1 (przerwa w dostępie do danych), 0.2 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 2× SL 1.333× max 24 | bias=zebranie, pierwsza=True, sma200=daleko | 141 | -0.01 | -1.35 | 44.0 | 51 | -0.21 | -1.77 |
| 2 | ATR14 TP 2× SL 1.333× max 24 | bias=zebranie, pierwsza=False, sma200=daleko | 141 | -0.01 | -1.35 | 44.0 | 51 | -0.21 | -1.77 |
| 3 | ATR14 TP 1.5× SL 1× max 24 | bias=zebranie, pierwsza=True, sma200=daleko | 143 | -0.02 | -1.85 | 44.1 | 51 | -0.15 | -0.34 |
| 4 | ATR14 TP 1.5× SL 1× max 24 | bias=zebranie, pierwsza=False, sma200=daleko | 143 | -0.02 | -1.85 | 44.1 | 51 | -0.15 | -0.34 |
| 5 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, pierwsza=False, sma200=daleko | 617 | -0.11 | -1.59 | 40.2 | 201 | -0.32 | -3.29 |
| 6 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, pierwsza=True, sma200=daleko | 603 | -0.11 | -1.63 | 40.1 | 196 | -0.32 | -3.41 |
| 7 | ATR14 TP 2× SL 1.333× max 24 | bias=brak, pierwsza=False, sma200=daleko | 599 | -0.13 | -2.82 | 39.2 | 199 | -0.29 | -4.30 |
| 8 | ATR14 TP 1× SL 0.667× max 24 | bias=brak, pierwsza=True, sma200=blisko | 212 | -0.13 | -1.16 | 42.0 | 41 | -0.14 | 0.16 |
| 9 | ATR14 TP 1× SL 0.667× max 24 | bias=brak, pierwsza=False, sma200=blisko | 212 | -0.13 | -1.16 | 42.0 | 41 | -0.14 | 0.16 |
| 10 | ATR14 TP 2× SL 1.333× max 24 | bias=brak, pierwsza=True, sma200=daleko | 590 | -0.14 | -2.96 | 39.0 | 196 | -0.29 | -4.52 |

## Najlepszy wariant IS: ATR14 TP 2× SL 1.333× max 24 (bias=zebranie, pierwsza=True, sma200=daleko)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 24 | 0.5 | 12.1 | 50.0 |
| EURGBP | 24 | -5.6 | -135.0 | 29.2 |
| EURJPY | 21 | -6.9 | -145.9 | 38.1 |
| EURUSD | 18 | 3.7 | 66.1 | 55.6 |
| GBPUSD | 29 | -0.3 | -8.1 | 41.4 |
| USDCAD | 26 | -7.1 | -185.2 | 38.5 |
| USDCHF | 26 | -3.6 | -93.3 | 38.5 |
| USDJPY | 24 | 8.7 | 208.9 | 50.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 14 | -19.9 | -279.2 | 21.4 |
| 2025 | 95 | 0.1 | 5.2 | 44.2 |
| 2026 | 83 | -0.1 | -6.4 | 43.4 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 141 | -1.3 | -190.3 | 44.0 |
| OOS | 51 | -1.8 | -90.0 | 37.3 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 9 563 | -4.4 | -2.3 | -5.9 | -0.55 | 0 |
| 10.0% | 9 125 | -8.7 | -4.6 | -11.6 | -0.55 | 0 |
| 15.0% | 8 689 | -13.1 | -6.9 | -17.0 | -0.55 | 0 |
| 20.0% | 8 255 | -17.4 | -9.3 | -22.3 | -0.55 | 0 |
| 30.0% | 7 398 | -26.0 | -14.3 | -32.2 | -0.54 | 2 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.46 pips/transakcję, percentyl **62.3** (losowe: 5%=-5.29, mediana=-2.12, 95%=1.26).

- **Deflated Sharpe Ratio**: 0.001 (Sharpe na transakcję -0.010, próg przy 48 próbach 0.259).

- **PBO** (CSCV, 16 bloków, 48 wariantów): 0.309 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 141 transakcji, śr. -1.88 pips, -0.11 R.

- **Bootstrap 95%** średnich pipsów: całość [-5.44; 2.74], OOS [-7.70; 4.76].

- **Spread**: ×1 -1.46, ×1,5 -2.29, ×2 -3.13 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 1.04% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """CRT (Candle Range Theory, „Nitro Trades”), przeniesione na H1 i FX. Świeca 1 wyznacza zakres (high–low).
Świeca 2 wybija jego dołek (zbiera zlecenia kupujących), ale zamyka się z powrotem w zakresie — sprzedający nie
mieli siły. Świeca 3 wybija szczyt świecy 2: potwierdzenie, że rynek „dowozi” zlecenia na drugą stronę zakresu,
do szczytu świecy 1. Lustrzanie dla short. Autor: cel = przeciwny koniec zakresu świecy 1, stop tak, by zysk/ryzyko
= 1,5, sesja Nowy Jork 9:30–12:00 ET, tylko pierwszy układ dnia, kierunek zgodny z ostatnim zebraniem płynności H1.
Różnice (ograniczenia IA5): tylko H1 (bez 15/30 min i bez „rebreak” na 1 min); wejście na open świecy po zamknięciu
świecy 3 ponad szczytem świecy 2 (silnik nie zna zleceń stop w trakcie świecy); cel i stop jako wielokrotności ATR14
w proporcji 1,5 : 1 zamiast poziomów ceny (silnik nie przyjmuje TP/SL z sygnału).
Wersja 2 (po 🔴 wersji 1): filtr odległości od SMA200 (≈ 8 dni H1). Pomysł Michała: „poszarpany rynek” autora to u nas
cena przy długiej średniej — handlujemy tylko blisko niej (|zamknięcie − SMA200| ≤ 1 × ATR14). Dla porównania wariant
odwrotny (daleko: ≥ 3 × ATR14) i bez filtra. OOS nie jest czysty (filtr dodany po obejrzeniu wersji 1)."""

import numpy as np
import pandas as pd

HOURS = (15, 18)   # wejścia 15:00–17:59 czasu polskiego ≈ 9:00–11:59 ET (sesja Nowy Jork autora)

PARAMS = {
    "bias": ["brak", "zebranie"],   # zebranie = ostatnie 24 h zebrały dołek/szczyt poprzednich 24 h i cena wróciła
    "pierwsza": [True, False],      # tylko pierwszy układ dnia (jak autor) albo każdy
    "sma200": ["blisko", "daleko", "brak"],   # blisko: |close − SMA200| ≤ 1 × ATR14; daleko: ≥ 3 × ATR14
}

# zysk / ryzyko = 1,5 (cel 1,5 × stop), bez innych wyjść; limit 24 świec
EXITS = [{"kind": "atr", "n": 14, "tp": tp, "sl": round(tp / 1.5, 3), "cap": 24} for tp in (0.75, 1.0, 1.5, 2.0)]


def signals(df, p, ind):
    h, lo, c = df.high, df.low, df.close
    h1, l1 = h.shift(2), lo.shift(2)                 # świeca 1
    h2, l2, c2 = h.shift(1), lo.shift(1), c.shift(1)  # świeca 2
    inside = (c2 > l1) & (c2 < h1)
    bull = (l2 < l1) & inside & (c > h2)             # świeca 2 zebrała dołek, świeca 3 zamknęła ponad jej szczytem
    bear = (h2 > h1) & inside & (c < l2)
    if p["bias"] == "zebranie":
        prev_low = lo.shift(24).rolling(24).min()     # dołek poprzednich 24 h
        prev_high = h.shift(24).rolling(24).max()
        swept_low = (lo.rolling(24).min() < prev_low) & (c > prev_low)
        swept_high = (h.rolling(24).max() > prev_high) & (c < prev_high)
        bull &= swept_low & ~swept_high
        bear &= swept_high & ~swept_low
    dist = (c - ind.sma(c, 200)).abs() / ind.atr(df, 14)
    if p["sma200"] == "blisko":
        bull &= dist <= 1.0
        bear &= dist <= 1.0
    elif p["sma200"] == "daleko":
        bull &= dist >= 3.0
        bear &= dist >= 3.0
    s = bull.astype("int8") - bear.astype("int8")
    if p["pierwsza"]:                                # pierwszy układ w oknie danego dnia (wejście na następnej świecy)
        nxt = (df.index + pd.Timedelta(hours=1)).tz_convert("Europe/Warsaw")
        ok = (nxt.hour >= 15) & (nxt.hour < 18)
        s = s.where(ok, 0)
        day = pd.Series(nxt.normalize(), index=df.index)
        first = (s != 0).astype(int).groupby(day).cumsum() == 1
        s = s.where(first & (s != 0), 0)
    return s.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
