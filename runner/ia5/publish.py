"""Publikacja na gałąź `data`: świece H1 Yahoo, mapa pokrycia, wyniki strategii i skany (D-039: jedno źródło — Yahoo)."""
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


def _push(tries: int = 4) -> None:
    """D-052: gałąź data ma dwóch piszących (Mac i GitHub Actions) — odrzucony push doczytuje cudzy commit i ponawia."""
    for attempt in range(tries):
        try:
            _git("push", "-q", "origin", "data")
            return
        except RuntimeError:
            if attempt == tries - 1:
                raise
            try:
                _git("pull", "-q", "--rebase", "origin", "data")
            except RuntimeError:
                _git("rebase", "--abort", check=False)
                raise


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
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  gałąź data: {changed} plików, {sha[:7]}")
    return sha


def publish_candles_d1(d1: dict[str, pd.DataFrame], tz: str, log=print, folder: str = "candles_d1", label: str = "D1",
                       meta: dict | None = None) -> str | None:
    """D-053: candles_d1/{PARA}.parquet (cała historia pary w jednym pliku, ok. 6 tys. świec) + candles_d1/manifest.json.
    Plik pary zapisywany tylko, gdy się zmienił (zwykle raz na dobę). Zwraca SHA lub None.
    D-063: ta sama funkcja publikuje kursy PLN (folder="candles_pln") — publish_candles_pln."""
    from .daily import day_of

    ensure_repo()
    mpath = DATA_REPO / folder / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {"files": {}}
    changed = 0
    for pair, df in d1.items():
        if df is None or df.empty:
            continue
        rel = f"{folder}/{pair}.parquet"
        part = df[["ts", "open", "high", "low", "close"]].reset_index(drop=True)
        h = frame_hash(part)
        if manifest["files"].get(rel, {}).get("hash") == h:
            continue
        path = DATA_REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        part.to_parquet(path, index=False)
        first, last = day_of([part.ts.iloc[0], part.ts.iloc[-1]], tz)
        manifest["files"][rel] = {"hash": h, "bars": len(part), "from": int(part.ts.iloc[0]), "to": int(part.ts.iloc[-1]),
                                  "first_day": str(first), "last_day": str(last)}
        changed += 1
    if not changed:
        log(f"  świece {label} na gałęzi data: bez zmian")
        return None
    manifest.update({"source": "yahoo", "interval": "1d", "tz": tz,
                     "ts": "czas otwarcia = północ dnia w strefie tz (D1, D-053)", **(meta or {})})
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    _git("add", "-A")
    _git("commit", "-q", "-m", f"dane: świece {label} ({changed})")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  świece {label}: {changed}, {sha[:7]}")
    return sha


def publish_candles_pln(pln: dict[str, pd.DataFrame], tz: str, log=print) -> str | None:
    """D-063: candles_pln/{WALUTA}.parquet + candles_pln/manifest.json — kursy złotówkowe D1 przyjętych walut (REV)."""
    from .rev_config import TICKER

    return publish_candles_d1(pln, tz, log=log, folder="candles_pln", label="PLN", meta={"series": "pln", "ticker": TICKER})


def publish_coverage(cov: dict, log=print) -> str | None:
    """coverage/coverage.json na gałęzi data (D-022): same liczniki i zakresy luk, bez cen.
    Push tylko, gdy treść (bez znacznika czasu) się zmieniła. Zwraca SHA lub None."""
    from .coverage import content_hash

    ensure_repo()
    path = DATA_REPO / "coverage" / "coverage.json"
    h = content_hash(cov)
    if path.exists():
        try:
            if content_hash(json.loads(path.read_text())) == h:
                log("  mapa pokrycia: bez zmian")
                return None
        except ValueError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cov, separators=(",", ":")))
    _git("add", "-A")
    _git("commit", "-q", "-m", f"dane: mapa pokrycia ({h})")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  mapa pokrycia: opublikowana, {sha[:7]}")
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
        "timeframe": m.get("timeframe", "H1"), "d1_background": bool(m.get("d1_background")),   # D-058
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
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  opublikowano results/{entry['id']} ({sha[:7]})")
    return sha


def publish_scan(folder: Path, run_id: str, log=print) -> str:
    """Wynik skanu (D-037) na gałąź data: scans/{run_id}/ (scan.md, scan.json, summary.csv, survivors.csv)."""
    import shutil

    ensure_repo()
    dst = DATA_REPO / "scans" / run_id
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(folder, dst)
    _git("add", "-A")
    _git("commit", "-q", "-m", f"skan hipotez {run_id}")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  opublikowano scans/{run_id} ({sha[:7]})")
    return sha


