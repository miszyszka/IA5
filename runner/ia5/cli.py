"""Komenda `ia5` (CLAUDE.md, sekcja 6)."""
from __future__ import annotations

import argparse
import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import ENGINE_VERSION
from .config import PAIRS
from .store import DATA, HOME, config


def log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def keep_awake():
    """Komputer nie usypia, dopóki działa ia5 (macOS: caffeinate, Windows: SetThreadExecutionState)."""
    if sys.platform == "darwin":
        return subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # CONTINUOUS | SYSTEM_REQUIRED
    return None


def migrate_legacy(log=print) -> bool:
    """D-039 (Michał, 2026-10-31): „usuń wszystkie dane pochodzące z Dukascopy z bazy lokalnej”.

    Usuwa z ~/.ia5 świece M1/H1 Dukascopy, dane do liczenia i skanu zbudowane z nich oraz lokalne wyniki i skany
    policzone na nich. Zwraca True, dopóki nie ma znacznika ~/.ia5/source.json — wtedy ia5 start usuwa też z gałęzi
    `data` wyniki i skany policzone na Dukascopy (historia gita zostaje, G4), wysyła policzone strategie do ponownego
    liczenia na świecach Yahoo i dopiero po udanym przejściu zapisuje znacznik (mark_source). Każdy następny start:
    tylko sprzątanie (nic nie znajdzie).
    """
    import shutil

    from .ready import SOURCE
    from .store import LEGACY, READY, RESULTS, SCANS

    marker = HOME / "source.json"
    try:
        first = json.loads(marker.read_text()).get("source") != SOURCE
    except (FileNotFoundError, ValueError):
        first = True
    targets = list(LEGACY) + ([READY, RESULTS, SCANS] if first else [])
    for d in targets:
        if not d.exists():
            continue
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        shutil.rmtree(d)
        log(f"Usunięto {d} ({size / 1e9:.2f} GB) — dane pochodzące z Dukascopy (D-039)")
    return first


def enforce_local_data(log=print) -> list[str]:
    """D-041 (Michał): lokalnie mają być tylko pary z Yahoo i nic innego. W ~/.ia5/data zostaje wyłącznie
    data/yahoo/{PARA}.parquet (8 par z config), data/yahoo_d1/{PARA}.parquet (świece dzienne Yahoo, D-053)
    i data/h1_ready/ (budowane z H1); wszystko inne jest usuwane
    przy każdym starcie i każdej synchronizacji. Zwraca listę usuniętych ścieżek."""
    import shutil

    from .store import DATA_ALLOWED, YAHOO, YAHOO_D1

    removed = []
    if DATA.exists():
        for f in DATA.iterdir():
            if f.name not in DATA_ALLOWED:
                shutil.rmtree(f) if f.is_dir() else f.unlink()
                removed.append(str(f))
    allowed = {f"{p}.parquet" for p in PAIRS}
    for folder in (YAHOO, YAHOO_D1):   # D-053: obok H1 także świece dzienne Yahoo, tylko 8 par
        if not folder.exists():
            continue
        for f in folder.iterdir():
            if f.name not in allowed:
                shutil.rmtree(f) if f.is_dir() else f.unlink()
                removed.append(str(f))
    for r in removed:
        log(f"Usunięto {r} — lokalnie trzymamy tylko świece Yahoo (D-041)")
    return removed


def mark_source() -> None:
    from .ready import SOURCE

    (HOME / "source.json").write_text(json.dumps({"source": SOURCE, "since": int(time.time())}))


def do_prepare(progress=None) -> dict:
    """Weryfikacja aktualności danych (D-039): kopia świec Yahoo z Firestore → kontrola jakości (D5) → dane do liczenia
    (warstwa czyszczenia, D8) → mapa pokrycia → publikacja na gałąź data. Zwraca kontekst dla przeglądu zdrowia."""
    from . import cloud, coverage, quality, ready
    from .session import H, expected_ts
    from .store import READY, YAHOO

    if progress:
        progress("Kopia świec Yahoo z Firestore", 10)
    enforce_local_data(log)
    log("Stan bazy (Firestore)…")
    try:
        st = cloud.read_status()
    except Exception as e:  # noqa: BLE001
        log(f"  Firestore niedostępny ({e}).")
        st = {}
    log(f"  świece Yahoo w bazie: {st.get('totalBars', 0):,}; ostatnie pobranie Apps Script: "
        f"{'OK' if (st.get('lastRun') or {}).get('ok', True) else 'BŁĄD — ' + str(st['lastRun'].get('error'))}")
    log("Kopia świec Yahoo na Macu…")
    try:
        yahoo = cloud.sync_yahoo(YAHOO, log=lambda m: log(m))
    except Exception as e:  # noqa: BLE001 — bez sieci liczymy na kopii lokalnej; przegląd zdrowia to pokaże
        log(f"  Nie udało się pobrać świec z Firestore ({e}) — używam kopii lokalnej.")
        yahoo = cloud.load_yahoo(YAHOO)
    d1, d1_tz = sync_d1(cloud, st)

    if progress:
        progress("Kontrola danych", 40)
    now = int(time.time())
    exp = expected_ts(now)
    late = [p for p in PAIRS if not len(yahoo.get(p, [])) or int(yahoo[p]["ts"].max()) < exp]
    if late:
        log(f"  Uwaga: brak świecy {time.strftime('%Y-%m-%d %H:%M', time.gmtime(exp))}–{time.strftime('%H:%M', time.gmtime(exp + H))} UTC "
            f"w {len(late)} parach ({', '.join(late)}) — Apps Script jeszcze jej nie zapisał albo Yahoo ma przerwę.")
    else:
        log(f"  Dane aktualne: każda para ma świecę {time.strftime('%Y-%m-%d %H:%M', time.gmtime(exp))} UTC (ostatnia zamknięta w sesji).")
    for pair, df in yahoo.items():
        f = quality.bar_flags(df)
        if f["ohlc"] or f["price"] or f["ts"] or f["gaps"]:
            log(f"  {pair}: luki w sesji {f['gaps']} · złe OHLC {f['ohlc']} · cena ≤ 0 {f['price']} · czas poza pełną godziną {f['ts']}")
    for k, v in quality.cross_check(yahoo).items():
        log(f"  trójkąt {k}: mediana {v['median']:.2f} pips, p99 {v['p99']:.2f} pips ({v['n']:,} świec)")

    if progress:
        progress("Dane do liczenia", 60)
    log("Dane do liczenia (warstwa czyszczenia, D8)…")
    rdy = ready.build(yahoo, READY, log=log)
    if d1:   # D-058: świece dzienne do liczenia (TIMEFRAME = "D1" i tło D1 dla strategii H1)
        from .store import D1_READY

        ready.build_d1(d1, D1_READY, tz=d1_tz, log=log)
    log("Mapa pokrycia…")
    cov = coverage.build(yahoo)
    if progress:
        progress("Publikacja", 80)
    log("Publikacja na gałąź data…")
    publish_error = None
    try:
        from . import publish

        sha = publish.publish_candles(yahoo, source="yahoo", log=lambda m: log(m))
        sha = publish.publish_coverage(cov, log=lambda m: log(m)) or sha
        if d1:
            sha = publish.publish_candles_d1(d1, d1_tz, log=lambda m: log(m)) or sha
        if sha:
            cloud.set_data_sha(sha)
    except Exception as e:  # noqa: BLE001 — brak publikacji nie zatrzymuje programu; zgłasza go przegląd zdrowia
        publish_error = str(e)[:300]
        log(f"  publikacja nie powiodła się: {publish_error}")
    return {"yahoo": yahoo, "cov": cov, "ready": rdy, "publish_error": publish_error, "d1": d1}


def sync_d1(cloud, st: dict) -> tuple[dict, str]:
    """D-053: kopia świec dziennych Yahoo z Firestore + kontrola (D5). Błąd nie zatrzymuje synchronizacji H1."""
    from . import daily, quality
    from .store import YAHOO_D1

    tz = (st.get("d1") or {}).get("tz") or daily.D1_TZ
    log("Kopia świec dziennych (D1) Yahoo…")
    try:
        d1 = cloud.sync_yahoo_d1(YAHOO_D1, st, log=lambda m: log(m))
    except Exception as e:  # noqa: BLE001
        log(f"  Nie udało się pobrać świec D1 z Firestore ({e}) — używam kopii lokalnej.")
        d1 = cloud.load_yahoo_d1(YAHOO_D1)
    if not d1:
        log("  W bazie nie ma jeszcze świec D1 — uruchom raz backfillD1() w Apps Script (docs/SETUP.md).")
        return d1, tz
    for pair, df in d1.items():
        f = daily.d1_flags(df, tz)
        if f["ohlc"] or f["price"] or f["offgrid"] or f["dup_days"]:
            log(f"  D1 {pair}: złe OHLC {f['ohlc']} · cena ≤ 0 {f['price']} · czas nie o północy {f['offgrid']} · "
                f"dwa wpisy na dzień {f['dup_days']}")
    for k, v in quality.cross_check(d1).items():
        log(f"  D1 trójkąt {k}: mediana {v['median']:.2f} pips, p99 {v['p99']:.2f} pips ({v['n']:,} dni)")
    return d1, tz


REPO_ROOT = Path(__file__).resolve().parents[2]   # folder repozytorium IA5, z którego działa program


def _git_repo(*args) -> str:
    r = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, timeout=30)
    return r.stdout.strip() if r.returncode == 0 else ""


STARTED_SHA = None   # commit, którym wystartował ia5 start (kod wczytany do pamięci)


def code_info(fetch: bool = True) -> dict | None:
    """D-046: commit wczytany przy starcie, commit na dysku i ile zmian jest na GitHub (origin/main) ponad niego."""
    try:
        head = _git_repo("rev-parse", "HEAD")
        if not head:
            return None
        behind = None
        if fetch and _git_repo("fetch", "-q", "origin", "main") == "" and _git_repo("rev-parse", "--verify", "-q", "origin/main"):
            n = _git_repo("rev-list", "--count", "HEAD..origin/main")
            behind = int(n) if n.isdigit() else None
        return {"repo": str(REPO_ROOT).replace(str(Path.home()), "~"), "head": head, "loaded": STARTED_SHA, "behind": behind}
    except Exception:  # noqa: BLE001 — brak gita albo sieci nie może zatrzymać przeglądu
        return None


