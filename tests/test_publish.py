"""Publikacja wyników i usuwanie strategii na gałęzi data — na lokalnym repo zamiast GitHub."""
import json
import subprocess

import pytest
from ia5 import publish


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    monkeypatch.setattr(publish, "DATA_REPO", tmp_path / "data-repo")
    monkeypatch.setattr(publish, "REPO_URL", str(bare))
    return bare


def fake_result(tmp_path, sid, name):
    d = tmp_path / "res" / sid
    d.mkdir(parents=True)
    (d / "manifest.json").write_text(json.dumps({"id": sid, "name": name, "run_id": "r1", "created": 1, "n_variants": 233,
                                                 "pairs": ["EURUSD"], "data_from": 0, "data_to": 1, "data_source": "x",
                                                 "engine_version": "0"}))
    (d / "validation.json").write_text(json.dumps({"verdict": {"color": "red", "note": "n"}, "best_exit": "e"}))
    return d


def ls_remote_files(bare):
    out = subprocess.run(["git", "--git-dir", str(bare), "ls-tree", "-r", "--name-only", "data"],
                         capture_output=True, text=True, check=True).stdout
    return set(out.split())


def test_publish_then_delete(repo, tmp_path):
    publish.publish_result(fake_result(tmp_path, "a", "A"), log=lambda m: None)
    publish.publish_result(fake_result(tmp_path, "b", "B"), log=lambda m: None)
    files = ls_remote_files(repo)
    assert {"results/a/manifest.json", "results/b/manifest.json", "results/index.json"} <= files
    idx = json.loads((publish.DATA_REPO / "results" / "index.json").read_text())
    assert [e["id"] for e in idx["strategies"]] and {e["id"] for e in idx["strategies"]} == {"a", "b"}

    publish.delete_result("a", log=lambda m: None)
    files = ls_remote_files(repo)
    assert "results/a/manifest.json" not in files and "results/b/manifest.json" in files
    idx = json.loads((publish.DATA_REPO / "results" / "index.json").read_text())
    assert [e["id"] for e in idx["strategies"]] == ["b"]
    assert publish.delete_result("nie-ma", log=lambda m: None) is None


def test_publish_coverage_only_when_changed(repo):
    cov = {"v": 1, "generated": 1, "sources": {"dukascopy": {"pairs": {"EURUSD": {"m": [[1, 120, 118, 2, 0, 0]], "gaps": []}}}}}
    assert publish.publish_coverage(cov, log=lambda m: None)
    assert "coverage/coverage.json" in ls_remote_files(repo)
    # inny znacznik czasu, ta sama treść → bez nowego commitu
    assert publish.publish_coverage({**cov, "generated": 2}, log=lambda m: None) is None
    cov["sources"]["dukascopy"]["pairs"]["EURUSD"]["m"][0][2] = 120
    assert publish.publish_coverage(cov, log=lambda m: None)


def fake_investor(iid, eq=10_000.0, at=1):
    return {"id": iid, "name": iid.upper(), "capital": 10_000.0, "pct": 5.0, "start": 0, "computedAt": at, "dataTo": 10,
            "equity": {"now": eq, "return_pct": 0.0}, "counts": {"closed": 0, "open": 0}, "strategies": [{"name": "S"}],
            "trades": [], "curve": {"ts": [0], "equity": [10_000.0]}}


def test_publish_investors_add_update_remove(repo):
    """D-045: stan inwestorów na gałęzi data; bez zmian treści — bez commita; usunięty znika z gałęzi i indeksu."""
    q = lambda m: None  # noqa: E731
    assert publish.publish_investors({"a": fake_investor("a"), "b": fake_investor("b")}, [], log=q)
    files = ls_remote_files(repo)
    assert {"investors/a/state.json", "investors/b/state.json", "investors/index.json"} <= files
    assert publish.publish_investors({"a": fake_investor("a", at=99), "b": fake_investor("b", at=99)}, [], log=q) is None
    assert publish.publish_investors({"a": fake_investor("a", eq=10_500.0)}, ["b"], log=q)
    files = ls_remote_files(repo)
    assert "investors/b/state.json" not in files
    idx = json.loads((publish.DATA_REPO / "investors" / "index.json").read_text())
    assert [(e["id"], e["equity"]) for e in idx["investors"]] == [("a", 10_500.0)]


def test_publish_forest_tylko_zmiany(tmp_path, monkeypatch):
    """Sam nowy czas liczenia nie jest zmianą; miesiąc, którego już nie ma, znika z gałęzi."""
    import json as js

    from ia5 import publish as pb

    commits = []
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(pb, "DATA_REPO", repo)
    monkeypatch.setattr(pb, "ensure_repo", lambda: None)
    monkeypatch.setattr(pb, "_git", lambda *a, check=True: commits.append(a) or "abc1234")
    src = tmp_path / "public"
    (src / "journal").mkdir(parents=True)
    (src / "state.json").write_text(js.dumps({"computedAt": 1, "id": "x"}))
    (src / "journal" / "2026-11.parquet").write_bytes(b"a")
    assert pb.publish_forest(src, log=lambda m: None) == "abc1234"
    n = len(commits)
    (src / "state.json").write_text(js.dumps({"computedAt": 2, "id": "x"}))
    assert pb.publish_forest(src, log=lambda m: None) is None and len(commits) == n
    (src / "journal" / "2026-11.parquet").unlink()
    (src / "journal" / "2026-12.parquet").write_bytes(b"b")
    assert pb.publish_forest(src, log=lambda m: None) == "abc1234"
    assert sorted(f.name for f in (repo / "forest" / "journal").iterdir()) == ["2026-12.parquet"]
