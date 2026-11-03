"""FOREST (D-048): 1000 wirtualnych inwestorów, Manager, mapy głosów — demokratyczny eksperyment samouczący się.

Inwestor (zamrożony po kuciu) = tablica decyzyjna: 1–4 testy cech rynku dzielą każdą świecę na stany, a każdy stan ma
policzone na danych kucia oczekiwane ruchy na 1–5 świec. Dzięki temu inwestor ZAWSZE ma zdanie: każda świeca wpada w jakiś
stan, stan mówi BUY albo SELL i ile (statystycznie) można zarobić na każdym horyzoncie. Jedna reguła działa na 8 parach.

Oś czasu (granice jak w search.py, wspólne dla par):
  KUCIE [0, 50%)      wybór 1000 inwestorów i ich tablic. Walidacja krzyżowa blokami czasu.
  MAPY  [50, 75%)     inwestorzy nie widzieli tych świec; Manager zbiera pierwsze mapy. Razem z kuciem to IS (W1).
  OOS   [75, 100%]    ostatnie 25% (W1): ten sam proces, nic już nie jest dobierane.
  LIVE                nowe świece po kuciu: paper trading przy działającym ia5 start.

Model wykonania jak silnik: sygnał na zamknięciu t, wejście na open t+1 (B1), wyjście czasowe na zamknięciu t+h
(Exit("time", n=h, cap=h)), spread raz (B3), wejścia w oknie 07–17 (B11), jedna pozycja na parę (B8), transakcja nachodząca
na przerwę lub świecę uzupełnioną anulowana (B12). Test: wynik każdej transakcji = engine.simulate co do pipsa.
"""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
import os
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from . import forest_rules as FR
from .config import OOS_FRACTION, PAIRS
from .engine import data_cancel, prepare
from .session import in_trading_hours

FOREST_VERSION = "1.0"  # zmiana logiki kucia, Managera albo map = podbicie (jak B10)
H = 3600
HORIZONS = (1, 2, 3, 4, 5)
NH = len(HORIZONS)
N_INVESTORS = 1000
N_CANDIDATES = 300_000
SPLIT_FORGE = 0.50  # KUCIE [0, 50%), MAPY [50%, 75%), OOS [75%, 100%]
FOLDS = 4  # bloki czasu w walidacji krzyżowej kucia
MIN_LEAF = 100  # każdy stan inwestora musi mieć tyle świec w kuciu, inaczej to nie statystyka
MIN_FOLDS_POS = 3  # dodatni wynik poza próbą w co najmniej tylu blokach
BUY_SHARE = (0.15, 0.85)  # inwestor musi zmieniać zdanie: udział głosów BUY na danych kucia
RHO_CAP = 0.60  # największa dozwolona |korelacja| głosów dwóch inwestorów
FAMILY_CAP = 0.25  # najwyżej tyle inwestorów z jedną rodziną główną
SHORTLIST = 40_000
SHRINK = 30.0  # ściąganie średnich stanu do zera (świece „pseudo-zerowe”)
QUANTILES = (0.15, 0.35, 0.50, 0.65, 0.85)
MAX_DEPTH = 4


def popcount(a: np.ndarray) -> np.ndarray:
    return np.bitwise_count(a)


# ---------- dane: każda świeca każdej pary jako jeden wiersz ----------


def cuts_for(frames: dict[str, pd.DataFrame]) -> dict:
    t0 = min(int(df["ts"].iloc[0]) for df in frames.values())
    t1 = max(int(df["ts"].iloc[-1]) for df in frames.values())
    return {"t0": t0, "forge": int(t0 + SPLIT_FORGE * (t1 - t0)), "oos": int(t0 + (1 - OOS_FRACTION) * (t1 - t0)), "t1": t1}


