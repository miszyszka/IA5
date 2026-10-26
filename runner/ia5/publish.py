"""Publikacja świec H1 na gałąź `data` (D-010: na GitHub tylko dane z Yahoo, Dukascopy zostaje lokalnie)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

from .store import DATA_REPO, REPO_URL


def _git(*args, check=True) -> str:
    r = subprocess.run(["git", "-C", str(DATA_REPO), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def _identity() -> None:
    """Commit wymaga tożsamości gita; gdy na komputerze jej nie ma, ustawiamy ją tylko dla klonu gałęzi data."""
    if not _git("config", "user.email", check=False):
        _git("config", "user.name", "IA5 (ia5 start)")
        _git("config", "user.email", "ia5@localhost")


def ensure_repo() -> None:
    _ensure_repo()
    _identity()


def _ensure_repo() -> None:
    if (DATA_REPO / ".git").exists():
        _git("fetch", "-q", "origin", "data", check=False)
        if _git("rev-parse", "--verify", "-q", "origin/data", check=False):
            _git("checkout", "-q", "data")
            _git("reset", "-q", "--hard", "origin/data")
        return
    DATA_REPO.mkdir(parents=True, exist_ok=True)
    _git("init", "-q")
    _git("remote", "add", "origin", REPO_URL)
    _git("fetch", "-q", "origin", "data", check=False)
    if _git("rev-parse", "--verify", "-q", "origin/data", check=False):
        _git("checkout", "-q", "-b", "data", "origin/data")
    else:
        _git("checkout", "-q", "--orphan", "data")


def frame_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:16]


def publish_candles(h1: dict[str, pd.DataFrame], source: str, log=print) -> str | None:
    """Zapisuje candles/{PARA}/{RRRR}.parquet tylko tam, gdzie dane się zmieniły. Zwraca SHA lub None."""
    ensure_repo()
    mpath = DATA_REPO / "candles" / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"files": {}}
    changed = 0
    for pair, df in h1.items():
        if df.empty:
            continue
        years = pd.to_datetime(df["ts"], unit="s", utc=True).dt.year
        for y, part in df.groupby(years):
            rel = f"candles/{pair}/{y}.parquet"
            part = part[["ts", "open", "high", "low", "close"]].reset_index(drop=True)
            h = frame_hash(part)
            if manifest["files"].get(rel, {}).get("hash") == h:
                continue
            path = DATA_REPO / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            part.to_parquet(path, index=False)
            manifest["files"][rel] = {"hash": h, "bars": len(part),
                                      "from": int(part.ts.iloc[0]), "to": int(part.ts.iloc[-1])}
            changed += 1
    if not changed:
        log("  gałąź data: bez zmian")
        return None
    manifest["source"] = source
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    _git("add", "-A")
    _git("commit", "-q", "-m", f"dane: świece H1 ({changed} plików)")
    _git("push", "-q", "origin", "data")
    sha = _git("rev-parse", "HEAD")
    log(f"  gałąź data: {changed} plików, {sha[:7]}")
    return sha


# ---------- wyniki strategii (results/{id}/ + results/index.json) ----------

def index_entry(res_dir: Path) -> dict:
    m = json.loads((res_dir / "manifest.json").read_text(encoding="utf-8"))
    v = json.loads((res_dir / "validation.json").read_text(encoding="utf-8"))
    return {
        "id": m["id"], "name": m["name"], "run_id": m["run_id"], "created": m["created"],
        "verdict": v.get("verdict", {}).get("color"), "verdict_note": v.get("verdict", {}).get("note"),
        "n_variants": m["n_variants"], "hypothesis": m.get("hypothesis"), "pairs": m["pairs"],
        "data_from": m["data_from"], "data_to": m["data_to"], "source": m["data_source"],
        "engine_version": m["engine_version"], "best_exit": v.get("best_exit"),
        "is_mean_r": v.get("is_mean_r"), "oos_mean_r": v.get("oos_mean_r"), "oos_mean_pips": v.get("oos_mean_pips"),
        "oos_trades": v.get("oos_trades"), "demo": bool(m.get("demo")),
    }


def _write_index(entries: list[dict]) -> None:
    p = DATA_REPO / "results" / "index.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    entries = sorted(entries, key=lambda e: e.get("created", 0), reverse=True)
    p.write_text(json.dumps({"strategies": entries}, ensure_ascii=False, indent=1), encoding="utf-8")


def _read_index() -> list[dict]:
    p = DATA_REPO / "results" / "index.json"
    return json.loads(p.read_text(encoding="utf-8"))["strategies"] if p.exists() else []


def publish_result(res_dir: Path, log=print) -> str:
    """Kopiuje wynik na gałąź data (zastępuje poprzedni run tej strategii) i aktualizuje indeks."""
    import shutil

    ensure_repo()
    entry = index_entry(res_dir)
    dst = DATA_REPO / "results" / entry["id"]
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(res_dir, dst)
    _write_index([e for e in _read_index() if e["id"] != entry["id"]] + [entry])
    _git("add", "-A")
    _git("commit", "-q", "-m", f"wyniki: {entry['name']} ({entry['run_id']})")
    _git("push", "-q", "origin", "data")
    sha = _git("rev-parse", "HEAD")
    log(f"  opublikowano results/{entry['id']} ({sha[:7]})")
    return sha


def delete_result(strategy_id: str, log=print) -> str | None:
    """Usuwa wynik strategii z gałęzi data i z indeksu (historia gita zostaje — G4)."""
    import shutil

    ensure_repo()
    dst = DATA_REPO / "results" / strategy_id
    before = _read_index()
    after = [e for e in before if e["id"] != strategy_id]
    if not dst.exists() and len(after) == len(before):
        return None
    if dst.exists():
        shutil.rmtree(dst)
    _write_index(after)
    _git("add", "-A")
    _git("commit", "-q", "-m", f"usunięto strategię {strategy_id}")
    _git("push", "-q", "origin", "data")
    log(f"  usunięto results/{strategy_id}")
    return _git("rev-parse", "HEAD")
