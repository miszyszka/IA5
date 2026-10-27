"""Pobieracz `ia5 fetch` (D-031) — osobny proces, niezależny od liczenia strategii.

Kolejność: najpierw pary do liczenia (COMPUTE_PAIRS), potem reszta. Para jest pobierana do końca, zanim ruszy następna:
runda 1 szybka (jedna próba na plik), kolejne rundy tempem naprawczym i z rosnącą przerwą, gdy nic nie zeszło.
Dzień odrzucany przez GIVE_UP rund (i starszy niż tydzień) jest uznawany za niedostępny — miesiąc jest wtedy
zatwierdzony, a brakujące godziny backtest zna jako lukę. Gdy para przez NO_PROGRESS rund nie posuwa się
(np. długa blokada serwera), pobieracz przechodzi dalej i wraca do niej w następnym obiegu.
Po każdej rundzie zapisuje świece H1 pary (data/h1/{PARA}.parquet, zapis atomowy) — `ia5 start` je odczyta.
Na gałąź `data` nic nie publikuje (jeden pisarz: `ia5 start`).
"""
from __future__ import annotations

import time
from pathlib import Path

from . import dukascopy
from .bars import m1_to_h1
from .config import COMPUTE_PAIRS, PAIRS

NO_PROGRESS = 8           # rund bez ani jednego nowego dnia → następna para, powrót w kolejnym obiegu
PAUSE = (30, 1800)        # przerwa po rundzie bez postępu: 30 s, podwajana do 30 min
IDLE = 3600               # wszystko pobrane — sprawdzenie nowych dni co godzinę


def order() -> list[str]:
    return list(COMPUTE_PAIRS) + [p for p in PAIRS if p not in COMPUTE_PAIRS]


def build_raw_h1(root: Path, pair: str):
    """Świece H1 ze wszystkiego, co jest na dysku (do mapy pokrycia i kontroli; liczenie bierze tylko zatwierdzone)."""
    h1 = m1_to_h1(dukascopy.load_m1(pair, root))
    (root / "h1").mkdir(parents=True, exist_ok=True)
    path = root / "h1" / f"{pair}.parquet"
    tmp = path.with_suffix(".tmp")
    h1.to_parquet(tmp, index=False)
    tmp.replace(path)
    return h1


def fetch_pair(pair: str, root: Path, log=print, state: dict | None = None, on_month=None, sleep=time.sleep,
               max_rounds: int | None = None, today=None) -> dict:
    """Pobiera parę do końca (albo do NO_PROGRESS rund bez postępu / max_rounds). Zwraca końcowy pair_status."""
    state = state if state is not None else {}
    rnd, idle = 0, 0
    while True:
        st0 = dukascopy.pair_status(root, pair)
        state.update({"state": "pobiera" if rnd == 0 else "naprawia", "pair": pair, "progress": st0["pct"],
                      "round": rnd + 1, "until": None})
        if st0["complete"]:
            log(f"{pair}: komplet — {st0['months']} mies. zatwierdzonych"
                + (f", {st0['given_up']} dni niedostępnych (luki znane backtestowi)" if st0["given_up"] else ""))
            return st0

        def prog(i, n, base=st0["pct"]):
            state["month"] = f"{i}/{n}"

        r = dukascopy.sync_pair(pair, root, log=log, progress=prog, on_month=on_month, gentle=rnd > 0, today=today)
        build_raw_h1(root, pair)
        st = dukascopy.pair_status(root, pair)
        state["progress"] = st["pct"]
        rnd += 1
        if st["complete"]:
            continue  # pętla wypisze „komplet”
        idle = 0 if r["got"] else idle + 1
        log(f"{pair}: runda {rnd} — {st['pct']}% miesięcy zatwierdzonych, zostało {st['missing_days']} dni"
            f" + {st['no_file']} mies. bez pliku; pobrano {r['got']} dni"
            + (f", {r['gave_up']} uznane za niedostępne" if r["gave_up"] else ""))
        if (max_rounds and rnd >= max_rounds) or idle >= NO_PROGRESS:
            if idle >= NO_PROGRESS:
                log(f"{pair}: {idle} rund bez postępu — przechodzę do następnej pary, wrócę w kolejnym obiegu")
            return st
        if idle:
            pause = min(PAUSE[1], PAUSE[0] * 2 ** (idle - 1))
            state.update({"state": "czeka", "until": int(time.time()) + pause})
            log(f"{pair}: przerwa {pause} s przed następną rundą")
            sleep(pause)


def run_forever(root: Path, log=print, state: dict | None = None, live: dict | None = None, sleep=time.sleep,
                once: bool = False) -> dict:
    """Obieg po wszystkich parach w kolejności order(); once=True — jeden obieg (ia5 sync), po 2 rundy na parę."""
    from . import coverage

    state = state if state is not None else {}
    while True:
        until = dukascopy.yesterday()
        start = dukascopy.START
        if live is not None:
            live.update({"start": f"{start.year}-{start.month:02d}",
                         "pairs": {p: coverage.live_states(root, p, until) for p in PAIRS}})
        summary = {}
        for pair in order():
            def on_month(y, m, code, pair=pair):
                if live is None:
                    return
                i = (y - start.year) * 12 + m - start.month
                s = list(live["pairs"][pair])
                if 0 <= i < len(s):
                    s[i] = code
                    live["pairs"][pair] = "".join(s)

            st = fetch_pair(pair, root, log=log, state=state, on_month=on_month, sleep=sleep,
                            max_rounds=2 if once else None)
            summary[pair] = st["pct"]
            state["pairs"] = {**state.get("pairs", {}), pair: st["pct"]}
        if once:
            return summary
        done = all(v >= 100 for v in summary.values())
        state.update({"state": "komplet" if done else "czeka", "pair": None, "until": int(time.time()) + IDLE})
        log("Wszystkie pary pobrane — sprawdzam nowe dni co godzinę." if done
            else "Obieg skończony; pary z brakami dociągnę w następnym obiegu (za godzinę).")
        sleep(IDLE)
