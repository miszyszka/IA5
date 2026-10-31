"""Pełne liczenie strategii: kod → sygnały (sandbox) → silnik → walidacja → pliki wyników (sekcja 4) + raport.

Pliki w katalogu wyników (to samo trafia na gałąź `data` pod results/{id}/):
  manifest.json    D6: hashe, wersja silnika, zakres danych, liczba wariantów (W2)
  variants.json    metryki per wariant + zakres wierszy w trades.parquet (row_start, row_end)
  trades.parquet   wszystkie transakcje wszystkich wariantów, posortowane po variant_id
  validation.json  benchmark losowy, DSR, PBO, walk-forward, bootstrap, spread, kapitał, werdykt
  candles/{PARA}.parquet  wszystkie świece użyte w liczeniu (Yahoo po czyszczeniu, D-039) — do wykresu
  report.md        raport dla Claude
  strategy.py      kod strategii
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import ENGINE_VERSION
from .config import DEFAULT_SIZING
from .engine import Exit, default_exits, run, summarize
from .portfolio import equity_stats, simulate_equity
from .report import write_report
from .sandbox import run_strategy_code
from .validate import (
    bootstrap_ci,
    deflated_sharpe,
    pbo_cscv,
    per_trade_sharpe,
    random_benchmark,
    spread_stress,
    verdict,
    walk_forward,
)

MIN_TRADES = 30          # wariant z mniejszą liczbą transakcji IS nie trafia na szczyt rankingu
TOP_FOR_CANDLES = 10     # wycinki świec dla tylu najlepszych wariantów
CANDLE_PAD = 24          # świec przed wejściem i po wyjściu


def data_hash(h1_dir: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(h1_dir.glob("*.parquet")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def data_clean_info(h1_dir: Path, h1: dict) -> dict:
    """D8: opis warstwy czyszczenia per para (plik {PARA}.json obok świec, z ready.build)."""
    out = {}
    for pair, df in h1.items():
        f = h1_dir / f"{pair}.json"
        info = {}
        if f.exists():
            try:
                info = json.loads(f.read_text())
            except ValueError:
                info = {}
        filled = int(df["filled"].sum()) if "filled" in df else 0
        gaps = int((df["gap_before"] > 0).sum()) if "gap_before" in df else 0
        out[pair] = {"version": info.get("version"), "source": info.get("source"), "filled": filled, "gaps": gaps,
                     "gap_hours": int(df["gap_before"].sum()) if "gap_before" in df else 0,
                     "rejected": info.get("rejected", 0), "closed_hours": info.get("closed_hours", 0)}
    return out


def exits_from(meta_exits) -> list[Exit]:
    if not meta_exits:
        return default_exits()
    return [Exit(**e) for e in meta_exits]


def variant_table(res: dict) -> pd.DataFrame:
    """Metryki per wariant: całość, IS, OOS (W1: ranking tylko po IS)."""
    o = res["outcomes"]
    v = res["variants"].copy()
    if o.empty:
        v["rank_is"] = np.nan
        return v
    for name, part in (("all", o), ("is", o[o["sample"] == "IS"]), ("oos", o[o["sample"] == "OOS"])):
        s = summarize(part).set_index("variant_id").add_prefix(f"{name}_")
        v = v.join(s, on="variant_id")
    ok = v["is_trades"].fillna(0) >= MIN_TRADES
    v["rank_is"] = v["is_exp_r"].where(ok).rank(ascending=False, method="first")
    return v


def trades_table(res: dict) -> pd.DataFrame:
    """Transakcje w jednej tabeli dla dashboardu (posortowane po variant_id, typy kompaktowe)."""
    o, e = res["outcomes"], res["entries"]
    if o.empty:
        return pd.DataFrame()
    t = o.merge(e[["entry_id", "entry_i", "dir", "weight", "entry_ts", "entry_px"]], on="entry_id")
    t = t.sort_values(["variant_id", "entry_ts"], kind="stable").reset_index(drop=True)
    return pd.DataFrame({
        "variant_id": t["variant_id"].astype(np.int32), "pair": t["pair"].astype(str),
        "dir": t["dir"].astype(np.int8), "entry_ts": t["entry_ts"].astype(np.int32),
        "entry_px": t["entry_px"].astype(float), "exit_ts": t["exit_ts"].astype(np.int32),
        "exit_px": t["exit_px"].astype(float), "reason": t["reason"].astype(str),
        "pips_gross": t["pips_gross"].astype(np.float32), "pips_net": t["pips_net"].astype(np.float32),
        "r_net": t["r_net"].astype(np.float32), "mae": t["mae"].astype(np.float32), "mfe": t["mfe"].astype(np.float32),
        "bars": t["bars"].astype(np.int16), "ambiguous": t["ambiguous"].astype(bool),
        "sample": t["sample"].astype(str), "weight": t["weight"].astype(np.float32), "entry_i": t["entry_i"].astype(np.int32),
    })


def clean(x):
    """JSON bez NaN/inf (null zamiast) i bez typów numpy."""
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if math.isnan(x) or math.isinf(x) else round(float(x), 6)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def validate_best(res: dict, variants: pd.DataFrame, trades: pd.DataFrame, exits: list[Exit], signals: dict,
                  h1: dict, sizing, log=print, hours=None) -> dict:
    ranked = variants.dropna(subset=["rank_is"]).sort_values("rank_is")
    if ranked.empty:
        return {"verdict": {"color": "yellow", "note": "żaden wariant nie ma 30 transakcji IS", "checks": []}}
    best = ranked.iloc[0]
    vid, pid = int(best["variant_id"]), int(best["param_id"])
    ex = exits[vid - pid * len(exits)]
    bt = trades[trades["variant_id"] == vid]
    oos = bt[bt["sample"] == "OOS"]
    out: dict = {"best_variant_id": vid, "best_exit": ex.label(), "best_params": best["params"],
                 "oos_trades": int(len(oos)), "oos_mean_pips": float(oos["pips_net"].mean()) if len(oos) else None,
                 "oos_mean_r": float(oos["r_net"].mean()) if len(oos) else None,
                 "is_mean_r": float(best["is_exp_r"])}
    log("Walidacja: benchmark losowych wejść (1000 losowań)…")
    sig_best = {pair: signals[(pid, pair)] for pair in h1}
    out["benchmark"] = random_benchmark(res["preps"], bt, ex, signals=sig_best, hours=hours)
    log("Walidacja: Deflated Sharpe, PBO, walk-forward…")
    is_t = trades[trades["sample"] == "IS"]
    sharpes = is_t.groupby("variant_id")["r_net"].apply(lambda r: per_trade_sharpe(r.to_numpy(float))
                                                        if len(r) >= MIN_TRADES else np.nan).to_numpy(float)
    out["dsr"] = deflated_sharpe(bt[bt["sample"] == "IS"]["r_net"].to_numpy(float), sharpes)
    out["pbo"] = pbo_cscv(trades[["variant_id", "r_net", "entry_ts"]], trades["entry_ts"])
    out["walk_forward"] = walk_forward(trades[["variant_id", "r_net", "pips_net", "entry_ts"]])
    out["bootstrap"] = {"all": bootstrap_ci(bt["pips_net"].to_numpy(float)),
                        "oos": bootstrap_ci(oos["pips_net"].to_numpy(float))}
    out["spread"] = spread_stress(bt)
    out["ambiguous_pct"] = float(bt["ambiguous"].mean() * 100)
    out["equity"] = {}
    for pct in sizing:
        curve = simulate_equity(bt, pct)
        out["equity"][str(pct)] = {**equity_stats(curve), "taken": curve["taken"], "skipped_margin": curve["skipped_margin"]}
    out["verdict"] = verdict(out)
    return out


def candle_slices(h1: dict, trades: pd.DataFrame, variants: pd.DataFrame, full: bool) -> dict[str, pd.DataFrame]:
    out = {}
    top = variants.dropna(subset=["rank_is"]).sort_values("rank_is").head(TOP_FOR_CANDLES)["variant_id"]
    sel = trades[trades["variant_id"].isin(top)]
    for pair, df in h1.items():
        cols = ["ts", "open", "high", "low", "close"]
        if full:
            out[pair] = df[cols].reset_index(drop=True)
            continue
        t = sel[sel["pair"] == pair]
        if t.empty:
            continue
        keep = np.zeros(len(df), bool)
        ts = df["ts"].to_numpy()
        a = np.searchsorted(ts, t["entry_ts"].to_numpy()) - CANDLE_PAD
        b = np.searchsorted(ts, t["exit_ts"].to_numpy()) + CANDLE_PAD
        for x, y in zip(np.clip(a, 0, None), np.clip(b, 0, len(df))):
            keep[x:y] = True
        out[pair] = df.loc[keep, cols].reset_index(drop=True)
    return out


def ready_source(h1_dir: Path) -> str | None:
    """Źródło danych do liczenia z opisów {PARA}.json (ready.build): jedno wspólne dla wszystkich par albo None."""
    found = set()
    for f in sorted(h1_dir.glob("*.parquet")):
        try:
            found.add(json.loads(f.with_suffix(".json").read_text()).get("source"))
        except (FileNotFoundError, ValueError):
            found.add(None)
    return found.pop() if len(found) == 1 else None


def run_file(code: str, name: str, h1_dir: Path, out_root: Path, log=print,
             source: str | None = None, full_candles: bool = True, strategy_id: str | None = None,
             extra: dict | None = None, require_source: str | None = None) -> Path:
    """require_source="yahoo" (ia5 start, ia5 run) — liczenie tylko na danych z tego źródła (D7, D-041)."""
    t_start = time.time()
    src = ready_source(h1_dir)
    if not any(h1_dir.glob("*.parquet")):
        raise SystemExit(f"Brak danych do liczenia w {h1_dir} — uruchom ia5 start (zrobi kopię świec Yahoo).")
    if require_source and src != require_source:
        raise SystemExit(f"Dane do liczenia w {h1_dir} nie pochodzą w całości z {require_source} (źródło: {src or 'nieznane'}) — "
                         "ia5 start przebuduje je z kopii świec Yahoo.")
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
            arr = np.zeros(len(df), np.float32)
            part = sig[(sig.param_id == pid) & (sig.pair == pair)]
            arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
            signals[(pid, pair)] = arr
    exits = exits_from(meta.get("exits"))
    sizing = [float(x) for x in (meta.get("sizing") or DEFAULT_SIZING)]
    log(f"Silnik: {len(meta['params'])} wariant(y) wejścia × {len(exits)} wyjść × {len(h1)} par…")
    hours = meta.get("hours")  # D-034: None = okno z config (B11), False = bez okna, [od, do] = własne
    hours = tuple(hours) if isinstance(hours, list) else hours
    pyramid = int(meta.get("pyramid") or 1)
    res = run(h1, signals, meta["params"], exits=exits, hours=hours, pyramid=pyramid)
    variants = variant_table(res)
    trades = trades_table(res)
    validation = validate_best(res, variants, trades, exits, signals, h1, sizing, log=log, hours=hours)

    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    sid = strategy_id or name
    out = out_root / sid / run_id
    (out / "candles").mkdir(parents=True, exist_ok=True)

    # zakres wierszy każdego wariantu w trades.parquet → dashboard czyta tylko potrzebny fragment
    if not trades.empty:
        bounds = trades.groupby("variant_id").apply(lambda g: (int(g.index[0]), int(g.index[-1]) + 1), include_groups=False)
        variants["row_start"] = variants["variant_id"].map(lambda v: bounds.get(v, (0, 0))[0])
        variants["row_end"] = variants["variant_id"].map(lambda v: bounds.get(v, (0, 0))[1])
        trades.drop(columns=["entry_i"]).to_parquet(out / "trades.parquet", index=False, compression="snappy",
                                                    row_group_size=20_000)
    for pair, df in candle_slices(h1, trades, variants, full_candles).items():
        df = df.astype({"ts": np.int32})  # int32: przeglądarka dostaje zwykłe liczby, nie BigInt
        df.to_parquet(out / "candles" / f"{pair}.parquet", index=False, compression="snappy")

    manifest = {
        "id": sid, "name": name, "run_id": run_id, "engine_version": ENGINE_VERSION,       # D6
        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16], "data_hash": data_hash(h1_dir),
        "data_source": src or source or "inne",
        "candles": "pełne" if full_candles else f"wycinki ±{CANDLE_PAD} świec wokół transakcji {TOP_FOR_CANDLES} najlepszych wariantów",
        "pairs": sorted(h1), "params": meta["params"], "n_variants": res["n_variants"], "n_exits": len(exits),
        "oos_cutoff": int(res["cutoff"]), "sizing": sizing, "pyramid": pyramid,
        "hours": "bez okna" if hours is False else (list(hours) if hours else "07–17 czasu polskiego (B11)"),
        "data_from": int(min(df.ts.iloc[0] for df in h1.values())), "data_to": int(max(df.ts.iloc[-1] for df in h1.values())),
        "data_clean": data_clean_info(h1_dir, h1),
        "skipped": res["skipped"], "hypothesis": meta.get("hypothesis"), "trades_rows": int(len(trades)),
        "created": int(time.time()), "seconds": round(time.time() - t_start, 1),
        "verdict": validation.get("verdict", {}).get("color"),
        **(extra or {}),
    }
    vcols = [c for c in variants.columns if c not in ("x_kind",)]
    vjson = [clean(r) for r in variants[vcols].to_dict(orient="records")]
    (out / "manifest.json").write_text(json.dumps(clean(manifest), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "variants.json").write_text(json.dumps(vjson, ensure_ascii=False), encoding="utf-8")
    (out / "validation.json").write_text(json.dumps(clean(validation), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "strategy.py").write_text(code, encoding="utf-8")
    write_report(out, manifest, variants, trades, validation, code)
    log(f"Gotowe w {round(time.time() - t_start, 1)} s → {out}")
    return out
