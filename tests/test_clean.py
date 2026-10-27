"""D-031: warstwa czyszczenia (uzupełnianie pojedynczych świec, długie luki), anulowanie transakcji na lukach,
zatwierdzanie miesięcy i pobieracz „para po parze do końca” — na podłożonych danych, bez sieci."""
from datetime import date

import numpy as np
import pandas as pd
import pytest
from ia5 import dukascopy, fetch
from ia5.clean import FILL_MAX, clean_h1
from ia5.engine import Exit, data_cancel, prepare, run

T0 = 1761523200  # poniedziałek 2025-10-27 00:00 UTC
H = 3600


def walk(n, seed=1):
    rng = np.random.default_rng(seed)
    c = 1.1 + np.cumsum(rng.normal(0, 0.0005, n))
    o = np.concatenate([[1.1], c[:-1]])
    df = pd.DataFrame({"ts": T0 + H * np.arange(n), "open": o, "high": np.maximum(o, c) + 0.0003,
                       "low": np.minimum(o, c) - 0.0003, "close": c})
    df["bid_close"], df["ask_close"], df["spread_avg"], df["minutes"] = c - 0.00005, c + 0.00005, 0.0001, 60
    return df


def test_single_missing_bar_is_filled_and_marked():
    raw = walk(30)
    hole = raw.iloc[10]
    df, info = clean_h1(raw.drop(index=10))
    row = df[df.ts == hole.ts].iloc[0]
    assert bool(row.filled) and row.minutes == 0
    assert row.open == pytest.approx(raw.close[9]) and row.close == pytest.approx(raw.open[11])  # od zamknięcia do otwarcia
    assert row.high == max(row.open, row.close) and row.low == min(row.open, row.close)
    assert info["filled"] == 1 and info["gaps"] == [] and df.gap_before.sum() == 0
    assert len(df) == 30 and df.filled.sum() == 1          # dane surowe: nic nie zmienione poza dopisaną świecą
    pd.testing.assert_frame_equal(df[~df.filled].drop(columns=["filled", "gap_before"]).reset_index(drop=True),
                                  raw.drop(index=10).reset_index(drop=True), check_dtype=False)


def test_three_hours_filled_linearly_longer_quiet_hole_is_not_a_barrier():
    raw = walk(40)
    df3, i3 = clean_h1(raw.drop(index=[10, 11, 12]))
    assert i3["filled"] == FILL_MAX == 3
    f = df3[df3.filled]
    assert f.close.iloc[-1] == pytest.approx(raw.open[13]) and f.open.iloc[0] == pytest.approx(raw.close[9])
    # D-032: 4 godziny bez notowań w pobranym dniu — ani uzupełnienie, ani bariera (jak weekend)
    df4, i4 = clean_h1(raw.drop(index=[20, 21, 22, 23]))
    assert i4["filled"] == 0 and i4["gaps"] == [] and i4["quiet_runs"] == 1 and df4.gap_before.sum() == 0


def test_access_gap_is_a_barrier_even_when_short():
    raw = walk(40)
    hole = [int(raw.ts[20]), int(raw.ts[22]) + H]           # dzień niedostępny obejmuje te godziny
    df, info = clean_h1(raw.drop(index=[20, 21, 22]), unavailable=[hole])
    assert info["filled"] == 0 and info["gaps"] == [[hole[0], hole[1], 3]]
    assert df.loc[df.ts == raw.ts[23], "gap_before"].item() == 3


def test_weekend_and_holiday_are_not_gaps():
    # piątek 2025-10-31 18:00 → poniedziałek: brak świec w weekend to nie luka; 24–25.12 to święto
    fri = pd.DataFrame({"ts": [1761933600 + H * k for k in range(3)]})  # pt 18, 19, 20 UTC
    mon = pd.DataFrame({"ts": [1762128000 + H * k for k in range(2)]})  # pn 00, 01 UTC
    sun = pd.DataFrame({"ts": [1762120800 + H * k for k in range(2)]})  # nd 22, 23 UTC
    df = pd.concat([fri, sun, mon], ignore_index=True)
    for c in ("open", "high", "low", "close"):
        df[c] = 1.1
    out, info = clean_h1(df)
    assert info["filled"] == 0 and info["gaps"] == []


