"""D-076: zakładka Zasięg — prognoza zasięgu ruchu na 1/3/5 dni, ściśnięcie na H1 i poziomy wybicia z TP = k × SL.

Liczone co godzinę (GitHub Actions `ia5 live`, Mac zapasowo) na tych samych danych co silnik (data/h1_ready, data/d1_ready)
i tymi samymi funkcjami co strategia `strategies/examples/zasieg_wybicie.py` (ind.range_forecast, ind.squeeze) — test
pilnuje, że sygnały tutaj = sygnały strategii. Wynik: range/state.json na gałęzi data (0 odczytów Firestore).

Co jest w stanie każdej pary:
  forecast  — prognoza zasięgu (max high − min low) na 1, 3 i 5 kolejnych dni: mediana i pasmo 80% w pipsach, obok zwykły
              zasięg (mediana z ostatniego roku) i „żywiej / normalnie / spokojniej niż zwykle”;
  history   — ostatnie 120 dni prognozy 3-dniowej obok tego, co się zrealizowało (dowód, że model działa — albo nie);
  box       — pudełko z 24 ostatnich godzin, percentyl jego wysokości, stan „ściśnięcie”, poziomy wybicia w obie strony
              (zamknięcie godziny za granicą → wejście na open następnej, SL za drugą stroną, TP = 3 × SL) i czy cel
              mieści się w prognozie 3 dni;
  signals   — sygnały reguły z ostatnich 7 dni z wynikiem z silnika (TP / SL / czas / otwarta).
Jakość modelu (`quality`): na ostatnich 25% historii każdej pary (OOS), błąd prognozy wobec naiwnej „średni zakres × stała”
i trafienie pasma 80% — liczby, nie obietnica.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import COMPUTE_PAIRS, instrument
from .engine import Exit, find_entries, no_overlap, prepare, simulate
from .session import in_trading_hours

RANGE_VERSION = "1"
HORIZONS = (1, 3, 5)
BOX, REF, PCT, H = 24, 500, 20, 3      # te same stałe co strategies/examples/zasieg_wybicie.py
TP_MULT = 3
CAP = 72
HISTORY_DAYS = 120
SIGNAL_DAYS = 7
TYPICAL_DAYS = 250


def d1_frame(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))
    cols = ["open", "high", "low", "close"] + (["close_ts"] if "close_ts" in d else [])
    d = d[cols].copy()
    if "close_ts" not in d:
        d["close_ts"] = raw["ts"].to_numpy(np.int64) + 86400
    return d


def h1_frame(raw: pd.DataFrame) -> pd.DataFrame:
    return raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]].copy()


def signal_frame(h1: pd.DataFrame, d1: pd.DataFrame | None, m: float) -> pd.DataFrame:
    """Reguła wybicia z ściśnięcia — DOKŁADNIE jak w zasieg_wybicie.py (test tests/test_zasieg_d076.py).
    Kolumny: dir (+1/−1/0), sl, tp, upper, lower, pct (pudełko sprzed świecy), reach (prognoza zasięgu 3 dni w cenie)."""
    n = len(h1)
    frame = h1.copy()
    ind.attach_d1(frame, d1)
    out = pd.DataFrame(index=h1.index, data={"dir": np.zeros(n, int), "sl": np.nan, "tp": np.nan})
    if d1 is None or len(d1) < 300:
        return out.assign(upper=np.nan, lower=np.nan, pct=np.nan, reach=np.nan)
    reach = ind.d1_to_h1(frame, ind.range_forecast(ind.d1(frame), H)["mid"]).to_numpy(float)
    sq = ind.squeeze(frame, BOX, REF)
    up, lo, pct = (sq[k].shift(1).to_numpy(float) for k in ("upper", "lower", "pct"))
    c = frame["close"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        scisk = pct <= PCT
        dlugi = scisk & (c > up)
        krotki = scisk & (c < lo)
        srodek = (up + lo) / 2
        sl = np.where(dlugi, lo, np.where(krotki, up, np.nan))
        za_daleko = m * np.abs(c - sl) > reach
        sl = np.where(za_daleko, srodek, sl)
        ryzyko = np.abs(c - sl)
        ok = (dlugi | krotki) & (ryzyko > 0) & (m * ryzyko <= reach)
    kier = np.where(ok, np.where(dlugi, 1, -1), 0)
    out["dir"] = kier
    out["sl"] = np.where(ok, sl, np.nan)
    out["tp"] = np.where(ok, c + kier * m * ryzyko, np.nan)
    out["upper"], out["lower"], out["pct"], out["reach"] = up, lo, pct, reach
    ind.attach_d1(frame, None)
    return out


def _pips(x, pip):
    return None if x is None or not np.isfinite(x) else round(float(x) / pip, 1)


def mood(ratio_typical: float | None) -> str:
    if ratio_typical is None or not np.isfinite(ratio_typical):
        return "—"
    return "żywiej niż zwykle" if ratio_typical >= 1.15 else "spokojniej niż zwykle" if ratio_typical <= 0.85 else "jak zwykle"


def forecast_block(d: pd.DataFrame, pip: float) -> list[dict]:
    out = []
    for h in HORIZONS:
        f = ind.range_forecast(d, h)
        real = ind.realized_range(d, h)
        last = f.iloc[-1]
        typical = float(real.dropna().iloc[-TYPICAL_DAYS:].median()) if real.notna().any() else np.nan
        rt = float(last["mid"] / typical) if np.isfinite(last["mid"]) and typical > 0 else None
        out.append({"h": h, "mid": _pips(last["mid"], pip), "low": _pips(last["low"], pip), "high": _pips(last["high"], pip),
                    "typical": _pips(typical, pip), "vs_typical": None if rt is None else round(rt, 3), "mood": mood(rt)})
    return out


def quality(d: pd.DataFrame, h: int = H) -> dict:
    """Ocena prognozy h-dniowej na ostatnich 25% dni (OOS): średni błąd |log(rzeczywisty ÷ prognoza)| modelu i naiwnej
    prognozy (średni zakres 20 dni × stała dobrana na IS), trafienie pasma 80%, liczba dni."""
    f = ind.range_forecast(d, h)
    real = ind.realized_range(d, h)
    ok = (f["mid"].notna() & real.notna()).to_numpy()
    if ok.sum() < 100:
        return {"n": int(ok.sum())}
    idx = np.flatnonzero(ok)
    cut = idx[int(len(idx) * 0.75)]
    is_ = ok & (np.arange(len(d)) < cut)
    oos = ok & (np.arange(len(d)) >= cut)
    r, mid, base, lo, hi = (x.to_numpy(float) for x in (real, f["mid"], f["base"], f["low"], f["high"]))
    k = np.median(np.log(r[is_] / base[is_]))
    e_model = np.abs(np.log(r[oos] / mid[oos]))
    e_naive = np.abs(np.log(r[oos] / (base[oos] * np.exp(k))))
    return {"n": int(oos.sum()), "from": int(d.index[cut].timestamp()), "err_model": float(e_model.mean()),
            "err_naive": float(e_naive.mean()), "better_pct": float((1 - e_model.mean() / e_naive.mean()) * 100),
            "band80": float(((r[oos] >= lo[oos]) & (r[oos] <= hi[oos])).mean() * 100)}


def history_block(d: pd.DataFrame, pip: float, h: int = H) -> dict:
    f = ind.range_forecast(d, h).iloc[-HISTORY_DAYS:]
    real = ind.realized_range(d, h).iloc[-HISTORY_DAYS:]
    p = lambda s: [None if not np.isfinite(v) else round(float(v) / pip, 1) for v in s.to_numpy(float)]  # noqa: E731
    return {"ts": [int(t.timestamp()) for t in f.index], "low": p(f["low"]), "mid": p(f["mid"]), "high": p(f["high"]),
            "real": p(real)}


def box_block(h1: pd.DataFrame, d1: pd.DataFrame | None, pip: float) -> dict:
    """Pudełko z 24 ostatnich godzin (włącznie z ostatnią zamkniętą) i poziomy wybicia dla NASTĘPNEJ świecy."""
    sq = ind.squeeze(h1, BOX, REF).iloc[-1]
    up, lo, pct = float(sq["upper"]), float(sq["lower"]), float(sq["pct"]) if np.isfinite(sq["pct"]) else None
    frame = h1.copy()
    ind.attach_d1(frame, d1)
    reach = np.nan
    if d1 is not None and len(d1) >= 300:
        reach = float(ind.d1_to_h1(frame, ind.range_forecast(ind.d1(frame), H)["mid"]).iloc[-1])
    ind.attach_d1(frame, None)
    mid = (up + lo) / 2
    sides = {}
    for name, d, trig, far in (("long", 1, up, lo), ("short", -1, lo, up)):
        sl = far
        if TP_MULT * abs(trig - sl) > reach:
            sl = mid
        risk = abs(trig - sl)
        tp = trig + d * TP_MULT * risk
        sides[name] = {"trigger": trig, "sl": sl, "tp": tp, "risk_pips": _pips(risk, pip), "tp_pips": _pips(TP_MULT * risk, pip),
                       "reachable": bool(np.isfinite(reach) and risk > 0 and TP_MULT * risk <= reach),
                       "sl_mid": bool(sl == mid)}
    squeezed = pct is not None and pct <= PCT
    return {"upper": up, "lower": lo, "height_pips": _pips(up - lo, pip), "pct": None if pct is None else round(pct, 1),
            "squeezed": squeezed, "reach_pips": _pips(reach, pip), "tp_mult": TP_MULT, "long": sides["long"],
            "short": sides["short"], "armed": bool(squeezed and (sides["long"]["reachable"] or sides["short"]["reachable"]))}


def signals_block(raw_h1: pd.DataFrame, h1: pd.DataFrame, d1: pd.DataFrame | None, pair: str, now_ts: int) -> list[dict]:
    """Sygnały reguły (TP = 3 × SL) z ostatnich SIGNAL_DAYS dni z wynikiem z silnika — te same zasady co backtest (B1, B5, B11)."""
    sf = signal_frame(h1, d1, TP_MULT)
    since = now_ts - SIGNAL_DAYS * 86400
    ts = raw_h1["ts"].to_numpy(np.int64)
    sig = sf["dir"].to_numpy(float)
    sig[ts < since] = 0
    if not np.any(sig):
        return []
    P = prepare(raw_h1.reset_index(drop=True))
    lv = np.column_stack([sf["tp"].to_numpy(float), sf["sl"].to_numpy(float)])
    ent = find_entries(P, sig, lv)
    pend = np.flatnonzero(sig)[-1] == len(ts) - 1      # sygnał na ostatniej świecy — wejście dopiero na następnej
    out = []
    if len(ent):
        window = in_trading_hours(ent["entry_ts"].to_numpy(), None)   # B11: poza oknem silnik nie wchodzi
        ent = ent[window].reset_index(drop=True)
    if len(ent):
        res = simulate(P, ent, Exit("level", cap=CAP), pair)
        xi = res["exit_i"].to_numpy(float)
        keep = no_overlap(ent["entry_i"].to_numpy(), np.where(np.isnan(xi), 1e15, xi), ent["dir"].to_numpy())   # B8
        ent, res = ent[keep].reset_index(drop=True), res[keep].reset_index(drop=True)
        pip = instrument(pair).pip
        last_c = float(P["c"][-1])
        for k in range(len(ent)):
            e, r = ent.iloc[k], res.iloc[k]
            d = int(e["dir"])
            if r["reason"] == "brak danych":
                status, pips = "otwarta", (last_c - e["entry_px"]) * d / pip
            else:
                status, pips = {"TP": "TP", "SL": "SL"}.get(r["reason"], "czas"), r["pips_gross"]
            out.append({"signal_ts": int(e["signal_ts"]), "entry_ts": int(e["entry_ts"]), "dir": d, "entry": float(e["entry_px"]),
                        "sl": float(e["sl_px"]), "tp": float(e["tp_px"]), "status": status,
                        "pips": round(float(pips) - instrument(pair).spread_pips, 1)})
    if pend and bool(in_trading_hours(np.array([int(ts[-1]) + 3600]), None)[0]):
        i = len(ts) - 1
        out.append({"signal_ts": int(ts[i]), "entry_ts": None, "dir": int(sig[i]), "entry": None, "sl": float(sf["sl"].iloc[i]),
                    "tp": float(sf["tp"].iloc[i]), "status": "wejście na open następnej świecy", "pips": None})
    return out


def compute_state(h1_raw: dict[str, pd.DataFrame], d1_raw: dict[str, pd.DataFrame], now: int | None = None) -> dict:
    now = int(time.time()) if now is None else int(now)
    pairs, qual = {}, []
    data_to = 0
    for pair in COMPUTE_PAIRS:
        if pair not in d1_raw:
            continue
        pip = instrument(pair).pip
        d = d1_frame(d1_raw[pair])
        item: dict = {"pair": pair, "d1_last": int(d.index[-1].timestamp()), "forecast": forecast_block(d, pip),
                      "history": history_block(d, pip)}
        q = quality(d)
        item["quality"] = q
        if q.get("n", 0) >= 100:
            qual.append(q)
        if pair in h1_raw and len(h1_raw[pair]) > REF + BOX:
            raw = h1_raw[pair]
            h1 = h1_frame(raw)
            item["h1_last"] = int(raw["ts"].iloc[-1])
            data_to = max(data_to, item["h1_last"] + 3600)
            item["box"] = box_block(h1, d, pip)
            item["signals"] = signals_block(raw, h1, d, pair, item["h1_last"] + 3600)
        pairs[pair] = item
    pooled = {}
    if qual:
        w = np.array([q["n"] for q in qual], float)
        for k in ("err_model", "err_naive", "band80"):
            pooled[k] = float(np.average([q[k] for q in qual], weights=w))
        pooled["better_pct"] = float((1 - pooled["err_model"] / pooled["err_naive"]) * 100)
        pooled["n"] = int(w.sum())
    return {"version": RANGE_VERSION, "computedAt": now, "dataTo": data_to,
            "params": {"box": BOX, "ref": REF, "pct": PCT, "h": H, "tp_mult": TP_MULT, "cap": CAP},
            "quality": pooled, "pairs": pairs}


def load_ready(folder: Path) -> dict[str, pd.DataFrame]:
    return {f.stem: pd.read_parquet(f) for f in sorted(Path(folder).glob("*.parquet"))}


def to_json(state: dict) -> str:
    def clean(x):
        if isinstance(x, dict):
            return {k: clean(v) for k, v in x.items()}
        if isinstance(x, list):
            return [clean(v) for v in x]
        if isinstance(x, (np.floating, float)):
            return None if not np.isfinite(x) else round(float(x), 6)
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, np.bool_):
            return bool(x)
        return x
    return json.dumps(clean(state), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
