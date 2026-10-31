"""Mapa pokrycia (D-022, D-039): kalendarz, statusy miesięcy, luki wspólne, tylko jednej pary i „bez ruchu” — świece Yahoo."""
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from ia5 import coverage
from ia5.session import is_expected_bar

H = 3600


def ts(*a):
    return int(datetime(*a, tzinfo=UTC).timestamp())


def test_vector_calendar_equals_is_expected_bar_every_hour_since_2003():
    hours = np.arange(ts(2003, 1, 1), ts(2027, 1, 1), H, dtype=np.int64)
    ref = np.fromiter((is_expected_bar(int(t)) for t in hours), bool, len(hours))
    assert (coverage.expected_mask(hours) == ref).all()


def frame(hours, price=1.1):
    p = np.full(len(hours), price) if np.isscalar(price) else price
    return pd.DataFrame({"ts": [int(t) for t in hours], "open": p, "high": p, "low": p, "close": p})


def test_map_finds_planted_gaps_and_classifies_them():
    pairs = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP"]
    base = [int(t) for t in coverage.expected_hours(ts(2024, 1, 2), ts(2024, 3, 10, 18))]
    common = {ts(2024, 1, 7, 22), ts(2024, 1, 7, 23)}                     # wszystkie pary, niedziela 22–23 — granica tygodnia
    holes = {"EURUSD": {ts(2024, 2, 14, 3), ts(2024, 2, 14, 4)},
             "USDJPY": {ts(2024, 2, 9, 19), ts(2024, 2, 9, 20), ts(2024, 2, 11, 22), ts(2024, 2, 11, 23)}}  # przez weekend
    yahoo = {}
    for p in pairs:
        hrs = [t for t in base if t not in common and t not in holes.get(p, set())]
        price = np.array([1.1 + 0.001 * (i % 7) for i in range(len(hrs))])   # cena się rusza — luki nie są „bez ruchu”
        yahoo[p] = frame(hrs, price)
    cov = coverage.build(yahoo, now=ts(2024, 3, 11, 6))
    d = cov["sources"]["yahoo"]["pairs"]
    assert cov["sources"]["yahoo"]["start"] == "2024-01" and list(cov["sources"]) == ["yahoo"]
    assert [m[0] for m in d["EURUSD"]["m"]] == [1, 1, 2]                   # bieżący miesiąc w toku
    assert d["EURUSD"]["m"][0][3:5] == [0, 2]                               # granica tygodnia, nie dziura
    assert [ts(2024, 1, 7, 22), ts(2024, 1, 8), 2, "w", 4] in d["EURUSD"]["gaps"]   # 4 = wszystkie pary
    assert d["EURUSD"]["m"][1][3:5] == [2, 0]
    assert [ts(2024, 2, 14, 3), ts(2024, 2, 14, 5), 2, "p", 1] in d["EURUSD"]["gaps"]
    assert [ts(2024, 2, 9, 19), ts(2024, 2, 12), 4, "p", 1] in d["USDJPY"]["gaps"]  # przez weekend = jedna luka, > 3 h
    assert coverage.content_hash(cov) == coverage.content_hash({**cov, "generated": 1})


def test_holiday_is_not_expected_and_quiet_gap_is_not_a_hole():
    """D-028: 25.12 nie jest oczekiwany; krótka luka bez zmiany ceny to „bez ruchu”, nie dziura."""
    assert not is_expected_bar(ts(2024, 12, 25, 10)) and is_expected_bar(ts(2024, 12, 25, 22))
    assert not is_expected_bar(ts(2025, 1, 1, 5)) and not is_expected_bar(ts(2024, 12, 31, 21))
    hrs = [int(t) for t in coverage.expected_hours(ts(2024, 2, 1), ts(2024, 3, 1))]
    quiet = {ts(2024, 2, 6, 21)}                       # cena przed i po taka sama
    moved = {ts(2024, 2, 13, 10), ts(2024, 2, 13, 11)}  # cena po luce inna
    keep = [t for t in hrs if t not in quiet | moved]
    price = np.array([1.1 if t < ts(2024, 2, 13, 12) else 1.2 for t in keep])
    cov = coverage.build({"EURUSD": frame(keep, price)}, now=ts(2024, 3, 6))
    d = cov["sources"]["yahoo"]["pairs"]["EURUSD"]
    assert {g[0]: g[3] for g in d["gaps"]} == {ts(2024, 2, 6, 21): "q", ts(2024, 2, 13, 10): "p"}
    assert d["m"][0][3:5] == [2, 1]  # dziury 2 h, „bez ruchu” 1 h liczona razem ze wspólnymi
