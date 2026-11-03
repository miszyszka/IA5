"""FOREST v2 (D-049): budowa i krok na nowych świecach. Liczy Mac: `ia5 start` robi to sam, po każdej kopii świec."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import pandas as pd

from . import forest as F
from . import forest_report as Rp
from .forest_manager import BOOKS, SEGMENTS, Manager
from .search import LEDGER_NAME
from .store import FOREST

MIN_BARS = 24 * 150


def current_dir(root: Path = FOREST) -> Path:
    return root / "current"


def public_dir(root: Path = FOREST) -> Path:
    return root / "public"


def exists(root: Path = FOREST) -> bool:
    """Las w aktualnej wersji. Starszy las nie liczy się dalej: build przeniesie go do archiwum."""
    f = current_dir(root) / "forest.json"
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("version") == F.FOREST_VERSION
    except (FileNotFoundError, ValueError):
        return False


def usable(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {p: df for p, df in frames.items() if len(df) >= MIN_BARS}


def run_all(frames, seed: int, log=print, until: int | None = None) -> tuple[Manager, F.Panel]:
    pn = F.Panel(frames)
    fr = F.new_forest(pn, seed)
    fr["built_to"] = int(pn.ts.max())
    g = Manager(fr)
    g.advance(pn, until=until, log=log)
    return g, pn


def zero_run(frames, seed: int, log=print) -> dict:
    """Całe doświadczenie na danych bez przewagi: pokazuje, ile reguł i jaki wynik daje samo szczęście."""
    g, pn = run_all(F.null_blocks(frames, seed), 5, lambda m: log(f"[zero] {m}"))
    df = g.frame()
    gens = g.fr["generations"]
    px = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    t = Rp.trades(df, df["ex_m"].to_numpy(bool), px) if len(df) else pd.DataFrame(columns=Rp.EMPTY)
    t = t[t["status"] == "zamknięta"]
    return {
        "seed": seed,
        "passed": round(sum(x["passed"] for x in gens) / max(1, len(gens))),
        "kept": round(sum(x["kept"] for x in gens) / max(1, len(gens))),
        "seg": {s: Rp.cell(t[t["seg"] == s]) for s in SEGMENTS},
    }


def ledger_note(home: Path, fr: dict) -> None:
    f = home / LEDGER_NAME
    try:
        rows = json.loads(f.read_text())
    except (FileNotFoundError, ValueError):
        rows = []
    rows.append(
        {
            "run": fr["id"],
            "at": int(time.time()),
            "kind": "forest2",
            "size": "las v2",
            "tested": F.N_RULES,
            "opened": len(fr["generations"]),
            "oos_from": F.DESIGN_END,
            "oos_to": fr["built_to"],
        }
    )
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, indent=1))


def build(
    frames: dict[str, pd.DataFrame], root: Path = FOREST, zero: int = 1, seed: int = 5, log=print, ledger: Path | None = None
) -> dict:
    """Przejście przez całą historię, odświeżenie po odświeżeniu. Poprzedni las idzie do archiwum."""
    t0 = time.time()
    frames = usable(frames)
    if len(frames) < 2:
        raise ValueError("za mało świec do zbudowania lasu")
    zeros = []
    for k in range(zero):
        log(f"Dane bez przewagi {k + 1}/{zero}…")
        zeros.append(zero_run(frames, 1000 + k, log))
    log("Prawdziwe świece…")
    g, pn = run_all(frames, seed, log)
    g.fr["zero"] = zeros
    if ledger is not None:
        ledger_note(ledger, g.fr)
    cur = current_dir(root)
    if (cur / "forest.json").exists():
        old = json.loads((cur / "forest.json").read_text(encoding="utf-8"))
        arch = root / "archive" / str(old.get("id"))
        if not arch.exists():
            arch.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(cur, arch)
    cur.parent.mkdir(parents=True, exist_ok=True)
    g.save(cur)
    st = Rp.write_public(g, pn, public_dir(root))
    log(
        f"FOREST {g.fr['id']}: {st['counts']['decyzje']:,} decyzji · {len(g.fr['generations'])} odświeżeń "
        f"· {(time.time() - t0) / 60:.1f} min"
    )
    return st


def step(frames: dict[str, pd.DataFrame], root: Path = FOREST, log=print) -> tuple[dict, int]:
    """Nowe świece po kolei; gdy minął termin, las odświeża się sam. Po przerwie nadrabia wszystko."""
    cur = current_dir(root)
    g = Manager.load(cur)
    frames = {p: frames[p] for p in g.fr["pairs"] if p in frames}
    pn = F.Panel(frames)
    made = g.advance(pn, log=log)
    g.save(cur)
    return Rp.write_public(g, pn, public_dir(root)), made


__all__ = ["BOOKS", "build", "step", "exists"]
