"""Głębokie poszukiwanie strategii (D-044): setki tysięcy – miliony konfiguracji na IS, potem jeden raz na OOS.

Konfiguracja = wyzwalacz wejścia (13 rodzin, search_rules.py) × tryb (za / przeciw) × wyjście (Exit silnika)
× filtr trendu × filtr zmienności × sesja wejścia × dni tygodnia × kierunek. Jedna konfiguracja działa na
WSZYSTKICH parach naraz (pula) — jedna reguła dla 8 par to jedna próba, a nie osiem.

Model wykonania jest model silnika, nie kopia: te same funkcje `engine.find_entries`, `engine.simulate`,
`engine.data_cancel`, okno B11 (`session.in_trading_hours`), spread raz (B3), B5, B6, B8 (bez nakładania),
B12 (anulowanie na przerwach). Sygnały liczy ten sam kod, który trafia do wygenerowanej strategii.

Etapy (granice czasu wspólne dla 8 par, jak w silniku):
  1. IS-A  [0, 50%)  — odkrycie: t-stat średniej R netto, korekta Benjaminiego–Hochberga (FDR 5%) na WSZYSTKIE
                       konfiguracje z wystarczającą liczbą transakcji.
  2. IS-B  [50, 75%) — potwierdzenie w drugiej połowie IS: średnia > 0 i t ≥ 2; ≥ 5/8 par na plusie w IS;
                       płaskowyż (sąsiedzi w siatce też dodatni w IS-A i IS-B).
     Ranking: min(t IS-A, t IS-B). Do OOS idzie z góry ustalona liczba K konfiguracji (domyślnie 20), wybrana
     WYŁĄCZNIE po IS, z ograniczeniem powtórek (1 na wyzwalacz × tryb, ≤ 3 na rodzinę wyzwalacza).
  3. OOS     [75, 100%] — liczony dopiero tu i tylko dla tych K. Raport pokazuje wszystkie K, także przegrane.
     Każde otwarcie OOS jest zapisane w ~/.ia5/oos_ledger.json (OOS tych samych danych traci czystość
     z każdym kolejnym spojrzeniem).
Etapy 1–2 nie dostają transakcji z wejściem w OOS (test: zmiana cen w OOS nie zmienia rankingu).

Wynik: hipotezy z uczciwą liczbą prób, nie werdykt. Wygenerowana strategia (≤ 12 najlepszych konfiguracji IS)
wkleja się do dashboardu — tam silnik liczy benchmark losowy, PBO, walk-forward, test spreadu.
"""
from __future__ import annotations

import itertools
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from . import indicators as ind
from . import search_rules as R
from .config import OOS_FRACTION, PAIRS
from .engine import Exit, data_cancel, find_entries, prepare, simulate
from .session import in_trading_hours

SPLIT_A = 0.50              # IS-A [0, 0.5), IS-B [0.5, 0.75), OOS [0.75, 1]
FDR_Q = 0.05
T_B = 2.0                   # potwierdzenie w IS-B
MIN_A, MIN_B = 60, 30       # minimalna liczba transakcji (wszystkie pary razem) w IS-A i IS-B
MIN_PAIRS_SHARE = 5 / 8     # jaki udział par (z ≥ 5 transakcjami) musi mieć dodatni wynik w całym IS
PLATEAU = 0.5               # udział dodatnich sąsiadów
PAIR_MIN_TRADES = 5
TOP_K = 20
MAX_STRATEGY = 12           # konfiguracji w wygenerowanej strategii (K1: ≤ ~12 kombinacji PARAMS)
FILTER_DIMS = ("trend", "zmiennosc", "sesja", "dni", "kierunek")
STAT_KEYS = ("nA", "sA", "qA", "pA", "nB", "sB", "qB", "pB", "pp", "pn")   # n, suma R, suma R², suma pips; pary
FLOAT_KEYS = {"sA", "qA", "pA", "sB", "qB", "pB"}


# ---------- siatka ----------

