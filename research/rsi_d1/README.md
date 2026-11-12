# Poszukiwanie: RSI na świecach dziennych (2026-11-12)

Prośba Michała: progi wyprzedania/wykupienia RSI, sztywne TP/SL (ATR albo szczyt/dołek z X dni), wyjście po X dniach
na zamknięciu, stawka zależna od głębokości RSI / numeru świecy / liczby otwartych pozycji, piramidowanie; szukać
strategii zyskownej, ale stabilnej (mało okresów stratnych) i z dużą liczbą transakcji.

**Dane i model:** świece D1 Yahoo z gałęzi `data` po `daily.clean_d1` (8 par, 1996–2026-11-11), transakcje liczone
`engine.simulate` (wyjście `level` + limit dni) — ten sam model co karta strategii. Wejście rano (open następnego
dnia), wyjście po limicie na zamknięciu dnia, spread raz na transakcję, w ocenie dodatkowo **0,5 pipsa za noc** (swap, O5).
IS = wejścia przed 2019-05-09 (75% czasu, jak silnik), OOS = 2019-05-09 → 2026-11-11.

**Ocena stabilności (tylko IS):** miesięczne sumy zwrotów wszystkich par (waga × zwrot na nominale), Sharpe z miesięcy,
odsetek zyskownych kwartałów i lat, liczba transakcji, liczba par na plusie. Wagi znormalizowane do średniej 1 na IS,
żeby stawka nie udawała przewagi.

## Skala

| przebieg | wejścia | wyjścia | piramida | stawki | konfiguracji |
|---|---|---|---|---|---|
| 1 (`search_rsi.py`; wtedy jeszcze bez progu RSI14 45) | RSI 2/3/5/14 × 4 progi × zdarzenie/stan × bez trendu/SMA200 = 64 | 141 | 1/3/5 | 6 | 157 356 |
| 2 (`run2.py`) | + RSI14 45, sumy reguł, 3 filtry trendu = 138 | 141 | 1/3/5 | 6 | 335 016 |

Wyjścia: po 1–20 dniach; TP 0,5–3 × ATR14 / SL 1–3 × ATR14 / limit 5–20; sam SL 1,5–3 × ATR; SL pod dołkiem 3–20 dni
(± 0,5 ATR) z TP na szczycie, 1R, 2R albo bez TP. Stawki: stała, głębokość RSI, numer świecy w serii (rosnąco/malejąco),
liczba sygnałów w 5 poprzednich dniach ≈ otwarte pozycje (rosnąco/malejąco). **Razem ~492 tys. prób** — to liczba,
którą trzeba mieć w głowie, patrząc na DSR w karcie (karta liczy tylko 36 wariantów strategii).

## Co wyszło (IS)

- **Bez filtra trendu powrót RSI na D1 traci po kosztach:** dodatnich 16% konfiguracji, mediana Sharpe −0,24.
- **Z filtrem trendu** (kupuj wyprzedanie nad SMA200, sprzedawaj wykupienie pod nią) — ok. 50% dodatnich, najlepsze
  rodziny: RSI14 < 35–40 i sumy „RSI3 < 15 lub RSI14 < 40”, „RSI5 < 20 lub RSI14 < 40”. Sufit Sharpe z miesięcy ≈ 0,5–0,6.
- **Stawka:** mały wpływ. Lepiej dokładać przy kolejnej świecy wyprzedania (seria rosnąco: mediana 0,065) i przy
  kolejnych otwartych (0,079) niż zmniejszać (−0,015 / −0,037); głębokość RSI ≈ stała stawka.
- **Piramida:** 3–5 pozycji w parze nieco lepiej niż 1 (mediana 0,05 vs −0,02) — więcej transakcji z tej samej przewagi.
- **Tryb „stan”** (sygnał w każdej świecy za progiem) lepszy niż „zdarzenie” (pierwsza świeca) — działa jak piramida.
- **Wyjście po X dniach:** 1–2 dni na minusie, 5–10 dni najlepiej; SL w ATR bez TP najlepszy z wyjść cenowych,
  stop pod dołkiem z dnia sygnału jest za ciasny (przy wyprzedaniu dołek 3 i 20 dni to zwykle ten sam dzień).

Wybór na IS (najwięcej zyskownych kwartałów przy największej liczbie transakcji): **cfg 0, limit 3 dni** —
RSI3 < 15 lub RSI14 < 40, nad rosnącą SMA200 (short lustrzanie), stawka rośnie z kolejną świecą (1/2/3), PYRAMID 3,
wyjście po 3 dniach na zamknięciu. IS: 2 859 transakcji (124 rocznie), 63% zyskownych kwartałów, 70% zyskownych lat, 7/8 par.

## OOS (otwarty raz, po wyborze listy 12 konfiguracji w `strategies/examples/rsi_d1_powrot_w_trendzie.py`)

