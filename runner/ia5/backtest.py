"""Pełne liczenie strategii: kod → sygnały (sandbox) → silnik → pliki wyników + raport (sekcja 4)."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from .engine import Exit, default_exits, m1_resolver_lazy, run, summarize
from .report import write_report
from .sandbox import run_strategy_code

MIN_TRADES = 30  # wariant z mniejszą liczbą transakcji IS nie trafia na szczyt rankingu


def data_hash(h1_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(h1_dir.glob("*.parquet")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def exits_from(meta_exits) -> list[Exit]:
    if not meta_exits:
        return default_exits()
    return [Exit(**e) for e in meta_exits]


def variant_table(res: dict) -> pd.DataFrame:
    """Metryki per wariant: całość, IS, OOS (W1: ranking tylko po IS)."""
    o = res["outcomes"]
    v = res["variants"].copy()
    if o.empty:
        return v
    for name, part in (("all", o), ("is", o[o["sample"] == "IS"]), ("oos", o[o["sample"] == "OOS"])):
        s = summarize(part).set_index("variant_id").add_prefix(f"{name}_")
        v = v.join(s, on="variant_id")
    ok = v["is_trades"].fillna(0) >= MIN_TRADES
    v["rank_is"] = v["is_exp_r"].where(ok).rank(ascending=False, method="first")
    return v.sort_values("rank_is", na_position="last").reset_index(drop=True)


def run_file(code: str, name: str, h1_dir: Path, out_root: Path, m1_dir: Path | None = None,
             log=print) -> Path:
    t_start = time.time()
    log("Sygnały (osobny proces, detektor look-ahead)…")
    sig, meta = run_strategy_code(code, h1_dir)
    if meta["lookahead"]:
        bad = meta["lookahead"][0]
        raise SystemExit(f"Błąd: look-ahead (B2) — {bad['pair']}, wariant parametrów {bad['param_id']}: "
                         "sygnały zmieniają się po dopisaniu przyszłych świec.")
    h1 = {f.stem: pd.read_parquet(f) for f in sorted(h1_dir.glob("*.parquet"))}
    signals = {}
    for pid in range(len(meta["params"])):
        for pair, df in h1.items():
            arr = np.zeros(len(df), np.int8)
            part = sig[(sig.param_id == pid) & (sig.pair == pair)]
            arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.int8)
            signals[(pid, pair)] = arr
    exits = exits_from(meta.get("exits"))
    log(f"Silnik: {len(meta['params'])} wariant(y) wejścia × {len(exits)} wyjść × {len(h1)} par…")
    resolver = m1_resolver_lazy(m1_dir) if m1_dir and m1_dir.exists() else None
    res = run(h1, signals, meta["params"], exits=exits, resolver=resolver)
    variants = variant_table(res)

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    out = out_root / name / run_id
    out.mkdir(parents=True, exist_ok=True)
    res["entries"].to_parquet(out / "entries.parquet", index=False)
    res["outcomes"].to_parquet(out / "outcomes.parquet", index=False)
    variants.assign(params=variants["params"].map(json.dumps)).to_parquet(out / "variants.parquet", index=False)
    manifest = {
        "name": name, "run_id": run_id, "engine_version": ENGINE_VERSION,         # D6
        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
        "data_hash": data_hash(h1_dir),
        "data_source": "dukascopy" if m1_dir else "inne",
        "m1_resolver": resolver is not None,
        "pairs": sorted(h1), "params": meta["params"], "n_variants": res["n_variants"],
        "n_exits": len(exits), "oos_cutoff": int(res["cutoff"]),
        "data_from": int(min(df.ts.iloc[0] for df in h1.values())),
        "data_to": int(max(df.ts.iloc[-1] for df in h1.values())),
        "skipped": res["skipped"], "hypothesis": meta.get("hypothesis"), "sizing": meta.get("sizing"),
        "seconds": round(time.time() - t_start, 1),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    (out / "strategy.py").write_text(code, encoding="utf-8")
    write_report(out, manifest, variants, res, code)
    log(f"Gotowe w {manifest['seconds']} s → {out}")
    return out
