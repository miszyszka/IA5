"""Ścieżki lokalne i konfiguracja (~/.ia5, poza repo — S3)."""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("IA5_HOME", Path.home() / ".ia5"))
DATA = HOME / "data"
YAHOO = DATA / "yahoo"      # D-039: kopia świec H1 Yahoo z Firestore — jedyne źródło cen
READY = DATA / "h1_ready"   # H1 Yahoo po warstwie czyszczenia (clean.py) — jedyne wejście silnika i skanera
YAHOO_D1 = DATA / "yahoo_d1"   # D-053: kopia świec dziennych (D1) Yahoo z Firestore (surowa)
D1_READY = DATA / "d1_ready"   # D-058: D1 po warstwie czyszczenia (daily.clean_d1) — wejście silnika dla TIMEFRAME = "D1" i tło D1 dla H1
RESULTS = HOME / "results"
SCANS = HOME / "scans"
SEARCHES = HOME / "searches"   # D-044: głębokie poszukiwanie (ia5 search)
FOREST = HOME / "forest"       # D-048: las inwestorów, mapy, dziennik (current/, public/, archive/)
REV = HOME / "rev"             # D-062: badania REV (research/{run}/)
YAHOO_PLN = DATA / "yahoo_pln"   # D-062: kopia kursów złotówkowych D1 Yahoo z Firestore (surowa) — REV
PLN_READY = DATA / "pln_ready"   # D-062: kursy PLN po warstwie REV (rev_data.clean_pln) — wejście REV
DATA_ALLOWED = ("yahoo", "h1_ready", "yahoo_d1", "d1_ready", "yahoo_pln", "pln_ready")   # D-041, D-053, D-058, D-062: tylko dane Yahoo
# D-039: pozostałości po źródle Dukascopy (usuwane przy starcie za zgodą Michała z 2026-10-31)
LEGACY = (DATA / "m1", DATA / "h1", DATA / "h1_scan")
SERVICE_ACCOUNT = HOME / "service-account.json"
CONFIG = HOME / "config.json"
DATA_REPO = HOME / "data-repo"
REPO_URL = "https://github.com/miszyszka/IA5.git"


def config() -> dict:
    """{"owner_uid": "..."} — UID właściciela (S1). Brak pliku = brak liczenia strategii."""
    try:
        return json.loads(CONFIG.read_text())
    except FileNotFoundError:
        return {}
