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


def make_h1(n=3000, seed=1, start=1.1):
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
    v = pd.read_parquet(out / "variants.parquet")
    assert len(v) == 466 and {"is_exp_r", "oos_exp_r", "rank_is"} <= set(v.columns)
    o = pd.read_parquet(out / "outcomes.parquet")
    assert set(o["sample"]) == {"IS", "OOS"}
    rep = (out / "report.md").read_text()
    assert "Przetestowane warianty: 466" in rep and "## Kod strategii" in rep


def test_full_run_refuses_lookahead(h1_dir, tmp_path):
    with pytest.raises(SystemExit, match="look-ahead"):
        run_file(PEEKING, "zla", h1_dir, tmp_path / "results", log=lambda m: None)