def publish_search(folder: Path, run_id: str, log=print) -> str:
    """Wynik poszukiwania (D-044) na gałąź data: searches/{run_id}/ — bez all_is.parquet (zostaje lokalnie)."""
    import shutil

    ensure_repo()
    dst = DATA_REPO / "searches" / run_id
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(folder, dst, ignore=shutil.ignore_patterns("all_is.parquet"))
    _git("add", "-A")
    _git("commit", "-q", "-m", f"poszukiwanie {run_id}")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  opublikowano searches/{run_id} ({sha[:7]})")
    return sha


def publish_investors(states: dict[str, dict], removed: list[str], log=print, extra: dict[str, str] | None = None) -> str | None:
    """D-045: investors/{id}/state.json + investors/index.json na gałęzi data. Inwestorzy spoza `states` i z `removed`
    znikają z gałęzi (historia gita zostaje). Push tylko, gdy treść (bez znacznika czasu liczenia) się zmieniła."""
    import shutil

    from .investors import content_hash, index_entry

    ensure_repo()
    root = DATA_REPO / "investors"
    root.mkdir(parents=True, exist_ok=True)
    changed = False
    for rel, text in (extra or {}).items():      # D-052: dziennik maili i znacznik przebiegu jadą tym samym commitem
        p = DATA_REPO / rel
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
            changed = True
    for iid, st in states.items():
        p = root / iid / "state.json"
        if p.exists():
            try:
                if content_hash(json.loads(p.read_text(encoding="utf-8"))) == content_hash(st):
                    continue
            except ValueError:
                pass
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        changed = True
    for d in root.iterdir():
        if d.is_dir() and (d.name in removed or d.name not in states):
            shutil.rmtree(d)
            changed = True
    if not changed:
        log("  inwestorzy: bez zmian")
        return None
    entries = []
    for d in sorted(root.iterdir()):
        if (d / "state.json").exists():
            entries.append(index_entry(json.loads((d / "state.json").read_text(encoding="utf-8"))))
    (root / "index.json").write_text(json.dumps({"investors": entries}, ensure_ascii=False, indent=1), encoding="utf-8")
    _git("add", "-A")
    _git("commit", "-q", "-m", f"inwestorzy: {len(entries)} (paper trading)")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  inwestorzy: opublikowani, {sha[:7]}")
    return sha


def publish_forest(folder: Path, log=print) -> str | None:
    """D-048: forest/ na gałęzi data (state.json, investors.json, report.md, journal/{RRRR-MM}.parquet). Tylko pliki, które się
    zmieniły; sam nowy czas liczenia nie jest zmianą. Zwraca SHA lub None."""
    import shutil

    ensure_repo()
    dst = DATA_REPO / "forest"
    (dst / "journal").mkdir(parents=True, exist_ok=True)

    def same_state(a: Path, b: Path) -> bool:
        if not b.exists():
            return False
        x, y = json.loads(a.read_text(encoding="utf-8")), json.loads(b.read_text(encoding="utf-8"))
        x.pop("computedAt", None)
        y.pop("computedAt", None)
        return x == y

    changed = 0
    for f in sorted(folder.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(folder)
        t = dst / rel
        same = same_state(f, t) if rel.name == "state.json" else t.exists() and t.read_bytes() == f.read_bytes()
        if not same:
            t.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, t)
            changed += 1
    for f in (dst / "journal").glob("*.parquet"):
        if not (folder / "journal" / f.name).exists():
            f.unlink()
            changed += 1
    if not changed:
        log("  FOREST: bez zmian")
        return None
    _git("add", "-A")
    _git("commit", "-q", "-m", f"FOREST: {changed} plików")
    _push()
    sha = _git("rev-parse", "HEAD")
    log(f"  FOREST: opublikowany, {sha[:7]}")
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
    _push()
    log(f"  usunięto results/{strategy_id}")
    return _git("rev-parse", "HEAD")


def purge_dukascopy_results(log=print) -> int:
    """D-039: usuwa z gałęzi data wyniki policzone na Dukascopy (results/{id}/ z manifestem data_source = dukascopy,
    wpisy w indeksie) i wszystkie skany (liczone na Dukascopy). Historia gita zostaje (G4). Zwraca liczbę wyników."""
    import shutil

    ensure_repo()
    gone = set()
    root = DATA_REPO / "results"
    for m in root.glob("*/manifest.json"):
        try:
            src = json.loads(m.read_text(encoding="utf-8")).get("data_source")
        except ValueError:
            continue
        if src == "dukascopy":
            gone.add(m.parent.name)
            shutil.rmtree(m.parent)
    before = _read_index()
    after = [e for e in before if e.get("source") != "dukascopy" and e["id"] not in gone]
    scans = DATA_REPO / "scans"
    had_scans = scans.exists()
    if had_scans:
        shutil.rmtree(scans)
    if not gone and len(after) == len(before) and not had_scans:
        return 0
    _write_index(after)
    _git("add", "-A")
    _git("commit", "-q", "-m", "D-039: usunięte wyniki i skany policzone na Dukascopy")
    _push()
    return len(gone | {e["id"] for e in before} - {e["id"] for e in after})
