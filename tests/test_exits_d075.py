"""D-075: nowe opcje wyjść (breakeven, stop czasowy bez zysku, zamknięcie przed weekendem, częściowe TP) i swapy —
złote scenariusze na ręcznie ułożonych świecach."""
import numpy as np
import pandas as pd
import pytest
from ia5 import config
from ia5.engine import Exit, default_exits, find_entries, prepare, run, simulate
from ia5.sandbox import StrategyError, read_settings

T0 = 1735516800 + 3600 * 24 * 5   # poniedziałek 2025-01-06 00:00 UTC
FLAT = (1.1000, 1.1002, 1.0998, 1.1000)


def bars(rows, ts=None):
    o, h, lo, c = zip(*rows)
    ts = T0 + 3600 * np.arange(len(rows)) if ts is None else np.asarray(ts)
    return pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c})


def sim(df, d, ex, atr=0.001, signal_i=0):
    P = prepare(df)
    sig = np.zeros(len(df))
    sig[signal_i] = d
    ent = find_entries(P, sig)
    ent["atr14"] = ent["atr5"] = atr
    return simulate(P, ent, ex, "EURUSD").iloc[0]


def test_options_off_change_nothing():
    """Domyślne wartości opcji = wynik jak w silniku 0.14 (etykiety też bez zmian)."""
    for ex in default_exits():
        assert ex.label() == ex._base_label()
    assert Exit("atr", tp=2, sl=1).be == 0 and not Exit("time", n=3).weekend


def test_breakeven_moves_stop_to_entry():
    rows = [FLAT, FLAT,                              # 1: wejście 1.1000, SL 1.0980 (2 ATR)
            (1.1000, 1.1016, 1.0999, 1.1010),        # 2: high +1,6 ATR ≥ be 1,5 → od świecy 3 stop na 1.1000
            (1.1010, 1.1012, 1.0995, 1.0997)]        # 3: low 1.0995 ≤ 1.1000 → wyjście po 1.1000
    rows += [FLAT] * 6
    r = sim(bars(rows), 1, Exit("atr", n=14, tp=4, sl=2, cap=24, be=1.5))
    assert r.reason == "breakeven" and int(r.exit_i) == 3 and np.isclose(r.exit_px, 1.1000) and np.isclose(r.pips_gross, 0)
    r = sim(bars(rows), 1, Exit("atr", n=14, tp=4, sl=2, cap=8))           # bez breakeven: ta sama świeca nie zamyka
    assert r.reason != "breakeven" and int(r.exit_i) != 3


def test_breakeven_not_from_same_bar_high():
    # świeca 2: high +2 ATR i low pod wejściem — w tej świecy stop jeszcze stoi na SL (kolejności nie znamy);
    # przesuwa się dopiero od świecy 3, która schodzi do 1.0998 → breakeven na świecy 3, nie 2
    rows = [FLAT, FLAT, (1.1000, 1.1020, 1.0990, 1.1000)] + [FLAT] * 6
    r = sim(bars(rows), 1, Exit("atr", n=14, tp=4, sl=2, cap=8, be=1.0))
    assert r.reason == "breakeven" and int(r.exit_i) == 3


def test_stale_exits_when_not_in_profit():
    rows = [FLAT, FLAT, (1.1000, 1.1003, 1.0996, 1.0999), (1.0999, 1.1001, 1.0990, 1.0995)] + [FLAT] * 10
    r = sim(bars(rows), 1, Exit("time", n=12, cap=12, stale=3))
    assert r.reason == "bez zysku" and int(r.bars) == 3 and np.isclose(r.exit_px, 1.0995)   # zamknięcie 3. świecy
    up = [FLAT, FLAT, FLAT, (1.1000, 1.1010, 1.0999, 1.1008)] + [FLAT] * 10
    r = sim(bars(up), 1, Exit("time", n=12, cap=12, stale=3))
    assert r.reason == "czas" and int(r.bars) == 12                                          # w zysku — trzyma dalej


def test_weekend_exit_on_last_bar_before_break():
    ts = list(T0 + 3600 * np.arange(6)) + list(T0 + 3600 * 5 + 3600 * 49 + 3600 * np.arange(6))   # przerwa 48 h po świecy 5
    rows = [FLAT] * 3 + [(1.1000, 1.1005, 1.0999, 1.1004)] * 3 + [FLAT] * 6
    r = sim(bars(rows, ts), 1, Exit("time", n=8, cap=8, weekend=True))
    assert r.reason == "weekend" and int(r.exit_i) == 5 and np.isclose(r.exit_px, 1.1004)
    r = sim(bars(rows, ts), 1, Exit("time", n=8, cap=8))
    assert r.reason == "czas" and int(r.exit_i) == 8


def test_partial_tp():
    rows = [FLAT, FLAT, (1.1000, 1.1012, 1.0999, 1.1008),       # 2: high ≥ 1 ATR → połowa po 1.1010
            (1.1008, 1.1009, 1.0975, 1.0978)] + [FLAT] * 4     # 3: SL 1.0980
    r = sim(bars(rows), 1, Exit("atr", n=14, tp=3, sl=2, cap=6, tp1=1.0, part=0.5))
    assert r.reason == "SL" and bool(r.partial)
    assert np.isclose(r.pips_gross, 0.5 * 10 + 0.5 * -20) and np.isclose(r.part_pips, 5)
    # tp1 i SL w tej samej świecy → bez częściowego (pesymistycznie)
    same = [FLAT, FLAT, (1.1000, 1.1012, 1.0975, 1.0990)] + [FLAT] * 4
    r = sim(bars(same), 1, Exit("atr", n=14, tp=3, sl=2, cap=5, tp1=1.0))
    assert r.reason == "SL" and not bool(r.partial) and np.isclose(r.pips_gross, -20)
    # TP wyżej niż tp1 w tej samej świecy → częściowe też
    big = [FLAT, FLAT, (1.1000, 1.1040, 1.0999, 1.1035)] + [FLAT] * 4
    r = sim(bars(big), 1, Exit("atr", n=14, tp=3, sl=2, cap=5, tp1=1.0))
    assert r.reason == "TP" and bool(r.partial) and np.isclose(r.pips_gross, 0.5 * 10 + 0.5 * 30)


def test_swaps_from_table(monkeypatch):
    rows = [FLAT] * 80
    df = bars(rows)
    sig = np.zeros(len(df))
    sig[30] = 1
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=30, cap=30)], hours=False)
    base = res["outcomes"].iloc[0]
    assert base["swap_pips"] == 0 and base["nights"] >= 1
    monkeypatch.setitem(config.SWAP_PIPS, "EURUSD", (-0.4, 0.1))
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=30, cap=30)], hours=False)
    o = res["outcomes"].iloc[0]
    assert np.isclose(o["swap_pips"], -0.4 * base["nights"]) and np.isclose(o["pips_net"], base["pips_net"] - 0.4 * base["nights"])


@pytest.mark.parametrize("bad", [{"kind": "time", "n": 3, "cap": 3, "stale": 5}, {"kind": "atr", "tp": 1, "sl": 1, "tp1": 1, "part": 1.2},
                                 {"kind": "atr", "tp": 1, "sl": 1, "be": -1}, {"kind": "time", "n": 3, "weekend": 1}])
def test_settings_validation(bad):
    with pytest.raises(StrategyError):
        read_settings({"EXITS": [bad]})
    ok = read_settings({"EXITS": [{"kind": "atr", "tp": 2, "sl": 1, "cap": 24, "be": 1, "stale": 5, "weekend": True, "tp1": 1}]})
    assert ok["pyramid"] == 1
