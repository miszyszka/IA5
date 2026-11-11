"""D-037: skaner hipotez — znajduje podłożony efekt, nie patrzy w OOS, kontroluje wielokrotne próby."""
import numpy as np
import pandas as pd
from ia5 import scan

T0 = 1041811200  # 2003-01-06 00:00 UTC, poniedziałek


def synth(years=12, effect=0.0, effect_from=0.0, seed=0, hour_utc=8):
    n = int(years * 365.25 * 24)
    ts = T0 + 3600 * np.arange(n)
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.0010, n)
    h = (ts // 3600) % 24
    frac = np.arange(n) / n
    r[(h == hour_utc) & (frac >= effect_from)] -= effect      # euro „słabnie” o tej godzinie
    c = 1.2 + np.cumsum(r)
    o = np.r_[c[0], c[:-1]]
    df = pd.DataFrame({"ts": ts, "open": o, "high": np.maximum(o, c) + 0.0003, "low": np.minimum(o, c) - 0.0003, "close": c})
    wd = pd.to_datetime(ts, unit="s", utc=True).dayofweek
    return df[wd < 5].reset_index(drop=True)


def test_finds_planted_season_effect():
    out = scan.run({"EURUSD": synth(effect=0.0006)}, log=lambda m: None)
    s = out["survivors"]
    assert out["tested"] > 5000 and out["confirmed"] > 0
    top = s[s.family == "sezon"].iloc[0]
    assert top.dir == -1 and top.mean_val > 0
    assert "short" in scan.describe(top)


def test_no_effect_no_survivors_and_oos_untouched():
    # brak efektu → (prawie) nic nie przechodzi; efekt tylko w ostatnich 25% (OOS) → skaner go nie widzi
    noise = scan.run({"EURUSD": synth(seed=1)}, log=lambda m: None)
    assert noise["confirmed"] <= 2
    late = scan.run({"EURUSD": synth(seed=2, effect=0.002, effect_from=0.80)}, log=lambda m: None)
    s = late["survivors"]
    assert s[(s.family == "sezon") & (s.dir == -1)].empty


def test_bh_threshold():
    assert scan.bh_threshold(np.array([0.001, 0.02, 0.5, 0.9]), 0.05) == 0.02  # 0.02 ≤ 0.05·2/4
    assert scan.bh_threshold(np.array([0.3, 0.6]), 0.05) == 0.0


def test_report_and_save(tmp_path):
    out = scan.run({"EURUSD": synth(effect=0.0006, years=10)}, log=lambda m: None)
    f = scan.save(out, tmp_path / "s")
    md = (f / "scan.md").read_text()
    assert "Przetestowane reguły" in md and "nie było liczone" in md and (f / "survivors.csv").exists()


def test_cli_scan_local(tmp_path, monkeypatch, capsys):
    from ia5 import cloud, ready, store

    (tmp_path / "ready").mkdir(parents=True)
    synth(years=6, effect=0.0006).to_parquet(tmp_path / "ready" / "EURUSD.parquet", index=False)
    monkeypatch.setattr(store, "READY", tmp_path / "ready")
    monkeypatch.setattr(store, "SCANS", tmp_path / "scans")
    monkeypatch.setattr(cloud, "load_yahoo", lambda folder: {"EURUSD": pd.DataFrame()})
    monkeypatch.setattr(ready, "build", lambda *a, **k: {})
    from ia5 import cli

    assert cli.main(["scan", "--lokalnie", "--pary", "EURUSD"]) == 0
    assert "Skan hipotez" in capsys.readouterr().out
    assert len(list((tmp_path / "scans").glob("*/scan.md"))) == 1


def test_strategy_sees_pair_name(tmp_path):
    from ia5.sandbox import run_strategy_code

    d = tmp_path / "h1"
    d.mkdir()
    for p in ("EURUSD", "GBPUSD"):
        synth(years=1, seed=3).to_parquet(d / f"{p}.parquet", index=False)
    code = ("def signals(df, p, ind):\n"
            "    s = (ind.hour(df) == 7).astype('int8')\n"
            "    return s if df.attrs.get('pair') == 'EURUSD' else s * 0\n")
    sig, meta = run_strategy_code(code, d)
    assert not meta["lookahead"] and set(sig.pair) == {"EURUSD"}
