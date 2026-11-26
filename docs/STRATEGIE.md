# STRATEGIE — jak pisać kod strategii dla IA5

Wersja 0.52 · 2026-11-26 (dodane, D-075: zasady portfela — `SIZING_MODE = "risk"`, `VOL_TARGET`, `MAX_CCY`, `BRAKE` — sekcja 5a; opcje wyjść `be`, `stale`, `weekend`, `tp1`/`part` i swapy — sekcja 5; nowe wskaźniki i wszystkie pary w `ind` (`ind.pairs`, `ind.pair_close`, `ind.strength`) — sekcja 3; `TIMEFRAME = "W1"` i `EXECUTE = "H1"` + `ENTRY_HOUR` — sekcja 2b; korelacja strategii; jak myśleć o strategii o małych spadkach — sekcja 11; przykład `ksiega_v2.py`; wcześniej, 0.51: dodane: przykład `eurusd_codziennie_24h.py` — codziennie jedna transakcja na 24 h, własne `EXITS`, `EXPLORE = False`; wcześniej: limit 100 MB pliku transakcji na GitHub — sekcja 2a; `ind.alma` — średnia Arnauda Legoux i przykład `alma_d1_zwrot.py`, D-073; wcześniej: eksploracja Maca po liczeniu i `EXPLORE = False`, kod odmiany „Jako nowa strategia”, OOS na akcjach dla D1 — sekcja 10, D-072; wcześniej: `levels()` z kolumną `bars` — własny limit świec każdego wejścia, D-070; zamknięcie dnia D1 naprawione w danych, D-068; przykład `d1_skladana.py` — księga trzech składników w jednej strategii D1; wcześniej: przykłady `poniedzialek_powrot.py` i `azja_powrot.py` — sygnał w konkretnej godzinie, dzienne zamknięcia liczone z H1, `HOURS = False`, D-069; ostrzeżenie o zamknięciu D1 Yahoo od 2011, D-068; przykład `rsi_d1_seria_w_trendzie.py`; przykład `rsi_d1_powrot_w_trendzie.py` — wersje w `CONFIGS`, wyjście po X dniach przez `level` + `cap`, D-067; wyjście `level` z `cap = 0` — bez limitu czasu, D-061; `TIMEFRAME = "D1"` i tło D1 w strategiach H1 — D-058; `levels()` — D-057; noce i obsunięcie z MAE — D-054/D-055)

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
3a. **Portfel (D-075).** Gdy Michałowi zależy na małych spadkach, rozważ zasady portfela z sekcji 5a (`SIZING_MODE = "risk"`, `MAX_CCY`, `VOL_TARGET`) — nie dodają prób do DSR, bo działają tylko w symulacji kapitału. Hamulca (`BRAKE`) nie dawaj domyślnie — tylko na życzenie albo jako świadomy test. Jak myśleć o całości: sekcja 11.
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