def test_engine_cancels_trades_on_access_gap_and_filled_entry():
    full = walk(60)
    raw = full.drop(index=[20] + list(range(40, 45)))   # 1 świeca (uzupełniona) i 5 godzin bez dostępu do danych
    df, info = clean_h1(raw, unavailable=[[int(full.ts[40]), int(full.ts[44]) + H]])
    assert info["filled"] == 1 and len(info["gaps"]) == 1
    idx = {int(t): i for i, t in enumerate(df.ts)}
    sig = np.zeros(len(df), np.int8)
    for h in (19, 25, 37):   # wejście na uzupełnionej świecy; czysta transakcja; transakcja przez przerwę
        sig[idx[T0 + h * H]] = 1
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=4, cap=4)], hours=False)
    out = res["outcomes"]
    assert res["skipped"]["luka_danych"] == 1 and res["skipped"]["swieca_uzupelniona"] == 1
    assert len(out) == 1
    ent = res["entries"].set_index("entry_id").loc[out.entry_id.iloc[0]]
    assert ent.entry_ts == T0 + 26 * H


def test_trade_through_weekend_is_not_cancelled():
    """D-032: po ostatniej piątkowej świecy następna jest niedzielna/poniedziałkowa — weekend nie jest barierą."""
    fri = 1761868800  # piątek 2025-10-31 00:00 UTC
    ts = [fri + H * k for k in range(21)] + [1762120800 + H * k for k in range(30)]  # pt 00–20, nd 22 → pn
    n = len(ts)
    c = 1.1 + np.arange(n) * 1e-5
    df = pd.DataFrame({"ts": ts, "open": c, "high": c + 2e-4, "low": c - 2e-4, "close": c})
    df, info = clean_h1(df)
    assert info["gaps"] == [] and info["filled"] == 0
    sig = np.zeros(n, np.int8)
    sig[18] = 1  # piątek 18:00 UTC (po rozgrzewce ATR) → wejście 19:00, wyjście po 6 świecach = niedziela/poniedziałek
    res = run({"EURUSD": df}, {(0, "EURUSD"): sig}, [{}], exits=[Exit("time", n=6, cap=6)], hours=False)
    t = res["outcomes"].iloc[0]
    assert res["skipped"]["luka_danych"] == 0 and t["reason"] == "czas" and t["exit_ts"] > 1762120800


def test_data_cancel_rules():
    full = walk(30)
    df, _ = clean_h1(full.drop(index=[10] + list(range(20, 25))), unavailable=[[int(full.ts[20]), int(full.ts[24]) + H]])
    P = prepare(df)
    i_f = int(np.flatnonzero(P["filled"])[0])           # świeca uzupełniona
    i_g = int(np.flatnonzero(df.gap_before.to_numpy())[0])  # pierwsza świeca po przerwie w dostępie do danych
    c = data_cancel(P, np.array([i_f, i_f - 2, i_f - 3, i_g - 3, i_g - 1, 2]),
                    np.array([i_f + 1, i_f - 1, i_f - 2, i_g - 2, i_g, 3]),
                    np.array([i_f + 2, i_f, i_f + 1, i_g, i_g + 1, 5.0]))
    # sygnał na uzupełnionej · wyjście na uzupełnionej · przez uzupełnioną (dozwolone) · przez przerwę · przerwa przed wejściem · czysta
    assert c.tolist() == [True, True, False, True, True, False]


def test_unavailable_ranges_from_months_and_given_up_days(tmp_path):
    from ia5 import ready

    f = tmp_path / "m1" / "EURUSD"
    f.mkdir(parents=True)
    (f / "2024-03.missing.json").write_text('{"missing": {}, "given_up": ["2024-03-05"]}')
    r = ready.unavailable_ranges(tmp_path, "EURUSD", ["2024-01", "2024-03"])
    ts = lambda *a: int(pd.Timestamp(*a, tz="UTC").timestamp())  # noqa: E731
    assert r == [[ts(2024, 2, 1), ts(2024, 3, 1)], [ts(2024, 3, 5), ts(2024, 3, 6)]]


# ---------- zatwierdzanie miesięcy i pobieracz ----------

def patch_clock(monkeypatch, y=2024, m=3, d=10):
    class Today(dukascopy.datetime):
        @classmethod
        def now(cls, tz=None):
            return dukascopy.datetime(y, m, d, 6, tzinfo=tz)

    monkeypatch.setattr(dukascopy, "datetime", Today)


