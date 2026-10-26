"""Raport dla Claude (CLAUDE.md 10.6). Same liczby w tabelach markdown, bez obrazków."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import LEVERAGE, PAIRS


def _d(ts) -> str:
    return datetime.fromtimestamp(int(ts), UTC).strftime("%Y-%m-%d")


def _f(x, nd=2) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "—" if x is None or np.isnan(x) else "∞"
    return f"{x:,.{nd}f}".replace(",", " ")


def _table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def write_report(out: Path, m: dict, variants: pd.DataFrame, res: dict, code: str) -> None:
    o = res["outcomes"]
    ranked = variants.dropna(subset=["rank_is"]).head(10) if "rank_is" in variants else variants.head(0)
    top = pd.DataFrame({
        "#": ranked["rank_is"].astype(int) if len(ranked) else [],
        "wyjście": ranked.get("exit", []),
        "parametry wejścia": ranked["params"].map(lambda p: ", ".join(f"{k}={v}" for k, v in p.items()) or "—")
        if len(ranked) else [],
        "IS transakcje": ranked.get("is_trades", pd.Series(dtype=float)).map(lambda x: _f(x, 0)),
        "IS śr. R": ranked.get("is_exp_r", pd.Series(dtype=float)).map(_f),
        "IS śr. pips": ranked.get("is_exp_pips", pd.Series(dtype=float)).map(_f),
        "IS win %": ranked.get("is_win_rate", pd.Series(dtype=float)).map(lambda x: _f(100 * x, 1)),
        "OOS transakcje": ranked.get("oos_trades", pd.Series(dtype=float)).map(lambda x: _f(x, 0)),
        "OOS śr. R": ranked.get("oos_exp_r", pd.Series(dtype=float)).map(_f),
        "OOS śr. pips": ranked.get("oos_exp_pips", pd.Series(dtype=float)).map(_f),
    })
    best = ranked.iloc[0] if len(ranked) else None
    by_pair = by_year = pd.DataFrame()
    if best is not None and not o.empty:
        b = o[o["variant_id"] == best["variant_id"]].copy()
        b["rok"] = pd.to_datetime(b["exit_ts"], unit="s", utc=True).dt.year
        agg = {"transakcje": ("pips_net", "size"), "śr. pips": ("pips_net", "mean"), "suma pips": ("pips_net", "sum"),
               "win %": ("pips_net", lambda x: 100 * (x > 0).mean())}
        by_pair = b.groupby("pair").agg(**agg).reset_index().rename(columns={"pair": "para"})
        by_year = b.groupby("rok").agg(**agg).reset_index()
        for t in (by_pair, by_year):
            for c in ("śr. pips", "suma pips", "win %"):
                t[c] = t[c].map(lambda x: _f(x, 1))
    n_amb = float(o["ambiguous"].mean() * 100) if not o.empty else 0.0
    spreads = ", ".join(f"{p} {c.spread_pips:g}" for p, c in PAIRS.items())

    parts = [
        f"# Raport strategii: {m['name']}",
        f"Run `{m['run_id']}` · silnik {m['engine_version']} · kod `{m['code_hash']}` · dane `{m['data_hash']}`",
        "## Hipoteza", m.get("hypothesis") or "_Brak hipotezy (ostrzeżenie: spisz ją przed liczeniem)._",
        "## Dane i model wykonania",
        f"- Pary: {', '.join(m['pairs'])}; świece H1 od {_d(m['data_from'])} do {_d(m['data_to'])}; źródło: {m['data_source']}.",
        f"- In-sample do {_d(m['oos_cutoff'])}, out-of-sample (ostatnie 25%) od tej daty. Ranking tylko po IS.",
        "- Wejście na open świecy po sygnale. TP/SL w tej samej świecy: "
        + ("rozstrzygane na M1, a w tej samej minucie — SL." if m["m1_resolver"] else "przyjęty SL (brak danych M1)."),
        f"- Spread odejmowany raz na transakcję (pips): {spreads}. Swapy pominięte. Dźwignia 1:{LEVERAGE}.",
        "## Skala przeszukiwania",
        f"- **Przetestowane warianty: {m['n_variants']}** ({len(m['params'])} wejścia × {m['n_exits']} wyjść). "
        "Najlepszy wariant z tak wielu jest w dużej mierze szczęściarzem — patrz OOS.",
        f"- Pominięte sygnały, średnio na wariant: {m['skipped']['B8'] / m['n_variants']:,.0f} (otwarta pozycja w parze), "
        f"{m['skipped']['brak_danych'] / m['n_variants']:,.1f} (brak danych do wyjścia); "
        f"{m['skipped'].get('rozgrzewka', 0)} wejść w okresie rozgrzewki ATR.",
        f"- Transakcje z niejednoznaczną kolejnością TP/SL: {n_amb:.2f}%.",
        "## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)",
        _table(top) if len(top) else "_Żaden wariant nie ma 30 transakcji w IS._",
    ]
    if best is not None:
        parts += [f"## Najlepszy wariant IS: {best['exit']}", "### Według pary", _table(by_pair),
                  "### Według roku", _table(by_year)]
    parts += [
        "## Walidacja",
        "_Deflated Sharpe, PBO, benchmark losowych wejść, walk-forward i test spreadu — etap E5 (jeszcze nie liczone)._",
        "## Znane ograniczenia",
        "- Brak swapów. Spread stały z tabeli. Pesymistyczne założenie SL przy niejednoznacznej świecy.",
        "- Wyniki w pipsach i R; symulacja kapitału (5–30% depozytu) — etap E5.",
        "## Kod strategii", "```python", code.strip(), "```",
        "## Pytania do recenzenta",
        "1. Czy wynik OOS potwierdza IS, czy najlepszy wariant to efekt przeszukania?",
        "2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?",
        "3. Czy wynik nie opiera się na jednej parze lub jednym roku?",
        "4. Co w kodzie wejścia może być dopasowane do historii?",
    ]
    (out / "report.md").write_text("\n\n".join(parts) + "\n", encoding="utf-8")
