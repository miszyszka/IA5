"""Świece H1 z niezależnego źródła (broker MT, ejtraderLabs/historical-data) → UTC, ceny rzeczywiste."""
import pandas as pd, numpy as np
from pathlib import Path
D = Path(__file__).parent / "data"   # CSV pobrane według README — nie trafiają do repo
PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "AUDUSD", "USDCHF", "USDCAD", "EURJPY"]
PIP = {p: (0.01 if "JPY" in p else 0.0001) for p in PAIRS}
SPREAD = {"EURUSD": .9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7, "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0, "EURJPY": 2.1}

def load(p):
    df = pd.read_csv(D / f"{p}.csv", parse_dates=["Date"])
    scale = 1e3 if "JPY" in p else 1e5
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c] / scale
    # czas serwera = Nowy Jork + 7 h (zamknięcie tygodnia 17:00 NY = 00:00 serwera)
    ny = (df["Date"] - pd.Timedelta(hours=7)).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    df.index = ny.dt.tz_convert("UTC")
    df = df[df.index.notna()][["open", "high", "low", "close"]]
    return df[~df.index.duplicated()]

def all_pairs():
    return {p: load(p) for p in PAIRS}
