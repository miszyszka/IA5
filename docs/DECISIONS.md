# DECISIONS — dziennik decyzji IA5

Każda decyzja architektoniczna: data, decyzja, powód, odrzucone alternatywy (zasada G5 w `CLAUDE.md`).
Najnowsze na górze.

---

### D-038 · 2026-10-27 · Strategie liczone na wszystkich parach (zmiana D8)
- **Decyzja (Michał):** „Zgadzam się” — na pytanie, czy po skanie liczyć strategie na wszystkich parach z kompletem zatwierdzonych danych.
- **D8:** `COMPUTE_PAIRS` = wszystkie 8 par. Para bez zatwierdzonych miesięcy jest pomijana (bez zmian w zasadach zatwierdzania i czyszczenia). Do wyniku trafiają tylko pary, które mają dane do liczenia; raport podaje ich listę.
- Skutek uboczny: `ia5 fetch` pobiera w kolejności tabeli z sekcji 2 (EUR/USD pierwsza) — bez zmian dla EUR/USD.
- **Skaner (D-037) po pierwszym przebiegu:** dane miały tylko EUR/USD i USD/JPY (reszta w trakcie pobierania); siatka duża 312 tys. reguł → próg t ≥ 4,23; potwierdzona 1 reguła (EUR/USD long w grudniu 01–08 Londynu — 12 grudni, słaba podstawa). Dodane: „lata dodatnie” (odporne na skupienie transakcji w kilku okresach), lista „najbliżej progu” (`near.csv`), opis danych per para.
- **Odrzucone:** ręczne obniżenie progu FDR, żeby „coś przeszło” — to byłoby dokładnie to przeuczenie, przed którym skaner chroni.

### D-037 · 2026-10-27 · Skaner hipotez `ia5 scan` — szeroko na Macu, z kontrolą wielokrotnych prób
- **Decyzja (Michał):** „Skorzystaj z tego, że MAC może policzyć bardzo długo miliony różnych opcji.”
- **Problem:** miliony wariantów w zwykłym liczeniu strategii = miliony szans na przypadkowego zwycięzcę (DSR/PBO to wyłapią i strategia i tak będzie 🔴), a do tego miliardy wierszy transakcji, których nie da się zapisać ani opublikować.
- **Rozwiązanie:** osobny etap przed strategią. `ia5 scan` liczy proste reguły (sezon: godzina × długość × dzień × miesiąc × kierunek; impuls: ruch k świec ponad próg × za/przeciw × długość × sesja/godzina; trend: D dni × godzina × długość × za/przeciw) na **wszystkich parach** z zatwierdzonymi miesiącami — tylko statystyki, bez zapisu transakcji. Standardowo ~5,7 tys. reguł na parę (sekundy), `--duzy` ~160 tys. na parę (~1,3 mln na 8 par, minuty).
- **Kontrola:** odkrycie na pierwszych 50% historii z korektą Benjaminiego–Hochberga (FDR 5%) na wszystkie reguły naraz; potwierdzenie na 50–75% (ten sam znak, t ≥ 2); sąsiedzi w siatce (płaskowyż). **Ostatnie 25% (OOS silnika) skaner pomija całkowicie** — wybór reguł nie widzi okresu, na którym silnik je potem ocenia. Koszt: spread z tabeli raz na transakcję; transakcje na przerwach w danych i świecach uzupełnionych pomijane (B12); transakcje jednej reguły się nie nakładają.
- **Wynik skanu to hipotezy, nie werdykt.** Werdykt daje zwykłe liczenie strategii zbudowanej z najlepszych reguł (OOS, benchmark losowy, DSR, PBO).
- Skan liczy wszystkie pary (dane do liczenia budowane osobno w `data/h1_scan/`, te same zasady D8 poza listą par); silnik nadal tylko `COMPUTE_PAIRS` (D8 zmienia tylko Michał).
- Strategia widzi nazwę pary: `df.attrs["pair"]` — reguły z różnych par można złożyć w jedną strategię.
- **Odrzucone:** miliony wariantów w silniku (pamięć, publikacja, kara za próby); losowe przeszukiwanie (genetyczne, optymalizatory) — trudno policzyć, ile prób naprawdę wykonano, więc nie da się uczciwie skorygować wyniku; Romano–Wolf z bootstrapem na milionie reguł (pamięć macierzy dzień × reguła) — może później dla zawężonej listy.

### D-036 · 2026-10-27 · Badanie przed strategią na niezależnych danych (research/)
- **Powód:** cztery strategie pisane „z głowy” i oceniane na tych samych danych dały 🔴 — każda kolejna poprawka była dopasowaniem do historii EUR/USD. Michał: „postaraj się bardziej”.
- **Decyzja:** hipotezę szukamy na innym źródle niż to, na którym Mac ją ocenia. Odkrycie: H1 brokera MT (8 par, 2012–2022, publiczne repo `ejtraderLabs/historical-data`), z podziałem na połowę odkrycia (≤ 2017) i potwierdzenia (≥ 2018). Ocena: Dukascopy na Macu (2003–2026) — inne źródło cen i 9 lat, których badanie nie widziało. Skrypty w `research/`, dane tylko lokalnie (nie w repo, nie do backtestów — D7 bez zmian).
- **Pierwszy wynik:** EUR/USD słabnie w porannej sesji europejskiej (zgodne z Breedon i Ranaldo 2013) → `strategies/examples/eurusd_europe_morning.py`, 18 wariantów.
- **Odrzucone:** dalsze strojenie strategii RSI/Donchian na Dukascopy (PBO i korelacja IS–OOS pokazały brak przewagi); przeszukiwanie setek wariantów na jednych danych.

### D-035 · 2026-10-27 · Stop kroczący i limit czasu do 480 świec
- **Decyzja (Michał):** „Zrób oba jako dwie strategie” — strategia 4 (wybicie z kanału Donchiana, trend D1, wyjścia z obecnej siatki) i strategia 5 (to samo wejście, nowy stop kroczący).
- **Nowe wyjście `trail`** (`n`, `sl`, `trail`, opcjonalnie `tp`, `cap`): stop w świecy j = max(stop początkowy `sl`×ATR, najwyższe high świec przed j − `trail`×ATR) dla long, lustrzanie dla short. ATR ze świecy sygnału, stały przez całą transakcję. High bieżącej świecy nie przesuwa stopu w tej samej świecy — nie wiemy, czy padło przed dołkiem (pesymistycznie, jak B5). Luka za stopem → wyjście po open (B6). Powód wyjścia „stop kroczący”, gdy stop był już wyżej niż początkowy; R względem stopu początkowego.
- **B7 / limit czasu:** `cap` w `EXITS` do **480 świec** (ok. 20 dni handlu; było 120) — strategie trendowe trzymają pozycje tygodniami. Domyślna siatka bez zmian.
- Dashboard: rodzina wyjść „stop kroczący” w filtrze rankingu.
- `ENGINE_VERSION` 0.7.0.
- **Odrzucone:** stop kroczący od zamknięć (mniej czuły, zostawia więcej zysku — można dodać jako wariant później); ATR przeliczany co świecę (stop „oddychałby” z rynkiem, ale trudniej go sprawdzić ręcznie); TP w tych strategiach (ucina właśnie te duże ruchy, z których żyje strategia trendowa).

