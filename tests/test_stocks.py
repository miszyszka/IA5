"""Stocks (D-071): warstwa czyszczenia, pasmo ±B, brak look-ahead, wybór tylko z IS, portfel na żywo (całe akcje, wtorek)."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from ia5 import stk_data as sd
from ia5 import stk_live as sl
from ia5 import stk_method as sm
from ia5 import stk_research as sr
from stk_fixtures import raw_stock, universe


def ready_of(raw: dict) -> dict:
    return {k: sd.clean_stk(v)[0] for k, v in raw.items()}


def cut(ready: dict, now: int) -> dict:
    """Świeca dnia dostępna po północy w Nowym Jorku (dzień zamknięty, + 60 s)."""
    return {k: v[v.ts + 86400 + 60 <= now].reset_index(drop=True) for k, v in ready.items()}


def ts_utc(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


# ---------- warstwa czyszczenia ----------

def test_clean_dividend_split_spike_weekend():
    r = raw_stock(1, start="2020-01-02", end="2020-12-31")
    sat = int(pd.Timestamp("2020-03-07", tz="America/New_York").tz_convert("UTC").timestamp())
    r = pd.concat([r, pd.DataFrame([{"ts": sat, "open": 1, "high": 1, "low": 1, "close": 1, "div": 0.0, "split": 1.0}])])
    # dywidenda z dnia bez świecy (sobota 14.03) → poniedziałek 16.03
    sat2 = int(pd.Timestamp("2020-03-14", tz="America/New_York").tz_convert("UTC").timestamp())
    nan = np.nan
    r = pd.concat([r, pd.DataFrame([{"ts": sat2, "open": nan, "high": nan, "low": nan, "close": nan, "div": 0.7, "split": 1.0}])])
    r = r.sort_values("ts").reset_index(drop=True)
    # split 2:1 nieprzeliczony wstecz od 2020-06-01
    d = sd.day_str(r.ts)
    pre = d < "2020-06-01"
    for c in ("open", "high", "low", "close"):
        r.loc[pre, c] *= 2
    r.loc[d == "2020-06-01", "split"] = 2.0
    # wyskok jednego dnia
    i = int(np.flatnonzero(d == "2020-09-15")[0])
    r.loc[i, ["open", "high", "low", "close"]] *= 3
    out, info = sd.clean_stk(r)
    assert info["off_session"] == 2 and info["rescaled"] == [["2020-06-01", 2.0]] and info["spikes"] == 1
    assert out.loc[out.day == "2020-03-16", "div"].iloc[0] == pytest.approx(0.35)   # dywidenda sprzed splitu też ÷ 2
    c = out.set_index("day").close
    assert abs(c["2020-05-29"] / c["2020-06-02"] - 1) < 0.1          # ciągłość po splicie
    assert abs(c["2020-09-15"] / c["2020-09-14"] - 1) < 1e-12         # wyskok zastąpiony
    assert (pd.to_datetime(out.day).dt.weekday < 5).all()


def test_build_stk_rebuilds_only_on_change(tmp_path):
    raw = {"AAA": raw_stock(3, start="2018-01-02", end="2020-01-01")}
    a = sd.build_stk(raw, tmp_path, log=lambda m: None)
    b = sd.build_stk(raw, tmp_path, log=lambda m: None)
    assert a["AAA"]["rebuilt"] and not b["AAA"]["rebuilt"]
    sd.build_stk({}, tmp_path, log=lambda m: None)
    assert not list(tmp_path.glob("AAA.*"))


# ---------- pasmo i cele ----------

def test_project_stays_in_band_and_sums_to_one():
    rng = np.random.default_rng(0)
    w = rng.uniform(0.01, 0.2, size=(200, 9))
    w /= w.sum(axis=1, keepdims=True)
    s = rng.uniform(-1, 1, size=(200, 9))
    t = sm.project(w, s, 0.2)
    assert np.allclose(t.sum(axis=1), 1)
    assert (t >= w * 0.8 - 1e-12).all() and (t <= w * 1.2 + 1e-12).all()
    assert np.allclose(sm.project(w, np.zeros_like(s), 0.2), w)


def test_configs_grid():
    assert len(sm.CONFIGS) == len(sm.GROUPS) * 3 * 3 * 3 >= 4000
    assert len({c.id for c in sm.CONFIGS}) == len(sm.CONFIGS)
    c = sm.CONFIGS[1234]
    g = sm.GROUPS.index((c.signal, c.norm, c.smooth))
    from ia5.stk_config import FILTERS, STRENGTHS, THRESHOLDS
    assert sm.config_index(g, STRENGTHS.index(c.strength), FILTERS.index(c.filter), THRESHOLDS.index(c.threshold)) == 1234


# ---------- uczciwość ----------

@pytest.fixture(scope="module")
def uni():
    return ready_of(universe(6, revert=0.003, late={2: "2004-08-19"}, end="2026-12-31"))


def test_scores_have_no_lookahead(uni):
    w = np.ones(6) / 6
    full = sd.Panel(uni, list(uni))
    Wf = sm.prepare(full, w)
    k = len(Wf.sig) - 40
    day = full.days[Wf.sig[k]]
    short = {t: f[f.day <= day].reset_index(drop=True) for t, f in uni.items()}
    ps = sd.Panel(short, list(uni))
    Ws = sm.prepare(ps, w)
    n = int(np.searchsorted(Ws.sig, Ws.sig.max())) + 1
    kk = min(k + 1, n)
    assert np.allclose(Wf.scores[:, :kk], Ws.scores[:, :kk], equal_nan=True)
    assert np.array_equal(Wf.elig[:kk], Ws.elig[:kk])
    # zaburzenie przyszłości nie zmienia celów
    a = sm.targets_for(Wf, k, None, 0.2)
    pert = {t: f.assign(close=np.where(f.day > day, f.close * 1.7, f.close)) for t, f in uni.items()}
    Wp = sm.prepare(sd.Panel(pert, list(uni)), w)
    assert np.allclose(a, sm.targets_for(Wp, k, None, 0.2))


def test_zero_band_equals_fixed(uni):
    w = np.array([3, 2, 2, 1, 1, 1], float)
    w /= w.sum()
    W = sm.prepare(sd.Panel(uni, list(uni)), w)
    s0 = sm.start_week(W, w, 0.8)
    end = len(W.sig) - 1
    fixed = sm.run_baselines(W, s0, end)["fixed"][0]
    cfg = sm.BY_ID["dd252|rank|full|s1|none|h0"]
    r, _ = sm.run_one(W, cfg, 0.0, s0, end)
    assert np.allclose(r, fixed)


def test_research_choice_ignores_oos_and_is_serializable(uni):
    cfg = {"tickers": [{"t": t, "w": 1} for t in uni] + [{"t": "NOPE", "w": 1}], "capital": 20000, "band": 20}
    now = ts_utc("2026-11-15 12:00")
    res = sr.run_research(cut(uni, now), cfg, now, paths=40, log=lambda m: None)
    json.dumps(res, allow_nan=False)
    assert res["missing"] == ["NOPE"] and res["trials"] == len(sm.CONFIGS)
    assert res["verdict"]["color"] in ("green", "yellow", "red") and len(res["verdict"]["checks"]) == 5
    assert abs(sum(res["weights"].values()) - 1) < 1e-9
    # zmiana cen na OOS nie zmienia wyboru (W1)
    is_end_day = sd.day_str([res["periods"]["is_end_ts"]])[0]
    pert = {t: f.assign(open=np.where(f.day > is_end_day, f.open * np.linspace(1, 3, len(f)), f.open),
                        close=np.where(f.day > is_end_day, f.close * np.linspace(1, 3, len(f)), f.close)) for t, f in cut(uni, now).items()}
    res2 = sr.run_research(pert, cfg, now, paths=40, log=lambda m: None)
    assert res2["winner"] == res["winner"]
    assert "## Walidacja" in sr.report_md(res)


# ---------- portfel na żywo ----------

def test_live_whole_shares_tuesday_open_and_catch_up(uni):
    t0 = ts_utc("2026-11-15 12:00")
    cfg = {"tickers": [{"t": t, "w": w} for t, w in zip(uni, [30, 20, 20, 10, 10, 10])], "capital": 50000, "band": 20}
    res = sr.run_research(cut(uni, t0), cfg, t0, paths=20, log=lambda m: None)
    st, t = None, t0
    while t < t0 + 28 * 86400:
        st = sl.live_step(st, res, cut(uni, t), t)
        t += 5 * 3600
    one = sl.live_step(None, res, cut(uni, t - 5 * 3600), t - 5 * 3600)
    strip = lambda x: json.dumps({k: v for k, v in x.items() if k != "computedAt"}, sort_keys=True)   # noqa: E731
    assert strip(st) == strip(one)
    plans = st["plans"]
    assert plans[0]["exec_day"] == "2026-11-16"                          # start od razu: następny dzień sesji
    assert [p["exec_day"] for p in plans[1:4]] == ["2026-11-17", "2026-11-24", "2026-12-01"]   # wtorki
    for p in plans:
        assert all(isinstance(o["shares"], int) and o["shares"] > 0 for o in p["orders"])
    open_t = {f: uni[f].set_index("day").open for f in uni}
    for row in st["ledger"]:
        assert row["price"] == pytest.approx(open_t[row["t"]][row["exec_day"]])   # wykonanie po otwarciu
    assert st["books"]["method"]["cash"] >= -1e-6
    tot = st["today"]["total"]
    assert tot == pytest.approx(st["valuation"][-1][1])
    for r in st["today"]["rows"]:
        if r["shares"]:
            assert r["lo"] - 0.03 <= r["weight"] <= r["hi"] + 0.03


def test_live_waits_for_monday_and_skips_holiday_tuesday(uni):
    t0 = ts_utc("2026-11-15 12:00")
    cfg = {"tickers": [{"t": t, "w": 1} for t in uni], "capital": 30000, "band": 20}
    res = sr.run_research(cut(uni, t0), cfg, t0, paths=20, log=lambda m: None)
    # wtorek 24.11 08:00 bez świecy poniedziałku 23.11 → planu jeszcze nie ma; po 15:00 — plan z piątku (spóźniony)
    tue = ts_utc("2026-11-24 07:30")
    no_mon = {k: v[v.day < "2026-11-23"].reset_index(drop=True) for k, v in uni.items()}
    st = sl.live_step(None, res, no_mon, tue)
    assert [p["signal_day"] for p in st["plans"]] == ["2026-11-13", "2026-11-16"]
    st = sl.live_step(None, res, no_mon, ts_utc("2026-11-24 14:30"))
    assert st["plans"][-1]["signal_day"] == "2026-11-20" and st["plans"][-1]["late"]
    # święto we wtorek 24.11 (brak świecy wtorku w danych) → wykonanie w środę
    hol = {k: v[v.day != "2026-11-24"].reset_index(drop=True) for k, v in uni.items()}
    t = ts_utc("2026-11-27 12:00")
    st = sl.live_step(None, res, cut(hol, t), t)
    p = [x for x in st["plans"] if x["signal_day"] == "2026-11-23"][0]
    assert p["exec_day"] == "2026-11-25"


def test_normalize_config_and_hash():
    c = sr.normalize_config({"tickers": [{"t": " ko ", "w": 2}, {"t": "KO", "w": 3}, {"t": "X", "w": 0}], "capital": 1000, "band": 80})
    assert c == {"tickers": [{"t": "KO", "w": 2.0}], "capital": 1000.0, "band": 50.0}
    assert sr.config_hash({"tickers": [{"t": "KO", "w": 2}], "capital": 1000, "band": 50}) == sr.config_hash(c)
    d = sr.normalize_config(None)
    assert len(d["tickers"]) == 27 and abs(sum(x["w"] for x in d["tickers"]) - 100) < 1e-6


# ---------- przebieg na Macu: „Policz backtest” → statusy w stocks/config → publikacja ----------

class FakeCloud:
    def __init__(self, raw: dict):
        self.raw = raw
        self.cfg_writes: list[dict] = []
        self.status = {"stk": {"tz": "America/New_York", "rejected": {"NOPE": "Yahoo nie zna tickera NOPE"},
                               "tickers": {t: {"lastTs": int(f.ts.max()), "count": len(f)} for t, f in raw.items()}}}

    def read_status(self):
        return self.status

    def write_stocks_config(self, fields):
        self.cfg_writes.append(dict(fields))

    def sync_yahoo_stk(self, folder, status, tickers, log=print):
        return {t: self.raw[t] for t in tickers if t in self.raw}

    def load_yahoo_stk(self, folder, tickers=None):
        return {}

    def set_data_sha(self, sha):
        pass


def test_mac_flow_policz_backtest(tmp_path, monkeypatch):
    from ia5 import publish, stk_run

    raw = universe(4, revert=0.003, end="2026-11-13")
    monkeypatch.setattr(stk_run, "DATA_REPO", tmp_path / "repo")
    monkeypatch.setattr(stk_run, "STK_READY", tmp_path / "ready")
    monkeypatch.setattr(stk_run, "STOCKS", tmp_path / "stocks")
    monkeypatch.setattr(stk_run, "HOME", tmp_path)
    monkeypatch.setattr(stk_run, "RANDOM_PATHS", 20)
    published = {}

    def fake_publish(files, log=print, remove=()):
        (tmp_path / "repo" / "stocks").mkdir(parents=True, exist_ok=True)
        for k, v in files.items():
            (tmp_path / "repo" / "stocks" / k).write_text(v)
            published[k] = v
        return "abc"

    monkeypatch.setattr(publish, "publish_stocks", fake_publish)
    monkeypatch.setattr(publish, "ensure_repo", lambda: None)
    cloud = FakeCloud(raw)
    doc = {"tickers": [{"t": t, "w": 25} for t in raw] + [{"t": "NOPE", "w": 5}], "capital": 25000, "band": 20,
           "status": "do_policzenia", "updatedBy": "u1"}
    stk_run.handle(cloud, {}, doc, True, "mac", log=lambda m: None)
    statuses = [w.get("status") for w in cloud.cfg_writes if "status" in w]
    assert statuses[0] == "liczy_sie" and statuses[-1] == "policzony"
    res = json.loads(published["research.json"])
    assert res["missing"] == ["NOPE"] and "NOPE" in res["rejected"]
    assert set(published) == {"research.json", "report.md", "config.json", "state.json"}
    st = json.loads(published["state.json"])
    assert st["method"]["id"] == res["winner"] and st["capital0"] == 25000
    assert (tmp_path / "oos_ledger.json").exists()


def test_mac_flow_without_stock_data_does_not_wait(tmp_path, monkeypatch):
    from ia5 import publish, stk_run

    monkeypatch.setattr(stk_run, "DATA_REPO", tmp_path / "repo")
    monkeypatch.setattr(publish, "ensure_repo", lambda: None)
    cloud = FakeCloud({})
    cloud.status = {}
    stk_run.handle(cloud, {}, None, False, "mac", log=lambda m: None)
    assert cloud.cfg_writes[0]["status"] == "do_policzenia" and cloud.cfg_writes[0]["updatedBy"] == "mac"   # lista startowa
    assert cloud.cfg_writes[-1]["status"] == "czeka_na_dane" and "Code.gs" in cloud.cfg_writes[-1]["error"]


def test_clean_normalizes_yahoo_open_stamps_and_dedupes_days():
    """D-071: Yahoo stempluje świece spółek 09:30 NY; stare wpisy o północy — ten sam dzień, jeden wiersz, ts = północ."""
    r = raw_stock(5, start="2026-03-02", end="2026-03-20")
    open_ts = r.ts + int(9.5 * 3600)
    both = pd.concat([r.assign(ts=open_ts), r.assign(close=r.close * 1.0)]).reset_index(drop=True)
    out, info = sd.clean_stk(both)
    assert len(out) == len(r) and info["duplicates"] == len(r)
    assert (out.ts.to_numpy() == r.ts.to_numpy()).all()
    assert out.day.tolist() == list(sd.day_str(r.ts))


def test_mac_flow_never_computes_on_incomplete_list(tmp_path, monkeypatch):
    """Spółka bez danych (nie odrzucona) = backtest czeka, a nie liczy się z przeskalowanymi udziałami pozostałych.
    Gdy dane dojdą — liczy się przy następnym przebiegu (status czeka_na_dane)."""
    from ia5 import publish, stk_run

    raw = universe(4, revert=0.003, end="2026-11-13")
    for k, v in (("DATA_REPO", tmp_path / "repo"), ("STK_READY", tmp_path / "ready"), ("STOCKS", tmp_path / "stocks"),
                 ("HOME", tmp_path), ("RANDOM_PATHS", 20), ("WAIT_DATA_S", 0)):
        monkeypatch.setattr(stk_run, k, v)
    published = {}

    def fake_publish(files, log=print, remove=()):
        (tmp_path / "repo" / "stocks").mkdir(parents=True, exist_ok=True)
        for k, v in files.items():
            (tmp_path / "repo" / "stocks" / k).write_text(v)
            published[k] = v
        return "abc"

    monkeypatch.setattr(publish, "publish_stocks", fake_publish)
    monkeypatch.setattr(publish, "ensure_repo", lambda: None)
    cloud = FakeCloud(raw)
    late = cloud.status["stk"]["tickers"].pop("T3")
    doc = {"tickers": [{"t": t, "w": 25} for t in raw], "capital": 10000, "band": 20, "status": "do_policzenia", "updatedBy": "u1"}
    stk_run.handle(cloud, {}, doc, True, "mac", log=lambda m: None)
    assert "research.json" not in published
    assert cloud.cfg_writes[-1]["status"] == "czeka_na_dane" and cloud.cfg_writes[-1]["waiting"] == ["T3"]
    cloud.status["stk"]["tickers"]["T3"] = late          # Apps Script dociągnął spółkę
    stk_run.handle(cloud, {}, {**doc, "status": "czeka_na_dane"}, False, "mac", log=lambda m: None)
    res = json.loads(published["research.json"])
    assert res["universe"] == list(raw) and res["missing"] == []


def test_plan_after_open_executes_next_session():
    """Plan zrobiony po otwarciu sesji (np. poniedziałek 16:58 w Polsce = 10:58 w NY) wykonuje się na następnym otwarciu."""
    assert sl.exec_from(ts_utc("2026-11-16 15:58")) == "2026-11-17"
    assert sl.exec_from(ts_utc("2026-11-17 07:00")) == "2026-11-17"   # wtorek 08:00 w Polsce = 02:00 w NY
    assert sl.exec_from(ts_utc("2026-11-15 12:00")) == "2026-11-15"   # niedziela → pierwszy dzień sesji ≥ niedziela = poniedziałek
