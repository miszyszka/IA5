# Raport strategii: D2

Run `20261111-102532` · silnik 0.11.0 · kod `05aa6c791f07a957` · dane `3197cf8521901cb3`

## Werdykt: 🟢 ZIELONY — wszystkie testy zaliczone

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 108.63 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✔ | 1.00 |
| dodatni przy spreadzie ×1,5 | ✔ | 274.93 |

## Hipoteza

Kurs, który odjechał o co najmniej 5% od swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Cena ≥ 5% poniżej średniej = long, ≥ 5% powyżej = short (lustrzanie). Jedno wejście na tydzień (co najmniej
5 dni handlu od poprzedniego w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop
lossa. Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Dokładanie (D-034): do 10 pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag.

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 1%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 826 (limit otwartych pozycji w parze), 332.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, max 480 | — | 127 | 6.38 | 633.71 | 91.3 | 272 | 1.26 | 108.63 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, max 480 (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 78 | 350.0 | 27 303.5 | 85.9 |
| EURGBP | 20 | 74.0 | 1 479.1 | 50.0 |
| EURJPY | 58 | -273.9 | -15 887.6 | 65.5 |
| EURUSD | 48 | 679.0 | 32 593.7 | 93.8 |
| GBPUSD | 62 | 729.4 | 45 225.8 | 100.0 |
| USDCAD | 53 | 657.8 | 34 863.0 | 86.8 |
| USDCHF | 43 | 301.0 | 12 942.9 | 76.7 |
| USDJPY | 37 | -770.1 | -28 492.2 | 51.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2017 | 57 | 904.3 | 51 545.7 | 100.0 |
| 2018 | 50 | 433.1 | 21 652.6 | 80.0 |
| 2019 | 20 | 651.9 | 13 037.0 | 100.0 |
| 2020 | 53 | 644.9 | 34 177.4 | 98.1 |
| 2021 | 26 | 593.6 | 15 434.7 | 100.0 |
| 2022 | 62 | 664.3 | 41 187.5 | 100.0 |
| 2023 | 27 | -594.3 | -16 045.4 | 66.7 |
| 2024 | 42 | -514.2 | -21 598.1 | 57.1 |
| 2025 | 43 | -294.6 | -12 669.7 | 32.6 |
| 2026 | 19 | -878.6 | -16 693.6 | 36.8 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 127 | 633.7 | 80 481.1 | 91.3 |
| OOS | 272 | 108.6 | 29 547.0 | 75.0 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 13 385 | 33.9 | 3.0 | -97.0 | -204.0 | 0.22 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 275.76 pips/transakcję, percentyl **100.0** (losowe: 5%=-83.82, mediana=14.90, 95%=121.02).

- **Deflated Sharpe Ratio**: 1.000 (Sharpe na transakcję 1.596, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 239 transakcji, śr. 19.52 pips, 0.39 R.

- **Bootstrap 95%** średnich pipsów: całość [175.63; 369.16], OOS [-28.37; 238.12].

- **Spread**: ×1 275.76, ×1,5 274.93, ×2 274.10 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 359.0 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: 96.24, 1 pips: -83.28 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który odjechał o co najmniej 5% od swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Cena ≥ 5% poniżej średniej = long, ≥ 5% powyżej = short (lustrzanie). Jedno wejście na tydzień (co najmniej
5 dni handlu od poprzedniego w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop
lossa. Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant: żadnych parametrów, jedno wyjście.
START = "2016-11-11"      # ostatnie 10 lat (stała data — sygnały wcześniejsze są wyzerowane)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)

PYRAMID = 10              # maksimum silnika: do 10 pozycji naraz w parze (w jednym kierunku)
SIZING = [1]              # zawsze 1% kapitału jako depozyt
EXITS = [{"kind": "level", "cap": 480}]   # TP = średnia (levels), bez SL; cap 480 dni to wymagany przez silnik limit czasu (B7)


def levels(df, p, ind):
    """Zamknięcie na przecięciu średniej: cel = średnia z 756 dni policzona na świecy sygnału. Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    dev = (df.close / sma - 1.0).to_numpy()
    live = (df.index >= pd.Timestamp(START, tz="UTC")) & np.isfinite(dev)
    below = live & (dev <= -BAND)     # long
    above = live & (dev >= BAND)      # short
    out = np.zeros(len(dev))
    last = -10**9                     # tylko z przeszłości: najwyżej jedno wejście na GAP_DAYS dni
    for t in range(len(dev)):
        if t - last < GAP_DAYS:
            continue
        if below[t]:
            out[t], last = 1.0, t
        elif above[t]:
            out[t], last = -1.0, t
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
