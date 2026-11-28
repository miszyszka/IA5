# ROADMAP — jak IA5 ma się dalej rozwijać

Wersja 0.6 · 2026-11-28 · Spisane po przeglądzie całego projektu (D-054–D-058); REV (D-063); FOREST usunięty, Stocks (D-071); eksploracja Maca i OOS na akcjach (D-072); narzędzia do strategii o małych spadkach (D-075); zakładka Zasięg (D-076). Aktualizować, gdy zmienia się kierunek.

## Zasada nadrzędna

**Celem jest zyskowna strategia, nie bogatszy system.** Każdy kolejny krok ma odpowiadać na jedno z trzech pytań:
1. Czy zwiększa szansę znalezienia przewagi, która przetrwa koszty? (dłuższa próba, niższe koszty względem ruchu, nowe źródło informacji)
2. Czy skraca drogę od pomysłu do uczciwego werdyktu?
3. Czy przybliża rzeczywisty handel (forward → małe realne konto)?

Rzeczy, które tylko dokładają warstwę (kolejne zakładki, ładniejsze wykresy, więcej wariantów tej samej przestrzeni H1) — odkładamy.

## Gdzie jesteśmy (2026-11-11)

- **Infrastruktura** (dane, silnik, walidacja, dashboard, inwestorzy, maile) — dojrzała, przetestowana (≈ 200 testów), uczciwa wobec look-ahead i przeszukania. Nie wymaga rozbudowy.
- **Wynik badań na H1:** skaner, `ia5 search` (3,1 mln konfiguracji) i FOREST nie znalazły przewagi prostych reguł H1 po kosztach. Na H1 spread to 15–25% ATR godzinowego, a historia to 2 lata (OOS 6 miesięcy, już otwierany 2 razy).
- **Żywe kandydatki:** RSI 2 (🟡 4/5, OOS +6,2 pipsa, 134 transakcje) i Powrót (🟡 4/5, OOS +10,0, 72) — obie oblewają DSR z powodu braku stopu (skośność −2,4 / −4,5). Inwestor „Combined” na żywo od 3.11.
- **Nowe od dziś:** strategie na D1 z ~20 latami historii (D-058), tło D1 w H1, TP/SL jako ceny (D-057), uczciwy forward test (D-056), noce i obsunięcie z MAE w każdym raporcie (D-054, D-055).

## Etap A — teraz (1–3 tygodnie): sprawdzić D1

Najtańszy krok o największej szansie. Nic nowego w kodzie — tylko używanie tego, co jest.

1. **Michał:** `git pull`, `uv tool install -e runner --force`, restart `ia5 start` (zbuduje `data/d1_ready/`). Jeśli `backfillD1()` jeszcze nie był uruchomiony w Apps Script — najpierw on (`docs/SETUP.md`, „Świece dzienne D1”).
2. Policzyć wzorcowe strategie D1 (`d1_trend_pullback.py`) i 3–5 klasycznych hipotez dziennych, każda **spisana przed liczeniem**:
   - trend: przecięcie / nachylenie SMA50–200, wybicie Donchian 20/55 (żółwie), z wyjściem czasowym albo stopem kroczącym;
   - powrót: RSI 2–3 na D1 w trendzie SMA200 (odpowiednik żywej RSI 2, ale na 20 latach zamiast 2);
   - carry/sezonowość: dzień tygodnia, koniec miesiąca (przepływy rebalansowe), grudzień EUR/USD (z D-038 — teraz da się sprawdzić na 20 latach).
3. Przy każdej patrzeć najpierw na: **noce × koszt nocy** (D-054) i **obsunięcie z MAE** (D-055), potem na werdykt.
4. **Kryterium wyjścia z etapu:** jedna strategia D1 z 🟢 albo 🟡 z DSR ≥ 0,8 i dodatnim wynikiem przy koszcie nocy 1 pips → zamrozić (W4) i dać inwestorowi.
5. Jeśli żadna: to też wynik — wtedy etap B.

## Etap B — gdy D1 da kandydatkę (miesiąc): z backtestu do rzeczywistości

