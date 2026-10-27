"""Pobieranie świec M1 bid/ask z Dukascopy (D7).

Plik dzienny: datafeed/{PARA}/{RRRR}/{MM-1:02}/{DD:02}/{BID|ASK}_candles_min_1.bi5
Format: LZMA, rekordy po 24 bajty, big-endian: czas od początku doby [s], open, close, low, high (int,
cena × punkt), wolumen (float32). Punkt: 1000 dla par z JPY, 100000 dla pozostałych.
Dane bieżącego dnia pojawiają się po jego zakończeniu, więc M1 kończy się na wczoraj (UTC).
"""
from __future__ import annotations

import json
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
WORKERS = 6      # jednoczesne dni na start (każdy dzień = 2 pliki: BID i ASK); dalej tempo dobiera się samo (D-026)
MIN_WORKERS, MAX_WORKERS = 1, 8
COOLDOWN = 15    # s przerwy, gdy serwer odrzuca > 1/3 dni miesiąca (dławienie po stronie Dukascopy)
TRIES = 3        # próby na plik, przerwy 2, 4 s — dzień, który się nie pobrał, zostaje zapisany jako brakujący
                 # i jest dociągany przy następnym uruchomieniu (D-025), więc nie warto czekać minutami
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


FAST = {"tries": 1, "timeout": (5, 15)}     # D-029: przebieg główny — jedna krótka próba, nieudany dzień idzie na listę
REPAIR = {"tries": 2, "timeout": (10, 30)}  # przebieg naprawczy — tylko brakujące dni, wolniej i cierpliwiej


def _get(url: str, tries: int = TRIES, timeout=(10, 45)) -> bytes:
    """Plik bi5; 404 = brak danych tego dnia (b""). Po `tries` nieudanych próbach — RuntimeError."""
    err: object = None
    for i in range(tries):
        try:
            r = _session().get(url, timeout=timeout)
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


def fetch_day(pair: str, d: date, tries: int = TRIES, timeout=(10, 45)) -> pd.DataFrame:
    """Jeden dzień M1 z bid i ask w jednej tabeli (tylko minuty obecne w obu stronach)."""
    start = int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())
    pt = point(pair)
    bid = decode_bi5(_get(day_url(pair, d, "BID"), tries, timeout), start, pt)
    ask = decode_bi5(_get(day_url(pair, d, "ASK"), tries, timeout), start, pt)
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


def missing_path(path: Path) -> Path:
    """Plik obok miesiąca z listą dni, których nie udało się pobrać (D-025): RRRR-MM.missing.json."""
    return path.with_name(path.stem + ".missing.json")


def read_missing(path: Path) -> list[str]:
    try:
        return sorted(json.loads(missing_path(path).read_text()))
    except (FileNotFoundError, ValueError):
        return []


def days_to_fetch(path: Path, y: int, m: int, until: date) -> list[date]:
    """Dni do pobrania: cały miesiąc, gdy pliku nie ma; inaczej brakujące dni + dni po ostatnim dniu w pliku."""
    days = month_days(y, m, until)
    if not path.exists():
        return days
    missing = set(read_missing(path))
    mx = _max_ts(path)
    last = datetime.fromtimestamp(mx, UTC).date() if mx is not None else None
    return [d for d in days if d.isoformat() in missing or (last is not None and d > last)
            or (last is None and not missing)]


def month_complete(path: Path, y: int, m: int) -> bool:
    """Czy zapisany miesiąc ma wszystkie dni.

    Plik zapisany w trakcie miesiąca (np. 20-go) kończy się na dniu przed zapisem. Bez tej kontroli
    po przejściu na nowy miesiąc zostałby „zamknięty" z trwałą luką do końca miesiąca.
    Pełny = ma dane z ostatniego dnia handlowego albo został zapisany ≥ 2 dni po końcu miesiąca
    (wtedy zawiera wszystko, co Dukascopy ma — np. gdy ostatni dzień był świętem bez notowań).
    Pusty plik = Dukascopy nie ma tego miesiąca (np. przed startem notowań pary) — pełny.
    """
    if not path.exists() or missing_path(path).exists():
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


