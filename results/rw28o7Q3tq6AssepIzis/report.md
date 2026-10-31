# Raport strategii: Strategia 6

Run `20261031-101921` · silnik 0.7.0 · kod `f744cef3ce28e241` · dane `51eede8f48c7f380`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -7.93 |
| percentyl benchmarku ≥ 95 | ✔ | 95.30 |
| PBO < 0,3 | ✘ | 0.61 |
| DSR ≥ 0,95 | ✘ | 0.60 |
| dodatni przy spreadzie ×1,5 | ✔ | 14.87 |

## Hipoteza

Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu; zysk daje kilka dużych ruchów, nie trafność. Wersja 5b: stop początkowy i stop
kroczący w skali DNIA (ok. 2–3 dzienne ATR), bo trend trwający tygodnie musi przetrwać zwykłe wahania w ciągu
dnia — w wersji 5 stop 2–4 × ATR godzinowego (0,3–0,7 dziennego zakresu) zamykał pozycję po medianie 18 h.
Uwaga: zmiana stopu powstała po obejrzeniu wyniku wersji 5 na całej historii (także OOS) — OOS tej wersji nie jest
czysty; liczba prób łącznie z wersją 5: 96. Rozstrzyga forward test po zamrożeniu (W4).

## Dane i model wykonania

- Pary: EURUSD, USDJPY; świece H1 od 2003-05-04 do 2026-09-30; źródło: dukascopy.

