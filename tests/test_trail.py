"""D-035: stop kroczący (wyjście `trail`) — złote scenariusze na ręcznie ułożonych świecach."""
import numpy as np
import pandas as pd
import pytest
from ia5.engine import Exit, find_entries, prepare, simulate
from ia5.sandbox import StrategyError, read_settings

T0 = 1735516800


def bars(rows):
    o, h, lo, c = zip(*rows)
    return pd.DataFrame({"ts": T0 + 3600 * np.arange(len(rows)), "open": o, "high": h, "low": lo, "close": c})


def sim(df, d, ex, atr=0.001, signal_i=0):
    P = prepare(df)
    sig = np.zeros(len(df))
    sig[signal_i] = d
    ent = find_entries(P, sig)
    ent["atr14"] = atr
    return simulate(P, ent, ex, "EURUSD").iloc[0]


FLAT = (1.1000, 1.1002, 1.0998, 1.1000)


def test_long_trail_moves_up_and_exits_at_level():
    rows = [FLAT,                                # 0: sygnał
            FLAT,                                # 1: wejście 1.1000, stop 1.0980 (2 ATR)
            (1.1000, 1.1050, 1.0999, 1.1045),    # 2: high 1.1050 — stop dla świecy 3: 1.1050 − 0.0010 = 1.1040
            (1.1045, 1.1048, 1.1030, 1.1035)]    # 3: low 1.1030 ≤ 1.1040 → wyjście po 1.1040
    rows += [FLAT] * 10
    r = sim(bars(rows), 1, Exit("trail", n=14, sl=2.0, trail=1.0, cap=480))
    assert r.reason == "stop kroczący" and int(r.exit_i) == 3 and np.isclose(r.exit_px, 1.1040)
    assert np.isclose(r.pips_gross, 40) and np.isclose(r.risk_pips, 20)


def test_same_bar_high_does_not_move_stop():
    # świeca 2: high 1.1050 i low 1.0990. Stop dla świecy 2 liczy się tylko z wcześniejszych świec:
    # high świecy wejścia 1.1002 − 0.0010 = 1.0992 → wyjście po 1.0992 (a nie po 1.1040 z high tej samej świecy)
    rows = [FLAT, FLAT, (1.1000, 1.1050, 1.0990, 1.1000)] + [FLAT] * 5
    r = sim(bars(rows), 1, Exit("trail", n=14, sl=2.0, trail=1.0, cap=480))
    assert int(r.exit_i) == 2 and np.isclose(r.exit_px, 1.0992) and r.reason == "stop kroczący"


def test_gap_below_trail_exits_at_open_and_short_mirror():
    rows = [FLAT, FLAT, (1.1000, 1.1050, 1.0999, 1.1045), (1.1020, 1.1025, 1.1010, 1.1015)] + [FLAT] * 5
    r = sim(bars(rows), 1, Exit("trail", n=14, sl=2.0, trail=1.0, cap=480))
    assert int(r.exit_i) == 3 and np.isclose(r.exit_px, 1.1020)           # luka pod stopem → open (B6)
    rows = [FLAT, FLAT, (1.1000, 1.1001, 1.0950, 1.0955), (1.0955, 1.0970, 1.0952, 1.0965)] + [FLAT] * 5
    r = sim(bars(rows), -1, Exit("trail", n=14, sl=2.0, trail=1.0, cap=480))
    assert r.reason == "stop kroczący" and np.isclose(r.exit_px, 1.0960)  # short: 1.0950 + 0.0010


def test_initial_stop_and_time_cap():
    rows = [FLAT, FLAT, (1.1000, 1.1001, 1.0975, 1.0978)] + [FLAT] * 5
    r = sim(bars(rows), 1, Exit("trail", n=14, sl=2.0, trail=3.0, cap=480))
    assert r.reason == "SL" and np.isclose(r.exit_px, 1.0980)
    r = sim(bars([FLAT] * 12), 1, Exit("trail", n=14, sl=2.0, trail=1.0, cap=5))
    assert r.reason == "czas" and int(r.bars) == 5


def test_trail_settings_validation():
    assert read_settings({"EXITS": [{"kind": "trail", "n": 14, "sl": 2, "trail": 3, "cap": 480}]})["pyramid"] == 1
    for bad in ({"kind": "trail", "sl": 0, "trail": 3}, {"kind": "trail", "sl": 2, "trail": 0}, {"kind": "trail", "sl": 2, "trail": 3, "cap": 481}):
        with pytest.raises(StrategyError):
            read_settings({"EXITS": [bad]})
