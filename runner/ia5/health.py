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
from .coverage import NONE, expected_hours, expected_mask
from .quality import bar_flags
from .session import H, expected_ts, is_expected_bar, last_closed_ts, week_open_grace

RANK = {"ok": 0, "warn": 1, "bad": 2}
# Yahoo podaje zamknięcia par z różnych chwil, więc trójkąty „pływają” bardziej niż przy jednym feedzie: na danych
# 2024–2026 mediana EUR/JPY 5 pips, EUR/GBP 2,6 pips; > 25 / 12 pips w 0,02% / 0,1% godzin. Przesunięcie jednej pary
# o godzinę daje ~11% godzin ponad próg — to kontrola ma złapać (D-039).
TRIANGLE_PIPS = {"EURJPY": 25.0, "EURGBP": 12.0}  # odchyłka godziny ponad próg = podejrzana
TRIANGLE_SHARE = 0.005  # > 0,5% podejrzanych godzin → uwaga
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
    late = {p: pairs.get(p, {}).get("lastTs", 0) for p in PAIRS if pairs.get(p, {}).get("lastTs", 0) < exp
            and not week_open_grace(pairs.get(p, {}).get("lastTs", 0), now)}  # Yahoo otwiera tydzień później (D-039)
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
        "Sprawdź arkusz „log” w Apps Script i czy wyzwalacz tick() co 1 min istnieje (installTrigger()).",
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
        "Świece z błędem warstwa czyszczenia odrzuca, luki ≤ 3 h uzupełnia, dłuższe anulują transakcje (D8, B12) — "
        "szczegóły w Stats → mapa pokrycia.",
    )


def local_data(home: Path, yahoo: dict) -> dict:
    """D-041: lokalnie tylko świece Yahoo (data/yahoo) i dane do liczenia zbudowane z nich (data/h1_ready, źródło yahoo)."""
    import json

    data = home / "data"
    foreign = [f.name for f in data.iterdir() if f.name not in ("yahoo", "h1_ready")] if data.exists() else []
    foreign += [f"yahoo/{f.name}" for f in (data / "yahoo").iterdir() if f.stem not in PAIRS] if (data / "yahoo").exists() else []
    ready = data / "h1_ready"
    srcs = {}
    for f in sorted(ready.glob("*.parquet")) if ready.exists() else []:
        try:
            srcs[f.stem] = json.loads(f.with_suffix(".json").read_text()).get("source")
        except (FileNotFoundError, ValueError):
            srcs[f.stem] = None
    bad_src = [f"h1_ready/{p}: źródło {s or 'nieznane'}" for p, s in srcs.items() if s != "yahoo"]
    n = sum(len(df) for df in yahoo.values() if df is not None)
    if foreign or bad_src:
        return check("local_data", "Dane lokalne", "bad", "Na Macu są dane spoza Yahoo.", foreign + bad_src,
                     "ia5 start usuwa je przy każdym starcie i synchronizacji (D-041) — uruchom go ponownie.")
    return check("local_data", "Dane lokalne", "ok",
                 f"Tylko świece Yahoo: {len(yahoo)} par, {fmt(n)} świec; do liczenia {len(srcs)} par (źródło: Yahoo).")


def mac_copy(status: dict, yahoo: dict) -> dict:
    """Kopia świec na Macu (data/yahoo) ma to samo co Firestore — inaczej liczenie idzie na starych danych."""
    pairs = status.get("pairs") or {}
    if not yahoo or all(df is None or df.empty for df in yahoo.values()):
        return check("mac_copy", "Kopia danych na Macu", "bad", "Na Macu nie ma świec Yahoo.",
                     fix="Uruchom ia5 start — pobierze kopię z Firestore.")
    behind = []
    for p in PAIRS:
        df = yahoo.get(p)
        local = int(df["ts"].max()) if df is not None and len(df) else 0
        remote = int((pairs.get(p) or {}).get("lastTs") or 0)
        if remote > local:
            behind.append(f"{label(p)}: na Macu do {utc(local) if local else 'brak'}, w Firestore do {utc(remote)}")
    if behind:
        return check("mac_copy", "Kopia danych na Macu", "warn", f"{len(behind)} par ma na Macu starsze świece niż w Firestore.",
                     behind, "ia5 start synchronizuje co godzinę; nowa świeca mogła dojść po ostatniej synchronizacji.")
    n = sum(len(df) for df in yahoo.values() if df is not None)
    return check("mac_copy", "Kopia danych na Macu", "ok", f"Kopia na Macu zgodna z Firestore ({fmt(n)} świec).")


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
        None if worst_state == "ok"
        else "Otwórz te miesiące w mapie pokrycia; pojedyncze godziny to zwykle przesunięcie znaczników Yahoo między parami.",
    )


def frozen(h1: dict) -> dict:
    """Cena stoi ≥ FROZEN_HOURS godzin sesji (świece poza sesją i w święta pomijamy — Yahoo powtarza w nich starą cenę,
    a warstwa czyszczenia je odrzuca)."""
    hits = []
    for p, df in h1.items():
        if df is None or len(df) < FROZEN_HOURS:
            continue
        df = df[expected_mask(df["ts"].to_numpy())].reset_index(drop=True)
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
            "Warstwa czyszczenia odrzuca te świece przed liczeniem (D8); jeśli jest ich dużo — Yahoo podaje błędne ceny.",
        )
    return check("bars_valid", "Poprawność świec", "ok", "Każda świeca: high ≥ max(open, close), low ≤ min, ceny > 0, pełne godziny.")


