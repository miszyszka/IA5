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


def load_frames(folder) -> dict:
    import pandas as pd

    out = {}
    for p in PAIRS:
        f = folder / f"{p}.parquet"
        out[p] = pd.read_parquet(f) if f.exists() else pd.DataFrame(columns=["ts", "open", "high", "low", "close", "minutes"])
    return out


def raw_signature() -> str:
    """Podpis surowych H1 (pisze je `ia5 fetch`) — zmiana = nowe dane do przeliczenia mapy, kontroli i forward testu."""
    parts = []
    for f in sorted((DATA / "h1").glob("*.parquet")):
        st = f.stat()
        parts.append(f"{f.name}:{st.st_size}:{st.st_mtime_ns}")
    return "|".join(parts)


def do_prepare(progress=None) -> dict:
    """`ia5 start` bez pobierania (D-031): świece do liczenia z zatwierdzonych miesięcy, Yahoo, kontrole, mapa, publikacja.
    Dukascopy pobiera osobny proces `ia5 fetch`; tutaj tylko czytamy to, co już jest na dysku."""
    from datetime import UTC, datetime, timedelta

    from . import cloud, coverage, quality, ready
    from .config import COMPUTE_PAIRS
    from .store import READY

    log("Stan bazy (Firestore)…")
    st = cloud.read_status()
    log(f"  świece Yahoo w bazie: {st.get('totalBars', 0):,}")
    until = datetime.now(UTC).date() - timedelta(days=1)
    if progress:
        progress("Przygotowanie danych do liczenia", 10)
    log(f"Dane do liczenia (tylko zatwierdzone miesiące, D-031): {', '.join(COMPUTE_PAIRS)}…")
    rdy = ready.build(DATA, READY, until=until, log=log)
    h1 = load_frames(DATA / "h1")
    for pair, df in h1.items():
        if len(df):
            f = quality.bar_flags(df)
            log(f"  {pair} H1 (wszystko na dysku): {len(df):,} świec · luki {f['gaps']} · OHLC {f['ohlc']} · ts {f['ts']}")
        else:
            log(f"  {pair} H1: jeszcze brak — pobierze `ia5 fetch`")
    if progress:
        progress("Kontrola danych", 50)
    log("Yahoo z Firestore…")
    yahoo = cloud.sync_yahoo(DATA / "yahoo", log=lambda m: log(m))
    full = {p: df for p, df in h1.items() if len(df)}
    log("Kontrola: trójkąty (Dukascopy)")
    for k, v in quality.cross_check(full).items():
        log(f"  {k}: mediana {v['median']:.2f} pips, p99 {v['p99']:.2f} pips ({v['n']:,} świec)")
    log("Kontrola: Dukascopy vs Yahoo (zamknięcia)")
    for pair in full:
        c = quality.compare_sources(full[pair], yahoo[pair], pair)
        if c and c.get("n"):
            log(f"  {pair}: mediana {c['median']:.2f} pips, p99 {c['p99']:.2f} pips ({c['n']:,} wspólnych)")
    log("Mapa pokrycia (luki wobec kalendarza sesji)…")
    cov = coverage.build(DATA, h1, yahoo, until=until)
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
    until_ts = int(datetime(until.year, until.month, until.day, tzinfo=UTC).timestamp()) + 86400
    return {"h1": h1, "yahoo": yahoo, "cov": cov, "until_ts": until_ts, "publish_error": publish_error,
            "ready": rdy, "raw_sig": raw_signature()}


def cmd_fetch(_args) -> int:
    """Pobieracz Dukascopy (D-031): osobny terminal, działa bez końca; para po parze do końca, potem nowe dni co godzinę."""
    from . import cloud, fetch

    HOME.mkdir(parents=True, exist_ok=True)
    caff = keep_awake()
    stop = threading.Event()
    state: dict = {"state": "pobiera"}
    live: dict = {}

    def beat_now():
        cloud.fetch_heartbeat({k: v for k, v in {**state, "sync": live or None}.items() if v is not None})

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
            cloud.fetch_heartbeat(None)
        finally:
            if caff:
                caff.terminate()
            log("Pobieranie zatrzymane.")
            os._exit(0)

    signal.signal(signal.SIGINT, bye)
    signal.signal(signal.SIGTERM, bye)
    log(f"IA5 fetch · kolejność: {', '.join(fetch.order())} · każda para do końca, zanim ruszy następna")
    fetch.run_forever(DATA, log=log, state=state, live=live)
    return 0


