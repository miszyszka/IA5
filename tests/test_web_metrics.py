"""Logika dashboardu (web/js/metrics.js) uruchamiana w Node; kapitał porównany z runner/ia5/portfolio.py."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from ia5.portfolio import simulate_equity

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="brak Node")
def test_dashboard_js(tmp_path):
    rng = np.random.default_rng(5)
    n = 300
    entry = 1_600_000_000 + np.sort(rng.integers(0, 3600 * 24 * 200, n)) // 3600 * 3600
    t = pd.DataFrame({"pair": rng.choice(["EURUSD", "USDJPY", "EURGBP"], n), "entry_ts": entry,
                      "exit_ts": entry + 3600 * rng.integers(1, 60, n), "pips_net": rng.normal(1, 20, n).round(1)})
    t["entry_px"] = t["pair"].map({"EURUSD": 1.1, "USDJPY": 150.0, "EURGBP": 0.85})
    expected = {}
    for pct in (5, 10, 15, 20, 30):
        c = simulate_equity(t, pct)
        expected[str(pct)] = {"final": c["final"], "skipped": c["skipped_margin"]}
    fx = tmp_path / "fx.json"
    fx.write_text(json.dumps({"trades": json.loads(t.to_json(orient="records")), "expected": expected}))
    r = subprocess.run(["node", "--test", str(ROOT / "tests" / "web" / "metrics.test.mjs")], capture_output=True, text=True,
                       env={**os.environ, "IA5_EQUITY_FIXTURE": str(fx)})
    assert r.returncode == 0, r.stdout + r.stderr
