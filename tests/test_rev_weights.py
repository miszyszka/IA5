"""REV (D-063): podział proporcjonalny i według rankingu, limit 50% (R4), pasmo 2 p.p. (R3)."""
import numpy as np
import pandas as pd
import pytest
from ia5 import rev_method as rm


def test_proportional():
    w = rm.target_weights(pd.Series([3.0, 1.0, -1.0, -3.0]), "P")
    assert np.allclose(w.to_numpy(), [0.5, 0.5, 0, 0])


def test_rank_n6():
    w = rm.target_weights(pd.Series([6.0, 5, 4, 3, 2, 1]), "R")
    assert np.allclose(w.to_numpy(), [0.5, 0.375, 0.125, 0, 0, 0], atol=1e-9)


def test_nan_basket_gets_nothing_and_all_equal_splits():
    w = rm.target_weights(pd.Series([np.nan, 1.0, 1.0, 1.0]), "P")
    assert w.iloc[0] == 0 and np.allclose(w.iloc[1:].to_numpy(), 1 / 3)


def test_cap_one_positive_goes_to_next_rank():
    assert np.allclose(rm.cap_fill(np.array([1.0, 0, 0, 0]), np.array([0, 1, 2, 3]), 0.5), [0.5, 0.5, 0, 0])


def test_band_keeps_small_changes():
    new = rm.rebalance(np.array([.30, .30, .40]), np.array([.31, .25, .44]), np.array([2, 0, 1]), np.zeros(3, bool))
    assert np.allclose(new, [.30, .70 * .25 / .69, .70 * .44 / .69])


def test_band_forces_over_cap():
    new = rm.rebalance(np.array([.51, .49]), np.array([.5, .5]), np.array([0, 1]), np.zeros(2, bool))
    assert np.allclose(new, [.5, .5])


def test_band_only_sells_pull_buyers():
    new = rm.rebalance(np.array([.49, .49, .02]), np.array([.5, .5, 0]), np.array([0, 1, 2]), np.zeros(3, bool))
    assert np.allclose(new, [.5, .5, 0])


def test_frozen_untouched():
    cur = np.array([.2, .3, .5])
    new = rm.rebalance(cur, np.array([.5, .5, 0]), np.array([0, 1, 2]), np.array([True, False, False]))
    assert new[0] == .2 and np.isclose(new[1:].sum(), .8) and new.max() <= .5 + 1e-9


@pytest.mark.parametrize("seed", range(200))
def test_properties(seed):   # 200 losowych przypadków (bez biblioteki hypothesis — G6)
    rng = np.random.default_rng(seed)
    n, with_frozen = int(rng.integers(2, 13)), bool(seed % 2)
    cur = rng.dirichlet(np.ones(n))
    cur = rm.cap_fill(cur, np.arange(n), 0.5)
    s = pd.Series(rng.normal(0, 1, n))
    s[rng.random(n) < 0.2] = np.nan
    for how in ("P", "R"):
        tgt = rm.target_weights(s, how).to_numpy()
        assert np.isclose(tgt.sum(), 1) and (tgt >= -1e-12).all()
        frozen = np.zeros(n, bool)
        if with_frozen and n >= 3:
            frozen[rng.integers(n)] = True
        new = rm.rebalance(cur, tgt, rm._order(s.to_numpy()), frozen)
        assert np.isclose(new.sum(), 1, atol=1e-9)
        assert (new >= -1e-12).all()
        assert new.max() <= 0.5 + 1e-9
        assert np.allclose(new[frozen], cur[frozen])
