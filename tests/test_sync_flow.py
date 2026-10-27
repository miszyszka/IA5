"""ia5 sync: obieg pobieracza (fetch) ze statusami na żywo, potem do_prepare — mapa pokrycia i dane do liczenia (bez sieci)."""
from datetime import date

import pandas as pd
from ia5 import cli, cloud, dukascopy, fetch, publish, store


def test_do_sync_live_states_and_coverage(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "DATA", tmp_path)
    monkeypatch.setattr(cli, "PAIRS", {"EURUSD": None, "USDJPY": None})
    monkeypatch.setattr(fetch, "PAIRS", {"EURUSD": None, "USDJPY": None})
    monkeypatch.setattr(store, "READY", tmp_path / "h1_ready")
    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)
    monkeypatch.setattr(dukascopy, "BLOCK_PAUSE", (0, 0))

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

    def fake_fetch(pair, d, *a):
        if pair == "USDJPY" and d.month == 2:
            raise RuntimeError("timeout")
        t = int(pd.Timestamp(d, tz="UTC").timestamp()) + 10 * 3600
        return pd.DataFrame([[t + 60 * i, 1, 1.001, 0.999, 1, 1, 1.0001, 1.0011, 0.9991, 1.0001, 1] for i in range(60)],
                            columns=dukascopy.COLS)

    monkeypatch.setattr(dukascopy, "fetch_day", fake_fetch)
    published = {}
    monkeypatch.setattr(cloud, "read_status", lambda: {})
    monkeypatch.setattr(cloud, "sync_yahoo", lambda folder, log: {p: pd.DataFrame(columns=["ts", "open", "high", "low", "close"])
                                                                for p in ("EURUSD", "USDJPY")})
    monkeypatch.setattr(cloud, "set_data_sha", lambda sha: None)
    monkeypatch.setattr(publish, "publish_candles", lambda *a, **k: None)
    monkeypatch.setattr(publish, "publish_coverage", lambda cov, log: published.setdefault("cov", cov) and "abc")

    live, state = {}, {}
    seen = []
    orig = fetch.fetch_pair

    def spy(pair, root, **k):
        seen.append({p: v for p, v in live["pairs"].items()})
        return orig(pair, root, **k)

    monkeypatch.setattr(fetch, "fetch_pair", spy)
    fetch.run_forever(tmp_path, log=lambda m: None, state=state, live=live, sleep=lambda s: None, once=True)
    assert seen[0] == {"EURUSD": "...", "USDJPY": "..."}  # pierwszy obraz: nic jeszcze nie ma
    assert live["pairs"] == {"EURUSD": "oo~", "USDJPY": "ox~"}
    assert state["pairs"]["EURUSD"] == 100.0 and state["pairs"]["USDJPY"] < 100
    ctx = cli.do_prepare()
    d = published["cov"]["sources"]["dukascopy"]["pairs"]
    assert [m[0] for m in d["USDJPY"]["m"]] == [1, 0, 2]   # luty bez pliku — „nie pobrany”, dociągnie następny obieg
    assert ctx["ready"]["EURUSD"]["months"] == 3          # EUR/USD: wszystkie miesiące zatwierdzone → do liczenia
    assert (tmp_path / "h1_ready" / "EURUSD.parquet").exists()
    # D-038: USD/JPY też jest liczona — ale tylko z zatwierdzonych miesięcy (luty bez pliku, marzec niepełny → poza)
    assert ctx["ready"]["USDJPY"]["months"] < 3
