"""Przegląd zdrowia systemu (D-023): nazwane kontrole na pełnych danych, opisowo, z podpowiedzią co zrobić.

Uruchamiane przez `ia5 start` po każdej synchronizacji i co godzinę, ręcznie przez `ia5 health`.
Wynik w meta/status.health — dashboard i tak nasłuchuje tego dokumentu (Z2). Zgłasza, niczego nie naprawia (D5).

Każda kontrola: {"id", "name", "state": ok|warn|bad, "text", "detail": [...], "fix"}.
"""

from __future__ import annotations

import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import PAIRS
from .coverage import EMPTY, FAILED, INCOMPLETE, NONE, expected_hours
from .quality import bar_flags
from .session import H, expected_ts, is_expected_bar, last_closed_ts

RANK = {"ok": 0, "warn": 1, "bad": 2}
TRIANGLE_PIPS = {"EURJPY": 15.0, "EURGBP": 8.0}  # odchyłka godziny ponad próg = podejrzana
TRIANGLE_SHARE = 0.001  # > 0,1% podejrzanych godzin → uwaga
SOURCE_MEDIAN_PIPS = 3.0  # mediana różnicy zamknięć Yahoo vs Dukascopy
FROZEN_HOURS = 8  # tyle kolejnych identycznych zamknięć = zamrożony feed
STUCK_SECONDS = 2 * 3600
DISK_WARN, DISK_BAD = 5e9, 1e9


def utc(ts) -> str:
    return datetime.fromtimestamp(int(ts), UTC).strftime("%Y-%m-%d %H:%M") + " UTC"


def label(pair: str) -> str:
    return f"{pair[:3]}/{pair[3:]}"


def fmt(n, d=0) -> str:
    return f"{n:,.{d}f}".replace(",", " ").replace(".", ",")


def pl(n: int, one: str, few: str, many: str) -> str:
    """Polska odmiana: 1 problem, 2 problemy, 5 problemów."""
    if n == 1:
        return one
    return few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many


def month_key(start: str, i: int) -> str:
    y, m = int(start[:4]), int(start[5:7]) - 1 + i
    return f"{y + m // 12}-{m % 12 + 1:02d}"


STATUS_PL = {"policzona": "policzone", "blad": "z błędem", "do_policzenia": "w kolejce", "liczy_sie": "w trakcie liczenia",
             "do_usuniecia": "do usunięcia"}


def check(cid, name, state, text, detail=None, fix=None) -> dict:
    return {"id": cid, "name": name, "state": state, "text": text, "detail": list(detail or [])[:12], "fix": fix}


# ---------- kontrole ----------


def yahoo_fresh(status: dict, now: int) -> dict:
    pairs = status.get("pairs") or {}
    if not pairs:
        return check(
            "yahoo_fresh", "Świeże dane Yahoo", "bad", "W bazie nie ma świec Yahoo.", fix="Uruchom setup() w Apps Script (docs/SETUP.md)."
        )
    exp = expected_ts(now)
    late = {p: pairs.get(p, {}).get("lastTs", 0) for p in PAIRS if pairs.get(p, {}).get("lastTs", 0) < exp}
    closed = not is_expected_bar(last_closed_ts(now) + H) and not is_expected_bar(last_closed_ts(now))
    if not late:
        return check(
            "yahoo_fresh",
            "Świeże dane Yahoo",
            "ok",
            "Rynek zamknięty, ostatnie świece są w bazie." if closed else f"Wszystkie pary mają świecę z {utc(exp)}.",
        )
    # od zamknięcia pierwszej brakującej świecy (nie tylko ostatniej oczekiwanej) — dłuższa awaria = dłuższy czas
    oldest = min(late.values())
    first_missing = next((int(t) for t in expected_hours(oldest + H, exp + H)), exp)
    mins = round((now - (first_missing + H)) / 60)
    state = "warn" if mins < 75 else "bad"
    return check(
        "yahoo_fresh",
        "Świeże dane Yahoo",
        state,
        f"{len(late)} z {len(PAIRS)} par bez nowych świec od {utc(first_missing + H)} "
        f"({f'{mins} min' if mins < 120 else f'{fmt(mins / 60, 0)} h'}).",
        [f"{label(p)}: ostatnia {utc(t) if t else 'brak'}" for p, t in late.items()],
        "Sprawdź arkusz „log” w Apps Script i czy wyzwalacz tick() co 5 min istnieje.",
    )


