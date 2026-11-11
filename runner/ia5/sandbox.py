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
TIMEFRAMES = ("H1", "D1")            # D-058: interwał strategii; D1 = świece dzienne Yahoo (cała historia)
H = 3600
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


def _as_levels(lv, df) -> np.ndarray:
    """D-057: levels(df, p, ind) → tablica (n, 2) cen TP i SL na świecy sygnału; NaN = brak poziomu."""
    if lv is None:
        return np.full((len(df), 2), np.nan)
    if not isinstance(lv, pd.DataFrame):
        raise StrategyError("levels() musi zwrócić DataFrame z kolumnami tp i/lub sl (ceny) na indeksie df")
    if len(lv) != len(df) or not lv.index.equals(df.index):
        raise StrategyError("levels() musi zwrócić DataFrame na tym samym indeksie co df")
    extra = set(lv.columns) - {"tp", "sl"}
    if extra or not (set(lv.columns) & {"tp", "sl"}):
        raise StrategyError("levels(): dozwolone kolumny to tp i sl (ceny); " + (f"nieznane: {sorted(extra)}" if extra else "brak obu"))
    out = np.full((len(df), 2), np.nan)
    for k, col in enumerate(("tp", "sl")):
        if col in lv:
            v = pd.to_numeric(lv[col], errors="coerce").to_numpy(float)
            if (v <= 0).any():
                raise StrategyError(f"levels(): kolumna {col} ma cenę ≤ 0")
            out[:, k] = v
    return out


def read_timeframe(ns: dict) -> str:
    tf = ns.get("TIMEFRAME", "H1")
    if tf not in TIMEFRAMES:
        raise StrategyError(f"TIMEFRAME: {TIMEFRAMES[0]} (domyślnie) albo {TIMEFRAMES[1]} — świece dzienne (D-058)")
    return tf


def read_settings(ns: dict) -> dict:
    """Ustawienia modułu strategii poza PARAMS/EXITS/SIZING (D-034): PYRAMID i HOURS; TIMEFRAME (D-058)."""
    out = {"timeframe": read_timeframe(ns)}
    if out["timeframe"] == "D1" and isinstance(ns.get("HOURS"), (list, tuple)):
        raise StrategyError("HOURS: na świecach dziennych nie ma okna godzin (wejście na open dnia = północ w Londynie, D-058)")
    pyr = ns.get("PYRAMID", 1)
    if not isinstance(pyr, int) or isinstance(pyr, bool) or not 1 <= pyr <= MAX_PYRAMID:
        raise StrategyError(f"PYRAMID musi być liczbą całkowitą 1–{MAX_PYRAMID}")
    out["pyramid"] = pyr
    if "MAX_PAIRS" in ns:   # D-050: najwyżej tyle par z otwartymi pozycjami naraz (cały portfel strategii)
        mp = ns["MAX_PAIRS"]
        if not isinstance(mp, int) or isinstance(mp, bool) or not 1 <= mp <= 8:
            raise StrategyError("MAX_PAIRS musi być liczbą całkowitą 1–8")
        out["max_pairs"] = mp
        rank = ns.get("PAIR_RANK", [])
        if not isinstance(rank, (list, tuple)) or not all(isinstance(x, str) for x in rank):
            raise StrategyError("PAIR_RANK: lista nazw par, np. [\"USDCHF\", \"AUDUSD\"] — kolejność przy równoczesnych sygnałach")
        out["pair_rank"] = [str(x) for x in rank]
    if out["timeframe"] == "D1":
        out["hours"] = False   # D-058: B11 nie dotyczy D1 — wejście na open dnia
    elif "HOURS" in ns:
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
            if ex.kind not in ("time", "atr", "rsi50", "sma", "opposite", "rsi_streak", "trail", "level"):
                raise StrategyError(f"EXITS: nieznany rodzaj wyjścia „{ex.kind}”")
            if ex.kind == "level" and "levels" not in ns:
                raise StrategyError("EXITS level: strategia musi mieć funkcję levels(df, p, ind) z kolumnami tp i/lub sl (D-057)")
            if ex.cap == 0:   # D-061: bez limitu czasu — wyjątek od B7 na wyraźne życzenie Michała, tylko poziomy ze strategii
                if ex.kind != "level":
                    raise StrategyError("EXITS: cap = 0 (bez limitu czasu, D-061) tylko dla wyjścia level z poziomem TP z levels()")
            elif not 1 <= ex.cap <= W_MAX:
                raise StrategyError(f"EXITS: limit czasu cap 1–{W_MAX} świec (B7); cap = 0 = bez limitu tylko dla level (D-061)")
            if ex.kind == "trail" and not (ex.sl > 0 and ex.trail > 0):
                raise StrategyError("EXITS trail: sl > 0 (stop początkowy) i trail > 0 (odległość stopu kroczącego)")
            if ex.kind == "rsi_streak" and not (ex.run >= 1 and 50 < ex.level < 100):
                raise StrategyError("EXITS rsi_streak: run ≥ 1 i level między 50 a 100 (np. 70)")
    if "levels" in ns and not callable(ns["levels"]):
        raise StrategyError("levels musi być funkcją levels(df, p, ind)")
    if "levels" in ns and not any(e.get("kind") == "level" for e in (ns.get("EXITS") or [])):
        raise StrategyError("Strategia ma levels(), ale żadne wyjście w EXITS nie jest rodzaju „level” — poziomy nie byłyby użyte")
    return out