### D-034 · 2026-10-27 · Dokładanie pozycji, wagi, wyjście „seria RSI”, strategia bez okna godzin
- **Decyzja (Michał), przy strategii „RSI 70/30 w silnym trendzie”:** „do 5 pozycji na wybicie: kolejna, gdy RSI na zamknięciu pobije rekord z ostatniego wejścia; waga = 1 + (odległość RSI od progu) / 5, maksymalnie 3”; „zamknięcie wszystkiego, gdy RSI 6 świec z rzędu > 70 przy short (< 30 przy long), wyjście na open następnej świecy”; „bez okna godzin”; „dla porównania druga wersja: 1 pozycja, stała stawka”.
- **B8:** domyślnie bez zmian (1 pozycja na parę). Strategia może ustawić `PYRAMID = k` (1–10): do k pozycji naraz w parze, tylko w jednym kierunku; pozycja zajmuje miejsce do swojej świecy wyjścia włącznie. Każda pozycja ma własne TP (od własnej ceny wejścia, ATR ze swojej świecy sygnału) i własny limit czasu.
- **Wagi:** sygnał może być liczbą: znak = kierunek, |sygnał| (0,1–10) = waga. Waga mnoży depozyt w symulacji kapitału (Python i przeglądarka, B4: suma depozytów ≤ 100% — nadwyżka pominięta). Pipsy, R, ranking, DSR, PBO i benchmark losowy liczone na pozycję, bez wag — żeby wagi nie mnożyły prób i nie zmieniały definicji przewagi transakcji.
- **Nowe wyjście `rsi_streak`** (`run`, `level`, opcjonalnie `tp`×ATR(n), `sl`, `cap`): RSI14 przez `run` kolejnych zamknięć po złej stronie poziomu (short > level, long < 100 − level) → wyjście na open następnej świecy. Seria liczona na RSI całej pary, więc zamyka wszystkie otwarte pozycje naraz. TP w świecy ma pierwszeństwo przed wyjściem na open następnej.
- **B11:** strategia może ustawić `HOURS = False` (bez okna) albo `HOURS = (od, do)` w godzinach czasu polskiego; domyślnie 07–17. Benchmark losowy losuje w tym samym oknie.
- Logika dokładania (epizod, rekord RSI, licznik do 5, waga) jest w kodzie strategii, nie w silniku — silnik tylko pilnuje limitu i kierunku.
- `ENGINE_VERSION` 0.6.0 (domyślne zachowanie bez zmian, ale B10).
- **Odrzucone:** dokładanie wbudowane w silnik (każda strategia ma inną regułę dokładania); wagi jako osobne warianty w rankingu (mnożyłyby próby, W2); wyjście „seria RSI” liczone od świecy wejścia zamiast od początku przesady (Michał: „6 świec z rzędu” — świeca przebicia jest pierwszą).

### D-033 · 2026-10-27 · Świece Yahoo najszybciej, jak się da; audyt ostatniej doby z zegarem od pełnej godziny
- **Decyzja (Michał):** „Jak wybija pełna godzina, musi się zacząć odliczanie na czerwono przy każdej parze i trwać, dopóki nowa świeca nie zostanie zapisana. Skrypt ma pobierać najnowsze świece najszybciej, jak to możliwe. Mapa Yahoo: ostatnia doba, każda świeca podpisana godziną, trwająca godzina jako przerywana kratka.”
- **Apps Script:** wyzwalacz co 1 min (najkrótszy w Apps Script). Gdy wszystkie pary mają oczekiwaną świecę — koniec po odczycie Script Properties. W pierwszej minucie po pełnej godzinie skrypt czeka do +61 s (D2), potem rundy co 15 s tylko dla brakujących par, przez 10 min po zamknięciu, najwyżej 100 s na uruchomienie (blokada nie pozwala nałożyć się dwóm). Status zapisywany po każdej rundzie z nową świecą — dashboard zatrzymuje zegar tej pary od razu. W arkuszu `log` tylko wiersze z nową świecą, flagą albo błędem.
- **Budżet:** czas wykonania ok. 30–40 min/dobę (limit konta 90 min); Firestore ok. 300 zapisów/dobę (było ok. 220), 0 odczytów; UrlFetch ok. 200–400/dobę.
- **Dashboard:** zegar startuje równo o pełnej godzinie (nie po 60 s z D2) — `session.waitingSince`. Nagłówek: „czeka k/8 · m:ss” na czerwono. Stats → Yahoo: 24 zamknięte godziny + trwająca, podpis = godzina otwarcia w czasie polskim, przy każdej parze zegar albo czas ostatniego zapisu; kratki „czeka” z zegarem. Lista problemów z ostatniej doby.
- **Odrzucone:** dłuższe czekanie w jednym uruchomieniu (limit 90 min/dobę); odpytywanie Yahoo z przeglądarki (CORS, i świeca w Firestore jest tym, co mierzymy); zostawienie 3 tygodni w mapie (Michał chce widzieć dobę dokładnie).

