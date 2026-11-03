"""FOREST (D-048): zawsze jest zdanie, zero zaglądania w przyszłość, ten sam model co silnik, nadrabianie, kontrola pozytywna."""

import json

import numpy as np
import pandas as pd
import pytest
from ia5 import engine, forest_report, forest_rules, forest_run
from ia5 import forest as F
from ia5 import forest_manager as M
from ia5.config import PAIRS

H = 3600
PAIRS8 = list(PAIRS)
START = 1600041600 - 1600041600 % (7 * 86400) + 4 * 86400  # poniedziałek 00:00 UTC


def candles(n, seed, start=1.1, drift=None):
    rng = np.random.default_rng(seed)
    step = rng.normal(0, 0.0008, n) * start
    if drift is not None:
        step = step + drift
    c = start + np.cumsum(step)
    o = np.r_[c[0], c[:-1]]
    hi = np.maximum(o, c) + rng.random(n) * 0.0006 * start
    lo = np.minimum(o, c) - rng.random(n) * 0.0006 * start
    return pd.DataFrame({"ts": START + H * np.arange(n), "open": o, "high": hi, "low": lo, "close": c, "filled": False, "gap_before": 0})


def frames(n=4200, seed=1):
    px = {"EURUSD": 1.1, "USDJPY": 140.0, "GBPUSD": 1.3, "EURGBP": 0.85, "AUDUSD": 0.7, "USDCHF": 0.9, "USDCAD": 1.3, "EURJPY": 150.0}
    return {p: candles(n, seed + k, px[p]) for k, p in enumerate(PAIRS8)}


@pytest.fixture(scope="module")
def world():
    fr = frames()
    pn = F.Panel(fr)
    las = F.forge(fr, n_candidates=3000, n_investors=60, workers=1, log=lambda m: None, pn=pn)
    g = M.Manager(las)
    g.advance(pn, log=lambda m: None)
    return fr, pn, las, g


def test_cechy_bez_look_ahead():
    fr = frames(n=1500)
    cut = fr["EURUSD"]["ts"].iloc[1100]
    tr = {p: d[d.ts < cut].reset_index(drop=True) for p, d in fr.items()}
    a = forest_rules.pair_features("GBPUSD", fr["GBPUSD"], forest_rules.currency_panel(fr))
    b = forest_rules.pair_features("GBPUSD", tr["GBPUSD"], forest_rules.currency_panel(tr))
    assert len(a) >= 130
    for k, (_, _, y) in b.items():
        x = a[k][2][: len(y)]
        assert np.allclose(np.nan_to_num(x, nan=-9e9), np.nan_to_num(y, nan=-9e9), atol=1e-4, rtol=1e-4), k


def test_ruch_to_transakcja_silnika():
    """r[t, h] = wejście na open t+1, wyjście na zamknięciu t+h — to samo co Exit("time", n=h, cap=h)."""
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


def test_przerwa_i_swieca_uzupelniona_anuluja():
    raw = frames(n=800)["EURUSD"].copy()
    raw.loc[300, "filled"] = True
    raw.loc[500, "gap_before"] = 6
    r = F.forward(engine.prepare(raw))
    assert np.isnan(r[297, 2])  # wyjście na świecy uzupełnionej
    assert np.isnan(r[299, 0])  # wejście na świecy uzupełnionej
    assert np.isnan(r[497, 4])  # przerwa w trakcie
    assert np.isfinite(r[290, 4])


def test_zawsze_jest_zdanie(world):
    _, _, las, g = world
    df = g.frame()
    assert len(df) > 500
    assert (df["buy"] + df["sell"] == g.forest.m).all()
    assert df["dir"].isin([1, -1]).all()
    assert df["h"].between(1, 5).all()
    for k in range(5):
        assert df[f"f{k + 1}"].notna().all()
    assert all(len(i["table"]) == 1 << len(i["tests"]) for i in las["investors"])
    assert all(np.asarray(i["table"]).shape[1] == 5 for i in las["investors"])


def test_inwestorzy_naprawde_sie_roznia(world):
    _, pn, las, _ = world
    f = M.Forest(las)
    sample = F.forge_sample(pn, las["cuts"]["forge"])[::2]
    cols = F.test_columns(pn.X[sample], pn.col, las["tests"])
    v = np.array([f.vote(cols[:, k])[1] for k in range(len(sample))]).T
    c = np.corrcoef(v.astype(float))
    np.fill_diagonal(c, 0)
    assert np.abs(c).max() <= F.RHO_CAP + 0.05  # próbka parzysta tych samych świec i pełne tablice
    assert las["forge"]["n_eff"] > 5
    assert len({tuple(i["tests"]) for i in las["investors"]}) == len(las["investors"])


