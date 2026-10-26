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
    return True


def expected_ts(now: int) -> int:
    ts = last_closed_ts(now)
    for _ in range(80):
        if is_expected_bar(ts):
            break
        ts -= H
    return ts
