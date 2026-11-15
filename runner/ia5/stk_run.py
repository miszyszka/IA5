"""Stocks (D-071) — przebiegi na Macu i w GitHub Actions: dane spółek, badanie na żądanie ze strony, portfel na żywo.

Protokół (jedyna droga komunikacji: Firestore `stocks/config` + gałąź `data`):
- strona (zalogowany właściciel) zapisuje stocks/config: tickers [{t, w}], capital, band, status="do_policzenia";
- Mac (nasłuch): status="liczy_sie" → brakujące spółki? status="czeka_na_dane" (Apps Script pobiera nowe spółki co ≤ 5 min)
  → badanie → publikacja stocks/research.json, report.md, config.json → status="policzony", result={at, verdict, winner};
  błąd → status="blad", error;
- portfel na żywo (stocks/state.json): GitHub Actions co godzinę (`ia5 live`), Mac zapasowo i od razu po badaniu.
Bez dokumentu stocks/config Mac liczy listę startową (równe udziały) i zapisuje ją jako konfigurację.
"""
from __future__ import annotations

import json
import time

from .stk_config import DEFAULT_BAND, DEFAULT_CAPITAL, DEFAULT_TICKERS, RANDOM_PATHS, STK_VERSION, TZ
from .store import DATA_REPO, HOME, STK_READY, STOCKS, YAHOO_STK

WAIT_DATA_S = 20 * 60     # tyle czekamy na nowe spółki z Apps Script
WAIT_POLL_S = 60


def default_config() -> dict:
    w = round(100 / len(DEFAULT_TICKERS), 4)
    return {"tickers": [{"t": t, "w": w} for t in DEFAULT_TICKERS], "capital": DEFAULT_CAPITAL, "band": DEFAULT_BAND}


def _read(path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def tickers_wanted(cfg: dict | None) -> list[str]:
    """Spółki do kopii: z konfiguracji (strona), z zamrożonego badania (portfel na żywo), inaczej lista startowa."""
    out = []
    for x in (cfg or {}).get("tickers") or []:
        t = str(x.get("t") if isinstance(x, dict) else x).strip().upper()
        if t and t not in out:
            out.append(t)
    res = _read(DATA_REPO / "stocks" / "research.json")
    for t in (res or {}).get("universe") or []:
        if t not in out:
            out.append(t)
    return out or list(DEFAULT_TICKERS)


def sync(cloud, status: dict, tickers: list[str], log=print) -> dict:
    """Kopia świec spółek z Firestore + warstwa czyszczenia (data/stk_ready/). Zwraca surowe kopie."""
    from .stk_data import build_stk

    if not ((status or {}).get("stk") or {}).get("tickers"):
        local = cloud.load_yahoo_stk(YAHOO_STK, tickers)
        if not local:
            log("  W bazie nie ma jeszcze świec spółek — wklej nowy Code.gs w Apps Script (docs/SETUP.md, „Spółki”); tick pobierze je sam.")
        raw = local
    else:
        log("Kopia świec spółek (Stocks) Yahoo…")
        try:
            raw = cloud.sync_yahoo_stk(YAHOO_STK, status, tickers, log=log)
        except Exception as e:  # noqa: BLE001
            log(f"  Nie udało się pobrać świec spółek z Firestore ({e}) — używam kopii lokalnej.")
            raw = cloud.load_yahoo_stk(YAHOO_STK, tickers)
    if raw:
        build_stk(raw, STK_READY, tz=((status or {}).get("stk") or {}).get("tz") or TZ, log=log)
    return raw


def research_run(ready: dict, cfg: dict, now: int, rejected: dict, log=print, publish_it: bool = True,
                 paths: int | None = None) -> dict:
    from . import publish, stk_research

    res = stk_research.run_research(ready, cfg, now, paths=paths or RANDOM_PATHS, log=log, rejected=rejected)
    run_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime(now))
    res["oos_openings"] = stk_research.ledger_add(HOME, res, run_id)
    md = stk_research.report_md(res)
    out = STOCKS / "research" / run_id
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(res, ensure_ascii=False, indent=1, allow_nan=False)
    (out / "research.json").write_text(text, encoding="utf-8")
    (out / "report.md").write_text(md, encoding="utf-8")
    log(f"Stocks: badanie zapisane w {out} ({res['seconds']} s)")
    if publish_it:
        publish.publish_stocks({"research.json": text, "report.md": md,
                                "config.json": json.dumps(res["config"], ensure_ascii=False, indent=1)}, log=log)
    return res


