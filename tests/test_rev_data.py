"""REV (D-062): warstwa czyszczenia kursów PLN (tylko zamknięcia) i seria tygodniowa decyzji."""
import numpy as np
import pandas as pd
from ia5.rev_data import clean_pln, daily_panel, decision_times, next_decision, stale_wd, weekly_panel
from rev_fixtures import frame, london_midnight, synthetic_raw, workdays


def utc(s: str) -> int:
    return int(pd.Timestamp(s, tz="UTC").timestamp())


def warsaw(s: str) -> int:
    return int(pd.Timestamp(s).tz_localize("Europe/Warsaw").timestamp())


def walk(days, seed=3, vol=0.004):
    rng = np.random.default_rng(seed)
    return 4.0 * np.exp(np.cumsum(rng.normal(0, vol, len(days))))


def test_clean_keeps_bad_ohlc_drops_offday_and_repeats():
    days = workdays("2025-01-01", "2025-06-30")
    c = walk(days)
    c[50] = c[49]                                     # powtórzone zamknięcie → brak notowania
    raw = frame(days, c)
    raw.loc[10, "high"] = raw.loc[10, "close"] * 0.9  # zły OHLC — REV używa tylko zamknięcia, świeca zostaje
    sat = frame(["2025-03-08"], [4.0])                # sobota
    out, info = clean_pln(pd.concat([raw, sat], ignore_index=True))
    assert info["offday"] == 1 and info["repeated"] == 1
    assert int(raw.ts[10]) in set(out.ts)
    assert int(raw.ts[50]) not in set(out.ts)
    assert list(out.columns) == ["ts", "close", "close_ts", "day", "spike", "big"]


def test_spike_flag_only_when_reverted():
    days = workdays("2025-01-01", "2025-12-31")
    c = walk(days)
    k = 150
    rev = c.copy()
    rev[k] = c[k] * 1.5                              # wyskok cofnięty następnego dnia
    out, info = clean_pln(frame(days, rev))
    assert out.spike[k] and out.big[k] and not out.big[k + 1]
    assert info["spikes"] == 1
    kept = c.copy()
    kept[k:] = c[k:] * 1.5                           # skok, który się utrzymuje
    out2, _ = clean_pln(frame(days, kept))
    assert out2.big[k] and not out2.spike[k] and not out2.big[k + 1]


def test_scale_jump_rescaled():
    days = workdays("2025-01-01", "2025-12-31")
    c = walk(days)
    k = 120
    s = c.copy()
    s[k:] = c[k:] * 100                              # Yahoo zmienia skalę kwotowania na stałe
    out, info = clean_pln(frame(days, s))
    assert info["rescaled"] == [[int(london_midnight(days[k])), 100.0]]
    assert np.allclose(out.close.to_numpy()[:k], c[:k] * 100)
    assert not out.big.any()


def test_decision_times_dst():
    assert list(decision_times(utc("2026-03-23"), utc("2026-04-01"))) == [utc("2026-03-24 07:00"), utc("2026-03-31 06:00")]
    assert list(decision_times(utc("2026-10-19"), utc("2026-10-28"))) == [utc("2026-10-20 06:00"), utc("2026-10-27 07:00")]
    assert next_decision(utc("2026-11-11 10:00")) == utc("2026-11-17 07:00")
    assert next_decision(utc("2026-11-10 07:00")) == utc("2026-11-10 07:00")


def _ready(days, c):
    return clean_pln(frame(days, c))[0]


def test_weekly_price_uses_monday_close():
    days = workdays("2026-01-01", "2026-11-10")
    r = {"EUR": _ready(days, walk(days))}
    t = np.array([warsaw("2026-11-10 08:00")])
    p, pts = weekly_panel(r, ["EUR", "PLN"], t)
    assert pts.loc[t[0], "EUR"] == london_midnight("2026-11-09")
    assert p.loc[t[0], "PLN"] == 1.0


