"""Niezależne dane brokera (H1 → dni londyńskie) w układzie d1_ready — do sprawdzenia zamrożonej strategii na innym źródle cen."""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
from pathlib import Path

import numpy as np
import pandas as pd

import glib
from ia5.daily import close_ts

out = paths.DATA / "d1_ej"; out.mkdir(exist_ok=True)
for p, d in glib.load("ej").items():
    ts = (d.index.tz_localize("Europe/London").tz_convert("UTC") - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)
    r = pd.DataFrame({"ts": np.asarray(ts, "int64"), "open": d.open.to_numpy(), "high": d.high.to_numpy(), "low": d.low.to_numpy(),
                      "close": d.close.to_numpy(), "filled": False, "gap_before": 0})
    r["close_ts"] = close_ts(r["ts"].to_numpy(), "Europe/London")
    r.to_parquet(out / f"{p}.parquet", index=False)
print("ok", len(r))
