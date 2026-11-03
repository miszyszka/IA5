"""D-044: głębokie poszukiwanie — ten sam model co silnik, OOS zamknięty do etapu 3, strategia zgodna z kontraktem."""
import numpy as np
import pandas as pd
import pytest
from ia5 import engine, search
from ia5 import indicators as ind
from ia5 import search_rules as R
from ia5.check import check_code_on
from ia5.sandbox import lookahead_cuts

T0 = 1735516800  # poniedziałek 2024-12-30 00:00 UTC


def synth(n=9000, seed=0, p0=1.1, pip=0.0001, drift_after_up=0.0):
    """Świece tylko w dni robocze; opcjonalnie podłożony efekt: po 4 wzrostach z rzędu cena rośnie przez 8 świec."""
    rng = np.random.default_rng(seed)
    ts = T0 + 3600 * np.arange(int(n * 1.45))
    wd = pd.to_datetime(ts, unit="s", utc=True).dayofweek
    ts = ts[wd < 5][:n]
    r = rng.normal(0, 12 * pip, n)
    if drift_after_up:
        run, boost = 0, 0
        for i in range(1, n):
            if boost:
                r[i] += drift_after_up * pip
                boost -= 1
            run = run + 1 if r[i] > 0 else 0
            if run == 4:
                boost = 8
    c = p0 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]] + rng.normal(0, pip, n)
    h = np.maximum(o, c) + rng.random(n) * 6 * pip
    lo = np.minimum(o, c) - rng.random(n) * 6 * pip
    return pd.DataFrame({"ts": ts, "open": o, "high": h, "low": lo, "close": c})


def frames(k=2, **kw):
    pairs = [("EURUSD", 1.1, 0.0001), ("USDJPY", 150.0, 0.01), ("GBPUSD", 1.3, 0.0001), ("AUDUSD", 0.66, 0.0001)]
    return {p: synth(seed=i, p0=p0, pip=pip, **kw) for i, (p, p0, pip) in enumerate(pairs[:k])}


TINY = {
    "trig": {"donchian": {"n": [24, 48]}, "seria": {"n": [3, 4]}, "rsi": {"n": [2], "lvl": [10]}},
    "exits": [engine.Exit("time", n=8, cap=8), engine.Exit("atr", n=14, tp=2, sl=1, cap=120),
              engine.Exit("trail", n=14, sl=2, trail=3, cap=480)],
    "filters": {"trend": ["brak", "zgodny_ema200"], "zmiennosc": ["brak", "ruch"], "sesja": ["07-17", "10-13"],
                "dni": ["pn-pt"], "kierunek": ["oba", "long"]},
}


@pytest.fixture
def tiny(monkeypatch):
    monkeypatch.setattr(search, "grid", lambda size="duzy": TINY)


def engine_trades(fr, cfg):
    """Ten sam config policzony zwykłym silnikiem (engine.run) na sygnałach z config_signal."""
    h1, sig = {}, {}
    for p, raw in fr.items():
        df = search.frame_index(raw)
        df.attrs["pair"] = p
        h1[p] = raw
        sig[(0, p)] = R.config_signal(df, ind, cfg).astype(np.float32)
    res = engine.run(h1, sig, [{}], exits=[cfg["exit"]])
    if res["outcomes"].empty:
        return pd.DataFrame(columns=["pair", "entry_ts", "pips_net", "r_net"])
    o = res["outcomes"].merge(res["entries"][["entry_id", "entry_ts"]], on="entry_id")
    return o.sort_values(["pair", "entry_ts"]).reset_index(drop=True)


