"""ALMA (D-073): TA-Lib jej nie ma, więc wzorcem jest wzór z definicji liczony pętlą, plus własności z opisu wskaźnika."""
import math

import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind


def alma_ref(v, n, offset, sigma):
    """Wzór Legoux / TradingView `ta.alma` krok po kroku, bez numpy-owych skrótów."""
    m, s = offset * (n - 1), n / sigma
    out = []
    for t in range(len(v)):
        if t < n - 1:
            out.append(float("nan"))
            continue
        num = den = 0.0
        for i in range(n):
            w = math.exp(-((i - m) ** 2) / (2 * s * s))
            num += w * v[t - n + 1 + i]
            den += w
        out.append(num / den)
    return np.array(out)


@pytest.fixture(scope="module")
def close():
    rng = np.random.default_rng(11)
    return pd.Series(1.1 + np.cumsum(rng.normal(0, 0.001, 800)))


@pytest.mark.parametrize("n,offset,sigma", [(9, 0.85, 6), (21, 0.85, 6), (9, 0.99, 6), (9, 0.5, 6), (50, 0.85, 3), (1, 0.85, 6)])
def test_alma_matches_formula(close, n, offset, sigma):
    ours, ref = ind.alma(close, n, offset, sigma).to_numpy(), alma_ref(close.to_numpy(), n, offset, sigma)
    assert np.array_equal(np.isnan(ours), np.isnan(ref))
    m = ~np.isnan(ref)
    assert np.max(np.abs(ours[m] - ref[m])) < 1e-12


def test_alma_known_value():
    # stała seria → ta sama stała; seria 1..9 przy offset 0,5 (dzwon symetryczny) → środek okna = 5
    assert np.allclose(ind.alma(pd.Series([2.0] * 20), 9).dropna(), 2.0)
    assert ind.alma(pd.Series(np.arange(1.0, 10.0)), 9, 0.5, 6).iloc[-1] == pytest.approx(5.0)


def test_alma_reacts_faster_than_sma_to_jump():
    # „jeden skok ceny przesuwa ALMA mocniej niż SMA” — skok o 1 na ostatniej świecy
    x = pd.Series([0.0] * 30 + [1.0])
    a, s = ind.alma(x, 9).iloc[-1], ind.sma(x, 9).iloc[-1]
    assert a > 1.5 * s
    # offset 0,99 szybszy niż 0,85, a 0,5 wolniejszy
    assert ind.alma(x, 9, 0.99).iloc[-1] > a > ind.alma(x, 9, 0.5).iloc[-1]


def test_alma_no_lookahead(close):
    full = ind.alma(close, 21)
    for cut in (100, 333, 700):
        part = ind.alma(close.iloc[:cut], 21)
        assert np.allclose(part.to_numpy(), full.iloc[:cut].to_numpy(), equal_nan=True)


def test_alma_bad_args(close):
    with pytest.raises(ValueError):
        ind.alma(close, 0)
    with pytest.raises(ValueError):
        ind.alma(close, 9, 0.85, 0)