def do_health(ctx: dict, beat_state: str | None = None, write: bool = True) -> dict:
    """Przegląd zdrowia (D-023) na danych z ostatniej synchronizacji i świeżym meta/status."""
    from . import cloud, health

    try:
        docs = cloud.list_strategies()
    except Exception:  # noqa: BLE001
        docs = None
    h = health.run(cloud.read_status(), ctx["h1"], ctx["yahoo"], ctx["cov"], ctx["until_ts"], docs=docs,
                   beat_state=beat_state, publish_error=ctx.get("publish_error"), home=HOME,
                   ready=ctx.get("ready"))
    if write:
        cloud.write_health(h)
    bad = [c for c in h["checks"] if c["state"] != "ok"]
    log(f"Przegląd zdrowia: {h['summary'] if bad else 'wszystko w porządku'}")
    return h


def cmd_start(_args) -> int:
    from . import cloud

    HOME.mkdir(parents=True, exist_ok=True)
    caff = keep_awake()
    stop = threading.Event()

    def beat_now():
        cloud.heartbeat(state["now"], state.get("job"), state.get("sync"))

    def beat():
        while not stop.wait(30):
            try:
                beat_now()
            except Exception as e:  # noqa: BLE001
                log(f"heartbeat: {e}")

    state = {"now": "syncing"}
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

    log(f"IA5 start · silnik {ENGINE_VERSION} · liczenie na danych już pobranych (pobieranie: `ia5 fetch` w osobnym terminalu)")

    def sync_progress(name, pct):
        state["job"] = {"id": "sync", "name": name, "progress": pct}

    ctx = do_prepare(progress=sync_progress)
    state["job"] = None
    safe_health(ctx, "idle")

    owner = config().get("owner_uid")
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
    cloud.heartbeat("idle")
    enqueue_frozen(jobs, owner)
    log("Połączony. Czekam na strategie (Ctrl+C kończy).")
    last_sync = last_health = last_check = time.time()
    while True:
        try:
            sid, data = jobs.get(timeout=60)
        except queue.Empty:
            if time.time() - last_health > HEALTH_SECONDS:
                safe_health(ctx, state["now"])
                last_health = time.time()
            # nowe dane od `ia5 fetch` (co 30 min) albo co 6 h (Yahoo) → przygotowanie, mapa, forward test zamrożonych (W4)
            due = time.time() - last_sync > RESYNC_SECONDS
            if not due and time.time() - last_check > CHECK_SECONDS:
                last_check = time.time()
                due = raw_signature() != ctx.get("raw_sig")
            if due:
                state["now"] = "syncing"
                ctx = do_prepare(progress=sync_progress)
                state["job"] = None
                safe_health(ctx, "idle")
                last_health = time.time()
                last_sync = time.time()
                state["now"] = "idle"
                enqueue_frozen(jobs, owner)
            continue
        state["queue"] = jobs.qsize()
        if data.get("status") == "do_usuniecia":
            handle_delete(sid)
        else:
            handle_job(sid, data, state)
        seen.discard((sid, data.get("status")))


RESYNC_SECONDS = 6 * 3600
CHECK_SECONDS = 1800   # co tyle sprawdzamy, czy `ia5 fetch` dopisał dane
HEALTH_SECONDS = 3600


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

        out = run_file(data.get("code", ""), name, READY, HOME / "results", m1_dir=DATA / "m1",
                       log=step, source="dukascopy", strategy_id=sid)
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


def cmd_sync(_args) -> int:
    """Jednorazowo: jeden obieg pobierania (po 2 rundy na parę), potem przygotowanie danych i przegląd zdrowia."""
    from . import cloud, fetch

    fetch.run_forever(DATA, log=log, once=True)
    safe_health(do_prepare(), None)
    cloud.heartbeat("offline")
    return 0


