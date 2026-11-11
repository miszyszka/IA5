"""Wirtualni inwestorzy — paper trading na żywych świecach Yahoo (E6, D-045).

Inwestor (Firestore `investors/{id}`, tworzy go dashboard — tylko właściciel, S1):
  name, capital (USD), pct (% kapitału jako depozyt na każde wejście), createdAt (= start), createdBy, status,
  strategies: [{strategyId, name, code, variantId, variantLabel}]  — kod i wariant zapisane w chwili dodania.
Ustawień nie da się zmienić (decyzja Michała) — tylko usunąć inwestora.

Zasady liczenia (te same co silnik — B1–B12, B4, 8.5 — bez osobnego modelu wykonania):
  * liczą się tylko sygnały ze świec zamkniętych PO dodaniu inwestora (signal_ts + 1 h > start) — prawdziwy
    forward, bez historii; wejście na open następnej świecy (B1), okno godzin i dokładanie według strategii;
  * wyjście według wybranego wariantu; pozycja bez wyjścia w danych jest OTWARTA i wyceniana po zamknięciu
    ostatniej świecy (wycena, nie zysk zrealizowany);
  * transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną — anulowana (B12), widoczna na liście;
  * wszystkie strategie inwestora dzielą jeden kapitał: depozyt = pct% bieżącego kapitału × waga sygnału,
    suma depozytów otwartych pozycji ≤ 100% kapitału (B4) — sygnał bez wolnego depozytu pominięty i pokazany;
  * zysk = nominał (30 × depozyt) × zwrot w walucie kwotowanej (jak portfolio.py — przybliżenie dla par bez USD).
Każde liczenie zaczyna od zera na aktualnych danych, więc wynik jest powtarzalny (te same świece → ten sam stan).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from .backtest import exits_from
from .config import LEVERAGE, PAIRS
from .engine import data_cancel, find_entries, no_overlap, prepare, simulate
from .sandbox import StrategyError, run_probe, run_strategy_code
from .session import in_trading_hours

H = 3600
PROBE_MOVES = [0.0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0]   # D-051: hipotetyczne zamknięcie, w ATR14 od ostatniej ceny
OPEN_EXIT = 1e15   # pozycja otwarta zajmuje miejsce w parze do końca danych (B8 / PYRAMID)


def paper_trades(P: dict, sig: np.ndarray, ex, pair: str, start: int, hours=None, pyramid: int = 1,
                 lv: np.ndarray | None = None) -> pd.DataFrame:
    """Transakcje jednej pary od chwili `start`: zamknięte, otwarte (wycena) i anulowane (B12).
    lv (D-057): poziomy TP/SL ze strategii na świecy sygnału (wyjścia rodzaju „level”)."""
    ent = find_entries(P, sig, lv)
    ent = ent[ent["signal_ts"].to_numpy() + H > start]          # sygnał ze świecy zamkniętej po dodaniu inwestora
    ent = ent[~(ent["atr14"].isna() | ent["atr5"].isna()).to_numpy()]
    ent = ent[in_trading_hours(ent["entry_ts"].to_numpy(), hours)].reset_index(drop=True)
    if ent.empty:
        return pd.DataFrame()
    res = simulate(P, ent, ex, pair, opp=np.asarray(sig))
    xi = res["exit_i"].to_numpy(float)
    is_open = np.isnan(xi)
    last = len(P["ts"]) - 1
    gap, fill = data_cancel(P, ent["signal_i"].to_numpy(), ent["entry_i"].to_numpy(), np.where(is_open, last, xi), split=True)
    cancel = gap | (fill & ~is_open)
    xi_eff = np.where(is_open, OPEN_EXIT, xi)
    xi_eff[cancel] = np.nan
    keep = no_overlap(ent["entry_i"].to_numpy(), xi_eff, ent["dir"].to_numpy(), pyramid)
    show = keep | cancel
    out = pd.concat([ent.reset_index(drop=True), res.reset_index(drop=True)], axis=1)[show].copy()
    is_open, cancel, gap = is_open[show], cancel[show], gap[show]
    c = PAIRS[pair]
    px_last = float(P["c"][last])
    mark = (px_last - out["entry_px"].to_numpy()) * out["dir"].to_numpy() / c.pip
    out["pips_gross"] = np.where(is_open, mark, out["pips_gross"].to_numpy(float))
    out["exit_px"] = np.where(is_open, px_last, out["exit_px"].to_numpy(float))
    out["exit_ts"] = np.where(is_open, np.nan, out["exit_ts"].to_numpy(float))
    out["bars"] = np.where(is_open, last - out["entry_i"].to_numpy() + 1, out["bars"].to_numpy(float))
    out["pips_net"] = out["pips_gross"] - c.spread_pips          # B3: spread jednorazowo, także przy wycenie
    out["status"] = np.where(cancel, np.where(gap, "anulowana: przerwa w danych", "anulowana: świeca uzupełniona"),
                             np.where(is_open, "otwarta", "zamknięta"))
    out.loc[is_open, "reason"] = "wycena"
    out["pair"] = pair
    out["mark_ts"] = int(P["ts"][last]) + H
    return out


def exit_levels(ex, entry, d, atr14, atr5, tp_px=None, sl_px=None) -> tuple:
    """Poziomy TP/SL wariantu — te same wzory co engine.simulate. None = brak poziomu (stop kroczący: SL = początkowy).
    Wyjście „level” (D-057): poziomy w cenie ze strategii (tp_px, sl_px), NaN = brak."""
    if ex.kind == "level":
        f = lambda x: None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)  # noqa: E731
        return f(tp_px), f(sl_px)
    atr = atr5 if ex.n == 5 and ex.kind in ("atr", "rsi_streak", "trail") else atr14
    tp = entry + d * ex.tp * atr if ex.kind == "atr" or (ex.kind in ("rsi_streak", "trail") and ex.tp > 0) else None
    sl = entry - d * ex.sl * atr if ex.sl > 0 else None
    return tp, sl


def upcoming_signals(code: str, h1_dir: Path, pid: int, strategy: int, target: int, hours, busy: set) -> list[dict]:
    """D-051: na którym instrumencie sygnał jest osiągalny przy zamknięciu trwającej świecy (o `target`) i przy jakiej cenie."""
    if not bool(in_trading_hours(np.array([target]), hours)[0]):
        return []
    best: dict = {}
    for x in run_probe(code, h1_dir, pid, PROBE_MOVES):
        if x["pair"] in busy:
            continue
        key = (x["pair"], x["dir"])
        if key not in best or abs(x["k"]) < abs(best[key]["k"]):
            best[key] = x
    return [{"strategy": strategy, "pair": p, "dir": d, "target_ts": target, "move_atr": x["k"], "level": x["level"]}
            for (p, d), x in sorted(best.items())]


def pending_signals(P: dict, sig: np.ndarray, start: int, hours=None) -> list[dict]:
    """Sygnał na ostatniej zamkniętej świecy — wejście dopiero na open następnej (jeszcze jej nie ma)."""
    last = len(P["ts"]) - 1
    v = float(np.nan_to_num(np.asarray(sig, float))[last]) if last >= 0 else 0.0
    ts = int(P["ts"][last])
    if not v or ts + H <= start or not bool(in_trading_hours(np.array([ts + H]), hours)[0]):
        return []
    return [{"signal_ts": ts, "dir": int(np.sign(v)), "weight": abs(v)}]


def book(trades: pd.DataFrame, capital: float, pct: float, leverage: float = LEVERAGE) -> dict:
    """Wspólny kapitał inwestora (B4, 8.5): depozyt przy wejściu, suma depozytów ≤ kapitał, zysk przy wyjściu.
    Zwraca transakcje z kwotami, krzywą kapitału i stan teraz (zrealizowany + wycena otwartych)."""
    t = trades.reset_index(drop=True).copy()
    for col in ("margin_usd", "nominal_usd", "pnl_usd", "equity_after"):
        t[col] = np.nan
    if t.empty:
        return {"trades": t, "curve": {"ts": [], "equity": []}, "realized": capital, "unrealized": 0.0,
                "margin_used": 0.0, "skipped_margin": 0}
    pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
    ret = t["pips_net"].to_numpy(float) * pip / t["entry_px"].to_numpy(float)
    wts = t["weight"].to_numpy(float) if "weight" in t else np.ones(len(t))
    live = t["status"].isin(["zamknięta", "otwarta"]).to_numpy()
    ev = []
    for k in np.flatnonzero(live):
        ev.append((int(t.at[k, "entry_ts"]), 1, k))
        if t.at[k, "status"] == "zamknięta":
            ev.append((int(t.at[k, "exit_ts"]), 0, k))
    ev.sort()
    eq, used, held = capital, 0.0, {}
    curve_ts, curve_eq = [], []
    skipped = 0
    for ts, kind, k in ev:
        if kind == 1:
            m = eq * pct / 100 * wts[k]
            if eq <= 0 or used + m > eq + 1e-9:
                t.at[k, "status"] = "pominięta: brak wolnego depozytu"
                skipped += 1
                continue
            held[k] = m
            used += m
            t.at[k, "margin_usd"] = m
            t.at[k, "nominal_usd"] = m * leverage
        elif k in held:
            m = held.pop(k)
            used -= m
            pnl = m * leverage * ret[k]
            eq += pnl
            t.at[k, "pnl_usd"] = pnl
            t.at[k, "equity_after"] = eq
            curve_ts.append(ts)
            curve_eq.append(eq)
    unreal = 0.0
    for k, m in held.items():                       # pozostały tylko otwarte
        pnl = m * leverage * ret[k]
        t.at[k, "pnl_usd"] = pnl
        unreal += pnl
    return {"trades": t, "curve": {"ts": curve_ts, "equity": curve_eq}, "realized": eq, "unrealized": unreal,
            "margin_used": used, "skipped_margin": skipped}


def _ts(v) -> int:
    if hasattr(v, "timestamp"):
        return int(v.timestamp())
    return int(v or 0)


def limit_pairs(t: pd.DataFrame, max_pairs: int, rank: list[str], pyramid: int) -> pd.DataFrame:
    """D-050: limit par z otwartymi pozycjami (jak engine.no_overlap_pairs) na transakcjach jednej strategii.
    Transakcje anulowane zostają na liście; otwarte zajmują parę do końca danych."""
    from .engine import no_overlap_pairs

    t = t.reset_index(drop=True)
    act = ~t["status"].str.startswith("anulowana")
    ets = t["entry_ts"].to_numpy(float)
    xts = t["exit_ts"].to_numpy(float)
    bar_exit = np.where(np.isnan(xts), np.inf, xts - H)      # świeca wyjścia (ostrożnie: zajęta do jej końca)
    rk = {q: i for i, q in enumerate(rank)}
    keep, _ = no_overlap_pairs(t["pair"].to_numpy(), ets, ets // H, np.where(act, bar_exit // H, np.nan), bar_exit,
                               t["dir"].to_numpy(), np.array([rk.get(q, len(rk)) for q in t["pair"]]), pyramid, max_pairs)
    return t[keep | ~act]


def compute(inv: dict, h1_dir: Path, now: int | None = None, log=print) -> dict:
    """Pełny stan inwestora na aktualnych danych do liczenia (data/h1_ready)."""
    now = int(time.time()) if now is None else int(now)
    start = _ts(inv.get("createdAt"))
    capital, pct = float(inv["capital"]), float(inv["pct"])
    h1 = {f.stem: pd.read_parquet(f) for f in sorted(Path(h1_dir).glob("*.parquet"))}
    preps = {p: prepare(df) for p, df in h1.items()}
    data_to = max((int(df["ts"].iloc[-1]) + H for df in h1.values()), default=0)
    frames, pending, strat_info, probes = [], [], [], []
    for k, s in enumerate(inv.get("strategies") or []):
        info = {"strategyId": s.get("strategyId"), "name": s.get("name"), "variantId": int(s.get("variantId", 0)),
                "variantLabel": s.get("variantLabel"), "code_hash": hashlib.sha256((s.get("code") or "").encode()).hexdigest()[:16]}
        try:
            # wariant = param_id × liczba wyjść + numer wyjścia (engine.run) — liczymy tylko ten wariant parametrów
            _sig0, meta0 = run_strategy_code(s.get("code") or "", h1_dir, param_ids=[])
            exits = exits_from(meta0.get("exits"))
            pid, xid = divmod(info["variantId"], len(exits))
            if pid >= len(meta0["params"]):
                raise StrategyError(f"wariant {info['variantId']} nie istnieje w kodzie strategii")
            sig, meta = run_strategy_code(s.get("code") or "", h1_dir, param_ids=[pid])
            if meta["lookahead"]:
                raise StrategyError("look-ahead (B2): sygnały zmieniają się po dopisaniu przyszłych świec")
            hours = meta.get("hours")
            hours = tuple(hours) if isinstance(hours, list) else hours
            pyramid = int(meta.get("pyramid") or 1)
            ex = exits[xid]
            info.update({"params": meta["params"][pid], "exit": ex.label()})
            mine = []
            for pair, df in h1.items():
                arr = np.zeros(len(df), np.float32)
                part = sig[(sig.param_id == pid) & (sig.pair == pair)]
                arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
                lvl = None
                if meta.get("levels"):   # D-057
                    lvl = np.full((len(df), 2), np.nan)
                    lvl[part["i"].to_numpy(int), 0] = part["tp"].to_numpy(float)
                    lvl[part["i"].to_numpy(int), 1] = part["sl"].to_numpy(float)
                t = paper_trades(preps[pair], arr, ex, pair, start, hours, pyramid, lv=lvl)
                if not t.empty:
                    tpx = t["tp_px"] if "tp_px" in t else [None] * len(t)
                    spx = t["sl_px"] if "sl_px" in t else [None] * len(t)
                    lv = [exit_levels(ex, e, d, a14, a5, tp_, sl_) for e, d, a14, a5, tp_, sl_ in
                          zip(t["entry_px"], t["dir"], t["atr14"], t["atr5"], tpx, spx)]
                    t["tp"] = [x[0] for x in lv]
                    t["sl"] = [x[1] for x in lv]
                    t["strategy"] = k
                    mine.append(t)
                for x in pending_signals(preps[pair], arr, start, hours):
                    P, i = preps[pair], len(preps[pair]["ts"]) - 1
                    px = float(P["c"][i])
                    tp, sl = exit_levels(ex, px, x["dir"], float(P["atr14"][i]), float(P["atr5"][i]),
                                         lvl[i, 0] if lvl is not None else None, lvl[i, 1] if lvl is not None else None)
                    pending.append({**x, "pair": pair, "strategy": k, "price": px, "tp": tp, "sl": sl, "free": True})
            if mine and meta.get("max_pairs"):
                mine = [limit_pairs(pd.concat(mine, ignore_index=True), meta["max_pairs"], meta.get("pair_rank") or [], pyramid)]
            frames += mine
            probes.append((k, s.get("code") or "", pid, ex, hours, pyramid))
        except (StrategyError, SystemExit) as e:
            info["error"] = str(e)[:500]
            log(f"  inwestor „{inv.get('name')}”: strategia „{s.get('name')}” — błąd: {e}")
        strat_info.append(info)

    trades = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not trades.empty:
        trades = trades.sort_values(["entry_ts", "strategy", "pair"], kind="stable").reset_index(drop=True)
    b = book(trades, capital, pct)
    t = b["trades"]
    now_eq = b["realized"] + b["unrealized"]
    curve_ts = [start] + b["curve"]["ts"] + ([data_to] if data_to > start else [])
    curve_eq = [capital] + b["curve"]["equity"] + ([now_eq] if data_to > start else [])
    eq = np.asarray(curve_eq, float)
    max_dd = float(((eq - np.maximum.accumulate(eq)) / np.maximum.accumulate(eq)).min() * 100) if len(eq) else 0.0
    held = set()
    if not t.empty:
        held = {(int(a), b) for a, b in zip(t.loc[t["status"] == "otwarta", "strategy"], t.loc[t["status"] == "otwarta", "pair"])}
    pyr = {p[0]: p[5] for p in probes}
    for p in pending:                               # B8: sygnał przy zajętej parze nie da wejścia, więc nie alarmuje
        p["free"] = pyr.get(p["strategy"], 1) > 1 or (p["strategy"], p["pair"]) not in held
    upcoming = []
    target = data_to + H                            # zamknięcie trwającej świecy; po przerwie w danych leży w przeszłości
    if h1 and target > now and data_to > 0:
        for k, code, pid, _ex, hours, pyramid in probes:
            busy = set() if pyramid > 1 else {q for s_, q in held if s_ == k} | {p["pair"] for p in pending if p["strategy"] == k}
            try:
                upcoming += upcoming_signals(code, h1_dir, pid, k, target, hours, busy)
            except (StrategyError, SystemExit) as e:
                log(f"  inwestor „{inv.get('name')}”: prognoza sygnału — błąd: {e}")
    rows = []
    for _, r in t.iterrows():
        rows.append({
            "strategy": int(r["strategy"]), "pair": r["pair"], "dir": int(r["dir"]), "weight": round(float(r["weight"]), 3),
            "signal_ts": int(r["signal_ts"]), "entry_ts": int(r["entry_ts"]), "entry_px": float(r["entry_px"]),
            "exit_ts": None if pd.isna(r["exit_ts"]) else int(r["exit_ts"]), "exit_px": float(r["exit_px"]),
            "reason": r["reason"], "status": r["status"], "bars": None if pd.isna(r["bars"]) else int(r["bars"]),
            "pips_net": round(float(r["pips_net"]), 2),
            "tp": None if pd.isna(r["tp"]) else float(r["tp"]), "sl": None if pd.isna(r["sl"]) else float(r["sl"]),
            **{k: None if pd.isna(r[k]) else round(float(r[k]), 2) for k in ("margin_usd", "nominal_usd", "pnl_usd", "equity_after")},
        })
    for si in strat_info:
        k = strat_info.index(si)
        mine = t[t.get("strategy", pd.Series(dtype=int)) == k] if not t.empty else t
        si["trades"] = int((mine["status"] == "zamknięta").sum()) if not t.empty else 0
        si["open"] = int((mine["status"] == "otwarta").sum()) if not t.empty else 0
        si["pnl_usd"] = round(float(mine["pnl_usd"].fillna(0).sum()), 2) if not t.empty else 0.0
    st = t["status"] if not t.empty else pd.Series(dtype=str)
    return {
        "id": inv["id"], "name": inv.get("name"), "capital": capital, "pct": pct, "leverage": LEVERAGE,
        "start": start, "computedAt": now, "dataTo": data_to, "engine_version": ENGINE_VERSION,
        "strategies": strat_info,
        "equity": {"now": round(float(now_eq), 2), "realized": round(float(b["realized"]), 2),
                   "unrealized": round(float(b["unrealized"]), 2), "return_pct": round(float(now_eq / capital - 1) * 100, 3),
                   "max_dd_pct": round(max_dd, 3), "margin_used": round(max(0.0, float(b["margin_used"])), 2)},
        "counts": {"closed": int((st == "zamknięta").sum()), "open": int((st == "otwarta").sum()),
                   "cancelled": int(st.str.startswith("anulowana").sum()) if len(st) else 0,
                   "skipped_margin": int(b["skipped_margin"])},
        "curve": {"ts": [int(x) for x in curve_ts], "equity": [round(float(x), 2) for x in curve_eq]},
        "trades": rows, "pending": pending, "upcoming": upcoming,
    }


def content_hash(state: dict) -> str:
    """Hash treści bez znacznika czasu liczenia — publikujemy tylko, gdy coś się zmieniło."""
    s = {k: v for k, v in state.items() if k != "computedAt"}
    return hashlib.sha256(json.dumps(s, sort_keys=True, default=str).encode()).hexdigest()[:16]


def index_entry(state: dict) -> dict:
    return {"id": state["id"], "name": state["name"], "capital": state["capital"], "pct": state["pct"],
            "start": state["start"], "computedAt": state["computedAt"], "dataTo": state["dataTo"],
            "equity": state["equity"]["now"], "return_pct": state["equity"]["return_pct"],
            "closed": state["counts"]["closed"], "open": state["counts"]["open"],
            "strategies": [s.get("name") for s in state["strategies"]],
            "errors": sum(1 for s in state["strategies"] if s.get("error"))}
