"""Złote scenariusze silnika — wyniki policzone ręcznie (CLAUDE.md sekcja 9)."""
import numpy as np
import pandas as pd
import pytest
from ia5.engine import Exit, default_exits, find_entries, m1_resolver, no_overlap, prepare, run, simulate

T0 = 1761523200  # poniedziałek 2025-10-27 00:00 UTC


def bars(rows):
    """rows: (open, high, low, close) — kolejne świece H1."""
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    df.insert(0, "ts", T0 + 3600 * np.arange(len(rows)))
    return df


def entries(P, sig, atr=0.0010):
    ent = find_entries(P, np.array(sig))
    ent["atr5"] = ent["atr14"] = atr
    return ent


FLAT = (1.1000, 1.1002, 1.0998, 1.1000)


def test_default_grid_has_233_variants_and_every_exit_is_bounded():
    ex = default_exits()
    assert len(ex) == 233
    assert all(e.cap <= 120 for e in ex)  # B7


def test_entry_next_open_b1():
    P = prepare(bars([FLAT, (1.1010, 1.1020, 1.1000, 1.1015), FLAT]))
    ent = find_entries(P, np.array([1, 0, 0]))
    assert ent.entry_i.tolist() == [1] and ent.entry_px.tolist() == [1.1010]


def test_signal_on_last_bar_has_no_entry():
    P = prepare(bars([FLAT, FLAT]))
    assert find_entries(P, np.array([0, 1])).empty


def test_time_exit_long():
    # wejście open[1]=1.1010, wyjście po 2 świecach = close[2]=1.1032 → +22 pipsy
    P = prepare(bars([FLAT, (1.1010, 1.1020, 1.1005, 1.1015), (1.1015, 1.1040, 1.1010, 1.1032), FLAT]))
    r = simulate(P, entries(P, [1, 0, 0, 0]), Exit("time", n=2, cap=2), "EURUSD").iloc[0]
    assert r.reason == "czas" and r.exit_px == 1.1032
    assert r.pips_gross == pytest.approx(22.0)
    assert r.bars == 2 and r.exit_ts == T0 + 3 * 3600


def test_atr_take_profit_and_r():
    # wejście 1.1000, ATR 10 pipsów, TP=SL=1×ATR → TP 1.1010 trafiony w świecy 1
    P = prepare(bars([FLAT, (1.1000, 1.1012, 1.0995, 1.1008), FLAT]))
    r = simulate(P, entries(P, [1, 0, 0]), Exit("atr", n=14, tp=1, sl=1, cap=24), "EURUSD").iloc[0]
    assert r.reason == "TP" and r.exit_px == pytest.approx(1.1010)
    assert r.pips_gross == pytest.approx(10) and r.r == pytest.approx(1) and r.risk_pips == pytest.approx(10)
    assert not r.ambiguous


def test_tp_and_sl_same_bar_is_sl_and_ambiguous_b5():
    P = prepare(bars([FLAT, (1.1000, 1.1015, 1.0985, 1.1000), FLAT]))
    ex = Exit("atr", n=14, tp=1, sl=1, cap=24)
    r = simulate(P, entries(P, [1, 0, 0]), ex, "EURUSD").iloc[0]
    assert r.reason == "SL" and r.ambiguous and r.pips_gross == pytest.approx(-10)
    # resolver M1 mówi: najpierw TP
    r2 = simulate(P, entries(P, [1, 0, 0]), ex, "EURUSD", resolver=lambda *a: "tp").iloc[0]
    assert r2.reason == "TP" and not r2.ambiguous and r2.pips_gross == pytest.approx(10)


def test_gap_through_stop_exits_at_open_b6():
    # SL 1.0990; świeca 2 otwiera się na 1.0980 → wyjście po 1.0980 = −20 pipsów
    P = prepare(bars([FLAT, (1.1000, 1.1005, 1.0995, 1.1000), (1.0980, 1.0985, 1.0975, 1.0982), FLAT]))
    r = simulate(P, entries(P, [1, 0, 0, 0]), Exit("atr", n=14, tp=1, sl=1, cap=24), "EURUSD").iloc[0]
    assert r.reason == "SL" and r.exit_px == pytest.approx(1.0980) and r.pips_gross == pytest.approx(-20)


