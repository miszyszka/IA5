"""REV (D-063): portfele tygodniowe, równy podział, przełącznik, wycena dzienna."""
import numpy as np
import pandas as pd
from ia5 import rev_method as rm
from ia5.rev_data import daily_panel, decision_times, weekly_panel


def frame(rows: list[list[float]], cols=("A", "PLN")) -> pd.DataFrame:
    idx = 1_700_000_000 + 7 * 86400 * np.arange(len(rows))
    return pd.DataFrame(rows, index=idx, columns=list(cols), dtype=float)


def test_constant_prices_constant_value():
    p = frame([[2.0, 1.0]] * 10)
    t = frame([[0.5, 0.5]] * 10)
    s = rm.simulate(p, t)
    assert np.allclose(s.value.to_numpy(), 10_000)
    assert np.allclose(s.weights.to_numpy(), 0.5)


def test_value_tracks_prices():
    p = frame([[1.0, 1.0], [2.0, 1.0], [2.0, 1.0]])
    t = frame([[0.5, 0.5]] * 3)
    s = rm.simulate(p, t)
    assert np.isclose(s.value.iloc[1], 15_000)
    assert np.isclose(s.ret.iloc[0], np.log(1.5))


def test_equal_weight_rebalanced_without_band():
    p = frame([[1.0, 1.0], [1.03, 1.0], [1.0, 1.0]])
    eq = rm.equal_targets(frame([[1, 1]] * 3).astype(bool))
    s = rm.simulate(p, eq, band=0.0)
    assert np.allclose(s.weights.to_numpy(), 0.5)            # mała zmiana też przewalutowana


def test_exec_prices_used_for_trades():
    exe = frame([[2.0, 1.0], [2.0, 1.0]])
    t = frame([[0.5, 0.5]] * 2)
    s = rm.simulate(exe, t)
    assert np.isclose(s.units.iloc[0]["A"], 2500)            # 5000 zł po kursie wykonania 2,0


def test_no_price_basket_frozen():
    p = frame([[1.0, 1.0, 1.0], [np.nan, 1.0, 1.0], [1.2, 1.0, 1.0]], cols=("A", "B", "PLN"))
    t = frame([[0.4, 0.3, 0.3], [0.0, 0.5, 0.5], [0.0, 0.5, 0.5]], cols=("A", "B", "PLN"))
    s = rm.simulate(p, t)
    assert np.isclose(s.units.iloc[1]["A"], s.units.iloc[0]["A"])   # bez ceny — bez handlu
    assert np.isclose(s.value.iloc[1], 10_000)                      # wycena po ostatniej znanej cenie
    assert np.isclose(s.units.iloc[2]["A"], 0.0)                    # cena wróciła — sprzedane


def test_switcher_schedule():
    n = 400
    idx = 1_700_000_000 + 7 * 86400 * np.arange(n)
    rng = np.random.default_rng(5)
    ids = [v.id for v in rm.STATIC]
    ex = pd.DataFrame(rng.normal(0, 0.01, (n, len(ids))), index=idx, columns=ids)
    ex.loc[idx[:160], "M3-P"] += 0.02
    ex.loc[idx[160:], "V5-R"] += 0.02
    eq = pd.DataFrame(0.5, index=idx, columns=["A", "PLN"])
    static = {i: eq.copy() for i in ids}
    _, chosen, _ = rm.switcher_targets(ex, static, eq, start=0)
    assert (chosen.iloc[:156] == "equal").all()
    changes = np.flatnonzero(chosen.to_numpy()[1:] != chosen.to_numpy()[:-1]) + 1
    assert all(c % 13 == 0 for c in changes)
    assert chosen.iloc[156] == "M3-P" and chosen.iloc[-1] == "V5-R"


def test_max_weight_cap_every_week():
    from rev_fixtures import synthetic_ready

    codes = ["EUR", "USD", "CHF", "GBP", "JPY", "NOK", "SEK", "CZK", "HUF"]
    ready = synthetic_ready(codes, start="2008-01-01", end="2026-11-10", seed=8)
    times = decision_times(ready["EUR"]["close_ts"].iloc[0], ready["EUR"]["close_ts"].iloc[-1] + 86400)
    prices, _ = weekly_panel(ready, codes + ["PLN"], times)
    elig = rm.eligible(prices)
    start = int(np.argmax(elig.drop(columns="PLN").sum(axis=1).to_numpy() >= 8))
    for v in (rm.VARIANT_BY_ID["V5-P"], rm.VARIANT_BY_ID["M3-R"]):
        tg, order = rm.variant_targets(prices, elig, v)
        s = rm.simulate(prices, tg, order, start=start)
        assert s.weights.max(axis=1).max() <= 0.5 + 1e-9
        assert np.allclose(s.weights.sum(axis=1), 1)
        assert s.trades > 0


def test_daily_equity_matches_weekly():
    from rev_fixtures import synthetic_ready

    codes = ["EUR", "USD", "CHF"]
    ready = synthetic_ready(codes, start="2024-01-01", end="2026-11-10", seed=9)
    times = decision_times(ready["EUR"]["close_ts"].iloc[0], ready["EUR"]["close_ts"].iloc[-1] + 86400)
    prices, _ = weekly_panel(ready, codes + ["PLN"], times)
    t = pd.DataFrame(0.25, index=prices.index, columns=prices.columns)
    s = rm.simulate(prices, t, start=1, band=0.0)
    daily = daily_panel(ready, codes + ["PLN"])
    eq = rm.daily_equity(s.units, daily)
    for i in range(2, 40):
        t_dec = s.value.index[i]
        monday = eq[eq.index < t_dec].iloc[-1]                 # zamknięcie poniedziałku przed wtorkiem 08:00
        assert np.isclose(monday, s.value.iloc[i]), i