### D-032 · 2026-10-27 · Wyjście na dowolnej świecy; anuluje tylko przerwa w dostępie do danych
- **Decyzja (Michał):** „Wejście w transakcję między 7:00 a 17:00, ale limit może być na jakiejkolwiek świecy. Przerwy, które anulują transakcję — tylko przerwy w dostępie do danych; weekendy nie stanowią bariery: po ostatniej piątkowej świecy jest pierwsza poniedziałkowa (lub późno-niedzielna).”
- **B11:** limit 23:00 (D-030) usunięty — pozycja kończy się według wariantu wyjścia (TP/SL, N świec, wskaźnik), także w nocy i po weekendzie. Limit N świec liczy świece, więc weekend go nie zjada. Swapy (O5) znów mają znaczenie — raport pokazuje ich skalę.
- **B12 / clean.py v2:** barierą jest tylko czas bez dostępu do danych: dzień uznany za niedostępny (`given_up`) i niezatwierdzony miesiąc między zatwierdzonymi (`ready.unavailable_ranges`). Dziura w pobranym dniu (Dukascopy ma plik, ale bez notowań) nie jest barierą: ≤ 3 h → uzupełniona i oznaczona (sygnał/wejście/wyjście na niej nadal anulowane — to cena z przyszłości), dłuższa → nic, jak weekend. Raport liczy osobno: „przerwa w dostępie do danych” i „świeca uzupełniona”.
- `ENGINE_VERSION` 0.5.0; `CLEAN_VERSION` 2 (ia5 start sam przebuduje `data/h1_ready/`).
- **Odrzucone:** traktowanie każdej godziny bez notowań jako przerwy (anulowałoby transakcje przez święta i ciche godziny — nie o to chodzi); brak uzupełniania w ogóle (Michał wcześniej chciał uśredniania pojedynczych świec).

### D-031a · 2026-10-27 · Wykres transakcji: osobne okna zamiast sklejonych wycinków
- **Problem (zrzut Michała):** wynik publikuje tylko ±24 świece wokół transakcji 10 najlepszych wariantów (D-010). Wykres kleił te wycinki jeden za drugim — odstęp tygodni wyglądał jak skok ceny o 200–400 pipsów, a markery transakcji spoza opublikowanych świec trafiały na najbliższą świecę z innego okresu. Same dane są poprawne (sprawdzone w plikach wyniku: OHLC spójne, ceny zgodne z historią EUR/USD, transakcje zgodne ze świecami).
- **Decyzja:** wycinki dzielone na okna (przerwa = ≥ 4 brakujące godziny sesji; weekend nie dzieli), między oknami puste miejsce; markery tylko dla transakcji z wejściem i wyjściem w jednym oknie (reszta policzona w podpisie); widok startuje na ostatniej transakcji, przyciski ← → przechodzą między transakcjami, skala cen tylko z okna transakcji. Logo TradingView zastąpione podpisem.

### D-031 · 2026-10-27 · Dwa procesy: pobieranie (`ia5 fetch`) i liczenie (`ia5 start`); tylko dane zatwierdzone; luki: uzupełnianie ≤ 3 h, dłuższe anulują transakcje
- **Decyzja (Michał):** „Niech jeden program pobiera dane, a inny już liczy strategie na tym co jest. Liczyć na razie tylko na EURUSD. Algorytm pobierający niech pobierze całą jedną parę do końca. Backtest liczy tylko na zatwierdzonych. Pojedyncze brakujące świece uzupełnij uśredniając; dłuższe okresy — backtest ma o nich wiedzieć, a transakcje na nie nachodzące anulować.”
- **Pobieracz `ia5 fetch`:** osobny proces, kolejność `COMPUTE_PAIRS` (EUR/USD), potem reszta. Para do końca: runda szybka, potem naprawcze (2 próby, wolniej), po rundzie bez postępu przerwa 30 s ×2 do 30 min. Każda nieudana próba dnia liczona w `RRRR-MM.missing.json` (`{"missing": {dzień: próby}, "given_up": [...]}`); po 6 próbach dzień starszy niż 7 dni → niedostępny (świeży dzień nigdy — Dukascopy może jeszcze publikować). 8 rund bez postępu (np. długa blokada) → następna para, powrót za godzinę. Zapisy atomowe (plik tymczasowy + `replace`), bo `ia5 start` czyta równolegle. Heartbeat w polu `runner/heartbeat.fetch` (zapis z `merge` po polach — dwa procesy nie nadpisują się). Na gałąź `data` publikuje tylko `ia5 start` (jeden pisarz do lokalnego klonu).
- **Zatwierdzony miesiąc:** plik jest, żaden dzień nie czeka na dociągnięcie (niedostępne dozwolone), miesiąc kompletny (bieżący: dane do ≤ 3 dni przed wczoraj). Silnik dostaje tylko zatwierdzone miesiące par z `COMPUTE_PAIRS` → `data/h1_ready/`. Przebudowa tylko po zmianie plików (podpis: rozmiar + czas modyfikacji + niedostępne dni + `CLEAN_VERSION`).
- **Czyszczenie (`clean.py`, wersja 1):** oś = świece istniejące + oczekiwane godziny sesji (kalendarz D-028). Seria ≤ 3 brakujących godzin → świece uzupełnione liniowo od zamknięcia przed luką do otwarcia po niej (`filled=True`, `minutes=0`, spread z ostatniej świecy). Dłuższa → dziura, `gap_before` = liczba godzin na pierwszej świecy po niej. Strategie widzą tylko OHLC.
- **Silnik (B12, `ENGINE_VERSION` 0.4.0):** transakcja anulowana, gdy między świecą wejścia a świecą wyjścia (włącznie; także przed wejściem) jest długa luka, albo gdy świeca sygnału, wejścia lub wyjścia jest uzupełniona. Uzupełniona świeca w środku trzymanej pozycji jest dozwolona. Anulowana transakcja nie blokuje kolejnych (B8). Benchmark losowy anuluje tak samo. Raport: ile świec uzupełniono, ile długich luk, ile transakcji anulowano.
- **Dlaczego świeca sygnału/wejścia/wyjścia nie może być uzupełniona:** uzupełniona świeca kończy się na otwarciu następnej — to cena z przyszłości. Sygnał liczony na niej znałby cenę wejścia (look-ahead), a wejście/wyjście po niej byłoby po cenie, której nikt nie widział.
- **Odrzucone:** uzupełnianie dłuższych luk (wymyślone ceny przez godziny — wynik fikcyjny); wyrzucanie całych miesięcy z dziurą (traci się lata danych przez jedną godzinę); ciche łatanie w danych surowych (łamie D4/D5); jeden proces z pobieraniem w wątku (blokada Dukascopy wstrzymywałaby liczenie i odwrotnie); osobny dokument Firestore na stan pobieracza (dodatkowy nasłuch w dashboardzie — Z2).
- **Budżet (Z4):** heartbeat pobieracza co 30 s ≈ 2 880 zapisów/dobę; razem z `ia5 start` ≈ 5 760 z 20 000. Odczyty dashboardu bez zmian (ten sam dokument `runner/heartbeat`).
- **Progi do kalibracji:** 3 h uzupełniania, 6 prób / 7 dni, 8 rund bez postępu.

