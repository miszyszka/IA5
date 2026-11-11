"""REV (D-063): turniej 13 wariantów — odcinki stałe, wybór tylko na IS, walidacja, werdykt, raport, dziennik OOS."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5 import rev_research as rr
from ia5.rev_method import eligible

CODES = ["EUR", "USD", "CHF", "GBP", "JPY", "NOK", "SEK", "CZK", "HUF", "AUD"]
NOW = int(pd.Timestamp("2026-11-11 12:00", tz="UTC").timestamp())


@pytest.fixture(scope="module")
def ready():
    from rev_fixtures import synthetic_ready

    return synthetic_ready(CODES, start="2004-01-01", end="2026-11-10", seed=21)


@pytest.fixture(scope="module")
def research(ready):
    return rr.run_research(ready, CODES, None, NOW, paths=50, log=lambda m: None)


def test_periods_split_and_fixed():
    times = np.arange(600, dtype="int64") * 7 * 86400 + 1_000_000_000
    prices = pd.DataFrame(1.0, index=times, columns=[f"C{i}" for i in range(9)] + ["PLN"])
    elig = eligible(prices)
    p = rr.periods(times, elig)
    start, is_end, end = p["rows"]
    assert start == 260 and end == 599
    assert p["is_weeks"] == int(np.floor(0.75 * p["weeks"]))
    longer = np.arange(700, dtype="int64") * 7 * 86400 + 1_000_000_000
    q = rr.periods(longer, eligible(pd.DataFrame(1.0, index=longer, columns=prices.columns)), p)
    assert (q["start_ts"], q["is_end_ts"], q["oos_end_ts"]) == (p["start_ts"], p["is_end_ts"], p["oos_end_ts"])


def test_research_shape(research):
    r = research
    assert len(r["variants"]) == 13 and r["winner"] in {v["id"] for v in r["variants"]}
    assert r["frozen"]["code_hash"] == rr.code_hash() and r["frozen"]["id"] == r["winner"]
    assert r["validation"]["dsr"]["trials"] == 13
    assert 0 <= r["validation"]["random_pct"] <= 100
    ts = r["history"]["ts"]
    assert all(a < b for a, b in zip(ts, ts[1:])) and len(ts) == len(r["history"]["winner"]) == len(r["history"]["equal"])
    assert r["universe"][-1] == "PLN"
    s = json.dumps(r, allow_nan=False)
    assert "NaN" not in s
    assert r["verdict"]["color"] in ("green", "yellow", "red")


def test_winner_on_is_only(ready, research):
    """Zmiana cen po pierwszym tygodniu OOS nie zmienia zwycięzcy ani żadnej miary IS (wybór tylko na IS — W1, R5)."""
    p = research["periods"]
    cut = p["is_end_ts"] + 8 * 86400
    rng = np.random.default_rng(5)
    alt = {}
    for c, df in ready.items():
        d = df.copy()
        late = d["close_ts"] > cut
        d.loc[late, "close"] = d.loc[late, "close"] * np.exp(np.cumsum(rng.normal(0.002, 0.02, int(late.sum()))))
        alt[c] = d
    again = rr.run_research(alt, CODES, research, NOW, paths=10, log=lambda m: None)
    assert again["periods"]["is_end_ts"] == p["is_end_ts"]
    assert again["winner"] == research["winner"]
    for a, b in zip(research["variants"], again["variants"]):
        assert a["is"] == b["is"], a["id"]


def test_verdict_rules():
    good = {"oos_excess_pct": 1.0, "random_pct": 97.0, "dsr": 0.97, "pbo": 0.1, "lag_excess_pct": 0.5}
    assert rr.verdict(good)["color"] == "green" and rr.verdict(good)["passed"] == 5
    assert rr.verdict({**good, "dsr": 0.9})["color"] == "yellow"
    assert rr.verdict({**good, "dsr": 0.9})["passed"] == 4
    assert rr.verdict({**good, "oos_excess_pct": -0.1})["color"] == "red"
    assert rr.verdict({**good, "random_pct": 70.0})["color"] == "red"
    assert rr.verdict({**good, "pbo": None})["color"] == "yellow"


def test_ledger_counts_rev_openings(tmp_path, research):
    (tmp_path / "oos_ledger.json").write_text(json.dumps([{"kind": "search", "oos_from": 1, "oos_to": 2}]))
    assert rr.ledger_add(tmp_path, research) == 1
    assert rr.ledger_add(tmp_path, research) == 2
    rows = json.loads((tmp_path / "oos_ledger.json").read_text())
    assert [r["kind"] for r in rows] == ["search", "rev", "rev"]


def test_report_has_sections(research):
    md = rr.report_md(research)
    for h in ("## Odcinki", "## Warianty", "## Walidacja", "## Werdykt", "## Ograniczenia", "## Lata"):
        assert h in md
    assert research["winner"] in md


def test_block_bootstrap_contains_mean():
    x = np.random.default_rng(1).normal(0.001, 0.01, 400)
    ci = rr.block_bootstrap_ci(x)
    assert ci["low"] < x.mean() < ci["high"]


def test_windows52():
    r = pd.Series(np.full(104, 0.01))
    e = pd.Series(np.full(104, 0.02))
    w = rr.windows52(r, e)
    assert w["up"] == 100 and w["beat"] == 0 and w["n"] == 53
