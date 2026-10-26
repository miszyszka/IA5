"""Zgodność z niezależnym silnikiem backtesting.py (CLAUDE.md sekcja 9).

Strategia referencyjna: long, gdy SMA10 przecina SMA30 w górę; wyjście po 5 świecach; jedna pozycja naraz.
Dane syntetyczne z open[t] = close[t-1], więc nasze wyjście na zamknięciu świecy e+4 i wyjście
backtesting.py na otwarciu świecy e+5 to ta sama cena. Wymagana identyczna lista transakcji.
"""
import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind
from ia5.engine import Exit, run

bt = pytest.importorskip("backtesting")
N = 5


@pytest.fixture(scope="module")
def data():
    rng = np.random.default_rng(42)
    n = 4000
    c = 1.1 + np.cumsum(rng.normal(0, 0.0008, n))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + rng.random(n) * 0.0006
    lo = np.minimum(o, c) - rng.random(n) * 0.0006
    ts = 1761523200 + 3600 * np.arange(n)
    df = pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c})
    sig = ind.cross_above(ind.sma(df.close, 10), ind.sma(df.close, 30)).astype("int8").to_numpy()
    return df, sig


def ours(df, sig):
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=N, cap=N)])
    t = res["outcomes"].merge(res["entries"][["entry_id", "entry_i", "entry_px"]], on="entry_id")
    return [(int(a), round(b, 10), int(c) + 1, round(d, 10))
            for a, b, c, d in zip(t.entry_i, t.entry_px, t.exit_i, t.exit_px)]


def reference(df, sig):
    class Ref(bt.Strategy):
        def init(self):
            pass

        def next(self):
            k = len(self.data) - 1
            closing = False
            for t in self.trades:
                if k - t.entry_bar + 1 >= N:
                    t.close()
                    closing = True
            if sig[k] == 1 and (not self.position or closing):
                self.buy(size=1000)

    data = pd.DataFrame({"Open": df.open.to_numpy(), "High": df.high.to_numpy(),
                         "Low": df.low.to_numpy(), "Close": df.close.to_numpy()},
                        index=pd.to_datetime(df.ts, unit="s"))
    stats = bt.Backtest(data, Ref, cash=1_000_000, commission=0, trade_on_close=False).run()
    tr = stats._trades
    return [(int(a), round(b, 10), int(c), round(d, 10))
            for a, b, c, d in zip(tr.EntryBar, tr.EntryPrice, tr.ExitBar, tr.ExitPrice)]


def test_same_trades_as_backtesting_py(data):
    df, sig = data
    a, b = ours(df, sig), reference(df, sig)
    assert len(a) > 50
    assert a == b


def test_same_trades_with_atr_tp_sl(data):
    """TP 1,5×ATR14, SL 1×ATR14, limit 24 świec. Poziomy liczone od ceny wejścia (= close świecy sygnału)."""
    df, sig = data
    tp_k, sl_k, cap = 1.5, 1.0, 24
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("atr", n=14, tp=tp_k, sl=sl_k, cap=cap)])
    t = res["outcomes"].merge(res["entries"][["entry_id", "entry_i", "entry_px"]], on="entry_id")
    # ExitBar w backtesting.py: świeca, w której padł TP/SL; dla limitu czasu — następna świeca (open)
    a = [(int(e), round(p, 10), int(x) + (1 if r == "czas" else 0), round(xp, 10), r)
         for e, p, x, xp, r in zip(t.entry_i, t.entry_px, t.exit_i, t.exit_px, t.reason)]
    atr14 = ind.atr(df, 14).to_numpy()

    class Ref(bt.Strategy):
        def init(self):
            pass

        def next(self):
            k = len(self.data) - 1
            closing = False
            for tr in self.trades:
                if k - tr.entry_bar + 1 >= cap:
                    tr.close()
                    closing = True
            if sig[k] == 1 and (not self.position or closing) and not np.isnan(atr14[k]):
                px = df.close.iloc[k]
                self.buy(size=1000, tp=px + tp_k * atr14[k], sl=px - sl_k * atr14[k])

    data_bt = pd.DataFrame({"Open": df.open.to_numpy(), "High": df.high.to_numpy(),
                            "Low": df.low.to_numpy(), "Close": df.close.to_numpy()},
                           index=pd.to_datetime(df.ts, unit="s"))
    tr = bt.Backtest(data_bt, Ref, cash=1_000_000, commission=0).run()._trades
    b = [(int(e), round(p, 10), int(x), round(xp, 10)) for e, p, x, xp in
         zip(tr.EntryBar, tr.EntryPrice, tr.ExitBar, tr.ExitPrice)]
    assert len(a) > 50
    assert [x[:4] for x in a] == b
