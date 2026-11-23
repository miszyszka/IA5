"""D-072 — dziennik otwarć OOS dla strategii (ten sam plik co poszukiwanie, REV i Stocks: ~/.ia5/oos_ledger.json).

Luka, którą to zamyka: każde „Policz ponownie / popraw” po obejrzeniu OOS i każda nowa strategia patrzą na ten sam
ostatni kawałek historii. Po kilkunastu poprawkach OOS przestaje być czysty — dopasowujemy się do niego ręcznie.
Dziennik nic nie blokuje; liczy i pokazuje w raporcie i na karcie:
  - ile różnych wersji kodu tej strategii widziało OOS,
  - ile różnych wersji kodu (wszystkich strategii, plus kandydatów eksploracji) widziało ten sam okres OOS.
Przeliczenie tego samego kodu (forward test co 6 h) nie jest nowym otwarciem.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

LEDGER_NAME = "oos_ledger.json"
OVERLAP = 0.5   # „ten sam okres OOS” = okna nakładają się co najmniej w połowie krótszego


def _read(f: Path) -> list:
    try:
        rows = json.loads(f.read_text())
        return rows if isinstance(rows, list) else []
    except (FileNotFoundError, ValueError):
        return []


def _overlap(a0, a1, b0, b1) -> bool:
    inter = min(a1, b1) - max(a0, b0)
    short = max(1, min(a1 - a0, b1 - b0))
    return inter / short >= OVERLAP


def add(home: Path, sid: str, code_hash: str, timeframe: str, oos_from: int, oos_to: int, kind: str = "strategy",
        opened: int = 1, name: str | None = None) -> dict:
    """Dopisuje otwarcie (jeśli ten kod tej strategii jeszcze nie widział OOS) i zwraca liczniki."""
    f = Path(home) / LEDGER_NAME
    rows = _read(f)
    mine = [r for r in rows if r.get("kind") in ("strategy", "explore") and r.get("sid") == sid]
    known = any(r.get("code_hash") == code_hash and r.get("kind") == kind for r in mine)
    if not known:
        rows.append({"kind": kind, "sid": sid, "name": name, "code_hash": code_hash, "timeframe": timeframe, "at": int(time.time()),
                     "oos_from": int(oos_from), "oos_to": int(oos_to), "opened": int(opened)})
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(rows, indent=1))
    return counts(rows, sid, timeframe, oos_from, oos_to)


def counts(rows: list, sid: str, timeframe: str, oos_from: int, oos_to: int) -> dict:
    same = [r for r in rows if r.get("kind") in ("strategy", "explore") and r.get("timeframe") == timeframe
            and "oos_from" in r and _overlap(oos_from, oos_to, r["oos_from"], r["oos_to"])]
    versions = {r.get("code_hash") for r in rows if r.get("kind") == "strategy" and r.get("sid") == sid}
    return {"strategy_versions": len(versions),
            "window_codes": len({(r.get("sid"), r.get("code_hash")) for r in same if r.get("kind") == "strategy"}),
            "window_explore": int(sum(int(r.get("opened", 0)) for r in same if r.get("kind") == "explore"))}


def line(c: dict | None) -> str:
    if not c:
        return ""
    s = (f"OOS tego okresu widziało już {c['window_codes']} wersji kodu strategii"
         + (f" i {c['window_explore']} kandydatów eksploracji" if c.get("window_explore") else "")
         + f"; ta strategia: {c['strategy_versions']} wersji.")
    if c["window_codes"] + c.get("window_explore", 0) > 20:
        s += " To dużo — OOS traci czystość; prawdziwym testem jest forward od zamrożenia (W4)."
    return s
