## Eksploracja Maca (D-072)

Mac sprawdził 440 odmian (20 rodzajów). 3 z 5 kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów.

Rodzaje odmian: adx_silny, adx_slaby, adx_slaby+zmiennosc_niska, odwrocony, oryginal, potwierdzenie, przeciw200, siatka, trail, trend200, trend200+adx_slaby, trend200+tylko_long, trend200+zmiennosc_niska, trend50, tylko_long, tylko_long+adx_slaby, tylko_long+zmiennosc_niska, tylko_short, zmiennosc_niska, zmiennosc_wysoka. Prób (wariantów) łącznie: 440. Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.

Oryginał (najlepszy wariant wg tej samej oceny): TP 1.5×ATR14, RSI 6 świec za 70/30, max 120, {'ema': 200, 'nachylenie': 0.15, 'szok': 0} — IS 446 trans., śr. R +0.393, ocena +0.130; OOS 161 trans., śr. R +0.210.

| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) | percentyl losowych | akcje | werdykt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | tylko long + tylko bez wyraźnego trendu (ADX14 < 20) {'ema': 200, 'nachylenie': 0.15, 'szok': 0} | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | 33 | +0.365 | 11 | -0.611 | -4.77 | +0.766 | 78 | — | nie przetrwała OOS |
| 2 | tylko z trendem SMA200 + tylko przy spokojnym rynku (ATR14 < ATR100) {'ema': 200, 'nachylenie': 0.15, 'szok': 0} | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | 140 | +0.289 | 42 | +0.258 | +8.98 | +0.450 | 99 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 3 | szersza siatka parametrów {'ema': 300, 'nachylenie': 0.35, 'szok': 1.5} | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | 72 | +0.235 | 22 | +0.694 | +15.49 | +0.141 | 98 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |
| 4 | tylko long + tylko przy spokojnym rynku (ATR14 < ATR100) {'ema': 200, 'nachylenie': 0.15, 'szok': 0} | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | 72 | +0.228 | 22 | -1.099 | -10.06 | +0.268 | 80 | — | nie przetrwała OOS |
| 5 | tylko z trendem SMA200 + tylko long {'ema': 200, 'nachylenie': 0.25, 'szok': 0} | TP 1.5×ATR14, RSI 6 świec za 70/30, max 120 | 103 | +0.204 | 23 | +0.070 | +1.77 | +0.059 | 89 | — | dodatnia w OOS, ale nie przechodzi wszystkich testów |