def test_weekly_price_holiday_monday():
    days = workdays("2023-06-01", "2024-01-31")
    r = {"EUR": _ready(days, walk(days))}
    t = np.array([warsaw("2024-01-02 08:00")])
    _, pts = weekly_panel(r, ["EUR", "PLN"], t)
    assert pts.loc[t[0], "EUR"] == london_midnight("2023-12-29")


def test_stale_limit():
    t = warsaw("2026-11-10 08:00")
    assert stale_wd("2026-11-09", t) == 1
    assert stale_wd("2026-11-03", t) == 5
    assert stale_wd("2026-11-02", t) == 6
    days = workdays("2026-01-01", "2026-11-02")       # ostatnia świeca 6 dni roboczych przed decyzją
    r = {"EUR": _ready(days, walk(days))}
    p, _ = weekly_panel(r, ["EUR", "PLN"], np.array([t]))
    assert np.isnan(p.loc[t, "EUR"])


def test_guard_big_on_decision_day():
    days = workdays("2025-01-01", "2026-11-17")
    c = walk(days)
    k = days.index("2026-11-09")                      # wyskok w poniedziałek, cofnięty we wtorek
    c[k] *= 1.5
    t1, t2 = warsaw("2026-11-10 08:00"), warsaw("2026-11-17 08:00")
    for until in ("2026-11-09", "2026-11-17"):        # bez wtorku i z wtorkiem — ta sama decyzja
        n = days.index(until) + 1
        p, _ = weekly_panel({"EUR": _ready(days[:n], c[:n])}, ["EUR", "PLN"], np.array([t1, t2]))
        assert np.isnan(p.loc[t1, "EUR"]), until
    assert np.isfinite(p.loc[t2, "EUR"])


def test_panel_no_lookahead():
    raw = synthetic_raw(["EUR", "USD"], start="2020-01-01", end="2026-11-10", seed=5)
    full = {k: clean_pln(v)[0] for k, v in raw.items()}
    times = decision_times(utc("2021-01-01"), utc("2026-11-10"))
    p0, t0 = weekly_panel(full, ["EUR", "USD", "PLN"], times)
    rng = np.random.default_rng(1)
    for D in rng.choice(times[:-2], 20, replace=False):
        cut = {}
        for k, v in raw.items():
            v = v.copy()
            after = v.ts.to_numpy() > D
            v.loc[after, ["open", "high", "low", "close"]] *= 2.0
            cut[k] = clean_pln(v)[0]
        p1, t1 = weekly_panel(cut, ["EUR", "USD", "PLN"], times)
        keep = times <= D
        pd.testing.assert_frame_equal(p0[keep], p1[keep])
        pd.testing.assert_frame_equal(t0[keep], t1[keep])


def test_exec_lag_uses_tuesday_close():
    days = workdays("2026-01-01", "2026-11-12")
    r = {"EUR": _ready(days, walk(days))}
    t = np.array([warsaw("2026-11-10 08:00")])
    _, pts = weekly_panel(r, ["EUR", "PLN"], t, exec_lag_days=1)
    assert pts.loc[t[0], "EUR"] == london_midnight("2026-11-10")


def test_daily_panel_guard_and_ffill():
    days = workdays("2026-01-01", "2026-06-30")
    a = walk(days, seed=1)
    b = walk(days, seed=2)
    k = 80
    a[k] *= 1.5                                       # wyskok A → wartość dnia poprzedniego
    gap3 = set(range(100, 103))                       # B: 3 dni bez świecy → uzupełnione
    gap6 = set(range(120, 126))                       # B: 6 dni → brak wartości
    keep = [i for i in range(len(days)) if i not in gap3 | gap6]
    r = {"A": _ready(days, a), "B": _ready([days[i] for i in keep], b[keep])}
    d = daily_panel(r, ["A", "B", "PLN"])
    ix = r["A"].close_ts.to_numpy()
    assert d.loc[ix[k], "A"] == r["A"].close.iloc[k - 1]
    assert d.loc[ix[102], "B"] == b[99]
    assert np.isnan(d.loc[ix[125], "B"])
    assert (d["PLN"] == 1.0).all()
