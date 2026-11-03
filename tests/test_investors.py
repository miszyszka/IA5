"""Wirtualni inwestorzy (E6, D-045): ten sam silnik co backtest, start od chwili dodania, wspólny kapitał."""
import numpy as np
import pandas as pd
import pytest
from ia5 import engine, investors, portfolio
from ia5.backtest import exits_from
from ia5.sandbox import run_strategy_code

CODE = '''
HYPOTHESIS = "Wyprzedanie w trendzie wzrostowym wraca."
PARAMS = {"rsi_level": [30, 40]}
HOURS = False

def signals(df, p, ind):
    sma = ind.sma(df.close, 50)
    rsi = ind.rsi(df.close, 14)
    up = ind.cross_below(rsi, p["rsi_level"]) & (sma > sma.shift(5))
    dn = ind.cross_above(rsi, 100 - p["rsi_level"]) & (sma < sma.shift(5))
    return up.astype("int8") - dn.astype("int8")
'''
H = 3600


def make_h1(n=3000, seed=1, start=1.1):
    rng = np.random.default_rng(seed)
    c = start + np.cumsum(rng.normal(0, 0.0008, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.0006
    lo = np.minimum(o, c) - rng.random(n) * 0.0006
    return pd.DataFrame({"ts": 1600041600 + 3600 * np.arange(n), "open": o, "high": h, "low": lo, "close": c})


@pytest.fixture()
def h1_dir(tmp_path):
    d = tmp_path / "h1"
    d.mkdir()
    make_h1(n=3000, seed=1).to_parquet(d / "EURUSD.parquet", index=False)
    make_h1(n=3000, seed=2, start=1.3).to_parquet(d / "GBPUSD.parquet", index=False)
    return d


def inv(start, variant=1, pct=10.0, capital=10_000.0, code=CODE):
    return {"id": "x", "name": "Test", "capital": capital, "pct": pct, "createdAt": start,
            "strategies": [{"strategyId": "s", "name": "RSI", "code": code, "variantId": variant, "variantLabel": "v"}]}


def engine_trades(h1_dir, variant):
    sig, meta = run_strategy_code(CODE, h1_dir)
    exits = exits_from(meta.get("exits"))
    h1 = {f.stem: pd.read_parquet(f) for f in sorted(h1_dir.glob("*.parquet"))}
    signals = {}
    for pid in range(len(meta["params"])):
        for pair, df in h1.items():
            arr = np.zeros(len(df), np.float32)
            part = sig[(sig.param_id == pid) & (sig.pair == pair)]
            arr[part["i"].to_numpy(int)] = part["sig"].to_numpy(np.float32)
            signals[(pid, pair)] = arr
    res = engine.run(h1, signals, meta["params"], exits=exits, hours=False)
    out = res["outcomes"].join(res["entries"].set_index("entry_id")[["entry_ts"]], on="entry_id")
    return out[out.variant_id == variant]


def test_same_trades_as_backtest_engine(h1_dir):
    """Od początku danych inwestor ma dokładnie te transakcje co silnik backtestu (poza ostatnią otwartą)."""
    st = investors.compute(inv(0, variant=1), h1_dir)
    paper = pd.DataFrame(st["trades"])
    closed = paper[paper.status != "otwarta"].sort_values(["pair", "entry_ts"]).reset_index(drop=True)
    eng = engine_trades(h1_dir, 1).sort_values(["pair", "entry_ts"]).reset_index(drop=True)
    first_open = paper[paper.status == "otwarta"].groupby("pair").entry_ts.min()
    eng = eng[[ts < first_open.get(p, np.inf) for p, ts in zip(eng.pair, eng.entry_ts)]].reset_index(drop=True)
    assert len(closed) == len(eng) > 5
    assert (closed.entry_ts.to_numpy() == eng.entry_ts.to_numpy()).all()
    assert (closed.exit_ts.to_numpy() == eng.exit_ts.to_numpy()).all()
    assert np.allclose(closed.pips_net.to_numpy(), eng.pips_net.round(2).to_numpy(), atol=0.011)


def test_only_signals_after_start(h1_dir):
    start = int(pd.read_parquet(h1_dir / "EURUSD.parquet").ts.iloc[2000])
    st = investors.compute(inv(start), h1_dir)
    assert st["trades"] and all(t["signal_ts"] + H > start for t in st["trades"])
    assert st["curve"]["ts"][0] == start and st["curve"]["equity"][0] == 10_000.0


def test_capital_matches_portfolio_simulation():
    """Same transakcje zamknięte, jedna strategia: kapitał = portfolio.simulate_equity (8.5)."""
    t = pd.DataFrame({"pair": ["EURUSD"] * 3, "entry_ts": [0, 10, 50], "exit_ts": [20, 40, 60], "entry_px": [1.1] * 3,
                      "pips_net": [10.0, -5.0, 7.0], "weight": [1.0, 2.0, 1.0], "status": ["zamknięta"] * 3})
    for pct in (5, 30, 60):
        b = investors.book(t, 10_000, pct)
        ref = portfolio.simulate_equity(t, pct)
        assert b["realized"] == pytest.approx(ref["final"]) and b["skipped_margin"] == ref["skipped_margin"]
    b = investors.book(t, 10_000, 60)   # 60% + 120% > 100% → druga pozycja pominięta (B4)
    assert b["trades"].status.tolist()[1] == "pominięta: brak wolnego depozytu"


def test_open_position_marked_to_last_close(h1_dir):
    last = int(pd.read_parquet(h1_dir / "EURUSD.parquet").ts.iloc[-1])
    code = ("HOURS = False\ndef signals(df, p, ind):\n"
            f"    return pd.Series(df.index == pd.Timestamp({last - 3 * H}, unit='s', tz='UTC'), index=df.index).astype('int8')\n")
    st = investors.compute(inv(0, variant=4, code=code), h1_dir)   # wejście 2 świece przed końcem, wyjście po 6 → otwarta
    op = [t for t in st["trades"] if t["status"] == "otwarta"]
    assert op, "oczekiwana przynajmniej jedna otwarta pozycja"
    df = pd.read_parquet(h1_dir / f"{op[0]['pair']}.parquet")
    assert op[0]["exit_ts"] is None and op[0]["exit_px"] == pytest.approx(df.close.iloc[-1])
    assert st["equity"]["now"] == pytest.approx(st["equity"]["realized"] + st["equity"]["unrealized"], abs=0.02)
    assert st["curve"]["ts"][-1] == int(df.ts.iloc[-1]) + H


def test_broken_strategy_reported_not_crashing(h1_dir):
    st = investors.compute(inv(0, code="def signals(df, p, ind):\n    return df.close.shift(-1) > df.close\n"), h1_dir)
    assert "look-ahead" in st["strategies"][0]["error"] and st["trades"] == []


def test_content_hash_ignores_computed_at(h1_dir):
    a = investors.compute(inv(0), h1_dir, now=1)
    b = {**a, "computedAt": 2}
    assert investors.content_hash(a) == investors.content_hash(b)


def test_handle_investors_owner_only_and_delete(monkeypatch):
    """S1: liczony tylko inwestor właściciela; do_usuniecia → zdjęty z gałęzi data i z Firestore."""
    from ia5 import cli, cloud, publish

    calls = {"computed": [], "published": None, "deleted": []}
    monkeypatch.setattr(cloud, "heartbeat", lambda *a, **k: None)
    monkeypatch.setattr(cloud, "delete_investor", lambda i: calls["deleted"].append(i))
    monkeypatch.setattr(publish, "publish_investors", lambda st, rm, log=print: calls.__setitem__("published", (sorted(st), rm)))
    monkeypatch.setattr(investors, "compute", lambda d, *a, **k: calls["computed"].append(d["id"]) or
                        {"equity": {"now": 1.0, "return_pct": 0.0}, "counts": {"closed": 0, "open": 0}})
    docs = {"a": {"createdBy": "me", "status": "aktywny", "name": "A"},
            "b": {"createdBy": "obcy", "status": "aktywny", "name": "B"},
            "c": {"createdBy": "me", "status": "do_usuniecia", "name": "C"}}
    cli.handle_investors(docs, "me", {})
    assert calls["computed"] == ["a"] and calls["published"] == (["a"], ["c"]) and calls["deleted"] == ["c"]
