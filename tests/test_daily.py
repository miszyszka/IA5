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


def test_ohlc_flags_split_by_size_and_recency_d059():
    df = d1_frame()
    top = lambda i: max(df.loc[i, "open"], df.loc[i, "close"])   # noqa: E731
    df.loc[5, "high"] = top(5) - 0.0003                           # 3 pipsy, dawno
    df.loc[6, "high"] = top(6) - 0.0050                           # 50 pipsów, dawno
    df.loc[len(df) - 2, "high"] = top(len(df) - 2) - 0.0030       # 30 pipsów, świeże
    f = daily.d1_flags(df)
    assert (f["ohlc"], f["ohlc_big"], f["ohlc_big_recent"]) == (3, 2, 1) and round(f["ohlc_max_pips"]) == 50
    jpy = daily.d1_flags(df.assign(open=df.open * 100, high=df.high * 100, low=df.low * 100, close=df.close * 100), pip=0.01)
    assert jpy["ohlc"] == 3 and jpy["ohlc_big"] == 2                                   # rozmiar liczony w pipsach pary


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
    bad = dict(d1, USDJPY=d1["USDJPY"].assign(ts=d1["USDJPY"].ts + 3600))        # czas nie o północy — twarde, czerwone
    assert health.daily_candles(status, bad, now)["state"] == "bad"
    # D-059: Yahoo stale psuje ok. 2% świec — drobne i stare złe OHLC to informacja (✓), nie awaria
    quirk = d1["EURUSD"].copy()
    quirk.loc[40, "high"] = max(quirk.loc[40, "open"], quirk.loc[40, "close"]) - 0.0003        # 3 pipsy, dawno
    quirk.loc[len(quirk) - 2, "high"] = max(quirk.iloc[-2]["open"], quirk.iloc[-2]["close"]) - 0.0003   # 3 pipsy, świeże
    quirk.loc[50, "low"] = min(quirk.loc[50, "open"], quirk.loc[50, "close"]) + 0.0100          # 100 pipsów, ale dawno
    ok = health.daily_candles(status, dict(d1, EURUSD=quirk), now)
    assert ok["state"] == "ok" and "ze złym OHLC" in ok["text"]
    big = d1["EURUSD"].copy()
    big.loc[len(big) - 2, "low"] = min(big.iloc[-2]["open"], big.iloc[-2]["close"]) + 0.0100   # 100 pipsów w ostatnich 30 dniach
    w = health.daily_candles(status, dict(d1, EURUSD=big), now)
    assert w["state"] == "warn" and "EUR/USD" in w["text"] and "Yahoo" in w["fix"] and "Zwłoka" not in w["fix"]
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


