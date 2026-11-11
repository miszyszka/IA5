"""REV (D-063) — turniej 13 wariantów na historii kursów walut do PLN, walidacja, werdykt i raport dla Claude.

Odcinki (R5): IS = pierwsze 75% wtorków wspólnego okresu przy pierwszym badaniu, OOS = reszta do dnia badania; daty stałe
(`prior` = poprzedni research.json). Zwycięzca = najwyższy IR nadwyżki nad równym podziałem na IS. Testy potwierdzające
liczone poza danymi wyboru: losowe podziały, bootstrap i opóźnienie na OOS; DSR na IS (13 prób); PBO na całości.
Projekt: docs/superpowers/specs/2026-11-11-rev-design.md, §6.3.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import rev_method as rm
from .rev_config import (
    BASE,
    BLOCS,
    BOOT_BLOCK,
    CAP,
    CLEAN_PLN_VERSION,
    CSCV_BLOCKS,
    DECISION_TZ,
    IS_FRACTION,
    MIN_BASKETS,
    RANDOM_PATHS,
    REV_VERSION,
    START_PLN,
    VERDICT,
    baskets,
    members,
)
from .rev_data import daily_panel, decision_times, weekly_panel
from .validate import deflated_sharpe, pbo_cscv, per_trade_sharpe

LEDGER_NAME = "oos_ledger.json"
ROOT = Path(__file__).resolve().parent


# ---------- odcinki ----------

def periods(times: np.ndarray, elig: pd.DataFrame, prior: dict | None = None) -> dict:
    """Wspólny start: pierwszy wtorek z ≥ MIN_BASKETS koszykami (poza PLN) grającymi; IS = floor(75%) wtorków.
    `prior` → te same daty co w poprzednim badaniu (nowe tygodnie to już wynik na żywo, nie sprawdzian)."""
    times = np.asarray(times, dtype="int64")
    if prior:
        s, ie, oe = int(prior["start_ts"]), int(prior["is_end_ts"]), int(prior["oos_end_ts"])
        start = int(np.searchsorted(times, s))
        end = int(np.searchsorted(times, oe, side="right")) - 1
        is_end = int(np.searchsorted(times, ie, side="right")) - 1
    else:
        n = elig.drop(columns=[BASE], errors="ignore").sum(axis=1).to_numpy()
        ok = np.flatnonzero(n >= MIN_BASKETS)
        if not len(ok):
            raise ValueError(f"za mało koszyków z 5 latami historii (potrzeba {MIN_BASKETS} poza PLN)")
        start, end = int(ok[0]), len(times) - 1
        weeks = end - start + 1
        is_end = start + int(math.floor(IS_FRACTION * weeks)) - 1
        s, ie, oe = int(times[start]), int(times[is_end]), int(times[end])
    weeks = end - start + 1
    return {"start_ts": s, "is_end_ts": ie, "oos_end_ts": oe, "weeks": int(weeks), "is_weeks": int(is_end - start + 1),
            "oos_weeks": int(end - is_end), "rows": [int(start), int(is_end), int(end)]}


# ---------- miary ----------

def ir(x) -> float:
    return rm.ir(x)


def _ann_pct(mean_log: float) -> float:
    return float((math.exp(mean_log * 52) - 1) * 100) if np.isfinite(mean_log) else float("nan")


def windows52(ret: pd.Series, eq_ret: pd.Series) -> dict:
    """Udział okien 52-tygodniowych z wzrostem kapitału w PLN i z wynikiem lepszym od równego podziału."""
    r = np.asarray(ret, float)
    e = np.asarray(eq_ret, float)
    if len(r) < 52:
        return {"up": float("nan"), "beat": float("nan"), "n": 0}
    c = np.r_[0, np.cumsum(np.nan_to_num(r))]
    d = np.r_[0, np.cumsum(np.nan_to_num(r - e))]
    w = c[52:] - c[:-52]
    b = d[52:] - d[:-52]
    return {"up": float((w > 0).mean() * 100), "beat": float((b > 0).mean() * 100), "n": int(len(w))}


def max_dd_pct(log_ret) -> float:
    v = np.exp(np.r_[0, np.cumsum(np.nan_to_num(np.asarray(log_ret, float)))])
    return float((v / np.maximum.accumulate(v) - 1).min() * 100)


def block_bootstrap_ci(x, block: int = BOOT_BLOCK, n: int = 2000, seed: int = 11) -> dict:
    """Bootstrap blokowy 95% przedziału średniej (bloki po `block` tygodni — tygodnie nie są niezależne)."""
    a = np.asarray(x, float)
    a = a[np.isfinite(a)]
    if len(a) < 2 * block:
        return {"low": float("nan"), "high": float("nan"), "n": int(len(a))}
    rng = np.random.default_rng(seed)
    k = int(math.ceil(len(a) / block))
    starts = rng.integers(0, len(a) - block + 1, size=(n, k))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, : len(a)]
    means = a[idx].mean(axis=1)
    return {"low": float(np.percentile(means, 2.5)), "high": float(np.percentile(means, 97.5)), "n": int(len(a))}


def metrics(ret: pd.Series, eq_ret: pd.Series, lo: int, hi: int, idx: np.ndarray) -> dict:
    """Miary wariantu na wierszach decyzji [lo, hi] (ret[t] = zwrot od t do t+1)."""
    sel = (idx >= lo) & (idx <= hi)
    r = ret.to_numpy(float)[sel]
    e = eq_ret.to_numpy(float)[sel]
    ex = r - e
    w = windows52(r, e)
    return {"ir": ir(ex), "cagr_pct": _ann_pct(float(np.nanmean(r))) if len(r) else float("nan"),
            "excess_pct_yr": _ann_pct(float(np.nanmean(ex))) if len(r) else float("nan"),
            "up52": w["up"], "beat52": w["beat"], "max_dd_pct": max_dd_pct(r), "weeks": int(len(r))}


def verdict(v: dict) -> dict:
    """🟢 gdy wszystkie 5 warunków; 🔴 gdy nadwyżka OOS ≤ 0 albo percentyl losowych < 80; inaczej 🟡 (R5, sekcja 9)."""
    def num(k):
        x = v.get(k)
        return float(x) if x is not None and np.isfinite(float(x)) else float("nan")

    ex, rp, dsr, pbo, lag = num("oos_excess_pct"), num("random_pct"), num("dsr"), num("pbo"), num("lag_excess_pct")
    checks = [
        {"id": "oos_excess", "ok": bool(ex > 0), "value": ex, "need": "> 0"},
        {"id": "random", "ok": bool(rp >= VERDICT["random_pct"]), "value": rp, "need": f"≥ {VERDICT['random_pct']:g}"},
        {"id": "dsr", "ok": bool(dsr >= VERDICT["dsr"]), "value": dsr, "need": f"≥ {VERDICT['dsr']:g}"},
        {"id": "pbo", "ok": bool(pbo < VERDICT["pbo"]), "value": pbo, "need": f"< {VERDICT['pbo']:g}"},
        {"id": "lag", "ok": bool(lag > 0), "value": lag, "need": "> 0"},
    ]
    passed = sum(c["ok"] for c in checks)
    red = not (ex > 0) or not (rp >= VERDICT["red_random_pct"])
    color = "red" if red else ("green" if passed == len(checks) else "yellow")
    return {"color": color, "passed": int(passed), "of": len(checks), "checks": checks}


# ---------- benchmark losowych podziałów ----------

def random_benchmark(exe: pd.DataFrame, elig: pd.DataFrame, start: int, is_end: int, end: int, eq_ret: pd.Series,
                     n: int = RANDOM_PATHS, seed: int = 7) -> np.ndarray:
    """n ścieżek: co tydzień wagi z rozkładu Dirichleta(1) po grających koszykach, z limitem i pasmem (jak metoda).
    Wynik: suma tygodniowej nadwyżki nad równym podziałem na OOS (wiersze is_end < t < end) dla każdej ścieżki."""
    rng = np.random.default_rng(seed)
    P = exe.to_numpy(float)
    last = pd.DataFrame(P).ffill().to_numpy()
    px_all = np.where(np.isfinite(last), last, 0.0)
    E = elig.to_numpy(bool)
    N = P.shape[1]
    pln = list(exe.columns).index(BASE)
    er = eq_ret.reindex(exe.index).to_numpy(float)
    out = np.zeros(n)
    for k in range(n):
        units = np.zeros(N)
        units[pln] = START_PLN
        acc = 0.0
        for t in range(start, end):
            px = px_all[t]
            V = float(units @ px)
            cur = units * px / V
            frozen = ~np.isfinite(P[t])
            play = E[t] & ~frozen
            tgt = np.zeros(N)
            tgt[play] = rng.dirichlet(np.ones(int(play.sum())))
            order = rng.permutation(N)
            tgt = rm.cap_fill(tgt, order, CAP)
            new = rm.rebalance(cur, tgt, order, frozen)
            live = ~frozen & (px > 0)
            units[live] = new[live] * V / px[live]
            if t > is_end:
                V1 = float(units @ px_all[t + 1])
                acc += math.log(V1 / V) - (er[t] if np.isfinite(er[t]) else 0.0)
        out[k] = acc
    return out


# ---------- turniej ----------

def code_hash() -> str:
    h = hashlib.sha256(f"{REV_VERSION}:{CLEAN_PLN_VERSION}".encode())
    for name in ("rev_config.py", "rev_data.py", "rev_method.py", "rev_research.py", "rev_live.py"):
        h.update((ROOT / name).read_bytes())
    return h.hexdigest()[:16]


def _decision_frame(ready: dict[str, pd.DataFrame], universe: list[str], now: int,
                    prior: dict | None) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    have = [ready[c] for c in universe if c != BASE and ready.get(c) is not None and len(ready[c])]
    if not have:
        raise ValueError("brak kursów PLN do liczenia")
    first = int(min(int(f["close_ts"].iloc[0]) for f in have))
    last_cts = int(max(int(f["close_ts"].iloc[-1]) for f in have))
    times = decision_times(first, min(now, last_cts + 12 * 3600))
    if prior:
        times = times[times <= int(prior["periods"]["oos_end_ts"])]
    prices, _ = weekly_panel(ready, universe, times)
    lagged, _ = weekly_panel(ready, universe, times, exec_lag_days=1)
    return times, prices, lagged


def run_research(ready: dict[str, pd.DataFrame], admitted: list[str], prior: dict | None, now: int,
                 paths: int = RANDOM_PATHS, seed: int = 7, log=print, rejected: dict | None = None) -> dict:
    """Turniej: 12 wariantów statycznych + przełącznik na tych samych wtorkach, walidacja zwycięzcy, werdykt."""
    t0 = time.time()
    universe = list(prior["universe"]) if prior else baskets(admitted)
    times, prices, lagged = _decision_frame(ready, universe, now, prior)
    elig = rm.eligible(prices)
    per = periods(times, elig, prior.get("periods") if prior else None)
    start, is_end, end = per["rows"]
    log(f"  REV: {len(universe)} koszyków, wtorki {len(times)}, wspólny okres od wiersza {start} "
        f"(IS {per['is_weeks']} tyg., OOS {per['oos_weeks']} tyg.)")
    idx = np.arange(len(times))
    eqt = rm.equal_targets(elig)
    eq = rm.simulate(prices, eqt, None, band=0.0, start=start, end=end + 1)
    eq_ret = eq.ret.reindex(prices.index)

    sims, targets, orders = {}, {}, {}
    for v in rm.STATIC:
        tg, od = rm.variant_targets(prices, elig, v)
        targets[v.id], orders[v.id] = tg, od
        sims[v.id] = rm.simulate(prices, tg, od, start=start, end=end + 1)
    excess = pd.DataFrame({k: s.ret.reindex(prices.index) - eq_ret for k, s in sims.items()})
    tg_sw, chosen, od_sw = rm.switcher_targets(excess, targets, eqt, start, orders)
    targets["SW"], orders["SW"] = tg_sw, od_sw
    sims["SW"] = rm.simulate(prices, tg_sw, od_sw, start=start, end=end + 1)
    log(f"  REV: 13 wariantów policzone ({time.time() - t0:.0f} s)")

    variants = []
    for v in rm.VARIANTS:
        r = sims[v.id].ret.reindex(prices.index)
        variants.append({"id": v.id, "label": v.label, "is": metrics(r, eq_ret, start, is_end, idx),
                         "oos": metrics(r, eq_ret, is_end + 1, end - 1, idx)})
    is_ir = np.array([x["is"]["ir"] for x in variants], float)
    winner = variants[int(np.nanargmax(np.where(np.isfinite(is_ir), is_ir, -np.inf)))]["id"]
    win = sims[winner]
    wret = win.ret.reindex(prices.index)
    wex = (wret - eq_ret).to_numpy(float)
    is_sel = (idx >= start) & (idx <= is_end)
    oos_sel = (idx > is_end) & (idx <= end - 1)

    log(f"  REV: zwycięzca na IS: {winner}; losowe podziały ({paths} ścieżek)…")
    rand = random_benchmark(prices, elig, start, is_end, end, eq_ret, n=paths, seed=seed)
    w_oos = float(np.nansum(wex[oos_sel]))
    random_pct = float(((rand < w_oos).mean() + 0.5 * (rand == w_oos).mean()) * 100) if len(rand) else float("nan")
    trial = np.array([per_trade_sharpe((sims[v.id].ret.reindex(prices.index) - eq_ret).to_numpy(float)[is_sel])
                      for v in rm.VARIANTS])
    dsr = deflated_sharpe(wex[is_sel], trial)
    rows = []
    for v in rm.VARIANTS:
        e = (sims[v.id].ret.reindex(prices.index) - eq_ret).to_numpy(float)
        sel = (idx >= start) & (idx < end) & np.isfinite(e)
        rows.append(pd.DataFrame({"variant_id": v.id, "r_net": e[sel], "entry_ts": times[sel]}))
    pbo = pbo_cscv(pd.concat(rows, ignore_index=True), pd.concat(rows, ignore_index=True)["entry_ts"], CSCV_BLOCKS)
    boot = block_bootstrap_ci(wex[oos_sel])
    boot_pct = {"low": _ann_pct(boot["low"]), "high": _ann_pct(boot["high"]), "n": boot["n"]}
    lag_eq = rm.simulate(lagged, eqt, None, band=0.0, start=start, end=end + 1).ret.reindex(prices.index)
    lag_w = rm.simulate(lagged, targets[winner], orders[winner], start=start, end=end + 1).ret.reindex(prices.index)
    lag_ex = (lag_w - lag_eq).to_numpy(float)[oos_sel]
    daily = daily_panel(ready, universe, from_ts=int(times[start]), to_ts=int(times[end]))
    dd_w = rm.daily_equity(win.units, daily)
    dd_e = rm.daily_equity(eq.units, daily)

    def ddd(s: pd.Series) -> float:
        return float((s / s.cummax() - 1).min() * 100) if len(s) else float("nan")

    validation = {
        "oos_excess_pct": _ann_pct(float(np.nanmean(wex[oos_sel]))) if oos_sel.any() else float("nan"),
        "random_pct": random_pct, "random_paths": int(paths),
        "random_oos_excess_pct": {"p5": _ann_pct(float(np.percentile(rand, 5)) / max(oos_sel.sum(), 1)),
                                  "p50": _ann_pct(float(np.percentile(rand, 50)) / max(oos_sel.sum(), 1)),
                                  "p95": _ann_pct(float(np.percentile(rand, 95)) / max(oos_sel.sum(), 1))},
        "dsr": dsr, "pbo": pbo, "boot": boot_pct,
        "lag_excess_pct": _ann_pct(float(np.nanmean(lag_ex))) if len(lag_ex) else float("nan"),
        "max_dd_daily_pct": {"winner": ddd(dd_w), "equal": ddd(dd_e)},
        "trades_per_year": float(win.trades / max(per["weeks"] / 52, 1e-9)),
    }
    ver = verdict({"oos_excess_pct": validation["oos_excess_pct"], "random_pct": random_pct, "dsr": dsr.get("dsr"),
                   "pbo": pbo.get("pbo"), "lag_excess_pct": validation["lag_excess_pct"]})

    hist_rows = slice(start, end + 1)
    yrs = pd.to_datetime(times[hist_rows], unit="s", utc=True).tz_convert(DECISION_TZ).year
    yr_df = pd.DataFrame({"y": yrs, "w": wret.to_numpy(float)[hist_rows], "e": eq_ret.to_numpy(float)[hist_rows]})
    years = [{"year": int(y), "winner_pct": float((math.exp(np.nansum(g.w)) - 1) * 100),
              "equal_pct": float((math.exp(np.nansum(g.e)) - 1) * 100)} for y, g in yr_df.groupby("y")]
    W = win.weights.iloc[: end - start + 1]
    logp = np.log(prices.to_numpy(float))
    rr = np.nan_to_num(logp[1:] - logp[:-1])
    contrib = {c: float((W[c].to_numpy()[:-1] * rr[start:end, j]).sum() * 100) for j, c in enumerate(universe)}

    res = {
        "rev_version": REV_VERSION, "clean_version": CLEAN_PLN_VERSION, "computedAt": int(now),
        "universe": universe, "admitted": sorted(admitted),
        "blocs": {a: members(a, admitted) for a in BLOCS if a in admitted},
        "rejected": dict(rejected or {}), "periods": {k: v for k, v in per.items() if k != "rows"},
        "variants": variants, "winner": winner,
        "frozen": {"id": winner, "label": rm.VARIANT_BY_ID[winner].label, "code_hash": code_hash(),
                   "rev_version": REV_VERSION, "at": int(now)},
        "validation": validation, "verdict": ver,
        "history": {"ts": [int(t) for t in times[hist_rows]], "winner": [float(x) for x in win.value.to_numpy()],
                    "equal": [float(x) for x in eq.value.to_numpy()], "is_end_ts": per["is_end_ts"]},
        "switcher": [str(x) for x in chosen.to_numpy()[hist_rows]] if winner == "SW" else None,
        "years": years,
        "avg_weights": {c: float(W[c].mean()) for c in universe},
        "contrib_pct": contrib,
        "seconds": round(time.time() - t0, 1),
    }
    log(f"  REV: werdykt {ver['color']} {ver['passed']}/5 ({res['seconds']} s)")
    return clean_json(res)


def clean_json(o):
    """Do JSON bez NaN i typów numpy (NaN → None)."""
    if isinstance(o, dict):
        return {str(k): clean_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean_json(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        return f if math.isfinite(f) else None
    if isinstance(o, np.bool_):
        return bool(o)
    return o


# ---------- dziennik OOS i raport ----------

def ledger_add(home: Path, res: dict, run_id: str | None = None) -> int:
    """Dopisuje otwarcie OOS REV do ~/.ia5/oos_ledger.json; zwraca liczbę otwarć REV (R5: tylko przy nowej REV_VERSION)."""
    f = home / LEDGER_NAME
    try:
        rows = json.loads(f.read_text())
    except (FileNotFoundError, ValueError):
        rows = []
    p = res["periods"]
    rows.append({"run": run_id or time.strftime("%Y%m%d-%H%M%S"), "at": int(time.time()), "kind": "rev",
                 "rev_version": res.get("rev_version"), "oos_from": p["is_end_ts"], "oos_to": p["oos_end_ts"],
                 "variants": len(res.get("variants", []))})
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, indent=1))
    return sum(1 for r in rows if r.get("kind") == "rev")


def _d(ts) -> str:
    return pd.Timestamp(int(ts), unit="s", tz="UTC").tz_convert(DECISION_TZ).strftime("%Y-%m-%d") if ts else "—"


def _f(x, nd: int = 2, sign: bool = False) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


COLOR = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
CHECK_NAME = {"oos_excess": "Nadwyżka nad równym podziałem na OOS (% rocznie)",
              "random": "Percentyl wobec losowych podziałów (OOS)", "dsr": "DSR (IS, 13 prób)", "pbo": "PBO (CSCV, całość)",
              "lag": "Nadwyżka przy wymianie dzień później (OOS, % rocznie)"}


def report_md(res: dict) -> str:
    """Raport dla Claude (jak 10.6): liczby w tabelach markdown."""
    p, v, ver = res["periods"], res["validation"], res["verdict"]
    L = [f"# REV — badanie metody (REV_VERSION {res['rev_version']}, czyszczenie {res['clean_version']})", "",
         "## Hipoteza i metoda", "",
         "Kapitał w złotówkach rozkładany co wtorek 08:00 (cena: zamknięcie poniedziałku) na koszyki walut proporcjonalnie "
         "do oceny przeceny lub trendu, limit 50% na koszyk (waluta, blok o sztywnym kursie, PLN), pasmo 2 p.p., bez kosztów. "
         "Ceny względem łańcuchowego koszyka wszystkich koszyków (PLN też jest oceniany). Przecena = odchylenie od własnego "
         "trendu liniowego z 3/5 lat (ochrona przed pułapką inflacji), trend = zmiana z 3 mies. albo z roku bez ostatniego "
         "miesiąca; kombinacje = ½·z(przecena) + ½·z(trend 3 mies.). Zwycięzca wybrany tylko na IS (IR nadwyżki).", "",
         "## Dane", "",
         f"- Koszyki ({len(res['universe'])}): {', '.join(res['universe'])}",
         "- Bloki: " + ("; ".join(f"{a} (+{', '.join(m)})" for a, m in res["blocs"].items() if m) or "brak"),
         "- Odrzucone przy przyjęciu: " + (", ".join(f"{k} ({x})" for k, x in res["rejected"].items()) or "brak"),
         "- Źródło: Yahoo `{WALUTA}PLN=X`, D1; warstwa czyszczenia tylko zamknięć (wyskoki, przeskalowania, powtórzenia).", "",
         "## Odcinki", "",
         "| Odcinek | Od | Do | Tygodnie |", "|---|---|---|---|",
         f"| IS | {_d(p['start_ts'])} | {_d(p['is_end_ts'])} | {p['is_weeks']} |",
         f"| OOS | po {_d(p['is_end_ts'])} | {_d(p['oos_end_ts'])} | {p['oos_weeks']} |",
         f"| Na żywo | po {_d(p['oos_end_ts'])} | — | — |", "",
         f"Otwarcia OOS REV: {res.get('oos_openings', 1)}.", "",
         "## Warianty (13)", "",
         "| Wariant | IR IS | Nadwyżka IS % r. | CAGR IS % | IR OOS | Nadwyżka OOS % r. | CAGR OOS % | Wzrost 52 tyg. OOS % | "
         "Lepszy od równego OOS % | Maks. spadek OOS % |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for x in res["variants"]:
        mark = " **(zwycięzca)**" if x["id"] == res["winner"] else ""
        i, o = x["is"], x["oos"]
        L.append(f"| {x['id']} {x['label']}{mark} | {_f(i['ir'])} | {_f(i['excess_pct_yr'], sign=True)} | "
                 f"{_f(i['cagr_pct'], sign=True)} | {_f(o['ir'])} | {_f(o['excess_pct_yr'], sign=True)} | "
                 f"{_f(o['cagr_pct'], sign=True)} | {_f(o['up52'], 0)} | {_f(o['beat52'], 0)} | {_f(o['max_dd_pct'], 1)} |")
    L += ["", "## Walidacja", "", "| Test | Wynik | Próg | ✓ |", "|---|---|---|---|"]
    for c in ver["checks"]:
        L.append(f"| {CHECK_NAME[c['id']]} | {_f(c['value'])} | {c['need']} | {'✓' if c['ok'] else '✗'} |")
    rp = v.get("random_oos_excess_pct") or {}
    L += ["", f"- Losowe podziały: {v['random_paths']} ścieżek, nadwyżka OOS % r. p5 / p50 / p95: "
              f"{_f(rp.get('p5'), sign=True)} / {_f(rp.get('p50'), sign=True)} / {_f(rp.get('p95'), sign=True)}.",
          f"- Bootstrap blokowy (8 tyg.) 95% nadwyżki OOS % r.: {_f(v['boot']['low'], sign=True)} … "
          f"{_f(v['boot']['high'], sign=True)} ({v['boot']['n']} tyg.).",
          f"- Maks. spadek z wyceny dziennej (cały okres): zwycięzca {_f(v['max_dd_daily_pct']['winner'], 1)}%, "
          f"równy podział {_f(v['max_dd_daily_pct']['equal'], 1)}%.",
          f"- Zmian koszyka rocznie (zwycięzca): {_f(v['trades_per_year'], 0)}.", "",
          "## Werdykt", "", f"{COLOR[ver['color']]} {ver['passed']}/{ver['of']} — zwycięzca: {res['winner']} "
          f"({res['frozen']['label']}), zamrożony {_d(res['frozen']['at'])}, hash kodu `{res['frozen']['code_hash']}`.", ""]
    if ver["color"] == "red":
        L += ["Metoda nie pokonała równego podziału na sprawdzianie — na żywo działa i tak (R6), obok równy podział.", ""]
    L += ["## Lata", "", "| Rok | Zwycięzca % | Równy podział % |", "|---|---|---|"]
    L += [f"| {y['year']} | {_f(y['winner_pct'], 1, True)} | {_f(y['equal_pct'], 1, True)} |" for y in res["years"]]
    L += ["", "## Średnie udziały i wkład koszyków (zwycięzca, cały okres)", "", "| Koszyk | Średni udział % | Wkład p.p. (log) |",
          "|---|---|---|"]
    for c in sorted(res["universe"], key=lambda c: -(res["avg_weights"].get(c) or 0)):
        L.append(f"| {c} | {_f(100 * (res['avg_weights'].get(c) or 0), 1)} | {_f(res['contrib_pct'].get(c), 1, True)} |")
    L += ["", "## Ograniczenia", "",
          "- Wymiana po zamknięciu poniedziałku, a Michał wymienia we wtorek ok. 08:00 — test opóźnienia o dzień wyżej.",
          "- Bez odsetek od sald, spreadów i opłat (R3) — waluty z wysoką stopą wyglądają gorzej niż na lokacie.",
          "- Jedno źródło: Yahoo; rzadsze kursy mają gorszą historię; ok. 20 koszyków i kilkanaście lat to mała próba.",
          "- Bloki o sztywnym kursie traktowane jak kotwica — pęknięcie kursu wykrywa kontrola zdrowia, nie badanie.", "",
          "## Pytania do recenzenta", "",
          "1. Czy przewaga zwycięzcy na IS ma sensowną przyczynę ekonomiczną, czy to szczęście wśród 13 prób?",
          "2. Czy wynik nie stoi na jednej walucie lub jednym roku (tabele lat i wkładu)?",
          "3. Czy wynik przetrwa wymianę dzień później i inne pasmo?", ""]
    return "\n".join(L)
