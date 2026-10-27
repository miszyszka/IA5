# STRATEGIE — jak pisać kod strategii dla IA5

> Ten plik jest **regułą dla Claude**. Gdy Michał mówi „zrób mi strategię …”, Claude postępuje dokładnie według sekcji 1 i zwraca kod, który bez zmian wkleja się do okna „Nowa strategia” w dashboardzie i który program `ia5` na Macu zrozumie.
> Kontrakt jest egzekwowany w kodzie: `runner/ia5/sandbox.py` (wykonanie), `runner/ia5/check.py` (kontrola), `web/js/metrics.js` → `checkStrategyCode` (kontrola w przeglądarce).

---

## 1. Procedura „zrób mi strategię X” (obowiązkowa)

1. **Interpretacje.** Każde niejednoznaczne sformułowanie zamień na jedną konkretną definicję i wypisz ją krótko, np.
   - „SMA200 rośnie” → `SMA200[t] > SMA200[t−5]`;
   - „RSI spadło poniżej 30” → przecięcie w dół (zdarzenie), nie stan „RSI < 30”;
   - „wybicie szczytu z 20 świec” → zamknięcie powyżej maksimum 20 *poprzednich* świec;
   - „w sesji londyńskiej” → godziny 07–12 UTC.
   Gdy interpretacja zmienia sens strategii, a Michał jest w rozmowie — zapytaj jednym pytaniem. Gdy nie — wybierz najbardziej standardową i zaznacz to.
2. **Hipoteza.** 1–3 zdania: dlaczego to ma działać (mechanizm rynkowy), zanim ktokolwiek zobaczy wynik. Wpisz w `HYPOTHESIS`.
3. **Parametry.** Do `PARAMS` tylko to, co Michał wymienił, albo naturalne 2–3 wartości wokół standardu (np. RSI 25/30/35). Każda kombinacja to osobny wariant wejścia × 233 wyjścia — trzymaj łącznie ≤ ~3000 wariantów (≤ 12 kombinacji), bo więcej prób = ostrzejsza kara w DSR/PBO (W2).
4. **Kod** według kontraktu (sekcja 2), tylko z `ind`, `pandas`, `numpy`, `math`. Sygnał = **zdarzenie** (pierwsza świeca spełnienia warunku), nie stan. **Nie** dodawaj TP/SL/wyjść — silnik sam liczy siatkę 233 wyjść (sekcja 5). **Nie** ustawiaj spreadu, dźwigni, wielkości pozycji poza `SIZING`.
5. **Kontrola przed oddaniem.** W sesji z narzędziami (Claude Code) zapisz kod do pliku i uruchom
   `python scripts/check_strategy.py plik.py` — wynik musi być `OK`. Popraw każdy `✘`; ostrzeżenia `⚠` przemyśl i wyjaśnij. W czacie bez narzędzi napisz wprost: „nie sprawdziłem kodu automatycznie — sprawdzi go dashboard i `ia5` na Macu”.
6. **Odpowiedź** dla Michała, w tej kolejności:
   - nazwa strategii (do pola „Nazwa”);
   - lista interpretacji (punkt 1);
   - **jeden** blok ```python``` z całym kodem — gotowy do wklejenia w pole „Kod Python”;
   - liczba wariantów (`kombinacje PARAMS × 233`) i wynik kontroli;
   - 1–2 zdania, na co patrzeć w wynikach (np. „czy działa poza EUR/USD”, „czy OOS potwierdza IS”).
   Nigdy nie podawaj przewidywanych wyników liczbowych — liczy je Mac.
7. Gdy Michał wklei raport (`report.md`) — oceniaj według sekcji 9 `CLAUDE.md`: najpierw OOS, benchmark losowy, DSR, PBO, walk-forward, stabilność na heatmapie, dopiero potem średni zysk.

---

## 2. Kontrakt kodu

```python
HYPOTHESIS = """1–3 zdania: dlaczego to działa."""     # zalecane (brak = ostrzeżenie)

PARAMS = {                     # opcjonalne; każda wartość z listy = osobny wariant wejścia
    "level": [25, 30],         # iloczyn kartezjański wszystkich list
    "n": [20],
}

def signals(df, p, ind):       # WYMAGANE — dokładnie ta nazwa i te trzy argumenty
    ...
    return seria               # +1 long, -1 short, 0 nic — na indeksie df

# EXITS = [...]                # opcjonalne: własna siatka wyjść zamiast domyślnej (sekcja 5)
# SIZING = [5, 10, 20]         # opcjonalne: % kapitału jako depozyt (domyślnie 5, 10, 15, 20, 30)
# PYRAMID = 5                  # opcjonalne, tylko na życzenie: do 5 pozycji naraz w parze, jeden kierunek (D-034)
# HOURS = False                # opcjonalne, tylko na życzenie: bez okna 07–17 (albo (od, do) czasu polskiego)
```

