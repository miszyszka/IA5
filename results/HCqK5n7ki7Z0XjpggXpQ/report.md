# Raport strategii: Pivot

Run `20261103-174534` · silnik 0.9.0 · kod `1d99b8d4fbf585d6` · dane `e76fc4183c4b5596`

## Werdykt: 🔴 CZERWONY — brak przewagi

| test | wynik | wartość |
|---|---|---|
| expectancy netto OOS > 0 | ✘ | -4.04 |
| percentyl benchmarku ≥ 95 | ✘ | 20.80 |
| PBO < 0,3 | ✘ | 0.80 |
| DSR ≥ 0,95 | ✘ | 0.02 |
| dodatni przy spreadzie ×1,5 | ✘ | -6.27 |

## Hipoteza

Wczorajsze ekstrema i poprzedni poziom dalej za nimi to strefy, w których czekają duzi kupujący i sprzedający.
Gdy cena w godzinach 07–13 dochodzi do takiej strefy, następna świeca ją odrzuca, a kolejna przebija tę świecę,
cena ma wrócić w stronę przeciwnej strony wczorajszego zakresu. Przeniesienie Sneaky Pivot z M15 na H1.

## Dane i model wykonania

- Pary: AUDUSD, EURGBP, EURJPY, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY; świece H1 od 2024-10-28 do 2026-11-03; źródło: yahoo.

- In-sample do 2026-05-03, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.

- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: przyjęty SL (pesymistycznie — świece H1 nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5).

- Spread raz na transakcję (pips): EURUSD 0.9, USDJPY 1.4, GBPUSD 1.5, EURGBP 1.7, AUDUSD 1.7, USDCHF 1.9, USDCAD 2, EURJPY 2.1. Swapy pominięte.

- Jedna pozycja na parę naraz (B8).

- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): AUDUSD: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (99 h); EURGBP: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURJPY: odrzucone 0, uzupełnione 3 (luki ≤ 3 h), 3 przerw w danych (98 h); EURUSD: odrzucone 0, uzupełnione 5 (luki ≤ 3 h), 3 przerw w danych (98 h); GBPUSD: odrzucone 0, uzupełnione 4 (luki ≤ 3 h), 3 przerw w danych (98 h); USDCAD: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h); USDCHF: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 4 przerw w danych (98 h); USDJPY: odrzucone 0, uzupełnione 6 (luki ≤ 3 h), 3 przerw w danych (99 h). Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).

- Kapitał 10,000 USD, dźwignia 30:1, depozyt na pozycję: 5%, 10%, 15%, 20%, 30%; suma depozytów ≤ 100% kapitału.

## Skala przeszukiwania

- **Przetestowane warianty: 48** (8 wejścia × 6 wyjść).

