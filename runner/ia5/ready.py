"""Dane do liczenia (D8, D-039): świece Yahoo H1 po warstwie czyszczenia (clean.py).

Wynik: data/h1_ready/{PARA}.parquet (+ {PARA}.json z opisem) — jedyne wejście silnika, sandboxa i skanera.
Przebudowa pary tylko wtedy, gdy zmieniły się jej świece albo wersja czyszczenia (podpis w {PARA}.json).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from .clean import CLEAN_VERSION, COLS, clean_h1
from .config import COMPUTE_PAIRS

SOURCE = "yahoo"
MIN_BARS = 24 * 20   # para z mniej niż ~4 tygodniami świec nie trafia do liczenia (za mało na wskaźniki i OOS)


def signature(df: pd.DataFrame | None) -> str:
    h = hashlib.sha256(f"{SOURCE}:{CLEAN_VERSION}:{MIN_BARS}".encode())
    if df is not None and len(df):
        h.update(pd.util.hash_pandas_object(df[COLS].reset_index(drop=True), index=False).values.tobytes())
    return h.hexdigest()[:16]


def build(yahoo: dict[str, pd.DataFrame], out_dir: Path, pairs=COMPUTE_PAIRS, log=print) -> dict:
    """Przebudowuje świece do liczenia; pliki par spoza `pairs` usuwa z out_dir (to kopia pochodna, nie dane)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.json")) + list(out_dir.glob("*.tmp")):
        if f.stem not in pairs or f.suffix == ".tmp":
            f.unlink()
    frames = {p: df for p, df in yahoo.items() if df is not None and len(df)}
    out = {}
    for pair in pairs:
        jf, pf = out_dir / f"{pair}.json", out_dir / f"{pair}.parquet"
        try:
            old = json.loads(jf.read_text())
        except (FileNotFoundError, ValueError):
            old = {}
        raw = frames.get(pair)
        sig = signature(raw)
        if old.get("sig") == sig and old.get("source") == SOURCE and (pf.exists() or not old.get("bars")):
            out[pair] = {**old, "rebuilt": False}
            continue
        if raw is None or len(raw) < MIN_BARS:
            pf.unlink(missing_ok=True)
            info = {"version": CLEAN_VERSION, "source": SOURCE, "sig": sig, "bars": 0, "raw_bars": 0 if raw is None else len(raw)}
            jf.write_text(json.dumps(info))
            out[pair] = {**info, "rebuilt": True}
            log(f"  {pair}: za mało świec Yahoo ({info['raw_bars']}) — para pominięta w liczeniu")
            continue
        df, info = clean_h1(raw)
        tmp = pf.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(pf)
        info = {**info, "source": SOURCE, "sig": sig, "raw_bars": len(raw), "gaps_n": len(info["gaps"]),
                "gaps": info["gaps"][-200:], "at": int(time.time())}
        jf.write_text(json.dumps(info))
        out[pair] = {**info, "rebuilt": True}
        log(f"  {pair} do liczenia: {info['bars']:,} świec · odrzucone {info['rejected']} (D5) + {info['off_session']} poza sesją · "
            f"uzupełnione {info['filled']} (≤ 3 h) · "
            f"przerwy w danych {info['gaps_n']} ({info['gap_hours']} h) · granica tygodnia {info['closed_hours']} h")
    return out


MIN_BARS_D1 = 260   # D-058: para z mniej niż ~rokiem świec dziennych nie trafia do liczenia na D1