| Element | Szczegóły |
|---|---|
| `df` | Świece H1 **jednej** pary: kolumny `open`, `high`, `low`, `close` (ceny mid z Dukascopy). Indeks `DatetimeIndex` w UTC = czas **otwarcia** świecy. Tylko zamknięte świece. Funkcja jest wołana osobno dla każdej z 8 par. |
| `p` | Słownik z jedną kombinacją `PARAMS` (np. `{"level": 25, "n": 20}`); `{}` gdy brak `PARAMS`. |
| `ind` | Biblioteka wskaźników (sekcja 3). Własnych RSI/ATR/EMA nie piszemy (B9). |
| wynik | `pd.Series` na tym samym indeksie (albo tablica tej samej długości) z wartościami `-1`, `0`, `1`; `True/False` też działa (`.astype("int8")`). `NaN` = 0. Liczba = kierunek × **waga** (0,1–10, np. `-1.6`): waga mnoży depozyt w symulacji kapitału; pipsy i R są na pozycję (D-034). |
| moment | Sygnał w świecy `t` znaczy: warunek spełniony **na zamknięciu** `t`. Wejście silnik robi na **open** `t+1` (B1). |
| godziny | Silnik wchodzi tylko wtedy, gdy świeca `t+1` zaczyna się **07:00–16:00 czasu polskiego** (B11, najniższe spready). Sygnały poza oknem są pomijane i liczone w raporcie — strategia nie musi sama filtrować godzin. Wyjście na dowolnej świecy (także po nocy i weekendzie), według wariantu wyjścia. |
| importy | Tylko `numpy`, `pandas`, `math`. Zakazane: `open`, `exec`, `eval`, `compile`, `__import__`, atrybuty `__…`. |
| czas | Limit 30 min na całe liczenie sygnałów. |

Silnik dodatkowo: pomija sygnały, gdy w danej parze jest już otwarta pozycja tego wariantu (B8), pomija wejścia w okresie rozgrzewki ATR, odrzuca strategię z look-ahead (B2).

---

## 3. Biblioteka `ind`

Wszystkie wskaźniki zgodne z TA-Lib (test `tests/test_indicators.py`), wartości w rozgrzewce = `NaN`.

| Funkcja | Zwraca |
|---|---|
| `ind.sma(x, n)`, `ind.ema(x, n)` | Series |
| `ind.rsi(x, n=14)` | Series 0–100 (Wilder) |
| `ind.atr(df, n=14)` | Series (Wilder) |
| `ind.bollinger(x, n=20, k=2.0)` | DataFrame `mid`, `upper`, `lower` |
| `ind.macd(x, fast=12, slow=26, signal=9)` | DataFrame `macd`, `signal`, `hist` — **kolumny przez nawias**: `m["hist"]` |
| `ind.stoch(df, k=14, smooth_k=3, d=3)` | DataFrame `k`, `d` |
| `ind.adx(df, n=14)` | DataFrame `adx`, `plus_di`, `minus_di` |
| `ind.donchian(df, n=20)` | DataFrame `upper`, `lower` (włącznie z bieżącą świecą) |
| `ind.highest(x, n)`, `ind.lowest(x, n)` | Series (włącznie z bieżącą świecą) |
| `ind.cross_above(a, b)`, `ind.cross_below(a, b)` | bool — świeca przecięcia; `b` może być liczbą |
| `ind.rising(x, n=1)`, `ind.falling(x, n=1)` | bool — `x[t] > x[t-n]` / `<` |
| `ind.hour(df)` | godzina otwarcia UTC 0–23 |
| `ind.weekday(df)` | 0 = poniedziałek … 6 = niedziela (UTC) |
| `ind.session(df)` | `"azja"` 0–6, `"europa"` 7–12, `"usa"` 13–20, `"poza"` 21–23 UTC |

Brakuje wskaźnika? Najpierw dopisz go do `runner/ia5/indicators.py` z testem zgodności z TA-Lib (B9), dopiero potem użyj w strategii.

---

## 4. Wzorce (przepis → kod)

