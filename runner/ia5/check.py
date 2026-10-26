"""Szybka kontrola kodu strategii przed wysłaniem do liczenia (`ia5 check`, scripts/check_strategy.py).

Sprawdza: kontrakt (sekcja 7), import i wykonanie w osobnym procesie, detektor look-ahead (B2),
liczbę sygnałów na parę i wariant parametrów, typowe pomyłki (stan zamiast zdarzenia, brak sygnałów,
brak hipotezy, za duża siatka). Zwraca listę błędów (blokujących) i ostrzeżeń.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .engine import default_exits
from .sandbox import StrategyError, run_strategy_code

MAX_VARIANTS_WARN = 3000


def synthetic_h1(folder: Path, n: int = 6000, seed: int = 3) -> Path:
    """8 par z losowym błądzeniem w realistycznej skali cen i zmienności (tylko do kontroli kodu)."""
    from .config import PAIRS

    folder.mkdir(parents=True, exist_ok=True)
    start = {"EURUSD": 1.10, "USDJPY": 150.0, "GBPUSD": 1.30, "EURGBP": 0.85, "AUDUSD": 0.66,
             "USDCHF": 0.88, "USDCAD": 1.37, "EURJPY": 163.0}
    rng = np.random.default_rng(seed)
    ts = 1735516800 + 3600 * np.arange(n)  # od poniedziałku 2024-12-30, ciągłe godziny
    for pair in PAIRS:
        p0 = start[pair]
        vol = p0 * 0.0012
        c = p0 + np.cumsum(rng.normal(0, vol, n))
        o = np.r_[c[0], c[:-1]]
        h = np.maximum(o, c) + rng.random(n) * vol
        lo = np.minimum(o, c) - rng.random(n) * vol
        pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c}).to_parquet(folder / f"{pair}.parquet", index=False)
    return folder


def check_code_on(code: str, h1_dir: Path) -> dict:
    """Wynik: {"ok", "errors", "warnings", "info", "signals": tabela}."""
    errors, warnings, info = [], [], []
    try:
        sig, meta = run_strategy_code(code, h1_dir, timeout=600)
    except StrategyError as e:
        return {"ok": False, "errors": [str(e)], "warnings": [], "info": [], "signals": None}
    if meta["lookahead"]:
        for la in meta["lookahead"][:3]:
            errors.append(f"Look-ahead (B2): {la['pair']}, parametry #{la['param_id']} — sygnały zmieniają się po dopisaniu "
                          "przyszłych świec. Szukaj: shift(-k), statystyk z całej serii, center=True, niezamkniętej świecy "
                          "wyższego interwału (resample bez shift(1)), maksimum/minimum dnia przez transform "
                          "(docs/STRATEGIE.md, sekcja 6).")
    params = meta["params"]
    n_exits = len(meta["exits"]) if meta.get("exits") else len(default_exits())
    n_var = len(params) * n_exits
    info.append(f"Warianty: {len(params)} wejścia × {n_exits} wyjść = {n_var}.")
    if n_var > MAX_VARIANTS_WARN:
        warnings.append(f"{n_var} wariantów — przy tak dużym przeszukaniu DSR i PBO mocno ukarzą wynik (W2). Zawęź PARAMS.")
    if not meta.get("hypothesis"):
        warnings.append("Brak HYPOTHESIS — spisz w 1–3 zdaniach, dlaczego to ma działać, zanim zobaczysz wynik.")

    bars = {f.stem: len(pd.read_parquet(f, columns=["ts"])) for f in sorted(h1_dir.glob("*.parquet"))}
    rows = []
    for pid, p in enumerate(params):
        for pair, n in bars.items():
            s = sig[(sig.param_id == pid) & (sig.pair == pair)]
            i = np.sort(s["i"].to_numpy())
            consec = float(np.mean(np.diff(i) == 1)) if len(i) > 1 else 0.0
            rows.append({"param_id": pid, "params": p, "pair": pair, "signals": len(s), "long": int((s.sig > 0).sum()),
                         "short": int((s.sig < 0).sum()), "pct_bars": 100 * len(s) / n, "consecutive": consec})
    tab = pd.DataFrame(rows)
    if not tab.empty:
        if tab["signals"].sum() == 0:
            errors.append("Strategia nie daje żadnych sygnałów na żadnej parze.")
        elif (tab.groupby("param_id")["signals"].sum() == 0).any():
            dead = tab.groupby("param_id")["signals"].sum()
            warnings.append(f"Warianty parametrów bez sygnałów: {[params[i] for i in dead[dead == 0].index]}.")
        if tab["pct_bars"].max() > 10:
            warnings.append(f"Sygnał w {tab['pct_bars'].max():.0f}% świec — to raczej stan niż zdarzenie. "
                            "Użyj ind.cross_above / cross_below albo warunku „pierwsza świeca, w której…”.")
        if tab["consecutive"].max() > 0.5:
            warnings.append("Ponad połowa sygnałów pada w kolejnych świecach (stan zamiast zdarzenia). Silnik i tak "
                            "pominie je przy otwartej pozycji (B8), ale lepiej sygnalizować tylko moment wejścia.")
        if tab["short"].sum() == 0:
            info.append("Tylko pozycje long.")
        elif tab["long"].sum() == 0:
            info.append("Tylko pozycje short.")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "info": info, "signals": tab, "meta": meta}


def format_result(res: dict, data_label: str) -> str:
    out = [f"Kontrola strategii na: {data_label}"]
    out += [f"✘ {e}" for e in res["errors"]]
    out += [f"⚠ {w}" for w in res["warnings"]]
    out += [f"· {i}" for i in res["info"]]
    tab = res.get("signals")
    if tab is not None and not tab.empty:
        g = tab.groupby("param_id").agg(sygnały=("signals", "sum"), long=("long", "sum"), short=("short", "sum"),
                                        proc=("pct_bars", "mean"))
        for pid, r in g.iterrows():
            p = ", ".join(f"{k}={v}" for k, v in res["meta"]["params"][pid].items()) or "—"
            out.append(f"  parametry [{p}]: {int(r.sygnały)} sygnałów (long {int(r.long)}, short {int(r.short)}), "
                       f"{r.proc:.2f}% świec")
    out.append("WYNIK: " + ("OK — można wkleić do dashboardu." if res["ok"] else "BŁĄD — popraw przed wysłaniem."))
    return "\n".join(out)
