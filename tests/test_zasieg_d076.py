"""D-076: zakładka Zasięg — stan liczony na żywo = ta sama reguła co strategia zasieg_wybicie.py."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from ia5 import indicators as ind
from ia5 import zasieg
from ia5.check import synthetic_d1, synthetic_h1

EX = Path(__file__).resolve().parents[1] / "strategies" / "examples" / "zasieg_wybicie.py"


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    h = synthetic_h1(tmp_path_factory.mktemp("h1"), n=4000)
    d = synthetic_d1(tmp_path_factory.mktemp("d1"), days=2000)
    return zasieg.load_ready(h), zasieg.load_ready(d)


def test_rule_matches_strategy(data):
    h1_raw, d1_raw = data
    ns: dict = {}
    exec(compile(EX.read_text(encoding="utf-8"), str(EX), "exec"), ns)  # noqa: S102 — przykład z repo
    assert (ns["BOX"], ns["REF"], ns["PCT"], ns["H"]) == (zasieg.BOX, zasieg.REF, zasieg.PCT, zasieg.H)
    for pair in ("EURUSD", "USDJPY"):
        h1, d1 = zasieg.h1_frame(h1_raw[pair]), zasieg.d1_frame(d1_raw[pair])
        frame = h1.copy()
        ind.attach_d1(frame, d1)
        s = ns["signals"](frame, {"tp": 3}, ind).to_numpy()
        lv = ns["levels"](frame, {"tp": 3}, ind)
        ind.attach_d1(frame, None)
        sf = zasieg.signal_frame(h1, d1, 3)
        assert np.array_equal(s, sf["dir"].to_numpy()) and s.any()
        assert np.allclose(lv["sl"].to_numpy(), sf["sl"].to_numpy(), equal_nan=True)
        assert np.allclose(lv["tp"].to_numpy(), sf["tp"].to_numpy(), equal_nan=True)
        # TP = 3 × odległość do SL
        k = sf["dir"].to_numpy() != 0
        c = h1["close"].to_numpy()[k]
        assert np.allclose(np.abs(sf["tp"].to_numpy()[k] - c), 3 * np.abs(c - sf["sl"].to_numpy()[k]))


def test_state(data):
    h1_raw, d1_raw = data
    st = zasieg.compute_state(h1_raw, d1_raw, now=1_800_000_000)
    assert set(st["pairs"]) == set(h1_raw)
    e = st["pairs"]["EURUSD"]
    assert [f["h"] for f in e["forecast"]] == [1, 3, 5]
    f3 = e["forecast"][1]
    assert f3["low"] < f3["mid"] < f3["high"] and f3["mood"] in ("żywiej niż zwykle", "jak zwykle", "spokojniej niż zwykle")
    assert e["forecast"][0]["mid"] < f3["mid"] < e["forecast"][2]["mid"]       # dłuższy horyzont = większy zasięg
    b = e["box"]
    assert b["upper"] > b["lower"] and 0 <= b["pct"] <= 100
    assert b["long"]["tp"] - b["long"]["trigger"] == pytest.approx(3 * (b["long"]["trigger"] - b["long"]["sl"]))
    assert b["short"]["trigger"] - b["short"]["tp"] == pytest.approx(3 * (b["short"]["sl"] - b["short"]["trigger"]))
    assert len(e["history"]["ts"]) == zasieg.HISTORY_DAYS
    assert st["quality"]["n"] > 0 and 0 < st["quality"]["band80"] <= 100
    json.loads(zasieg.to_json(st))   # bez NaN


def test_signals_use_engine(data):
    h1_raw, d1_raw = data
    raw = h1_raw["GBPUSD"]
    h1, d1 = zasieg.h1_frame(raw), zasieg.d1_frame(d1_raw["GBPUSD"])
    end = int(raw["ts"].iloc[-1]) + 3600
    sig = zasieg.signals_block(raw, h1, d1, "GBPUSD", end + 400 * 86400)   # okno 7 dni przesunięte — nic
    assert sig == []
    allsig = []
    for k in range(0, 4000, 168):   # przesuwamy koniec danych tydzień po tygodniu, żeby trafić na sygnały
        part = raw.iloc[:k + 600]
        if len(part) < 600:
            continue
        allsig += zasieg.signals_block(part, zasieg.h1_frame(part), d1, "GBPUSD", int(part["ts"].iloc[-1]) + 3600)
    assert allsig and all(s["status"] in ("TP", "SL", "czas", "otwarta", "wejście na open następnej świecy") for s in allsig)
    done = [s for s in allsig if s["status"] in ("TP", "SL")]
    assert all((s["pips"] > 0) == (s["status"] == "TP") for s in done)
    assert isinstance(pd.Timestamp(allsig[0]["signal_ts"], unit="s"), pd.Timestamp)
