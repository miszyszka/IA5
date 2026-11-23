"""D-072 — pilotażowy OOS na akcjach: strategia D1 policzona na świecach dziennych spółek.

Po co: wzór ze świec (formacja, RSI, wybicie, cofnięcie w trendzie), który jest prawdziwą przewagą, a nie dopasowaniem do
8 par FX, powinien choć trochę działać także na zupełnie innych danych. Spółki nie brały udziału w żadnym wyborze
(ani parametrów, ani wyjścia), więc to próba spoza dziedziny — „drugi OOS”.

Zasady (pilotaż, nie wchodzi do werdyktu):
- tylko strategie TIMEFRAME = "D1" (spółek H1 nie mamy); ten sam kod, ten sam wariant parametrów i to samo wyjście;
- świece z data/stk_ready (Yahoo po warstwie czyszczenia Stocks), od stk_config.DATA_FROM; bez dywidend w wyniku;
- B1–B8 jak w silniku (sygnał na zamknięciu dnia, wejście na open następnego); koszt: stk_config.COST na każdą stronę;
- wynik w % ceny wejścia i w R; benchmark: losowe wejścia na tych samych spółkach, z tymi samymi kierunkami i wyjściem
  (≥ 1000 losowań) — to oddziela przewagę wzoru od zwykłego wzrostu akcji;
- MAX_PAIRS / PAIR_RANK strategii nie dotyczą spółek (dotyczą par FX).
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .config import extra_instruments
from .engine import Exit, run
from .sandbox import run_strategy_code
from .stk_config import COST, DATA_FROM
from .validate import bootstrap_ci, random_benchmark

DAY = 86400
GAP_DAYS = 5          # więcej niż 5 dni kalendarzowych bez sesji (poza weekendem i świętem) = przerwa w danych (B12)
MIN_TICKERS = 3
MIN_TRADES = 30
SIMS = 1000


def stock_frames(stk_dir: Path, since: str = DATA_FROM, tickers=None) -> dict[str, pd.DataFrame]:
    """Spółki w układzie świec D1 silnika: ts (północ dnia sesji w NY), open, high, low, close, close_ts, gap_before."""
    out = {}
    for pf in sorted(Path(stk_dir).glob("*.parquet")):
        if tickers is not None and pf.stem not in tickers:
            continue
        df = pd.read_parquet(pf)
        if "day" in df:
            df = df[df["day"] >= since]
        if "spike" in df:
            df = df[~df["spike"].astype(bool)]   # dzień-wyskok zastąpiony płaską świecą — poza liczeniem
        df = df[["ts", "open", "high", "low", "close"]].dropna().sort_values("ts").reset_index(drop=True)
        if len(df) < 300:
            continue
        ts = df["ts"].to_numpy(np.int64)
        gap = np.r_[0, (np.diff(ts) > GAP_DAYS * DAY).astype(np.int64)]
        nxt = np.r_[ts[1:], ts[-1] + DAY]
        df["close_ts"] = np.minimum(nxt, ts + DAY)
        df["gap_before"] = gap
        out[pf.stem] = df
    return out


def _write(frames: dict[str, pd.DataFrame], folder: Path) -> None:
    for t, df in frames.items():
        df.to_parquet(folder / f"{t}.parquet", index=False)
        (folder / f"{t}.json").write_text(json.dumps({"source": "yahoo", "series": "stk"}))


def _net_pct(o: pd.DataFrame, e: pd.DataFrame) -> pd.DataFrame:
    t = o.merge(e[["entry_id", "dir", "entry_px", "entry_ts"]], on="entry_id")
    px = t["entry_px"].to_numpy(float)
    gross = t["pips_gross"].to_numpy(float)              # pip = 1 → jednostki ceny
    cost = 2 * COST * px
    t["ret_pct"] = (gross - cost) / px * 100
    t["r_net"] = (gross - cost) / t["risk_pips"].to_numpy(float)
    t["pips_net"] = t["ret_pct"]                         # random_benchmark(pct_cost) porównuje w tych samych %
    return t


def _side(t: pd.DataFrame, m: pd.Series) -> dict:
    return {"trades": int(m.sum()), "mean_pct": float(t.loc[m, "ret_pct"].mean()) if m.any() else None}


def _verdict(mean, pct, n) -> dict:
    if n < MIN_TRADES or mean is None or pct is None:
        return {"color": "mute", "text": f"za mało transakcji na akcjach ({n})"}
    if mean > 0 and pct >= 90:
        return {"color": "green", "text": "akcje potwierdzają wzór"}
    if mean > 0 and pct >= 75:
        return {"color": "yellow", "text": "akcje słabo potwierdzają"}
    return {"color": "red", "text": "akcje nie potwierdzają"}


def evaluate(code: str, param_id: int, ex: Exit, stk_dir: Path, pyramid: int = 1, frames: dict | None = None,
             sims: int = SIMS, log=print, timeout: int = 1800) -> dict:
    """Jeden wariant (parametry param_id + wyjście ex) strategii D1 na spółkach. Zwraca blok wyniku (słownik JSON)."""
    frames = frames if frames is not None else stock_frames(stk_dir)
    if len(frames) < MIN_TICKERS:
        return {"na": f"za mało spółek z historią do liczenia ({len(frames)}; potrzeba {MIN_TICKERS}) — ustaw listę w zakładce Stocks"}
    with tempfile.TemporaryDirectory(prefix="ia5-stk-") as tmp:
        folder = Path(tmp)
        _write(frames, folder)
        sig, meta = run_strategy_code(code, folder, d1_dir=folder, param_ids=[param_id], timeout=timeout)
    if meta.get("timeframe") != "D1":
        return {"na": "tylko strategie na świecach dziennych (TIMEFRAME = \"D1\") — spółek H1 nie mamy"}
    if meta["lookahead"]:
        return {"na": "detektor look-ahead zatrzymał liczenie na spółkach"}
    p = meta["params"][param_id]
    signals, levels = {}, {}
    for t, df in frames.items():
        part = sig[(sig.param_id == param_id) & (sig.pair == t)]
        arr = np.zeros(len(df), np.float32)
        arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
        signals[(0, t)] = arr
        if meta.get("levels"):
            lv = np.full((len(df), 3), np.nan)
            lv[part["i"].to_numpy(int), 0] = part["tp"].to_numpy(float)
            lv[part["i"].to_numpy(int), 1] = part["sl"].to_numpy(float)
            if "bars" in part:
                lv[part["i"].to_numpy(int), 2] = part["bars"].to_numpy(float)
            levels[(0, t)] = lv
    with extra_instruments(frames):
        res = run(frames, signals, [p], exits=[ex], hours=False, pyramid=pyramid, levels=levels or None)
        o, e = res["outcomes"], res["entries"]
        if o.empty:
            return {"tickers": len(frames), "trades": 0, "verdict": _verdict(None, None, 0), "params": p, "exit": ex.label()}
        t = _net_pct(o, e)
        bench = random_benchmark(res["preps"], t[["pair", "dir", "pips_net"]], ex, sims=sims, hours=False, pct_cost=COST,
                                 level_entries=e if ex.kind == "level" else None)
    by_t = t.groupby("pair")["ret_pct"].agg(["count", "mean"])
    years = pd.to_datetime(t["entry_ts"], unit="s", utc=True).dt.year
    by_y = t.groupby(years)["ret_pct"].mean()
    mid = float(np.median(t["entry_ts"]))
    halves = [t[t["entry_ts"] < mid]["ret_pct"], t[t["entry_ts"] >= mid]["ret_pct"]]
    sd = t["ret_pct"].std(ddof=1)
    mean = float(t["ret_pct"].mean())
    out = {
        "tickers": len(frames), "tickers_traded": int(len(by_t)), "trades": int(len(t)),
        "params": p, "exit": ex.label(), "from": DATA_FROM, "cost_pct_side": COST * 100,
        "mean_pct": mean, "mean_r": float(t["r_net"].mean()), "win_rate": float((t["ret_pct"] > 0).mean()),
        "t_stat": float(mean / (sd / np.sqrt(len(t)))) if len(t) > 1 and sd > 0 else None,
        "long": _side(t, t["dir"] > 0), "short": _side(t, t["dir"] < 0),
        "halves_pct": [float(x.mean()) if len(x) else None for x in halves],
        "tickers_positive": int((by_t["mean"] > 0).sum()),
        "years_positive": int((by_y > 0).sum()), "years": int(len(by_y)),
        "bootstrap": bootstrap_ci(t["ret_pct"].to_numpy(float)),
        "benchmark": bench, "skipped": res["skipped"],
        "per_ticker": [{"ticker": k, "trades": int(r["count"]), "mean_pct": float(r["mean"])} for k, r in by_t.iterrows()],
    }
    out["verdict"] = _verdict(mean, bench.get("percentile"), len(t))
    log(f"  OOS akcje: {len(t)} transakcji na {len(by_t)} spółkach, średnio {mean:+.2f}% netto, "
        f"percentyl losowych {bench.get('percentile', float('nan')):.0f} → {out['verdict']['text']}")
    return out