def test_las_liczony_tylko_na_kuciu():
    """Zmiana świec po granicy kucia nie zmienia ani jednego inwestora."""
    fr = frames()
    a = F.forge(fr, n_candidates=1500, n_investors=30, workers=1, log=lambda m: None)
    cut = a["cuts"]["forge"]
    other = {}
    for p, d in fr.items():
        d2 = d.copy()
        m = d2.ts >= cut + 12 * H
        for c in ("open", "high", "low", "close"):
            d2.loc[m, c] = d2.loc[m, c] * 1.02
        other[p] = d2
    b = F.forge(other, n_candidates=1500, n_investors=30, workers=1, log=lambda m: None)
    assert a["id"] == b["id"]


def test_decyzje_nie_znaja_przyszlosci(world):
    """Zmiana cen po chwili T nie zmienia żadnej decyzji ani dopasowania do map sprzed T."""
    fr, pn, las, g = world
    t = las["cuts"]["oos"]
    other = {}
    for p, d in fr.items():
        d2 = d.copy()
        m = d2.ts > t
        for c in ("open", "high", "low", "close"):
            d2.loc[m, c] = d2.loc[m, c] * (1 + 0.01 * np.sin(np.arange(m.sum())))
        other[p] = d2
    pn2 = F.Panel(other)
    g2 = M.Manager(las)
    g2.advance(pn2, log=lambda m: None)
    a, b = g.frame(), g2.frame()
    a, b = a[a.ts < t - 8 * H], b[b.ts < t - 8 * H]
    assert len(a) > 100
    for c in ("buy", "dir", "h", "w", "l", "z", "z_b", "h_b", "take_b", "dir_c", "h_c", "maps", "ex_a", "ex_b", "ex_c"):
        pd.testing.assert_series_equal(a[c].reset_index(drop=True), b[c].reset_index(drop=True), check_names=False)


def test_pamiec_map_tylko_zamkniete(world):
    _, _, _, g = world
    df = g.frame()
    closes = np.sort(df["xt5"].dropna().to_numpy())
    for r in df.iloc[::50].itertuples():
        # map w pamięci nie może być więcej niż decyzji zamkniętych przed chwilą tej decyzji
        assert r.maps <= np.searchsorted(closes, r.ts + H, side="right")


def test_punkty_mapy_za_i_przeciw(world):
    """Zysk: obóz za +1, przeciw −1. Strata odwrotnie. Punkty inwestora to suma jego map."""
    _, _, _, g = world
    df = g.frame()
    bits = np.array(g.bits)
    closed = df[(df.known == 5) & (df.pkt != 0)]
    pos, neg = np.zeros(g.forest.m, int), np.zeros(g.forest.m, int)
    for r in closed.itertuples():
        a = np.where(g.forest.unpack(bits[r.seq]), 1, -1) * r.dir
        if r.pkt > 0:
            pos += a
        else:
            neg += a
    assert (pos == g.pos).all() and (neg == g.neg).all()
    h, d = closed["h"].to_numpy(), closed["dir"].to_numpy()
    g_ = closed[[f"g{x}" for x in F.HORIZONS]].to_numpy()
    net = d * g_[np.arange(len(h)), h - 1] - closed["spread"].to_numpy()
    assert ((net > 0) == (closed["pkt"].to_numpy() > 0)).all()


def test_ksiegi_ten_sam_model_co_silnik(world):
    """Każda transakcja każdej księgi = engine.simulate co do pipsa; B8: bez nakładania; B11: wejścia w oknie."""
    fr, pn, _, g = world
    df = g.frame()
    last = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    for b in M.BOOKS:
        t = forest_report.book_trades(df, b, last)
        t = t[t.status == "zamknięta"]
        assert len(t) > 20
        for pair, part in t.groupby("pair"):
            P = pn.P[pair]
            i = np.searchsorted(P["ts"], part["signal_ts"].to_numpy())
            sig = np.zeros(len(P["ts"]))
            sig[i] = part["dir"].to_numpy()
            ent = engine.find_entries(P, sig)
            ent["max_bars"] = part["h"].to_numpy()
            res = engine.simulate(P, ent, engine.Exit("time", n=5, cap=5), pair)
            assert np.allclose(res["pips_gross"].to_numpy(float), part["gross"].to_numpy(float), atol=1e-6), (b, pair)
            assert np.allclose(res["exit_ts"].to_numpy(float), part["exit_ts"].to_numpy(float))
            ex = res["exit_i"].to_numpy()
            assert (i[1:] + 1 > ex[:-1]).all()  # B8
        from ia5.session import in_trading_hours

        assert in_trading_hours(t["entry_ts"].to_numpy(int)).all()
        assert (t["pips_net"] - (t["gross"] - t["spread"])).abs().max() < 1e-9