def forward(P: dict) -> np.ndarray:
    """r[t, k] = ruch rynku od wejścia na open t+1 do zamknięcia t+h, w ATR14 świecy t (+ = w górę, przed spreadem).
    Wiersz bez pełnych danych albo anulowany (B12) = NaN."""
    n = len(P["o"])
    r = np.full((n, NH), np.nan, np.float64)
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
    """Wiersze: wszystkie świece wszystkich par. Cechy i ruchy liczone raz."""

    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.pairs = sorted(frames)
        self.frames = {p: frames[p].reset_index(drop=True) for p in self.pairs}
        cur = FR.currency_panel(self.frames)
        self.P, xs, self.offset = {}, [], {}
        ts, pid, idx, atr, cost, r = [], [], [], [], [], []
        pos = 0
        names = None
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
            spread = PAIRS[pair].spread_pips * PAIRS[pair].pip
            with np.errstate(divide="ignore", invalid="ignore"):
                cost.append(spread / P["atr14"])
            r.append(forward(P))
        self.names = names
        self.col = {n: j for j, n in enumerate(names)}
        self.X = np.vstack(xs)
        self.ts, self.pid, self.idx = np.concatenate(ts), np.concatenate(pid), np.concatenate(idx)
        self.atr, self.cost, self.r = np.concatenate(atr), np.concatenate(cost), np.vstack(r)
        self.window = in_trading_hours(self.ts + H)  # B11: wejście na świecy o ts + 1 h
        self.n = len(self.ts)

    def row(self, pair: str, i: int) -> int:
        return self.offset[pair] + i


# ---------- kucie ----------


def forge_sample(pn: Panel, cut: int) -> np.ndarray:
    """Wiersze kucia: okno B11, po rozgrzewce, z pełnym wynikiem na 5 świec zamkniętym przed granicą (czysta granica)."""
    ok = (pn.ts + (NH + 1) * H <= cut) & (pn.idx >= FR.WARMUP) & pn.window
    ok &= np.isfinite(pn.r).all(1) & np.isfinite(pn.cost)
    return np.flatnonzero(ok)


def make_tests(pn: Panel, sample: np.ndarray) -> list[dict]:
    """Testy „cecha ≥ próg”. Progi z próby kucia (nigdy z całej historii); cechy zero-jedynkowe mają jeden próg."""
    tests = []
    x = pn.X[sample]
    for j, name in enumerate(pn.names):
        v = x[:, j]
        v = v[np.isfinite(v)].astype(float)
        if not len(v):
            continue
        u = np.unique(v)
        if len(u) <= 3:
            edges = (u[:-1] + u[1:]) / 2
        else:
            edges = np.unique(np.round(np.quantile(v, QUANTILES), 5))
        for e in edges:
            tests.append({"f": name, "e": float(e), "fam": pn.family[name], "label": pn.label[name]})
    return tests


def test_columns(X: np.ndarray, names: dict, tests: list[dict]) -> np.ndarray:
    """Macierz (testy, wiersze) uint8; NaN = fałsz. Kolumna fikcyjna na końcu (same zera) dopełnia płytsze drzewa."""
    out = np.zeros((len(tests) + 1, len(X)), np.uint8)
    with np.errstate(invalid="ignore"):
        for k, t in enumerate(tests):
            out[k] = X[:, names[t["f"]]] >= t["e"]
    return out


def make_candidates(tests: list[dict], n: int, seed: int) -> list[tuple[int, ...]]:
    """Wszystkie pojedyncze testy + losowe kombinacje 2–4 testów na różnych cechach: pół z jednej rodziny, pół mieszane."""
    rng = np.random.default_rng(seed)
    by_fam: dict[str, list[int]] = {}
    for k, t in enumerate(tests):
        by_fam.setdefault(t["fam"], []).append(k)
    fams = sorted(by_fam)
    feat = [t["f"] for t in tests]
    out = {(k,) for k in range(len(tests))}
    u = rng.random((int(n * 2.5) + 1000, 6))
    pick = rng.random((len(u), 4))
    for row, pk in zip(u, pick):
        if len(out) >= n:
            break
        d = 2 if row[0] < 0.30 else 3 if row[0] < 0.75 else 4
        pure = row[1] < 0.5
        f0 = fams[int(row[2] * len(fams))]
        items, used = [], set()
        for k in range(d):
            fam = f0 if pure or k == 0 else fams[int(row[3 + k % 3] * len(fams))]
            lst = by_fam[fam]
            t = lst[int(pk[k] * len(lst))]
            if feat[t] in used:
                continue
            used.add(feat[t])
            items.append(t)
        if len(items) >= 2:
            out.add(tuple(sorted(items)))
    return sorted(out)