# TIMEFRAME = "D1"             # opcjonalne: świece dzienne (cała historia Yahoo) zamiast H1 — sekcja 2a (D-058)
# EXITS = [...]                # opcjonalne: własna siatka wyjść zamiast domyślnej (sekcja 5)
# SIZING = [5, 10, 20]         # opcjonalne: % kapitału jako depozyt (domyślnie 5, 10, 15, 20, 30)
# PYRAMID = 5                  # opcjonalne, tylko na życzenie: do 5 pozycji naraz w parze, jeden kierunek (D-034)
# HOURS = False                # opcjonalne, tylko na życzenie: bez okna 07–17 (albo (od, do) czasu polskiego)
# MAX_PAIRS = 1                # opcjonalne, tylko na życzenie: najwyżej 1 para z otwartymi pozycjami naraz (D-050)
# PAIR_RANK = ["USDCHF", ...]  # kolejność par przy równoczesnych sygnałach — tylko z wyników IS
# --- D-075 (wszystko opcjonalne) ---
# TIMEFRAME = "W1"             # świece tygodniowe z dziennych — sekcja 2b
# EXECUTE = "H1"; ENTRY_HOUR = 8   # przy TIMEFRAME = "D1": sygnał z dnia, wejście na H1 o 8:00 czasu polskiego — sekcja 2b
# SIZING_MODE = "risk"         # SIZING = % kapitału ryzykowany do SL (domyślnie 0,25 / 0,5 / 1 / 2) — sekcja 5a
# VOL_TARGET = 8               # cel zmienności kapitału, % rocznie — sekcja 5a
# MAX_CCY = 3                  # najwyżej 3 pozycje w jedną stronę na walutę — sekcja 5a
# BRAKE = (10, 20)             # spadek 10% od szczytu → 20 dni bez nowych wejść — sekcja 5a
```

| Element | Szczegóły |
|---|---|
| `df` | Świece H1 **jednej** pary: kolumny `open`, `high`, `low`, `close` (świece H1 Yahoo po warstwie czyszczenia, D8). Indeks `DatetimeIndex` w UTC = czas **otwarcia** świecy. Tylko zamknięte świece. Funkcja jest wołana osobno dla każdej z 8 par. |
| `df.attrs["pair"]` | Nazwa pary, np. `"EURUSD"` — gdy reguła dotyczy tylko niektórych par albo ma inny kierunek dla każdej (D-037). |
| `p` | Słownik z jedną kombinacją `PARAMS` (np. `{"level": 25, "n": 20}`); `{}` gdy brak `PARAMS`. |
| `ind` | Biblioteka wskaźników (sekcja 3). Własnych RSI/ATR/EMA nie piszemy (B9). |
| wynik | `pd.Series` na tym samym indeksie (albo tablica tej samej długości) z wartościami `-1`, `0`, `1`; `True/False` też działa (`.astype("int8")`). `NaN` = 0. Liczba = kierunek × **waga** (0,1–10, np. `-1.6`): waga mnoży depozyt w symulacji kapitału; pipsy i R są na pozycję (D-034). |
| moment | Sygnał w świecy `t` znaczy: warunek spełniony **na zamknięciu** `t`. Wejście silnik robi na **open** `t+1` (B1). |
| godziny | Silnik wchodzi tylko wtedy, gdy świeca `t+1` zaczyna się **07:00–16:00 czasu polskiego** (B11, najniższe spready). Sygnały poza oknem są pomijane i liczone w raporcie — strategia nie musi sama filtrować godzin. Wyjście na dowolnej świecy (także po nocy i weekendzie), według wariantu wyjścia. |
| importy | Tylko `numpy`, `pandas`, `math`. Zakazane: `open`, `exec`, `eval`, `compile`, `__import__`, atrybuty `__…`. |
| czas | Limit 30 min na całe liczenie sygnałów. |

Silnik dodatkowo: pomija sygnały, gdy w danej parze jest już otwarta pozycja tego wariantu (B8), pomija wejścia w okresie rozgrzewki ATR, odrzuca strategię z look-ahead (B2).

**Krótka historia (D-039).** Dane to świece Yahoo od ok. 2024-10 (~12 tys. świec na parę, rośnie z każdą godziną). Wskaźnik z długą rozgrzewką zjada dużą część próby: SMA200 na D1 to ~40% historii, a OOS (ostatnie 25%) to tylko ~6 miesięcy. Preferuj okresy liczone w godzinach i dniach, nie w miesiącach; mało wariantów (`PARAMS` ≤ ~12), bo każdy kolejny przy tak krótkiej próbie mocniej podnosi poprzeczkę DSR. TP i SL w tej samej świecy zawsze liczone jako SL (B5) — bardzo ciasne TP/SL w ATR częściej dają `ambiguous`.

**Świece dzienne Yahoo (D-053, D-058).** Pełna historia D1 (od ok. 2003) jest dostępna na dwa sposoby — sekcja 2a. Filtr dzienny w strategii H1 bierz z `ind.d1(df)`, nie z `resample` na H1: ten sam wskaźnik ma wtedy 20 lat rozgrzewki zamiast 2.

### 2a. Świece dzienne (D-058)

**Strategia na D1** — jedna linia w kodzie:

```python
TIMEFRAME = "D1"

def signals(df, p, ind):             # df = świece DZIENNE jednej pary, indeks = czas otwarcia dnia (północ w Londynie, UTC)
    fast, slow = ind.sma(df.close, 50), ind.sma(df.close, 200)
    return ((fast > slow) & ind.cross_above(ind.rsi(df.close, 14), 40)).astype("int8")
