# Raport strategii: D1

Run `20261111-101442` · silnik 0.11.0 · kod `cfbdb537655379dc` · dane `3197cf8521901cb3`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -25.87 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✘ | 0.55 |
| DSR ≥ 0,95 | ✘ | 0.45 |
| dodatni przy spreadzie ×1,5 | ✔ | 268.85 |

## Hipoteza

Kurs walutowy, który odjechał daleko od swojej średniej z ok. 3 lat (756 dni handlu), ma tendencję wracać
w stronę tej średniej: parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale
w skali lat ciągną kurs z powrotem. Cena poniżej średniej = long, powyżej = short (lustrzanie, więc jednostronny dryf
pary nie udaje przewagi). Odchylenie mierzymy trzema sposobami (w %, w ATR14 dziennym, w odchyleniach standardowych
ceny z 756 dni), każdym na 4 progach; wchodzimy trzema sposobami (pierwszy dzień przekroczenia / co najwyżej jedna
pozycja na tydzień dopóki odchylenie trwa — piramidowanie / jak poprzednie, ale tylko w dniu, gdy cena zawraca
w stronę średniej). Bez stop lossa: pozycję zamyka powrót do średniej, TP w ATR albo upływ czasu (20–480 dni).
Hipoteza zapisana PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 10 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 1%, 2%, 5%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 324** (36 wejścia × 9 wyjść).

- Pominięte sygnały, średnio na wariant: 632 (limit otwartych pozycji w parze), 60.4 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 77.6 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 480 świecach | dev=atr, level=0, entry=cross | 219 | 4.89 | 428.98 | 62.1 | 118 | 1.76 | -25.87 |
| 2 | po 480 świecach | dev=pct, level=2, entry=cross | 157 | 4.74 | 451.22 | 65.0 | 38 | -1.69 | -419.00 |
| 3 | ATR14 TP 16× SL 0× max 480 | dev=pct, level=2, entry=cross | 182 | 4.51 | 500.78 | 63.7 | 38 | -1.69 | -419.00 |
| 4 | poziomy TP/SL ze strategii, max 480 | dev=atr, level=3, entry=cross | 90 | 3.84 | 422.91 | 66.7 | 20 | -9.79 | -1 216.02 |
| 5 | poziomy TP/SL ze strategii, max 480 | dev=atr, level=3, entry=weekly | 150 | 3.73 | 394.98 | 67.3 | 23 | -7.71 | -912.20 |
| 6 | ATR14 TP 16× SL 0× max 480 | dev=atr, level=3, entry=weekly | 157 | 3.63 | 400.03 | 68.8 | 25 | -3.78 | -537.55 |
| 7 | poziomy TP/SL ze strategii, max 480 | dev=atr, level=2, entry=cross | 185 | 3.46 | 359.50 | 64.9 | 29 | 0.33 | -494.93 |
| 8 | ATR14 TP 16× SL 0× max 480 | dev=atr, level=2, entry=cross | 184 | 3.46 | 346.98 | 63.0 | 29 | -3.00 | -711.80 |
| 9 | ATR14 TP 16× SL 0× max 480 | dev=atr, level=3, entry=cross | 90 | 3.44 | 389.05 | 66.7 | 21 | -8.56 | -1 107.66 |
| 10 | ATR14 TP 16× SL 0× max 480 | dev=atr, level=3, entry=turn | 132 | 3.40 | 363.95 | 71.2 | 22 | -5.92 | -714.45 |

## Najlepszy wariant IS: po 480 świecach (dev=atr, level=0, entry=cross)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 41 | 314.3 | 12 885.5 | 58.5 |
| EURGBP | 56 | 221.5 | 12 402.8 | 75.0 |
| EURJPY | 54 | -397.9 | -21 485.0 | 46.3 |
| EURUSD | 25 | 1 076.7 | 26 916.4 | 88.0 |
| GBPUSD | 37 | 1 489.3 | 55 103.5 | 91.9 |
| USDCAD | 45 | 338.0 | 15 209.2 | 48.9 |
| USDCHF | 55 | -293.0 | -16 117.5 | 30.9 |
| USDJPY | 24 | 249.1 | 5 978.9 | 58.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2001 | 1 | 1 097.6 | 1 097.6 | 100.0 |
| 2003 | 1 | 329.6 | 329.6 | 100.0 |
| 2004 | 8 | 128.4 | 1 027.0 | 25.0 |
| 2006 | 6 | 152.7 | 916.3 | 100.0 |
| 2007 | 5 | -178.5 | -892.6 | 60.0 |
| 2008 | 12 | -720.5 | -8 646.2 | 25.0 |
| 2009 | 6 | -222.1 | -1 332.8 | 50.0 |
| 2010 | 23 | 687.1 | 15 804.2 | 34.8 |
| 2011 | 10 | -694.0 | -6 940.0 | 20.0 |
| 2012 | 14 | -46.1 | -645.2 | 35.7 |
| 2013 | 27 | 690.7 | 18 649.5 | 81.5 |
| 2014 | 14 | 1 115.4 | 15 614.9 | 85.7 |
| 2015 | 2 | 1 406.2 | 2 812.3 | 100.0 |
| 2016 | 18 | 1 564.2 | 28 155.1 | 94.4 |
| 2017 | 7 | 1 381.6 | 9 671.2 | 100.0 |
| 2018 | 17 | -138.2 | -2 350.0 | 29.4 |
| 2019 | 21 | 381.3 | 8 007.3 | 61.9 |
| 2020 | 19 | 381.7 | 7 251.4 | 84.2 |
| 2021 | 21 | 970.7 | 20 384.0 | 100.0 |
| 2022 | 13 | 1 560.9 | 20 291.4 | 100.0 |
| 2023 | 21 | 44.5 | 934.4 | 47.6 |
| 2024 | 27 | -863.9 | -23 324.4 | 51.9 |
| 2025 | 18 | -181.6 | -3 268.2 | 27.8 |
| 2026 | 26 | -486.7 | -12 653.1 | 34.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 219 | 429.0 | 93 945.9 | 62.1 |
| OOS | 118 | -25.9 | -3 052.2 | 54.2 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 20 599 | 106.0 | 2.7 | -74.7 | -186.1 | 0.24 | 0 |
| 2.0% | -34 073 | -440.7 | -100.0 | -117.4 | -307.7 | -0.17 | 36 |
| 5.0% | -200 233 | -2 102.3 | -100.0 | -172.9 | -650.3 | -0.12 | 169 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 269.71 pips/transakcję, percentyl **100.0** (losowe: 5%=-213.71, mediana=-96.55, 95%=26.49).

