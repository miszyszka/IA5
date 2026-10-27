"""Silnik backtestu (CLAUDE.md sekcja 8, zasady B1–B8).

Model wykonania:
- B1: sygnał na zamknięciu świecy t → wejście na open świecy t+1.
- TP/SL sprawdzane wewnątrz świecy (high/low); TP i SL w tej samej świecy → resolver M1, inaczej SL + ambiguous (B5).
- B6: open za SL → wyjście po open; open za TP → wyjście po poziomie TP.
- Wyjście czasowe po N świecach: zamknięcie świecy e+N-1.
- Wyjścia wskaźnikowe (RSI 50, SMA, sygnał przeciwny): warunek na zamknięciu świecy j → wyjście na open j+1.
- B8: jedna pozycja na parę na wariant; nowe wejście tylko na świecy późniejszej niż świeca wyjścia.
  Strategia może pozwolić na dokładanie (PYRAMID = k, D-034): do k pozycji naraz w parze, tylko w jednym kierunku.
- Waga pozycji (D-034): |sygnał| (domyślnie 1) mnoży depozyt w symulacji kapitału; pipsy i R są na pozycję.
- Wyjście „seria RSI” (D-034): RSI14 przez `run` kolejnych zamknięć po złej stronie poziomu → wyjście na open następnej.
- Transakcje, którym zabrakło danych do wyjścia, są odrzucane i liczone.

Obliczenia są wektorowe (numpy) po wszystkich wejściach naraz, osobno dla każdego wariantu wyjścia.
"""
from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import PAIRS
from .session import in_trading_hours

W = 120  # najdłuższe trzymanie pozycji w świecach
H = 3600


@dataclass(frozen=True)
class Exit:
    kind: str          # time | atr | rsi50 | sma | opposite | rsi_streak
    n: int = 14        # time: N świec; atr: okres ATR
    tp: float = 0.0    # × ATR (tylko atr)
    sl: float = 0.0    # × ATR(n) dla atr, × ATR(14) dla wskaźnikowych; 0 = bez SL
    cap: int = W       # limit czasu w świecach (B7)
    run: int = 0       # rsi_streak: ile kolejnych zamknięć RSI14 po złej stronie poziomu zamyka pozycję
    level: float = 0.0  # rsi_streak: poziom dla short (np. 70); dla long lustrzany 100 − level (30)

    @property
    def family(self) -> str:
        return {"time": "czas", "atr": "ATR"}.get(self.kind, "wskaźnik")

    def label(self) -> str:
        if self.kind == "time":
            return f"po {self.n} świecach"
        if self.kind == "atr":
            return f"ATR{self.n} TP {self.tp:g}× SL {self.sl:g}× max {self.cap}"
        if self.kind == "rsi_streak":
            tp = f"TP {self.tp:g}×ATR{self.n}, " if self.tp > 0 else ""
            sl = f"SL {self.sl:g}×ATR14, " if self.sl > 0 else ""
            return f"{tp}{sl}RSI {self.run} świec za {self.level:g}/{100 - self.level:g}, max {self.cap}"
        name = {"rsi50": "RSI do 50", "sma": "cena przez SMA20", "opposite": "sygnał przeciwny"}[self.kind]
        return f"{name}, SL {self.sl:g}×ATR14, max {self.cap}"


def default_exits() -> list[Exit]:
    """Domyślna siatka wyjść (CLAUDE.md 8.2): 14 czasowych + 210 ATR + 9 wskaźnikowych = 233."""
    ex = [Exit("time", n=N, cap=N) for N in (1, 2, 3, 4, 6, 8, 12, 16, 24, 36, 48, 72, 96, 120)]
    for n, tp, sl, cap in itertools.product((5, 14), (0.5, 0.75, 1, 1.5, 2, 3, 4), (0.5, 1, 1.5, 2, 3), (24, 72, 120)):
        ex.append(Exit("atr", n=n, tp=tp, sl=sl, cap=cap))
    for kind, sl in itertools.product(("rsi50", "sma", "opposite"), (1, 2, 3)):
        ex.append(Exit(kind, n=14, sl=sl, cap=W))
    return ex


# ---------- przygotowanie danych pary ----------

def prepare(df: pd.DataFrame) -> dict:
    """Tablice pary + wskaźniki potrzebne wyjściom (liczone raz)."""
    df = df.reset_index(drop=True)
    return {
        "ts": df["ts"].to_numpy(np.int64),
        "o": df["open"].to_numpy(float), "h": df["high"].to_numpy(float),
        "l": df["low"].to_numpy(float), "c": df["close"].to_numpy(float),
        "atr5": ind.atr(df, 5).to_numpy(), "atr14": ind.atr(df, 14).to_numpy(),
        "rsi14": ind.rsi(df["close"], 14).to_numpy(),
        "sma20": ind.sma(df["close"], 20).to_numpy(),
        # D-031: warstwa czyszczenia (clean.py) — świece uzupełnione i długie luki; brak kolumn = dane bez luk
        "filled": df["filled"].to_numpy(bool) if "filled" in df else np.zeros(len(df), bool),
        "gapcum": np.concatenate([[0], np.cumsum(df["gap_before"].to_numpy(np.int64) > 0)])
        if "gap_before" in df else np.zeros(len(df) + 1, np.int64),
    }


def data_cancel(P: dict, signal_i: np.ndarray, entry_i: np.ndarray, exit_i: np.ndarray, split: bool = False):
    """D-031/D-032: transakcje do anulowania — nachodzą na przerwę w dostępie do danych (od świecy wejścia do wyjścia
    włącznie, także przerwa między sygnałem a wejściem) albo jej świeca sygnału, wejścia lub wyjścia jest uzupełniona.
    Weekend i godziny bez notowań nie są przerwą (clean.py nie oznacza ich w gap_before).
    split=True → (przerwa, uzupełniona) osobno."""
    xi = np.asarray(exit_i, float)
    ok = ~np.isnan(xi)
    e = np.asarray(entry_i, np.int64)
    x = np.where(ok, xi, e).astype(np.int64)
    gc, f = P["gapcum"], P["filled"]
    gap = ok & (gc[x + 1] - gc[e] > 0)
    fill = ok & ~gap & (f[np.asarray(signal_i, np.int64)] | f[e] | f[x])
    return (gap, fill) if split else gap | fill


def find_entries(P: dict, sig: np.ndarray) -> pd.DataFrame:
    """B1: sygnał w świecy i → wejście na open świecy i+1."""
    v = np.nan_to_num(np.asarray(sig, float))
    i = np.flatnonzero(v != 0)
    i = i[i + 1 < len(P["o"])]
    e = i + 1
    return pd.DataFrame({
        "signal_i": i, "entry_i": e, "dir": np.sign(v[i]).astype(np.int8), "weight": np.abs(v[i]),
        "signal_ts": P["ts"][i], "entry_ts": P["ts"][e], "entry_px": P["o"][e],
        "atr5": P["atr5"][i], "atr14": P["atr14"][i],
    })


def _windows(P: dict, e: np.ndarray, d: np.ndarray, width: int) -> dict:
    """Okna cen od świecy wejścia, w przestrzeni „long" (dla short ceny odwrócone znakiem)."""
    n = len(P["o"])
    idx = e[:, None] + np.arange(width)[None, :]
    ok = idx < n
    idx = np.where(ok, idx, n - 1)
    sgn = d[:, None].astype(float)

    def take(a):
        w = a[idx]
        return np.where(ok, w, np.nan)

    o, h, lo, c = take(P["o"]), take(P["h"]), take(P["l"]), take(P["c"])
    long_ = sgn > 0
    return {
        "idx": idx, "ok": ok,
        "O": o * sgn, "C": c * sgn,
        "H": np.where(long_, h, -lo), "L": np.where(long_, lo, -h),
        "rsi": take(P["rsi14"]), "sma": take(P["sma20"]) * sgn, "c_raw": c,
    }


def _streak(x: np.ndarray) -> np.ndarray:
    """Długość bieżącej serii True kończącej się w każdej świecy (0 gdy False)."""
    out = np.zeros(len(x), np.int64)
    run = 0
    for k, v in enumerate(x):
        run = run + 1 if v else 0
        out[k] = run
    return out


def _first(mask: np.ndarray) -> np.ndarray:
    """Indeks pierwszego True w wierszu; brak = szerokość."""
    has = mask.any(axis=1)
    return np.where(has, mask.argmax(axis=1), mask.shape[1])


