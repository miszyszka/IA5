"""Przegląd zdrowia (D-023): czyste dane nie zapalają nic, każda podłożona usterka zapala właściwą kontrolę."""
from datetime import UTC, datetime

import numpy as np
import pandas as pd
from ia5 import health
from ia5.coverage import expected_hours

H = 3600
START, END = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp()), int(datetime(2024, 7, 1, tzinfo=UTC).timestamp())


def bars(close, ts):
    c = np.asarray(close, float)
    o = np.concatenate([[c[0]], c[:-1]])
    return pd.DataFrame({"ts": ts, "open": o, "high": np.maximum(o, c) * 1.0002, "low": np.minimum(o, c) * 0.9998, "close": c})


def clean():
    rng = np.random.default_rng(7)
    ts = expected_hours(START, END)
    walk = lambda s, v: s * np.exp(np.cumsum(rng.normal(0, v, len(ts))))  # noqa: E731
    eu, uj, gu = walk(1.10, 8e-4), walk(150.0, 8e-4), walk(1.27, 8e-4)
    closes = {"EURUSD": eu, "USDJPY": uj, "GBPUSD": gu, "EURJPY": eu * uj + rng.normal(0, 0.005, len(ts)),
              "EURGBP": eu / gu + rng.normal(0, 0.00005, len(ts)), "AUDUSD": walk(0.66, 8e-4),
              "USDCHF": walk(0.88, 8e-4), "USDCAD": walk(1.36, 8e-4)}
    return {p: bars(c, ts) for p, c in closes.items()}, ts


def status(last):
    return {"pairs": {p: {"lastTs": last, "flags": []} for p in health.PAIRS}, "lastRun": {"ok": True, "finishedAt": last + H},
            "totalBars": 1000, "dataSha": "abcdef0123"}


def states(h):
    return {c["id"]: c["state"] for c in h["checks"]}


def test_clean_data_is_all_ok():
    yahoo, ts = clean()
    now = int(ts[-1]) + H + 300
    h = health.run(status(int(ts[-1])), yahoo, None, docs=[], now=now, ready={"EURUSD": {"bars": 100, "filled": 2}})
    s = states(h)
    ids = "yahoo_fresh apps_script yahoo_flags mac_copy bars_valid triangles frozen publish strategies".split()
    for cid in ids:
        assert s[cid] == "ok", (cid, [c for c in h["checks"] if c["id"] == cid])
    assert "8 par" in h["facts"][0] and "ostatnia świeca" in h["facts"][0] and "D-0" not in " ".join(h["facts"])   # D-060: krótko
    assert "Dukascopy" not in health.report(h) and "Stan systemu IA5" in health.report(h)


def test_wrong_price_in_one_pair_breaks_triangle():
    h1, _ = clean()
    m = (h1["EURJPY"].ts >= START + 60 * 86400) & (h1["EURJPY"].ts < START + 66 * 86400)
    h1["EURJPY"].loc[m, ["open", "high", "low", "close"]] += 0.6  # 60 pipsów
    c = health.triangles(h1)
    assert c["state"] == "warn" and any("EUR/JPY 2024-03" in d for d in c["detail"])


def test_mac_copy_behind_firestore():
    yahoo, ts = clean()
    c = health.mac_copy(status(int(ts[-1]) + 2 * H), yahoo)
    assert c["state"] == "warn" and len(c["detail"]) == 8
    assert health.mac_copy(status(int(ts[-1])), yahoo)["state"] == "ok"
    assert health.mac_copy(status(int(ts[-1])), {})["state"] == "bad"


def test_frozen_feed():
    h1, _ = clean()
    i = 500
    h1["GBPUSD"].loc[i:i + 9, ["open", "high", "low", "close"]] = h1["GBPUSD"].close.iloc[i]
    c = health.frozen(h1)
    assert c["state"] == "warn" and "GBP/USD" in c["detail"][0]


def test_stale_yahoo_broken_bar_failed_publish_stuck_strategy():
    yahoo, ts = clean()
    now = int(ts[-1]) + 3 * H  # świeca sprzed 2 h powinna już być
    yahoo["AUDUSD"].loc[10, "high"] = yahoo["AUDUSD"].loc[10, "low"] * 0.9
    docs = [{"id": "a", "name": "A", "status": "liczy_sie"}, {"id": "b", "name": "B", "status": "blad", "error": "look-ahead"}]
    h = health.run(status(int(ts[-60])), yahoo, None, docs=docs, beat_state="idle",
                   publish_error="git push: denied", now=now)
    s = states(h)
    # D-060: pojedyncza zła świeca Yahoo jest zastąpiona średnią — to nie problem; problemy to tylko rzeczy do zrobienia
    assert s["yahoo_fresh"] == "bad" and s["bars_valid"] == "ok" and s["publish"] == "bad" and s["strategies"] == "warn"
    assert h["state"] == "bad" and h["summary"].startswith("Do zrobienia:")


