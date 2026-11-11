"""REV (D-063) — portfel na żywo: przeliczenie we wtorek 08:00 (R2), wycena każdego zamkniętego dnia, dziennik (R7).

Stan (`rev/state.json` na gałęzi data) jest tylko dopisywany: rozliczonych wierszy dziennika i wyceny nigdy się nie
przelicza. Zdarzenia (dni wyceny i wtorki) idą po kolei, więc po przerwie nadrabianie daje ten sam wynik co krok po kroku.
Metoda = zwycięzca badania zamrożony w `research.frozen`; zmiana metody (id albo hash kodu) = nowy start, stary portfel
trafia do `archive` (R6). Ten sam krok przeliczenia co w badaniu (`rev_method.trade`).
"""
from __future__ import annotations

import copy
from datetime import date, timedelta

import numpy as np
import pandas as pd

from . import rev_method as rm
from .daily import is_expected_day
from .rev_config import BASE, DEADLINE_HOUR, DECISION_HOUR, DECISION_TZ, START_PLN
from .rev_data import daily_panel, decision_times, next_decision, weekly_panel
from .rev_research import clean_json

GRACE_S = (DEADLINE_HOUR - DECISION_HOUR) * 3600   # wtorek 08:00 → najpóźniej 20:00 bez spóźnionych świec
DAY_GRACE_S = 12 * 3600                              # dzień wyceny: czekamy na komplet świec najwyżej 12 h
TINY = 1e-9


def method_of(research: dict) -> dict:
    fr = research["frozen"]
    return {"id": fr["id"], "label": fr.get("label") or rm.VARIANT_BY_ID[fr["id"]].label, "code_hash": fr["code_hash"],
            "frozen_at": int(fr["at"]), "rev_version": fr.get("rev_version")}


def _warsaw_date(ts: int) -> date:
    return pd.Timestamp(int(ts), unit="s", tz="UTC").tz_convert(DECISION_TZ).date()


def expected_price_day(decision_ts: int) -> str:
    """Dzień świecy, na którą czekamy przy decyzji: ostatni dzień roboczy przed dniem decyzji (zwykle poniedziałek)."""
    d = _warsaw_date(decision_ts) - timedelta(days=1)
    while not is_expected_day(d):
        d -= timedelta(days=1)
    return d.isoformat()


def new_state(research: dict, archive: list | None = None) -> dict:
    m = method_of(research)
    universe = list(research["universe"])
    start = next_decision(m["frozen_at"])
    units = {b: (START_PLN if b == BASE else 0.0) for b in universe}
    return {"rev_version": research.get("rev_version"), "method": m, "universe": universe,
            "blocs": research.get("blocs", {}), "start_ts": int(start), "capital0": START_PLN,
            "units": dict(units), "equal_units": dict(units), "ledger": [], "rebalances": [], "valuation": [],
            "scale_known": [], "scale_applied": [], "last_day": None, "last_decision": None,
            "next_rebalance": int(start), "today": {}, "archive": list(archive or []), "computedAt": None}


def summary(st: dict) -> dict:
    v = st.get("valuation") or []
    return {"method": st.get("method"), "start_ts": st.get("start_ts"), "end_ts": v[-1][0] if v else None,
            "final": v[-1][1] if v else st.get("capital0"), "equal_final": v[-1][2] if v else st.get("capital0")}


def _apply_scale_events(st: dict, infos: dict | None, now: int) -> None:
    """Przeskalowanie historii waluty w warstwie czyszczenia (×10^k) zmienia skalę cen — jednostki trzymane w starej skali
    dzielimy przez czynnik (wartość w złotych bez zmian). Zdarzenia znane w chwili zakupu już są w cenach zakupu."""
    known = {(c, int(t)) for c, t in st["scale_known"]}
    for c, info in sorted((infos or {}).items()):
        for ts, f in info.get("rescaled", []) or []:
            key = (c, int(ts))
            if key in known:
                continue
            if c in st["units"] and (st["units"][c] or st["equal_units"].get(c)):
                st["units"][c] = st["units"][c] / float(f)
                st["equal_units"][c] = st["equal_units"].get(c, 0.0) / float(f)
                st["scale_applied"].append([int(now), c, float(f), int(ts)])
            st["scale_known"].append([c, int(ts)])
            known.add(key)


