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
    data/yahoo/{PARA}.parquet (8 par z config) i data/h1_ready/ (budowane z nich); wszystko inne jest usuwane
    przy każdym starcie i każdej synchronizacji. Zwraca listę usuniętych ścieżek."""
    import shutil

    from .store import DATA_ALLOWED, YAHOO

    removed = []
    if DATA.exists():
        for f in DATA.iterdir():
            if f.name not in DATA_ALLOWED:
                shutil.rmtree(f) if f.is_dir() else f.unlink()
                removed.append(str(f))
    if YAHOO.exists():
        allowed = {f"{p}.parquet" for p in PAIRS}
        for f in YAHOO.iterdir():
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
        if sha:
            cloud.set_data_sha(sha)
    except Exception as e:  # noqa: BLE001 — brak publikacji nie zatrzymuje programu; zgłasza go przegląd zdrowia
        publish_error = str(e)[:300]
        log(f"  publikacja nie powiodła się: {publish_error}")
    return {"yahoo": yahoo, "cov": cov, "ready": rdy, "publish_error": publish_error}


def do_health(ctx: dict, beat_state: str | None = None, write: bool = True) -> dict:
    """Przegląd zdrowia (D-023) na danych z ostatniej synchronizacji i świeżym meta/status."""
    from . import cloud, health

    try:
        docs = cloud.list_strategies()
    except Exception:  # noqa: BLE001
        docs = None
    h = health.run(cloud.read_status(), ctx["yahoo"], ctx["cov"], docs=docs, beat_state=beat_state,
                   publish_error=ctx.get("publish_error"), home=HOME, ready=ctx.get("ready"))
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

    log(f"IA5 start · silnik {ENGINE_VERSION} · dane: świece H1 Yahoo (Firestore)")
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
    state["now"] = "idle"
    beat_now()
    enqueue_frozen(jobs, owner)
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
    log(f"Strategia „{name}” ({sid}): liczenie…")
    state["now"] = "computing"
    state["job"] = {"id": sid, "name": name, "progress": 0, "phase": "start"}
    cloud.update_strategy(sid, {"status": "liczy_sie", "error": None})

    def step(msg):
        log(msg)
        for k, p in PHASES.items():
            if msg.startswith(k):
                state["job"] = {"id": sid, "name": name, "progress": p, "phase": msg[:60]}
                cloud.heartbeat("computing", state["job"])

    try:
        from .store import READY

        out = run_file(data.get("code", ""), name, READY, HOME / "results", log=step, source="yahoo", strategy_id=sid,
                       require_source="yahoo")
        sha = publish.publish_result(out, log=log)
        v = json.loads((out / "validation.json").read_text(encoding="utf-8"))
        cloud.update_strategy(sid, {"status": "policzona", "result": {"sha": sha, "path": f"results/{sid}",
                                    "run_id": out.name, "verdict": v.get("verdict", {}).get("color")}})
        log(f"Strategia „{name}”: gotowa.")
    except (StrategyError, SystemExit) as e:
        cloud.update_strategy(sid, {"status": "blad", "error": str(e)[:2000]})
        log(f"Strategia „{name}”: błąd — {e}")
    except Exception as e:  # noqa: BLE001 — błąd nie może zatrzymać programu
        cloud.update_strategy(sid, {"status": "blad", "error": f"{type(e).__name__}: {e}"[:2000]})
        log(f"Strategia „{name}”: nieoczekiwany błąd — {e}")
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
    from .store import READY, YAHOO

    yahoo = cloud.load_yahoo(YAHOO)
    if not yahoo:
        print("Na Macu nie ma jeszcze świec — uruchom ia5 start.")
        return 1
    ctx = {"yahoo": yahoo, "cov": coverage.build(yahoo), "ready": ready.build(yahoo, READY, log=log)}
    h = do_health(ctx)
    print(health.report(h))
    return 0 if h["state"] != "bad" else 1


def cmd_run(args) -> int:
    """Liczenie strategii z pliku, lokalnie, bez dashboardu."""
    from pathlib import Path

    from .backtest import run_file
    from .sandbox import StrategyError

    path = Path(args.file)
    from .store import READY

    h1_dir = Path(args.h1) if args.h1 else READY
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec do liczenia w {h1_dir} — najpierw ia5 start (zrobi kopię świec Yahoo).")
        return 1
    try:
        run_file(path.read_text(encoding="utf-8"), args.name or path.stem, h1_dir, HOME / "results", log=log,
                 require_source=None if args.h1 else "yahoo")
    except StrategyError as e:
        print(f"Błąd strategii: {e}")
        return 1
    return 0


def cmd_check(args) -> int:
    """Kontrola kodu strategii na prawdziwych danych (bez pełnego liczenia)."""
    from pathlib import Path

    from .check import check_code_on, format_result
    from .store import READY

    h1_dir = Path(args.h1) if args.h1 else READY
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec do liczenia w {h1_dir} — najpierw ia5 start (zrobi kopię świec Yahoo).")
        return 1
    res = check_code_on(Path(args.file).read_text(encoding="utf-8"), h1_dir)
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
    p_run.set_defaults(func=cmd_run)
    p_chk = sub.add_parser("check", help="sprawdź kod strategii (kontrakt, look-ahead, sygnały)")
    p_chk.add_argument("file")
    p_chk.add_argument("--h1")
    p_chk.set_defaults(func=cmd_check)
    p_scan = sub.add_parser("scan", help="skaner hipotez: tysiące–miliony prostych reguł z kontrolą FDR (D-037)")
    p_scan.add_argument("--duzy", action="store_true", help="duża siatka: ~160 tys. reguł na parę (~1,3 mln na 8 par)")
    p_scan.add_argument("--pary", nargs="*", help="np. EURUSD GBPUSD (domyślnie wszystkie)")
    p_scan.add_argument("--lokalnie", action="store_true", help="bez publikacji na gałąź data")
    p_scan.set_defaults(func=cmd_scan)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("health", help="opisowy przegląd zdrowia danych i projektu").set_defaults(func=cmd_health)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
