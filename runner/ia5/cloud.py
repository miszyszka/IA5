"""Firestore z Maca (firebase-admin, service account — uprawnienia administracyjne).

Budżet (Z4): heartbeat co 30 s ≈ 2 880 zapisów/dobę, gdy program działa; kopia świec Yahoo: ok. 200 odczytów
za pierwszym razem, potem 16 (poprzedni i bieżący miesiąc × 8 par) co godzinę ≈ 400 odczytów/dobę;
przegląd zdrowia: 1 odczyt meta/status + lista strategii (kilka–kilkanaście) co godzinę.
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


def months_since(ts: int, now: datetime) -> list[str]:
    """Miesiące od miesiąca przed `ts` do bieżącego — tyle trzeba doczytać, żeby kopia nie miała dziury po przerwie."""
    d = (datetime.fromtimestamp(int(ts), timezone.utc).replace(day=1) - pd.Timedelta(days=1)).replace(day=1)
    out = []
    while (d.year, d.month) <= (now.year, now.month):
        out.append(d.strftime("%Y-%m"))
        d = (d + pd.Timedelta(days=32)).replace(day=1)
    return out


def keep_other_months(df: pd.DataFrame, months: list[str] | None) -> pd.DataFrame:
    """Wiersze kopii spoza doczytanych miesięcy (doczytane miesiące zastępujemy w całości)."""
    if not months or df is None or df.empty:
        return df
    m = pd.to_datetime(df["ts"], unit="s", utc=True).dt.strftime("%Y-%m")
    return df[~m.isin(months)]


def sync_yahoo(folder, log=print) -> dict[str, pd.DataFrame]:
    """Kopia świec Yahoo z Firestore do folder/{PARA}.parquet (D-039: jedyne źródło cen).

    Pierwszy raz pełny odczyt (ok. 25 dokumentów na parę), potem miesiące od ostatniej świecy kopii do dziś
    (zwykle 2 na parę → 16 odczytów; po dłuższej przerwie Maca więcej — kopia nie ma dziur). Yahoo poprawia
    ostatnie świece, więc doczytane miesiące zastępują stare W CAŁOŚCI — kopia = Firestore także wtedy, gdy
    z dokumentu usunięto wpis (np. notowanie Yahoo poza pełną godziną, D-042). Zapis atomowy.
    """
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    out = {}
    for pair in PAIRS:
        path = folder / f"{pair}.parquet"
        old = pd.read_parquet(path) if path.exists() else None
        if old is not None and old.empty:
            old = None
        months = None if old is None else months_since(int(old["ts"].max()), now)
        new = _bars_to_df(yahoo_docs(pair, months))
        df = new if old is None else pd.concat([keep_other_months(old, months), new])
        df = df.drop_duplicates("ts", keep="last").sort_values("ts").reset_index(drop=True)
        df["ts"] = df["ts"].astype("int64")
        tmp = path.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(path)
        out[pair] = df
        last = f", ostatnia {datetime.fromtimestamp(int(df.ts.iloc[-1]), timezone.utc):%Y-%m-%d %H:%M} UTC" if len(df) else ""
        log(f"  Yahoo {pair}: {len(df):,} świec{last}")
    return out


def load_yahoo(folder) -> dict[str, pd.DataFrame]:
    """Kopia lokalna bez czytania Firestore (ia5 health, ia5 run)."""
    return {p: pd.read_parquet(folder / f"{p}.parquet") for p in PAIRS if (folder / f"{p}.parquet").exists()}


def heartbeat(state: str, job: dict | None = None) -> None:
    """runner/heartbeat (Z4: co 30 s ≈ 2 880 zapisów/dobę, gdy ia5 start działa).
    Pola `sync` i `fetch` zostały po pobieraniu Dukascopy — usuwane przy każdym zapisie (D-039)."""
    from firebase_admin import firestore

    doc = {
        "lastSeen": firestore.SERVER_TIMESTAMP,
        "state": state,
        "job": job or {},
        "version": ENGINE_VERSION,
        "host": socket.gethostname(),
        "sync": firestore.DELETE_FIELD,
        "fetch": firestore.DELETE_FIELD,
    }
    db().collection("runner").document("heartbeat").set(doc, merge=list(doc))


def list_strategies() -> list[dict]:
    """Wszystkie strategie (do przeglądu zdrowia; tyle odczytów, ile strategii — kilka-kilkanaście)."""
    out = []
    for snap in db().collection("strategies").stream():
        d = snap.to_dict() or {}
        if hasattr(d.get("createdAt"), "timestamp"):
            d["createdAt"] = int(d["createdAt"].timestamp())
        out.append({"id": snap.id, **{k: d.get(k) for k in ("name", "status", "error", "createdAt", "frozenAt")}})
    return out


def write_health(h: dict) -> None:
    """meta/status.health — 1 zapis na przegląd (co godzinę ≈ 24 zapisy/dobę, D-023)."""
    db().collection("meta").document("status").set({"health": h}, merge=True)


def set_data_sha(sha: str) -> None:
    db().collection("meta").document("status").set({"dataSha": sha}, merge=True)


def update_strategy(sid: str, fields: dict) -> None:
    db().collection("strategies").document(sid).set(fields, merge=True)


def delete_strategy(sid: str) -> None:
    db().collection("strategies").document(sid).delete()


def computed_strategies() -> list[tuple[str, dict]]:
    """Strategie z wynikiem (policzone) — do ponownego liczenia po zmianie źródła danych (D-039)."""
    from google.cloud.firestore_v1.base_query import FieldFilter

    q = db().collection("strategies").where(filter=FieldFilter("status", "==", "policzona"))
    return [(s.id, s.to_dict() or {}) for s in q.stream()]


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
