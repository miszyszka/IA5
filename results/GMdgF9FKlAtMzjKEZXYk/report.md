# Raport strategii: Strategia 5

Run `20261031-102827` · silnik 0.8.0 · kod `9322b9d60f8d5553` · dane `fca2a7086f281a13`

## Werdykt: 🟡 ŻÓŁTY — zaliczone 2 z 5 testów

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 0.63 |
| percentyl benchmarku ≥ 95 | ✘ | 89.60 |
| PBO < 0,3 | ✔ | 0.00 |
| DSR ≥ 0,95 | ✘ | 0.00 |
| dodatni przy spreadzie ×1,5 | ✘ | -1.48 |

## Hipoteza

Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na Dukascopy 2003–2026 — innym źródle i dłuższym okresie.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-10-30; źródło: yahoo.

- In-sample do 2026-04-30, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 33, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 30, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 18** (3 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 24 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.3 (przerwa w dostępie do danych), 4.4 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 50× SL 2× max 8 | start=7 | 3 104 | -0.04 | -1.09 | 43.7 | 1 024 | -0.02 | 0.63 |
| 2 | ATR14 TP 50× SL 2× max 6 | start=8 | 3 094 | -0.05 | -1.17 | 44.6 | 1 024 | -0.06 | -0.73 |
| 3 | ATR14 TP 50× SL 2× max 8 | start=6 | 3 104 | -0.05 | -1.44 | 43.1 | 1 024 | -0.02 | 0.24 |
| 4 | ATR14 TP 50× SL 2× max 6 | start=7 | 3 104 | -0.06 | -1.57 | 44.0 | 1 024 | -0.07 | -1.06 |
| 5 | ATR14 TP 50× SL 2× max 8 | start=8 | 3 094 | -0.06 | -1.51 | 42.1 | 1 022 | -0.06 | -0.84 |
| 6 | ATR14 TP 50× SL 2× max 4 | start=8 | 3 094 | -0.07 | -1.83 | 43.7 | 1 024 | -0.08 | -1.39 |
| 7 | ATR14 TP 50× SL 2× max 6 | start=6 | 3 104 | -0.08 | -2.27 | 43.1 | 1 024 | -0.06 | -0.72 |
| 8 | ATR14 TP 50× SL 2× max 4 | start=6 | 3 095 | -0.08 | -2.46 | 44.0 | 1 024 | -0.06 | -0.68 |
| 9 | ATR14 TP 50× SL 2× max 4 | start=7 | 3 103 | -0.09 | -2.52 | 43.1 | 1 024 | -0.07 | -1.30 |
| 10 | po 6 świecach | start=8 | 3 094 | -0.13 | -1.59 | 46.3 | 1 024 | -0.14 | -1.07 |

## Najlepszy wariant IS: ATR14 TP 50× SL 2× max 8 (start=7)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 516 | -1.3 | -684.4 | 43.8 |
| EURGBP | 516 | -1.2 | -640.0 | 44.6 |
| EURJPY | 516 | -0.3 | -153.2 | 41.3 |
| EURUSD | 516 | -0.2 | -111.3 | 44.2 |
| GBPUSD | 516 | -1.6 | -843.8 | 40.1 |
| USDCAD | 516 | -1.5 | -784.7 | 45.0 |
| USDCHF | 516 | -0.7 | -358.9 | 43.8 |
| USDJPY | 516 | 1.7 | 853.0 | 45.3 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 360 | -1.9 | -673.7 | 45.0 |
| 2025 | 2072 | -1.4 | -2 967.6 | 42.7 |
| 2026 | 1696 | 0.5 | 918.1 | 44.2 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 3104 | -1.1 | -3 368.0 | 43.7 |
| OOS | 1024 | 0.6 | 644.8 | 43.1 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 5 842 | -41.6 | -23.5 | -51.9 | -0.98 | 0 |
| 10.0% | 3 141 | -68.6 | -43.9 | -78.4 | -0.98 | 0 |
| 15.0% | 1 686 | -83.1 | -58.9 | -87.8 | -1.10 | 1032 |
| 20.0% | 1 020 | -89.8 | -68.0 | -93.8 | -0.82 | 1548 |
| 30.0% | 1 011 | -89.9 | -68.2 | -93.8 | -0.95 | 2580 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -0.66 pips/transakcję, percentyl **89.6** (losowe: 5%=-2.17, mediana=-1.33, 95%=-0.45).

- **Deflated Sharpe Ratio**: 0.000 (Sharpe na transakcję -0.040, próg przy 18 próbach 0.045).

- **PBO** (CSCV, 16 bloków, 18 wariantów): 0.002 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 2464 transakcji, śr. -0.92 pips, -0.06 R.

- **Bootstrap 95%** średnich pipsów: całość [-1.68; 0.44], OOS [-1.31; 2.51].

- **Spread**: ×1 -0.66, ×1,5 -1.48, ×2 -2.31 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Sezonowość w ciągu doby: waluta słabnie w godzinach pracy własnego rynku (Breedon i Ranaldo, 2013 —
„Intraday patterns in FX returns and order flow”). Europejskie firmy i fundusze sprzedają euro rano, gdy otwiera
się Londyn i Frankfurt, a po południu przejmuje Nowy Jork. Stąd short EUR/USD od otwarcia Londynu na kilka godzin.
Efekt znaleziony na niezależnych danych brokera MT 2012–2022 (8 par): tylko EUR/USD przebija spread, w obu
połowach próby i w 10 z 11 lat; tu sprawdzamy go na Dukascopy 2003–2026 — innym źródle i dłuższym okresie."""

PARAMS = {
    "start": [6, 7, 8],      # godzina wejścia w czasie Londynu (z czasem letnim); 7:00 = otwarcie Londynu
}

# Wyjście po 4, 6 albo 8 godzinach; każde także z awaryjnym stopem 2×ATR14 (TP tak daleko, że w praktyce go nie ma)
EXITS = (
    [{"kind": "time", "n": n, "cap": n} for n in (4, 6, 8)]
    + [{"kind": "atr", "n": 14, "tp": 50.0, "sl": 2.0, "cap": n} for n in (4, 6, 8)]
)


def signals(df, p, ind):
    london = df.index.tz_convert("Europe/London")
    weekday = london.dayofweek < 5
    # sygnał na zamknięciu świecy start−1 → wejście na open świecy o godzinie start (czas Londynu)
    sig = weekday & (london.hour == p["start"] - 1)
    return -sig.astype("int8")              # short EUR/USD

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
