# Skan hipotez (D-037)

Pary: EURUSD, USDJPY · historia 2003-05-04 – 2026-10-26 · siatka duża · 10.9 s

- Dane: EURUSD 146,529 świec od 2003-05-04; USDJPY 69,251 świec od 2003-05-04.
- Odkrycie: 2003-05-04 – 2015-01-29; potwierdzenie: do 2020-12-12; **ostatnie 25% (OOS silnika) nie było liczone**.
- **Przetestowane reguły: 312,640** (z wystarczającą liczbą transakcji: 46,860).
- Próg odkrycia po korekcie FDR 5% na wszystkie reguły: p ≤ 5.07e-06 (t ≥ 4.41); odkrytych: 7.
- Potwierdzone w drugim okresie (średnia > 0, t ≥ 2): **1**.

## Potwierdzone reguły (ranking: mniejsze z t odkrycia i t potwierdzenia)

| # | reguła | n odkr. | pips netto odkr. | t odkr. | n potw. | pips netto potw. | t potw. | lata + | sąsiedzi + |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EURUSD long od 01:00 Londynu przez 7 h, tylko miesiąc 12 | 267 | +8.06 | 4.5 | 118 | +4.17 | 2.8 | 17/18 | 100% |

## Potwierdzone według pary i rodziny

| para | rodzina | reguł |
|---|---|---|
| EURUSD | sezon | 1 |

## Najbliżej progu (nie przeszły — dodatnie w obu okresach, za słabe po korekcie)

To NIE są odkrycia. Lista pokazuje, czego szukać przy większej liczbie par albo węższej siatce.

| # | reguła | n odkr. | pips netto odkr. | t odkr. | n potw. | pips netto potw. | t potw. | lata + | sąsiedzi + |
|---|---|---|---|---|---|---|---|---|---|
| 1 | EURUSD long od 01:00 Londynu przez 6 h, tylko miesiąc 12 | 267 | +5.68 | 3.8 | 118 | +4.17 | 3.4 | 17/18 | 100% |
| 2 | EURUSD long od 00:00 Londynu przez 7 h, tylko miesiąc 12 | 267 | +5.40 | 3.2 | 118 | +4.21 | 3.0 | 17/18 | 100% |
| 3 | EURUSD short od 11:00 Londynu przez 2 h | 3059 | +1.33 | 3.1 | 1522 | +1.25 | 2.8 | 16/18 | 25% |
| 4 | EURUSD: po ruchu > 0.5×ATR14·√k z 1 świec — za ruchem, 3 świec, sesja h22 | 253 | +3.60 | 2.6 | 114 | +3.07 | 2.7 | 15/18 | 100% |
| 5 | EURUSD long od 01:00 Londynu przez 5 h, tylko miesiąc 12 | 267 | +3.44 | 2.6 | 118 | +4.33 | 4.1 | 16/18 | 100% |
| 6 | EURUSD long od 00:00 Londynu przez 8 h, tylko miesiąc 12 | 267 | +7.78 | 3.9 | 118 | +4.21 | 2.6 | 17/18 | 100% |
| 7 | EURUSD long od 16:00 Londynu przez 16 h, tylko miesiąc 12 | 265 | +8.55 | 2.6 | 114 | +7.51 | 2.5 | 15/18 | 100% |
| 8 | EURUSD long od 01:00 Londynu przez 3 h, tylko miesiąc 12 | 267 | +2.92 | 2.5 | 118 | +3.11 | 3.4 | 14/18 | 100% |
| 9 | EURUSD long od 22:00 Londynu przez 9 h, tylko miesiąc 12 | 214 | +5.45 | 2.7 | 92 | +4.79 | 2.5 | 15/18 | 100% |
| 10 | EURUSD: po ruchu > 0.5×ATR14·√k z 1 świec — za ruchem, 2 świec, sesja h22 | 327 | +2.85 | 2.4 | 142 | +2.52 | 3.2 | 13/18 | 100% |
| 11 | EURUSD long od 01:00 Londynu przez 4 h, tylko miesiąc 12 | 267 | +3.07 | 2.4 | 118 | +2.74 | 2.8 | 16/18 | 100% |
| 12 | USDJPY: po ruchu > 0.5×ATR14·√k z 3 świec — za ruchem, 3 świec, sesja h22 | 207 | +4.14 | 2.8 | 57 | +7.37 | 2.4 | 12/14 | 100% |
| 13 | EURUSD long od 02:00 Londynu przez 5 h, tylko miesiąc 12 | 267 | +3.83 | 3.0 | 118 | +2.61 | 2.4 | 16/18 | 100% |
| 14 | EURUSD: po ruchu > 0.5×ATR14·√k z 2 świec — za ruchem, 1 świec, sesja h23 | 307 | +2.58 | 3.4 | 102 | +2.34 | 2.3 | 14/18 | 100% |
| 15 | EURUSD long od 23:00 Londynu przez 8 h, tylko miesiąc 12 | 212 | +5.74 | 2.9 | 91 | +3.91 | 2.3 | 15/18 | 100% |

Następny krok: najlepsze reguły (z sąsiadami ≥ 60%) zamienić w strategię i policzyć silnikiem — dopiero tam liczy się OOS, benchmark losowy, DSR i PBO.