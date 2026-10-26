"""Wskaźniki (B9). Definicje zgodne z TA-Lib — sprawdzane testem tests/test_indicators.py.

Każda funkcja przyjmuje i zwraca pd.Series na tym samym indeksie; okres rozgrzewki = NaN.
Wartość w punkcie t używa wyłącznie danych do t włącznie (brak look-ahead).
"""
import numpy as np
import pandas as pd


def sma(x: pd.Series, n: int) -> pd.Series:
    return x.rolling(n, min_periods=n).mean()


def ema(x: pd.Series, n: int) -> pd.Series:
    """EMA z ziarnem = SMA pierwszych n wartości (jak TA-Lib)."""
    v = x.to_numpy(dtype=float)
    out = np.full(len(v), np.nan)
    if len(v) >= n:
        a = 2.0 / (n + 1)
        out[n - 1] = v[:n].mean()
        for i in range(n, len(v)):
            out[i] = out[i - 1] + a * (v[i] - out[i - 1])
    return pd.Series(out, index=x.index)


def _wilder(v: np.ndarray, n: int, first: int) -> np.ndarray:
    """Średnia Wildera: ziarno = średnia v[first-n+1 .. first], potem (prev*(n-1) + v) / n."""
    out = np.full(len(v), np.nan)
    if len(v) > first:
        out[first] = v[first - n + 1 : first + 1].mean()
        for i in range(first + 1, len(v)):
            out[i] = (out[i - 1] * (n - 1) + v[i]) / n
    return out


def rsi(x: pd.Series, n: int = 14) -> pd.Series:
    c = x.to_numpy(dtype=float)
    d = np.diff(c, prepend=np.nan)
    up = _wilder(np.where(d > 0, d, 0.0), n, n)
    dn = _wilder(np.where(d < 0, -d, 0.0), n, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(up + dn == 0, 0.0, 100.0 * up / (up + dn))
    out[np.isnan(up)] = np.nan
    return pd.Series(out, index=x.index)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, lo, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    pc = np.roll(c, 1)
    tr = np.maximum.reduce([h - lo, np.abs(h - pc), np.abs(lo - pc)])
    tr[0] = np.nan
    return pd.Series(_wilder(tr, n, n), index=df.index)


def bollinger(x: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    m = sma(x, n)
    s = x.rolling(n, min_periods=n).std(ddof=0)
    return pd.DataFrame({"mid": m, "upper": m + k * s, "lower": m - k * s})


def highest(x: pd.Series, n: int) -> pd.Series:
    return x.rolling(n, min_periods=n).max()


def lowest(x: pd.Series, n: int) -> pd.Series:
    return x.rolling(n, min_periods=n).min()


def cross_above(a: pd.Series, b) -> pd.Series:
    """True w świecy, w której a przechodzi nad b (b może być liczbą)."""
    bp = b.shift(1) if isinstance(b, pd.Series) else b
    return (a > b) & (a.shift(1) <= bp)


def cross_below(a: pd.Series, b) -> pd.Series:
    bp = b.shift(1) if isinstance(b, pd.Series) else b
    return (a < b) & (a.shift(1) >= bp)
