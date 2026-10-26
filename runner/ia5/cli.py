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


def do_sync() -> None:
    from . import cloud, dukascopy, publish, quality
    from .bars import m1_to_h1

    log("Stan bazy (Firestore)…")
    st = cloud.read_status()
    log(f"  świece Yahoo w bazie: {st.get('totalBars', 0):,}")

    cloud.heartbeat("syncing")
    log("Dukascopy M1 → lokalnie (pierwszy raz: kilka godzin, potem sekundy)…")
    h1 = {}
    for pair in PAIRS:
        dukascopy.sync_pair(pair, DATA, log=lambda m: log(m))
        h1[pair] = m1_to_h1(dukascopy.load_m1(pair, DATA))
        (DATA / "h1").mkdir(parents=True, exist_ok=True)
        h1[pair].to_parquet(DATA / "h1" / f"{pair}.parquet", index=False)
        f = quality.bar_flags(h1[pair])
        log(f"  {pair} H1: {len(h1[pair]):,} świec · luki {f['gaps']} · OHLC {f['ohlc']} · ts {f['ts']}")
        cloud.heartbeat("syncing")

    log("Yahoo z Firestore…")
    yahoo = cloud.sync_yahoo(DATA / "yahoo", log=lambda m: log(m))

    log("Kontrola: trójkąty (Dukascopy)")
    for k, v in quality.cross_check(h1).items():
        log(f"  {k}: mediana {v['median']:.2f} pips, p99 {v['p99']:.2f} pips ({v['n']:,} świec)")
    log("Kontrola: Dukascopy vs Yahoo (zamknięcia)")
    for pair in PAIRS:
        c = quality.compare_sources(h1[pair], yahoo[pair], pair)
        if c and c.get("n"):
            log(f"  {pair}: mediana {c['median']:.2f} pips, p99 {c['p99']:.2f} pips ({c['n']:,} wspólnych)")

    log("Publikacja świec (Yahoo) na gałąź data…")
    sha = publish.publish_candles(yahoo, source="yahoo", log=lambda m: log(m))
    if sha:
        cloud.set_data_sha(sha)


def cmd_start(_args) -> int:
    from . import cloud

    HOME.mkdir(parents=True, exist_ok=True)
    caff = keep_awake()
    stop = threading.Event()

    def beat():
        while not stop.wait(30):
            try:
                cloud.heartbeat(state["now"], state.get("job"))
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

    log(f"IA5 start · silnik {ENGINE_VERSION}")
    do_sync()

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
    last_sync = time.time()
    while True:
        try:
            sid, data = jobs.get(timeout=60)
        except queue.Empty:
            if time.time() - last_sync > RESYNC_SECONDS:  # nowe świece → forward test zamrożonych (W4)
                state["now"] = "syncing"
                do_sync()
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
        out = run_file(data.get("code", ""), name, DATA / "h1", HOME / "results", m1_dir=DATA / "m1",
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
    from . import cloud

    do_sync()
    cloud.heartbeat("offline")
    return 0


def cmd_run(args) -> int:
    """Liczenie strategii z pliku, lokalnie, bez dashboardu."""
    from pathlib import Path

    from .backtest import run_file
    from .sandbox import StrategyError

    path = Path(args.file)
    h1_dir = Path(args.h1) if args.h1 else DATA / "h1"
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec H1 w {h1_dir} — najpierw `ia5 sync`.")
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

    h1_dir = Path(args.h1) if args.h1 else DATA / "h1"
    if not any(h1_dir.glob("*.parquet")):
        print(f"Brak świec H1 w {h1_dir} — najpierw `ia5 sync`.")
        return 1
    res = check_code_on(Path(args.file).read_text(encoding="utf-8"), h1_dir)
    print(format_result(res, str(h1_dir)))
    return 0 if res["ok"] else 1


def cmd_status(_args) -> int:
    print(f"IA5 runner · silnik {ENGINE_VERSION}")
    print("Pary:", ", ".join(PAIRS))
    print("Katalog danych:", DATA)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ia5")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("start", help="sync + heartbeat + kolejka strategii").set_defaults(func=cmd_start)
    sub.add_parser("sync", help="tylko synchronizacja danych").set_defaults(func=cmd_sync)
    p_run = sub.add_parser("run", help="policz strategię z pliku .py lokalnie")
    p_run.add_argument("file")
    p_run.add_argument("--name")
    p_run.add_argument("--h1", help="katalog ze świecami H1 (domyślnie ~/.ia5/data/h1)")
    p_run.set_defaults(func=cmd_run)
    p_chk = sub.add_parser("check", help="sprawdź kod strategii (kontrakt, look-ahead, sygnały)")
    p_chk.add_argument("file")
    p_chk.add_argument("--h1")
    p_chk.set_defaults(func=cmd_check)
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
