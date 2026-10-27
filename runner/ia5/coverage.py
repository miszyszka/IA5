"""Mapa pokrycia danych (zakładka Stats): para × miesiąc wobec kalendarza sesji (D-022).

Liczone z surowych danych na Macu: pliki M1 Dukascopy (który miesiąc jest, który nie) i świece H1 z nich
zbudowane (która godzina jest, z ilu aktywnych minut). Zgłasza, niczego nie naprawia (D5).
Wynik to same liczniki i zakresy luk — bez cen, więc może iść na publiczną gałąź `data` (D-010).

Statusy miesiąca:
  0 brak pliku · 1 pełny · 2 w toku / niepełny (dociągnie się) · 3 Dukascopy nie ma danych · 4 błąd pobierania
Luki (godziny oczekiwane w sesji, a nieobecne) w dwóch rodzajach:
  "w" wspólna — brakuje jej w co najmniej połowie par, które mają ten okres (święto, krótka sesja albo przerwa źródła),
  "p" tylko ta para — prawdziwa dziura w danych tej pary.
Każda luka ma potwierdzenie z drugiego źródła: ile z jej godzin ma Yahoo (dla Dukascopy) albo Dukascopy (dla Yahoo);
-1 = drugie źródło nie obejmuje tego okresu.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

H = 3600
DAY = 86400
THIN_MINUTES = 30      # godzina H1 złożona z mniej niż 30 minut z notowaniami = „cienka”
COMMON_SHARE = 0.5     # luka wspólna, gdy brakuje jej w ≥ połowie par mających ten okres
COMMON_MIN_PAIRS = 3   # przy mniej niż 3 parach nie da się powiedzieć, że luka jest wspólna
QUIET_PIPS = 1.0       # luka do 3 h, po której cena jest ta sama (< 1 pips) = „bez ruchu” — nic nie przepadło (D-028)
QUIET_MAX_H = 3
NONE, FULL, PARTIAL, EMPTY, FAILED, INCOMPLETE = 0, 1, 2, 3, 4, 5
LIVE_CODE = {NONE: ".", FULL: "o", PARTIAL: "~", EMPTY: "-", FAILED: "x", INCOMPLETE: "!"}


# ---------- kalendarz ----------

def expected_mask(ts) -> np.ndarray:
    """Wektorowo to samo co session.is_expected_bar (test sprawdza każdą godzinę od 2003)."""
    ts = np.asarray(ts, dtype=np.int64)
    wd = (ts // DAY + 4) % 7  # 0 = niedziela; 1970-01-01 był czwartkiem
    hr = (ts % DAY) // H
    day = (ts // DAY).astype("datetime64[D]")
    mon = day.astype("datetime64[M]")
    dom = (day - mon).astype(np.int64) + 1
    mo = mon.astype(np.int64) % 12 + 1
    # święta FX: 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC — rynek nieczynny (D-028)
    hol = ((mo == 12) & ((dom == 24) | (dom == 31)) & (hr >= 21)) | (((mo == 12) & (dom == 25)) | ((mo == 1) & (dom == 1))) & (hr < 22)
    return ~((wd == 6) | ((wd == 5) & (hr >= 21)) | ((wd == 0) & (hr < 22)) | hol)


def expected_hours(a: int, b: int) -> np.ndarray:
    """Godziny [a, b), w których świeca musi istnieć."""
    a = -(-int(a) // H) * H
    hours = np.arange(a, int(b), H, dtype=np.int64)
    return hours[expected_mask(hours)]


def win_hours(mi: dict) -> np.ndarray:
    """Oczekiwane godziny okna miesiąca bez dni, których jeszcze nie pobrano (te nie są lukami)."""
    e = expected_hours(*mi["win"])
    if mi.get("skip"):
        e = e[~np.isin(e // DAY * DAY, np.asarray(mi["skip"], np.int64))]
    return e


def month_key(y: int, m: int) -> str:
    return f"{y}-{m:02d}"


def months(start: date, last: date) -> list[tuple[int, int]]:
    y, m, out = start.year, start.month, []
    while (y, m) <= (last.year, last.month):
        out.append((y, m))
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def month_bounds(y: int, m: int) -> tuple[int, int]:
    a = datetime(y, m, 1, tzinfo=UTC)
    b = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=UTC)
    return int(a.timestamp()), int(b.timestamp())


def month_index(ts: np.ndarray, start: date) -> np.ndarray:
    """Numer miesiąca liczony od `start` (0 = miesiąc startu)."""
    mon = np.asarray(ts, dtype=np.int64).astype("datetime64[s]").astype("datetime64[M]").astype(np.int64)
    return mon - ((start.year - 1970) * 12 + start.month - 1)


def day_end(ts: int) -> int:
    return (int(ts) // DAY + 1) * DAY


# ---------- stan plików Dukascopy ----------

def _rows(path: Path) -> int:
    import pyarrow.parquet as pq

    return pq.ParquetFile(path).metadata.num_rows


def dukascopy_months(root: Path, pair: str, until: date, failed=()) -> list[dict]:
    """Stan każdego miesiąca od START do `until`: status i okno [a, b), w którym liczymy godziny.

    Okno pełnego miesiąca kończy się z miesiącem (albo z końcem danych). Okno niepełnego kończy się
    na ostatnim dniu w pliku — brakujący ogon to nie luka, tylko dane do dociągnięcia.
    """
    from .dukascopy import START, _max_ts, month_complete, read_missing

    folder = root / "m1" / pair
    data_end = int(datetime(until.year, until.month, until.day, tzinfo=UTC).timestamp()) + DAY
    failed = set(failed)
    out = []
    for y, m in months(START, until):
        a, b = month_bounds(y, m)
        b = min(b, data_end)
        path = folder / f"{month_key(y, m)}.parquet"
        has = path.exists()
        rows = _rows(path) if has else 0
        missing = read_missing(path) if has else []
        if not has:
            st = FAILED if month_key(y, m) in failed else NONE
        elif missing:
            st = INCOMPLETE  # część dni pobrana i zapisana, reszta dociągnie się później (D-025)
        elif rows == 0:
            st = EMPTY
        elif (y, m) == (until.year, until.month) or not month_complete(path, y, m):
            st = PARTIAL
        else:
            st = FULL
        win = None
        skip = [int(datetime.fromisoformat(d).replace(tzinfo=UTC).timestamp()) for d in missing]
        if rows or missing:
            end = max(([day_end(_max_ts(path))] if rows else []) + [x + DAY for x in skip])
            win = (a, b) if st == FULL else (a, min(b, end))
        out.append({"key": month_key(y, m), "status": st, "cal": (a, b), "win": win, "skip": skip})
    return out


def live_states(root: Path, pair: str, until: date, failed=()) -> str:
    """Statusy miesięcy jako krótki napis (1 znak = 1 miesiąc) — do heartbeatu w trakcie pobierania."""
    return "".join(LIVE_CODE[m["status"]] for m in dukascopy_months(root, pair, until, failed))


# ---------- liczenie pokrycia ----------

def _present(df: pd.DataFrame | None) -> tuple[np.ndarray, np.ndarray | None]:
    if df is None or df.empty:
        return np.empty(0, np.int64), None
    ts = df["ts"].to_numpy(np.int64)
    mins = df["minutes"].to_numpy() if "minutes" in df else None
    return ts, mins


def source_coverage(month_info: dict[str, list[dict]], frames: dict[str, pd.DataFrame], start: date,
                    other: dict[str, tuple[np.ndarray, np.ndarray]] | None = None) -> dict:
    """month_info[para] = lista miesięcy (status, cal, win), frames[para] = H1 (ts, opcjonalnie minutes).

    other[para] = (godziny obecne w drugim źródle, godziny objęte drugim źródłem) — do potwierdzenia luk.
    Zwraca {"pairs": {para: {"m": [[status, oczekiwane, obecne, dziury, wspólne, cienkie], ...],
                              "gaps": [[od, do, godzin, rodzaj, w drugim źródle], ...]}}}.
    Rodzaj luki: "p" dziura tej pary (rynek działał, cena się ruszała), "w" wspólna (rynek nieczynny / przerwa
    źródła), "q" bez ruchu (≤ 3 h, cena po luce taka jak przed — nic nie przepadło). Pole „wspólne” = w + q.
    """
    from .config import PAIRS

    exp, miss, pres_sets, mins_map = {}, {}, {}, {}
    for pair, info in month_info.items():
        ts, mins = _present(frames.get(pair))
        hours = [win_hours(mi) for mi in info if mi["win"]]
        e = np.concatenate(hours) if hours else np.empty(0, np.int64)
        exp[pair] = e
        miss[pair] = e[~np.isin(e, ts)]
        pres_sets[pair] = ts
        mins_map[pair] = mins

    # ile par ma daną godzinę w oknie i ilu z nich jej brakuje → luka wspólna czy tylko tej pary
    all_e = np.concatenate(list(exp.values())) if exp else np.empty(0, np.int64)
    all_m = np.concatenate(list(miss.values())) if miss else np.empty(0, np.int64)
    eu, ec = np.unique(all_e, return_counts=True)
    mu, mc = np.unique(all_m, return_counts=True)

    out = {}
    for pair, info in month_info.items():
        e, mh, ts, mins = exp[pair], miss[pair], pres_sets[pair], mins_map[pair]
        cover = ec[np.searchsorted(eu, mh)] if len(mh) else np.empty(0, np.int64)
        missing = mc[np.searchsorted(mu, mh)] if len(mh) else np.empty(0, np.int64)
        common = (cover >= COMMON_MIN_PAIRS) & (missing >= COMMON_SHARE * cover)

        # zakresy luk: kolejne godziny w ciągu oczekiwanych (luka przez weekend to jedna luka)
        gaps = []
        if len(mh):
            pos = np.searchsorted(e, mh)
            # cięcie: przerwa w ciągu oczekiwanych godzin, zmiana rodzaju albo miesiąc bez danych pomiędzy
            cut = np.flatnonzero((np.diff(pos) != 1) | (np.diff(common.astype(np.int8)) != 0)
                                 | (np.diff(mh) > 4 * DAY)) + 1
            o_pres, o_cov = (other or {}).get(pair, (None, None))
            df = frames.get(pair)
            px = df is not None and {"open", "close"} <= set(df.columns) and pair in PAIRS
            if px:
                ord_ = np.argsort(ts)
                ts_s, op_s, cl_s = ts[ord_], df["open"].to_numpy(float)[ord_], df["close"].to_numpy(float)[ord_]
            quiet = np.zeros(len(mh), bool)
            for seg_i, seg_h, seg_c in zip(np.split(np.arange(len(mh)), cut), np.split(mh, cut), np.split(common, cut)):
                conf = -1
                if o_cov is not None and np.isin(seg_h, o_cov).all():
                    conf = int(np.isin(seg_h, o_pres).sum())
                kind = "w" if seg_c[0] else "p"
                # D-028: krótka luka, po której cena się nie ruszyła — rynek stał, nie ma czego brakować
                if kind == "p" and px and len(seg_h) <= QUIET_MAX_H:
                    j = np.searchsorted(ts_s, seg_h[0])
                    if 0 < j < len(ts_s) and abs(op_s[j] - cl_s[j - 1]) / PAIRS[pair].pip < QUIET_PIPS:
                        kind = "q"
                        quiet[seg_i] = True
                gaps.append([int(seg_h[0]), int(seg_h[-1]) + H, int(len(seg_h)), kind, conf])
            common = common | quiet
        # dziury = tylko luki, w których rynek działał i cena się ruszała; wspólne i „bez ruchu” liczone osobno
        n = len(info)
        holes = np.bincount(month_index(mh[~common], start), minlength=n)[:n]
        shared = np.bincount(month_index(mh[common], start), minlength=n)[:n]
        in_win = np.isin(ts, e)
        present = np.bincount(month_index(ts[in_win], start), minlength=n)[:n]
        thin = np.zeros(n, np.int64)
        if mins is not None:
            t = ts[in_win & (mins < THIN_MINUTES)]
            thin = np.bincount(month_index(t, start), minlength=n)[:n]

        rows = []
        for i, mi in enumerate(info):
            # 7. pole: godziny sesji w dniach jeszcze niepobranych (tyle brakuje w niepełnym miesiącu)
            if mi["win"]:
                skipped = int(len(expected_hours(*mi["win"])) - len(win_hours(mi))) if mi.get("skip") else 0
                rows.append([mi["status"], int(len(win_hours(mi))), int(present[i]),
                             int(holes[i]), int(shared[i]), int(thin[i]), skipped])
            else:  # bez danych: oczekiwane wg kalendarza całego miesiąca — tyle brakuje
                rows.append([mi["status"], int(len(expected_hours(*mi["cal"]))) if mi["status"] != EMPTY else 0, 0, 0, 0, 0, 0])

        out[pair] = {"m": rows, "gaps": gaps}
    return {"pairs": out}


def yahoo_months(df: pd.DataFrame | None, start: date, last: date) -> list[dict]:
    """Yahoo: okno od pierwszej do ostatniej zapisanej świecy; bieżący miesiąc = w toku."""
    info = []
    first = int(df["ts"].min()) if df is not None and len(df) else None
    end = int(df["ts"].max()) + H if first is not None else None
    for y, m in months(start, last):
        a, b = month_bounds(y, m)
        win = None
        st = NONE
        if first is not None and b > first and a < end:
            win = (max(a, first), min(b, end))
            st = PARTIAL if b > end else FULL
        info.append({"key": month_key(y, m), "status": st, "cal": (a, b), "win": win})
    return info


def build(root: Path, h1: dict[str, pd.DataFrame], yahoo: dict[str, pd.DataFrame], failed: dict | None = None,
          until: date | None = None, now: int | None = None) -> dict:
    """Pełna mapa dla obu źródeł. root = ~/.ia5/data (pliki M1), h1 = Dukascopy H1, yahoo = świece Yahoo."""
    from .dukascopy import START

    now = now or int(datetime.now(UTC).timestamp())
    until = until or (datetime.fromtimestamp(now, UTC).date() - timedelta(days=1))
    failed = failed or {}
    pairs = list(h1.keys() | yahoo.keys())
    pairs.sort(key=lambda p: list(_pairs()).index(p) if p in _pairs() else 99)

    d_info = {p: dukascopy_months(root, p, until, failed.get(p, ())) for p in pairs}
    y_first = min((int(df["ts"].min()) for df in yahoo.values() if df is not None and len(df)), default=None)
    y_start = datetime.fromtimestamp(y_first, UTC).date().replace(day=1) if y_first else until.replace(day=1)
    y_info = {p: yahoo_months(yahoo.get(p), y_start, datetime.fromtimestamp(now, UTC).date()) for p in pairs}

    def cover(info):  # godziny objęte oknami źródła
        hours = [win_hours(mi) for mi in info if mi["win"]]
        return np.concatenate(hours) if hours else np.empty(0, np.int64)

    d_ts = {p: _present(h1.get(p))[0] for p in pairs}
    y_ts = {p: _present(yahoo.get(p))[0] for p in pairs}
    d_other = {p: (y_ts[p], cover(y_info[p])) for p in pairs}
    y_other = {p: (d_ts[p], cover(d_info[p])) for p in pairs}

    duka = source_coverage(d_info, h1, START, d_other)
    yah = source_coverage(y_info, yahoo, y_start, y_other)
    data_end = int(datetime(until.year, until.month, until.day, tzinfo=UTC).timestamp()) + DAY
    return {
        "v": 1, "generated": now, "thin_minutes": THIN_MINUTES, "common_share": COMMON_SHARE,
        "sources": {
            "dukascopy": {"label": "Dukascopy M1 → H1", "role": "backtesty", "start": month_key(START.year, START.month),
                          "end": data_end, "thin": True, "other": "Yahoo", **duka},
            "yahoo": {"label": "Yahoo H1", "role": "monitoring", "start": month_key(y_start.year, y_start.month),
                      "end": max((int(df["ts"].max()) + H for df in yahoo.values() if df is not None and len(df)), default=now),
                      "thin": False, "other": "Dukascopy", **yah},
        },
    }


def _pairs():
    from .config import PAIRS

    return PAIRS


def content_hash(cov: dict) -> str:
    """Hash bez znacznika czasu — publikujemy tylko, gdy coś się zmieniło."""
    body = {k: v for k, v in cov.items() if k != "generated"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
