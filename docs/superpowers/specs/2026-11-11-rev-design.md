# REV — kapitał w złotówkach rozłożony na przecenione waluty · projekt

Wersja 0.1 · 2026-11-11 · Status: **do zatwierdzenia przez Michała** · Po zatwierdzeniu: plan wykonania (`writing-plans`), potem etapy R0–R3.

---

## 1. Po co

Michał trzyma kapitał w złotówkach (na start wirtualnie **10 000 zł**) i chce go przenosić między walutami tak, żeby **z możliwie największym prawdopodobieństwem rósł w złotówkach**. Kapitał leży tam, gdzie waluty są teraz *względnie tanie i mają potencjał wzrostu*, a nie w jednej „najlepszej” walucie — *nie trzymamy wszystkich jajek w jednym koszyku*.

Najważniejsza część projektu to **metoda oceny „tania / droga”**: ma być możliwie przewidywalna i powtarzalna, a nie efektowna. Dlatego metodę wybiera się w **turnieju** spisanym z góry i sprawdzonym na ok. 20 latach historii (droga B, wybrana przez Michała 2026-11-11), według tych samych zasad uczciwości co reszta IA5 (W1–W4: wybór tylko na części historii, reszta jako sprawdzian, porównanie z losem, liczba prób w raporcie).

Wynik widać w nowej zakładce **REV**: gdzie dziś jest kapitał (słupki obok siebie), jak zmienia się jego wartość w złotówkach dzień po dniu (linia) i wszystkie przewalutowania.

## 2. Cele, czego nie robimy, czego się wystrzegamy

**Cele**
1. Dzienne świece walut w złotówkach (`{WALUTA}PLN=X` z Yahoo) z całą historią, dopisywane dzień po dniu jak D1 (D-053).
2. Metoda oceny przeceny wybrana w uczciwym turnieju, z werdyktem i raportem.
3. Wirtualny portfel na żywo: co wtorek o 08:00 przeliczenie i przewalutowania, codzienna wycena w PLN, pełny dziennik transakcji.
4. Zakładka REV z trzema widokami: słupki (gdzie kapitał dziś), linia (wartość w PLN), transakcje — i z wynikami badania.

**Czego nie robimy (poza zakresem)**
- Spreadów, opłat, odsetek od sald walutowych, podatków — model liczy sam kurs (decyzja Michała: „nie przyjmuj żadnych spreadów ani opłat”).
- Dźwigni, krótkiej sprzedaży, pożyczania walut.
- Prawdziwego handlu i połączenia z kontem / brokerem (G6). Michał wykonuje przewalutowania sam, jeśli zechce.
- Świec godzinowych dla kursów złotówkowych, innej waluty bazowej niż PLN.
- Danych spoza Yahoo (inflacja, stopy procentowe) — możliwe później jako R4, tylko po zmianie D7.

**Czego się wystrzegamy (porażka, nawet gdy „działa”)**
- **Ukryta koncentracja:** kapitał po cichu w dolarze przez HKD/AED/SAR/QAR albo w euro przez DKK, mimo limitu 50%.
- **Pułapka inflacji:** metoda, która uznaje lirę (albo inną walutę z wysoką inflacją) za wiecznie „tanią” i ładuje w nią kapitał, choć ona tanieje dalej.
- **Wybór metody pod wynik sprawdzianu** albo ciągłe dostrajanie po fakcie.
- **Fałszywa pewność:** pokazywanie „potencjału wzrostu” jako prognozy w procentach (K3: nie przewidujemy wyników) albo sklejanie historii z wynikiem na żywo, jakby to był jeden wynik.
- **Naruszenie reszty IA5:** REV nie zmienia silnika FX, zasad B1–B12 ani strategii.

## 3. Ograniczenia (żelazne zasady, których to dotyczy)

