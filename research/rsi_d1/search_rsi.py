"""Poszukiwanie strategii RSI na świecach dziennych (D1) — model wykonania = silnik IA5 (engine.simulate, level + cap).

Wybór WYŁĄCZNIE na IS (wejścia przed granicą 75% czasu, jak silnik). OOS zapisywany osobno i otwierany raz dla listy
wybranej po IS. Wynik transakcji = zwrot na nominale po spreadzie (portfolio.trade_returns) × waga; koszt nocy 0,5 pipsa
(stres O5/D-054) odejmowany w ocenie.

Użycie: python search_rsi.py <katalog d1_ready> <plik wyjściowy .parquet>  (przebieg 1; przebieg 2: run2.py)
"""
from __future__ import annotations

import itertools
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from ia5 import engine
from ia5 import indicators as ind
from ia5.config import PAIRS

RSI_LEVELS = {2: (5, 10, 15, 20), 3: (10, 15, 20, 25), 5: (15, 20, 25, 30), 14: (25, 30, 35, 40, 45)}
MODES = ("zdarzenie", "stan")           # zdarzenie = pierwsza świeca za progiem; stan = każda świeca za progiem
TRENDS = ("bez", "sma200")              # sma200: long tylko nad SMA200, short tylko pod
PYRAMIDS = (1, 3, 5)
WEIGHTS = ("stała", "głębokość", "seria_rosnąco", "seria_malejąco", "otwarte_malejąco", "otwarte_rosnąco")
NIGHT_COST_PIPS = 0.5
RECENT = 5                               # „otwarte” ≈ sygnały w tym samym kierunku w 5 poprzednich dniach


def exits_grid():
    ex = [("czas", x, None, None, x) for x in (1, 2, 3, 5, 7, 10, 15, 20)]
    ex += [("atr", a, b, None, cap) for a, b, cap in itertools.product((1, 1.5, 2, 3), (0.5, 1, 1.5, 2, 3), (5, 10, 20))]
    ex += [("atr_sl", a, None, None, cap) for a, cap in itertools.product((1.5, 2, 3), (3, 5, 10))]
    ex += [("swing", k, tp, buf, cap) for k, tp, buf, cap in itertools.product((3, 5, 10, 20), ("hh", 1, 2, "brak"), (0, 0.5), (10, 20))]
    return ex


EXITS = exits_grid()
SPECS = None
G = {}


def load(folder):
    return {f.stem: pd.read_parquet(f) for f in sorted(Path(folder).glob("*.parquet"))}


def init(folder):
    D = load(folder)
    t0 = min(int(df.ts.iloc[0]) for df in D.values())
    t1 = max(int(df.ts.iloc[-1]) for df in D.values())
    G["cutoff"] = t0 + 0.75 * (t1 - t0)
    G["m0"] = pd.Timestamp(t0, unit="s").year * 12 + pd.Timestamp(t0, unit="s").month - 1
    G["data"] = {}
    for pair, df in D.items():
        P = engine.prepare(df)
        x = {"P": P, "c": df.close.to_numpy(float), "atr": P["atr14"]}
        x["rsi"] = {n: ind.rsi(df.close, n).to_numpy() for n in RSI_LEVELS}
        x["sma200"] = ind.sma(df.close, 200).to_numpy()
        x["sma50"] = ind.sma(df.close, 50).to_numpy()
        x["ll"] = {k: ind.lowest(df.low, k).to_numpy() for k in (3, 5, 10, 20)}
        x["hh"] = {k: ind.highest(df.high, k).to_numpy() for k in (3, 5, 10, 20)}
        G["data"][pair] = x


def streak(mask):
    out = np.zeros(len(mask), np.int64)
    run = 0
    for i, v in enumerate(mask):
        run = run + 1 if v else 0
        out[i] = run
    return out


