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
    t["weight"] = rng.choice([1.0, 1.0, 1.6, 3.0], n)  # D-034: wagi pozycji — JS i Python muszą liczyć tak samo
    t["mae"] = rng.uniform(0, 40, n).round(1)          # D-055: obsunięcie z MAE — też w obu miejscach
    t["dir"] = rng.choice([1, -1], n)
    t["risk_pips"] = rng.uniform(5, 60, n).round(1)
    expected = {}
    for pct in (5, 10, 15, 20, 30):
        c = simulate_equity(t, pct)
        expected[str(pct)] = {"final": c["final"], "skipped": c["skipped_margin"], "max_dd_mae": c["max_dd_mae"]}
    # D-075: zasady portfela — stawka od ryzyka, cel zmienności, limit na walutę, hamulec; JS = Python
    rules_cases = [
        {"sizing_mode": "risk"}, {"vol_target": 8}, {"max_ccy": 1}, {"brake": [3, 10]},
        {"sizing_mode": "risk", "vol_target": 10, "max_ccy": 2, "brake": [5, 20]},
    ]
    expected_rules = []
    for rc in rules_cases:
        pct = 1.0 if rc.get("sizing_mode") == "risk" else 10
        c = simulate_equity(t, pct, rules=rc)
        assert c["taken"] + c["skipped_margin"] + c["skipped_ccy"] + c["skipped_brake"] == n
        expected_rules.append({"rules": rc, "pct": pct, "final": c["final"], "skipped": c["skipped_margin"],
                               "skipped_ccy": c["skipped_ccy"], "skipped_brake": c["skipped_brake"], "capped": c["capped"],
                               "max_dd_mae": c["max_dd_mae"]})
    assert expected_rules[2]["skipped_ccy"] > 0 and expected_rules[3]["skipped_brake"] > 0
    assert expected_rules[1]["final"] != expected["10"]["final"]
    fx = tmp_path / "fx.json"
    fx.write_text(json.dumps({"trades": json.loads(t.to_json(orient="records")), "expected": expected, "rules": expected_rules}))
    r = subprocess.run(["node", "--test", str(ROOT / "tests" / "web" / "metrics.test.mjs")], capture_output=True, text=True,
                       env={**os.environ, "IA5_EQUITY_FIXTURE": str(fx)})
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="brak Node")
def test_rev_page_logic():
    """D-063: zakładka REV — odliczanie do wtorku 08:00 (z czasem letnim), podział, ranking, CSV dziennika."""
    r = subprocess.run(["node", "--test", str(ROOT / "tests" / "web" / "rev.test.mjs")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