def handle(cloud, state: dict, cfg_doc: dict | None, want_research: bool, source: str, log=print, beat=None,
           cloud_active=None) -> None:
    """Badanie (na żądanie albo gdy go brak / nowa STK_VERSION — tylko Mac) i krok portfela na żywo."""
    from . import publish, stk_live
    from .stk_data import load_stk

    beat = beat or (lambda *a, **k: None)
    now = int(time.time())
    publish.ensure_repo()
    research = _read(DATA_REPO / "stocks" / "research.json")
    fresh = False
    if source == "mac":
        need = want_research or research is None or research.get("stk_version") != STK_VERSION
        if need:
            cfg = cfg_doc if cfg_doc and cfg_doc.get("tickers") else default_config()
            if not cfg_doc:
                cloud.write_stocks_config({**default_config(), "status": "do_policzenia", "requestedAt": now, "updatedBy": "mac"})
            research = _compute(cloud, state, cfg, now, log, beat, wait=want_research) or research
            fresh = research is not None
    if research is None:
        log("Stocks: badania jeszcze nie ma — policzy je Mac (ia5 start).")
        return
    if research.get("stk_version") != STK_VERSION:
        log(f"Stocks: kod w wersji {STK_VERSION}, badanie w {research.get('stk_version')} — portfel czeka na nowe badanie (Mac).")
        return
    if source == "mac" and not fresh and cloud_active and cloud_active(DATA_REPO, now):
        log("Stocks: portfel liczy GitHub Actions — Mac pomija.")
        return
    ready = load_stk(STK_READY, set(research["universe"]))
    prev = _read(DATA_REPO / "stocks" / "state.json")
    st = stk_live.live_step(prev, research, ready, now)
    st["source"] = source
    tot = (st.get("today") or {}).get("total")
    log(f"Stocks: {st['method']['id']} · " + (f"kapitał {tot:,.2f} USD" if tot else "czeka na pierwsze wykonanie")
        + f" · planów {len(st['plans'])}, transakcji {len(st['ledger'])}")
    sha = publish.publish_stocks({"state.json": json.dumps(st, ensure_ascii=False, separators=(",", ":"), allow_nan=False)}, log=log)
    if sha and source == "mac":
        cloud.set_data_sha(sha)


def _compute(cloud, state: dict, cfg: dict, now: int, log, beat, wait: bool = True) -> dict | None:
    """Backtest dla ustawień. wait = czekaj na dane nowych spółek (tylko po „Policz backtest”); bez świec spółek w bazie
    (Apps Script bez nowego Code.gs) — od razu komunikat, bez czekania."""
    from .stk_data import load_stk
    from .stk_research import normalize_config

    cfg = normalize_config(cfg)
    want = [r["t"] for r in cfg["tickers"]]
    job = {"id": "stocks", "name": "Stocks: backtest", "progress": 5, "phase": "dane spółek"}
    state["now"], state["job"] = "computing", job
    beat("computing", job)
    try:
        if not ((cloud.read_status().get("stk") or {}).get("tickers")):
            log("Stocks: w bazie nie ma świec spółek — wklej nowy Code.gs w Apps Script (docs/SETUP.md, „Spółki”).")
            cloud.write_stocks_config({"status": "czeka_na_dane", "waiting": want,
                                       "error": "Brak świec spółek w bazie — wklej nowy Code.gs w Apps Script (docs/SETUP.md, „Spółki”)."})
            return None
        cloud.write_stocks_config({"status": "liczy_sie", "startedAt": now, "error": None, "waiting": []})
        t0 = time.time()
        while True:
            st = cloud.read_status()
            stk = st.get("stk") or {}
            have, rej = set((stk.get("tickers") or {})), dict(stk.get("rejected") or {})
            missing = [t for t in want if t not in have and t not in rej]
            if not missing or not wait or time.time() - t0 > WAIT_DATA_S:
                break
            cloud.write_stocks_config({"status": "czeka_na_dane", "waiting": missing})
            log(f"Stocks: czekam na dane nowych spółek z Apps Script: {', '.join(missing)}")
            job["phase"] = f"czeka na dane: {', '.join(missing)[:40]}"
            beat("computing", job)
            time.sleep(WAIT_POLL_S)
        cloud.write_stocks_config({"status": "liczy_sie", "waiting": []})
        sync(cloud, st, list(dict.fromkeys(want + tickers_wanted(None))), log=log)
        ready = load_stk(STK_READY, set(want))
        job.update({"progress": 30, "phase": "turniej konfiguracji"})
        beat("computing", job)
        res = research_run(ready, cfg, now, rej, log=log)
        cloud.write_stocks_config({"status": "policzony", "error": None, "waiting": [],
                                   "result": {"at": int(time.time()), "verdict": res["verdict"]["color"], "winner": res["winner"],
                                              "label": res["frozen"]["label"], "missing": res["missing"]}})
        return res
    except Exception as e:  # noqa: BLE001 — błąd pokazujemy na stronie
        log(f"Stocks: błąd badania — {type(e).__name__}: {e}")
        cloud.write_stocks_config({"status": "blad", "error": f"{type(e).__name__}: {e}"[:300]})
        return None
    finally:
        state["now"], state["job"] = "idle", None
        beat("idle")
