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


@pytest.mark.parametrize("f,s,g", [(12, 26, 9), (5, 35, 5)])
def test_macd(ohlc, f, s, g):
    m, sig, h = talib.MACD(ohlc.close.to_numpy(), f, s, g)
    ours = ind.macd(ohlc.close, f, s, g)
    same(ours["macd"], m)
    same(ours["signal"], sig)
    same(ours["hist"], h)


@pytest.mark.parametrize("k,sk,d", [(14, 3, 3), (5, 3, 3)])
def test_stoch(ohlc, k, sk, d):
    ks, ds = talib.STOCH(ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy(), k, sk, 0, d, 0)
    ours = ind.stoch(ohlc, k, sk, d)
    same(ours.k, ks)
    same(ours.d, ds)


@pytest.mark.parametrize("n", [14, 7])
def test_adx(ohlc, n):
    h, lo, c = ohlc.high.to_numpy(), ohlc.low.to_numpy(), ohlc.close.to_numpy()
    ours = ind.adx(ohlc, n)
    same(ours.adx, talib.ADX(h, lo, c, n))
    same(ours.plus_di, talib.PLUS_DI(h, lo, c, n))
    same(ours.minus_di, talib.MINUS_DI(h, lo, c, n))


def test_time_helpers():
    idx = pd.to_datetime([1761523200, 1761523200 + 13 * 3600], unit="s", utc=True)  # pon 00:00, 13:00
    df = pd.DataFrame({"close": [1, 2]}, index=idx)
    assert ind.hour(df).tolist() == [0, 13] and ind.weekday(df).tolist() == [0, 0]
    assert ind.session(df).tolist() == ["azja", "usa"]