def load_d1_background(d1_dir: Path | None, pair: str) -> pd.DataFrame | None:
    """D-058: świece dzienne pary do df.attrs["d1"] strategii H1 — indeks = czas otwarcia dnia (UTC), kolumny OHLC + close_ts
    (koniec dnia w UTC; od tej chwili świeca jest znana). Brak pliku = None (strategia dostaje df bez tła)."""
    if d1_dir is None:
        return None
    f = Path(d1_dir) / f"{pair}.parquet"
    if not f.exists():
        return None
    raw = pd.read_parquet(f)
    cols = ["open", "high", "low", "close", "close_ts"]
    if "close_ts" not in raw:
        raw = raw.assign(close_ts=raw["ts"].astype("int64") + 86400)
    d = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[cols]
    d.index.name = "ts"
    return d


def known_until(frame: pd.DataFrame) -> int:
    """Chwila, w której strategia liczy sygnał na ostatniej świecy ramki: jej zamknięcie (H1: open + 1 h)."""
    return int(frame.index[-1].timestamp()) + H


def fresh(frame: pd.DataFrame) -> pd.DataFrame:
    """Kopia ramki dla kodu strategii (nie zmieni oryginału) bez głębokiej kopii attrs — DataFrame.copy() kopiuje attrs
    rekurencyjnie, a tło D1 (D-058) ma tysiące wierszy; przy ~30 cięciach × 8 par to sekundy na każdy wariant."""
    f = pd.DataFrame(frame.to_numpy(copy=True), index=frame.index, columns=frame.columns)
    f.attrs = dict(frame.attrs)
    return f


def with_d1(frame: pd.DataFrame, d1: pd.DataFrame | None, factor: float | None = None, since: int | None = None) -> pd.DataFrame:
    """Ramka H1 z tłem D1 ograniczonym do dni zamkniętych przed jej końcem (look-ahead: dzień d widać dopiero po jego zamknięciu).
    factor/since: zaburzenie przyszłości — dni zamknięte po `since` dostają ceny × factor (test, że sygnały ich nie widzą)."""
    from . import indicators as ind

    if d1 is None:
        ind.attach_d1(frame, None)
        return frame
    cts = d1["close_ts"].to_numpy()
    d = d1.iloc[:int(np.searchsorted(cts, known_until(frame), side="right"))]   # close_ts rośnie — jedno cięcie
    if factor is not None and since is not None:
        fut = cts[:len(d)] > since
        if fut.any():
            vals = d.to_numpy(copy=True)
            cols = [d.columns.get_loc(c) for c in ("open", "high", "low", "close")]
            vals[np.ix_(fut, cols)] = vals[np.ix_(fut, cols)] * factor
            d = pd.DataFrame(vals, index=d.index, columns=d.columns)
    ind.attach_d1(frame, d)
    return frame


