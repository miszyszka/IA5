"""Silnik backtestu (CLAUDE.md sekcja 8, zasady B1–B8).

Model wykonania:
- B1: sygnał na zamknięciu świecy t → wejście na open świecy t+1.
- TP/SL sprawdzane wewnątrz świecy (high/low); TP i SL w tej samej świecy → SL + ambiguous (B5, pesymistycznie).
- B6: open za SL → wyjście po open; open za TP → wyjście po poziomie TP.
- Wyjście czasowe po N świecach: zamknięcie świecy e+N-1.
- Wyjścia wskaźnikowe (RSI 50, SMA, sygnał przeciwny): warunek na zamknięciu świecy j → wyjście na open j+1.
- B8: jedna pozycja na parę na wariant; nowe wejście tylko na świecy późniejszej niż świeca wyjścia.
  Strategia może pozwolić na dokładanie (PYRAMID = k, D-034): do k pozycji naraz w parze, tylko w jednym kierunku.
- Waga pozycji (D-034): |sygnał| (domyślnie 1) mnoży depozyt w symulacji kapitału; pipsy i R są na pozycję.
- Stop kroczący (D-035): stop w świecy j = max(SL początkowy, najwyższe high świec przed j − trail × ATR);
  liczony tylko z zamkniętych świec, więc nigdy nie zakłada, że szczyt świecy padł przed jej dołkiem.
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
from .session import in_trading_hours, nights

W = 120  # najdłuższe trzymanie pozycji w świecach
UNLIMITED_CELLS = 6_000_000   # D-061: wyjście bez limitu czasu — najwyżej tyle komórek (wejścia × świece) okna cen naraz
H = 3600


@dataclass(frozen=True)
class Exit:
    kind: str          # time | atr | rsi50 | sma | opposite | rsi_streak | trail | level
    n: int = 14        # time: N świec; atr: okres ATR
    tp: float = 0.0    # × ATR (tylko atr)
    sl: float = 0.0    # × ATR(n) dla atr, × ATR(14) dla wskaźnikowych; 0 = bez SL
    cap: int = W       # limit czasu w świecach (B7); 0 = bez limitu — tylko kind "level", na wyraźne życzenie Michała (D-061)
    run: int = 0       # rsi_streak: ile kolejnych zamknięć RSI14 po złej stronie poziomu zamyka pozycję
    level: float = 0.0  # rsi_streak: poziom dla short (np. 70); dla long lustrzany 100 − level (30)
    trail: float = 0.0  # trail: odległość stopu kroczącego od najwyższego high (long) w × ATR(n)

    @property
    def family(self) -> str:
        return {"time": "czas", "atr": "ATR", "trail": "stop kroczący", "level": "poziomy"}.get(self.kind, "wskaźnik")

    def label(self) -> str:
        if self.kind == "time":
            return f"po {self.n} świecach"
        if self.kind == "level":
            return "poziomy TP/SL ze strategii, bez limitu czasu" if self.cap == 0 else f"poziomy TP/SL ze strategii, max {self.cap}"
        if self.kind == "atr":
            return f"ATR{self.n} TP {self.tp:g}× SL {self.sl:g}× max {self.cap}"
        if self.kind == "trail":
            tp = f" TP {self.tp:g}×," if self.tp > 0 else ""
            return f"ATR{self.n} SL {self.sl:g}× kroczący {self.trail:g}×{tp} max {self.cap}"
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
        # D-058: czas zamknięcia świecy — H1: open + 1 h; D1: północ następnego dnia w Londynie (kolumna close_ts z clean_d1)
        "cts": df["close_ts"].to_numpy(np.int64) if "close_ts" in df else df["ts"].to_numpy(np.int64) + H,
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


def find_entries(P: dict, sig: np.ndarray, lv: np.ndarray | None = None) -> pd.DataFrame:
    """B1: sygnał w świecy i → wejście na open świecy i+1.
    lv (D-057): tablica (n, 2) cen TP/SL z levels() na świecy sygnału; NaN = brak poziomu."""
    v = np.nan_to_num(np.asarray(sig, float))
    i = np.flatnonzero(v != 0)
    i = i[i + 1 < len(P["o"])]
    e = i + 1
    ent = pd.DataFrame({
        "signal_i": i, "entry_i": e, "dir": np.sign(v[i]).astype(np.int8), "weight": np.abs(v[i]),
        "signal_ts": P["ts"][i], "entry_ts": P["ts"][e], "entry_px": P["o"][e],
        "atr5": P["atr5"][i], "atr14": P["atr14"][i],
    })
    if lv is not None:
        lv = np.asarray(lv, float)
        ent["tp_px"], ent["sl_px"] = lv[i, 0], lv[i, 1]
    return ent


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


def simulate(P: dict, ent: pd.DataFrame, ex: Exit, pair: str, opp: np.ndarray | None = None) -> pd.DataFrame:
    """Wynik każdego wejścia dla jednego wariantu wyjścia (bez filtra B8)."""
    m = len(ent)
    cols = ["exit_i", "exit_ts", "exit_px", "reason", "pips_gross", "r", "risk_pips", "mae", "mfe", "bars", "nights", "ambiguous"]
    if m == 0:
        return pd.DataFrame(columns=cols)
    pip = PAIRS[pair].pip
    e = ent["entry_i"].to_numpy()
    d = ent["dir"].to_numpy().astype(int)
    n_bars = len(P["o"])
    unlimited = ex.cap == 0   # D-061: bez limitu czasu — do TP albo do końca danych (wtedy „otwarta”, wycena po ostatnim close)
    if unlimited:
        if ex.kind != "level":
            raise ValueError("cap = 0 (bez limitu czasu) tylko dla wyjścia level")
        if m > 1 and m * (n_bars - int(e.min()) + 1) > UNLIMITED_CELLS:   # pamięć: okna cen m × świec — liczymy porcjami wejść
            half = max(1, UNLIMITED_CELLS // max(1, n_bars - int(e.min()) + 1))
            parts = [simulate(P, ent.iloc[k:k + half], ex, pair, opp) for k in range(0, m, half)]
            return pd.concat(parts, ignore_index=True)
    cap = n_bars - int(e.min()) if unlimited else ex.cap
    w = _windows(P, e, d, cap + 1)
    En = ent["entry_px"].to_numpy() * d
    atr = ent[f"atr{ex.n}" if ex.kind in ("atr", "rsi_streak", "trail") else "atr14"].to_numpy()

    # opcjonalny limit świec dla każdego wejścia osobno (kolumna max_bars); domyślnie limit wariantu
    cap_r = np.clip(ent["max_bars"].to_numpy(np.int64), 1, cap) if "max_bars" in ent else np.full(m, cap)
    if unlimited:   # ostatnia dostępna świeca każdego wejścia = koniec danych
        cap_r = np.minimum(cap_r, n_bars - e)
    beyond = np.arange(cap)[None, :] >= cap_r[:, None]
    if ex.kind == "level":
        # D-057: poziomy w cenie ze strategii (świeca sygnału), w przestrzeni „long” (× kierunek); brak poziomu = brak TP/SL
        tp_px = ent["tp_px"].to_numpy(float) if "tp_px" in ent else np.full(m, np.nan)
        sl_px = ent["sl_px"].to_numpy(float) if "sl_px" in ent else np.full(m, np.nan)
        tp = np.where(np.isnan(tp_px), np.inf, tp_px * d)
        sl = np.where(np.isnan(sl_px), -np.inf, sl_px * d)
    else:
        tp = En + ex.tp * atr if ex.kind == "atr" or (ex.kind in ("rsi_streak", "trail") and ex.tp > 0) else np.full(m, np.inf)
        sl = En - ex.sl * atr if ex.sl > 0 else np.full(m, -np.inf)
    Hw, Lw, Ow = w["H"][:, :cap], w["L"][:, :cap], w["O"][:, :cap]
    if ex.kind == "trail":
        # najwyższe high świec PRZED świecą j (w świecy wejścia: cena wejścia)
        hh = np.fmax.accumulate(np.where(np.isnan(Hw), -np.inf, Hw), axis=1)
        prev = np.maximum(np.concatenate([En[:, None], hh[:, :-1]], axis=1), En[:, None])
        SLm = np.maximum(sl[:, None], prev - ex.trail * atr[:, None])
    else:
        SLm = np.broadcast_to(sl[:, None], (m, cap))
    hit_sl = Lw <= SLm
    hit_tp = Hw >= tp[:, None]
    gap_sl = Ow <= SLm
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
    # B5 (D-039): TP i SL w tej samej świecy H1 — kolejności nie znamy (brak danych wewnątrz świecy) → SL + ambiguous
    both = stop & ~gs & ~gt & hs & ht
    ht = ht & ~both
    amb[both] = True
    is_sl = stop & (gs | (hs & ~gt))
    is_tp = stop & ~is_sl
    sl_j = SLm[rows, j]
    exit_n = np.where(is_sl, np.where(gs, Ow[rows, j], sl_j), exit_n)
    exit_n = np.where(is_tp, tp, exit_n)
    reason[is_sl] = "SL"
    reason[is_sl & (sl_j > sl + 1e-12)] = "stop kroczący"
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
    reason[tw] = "otwarta" if unlimited else "czas"   # D-061: bez limitu, koniec danych — pozycja otwarta, wycena po ostatnim close

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
    timed = (reason == "czas") | (reason == "otwarta")
    bar_max = np.where(in_bar & timed, w["H"][rows, jb], -np.inf)
    bar_min = np.where(in_bar & timed, w["L"][rows, jb], np.inf)
    mfe = np.maximum.reduce([prev_max, bar_max, exit_n, En]) - En
    mae = En - np.minimum.reduce([prev_min, bar_min, exit_n, En])

    gross = exit_n - En
    if ex.kind == "level":   # R względem odległości do SL ze strategii; bez SL — względem 1 × ATR14 (8.4)
        risk = np.where(np.isfinite(sl) & (En - sl > 0), En - sl, ent["atr14"].to_numpy())
    else:
        risk = np.where(ex.sl > 0, ex.sl * atr, ent["atr14"].to_numpy())
    bar_idx = w["idx"][rows, np.clip(exit_j, 0, cap)]
    out["exit_i"] = np.where(done, bar_idx, np.nan)
    out["exit_ts"] = np.where(done, np.where(exit_at_open, P["ts"][bar_idx], P["cts"][bar_idx]), np.nan)
    out["exit_px"] = exit_n * d
    out["pips_gross"] = gross / pip
    out["r"] = gross / risk
    out["risk_pips"] = risk / pip
    out["mae"] = mae / pip
    out["mfe"] = mfe / pip
    out["bars"] = np.where(done, exit_j + np.where(exit_at_open, 0, 1), np.nan)
    # D-054: noce przez 21:00 UTC — koszt swapu, którego model nie liczy (O5); do stresu w walidacji i raporcie
    out["nights"] = np.where(done, nights(P["ts"][e].astype(float), out["exit_ts"]), np.nan)
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


def no_overlap_pairs(pair: np.ndarray, entry_ts: np.ndarray, entry_i: np.ndarray, exit_i: np.ndarray,
                     exit_bar_ts: np.ndarray, dirs: np.ndarray, rank: np.ndarray, cap: int = 1,
                     max_pairs: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """D-050: B8 w każdej parze (jak no_overlap) + najwyżej `max_pairs` par z otwartymi pozycjami naraz w całym wariancie.

    Wejścia rozpatrywane po kolei w czasie; przy tej samej świecy wejścia wygrywa para z niższym `rank` (ranking z IS,
    podany przez strategię). Para jest zajęta od wejścia do swojej świecy wyjścia włącznie; w zajętej parze wolno
    dokładać w tym samym kierunku (PYRAMID). Zwraca (wykonane, pominięte przez limit par)."""
    n = len(entry_ts)
    keep = np.zeros(n, bool)
    blocked = np.zeros(n, bool)
    order = np.lexsort((rank, entry_ts))
    open_: dict = {}                     # para → lista (exit_i, kierunek, ts świecy wyjścia)
    for k in order:
        if np.isnan(exit_i[k]):
            continue
        t = entry_ts[k]
        for q in list(open_):            # zamknięte pozycje zwalniają parę po swojej świecy wyjścia
            open_[q] = [o for o in open_[q] if o[2] >= t]
            if not open_[q]:
                del open_[q]
        mine = [o for o in open_.get(pair[k], []) if o[0] >= entry_i[k]]
        d = int(dirs[k])
        if not (len(mine) < cap and all(o[1] == d for o in mine)):
            continue                     # B8 w parze
        if pair[k] not in open_ and len(open_) >= max_pairs:
            blocked[k] = True            # limit par
            continue
        keep[k] = True
        open_.setdefault(pair[k], []).append((exit_i[k], d, exit_bar_ts[k]))
    return keep, blocked


# ---------- uruchomienie dla strategii ----------

def run(h1: dict[str, pd.DataFrame], signals: dict[tuple[int, str], np.ndarray], params: list[dict],
        exits: list[Exit] | None = None, oos_frac: float = 0.25, hours=None, pyramid: int = 1,
        max_pairs: int | None = None, pair_rank: list[str] | None = None,
        levels: dict[tuple[int, str], np.ndarray] | None = None) -> dict:
    """Pełny przebieg: wszystkie warianty wejścia (params) × wszystkie wyjścia × wszystkie pary.

    signals[(param_id, pair)] = tablica sygnałów (+1/-1/0) na świecach h1[pair].
    levels[(param_id, pair)] (D-057) = tablica (n, 2) cen TP/SL na świecy sygnału dla wyjść rodzaju „level”.
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
    if max_pairs:
        skipped["limit_par"] = 0
    pending: dict = {}   # D-050: kandydaci wariantu ze wszystkich par, rozstrzygani razem po pętli
    eid = 0
    for (pid, pair), sig in signals.items():
        P = preps[pair]
        ent = find_entries(P, sig, (levels or {}).get((pid, pair)))
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
            res = simulate(P, ent, ex, pair, opp=np.asarray(sig))
            missing = res["exit_i"].isna().to_numpy()
            # D-031: transakcja nachodząca na długą lukę albo na świecę uzupełnioną — anulowana, jakby jej nie było
            gap, fill = data_cancel(P, ent["signal_i"].to_numpy(), ent["entry_i"].to_numpy(), res["exit_i"].to_numpy(float),
                                    split=True)
            cancel = gap | fill
            xi = res["exit_i"].to_numpy(float).copy()
            xi[cancel] = np.nan
            skipped["brak_danych"] += int(missing.sum())
            skipped["luka_danych"] += int(gap.sum())
            skipped["swieca_uzupelniona"] += int(fill.sum())
            if max_pairs:
                xb = np.where(np.isnan(xi), np.inf, P["ts"][np.nan_to_num(xi, nan=0).astype(np.int64)])
                pending.setdefault((pid, xid), []).append((pair, ent, res, xi, xb, missing | cancel))
                continue
            keep = no_overlap(ent["entry_i"].to_numpy(), xi, ent["dir"].to_numpy(), pyramid)
            skipped["B8"] += int((~keep & ~missing & ~cancel).sum())
            res = res[keep].copy()
            res.insert(0, "variant_id", pid * len(exits) + xid)
            res.insert(1, "entry_id", ent["entry_id"].to_numpy()[keep])
            out_frames.append(res)

    rank_of = {p: i for i, p in enumerate(pair_rank or [])}
    for (pid, xid), parts in pending.items():
        pr = np.concatenate([np.full(len(e), pr_) for pr_, e, *_ in parts])
        ets = np.concatenate([e["entry_ts"].to_numpy() for _, e, *_ in parts])
        ei = np.concatenate([e["entry_i"].to_numpy() for _, e, *_ in parts])
        xi = np.concatenate([x for *_, x, _xb, _m in parts])
        xb = np.concatenate([b for *_, b, _m in parts])
        dr = np.concatenate([e["dir"].to_numpy() for _, e, *_ in parts])
        bad = np.concatenate([m for *_, m in parts])
        rk = np.array([rank_of.get(q, len(rank_of)) for q in pr])
        keep, blocked = no_overlap_pairs(pr, ets, ei, xi, xb, dr, rk, pyramid, max_pairs)
        skipped["limit_par"] += int(blocked.sum())
        skipped["B8"] += int((~keep & ~blocked & ~bad).sum())
        off = 0
        for _pair, e, res, *_ in parts:
            k = keep[off:off + len(e)]
            off += len(e)
            r = res[k].copy()
            r.insert(0, "variant_id", pid * len(exits) + xid)
            r.insert(1, "entry_id", e["entry_id"].to_numpy()[k])
            out_frames.append(r)

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
            "avg_nights": g["nights"].mean() if "nights" in g else np.nan,
        })

    return outcomes.groupby(list(by)).apply(agg, include_groups=False).reset_index()