def apps_script(status: dict, now: int) -> dict:
    run = status.get("lastRun") or {}
    if not run:
        return check("apps_script", "Apps Script", "bad", "Brak śladu uruchomień Apps Script.", fix="Uruchom setup().")
    if run.get("ok") is False:
        return check(
            "apps_script",
            "Apps Script",
            "bad",
            f"Ostatnie uruchomienie zakończyło się błędem: {run.get('error')}",
            fix="Arkusz „log” → wiersze z BŁĄD; najczęściej Yahoo chwilowo nie odpowiada (samo przejdzie) albo wygasła autoryzacja.",
        )
    return check(
        "apps_script",
        "Apps Script",
        "ok",
        f"Ostatnie uruchomienie bez błędów, {utc(run.get('finishedAt') or run.get('startedAt') or now)}.",
    )


def yahoo_flags(status: dict) -> dict:
    items = [(p, f) for p, v in (status.get("pairs") or {}).items() for f in (v.get("flags") or [])]
    items += [("trójkąt", f) for f in ((status.get("cross") or {}).get("flags") or [])]
    if not items:
        return check("yahoo_flags", "Jakość świec Yahoo", "ok", "Ostatnie pobrania przeszły kontrolę świec (OHLC, czas, luki, korekty).")
    return check(
        "yahoo_flags",
        "Flagi jakości Yahoo",
        "warn",
        f"{len(items)} flag z ostatnich pobrań Yahoo.",
        [f"{p}: {f}" for p, f in items],
        "Lista w Stats → Flagi. Luki i korekty Yahoo nie wpływają na backtesty (te liczą się z Dukascopy).",
    )


def duka_fresh(h1: dict, until_ts: int) -> dict:
    if not h1 or all(df is None or df.empty for df in h1.values()):
        return check(
            "duka_fresh",
            "Aktualność Dukascopy",
            "bad",
            "Brak świec Dukascopy na Macu.",
            fix="ia5 start pobierze historię (pierwszy raz 1–3 godziny).",
        )
    late = []
    for p, df in h1.items():
        last = int(df["ts"].max()) if df is not None and len(df) else 0
        missing = len(expected_hours(last + H, until_ts)) if last else None
        if missing is None or missing > 24:
            late.append(f"{label(p)}: ostatnia {utc(last) if last else 'brak'}")
    if late:
        return check(
            "duka_fresh",
            "Aktualność Dukascopy",
            "warn",
            f"{len(late)} par z danymi starszymi niż doba sesji.",
            late,
            "Uruchom ia5 start; jeśli nie pomaga — Dukascopy mogło jeszcze nie opublikować dnia.",
        )
    return check("duka_fresh", "Aktualność Dukascopy", "ok", f"Wszystkie pary mają dane do {utc(until_ts - H)}.")


def triangles(h1: dict) -> dict:
    """Trójkąty na całej historii, godzina po godzinie: EUR/JPY ≈ EUR/USD×USD/JPY, EUR/GBP ≈ EUR/USD÷GBP/USD."""
    rows, detail, worst_state = [], [], "ok"
    for target, (a, b, op) in {"EURJPY": ("EURUSD", "USDJPY", np.multiply), "EURGBP": ("EURUSD", "GBPUSD", np.divide)}.items():
        frames = [h1.get(x) for x in (target, a, b)]
        if any(f is None or f.empty for f in frames):
            continue
        j = frames[0][["ts", "close"]].rename(columns={"close": "t"})
        j = j.merge(frames[1][["ts", "close"]].rename(columns={"close": "a"}), on="ts").merge(
            frames[2][["ts", "close"]].rename(columns={"close": "b"}), on="ts"
        )
        if j.empty:
            continue
        dev = np.abs(j["t"] - op(j["a"], j["b"])) / PAIRS[target].pip
        bad = dev > TRIANGLE_PIPS[target]
        share = float(bad.mean())
        rows.append(
            f"{label(target)}: mediana {fmt(dev.median(), 2)} pips, 99% godzin poniżej {fmt(dev.quantile(0.99), 1)} pips, "
            f"podejrzanych {fmt(bad.sum())} z {fmt(len(j))} (> {fmt(TRIANGLE_PIPS[target])} pips)"
        )
        if share > TRIANGLE_SHARE:
            worst_state = "warn"
            mon = pd.to_datetime(j["ts"], unit="s", utc=True).dt.strftime("%Y-%m").to_numpy()
            months = pd.Series(bad.to_numpy(), index=mon).groupby(level=0).sum()
            for m, n in months[months > 0].sort_values(ascending=False).head(5).items():
                mx = dev.to_numpy()[bad.to_numpy() & (mon == m)].max()
                detail.append(f"{label(target)} {m}: {n} podejrzanych godzin, maks. {fmt(mx, 1)} pips")
    if not rows:
        return check("triangles", "Spójność par (trójkąty)", "warn", "Brak danych do porównania trójkątów.")
    text = (
        "Pary zgadzają się ze sobą na całej historii."
        if worst_state == "ok"
        else "W części godzin para nie zgadza się z dwiema pozostałymi — błędna cena, przesunięty czas albo zamrożony feed w jednej z nich."
    )
    return check(
        "triangles",
        "Spójność par (trójkąty)",
        worst_state,
        text,
        rows + detail,
        None if worst_state == "ok" else "Otwórz te miesiące w mapie pokrycia; jeśli to jedna para — porównaj ją z Yahoo.",
    )


def sources(h1: dict, yahoo: dict) -> dict:
    """Dukascopy vs Yahoo na wspólnych godzinach; wykrywa też przesunięcie czasu o ±1 h."""
    rows, problems = [], []
    for p in PAIRS:
        d, y = h1.get(p), yahoo.get(p)
        if d is None or y is None or d.empty or y.empty:
            continue
        res = {}
        for shift in (-H, 0, H):
            j = d[["ts", "close"]].merge(y[["ts", "close"]].assign(ts=y["ts"] + shift), on="ts", suffixes=("_d", "_y"))
            if len(j) >= 24:
                res[shift] = float(((j["close_d"] - j["close_y"]).abs() / PAIRS[p].pip).median())
        if 0 not in res:
            continue
        rows.append(f"{label(p)}: mediana różnicy zamknięć {fmt(res[0], 2)} pips")
        best = min(res, key=res.get)
        if best != 0 and res[best] < res[0] / 2:
            problems.append(
                f"{label(p)}: zgodność lepsza po przesunięciu Yahoo o {best // H:+d} h ({fmt(res[best], 2)} vs {fmt(res[0], 2)} pips)"
            )
        elif res[0] > SOURCE_MEDIAN_PIPS:
            problems.append(f"{label(p)}: mediana {fmt(res[0], 2)} pips — więcej niż {fmt(SOURCE_MEDIAN_PIPS)}")
    if not rows:
        return check(
            "sources",
            "Dukascopy vs Yahoo",
            "warn",
            "Brak wspólnych świec do porównania.",
            fix="Pojawią się po ia5 start, gdy oba źródła będą na Macu.",
        )
    if problems:
        return check(
            "sources",
            "Dukascopy vs Yahoo",
            "bad" if any("przesunięciu" in x for x in problems) else "warn",
            "Źródła różnią się bardziej niż zwykle.",
            problems + rows,
            "Przesunięcie o godzinę = błąd strefy czasu w jednym źródle (D1); duża mediana = inny feed lub błędne ceny.",
        )
    return check("sources", "Dukascopy vs Yahoo", "ok", "Oba źródła podają te same ceny w tych samych godzinach.", rows)


def frozen(h1: dict) -> dict:
    hits = []
    for p, df in h1.items():
        if df is None or len(df) < FROZEN_HOURS:
            continue
        c = df["close"].to_numpy()
        same = np.concatenate([[False], c[1:] == c[:-1]])
        run_id = np.cumsum(~same)
        lens = np.bincount(run_id)
        for rid in np.flatnonzero(lens >= FROZEN_HOURS)[:3]:
            i = int(np.argmax(run_id == rid))
            hits.append(f"{label(p)}: {lens[rid]} godzin z tym samym zamknięciem od {utc(df['ts'].iloc[i])}")
    if hits:
        return check(
            "frozen",
            "Zamrożone notowania",
            "warn",
            f"{len(hits)} {pl(len(hits), 'okres', 'okresy', 'okresów')}, w których cena stała w miejscu ≥ {FROZEN_HOURS} h.",
            hits,
            "Na żywym rynku to prawie niemożliwe — prawdopodobnie źródło powtarzało starą cenę.",
        )
    return check("frozen", "Zamrożone notowania", "ok", f"Nigdzie cena nie stoi w miejscu ≥ {FROZEN_HOURS} h.")


def bars_valid(h1: dict) -> dict:
    bad = []
    for p, df in h1.items():
        if df is None or df.empty:
            continue
        f = bar_flags(df)
        if f["ohlc"] or f["price"] or f["ts"]:
            bad.append(f"{label(p)}: OHLC {f['ohlc']}, cena ≤ 0 {f['price']}, czas poza pełną godziną {f['ts']}")
    if bad:
        return check(
            "bars_valid",
            "Poprawność świec",
            "bad",
            "Są świece łamiące podstawowe reguły (D5).",
            bad,
            "Zgłoś — to błąd budowy H1 z M1 albo uszkodzony plik.",
        )
    return check("bars_valid", "Poprawność świec", "ok", "Każda świeca: high ≥ max(open, close), low ≤ min, ceny > 0, pełne godziny.")