def _lv_equal(a: np.ndarray, b: np.ndarray) -> bool:
    return np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(np.nan_to_num(a), np.nan_to_num(b), rtol=0, atol=1e-12)


def lookahead_cuts(fn, df, p, ind, seed: int = 0, fn_lv=None, d1: pd.DataFrame | None = None) -> list[int]:
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

    def ev(frame, factor=None, since=None):
        """(sygnały, poziomy) na ramce; poziomy liczą się tylko tam, gdzie jest sygnał (D-057).
        Tło D1 (D-058) przycięte do dni zamkniętych przed końcem ramki — tak samo przy każdym cięciu."""
        frame = with_d1(frame, d1, factor, since)
        sg = _as_signal(fn(fresh(frame), p, ind), frame)
        if fn_lv is None:
            return sg, None
        lv = _as_levels(fn_lv(fresh(frame), p, ind), frame)
        lv[sg == 0] = np.nan
        return sg, lv

    def same(x, y, k):
        return np.array_equal(x[0][:k], y[0][:k]) and (x[1] is None or _lv_equal(x[1][:k], y[1][:k]))

    full = ev(df)
    for cut in sorted(rng.integers(WARMUP, n - 1, LOOKAHEAD_CUTS)):
        part = df.iloc[:cut].copy()
        if not same(ev(part), full, cut):
            bad.append(int(cut))
    if bad:
        return bad
    a = max(0, n // 2 - DENSE_BARS // 2)
    seg = df.iloc[a:a + DENSE_BARS]
    seg_full = ev(seg)
    lo = min(WARMUP * 2, len(seg) // 3)
    cols = ["open", "high", "low", "close"]
    for cut in np.unique(np.linspace(lo, len(seg) - 1, DENSE_CUTS).astype(int) + rng.integers(0, 4, DENSE_CUTS)):
        cut = int(min(cut, len(seg) - 1))
        part = seg.iloc[:cut].copy()
        if not same(ev(part), seg_full, cut):
            bad.append(a + cut)
            break
        # zaburzenie przyszłości: ceny po cięciu ×1,3 i ×0,7 — sygnały (i poziomy) sprzed cięcia nie mogą się zmienić
        up, dn = seg.copy(), seg.copy()
        up.iloc[cut:, up.columns.get_indexer(cols)] *= 1.3
        dn.iloc[cut:, dn.columns.get_indexer(cols)] *= 0.7
        since = known_until(part) if d1 is not None else None   # tło D1: dni zamknięte po cięciu też zaburzone
        if not same(ev(up, 1.3, since), ev(dn, 0.7, since), cut):
            bad.append(a + cut)
            break
    return bad


def worker_main(code_path: str, h1_dir: str, out_dir: str, param_ids: list[int] | None = None, d1_dir: str | None = None) -> None:
    """Uruchamiane w osobnym procesie. Zapisuje signals.parquet i meta.json w out_dir.
    param_ids: liczyć tylko te warianty parametrów (inwestorzy, D-045) — reszta pominięta, numeracja bez zmian.
    d1_dir (D-058): świece dzienne — dane strategii przy TIMEFRAME = "D1", tło (df.attrs["d1"]) przy H1."""
    from . import indicators as ind

    out = Path(out_dir)
    meta: dict = {"errors": [], "lookahead": [], "params": []}
    try:
        ns: dict = {"np": np, "pd": pd}
        exec(compile(Path(code_path).read_text(encoding="utf-8"), "strategia.py", "exec"), ns)  # noqa: S102
        fn = ns["signals"]
        fn_lv = ns.get("levels")   # D-057: opcjonalne poziomy TP/SL w cenie na świecy sygnału
        params = param_grid(ns.get("PARAMS"))
        meta["params"] = params
        meta["hypothesis"] = ns.get("HYPOTHESIS")
        meta["sizing"] = ns.get("SIZING")
        meta["exits"] = ns.get("EXITS")
        meta.update(read_settings(ns))
        tf = meta["timeframe"]
        data_dir = Path(d1_dir) if tf == "D1" and d1_dir else Path(h1_dir)
        if tf == "D1" and (not d1_dir or not any(data_dir.glob("*.parquet"))):
            raise StrategyError("TIMEFRAME = \"D1\": brak świec dziennych do liczenia — na Macu uruchom ia5 start "
                                "(po backfillD1 w Apps Script)")
        rows = []
        for f in sorted(data_dir.glob("*.parquet")):
            pair = f.stem
            raw = pd.read_parquet(f)
            df = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]
            df.attrs["pair"] = pair   # D-037: strategia może zależeć od pary (df.attrs["pair"], np. "EURUSD")
            df.attrs["timeframe"] = tf
            d1 = load_d1_background(d1_dir, pair) if tf == "H1" else None   # D-058: tło D1 dla strategii H1
            for pid, p in enumerate(params):
                if param_ids is not None and pid not in param_ids:
                    continue
                bad = lookahead_cuts(fn, df, p, ind, fn_lv=fn_lv, d1=d1)
                if bad:
                    meta["lookahead"].append({"pair": pair, "param_id": pid, "cuts": [int(raw.ts.iloc[c]) for c in bad]})
                    continue
                full = with_d1(fresh(df), d1)
                s = _as_signal(fn(fresh(full), p, ind), full)
                nz = np.flatnonzero(s)
                lv = _as_levels(fn_lv(fresh(full), p, ind), full) if fn_lv is not None else np.full((len(df), 2), np.nan)
                rows.append(pd.DataFrame({"param_id": pid, "pair": pair, "i": nz, "sig": s[nz], "tp": lv[nz, 0], "sl": lv[nz, 1]}))
        sig = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["param_id", "pair", "i", "sig", "tp", "sl"])
        meta["levels"] = fn_lv is not None
        meta["d1_background"] = tf == "H1" and bool(d1_dir) and any(Path(d1_dir).glob("*.parquet"))
        sig.to_parquet(out / "signals.parquet", index=False)
    except Exception as e:  # noqa: BLE001 — każdy błąd strategii trafia do raportu
        meta["errors"].append(f"{type(e).__name__}: {e}")
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, default=str))


