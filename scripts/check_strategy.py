"""Kontrola kodu strategii BEZ danych Michała (sesja Claude, CI): syntetyczne 8 par + przykładowy EUR/USD.

Użycie:  python scripts/check_strategy.py strategia.py
Kod wyjścia 0 = OK, 1 = błąd kontraktu / look-ahead / brak sygnałów.
Na Macu z prawdziwymi danymi: `ia5 check strategia.py`.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runner"))
from ia5.check import check_code_on, format_result, synthetic_h1  # noqa: E402


def main() -> int:
    code = Path(sys.argv[1]).read_text(encoding="utf-8")
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        res = check_code_on(code, synthetic_h1(Path(tmp) / "syn"))
        print(format_result(res, "syntetyczne 8 par × 6000 świec H1"))
        ok &= res["ok"]
        try:
            import pandas as pd
            from backtesting.test import EURUSD

            d = Path(tmp) / "eurusd"
            d.mkdir()
            pd.DataFrame({"ts": ((EURUSD.index - pd.Timestamp("1970-01-01")) // pd.Timedelta("1s")).astype("int64"),
                          "open": EURUSD.Open.to_numpy(), "high": EURUSD.High.to_numpy(),
                          "low": EURUSD.Low.to_numpy(), "close": EURUSD.Close.to_numpy()}).to_parquet(d / "EURUSD.parquet", index=False)
            res2 = check_code_on(code, d)
            print()
            print(format_result(res2, "prawdziwy EUR/USD H1 2017–2018 (przykład z backtesting.py)"))
            ok &= not res2["errors"] or all("żadnych sygnałów" in e for e in res2["errors"])
        except ImportError:
            pass
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
