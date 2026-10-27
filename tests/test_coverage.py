"""Mapa pokrycia (D-022): kalendarz, statusy miesięcy, luki wspólne i tylko jednej pary, potwierdzenie z Yahoo."""
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
from ia5 import coverage, dukascopy
from ia5.session import is_expected_bar

H = 3600


def ts(*a):
    return int(datetime(*a, tzinfo=UTC).timestamp())


def test_vector_calendar_equals_is_expected_bar_every_hour_since_2003():
    hours = np.arange(ts(2003, 1, 1), ts(2027, 1, 1), H, dtype=np.int64)
    ref = np.fromiter((is_expected_bar(int(t)) for t in hours), bool, len(hours))
    assert (coverage.expected_mask(hours) == ref).all()


def write_m1(folder, key, last_ts=None):
    folder.mkdir(parents=True, exist_ok=True)
    rows = [[last_ts, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]] if last_ts else []
    df = pd.DataFrame(rows, columns=dukascopy.COLS).astype("int64")
    df.to_parquet(folder / f"{key}.parquet", index=False)


def test_map_finds_planted_gaps_and_classifies_them(tmp_path, monkeypatch):
    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    until = date(2024, 3, 10)
    pairs = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP"]
    files = {p: ["2024-01", "2024-02", "2024-03"] for p in pairs}
    files["GBPUSD"] = ["2024-01", "2024-03"]          # luty: błąd pobierania
    for p, keys in files.items():
        for k in keys:
            last = ts(2024, 3, 10, 23, 59) if k == "2024-03" else ts(int(k[:4]), int(k[5:]), 15)
            write_m1(tmp_path / "m1" / p, k, None if (p == "EURGBP" and k == "2024-01") else last)  # EURGBP styczeń: brak u Dukascopy

    common = {ts(2024, 1, 3, h) for h in range(5)}                        # wszystkie pary (1.01 to święto, D-028)
    holes = {"EURUSD": {ts(2024, 2, 14, 3), ts(2024, 2, 14, 4)},
             "USDJPY": {ts(2024, 2, 9, 19), ts(2024, 2, 9, 20), ts(2024, 2, 11, 22), ts(2024, 2, 11, 23)}}  # przez weekend
    windows = {"2024-01": (ts(2024, 1, 1), ts(2024, 2, 1)), "2024-02": (ts(2024, 2, 1), ts(2024, 3, 1)),
               "2024-03": (ts(2024, 3, 1), ts(2024, 3, 11))}
    h1 = {}
    for p, keys in files.items():
        hrs = [t for k in keys if not (p == "EURGBP" and k == "2024-01") for t in coverage.expected_hours(*windows[k])]
        hrs = [int(t) for t in hrs if t not in common and t not in holes.get(p, set())]
        mins = [5 if (p == "EURUSD" and t == ts(2024, 3, 5, 10)) else 60 for t in hrs]
        h1[p] = pd.DataFrame({"ts": hrs, "minutes": mins})
    y_hours = [int(t) for t in coverage.expected_hours(ts(2024, 2, 1), ts(2024, 3, 10, 18))]
    yahoo = {"EURUSD": pd.DataFrame({"ts": y_hours}), "USDJPY": pd.DataFrame(columns=["ts"])}

    cov = coverage.build(tmp_path, h1, yahoo, failed={"GBPUSD": ["2024-02"]}, until=until, now=ts(2024, 3, 11, 6))
    d = cov["sources"]["dukascopy"]["pairs"]
    feb = len(coverage.expected_hours(*windows["2024-02"]))

    # statusy: pełny, błąd, brak u Dukascopy, bieżący w toku
    assert [m[0] for m in d["EURUSD"]["m"]] == [1, 1, 2]
    assert d["GBPUSD"]["m"][1][:3] == [4, feb, 0]
    assert d["EURGBP"]["m"][0][:3] == [3, 0, 0]
    assert d["EURUSD"]["m"][2][1] == len(coverage.expected_hours(*windows["2024-03"]))

    # 3 stycznia: brakuje wszystkim parom z danymi → wspólna, nie dziura
    assert d["EURUSD"]["m"][0][3:5] == [0, 5]
    assert [ts(2024, 1, 3), ts(2024, 1, 3, 5), 5, "w", -1] in d["EURUSD"]["gaps"]
    # dziura tylko EURUSD, Yahoo ma obie godziny → potwierdzona
    assert d["EURUSD"]["m"][1][3:5] == [2, 0]
    assert [ts(2024, 2, 14, 3), ts(2024, 2, 14, 5), 2, "p", 2] in d["EURUSD"]["gaps"]
    # luka przez weekend to jedna luka; Yahoo nie ma USDJPY → brak potwierdzenia
    assert [ts(2024, 2, 9, 19), ts(2024, 2, 12), 4, "p", -1] in d["USDJPY"]["gaps"]
    # cienka godzina: 5 aktywnych minut
    assert d["EURUSD"]["m"][2][5] == 1 and d["USDJPY"]["m"][2][5] == 0

    # Yahoo: pełne w swoim oknie, okno od lutego
    y = cov["sources"]["yahoo"]
    assert y["start"] == "2024-02" and y["pairs"]["EURUSD"]["gaps"] == []
    assert coverage.live_states(tmp_path, "GBPUSD", until, ["2024-02"]) == "ox~"
    assert coverage.live_states(tmp_path, "EURGBP", until) == "-o~"
    assert coverage.content_hash(cov) == coverage.content_hash({**cov, "generated": 1})


