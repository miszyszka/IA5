"""Powiadomienia mailowe inwestorów (D-051): sygnał, otwarcie, zamknięcie przez limit czasu.

Zdarzenia wynikają ze stanu inwestora (`investors.compute`). Dziennik `~/.ia5/mail_sent.json` pilnuje, żeby każde poszło raz.
Pierwszy przebieg inwestora i zdarzenia przy wyłączonym przełączniku są tylko odnotowywane — włączenie nie wysyła historii.
Nieudana wysyłka nie trafia do dziennika, więc ponowi się po następnym liczeniu.
Dane Gmaila leżą poza repo (S3): `~/.ia5/smtp.json` = {"user", "app_password", "to"}.
"""
from __future__ import annotations

import json
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

PL = ZoneInfo("Europe/Warsaw")


def _pl(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).astimezone(PL).strftime("%Y-%m-%d %H:%M")


def _px(x: float | None) -> str:
    if x is None:
        return "brak"
    return f"{x:.3f}" if x > 20 else f"{x:.5f}"


def _pair(p: str) -> str:
    return f"{p[:3]}/{p[3:]}"


def _word(d: int) -> str:
    return "long" if d > 0 else "short"


def events(state: dict) -> list[dict]:
    """Wszystkie zdarzenia widoczne w stanie: {key, subject, body}."""
    name = state.get("name") or state.get("id")
    strat = state.get("strategies") or []
    sname = lambda k: strat[k].get("name") if k < len(strat) else f"#{k + 1}"  # noqa: E731
    out = []

    def add(key, title, lines):
        out.append({"key": key, "subject": f"IA5 · {name} · {title}", "body": "\n".join([f"Inwestor: {name}", *lines]) + "\n"})

    for p in state.get("pending") or []:
        if not p.get("free", True):
            continue
        k, q = p["strategy"], p["pair"]
        add(f"signal|{k}|{q}|{p['signal_ts']}", f"SYGNAŁ {_pair(q)} {_word(p['dir'])}", [
            f"Strategia: {sname(k)}", f"Instrument: {_pair(q)} ({_word(p['dir'])})",
            f"Cena (ostatnie zamknięcie): {_px(p.get('price'))}", f"TP (szacunek): {_px(p.get('tp'))}",
            f"SL (szacunek): {_px(p.get('sl'))}", f"Świeca sygnału: {_pl(p['signal_ts'])} czasu polskiego",
            "Wejście na otwarciu świecy po sygnale; dokładne poziomy przyjdą w mailu o otwarciu."])
    for t in state.get("trades") or []:
        if t.get("margin_usd") is None or t.get("status") not in ("otwarta", "zamknięta"):
            continue
        k, q, e = t["strategy"], t["pair"], t["entry_ts"]
        add(f"open|{k}|{q}|{e}", f"OTWARCIE {_pair(q)} {_word(t['dir'])}", [
            f"Strategia: {sname(k)}", f"Instrument: {_pair(q)} ({_word(t['dir'])})", f"Cena wejścia: {_px(t['entry_px'])}",
            f"TP: {_px(t.get('tp'))}", f"SL: {_px(t.get('sl'))}", f"Czas wejścia: {_pl(e)} czasu polskiego"])
        if t["status"] == "zamknięta" and t.get("reason") == "czas":
            add(f"close|{k}|{q}|{e}", f"ZAMKNIĘCIE (limit czasu) {_pair(q)}", [
                f"Strategia: {sname(k)}", f"Instrument: {_pair(q)} ({_word(t['dir'])})",
                f"Cena wyjścia: {_px(t['exit_px'])}", f"Wynik: {t.get('pips_net'):+.1f} pips, {t.get('pnl_usd') or 0:+.2f} USD",
                f"Czas wyjścia: {_pl(t['exit_ts'])} czasu polskiego"])
    return out


def load_config(path: Path) -> dict | None:
    try:
        c = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not (c.get("user") and c.get("app_password")):
        return None
    return {"user": c["user"], "app_password": str(c["app_password"]).replace(" ", ""), "to": c.get("to") or c["user"]}


def smtp_sender(cfg: dict):
    def send(subject: str, body: str) -> None:
        m = EmailMessage()
        m["From"], m["To"], m["Subject"] = cfg["user"], cfg["to"], subject
        m.set_content(body)
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as s:
            s.login(cfg["user"], cfg["app_password"])
            s.send_message(m)
    return send


def process(iid: str, enabled: bool, state: dict, ledger: dict, send) -> str | None:
    """Wysyła nowe zdarzenia, dopisuje je do `ledger`; zwraca opis błędu albo None. send=None: brak konfiguracji."""
    ev = events(state)
    if iid not in ledger or not enabled:
        ledger[iid] = sorted(set(ledger.get(iid, [])) | {e["key"] for e in ev})
        return None
    done = set(ledger[iid])
    new = [e for e in ev if e["key"] not in done]
    if send is None:
        return "Maile włączone, ale brak ~/.ia5/smtp.json — wiadomości czekają na konfigurację."
    for e in new:
        try:
            send(e["subject"], e["body"])
        except Exception as x:  # noqa: BLE001 — błąd poczty nie może zatrzymać liczenia
            ledger[iid] = sorted(done)
            return f"Nie udało się wysłać maila: {x}"[:300]
        done.add(e["key"])
    ledger[iid] = sorted(done)
    return None


def load_ledger(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_ledger(path: Path, ledger: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(ledger, ensure_ascii=False), encoding="utf-8")
