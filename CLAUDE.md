# IA5 — instrukcja projektu i żelazne zasady

> **Plik nadrzędny.** Każda sesja pracy (Claude albo człowiek) zaczyna się od przeczytania tego pliku, `docs/STATUS.md` i `docs/DECISIONS.md`.
> Żelazne zasady (sekcja 1) zmienia wyłącznie Michał — wyraźnie, w rozmowie — i każda zmiana ma wpis w `docs/DECISIONS.md`.

Wersja 0.50 · 2026-11-11 · Status: E0–E5 zbudowane (kod); uruchomienie na Macu w toku; `ia5 search` (D-044); zakładka Inwestorzy (D-045); eksperyment FOREST (D-048, v2: D-049); świece dzienne D1 (D-053); silnik 0.10.0: noce, obsunięcie z MAE, uczciwy forward, wyjście „level” (D-054–D-057); silnik 0.11.0: strategie na D1 i tło D1 dla H1 (D-058); przegląd D1 bez fałszywego alarmu o OHLC Yahoo (D-059); samonaprawa danych i prosty „Stan systemu”, silnik 0.12.0 (D-060); silnik 0.13.0: wyjście bez limitu czasu — wyjątek od B7 (D-061); czas trwania transakcji i status „otwarta/zamknięta” w raporcie i tabeli transakcji (D-062) — `docs/STATUS.md`

---

## 0. Cel

IA5 to laboratorium do **szukania i weryfikowania** strategii FX na świecach godzinowych (H1) i dziennych (D1, cała historia Yahoo — D-058).
Dashboard ma odpowiadać na dwa pytania naraz: *ile strategia by zarobiła* i *czy to nie przypadek*.

Zakres teraz: system świec + program na Macu (`ia5`) + dashboard (zakładki **Strategie**, **Stats**, **Inwestorzy**, **FOREST**).
Zakładka **Inwestorzy** (D-045): wirtualni inwestorzy — paper trading wybranymi strategiami od chwili dodania, na żywych świecach Yahoo.
Zakładka **FOREST** (D-048, v2: D-049): demokratyczny eksperyment — do 1000 reguł mówi tylko wtedy, gdy ma co powiedzieć, Manager wchodzi przy szerokiej zgodzie, a las odświeża się co 4 tygodnie.

---

## 1. ŻELAZNE ZASADY

### Dane
- **D1.** Czas zawsze w UTC. Znacznik świecy = czas jej **otwarcia** (epoch, sekundy). Świeca `13:00` zamyka się o `14:00:00`.
- **D2.** Zapisujemy wyłącznie świece zamknięte: `ts + 3600 ≤ teraz − 60 s`. Świeca w trakcie nigdy nie trafia do bazy.
- **D3.** Zapis jest idempotentny (upsert po `ts`): ponowne uruchomienie nie tworzy duplikatów. **Nigdy `arrayUnion` dla cen** — usuwa powtarzające się wartości i po cichu psuje dane.
- **D4.** Dane surowe są niezmienne. Czyszczenie (weekendowe świece, odrzucone błędy) to osobna, jawna i wersjonowana warstwa.
- **D5.** Każda świeca przechodzi kontrolę jakości (kalendarz sesji bez weekendów i świąt 24/25.12 i 31.12/1.01 — D-028): `high ≥ max(open, close)`, `low ≤ min(open, close)`, ceny > 0, `ts % 3600 == 0`, brak luk w sesji (tydzień FX: niedziela ~21/22:00 → piątek ~21/22:00 UTC, zależnie od czasu letniego w USA), test krzyżowy par (EUR/JPY ≈ EUR/USD × USD/JPY; EUR/GBP ≈ EUR/USD ÷ GBP/USD). Naruszenie = flaga w statusie. Od D-060 system **sam naprawia** to, co da się naprawić (samonaprawa Apps Script co 6 h, uzupełnianie średnią na Macu), a flagi są sprawdzane na danych — naprawione znikają; każda naprawa jest policzona i widoczna w „Szczegółach” Stats.
- **D6.** Każdy wynik backtestu zapisuje hash danych, hash kodu strategii i `ENGINE_VERSION`. Wynik bez tych trzech pól nie istnieje.
- **D7.** **Jedno źródło cen: Yahoo** (Apps Script → Firestore → kopia na Macu) — do backtestów, forward testów, skanera i monitoringu (D-039). Innych źródeł nie używamy ani nie doklejamy; dane z `research/` służą tylko do szukania hipotez, nigdy do liczenia wyników. Dwie serie: **świece H1** — historia ok. 730 dni wstecz (tyle udostępnia Yahoo), rośnie z każdą godziną; **świece dzienne D1** (D-053) — cała historia, jaką Yahoo ma (dla par FX od ok. 2003), rośnie o każdy dzień. Silnik i inwestorzy liczą na H1 albo — gdy strategia ustawi `TIMEFRAME = "D1"` — na D1; strategia H1 może też czytać zamknięte świece dzienne jako tło (`ind.d1`, `ind.d1_to_h1`) (D-058). Skaner, `ia5 search` i las liczą tylko na H1. **Lokalnie na Macu tylko świece Yahoo** (`data/yahoo/` H1 i `data/yahoo_d1/` D1 — po 8 par) i dane do liczenia zbudowane z nich (`data/h1_ready/`, `data/d1_ready/`); wszystko inne w `~/.ia5/data` `ia5 start` usuwa przy każdym starcie i synchronizacji, a silnik odmawia liczenia na danych, których opis nie mówi „yahoo” (D-041).
- **D7a.** Świeca D1 (D-053): znacznik = czas otwarcia = **północ dnia w strefie Yahoo** (dla par FX `Europe/London`: zimą 00:00 UTC, latem 23:00 UTC dnia poprzedniego). Zapisujemy tylko dni zamknięte (w tej strefie zaczął się już następny dzień, + 60 s). Wpis nie o północy, zły OHLC, cena ≤ 0 = flaga, nigdy cicha naprawa (D5). Oczekiwane dni: poniedziałek–piątek bez 25.12 i 1.01; luki, płaskie świece i świece weekendowe w starej historii Yahoo są pokazywane w kontroli. **Do liczenia** (D-058, `daily.clean_d1` → `data/d1_ready/`): świeca łamiąca D5 odrzucona; weekend/święto i świeca płaska (O=H=L=C) odrzucone; 1–2 brakujące dni robocze — nic; ≥ 3 — przerwa w danych (`gap_before`, B12); bez uzupełniania; `close_ts` = północ następnego dnia w Londynie (czas zamknięcia świecy).
- **D8.** Backtest liczy na kopii świec Yahoo po **warstwie czyszczenia** (`ia5/clean.py`, dane w `data/h1_ready/`, wersja w raporcie): świeca łamiąca D5 jest odrzucana; świeca poza sesją jest odrzucana, gdy to sobota/święto albo świeca płaska (Yahoo powtarza wtedy starą cenę); brak **≤ 3 godzin** przy weekendzie/święcie to **granica tygodnia** (Yahoo zaczyna i kończy tydzień inaczej niż kalendarz) — nic; **każdy inny brak → uzupełniony liniowo** od zamknięcia przed nim do otwarcia po nim, znacznik `filled` (D-060); brak > 3 h ma dodatkowo znacznik **przerwy w danych** (`gap_before`), także gdy brakuje we wszystkich parach naraz — transakcje przez nią są anulowane (B12). Liczymy wszystkie pary z `COMPUTE_PAIRS` (8); para z mniej niż ~4 tygodniami świec jest pomijana. Surowa kopia (`data/yahoo/`) zostaje nietknięta; liczby odrzuconych, uzupełnionych i przerw są w raporcie.

