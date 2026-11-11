"""REV wersja 2 (D-065): zawór złotówkowy, hamulec zmienności, „nie sprzedawaj na stracie”, PLN do 75%."""
import numpy as np
import pandas as pd
from ia5 import rev_method as rm


def panel(cols: dict[str, np.ndarray]) -> pd.DataFrame:
    n = len(next(iter(cols.values())))
    df = pd.DataFrame(cols, index=1_700_000_000 + 7 * 86400 * np.arange(n))
    df["PLN"] = 1.0
    return df


def test_variants_grid():
    assert len(rm.VARIANTS) == 61 and len(rm.STATIC) == 60
    assert rm.VARIANT_BY_ID["V5-P"].overlay == "" and rm.VARIANT_BY_ID["V5-P+Z26"].base == "V5-P"
    assert {v.overlay for v in rm.STATIC} == {"", "Z26", "Z52", "H", "S"}


def test_valve_on_when_zloty_strengthens():
    up = np.exp(np.linspace(0, 0.2, 60))                     # złoty słabnie (waluty obce drożeją)…
    down = up[-1] * np.exp(np.linspace(0, -0.2, 60))         # …potem się umacnia
    p = panel({"A": np.r_[up, down], "B": np.r_[up, down] * 2})
    on = rm.valve_on(p, 26)
    assert not on[:60].any()
    assert on[90:].all()
    f = rm.foreign_index(p)
    assert f.iloc[59] > 0.19 and f.iloc[-1] < f.iloc[59]


def test_overlays_no_lookahead():
    rng = np.random.default_rng(3)
    n = 500
    p = panel({c: np.exp(np.cumsum(rng.normal(0, 0.015, n))) for c in "ABCD"})
    full = {k: rm.overlay_on(p, k) for k in ("Z26", "Z52", "H")}
    for t in (300, 400, 450):
        q = p.copy()
        q.iloc[t + 1:, :-1] *= np.exp(rng.normal(0, 0.3, (n - t - 1, 4)))
        for k, v in full.items():
            assert (rm.overlay_on(q, k)[: t + 1] == v[: t + 1]).all(), (k, t)


def test_pln_floor_and_caps():
    W = np.array([[0.5, 0.3, 0.2], [0.5, 0.3, 0.2]])
    Wf, caps = rm.pln_floor(W, np.array([True, False]), pln=2)
    assert np.allclose(Wf[0], [0.5 * 0.25 / 0.8, 0.3 * 0.25 / 0.8, 0.75]) and np.allclose(Wf[1], W[1])
    assert caps[0, 2] == 0.75 and caps[0, 0] == 0.5 and caps[1, 2] == 0.5


def test_rebalance_respects_pln_cap_75():
    cap = np.array([0.5, 0.5, 0.75])
    new = rm.rebalance(np.array([0.4, 0.4, 0.2]), np.array([0.15, 0.1, 0.75]), np.array([2, 0, 1]), np.zeros(3, bool), cap=cap)
    assert np.allclose(new, [0.15, 0.1, 0.75])
    back = rm.rebalance(new, np.array([0.5, 0.3, 0.2]), np.array([0, 1, 2]), np.zeros(3, bool))   # zawór wyłączony → PLN ≤ 50%
    assert back[2] <= 0.5 + 1e-9 and np.isclose(back.sum(), 1)


def test_valve_variant_keeps_75_pln_and_caps():
    from ia5.rev_data import decision_times, weekly_panel
    from rev_fixtures import synthetic_ready

    codes = ["EUR", "USD", "CHF", "GBP", "JPY", "NOK", "SEK", "CZK", "HUF"]
    ready = synthetic_ready(codes, start="2008-01-01", end="2026-11-10", seed=8)
    times = decision_times(ready["EUR"]["close_ts"].iloc[0], ready["EUR"]["close_ts"].iloc[-1] + 86400)
    prices, _ = weekly_panel(ready, codes + ["PLN"], times)
    elig = rm.eligible(prices)
    start = int(np.argmax(elig.drop(columns="PLN").sum(axis=1).to_numpy() >= 8))
    plan = rm.variant_plan(prices, elig, rm.VARIANT_BY_ID["V5-P+Z26"])
    s = rm.simulate_plan(prices, plan, start=start)
    w = s.weights
    on = plan.on[start:]
    assert on.any() and (~on).any()
    pw = w["PLN"].to_numpy()[on]
    assert pw.min() >= 0.65 and pw.mean() >= 0.73   # pasmo 2 p.p. zostawia drobne pozycje, więc PLN bywa trochę poniżej 75%
    assert (w["PLN"] <= 0.75 + 1e-9).all() and (w.drop(columns="PLN").max(axis=1) <= 0.5 + 1e-9).all()
    assert (w["PLN"].to_numpy()[~on] <= 0.5 + 1e-9).all()
    assert np.allclose(w.sum(axis=1), 1)


def test_no_loss_keeps_losers_and_tracks_cost():
    idx = 1_700_000_000 + 7 * 86400 * np.arange(3)
    p = pd.DataFrame({"A": [1.0, 0.9, 0.9], "B": [1.0, 1.0, 1.0], "PLN": [1.0, 1.0, 1.0]}, index=idx)
    t = pd.DataFrame({"A": [0.5, 0.0, 0.0], "B": [0.0, 0.5, 0.5], "PLN": [0.5, 0.5, 0.5]}, index=idx)
    hold = rm.simulate(p, t, np.tile([0, 1, 2], (3, 1)), no_loss=True)
    sell = rm.simulate(p, t, np.tile([0, 1, 2], (3, 1)), no_loss=False)
    assert np.isclose(hold.units["A"].iloc[1], 5000) and np.isclose(sell.units["A"].iloc[1], 0)   # A na stracie — zostaje
    cost = rm.update_cost(np.array([1.0, np.nan]), np.array([100.0, 0.0]), np.array([200.0, 50.0]), np.array([1.2, 2.0]))
    assert np.isclose(cost[0], 1.1) and np.isclose(cost[1], 2.0)
    assert np.isnan(rm.update_cost(np.array([1.0]), np.array([10.0]), np.array([0.0]), np.array([1.0]))[0])
