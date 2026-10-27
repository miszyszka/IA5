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