def grid(size: str = "duzy") -> dict:
    """szybki ≈ 20 tys. konfiguracji (minuty), duzy ≈ 0,8 mln (dziesiątki minut), gigant ≈ 4 mln (godziny)."""
    if size == "szybki":
        trig = {
            "wstega": {"s": ["5,10,15,25,40", "8,13,21,34,55"]},
            "przeciecie": {"typ": ["ema"], "f": [10, 20], "w": [50, 200]},
            "rsi": {"n": [2, 14], "lvl": [10, 30]},
            "donchian": {"n": [24, 96]},
            "bollinger": {"n": [20], "k": [2.0]},
            "impuls": {"k": [3, 12], "th": [1.0, 1.5]},
            "azja": {"bufor": [0.0]},
            "wczoraj": {"bufor": [0.0]},
            "macd": {"f": [12], "w": [26], "s": [9]},
            "seria": {"n": [4]},
            "duza": {"x": [1.5]},
        }
        exits = [Exit("time", n=n, cap=n) for n in (8, 24)]
        exits += [Exit("atr", n=14, tp=tp, sl=sl, cap=120) for tp, sl in ((1, 1), (2, 1), (2, 2))]
        exits += [Exit("trail", n=14, sl=2, trail=3, cap=480)]
        filters = {"trend": ["brak", "zgodny_ema200", "przeciw_ema200"], "zmiennosc": ["brak"],
                   "sesja": ["07-17", "07-10", "13-17"], "dni": ["pn-pt"], "kierunek": ["oba", "long", "short"]}
        return {"trig": trig, "exits": exits, "filters": filters}
    big = size == "gigant"
    trig = {
        "wstega": {"s": ["3,5,8,13,21", "5,10,15,25,40", "8,13,21,34,55"] + (["10,20,30,50,80", "4,8,12,20,32"] if big else [])},
        "przeciecie": {"typ": ["ema", "sma"], "f": [5, 10, 20, 50] if big else [10, 20, 50], "w": [50, 100, 200] if big else [50, 200]},
        "rsi": {"n": [2, 3, 5, 14], "lvl": [5, 10, 20, 30] if big else [10, 20, 30]},
        "donchian": {"n": [12, 24, 48, 96, 240] + ([480] if big else [])},
        "bollinger": {"n": [20, 50], "k": [1.5, 2.0, 2.5, 3.0]},
        "impuls": {"k": [1, 3, 6, 12, 24] + ([48] if big else []), "th": [1.0, 1.5, 2.0, 2.5] if big else [1.0, 1.5, 2.0]},
        "azja": {"bufor": [0.0, 0.25] + ([0.5] if big else [])},
        "wczoraj": {"bufor": [0.0, 0.25] + ([0.5] if big else [])},
        "scisk": {"x": [0.6, 0.8], "n": [12, 24] + ([48] if big else [])},
        "macd": {"f": [12, 5], "w": [26, 35], "s": [9, 5]} if big else {"f": [12], "w": [26], "s": [9]},
        "stoch": {"k": [5, 14], "lvl": [10, 20]},
        "seria": {"n": [3, 4, 5, 6]},
        "duza": {"x": [1.0, 1.5, 2.0] + ([2.5] if big else [])},
    }
    times = (2, 4, 8, 12, 24, 48, 96) if big else (4, 8, 24, 48, 96)
    exits = [Exit("time", n=n, cap=n) for n in times]
    tpsl = [(tp, sl) for tp in (0.75, 1, 1.5, 2, 3, 4) for sl in (0.75, 1, 1.5, 2, 3)] if big else \
        [(1, 1), (1.5, 1), (2, 1), (3, 1.5), (1, 2), (2, 2), (4, 2)]
    exits += [Exit("atr", n=14, tp=tp, sl=sl, cap=120) for tp, sl in tpsl]
    trails = [(sl, tr) for sl in (1.5, 2, 3) for tr in (2, 3, 4)] if big else [(2, 2), (2, 3), (3, 4)]
    exits += [Exit("trail", n=14, sl=sl, trail=tr, cap=480) for sl, tr in trails]
    exits += [Exit("rsi50", n=14, sl=2, cap=120), Exit("sma", n=14, sl=2, cap=120)]
    filters = {"trend": list(R.TREND), "zmiennosc": list(R.ZMIENNOSC), "sesja": list(R.SESJA), "dni": list(R.DNI),
               "kierunek": list(R.KIERUNEK)}
    return {"trig": trig, "exits": exits, "filters": filters}


def expand_triggers(trig: dict) -> list[dict]:
    """Lista {"trig", "kw"} z siatki (przecięcie tylko f < w)."""
    out = []
    for name, g in trig.items():
        keys = list(g)
        for vals in itertools.product(*(g[k] for k in keys)):
            kw = dict(zip(keys, vals))
            if name == "przeciecie" and kw["f"] >= kw["w"]:
                continue
            if name == "macd" and kw["f"] >= kw["w"]:
                continue
            out.append({"trig": name, "kw": kw})
    return out


class Space:
    """Indeksowanie konfiguracji: wymiary (wyzwalacz, tryb, wyjście, trend, zmienność, sesja, dni, kierunek)."""

    def __init__(self, g: dict):
        self.g = g
        self.triggers = expand_triggers(g["trig"])
        self.exits = list(g["exits"])
        self.filters = g["filters"]
        self.dims = (len(self.triggers), 2, len(self.exits), *(len(self.filters[d]) for d in FILTER_DIMS))
        self.n = int(np.prod(self.dims))
        self.n_filters = int(np.prod(self.dims[3:]))

    def flat(self, ti: int, mi: int, xi: int) -> np.ndarray:
        """Indeksy wszystkich kombinacji filtrów dla (wyzwalacz, tryb, wyjście) — w kolejności itertools.product."""
        base = np.ravel_multi_index((ti, mi, xi, *([0] * len(FILTER_DIMS))), self.dims)
        return base + np.arange(self.n_filters)

    def config(self, idx: int) -> dict:
        ti, mi, xi, *fi = np.unravel_index(int(idx), self.dims)
        t = self.triggers[ti]
        c = {"trig": t["trig"], "kw": dict(t["kw"]), "tryb": 1 if mi == 0 else -1}
        c.update({d: self.filters[d][k] for d, k in zip(FILTER_DIMS, fi)})
        c["exit"] = self.exits[xi]
        return c


def describe(c: dict) -> str:
    kw = ", ".join(f"{k}={v}" for k, v in c["kw"].items())
    tryb = "za sygnałem" if c["tryb"] > 0 else "przeciw sygnałowi"
    f = [c["trend"], c["zmiennosc"], f"sesja {c['sesja']}", c["dni"], c["kierunek"]]
    f = [x for x in f if x not in ("brak", "pn-pt", "oba", "sesja 07-17")]
    return f"{c['trig']}({kw}) {tryb}" + (f" · {' · '.join(f)}" if f else "") + f" → {c['exit'].label()}"


# ---------- dane pary ----------