| Zasada | Co znaczy dla REV | Co trzeba zmienić |
|---|---|---|
| D7 — tylko Yahoo, dwie serie, lokalnie tylko 8 par | kursy PLN to **trzecia seria Yahoo**: D1, cała historia, tylko do REV | dopisać serię do D7; `yahoo_pln/` i `pln_ready/` do listy dozwolonych na Macu (D-041) |
| D7a — świeca D1: znacznik = północ w strefie Yahoo, tylko dni zamknięte, czyszczenie | bez zmian — kursy PLN przechodzą tę samą warstwę (`daily.clean_d1`) | — |
| B3 — spread od każdej transakcji | REV **bez spreadów i opłat** | wyjątek tylko dla REV (nowa sekcja R) |
| W1–W4 — OOS 25%, liczba wariantów i DSR, benchmark losowy, zamrożenie | obowiązują w wersji dla portfela tygodniowego | opis w sekcji R |
| Z1–Z4 — budżet Firestore | 1 dokument = 1 waluta × 1 rok (jak D1); dashboard 0 nowych odczytów | szacunek w commicie (Z4) |
| K3 — nie podajemy przewidywanych wyników | ocena przeceny to liczba porządkująca waluty, nie prognoza zysku | — |
| G4 — nie usuwamy danych bez zgody | waluty odrzucone przy przyjęciu w ogóle nie są zapisywane | — |
| Design D-019 | zakładka w tym samym stylu: jeden akcent, kolory tylko jako stan | — |

Bez nowych bibliotek: numpy, pandas po stronie Maca; ECharts po stronie strony (już w `web/vendor/`).

## 4. Rozważone podejścia

| | Na czym polega | Za | Przeciw |
|---|---|---|---|
| **A.** Jedna metoda z literatury od razu na żywo | np. przecena + filtr trendu, bez porównań | najszybsze | brak dowodu, że działa na kursach złotówkowych; nie wiadomo, czy lepsze od równego podziału |
| **B. Turniej metod spisanych z góry** ✅ | ~12 wariantów (przecena, trend, ich połączenie × 2 sposoby podziału) + przełącznik; odtworzenie każdego wtorku od ok. 2008; wybór na pierwszych 75%, sprawdzian na ostatnich 25%; porównanie z równym podziałem, z trzymaniem PLN i z losowymi podziałami | uczciwe, zgodne z IA5 (W1–W3); widać, czy jakakolwiek metoda bije prosty podział | więcej pracy; może wyjść, że nic nie bije równego podziału |
| **C.** Metoda sama się przełącza | co kwartał bierze tę, która ostatnio szła najlepiej | brzmi najmądrzej | najłatwiej o wynik z przypadku, najtrudniej ocenić — **dlatego jest w turnieju B jako 13. zawodnik**, a nie osobną drogą |

**Wybór Michała: B** (2026-11-11, „B”).

## 5. Ustalone z Michałem (jego słowami)

1. Waluty: AED, AUD, CAD, CHF, CZK, DKK, EUR, GBP, HKD, HUF, ILS, JPY, MXN, NOK, NZD, QAR, RON, SAR, SEK, SGD, THB, TRY, USD, ZAR — **bez RUB** („omiń rubla”) i **bez rzadkich kursów** („omiń rzadkie kursy”).
2. Waluty o sztywnym kursie liczone razem z kotwicą do limitu — „KONIECZNIE”: **blok USD** (USD, HKD, AED, SAR, QAR) i **blok EUR** (EUR, DKK).
3. **Przeliczenie we wtorek o 08:00** (Europe/Warsaw) na podstawie **zamkniętej świecy poniedziałkowej** — żeby to, co zmieniło się w weekend, było już w cenie.
4. **PLN jest pełnoprawnym koszykiem** (wariant A): gdy wszystko jest drogie, kapitał może zostać w złotówkach.
5. **Limit: żaden koszyk > 50% kapitału** (waluta, blok albo PLN).
6. Podział **proporcjonalny do oceny przeceny**, nie wszystko w jedną walutę.
7. Bez spreadów i opłat. Wszystkie transakcje zapisane. Wykres liniowy wartości w PLN dzień po dniu. Słupki obok siebie: gdzie kapitał dziś.
8. Kapitał startowy: 10 000 zł.

## 6. Projekt

### 6.1 Waluty, koszyki, bloki