def do_health(ctx: dict, beat_state: str | None = None, write: bool = True) -> dict:
    """Przegląd zdrowia (D-023) na danych z ostatniej synchronizacji i świeżym meta/status."""
    from . import cloud, health

    try:
        docs = cloud.list_strategies()
    except Exception:  # noqa: BLE001
        docs = None
    h = health.run(cloud.read_status(), ctx["yahoo"], ctx["cov"], docs=docs, beat_state=beat_state,
                   publish_error=ctx.get("publish_error"), home=HOME, ready=ctx.get("ready"), code=code_info(),
                   d1=ctx.get("d1"))
    if write:
        cloud.write_health(h)
    bad = [c for c in h["checks"] if c["state"] != "ok"]
    log(f"Przegląd zdrowia: {h['summary'] if bad else 'wszystko w porządku'}")
    return h


def cmd_start(_args) -> int:
    """Jedyny proces (D-039): weryfikacja aktualności danych, potem nasłuch strategii do policzenia.
    Co godzinę (5 min po pełnej godzinie — Apps Script zdąży zapisać świecę) nowa kopia świec i przegląd zdrowia;
    co 6 h ponowne liczenie zamrożonych strategii (forward test, W4)."""
    from . import cloud

    HOME.mkdir(parents=True, exist_ok=True)
    caff = keep_awake()
    stop = threading.Event()
    state = {"now": "syncing"}

    def beat_now():
        cloud.heartbeat(state["now"], state.get("job"))

    def beat():
        while not stop.wait(30):
            try:
                beat_now()
            except Exception as e:  # noqa: BLE001
                log(f"heartbeat: {e}")

    threading.Thread(target=beat, daemon=True).start()

    def bye(*_):
        stop.set()
        try:
            cloud.heartbeat("offline")
        finally:
            if caff:
                caff.terminate()
            log("Zamknięte.")
            os._exit(0)

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)

    global STARTED_SHA
    STARTED_SHA = _git_repo("rev-parse", "HEAD") or None
    sha = STARTED_SHA[:7] if STARTED_SHA else "?"
    log(f"IA5 start · silnik {ENGINE_VERSION} · kod {sha} z {REPO_ROOT} · dane: świece H1 Yahoo (Firestore)")
    first = migrate_legacy(log)
    enforce_local_data(log)

    def sync_progress(name, pct):
        state["job"] = {"id": "sync", "name": name, "progress": pct}

    ctx = do_prepare(progress=sync_progress)
    state["job"] = None
    owner = config().get("owner_uid")
    if first and requeue_after_source_change(owner):
        mark_source()
    safe_health(ctx, "idle")

    jobs: queue.Queue = queue.Queue()
    seen: set = set()

    def on_job(sid, data):
        key = (sid, data.get("status"))
        if key in seen:
            return
        seen.add(key)
        if not owner:
            log(f"Strategia {sid}: pomijam — brak owner_uid w {HOME / 'config.json'} (S1)")
        elif data.get("createdBy") != owner:
            log(f"Strategia {sid}: pomijam — autor nie jest właścicielem (S1)")
        else:
            jobs.put((sid, data))

    cloud.watch_queue(on_job)

    # D-045: wirtualni inwestorzy — przeliczani po każdej zmianie listy i po każdej cogodzinnej kopii świec
    inv_docs: dict = {}
    inv_seen = {"sig": None, "queued": False}

    def queue_investors():
        if not inv_seen["queued"]:
            inv_seen["queued"] = True
            jobs.put((INVESTORS_JOB, None))

    def on_investors(items):
        inv_docs.clear()
        inv_docs.update(dict(items))
        sig = sorted((i, d.get("status")) for i, d in items)
        if sig != inv_seen["sig"]:          # nowy, usunięty albo do usunięcia — liczymy od razu
            inv_seen["sig"] = sig
            queue_investors()

    cloud.watch_investors(on_investors)
    state["now"] = "idle"
    beat_now()
    enqueue_frozen(jobs, owner)
    jobs.put((FOREST_JOB, None))                                   # D-048: las zbuduje się sam przy pierwszym starcie
    log("Połączony. Czekam na strategie (Ctrl+C kończy).")
    next_sync, last_forward = next_sync_time(), time.time()
    while True:
        try:
            sid, data = jobs.get(timeout=30)
        except queue.Empty:
            if time.time() >= next_sync:
                state["now"] = "syncing"
                try:
                    ctx = do_prepare(progress=sync_progress)
                except Exception as e:  # noqa: BLE001 — chwilowy brak sieci nie zatrzymuje nasłuchu
                    log(f"Synchronizacja nieudana: {e} — ponowię za godzinę")
                state["job"] = None
                state["now"] = "idle"
                safe_health(ctx, "idle")
                next_sync = next_sync_time()
                if time.time() - last_forward > FORWARD_SECONDS:  # nowe świece → forward test zamrożonych (W4)
                    enqueue_frozen(jobs, owner)
                    last_forward = time.time()
                queue_investors()                                  # nowe świece → paper trading inwestorów (D-045)
                jobs.put((FOREST_JOB, None))                       # nowe świece → FOREST (D-048)
            continue
        if sid == INVESTORS_JOB:
            inv_seen["queued"] = False
            handle_investors(dict(inv_docs), owner, state)
            continue
        if sid == FOREST_JOB:
            handle_forest(state)
            continue
        if data.get("status") == "do_usuniecia":
            handle_delete(sid)
        else:
            handle_job(sid, data, state)
        seen.discard((sid, data.get("status")))