def frame_index(raw: pd.DataFrame) -> pd.DataFrame:
    """Świece w postaci, jaką dostaje strategia w sandboxie (indeks UTC, kolumny OHLC, attrs["pair"])."""
    return raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]


def cuts_for(frames: dict[str, pd.DataFrame]) -> tuple[float, float, float, float]:
    """(t0, granica IS-A/IS-B, granica IS/OOS jak w silniku, t1)."""
    t0 = min(int(df["ts"].iloc[0]) for df in frames.values())
    t1 = max(int(df["ts"].iloc[-1]) for df in frames.values())
    return t0, t0 + SPLIT_A * (t1 - t0), t0 + (1 - OOS_FRACTION) * (t1 - t0), t1


def _outcomes(P: dict, F: dict, sig: np.ndarray, ex: Exit, pair: str, until: float | None) -> dict | None:
    """Wejścia jednego sygnału (przed filtrami) i ich wynik dla jednego wyjścia — dokładnie jak engine.run,
    bez B8 (nakładanie liczone później, po filtrach). until = granica IS: wejścia od niej nie istnieją."""
    ent = find_entries(P, sig)
    if ent.empty:
        return None
    keep = ~(ent["atr14"].isna() | ent["atr5"].isna()).to_numpy()
    keep &= in_trading_hours(ent["entry_ts"].to_numpy(), None)
    if until is not None:
        keep &= ent["entry_ts"].to_numpy() < until
    ent = ent[keep].reset_index(drop=True)
    if ent.empty:
        return None
    res = simulate(P, ent, ex, pair)
    xi = res["exit_i"].to_numpy(float).copy()
    xi[data_cancel(P, ent["signal_i"].to_numpy(), ent["entry_i"].to_numpy(), xi)] = np.nan
    ok = ~np.isnan(xi)
    pip = PAIRS[pair]
    pn = res["pips_gross"].to_numpy(float) - pip.spread_pips
    rn = pn / res["risk_pips"].to_numpy(float)
    return {"i": ent["signal_i"].to_numpy()[ok], "d": ent["dir"].to_numpy().astype(int)[ok],
            "e": ent["entry_i"].to_numpy()[ok], "x": xi[ok], "ts": ent["entry_ts"].to_numpy()[ok],
            "xts": res["exit_ts"].to_numpy(float)[ok], "r": rn[ok], "p": pn[ok]}


def _chain(e: np.ndarray, x: np.ndarray) -> list[int]:
    """B8 (jedna pozycja na parę): kolejne wejście dopiero po świecy wyjścia poprzedniego — jak engine.no_overlap."""
    nxt = np.searchsorted(e, x, side="right").tolist()
    out, j, m = [], 0, len(e)
    while j < m:
        out.append(j)
        j = nxt[j]
    return out


def _masks(F: dict, o: dict, space: Space) -> list[np.ndarray]:
    """Maski filtrów dla wejść o — w kolejności Space.flat."""
    parts = {}
    for dim in FILTER_DIMS:
        opts = space.filters[dim]
        parts[dim] = [_one_filter(F, o, dim, v) for v in opts]
    out = []
    for combo in itertools.product(*(parts[d] for d in FILTER_DIMS)):
        m = combo[0].copy()
        for c in combo[1:]:
            m &= c
        out.append(m)
    return out


def _one_filter(F: dict, o: dict, dim: str, value: str) -> np.ndarray:
    base = {"trend": "brak", "zmiennosc": "brak", "sesja": "07-17", "dni": "pn-pt", "kierunek": "oba"}
    kw = dict(base)
    kw[dim] = value
    return R.filter_mask(F, o["i"], o["d"], kw["trend"], kw["zmiennosc"], kw["sesja"], kw["dni"], kw["kierunek"])