- **Kandydaci:** 24 waluty z punktu 5.1. Ticker Yahoo: `{WALUTA}PLN=X` (np. `EURPLN=X`, `USDPLN=X`, `JPYPLN=X`). Cena = ile złotych za 1 jednostkę waluty (skalę — np. czy JPY jest za 1, czy za 100 — sprawdza test krzyżowy, 6.2).
- **„Rzadki kurs” — reguła przyjęcia (moja decyzja, do zmiany):** waluta trafia do REV, gdy w Yahoo ma (a) co najmniej **10 lat** historii dziennej, (b) świeżą świecę (nie starszą niż 5 dni roboczych), (c) mniej niż **5% dni bez ruchu** (zamknięcie = poprzednie zamknięcie albo O = H = L = C) w ostatnich 5 latach. Reguła jest sprawdzana raz, przy pierwszym pobraniu; odrzucona waluta nie jest zapisywana, a powód trafia do `meta/status.pln.rejected`. **Lista przyjętych walut jest potem zamrożona** w konfiguracji i w `DECISIONS.md` — zbiór walut nie zmienia się po cichu w trakcie. Spodziewam się odrzucenia części z AED, QAR, SAR, THB, ILS, ale nie da się tego sprawdzić z sesji Claude (Yahoo zablokowane) — rozstrzyga pierwsze pobranie.
- **Bloki (sztywny kurs):** blok USD = USD + przyjęte z {HKD, AED, SAR, QAR}; blok EUR = EUR + DKK (jeśli przyjęta). Blok to **jeden koszyk**: ocena liczona na kotwicy (USD, EUR), kapitał bloku trzymany w kotwicy, limit 50% liczony na cały blok, w koszyku porównawczym (6.3) blok liczy się raz. Członkowie bloku są w danych i w tabeli kursów, ale nie są osobną pozycją (moja decyzja: trzymanie HKD zamiast USD nic nie zmienia poza szumem w paśmie). **Kontrola pęknięcia kursu:** gdy członek odbiega od kotwicy o > 3% albo korelacja tygodniowych zmian z kotwicą w ostatnim roku < 0,95 — ostrzeżenie w przeglądzie zdrowia i decyzja Michała (blok mógł przestać istnieć).
- **Koszyki:** wszystkie przyjęte waluty spoza bloków + blok USD + blok EUR + **PLN**. Przy pełnej liście to ok. 20 koszyków.

### 6.2 Dane — kursy złotówkowe (etap R0)

Ta sama droga co świece D1 (D-053), osobna seria, żeby nie ruszać kontroli 8 par FX:

