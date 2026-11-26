"""D-075: zasady portfela — stawka od ryzyka, cel zmienności, limit ekspozycji na walutę, hamulec konta."""
import numpy as np
import pandas as pd
import pytest
from ia5.investors import book, merge_rules
from ia5.portfolio import simulate_equity, vol_scale
from ia5.sandbox import StrategyError, read_settings

T = 1_700_000_000 // 86400 * 86400


def tr(rows):
    """rows: (para, dir, wejście [dni], wyjście [dni], pips netto, risk_pips)."""
    return pd.DataFrame([{"pair": p, "dir": d, "entry_ts": T + int(a * 86400), "exit_ts": T + int(b * 86400), "pips_net": pn,
                          "entry_px": 1.0, "risk_pips": rp, "weight": 1.0, "mae": 0.0} for p, d, a, b, pn, rp in rows])


def test_risk_sizing_loses_exactly_risk_at_sl():
    t = tr([("EURUSD", 1, 0, 1, -20, 20)])          # strata = pełna odległość do SL
    c = simulate_equity(t, 1.0, rules={"sizing_mode": "risk"})
    assert c["final"] == pytest.approx(10_000 * 0.99)
    t2 = tr([("EURUSD", 1, 0, 1, -40, 40)])          # SL dwa razy dalej → ta sama strata w USD (pozycja o połowę mniejsza)
    assert simulate_equity(t2, 1.0, rules={"sizing_mode": "risk"})["final"] == pytest.approx(9_900)
    assert simulate_equity(t2, 10)["final"] != pytest.approx(9_900)   # tryb depozytu: strata rośnie z odległością


def test_risk_sizing_capped_by_free_margin():
    t = tr([("EURUSD", 1, 0, 1, 1, 0.5)])            # bardzo bliski SL → wymagany depozyt > 100% kapitału
    c = simulate_equity(t, 2.0, rules={"sizing_mode": "risk"})
    assert c["capped"] == 1 and c["taken"] == 1
    assert c["final"] == pytest.approx(10_000 + 10_000 * 30 * 1 * 0.0001)


def test_max_ccy_blocks_same_currency_stack():
    t = tr([("EURUSD", -1, 0, 5, 1, 10), ("GBPUSD", -1, 1, 5, 1, 10), ("AUDUSD", -1, 2, 5, 1, 10), ("USDJPY", -1, 3, 5, 1, 10)])
    c = simulate_equity(t, 5, rules={"max_ccy": 2})
    # short EUR/USD i GBP/USD = +2 USD; short AUD/USD = +3 USD → pominięte; short USD/JPY = −1 USD → wolno
    assert c["skipped_ccy"] == 1 and c["taken"] == 3


def test_brake_pauses_after_drawdown_then_resumes():
    t = tr([("EURUSD", 1, 0, 1, -100, 20), ("EURUSD", 1, 2, 3, 10, 20), ("EURUSD", 1, 40, 41, 10, 20)])
    c = simulate_equity(t, 30, rules={"brake": [5, 30]})
    assert c["skipped_brake"] == 1 and c["taken"] == 2          # druga w pauzie, trzecia po 30 dniach już tak


def test_vol_scale_bounds_and_history():
    assert vol_scale([], [], T, 10) == 1.0
    days = list(range(T // 86400 - 70, T // 86400))
    calm = [10_000 * (1 + 0.0001 * k) for k in range(len(days))]
    wild = [10_000 * (1 + 0.05 * (-1) ** k) for k in range(len(days))]
    assert vol_scale(days, calm, T, 10) == 2.0                   # bardzo spokojny kapitał → maks. skala
    assert vol_scale(days, wild, T, 10) == 0.25                  # bardzo nerwowy → min. skala
    assert vol_scale(days[-5:], calm[-5:], T, 10) == 1.0         # za krótka historia


def test_vol_target_uses_only_past():
    rng = np.random.default_rng(3)
    rows = [("EURUSD", 1, k, k + 0.5, float(rng.normal(0, 30)), 20) for k in range(120)]
    t = tr(rows)
    full = simulate_equity(t, 10, rules={"vol_target": 8})
    part = simulate_equity(t.iloc[:60], 10, rules={"vol_target": 8})
    assert full["equity"][:61] == pytest.approx(part["equity"])  # przyszłe transakcje nie zmieniają przeszłych stawek


def test_settings_validation():
    s = read_settings({"SIZING_MODE": "risk", "SIZING": [0.5, 1], "VOL_TARGET": 10, "MAX_CCY": 2, "BRAKE": (10, 20)})
    assert s["sizing_mode"] == "risk" and s["vol_target"] == 10 and s["max_ccy"] == 2 and s["brake"] == [10, 20]
    assert "sizing_mode" not in read_settings({})       # domyślnie B4 — bez nowych kluczy
    for bad in ({"SIZING_MODE": "kelly"}, {"SIZING_MODE": "risk", "SIZING": [10]}, {"VOL_TARGET": 0}, {"MAX_CCY": 0},
                {"BRAKE": (10,)}, {"BRAKE": (0, 5)}):
        with pytest.raises(StrategyError):
            read_settings(bad)


def test_investor_book_applies_rules():
    t = tr([("EURUSD", -1, 0, 5, 1, 10), ("GBPUSD", -1, 1, 5, 1, 10), ("AUDUSD", -1, 2, 5, 1, 10)])
    t["status"] = "zamknięta"
    b = book(t, 10_000, 5, rules={"max_ccy": 2})
    assert (b["trades"]["status"] == "pominięta: limit na walutę").sum() == 1
    assert merge_rules([{"max_ccy": 3, "brake": [10, 5]}, {"max_ccy": 2, "brake": [5, 20], "vol_target": 9}, {}]) == \
        {"max_ccy": 2, "vol_target": 9, "brake": [5, 20]}