def entry_set(x, n, L, mode, trend):
    """Kierunek sygnału i cechy do wag na każdej świecy. n, L mogą być krotkami (suma kilku reguł RSI)."""
    rules = list(zip(n, L)) if isinstance(n, tuple) else [(n, L)]
    lo = np.zeros(len(x["c"]), bool)
    hi = np.zeros(len(x["c"]), bool)
    zone_lo = np.zeros(len(x["c"]), bool)
    zone_hi = np.zeros(len(x["c"]), bool)
    depth_lo = np.zeros(len(x["c"]))
    depth_hi = np.zeros(len(x["c"]))
    with np.errstate(invalid="ignore"):
        for nn, LL in rules:
            r = x["rsi"][nn]
            a, b = r < LL, r > 100 - LL
            zone_lo |= a
            zone_hi |= b
            depth_lo = np.fmax(depth_lo, np.where(a, (LL - r) / LL, 0))
            depth_hi = np.fmax(depth_hi, np.where(b, (r - (100 - LL)) / LL, 0))
            if mode == "zdarzenie":
                prev = np.r_[np.nan, r[:-1]]
                a, b = a & (prev >= LL), b & (prev <= 100 - LL)
            lo |= a & ~np.isnan(r)
            hi |= b & ~np.isnan(r)
        c, s200 = x["c"], x["sma200"]
        if trend in ("sma200", "sma200_rosnie", "sma50_200"):
            up, dn = c > s200, c < s200
            if trend == "sma200_rosnie":
                prev = np.r_[np.full(20, np.nan), s200[:-20]]
                up, dn = up & (s200 > prev), dn & (s200 < prev)
            if trend == "sma50_200":
                up, dn = up & (x["sma50"] > s200), dn & (x["sma50"] < s200)
            lo &= up
            hi &= dn
    sig = lo.astype(np.int8) - hi.astype(np.int8)
    st = np.where(sig > 0, streak(zone_lo), np.where(sig < 0, streak(zone_hi), 0))
    depth = np.where(sig > 0, depth_lo, np.where(sig < 0, depth_hi, 0))
    s = pd.Series(sig.astype(float))
    up = (s > 0).astype(float).rolling(RECENT, min_periods=1).sum().shift(1).fillna(0).to_numpy()
    dn = (s < 0).astype(float).rolling(RECENT, min_periods=1).sum().shift(1).fillna(0).to_numpy()
    recent = np.where(sig > 0, up, np.where(sig < 0, dn, 0))
    W = {
        "stała": np.ones(len(sig)),
        "głębokość": np.clip(0.5 + 2 * np.nan_to_num(depth), 0.5, 2.5),
        "seria_rosnąco": np.clip(st, 1, 3).astype(float),
        "seria_malejąco": 1 / np.clip(st, 1, 3),
        "otwarte_malejąco": 1 / (1 + recent),
        "otwarte_rosnąco": np.clip(1 + recent, 1, 3),
    }
    return sig, W


def levels_for(x, ex, i, d):
    kind, a, b, buf, _cap = ex
    c, atr = x["c"][i], x["atr"][i]
    if kind == "czas":
        return np.full(len(i), np.nan), np.full(len(i), np.nan)
    if kind == "atr":
        return c + d * b * atr, c - d * a * atr
    if kind == "atr_sl":
        return np.full(len(i), np.nan), c - d * a * atr
    k, tpk = a, b
    sl = np.where(d > 0, x["ll"][k][i] - buf * atr, x["hh"][k][i] + buf * atr)
    if tpk == "hh":
        tp = np.where(d > 0, x["hh"][k][i], x["ll"][k][i])
    elif tpk == "brak":
        tp = np.full(len(i), np.nan)
    else:
        tp = c + tpk * (c - sl)
    return tp, sl


def month_ids(ts):
    t = pd.to_datetime(ts, unit="s")
    return (t.year * 12 + t.month - 1).to_numpy() - G["m0"]


def metrics(ret, mon, is_mask, n_months_is):
    """Miesięczne sumy zwrotów IS → Sharpe, odsetek zyskownych miesięcy/kwartałów/lat, obsunięcie."""
    r, m = ret[is_mask], mon[is_mask]
    ms = np.bincount(np.clip(m, 0, n_months_is - 1), weights=r, minlength=n_months_is)
    active = np.bincount(np.clip(m, 0, n_months_is - 1), minlength=n_months_is) > 0
    first = np.argmax(active) if active.any() else 0
    ms = ms[first:]
    q = np.add.reduceat(ms, np.arange(0, len(ms), 3))
    y = np.add.reduceat(ms, np.arange(0, len(ms), 12))
    sd = ms.std(ddof=1)
    cum = np.cumsum(ms)
    dd = (cum - np.maximum.accumulate(np.r_[0, cum])[1:]).min() if len(cum) else 0
    return {"sum": float(ms.sum()), "sharpe_m": float(ms.mean() / sd * np.sqrt(12)) if sd > 0 else np.nan,
            "pos_m": float((ms[active[first:]] > 0).mean()) if active[first:].any() else np.nan,
            "pos_q": float((q > 0).mean()), "pos_y": float((y > 0).mean()), "max_dd": float(dd),
            "worst_y": float(y.min())}