def simulate(P: dict, ent: pd.DataFrame, ex: Exit, pair: str, opp: np.ndarray | None = None,
             resolver=None) -> pd.DataFrame:
    """Wynik każdego wejścia dla jednego wariantu wyjścia (bez filtra B8)."""
    m = len(ent)
    cols = ["exit_i", "exit_ts", "exit_px", "reason", "pips_gross", "r", "risk_pips", "mae", "mfe", "bars", "ambiguous"]
    if m == 0:
        return pd.DataFrame(columns=cols)
    pip = PAIRS[pair].pip
    e = ent["entry_i"].to_numpy()
    d = ent["dir"].to_numpy().astype(int)
    cap = ex.cap
    w = _windows(P, e, d, cap + 1)
    En = ent["entry_px"].to_numpy() * d
    atr = ent[f"atr{ex.n}" if ex.kind in ("atr", "rsi_streak") else "atr14"].to_numpy()

    # opcjonalny limit świec dla każdego wejścia osobno (kolumna max_bars); domyślnie limit wariantu
    cap_r = np.clip(ent["max_bars"].to_numpy(np.int64), 1, cap) if "max_bars" in ent else np.full(m, cap)
    beyond = np.arange(cap)[None, :] >= cap_r[:, None]
    tp = En + ex.tp * atr if ex.kind == "atr" or (ex.kind == "rsi_streak" and ex.tp > 0) else np.full(m, np.inf)
    sl = En - ex.sl * atr if ex.sl > 0 else np.full(m, -np.inf)
    Hw, Lw, Ow = w["H"][:, :cap], w["L"][:, :cap], w["O"][:, :cap]
    hit_sl = Lw <= sl[:, None]
    hit_tp = Hw >= tp[:, None]
    gap_sl = Ow <= sl[:, None]
    gap_tp = Ow >= tp[:, None]
    gap_sl[:, 0] = gap_tp[:, 0] = False
    hit_sl &= ~beyond
    hit_tp &= ~beyond
    gap_sl &= ~beyond
    gap_tp &= ~beyond

    # warunek wyjścia wskaźnikowego na zamknięciu świecy j → wyjście na open j+1
    xs = np.zeros((m, cap), bool)
    if ex.kind == "rsi50":
        r = w["rsi"][:, :cap]
        xs = np.where(d[:, None] > 0, r >= 50, r <= 50)
    elif ex.kind == "sma":
        xs = w["C"][:, :cap] < w["sma"][:, :cap]
    elif ex.kind == "rsi_streak":
        key = ("streak", ex.level)
        if key not in P:  # liczone raz na parę i poziom
            r = np.nan_to_num(P["rsi14"], nan=50.0)
            P[key] = (_streak(r > ex.level), _streak(r < 100 - ex.level))
        up, dn = P[key]
        wi = w["idx"][:, :cap]
        xs = np.where(d[:, None] < 0, up[wi], dn[wi]) >= ex.run
        xs &= w["ok"][:, :cap]
    elif ex.kind == "opposite" and opp is not None:
        o_sig = np.sign(np.nan_to_num(opp[w["idx"][:, :cap]])).astype(int)
        xs = (o_sig == -d[:, None]) & w["ok"][:, :cap]
    if cap > 0:
        xs = xs & ~beyond
        xs[np.arange(m), cap_r - 1] = False  # na ostatniej świecy i tak kończy limit czasu

    f_hit = _first(hit_sl | hit_tp)
    f_x = _first(xs)
    out = {k: np.full(m, np.nan) for k in ("exit_i", "exit_ts", "exit_px", "pips_gross", "r", "risk_pips", "mae", "mfe",
                                           "bars")}
    reason = np.full(m, "", dtype=object)
    amb = np.zeros(m, bool)
    rows = np.arange(m)
    exit_n = np.full(m, np.nan)
    exit_j = np.full(m, -1)
    exit_at_open = np.zeros(m, bool)

    # 1) zdarzenie TP/SL wewnątrz świecy
    stop = (f_hit < cap) & (f_hit <= f_x)
    j = np.minimum(f_hit, cap - 1)
    gs, gt = gap_sl[rows, j], gap_tp[rows, j]
    hs, ht = hit_sl[rows, j], hit_tp[rows, j]
    both = stop & ~gs & ~gt & hs & ht
    for k in np.flatnonzero(both):
        res = None
        if resolver is not None:
            bar_ts = int(P["ts"][w["idx"][k, j[k]]])
            res = resolver(pair, bar_ts, int(d[k]), float(tp[k] * d[k]), float(sl[k] * d[k]))
        if res == "tp":
            hs[k] = False
        else:
            ht[k] = False
            amb[k] = res is None
    is_sl = stop & (gs | (hs & ~gt))
    is_tp = stop & ~is_sl
    exit_n = np.where(is_sl, np.where(gs, Ow[rows, j], sl), exit_n)
    exit_n = np.where(is_tp, tp, exit_n)
    reason[is_sl] = "SL"
    reason[is_tp] = "TP"
    exit_j = np.where(stop, j, exit_j)

    # 2) wyjście wskaźnikowe na open następnej świecy
    xw = ~stop & (f_x < cap_r - 1)
    jx = np.minimum(f_x + 1, cap)
    exit_n = np.where(xw, w["O"][rows, jx], exit_n)
    exit_j = np.where(xw, jx, exit_j)
    exit_at_open |= xw
    reason[xw] = {"rsi50": "RSI50", "sma": "SMA", "opposite": "przeciwny", "rsi_streak": "seria RSI"}.get(ex.kind, "")

    # 3) limit czasu: zamknięcie świecy cap-1
    tw = ~stop & ~xw
    exit_n = np.where(tw, w["C"][rows, cap_r - 1], exit_n)
    exit_j = np.where(tw, cap_r - 1, exit_j)
    reason[tw] = "czas"

    done = ~np.isnan(exit_n)
    # MAE/MFE: świece przed świecą wyjścia + cena wyjścia
    cmaxH = np.fmax.accumulate(np.where(np.isnan(w["H"]), -np.inf, w["H"]), axis=1)
    cminL = np.fmin.accumulate(np.where(np.isnan(w["L"]), np.inf, w["L"]), axis=1)
    jj = np.clip(exit_j - 1, 0, None)
    prev_max = np.where(exit_j > 0, cmaxH[rows, jj], -np.inf)
    prev_min = np.where(exit_j > 0, cminL[rows, jj], np.inf)
    # świeca wyjścia wewnątrz-świecowego/czasowego sama też należy do przebiegu pozycji
    in_bar = ~exit_at_open
    jb = np.clip(exit_j, 0, cap)
    timed = reason == "czas"
    bar_max = np.where(in_bar & timed, w["H"][rows, jb], -np.inf)
    bar_min = np.where(in_bar & timed, w["L"][rows, jb], np.inf)
    mfe = np.maximum.reduce([prev_max, bar_max, exit_n, En]) - En
    mae = En - np.minimum.reduce([prev_min, bar_min, exit_n, En])

    gross = exit_n - En
    risk = np.where(ex.sl > 0, ex.sl * atr, ent["atr14"].to_numpy())
    bar_idx = w["idx"][rows, np.clip(exit_j, 0, cap)]
    out["exit_i"] = np.where(done, bar_idx, np.nan)
    out["exit_ts"] = np.where(done, P["ts"][bar_idx] + np.where(exit_at_open, 0, H), np.nan)
    out["exit_px"] = exit_n * d
    out["pips_gross"] = gross / pip
    out["r"] = gross / risk
    out["risk_pips"] = risk / pip
    out["mae"] = mae / pip
    out["mfe"] = mfe / pip
    out["bars"] = np.where(done, exit_j + np.where(exit_at_open, 0, 1), np.nan)
    df = pd.DataFrame(out)
    df["reason"] = reason
    df["ambiguous"] = amb
    df.loc[~done, "reason"] = "brak danych"
    return df[cols]


