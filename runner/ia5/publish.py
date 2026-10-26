"""Publikacja świec H1 na gałąź `data` (D-010: na GitHub tylko dane z Yahoo, Dukascopy zostaje lokalnie)."""
from __future__ import annotations

import hashlib
import json
import subprocess

import pandas as pd

from .store import DATA_REPO, REPO_URL


def _git(*args, check=True) -> str:
    r = subprocess.run(["git", "-C", str(DATA_REPO), *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout.strip()


def ensure_repo() -> None:
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
