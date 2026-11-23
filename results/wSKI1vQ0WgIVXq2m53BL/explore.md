## Eksploracja Maca (D-072)

Mac sprawdził 98 odmian (19 rodzajów). 5 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_silny+cofniecie20, adx_silny+trend50, adx_silny+zmiennosc_wysoka, adx_slaby, cofniecie20, cofniecie20+trend50, odwrocony, oryginal, potwierdzenie, przeciw200, trail, trend200, trend50, tylko_long, zmiennosc_niska, zmiennosc_wysoka, zmiennosc_wysoka+cofniecie20, zmiennosc_wysoka+trend50. Prób (wariantów) łącznie: 98. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): ATR14 TP 1× SL 0× max 60, {} — IS 216 trans., śr. R +0.442, ocena +0.181; OOS 77 trans., śr. R +0.504.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | tylko przy silnym trendzie (ADX14 > 25) {} | ATR14 TP 1.5× SL 0× max 60 | 126 | +0.248 | 43 | +0.539 | +14.17 | +0.425 | 100 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 2 | tylko przy podwyższonej zmienności (ATR14 > ATR100) {} | ATR14 TP 1× SL 0× max 60 | 193 | +0.220 | 68 | +0.587 | +9.85 | +0.422 | 100 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 3 | tylko przy podwyższonej zmienności (ATR14 > ATR100) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) {} | ATR14 TP 1× SL 0× max 60 | 180 | +0.217 | 61 | +0.595 | +9.26 | +0.369 | 100 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 4 | tylko przy silnym trendzie (ADX14 > 25) + tylko przy podwyższonej zmienności (ATR14 > ATR100) {} | ATR14 TP 1.5× SL 0× max 60 | 120 | +0.210 | 38 | +0.870 | +17.82 | +0.368 | 100 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 5 | tylko przy silnym trendzie (ADX14 > 25) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) {} | ATR14 TP 1.5× SL 0× max 60 | 116 | +0.205 | 40 | +0.472 | +11.58 | +0.356 | 100 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |

