"""FOREST v2 (D-049): wyniki, „dlaczego”, stan dla dashboardu i raport."""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .config import LEVERAGE, PAIRS, START_CAPITAL
from .forest import DESIGN_END, HORIZONS, MAX_INVESTORS, MIN_EVENTS, RHO_CAP, T_MIN, H, Panel
from .forest_manager import BOOKS, CONSENSUS, QUORUM, SEGMENTS, WHY, Manager
from .investors import book

BOOK_PCT = 5.0
SWAP_PIPS = 0.5  # założenie do testu wrażliwości: koszt nocy, której model nie liczy (O5)
GRID_N = (1, 3, 5, 10, 20)
GRID_C = (0.5, 0.6, 0.7, 0.8, 0.9)
EMPTY = "seq seg pair dir h ts entry_ts entry_px exit_ts gross spread weight status pips_net n cons noce".split()


def num(x, nd=2):
    x = float(x)
    return None if not math.isfinite(x) else round(x, nd)


def nights(entry, exit_) -> np.ndarray:
    """Ile razy pozycja przeszła przez 21:00 UTC (rolowanie)."""
    e, x = (np.asarray(entry, float) - 21 * H) // 86400, (np.asarray(exit_, float) - 21 * H) // 86400
    return np.nan_to_num(x - e)