def test_nadrabianie_daje_ten_sam_wynik(world, tmp_path):
    """Mac wyłączony w połowie: zapis, wczytanie, nadrobienie = przebieg bez przerwy, co do bajta."""
    _, pn, las, g = world
    a = M.Manager(las)
    a.advance(pn, until=las["cuts"]["oos"] + 37 * H, log=lambda m: None)
    a.save(tmp_path / "current")
    b = M.Manager.load(tmp_path / "current")
    b.advance(pn, log=lambda m: None)
    x, y = g.frame(), b.frame()
    pd.testing.assert_frame_equal(x, y, check_dtype=False)
    assert (g.pos == b.pos).all() and (g.neg == b.neg).all()
    assert (np.array(g.bits) == np.array(b.bits)).all()


def test_publikacja_scisly_json(world, tmp_path):
    _, pn, _, g = world
    st = forest_report.write_public(g, pn, tmp_path / "public", now=1800000000)
    s = json.loads((tmp_path / "public" / "state.json").read_text(encoding="utf-8"), parse_constant=lambda x: pytest.fail(f"{x} w JSON"))
    assert s["computedAt"] == 1800000000 and len(s["now"]) == 8
    assert len(s["now"][0]["votes"]) == g.forest.words * 16
    inv = json.loads((tmp_path / "public" / "investors.json").read_text(encoding="utf-8"), parse_constant=lambda x: pytest.fail(x))
    assert len(inv["investors"]) == g.forest.m
    months = sorted((tmp_path / "public" / "journal").glob("*.parquet"))
    assert len(months) == len(st["months"])
    j = pd.concat([pd.read_parquet(f) for f in months])
    assert len(j) == st["counts"]["decyzje"]
    assert {"buy", "sell", "dir", "h", "z", "sila", "dop", "w", "l", "pkt", "punkty", "votes", "ex_a", "ex_b", "ex_c", "usd_a"} <= set(
        j.columns
    )
    assert "report" not in s and (tmp_path / "public" / "report.md").read_text(encoding="utf-8").startswith("# FOREST")


def test_budowa_i_krok(tmp_path):
    fr = frames(n=4200)
    cut = fr["EURUSD"]["ts"].iloc[-30]
    early = {p: d[d.ts <= cut].reset_index(drop=True) for p, d in fr.items()}
    st = forest_run.build(early, root=tmp_path, n_candidates=800, zero=1, workers=1, log=lambda m: None, ledger=tmp_path, n_investors=40)
    assert st["counts"]["decyzje"] > 0 and st["zero"][0]["seed"] == 1000
    st2, made = forest_run.step(fr, root=tmp_path, log=lambda m: None)
    assert made > 0 and st2["counts"]["decyzje"] == st["counts"]["decyzje"] + made
    df = pd.read_parquet(tmp_path / "current" / "journal.parquet")
    assert (df["seg"] == "LIVE").sum() == made
    assert json.loads((tmp_path / "oos_ledger.json").read_text())[0]["kind"] == "forest"


def planted(n=6000, seed=5, strength=0.00045, od=0):
    """Rynek z podłożoną zależnością od układu dwóch rzeczy naraz: rano (6–10 UTC) ruch z 24 świec trwa, po południu (10–15 UTC)
    się odwraca. od = od której świecy zależność działa: późny start znaczy, że las o niej nie wie i uczyć się mogą tylko mapy."""
    px = {"EURUSD": 1.1, "USDJPY": 140.0, "GBPUSD": 1.3, "EURGBP": 0.85, "AUDUSD": 0.7, "USDCHF": 0.9, "USDCAD": 1.3, "EURJPY": 150.0}
    out = {}
    hours = (START + H * np.arange(n)) // H % 24
    pora = np.where((hours >= 6) & (hours < 10), 1.0, np.where((hours >= 10) & (hours < 15), -1.0, 0.0))
    for k, p in enumerate(PAIRS8):
        rng = np.random.default_rng(seed + k)
        c = np.zeros(n)
        c[0] = px[p]
        noise = rng.normal(0, 0.0007, n)
        for t in range(1, n):
            mom = np.sign(c[t - 1] - c[max(0, t - 25)]) or 1.0
            c[t] = c[t - 1] * (1 + noise[t] + (strength * mom * pora[t] if t >= od else 0.0))
        o = np.r_[c[0], c[:-1]]
        hi = np.maximum(o, c) * (1 + rng.random(n) * 0.0004)
        lo = np.minimum(o, c) * (1 - rng.random(n) * 0.0004)
        ts = START + H * np.arange(n)
        out[p] = pd.DataFrame({"ts": ts, "open": o, "high": hi, "low": lo, "close": c, "filled": False, "gap_before": 0})
    return out