def scan_pair(pair: str, raw: pd.DataFrame, size: str, cuts: tuple, progress: bool = True) -> tuple[str, dict]:
    """Etapy 1–2 dla jednej pary: statystyki IS-A i IS-B każdej konfiguracji (float32/int32)."""
    space = Space(grid(size))
    t_start = time.time()
    _, cut_a, cut_is, _ = cuts
    raw = raw.reset_index(drop=True)
    P = prepare(raw)
    df = frame_index(raw)
    df.attrs["pair"] = pair
    F = R.features(df, ind)
    acc = {k: np.zeros(space.n, np.float32 if k in FLOAT_KEYS else np.int32) for k in STAT_KEYS}
    nt = len(space.triggers)
    for ti, t in enumerate(space.triggers):
        base_sig = R.TRIGGERS[t["trig"]](df, ind, **t["kw"]).astype(np.int8)
        for mi, tryb in enumerate((1, -1)):
            sig = base_sig * tryb
            for xi, ex in enumerate(space.exits):
                o = _outcomes(P, F, sig, ex, pair, cut_is)
                if o is None:
                    continue
                idx = space.flat(ti, mi, xi)
                isa = o["ts"] < cut_a
                for k, m in enumerate(_masks(F, o, space)):
                    sel = np.flatnonzero(m)
                    if len(sel) == 0:
                        continue
                    kept = sel[_chain(o["e"][sel], o["x"][sel])]
                    r, p, a = o["r"][kept], o["p"][kept], isa[kept]
                    j = idx[k]
                    na = int(a.sum())
                    nb = len(kept) - na
                    ra, rb = r[a], r[~a]
                    acc["nA"][j] = na
                    acc["nB"][j] = nb
                    acc["sA"][j], acc["qA"][j], acc["pA"][j] = ra.sum(), (ra * ra).sum(), p[a].sum()
                    acc["sB"][j], acc["qB"][j], acc["pB"][j] = rb.sum(), (rb * rb).sum(), p[~a].sum()
                    if len(kept) >= PAIR_MIN_TRADES:
                        acc["pn"][j] = 1
                        acc["pp"][j] = int(r.sum() > 0)
        if progress and (ti + 1) % max(1, nt // 10) == 0:
            el = time.time() - t_start
            print(f"  {pair}: {ti + 1}/{nt} wyzwalaczy · {el / 60:.1f} min · zostało ~{el / (ti + 1) * (nt - ti - 1) / 60:.0f} min",
                  flush=True)
    return pair, acc


# ---------- statystyka ----------

def _t(n, s, q):
    n = n.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        m = s / n
        var = (q - n * m * m) / (n - 1)
        t = m / np.sqrt(var / n)
    t[(n < 2) | ~np.isfinite(t)] = np.nan
    return m, t


def p_one_sided(t: np.ndarray) -> np.ndarray:
    from math import erfc, sqrt
    return np.array([0.5 * erfc(x / sqrt(2)) if np.isfinite(x) else np.nan for x in t])


def bh_threshold(p: np.ndarray, q: float) -> float:
    p = np.sort(p[~np.isnan(p)])
    m = len(p)
    if m == 0:
        return 0.0
    ok = p <= q * np.arange(1, m + 1) / m
    return float(p[np.flatnonzero(ok)[-1]]) if ok.any() else 0.0


def table(acc: dict, space: Space) -> pd.DataFrame:
    """Statystyki IS wszystkich konfiguracji (bez OOS) + bramki etapów 1–2."""
    n_a, n_b = acc["nA"], acc["nB"]
    mA, tA = _t(n_a, acc["sA"].astype(float), acc["qA"].astype(float))
    mB, tB = _t(n_b, acc["sB"].astype(float), acc["qB"].astype(float))
    n = (n_a + n_b).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        s, q = acc["sA"].astype(float) + acc["sB"], acc["qA"].astype(float) + acc["qB"]
        m = s / n
        sd = np.sqrt((q - n * m * m) / (n - 1))
        sharpe = m / sd
        pips = (acc["pA"].astype(float) + acc["pB"]) / n
    t = pd.DataFrame({"cfg": np.arange(space.n), "nA": n_a, "rA": mA, "tA": tA, "nB": n_b, "rB": mB, "tB": tB,
                      "sharpe_is": sharpe, "pips_is": pips, "pary_plus": acc["pp"], "pary": acc["pn"]})
    t["eligible"] = (t.nA >= MIN_A) & (t.nB >= MIN_B)
    t["robust"] = np.minimum(t.tA, t.tB)
    return t


def gates(t: pd.DataFrame, space: Space, deep: int = 3000) -> dict:
    """Bramki etapów 1–2 (tylko IS). Płaskowyż liczony dla `deep` najlepszych po robust."""
    el = t[t.eligible].copy()
    el["p"] = p_one_sided(el.tA.to_numpy())
    thr = bh_threshold(el.p.to_numpy(), FDR_Q)
    el["odkryta"] = el.p <= thr
    el["potwierdzona"] = el.odkryta & (el.rB > 0) & (el.tB >= T_B)
    el["pary_ok"] = (el.pary > 0) & (el.pary_plus >= np.ceil(MIN_PAIRS_SHARE * el.pary - 1e-9))
    head = el.sort_values("robust", ascending=False).head(deep).copy()
    good = (t.rA > 0) & (t.rB > 0) & t.eligible
    head["plaskowyz"] = [plateau(int(c), space, good.to_numpy()) for c in head.cfg]
    head["bramki"] = head.potwierdzona & head.pary_ok & (head.plaskowyz >= PLATEAU)
    from statistics import NormalDist
    t_thr = NormalDist().inv_cdf(1 - thr) if thr > 0 else float("nan")
    t_need = NormalDist().inv_cdf(1 - FDR_Q / len(el)) if len(el) else float("nan")   # najmniejsze p musi być ≤ q/m
    return {"eligible": el, "head": head, "p_threshold": thr, "t_threshold": t_thr, "t_needed": t_need,
            "discovered": int(el.odkryta.sum()), "confirmed": int(el.potwierdzona.sum())}


def _neighbours(items: list[dict], keys_of) -> list[list[int]]:
    """Sąsiedzi: ta sama grupa, różnica w dokładnie jednym parametrze o jeden krok jego siatki."""
    out = []
    for a in items:
        ga, ka = keys_of(a)
        nb = []
        for j, b in enumerate(items):
            gb, kb = keys_of(b)
            if ga != gb or ka == kb:
                continue
            diff = [k for k in ka if ka[k] != kb[k]]
            if len(diff) != 1:
                continue
            k = diff[0]
            lv = sorted({keys_of(x)[1][k] for x in items if keys_of(x)[0] == ga})
            if abs(lv.index(ka[k]) - lv.index(kb[k])) == 1:
                nb.append(j)
        out.append(nb)
    return out


_NB_CACHE: dict = {}


def _exit_keys(x: Exit):
    if x.kind == "time":
        return "time", {"n": x.n}
    return (x.kind, x.n), {"tp": x.tp, "sl": x.sl, "cap": x.cap, "trail": x.trail}


def plateau(cfg: int, space: Space, good: np.ndarray) -> float:
    key = id(space)
    if key not in _NB_CACHE:
        tn = _neighbours(space.triggers, lambda x: (x["trig"], x["kw"]))
        xn = _neighbours(space.exits, _exit_keys)
        _NB_CACHE.clear()
        _NB_CACHE[key] = (tn, xn)
    tn, xn = _NB_CACHE[key]
    ti, mi, xi, *fi = np.unravel_index(cfg, space.dims)
    cand = [np.ravel_multi_index((t2, mi, xi, *fi), space.dims) for t2 in tn[ti]]
    cand += [np.ravel_multi_index((ti, mi, x2, *fi), space.dims) for x2 in xn[xi]]
    return float(np.mean(good[cand])) if cand else float("nan")


def pick(head: pd.DataFrame, space: Space, k: int) -> pd.DataFrame:
    """K konfiguracji do OOS — tylko po IS: najpierw te z wszystkimi bramkami, potem reszta; po robust.
    Bez powtórek: 1 na (wyzwalacz, tryb), ≤ 3 na rodzinę wyzwalacza."""
    h = head.sort_values(["bramki", "robust"], ascending=[False, False])
    chosen, seen, fam = [], set(), {}
    for row in h.itertuples():
        ti, mi = np.unravel_index(int(row.cfg), space.dims)[:2]
        name = space.triggers[ti]["trig"]
        if (ti, mi) in seen or fam.get(name, 0) >= 3 or not np.isfinite(row.robust):
            continue
        seen.add((ti, mi))
        fam[name] = fam.get(name, 0) + 1
        chosen.append(row.Index)
        if len(chosen) == k:
            break
    return h.loc[chosen]


# ---------- etap 3: OOS dla wybranych ----------

def config_trades(frames: dict[str, pd.DataFrame], cfg: dict, cuts: tuple) -> pd.DataFrame:
    """Wszystkie transakcje jednej konfiguracji (IS i OOS) — ta sama droga co etapy 1–2, bez granicy IS."""
    _, cut_a, cut_is, _ = cuts
    rows = []
    for pair, raw in frames.items():
        raw = raw.reset_index(drop=True)
        P = prepare(raw)
        df = frame_index(raw)
        df.attrs["pair"] = pair
        F = R.features(df, ind)
        sig = R.TRIGGERS[cfg["trig"]](df, ind, **cfg["kw"]).astype(np.int8) * int(cfg["tryb"])
        o = _outcomes(P, F, sig, cfg["exit"], pair, None)
        if o is None:
            continue
        m = R.filter_mask(F, o["i"], o["d"], cfg["trend"], cfg["zmiennosc"], cfg["sesja"], cfg["dni"], cfg["kierunek"])
        sel = np.flatnonzero(m)
        kept = sel[_chain(o["e"][sel], o["x"][sel])]
        rows.append(pd.DataFrame({"pair": pair, "entry_ts": o["ts"][kept], "exit_ts": o["xts"][kept],
                                  "dir": o["d"][kept], "pips_net": o["p"][kept], "r_net": o["r"][kept]}))
    t = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["pair", "entry_ts", "exit_ts", "dir", "pips_net", "r_net"])
    t["okres"] = np.where(t.entry_ts < cut_a, "IS-A", np.where(t.entry_ts < cut_is, "IS-B", "OOS"))
    return t


