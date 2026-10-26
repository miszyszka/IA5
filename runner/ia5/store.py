"""Ścieżki lokalne i konfiguracja (~/.ia5, poza repo — S3)."""
import json
import os
from pathlib import Path

HOME = Path(os.environ.get("IA5_HOME", Path.home() / ".ia5"))
DATA = HOME / "data"
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
