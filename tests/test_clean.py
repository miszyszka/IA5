"""D8, B12, D-039: warstwa czyszczenia świec Yahoo (odrzucanie złych świec, uzupełnianie ≤ 3 h, przerwy w danych,
rynek nieczynny we wszystkich parach), anulowanie transakcji, dane do liczenia, sprzątanie po Dukascopy — bez sieci."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5.clean import FILL_MAX, clean_h1
from ia5.engine import Exit, data_cancel, prepare, run

T0 = 1761523200  # poniedziałek 2025-10-27 00:00 UTC
H = 3600


def walk(n, seed=1, t0=T0):
    rng = np.random.default_rng(seed)
    c = 1.1 + np.cumsum(rng.normal(0, 0.0005, n))
    o = np.concatenate([[1.1], c[:-1]])
    return pd.DataFrame({"ts": t0 + H * np.arange(n), "open": o, "high": np.maximum(o, c) + 0.0003,
                         "low": np.minimum(o, c) - 0.0003, "close": c})


def test_single_missing_bar_is_filled_and_marked():
    raw = walk(30)
    hole = raw.iloc[10]
    df, info = clean_h1(raw.drop(index=10))
    row = df[df.ts == hole.ts].iloc[0]
    assert bool(row.filled)
    assert row.open == pytest.approx(raw.close[9]) and row.close == pytest.approx(raw.open[11])  # od zamknięcia do otwarcia
    assert row.high == max(row.open, row.close) and row.low == min(row.open, row.close)
    assert info["filled"] == 1 and info["gaps"] == [] and df.gap_before.sum() == 0
    pd.testing.assert_frame_equal(df[~df.filled].drop(columns=["filled", "gap_before"]).reset_index(drop=True),
                                  raw.drop(index=10).reset_index(drop=True), check_dtype=False)  # dane surowe bez zmian


def test_three_hours_filled_four_is_a_data_gap():
    raw = walk(40)
    df3, i3 = clean_h1(raw.drop(index=[10, 11, 12]))
    assert i3["filled"] == FILL_MAX == 3
    f = df3[df3.filled]
    assert f.close.iloc[-1] == pytest.approx(raw.open[13]) and f.open.iloc[0] == pytest.approx(raw.close[9])
    df4, i4 = clean_h1(raw.drop(index=[20, 21, 22, 23]))
    assert i4["filled"] == 0 and i4["gaps"] == [[int(raw.ts[20]), int(raw.ts[23]) + H, 4]]
    assert df4.loc[df4.ts == raw.ts[24], "gap_before"].item() == 4


def test_week_boundary_gap_is_not_a_barrier_but_long_one_is():
    """Yahoo zaczyna tydzień o 1–2 h później niż kalendarz (niedziela 22:00 UTC) — to granica tygodnia, nie przerwa.
    6 h braku od niedzieli 22:00 to już przerwa w danych (rynek działał, Yahoo nie)."""
    sun = 1762120800  # niedziela 2025-11-02 22:00 UTC
    fri = [1761868800 + H * k for k in range(21)]               # pt 00–20 UTC
    late2 = [sun + H * k for k in range(2, 30)]                   # nd 22–23 brak
    late6 = [sun + H * k for k in range(6, 30)]                   # nd 22 – pn 03 brak
    for ts, gap in ((late2, 0), (late6, 6)):
        c = 1.1 + np.arange(len(fri) + len(ts)) * 1e-5
        df, info = clean_h1(pd.DataFrame({"ts": fri + ts, "open": c, "high": c + 2e-4, "low": c - 2e-4, "close": c}))
        assert int(df.gap_before.sum()) == gap and info["filled"] == 0
        assert info["closed_hours"] == (2 if gap == 0 else 0)


def test_off_session_stale_bars_are_dropped():
    """Yahoo dopisuje płaskie świece po piątkowym zamknięciu i w święta — odrzucone; świeca z ruchem poza kalendarzem zostaje."""
    fri20 = 1761940800  # piątek 2025-10-31 20:00 UTC
    df = pd.DataFrame({"ts": [fri20, fri20 + H, fri20 + 2 * H], "open": [1.1, 1.1, 1.1],
                       "high": [1.101, 1.1005, 1.1], "low": [1.099, 1.0995, 1.1], "close": [1.1, 1.1002, 1.1]})
    xmas = pd.DataFrame({"ts": [1766656800], "open": [1.2], "high": [1.201], "low": [1.199], "close": [1.2]})  # 25.12 10:00
    out, info = clean_h1(pd.concat([df, xmas], ignore_index=True))
    assert info["off_session"] == 2 and out.ts.tolist() == [fri20, fri20 + H]


def test_invalid_bar_is_rejected_and_counted():
    raw = walk(30)
    raw.loc[5, "high"] = raw.loc[5, "low"] - 0.001     # high < low: łamie D5
    raw.loc[7, "close"] = np.nan
    df, info = clean_h1(raw)
    assert info["rejected"] == 2 and info["rejected_ts"] == [int(raw.ts[5]), int(raw.ts[7])]
    assert df.loc[df.ts == raw.ts[5], "filled"].item() and df.loc[df.ts == raw.ts[7], "filled"].item()


def test_weekend_and_holiday_are_not_gaps():
    fri = pd.DataFrame({"ts": [1761933600 + H * k for k in range(3)]})  # pt 18, 19, 20 UTC
    sun = pd.DataFrame({"ts": [1762120800 + H * k for k in range(2)]})  # nd 22, 23 UTC
    mon = pd.DataFrame({"ts": [1762128000 + H * k for k in range(2)]})  # pn 00, 01 UTC
    df = pd.concat([fri, sun, mon], ignore_index=True)
    for c in ("open", "high", "low", "close"):
        df[c] = 1.1
    _, info = clean_h1(df)
    assert info["filled"] == 0 and info["gaps"] == []


def test_engine_cancels_trades_on_data_gap_and_filled_entry():
    raw = walk(60).drop(index=[20] + list(range(40, 45)))   # 1 świeca (uzupełniona) i 5 godzin (przerwa w danych)
    df, info = clean_h1(raw)
    assert info["filled"] == 1 and len(info["gaps"]) == 1
    idx = {int(t): i for i, t in enumerate(df.ts)}
    sig = np.zeros(len(df), np.int8)
    for h in (19, 25, 37):   # wejście na uzupełnionej świecy; czysta transakcja; transakcja przez przerwę
        sig[idx[T0 + h * H]] = 1
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=4, cap=4)], hours=False)
    out = res["outcomes"]
    assert res["skipped"]["luka_danych"] == 1 and res["skipped"]["swieca_uzupelniona"] == 1
    assert len(out) == 1
    assert res["entries"].set_index("entry_id").loc[out.entry_id.iloc[0]].entry_ts == T0 + 26 * H


def test_trade_through_weekend_is_not_cancelled():
    """B12: po ostatniej piątkowej świecy następna jest niedzielna/poniedziałkowa — weekend nie jest barierą."""
    fri = 1761868800  # piątek 2025-10-31 00:00 UTC
    ts = [fri + H * k for k in range(21)] + [1762120800 + H * k for k in range(30)]  # pt 00–20, nd 22 → pn
    c = 1.1 + np.arange(len(ts)) * 1e-5
    df, info = clean_h1(pd.DataFrame({"ts": ts, "open": c, "high": c + 2e-4, "low": c - 2e-4, "close": c}))
    assert info["gaps"] == [] and info["filled"] == 0
    sig = np.zeros(len(ts), np.int8)
    sig[18] = 1  # piątek 18:00 UTC → wejście 19:00, wyjście po 6 świecach = niedziela/poniedziałek
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=6, cap=6)], hours=False)
    t = res["outcomes"].iloc[0]
    assert res["skipped"]["luka_danych"] == 0 and t["reason"] == "czas" and t["exit_ts"] > 1762120800


def test_data_cancel_rules():
    df, _ = clean_h1(walk(30).drop(index=[10] + list(range(20, 25))))
    P = prepare(df)
    i_f = int(np.flatnonzero(P["filled"])[0])           # świeca uzupełniona
    i_g = int(np.flatnonzero(df.gap_before.to_numpy())[0])  # pierwsza świeca po przerwie w danych
    c = data_cancel(P, np.array([i_f, i_f - 2, i_f - 3, i_g - 3, i_g - 1, 2]),
                    np.array([i_f + 1, i_f - 1, i_f - 2, i_g - 2, i_g, 3]),
                    np.array([i_f + 2, i_f, i_f + 1, i_g, i_g + 1, 5.0]))
    # sygnał na uzupełnionej · wyjście na uzupełnionej · przez uzupełnioną (dozwolone) · przez przerwę · przerwa przed wejściem · czysta
    assert c.tolist() == [True, True, False, True, True, False]


# ---------- dane do liczenia i sprzątanie po Dukascopy ----------

def test_ready_build_reuses_and_skips_short_pairs(tmp_path):
    from ia5 import ready

    yahoo = {"EURUSD": walk(600).drop(index=[100]), "USDJPY": walk(50, seed=2)}
    (tmp_path / "ready").mkdir()
    (tmp_path / "ready" / "OLDPAIR.parquet").write_bytes(b"x")      # plik spoza listy par znika
    r1 = ready.build(yahoo, tmp_path / "ready", pairs=("EURUSD", "USDJPY"), log=lambda m: None)
    assert r1["EURUSD"]["rebuilt"] and r1["EURUSD"]["filled"] == 1 and r1["EURUSD"]["source"] == "yahoo"
    assert r1["USDJPY"]["bars"] == 0 and not (tmp_path / "ready" / "USDJPY.parquet").exists()
    assert not (tmp_path / "ready" / "OLDPAIR.parquet").exists()
    r2 = ready.build(yahoo, tmp_path / "ready", pairs=("EURUSD", "USDJPY"), log=lambda m: None)
    assert not r2["EURUSD"]["rebuilt"]                                       # te same świece — bez przebudowy
    yahoo["EURUSD"] = pd.concat([yahoo["EURUSD"], walk(1, t0=T0 + 600 * H)])
    assert ready.build(yahoo, tmp_path / "ready", pairs=("EURUSD",), log=lambda m: None)["EURUSD"]["rebuilt"]


def test_migrate_legacy_removes_dukascopy_data_once(tmp_path, monkeypatch):
    from ia5 import cli, store

    data = tmp_path / "data"
    legacy = (data / "m1", data / "h1", data / "h1_scan")
    for d in legacy + (data / "h1_ready", tmp_path / "results", tmp_path / "scans", data / "yahoo"):
        d.mkdir(parents=True)
        (d / "x.parquet").write_bytes(b"123")
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(store, "LEGACY", legacy)
    monkeypatch.setattr(store, "READY", data / "h1_ready")
    monkeypatch.setattr(store, "RESULTS", tmp_path / "results")
    monkeypatch.setattr(store, "SCANS", tmp_path / "scans")
    assert cli.migrate_legacy(log=lambda m: None) is True
    assert not any(d.exists() for d in legacy + (data / "h1_ready", tmp_path / "results", tmp_path / "scans"))
    assert (data / "yahoo" / "x.parquet").exists()                           # kopia Yahoo zostaje
    assert cli.migrate_legacy(log=lambda m: None) is True                     # bez znacznika — przejście niedokończone
    cli.mark_source()
    assert json.loads((tmp_path / "source.json").read_text())["source"] == "yahoo"
    (tmp_path / "results").mkdir()
    assert cli.migrate_legacy(log=lambda m: None) is False                    # po przejściu: wyniki Yahoo zostają
    assert (tmp_path / "results").exists()


def test_next_sync_is_five_minutes_after_the_hour():
    from ia5 import cli

    assert cli.next_sync_time(T0 + 120) == T0 + 300
    assert cli.next_sync_time(T0 + 300) == T0 + H + 300
    assert cli.next_sync_time(T0 + 3000) == T0 + H + 300


def test_months_since_covers_offline_period():
    from datetime import datetime, timezone

    from ia5 import cloud

    now = datetime(2026, 10, 31, tzinfo=timezone.utc)
    assert cloud.months_since(int(datetime(2026, 7, 15, tzinfo=timezone.utc).timestamp()), now) == \
        ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
    assert cloud.months_since(int(datetime(2026, 10, 30, tzinfo=timezone.utc).timestamp()), now) == ["2026-09", "2026-10"]


def test_week_open_grace():
    """Niedziela 22–23 UTC bez świec (Yahoo otwiera tydzień później) to nie awaria; 4 h albo środek tygodnia — tak."""
    from ia5.session import week_open_grace

    fri20 = 1761940800          # piątek 2025-10-31 20:00 UTC — ostatnia świeca tygodnia
    sun22 = 1762120800          # niedziela 22:00 UTC
    assert week_open_grace(fri20, sun22 + 2 * H + 120)         # brak 22:00 i 23:00
    assert not week_open_grace(fri20, sun22 + 4 * H + 120)     # brak 4 godzin
    assert not week_open_grace(T0 + 10 * H, T0 + 13 * H + 120)  # poniedziałek w środku dnia


def test_requeue_after_source_change(monkeypatch):
    """D-039: wyniki Dukascopy znikają z gałęzi data, strategie właściciela wracają do kolejki; bez właściciela — nic."""
    from ia5 import cli, cloud, publish

    updates = []
    monkeypatch.setattr(publish, "purge_dukascopy_results", lambda log: 2)
    monkeypatch.setattr(cloud, "computed_strategies", lambda: [("a", {"createdBy": "me", "name": "A"}), ("b", {"createdBy": "x"})])
    monkeypatch.setattr(cloud, "update_strategy", lambda sid, f: updates.append((sid, f["status"])))
    assert cli.requeue_after_source_change(None) is False and updates == []
    assert cli.requeue_after_source_change("me") is True and updates == [("a", "do_policzenia")]
    monkeypatch.setattr(publish, "purge_dukascopy_results", lambda log: (_ for _ in ()).throw(RuntimeError("git push")))
    assert cli.requeue_after_source_change("me") is False


def test_only_yahoo_data_stays_local_and_engine_refuses_other_sources(tmp_path, monkeypatch):
    """D-041: w ~/.ia5/data zostaje tylko kopia świec Yahoo (8 par) i dane do liczenia z niej; silnik nie liczy
    na danych z innego źródła."""
    from ia5 import cli, health, ready, store
    from ia5.backtest import ready_source, run_file

    data = tmp_path / "data"
    for d in ("yahoo", "h1_ready", "m1", "stare"):
        (data / d).mkdir(parents=True)
    (data / "notatka.txt").write_text("x")
    (data / "yahoo" / "EURUSD.parquet").write_bytes(b"1")
    (data / "yahoo" / "XAUUSD.parquet").write_bytes(b"1")
    monkeypatch.setattr(cli, "DATA", data)
    monkeypatch.setattr(store, "YAHOO", data / "yahoo")
    removed = cli.enforce_local_data(log=lambda m: None)
    assert sorted(f.name for f in data.iterdir()) == ["h1_ready", "yahoo"]
    assert [f.name for f in (data / "yahoo").iterdir()] == ["EURUSD.parquet"] and len(removed) == 4

    yahoo = {"EURUSD": walk(600)}
    info = ready.build(yahoo, data / "h1_ready", pairs=("EURUSD",), log=lambda m: None)
    assert ready_source(data / "h1_ready") == "yahoo" and info["EURUSD"]["source"] == "yahoo"
    assert health.local_data(tmp_path, yahoo)["state"] == "ok"
    (data / "h1_ready" / "EURUSD.json").write_text('{"source": "inne"}')
    assert health.local_data(tmp_path, yahoo)["state"] == "bad"
    with pytest.raises(SystemExit, match="nie pochodzą"):
        run_file("def signals(df, p, ind):\n    return df.close * 0\n", "x", data / "h1_ready", tmp_path / "r",
                 log=lambda m: None, require_source="yahoo")
