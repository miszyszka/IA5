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
    tf = m.get("timeframe", "H1")
    spreads = ", ".join(f"{p} {c.spread_pips:g}" for p, c in PAIRS.items())
    vd = v.get("verdict", {})

    parts = [
        f"# Raport strategii: {m['name']}",
        f"Run `{m['run_id']}` · silnik {m['engine_version']} · kod `{m['code_hash']}` · dane `{m['data_hash']}`",
        f"## Werdykt: {VERDICT.get(vd.get('color'), '—')} — {vd.get('note', '')}",
        _table(pd.DataFrame([{"test": c["test"], "wynik": "nie dotyczy" if c.get("na") else "✔" if c["ok"] else "✘",
                              "wartość": _f(c["value"]) if isinstance(c["value"], (int, float)) else "—"}
                             for c in vd.get("checks", [])])) if vd.get("checks") else "",
        "## Hipoteza", m.get("hypothesis") or "_Brak hipotezy — spisz ją przed liczeniem._",
        "## Dane i model wykonania",
        f"- Pary: {', '.join(m['pairs'])}; świece {tf} od {_d(m['data_from'])} do {_d(m['data_to'])}; źródło: {m['data_source']}"
        + ("; tło D1 (świece dzienne, cała historia Yahoo) w signals() — D-058" if m.get("d1_background") else "") + ".",
        f"- In-sample do {_d(m['oos_cutoff'])}, out-of-sample (ostatnie 25%) od tej daty. Ranking i wybór wariantu tylko po IS.",
        ("- Świece dzienne (D-058): sygnał na zamknięciu dnia (północ w Londynie), wejście na open następnego dnia; okno B11 nie dotyczy; "
         if tf == "D1" else
         "- Wejście na open świecy po sygnale, o dowolnej godzinie (strategia wyłączyła okno handlu, HOURS = False, D-034); "
         if m.get("hours") == "bez okna" else
         "- Wejście na open świecy po sygnale, tylko w oknie handlu 07:00–17:00 czasu polskiego (B11 — najniższe spready); ")
        + "wyjście na dowolnej świecy, także po nocy i weekendzie (D-032). TP i SL w tej samej świecy: "
        + f"przyjęty SL (pesymistycznie — świece {tf} nie mówią, co padło pierwsze; transakcja z flagą `ambiguous`, B5)"
        + (" — na świecach dziennych ten pesymizm jest większy niż na H1: ciasne TP/SL w ATR dziennym często mieszczą się "
           "w jednej świecy." if tf == "D1" else "") + ".",
        f"- Spread raz na transakcję (pips): {spreads}. Swapy pominięte (O5) — liczba nocy i stres „koszt nocy” w walidacji (D-054).",
        (f"- Dokładanie (D-034): do {m['pyramid']} pozycji naraz w parze, tylko w jednym kierunku; każda pozycja ma własne "
         "TP i limit czasu, wyjście wskaźnikowe zamyka wszystkie naraz. Waga pozycji (|sygnał|) mnoży depozyt w symulacji "
         "kapitału; pipsy, R, ranking, DSR, PBO i benchmark losowy liczone są na pozycję, bez wag."
         if m.get("pyramid", 1) > 1 else "- Jedna pozycja na parę naraz (B8)."),
        _clean_line(m),
        f"- Kapitał {START_CAPITAL:,.0f} USD, dźwignia {LEVERAGE}:1, depozyt na pozycję: "
        + ", ".join(f"{x:g}%" for x in m["sizing"]) + "; suma depozytów ≤ 100% kapitału.",
        "## Skala przeszukiwania",
        f"- **Przetestowane warianty: {n_var}** ({len(m['params'])} wejścia × {m['n_exits']} wyjść).",
        f"- Pominięte sygnały, średnio na wariant: {sk['B8'] / n_var:,.0f} (limit otwartych pozycji w parze), "
        f"{sk['brak_danych'] / n_var:,.1f} (brak danych do wyjścia); {sk.get('rozgrzewka', 0)} wejść w rozgrzewce ATR, "
        f"{sk.get('poza_godzinami', 0)} sygnałów poza oknem 07:00–17:00 czasu polskiego (B11), "
        f"anulowane transakcje, średnio na wariant: {sk.get('luka_danych', 0) / n_var:,.1f} (przerwa w dostępie do danych), "
        f"{sk.get('swieca_uzupelniona', 0) / n_var:,.1f} (sygnał, wejście lub wyjście na świecy uzupełnionej) — D-032.",
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
                            "obsunięcie z otwartymi (MAE) %": _f(e.get("max_dd_mae_pct"), 1),
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
            + " pips/transakcję.",
            f"- TP i SL w tej samej świecy bez rozstrzygnięcia: {_f(v['ambiguous_pct'])}% transakcji.",
            _swap_line(v.get("swap") or {}),
        ]
    fw = v.get("forward")
    if fw:
        parts += ["## Forward test od zamrożenia (W4, D-056)", _forward_lines(fw, v)]
    parts += [
        "## Znane ograniczenia",
        ("- Dane: świece dzienne Yahoo (D-058) — historia od ok. 2003; stara historia Yahoo ma pojedyncze brakujące dni i świece "
         "płaskie (odrzucone w warstwie czyszczenia). Yahoo nie podaje bid/ask ani wolumenu."
         if tf == "D1" else
         "- Dane: świece H1 Yahoo (jedno źródło, D-039) — historia od ok. 2 lat wstecz i rośnie; krótka historia = mało transakcji "
         "w OOS, a wyniki są wrażliwe na jeden reżim rynku. Yahoo nie podaje bid/ask ani wolumenu."),
        f"- Brak swapów. Spread stały z tabeli. TP i SL w tej samej świecy {tf} — przyjmowany SL (brak danych wewnątrz świecy).",
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


def _forward_lines(fw: dict, v: dict) -> str:
    """D-056: wynik zamrożonego wariantu od daty zamrożenia wobec oczekiwania z backtestu sprzed niej."""
    head = (f"- Zamrożona {_d(fw['since'])}; oceniany wariant: {v.get('best_exit')}"
            f"{' (zamrożony, nie ranking)' if v.get('pinned_variant') else ''}; oczekiwanie sprzed zamrożenia: "
            f"{_f(fw.get('expected_pips'))} pips / {_f(fw.get('expected_r'))} R na transakcję ({fw.get('pre_trades')} transakcji).")
    if not fw.get("trades"):
        return head + "\n- Jeszcze żadnej transakcji od zamrożenia."
    bs = fw.get("bootstrap") or {}
    return "\n".join([
        head,
        f"- **Forward: {fw['trades']} transakcji, śr. {_f(fw.get('mean_pips'))} pips ({_f(fw.get('mean_r'))} R), "
        f"suma {_f(fw.get('sum_pips'), 0)} pips, win {_f(100 * fw.get('win_rate', 0), 0)}%, t = {_f(fw.get('t_stat'))}; "
        f"bootstrap 95% [{_f(bs.get('low'))}; {_f(bs.get('high'))}].**",
        f"- Odchylenie od oczekiwania: z = {_f(fw.get('z_vs_expected'))} (|z| ≥ 2 = forward nie wygląda jak backtest; "
        f"przy małym n liczba ta jest głównie szumem — potrzeba setek transakcji, żeby odróżnić +3 pipsy od zera).",
    ])


def _swap_line(sw: dict) -> str:
    """D-054: ile nocy trzymano pozycje i co zostaje z wyniku, gdyby każda noc kosztowała 0,5 / 1 pips."""
    if not sw:
        return ""
    return (f"- **Noce (swap pominięty, O5)**: średnio {_f(sw.get('nights_mean'), 1)} nocy na transakcję, "
            f"{_f(sw.get('overnight_pct'), 0)}% transakcji przez 21:00 UTC; wynik netto przy koszcie nocy "
            f"0,5 pipsa: {_f(sw.get('x0_5'))}, 1 pips: {_f(sw.get('x1'))} pips/transakcję.")


def _clean_line(m: dict) -> str:
    """D8: na jakich danych liczono — świece odrzucone, uzupełnione i przerwy w danych."""
    dc = m.get("data_clean") or {}
    if not dc:
        return "- Dane bez warstwy czyszczenia (brak informacji o lukach)."
    parts = []
    for p, d in dc.items():
        parts.append(f"{p}: odrzucone {d.get('rejected', 0)}, uzupełnione {d.get('filled', 0)} (luki ≤ 3 h), "
                     f"{d.get('gaps', 0)} przerw w danych ({d.get('gap_hours', 0)} h)")
    return ("- Świece H1 Yahoo po warstwie czyszczenia (D8, D-039): " + "; ".join(parts)
            + ". Transakcja nachodząca na przerwę w danych albo na świecę uzupełnioną jest anulowana; "
            "weekendy, święta i godziny, których brakuje we wszystkich parach, nie są przerwą (B12).")
