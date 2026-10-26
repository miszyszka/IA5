# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

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