def sync_pair(pair: str, root: Path, log=print, workers: int = WORKERS, progress=None, on_month=None, repair: bool = False) -> dict:
    """Dociąga brakujące dane do root/m1/{PARA}/{RRRR-MM}.parquet (D-025).

    Pobierane są tylko brakujące dni: cały miesiąc, gdy pliku nie ma; inaczej dni z listy brakujących
    (RRRR-MM.missing.json) i dni po ostatnim dniu w pliku (bieżący miesiąc, miesiąc zapisany w trakcie).
    Pobrane dni są dopisywane do pliku od razu — nawet gdy część dni się nie udała; te trafiają na listę
    brakujących i są ponawiane przy następnym uruchomieniu. Już zapisane minuty się nie zmieniają (D4).
    Błąd sieci nigdy nie przerywa całej synchronizacji.
    progress(i, n) — wołane po każdym miesiącu.
    on_month(y, m, code) — stan miesiąca dla mapy na żywo: "o" pełny, "~" bieżący, "!" niepełny, "x" nic, "-" brak u Dukascopy.

    D-029: przebieg główny (repair=False) robi jedną krótką próbę na plik i nie czeka — dzień odrzucony przez serwer
    od razu trafia na listę brakujących. Przebieg naprawczy (repair=True) wraca tylko do miesięcy z brakującymi
    dniami, wolniej i z dwiema próbami. Dawniej jeden zawieszony plik kosztował do 3 min (3 próby × 55 s).
    """
    folder = root / "m1" / pair
    folder.mkdir(parents=True, exist_ok=True)
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    todo = months_to_sync(root, pair, yesterday)
    if repair:
        todo = [(y, m) for y, m in todo if missing_path(folder / f"{y}-{m:02d}.parquet").exists()]
    written, failed = 0, []
    opts = REPAIR if repair else FAST
    t0 = time.time()

    def safe_day(d):
        try:
            return fetch_day(pair, d, opts["tries"], opts["timeout"])
        except Exception as e:  # noqa: BLE001
            return e

    pace = 2 if repair else workers

    def fetch(days, n):
        with ThreadPoolExecutor(max(1, n)) as ex:
            return list(ex.map(safe_day, days))

    for k, (y, m) in enumerate(todo, 1):
        path = folder / f"{y}-{m:02d}.parquet"
        days = days_to_fetch(path, y, m, yesterday)
        res = fetch(days, pace)
        bad_i = [i for i, r in enumerate(res) if isinstance(r, Exception)]
        if bad_i and len(bad_i) > len(days) // 3:
            # serwer dławi — zwalniamy i krótko odpoczywamy; odrzucone dni czekają na przebieg naprawczy
            pace = max(MIN_WORKERS + 1, pace // 2)
            time.sleep(COOLDOWN)
        elif not bad_i and pace < MAX_WORKERS:
            pace += 1  # czysty miesiąc — przyspieszamy
        bad = [d for d, r in zip(days, res) if isinstance(r, Exception)]
        frames = [r for r in res if not isinstance(r, Exception) and len(r)]
        missing = sorted((set(read_missing(path)) - {d.isoformat() for d in days}) | {d.isoformat() for d in bad})
        if len(bad) == len(days) and days and not path.exists():
            failed.append(f"{y}-{m:02d}")
            log(f"  {pair} {y}-{m:02d}: nic nie pobrano ({str(res[0])[-80:]}) — ponowię przy następnym uruchomieniu")
            code = "x"
        else:
            old = pd.read_parquet(path) if path.exists() else None
            parts = ([old] if old is not None and len(old) else []) + frames
            df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=COLS)
            if len(df):
                df = df.drop_duplicates("ts", keep="first").sort_values("ts").reset_index(drop=True)  # D4: stare minuty zostają
            df.to_parquet(path, index=False)
            mp = missing_path(path)
            if missing:
                mp.write_text(json.dumps(missing))
                failed.append(f"{y}-{m:02d}")
                log(f"  {pair} {y}-{m:02d}: {len(df):,} minut, brakuje {len(missing)} dni ({', '.join(x[8:] for x in missing[:6])}"
                    f"{'…' if len(missing) > 6 else ''}) — {'na następne uruchomienie' if repair else 'wrócę w naprawie'}")
                code = "!"
            else:
                mp.unlink(missing_ok=True)
                log(f"  {pair} {y}-{m:02d}: {len(df):,} minut")
                code = "-" if not len(df) else "~" if (y, m) == (yesterday.year, yesterday.month) else "o"
            written += 1
        if on_month:
            on_month(y, m, code)
        if k % 12 == 0 and k < len(todo):  # co rok: postęp i szacowany czas do końca pary
            left = (time.time() - t0) / k * (len(todo) - k)
            log(f"  {pair}: {k}/{len(todo)} mies.{' (naprawa)' if repair else ''} · zostało ok. {left / 60:.0f} min")
        if progress:
            progress(k, len(todo))
    return {"written": written, "failed": failed, "todo": len(todo)}


def load_m1(pair: str, root: Path) -> pd.DataFrame:
    files = sorted((root / "m1" / pair).glob("????-??.parquet"))
    if not files:
        return pd.DataFrame(columns=COLS)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