| cfg | limit | IS Sharpe | IS kw.+ | OOS trans. | OOS Sharpe | OOS kw.+ | OOS lata+ | OOS pary+ |
|---|---|---|---|---|---|---|---|---|
| **0** (wybór) | 3 | 0,49 | 63% | 1 177 | **−0,04** | 55% | 63% | 5 |
| 1 | 3 | 0,51 | 61% | 894 | −0,06 | 58% | 75% | 5 |
| 2 | 3 | 0,52 | 60% | 1 177 | −0,20 | 45% | 63% | 4 |
| 4 | 5 | 0,48 | 57% | 729 | 0,13 | 55% | 63% | 5 |
| 6 (stała) | 3 | 0,43 | 59% | 894 | 0,01 | 55% | 75% | 4 |
| 9 | 5 | 0,50 | 56% | 701 | **0,59** | 65% | 38% | 6 |
| 11 (dołek/szczyt) | 10 | 0,43 | 47% | 222 | −0,45 | 33% | 25% | 2 |

Pełne liczby: `eval_cfg.py … --oos`. Silnikiem (`ia5 run`, ten sam kod co Mac): werdykt 🔴 — wariant #1 IS według R
to cfg 11 z limitem 10 dni, OOS −12 pipsów na transakcję; percentyl benchmarku 100, PBO 0,14, DSR 1,00 (na 36
wariantach, nie na 492 tys.). Kapitał przy 5% depozytu: obsunięcie > 90% (waga do 3× × 3 pozycje × 8 par) — stąd
`SIZING = [1, 2, 3, 5]`.

## Wniosek

Stabilność z IS (Sharpe ≈ 0,5, ~60% zyskownych kwartałów) **nie przetrwała 2019–2026**: rodzina „wyprzedanie RSI w
trendzie D1” jest w OOS koło zera po kosztach i 0,5 pipsa za noc. Jedyny wyraźnie dodatni w OOS jest cfg 9 (RSI5 < 25,
TP 1,5 × ATR, SL 1 × ATR, stawka z liczbą otwartych) — ale wybranie go teraz byłoby wyborem po OOS (W1). Uczciwa droga:
zamrozić go w dashboardzie i patrzeć na forward (W4), albo nowa hipoteza.

## Uruchomienie

```bash
cd research/rsi_d1
python search_rsi.py ~/.ia5/data/d1_ready przebieg1.parquet      # ~7 min na 2 rdzeniach
python run2.py ~/.ia5/data/d1_ready przebieg2.parquet            # ~12 min
python eval_cfg.py ../../strategies/examples/rsi_d1_powrot_w_trendzie.py ~/.ia5/data/d1_ready [--oos]
```
Kolumny `oos_*` w plikach przebiegów są liczone, ale nie służyły do wyboru.

---

# Wersja 2 (2026-11-12 wieczór): diagnoza stratnych i zyskownych wejść

Prośba Michała: „przeanalizuj, co poszło nie tak, co łączy stratne i co zyskowne wejścia, co wzmocnić, a co uciąć;
nie musi być aż tyle transakcji”. Diagnoza i wybór **tylko na IS**, w dwóch połowach: A = 1996–2011, B = 2012–2019-05.

## 1. Co poszło nie tak — dane: zamknięcie D1 Yahoo od 2011 to w praktyce otwarcie dnia

Mediana |close − open| / zakres dnia: do 2009 ok. 0,5, **od 2011 ok. 0,02** (wszystkie 8 par, przełom 2010/2011).
Na EUR/USD 2025–2026 (porównanie z H1): D1 close różni się od ostatniego close H1 przed północą o 26 pipsów (mediana),
a **open następnego dnia — o 3,4 pipsa**. Skutek dla każdej strategii D1: RSI i inne wskaźniki „na zamknięciu” od 2011
liczą się z ceny z początku dnia (sygnał spóźniony o dzień względem wejścia), a wyjście „po X dniach na zamknięciu” wypada
w praktyce na otwarciu dnia. Na wersji 1 z poprawionym zamknięciem (close dnia t := open dnia t+1, `fix_close.py`)
wybór z IS (cfg 0, 3 dni) daje w OOS Sharpe **+0,31 zamiast −0,04** — duża część porażki wersji 1 to ten błąd danych.
Propozycja naprawy warstwy czyszczenia czeka na decyzję Michała (D-068); silnik i dane bez zmian.

## 2. Co łączy straty, a co zyski (populacja: każdy dzień wyprzedania/wykupienia, wynik w ATR po 5 dniach, poprawione zamknięcia)

