# research/d1 — najbardziej stabilna strategia na samych świecach dziennych (D-070)

Wersja 1.0 · 2026-11-13 · wynik: `strategies/examples/d1_skladana.py`

Prośba Michała: „zaprojektuj najlepszą, najbardziej stabilną, wzrastającą strategię na świecach dziennych, biorąc pod uwagę
tylko je i całą dostępną bazę; policz tysiące kombinacji i pomysłów”.

## Dane

- **Yahoo D1 po naprawie zamknięć (D-068, `clean_d1` wersja 2)** — 8 par, 1996/2003 → 2026-11. Odcinki: **A** < 2012,
  **B** 2012 → 2019-05-09 (A + B = IS silnika), **O** od 2019-05-09 (OOS, 25% czasu).
- **Niezależne dane brokera** (świece H1 2012-11 → 2022-03 złożone w dni londyńskie; prawdziwe zamknięcie piątku) —
  tylko do potwierdzania, nigdy do wyboru.
- VIX i cechy międzyparowe były w pierwszym skanie, ale strategia ich nie używa (D7; kontrakt strategii widzi jedną parę).

## Kolejność pracy

1. **Skan strukturalny** (`scan.py`, `scan_read.py`): 75 924 reguły (wyzwalacz × zgodność z trendem × filtr × 1–20 dni),
   osobno A, B i dane brokera. Przy progu |t| ≥ 2,5 w A i ≥ 2,0 w B, z zyskiem netto w obu: 71 reguł, wszystkie z tym samym
   znakiem na danych brokera. Z własnych świec pary: 26 — prawie wszystkie to **wejście w poniedziałek przeciw ruchowi z
   końca tygodnia, wyjście tego samego dnia**.
2. **Siatka z progami** (`grid.py`, `grid_read.py`): 191 100 reguł (70 miar rozciągnięcia × 7 trybów trendu × 13 dni
   wejścia × 5 filtrów zmienności × 6 długości). min(t A, t B) ≥ 2: 107 reguł, z nich 94 dodatnie w obu połowach danych
   brokera. Trzy rodziny, każda dodatnia we wszystkich czterech odcinkach: poniedziałek, cofnięcie w trendzie,
   początek miesiąca. „Kontynuacja” w dni wtorek–piątek to złudzenie: ujemne t strony przeciwnej to sam koszt spreadu.
3. **Składniki silnikiem** (`csearch.py`, `comp.py`, `skl.py`): 312 + 2 592 + 3 312 = 6 216 konfiguracji przez
   `engine.simulate` (B8, B12, spread, 0,5 pipsa za noc), ocena = mniejszy z Sharpe’ów A i B.
   - poniedziałek: 38 z 39 miar dodatnich w obu połowach (płaskowyż); wyjście po 2 dniach psuje wynik;
   - cofnięcie w trendzie: RSI5 < 25 od 2. dnia nad SMA200, 3–4 dni — ten sam wybór co w `research/rsi_d1`;
   - początek miesiąca: **wąski** (39% konfiguracji dodatnich w obu połowach, działa tylko „pierwsze 2 dni, 2 dni
     trzymania”) — najsłabsze ogniwo, dlatego waga 0,5 i osobny wariant bez niego.
4. **Głosowanie miar w poniedziałek** (`pon_glosy.py`): 60 zestawów, wszystkie 0,47–0,88; wybrany środek (5 miar, ≥ 2 głosy).
5. **Złożenie** (`sklad.py`, `odpornosc.py`): wagi × PYRAMID, potem 19 odmian wokół wyboru — wszystkie 0,92–1,14
   (mniejszy z A, B). Ochronny stop 2 × ATR nie szkodzi; TP poniżej 1,5 × ATR szkodzi.
6. **Zamrożenie** kodu strategii (sha256 `94acd034…`), dopiero potem O i pełne liczenie (`eval.py`, `runfull.py`).
   Po otwarciu O zmieniono tylko jedną liczbę w opisie hipotezy (273 → 267 tys.), kod bez zmian.

## Wynik zamrożonej konfiguracji 0 (silnik IA5; Sharpe z miesięcznych sum, ze stresem 0,5 pipsa za noc)

| odcinek | transakcji / rok | netto / transakcję | Sharpe | lata na plusie | kwartały na plusie | pary na plusie |
|---|---|---|---|---|---|---|
| A (do 2011) | 189 | +13,0 pipsa | 1,09 | 75% | 69% | 8 / 8 |
| B (2012 → 2019-05) | 316 | +9,2 pipsa | 1,29 | 100% | 77% | 8 / 8 |
| **O — OOS (2019-05 → 2026-11)** | 289 | **+6,3 pipsa** | **0,73** | 75% | 71% | 7 / 8 |
| dane brokera 2012-11 → 2017-06 | — | — | 1,46 | — | — | — |
| dane brokera 2017-07 → 2022-03 | — | — | 0,72 | — | — | — |