1. **Swapy naprawdę (zamknięcie O5).** ✅ Mechanizm gotowy (D-075): `config.SWAP_PIPS` (long/short, pips za noc) + `SWAP_VERSION`, silnik odejmuje `nights × stawka`. **Zostało:** Michał wybiera brokera i wpisuje stawki (raz w miesiącu), wpis w DECISIONS.
2. **Spread zmienny w czasie** — stały spread z tabeli jest optymistyczny w nocy i w okolicy danych. Dla D1 (wejście o północy w Londynie = zaraz po rolowaniu, najszersze spready dnia!) to ważne: rozważyć wejście na open świecy H1 o 08:00 Londynu po sygnale D1 — „sygnał D1, wykonanie H1”. To naturalne rozszerzenie D-058 (strategia D1 z `ENTRY_HOUR`), ale **tylko jeśli** etap A coś znajdzie. ✅ Gotowe (D-075): `EXECUTE = "H1"` + `ENTRY_HOUR` — używać jako drugiego testu kandydatki D1 (liczy się tylko na ~2 latach H1).
3. **Forward na żywo ≥ 3 miesiące** w zakładce Inwestorzy, porównywany z blokiem `forward` (z-score wobec oczekiwania). Przy |z| ≥ 2 — stop i analiza.
4. **Małe realne konto** (decyzja Michała, poza systemem): ta sama strategia, minimalny lot, ręcznie z maili inwestora. System już wysyła sygnał, otwarcie i zamknięcie.

## Etap C — gdy D1 nic nie da (opcje, w kolejności sensowności)

1. **`ia5 search --d1`** — ta sama maszyna przeszukiwania (FDR, test zerowy, raz OOS), ale na świecach dziennych. Mało kodu (silnik już działa na D1), dużo nowej próby. Zrobić dopiero po etapie A, żeby nie zmarnować OOS D1 przeszukaniem przed sprawdzeniem prostych hipotez.
2. **Portfel zamiast pojedynczej strategii** — kilka słabych (🟡), mało skorelowanych strategii na wspólnym kapitale. Inwestor już to umie (wspólny kapitał, wiele strategii). ✅ Raport korelacji (D-075): w walidacji każdej strategii i `ia5 korelacja`; do tego zasady portfela (stawka od ryzyka, limit walut, cel zmienności) i przykład `ksiega_v2.py`.
3. **Inne dane (zmiana D7 — tylko za zgodą Michała):** stopy procentowe (różnica stóp = carry), kalendarz danych makro (unikanie / granie publikacji). To nowe źródło informacji, nie nowa kombinacja tych samych świec — jedyna droga, jeśli ceny same nie wystarczą.

## REV — osobny tor (D-063)

REV nie zmienia etapów A–C: to portfel walut wobec złotego, bez dźwigni i kosztów, liczony obok strategii FX.

| Etap | Zakres | Gotowe, gdy |
|---|---|---|
| **R0 Dane** | kursy `{WALUTA}PLN=X` (Apps Script `backfillPLN` + `tickPLN_`), kopia i czyszczenie (tylko zamknięcia), kontrola „Kursy złotówkowe (REV)” | lista przyjętych walut w `DECISIONS.md`, kontrola zielona, nowe dni dopisują się same |
| **R1 Badanie metody** | turniej 13 wariantów (przecena, trend, połączenie × 2 podziały + przełącznik), walidacja, werdykt, zamrożenie | raport z werdyktem na stronie |
| **R2 Portfel na żywo** | wtorek 08:00, wycena dzienna, dziennik, równy podział obok; Actions + Mac zapasowo | pierwszy wtorek przeliczony sam |
| **R3 Zakładka REV** | słupki, linia, ranking, transakcje, badanie | wszystko na żywej stronie |
| **R4 Później (na życzenie)** | mail we wtorek z listą przewalutowań; inflacja i stopy procentowe (zmiana D7) | decyzja Michała |

## Stocks — osobny tor (D-071)

Portfel spółek Michała rebalansowany co wtorek na otwarciu, w paśmie ±20% udziału docelowego. Nie zmienia etapów A–C.

| Etap | Zakres | Gotowe, gdy |
|---|---|---|
| **S0 Dane** | `tickSTK_` w Apps Script (lista ze strony, dywidendy, splity), kopia i czyszczenie na Macu, kontrola „Spółki (Stocks)” | reguły Firestore wdrożone, 27 spółek w bazie, kontrola zielona |
| **S1 Backtest** | turniej 4 374 konfiguracji, walidacja, werdykt, raport | wynik na stronie dla udziałów Michała |
| **S2 Na żywo** | plan wtorek 08:00, wykonanie na otwarciu, całe akcje, dywidendy, porównania | pierwszy wtorek wykonany sam |
| **S3 Później (na życzenie)** | mail we wtorek z listą zleceń; waluta inna niż USD; dane fundamentalne (zmiana D7) | decyzja Michała |