def fake_m1(d):
    t = int(pd.Timestamp(d, tz="UTC").timestamp()) + 10 * H
    return pd.DataFrame([[t + 60 * i, 1, 1.001, 0.999, 1, 1, 1.0001, 1.0011, 0.9991, 1.0001, 1] for i in range(60)],
                        columns=dukascopy.COLS)


@pytest.fixture
def quiet(monkeypatch):
    monkeypatch.setattr(dukascopy, "START", date(2024, 1, 1))
    monkeypatch.setattr(dukascopy, "COOLDOWN", 0)
    monkeypatch.setattr(dukascopy, "BLOCK_PAUSE", (0, 0))
    patch_clock(monkeypatch)


def test_month_with_missing_day_is_not_ready_until_given_up(tmp_path, monkeypatch, quiet):
    calls = []

    def fake(pair, d, *a):
        calls.append((pair, d))
        if d == date(2024, 2, 7):
            raise RuntimeError("HTTP 503")
        return fake_m1(d)

    monkeypatch.setattr(dukascopy, "fetch_day", fake)
    folder = tmp_path / "m1" / "EURUSD"
    dukascopy.sync_pair("EURUSD", tmp_path, log=lambda m: None)
    st = dukascopy.pair_status(tmp_path, "EURUSD")
    assert "2024-02" not in st["ready"] and st["missing_days"] == 1 and not st["complete"]
    assert st["ready"] == ["2024-01", "2024-03"]
    st = fetch.fetch_pair("EURUSD", tmp_path, log=lambda m: None, sleep=lambda s: None)
    side = dukascopy.read_sidecar(folder / "2024-02.parquet")
    assert side == {"missing": {}, "given_up": ["2024-02-07"]}            # po GIVE_UP próbach — niedostępny
    assert st["complete"] and st["given_up"] == 1
    # GIVE_UP rund: pierwsza szybka (1 próba), kolejne naprawcze (po REPAIR["tries"] prób)
    assert sum(1 for c in calls if c[1] == date(2024, 2, 7)) == 1 + (dukascopy.GIVE_UP - 1) * dukascopy.REPAIR["tries"]


def test_recent_missing_day_is_never_given_up(tmp_path, monkeypatch, quiet):
    def fake(pair, d, *a):
        if d == date(2024, 3, 6):  # 3 dni temu — Dukascopy może jeszcze publikować
            raise RuntimeError("HTTP 503")
        return fake_m1(d)

    monkeypatch.setattr(dukascopy, "fetch_day", fake)
    monkeypatch.setattr(fetch, "NO_PROGRESS", 3)
    st = fetch.fetch_pair("EURUSD", tmp_path, log=lambda m: None, sleep=lambda s: None)
    assert not st["complete"] and st["missing_days"] == 1 and st["given_up"] == 0


def test_fetcher_finishes_one_pair_before_the_next(tmp_path, monkeypatch, quiet):
    monkeypatch.setattr(fetch, "PAIRS", {"USDJPY": None, "EURUSD": None, "GBPUSD": None})
    order, tries = [], {}

    def fake(pair, d, *a):
        order.append(pair)
        if pair == "EURUSD" and d == date(2024, 1, 15):
            tries[d] = tries.get(d, 0) + 1
            if tries[d] < 3:  # dzień odrzucany dwa razy, potem schodzi
                raise RuntimeError("timeout")
        return fake_m1(d)

    class Stop(Exception):
        pass

    def sleep(s):
        if s == fetch.IDLE:
            raise Stop

    monkeypatch.setattr(dukascopy, "fetch_day", fake)
    state = {}
    with pytest.raises(Stop):
        fetch.run_forever(tmp_path, log=lambda m: None, state=state, sleep=sleep)
    first = [p for i, p in enumerate(order) if p not in order[:i]]
    assert first == ["EURUSD", "USDJPY", "GBPUSD"]               # najpierw para do liczenia
    last_eur = max(i for i, p in enumerate(order) if p == "EURUSD")
    assert last_eur < order.index("USDJPY")                     # EUR/USD skończona, zanim ruszyła następna
    assert state["state"] == "komplet" and state["pairs"] == {"EURUSD": 100.0, "USDJPY": 100.0, "GBPUSD": 100.0}
