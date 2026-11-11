"""Apps Script (apps_script/Code.gs) w Node z atrapami usług Google — samonaprawa świec H1 (D-060)."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="brak Node")
def test_repair_rewrites_window_clears_flags_and_keeps_real_gaps():
    r = subprocess.run(["node", str(ROOT / "tests" / "apps_script_repair.sim.js"), str(ROOT / "apps_script" / "Code.gs")],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("OK")


@pytest.mark.skipif(shutil.which("node") is None, reason="brak Node")
def test_pln_series_admission_and_tick():
    """D-063: backfillPLN() przyjmuje tylko waluty z długą, świeżą i ruchomą historią; tickPLN_ dopisuje dni."""
    r = subprocess.run(["node", str(ROOT / "tests" / "apps_script_pln.sim.js"), str(ROOT / "apps_script" / "Code.gs")],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("OK")
