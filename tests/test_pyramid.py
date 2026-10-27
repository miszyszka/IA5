"""D-034: dokładanie pozycji (PYRAMID), wagi pozycji, wyjście „seria RSI”, strategia bez okna godzin."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from ia5 import ENGINE_VERSION
from ia5.backtest import run_file
from ia5.engine import Exit, find_entries, no_overlap, prepare, run, simulate
from ia5.portfolio import simulate_equity
from ia5.sandbox import StrategyError, _as_signal, read_settings

T0 = 1735516800  # poniedziałek 2024-12-30 00:00 UTC


def flat(n=60, px=1.1):
    ts = T0 + 3600 * np.arange(n)
    return pd.DataFrame({"ts": ts, "open": px, "high": px + 0.0005, "low": px - 0.0005, "close": px})


def test_rsi_streak_exit_on_open_after_sixth_close():
    P = prepare(flat())
    r = np.full(60, 50.0)
    r[10:30] = 75.0                     # RSI > 70 od świecy 10 (sygnał) przez 20 świec
    P["rsi14"] = r
    sig = np.zeros(60)
    sig[10] = -1
    ent = find_entries(P, sig)
    ent["atr14"] = 0.01                  # TP 1,5 × 0,01 = 150 pipsów — nieosiągalny
    res = simulate(P, ent, Exit("rsi_streak", n=14, tp=1.5, run=6, level=70, cap=120), "EURUSD").iloc[0]
    # seria: świeca 10 = 1 … świeca 15 = 6 → wyjście na open świecy 16
    assert res.reason == "seria RSI" and int(res.exit_i) == 16 and res.exit_ts == P["ts"][16]


def test_rsi_streak_long_mirror_and_tp_first():
    df = flat()
    df.loc[14, "high"] = 1.2             # świeca 14 sięga TP (long)
    P = prepare(df)
    r = np.full(60, 50.0)
    r[10:30] = 25.0                      # long: RSI < 30
    P["rsi14"] = r
    sig = np.zeros(60)
    sig[10] = 1
    ent = find_entries(P, sig)
    ent["atr14"] = 0.001
    res = simulate(P, ent, Exit("rsi_streak", n=14, tp=1.5, run=6, level=70, cap=120), "EURUSD").iloc[0]
    assert res.reason == "TP" and int(res.exit_i) == 14
    assert np.isclose(res.exit_px, 1.1 + 0.0015)


def test_no_overlap_pyramid_cap_and_direction():
    e = np.array([1, 2, 3, 4, 5, 6, 7])
    x = np.array([20, 20, 20, 20, 20, 20, 20], float)
    d = np.array([1, 1, 1, -1, 1, 1, 1])
    assert no_overlap(e, x).tolist() == [True] + [False] * 6           # B8 jak dotąd
    k = no_overlap(e, x, d, cap=5)
    assert k.tolist() == [True, True, True, False, True, True, False]  # short przy otwartych long — nie; szósta — nie
    # po wyjściu (świeca 20) miejsce się zwalnia; wyjście w świecy wejścia jeszcze blokuje (jak B8)
    assert no_overlap(np.array([1, 20, 21]), np.array([20, 30, 40.0]), np.array([1, 1, 1])).tolist() == [True, False, True]


def test_weights_in_entries_and_equity():
    P = prepare(flat())
    sig = np.zeros(60)
    sig[10], sig[20] = -2.5, 1
    ent = find_entries(P, sig)
    assert ent["dir"].tolist() == [-1, 1] and ent["weight"].tolist() == [2.5, 1.0]
    t = pd.DataFrame({"pair": "EURUSD", "entry_ts": [0, 10], "exit_ts": [5, 15], "pips_net": [10.0, 10.0],
                      "entry_px": [1.0, 1.0], "weight": [1.0, 2.0]})
    eq = simulate_equity(t, 10, capital=10_000, leverage=30)
    # +10 pips na nominale 30 × 1000 = 30 USD; druga pozycja z wagą 2 → depozyt 2 × 10% → 2006 × 30 × 0,001 = 60,18 USD
    assert np.isclose(eq["equity"][1], 10_030) and np.isclose(eq["equity"][2] - eq["equity"][1], 60.18, atol=0.01)


def test_signal_weights_validation_and_settings():
    df = pd.DataFrame({"close": [1, 2, 3]})
    assert _as_signal(pd.Series([0, -1.6, 3.0], index=df.index), df).tolist() == pytest.approx([0, -1.6, 3.0])
    with pytest.raises(StrategyError):
        _as_signal([0, 11, 0], df)
    assert read_settings({}) == {"pyramid": 1}
    assert read_settings({"PYRAMID": 5, "HOURS": False}) == {"pyramid": 5, "hours": False}
    for bad in ({"PYRAMID": 0}, {"PYRAMID": 2.5}, {"HOURS": (17, 7)}, {"EXITS": [{"kind": "rsi_streak", "run": 0, "level": 70}]},
                {"EXITS": [{"kind": "x"}]}, {"EXITS": [{"kind": "time", "n": 5, "cap": 500}]}):
        with pytest.raises(StrategyError):
            read_settings(bad)


def test_run_pyramid_takes_up_to_cap():
    P_df = flat(80)
    P_df["close"] = P_df["open"] = 1.1 + 0.0001 * np.arange(80)
    sig = np.zeros(80)
    sig[[20, 21, 22, 23, 24, 25, 26]] = -1
    ex = [Exit("time", n=10, cap=10)]
    one = run({"EURUSD": P_df}, {(0, "EURUSD"): sig}, [{}], exits=ex, hours=False)
    five = run({"EURUSD": P_df}, {(0, "EURUSD"): sig}, [{}], exits=ex, hours=False, pyramid=5)
    assert len(one["outcomes"]) == 1 and len(five["outcomes"]) == 5 and five["skipped"]["B8"] == 2


def rw_h1(folder: Path, n=4000, seed=5):
    folder.mkdir()
    rng = np.random.default_rng(seed)
    c = 1.1 + np.cumsum(rng.normal(0, 0.0012, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.0008
    lo = np.minimum(o, c) - rng.random(n) * 0.0008
    pd.DataFrame({"ts": T0 + 3600 * np.arange(n), "open": o, "high": h, "low": lo, "close": c}).to_parquet(
        folder / "EURUSD.parquet", index=False)
    return folder


@pytest.mark.parametrize("name", ["rsi_trend_pyramid", "rsi_trend_single"])
def test_full_run_example(tmp_path, name):
    code = (Path(__file__).parent.parent / "strategies" / "examples" / f"{name}.py").read_text()
    out = run_file(code, name, rw_h1(tmp_path / "h1"), tmp_path / "res", log=lambda m: None)
    m = json.loads((out / "manifest.json").read_text())
    assert m["engine_version"] == ENGINE_VERSION and m["hours"] == "bez okna" and m["n_variants"] == 1
    assert m["skipped"]["poza_godzinami"] == 0
    t = pd.read_parquet(out / "trades.parquet")
    assert set(t["reason"]) <= {"TP", "seria RSI", "czas"}
    if name == "rsi_trend_pyramid":
        assert m["pyramid"] == 5 and t["weight"].between(1, 3).all()
        # nigdy więcej niż 5 naraz
        ev = sorted([(a, 1) for a in t.entry_ts] + [(b, -1) for b in t.exit_ts], key=lambda z: (z[0], z[1]))
        assert max(np.cumsum([z[1] for z in ev])) <= 5
        assert "Dokładanie (D-034)" in (out / "report.md").read_text()
    else:
        assert m["pyramid"] == 1 and (t["weight"] == 1).all()