- **Apps Script:** `backfillPLN()` ręcznie raz — dla każdego kandydata `interval=1d&period1=0`, reguła przyjęcia (6.1), zapis przyjętych. Potem `tick` wywołuje `tickPLN_()` po `tickD1_()` (osobny `try`, błąd nigdy nie zatrzymuje H1 ani D1), z tym samym wzorcem: po północy w Londynie dopisuje zamknięty dzień, ponawia co 15 min, nadpisuje 4 ostatnie dni (Yahoo koryguje), bez zapisu, gdy nic nowego. Rozsądnie: `runD1_` sparametryzowane listą, kolekcją i polem statusu zamiast kopii kodu.
- **Firestore:** `candles_pln/{WALUTA}_{RRRR}` — pola jak `candles_d1` (`pair`, `year`, `tz`, `bars { ts: [o,h,l,c] }`, `updatedAt`); `meta/status.pln` — `{ tz, totalBars, lastRun, currencies: { WALUTA: { firstDay, lastTs, lastDay, count, flags, savedAt } }, rejected: { WALUTA: powód } }`.
- **Budżet (Z4):** backfill ≈ 20 walut × ~22 lata ≈ **450 zapisów raz**; potem ≈ **20 zapisów dziennie** + 1 status. Mac i Actions czytają tylko waluty z nowszą świecą: ≤ 2 × 20 odczytów dziennie. Dashboard: **0 nowych odczytów** (pole `pln` w już nasłuchiwanym `meta/status`, kilka KB).
- **Mac (`ia5 start`) i Actions (`ia5 live`):** kopia `~/.ia5/data/yahoo_pln/{WALUTA}.parquet` (surowa, D4) → warstwa czyszczenia `daily.clean_d1` → `~/.ia5/data/pln_ready/` (jak `d1_ready`, źródło „yahoo”). Push `candles_pln/{WALUTA}.parquet` + `manifest.json` na gałąź `data` (tylko gdy się zmieniło). Actions bierze historię z gałęzi `data`, najnowsze dni z Firestore — jak D1 w `cmd_live`.
- **Przegląd zdrowia:** nowa kontrola **„Kursy złotówkowe (REV)”** — przyjęte waluty obecne, świeże (ostatni dzień roboczy), kopia = Firestore, **test krzyżowy** z dziennymi świecami FX tam, gdzie się da (EURPLN ÷ USDPLN ≈ EURUSD, GBPPLN ÷ USDPLN ≈ GBPUSD, USDPLN ÷ JPYPLN ≈ USDJPY, USDPLN ÷ CHFPLN ≈ USDCHF, USDPLN ÷ CADPLN ≈ USDCAD, AUDPLN ÷ USDPLN ≈ AUDUSD — mediana i p99 odchylenia w %), kotwice bloków. Zgodnie z D-060: zielono z liczbami, gdy wszystko obsłużone; ostrzeżenie tylko, gdy jest coś do zrobienia (waluta stoi > 5 dni roboczych, blok pękł, skala kursu się nie zgadza).
- **Stats:** kursy złotówkowe w tabeli/kalendarzu tak jak D1 (szczegóły — budujący).

### 6.3 Metoda — turniej (etap R1, najważniejszy)

**Rytm i ceny.** Decyzja co tydzień: wtorek 08:00 Europe/Warsaw. Cena decyzji i cena wymiany = **zamknięcie ostatniej zamkniętej świecy D1 przed wtorkiem 08:00** (normalnie poniedziałek; w święto — ostatni wcześniejszy dzień z notowaniem). Wycena portfela: każde zamknięcie dnia roboczego. Brak świeży dla waluty: zamknięcie nie starsze niż 5 dni roboczych; starsze → waluta „bez notowań” w tym tygodniu: jej stan zostaje bez zmian, reszta kapitału jest przeliczana bez niej.

**Ceny względem koszyka (żeby PLN był oceniany tak samo jak inne).** Niech `y_i(t) = ln(PLN za 1 jednostkę i)` na wtorkowej cenie, `y_PLN ≡ 0`. Indeks koszyka `b(t)` łańcuchowo: `b(t) − b(t−1)` = średnia zmian `y_j` wszystkich koszyków z notowaniem w obu tygodniach (blok raz, PLN włącznie). Cena względna `x_i(t) = y_i(t) − b(t)`; dla PLN `x_PLN = −b(t)` (złoty tani, gdy słaby wobec reszty). Łańcuchowanie sprawia, że dołączenie nowej waluty nie robi skoku w indeksie.

**Oceny (spisane z góry; dodatnia = tania / rosnąca):**

| Symbol | Nazwa po ludzku | Wzór |
|---|---|---|
| `V3`, `V5` | **Przecena** wobec własnego trendu z 3 / 5 lat | regresja liniowa `x_i` na czasie w oknie 156 / 260 tygodni do `t` włącznie; `V = −(x_i(t) − trend(t)) / σ_reszt`. Trend liniowy „zjada” stałą inflację (lira tanieje stale → to trend, nie przecena) |
| `M3` | **Trend krótki** — 3 miesiące | `(x_i(t) − x_i(t−13)) / (σ_tyg · √13)`, `σ_tyg` = odchylenie tygodniowych zmian `x_i` z 52 tygodni |
| `M12` | **Trend roczny** bez ostatniego miesiąca | `(x_i(t−4) − x_i(t−52)) / (σ_tyg · √48)` |
| `V3+M3`, `V5+M3` | **Tania i przestała tanieć** | `½·z(V) + ½·z(M3)`, `z` = standaryzacja w przekroju koszyków w tygodniu `t` |