Pełne liczenie (`runfull.py`, jak na Macu): werdykt 🟢; OOS +7,3 pipsa netto (bootstrap 95%: 4,1–10,4); benchmark
losowych wejść: percentyl 100; PBO 0,10; spread × 2: +9,1 pipsa (cała historia); koszt nocy 1 pips: +8,8 pipsa.
Kapitał przy depozycie 2%: CAGR 7,1%, największe obsunięcie −15,2% (−16,7% z otwartymi pozycjami),
najdłużej pod wodą 1 177 dni. **DSR = 1,0 jest zawyżony**: silnik widzi 5 wariantów, a prób było ok. 273 tys.

### Składniki osobno (zysk netto na transakcję w ATR14)

| składnik | A | B | O (OOS) | broker 2012–17 | broker 2017–22 |
|---|---|---|---|---|---|
| poniedziałek (1 dzień) | 0,080 | 0,061 | **−0,016** | 0,074 | 0,019 |
| cofnięcie w trendzie (3 dni) | 0,136 | 0,156 | 0,178 | 0,135 | 0,177 |
| początek miesiąca (2 dni) | 0,095 | 0,129 | 0,176 | 0,094 | 0,061 |

**Poniedziałek — najmocniejszy w IS — po 2019 nie zarabia.** Księga została na plusie dzięki dwóm pozostałym składnikom;
to jest argument za składaniem, ale też ostrzeżenie: przewaga, którą widzi wielu, znika.

OOS rok po roku (% nominału × waga): 2019 (od maja) −9,1 · 2020 +16,1 · 2021 +1,4 · 2022 +13,4 · 2023 +8,0 ·
2024 −2,2 · 2025 +23,2 · 2026 +8,9.

## Dziennik otwarć OOS

| data | co | wynik |
|---|---|---|
| 2026-11-13 | `d1_skladana.py`, 5 konfiguracji, po zamrożeniu | cfg 0: Sharpe 0,73; cfg 1: 0,77; cfg 2: 0,50; cfg 3: 0,68; cfg 4: 0,36 |

Wcześniejsze otwarcia tego samego odcinka dla innych strategii D1: `research/rsi_d1/README.md` (3) i skan z
`research/rynek/` (znak poniedziałkowego efektu w O był znany przed tą rundą).

## Ograniczenia

- **Piątek w starszej historii Yahoo** (do 2024-10): zamknięcie dnia = otwarcie następnego dnia handlu, więc „zamknięcie
  piątku” zawiera lukę weekendową (mediana 12 pipsów na EUR/USD) i jest tą samą ceną co wejście w poniedziałek. Na żywo
  i od 2024-10 zamknięcie piątku to ostatnia świeca H1. Dlatego składnik poniedziałkowy potwierdzałem na danych brokera.
- Wejście o północy w Londynie: spread bywa szerszy niż w tabeli (sekcja 2 `CLAUDE.md`); test spreadu × 2 jest w karcie.
- Swapy pominięte (O5); pozycja trwa średnio 1,9 nocy.
- Do 2003 r. w danych są 2 pary, komplet 8 par od 2006 r. — pierwsze lata odcinka A ważą mało.
- Liczone w piaskownicy Claude na świecach z gałęzi `data`; rozstrzyga liczenie na Macu.

## Jak powtórzyć

Dane robocze w `research/d1/data/` (poza repo): `d1raw/` = `candles_d1/` z gałęzi `data`, `h1raw/` = `candles/{PARA}/{ROK}.parquet`
jako `{PARA}_{ROK}.parquet`, `h1_ready/` = dane H1 do liczenia. Dane brokera i VIX jak w `research/rynek/`.

```
cd runner && export PYTHONPATH=../research/d1
python ../research/d1/build_v2.py ../research/d1/data/d1_v2      # D1 po naprawie zamknięć (D-068)
python ../research/d1/scan.py yahoo && python ../research/d1/scan.py ej && python ../research/d1/scan_read.py
python ../research/d1/grid.py yahoo && python ../research/d1/grid.py ej && python ../research/d1/grid_read.py
python ../research/d1/csearch.py pon; python ../research/d1/csearch.py trend; python ../research/d1/csearch.py mies
python ../research/d1/pon_glosy.py; python ../research/d1/sklad.py; python ../research/d1/odpornosc.py
python ../research/d1/eval.py ../strategies/examples/d1_skladana.py ../research/d1/data/d1_v2 [--oos]
python ../research/d1/runfull.py ../strategies/examples/d1_skladana.py
```

Pierwszy skan był liczony na równoważnym obejściu z `research/rsi_d1/fix_close.py` (zamknięcie = otwarcie następnego dnia),
zanim powstała wersja 2 warstwy czyszczenia; `scan.py` w repo czyta już `d1_v2`.
