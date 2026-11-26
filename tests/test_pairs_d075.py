"""D-075: strategia widzi wszystkie pary (ind.pairs, ind.pair_close, ind.strength) bez look-ahead."""
import pytest
from ia5.check import check_code_on, synthetic_d1, synthetic_h1


@pytest.fixture(scope="module")
def syn(tmp_path_factory):
    return synthetic_h1(tmp_path_factory.mktemp("syn"), n=2500)


@pytest.fixture(scope="module")
def syn_d1(tmp_path_factory):
    return synthetic_d1(tmp_path_factory.mktemp("syn_d1"), days=1500)


STRENGTH = '''
HYPOTHESIS = "Silniejsza waluta bazowa od słabszej kwotowanej — momentum przekrojowe."
def signals(df, p, ind):
    s = ind.strength(df, 24)
    pair = df.attrs["pair"]
    diff = s[pair[:3]] - s[pair[3:]]
    return ind.cross_above(diff, 0).astype("int8") - ind.cross_below(diff, 0).astype("int8")
'''


def test_strength_strategy_passes_and_uses_other_pairs(syn, syn_d1):
    res = check_code_on(STRENGTH, syn, d1_dir=syn_d1)
    assert res["ok"], res["errors"]
    assert res["meta"]["cross_pairs"]
    assert res["signals"]["signals"].sum() > 0


def test_d1_strength_and_pair_close(syn, syn_d1):
    code = 'TIMEFRAME = "D1"\n' + STRENGTH.replace("24)", "20)") + '''
def _unused(df, ind):
    return ind.pair_close(df, "USDJPY")
'''
    res = check_code_on(code, syn, d1_dir=syn_d1)
    assert res["ok"], res["errors"]


def test_peeking_into_other_pair_future_is_caught(syn, syn_d1):
    cheat = '''
HYPOTHESIS = "Oszustwo: jutrzejsza cena USD/JPY."
def signals(df, p, ind):
    other = ind.pairs(df)["USDJPY"]["close"].shift(-1).reindex(df.index, method="ffill")
    return (other > ind.pair_close(df, "USDJPY")).astype("int8")
'''
    res = check_code_on(cheat, syn, d1_dir=syn_d1)
    assert not res["ok"] and any("ook-ahead" in e for e in res["errors"]), res["errors"]


def test_without_pair_api_no_cross_data(syn, syn_d1):
    code = 'HYPOTHESIS = "x"\ndef signals(df, p, ind):\n    return ind.cross_above(ind.rsi(df.close, 14), 30).astype("int8")\n'
    res = check_code_on(code, syn, d1_dir=syn_d1)
    assert res["ok"] and not res["meta"]["cross_pairs"]
