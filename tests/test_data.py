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