def cmd_health(_args) -> int:
    """Opisowy przegląd zdrowia na danych lokalnych, bez pobierania; wynik też na dashboard (Stats)."""
    from datetime import UTC, datetime, timedelta

    import pandas as pd

    from . import coverage, health

    load = lambda d: {p: pd.read_parquet(d / f"{p}.parquet") for p in PAIRS if (d / f"{p}.parquet").exists()}  # noqa: E731
    from . import ready
    from .store import READY

    rdy = ready.build(DATA, READY, log=log)
    h1, yahoo = load(DATA / "h1"), load(DATA / "yahoo")
    until = datetime.now(UTC).date() - timedelta(days=1)
    ctx = {"h1": h1, "yahoo": yahoo, "cov": coverage.build(DATA, h1, yahoo, until=until) if h1 else None,
           "until_ts": int(datetime(until.year, until.month, until.day, tzinfo=UTC).timestamp()) + 86400, "ready": rdy}
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
        print(f"Brak świec do liczenia w {h1_dir} — najpierw `ia5 fetch` (pobieranie), potem `ia5 start` albo `ia5 health`.")
        return 1
    try:
        run_file(path.read_text(encoding="utf-8"), args.name or path.stem, h1_dir, HOME / "results",
                 m1_dir=DATA / "m1", log=log)
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
        print(f"Brak świec do liczenia w {h1_dir} — najpierw `ia5 fetch`, potem `ia5 start`.")
        return 1
    res = check_code_on(Path(args.file).read_text(encoding="utf-8"), h1_dir)
    print(format_result(res, str(h1_dir)))
    return 0 if res["ok"] else 1


def cmd_scan(args) -> int:
    """Skaner hipotez (D-037): szerokie przeszukanie prostych reguł na wszystkich parach z zatwierdzonymi miesiącami.
    Ostatnie 25% historii jest pomijane (zostaje na OOS silnika). Wynik: ~/.ia5/scans/{run}/ + gałąź data scans/{run}/."""
    from datetime import UTC, datetime, timedelta

    import pandas as pd

    from . import ready, scan

    until = datetime.now(UTC).date() - timedelta(days=1)
    pairs = [p.upper() for p in args.pary] if args.pary else list(PAIRS)
    folder = DATA / "h1_scan"
    log(f"Dane do skanu (tylko zatwierdzone miesiące): {', '.join(pairs)}…")
    ready.build(DATA, folder, pairs=pairs, until=until, log=log)
    frames = {f.stem: pd.read_parquet(f) for f in sorted(folder.glob("*.parquet"))}
    frames = {p: df for p, df in frames.items() if len(df) > 24 * 365}
    if not frames:
        print("Brak danych do skanu — najpierw `ia5 fetch`.")
        return 1
    log(f"Skan: {len(frames)} par, siatka {'duża (~160 tys. reguł na parę)' if args.duzy else 'standardowa'}…")
    out = scan.run(frames, big=args.duzy, log=log)
    run_id = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    dst = scan.save(out, HOME / "scans" / run_id)
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
    print("Katalog danych:", DATA)
    return 0


def main(argv=None) -> int:
    # gRPC (Firestore) wypisuje szum „FD from fork parent…” przy każdym podprocesie (git, sandbox) — tylko błędy
    os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
    os.environ.setdefault("GLOG_minloglevel", "2")
    parser = argparse.ArgumentParser(prog="ia5")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start", help="liczenie strategii na pobranych danych + heartbeat + kolejka").set_defaults(func=cmd_start)
    sub.add_parser("fetch", help="pobieranie Dukascopy, para po parze do końca (osobny terminal)").set_defaults(func=cmd_fetch)
    sub.add_parser("sync", help="jeden obieg pobierania + przygotowanie danych").set_defaults(func=cmd_sync)
    p_run = sub.add_parser("run", help="policz strategię z pliku .py lokalnie")
    p_run.add_argument("file")
    p_run.add_argument("--name")
    p_run.add_argument("--h1", help="katalog ze świecami H1 (domyślnie ~/.ia5/data/h1)")
    p_run.set_defaults(func=cmd_run)
    p_chk = sub.add_parser("check", help="sprawdź kod strategii (kontrakt, look-ahead, sygnały)")
    p_chk.add_argument("file")
    p_chk.add_argument("--h1")
    p_chk.set_defaults(func=cmd_check)
    p_scan = sub.add_parser("scan", help="skaner hipotez: tysiące–miliony prostych reguł z kontrolą FDR (D-037)")
    p_scan.add_argument("--duzy", action="store_true", help="duża siatka: ~160 tys. reguł na parę (~1,3 mln na 8 par)")
    p_scan.add_argument("--pary", nargs="*", help="np. EURUSD GBPUSD (domyślnie wszystkie z zatwierdzonymi miesiącami)")
    p_scan.add_argument("--lokalnie", action="store_true", help="bez publikacji na gałąź data")
    p_scan.set_defaults(func=cmd_scan)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("health", help="opisowy przegląd zdrowia danych i projektu").set_defaults(func=cmd_health)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