### D-030 · 2026-10-27 · Zamknięcie pozycji najpóźniej o 23:00 czasu polskiego; Dukascopy: czekanie przy pełnej blokadzie
- **Decyzja (Michał):** „Nie zamykaj o 17. Zamykaj najpóźniej o 23:00.” B11 rozszerzone: każda pozycja (każdy wariant wyjścia) kończy się najpóźniej na zamknięciu świecy 22:00 czasu polskiego, czyli o 23:00 (zimą 22:00 UTC, latem 21:00 UTC); powód wyjścia `23:00`. TP/SL i wyjścia wskaźnikowe działają normalnie do tego momentu. Benchmark losowych wejść ma ten sam limit. `ENGINE_VERSION` 0.3.0.
- **Skutek:** pozycje nie przechodzą przez noc, więc problem swapów (O5) w praktyce znika; wyjścia czasowe dłuższe niż czas do 23:00 (np. 24–120 świec) kończą się o 23:00 — ich wyniki będą do siebie podobne i to widać w rankingu.
- **Dukascopy (log 27.10 17:02–17:48):** serwer zaczął odpowiadać HTTP 503 / brakiem odpowiedzi na całe miesiące; przebieg szybki przelatywał przez kolejne „nic nie pobrano”, co tylko przedłużało blokadę. Teraz: miesiąc odrzucony w całości → przerwa 60 s, podwajana do 10 min, i ponowienie tego samego miesiąca; start od 4 dni naraz, maks. 6.

### D-029 · 2026-10-27 · Dukascopy: przebieg szybki + przebieg naprawczy (zamiast czekania na zawieszone pliki)
- **Obserwacja (log z Maca, 27.10, ~8 h pracy):** EUR/USD gotowe w 99%, USD/JPY w ok. 25%, reszta par nie zaczęta — ok. 15% całości. Czysty miesiąc pobiera się w ~10 s, ale miesiąc z odrzuconymi plikami trwał 5–30 min: każdy zawieszony plik kosztował do ~3 min (3 próby × limit 10 s + 45 s), dzień to 2 pliki, a po błędach tempo spadało do 1 dnia naraz i przerwy 45 s.
- **Decyzja:** przebieg główny robi **jedną** próbę na plik z krótkim limitem (5 s połączenie, 15 s odczyt) i nie czeka — odrzucony dzień od razu trafia na listę brakujących; tempo spada o połowę i krótka przerwa 15 s tylko, gdy serwer odrzuca > 1/3 dni miesiąca. Po wszystkich parach **przebieg naprawczy** wraca tylko do miesięcy z brakującymi dniami (2 dni naraz, 2 próby, dłuższy limit). Log co 12 miesięcy pokazuje postęp i szacowany czas do końca pary.
- **Oczekiwany efekt:** czas zależy od czystych miesięcy (~10–15 s), a nie od zawieszonych plików; zostało ok. 1 900 miesięcy → rzędu kilku godzin zamiast kilku dni.
- **Odrzucone:** dalsze zwiększanie równoległości (serwer dławi mocniej); pobieranie z innego źródła (D7, D-010 — Dukascopy jest jedynym źródłem do backtestów).

### D-028 · 2026-10-27 · Handel 07:00–17:00 czasu polskiego (B11), święta w kalendarzu, dziury tylko tam, gdzie rynek się ruszał
- **Decyzja (Michał):** „trading robimy w godzinach 7:00–17:00 czasu polskiego — wtedy są najniższe spready”. Nowa żelazna zasada **B11**: wejście tylko na open świecy otwartej o 07:00…16:00 `Europe/Warsaw` (z czasem letnim). Sygnały poza oknem pomijane i liczone (`poza_godzinami` w raporcie). Benchmark losowych wejść losuje w tym samym oknie — inaczej porównanie byłoby nieuczciwe (W3). `ENGINE_VERSION` 0.2.0. Wyjścia na razie o dowolnej porze — **do decyzji Michała**: czy zamykać pozycje o 17:00.
- **Święta:** kalendarz sesji (Python, wektorowy w mapie pokrycia, Apps Script, dashboard) nie oczekuje świec 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC. Rozwiązuje znany problem z D-009.
- **Dziury tylko tam, gdzie mogły być ruchy:** dziurą jest godzina, w której rynek działał (≥ połowa par ma notowania) i cena się ruszała. Nie są dziurami: luka wspólna dla ≥ połowy par (rynek nieczynny, święto spoza listy, przerwa źródła) i luka „bez ruchu” — do 3 h, po której cena jest ta sama co przed (< 1 pips). W audycie Yahoo godzina brakująca w ≥ 75% par to „brak we wszystkich parach”, nie brak konkretnej pary.
- **Mapa Dukascopy:** kafelek wypełnia się od dołu proporcjonalnie do tego, ile miesiąca pobrano; kolor mówi, jak duże są dziury (zielony bez dziur, bursztyn 1–5 h i 6–47 h, czerwony ≥ 48 h). W audycie Yahoo świeca, która dotarła, jest zielona (szare kafelki się myliły).
- **Odrzucone:** okno godzin jako filtr w strategii (każdy musiałby pamiętać; B11 trzyma to w silniku); stała lista wszystkich świąt bankowych (FX handluje w większość z nich — wystarcza 25.12 i 1.01 plus wykrywanie luk wspólnych z danych).

### D-027 · 2026-10-27 · Stats: audyt Yahoo świeca po świecy, pełny kafelek przeglądu, bez listy flag
- **Decyzja (Michał):** w widoku Yahoo mapy jeden kafelek = jedna świeca H1, ostatnie 3 tygodnie, na bieżąco. Apps Script prowadzi `meta/status.recent` (504 znaki na parę: `1` jest, `l` spóźniona > 20 min po zamknięciu, `f` z flagą jakości, `.` brak); dashboard dokłada kalendarz sesji i czas: brak = świeca w godzinach rynku, która nie dotarła 20 min po zamknięciu; „w drodze” = jeszcze w tym oknie. Ponowny zapis świecy nie kasuje oznaczeń „spóźniona” ani „flaga”.
- **Kafelek „Przegląd zdrowia”** pokazuje każdy problem (nazwa + jedno zdanie), nie samą liczbę. **Flagi:** usunięty kafelek i lista flag (mało czytelne tokeny `luka@…`, `revised@…`); te same informacje są teraz w audycie (kafelki „z flagą”, braki) i w kontroli „Jakość świec Yahoo” przeglądu zdrowia. Apps Script nadal je liczy.
- **Script Properties:** dziennik i audyt w osobnych właściwościach (`daily`, `recent`) — limit 9 KB na wartość był blisko przekroczenia. Stary format stanu jest wczytywany i rozdzielany automatycznie.
- **Z4:** 0 dodatkowych zapisów (pole w istniejącym zapisie statusu), +4 KB dokumentu `meta/status`; zasiew jednorazowo 16 odczytów (te same co dziennik). Dashboard: 0 dodatkowych odczytów.
- **Odrzucone:** czytanie świec Yahoo z Firestore w przeglądarce (Z2); audyt z mapy pokrycia Maca (aktualizowany co 6 h, nie „na bieżąco”).

