"""FOREST (D-048): budowa lasu i krok na nowych świecach. Liczy Mac: `ia5 start` robi to sam, po każdej kopii świec."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import forest as F
from . import forest_report as Rp
from .forest_manager import BOOKS, SEGMENTS, Manager
from .search import LEDGER_NAME, null_frames
from .store import FOREST

MIN_BARS = 24 * 150  # poniżej tego las nie ma z czego się uczyć (kucie + mapy + OOS)


def current_dir(root: Path = FOREST) -> Path:
    return root / "current"


def public_dir(root: Path = FOREST) -> Path:
    return root / "public"


def exists(root: Path = FOREST) -> bool:
    return (current_dir(root) / "state.json").exists()


def usable(frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {p: df for p, df in frames.items() if len(df) >= MIN_BARS}


def zero_run(frames, seed: int, n_candidates: int, workers: int | None, log=print, n_investors: int = F.N_INVESTORS) -> dict:
    """Całe doświadczenie na danych bez przewagi: kucie, mapy, księgi. To pokazuje, ile daje samo szczęście."""
    nf = null_frames(frames, seed)
    pn = F.Panel(nf)
    fr = F.forge(nf, n_candidates, n_investors, seed=seed, workers=workers, log=lambda m: log(f"[zero] {m}"), pn=pn)
    g = Manager(fr)
    g.advance(pn, log=lambda m: log(f"[zero] {m}"))
    df = g.frame()
    gross, closed, _ = Rp.outcomes(df, df["dir"].to_numpy(), df["h"].to_numpy())
    books = {}
    for b in BOOKS:
        t = Rp.book_trades(df, b, {p: float(pn.P[p]["c"][-1]) for p in pn.pairs})
        t = t[t["status"] == "zamknięta"]
        books[b] = {s: Rp.cell(t.gross[t.seg == s].to_numpy(float), t.pips_net[t.seg == s].to_numpy(float)) for s in SEGMENTS}
    d = df.assign(net=gross - df["spread"].to_numpy())[closed & np.isfinite(gross)].sort_values("ts", kind="stable")
    learn = {s: Rp.rank_test(d.z[d.seg == s].to_numpy(float), d.net[d.seg == s].to_numpy(float)) for s in ("MAPY", "OOS")}
    return {
        "seed": seed,
        "forge": {k: fr["forge"][k] for k in ("passed", "t_cv_mean", "t_cv_min", "t_cv_top", "n_eff", "srednia_abs_rho")},
        "quality": Rp.forest_quality(g),
        "books": books,
        "uczenie": learn,
    }


def ledger_note(home: Path, fr: dict) -> int:
    """Dziennik otwarć OOS (D-044): las też go otwiera, a każde spojrzenie obniża jego wartość."""
    f = home / LEDGER_NAME
    try:
        rows = json.loads(f.read_text())
    except (FileNotFoundError, ValueError):
        rows = []
    rows.append(
        {
            "run": fr["id"],
            "at": int(time.time()),
            "kind": "forest",
            "size": "las",
            "tested": fr["forge"]["candidates"],
            "opened": len(fr["investors"]),
            "oos_from": fr["cuts"]["oos"],
            "oos_to": fr["cuts"]["t1"],
        }
    )
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(rows, indent=1))
    return sum(1 for r in rows if abs(r["oos_from"] - fr["cuts"]["oos"]) < 30 * 86400)


def build(
    frames: dict[str, pd.DataFrame],
    root: Path = FOREST,
    n_candidates: int = F.N_CANDIDATES,
    zero: int = 1,
    seed: int = 1,
    workers: int | None = None,
    log=print,
    ledger: Path | None = None,
    n_investors: int = F.N_INVESTORS,
) -> dict:
    """Kucie → test zerowy (przed otwarciem OOS) → przejście Managera przez MAPY i OOS → zapis. Poprzedni las idzie do archiwum."""
    t0 = time.time()
    frames = usable(frames)
    if len(frames) < 2:
        raise ValueError("za mało świec do zbudowania lasu")
    pn = F.Panel(frames)
    fr = F.forge(frames, n_candidates, n_investors, seed=seed, workers=workers, log=log, pn=pn)
    fr["zero"] = []
    for k in range(zero):
        log(f"Test zerowy {k + 1}/{zero}: to samo na danych bez przewagi…")
        fr["zero"].append(zero_run(frames, 1000 + k, n_candidates, workers, log, n_investors))
    log("Manager: przejście przez MAPY i OOS…")
    g = Manager(fr)
    g.advance(pn, log=log)
    if ledger is not None:
        fr["oos_opened"] = ledger_note(ledger, fr)
    cur = current_dir(root)
    if exists(root):
        old = json.loads((cur / "forest.json").read_text(encoding="utf-8"))
        arch = root / "archive" / old["id"]
        if not arch.exists():
            arch.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(cur, arch)
    cur.parent.mkdir(parents=True, exist_ok=True)
    g.save(cur)
    st = Rp.write_public(g, pn, public_dir(root))
    log(f"FOREST {fr['id']}: {st['counts']['decyzje']:,} decyzji, {st['counts']['mapy']:,} map · {(time.time() - t0) / 60:.1f} min")
    return st


def step(frames: dict[str, pd.DataFrame], root: Path = FOREST, log=print) -> tuple[dict, int]:
    """Nowe świece po kolei: decyzje, rozliczenia, mapy. Po przerwie nadrabia wszystko, co ominęło. Zwraca (stan, nowe decyzje)."""
    cur = current_dir(root)
    g = Manager.load(cur)
    frames = {p: frames[p] for p in g.fr["pairs"] if p in frames}
    pn = F.Panel(frames)
    made = g.advance(pn, log=log)
    g.save(cur)
    return Rp.write_public(g, pn, public_dir(root)), made
