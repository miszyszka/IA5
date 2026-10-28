# Skan hipotez (D-037)

Pary: EURUSD, USDJPY · historia 2003-05-04 – 2026-10-26 · siatka standardowa · 0.9 s

- Dane: EURUSD 146,529 świec od 2003-05-04; USDJPY 69,251 świec od 2003-05-04.
- Odkrycie: 2003-05-04 – 2015-01-29; potwierdzenie: do 2020-12-12; **ostatnie 25% (OOS silnika) nie było liczone**.
- **Przetestowane reguły: 11,364** (z wystarczającą liczbą transakcji: 7,522).
- Próg odkrycia po korekcie FDR 5% na wszystkie reguły: p ≤ 5.27e-05 (t ≥ 3.88); odkrytych: 8.
- Potwierdzone w drugim okresie (średnia > 0, t ≥ 2): **0**.

Żadna reguła nie przeszła obu progów. To też wynik: w tej rodzinie reguł nie ma przewagi, która przetrwałaby uczciwe liczenie.

## Najbliżej progu (nie przeszły — dodatnie w obu okresach, za słabe po korekcie)

To NIE są odkrycia. Lista pokazuje, czego szukać przy większej liczbie par albo węższej siatce.

| # | reguła | n odkr. | pips netto odkr. | t odkr. | n potw. | pips netto potw. | t potw. | lata + | sąsiedzi + |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EURUSD short od 11:00 Londynu przez 2 h | 3059 | +1.33 | 3.1 | 1522 | +1.25 | 2.8 | 16/18 | 25% |
| 2 | EURUSD short od 08:00 Londynu przez 5 h | 3058 | +1.75 | 2.3 | 1522 | +1.73 | 2.3 | 15/18 | 100% |
| 3 | EURUSD short od 07:00 Londynu przez 6 h | 3060 | +1.79 | 2.2 | 1526 | +2.40 | 2.9 | 15/18 | 100% |
| 4 | EURUSD short od 10:00 Londynu przez 3 h | 3059 | +1.94 | 3.6 | 1522 | +1.17 | 2.2 | 15/18 | 75% |
| 5 | USDJPY: po ruchu > 1.5×ATR14·√k z 24 świec — za ruchem, 4 świec, sesja wszystkie | 168 | +6.69 | 2.0 | 79 | +7.35 | 2.0 | 9/14 | 60% |
| 6 | EURUSD short od 11:00 Londynu przez 2 h, tylko śr | 611 | +2.34 | 2.5 | 303 | +1.73 | 1.9 | 15/18 | 75% |
| 7 | USDJPY: po ruchu > 1.5×ATR14·√k z 24 świec — za ruchem, 3 świec, sesja wszystkie | 177 | +5.58 | 1.9 | 89 | +6.26 | 2.2 | 8/14 | 40% |
| 8 | EURUSD short od 09:00 Londynu przez 4 h | 3059 | +1.23 | 1.9 | 1522 | +1.94 | 3.0 | 13/18 | 100% |
| 9 | USDJPY short od 02:00 Londynu przez 5 h, tylko czw | 456 | +2.15 | 1.9 | 124 | +6.95 | 2.0 | 11/15 | 100% |
| 10 | EURUSD short od 11:00 Londynu przez 2 h, tylko pt | 612 | +1.70 | 1.9 | 305 | +1.90 | 2.1 | 16/18 | 25% |
| 11 | USDJPY: po ruchu > 1×ATR14·√k z 48 świec — za ruchem, 6 świec, sesja usa | 233 | +7.07 | 2.7 | 92 | +5.76 | 1.9 | 11/14 | 67% |
| 12 | USDJPY: po ruchu > 1×ATR14·√k z 48 świec — za ruchem, 12 świec, sesja usa | 180 | +6.81 | 1.8 | 76 | +7.11 | 1.8 | 9/14 | 67% |
| 13 | USDJPY: po ruchu > 1×ATR14·√k z 48 świec — za ruchem, 8 świec, sesja usa | 208 | +5.20 | 1.8 | 85 | +9.54 | 2.7 | 11/14 | 67% |
| 14 | USDJPY short od 00:00 Londynu przez 5 h, tylko czw | 455 | +2.69 | 2.0 | 121 | +5.45 | 1.7 | 10/15 | 100% |
| 15 | EURUSD short od 07:00 Londynu przez 6 h, tylko pt | 612 | +5.26 | 2.9 | 306 | +2.86 | 1.7 | 16/18 | 100% |