def coverage_check(cov: dict | None) -> dict:
    src = (cov or {}).get("sources", {}).get("dukascopy")
    if not src:
        return check("coverage", "Kompletność historii", "warn", "Mapy pokrycia jeszcze nie ma.", fix="Pojawi się po ia5 start.")
    months = [m for d in src["pairs"].values() for m in d["m"] if m[0] != EMPTY]
    left = sum(1 for m in months if m[0] == NONE)
    failed = [(p, i) for p, d in src["pairs"].items() for i, m in enumerate(d["m"]) if m[0] == FAILED]
    holes = sum(m[3] or 0 for m in months)
    exp = sum(m[1] or 0 for m in months if m[0] not in (NONE, FAILED))
    share = fmt(100 * holes / exp, 3) if exp else "0"
    text = f"Pobrane {fmt(len(months) - left - len(failed))} z {fmt(len(months))} miesięcy; dziury {fmt(holes)} h ({share}% godzin)."
    if failed:
        return check(
            "coverage",
            "Kompletność historii",
            "bad",
            f"{len(failed)} {pl(len(failed), 'miesiąca', 'miesięcy', 'miesięcy')} nie udało się pobrać. " + text,
            [f"{label(p)}: {month_key(src['start'], i)}" for p, i in failed],
            "ia5 start ponowi je automatycznie; jeśli błąd się powtarza — sprawdź sieć.",
        )
    partial = [(p, i, m[6] if len(m) > 6 else 0) for p, d in src["pairs"].items() for i, m in enumerate(d["m"]) if m[0] == INCOMPLETE]
    if left or partial:
        lead = (f"Brakuje {fmt(left)} miesięcy. " if left else "") + (
            f"{len(partial)} {pl(len(partial), 'miesiąc', 'miesiące', 'miesięcy')} pobrane częściowo "
            f"(brakuje {fmt(sum(x[2] for x in partial))} h sesji). " if partial else "")
        return check("coverage", "Kompletność historii", "warn", lead + text,
                     [f"{label(p)}: {month_key(src['start'], i)} — brakuje {h} h" for p, i, h in partial],
                     "ia5 start dociągnie brakujące dni; pobrane już są zapisane i używane.")
    if exp and holes / exp > 0.001:
        return check("coverage", "Kompletność historii", "warn", text, fix="Szczegóły w mapie pokrycia — „Największe dziury”.")
    return check("coverage", "Kompletność historii", "ok", text)


def publishing(status: dict, publish_error: str | None) -> dict:
    if publish_error:
        return check(
            "publish",
            "Publikacja na GitHub",
            "bad",
            f"Ostatnia publikacja na gałąź data nie powiodła się: {publish_error}",
            fix="Sprawdź, czy git na Macu ma dostęp do repo (git push w ~/.ia5/data-repo).",
        )
    sha = status.get("dataSha")
    if not sha:
        return check(
            "publish",
            "Publikacja na GitHub",
            "warn",
            "Gałąź data nie ma jeszcze świec ani mapy pokrycia.",
            fix="ia5 start opublikuje je po synchronizacji.",
        )
    return check("publish", "Publikacja na GitHub", "ok", f"Gałąź data aktualna (commit {sha[:7]}).")


def strategies(docs: list[dict] | None, beat_state: str | None, now: int) -> dict:
    if docs is None:
        return check("strategies", "Strategie", "ok", "Nie sprawdzono (brak dostępu do listy).")
    errs = [d for d in docs if d.get("status") == "blad"]
    stuck = [d for d in docs if d.get("status") == "liczy_sie" and beat_state != "computing"]
    waiting = [d for d in docs if d.get("status") == "do_policzenia" and now - (d.get("createdAt") or now) > 3600]
    detail = [f"{d.get('name', d['id'])}: błąd — {str(d.get('error', ''))[:120]}" for d in errs]
    detail += [f"{d.get('name', d['id'])}: oznaczona „liczy się”, a Mac nic nie liczy" for d in stuck]
    detail += [f"{d.get('name', d['id'])}: czeka w kolejce ponad godzinę" for d in waiting]
    counts = {}
    for d in docs:
        counts[d.get("status")] = counts.get(d.get("status"), 0) + 1
    text = ", ".join(f"{n} {STATUS_PL.get(s, s)}" for s, n in sorted(counts.items(), key=lambda x: -x[1])) or "Brak strategii."
    if stuck or waiting:
        return check("strategies", "Strategie", "warn", text, detail, "Strategię „utkniętą” wyślij ponownie: karta → Policz ponownie.")
    if errs:
        return check("strategies", "Strategie", "warn", text, detail, "Karta strategii → Popraw kod.")
    return check("strategies", "Strategie", "ok", text)


def disk(path: Path) -> dict:
    try:
        u = shutil.disk_usage(path)
    except OSError:
        return check("disk", "Miejsce na dysku", "warn", "Nie udało się sprawdzić dysku.")
    used = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) if path.exists() else 0
    text = f"Wolne {fmt(u.free / 1e9, 1)} GB; dane IA5 zajmują {fmt(used / 1e9, 2)} GB."
    state = "bad" if u.free < DISK_BAD else "warn" if u.free < DISK_WARN else "ok"
    return check(
        "disk",
        "Miejsce na dysku",
        state,
        text,
        fix=None if state == "ok" else "Zwolnij miejsce — pobieranie Dukascopy potrzebuje kilku GB.",
    )


# ---------- opis stanu bazy i projektu ----------


def facts(status: dict, h1: dict, yahoo: dict, cov: dict | None, docs: list[dict] | None) -> list[str]:
    out = []
    yb = status.get("totalBars") or sum(len(d) for d in yahoo.values() if d is not None)
    yfirst = min((int(d["ts"].min()) for d in yahoo.values() if d is not None and len(d)), default=None)
    ylast = max((v.get("lastTs", 0) for v in (status.get("pairs") or {}).values()), default=0)
    out.append(
        f"Yahoo (monitoring): {fmt(yb)} świec H1 w Firestore, {len(status.get('pairs') or {})} par"
        + (f", od {utc(yfirst)[:10]}" if yfirst else "")
        + (f", ostatnia {utc(ylast)}" if ylast else "")
        + "."
    )
    db = sum(len(d) for d in h1.values() if d is not None)
    if db:
        first = min(int(d["ts"].min()) for d in h1.values() if d is not None and len(d))
        last = max(int(d["ts"].max()) for d in h1.values() if d is not None and len(d))
        out.append(f"Dukascopy (backtesty): {fmt(db)} świec H1 na Macu, {utc(first)[:10]} → {utc(last)[:10]}.")
    else:
        out.append("Dukascopy (backtesty): jeszcze brak danych na Macu.")
    if docs is not None:
        done = sum(1 for d in docs if d.get("status") == "policzona")
        frozen_n = sum(1 for d in docs if d.get("frozenAt"))
        out.append(f"Strategie: {len(docs)} w bazie, {done} policzonych, {frozen_n} zamrożonych (forward test).")
    if status.get("dataSha"):
        out.append(f"Gałąź data: commit {status['dataSha'][:7]}.")
    return out


def run(
    status: dict,
    h1: dict,
    yahoo: dict,
    cov: dict | None,
    until_ts: int,
    docs: list[dict] | None = None,
    beat_state: str | None = None,
    publish_error: str | None = None,
    home: Path | None = None,
    now: int | None = None,
) -> dict:
    now = now or int(time.time())
    checks = [
        yahoo_fresh(status, now),
        apps_script(status, now),
        yahoo_flags(status),
        duka_fresh(h1, until_ts),
        coverage_check(cov),
        bars_valid(h1),
        triangles(h1),
        sources(h1, yahoo),
        frozen(h1),
        publishing(status, publish_error),
        strategies(docs, beat_state, now),
    ]
    if home is not None:
        checks.append(disk(home))
    worst = max((c["state"] for c in checks), key=RANK.get)
    problems = [c for c in checks if c["state"] != "ok"]
    summary = (
        "Wszystko w porządku — każda kontrola przeszła."
        if not problems
        else f"{len(problems)} {pl(len(problems), 'problem', 'problemy', 'problemów')}: "
        + "; ".join(f"{c['name']} — {c['text'].rstrip('.')}" for c in sorted(problems, key=lambda c: -RANK[c["state"]])[:3])
    )
    return {"at": now, "state": worst, "summary": summary, "facts": facts(status, h1, yahoo, cov, docs), "checks": checks}


def report(h: dict) -> str:
    """Opisowy raport do terminala (ia5 health)."""
    mark = {"ok": "✔", "warn": "!", "bad": "✘"}
    lines = [f"Stan systemu IA5 — {utc(h['at'])}", "", h["summary"], ""] + [f"  {f}" for f in h["facts"]] + [""]
    for c in h["checks"]:
        lines.append(f"{mark[c['state']]} {c['name']}: {c['text']}")
        lines += [f"     {d}" for d in c["detail"]]
        if c.get("fix"):
            lines.append(f"     → {c['fix']}")
    return "\n".join(lines)