### Backtest (model wykonania)
- **B1.** Sygnał liczony na zamknięciu świecy `t`, wejście na **open świecy `t+1`**. Nigdy po cenie, której w danej chwili nie dało się znać.
- **B2.** Strategia widzi tylko przeszłość. Przed liczeniem każda strategia przechodzi **detektor look-ahead** (sekcja 9). Niezaliczony = status `błąd: look-ahead`, bez liczenia.
- **B3.** Sygnały i poziomy TP/SL liczone na cenach świec Yahoo. Spread z tabeli (sekcja 2) odejmowany **jednorazowo** od każdej transakcji, w pipsach. Pips = `0,0001`; dla par z JPY = `0,01`. Test wrażliwości: spread × 1,5 i × 2 (sekcja 9).
- **B4.** Dźwignia **30:1** — zawsze (D-024). Wielkość pozycji = X% kapitału jako depozyt, nominał = 30 × X% kapitału. Domyślnie zawsze liczymy **X ∈ {5, 10, 15, 20, 30}%**; strategia może podać własne wartości (`SIZING`). Suma depozytów otwartych pozycji ≤ 100% kapitału, czyli łącznie nigdy ponad 30:1. Sygnał bez wolnego depozytu jest pomijany i liczony w raporcie. Szczegóły: 8.5.
- **B5.** Gdy w jednej świecy H1 mieszczą się i TP, i SL — kolejności nie znamy (Yahoo nie daje danych wewnątrz świecy), więc zawsze **SL** (pesymistycznie) i transakcja dostaje flagę `ambiguous`. Wynik z > 2% takich transakcji dostaje ostrzeżenie.
- **B6.** Luka cenowa: open za poziomem SL → wyjście po open (gorzej). Open za poziomem TP → wyjście po poziomie TP (bez zysku z luki).
- **B7.** Każdy wariant wyjścia ma SL albo limit czasu. Żadnych pozycji bez końca. **Wyjątek na wyraźne życzenie Michała (D-061):** strategia może zadeklarować wyjście `level` z `cap = 0` (bez limitu czasu) — pozycja trwa do TP ze strategii; jeśli do końca danych nie zamknęła się, jest „otwarta” i wyceniona po ostatnim close, a jej wynik niezrealizowany wchodzi do wszystkich statystyk (nigdy nie jest pomijany). Bez tej deklaracji B7 obowiązuje bez zmian.
- **B8.** Jedna pozycja na parę na wariant. Sygnał przy otwartej pozycji w tej parze jest pomijany (licznik pominiętych w raporcie). Wyjątek na życzenie Michała: strategia ustawia `PYRAMID = k` — do k pozycji naraz w parze, tylko w jednym kierunku; |sygnał| = waga depozytu (D-034). Strategia może też ustawić `MAX_PAIRS = k` — najwyżej k par z otwartymi pozycjami naraz; przy równoczesnych sygnałach wygrywa para wyżej w `PAIR_RANK` (ranking tylko z IS) (D-050).
- **B9.** Wskaźniki tylko z modułu `ia5.indicators`, zweryfikowanego testami zgodności z TA-Lib. Strategie nie piszą własnych RSI/ATR.
- **B10.** Zmiana logiki silnika = podbicie `ENGINE_VERSION`. Wyniki starszej wersji dashboard oznacza jako nieaktualne.
- **B11.** Handlujemy tylko **07:00–17:00 czasu polskiego** (`Europe/Warsaw`, z czasem letnim; zimą 06–16 UTC, latem 05–15 UTC) — wtedy spready są najniższe (D-028). Wejście wyłącznie na open świecy otwartej o 07:00…16:00 czasu polskiego; sygnały poza oknem są pomijane i liczone w raporcie. **Wyjście na dowolnej świecy** — według wariantu wyjścia, także w nocy i po weekendzie; bez limitu 23:00 (D-032 zastępuje D-030). Benchmark losowych wejść (W3) losuje w tym samym oknie. Strategia może wyłączyć okno (`HOURS = False`) albo podać własne (`HOURS = (od, do)`) — tylko na wyraźne życzenie Michała (D-034). Strategia na świecach dziennych (`TIMEFRAME = "D1"`) wchodzi na open dnia — okno jej nie dotyczy (D-058).
- **B12.** Transakcja nachodząca na **przerwę w danych** (D8) (od świecy wejścia do świecy wyjścia, także przerwa między sygnałem a wejściem) albo mająca świecę sygnału, wejścia lub wyjścia **uzupełnioną** jest **anulowana** — jakby jej nie było; liczby anulowanych (osobno) w raporcie. **Weekend, święto i granica tygodnia nie są przerwą:** po ostatniej piątkowej świecy następna jest pierwsza niedzielna/poniedziałkowa. Benchmark losowy anuluje tak samo (D-031, D-032, D-039).

### Walidacja (bez niej wynik to anegdota)
- **W1.** Ostatnie **25%** historii to out-of-sample (OOS). Ranking i wybór wariantów tylko na in-sample (IS). OOS pokazujemy obok, nigdy nie służy do wyboru.
- **W2.** Raport zawsze podaje **liczbę przetestowanych wariantów** i Deflated Sharpe Ratio. Przy setkach wariantów najlepszy jest w dużej mierze szczęściarzem.
- **W3.** Każda strategia jest porównana z **benchmarkiem losowych wejść** (te same pary, ta sama liczba transakcji, te same zasady wyjścia, ≥ 1000 losowań) → percentyl.
- **W4.** Zatwierdzoną strategię można **zamrozić** (hash kodu + parametrów + data + **wariant**). Od tej chwili system sam liczy jej wyniki forward na nowych świecach: walidacja i werdykt dotyczą **zamrożonego wariantu** (nie bieżącego szczytu rankingu), a blok `forward` podaje wynik od daty zamrożenia wobec oczekiwania sprzed niej (liczba transakcji, średnia, t, bootstrap, z) — D-056.

### Bezpieczeństwo
- **S1.** Kod strategii wpisany na stronie wykonuje się na Macu. Dlatego: zapis strategii tylko po zalogowaniu (Firebase Auth, Google) i tylko dla UID właściciela (reguły Firestore), a runner dodatkowo sprawdza `createdBy == OWNER_UID`.
- **S2.** Kod strategii działa w osobnym procesie, z limitem czasu i pamięci, z czystymi zmiennymi środowiskowymi (bez dostępu do kluczy).
- **S3.** Żadnych sekretów w repo. Klucz service account leży w `~/.ia5/`, `.gitignore` od pierwszego commita. Konfiguracja webowa Firebase jest publiczna z natury — chronią ją reguły Firestore i ograniczenie klucza API do domeny strony.

### Budżet zasobów (darmowy plan Firebase: 50 000 odczytów i 20 000 zapisów dziennie)
- **Z1.** Świece w Firestore grupowane: **1 dokument = 1 para × 1 miesiąc**. Nigdy 1 świeca = 1 dokument (sam backfill ~100 tys. świec zjadłby 5 dni limitu zapisów); świece D1: **1 dokument = 1 para × 1 rok** (D-053).
- **Z2.** Dashboard nie czyta świec ani wyników z Firestore — czyta je z gałęzi `data` na GitHub. Z Firestore czyta tylko `meta/status`, `runner/heartbeat`, listę `strategies` i listę `investors` (D-045, zgoda Michała z 2026-11-03) (nasłuch `onSnapshot`, bez odpytywania w pętli).
- **Z3.** Liczniki (np. liczba świec) są przechowywane w `meta/status`, nigdy liczone zapytaniem.
- **Z4.** Każda nowa funkcja, która czyta lub zapisuje Firestore, ma w commicie oszacowanie dziennego zużycia.

### Strategie (K) — gdy Michał mówi „zrób mi strategię …”
- **K1.** Claude postępuje według procedury z `docs/STRATEGIE.md` (sekcja 1): interpretacje → hipoteza → `PARAMS` (≤ ~12 kombinacji) → kod według kontraktu → **kontrola `python scripts/check_strategy.py plik.py` z wynikiem OK** → odpowiedź z jednym blokiem kodu gotowym do wklejenia w dashboard.
- **K2.** Strategia definiuje wyłącznie wejścia (`signals`). Wyjścia, spread, dźwignię i wielkość pozycji liczy silnik; własne `EXITS` / `SIZING` tylko na wyraźne życzenie.
- **K3.** Claude nie podaje przewidywanych wyników strategii. Wyniki liczy Mac; ocenę robi się na raporcie według sekcji 9.

### FOREST (F) — eksperyment demokratyczny (D-048, v2: D-049; zgoda Michała z 2026-11-03)
- **F1. Inwestor** = reguła lustrzana: 1–3 warunki rynku + horyzont. Ta sama logika działa na long i short (warunek x ≥ e dla long to x ≤ −e dla short), więc jednostronny dryf pary nie udaje przewagi. Gdy warunki nie są spełnione, inwestor milczy. Jedna reguła na 8 par. Cechy tylko z przeszłości (`forest_rules.py`, wskaźniki z `ia5.indicators`).
- **F2. Pula i las:** 150 tys. reguł (nasiono, progi z pierwszych 39 tygodni) jest stała. Do lasu wchodzi reguła z zyskiem po spreadzie (t tygodniowe ≥ 2,5), ≥ 30 oddzielnymi zdarzeniami, dodatnia w ≥ 3 z 4 bloków czasu, działająca w obie strony (BUY 25–75%), |korelacja głosów| ≤ 0,6, najwyżej 1000 reguł.
- **F3. Nauka:** pierwsze 39 tygodni to tylko nauka; potem co 4 tygodnie las jest wybierany od nowa na wszystkich zamkniętych danych. Każda decyzja używa lasu wybranego wcześniej niż ona sama. Test: zmiana przyszłych cen nie zmienia żadnej wcześniejszej decyzji ani lasu.
- **F4. Manager:** kierunek = większość. Wejście tylko przy ≥ 5 głosach i ≥ 90% zgody, gdy para jest wolna; inaczej zapisuje powód. Horyzont = mediana obozu zwycięzców (24 albo 48 świec). Wykonanie jak silnik: B1, B3, B4, B8, B11, B12; wyjście na zamknięciu t+h, bez SL (B7: limit czasu). Test: każda transakcja = `engine.simulate` co do pipsa.
- **F5. Kontrola:** druga księga bierze każdą większość bez progów. Raport zawsze pokazuje całą tabelę progów, a nie tylko wybrany próg.
- **F6. Odcinki:** HISTORIA = świece do 2026-05-03, na nich ustalono zasady. TEST = od tej daty do budowy lasu. LIVE = później. Progi i horyzonty nie są dobierane pod wynik TEST ani LIVE; zmiana = nowa wersja i wpis w `DECISIONS.md`.
- **F7. Dziennik:** każda decyzja z co najmniej jednym głosem zapisuje kto i jak głosował, zgodę, kierunek, horyzont, powód decyzji, wynik na obu horyzontach. Rozliczonych wierszy się nie zmienia.
- **F8. Liczy tylko Mac, przy `ia5 start`.** Stan leży na dysku; po przerwie świece są nadrabiane po kolei, wynik jest ten sam (test). Firestore: 0 odczytów i zapisów.
- **F9. Ocena:** zawsze obok Kontroli i danych bez przewagi (wspólny losowy znak dla par na blok 24 h). Raport liczy też noce: model silnika ich nie uwzględnia (O5), a pozycja trwa 2–3 noce. Rozstrzyga LIVE. Zmiana logiki = podbicie `FOREST_VERSION`.