### D-026 · 2026-10-27 · Dukascopy: tempo pobierania dobierane do dławienia serwera
- **Obserwacja (log z Maca, 27.10):** miesiąc bez błędów pobiera się w ~10–15 s, miesiąc z błędami w 2–3 min; błędy to `connect timeout` / `read timeout` seriami — serwer dławi zbyt wiele połączeń naraz (8 dni = 16 plików jednocześnie w D-025 pogorszyło sprawę).
- **Decyzja:** start od 6 dni naraz; po miesiącu z błędami tempo spada o połowę (min. 1), przy > 25% odrzuconych dni przerwa 45 s; odrzucone dni są od razu ponawiane wolniej w tym samym przebiegu; po czystym miesiącu tempo rośnie o 1 (maks. 8). Ucisza też szum gRPC („FD from fork parent…”).
- **Sprzątanie:** z repo usunięte przypadkowo dodane paczki `.whl` (≈ 49 MB, stąd wolny `git pull`); `*.whl` w `.gitignore`. Historia gita zostaje (G4).

### D-025 · 2026-10-27 · Dukascopy: niepełne miesiące zapisywane od razu, pobierane tylko brakujące dni
- **Problem (Michał):** pojedynczy nieudany dzień wyrzucał cały pobrany miesiąc; przy wielogodzinnym pierwszym pobieraniu częste błędy sieci oznaczały powtarzanie tej samej pracy, a dashboard nie pokazywał, co już jest.
- **Decyzja:** pobrane dni są dopisywane do `RRRR-MM.parquet` od razu; dni, które się nie udały, trafiają do `RRRR-MM.missing.json` i przy następnym uruchomieniu pobierane są tylko one (oraz dni po ostatnim zapisanym — bieżący miesiąc nie jest już pobierany od nowa przy każdym starcie). Już zapisane minuty się nie zmieniają (D4). Szybciej: 8 dni naraz zamiast 4, 3 próby na plik zamiast 6 (nieudany dzień i tak wróci w kolejnym przebiegu).
- **Mapa pokrycia:** nowy stan „pobrany częściowo” (przerywany bursztynowy obrys), godziny niepobranych dni liczone osobno jako „brakuje”, nie jako dziury. W trakcie długiego pobierania mapa jest publikowana po każdej parze (gdy para pobierała się > 2 min), a statusy miesięcy idą na żywo przez heartbeat.
- **Odrzucone:** zapis dziennych plików (≈ 60 tys. plików na parę); zapis bez listy brakujących dni (luki stałyby się niewidoczne i trwałe).

### D-024 · 2026-10-27 · Dźwignia 30:1 zawsze (zmiana żelaznej zasady B4)
- **Decyzja (Michał, wprost: „trading zawsze jest na dźwigni 30:1”):** B4, sekcja 2 i 8.5: nominał = 30 × depozyt. Depozyt nadal X% kapitału, X ∈ {5, 10, 15, 20, 30}%, suma depozytów ≤ 100% kapitału → łączna ekspozycja ≤ 30:1. `LEVERAGE = 30` w `runner/ia5/config.py` i `web/js/metrics.js`; `ENGINE_VERSION` 0.0.1 → 0.1.0 (B10 — starsze wyniki, w tym DEMO, są nieaktualne).
- **Skutek:** przy tej samej wielkości depozytu wynik i obsunięcia kapitału są 6× większe niż przy 1:5 (np. depozyt 30% = nominał 9× kapitału na pozycję). Przewaga transakcji (pips, R), ranking, DSR i PBO się nie zmieniają — zależą tylko od transakcji.
- **Do decyzji:** brak modelu stop-out brokera — kapitał może spaść poniżej zera, wtedy nowe wejścia są pomijane. Jeśli „X%” miało oznaczać nominał, a nie depozyt — trzeba zmienić B4.
- **Odrzucone:** zostawienie 1:5 jako domyślnej i 30:1 jako opcji (Michał: „zawsze”).

### D-023 · 2026-10-27 · Przegląd zdrowia zamiast kafelka „Kontrola krzyżowa”
- **Decyzja (Michał: „ogólny system, który informuje o błędach i opisowo mówi o stanie bazy i projektu”):** `ia5/health.py` na Macu uruchamia zestaw nazwanych kontroli po każdej synchronizacji, co godzinę i na żądanie (`ia5 health`, opisowy raport w terminalu). Wynik w `meta/status.health`: stan, jedno zdanie, opis bazy i projektu, kontrole `{id, name, state, text, detail, fix}`. Stats otwiera się panelem „Stan systemu”; nagłówek liczy problemy z przeglądu.
- **Kontrole:** świeżość Yahoo (od pierwszej brakującej świecy), Apps Script bez błędów, flagi Yahoo, aktualność Dukascopy, kompletność historii (z mapy pokrycia), poprawność świec, trójkąty EUR/JPY i EUR/GBP godzina po godzinie na całej historii (próg 15 / 8 pips, uwaga > 0,1% godzin, lista najgorszych miesięcy), Dukascopy vs Yahoo z wykrywaniem przesunięcia czasu o ±1 h, zamrożone notowania (≥ 8 h tego samego zamknięcia), publikacja na GitHub (błąd pusha już nie przerywa synchronizacji), strategie z błędem / utknięte / zbyt długo w kolejce, wolne miejsce na dysku.
- **Strażnik:** dashboard dokłada kontrolę „Sprawdzanie”, gdy przegląd jest starszy niż 2 h (albo go nie było) — cisza nie wygląda jak „wszystko OK”.
- **Z4:** 1 zapis `meta/status` co godzinę (≈ 25/dobę), odczyt `meta/status` i listy strategii co godzinę (kilkanaście–kilkadziesiąt odczytów/dobę). Dashboard: 0 dodatkowych odczytów (nasłuchuje `meta/status`). Dokument rośnie o ok. 5–15 KB.
- **Sprawdzenie:** testy z podłożonymi usterkami — zła cena w jednej parze (trójkąt wskazuje parę i miesiąc), przesunięcie Yahoo o godzinę, zamrożony feed, przeterminowane Yahoo, zepsuta świeca, nieudana publikacja, utknięta strategia; czyste dane nie zapalają żadnej kontroli.
- **Odrzucone:** osobny skrypt w Apps Script (nie widzi historii Dukascopy ani Maca); powiadomienia mailem/push (na razie bez nowej usługi — G6; łatwo dołożyć, gdy będzie potrzebne); zostawienie trójkąta tylko na ostatniej świecy Yahoo (wyłapuje mało i tylko „teraz”).

