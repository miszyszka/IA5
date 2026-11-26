"""D-075: korelacja wyników strategii — czy nowa strategia jest innym źródłem zysku niż te, które już mamy.

Miara: tygodniowe sumy R netto najlepszego (albo zamrożonego) wariantu, tydzień = tydzień wyjścia (UTC, od poniedziałku).
Para strategii porównywana tylko na wspólnym okresie (od późniejszego startu do wcześniejszego końca), tygodnie bez
transakcji = 0. Mniej niż MIN_WEEKS wspólnych tygodni → bez wyniku. Korelacja tylko informuje — nic nie blokuje i nie
wchodzi do werdyktu; służy do składania księgi z mało skorelowanych strategii (ROADMAP, etap C2).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

MIN_WEEKS = 26
WEEK = 7 * 86400
MONDAY0 = 4 * 86400   # 1970-01-01 to czwartek — przesunięcie, żeby tydzień zaczynał się w poniedziałek


def weekly(trades: pd.DataFrame) -> pd.Series:
    """Tygodniowe sumy r_net (indeks = numer tygodnia od poniedziałku 1969-12-29)."""
    if trades is None or trades.empty:
        return pd.Series(dtype=float)
    wk = ((trades["exit_ts"].to_numpy(np.int64) + MONDAY0) // WEEK)
    return pd.Series(trades["r_net"].to_numpy(float)).groupby(wk).sum()


def corr(a: pd.Series, b: pd.Series, min_weeks: int = MIN_WEEKS) -> tuple[float | None, int]:
    if a.empty or b.empty:
        return None, 0
    lo, hi = max(a.index.min(), b.index.min()), min(a.index.max(), b.index.max())
    if hi - lo + 1 < min_weeks:
        return None, max(0, int(hi - lo + 1))
    idx = np.arange(lo, hi + 1)
    x, y = a.reindex(idx, fill_value=0.0).to_numpy(), b.reindex(idx, fill_value=0.0).to_numpy()
    if x.std() == 0 or y.std() == 0:
        return None, len(idx)
    return float(np.corrcoef(x, y)[0, 1]), len(idx)


def latest_runs(root: Path) -> dict[str, Path]:
    """Ostatni run każdej strategii w katalogu wyników (results/{id}/{run}/)."""
    out = {}
    root = Path(root)
    if not root.exists():
        return out
    for sdir in sorted(p for p in root.iterdir() if p.is_dir()):
        runs = sorted(r for r in sdir.iterdir() if r.is_dir() and (r / "validation.json").exists() and (r / "trades.parquet").exists())
        if runs:
            out[sdir.name] = runs[-1]
    return out


def run_series(run: Path) -> tuple[pd.Series, dict]:
    """Tygodniowy wynik najlepszego/zamrożonego wariantu jednego runu + opis (nazwa, zamrożona)."""
    v = json.loads((run / "validation.json").read_text(encoding="utf-8"))
    m = json.loads((run / "manifest.json").read_text(encoding="utf-8")) if (run / "manifest.json").exists() else {}
    vid = v.get("best_variant_id")
    info = {"id": m.get("id") or run.parent.name, "name": m.get("name") or run.parent.name, "frozen": bool(m.get("frozen_at")),
            "variant": vid}
    if vid is None:
        return pd.Series(dtype=float), info
    t = pd.read_parquet(run / "trades.parquet", columns=["variant_id", "exit_ts", "r_net"], filters=[("variant_id", "==", int(vid))])
    return weekly(t), info


def against_others(root: Path, sid: str, best: pd.DataFrame, min_weeks: int = MIN_WEEKS) -> dict:
    """Korelacja najlepszego wariantu liczonej strategii z ostatnim runem każdej innej strategii w `root`."""
    mine = weekly(best)
    others = []
    for oid, run in latest_runs(root).items():
        if oid == sid:
            continue
        try:
            s, info = run_series(run)
        except (OSError, ValueError, KeyError):
            continue
        c, n = corr(mine, s, min_weeks)
        if c is not None:
            others.append({**info, "corr": round(c, 3), "weeks": n})
    return {"min_weeks": min_weeks, "others": others}


def matrix(root: Path, min_weeks: int = MIN_WEEKS) -> pd.DataFrame:
    """Macierz korelacji wszystkich policzonych strategii (ia5 korelacja)."""
    series, names = {}, {}
    for oid, run in latest_runs(root).items():
        try:
            s, info = run_series(run)
        except (OSError, ValueError, KeyError):
            continue
        series[oid] = s
        names[oid] = info["name"] + (" ❄" if info["frozen"] else "")
    ids = list(series)
    out = pd.DataFrame(np.nan, index=[names[i] for i in ids], columns=[names[i] for i in ids])
    for a in ids:
        for b in ids:
            out.loc[names[a], names[b]] = 1.0 if a == b else corr(series[a], series[b], min_weeks)[0]
    return out