@pytest.mark.parametrize("ci", [0, 7, 23, 41, 66, 90])
def test_same_trades_as_engine(tiny, ci):
    fr = frames(2)
    space = search.Space(search.grid())
    cfg = space.config(ci * 7 % space.n)
    cuts = search.cuts_for(fr)
    mine = search.config_trades(fr, cfg, cuts).sort_values(["pair", "entry_ts"]).reset_index(drop=True)
    ref = engine_trades(fr, cfg)
    assert len(mine) == len(ref)
    assert (mine.entry_ts.to_numpy(float) == ref.entry_ts.to_numpy(float)).all()
    np.testing.assert_allclose(mine.pips_net.to_numpy(float), ref.pips_net.to_numpy(float), rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(mine.r_net.to_numpy(float), ref.r_net.to_numpy(float), rtol=1e-9, atol=1e-9)


def test_is_stats_match_full_trades_and_oos_is_sealed(tiny):
    fr = frames(2)
    st = search.is_stage(fr, "duzy", workers=1, log=lambda m: None)
    space, cuts, t = st["space"], st["cuts"], st["table"]
    # etap 1–2 = te same transakcje co pełne liczenie, ograniczone do IS
    for c in t[t.nA + t.nB > 0].cfg.to_numpy()[::37][:5]:
        tr = search.config_trades(fr, space.config(int(c)), cuts)
        a, b = tr[tr.okres == "IS-A"], tr[tr.okres == "IS-B"]
        row = t.loc[c]
        assert (row.nA, row.nB) == (len(a), len(b))
        assert row.rA == pytest.approx(a.r_net.mean(), rel=1e-5) if len(a) else True
    # zmiana cen w OOS (poza ostatnimi świecami IS potrzebnymi do wyjść) nie zmienia niczego w etapach 1–2
    bent = {}
    for p, df in fr.items():
        d = df.copy()
        late = d.ts >= cuts[2] + 3600 * 24 * 30
        for k in ("open", "high", "low", "close"):
            d.loc[late, k] *= 1.07
        bent[p] = d
    t2 = search.is_stage(bent, "duzy", workers=1, log=lambda m: None)["table"]
    pd.testing.assert_frame_equal(t[["nA", "nB", "rA", "rB"]], t2[["nA", "nB", "rA", "rB"]])


def test_full_run_report_and_generated_strategy(tiny, tmp_path):
    fr = frames(2)
    out = search.run(fr, size="duzy", top=4, workers=1, log=lambda m: None, null=1)
    assert out["tested"] == search.Space(TINY).n
    assert len(out["oos"]) == len(out["chosen"]) <= 4
    assert out["oos"].rank_is.tolist() == list(range(1, len(out["oos"]) + 1))   # kolejność IS, nie OOS
    assert len(out["null"]) == 1
    md = search.report(out, ledger_count=1)
    assert "Przetestowane konfiguracje" in md and "Test zerowy" in md
    folder = search.save(out, tmp_path / "run", "test", 1)
    code = (folder / "strategy.py").read_text()
    h1 = tmp_path / "h1"
    h1.mkdir()
    for p, df in fr.items():
        df.to_parquet(h1 / f"{p}.parquet", index=False)
    res = check_code_on(code, h1)
    assert res["ok"], res["errors"]
    # sygnały wygenerowanej strategii = sygnały konfiguracji z poszukiwania
    ns = {}
    exec(compile(code, "s.py", "exec"), ns)  # noqa: S102
    df = search.frame_index(fr["EURUSD"])
    for k, cfg_id in enumerate(out["chosen"].cfg.head(3)):
        cfg = out["space"].config(int(cfg_id))
        assert np.array_equal(ns["signals"](df, {"cfg": k}, ind), R.config_signal(df, ind, cfg))


def test_rules_have_no_lookahead():
    raw = synth(4000, seed=5)
    df = search.frame_index(raw)
    for name, kw in [("wstega", {"s": "5,10,15,25,40"}), ("azja", {"bufor": 0.25}), ("wczoraj", {"bufor": 0.0}),
                     ("scisk", {"x": 0.8, "n": 12}), ("impuls", {"k": 3, "th": 1.0})]:
        cfg = {"trig": name, "kw": kw, "tryb": 1, "trend": "zgodny_sma480", "zmiennosc": "cisza", "sesja": "10-13",
               "dni": "wt-czw", "kierunek": "oba"}
        assert lookahead_cuts(lambda d, p, i, c=cfg: R.config_signal(d, i, c), df, {}, ind) == [], name


def test_null_frames_keep_volatility_and_valid_candles():
    fr = frames(1)
    nf = search.null_frames(fr, seed=3)["EURUSD"]
    a, b = fr["EURUSD"], nf
    assert (b.high >= np.maximum(b.open, b.close) - 1e-12).all() and (b.low <= np.minimum(b.open, b.close) + 1e-12).all()
    ra = np.abs(np.diff(np.log(a.close)))
    rb = np.abs(np.diff(np.log(b.close)))
    np.testing.assert_allclose(ra, rb, rtol=1e-9, atol=1e-12)


def test_finds_planted_effect_but_not_in_noise(monkeypatch):
    g = {"trig": {"seria": {"n": [3, 4, 5]}, "donchian": {"n": [24, 48]}},
         "exits": [engine.Exit("time", n=n, cap=n) for n in (4, 8, 12)],
         "filters": {"trend": ["brak"], "zmiennosc": ["brak"], "sesja": ["07-17"], "dni": ["pn-pt"], "kierunek": ["oba", "long"]}}
    monkeypatch.setattr(search, "grid", lambda size="duzy": g)
    eff = search.run(frames(3, drift_after_up=6), top=3, workers=1, log=lambda m: None)
    best = eff["space"].config(int(eff["chosen"].iloc[0].cfg))
    assert eff["passed"] > 0 and best["trig"] == "seria" and best["tryb"] == 1
    assert (eff["oos"].r_oos.iloc[0]) > 0
    noise = search.run(frames(3), top=3, workers=1, log=lambda m: None, open_oos=False)
    assert noise["passed"] == 0
