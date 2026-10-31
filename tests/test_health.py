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
    assert "Jedyne źródło cen" in " ".join(h["facts"]) and "Do liczenia: 1 par" in " ".join(h["facts"])
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
    assert s["yahoo_fresh"] == "bad" and s["bars_valid"] == "bad" and s["publish"] == "bad" and s["strategies"] == "warn"
    assert h["state"] == "bad" and h["summary"].startswith("5 problemów")  # + brak mapy pokrycia
