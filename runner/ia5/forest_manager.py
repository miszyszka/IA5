"""FOREST (D-048): Manager, mapy głosów i księgi. Liczy Mac, tylko przy działającym ia5 start.

Po zamknięciu każdej świecy w oknie B11, dla każdej pary:
  1. 1000 inwestorów głosuje: BUY albo SELL (znak średniej prognozy z 5 horyzontów swojego stanu).
  2. Manager bierze kierunek większości, a horyzont z najwyższego średniego prognozowanego zysku obozu zwycięzców po spreadzie.
  3. Porównuje układ głosów z zamkniętymi mapami. Mapa = 1000 głosów jednej decyzji + jej wynik. Pełny układ praktycznie się
     nie powtarza, więc liczy się podobieństwo: q = (głosy zgodne − niezgodne) / 1000. Bierzemy K najbliższych map. Mapa o q < 0
     to lustro: dzisiejszy obóz „za” był wtedy obozem „przeciw” — dlatego jedna transakcja daje dwie mapy (za i przeciw).
     Wynik: W wygranych, L przegranych, siła = (W−L)/K, z = (W−L)/√K.
Każda decyzja jest liczona wirtualnie na 5 horyzontach, także gdy para ma otwartą pozycję: uczenie tylko na wykonanych
transakcjach byłoby obciążone (Manager nie dowiedziałby się niczego o tym, co pominął).
Po zamknięciu (5 świec później) mapa „za” dostaje +1 przy zysku netto i −1 przy stracie, mapa „przeciw” odwrotnie; punkt dostają
też mapy podobne, a każdy inwestor ma sumę punktów ze swoich map.

Księgi (te same decyzje, różne zasady — bez grupy kontrolnej nie wiadomo, czy mapy czegokolwiek uczą):
  A Demokracja  1 inwestor = 1 głos, handluje zawsze, gdy para jest wolna. Grupa kontrolna: nic się nie uczy.
  B Mapy        decyzja A, ale wejście tylko gdy podobne mapy dają z ≥ Z_MIN; horyzont z najlepszym z.
  C Reputacja   głos waży tyle, ile inwestor zarobił punktów na mapach (powyżej średniej); handluje jak A.

Zero zaglądania w przyszłość: mapa trafia do pamięci dopiero, gdy zamknie się świeca 5. horyzontu. Stan jest zapisywany na dysku,
więc po przerwie Maca kolejne świece są nadrabiane po kolei i wynik jest ten sam, co bez przerwy (test).
"""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import forest_rules as FR
from .config import PAIRS
from .forest import HORIZONS, MAX_DEPTH, NH, H, Panel, popcount, test_columns

K_MAPS = 151  # ile najbliższych map porównujemy
MIN_MAPS = 1000  # poniżej tej liczby map Manager nie opiera się na pamięci (księgi B i C)
Z_MIN = 1.0  # księga B: tyle musi wynosić z podobnych map
EMBARGO = 24 * H  # mapy tej samej pary z ostatniej doby nie są dowodem (ten sam ruch, ta sama godzina)
SEGMENTS = ("MAPY", "OOS", "LIVE")
BOOKS = {"a": "Demokracja", "b": "Mapy", "c": "Reputacja"}
START_MEM = 4096
ROW_FLOATS = [f"g{h}" for h in HORIZONS] + [f"xt{h}" for h in HORIZONS]