### Praca w repo (Claude)
- **G1.** Start sesji: `git pull`, przeczytaj ten plik, `docs/STATUS.md`, `docs/DECISIONS.md`.
- **G2.** Małe commity, każdy działający. **Claude sam robi push** do `origin` po każdym ukończonym kroku, bez pytania.
- **G3.** Przed pushem: testy (`pytest`) zielone, lint czysty. Czerwone testy = brak pusha.
- **G4.** Nigdy `push --force` na `main`. Nigdy nie usuwać danych ani historii danych bez zgody Michała.
- **G5.** Koniec sesji: aktualizacja `docs/STATUS.md` (zrobione / następne / znane problemy). Każda decyzja architektoniczna → wpis w `docs/DECISIONS.md` (data, decyzja, powód, odrzucone alternatywy).
- **G6.** Bez rozszerzania zakresu na własną rękę. Nowa biblioteka lub usługa spoza sekcji 10.7 i 12 → najpierw wpis w `DECISIONS.md`.
- **G7.** Instrukcja niejasna albo sprzeczna z tym plikiem → pytać, nie zgadywać.

---

## 2. Parametry rynku

| Para | Ticker Yahoo | Pips | Spread (pips) | Waluta wyniku |
|---|---|---|---|---|
| EUR/USD | `EURUSD=X` | 0,0001 | 0,9 | USD |
| USD/JPY | `JPY=X` | 0,01 | 1,4 | JPY |
| GBP/USD | `GBPUSD=X` | 0,0001 | 1,5 | USD |
| EUR/GBP | `EURGBP=X` | 0,0001 | 1,7 | GBP |
| AUD/USD | `AUDUSD=X` | 0,0001 | 1,7 | USD |
| USD/CHF | `CHF=X` | 0,0001 | 1,9 | CHF |
| USD/CAD | `CAD=X` | 0,0001 | 2,0 | CAD |
| EUR/JPY | `EURJPY=X` | 0,01 | 2,1 | JPY |

- Godziny handlu: wejścia **07:00–17:00** czasu polskiego, wyjście na dowolnej świecy (B11, D-028, D-032). Dźwignia **30:1** (B4, D-024). Waluta konta: **USD**. Kapitał startowy: **10 000 USD**.
- Wynik w walucie kwotowanej przeliczany na walutę konta po kursie z zamknięcia świecy wyjścia, z naszych własnych danych (JPY przez USD/JPY, GBP przez GBP/USD, CHF przez USD/CHF, CAD przez USD/CAD).
- Swap / rolowanie: domyślnie 0 (decyzja O5). Raport pokazuje, ile nocy przez 21:00 UTC trzymano pozycje, żeby było widać skalę pominiętego kosztu.

---

## 3. Architektura — 4 miejsca, każde z jedną rolą

```mermaid
flowchart LR
  Y[Yahoo Finance<br/>świece 1h] -->|co 1 min, tylko gdy brak nowej świecy| GAS[Google Apps Script<br/>+ arkusz: log]
  GAS -->|upsert zamkniętych świec<br/>+ meta/status| FS[(Firestore<br/>świece Yahoo)]
  FS -->|ia5 start: kopia świec co godzinę + kontrola| MAC[Mac: ia5<br/>kopia lokalna + silnik]
  MAC -->|heartbeat, status liczenia| FS
  FS -->|nasłuch: do_policzenia| MAC
  MAC -->|push: snapshot świec + wyniki| GHD[GitHub<br/>gałąź data]
  GHM[GitHub main<br/>kod] -->|Actions| PAGES[Dashboard<br/>GitHub Pages]
  PAGES -->|status, heartbeat, strategie| FS
  PAGES -->|nowa strategia| FS
  PAGES -->|świece i wyniki, URL z SHA| GHD
```

| Miejsce | Rola | Pisze do | Czyta z |
|---|---|---|---|
| Google Apps Script (+ arkusz) | Pobiera świece H1 i D1, prowadzi log uruchomień | Firestore `candles/*`, `candles_d1/*`, `meta/status`; arkusz `log` | Yahoo |
| Firestore | Baza świec Yahoo (jedyne źródło cen), status, heartbeat, kolejka strategii | — | — |
| Mac (`ia5`) | Kopia świec, kontrola jakości, czyszczenie, liczenie, publikacja | Firestore `runner/heartbeat`, `strategies/*`; GitHub gałąź `data` | Firestore |
| GitHub | `main`: kod + strona (Pages). `data`: zimna kopia świec i wyniki | — | — |
| Dashboard | Podgląd i dodawanie strategii | Firestore `strategies/*` | Firestore (3 małe rzeczy), GitHub `data` |

### Przepływ

1. **Apps Script — co minutę (D-033), nie co godzinę.** Najpierw sprawdza w Script Properties, czy oczekiwana nowa świeca jest już zapisana. Jeśli tak — kończy bez żadnego zapytania. Jeśli nie — pyta Yahoo o ostatnie dni (interwał 1h), zapisuje zamknięte świece (upsert), aktualizuje `meta/status`.
   *Dlaczego:* wyzwalacz godzinowy Apps Script odpala się w dowolnej minucie godziny, więc pomiar „ile sekund zajęło pobranie świecy" byłby szumem rzędu 0–60 min.
   Ten sam wyzwalacz po północy w Londynie dopisuje zamkniętą świecę dzienną każdej pary (D-053); gdy jej brak — ponawia co 15 min, inaczej kończy bez zapytań.
2. **Mac — jeden proces `ia5 start` (D-039).** Na starcie i co godzinę (5 min po pełnej godzinie): kopia świec Yahoo z Firestore → kontrola aktualności i jakości (D5, trójkąty) → dane do liczenia po warstwie czyszczenia (`data/h1_ready/`, D8) → mapa pokrycia → push świec i mapy na gałąź `data` (tylko gdy się zmieniły) i SHA w `meta/status.dataSha` → przegląd zdrowia. Między synchronizacjami nasłuchuje strategii do policzenia.
3. **Dashboard.** Status z `meta/status` i `runner/heartbeat`. Świece i wyniki z gałęzi `data` przez `raw.githubusercontent.com/miszyszka/IA5/<SHA>/...` — adres z konkretnym SHA, więc bez problemu z cache.
4. **Nowa strategia.** Dashboard zapisuje `strategies/{id}` ze statusem `do_policzenia` → Mac dostaje to przez nasłuch → `liczy_sie` + postęp → wyniki na gałąź `data` → `policzona` + SHA commita.

### Pomiar latencji (to, co widać na dashboardzie)

`latencja_s = czas_zapisu_do_Firestore − (ts_otwarcia + 3600)`

To uczciwa liczba od końca do końca: obejmuje też opóźnienie, z jakim Yahoo publikuje świecę. Dashboard pokazuje ostatnią wartość, medianę z 24 h i mini-wykres.

---

## 4. Model danych

### Firestore

