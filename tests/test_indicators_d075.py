"""D-075: nowe wskaźniki — zgodność z TA-Lib (ROC, KAMA, WILLR, CCI), a gdzie TA-Lib ich nie ma — wzór z definicji pętlą."""
import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind


@pytest.fixture(scope="module")
def ohlc():
    rng = np.random.default_rng(21)
    c = 1.1 + np.cumsum(rng.normal(0, 0.001, 1500))
    o = c + rng.normal(0, 0.0003, 1500)
    h = np.maximum(o, c) + rng.random(1500) * 0.001
    lo = np.minimum(o, c) - rng.random(1500) * 0.001
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c})


def same(ours, ref, tol=1e-9):
    ours, ref = np.asarray(ours, float), np.asarray(ref, float)
    assert np.array_equal(np.isnan(ours), np.isnan(ref)), "inna rozgrzewka (NaN)"
    m = ~np.isnan(ref)
    assert np.max(np.abs(ours[m] - ref[m])) < tol


talib = pytest.importorskip("talib")


@pytest.mark.parametrize("n", [1, 10, 50])
def test_roc(ohlc, n):
    same(ind.roc(ohlc.close, n), talib.ROC(ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [10, 30])
def test_kama(ohlc, n):
    same(ind.kama(ohlc.close, n), talib.KAMA(ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [5, 14])
def test_willr(ohlc, n):
    same(ind.willr(ohlc, n), talib.WILLR(ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [14, 20])
def test_cci(ohlc, n):
    same(ind.cci(ohlc, n), talib.CCI(ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy(), n), tol=1e-7)


def test_efficiency_ratio_formula(ohlc):
    v, n = ohlc.close.to_numpy(), 10
    ref = [np.nan] * n + [abs(v[t] - v[t - n]) / sum(abs(v[k] - v[k - 1]) for k in range(t - n + 1, t + 1))
                          for t in range(n, len(v))]
    same(ind.efficiency_ratio(ohlc.close, n), ref, 1e-12)
    trend = pd.Series(np.arange(50.0))
    assert ind.efficiency_ratio(trend, 10).iloc[-1] == pytest.approx(1.0)
    flat = pd.Series(np.ones(30))
    assert ind.efficiency_ratio(flat, 10).iloc[-1] == 0.0


def test_ibs_formula(ohlc):
    ref = [(c - lo) / (h - lo) for h, lo, c in zip(ohlc.high, ohlc.low, ohlc.close)]
    same(ind.ibs(ohlc), ref, 1e-12)
    flat = pd.DataFrame({"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]})
    assert ind.ibs(flat).iloc[0] == 0.5


def test_keltner_is_ema_plus_atr(ohlc):
    k = ind.keltner(ohlc, 20, 1.5, 10)
    mid = talib.EMA(ohlc.close.to_numpy(), 20)
    a = talib.ATR(ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy(), 10)
    same(k["mid"], mid)
    same(k["upper"], mid + 1.5 * a)
    same(k["lower"], mid - 1.5 * a)


def test_zscore_formula(ohlc):
    v, n = ohlc.close.to_numpy(), 20
    ref = [np.nan] * (n - 1) + [(v[t] - v[t - n + 1:t + 1].mean()) / v[t - n + 1:t + 1].std() for t in range(n - 1, len(v))]
    same(ind.zscore(ohlc.close, n), ref, 1e-9)


def test_pct_rank_formula(ohlc):
    v, n = ohlc.close.to_numpy(), 50
    ref = [np.nan] * (n - 1) + [sum(1 for x in v[t - n + 1:t + 1] if x <= v[t]) / n * 100 for t in range(n - 1, len(v))]
    same(ind.pct_rank(ohlc.close, n), ref, 1e-12)


def test_patterns():
    df = pd.DataFrame({"high": [10, 9, 12, 11.5, 11.6], "low": [5, 6, 4, 4.5, 4.4], "open": 7.0, "close": 8.0})
    assert ind.inside_bar(df).tolist() == [False, True, False, True, False]
    nr = ind.narrowest(df, 2)
    assert nr.tolist() == [False, True, False, True, False]


@pytest.mark.parametrize("fn", [
    lambda d: ind.roc(d.close, 10), lambda d: ind.kama(d.close, 10), lambda d: ind.efficiency_ratio(d.close, 10),
    lambda d: ind.ibs(d), lambda d: ind.keltner(d).upper, lambda d: ind.zscore(d.close), lambda d: ind.pct_rank(d.close, 50),
    lambda d: ind.willr(d), lambda d: ind.cci(d), lambda d: ind.narrowest(d), lambda d: ind.inside_bar(d),
])
def test_no_lookahead(ohlc, fn):
    full, cut = fn(ohlc), fn(ohlc.iloc[:700])
    a, b = np.asarray(full.iloc[:700], float), np.asarray(cut, float)
    assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)])