```

- Wejście na open następnego dnia; okno B11 nie dotyczy (`HOURS = (od, do)` = błąd). „Świeca” w wyjściach = dzień: `po 24 świecach` = 24 dni handlu, ATR dzienny, limit `cap` do 480 dni.
- Historia ok. 20 lat × 8 par — rozgrzewka SMA200 to ~4% próby, OOS ~5 lat. Można używać dłuższych okresów i trochę więcej wariantów niż na H1.
- **Rozmiar wyniku (D-073):** `trades.parquet` trafia na GitHub, a ten przyjmuje plik do 100 MB. Na D1 każda transakcja to ok. 4–5 KB na 1 000 sygnałów × 233 wyjść: częsty sygnał (≥ ~10% dni) × 12 wariantów daje setki MB i wynik się nie opublikuje. Przy częstych sygnałach: mniej wariantów (`CONFIGS`) i wyciszenie/potwierdzenie sygnału; `scripts/check_strategy.py` podaje liczbę sygnałów — suma po wariantach ≲ 15 000 na danych syntetycznych mieści się z zapasem.
- Koszt spreadu jest mały wobec ruchu dnia — za to **każda pozycja przechodzi przez noc**: patrz „koszt nocy” w walidacji (D-054), bo swapy (O5) na D1 ważą najwięcej.
- B5 (TP i SL w tej samej świecy → SL) jest na D1 bardziej pesymistyczne — ciasne TP/SL w ATR dziennym często mieszczą się w jednej świecy. Wyjścia czasowe i szerokie (≥ 1,5 ATR) są tu uczciwiej liczone.
- Dane: `data/d1_ready/` — świece z D5-błędem, weekendowe i płaskie (stara historia Yahoo) odrzucone; ≥ 3 brakujące dni robocze z rzędu = przerwa (B12).
- **Zamknięcie dnia (D-068, naprawione w danych, `clean_d1` wersja 2):** Yahoo od ok. 2011 podaje dla par FX `close` ≈ `open` tego samego dnia. W `data/d1_ready/` zamknięcie dnia to ostatnia świeca H1 przed północą w Londynie (tam, gdzie H1 jest — ostatnie ok. 2 lata i na żywo), a wcześniej otwarcie następnego dnia handlu; kolumna `close_src` mówi skąd (2 = H1, 1 = następny dzień, 0 = Yahoo). Uwaga na piątek w starszej historii: jego „zamknięcie” to otwarcie poniedziałku, czyli zawiera lukę weekendową i jest tą samą ceną co poniedziałkowe wejście — regułę „po piątku” potwierdzaj na danych z prawdziwym zamknięciem (`research/d1/README.md`).

**Tło D1 w strategii H1** — kierunek z dziennych, wejście z godzinowych:

```python
def signals(df, p, ind):                                  # df = H1
    d = ind.d1(df)                                        # zamknięte świece dzienne tej pary (DataFrame) albo None
    if d is None:
        return pd.Series(0, index=df.index, dtype="int8")
    up = ind.d1_to_h1(df, d.close > ind.sma(d.close, 200)).fillna(False).astype(bool)   # liczone na D1 → na H1
    return (up & ind.cross_above(ind.rsi(df.close, 14), 30)).astype("int8")