### D-022 · 2026-10-27 · Mapa pokrycia danych w Stats
- **Decyzja (Michał: „mapa wszystkich par, ile brakuje, gdzie są luki”):** Mac liczy z surowych danych (pliki M1 Dukascopy i zbudowane z nich H1, kopia Yahoo) pokrycie para × miesiąc wobec kalendarza sesji (`ia5/coverage.py`, ten sam kalendarz co `is_expected_bar`, wektorowo) i publikuje `coverage/coverage.json` na gałęzi `data` po każdej synchronizacji (tylko gdy treść się zmieniła). W trakcie pobierania statusy miesięcy idą w `runner/heartbeat.sync` (1 znak = 1 miesiąc), więc mapa wypełnia się na żywo.
- **Rozróżnienia:** status pliku (nie pobrany / błąd / pełny / w toku / Dukascopy nie ma) oddzielnie od luk. Luka = godzina sesji bez świecy. *Dziura* — brakuje jej tylko tej parze (lub mniej niż połowie par mających ten okres); *wspólna* — brakuje jej ≥ połowie z co najmniej 3 par (święto, krótka sesja albo przerwa źródła — nie twierdzimy, że to na pewno święto). Każda luka ma liczbę jej godzin obecnych w drugim źródle (Yahoo dla Dukascopy i odwrotnie): jeśli Yahoo ją ma, dziura jest po naszej stronie. Cienka godzina = świeca z < 30 minut z notowaniami. Pokrycie % = obecne / (oczekiwane − wspólne), z niepobranymi miesiącami w mianowniku — to jest „ile brakuje”.
- **D-010:** plik zawiera tylko liczniki i znaczniki czasu luk, żadnych cen Dukascopy — publikacja zgodna z zakazem redystrybucji.
- **Z4:** Firestore 0 dodatkowych zapisów i odczytów (heartbeat i tak co 30 s; pole `sync` ok. 2,3 KB i tylko w trakcie pobierania). Dashboard czyta mapę z gałęzi `data` (Z2), ok. 80 KB.
- **Sprawdzenie:** test porównuje kalendarz wektorowy z `is_expected_bar` dla każdej godziny 2003–2026; podłożone dziury, luka przez weekend, wspólna luka, błąd pobierania, miesiąc bez danych i cienka godzina są wykrywane co do godziny; przepływ `do_sync` (statusy na żywo + publikacja) testowany bez sieci.
- **Odrzucone:** dokument `meta/coverage` w Firestore (zmiana Z2, odczyty przy każdej zmianie); jeden pasek 282 miesięcy w poprzek (komórki 3 px — nie da się kliknąć; zamiast tego pasy po latach); kolorowanie wspólnych luk (każdy grudzień byłby bursztynowy i zagłuszałby prawdziwe dziury).

### D-021 · 2026-10-26 · Dukascopy: miesiąc zapisany w trakcie jest dociągany po jego końcu
- **Problem:** `months_to_sync` pomijał każdy miesiąc, który miał już plik. Miesiąc zapisany np. 20-go (bo wtedy działał `ia5 start`) po przejściu na nowy miesiąc zostawał z trwałą luką od 20-go do końca miesiąca — kontrola jakości by ją zgłosiła, ale nic by jej nie uzupełniło.
- **Decyzja:** miesiąc jest pełny, gdy ma dane z ostatniego dnia handlowego (pn–pt) albo plik zapisano ≥ 2 dni po końcu miesiąca (wtedy zawiera wszystko, co Dukascopy ma — np. przy święcie bez notowań). Niepełny → pobierany ponownie przy najbliższym `ia5 start`. Pusty plik = brak notowań w Dukascopy → pełny.
- **Odrzucone:** osobny plik-znacznik pełnych miesięcy (nie naprawia plików już zapisanych na Macu); sama data modyfikacji pliku (zapis tuż po północy mógłby udawać pełny miesiąc).

### D-020 · 2026-10-26 · Dziennik świec w `meta/status.daily`
- **Decyzja:** Apps Script liczy świece w bazie wg dnia świecy (UTC), per para, ostatnie 60 dni; backfill przelicza, tick dolicza nowe. Pierwsze uruchomienie (i ręczne `rebuildDaily()`) zasiewa dziennik z dokumentów `candles/*` bieżącego i poprzedniego miesiąca. Zakładka Stats pokazuje 30 dni wobec oczekiwanych z kalendarza sesji.
- **Z4:** 0 dodatkowych zapisów (pole jedzie w istniejącym zapisie statusu), 16 odczytów jednorazowo przy zasiewie, dashboard 0 dodatkowych odczytów (i tak nasłuchuje `meta/status`). Rozmiar: ok. 60 × 8 liczb.
- **Odrzucone:** liczenie w przeglądarce ze świec na gałęzi `data` (zależne od działającego Maca, gałąź jeszcze bez świec); czytanie arkusza `log` (wymaga logowania do Google Sheets); dokument na każdy dzień (zbędne odczyty).
- **Ograniczenie:** dziennik liczy Yahoo (monitoring). Kompletność Dukascopy (dane do backtestów) widać na razie tylko w terminalu `ia5 start` („luki N”).

### D-019 · 2026-10-26 · Design: płasko, jeden akcent, stan w nagłówku, zakładka Stats (CLAUDE.md 10.1, 10.2, 11)
- **Decyzja (Michał):** bardziej minimalistycznie i spójnie — bez gradientów, mniej kolorów, poświata. Wskaźnik „dane żyją” tuż obok „Mac połączony”, bez kafli KPI; liczba świec i reszta liczb w nowej zakładce **Stats** z dziennikiem dzień po dniu; pary jako jeden symboliczny kafelek bez danych i bez rozwijania.
- **Jak:** jeden akcent (pomarańcz) wyłącznie dla „wybrane”; zielony/bursztyn/czerwony wyłącznie jako stan i znak wyniku; usunięty niebieski i błękit; poświata tylko na kropkach stanu (lekko „oddychają”, gdy system działa; wyłączone przy `prefers-reduced-motion`). Wykresy bez wypełnienia gradientem i bez poświaty linii.
- **Odrzucone:** poświata na przyciskach, paskach i kartach (rozmywa znaczenie — świeci wszystko, więc nic); osobny pasek statusu pod nagłówkiem (więcej miejsca, a Michał chciał prościej).