class Forest:
    """Las w postaci tablic (szybkie głosowanie)."""

    def __init__(self, fr: dict):
        self.fr = fr
        inv = fr["investors"]
        self.m = len(inv)
        self.nt = len(fr["tests"])
        self.T = np.full((self.m, MAX_DEPTH), self.nt, np.int64)
        self.E = np.zeros((self.m, 1 << MAX_DEPTH, NH))
        for k, i in enumerate(inv):
            self.T[k, : len(i["tests"])] = i["tests"]
            tab = np.asarray(i["table"], float)
            self.E[k, : len(tab)] = tab
        self.ids = np.arange(self.m)
        self.fam_idx = np.array([FR.FAMILIES.index(i["fam"]) for i in inv], np.int64)
        self.fam_size = np.maximum(1, np.bincount(self.fam_idx, minlength=len(FR.FAMILIES)))
        self.words = (self.m + 63) // 64
        self.bitw = 1 << np.arange(MAX_DEPTH)

    def vote(self, col: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """col = wartości testów jednej świecy. Zwraca (prognozy inwestorów (m, 5) w ATR, głos bool: True = BUY)."""
        leaf = (col[self.T] * self.bitw).sum(1)
        e = self.E[self.ids, leaf]
        return e, e.mean(1) >= 0  # zawsze jest zdanie: remis (0) to BUY — w praktyce nie występuje

    def pack(self, v: np.ndarray) -> np.ndarray:
        b = np.packbits(v)
        return np.pad(b, (0, self.words * 8 - len(b))).view(np.uint64).copy()

    def unpack(self, bits: np.ndarray) -> np.ndarray:
        return np.unpackbits(bits.view(np.uint8))[: self.m].astype(bool)


def hex_votes(bits: np.ndarray) -> str:
    return bits.tobytes().hex()


def plain(x):
    """Wartość do JSON: NaN → null, typy numpy → zwykłe liczby."""
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    return int(x) if isinstance(x, np.integer) else x


def seg_of(ts: int, cuts: dict) -> str:
    if ts < cuts["oos"]:
        return "MAPY"
    return "OOS" if ts <= cuts["t1"] else "LIVE"


class Manager:
    def __init__(self, fr: dict):
        self.fr = fr
        self.forest = Forest(fr)
        m = self.forest.m
        self.cursor = {p: fr["cuts"]["forge"] - H for p in fr["pairs"]}
        self.left = {b: {p: 0 for p in fr["pairs"]} for b in BOOKS}  # ile świec zostało otwartej pozycji w parze (B8)
        self.rows: list[dict] = []
        self.bits: list[np.ndarray] = []
        self.pending: list[int] = []
        self.neigh: dict[int, tuple[list[int], list[int]]] = {}
        # pamięć map: tylko zamknięte decyzje
        self.n_mem = 0
        self.mem_bits = np.zeros((START_MEM, self.forest.words), np.uint64)
        self.mem_seq = np.zeros(START_MEM, np.int64)
        self.mem_pid = np.zeros(START_MEM, np.int16)
        self.mem_ts = np.zeros(START_MEM, np.int64)
        self.mem_r = np.zeros((START_MEM, NH))
        self.mem_cost = np.zeros(START_MEM)
        self.mem_pts = np.zeros(START_MEM, np.int64)
        # inwestorzy: punkty z map (zysk: +głos w obozie, strata: −) i wyniki per odcinek × horyzont
        self.pos = np.zeros(m, np.int64)  # suma głosów (+1 za / −1 przeciw) na mapach zyskownych
        self.neg = np.zeros(m, np.int64)  # to samo na stratnych
        self.n_win = self.n_loss = 0
        self.hits = np.zeros((len(SEGMENTS), m, NH), np.int64)
        self.nets = np.zeros((len(SEGMENTS), m, NH))
        self.seen = np.zeros((len(SEGMENTS), NH), np.int64)

    # ---------- pamięć ----------

    def _grow(self):
        if self.n_mem < len(self.mem_seq):
            return
        for k in ("mem_bits", "mem_seq", "mem_pid", "mem_ts", "mem_r", "mem_cost", "mem_pts"):
            a = getattr(self, k)
            setattr(self, k, np.concatenate([a, np.zeros_like(a)]))

    def weights(self) -> np.ndarray | None:
        """Księga C: waga głosu = punkty inwestora z map powyżej średniej (z-score). Za mało map = każdy po równo."""
        n = self.n_win + self.n_loss
        if n < MIN_MAPS:
            return None
        z = (self.pos - self.neg) / math.sqrt(n)
        return np.maximum(0.0, z - z.mean())

    def neighbours(self, bits: np.ndarray, pid: int, ts: int, d: int) -> dict | None:
        """K najbliższych zamkniętych map dla obozu o kierunku d. Tylko pamięć z tej chwili (test: brak look-ahead)."""
        n = self.n_mem
        if n < MIN_MAPS:
            return None
        m = self.forest.m
        q = 1 - 2 * popcount(self.mem_bits[:n] ^ bits).sum(1) / m
        aq = np.abs(q)
        aq[(self.mem_pid[:n] == pid) & (ts - self.mem_ts[:n] < EMBARGO)] = -1
        k = min(K_MAPS, n)
        idx = np.argpartition(-aq, k - 1)[:k]
        idx = idx[aq[idx] >= 0]
        if not len(idx):
            return None
        sgn = np.sign(q[idx])
        sgn[sgn == 0] = 1
        gain = d * sgn[:, None] * self.mem_r[idx] - self.mem_cost[idx, None]  # wynik netto dzisiejszego obozu w podobnych mapach
        with np.errstate(invalid="ignore"):
            w = (gain > 0).sum(0)
            lo = (gain <= 0).sum(0)
        cnt = np.maximum(1, w + lo)
        return {
            "idx": idx.tolist(),
            "sgn": sgn.astype(int).tolist(),
            "w": w,
            "l": lo,
            "z": (w - lo) / np.sqrt(cnt),
            "sila": (w - lo) / cnt,
            "gain": np.nanmean(gain, 0),
            "dop": float(((1 + aq[idx]) / 2).mean()),
            "dop_max": float(((1 + aq[idx]) / 2).max()),
            "best": int(self.mem_seq[idx[int(np.argmax(aq[idx]))]]),
        }

    def match_profit(self, v: np.ndarray, d: int) -> tuple[float, float]:
        """Dopasowanie obozu do Mapy Zysku i Mapy Straty: u ilu inwestorów dziś jest tak, jak zwykle bywało przy zysku / stracie."""
        camp = v if d > 0 else ~v
        if self.n_win == 0 or self.n_loss == 0:
            return float("nan"), float("nan")
        return float(((self.pos > 0) == camp).mean()), float(((self.neg > 0) == camp).mean())

    # ---------- decyzja ----------

    def decide(self, pn: Panel, r: int, col: np.ndarray, seq: int) -> tuple[dict, np.ndarray, dict | None]:
        F = self.forest
        pair = pn.pairs[int(pn.pid[r])]
        pip, spread = PAIRS[pair].pip, PAIRS[pair].spread_pips
        ts, atr = int(pn.ts[r]), float(pn.atr[r])
        e, v = F.vote(col)
        buy = int(v.sum())
        sell = F.m - buy
        d = 1 if buy > sell else -1 if sell > buy else (1 if e.mean() >= 0 else -1)
        camp = v if d > 0 else ~v
        fc = d * e[camp].mean(0) * atr / pip - spread
        h = int(np.argmax(fc)) + 1
        bits = F.pack(v)
        nb = self.neighbours(bits, int(pn.pid[r]), ts, d)
        mz, ms = self.match_profit(v, d)
        fam = np.bincount(F.fam_idx, weights=v, minlength=len(FR.FAMILIES)) / F.fam_size
        wt = self.weights()
        if wt is None or wt.sum() <= 0:
            dc, hc, share = d, h, float(camp.mean())
        else:
            wb, ws = float(wt[v].sum()), float(wt[~v].sum())
            dc = 1 if wb >= ws else -1
            cc = v if dc > 0 else ~v
            fw = (wt[cc, None] * (dc * e[cc])).sum(0) / wt[cc].sum() * atr / pip - spread
            hc = int(np.argmax(fw)) + 1
            share = max(wb, ws) / (wb + ws)
        row = {
            "seq": seq,
            "seg": seg_of(ts, self.fr["cuts"]),
            "pair": pair,
            "ts": ts,
            "atr": atr,
            "spread": spread,
            "buy": buy,
            "sell": sell,
            "dir": d,
            "h": h,
            "przewaga": abs(buy - sell) / F.m,
            **{f"f{k + 1}": round(float(fc[k]), 3) for k in range(NH)},
            **{f"r{k}": round(float(fam[k]), 3) for k in range(len(fam))},
            "maps": self.n_mem,
            "m_zysk": mz,
            "m_strata": ms,
            "dir_c": dc,
            "h_c": hc,
            "waga_c": round(share, 4),
            "take_b": False,
            "h_b": h,
            "z_b": float("nan"),
            "k": 0,
            "w": 0,
            "l": 0,
            "sila": float("nan"),
            "z": float("nan"),
            "dop": float("nan"),
            "dop_max": float("nan"),
            "best": -1,
            "g_map": float("nan"),
            "known": 0,
            "e_ts": 0,
            "e_px": float("nan"),
            "pkt": 0,
        }
        if nb is not None:
            k = h - 1
            kb = int(np.argmax(nb["z"]))
            row.update(
                {
                    "k": len(nb["idx"]),
                    "w": int(nb["w"][k]),
                    "l": int(nb["l"][k]),
                    "sila": float(nb["sila"][k]),
                    "z": float(nb["z"][k]),
                    "dop": nb["dop"],
                    "dop_max": nb["dop_max"],
                    "best": nb["best"],
                    "g_map": float(nb["gain"][k] * atr / pip),
                    "h_b": kb + 1,
                    "z_b": float(nb["z"][kb]),
                    "take_b": bool(nb["z"][kb] >= Z_MIN),
                }
            )
        for h_ in HORIZONS:
            row[f"g{h_}"] = float("nan")
            row[f"xt{h_}"] = float("nan")
        return row, bits, nb

    def _execute(self, row: dict) -> None:
        """B8: wejście tylko gdy para jest wolna w danej księdze. Decyzja z wiedzą tej chwili (bez wiedzy o przyszłych przerwach)."""
        pair = row["pair"]
        for b, go, hh in (("a", True, row["h"]), ("b", row["take_b"], row["h_b"]), ("c", True, row["h_c"])):
            free = self.left[b][pair] == 0
            row[f"ex_{b}"] = bool(go and free)
            if row[f"ex_{b}"]:
                self.left[b][pair] = int(hh)

    # ---------- rozliczenie ----------

    def _settle(self, pn: Panel, now: int) -> None:
        still = []
        for s in self.pending:
            row = self.rows[s]
            P = pn.P[row["pair"]]
            i = int(np.searchsorted(P["ts"], row["ts"]))
            n = len(P["ts"])
            if i >= n or int(P["ts"][i]) != int(row["ts"]):         # świeca zniknęła z bazy (korekta Yahoo): decyzja bez wyniku
                row["known"] = NH
                row["pkt"] = 0
                continue
            r = pn.row(row["pair"], i)
            if row["e_ts"] == 0 and i + 1 < n and P["ts"][i + 1] + H <= now + H:  # open świecy t+1 jest już znany
                row["e_ts"], row["e_px"] = int(P["ts"][i + 1]), float(P["o"][i + 1])
            k = row["known"]
            while k < NH:
                x = i + HORIZONS[k]
                if x >= n or P["ts"][x] + H > now:
                    break
                rv = pn.r[r, k]
                row[f"g{k + 1}"] = float(rv * row["atr"] / PAIRS[row["pair"]].pip)  # ruch rynku w pipsach, + = w górę; NaN = anulowana
                row[f"xt{k + 1}"] = int(P["ts"][x]) + H
                k += 1
            row["known"] = k
            if k == NH:
                self._close(pn, s, r)
            else:
                still.append(s)
        self.pending = still

    def _close(self, pn: Panel, s: int, r: int) -> None:
        """Wszystkie horyzonty znane: mapa trafia do pamięci, punkty dla map i inwestorów."""
        row = self.rows[s]
        F = self.forest
        rv = pn.r[r]
        nb = self.neigh.pop(s, None)
        v = F.unpack(self.bits[s])
        d, h = row["dir"], row["h"]
        g = row[f"g{h}"]
        net = d * g - row["spread"]
        y = 0 if not np.isfinite(g) else (1 if net > 0 else -1)
        row["pkt"] = y
        sg = SEGMENTS.index(row["seg"])
        sign = np.where(v, 1, -1)
        cost = float(pn.cost[r])
        for k in range(NH):
            if np.isfinite(rv[k]):
                self.seen[sg, k] += 1
                self.hits[sg, :, k] += sign * rv[k] > 0
                self.nets[sg, :, k] += sign * rv[k] - cost
        if not np.isfinite(rv).any():
            return
        self._grow()
        n = self.n_mem
        self.mem_bits[n] = self.bits[s]
        self.mem_seq[n], self.mem_pid[n], self.mem_ts[n] = s, pn.pid[r], row["ts"]
        self.mem_r[n], self.mem_cost[n] = rv, cost
        self.mem_pts[n] = y
        self.n_mem = n + 1
        if y:
            a = sign * d  # +1 obóz „za”, −1 obóz „przeciw”
            if y > 0:
                self.pos += a
                self.n_win += 1
            else:
                self.neg += a
                self.n_loss += 1
            if nb is not None:  # mapy podobne dostają punkt od tej transakcji
                self.mem_pts[nb[0]] += np.asarray(nb[1]) * y

    def advance(self, pn: Panel, until: int | None = None, log=print) -> int:
        """Przetwarza nowe świece po kolei (czas, para). Zwraca liczbę nowych decyzji."""
        fresh = [np.flatnonzero((pn.pid == k) & (pn.ts > self.cursor.get(p, 0)) & (pn.idx >= FR.WARMUP)) for k, p in enumerate(pn.pairs)]
        idx = np.concatenate(fresh) if fresh else np.array([], int)
        if until is not None:
            idx = idx[pn.ts[idx] <= until]
        if not len(idx):
            self._settle(pn, int(pn.ts.max()) + H)
            return 0
        order = idx[np.lexsort((pn.pid[idx], pn.ts[idx]))]
        win = order[pn.window[order] & np.isfinite(pn.atr[order])]
        pos = {int(r): k for k, r in enumerate(win)}
        cols = test_columns(pn.X[win], pn.col, self.fr["tests"]) if len(win) else None
        made, last, t0 = 0, None, time.time()
        for r in order:
            ts = int(pn.ts[r])
            if ts != last:
                self._settle(pn, ts + H)
                last = ts
            pair = pn.pairs[int(pn.pid[r])]
            for b in BOOKS:
                self.left[b][pair] = max(0, self.left[b][pair] - 1)
            self.cursor[pair] = ts
            k = pos.get(int(r))
            if k is None:
                continue
            s = len(self.rows)
            row, bits, nb = self.decide(pn, int(r), cols[:, k], s)
            self._execute(row)
            self.rows.append(row)
            self.bits.append(bits)
            self.pending.append(s)
            if nb is not None:
                self.neigh[s] = (nb["idx"], nb["sgn"])
            made += 1
            if made % 5000 == 0:
                log(f"  decyzje: {made:,} · mapy {self.n_mem:,} · {(time.time() - t0) / 60:.1f} min")
        self._settle(pn, last + H)
        return made

    def frame(self) -> pd.DataFrame:
        df = pd.DataFrame(self.rows)
        if len(df):
            mp = {int(s): int(p) for s, p in zip(self.mem_seq[: self.n_mem], self.mem_pts[: self.n_mem])}
            df["punkty"] = [mp.get(int(s), 0) for s in df["seq"]]
        return df

    def view_now(self, pn: Panel) -> list[dict]:
        """Ostatnia świeca każdej pary: głosy są zawsze, także poza oknem handlu (wtedy bez wejścia)."""
        out = []
        tests = self.fr["tests"]
        F = self.forest
        last_row = {}
        for row in self.rows[-len(pn.pairs) * 3 :]:
            last_row[(row["pair"], row["ts"])] = row
        for pair in pn.pairs:
            i = len(pn.P[pair]["ts"]) - 1
            r = pn.row(pair, i)
            ts = int(pn.ts[r])
            col = test_columns(pn.X[[r]], pn.col, tests)[:, 0]
            s = None
            row = last_row.get((pair, ts))
            if row is not None:
                s = row["seq"]
            else:
                row, _, _ = self.decide(pn, r, col, -1)
            bits = self.bits[s] if s is not None else F.pack(F.vote(col)[1])
            keys = (
                "buy",
                "sell",
                "dir",
                "h",
                "przewaga",
                "maps",
                "k",
                "w",
                "l",
                "sila",
                "z",
                "dop",
                "dop_max",
                "g_map",
                "take_b",
                "h_b",
                "z_b",
                "dir_c",
                "h_c",
                "waga_c",
                "m_zysk",
                "m_strata",
            )
            out.append(
                {
                    "pair": pair,
                    "ts": ts,
                    "okno": bool(pn.window[r]),
                    "f": [plain(row[f"f{k + 1}"]) for k in range(NH)],
                    "rodziny": [plain(row[f"r{k}"]) for k in range(len(FR.FAMILIES))],
                    "votes": hex_votes(bits),
                    "seq": plain(s),
                    **{k: plain(row[k]) for k in keys},
                }
            )
        return out

    # ---------- zapis i wczytanie ----------

    def save(self, folder: Path) -> None:
        new = folder.with_name(folder.name + ".new")
        if new.exists():
            shutil.rmtree(new)
        new.mkdir(parents=True)
        (new / "forest.json").write_text(json.dumps(self.fr, ensure_ascii=False), encoding="utf-8")
        pd.DataFrame(self.rows).to_parquet(new / "journal.parquet", index=False)
        np.save(new / "votes.npy", np.array(self.bits, np.uint64) if self.bits else np.zeros((0, self.forest.words), np.uint64))
        n = self.n_mem
        np.savez_compressed(
            new / "memory.npz",
            mem_bits=self.mem_bits[:n],
            mem_seq=self.mem_seq[:n],
            mem_pid=self.mem_pid[:n],
            mem_ts=self.mem_ts[:n],
            mem_r=self.mem_r[:n],
            mem_cost=self.mem_cost[:n],
            mem_pts=self.mem_pts[:n],
            pos=self.pos,
            neg=self.neg,
            hits=self.hits,
            nets=self.nets,
            seen=self.seen,
        )
        (new / "state.json").write_text(
            json.dumps(
                {
                    "cursor": self.cursor,
                    "left": self.left,
                    "pending": self.pending,
                    "n_win": self.n_win,
                    "n_loss": self.n_loss,
                    "neigh": {str(k): v for k, v in self.neigh.items()},
                }
            ),
            encoding="utf-8",
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
        fr = json.loads((folder / "forest.json").read_text(encoding="utf-8"))
        g = cls(fr)
        st = json.loads((folder / "state.json").read_text(encoding="utf-8"))
        g.cursor, g.left, g.pending, g.n_win, g.n_loss = st["cursor"], st["left"], st["pending"], st["n_win"], st["n_loss"]
        g.neigh = {int(k): (v[0], v[1]) for k, v in st["neigh"].items()}
        rows = pd.read_parquet(folder / "journal.parquet")
        g.rows = rows.to_dict("records") if len(rows) else []
        votes = np.load(folder / "votes.npy")
        g.bits = [votes[i] for i in range(len(votes))]
        mem = np.load(folder / "memory.npz")
        n = len(mem["mem_seq"])
        cap = max(START_MEM, 2 * n)
        for k in ("mem_bits", "mem_seq", "mem_pid", "mem_ts", "mem_r", "mem_cost", "mem_pts"):
            a = mem[k]
            b = np.zeros((cap, *a.shape[1:]), a.dtype)
            b[:n] = a
            setattr(g, k, b)
        g.n_mem = n
        for k in ("pos", "neg", "hits", "nets", "seen"):
            setattr(g, k, mem[k])
        return g
