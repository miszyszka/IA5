"""D-075: świece tygodniowe (W1) z dziennych i wykonanie sygnału D1 na świecach H1 (EXECUTE = "H1", ENTRY_HOUR)."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5.backtest import run_file
from ia5.check import check_code_on, synthetic_d1, synthetic_h1
from ia5.daily import close_ts
from ia5.frames import entry_bar_index, to_weekly
from ia5.sandbox import StrategyError, read_settings


@pytest.fixture(scope="module")
def syn(tmp_path_factory):
    return synthetic_h1(tmp_path_factory.mktemp("syn"), n=3000)


@pytest.fixture(scope="module")
def syn_d1(tmp_path_factory):
    return synthetic_d1(tmp_path_factory.mktemp("syn_d1"), days=1200)


def test_to_weekly_aggregates_monday_to_friday():
    days = pd.bdate_range("2026-01-05", periods=10, tz="Europe/London")      # 2 tygodnie pn–pt
    ts = np.asarray((days.tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1), "int64")
    d = pd.DataFrame({"ts": ts, "open": np.arange(10.0) + 1, "high": np.arange(10.0) + 2, "low": np.arange(10.0),
                      "close": np.arange(10.0) + 1.5, "close_ts": close_ts(ts), "gap_before": 0})
    d.loc[7, "gap_before"] = 3
    w = to_weekly(d)
    assert len(w) == 2
    assert w.loc[0, "ts"] == ts[0] and w.loc[0, "close_ts"] == close_ts(ts)[4]
    assert (w.loc[0, "open"], w.loc[0, "high"], w.loc[0, "low"], w.loc[0, "close"]) == (1.0, 6.0, 0.0, 5.5)
    assert list(w["gap_before"]) == [0, 1]                                  # przerwa w danych w drugim tygodniu


def test_entry_bar_index_picks_polish_hour_after_day_close():
    h1 = 1767571200 + 3600 * np.arange(24 * 7)                             # 2026-01-05 00:00 UTC (zima: PL = UTC+1)
    day_close = np.array([1767571200 + 86400])                              # wtorek 00:00 UTC
    e = entry_bar_index(h1, day_close, 8)
    assert pd.to_datetime(h1[e[0]], unit="s", utc=True).tz_convert("Europe/Warsaw").hour == 8
    assert h1[e[0]] >= day_close[0] and h1[e[0]] - day_close[0] < 86400
    assert entry_bar_index(h1, np.array([h1[-1] + 3600]), 8)[0] == -1       # po końcu danych — brak


def test_w1_strategy_checks(syn, syn_d1):
    code = 'TIMEFRAME = "W1"\nHYPOTHESIS = "Trend tygodniowy."\ndef signals(df, p, ind):\n' \
           '    return ind.cross_above(df.close, ind.sma(df.close, 10)).astype("int8")\n'
    res = check_code_on(code, syn, d1_dir=syn_d1)
    assert res["ok"], res["errors"]
    assert res["meta"]["timeframe"] == "W1" and res["meta"]["hours"] is False
    assert res["signals"]["signals"].sum() > 0


def test_execute_settings():
    s = read_settings({"TIMEFRAME": "D1", "EXECUTE": "H1", "ENTRY_HOUR": 9})
    assert s["execute"] == "H1" and s["hours"] == [9, 10]
    for bad in ({"EXECUTE": "H1"}, {"TIMEFRAME": "D1", "EXECUTE": "H4"}, {"TIMEFRAME": "D1", "EXECUTE": "H1", "ENTRY_HOUR": 3}):
        with pytest.raises(StrategyError):
            read_settings(bad)


def test_execute_d1_signal_on_h1(syn, syn_d1, tmp_path):
    code = '''
TIMEFRAME = "D1"
EXECUTE = "H1"
ENTRY_HOUR = 8
HYPOTHESIS = "Sygnał dzienny, wejście rano po rolowaniu."
EXITS = [{"kind": "time", "n": 24, "cap": 24}, {"kind": "atr", "n": 14, "tp": 2, "sl": 1, "cap": 48, "weekend": True}]
def signals(df, p, ind):
    r = ind.rsi(df.close, 2)
    return ind.cross_below(r, 20).astype("int8") - ind.cross_above(r, 80).astype("int8")
'''
    out = run_file(code, "exe", syn, tmp_path, log=lambda *_: None, d1_dir=syn_d1)
    m = json.loads((out / "manifest.json").read_text())
    assert m["execute"] == "H1" and m["entry_hour"] == 8 and m["timeframe"] == "D1"
    t = pd.read_parquet(out / "trades.parquet")
    assert len(t)
    hrs = pd.to_datetime(t["entry_ts"], unit="s", utc=True).dt.tz_convert("Europe/Warsaw").dt.hour
    assert (hrs == 8).all()
    h1 = pd.read_parquet(syn / "EURUSD.parquet")
    assert t["entry_ts"].min() >= h1["ts"].iloc[0]
    v = json.loads((out / "validation.json").read_text())
    assert "correlation" in v
