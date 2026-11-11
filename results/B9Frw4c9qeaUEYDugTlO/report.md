# Raport strategii: D5

Run `20261111-214455` · silnik 0.13.0 · kod `d5b214d5d34d7b4f` · dane `3197cf8521901cb3`

## Werdykt: 🟡 ŻÓŁTY — żaden wariant nie ma 30 transakcji IS

## Hipoteza

Kurs, który spadł o 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę: parytet siły
nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs z powrotem.
Tylko long, BEZ DŹWIGNI: jedna pozycja naraz w całym portfelu (wszystkie 8 par), wartość pozycji = cały kapitał (1× kapitał,
nie 30×). Wejście w dniu, w którym cena po raz pierwszy spada o 5% poniżej średniej (zdarzenie, nie stan); sygnały w czasie,
gdy pozycja jest otwarta, przepadają. Wyjście tylko wtedy, gdy cena dobije do poziomu średniej z dnia otwarcia transakcji
(stała cena celu, nie ruchoma średnia); bez stop lossa i bez limitu czasu. Cała dostępna historia D1 (średnia 3-letnia
potrzebuje ok. 3 lat rozgrzewki). Hipoteza zapisana PRZED liczeniem.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece D1 od 1996-10-30 do 2026-11-10; źródło: yahoo.

- In-sample do 2019-05-09, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece D1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5) — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy..

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 148, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURGBP: odrzucone 69, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); EURJPY: odrzucone 235, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (17 h); EURUSD: odrzucone 130, uzupełnione 0 (luki ≤ 3 h), 3 przerw w danych (20 h); GBPUSD: odrzucone 105, uzupełnione 0 (luki ≤ 3 h), 1 przerw w danych (3 h); USDCAD: odrzucone 117, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDCHF: odrzucone 104, uzupełnione 0 (luki ≤ 3 h), 0 przerw w danych (0 h); USDJPY: odrzucone 278, uzupełnione 0 (luki ≤ 3 h), 6 przerw w danych (29 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 3.33333%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 1** (1 wejścia × 1 wyjść).

- Pominięte sygnały, średnio na wariant: 78 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 0 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 14.0 (przerwa w dostępie do danych), 0.0 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

_Żaden wariant nie ma 30 transakcji w IS._

## Znane ograniczenia

- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy D1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

- **Pozycje otwarte (D-061, wyjście bez limitu czasu):** 1 z 9 transakcji (11.1%) nie zamknęło się do końca danych — liczone po ostatnim close jako wynik niezrealizowany; średnio -2 438.51 pips netto na pozycję. Wynik realny zależy od tego, czy cena jeszcze wróci do poziomu; nie ma stopu, więc przegrywająca pozycja trwa.

## Kod strategii

```python

TIMEFRAME = "D1"

HYPOTHESIS = """Kurs, który spadł o 5% poniżej swojej średniej z ok. 3 lat (756 dni handlu), wraca w jej stronę: parytet siły
nabywczej, bilanse handlowe i polityka banków centralnych działają wolno, ale w skali lat ciągną kurs z powrotem.
Tylko long, BEZ DŹWIGNI: jedna pozycja naraz w całym portfelu (wszystkie 8 par), wartość pozycji = cały kapitał (1× kapitał,
nie 30×). Wejście w dniu, w którym cena po raz pierwszy spada o 5% poniżej średniej (zdarzenie, nie stan); sygnały w czasie,
gdy pozycja jest otwarta, przepadają. Wyjście tylko wtedy, gdy cena dobije do poziomu średniej z dnia otwarcia transakcji
(stała cena celu, nie ruchoma średnia); bez stop lossa i bez limitu czasu. Cała dostępna historia D1 (średnia 3-letnia
potrzebuje ok. 3 lat rozgrzewki). Hipoteza zapisana PRZED liczeniem."""

# Jeden wariant, żadnych parametrów.
MEAN_DAYS = 756           # średnia 3-letnia: 3 × 252 dni handlu
BAND = 0.05               # wejście, gdy cena jest 5% poniżej średniej

# BEZ DŹWIGNI: silnik liczy nominał = 30 × depozyt, więc depozyt 100/30 % kapitału daje nominał = 100% kapitału (1×).
# Jedna pozycja naraz w całym portfelu (MAX_PAIRS = 1, bez PYRAMID) — inaczej kilka pozycji naraz byłoby dźwignią.
SIZING = [100 / 30]
MAX_PAIRS = 1
PAIR_RANK = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "AUDUSD", "USDCHF", "USDCAD", "EURJPY"]   # tylko przy sygnałach tego samego dnia: kolejność z tabeli spreadów (bez wyników)
EXITS = [{"kind": "level", "cap": 0}]     # TP = średnia z dnia sygnału (levels), bez SL i BEZ limitu czasu (D-061)


def levels(df, p, ind):
    """Cel = średnia z 756 dni policzona na świecy sygnału (cena z momentu otwarcia transakcji, nie ruchoma). Bez SL."""
    return pd.DataFrame({"tp": ind.sma(df.close, MEAN_DAYS)}, index=df.index)


def signals(df, p, ind):
    sma = ind.sma(df.close, MEAN_DAYS)
    below = ((df.close / sma - 1.0) <= -BAND).to_numpy()          # NaN w rozgrzewce → False
    out = np.zeros(len(below))
    out[1:] = (below[1:] & ~below[:-1]).astype(float)             # zdarzenie: pierwszy dzień poniżej −5%
    return out

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
