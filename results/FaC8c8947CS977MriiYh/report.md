# Raport strategii: simple

Run `20261103-125900` · silnik 0.8.0 · kod `3caee1102d98b8d9` · dane `31b6742d29a9c1d9`

## Werdykt: 🟡 ŻÓŁTY — za mało transakcji OOS do oceny

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✔ | 0.85 |
| percentyl benchmarku ≥ 95 | ✔ | 100.00 |
| PBO < 0,3 | ✘ | 0.55 |
| DSR ≥ 0,95 | ✘ | 0.35 |
| dodatni przy spreadzie ×1,5 | ✔ | 3.85 |

## Hipoteza

Po gwałtownym spadku EUR/USD w 10 świecach rynek jest wyprzedany: sprzedający kończą, a pierwsza zielona
świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 932** (4 wejścia × 233 wyjść).

- Pominięte sygnały, średnio na wariant: 3 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 201 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.1 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 1× SL 0.5× max 24 | drop_pips=50 | 57 | 0.37 | 4.78 | 49.1 | 8 | -0.01 | 0.85 |
| 2 | ATR14 TP 1× SL 0.5× max 72 | drop_pips=50 | 57 | 0.37 | 4.78 | 49.1 | 8 | -0.01 | 0.85 |
| 3 | ATR14 TP 1× SL 0.5× max 120 | drop_pips=50 | 57 | 0.37 | 4.78 | 49.1 | 8 | -0.01 | 0.85 |
| 4 | ATR14 TP 0.75× SL 0.5× max 24 | drop_pips=50 | 57 | 0.26 | 3.30 | 54.4 | 8 | 0.12 | 0.84 |
| 5 | ATR14 TP 0.75× SL 0.5× max 72 | drop_pips=50 | 57 | 0.26 | 3.30 | 54.4 | 8 | 0.12 | 0.84 |
| 6 | ATR14 TP 0.75× SL 0.5× max 120 | drop_pips=50 | 57 | 0.26 | 3.30 | 54.4 | 8 | 0.12 | 0.84 |
| 7 | ATR14 TP 1.5× SL 0.5× max 24 | drop_pips=50 | 57 | 0.23 | 3.18 | 33.3 | 8 | -1.13 | -7.93 |
| 8 | ATR14 TP 1.5× SL 0.5× max 72 | drop_pips=50 | 57 | 0.23 | 3.18 | 33.3 | 8 | -1.13 | -7.93 |
| 9 | ATR14 TP 1.5× SL 0.5× max 120 | drop_pips=50 | 57 | 0.23 | 3.18 | 33.3 | 8 | -1.13 | -7.93 |
| 10 | ATR5 TP 0.75× SL 0.5× max 24 | drop_pips=50 | 57 | 0.22 | 2.78 | 52.6 | 8 | 0.14 | 0.90 |

## Najlepszy wariant IS: ATR14 TP 1× SL 0.5× max 24 (drop_pips=50)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| EURUSD | 65 | 4.3 | 279.2 | 47.7 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 7 | 4.4 | 30.5 | 42.9 |
| 2025 | 37 | 3.3 | 120.4 | 43.2 |
| 2026 | 21 | 6.1 | 128.3 | 57.1 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 57 | 4.8 | 272.4 | 49.1 |
| OOS | 8 | 0.8 | 6.8 | 37.5 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 10 377 | 3.8 | 1.9 | -0.9 | 1.26 | 0 |
| 10.0% | 10 765 | 7.7 | 3.9 | -1.7 | 1.26 | 0 |
| 15.0% | 11 165 | 11.7 | 5.8 | -2.6 | 1.26 | 0 |
| 20.0% | 11 577 | 15.8 | 7.8 | -3.4 | 1.25 | 0 |
| 30.0% | 12 436 | 24.4 | 11.8 | -5.1 | 1.25 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik 4.30 pips/transakcję, percentyl **100.0** (losowe: 5%=-2.59, mediana=-0.87, 95%=1.07).

- **Deflated Sharpe Ratio**: 0.348 (Sharpe na transakcję 0.243, próg przy 230 próbach 0.295).

- **PBO** (CSCV, 16 bloków, 232 wariantów): 0.550 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 27 transakcji, śr. -10.12 pips, -0.38 R.

- **Bootstrap 95%** średnich pipsów: całość [0.78; 7.90], OOS [-5.53; 9.11].

- **Spread**: ×1 4.30, ×1,5 3.85, ×2 3.40 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 4.62% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Po gwałtownym spadku EUR/USD w 10 świecach rynek jest wyprzedany: sprzedający kończą, a pierwsza zielona
świeca pokazuje powrót kupujących. Oczekujemy krótkiego odbicia na long."""

PARAMS = {
    "drop_pips": [50, 80, 100, 150],   # spadek zamknięć z 10 świec przed zieloną świecą
}


def signals(df, p, ind):
    if df.attrs.get("pair") != "EURUSD":
        return (df.close * 0).astype("int8")      # tylko EUR/USD
    pip = 0.0001
    drop = df.close.shift(1) - df.close.shift(11)  # 10 świec zakończonych tuż przed bieżącą
    green = df.close > df.open
    first_green = green & ~green.shift(1, fill_value=False)
    return (first_green & (drop <= -p["drop_pips"] * pip)).astype("int8")   # +1 = long

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