def work(spec):
    n, L, mode, trend = spec
    cutoff = G["cutoff"]
    n_is = int(month_ids(np.array([int(cutoff)]))[0]) + 1
    per_pair = {}
    for pair, x in G["data"].items():
        P = x["P"]
        sig, W = entry_set(x, n, L, mode, trend)
        ent = engine.find_entries(P, sig)
        ent = ent[~(ent["atr14"].isna() | ent["atr5"].isna())].reset_index(drop=True)
        per_pair[pair] = (x, ent, W)
    rows = []
    for xid, ex in enumerate(EXITS):
        acc = {pyr: [] for pyr in PYRAMIDS}
        for pair, (x, ent, W) in per_pair.items():
            if ent.empty:
                continue
            P = x["P"]
            i = ent["signal_i"].to_numpy()
            d = ent["dir"].to_numpy().astype(float)
            e2 = ent.copy()
            e2["tp_px"], e2["sl_px"] = levels_for(x, ex, i, d)
            res = engine.simulate(P, e2, engine.Exit("level", cap=ex[4]), pair)
            xi = res["exit_i"].to_numpy(float).copy()
            xi[engine.data_cancel(P, i, ent["entry_i"].to_numpy(), xi)] = np.nan
            pip, spread = PAIRS[pair].pip, PAIRS[pair].spread_pips
            net = res["pips_gross"].to_numpy(float) - spread
            px = ent["entry_px"].to_numpy(float)
            ret = net * pip / px
            cost = NIGHT_COST_PIPS * np.nan_to_num(res["nights"].to_numpy(float)) * pip / px
            for pyr in PYRAMIDS:
                keep = engine.no_overlap(ent["entry_i"].to_numpy(), xi, ent["dir"].to_numpy(), pyr)
                acc[pyr].append({
                    "pair": pair, "ret": ret[keep], "cost": cost[keep], "w": {k: v[i[keep]] for k, v in W.items()},
                    "exit_ts": res["exit_ts"].to_numpy(float)[keep], "is": ent["entry_ts"].to_numpy()[keep] < cutoff,
                    "r": res["r"].to_numpy(float)[keep] - spread / res["risk_pips"].to_numpy(float)[keep],
                    "bars": res["bars"].to_numpy(float)[keep],
                })
        for pyr in PYRAMIDS:
            parts = acc[pyr]
            if not parts:
                continue
            ret = np.concatenate([p["ret"] for p in parts])
            cost = np.concatenate([p["cost"] for p in parts])
            isk = np.concatenate([p["is"] for p in parts])
            if isk.sum() < 50:
                continue
            mon = month_ids(np.concatenate([p["exit_ts"] for p in parts]).astype(np.int64))
            pr = np.concatenate([np.full(len(p["ret"]), p["pair"]) for p in parts])
            rr = np.concatenate([p["r"] for p in parts])
            bars = np.concatenate([p["bars"] for p in parts])
            for wname in WEIGHTS:
                w = np.concatenate([p["w"][wname] for p in parts])
                w = w / w[isk].mean()                       # ta sama średnia ekspozycja na IS dla każdej wagi
                val = w * (ret - cost)
                mt = metrics(val, mon, isk, n_is)
                pp = pd.Series(val[isk]).groupby(pr[isk]).sum()
                oos = ~isk
                rows.append({
                    "rsi_n": str(n), "L": str(L), "mode": mode, "trend": trend, "exit_id": xid, "exit": str(ex), "pyramid": pyr,
                    "weight": wname, "n_is": int(isk.sum()), "n_oos": int(oos.sum()),
                    "exp_r_is": float(np.nanmean(rr[isk])), "avg_bars": float(np.nanmean(bars[isk])),
                    "pairs_pos": int((pp > 0).sum()), "n_pairs": len(pp),
                    **{f"is_{k}": v for k, v in mt.items()},
                    # OOS liczony, ale nie używany do wyboru (W1); otwierany dopiero dla listy wybranej po IS
                    "oos_sum": float(val[oos].sum()), "oos_mean": float(val[oos].mean()) if oos.any() else np.nan,
                    "_oos_mon": None,
                })
    return rows


def main():
    folder, out = sys.argv[1], sys.argv[2]
    specs = SPECS() if SPECS else [(n, L, m, t) for n, Ls in RSI_LEVELS.items() for L in Ls for m in MODES for t in TRENDS]
    if len(sys.argv) > 3:
        specs = specs[: int(sys.argv[3])]
    t = time.time()
    with Pool(2, initializer=init, initargs=(folder,)) as pool:
        rows = []
        for k, r in enumerate(pool.imap_unordered(work, specs)):
            rows += r
            print(f"{k + 1}/{len(specs)} wejść, {len(rows)} konfiguracji, {time.time() - t:.0f} s", flush=True)
    df = pd.DataFrame(rows).drop(columns=["_oos_mon"])
    df.to_parquet(out, index=False)
    print("zapisano", out, len(df))


if __name__ == "__main__":
    main()