```
candles/{PARA}_{RRRR-MM}            np. candles/EURUSD_2026-10
  pair: "EURUSD", month: "2026-10"
  bars: { "1793016000": [o, h, l, c], ... }      # klucz = ts otwarcia
  updatedAt

meta/status
  lastRun: { startedAt, finishedAt, ok, error }
  daily:   { "2026-10-26": { EURUSD: 19, ... }, ... }   # świece wg dnia, 60 dni (pisze Apps Script; strona od D-040 korzysta z kalendarza w coverage.json)
  recent:  { start, pairs: { EURUSD: "111l1.f…" } }       # audyt świeca po świecy, 3 tygodnie: 1 jest, l spóźniona, f flaga, . brak (D-027)
  pairs:   { EURUSD: { lastTs, latencySec, count, flags[] }, ... }
  totalBars, latency24h[], dataSha
  health:  { at, state, summary, facts[], checks: [{ id, name, state, text, detail[], fix }] }   # przegląd zdrowia z Maca (D-023)
  d1:      { tz, totalBars, lastRun: { mode, at, ok, error }, pairs: { EURUSD: { firstDay, lastTs, lastDay, count, flags[] } } }   # D-053

runner/heartbeat
  lastSeen, state: idle|syncing|computing|offline,
  job: { id, progress, eta }, version, host

strategies/{id}
  name, hypothesis, code, status, createdAt, createdBy,
  engineVersion, frozenAt?, result?: { sha, path, summary }, error?

candles_d1/{PARA}_{RRRR}            # D-053: świece dzienne, 1 dokument = 1 para × 1 rok (rok wg dnia w strefie tz)
  pair, year, tz: "Europe/London", bars: { "<ts północy>": [o, h, l, c], ... }, updatedAt

investors/{id}                       # D-045: wirtualny inwestor (paper trading); ustawienia stałe — tylko usunięcie
  name, capital, pct, status: aktywny|do_usuniecia, createdAt (= start), createdBy,
  strategies: [{ strategyId, name, code, variantId, variantLabel }]   # kod i wariant zapisane w chwili dodania
  emailAlerts?: bool                 # D-051: jedyne pole, które można zmienić po dodaniu
```

- Zapis świec: REST `PATCH` z `updateMask` na pojedyncze klucze mapy `bars` → bez odczytu przed zapisem, idempotentnie.
- Wyłączyć indeksowanie pola `bars` (wyjątek indeksu pojedynczego pola) — taniej i z dala od limitu 40 000 wpisów indeksu na dokument.
- Rozmiar: ~744 świece × 4 liczby ≈ 30 KB na dokument (limit 1 MiB). Backfill: 8 par × ~25 miesięcy ≈ 200 zapisów.
- D1 (D-053): ~260 świec na dokument roczny; backfill 8 par × ~23 lata ≈ 200 zapisów, potem ok. 9 zapisów na dobę.
- Statusy strategii: `do_policzenia` → `liczy_sie` → `policzona` | `blad` ; opcjonalnie `zamrozona`.

### Reguły Firestore

Aktualne reguły: [`firestore.rules`](firestore.rules) (wklejane w Firebase → Firestore → Rules, z `<OWNER_UID>` zamienionym na UID Michała). Zasada: `meta/*` i `runner/*` czyta każdy (pasek statusu), piszą tylko Apps Script i Mac; `candles/*` i `candles_d1/*` czyta właściciel; `strategies/*` czyta i zmienia wyłącznie właściciel, tworzyć można tylko ze statusem `do_policzenia` albo `do_usuniecia`, zmieniać tylko pola `name, hypothesis, code, status, frozenAt, frozenVariant`.

Apps Script i Mac działają na uprawnieniach administracyjnych (OAuth właściciela / service account) i reguł nie potrzebują.

### GitHub, gałąź `data` (osobna, bez historii kodu)

```
candles/{PARA}/{RRRR}.parquet        # H1 z Yahoo (surowa kopia): ts, open, high, low, close; zmienia się tylko bieżący rok
candles/manifest.json                # hash, liczba świec, zakres per para
candles_d1/{PARA}.parquet            # D-053: świece dzienne Yahoo, cała historia pary (ts = północ w strefie tz)
candles_d1/manifest.json             # hash, liczba świec, pierwszy i ostatni dzień per para, tz
coverage/coverage.json               # mapa pokrycia (D-022): para × miesiąc, luki jako zakresy, kalendarz dzień po dniu (D-040) — bez cen
results/index.json                   # lista policzonych strategii (dashboard)
results/{strategyId}/                # ostatni run strategii (poprzedni jest w historii gita)
  manifest.json     # hash danych, hash kodu, ENGINE_VERSION, źródło, opis czyszczenia, zakres, liczba wariantów, pominięte
  variants.json     # metryki per wariant + zakres wierszy w trades.parquet (row_start, row_end)
  trades.parquet    # wszystkie transakcje wszystkich wariantów, posortowane po wariancie (dashboard czyta tylko potrzebny fragment)
  validation.json   # DSR, PBO, benchmark losowy, walk-forward, bootstrap, test spreadu, kapitał, werdykt
  candles/{PARA}.parquet  # wszystkie świece użyte w liczeniu (po czyszczeniu) — do wykresu
  report.md         # raport dla Claude (sekcja 10.6)
  strategy.py       # kod strategii
scans/{run}/                         # wyniki skanera hipotez (D-037)
searches/{run}/                      # głębokie poszukiwanie (D-044): search.md, candidates_is.csv, top_oos.csv, strategy.py
investors/index.json                 # lista inwestorów: kapitał teraz, wynik, liczba transakcji (D-045)
investors/{id}/state.json            # stan inwestora: kapitał (zrealizowany + wycena otwartych), krzywa, wszystkie transakcje
alerts/mail_sent.json, alerts/run.json # D-052: klucze wysłanych maili; ostatni przebieg inwestorów
forest/state.json                    # FOREST (D-049): decyzje teraz, księgi, progi, odświeżenia, wnioski
forest/investors.json                # inwestorzy: reguła, horyzont, w lesie od, czy aktywny
forest/journal/{RRRR-MM}.parquet     # dziennik decyzji z listą głosujących (zmienia się tylko bieżący miesiąc)
forest/report.md                     # raport dla Claude
```

### Lokalnie na Macu (poza repo)

```
~/.ia5/
  service-account.json                     # klucz Firebase (S3)
  smtp.json                                # D-051: {"user", "app_password", "to"} — Gmail, hasło aplikacji (S3); w Actions z sekretu
  config.json                              # {"owner_uid": "..."} — kto może zlecać liczenie (S1)
  source.json                              # {"source": "yahoo"} — znacznik po przejściu na jedno źródło (D-039)
  data/yahoo/{PARA}.parquet                # surowa kopia świec z Firestore — niezmieniana (D4); tylko 8 par z sekcji 2 (D-041)
  data/yahoo_d1/{PARA}.parquet             # D-053: surowa kopia świec dziennych z Firestore — niezmieniana (D4); 8 par
  data/h1_ready/{PARA}.parquet + .json     # po warstwie czyszczenia (filled, gap_before) + opis — wejście silnika (H1) i skanera (D8)
  data/d1_ready/{PARA}.parquet + .json     # D-058: D1 po warstwie czyszczenia (gap_before, close_ts) — wejście silnika przy TIMEFRAME = "D1" i tło D1
  data-repo/                               # lokalny klon gałęzi data
  results/{id}/{run}/  scans/{run}/        # wyniki liczenia i skanów (to samo trafia na gałąź data)
  searches/{run}/                          # głębokie poszukiwanie (D-044); all_is.parquet tylko lokalnie
  oos_ledger.json                          # dziennik otwarć OOS przez poszukiwanie i las (D-044, D-048)
  forest/current/                          # FOREST: las z odświeżeniami, dziennik, stan (D-049); forest/archive/{id}/ = poprzednie lasy
  forest/public/                           # to, co idzie na gałąź data
```

---

## 5. Google Apps Script

- Kod w repo `apps_script/`, synchronizowany narzędziem `clasp`. Nie edytujemy tylko w przeglądarce.
- Funkcje:
  - `backfill()` — jednorazowo, i gdy przegląd zdrowia pokaże przerwy w danych. Yahoo udostępnia świece 1h tylko z ostatnich **730 dni** — to cała dostępna historia; dalej rośnie o każdą nową godzinę (D7). Ponowny backfill uzupełnia dziury, jeśli Yahoo ma już te świece (upsert, ok. 200 zapisów). Zapis porcjami po miesiącu.
  - `tick()` — wyzwalacz **co 1 min** (D-033). Gdy wszystko jest — koniec bez zapytań. Tuż po pełnej godzinie czeka na zamknięcie świecy (D2) i ponawia brakujące pary co 15 s przez 10 min (najwyżej 100 s na uruchomienie); status zapisuje po każdej rundzie z nową świecą. Po wklejeniu nowej wersji uruchom raz `installTrigger()`.
  - Po komplecie świec `tick` uruchamia GitHub Actions (`dispatchLive_`, D-052; token w Script Properties `GITHUB_TOKEN`).
  - `backfillD1()` (D-053) — ręcznie, raz: cała historia świec dziennych Yahoo (`interval=1d`, od 1970 — Yahoo zwraca od pierwszej notowanej daty) → `candles_d1/*` i `meta/status.d1`. Ponowne uruchomienie = upsert. Dopiero po nim `tick` dopisuje kolejne dni (ostatnie 4 dni nadpisywane — Yahoo je koryguje; zapis tylko, gdy przybył dzień albo korekta > 0,5 pipsa).
  - `healthcheck()` — ręczna diagnostyka.
  - **Samonaprawa (D-060):** `tick` co 6 h (poza pierwszymi 10 min godziny) pobiera ponownie ostatnie 30 dni i nadpisuje świece — dziury i korekty Yahoo trafiają do bazy, flagi liczą się od nowa; ręcznie: `repair()`.
  - `removeOffGrid()` — ręcznie: usuwa z `candles/*` wpisy z czasem nie na pełnej godzinie (notowania Yahoo, nie świece; D-042). `tick` takich wpisów już nie zapisuje.
