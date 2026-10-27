import lzma
from datetime import date

import numpy as np
import pandas as pd
from ia5.bars import m1_to_h1
from ia5.dukascopy import REC, day_url, decode_bi5, month_days, point
from ia5.quality import bar_flags, compare_sources, cross_check
from ia5.session import expected_ts, is_expected_bar

DAY = 1761436800  # 2025-10-26 00:00 UTC


def make_bi5(rows, pt):
    raw = b"".join(REC.pack(t, round(o * pt), round(c * pt), round(lo * pt), round(h * pt), v)
                   for t, o, h, lo, c, v in rows)
    return lzma.compress(raw, format=lzma.FORMAT_ALONE)


def test_url_month_is_zero_based():
    assert day_url("EURUSD", date(2024, 1, 15), "BID").endswith("/EURUSD/2024/00/15/BID_candles_min_1.bi5")


def test_decode_bi5_order_open_close_low_high():
    raw = make_bi5([(60, 1.1, 1.2, 1.0, 1.15, 3.5)], point("EURUSD"))
    out = decode_bi5(raw, DAY, point("EURUSD"))
    ts, o, h, lo, c, v = out[0]
    assert ts == DAY + 60
    assert (o, h, lo, c) == (1.1, 1.2, 1.0, 1.15)
    assert v == 3.5


def test_jpy_point():
    assert point("USDJPY") == 1000 and point("EURGBP") == 100000
    raw = make_bi5([(0, 150.123, 150.2, 150.0, 150.1, 1.0)], 1000)
    assert decode_bi5(raw, DAY, 1000)[0][1] == 150.123


def test_empty_file():
    assert decode_bi5(b"", DAY, 100000).shape == (0, 6)


def test_month_days_skip_saturday():
    days = month_days(2026, 10, date(2026, 10, 31))
    assert all(d.isoweekday() != 6 for d in days)
    assert date(2026, 10, 31) not in days  # sobota


def m1(ts, bid, ask, vol=1.0):
    return dict(ts=ts, bo=bid[0], bh=bid[1], bl=bid[2], bc=bid[3], bv=vol,
                ao=ask[0], ah=ask[1], al=ask[2], ac=ask[3], av=vol)


def test_m1_to_h1_mid_and_hours():
    rows = [
        m1(DAY + 0, (1.0, 1.2, 0.9, 1.1), (1.2, 1.4, 1.1, 1.3)),
        m1(DAY + 60, (1.1, 1.5, 1.0, 1.4), (1.3, 1.7, 1.2, 1.6)),
        m1(DAY + 120, (9, 9, 9, 9), (9, 9, 9, 9), vol=0.0),  # brak handlu — pomijana
        m1(DAY + 3600, (2.0, 2.0, 2.0, 2.0), (2.2, 2.2, 2.2, 2.2)),
    ]
    h1 = m1_to_h1(pd.DataFrame(rows))
    assert list(h1.ts) == [DAY, DAY + 3600]
    r = h1.iloc[0]
    assert np.isclose(r.open, 1.1) and np.isclose(r.high, 1.6) and np.isclose(r.low, 1.0)
    assert np.isclose(r.close, 1.5) and r.minutes == 2
    assert np.isclose(r.spread_avg, 0.2)


def test_session_weekend():
    sat = 1761307200  # 2025-10-24 12:00 UTC piątek
    assert is_expected_bar(sat)
    assert not is_expected_bar(sat + 24 * 3600)  # sobota
    assert expected_ts(DAY + 10 * 3600) == 1761336000  # niedziela 10:00 → piątek 20:00


def test_bar_flags_and_gaps():
    ts = [DAY + 86400 + k * 3600 for k in (0, 1, 4)]  # poniedziałek, luka 2 godzin
    df = pd.DataFrame({"ts": ts, "open": [1, 1, 1], "high": [1.1, 0.9, 1.1],
                       "low": [0.9, 0.8, 0.9], "close": [1, 1, 1]})
    f = bar_flags(df)
    assert f["ohlc"] == 1 and f["gaps"] == 1 and f["gap_list"][0] == (ts[1] + 3600, 2)


def test_cross_and_compare():
    ts = [DAY + 86400]
    h1 = {p: pd.DataFrame({"ts": ts, "close": [c]}) for p, c in
          {"EURUSD": 1.1, "USDJPY": 150.0, "EURJPY": 165.05, "GBPUSD": 1.3, "EURGBP": 0.8462}.items()}
    res = cross_check(h1)
    assert np.isclose(res["EURJPY"]["median"], 5.0)
    assert res["EURGBP"]["median"] < 1
    c = compare_sources(h1["EURUSD"], pd.DataFrame({"ts": ts, "close": [1.1002]}), "EURUSD")
    assert np.isclose(c["median"], 2.0)


