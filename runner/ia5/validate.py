"""Walidacja (CLAUDE.md sekcja 9, W1–W3): czy wynik nie jest przypadkiem albo efektem przeszukania.

- benchmark losowych wejść: te same pary, ta sama liczba i kierunki transakcji, ta sama reguła wyjścia;
- Deflated Sharpe Ratio (Bailey, López de Prado 2014) — korekta za liczbę przetestowanych wariantów;
- PBO metodą CSCV (Bailey i in. 2015) — prawdopodobieństwo, że najlepszy wariant IS jest poniżej mediany OOS;
- walk-forward (okna kotwiczone), bootstrap przedziału ufności, test spreadu ×1,5 / ×2 / faktyczny.
Każda funkcja jest deterministyczna (stałe ziarno), żeby wynik dało się odtworzyć (D6).
"""
from __future__ import annotations

import itertools
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from .config import PAIRS
from .engine import Exit, simulate

N01 = NormalDist()
EULER = 0.5772156649
MIN_TRADES = 30


# ---------- benchmark losowych wejść (W3) ----------

def random_benchmark(preps: dict, trades: pd.DataFrame, ex: Exit, signals: dict | None = None,
                     sims: int = 1000, seed: int = 7, max_rows: int = 200_000) -> dict:
    """Rozkład średnich pipsów netto z losowych wejść; percentyl faktycznego wyniku w tym rozkładzie."""
    rng = np.random.default_rng(seed)
    actual = float(trades["pips_net"].mean())
    total = np.zeros(sims)
    count = np.zeros(sims)
    for pair, g in trades.groupby("pair"):
        P = preps[pair]
        n = len(P["o"])
        ok = np.flatnonzero(~np.isnan(P["atr14"][:-1]) & ~np.isnan(P["atr5"][:-1]))  # świeca sygnału
        if len(ok) == 0:
            continue
        k = len(g)
        dirs = g["dir"].to_numpy()
        spread = PAIRS[pair].spread_pips
        per_chunk = max(1, max_rows // k)
        for s0 in range(0, sims, per_chunk):
            s1 = min(sims, s0 + per_chunk)
            i = rng.choice(ok, size=(s1 - s0, k))
            d = rng.choice(dirs, size=(s1 - s0, k))
            i, d = i.ravel(), d.ravel()
            e = np.minimum(i + 1, n - 1)
            ent = pd.DataFrame({"entry_i": e, "dir": d.astype(np.int8), "entry_px": P["o"][e],
                                "atr5": P["atr5"][i], "atr14": P["atr14"][i]})
            opp = signals.get(pair) if signals else None
            res = simulate(P, ent, ex, pair, opp=opp)
            net = (res["pips_gross"] - spread).to_numpy().reshape(s1 - s0, k)
            valid = ~np.isnan(net)
            total[s0:s1] += np.where(valid, net, 0).sum(axis=1)
            count[s0:s1] += valid.sum(axis=1)
    means = np.where(count > 0, total / np.maximum(count, 1), np.nan)
    means = means[~np.isnan(means)]
    if len(means) == 0:
        return {"sims": 0}
    return {
        "sims": int(len(means)), "actual_mean_pips": actual,
        "percentile": float((means < actual).mean() * 100),
        "p5": float(np.percentile(means, 5)), "p50": float(np.percentile(means, 50)), "p95": float(np.percentile(means, 95)),
    }


# ---------- Deflated Sharpe Ratio (W2) ----------

def per_trade_sharpe(r: np.ndarray) -> float:
    r = r[~np.isnan(r)]
    return float(r.mean() / r.std(ddof=1)) if len(r) > 2 and r.std(ddof=1) > 0 else np.nan


def deflated_sharpe(best_r: np.ndarray, trial_sharpes: np.ndarray) -> dict:
    """DSR = P(prawdziwy Sharpe > 0) po korekcie za liczbę prób. Sharpe na transakcję (nie roczny)."""
    r = best_r[~np.isnan(best_r)]
    srs = trial_sharpes[~np.isnan(trial_sharpes)]
    T, N = len(r), len(srs)
    if T < 10 or N < 2:
        return {"dsr": np.nan, "trials": int(N)}
    sr = per_trade_sharpe(r)
    var = float(np.var(srs, ddof=1))
    sr0 = math.sqrt(var) * ((1 - EULER) * N01.inv_cdf(1 - 1 / N) + EULER * N01.inv_cdf(1 - 1 / (N * math.e)))
    z = (r - r.mean()) / r.std(ddof=0)
    skew = float((z**3).mean())
    kurt = float((z**4).mean())
    denom = 1 - skew * sr + (kurt - 1) / 4 * sr**2
    dsr = N01.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(denom)) if denom > 0 else np.nan
    return {"dsr": float(dsr), "sharpe": sr, "sharpe0": sr0, "trials": int(N), "trades": int(T),
            "skew": skew, "kurtosis": kurt}


# ---------- PBO metodą CSCV ----------

