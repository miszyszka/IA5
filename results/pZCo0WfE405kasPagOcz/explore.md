## Eksploracja Maca (D-072)

Mac sprawdził 7,562 odmian (18 rodzajów). 2 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_slaby, odwrocony, oryginal, potwierdzenie, potwierdzenie+adx_silny, potwierdzenie+przeciw200, potwierdzenie+zmiennosc_wysoka, przeciw200, przeciw200+adx_silny, siatka, trail, trend200, tylko_short, zmiennosc_niska, zmiennosc_wysoka, zmiennosc_wysoka+adx_silny, zmiennosc_wysoka+przeciw200. Prób (wariantów) łącznie: 7,562. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): po 4 świecach, {'rsi_level': 25} — IS 63 trans., śr. R +0.238, ocena +0.124; OOS 26 trans., śr. R -0.449.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | potwierdzenie: następna świeca zamyka się w kierunku sygnału {'rsi_level': 25} | po 120 świecach | 34 | +0.222 | 11 | +0.703 | +2.35 | +0.176 | 93 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 2 | potwierdzenie: następna świeca zamyka się w kierunku sygnału + tylko przy podwyższonej zmienności (ATR14 > ATR100) {'rsi_level': 30} | po 120 świecach | 36 | +0.170 | 10 | -3.042 | -64.31 | +0.128 | 53 | — | nie przetrwała OOS |
| 3 | potwierdzenie: następna świeca zamyka się w kierunku sygnału + tylko przy silnym trendzie (ADX14 > 25) {'rsi_level': 30} | po 96 świecach | 49 | +0.140 | 11 | -0.714 | -40.03 | +0.023 | 62 | — | nie przetrwała OOS |
| 4 | tylko przy podwyższonej zmienności (ATR14 > ATR100) {'rsi_level': 25} | po 4 świecach | 49 | +0.125 | 18 | -0.602 | -13.52 | +0.007 | 45 | — | nie przetrwała OOS |
| 5 | tylko przeciw trendowi SMA200 {'rsi_level': 25} | RSI do 50, SL 2×ATR14, max 120 | 55 | +0.119 | 23 | +0.005 | -3.20 | +0.005 | 92 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |

