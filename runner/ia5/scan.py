"""Skaner hipotez (D-037): szerokie przeszukanie prostych reguł na wszystkich parach, z kontrolą wielokrotnych prób.

Po co: pojedyncza strategia oceniana na tych samych danych, na których ją wymyślono, to anegdota. Skaner liczy
dziesiątki tysięcy (wariant `--duzy`: setki tysięcy) prostych reguł naraz i przepuszcza tylko te, które:
  1. są istotne w okresie ODKRYCIA (pierwsze 50% historii) po korekcie Benjaminiego–Hochberga (FDR 5%)
     na WSZYSTKIE przetestowane reguły — im więcej reguł, tym wyższa poprzeczka;
  2. powtarzają się w okresie POTWIERDZENIA (50–75% historii): ten sam znak, t ≥ 2;
  3. mają sąsiadów: reguły różniące się o krok parametru też są dodatnie (płaskowyż, nie pojedynczy pik).
Ostatnie 25% historii (OOS silnika, W1) skaner pomija CAŁKOWICIE — nie liczy tam nic, więc wybór reguł nie może
podejrzeć wyniku, na którym potem ocenia je silnik. Wynik skanera to hipotezy, nie werdykt; werdykt daje
dopiero zwykłe liczenie strategii (silnik, benchmark losowy, DSR, PBO) z OOS.

Rodziny reguł (wszystkie na cenie mid, koszt = spread z tabeli raz na transakcję, B3):
  sezon   — wejście na open świecy o godzinie `a` czasu Londynu, wyjście na close świecy a+L−1; kierunek ±;
            filtr dnia tygodnia (wszystkie / pon…pt); [--duzy: także filtr miesiąca].
  impuls  — zdarzenie: ruch z k świec w jednostkach ATR14·√k przecina próg th (w górę albo w dół);
            wejście na open następnej świecy, kierunek „za ruchem” (mom) albo „przeciw” (rev), wyjście po L świecach;
            filtr sesji wejścia (wszystkie / Azja / Europa / USA, czas Londynu).
  trend   — o godzinie a czasu Londynu: znak zmiany ceny z D dni → pozycja za trendem (mom) albo przeciw (rev)
            na L świec (do 480).
Transakcje jednej reguły nigdy się nie nakładają (zdarzenie bliżej niż L świec od poprzedniego jest pomijane).
Transakcje nachodzące na przerwę w dostępie do danych albo na świecę uzupełnioną są pomijane (B12).
"""
from __future__ import annotations

import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import PAIRS

DISC, VAL = 0.50, 0.75          # granice okresów: odkrycie [0, 0.5), potwierdzenie [0.5, 0.75), OOS [0.75, 1] — pomijany
FDR_Q = 0.05
T_VAL = 2.0
H = 3600
SESSIONS = {"wszystkie": (0, 24), "azja": (0, 7), "europa": (7, 13), "usa": (13, 21)}   # godziny Londynu


def grid(big: bool = False) -> dict:
    """Standardowa: ~5,7 tys. reguł na parę (sekundy). Duża (`--duzy`): ~160 tys. na parę, ~1,3 mln na 8 par (minuty)."""
    if not big:
        return {
            "sezon": {"a": list(range(24)), "L": [1, 2, 3, 4, 5, 6, 8, 10, 12], "wd": ["wszystkie", 0, 1, 2, 3, 4],
                      "mies": ["wszystkie"]},
            "impuls": {"k": [1, 2, 3, 4, 6, 8, 12, 24, 48], "th": [1.0, 1.5, 2.0, 2.5, 3.0],
                       "L": [1, 2, 3, 4, 6, 8, 12, 24], "sesja": list(SESSIONS)},
            "trend": {"D": [1, 2, 3, 5, 10, 20, 60], "a": [0, 7, 13], "L": [24, 48, 120, 240, 480]},
        }
    return {
        "sezon": {"a": list(range(24)), "L": list(range(1, 25)), "wd": ["wszystkie", 0, 1, 2, 3, 4],
                  "mies": ["wszystkie", *range(1, 13)]},
        "impuls": {"k": [1, 2, 3, 4, 6, 8, 12, 24, 48, 72, 120], "th": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0],
                   "L": [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24, 36, 48], "sesja": list(SESSIONS) + [f"h{h}" for h in range(24)]},
        "trend": {"D": [1, 2, 3, 5, 10, 20, 40, 60, 120, 250], "a": list(range(24)), "L": [24, 48, 120, 240, 480]},
    }


def session_hours(name: str) -> tuple[int, int]:
    """Sesja albo pojedyncza godzina wejścia „hN” (czas Londynu)."""
    if name.startswith("h"):
        h = int(name[1:])
        return h, h + 1
    return SESSIONS[name]


# ---------- dane ----------

def prepare(df: pd.DataFrame, pair: str) -> dict:
    df = df.reset_index(drop=True)
    ts = df["ts"].to_numpy(np.int64)
    lon = pd.to_datetime(ts, unit="s", utc=True).tz_convert("Europe/London")
    filled = df["filled"].to_numpy(bool) if "filled" in df else np.zeros(len(df), bool)
    gap = (df["gap_before"].to_numpy(np.int64) > 0) if "gap_before" in df else np.zeros(len(df), bool)
    return {
        "pair": pair, "ts": ts, "o": df["open"].to_numpy(float), "c": df["close"].to_numpy(float),
        "hour": np.asarray(lon.hour), "wd": np.asarray(lon.dayofweek), "month": np.asarray(lon.month),
        "day": np.asarray(lon.normalize().asi8 // 10**9), "atr": ind.atr(df, 14).to_numpy(),
        "filled": filled, "gapcum": np.concatenate([[0], np.cumsum(gap)]),
        "pip": PAIRS[pair].pip, "spread": PAIRS[pair].spread_pips,
    }


def trades(P: dict, entry: np.ndarray, L: int) -> tuple[np.ndarray, np.ndarray]:
    """Wejście na open `entry`, wyjście na close entry+L−1. Zwraca (entry, ruch w pipsach brutto, long) po odrzuceniu
    transakcji bez danych do wyjścia, na przerwie w dostępie do danych albo na świecy uzupełnionej (B12)."""
    n = len(P["o"])
    e = entry[(entry >= 1) & (entry + L - 1 < n)]
    x = e + L - 1
    ok = (P["gapcum"][x + 1] - P["gapcum"][e] == 0) & ~P["filled"][e - 1] & ~P["filled"][e] & ~P["filled"][x]
    e, x = e[ok], x[ok]
    return e, (P["c"][x] - P["o"][e]) / P["pip"]


def spaced(e: np.ndarray, L: int) -> np.ndarray:
    """Bez nakładania: zdarzenie bliżej niż L świec od POPRZEDNIEGO zdarzenia jest pomijane (ostrożnie: nigdy nie
    zostają dwie nakładające się transakcje, choć czasem odpada też taka, która by się zmieściła)."""
    if len(e) < 2:
        return e
    keep = np.r_[True, np.diff(e) >= L]
    return e[keep]


# ---------- statystyka ----------

def stats(r: np.ndarray) -> tuple[int, float, float]:
    n = len(r)
    if n < 2:
        return n, float("nan"), float("nan")
    m, s = float(r.mean()), float(r.std(ddof=1))
    return n, m, (m / (s / math.sqrt(n)) if s > 0 else float("nan"))


def bh_threshold(p: np.ndarray, q: float) -> float:
    """Benjamini–Hochberg: największe p, które przechodzi; reguły z p ≤ próg są „odkryte”."""
    p = np.sort(p[~np.isnan(p)])
    m = len(p)
    if m == 0:
        return 0.0
    ok = p <= q * np.arange(1, m + 1) / m
    return float(p[np.flatnonzero(ok)[-1]]) if ok.any() else 0.0


def p_one_sided(t: float) -> float:
    return float("nan") if math.isnan(t) else 0.5 * math.erfc(t / math.sqrt(2))


# ---------- rodziny ----------

def _emit(rows, P, family, params, e, gross, direction, cuts):
    """Jeden wiersz na regułę: statystyki netto (po spreadzie) w odkryciu i potwierdzeniu. OOS nie jest liczony."""
    net = direction * gross - P["spread"]
    t = P["ts"][e]
    d = net[t < cuts[0]]
    v = net[(t >= cuts[0]) & (t < cuts[1])]
    nd, md, td = stats(d)
    nv, mv, tv = stats(v)
    rows.append({"pair": P["pair"], "family": family, **params, "dir": int(direction),
                 "n_disc": nd, "mean_disc": md, "t_disc": td, "n_val": nv, "mean_val": mv, "t_val": tv})


def scan_season(P, g, cuts, rows):
    weekday = P["wd"] < 5
    for a in g["a"]:
        base = np.flatnonzero((P["hour"] == a) & weekday)
        for L in g["L"]:
            e, gross = trades(P, base, L)
            for wd, mo in itertools.product(g["wd"], g["mies"]):
                m = np.ones(len(e), bool)
                if wd != "wszystkie":
                    m &= P["wd"][e] == wd
                if mo != "wszystkie":
                    m &= P["month"][e] == mo
                for direction in (1, -1):
                    _emit(rows, P, "sezon", {"a": a, "L": L, "wd": str(wd), "mies": str(mo)}, e[m], gross[m], direction, cuts)


def scan_impulse(P, g, cuts, rows):
    c, atr = P["c"], P["atr"]
    for k in g["k"]:
        move = np.full(len(c), np.nan)
        move[k:] = (c[k:] - c[:-k]) / (atr[k:] * math.sqrt(k))
        prev = np.r_[np.nan, move[:-1]]
        for th in g["th"]:
            up = np.flatnonzero((move > th) & (prev <= th)) + 1      # wejście na open świecy po zdarzeniu
            dn = np.flatnonzero((move < -th) & (prev >= -th)) + 1
            for L in g["L"]:
                ev = np.r_[up, dn]
                side = np.r_[np.ones(len(up)), -np.ones(len(dn))]
                order = np.argsort(ev, kind="stable")
                ev, side = ev[order], side[order]
                keep = np.r_[True, np.diff(ev) >= L] if len(ev) > 1 else np.ones(len(ev), bool)
                ev, side = ev[keep], side[keep]
                e, gross = trades(P, ev, L)
                side = side[np.isin(ev, e)]
                for ses in g["sesja"]:
                    h0, h1 = session_hours(ses)
                    m = (P["hour"][e] >= h0) & (P["hour"][e] < h1)
                    for mode, direction in (("mom", 1), ("rev", -1)):
                        _emit(rows, P, "impuls", {"k": k, "th": th, "L": L, "sesja": ses, "tryb": mode},
                              e[m], gross[m] * side[m], direction, cuts)


def scan_trend(P, g, cuts, rows):
    c = P["c"]
    day_close = pd.Series(c).groupby(P["day"]).last()
    for D in g["D"]:
        chg = day_close.diff(D).shift(1)            # zmiana z D ZAMKNIĘTYCH dni (bez dnia bieżącego)
        sign = np.sign(pd.Series(P["day"]).map(chg).to_numpy())
        for a in g["a"]:
            base = np.flatnonzero((P["hour"] == a) & (P["wd"] < 5) & (sign != 0) & ~np.isnan(sign))
            for L in g["L"]:
                ev = spaced(base, L)
                e, gross = trades(P, ev, L)
                s = sign[e]
                for mode, direction in (("mom", 1), ("rev", -1)):
                    _emit(rows, P, "trend", {"D": D, "a": a, "L": L, "tryb": mode}, e, gross * s, direction, cuts)


# ---------- całość ----------

def run(frames: dict[str, pd.DataFrame], big: bool = False, log=print, min_disc: int = 100, min_val: int = 50) -> dict:
    t_start = time.time()
    g = grid(big)
    t0 = min(int(df["ts"].iloc[0]) for df in frames.values())
    t1 = max(int(df["ts"].iloc[-1]) for df in frames.values())
    cuts = (t0 + DISC * (t1 - t0), t0 + VAL * (t1 - t0))
    parts = []
    for pair, df in frames.items():
        P = prepare(df, pair)
        rows: list[dict] = []
        scan_season(P, g["sezon"], cuts, rows)
        scan_impulse(P, g["impuls"], cuts, rows)
        scan_trend(P, g["trend"], cuts, rows)
        parts.append(pd.DataFrame(rows))   # ramka na parę — lista słowników nie rośnie do milionów naraz
        log(f"  {pair}: {len(rows):,} reguł ({time.time() - t_start:.0f} s)")
    res = pd.concat(parts, ignore_index=True)
    tested = int(len(res))
    res = res[(res.n_disc >= min_disc) & (res.n_val >= min_val)].copy()
    res["p_disc"] = [p_one_sided(t) for t in res.t_disc]
    thr = bh_threshold(res.p_disc.to_numpy(), FDR_Q)
    res["odkryta"] = res.p_disc <= thr
    res["potwierdzona"] = res.odkryta & (res.mean_val > 0) & (res.t_val >= T_VAL)
    res["sasiedzi"] = neighbours(res)
    res["robust"] = res[["t_disc", "t_val"]].min(axis=1)
    surv = res[res.potwierdzona].sort_values("robust", ascending=False)
    t_bh = float(np.sqrt(2) * _erfcinv(2 * thr)) if thr > 0 else float("nan")
    return {"tested": tested, "eligible": int(len(res)), "discovered": int(res.odkryta.sum()),
            "confirmed": int(len(surv)), "p_threshold": thr, "t_threshold": t_bh, "cuts": [int(x) for x in cuts],
            "t0": t0, "t1": t1, "pairs": sorted(frames), "big": big, "seconds": round(time.time() - t_start, 1),
            "survivors": surv, "all": res}


def _erfcinv(y: float) -> float:
    """Odwrotność erfc przez bisekcję (bez scipy)."""
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if math.erfc(mid) > y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def neighbours(res: pd.DataFrame) -> pd.Series:
    """Udział sąsiadów (ta sama reguła, jeden parametr o krok obok) z dodatnią średnią w odkryciu I potwierdzeniu."""
    keys = {"sezon": ["a", "L"], "impuls": ["k", "th", "L"], "trend": ["D", "L"]}
    out = pd.Series(np.nan, index=res.index)
    for fam, cols in keys.items():
        sub = res[res.family == fam]
        if sub.empty:
            continue
        fixed = [c for c in sub.columns if c not in cols and c not in
                 ("n_disc", "mean_disc", "t_disc", "n_val", "mean_val", "t_val", "p_disc", "odkryta", "potwierdzona")]
        fixed = [c for c in fixed if sub[c].notna().all()]
        good = ((sub.mean_disc > 0) & (sub.mean_val > 0))
        index = {tuple(r): g for r, g in zip(sub[fixed + cols].itertuples(index=False, name=None), good)}
        levels = {c: sorted(sub[c].dropna().unique()) for c in cols}
        shares = []
        for row in sub[fixed + cols].itertuples(index=False, name=None):
            base, vals = row[:len(fixed)], list(row[len(fixed):])
            hits = tot = 0
            for i, c in enumerate(cols):
                lv = levels[c]
                j = lv.index(vals[i])
                for jj in (j - 1, j + 1):
                    if 0 <= jj < len(lv):
                        nb = vals.copy()
                        nb[i] = lv[jj]
                        key = (*base, *nb)
                        if key in index:
                            tot += 1
                            hits += bool(index[key])
            shares.append(hits / tot if tot else np.nan)
        out[sub.index] = shares
    return out


def describe(r: dict) -> str:
    """Reguła słowami (do raportu)."""
    pair = r["pair"]
    d = "long" if r["dir"] > 0 else "short"
    if r["family"] == "sezon":
        wd = "" if r["wd"] == "wszystkie" else f", tylko {['pon', 'wt', 'śr', 'czw', 'pt'][int(r['wd'])]}"
        mo = "" if str(r.get("mies", "wszystkie")) == "wszystkie" else f", tylko miesiąc {r['mies']}"
        return f"{pair} {d} od {int(r['a']):02d}:00 Londynu przez {int(r['L'])} h{wd}{mo}"
    if r["family"] == "impuls":
        mode = "za ruchem" if (r["tryb"] == "mom") == (r["dir"] > 0) else "przeciw ruchowi"
        return (f"{pair}: po ruchu > {r['th']:g}×ATR14·√k z {int(r['k'])} świec — {mode}, {int(r['L'])} świec, "
                f"sesja {r['sesja']}")
    mode = "za trendem" if (r["tryb"] == "mom") == (r["dir"] > 0) else "przeciw trendowi"
    return f"{pair}: o {int(r['a']):02d}:00 Londynu {mode} z {int(r['D'])} dni, {int(r['L'])} świec"


def report(out: dict, top: int = 40) -> str:
    from datetime import UTC, datetime

    def dt(x):
        return datetime.fromtimestamp(x, UTC).strftime("%Y-%m-%d")

    s = out["survivors"]
    lines = [
        "# Skan hipotez (D-037)", "",
        f"Pary: {', '.join(out['pairs'])} · historia {dt(out['t0'])} – {dt(out['t1'])} · siatka {'duża' if out['big'] else 'standardowa'}"
        f" · {out['seconds']} s", "",
        f"- Odkrycie: {dt(out['t0'])} – {dt(out['cuts'][0])}; potwierdzenie: do {dt(out['cuts'][1])}; "
        "**ostatnie 25% (OOS silnika) nie było liczone**.",
        f"- **Przetestowane reguły: {out['tested']:,}** (z wystarczającą liczbą transakcji: {out['eligible']:,}).",
        f"- Próg odkrycia po korekcie FDR 5% na wszystkie reguły: p ≤ {out['p_threshold']:.2e} "
        f"(t ≥ {out['t_threshold']:.2f}); odkrytych: {out['discovered']:,}.",
        f"- Potwierdzone w drugim okresie (średnia > 0, t ≥ {T_VAL:g}): **{out['confirmed']:,}**.", "",
    ]
    if s.empty:
        lines += ["Żadna reguła nie przeszła obu progów. To też wynik: w tej rodzinie reguł nie ma przewagi, "
                  "która przetrwałaby uczciwe liczenie."]
        return "\n".join(lines)
    lines += ["## Potwierdzone reguły (ranking: mniejsze z t odkrycia i t potwierdzenia)", "",
              "| # | reguła | n odkr. | pips netto odkr. | t odkr. | n potw. | pips netto potw. | t potw. | sąsiedzi + |",
              "|---|---|---|---|---|---|---|---|---|"]
    for i, (_, r) in enumerate(s.head(top).iterrows(), 1):
        nb = "—" if pd.isna(r.sasiedzi) else f"{r.sasiedzi:.0%}"
        lines.append(f"| {i} | {describe(r)} | {int(r.n_disc)} | {r.mean_disc:+.2f} | {r.t_disc:.1f} | {int(r.n_val)} | "
                     f"{r.mean_val:+.2f} | {r.t_val:.1f} | {nb} |")
    by = s.groupby(["pair", "family"]).size().rename("liczba").reset_index()
    lines += ["", "## Potwierdzone według pary i rodziny", "", "| para | rodzina | reguł |", "|---|---|---|"]
    lines += [f"| {r.pair} | {r.family} | {r.liczba} |" for r in by.itertuples()]
    lines += ["", "Następny krok: najlepsze reguły (z sąsiadami ≥ 60%) zamienić w strategię i policzyć silnikiem — "
              "dopiero tam liczy się OOS, benchmark losowy, DSR i PBO."]
    return "\n".join(lines)


def save(out: dict, folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "scan.md").write_text(report(out), encoding="utf-8")
    cols = [c for c in out["survivors"].columns if c != "potwierdzona"]
    out["survivors"][cols].to_csv(folder / "survivors.csv", index=False)
    meta = {k: v for k, v in out.items() if k not in ("survivors", "all")}
    (folder / "scan.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    fam = out["all"].groupby(["pair", "family"]).agg(reguly=("t_disc", "size"), odkryte=("odkryta", "sum"),
                                                     potwierdzone=("potwierdzona", "sum"))
    fam.to_csv(folder / "summary.csv")
    return folder