def run_world(fr, n=120, c=6000):
    pn = F.Panel(fr)
    las = F.forge(fr, n_candidates=c, n_investors=n, workers=1, log=lambda m: None, pn=pn)
    g = M.Manager(las)
    g.advance(pn, log=lambda m: None)
    df = g.frame()
    gross, closed, _ = forest_report.outcomes(df, df["dir"].to_numpy(), df["h"].to_numpy())
    d = df.assign(gross=gross, net=gross - df["spread"].to_numpy())[closed & np.isfinite(gross)].sort_values("ts", kind="stable")
    return g, d


def test_kontrola_pozytywna_lasu_i_szum():
    """Gdy jest czego się uczyć, las to znajduje; na szumie nie. Bez tego „brak przewagi” mógłby być błędem w kodzie."""
    g, d = run_world(planted())
    hit = (g.hits[1] / g.seen[1][None, :]).mean()
    oos = d[d.seg == "OOS"]
    assert hit > 0.53
    assert oos.gross.mean() > 2 and (oos.net > 0).mean() > 0.55
    g0, d0 = run_world(frames(n=4200, seed=11))
    assert abs((g0.hits[1] / g0.seen[1][None, :]).mean() - 0.5) < 0.012


def test_kontrola_pozytywna_map():
    """Zależność startuje po kuciu: las jej nie zna, ale jego głosy opisują stan rynku, więc mapy powinny się jej nauczyć.
    To jedyny dowód, że mechanizm map działa, gdy rynek daje mu coś do nauczenia. Na szumie mapy nie widzą nic."""
    n = 6000
    g, d = run_world(planted(od=int(n * 0.5) + 12))
    o = d[d.seg == "OOS"]
    u = forest_report.rank_test(o.z.to_numpy(float), o.net.to_numpy(float))
    assert u["rho"] > 0.05 and u["p"] < 0.05, u
    assert o[o.z >= 1].net.mean() > o.net.mean() + 1
    g0, d0 = run_world(frames(n=n, seed=21))
    o0 = d0[d0.seg == "OOS"]
    assert abs(forest_report.rank_test(o0.z.to_numpy(float), o0.net.to_numpy(float))["rho"]) < 0.1


def test_wnioski_i_pusty_las(world, tmp_path):
    """Las bez jednej decyzji też się publikuje (pierwsza budowa tuż przed weekendem)."""
    _, pn, las, g = world
    st, _ = forest_report.build_state(M.Manager(las), pn, now=1800000000)
    assert st["counts"]["decyzje"] == 0 and st["conclusions"] == [] and len(st["now"]) == 8
    json.dumps(st, allow_nan=False)
    full, _ = forest_report.build_state(g, pn, now=1800000000)
    assert any("Demokracja" in c["text"] for c in full["conclusions"])
    assert all(c["state"] in ("ok", "warn", "bad") for c in full["conclusions"])
    assert forest_report.pl(-1.5, 2, True) == "−1,50"


def test_obrot_wykrywa_zaleznosc_i_nie_zmysla():
    rng = np.random.default_rng(3)
    x = rng.normal(size=4000)
    assert forest_report.rank_test(x, x + rng.normal(size=4000))["p"] < 0.01
    assert forest_report.rank_test(x, rng.normal(size=4000))["p"] > 0.01


def test_ia5_start_buduje_i_liczy(monkeypatch):
    """Brak lasu → budowa, jest las → krok; błąd nie zatrzymuje programu i Mac wraca do bezczynności."""
    from ia5 import cli, cloud, publish, ready

    beats, calls = [], []
    st = {"counts": {"decyzje": 5, "mapy": 2}, "books": {"a": {"equity": 10000.0}}}
    monkeypatch.setattr(cloud, "heartbeat", lambda s, job=None: beats.append(s))
    monkeypatch.setattr(ready, "load", lambda d: {})
    monkeypatch.setattr(publish, "publish_forest", lambda p, log=print: calls.append("publikacja"))
    monkeypatch.setattr(forest_run, "exists", lambda: False)
    monkeypatch.setattr(forest_run, "build", lambda f, log=print, ledger=None: calls.append("budowa") or st)
    monkeypatch.setattr(forest_run, "step", lambda f, log=print: calls.append("krok") or (st, 3))
    state = {"now": "idle"}
    cli.handle_forest(state)
    assert calls == ["budowa", "publikacja"] and state == {"now": "idle", "job": None} and beats[-1] == "idle"
    calls.clear()
    monkeypatch.setattr(forest_run, "exists", lambda: True)
    cli.handle_forest(state)
    assert calls == ["krok", "publikacja"]

    def boom(f, log=print):
        raise RuntimeError("awaria")

    monkeypatch.setattr(forest_run, "step", boom)
    cli.handle_forest(state)
    assert state == {"now": "idle", "job": None} and beats[-1] == "idle"
