"""REV (D-063): badanie i portfel w ia5 start (Mac) i ia5 live (GitHub Actions), publikacja rev/ na gałęzi data."""
import json
import time

import pytest
from ia5 import cli, cloud, publish, ready, rev_config, rev_live, rev_research, store

CODES = ["EUR", "USD", "CHF", "GBP", "JPY", "NOK", "SEK", "CZK", "HUF", "AUD"]


@pytest.fixture(scope="module")
def pln():
    from rev_fixtures import synthetic_ready

    return synthetic_ready(CODES, start="2004-01-01", end="2026-11-10", seed=41)


@pytest.fixture
def env(monkeypatch, tmp_path, pln):
    calls = {"published": [], "logs": [], "research": 0, "live": 0}
    repo = tmp_path / "data-repo"
    (repo / "rev").mkdir(parents=True)
    monkeypatch.setattr(store, "DATA_REPO", repo)
    monkeypatch.setattr(store, "REV", tmp_path / "rev")
    monkeypatch.setattr(cli, "HOME", tmp_path)
    monkeypatch.setattr(rev_config, "RANDOM_PATHS", 10)
    monkeypatch.setattr(publish, "ensure_repo", lambda: None)
    monkeypatch.setattr(publish, "publish_rev", lambda files, **k: calls["published"].append(dict(files)) or "sha1")
    monkeypatch.setattr(cloud, "heartbeat", lambda *a, **k: None)
    monkeypatch.setattr(cloud, "set_data_sha", lambda *a, **k: None)
    monkeypatch.setattr(cloud, "read_status", lambda: {"pln": {"rejected": {"QAR": "historia krótsza niż 10 lat"}}})
    monkeypatch.setattr(ready, "load_pln", lambda folder: pln)
    monkeypatch.setattr(cli, "log", lambda m: calls["logs"].append(m))
    real_rr, real_live = rev_research.run_research, rev_live.live_step

    def rr(*a, **k):
        calls["research"] += 1
        return real_rr(*a, **k)

    def live(*a, **k):
        calls["live"] += 1
        return real_live(*a, **k)

    monkeypatch.setattr(rev_research, "run_research", rr)
    monkeypatch.setattr(rev_live, "live_step", live)
    return calls, repo, tmp_path


def test_handle_rev_runs_research_when_missing(env, monkeypatch):
    calls, repo, home = env
    monkeypatch.setattr(cli, "cloud_active", lambda *a: True)          # portfel liczy Actions
    cli.handle_rev({})
    assert calls["research"] == 1 and calls["live"] == 0
    runs = list((home / "rev" / "research").iterdir())
    assert len(runs) == 1 and (runs[0] / "research.json").exists() and (runs[0] / "report.md").exists()
    res = json.loads((runs[0] / "research.json").read_text())
    assert res["rejected"] == {"QAR": "historia krótsza niż 10 lat"} and res["oos_openings"] == 1
    assert set(calls["published"][0]) == {"research.json", "report.md"}
    assert json.loads((home / "oos_ledger.json").read_text())[0]["kind"] == "rev"


def test_handle_rev_skips_when_current(env, monkeypatch):
    calls, repo, home = env
    (repo / "rev" / "research.json").write_text(json.dumps({"rev_version": rev_config.REV_VERSION}))
    monkeypatch.setattr(cli, "cloud_active", lambda *a: True)
    cli.handle_rev({})
    assert calls["research"] == 0


def test_handle_rev_no_data_logs_hint(env, monkeypatch):
    calls, repo, home = env
    monkeypatch.setattr(ready, "load_pln", lambda folder: {})
    cli.handle_rev({})
    assert any("backfillPLN" in m for m in calls["logs"]) and not calls["published"]


def test_handle_rev_without_research(env):
    calls, repo, home = env
    cli.handle_rev({}, source="actions")
    assert calls["research"] == 0 and calls["live"] == 0 and not calls["published"]


def test_handle_rev_live_publishes_state(env, monkeypatch):
    calls, repo, home = env
    monkeypatch.setattr(cli, "cloud_active", lambda *a: True)
    cli.handle_rev({})                                                   # Mac: badanie
    (repo / "rev" / "research.json").write_text(calls["published"][0]["research.json"])
    cli.handle_rev({}, source="actions")                                 # Actions: portfel
    st = json.loads(calls["published"][-1]["state.json"])
    assert st["start_ts"] > 0 and st["method"]["id"]
    assert calls["live"] == 1


def test_mac_skips_live_when_actions_fresh(env):
    calls, repo, home = env
    (repo / "rev" / "research.json").write_text(json.dumps({"rev_version": rev_config.REV_VERSION}))
    (repo / "alerts").mkdir()
    (repo / "alerts" / "run.json").write_text(json.dumps({"at": int(time.time()) - 600, "source": "actions"}))
    cli.handle_rev({})
    assert calls["live"] == 0
    assert any("GitHub Actions" in m for m in calls["logs"])


def test_publish_rev_ignores_computed_at(monkeypatch, tmp_path):
    monkeypatch.setattr(publish, "DATA_REPO", tmp_path)
    monkeypatch.setattr(publish, "ensure_repo", lambda: None)
    monkeypatch.setattr(publish, "_git", lambda *a, **k: "abc1234")
    monkeypatch.setattr(publish, "_push", lambda *a, **k: None)
    a = json.dumps({"x": 1, "computedAt": 1})
    b = json.dumps({"x": 1, "computedAt": 2})
    assert publish.publish_rev({"state.json": a}, log=lambda m: None) == "abc1234"
    assert publish.publish_rev({"state.json": b}, log=lambda m: None) is None
    assert publish.publish_rev({"state.json": json.dumps({"x": 2})}, log=lambda m: None) == "abc1234"


def test_failed_publish_does_not_reopen_oos(env, monkeypatch):
    """Przegląd: badanie policzone, publikacja padła — następny przebieg bierze badanie z Maca, bez drugiego otwarcia OOS."""
    calls, repo, home = env
    monkeypatch.setattr(cli, "cloud_active", lambda *a: True)
    cli.handle_rev({})
    assert calls["research"] == 1
    cli.handle_rev({})                                   # na gałęzi data nadal brak research.json
    assert calls["research"] == 1
    assert len(json.loads((home / "oos_ledger.json").read_text())) == 1
    assert "research.json" in calls["published"][-1]


def test_live_waits_when_code_version_differs(env):
    calls, repo, home = env
    (repo / "rev" / "research.json").write_text(json.dumps({"rev_version": "0", "frozen": {"code_hash": "x"}}))
    cli.handle_rev({}, source="actions")
    assert calls["live"] == 0 and any("czeka na nowe badanie" in m for m in calls["logs"])
