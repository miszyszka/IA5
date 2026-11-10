"""Ścieżki lokalne i konfiguracja (~/.ia5, poza repo — S3)."""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("IA5_HOME", Path.home() / ".ia5"))
DATA = HOME / "data"
YAHOO = DATA / "yahoo"      # D-039: kopia świec H1 Yahoo z Firestore — jedyne źródło cen
READY = DATA / "h1_ready"   # H1 Yahoo po warstwie czyszczenia (clean.py) — jedyne wejście silnika i skanera
YAHOO_D1 = DATA / "yahoo_d1"   # D-053: kopia świec dziennych (D1) Yahoo z Firestore — przechowywana, silnik jej nie używa
RESULTS = HOME / "results"
SCANS = HOME / "scans"
SEARCHES = HOME / "searches"   # D-044: głębokie poszukiwanie (ia5 search)
FOREST = HOME / "forest"       # D-048: las inwestorów, mapy, dziennik (current/, public/, archive/)
DATA_ALLOWED = ("yahoo", "h1_ready", "yahoo_d1")   # D-041, D-053: lokalnie tylko świece Yahoo (H1, D1) i dane do liczenia
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
