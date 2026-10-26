"""Zgodność wskaźników z TA-Lib (niezależny wzorzec, CLAUDE.md sekcja 9)."""
import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind

talib = pytest.importorskip("talib")


@pytest.fixture(scope="module")
def ohlc():
    rng = np.random.default_rng(7)
    c = 1.1 + np.cumsum(rng.normal(0, 0.001, 3000))
    o = c + rng.normal(0, 0.0003, 3000)
    h = np.maximum(o, c) + rng.random(3000) * 0.001
    lo = np.minimum(o, c) - rng.random(3000) * 0.001
    return pd.DataFrame({"open": o, "high": h, "low": lo, "close": c})


def same(ours, ref):
    ours, ref = np.asarray(ours, float), np.asarray(ref, float)
    assert np.array_equal(np.isnan(ours), np.isnan(ref)), "inna rozgrzewka (NaN)"
    m = ~np.isnan(ref)
    assert np.max(np.abs(ours[m] - ref[m])) < 1e-9


@pytest.mark.parametrize("n", [5, 20, 200])
def test_sma(ohlc, n):
    same(ind.sma(ohlc.close, n), talib.SMA(ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [9, 50])
def test_ema(ohlc, n):
    same(ind.ema(ohlc.close, n), talib.EMA(ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [2, 14, 21])
def test_rsi(ohlc, n):
    same(ind.rsi(ohlc.close, n), talib.RSI(ohlc.close.to_numpy(), n))


@pytest.mark.parametrize("n", [5, 14])
def test_atr(ohlc, n):
    same(ind.atr(ohlc, n), talib.ATR(ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy(), n))


def test_bollinger(ohlc):
    u, m, lo = talib.BBANDS(ohlc.close.to_numpy(), 20, 2, 2)
    b = ind.bollinger(ohlc.close, 20, 2)
    same(b.upper, u)
    same(b.mid, m)
    same(b.lower, lo)


def test_no_lookahead_in_indicators(ohlc):
    full = ind.rsi(ohlc.close, 14)
    cut = ind.rsi(ohlc.close.iloc[:1500], 14)
    same(full.iloc[:1500], cut)
