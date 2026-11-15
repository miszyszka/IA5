"""Stocks (D-071) — metody rebalansowania: oceny przeceny, cele w paśmie ±B wokół udziałów Michała, symulacja tygodniowa.

Cel spółki i w tygodniu k: t_i = w_i · (1 + B · s_i), s_i ∈ [−1, 1] (dodatnia = spółka przeceniona → więcej kapitału),
potem rzut na sumę 1 w granicach [w_i(1 − B), w_i(1 + B)] (dokładny, jednym krokiem). w_i = udział docelowy Michała
przeliczony na spółki grające w danym tygodniu. Ocena s liczona tylko z cen do zamknięcia dnia oceny (poprzedni dzień sesji
przed wykonaniem) — wykonanie na otwarciu wtorku (B1). Wszystkie konfiguracje liczone naraz (wektorowo), te same tygodnie,
ten sam koszt (COST od wartości każdej strony transakcji).
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import indicators as ind
from .stk_config import (
    COMBOS,
    COST,
    FILTERS,
    LABEL_FILTER,
    LABEL_NORM,
    LABEL_SIGNAL,
    LABEL_STRENGTH,
    NORMS,
    SIGNALS,
    SMOOTH,
    STRENGTHS,
    THRESHOLDS,
)
from .stk_data import Panel

TINY = 1e-12


@dataclass(frozen=True)
class Config:
    i: int
    signal: str
    norm: str
    strength: str
    smooth: int
    filter: str
    threshold: float

    @property
    def id(self) -> str:
        return f"{self.signal}|{self.norm}|{self.strength}|s{self.smooth}|{self.filter}|h{self.threshold:g}"

    @property
    def label(self) -> str:
        return " · ".join([signal_label(self.signal), LABEL_NORM[self.norm], LABEL_STRENGTH[self.strength],
                           "ocena z tygodnia" if self.smooth == 1 else f"średnia z {self.smooth} tygodni", LABEL_FILTER[self.filter],
                           "każda zmiana" if self.threshold == 0 else f"próg {self.threshold * 100:g}% udziału"])

    def as_dict(self) -> dict:
        return {"id": self.id, "label": self.label, "signal": self.signal, "norm": self.norm, "strength": self.strength,
                "smooth": self.smooth, "filter": self.filter, "threshold": self.threshold}


def signal_label(sig: str) -> str:
    if sig in COMBOS:
        a, b = COMBOS[sig]
        return f"{signal_label(a)} + {signal_label(b)}"
    kind, n = SIGNALS[sig]
    return LABEL_SIGNAL[kind].format(n=n)


SIGNAL_NAMES: tuple[str, ...] = tuple(SIGNALS) + tuple(COMBOS)
GROUPS = [(s, nm, sm) for s in SIGNAL_NAMES for nm in NORMS for sm in SMOOTH]   # wspólne oceny (przed siłą, filtrem, progiem)
CONFIGS: list[Config] = [Config(i, s, nm, st, sm, f, h) for i, ((s, nm, sm), st, f, h) in
                         enumerate(itertools.product(GROUPS, STRENGTHS, FILTERS, THRESHOLDS))]
BY_ID = {c.id: c for c in CONFIGS}


def config_index(g: int, st: int, f: int, h: int) -> int:
    return ((g * len(STRENGTHS) + st) * len(FILTERS) + f) * len(THRESHOLDS) + h


# ---------- cechy dzienne ----------

def _segments(col: np.ndarray):
    """Kawałek od pierwszej wartości (indeks całkowitego zwrotu jest ffill w życiu spółki)."""
    ok = np.flatnonzero(np.isfinite(col))
    return (int(ok[0]), len(col)) if len(ok) else None


def daily_features(p: Panel) -> dict[str, np.ndarray]:
    """Surowe cechy (dni × spółki), niższa = taniej. Plus pomocnicze: vol63, below200, falling200."""
    n, m = p.tr.shape
    out = {k: np.full((n, m), np.nan) for k in list(SIGNALS) + ["vol63", "below200", "falling200"]}
    for j in range(m):
        seg = _segments(p.tr[:, j])
        if seg is None:
            continue
        a, b = seg
        s = pd.Series(p.tr[a:b, j])
        lg = np.log(s)
        for name, (kind, w) in SIGNALS.items():
            if kind == "dd":
                v = lg - np.log(s.rolling(w, min_periods=w).max())
            elif kind == "ma":
                v = lg - np.log(ind.sma(s, w))
            elif kind == "rel":
                v = lg - lg.shift(w)
            elif kind == "z":
                mu = lg.rolling(w, min_periods=w).mean()
                sd = lg.rolling(w, min_periods=w).std(ddof=0)
                v = (lg - mu) / sd.where(sd > 0)
            else:   # rsi
                v = ind.rsi(s, w) - 50.0
            out[name][a:b, j] = v.to_numpy(float)
        r = lg.diff()
        out["vol63"][a:b, j] = r.rolling(63, min_periods=40).std(ddof=0).to_numpy(float)
        sma200 = ind.sma(s, 200)
        out["below200"][a:b, j] = (s < sma200).astype(float).where(sma200.notna()).to_numpy(float)
        out["falling200"][a:b, j] = (sma200 < sma200.shift(20)).astype(float).where(sma200.shift(20).notna()).to_numpy(float)
    return out


# ---------- oceny tygodniowe ----------

def _rank_rows(c: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Ranking w przekroju → [−1, 1] (najtańsza = +1); poza grą albo bez wartości = 0."""
    out = np.zeros_like(c)
    for k in range(c.shape[0]):
        idx = np.flatnonzero(ok[k])
        if len(idx) < 2:
            continue
        r = pd.Series(c[k, idx]).rank(method="average").to_numpy() - 1
        out[k, idx] = 2 * r / (len(idx) - 1) - 1
    return out


