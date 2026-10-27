"""ia5 start → do_sync: statusy miesięcy na żywo w heartbeacie i publikacja mapy pokrycia (bez sieci)."""
from datetime import date

import pandas as pd
from ia5 import cli, cloud, dukascopy, publish


def test_do_sync_live_states_and_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "DATA", tmp_path)
    monkeypatch.setattr(cli, "PAIRS", {"EURUSD": None, "USDJPY": None})
    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)

    class Today(dukascopy.datetime):
        @classmethod
        def now(cls, tz=None):
            return dukascopy.datetime(2024, 3, 10, 6, tzinfo=tz)

    monkeypatch.setattr(dukascopy, "datetime", Today)
    import datetime as dt

    class Now(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return dt.datetime(2024, 3, 10, 6, tzinfo=tz)

    monkeypatch.setattr(dt, "datetime", Now)

    def fake_fetch(pair, d):
        if pair == "USDJPY" and d.month == 2:
            raise RuntimeError("timeout")
        t = int(pd.Timestamp(d, tz="UTC").timestamp()) + 10 * 3600
        return pd.DataFrame([[t + 60 * i, 1, 1.001, 0.999, 1, 1, 1.0001, 1.0011, 0.9991, 1.0001, 1] for i in range(60)],
                            columns=dukascopy.COLS)

    monkeypatch.setattr(dukascopy, "fetch_day", fake_fetch)
    beats, published = [], {}
    monkeypatch.setattr(cloud, "read_status", lambda: {})
    monkeypatch.setattr(cloud, "sync_yahoo", lambda folder, log: {p: pd.DataFrame(columns=["ts", "open", "high", "low", "close"])
                                                                for p in ("EURUSD", "USDJPY")})
    monkeypatch.setattr(cloud, "set_data_sha", lambda sha: None)
    monkeypatch.setattr(publish, "publish_candles", lambda *a, **k: None)
    monkeypatch.setattr(publish, "publish_coverage", lambda cov, log: published.setdefault("cov", cov) and "abc")

    live = {}
    cli.do_sync(live=live, beat=lambda: beats.append({k: dict(v) if isinstance(v, dict) else v for k, v in live.items()}))
    assert beats[0]["pairs"] == {"EURUSD": "...", "USDJPY": "..."}  # pierwszy obraz: nic jeszcze nie ma
    assert live["pairs"] == {"EURUSD": "oo~", "USDJPY": "ox~"}
    d = published["cov"]["sources"]["dukascopy"]["pairs"]
    assert [m[0] for m in d["USDJPY"]["m"]] == [1, 4, 2]
