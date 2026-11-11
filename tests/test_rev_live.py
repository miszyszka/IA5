"""REV (D-063): portfel na żywo — wtorek 08:00, wycena dzienna, dziennik tylko dopisywany, nadrabianie = krok po kroku."""
import json

import numpy as np
import pandas as pd
import pytest
from ia5 import rev_method as rm
from ia5.daily import close_ts
from ia5.rev_config import baskets
from ia5.rev_data import clean_pln, decision_times, weekly_panel
from ia5.rev_live import live_step

CODES = ["EUR", "USD", "CHF", "GBP", "NOK", "SEK"]
W = "Europe/Warsaw"


def ts(s: str, tz: str = W) -> int:
    return int(pd.Timestamp(s).tz_localize(tz).tz_convert("UTC").timestamp())


@pytest.fixture(scope="module")
def raw():
    from rev_fixtures import synthetic_raw

    return synthetic_raw(CODES, start="2015-01-01", end="2026-12-31", seed=31)


def ready_at(raw: dict, now: int, edit=None) -> tuple[dict, dict]:
    """Dane tak, jak wyglądały w chwili `now`: tylko świece zamknięte (close_ts ≤ now), po warstwie czyszczenia."""
    out, infos = {}, {}
    for c, df in raw.items():
        d = df[close_ts(df["ts"].to_numpy("int64")) <= now]
        if edit:
            d = edit(c, d.copy())
        out[c], infos[c] = clean_pln(d)
    return out, infos


def research(frozen_id="V5-R", at="2026-11-17 08:00"):
    return {"rev_version": "1", "universe": baskets(CODES), "blocs": {},
            "periods": {"start_ts": ts("2021-01-05 08:00")},
            "frozen": {"id": frozen_id, "label": rm.VARIANT_BY_ID[frozen_id].label, "code_hash": "abc123",
                       "at": ts(at), "rev_version": "1"}}


def roundtrip(st):
    return json.loads(json.dumps(st, allow_nan=False))