def _decision(st: dict, research: dict, ready: dict, D: int, exp_day: str) -> None:
    """Wtorkowe przeliczenie zamrożoną metodą na cenach z zamknięcia ostatniego dnia przed D."""
    universe = st["universe"]
    have = [ready[c] for c in universe if c != BASE and ready.get(c) is not None and len(ready[c])]
    first = int(min(int(f["close_ts"].iloc[0]) for f in have))
    times = decision_times(first, D)
    prices, pts = weekly_panel(ready, universe, times)
    elig = rm.eligible(prices)
    x = rm.relative(prices)
    mid = st["method"]["id"]
    if mid == "SW":
        start = int(np.searchsorted(times, int(research["periods"]["start_ts"])))
        eqt = rm.equal_targets(elig)
        eq = rm.simulate(prices, eqt, None, band=0.0, start=start)
        targets, orders, excess = {}, {}, {}
        for v in rm.STATIC:
            tg, od = rm.variant_targets(prices, elig, v)
            targets[v.id], orders[v.id] = tg, od
            excess[v.id] = rm.simulate(prices, tg, od, start=start).ret.reindex(prices.index) - eq.ret.reindex(prices.index)
        tg_sw, chosen, od_sw = rm.switcher_targets(pd.DataFrame(excess), targets, eqt, start, orders)
        target, order = tg_sw.iloc[-1].to_numpy(float), od_sw[-1]
        pick = str(chosen.iloc[-1])
        sc = rm.score(x, rm.VARIANT_BY_ID[pick].score, elig).where(elig).iloc[-1] if pick != "equal" else None
    else:
        v = rm.VARIANT_BY_ID[mid]
        sc = rm.score(x, v.score, elig).where(elig).iloc[-1]
        target = rm.target_weights(sc, v.how).to_numpy(float)
        order = rm._order(sc.to_numpy(float))
        pick = mid
    value_s = rm.score(x, "V5", elig).where(elig).iloc[-1]
    trend_s = rm.score(x, "M3", elig).where(elig).iloc[-1]
    raw = prices.iloc[-1].to_numpy(float)
    last = prices.ffill().iloc[-1].to_numpy(float)
    units = np.array([st["units"][b] for b in universe], float)
    nu, V, frozen, chg = rm.trade(units, raw, last, target, order)
    eu = np.array([st["equal_units"][b] for b in universe], float)
    enu, EV, _, _ = rm.trade(eu, raw, last, rm.equal_targets(elig).iloc[-1].to_numpy(float), order, band=0.0)
    days = {b: (pd.Timestamp(int(t), unit="s", tz="UTC").tz_convert("Europe/London").strftime("%Y-%m-%d")
                if np.isfinite(t) else None) for b, t in zip(universe, pts.iloc[-1].to_numpy(float))}
    rows = []
    for j, b in enumerate(universe):
        if abs(nu[j] - units[j]) > TINY * max(abs(units[j]), 1.0) and (chg[j] or b == BASE):
            px = 1.0 if b == BASE else float(raw[j])
            rows.append({"ts": int(D), "basket": b, "units_before": float(units[j]), "units_after": float(nu[j]),
                         "price": px, "price_day": days[b] if b != BASE else exp_day,
                         "value_pln": float((nu[j] - units[j]) * px)})
    late = [b for b in universe if b != BASE and days.get(b) and np.isfinite(raw[universe.index(b)]) and days[b] != exp_day]
    st["ledger"].extend(rows)
    pxv = np.where(np.isfinite(last), last, 0.0)
    st["rebalances"].append({
        "ts": int(D), "value": float(V), "equal_value": float(EV), "changes": len([r for r in rows if r["basket"] != BASE]),
        "turnover_pln": float(sum(abs(r["value_pln"]) for r in rows) / 2), "variant": pick,
        "targets": {b: float(w) for b, w in zip(universe, target)},
        "weights": {b: float(w) for b, w in zip(universe, nu * pxv / V if V > 0 else nu * 0)},
        "scores": {b: (float(s) if sc is not None and np.isfinite(s) else None)
                   for b, s in zip(universe, (sc.to_numpy(float) if sc is not None else [np.nan] * len(universe)))},
        "value_score": {b: (float(s) if np.isfinite(s) else None) for b, s in zip(universe, value_s.to_numpy(float))},
        "trend_score": {b: (float(s) if np.isfinite(s) else None) for b, s in zip(universe, trend_s.to_numpy(float))},
        "late": late, "frozen": [b for b, f in zip(universe, frozen) if f], "price_day": exp_day})
    st["units"] = {b: float(u) for b, u in zip(universe, nu)}
    st["equal_units"] = {b: float(u) for b, u in zip(universe, enu)}
    st["last_decision"] = int(D)