- Pominięte sygnały, średnio na wariant: 0 (limit otwartych pozycji w parze), 0.0 (brak danych do wyjścia); 0 wejść w rozgrzewce ATR, 1 sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), anulowane transakcje, średnio na wariant: 0.0 (przerwa w dostępie do danych), 0.8 (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.

## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)

| # | wyjście | parametry | IS trans. | IS śr. R | IS śr. pips | IS win % | OOS trans. | OOS śr. R | OOS śr. pips |
|---|---|---|---|---|---|---|---|---|---|
| 1 | ATR14 TP 3× SL 1.5× max 10 | tol=0.25, bold=0.0, wait=1 | 37 | -0.30 | -5.91 | 37.8 | 13 | -0.19 | -4.04 |
| 2 | ATR14 TP 2× SL 1.5× max 10 | tol=0.25, bold=0.0, wait=2 | 43 | -0.32 | -6.86 | 34.9 | 15 | -0.15 | -3.80 |
| 3 | ATR14 TP 2× SL 1.5× max 10 | tol=0.25, bold=0.0, wait=1 | 37 | -0.32 | -7.03 | 37.8 | 13 | -0.09 | -2.59 |
| 4 | po 10 świecach | tol=0.25, bold=0.0, wait=1 | 37 | -0.34 | -5.15 | 45.9 | 13 | -0.68 | -6.65 |
| 5 | ATR14 TP 3× SL 1.5× max 10 | tol=0.25, bold=0.0, wait=2 | 43 | -0.34 | -6.86 | 32.6 | 15 | -0.24 | -5.06 |
| 6 | ATR14 TP 2× SL 1× max 10 | tol=0.5, bold=0.0, wait=2 | 52 | -0.37 | -5.36 | 28.8 | 22 | -0.34 | -7.78 |
| 7 | ATR14 TP 2× SL 1× max 10 | tol=0.5, bold=0.0, wait=1 | 45 | -0.37 | -5.44 | 28.9 | 20 | -0.32 | -7.60 |
| 8 | ATR14 TP 2× SL 1.5× max 10 | tol=0.5, bold=0.0, wait=2 | 52 | -0.39 | -9.82 | 38.5 | 22 | -0.12 | -4.63 |
| 9 | ATR14 TP 3× SL 1× max 10 | tol=0.5, bold=0.0, wait=1 | 45 | -0.39 | -5.45 | 26.7 | 20 | -0.49 | -9.02 |
| 10 | ATR14 TP 3× SL 1.5× max 10 | tol=0.5, bold=0.0, wait=1 | 45 | -0.39 | -10.01 | 40.0 | 20 | -0.31 | -6.66 |

## Najlepszy wariant IS: ATR14 TP 3× SL 1.5× max 10 (tol=0.25, bold=0.0, wait=1)

### Według pary

| para | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| AUDUSD | 10 | -4.1 | -40.7 | 40.0 |
| EURGBP | 2 | -10.1 | -20.1 | 0.0 |
| EURJPY | 8 | -5.6 | -45.2 | 50.0 |
| EURUSD | 2 | -5.3 | -10.6 | 50.0 |
| GBPUSD | 3 | 2.9 | 8.8 | 33.3 |
| USDCAD | 4 | -2.5 | -9.9 | 50.0 |
| USDCHF | 6 | -4.4 | -26.7 | 50.0 |
| USDJPY | 15 | -8.5 | -127.0 | 40.0 |

### Według roku

| rok | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| 2024 | 4 | -10.6 | -42.4 | 25.0 |
| 2025 | 27 | -5.1 | -138.9 | 37.0 |
| 2026 | 19 | -4.7 | -90.1 | 52.6 |

### IS i OOS

| próba | transakcje | śr. pips | suma pips | win % |
|---|---|---|---|---|
| IS | 37 | -5.9 | -218.8 | 37.8 |
| OOS | 13 | -4.0 | -52.5 | 53.8 |

### Kapitał

| depozyt | kapitał końcowy | zwrot % | CAGR % | max obsunięcie % | Sharpe | pominięte (depozyt) |
|---|---|---|---|---|---|---|
| 5.0% | 9 645 | -3.5 | -1.9 | -3.8 | -0.84 | 0 |
| 10.0% | 9 298 | -7.0 | -3.7 | -7.4 | -0.84 | 0 |
| 15.0% | 8 959 | -10.4 | -5.5 | -11.0 | -0.84 | 0 |
| 20.0% | 8 629 | -13.7 | -7.3 | -14.5 | -0.84 | 0 |
| 30.0% | 7 991 | -20.1 | -10.9 | -21.1 | -0.84 | 0 |

## Walidacja

- **Benchmark losowych wejść** (1000 losowań, te same pary, kierunki i wyjście): wynik -5.43 pips/transakcję, percentyl **20.8** (losowe: 5%=-9.28, mediana=-1.81, 95%=6.07).

- **Deflated Sharpe Ratio**: 0.018 (Sharpe na transakcję -0.263, próg przy 24 próbach 0.123).

- **PBO** (CSCV, 16 bloków, 24 wariantów): 0.805 — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.

- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): 33 transakcji, śr. -9.88 pips, -0.44 R.

- **Bootstrap 95%** średnich pipsów: całość [-12.98; 2.26], OOS [-10.98; 2.90].

- **Spread**: ×1 -5.43, ×1,5 -6.27, ×2 -7.11 pips/transakcję.

- TP i SL w tej samej świecy bez rozstrzygnięcia: 2.00% transakcji.

## Znane ograniczenia

- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu.

- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy H1 — przyjmowany SL (brak danych wewnątrz świecy).

- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).

- Benchmark losowy nie stosuje reguły jednej pozycji na parę.

## Kod strategii