| cecha w dniu sygnału | górny − dolny kwintyl, A | B | wniosek |
|---|---|---|---|
| DI+ − DI− w stronę transakcji | +0,11 | +0,15 | trend dzienny po naszej stronie = lepiej |
| RSI14 (płytsze wyprzedanie) | +0,06 | +0,18 | głęboki krach trwa dalej — **uciąć** |
| zakres dnia / ATR (dzień-szok) | −0,02 (10 dni: −0,13) | −0,14 (−0,25) | dni-szoki z newsów — **uciąć** |
| ile par z USD wyprzedanych naraz | −0,09 | −0,03 | szok dolarowy gorszy niż ruch własny pary (nie da się użyć: strategia widzi 1 parę) |
| momentum 60 dni w stronę transakcji | +0,11 | +0,07 | trend średni po naszej stronie = lepiej |

**Który dzień z rzędu** (RSI3 < 15 nad SMA200, dzień bez szoku, wynik po 3 dniach, ATR): 1. dzień +0,09 / +0,06,
2. +0,15 / +0,07, 3. +0,26 / +0,21, 4. i dalej +0,31 / +0,25 (A / B). **Pierwszy dzień wyprzedania to najsłabsze wejście** —
spadek często trwa; kolejne dni z rzędu to wyczerpanie sprzedających. To jest główna rzecz do wzmocnienia.

Sprawdzone i odrzucone: model uczony na wszystkich cechach (ridge, gradient boosting; A → B) — korelacja prognoz z wynikiem
≤ 0,03, czyli poza tym nic się w dziennych OHLC nie chowa; podążanie za trendem (trzymanie 20–120 dni) — przewaga ≈ koszt
nocy 0,5 pipsa, po swapach znika; filtr DI i „dno RSI14 ≥ 30” — bez poprawy w obu połowach.

## 3. Wersja 2: `strategies/examples/rsi_d1_seria_w_trendzie.py`

Wejście od 2. dnia z rzędu z RSI5 < 25 nad SMA200 (short lustrzanie), pomijając dni o zakresie ≥ 2 × ATR14; do 3 pozycji
w parze (kolejne dni dokładają); wyjście po 3 dniach na zamknięciu. 12 wersji (próg, który dzień, cięcie zakresu, stop,
stawka) × 3 limity (3/4/5 dni). Wybór: najwyższe **minimum** Sharpe z czterech prób (2 połowy IS × 2 wersje zamknięć) —
konfiguracje z RSI2 wypadały świetnie na jednej wersji danych i słabo na drugiej (kruche), RSI5 trzyma się na obu.
Siatka badania: `streak.py` (1 944 konfiguracje), wcześniej `refine.py` (960).

| | IS A | IS B | OOS (poprawione zamknięcia) | OOS (dane Yahoo jak w silniku) |
|---|---|---|---|---|
| cfg 0, 3 dni — Sharpe z miesięcy (z kosztem nocy) | 0,59 | 0,57 | **0,44** | 0,18 |
| cfg 0, 4 dni | 0,58 | 0,55 | 0,58 | 0,40 |
| transakcji rocznie (cfg 0, 3 dni) | 41 | 56 | 51 | 51 |
| zyskownych lat | 79% | 75% | 62% | 62% |

Wszystkie 36 wariantów są dodatnie w OOS na poprawionych zamknięciach (Sharpe 0,44–0,85); na danych silnika dodatnie
wszystkie poza dwiema wersjami z RSI2. Silnikiem (`ia5 run`): na danych Yahoo 🟡 4/5 (OOS +9,7 pipsa na transakcję,
percentyl 100, DSR 1,00, spread ×1,5 dodatni; PBO 0,62 ✘), na poprawionych 🟡 4/5 (OOS +21 pipsów, PBO 0,38 ✘).
Kapitał (cfg 0, 3 dni, dane Yahoo, depozyt 2%): CAGR ≈ 2,8%, obsunięcie z otwartymi −22%, Sharpe dzienny 0,51,
najdłużej pod wodą ok. 6 lat (2010-04 → 2016-04); na poprawionych: CAGR 4,2%, −22%, Sharpe 0,64, a najdłuższy okres pod wodą trwa **od 2023-02 do dziś** (3,7 roku; najgorszy rok obu wersji: 2024).
To nadal skromna przewaga — ale stabilna w obu połowach IS i w OOS, w przeciwieństwie do wersji 1.

## Dziennik otwarć OOS tej rodziny

1. 2026-11-12 popołudnie — lista 12 konfiguracji wersji 1, dane Yahoo (wynik: koło zera).
2. 2026-11-12 wieczór — ta sama lista na poprawionych zamknięciach (diagnoza błędu danych, nie wybór).
3. 2026-11-12 wieczór — lista 12 konfiguracji wersji 2, obie wersje danych, po wyborze na IS.

Uruchomienie (wersja 2): `python fix_close.py ~/.ia5/data/d1_ready d1_fixed`, potem `D1=d1_fixed python diag.py && python uni2.py`,
`python ml.py`, `python refine.py d1_fixed`, `D1=d1_fixed python streak.py`, `python eval_ab.py <strategia.py> d1_fixed [--oos]`.
