"""Strategia DEMO na przykładowych danych EUR/USD H1 (kwiecień 2017 – luty 2018) z pakietu backtesting.py.

To jedyne prawdziwe świece FX dostępne w sesji Claude (Dukascopy, Yahoo i Firestore są tam niedostępne).
Wynik trafia na gałąź `data` jako results/demo-sma200-rsi/ i jest oznaczony jako DEMO. Usuwa się go
z dashboardu jak każdą inną strategię.
"""
import sys
from pathlib import Path

import pandas as pd
from backtesting.test import EURUSD

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runner"))
from ia5.backtest import run_file  # noqa: E402

CODE = '''HYPOTHESIS = """Gdy długoterminowy trend jest wzrostowy (SMA200 rośnie), głębokie krótkoterminowe
wyprzedanie (RSI14 spada poniżej progu) jest chwilowe i cena wraca w górę."""

PARAMS = {
    "rsi_level": [30, 35, 40],   # „RSI spadło poniżej X" — każdy próg to osobny wariant wejścia
    "slope_bars": [5, 20],       # „SMA200 rosnąca" = SMA200 dziś > SMA200 sprzed N świec
}

def signals(df, p, ind):
    sma200 = ind.sma(df.close, 200)
    rsi = ind.rsi(df.close, 14)
    rising = sma200 > sma200.shift(p["slope_bars"])        # interpretacja „rosnąca"
    crossed = ind.cross_below(rsi, p["rsi_level"])          # przecięcie w dół, nie sam stan „poniżej"
    return (rising & crossed).astype("int8")                # +1 = long, tylko longi
'''

out_root = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ia5-demo")
h1_dir = out_root / "h1"
h1_dir.mkdir(parents=True, exist_ok=True)
df = pd.DataFrame({"ts": ((EURUSD.index - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")).astype("int64"),
                   "open": EURUSD.Open.to_numpy(), "high": EURUSD.High.to_numpy(),
                   "low": EURUSD.Low.to_numpy(), "close": EURUSD.Close.to_numpy()})
df.to_parquet(h1_dir / "EURUSD.parquet", index=False)
out = run_file(CODE, "DEMO · SMA200 rośnie + RSI poniżej progu", h1_dir, out_root / "results",
               source="DEMO: przykładowe świece EUR/USD H1 2017–2018 z pakietu backtesting.py (nie Twoja baza)",
               full_candles=True, strategy_id="demo-sma200-rsi", extra={"demo": True})
print(out)
