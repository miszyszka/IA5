"""Symulacja kapitału (CLAUDE.md 8.5, B4). Ta sama logika jest w web/js/portfolio.js — zmiany w obu miejscach.

Model: depozyt = X% bieżącego kapitału przy wejściu, nominał = dźwignia × depozyt. Suma depozytów otwartych
pozycji ≤ 100% kapitału — sygnał bez wolnego depozytu jest pomijany. Zysk transakcji = nominał × zwrot,
gdzie zwrot = pipsy netto × pips ÷ cena wejścia (zwrot na nominale w walucie kwotowanej; dla par bez USD
jako waluty kwotowanej to przybliżenie — różnica kursów przeliczenia między wejściem a wyjściem pomijana, D-014).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import LEVERAGE, PAIRS, START_CAPITAL


def trade_returns(t: pd.DataFrame) -> np.ndarray:
    pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
    return t["pips_net"].to_numpy(float) * pip / t["entry_px"].to_numpy(float)


def simulate_equity(t: pd.DataFrame, pct: float, capital: float = START_CAPITAL, leverage: float = LEVERAGE) -> dict:
    """t: transakcje jednego wariantu (entry_ts, exit_ts, pair, pips_net, entry_px). pct: depozyt w % kapitału."""
    if t.empty:
        return {"ts": [], "equity": [], "taken": 0, "skipped_margin": 0, "final": capital}
    ret = trade_returns(t)
    ev = []  # (czas, typ: 0=wyjście przed 1=wejście w tej samej chwili, indeks)
    for k, (a, b) in enumerate(zip(t["entry_ts"].to_numpy(), t["exit_ts"].to_numpy())):
        ev.append((int(a), 1, k))
        ev.append((int(b), 0, k))
    ev.sort()
    eq = capital
    margin_used = 0.0
    open_pos: dict[int, float] = {}
    pts_ts, pts_eq = [int(t["entry_ts"].min())], [capital]
    skipped = 0
    for ts, kind, k in ev:
        if kind == 1:
            m = eq * pct / 100
            if margin_used + m > eq + 1e-9 or eq <= 0:
                skipped += 1
                continue
            open_pos[k] = m
            margin_used += m
        elif k in open_pos:
            m = open_pos.pop(k)
            margin_used -= m
            eq += m * leverage * ret[k]
            pts_ts.append(ts)
            pts_eq.append(eq)
    return {"ts": pts_ts, "equity": pts_eq, "taken": len(t) - skipped, "skipped_margin": skipped, "final": eq}


def equity_stats(curve: dict, capital: float = START_CAPITAL) -> dict:
    ts, eq = np.asarray(curve["ts"], float), np.asarray(curve["equity"], float)
    if len(eq) < 2:
        return {}
    peak = np.maximum.accumulate(eq)
    dd = (eq - peak) / peak
    years = max((ts[-1] - ts[0]) / (365.25 * 86400), 1e-9)
    final = eq[-1]
    cagr = (final / capital) ** (1 / years) - 1 if final > 0 else -1.0
    s = pd.Series(eq, index=pd.to_datetime(ts, unit="s", utc=True)).resample("1D").last().ffill()
    r = s.pct_change().dropna()
    sharpe = float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 2 and r.std() > 0 else np.nan
    neg = r[r < 0]
    sortino = float(r.mean() / neg.std() * np.sqrt(252)) if len(neg) > 2 and neg.std() > 0 else np.nan
    max_dd = float(dd.min())
    under = dd < 0
    longest = cur = 0.0
    for k in range(1, len(ts)):
        cur = cur + (ts[k] - ts[k - 1]) if under[k] else 0.0
        longest = max(longest, cur)
    return {"final": float(final), "return_pct": float(final / capital - 1) * 100, "cagr_pct": cagr * 100,
            "max_dd_pct": max_dd * 100, "calmar": (cagr / -max_dd) if max_dd < 0 else np.nan,
            "sharpe": sharpe, "sortino": sortino, "longest_underwater_days": longest / 86400}
