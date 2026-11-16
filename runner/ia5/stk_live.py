"""Stocks (D-071) — portfel na żywo: plan zleceń we wtorek 08:00 czasu polskiego (po zamknięciu poprzedniego dnia sesji),
wykonanie na otwarciu wtorku (święto → następny dzień sesji), wycena na zamknięciu każdego dnia, dywidendy do gotówki.

Całe akcje: liczba sztuk = zaokrąglenie celu ÷ cena zamknięcia z dnia planu; reszta w gotówce, kupna przycinane tak, żeby
gotówka po planie nie była ujemna. Koszt COST od wartości każdej transakcji (jak w badaniu). Obok dwa portfele odniesienia
liczone tak samo: stały podział (co tydzień do celu) i „kup i trzymaj”. Stan (`stocks/state.json`) jest tylko dopisywany;
zdarzenia idą po kolei, więc po przerwie nadrabianie daje ten sam wynik. Zmiana metody, kodu albo konfiguracji = nowy start
(stary portfel do `archive`). Pierwszy podział od razu po badaniu: plan z ostatniego zamkniętego dnia, wykonanie na
otwarciu następnego dnia sesji.
"""
from __future__ import annotations

import copy
from datetime import date

import numpy as np
import pandas as pd

from . import stk_method as sm
from .rev_data import decision_times, next_decision
from .stk_config import COST, TZ
from .stk_data import Panel, eligible, last_session_before, schedule
from .stk_research import clean_json

GRACE_S = 7 * 3600            # wtorek 08:00 → najpóźniej 15:00 (sesja w Nowym Jorku startuje 15:30) bez spóźnionej świecy
CLOSE_S = 16 * 3600           # świeca dnia „zamyka się” o 16:00 w Nowym Jorku (do kolejności zdarzeń)
BOOKS = ("method", "fixed", "hold")


def _ny_date(ts: int) -> date:
    return pd.Timestamp(int(ts), unit="s", tz="UTC").tz_convert(TZ).date()


def exec_from(plan_ts: int) -> str:
    """Pierwszy dzień, którego otwarcie (09:30 w NY) jest po planie: dzień planu, gdy plan przed 09:30 NY, inaczej następny."""
    t = pd.Timestamp(int(plan_ts), unit="s", tz="UTC").tz_convert(TZ)
    d = t.date()
    if (t.hour, t.minute) >= (9, 30):
        d = d + pd.Timedelta(days=1)
    return d.isoformat()


def _close_time(day_ts: int) -> int:
    return int(day_ts) + CLOSE_S


def method_of(res: dict) -> dict:
    fr = res["frozen"]
    return {"id": fr["id"], "label": fr["label"], "code_hash": fr["code_hash"], "config_hash": fr["config_hash"],
            "frozen_at": int(fr["at"]), "stk_version": fr.get("stk_version")}


def new_state(res: dict, archive: list | None = None) -> dict:
    cap = float(res["config"]["capital"])
    book = {"shares": {t: 0 for t in res["universe"]}, "cash": cap}
    return {"stk_version": res.get("stk_version"), "method": method_of(res), "config": res["config"], "universe": list(res["universe"]),
            "weights": res["weights"], "band": res["band"], "capital0": cap, "start_ts": int(res["frozen"]["at"]),
            "books": {b: copy.deepcopy(book) for b in BOOKS}, "plans": [], "ledger": [], "dividends": [], "valuation": [],
            "last_day": None, "today": {}, "next": {}, "archive": list(archive or []), "computedAt": None}


def summary(st: dict) -> dict:
    v = st.get("valuation") or []
    return {"method": st.get("method"), "start_ts": st.get("start_ts"), "end_ts": v[-1][0] if v else None,
            "final": v[-1][1] if v else st.get("capital0"), "fixed_final": v[-1][2] if v else st.get("capital0"),
            "hold_final": v[-1][3] if v else st.get("capital0"), "capital0": st.get("capital0")}


def _orders(shares: dict, cash: float, universe: list[str], px: np.ndarray, target: np.ndarray, base: np.ndarray,
            thr: float, hold_mode: bool = False) -> list[dict]:
    """Zlecenia w sztukach z cen zamknięcia dnia planu. Próg i wejścia/wyjścia jak w symulacji badania."""
    sh = np.array([shares.get(t, 0) for t in universe], float)
    p = np.where(np.isfinite(px) & (px > 0), px, np.nan)
    val = np.nan_to_num(sh * p)
    V = cash + val.sum()
    if V <= 0:
        return []
    cur = val / V
    entry = (sh <= 0) & (target > 0)
    exit_ = (target <= 0) & (sh > 0)
    if hold_mode:
        trade = entry | exit_
    else:
        trade = (np.abs(target - cur) > np.maximum(thr * base, 1e-12)) | entry | exit_
    trade &= np.isfinite(p)
    want = np.where(trade, np.round(np.nan_to_num(target * V / np.where(np.isfinite(p), p, 1))), sh)
    if hold_mode and entry.any():       # „kup i trzymaj”: wejście nowej spółki finansuje gotówka (bez sprzedaży)
        want = np.where(entry, np.floor(np.nan_to_num(target * V / np.where(np.isfinite(p), p, 1))), sh)
    d = want - sh

    def cash_after(dd):
        flow = -np.nansum(dd * p)
        return cash + flow - COST * np.nansum(np.abs(dd) * p)

    while cash_after(d) < -1e-9 and (d > 0).any():     # kupna przycinane od największego, aż gotówka ≥ 0
        j = int(np.nanargmax(np.where(d > 0, d * p, -np.inf)))
        d[j] -= 1
    out = []
    for j, t in enumerate(universe):
        if d[j] != 0:
            out.append({"t": t, "side": "kupno" if d[j] > 0 else "sprzedaż", "shares": int(abs(d[j])), "price_plan": float(p[j]),
                        "value_plan": float(d[j] * p[j])})
    return out