### D-018 · 2026-10-26 · Detektor look-ahead: cięcia + zaburzenie przyszłości
- **Decyzja:** oprócz 8 losowych cięć pełnych danych — 24 gęste cięcia na wycinku 2000 świec, a przy każdym porównanie sygnałów sprzed cięcia przy przyszłości ×1,3 i ×0,7.
- **Powód:** same cięcia nie wykrywały „krótkiego” look-ahead (SMA z niezamkniętej świecy H4 zmienia średnią minimalnie). Zaburzenie przyszłości wykrywa go na każdej parze (test `test_unclosed_higher_timeframe_is_caught`).

### D-017 · 2026-10-26 · Reguła „zrób mi strategię” (K1–K3) i `scripts/check_strategy.py`
- **Decyzja:** procedura w `docs/STRATEGIE.md`; Claude przed oddaniem kodu uruchamia kontrolę na danych syntetycznych (8 par) i prawdziwym EUR/USD 2017–2018 z backtesting.py; na Macu to samo robi `ia5 check` na danych Dukascopy.
- **Powód:** kod wklejony do dashboardu ma działać za pierwszym razem; błędy kontraktu i look-ahead wychodzą przed liczeniem, nie po godzinie.
- **Biblioteka `ind` rozszerzona** o MACD, stochastyk, ADX/DI, Donchian, rising/falling, godzinę/dzień/sesję — każdy wskaźnik zgodny z TA-Lib.

### D-016 · 2026-10-26 · Protokół dashboard ↔ Mac
- **Decyzja:** jedynym kanałem jest dokument `strategies/{id}` (statusy `do_policzenia → liczy_sie → policzona | blad`, `do_usuniecia`) + heartbeat z postępem + wyniki na gałęzi `data`. Usunięcie = status `do_usuniecia` (strategia znika z listy od razu, pliki usuwa Mac). Strategie istniejące tylko na gałęzi `data` (np. DEMO) dostają dokument przy pierwszej akcji (usuń / policz ponownie).
- **Powód:** dashboard nie ma uprawnień do zapisu na GitHub (brak tokenu w przeglądarce) — pisze tylko do Firestore; Mac jest jedynym zapisującym gałąź `data`. Lista działa także bez Firestore (tylko odczyt z GitHub).
- **Odświeżanie:** dashboard pobiera SHA gałęzi `data` z API GitHub (60 zapytań/h na IP — wystarcza), ponownie po zakończeniu liczenia (heartbeat `computing → idle`) i po zmianie statusu na `policzona`.

### D-015 · 2026-10-26 · Dashboard: biblioteki w repo, hyparquet zamiast DuckDB-WASM, pole tekstowe zamiast CodeMirror
- **Decyzja:** ECharts, Lightweight Charts i hyparquet skopiowane do `web/vendor/` (licencje obok). Parquet czytany przez hyparquet — tylko zakres wierszy wybranego wariantu (`row_start`, `row_end` w `variants.json`, plik posortowany po `variant_id`). Kod strategii w zwykłym polu tekstowym z obsługą Tab i kontrolą na żywo.
- **Powód:** brak zależności od CDN (strona działa, gdy CDN ma awarię); DuckDB-WASM to kilkadziesiąt MB do pobrania dla prostego filtra; CodeMirror wymaga bundlera lub wielu modułów z CDN. Do zmiany, gdy edytor okaże się za ubogi.

### D-014 · 2026-10-26 · Kapitał: zwrot na nominale w walucie kwotowanej
- **Decyzja:** zysk transakcji = nominał × (pipsy netto × pips ÷ cena wejścia). Ta sama funkcja w Pythonie (`portfolio.py`) i JS (`metrics.js`), zgodność sprawdzana testem.
- **Powód:** prosto i identycznie w obu miejscach; dla par bez USD jako waluty kwotowanej pomija zmianę kursu przeliczenia w trakcie transakcji (efekt drugiego rzędu).

### D-013 · 2026-10-26 · E3: R po kosztach, rozgrzewka, granice sandboxa
- **R po kosztach** = pipsy netto ÷ ryzyko w pipsach (SL w pipsach albo 1×ATR14 dla wyjść bez SL). Wcześniejsze przeskalowanie przez netto/brutto wybuchało przy transakcjach bliskich zeru — wykryte testem w realnej skali.
- **Rozgrzewka:** wejścia, dla których ATR5 lub ATR14 jeszcze nie istnieje, są pomijane i liczone w raporcie.
- **Sandbox:** kod strategii działa w osobnym procesie (`python -I`, czyste środowisko bez kluczy, limit czasu 30 min, limit pamięci na Linuksie). Lista dozwolonych importów (`numpy`, `pandas`, `math`) chroni przed pomyłką, nie przed celowym atakiem — granicą bezpieczeństwa pozostaje S1 (logowanie + reguły + kontrola właściciela).
- **Ranking:** wariant musi mieć ≥ 30 transakcji IS, żeby trafić na szczyt; sortowanie po średnim R netto w IS (W1).
- **Wydajność:** 8 par × 140 tys. świec × 466 wariantów ≈ 1 min.

### D-012 · 2026-10-26 · E3: silnik — szczegóły modelu wykonania i bez numba
- **Decyzja:** silnik w jednym module `runner/ia5/engine.py`, obliczenia wektorowe numpy (okna cen od świecy wejścia) zamiast numba.
- **Doprecyzowania modelu (uzupełniają B1–B8):** wyjście czasowe po N świecach = zamknięcie świecy e+N−1; wyjścia wskaźnikowe (RSI do 50, cena przez SMA20, sygnał przeciwny) — warunek na zamknięciu świecy, wykonanie na open następnej; „przecięcie SMA" z 8.2 = zamknięcie po złej stronie SMA20; nowe wejście w tej samej parze tylko na świecy późniejszej niż świeca wyjścia; transakcje bez danych do wyjścia odrzucane i liczone.
- **Powód:** numpy wystarcza (setki wariantów × tysiące wejść liczą się w sekundach), jedna zależność mniej. Doprecyzowania usuwają niejednoznaczności spisane w 8.2.
- **Weryfikacja:** wskaźniki = TA-Lib (1e-9); listy transakcji = backtesting.py (wyjście czasowe oraz TP/SL z ATR, identyczne co do świecy i ceny); 16 złotych scenariuszy.