def no_overlap(entry_i: np.ndarray, exit_i: np.ndarray, dirs: np.ndarray | None = None, cap: int = 1) -> np.ndarray:
    """B8: maska wykonanych wejść (kolejność rosnąca entry_i). cap = najwięcej pozycji naraz w parze (PYRAMID, D-034);
    pozycja jest otwarta do swojej świecy wyjścia włącznie; dokładać można tylko w kierunku już otwartych pozycji."""
    keep = np.zeros(len(entry_i), bool)
    open_: list[tuple[float, int]] = []
    for k in range(len(entry_i)):
        if np.isnan(exit_i[k]):
            continue
        open_ = [o for o in open_ if o[0] >= entry_i[k]]
        d = int(dirs[k]) if dirs is not None else 0
        if len(open_) < cap and all(o[1] == d for o in open_):
            keep[k] = True
            open_.append((exit_i[k], d))
    return keep


# ---------- uruchomienie dla strategii ----------

def run(h1: dict[str, pd.DataFrame], signals: dict[tuple[int, str], np.ndarray], params: list[dict],
        exits: list[Exit] | None = None, resolver=None, oos_frac: float = 0.25, hours=None, pyramid: int = 1) -> dict:
    """Pełny przebieg: wszystkie warianty wejścia (params) × wszystkie wyjścia × wszystkie pary.

    signals[(param_id, pair)] = tablica sygnałów (+1/-1/0) na świecach h1[pair].
    Zwraca tabele entries, outcomes, variants i liczniki.
    """
    exits = exits or default_exits()
    preps = {p: prepare(df) for p, df in h1.items()}
    t0 = min(int(df["ts"].iloc[0]) for df in h1.values())
    t1 = max(int(df["ts"].iloc[-1]) for df in h1.values())
    cutoff = t0 + (1 - oos_frac) * (t1 - t0)

    ent_frames, out_frames = [], []
    skipped = {"B8": 0, "brak_danych": 0, "rozgrzewka": 0, "poza_godzinami": 0, "luka_danych": 0,
               "swieca_uzupelniona": 0}
    eid = 0
    for (pid, pair), sig in signals.items():
        P = preps[pair]
        ent = find_entries(P, sig)
        warm = ent["atr14"].isna() | ent["atr5"].isna()  # bez ATR nie ma poziomów TP/SL ani R
        skipped["rozgrzewka"] += int(warm.sum())
        # B11: wejście tylko w oknie handlu 07:00–17:00 czasu polskiego (D-028); wyjście na dowolnej świecy (D-032)
        outside = ~in_trading_hours(ent["entry_ts"].to_numpy(), hours) & ~warm.to_numpy()
        skipped["poza_godzinami"] += int(outside.sum())
        ent = ent[~warm.to_numpy() & ~outside].reset_index(drop=True)
        if ent.empty:
            continue
        ent.insert(0, "entry_id", np.arange(eid, eid + len(ent)))
        ent.insert(1, "param_id", pid)
        ent.insert(2, "pair", pair)
        ent["sample"] = np.where(ent["entry_ts"] < cutoff, "IS", "OOS")
        eid += len(ent)
        ent_frames.append(ent)
        for xid, ex in enumerate(exits):
            res = simulate(P, ent, ex, pair, opp=np.asarray(sig), resolver=resolver)
            missing = res["exit_i"].isna().to_numpy()
            # D-031: transakcja nachodząca na długą lukę albo na świecę uzupełnioną — anulowana, jakby jej nie było
            gap, fill = data_cancel(P, ent["signal_i"].to_numpy(), ent["entry_i"].to_numpy(), res["exit_i"].to_numpy(float),
                                    split=True)
            cancel = gap | fill
            xi = res["exit_i"].to_numpy(float).copy()
            xi[cancel] = np.nan
            keep = no_overlap(ent["entry_i"].to_numpy(), xi, ent["dir"].to_numpy(), pyramid)
            skipped["brak_danych"] += int(missing.sum())
            skipped["luka_danych"] += int(gap.sum())
            skipped["swieca_uzupelniona"] += int(fill.sum())
            skipped["B8"] += int((~keep & ~missing & ~cancel).sum())
            res = res[keep].copy()
            res.insert(0, "variant_id", pid * len(exits) + xid)
            res.insert(1, "entry_id", ent["entry_id"].to_numpy()[keep])
            out_frames.append(res)

    entries = pd.concat(ent_frames, ignore_index=True) if ent_frames else pd.DataFrame()
    outcomes = pd.concat(out_frames, ignore_index=True) if out_frames else pd.DataFrame()
    if not outcomes.empty:
        meta = entries.set_index("entry_id")[["pair", "sample"]]
        outcomes = outcomes.join(meta, on="entry_id")
        spread = outcomes["pair"].map({p: c.spread_pips for p, c in PAIRS.items()})
        outcomes["pips_net"] = outcomes["pips_gross"] - spread  # B3: spread jednorazowo
        outcomes["r_net"] = outcomes["pips_net"] / outcomes["risk_pips"]  # R po spreadzie
    variants = pd.DataFrame([
        {"variant_id": pid * len(exits) + xid, "param_id": pid, "params": params[pid],
         "family": ex.family, "exit": ex.label(), **{f"x_{k}": v for k, v in asdict(ex).items()}}
        for pid in range(len(params)) for xid, ex in enumerate(exits)
    ])
    return {"entries": entries, "outcomes": outcomes, "variants": variants, "preps": preps,
            "skipped": skipped, "cutoff": cutoff, "n_variants": len(variants)}


