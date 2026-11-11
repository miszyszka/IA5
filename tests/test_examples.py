"""Przykładowe strategie (strategies/examples) muszą zawsze przechodzić kontrolę — to wzorce dla Claude."""
from pathlib import Path

import pytest
from ia5.check import check_code_on, synthetic_d1, synthetic_h1

EX = sorted((Path(__file__).resolve().parents[1] / "strategies" / "examples").glob("*.py"))


@pytest.fixture(scope="module")
def syn(tmp_path_factory):
    return synthetic_h1(tmp_path_factory.mktemp("syn"), n=3000)


@pytest.fixture(scope="module")
def syn_d1(tmp_path_factory):
    return synthetic_d1(tmp_path_factory.mktemp("syn_d1"), days=2500)


@pytest.mark.parametrize("path", EX, ids=[p.stem for p in EX])
def test_example_passes(path, syn, syn_d1):
    res = check_code_on(path.read_text(encoding="utf-8"), syn, d1_dir=syn_d1)
    assert res["ok"], res["errors"]
    assert res["meta"]["hypothesis"]


def test_h1_strategy_peeking_at_unclosed_d1_day_is_caught(syn, syn_d1):
    """D-058: strategia H1 korzystająca z D1 musi widzieć tylko dni zamknięte — użycie bieżącego dnia (ffill po otwarciu)
    albo dnia przyszłego to look-ahead; ind.d1_to_h1 przenosi wartości dopiero po zamknięciu dnia."""
    peek_today = '''
def signals(df, p, ind):
    d1 = ind.d1(df)
    up = (d1.close > d1.open).reindex(df.index, method="ffill").fillna(False).astype(bool)   # dzień widoczny od jego OTWARCIA
    return (up & ind.cross_above(ind.rsi(df.close, 14), 40)).astype("int8")
'''
    res = check_code_on(peek_today, syn, d1_dir=syn_d1)
    assert not res["ok"] and any("Look-ahead" in e for e in res["errors"]), res
    honest = peek_today.replace('(d1.close > d1.open).reindex(df.index, method="ffill")', 'ind.d1_to_h1(df, d1.close > d1.open)')
    res = check_code_on(honest, syn, d1_dir=syn_d1)
    assert res["ok"], res["errors"]
    assert res["meta"]["d1_background"] and res["meta"]["timeframe"] == "H1"


def test_d1_strategy_runs_on_daily_candles_and_rejects_hours(syn, syn_d1):
    code = '''
TIMEFRAME = "D1"
HYPOTHESIS = "Dzienny powrót."
def signals(df, p, ind):
    return ind.cross_above(ind.rsi(df.close, 14), 35).astype("int8")
'''
    res = check_code_on(code, syn, d1_dir=syn_d1)
    assert res["ok"] and res["meta"]["timeframe"] == "D1" and res["meta"]["hours"] is False
    assert res["signals"]["signals"].sum() > 0
    res = check_code_on(code + "HOURS = (7, 17)\n", syn, d1_dir=syn_d1)
    assert not res["ok"] and any("HOURS" in e for e in res["errors"])
    res = check_code_on(code.replace('"D1"', '"M15"'), syn, d1_dir=syn_d1)
    assert not res["ok"] and any("TIMEFRAME" in e for e in res["errors"])
    res = check_code_on(code, syn, d1_dir=None)
    assert not res["ok"] and any("brak świec dziennych" in e for e in res["errors"])


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