- **Deflated Sharpe Ratio**: 0.450 (Sharpe na transakcję 0.366, próg przy 324 próbach 0.373).

- **PBO** (CSCV, 16 bloków, 324 wariantów): 0.547 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 304 transakcji, śr. -95.76 pips, 0.36 R.

- **Bootstrap 95%** średnich pipsów: całość [131.25; 421.69], OOS [-276.71; 219.04].

- **Spread**: ×1 269.71, ×1,5 268.85, ×2 267.98 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 695.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -77.80, 1 pips: -425.31 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs walutowy, który odjechał daleko od swojej średniej z ok. 3 lat (756 dni handlu), ma tendencję wracać
w stronę tej średniej: parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale
w skali lat ciągną kurs z powrotem. Cena poniżej średniej = long, powyżej = short (lustrzanie, więc jednostronny dryf
pary nie udaje przewagi). Odchylenie mierzymy trzema sposobami (w %, w ATR14 dziennym, w odchyleniach standardowych
ceny z 756 dni), każdym na 4 progach; wchodzimy trzema sposobami (pierwszy dzień przekroczenia / co najwyżej jedna
pozycja na tydzień dopóki odchylenie trwa — piramidowanie / jak poprzednie, ale tylko w dniu, gdy cena zawraca
w stronę średniej). Bez stop lossa: pozycję zamyka powrót do średniej, TP w ATR albo upływ czasu (20–480 dni).
Hipoteza zapisana PRZED liczeniem."""

# Rodzaj odchylenia × próg (indeks 0–3 w THR) × sposób wejścia = 3 × 4 × 3 = 36 wariantów wejścia.
PARAMS = {"dev": ["pct", "atr", "z"], "level": [0, 1, 2, 3], "entry": ["cross", "weekly", "turn"]}
THR = {"pct": (5.0, 8.0, 12.0, 16.0),      # % odległości ceny od SMA756
       "atr": (6.0, 10.0, 14.0, 18.0),     # odległość w ATR14 dziennych
       "z": (1.0, 1.5, 2.0, 2.5)}          # odchylenia standardowe ceny z 756 dni
MEAN_DAYS = 756                             # ok. 3 lata handlu (3 × 252)
GAP_DAYS = 5                                # „weekly”/„turn”: najwyżej jedno wejście na 5 dni handlu

# Piramidowanie: do 10 pozycji naraz w parze, jeden kierunek (D-034); mały depozyt na pozycję, bo nie ma stop lossa.
PYRAMID = 10
SIZING = [1, 2, 5]

# Wyjścia BEZ stop lossa (B7: każde ma limit czasu): czas, TP w ATR14 (sl = 0), powrót do średniej (levels).
EXITS = (
    [{"kind": "time", "n": n, "cap": n} for n in (20, 60, 120, 240, 480)]
    + [{"kind": "atr", "n": 14, "tp": tp, "sl": 0.0, "cap": 480} for tp in (4.0, 8.0, 16.0)]
    + [{"kind": "level", "cap": 480}]
)


def deviation(df, kind, ind):
    """Znak: ujemne = cena poniżej średniej z 756 dni. Tylko zamknięte świece (rolling, bez przyszłości)."""
    sma = ind.sma(df.close, MEAN_DAYS)
    if kind == "pct":
        return (df.close / sma - 1.0) * 100.0
    if kind == "atr":
        return (df.close - sma) / ind.atr(df, 14)
    return (df.close - sma) / df.close.rolling(MEAN_DAYS).std()


def levels(df, p, ind):
    """Cel = powrót do średniej z 756 dni, policzonej na świecy sygnału (long: powyżej ceny, short: poniżej). Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    thr = THR[p["dev"]][p["level"]]
    x = deviation(df, p["dev"], ind).to_numpy()
    c = df.close.to_numpy()
    n = len(x)
    ok = np.isfinite(x)
    below = ok & (x <= -thr)          # long
    above = ok & (x >= thr)           # short
    out = np.zeros(n)
    if p["entry"] == "cross":         # zdarzenie: pierwszy dzień po wyjściu odchylenia za próg
        out[1:] = np.where(below[1:] & ~below[:-1], 1.0, 0.0) - np.where(above[1:] & ~above[:-1], 1.0, 0.0)
        return out
    last = -10**9                     # „weekly” / „turn”: stan, ale najwyżej jedno wejście na GAP_DAYS dni (tylko z przeszłości)
    for t in range(1, n):
        if t - last < GAP_DAYS:
            continue
        if below[t] and (p["entry"] == "weekly" or c[t] > c[t - 1]):
            out[t], last = 1.0, t
        elif above[t] and (p["entry"] == "weekly" or c[t] < c[t - 1]):
            out[t], last = -1.0, t
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
