"""Raport dla Claude (CLAUDE.md 10.6). Same liczby w tabelach markdown, bez obrazków."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from .config import LEVERAGE, PAIRS, START_CAPITAL

VERDICT = {"green": "🟢 ZIELONY", "yellow": "🟡 ŻÓŁTY", "red": "🔴 CZERWONY"}


def _d(ts) -> str:
    return datetime.fromtimestamp(int(ts), UTC).strftime("%Y-%m-%d")


def _f(x, nd=2) -> str:
    if x is None:
        return "—"
    x = float(x)
    if np.isnan(x):
        return "—"
    if np.isinf(x):
        return "∞"
    return f"{x:,.{nd}f}".replace(",", " ")


def _table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def _params(p) -> str:
    return ", ".join(f"{k}={v}" for k, v in (p or {}).items()) or "—"


def write_report(out: Path, m: dict, variants: pd.DataFrame, trades: pd.DataFrame, v: dict, code: str) -> None:
    ranked = variants.dropna(subset=["rank_is"]).sort_values("rank_is").head(10)
    top = pd.DataFrame({
        "#": ranked["rank_is"].astype(int), "wyjście": ranked["exit"], "parametry": ranked["params"].map(_params),
        "IS trans.": ranked["is_trades"].map(lambda x: _f(x, 0)), "IS śr. R": ranked["is_exp_r"].map(_f),
        "IS śr. pips": ranked["is_exp_pips"].map(_f), "IS win %": ranked["is_win_rate"].map(lambda x: _f(100 * x, 1)),
        "OOS trans.": ranked["oos_trades"].map(lambda x: _f(x, 0)), "OOS śr. R": ranked["oos_exp_r"].map(_f),
        "OOS śr. pips": ranked["oos_exp_pips"].map(_f),
    }) if len(ranked) else pd.DataFrame()
    n_var = m["n_variants"]
    sk = m["skipped"]
    spreads = ", ".join(f"{p} {c.spread_pips:g}" for p, c in PAIRS.items())
    vd = v.get("verdict", {})

    parts = [
        f"# Raport strategii: {m['name']}",
        f"Run `{m['run_id']}` · silnik {m['engine_version']} · kod `{m['code_hash']}` · dane `{m['data_hash']}`",
        f"## Werdykt: {VERDICT.get(vd.get('color'), '—')} — {vd.get('note', '')}",
        _table(pd.DataFrame([{"test": c["test"], "wynik": "✔" if c["ok"] else "✘",
                              "wartość": _f(c["value"]) if isinstance(c["value"], (int, float)) else "—"}
                             for c in vd.get("checks", [])])) if vd.get("checks") else "",
        "## Hipoteza", m.get("hypothesis") or "_Brak hipotezy — spisz ją przed liczeniem._",
        "## Dane i model wykonania",
        f"- Pary: {', '.join(m['pairs'])}; świece H1 od {_d(m['data_from'])} do {_d(m['data_to'])}; źródło: {m['data_source']}.",
        f"- In-sample do {_d(m['oos_cutoff'])}, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.",
        "- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); "
        "zamknięcie najpóźniej o 23:00 czasu polskiego (powód `23:00`). TP i SL w tej samej świecy: "
        + ("rozstrzygane na M1, w tej samej minucie — SL." if m["m1_resolver"] else "przyjęty SL (brak danych M1)."),
        f"- Spread raz na transakcję (pips): {spreads}. Swapy pominięte.",
        _clean_line(m),
        f"- Kapitał {START_CAPITAL:,.0f} USD, dźwignia {LEVERAGE}:1, depozyt na pozycję: "
        + ", ".join(f"{x:g}%" for x in m["sizing"]) + "; suma depozytów ≤ 100% kapitału.",
        "## Skala przeszukiwania",
        f"- **Przetestowane warianty: {n_var}** ({len(m['params'])} wejścia × {m['n_exits']} wyjść).",
        f"- Pominięte sygnały, średnio na wariant: {sk['B8'] / n_var:,.0f} (otwarta pozycja w parze), "
        f"{sk['brak_danych'] / n_var:,.1f} (brak danych do wyjścia); {sk.get('rozgrzewka', 0)} wejść w rozgrzewce ATR, "
        f"{sk.get('poza_godzinami', 0)} sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), "
        f"{sk.get('luka_danych', 0) / n_var:,.1f} transakcji anulowanych przez lukę w danych lub świecę uzupełnioną (D-031).",
        "## Top 10 wariantów (ranking po IS, min. 30 transakcji IS)",
        _table(top) if len(top) else "_Żaden wariant nie ma 30 transakcji w IS._",
    ]
    if "best_variant_id" in v:
        bt = trades[trades["variant_id"] == v["best_variant_id"]].copy()
        bt["rok"] = pd.to_datetime(bt["exit_ts"], unit="s", utc=True).dt.year
        agg = {"transakcje": ("pips_net", "size"), "śr. pips": ("pips_net", "mean"), "suma pips": ("pips_net", "sum"),
               "win %": ("pips_net", lambda x: 100 * (x > 0).mean())}
        tabs = []
        for key, label in (("pair", "para"), ("rok", "rok"), ("sample", "próba")):
            t = bt.groupby(key).agg(**agg).reset_index().rename(columns={key: label})
            for c in ("śr. pips", "suma pips", "win %"):
                t[c] = t[c].map(lambda x: _f(x, 1))
            tabs.append(t)
        b = v["benchmark"]
        eq = pd.DataFrame([{"depozyt": f"{k}%", "kapitał końcowy": _f(e.get("final"), 0), "zwrot %": _f(e.get("return_pct"), 1),
                            "CAGR %": _f(e.get("cagr_pct"), 1), "max obsunięcie %": _f(e.get("max_dd_pct"), 1),
                            "Sharpe": _f(e.get("sharpe")), "pominięte (depozyt)": e.get("skipped_margin", 0)}
                           for k, e in v["equity"].items()])
        wf = v["walk_forward"]
        parts += [
            f"## Najlepszy wariant IS: {v['best_exit']} ({_params(v['best_params'])})",
            "### Według pary", _table(tabs[0]), "### Według roku", _table(tabs[1]), "### IS i OOS", _table(tabs[2]),
            "### Kapitał", _table(eq),
            "## Walidacja",
            f"- **Benchmark losowych wejść** ({b.get('sims', 0)} losowań, te same pary, kierunki i wyjście): "
            f"wynik {_f(b.get('actual_mean_pips'))} pips/transakcję, percentyl **{_f(b.get('percentile'), 1)}** "
            f"(losowe: 5%={_f(b.get('p5'))}, mediana={_f(b.get('p50'))}, 95%={_f(b.get('p95'))}).",
            f"- **Deflated Sharpe Ratio**: {_f(v['dsr'].get('dsr'), 3)} (Sharpe na transakcję {_f(v['dsr'].get('sharpe'), 3)}, "
            f"próg przy {v['dsr'].get('trials')} próbach {_f(v['dsr'].get('sharpe0'), 3)}).",
            f"- **PBO** (CSCV, {v['pbo'].get('blocks', '—')} bloków, {v['pbo'].get('variants', 0)} wariantów): "
            f"{_f(v['pbo'].get('pbo'), 3)} — szansa, że najlepszy wariant IS wypada poniżej mediany poza próbą.",
            f"- **Walk-forward** (okna kotwiczone, wybór najlepszego wariantu przed każdym oknem): "
            f"{wf['trades']} transakcji, śr. {_f(wf['mean_pips'])} pips, {_f(wf['mean_r'])} R.",
            f"- **Bootstrap 95%** średnich pipsów: całość [{_f(v['bootstrap']['all']['low'])}; {_f(v['bootstrap']['all']['high'])}], "
            f"OOS [{_f(v['bootstrap']['oos']['low'])}; {_f(v['bootstrap']['oos']['high'])}].",
            f"- **Spread**: ×1 {_f(v['spread']['x1'])}, ×1,5 {_f(v['spread']['x1_5'])}, ×2 {_f(v['spread']['x2'])}"
            + (f", faktyczny {_f(v['spread']['real'])}" if "real" in v["spread"] else "") + " pips/transakcję.",
            f"- TP i SL w tej samej świecy bez rozstrzygnięcia: {_f(v['ambiguous_pct'])}% transakcji.",
        ]
    parts += [
        "## Znane ograniczenia",
        "- Brak swapów. Spread stały z tabeli. Przy nierozstrzygniętej kolejności TP/SL przyjmowany SL.",
        "- Kapitał: zwrot liczony na nominale w walucie kwotowanej (dla EUR/GBP, EUR/JPY, USD/JPY, USD/CHF, USD/CAD "
        "przybliżenie — pomija zmianę kursu przeliczenia w trakcie transakcji).",
        "- Benchmark losowy nie stosuje reguły jednej pozycji na parę.",
        "## Kod strategii", "```python", code.strip(), "```",
        "## Pytania do recenzenta",
        "1. Czy OOS i walk-forward potwierdzają IS, czy najlepszy wariant to efekt przeszukania?",
        "2. Czy sąsiednie warianty (podobne TP/SL) dają podobny wynik — płaskowyż czy pojedynczy pik?",
        "3. Czy wynik nie opiera się na jednej parze lub jednym roku?",
        "4. Co w kodzie wejścia może być dopasowane do historii?",
    ]
    (out / "report.md").write_text("\n\n".join(p for p in parts if p) + "\n", encoding="utf-8")


def _clean_line(m: dict) -> str:
    """D-031: na jakich danych liczono — zatwierdzone miesiące, uzupełnione świece, długie luki."""
    dc = m.get("data_clean") or {}
    if not dc:
        return "- Dane bez warstwy czyszczenia (brak informacji o lukach)."
    parts = []
    for p, d in dc.items():
        months = f"{d['months']}/{d['months_total']} mies. zatwierdzonych, " if d.get("months") is not None else ""
        parts.append(f"{p}: {months}{d.get('filled', 0)} świec uzupełnionych (luki ≤ 3 h), "
                     f"{d.get('gaps', 0)} długich luk ({d.get('gap_hours', 0)} h)")
    return ("- Dane tylko z zatwierdzonych miesięcy (D-031): " + "; ".join(parts)
            + ". Transakcja nachodząca na długą lukę albo na świecę uzupełnioną jest anulowana.")
