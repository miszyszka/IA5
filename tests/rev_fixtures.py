"""Syntetyczne kursy walut do PLN dla testów REV (D-062): dni robocze, znacznik = północ w Londynie (jak D1 Yahoo)."""
from __future__ import annotations

import numpy as np
import pandas as pd

LONDON = "Europe/London"


def london_midnight(day: str) -> int:
    return int(pd.Timestamp(day).tz_localize(LONDON).tz_convert("UTC").timestamp())


def workdays(start: str, end: str) -> list[str]:
    out = []
    for d in pd.date_range(start, end, freq="D"):
        if d.weekday() < 5 and (d.month, d.day) not in ((12, 25), (1, 1)):
            out.append(d.strftime("%Y-%m-%d"))
    return out


def frame(days: list[str], closes) -> pd.DataFrame:
    c = np.asarray(closes, float)
    return pd.DataFrame({"ts": [london_midnight(d) for d in days], "open": c * 0.999, "high": c * 1.002,
                         "low": c * 0.997, "close": c})


def synthetic_raw(codes: list[str], start: str = "2004-01-01", end: str = "2026-11-10", seed: int = 1,
                  drift: dict[str, float] | None = None, vol: float = 0.005) -> dict[str, pd.DataFrame]:
    """Błądzenie losowe kursów (dzienna zmienność `vol`), `drift` = roczny dryf logarytmu kursu dla wybranych walut."""
    rng = np.random.default_rng(seed)
    days = workdays(start, end)
    out = {}
    for i, c in enumerate(codes):
        mu = (drift or {}).get(c, 0.0) / 260
        r = rng.normal(mu, vol, len(days))
        out[c] = frame(days, (1.0 + i * 0.37) * np.exp(np.cumsum(r)))
    return out


def synthetic_ready(codes: list[str], **kw) -> dict[str, pd.DataFrame]:
    from ia5.rev_data import clean_pln

    return {c: clean_pln(df)[0] for c, df in synthetic_raw(codes, **kw).items()}