def test_sync_saves_partial_month_and_fetches_only_missing_days(tmp_path, monkeypatch):
    """D-025: błąd jednego dnia nie wyrzuca miesiąca — pobrane dni są zapisane, brakujący dzień trafia na listę
    i przy następnym uruchomieniu pobierany jest tylko on. Błąd sieci nie przerywa synchronizacji."""
    import json

    from ia5 import dukascopy

    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)
    bad_day = {date(2024, 2, 7)}
    calls = []

    def fake_fetch(pair, d):
        calls.append(d)
        if d in bad_day:
            raise RuntimeError("Dukascopy: timeout")
        return pd.DataFrame([[int(pd.Timestamp(d).timestamp()), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], columns=dukascopy.COLS)

    class Today(dukascopy.datetime):
        @classmethod
        def now(cls, tz=None):
            return dukascopy.datetime(2024, 4, 10, tzinfo=tz)

    monkeypatch.setattr(dukascopy, "fetch_day", fake_fetch)
    monkeypatch.setattr(dukascopy, "datetime", Today)
    codes = []
    r = dukascopy.sync_pair("EURUSD", tmp_path, log=lambda m: None, on_month=lambda y, m, c: codes.append(c))
    folder = tmp_path / "m1" / "EURUSD"
    assert r["failed"] == ["2024-02"] and codes == ["o", "!", "o", "~"]
    assert sorted(p.name for p in folder.glob("*.parquet")) == ["2024-01.parquet", "2024-02.parquet", "2024-03.parquet", "2024-04.parquet"]
    assert json.loads((folder / "2024-02.missing.json").read_text()) == ["2024-02-07"]
    assert len(pd.read_parquet(folder / "2024-02.parquet")) == len(dukascopy.month_days(2024, 2, date(2024, 4, 9))) - 1
    # następne uruchomienie: tylko brakujący dzień lutego + dni kwietnia po ostatnim zapisanym (9-ty już jest)
    bad_day.clear()
    calls.clear()
    dukascopy.sync_pair("EURUSD", tmp_path, log=lambda m: None)
    assert calls == [date(2024, 2, 7)]
    assert not (folder / "2024-02.missing.json").exists()
    assert len(pd.read_parquet(folder / "2024-02.parquet")) == len(dukascopy.month_days(2024, 2, date(2024, 4, 9)))
    assert len(dukascopy.load_m1("EURUSD", tmp_path)) == sum(len(dukascopy.month_days(2024, m, date(2024, 4, 9))) for m in (1, 2, 3, 4))


def test_get_retries_then_raises_and_404_is_empty(monkeypatch):
    from ia5 import dukascopy

    class R:
        def __init__(self, code):
            self.status_code, self.content = code, b"x"

    seq = iter([R(503), R(503), R(200)])
    monkeypatch.setattr(dukascopy, "_session", lambda: type("S", (), {"get": lambda self, u, timeout: next(seq)})())
    monkeypatch.setattr(dukascopy.time, "sleep", lambda s: None)
    assert dukascopy._get("u", tries=3) == b"x"
    monkeypatch.setattr(dukascopy, "_session", lambda: type("S", (), {"get": lambda self, u, timeout: R(404)})())
    assert dukascopy._get("u") == b""
    monkeypatch.setattr(dukascopy, "_session", lambda: type("S", (), {"get": lambda self, u, timeout: R(500)})())
    import pytest
    with pytest.raises(RuntimeError, match="HTTP 500"):
        dukascopy._get("u", tries=2)


def test_month_written_mid_month_is_refetched(tmp_path, monkeypatch):
    """Miesiąc zapisany w trakcie (np. 15-go) nie może zostać „zamknięty" z luką do końca miesiąca."""
    import os

    from ia5 import dukascopy

    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)
    folder = tmp_path / "m1" / "EURUSD"
    folder.mkdir(parents=True)

    def write(name, last_day, written):
        ts = int(pd.Timestamp(last_day, tz="UTC").timestamp()) if last_day else 0
        df = pd.DataFrame([[ts, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], columns=dukascopy.COLS) if last_day else \
            pd.DataFrame(columns=dukascopy.COLS).astype("int64")
        df.to_parquet(folder / name, index=False)
        w = pd.Timestamp(written, tz="UTC").timestamp()
        os.utime(folder / name, (w, w))

    write("2024-01.parquet", None, "2024-01-20")               # pusty: Dukascopy nie ma tego miesiąca
    write("2024-02.parquet", "2024-02-14", "2024-02-15")       # zapisany 15-go → niepełny
    write("2024-03.parquet", "2024-03-29", "2024-03-30")       # 31.03 to niedziela, ostatni handlowy = pt 29
    assert dukascopy.last_trading_day(2024, 3) == date(2024, 3, 29)
    assert dukascopy.months_to_sync(tmp_path, "EURUSD", date(2024, 4, 9)) == [(2024, 2), (2024, 4)]
    # niepełny, ale zapisany długo po końcu miesiąca (np. święto bez notowań) — nie pobieramy w kółko
    write("2024-02.parquet", "2024-02-27", "2024-03-10")
    assert dukascopy.months_to_sync(tmp_path, "EURUSD", date(2024, 4, 9)) == [(2024, 4)]


def test_sync_retries_throttled_days_in_same_run(tmp_path, monkeypatch):
    """D-026: dzień odrzucony przez serwer (dławienie) jest ponawiany wolniej w tym samym przebiegu."""
    from ia5 import dukascopy

    monkeypatch.setattr(dukascopy, "START", date(2024, 3, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)
    seen = set()

    def flaky(pair, d):
        if d.day % 3 == 0 and d not in seen:  # co trzeci dzień: pierwsza próba odrzucona
            seen.add(d)
            raise RuntimeError("Connection timed out")
        return pd.DataFrame([[int(pd.Timestamp(d).timestamp()), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]], columns=dukascopy.COLS)

    class Today(dukascopy.datetime):
        @classmethod
        def now(cls, tz=None):
            return dukascopy.datetime(2024, 4, 2, tzinfo=tz)

    monkeypatch.setattr(dukascopy, "fetch_day", flaky)
    monkeypatch.setattr(dukascopy, "datetime", Today)
    r = dukascopy.sync_pair("EURUSD", tmp_path, log=lambda m: None)
    assert r["failed"] == [] and not list((tmp_path / "m1" / "EURUSD").glob("*.missing.json"))
