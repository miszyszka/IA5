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