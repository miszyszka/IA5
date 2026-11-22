"""Stocks (D-071) — badanie: turniej wszystkich konfiguracji rebalansowania na historii spółek, walidacja, werdykt, raport.

Odcinki (W1): od pierwszego tygodnia, w którym spółki z rokiem notowań mają ≥ 80% udziałów docelowych; IS = pierwsze 75%
tygodni, OOS = reszta. Zwycięzca = najwyższy IR (Sharpe tygodniowej nadwyżki nad stałym podziałem, po kosztach) na IS.
Testy potwierdzające poza danymi wyboru: losowe przesunięcia w paśmie (W3), bootstrap i koszt × 2 na OOS; DSR na IS z liczbą
wszystkich prób (W2); PBO (CSCV) na całości. Każde liczenie otwiera OOS — wpis w dzienniku ~/.ia5/oos_ledger.json.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np

from . import stk_method as sm
from .stk_config import (
    BOOT_BLOCK,
    CLEAN_STK_VERSION,
    COST,
    CSCV_BLOCKS,
    DATA_FROM,
    IS_FRACTION,
    RANDOM_HOLD,
    RANDOM_PATHS,
    START_WEIGHT,
    STK_VERSION,
    TZ,
    VERDICT,
)
from .stk_data import Panel
from .validate import deflated_sharpe

ROOT = Path(__file__).resolve().parent
LEDGER_NAME = "oos_ledger.json"


def code_hash() -> str:
    h = hashlib.sha256()
    for f in sorted(ROOT.glob("stk_*.py")):
        h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()[:16]


def normalize_config(cfg: dict | None) -> dict:
    """Konfiguracja ze strony (stocks/config): tickery z udziałami w %, kapitał USD, pasmo ±%."""
    from .stk_config import DEFAULT_BAND, DEFAULT_CAPITAL, DEFAULT_TICKERS

    cfg = cfg or {}
    rows = []
    for x in cfg.get("tickers") or [{"t": t, "w": 100 / len(DEFAULT_TICKERS)} for t in DEFAULT_TICKERS]:
        t = str((x.get("t") if isinstance(x, dict) else x) or "").strip().upper()
        w = float((x.get("w") if isinstance(x, dict) else 0) or 0)
        if t and t not in [r["t"] for r in rows] and w > 0:
            rows.append({"t": t, "w": w})
    cap = float(cfg.get("capital") or DEFAULT_CAPITAL)
    band = float(cfg.get("band") if cfg.get("band") is not None else DEFAULT_BAND)
    return {"tickers": rows, "capital": cap, "band": max(0.0, min(band, 50.0))}


def config_hash(cfg: dict) -> str:
    c = normalize_config(cfg)
    return hashlib.sha256(json.dumps(c, sort_keys=True).encode()).hexdigest()[:12]


def _ann(mean_log: float) -> float:
    return float((math.exp(mean_log * 52) - 1) * 100) if np.isfinite(mean_log) else float("nan")


def max_dd(r) -> float:
    v = np.exp(np.r_[0, np.cumsum(np.nan_to_num(np.asarray(r, float)))])
    return float((v / np.maximum.accumulate(v) - 1).min() * 100)


def block_ci(x, block: int = BOOT_BLOCK, n: int = 2000, seed: int = 11) -> dict:
    a = np.asarray(x, float)
    a = a[np.isfinite(a)]
    if len(a) < 2 * block:
        return {"low": float("nan"), "high": float("nan")}
    rng = np.random.default_rng(seed)
    k = int(math.ceil(len(a) / block))
    st = rng.integers(0, len(a) - block + 1, size=(n, k))
    idx = (st[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, : len(a)]
    m = a[idx].mean(axis=1)
    return {"low": _ann(float(np.percentile(m, 2.5))), "high": _ann(float(np.percentile(m, 97.5)))}


def pbo(ex: np.ndarray, blocks: int = CSCV_BLOCKS, chunk: int = 1500) -> dict:
    """PBO metodą CSCV na tygodniowych nadwyżkach (konfiguracje × tygodnie), liczone porcjami kombinacji."""
    K, T = ex.shape
    if K < 2 or T < blocks * 4:
        return {"pbo": float("nan"), "variants": int(K)}
    b = np.minimum((np.arange(T) * blocks) // T, blocks - 1)
    sums = np.zeros((K, blocks))
    for j in range(blocks):
        sums[:, j] = np.nansum(ex[:, b == j], axis=1)
    cnts = np.bincount(b, minlength=blocks).astype(float)
    combos = np.array(list(itertools.combinations(range(blocks), blocks // 2)))
    lam = []
    for a in range(0, len(combos), chunk):
        cc = combos[a:a + chunk]
        C = np.zeros((len(cc), blocks))
        C[np.arange(len(cc))[:, None], cc] = 1
        isp = (C @ sums.T) / (C @ cnts)[:, None]
        oop = ((1 - C) @ sums.T) / ((1 - C) @ cnts)[:, None]
        best = isp.argmax(axis=1)
        ob = oop[np.arange(len(cc)), best]
        rank = (oop < ob[:, None]).sum(axis=1) + 1
        w = rank / (K + 1)
        lam.append(np.log(w / (1 - w)))
    lam = np.concatenate(lam)
    return {"pbo": float((lam <= 0).mean()), "variants": int(K), "combinations": int(len(combos)), "blocks": blocks}


def verdict(v: dict) -> dict:
    def num(k):
        x = v.get(k)
        return float(x) if x is not None and np.isfinite(x) else None

    checks = [
        {"id": "oos_excess", "value": num("oos_excess"), "need": "> 0", "ok": (num("oos_excess") or -1) > 0},
        {"id": "random", "value": num("random_pct"), "need": f"≥ {VERDICT['random_pct']:g}",
         "ok": (num("random_pct") or 0) >= VERDICT["random_pct"]},
        {"id": "dsr", "value": num("dsr"), "need": f"≥ {VERDICT['dsr']:g}", "ok": (num("dsr") or 0) >= VERDICT["dsr"]},
        {"id": "pbo", "value": num("pbo"), "need": f"< {VERDICT['pbo']:g}", "ok": num("pbo") is not None and num("pbo") < VERDICT["pbo"]},
        {"id": "cost2", "value": num("cost2_excess"), "need": "> 0", "ok": (num("cost2_excess") or -1) > 0},
    ]
    passed = sum(c["ok"] for c in checks)
    red = (num("oos_excess") or -1) <= 0 or (num("random_pct") or 0) < VERDICT["red_random_pct"]
    color = "green" if passed == len(checks) else ("red" if red else "yellow")
    return {"color": color, "passed": passed, "of": len(checks), "checks": checks}


def _metrics(r: np.ndarray, f: np.ndarray, turn: np.ndarray) -> dict:
    ex = r - f
    return {"ir": sm.ir(ex), "sharpe": sm.ir(r), "cagr_pct": _ann(float(np.mean(r))) if len(r) else None,
            "excess_pct_yr": _ann(float(np.mean(ex))) if len(r) else None, "max_dd_pct": max_dd(r),
            "turnover_yr": float(np.sum(turn) / max(len(r), 1) * 52 * 100), "weeks": int(len(r))}


def _years(ts: np.ndarray, series: dict[str, np.ndarray]) -> list[dict]:
    from .stk_data import day_str

    yrs = day_str(ts).astype("U4")
    out = []
    for y in sorted(set(yrs)):
        m = yrs == y
        out.append({"year": int(y), **{k: float((math.exp(float(np.sum(v[m]))) - 1) * 100) for k, v in series.items()}})
    return out


def run_research(ready: dict, cfg: dict, now: int, paths: int = RANDOM_PATHS, log=print, rejected: dict | None = None) -> dict:
    t0 = time.time()
    cfg = normalize_config(cfg)
    want = [r["t"] for r in cfg["tickers"]]
    universe = [t for t in want if t in ready and len(ready[t])]
    missing = [t for t in want if t not in universe]
    if len(universe) < 2:
        raise ValueError("za mało spółek z danymi (potrzeba co najmniej 2)")
    wmap = {r["t"]: r["w"] for r in cfg["tickers"]}
    w_user = np.array([wmap[t] for t in universe], float)
    w_user = w_user / w_user.sum()
    band = cfg["band"] / 100.0
    log(f"Stocks: panel dzienny {len(universe)} spółek…")
    p = Panel(ready, universe)
    feat = sm.daily_features(p)
    W = sm.prepare(p, w_user, feat)
    start = sm.start_week(W, w_user, START_WEIGHT)
    end = len(W.sig) - 1
    weeks = end - start
    if weeks < 104:
        raise ValueError(f"za krótka wspólna historia ({weeks} tygodni, potrzeba ≥ 104)")
    is_n = int(math.floor(IS_FRACTION * weeks))
    K = len(sm.CONFIGS)
    log(f"Stocks: {K:,} konfiguracji × {weeks:,} tygodni (IS {is_n}, OOS {weeks - is_n})…")
    R, TV = sm.run_all(W, band, start, end)
    base = sm.run_baselines(W, start, end)
    fixed, hold = base["fixed"][0], base["hold"][0]
    EX = R - fixed[None, :]
    is_sl, oos_sl = slice(0, is_n), slice(is_n, weeks)
    is_ir = np.array([sm.ir(x) for x in EX[:, is_sl]])
    oos_ir = np.array([sm.ir(x) for x in EX[:, oos_sl]])
    is_ex = np.array([_ann(float(np.mean(x))) for x in EX[:, is_sl]])
    oos_ex = np.array([_ann(float(np.mean(x))) for x in EX[:, oos_sl]])
    wi = int(np.nanargmax(np.where(np.isfinite(is_ir), is_ir, -np.inf)))
    win = sm.CONFIGS[wi]
    log(f"Stocks: zwycięzca IS — {win.label} (IR IS {is_ir[wi]:.2f}, OOS {oos_ir[wi]:.2f})")
    # walidacja
    trial_sr = np.array([np.nanmean(x) / np.nanstd(x, ddof=1) if np.nanstd(x, ddof=1) > 0 else np.nan for x in EX[:, is_sl]])
    dsr = deflated_sharpe(EX[wi, is_sl], trial_sr)
    log(f"Stocks: {paths} losowych przesunięć w paśmie…")
    RR = sm.run_random(W, band, start, end, paths, RANDOM_HOLD)
    rand_oos = np.array([_ann(float(np.mean(x))) for x in (RR - fixed[None, :])[:, oos_sl]])
    rand_pct = float((rand_oos < oos_ex[wi]).mean() * 100)
    log("Stocks: PBO, bootstrap, koszt × 2…")
    pb = pbo(EX)
    boot = block_ci(EX[wi, oos_sl])
    r2, _ = sm.run_one(W, win, band, start, end, cost=2 * COST)
    f2 = sm.run_baselines(W, start, end, cost=2 * COST)["fixed"][0]
    cost2 = _ann(float(np.mean((r2 - f2)[oos_sl])))
    v = {"oos_excess": float(oos_ex[wi]), "random_pct": rand_pct, "dsr": dsr.get("dsr"), "pbo": pb.get("pbo"), "cost2_excess": cost2}
    ver = verdict(v)
    ts = p.ts[W.exe[start:end]]
    ts_end = p.ts[W.exe[end]]

    def curve(r):
        return [float(cfg["capital"])] + [float(x) for x in cfg["capital"] * np.exp(np.cumsum(r))]

    hist_ts = [int(x) for x in ts] + [int(ts_end)]
    order = np.argsort(-np.where(np.isfinite(is_ir), is_ir, -np.inf))
    top_idx = list(order[:25]) + ([wi] if wi not in order[:25] else [])

    def row(i):
        c = sm.CONFIGS[i]
        return {**c.as_dict(), "rank_is": int(np.flatnonzero(order == i)[0]) + 1,
                "is": _metrics(R[i, is_sl], fixed[is_sl], TV[i, is_sl]), "oos": _metrics(R[i, oos_sl], fixed[oos_sl], TV[i, oos_sl])}

    families = []
    for s in sm.SIGNAL_NAMES:
        ii = [c.i for c in sm.CONFIGS if c.signal == s]
        b = max(ii, key=lambda i: is_ir[i] if np.isfinite(is_ir[i]) else -9)
        families.append({"signal": s, "label": sm.signal_label(s), "best_id": sm.CONFIGS[b].id, "is_ir": float(is_ir[b]),
                         "oos_ir": float(oos_ir[b]), "oos_excess_pct_yr": float(oos_ex[b]),
                         "share_oos_positive": float(np.mean(oos_ex[ii] > 0) * 100)})
    first_days = {t: (max(str(ready[t]["day"].iloc[0]), DATA_FROM) if len(ready[t]) else None) for t in universe}
    res = {
        "stk_version": STK_VERSION, "clean_version": CLEAN_STK_VERSION, "code_hash": code_hash(), "computedAt": int(now),
        "config": cfg, "config_hash": config_hash(cfg), "universe": universe, "weights": {t: float(x) for t, x in zip(universe, w_user)},
        "missing": missing, "rejected": {k: v for k, v in (rejected or {}).items() if k in want}, "first_days": first_days, "tz": TZ,
        "cost": COST, "band": band, "data_from": DATA_FROM,
        "periods": {"start_ts": int(ts[0]), "is_end_ts": int(ts[is_n]), "oos_end_ts": int(ts_end), "weeks": int(weeks),
                    "is_weeks": int(is_n), "oos_weeks": int(weeks - is_n)},
        "trials": int(K), "winner": win.id,
        "winner_detail": row(wi),
        "baselines": {"fixed": {"is": _metrics(fixed[is_sl], fixed[is_sl], base["fixed"][1][is_sl]),
                                "oos": _metrics(fixed[oos_sl], fixed[oos_sl], base["fixed"][1][oos_sl])},
                      "hold": {"is": _metrics(hold[is_sl], fixed[is_sl], base["hold"][1][is_sl]),
                               "oos": _metrics(hold[oos_sl], fixed[oos_sl], base["hold"][1][oos_sl])}},
        "top": [row(i) for i in top_idx], "families": families,
        "distribution": {"oos_positive_pct": float(np.mean(oos_ex > 0) * 100), "oos_excess_median": float(np.nanmedian(oos_ex)),
                         "is_excess_median": float(np.nanmedian(is_ex))},
        "validation": {"dsr": dsr, "pbo": pb, "random_paths": int(paths), "random_pct": rand_pct,
                       "random_oos_median": float(np.median(rand_oos)), "boot": boot, "cost2_excess": cost2,
                       "selection": "ir_excess_fixed"},
        "verdict": ver,
        "history": {"ts": hist_ts, "winner": curve(R[wi]), "fixed": curve(fixed), "hold": curve(hold)},
        "years": _years(ts, {"winner": R[wi], "fixed": fixed, "hold": hold}),
        "frozen": {"id": win.id, "label": win.label, "code_hash": code_hash(), "stk_version": STK_VERSION, "at": int(now),
                   "config_hash": config_hash(cfg)},
        "seconds": round(time.time() - t0, 1),
    }
    return clean_json(res)


def clean_json(o):
    if isinstance(o, dict):
        return {str(k): clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean_json(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return clean_json(o.tolist())
    return o


def ledger_add(home: Path, res: dict, run_id: str) -> int:
    """Dziennik otwarć OOS (wspólny z poszukiwaniem i REV): każde badanie Stocks otwiera sprawdzian."""
    path = home / LEDGER_NAME
    try:
        led = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        led = {}
    entries = led if isinstance(led, list) else led.setdefault("entries", [])
    entries.append({"kind": "stocks", "run": run_id, "at": res["computedAt"], "config": res["config_hash"],
                    "trials": res["trials"], "winner": res["winner"]})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(led, ensure_ascii=False, indent=1), encoding="utf-8")
    return sum(1 for e in entries if isinstance(e, dict) and e.get("kind") == "stocks")


# ---------- raport dla Claude ----------

def _d(ts) -> str:
    from .stk_data import day_str

    return str(day_str([int(ts)])[0]) if ts else "—"


def _f(x, nd: int = 2, sign: bool = False) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "—"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


COLOR = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
CHECK_NAME = {"oos_excess": "Nadwyżka nad stałym podziałem na OOS (% rocznie)",
              "random": "Percentyl wobec losowych przesunięć (OOS)",
              "dsr": "Deflated Sharpe (IS, wszystkie próby)", "pbo": "PBO (CSCV, cała historia)",
              "cost2": "Nadwyżka OOS przy koszcie × 2 (% rocznie)"}


def report_md(res: dict) -> str:
    p, v, ver = res["periods"], res["validation"], res["verdict"]
    w = res["winner_detail"]
    L = [f"# Stocks — badanie metody rebalansowania (wersja {res['stk_version']})", "",
         f"Policzone {_d(res['computedAt'])} · {res['trials']:,} konfiguracji · "
         f"werdykt {COLOR[ver['color']]} {ver['passed']}/{ver['of']}", "",
         "## Dane i model", "",
         f"- Spółki ({len(res['universe'])}): " + ", ".join(f"{t} {res['weights'][t] * 100:.1f}%" for t in res["universe"]),
         f"- Pominięte (brak danych): {', '.join(res['missing']) or '—'}; odrzucone przez Apps Script: "
         + (", ".join(f"{k} ({x})" for k, x in res["rejected"].items()) or "—"),
         f"- Kapitał {res['config']['capital']:,.0f} USD · pasmo ±{res['band'] * 100:g}% udziału docelowego · "
         f"koszt {res['cost'] * 100:.2f}% od strony transakcji",
         f"- Świece dzienne Yahoo od {DATA_FROM} (ceny po splitach, dywidendy z dniem bez prawa), "
         f"czyszczenie wersja {res['clean_version']}",
         "- Ocena na zamknięciu dnia sesji przed wtorkiem, wykonanie na otwarciu wtorku (święto → następny dzień sesji); "
         "spółka gra po roku notowań",
         f"- Odcinki: {_d(p['start_ts'])} → IS do {_d(p['is_end_ts'])} ({p['is_weeks']} tyg.) → "
         f"OOS do {_d(p['oos_end_ts'])} ({p['oos_weeks']} tyg.)",
         "- Wybór: najwyższy IR tygodniowej nadwyżki nad stałym podziałem (co tydzień do celu), tylko na IS", "",
         "## Zwycięzca", "", f"**{w['label']}** (`{w['id']}`)", "",
         "| odcinek | CAGR % | nadwyżka % r. | IR nadwyżki | Sharpe | maks. spadek % | obrót % r. |", "|---|---|---|---|---|---|---|"]
    for k, name in (("is", "IS"), ("oos", "OOS")):
        m = w[k]
        L.append(f"| {name} | {_f(m['cagr_pct'], sign=True)} | {_f(m['excess_pct_yr'], sign=True)} | {_f(m['ir'])} | {_f(m['sharpe'])} | "
                 f"{_f(m['max_dd_pct'], 1)} | {_f(m['turnover_yr'], 0)} |")
    for b, name in (("fixed", "stały podział"), ("hold", "kup i trzymaj")):
        for k in ("is", "oos"):
            m = res["baselines"][b][k]
            L.append(f"| {name} {k.upper()} | {_f(m['cagr_pct'], sign=True)} | {_f(m['excess_pct_yr'], sign=True)} | — | "
                     f"{_f(m['sharpe'])} | "
                     f"{_f(m['max_dd_pct'], 1)} | {_f(m['turnover_yr'], 0)} |")
    L += ["", "## Walidacja", "", "| test | wynik | próg | |", "|---|---|---|---|"]
    for c in ver["checks"]:
        L.append(f"| {CHECK_NAME[c['id']]} | {_f(c['value'])} | {c['need']} | {'✓' if c['ok'] else '✗'} |")
    L += ["", f"Bootstrap nadwyżki OOS: {_f(v['boot']['low'])} … {_f(v['boot']['high'])}% rocznie. Mediana losowych przesunięć OOS: "
          f"{_f(v['random_oos_median'], sign=True)}%. Konfiguracji z dodatnią nadwyżką OOS: "
          f"{_f(res['distribution']['oos_positive_pct'], 0)}% "
          f"(mediana {_f(res['distribution']['oos_excess_median'], sign=True)}% r.).", "",
          "## Najlepsze w rodzinach ocen (wybór po IS)", "",
          "| ocena | IR IS | IR OOS | nadwyżka OOS % r. | konfiguracji z OOS > 0 |", "|---|---|---|---|---|"]
    for f in sorted(res["families"], key=lambda x: -(x["is_ir"] or -9)):
        L.append(f"| {f['label']} | {_f(f['is_ir'])} | {_f(f['oos_ir'])} | {_f(f['oos_excess_pct_yr'], sign=True)} | "
                 f"{_f(f['share_oos_positive'], 0)}% |")
    L += ["", "## Top 25 po IS", "", "| # | konfiguracja | IR IS | IR OOS | nadwyżka OOS % r. |", "|---|---|---|---|---|"]
    for r in res["top"]:
        L.append(f"| {r['rank_is']} | {r['label']} | {_f(r['is']['ir'])} | {_f(r['oos']['ir'])} | "
                 f"{_f(r['oos']['excess_pct_yr'], sign=True)} |")
    L += ["", "## Lata (wynik %)", "", "| rok | metoda | stały podział | kup i trzymaj |", "|---|---|---|---|"]
    for y in res["years"]:
        L.append(f"| {y['year']} | {_f(y['winner'], 1, True)} | {_f(y['fixed'], 1, True)} | {_f(y['hold'], 1, True)} |")
    L += ["", "## Znane ograniczenia", "",
          "- Dane tylko z Yahoo: brak spółek, które zniknęły z giełdy (lista dzisiejszych spółek = błąd przetrwania, "
          "zawyża wszystkie warianty po równo).",
          "- Backtest liczy udziały ciągłe; portfel na żywo — całe akcje (reszta w gotówce).",
          "- Bez podatków; koszt stały 0,10% strony. Dywidendy reinwestowane przy następnym rebalansie.",
          "- Każde ponowne liczenie (nowe udziały, nowe spółki) otwiera OOS jeszcze raz — liczba otwarć w dzienniku OOS."]
    return "\n".join(L) + "\n"
