"""Komenda `ia5` (CLAUDE.md, sekcja 6)."""
from __future__ import annotations

import argparse
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

    def on_job(sid, data):
        if not owner:
            log(f"Strategia {sid}: pomijam — brak owner_uid w {HOME / 'config.json'} (S1)")
        elif data.get("createdBy") != owner:
            log(f"Strategia {sid}: pomijam — autor nie jest właścicielem (S1)")
        else:
            jobs.put((sid, data))

    cloud.watch_queue(on_job)
    state["now"] = "idle"
    cloud.heartbeat("idle")
    log("Połączony. Czekam na strategie (Ctrl+C kończy).")
    while True:
        sid, data = jobs.get()
        log(f"Strategia {sid} „{data.get('name')}”: silnik powstaje w etapie E3 — na razie tylko odbiór.")


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
    sub.add_parser("status").set_defaults(func=cmd_status)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
