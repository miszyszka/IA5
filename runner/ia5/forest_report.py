"""FOREST (D-048): księgi, statystyki „co znaczy głos”, stan dla dashboardu i raport."""

from __future__ import annotations

import json
import math
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import forest_rules as FR
from .config import LEVERAGE, PAIRS, START_CAPITAL
from .forest import HORIZONS, NH, H, Panel
from .forest_manager import BOOKS, K_MAPS, MIN_MAPS, SEGMENTS, Z_MIN, Manager, hex_votes
from .investors import book

BOOK_PCT = 5.0  # depozyt na wejście, % kapitału (B4); przy 30:1 nominał = 1,5 × kapitał
BANDS = {
    "przewaga": ("przewaga głosów", [0, 0.05, 0.10, 0.20, 0.30, 1.01], ["< 5%", "5–10%", "10–20%", "20–30%", "≥ 30%"], 1),
    "z": ("z podobnych map", [-99, -2, -1, 0, 1, 2, 99], ["z < −2", "−2…−1", "−1…0", "0…1", "1…2", "z ≥ 2"], 1),
    "dop": ("dopasowanie do map", [0, 0.65, 0.70, 0.75, 1.01], ["< 65%", "65–70%", "70–75%", "≥ 75%"], 1),
}


def _num(x, nd=3):
    x = float(x)
    return None if not math.isfinite(x) else round(x, nd)


EMPTY_TRADES = "seq seg pair dir h signal_ts entry_ts entry_px exit_ts gross spread weight status pips_net".split()