def normalize(x: np.ndarray, elig: np.ndarray, norm: str, vol: np.ndarray | None = None) -> np.ndarray:
    """x: surowa cecha (tygodnie × spółki, niższa = taniej) → ocena przeceny w [−1, 1], dodatnia = tania."""
    c = -np.asarray(x, float)
    if norm == "vrank":
        c = c / np.where(np.isfinite(vol) & (vol > 0), vol, np.nan)
    ok = elig & np.isfinite(c)
    if norm in ("rank", "vrank"):
        return _rank_rows(c, ok)
    cc = np.where(ok, c, 0.0)
    cnt = ok.sum(axis=1, keepdims=True)
    mu = cc.sum(axis=1, keepdims=True) / np.maximum(cnt, 1)
    sd = np.sqrt((np.where(ok, (cc - mu) ** 2, 0.0)).sum(axis=1, keepdims=True) / np.maximum(cnt, 1))
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (cc - mu) / np.where((sd > 0) & (cnt >= 2), sd, np.nan)
    z = np.clip(z, -2, 2) / 2
    return np.where(ok & np.isfinite(z), z, 0.0)


def smooth(s: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return s
    c = np.cumsum(np.vstack([np.zeros((1, s.shape[1])), s]), axis=0)
    out = np.empty_like(s)
    for t in range(s.shape[0]):
        a = max(0, t - k + 1)
        out[t] = (c[t + 1] - c[a]) / (t + 1 - a)
    return out


def weekly_scores(feat: dict[str, np.ndarray], sig: np.ndarray, elig: np.ndarray) -> np.ndarray:
    """Oceny wszystkich grup (sygnał × normalizacja × wygładzenie): tablica (grupy, tygodnie, spółki), float32."""
    vol = feat["vol63"][sig]
    base = {}
    for name in SIGNALS:
        x = feat[name][sig]
        for nm in NORMS:
            base[(name, nm)] = normalize(x, elig, nm, vol)
    out = np.zeros((len(GROUPS), len(sig), elig.shape[1]), np.float32)
    for g, (s, nm, sm) in enumerate(GROUPS):
        if s in COMBOS:
            a, b = COMBOS[s]
            v = (base[(a, nm)] + base[(b, nm)]) / 2
        else:
            v = base[(s, nm)]
        out[g] = smooth(v, sm)
    return out


def apply_strength(s: np.ndarray, strength: str) -> np.ndarray:
    if strength == "half":
        return 0.5 * s
    if strength == "tails":
        return np.where(np.abs(s) >= 0.5, np.sign(s), 0.0)
    return s


def apply_filter(s: np.ndarray, flt: str, below: np.ndarray, falling: np.ndarray) -> np.ndarray:
    if flt == "knife":
        return np.where((s > 0) & (below > 0.5) & (falling > 0.5), 0.0, s)
    if flt == "trend":
        return np.where((s > 0) & (below > 0.5), 0.0, s)
    return s


def base_weights(w_user: np.ndarray, elig: np.ndarray) -> np.ndarray:
    """Udziały Michała przeliczone na spółki grające w danym tygodniu (tygodnie × spółki)."""
    w = np.where(elig, w_user[None, :], 0.0)
    tot = w.sum(axis=1, keepdims=True)
    return np.where(tot > 0, w / np.where(tot > 0, tot, 1), 0.0)


def project(w: np.ndarray, s: np.ndarray, band: float) -> np.ndarray:
    """Cel w paśmie: t = w(1 + B s), suma 1, t ∈ [w(1 − B), w(1 + B)]. w, s: (..., spółki); wiersze o sumie w = 0 → 0."""
    lo, hi = w * (1 - band), w * (1 + band)
    t0 = np.clip(w * (1 + band * s), lo, hi)
    e = t0.sum(axis=-1, keepdims=True) - 1.0
    dn = t0 - lo
    up = hi - t0
    sdn = dn.sum(axis=-1, keepdims=True)
    sup = up.sum(axis=-1, keepdims=True)
    t = np.where(e > 0, t0 - e * dn / np.where(sdn > 0, sdn, 1), t0 - e * up / np.where(sup > 0, sup, 1))
    return np.where(w.sum(axis=-1, keepdims=True) > 0, t, 0.0)


# ---------- symulacja (wszystkie konfiguracje naraz) ----------

@dataclass
class Weekly:
    """Dane tygodniowe wspólne dla metod: dni oceny i wykonania, mnożniki okresów, kto gra, kto ma świecę w dniu wykonania."""
    sig: np.ndarray
    exe: np.ndarray
    growth: np.ndarray
    elig: np.ndarray
    trade: np.ndarray
    w: np.ndarray            # udziały bazowe (tygodnie × spółki)
    below: np.ndarray
    falling: np.ndarray
    scores: np.ndarray       # (grupy, tygodnie, spółki)


def prepare(p: Panel, w_user: np.ndarray, feat: dict | None = None) -> Weekly:
    from .stk_data import eligible, period_growth, schedule, tradeable

    sig, exe = schedule(p)
    feat = feat or daily_features(p)
    elig = eligible(p, sig)
    return Weekly(sig=sig, exe=exe, growth=period_growth(p, exe), elig=elig, trade=tradeable(p, exe),
                  w=base_weights(np.asarray(w_user, float), elig), below=np.nan_to_num(feat["below200"][sig]),
                  falling=np.nan_to_num(feat["falling200"][sig]), scores=weekly_scores(feat, sig, elig))


def targets_for(W: Weekly, k: int, groups: np.ndarray | None, band: float) -> np.ndarray:
    """Cele tygodnia k dla wszystkich konfiguracji (K × spółki) w kolejności CONFIGS (albo tylko dla `groups`)."""
    g_idx = np.arange(len(GROUPS)) if groups is None else np.asarray(groups)
    s = W.scores[g_idx, k, :].astype(float)                                  # (G, n)
    rows = []
    for st in STRENGTHS:
        a = apply_strength(s, st)
        for f in FILTERS:
            rows.append(apply_filter(a, f, W.below[k], W.falling[k]))
    S = np.stack(rows, axis=1)                                               # (G, ST*F, n)
    T = project(W.w[k][None, None, :], S, band)                              # (G, ST*F, n)
    return np.repeat(T[:, :, None, :], len(THRESHOLDS), axis=2).reshape(-1, T.shape[-1])


def simulate(W: Weekly, target_fn, thresholds: np.ndarray, start: int, end: int, cost: float = COST,
             hold: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Tygodnie start..end (indeksy decyzji). target_fn(k) → (K, n). thresholds: (K,) próg względny do udziału bazowego.
    hold: (K,) bool — „kup i trzymaj” (handel tylko przy wejściu nowej spółki, finansowany ze wszystkich proporcjonalnie).
    Zwraca (zwroty log netto (K, tygodnie), obrót (K, tygodnie)); tydzień k = od wykonania k do wykonania k+1."""
    thr = np.asarray(thresholds, float)[:, None]
    K = len(thr)
    hold = np.zeros(K, bool) if hold is None else np.asarray(hold, bool)
    weeks = end - start
    ret = np.zeros((K, weeks))
    turn = np.zeros((K, weeks))
    cur = None
    for t in range(weeks):
        k = start + t
        tgt = target_fn(k)
        if cur is None:
            new = tgt.copy()
            tv = np.zeros(K)
        else:
            diff = tgt - cur
            tradeable = W.trade[k][None, :]
            want = np.abs(diff) > np.maximum(thr * W.w[k][None, :], TINY)
            entry = (cur <= TINY) & (tgt > TINY)
            exit_ = (tgt <= TINY) & (cur > TINY)
            mask = tradeable & np.where(hold[:, None], entry | exit_, want | entry | exit_)
            new = np.where(mask, tgt, cur)
            resid = 1.0 - new.sum(axis=1, keepdims=True)
            # reszta (z handlu tylko części spółek) rozkładana na spółki, którymi handlujemy, w proporcji celu;
            # przy „kup i trzymaj” — na wszystkie trzymane w proporcji wartości
            basis = np.where(hold[:, None], np.where(tradeable, new, 0.0), np.where(mask, tgt, 0.0))
            bs = basis.sum(axis=1, keepdims=True)
            fallback = np.where(tradeable, new, 0.0)
            basis = np.where(bs > TINY, basis, fallback)
            bs = basis.sum(axis=1, keepdims=True)
            new = new + resid * basis / np.where(bs > TINY, bs, 1.0)
            new = np.maximum(new, 0.0)
            tv = np.abs(new - cur).sum(axis=1)
        g = W.growth[k]
        g = np.where(np.isfinite(g), g, 1.0)
        R = (new * g[None, :]).sum(axis=1)
        ret[:, t] = np.log(np.maximum(R, TINY)) + np.log(np.maximum(1 - cost * tv, TINY))
        turn[:, t] = tv
        cur = new * g[None, :] / np.where(R > TINY, R, 1.0)[:, None]
    return ret, turn


def start_week(W: Weekly, w_user: np.ndarray, min_weight: float) -> int:
    """Pierwszy tydzień, w którym spółki z rokiem notowań mają ≥ min_weight udziałów docelowych Michała."""
    share = (np.where(W.elig, np.asarray(w_user, float)[None, :], 0.0).sum(axis=1)) / max(float(np.sum(w_user)), TINY)
    ok = np.flatnonzero(share >= min_weight - 1e-9)
    if not len(ok):
        raise ValueError("za mało spółek z rokiem notowań — backtest nie ma od czego zacząć")
    return int(ok[0])


def run_all(W: Weekly, band: float, start: int, end: int, cost: float = COST) -> tuple[np.ndarray, np.ndarray]:
    thr = np.array([c.threshold for c in CONFIGS])
    return simulate(W, lambda k: targets_for(W, k, None, band), thr, start, end, cost)


def run_one(W: Weekly, cfg: Config, band: float, start: int, end: int, cost: float = COST) -> tuple[np.ndarray, np.ndarray]:
    g = GROUPS.index((cfg.signal, cfg.norm, cfg.smooth))
    j = (STRENGTHS.index(cfg.strength) * len(FILTERS) + FILTERS.index(cfg.filter)) * len(THRESHOLDS) + THRESHOLDS.index(cfg.threshold)
    r, tv = simulate(W, lambda k: targets_for(W, k, [g], band)[j:j + 1], np.array([cfg.threshold]), start, end, cost)
    return r[0], tv[0]


def run_baselines(W: Weekly, start: int, end: int, cost: float = COST) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Stały podział co tydzień do celu (próg 0) i „kup i trzymaj”."""
    def fn(k):
        return np.vstack([W.w[k], W.w[k]])
    r, tv = simulate(W, fn, np.array([0.0, 0.0]), start, end, cost, hold=np.array([False, True]))
    return {"fixed": (r[0], tv[0]), "hold": (r[1], tv[1])}


def run_random(W: Weekly, band: float, start: int, end: int, paths: int, hold_weeks: int, seed: int = 7,
               cost: float = COST) -> np.ndarray:
    """W3: losowe oceny s ~ U(−1, 1) dla każdej spółki, zmieniane co `hold_weeks` tygodni, całe pasmo, próg 0."""
    rng = np.random.default_rng(seed)
    n = W.w.shape[1]
    blocks = (end - start) // hold_weeks + 2
    S = rng.uniform(-1, 1, size=(paths, blocks, n))

    def fn(k):
        return project(W.w[k][None, :], S[:, (k - start) // hold_weeks, :], band)
    r, _ = simulate(W, fn, np.zeros(paths), start, end, cost)
    return r


def targets_live(W: Weekly, cfg: Config, band: float, k: int, group: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Cel tygodnia k zamrożoną metodą (spółki) i ocena po sile i filtrze (do tabeli „dlaczego”).
    group: indeks w W.scores (gdy W.scores ma tylko oceny tej metody — portfel na żywo), inaczej z GROUPS."""
    g = GROUPS.index((cfg.signal, cfg.norm, cfg.smooth)) if group is None else group
    s = W.scores[g, k, :].astype(float)
    s = apply_filter(apply_strength(s, cfg.strength), cfg.filter, W.below[k], W.falling[k])
    return project(W.w[k], s, band), s


def ir(x) -> float:
    a = np.asarray(x, float)
    a = a[np.isfinite(a)]
    if len(a) < 10 or a.std(ddof=1) <= 0:
        return float("nan")
    return float(a.mean() / a.std(ddof=1) * math.sqrt(52))