## Eksploracja i drugi OOS (D-072)

- Każda strategia dostaje po liczeniu godzinę „kreatywnego” liczenia na Macu — odmiany wybierane tylko po IS, kandydaci raz na OOS, DSR z wszystkich prób.
- Strategie D1 mają drugi, niezależny OOS: świece dzienne spółek (pilotaż, poza werdyktem). Jeśli po kilku strategiach okaże się, że „akcje potwierdzają” idzie w parze z dobrym forwardem — rozważyć wpisanie go do werdyktu (decyzja Michała).
- Następne kroki do rozważenia: odmiany H1 z tłem D1 (trend dzienny jako filtr), „ten sam wzór H1 na D1”, raport korelacji kandydatów z już zamrożonymi strategiami (portfel zamiast pojedynczej strategii — etap C2).

## Małe spadki (D-075) — co jest gotowe i jak używać

- Narzędzia: `SIZING_MODE = "risk"`, `VOL_TARGET`, `MAX_CCY`, `BRAKE` (portfel), opcje wyjść `be` / `stale` / `weekend` / `tp1`, wskaźniki reżimu (`efficiency_ratio`, `pct_rank`, `kama`, `ibs`…), `ind.strength` (siła walut ze wszystkich par), `TIMEFRAME = "W1"`, `EXECUTE = "H1"`, korelacja strategii.
- Kolejność pracy: (1) `ksiega_v2.py` na Macu — porównać cfg 0 / 1 / 2 i korelację z `d1_skladana`; (2) jeśli trend obniża korelację i spadek — zamrozić cfg 0, inwestor; (3) nowa przewaga przekrojowa (`ind.strength`, momentum 3–12 miesięcy na W1) jako osobna strategia, potem do księgi tylko przy |r| < 0,3.
- Nie stroić zasad portfela pod OOS — ustawić z góry (jak w przykładzie) i oceniać forwardem.

## Zasięg (D-076) — prognoza zmienności zamiast kierunku

- Zakładka pokazuje prognozę zasięgu 1/3/5 dni i poziomy wybicia z ściśnięcia (TP = 3 × SL). Najpierw backtest `zasieg_wybicie.py` (tp 2/3/4) — dopiero wynik mówi, czy reguła zarabia.
- Następne kroki, jeśli prognoza na prawdziwych danych okaże się wyraźnie lepsza od naiwnej: prognoza zasięgu jako filtr dla innych strategii (np. `ksiega_v2` tylko przy „spokojniej niż zwykle”), stawka odwrotnie do prognozy (`VOL_TARGET` z prognozy zamiast z przeszłości), wybicia z ściśnięcia na D1 (20 lat historii zamiast 2).

## Czego NIE robić (świadomie)

- Nie wracać do FOREST (usunięty w D-071) ani nie rozbudowywać `ia5 search` na H1 — rzetelnie pokazały brak przewagi; kolejne przebiegi na tym samym OOS to już dopasowanie.
- Nie stroić RSI 2 / Powrotu pod OOS (otwarty 2×). Ich jedynym uczciwym testem jest forward od zamrożenia.
- Nie dokładać par spoza tabeli bez potrzeby — więcej par to więcej prób, nie więcej przewagi.
- Nie przechodzić na M15/M5 — koszt względem ruchu rośnie, Yahoo nie ma tej historii.

## Architektura — co jest gotowe na rozwój

| Potrzeba | Gdzie się podpina | Koszt |
|---|---|---|
| Nowy interwał (np. H4, W1) | `TIMEFRAMES` w `sandbox.py`, dane `*_ready` z kolumną `close_ts`, `ready.build_*` | mały — silnik liczy na dowolnej siatce świec z czasem zamknięcia |
| Wykonanie na innym interwale niż sygnał | `engine.find_entries` (mapowanie świecy sygnału na świecę wejścia) | średni |
| Swapy w modelu | `engine.run` po `pips_net` (jest już `nights`) | mały + decyzja O5 |
| Nowe wyjście | `Exit.kind` + `simulate` + walidacja w `read_settings` | mały (wzór: `level`, D-057) |
| Przeszukiwanie na D1 | `search.py` — wejście z `d1_ready` zamiast `h1_ready` | średni |
| Realne konto / broker API | **poza zakresem** — maile inwestora wystarczą do ręcznego handlu; API brokera to nowa usługa (G6) | duży |