```

- `ind.d1(df)` zawiera tylko dni zamknięte przed końcem `df` (kolumny `open`, `high`, `low`, `close`, `close_ts`).
- `ind.d1_to_h1(df, x)` przenosi wartość dnia d na świece H1 **od zamknięcia dnia d** (północ w Londynie). Nie używaj `reindex(df.index, method="ffill")` — przenosi dzień od jego **otwarcia** i detektor look-ahead to odrzuci.

### 2b. Świece tygodniowe i wykonanie sygnału dziennego na H1 (D-075)

**`TIMEFRAME = "W1"`** — świece tygodniowe budowane w locie z `data/d1_ready` (te same dane i czyszczenie co D1): tydzień pn–pt wg dnia w Londynie, `open`/`close` = pierwszy/ostatni dzień, `high`/`low` = skrajne; sygnał na zamknięciu tygodnia, wejście na open następnego. „Świeca” w wyjściach = tydzień (`cap` do 480 tygodni). Przerwa w danych w którymkolwiek dniu tygodnia albo brak całego tygodnia = przerwa (B12). Eksploracja Maca (sekcja 10) W1 pomija.

**`EXECUTE = "H1"` + `ENTRY_HOUR`** (tylko przy `TIMEFRAME = "D1"`):

```python
TIMEFRAME = "D1"
EXECUTE = "H1"        # sygnał liczony na D1, wejście i wyjścia na świecach H1
ENTRY_HOUR = 8        # wejście na open świecy H1 otwartej o 8:00 czasu polskiego (7–16, okno B11) następnego dnia handlu
EXITS = [{"kind": "time", "n": 24, "cap": 24}, {"kind": "atr", "n": 14, "tp": 2, "sl": 1, "cap": 72}]   # w świecach H1!
```

- Po co: domyślnie strategia D1 wchodzi o północy w Londynie — zaraz po rolowaniu, gdy spready są najszersze. Tu wejście jest rano, po rolowaniu.
- Koszt: liczenie obejmuje tylko okres świec H1 (~2 lata, OOS ~6 miesięcy). Dobre jako **drugi test** strategii D1 (czy wykonanie rano nie zjada przewagi), nie jako jedyny.
- `EXITS`, `cap` i `bars` z `levels()` są w świecach **H1**; ATR w wyjściach = ATR godzinowy. Benchmark losowy losuje wejścia tylko o `ENTRY_HOUR`.
- Dzień sygnału bez świecy H1 o tej godzinie w ciągu 4 dni (przerwa w danych) — pominięty i policzony w manifeście (`execute_skipped`).

---

## 3. Biblioteka `ind`

Wszystkie wskaźniki zgodne z TA-Lib (test `tests/test_indicators.py`; ALMA — z wzorem z definicji, `tests/test_alma.py`), wartości w rozgrzewce = `NaN`.

| Funkcja | Zwraca |
|---|---|
| `ind.sma(x, n)`, `ind.ema(x, n)` | Series |
| `ind.alma(x, n=9, offset=0.85, sigma=6)` | Series — ALMA (Legoux 2009), dzwon Gaussa przesunięty ku najnowszym świecom; offset → 1 szybsza i nerwowa, → 0,5 gładka i spóźniona (D-073, wzorzec: wzór z definicji, TA-Lib jej nie ma) |
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
| `ind.roc(x, n=10)` | D-075: zmiana w % z n świec (TA-Lib ROC) |
| `ind.kama(x, n=10, fast=2, slow=30)` | D-075: adaptacyjna średnia Kaufmana (TA-Lib KAMA) — szybka w trendzie, stoi w szarpaniu |
| `ind.efficiency_ratio(x, n=10)` | D-075: 0–1, \|ruch netto\| ÷ suma ruchów; blisko 1 = trend, blisko 0 = szarpanie (filtr reżimu) |
| `ind.ibs(df)` | D-075: 0–1, gdzie w zakresie świecy jest zamknięcie; < 0,2 na D1 = klasyczny sygnał powrotu |
| `ind.keltner(df, n=20, k=2.0, atr_n=10)` | D-075: DataFrame `mid`, `upper`, `lower` = EMA ± k·ATR |
| `ind.zscore(x, n=20)` | D-075: (x − SMA) ÷ odchylenie z n świec |
| `ind.pct_rank(x, n=100)` | D-075: percentyl bieżącej wartości w oknie n (0–100), np. `pct_rank(ind.atr(df, 14), 250) > 80` = wysoka zmienność |
| `ind.willr(df, n=14)`, `ind.cci(df, n=14)` | D-075: Williams %R i CCI (TA-Lib) |
| `ind.inside_bar(df)`, `ind.narrowest(df, n=7)` | D-075: bool — świeca wewnętrzna; NR-n (najwęższa z n) |
| `ind.pairs(df)` | D-075: słownik para → świece wszystkich 8 par (ten sam interwał), tylko zamknięte do końca df; `None` bez innych par |
| `ind.pair_close(df, "USDJPY")` | D-075: zamknięcie innej pary na świecach df |
| `ind.strength(df, n=24)` | D-075: DataFrame `EUR, USD, JPY, GBP, AUD, CHF, CAD` — siła waluty ze wszystkich par (średnia zmian log z n świec); para X/Y: `s[X] − s[Y]` |
| `ind.d1(df)` | D-058: zamknięte świece dzienne tej pary (tło dla strategii H1) albo `None` |
| `ind.d1_to_h1(df, x)` | D-058: wartość z D1 (Series/DataFrame na indeksie `ind.d1(df)`) przeniesiona na H1 od zamknięcia dnia |

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

# D-075: siła walut — kupuj silniejszą od słabszej (momentum przekrojowe)
s = ind.strength(df, 24)
diff = s[df.attrs["pair"][:3]] - s[df.attrs["pair"][3:]]
ind.cross_above(diff, 0).astype("int8") - ind.cross_below(diff, 0).astype("int8")

# D-075: tylko w trendzie (Efficiency Ratio) i przy zmienności niższej niż zwykle
(ind.efficiency_ratio(df.close, 20) > 0.3) & (ind.pct_rank(ind.atr(df, 14), 250) < 50)
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
    {"kind": "trail", "n": 14, "sl": 2.0, "trail": 3.0, "cap": 480},
    # ↑ stop początkowy 2×ATR14, potem 3×ATR14 od najwyższego high poprzednich świec (long); bez TP (D-035)
    {"kind": "level", "cap": 60},
    # ↑ TP/SL jako CENY ze strategii — wymaga funkcji levels(df, p, ind) (poniżej); bez poziomu = tylko limit czasu (D-057)
]

Limit czasu `cap`: 1–480 świec (B7).

**Bez limitu czasu (D-061, tylko na wyraźne życzenie Michała):** `{"kind": "level", "cap": 0}` — pozycja trwa do TP z `levels()` (bez SL). Gdy do końca danych cena nie dotarła do celu, pozycja ma powód „otwarta”: wyceniona po ostatnim close, wliczona do wszystkich statystyk (też OOS, DSR, benchmark) i opisana w raporcie. Nie ma stopu, więc przegrywająca pozycja trwa — patrz obsunięcie z MAE (D-055) i noce (D-054). Transakcja nachodząca na przerwę w danych jest anulowana (B12), a przy trzymaniu latami przerwy trafiają się częściej — liczby anulowanych są w raporcie.
```