- Yahoo: nieoficjalny endpoint `v8/finance/chart`, `interval=1h`. Ponawianie z rosnącym odstępem, maks. 3 próby, nigdy pętla bez końca. Odpowiedź, która nie jest JSON-em → błąd w `meta/status`, nie awaria.
- Odrzucamy ostatnią, niezamkniętą świecę (D2). Nadpisujemy 3 ostatnie zamknięte (Yahoo czasem je koryguje). Korekta > 0,5 pipsa → flaga `revised`.
- Zapis do Firestore przez REST z tokenem `ScriptApp.getOAuthToken()` (zakres `datastore`).
- Arkusz: zakładka `log` — wiersz na uruchomienie (czas, para, nowe świece, latencja, błąd). Tania druga linia diagnostyki.
- Ryzyko: Yahoo nie ma oficjalnego API i potrafi zmienić lub przyciąć nieoficjalne zapytania; to jedyne źródło (D7), więc awaria Yahoo zatrzymuje dopływ nowych świec — historia na Macu i liczenie działają dalej, a przerwa jest oznaczona w danych (B12). Na danych 2024–2026 Yahoo miało 3 takie przerwy (26 h, 6 h, 66 h, wszystkie pary naraz). Plan B — wpis w `DECISIONS.md`, gdy będzie potrzebny.

---

## 6. Program na Macu (`ia5`)

- Python 3.12, menedżer `uv`. Instalacja: `uv tool install -e runner` → w terminalu działa komenda `ia5`.
- `ia5 start` — **jedyny proces** (D-039): najpierw weryfikuje aktualność danych, potem nasłuchuje strategii do policzenia.
  1. Pierwszy start po D-039: usuwa z `~/.ia5` dane Dukascopy i policzone na nich wyniki, z gałęzi `data` wyniki i skany policzone na Dukascopy (historia gita zostaje), a policzone strategie wysyła do ponownego liczenia na świecach Yahoo (zgoda Michała z 2026-10-31).
  2. Stan bazy (`meta/status`), kopia świec Yahoo z Firestore (pierwszy raz pełna, potem miesiące od ostatniej świecy kopii — po przerwie Maca kopia nie ma dziur). Kopia świec D1 (D-053): para doczytywana tylko, gdy `meta/status.d1` ma nowszą świecę lub inną liczbę świec niż kopia.
  3. Sprzątanie: w `~/.ia5/data` zostaje tylko `yahoo/`, `yahoo_d1/` (po 8 par), `h1_ready/` i `d1_ready/` (D-041, D-053, D-058). Kontrola aktualności (czy każda para ma ostatnią zamkniętą świecę sesji) i jakości (D5, trójkąty par).
  4. Dane do liczenia (`data/h1_ready/`, warstwa czyszczenia D8; `data/d1_ready/`, D7a/D-058) — przebudowa pary tylko, gdy zmieniły się jej świece.
  5. Mapa pokrycia (D-022) i push na gałąź `data` świec H1, świec D1 (`candles_d1/`) oraz `coverage/coverage.json` (każde tylko, jeśli coś się zmieniło); przegląd zdrowia (D-023) → `meta/status.health` (z kontrolą „Świece dzienne (D1)”).
  6. Heartbeat co 30 s do `runner/heartbeat`; `caffeinate -i`, żeby Mac nie usnął.
  7. Nasłuch `strategies` ze statusem `do_policzenia` / `do_usuniecia`; kolejka FIFO, jedna strategia na raz.
  8. Co godzinę (5 min po pełnej godzinie) kroki 2–5 od nowa; co 6 h ponowne liczenie zamrożonych strategii (forward test, W4).
  8a. **Inwestorzy (D-045, D-052):** liczy GitHub Actions (`ia5 live`), uruchamiane przez Apps Script po komplecie świec. Mac robi to tylko, gdy `alerts/run.json` z gałęzi `data` jest starszy niż 2 h: po każdej kopii świec i po każdej zmianie listy `investors` — przeliczenie wszystkich aktywnych inwestorów właściciela (`ia5/investors.py`) i publikacja `investors/` na gałęzi `data`; inwestorzy `do_usuniecia` znikają z gałęzi i z Firestore.
  8b. **FOREST (D-049):** po każdej kopii świec: brak lasu albo starsza wersja → budowa (kilka minut); jest las → nowe świece po kolei, co 4 tygodnie odświeżenie lasu, publikacja `forest/` na gałęzi `data`.
  9. `Ctrl+C` → heartbeat `offline`, czyste wyjście.
- `ia5 scan [--duzy] [--pary …]` — **skaner hipotez** (D-037): tysiące–miliony prostych reguł na wszystkich parach, FDR 5% w odkryciu (pierwsze 50%), potwierdzenie (50–75%), ostatnie 25% pominięte; wynik `~/.ia5/scans/{run}/` i gałąź `data` `scans/{run}/`. To hipotezy do zbudowania strategii, nie werdykt.
- `ia5 search [--rozmiar szybki|duzy|gigant] [--zero N] [--top K] [--bez-oos]` — **głębokie poszukiwanie** (D-044): 7 tys. / 0,71 mln / 3,1 mln konfiguracji (wyzwalacz × tryb × wyjście silnika × filtry), jedna konfiguracja = te same zasady na 8 parach. IS-A (FDR 5%) → IS-B (t ≥ 2) → ≥ 5/8 par → płaskowyż; K (domyślnie 20) wybranych **tylko po IS** otwartych raz na OOS i zapisanych w `oos_ledger.json`; `--zero N` = N przebiegów na danych bez przewagi (test szczęścia, liczony przed OOS). Ten sam model co silnik (test zgodności transakcji). Wynik `~/.ia5/searches/{run}/` + `strategy.py` (≤ 12 konfiguracji) do dashboardu.
- `ia5 forest build|krok|status [--zero N] [--nasiono S] [--lokalnie]` — ręczne sterowanie FOREST (D-049), przy wyłączonym `ia5 start`. Normalnie niepotrzebne: `ia5 start` robi to sam. `build` liczy las od nowa (poprzedni idzie do `forest/archive/`) i zapisuje wpis w dzienniku OOS.
- Pozostałe komendy (pomocnicze, na kopii lokalnej): `ia5 health` (opisowy raport zdrowia w terminalu + zapis na dashboard), `ia5 status`, `ia5 run <plik.py>` (liczenie lokalne, bez dashboardu; wyniki w `~/.ia5/results/{nazwa}/{run}/`), `ia5 check <plik.py>`.
- Dashboard pokazuje „połączony", gdy `teraz − lastSeen < 90 s`.

### Protokół dashboard ↔ Mac (jedyna droga komunikacji: Firestore `strategies/{id}` + gałąź `data`)

| Krok | Kto | Zapis | Odczyt |
|---|---|---|---|
| Nowa strategia | dashboard (zalogowany właściciel) | `strategies/{id}`: `name, hypothesis, code, status="do_policzenia", createdBy, createdAt` | Mac: nasłuch `status in [do_policzenia, do_usuniecia]` |
| Start liczenia | Mac | `status="liczy_sie"`; `runner/heartbeat.job = {id, name, progress, phase}` | dashboard: pasek postępu |
| Wynik | Mac | push `results/{id}/` + `results/index.json` na gałąź `data`; `status="policzona"`, `result={sha, path, run_id, verdict}` | dashboard: odświeża SHA gałęzi `data`, karta strategii |
| Błąd | Mac | `status="blad"`, `error` (kontrakt, look-ahead, wyjątek) | dashboard: komunikat + „Popraw kod” |
| Popraw / policz ponownie | dashboard | `code, hypothesis, status="do_policzenia"` (tworzy dokument, gdy strategia była tylko na gałęzi `data`) | Mac jak wyżej |
| Usunięcie | dashboard | `status="do_usuniecia"` — strategia znika z listy od razu | Mac: usuwa `results/{id}/` i wpis z indeksu, potem dokument |
| Zamrożenie | dashboard | `frozenAt, frozenVariant` | Mac: co 6 h przelicza zamrożony wariant z blokiem `forward` (D-056); karta: tabela forward + filtr „tylko forward” |

