"""Kontrakt strategii, detektor look-ahead (B2), uruchomienie w osobnym procesie (S2) i pełny przebieg."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind
from ia5.backtest import run_file
from ia5.sandbox import StrategyError, check_code, lookahead_cuts, param_grid, run_strategy_code

GOOD = '''
HYPOTHESIS = "Wyprzedanie w trendzie wzrostowym wraca."
PARAMS = {"rsi_level": [30, 40]}

def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    rising = sma200 > sma200.shift(5)
    crossed = ind.cross_below(rsi, p["rsi_level"])
    return (rising & crossed).astype("int8")
'''

PEEKING = '''
def signals(df, p, ind):
    return (df.close.shift(-1) > df.close).astype("int8")   # patrzy w przyszłość
'''


def make_h1(n=8000, seed=1, start=1.1):  # dość świec, żeby po oknie B11 zostało ≥ 30 transakcji IS
    rng = np.random.default_rng(seed)
    c = start + np.cumsum(rng.normal(0, 0.0008, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.0006
    lo = np.minimum(o, c) - rng.random(n) * 0.0006
    return pd.DataFrame({"ts": 1600041600 + 3600 * np.arange(n), "open": o, "high": h, "low": lo, "close": c})


@pytest.fixture()
def h1_dir(tmp_path):
    d = tmp_path / "h1"
    d.mkdir()
    make_h1(seed=1).to_parquet(d / "EURUSD.parquet", index=False)
    make_h1(seed=2, start=1.3).to_parquet(d / "GBPUSD.parquet", index=False)
    return d


def test_check_code_rejects_imports_and_builtins():
    errs = check_code("import os\ndef signals(df, p, ind):\n    open('x')\n    return df.close*0")
    assert any("os" in e for e in errs) and any("open" in e for e in errs)
    assert check_code("def f(): pass") == ["Brak funkcji signals(df, p, ind)"]
    assert check_code(GOOD) == []


def test_param_grid():
    assert param_grid({"a": [1, 2], "b": 3}) == [{"a": 1, "b": 3}, {"a": 2, "b": 3}]
    assert param_grid(None) == [{}]


def test_lookahead_detector_catches_future_peeking():
    df = make_h1().set_index("ts")[["open", "high", "low", "close"]]
    ns = {}
    exec(PEEKING, ns)
    assert lookahead_cuts(ns["signals"], df, {}, ind)
    exec(GOOD, ns)
    assert lookahead_cuts(ns["signals"], df, {"rsi_level": 30}, ind) == []


def test_sandbox_runs_in_separate_process(h1_dir):
    sig, meta = run_strategy_code(GOOD, h1_dir)
    assert meta["params"] == [{"rsi_level": 30}, {"rsi_level": 40}]
    assert not meta["lookahead"] and len(sig) > 0
    assert set(sig["sig"]) <= {1}


def test_sandbox_reports_strategy_exception(h1_dir):
    with pytest.raises(StrategyError, match="ZeroDivisionError"):
        run_strategy_code("def signals(df, p, ind):\n    return 1/0", h1_dir)


def test_sandbox_has_no_secrets_in_env(h1_dir, monkeypatch):
    monkeypatch.setenv("IA5_SECRET", "x")
    code = 'import pandas as pd\ndef signals(df, p, ind):\n    raise ValueError(str(sorted(pd.io.common.os.environ)))'
    with pytest.raises(StrategyError) as e:
        run_strategy_code(code, h1_dir)
    assert "IA5_SECRET" not in str(e.value)


def test_full_run_writes_results_and_report(h1_dir, tmp_path):
    out = run_file(GOOD, "test", h1_dir, tmp_path / "results", log=lambda m: None)
    m = json.loads((out / "manifest.json").read_text())
    assert m["n_variants"] == 2 * 233 and m["engine_version"] and m["code_hash"] and m["data_hash"]  # D6, W2
    v = pd.DataFrame(json.loads((out / "variants.json").read_text()))
    assert len(v) == 466 and {"is_exp_r", "oos_exp_r", "rank_is", "row_start", "row_end"} <= set(v.columns)
    t = pd.read_parquet(out / "trades.parquet")
    assert set(t["sample"]) == {"IS", "OOS"} and t["variant_id"].is_monotonic_increasing
    row = v.dropna(subset=["rank_is"]).iloc[0]
    part = t.iloc[int(row.row_start):int(row.row_end)]
    assert (part["variant_id"] == row.variant_id).all() and len(part) == row.all_trades
    val = json.loads((out / "validation.json").read_text())
    assert val["verdict"]["color"] in {"green", "yellow", "red"}
    assert val["benchmark"]["sims"] == 1000 and 0 <= val["pbo"]["pbo"] <= 1
    assert set(val["equity"]) == {"5.0", "10.0", "15.0", "20.0", "30.0"}
    assert (out / "candles" / "EURUSD.parquet").exists()
    rep = (out / "report.md").read_text()
    assert "Przetestowane warianty: 466" in rep and "## Walidacja" in rep and "## Kod strategii" in rep


def test_full_run_refuses_lookahead(h1_dir, tmp_path):
    with pytest.raises(SystemExit, match="look-ahead"):
        run_file(PEEKING, "zla", h1_dir, tmp_path / "results", log=lambda m: None)


def test_exit_reason_explains_killed_process():
    """D-047: „Proces strategii przerwany” bez komunikatu — w błędzie widać, czy to system (pamięć), czy Ctrl+C."""
    from ia5.sandbox import exit_reason

    assert "pamięci" in exit_reason(-9) and "Ctrl+C" in exit_reason(-2) and "kod wyjścia 1" in exit_reason(1)


def test_frozen_strategy_is_judged_on_frozen_variant_with_forward_block_d056(h1_dir, tmp_path):
    """D-056 (W4): zamrożona strategia — walidacja zamrożonego wariantu, blok forward od daty zamrożenia, noce i obsunięcie z MAE."""
    base = run_file(GOOD, "test", h1_dir, tmp_path / "r1", log=lambda m: None)
    v0 = json.loads((base / "validation.json").read_text())
    var = pd.DataFrame(json.loads((base / "variants.json").read_text()))
    other = int(var.dropna(subset=["rank_is"]).sort_values("rank_is").iloc[3]["variant_id"])   # nie szczyt rankingu
    t = pd.read_parquet(base / "trades.parquet")
    assert "nights" in t and (t["nights"] >= 0).all()                                           # D-054
    assert v0["swap"]["nights_mean"] >= 0 and v0["spread"]["x1"] >= v0["swap"]["x0_5"] >= v0["swap"]["x1"]   # noce tylko kosztują
    assert all("max_dd_mae_pct" in e and e["max_dd_mae_pct"] <= e["max_dd_pct"] + 1e-9 for e in v0["equity"].values())  # D-055
    mid = int(t["entry_ts"].quantile(0.8))
    out = run_file(GOOD, "test", h1_dir, tmp_path / "r2", log=lambda m: None, frozen_at=mid, frozen_variant=other)
    v = json.loads((out / "validation.json").read_text())
    assert v["best_variant_id"] == other and v["pinned_variant"] is True
    fw = v["forward"]
    assert fw["since"] == mid and fw["trades"] > 0 and fw["pre_trades"] > 0
    tv = t[t["variant_id"] == other]
    assert fw["trades"] == int((tv["entry_ts"] >= mid).sum())
    assert abs(fw["expected_pips"] - tv[tv["entry_ts"] < mid]["pips_net"].mean()) < 1e-4
    rep = (out / "report.md").read_text()
    assert "Forward test od zamrożenia" in rep and "Noce (swap pominięty" in rep
    m = json.loads((out / "manifest.json").read_text())
    assert m["frozen_at"] == mid and m["frozen_variant"] == other


LEVELS_OK = '''
HYPOTHESIS = "Cel w cenie."
EXITS = [{"kind": "level", "cap": 24}]
def signals(df, p, ind):
    return ind.cross_below(ind.rsi(df.close, 14), 30).astype("int8")
def levels(df, p, ind):
    atr = ind.atr(df, 14)
    return pd.DataFrame({"tp": df.close + 2 * atr, "sl": df.close - atr})
'''

LEVELS_PEEK = LEVELS_OK.replace("df.close + 2 * atr", "df.high.shift(-5)")   # poziom zna przyszłość


def test_levels_go_through_lookahead_detector_and_engine_d057(h1_dir, tmp_path):
    sig, meta = run_strategy_code(LEVELS_OK, h1_dir)
    assert meta["levels"] and not meta["lookahead"] and {"tp", "sl"} <= set(sig.columns) and sig["tp"].notna().all()
    _sig, meta = run_strategy_code(LEVELS_PEEK, h1_dir)
    assert meta["lookahead"], "poziom liczony z przyszłości musi być wykryty"
    out = run_file(LEVELS_OK, "lv", h1_dir, tmp_path / "results", log=lambda m: None)
    v = json.loads((out / "validation.json").read_text())
    assert v["best_exit"].startswith("poziomy TP/SL") and v["benchmark"]["sims"] == 1000
    t = pd.read_parquet(out / "trades.parquet")
    assert set(t["reason"]) <= {"TP", "SL", "czas"} and (t["reason"] != "czas").any()
    # kontrakt: EXITS level bez levels() → błąd; levels() bez wyjścia level → błąd
    with pytest.raises(StrategyError, match="levels"):
        run_strategy_code(LEVELS_OK.replace("def levels", "def poziomy"), h1_dir)
    with pytest.raises(StrategyError, match="level"):
        run_strategy_code(LEVELS_OK.replace('"kind": "level"', '"kind": "time", "n": 24'), h1_dir)