def _stats(r: np.ndarray) -> tuple[int, float, float]:
    n = len(r)
    if n < 2:
        return n, float(r.mean()) if n else float("nan"), float("nan")
    s = r.std(ddof=1)
    return n, float(r.mean()), float(r.mean() / (s / math.sqrt(n))) if s > 0 else float("nan")


def oos_report(frames, space: Space, chosen: pd.DataFrame, cuts) -> pd.DataFrame:
    rows = []
    for rank, row in enumerate(chosen.itertuples(), 1):
        cfg = space.config(int(row.cfg))
        tr = config_trades(frames, cfg, cuts)
        o = tr[tr.okres == "OOS"]
        n, m, t = _stats(o.r_net.to_numpy(float))
        isr = tr[tr.okres != "OOS"]
        by_pair = o.groupby("pair").r_net.sum()
        rows.append({"rank_is": rank, "cfg": int(row.cfg), "opis": describe(cfg), "bramki": bool(row.bramki),
                     "nA": int(row.nA), "rA": row.rA, "tA": row.tA, "nB": int(row.nB), "rB": row.rB, "tB": row.tB,
                     "plaskowyz": row.plaskowyz, "pary_plus_is": int(row.pary_plus),
                     "is_check_n": int(len(isr)), "n_oos": n, "r_oos": m, "t_oos": t,
                     "pips_oos": float(o.pips_net.mean()) if n else float("nan"),
                     "win_oos": float((o.pips_net > 0).mean()) if n else float("nan"),
                     "pary_plus_oos": int((by_pair > 0).sum()), "pary_oos": int(len(by_pair))})
    return pd.DataFrame(rows)


def dsr_best(frames, space: Space, best_cfg: int, eligible: pd.DataFrame, cuts) -> dict:
    """DSR najlepszej konfiguracji IS: N = wszystkie konfiguracje z wystarczającą liczbą transakcji,
    wariancja Sharpe'a z tych samych prób (Bailey, López de Prado)."""
    from .validate import deflated_sharpe

    tr = config_trades(frames, space.config(best_cfg), cuts)
    r = tr[tr.okres != "OOS"].r_net.to_numpy(float)
    return deflated_sharpe(r, eligible.sharpe_is.to_numpy(float))