```python
# Zdarzenie zamiast stanu: „RSI spada poniżej 30”
ind.cross_below(rsi, 30)                      # TAK — jedna świeca
rsi < 30                                      # NIE — sygnał w każdej świecy poniżej (stan)

# Filtr trendu
trend_up = ind.rising(ind.sma(df.close, 200), 5)
trend_up = df.close > ind.sma(df.close, 200)

# Wybicie maksimum N POPRZEDNICH świec (bez bieżącej)
ind.cross_above(df.close, ind.highest(df.high, 20).shift(1))

# „Przez 3 świece z rzędu zamknięcie powyżej SMA20”, sygnał w trzeciej
above = (df.close > ind.sma(df.close, 20)).astype(int)
ind.cross_above(above.rolling(3).sum(), 2.5)

# Pierwszy sygnał od N świec (wyciszenie powtórek)
raw = ind.cross_above(df.close, ind.sma(df.close, 50))
raw & (raw.astype(int).rolling(24).sum().shift(1) == 0)

# Godziny, dni, sesje (UTC)
(ind.hour(df) >= 7) & (ind.hour(df) < 12)
ind.weekday(df).between(1, 3)                 # wtorek–czwartek
ind.session(df) == "europa"

# Poziom dnia BEZ look-ahead: maksimum dotychczasowych świec danego dnia
day = df.index.floor("D")
day_high_so_far = df.high.groupby(day).cummax()
prev_day_high = df.high.groupby(day).max().shift(1).reindex(day).set_axis(df.index)  # wczorajsze maksimum

# Wyższy interwał (H4) BEZ look-ahead: tylko zamknięte świece H4, przeniesione na H1
h4_close = df.close.resample("4h").last().dropna()   # dropna: weekendy tworzą puste świece H4
h4_sma = ind.sma(h4_close, 50).shift(1)       # shift(1): ostatnia ZAMKNIĘTA świeca H4
h4_trend = h4_sma.reindex(df.index, method="ffill")

# Long i short naraz
(long_cond).astype("int8") - (short_cond).astype("int8")
```

---

## 5. Wyjścia (silnik, nie strategia)

Domyślnie każde wejście jest liczone z **233** wariantami wyjścia (CLAUDE.md 8.2): 14 czasowych (1–120 świec), 210 ATR (ATR5/14 × TP 0,5–4 × SL 0,5–3 × limit 24/72/120) i 9 wskaźnikowych (RSI do 50, cena przez SMA20, sygnał przeciwny × SL 1/2/3 ATR14). Dlatego **strategia podaje tylko wejścia**.

Własna siatka — tylko gdy Michał wyraźnie ją określi:

```python
EXITS = [
    {"kind": "time", "n": 24, "cap": 24},                               # po 24 świecach
    {"kind": "atr", "n": 14, "tp": 2.0, "sl": 1.0, "cap": 72},           # TP 2×ATR14, SL 1×ATR14, max 72 świece
    {"kind": "rsi50", "n": 14, "sl": 2.0, "cap": 120},                   # RSI wraca do 50, SL 2×ATR14
    {"kind": "sma", "n": 14, "sl": 2.0, "cap": 120},                     # zamknięcie po złej stronie SMA20
    {"kind": "opposite", "n": 14, "sl": 2.0, "cap": 120},                # sygnał przeciwny z signals()
    {"kind": "rsi_streak", "n": 14, "tp": 1.5, "run": 6, "level": 70, "cap": 120},
    # ↑ TP 1,5×ATR14; RSI14 6 zamknięć z rzędu > 70 (short) / < 30 (long) → wyjście na open następnej (D-034)
]
```

Każde wyjście musi mieć SL albo limit czasu (B7).

---

## 6. Pułapki look-ahead (B2) — detektor je łapie, ale lepiej ich nie pisać

| Błąd | Dlaczego zły | Poprawnie |
|---|---|---|
| `x.shift(-1)` | bierze przyszłą świecę | `x.shift(1)` |
| `df.close.mean()`, `.std()`, `.max()` całej serii | zna całą historię | `rolling(n)`, `expanding()` |
| `rolling(..., center=True)` | okno sięga w przyszłość | domyślne `center=False` |
| `groupby(dzień).transform("max")` | maksimum całego dnia, także przyszłych godzin | `groupby(dzień).cummax()` |
| `resample("4h").last()` bez `shift(1)` | niezamknięta świeca wyższego interwału | `.shift(1)` przed `reindex(..., ffill)` |
| normalizacja przez min/max całej serii | zna przyszłe skrajności | okno kroczące |

---

## 7. Przykłady (każdy sprawdzany w CI)

`strategies/examples/`: `rsi_trend_pyramid.py` (dokładanie z wagami, `PYRAMID`, `HOURS`, wyjście `rsi_streak`), `rsi_trend_single.py` (to samo, 1 pozycja), `sma200_rsi_pullback.py`, `donchian_breakout.py`, `bollinger_reversion.py`, `macd_trend_adx.py`, `asia_range_breakout.py` (poziomy sesji bez look-ahead), `stoch_session_reversal.py` (filtry czasu).

---

## 8. Co dzieje się po wklejeniu

1. Dashboard sprawdza kontrakt i zapisuje strategię w Firestore ze statusem `do_policzenia` (wymaga logowania).
2. `ia5 start` na Macu odbiera ją w kilka sekund (nasłuch) → `liczy_sie` + postęp w dashboardzie.
3. Sygnały liczone w osobnym procesie, detektor look-ahead, silnik, walidacja.
4. Wyniki trafiają na gałąź `data` (`results/{id}/`) → status `policzona` → karta strategii.
5. Błąd w kodzie → status `blad` z komunikatem; w dashboardzie „Popraw kod”.
