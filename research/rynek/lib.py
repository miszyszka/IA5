"""Wspólne: wczytanie świec H1 (niezależne dane brokera MT 2012–2022 = odkrycie; Yahoo po warstwie czyszczenia = test)."""
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
PAIRS = ["EURUSD", "USDJPY", "GBPUSD", "EURGBP", "AUDUSD", "USDCHF", "USDCAD", "EURJPY"]
PIP = {p: (0.01 if "JPY" in p else 0.0001) for p in PAIRS}
SPREAD = {"EURUSD": .9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7, "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0, "EURJPY": 2.1}
CUT_AB = pd.Timestamp("2017-07-01", tz="UTC")


def load_ej(p):
    df = pd.read_csv(HERE / "ej" / f"{p}.csv", parse_dates=["Date"])
    scale = 1e3 if "JPY" in p else 1e5
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c] / scale
    ny = (df["Date"] - pd.Timedelta(hours=7)).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    df.index = ny.dt.tz_convert("UTC")
    df = df[df.index.notna()][["open", "high", "low", "close"]]
    df = df[~df.index.duplicated()].sort_index()
    df.index.name = "t"
    return df


def load_yh(p):
    df = pd.read_parquet(HERE / "yh_ready" / f"{p}.parquet")
    df.index = pd.to_datetime(df.ts, unit="s", utc=True)
    df.index.name = "t"
    return df[["open", "high", "low", "close", "filled", "gap_before"]]


def load(src, p):
    return load_ej(p) if src == "ej" else load_yh(p)


def atr(df, n):
    pc = df.close.shift(1)
    tr = np.maximum(df.high - df.low, np.maximum((df.high - pc).abs(), (df.low - pc).abs()))
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def add_time(df):
    df = df.copy()
    lon = df.index.tz_convert("Europe/London")
    ny = df.index.tz_convert("America/New_York")
    tk = df.index.tz_convert("Asia/Tokyo")
    df["h_utc"], df["h_lon"], df["h_ny"], df["h_tk"] = df.index.hour, lon.hour, ny.hour, tk.hour
    df["dow"] = ny.dayofweek                     # dzień handlu wg Nowego Jorku
    # dzień FX: zaczyna się o 17:00 NY
    fxday = (ny + pd.Timedelta(hours=7)).normalize().tz_localize(None)
    df["fxday"] = fxday
    df["londay"] = lon.normalize().tz_localize(None)
    return df


def tstat(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan


def epoch(idx):
    """Sekundy epoki z DatetimeIndex niezależnie od rozdzielczości (pandas 3: us)."""
    return np.asarray(idx.tz_convert("UTC").tz_localize(None).astype("datetime64[s]").astype("int64"))