Reguły Firestore (`firestore.rules`) pozwalają na te zapisy wyłącznie właścicielowi (S1); Mac dodatkowo sprawdza `createdBy == owner_uid` z `~/.ia5/config.json`.

---

## 7. Kontrakt strategii (to wpisuję w okno dialogowe)

**Pełny przewodnik i reguła dla Claude: [`docs/STRATEGIE.md`](docs/STRATEGIE.md)** — kontrakt, lista funkcji `ind`, wzorce, pułapki look-ahead, procedura „zrób mi strategię”. Wzorce działające: `strategies/examples/` (sprawdzane w CI).

```python
HYPOTHESIS = """Dlaczego to działa — spisane PRZED liczeniem."""
PARAMS = {"rsi_level": [25, 30, 35], "slope_bars": [5, 20]}   # każda kombinacja = wariant wejścia

def signals(df, p, ind):          # df: H1 jednej pary, indeks UTC = czas otwarcia; p: jedna kombinacja PARAMS
    trend_up = ind.rising(ind.sma(df.close, 200), p["slope_bars"])   # „SMA200 rośnie”
    oversold = ind.cross_below(ind.rsi(df.close, 14), p["rsi_level"])  # zdarzenie, nie stan
    return (trend_up & oversold).astype("int8")                       # +1 long / −1 short / 0
```

Interwał (D-058): `TIMEFRAME = "D1"` → `df` to świece dzienne (cała historia Yahoo), wyjścia liczone w dniach. W strategii H1 tło dzienne: `d = ind.d1(df)` (zamknięte dni) i `ind.d1_to_h1(df, wartość_na_d1)` (przeniesienie na H1 bez look-ahead). Szczegóły: `docs/STRATEGIE.md`.

Egzekwowanie: `runner/ia5/sandbox.py` (osobny proces, dozwolone importy `numpy`, `pandas`, `math`), detektor look-ahead (cięcia danych + zaburzenie przyszłości, także tła D1), `ia5 check` / `scripts/check_strategy.py`, kontrola w edytorze dashboardu.

---

## 8. Silnik backtestu

### 8.1 Wejścia
Domyślnie open świecy `t+1`, tylko w oknie 07:00–17:00 czasu polskiego (B11). Przy `TIMEFRAME = "D1"` (D-058): open następnego dnia, bez okna; „świeca” we wszystkich wyjściach = dzień, czas wyjścia na zamknięciu = `close_ts`. Opcjonalne warianty: opóźnienie o k świec; potwierdzenie (następna świeca zamyka się w kierunku sygnału).

### 8.2 Domyślna siatka wyjść (~230 wariantów)
- **Czasowe:** wyjście po N świecach, N ∈ {1, 2, 3, 4, 6, 8, 12, 16, 24, 36, 48, 72, 96, 120}.
- **ATR:** ATR(n), n ∈ {5, 14}, liczony na świecach przed wejściem; TP ∈ {0,5; 0,75; 1; 1,5; 2; 3; 4} × ATR; SL ∈ {0,5; 1; 1,5; 2; 3} × ATR; limit czasu ∈ {24, 72, 120} świec.
- **Na życzenie strategii (`EXITS`):** `rsi_streak` — RSI14 przez N zamknięć z rzędu po złej stronie poziomu → wyjście na open następnej (D-034); `trail` — stop kroczący `trail`×ATR od najwyższego high poprzednich świec, ze stopem początkowym (D-035); `level` — **TP i SL jako ceny ze strategii** z funkcji `levels(df, p, ind)` liczonej na świecy sygnału (przechodzi detektor look-ahead jak sygnały; D-057). Limit czasu w `EXITS` do 480 świec (albo `cap = 0` tylko dla `level` — D-061).
- **Wskaźnikowe:** RSI(14) dochodzi do 50 (long ≥ 50, short ≤ 50); przecięcie SMA; sygnał przeciwny. Każde z SL ∈ {1, 2, 3} × ATR(14) i limitem 120 świec.

### 8.3 Liczenie
Wejścia liczone raz; wszystkie wyjścia na tych samych wejściach. numpy wektorowo + numba dla pętli wyjść. Cel: strategia na 8 parach liczy się w minutach, nie godzinach.

### 8.4 Zapis transakcji
Pips brutto, pips netto (− spread), R (względem SL; dla wyjść bez SL — względem 1 × ATR(14)), MAE, MFE, liczba świec, **noce** (przejścia przez 21:00 UTC, D-054), powód wyjścia, `ambiguous`, IS/OOS.

### 8.5 Portfel i kapitał
- Najpierw przewaga transakcji (pips, R) — niezależna od wielkości pozycji. Osobno symulacja kapitału — zależna od wielkości pozycji.
- Wielkość pozycji (B4): depozyt = X% bieżącego kapitału, nominał = 30 × depozyt, procent składany przy wejściu. Domyślnie liczymy wszystkie X ∈ {5, 10, 15, 20, 30}%; strategia może podać własną listę w `SIZING`.
- Limit: suma depozytów otwartych pozycji ≤ 100% kapitału. Przy X = 30% to najwyżej 3 pozycje naraz; czwarty sygnał jest pomijany i liczony. Dzięki temu łącznie nigdy ponad 30:1. Kapitał może spaść do zera lub poniżej (brak modelu stop-out brokera) — wtedy nowe wejścia są pomijane.
- Wynik w USD: zysk w walucie kwotowanej przeliczany po kursie z zamknięcia świecy wyjścia (sekcja 2).
- W karcie strategii wielkość pozycji to **przełącznik**, nie kolejne warianty w rankingu. Ranking, DSR i PBO liczymy na przewadze transakcji (R), żeby wielkość pozycji nie mnożyła liczby prób.
- Kapitał przeliczany także w przeglądarce, gdy wyłączasz pary w filtrach.
- Obok obsunięcia zrealizowanego (z zamknięć) liczymy **obsunięcie z otwartymi pozycjami**: kapitał pomniejszony o MAE wszystkich otwartych pozycji wobec szczytu — pesymistyczna granica, nigdy łagodniejsza (D-055). Ta sama logika w Pythonie i JS.

### 8.6 Metryki
Liczba transakcji, win rate, średni zysk i strata, profit factor, expectancy (pips, R, %), CAGR, maksymalne obsunięcie, czas pod wodą, Sharpe i Sortino (z dziennych zwrotów), Calmar, najdłuższa seria strat, ekspozycja (% czasu w rynku), t-stat średniej transakcji.
Rozbicia: para, rok, kierunek, sesja (Azja 00–07, Europa 07–13, USA 13–21 UTC), dzień tygodnia.

---

## 9. Walidacja — kto poza nami mówi, że wynik jest prawdziwy

| Co sprawdzamy | Niezależny sędzia | Kiedy |
|---|---|---|
| Wskaźniki | TA-Lib — zgodność do 1e-9 | CI, każdy push |
| Silnik | Ręcznie policzone „złote" scenariusze na syntetycznych świecach; testy własności (`hypothesis`), np. netto = brutto − spread zawsze | CI |
| Silnik vs inny silnik | `backtesting.py` na strategii referencyjnej (przecięcie SMA + wyjście po N świecach) — identyczna lista transakcji. Ręcznie: TradingView Strategy Tester | CI / raz na etap |
| Dane | Przegląd zdrowia (D-023): świece D1 (D-053, D-059: 8 par, świeżość, kopia = Firestore, czas o północy; złe OHLC Yahoo to informacja, ostrzeżenie dopiero przy dużym świeżym), wersja programu na Macu (D-046: liczy kodem z dysku i aktualnym z GitHub), świeżość Yahoo, kopia na Macu = Firestore, na Macu tylko dane Yahoo (D-041), trójkąty par godzina po godzinie na całej historii (przesunięcie czasu jednej pary daje ~11% godzin ponad próg), zamrożone notowania w sesji, kompletność i przerwy, poprawność świec | każda synchronizacja (co godzinę) |
| Look-ahead | Detektor: sygnały liczone na pełnych danych i na danych obciętych w losowych punktach muszą być identyczne do punktu cięcia | przed każdym liczeniem |
| Przeuczenie | OOS 25% (W1), walk-forward (okna roczne), Deflated Sharpe Ratio, PBO metodą CSCV (16 bloków), bootstrap 95% CI expectancy | każde liczenie |
| Przypadek | Benchmark losowych wejść, ≥ 1000 losowań → percentyl (W3) | każde liczenie |
| Stabilność | Heatmapa TP × SL — szukamy płaskowyżu, nie pojedynczego piku; wynik przy spreadzie × 1,5 i × 2; wynik przy koszcie nocy 0,5 / 1 pips (swap pominięty w modelu, O5 — D-054) | każde liczenie |
| Rzeczywistość | Forward test po zamrożeniu (W4): zamrożony wariant, wynik od zamrożenia wobec oczekiwania (D-056) | automatycznie, co 6 h |