**Podział (dwa sposoby):**
- **P — proporcjonalnie do oceny:** `s_i = S_i − średnia_j S_j` (w przekroju koszyków); `w_i ∝ max(s_i, 0)`. Kapitał dostaje mniej więcej tańsza połowa, im taniej, tym więcej.
- **R — według miejsca w rankingu:** `w_i ∝ max((N+1)/2 − miejsce_i, 0)` (miejsce 1 = najtańszy). Ta sama tańsza połowa, ale wagi nie zależą od skrajnych ocen — odporniej na pojedynczy wyskok.
- **Limit 50% (każdy koszyk, blok w całości):** waga > 50% ucinana do 50%, nadwyżka rozdzielana proporcjonalnie na pozostałe koszyki z dodatnią wagą; gdy takich brak — na kolejne w rankingu według R. Zawsze suma = 100%, maks. ≤ 50%.
- **Pasmo bez przewalutowania (moja decyzja, stała dla wszystkich wariantów):** koszyk, którego cel różni się od obecnego udziału o mniej niż **2 p.p.**, zostaje bez zmian; różnicę rozkłada się na koszyki, które i tak się zmienia (proporcjonalnie do celu, z limitem 50%). Bez opłat pasmo nie jest potrzebne dla wyniku — chodzi o to, żeby przewalutowania dało się wykonać ręcznie, bez kilkunastu drobnych zmian co tydzień. „Ewentualne przewalutowania” z opisu Michała.

**Warianty turnieju: 6 ocen × 2 podziały = 12 + przełącznik = 13.**
- **Przełącznik (droga C jako zawodnik):** co 13 tygodni wybiera spośród 12 ten, który miał najwyższy wskaźnik IR (niżej) w ostatnich 156 tygodniach, i stosuje go przez kolejne 13. Zanim ma 156 tygodni historii — równy podział.

**Wspólny okres.** Wszystkie warianty liczone na tych samych wtorkach: od pierwszego wtorku, w którym co najmniej 8 koszyków ma 260 tygodni historii, do ostatniego zamkniętego poniedziałku. Koszyk wchodzi do turnieju — do wszystkich wariantów i benchmarków naraz — dopiero, gdy ma 260 tygodni historii (najdłuższe okno w turnieju), więc w każdym tygodniu wszyscy grają na tych samych koszykach. PLN jest w turnieju od początku. Indeks `b(t)` liczony jest ze wszystkich koszyków z notowaniem w obu tygodniach, niezależnie od tego, czy są już w turnieju. Prawdopodobny start: ok. 2009–2011 (zależnie od historii Yahoo). Na żywo wszystkie przyjęte waluty mają ≥ 10 lat historii, więc grają od pierwszego wtorku.

**Wybór (spisany z góry, W1).**
- **IS** = pierwsze 75% wtorków wspólnego okresu, **OOS** = ostatnie 25%.
- Kryterium: **IR wobec równego podziału** = średnia tygodniowa nadwyżka log-zwrotu nad równym podziałem / jej odchylenie, w skali roku. Wygrywa najwyższy IR na IS. OOS jest liczony **raz** dla wszystkich i zapisany w dzienniku OOS (`oos_ledger.json`, jak D-044); nie służy do wyboru.
- **Równy podział** = 1/N na każdy koszyk (z PLN), przeliczany co wtorek, bez pasma.

**Walidacja i werdykt** (progi z góry, jak sekcja 9 CLAUDE.md):

| Co | Jak |
|---|---|
| Przypadek | **≥ 1000 losowych podziałów:** co wtorek wagi z rozkładu Dirichleta(1) na te same koszyki, z limitem 50% i pasmem 2 p.p. → percentyl nadwyżki zwycięzcy (W3) |
| Liczba prób | 13 wariantów w raporcie; **DSR** na tygodniowych nadwyżkach (W2) |
| Przeuczenie | **PBO** metodą CSCV (16 bloków) na 13 wariantach; wynik w latach (walk-forward roczny) |
| Niepewność | bootstrap blokowy 95% CI średniej tygodniowej nadwyżki |
| Opóźnienie | ten sam wariant, wymiana po **zamknięciu wtorku** zamiast poniedziałku — wynik musi zostać dodatni (odpowiednik testu spreadu) |
| To, czego chce Michał | % okien 52-tygodniowych z **wzrostem kapitału w PLN** i % okien **lepszych od równego podziału**; największy spadek (z wyceny dziennej); udział każdej waluty w wyniku |
| Pułapka inflacji | średnia waga TRY (i innych walut z trendem spadkowym) w czasie — widoczna w raporcie |