def next_sync_time(now: float | None = None) -> float:
    """SYNC_OFFSET sekund po najbliższej pełnej godzinie (Apps Script zdąży zapisać nową świecę)."""
    now = time.time() if now is None else now
    t = int(now) // 3600 * 3600 + SYNC_OFFSET
    return t if t > now else t + 3600


def requeue_after_source_change(owner: str | None) -> bool:
    """D-039: wyniki policzone na Dukascopy znikają z gałęzi data, a strategie wracają do kolejki — policzą się
    na świecach Yahoo. Zwraca True po udanym przejściu (wtedy znacznik; inaczej ponowienie przy następnym starcie)."""
    from . import cloud, publish

    if not owner:
        log(f"Przejście na Yahoo: brak owner_uid w {HOME / 'config.json'} (S1) — stare wyniki zostają do następnego startu.")
        return False
    try:
        n = publish.purge_dukascopy_results(log=log)
        log(f"Gałąź data: usunięto {n} wyników i skany policzone na Dukascopy (historia gita zostaje).")
        for sid, data in cloud.computed_strategies():
            if data.get("createdBy") == owner:
                cloud.update_strategy(sid, {"status": "do_policzenia", "result": None, "error": None})
                log(f"Strategia „{data.get('name', sid)}”: do ponownego liczenia na świecach Yahoo")
    except Exception as e:  # noqa: BLE001 — ponowimy przy następnym starcie
        log(f"Przejście na Yahoo nie dokończone ({e}) — ponowię przy następnym starcie.")
        return False
    return True


FORWARD_SECONDS = 6 * 3600   # W4: forward test zamrożonych strategii
INVESTORS_JOB = "__inwestorzy__"
FOREST_JOB = "__forest__"
SYNC_OFFSET = 300            # kopia świec 5 min po pełnej godzinie


def safe_health(ctx: dict, beat_state: str | None) -> None:
    try:
        do_health(ctx, beat_state)
    except Exception as e:  # noqa: BLE001 — przegląd nie może zatrzymać programu
        log(f"Przegląd zdrowia: błąd — {e}")


def enqueue_frozen(jobs: queue.Queue, owner: str | None) -> None:
    """Zamrożone strategie liczone ponownie na nowych danych — karta pokazuje wynik od daty zamrożenia (W4)."""
    from . import cloud

    for sid, data in cloud.frozen_strategies():
        if owner and data.get("createdBy") == owner:
            log(f"Forward test: {data.get('name', sid)}")
            jobs.put((sid, {**data, "status": "forward"}))


PHASES = {"Sygnały": 10, "Silnik": 25, "Walidacja: benchmark": 60, "Walidacja: Deflated": 80, "Gotowe": 90}


def handle_job(sid: str, data: dict, state: dict) -> None:
    from . import cloud, publish
    from .backtest import run_file
    from .sandbox import StrategyError

    name = data.get("name") or sid
    forward = data.get("status") == "forward"   # W4: zamrożona strategia na nowych świecach
    log(f"Strategia „{name}” ({sid}): {'forward test' if forward else 'liczenie'}…")
    state["now"] = "computing"
    state["job"] = {"id": sid, "name": name, "progress": 0, "phase": "start"}
    cloud.update_strategy(sid, {"status": "liczy_sie", "error": None})

    def failed(msg: str) -> None:
        # D-046: nieudany forward test nie zmienia strategii w „błąd” — zostaje policzona (z poprzednim wynikiem)
        # i wraca do forward testu za 6 h; błąd widać w karcie, na liście i w przeglądzie zdrowia
        if forward and data.get("result"):
            cloud.update_strategy(sid, {"status": "policzona", "forwardError": {"at": int(time.time()), "message": msg[:2000]}})
        else:
            cloud.update_strategy(sid, {"status": "blad", "error": msg[:2000]})

    def step(msg):
        log(msg)
        for k, p in PHASES.items():
            if msg.startswith(k):
                state["job"] = {"id": sid, "name": name, "progress": p, "phase": msg[:60]}
                cloud.heartbeat("computing", state["job"])

    try:
        from .store import D1_READY, READY

        fz = data.get("frozenAt")   # D-056: zamrożona → ocena zamrożonego wariantu i blok forward od tej daty
        fv = data.get("frozenVariant")
        out = run_file(data.get("code", ""), name, READY, HOME / "results", log=step, source="yahoo", strategy_id=sid,
                       require_source="yahoo", d1_dir=D1_READY, frozen_at=int(fz) if fz else None,
                       frozen_variant=int(fv) if fz and fv is not None and str(fv).lstrip("-").isdigit() else None)
        sha = publish.publish_result(out, log=log)
        v = json.loads((out / "validation.json").read_text(encoding="utf-8"))
        cloud.update_strategy(sid, {"status": "policzona", "forwardError": None, "forwardAt": int(time.time()) if forward else None,
                                    "result": {"sha": sha, "path": f"results/{sid}",
                                               "run_id": out.name, "verdict": v.get("verdict", {}).get("color")}})
        log(f"Strategia „{name}”: gotowa.")
    except (StrategyError, SystemExit) as e:
        failed(str(e))
        log(f"Strategia „{name}”: błąd — {e}")
    except Exception as e:  # noqa: BLE001 — błąd nie może zatrzymać programu
        failed(f"{type(e).__name__}: {e}")
        log(f"Strategia „{name}”: nieoczekiwany błąd — {e}")
    finally:
        state["now"] = "idle"
        state["job"] = None
        cloud.heartbeat("idle")


