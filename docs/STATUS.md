# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

## 2026-10-31 — sesja 4

**Zrobione (D-039: tylko świece Yahoo)**
- Dukascopy usunięte z kodu, dokumentów i strony: `ia5 fetch`, `ia5 sync`, pobieranie M1, rozstrzyganie TP/SL na M1, mapa Dukascopy, wskaźnik „Pobieranie”. Jeden proces `ia5 start`: weryfikacja danych → nasłuch strategii; synchronizacja co godzinę.
- Pierwszy start na Macu sam usunie dane i wyniki Dukascopy (lokalnie i z gałęzi `data`) i wyśle policzone strategie do ponownego liczenia na Yahoo.
- Warstwa czyszczenia dla Yahoo sprawdzona na prawdziwych świecach (2 lata × 8 par): stare płaskie świece po zamknięciu i w święta odrzucane, granica tygodnia nie jest przerwą, 3 przerwy Yahoo (26, 6, 66 h) oznaczone — transakcje przez nie są anulowane.
- Kopia świec bez dziur po dłuższej przerwie Maca (wcześniej tylko 2 ostatnie miesiące). Przegląd zdrowia: kontrola „Kopia danych na Macu”, trójkąty skalibrowane na Yahoo, zamrożone notowania tylko w sesji. Strona i Apps Script: pierwsze ≤ 3 h tygodnia to „otwarcie tygodnia”, nie awaria.
- Pełny przebieg na prawdziwych świecach: `do_prepare` < 1 s, strategia „poranna sesja Europy” (18 wariantów × 8 par) 12 s. 116 testów + Node zielone.

- **D-040:** Stats — kalendarz danych dzień po dniu całej historii (miesiąc po miesiącu) zamiast dziennika 30 dni.

- **D-041:** lokalnie tylko świece Yahoo (8 par) i dane do liczenia z nich — reszta usuwana przy każdym starcie i synchronizacji; silnik odmawia liczenia na danych spoza Yahoo; kontrola „Dane lokalne” w przeglądzie zdrowia.

- **Strategia 5b** (`strategies/examples/donchian_d1_trail_v2.py`): strategia 5 na Yahoo — 0/48 wariantów na plusie, percentyl 44, mediana trzymania 18 h (stop 2–4 × ATR H1 ≈ 0,3–0,7 dziennego zakresu, nie mierzył hipotezy tygodniowych trendów). 5b: to samo wejście, stop początkowy 10/15 i kroczący 10/15/20 × ATR14(H1) (≈ 2–4 dzienne ATR), D1 bez niedzielnych skrawków. Zmiana po obejrzeniu OOS wersji 5 — OOS 5b nie jest czysty, łącznie 96 prób; rozstrzyga forward test.

- **Apps Script:** Yahoo 30.10.2026 17:59–18:25 UTC zwróciło dla USD/CAD i USD/CHF 63 notowania z czasem nie na pełnej godzinie; trafiły do Firestore (świece godzinowe obok są całe), warstwa czyszczenia je odrzuca (D5). Od teraz `tick` ich nie zapisuje (flaga `ts` + wpis w logu), a `lastTs` jest zawsze pełną godziną. Stare wpisy w Firestore zostają (D4, bez zgody nie usuwamy).

**Następne (Michał)**
1. Wkleić nowy `apps_script/Code.gs` do Apps Script (bez fałszywych flag „luka” na otwarciu tygodnia). Opcjonalnie raz `backfill()` — uzupełni 3 przerwy Yahoo, jeśli Yahoo ma już te świece.
2. Na Macu: zatrzymać `ia5 fetch` i `ia5 start` (Ctrl+C), `git pull`, potem tylko `ia5 start` (jeden terminal). Pierwszy start usunie dane Dukascopy i przeliczy strategie.

**Znane problemy**
- Historia krótka (od 2024-10): OOS ≈ 6 miesięcy, mało transakcji w rzadkich strategiach — werdykty będą częściej 🟡/🔴 z braku mocy, nie z braku przewagi.
- TP i SL w tej samej świecy zawsze SL (brak danych wewnątrz świecy) — pesymizm rośnie przy ciasnych wyjściach ATR.

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

- Strategia 5 (sezon EUR/USD, Dukascopy): 🟡 4/5 — percentyl 100, PBO 0,07, OOS +0,7 pips; lata 2003–2011 (niewidziane w badaniu) w 7/9 dodatnie. DSR 0,60 — przewaga na transakcję mała (+1,7 pips), słabnie od 2020.
- **D-037:** `ia5 scan` — skaner hipotez (5,7 tys. / z `--duzy` 160 tys. reguł na parę), FDR + potwierdzenie, OOS pominięty; `df.attrs["pair"]` w strategiach.

- **Skan 2026-10-27 22:06** (`--duzy`, tylko EUR/USD + USD/JPY z danymi): 312 tys. reguł, próg t ≥ 4,23, 7 odkrytych, 1 potwierdzona (EUR/USD long w grudniu 01–08 Londynu). Poranny short EUR/USD nie przeszedł progu duże siatki — za dużo słabych reguł podnosi poprzeczkę.
- **D-038:** silnik liczy wszystkie pary z zatwierdzonymi miesiącami (zmiana D8 za zgodą Michała). Skaner: lata dodatnie, „najbliżej progu”, opis danych per para.

- **Skany 2026-10-28** (standard 11 tys. i duży 313 tys. reguł; dane nadal tylko EUR/USD i USD/JPY ~ połowa historii): potwierdzona 1 reguła (EUR/USD long w grudniu nocą, 17/18 lat dodatnich); najbliżej progu — poranny short EUR/USD (15–16/18 lat, płaskowyż). Reguły o 22–23 Londynu (godzina rolowania, realny spread wyższy) odrzucone jako artefakt kosztów. Strategia `eurusd_seasonal_pair.py`: oba składniki, 2 warianty, `HOURS = False` (wymaga zgody na wyjątek B11).

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