### D-011 · 2026-10-26 · E2: zależności i układ plików M1
- **Decyzja:** runner używa `numpy`, `pandas`, `pyarrow`, `firebase-admin`; pobieranie Dukascopy własnym czytnikiem plików `bi5` (stdlib: `urllib`, `lzma`, `struct`), bez `dukascopy-node`. M1 zapisywane per miesiąc (`{RRRR-MM}.parquet`), żeby pierwsze pobieranie dało się przerwać i wznowić.
- **Powód:** mniej zależności (bez Node), wznawialność kilkugodzinnego pierwszego pobrania.
- **Do potwierdzenia na Macu:** kolejność pól w rekordzie (open, close, low, high) i punkt (1000 dla JPY, 100 000 dla reszty) — sprawdzone tylko na danych syntetycznych, bo serwer Dukascopy jest niedostępny z sesji Claude.

### D-010 · 2026-10-26 · O6: dane Dukascopy nie trafiają na publiczny GitHub
- **Decyzja:** M1 i H1 z Dukascopy zostają na Macu. Gałąź `data` dostaje świece H1 z Yahoo; wyniki strategii — tylko wycinki świec wokół transakcji.
- **Powód:** okno pobierania danych Dukascopy określa je jako użytek osobisty; publiczne repo to redystrybucja.
- **Odrzucone:** publikacja pełnej historii H1 z Dukascopy.

### D-009 · 2026-10-26 · Apps Script: zapis przez `documents:commit`, nie `PATCH`
- **Decyzja:** świece i status zapisywane przez endpoint `commit` z `updateMask` w treści żądania, nagłówek `x-goog-user-project: project-ia5`.
- **Powód:** `PATCH` wymaga listy pól w adresie URL — przy ~740 świecach w miesiącu adres przekracza limit długości UrlFetch. Nagłówek kieruje limity na projekt Firebase, a nie domyślny projekt skryptu.
- **Ograniczenie:** święta (np. 25 grudnia) nie są w kalendarzu sesji — tego dnia status pokaże STOI. Do poprawy, gdy będzie przeszkadzać.

### D-008 · 2026-10-26 · Wielkość pozycji: % kapitału jako depozyt, domyślnie 5/10/15/20/30%
- **Decyzja:** depozyt = X% kapitału, nominał = 5 × depozyt (dźwignia 1:5). Domyślnie liczymy X ∈ {5, 10, 15, 20, 30}%; strategia może podać własne (`SIZING`). Suma depozytów otwartych pozycji ≤ 100% kapitału; sygnał bez wolnego depozytu pomijany i liczony.
- **Powód:** Michał: „zależy od strategii, domyślnie zawsze kilka opcji 5, 10, 15, 20, 30% kapitału". Limit depozytu utrzymuje łączną ekspozycję ≤ 1:5.
- **Interpretacja do potwierdzenia:** „X% kapitału" rozumiane jako depozyt (nominał 5 × X%). Jeśli Michał miał na myśli nominał — zmienić B4 i 8.5.
- **Odrzucone:** sloty po równo; pełna dźwignia na każdą pozycję (łamie 1:5 przy nakładaniu); stałe ryzyko na SL.
- Wielkość pozycji to przełącznik w karcie, nie wariant w rankingu — nie mnoży liczby prób w DSR/PBO.

### D-007 · 2026-10-26 · Dwa źródła danych o rozdzielonych rolach
- **Decyzja:** Dukascopy M1 bid/ask = jedyne źródło do backtestów i forward testów (świece H1 budowane lokalnie z M1). Yahoo → Apps Script → Firestore = monitoring na żywo i niezależna kontrola danych.
- **Powód:** Yahoo daje świece 1h tylko z ostatnich 730 dni i bez bid/ask. Dukascopy daje kilkanaście lat historii i M1, co pozwala rozstrzygnąć kolejność TP/SL wewnątrz świecy H1.
- **Odrzucone:** tylko Yahoo (za krótka historia, brak rozstrzygania wewnątrz świecy); sklejanie obu źródeł w jedną serię (szew między różnymi feedami fałszuje wyniki).
- **Otwarte (O6):** czy warunki Dukascopy pozwalają publikować zbudowane świece H1 na publicznej gałęzi `data`.

### D-006 · 2026-10-26 · Wyniki i kod strategii publiczne
- **Decyzja:** wyniki na publicznej gałęzi `data` repo IA5.
- **Powód:** Michał: „publiczne są OK". Najprostsze, bez kosztów.
- **Odrzucone:** wyniki w Firestore za logowaniem (koszt odczytów); Firebase Storage (wymaga planu Blaze).

### D-005 · 2026-10-26 · Waluta konta USD
- **Decyzja:** kapitał i wyniki w USD, start 10 000 USD.
- **Powód:** wszystkie przeliczenia możliwe z naszych 8 par, bez dodatkowej serii.

### D-004 · 2026-10-26 · Model wykonania
- **Decyzja:** sygnał na zamknięciu świecy, wejście na open następnej; TP/SL w tej samej świecy rozstrzygane na M1, w tej samej minucie → SL; luki: SL po open, TP po poziomie; spread raz na transakcję.
- **Powód:** brak look-ahead i konserwatywne założenia tam, gdzie dane nie rozstrzygają.

### D-003 · 2026-10-26 · Dashboard czyta świece i wyniki z GitHub, nie z Firestore
- **Decyzja:** gałąź `data` (Parquet, JSON, raport) czytana przez `raw.githubusercontent.com` z SHA w adresie. Z Firestore dashboard czyta tylko `meta/status`, `runner/heartbeat`, `strategies`.
- **Powód:** darmowy plan Firebase (50 000 odczytów / 20 000 zapisów dziennie); pliki z wynikami przekraczają limit 1 MiB na dokument.

### D-002 · 2026-10-26 · Świece w Firestore: 1 dokument = 1 para × 1 miesiąc
- **Decyzja:** mapa `bars` kluczowana `ts`, zapis `PATCH` z `updateMask` (idempotentnie, bez odczytu), wyłączone indeksowanie `bars`.
- **Powód:** backfill ok. 200 zapisów zamiast ok. 100 tys.; bieżąca praca ok. 200 zapisów dziennie.
- **Odrzucone:** 1 świeca = 1 dokument (limit zapisów); tablice z `arrayUnion` (usuwa powtarzające się ceny).

### D-001 · 2026-10-26 · Apps Script co 5 min zamiast co godzinę
- **Decyzja:** wyzwalacz co 5 min; skrypt kończy bez zapytań, gdy oczekiwana świeca jest już zapisana.
- **Powód:** wyzwalacz godzinowy odpala się w dowolnej minucie godziny, więc pomiar latencji w sekundach nie miałby sensu.