def _build_daily(raw_map: dict[str, pd.DataFrame], out_dir: Path, tz: str, names, clean_fn, version: str, min_bars: int,
                 tag: str, meta: dict, describe, log=print) -> dict:
    """Wspólna przebudowa serii dziennych (D1 FX, kursy PLN): plik pochodny tylko, gdy zmieniły się surowe świece, wersja
    czyszczenia albo strefa (podpis w {NAZWA}.json); pliki nazw spoza `names` znikają (to kopia pochodna, nie dane)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.json")) + list(out_dir.glob("*.tmp")):
        if f.stem not in names or f.suffix == ".tmp":
            f.unlink()
    out = {}
    for name in names:
        jf, pf = out_dir / f"{name}.json", out_dir / f"{name}.parquet"
        try:
            old = json.loads(jf.read_text())
        except (FileNotFoundError, ValueError):
            old = {}
        raw = raw_map.get(name)
        raw = raw if raw is not None and len(raw) else None
        h = hashlib.sha256(f"{SOURCE}:{tag}:{version}:{min_bars}:{tz}".encode())
        if raw is not None:
            h.update(pd.util.hash_pandas_object(raw[COLS].reset_index(drop=True), index=False).values.tobytes())
        sig = h.hexdigest()[:16]
        if old.get("sig") == sig and old.get("source") == SOURCE and (pf.exists() or not old.get("bars")):
            out[name] = {**old, "rebuilt": False}
            continue
        if raw is None or len(raw) < min_bars:
            pf.unlink(missing_ok=True)
            info = {"version": version, "source": SOURCE, **meta, "sig": sig, "bars": 0, "raw_bars": 0 if raw is None else len(raw)}
            jf.write_text(json.dumps(info))
            out[name] = {**info, "rebuilt": True}
            log(f"  {tag} {name}: za mało świec dziennych ({info['raw_bars']}) — pominięte w liczeniu")
            continue
        df, info = clean_fn(raw, tz)
        tmp = pf.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(pf)
        info = {**info, "source": SOURCE, **meta, "sig": sig, "raw_bars": len(raw), "at": int(time.time())}
        if "gaps" in info:
            info.update({"gaps_n": len(info["gaps"]), "gaps": info["gaps"][-200:]})
        jf.write_text(json.dumps(info))
        out[name] = {**info, "rebuilt": True}
        log(describe(name, info))
    return out


def build_d1(d1: dict[str, pd.DataFrame], out_dir: Path, tz: str | None = None, pairs=COMPUTE_PAIRS, log=print) -> dict:
    """D-058: świece dzienne do liczenia (data/d1_ready/) — jak build(), ale warstwa czyszczenia D1 (daily.clean_d1).
    Pliki {PARA}.json mają "source": "yahoo" i "timeframe": "D1"."""
    from .daily import CLEAN_D1_VERSION, D1_TZ, clean_d1

    def describe(pair, info):
        return (f"  D1 {pair} do liczenia: {info['bars']:,} dni · odrzucone {info['rejected']} (D5) + {info['off_session']} "
                f"weekend/święto + {info['flat']} płaskie · brakujące dni {info['missing_days']} · przerwy {info['gaps_n']} "
                f"({info['gap_days']} dni)")

    return _build_daily(d1, out_dir, tz or D1_TZ, pairs, clean_d1, CLEAN_D1_VERSION, MIN_BARS_D1, "D1", {"timeframe": "D1"},
                        describe, log)


MIN_BARS_PLN = 260   # D-063: waluta z mniej niż ~rokiem kursów nie trafia do REV


def build_pln(pln: dict[str, pd.DataFrame], out_dir: Path, tz: str | None = None, log=print) -> dict:
    """D-063: kursy złotówkowe do liczenia REV (data/pln_ready/{WALUTA}.parquet + .json) — warstwa tylko zamknięć
    (rev_data.clean_pln). Waluty spoza `pln` znikają z katalogu."""
    from .daily import D1_TZ
    from .rev_config import CLEAN_PLN_VERSION
    from .rev_data import clean_pln

    def describe(c, info):
        return (f"  PLN {c} do liczenia: {info['bars']:,} dni · poza sesją {info['offday']} · odrzucone {info['rejected']} · "
                f"powtórzone {info['repeated']} · wyskoki {info['spikes']} · przeskalowania {len(info['rescaled'])}")

    return _build_daily(pln, out_dir, tz or D1_TZ, sorted(pln), clean_pln, CLEAN_PLN_VERSION, MIN_BARS_PLN, "PLN",
                        {"timeframe": "D1", "series": "pln"}, describe, log)


def load_pln(folder: Path) -> dict[str, pd.DataFrame]:
    """Kursy PLN po czyszczeniu; info z {WALUTA}.json w df.attrs["info"] (np. przeskalowania dla portfela na żywo)."""
    out = {}
    for pf in sorted(Path(folder).glob("*.parquet")):
        df = pd.read_parquet(pf)
        try:
            df.attrs["info"] = json.loads(pf.with_suffix(".json").read_text())
        except (FileNotFoundError, ValueError):
            df.attrs["info"] = {}
        out[pf.stem] = df
    return out


def load(folder: Path, pairs=COMPUTE_PAIRS) -> dict[str, pd.DataFrame]:
    return {p: pd.read_parquet(folder / f"{p}.parquet") for p in pairs if (folder / f"{p}.parquet").exists()}
