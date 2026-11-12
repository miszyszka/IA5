"""Poprawione zamknięcia D1 (badanie, nie warstwa silnika): od ~2011 Yahoo podaje dla par FX close ≈ open tego samego dnia
(mediana |close − open| ≈ 2% zakresu dnia; do 2009 ≈ 50%). Prawdziwe zamknięcie dnia t to open dnia t+1 (zgodne z ostatnim close H1
przed północą w Londynie: mediana 3,4 pipsa na EUR/USD 2025–2026). Ostatni dzień odrzucony (jego zamknięcie nieznane z D1).
Użycie: python fix_close.py <d1_ready> <d1_fixed>"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(exist_ok=True)
for f in sorted(src.glob("*.parquet")):
    d = pd.read_parquet(f)
    nxt = d.open.shift(-1)
    ok = (d.gap_before.shift(-1).fillna(1) == 0) & nxt.notna()
    d.loc[ok, "close"] = nxt[ok]
    d = d.iloc[:-1].copy()
    d["high"], d["low"] = np.maximum(d.high, d.close), np.minimum(d.low, d.close)
    d.to_parquet(out / f.name, index=False)
    (out / (f.stem + ".json")).write_text(f.with_suffix(".json").read_text())
