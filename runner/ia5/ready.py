"""Dane do liczenia (D-031): H1 tylko z zatwierdzonych miesięcy M1, po warstwie czyszczenia (clean.py).

Wynik: data/h1_ready/{PARA}.parquet (+ {PARA}.json z opisem) — jedyne wejście silnika i sandboxa.
Przebudowa tylko wtedy, gdy zmienił się zestaw zatwierdzonych miesięcy albo ich pliki (podpis w {PARA}.json).
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from . import dukascopy
from .bars import m1_to_h1
from .clean import CLEAN_VERSION, clean_h1
from .config import COMPUTE_PAIRS


def signature(root: Path, pair: str, months: list[str]) -> str:
    h = hashlib.sha256(CLEAN_VERSION.encode())
    for k in months:
        f = root / "m1" / pair / f"{k}.parquet"
        st = f.stat()
        h.update(f"{k}:{st.st_size}:{st.st_mtime_ns};".encode())
        mp = dukascopy.missing_path(f)
        if mp.exists():  # dni uznane za niedostępne też zmieniają dane
            h.update(mp.read_bytes())
    return h.hexdigest()[:16]


def build(root: Path, out_dir: Path, pairs=COMPUTE_PAIRS, until: date | None = None, log=print) -> dict:
    """Przebudowuje świece do liczenia dla `pairs`; pliki innych par usuwa z out_dir (to kopia pochodna, nie dane)."""
    until = until or datetime.now(UTC).date() - timedelta(days=1)
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in list(out_dir.glob("*.parquet")) + list(out_dir.glob("*.json")):
        if f.stem not in pairs:
            f.unlink()
    out = {}
    for pair in pairs:
        st = dukascopy.pair_status(root, pair, until)
        sig = signature(root, pair, st["ready"])
        jf, pf = out_dir / f"{pair}.json", out_dir / f"{pair}.parquet"
        try:
            old = json.loads(jf.read_text())
        except (FileNotFoundError, ValueError):
            old = {}
        if old.get("sig") == sig and pf.exists():
            out[pair] = {**old, "rebuilt": False}
            continue
        if not st["ready"]:
            pf.unlink(missing_ok=True)
            info = {"version": CLEAN_VERSION, "sig": sig, "months": 0, "months_total": st["months"], "bars": 0}
            jf.write_text(json.dumps(info))
            out[pair] = {**info, "rebuilt": True}
            log(f"  {pair}: brak zatwierdzonych miesięcy — nie liczymy jeszcze tej pary")
            continue
        t0 = time.time()
        raw = m1_to_h1(dukascopy.load_m1(pair, root, months=st["ready"]))
        df, info = clean_h1(raw)
        tmp = pf.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(pf)
        info = {**info, "sig": sig, "months": len(st["ready"]), "months_total": st["months"],
                "given_up_days": st["given_up"], "gaps_n": len(info["gaps"]),
                "gaps": info["gaps"][-200:], "at": int(time.time())}
        jf.write_text(json.dumps(info))
        out[pair] = {**info, "rebuilt": True}
        log(f"  {pair} do liczenia: {info['bars']:,} świec z {info['months']}/{info['months_total']} zatwierdzonych mies.; "
            f"uzupełnione {info['filled']} (≤ 3 h), długie luki {info['gaps_n']} ({info['gap_hours']} h) "
            f"— {time.time() - t0:.0f} s")
    return out
