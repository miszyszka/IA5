"""REV (D-063): waluty, bloki o sztywnym kursie, koszyki."""
from ia5.rev_config import BLOCS, CANDIDATES, baskets, bloc_of


def test_candidates():
    assert len(CANDIDATES) == 24
    assert "RUB" not in CANDIDATES
    for anchor, members in BLOCS.items():
        assert anchor in CANDIDATES
        assert all(m in CANDIDATES for m in members)


def test_baskets_merge_blocs():
    b = baskets(CANDIDATES)
    assert len(b) == 20 and b[-1] == "PLN"
    assert not {"HKD", "AED", "SAR", "QAR", "DKK"} & set(b)
    assert b[:-1] == sorted(b[:-1])


def test_member_without_anchor_dropped():
    assert baskets(["HKD", "CHF"]) == ["CHF", "PLN"]


def test_bloc_of():
    assert bloc_of("HKD") == "USD"
    assert bloc_of("DKK") == "EUR"
    assert bloc_of("CHF") == "CHF"