def test_waits_for_research_moment(raw):
    now = ts("2026-11-14 12:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    assert st["start_ts"] == ts("2026-11-17 08:00")
    assert st["ledger"] == [] and st["valuation"] == [] and st["next_rebalance"] == st["start_ts"]
    assert st["units"]["PLN"] == 10_000


def test_first_split_right_after_research_d064(raw):
    """D-064 (Michał: „możemy zrobić już pierwszy podział teraz?”): start od razu po badaniu, cena z ostatniego zamkniętego
    dnia; kolejne przeliczenia co wtorek 08:00."""
    at = "2026-11-11 15:41"
    now = ts("2026-11-11 16:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(at=at), r, now, i)
    assert st["start_ts"] == ts(at) and len(st["rebalances"]) == 1
    assert st["rebalances"][0]["ts"] == ts(at) and st["rebalances"][0]["price_day"] == "2026-11-10"
    assert {x["price_day"] for x in st["ledger"] if x["basket"] != "PLN"} == {"2026-11-10"}
    assert st["next_rebalance"] == ts("2026-11-17 08:00")
    later = ts("2026-11-17 09:00")
    r2, i2 = ready_at(raw, later)
    st2 = live_step(roundtrip(st), research(at=at), r2, later, i2)
    assert [x["ts"] for x in st2["rebalances"]] == [ts(at), ts("2026-11-17 08:00")]
    once = live_step(None, research(at=at), r2, later, i2)        # nadrabianie = krok po kroku
    assert once["ledger"] == st2["ledger"]


def test_first_rebalance_from_pln(raw):
    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    assert len(st["rebalances"]) == 1
    assert abs(sum(x["value_pln"] for x in st["ledger"])) < 1e-6
    assert st["units"]["PLN"] < 10_000
    assert max(st["rebalances"][0]["weights"].values()) <= 0.5 + 1e-9
    assert abs(sum(st["today"]["weights"].values()) - 1) < 1e-9
    assert st["next_rebalance"] == ts("2026-11-24 08:00")


def test_valuation_every_weekday(raw):
    now = ts("2026-12-01 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    days = [pd.Timestamp(t - 1, unit="s", tz="UTC").tz_convert("Europe/London") for t, _, _ in st["valuation"]]
    assert len(days) == 10
    assert all(d.weekday() < 5 for d in days)
    assert len(st["rebalances"]) == 3


def test_late_monday_waits_until_20(raw):
    monday = ts("2026-11-16 00:00", "Europe/London")

    def drop(c, d):
        return d[d["ts"] != monday] if c == "NOK" else d

    early = ts("2026-11-17 09:00")
    r, i = ready_at(raw, early, drop)
    st = live_step(None, research(), r, early, i)
    assert st["rebalances"] == []
    late = ts("2026-11-17 20:01")
    r, i = ready_at(raw, late, drop)
    st = live_step(roundtrip(st), research(), r, late, i)
    assert len(st["rebalances"]) == 1 and st["rebalances"][0]["late"] == ["NOK"]
    rows = [x for x in st["ledger"] if x["basket"] == "NOK"]
    assert all(x["price_day"] == "2026-11-13" for x in rows)


def test_catch_up_equals_stepwise(raw):
    t0, t1 = ts("2026-11-14 00:00"), ts("2026-12-05 00:00")
    st = None
    for now in range(t0, t1 + 1, 6 * 3600):
        r, i = ready_at(raw, now)
        st = live_step(roundtrip(st) if st else None, research(), r, now, i)
    r, i = ready_at(raw, t1)
    once = live_step(None, research(), r, t1, i)
    assert len(st["ledger"]) == len(once["ledger"]) > 0
    for a, b in zip(st["ledger"], once["ledger"]):
        assert a.keys() == b.keys()
        for k in a:
            assert (np.isclose(a[k], b[k]) if isinstance(a[k], float) else a[k] == b[k]), k
    assert np.allclose(np.array(st["valuation"]), np.array(once["valuation"]))
    assert np.allclose([st["units"][c] for c in st["universe"]], [once["units"][c] for c in once["universe"]])


def test_settled_rows_never_change(raw):
    now1 = ts("2026-11-25 12:00")
    r, i = ready_at(raw, now1)
    st1 = live_step(None, research(), r, now1, i)
    fix_day = ts("2026-11-16 00:00", "Europe/London")

    def fix(c, d):
        if c == "EUR":
            d.loc[d["ts"] == fix_day, "close"] *= 1.03            # Yahoo poprawia kurs sprzed ponad tygodnia
        return d

    now2 = ts("2026-11-26 12:00")
    r, i = ready_at(raw, now2, fix)
    st2 = live_step(roundtrip(st1), research(), r, now2, i)
    assert st2["ledger"][: len(st1["ledger"])] == st1["ledger"]
    assert st2["valuation"][: len(st1["valuation"])] == st1["valuation"]
    assert len(st2["valuation"]) > len(st1["valuation"])


def test_method_change_restarts_and_archives(raw):
    now = ts("2026-11-25 12:00")
    r, i = ready_at(raw, now)
    st1 = live_step(None, research(), r, now, i)
    r2 = research("M3-P", "2026-11-25 10:00")
    r2["frozen"]["code_hash"] = "def456"
    st2 = live_step(roundtrip(st1), r2, r, now, i)
    assert st2["method"]["id"] == "M3-P" and st2["start_ts"] == ts("2026-11-25 10:00")
    assert [x["ts"] for x in st2["rebalances"]] == [ts("2026-11-25 10:00")] and len(st2["archive"]) == 1
    assert st2["archive"][0]["method"]["id"] == "V5-R" and st2["archive"][0]["final"] > 0


def test_stale_held_currency_frozen(raw):
    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    held = [c for c in CODES if st["units"][c] > 0][0]
    gone_from = ts("2026-11-17 00:00", "Europe/London")

    def stop(c, d):
        return d[d["ts"] < gone_from] if c == held else d      # waluta przestaje być notowana na 8 dni roboczych

    now2 = ts("2026-11-27 12:00")
    r2, i2 = ready_at(raw, now2, stop)
    st2 = live_step(roundtrip(st), research(), r2, now2, i2)
    assert st2["units"][held] == st["units"][held]
    assert not [x for x in st2["ledger"][len(st["ledger"]):] if x["basket"] == held]
    assert held in st2["rebalances"][-1]["frozen"]
    last_close = float(r2[held]["close"].iloc[-1])
    v = st2["today"]["values"][held]
    assert np.isclose(v, st2["units"][held] * last_close)


def test_scale_event_adjusts_units(raw):
    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    held = [c for c in CODES if st["units"][c] > 0][0]
    jump = ts("2026-11-19 00:00", "Europe/London")

    def scale(c, d):
        if c == held:
            d.loc[d["ts"] >= jump, ["open", "high", "low", "close"]] *= 100.0   # Yahoo zmienia skalę kwotowania
        return d

    for now in (ts("2026-11-19 12:00"), ts("2026-11-20 12:00"), ts("2026-11-21 12:00"), ts("2026-11-24 12:00")):
        r2, i2 = ready_at(raw, now, scale)
        st = live_step(roundtrip(st), research(), r2, now, i2)
    assert st["scale_applied"] and st["scale_applied"][0][1] == held
    vals = np.array([v for _, v, _ in st["valuation"]])
    assert (np.abs(np.diff(np.log(vals))) < 0.05).all()


def test_switcher_live_uses_prices_only(raw):
    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research("SW"), r, now, i)
    assert not any(k for k in st if "portfolio" in k or "shadow" in k)
    D = ts("2026-11-17 08:00")
    times = decision_times(int(min(f["close_ts"].iloc[0] for f in r.values())), D)
    prices, _ = weekly_panel(r, baskets(CODES), times)
    elig = rm.eligible(prices)
    start = int(np.searchsorted(times, ts("2021-01-05 08:00")))
    eqt = rm.equal_targets(elig)
    eq = rm.simulate(prices, eqt, None, band=0.0, start=start)
    tg, od, ex = {}, {}, {}
    for v in rm.STATIC:
        tg[v.id], od[v.id] = rm.variant_targets(prices, elig, v)
        ex[v.id] = rm.simulate(prices, tg[v.id], od[v.id], start=start).ret.reindex(prices.index) - eq.ret.reindex(prices.index)
    _, chosen, _ = rm.switcher_targets(pd.DataFrame(ex), tg, eqt, start, od)
    assert st["rebalances"][0]["variant"] == chosen.iloc[-1]


def test_missing_currency_file_keeps_last_price(raw):
    """Przegląd: brak pliku waluty (np. nieudana synchronizacja) — wycena po ostatniej znanej cenie, nie zero."""
    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now)
    st = live_step(None, research(), r, now, i)
    held = max(CODES, key=lambda c: st["units"][c])
    now2 = ts("2026-11-19 12:00")
    r2, i2 = ready_at(raw, now2)
    r2.pop(held)
    i2.pop(held)
    st2 = live_step(roundtrip(st), research(), r2, now2, i2)
    vals = np.array([v for _, v, _ in st2["valuation"]])
    assert (np.abs(np.diff(np.log(vals))) < 0.05).all()            # bez skoku o wartość brakującej waluty
    assert st2["today"]["values"][held] > 0


def test_unchanged_monday_close_does_not_delay(raw):
    """Przegląd: zamknięcie poniedziałku = piątku (warstwa czyszczenia je usuwa) — przeliczenie i tak o 08:00, nie o 20:00."""
    monday, friday = ts("2026-11-16 00:00", "Europe/London"), ts("2026-11-13 00:00", "Europe/London")

    def flat(c, d):
        if c == "CHF" and (d["ts"] == monday).any():
            d.loc[d["ts"] == monday, "close"] = float(d.loc[d["ts"] == friday, "close"].iloc[0])
        return d

    now = ts("2026-11-17 09:00")
    r, i = ready_at(raw, now, flat)
    st = live_step(None, research(), r, now, i)
    assert len(st["rebalances"]) == 1
