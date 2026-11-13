"""Ścieżki rundy D1: dane robocze w research/d1/data/ (poza repo), wspólne funkcje z research/rynek/lib.py."""
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"          # d1raw/ (candles_d1 z gałęzi data), h1raw/ ({PARA}_{ROK}.parquet), h1_ready/, d1_v2/, d1_ej/, out/, results/
(DATA / "out").mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE.parent / "rynek"))
