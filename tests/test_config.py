from ia5.cli import main
from ia5.config import PAIRS, spread_price


def test_eight_pairs():
    assert len(PAIRS) == 8


def test_jpy_pip():
    for name, p in PAIRS.items():
        assert p.pip == (0.01 if "JPY" in name else 0.0001)


def test_spreads_from_brief():
    expected = {"EURUSD": 0.9, "USDJPY": 1.4, "GBPUSD": 1.5, "EURGBP": 1.7,
                "AUDUSD": 1.7, "USDCHF": 1.9, "USDCAD": 2.0, "EURJPY": 2.1}
    assert {k: p.spread_pips for k, p in PAIRS.items()} == expected
    assert abs(spread_price("USDJPY") - 0.014) < 1e-12


def test_cli_status():
    assert main(["status"]) == 0