def pbo_cscv(outcomes: pd.DataFrame, entries_ts: pd.Series, blocks: int = 16) -> dict:
    """outcomes: variant_id, r_net, entry_ts. Wymaga ≥ MIN_TRADES transakcji w wariancie."""
    o = outcomes.assign(entry_ts=entries_ts.to_numpy()) if "entry_ts" not in outcomes else outcomes
    cnt = o.groupby("variant_id").size()
    keep = cnt[cnt >= MIN_TRADES].index
    o = o[o["variant_id"].isin(keep)]
    N = len(keep)
    if N < 2:
        return {"pbo": np.nan, "variants": int(N)}
    t0, t1 = o["entry_ts"].min(), o["entry_ts"].max() + 1
    b = np.clip(((o["entry_ts"] - t0) / (t1 - t0) * blocks).astype(int), 0, blocks - 1)
    vid = pd.Categorical(o["variant_id"], categories=keep).codes
    sums = np.zeros((N, blocks))
    cnts = np.zeros((N, blocks))
    np.add.at(sums, (vid, b.to_numpy()), o["r_net"].fillna(0).to_numpy())
    np.add.at(cnts, (vid, b.to_numpy()), 1)
    combos = np.array([c for c in itertools.combinations(range(blocks), blocks // 2)])
    C = np.zeros((len(combos), blocks))
    C[np.arange(len(combos))[:, None], combos] = 1
    is_perf = (C @ sums.T) / np.maximum(C @ cnts.T, 1)
    oos_perf = ((1 - C) @ sums.T) / np.maximum((1 - C) @ cnts.T, 1)
    best = is_perf.argmax(axis=1)
    oos_best = oos_perf[np.arange(len(C)), best]
    rank = (oos_perf < oos_best[:, None]).sum(axis=1) + 1  # 1 = najgorszy
    w = rank / (N + 1)
    lam = np.log(w / (1 - w))
    return {"pbo": float((lam <= 0).mean()), "variants": int(N), "combinations": int(len(C)), "blocks": blocks,
            "logit_median": float(np.median(lam))}


# ---------- walk-forward ----------

def walk_forward(outcomes: pd.DataFrame, windows: int = 5) -> dict:
    """Okna kotwiczone: wybór najlepszego wariantu na wszystkim przed oknem w, wynik w oknie w."""
    o = outcomes
    t0, t1 = o["entry_ts"].min(), o["entry_ts"].max() + 1
    edges = np.linspace(t0, t1, windows + 1)
    rows, picked = [], []
    for w in range(2, windows):
        train = o[o["entry_ts"] < edges[w]]
        test = o[(o["entry_ts"] >= edges[w]) & (o["entry_ts"] < edges[w + 1])]
        stats = train.groupby("variant_id")["r_net"].agg(["mean", "size"])
        stats = stats[stats["size"] >= MIN_TRADES]
        if stats.empty:
            continue
        vid = int(stats["mean"].idxmax())
        t = test[test["variant_id"] == vid]
        picked.append(t)
        rows.append({"from": int(edges[w]), "to": int(edges[w + 1]), "variant_id": vid,
                     "train_r": float(stats.loc[vid, "mean"]), "test_trades": int(len(t)),
                     "test_r": float(t["r_net"].mean()) if len(t) else np.nan,
                     "test_pips": float(t["pips_net"].mean()) if len(t) else np.nan})
    allt = pd.concat(picked) if picked else pd.DataFrame(columns=["r_net", "pips_net"])
    return {"windows": rows, "trades": int(len(allt)),
            "mean_r": float(allt["r_net"].mean()) if len(allt) else np.nan,
            "mean_pips": float(allt["pips_net"].mean()) if len(allt) else np.nan}


# ---------- bootstrap i spread ----------

def bootstrap_ci(x: np.ndarray, n: int = 2000, seed: int = 11) -> dict:
    x = x[~np.isnan(x)]
    if len(x) < 5:
        return {"low": np.nan, "high": np.nan, "n": int(len(x))}
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), (n, len(x)))].mean(axis=1)
    return {"low": float(np.percentile(means, 2.5)), "high": float(np.percentile(means, 97.5)), "n": int(len(x))}


def spread_stress(t: pd.DataFrame, real_spread_pips: np.ndarray | None = None) -> dict:
    sp = t["pair"].map({p: c.spread_pips for p, c in PAIRS.items()}).to_numpy(float)
    g = t["pips_gross"].to_numpy(float)
    out = {"x1": float((g - sp).mean()), "x1_5": float((g - 1.5 * sp).mean()), "x2": float((g - 2 * sp).mean())}
    if real_spread_pips is not None and not np.all(np.isnan(real_spread_pips)):
        out["real"] = float(np.nanmean(g - real_spread_pips))
    return out


# ---------- werdykt ----------

def verdict(v: dict) -> dict:
    """Progi z CLAUDE.md sekcja 9 (ustalone z góry)."""
    oos = v.get("oos_mean_pips")
    pct = v.get("benchmark", {}).get("percentile")
    pbo = v.get("pbo", {}).get("pbo")
    dsr = v.get("dsr", {}).get("dsr")
    s15 = v.get("spread", {}).get("x1_5")
    reasons = []

    def ok(x, cond, label):
        good = x is not None and not (isinstance(x, float) and np.isnan(x)) and cond(x)
        reasons.append({"test": label, "ok": bool(good), "value": None if x is None or (isinstance(x, float) and np.isnan(x)) else x})
        return good

    checks = [
        ok(oos, lambda x: x > 0, "expectancy netto OOS > 0"),
        ok(pct, lambda x: x >= 95, "percentyl benchmarku ≥ 95"),
        ok(pbo, lambda x: x < 0.3, "PBO < 0,3"),
        ok(dsr, lambda x: x >= 0.95, "DSR ≥ 0,95"),
        ok(s15, lambda x: x > 0, "dodatni przy spreadzie ×1,5"),
    ]
    if v.get("oos_trades", 0) < 10:
        color = "yellow"
        note = "za mało transakcji OOS do oceny"
    elif (oos is not None and oos <= 0) or (pct is not None and pct < 80):
        color, note = "red", "brak przewagi"
    elif all(checks):
        color, note = "green", "wszystkie testy zaliczone"
    else:
        color, note = "yellow", f"zaliczone {sum(checks)} z {len(checks)} testów"
    return {"color": color, "note": note, "checks": reasons}
