"""Złote scenariusze silnika — wyniki policzone ręcznie (CLAUDE.md sekcja 9)."""
import numpy as np
import pandas as pd
import pytest
from ia5.engine import Exit, default_exits, find_entries, no_overlap, prepare, run, simulate

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
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=1, cap=1)], hours=False)  # bez okna B11
    o = res["outcomes"]
    assert (o["pips_net"] == o["pips_gross"] - 0.9).all()  # B3
    assert np.allclose(o["r_net"], o["pips_net"] / o["risk_pips"])
    assert res["entries"]["sample"].tolist() == ["IS", "OOS"]
    assert res["n_variants"] == 1 and res["skipped"]["rozgrzewka"] == 1


def test_trading_window_polish_time_with_dst():
    """B11 (D-028): wejścia tylko 07:00–17:00 czasu polskiego — zimą 06–16 UTC, latem 05–15 UTC."""
    from datetime import UTC, datetime

    from ia5.session import in_trading_hours

    t = lambda *a: int(datetime(*a, tzinfo=UTC).timestamp())  # noqa: E731
    winter = [t(2024, 1, 10, h) for h in (5, 6, 15, 16)]
    summer = [t(2024, 7, 10, h) for h in (4, 5, 14, 15)]
    assert list(in_trading_hours(winter)) == [False, True, True, False]
    assert list(in_trading_hours(summer)) == [False, True, True, False]
    assert in_trading_hours(winter, hours=False).all()


def test_no_forced_close_position_runs_overnight():
    """B11 (D-032): wejście tylko 07–17 czasu polskiego, ale wyjście na dowolnej świecy — bez limitu 23:00."""
    from datetime import UTC, datetime

    t0 = int(datetime(2024, 1, 9, 0, tzinfo=UTC).timestamp())
    n = 80
    c = 1.1 + np.arange(n) * 1e-5
    df = pd.DataFrame({"ts": t0 + 3600 * np.arange(n), "open": c, "high": c + 1e-4, "low": c - 1e-4, "close": c})
    sig = np.zeros(n, np.int8)
    sig[32] = 1  # 10.01 08:00 UTC → wejście 09:00 UTC (10:00 czasu polskiego)
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=24, cap=24)])
    t = res["outcomes"].iloc[0]
    assert t["reason"] == "czas" and t["bars"] == 24 and t["exit_ts"] == df.ts[33 + 24]


def test_nights_count_rollovers_at_21_utc_d054():
    """D-054: noce = przejścia przez 21:00 UTC między wejściem a wyjściem (piątek → poniedziałek = 3 noce)."""
    from ia5.session import nights

    mon_10 = T0 + 10 * 3600                       # poniedziałek 10:00 UTC
    assert nights([mon_10], [mon_10 + 5 * 3600]).tolist() == [0]        # 15:00 tego samego dnia
    assert nights([mon_10], [mon_10 + 12 * 3600]).tolist() == [1]       # 22:00 — po rolowaniu
    assert nights([mon_10], [mon_10 + 3 * 86400]).tolist() == [3]       # czwartek 10:00
    fri_15 = T0 + 4 * 86400 + 15 * 3600
    assert nights([fri_15], [fri_15 + 3 * 86400]).tolist() == [3]       # poniedziałek 15:00 — weekend potrójnie
    # w silniku: wyjście czasowe po 24 świecach o tej samej godzinie następnego dnia = 1 noc
    rows = [FLAT] * 30
    P = prepare(bars(rows))
    r = simulate(P, entries(P, [1] + [0] * 29), Exit("time", n=24, cap=24), "EURUSD").iloc[0]
    assert r.nights == 1


def test_level_exit_uses_prices_from_strategy_d057():
    """D-057: TP/SL to ceny z levels() na świecy sygnału; R względem odległości do SL; brak poziomu = brak TP/SL."""
    rows = [FLAT, (1.1000, 1.1012, 1.0995, 1.1008), (1.1008, 1.1030, 1.1000, 1.1020), FLAT, FLAT]
    P = prepare(bars(rows))
    lv = np.full((len(rows), 2), np.nan)
    lv[0] = [1.1025, 1.0990]                          # TP +25 pipsów, SL −10 pipsów od wejścia 1.1000
    ent = find_entries(P, np.array([1, 0, 0, 0, 0]), lv)
    ent["atr5"] = ent["atr14"] = 0.0010
    r = simulate(P, ent, Exit("level", cap=24), "EURUSD").iloc[0]
    assert r.reason == "TP" and r.exit_px == pytest.approx(1.1025) and r.bars == 2
    assert r.risk_pips == pytest.approx(10) and r.r == pytest.approx(2.5)
    # short: lustrzanie — TP niżej, SL wyżej
    rows_s = [FLAT, (1.1000, 1.1004, 1.0990, 1.0992), (1.0992, 1.1000, 1.0970, 1.0975), FLAT]
    P2 = prepare(bars(rows_s))
    lv2 = np.full((4, 2), np.nan)
    lv2[0] = [1.0975, 1.1006]
    ent2 = find_entries(P2, np.array([-1, 0, 0, 0]), lv2)
    ent2["atr5"] = ent2["atr14"] = 0.0010
    r2 = simulate(P2, ent2, Exit("level", cap=24), "EURUSD").iloc[0]
    assert r2.reason == "TP" and r2.exit_px == pytest.approx(1.0975) and r2.pips_gross == pytest.approx(25)
    # SL trafiony najpierw → SL; brak SL (NaN) → tylko TP albo czas, R względem ATR14
    lv3 = np.full((len(rows), 2), np.nan)
    lv3[0] = [1.1050, 1.0996]
    r3 = simulate(P, find_entries(P, np.array([1, 0, 0, 0, 0]), lv3).assign(atr5=0.001, atr14=0.001),
                  Exit("level", cap=24), "EURUSD").iloc[0]
    assert r3.reason == "SL" and r3.exit_px == pytest.approx(1.0996)
    lv4 = np.full((len(rows), 2), np.nan)
    lv4[0, 0] = 1.1050
    r4 = simulate(P, find_entries(P, np.array([1, 0, 0, 0, 0]), lv4).assign(atr5=0.001, atr14=0.001),
                  Exit("level", cap=3), "EURUSD").iloc[0]
    assert r4.reason == "czas" and r4.risk_pips == pytest.approx(10)


