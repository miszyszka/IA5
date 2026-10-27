"""Parametry rynku — jedyne źródło prawdy (CLAUDE.md, sekcja 2)."""
from dataclasses import dataclass

LEVERAGE = 30  # B4, D-024: zawsze 30:1
ACCOUNT_CCY = "USD"
START_CAPITAL = 10_000.0
DEFAULT_SIZING = (5, 10, 15, 20, 30)  # % kapitału jako depozyt (B4)
OOS_FRACTION = 0.25  # W1
TRADING_TZ = "Europe/Warsaw"   # B11, D-028: handel tylko 07:00–17:00 czasu polskiego (najniższe spready)
TRADING_HOURS = (7, 17)        # wejście na open świecy otwartej o 07:00 … 16:00 czasu polskiego


@dataclass(frozen=True)
class Pair:
    name: str
    yahoo: str
    dukascopy: str
    pip: float
    spread_pips: float
    quote_ccy: str


PAIRS = {
    p.name: p
    for p in (
        Pair("EURUSD", "EURUSD=X", "EURUSD", 0.0001, 0.9, "USD"),
        Pair("USDJPY", "JPY=X", "USDJPY", 0.01, 1.4, "JPY"),
        Pair("GBPUSD", "GBPUSD=X", "GBPUSD", 0.0001, 1.5, "USD"),
        Pair("EURGBP", "EURGBP=X", "EURGBP", 0.0001, 1.7, "GBP"),
        Pair("AUDUSD", "AUDUSD=X", "AUDUSD", 0.0001, 1.7, "USD"),
        Pair("USDCHF", "CHF=X", "USDCHF", 0.0001, 1.9, "CHF"),
        Pair("USDCAD", "CAD=X", "USDCAD", 0.0001, 2.0, "CAD"),
        Pair("EURJPY", "EURJPY=X", "EURJPY", 0.01, 2.1, "JPY"),
    )
}


# D-038 (zmiana D8 przez Michała 2026-10-27): strategie liczymy na wszystkich parach, które mają zatwierdzone miesiące;
# para bez zatwierdzonych miesięcy jest pomijana (ready.build). Kolejność = kolejność pobierania (EUR/USD pierwsza).
COMPUTE_PAIRS = tuple(PAIRS)


def spread_price(pair: str) -> float:
    """Spread w jednostkach ceny (B3)."""
    p = PAIRS[pair]
    return p.spread_pips * p.pip
