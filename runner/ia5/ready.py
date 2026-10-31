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


def load(folder: Path, pairs=COMPUTE_PAIRS) -> dict[str, pd.DataFrame]:
    return {p: pd.read_parquet(folder / f"{p}.parquet") for p in pairs if (folder / f"{p}.parquet").exists()}