def test_code_version_check():
    """D-046: program liczący starą wersją kodu albo kod starszy niż GitHub — widać to w przeglądzie zdrowia."""
    from ia5.health import code_version

    assert code_version(None)["state"] == "ok"
    ok = code_version({"repo": "~/IA5", "head": "abc1234def", "loaded": "abc1234def", "behind": 0})
    assert ok["state"] == "ok" and "~/IA5" in ok["text"]
    stale = code_version({"repo": "~/IA5", "head": "bbb", "loaded": "aaa", "behind": 0})
    assert stale["state"] == "bad" and "Ctrl+C" in stale["fix"]
    behind = code_version({"repo": "~/IA5", "head": "aaa", "loaded": "aaa", "behind": 3})
    assert behind["state"] == "warn" and "git pull" in behind["fix"] and "3 nowsze zmiany" in behind["text"]


def test_code_info_reads_this_repo():
    from ia5 import cli

    info = cli.code_info(fetch=False)
    assert info is None or (len(info["head"]) == 40 and info["behind"] is None)


def test_flags_are_verified_against_data_and_never_warn_d060():
    """D-060: zgłoszenia Apps Script sprawdzane na kopii — naprawione u źródła i obsłużone średnią to nie problem."""
    yahoo, ts = clean()
    t_have, t_gone = int(ts[100]), int(ts[-1]) + 5 * H
    st = {"pairs": {"EURUSD": {"flags": [f"luka@{t_have}", f"revised@{t_have}", f"luka@{t_gone}", f"ohlc@{t_have}"]}},
          "cross": {"flags": ["EURJPY≠EURUSD×USDJPY"]}}
    c = health.yahoo_flags(st, yahoo)
    assert c["state"] == "ok" and "2 już naprawionych" in c["text"] and "3 uzupełnionych" in c["text"]
    assert health.yahoo_flags({"pairs": {}}, yahoo)["state"] == "ok"
    many = {p: df.copy() for p, df in yahoo.items()}
    for df in many.values():
        df.loc[: len(df) // 50, "high"] = 0.5                     # 2% złych świec we wszystkich parach → to już nie przypadek
    assert health.bars_valid(many)["state"] == "warn"


# ---------- D-063: kursy złotówkowe (REV) ----------

NOW_PLN = int(datetime(2026, 11, 11, 10, tzinfo=UTC).timestamp())


def pln_status(pln, rejected=None):
    cur = {c: {"lastTs": int(df.ts.max()), "count": len(df)} for c, df in pln.items()}
    return {"pln": {"tz": "Europe/London", "currencies": cur, "rejected": rejected or {}}}


def test_pln_no_data_warns_with_fix():
    c = health.pln_rates({}, {}, None, NOW_PLN)
    assert c["state"] == "warn" and "backfillPLN" in c["fix"]


def test_pln_ok_lists_rejected():
    from rev_fixtures import synthetic_raw

    pln = synthetic_raw(["EUR", "USD", "CHF"], start="2014-01-01", end="2026-11-10")
    c = health.pln_rates(pln_status(pln, {"QAR": "historia od 2023-11-01 — krótsza niż 10 lat"}), pln, None, NOW_PLN)
    assert c["state"] == "ok", c
    assert "QAR" in c["text"] and "3 waluty" in c["text"]


def test_pln_cross_check_detects_scale():
    from rev_fixtures import frame, workdays

    days = workdays("2024-01-01", "2026-11-10")
    rng = np.random.default_rng(3)
    usdpln = 4.0 * np.exp(np.cumsum(rng.normal(0, 0.004, len(days))))
    usdjpy = 150 * np.exp(np.cumsum(rng.normal(0, 0.004, len(days))))
    pln = {"USD": frame(days, usdpln), "JPY": frame(days, usdpln / usdjpy * 100)}    # JPY kwotowany za 100 jednostek
    fx = {"USDJPY": frame(days, usdjpy)}
    cross = health.pln_cross(pln, fx)
    assert cross["USD/JPY"]["median_pct"] > 50
    c = health.pln_rates(pln_status(pln), pln, fx, NOW_PLN)
    assert c["state"] == "warn" and "JPY" in c["text"]
    ok = {"USD": pln["USD"], "JPY": frame(days, usdpln / usdjpy)}
    assert health.pln_cross(ok, fx)["USD/JPY"]["median_pct"] < 0.01


def test_pln_peg_break_warns():
    from rev_fixtures import frame, workdays

    days = workdays("2023-01-01", "2026-11-10")
    rng = np.random.default_rng(4)
    usd = 4.0 * np.exp(np.cumsum(rng.normal(0, 0.004, len(days))))
    hkd = usd / 7.8 * (1 + rng.normal(0, 0.0003, len(days)))
    pln = {"USD": frame(days, usd), "HKD": frame(days, hkd)}
    assert health.pln_rates(pln_status(pln), pln, None, NOW_PLN)["state"] == "ok"
    broken = hkd.copy()
    broken[-20:] *= 1.05
    pln["HKD"] = frame(days, broken)
    c = health.pln_rates(pln_status(pln), pln, None, NOW_PLN)
    assert c["state"] == "warn" and "HKD" in c["text"]


def test_pln_stale_currency_warns():
    from rev_fixtures import synthetic_raw

    pln = synthetic_raw(["EUR", "CHF"], start="2014-01-01", end="2026-11-10")
    pln["CHF"] = pln["CHF"].iloc[:-8]
    c = health.pln_rates(pln_status(pln), pln, None, NOW_PLN)
    assert c["state"] == "warn" and "CHF" in c["text"]
