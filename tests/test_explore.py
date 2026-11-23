"""D-072: eksploracja Maca, OOS na akcjach (pilotaż) i dziennik otwarć OOS strategii."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5 import config, explore, oos_log, stk_oos
from ia5.engine import Exit
from ia5.sandbox import check_code, run_strategy_code
from ia5.stk_data import clean_stk
from stk_fixtures import raw_stock
from test_strategy_run import GOOD, make_h1

D1 = '''
TIMEFRAME = "D1"
HYPOTHESIS = "Krótkie wyprzedanie w trendzie wraca."
PARAMS = {"lvl": [10, 20]}

def signals(df, p, ind):
    r = ind.rsi(df.close, 2)
    up = df.close > ind.sma(df.close, 100)
    return ((r < p["lvl"]) & up).astype("int8")
'''


@pytest.fixture()
def small(monkeypatch):
    """Mniejsza eksploracja — te same ścieżki kodu, krócej."""
    monkeypatch.setattr(explore, "TOP_PIDS", 1)
    monkeypatch.setattr(explore, "MAX_GRID", 2)
    monkeypatch.setattr(explore, "TOP_K", 2)
    monkeypatch.setattr(explore, "TRANSFORMS", {k: explore.TRANSFORMS[k] for k in ("odwrocony", "tylko_long", "trend200")})


def h1_folder(tmp_path, name="h1", oos_factor=None, n=6000):
    d = tmp_path / name
    d.mkdir()
    for seed, pair, start in ((1, "EURUSD", 1.1), (2, "GBPUSD", 1.3)):
        df = make_h1(n=n, seed=seed, start=start)
        if oos_factor is not None:          # zmiana cen daleko w OOS (poza zasięgiem transakcji otwartych w IS)
            t0, t1 = df.ts.iloc[0], df.ts.iloc[-1]
            cut = t0 + 0.75 * (t1 - t0) + 400 * 3600
            m = df.ts > cut
            rng = np.random.default_rng(seed + 50)
            noise = np.cumsum(rng.normal(0, 0.002, m.sum()))
            for c in ("open", "high", "low", "close"):
                df.loc[m, c] = df.loc[m, c] * oos_factor + noise
        df.to_parquet(d / f"{pair}.parquet", index=False)
    return d


def make_d1(seed, n=4200, start=1.1):
    rng = np.random.default_rng(seed)
    c = start * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    o = np.r_[c[0], c[:-1]] * np.exp(rng.normal(0, 0.001, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.003, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.003, n)))
    ts = pd.bdate_range("2008-01-07", periods=n).tz_localize("Europe/London").tz_convert("UTC").as_unit("s").asi8
    return pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c, "close_ts": np.r_[ts[1:], ts[-1] + 86400],
                         "gap_before": 0})


@pytest.fixture()
def stk_dir(tmp_path):
    d = tmp_path / "stk"
    d.mkdir()
    for i in range(4):
        df, _ = clean_stk(raw_stock(i, start="2008-01-02"))
        df.to_parquet(d / f"T{i}.parquet", index=False)
    return d


# ---------- szersza siatka ----------

def test_wider_values_keeps_categories_and_expands_scales():
    assert explore.wider_values("cfg", [0, 1, 2]) == [0, 1, 2]
    assert explore.wider_values("n", [0, 1, 2, 3]) == [0, 1, 2, 3]           # numer wersji, nie skala
    assert explore.wider_values("rsi_level", [25, 30, 35]) == [20, 25, 28, 30, 32, 35, 40]
    assert explore.wider_values("k", [0.5]) == [0.375, 0.5, 0.625]
    assert all(v > 0 for v in explore.wider_values("n", [2, 10]))
    assert explore.wider_values("mode", ["a", "b"]) == ["a", "b"]


def test_wider_grid_only_new_and_capped(monkeypatch):
    monkeypatch.setattr(explore, "MAX_GRID", 5)
    params = [{"a": 10, "b": 1.0}, {"a": 20, "b": 1.0}]
    new = explore.wider_grid(params)
    assert 0 < len(new) <= 5 and not any(p in params for p in new)
    assert explore.wider_grid(new[:0]) == []


# ---------- kod kandydata ----------

def test_candidate_code_is_a_valid_strategy_with_same_signals(tmp_path):
    d = h1_folder(tmp_path)
    code = explore.candidate_code(GOOD, "test", ["trend200", "potwierdzenie"], {"rsi_level": 40}, None, 123)
    assert check_code(code) == []
    sig, meta = run_strategy_code(code, d)
    assert meta["params"] == [{"rsi_level": 40}] and not meta["lookahead"]
    assert "eksploracji Maca" in meta["hypothesis"]
    base, _ = run_strategy_code(GOOD, d)
    data = explore._load(d)
    frames = explore._frames(data, "H1")
    want = {pair: explore.apply_transforms(frames[pair], explore._sig_arrays(base, data, 1)[pair], ["trend200", "potwierdzenie"],
                                           {"rsi_level": 40}) for pair in data}
    got = explore._sig_arrays(sig, data, 0)
    assert all(np.allclose(got[p], want[p]) for p in data)


def test_candidate_code_with_trail_exits(tmp_path):
    code = explore.candidate_code(GOOD, "t", [], {"rsi_level": 30}, explore.trail_exits("H1"), 1)
    ns: dict = {}
    exec(code, ns)
    assert [Exit(**e) for e in ns["EXITS"]] == explore.trail_exits("H1")


def test_disabled_flag():
    assert explore.disabled(GOOD + "\nEXPLORE = False\n")
    assert not explore.disabled(GOOD)


# ---------- przebieg ----------

def test_explorer_runs_and_opens_oos_only_for_is_choice(tmp_path, small):
    a = explore.Explorer(GOOD, h1_folder(tmp_path, "a"), None, log=lambda *_: None, max_seconds=600).run()
    b = explore.Explorer(GOOD, h1_folder(tmp_path, "b", oos_factor=1.03), None, log=lambda *_: None, max_seconds=600).run()
    assert a["trials"] > 0 and a["units"] >= 3 and "oryginal" in a["mutations"]
    pick = [(c["label"], c["params"], c["exit"]) for c in a["candidates"]]
    assert pick == [(c["label"], c["params"], c["exit"]) for c in b["candidates"]]   # zmiana OOS nie zmienia wyboru (W1)
    for c in a["candidates"]:
        assert c["check"]["ok"] and c["code"] and c["dsr"]["trials"] >= 1
        assert c["verdict"]["color"] in ("green", "yellow", "red", "mute")
    assert "Eksploracja Maca" in explore.markdown(a)


def test_explorer_stops_when_asked(tmp_path, small):
    calls = {"n": 0}

    def stop():
        calls["n"] += 1
        return calls["n"] > 1

    out = explore.Explorer(GOOD, h1_folder(tmp_path), None, log=lambda *_: None, stop=stop).run()
    assert out["interrupted"] == "nowa strategia w kolejce"
    assert out["units"] == 1


def test_duplicate_mutation_is_not_a_new_trial(tmp_path, small):
    ex = explore.Explorer(GOOD, h1_folder(tmp_path), None, log=lambda *_: None, max_seconds=600)
    out = ex.run()
    assert "tylko_long" not in out["mutations"]     # GOOD gra tylko long — „tylko long” to ten sam sygnał


def test_save_appends_to_report_and_carry_over(tmp_path):
    old, new = tmp_path / "s" / "20260101-000000", tmp_path / "s" / "20260102-000000"
    for d in (old, new):
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps({"code_hash": "abc"}))
        (d / "report.md").write_text("# raport\n")
    res = {"summary": "x", "trials": 10, "mutations": ["oryginal"], "candidates": [], "reference": None}
    explore.save(res, old)
    explore.save(res, old)       # drugi zapis nie dubluje sekcji
    assert (old / "report.md").read_text().count("## Eksploracja Maca") == 1
    assert explore.carry_over(new) and (new / "explore.json").exists()
    assert "## Eksploracja Maca" in (new / "report.md").read_text()


# ---------- OOS na akcjach ----------

def test_stocks_oos_for_d1_strategy(stk_dir):
    before = dict(config.PAIRS)
    out = stk_oos.evaluate(D1, 0, Exit("time", n=5, cap=5), stk_dir, sims=100, log=lambda *_: None)
    assert out["trades"] > 30 and out["tickers"] == 4
    assert out["benchmark"]["sims"] > 0 and 0 <= out["benchmark"]["percentile"] <= 100
    assert out["verdict"]["color"] in ("green", "yellow", "red")
    assert out["long"]["trades"] == out["trades"] and out["short"]["trades"] == 0
    assert config.PAIRS == before and not config._EXTRA   # spółki zarejestrowane tylko na czas liczenia
    with pytest.raises(KeyError):
        config.instrument("T0")


def test_stocks_oos_cost_is_charged(stk_dir, monkeypatch):
    a = stk_oos.evaluate(D1, 0, Exit("time", n=5, cap=5), stk_dir, sims=50, log=lambda *_: None)
    monkeypatch.setattr(stk_oos, "COST", 0.0)
    b = stk_oos.evaluate(D1, 0, Exit("time", n=5, cap=5), stk_dir, sims=50, log=lambda *_: None)
    assert b["mean_pct"] - a["mean_pct"] == pytest.approx(0.2, abs=0.05)   # 2 × 0,10% na transakcję


def test_stocks_oos_only_for_d1(stk_dir):
    assert "na" in stk_oos.evaluate(GOOD, 0, Exit("time", n=5, cap=5), stk_dir, log=lambda *_: None)


def test_extra_instruments_cannot_override_fx():
    with pytest.raises(ValueError):
        with config.extra_instruments(["EURUSD"]):
            pass
    assert config.instrument("EURUSD").pip == 0.0001


def test_explorer_d1_with_stocks(tmp_path, stk_dir, small):
    d1 = tmp_path / "d1"
    d1.mkdir()
    for i, p in enumerate(("EURUSD", "GBPUSD")):
        make_d1(i + 10).to_parquet(d1 / f"{p}.parquet", index=False)
    out = explore.Explorer(D1, h1_folder(tmp_path), d1, log=lambda *_: None, max_seconds=600, stk_dir=stk_dir).run()
    assert out["timeframe"] == "D1"
    assert "trades" in out["reference"]["stocks"] or "na" in out["reference"]["stocks"]
    for c in out["candidates"]:
        if c["check"]["ok"]:
            assert "stocks" in c


# ---------- dziennik OOS ----------

def test_oos_log_counts_versions_and_window(tmp_path):
    a = oos_log.add(tmp_path, "s1", "h1", "H1", 1000, 2000)
    assert a == {"strategy_versions": 1, "window_codes": 1, "window_explore": 0}
    assert oos_log.add(tmp_path, "s1", "h1", "H1", 1010, 2010)["strategy_versions"] == 1    # forward test tego samego kodu
    b = oos_log.add(tmp_path, "s1", "h2", "H1", 1010, 2010)
    assert b["strategy_versions"] == 2 and b["window_codes"] == 2
    c = oos_log.add(tmp_path, "s2", "x", "H1", 1100, 2100, kind="explore", opened=5)
    assert c["window_explore"] == 5
    assert oos_log.add(tmp_path, "s3", "y", "D1", 1000, 2000)["window_codes"] == 1          # inny interwał = inny OOS
    assert oos_log.add(tmp_path, "s4", "z", "H1", 5000, 6000)["window_codes"] == 1          # okno bez nakładania
    assert "wersji" in oos_log.line(b)


# ---------- ia5 start: kolejka eksploracji ----------

def _fake_out(tmp_path):
    out = tmp_path / "results" / "s" / "20261123-000000"
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"code_hash": "abc", "oos_cutoff": 1000, "data_to": 2000, "timeframe": "H1",
                                                   "verdict": "red", "id": "s", "name": "RSI"}))
    (out / "validation.json").write_text(json.dumps({"verdict": {"color": "red"}}))
    (out / "report.md").write_text("# raport\n")
    return out


def test_handle_job_queues_exploration_and_explore_yields(monkeypatch, tmp_path):
    import queue

    from ia5 import backtest, cli, cloud, publish

    out = _fake_out(tmp_path)
    monkeypatch.setattr(cloud, "update_strategy", lambda *a: None)
    monkeypatch.setattr(cloud, "heartbeat", lambda *a, **k: None)
    monkeypatch.setattr(backtest, "run_file", lambda *a, **k: out)
    monkeypatch.setattr(publish, "publish_result", lambda *a, **k: "sha1")
    jobs = queue.Queue()
    cli.handle_job("s", {"name": "RSI", "code": GOOD, "status": "do_policzenia"}, {}, jobs)
    sid, job = jobs.get_nowait()
    assert sid == cli.EXPLORE_JOB and job["out"] == str(out)
    cli.handle_job("s", {"name": "RSI", "code": GOOD + "\nEXPLORE = False\n", "status": "do_policzenia"}, {}, jobs)
    assert jobs.empty()
    jobs.put((cli.EXPLORE_JOB, job))
    assert not cli._strategy_waiting(jobs)
    jobs.put(("abc123", {"status": "do_policzenia"}))
    assert cli._strategy_waiting(jobs)


def test_handle_explore_saves_publishes_and_logs_oos(monkeypatch, tmp_path):
    import queue

    from ia5 import cli, cloud, publish

    out = _fake_out(tmp_path)
    writes = []
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(cloud, "update_strategy", lambda sid, f: writes.append(f))
    monkeypatch.setattr(cloud, "heartbeat", lambda *a, **k: None)
    monkeypatch.setattr(publish, "publish_result", lambda *a, **k: "sha2")
    cand = {"rank": 1, "label": "x", "params": {}, "exit": "e", "is": {"trades": 40, "score": 0.1}, "oos": {"trades": 12},
            "verdict": {"color": "green", "text": "ok"}, "check": {"ok": True}}

    class Fake:
        def __init__(self, *a, **k):
            pass

        def run(self):
            return {"summary": "Mac sprawdził", "trials": 9, "mutations": ["oryginal"], "candidates": [cand], "reference": None}

    monkeypatch.setattr(explore, "Explorer", Fake)
    cli.handle_explore({"sid": "s", "name": "RSI", "code": GOOD, "out": str(out), "tries": 0}, {}, queue.Queue())
    assert (out / "explore.json").exists() and "Eksploracja Maca" in (out / "report.md").read_text()
    assert writes[-1]["result"]["sha"] == "sha2" and writes[-1]["explore"]["green"] == 1
    rows = json.loads((tmp_path / oos_log.LEDGER_NAME).read_text())
    assert rows[-1]["kind"] == "explore" and rows[-1]["opened"] == 1
