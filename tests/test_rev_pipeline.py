"""REV (D-063): kursy PLN — dane do liczenia (pln_ready), sprzątanie lokalne, publikacja na gałąź data."""
import json

import pandas as pd
from ia5 import ready
from ia5.rev_config import CLEAN_PLN_VERSION
from rev_fixtures import synthetic_raw
from test_publish import ls_remote_files, repo  # noqa: F401 — fikstura lokalnego repo gałęzi data


def test_build_pln_writes_ready_with_source(tmp_path):
    raw = synthetic_raw(["EUR", "USD"], start="2020-01-01", end="2026-11-10")
    out = ready.build_pln(raw, tmp_path, log=lambda m: None)
    for c in ("EUR", "USD"):
        df = pd.read_parquet(tmp_path / f"{c}.parquet")
        assert list(df.columns) == ["ts", "close", "close_ts", "day", "spike", "big"]
        info = json.loads((tmp_path / f"{c}.json").read_text())
        assert info["source"] == "yahoo" and info["series"] == "pln" and info["version"] == CLEAN_PLN_VERSION
        assert out[c]["rebuilt"]
    again = ready.build_pln(raw, tmp_path, log=lambda m: None)
    assert not again["EUR"]["rebuilt"]
    assert set(ready.load_pln(tmp_path)) == {"EUR", "USD"}


def test_build_pln_skips_short_history(tmp_path):
    raw = {"EUR": synthetic_raw(["EUR"], start="2026-06-01", end="2026-11-10")["EUR"].iloc[:100]}
    out = ready.build_pln(raw, tmp_path, log=lambda m: None)
    assert out["EUR"]["bars"] == 0 and not (tmp_path / "EUR.parquet").exists()


def test_build_pln_removes_currencies_not_in_input(tmp_path):
    raw = synthetic_raw(["EUR", "USD"], start="2020-01-01", end="2026-11-10")
    ready.build_pln(raw, tmp_path, log=lambda m: None)
    ready.build_pln({"EUR": raw["EUR"]}, tmp_path, log=lambda m: None)
    assert not (tmp_path / "USD.parquet").exists()


def test_enforce_local_data_keeps_pln(tmp_path, monkeypatch):
    from ia5 import cli, store

    data = tmp_path / "data"
    for d in ("yahoo", "yahoo_pln", "pln_ready", "obce"):
        (data / d).mkdir(parents=True)
    for f in ("yahoo_pln/EUR.parquet", "yahoo_pln/RUB.parquet", "pln_ready/EUR.parquet", "obce/x"):
        (data / f).write_bytes(b"1")
    monkeypatch.setattr(cli, "DATA", data)
    monkeypatch.setattr(store, "YAHOO", data / "yahoo")
    monkeypatch.setattr(store, "YAHOO_D1", data / "yahoo_d1")
    monkeypatch.setattr(store, "YAHOO_PLN", data / "yahoo_pln")
    cli.enforce_local_data(log=lambda m: None)
    assert sorted(f.name for f in (data / "yahoo_pln").iterdir()) == ["EUR.parquet"]
    assert (data / "pln_ready" / "EUR.parquet").exists()
    assert not (data / "obce").exists()


def test_publish_candles_pln_folder(repo):  # noqa: F811
    from ia5 import publish

    raw = synthetic_raw(["EUR", "CHF"], start="2024-01-01", end="2026-11-10")
    assert publish.publish_candles_pln(raw, "Europe/London", log=lambda m: None)
    files = ls_remote_files(repo)
    assert {"candles_pln/EUR.parquet", "candles_pln/CHF.parquet", "candles_pln/manifest.json"} <= files
    m = json.loads((publish.DATA_REPO / "candles_pln" / "manifest.json").read_text())
    assert m["series"] == "pln" and m["ticker"] == "{}PLN=X"
    assert publish.publish_candles_pln(raw, "Europe/London", log=lambda m: None) is None
