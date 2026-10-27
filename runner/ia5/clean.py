"""Warstwa czyszczenia H1 do backtestu (D4, D5, D-031) — jawna, wersjonowana, nigdy cicha.

Wejście: świece H1 zbudowane z zatwierdzonych miesięcy M1 (dukascopy.month_ready).
Wyjście: te same świece + dwie kolumny:
  filled      — True dla świecy uzupełnionej (nie istniała w danych, wstawiona tutaj);
  gap_before  — ile oczekiwanych godzin sesji brakuje tuż przed tą świecą i NIE zostało uzupełnionych (0 = brak luki).

Zasady:
  * Luka w kalendarzu sesji (coverage.expected_mask) o długości ≤ FILL_MAX godzin → uzupełniona:
    ceny idą liniowo od zamknięcia ostatniej świecy przed luką do otwarcia pierwszej po niej
    (open = poprzedni punkt, close = następny, high/low = max/min z nich), spread = ostatni znany, minutes = 0.
  * Dłuższa luka → zostaje dziurą; pierwsza świeca po niej dostaje gap_before = liczba brakujących godzin.
    Silnik anuluje każdą transakcję, która na taką lukę nachodzi (engine.data_cancel).
  * Świeca uzupełniona zna otwarcie następnej świecy (przyszłość), więc silnik anuluje też transakcje,
    których świeca sygnału, wejścia albo wyjścia jest uzupełniona. Strategie widzą tylko OHLC (bez tych kolumn).
Surowe dane (M1, H1 z M1) zostają nietknięte; ten plik tworzy osobną kopię w data/h1_ready/.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .coverage import expected_mask

CLEAN_VERSION = "1"
FILL_MAX = 3   # D-031: uzupełniamy najwyżej 3 kolejne brakujące godziny; dłuższa luka = dziura znana silnikowi
H = 3600


def clean_h1(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Zwraca (świece z kolumnami filled i gap_before, opis: ile uzupełniono, lista długich luk)."""
    info = {"version": CLEAN_VERSION, "fill_max": FILL_MAX, "bars": 0, "filled": 0, "fill_runs": 0,
            "gaps": [], "gap_hours": 0}
    if raw is None or raw.empty:
        out = pd.DataFrame(columns=list(raw.columns if raw is not None else []) + ["filled", "gap_before"])
        return out, info
    df = raw.sort_values("ts").drop_duplicates("ts").reset_index(drop=True)
    ts = df["ts"].to_numpy(np.int64)
    hours = np.arange(ts[0], ts[-1] + H, H, dtype=np.int64)
    present = np.isin(hours, ts)
    grid = hours[present | expected_mask(hours)]          # oś: świece istniejące + oczekiwane godziny sesji
    miss = ~np.isin(grid, ts)
    # serie kolejnych brakujących godzin na tej osi (weekend nie przerywa serii — nie ma go na osi)
    edges = np.diff(np.concatenate([[0], miss.astype(np.int8), [0]]))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)   # [start, end) w indeksach grid
    pos = {int(t): i for i, t in enumerate(ts)}
    new_rows, gap_before = [], np.zeros(len(df), np.int64)
    o, c = df["open"].to_numpy(float), df["close"].to_numpy(float)
    spr = df["spread_avg"].to_numpy(float) if "spread_avg" in df else np.zeros(len(df))
    for a, b in zip(starts, ends):
        n = int(b - a)
        prev_i, next_i = pos[int(grid[a - 1])], pos[int(grid[b])]   # luka zawsze między dwiema świecami
        if n <= FILL_MAX:
            p0, p1 = c[prev_i], o[next_i]
            for k in range(n):
                op = p0 + (p1 - p0) * k / n
                cl = p0 + (p1 - p0) * (k + 1) / n
                new_rows.append({"ts": int(grid[a + k]), "open": op, "high": max(op, cl), "low": min(op, cl), "close": cl,
                                 "spread_avg": spr[prev_i], "spread": spr[prev_i]})
            info["fill_runs"] += 1
        else:
            gap_before[next_i] = n
            info["gaps"].append([int(grid[a]), int(grid[b - 1]) + H, n])
            info["gap_hours"] += n
    out = df.copy()
    out["filled"] = False
    out["gap_before"] = gap_before
    if new_rows:
        add = pd.DataFrame(new_rows)
        s = add.pop("spread")
        if "bid_close" in out:
            add["bid_close"] = add["close"] - s / 2
            add["ask_close"] = add["close"] + s / 2
        if "minutes" in out:
            add["minutes"] = 0
        add["filled"] = True
        add["gap_before"] = 0
        out = pd.concat([out, add[[c_ for c_ in out.columns if c_ in add]]], ignore_index=True)
        out = out.sort_values("ts").reset_index(drop=True)
    out["ts"] = out["ts"].astype("int64")
    if "minutes" in out:
        out["minutes"] = out["minutes"].astype("int16")
    out["filled"] = out["filled"].astype(bool)
    out["gap_before"] = out["gap_before"].astype("int64")
    info["bars"] = int(len(out))
    info["filled"] = int(out["filled"].sum())
    info["from"], info["to"] = int(out["ts"].iloc[0]), int(out["ts"].iloc[-1])
    return out, info