Każde wyjście musi mieć SL albo limit czasu (B7; jedyny wyjątek: `level` z `cap = 0`, D-061).

**Opcje dla każdego wyjścia (D-075, silnik 0.15.0)** — dopisz do słownika w `EXITS`, domyślnie wyłączone:

```python
EXITS = [
    {"kind": "atr", "n": 14, "tp": 3, "sl": 1.5, "cap": 72, "be": 1.0},      # breakeven: po +1 ATR (high zamkniętych świec) SL → cena wejścia
    {"kind": "time", "n": 48, "cap": 48, "stale": 12},                      # po 12 świecach bez zysku (zamknięcie ≤ wejście) → wyjście
    {"kind": "level", "cap": 20, "weekend": True},                          # wyjście na zamknięciu ostatniej świecy przed weekendem/świętem
    {"kind": "atr", "n": 14, "tp": 3, "sl": 1.5, "cap": 72, "tp1": 1.0, "part": 0.5},   # połowa pozycji na +1 ATR, reszta do TP/SL
]
```

- `be` nie bierze high świecy, w której cena spada — kolejność w świecy nieznana (jak B5); powód wyjścia „breakeven”.
- `stale` — powód „bez zysku”; `weekend` — „weekend” (przerwa ≥ 24 h do następnej świecy; na W1 każdy tydzień kończy się weekendem — nie używaj).
- `tp1`: część zamknięta na poziomie; SL w tej samej świecy co tp1 → bez częściowego (pesymistycznie); TP nie niższe niż tp1 w tej samej świecy → z częściowym. Kolumna `partial` w transakcjach. Częściowe TP zwykle **nie** poprawia przewagi — wygładza krzywą kosztem średniego wyniku; licz je jako wariant obok wersji bez niego.
- Każda opcja w `EXITS` to osobny wariant (×1 próba) — nie mnóż ich bez potrzeby.

**Swapy (D-075):** `config.SWAP_PIPS` = pips za noc (long, short) na parę, noce przez 21:00 UTC (weekend = 3). Dziś tabela ma zera (O5 otwarte) — po wpisaniu stawek brokera silnik odejmuje je w pipsach netto (kolumna `swap_pips`); stres 0,5 / 1 pips za noc w walidacji zostaje na dodatek.

### Poziomy w cenie: `levels(df, p, ind)` (D-057)

Gdy reguła mówi „cel w połowie drogi do bazy”, „stop pod dołkiem układu”, „TP na szczycie poprzedniej świecy” — to są
**ceny**, nie wielokrotności ATR. Zamiast przybliżać je w `EXITS`, strategia podaje je wprost:

```python
EXITS = [{"kind": "level", "cap": 60}]

def levels(df, p, ind):                      # ten sam df i p co signals(); liczona na ŚWIECY SYGNAŁU
    low3 = df.low.rolling(3).min()           # dołek układu (tylko zamknięte świece — jak w signals)
    return pd.DataFrame({"tp": df.close + 2 * (df.close - low3), "sl": low3})
```

- Kolumny `tp` i/lub `sl` — ceny; `NaN` = brak poziomu na tej świecy (wtedy tylko limit `cap`). Dla short poziomy są
  po prostu niżej/wyżej — silnik sam bierze kierunek z sygnału; podajesz ceny, nie odległości.
- Poziomy przechodzą **ten sam detektor look-ahead** co sygnały (cięcia + zaburzenie przyszłości): poziom liczony
  z przyszłych świec = `błąd: look-ahead`.
- R liczony względem odległości wejście → SL; bez SL — względem 1 × ATR14 (jak dla innych wyjść bez stopu).
- B5 i B6 bez zmian: TP i SL w tej samej świecy → SL; luka przez SL → open, luka przez TP → poziom TP.
- Benchmark losowych wejść (W3) dostaje te same odległości TP/SL (w ATR) wylosowane z transakcji strategii — porównuje
  moment wejścia, nie regułę wyjścia.
