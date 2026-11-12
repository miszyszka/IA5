# Co steruje rynkiem — badanie strukturalne (2026-11-12, noc)

Prośba Michała: „przeanalizuj to jak rasowy trader — jak działa rynek, co nim steruje, jak to widać na wykresie; setki pomysłów
na wejścia i filtry; czas liczenia nie gra roli”. Zamiast kolejnych wskaźników — hipotezy o **przepływach**: kto i kiedy *musi*
handlować (koniec tygodnia, zamknięcie Nowego Jorku, fixing, koniec miesiąca) i czy cena po takim wymuszonym ruchu wraca.

## Dane (zasada D-036: szukamy na danych niezależnych, oceniamy na świecach Yahoo)

| zbiór | co | rola |
|---|---|---|
| A, B | świece H1 brokera MT, 8 par, 2012-11 → 2017-06 (A) i 2017-07 → 2022-03 (B) — `ejtraderLabs/historical-data` | odkrycie i potwierdzenie |
| D1 | świece dzienne Yahoo z poprawionym zamknięciem (D-068), A 2003–2011, B 2012–2019-05 | odkrycie na 16 latach |
| VIX | dzienny VIX (CBOE, `datasets/finance-vix`) | tylko filtr w badaniu |
| **C** | świece H1 Yahoo 2024-10 → 2026-11 po warstwie czyszczenia (te same, na których liczy Mac) | test — otwarty raz, dla listy z `LISTA_PRZED_TESTEM.md` |

Uwaga do danych brokera: to ceny bid. W godzinie rolowania (16:00–18:00 w Nowym Jorku) spread się rozszerza i bid spada —
w surowej sezonowości godzinowej wygląda to jak „efekt” na wszystkich parach (`s1_hours.py`). Wejścia w tych godzinach są
pominięte, a zamknięcia z tych godzin zastąpione ostatnią czystą ceną.

## Co sprawdziłem (liczba reguł = liczba prób)

| badanie | skrypt | prób | wynik |
|---|---|---|---|
| sezonowość godzinowa 8 par × 3 strefy | `s1_hours.py` | 576 | poza artefaktem rolowania zostaje znany spadek EUR i GBP rano w Europie (~1 pips/h < spread) |
| polowania na stopy: wczorajszy szczyt/dołek i zakres Azji, odrzucenie i wybicie | `s2_sweeps.py` | 17 | brutto ≈ 0 — wszystkie warianty tracą dokładnie spread |
| skaner H1: 46 wyzwalaczy × 19 filtrów × 15 godzin wejścia × 6 horyzontów | `scan.py`, `scan_read.py` | 78 660 | 49 zgodnych w A i B (losowo ≈ 9), tylko 16 większych od spreadu |
| skaner D1: 56 wyzwalaczy × 3 tryby trendu × 16 filtrów × 6 horyzontów | `d1scan.py`, `d1read.py` | 16 128 | 12 zgodnych (losowo ≈ 1), w tym cała rodzina „wejście w poniedziałek” |
| siatki szczegółowe: Azja, fixing, poniedziałek | `s3_asia.py`, `s4_fix.py`, `s5_monday.py`, `s5b.py` | ~190 | niżej |

Wyzwalacze: momentum 1 h … 20 dni (zwykłe i „duże”), sesje (Azja, Londyn rano, Nowy Jork rano), odległość od otwarcia dnia
i tygodnia, skraj zakresu, wyczerpany zakres dnia, świeca-szok, pin bar, objęcie, fałszywe wybicie, serie, RSI, siła walut
(z 8 par → 7 walut: ruch dolarowy, ruch własny waluty, para „najmocniejsza przeciw najsłabszej”), stały kierunek waluty.
Filtry: zmienność, trend, dzień tygodnia, koniec i początek miesiąca, ostatni dzień miesiąca, dni gotobi (Tokio), piątek z danymi
z rynku pracy USA, VIX wysoki/niski/skok/spadek, „dzień dolarowy” i „dzień spokojny”.

## Co wyszło

1. **Poniedziałkowy powrót — główne znalezisko.** Para rozciągnięta na zamknięciu piątku (RSI2 dziennych zamknięć) wraca
   w poniedziałek; w pozostałe dni tygodnia tego nie ma. Świece dzienne: −0,098 / −0,091 / −0,075 ATR dla kierunku rozciągnięcia
   w 2003–2011 / 2012–2019 / 2019–2026 (t −3,5 / −3,3 / −2,2). Świece godzinowe brokera (próg 15/85, wejście pon. 01:00 Londynu,
   20 h): **+8,3 pipsa netto w A (t 3,3), +5,1 w B (t 2,1)**, ok. 160 transakcji rocznie; płaskowyż dla progów 10–20 i trzymania
   20–30 h. Wejście o 07:00–08:00 Londynu już nie działa — powrót zaczyna się w nocy.