def result(df: pd.DataFrame, hh: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(wynik brutto w pipsach, czy zamknięta, czas wyjścia) dla kierunku decyzji i horyzontu hh."""
    g24, g48 = df["g24"].to_numpy(float), df["g48"].to_numpy(float)
    x24, x48 = df["xt24"].to_numpy(float), df["xt48"].to_numpy(float)
    known = df["known"].to_numpy()
    is24 = hh == HORIZONS[0]
    return df["dir"].to_numpy() * np.where(is24, g24, g48), np.where(is24, known >= 1, known >= 2), np.where(is24, x24, x48)


def trades(df: pd.DataFrame, mask: np.ndarray, last_px: dict[str, float]) -> pd.DataFrame:
    """Transakcje: zamknięte, otwarte (wycena po ostatnim zamknięciu), anulowane (B12)."""
    if not len(df):
        return pd.DataFrame(columns=EMPTY)
    gross, closed, xt = result(df, df["h"].to_numpy())
    t = df.loc[mask, ["seq", "seg", "pair", "dir", "h", "ts", "spread", "n", "cons"]].copy()
    t["entry_ts"], t["entry_px"] = df.loc[mask, "e_ts"].to_numpy(), df.loc[mask, "e_px"].to_numpy()
    t["exit_ts"], t["gross"], c = xt[mask], gross[mask], closed[mask]
    t["weight"] = 1.0
    t["status"] = np.where(c, np.where(np.isfinite(t["gross"]), "zamknięta", "anulowana: przerwa w danych"), "otwarta")
    t = t[t["entry_ts"] > 0].reset_index(drop=True)
    if len(t):
        op = (t["status"] == "otwarta").to_numpy()
        pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
        mark = t["pair"].map(last_px).to_numpy(float)
        t["gross"] = np.where(op, (mark - t["entry_px"].to_numpy()) * t["dir"].to_numpy() / pip, t["gross"].to_numpy())
    t["pips_net"] = t["gross"] - t["spread"]
    t["noce"] = nights(t["entry_ts"], t["exit_ts"]) if len(t) else []
    return t


def cell(t: pd.DataFrame) -> dict:
    n = len(t)
    if not n:
        return {"n": 0, "win": None, "gross": None, "net": None, "t": None, "swap": None, "noce": None}
    w = t.groupby(t["ts"] // (7 * 86400))["pips_net"].sum()
    sd = w.std()
    return {
        "n": n,
        "win": num((t["pips_net"] > 0).mean() * 100, 1),
        "gross": num(t["gross"].mean()),
        "net": num(t["pips_net"].mean()),
        "t": num(w.mean() / sd * math.sqrt(len(w))) if len(w) > 2 and sd > 0 else None,
        "suma": num(t["pips_net"].sum(), 0),
        "swap": num((t["pips_net"] - SWAP_PIPS * t["noce"]).mean()),
        "noce": num(t["noce"].mean(), 1),
    }


def book_stats(t: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    res = book(t, START_CAPITAL, BOOK_PCT)
    tt = res["trades"]
    closed = tt[tt["status"] == "zamknięta"]
    eq = np.array([START_CAPITAL] + res["curve"]["equity"], float)
    peak = np.maximum.accumulate(eq)
    now = res["realized"] + res["unrealized"]
    ts, ev = res["curve"]["ts"], res["curve"]["equity"]
    step = max(1, len(ts) // 800)
    seg = {s: cell(closed[closed["seg"] == s]) for s in SEGMENTS}
    for s in SEGMENTS:
        seg[s]["usd"] = num(closed.loc[closed["seg"] == s, "pnl_usd"].fillna(0).sum(), 0)
    return {
        "equity": num(now),
        "return_pct": num((now / START_CAPITAL - 1) * 100),
        "max_dd_pct": num(((eq - peak) / peak).min() * 100),
        "closed": len(closed),
        "open": int((tt["status"] == "otwarta").sum()),
        "cancelled": int(tt["status"].str.startswith("anulowana").sum()),
        "seg": seg,
        "curve": {
            "ts": [int(x) for x in ts[::step]] + [int(x) for x in ts[-1:]],
            "equity": [num(x) for x in ev[::step]] + [num(x) for x in ev[-1:]],
        },
    }, tt


def chain(df: pd.DataFrame, n_min: int, c_min: float, last_px: dict) -> pd.DataFrame:
    """Te same decyzje przy innych progach, z zasadą jednej pozycji na parę (B8), po liczbie świec."""
    x = df[(df["dir"] != 0) & (df["n"] >= n_min) & (df["cons"] >= c_min)]
    keep, busy = x["seq"].tolist(), {}
    t = trades(df, df["seq"].isin(keep).to_numpy(), last_px)
    t = t[t["status"] == "zamknięta"].sort_values("entry_ts", kind="stable")
    out = []
    for r in t.itertuples():
        if r.entry_ts >= busy.get(r.pair, 0):
            busy[r.pair] = r.exit_ts
            out.append(r.Index)
    return t.loc[out]


def grid(df: pd.DataFrame, last_px: dict) -> dict:
    """Wszystkie sprawdzane progi naraz: żeby nie wybierać najlepszego po fakcie, widać całą tabelę."""
    out = {}
    for seg in (*SEGMENTS, "RAZEM"):
        d = df if seg == "RAZEM" else df[df["seg"] == seg]
        if not len(d):
            continue
        out[seg] = [{"n_min": a, "c_min": c, **cell(chain(d, a, c, last_px))} for a in GRID_N for c in GRID_C]
    return out


def bands(df: pd.DataFrame) -> dict:
    """Co znaczy zgoda: każda decyzja, także niewykonana, na swoim horyzoncie."""
    out = {}
    gross, closed, _ = result(df, df["h"].to_numpy())
    d = df.assign(gross=gross, pips_net=gross - df["spread"].to_numpy(), noce=nights(df["e_ts"], df["xt48"]))[
        closed & np.isfinite(gross) & (df["dir"].to_numpy() != 0)
    ]
    for seg in (*SEGMENTS, "RAZEM"):
        x = d if seg == "RAZEM" else d[d["seg"] == seg]
        if not len(x):
            continue
        rows = []
        for lo, hi, name in ((0.5, 0.6, "50–60%"), (0.6, 0.7, "60–70%"), (0.7, 0.8, "70–80%"), (0.8, 0.9, "80–90%"), (0.9, 1.01, "≥ 90%")):
            rows.append({"band": name, **cell(x[(x["cons"] >= lo) & (x["cons"] < hi)])})
        out[seg] = rows
    return out


def conclusions(st: dict) -> list[dict]:
    b = st["books"]["m"]["seg"]
    k = st["books"]["k"]["seg"]
    seg = "LIVE" if (b["LIVE"]["n"] or 0) >= 100 else "TEST" if (b["TEST"]["n"] or 0) else "HISTORIA"
    pl = lambda x, d=2: f"{x:+.{d}f}".replace(".", ",").replace("-", "−")  # noqa: E731
    L = []
    m, c = b[seg], k[seg]
    if m["n"]:
        good = (m["t"] or 0) >= 2 and (m["net"] or 0) > 0
        L.append(
            {
                "state": "ok" if good else "warn" if (m["net"] or 0) > 0 else "bad",
                "text": f"Manager ({seg}): {m['n']} transakcji, {pl(m['net'])} pipsa netto na transakcję, "
                f"pewność t = {f'{m["t"] or 0:.1f}'.replace('.', ',').replace('-', '−')}. "
                + ("To już mocny sygnał." if good else "Żeby uznać to za przewagę, t musi wynosić co najmniej 2."),
            }
        )
        if m["swap"] is not None:
            L.append(
                {
                    "state": "ok" if m["swap"] > 0 else "bad",
                    "text": f"Po doliczeniu nocy ({str(SWAP_PIPS).replace('.', ',')} pipsa za noc, średnio "
                    f"{str(m['noce']).replace('.', ',')} nocy "
                    f"na transakcję): {pl(m['swap'])} pipsa. Model silnika nocy nie liczy.",
                }
            )
    if c["n"] and m["n"]:
        L.append(
            {
                "state": "ok" if (m["net"] or 0) > (c["net"] or 0) else "bad",
                "text": f"Progi ({QUORUM} głosów, {int(CONSENSUS * 100)}% zgody) kontra bez progów ({seg}): "
                f"{pl(m['net'])} vs {pl(c['net'])} pipsa netto.",
            }
        )
    last = st["generations"][-1] if st["generations"] else None
    z = st.get("zero") or []
    if last and z:
        zp = float(np.mean([x["passed"] for x in z]))
        sh = zp / max(1, last["passed"]) * 100
        L.append(
            {
                "state": "ok" if sh < 25 else "warn",
                "text": f"Szczęście: na danych bez przewagi te same bramki przechodzi średnio {zp:.0f} reguł, "
                f"na prawdziwych {last['passed']}. "
                f"Około {sh:.0f}% wybranych może być dziełem przypadku.",
            }
        )
    return L


def build_state(g: Manager, pn: Panel, now: int | None = None) -> tuple[dict, dict]:
    now = int(time.time()) if now is None else int(now)
    df = g.frame()
    last_px = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    books, tr = {}, {}
    for b, name in BOOKS.items():
        t = trades(df, df[f"ex_{b}"].to_numpy(bool), last_px) if len(df) else pd.DataFrame(columns=EMPTY)
        s, tt = book_stats(t)
        books[b], tr[b] = {"name": name, **s}, tt
    pos = []
    tt = tr["m"]
    for r in tt[tt["status"] == "otwarta"].itertuples() if len(tt) else []:
        pos.append(
            {
                "pair": r.pair,
                "dir": int(r.dir),
                "h": int(r.h),
                "entry_ts": int(r.entry_ts),
                "entry_px": float(r.entry_px),
                "wycena": num(r.pips_net, 1),
                "pnl_usd": num(r.pnl_usd),
                "seq": int(r.seq),
            }
        )
    fr = g.fr
    gens = [{k: x[k] for k in ("week", "ts", "passed", "kept", "added", "retired")} for x in fr["generations"]]
    why = df["why"].value_counts().to_dict() if len(df) else {}
    active = fr["generations"][-1]["investors"] if fr["generations"] else []
    st = {
        "id": fr["id"],
        "version": fr["version"],
        "engine_version": fr["engine_version"],
        "created": fr["created"],
        "computedAt": now,
        "dataTo": int(pn.ts.max()) + H,
        "cursor": max(g.cursor.values()),
        "built_to": fr["built_to"],
        "design_end": DESIGN_END,
        "pairs": fr["pairs"],
        "horizons": list(HORIZONS),
        "params": {
            "QUORUM": QUORUM,
            "CONSENSUS": CONSENSUS,
            "T_MIN": T_MIN,
            "MIN_EVENTS": MIN_EVENTS,
            "RHO_CAP": RHO_CAP,
            "MAX_INVESTORS": MAX_INVESTORS,
            "BOOK_PCT": BOOK_PCT,
            "LEVERAGE": LEVERAGE,
            "START_CAPITAL": START_CAPITAL,
            "SWAP_PIPS": SWAP_PIPS,
        },
        "counts": {"decyzje": len(df), "las": len(active), "dlaczego": {WHY[k]: int(v) for k, v in why.items()}},
        "generations": gens,
        "zero": fr.get("zero") or [],
        "books": books,
        "open": pos,
        "now": g.view_now(pn),
        "grid": grid(df, last_px) if len(df) else {},
        "bands": bands(df) if len(df) else {},
    }
    st["months"] = sorted(pd.to_datetime(df["ts"], unit="s", utc=True).dt.strftime("%Y-%m").unique().tolist()) if len(df) else []
    st["conclusions"] = conclusions(st) if len(df) else []
    return st, tr


def report(st: dict) -> str:
    day = lambda x: time.strftime("%Y-%m-%d", time.gmtime(x))  # noqa: E731
    L = [
        f"# FOREST v2 (D-049) — las {st['id']}",
        "",
        f"- Dane do {day(st['dataTo'])}. Założenia ustalone na świecach do {day(st['design_end'])}. "
        f"HISTORIA = do tej daty, TEST = do budowy ({day(st['built_to'])}), LIVE = później.",
        f"- Inwestorzy: reguły lustrzane, horyzonty {st['horizons']} świec. Bramki: t ≥ {st['params']['T_MIN']}, "
        f"≥ {st['params']['MIN_EVENTS']} zdarzeń, 3/4 bloków dodatnich, |ρ| ≤ {st['params']['RHO_CAP']}. Odświeżenie co 4 tygodnie.",
        f"- Manager: ≥ {QUORUM} głosów i ≥ {int(CONSENSUS * 100)}% zgody. W lesie teraz {st['counts']['las']} inwestorów.",
        "",
        "## Wnioski",
        "",
    ]
    L += [f"- [{c['state']}] {c['text']}" for c in st["conclusions"]]
    L += [
        "",
        "## Księgi",
        "",
        "| księga | odcinek | n | wygrane % | brutto | netto | t | po nocach | wynik USD |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for x in st["books"].values():
        for s, v in x["seg"].items():
            if v["n"]:
                L.append(f"| {x['name']} | {s} | {v['n']} | {v['win']} | {v['gross']} | {v['net']} | {v['t']} | {v['swap']} | {v['usd']} |")
    L += ["", "## Wszystkie progi (nie wybieraj najlepszego po fakcie)", ""]
    for seg, rows in st["grid"].items():
        L += [f"### {seg}", "", "| głosy ≥ | zgoda ≥ | n | netto | t |", "|---|---|---|---|---|"]
        L += [f"| {r['n_min']} | {int(r['c_min'] * 100)}% | {r['n']} | {r['net']} | {r['t']} |" for r in rows]
        L.append("")
    L += ["## Odświeżenia lasu", "", "| data | przeszło bramki | w lesie | doszło | odpadło |", "|---|---|---|---|---|"]
    L += [f"| {day(x['ts'])} | {x['passed']} | {x['kept']} | {x['added']} | {x['retired']} |" for x in st["generations"]]
    for z in st["zero"]:
        L += [
            "",
            f"## Dane bez przewagi (nasiono {z['seed']})",
            "",
            f"- Średnio przeszło bramki {z['passed']}, w lesie {z['kept']}.",
            f"- Manager: {z['seg']}",
        ]
    return "\n".join(L)


def write_public(g: Manager, pn: Panel, folder: Path, now: int | None = None) -> dict:
    st, tr = build_state(g, pn, now)
    new = folder.with_name(folder.name + ".new")
    if new.exists():
        shutil.rmtree(new)
    (new / "journal").mkdir(parents=True)
    (new / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    fr = g.fr
    now_rules = {i["rule"] for i in fr["generations"][-1]["investors"]} if fr["generations"] else set()
    known: dict[int, dict] = {}
    for x in fr["generations"]:
        for i in x["investors"]:
            d = known.setdefault(i["rule"], {"id": i["rule"], "od": x["ts"], "rule": g.texts(i["rule"])})
            d.update({"h": HORIZONS[i["k"]], "t": i["t"], "ev": i["ev"], "do": x["ts"]})
    inv = sorted(({**d, "aktywny": d["id"] in now_rules} for d in known.values()), key=lambda d: (not d["aktywny"], -d["t"]))
    (new / "investors.json").write_text(
        json.dumps({"id": st["id"], "investors": inv}, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8"
    )
    (new / "report.md").write_text(report(st), encoding="utf-8")
    df = g.frame()
    if len(df):
        tt = tr["m"]
        df["usd"], df["kap"] = np.nan, np.nan
        if len(tt):
            df.loc[tt["seq"].to_numpy(int), "usd"] = tt["pnl_usd"].to_numpy(float)
            df.loc[tt["seq"].to_numpy(int), "kap"] = tt["equity_after"].to_numpy(float)
        month = pd.to_datetime(df["ts"], unit="s", utc=True).dt.strftime("%Y-%m")
        for m, part in df.groupby(month):
            part.reset_index(drop=True).to_parquet(new / "journal" / f"{m}.parquet", index=False)
    if folder.exists():
        shutil.rmtree(folder)
    new.replace(folder)
    return st
