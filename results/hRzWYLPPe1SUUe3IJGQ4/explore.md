## Eksploracja Maca (D-072)

Mac sprawdził 14,004 odmian (21 rodzajów). 2 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_slaby, cofniecie20, odwrocony, oryginal, potwierdzenie, przeciw200, trail, trend200, trend50, trend50+adx_slaby, trend50+zmiennosc_niska, tylko_long, tylko_short, wybicie20, wybicie20+adx_slaby, wybicie20+trend50, wybicie20+zmiennosc_niska, zmiennosc_niska, zmiennosc_niska+adx_slaby, zmiennosc_wysoka. Prób (wariantów) łącznie: 14,004. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): po 120 świecach, {'cfg': 2} — IS 266 trans., śr. R +0.793, ocena +0.079; OOS 110 trans., śr. R +0.720.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko przy spokojnym rynku (ATR14 < ATR100) {'cfg': 0} | po 36 świecach | 54 | +0.372 | 33 | +0.400 | +37.63 | +0.886 | 98 | akcje nie potwierdzają | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 2 | tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko bez wyraźnego trendu (ADX14 < 20) {'cfg': 0} | po 36 świecach | 48 | +0.338 | 21 | -0.618 | -0.84 | +0.812 | 95 | akcje nie potwierdzają | nie przetrwała OOS |
| 3 | tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) {'cfg': 0} | ATR5 TP 0.5× SL 3× max 120 | 104 | +0.158 | 48 | -0.011 | +4.91 | +0.318 | 42 | akcje nie potwierdzają | nie przetrwała OOS |
| 4 | tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko z trendem SMA50 {'cfg': 0} | po 48 świecach | 86 | +0.155 | 38 | -0.494 | -39.26 | +0.744 | 79 | akcje słabo potwierdzają | nie przetrwała OOS |
| 5 | tylko z trendem SMA50 {'cfg': 2} | po 96 świecach | 271 | +0.148 | 117 | +0.119 | +33.45 | +0.184 | 99 | akcje nie potwierdzają | dodatnia w OOS, ale nie przechodzi wszystkich testów |

### OOS na akcjach (pilotaż, poza werdyktem)

| wersja | spółki | transakcje | śr. % netto | śr. R | long % | short % | percentyl losowych | spółki na plusie | werdykt |
|---|---|---|---|---|---|---|---|---|---|
| oryginał | 14/14 | 461 | -1.904 | -0.675 | +8.235 | -10.689 | 19 | 7/14 | akcje nie potwierdzają |
| tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko przy spokojnym rynku (ATR14 < ATR100) | 14/14 | 77 | +0.916 | +0.485 | +1.670 | -0.267 | 69 | 8/14 | akcje nie potwierdzają |
| tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko bez wyraźnego trendu (ADX14 < 20) | 14/14 | 95 | +0.683 | +0.343 | +2.572 | -1.806 | 64 | 8/14 | akcje nie potwierdzają |
| tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) | 14/14 | 216 | -0.326 | -0.048 | +0.347 | -1.200 | 39 | 5/14 | akcje nie potwierdzają |
| tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem) + tylko z trendem SMA50 | 14/14 | 179 | +1.434 | +0.571 | +3.702 | -1.570 | 81 | 9/14 | akcje słabo potwierdzają |
| tylko z trendem SMA50 | 14/14 | 471 | +0.129 | +0.288 | +6.480 | -8.256 | 24 | 5/14 | akcje nie potwierdzają |

