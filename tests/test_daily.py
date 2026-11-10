"""Świece dzienne D1 (D-053): kalendarz dnia w strefie Yahoo, kontrola jakości, łączenie kopii, przegląd zdrowia, sprzątanie."""
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from ia5 import daily, health

LON = ZoneInfo("Europe/London")


def ts_utc(s: str) -> int:
    return int(datetime.fromisoformat(s).replace(tzinfo=UTC).timestamp())


def midnight(day: str) -> int:
    return int(datetime.fromisoformat(day).replace(tzinfo=LON).timestamp())


def d1_frame(start="2024-01-01", end="2024-12-31", seed=1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    days, d = [], date.fromisoformat(start)
    while d <= date.fromisoformat(end):
        if daily.is_expected_day(d):
            days.append(d.isoformat())
        d += timedelta(days=1)
    c = 1.1 * np.exp(np.cumsum(rng.normal(0, 4e-3, len(days))))
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame({"ts": [midnight(x) for x in days], "open": o, "high": np.maximum(o, c) * 1.002,
                         "low": np.minimum(o, c) * 0.998, "close": c})


def test_ts_is_london_midnight_in_summer_and_winter():
    assert midnight("2024-07-01") == ts_utc("2024-06-30T23:00:00")
    assert midnight("2024-01-15") == ts_utc("2024-01-15T00:00:00")
    assert list(daily.day_of([midnight("2024-07-01"), midnight("2024-01-15")])) == ["2024-07-01", "2024-01-15"]


def test_expected_day_skips_weekend_holidays_and_open_day():
    assert daily.expected_day(ts_utc("2026-11-10T16:33:00")) == "2026-11-09"     # wtorek → poniedziałek
    assert daily.expected_day(ts_utc("2026-11-09T00:00:30")) == "2026-11-06"     # tuż po północy: niedziela → piątek
    assert daily.expected_day(ts_utc("2026-11-10T00:01:30")) == "2026-11-09"
    assert daily.expected_day(ts_utc("2026-12-26T09:00:00")) == "2026-12-24"     # 25.12 bez świecy
    assert daily.expected_day(ts_utc("2026-07-07T23:30:00")) == "2026-07-07"     # w Londynie już 8.07
    assert daily.days_behind("2026-11-06", "2026-11-09") == 1 and daily.days_behind("2026-11-09", "2026-11-09") == 0


def test_clean_series_has_no_hard_flags():
    f = daily.d1_flags(d1_frame())
    assert f["bars"] > 250 and f["ohlc"] == f["price"] == f["offgrid"] == f["dup_days"] == f["weekend"] == 0
    assert f["missing"] == 0 and f["first_day"] == "2024-01-02"     # 1.01 — święto bez świecy


def test_flags_report_and_do_not_fix():
    df = d1_frame()
    df.loc[5, "high"] = df.loc[5, "low"] * 0.9                 # zły OHLC
    df.loc[10, "ts"] += 3600                                   # nie o północy
    df = pd.concat([df.drop(index=20), df.iloc[[30]].assign(open=1, high=1, low=1, close=1, ts=midnight("2024-03-02"))])
    f = daily.d1_flags(df.sort_values("ts"))
    assert f["ohlc"] == 1 and f["offgrid"] == 1 and f["weekend"] == 1 and f["flat"] == 1
    assert f["missing"] == 2                                   # usunięty dzień + dzień ze świecą nie o północy
    assert len(df) == f["bars"]                                # nic nie usunięte


def test_merge_replaces_read_years_entirely_and_keeps_others():
    old = d1_frame("2023-01-02", "2024-12-31")
    new = d1_frame("2024-01-01", "2024-06-30", seed=9)          # Firestore: rok 2024 ma teraz mniej świec
    out = daily.merge(old, new, ["2024"])
    years = pd.Series(daily.day_of(out.ts)).str[:4]
    assert (years == "2023").sum() == (pd.Series(daily.day_of(old.ts)).str[:4] == "2023").sum()
    assert (years == "2024").sum() == len(new) and out.ts.is_monotonic_increasing
    assert daily.years_to_read(midnight("2024-12-31"), ts_utc("2026-01-03T12:00:00")) == ["2024", "2025", "2026"]


def test_health_daily_check():
    now = ts_utc("2025-01-03T12:00:00")                         # oczekiwany dzień: 2025-01-02
    d1 = {p: d1_frame("2024-01-01", "2025-01-02", seed=i) for i, p in enumerate(health.PAIRS)}
    status = {"d1": {"tz": "Europe/London", "pairs": {p: {"lastTs": int(df.ts.max()), "count": len(df)} for p, df in d1.items()}}}
    assert health.daily_candles(status, d1, now)["state"] == "ok"
    assert health.daily_candles({}, {}, now)["state"] == "warn"                      # przed backfillD1()
    stale = dict(d1, EURUSD=d1["EURUSD"].iloc[:-3])
    assert health.daily_candles(status, stale, now)["state"] == "warn"
    bad = dict(d1, USDJPY=d1["USDJPY"].assign(high=d1["USDJPY"].low * 0.5))
    assert health.daily_candles(status, bad, now)["state"] == "bad"
    assert health.daily_candles(status, {p: v for p, v in d1.items() if p != "AUDUSD"}, now)["state"] == "bad"


def test_local_cleanup_keeps_d1_copy(tmp_path, monkeypatch):
    from ia5 import cli, store

    data = tmp_path / "data"
    for d in ("yahoo", "h1_ready", "yahoo_d1"):
        (data / d).mkdir(parents=True)
    (data / "yahoo_d1" / "EURUSD.parquet").write_bytes(b"1")
    (data / "yahoo_d1" / "XAUUSD.parquet").write_bytes(b"1")
    monkeypatch.setattr(cli, "DATA", data)
    monkeypatch.setattr(store, "YAHOO", data / "yahoo")
    monkeypatch.setattr(store, "YAHOO_D1", data / "yahoo_d1")
    removed = cli.enforce_local_data(log=lambda m: None)
    assert [f.name for f in (data / "yahoo_d1").iterdir()] == ["EURUSD.parquet"] and len(removed) == 1
    assert health.local_data(tmp_path, {})["state"] == "ok"