```python

HYPOTHESIS = """Wczorajsze ekstrema i poprzedni poziom dalej za nimi to strefy, w których czekają duzi kupujący i sprzedający.
Gdy cena w godzinach 07–13 dochodzi do takiej strefy, następna świeca ją odrzuca, a kolejna przebija tę świecę,
cena ma wrócić w stronę przeciwnej strony wczorajszego zakresu. Przeniesienie Sneaky Pivot z M15 na H1."""

PARAMS = {
    "tol": [0.25, 0.5],     # „blisko wystarczy”: tolerancja przy linii, w ATR14
    "bold": [0.0, 1.0],     # minimalny zakres świecy dotknięcia, w ATR14 (0 = bez warunku)
    "wait": [1, 2],         # 1 = potwierdza trzecia świeca, 2 = także czwarta
}

EXITS = [
    {"kind": "atr", "n": 14, "tp": 1.5, "sl": 1.0, "cap": 10},
    {"kind": "atr", "n": 14, "tp": 2.0, "sl": 1.0, "cap": 10},
    {"kind": "atr", "n": 14, "tp": 3.0, "sl": 1.0, "cap": 10},
    {"kind": "atr", "n": 14, "tp": 2.0, "sl": 1.5, "cap": 10},
    {"kind": "atr", "n": 14, "tp": 3.0, "sl": 1.5, "cap": 10},
    {"kind": "time", "n": 10, "cap": 10},
]

LOOKBACK_DAYS = 60
TOUCH_HOURS = (7, 13)   # świeca dotknięcia: od 07:00 do 13:00 czasu polskiego (najwyżej jeden sygnał dziennie)


def _pattern(i, end, side, o, h, l, c, atr, wait):
    """Świeca i dotknęła linii. Zwraca indeks potwierdzenia albo None: i+1 = sneaky, potem przebicie sneaky."""
    last = min(i + 1 + wait, end - 1)
    if i + 2 > last:
        return None
    sneaky = c[i + 1] > o[i + 1] if side > 0 else c[i + 1] < o[i + 1]
    if not sneaky:
        return None
    guard = min(l[i], l[i + 1]) if side > 0 else max(h[i], h[i + 1])
    for k in range(i + 2, last + 1):
        if (side > 0 and l[k] < guard) or (side < 0 and h[k] > guard):
            return None
        if (side > 0 and c[k] > h[i + 1]) or (side < 0 and c[k] < l[i + 1]):
            return k if abs(c[k] - guard) <= atr[k] else None   # stop 1×ATR ma leżeć za strefą
    return None


def signals(df, p, ind):
    local = df.index.tz_convert("Europe/Warsaw")
    days = np.asarray(local.normalize().tz_localize(None))
    hours = np.asarray(local.hour)
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    atr = ind.atr(df, 14).to_numpy()
    sig = np.zeros(len(df), dtype="int8")
    starts = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1]
    ends = np.r_[starts[1:], len(df)]
    day_hi = np.array([h[a:b].max() for a, b in zip(starts, ends)])
    day_lo = np.array([l[a:b].min() for a, b in zip(starts, ends)])
    tol, bold, wait = p["tol"], p["bold"], p["wait"]

    for d in range(2, len(starts)):
        rh, rl = day_hi[d - 1], day_lo[d - 1]
        back = range(d - 2, max(-1, d - 2 - LOOKBACK_DAYS), -1)
        sh = next((day_hi[j] for j in back if day_hi[j] > rh), np.nan)
        sw = next((day_lo[j] for j in back if day_lo[j] < rl), np.nan)
        if np.isnan(sh) or np.isnan(sw):
            continue
        for i in range(starts[d], ends[d]):
            if not TOUCH_HOURS[0] <= hours[i] <= TOUCH_HOURS[1]:
                continue
            a = atr[i]
            if not a > 0 or h[i] - l[i] < bold * a:
                continue
            buy = sw - tol * a <= l[i] <= rl + tol * a
            sell = rh - tol * a <= h[i] <= sh + tol * a
            if buy == sell:
                continue
            side = 1 if buy else -1
            k = _pattern(i, ends[d], side, o, h, l, c, atr, wait)
            if k is not None:
                sig[k] = side
                break
    return pd.Series(sig, index=df.index)

```

## Pytania do recenzenta

1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?

2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?

3. Czy wynik nie opiera się na jednej parze lub jednym roku?

4. Co w kodzie wejścia może być dopasowane do historii?
