# Raport strategii: simple

Run `20261103-132539` · silnik 0.8.0 · kod `4dff14a227d9c3f4` · dane `2e94d23547d8dd53`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -1.90 |
| percentyl benchmarku ≥ 95 | ✘ | 93.80 |
| PBO < 0,3 | nie dotyczy | — |
| DSR ≥ 0,95 | ✘ | 0.08 |
| dodatni przy spreadzie ×1,5 | ✘ | -1.95 |

## Hipoteza

„simple” na wszystkich 8 parach (wersja 1: tylko EUR/USD, najlepszy wariant IS: spadek 50 pipsów,
wyjście TP 1 × ATR14, SL 0,5 × ATR14, max 24 świece). Po gwałtownym spadku z 10 świec rynek jest wyprzedany:
sprzedający kończą, a pierwsza zielona świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long.
Ta sama reguła i to samo wyjście, bez zmian — tylko więcej par. Spadek w pipsach danej pary (JPY: 0,01).

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 23 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 4 wejść w rozgrzewce ATR, 1252 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 1.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1× SL 0.5× max 24 | drop_pips=50 | 680 | -0.08 | -0.98 | 35.4 | 117 | -0.10 | -1.90 |

## Najlepszy wariant IS: ATR14 TP 1× SL 0.5× max 24 (drop_pips=50)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 36 | 0.0 | 1.1 | 38.9 |
| EURJPY | 246 | -0.9 | -229.0 | 36.2 |
| EURUSD | 65 | 4.3 | 279.2 | 47.7 |
| GBPUSD | 110 | 1.5 | 163.3 | 43.6 |
| USDCAD | 41 | -6.4 | -263.8 | 22.0 |
| USDCHF | 50 | -1.1 | -53.2 | 36.0 |
| USDJPY | 249 | -3.2 | -784.6 | 29.7 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 82 | -2.7 | -223.5 | 30.5 |
| 2025 | 487 | -1.2 | -574.2 | 34.5 |
| 2026 | 228 | -0.4 | -89.4 | 39.5 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 680 | -1.0 | -664.8 | 35.4 |
| OOS | 117 | -1.9 | -222.2 | 35.9 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 9 205 | -8.0 | -4.0 | -10.5 | -0.68 | 0 |
| 10.0% | 8 431 | -15.7 | -8.2 | -20.2 | -0.68 | 0 |
| 15.0% | 7 685 | -23.2 | -12.3 | -29.0 | -0.68 | 0 |
| 20.0% | 6 970 | -30.3 | -16.5 | -37.1 | -0.68 | 0 |
| 30.0% | 5 380 | -46.2 | -26.6 | -53.2 | -0.78 | 6 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -1.11 pips/transakcję, percentyl **93.8** (losowe: 5%=-2.90, mediana=-2.01, 95%=-1.05).

- **Deflated Sharpe Ratio**: 0.085 (Sharpe na transakcję -0.054, próg przy 1 próbach 0.000).

- **PBO** (CSCV, — bloków, 1 wariantów): — — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 330 transakcji, śr. -0.17 pips, 0.02 R.

- **Bootstrap 95%** średnich pipsów: całość [-2.49; 0.27], OOS [-5.03; 1.33].

- **Spread**: ×1 -1.11, ×1,5 -1.95, ×2 -2.78 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 2.51% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """„simple” na wszystkich 8 parach (wersja 1: tylko EUR/USD, najlepszy wariant IS: spadek 50 pipsów,
wyjście TP 1 × ATR14, SL 0,5 × ATR14, max 24 świece). Po gwałtownym spadku z 10 świec rynek jest wyprzedany:
sprzedający kończą, a pierwsza zielona świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long.
Ta sama reguła i to samo wyjście, bez zmian — tylko więcej par. Spadek w pipsach danej pary (JPY: 0,01)."""

PARAMS = {"drop_pips": [50]}   # jak najlepszy wariant wersji 1

EXITS = [{"kind": "atr", "n": 14, "tp": 1.0, "sl": 0.5, "cap": 24}]   # TP 1 × ATR14, SL 0,5 × ATR14, max 24 świece


def signals(df, p, ind):
    pip = 0.01 if "JPY" in df.attrs.get("pair", "") else 0.0001
    drop = df.close.shift(1) - df.close.shift(11)  # 10 świec zakończonych tuż przed bieżącą
    green = df.close > df.open
    first_green = green & ~green.shift(1, fill_value=False)
    return (first_green & (drop <= -p["drop_pips"] * pip)).astype("int8")   # +1 = long, wszystkie pary

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
