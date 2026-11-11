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


def yahoo_flags(status: dict, yahoo: dict | None = None) -> dict:
    """D-060: zgłoszenia Apps Script sprawdzane na kopii świec — co już naprawione albo obsłużone, nie jest problemem.
    luka@ts: świeca jest już w kopii (Yahoo ją dosłał, samonaprawa ją zapisała) albo Mac ją uzupełnia; revised/ts: korekta
    zapisana / notowanie niezapisane; ohlc/cena: warstwa czyszczenia odrzuca świecę i uzupełnia; trójkąt: kontrola spójności."""
    items = [(p, f) for p, v in (status.get("pairs") or {}).items() for f in (v.get("flags") or [])]
    items += [("trójkąt", f) for f in ((status.get("cross") or {}).get("flags") or [])]
    name = "Jakość danych Yahoo"
    if not items:
        return check("yahoo_flags", name, "ok", "Ostatnie pobrania bez zastrzeżeń.")
    fixed = handled = 0
    detail = []
    for p, f in items:
        kind, _, ts = str(f).partition("@")
        df = (yahoo or {}).get(p)
        present = ts.isdigit() and df is not None and len(df) and bool((df["ts"].to_numpy() == int(ts)).any())
        if kind in ("revised", "ts") or (kind == "luka" and present):
            fixed += 1
        else:
            handled += 1
            what = {"luka": "brak świecy — uzupełniona średnią", "ohlc": "zła świeca — zastąpiona średnią",
                    "cena<=0": "zła cena — zastąpiona średnią"}.get(kind, "sprawdzane w kontroli spójności par")
            detail.append(f"{label(p) if p in PAIRS else p} {utc(int(ts)) if ts.isdigit() else str(f)}: {what}")
    parts = ([f"{fixed} już naprawionych u źródła"] if fixed else []) + ([f"{handled} uzupełnionych automatycznie"] if handled else [])
    return check("yahoo_flags", name, "ok", f"Zgłoszenia Yahoo obsłużone: {', '.join(parts)}.", detail[:20])


def local_data(home: Path, yahoo: dict) -> dict:
    """D-041: lokalnie tylko świece Yahoo (data/yahoo) i dane do liczenia zbudowane z nich (data/h1_ready, źródło yahoo)."""
    import json

    data = home / "data"
    foreign = [f.name for f in data.iterdir() if f.name not in ("yahoo", "h1_ready", "yahoo_d1", "d1_ready")] if data.exists() else []
    for sub in ("yahoo", "yahoo_d1"):   # D-053: obok H1 także kopia świec dziennych Yahoo
        if (data / sub).exists():
            foreign += [f"{sub}/{f.name}" for f in (data / sub).iterdir() if f.suffix != ".parquet" or f.stem not in PAIRS]
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