# ---------- całość ----------

def null_frames(frames: dict[str, pd.DataFrame], seed: int) -> dict[str, pd.DataFrame]:
    """Dane BEZ przewagi do testu zerowego: każda świeca odbita lustrzanie względem poprzedniego zamknięcia z losowym
    znakiem (open, high, low, close razem). Zostaje rozkład wielkości ruchów, zmienność w czasie (pora dnia, skupienia),
    luki i znaczniki czyszczenia; znika wszelka zależność kierunku od przeszłości. Żadna reguła nie ma tu przewagi,
    więc najlepszy wynik poszukiwania na takich danych = ile daje samo szczęście przy tej liczbie prób."""
    rng = np.random.default_rng(seed)
    out = {}
    for pair, df in frames.items():
        o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        prev = np.r_[o[0], c[:-1]]
        lr = {k: np.log(v / prev) for k, v in (("open", o), ("high", h), ("low", lo), ("close", c))}
        sgn = rng.choice((-1.0, 1.0), len(c))
        hi_r = np.where(sgn > 0, lr["high"], -lr["low"])
        lo_r = np.where(sgn > 0, lr["low"], -lr["high"])
        step = sgn * lr["close"]
        base = c[0] * np.exp(np.r_[0.0, np.cumsum(step)[:-1]])      # nowe poprzednie zamknięcie
        new = df.copy()
        new["open"] = base * np.exp(sgn * lr["open"])
        new["high"] = base * np.exp(hi_r)
        new["low"] = base * np.exp(lo_r)
        new["close"] = base * np.exp(step)
        out[pair] = new
    return out


def is_stage(frames: dict[str, pd.DataFrame], size: str, workers: int | None, log=print, label: str = "") -> dict:
    """Etapy 1–2 (tylko IS) na wszystkich parach, równolegle po parach."""
    t_start = time.time()
    space = Space(grid(size))
    cuts = cuts_for(frames)
    workers = workers or min(len(frames), os.cpu_count() or 1)
    acc = {k: np.zeros(space.n, np.float64 if k in FLOAT_KEYS else np.int64) for k in STAT_KEYS}
    progress = not label
    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(scan_pair, p, df, size, cuts, progress) for p, df in frames.items()]
            for f in as_completed(futs):
                pair, a = f.result()
                for k in STAT_KEYS:
                    acc[k] += a[k]
                log(f"  {label}{pair} gotowa ({(time.time() - t_start) / 60:.1f} min)")
    else:
        for p, df in frames.items():
            _, a = scan_pair(p, df, size, cuts, progress)
            for k in STAT_KEYS:
                acc[k] += a[k]
            log(f"  {label}{p} gotowa ({(time.time() - t_start) / 60:.1f} min)")
    t = table(acc, space)
    return {"space": space, "cuts": cuts, "table": t, "gates": gates(t, space)}


def run(frames: dict[str, pd.DataFrame], size: str = "duzy", top: int = TOP_K, workers: int | None = None,
        log=print, open_oos: bool = True, null: int = 0) -> dict:
    t_start = time.time()
    space = Space(grid(size))
    log(f"Poszukiwanie „{size}”: {space.n:,} konfiguracji × {len(frames)} par "
        f"({len(space.triggers)} wyzwalaczy × 2 tryby × {len(space.exits)} wyjść × {space.n_filters} kombinacji filtrów)"
        + (f" + {null} przebiegów zerowych" if null else "") + ".")
    st = is_stage(frames, size, workers, log)
    space, cuts, t, gt = st["space"], st["cuts"], st["table"], st["gates"]
    chosen = pick(gt["head"], space, top)
    out = {"size": size, "tested": space.n, "eligible": int(len(gt["eligible"])), "discovered": gt["discovered"],
           "confirmed": gt["confirmed"], "passed": int(gt["head"].bramki.sum()), "p_threshold": gt["p_threshold"],
           "t_threshold": gt["t_threshold"], "t_needed": gt["t_needed"],
           "best_tA": float(gt["eligible"].tA.max()) if len(gt["eligible"]) else float("nan"),
           "best_robust": float(gt["head"].robust.max()) if len(gt["head"]) else float("nan"),
           "cuts": [int(x) for x in cuts], "pairs": sorted(frames),
           "bars": {p: int(len(df)) for p, df in frames.items()}, "space": space, "table": t, "head": gt["head"],
           "chosen": chosen, "top": top, "engine_version": ENGINE_VERSION,
           "minutes_is": round((time.time() - t_start) / 60, 1)}
    # test zerowy PRZED otwarciem OOS — wynik nie może zależeć od tego, co pokaże OOS
    if null:
        nulls = []
        for k in range(null):
            log(f"Przebieg zerowy {k + 1}/{null} (dane bez przewagi)…")
            ns = is_stage(null_frames(frames, seed=1000 + k), size, workers, log, label=f"[zero {k + 1}] ")
            g = ns["gates"]
            nulls.append({"seed": 1000 + k, "best_robust": float(g["head"].robust.max()) if len(g["head"]) else float("nan"),
                          "discovered": g["discovered"], "confirmed": g["confirmed"], "passed": int(g["head"].bramki.sum())})
        out["null"] = nulls
    if open_oos and len(chosen):
        log(f"Etap 3: OOS dla {len(chosen)} konfiguracji wybranych po IS…")
        out["oos"] = oos_report(frames, space, chosen, cuts)
        out["dsr"] = dsr_best(frames, space, int(chosen.iloc[0].cfg), gt["eligible"], cuts)
    out["minutes"] = round((time.time() - t_start) / 60, 1)
    return out


