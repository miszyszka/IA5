"""REV (D-063): dane przykładowe dla zakładki REV (test w przeglądarce) — syntetyczne kursy, badanie, 6 tygodni portfela.

Użycie: python scripts/rev_fixture.py tests/web/fixtures/rev
Kursy są zmyślone (błądzenie losowe) — to tylko układ strony, nie wynik.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runner"), str(ROOT / "tests")]

from ia5 import rev_live, rev_research  # noqa: E402
from ia5.daily import close_ts  # noqa: E402
from ia5.rev_data import clean_pln  # noqa: E402
from rev_fixtures import synthetic_raw  # noqa: E402

CODES = ["AUD", "CAD", "CHF", "CZK", "DKK", "EUR", "GBP", "HKD", "HUF", "JPY", "MXN", "NOK", "NZD", "SEK", "TRY", "USD", "ZAR"]


def main(out: Path) -> None:
    raw = synthetic_raw(CODES, start="2004-01-01", end="2026-11-10", seed=12, drift={"TRY": -0.25, "CHF": 0.02})
    research_at = int(pd.Timestamp("2026-09-30 12:00", tz="UTC").timestamp())
    now = int(pd.Timestamp("2026-11-11 10:00", tz="UTC").timestamp())

    def ready(at: int):
        r, i = {}, {}
        for c, df in raw.items():
            r[c], i[c] = clean_pln(df[close_ts(df["ts"].to_numpy("int64")) <= at])
        return r, i

    r0, _ = ready(research_at)
    rejected = {"QAR": "historia od 2016-03-01 — krótsza niż 10 lat", "SAR": "ostatni kurs 2026-10-02 — Yahoo przestało notować"}
    res = rev_research.run_research(r0, CODES, None, research_at, paths=50, rejected=rejected)
    res["oos_openings"] = 1
    r1, i1 = ready(now)
    st = rev_live.live_step(None, res, r1, now, i1)
    st["source"] = "actions"
    out.mkdir(parents=True, exist_ok=True)
    (out / "research.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")
    (out / "state.json").write_text(json.dumps(st, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    (out / "report.md").write_text(rev_research.report_md(res), encoding="utf-8")
    print(f"{out}: zwycięzca {res['winner']}, werdykt {res['verdict']['color']}, przewalutowań {len(st['rebalances'])}, "
          f"kapitał {st['today']['total']:.2f} zł")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "tests" / "web" / "fixtures" / "rev"))
