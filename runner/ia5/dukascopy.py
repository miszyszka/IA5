"""Pobieranie świec M1 bid/ask z Dukascopy (D7).

Plik dzienny: datafeed/{PARA}/{RRRR}/{MM-1:02}/{DD:02}/{BID|ASK}_candles_min_1.bi5
Format: LZMA, rekordy po 24 bajty, big-endian: czas od początku doby [s], open, close, low, high (int,
cena × punkt), wolumen (float32). Punkt: 1000 dla par z JPY, 100000 dla pozostałych.
Dane bieżącego dnia pojawiają się po jego zakończeniu, więc M1 kończy się na wczoraj (UTC).
"""
from __future__ import annotations

import lzma
import struct
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

BASE = "https://datafeed.dukascopy.com/datafeed"
REC = struct.Struct(">5if")
START = date(2003, 5, 1)
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


def _get(url: str, tries: int = 4) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return b""
            err = e
        except Exception as e:  # noqa: BLE001 — sieć: ponawiamy
            err = e
        time.sleep(2 ** i)
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


def sync_pair(pair: str, root: Path, log=print, workers: int = 8) -> int:
    """Dociąga brakujące miesiące do root/m1/{PARA}/{RRRR-MM}.parquet. Zwraca liczbę nowych plików.

    Zamknięty miesiąc zapisujemy raz i nie ruszamy (D4). Bieżący miesiąc nadpisujemy przy każdym sync.
    """
    folder = root / "m1" / pair
    folder.mkdir(parents=True, exist_ok=True)
    yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
    y, m, written = START.year, START.month, 0
    while (y, m) <= (yesterday.year, yesterday.month):
        path = folder / f"{y}-{m:02d}.parquet"
        current = (y, m) == (yesterday.year, yesterday.month)
        if current or not path.exists():
            days = month_days(y, m, yesterday)
            with ThreadPoolExecutor(workers) as ex:
                frames = [f for f in ex.map(lambda d: fetch_day(pair, d), days) if len(f)]
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)
            df.to_parquet(path, index=False)
            written += 1
            log(f"  {pair} {y}-{m:02d}: {len(df):,} minut")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return written


def load_m1(pair: str, root: Path) -> pd.DataFrame:
    files = sorted((root / "m1" / pair).glob("*.parquet"))
    if not files:
        return pd.DataFrame(columns=COLS)
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