# ---------- raport, zapis, strategia ----------

def _dt(x) -> str:
    return datetime.fromtimestamp(int(x), UTC).strftime("%Y-%m-%d")


def binom_tail(k: int, n: int) -> float:
    """P(X ≥ k), X ~ Binom(n, 0,5)."""
    return float(sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n) if n else float("nan")


def report(out: dict, ledger_count: int | None = None) -> str:
    c = out["cuts"]
    L = [f"# Głębokie poszukiwanie (D-044) — siatka „{out['size']}”", "",
         f"- Pary: {', '.join(out['pairs'])} · świece H1 Yahoo po czyszczeniu · silnik {out['engine_version']} · "
         f"{out['minutes']} min.",
         f"- IS-A (odkrycie): {_dt(c[0])} – {_dt(c[1])}; IS-B (potwierdzenie): do {_dt(c[2])}; "
         f"OOS: {_dt(c[2])} – {_dt(c[3])}.",
         f"- **Przetestowane konfiguracje: {out['tested']:,}** (jedna konfiguracja = te same zasady na wszystkich parach); "
         f"z ≥ {MIN_A} transakcji w IS-A i ≥ {MIN_B} w IS-B: {out['eligible']:,}.",
         (f"- Próg odkrycia po FDR 5% na wszystkie te konfiguracje: t ≥ {out['t_threshold']:.2f} "
          f"(p ≤ {out['p_threshold']:.1e}); " if out["discovered"] else
          f"- Próg odkrycia po FDR 5%: żadna konfiguracja go nie przeszła — najlepsza musiałaby mieć t IS-A ≥ "
          f"{out.get('t_needed', float('nan')):.2f}, najlepsza ma {out.get('best_tA', float('nan')):.2f}; ")
         + f"odkrytych: {out['discovered']:,}; potwierdzonych w IS-B: {out['confirmed']:,}; "
         f"wszystkie bramki IS (też ≥ 5/8 par na plusie i płaskowyż): **{out['passed']:,}**.",
         "- Ranking i wybór wyłącznie na IS (W1). Liczba konfiguracji otwartych na OOS ustalona przed liczeniem: "
         f"**{out['top']}**.", ""]
    if ledger_count:
        L += [f"> OOS tych danych otwierano już {ledger_count} raz(y) (ten raz wliczony) — każde kolejne spojrzenie "
              "obniża jego wartość jako testu.", ""]
    nl = out.get("null")
    if nl:
        best = np.array([x["best_robust"] for x in nl], float)
        beat = int(np.sum(best >= out["best_robust"]))
        L += ["## Test zerowy: to samo poszukiwanie na danych bez przewagi", "",
              f"- {len(nl)} przebiegów na świecach odbitych losowo (zostaje zmienność, znika kierunek). "
              f"Najlepszy wynik IS (min t IS-A, t IS-B) prawdziwych danych: **{out['best_robust']:.2f}**; "
              f"w przebiegach zerowych: mediana {np.nanmedian(best):.2f}, max {np.nanmax(best):.2f}.",
              f"- Przebiegi zerowe z wynikiem ≥ prawdziwego: **{beat} z {len(nl)}** "
              f"(p ≈ {(beat + 1) / (len(nl) + 1):.2f}). Duża liczba = najlepsza konfiguracja nie odróżnia się od szczęścia.",
              f"- Konfiguracje ze wszystkimi bramkami IS: prawdziwe dane {out['passed']}, zerowe "
              f"{', '.join(str(x['passed']) for x in nl)}.", ""]
    oos = out.get("oos")
    if oos is not None and len(oos):
        k = int((oos.r_oos > 0).sum())
        n = int(oos.r_oos.notna().sum())
        L += ["## Wynik na OOS (wszystkie wybrane, także przegrane)", "",
              f"- Dodatnich na OOS: **{k} z {n}** (gdyby to był czysty przypadek: P(≥ {k}) = {binom_tail(k, n):.3f}; "
              "konfiguracje są ze sobą skorelowane, więc ta liczba jest optymistyczna).",
              f"- Średnio na OOS: {oos.r_oos.mean():+.3f} R na transakcję vs {np.nanmean(np.minimum(oos.rA, oos.rB)):+.3f} R "
              "(gorsza z połówek IS) — spadek z IS do OOS to typowa miara przeuczenia.",
              f"- Korelacja rangi IS z wynikiem OOS: {oos.rank_is.rank().corr(oos.r_oos.rank()):+.2f} "
              "(ujemna = ranking IS nic nie przewiduje)."]
        d = out.get("dsr") or {}
        if d.get("dsr") is not None and np.isfinite(d.get("dsr", np.nan)):
            L += [f"- Deflated Sharpe najlepszej konfiguracji IS: **{d['dsr']:.3f}** przy {d['trials']:,} próbach "
                  f"(Sharpe na transakcję {d['sharpe']:.3f}, próg szczęścia {d['sharpe0']:.3f})."]
        L += ["", "| # IS | konfiguracja | bramki IS | n A | R A | t A | n B | R B | t B | płaskowyż "
              "| n OOS | R OOS | t OOS | pips OOS | pary + OOS |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for r in oos.itertuples():
            pl = "—" if pd.isna(r.plaskowyz) else f"{r.plaskowyz:.0%}"
            L.append(f"| {r.rank_is} | {r.opis} | {'✓' if r.bramki else '✗'} | {r.nA} | {r.rA:+.3f} | {r.tA:.1f} | {r.nB} | "
                     f"{r.rB:+.3f} | {r.tB:.1f} | {pl} | {r.n_oos} | {r.r_oos:+.3f} | {r.t_oos:.1f} | {r.pips_oos:+.1f} | "
                     f"{r.pary_plus_oos}/{r.pary_oos} |")
    L += ["", "## Jak to czytać", "",
          "- Przy tylu próbach najlepszy wynik IS jest w dużej mierze szczęściem — dlatego liczy się OOS całej listy, "
          "a nie najlepszy wiersz.",
          "- Jeżeli żadna konfiguracja nie przeszła bramek IS, a OOS listy jest bliski zera — w tej przestrzeni reguł "
          "nie ma przewagi, która przetrwa koszty. To też wynik.",
          "- Wybieranie spośród tych K tej, która wyszła najlepiej na OOS, łamie W1: OOS staje się kolejnym IS. "
          "Wygenerowana strategia bierze konfiguracje po kolejności IS, nie OOS.",
          "- Następny krok: `strategy.py` z tego katalogu do dashboardu (benchmark losowy, PBO, walk-forward, spread ×1,5), "
          "potem zamrożenie i forward test (W4) — jedyny naprawdę czysty test."]
    return "\n".join(L)


def strategy_code(out: dict, run_id: str, n: int = MAX_STRATEGY) -> str:
    """Strategia do dashboardu z ≤ n najlepszych konfiguracji IS (kolejność IS, nie OOS)."""
    space: Space = out["space"]
    chosen = out["chosen"].head(n)
    cfgs = [space.config(int(c)) for c in chosen.cfg]
    exits, ex_list = [], []
    for c in cfgs:
        if c["exit"] not in exits:
            exits.append(c["exit"])
    for e in exits:
        d = {"kind": e.kind, "n": e.n}
        for k in ("tp", "sl", "trail"):
            if getattr(e, k):
                d[k] = getattr(e, k)
        d["cap"] = e.cap
        ex_list.append(d)
    rows = []
    for c in cfgs:
        d = {k: v for k, v in c.items() if k != "exit"}
        rows.append(f"    {json.dumps(d, ensure_ascii=False)},   # {c['exit'].label()}")
    lines = [
        'HYPOTHESIS = """Konfiguracje wybrane przez ia5 search (D-044, przebieg ' + run_id + ") z "
        + f"{out['tested']:,}".replace(",", " ") + " przetestowanych, wyłącznie na IS (IS-A + IS-B).\n"
        "Hipoteza: reguły, które przeszły FDR, potwierdzenie i płaskowyż na 8 parach, mają przewagę ponad koszty.\n"
        "Uwaga: OOS był już raz otwarty przez poszukiwanie; DSR w karcie liczy tylko warianty tej strategii,\n"
        "nie wszystkie próby poszukiwania — rozstrzyga forward test po zamrożeniu (W4).\"\"\"",
        "",
        "CONFIGS = [",
        *rows,
        "]",
        "",
        'PARAMS = {"cfg": list(range(len(CONFIGS)))}',
        "",
        "# wyjścia wybranych konfiguracji (silnik liczy każdą konfigurację z każdym z nich)",
        "EXITS = [",
        *[f"    {json.dumps(e)}," for e in ex_list],
        "]",
        "",
        R.rules_source(),
        "",
        "",
        "def signals(df, p, ind):",
        '    return config_signal(df, ind, CONFIGS[p["cfg"]])',
        "",
    ]
    return "\n".join(lines)


LEDGER_NAME = "oos_ledger.json"


def ledger_add(home: Path, run_id: str, out: dict) -> int:
    """Dziennik otwarć OOS: kto, kiedy, ile konfiguracji, jaka granica. Zwraca liczbę otwarć tej samej granicy ±30 dni."""
    f = home / LEDGER_NAME
    try:
        rows = json.loads(f.read_text())
    except (FileNotFoundError, ValueError):
        rows = []
    rows.append({"run": run_id, "at": int(time.time()), "kind": "search", "size": out["size"], "tested": out["tested"],
                 "opened": int(len(out.get("oos", []))), "oos_from": out["cuts"][2], "oos_to": out["cuts"][3]})
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, indent=1))
    return sum(1 for r in rows if abs(r["oos_from"] - out["cuts"][2]) < 30 * 86400)


def save(out: dict, folder: Path, run_id: str, ledger_count: int | None = None) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    space: Space = out["space"]
    (folder / "search.md").write_text(report(out, ledger_count), encoding="utf-8")
    head = out["head"].head(300).copy()
    head.insert(1, "opis", [describe(space.config(int(c))) for c in head.cfg])
    head.to_csv(folder / "candidates_is.csv", index=False)       # tylko IS
    if out.get("oos") is not None:
        out["oos"].to_csv(folder / "top_oos.csv", index=False)
    if len(out["chosen"]):
        (folder / "strategy.py").write_text(strategy_code(out, run_id), encoding="utf-8")
    out["table"].to_parquet(folder / "all_is.parquet", index=False)  # wszystkie konfiguracje, tylko IS (lokalnie)
    meta = {k: v for k, v in out.items() if k not in ("space", "table", "head", "chosen", "oos")}
    meta["dsr"] = {k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in (out.get("dsr") or {}).items()}
    (folder / "search.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return folder
