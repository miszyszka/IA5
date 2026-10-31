"""Walidacja i kapitał: zachowanie na przypadkach o znanej odpowiedzi."""
import numpy as np
import pandas as pd
from ia5.portfolio import simulate_equity
from ia5.validate import bootstrap_ci, deflated_sharpe, pbo_cscv, spread_stress, verdict, walk_forward


def trades(n, pips, start=1_600_000_000, step=7200, hold=3600, pair="EURUSD"):
    ts = start + step * np.arange(n)
    return pd.DataFrame({"pair": pair, "entry_ts": ts, "exit_ts": ts + hold, "pips_net": pips,
                         "pips_gross": np.asarray(pips, float) + 0.9, "entry_px": 1.0})


def test_equity_compounds_and_respects_margin():
    t = trades(2, [100.0, 100.0])                      # +1% na nominale każda
    c = simulate_equity(t, 10)                          # depozyt 10% → nominał 300% kapitału (30:1, D-024) → +3%
    assert np.isclose(c["final"], 10_000 * 1.03 * 1.03)
    over = trades(5, [10.0] * 5, step=60, hold=36_000)  # 5 pozycji naraz
    c = simulate_equity(over, 30)                       # 30% → zmieszczą się 3
    assert c["taken"] == 3 and c["skipped_margin"] == 2


def test_dsr_low_when_many_trials_and_noise():
    rng = np.random.default_rng(0)
    trials = np.array([rng.normal(0, 1, 200).mean() / 1 for _ in range(400)])
    best = rng.normal(0.02, 1, 200)
    assert deflated_sharpe(best, trials)["dsr"] < 0.5


def test_dsr_high_for_strong_edge_few_trials():
    rng = np.random.default_rng(1)
    best = rng.normal(0.5, 1, 500)
    trials = np.array([0.0, 0.01, -0.01, 0.02])
    assert deflated_sharpe(best, trials)["dsr"] > 0.99


def test_pbo_noise_near_half_and_real_edge_low():
    rng = np.random.default_rng(2)
    rows = []
    for v in range(40):
        rows.append(pd.DataFrame({"variant_id": v, "r_net": rng.normal(0, 1, 160), "entry_ts": np.arange(160) * 3600}))
    noise = pd.concat(rows)
    assert 0.3 < pbo_cscv(noise, noise["entry_ts"])["pbo"] < 0.8
    edge = noise.copy()
    edge.loc[edge.variant_id == 0, "r_net"] += 1.0      # jeden wariant naprawdę lepszy w każdym okresie
    assert pbo_cscv(edge, edge["entry_ts"])["pbo"] < 0.1


def test_walk_forward_picks_from_past_only():
    o = pd.concat([pd.DataFrame({"variant_id": v, "r_net": r, "pips_net": r, "entry_ts": np.arange(500) * 3600})
                   for v, r in ((0, np.r_[np.ones(300), -np.ones(200)]), (1, np.zeros(500)))])
    wf = walk_forward(o, windows=5)
    assert wf["windows"][0]["variant_id"] == 0          # w przeszłości lepszy był 0
    assert wf["mean_r"] < 1                             # i poza próbą się to zemściło


def test_bootstrap_and_spread():
    ci = bootstrap_ci(np.r_[np.ones(50), -np.ones(50)])
    assert ci["low"] < 0 < ci["high"]
    s = spread_stress(trades(3, [1.0, 1.0, 1.0]))
    assert np.isclose(s["x1"], 1.0) and np.isclose(s["x2"], 0.1)


def test_verdict_rules():
    good = {"oos_trades": 50, "oos_mean_pips": 2.0, "benchmark": {"percentile": 99}, "pbo": {"pbo": 0.1},
            "dsr": {"dsr": 0.97}, "spread": {"x1_5": 1.0}}
    assert verdict(good)["color"] == "green"
    assert verdict({**good, "oos_mean_pips": -1})["color"] == "red"
    assert verdict({**good, "pbo": {"pbo": 0.5}})["color"] == "yellow"
    assert verdict({**good, "oos_trades": 3})["color"] == "yellow"


def test_dsr_single_variant_equals_psr():
    """D-043: przy jednej próbie nie ma wyboru, więc DSR = PSR (próg Sharpe 0), a nie „—”."""
    rng = np.random.default_rng(3)
    best = rng.normal(0.2, 1.0, 400)
    d = deflated_sharpe(best, np.array([0.2]))
    assert d["sharpe0"] == 0.0 and 0.99 < d["dsr"] <= 1.0
    assert deflated_sharpe(rng.normal(0, 1, 400), np.array([0.0]))["dsr"] < 0.95


def test_verdict_pbo_not_applicable_for_single_variant():
    """D-043 (decyzja Michała): przy 1 wariancie PBO „nie dotyczy” — nie blokuje 🟢 i nie liczy się do testów."""
    v = {"oos_mean_pips": 5.0, "oos_trades": 50, "benchmark": {"percentile": 99.0}, "pbo": {"pbo": float("nan"), "variants": 1},
         "dsr": {"dsr": 0.99}, "spread": {"x1_5": 3.0}}
    out = verdict(v)
    assert out["color"] == "green"
    na = [c for c in out["checks"] if c.get("na")]
    assert len(na) == 1 and na[0]["test"].startswith("PBO")
    v["pbo"] = {"pbo": float("nan"), "variants": 5}
    assert verdict(v)["color"] == "yellow"
