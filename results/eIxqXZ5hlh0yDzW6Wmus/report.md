# Raport strategii: strategia 3

Run `20261027-181812` · silnik 0.6.0 · kod `145f53429abe3979` · dane `5d2ac9e95dedc57f`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -0.75 |
| percentyl benchmarku ≥ 95 | ✔ | 95.90 |
| PBO < 0,3 | ✘ | 0.79 |
| DSR ≥ 0,95 | ✘ | 0.09 |
| dodatni przy spreadzie ×1,5 | ✔ | 2.89 |

## Hipoteza

W wyraźnym trendzie (EMA200 na H1 i EMA50 na H4) skrajny ruch przeciw trendowi (RSI14 za 70/30)
zwykle się wyczerpuje — ale wejście w chwili przebicia łapie też te ruchy, które są początkiem odwrócenia trendu
i dają największe straty. Czekamy więc na dowód wyczerpania: RSI wraca zza poziomu, a świeca zamyka się
w kierunku trendu. Każda pozycja ma stop cenowy w ATR, więc pojedyncza pomyłka kosztuje z góry znaną kwotę.

## Dane i model wykonania

- Pary: EURUSD; świece H1 od 2003-05-04 do 2026-10-26; źródło: dukascopy.

- In-sample do 2020-12-12, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 276/282 mies. zatwierdzonych, 8 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 6 przerw w dostępie do danych (3147 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1248** (32 wejścia × 39 wyjść).

- Pominięte sygnały, średnio na wariant: 20 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 2× SL 1× max 120 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=False, sesja=7-20 UTC | 83 | 0.11 | 5.20 | 38.6 | 38 | -0.19 | -0.75 |
| 2 | ATR14 TP 2× SL 1× max 120 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=True, sesja=7-20 UTC | 83 | 0.11 | 5.20 | 38.6 | 38 | -0.19 | -0.75 |
| 3 | ATR14 TP 2× SL 1× max 48 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=False, sesja=7-20 UTC | 83 | 0.10 | 4.71 | 38.6 | 38 | -0.19 | -0.75 |
| 4 | ATR14 TP 2× SL 1× max 48 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=True, sesja=7-20 UTC | 83 | 0.10 | 4.71 | 38.6 | 38 | -0.19 | -0.75 |
| 5 | ATR14 TP 1.5× SL 2× max 120 | wejscie=powrot, poziom=75, nachylenie=0.3, h4=False, sesja=wszystkie | 36 | 0.09 | 7.02 | 63.9 | 15 | 0.26 | 14.10 |
| 6 | ATR14 TP 1.5× SL 2× max 120 | wejscie=powrot, poziom=75, nachylenie=0.3, h4=True, sesja=wszystkie | 36 | 0.09 | 7.02 | 63.9 | 15 | 0.26 | 14.10 |
| 7 | ATR14 TP 1.5× SL 2× max 48 | wejscie=powrot, poziom=75, nachylenie=0.3, h4=False, sesja=wszystkie | 36 | 0.08 | 5.96 | 63.9 | 15 | 0.32 | 17.36 |
| 8 | ATR14 TP 1.5× SL 2× max 48 | wejscie=powrot, poziom=75, nachylenie=0.3, h4=True, sesja=wszystkie | 36 | 0.08 | 5.96 | 63.9 | 15 | 0.32 | 17.36 |
| 9 | ATR14 TP 3× SL 1× max 48 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=False, sesja=7-20 UTC | 83 | 0.08 | 5.45 | 28.9 | 38 | -0.33 | -0.92 |
| 10 | ATR14 TP 3× SL 1× max 48 | wejscie=przebicie, poziom=75, nachylenie=0.15, h4=True, sesja=7-20 UTC | 83 | 0.08 | 5.45 | 28.9 | 38 | -0.33 | -0.92 |

## Najlepszy wariant IS: ATR14 TP 2× SL 1× max 120 (wejscie=przebicie, poziom=75, nachylenie=0.15, h4=False, sesja=7-20 UTC)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 121 | 3.3 | 403.6 | 35.5 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 3 | 50.7 | 152.2 | 100.0 |
| 2004 | 6 | 17.1 | 102.6 | 50.0 |
| 2005 | 6 | 0.0 | 0.2 | 33.3 |
| 2006 | 5 | 20.4 | 101.9 | 60.0 |
| 2007 | 7 | -9.2 | -64.4 | 14.3 |
| 2008 | 6 | 17.4 | 104.4 | 50.0 |
| 2009 | 4 | -32.8 | -131.4 | 0.0 |
| 2010 | 2 | 9.0 | 17.9 | 50.0 |
| 2011 | 6 | 13.4 | 80.4 | 50.0 |
| 2012 | 6 | 10.8 | 64.5 | 50.0 |
| 2013 | 2 | 7.6 | 15.1 | 50.0 |
| 2014 | 6 | 8.4 | 50.2 | 50.0 |
| 2015 | 3 | 22.0 | 65.9 | 66.7 |
| 2016 | 6 | -11.0 | -66.2 | 16.7 |
| 2017 | 3 | 6.1 | 18.2 | 33.3 |
| 2018 | 3 | -0.3 | -0.8 | 33.3 |
| 2019 | 6 | -6.6 | -39.6 | 16.7 |
| 2020 | 3 | -13.1 | -39.3 | 0.0 |
| 2021 | 5 | -5.3 | -26.5 | 20.0 |
| 2022 | 8 | 19.6 | 157.2 | 62.5 |
| 2023 | 7 | -2.9 | -20.1 | 28.6 |
| 2024 | 10 | -5.3 | -53.0 | 20.0 |
| 2025 | 8 | -10.7 | -85.9 | 12.5 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 83 | 5.2 | 432.0 | 38.6 |
| OOS | 38 | -0.7 | -28.4 | 28.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 495 | 5.0 | 0.2 | -2.5 | 0.18 | 0 |
| 10.0% | 10 990 | 9.9 | 0.4 | -5.0 | 0.18 | 0 |
| 15.0% | 11 480 | 14.8 | 0.6 | -7.4 | 0.18 | 0 |
| 20.0% | 11 965 | 19.7 | 0.8 | -9.7 | 0.18 | 0 |
| 30.0% | 12 910 | 29.1 | 1.2 | -14.3 | 0.18 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 3.34 pips/transakcję, percentyl **95.9** (losowe: 5%=-5.83, mediana=-1.52, 95%=3.08).

- **Deflated Sharpe Ratio**: 0.091 (Sharpe na transakcję 0.076, próg przy 1180 próbach 0.221).

- **PBO** (CSCV, 16 bloków, 1248 wariantów): 0.793 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 50 transakcji, śr. 1.60 pips, -0.09 R.

- **Bootstrap 95%** średnich pipsów: całość [-2.80; 10.00], OOS [-8.48; 8.33].

- **Spread**: ×1 3.34, ×1,5 2.89, ×2 2.44, faktyczny 3.59 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """W wyraźnym trendzie (EMA200 na H1 i EMA50 na H4) skrajny ruch przeciw trendowi (RSI14 za 70/30)
zwykle się wyczerpuje — ale wejście w chwili przebicia łapie też te ruchy, które są początkiem odwrócenia trendu
i dają największe straty. Czekamy więc na dowód wyczerpania: RSI wraca zza poziomu, a świeca zamyka się
w kierunku trendu. Każda pozycja ma stop cenowy w ATR, więc pojedyncza pomyłka kosztuje z góry znaną kwotę."""

import numpy as np

HOURS = False   # okno godzin sterowane parametrem „sesja” — żeby porównać obie wersje w jednym liczeniu

PARAMS = {
    "wejscie": ["przebicie", "powrot"],     # przebicie = jak dotąd (RSI wchodzi za poziom); powrot = RSI wraca zza poziomu
    "poziom": [70, 75],                     # short za 70/75, long za 30/25
    "nachylenie": [0.15, 0.3],              # zmiana EMA200 na 10 świec, w ATR14 — siła trendu H1
    "h4": [False, True],                    # dodatkowo trend H4 (EMA50 rośnie/spada na 3 zamkniętych świecach H4)
    "sesja": ["wszystkie", "7-20 UTC"],      # wejścia tylko w sesji europejskiej i amerykańskiej
}

# Wyjścia — każde ze stopem cenowym (największe straty poprzedniej wersji to brak SL: do −332 pipsów).
EXITS = (
    [{"kind": "atr", "n": 14, "tp": tp, "sl": sl, "cap": cap}
     for tp in (1.0, 1.5, 2.0, 3.0) for sl in (1.0, 1.5, 2.0, 3.0) for cap in (48, 120)]
    + [{"kind": "rsi_streak", "n": 14, "tp": tp, "sl": sl, "run": 6, "level": 70, "cap": 120}
       for tp in (1.5, 2.0) for sl in (1.5, 2.0)]
    + [{"kind": "rsi50", "n": 14, "sl": sl, "cap": 48} for sl in (1.0, 1.5, 2.0)]
)


def signals(df, p, ind):
    atr = ind.atr(df, 14)
    ema = ind.ema(df.close, 200)
    slope = (ema - ema.shift(10)) / atr
    up = slope > p["nachylenie"]
    down = slope < -p["nachylenie"]

    if p["h4"]:
        # H4 bez look-ahead: tylko zamknięte świece H4 (shift(1)), przeniesione na H1
        h4 = df.close.resample("4h").last().dropna()
        e4 = ind.ema(h4, 50)
        h4_up = ind.rising(e4, 3).shift(1).reindex(df.index, method="ffill").fillna(False).astype(bool)
        h4_down = ind.falling(e4, 3).shift(1).reindex(df.index, method="ffill").fillna(False).astype(bool)
        up, down = up & h4_up, down & h4_down

    rsi = ind.rsi(df.close, 14)
    hi, lo = p["poziom"], 100 - p["poziom"]
    # przesada w trendzie: RSI wchodzi za poziom, gdy trend jest wyraźny (trend sprawdzany w tej świecy)
    setup_short = ind.cross_above(rsi, hi) & down
    setup_long = ind.cross_below(rsi, lo) & up
    if p["wejscie"] == "przebicie":
        short, long_ = setup_short, setup_long
    else:
        # dowód wyczerpania: w ciągu 12 świec od przesady RSI wraca zza poziomu,
        # a świeca powrotu zamyka się w kierunku trendu
        recent_s = setup_short.astype(int).rolling(12, min_periods=1).max().shift(1).fillna(0) > 0
        recent_l = setup_long.astype(int).rolling(12, min_periods=1).max().shift(1).fillna(0) > 0
        short = ind.cross_below(rsi, hi) & (df.close < df.open) & recent_s
        long_ = ind.cross_above(rsi, lo) & (df.close > df.open) & recent_l

    if p["sesja"] != "wszystkie":
        h = ind.hour(df)
        ok = (h >= 7) & (h < 20)
        short, long_ = short & ok, long_ & ok

    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