def summarize(outcomes: pd.DataFrame, by=("variant_id",)) -> pd.DataFrame:
    """Podstawowe metryki przewagi transakcji (bez symulacji kapitału — 8.5)."""
    if outcomes.empty:
        return pd.DataFrame()

    def agg(g):
        p = g["pips_net"]
        wins, losses = p[p > 0].sum(), -p[p < 0].sum()
        n = len(p)
        sd = p.std(ddof=1) if n > 1 else np.nan
        return pd.Series({
            "trades": n,
            "win_rate": (p > 0).mean(),
            "exp_pips": p.mean(),
            "exp_r": g["r_net"].mean(),
            "profit_factor": wins / losses if losses > 0 else np.inf,
            "sum_pips": p.sum(),
            "t_stat": p.mean() / (sd / np.sqrt(n)) if n > 1 and sd > 0 else np.nan,
            "ambiguous_pct": g["ambiguous"].mean(),
            "avg_bars": g["bars"].mean(),
        })

    return outcomes.groupby(list(by)).apply(agg, include_groups=False).reset_index()


def _m1_arrays(df: pd.DataFrame):
    return (df["ts"].to_numpy(np.int64), ((df["bh"] + df["ah"]) / 2).to_numpy(), ((df["bl"] + df["al"]) / 2).to_numpy())


