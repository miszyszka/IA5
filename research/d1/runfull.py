"""Pełne liczenie jak na Macu (sandbox → silnik → walidacja → raport) na D1 po naprawie zamknięć. Użycie: python runfull.py strategia.py"""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import json
import sys
from pathlib import Path

from ia5.backtest import run_file

code = Path(sys.argv[1]).read_text()
out = run_file(code, Path(sys.argv[1]).stem, paths.DATA / "h1_ready", paths.DATA / "results", require_source="yahoo",
               d1_dir=paths.DATA / "d1_v2", log=lambda m: None)
v = json.loads((out / "validation.json").read_text())
print(out)
print({k: v.get(k) for k in ("best_variant_id", "best_params", "best_exit", "is_trades", "oos_trades", "is_mean_pips", "oos_mean_pips")})
print("benchmark:", v.get("benchmark")); print("dsr:", v.get("dsr")); print("pbo:", v.get("pbo")); print("werdykt:", v.get("verdict"))
print("spread:", v.get("spread_stress")); print("bootstrap:", v.get("bootstrap")); print("noce:", v.get("nights"))