def _fill(book: dict, orders: list[dict], opens: dict[str, float]) -> list[dict]:
    fills = []
    for o in orders:
        px = opens.get(o["t"])
        if px is None or not np.isfinite(px) or px <= 0:
            fills.append({**o, "filled": False})
            continue
        q = o["shares"] if o["side"] == "kupno" else -o["shares"]
        q = max(q, -book["shares"].get(o["t"], 0))
        val = q * px
        cost = COST * abs(val)
        book["shares"][o["t"]] = int(book["shares"].get(o["t"], 0) + q)
        book["cash"] = float(book["cash"] - val - cost)
        fills.append({**o, "filled": True, "price": float(px), "value": float(val), "cost": float(cost)})
    return fills


def _value(book: dict, universe: list[str], px: np.ndarray) -> float:
    return float(book["cash"] + sum(book["shares"].get(t, 0) * (p if np.isfinite(p) else 0.0) for t, p in zip(universe, px)))


def expected_signal_day(plan_ts: int) -> str:
    return last_session_before(pd.Timestamp(int(plan_ts), unit="s", tz="UTC").tz_convert(TZ).date()).isoformat()


def live_step(prev: dict | None, res: dict, ready: dict[str, pd.DataFrame], now: int) -> dict:
    m = method_of(res)
    archive = list((prev or {}).get("archive", []))
    key = ("id", "code_hash", "config_hash")
    if prev and tuple(prev["method"].get(k) for k in key) != tuple(m[k] for k in key):
        archive.append(summary(prev))
        prev = None
    st = new_state(res, archive) if prev is None else copy.deepcopy(prev)
    st["archive"] = archive
    uni = st["universe"]
    cfg = sm.BY_ID[m["id"]]
    band = float(st["band"])
    w_user = np.array([st["weights"][t] for t in uni], float)
    p = Panel(ready, uni)
    if not len(p.days):
        st["computedAt"] = int(now)
        return clean_json(st)
    feat = sm.daily_features(p)
    hist_sig, _ = schedule(p)
    day_ix = {d: i for i, d in enumerate(p.days)}
    start = int(st["start_ts"])
    plan_times = [start] + [int(t) for t in decision_times(start + 1, now) if _ny_date(t) > _ny_date(start)]
    # zdarzenia: dni (zamknięcie) po ostatnio wycenionym, plany po ostatnio zrobionym
    done_plans = {int(x["plan_ts"]) for x in st["plans"]}
    after = st["last_day"]
    days = [i for i, d in enumerate(p.days) if (after is None or d > after) and _close_time(p.ts[i]) > start]
    events = sorted([(_close_time(p.ts[i]), 0, i) for i in days] + [(t, 1, t) for t in plan_times if t not in done_plans and t <= now])
    for when, kind, x in events:
        if kind == 1:
            exp = expected_signal_day(x)
            have = [d for d in p.days if d < _ny_date(x).isoformat()]
            if not have:
                continue
            sday = have[-1]
            if sday < exp and now < x + GRACE_S:
                break                                   # czekamy na świecę dnia przed wtorkiem
            if any(pl["status"] == "zaplanowane" for pl in st["plans"]):
                break                                   # poprzedni plan jeszcze nie wykonany (brak świecy dnia wykonania)
            si = day_ix[sday]
            sig = np.r_[hist_sig[hist_sig < si], si].astype(int)
            el = eligible(p, sig)
            Wk = sm.Weekly(sig=sig, exe=sig, growth=np.ones((len(sig), len(uni))), elig=el, trade=el,
                           w=sm.base_weights(w_user, el), below=np.nan_to_num(feat["below200"][sig]),
                           falling=np.nan_to_num(feat["falling200"][sig]), scores=None)
            k = len(sig) - 1
            Wk.scores = _scores_for(feat, sig, el, cfg)
            tgt, s = sm.targets_live(Wk, cfg, band, k, group=0)
            px = p.cfill[si]
            base = Wk.w[k]
            orders = {"method": _orders(st["books"]["method"]["shares"], st["books"]["method"]["cash"], uni, px, tgt, base, cfg.threshold),
                      "fixed": _orders(st["books"]["fixed"]["shares"], st["books"]["fixed"]["cash"], uni, px, base, base, 0.0),
                      "hold": _orders(st["books"]["hold"]["shares"], st["books"]["hold"]["cash"], uni, px, base, base, 0.0,
                                      hold_mode=bool(st["plans"]))}
            vals = {b: _value(st["books"][b], uni, px) for b in BOOKS}
            st["plans"].append({"plan_ts": int(x), "signal_day": sday, "late": sday < exp, "status": "zaplanowane",
                                "value_plan": vals["method"], "targets": {t: float(v) for t, v in zip(uni, tgt)},
                                "base": {t: float(v) for t, v in zip(uni, base)}, "scores": {t: float(v) for t, v in zip(uni, s)},
                                "orders": orders["method"], "ref_orders": {"fixed": orders["fixed"], "hold": orders["hold"]},
                                "exec_from": exec_from(x), "exec_day": None})
            continue
        i = x
        d = p.days[i]
        for b in BOOKS:                                  # dywidendy: posiadacz z zamknięcia poprzedniego dnia
            bk = st["books"][b]
            for j, t in enumerate(uni):
                q = bk["shares"].get(t, 0)
                if q and p.div[i, j] > 0:
                    amt = float(q * p.div[i, j])
                    bk["cash"] = float(bk["cash"] + amt)
                    if b == "method":
                        st["dividends"].append({"day": d, "t": t, "shares": int(q), "per_share": float(p.div[i, j]), "amount": amt})
        pend = [pl for pl in st["plans"] if pl["status"] == "zaplanowane" and d > pl["signal_day"] and d >= pl["exec_from"]]
        for pl in pend:
            opens = {t: float(p.open[i, j]) for j, t in enumerate(uni) if np.isfinite(p.open[i, j])}
            fills = _fill(st["books"]["method"], pl["orders"], opens)
            _fill(st["books"]["fixed"], pl["ref_orders"]["fixed"], opens)
            _fill(st["books"]["hold"], pl["ref_orders"]["hold"], opens)
            pl["fills"], pl["exec_day"], pl["status"] = fills, d, "wykonane"
            for f in fills:
                if f["filled"]:
                    st["ledger"].append({"exec_day": d, "plan_ts": pl["plan_ts"], "t": f["t"], "side": f["side"], "shares": f["shares"],
                                         "price": f["price"], "price_plan": f["price_plan"], "value": f["value"], "cost": f["cost"]})
        if not st["plans"]:
            continue                                     # przed pierwszym wykonaniem nic do wyceny
        px = p.cfill[i]
        st["valuation"].append([int(p.ts[i])] + [_value(st["books"][b], uni, px) for b in BOOKS])
        st["last_day"] = d
    _today(st, p, uni)
    last = max([int(x["plan_ts"]) for x in st["plans"]] or [start])
    nxt = next_decision(last + 3600)
    st["next"] = {"plan_ts": int(nxt), "pending": next((pl for pl in st["plans"] if pl["status"] == "zaplanowane"), None) is not None}
    st["computedAt"] = int(now)
    return clean_json(st)


