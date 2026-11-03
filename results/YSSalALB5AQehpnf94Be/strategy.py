HYPOTHESIS = """Cena po jednej stronie wszystkich głównych średnich na H1, H4 i D1 oznacza zgodny trend krótko- i średnioterminowy
oraz brak bliskiego wsparcia lub oporu ze średnich, więc ruch ma wolną drogę. Wejście zgodne z tym trendem,
przy pierwszym pełnym ułożeniu albo na otwarciu Nowego Jorku, ma mieć przewagę nad wejściem losowym."""

PARAMS = {
    "mode": ["start", "ny"],   # start = pierwsza świeca pełnego ułożenia; ny = stan trwa przed otwarciem Nowego Jorku
    "d1_max": [100, 200],      # najdłuższa średnia D1: 200 zjada ok. 40% krótkiej historii
}


def _tf(close, rule, n, ind):
    """SMA z zamkniętych świec wyższego interwału, przeniesiona na H1 bez look-ahead."""
    x = close.resample(rule).last().dropna()
    return ind.sma(x, n).shift(1).reindex(close.index, method="ffill")


def signals(df, p, ind):
    c = df.close
    lines = [ind.sma(c, n) for n in (20, 50, 100, 200)]
    lines += [_tf(c, "4h", n, ind) for n in (20, 50, 100, 200)]
    lines += [_tf(c, "1D", n, ind) for n in (20, 50, 100, 200) if n <= p["d1_max"]]
    m = pd.concat(lines, axis=1)
    ready = m.notna().all(axis=1)
    up = (c > m.max(axis=1)) & ready
    dn = (c < m.min(axis=1)) & ready
    if p["mode"] == "start":
        go_up = up & ~up.shift(1, fill_value=False)
        go_dn = dn & ~dn.shift(1, fill_value=False)
    else:
        ny = np.asarray(df.index.tz_convert("America/New_York").hour) == 7   # świeca kończy się o 8:00 w Nowym Jorku
        go_up, go_dn = up & ny, dn & ny
    return go_up.astype("int8") - go_dn.astype("int8")