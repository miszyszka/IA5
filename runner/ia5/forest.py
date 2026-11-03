"""FOREST v2 (D-049): inwestorzy, którzy mówią tylko wtedy, gdy mają co powiedzieć.

Inwestor = reguła lustrzana: 1–3 warunki rynku i horyzont. Ta sama logika działa na long i short (warunek x ≥ e dla long to
x ≤ −e dla short), więc jednostronny dryf pary nie może udawać przewagi. Gdy warunki nie są spełnione, inwestor milczy.

Pula reguł jest stała (nasiono, progi z pierwszych 39 tygodni). Co 4 tygodnie las jest odświeżany: reguła wchodzi do lasu, gdy na
wszystkich dotąd zamkniętych danych ma zysk po spreadzie, minimalną liczbę transakcji i stabilny wynik; wypada, gdy to straci.
Do lasu wchodzi najwyżej 1000 reguł, korelacja głosów dwóch inwestorów ≤ 0,6. Każda decyzja używa lasu wybranego wcześniej niż
ona sama, więc cała historia po 39. tygodniu jest liczona poza próbą względem reguł (test: zmiana przyszłych cen niczego nie zmienia).

Model wykonania jak silnik: B1, B3, B8, B11, B12, wyjście czasowe `Exit("time", n=h, cap=h)`.
"""

from __future__ import annotations

import hashlib
import json
import math
import time

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from . import forest_rules as FR
from .config import PAIRS
from .engine import data_cancel, prepare
from .session import in_trading_hours

FOREST_VERSION = "2.0"
H = 3600
WEEK = 7 * 86400
HORIZONS = (24, 48)  # świece; spread jest stały, a ruch rośnie z czasem — na 1–5 świec koszt zjada wszystko
NH = len(HORIZONS)
DESIGN_END = 1777793400  # 2026-05-03: założenia v2 ustalone wyłącznie na świecach sprzed tej chwili (D-049)
N_RULES = 150_000
MAX_INVESTORS = 1000
START_WEEKS = 39  # pierwsze 9 miesięcy: tylko nauka
REFRESH_WEEKS = 4
PURGE_WEEKS = 1  # świece tuż przed odświeżeniem nie uczą: ich wynik na 48 świec nie byłby jeszcze znany
QUANT_DIR = (0.25, 0.5, 0.75, 0.9)
QUANT_FLT = (0.25, 0.5, 0.75)
MIN_EVENTS = 30  # minimalna liczba oddzielnych zdarzeń w danych nauki
T_MIN = 2.5  # zysk tygodniowy po spreadzie: co najmniej tyle odchyleń standardowych od zera
BLOCKS, MIN_BLOCKS = 4, 3  # zysk w co najmniej 3 z 4 kolejnych bloków czasu
BUY_SHARE = (0.25, 0.75)  # reguła musi działać w obie strony
RHO_CAP = 0.60
SHORTLIST = 4000
MODE_WITH, MODE_AGAINST, MODE_GE, MODE_LT = 1, -1, 2, 3


def forward(P: dict) -> np.ndarray:
    """r[t, k] = ruch od open t+1 do close t+h w ATR14 świecy t (+ = w górę, przed spreadem); NaN = brak danych albo B12."""
    n = len(P["o"])
    r = np.full((n, NH), np.nan)
    for k, h in enumerate(HORIZONS):
        t = np.arange(0, max(0, n - h))
        if not len(t):
            continue
        e, x = t + 1, t + h
        v = (P["c"][x] - P["o"][e]) / P["atr14"][t]
        v[data_cancel(P, t, e, x.astype(float))] = np.nan
        r[t, k] = v
    return r


