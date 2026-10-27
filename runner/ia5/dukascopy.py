"""Pobieranie świec M1 bid/ask z Dukascopy (D7).

Plik dzienny: datafeed/{PARA}/{RRRR}/{MM-1:02}/{DD:02}/{BID|ASK}_candles_min_1.bi5
Format: LZMA, rekordy po 24 bajty, big-endian: czas od początku doby [s], open, close, low, high (int,
cena × punkt), wolumen (float32). Punkt: 1000 dla par z JPY, 100000 dla pozostałych.
Dane bieżącego dnia pojawiają się po jego zakończeniu, więc M1 kończy się na wczoraj (UTC).
"""
from __future__ import annotations

import lzma
import struct
import threading
import time
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE = "https://datafeed.dukascopy.com/datafeed"
REC = struct.Struct(">5if")
START = date(2003, 5, 1)
WORKERS = 4      # jednoczesne dni na parę (każdy dzień = 2 pliki: BID i ASK)
TRIES = 6        # próby na plik, przerwy 2, 4, 8, 16, 32 s
COLS = ["ts", "bo", "bh", "bl", "bc", "bv", "ao", "ah", "al", "ac", "av"]


def point(pair: str) -> int:
    return 1000 if "JPY" in pair else 100000


def day_url(pair: str, d: date, side: str) -> str:
    return f"{BASE}/{pair}/{d.year}/{d.month - 1:02d}/{d.day:02d}/{side}_candles_min_1.bi5"


def decode_bi5(raw: bytes, day_start: int, pt: int) -> np.ndarray:
    """Zwraca tablicę [n, 6]: ts, open, high, low, close, volume."""
    if not raw:
        return np.empty((0, 6))
    data = lzma.decompress(raw)
    n = len(data) // REC.size
    out = np.empty((n, 6))
    for i, (t, o, c, lo, hi, v) in enumerate(REC.iter_unpack(data[: n * REC.size])):
        out[i] = (day_start + t, o / pt, hi / pt, lo / pt, c / pt, v)
    return out


_local = threading.local()


def _session():
    """Jedna sesja HTTP na wątek — połączenie utrzymywane między plikami (Dukascopy przycina nowe połączenia)."""
    s = getattr(_local, "s", None)
    if s is None:
        import requests

        s = requests.Session()
        s.headers["User-Agent"] = "Mozilla/5.0 (Macintosh; IA5 data sync)"
        _local.s = s
    return s


def _get(url: str, tries: int = TRIES) -> bytes:
    """Plik bi5; 404 = brak danych tego dnia (b""). Po TRIES nieudanych próbach — RuntimeError."""
    err: object = None
    for i in range(tries):
        try:
            r = _session().get(url, timeout=(10, 45))
            if r.status_code == 404:
                return b""
            if r.status_code == 200:
                return r.content
            err = f"HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001 — sieć: ponawiamy
            err = e
        if i < tries - 1:
            time.sleep(min(60, 2 ** (i + 1)))
    raise RuntimeError(f"Dukascopy: {url}: {err}")


def fetch_day(pair: str, d: date) -> pd.DataFrame:
    """Jeden dzień M1 z bid i ask w jednej tabeli (tylko minuty obecne w obu stronach)."""
    start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
    pt = point(pair)
    bid = decode_bi5(_get(day_url(pair, d, "BID")), start, pt)
    ask = decode_bi5(_get(day_url(pair, d, "ASK")), start, pt)
    if not len(bid) or not len(ask):
        return pd.DataFrame(columns=COLS)
    b = pd.DataFrame(bid, columns=["ts", "bo", "bh", "bl", "bc", "bv"])
    a = pd.DataFrame(ask, columns=["ts", "ao", "ah", "al", "ac", "av"])
    df = b.merge(a, on="ts", how="inner")
    df["ts"] = df["ts"].astype("int64")
    return df[COLS]


def month_days(y: int, m: int, until: date) -> list[date]:
    d, out = date(y, m, 1), []
    while d.month == m and d <= until:
        if d.isoweekday() != 6:  # soboty nie mają handlu
            out.append(d)
        d += timedelta(days=1)
    return out


def last_trading_day(y: int, m: int) -> date:
    """Ostatni dzień miesiąca od poniedziałku do piątku (dane FX kończą tydzień w piątek)."""
    d = date(y, m, monthrange(y, m)[1])
    while d.isoweekday() > 5:
        d -= timedelta(days=1)
    return d


