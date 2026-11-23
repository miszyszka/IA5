"""D-072 — eksploracja Maca: po zwykłym liczeniu strategii Mac sam szuka jej lepszych odmian.

Zwykłe liczenie sprawdza dokładnie to, co napisaliśmy (≤ ~12 kombinacji PARAMS × siatka wyjść). Eksploracja pracuje dalej,
w tle, aż do limitu czasu albo do nadejścia nowej strategii:

  1. oryginał — punkt odniesienia (te same warianty co liczenie);
  2. filtry i przekształcenia sygnału (TRANSFORMS): odwrócenie, tylko long / short, z trendem / przeciw trendowi SMA,
     reżim zmienności, siła trendu ADX, wybicie / cofnięcie, potwierdzenie następną świecą — na 4 najlepszych (w IS)
     wariantach parametrów, z pełną siatką wyjść;
  3. stop kroczący (8 wyjść `trail`) — na tych samych 4 wariantach;
  4. szersza siatka parametrów — środki między wartościami i krok poza krańce (do MAX_GRID nowych kombinacji),
     z 30 najlepszymi wyjściami oryginału;
  5. runda 2 — połączenia par najlepszych przekształceń z rundy 1.

Uczciwość (W1, W2):
- wybór TYLKO na IS; ocena = min(Sharpe na transakcję w pierwszej i drugiej połowie IS) — nagradza stałość, nie szczyt;
- każdy wariant każdej mutacji to próba: Deflated Sharpe kandydata liczony względem WSZYSTKICH prób eksploracji;
- OOS otwierany raz, tylko dla TOP_K kandydatów wybranych po IS; otwarcie zapisane w dzienniku OOS (oos_ledger.json);
- kod kandydata jest generowany i liczony ponownie w piaskownicy (detektor look-ahead + zgodność sygnałów co do świecy);
- strategie D1: kandydaci i oryginał dodatkowo na świecach spółek (stk_oos, pilotaż — informacja, nie werdykt).
Strategia może wyłączyć eksplorację: `EXPLORE = False`.
"""
from __future__ import annotations

import ast
import hashlib
import itertools
import json
import math
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import indicators as ind
from .engine import Exit, default_exits, run
from .sandbox import param_grid, run_strategy_code
from .validate import bootstrap_ci, deflated_sharpe, per_trade_sharpe, random_benchmark

EXPLORE_VERSION = "1"
MAX_SECONDS = 60 * 60       # limit czasu jednej eksploracji (Mac liczy dłużej — Michał: czas nie gra roli)
MIN_TRADES = 30             # jak ranking liczenia (backtest.MIN_TRADES)
MIN_HALF = 10               # transakcji w każdej połowie IS
TOP_PIDS = 4                # tyle najlepszych wariantów parametrów oryginału dostaje przekształcenia
TOP_EXITS = 30              # tyle najlepszych wyjść oryginału dla szerszej siatki parametrów
MAX_GRID = 60               # najwyżej tyle nowych kombinacji parametrów
TOP_K = 5                   # kandydatów otwieranych na OOS
ROUND2 = 4                  # najlepsze przekształcenia łączone parami w rundzie 2
CATEGORICAL = {"cfg", "config", "konfig", "wersja", "version", "mode", "tryb", "kind", "rodzaj", "wariant", "variant"}