- In-sample do 2020-11-23, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: rozstrzygane na M1, w tej samej minucie — SL.

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Dane tylko z zatwierdzonych miesięcy (D-031): EURUSD: 281/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 3 przerw w dostępie do danych (93 h); USDJPY: 141/282 mies. zatwierdzonych, 9 świec uzupełnionych (dziury ≤ 3 h w pobranych dniach), 16 przerw w dostępie do danych (40147 h). Transakcja nachodząca na przerwę w dostępie do danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny bez notowań nie są przerwą (D-032).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 48** (8 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 2,826 (limit otwartych pozycji w parze), 13.6 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 100.8 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 SL 10× kroczący 20× max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 432 | 0.08 | 21.28 | 44.4 | 109 | -0.11 | -7.93 |
| 2 | ATR14 SL 10× kroczący 15× max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 461 | 0.05 | 12.06 | 42.1 | 106 | 0.09 | 19.17 |
| 3 | ATR14 SL 10× kroczący 15× max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 343 | 0.04 | 18.76 | 41.4 | 81 | -0.02 | 7.80 |
| 4 | ATR14 SL 10× kroczący 20× max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 340 | 0.03 | 14.01 | 41.8 | 79 | 0.02 | 13.36 |
| 5 | ATR14 SL 15× kroczący 15× max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 324 | 0.03 | 19.16 | 43.8 | 77 | -0.02 | 7.55 |
| 6 | ATR14 SL 15× kroczący 15× max 480 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 378 | 0.02 | 7.86 | 46.3 | 93 | 0.05 | 14.39 |
| 7 | ATR14 SL 15× kroczący 20× max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 307 | 0.02 | 15.25 | 46.6 | 75 | -0.05 | 0.11 |
| 8 | ATR14 SL 10× kroczący 20× max 480 | kanal=120, filtr_d1=False, sesja=wszystkie | 471 | 0.02 | 7.13 | 40.8 | 109 | 0.03 | 6.39 |
| 9 | ATR14 SL 15× kroczący 15× max 480 | kanal=240, filtr_d1=False, sesja=wszystkie | 413 | 0.01 | 5.65 | 45.8 | 101 | -0.01 | 3.70 |
| 10 | ATR14 SL 10× kroczący 10× max 480 | kanal=240, filtr_d1=True, sesja=7-20 UTC | 348 | 0.01 | 10.21 | 38.5 | 77 | 0.06 | 15.75 |

## Najlepszy wariant IS: ATR14 SL 10× kroczący 20× max 480 (kanal=120, filtr_d1=False, sesja=7-20 UTC)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 371 | 8.5 | 3 159.3 | 42.9 |
| USDJPY | 170 | 30.4 | 5 169.0 | 45.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2003 | 19 | -58.0 | -1 101.6 | 36.8 |
| 2004 | 26 | 81.3 | 2 112.9 | 61.5 |
| 2005 | 27 | -6.3 | -169.2 | 48.1 |
| 2006 | 28 | -6.9 | -192.5 | 35.7 |
| 2007 | 28 | 98.6 | 2 760.9 | 64.3 |
| 2008 | 28 | 104.0 | 2 911.9 | 50.0 |
| 2009 | 27 | 77.2 | 2 084.2 | 51.9 |
| 2010 | 35 | 21.0 | 734.8 | 40.0 |
| 2011 | 20 | 16.0 | 319.2 | 45.0 |
| 2012 | 15 | 62.0 | 929.3 | 46.7 |
| 2013 | 19 | -37.0 | -702.2 | 36.8 |
| 2014 | 19 | 22.1 | 419.0 | 52.6 |
| 2015 | 30 | -11.3 | -340.3 | 33.3 |
| 2016 | 31 | 12.0 | 370.7 | 35.5 |
| 2017 | 24 | -11.7 | -280.5 | 45.8 |
| 2018 | 20 | -21.3 | -425.0 | 35.0 |
| 2019 | 19 | -32.7 | -621.8 | 31.6 |
| 2020 | 18 | 25.0 | 449.5 | 50.0 |
| 2021 | 28 | -9.9 | -276.8 | 35.7 |
| 2022 | 18 | -29.4 | -528.9 | 27.8 |
| 2023 | 17 | -18.7 | -317.4 | 52.9 |
| 2024 | 17 | -25.3 | -430.1 | 29.4 |
| 2025 | 17 | -5.3 | -90.0 | 35.3 |
| 2026 | 11 | 64.8 | 712.4 | 72.7 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 432 | 21.3 | 9 192.5 | 44.4 |
| OOS | 109 | -7.9 | -864.1 | 40.4 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 20 744 | 107.4 | 3.2 | -46.5 | 0.23 | 0 |
| 10.0% | 24 313 | 143.1 | 3.9 | -75.5 | 0.23 | 0 |
| 15.0% | 16 561 | 65.6 | 2.2 | -91.1 | 0.22 | 0 |
| 20.0% | 6 532 | -34.7 | -1.8 | -97.6 | 0.22 | 0 |
| 30.0% | 241 | -97.6 | -14.7 | -99.9 | 0.23 | 1 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 15.39 pips/transakcję, percentyl **95.3** (losowe: 5%=-20.03, mediana=-2.52, 95%=14.85).

- **Deflated Sharpe Ratio**: 0.605 (Sharpe na transakcję 0.065, próg przy 48 próbach 0.053).

- **PBO** (CSCV, 16 bloków, 48 wariantów): 0.614 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 291 transakcji, śr. -5.73 pips, -0.07 R.

- **Bootstrap 95%** średnich pipsów: całość [-5.90; 36.90], OOS [-36.68; 22.73].

- **Spread**: ×1 15.39, ×1,5 14.87, ×2 14.34, faktyczny 18.07 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu; zysk daje kilka dużych ruchów, nie trafność. Wersja 5b: stop początkowy i stop
kroczący w skali DNIA (ok. 2–3 dzienne ATR), bo trend trwający tygodnie musi przetrwać zwykłe wahania w ciągu
dnia — w wersji 5 stop 2–4 × ATR godzinowego (0,3–0,7 dziennego zakresu) zamykał pozycję po medianie 18 h.
Uwaga: zmiana stopu powstała po obejrzeniu wyniku wersji 5 na całej historii (także OOS) — OOS tej wersji nie jest
czysty; liczba prób łącznie z wersją 5: 96. Rozstrzyga forward test po zamrożeniu (W4)."""

HOURS = False   # okno godzin jako parametr „sesja” (jak w wersji 5)

PARAMS = {
    "kanal": [120, 240],                    # wybicie maksimum/minimum z 120 lub 240 poprzednich świec H1 (~5 / ~10 dni)
    "filtr_d1": [False, True],              # trend dzienny: zamknięcie D1 nad EMA50(D1) i EMA50 rośnie (short lustrzanie)
    "sesja": ["wszystkie", "7-20 UTC"],
}

# Stop kroczący (D-035) w skali dziennej: na danych Yahoo ATR dzienny ≈ 5–6 × ATR14 godzinowego, więc
# stop początkowy 10 / 15 × ATR14(H1) ≈ 2 / 2,5–3 dzienne ATR, stop kroczący 10 / 15 / 20 × ATR14(H1) ≈ 2 / 3 / 4 dzienne ATR.
# Bez TP; do 20 dni (480 świec).
EXITS = [{"kind": "trail", "n": 14, "sl": sl, "trail": tr, "cap": 480}
         for sl in (10.0, 15.0) for tr in (10.0, 15.0, 20.0)]


def d1_trend(df, ind):
    """Trend D1 bez look-ahead: tylko zamknięte dni robocze (shift(1)), przeniesione na H1.

    Niedzielne otwarcie tygodnia (1–3 świece) nie jest osobnym dniem — w wersji 5 robiło z niego „dzień” D1
    i skracało EMA50 do ok. 9 tygodni. Świece z niedzieli mają ten sam stan co piątek (bez ryzyka look-ahead).
    """
    d1 = df.close.resample("1D").last().dropna()
    d1 = d1[d1.index.dayofweek < 5]
    e = ind.ema(d1, 50)
    up = ((d1 > e) & ind.rising(e, 5)).shift(1)
    down = ((d1 < e) & ind.falling(e, 5)).shift(1)
    to_h1 = lambda s: s.reindex(df.index, method="ffill").fillna(False).astype(bool)  # noqa: E731
    return to_h1(up), to_h1(down)


def signals(df, p, ind):
    n = p["kanal"]
    top = ind.highest(df.high, n).shift(1)       # maksimum n POPRZEDNICH świec (bez bieżącej)
    bottom = ind.lowest(df.low, n).shift(1)
    long_ = ind.cross_above(df.close, top)        # pierwsze zamknięcie nad kanałem
    short = ind.cross_below(df.close, bottom)

    if p["filtr_d1"]:
        up, down = d1_trend(df, ind)
        long_, short = long_ & up, short & down

    if p["sesja"] != "wszystkie":
        h = ind.hour(df)
        ok = (h >= 7) & (h < 20)
        long_, short = long_ & ok, short & ok

    return long_.astype("int8") - short.astype("int8")

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
