"""Parametry rynku — jedyne źródło prawdy (CLAUDE.md, sekcja 2)."""
from contextlib import contextmanager
from dataclasses import dataclass

LEVERAGE = 30  # B4, D-024: zawsze 30:1
ACCOUNT_CCY = "USD"
START_CAPITAL = 10_000.0
DEFAULT_SIZING = (5, 10, 15, 20, 30)  # % kapitału jako depozyt (B4)
DEFAULT_RISK_SIZING = (0.25, 0.5, 1, 2)  # D-075: % kapitału ryzykowany do SL, gdy strategia ustawi SIZING_MODE = "risk"
OOS_FRACTION = 0.25  # W1
TRADING_TZ = "Europe/Warsaw"   # B11, D-028: handel tylko 07:00–17:00 czasu polskiego (najniższe spready)
TRADING_HOURS = (7, 17)        # wejście na open świecy otwartej o 07:00 … 16:00 czasu polskiego


@dataclass(frozen=True)
class Pair:
    name: str
    yahoo: str
    pip: float
    spread_pips: float
    quote_ccy: str


PAIRS = {
    p.name: p
    for p in (
        Pair("EURUSD", "EURUSD=X", 0.0001, 0.9, "USD"),
        Pair("USDJPY", "JPY=X", 0.01, 1.4, "JPY"),
        Pair("GBPUSD", "GBPUSD=X", 0.0001, 1.5, "USD"),
        Pair("EURGBP", "EURGBP=X", 0.0001, 1.7, "GBP"),
        Pair("AUDUSD", "AUDUSD=X", 0.0001, 1.7, "USD"),
        Pair("USDCHF", "CHF=X", 0.0001, 1.9, "CHF"),
        Pair("USDCAD", "CAD=X", 0.0001, 2.0, "CAD"),
        Pair("EURJPY", "EURJPY=X", 0.01, 2.1, "JPY"),
    )
}


# D-038: strategie liczymy na wszystkich parach; para bez danych do liczenia jest pomijana (ready.build).
COMPUTE_PAIRS = tuple(PAIRS)


# D-072: instrumenty spoza tabeli par (świece dzienne spółek w pilotażowym OOS na akcjach) — rejestrowane tylko na czas
# jednego liczenia; ceny w jednostkach ceny (pip = 1), koszt liczony osobno w procentach (stk_oos). Pary FX bez zmian.
_EXTRA: dict[str, Pair] = {}


def instrument(name: str) -> Pair:
    """Para z tabeli (sekcja 2) albo instrument zarejestrowany przez extra_instruments()."""
    p = PAIRS.get(name)
    if p is None:
        p = _EXTRA.get(name)
    if p is None:
        raise KeyError(name)
    return p


@contextmanager
def extra_instruments(names, pip: float = 1.0, spread_pips: float = 0.0):
    """Rejestruje instrumenty (np. spółki) na czas bloku with; nazwy z tabeli par są odrzucane."""
    added = []
    for n in names:
        if n in PAIRS:
            raise ValueError(f"{n} jest parą FX — nie można go nadpisać")
        if n not in _EXTRA:
            _EXTRA[n] = Pair(n, n, pip, spread_pips, "USD")
            added.append(n)
    try:
        yield
    finally:
        for n in added:
            _EXTRA.pop(n, None)


# D-075: swap (rolowanie) w pipsach ZA JEDNĄ NOC przez 21:00 UTC: (long, short). Ujemny = płacimy, dodatni = dostajemy.
# Weekend liczony jako 3 noce (session.nights). Domyślnie 0 — decyzja O5 dalej otwarta: tabelę wypełnia Michał stawkami
# swojego brokera (raz w miesiącu), każda zmiana = podbicie SWAP_VERSION i wpis w DECISIONS. Walidacja nadal pokazuje
# stres 0,5 / 1 pips za noc (D-054) — NA DODATEK do tej tabeli.
SWAP_VERSION = "0 (O5: swapy = 0, tabela niewypełniona)"
SWAP_PIPS: dict[str, tuple[float, float]] = {p: (0.0, 0.0) for p in PAIRS}


def swap_cost(pairs, dirs, nights):
    """Swap w pipsach dla każdej transakcji: noce × stawka (long gdy dir > 0, short gdy dir < 0); para spoza tabeli = 0."""
    import numpy as np

    pairs, dirs = np.asarray(pairs), np.asarray(dirs, float)
    n = np.nan_to_num(np.asarray(nights, float))
    lo = np.array([SWAP_PIPS.get(str(q), (0.0, 0.0))[0] for q in pairs], float)
    sh = np.array([SWAP_PIPS.get(str(q), (0.0, 0.0))[1] for q in pairs], float)
    return np.where(dirs > 0, lo, sh) * n


def spread_price(pair: str) -> float:
    """Spread w jednostkach ceny (B3)."""
    p = PAIRS[pair]
    return p.spread_pips * p.pip