def daily_candles(status: dict, d1: dict | None, now: int) -> dict:
    """D-053/D-059: świece dzienne Yahoo — czy są dla 8 par, czy są świeże, czy Mac ma kopię zgodną z Firestore, poprawność.
    Yahoo stale (ok. 2% świec, także dziś) podaje high/low niezgodne z open/close — to jego cecha, nie awaria potoku: warstwa
    czyszczenia D1 (D-058) takie świece odrzuca. Dlatego OHLC jest tylko informacją (✓ z liczbą odrzucanych), a ostrzeżeniem
    dopiero duże naruszenie (> 20 pipsów) w ostatnich 30 dniach. Czerwone: cena ≤ 0, czas nie o północy, dwa wpisy na dzień,
    brak pary."""
    from .config import PAIRS as PAIR_CFG
    from .daily import BIG_OHLC_PIPS, D1_TZ, RECENT_DAYS, d1_flags, days_behind, expected_day

    name = "Świece dzienne (D1)"
    st = status.get("d1") or {}
    remote, tz = st.get("pairs") or {}, st.get("tz") or D1_TZ
    if not remote and not d1:
        return check("daily", name, "warn", "W bazie nie ma jeszcze świec dziennych.",
                     fix="W Apps Script wklej nowy Code.gs i uruchom raz backfillD1() (docs/SETUP.md, „Świece dzienne”).")
    exp = expected_day(now, tz)
    state, problems, detail, fixes = "ok", [], [], []
    ohlc_total = 0
    for p in PAIRS:
        df = (d1 or {}).get(p)
        f = d1_flags(df, tz, PAIR_CFG[p].pip)
        r = remote.get(p) or {}
        if not f["bars"]:
            state = "bad"
            problems.append(f"{label(p)}: brak świec D1 na Macu")
            fixes.append("Brak pary: uruchom ia5 start (kopia D1 z Firestore); gdy Firestore jej nie ma — backfillD1() w Apps Script.")
            continue
        behind = days_behind(f["last_day"], exp)
        hard = f["price"] + f["offgrid"] + f["dup_days"]
        ohlc_total += f["ohlc"]
        line = (f"{label(p)}: {f['first_day']} – {f['last_day']}, {fmt(f['bars'])} świec; brakujące dni robocze "
                f"{fmt(f['missing'])}, płaskie {fmt(f['flat'])}, w weekend/święto {fmt(f['weekend'])}; "
                f"złe OHLC {fmt(f['ohlc'])} (największe {f['ohlc_max_pips']:.0f} pips, > {BIG_OHLC_PIPS} pips: {f['ohlc_big']})")
        if hard:
            state = "bad"
            problems.append(f"{label(p)}: cena ≤ 0 {f['price']}, czas nie o północy {f['offgrid']}, dwa wpisy na dzień {f['dup_days']}")
            fixes.append("Błędne wpisy zostają w surowej kopii z flagą (D5), a warstwa czyszczenia D1 je odrzuca. Jeśli to nie "
                         "przemija — zgłoś Claude'owi z listą powyżej.")
        if f["ohlc_big_recent"]:
            state = max(state, "warn", key=RANK.get)
            problems.append(f"{label(p)}: {f['ohlc_big_recent']} świec z ostatnich {RECENT_DAYS} dni ma OHLC złamane o ponad "
                            f"{BIG_OHLC_PIPS} pipsów")
            fixes.append("Yahoo podało świece z high/low daleko od open/close. Warstwa czyszczenia je odrzuca (strategie na D1 "
                         "tego dnia nie widzą), ale jeśli są to ostatnie dni — poczekaj, Yahoo czasem je poprawia (Apps Script "
                         "nadpisuje 4 ostatnie dni).")
        if behind > 1:   # jeden dzień zwłoki: Yahoo publikuje świecę dnia po północy, Apps Script ponawia
            state = max(state, "warn", key=RANK.get)
            problems.append(f"{label(p)}: ostatnia świeca {f['last_day']}, oczekiwana {exp}")
            fixes.append("Zwłoka: Apps Script ponawia co 15 min, ia5 start kopiuje co godzinę; jeśli trwa dłużej niż dzień — sprawdź "
                         "log Apps Script (tickD1_).")
        if r and int(r.get("lastTs") or 0) > int(df["ts"].max()):
            state = max(state, "warn", key=RANK.get)
            problems.append(f"{label(p)}: na Macu starsza kopia niż w Firestore")
            fixes.append("Kopia na Macu jest starsza niż Firestore: poczekaj na najbliższą synchronizację albo uruchom ia5 start ponownie.")
        if r.get("flags"):
            detail.append(f"{label(p)} — flagi Apps Script: {', '.join(map(str, r['flags'][-3:]))}")
        detail.append(line)
    if state == "ok":
        n = sum(len(v) for v in (d1 or {}).values() if v is not None)
        first = min(d1_flags(v, tz)["first_day"] for v in d1.values() if v is not None and len(v))
        note = (f" Yahoo ma w nich {fmt(ohlc_total)} świec ze złym OHLC (ok. {100 * ohlc_total / max(n, 1):.1f}%) — przy liczeniu "
                "są odrzucane (D-058), w surowej kopii zostają (D4).") if ohlc_total else ""
        return check("daily", name, "ok", f"8 par, {fmt(n)} świec dziennych od {first}; ostatni oczekiwany dzień {exp} jest." + note,
                     detail)
    return check("daily", name, state, problems[0] + (f" (i {len(problems) - 1} więcej)" if len(problems) > 1 else "") + ".",
                 problems + detail, " ".join(dict.fromkeys(fixes)))


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
    """D-060: świece łamiące D5 warstwa czyszczenia odrzuca i uzupełnia średnią — to nie awaria, dopóki jest ich mało."""
    bad, n_bad, n_all = [], 0, 0
    for p, df in h1.items():
        if df is None or df.empty:
            continue
        f = bar_flags(df)
        k = f["ohlc"] + f["price"] + f["ts"]
        n_bad += k
        n_all += len(df)
        if k:
            bad.append(f"{label(p)}: {k} {pl(k, 'świeca', 'świece', 'świec')}")
    if not n_bad:
        return check("bars_valid", "Poprawność świec", "ok", "Wszystkie świece poprawne.")
    share = n_bad / max(n_all, 1)
    if share >= 0.01:
        return check("bars_valid", "Poprawność świec", "warn",
                     f"{fmt(n_bad)} błędnych świec Yahoo ({fmt(100 * share, 1)}%) — za dużo, żeby to był przypadek.", bad,
                     "Sprawdź w arkuszu „log” Apps Script, od kiedy; zwykle mija samo po samonaprawie (co 6 h).")
    return check("bars_valid", "Poprawność świec", "ok",
                 f"{fmt(n_bad)} {pl(n_bad, 'błędna świeca', 'błędne świece', 'błędnych świec')} Yahoo zastąpione średnią.", bad)