def coverage_check(cov: dict | None, now: int | None = None) -> dict:
    """Dziury w świecach Yahoo. Przerwy > 3 h anulują transakcje (B12) — stare są już znane, więc tylko je wypisujemy;
    uwaga, gdy przerwa jest świeża (ostatnie 7 dni), bo wtedy da się ją jeszcze uzupełnić."""
    now = now or int(time.time())
    src = (cov or {}).get("sources", {}).get("yahoo")
    if not src:
        return check("coverage", "Kompletność historii", "warn", "Mapy pokrycia jeszcze nie ma.", fix="Pojawi się po ia5 start.")
    months = [m for d in src["pairs"].values() for m in d["m"] if m[0] != NONE]
    holes = sum(m[3] or 0 for m in months)
    exp = sum(m[1] or 0 for m in months)
    long_ = sorted(((p, g) for p, d in src["pairs"].items() for g in d["gaps"] if g[3] == "p" and g[2] > 3), key=lambda x: -x[1][0])
    share = fmt(100 * holes / exp, 3) if exp else "0"
    text = (f"Dziury {fmt(holes)} h ({share}% godzin sesji); przerw w danych (> 3 h, transakcje na nich anulowane): {len(long_)}.")
    detail = [f"{label(p)}: {utc(g[0])} → {utc(g[1])} ({g[2]} h{', wszystkie pary' if len(g) > 4 and g[4] >= len(src['pairs']) else ''})"
              for p, g in long_]
    fix = ("Uruchom backfill() w Apps Script — pobierze 730 dni Yahoo od nowa i uzupełni dziury, jeśli Yahoo ma już te świece "
           "(ok. 200 zapisów Firestore).")
    fresh = [x for x in long_ if x[1][1] > now - 7 * 86400]
    if fresh:
        return check("coverage", "Kompletność historii", "warn", f"Świeża przerwa w danych ({len(fresh)}). " + text, detail, fix)
    return check("coverage", "Kompletność historii", "ok", text, detail, fix if long_ else None)


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
        fix=None if state == "ok" else "Zwolnij miejsce — liczenie strategii zapisuje wyniki w ~/.ia5/results.",
    )


# ---------- opis stanu bazy i projektu ----------


def facts(status: dict, yahoo: dict, cov: dict | None, docs: list[dict] | None, ready: dict | None = None) -> list[str]:
    out = []
    yb = status.get("totalBars") or sum(len(d) for d in yahoo.values() if d is not None)
    yfirst = min((int(d["ts"].min()) for d in yahoo.values() if d is not None and len(d)), default=None)
    ylast = max((v.get("lastTs", 0) for v in (status.get("pairs") or {}).values()), default=0)
    out.append(
        f"Dane: świece H1 Yahoo — {fmt(yb)} w Firestore, {len(status.get('pairs') or {})} par"
        + (f", od {utc(yfirst)[:10]}" if yfirst else "")
        + (f", ostatnia {utc(ylast)}" if ylast else "")
        + ". Jedyne źródło cen (D-039); historia rośnie o każdą nową godzinę."
    )
    usable = {p: r for p, r in (ready or {}).items() if r.get("bars")}
    if ready is not None:
        tot = lambda k: fmt(sum(r.get(k, 0) for r in usable.values()))  # noqa: E731
        skipped = [label(p) for p, r in ready.items() if not r.get("bars")]
        out.append(
            f"Do liczenia: {len(usable)} par, {tot('bars')} świec; odrzucone (D5) {tot('rejected')}, uzupełnione {tot('filled')} "
            f"(luki ≤ 3 h), przerwy w danych {tot('gaps_n')} ({tot('gap_hours')} h) — transakcje na nich są anulowane."
            + (f" Pominięte (za mało świec): {', '.join(skipped)}." if skipped else "")
        )
    if docs is not None:
        done = sum(1 for d in docs if d.get("status") == "policzona")
        frozen_n = sum(1 for d in docs if d.get("frozenAt"))
        out.append(f"Strategie: {len(docs)} w bazie, {done} policzonych, {frozen_n} zamrożonych (forward test).")
    if status.get("dataSha"):
        out.append(f"Gałąź data: commit {status['dataSha'][:7]}.")
    return out


def run(
    status: dict,
    yahoo: dict,
    cov: dict | None,
    docs: list[dict] | None = None,
    beat_state: str | None = None,
    publish_error: str | None = None,
    home: Path | None = None,
    now: int | None = None,
    ready: dict | None = None,
) -> dict:
    now = now or int(time.time())
    checks = [
        yahoo_fresh(status, now),
        apps_script(status, now),
        yahoo_flags(status),
        mac_copy(status, yahoo),
        coverage_check(cov, now),
        bars_valid(yahoo),
        triangles(yahoo),
        frozen(yahoo),
        publishing(status, publish_error),
        strategies(docs, beat_state, now),
    ]
    if home is not None:
        checks.append(local_data(home, yahoo))
        checks.append(disk(home))
    worst = max((c["state"] for c in checks), key=RANK.get)
    problems = [c for c in checks if c["state"] != "ok"]
    summary = (
        "Wszystko w porządku — każda kontrola przeszła."
        if not problems
        else f"{len(problems)} {pl(len(problems), 'problem', 'problemy', 'problemów')}: "
        + "; ".join(f"{c['name']} — {c['text'].rstrip('.')}" for c in sorted(problems, key=lambda c: -RANK[c["state"]])[:3])
    )
    return {"at": now, "state": worst, "summary": summary, "facts": facts(status, yahoo, cov, docs, ready), "checks": checks}


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
