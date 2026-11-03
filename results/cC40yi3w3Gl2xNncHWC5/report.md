# Raport strategii: 3 Candles

Run `20261103-173126` · silnik 0.9.0 · kod `1c1f87b01cced769` · dane `e76fc4183c4b5596`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -3.39 |
| percentyl benchmarku ≥ 95 | ✘ | 15.50 |
| PBO < 0,3 | ✔ | 0.12 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -3.62 |

## Hipoteza

CRT (Candle Range Theory, „Nitro Trades”), przeniesione na H1 i FX. Świeca 1 wyznacza zakres (high–low).
Świeca 2 wybija jego dołek (zbiera zlecenia kupujących), ale zamyka się z powrotem w zakresie — sprzedający nie
mieli siły. Świeca 3 wybija szczyt świecy 2: potwierdzenie, że rynek „dowozi” zlecenia na drugą stronę zakresu,
do szczytu świecy 1. Lustrzanie dla short. Autor: cel = przeciwny koniec zakresu świecy 1, stop tak, by zysk/ryzyko
= 1,5, sesja Nowy Jork 9:30–12:00 ET, tylko pierwszy układ dnia, kierunek zgodny z ostatnim zebraniem płynności H1.
Różnice (ograniczenia IA5): tylko H1 (bez 15/30 min i bez „rebreak” na 1 min); wejście na open świecy po zamknięciu
świecy 3 ponad szczytem świecy 2 (silnik nie zna zleceń stop w trakcie świecy); cel i stop jako wielokrotności ATR14
w proporcji 1,5 : 1 zamiast poziomów ceny (silnik nie przyjmuje TP/SL z sygnału).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 16** (4 wejścia × 4 wyjść).

- Pominięte sygnały, średnio na wariant: 7 (limit otwartych pozycji w parze), 0.6 (brak danych do wyjścia); 10 wejść w rozgrzewce ATR, 10804 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 3.6 (przerwa w dostępie do danych), 0.4 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 2× SL 1.333× max 24 | bias=brak, pierwsza=False | 1 181 | -0.15 | -2.62 | 38.6 | 318 | -0.23 | -3.39 |
| 2 | ATR14 TP 2× SL 1.333× max 24 | bias=zebranie, pierwsza=False | 310 | -0.16 | -3.21 | 38.4 | 92 | -0.16 | -0.99 |
| 3 | ATR14 TP 2× SL 1.333× max 24 | bias=zebranie, pierwsza=True | 309 | -0.16 | -3.45 | 38.2 | 92 | -0.16 | -0.99 |
| 4 | ATR14 TP 2× SL 1.333× max 24 | bias=brak, pierwsza=True | 1 157 | -0.16 | -2.96 | 38.0 | 314 | -0.23 | -3.55 |
| 5 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, pierwsza=False | 1 207 | -0.18 | -2.45 | 37.8 | 324 | -0.27 | -2.67 |
| 6 | ATR14 TP 1.5× SL 1× max 24 | bias=brak, pierwsza=True | 1 173 | -0.18 | -2.57 | 37.6 | 317 | -0.27 | -2.75 |
| 7 | ATR14 TP 1.5× SL 1× max 24 | bias=zebranie, pierwsza=False | 313 | -0.21 | -3.72 | 36.4 | 92 | -0.12 | -0.25 |
| 8 | ATR14 TP 1.5× SL 1× max 24 | bias=zebranie, pierwsza=True | 311 | -0.22 | -3.87 | 36.3 | 92 | -0.12 | -0.25 |
| 9 | ATR14 TP 1× SL 0.667× max 24 | bias=brak, pierwsza=False | 1 224 | -0.22 | -1.85 | 38.5 | 330 | -0.39 | -2.77 |
| 10 | ATR14 TP 1× SL 0.667× max 24 | bias=brak, pierwsza=True | 1 179 | -0.22 | -2.00 | 38.2 | 321 | -0.40 | -2.92 |

## Najlepszy wariant IS: ATR14 TP 2× SL 1.333× max 24 (bias=brak, pierwsza=False)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 184 | -3.0 | -546.9 | 36.4 |
| EURGBP | 197 | -2.7 | -534.9 | 36.0 |
| EURJPY | 192 | -6.2 | -1 192.8 | 35.9 |
| EURUSD | 154 | 0.1 | 18.2 | 44.2 |
| GBPUSD | 188 | 1.0 | 180.7 | 43.1 |
| USDCAD | 186 | -2.8 | -512.0 | 38.7 |
| USDCHF | 199 | -4.8 | -955.2 | 34.7 |
| USDJPY | 199 | -3.2 | -633.5 | 37.7 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 143 | -2.8 | -395.0 | 39.9 |
| 2025 | 769 | -2.7 | -2 046.5 | 38.2 |
| 2026 | 587 | -3.0 | -1 735.0 | 37.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 1181 | -2.6 | -3 098.9 | 38.6 |
| OOS | 318 | -3.4 | -1 077.5 | 36.5 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 5 460 | -45.4 | -25.9 | -47.8 | -2.13 | 0 |
| 10.0% | 2 902 | -71.0 | -45.9 | -73.5 | -2.14 | 0 |
| 15.0% | 1 487 | -85.1 | -61.2 | -87.0 | -2.15 | 1 |
| 20.0% | 863 | -91.4 | -70.4 | -92.8 | -2.05 | 28 |
| 30.0% | 317 | -96.8 | -82.0 | -97.4 | -2.14 | 215 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -2.79 pips/transakcję, percentyl **15.5** (losowe: 5%=-3.24, mediana=-2.08, 95%=-1.02).

- **Deflated Sharpe Ratio**: 0.000 (Sharpe na transakcję -0.124, próg przy 16 próbach 0.138).

- **PBO** (CSCV, 16 bloków, 16 wariantów): 0.123 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 694 transakcji, śr. -3.16 pips, -0.21 R.

- **Bootstrap 95%** średnich pipsów: całość [-4.24; -1.36], OOS [-5.81; -0.93].

- **Spread**: ×1 -2.79, ×1,5 -3.62, ×2 -4.45 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.33% transakcji.

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
w proporcji 1,5 : 1 zamiast poziomów ceny (silnik nie przyjmuje TP/SL z sygnału)."""

import numpy as np
import pandas as pd

HOURS = (15, 18)   # wejścia 15:00–17:59 czasu polskiego ≈ 9:00–11:59 ET (sesja Nowy Jork autora)

PARAMS = {
    "bias": ["brak", "zebranie"],   # zebranie = ostatnie 24 h zebrały dołek/szczyt poprzednich 24 h i cena wróciła
    "pierwsza": [True, False],      # tylko pierwszy układ dnia (jak autor) albo każdy
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