**Werdykt w karcie** (progi ustalone z góry, do kalibracji w DECISIONS):
🟢 gdy jednocześnie: expectancy netto OOS > 0, percentyl benchmarku ≥ 95, PBO < 0,3, DSR ≥ 0,95, wynik dodatni przy spreadzie × 1,5.
🟡 gdy część warunków. 🔴 gdy OOS ≤ 0 albo percentyl < 80.
Przy jednym wariancie PBO „nie dotyczy” (nie liczy się ani za, ani przeciw), a DSR = PSR (D-043).

---

## 10. Dashboard

### 10.1 Stan systemu (zawsze widoczny, w nagłówku obok zakładek)
- **Dane** i **Mac** — dwa wskaźniki tuż obok siebie, każdy z kropką stanu (jedyne świecące elementy strony; przy działającym systemie kropka lekko „oddycha”).
  - Dane: działa / opóźnienie / stoi / rynek zamknięty / otwarcie tygodnia (weekend i pierwsze ≤ 3 h po nim to nie awaria, D-039); obok ostatnia świeca i odliczanie do następnej. Gdy wybije pełna godzina — **czerwony zegar** (ile par czeka, od pełnej godziny), aż wszystkie pary mają nową świecę (D-033). Progi w godzinach rynku: OPÓŹNIENIE gdy świecy brak > 20 min po zamknięciu, STOI gdy > 75 min.
  - Mac: połączony / sprawdza dane / liczy (nazwa, postęp %) / rozłączony (od kiedy).
- **Problemy** — liczba kontroli przeglądu zdrowia, które nie są OK (bursztyn: uwagi, czerwień: błąd); pojawia się tylko, gdy są (klik → Stats).
- **Pary** — jeden symboliczny kafelek („8 par” + kody walut), bez danych i bez rozwijania.
- Bez kafli KPI. Liczby (świece w bazie, latencja, flagi, pary) są w zakładce **Stats**.

### 10.2 Zakładki
**Strategie** | **Stats** | **Inwestorzy** (D-045) | **FOREST** (D-048).

**FOREST** (0 odczytów Firestore, wszystko z `forest/` na gałęzi `data`): stan lasu i jedno zdanie, jak to działa; **Teraz** (8 par: ilu głosuje, BUY, SELL, zgoda, decyzja i jej powód po ludzku, otwarta pozycja); **Co wiadomo** (wnioski liczone automatycznie); **Wynik** (kapitał Managera i Kontroli, tabela odcinków z wynikiem po nocach); **Dziennik** (klik = kto głosował, eksport CSV); **Czego się uczy** (odświeżenia: ile doszło, ile odpadło); **Co znaczy zgoda**; rozwijane **Szczegóły** (inwestorzy, cała tabela progów, dane bez przewagi, raport dla Claude).

