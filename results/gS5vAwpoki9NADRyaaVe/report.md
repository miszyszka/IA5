# Raport strategii: D3

Run `20261111-111117` · silnik 0.13.0 · kod `54e7fe2453c4f39c` · dane `3197cf8521901cb3`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -3.28 |
| percentyl benchmarku ≥ 95 | ✔ | 99.10 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✔ | 1.00 |
| dodatni przy spreadzie ×1,5 | ✔ | 279.36 |

## Hipoteza

Kurs, który odjechał o co najmniej 5% od swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Cena ≥ 5% poniżej średniej = long, ≥ 5% powyżej = short (lustrzanie). Jedno wejście na tydzień (co najmniej
5 dni handlu od poprzedniego w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop
lossa i bez limitu czasu. Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
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

- Pominięte sygnały, średnio na wariant: 1,237 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 3.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | poziomy TP/SL ze strategii, bez limitu czasu | — | 121 | 7.43 | 739.36 | 100.0 | 196 | 0.25 | -3.28 |

## Najlepszy wariant IS: poziomy TP/SL ze strategii, bez limitu czasu (—)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 78 | 458.8 | 35 782.6 | 100.0 |
| EURGBP | 10 | 176.1 | 1 760.5 | 100.0 |
| EURJPY | 48 | -195.4 | -9 378.8 | 79.2 |
| EURUSD | 58 | 721.7 | 41 860.2 | 100.0 |
| GBPUSD | 10 | 1 006.9 | 10 069.1 | 100.0 |
| USDCAD | 43 | 609.8 | 26 219.4 | 76.7 |
| USDCHF | 43 | 338.0 | 14 535.0 | 76.7 |
| USDJPY | 27 | -1 186.2 | -32 028.0 | 63.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2017 | 57 | 904.3 | 51 545.7 | 100.0 |
| 2018 | 30 | 654.4 | 19 632.5 | 100.0 |
| 2019 | 4 | 590.2 | 2 360.7 | 100.0 |
| 2020 | 40 | 693.4 | 27 737.6 | 100.0 |
| 2021 | 26 | 593.6 | 15 434.7 | 100.0 |
| 2022 | 50 | 641.4 | 32 067.6 | 100.0 |
| 2023 | 10 | 577.1 | 5 771.3 | 100.0 |
| 2025 | 10 | 839.3 | 8 393.3 | 100.0 |
| 2026 | 90 | -823.6 | -74 123.4 | 55.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 121 | 739.4 | 89 462.3 | 100.0 |
| OOS | 196 | -3.3 | -642.3 | 79.6 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | obsunięcie z otwartymi (MAE) % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|---|
| 1.0% | 79 544 | 695.4 | 23.1 | -87.8 | -246.0 | 0.79 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 280.19 pips/transakcję, percentyl **99.1** (losowe: 5%=-134.22, mediana=30.54, 95%=199.32).

- **Deflated Sharpe Ratio**: 1.000 (Sharpe na transakcję 2.649, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 160 transakcji, śr. -177.12 pips, -1.38 R.

- **Bootstrap 95%** średnich pipsów: całość [136.79; 404.62], OOS [-214.78; 195.82].

- **Spread**: ×1 280.19, ×1,5 279.36, ×2 278.54 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

- **Noce (swap pominięty, O5)**: średnio 679.4 nocy na transakcję, 100% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy 0,5 pipsa: -59.49, 1 pips: -399.18 pips/transakcję.

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

- **Pozycje otwarte (D-061, wyjście bez limitu czasu):** 80 z 317 transakcji (25.2%) nie zamknęło się do końca danych — liczone po ostatnim close jako wynik niezrealizowany; średnio -981.72 pips netto na pozycję. Wynik realny zależy od tego, czy cena jeszcze wróci do poziomu; nie ma stopu, więc przegrywająca pozycja trwa.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który odjechał o co najmniej 5% od swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę:
parytet siły nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs
z powrotem. Cena ≥ 5% poniżej średniej = long, ≥ 5% powyżej = short (lustrzanie). Jedno wejście na tydzień (co najmniej
5 dni handlu od poprzedniego w tej parze), zawsze ta sama wielkość. Zamknięcie tylko na powrocie do średniej, bez stop
lossa i bez limitu czasu. Liczone tylko od 2016-11-11 (ostatnie 10 lat); średnia 3-letnia korzysta z wcześniejszych danych.
Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant: żadnych parametrów, jedno wyjście.
START = "2016-11-11"      # ostatnie 10 lat (stała data — sygnały wcześniejsze są wyzerowane)
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # 5% od średniej
GAP_DAYS = 5              # jedno wejście na tydzień (5 dni handlu od poprzedniego)

PYRAMID = 10              # maksimum silnika: do 10 pozycji naraz w parze (w jednym kierunku)
SIZING = [1]              # zawsze 1% kapitału jako depozyt
EXITS = [{"kind": "level", "cap": 0}]     # TP = średnia (levels), bez SL i BEZ limitu czasu (D-061): zamknięcie tylko na średniej


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
