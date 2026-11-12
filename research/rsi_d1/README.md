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
