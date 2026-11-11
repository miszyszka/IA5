"""D-050: MAX_PAIRS — najwyżej k par z otwartymi pozycjami naraz, PAIR_RANK przy równoczesnych sygnałach."""
import numpy as np
import pandas as pd

from ia5 import engine

T0 = 1735545600  # poniedziałek 2024-12-30 08:00 UTC (09:00 czasu polskiego)


def flat(n=400, p0=1.1):
    ts = T0 + 3600 * np.arange(n)
    c = p0 + 0.0001 * np.sin(np.arange(n) / 5)
    return pd.DataFrame({"ts": ts, "open": c, "high": c + 0.0003, "low": c - 0.0003, "close": c})


def run(sig_a, sig_b, **kw):
    h1 = {"EURUSD": flat(), "GBPUSD": flat(p0=1.3)}
    sig = {(0, "EURUSD"): sig_a, (0, "GBPUSD"): sig_b}
    res = engine.run(h1, sig, [{}], exits=[engine.Exit("time", n=5, cap=5)], hours=False, **kw)
    o = res["outcomes"].merge(res["entries"][["entry_id", "entry_ts"]], on="entry_id")
    return o.sort_values("entry_ts"), res["skipped"]


def sig_at(*idx, n=400, v=1.0):
    s = np.zeros(n, np.float32)
    s[list(idx)] = v
    return s


def test_without_limit_both_pairs_trade():
    o, _ = run(sig_at(100), sig_at(100))
    assert sorted(o.pair) == ["EURUSD", "GBPUSD"]


def test_same_bar_rank_picks_pair():
    o, sk = run(sig_at(100), sig_at(100), max_pairs=1, pair_rank=["GBPUSD", "EURUSD"])
    assert list(o.pair) == ["GBPUSD"] and sk["limit_par"] == 1
    o, _ = run(sig_at(100), sig_at(100), max_pairs=1, pair_rank=["EURUSD", "GBPUSD"])
    assert list(o.pair) == ["EURUSD"]


def test_pair_busy_until_exit_then_free():
    # EURUSD wchodzi na 101 i trzyma 5 świec (do 105 włącznie); GBPUSD na 103 zablokowany, na 110 wolny
    o, sk = run(sig_at(100), sig_at(102, 109), max_pairs=1)
    assert list(o.pair) == ["EURUSD", "GBPUSD"] and sk["limit_par"] == 1
    assert int(o[o.pair == "GBPUSD"].entry_ts.iloc[0]) == T0 + 3600 * 110


def test_pyramid_inside_occupied_pair_allowed():
    o, _ = run(sig_at(100, 101, 102), sig_at(101), max_pairs=1, pyramid=3)
    assert list(o.pair) == ["EURUSD"] * 3


def test_two_pairs_allowed():
    o, _ = run(sig_at(100), sig_at(100), max_pairs=2)
    assert len(o) == 2