class Panel:
    """Wszystkie świece wszystkich par jako wiersze; cechy i ruchy liczone raz."""

    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.pairs = sorted(frames)
        self.frames = {p: frames[p].reset_index(drop=True) for p in self.pairs}
        cur = FR.currency_panel(self.frames)
        self.P, xs, self.offset = {}, [], {}
        ts, pid, idx, atr, cost, r = [], [], [], [], [], []
        pos, names = 0, None
        for k, pair in enumerate(self.pairs):
            raw = self.frames[pair]
            P = prepare(raw)
            self.P[pair] = P
            f = FR.pair_features(pair, raw, cur)
            if names is None:
                names = list(f)
                self.family = {n: f[n][0] for n in names}
                self.label = {n: f[n][1] for n in names}
            xs.append(np.column_stack([f[n][2] for n in names]))
            m = len(raw)
            self.offset[pair] = pos
            pos += m
            ts.append(P["ts"])
            pid.append(np.full(m, k, np.int16))
            idx.append(np.arange(m))
            atr.append(P["atr14"])
            with np.errstate(divide="ignore", invalid="ignore"):
                cost.append(PAIRS[pair].spread_pips * PAIRS[pair].pip / P["atr14"])
            r.append(forward(P))
        self.names, self.col = names, {n: j for j, n in enumerate(names)}
        self.X = np.vstack(xs)
        self.ts, self.pid, self.idx = np.concatenate(ts), np.concatenate(pid), np.concatenate(idx)
        self.atr, self.cost, self.r = np.concatenate(atr), np.concatenate(cost), np.vstack(r)
        self.window = in_trading_hours(self.ts + H)
        self.n = len(self.ts)
        self.t0 = int(self.ts.min())

    def row(self, pair: str, i: int) -> int:
        return self.offset[pair] + i

    def week(self, ts) -> np.ndarray:
        return (np.asarray(ts) - self.t0) // WEEK

    def usable(self) -> np.ndarray:
        return self.window & (self.idx >= FR.WARMUP) & np.isfinite(self.cost)


def make_conditions(pn: Panel, t_end: int) -> list[dict]:
    """Warunki z progami policzonymi wyłącznie na świecach sprzed t_end."""
    ok = pn.usable() & (pn.ts < t_end)
    out = []
    for j, n in enumerate(pn.names):
        fam = pn.family[n]
        x = pn.X[ok, j].astype(float)
        x = x[np.isfinite(x)]
        if not len(x):
            continue
        if FR.has_direction(n, fam):
            c = FR.center(n)
            for e in sorted(set(np.round(np.quantile(np.abs(x - c), QUANT_DIR), 4))):
                out.append({"f": n, "fam": fam, "label": pn.label[n], "kind": "dir", "e": float(e), "c": c})
        else:
            u = np.unique(x)
            edges = (u[:-1] + u[1:]) / 2 if len(u) <= 3 else np.unique(np.round(np.quantile(x, QUANT_FLT), 4))
            for e in edges:
                out.append({"f": n, "fam": fam, "label": pn.label[n], "kind": "flt", "e": float(e), "c": 0.0})
    return out