2. **Powrót w sesji azjatyckiej.** Ruch z 4 godzin przed północą w Londynie cofa się do otwarcia Londynu: +3,9 / +1,75 pipsa
   netto (t 2,1 / 2,3), ok. 330 transakcji rocznie, ale wąsko (okno 4 h tak, 2 h i 6 h nie).
3. **Fixing 16:00 w ostatnim dniu miesiąca.** Ruch przed fixingiem cofa się w 2 godziny: +2,2 / +2,0 pipsa netto, ale mało
   zdarzeń (t 1,1 / 1,6) — za słabe na strategię.
4. **Nie potwierdziło się:** polowania na stopy, wybicia zakresu Azji, kontynuacja po dużym dniu (jest w A, nie ma w B), dni
   gotobi w Tokio, ruch dolarowy kontra własny ruch waluty, para „najmocniejsza przeciw najsłabszej”. VIX jako filtr: niski VIX
   wzmacnia powrót w trendzie na danych Yahoo, na danych brokera słabiej, a wysoki działa niespójnie — za mało, żeby dodawać
   nową serię danych. Zmiana silnika (dostęp strategii do innych par) nie jest potrzebna — żadna cecha międzyparowa nie przeszła.
5. **Nie badane:** okrągłe poziomy (potrzebne dane drobniejsze niż H1), carry i różnice stóp (brak danych o stopach; model
   swapów to otwarta decyzja O5), pozycjonowanie (COT).

## Test na świecach Yahoo 2024-10 → 2026-11 (C, jedno otwarcie, `ctest.py`)

| | lista | n | netto pips | t | uwagi |
|---|---|---|---|---|---|
| poniedziałek 15/85, 20 h | 1 | 299 | **+2,6** | 0,7 | 6/8 par i 6/9 kwartałów na plusie; 30 h: +6,9 (t 1,7); 12 h: −0,9; przy spreadzie ×2: +0,9 |
| Azja 4 h, próg 0,5, 8 h | 2 | 627 | +1,9 | 0,4 | |
| fixing, ostatni dzień | 3 | 112 | +0,05 | 0,0 | niepotwierdzone |

Znak się zgadza, ale dwa lata to za mało, żeby to było rozstrzygnięcie; ostatnie pół roku jest płaskie. Silnik (`ia5 run` na tych
samych świecach): obie strategie 🔴, bo OOS karty to ostatnie 6 miesięcy (poniedziałek: IS +3,3…+9,6 pipsa, OOS −0,3…+0,6).

## Księga: trzy małe przewagi razem (`book.py`, `book_c.py`)

Poniedziałek (H1), Azja (H1) i seria wyprzedania w trendzie (D1, `rsi_d1_seria_w_trendzie.py`), każda przeskalowana do tej
samej zmienności miesięcznej. Korelacje miesięczne −0,22 … +0,29.

| | 2013–2022 (dane brokera; dla 1 i 2 to okres badania) | | | 2024-11 → 2026-10 (Yahoo, wagi z okresu badania) | |
|---|---|---|---|---|---|
| | Sharpe | kwartały + | lata + | Sharpe | kwartały + |
| poniedziałek | 1,25 | 78% | 8/10 | 0,35 | 5/9 |
| Azja | 0,89 | 70% | 7/10 | 0,92 | 6/9 |
| seria D1 | 0,58 | 49% | 6/10 | 1,44 | 6/9 |
| **księga** | **1,52** | **78%** | **9/10** | **1,30** | 6/9 |

Seria D1 policzona tu pierwszy raz na niezależnych danych z prawdziwymi zamknięciami dnia: Sharpe 0,58 — zgodnie z szacunkiem
z danych Yahoo (0,4–0,6). Pojedynczo żadna z tych przewag nie jest duża; razem dają stabilniejszą krzywą niż którakolwiek osobno.

## Uruchomienie

```bash
cd research/rynek && mkdir -p ej out
for p in EURUSD USDJPY GBPUSD EURGBP AUDUSD USDCHF USDCAD EURJPY; do
  curl -sS -o ej/$p.csv https://raw.githubusercontent.com/ejtraderLabs/historical-data/main/$p/${p}h1.csv; done
curl -sS -o vix.csv https://raw.githubusercontent.com/datasets/finance-vix/main/data/vix-daily.csv
ln -s ~/.ia5/data/h1_ready yh_ready                      # świece Yahoo H1 po czyszczeniu (okres C)
python s1_hours.py; python s2_sweeps.py; python scan.py ej && python scan_read.py     # ~1 min
D1_FIXED=../rsi_d1/d1_fixed python d1scan.py yahoo && python d1scan.py ej && python d1read.py
python s5b.py ej; python s3_asia.py ej; python s4_fix.py ej
python ctest.py                                          # okres C — lista z LISTA_PRZED_TESTEM.md
python book.py && python book_c.py
```
Dane (`ej/`, `yh_ready`, `vix.csv`, `out/`) nie trafiają do repo.
