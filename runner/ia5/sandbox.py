"""Uruchamianie kodu strategii (S2, B2, kontrakt z CLAUDE.md sekcja 7).

Kod strategii działa w osobnym procesie Pythona: izolowany tryb (-I), czyste zmienne środowiskowe
(bez kluczy), limit czasu, limit pamięci tam, gdzie system go wspiera. Sprawdzenie importów to
zabezpieczenie przed pomyłką, nie granica bezpieczeństwa — tą jest logowanie i reguły Firestore (S1).
"""
from __future__ import annotations

import ast
import itertools
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ALLOWED_IMPORTS = {"numpy", "pandas", "math"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "vars"}
LOOKAHEAD_CUTS = 8
WARMUP = 300


class StrategyError(Exception):
    pass


def check_code(code: str) -> list[str]:
    """Błędy kontraktu wykryte bez uruchamiania kodu."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Błąd składni w linii {e.lineno}: {e.msg}"]
    errs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [(node.module or "").split(".")[0]]
        else:
            mods = []
        for m in mods:
            if m not in ALLOWED_IMPORTS:
                errs.append(f"Niedozwolony import „{m}” (dozwolone: {', '.join(sorted(ALLOWED_IMPORTS))})")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            errs.append(f"Niedozwolona funkcja „{node.id}” (linia {node.lineno})")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            errs.append(f"Niedozwolony dostęp do „{node.attr}” (linia {node.lineno})")
    if not any(isinstance(n, ast.FunctionDef) and n.name == "signals" for n in tree.body):
        errs.append("Brak funkcji signals(df, p, ind)")
    return errs


def param_grid(params: dict | None) -> list[dict]:
    if not params:
        return [{}]
    keys = list(params)
    vals = [v if isinstance(v, (list, tuple)) else [v] for v in params.values()]
    return [dict(zip(keys, combo)) for combo in itertools.product(*vals)]


def _as_signal(s, df) -> np.ndarray:
    if isinstance(s, pd.Series):
        if len(s) != len(df) or not s.index.equals(df.index):
            raise StrategyError("signals() musi zwrócić Series na tym samym indeksie co df")
        v = s.to_numpy()
    else:
        v = np.asarray(s)
        if len(v) != len(df):
            raise StrategyError("signals() zwróciło inną liczbę wartości niż świec")
    v = np.nan_to_num(v.astype(float))
    if not np.isin(v, (-1, 0, 1)).all():
        raise StrategyError("Sygnał może mieć tylko wartości −1, 0, +1")
    return v.astype(np.int8)


def lookahead_cuts(fn, df, p, ind, seed: int = 0) -> list[int]:
    """B2: sygnały na danych obciętych w losowych punktach muszą równać się sygnałom z pełnych danych.

    Zwraca listę punktów cięcia (pozycji), w których wynik się różni — pusta lista = brak look-ahead.
    """
    n = len(df)
    if n < WARMUP + 10:
        return []
    full = _as_signal(fn(df.copy(), p, ind), df)
    rng = np.random.default_rng(seed)
    bad = []
    for cut in sorted(rng.integers(WARMUP, n - 1, LOOKAHEAD_CUTS)):
        part = df.iloc[:cut].copy()
        s = _as_signal(fn(part, p, ind), part)
        if not np.array_equal(s, full[:cut]):
            bad.append(int(cut))
    return bad


def worker_main(code_path: str, h1_dir: str, out_dir: str) -> None:
    """Uruchamiane w osobnym procesie. Zapisuje signals.parquet i meta.json w out_dir."""
    from . import indicators as ind

    out = Path(out_dir)
    meta: dict = {"errors": [], "lookahead": [], "params": []}
    try:
        ns: dict = {"np": np, "pd": pd}
        exec(compile(Path(code_path).read_text(encoding="utf-8"), "strategia.py", "exec"), ns)  # noqa: S102
        fn = ns["signals"]
        params = param_grid(ns.get("PARAMS"))
        meta["params"] = params
        meta["hypothesis"] = ns.get("HYPOTHESIS")
        meta["sizing"] = ns.get("SIZING")
        meta["exits"] = ns.get("EXITS")
        rows = []
        for f in sorted(Path(h1_dir).glob("*.parquet")):
            pair = f.stem
            raw = pd.read_parquet(f)
            df = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]
            for pid, p in enumerate(params):
                bad = lookahead_cuts(fn, df, p, ind)
                if bad:
                    meta["lookahead"].append({"pair": pair, "param_id": pid, "cuts": [int(raw.ts.iloc[c]) for c in bad]})
                    continue
                s = _as_signal(fn(df.copy(), p, ind), df)
                nz = np.flatnonzero(s)
                rows.append(pd.DataFrame({"param_id": pid, "pair": pair, "i": nz, "sig": s[nz]}))
        sig = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["param_id", "pair", "i", "sig"])
        sig.to_parquet(out / "signals.parquet", index=False)
    except Exception as e:  # noqa: BLE001 — każdy błąd strategii trafia do raportu
        meta["errors"].append(f"{type(e).__name__}: {e}")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, default=str))


def _limit_memory():  # pragma: no cover — zależne od systemu
    try:
        import resource

        lim = 6 * 1024**3
        resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
    except Exception:  # noqa: BLE001 — macOS/Windows: brak twardego limitu
        pass


def run_strategy_code(code: str, h1_dir: Path, timeout: int = 1800) -> tuple[pd.DataFrame, dict]:
    """Sprawdza kontrakt, uruchamia kod w osobnym procesie, zwraca (sygnały, meta)."""
    errs = check_code(code)
    if errs:
        raise StrategyError("; ".join(errs))
    pkg_parent = str(Path(__file__).resolve().parent.parent)
    with tempfile.TemporaryDirectory(prefix="ia5-") as tmp:
        code_path = Path(tmp) / "strategia.py"
        code_path.write_text(code, encoding="utf-8")
        boot = (f"import sys; sys.path.insert(0, {pkg_parent!r}); "
                f"from ia5.sandbox import worker_main; worker_main({str(code_path)!r}, {str(h1_dir)!r}, {tmp!r})")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "TMPDIR": tmp, "PYTHONHASHSEED": "0"}
        if sys.platform == "win32":
            env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
        try:
            r = subprocess.run([sys.executable, "-I", "-c", boot], env=env, cwd=tmp, timeout=timeout,
                               capture_output=True, text=True, check=False,
                               preexec_fn=_limit_memory if sys.platform.startswith("linux") else None)
        except subprocess.TimeoutExpired as e:
            raise StrategyError(f"Przekroczony limit czasu ({timeout} s)") from e
        meta_path = Path(tmp) / "meta.json"
        if not meta_path.exists():
            raise StrategyError(f"Proces strategii przerwany: {r.stderr.strip()[-500:]}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["errors"]:
            raise StrategyError("; ".join(meta["errors"]))
        sig = pd.read_parquet(Path(tmp) / "signals.parquet")
    return sig, meta