- 🟢 gdy jednocześnie: nadwyżka OOS nad równym podziałem > 0, percentyl losowych ≥ 95, DSR ≥ 0,95, PBO < 0,3, nadwyżka dodatnia z opóźnieniem.
- 🔴 gdy nadwyżka OOS ≤ 0 albo percentyl < 80. 🟡 w pozostałych przypadkach.
- **Gdy wyjdzie 🔴 (moja decyzja, do zmiany):** na żywo i tak działa zwycięzca IS, ale zakładka mówi wprost „metoda nie pokonała równego podziału na sprawdzianie” i obok pokazuje równy podział na żywo. Michał sam decyduje, czy w ogóle się tym kierować.
- **Brak look-ahead:** ocena w tygodniu `t` liczona tylko z cen do `t`; test jak detektor B2 — obcięcie danych w losowych punktach i zaburzenie przyszłości nie zmienia żadnej wcześniejszej oceny ani wagi.

**Zamrożenie (W4).** Zwycięzca jest zamrażany: id wariantu + parametry + hash kodu + `REV_VERSION` + data. Zmiana metody = nowa wersja, nowy start portfela na żywo, wpis w `DECISIONS.md`. Turnieju nie powtarza się na tym samym OOS w poszukiwaniu lepszego wyniku.

**Komenda:** `ia5 rev badanie` (lokalnie na Macu, przy wyłączonym `ia5 start` albo w nim — budujący) → `~/.ia5/rev/research/` i gałąź `data` `rev/research.json` + `rev/report.md` (raport dla Claude, tabele markdown jak 10.6).

### 6.4 Portfel na żywo (etap R2)

- **Start:** pierwszy wtorek 08:00 po zamrożeniu metody; 10 000 zł w PLN, w tym wtorku pierwszy podział.
- **Co wtorek ≥ 08:00:** gdy jest zamknięta świeca poniedziałku (albo reguła „bez notowań” z 6.3): oceny zamrożoną metodą → cele z limitem i pasmem → przewalutowania po cenie z poniedziałkowego zamknięcia → wpis do dziennika. Data transakcji = wtorek 08:00, cena = zamknięcie poniedziałku (zapisana w wierszu).
- **Codziennie:** po każdym zamkniętym dniu roboczym punkt wyceny: Σ jednostek × zamknięcie (PLN = 1). Obok liczony **równy podział na żywo** od tej samej daty startu (do porównania).
- **Dziennik:** wiersz na każdą zmianę koszyka: wtorek, waluta, jednostki przed → po, kurs (PLN za 1), wartość zmiany w zł. Suma wartości zmian w jednym przeliczeniu = 0 (bez opłat — test). **Rozliczonych wierszy się nie zmienia** (jak F7); późniejsza korekta kursu w Yahoo nie przepisuje dziennika ani wyceny.
- **Stan:** `rev/state.json` na gałęzi `data` — metoda (zamrożona), start, jednostki w koszykach, dziennik, seria wyceny, równy podział, oceny i cele z ostatniego przeliczenia, ostatni przetworzony dzień, termin następnego przeliczenia. Po przerwie nadrabianie dzień po dniu, w kolejności — wynik taki sam jak bez przerwy (test, jak F8).
- **Gdzie liczy:** `ia5 live` w GitHub Actions (już uruchamiane co godzinę i po komplecie świec), Mac przejmuje według tej samej reguły co inwestorzy (D-052: tylko gdy Actions nie działało od 2 h). Firestore: tylko odczyt świeżych kursów PLN (6.2), żadnych zapisów stanu.
- `REV_VERSION` — zmiana logiki = podbicie wersji (jak `FOREST_VERSION`).

