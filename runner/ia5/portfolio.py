"""Symulacja kapitału (CLAUDE.md 8.5, B4). Ta sama logika jest w web/js/metrics.js (simulateEquity) — zmiany w obu miejscach.

Model: depozyt = X% bieżącego kapitału przy wejściu, nominał = dźwignia × depozyt. Suma depozytów otwartych
pozycji ≤ 100% kapitału — sygnał bez wolnego depozytu jest pomijany. Zysk transakcji = nominał × zwrot,
gdzie zwrot = pipsy netto × pips ÷ cena wejścia (zwrot na nominale w walucie kwotowanej; dla par bez USD
jako waluty kwotowanej to przybliżenie — różnica kursów przeliczenia między wejściem a wyjściem pomijana, D-014).
"""
from __future__ import annotations

import bisect

import numpy as np
import pandas as pd

from .config import LEVERAGE, PAIRS, START_CAPITAL


def trade_returns(t: pd.DataFrame) -> np.ndarray:
    pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
    return t["pips_net"].to_numpy(float) * pip / t["entry_px"].to_numpy(float)


DAY = 86400
VOL_WINDOW_DAYS = 60      # D-075: cel zmienności — zmienność kapitału z ostatnich 60 dni kalendarzowych (tylko przeszłość)
VOL_MIN_DAYS = 20         # wcześniej skala 1
VOL_SCALE = (0.25, 2.0)   # skala stawki przycięta do tego zakresu


def rules_from(meta: dict | None) -> dict:
    """D-075: zasady portfela zadeklarowane przez strategię (sandbox.read_settings) — w manifeście i w karcie."""
    m = meta or {}
    return {"sizing_mode": m.get("sizing_mode") or "margin", "vol_target": m.get("vol_target"),
            "max_ccy": m.get("max_ccy"), "brake": m.get("brake")}


def vol_scale(days: list, eqs: list, now: int, target_pct: float) -> float:
    """Skala stawki z celu zmienności: target / zmienność roczna dziennych zmian kapitału z VOL_WINDOW_DAYS dni przed dniem `now`
    (kapitał zrealizowany, dni bez zmian = zwrot 0; √365 — dni kalendarzowe). Mniej niż VOL_MIN_DAYS historii albo zerowa
    zmienność → 1. Wynik przycięty do VOL_SCALE."""
    if not days:
        return 1.0
    today = now // DAY
    first = days[0]
    if today - first < VOL_MIN_DAYS:
        return 1.0
    lo = max(first, today - VOL_WINDOW_DAYS)
    # kapitał na koniec każdego dnia lo-1 … today-1 (ostatnia znana wartość)
    vals = []
    j = bisect.bisect_right(days, lo - 1)        # pierwszy dzień > lo−1; ostatnia znana wartość przed nim
    last = eqs[j - 1] if j > 0 else None
    for dd in range(lo - 1, today):
        while j < len(days) and days[j] <= dd:
            last = eqs[j]
            j += 1
        vals.append(last)
    v = np.array([x for x in vals if x is not None], float)
    if len(v) < 3:
        return 1.0
    r = v[1:] / v[:-1] - 1
    sd = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    if not sd > 0:
        return 1.0
    return float(np.clip(target_pct / 100 / (sd * np.sqrt(365)), *VOL_SCALE))


