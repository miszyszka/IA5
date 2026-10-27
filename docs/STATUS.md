# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

## 2026-10-27 — sesja 3

**Zrobione**
- Stats: **mapa pokrycia danych** (D-022) — 8 par × miesiące, Dukascopy od 2003 i Yahoo 730 dni; statusy miesięcy, dziury tylko jednej pary vs luki wspólne, potwierdzenie z drugiego źródła, cienkie godziny, lista luk co do godziny po kliknięciu, „największe dziury”, pokrycie % i ile miesięcy / godzin jeszcze brakuje. W trakcie pierwszego pobierania wypełnia się na żywo.
- Mac: `ia5/coverage.py`, publikacja `coverage/coverage.json` na gałąź `data`, `heartbeat.sync`; naprawione kasowanie `job` w heartbeacie po każdej parze.
- Testy: kalendarz wektorowy vs `is_expected_bar` (każda godzina 2003–2026), podłożone luki, przepływ `do_sync` bez sieci, publikacja tylko przy zmianie, logika mapy w Node. Zrzuty w headless Chromium 1440 / 390 px (spoczynek, pobieranie na żywo, klik w miesiąc, klik w parę, Yahoo).

- **Przegląd zdrowia** (D-023): `ia5/health.py`, `ia5 health`, co godzinę w `ia5 start`, panel „Stan systemu” w Stats, liczba problemów w nagłówku (zamiast kafelka „Kontrola krzyżowa”).

- **Dźwignia 30:1** (D-024, zmiana B4 na polecenie Michała), `ENGINE_VERSION` 0.1.0.
- **Pobieranie Dukascopy (D-025):** niepełne miesiące zapisywane od razu z listą brakujących dni, kolejne przebiegi pobierają tylko brakujące; szybciej (8 dni naraz, 3 próby); mapa publikowana po każdej parze w trakcie długiego pobierania.

- Stats: audyt Yahoo świeca po świecy (3 tygodnie, D-027), kafelek przeglądu z listą problemów, usunięte flagi jako osobna lista; tempo pobierania Dukascopy dobierane do dławienia (D-026).

- **B11 (D-028):** handel tylko 07:00–17:00 czasu polskiego (silnik + benchmark), `ENGINE_VERSION` 0.2.0; święta 25.12 i 1.01 w kalendarzu; dziury tylko tam, gdzie rynek działał i cena się ruszała; mapa Dukascopy: wysokość = ile pobrano, kolor = wielkość dziur.

- **Pobieranie Dukascopy (D-029):** przebieg szybki + naprawczy, krótkie limity, postęp i szacowany czas w logu. Stan 27.10 13:11 UTC: EUR/USD 99%, USD/JPY ~25%, pozostałe 6 par 0%.

- **B11 (D-030):** zamknięcie najpóźniej 23:00 czasu polskiego, `ENGINE_VERSION` 0.3.0; Dukascopy czeka przy pełnej blokadzie serwera (503).

- **D-031: dwa procesy.** `ia5 fetch` pobiera Dukascopy para po parze do końca (EUR/USD najpierw), dni odrzucane długo → niedostępne; `ia5 start` liczy tylko na zatwierdzonych miesiącach EUR/USD (`data/h1_ready/`). Luki ≤ 3 h uzupełnione i oznaczone, dłuższe anulują transakcje (B12, D8), także w benchmarku. `ENGINE_VERSION` 0.4.0. Nagłówek dashboardu: nowy wskaźnik „Pobieranie”; mapa na żywo z pobieracza. 101 testów + Node zielone.

- **D-032:** wyjście na dowolnej świecy (bez 23:00), anuluje tylko przerwa w dostępie do danych; weekend/święto/cisza nie. `ENGINE_VERSION` 0.5.0.
- **D-033:** Apps Script co 1 min + rundy co 15 s po pełnej godzinie; nagłówek i Stats → Yahoo: czerwony zegar od pełnej godziny do zapisu, audyt ostatniej doby z godzinami.
- Wykres transakcji: okna zamiast sklejonych wycinków, nawigacja ← → (D-031a). 107 testów + Node zielone.

