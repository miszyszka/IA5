## Eksploracja Maca (D-072)

Mac sprawdził 53 odmian (18 rodzajów). 5 kandydatów otwartych na OOS — żaden nie przetrwał.

Rodzaje odmian: adx_silny, adx_slaby, cofniecie20, odwrocony, odwrocony+przeciw200, odwrocony+trend50, odwrocony+tylko_long, oryginal, przeciw200, przeciw200+tylko_long, siatka, trend200, trend50, tylko_long, tylko_long+trend50, tylko_short, zmiennosc_niska, zmiennosc_wysoka. Prób (wariantów) łącznie: 53. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): poziomy TP/SL ze strategii, max 72, {'tp': 2} — IS 491 trans., śr. R -0.010, ocena -0.008; OOS 148 trans., śr. R +0.135.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | odwrócony sygnał + tylko przeciw trendowi SMA200 {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 331 | +4.351 | 134 | +2.455 | +18.68 | +1.000 | 0 | — | nie przetrwała OOS |
| 2 | odwrócony sygnał {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 507 | +4.104 | 175 | +2.387 | +18.52 | +1.000 | 0 | — | nie przetrwała OOS |
| 3 | odwrócony sygnał + tylko long {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 242 | +3.954 | 63 | +2.142 | +17.46 | +1.000 | 0 | — | nie przetrwała OOS |
| 4 | tylko przeciw trendowi SMA200 + tylko long {'tp': 4} | poziomy TP/SL ze strategii, max 72 | 61 | +0.101 | 7 | -1.115 | -18.89 | +0.000 | 85 | — | za mało transakcji OOS |
| 5 | tylko przeciw trendowi SMA200 {'tp': 2} | poziomy TP/SL ze strategii, max 72 | 192 | +0.057 | 48 | -0.174 | -5.06 | +0.000 | 93 | — | nie przetrwała OOS |