def simulate_equity(t: pd.DataFrame, pct: float, capital: float = START_CAPITAL, leverage: float = LEVERAGE,
                    rules: dict | None = None) -> dict:
    """t: transakcje jednego wariantu (entry_ts, exit_ts, pair, pips_net, entry_px). pct: depozyt w % kapitału (B4) —
    albo, przy rules["sizing_mode"] == "risk" (D-075), % kapitału RYZYKOWANY do SL (nominał = ryzyko ÷ odległość SL).

    rules (D-075, wszystkie opcjonalne):
      sizing_mode  "margin" (domyślnie, B4) | "risk";
      vol_target   % rocznie — stawka × skala z celu zmienności kapitału (vol_scale);
      max_ccy      najwięcej pozycji (suma wag) w jedną stronę na jedną walutę — long EUR/USD = +EUR −USD;
      brake        (spadek %, dni): spadek kapitału zrealizowanego od szczytu ≥ spadek → bez nowych wejść przez tyle dni
                   (potem szczyt liczony od nowa).
    Zawsze: suma depozytów ≤ 100% kapitału (łącznie nigdy ponad 30:1). W trybie risk depozyt większy niż wolny jest
    zmniejszany do wolnego (licznik capped)."""
    r_ = rules or {}
    mode = r_.get("sizing_mode") or "margin"
    vt, mcc, brake = r_.get("vol_target"), r_.get("max_ccy"), r_.get("brake")
    if t.empty:
        return {"ts": [], "equity": [], "taken": 0, "skipped_margin": 0, "final": capital,
                "skipped_ccy": 0, "skipped_brake": 0, "capped": 0}
    ret = trade_returns(t)
    wts = t["weight"].to_numpy(float) if "weight" in t else np.ones(len(t))
    pairs = t["pair"].to_numpy()
    dirs = t["dir"].to_numpy(float) if "dir" in t else np.ones(len(t))
    risk_ret = np.full(len(t), np.nan)
    if mode == "risk":
        if "risk_pips" not in t:
            raise ValueError("sizing_mode risk: transakcje bez kolumny risk_pips")
        pipv = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
        risk_ret = t["risk_pips"].to_numpy(float) * pipv / t["entry_px"].to_numpy(float)
    # D-055: najgorsza chwila każdej pozycji (MAE w pipsach) jako zwrot — do pesymistycznego obsunięcia
    pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
    mae_ret = (np.nan_to_num(t["mae"].to_numpy(float)) * pip / t["entry_px"].to_numpy(float)) if "mae" in t else np.zeros(len(t))
    ev = []  # (czas, typ: 0=wyjście przed 1=wejście w tej samej chwili, indeks)
    for k, (a, b) in enumerate(zip(t["entry_ts"].to_numpy(), t["exit_ts"].to_numpy())):
        ev.append((int(a), 1, k))
        ev.append((int(b), 0, k))
    ev.sort()
    eq = capital
    margin_used = 0.0
    open_pos: dict[int, float] = {}
    pts_ts, pts_eq = [int(t["entry_ts"].min())], [capital]
    skipped = skipped_ccy = skipped_brake = capped = 0
    peak, worst = capital, 0.0   # D-055: obsunięcie z wyceną otwartych pozycji w ich najgorszym punkcie
    expo: dict[str, float] = {}  # D-075: ekspozycja na waluty otwartych pozycji (suma wag ze znakiem)
    pause_until, brake_peak = -1, capital
    eq_days: list[int] = []
    eq_vals: list[float] = []
    for ts, kind, k in ev:
        if kind == 1:
            if brake and ts < pause_until:
                skipped_brake += 1
                continue
            scale = vol_scale(eq_days, eq_vals, ts, float(vt)) if vt else 1.0
            if mode == "risk":
                rr = risk_ret[k]
                m = eq * pct / 100 * wts[k] * scale / rr / leverage if rr > 0 else eq * pct / 100 * wts[k] * scale
            else:
                m = eq * pct / 100 * wts[k] * scale  # D-034: waga pozycji mnoży depozyt
            if mcc:
                b, q = str(pairs[k])[:3], str(pairs[k])[3:]
                sgn = dirs[k] * wts[k]
                if abs(expo.get(b, 0.0) + sgn) > mcc + 1e-9 or abs(expo.get(q, 0.0) - sgn) > mcc + 1e-9:
                    skipped_ccy += 1
                    continue
            if eq <= 0:
                skipped += 1
                continue
            if margin_used + m > eq + 1e-9:
                if mode == "risk" and eq - margin_used > 1e-9:
                    m = eq - margin_used
                    capped += 1
                else:
                    skipped += 1
                    continue
            open_pos[k] = m
            margin_used += m
            if mcc:
                expo[b] = expo.get(b, 0.0) + sgn
                expo[q] = expo.get(q, 0.0) - sgn
        elif k in open_pos:
            m = open_pos.pop(k)
            margin_used -= m
            eq += m * leverage * ret[k]
            pts_ts.append(ts)
            pts_eq.append(eq)
            if mcc:
                b, q = str(pairs[k])[:3], str(pairs[k])[3:]
                sgn = dirs[k] * wts[k]
                expo[b] = expo.get(b, 0.0) - sgn
                expo[q] = expo.get(q, 0.0) + sgn
            if vt:
                dday = int(ts) // DAY
                if eq_days and eq_days[-1] == dday:
                    eq_vals[-1] = eq
                else:
                    if not eq_days:   # dzień przed pierwszym wyjściem = kapitał startowy
                        eq_days.append(dday - 1)
                        eq_vals.append(capital)
                    eq_days.append(dday)
                    eq_vals.append(eq)
            if brake:
                brake_peak = max(brake_peak, eq)
                if brake_peak > 0 and (brake_peak - eq) / brake_peak * 100 >= float(brake[0]) - 1e-12:
                    pause_until = int(ts) + int(round(float(brake[1]) * DAY))
                    brake_peak = eq
        peak = max(peak, eq)
        floor = eq - sum(open_pos[j] * leverage * mae_ret[j] for j in open_pos)   # wszystkie otwarte w swoim najgorszym punkcie
        if peak > 0:
            worst = min(worst, (floor - peak) / peak)
    return {"ts": pts_ts, "equity": pts_eq, "taken": len(t) - skipped - skipped_ccy - skipped_brake, "skipped_margin": skipped,
            "final": eq, "max_dd_mae": worst, "skipped_ccy": skipped_ccy, "skipped_brake": skipped_brake, "capped": capped}


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
    dd_mae = min(float(curve.get("max_dd_mae", max_dd)), max_dd)   # D-055: nigdy łagodniejsze niż obsunięcie zrealizowane
    return {"final": float(final), "return_pct": float(final / capital - 1) * 100, "cagr_pct": cagr * 100,
            "max_dd_pct": max_dd * 100, "max_dd_mae_pct": dd_mae * 100,
            "calmar": (cagr / -max_dd) if max_dd < 0 else np.nan,
            "sharpe": sharpe, "sortino": sortino, "longest_underwater_days": longest / 86400}