- **D-034:** dokładanie pozycji (`PYRAMID`), wagi pozycji (|sygnał| mnoży depozyt), wyjście `rsi_streak`, `HOURS = False` dla strategii; `ENGINE_VERSION` 0.6.0. Strategie „RSI 70/30 w silnym trendzie” w dwóch wersjach: `strategies/examples/rsi_trend_pyramid.py` i `rsi_trend_single.py`. 122 testy + Node zielone.

- Analiza „RSI 70/30 w silnym trendzie” (obie wersje 🔴): straty z braku stopu cenowego (do −332 pips), wejście w chwili przebicia łapie początki odwróceń, dokładanie powiększa obsunięcie (−25% przy 5% depozytu), OOS 2021–2024 ujemny, tylko EUR/USD. Nowa strategia `strategies/examples/trend_pullback_v2.py`: 32 wejścia × 39 wyjść (każde z SL) = 1248 wariantów, ok. 70 s na 23 latach EUR/USD.

- Strategia 3 (🔴): stopy zadziałały (max obsunięcie −2,5% przy 5%), ale brak przewagi w całej siatce (średnio −0,04 R, 27% wariantów dodatnich, korelacja IS–OOS 0,12, PBO 0,79). Filtr H4 (EMA50) dublował EMA200 H1 — identyczne wyniki; poprawione w nowych strategiach na D1.
- **D-035:** stop kroczący (`trail`), limit czasu w `EXITS` do 480 świec, `ENGINE_VERSION` 0.7.0. Strategie 4 i 5: `donchian_d1_trend.py` (8 × 12 = 96 wariantów), `donchian_d1_trail.py` (8 × 6 = 48).

- Strategia 4 (🔴): trend-following IS +0,04 R, OOS −0,11 R, korelacja IS–OOS −0,19 — EUR/USD trendował do ~2014, potem nie.
- **D-036:** badanie na niezależnych danych (`research/`): jedyny efekt, który przeszedł filtr na 8 parach — EUR/USD słabnie w porannej sesji Europy. Strategia `eurusd_europe_morning.py` (3 × 6 = 18 wariantów); na danych badania (nie niezależny test) 🟡 4/5.

**Następne (Michał)**
0. Wkleić nowy `apps_script/Code.gs` do Apps Script, zapisać i **raz uruchomić `installTrigger()`** (wyzwalacz co 1 min zamiast co 5).
1. Na Macu: przerwij działające `ia5 start` (Ctrl+C), `git pull`. Potem **dwa terminale**: w pierwszym `ia5 fetch` (pobiera, działa bez końca), w drugim `ia5 start` (liczy).
2. Strategie policzone przed 0.5.0 dashboard oznaczy jako nieaktualne — „Policz ponownie” (bez limitu 23:00 wyniki się zmienią).

**Znane problemy**
- `ia5 start` ładuje całe M1 EUR/USD do pamięci przy przebudowie danych do liczenia (kilkaset MB, raz po zmianie plików).
- Miesiąc, z którego nic nie zeszło (pełna blokada), nie jest nigdy uznawany za niedostępny — pobieracz wraca do niego co obieg; do tego czasu jest długą luką.
- Próg „wspólnej” luki (≥ połowa par) i „bez ruchu” (≤ 3 h, < 1 pips) to założenia; do kalibracji na prawdziwych danych Dukascopy.

## 2026-10-26 — sesja 2

**Zrobione**
- Dashboard: nowy design (D-019) — płasko, jeden akcent, poświata tylko na kropkach stanu. Nagłówek: zakładki + Dane i Mac obok siebie + flagi (tylko gdy są) + jeden kafelek „8 par”. Kafle KPI usunięte.
- Nowa zakładka **Stats**: świece w bazie, latencja, kontrola krzyżowa, flagi, **dziennik dzień po dniu** (30 dni, dodane / oczekiwane, per para), tabela par, lista flag.
- Apps Script: `meta/status.daily` (D-020) + ręczne `rebuildDaily()`.
- Dukascopy: naprawiona trwała luka na końcu miesiąca, gdy `ia5 start` nie działał w ostatnim dniu miesiąca (D-021); test regresji.
- Sprawdzone w headless Chromium na 1440 / 1100 / 390 px (lista, Stats, karta DEMO), bez błędów JS (błędy w logu to tylko blokowane czcionki i limit API GitHub w sesji Claude).