def test_clean_d1_rejects_bad_bars_and_marks_long_gaps_d058(tmp_path):
    """D-058: warstwa czyszczenia D1 — złe OHLC, czas nie o północy, duplikat dnia → odrzucone; weekend i płaskie → poza sesją;
    1–2 brakujące dni → nic, ≥ 3 → gap_before; close_ts = północ następnego dnia w Londynie (23/25 h przy zmianie czasu)."""
    from ia5 import ready

    df = d1_frame("2023-01-02", "2024-12-31")
    bad = df.copy()
    bad.loc[5, "high"] = bad.loc[5, "low"] - 0.01                                  # złe OHLC
    bad.loc[10, ["open", "high", "low", "close"]] = 1.1                            # płaska
    sat = pd.Timestamp("2024-03-02", tz="Europe/London").value // 10**9           # sobota
    noon = pd.Timestamp("2024-03-05 12:00", tz="Europe/London").value // 10**9    # nie o północy
    bad = pd.concat([bad, pd.DataFrame({"ts": [sat, noon], "open": 1.1, "high": 1.11, "low": 1.09, "close": 1.1})])
    lo, hi = (pd.Timestamp(d, tz="Europe/London").value // 10**9 for d in ("2024-05-06", "2024-05-10"))
    bad = bad[(bad.ts < lo) | (bad.ts >= hi)]                                      # 4 dni robocze bez świecy
    one = pd.Timestamp("2024-08-14", tz="Europe/London").value // 10**9
    bad = bad[bad.ts != one]                                                       # 1 brakujący dzień
    out, info = daily.clean_d1(bad)
    assert info["rejected"] == 2 and info["flat"] == 1 and info["off_session"] == 1
    gi = int(out.index[out.gap_before > 0][0])
    assert info["gaps"] == [[int(out["ts"].iloc[gi - 1]), int(out["ts"].iloc[gi]), 4]]
    # 7 = 4 + 1 wycięte + świeca odrzucona (OHLC) + płaska — ich dni też są brakujące
    assert (out["gap_before"] > 0).sum() == 1 and info["missing_days"] == 7 and not out["filled"].any()
    assert ((out["close_ts"] - out["ts"]) // 3600 == 24).all()   # dni robocze: zmiana czasu zawsze w niedzielę
    sat, sat2 = (pd.Timestamp(d, tz="Europe/London").value // 10**9 for d in ("2025-03-29", "2025-10-25"))
    sun, sun2 = sat + 86400, sat2 + 86400                       # niedziele zmiany czasu: 23 h i 25 h
    assert ((daily.close_ts([sun, sun2]) - [sun, sun2]) // 3600).tolist() == [23, 25]
    # build_d1: opis z timeframe D1, para z za małą historią pominięta, bez zmian = bez przebudowy
    short = df.iloc[:100]
    b = ready.build_d1({"EURUSD": df, "USDJPY": short}, tmp_path / "d1_ready", pairs=("EURUSD", "USDJPY", "GBPUSD"))
    assert b["EURUSD"]["rebuilt"] and b["EURUSD"]["timeframe"] == "D1" and b["EURUSD"]["source"] == "yahoo"
    assert b["USDJPY"]["bars"] == 0 and not (tmp_path / "d1_ready" / "USDJPY.parquet").exists()
    assert (tmp_path / "d1_ready" / "EURUSD.parquet").exists() and "close_ts" in pd.read_parquet(tmp_path / "d1_ready" / "EURUSD.parquet")
    b2 = ready.build_d1({"EURUSD": df, "USDJPY": short}, tmp_path / "d1_ready", pairs=("EURUSD", "USDJPY", "GBPUSD"))
    assert not b2["EURUSD"]["rebuilt"]


# ---------- D-068: zamknięcie dnia w warstwie czyszczenia D1 (clean_d1 wersja 2) ----------

def yahoo_style(df: pd.DataFrame) -> pd.DataFrame:
    """Świece jak z Yahoo po 2011: close ≈ open tego samego dnia; prawdziwe zamknięcie = open następnego dnia."""
    out = df.copy()
    out["close"] = out["open"] * (1 + 1e-5)
    return out


def h1_for(day: str, closes: dict[int, float]) -> pd.DataFrame:
    """Świece H1 jednego dnia w Londynie: godzina otwarcia → zamknięcie."""
    ts = [int(pd.Timestamp(f"{day} {h:02d}:00", tz="Europe/London").timestamp()) for h in closes]
    c = list(closes.values())
    return pd.DataFrame({"ts": ts, "open": c, "high": c, "low": c, "close": c})


def test_clean_d1_close_is_next_days_open_d068():
    """Zamknięcie dnia = open następnego oczekiwanego dnia handlu (także piątek → poniedziałek); high/low obejmują nowe zamknięcie."""
    raw = yahoo_style(d1_frame("2024-01-01", "2024-03-29"))
    out, info = daily.clean_d1(raw)
    assert info["version"] == "2"
    nxt = out["open"].shift(-1)
    assert np.allclose(out["close"].iloc[:-1], nxt.iloc[:-1])
    fri = out[pd.to_datetime(out["ts"], unit="s", utc=True).dt.tz_convert("Europe/London").dt.dayofweek == 4].index[0]
    assert out["close"].iloc[fri] == out["open"].iloc[fri + 1]
    assert (out["high"] >= out["close"]).all() and (out["low"] <= out["close"]).all()
    assert (out["close_src"].iloc[:-1] == 1).all() and info["close_next_open"] == len(out) - 1


def test_clean_d1_keeps_yahoo_close_when_next_day_is_missing_d068():
    """Gdy następnego dnia handlu nie ma w danych (święto, koniec danych), zamknięcie zostaje z Yahoo i jest to policzone."""
    raw = yahoo_style(d1_frame("2024-01-01", "2024-03-29"))
    miss = midnight("2024-02-14")
    raw = raw[raw.ts != miss].reset_index(drop=True)
    out, info = daily.clean_d1(raw)
    before = out.index[out.ts == midnight("2024-02-13")][0]
    assert out["close_src"].iloc[before] == 0 and out["close"].iloc[before] == raw.close[raw.ts == midnight("2024-02-13")].iloc[0]
    assert out["close_src"].iloc[-1] == 0 and info["close_yahoo"] == 2


def test_clean_d1_prefers_last_h1_close_before_london_midnight_d068():
    """Gdy są świece H1 dnia, zamknięcie = close ostatniej świecy H1 tego dnia w Londynie (od 20:00) — także dla ostatniego dnia."""
    raw = yahoo_style(d1_frame("2024-01-01", "2024-03-29"))
    last_day, mid_day, early = "2024-03-29", "2024-03-13", "2024-03-20"
    h1 = pd.concat([h1_for(last_day, {21: 1.5001, 22: 1.5002}), h1_for(mid_day, {22: 1.4001, 23: 1.4002}),
                    h1_for(early, {14: 1.3001, 15: 1.3002})])        # dzień z ostatnią świecą o 15:00 — nie jest zamknięciem dnia
    out, info = daily.clean_d1(raw, h1=h1)
    row = lambda day: out[out.ts == midnight(day)].iloc[0]           # noqa: E731
    assert row(last_day)["close"] == 1.5002 and row(last_day)["close_src"] == 2
    assert row(mid_day)["close"] == 1.4002 and row(mid_day)["close_src"] == 2
    assert row(early)["close_src"] == 1 and info["close_h1"] == 2
    assert row(mid_day)["high"] >= 1.4002


def test_build_d1_rebuilds_when_h1_close_arrives_d068(tmp_path):
    """Plik do liczenia przebudowuje się, gdy dojdzie świeca H1 zamykająca ostatni dzień — bez zmiany świec D1."""
    from ia5 import ready

    raw = yahoo_style(d1_frame("2023-01-02", "2024-03-29"))
    out = tmp_path / "d1_ready"
    assert ready.build_d1({"EURUSD": raw}, out, pairs=("EURUSD",))["EURUSD"]["rebuilt"]
    assert not ready.build_d1({"EURUSD": raw}, out, pairs=("EURUSD",))["EURUSD"]["rebuilt"]
    h1 = {"EURUSD": h1_for("2024-03-29", {21: 1.5001, 22: 1.5002})}
    b = ready.build_d1({"EURUSD": raw}, out, pairs=("EURUSD",), h1=h1)
    assert b["EURUSD"]["rebuilt"] and b["EURUSD"]["close_h1"] == 1
    assert pd.read_parquet(out / "EURUSD.parquet")["close"].iloc[-1] == 1.5002
    assert not ready.build_d1({"EURUSD": raw}, out, pairs=("EURUSD",), h1=h1)["EURUSD"]["rebuilt"]