_W: dict = {}


def _init_worker(cols, y, sd, fold, K):
    _W.update(cols=cols, y=y, sd=sd, fold=fold, K=K)


def _score_block(block: list[tuple[int, ...]]) -> np.ndarray:
    """Walidacja krzyżowa kandydatów: kierunek stanu z pozostałych bloków, ocena na bloku odłożonym.
    Zwraca (score, liczba dodatnich bloków, najmniejszy stan)."""
    cols, y, sd, fold, K = _W["cols"], _W["y"], _W["sd"], _W["fold"], _W["K"]
    out = np.zeros((len(block), 3))
    total = y.shape[0]
    for c, tree in enumerate(block):
        leaf = np.zeros(total, np.int32)
        for b, t in enumerate(tree):
            leaf += cols[t].astype(np.int32) << b
        nleaf = 1 << len(tree)
        key = leaf + nleaf * fold
        N = np.bincount(key, minlength=K * nleaf).reshape(K, nleaf)
        S = np.stack([np.bincount(key, weights=y[:, h], minlength=K * nleaf) for h in range(NH)]).reshape(NH, K, nleaf)
        other = S.sum(1, keepdims=True) - S
        d = np.sign(other.sum(0))
        d[d == 0] = 1
        perf = (d[None] * S).sum(2)  # (horyzont, blok): suma ruchów w stronę prognozy
        std = perf / sd[:, None]
        fold_n = N.sum(1)
        out[c] = (std.sum(1).mean() / math.sqrt(total), ((std.mean(0) / fold_n) > 0).sum(), N.sum(0).min())
    return out


