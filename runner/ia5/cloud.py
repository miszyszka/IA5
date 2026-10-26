"""Firestore z Maca (firebase-admin, service account — uprawnienia administracyjne).

Budżet (Z4): heartbeat co 30 s ≈ 2 880 zapisów/dobę gdy program działa; sync Yahoo: ok. 200 odczytów
za pierwszym razem, potem 16 (bieżący i poprzedni miesiąc × 8 par) na każde `ia5 start`.
"""
from __future__ import annotations

import socket
from datetime import datetime, timezone

import pandas as pd

from . import ENGINE_VERSION
from .config import PAIRS
from .store import SERVICE_ACCOUNT

_db = None


def db():
    global _db
    if _db is None:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not SERVICE_ACCOUNT.exists():
            raise SystemExit(f"Brak klucza: {SERVICE_ACCOUNT} (docs/SETUP.md, krok 4)")
        app = firebase_admin.initialize_app(credentials.Certificate(str(SERVICE_ACCOUNT)))
        _db = firestore.client(app)
    return _db


def read_status() -> dict:
    snap = db().collection("meta").document("status").get()
    return snap.to_dict() or {}


def _bars_to_df(docs) -> pd.DataFrame:
    rows = []
    for d in docs:
        for ts, (o, h, lo, c) in (d.get("bars") or {}).items():
            rows.append((int(ts), o, h, lo, c))
    return pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close"])


def yahoo_docs(pair: str, months: list[str] | None):
    col = db().collection("candles")
    if months is None:
        return [s.to_dict() for s in col.where("pair", "==", pair).stream()]
    snaps = [col.document(f"{pair}_{m}").get() for m in months]
    return [s.to_dict() for s in snaps if s.exists]


def sync_yahoo(folder, log=print) -> dict[str, pd.DataFrame]:
    """Kopia świec Yahoo z Firestore do folder/{PARA}.parquet. Pełny odczyt tylko za pierwszym razem."""
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    prev = (now.replace(day=1) - pd.Timedelta(days=1)).strftime("%Y-%m")
    out = {}
    for pair in PAIRS:
        path = folder / f"{pair}.parquet"
        old = pd.read_parquet(path) if path.exists() else None
        new = _bars_to_df(yahoo_docs(pair, None if old is None else [prev, now.strftime("%Y-%m")]))
        df = new if old is None else pd.concat([old, new])
        df = df.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
        df.to_parquet(path, index=False)
        out[pair] = df
        log(f"  Yahoo {pair}: {len(df):,} świec")
    return out


def heartbeat(state: str, job: dict | None = None) -> None:
    from firebase_admin import firestore

    db().collection("runner").document("heartbeat").set({
        "lastSeen": firestore.SERVER_TIMESTAMP,
        "state": state,
        "job": job or {},
        "version": ENGINE_VERSION,
        "host": socket.gethostname(),
    })


def set_data_sha(sha: str) -> None:
    db().collection("meta").document("status").set({"dataSha": sha}, merge=True)


def update_strategy(sid: str, fields: dict) -> None:
    db().collection("strategies").document(sid).set(fields, merge=True)


def delete_strategy(sid: str) -> None:
    db().collection("strategies").document(sid).delete()


def frozen_strategies() -> list[tuple[str, dict]]:
    """Policzone strategie z datą zamrożenia (odczyt: tyle dokumentów, ile policzonych strategii)."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    q = db().collection("strategies").where(filter=FieldFilter("status", "==", "policzona"))
    return [(s.id, s.to_dict()) for s in q.stream() if (s.to_dict() or {}).get("frozenAt")]


def watch_queue(on_job):
    """Nasłuch strategii do policzenia i do usunięcia (bez odpytywania w pętli — Z2)."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    q = db().collection("strategies").where(filter=FieldFilter("status", "in", ["do_policzenia", "do_usuniecia"]))

    def cb(snaps, _changes, _read_time):
        for s in snaps:
            on_job(s.id, s.to_dict())

    return q.on_snapshot(cb)