def outcomes(df: pd.DataFrame, d: np.ndarray, hh: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(wynik brutto w pipsach dla kierunku d i horyzontu hh, zamknięta?, czas wyjścia)."""
    g = df[[f"g{h}" for h in HORIZONS]].to_numpy(float)
    xt = df[[f"xt{h}" for h in HORIZONS]].to_numpy(float)
    i = np.arange(len(df))
    k = hh - 1
    return d * g[i, k], df["known"].to_numpy() >= hh, xt[i, k]


def book_trades(df: pd.DataFrame, b: str, last_px: dict[str, float]) -> pd.DataFrame:
    """Transakcje księgi b: zamknięte, otwarte (wycena po ostatnim zamknięciu) i anulowane (B12). Bez wejścia = jeszcze nie ma."""
    d = (df["dir_c"] if b == "c" else df["dir"]).to_numpy()
    hh = (df["h_c"] if b == "c" else df["h_b"] if b == "b" else df["h"]).to_numpy()
    gross, closed, xts = outcomes(df, d, hh)
    t = pd.DataFrame(
        {
            "seq": df["seq"].to_numpy(),
            "seg": df["seg"].to_numpy(),
            "pair": df["pair"].to_numpy(),
            "dir": d,
            "h": hh,
            "signal_ts": df["ts"].to_numpy(),
            "entry_ts": df["e_ts"].to_numpy(),
            "entry_px": df["e_px"].to_numpy(),
            "exit_ts": xts,
            "gross": gross,
            "spread": df["spread"].to_numpy(),
            "weight": 1.0,
        }
    )
    t["status"] = np.where(closed, np.where(np.isfinite(gross), "zamknięta", "anulowana: przerwa w danych"), "otwarta")
    keep = df[f"ex_{b}"].to_numpy(bool) & (t["entry_ts"].to_numpy() > 0)
    t = t[keep].reset_index(drop=True)
    if len(t):
        op = (t["status"] == "otwarta").to_numpy()
        pip = t["pair"].map({p: c.pip for p, c in PAIRS.items()}).to_numpy(float)
        mark = t["pair"].map(last_px).to_numpy(float)
        t["gross"] = np.where(op, (mark - t["entry_px"].to_numpy()) * t["dir"].to_numpy() / pip, t["gross"].to_numpy())
    t["pips_net"] = t["gross"] - t["spread"]
    return t


def cell(gross: np.ndarray, net: np.ndarray) -> dict:
    n = len(net)
    if not n:
        return {"n": 0, "win": None, "gross": None, "net": None, "t": None, "t_gross": None}
    sd, sdg = net.std(ddof=1) if n > 1 else 0.0, gross.std(ddof=1) if n > 1 else 0.0
    return {
        "n": n,
        "win": _num((net > 0).mean() * 100, 1),
        "gross": _num(gross.mean(), 2),
        "net": _num(net.mean(), 2),
        "t": _num(net.mean() / (sd / math.sqrt(n)), 2) if sd > 0 else None,
        "t_gross": _num(gross.mean() / (sdg / math.sqrt(n)), 2) if sdg > 0 else None,
    }


def book_stats(t: pd.DataFrame, capital: float = START_CAPITAL) -> dict:
    res = book(t, capital, BOOK_PCT)
    tt = res["trades"]
    closed = tt[tt["status"] == "zamknięta"]
    eq = np.array([capital] + res["curve"]["equity"], float)
    dd = float(((eq - np.maximum.accumulate(eq)) / np.maximum.accumulate(eq)).min() * 100) if len(eq) else 0.0
    now = res["realized"] + res["unrealized"]
    seg = {
        s: cell(closed.loc[closed.seg == s, "gross"].to_numpy(float), closed.loc[closed.seg == s, "pips_net"].to_numpy(float))
        for s in SEGMENTS
    }
    for s in SEGMENTS:
        part = closed[closed.seg == s]
        seg[s]["usd"] = _num(part["pnl_usd"].fillna(0).sum(), 2)
    ts, ev = res["curve"]["ts"], res["curve"]["equity"]
    step = max(1, len(ts) // 1500)
    return {
        "equity": _num(now, 2),
        "return_pct": _num((now / capital - 1) * 100, 2),
        "max_dd_pct": _num(dd, 2),
        "realized": _num(res["realized"], 2),
        "unrealized": _num(res["unrealized"], 2),
        "closed": len(closed),
        "open": int((tt["status"] == "otwarta").sum()),
        "cancelled": int(tt["status"].str.startswith("anulowana").sum()),
        "skipped_margin": int(res["skipped_margin"]),
        "seg": seg,
        "curve": {
            "ts": [int(x) for x in ts[::step]] + ([int(ts[-1])] if ts else []),
            "equity": [_num(x, 2) for x in ev[::step]] + ([_num(ev[-1], 2)] if ev else []),
        },
    }, tt


def rank_test(x: np.ndarray, y: np.ndarray, n_rot: int = 2000, seed: int = 7) -> dict:
    """Czy x (w kolejności czasu) mówi coś o y: korelacja rang i p z losowych obrotów y względem x. Obrót zachowuje skupienia
    w czasie, które przy zwykłym tasowaniu dałyby fałszywie małe p (kolejne decyzje są mocno zależne)."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(x)
    if n < 200:
        return {"n": n, "rho": None, "p": None}
    rx = pd.Series(x).rank().to_numpy() - (n + 1) / 2
    ry = pd.Series(y).rank().to_numpy() - (n + 1) / 2
    den = np.sqrt((rx**2).sum() * (ry**2).sum())
    rho = float((rx * ry).sum() / den)
    rng = np.random.default_rng(seed)
    s = rng.integers(n // 20, n - n // 20, n_rot)
    fx = np.fft.rfft(rx)
    fy = np.fft.rfft(ry)
    cc = np.fft.irfft(fx * np.conj(fy), n) / den  # korelacje wszystkich obrotów naraz
    null = cc[s]
    return {"n": n, "rho": _num(rho, 4), "p": _num((np.sum(np.abs(null) >= abs(rho)) + 1) / (n_rot + 1), 4)}


def meaning(df: pd.DataFrame) -> dict:
    """Statystyczny obraz głosu: każda decyzja (także niewykonana) liczona wirtualnie na swoim horyzoncie."""
    gross, closed, _ = outcomes(df, df["dir"].to_numpy(), df["h"].to_numpy())
    d = df.assign(gross=gross, net=gross - df["spread"].to_numpy())
    d = d[closed & np.isfinite(gross)]
    gb, cb, _ = outcomes(df, df["dir"].to_numpy(), df["h_b"].to_numpy())
    db = df.assign(gross=gb, net=gb - df["spread"].to_numpy())[cb & np.isfinite(gb)]
    out = {}
    for seg in (*SEGMENTS, "RAZEM"):
        x = d if seg == "RAZEM" else d[d.seg == seg]
        xb = db if seg == "RAZEM" else db[db.seg == seg]
        t = {"wszystkie": cell(x.gross.to_numpy(), x.net.to_numpy())}
        for key, (name, edges, labels, _) in BANDS.items():
            cut = pd.cut(x[key].to_numpy(float), edges, labels=labels, right=False)
            t[key] = {
                "name": name,
                "rows": [{"band": lb, **cell(x.gross[cut == lb].to_numpy(), x.net[cut == lb].to_numpy())} for lb in labels],
            }
        cut = pd.cut(xb["z_b"].to_numpy(float), BANDS["z"][1], labels=BANDS["z"][2], right=False)
        t["z_b"] = {
            "name": "najlepszy z (księga B, jej horyzont)",
            "rows": [{"band": lb, **cell(xb.gross[cut == lb].to_numpy(), xb.net[cut == lb].to_numpy())} for lb in BANDS["z"][2]],
        }
        t["horyzont"] = {
            "name": "horyzont",
            "rows": [{"band": f"{h} św.", **cell(x.gross[x.h == h].to_numpy(), x.net[x.h == h].to_numpy())} for h in HORIZONS],
        }
        t["kierunek"] = {
            "name": "kierunek",
            "rows": [
                {"band": nm, **cell(x.gross[x.dir == s].to_numpy(), x.net[x.dir == s].to_numpy())} for s, nm in ((1, "long"), (-1, "short"))
            ],
        }
        t["para"] = {
            "name": "para",
            "rows": [{"band": p, **cell(x.gross[x.pair == p].to_numpy(), x.net[x.pair == p].to_numpy())} for p in sorted(x.pair.unique())],
        }
        s = x.sort_values("ts", kind="stable")
        t["uczenie"] = {
            "z_vs_wynik": rank_test(s.z.to_numpy(float), s.net.to_numpy(float)),
            "przewaga_vs_wynik": rank_test(s.przewaga.to_numpy(float), s.net.to_numpy(float)),
            "g_map_vs_wynik": rank_test(s.g_map.to_numpy(float), s.net.to_numpy(float)),
        }
        out[seg] = t
    return out


def investor_rows(g: Manager) -> list[dict]:
    w = g.weights()
    rows = []
    for k, i in enumerate(g.fr["investors"]):
        hit, net = {}, {}
        for s, seg in enumerate(SEGMENTS):
            seen = g.seen[s]
            if seen.max() > 0:
                with np.errstate(divide="ignore", invalid="ignore"):
                    hit[seg] = [_num(x, 2) for x in g.hits[s, k] / seen * 100]
                    net[seg] = [_num(x, 4) for x in g.nets[s, k] / seen]
        rows.append(
            {
                "id": i["id"],
                "fam": i["fam"],
                "families": i["families"],
                "rule": i["rule"],
                "t_cv": i["t_cv"],
                "folds": i["folds"],
                "stany": len(i["table"]),
                "hit": hit,
                "net": net,
                "punkty": int(g.pos[k] - g.neg[k]),
                "waga": _num(w[k], 2) if w is not None else None,
            }
        )
    return rows


def forest_quality(g: Manager) -> dict:
    """Trafność i wynik inwestorów na świecach, których nie widzieli przy kuciu."""
    out = {}
    for s, seg in enumerate(SEGMENTS):
        seen = g.seen[s]
        if not seen.max():
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            hit = g.hits[s] / seen * 100
            net = g.nets[s] / seen
        out[seg] = {
            "decyzje": int(seen.max()),
            "trafnosc_srednia": [_num(x, 2) for x in hit.mean(0)],
            "trafnosc_p95": [_num(x, 2) for x in np.quantile(hit, 0.95, axis=0)],
            "ponad_51": int((hit.mean(1) > 51).sum()),
            "ponad_50": int((hit.mean(1) > 50).sum()),
            "net_atr": [_num(x, 4) for x in net.mean(0)],
        }
    return out


def pl(x, d: int = 2, sign: bool = False) -> str:
    """Liczba po polsku: przecinek i prawdziwy minus."""
    t = f"{float(x):+.{d}f}" if sign else f"{float(x):.{d}f}"
    return t.replace(".", ",").replace("-", "−")


def conclusions(st: dict) -> list[dict]:
    """Automatyczne, dosłowne wnioski: te same progi przy każdym przeliczeniu. Rozstrzyga najczystszy odcinek, który ma dane."""
    L = []
    books = st["books"]
    seg = "LIVE" if (books["a"]["seg"]["LIVE"]["n"] or 0) >= 200 else "OOS" if (books["a"]["seg"]["OOS"]["n"] or 0) else "MAPY"
    q = st["quality"].get(seg) or {}
    z = st["zero"][0].get("quality", {}).get(seg, {}) if st.get("zero") else {}
    if q:
        h = float(np.nanmean(np.array(q["trafnosc_srednia"], float)))
        msg = f"Inwestorzy na świecach, których nie widzieli ({seg}): średnia trafność {pl(h)}%"
        if z:
            msg += f" (na danych bez przewagi {pl(np.nanmean(np.array(z['trafnosc_srednia'], float)))}%)"
        L.append({"state": "ok" if h >= 51 else "warn" if h >= 50.3 else "bad", "text": msg + ". Przewaga wymaga wyraźnie ponad 50%."})
    a, b, c = books["a"]["seg"][seg], books["b"]["seg"][seg], books["c"]["seg"][seg]
    if a["n"]:
        L.append({"state": "ok" if (a["t_gross"] or 0) >= 2 else "warn" if (a["gross"] or 0) > 0 else "bad",
                  "text": f"Demokracja ({seg}): {pl(a['gross'], 2, True)} pipsa brutto na transakcję (t {pl(a['t_gross'] or 0, 1)}), "
                          f"{pl(a['net'], 2, True)} netto, wygrane {pl(a['win'], 1)}%."})
    u = st["meaning"].get(seg, {}).get("uczenie", {}).get("z_vs_wynik", {})
    if u.get("rho") is not None:
        good = u["p"] < 0.05 and u["rho"] > 0
        L.append({"state": "ok" if good else "bad",
                  "text": f"Czy mapy przewidują wynik ({seg}): korelacja rang z i wyniku {pl(u['rho'], 3, True)}, p = {pl(u['p'], 3)}. "
                          + ("Wyższe z idzie w parze z lepszym wynikiem." if good else "Na razie brak dowodu, że mapy coś przewidują.")})
    for name, x in (("Mapy", b), ("Reputacja", c)):
        if x["n"] and a["n"]:
            better = (x["net"] or 0) > (a["net"] or 0)
            L.append({"state": "ok" if better and (x["net"] or 0) > 0 else "warn" if better else "bad",
                      "text": f"{name} kontra demokracja ({seg}): {pl(x['net'], 2, True)} vs {pl(a['net'], 2, True)} "
                              f"pipsa netto na transakcję "
                              f"({x['n']} vs {a['n']} transakcji)."})
    n_eff = st["forge"].get("n_eff")
    if n_eff:
        L.append({"state": "ok" if n_eff >= 50 else "warn",
                  "text": f"Różnorodność: {st['n_investors']} inwestorów to około {n_eff:.0f} niezależnych głosów "
                          f"(średnia |korelacja| {pl(st['forge']['srednia_abs_rho'], 3)})."})
    return L


def top_maps(g: Manager, df: pd.DataFrame, n: int = 12) -> dict:
    k = g.n_mem
    if not k:
        return {"zysk": [], "strata": []}
    pts = g.mem_pts[:k]
    seqs = g.mem_seq[:k]
    order = np.argsort(pts, kind="stable")

    def item(j):
        r = df.iloc[int(seqs[j])]
        za = max(int(r["buy"]), int(r["sell"]))
        return {
            "seq": int(r["seq"]),
            "punkty": int(pts[j]),
            "pair": r["pair"],
            "ts": int(r["ts"]),
            "dir": int(r["dir"]),
            "h": int(r["h"]),
            "za": za,
            "przeciw": 1000 - za if g.forest.m == 1000 else g.forest.m - za,
        }

    return {"zysk": [item(j) for j in order[::-1][:n] if pts[j] > 0], "strata": [item(j) for j in order[:n] if pts[j] < 0]}


def build_state(g: Manager, pn: Panel, now: int | None = None) -> tuple[dict, dict]:
    now = int(time.time()) if now is None else int(now)
    df = g.frame()
    last_px = {p: float(pn.P[p]["c"][-1]) for p in pn.pairs}
    books, trades = {}, {}
    for b, name in BOOKS.items():
        st, tt = book_stats(book_trades(df, b, last_px) if len(df) else pd.DataFrame(columns=EMPTY_TRADES))
        books[b] = {"name": name, **st}
        trades[b] = tt
    pos = []
    for b in BOOKS:
        tt = trades[b]
        for r in tt[tt["status"] == "otwarta"].itertuples() if len(tt) else []:
            pos.append(
                {
                    "book": b,
                    "pair": r.pair,
                    "dir": int(r.dir),
                    "h": int(r.h),
                    "entry_ts": int(r.entry_ts),
                    "entry_px": float(r.entry_px),
                    "wycena": _num(r.pips_net, 2),
                    "pnl_usd": _num(r.pnl_usd, 2),
                    "seq": int(r.seq),
                }
            )
    fr = g.fr
    st = {
        "id": fr["id"],
        "version": fr["version"],
        "engine_version": fr["engine_version"],
        "created": fr["created"],
        "computedAt": now,
        "dataTo": int(pn.ts.max()) + H,
        "cursor": max(g.cursor.values()),
        "cuts": fr["cuts"],
        "pairs": fr["pairs"],
        "families": list(FR.FAMILIES),
        "n_investors": g.forest.m,
        "params": {
            "K_MAPS": K_MAPS,
            "MIN_MAPS": MIN_MAPS,
            "Z_MIN": Z_MIN,
            "BOOK_PCT": BOOK_PCT,
            "LEVERAGE": LEVERAGE,
            "START_CAPITAL": START_CAPITAL,
        },
        "forge": fr["forge"],
        "zero": fr.get("zero") or [],
        "oos_open": bool(fr.get("oos_open", True)),
        "counts": {
            "decyzje": len(df),
            "zamkniete": int((df["known"] == NH).sum()) if len(df) else 0,
            "mapy": g.n_mem,
            "zyskowne": g.n_win,
            "stratne": g.n_loss,
        },
        "books": books,
        "open": pos,
        "now": g.view_now(pn),
        "meaning": meaning(df) if len(df) else {},
        "quality": forest_quality(g),
        "maps": top_maps(g, df) if len(df) else {},
        "mapa_zysku": hex_votes(g.forest.pack(g.pos > 0)),
        "mapa_straty": hex_votes(g.forest.pack(g.neg > 0)),
        "order": [int(i) for i in np.lexsort((np.arange(g.forest.m), g.forest.fam_idx))],
        "fam": [int(x) for x in g.forest.fam_idx],
    }
    st["months"] = sorted(pd.to_datetime(df["ts"], unit="s", utc=True).dt.strftime("%Y-%m").unique().tolist()) if len(df) else []
    st["conclusions"] = conclusions(st) if len(df) else []
    return st, trades


def _table(rows: list[dict]) -> list[str]:
    L = ["| przedział | n | wygrane % | brutto (pips) | netto (pips) | t netto |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['band']} | {r['n']} | {r['win']} | {r['gross']} | {r['net']} | {r['t']} |")
    return L


def report(st: dict) -> str:
    c = st["cuts"]
    day = lambda x: time.strftime("%Y-%m-%d", time.gmtime(x))  # noqa: E731
    f = st["forge"]
    L = [
        f"# FOREST (D-048) — las {st['id']}",
        "",
        f"- Silnik {st['engine_version']} · FOREST {st['version']} · dane do {day(st['dataTo'])} · świece H1 Yahoo po czyszczeniu, 8 par.",
        f"- KUCIE {day(c['t0'])} – {day(c['forge'])}; MAPY do {day(c['oos'])}; OOS do {day(c['t1'])}; LIVE później.",
        f"- Kandydaci: {f['candidates']:,}, po bramkach kucia {f['passed']:,}, wybrani {st['n_investors']} "
        f"(limit |ρ| ≤ {f['rho_cap']}, rodzina ≤ 25%).",
        f"- Różnorodność: N_eff {f.get('n_eff', 0):.1f}, średnia |ρ| {f.get('srednia_abs_rho', 0):.3f}, "
        f"p95 {f.get('p95_abs_rho', 0):.3f}. Rodziny: {f.get('rodziny')}.",
        f"- Parametry ustalone przed liczeniem, niedobierane: K = {K_MAPS}, min. map = {MIN_MAPS}, z ≥ {Z_MIN} (księga B). "
        f"Depozyt {BOOK_PCT:g}% kapitału, dźwignia {LEVERAGE}:1.",
        "",
        "## Wnioski",
        "",
    ]
    L += [f"- [{x['state']}] {x['text']}" for x in st["conclusions"]]
    L += [
        "",
        "## Księgi",
        "",
        "| księga | odcinek | transakcje | wygrane % | brutto | netto | t netto | t brutto | wynik USD |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for b, x in st["books"].items():
        for seg, v in x["seg"].items():
            if v["n"]:
                L.append(
                    f"| {b.upper()} {x['name']} | {seg} | {v['n']} | {v['win']} | {v['gross']} | {v['net']} | {v['t']} "
                    f"| {v['t_gross']} | {v['usd']} |"
                )
    L += ["", "| księga | kapitał | wynik % | maks. obsunięcie % | zamknięte | otwarte | anulowane |", "|---|---|---|---|---|---|---|"]
    for b, x in st["books"].items():
        L.append(
            f"| {b.upper()} {x['name']} | {x['equity']} | {x['return_pct']} | {x['max_dd_pct']} | {x['closed']} | {x['open']} "
            f"| {x['cancelled']} |"
        )
    L += [
        "",
        "## Inwestorzy na świecach niewidzianych przy kuciu",
        "",
        "| odcinek | decyzje | średnia trafność h=1…5 | p95 | ponad 50% | ponad 51% |",
        "|---|---|---|---|---|---|",
    ]
    for seg, q in st["quality"].items():
        L.append(f"| {seg} | {q['decyzje']} | {q['trafnosc_srednia']} | {q['trafnosc_p95']} | {q['ponad_50']} | {q['ponad_51']} |")
    for z in st["zero"]:
        L += [
            "",
            f"### Test zerowy: to samo na danych bez przewagi (nasiono {z['seed']})",
            "",
            f"- średnia CV kucia: prawdziwe {f.get('t_cv_mean', 0):.2f}, zerowe {z['forge']['t_cv_mean']:.2f}; "
            f"najlepszy kandydat: prawdziwe {f['t_cv_top'][0]:.2f}, zerowe {z['forge']['t_cv_top'][0]:.2f}; "
            f"po bramkach: prawdziwe {f['passed']:,}, zerowe {z['forge']['passed']:,}.",
        ]
        for seg, q in z["quality"].items():
            L.append(f"- {seg}: trafność {q['trafnosc_srednia']}, ponad 51%: {q['ponad_51']}.")
        for b, v in z["books"].items():
            for seg, s in v.items():
                if s["n"]:
                    L.append(f"- księga {b.upper()} {seg}: {s['n']} transakcji, brutto {s['gross']}, netto {s['net']}.")
        for seg, u in z["uczenie"].items():
            if u.get("rho") is not None:
                L.append(f"- mapy {seg}: ρ {u['rho']}, p {u['p']}.")
    for seg, t in st["meaning"].items():
        if not t["wszystkie"]["n"]:
            continue
        L += ["", f"## Co znaczy głos — {seg} (wszystkie decyzje, wirtualnie)", "", f"Razem: {t['wszystkie']}", f"Uczenie: {t['uczenie']}"]
        for key in ("przewaga", "z", "z_b", "dop", "horyzont", "kierunek", "para"):
            L += ["", f"### {t[key]['name']}", ""] + _table(t[key]["rows"])
    L += [
        "",
        "## Jak to czytać",
        "",
        "- Wynik MAPY to część IS (W1), OOS to ostatnie 25% historii, LIVE to nowe świece. Rozstrzyga LIVE.",
        "- Księga A jest grupą kontrolną: handluje zawsze, więc pokazuje pełny koszt spreadu. "
        "Mapy mają sens tylko wtedy, gdy B albo C biją A poza próbą.",
        "- t liczone na transakcji zakłada ich niezależność; decyzje na kolejnych świecach i parach są zależne, "
        "więc prawdziwa pewność jest niższa. p przy mapach pochodzi z obrotów w czasie i ten problem omija.",
        "- Nie dobieraj K, progu z ani okresu do wyniku OOS. Każda taka zmiana robi z OOS kolejne IS.",
    ]
    return "\n".join(L)


JOURNAL_DROP = ("known",)


def write_public(g: Manager, pn: Panel, folder: Path, now: int | None = None) -> dict:
    """Pliki dla gałęzi data: state.json, investors.json, report.md, journal/{RRRR-MM}.parquet (z pełną mapą głosów)."""
    st, trades = build_state(g, pn, now)
    new = folder.with_name(folder.name + ".new")
    if new.exists():
        shutil.rmtree(new)
    (new / "journal").mkdir(parents=True)
    (new / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    (new / "investors.json").write_text(
        json.dumps({"id": st["id"], "investors": investor_rows(g)}, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    (new / "report.md").write_text(report(st), encoding="utf-8")
    df = g.frame()
    if len(df):
        df["votes"] = [hex_votes(b) for b in g.bits]
        for b in BOOKS:
            tt = trades[b]
            for col, src in (("usd", "pnl_usd"), ("kap", "equity_after")):
                df[f"{col}_{b}"] = np.nan
                if len(tt):
                    df.loc[tt["seq"].to_numpy(int), f"{col}_{b}"] = tt[src].to_numpy(float)
        month = pd.to_datetime(df["ts"], unit="s", utc=True).dt.strftime("%Y-%m")
        for m, part in df.groupby(month):
            part.reset_index(drop=True).to_parquet(new / "journal" / f"{m}.parquet", index=False)
    if folder.exists():
        shutil.rmtree(folder)
    new.replace(folder)
    return st
