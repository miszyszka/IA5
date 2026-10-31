"""Mapa pokrycia danych (zakładka Stats): para × miesiąc wobec kalendarza sesji (D-022, D-039).

Liczone z kopii świec Yahoo na Macu (które godziny sesji są, których brakuje). Zgłasza, niczego nie naprawia (D5).
Wynik to same liczniki i zakresy luk — bez cen.

Statusy miesiąca: 0 brak danych · 1 pełny · 2 w toku (pierwszy/bieżący miesiąc).
Luki (godziny oczekiwane w sesji, a nieobecne) w trzech rodzajach — te same zasady co warstwa czyszczenia (clean.py):
  "w" granica tygodnia — ≤ 3 h tuż przy weekendzie albo święcie (Yahoo zaczyna/kończy tydzień inaczej niż kalendarz),
  "q" bez ruchu — ≤ 3 h, cena po luce taka jak przed (< 1 pips), nic nie przepadło,
  "p" dziura — brak danych (≤ 3 h uzupełniana do liczenia, dłuższa to przerwa w danych i anuluje transakcje, B12).
Pole „all” w luce: ile par miało ją w tym samym czasie (wszystkie naraz = przerwa źródła, nie jednej pary).
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd

H = 3600
DAY = 86400
BOUNDARY_H = 3         # luka ≤ 3 h przy weekendzie/święcie = granica tygodnia (D-039), nie brak danych
QUIET_PIPS = 1.0       # luka do 3 h, po której cena jest ta sama (< 1 pips) = „bez ruchu” — nic nie przepadło (D-028)
QUIET_MAX_H = 3
NONE, FULL, PARTIAL = 0, 1, 2


# ---------- kalendarz ----------

def _parts(ts):
    ts = np.asarray(ts, dtype=np.int64)
    wd = (ts // DAY + 4) % 7  # 0 = niedziela; 1970-01-01 był czwartkiem
    hr = (ts % DAY) // H
    day = (ts // DAY).astype("datetime64[D]")
    mon = day.astype("datetime64[M]")
    dom = (day - mon).astype(np.int64) + 1
    mo = mon.astype(np.int64) % 12 + 1
    # święta FX: 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC — rynek nieczynny (D-028)
    hol = ((mo == 12) & ((dom == 24) | (dom == 31)) & (hr >= 21)) | (((mo == 12) & (dom == 25)) | ((mo == 1) & (dom == 1))) & (hr < 22)
    return wd, hr, hol


def expected_mask(ts) -> np.ndarray:
    """Wektorowo to samo co session.is_expected_bar (test sprawdza każdą godzinę od 2003)."""
    wd, hr, hol = _parts(ts)
    return ~((wd == 6) | ((wd == 5) & (hr >= 21)) | ((wd == 0) & (hr < 22)) | hol)


def closed_mask(ts) -> np.ndarray:
    """Godziny, w których rynek na pewno nie działa: sobota i święta (D-028). Piątek po 21:00 i niedziela przed 22:00
    UTC nie należą tu — zależnie od czasu letniego w USA część z nich to jeszcze/już handel."""
    wd, _, hol = _parts(ts)
    return (wd == 6) | hol


def expected_hours(a: int, b: int) -> np.ndarray:
    """Godziny [a, b), w których świeca musi istnieć."""
    a = -(-int(a) // H) * H
    hours = np.arange(a, int(b), H, dtype=np.int64)
    return hours[expected_mask(hours)]


def win_hours(mi: dict) -> np.ndarray:
    """Oczekiwane godziny okna miesiąca (od pierwszej do ostatniej świecy źródła)."""
    return expected_hours(*mi["win"])


def month_key(y: int, m: int) -> str:
    return f"{y}-{m:02d}"


def months(start: date, last: date) -> list[tuple[int, int]]:
    y, m, out = start.year, start.month, []
    while (y, m) <= (last.year, last.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def month_bounds(y: int, m: int) -> tuple[int, int]:
    a = datetime(y, m, 1, tzinfo=UTC)
    b = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=UTC)
    return int(a.timestamp()), int(b.timestamp())


def month_index(ts: np.ndarray, start: date) -> np.ndarray:
    """Numer miesiąca liczony od `start` (0 = miesiąc startu)."""
    mon = np.asarray(ts, dtype=np.int64).astype("datetime64[s]").astype("datetime64[M]").astype(np.int64)
    return mon - ((start.year - 1970) * 12 + start.month - 1)


# ---------- liczenie pokrycia ----------

def _present(df: pd.DataFrame | None) -> np.ndarray:
    if df is None or df.empty:
        return np.empty(0, np.int64)
    return df["ts"].to_numpy(np.int64)


def source_coverage(month_info: dict[str, list[dict]], frames: dict[str, pd.DataFrame], start: date) -> dict:
    """month_info[para] = lista miesięcy (status, cal, win), frames[para] = H1 (ts, open, close).

    Zwraca {"pairs": {para: {"m": [[status, oczekiwane, obecne, dziury, granica/bez ruchu, 0, 0], ...],
                              "gaps": [[od, do, godzin, rodzaj, ile par ma tę lukę], ...]}}}.
    Rodzaj luki (te same zasady co clean.py): "w" granica tygodnia (≤ 3 h przy weekendzie/święcie), "q" bez ruchu
    (≤ 3 h, cena po luce taka jak przed), "p" dziura — brak danych.
    """
    from .config import PAIRS

    exp, miss, pres_sets = {}, {}, {}
    for pair, info in month_info.items():
        ts = _present(frames.get(pair))
        hours = [win_hours(mi) for mi in info if mi["win"]]
        e = np.concatenate(hours) if hours else np.empty(0, np.int64)
        exp[pair] = e
        miss[pair] = e[~np.isin(e, ts)]
        pres_sets[pair] = ts
    all_m = np.concatenate(list(miss.values())) if miss else np.empty(0, np.int64)
    mu, mc = np.unique(all_m, return_counts=True)   # ile par nie ma danej godziny

    out = {}
    for pair, info in month_info.items():
        e, mh, ts = exp[pair], miss[pair], pres_sets[pair]
        soft = np.zeros(len(mh), bool)   # granica tygodnia albo bez ruchu — nie dziura
        gaps = []
        if len(mh):
            pos = np.searchsorted(e, mh)
            # zakresy luk: kolejne godziny w ciągu oczekiwanych (luka przez weekend to jedna luka)
            cut = np.flatnonzero((np.diff(pos) != 1) | (np.diff(mh) > 4 * DAY)) + 1
            df = frames.get(pair)
            px = df is not None and {"open", "close"} <= set(df.columns) and pair in PAIRS
            if px:
                ord_ = np.argsort(ts)
                ts_s, op_s, cl_s = ts[ord_], df["open"].to_numpy(float)[ord_], df["close"].to_numpy(float)[ord_]
            for seg_i, seg_h in zip(np.split(np.arange(len(mh)), cut), np.split(mh, cut)):
                kind = "p"
                boundary = not expected_mask([seg_h[0] - H])[0] or not expected_mask([seg_h[-1] + H])[0]
                if boundary and len(seg_h) <= BOUNDARY_H:
                    kind = "w"
                elif px and len(seg_h) <= QUIET_MAX_H:  # D-028: krótka luka, po której cena się nie ruszyła
                    j = np.searchsorted(ts_s, seg_h[0])
                    if 0 < j < len(ts_s) and abs(op_s[j] - cl_s[j - 1]) / PAIRS[pair].pip < QUIET_PIPS:
                        kind = "q"
                if kind != "p":
                    soft[seg_i] = True
                n_pairs = int(mc[np.searchsorted(mu, seg_h[0])])
                gaps.append([int(seg_h[0]), int(seg_h[-1]) + H, int(len(seg_h)), kind, n_pairs])
        common = soft
        # dziury = tylko luki, w których rynek działał i cena się ruszała; wspólne i „bez ruchu” liczone osobno
        n = len(info)
        holes = np.bincount(month_index(mh[~common], start), minlength=n)[:n]
        shared = np.bincount(month_index(mh[common], start), minlength=n)[:n]
        in_win = np.isin(ts, e)
        present = np.bincount(month_index(ts[in_win], start), minlength=n)[:n]

        rows = []
        for i, mi in enumerate(info):
            if mi["win"]:
                rows.append([mi["status"], int(len(win_hours(mi))), int(present[i]), int(holes[i]), int(shared[i]), 0, 0])
            else:  # bez danych: oczekiwane wg kalendarza całego miesiąca — tyle brakuje
                rows.append([mi["status"], int(len(expected_hours(*mi["cal"]))), 0, 0, 0, 0, 0])

        out[pair] = {"m": rows, "gaps": gaps}
    return {"pairs": out}


def yahoo_months(df: pd.DataFrame | None, start: date, last: date) -> list[dict]:
    """Yahoo: okno od pierwszej do ostatniej zapisanej świecy; bieżący miesiąc = w toku."""
    info = []
    first = int(df["ts"].min()) if df is not None and len(df) else None
    end = int(df["ts"].max()) + H if first is not None else None
    for y, m in months(start, last):
        a, b = month_bounds(y, m)
        win = None
        st = NONE
        if first is not None and b > first and a < end:
            win = (max(a, first), min(b, end))
            st = PARTIAL if b > end else FULL
        info.append({"key": month_key(y, m), "status": st, "cal": (a, b), "win": win})
    return info


NO_SESSION, NO_DATA, BARRIER = -1, -2, 100


def day_map(yahoo: dict[str, pd.DataFrame], gaps: dict[str, list], now: int) -> dict:
    """Kalendarz dzień po dniu (Stats): {"start": "RRRR-MM-DD", "pairs": {PARA: [wartość na dzień, ...]}}.

    Wartość dnia (UTC): -1 = dzień bez sesji (weekend, święto), -2 = brak danych (przed pierwszą świecą pary albo
    dzień, w którym nie ma żadnej świecy), n = brakujące godziny sesji z dziur tej pary ≤ 3 h (uzupełniane do liczenia),
    100 + n = dzień należy do przerwy w danych (dziura > 3 h — transakcje anulowane, B12). Granica tygodnia
    i luki bez ruchu nie są liczone (nie są dziurami).
    """
    first = min((int(df["ts"].min()) for df in yahoo.values() if df is not None and len(df)), default=None)
    if first is None:
        return {"start": None, "pairs": {}}
    d0 = first // DAY * DAY
    n_days = int((now // DAY * DAY - d0) // DAY) + 1
    hours = d0 + H * np.arange(n_days * 24, dtype=np.int64)
    sess_h = expected_mask(hours).reshape(n_days, 24).sum(axis=1)
    sess = sess_h > 0
    out = {}
    for pair, df in yahoo.items():
        if df is None or df.empty:
            out[pair] = [NO_DATA] * n_days
            continue
        ts = df["ts"].to_numpy(np.int64)
        has = np.bincount(((ts - d0) // DAY).clip(0, n_days - 1), minlength=n_days) > 0
        miss = np.zeros(n_days, np.int64)
        soft = np.zeros(n_days, np.int64)   # godziny granicy tygodnia / bez ruchu — nie są dziurą
        barrier = np.zeros(n_days, bool)
        for a, b, n, kind, *_ in gaps.get(pair, []):
            for t in expected_hours(a, b):
                i = int((t - d0) // DAY)
                if not 0 <= i < n_days:
                    continue
                if kind != "p":
                    soft[i] += 1
                    continue
                miss[i] += 1
                barrier[i] |= n > BOUNDARY_H
        start_i = int((ts.min() - d0) // DAY)
        vals = np.where(barrier, BARRIER + miss, miss)
        live = sess_h - soft > 0            # dzień ma godziny sesji poza granicą tygodnia (np. niedziela zimą — nie ma)
        vals = np.where(~live, NO_SESSION, vals)
        vals = np.where(live & ~has & ~barrier, NO_DATA, vals)
        vals[:start_i] = np.where(sess[:start_i], NO_DATA, NO_SESSION)
        out[pair] = [int(v) for v in vals]
    return {"start": datetime.fromtimestamp(int(d0), UTC).strftime("%Y-%m-%d"), "pairs": out}


def build(yahoo: dict[str, pd.DataFrame], now: int | None = None) -> dict:
    """Mapa pokrycia świec Yahoo (jedyne źródło, D-039): para × miesiąc od pierwszej świecy."""
    now = now or int(datetime.now(UTC).timestamp())
    pairs = sorted(yahoo, key=lambda p: list(_pairs()).index(p) if p in _pairs() else 99)
    first = min((int(df["ts"].min()) for df in yahoo.values() if df is not None and len(df)), default=None)
    start = datetime.fromtimestamp(first, UTC).date().replace(day=1) if first else datetime.fromtimestamp(now, UTC).date().replace(day=1)
    info = {p: yahoo_months(yahoo.get(p), start, datetime.fromtimestamp(now, UTC).date()) for p in pairs}
    cov = source_coverage(info, yahoo, start)
    cov["days"] = day_map(yahoo, {p: v["gaps"] for p, v in cov["pairs"].items()}, now)
    return {
        "v": 3, "generated": now, "boundary_h": BOUNDARY_H,
        "sources": {
            "yahoo": {"label": "Yahoo H1", "role": "backtesty i monitoring", "start": month_key(start.year, start.month),
                      "end": max((int(df["ts"].max()) + H for df in yahoo.values() if df is not None and len(df)), default=now),
                      **cov},
        },
    }


def _pairs():
    from .config import PAIRS

    return PAIRS


def content_hash(cov: dict) -> str:
    """Hash bez znacznika czasu — publikujemy tylko, gdy coś się zmieniło."""
    body = {k: v for k, v in cov.items() if k != "generated"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