CLOUD_FRESH_S = 2 * 3600   # D-052: świeży przebieg GitHub Actions = Mac nie liczy inwestorów


def cloud_active(root, now: int) -> bool:
    try:
        r = json.loads((root / "alerts" / "run.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return r.get("source") == "actions" and now - int(r.get("at", 0)) < CLOUD_FRESH_S


def handle_investors(docs: dict, owner: str | None, state: dict, source: str = "mac") -> None:
    """D-045, D-052: liczy aktywnych inwestorów właściciela (S1), wysyła maile, publikuje stan na gałęzi data i usuwa inwestorów
    do_usuniecia. Normalnie robi to GitHub Actions; Mac przejmuje pracę tylko, gdy Actions nie działało od 2 h.
    Błąd jednego inwestora nie zatrzymuje pozostałych — zostaje jego ostatni opublikowany stan."""
    from . import alerts, cloud, publish
    from .investors import compute
    from .store import D1_READY, DATA_REPO, READY

    if not owner:
        if docs:
            log(f"Inwestorzy: pomijam — brak owner_uid w {HOME / 'config.json'} (S1)")
        return
    beat = cloud.heartbeat if source == "mac" else (lambda *a, **k: None)
    publish.ensure_repo()
    now = int(time.time())
    if source == "mac" and cloud_active(DATA_REPO, now):
        log("Inwestorzy: liczy GitHub Actions — Mac pomija.")
        return
    mine = {i: d for i, d in docs.items() if d.get("createdBy") == owner}
    removed = [i for i, d in mine.items() if d.get("status") == "do_usuniecia"]
    active = {i: d for i, d in mine.items() if d.get("status") == "aktywny"}
    if not active and not removed and not (DATA_REPO / "investors").exists():
        return
    states = {}
    state["now"] = "computing"
    try:
        for n, (iid, d) in enumerate(active.items()):
            state["job"] = {"id": iid, "name": f"Inwestor: {d.get('name', iid)}", "progress": int(100 * n / max(1, len(active))),
                            "phase": "paper trading"}
            beat("computing", state["job"])
            try:
                states[iid] = compute({**d, "id": iid}, READY, log=log, d1_dir=D1_READY)
                e = states[iid]["equity"]
                log(f"Inwestor „{d.get('name')}”: kapitał {e['now']:,.2f} USD ({e['return_pct']:+.2f}%), "
                    f"{states[iid]['counts']['closed']} zamkniętych, {states[iid]['counts']['open']} otwartych")
            except Exception as e:  # noqa: BLE001 — jeden inwestor nie zatrzymuje pozostałych
                log(f"Inwestor „{d.get('name', iid)}”: błąd — {e}")
                prev = DATA_REPO / "investors" / iid / "state.json"
                if prev.exists():
                    states[iid] = json.loads(prev.read_text(encoding="utf-8"))
        ledger = alerts.load_ledger(DATA_REPO / alerts.LEDGER)
        cfg = alerts.load_config(HOME / "smtp.json")
        send = alerts.smtp_sender(cfg) if cfg else None
        for iid, st in states.items():
            err = alerts.process(iid, bool(active[iid].get("emailAlerts")), st, ledger, send)
            st["mail_error"] = err
            if err:
                log(f"Inwestor „{active[iid].get('name', iid)}”: {err}")
        for iid in removed:
            ledger.pop(iid, None)
        extra = {alerts.LEDGER: json.dumps(ledger, ensure_ascii=False), "alerts/run.json": json.dumps({"at": now, "source": source})}
        sha = None
        for attempt in range(3):      # ensure_repo w publikacji zaczyna od świeżej gałęzi, więc ponowienie jest bezpieczne
            try:
                sha = publish.publish_investors(states, removed, log=log, extra=extra)
                break
            except RuntimeError:
                if attempt == 2:
                    raise
                time.sleep(5)
        if sha:
            cloud.set_data_sha(sha)
        for iid in removed:
            cloud.delete_investor(iid)
            log(f"Inwestor {iid}: usunięty")
    except Exception as e:  # noqa: BLE001 — publikacja nie może zatrzymać programu
        log(f"Inwestorzy: błąd publikacji — {e} (ponowię po następnej kopii świec)")
        if source != "mac":
            raise
    finally:
        state["now"] = "idle"
        state["job"] = None
        beat("idle")


def cmd_live(_args) -> None:
    """D-052: jeden przebieg w GitHub Actions. Historia świec z gałęzi data, najnowsze miesiące z Firestore."""
    import pandas as pd

    from . import cloud, publish, ready
    from .store import D1_READY, DATA_REPO, READY, YAHOO, YAHOO_D1

    publish.ensure_repo()
    YAHOO.mkdir(parents=True, exist_ok=True)
    YAHOO_D1.mkdir(parents=True, exist_ok=True)
    for pair in PAIRS:
        files = sorted((DATA_REPO / "candles" / pair).glob("*.parquet"))
        if files:
            pd.concat(pd.read_parquet(f) for f in files).to_parquet(YAHOO / f"{pair}.parquet", index=False)
        fd1 = DATA_REPO / "candles_d1" / f"{pair}.parquet"   # D-058: świece dzienne z gałęzi data (inwestorzy strategii D1)
        if fd1.exists():
            pd.read_parquet(fd1).to_parquet(YAHOO_D1 / f"{pair}.parquet", index=False)
    yahoo = cloud.sync_yahoo(YAHOO, log=log)
    ready.build(yahoo, READY, log=log)
    try:
        st = cloud.read_status()
    except Exception:  # noqa: BLE001
        st = {}
    d1, d1_tz = sync_d1(cloud, st)
    if d1:
        ready.build_d1(d1, D1_READY, tz=d1_tz, log=log)
    handle_investors(cloud.list_investors(), config().get("owner_uid"), {}, source="actions")


def handle_forest(state: dict) -> None:
    """D-048: FOREST działa tylko tu, przy ia5 start. Brak lasu → budowa; jest las → nowe świece po kolei (po przerwie Maca
    nadrabia wszystko, co ominęło) i publikacja na gałąź data. Błąd nie zatrzymuje programu; stan na dysku zostaje poprzedni."""
    from . import cloud, forest_run, publish, ready
    from .store import READY

    job = {"id": "forest", "name": "FOREST", "progress": 0, "phase": "start"}
    state["now"], state["job"] = "computing", job

    def step(msg: str) -> None:
        log(msg)
        job["phase"] = msg.strip()[:60]
        try:
            cloud.heartbeat("computing", job)
        except Exception:  # noqa: BLE001 — chwilowy brak sieci nie przerywa liczenia
            pass

    try:
        frames = ready.load(READY)
        if not forest_run.exists():
            step("FOREST: pierwsza budowa lasu (kilka–kilkanaście minut)…")
            st = forest_run.build(frames, log=step, ledger=HOME)
            made = st["counts"]["decyzje"]
        else:
            st, made = forest_run.step(frames, log=step)
        log(f"FOREST: {made} nowych decyzji · w lesie {st['counts']['las']} · " + " · ".join(
            f"{x['name']} {x['equity']:,.0f} USD" for x in st["books"].values()))
        publish.publish_forest(forest_run.public_dir(), log=log)
    except Exception as e:  # noqa: BLE001 — błąd lasu nie może zatrzymać programu
        log(f"FOREST: błąd — {type(e).__name__}: {e}")
    finally:
        state["now"] = "idle"
        state["job"] = None
        cloud.heartbeat("idle")


def handle_delete(sid: str) -> None:
    from . import cloud, publish

    log(f"Usuwanie strategii {sid}…")
    try:
        publish.delete_result(sid, log=log)
    finally:
        cloud.delete_strategy(sid)


def cmd_health(_args) -> int:
    """Opisowy przegląd zdrowia na kopii lokalnej (bez synchronizacji świec); wynik też na dashboard (Stats)."""
    from . import cloud, coverage, health, ready
    from .store import READY, YAHOO, YAHOO_D1

    yahoo = cloud.load_yahoo(YAHOO)
    if not yahoo:
        print("Na Macu nie ma jeszcze świec — uruchom ia5 start.")
        return 1
    ctx = {"yahoo": yahoo, "cov": coverage.build(yahoo), "ready": ready.build(yahoo, READY, log=log),
           "d1": cloud.load_yahoo_d1(YAHOO_D1)}
    h = do_health(ctx)
    print(health.report(h))
    return 0 if h["state"] != "bad" else 1


def cmd_run(args) -> int:
    """Liczenie strategii z pliku, lokalnie, bez dashboardu."""
    from pathlib import Path

    from .backtest import run_file
    from .sandbox import StrategyError

    path = Path(args.file)
    from .store import D1_READY, READY

    h1_dir = Path(args.h1) if args.h1 else READY
    d1_dir = Path(args.d1) if getattr(args, "d1", None) else D1_READY
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec do liczenia w {h1_dir} — najpierw ia5 start (zrobi kopię świec Yahoo).")
        return 1
    try:
        run_file(path.read_text(encoding="utf-8"), args.name or path.stem, h1_dir, HOME / "results", log=log,
                 require_source=None if args.h1 else "yahoo", d1_dir=d1_dir)
    except StrategyError as e:
        print(f"Błąd strategii: {e}")
        return 1
    return 0


def cmd_check(args) -> int:
    """Kontrola kodu strategii na prawdziwych danych (bez pełnego liczenia)."""
    from pathlib import Path

    from .check import check_code_on, format_result
    from .store import D1_READY, READY

    h1_dir = Path(args.h1) if args.h1 else READY
    d1_dir = Path(args.d1) if getattr(args, "d1", None) else D1_READY
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec do liczenia w {h1_dir} — najpierw ia5 start (zrobi kopię świec Yahoo).")
        return 1
    res = check_code_on(Path(args.file).read_text(encoding="utf-8"), h1_dir, d1_dir=d1_dir)
    print(format_result(res, str(h1_dir)))
    return 0 if res["ok"] else 1


def cmd_scan(args) -> int:
    """Skaner hipotez (D-037): szerokie przeszukanie prostych reguł na danych do liczenia (świece Yahoo po czyszczeniu).
    Ostatnie 25% historii jest pomijane (zostaje na OOS silnika). Wynik: ~/.ia5/scans/{run}/ + gałąź data scans/{run}/."""
    from datetime import UTC, datetime

    from . import cloud, ready, scan
    from .store import READY, SCANS, YAHOO

    pairs = [p.upper() for p in args.pary] if args.pary else list(PAIRS)
    yahoo = cloud.load_yahoo(YAHOO)
    if not yahoo:
        print("Brak świec na Macu — najpierw ia5 start.")
        return 1
    ready.build(yahoo, READY, log=log)
    frames = {p: df for p, df in ready.load(READY, pairs).items() if len(df) > 24 * 120}
    if not frames:
        print("Za mało danych do skanu (potrzeba ≥ ok. 6 miesięcy świec na parę).")
        return 1
    log(f"Skan: {len(frames)} par, siatka {'duża (~160 tys. reguł na parę)' if args.duzy else 'standardowa'}…")
    out = scan.run(frames, big=args.duzy, log=log)
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    dst = scan.save(out, SCANS / run_id)
    print(scan.report(out, top=15))
    log(f"Zapisano: {dst}")
    if not args.lokalnie:
        try:
            from . import publish

            publish.publish_scan(dst, run_id, log=log)
        except Exception as e:  # noqa: BLE001 — skan jest lokalnie, publikacja się nie udała
            log(f"  publikacja nieudana ({e}) — wynik jest lokalnie w {dst}")
    return 0


def cmd_search(args) -> int:
    """Głębokie poszukiwanie (D-044): setki tysięcy – miliony konfiguracji na IS, test zerowy, jeden raz OOS dla
    K wybranych po IS. Wynik: ~/.ia5/searches/{run}/ (+ gałąź data searches/{run}/) i strategy.py do dashboardu."""
    from datetime import UTC, datetime

    from . import cloud, ready, search
    from .store import HOME, READY, SEARCHES, YAHOO

    pairs = [p.upper() for p in args.pary] if args.pary else list(PAIRS)
    yahoo = cloud.load_yahoo(YAHOO)
    if not yahoo:
        print("Brak świec na Macu — najpierw ia5 start.")
        return 1
    ready.build(yahoo, READY, log=log)
    frames = {p: df for p, df in ready.load(READY, pairs).items() if len(df) > 24 * 120}
    if not frames:
        print("Za mało danych (potrzeba ≥ ok. 6 miesięcy świec na parę).")
        return 1
    caffeinate = None
    if sys.platform == "darwin":   # Mac nie może usnąć w trakcie wielogodzinnego liczenia
        caffeinate = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    try:
        out = search.run(frames, size=args.rozmiar, top=args.top, workers=args.procesy, log=log, null=args.zero,
                         open_oos=not args.bez_oos)
    finally:
        if caffeinate:
            caffeinate.terminate()
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    count = search.ledger_add(HOME, run_id, out) if out.get("oos") is not None else None
    dst = search.save(out, SEARCHES / run_id, run_id, count)
    print(search.report(out, count))
    log(f"Zapisano: {dst}" + (" · strategia do dashboardu: strategy.py" if (dst / "strategy.py").exists() else ""))
    if not args.lokalnie:
        try:
            from . import publish

            publish.publish_search(dst, run_id, log=log)
        except Exception as e:  # noqa: BLE001 — wynik jest lokalnie, publikacja się nie udała
            log(f"  publikacja nieudana ({e}) — wynik jest lokalnie w {dst}")
    return 0


def cmd_forest(args) -> int:
    """FOREST (D-048) ręcznie. Normalnie nic z tego nie jest potrzebne: `ia5 start` buduje las sam i liczy go co godzinę.
    Komend `build` i `krok` używaj przy wyłączonym ia5 start, bo oba procesy zapisują ten sam stan."""
    from . import cloud, forest_run, ready
    from .store import READY, YAHOO

    if args.co == "status":
        if not forest_run.exists():
            print("Lasu jeszcze nie ma — zbuduje go ia5 start albo ia5 forest build.")
            return 0
        st = json.loads((forest_run.public_dir() / "state.json").read_text(encoding="utf-8"))
        print(f"Las {st['id']} · dane do {time.strftime('%Y-%m-%d %H:%M', time.gmtime(st['dataTo']))} UTC · "
              f"decyzje {st['counts']['decyzje']:,} · w lesie {st['counts']['las']}")
        for b, x in st["books"].items():
            print(f"  {b.upper()} {x['name']}: {x['equity']:,.2f} USD ({x['return_pct']:+.2f}%), {x['closed']} transakcji")
        for c in st["conclusions"]:
            print(f"  [{c['state']}] {c['text']}")
        return 0
    yahoo = cloud.load_yahoo(YAHOO)
    if not yahoo:
        print("Brak świec na Macu — najpierw ia5 start.")
        return 1
    ready.build(yahoo, READY, log=log)
    frames = ready.load(READY)
    caffeinate = subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())]) if sys.platform == "darwin" else None
    try:
        if args.co == "build":
            st = forest_run.build(frames, zero=args.zero, seed=args.nasiono, log=log, ledger=HOME)
        else:
            if not forest_run.exists():
                print("Lasu jeszcze nie ma — najpierw ia5 forest build.")
                return 1
            st, _ = forest_run.step(frames, log=log)
    finally:
        if caffeinate:
            caffeinate.terminate()
    print((forest_run.public_dir() / "report.md").read_text(encoding="utf-8")[:4000])
    if not args.lokalnie:
        try:
            from . import publish

            publish.publish_forest(forest_run.public_dir(), log=log)
        except Exception as e:  # noqa: BLE001 — wynik jest lokalnie, publikacja się nie udała
            log(f"  publikacja nieudana ({e}) — wynik jest lokalnie w {forest_run.public_dir()}")
    return 0