def probe_main(code_path: str, h1_dir: str, out_dir: str, param_id: int, moves: list[float], d1_dir: str | None = None) -> None:
    """D-051: sygnał na ostatniej świecy po dopisaniu hipotetycznej świecy (open = ostatnie zamknięcie, close = open + k × ATR14).
    Świeca istnieje tylko w pamięci tego procesu — nie trafia do danych, nie ma wpływu na wyniki (D2)."""
    from . import indicators as ind

    out: dict = {"errors": [], "hits": []}
    try:
        ns: dict = {"np": np, "pd": pd}
        exec(compile(Path(code_path).read_text(encoding="utf-8"), "strategia.py", "exec"), ns)  # noqa: S102
        p = param_grid(ns.get("PARAMS"))[param_id]
        for f in sorted(Path(h1_dir).glob("*.parquet")):
            raw = pd.read_parquet(f)[["ts", "open", "high", "low", "close"]]
            df = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]
            atr = float(ind.atr(df, 14).iloc[-1])
            if not atr > 0:
                continue
            o = float(df["close"].iloc[-1])
            when = df.index[-1] + pd.Timedelta(hours=1)
            for k in moves:
                c = o + k * atr
                x = pd.concat([df, pd.DataFrame({"open": [o], "high": [max(o, c)], "low": [min(o, c)], "close": [c]}, index=[when])])
                x.attrs["pair"] = f.stem
                x.attrs["timeframe"] = "H1"
                x = with_d1(x, load_d1_background(d1_dir, f.stem))   # D-058: tło D1 jak przy liczeniu
                v = float(_as_signal(ns["signals"](x, p, ind), x)[-1])
                if v:
                    out["hits"].append({"pair": f.stem, "k": k, "level": c, "dir": int(np.sign(v))})
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"{type(e).__name__}: {e}")
    (Path(out_dir) / "probe.json").write_text(json.dumps(out))