- **Własny limit świec wejścia — kolumna `bars` (D-070):** gdy strategia ma kilka rodzajów wejść i każdy trwa inaczej
  (np. poniedziałkowe 1 dzień, cofnięcie w trendzie 3 dni), `levels()` zwraca też `bars` — liczbę świec, po której TO
  wejście wychodzi na zamknięciu (liczba całkowita ≥ 1; `NaN` = limit wariantu `cap`; silnik przycina do `cap`).
  `bars` może być jedyną kolumną (wtedy bez TP/SL). Limit dotyczy każdego wyjścia z `EXITS`; benchmark losowy losuje
  go razem z poziomami. Przykład: `strategies/examples/d1_skladana.py`.
- Przykład: `strategies/examples/powrot_poziom.py`.

### 5a. Zasady portfela (D-075) — tylko symulacja kapitału

Nie zmieniają transakcji ani rankingu (ranking, DSR, PBO, benchmark — na R), więc **nie dodają prób**. Zmieniają, ile kapitału idzie w każdą transakcję i które wejścia przepadają. Ta sama logika w karcie (`metrics.js`) i w Pythonie.

| Ustawienie | Co robi | Uwaga |
|---|---|---|
| `SIZING_MODE = "risk"` | `SIZING` = % kapitału **ryzykowany do SL**: nominał = ryzyko ÷ odległość do SL (bez SL — do 1 × ATR14). Domyślnie `[0.25, 0.5, 1, 2]`, każde 0–5 | Równe ryzyko w USD na każdą transakcję niezależnie od zmienności pary i odległości stopu — zwykle najprostszy sposób na równiejszą krzywą. Depozyt większy niż wolny jest zmniejszany (licznik `capped`). Domyślnie B4 (depozyt) |
| `VOL_TARGET = 8` | stawka × (8% ÷ zmienność roczna dziennych zmian kapitału z 60 dni przed wejściem), 0,25–2× | Tylko przeszłość (kapitał zrealizowany). Przed 20 dniami historii 1× |
| `MAX_CCY = 3` | najwyżej 3 pozycje (suma wag) w jedną stronę na jedną walutę; long EUR/USD = +EUR −USD | Łapie ukryte skupiska (3 × short USD przez trzy różne pary). Pominięte: licznik „limit walut” |
| `BRAKE = (10, 20)` | po spadku kapitału zrealizowanego o 10% od szczytu — 20 dni bez nowych wejść, potem szczyt od nowa | Często zjada więcej zysku, niż oszczędza na spadkach — testuj, nie zakładaj |

U inwestorów (zakładka Inwestorzy) działają `MAX_CCY`, `VOL_TARGET` i `BRAKE` (najostrzejsze z jego strategii) — `SIZING_MODE = "risk"` **nie**: % inwestora to zawsze depozyt.

**Korelacja (D-075):** po każdym liczeniu walidacja, karta i raport pokazują korelację tygodniowych wyników najlepszego wariantu z innymi policzonymi strategiami (≥ 26 wspólnych tygodni); `ia5 korelacja` na Macu wypisuje całą macierz. |r| < 0,3 = dobry kandydat do wspólnej księgi.

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
| inna para przez `shift(-1)` albo spoza `ind.pairs` | przyszła cena innej pary | `ind.pairs(df)` / `ind.pair_close` / `ind.strength` — detektor tnie i zaburza też inne pary (D-075) |

---

## 7. Przykłady (każdy sprawdzany w CI)

