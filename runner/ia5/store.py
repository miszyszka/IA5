"""Ścieżki lokalne i konfiguracja (~/.ia5, poza repo — S3)."""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("IA5_HOME", Path.home() / ".ia5"))
DATA = HOME / "data"
READY = DATA / "h1_ready"   # D-031: H1 tylko z zatwierdzonych miesięcy, po warstwie czyszczenia — jedyne wejście silnika
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
