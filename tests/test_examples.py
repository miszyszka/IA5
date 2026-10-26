"""Przykładowe strategie (strategies/examples) muszą zawsze przechodzić kontrolę — to wzorce dla Claude."""
from pathlib import Path

import pytest
from ia5.check import check_code_on, synthetic_h1

EX = sorted((Path(__file__).resolve().parents[1] / "strategies" / "examples").glob("*.py"))


@pytest.fixture(scope="module")
def syn(tmp_path_factory):
    return synthetic_h1(tmp_path_factory.mktemp("syn"), n=3000)


@pytest.mark.parametrize("path", EX, ids=[p.stem for p in EX])
def test_example_passes(path, syn):
    res = check_code_on(path.read_text(encoding="utf-8"), syn)
    assert res["ok"], res["errors"]
    assert res["meta"]["hypothesis"]


def test_daily_max_with_transform_is_caught_as_lookahead(syn):
    bad = '''
def signals(df, p, ind):
    day = df.index.floor("D")
    day_mid = df.close.groupby(day).transform("mean")    # średnia CAŁEGO dnia — także przyszłych godzin
    return ind.cross_above(df.close, day_mid).astype("int8")
'''
    res = check_code_on(bad, syn)
    assert not res["ok"] and any("Look-ahead" in e for e in res["errors"])


def test_unclosed_higher_timeframe_is_caught(syn):
    """Subtelny look-ahead: SMA z niezamkniętej świecy H4 (resample bez shift(1)) — zaburzenie przyszłości go wykrywa."""
    bad = '''
def signals(df, p, ind):
    h4 = ind.sma(df.close.resample("4h").last().dropna(), 50)
    return ind.cross_above(df.close, h4.reindex(df.index, method="ffill")).astype("int8")
'''
    res = check_code_on(bad, syn)
    assert any("Look-ahead" in e for e in res["errors"])
    good = bad.replace(".dropna(), 50)", ".dropna(), 50).shift(1)")
    assert check_code_on(good, syn)["ok"]
