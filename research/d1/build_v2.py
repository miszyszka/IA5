"""Dane D1 do liczenia po naprawie zamknięć (clean_d1 wersja 2, D-068) — z surowych świec D1 i H1 Yahoo (gałąź data)."""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import sys
from pathlib import Path

import pandas as pd

from ia5.ready import build_d1

raw = {p.stem: pd.read_parquet(p) for p in sorted((paths.DATA / "d1raw").glob("*.parquet"))}
h1 = {}
for p in sorted((paths.DATA / "h1raw").glob("*.parquet")):
    h1.setdefault(p.stem.split("_")[0], []).append(pd.read_parquet(p))
h1 = {k: pd.concat(v, ignore_index=True) for k, v in h1.items()}
out = Path(sys.argv[1])
b = build_d1(raw, out, h1=h1 if "--bez-h1" not in sys.argv else None)
