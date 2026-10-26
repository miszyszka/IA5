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


def macd(x: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    """MACD jak TA-Lib: obie EMA zasiane w świecy slow-1, wynik od świecy slow+signal-2."""
    v = x.to_numpy(dtype=float)
    n = len(v)
    cols = {"macd": np.full(n, np.nan), "signal": np.full(n, np.nan), "hist": np.full(n, np.nan)}
    start = slow - 1
    if n >= slow + signal - 1:
        kf, ks = 2.0 / (fast + 1), 2.0 / (slow + 1)
        ef, es = v[start - fast + 1 : start + 1].mean(), v[:slow].mean()
        m = np.full(n, np.nan)
        m[start] = ef - es
        for i in range(start + 1, n):
            ef += kf * (v[i] - ef)
            es += ks * (v[i] - es)
            m[i] = ef - es
        first = start + signal - 1
        sig = np.full(n, np.nan)
        sig[first] = m[start : first + 1].mean()
        kg = 2.0 / (signal + 1)
        for i in range(first + 1, n):
            sig[i] = sig[i - 1] + kg * (m[i] - sig[i - 1])
        m[:first] = np.nan
        cols = {"macd": m, "signal": sig, "hist": m - sig}
    return pd.DataFrame(cols, index=x.index)


def stoch(df: pd.DataFrame, k: int = 14, smooth_k: int = 3, d: int = 3) -> pd.DataFrame:
    """Stochastyk wolny (SMA) jak TA-Lib STOCH: %K i %D od świecy k+smooth_k+d-3."""
    hh = df["high"].rolling(k, min_periods=k).max()
    ll = df["low"].rolling(k, min_periods=k).min()
    rng = hh - ll
    fast = (100 * (df["close"] - ll) / rng).where(rng != 0, 0.0)
    fast[hh.isna()] = np.nan
    sk = fast.rolling(smooth_k, min_periods=smooth_k).mean()
    sd = sk.rolling(d, min_periods=d).mean()
    sk[sd.isna()] = np.nan
    return pd.DataFrame({"k": sk, "d": sd}, index=df.index)


def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    """ADX, +DI, −DI (Wilder) jak TA-Lib: DI od świecy n, ADX od świecy 2n-1."""
    h, lo, c = (df[k].to_numpy(dtype=float) for k in ("high", "low", "close"))
    m = len(c)
    pdi, mdi, ax = np.full(m, np.nan), np.full(m, np.nan), np.full(m, np.nan)
    if m > 2 * n - 1:
        up = np.r_[0.0, h[1:] - h[:-1]]
        dn = np.r_[0.0, lo[:-1] - lo[1:]]
        pdm = np.where((up > dn) & (up > 0), up, 0.0)
        mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
        tr = np.r_[np.nan, np.maximum.reduce([h[1:] - lo[1:], np.abs(h[1:] - c[:-1]), np.abs(lo[1:] - c[:-1])])]
        sp, sm, st = pdm[1:n].sum(), mdm[1:n].sum(), tr[1:n].sum()
        dx = np.full(m, np.nan)
        for i in range(n, m):
            sp += pdm[i] - sp / n
            sm += mdm[i] - sm / n
            st += tr[i] - st / n
            if st != 0:
                pdi[i], mdi[i] = 100 * sp / st, 100 * sm / st
                s = pdi[i] + mdi[i]
                dx[i] = 100 * abs(pdi[i] - mdi[i]) / s if s != 0 else 0.0
            else:
                pdi[i] = mdi[i] = dx[i] = 0.0
        ax[2 * n - 1] = dx[n : 2 * n].mean()
        for i in range(2 * n, m):
            ax[i] = (ax[i - 1] * (n - 1) + dx[i]) / n
    return pd.DataFrame({"adx": ax, "plus_di": pdi, "minus_di": mdi}, index=df.index)


def donchian(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Kanał Donchiana z n świec, włącznie z bieżącą (do wybicia porównuj z .shift(1))."""
    return pd.DataFrame({"upper": highest(df["high"], n), "lower": lowest(df["low"], n)}, index=df.index)


def rising(x: pd.Series, n: int = 1) -> pd.Series:
    """x[t] > x[t-n] — np. „SMA200 rośnie" = rising(sma200, 5)."""
    return x > x.shift(n)


def falling(x: pd.Series, n: int = 1) -> pd.Series:
    return x < x.shift(n)


def hour(df: pd.DataFrame) -> pd.Series:
    """Godzina otwarcia świecy w UTC (0–23)."""
    return pd.Series(df.index.hour, index=df.index)


def weekday(df: pd.DataFrame) -> pd.Series:
    """Dzień tygodnia świecy w UTC: 0 = poniedziałek … 6 = niedziela."""
    return pd.Series(df.index.weekday, index=df.index)


def session(df: pd.DataFrame) -> pd.Series:
    """Sesja wg godziny UTC: 'azja' 0–6, 'europa' 7–12, 'usa' 13–20, 'poza' 21–23 (jak w raporcie, 8.6)."""
    h = df.index.hour
    return pd.Series(np.select([h < 7, h < 13, h < 21], ["azja", "europa", "usa"], "poza"), index=df.index)
