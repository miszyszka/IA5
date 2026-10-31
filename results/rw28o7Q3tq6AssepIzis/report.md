# Raport strategii: Strategia 6

Run `20261031-102844` · silnik 0.8.0 · kod `f744cef3ce28e241` · dane `fca2a7086f281a13`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -7.10 |
| percentyl benchmarku ≥ 95 | ✘ | 35.50 |
| PBO < 0,3 | ✘ | 0.52 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -15.25 |

## Hipoteza

Kursy walut mają trendy trwające tygodnie (przepływy kapitału, polityka banków centralnych zmienia się
powoli), a rynek reaguje na nie z opóźnieniem. Wybicie ceny z kanału kilku dni w kierunku trendu dziennego
łapie początek takiego ruchu; zysk daje kilka dużych ruchów, nie trafność. Wersja 5b: stop początkowy i stop
kroczący w skali DNIA (ok. 2–3 dzienne ATR), bo trend trwający tygodnie musi przetrwać zwykłe wahania w ciągu
dnia — w wersji 5 stop 2–4 × ATR godzinowego (0,3–0,7 dziennego zakresu) zamykał pozycję po medianie 18 h.
Uwaga: zmiana stopu powstała po obejrzeniu wyniku wersji 5 na całej historii (także OOS) — OOS tej wersji nie jest
czysty; liczba prób łącznie z wersją 5: 96. Rozstrzyga forward test po zamrożeniu (W4).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-10-30; źródło: yahoo.

- In-sample do 2026-04-30, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 33, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 30, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 48** (8 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 1,073 (limit otwartych pozycji w parze), 31.8 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 112.0 (przerwa w dostępie do danych), 1.5 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 SL 10× kroczący 20× max 480 | kanal=120, filtr_d1=False, sesja=wszystkie | 198 | -0.09 | -16.77 | 39.9 | 63 | 0.02 | -7.10 |
| 2 | ATR14 SL 15× kroczący 10× max 480 | kanal=120, filtr_d1=False, sesja=wszystkie | 297 | -0.09 | -20.43 | 33.7 | 88 | -0.00 | 4.92 |
| 3 | ATR14 SL 15× kroczący 15× max 480 | kanal=240, filtr_d1=False, sesja=wszystkie | 165 | -0.09 | -25.38 | 39.4 | 52 | 0.10 | 11.62 |
| 4 | ATR14 SL 15× kroczący 10× max 480 | kanal=120, filtr_d1=True, sesja=wszystkie | 180 | -0.10 | -21.71 | 34.4 | 56 | -0.08 | -15.26 |
| 5 | ATR14 SL 15× kroczący 10× max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 276 | -0.10 | -22.11 | 33.0 | 84 | -0.02 | 6.77 |
| 6 | ATR14 SL 15× kroczący 20× max 480 | kanal=120, filtr_d1=False, sesja=7-20 UTC | 152 | -0.11 | -22.46 | 47.4 | 46 | -0.06 | -8.16 |
| 7 | ATR14 SL 15× kroczący 10× max 480 | kanal=120, filtr_d1=True, sesja=7-20 UTC | 164 | -0.12 | -21.66 | 31.7 | 55 | -0.11 | -17.92 |
| 8 | ATR14 SL 15× kroczący 15× max 480 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 154 | -0.12 | -27.15 | 39.0 | 49 | -0.00 | -7.79 |
| 9 | ATR14 SL 15× kroczący 20× max 480 | kanal=120, filtr_d1=False, sesja=wszystkie | 162 | -0.13 | -33.62 | 42.6 | 50 | 0.01 | -13.02 |
| 10 | ATR14 SL 15× kroczący 20× max 480 | kanal=240, filtr_d1=False, sesja=7-20 UTC | 135 | -0.13 | -32.78 | 43.7 | 44 | -0.09 | -15.98 |

## Najlepszy wariant IS: ATR14 SL 10× kroczący 20× max 480 (kanal=120, filtr_d1=False, sesja=wszystkie)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 39 | -55.1 | -2 147.7 | 33.3 |
| EURGBP | 28 | -2.0 | -55.5 | 42.9 |
| EURJPY | 32 | -12.4 | -396.5 | 37.5 |
| EURUSD | 35 | 14.8 | 516.5 | 42.9 |
| GBPUSD | 37 | -13.7 | -505.4 | 40.5 |
| USDCAD | 28 | -0.1 | -2.2 | 50.0 |
| USDCHF | 30 | 5.3 | 158.8 | 40.0 |
| USDJPY | 32 | -41.7 | -1 334.8 | 34.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 19 | -50.5 | -959.5 | 36.8 |
| 2025 | 127 | 16.8 | 2 130.1 | 49.6 |
| 2026 | 115 | -42.9 | -4 937.2 | 29.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 198 | -16.8 | -3 319.5 | 39.9 |
| OOS | 63 | -7.1 | -447.1 | 39.7 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 4 892 | -51.1 | -30.2 | -61.4 | -0.78 | 0 |
| 10.0% | 1 819 | -81.8 | -57.6 | -88.0 | -0.74 | 2 |
| 15.0% | 505 | -94.9 | -77.8 | -95.8 | -1.04 | 65 |
| 20.0% | 1 064 | -89.4 | -67.6 | -92.0 | -0.60 | 119 |
| 30.0% | 1 046 | -89.5 | -67.9 | -94.2 | -0.51 | 171 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -14.43 pips/transakcję, percentyl **35.5** (losowe: 5%=-28.83, mediana=-10.01, 95%=9.84).

- **Deflated Sharpe Ratio**: 0.002 (Sharpe na transakcję -0.076, próg przy 48 próbach 0.138).

- **PBO** (CSCV, 16 bloków, 48 wariantów): 0.520 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 151 transakcji, śr. -27.00 pips, -0.13 R.

- **Bootstrap 95%** średnich pipsów: całość [-36.66; 8.32], OOS [-46.37; 34.87].

- **Spread**: ×1 -14.43, ×1,5 -15.25, ×2 -16.06 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

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