def cmd_status(_args) -> int:
    print(f"IA5 runner · silnik {ENGINE_VERSION}")
    print("Pary:", ", ".join(PAIRS))
    print("Dane: świece H1 Yahoo (Firestore) → kopia", DATA / "yahoo")
    return 0


def main(argv=None) -> int:
    # gRPC (Firestore) wypisuje szum „FD from fork parent…” przy każdym podprocesie (git, sandbox) — tylko błędy
    os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
    os.environ.setdefault("GLOG_minloglevel", "2")
    parser = argparse.ArgumentParser(prog="ia5")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start", help="weryfikacja danych (świece Yahoo) + nasłuch strategii do policzenia").set_defaults(func=cmd_start)
    p_run = sub.add_parser("run", help="policz strategię z pliku .py lokalnie")
    p_run.add_argument("file")
    p_run.add_argument("--name")
    p_run.add_argument("--h1", help="katalog ze świecami H1 (domyślnie ~/.ia5/data/h1_ready)")
    p_run.add_argument("--d1", help="katalog ze świecami D1 (domyślnie ~/.ia5/data/d1_ready; D-058)")
    p_run.set_defaults(func=cmd_run)
    p_chk = sub.add_parser("check", help="sprawdź kod strategii (kontrakt, look-ahead, sygnały)")
    p_chk.add_argument("file")
    p_chk.add_argument("--h1")
    p_chk.add_argument("--d1")
    p_chk.set_defaults(func=cmd_check)
    p_scan = sub.add_parser("scan", help="skaner hipotez: tysiące–miliony prostych reguł z kontrolą FDR (D-037)")
    p_scan.add_argument("--duzy", action="store_true", help="duża siatka: ~160 tys. reguł na parę (~1,3 mln na 8 par)")
    p_scan.add_argument("--pary", nargs="*", help="np. EURUSD GBPUSD (domyślnie wszystkie)")
    p_scan.add_argument("--lokalnie", action="store_true", help="bez publikacji na gałąź data")
    p_scan.set_defaults(func=cmd_scan)
    p_srch = sub.add_parser("search", help="głębokie poszukiwanie: setki tysięcy konfiguracji na IS, potem OOS (D-045)")
    p_srch.add_argument("--rozmiar", choices=["szybki", "duzy", "gigant"], default="duzy",
                        help="szybki ~7 tys., duzy ~0,7 mln, gigant ~3,1 mln konfiguracji")
    p_srch.add_argument("--top", type=int, default=20, help="ile konfiguracji (wybranych po IS) otworzyć na OOS")
    p_srch.add_argument("--zero", type=int, default=0, help="przebiegi zerowe na danych bez przewagi (każdy = całe poszukiwanie)")
    p_srch.add_argument("--procesy", type=int, help="równoległe procesy (domyślnie liczba rdzeni, max 8)")
    p_srch.add_argument("--pary", nargs="*", help="np. EURUSD GBPUSD (domyślnie wszystkie)")
    p_srch.add_argument("--bez-oos", action="store_true", help="tylko IS — OOS zostaje zamknięty")
    p_srch.add_argument("--lokalnie", action="store_true", help="bez publikacji na gałąź data")
    p_srch.set_defaults(func=cmd_search)
    p_fr = sub.add_parser("forest", help="FOREST: las 1000 inwestorów (D-048); ia5 start liczy go sam, to tylko ręczne sterowanie")
    p_fr.add_argument("co", choices=["build", "krok", "status"],
                      help="build = nowy las (poprzedni do archiwum), krok = nowe świece, status")
    p_fr.add_argument("--zero", type=int, default=1, help="przebiegi na danych bez przewagi")
    p_fr.add_argument("--nasiono", type=int, default=5)
    p_fr.add_argument("--lokalnie", action="store_true", help="bez publikacji na gałąź data")
    p_fr.set_defaults(func=cmd_forest)
    sub.add_parser("live", help="jeden przebieg inwestorów i maili w GitHub Actions (D-052)").set_defaults(func=cmd_live)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("health", help="opisowy przegląd zdrowia danych i projektu").set_defaults(func=cmd_health)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