def _max_ts(path: Path) -> int | None:
    """Najnowsza minuta w pliku — ze statystyk Parquet, bez czytania danych."""
    try:
        import pyarrow.parquet as pq

        meta = pq.ParquetFile(path).metadata
        if meta.num_rows == 0:
            return None
        col = meta.schema.names.index("ts")
        stats = [meta.row_group(i).column(col).statistics for i in range(meta.num_row_groups)]
        if all(s is not None and s.has_min_max for s in stats):
            return int(max(s.max for s in stats))
    except Exception:  # noqa: BLE001 — niżej pełny odczyt kolumny
        pass
    ts = pd.read_parquet(path, columns=["ts"])["ts"]
    return int(ts.max()) if len(ts) else None


def month_complete(path: Path, y: int, m: int) -> bool:
    """Czy zapisany miesiąc ma wszystkie dni.

    Plik zapisany w trakcie miesiąca (np. 20-go) kończy się na dniu przed zapisem. Bez tej kontroli
    po przejściu na nowy miesiąc zostałby „zamknięty" z trwałą luką do końca miesiąca.
    Pełny = ma dane z ostatniego dnia handlowego albo został zapisany ≥ 2 dni po końcu miesiąca
    (wtedy zawiera wszystko, co Dukascopy ma — np. gdy ostatni dzień był świętem bez notowań).
    Pusty plik = Dukascopy nie ma tego miesiąca (np. przed startem notowań pary) — pełny.
    """
    if not path.exists():
        return False
    end = datetime(y, m, monthrange(y, m)[1], tzinfo=UTC) + timedelta(days=1)
    if datetime.fromtimestamp(path.stat().st_mtime, UTC) >= end + timedelta(days=2):
        return True
    mx = _max_ts(path)
    return mx is None or datetime.fromtimestamp(mx, UTC).date() >= last_trading_day(y, m)


def months_to_sync(root: Path, pair: str, until: date) -> list[tuple[int, int]]:
    """Miesiące do pobrania: brakujące lub niepełne pliki + bieżący miesiąc (zawsze odświeżany)."""
    folder = root / "m1" / pair
    y, m, out = START.year, START.month, []
    while (y, m) <= (until.year, until.month):
        if (y, m) == (until.year, until.month) or not month_complete(folder / f"{y}-{m:02d}.parquet", y, m):
            out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def sync_pair(pair: str, root: Path, log=print, workers: int = WORKERS, progress=None, on_month=None) -> dict:
    """Dociąga brakujące miesiące do root/m1/{PARA}/{RRRR-MM}.parquet.

    Zamknięty miesiąc zapisujemy raz i nie ruszamy (D4). Bieżący miesiąc nadpisujemy przy każdym sync.
    Miesiąc, w którym choć jeden dzień się nie pobrał, NIE jest zapisywany — dociągnie się przy następnym
    uruchomieniu (inaczej zostałaby trwała luka). Błąd sieci nigdy nie przerywa całej synchronizacji.
    progress(i, n) — wołane po każdym miesiącu.
    on_month(y, m, ok, rows) — wynik miesiąca (mapa pokrycia na żywo w dashboardzie).
    """
    folder = root / "m1" / pair
    folder.mkdir(parents=True, exist_ok=True)
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    todo = months_to_sync(root, pair, yesterday)
    written, failed = 0, []

    def safe_day(d):
        try:
            return fetch_day(pair, d)
        except Exception as e:  # noqa: BLE001
            return e

    for k, (y, m) in enumerate(todo, 1):
        days = month_days(y, m, yesterday)
        with ThreadPoolExecutor(workers) as ex:
            res = list(ex.map(safe_day, days))
        errs = [r for r in res if isinstance(r, Exception)]
        if errs:
            failed.append(f"{y}-{m:02d}")
            log(f"  {pair} {y}-{m:02d}: {len(errs)} dni nie pobrano ({str(errs[0])[-80:]}) — ponowię przy następnym uruchomieniu")
            if on_month:
                on_month(y, m, False, 0)
        else:
            frames = [f for f in res if len(f)]
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)
            df.to_parquet(folder / f"{y}-{m:02d}.parquet", index=False)
            written += 1
            log(f"  {pair} {y}-{m:02d}: {len(df):,} minut")
            if on_month:
                on_month(y, m, True, len(df))
        if progress:
            progress(k, len(todo))
    return {"written": written, "failed": failed, "todo": len(todo)}


def load_m1(pair: str, root: Path) -> pd.DataFrame:
    files = sorted((root / "m1" / pair).glob("*.parquet"))
    if not files:
        return pd.DataFrame(columns=COLS)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