def condition_masks(X: np.ndarray, col: dict, conds: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """(warunek, wiersz): U = strona long, D = strona short. Dla filtra obie są takie same. NaN = fałsz."""
    U = np.zeros((len(conds), len(X)), bool)
    D = np.zeros_like(U)
    with np.errstate(invalid="ignore"):
        for k, c in enumerate(conds):
            x = X[:, col[c["f"]]].astype(float)
            if c["kind"] == "dir":
                y = x - c["c"]
                U[k], D[k] = (y > 0, y < 0) if c["e"] == 0 else (y >= c["e"], y <= -c["e"])
            else:
                U[k] = D[k] = x >= c["e"]
    return U, D


def make_rules(conds: list[dict], n: int, seed: int) -> list[tuple]:
    """Pula reguł: każda ma co najmniej jeden warunek z kierunkiem (za nim albo przeciw niemu) i do 2 kolejnych."""
    rng = np.random.default_rng(seed)
    dirs = [k for k, c in enumerate(conds) if c["kind"] == "dir"]
    flts = [k for k, c in enumerate(conds) if c["kind"] == "flt"]
    feat = [c["f"] for c in conds]
    seen = {((k, m),) for k in dirs for m in (MODE_WITH, MODE_AGAINST)}
    guard = 0
    while len(seen) < n and guard < n * 20:
        guard += 1
        d = int(rng.integers(2, 4))
        k = dirs[int(rng.integers(len(dirs)))]
        it, used = [(k, MODE_WITH if rng.random() < 0.5 else MODE_AGAINST)], {feat[k]}
        for _ in range(d - 1):
            if rng.random() < 0.55 or not flts:
                k, m = dirs[int(rng.integers(len(dirs)))], MODE_WITH if rng.random() < 0.5 else MODE_AGAINST
            else:
                k, m = flts[int(rng.integers(len(flts)))], MODE_GE if rng.random() < 0.5 else MODE_LT
            if feat[k] not in used:
                used.add(feat[k])
                it.append((k, m))
        if len(it) >= 2:
            seen.add(tuple(sorted(it)))
    return sorted(seen)


def rule_masks(U: np.ndarray, D: np.ndarray, rule, idx=None) -> tuple[np.ndarray, np.ndarray]:
    """(kiedy reguła mówi BUY, kiedy SELL)."""
    b = s = None
    for k, m in rule:
        u = U[k] if idx is None else U[k][idx]
        d = D[k] if idx is None else D[k][idx]
        x, y = (u, d) if m == MODE_WITH else (d, u) if m == MODE_AGAINST else (u, u) if m == MODE_GE else (~u, ~u)
        b = x if b is None else b & x
        s = y if s is None else s & y
    return b, s


def rule_text(rule, conds: list[dict]) -> str:
    """Opis reguły od strony BUY; strona SELL jest lustrem."""
    parts = []
    for k, m in rule:
        c = conds[k]
        e, name, mid = c["e"], c["label"], c["c"]
        if m == MODE_GE:
            parts.append(f"{name} ≥ {e:g}" if not (e == 0.5 and c["fam"] == "kalendarz") else name)
        elif m == MODE_LT:
            parts.append(f"{name} < {e:g}" if not (e == 0.5 and c["fam"] == "kalendarz") else f"nie: {name}")
        else:
            a, op = (mid + e, "≥") if m == MODE_WITH else (mid - e, "≤")
            parts.append(f"{name} {op} {a:g}")
    return " · ".join(parts)


class Cube:
    """Wyniki każdej reguły tydzień po tygodniu: dzięki temu odświeżenie lasu to sekundy, a nie godziny."""

    def __init__(self, pn: Panel, rules: list[tuple], conds: list[dict], log=print):
        t0 = time.time()
        self.rows = np.flatnonzero(pn.usable())
        self.wk = pn.week(pn.ts[self.rows]).astype(np.int32)
        self.nw = int(self.wk.max()) + 1 if len(self.wk) else 0
        self.U, self.D = condition_masks(pn.X[self.rows], pn.col, conds)
        self.rules = rules
        nr = len(rules)
        self.S = np.zeros((nr, self.nw, NH), np.float32)  # suma ruchów w stronę reguły
        self.C = np.zeros((nr, self.nw), np.float32)  # suma kosztów
        self.E = np.zeros((nr, self.nw), np.float32)  # oddzielne zdarzenia
        self.B = np.zeros((nr, self.nw), np.int32)  # ile razy BUY
        self.N = np.zeros((nr, self.nw), np.int32)  # ile razy reguła mówiła
        r = np.nan_to_num(pn.r[self.rows])
        cost = pn.cost[self.rows]
        key = pn.idx[self.rows].astype(np.int64) + pn.pid[self.rows].astype(np.int64) * 1_000_000
        for c, rule in enumerate(rules):
            b, s = rule_masks(self.U, self.D, rule)
            ib, ik = np.flatnonzero(b), np.flatnonzero(s)
            if len(ib) + len(ik) < 30:
                continue
            i = np.r_[ib, ik]
            w = self.wk[i]
            sg = np.r_[np.ones(len(ib)), -np.ones(len(ik))]
            for h in range(NH):
                self.S[c, :, h] = np.bincount(w, weights=sg * r[i, h], minlength=self.nw)
            self.C[c] = np.bincount(w, weights=cost[i], minlength=self.nw)
            ev = []
            for part in (ib, ik):
                if len(part):
                    # ta sama seria świec z rzędu to jedno zdarzenie
                    o = part[np.argsort(key[part], kind="stable")]
                    ev.append(self.wk[o[np.r_[True, np.diff(key[o]) != 1]]])
            self.E[c] = np.bincount(np.concatenate(ev), minlength=self.nw)
            self.B[c] = np.bincount(self.wk[ib], minlength=self.nw)
            self.N[c] = np.bincount(w, minlength=self.nw)
            if (c + 1) % 50_000 == 0:
                log(f"  reguły: {c + 1:,}/{nr:,} · {(time.time() - t0) / 60:.1f} min")


def select(cube: Cube, week: int, cap: int = MAX_INVESTORS, rho: float = RHO_CAP) -> tuple[pd.DataFrame, dict]:
    """Las na tydzień `week`: tylko tygodnie zamknięte przed odświeżeniem (bez ostatniego — ich wyniku jeszcze nie znamy)."""
    b = week - PURGE_WEEKS
    C = cube.C[:, :b]
    nw = C.shape[1]
    E = cube.E[:, :b].sum(1)
    blocks = np.array_split(np.arange(nw), BLOCKS)
    share = cube.B[:, :b].sum(1) / np.maximum(1, cube.N[:, :b].sum(1))
    parts = []
    for h in range(NH):
        p = cube.S[:, :b, h] - C
        m, sd = p.mean(1), p.std(1, ddof=1)
        with np.errstate(all="ignore"):
            t = np.nan_to_num(m / sd * math.sqrt(nw))
        pos = sum((p[:, x].sum(1) > 0).astype(int) for x in blocks)
        i = np.flatnonzero((E >= MIN_EVENTS) & (t >= T_MIN) & (pos >= MIN_BLOCKS) & (share >= BUY_SHARE[0]) & (share <= BUY_SHARE[1]))
        parts.append(pd.DataFrame({"rule": i, "k": h, "t": t[i], "ev": E[i]}))
    t = pd.concat(parts, ignore_index=True)
    t = t.sort_values(["t", "rule"], ascending=[False, True], kind="stable").drop_duplicates("rule")
    passed = len(t)
    t = t.head(SHORTLIST)
    tr = np.flatnonzero(cube.wk < b)[::3]
    vecs, keep = [], []
    for j, c in enumerate(t["rule"].to_numpy()):
        bu, se = rule_masks(cube.U, cube.D, cube.rules[c], tr)
        v = bu.astype(np.float32) - se.astype(np.float32)
        v -= v.mean()
        nr = np.linalg.norm(v)
        if nr == 0:
            continue
        v /= nr
        if vecs and np.abs(np.asarray(vecs) @ v).max() > rho:
            continue
        vecs.append(v)
        keep.append(j)
        if len(keep) == cap:
            break
    sel = t.iloc[keep].reset_index(drop=True)
    info = {"week": int(week), "passed": int(passed), "kept": len(sel)}
    return sel, info


def null_blocks(frames: dict[str, pd.DataFrame], seed: int, hours: int = 24) -> dict[str, pd.DataFrame]:
    """Dane bez przewagi: na każdy blok czasu wszystkie pary dostają ten sam losowy znak. Zostaje zmienność, korelacja między parami
    i ruch wewnątrz bloku, a znika zależność następnych dni od przeszłości. Żadna reguła długiego horyzontu nie ma tu przewagi."""
    rng = np.random.default_rng(seed)
    t0 = min(int(d["ts"].iloc[0]) for d in frames.values())
    t1 = max(int(d["ts"].iloc[-1]) for d in frames.values())
    sign = rng.choice((-1.0, 1.0), (t1 - t0) // (hours * H) + 2)
    out = {}
    for p, df in frames.items():
        o, hi, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
        prev = np.r_[o[0], c[:-1]]
        lr = {k: np.log(v / prev) for k, v in (("o", o), ("h", hi), ("l", lo), ("c", c))}
        s = sign[((df["ts"].to_numpy() - t0) // (hours * H)).astype(int)]
        step = s * lr["c"]
        base = c[0] * np.exp(np.r_[0.0, np.cumsum(step)[:-1]])
        new = df.copy()
        new["open"] = base * np.exp(s * lr["o"])
        new["high"] = base * np.exp(np.where(s > 0, lr["h"], -lr["l"]))
        new["low"] = base * np.exp(np.where(s > 0, lr["l"], -lr["h"]))
        new["close"] = base * np.exp(step)
        out[p] = new
    return out


def pool_id(conds: list[dict], seed: int) -> str:
    core = json.dumps({"c": conds, "s": seed, "v": FOREST_VERSION, "n": N_RULES}, sort_keys=True)
    return hashlib.sha256(core.encode()).hexdigest()[:12]


def new_forest(pn: Panel, seed: int = 5) -> dict:
    """Pula: progi z pierwszych 39 tygodni, reguły z nasiona. Niezmienne przez cały eksperyment."""
    conds = make_conditions(pn, pn.t0 + START_WEEKS * WEEK)
    return {
        "version": FOREST_VERSION,
        "engine_version": ENGINE_VERSION,
        "created": int(time.time()),
        "pairs": pn.pairs,
        "t0": pn.t0,
        "seed": seed,
        "conds": conds,
        "id": pool_id(conds, seed),
        "generations": [],
    }
