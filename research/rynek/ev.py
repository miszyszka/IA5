"""Maszyna badań zdarzeń: sygnał na zamknięciu świecy t → wejście open t+1 → wyjście close po h świecach; pips netto po spreadzie.
Statystyka po dniach (średnia dzienna zdarzeń, t po dniach), osobno A i B (albo C = Yahoo)."""
import functools

import lib
import numpy as np
import pandas as pd

HS = (1, 2, 4, 8, 24)
N_TESTS = {"n": 0}


@functools.lru_cache(None)
def frames(src="ej"):
    F = {}
    for p in lib.PAIRS:
        d = lib.add_time(lib.load(src, p))
        d["atr"] = lib.atr(d, 24)
        d["atr_d"] = lib.atr(d, 24 * 20)
        d["per"] = np.where(d.index < lib.CUT_AB, "A", "B") if src == "ej" else "C"
        d["roll"] = d.h_ny.isin([16, 17, 18])
        # ciągłość: następna świeca dokładnie za godzinę (bez dziur) — do horyzontów
        ts = lib.epoch(d.index)
        d["ts"] = ts
        F[p] = d
    return F


def outcomes(d, p, sig, hs=HS, skip_roll=True):
    """sig: Series ±1/0 na indeksie d. Zwraca DataFrame zdarzeń: dir, fxday, per, net_h (pips netto) dla h w hs."""
    s = np.nan_to_num(np.asarray(sig, float))
    i = np.flatnonzero(s != 0)
    n = len(d)
    i = i[i + 1 + max(hs) < n]
    o, c, ts = d.open.to_numpy(), d.close.to_numpy(), d.ts.to_numpy()
    e = i + 1
    ok = np.ones(len(i), bool)
    if skip_roll:
        ok &= ~d.roll.to_numpy()[e]
    if "gap_before" in d:                      # Yahoo: bez przerw w danych w oknie
        gc = np.r_[0, np.cumsum(d.gap_before.to_numpy() > 0)]
        ok &= (gc[np.minimum(e + max(hs) + 1, n)] - gc[i + 1]) == 0
    i, e = i[ok], e[ok]
    out = pd.DataFrame({"dir": s[i], "fxday": d.fxday.to_numpy()[e], "per": d.per.to_numpy()[e], "h": d.h_lon.to_numpy()[e]})
    for h in hs:
        x = e + h - 1
        # horyzont w czasie zegarowym nie dłuższy niż h + 60 h (weekend) — inaczej dziura w danych
        good = (ts[x] - ts[e]) <= (h + 60) * 3600
        out[f"n{h}"] = np.where(good, s[i] * (c[x] - o[e]) / lib.PIP[p] - lib.SPREAD[p], np.nan)
    return out


def summarize(E, hs=HS):
    """E: zdarzenia (z kolumną per). Zwraca {per: {h: (n, śr., t po dniach)}}."""
    res = {}
    for per, g in E.groupby("per"):
        r = {"n": len(g)}
        for h in hs:
            dm = g.groupby("fxday")[f"n{h}"].mean()
            r[f"m{h}"] = g[f"n{h}"].mean()
            r[f"t{h}"] = lib.tstat(dm)
        res[per] = r
    return res


def study(name, make_sig, src="ej", pairs=lib.PAIRS, hs=HS, show=True, skip_roll=True):
    """make_sig(d, p) -> Series ±1/0. Łączy wszystkie pary; wypisuje A | B."""
    F = frames(src)
    ev = []
    for p in pairs:
        E = outcomes(F[p], p, make_sig(F[p], p), hs, skip_roll)
        E["pair"] = p
        ev.append(E)
    E = pd.concat(ev, ignore_index=True)
    S = summarize(E, hs)
    N_TESTS["n"] += 1
    if show:
        line = f"{name:<58}"
        for per in sorted(S):
            r = S[per]
            line += f" | {per} n={r['n']:<6}" + " ".join(f"{h}h:{r[f'm{h}']:+5.1f}({r[f't{h}']:+4.1f})" for h in hs)
        print(line)
    return E, S