def coverage_check(cov: dict | None, now: int | None = None) -> dict:
    """D-060: każda dziura jest uzupełniona średnią w danych do liczenia, a samonaprawa Apps Script co 6 h dociąga z Yahoo
    to, co tam się pojawiło. Ostrzeżenie tylko wtedy, gdy mapy pokrycia jeszcze nie ma."""
    src = (cov or {}).get("sources", {}).get("yahoo")
    if not src:
        return check("coverage", "Kompletność historii", "warn", "Mapy pokrycia jeszcze nie ma.", fix="Pojawi się po ia5 start.")
    months = [m for d in src["pairs"].values() for m in d["m"] if m[0] != NONE]
    holes = sum(m[3] or 0 for m in months)
    long_ = sorted(((p, g) for p, d in src["pairs"].items() for g in d["gaps"] if g[3] == "p" and g[2] > 3), key=lambda x: -x[1][0])
    if not holes:
        return check("coverage", "Kompletność historii", "ok", "Historia bez dziur.")
    detail = [f"{label(p)}: {utc(g[0])} → {utc(g[1])} ({g[2]} h)" for p, g in long_[:20]]
    return check("coverage", "Kompletność historii", "ok",
                 f"Komplet: {fmt(holes)} brakujących godzin Yahoo uzupełnionych średnią"
                 + (f" (z tego {len(long_)} {pl(len(long_), 'dłuższa przerwa', 'dłuższe przerwy', 'dłuższych przerw')}"
                    " — backtest nie liczy transakcji przez nie)." if long_ else "."),
                 detail)


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
    fwd = [d for d in docs if d.get("frozenAt") and d.get("forwardError")]   # D-046
    detail += [f"{d.get('name', d['id'])}: forward test nieudany — {str((d.get('forwardError') or {}).get('message', ''))[:120]}"
               for d in fwd]
    counts = {}
    for d in docs:
        counts[d.get("status")] = counts.get(d.get("status"), 0) + 1
    text = ", ".join(f"{n} {STATUS_PL.get(s, s)}" for s, n in sorted(counts.items(), key=lambda x: -x[1])) or "Brak strategii."
    if stuck or waiting:
        return check("strategies", "Strategie", "warn", text, detail, "Strategię „utkniętą” wyślij ponownie: karta → Policz ponownie.")
    if errs or fwd:
        return check("strategies", "Strategie", "warn", text, detail,
                     "Karta strategii → Popraw kod." if errs else "Forward test ponowi się sam za 6 h; gdy błąd wraca — wklej go Claude.")
    return check("strategies", "Strategie", "ok", text)