def test_level_exit_without_time_limit_d060():
    """D-061: cap = 0 — pozycja trwa do TP (także po > 24 świecach); gdy dane się kończą, jest „otwarta” i wyceniona po ostatnim
    close (nie znika z wyników — inaczej przegrane pozycje na końcu danych zawyżałyby wynik)."""
    n = 40
    flat = [(1.1000, 1.1004, 1.0996, 1.1000)] * n
    rows = [FLAT] + flat
    rows[35] = (1.1000, 1.1030, 1.0996, 1.1020)           # high 1.1030 ≥ TP 1.1025 — trafiony dopiero w 35. świecy
    P = prepare(bars(rows))
    lv = np.full((len(rows), 2), np.nan)
    lv[0, 0] = 1.1025                                      # tylko TP (średnia), bez SL
    ent = find_entries(P, np.array([1] + [0] * n), lv).assign(atr5=0.001, atr14=0.001)
    r = simulate(P, ent, Exit("level", cap=0), "EURUSD").iloc[0]
    assert r.reason == "TP" and r.exit_px == pytest.approx(1.1025) and r.bars == 35 and r.pips_gross == pytest.approx(25)
    # z limitem 24 ta sama pozycja zostałaby zamknięta „czasem” — to różnica D-061
    r24 = simulate(P, ent, Exit("level", cap=24), "EURUSD").iloc[0]
    assert r24.reason == "czas" and r24.bars == 24
    # TP nigdy nie trafiony → otwarta na końcu danych: wycena po ostatnim close, flaga w powodzie, MAE liczone
    rows2 = [FLAT] + [(1.1000, 1.1004, 1.0990, 1.0995)] * 30 + [(1.0995, 1.1002, 1.0980, 1.0985)]
    P2 = prepare(bars(rows2))
    lv2 = np.full((len(rows2), 2), np.nan)
    lv2[0, 0] = 1.1100
    ent2 = find_entries(P2, np.array([1] + [0] * (len(rows2) - 1)), lv2).assign(atr5=0.001, atr14=0.001)
    o = simulate(P2, ent2, Exit("level", cap=0), "EURUSD").iloc[0]
    last = len(rows2) - 1
    assert o.reason == "otwarta" and o.exit_px == pytest.approx(1.0985) and o.pips_gross == pytest.approx(-15)
    assert o.exit_i == last and o.exit_ts == T0 + (last + 1) * 3600 and o.mae == pytest.approx(20)
    # dwa wejścia: późniejsze też liczone do końca danych, wcześniejsze nie wpływa na późniejsze
    ent3 = find_entries(P2, np.array([1] + [0] * 9 + [1] + [0] * (len(rows2) - 11)), lv2).assign(atr5=0.001, atr14=0.001)
    res = simulate(P2, ent3, Exit("level", cap=0), "EURUSD")
    assert res.reason.tolist() == ["otwarta", "otwarta"] and res.exit_i.tolist() == [last, last]
    # porcjowanie okien (pamięć) nie zmienia wyniku
    import ia5.engine as eng
    old = eng.UNLIMITED_CELLS
    eng.UNLIMITED_CELLS = 10
    try:
        res2 = simulate(P2, ent3, Exit("level", cap=0), "EURUSD")
    finally:
        eng.UNLIMITED_CELLS = old
    pd.testing.assert_frame_equal(res, res2)
    with pytest.raises(ValueError):
        simulate(P2, ent3, Exit("time", n=3, cap=0), "EURUSD")


def test_sandbox_allows_cap_zero_only_for_level_d060():
    from ia5.sandbox import StrategyError, read_settings

    ok = {"EXITS": [{"kind": "level", "cap": 0}], "levels": lambda d, p, i: None}
    read_settings(ok)
    for bad in ({"kind": "time", "n": 5, "cap": 0}, {"kind": "atr", "n": 14, "tp": 2.0, "cap": 0},
                {"kind": "level", "cap": 481}, {"kind": "level", "cap": -1}):
        with pytest.raises(StrategyError):
            read_settings({"EXITS": [bad], "levels": lambda d, p, i: None})