# Przekształcenia sygnału: (opis, ciało funkcji f(df, s, p, ind) → s). Ten sam tekst liczy się w eksploracji i trafia do
# kodu kandydata — jedno źródło prawdy. Wszystkie używają tylko świec do t włącznie (potwierdzenie przesuwa sygnał na t+1).
TRANSFORMS: dict[str, tuple[str, str]] = {
    "odwrocony": ("odwrócony sygnał", "return -s"),
    "tylko_long": ("tylko long", "return s.where(s > 0, 0.0)"),
    "tylko_short": ("tylko short", "return s.where(s < 0, 0.0)"),
    "trend200": ("tylko z trendem SMA200",
                 "m = ind.sma(df.close, 200)\n    return s.where(((s > 0) & (df.close > m)) | ((s < 0) & (df.close < m)), 0.0)"),
    "przeciw200": ("tylko przeciw trendowi SMA200",
                   "m = ind.sma(df.close, 200)\n    return s.where(((s > 0) & (df.close < m)) | ((s < 0) & (df.close > m)), 0.0)"),
    "trend50": ("tylko z trendem SMA50",
                "m = ind.sma(df.close, 50)\n    return s.where(((s > 0) & (df.close > m)) | ((s < 0) & (df.close < m)), 0.0)"),
    "zmiennosc_wysoka": ("tylko przy podwyższonej zmienności (ATR14 > ATR100)",
                         "return s.where(ind.atr(df, 14) > ind.atr(df, 100), 0.0)"),
    "zmiennosc_niska": ("tylko przy spokojnym rynku (ATR14 < ATR100)",
                        "return s.where(ind.atr(df, 14) < ind.atr(df, 100), 0.0)"),
    "adx_silny": ("tylko przy silnym trendzie (ADX14 > 25)", "return s.where(ind.adx(df, 14)[\"adx\"] > 25, 0.0)"),
    "adx_slaby": ("tylko bez wyraźnego trendu (ADX14 < 20)", "return s.where(ind.adx(df, 14)[\"adx\"] < 20, 0.0)"),
    "wybicie20": ("tylko z wybiciem 20 świec (zamknięcie za szczytem / dołkiem)",
                  "hi = ind.highest(df.high, 20).shift(1)\n    lo = ind.lowest(df.low, 20).shift(1)\n"
                  "    return s.where(((s > 0) & (df.close > hi)) | ((s < 0) & (df.close < lo)), 0.0)"),
    "cofniecie20": ("tylko po cofnięciu (kupno pod SMA20, sprzedaż nad SMA20)",
                    "m = ind.sma(df.close, 20)\n    return s.where(((s > 0) & (df.close < m)) | ((s < 0) & (df.close > m)), 0.0)"),
    "potwierdzenie": ("potwierdzenie: następna świeca zamyka się w kierunku sygnału",
                      "prev = s.shift(1).fillna(0.0)\n    return prev.where(np.sign(prev) == np.sign(df.close - df.open), 0.0)"),
}
EXCLUSIVE = [{"tylko_long", "tylko_short"}, {"trend200", "przeciw200"}, {"zmiennosc_wysoka", "zmiennosc_niska"},
             {"trend200", "trend50"}, {"przeciw200", "trend50"}, {"adx_silny", "adx_slaby"}, {"wybicie20", "cofniecie20"}]
SHIFTS = {"potwierdzenie"}  # przesuwa sygnał — nie z poziomami levels() (poziom liczony na świecy sygnału)


def trail_exits(tf: str) -> list[Exit]:
    caps = (20, 60) if tf == "D1" else (72, 240)
    return [Exit("trail", n=14, sl=2.0, trail=t, cap=c) for t, c in itertools.product((1.0, 1.5, 2.0, 3.0), caps)]


_FN: dict = {}


def _fn(name: str):
    if name not in _FN:
        ns = {"np": np, "pd": pd}
        exec(compile(f"def f(df, s, p, ind):\n    {TRANSFORMS[name][1]}\n", f"transform_{name}", "exec"), ns)  # noqa: S102 — nasz kod
        _FN[name] = ns["f"]
    return _FN[name]


def apply_transforms(df: pd.DataFrame, s: np.ndarray, names: list[str], p: dict) -> np.ndarray:
    x = pd.Series(np.asarray(s, float), index=df.index)
    for n in names:
        x = _fn(n)(df, x, p, ind)
    return np.nan_to_num(np.asarray(x, float)).astype(np.float32)


# ---------- szersza siatka parametrów ----------

def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def wider_values(key: str, vals: list) -> list:
    """Wartości do sprawdzenia dla jednego parametru: oryginalne + środki + krok poza krańce. Kategorie bez zmian."""
    if key.lower() in CATEGORICAL or not vals or not all(_is_num(v) for v in vals):
        return list(vals)
    ints = all(isinstance(v, int) for v in vals)
    u = sorted(set(vals))
    if ints and len(u) > 1 and u == list(range(u[0], u[0] + len(u))) and u[0] in (0, 1):
        return list(vals)          # 0, 1, 2, … = numer wersji/konfiguracji — nie skala
    pos = all(v > 0 for v in u)
    if len(u) == 1:
        cand = [u[0] * 0.75, u[0], u[0] * 1.25]
    else:
        steps = np.diff(u)
        cand = list(u) + [(a + b) / 2 for a, b in zip(u, u[1:])] + [u[0] - steps[0], u[-1] + steps[-1]]
    out = []
    for c in cand:
        c = int(round(c)) if ints else round(float(c), 6)
        if pos and c <= 0:
            continue
        if c not in out:
            out.append(c)
    return sorted(out)


def wider_grid(params: list[dict], seed: int = 5) -> list[dict]:
    """Nowe kombinacje (bez już policzonych), najwyżej MAX_GRID, wybrane deterministycznie."""
    if not params or params == [{}]:
        return []
    keys = list(params[0])
    vals = {k: [] for k in keys}
    for p in params:
        for k in keys:
            if p.get(k) not in vals[k]:
                vals[k].append(p.get(k))
    space = param_grid({k: wider_values(k, v) for k, v in vals.items()})
    seen = {json.dumps(p, sort_keys=True, default=str) for p in params}
    new = [p for p in space if json.dumps(p, sort_keys=True, default=str) not in seen]
    if len(new) > MAX_GRID:
        rng = np.random.default_rng(seed)
        new = [new[i] for i in sorted(rng.choice(len(new), MAX_GRID, replace=False))]
    return new