def _resolve(arrays, bar_ts, d, tp, sl):
    """Pierwsza minuta świecy, w której pada TP albo SL (ceny mid). Obie w tej samej minucie → None."""
    ts, hi, lo = arrays
    a, b = np.searchsorted(ts, [bar_ts, bar_ts + H])
    for k in range(a, b):
        hit_tp = hi[k] >= tp if d > 0 else lo[k] <= tp
        hit_sl = lo[k] <= sl if d > 0 else hi[k] >= sl
        if hit_tp and hit_sl:
            return None
        if hit_sl:
            return "sl"
        if hit_tp:
            return "tp"
    return None


def m1_resolver(m1: dict[str, pd.DataFrame]):
    """B5: kolejność TP/SL w świecy H1 rozstrzygana na M1 (ceny mid). Ta sama minuta → None (SL + ambiguous)."""
    cache = {pair: _m1_arrays(df) for pair, df in m1.items()}

    def resolve(pair, bar_ts, d, tp, sl):
        return _resolve(cache[pair], bar_ts, d, tp, sl) if pair in cache else None

    return resolve


def m1_resolver_lazy(m1_dir):
    """Jak m1_resolver, ale czyta miesięczne pliki M1 (data/m1/{PARA}/{RRRR-MM}.parquet) dopiero, gdy są potrzebne."""
    from collections import OrderedDict
    from datetime import UTC, datetime
    from pathlib import Path

    cache: OrderedDict = OrderedDict()

    def resolve(pair, bar_ts, d, tp, sl):
        ym = datetime.fromtimestamp(bar_ts, UTC).strftime("%Y-%m")
        key = (pair, ym)
        if key not in cache:
            f = Path(m1_dir) / pair / f"{ym}.parquet"
            cache[key] = _m1_arrays(pd.read_parquet(f)) if f.exists() else None
            if len(cache) > 48:
                cache.popitem(last=False)
        return _resolve(cache[key], bar_ts, d, tp, sl) if cache[key] is not None else None

    return resolve