def _scores_for(feat: dict, sig: np.ndarray, el: np.ndarray, cfg: sm.Config) -> np.ndarray:
    """Oceny jednej grupy (sygnał × normalizacja × wygładzenie) zamrożonej metody: (1, tygodnie, spółki)."""
    vol = feat["vol63"][sig]
    if cfg.signal in sm.COMBOS:
        a, b = sm.COMBOS[cfg.signal]
        v = (sm.normalize(feat[a][sig], el, cfg.norm, vol) + sm.normalize(feat[b][sig], el, cfg.norm, vol)) / 2
    else:
        v = sm.normalize(feat[cfg.signal][sig], el, cfg.norm, vol)
    return sm.smooth(v, cfg.smooth)[None, :, :].astype(np.float32)


def _today(st: dict, p: Panel, uni: list[str]) -> None:
    if not st["plans"]:
        st["today"] = {}
        return
    i = len(p.days) - 1
    px = p.cfill[i]
    bk = st["books"]["method"]
    tot = _value(bk, uni, px)
    last = st["plans"][-1]
    band = float(st["band"])
    rows = []
    for j, t in enumerate(uni):
        q = bk["shares"].get(t, 0)
        v = q * px[j] if np.isfinite(px[j]) else 0.0
        b = last["base"].get(t, 0.0)
        rows.append({"t": t, "shares": int(q), "price": float(px[j]) if np.isfinite(px[j]) else None, "value": float(v),
                     "weight": float(v / tot) if tot > 0 else 0.0, "base": b, "lo": b * (1 - band), "hi": b * (1 + band),
                     "target": last["targets"].get(t, 0.0), "score": last["scores"].get(t, 0.0)})
    st["today"] = {"day": p.days[i], "ts": int(p.ts[i]), "total": float(tot), "cash": float(bk["cash"]), "rows": rows,
                   "fixed_total": _value(st["books"]["fixed"], uni, px), "hold_total": _value(st["books"]["hold"], uni, px)}