def code_version(info: dict | None) -> dict:
    """D-046: czy ia5 start liczy aktualnym kodem. info = {repo, loaded, head, behind} (cli.code_info).
    W 2026-10-31 Mac liczył starą wersją przez kilka godzin (git pull w innym folderze) — ta kontrola to pokazuje."""
    name = "Wersja programu na Macu"
    if not info or not info.get("head"):
        return check("code", name, "ok", "Nie sprawdzono (program nie działa z repozytorium git).")
    repo, head, loaded, behind = info.get("repo"), info["head"][:7], (info.get("loaded") or "")[:7], info.get("behind")
    if loaded and loaded != head:
        text = f"Kod w {repo} zmienił się po uruchomieniu ia5 start ({loaded} → {head}) — program liczy starą wersją."
        return check("code", name, "bad", text, fix="W oknie ia5 start: Ctrl+C, potem ponownie ia5 start.")
    if behind:
        word = pl(behind, "nowsza zmiana", "nowsze zmiany", "nowszych zmian")
        return check("code", name, "warn", f"Na GitHub jest {behind} {word} niż kod w {repo} ({head}).",
                     fix=f"cd {repo} && git pull, potem Ctrl+C i ponownie ia5 start.")
    note = "" if behind is not None else " (bez porównania z GitHub — brak sieci)"
    return check("code", name, "ok", f"Aktualny kod {head} z folderu {repo}{note}.")


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
    """D-060: krótko — trzy zdania, bez numerów decyzji."""
    out = []
    ylast = max((v.get("lastTs", 0) for v in (status.get("pairs") or {}).values()), default=0)
    yfirst = min((int(d["ts"].min()) for d in yahoo.values() if d is not None and len(d)), default=None)
    d1first = min(((v.get("firstDay") or "9999") for v in ((status.get("d1") or {}).get("pairs") or {}).values()), default=None)
    line = f"{len(status.get('pairs') or {})} par"
    if yfirst:
        line += f" · godzinowe od {utc(yfirst)[:10]}"
    if d1first and d1first != "9999":
        line += f" · dzienne od {d1first}"
    if ylast:
        line += f" · ostatnia świeca {utc(ylast)}"
    out.append(line)
    if ready:
        filled = sum(r.get("filled", 0) for r in ready.values() if r.get("bars"))
        rejected = sum(r.get("rejected", 0) for r in ready.values() if r.get("bars"))
        if filled or rejected:
            out.append(f"Naprawione automatycznie: {fmt(filled)} brakujących lub błędnych świec uzupełnionych średnią.")
    if docs is not None:
        frozen_n = sum(1 for d in docs if d.get("frozenAt"))
        out.append(f"Strategie: {len(docs)}" + (f", w tym {frozen_n} w forward teście" if frozen_n else "") + ".")
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
    code: dict | None = None,
    d1: dict | None = None,
) -> dict:
    now = now or int(time.time())
    checks = [
        yahoo_fresh(status, now),
        apps_script(status, now),
        yahoo_flags(status, yahoo),
        mac_copy(status, yahoo),
        coverage_check(cov, now),
        bars_valid(yahoo),
        triangles(yahoo),
        frozen(yahoo),
        publishing(status, publish_error),
        strategies(docs, beat_state, now),
    ]
    if d1 is not None:
        checks.append(daily_candles(status, d1, now))
    if code is not None:
        checks.append(code_version(code))
    if home is not None:
        checks.append(local_data(home, yahoo))
        checks.append(disk(home))
    worst = max((c["state"] for c in checks), key=RANK.get)
    problems = [c for c in checks if c["state"] != "ok"]
    summary = (
        "Wszystko działa."
        if not problems
        else "Do zrobienia: "
        + "; ".join(f"{c['name']} — {c['text'].rstrip('.')}" for c in sorted(problems, key=lambda c: -RANK[c["state"]])[:3]) + "."
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