`strategies/examples/`: `donchian_d1_trend.py` (wybicie z kanału + trend D1, wyjścia ATR/SMA/przeciwny), `donchian_d1_trail.py` (to samo ze stopem kroczącym), `trend_pullback_v2.py` (powrót RSI w trendzie, stop w ATR), `rsi_trend_pyramid.py` (dokładanie z wagami, `PYRAMID`, `HOURS`, wyjście `rsi_streak`), `rsi_trend_single.py` (to samo, 1 pozycja), `sma200_rsi_pullback.py`, `donchian_breakout.py`, `bollinger_reversion.py`, `macd_trend_adx.py`, `asia_range_breakout.py` (poziomy sesji bez look-ahead), `stoch_session_reversal.py` (filtry czasu). Nowe: `d1_trend_pullback.py` (strategia na świecach dziennych, `TIMEFRAME = "D1"`, D-058), `h1_z_tlem_d1.py` (H1 z trendem z D1 — `ind.d1`, `ind.d1_to_h1`), `powrot_poziom.py` (TP/SL jako ceny, `levels()`, D-057), `poniedzialek_powrot.py` (H1: RSI2 dziennych zamknięć z 16:00 NY liczonych z H1, sygnał tylko w poniedziałek o 00:00 Londynu, wyjścia czasowe, `HOURS = False`; D-069), `azja_powrot.py` (H1: powrót ruchu z popołudnia w Nowym Jorku, wejście 00:00 Londynu), `d1_skladana.py` (D1: trzy składniki w jednej księdze — poniedziałek przeciw rozciągnięciu z głosowaniem 5 miar, cofnięcie w trendzie, początek miesiąca; każdy z własną liczbą dni przez `levels()` → `bars`, stawka odwrotnie do zmienności, `PYRAMID`; D-070), `rsi_d1_seria_w_trendzie.py` (D1, wersja 2 z diagnozy wejść: od N-tego dnia wyprzedania z rzędu, bez dni-szoków, wyjście po 3–5 dniach), `eurusd_codziennie_24h.py` (D1, tylko EUR/USD: codziennie jedna transakcja open → zamknięcie dnia, kierunek z RSI albo EMA rosnącej/malejącej, 56 wersji w `CONFIGS`, `EXITS` z jednym wyjściem po 1 świecy, `EXPLORE = False`), `alma_d1_zwrot.py` (D1: zwrot ALMA po ruchu trwającym co najmniej 3–5 dni, 3 wersje w `CONFIGS` — 9·0,85·6, 21·0,85·6, 21·0,99·6; D-073), `ksiega_v2.py` (D1, D-075: trzy składniki `d1_skladana` bez zmian + wybicie Donchiana 55 w stronę SMA200 o przeciwnej skośności, stop 2,5 ATR tylko dla wejść trendowych przez `levels()`, `SIZING_MODE = "risk"`, `VOL_TARGET = 8`, `MAX_CCY = 3`; 3 wersje: pełna, bez trendu, sam trend — do porównania i korelacji), `rsi_d1_powrot_w_trendzie.py` (D1: 12 wersji w `CONFIGS` — progi RSI, TP/SL w ATR albo od dołka/szczytu, wyjście po X dniach na zamknięciu przez `level` + `cap`, stawka od serii / otwartych / głębokości, `PYRAMID`, `SIZING`; D-067).

---

## 8. Co dzieje się po wklejeniu

1. Dashboard sprawdza kontrakt i zapisuje strategię w Firestore ze statusem `do_policzenia` (wymaga logowania).
2. `ia5 start` na Macu odbiera ją w kilka sekund (nasłuch) → `liczy_sie` + postęp w dashboardzie.
3. Sygnały liczone w osobnym procesie, detektor look-ahead, silnik, walidacja.
4. Wyniki trafiają na gałąź `data` (`results/{id}/`) → status `policzona` → karta strategii.
5. Błąd w kodzie → status `blad` z komunikatem; w dashboardzie „Popraw kod”.
6. Potem, gdy Mac nie ma innej pracy — **eksploracja** (do 60 min, sekcja 10): wynik dopisuje się do karty i do raportu dla Claude.

---

## 9. Strategia z głębokiego poszukiwania (`ia5 search`, D-044)

Gdy Michał chce „setek tysięcy kombinacji”, **nie** piszemy strategii z ogromnym `PARAMS` (K1, pamięć, kara w DSR). Zamiast tego:
1. Na Macu: `ia5 search --rozmiar duzy --zero 5` (albo `gigant`, więcej przebiegów zerowych = dłużej i uczciwiej). Wybór wyłącznie na IS; OOS otwierany raz dla K konfiguracji ustalonych z góry.
2. Wynik: `~/.ia5/searches/{run}/search.md` + `strategy.py` — ≤ 12 najlepszych konfiguracji IS (`CONFIGS`, `PARAMS = {"cfg": …}`, własne `EXITS`, sekcja reguł skopiowana z `runner/ia5/search_rules.py`). Ten plik wkleja się do dashboardu bez zmian.
3. Ocena: najpierw test zerowy i OOS **całej listy K** w `search.md`, potem karta w dashboardzie (benchmark losowy, PBO, walk-forward, spread ×1,5). DSR w karcie liczy tylko warianty tej strategii — prawdziwa liczba prób jest w `search.md`.
4. Nie wybieramy z listy K tej konfiguracji, która wyszła najlepiej na OOS (W1). Rozstrzyga forward test po zamrożeniu (W4).
5. Nowy wyzwalacz albo filtr dopisujemy w `search_rules.py` (sekcja między znacznikami — tylko `numpy`, `pandas`, `math`, `ind`) z testem look-ahead w `tests/test_search.py`.

---

## 10. Eksploracja Maca i OOS na akcjach (D-072)

