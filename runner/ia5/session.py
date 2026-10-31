"""Kalendarz sesji FX — ta sama logika co apps_script/Code.gs i web/status.js."""
from datetime import datetime, timezone

H = 3600


def last_closed_ts(now: int) -> int:
    """Najnowsza zamknięta świeca H1 (D2)."""
    return ((now - 60 - H) // H) * H


def is_expected_bar(ts: int) -> bool:
    """Czy świeca otwarta o ts musi istnieć (szerokie okno weekendu: lato i zima)."""
    d = datetime.fromtimestamp(ts, tz=timezone.utc)
    wd, hr = d.isoweekday() % 7, d.hour  # 0 = niedziela, 6 = sobota
    if wd == 6:
        return False
    if wd == 5 and hr >= 21:
        return False
    if wd == 0 and hr < 22:
        return False
    # święta FX: 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC — rynek nieczynny (D-028)
    md = (d.month, d.day)
    if md in ((12, 24), (12, 31)) and hr >= 21:
        return False
    if md in ((12, 25), (1, 1)) and hr < 22:
        return False
    return True


BOUNDARY_H = 3  # D-039: Yahoo otwiera tydzień 1–2 h później niż kalendarz (niedziela 22:00 UTC) — to nie brak danych


def week_open_grace(last_ts: int, now: int) -> bool:
    """Czy brakuje tylko pierwszych ≤ 3 godzin po weekendzie albo święcie (granica tygodnia, jak w clean.py)."""
    if not last_ts or now - last_ts > 5 * 86400:
        return False
    missing = [t for t in range(int(last_ts) + H, last_closed_ts(now) + H, H) if is_expected_bar(t)]
    return 0 < len(missing) <= BOUNDARY_H and not is_expected_bar(missing[0] - H)


def in_trading_hours(ts, hours=None, tz=None):
    """B11 (D-028): czy świeca otwarta o ts (UTC) zaczyna się w oknie handlu czasu polskiego.

    Okno [07:00, 17:00) Europe/Warsaw — z czasem letnim: zimą 06–16 UTC, latem 05–15 UTC.
    hours=None → wartości z config; hours=False → bez ograniczenia (testy zgodności z innym silnikiem).
    """
    import numpy as np
    import pandas as pd

    from .config import TRADING_HOURS, TRADING_TZ

    ts = np.asarray(ts, dtype=np.int64)
    if hours is False:
        return np.ones(len(ts), bool)
    a, b = hours or TRADING_HOURS
    hr = pd.to_datetime(ts, unit="s", utc=True).tz_convert(tz or TRADING_TZ).hour.to_numpy()
    return (hr >= a) & (hr < b)


def expected_ts(now: int) -> int:
    ts = last_closed_ts(now)
    for _ in range(80):
        if is_expected_bar(ts):
            break
        ts -= H
    return ts
