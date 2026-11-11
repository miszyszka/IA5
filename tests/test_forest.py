"""FOREST v2 (D-049): inwestorzy milczą, gdy nie mają zdania; progi Managera; nauka co 4 tygodnie; ten sam model co silnik."""

import json

import numpy as np
import pandas as pd
import pytest

from ia5 import engine, forest_manager, forest_report, forest_rules, forest_run
from ia5 import forest as F
from ia5 import forest_manager as M
from ia5.config import PAIRS
from ia5.session import in_trading_hours

H = 3600
PAIRS8 = list(PAIRS)
START = 1600041600 - 1600041600 % (7 * 86400) + 4 * 86400
PX = {"EURUSD": 1.1, "USDJPY": 140.0, "GBPUSD": 1.3, "EURGBP": 0.85, "AUDUSD": 0.7, "USDCHF": 0.9, "USDCAD": 1.3, "EURJPY": 150.0}
N = 9500
QUIET = {"log": lambda m: None}


def candles(n, seed, start, strength=0.0, od=0):
    """Szum; strength > 0 podkłada zależność: ruch z 24 świec trwa dalej (lustrzanie w obie strony)."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, 0.0008, n)
    c = np.zeros(n)
    c[0] = start
    for t in range(1, n):
        mom = np.sign(c[t - 1] - c[max(0, t - 25)]) if strength and t >= od else 0.0
        c[t] = c[t - 1] * (1 + noise[t] + strength * mom)
    o = np.r_[c[0], c[:-1]]
    hi = np.maximum(o, c) * (1 + rng.random(n) * 0.0004)
    lo = np.minimum(o, c) * (1 - rng.random(n) * 0.0004)
    return pd.DataFrame({"ts": START + H * np.arange(n), "open": o, "high": hi, "low": lo, "close": c, "filled": False, "gap_before": 0})


def frames(n=N, seed=1, strength=0.0):
    return {p: candles(n, seed + k, PX[p], strength) for k, p in enumerate(PAIRS8)}


@pytest.fixture(scope="module", autouse=True)
def mala_pula():
    old = M.N_RULES, F.N_RULES
    M.N_RULES = F.N_RULES = 6000
    yield
    M.N_RULES, F.N_RULES = old


@pytest.fixture(scope="module")
def world(mala_pula):
    fr = frames(strength=0.00012)
    g, pn = forest_run.run_all(fr, 5, **QUIET)
    return fr, pn, g


def test_cechy_bez_look_ahead():
    fr = frames(n=1500)
    cut = fr["EURUSD"]["ts"].iloc[1100]
    tr = {p: d[d.ts < cut].reset_index(drop=True) for p, d in fr.items()}
    a = forest_rules.pair_features("GBPUSD", fr["GBPUSD"], forest_rules.currency_panel(fr))
    b = forest_rules.pair_features("GBPUSD", tr["GBPUSD"], forest_rules.currency_panel(tr))
    for k, (_, _, y) in b.items():
        x = a[k][2][: len(y)]
        assert np.allclose(np.nan_to_num(x, nan=-9e9), np.nan_to_num(y, nan=-9e9), atol=1e-4, rtol=1e-4), k


def test_ruch_to_transakcja_silnika():
    raw = frames(n=800)["EURUSD"]
    P = engine.prepare(raw)
    r = F.forward(P)
    sig = np.zeros(len(raw))
    sig[np.arange(100, 700, 7)] = 1
    ent = engine.find_entries(P, sig)
    for k, h in enumerate(F.HORIZONS):
        res = engine.simulate(P, ent, engine.Exit("time", n=h, cap=h), "EURUSD")
        mine = r[ent["signal_i"].to_numpy(), k] * P["atr14"][ent["signal_i"].to_numpy()] / PAIRS["EURUSD"].pip
        assert np.allclose(mine, res["pips_gross"].to_numpy(float), atol=1e-9)


def test_regula_jest_lustrzana():
    conds = [
        {"f": "x", "fam": "trend", "label": "x", "kind": "dir", "e": 1.0, "c": 0.0},
        {"f": "y", "fam": "zmienność", "label": "y", "kind": "flt", "e": 0.5, "c": 0.0},
    ]
    X = np.array([[2.0, 1.0], [-2.0, 1.0], [2.0, 0.0], [0.0, 1.0]])
    U, D = F.condition_masks(X, {"x": 0, "y": 1}, conds)
    b, s = F.rule_masks(U, D, ((0, F.MODE_WITH), (1, F.MODE_GE)))
    assert b.tolist() == [True, False, False, False] and s.tolist() == [False, True, False, False]
    b2, s2 = F.rule_masks(U, D, ((0, F.MODE_AGAINST),))
    assert b2.tolist() == [False, True, False, False] and s2.tolist() == [True, False, True, False]
    assert "x ≥ 1" in F.rule_text(((0, F.MODE_WITH),), conds)


def test_inwestorzy_milcza_gdy_nie_maja_zdania(world):
    _, _, g = world
    df = g.frame()
    assert len(df) > 200
    las = max(len(x["investors"]) for x in g.fr["generations"])
    assert (df["n"] == df["up"] + df["dn"]).all() and (df["n"] > 0).all()
    assert (df["n"] < las).mean() > 0.9  # zwykle mówi tylko część lasu
    assert (df["voters"].str.split(",").str.len() == df["n"]).all()


def test_progi_managera():
    t = {"n": 4, "dir": 1, "cons": 1.0}
    assert M.Manager.verdict(t) == "few"
    assert M.Manager.verdict({"n": 20, "dir": 1, "cons": 0.7}) == "split"
    assert M.Manager.verdict({"n": 20, "dir": 0, "cons": 0.5}) == "split"
    assert M.Manager.verdict({"n": M.QUORUM, "dir": -1, "cons": M.CONSENSUS}) == "go"


def test_manager_wchodzi_tylko_powyzej_progow(world):
    _, _, g = world
    df = g.frame()
    x = df[df["ex_m"]]
    assert len(x) and (x["n"] >= M.QUORUM).all() and (x["cons"] >= M.CONSENSUS).all()
    assert (df.loc[df["why"] == "few", "n"] < M.QUORUM).all()
    assert not df.loc[df["why"].isin(["few", "split", "busy"]), "ex_m"].any()


def test_decyzje_nie_znaja_przyszlosci(world):
    fr, pn, g = world
    t = pn.t0 + (F.START_WEEKS + 2 * F.REFRESH_WEEKS) * F.WEEK
    other = {}
    for p, d in fr.items():
        d2 = d.copy()
        m = d2.ts > t
        for c in ("open", "high", "low", "close"):
            d2.loc[m, c] = d2.loc[m, c] * (1 + 0.01 * np.sin(np.arange(m.sum())))
        other[p] = d2
    g2, _ = forest_run.run_all(other, 5, **QUIET)
    a, b = g.frame(), g2.frame()
    a, b = a[a.ts < t].reset_index(drop=True), b[b.ts < t].reset_index(drop=True)
    assert len(a) > 50
    for c in ("n", "up", "dn", "dir", "h", "why", "ex_m", "ex_k", "voters"):
        pd.testing.assert_series_equal(a[c], b[c], check_names=False)
    assert [i["rule"] for i in g.fr["generations"][1]["investors"]] == [i["rule"] for i in g2.fr["generations"][1]["investors"]]


def test_nauka_co_cztery_tygodnie(world):
    _, pn, g = world
    gens = g.fr["generations"]
    assert len(gens) >= 3 and all(b["week"] - a["week"] == F.REFRESH_WEEKS for a, b in zip(gens, gens[1:]))
    assert any(x["added"] or x["retired"] for x in gens[1:])


def test_las_zroznicowany(world):
    _, pn, g = world
    cube = F.Cube(pn, g.pool(), g.fr["conds"], log=lambda m: None)
    gen = g.fr["generations"][-1]
    tr = np.flatnonzero(cube.wk < gen["week"] - 1)[::3]
    v = []
    for i in gen["investors"][:60]:
        b, s = F.rule_masks(cube.U, cube.D, g.pool()[i["rule"]], tr)
        v.append(b.astype(float) - s)
    c = np.corrcoef(np.array(v))
    np.fill_diagonal(c, 0)
    assert np.abs(np.nan_to_num(c)).max() <= F.RHO_CAP + 0.02


def test_transakcje_jak_silnik(world):
    fr, pn, g = world
    df = g.frame()
    last = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    for b in M.BOOKS:
        t = forest_report.trades(df, df[f"ex_{b}"].to_numpy(bool), last)
        t = t[t.status == "zamknięta"]
        assert len(t) > 5
        for pair, part in t.groupby("pair"):
            P = pn.P[pair]
            i = np.searchsorted(P["ts"], part["ts"].to_numpy())
            sig = np.zeros(len(P["ts"]))
            sig[i] = part["dir"].to_numpy()
            ent = engine.find_entries(P, sig)
            ent["max_bars"] = part["h"].to_numpy()
            res = engine.simulate(P, ent, engine.Exit("time", n=48, cap=48), pair)
            assert np.allclose(res["pips_gross"].to_numpy(float), part["gross"].to_numpy(float), atol=1e-6)
            assert (i[1:] + 1 > res["exit_i"].to_numpy()[:-1]).all()  # B8
        assert in_trading_hours(t["entry_ts"].to_numpy(int)).all()


def test_nadrabianie_daje_ten_sam_wynik(world, tmp_path):
    _, pn, g = world
    a = M.Manager(json.loads(json.dumps({**g.fr, "generations": []})))
    a.advance(pn, until=pn.t0 + (F.START_WEEKS + 7) * F.WEEK, **QUIET)
    a.save(tmp_path / "current")
    b = M.Manager.load(tmp_path / "current")
    b.advance(pn, **QUIET)
    pd.testing.assert_frame_equal(g.frame(), b.frame(), check_dtype=False)
    assert [x["week"] for x in g.fr["generations"]] == [x["week"] for x in b.fr["generations"]]


def test_publikacja(world, tmp_path):
    _, pn, g = world
    st = forest_report.write_public(g, pn, tmp_path / "public", now=1800000000)
    bad = lambda x: pytest.fail(x)  # noqa: E731
    s = json.loads((tmp_path / "public" / "state.json").read_text(encoding="utf-8"), parse_constant=bad)
    assert len(s["now"]) == 8 and s["params"]["QUORUM"] == M.QUORUM and s["grid"]
    assert {"why", "n", "up", "dn"} <= set(s["now"][0])
    inv = json.loads((tmp_path / "public" / "investors.json").read_text(encoding="utf-8"), parse_constant=bad)
    assert sum(i["aktywny"] for i in inv["investors"]) == len(g.fr["generations"][-1]["investors"]) and inv["investors"][0]["rule"]
    j = pd.concat(pd.read_parquet(f) for f in sorted((tmp_path / "public" / "journal").glob("*.parquet")))
    assert len(j) == st["counts"]["decyzje"] and {"voters", "why", "cons", "g24", "g48", "usd"} <= set(j.columns)


def test_pusty_las(world):
    _, pn, g = world
    fr = {**g.fr, "generations": []}
    st, _ = forest_report.build_state(M.Manager(fr), pn, now=1800000000)
    assert st["counts"]["decyzje"] == 0 and st["conclusions"] == [] and len(st["now"]) == 8
    json.dumps(st, allow_nan=False)


def test_budowa_krok_i_stary_las(tmp_path):
    fr = frames()
    cut = fr["EURUSD"]["ts"].iloc[-30]
    early = {p: d[d.ts <= cut].reset_index(drop=True) for p, d in fr.items()}
    (tmp_path / "current").mkdir()
    (tmp_path / "current" / "forest.json").write_text('{"version": "1.0", "id": "stary"}')
    assert not forest_run.exists(tmp_path)
    st = forest_run.build(early, root=tmp_path, zero=1, ledger=tmp_path, **QUIET)
    assert forest_run.exists(tmp_path) and (tmp_path / "archive" / "stary" / "forest.json").exists()
    assert st["zero"][0]["seed"] == 1000
    st2, made = forest_run.step(fr, root=tmp_path, **QUIET)
    assert st2["counts"]["decyzje"] == st["counts"]["decyzje"] + made
    df = pd.read_parquet(tmp_path / "current" / "journal.parquet")
    assert (df["seg"] == "LIVE").sum() == made
    assert json.loads((tmp_path / "oos_ledger.json").read_text())[0]["kind"] == "forest2"


def test_null_zachowuje_ruchy_i_korelacje():
    fr = frames(n=800)
    nf = F.null_blocks(fr, 3)
    for p in ("EURUSD", "GBPUSD"):
        a = np.abs(np.log(fr[p].close / fr[p].close.shift(1))).to_numpy()[1:]
        b = np.abs(np.log(nf[p].close / nf[p].close.shift(1))).to_numpy()[1:]
        assert np.allclose(a, b, atol=1e-9)
    day = (nf["EURUSD"].ts.to_numpy() - START) // (24 * H)
    sa = np.sign(np.log(nf["EURUSD"].close / fr["EURUSD"].close))
    assert len(np.unique(day)) > 20 and sa.notna().all()


def test_kontrola_pozytywna_i_szum():
    """Gdy rynek ma zależność, reguły przechodzą bramki i Manager zarabia; na szumie bramki przechodzi niewiele."""
    g, pn = forest_run.run_all(frames(strength=0.00012), 5, **QUIET)
    df = g.frame()
    px = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    t = forest_report.trades(df, df["ex_m"].to_numpy(bool), px)
    t = t[t.status == "zamknięta"]
    g0, _ = forest_run.run_all(frames(seed=31), 5, **QUIET)
    p1 = np.mean([x["passed"] for x in g.fr["generations"]])
    p0 = np.mean([x["passed"] for x in g0.fr["generations"]])
    assert p1 > 5 * max(1, p0)
    assert len(t) > 50 and t.pips_net.mean() > 3


def test_ia5_start_buduje_i_liczy(monkeypatch):
    from ia5 import cli, cloud, publish, ready

    beats, calls = [], []
    st = {"counts": {"decyzje": 5, "las": 2}, "books": {"m": {"name": "Manager", "equity": 10000.0}}}
    monkeypatch.setattr(cloud, "heartbeat", lambda s, job=None: beats.append(s))
    monkeypatch.setattr(ready, "load", lambda d: {})
    monkeypatch.setattr(publish, "publish_forest", lambda p, log=print: calls.append("publikacja"))
    monkeypatch.setattr(forest_run, "exists", lambda: False)
    monkeypatch.setattr(forest_run, "build", lambda f, log=print, ledger=None: calls.append("budowa") or st)
    monkeypatch.setattr(forest_run, "step", lambda f, log=print: calls.append("krok") or (st, 3))
    state = {"now": "idle"}
    cli.handle_forest(state)
    assert calls == ["budowa", "publikacja"] and state == {"now": "idle", "job": None}
    calls.clear()
    monkeypatch.setattr(forest_run, "exists", lambda: True)
    cli.handle_forest(state)
    assert calls == ["krok", "publikacja"]
    assert forest_manager.BOOKS["m"] == "Manager"