Po zwykłym liczeniu Mac sam szuka lepszych odmian strategii — nie trzeba ich dopisywać do `PARAMS` (zostaje ≤ ~12 kombinacji, K1).
- **Co sprawdza:** przekształcenia sygnału (odwrócony, tylko long/short, z trendem/przeciw trendowi SMA200, z trendem SMA50, podwyższona/niska zmienność, silny trend / brak trendu wg ADX, z wybiciem 20 świec, po cofnięciu do SMA20, potwierdzenie następną świecą), stop kroczący, szerszą siatkę parametrów (środki i krok poza krańce; parametry-numery wersji jak `cfg` zostają), połączenia dwóch najlepszych przekształceń.
- **Jak wybiera:** tylko po IS — gorszy z Sharpe na transakcję w dwóch połowach IS. 5 kandydatów raz na OOS, DSR względem wszystkich prób eksploracji, benchmark losowy, kod kandydata sprawdzony w piaskownicy.
- **Strategie D1:** oryginał i kandydaci dodatkowo na świecach dziennych spółek z zakładki Stocks (koszt 0,1% na stronę, losowe wejścia na tych samych spółkach jako tło). Pilotaż: „akcje potwierdzają” wzmacnia zaufanie do wzoru ze świec, ale nie zmienia werdyktu. Strategia zależna od nazwy pary (`df.attrs["pair"]`) albo od kalendarza FX na spółkach nic nie da — to też informacja.
- **Wyłączenie:** `EXPLORE = False` w kodzie (np. strategia z `ia5 search`, która już przeszła duże przeszukanie).
- **Dla Claude przy ocenie raportu:** sekcja „Eksploracja Maca” mówi, czy odmiana jest lepsza od oryginału **po uczciwej korekcie**. Kandydat 🟢 można wkleić przyciskiem „Jako nowa strategia” — jego OOS był już raz oglądany, więc rozstrzyga forward test po zamrożeniu (W4). Nie dopisujemy kolejnych odmian ręcznie pod wynik OOS kandydatów; wiersz „OOS oglądany” w karcie pokazuje, ile razy ten okres był już widziany.

---

## 11. Strategia o małych spadkach — jak myśleć (D-075)

Zasady, które Claude stosuje, gdy Michał prosi o „najbardziej konsekwentną strategię z możliwie małymi spadkami”:

1. **Nie szukaj strategii o małym spadku — szukaj najwyższego stabilnego Sharpe'a, a spadek ustaw wielkością pozycji.** Spadek ≈ Sharpe × dźwignia: ta sama strategia przy 5% depozytu ma ~6× mniejszy spadek niż przy 30%. Prawdziwa poprawa to tylko wyższy Sharpe przy tej samej liczbie prób.
2. **Najpierw płatnik.** Przewaga z kimś, kto płaci, przetrwa: płynność (ktoś musi zamknąć — poniedziałkowy powrót, cofnięcie w trendzie), przepływy (początek miesiąca), premia za ryzyko (carry, trend 3–12 miesięcy). Reguła bez płatnika to szum dopasowany do historii — wpisz płatnika w `HYPOTHESIS`.
3. **Łącz przeciwne skośności.** Powrót do średniej: gładko, potem krach (ujemna skośność — RSI 2 i Powrót oblały DSR właśnie przez to). Trend: dużo małych strat, rzadkie duże zyski. Razem wygładzają krzywą lepiej niż każde osobno (`ksiega_v2.py`).
4. **3–5 słabych, mało skorelowanych przewag > jedna mocna.** Przy korelacji ≈ 0 Sharpe księgi rośnie ≈ √N. Sprawdzaj korelację (sekcja 5a, `ia5 korelacja`) zanim dołożysz składnik.
5. **Portfel, nie sygnał, tnie spadki:** `SIZING_MODE = "risk"` (równe ryzyko), `MAX_CCY` (skupiska waluty), `VOL_TARGET` (mniej, gdy rynek nerwowy). Bez nowych prób w DSR.
6. **Jedna miara stabilności, z góry, tylko na IS** — np. najgorszy wynik z kroczących 12 miesięcy albo czas pod wodą. Nie przeglądaj dziesięciu metryk, bo któraś zawsze „wygra”.
7. **Zakładaj, że OOS da ~połowę Sharpe'a z IS** i dobieraj wielkość pozycji pod tę połowę. Warunek wyłączenia ustal przed startem (forward z |z| ≥ 2, W4).
8. **Na D1 licz koszty dnia:** swapy (sekcja 5 — po wypełnieniu tabeli), wejście po rolowaniu (`EXECUTE = "H1"`, sekcja 2b) jako drugi test.