**Następne (Michał)**
1. Wkleić nowy `apps_script/Code.gs` do Apps Script (zapisz). Najbliższy `tick()` sam zasieje dziennik z bazy — Stats pokaże go od razu.
2. Na Macu `git pull` — poprawka luk Dukascopy działa przy następnym `ia5 start`.

**Znane problemy**
- Dziennik w Stats liczy świece Yahoo. Kompletność Dukascopy dzień po dniu (dane do backtestów) — do zrobienia: Mac mógłby publikować ją na gałąź `data`.

## 2026-10-26 — sesja 1

**Zrobione (kod w repo, testy zielone — 75)**
- E0: infrastruktura, CI, Pages, reguły Firestore, SETUP.
- E1: Apps Script (Yahoo → Firestore co 5 min, kontrola jakości, latencja) — uruchomione przez Michała.
- E2: `ia5 start` — Dukascopy M1 → H1, sync Yahoo, kontrole, gałąź `data`, heartbeat, kolejka, resync co 6 h, forward test zamrożonych.
- E3: wskaźniki zgodne z TA-Lib, silnik 233 wyjść (B1–B8, resolver M1), zgodność z backtesting.py, sandbox + detektor look-ahead (cięcia + zaburzenie przyszłości).
- E4: dashboard — status, lista (szukaj, sortuj, usuń), okno nowej strategii z kontrolą na żywo, karta strategii (werdykt, walidacja, filtry par/kierunku/próby/depozytu, ranking, heatmapa TP×SL, krzywa wyjść czasowych, kapitał + obsunięcie, świece z transakcjami, rozbicia, tabela + CSV, raport dla Claude, zamrażanie, ponowne liczenie). Przetestowany w headless Chromium (bez błędów konsoli), także na szerokości telefonu.
- E5: walidacja — benchmark losowych wejść, DSR, PBO (CSCV), walk-forward, bootstrap, spread ×1,5/×2/faktyczny, kapitał 5–30%, werdykt.
- Reguła „zrób mi strategię” (K1–K3, `docs/STRATEGIE.md`), `scripts/check_strategy.py`, `ia5 check`, 6 przykładów w `strategies/examples/`.
- Sprawdzone na żywej stronie (przeglądarka w aplikacji Claude): status z Firestore (DZIAŁA, 97 808 świec, 0 flag), karta DEMO z gałęzi `data` (fragmenty Parquet zakresami HTTP), 0 błędów konsoli.
- DEMO na gałęzi `data`: strategia z przykładu CLAUDE.md policzona na prawdziwym EUR/USD H1 2017–2018 (dane z backtesting.py) — do podglądu, usuwa się przyciskiem.

**Następne (Michał)**
1. ✅ Logowanie, UID w regułach, usuwanie strategii — działa.
2. ✅ Dukascopy pobiera się na Macu.
3. Na Macu: `~/.ia5/config.json` = `{"owner_uid": "<UID>"}`, instalacja i `ia5 start` (docs/SETUP.md).
4. Pierwsza własna strategia z dashboardu → sprawdzić cały obieg.

**Znane problemy / ryzyka**
- Format plików Dukascopy potwierdzony na Macu (2026-10-26): EURUSD 2003-06 bid 1,17815 / ask 1,17825, spread 1 pips, minuty bez wolumenu pomijane przy budowie H1.
- Windows: `403 Missing or insufficient permissions` ustąpiło po dodaniu roli w IAM (z opóźnieniem propagacji) — o 15:44 heartbeat z hosta `1h85476gv9` w stanie `syncing`, czyli `ia5 start` przeszedł przez Firestore i zaczął pobierać Dukascopy. Do potwierdzenia pełnym przebiegiem.
- Yahoo bez oficjalnego API (tylko monitoring). Święta poza kalendarzem sesji (D-009).
- `clasp` nieustawiony — kod Apps Script wklejany z repo.
- O5 (swapy) otwarte.
