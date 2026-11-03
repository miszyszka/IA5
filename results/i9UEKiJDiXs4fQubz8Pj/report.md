# Raport strategii: Simple v2

Run `20261103-131909` · silnik 0.8.0 · kod `2f1b6d5ecad47623` · dane `2e94d23547d8dd53`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -57.82 |
| percentyl benchmarku ≥ 95 | ✘ | 88.70 |
| PBO < 0,3 | ✘ | 0.56 |
| DSR ≥ 0,95 | ✘ | 0.21 |
| dodatni przy spreadzie ×1,5 | ✔ | 22.17 |

## Hipoteza

Wersja 2 strategii „simple” (wersja 1: tylko EUR/USD, spadek 50–150 pipsów z 10 świec, 8 transakcji OOS).
Po gwałtownym spadku rynek jest wyprzedany: sprzedający kończą, a zielona świeca pokazuje powrót kupujących —
oczekujemy krótkiego odbicia na long. To samo dotyczy każdej pary, więc spadek mierzymy w jednostkach zmienności
pary (ATR14 · √N), a nie w pipsach: 50 pipsów na EUR/USD to coś innego niż 50 pipsów na EUR/GBP czy USD/JPY.
Sprawdzamy: krótsze i dłuższe okno spadku, mniejszy i większy spadek, wejście po pierwszej albo po drugiej zielonej.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 2796** (12 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 26 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 4921 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 1.7 (przerwa w dostępie do danych), 0.3 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | po 120 świecach | okno=10, spadek=1.7, zielona=1 | 37 | 2.65 | 49.11 | 64.9 | 12 | -4.25 | -57.82 |
| 2 | po 96 świecach | okno=10, spadek=1.7, zielona=1 | 38 | 2.39 | 42.40 | 65.8 | 12 | -3.83 | -56.39 |
| 3 | po 72 świecach | okno=20, spadek=1.7, zielona=1 | 30 | 2.29 | 29.11 | 56.7 | 14 | -0.90 | -1.68 |
| 4 | po 96 świecach | okno=20, spadek=1.7, zielona=1 | 30 | 2.21 | 29.82 | 53.3 | 14 | -0.86 | -3.94 |
| 5 | po 120 świecach | okno=10, spadek=1.35, zielona=2 | 59 | 1.99 | 34.17 | 64.4 | 23 | -4.28 | -47.05 |
| 6 | po 120 świecach | okno=20, spadek=1.35, zielona=1 | 94 | 1.91 | 31.41 | 58.5 | 36 | -0.45 | -7.17 |
| 7 | po 48 świecach | okno=10, spadek=1.7, zielona=2 | 31 | 1.80 | 40.33 | 74.2 | 10 | -2.30 | -30.04 |
| 8 | po 36 świecach | okno=10, spadek=1.7, zielona=2 | 31 | 1.66 | 37.52 | 71.0 | 10 | -2.57 | -45.50 |
| 9 | po 72 świecach | okno=10, spadek=1.7, zielona=2 | 31 | 1.53 | 35.09 | 67.7 | 10 | -4.69 | -72.33 |
| 10 | po 48 świecach | okno=20, spadek=1.7, zielona=1 | 30 | 1.40 | 16.79 | 63.3 | 14 | -0.62 | 0.35 |

## Najlepszy wariant IS: po 120 świecach (okno=10, spadek=1.7, zielona=1)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 7 | 18.1 | 126.8 | 57.1 |
| EURGBP | 1 | -7.7 | -7.7 | 0.0 |
| EURJPY | 5 | 9.3 | 46.7 | 60.0 |
| EURUSD | 10 | 13.3 | 132.9 | 50.0 |
| GBPUSD | 11 | 20.5 | 225.9 | 54.5 |
| USDCHF | 8 | 23.1 | 184.8 | 50.0 |
| USDJPY | 7 | 59.1 | 413.9 | 71.4 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 3 | -56.3 | -168.9 | 33.3 |
| 2025 | 25 | 76.6 | 1 914.3 | 72.0 |
| 2026 | 21 | -29.6 | -622.0 | 38.1 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 37 | 49.1 | 1 817.2 | 64.9 |
| OOS | 12 | -57.8 | -693.8 | 25.0 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 11 520 | 15.2 | 7.4 | -11.1 | 0.57 | 0 |
| 10.0% | 12 940 | 29.4 | 13.9 | -21.7 | 0.57 | 0 |
| 15.0% | 14 183 | 41.8 | 19.3 | -31.7 | 0.57 | 0 |
| 20.0% | 15 179 | 51.8 | 23.5 | -41.0 | 0.57 | 0 |
| 30.0% | 17 159 | 71.6 | 31.4 | -54.9 | 0.60 | 1 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 22.93 pips/transakcję, percentyl **88.7** (losowe: 5%=-31.88, mediana=1.61, 95%=32.54).

- **Deflated Sharpe Ratio**: 0.209 (Sharpe na transakcję 0.320, próg przy 2560 próbach 0.458).

- **PBO** (CSCV, 16 bloków, 2796 wariantów): 0.564 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 41 transakcji, śr. -13.35 pips, -1.53 R.

- **Bootstrap 95%** średnich pipsów: całość [-23.04; 73.00], OOS [-183.01; 27.12].

- **Spread**: ×1 22.93, ×1,5 22.17, ×2 21.40 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 0.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Wersja 2 strategii „simple” (wersja 1: tylko EUR/USD, spadek 50–150 pipsów z 10 świec, 8 transakcji OOS).
Po gwałtownym spadku rynek jest wyprzedany: sprzedający kończą, a zielona świeca pokazuje powrót kupujących —
oczekujemy krótkiego odbicia na long. To samo dotyczy każdej pary, więc spadek mierzymy w jednostkach zmienności
pary (ATR14 · √N), a nie w pipsach: 50 pipsów na EUR/USD to coś innego niż 50 pipsów na EUR/GBP czy USD/JPY.
Sprawdzamy: krótsze i dłuższe okno spadku, mniejszy i większy spadek, wejście po pierwszej albo po drugiej zielonej."""

PARAMS = {
    "okno": [10, 20],           # ile świec obejmuje spadek przed zieloną świecą
    "spadek": [1.0, 1.35, 1.7],  # spadek ≥ tyle × ATR14 · √okno (EUR/USD, okno 10: ok. 37 / 50 / 63 pipsy)
    "zielona": [1, 2],          # wejście po pierwszej zielonej albo po drugiej zielonej z rzędu
}


def signals(df, p, ind):
    n, k, g = p["okno"], p["spadek"], p["zielona"]
    green = df.close > df.open
    if g == 1:
        trigger = green & ~green.shift(1, fill_value=False)                      # pierwsza zielona po czerwonej
    else:
        trigger = green & green.shift(1, fill_value=False) & ~green.shift(2, fill_value=False)   # druga zielona z rzędu
    ref = g                                     # ostatnia świeca przed pierwszą zieloną
    drop = df.close.shift(ref) - df.close.shift(ref + n)
    atr = ind.atr(df, 14).shift(ref)
    deep = drop <= -k * atr * (n ** 0.5)
    return (trigger & deep).astype("int8")      # +1 = long, wszystkie pary

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
