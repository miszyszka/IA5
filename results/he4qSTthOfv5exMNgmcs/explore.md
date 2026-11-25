## Eksploracja Maca (D-072)

Mac sprawdził 1,004 odmian (22 rodzajów). 1 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_silny+cofniecie20, adx_silny+trend200, adx_silny+zmiennosc_wysoka, adx_slaby, cofniecie20, cofniecie20+trend200, cofniecie20+zmiennosc_wysoka, odwrocony, oryginal, potwierdzenie, przeciw200, siatka, trail, trend200, trend50, tylko_long, tylko_short, wybicie20, zmiennosc_niska, zmiennosc_wysoka, zmiennosc_wysoka+trend200. Prób (wariantów) łącznie: 1,004. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): ATR14 TP 1× SL 5× max 60, {'mode': 'trend', 'ema': 100, 'k': 20} — IS 2808 trans., śr. R +0.009, ocena +0.013; OOS 1276 trans., śr. R -0.030.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | tylko przy silnym trendzie (ADX14 > 25) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 715 | +0.112 | 285 | -0.002 | -6.38 | +0.636 | 98 | akcje nie potwierdzają | nie przetrwała OOS |
| 2 | tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) + tylko przy podwyższonej zmienności (ATR14 > ATR100) {'mode': 'trend', 'ema': 100, 'k': 5} | ATR14 TP 0.3× SL 10× max 60 | 1568 | +0.068 | 710 | -0.003 | -5.03 | +0.286 | 100 | akcje nie potwierdzają | nie przetrwała OOS |
| 3 | tylko przy silnym trendzie (ADX14 > 25) {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1413 | +0.051 | 594 | -0.006 | -3.78 | +0.084 | 92 | akcje nie potwierdzają | nie przetrwała OOS |
| 4 | tylko przy silnym trendzie (ADX14 > 25) + tylko z trendem SMA200 {'mode': 'trend', 'ema': 100, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1377 | +0.044 | 576 | -0.011 | -8.57 | +0.036 | 82 | akcje nie potwierdzają | nie przetrwała OOS |
| 5 | tylko przy podwyższonej zmienności (ATR14 > ATR100) + tylko z trendem SMA200 {'mode': 'trend', 'ema': 200, 'k': 20} | ATR14 TP 1× SL 10× max 60 | 1092 | +0.041 | 524 | +0.004 | +2.44 | +0.059 | 94 | akcje nie potwierdzają | dodatnia w OOS, ale nie przechodzi wszystkich testów |

### OOS na akcjach (pilotaż, poza werdyktem)

| wersja | spółki | transakcje | śr. % netto | śr. R | long % | short % | percentyl losowych | spółki na plusie | werdykt |
|---|---|---|---|---|---|---|---|---|---|
| oryginał | 14/14 | 5216 | -0.354 | -0.031 | +0.180 | -1.793 | 0 | 2/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) + tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) | 14/14 | 1238 | +0.032 | -0.006 | +0.466 | -0.914 | 49 | 7/14 | akcje nie potwierdzają |
| tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20) + tylko przy podwyższonej zmienności (ATR14 > ATR100) | 14/14 | 3424 | -0.128 | -0.008 | +0.034 | -0.503 | 50 | 3/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) | 14/14 | 2632 | -0.232 | -0.008 | +0.455 | -2.275 | 0 | 5/14 | akcje nie potwierdzają |
| tylko przy silnym trendzie (ADX14 > 25) + tylko z trendem SMA200 | 14/14 | 2565 | -0.153 | -0.005 | +0.471 | -2.033 | 0 | 5/14 | akcje nie potwierdzają |
| tylko przy podwyższonej zmienności (ATR14 > ATR100) + tylko z trendem SMA200 | 14/14 | 2662 | +0.116 | +0.006 | +0.638 | -2.039 | 1 | 8/14 | akcje nie potwierdzają |