### 6.5 Zakładka REV (etap R3)

Piąta zakładka: **Strategie | Stats | Inwestorzy | FOREST | REV**. 0 odczytów Firestore — wszystko z `rev/` na gałęzi `data`. Styl D-019 (linia kapitału w akcencie, zysk/strata ze znakiem, kolory tylko jako stan, bez wygładzania).

```
REV · metoda: Przecena 5 lat + trend 3 mies., ranking · 🟡 4/5           następne przeliczenie: wt 08:00 (za 5 d 20 h)
Kapitał teraz  10 412 zł  (+412 zł · +4,1% od 12.11.2026)     Równy podział  10 198 zł (+1,98%)

Gdzie jest kapitał dziś                                          ── 50%
 CHF ███████████████ 2 950 zł 28%
 PLN ██████████ 1 880 zł 18%
 USD*████████ 1 560 zł 15%    *blok USD: USD, HKD
 NOK ██████ 1 170 zł 11%   …

Kapitał w złotówkach (dzień po dniu)   ── REV  ┄┄ równy podział  ··· 10 000 zł   ▲ wtorki z przewalutowaniem

Ranking dziś:  waluta · przecena · trend · cel % · teraz % · zmiana we wtorek
Transakcje:    data · waluta · kupno/sprzedaż · ilość · kurs · wartość zł        [CSV]
Badanie metody (historia, nie wynik na żywo): turniej 13 wariantów (IS | OOS), walidacja, wykres od ok. 2010 z granicą IS/OOS, [Kopiuj raport dla Claude]
```
(liczby w szkicu są zmyślone — tylko układ)

### 6.6 Proponowana nowa sekcja żelaznych zasad „REV (R)” w CLAUDE.md

> Do wpisania w etapie R0 razem z D-062; zatwierdzenie tego dokumentu przez Michała = zgoda na tę treść.

- **R1. Waluty i koszyki:** lista przyjętych walut zamrożona w konfiguracji (reguła przyjęcia przy pierwszym pobraniu). Bloki o sztywnym kursie — USD (USD, HKD, AED, SAR, QAR) i EUR (EUR, DKK) — to jeden koszyk, trzymany w kotwicy. PLN jest koszykiem. Zmiana listy lub bloków = wpis w `DECISIONS.md`.
- **R2. Rytm:** przeliczenie we wtorek 08:00 Europe/Warsaw po cenie zamknięcia ostatniej zamkniętej świecy D1 (poniedziałek); wycena codziennie na zamknięciu.
- **R3. Bez kosztów:** bez spreadów, opłat, odsetek i podatków — wyjątek od B3 tylko dla REV. Bez dźwigni i krótkiej sprzedaży.
- **R4. Limit:** żaden koszyk (waluta, blok, PLN) nie ma więcej niż 50% kapitału po żadnym przeliczeniu.
- **R5. Uczciwość:** oceny tylko z przeszłości (test obcięcia danych). Metoda wybierana na pierwszych 75% tygodni, ostatnie 25% otwarte raz (dziennik OOS); porównanie z równym podziałem, PLN i ≥ 1000 losowymi podziałami; liczba wariantów i DSR w raporcie.
- **R6. Zamrożenie:** na żywo działa zamrożona metoda (hash kodu + parametry + data); zmiana = nowa `REV_VERSION`, nowy start, wpis w `DECISIONS.md`. Historia i wynik na żywo pokazywane osobno.
- **R7. Dziennik:** każde przewalutowanie zapisane; rozliczonych wierszy się nie zmienia; po przerwie nadrabianie po kolei z tym samym wynikiem.
- **R8. Budżet:** dashboard 0 odczytów Firestore dla REV; Mac i Actions czytają tylko waluty z nową świecą.

## 7. Etapy — żeby nic się nie pogubiło

Każdy etap: testy zielone → push → `STATUS.md` → działa na żywej stronie (jak sekcja 13 CLAUDE.md). Ten podział wchodzi też do `docs/ROADMAP.md` i tabeli etapów w CLAUDE.md (jako E8 REV z podetapami).

| Etap | Zakres | Gotowe, gdy | Krok Michała |
|---|---|---|---|
| **R0 Dane** | Apps Script `backfillPLN` + `tickPLN_`, Firestore, kopia i czyszczenie na Macu i w Actions, gałąź `data`, kontrola zdrowia, Stats; D-062 + CLAUDE.md (D7, sekcja R) | lista przyjętych walut w `DECISIONS.md`, kontrola „Kursy złotówkowe” zielona, nowe dni dopisują się same | wkleić Code.gs, uruchomić raz `backfillPLN()`, `git pull` + `uv tool install … --force` + restart |
| **R1 Badanie metody** | `ia5 rev badanie`: oceny, podziały, limit, pasmo, 13 wariantów, walidacja, werdykt, raport, zamrożenie; zakładka REV w wersji „Badanie metody” | raport z werdyktem widoczny na stronie, metoda zamrożona | uruchomić `ia5 rev badanie` (albo samo przy `ia5 start`) |
| **R2 Portfel na żywo** | stan, wtorkowe przeliczenie, wycena dzienna, dziennik, równy podział na żywo; `ia5 live` + Mac zapasowo | pierwszy wtorek przeliczony automatycznie, wycena dopisuje się dzień po dniu | — |
| **R3 Zakładka REV** | słupki, linia, ranking, transakcje + CSV, odliczanie do wtorku, badanie metody | wszystko z 6.5 na żywej stronie | — |
| **R4 Później (tylko na życzenie)** | mail we wtorek z listą przewalutowań (jak D-051); dane spoza Yahoo: inflacja (kurs realny zamiast trendu), stopy procentowe — wymaga zmiany D7 | — | decyzja Michała |

## 8. Zostawione budującemu

- Nazwy modułów i podział kodu (np. `runner/ia5/rev.py`, `rev_data.py`), format plików stanu i badania, algorytm limitu (wodne wypełnianie lub inny o tych samych własnościach).
- Refaktoryzacja `runD1_` w Apps Script (parametr: lista, kolekcja, pole statusu) albo osobna funkcja — byle z testem w symulacji Node (`tests/test_apps_script.py`).
- Czy `ia5 rev badanie` uruchamia się sam przy `ia5 start`, gdy brak badania albo zmieniła się `REV_VERSION` (jak FOREST), czy tylko ręcznie.
- Dokładny układ zakładki w ramach D-019 i szkicu 6.5; kolejność dostarczania widoków (część zakładki może przyjść już w R1).
- Wykorzystanie istniejących funkcji `validate.py` (DSR, PBO, bootstrap), jeśli pasują do serii tygodniowych.
- Testy: brak look-ahead, limit 50% i bloki w każdym tygodniu, suma transakcji = 0, nadrabianie = bez przerwy, łańcuchowy indeks koszyka bez skoku przy dołączeniu waluty, zgodność skali kursów z testem krzyżowym.

## 9. Moje decyzje w tym dokumencie (do sprawdzenia przez Michała)

1. Reguła „rzadkiego kursu”: ≥ 10 lat historii, świeża świeca, < 5% dni bez ruchu; lista zamrożona po pierwszym pobraniu.
2. Blok trzymany w kotwicy (USD, EUR); ostrzeżenie, gdy sztywny kurs pęknie.
3. Ceny względem łańcuchowego koszyka wszystkich koszyków z PLN — dzięki temu PLN jest oceniany tą samą miarą.
4. Przecena = odchylenie od **trendu liniowego** z 3/5 lat (nie od średniej) — ochrona przed pułapką inflacji.
5. Zestaw 13 wariantów i kryterium wyboru IR wobec równego podziału na IS.
6. Pasmo 2 p.p. bez przewalutowania.
7. Waluta bez notowań > 5 dni roboczych zostaje bez zmian w danym tygodniu.
8. Przy werdykcie 🔴 na żywo i tak działa zwycięzca IS, z wyraźnym komunikatem i równym podziałem obok.
9. Liczy GitHub Actions, Mac zapasowo (jak inwestorzy).