# ---------- kod kandydata ----------

def _defines(code: str, name: str) -> bool:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    return any(isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets) for n in tree.body)


def disabled(code: str) -> bool:
    """EXPLORE = False w kodzie strategii wyłącza eksplorację."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return True
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EXPLORE" for t in n.targets):
            return isinstance(n.value, ast.Constant) and n.value.value is False
    return False


def candidate_code(code: str, label: str, transforms: list[str], params: dict, exits: list[Exit] | None, trials: int) -> str:
    lines = ["", "", f"# ---- Eksploracja Maca (D-072): {label} ----",
             f"# Wybrane tylko po IS spośród {trials:,} prób eksploracji; OOS tej wersji był już raz oglądany (dziennik OOS).",
             "import numpy as np", "import pandas as pd", ""]
    if transforms:
        lines += ["_ia5_baza = signals", ""]
        for n in transforms:
            lines += [f"def _ia5_{n}(df, s, p, ind):", f"    {TRANSFORMS[n][1]}", ""]
        lines += ["def signals(df, p, ind):", "    s = _ia5_baza(df, p, ind)",
                  "    s = pd.Series(np.nan_to_num(np.asarray(s, dtype=float)), index=df.index)"]
        lines += [f"    s = _ia5_{n}(df, s, p, ind)" for n in transforms]
        lines += ["    return s", ""]
    lines.append("PARAMS = " + repr({k: [v] for k, v in params.items()}))
    if exits:
        lines.append("EXITS = " + repr([{k: v for k, v in asdict(e).items()} for e in exits]))
    note = f"Wersja z eksploracji Maca: {label}. Wybrana po IS spośród {trials:,} prób."
    lines.append(f"HYPOTHESIS = HYPOTHESIS + {chr(10) * 2!r} + {note!r}" if _defines(code, "HYPOTHESIS") else f"HYPOTHESIS = {note!r}")
    return code.rstrip() + "\n" + "\n".join(lines) + "\n"


# ---------- ocena ----------

def _load(folder: Path) -> dict[str, pd.DataFrame]:
    return {f.stem: pd.read_parquet(f) for f in sorted(Path(folder).glob("*.parquet"))}


def _frames(data: dict[str, pd.DataFrame], tf: str) -> dict[str, pd.DataFrame]:
    out = {}
    for pair, raw in data.items():
        df = raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]
        df.attrs["pair"], df.attrs["timeframe"] = pair, tf
        out[pair] = df
    return out


def _sig_arrays(sig: pd.DataFrame, data: dict, pid: int) -> dict[str, np.ndarray]:
    out = {}
    for pair, df in data.items():
        arr = np.zeros(len(df), np.float32)
        part = sig[(sig.param_id == pid) & (sig.pair == pair)]
        arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
        out[pair] = arr
    return out


def _lv_arrays(sig: pd.DataFrame, data: dict, pid: int) -> dict[str, np.ndarray]:
    out = {}
    for pair, df in data.items():
        lv = np.full((len(df), 3), np.nan)
        part = sig[(sig.param_id == pid) & (sig.pair == pair)]
        i = part["i"].to_numpy(int)
        lv[i, 0], lv[i, 1] = part["tp"].to_numpy(float), part["sl"].to_numpy(float)
        if "bars" in part:
            lv[i, 2] = part["bars"].to_numpy(float)
        out[pair] = lv
    return out


def is_stats(outcomes: pd.DataFrame, t0: float, cutoff: float) -> pd.DataFrame:
    """Metryki IS per wariant (variant_id = numer wyjścia przy jednym wariancie parametrów). OOS nie jest tu czytany."""
    o = outcomes[outcomes["sample"] == "IS"] if len(outcomes) and "sample" in outcomes else outcomes.iloc[0:0]
    if o.empty:
        return pd.DataFrame(columns=["xid", "n", "mean_r", "mean_pips", "sharpe", "sharpe_a", "sharpe_b", "score"])
    mid = t0 + (cutoff - t0) / 2
    rows = []
    for xid, g in o.groupby("variant_id"):
        r = g["r_net"].to_numpy(float)
        a = r[g["entry_ts"].to_numpy() < mid] if "entry_ts" in g else r[: len(r) // 2]
        b = r[g["entry_ts"].to_numpy() >= mid] if "entry_ts" in g else r[len(r) // 2:]
        sa = per_trade_sharpe(a) if len(a) >= MIN_HALF else np.nan
        sb = per_trade_sharpe(b) if len(b) >= MIN_HALF else np.nan
        n = len(r)
        score = min(sa, sb) if n >= MIN_TRADES and np.isfinite(sa) and np.isfinite(sb) else np.nan
        rows.append({"xid": int(xid), "n": n, "mean_r": float(np.nanmean(r)), "mean_pips": float(g["pips_net"].mean()),
                     "sharpe": per_trade_sharpe(r) if n >= MIN_TRADES else np.nan, "sharpe_a": sa, "sharpe_b": sb, "score": score})
    return pd.DataFrame(rows)


class Explorer:
    def __init__(self, code: str, h1_dir: Path, d1_dir: Path | None, log=print, stop=None, max_seconds: int = MAX_SECONDS,
                 stk_dir: Path | None = None, progress=None):
        self.code, self.h1_dir, self.d1_dir, self.log = code, Path(h1_dir), Path(d1_dir) if d1_dir else None, log
        self.stop = stop or (lambda: False)
        self.max_seconds = max_seconds
        self.deadline = time.time() + max_seconds
        self.stk_dir = Path(stk_dir) if stk_dir else None
        self.progress = progress or (lambda pct, msg: None)
        self.units: list[dict] = []           # każda policzona jednostka (mutacja × wariant parametrów)
        self.sharpes: list[float] = []        # Sharpe IS wszystkich prób (W2 — do DSR kandydatów)
        self.trials = 0
        self.interrupted = None
        self.seen: set = set()                # odcisk (sygnały, parametry, wyjścia) — ta sama odmiana nie liczy się dwa razy

    # -- pomocnicze --
    def _halt(self) -> bool:
        if self.interrupted:
            return True
        if self.stop():
            self.interrupted = "nowa strategia w kolejce"
        elif time.time() > self.deadline:
            self.interrupted = f"limit czasu {round(self.max_seconds / 60)} min"
        return bool(self.interrupted)

    def _run(self, sig_by_pair: dict, p: dict, exits: list[Exit], lv_by_pair: dict | None = None) -> dict:
        signals = {(0, pair): s for pair, s in sig_by_pair.items()}
        levels = {(0, pair): lv for pair, lv in lv_by_pair.items()} if lv_by_pair else None
        return run(self.data, signals, [p], exits=exits, hours=self.hours, pyramid=self.pyramid, max_pairs=self.max_pairs,
                   pair_rank=self.pair_rank, levels=levels)

    def _unit(self, mutation: str, label: str, family: str, pid: int, p: dict, sig_by_pair: dict, exits: list[Exit],
              transforms: list[str], exit_ids: list[int] | None = None, lv: dict | None = None, own_exits: bool = False) -> dict | None:
        if self._halt():
            return None
        h = hashlib.sha256(json.dumps([p, [e.label() for e in exits]], sort_keys=True, default=str).encode())
        for pair in sorted(sig_by_pair):
            h.update(np.ascontiguousarray(sig_by_pair[pair]).tobytes())
        key = h.hexdigest()
        if key in self.seen:      # np. „tylko long” strategii, która i tak gra tylko long — to nie jest nowa próba
            return {"duplicate": True}
        self.seen.add(key)
        res = self._run(sig_by_pair, p, exits, lv)
        st = is_stats(res["outcomes"].merge(res["entries"][["entry_id", "entry_ts"]], on="entry_id")
                      if not res["outcomes"].empty else res["outcomes"], self.t0, res["cutoff"])
        self.trials += len(exits)
        self.sharpes += [float(x) for x in st["sharpe"].dropna()]
        best = st.dropna(subset=["score"]).sort_values("score", ascending=False).head(1)
        u = {"mutation": mutation, "label": label, "family": family, "pid": pid, "params": p, "transforms": transforms,
             "exits": exits, "own_exits": own_exits, "stats": st, "sig": sig_by_pair, "lv": lv,
             "best": None if best.empty else best.iloc[0].to_dict()}
        if u["best"] is not None:
            u["best"]["exit"] = exits[int(u["best"]["xid"])]
        self.units.append(u)
        return u

    # -- główny przebieg --
    def run(self) -> dict:
        t_start = time.time()
        self.log("Eksploracja: sygnały oryginału (piaskownica)…")
        sig, meta = run_strategy_code(self.code, self.h1_dir, d1_dir=self.d1_dir)
        if meta["lookahead"]:
            return {"skipped": "look-ahead w oryginale"}
        self.tf = meta.get("timeframe", "H1")
        folder = self.d1_dir if self.tf == "D1" else self.h1_dir
        self.data = _load(folder)
        self.frames = _frames(self.data, self.tf)
        self.t0 = min(int(df["ts"].iloc[0]) for df in self.data.values())
        hours = meta.get("hours")
        self.hours = tuple(hours) if isinstance(hours, list) else hours
        self.pyramid = int(meta.get("pyramid") or 1)
        self.max_pairs, self.pair_rank = meta.get("max_pairs"), meta.get("pair_rank")
        self.levels = bool(meta.get("levels"))
        exits = [Exit(**e) for e in meta["exits"]] if meta.get("exits") else default_exits()
        self.base_exits = exits
        params = meta["params"]

        # 1. oryginał — wszystkie warianty parametrów, wszystkie wyjścia
        total_steps = len(params) + TOP_PIDS * (len(TRANSFORMS) + 1) + MAX_GRID // 4 + ROUND2 * TOP_PIDS
        step = 0
        base = {}
        for pid, p in enumerate(params):
            base[pid] = (_sig_arrays(sig, self.data, pid), _lv_arrays(sig, self.data, pid) if self.levels else None)
            self._unit("oryginal", "oryginał", "oryginał", pid, p, base[pid][0], exits, [], lv=base[pid][1])
            step += 1
            self.progress(step / total_steps, "oryginał")
        orig = [u for u in self.units if u["best"] is not None]
        top = sorted(orig, key=lambda u: -u["best"]["score"])[:TOP_PIDS] or [u for u in self.units if u["mutation"] == "oryginal"][:1]
        top_pids = [u["pid"] for u in top]

        # 2. przekształcenia sygnału
        names = [n for n in TRANSFORMS if not (self.levels and n in SHIFTS)]
        for n in names:
            for pid in top_pids:
                p = params[pid]
                s = {pair: apply_transforms(self.frames[pair], base[pid][0][pair], [n], p) for pair in self.data}
                self._unit(n, TRANSFORMS[n][0], "przekształcenie", pid, p, s, exits, [n], lv=base[pid][1])
                step += 1
                self.progress(step / total_steps, TRANSFORMS[n][0])

        # 3. stop kroczący (gdy strategia nie ma własnych poziomów)
        if not self.levels:
            tex = trail_exits(self.tf)
            for pid in top_pids:
                self._unit("trail", "stop kroczący 1–3 × ATR14", "wyjście", pid, params[pid], base[pid][0], tex, [], own_exits=True)
                step += 1
                self.progress(step / total_steps, "stop kroczący")

        # 4. szersza siatka parametrów
        new = wider_grid(params)
        if new and not self._halt():
            ranks = pd.concat([u["stats"].assign(pid=u["pid"]) for u in self.units if u["mutation"] == "oryginal"], ignore_index=True)
            ranks = ranks.dropna(subset=["score"]).groupby("xid")["score"].max().sort_values(ascending=False)
            keep = [int(x) for x in ranks.index[:TOP_EXITS]] or list(range(min(TOP_EXITS, len(exits))))
            sub = [exits[i] for i in keep]
            union = {k: [] for k in new[0]}
            for p in new:
                for k in union:
                    if p[k] not in union[k]:
                        union[k].append(p[k])
            code = self.code + "\n\nPARAMS = " + repr(union) + "\n"
            want_ids = [i for i, p in enumerate(param_grid(union)) if p in new]   # piaskownica liczy tylko wybrane kombinacje
            self.log(f"Eksploracja: szersza siatka parametrów — {len(new)} nowych kombinacji × {len(sub)} wyjść…")
            try:
                gsig, gmeta = run_strategy_code(code, self.h1_dir, d1_dir=self.d1_dir, param_ids=want_ids)
            except Exception as e:  # noqa: BLE001 — np. parametr poza zakresem strategii; ta mutacja odpada
                self.log(f"Eksploracja: szersza siatka nieudana ({str(e)[:200]})")
                gsig, gmeta = None, None
            if gsig is not None and not gmeta["lookahead"]:
                want = {json.dumps(p, sort_keys=True, default=str) for p in new}
                for gpid, p in enumerate(gmeta["params"]):
                    if json.dumps(p, sort_keys=True, default=str) not in want:
                        continue
                    lv = _lv_arrays(gsig, self.data, gpid) if self.levels else None
                    u = self._unit("siatka", "szersza siatka parametrów", "parametry", gpid, p, _sig_arrays(gsig, self.data, gpid), sub,
                                   [], lv=lv)
                    if u is None and self.interrupted:
                        break
                    step += 0.25
                    self.progress(min(step / total_steps, 0.95), "szersza siatka")

        # 5. runda 2 — połączenia najlepszych przekształceń
        tr = [u for u in self.units if u["family"] == "przekształcenie" and u["best"] is not None]
        best_by = {}
        for u in tr:
            n = u["transforms"][0]
            if n not in best_by or u["best"]["score"] > best_by[n]:
                best_by[n] = u["best"]["score"]
        lead = [n for n, _ in sorted(best_by.items(), key=lambda kv: -kv[1])[:ROUND2]]
        for a, b in itertools.combinations(lead, 2):
            if any({a, b} <= ex for ex in EXCLUSIVE):
                continue
            for pid in top_pids:
                p = params[pid]
                s = {pair: apply_transforms(self.frames[pair], base[pid][0][pair], [a, b], p) for pair in self.data}
                if self._unit(f"{a}+{b}", f"{TRANSFORMS[a][0]} + {TRANSFORMS[b][0]}", "połączenie", pid, p, s, exits, [a, b],
                              lv=base[pid][1]) is None and self.interrupted:
                    break
                step += 1
                self.progress(min(step / total_steps, 0.95), "połączenia")

        self.log(f"Eksploracja: {len(self.units)} jednostek, {self.trials:,} prób — wybór kandydatów tylko po IS…")
        out = self.choose_and_open(meta)
        out["seconds"] = round(time.time() - t_start, 1)
        return out

    # -- wybór po IS i jednorazowe otwarcie OOS --
    def choose_and_open(self, meta: dict) -> dict:
        def row(u):
            b = u["best"]
            return {"mutation": u["mutation"], "label": u["label"], "family": u["family"], "params": u["params"],
                    "exit": b["exit"].label(), "is_trades": int(b["n"]), "is_mean_r": b["mean_r"], "is_mean_pips": b["mean_pips"],
                    "is_sharpe_a": b["sharpe_a"], "is_sharpe_b": b["sharpe_b"], "score": b["score"]}

        scored = [u for u in self.units if u["best"] is not None]
        orig = [u for u in scored if u["mutation"] == "oryginal"]
        ref = max(orig, key=lambda u: u["best"]["score"]) if orig else None
        best_by_mut: dict[str, dict] = {}
        for u in scored:
            if u["mutation"] == "oryginal" or u["best"]["mean_r"] <= 0 or u["best"]["score"] <= 0:
                continue
            k = u["mutation"]
            if k not in best_by_mut or u["best"]["score"] > best_by_mut[k]["best"]["score"]:
                best_by_mut[k] = u
        chosen = sorted(best_by_mut.values(), key=lambda u: -u["best"]["score"])[:TOP_K]
        sharpes = np.array(self.sharpes, float)
        out = {"version": EXPLORE_VERSION, "timeframe": self.tf, "units": len(self.units), "trials": int(self.trials),
               "mutations": sorted({u["mutation"] for u in self.units}), "interrupted": self.interrupted,
               "reference": row(ref) if ref else None, "candidates": [],
               "is_table": sorted([row(u) for u in scored if u["mutation"] != "oryginal"], key=lambda r: -r["score"])[:40]}
        for k, u in enumerate(chosen, 1):
            out["candidates"].append(self.open_candidate(k, u, sharpes))
        if ref is not None:
            out["reference"]["oos"] = self.oos_block(ref)[0]
            if self.tf == "D1" and self.stk_dir:
                out["reference"]["stocks"] = self.stocks(self.code, ref["pid"], ref["best"]["exit"])
        out["summary"] = summary_line(out)
        return out

    def oos_block(self, u: dict) -> tuple[dict, pd.DataFrame, dict]:
        ex = u["best"]["exit"]
        res = self._run(u["sig"], u["params"], [ex], u["lv"])
        o = res["outcomes"]
        if o.empty:
            return {"trades": 0}, o, res
        t = o.merge(res["entries"][["entry_id", "dir", "entry_ts"]], on="entry_id")
        oos = t[t["sample"] == "OOS"]
        r = oos["r_net"].to_numpy(float)
        sd = oos["pips_net"].std(ddof=1)
        blk = {"trades": int(len(oos)), "mean_r": float(r.mean()) if len(r) else None,
               "mean_pips": float(oos["pips_net"].mean()) if len(oos) else None,
               "t_stat": float(oos["pips_net"].mean() / (sd / math.sqrt(len(oos)))) if len(oos) > 1 and sd > 0 else None,
               "bootstrap": bootstrap_ci(oos["pips_net"].to_numpy(float))}
        return blk, t, res

    def open_candidate(self, k: int, u: dict, sharpes: np.ndarray) -> dict:
        b = u["best"]
        ex = b["exit"]
        self.log(f"Eksploracja: kandydat {k} — {u['label']} ({ex.label()}) → OOS (raz)…")
        oos, t, res = self.oos_block(u)
        is_r = t[t["sample"] == "IS"]["r_net"].to_numpy(float) if len(t) else np.array([])
        dsr = deflated_sharpe(is_r, sharpes)
        bench = random_benchmark(res["preps"], t, ex, signals=u["sig"], hours=self.hours,
                                 level_entries=res["entries"] if ex.kind == "level" else None) if len(t) else {}
        code = candidate_code(self.code, u["label"], u["transforms"], u["params"], u["exits"] if u["own_exits"] else None, self.trials)
        check = self.verify(code, u)
        c = {"rank": k, "mutation": u["mutation"], "label": u["label"], "family": u["family"], "params": u["params"],
             "exit": ex.label(), "is": {"trades": int(b["n"]), "mean_r": b["mean_r"], "mean_pips": b["mean_pips"],
                                        "sharpe_a": b["sharpe_a"], "sharpe_b": b["sharpe_b"], "score": b["score"]},
             "oos": oos, "dsr": dsr, "benchmark": bench, "check": check, "code": code if check["ok"] else None,
             "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16]}
        c["verdict"] = candidate_verdict(c)
        if self.tf == "D1" and self.stk_dir and check["ok"]:
            c["stocks"] = self.stocks(code, 0, ex)
        return c

    def verify(self, code: str, u: dict) -> dict:
        """Kod kandydata w piaskownicy: look-ahead i te same sygnały co w eksploracji (co do świecy)."""
        try:
            sig, meta = run_strategy_code(code, self.h1_dir, d1_dir=self.d1_dir)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "why": f"kod kandydata nie działa: {str(e)[:300]}"}
        if meta["lookahead"]:
            return {"ok": False, "why": "detektor look-ahead"}
        got = _sig_arrays(sig, self.data, 0)
        bad = [pair for pair in self.data if not np.allclose(got[pair], u["sig"][pair], atol=1e-6)]
        return {"ok": not bad, "why": f"inne sygnały w piaskownicy: {', '.join(bad)}" if bad else ""}

    def stocks(self, code: str, pid: int, ex: Exit) -> dict:
        from .stk_oos import evaluate

        try:
            return evaluate(code, pid, ex, self.stk_dir, pyramid=self.pyramid, log=self.log)
        except Exception as e:  # noqa: BLE001 — pilotaż nie może zatrzymać eksploracji
            return {"na": f"błąd liczenia na spółkach: {type(e).__name__}: {str(e)[:200]}"}


def candidate_verdict(c: dict) -> dict:
    o, d, b = c.get("oos") or {}, (c.get("dsr") or {}).get("dsr"), (c.get("benchmark") or {}).get("percentile")
    if not c["check"]["ok"]:
        return {"color": "mute", "text": c["check"]["why"]}
    if (o.get("trades") or 0) < 10 or o.get("mean_r") is None:
        return {"color": "mute", "text": "za mało transakcji OOS"}
    if o["mean_r"] > 0 and (b or 0) >= 95 and d is not None and not math.isnan(d) and d >= 0.95:
        return {"color": "green", "text": "przetrwała OOS, losowe wejścia i korektę za liczbę prób"}
    if o["mean_r"] > 0 and (b or 0) >= 80:
        return {"color": "yellow", "text": "dodatnia w OOS, ale nie przechodzi wszystkich testów"}
    return {"color": "red", "text": "nie przetrwała OOS"}


def summary_line(out: dict) -> str:
    c = out.get("candidates") or []
    g = [x for x in c if x["verdict"]["color"] == "green"]
    y = [x for x in c if x["verdict"]["color"] == "yellow"]
    head = f"Mac sprawdził {out['trials']:,} odmian ({len(out['mutations'])} rodzajów)"
    if out.get("interrupted"):
        head += f", przerwane: {out['interrupted']}"
    if not c:
        return head + ". Żadna odmiana nie była stabilnie dodatnia w obu połowach IS — nic do otwarcia na OOS."
    if g:
        return head + f". {len(g)} z {len(c)} kandydatów przetrwało wszystkie testy — najlepszy: {g[0]['label']}."
    if y:
        return head + f". {len(y)} z {len(c)} kandydatów dodatnich w OOS, żaden nie przeszedł wszystkich testów."
    return head + f". {len(c)} kandydatów otwartych na OOS — żaden nie przetrwał."


# ---------- zapis ----------

def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, Exit):
        return x.label()
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if math.isnan(x) or math.isinf(x) else round(float(x), 6)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def markdown(out: dict) -> str:
    def f(x, nd=3):
        return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.{nd}f}"

    def pc(x):
        return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.0f}"

    L = ["## Eksploracja Maca (D-072)", "", out.get("summary", ""), "",
         f"Rodzaje odmian: {', '.join(out.get('mutations', []))}. Prób (wariantów) łącznie: {out.get('trials', 0):,}. "
         "Wybór tylko po IS: ocena = min(Sharpe na transakcję w 1. i 2. połowie IS). OOS otwarty raz, tylko dla kandydatów.", ""]
    ref = out.get("reference")
    if ref:
        o = ref.get("oos") or {}
        L += [f"Oryginał (najlepszy wariant wg tej samej oceny): {ref['exit']}, {ref['params']} — IS {ref['is_trades']} trans., "
              f"śr. R {f(ref['is_mean_r'])}, ocena {f(ref['score'])}; OOS {o.get('trades', 0)} trans., śr. R {f(o.get('mean_r'))}.", ""]
    if out.get("candidates"):
        L += ["| # | odmiana | wyjście | IS trans. | IS ocena | OOS trans. | OOS śr. R | OOS śr. pips | DSR (wszystkie próby) "
              "| percentyl losowych | akcje | werdykt |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for c in out["candidates"]:
            o, s = c.get("oos") or {}, c.get("stocks") or {}
            st = s.get("verdict", {}).get("text") if "verdict" in s else (s.get("na") or "—")
            L.append(f"| {c['rank']} | {c['label']} {c['params']} | {c['exit']} | {c['is']['trades']} | {f(c['is']['score'])} | "
                     f"{o.get('trades', 0)} | {f(o.get('mean_r'))} | {f(o.get('mean_pips'), 2)} | {f((c.get('dsr') or {}).get('dsr'))} | "
                     f"{pc((c.get('benchmark') or {}).get('percentile'))} | {st} | {c['verdict']['text']} |")
        L.append("")
    stk = [(c["label"], c["stocks"]) for c in out.get("candidates", []) if c.get("stocks") and "mean_pct" in c["stocks"]]
    if ref and (ref.get("stocks") or {}).get("mean_pct") is not None:
        stk.insert(0, ("oryginał", ref["stocks"]))
    if stk:
        L += ["### OOS na akcjach (pilotaż, poza werdyktem)", "",
              "| wersja | spółki | transakcje | śr. % netto | śr. R | long % | short % | percentyl losowych | spółki na plusie | werdykt |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for name, s in stk:
            L.append(f"| {name} | {s['tickers_traded']}/{s['tickers']} | {s['trades']} | {f(s['mean_pct'])} | {f(s['mean_r'])} | "
                     f"{f(s['long']['mean_pct'])} | {f(s['short']['mean_pct'])} | {pc(s['benchmark'].get('percentile'))} | "
                     f"{s['tickers_positive']}/{s['tickers_traded']} | {s['verdict']['text']} |")
        L.append("")
    return "\n".join(L) + "\n"


def save(out: dict, run_dir: Path) -> None:
    run_dir = Path(run_dir)
    (run_dir / "explore.json").write_text(json.dumps(_clean(out), ensure_ascii=False, indent=1), encoding="utf-8")
    md = markdown(out)
    (run_dir / "explore.md").write_text(md, encoding="utf-8")
    rep = run_dir / "report.md"
    if rep.exists():
        txt = rep.read_text(encoding="utf-8").split("\n## Eksploracja Maca (D-072)")[0].rstrip()
        rep.write_text(txt + "\n\n" + md, encoding="utf-8")


EXPLORE_FILES = ("explore.json", "explore.md")


def carry_over(out: Path) -> bool:
    """Forward test (W4) tworzy nowy katalog wyników — eksploracja tej samej wersji kodu przechodzi do niego,
    żeby nie zniknęła ze strony po publikacji. Zwraca True, gdy coś przeniesiono."""
    try:
        code_hash = json.loads((out / "manifest.json").read_text())["code_hash"]
    except (OSError, ValueError, KeyError):
        return False
    for prev in sorted((p for p in Path(out).parent.iterdir() if p.is_dir() and p != out), reverse=True):
        try:
            same = json.loads((prev / "manifest.json").read_text()).get("code_hash") == code_hash
        except (OSError, ValueError):
            continue
        if same and (prev / "explore.json").exists():
            ex = json.loads((prev / "explore.json").read_text(encoding="utf-8"))
            for f in EXPLORE_FILES:
                (out / f).write_bytes((prev / f).read_bytes())
            save_md_only(ex, out)
            return True
    return False


def save_md_only(ex: dict, run_dir: Path) -> None:
    rep = Path(run_dir) / "report.md"
    if rep.exists() and (Path(run_dir) / "explore.md").exists():
        txt = rep.read_text(encoding="utf-8").split("\n## Eksploracja Maca (D-072)")[0].rstrip()
        rep.write_text(txt + "\n\n" + (Path(run_dir) / "explore.md").read_text(encoding="utf-8"), encoding="utf-8")