def test_gap_through_target_exits_at_target_b6():
    P = prepare(bars([FLAT, (1.1000, 1.1005, 1.0995, 1.1000), (1.1030, 1.1035, 1.1025, 1.1030), FLAT]))
    r = simulate(P, entries(P, [1, 0, 0, 0]), Exit("atr", n=14, tp=1, sl=1, cap=24), "EURUSD").iloc[0]
    assert r.reason == "TP" and r.exit_px == pytest.approx(1.1010)


def test_short_take_profit_mirror():
    # short od 1.1000, TP 1.0990 trafiony
    P = prepare(bars([FLAT, (1.1000, 1.1004, 1.0988, 1.0992), FLAT]))
    r = simulate(P, entries(P, [-1, 0, 0]), Exit("atr", n=14, tp=1, sl=1, cap=24), "EURUSD").iloc[0]
    assert r.reason == "TP" and r.exit_px == pytest.approx(1.0990) and r.pips_gross == pytest.approx(10)


def test_short_stop_loss():
    P = prepare(bars([FLAT, (1.1000, 1.1012, 1.0996, 1.1008), FLAT]))
    r = simulate(P, entries(P, [-1, 0, 0]), Exit("atr", n=14, tp=1, sl=1, cap=24), "EURUSD").iloc[0]
    assert r.reason == "SL" and r.exit_px == pytest.approx(1.1010) and r.pips_gross == pytest.approx(-10)


def test_opposite_signal_exits_next_open():
    rows = [FLAT, (1.1000, 1.1005, 1.0999, 1.1003), (1.1003, 1.1006, 1.1001, 1.1004),
            (1.1007, 1.1009, 1.1004, 1.1006), FLAT]
    P = prepare(bars(rows))
    sig = np.array([1, 0, -1, 0, 0])
    ent = entries(P, sig)
    r = simulate(P, ent.iloc[:1], Exit("opposite", sl=3, cap=24), "EURUSD", opp=sig).iloc[0]
    # sygnał przeciwny na zamknięciu świecy 2 → wyjście open[3]=1.1007 → +7 pipsów
    assert r.reason == "przeciwny" and r.exit_px == pytest.approx(1.1007) and r.pips_gross == pytest.approx(7)


def test_jpy_pips():
    P = prepare(bars([(150.00, 150.05, 149.95, 150.00), (150.00, 150.30, 149.98, 150.25), (150.25,) * 4]))
    r = simulate(P, entries(P, [1, 0, 0], atr=0.20), Exit("time", n=1, cap=1), "USDJPY").iloc[0]
    assert r.pips_gross == pytest.approx(25)


def test_missing_data_trade_is_dropped():
    P = prepare(bars([FLAT, FLAT, FLAT]))
    r = simulate(P, entries(P, [1, 0, 0]), Exit("time", n=5, cap=5), "EURUSD").iloc[0]
    assert r.reason == "brak danych" and np.isnan(r.exit_i)


def test_one_position_per_pair_b8():
    # wejścia na świecach 1, 2, 5; wyjścia 3, 4, 7 → drugie pominięte
    keep = no_overlap(np.array([1, 2, 5]), np.array([3.0, 4.0, 7.0]))
    assert keep.tolist() == [True, False, True]


def test_run_spread_net_and_oos_split():
    rows = [FLAT] * 20 + [(1.1000, 1.1030, 1.0999, 1.1020)] * 20
    df = bars(rows)
    sig = np.zeros(40)
    sig[[2, 15, 35]] = 1  # świeca 2: rozgrzewka ATR → pominięta
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=1, cap=1)])
    o = res["outcomes"]
    assert (o["pips_net"] == o["pips_gross"] - 0.9).all()  # B3
    assert np.allclose(o["r_net"], o["pips_net"] / o["risk_pips"])
    assert res["entries"]["sample"].tolist() == ["IS", "OOS"]
    assert res["n_variants"] == 1 and res["skipped"]["rozgrzewka"] == 1


def test_m1_resolver_orders_minutes():
    m1 = pd.DataFrame({"ts": T0 + 3600 + 60 * np.arange(3),
                       "bh": [1.1003, 1.1012, 1.1000], "ah": [1.1003, 1.1012, 1.1000],
                       "bl": [1.0995, 1.0995, 1.0985], "al": [1.0995, 1.0995, 1.0985]})
    res = m1_resolver({"EURUSD": m1})
    assert res("EURUSD", T0 + 3600, 1, 1.1010, 1.0990) == "tp"
    # short: SL 1.1010 pada w 2. minucie, zanim TP 1.0990 w 3. minucie
    assert res("EURUSD", T0 + 3600, -1, 1.0990, 1.1010) == "sl"