def live_step(prev: dict | None, research: dict, ready: dict[str, pd.DataFrame], now: int,
              infos: dict | None = None) -> dict:
    """Portfel do chwili `now`: przeskalowania, potem po kolei dni wyceny i wtorkowe przeliczenia, aż do pierwszego
    zdarzenia, na które jeszcze czekamy (komplet świec albo termin: dzień + 12 h, wtorek do 20:00)."""
    m = method_of(research)
    archive = list((prev or {}).get("archive", []))
    if prev and (prev["method"]["id"], prev["method"]["code_hash"]) != (m["id"], m["code_hash"]):
        archive.append(summary(prev))
        prev = None
    if prev is None:
        st = new_state(research, archive)
        st["scale_known"] = [[c, int(t)] for c, i in sorted((infos or {}).items()) for t, _ in (i.get("rescaled") or [])]
    else:
        st = copy.deepcopy(prev)
        st["archive"] = archive
        _apply_scale_events(st, infos, now)
    universe = st["universe"]
    start = st["start_ts"]
    frames = {c: ready[c] for c in universe if c != BASE and ready.get(c) is not None and len(ready[c])}
    if frames and now >= start:
        daily = daily_panel(ready, universe, from_ts=start - 40 * 86400).ffill()
        cts = {c: set(f["close_ts"].to_numpy("int64").tolist()) for c, f in frames.items()}
        after = st["last_day"] if st["last_day"] is not None else start
        days = [int(d) for d in daily.index.to_numpy("int64") if after < d <= now]
        last_dec = st["last_decision"]
        decs = [int(D) for D in decision_times(start, now) if last_dec is None or D > last_dec]
        events = sorted([(d, 0) for d in days] + [(D, 1) for D in decs])
        for t, kind in events:
            if kind == 0:
                if not (all(t in s for s in cts.values()) or now >= t + DAY_GRACE_S):
                    break
                row = daily.loc[t].reindex(universe).to_numpy(float)
                px = np.where(np.isfinite(row), row, 0.0)
                val = sum(st["units"][b] * p for b, p in zip(universe, px))
                eqv = sum(st["equal_units"][b] * p for b, p in zip(universe, px))
                st["valuation"].append([int(t), float(val), float(eqv)])
                st["last_day"] = int(t)
            else:
                exp_day = expected_price_day(t)
                on_time = all(_last_day_before(f, t) == exp_day for f in frames.values())
                if not (on_time or now >= t + GRACE_S):
                    break
                _decision(st, research, ready, t, exp_day)
        if st["rebalances"] and (not st["valuation"] or st["valuation"][-1][0] < st["rebalances"][-1]["ts"]):
            rb = st["rebalances"][-1]             # po przeliczeniu, przed pierwszą wyceną — udziały z przeliczenia
            st["today"] = {"ts": rb["ts"], "values": {b: w * rb["value"] for b, w in rb["weights"].items()},
                           "weights": rb["weights"], "total": rb["value"], "equal_total": rb["equal_value"],
                           "targets": rb["targets"], "scores": rb["scores"], "value_score": rb["value_score"],
                           "trend_score": rb["trend_score"]}
        elif st["valuation"]:
            t, _, _ = st["valuation"][-1]
            row = daily.loc[:t].iloc[-1].reindex(universe).to_numpy(float)
            px = np.where(np.isfinite(row), row, 0.0)
            vals = {b: float(st["units"][b] * p) for b, p in zip(universe, px)}
            tot = sum(vals.values())
            last_rb = st["rebalances"][-1] if st["rebalances"] else {}
            st["today"] = {"ts": int(t), "values": vals, "weights": {b: (v / tot if tot > 0 else 0.0) for b, v in vals.items()},
                           "total": float(tot), "equal_total": float(st["valuation"][-1][2]),
                           "targets": last_rb.get("targets", {}), "scores": last_rb.get("scores", {}),
                           "value_score": last_rb.get("value_score", {}), "trend_score": last_rb.get("trend_score", {})}
    nd = st["last_decision"]
    st["next_rebalance"] = int(next_decision(nd + 3600) if nd is not None else start)
    st["computedAt"] = int(now)
    return clean_json(st)


def _last_day_before(f: pd.DataFrame, t: int) -> str | None:
    cts = f["close_ts"].to_numpy("int64")
    i = int(np.searchsorted(cts, t, side="right")) - 1
    return str(f["day"].iloc[i]) if i >= 0 else None
