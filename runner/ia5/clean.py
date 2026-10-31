"""Warstwa czyszczenia H1 do backtestu (D4, D5, D8) — jawna, wersjonowana, nigdy cicha.

Wejście: kopia świec Yahoo H1 z Firestore (data/yahoo/{PARA}.parquet), wszystkie pary naraz.
Wyjście (data/h1_ready/{PARA}.parquet): te same świece + dwie kolumny:
  filled      — True dla świecy uzupełnionej (nie istniała w danych, wstawiona tutaj);
  gap_before  — ile oczekiwanych godzin sesji brakuje tuż przed tą świecą i NIE zostało uzupełnionych (0 = brak przerwy).

Zasady (D-039):
  * Świeca łamiąca D5 (brak ceny, cena ≤ 0, high < max(open, close), low > min(open, close), czas poza pełną godziną)
    jest odrzucana i liczona w opisie — jej godzina staje się brakującą.
  * Świeca poza sesją jest odrzucana, gdy rynek na pewno nie działał (sobota, święta 25.12 i 1.01) albo gdy jest płaska
    (high = low) poza kalendarzem sesji — Yahoo dopisuje takie świece po piątkowym zamknięciu i w święta, powtarzając
    starą cenę (sprawdzone na danych 2024–2026, D-039). Poza sesją zostają tylko świece z ruchem ceny (np. piątek
    21:00 UTC zimą, gdy rynek jeszcze działa).
  * Brakujące godziny sesji (kalendarz D-028) dzielimy na serie. Seria ≤ BOUNDARY_H godzin przylegająca do weekendu
    albo święta (godzina tuż przed nią albo tuż po niej jest poza sesją) to granica tygodnia — Yahoo zaczyna i kończy
    tydzień o godzinę–dwie inaczej niż kalendarz (czas letni w USA). Jak weekend: ani uzupełnienie, ani bariera,
    następna świeca jest kolejną.
  * Każda inna seria ≤ FILL_MAX godzin → uzupełniona: ceny liniowo od zamknięcia ostatniej świecy przed nią
    do otwarcia pierwszej po niej (high/low = max/min z nich), filled = True.
  * Dłuższa seria = przerwa w dostępie do danych (także gdy brakuje jej we wszystkich parach naraz — rynek FX w tygodniu
    nie zamyka się na kilka godzin, to przerwa Yahoo): pierwsza świeca po niej dostaje gap_before = liczba brakujących
    godzin; silnik anuluje każdą transakcję, która na nią nachodzi (B12, engine.data_cancel).
  * Świeca uzupełniona zna otwarcie następnej świecy (przyszłość), więc silnik anuluje też transakcje, których świeca
    sygnału, wejścia albo wyjścia jest uzupełniona. Strategie widzą tylko OHLC (bez tych kolumn).
Kopia surowa (data/yahoo) zostaje nietknięta.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .coverage import BOUNDARY_H, closed_mask, expected_mask

CLEAN_VERSION = "5"
FILL_MAX = 3   # D8: uzupełniamy najwyżej 3 kolejne brakujące godziny jednej pary
H = 3600
COLS = ["ts", "open", "high", "low", "close"]


def invalid_mask(df: pd.DataFrame) -> np.ndarray:
    """Świece łamiące D5 (te same reguły co quality.bar_flags)."""
    o, h, lo, c = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    ts = df["ts"].to_numpy(np.int64)
    with np.errstate(invalid="ignore"):
        bad = ~np.isfinite(np.c_[o, h, lo, c]).all(axis=1)
        bad |= np.minimum.reduce([o, h, lo, c]) <= 0
        bad |= (h < np.maximum(o, c) - 1e-12) | (lo > np.minimum(o, c) + 1e-12)
    return bad | (ts % H != 0)


def off_session_mask(df: pd.DataFrame) -> np.ndarray:
    """Świece poza sesją do odrzucenia: sobota/święto albo płaska świeca poza kalendarzem sesji."""
    ts = df["ts"].to_numpy(np.int64)
    flat = df["high"].to_numpy(float) <= df["low"].to_numpy(float)
    return closed_mask(ts) | (~expected_mask(ts) & flat)


def clean_h1(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Zwraca (świece z kolumnami filled i gap_before, opis)."""
    info = {"version": CLEAN_VERSION, "fill_max": FILL_MAX, "bars": 0, "rejected": 0, "rejected_ts": [], "off_session": 0,
            "filled": 0, "fill_runs": 0, "gaps": [], "gap_hours": 0, "closed_runs": 0, "closed_hours": 0}
    if raw is None or raw.empty:
        return pd.DataFrame(columns=COLS + ["filled", "gap_before"]), info
    df = raw[COLS].sort_values("ts").drop_duplicates("ts", keep="last").reset_index(drop=True)
    bad = invalid_mask(df)
    if bad.any():
        info["rejected"] = int(bad.sum())
        info["rejected_ts"] = [int(t) for t in df["ts"].to_numpy()[bad][:50]]
        df = df[~bad].reset_index(drop=True)
    off = off_session_mask(df)
    if off.any():
        info["off_session"] = int(off.sum())
        df = df[~off].reset_index(drop=True)
    if df.empty:
        return pd.DataFrame(columns=COLS + ["filled", "gap_before"]), info
    df["ts"] = df["ts"].astype(np.int64)
    ts = df["ts"].to_numpy(np.int64)
    hours = np.arange(ts[0], ts[-1] + H, H, dtype=np.int64)
    grid = hours[np.isin(hours, ts) | expected_mask(hours)]   # oś: świece istniejące + oczekiwane godziny sesji
    miss = ~np.isin(grid, ts)
    # serie kolejnych brakujących godzin na tej osi (weekend nie przerywa serii — nie ma go na osi)
    edges = np.diff(np.concatenate([[0], miss.astype(np.int8), [0]]))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)   # [start, end) w indeksach grid
    pos = {int(t): i for i, t in enumerate(ts)}
    new_rows, gap_before = [], np.zeros(len(df), np.int64)
    o, c = df["open"].to_numpy(float), df["close"].to_numpy(float)
    for a, b in zip(starts, ends):
        n = int(b - a)
        prev_i, next_i = pos[int(grid[a - 1])], pos[int(grid[b])]   # seria zawsze między dwiema świecami
        run = grid[a:b]
        boundary = not expected_mask([run[0] - H])[0] or not expected_mask([run[-1] + H])[0]
        if boundary and n <= BOUNDARY_H:  # granica weekendu / święta — jak weekend
            info["closed_runs"] += 1
            info["closed_hours"] += n
        elif n <= FILL_MAX:
            p0, p1 = c[prev_i], o[next_i]
            for k in range(n):
                op = p0 + (p1 - p0) * k / n
                cl = p0 + (p1 - p0) * (k + 1) / n
                new_rows.append({"ts": int(run[k]), "open": op, "high": max(op, cl), "low": min(op, cl), "close": cl})
            info["fill_runs"] += 1
        else:  # przerwa w dostępie do danych tej pary — bariera dla transakcji (B12)
            gap_before[next_i] = n
            info["gaps"].append([int(run[0]), int(run[-1]) + H, n])
            info["gap_hours"] += n
    out = df.copy()
    out["filled"] = False
    out["gap_before"] = gap_before
    if new_rows:
        add = pd.DataFrame(new_rows)
        add["filled"] = True
        add["gap_before"] = 0
        out = pd.concat([out, add[out.columns]], ignore_index=True).sort_values("ts").reset_index(drop=True)
    out["ts"] = out["ts"].astype("int64")
    out["filled"] = out["filled"].astype(bool)
    out["gap_before"] = out["gap_before"].astype("int64")
    info["bars"] = int(len(out))
    info["filled"] = int(out["filled"].sum())
    info["from"], info["to"] = int(out["ts"].iloc[0]), int(out["ts"].iloc[-1])
    return out, info
