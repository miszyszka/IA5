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
DENSE_CUTS = 24
DENSE_BARS = 2000
WARMUP = 300
MIN_WEIGHT, MAX_WEIGHT = 0.1, 10.0   # D-034: |sygnał| = waga pozycji
MAX_PYRAMID = 10
W_MAX = 480   # D-035: do 20 dni handlu — strategie trendowe trzymają pozycje tygodniami


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
    a = np.abs(v)
    if ((a > 0) & (a < MIN_WEIGHT) | (a > MAX_WEIGHT)).any():
        raise StrategyError(f"Sygnał: 0 albo ±waga, waga od {MIN_WEIGHT:g} do {MAX_WEIGHT:g} (+1 / −1 = zwykła pozycja)")
    return v.astype(np.float32)


def read_settings(ns: dict) -> dict:
    """Ustawienia modułu strategii poza PARAMS/EXITS/SIZING (D-034): PYRAMID i HOURS."""
    out = {}
    pyr = ns.get("PYRAMID", 1)
    if not isinstance(pyr, int) or isinstance(pyr, bool) or not 1 <= pyr <= MAX_PYRAMID:
        raise StrategyError(f"PYRAMID musi być liczbą całkowitą 1–{MAX_PYRAMID}")
    out["pyramid"] = pyr
    if "HOURS" in ns:
        h = ns["HOURS"]
        if h is False or h is None:
            out["hours"] = False
        elif isinstance(h, (list, tuple)) and len(h) == 2 and all(isinstance(x, int) and 0 <= x <= 24 for x in h) and h[0] < h[1]:
            out["hours"] = [int(h[0]), int(h[1])]
        else:
            raise StrategyError("HOURS: False (bez okna) albo (od, do) w godzinach czasu polskiego, np. (7, 17)")
    if ns.get("EXITS"):
        from .engine import Exit

        for e in ns["EXITS"]:
            try:
                ex = Exit(**e)
            except TypeError as err:
                raise StrategyError(f"EXITS: {e} — {err}") from err
            if ex.kind not in ("time", "atr", "rsi50", "sma", "opposite", "rsi_streak", "trail"):
                raise StrategyError(f"EXITS: nieznany rodzaj wyjścia „{ex.kind}”")
            if not 1 <= ex.cap <= W_MAX:
                raise StrategyError(f"EXITS: limit czasu cap 1–{W_MAX} świec (B7)")
            if ex.kind == "trail" and not (ex.sl > 0 and ex.trail > 0):
                raise StrategyError("EXITS trail: sl > 0 (stop początkowy) i trail > 0 (odległość stopu kroczącego)")
            if ex.kind == "rsi_streak" and not (ex.run >= 1 and 50 < ex.level < 100):
                raise StrategyError("EXITS rsi_streak: run ≥ 1 i level między 50 a 100 (np. 70)")
    return out


def lookahead_cuts(fn, df, p, ind, seed: int = 0) -> list[int]:
    """B2: sygnały na danych obciętych w punkcie c muszą równać się sygnałom z pełnych danych (do c).

    Dwa przebiegi:
    - LOOKAHEAD_CUTS losowych cięć na pełnych danych — łapie statystyki z całej serii (mean(), max()…);
    - DENSE_CUTS gęstych cięć na wycinku DENSE_BARS świec — łapie „krótki” look-ahead (niezamknięta świeca
      wyższego interwału, maksimum dnia z przyszłych godzin), który zmienia tylko kilka świec przed cięciem.
    Zwraca pozycje cięć z różnicą (względem pełnych danych) — pusta lista = brak look-ahead.
    """
    n = len(df)
    if n < WARMUP + 10:
        return []
    rng = np.random.default_rng(seed)
    bad = []
    full = _as_signal(fn(df.copy(), p, ind), df)
    for cut in sorted(rng.integers(WARMUP, n - 1, LOOKAHEAD_CUTS)):
        part = df.iloc[:cut].copy()
        if not np.array_equal(_as_signal(fn(part, p, ind), part), full[:cut]):
            bad.append(int(cut))
    if bad:
        return bad
    a = max(0, n // 2 - DENSE_BARS // 2)
    seg = df.iloc[a:a + DENSE_BARS]
    seg_full = _as_signal(fn(seg.copy(), p, ind), seg)
    lo = min(WARMUP * 2, len(seg) // 3)
    cols = ["open", "high", "low", "close"]
    for cut in np.unique(np.linspace(lo, len(seg) - 1, DENSE_CUTS).astype(int) + rng.integers(0, 4, DENSE_CUTS)):
        cut = int(min(cut, len(seg) - 1))
        part = seg.iloc[:cut].copy()
        if not np.array_equal(_as_signal(fn(part, p, ind), part), seg_full[:cut]):
            bad.append(a + cut)
            break
        # zaburzenie przyszłości: ceny po cięciu ×1,3 i ×0,7 — sygnały sprzed cięcia nie mogą się zmienić
        up, dn = seg.copy(), seg.copy()
        up.iloc[cut:, up.columns.get_indexer(cols)] *= 1.3
        dn.iloc[cut:, dn.columns.get_indexer(cols)] *= 0.7
        if not np.array_equal(_as_signal(fn(up, p, ind), up)[:cut], _as_signal(fn(dn, p, ind), dn)[:cut]):
            bad.append(a + cut)
            break
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
        meta.update(read_settings(ns))
        rows = []
        for f in sorted(Path(h1_dir).glob("*.parquet")):
            pair = f.stem
            raw = pd.read_parquet(f)
            df = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]
            df.attrs["pair"] = pair   # D-037: strategia może zależeć od pary (df.attrs["pair"], np. "EURUSD")
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