def run_probe(code: str, h1_dir: Path, param_id: int, moves: list[float], timeout: int = 300,
              d1_dir: Path | None = None) -> list[dict]:
    """Uruchamia probe_main w tym samym odgrodzeniu co strategie (S2)."""
    errs = check_code(code)
    if errs:
        raise StrategyError("; ".join(errs))
    pkg_parent = str(Path(__file__).resolve().parent.parent)
    with tempfile.TemporaryDirectory(prefix="ia5-") as tmp:
        code_path = Path(tmp) / "strategia.py"
        code_path.write_text(code, encoding="utf-8")
        boot = (f"import sys; sys.path.insert(0, {pkg_parent!r}); from ia5.sandbox import probe_main; "
                f"probe_main({str(code_path)!r}, {str(h1_dir)!r}, {tmp!r}, {int(param_id)}, {[float(x) for x in moves]!r}, "
                f"{str(d1_dir) if d1_dir else None!r})")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": tmp, "TMPDIR": tmp, "PYTHONHASHSEED": "0"}
        try:
            r = subprocess.run([sys.executable, "-I", "-c", boot], env=env, cwd=tmp, timeout=timeout,
                               capture_output=True, text=True, check=False,
                               preexec_fn=_limit_memory if sys.platform.startswith("linux") else None)
        except subprocess.TimeoutExpired as e:
            raise StrategyError(f"Przekroczony limit czasu ({timeout} s)") from e
        p = Path(tmp) / "probe.json"
        if not p.exists():
            raise StrategyError(f"Proces przerwany ({exit_reason(r.returncode)})")
        out = json.loads(p.read_text(encoding="utf-8"))
    if out["errors"]:
        raise StrategyError("; ".join(out["errors"]))
    return out["hits"]


def _limit_memory():  # pragma: no cover — zależne od systemu
    try:
        import resource

        lim = 6 * 1024**3
        resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
    except Exception:  # noqa: BLE001 — macOS/Windows: brak twardego limitu
        pass


def exit_reason(code: int | None) -> str:
    """Czytelny powód końca procesu strategii (D-047) — „przerwany” bez komunikatu to zwykle sygnał systemu."""
    names = {-9: "zabity przez system — zwykle brak pamięci albo zamknięcie programu",
             -2: "przerwany Ctrl+C — np. restart ia5 start w trakcie liczenia",
             -15: "zakończony z zewnątrz (SIGTERM)", -11: "błąd pamięci procesu (SIGSEGV)"}
    if code is None:
        return "kod wyjścia nieznany"
    return f"kod wyjścia {code}: {names.get(code, 'błąd procesu')}"


def run_strategy_code(code: str, h1_dir: Path, timeout: int = 1800,
                      param_ids: list[int] | None = None, d1_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    """Sprawdza kontrakt, uruchamia kod w osobnym procesie, zwraca (sygnały, meta).
    param_ids: tylko wybrane warianty parametrów (np. wariant przypisany inwestorowi).
    d1_dir (D-058): katalog świec dziennych do liczenia (data/d1_ready) — dane dla TIMEFRAME = "D1", tło dla H1."""
    errs = check_code(code)
    if errs:
        raise StrategyError("; ".join(errs))
    pkg_parent = str(Path(__file__).resolve().parent.parent)
    with tempfile.TemporaryDirectory(prefix="ia5-") as tmp:
        code_path = Path(tmp) / "strategia.py"
        code_path.write_text(code, encoding="utf-8")
        boot = (f"import sys; sys.path.insert(0, {pkg_parent!r}); "
                f"from ia5.sandbox import worker_main; worker_main({str(code_path)!r}, {str(h1_dir)!r}, {tmp!r}, "
                f"{[int(x) for x in param_ids] if param_ids is not None else None!r}, {str(d1_dir) if d1_dir else None!r})")
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
            raise StrategyError(f"Proces strategii przerwany ({exit_reason(r.returncode)}): {r.stderr.strip()[-500:] or 'bez komunikatu'}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta["errors"]:
            raise StrategyError("; ".join(meta["errors"]))
        sig = pd.read_parquet(Path(tmp) / "signals.parquet")
    return sig, meta