**Inwestorzy** — wirtualne konta (paper trading). Dodawanie: nazwa, kapitał początkowy (USD), % kapitału jako depozyt na każde wejście, strategie wyłącznie z listy policzonych strategii, każda z wariantem wybranym przy dodaniu (domyślnie zamrożony albo #1 IS); kod i wariant zapisują się w tej wersji. Ustawień nie da się zmienić — tylko usunąć inwestora; wyjątek to przełącznik **Wysyłaj mail** (D-051, D-052: ostrzeżenie, sygnał, otwarcie, zamknięcie przez limit czasu; działa bez Maca). Na górze karty: „za x minut możliwy sygnał na instrumencie Y” z ceną zamknięcia, która go wywoła (próby hipotetycznych zamknięć do ±1 ATR14, nie zapisywane w danych). Model: te same zasady co silnik (B1–B12), sygnały tylko ze świec zamkniętych po dodaniu, wszystkie strategie na wspólnym kapitale (B4: suma depozytów ≤ 100%, nominał = 30 × depozyt), pozycja bez wyjścia = otwarta, wyceniana po ostatnim zamknięciu. Lista: wskaźnik stanu (INWESTOR DZIAŁA / URUCHAMIANIE / WSTRZYMANY — Mac rozłączony / OPÓŹNIONY / BŁĄD), kapitał teraz, wynik. Karta: stan, kapitał (zrealizowany + wycena otwartych), wykres kapitału z obsunięciem, strategie inwestora, sygnały czekające na wejście i chronologiczna lista wszystkich transakcji (także pominiętych z braku depozytu i anulowanych), eksport CSV. Wskaźnik stanu inwestora to kropka bez poświaty — poświata zostaje tylko w nagłówku (D-019).

**Stats** (`meta/status` + `runner/heartbeat` + `coverage/coverage.json` z gałęzi `data`, 0 dodatkowych odczytów Firestore): **Stan systemu** (D-023, uproszczony w D-060) — „✓ Wszystko działa” albo „Do zrobienia: …”, pod nim tylko rzeczy do zrobienia z podpowiedzią; pełna lista kontroli i trzy zdania o bazie w zwiniętych „Szczegółach”; co system naprawił sam, jest zielone; gdy przegląd jest starszy niż 2 h, strona mówi to wprost; świece w bazie i ostatnie pobranie, latencja (ostatnia, mediana 24 h, mini-wykres), kafelek przeglądu z listą wszystkich problemów (nazwa + zdanie);
**mapa pokrycia świec Yahoo** (D-022, D-033, D-039) z przełącznikiem: *Ostatnia doba* — 24 zamknięte świece + trwająca godzina (przerywana kratka), nad kolumną godzina otwarcia w czasie polskim; stany: jest / spóźniona > 20 min / z flagą / czeka (czerwony zegar od pełnej godziny do zapisu) / rynek zamknięty; przy każdej parze zegar albo czas ostatniego zapisu; na żywo z `meta/status.recent` i `pairs`; *Cała historia* — 8 par × miesiące od pierwszej świecy: kolor = jak duże dziury, luki rozdzielone na *dziury* (brak danych: ≤ 3 h uzupełniana do liczenia, dłuższa = przerwa, transakcje anulowane), *granicę tygodnia* i *bez ruchu ceny*; klik miesiąc → lista luk co do godziny ze skutkiem dla liczenia, klik para → wszystkie jej dziury; **kalendarz danych dzień po dniu** (D-040) — cała historia, miesiąc pod miesiącem (od najnowszego), 1 kratka = 1 dzień UTC: komplet / pojedyncze braki ≤ 3 h (uzupełnione) / przerwa w danych > 3 h / brak danych / bez sesji / dziś; wszystkie pary (najgorszy stan) albo jedna para; podsumowanie „dane od … do …”, klik w dzień → luki co do godziny; tabela par. Flagi Yahoo nie mają osobnej listy — widać je w audycie jako kafelki „z flagą”, a ich liczbę w przeglądzie zdrowia.

### 10.3 Lista strategii
Nazwa, status (do policzenia / liczy się x% / policzona / błąd / zamrożona), data, werdykt, kluczowe liczby najlepszego wariantu IS obok OOS.

### 10.4 Nowa strategia
Duże okno: nazwa, hipoteza, kod (pole tekstowe z czcionką o stałej szerokości, Tab = 4 spacje, Ctrl/⌘+Enter = wyślij). Kontrola kontraktu na żywo (`checkStrategyCode`) blokuje wysłanie przy błędzie. Szablon startowy. Zapis → status `do_policzenia`.

### 10.5 Karta strategii
- Nagłówek: werdykt, hipoteza, liczba wariantów, `ENGINE_VERSION`, zakres danych, hashe.
- **Panele zwijane** (D-046): klik w nagłówek panelu zwija/rozwija, „Zwiń wszystko / Rozwiń wszystko”; stan pamiętany w przeglądarce. Tak samo w karcie inwestora.
- **Filtry globalne karty:** pary (checkboxy), kierunek, okres, IS / OOS / całość, rodzina wyjść, sesja, wielkość pozycji (5 / 10 / 15 / 20 / 30% lub z `SIZING`).
- **Ranking wariantów:** tabela sortowalna + paski metryki (styl z inspiracji 3).
- **Heatmapa TP × SL** (rodzina ATR) i krzywa expectancy względem N (rodzina czasowa).
- **Kapitał od początku** dla wybranego wariantu: granica IS/OOS, data zamrożenia, obsunięcie pod spodem, pasmo benchmarku losowego (mediana i 5–95%).
- **Wykres świecowy ze wszystkimi transakcjami:** markery wejścia i wyjścia, linie TP/SL, kolor wg wyniku, przełączanie par; klik w tabeli transakcji → skok na wykresie.
- **Tabela transakcji** z filtrami i eksportem CSV; kolumny **dni** (czas trwania, dni kalendarzowe) i **status** (zamknięta / OTWARTA — nie zamknęła się do końca danych) — D-062.
- **Rozbicia:** para, rok, sesja, dzień tygodnia.
- **Walidacja:** DSR, PBO, percentyl benchmarku, przedział bootstrap, test spreadu, noce i koszt nocy (D-054), % `ambiguous`; dla zamrożonej — tabela forward testu (D-056).
- Przyciski: **Kopiuj raport dla Claude**, **Pobierz report.md**, **Zamroź strategię**, **Policz ponownie**.

### 10.6 Raport dla Claude (`report.md`)
Stała struktura: hipoteza → kod → dane (zakres, pary, koszty, model wykonania) → liczba wariantów → top 10 wariantów IS z ich wynikami OOS → stabilność (sąsiedzi najlepszego wariantu na siatce) → walidacja → rozbicia → **czas trwania transakcji i pozycje otwarte** (D-062: ile dni trwała każda transakcja, czy jest zamknięta czy OTWARTA na koniec danych, statystyki obu grup) → najgorsze obsunięcia → znane ograniczenia (źródło danych, brak swapów, pesymizm w niejednoznacznej świecy) → pytania do recenzenta.
Liczby w tabelach markdown, bez obrazków — tak, żeby model mógł je czytać.

### 10.7 Technologia
Statyczny HTML + moduły ES, bez kroku budowania (`web/`). Biblioteki w repo (`web/vendor/`, bez zależności od CDN): ECharts 5.5 (kapitał, heatmapy, krzywe), Lightweight Charts 4.2 (świece z transakcjami), hyparquet 1.31 (czytanie fragmentów Parquet zakresami HTTP — tylko wiersze wybranego wariantu). Firebase JS SDK 10.14 ładowany dynamicznie z gstatic — gdy zawiedzie, wyniki z GitHub nadal działają. Logika obliczeń w `web/js/metrics.js` testowana w Node (`tests/web`), kapitał zgodny z `runner/ia5/portfolio.py`. Wdrażanie przez GitHub Actions → Pages. Test w przeglądarce: parametry `?data=<url>&nofb=1`.

---

## 11. Design (D-019)

- Tło `#0A0E13`, panele `#0F141A`, uniesione elementy `#151B23`, obramowanie 1 px `#1C232D`. Zaokrąglenia: panele 8 px, kontrolki 6 px, wskaźniki stanu w pełni zaokrąglone.
- **Płasko:** bez gradientów i bez dekoracyjnych cieni — także na wykresach.
- **Jeden akcent** — pomarańczowy `#FF7A1A` — tylko dla tego, co *wybrane*: aktywna zakładka, główny przycisk, zaznaczony wiersz/filtr, linia kapitału.
- **Kolory stanu tylko jako stan:** zielony `#3DDC84` (działa, zysk), bursztyn `#F5A524` (opóźnienie, braki, flagi), czerwony `#FF4D4F` (stoi, błąd, strata), szary (rynek zamknięty, rozłączony). Żadnych innych kolorów (bez niebieskiego dla informacji).
- **Poświata tylko na kropkach stanu** w nagłówku — jedyna „żywa” rzecz na stronie, więc coś znaczy. Ruch („oddychanie”) tylko przy działającym systemie, wyłączony przy `prefers-reduced-motion`.
- Etykiety (DEMO, zamrożona, w kolejce) jako obrys, bez wypełnień; kolor tylko gdy niesie stan.
- Liczby: JetBrains Mono z cyframi tabelarycznymi. Tekst: Inter.
- **Zasada uczciwości wykresów:** dekoracja nigdy nie zmienia danych. Ceny i kapitał bez wygładzania krzywych. Zysk i strata zawsze ze znakiem, nie tylko kolorem.

---

## 12. Struktura repo

```
IA5/
├─ CLAUDE.md                 # ten plik
├─ docs/
│  ├─ STATUS.md              # stan prac, aktualizowany co sesję
│  ├─ DECISIONS.md           # dziennik decyzji
│  ├─ STRATEGIE.md           # jak pisać strategie + reguła „zrób mi strategię” (K1–K3)
│  └─ SETUP.md               # kroki do kliknięcia
├─ web/                      # dashboard (GitHub Pages): index.html, css/, js/ (app, list, card, charts, editor,
│                            #   status, stats, session, coverage, health, data, fb, metrics, util, config, investors, forest), vendor/
├─ scripts/                  # check_strategy.py (kontrola kodu bez danych Michała), demo.py
├─ research/                 # badania hipotez na niezależnych danych, przed strategią (D-036)
├─ apps_script/              # Code.gs + appsscript.json (clasp)
├─ runner/                   # program na Maca
│  ├─ pyproject.toml
│  └─ ia5/  cli.py  config.py  session.py  store.py
│           quality.py  clean.py  ready.py  coverage.py  health.py  cloud.py  publish.py   # dane (E2)
           daily.py                                                      # świece dzienne D1: kalendarz, kontrola (D-053), warstwa czyszczenia do liczenia (D-058)
│           indicators.py  engine.py  sandbox.py  backtest.py  report.py # silnik (E3)
│           validate.py  portfolio.py  check.py                           # walidacja, kapitał, kontrola (E5)
│           scan.py                                                       # skaner hipotez (D-037)
│           search.py  search_rules.py                                    # głębokie poszukiwanie (D-044)
│           investors.py                                                  # wirtualni inwestorzy — paper trading (D-045)
│           forest_rules.py  forest.py  forest_manager.py  forest_report.py  forest_run.py   # FOREST (D-049): cechy, reguły i las, Manager, statystyki, budowa i krok
├─ tests/                    # wskaźniki vs TA-Lib, złote scenariusze, zgodność z backtesting.py, walidacja,
│                            #   strategie, publikacja, przykłady, web/ (Node)
├─ strategies/examples/
├─ firestore.rules
└─ .github/workflows/        # ci.yml (pytest, lint), pages.yml
```

Gałąź `data` — osobna, tylko dane (sekcja 4).

---

## 13. Etapy

| Etap | Zakres | Gotowe, gdy |
|---|---|---|
| **E0** Infrastruktura | Repo, ten plik, CI, `.gitignore`, reguły Firestore, Auth, gałąź `data` | CI zielone, reguły wdrożone |
| **E1** Świece | Apps Script: backfill, tick, status, log; kontrola jakości | 8 par w bazie, latencja widoczna, 0 duplikatów, test krzyżowy zielony |
| **E2** Mac | `ia5 start`: kopia świec Yahoo, kontrola, warstwa czyszczenia, Parquet, heartbeat, kolejka | Dashboard pokazuje „połączony" i postęp; 8 par lokalnie |
| **E3** Silnik | Wskaźniki + zgodność z TA-Lib, wejścia, siatka wyjść, złote testy, zgodność z backtesting.py | Wszystkie testy zielone |
| **E4** Dashboard | Status, lista, nowa strategia, karta, raport | Pierwsza strategia policzona od wpisania do raportu |
| **E5** Walidacja | OOS, walk-forward, benchmark losowy, DSR, PBO, zamrażanie + forward | Werdykt w karcie |
| **E6** Inwestorzy | Wirtualni inwestorzy (paper trading): dodawanie/usuwanie, kapitał, % na wejście, wiele strategii naraz, wykres kapitału, lista transakcji (D-045) | Pierwszy inwestor liczony na Macu i widoczny na stronie |
| **E7** FOREST | Las reguł z progami Managera, odświeżenie co 4 tygodnie, dziennik, zakładka (D-048, D-049) | Las zbudowany na Macu, LIVE liczony co godzinę, widoczny na stronie |

Każdy etap: testy zielone → push → `STATUS.md` zaktualizowany → działa na żywej stronie. Aktualny stan etapów: `docs/STATUS.md`.

**Do kliknięcia przez Michała w E0** (Claude prowadzi krok po kroku): włączenie Firestore, włączenie logowania Google w Firebase Auth (+ domena `miszyszka.github.io`), klucz service account do `~/.ia5/`, ograniczenie klucza API do domeny strony w Google Cloud Console, projekt Apps Script podpięty pod arkusz, włączenie GitHub Pages przez Actions.

---

## 14. Decyzje

| Nr | Pytanie | Decyzja (2026-10-26) |
|---|---|---|
| O1 | Waluta konta | **USD** |
| O2 | Wielkość pozycji przy kilku pozycjach naraz | **Zależy od strategii** (`SIZING`); domyślnie zawsze **5, 10, 15, 20, 30%** kapitału jako depozyt (B4, 8.5) |
| O3 | Repo publiczne → wyniki i kod strategii widzi każdy | **Publiczne są OK** |
| O4 | Źródło danych | **Tylko Yahoo**: świece H1 (D-039, 2026-10-31; wcześniejsza decyzja o Dukascopy wycofana — dane uznane za niewiarygodne) i świece dzienne D1 z całą historią (D-053, 2026-11-10) |

Otwarte:

| Nr | Pytanie | Domyślnie, do czasu decyzji |
|---|---|---|
| O5 | Swapy | 0 w modelu; w każdej transakcji liczba nocy, a w walidacji wynik przy 0,5 i 1 pips za noc (D-054) |