def score_candidates(cands, cols, y, sd, fold, K, workers: int, log=print) -> np.ndarray:
    size = 4000
    blocks = [cands[i : i + size] for i in range(0, len(cands), size)]
    t0 = time.time()
    if workers > 1:
        res = [None] * len(blocks)
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=workers, mp_context=ctx, initializer=_init_worker, initargs=(cols, y, sd, fold, K)) as ex:
            for k, r in enumerate(ex.map(_score_block, blocks)):
                res[k] = r
                if (k + 1) % max(1, len(blocks) // 5) == 0:
                    log(f"  kandydaci: {min((k + 1) * size, len(cands)):,}/{len(cands):,} · {(time.time() - t0) / 60:.1f} min")
    else:
        _init_worker(cols, y, sd, fold, K)
        res = []
        for k, b in enumerate(blocks):
            res.append(_score_block(b))
            if (k + 1) % max(1, len(blocks) // 5) == 0:
                log(f"  kandydaci: {min((k + 1) * size, len(cands)):,}/{len(cands):,} · {(time.time() - t0) / 60:.1f} min")
    return np.vstack(res) if res else np.zeros((0, 3))


def fit_table(tree: tuple[int, ...], cols: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Tablica stanów: oczekiwany ruch (ATR) na 5 horyzontów, ze ściągnięciem do zera, i liczba świec w stanie."""
    leaf = np.zeros(y.shape[0], np.int32)
    for b, t in enumerate(tree):
        leaf += cols[t].astype(np.int32) << b
    nleaf = 1 << len(tree)
    n = np.bincount(leaf, minlength=nleaf).astype(float)
    S = np.stack([np.bincount(leaf, weights=y[:, h], minlength=nleaf) for h in range(NH)], axis=1)
    return S / (n[:, None] + SHRINK), n


def primary_family(tree, tests) -> str:
    fams = [tests[t]["fam"] for t in tree]
    return sorted(set(fams), key=lambda f: (-fams.count(f), FR.FAMILIES.index(f)))[0]


def select_diverse(
    order: np.ndarray, votes: np.ndarray, fam: list[str], k: int, cap: float, fam_cap: float, log=print
) -> tuple[list[int], dict]:
    """Chciwy dobór od najlepszego: kandydat wchodzi tylko, gdy jego głosy nie są skorelowane (także odwrotnie) z nikim z
    już wybranych ponad `cap`, a jego rodzina główna nie przekroczyła limitu. To „1000 różnych”, a nie 1000 kopii lidera."""
    n = votes.shape[1]
    packed = np.packbits(votes > 0, axis=1)
    pad = (-packed.shape[1]) % 8
    packed = np.pad(packed, ((0, 0), (0, pad))).view(np.uint64)
    mean = votes.mean(1).astype(float)
    sd = np.sqrt(np.maximum(1e-9, 1 - mean**2))
    chosen: list[int] = []
    sel_bits = np.zeros((k, packed.shape[1]), np.uint64)
    sel_m, sel_s = np.zeros(k), np.zeros(k)
    per_fam: dict[str, int] = {}
    limit = int(math.ceil(k * fam_cap))
    rej_rho = rej_fam = 0
    for c in order:
        if per_fam.get(fam[c], 0) >= limit:
            rej_fam += 1
            continue
        m = len(chosen)
        if m:
            diff = popcount(sel_bits[:m] ^ packed[c]).sum(1)
            agree = 1 - 2 * diff / n
            rho = (agree - sel_m[:m] * mean[c]) / (sel_s[:m] * sd[c])
            if np.abs(rho).max() > cap:
                rej_rho += 1
                continue
        sel_bits[m] = packed[c]
        sel_m[m], sel_s[m] = mean[c], sd[c]
        chosen.append(int(c))
        per_fam[fam[c]] = per_fam.get(fam[c], 0) + 1
        if len(chosen) == k:
            break
    return chosen, {"odrzuceni_korelacja": rej_rho, "odrzuceni_rodzina": rej_fam, "rodziny": per_fam}


def diversity(votes: np.ndarray) -> dict:
    """Ile niezależnych głosów naprawdę jest: N_eff = (Σλ)²/Σλ² z macierzy korelacji głosów."""
    v = votes.astype(np.float32)
    v = (v - v.mean(1, keepdims=True)) / (v.std(1, keepdims=True) + 1e-9)
    c = v @ v.T / v.shape[1]
    np.fill_diagonal(c, np.nan)
    a = np.abs(c)
    m = len(c)
    return {
        "srednia_abs_rho": float(np.nanmean(a)),
        "max_abs_rho": float(np.nanmax(a)),
        "p95_abs_rho": float(np.nanquantile(a, 0.95)),
        "n_eff": float(m**2 / (m + np.nansum(c**2))),
    }


def forest_id(fr: dict) -> str:
    core = json.dumps({"tests": fr["tests"], "inv": [(i["tests"], i["table"]) for i in fr["investors"]]}, sort_keys=True)
    return hashlib.sha256(core.encode()).hexdigest()[:12]


def forge(
    frames: dict[str, pd.DataFrame],
    n_candidates: int = N_CANDIDATES,
    n_investors: int = N_INVESTORS,
    seed: int = 1,
    workers: int | None = None,
    log=print,
    pn: Panel | None = None,
    rho_cap: float = RHO_CAP,
) -> dict:
    """Kucie lasu: tylko świece z pierwszych 50% historii."""
    t_start = time.time()
    pn = pn or Panel(frames)
    cuts = cuts_for(pn.frames)
    sample = forge_sample(pn, cuts["forge"])
    log(f"Kucie: {len(sample):,} świec (8 par × okno 07–17, pierwsze 50% historii), {len(pn.names)} cech.")
    tests = make_tests(pn, sample)
    cols = test_columns(pn.X[sample], pn.col, tests)
    # bez dryfu pary: rok trendu EUR/USD to nie wiedza o rynku — bez tego las głosuje BUY z przyzwyczajenia (D-048)
    y = pn.r[sample].copy()
    pair_id = pn.pid[sample]
    for k in np.unique(pair_id):
        y[pair_id == k] -= y[pair_id == k].mean(0)
    sd = y.std(0)
    ts = pn.ts[sample]
    edges = np.quantile(ts, np.linspace(0, 1, FOLDS + 1)[1:-1])
    fold = np.searchsorted(edges, ts).astype(np.int32)
    cands = make_candidates(tests, n_candidates, seed)
    workers = workers or min(8, os.cpu_count() or 1)
    log(f"  {len(tests)} testów, {len(cands):,} kandydatów, {workers} proc.")
    sc = score_candidates(cands, cols, y, sd, fold, FOLDS, workers, log)
    good = np.flatnonzero((sc[:, 0] > 0) & (sc[:, 1] >= MIN_FOLDS_POS) & (sc[:, 2] >= MIN_LEAF))
    log(f"  bramki kucia (wynik > 0 poza próbą, ≥ {MIN_FOLDS_POS}/{FOLDS} bloków, stan ≥ {MIN_LEAF} świec): {len(good):,}")
    order = good[np.argsort(-sc[good, 0], kind="stable")][:SHORTLIST]
    sub = np.arange(0, len(sample), 2)
    trees = [cands[c] for c in order]
    votes, keep = [], []
    for k, tree in enumerate(trees):
        table, _ = fit_table(tree, cols, y)
        side = np.where(table.mean(1) >= 0, 1, -1).astype(np.int8)
        leaf = np.zeros(len(sub), np.int32)
        for b, t in enumerate(tree):
            leaf += cols[t][sub].astype(np.int32) << b
        v = side[leaf]
        share = (v > 0).mean()
        if BUY_SHARE[0] <= share <= BUY_SHARE[1]:
            keep.append(k)
            votes.append(v)
    votes = np.array(votes, np.int8)
    fam = [primary_family(trees[k], tests) for k in keep]
    log(f"  po warunku „zmienia zdanie” (BUY {BUY_SHARE[0]:.0%}–{BUY_SHARE[1]:.0%}): {len(keep):,}")
    chosen, info = select_diverse(np.arange(len(keep)), votes, fam, n_investors, rho_cap, FAMILY_CAP, log)
    if len(chosen) < n_investors:
        log(f"  UWAGA: przy limicie korelacji {rho_cap} zmieściło się tylko {len(chosen)} inwestorów.")
    sel = [keep[c] for c in chosen]
    div = diversity(votes[chosen]) if len(chosen) > 1 else {}
    used = sorted({t for k in sel for t in trees[k]})
    remap = {t: j for j, t in enumerate(used)}
    investors = []
    for rank, k in enumerate(sel):
        tree = trees[k]
        table, nn = fit_table(tree, cols, y)
        c = order[k]
        investors.append(
            {
                "id": rank + 1,
                "tests": [remap[t] for t in tree],
                "table": np.round(table, 6).tolist(),
                "n": nn.astype(int).tolist(),
                "fam": primary_family(tree, tests),
                "families": sorted({tests[t]["fam"] for t in tree}),
                "rule": " · ".join(f"{tests[t]['label']} ≥ {tests[t]['e']:g}" for t in tree),
                "t_cv": round(float(sc[c, 0]), 3),
                "folds": int(sc[c, 1]),
                "min_leaf": int(nn.min()),
            }
        )
    fr = {
        "version": FOREST_VERSION,
        "engine_version": ENGINE_VERSION,
        "created": int(time.time()),
        "pairs": pn.pairs,
        "cuts": cuts,
        "tests": [tests[t] for t in used],
        "investors": investors,
        "forge": {
            "candidates": len(cands),
            "passed": int(len(good)),
            "sample": int(len(sample)),
            "tests_all": len(tests),
            "rho_cap": rho_cap,
            "seed": seed,
            "t_cv_top": [round(float(x), 3) for x in sc[order[:5], 0]],
            "t_cv_mean": float(np.mean([i["t_cv"] for i in investors])) if investors else 0.0,
            "t_cv_min": float(np.min([i["t_cv"] for i in investors])) if investors else 0.0,
            "minutes": round((time.time() - t_start) / 60, 1),
            **info,
            **div,
        },
    }
    fr["id"] = forest_id(fr)
    log(
        f"  las {fr['id']}: {len(investors)} inwestorów · N_eff {div.get('n_eff', 0):.1f} "
        f"· średnia |ρ| {div.get('srednia_abs_rho', 0):.3f} "
        f"· {fr['forge']['minutes']} min"
    )
    return fr