def test_incomplete_month_missing_days_are_not_holes(tmp_path, monkeypatch):
    """D-025: dzień, którego jeszcze nie pobrano, nie jest dziurą — liczy się osobno jako brakujący."""
    import json

    monkeypatch.setattr(dukascopy, "START", date(2024, 2, 1))
    f = tmp_path / "m1" / "EURUSD"
    write_m1(f, "2024-02", ts(2024, 2, 29, 20))
    (f / "2024-02.missing.json").write_text(json.dumps(["2024-02-07"]))
    hrs = [int(t) for t in coverage.expected_hours(ts(2024, 2, 1), ts(2024, 3, 1)) if not ts(2024, 2, 7) <= t < ts(2024, 2, 8)]
    cov = coverage.build(tmp_path, {"EURUSD": pd.DataFrame({"ts": hrs, "minutes": 60})}, {}, until=date(2024, 3, 5), now=ts(2024, 3, 6))
    row = cov["sources"]["dukascopy"]["pairs"]["EURUSD"]["m"][0]
    assert row[0] == coverage.INCOMPLETE and row[3] == 0 and row[6] == 24 and row[1] == row[2]
    assert coverage.live_states(tmp_path, "EURUSD", date(2024, 3, 5)) == "!."


def test_holiday_is_not_expected_and_quiet_gap_is_not_a_hole(tmp_path, monkeypatch):
    """D-028: 25.12 nie jest oczekiwany; krótka luka bez zmiany ceny to „bez ruchu”, nie dziura."""
    from ia5.session import is_expected_bar

    assert not is_expected_bar(ts(2024, 12, 25, 10)) and is_expected_bar(ts(2024, 12, 25, 22))
    assert not is_expected_bar(ts(2025, 1, 1, 5)) and not is_expected_bar(ts(2024, 12, 31, 21))
    monkeypatch.setattr(dukascopy, "START", date(2024, 2, 1))
    write_m1(tmp_path / "m1" / "EURUSD", "2024-02", ts(2024, 2, 29, 20))
    hrs = [int(t) for t in coverage.expected_hours(ts(2024, 2, 1), ts(2024, 3, 1))]
    quiet = {ts(2024, 2, 6, 21)}                       # cena przed i po taka sama
    moved = {ts(2024, 2, 13, 10), ts(2024, 2, 13, 11)}  # cena po luce inna
    keep = [t for t in hrs if t not in quiet | moved]
    price = np.array([1.1 if t < ts(2024, 2, 13, 12) else 1.2 for t in keep])
    df = pd.DataFrame({"ts": keep, "minutes": 60, "open": price, "close": price})
    cov = coverage.build(tmp_path, {"EURUSD": df}, {}, until=date(2024, 3, 5), now=ts(2024, 3, 6))
    d = cov["sources"]["dukascopy"]["pairs"]["EURUSD"]
    kinds = {g[0]: g[3] for g in d["gaps"]}
    assert kinds == {ts(2024, 2, 6, 21): "q", ts(2024, 2, 13, 10): "p"}
    assert d["m"][0][3:5] == [2, 1]  # dziury 2 h, „bez ruchu” 1 h liczona razem ze wspólnymi
