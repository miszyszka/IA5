"""FOREST v2 (D-049): Manager. Liczy Mac, tylko przy działającym ia5 start.

Po zamknięciu świecy w oknie B11, dla każdej pary:
  1. Mówią tylko ci inwestorzy, których reguła jest spełniona; reszta milczy.
  2. Kierunek = większość głosów. Manager wchodzi tylko, gdy głosów jest co najmniej QUORUM, zgoda wynosi co najmniej CONSENSUS,
     a para jest wolna (B8). Inaczej nie handluje i zapisuje dlaczego.
  3. Horyzont = mediana horyzontów inwestorów z obozu zwycięzców.
Księga Kontrola bierze każdą większość bez progów: pokazuje, co dają same progi.

Uczenie: co 4 tygodnie las jest wybierany od nowa na wszystkich zamkniętych danych. Stan jest na dysku, a świece są przetwarzane
po kolei, więc po przerwie Maca wynik jest taki sam jak bez przerwy (test).
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import PAIRS
from .forest import (
    DESIGN_END,
    HORIZONS,
    N_RULES,
    NH,
    REFRESH_WEEKS,
    START_WEEKS,
    Cube,
    H,
    Panel,
    condition_masks,
    make_rules,
    rule_masks,
    rule_text,
    select,
)

QUORUM = 5  # najmniej tylu inwestorów musi się odezwać
CONSENSUS = 0.90  # tylu z nich musi być po jednej stronie (dobrane na świecach do DESIGN_END; cała tabela progów jest w raporcie)
SEGMENTS = ("HISTORIA", "TEST", "LIVE")
BOOKS = {"m": "Manager", "k": "Kontrola"}
WHY = {"go": "wejście", "few": "za mało głosów", "split": "za mała zgoda", "busy": "para zajęta"}


def segment(ts: int, fr: dict) -> str:
    if ts > fr["built_to"]:
        return "LIVE"
    return "HISTORIA" if ts < DESIGN_END else "TEST"


class Manager:
    def __init__(self, fr: dict):
        self.fr = fr
        self.rules = None
        self.cursor = {p: fr["t0"] + START_WEEKS * 7 * 86400 - H for p in fr["pairs"]}
        self.left = {b: {p: 0 for p in fr["pairs"]} for b in BOOKS}
        self.rows: list[dict] = []
        self.pending: list[int] = []
        self._cube = None

    def pool(self) -> list[tuple]:
        if self.rules is None:
            self.rules = make_rules(self.fr["conds"], N_RULES, self.fr["seed"])
        return self.rules

    def generation(self, pn: Panel, week: int, log=print) -> dict:
        """Las obowiązujący w danym tygodniu; gdy minął termin odświeżenia, wybiera nowy."""
        g = self.fr["generations"]
        due = START_WEEKS + (week - START_WEEKS) // REFRESH_WEEKS * REFRESH_WEEKS
        if g and g[-1]["week"] >= due:
            return next(x for x in reversed(g) if x["week"] <= week)
        if self._cube is None:
            log("FOREST: wyniki reguł tydzień po tygodniu…")
            self._cube = Cube(pn, self.pool(), self.fr["conds"], log=log)
        sel, info = select(self._cube, due)
        prev = {i["rule"] for i in g[-1]["investors"]} if g else set()
        inv = [{"rule": int(r.rule), "k": int(r.k), "t": round(float(r.t), 2), "ev": int(r.ev)} for r in sel.itertuples()]
        now = {i["rule"] for i in inv}
        gen = {**info, "ts": int(pn.t0 + due * 7 * 86400), "added": len(now - prev), "retired": len(prev - now), "investors": inv}
        g.append(gen)
        log(f"  las #{len(g)}: przeszło bramki {info['passed']}, w lesie {info['kept']}, doszło {gen['added']}, odpadło {gen['retired']}")
        return gen

    def votes(self, pn: Panel, gen: dict, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        U, D = condition_masks(pn.X[rows], pn.col, self.fr["conds"])
        K = len(gen["investors"])
        B, S = np.zeros((K, len(rows)), bool), np.zeros((K, len(rows)), bool)
        pool = self.pool()
        for j, i in enumerate(gen["investors"]):
            B[j], S[j] = rule_masks(U, D, pool[i["rule"]])
        return B, S

    @staticmethod
    def tally(gen: dict, b: np.ndarray, s: np.ndarray) -> dict:
        """Jedna świeca jednej pary: kto mówi, w którą stronę, jaki horyzont."""
        up, dn = int(b.sum()), int(s.sum())
        n = up + dn
        if n == 0 or up == dn:
            return {"n": n, "up": up, "dn": dn, "dir": 0, "h": 0, "cons": 0.5 if n else 0.0}
        d = 1 if up > dn else -1
        camp = b if d > 0 else s
        ks = np.array([i["k"] for i in gen["investors"]])[camp]
        return {"n": n, "up": up, "dn": dn, "dir": d, "h": HORIZONS[int(np.median(ks))], "cons": max(up, dn) / n}

    @staticmethod
    def verdict(t: dict) -> str:
        if t["n"] < QUORUM:
            return "few"
        return "split" if t["dir"] == 0 or t["cons"] < CONSENSUS else "go"

    def advance(self, pn: Panel, until: int | None = None, log=print) -> int:
        """Nowe świece po kolei (czas, para). Zwraca liczbę nowych decyzji."""
        fresh = [np.flatnonzero((pn.pid == k) & (pn.ts > self.cursor.get(p, 0))) for k, p in enumerate(pn.pairs)]
        idx = np.concatenate(fresh) if fresh else np.array([], int)
        if until is not None:
            idx = idx[pn.ts[idx] <= until]
        made = 0
        if len(idx):
            order = idx[np.lexsort((pn.pid[idx], pn.ts[idx]))]
            weeks = pn.week(pn.ts[order])
            due = START_WEEKS + (weeks - START_WEEKS) // REFRESH_WEEKS * REFRESH_WEEKS
            for d in np.unique(due):
                part = order[due == d]
                gen = self.generation(pn, int(d), log)
                ok = part[pn.usable()[part]]
                B, S = self.votes(pn, gen, ok) if len(ok) and gen["investors"] else (None, None)
                pos = {int(r): k for k, r in enumerate(ok)}
                for r in part:
                    pair = pn.pairs[int(pn.pid[r])]
                    for b in BOOKS:
                        self.left[b][pair] = max(0, self.left[b][pair] - 1)
                    self.cursor[pair] = int(pn.ts[r])
                    k = pos.get(int(r))
                    if k is None or B is None:
                        continue
                    t = self.tally(gen, B[:, k], S[:, k])
                    if t["n"] == 0:
                        continue
                    self._record(pn, int(r), pair, gen, t, B[:, k], S[:, k])
                    made += 1
        self._settle(pn)
        self._cube = None
        return made

    def _record(self, pn, r, pair, gen, t, b, s) -> None:
        v = self.verdict(t)
        free_m, free_k = self.left["m"][pair] == 0, self.left["k"][pair] == 0
        ex_m = v == "go" and free_m
        ex_k = t["dir"] != 0 and free_k
        if ex_m:
            self.left["m"][pair] = t["h"]
        if ex_k:
            self.left["k"][pair] = t["h"]
        ids = [i["rule"] for i in gen["investors"]]
        ts = int(pn.ts[r])
        self.rows.append(
            {
                "seq": len(self.rows),
                "seg": segment(ts, self.fr),
                "gen": gen["week"],
                "pair": pair,
                "ts": ts,
                "atr": float(pn.atr[r]),
                "spread": PAIRS[pair].spread_pips,
                "n": t["n"],
                "up": t["up"],
                "dn": t["dn"],
                "dir": t["dir"],
                "h": t["h"],
                "cons": round(t["cons"], 4),
                "why": "busy" if v == "go" and not free_m else v,
                "ex_m": bool(ex_m),
                "ex_k": bool(ex_k),
                "voters": ",".join([f"+{ids[j]}" for j in np.flatnonzero(b)] + [f"-{ids[j]}" for j in np.flatnonzero(s)]),
                "known": 0,
                "e_ts": 0,
                "e_px": float("nan"),
                "g24": float("nan"),
                "g48": float("nan"),
                "xt24": float("nan"),
                "xt48": float("nan"),
            }
        )
        self.pending.append(len(self.rows) - 1)

    def _settle(self, pn: Panel) -> None:
        still = []
        for s in self.pending:
            row = self.rows[s]
            P = pn.P[row["pair"]]
            i, n = int(np.searchsorted(P["ts"], row["ts"])), len(P["ts"])
            if i >= n or int(P["ts"][i]) != row["ts"]:  # świeca zniknęła z bazy (korekta Yahoo): decyzja bez wyniku
                row["known"] = NH
                continue
            if row["e_ts"] == 0 and i + 1 < n:
                row["e_ts"], row["e_px"] = int(P["ts"][i + 1]), float(P["o"][i + 1])
            k = row["known"]
            while k < NH and i + HORIZONS[k] < n:
                h = HORIZONS[k]
                row[f"g{h}"] = float(pn.r[pn.row(row["pair"], i), k] * row["atr"] / PAIRS[row["pair"]].pip)
                row[f"xt{h}"] = int(P["ts"][i + h]) + H
                k += 1
            row["known"] = k
            if k < NH:
                still.append(s)
        self.pending = still

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)

    def view_now(self, pn: Panel) -> list[dict]:
        """Ostatnia świeca każdej pary: kto mówi i co robi Manager, także poza oknem handlu."""
        gen = self.fr["generations"][-1] if self.fr["generations"] else None
        out = []
        for pair in pn.pairs:
            r = pn.row(pair, len(pn.P[pair]["ts"]) - 1)
            t = {"n": 0, "up": 0, "dn": 0, "dir": 0, "h": 0, "cons": 0.0}
            if gen and gen["investors"] and np.isfinite(pn.atr[r]):
                B, S = self.votes(pn, gen, np.array([r]))
                t = self.tally(gen, B[:, 0], S[:, 0])
            okno = bool(pn.window[r])
            v = self.verdict(t)
            busy = self.left["m"][pair] > 0
            why = "okno" if not okno else "none" if t["n"] == 0 else "busy" if v == "go" and busy else v
            out.append({"pair": pair, "ts": int(pn.ts[r]), "okno": okno, **t, "cons": round(t["cons"], 4), "why": why})
        return out

    def texts(self, rule: int) -> str:
        return rule_text(self.pool()[rule], self.fr["conds"])

    def save(self, folder: Path) -> None:
        new = folder.with_name(folder.name + ".new")
        if new.exists():
            shutil.rmtree(new)
        new.mkdir(parents=True)
        (new / "forest.json").write_text(json.dumps(self.fr, ensure_ascii=False), encoding="utf-8")
        pd.DataFrame(self.rows).to_parquet(new / "journal.parquet", index=False)
        (new / "state.json").write_text(
            json.dumps({"cursor": self.cursor, "left": self.left, "pending": self.pending, "saved": int(time.time())}), encoding="utf-8"
        )
        old = folder.with_name(folder.name + ".old")
        if folder.exists():
            if old.exists():
                shutil.rmtree(old)
            folder.replace(old)
        new.replace(folder)
        if old.exists():
            shutil.rmtree(old)

    @classmethod
    def load(cls, folder: Path) -> Manager:
        g = cls(json.loads((folder / "forest.json").read_text(encoding="utf-8")))
        st = json.loads((folder / "state.json").read_text(encoding="utf-8"))
        g.cursor, g.left, g.pending = st["cursor"], st["left"], st["pending"]
        rows = pd.read_parquet(folder / "journal.parquet")
        g.rows = rows.to_dict("records") if len(rows) else []
        return g
