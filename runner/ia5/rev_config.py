"""REV (D-063) — kapitał w złotówkach rozłożony na przecenione waluty. Stałe projektu: jedno źródło prawdy.

Projekt: docs/superpowers/specs/2026-11-11-rev-design.md; zasady: CLAUDE.md, sekcja „REV (R)”.
Zmiana logiki liczenia = podbicie REV_VERSION; zmiana warstwy czyszczenia = podbicie CLEAN_PLN_VERSION (R6).
"""
from __future__ import annotations

from collections.abc import Iterable

REV_VERSION = "2"   # D-065: nakładki (zawór złotówkowy, hamulec, „nie sprzedawaj na stracie”), wybór po Sharpe w PLN
CLEAN_PLN_VERSION = "1"

# 24 waluty od Michała bez RUB (sankcje, notowania Yahoo stoją) — rzadkie kursy odpadają przy przyjęciu (Apps Script)
CANDIDATES: tuple[str, ...] = (
    "AED", "AUD", "CAD", "CHF", "CZK", "DKK", "EUR", "GBP", "HKD", "HUF", "ILS", "JPY",
    "MXN", "NOK", "NZD", "QAR", "RON", "SAR", "SEK", "SGD", "THB", "TRY", "USD", "ZAR",
)
# R1: sztywny kurs — blok to jeden koszyk trzymany w kotwicy (limit 50% na cały blok)
BLOCS: dict[str, tuple[str, ...]] = {"USD": ("HKD", "AED", "SAR", "QAR"), "EUR": ("DKK",)}
TICKER = "{}PLN=X"
BASE = "PLN"

START_PLN = 10_000.0
CAP = 0.5      # R4: żaden koszyk (waluta, blok, PLN) > 50% kapitału…
PLN_CAP_VALVE = 0.75   # …poza PLN przy włączonym zaworze albo hamulcu (D-065, wybór Michała „B”): wtedy PLN co najmniej i najwyżej 75%
BAND = 0.02    # pasmo bez przewalutowania: zmiana udziału < 2 p.p. — bez transakcji

# R2: przeliczenie we wtorek 08:00 czasu polskiego po zamknięciu poniedziałku; najpóźniej o 20:00 bez spóźnionych świec
DECISION_TZ = "Europe/Warsaw"
DECISION_WEEKDAY = 1   # wtorek (poniedziałek = 0)
DECISION_HOUR = 8
DEADLINE_HOUR = 20
MAX_STALE_WD = 5       # cena tygodnia nie starsza niż 5 dni roboczych

# przyjęcie waluty („rzadki kurs”) — sprawdza Apps Script przy backfillPLN(); tu dla kontroli i dokumentacji
ADMIT_MIN_YEARS = 10
ADMIT_FRESH_WD = 5
ADMIT_FLAT_MAX = 0.05
ADMIT_FLAT_YEARS = 5

# R0: warstwa czyszczenia (tylko zamknięcia)
SPIKE_SIGMA = 10.0
SPIKE_MAD_DAYS = 60
SPIKE_REVERT = 0.8
SCALE_TOL = 0.02

# turniej (R5)
ELIGIBLE_WEEKS = 260
WINDOW_MAX_MISSING = 0.08
MIN_BASKETS = 8
IS_FRACTION = 0.75
SWITCH_EVERY = 13
SWITCH_LOOKBACK = 156
RANDOM_PATHS = 1000
CSCV_BLOCKS = 16
BOOT_BLOCK = 8
VERDICT = {"random_pct": 95.0, "dsr": 0.95, "pbo": 0.3, "red_random_pct": 80.0}

# D-065: nakładki — spisane przed liczeniem (projekt REV §10)
VALVE_WEEKS = (26, 52)   # zawór złotówkowy: indeks walut obcych wobec PLN spadł przez tyle tygodni → PLN 75%
BRAKE_SHORT = 13         # hamulec zmienności: odchylenie tygodniowych zmian indeksu z 13 tygodni…
BRAKE_LONG = 260         # …wobec mediany tego odchylenia z 260 tygodni…
BRAKE_MULT = 1.5         # …większe o 50% → PLN 75%
OVERLAYS = ("", "Z26", "Z52", "H", "S")   # bez nakładki, zawór 26/52 tyg., hamulec, „nie sprzedawaj na stracie”

# kontrola bloków: członek odbiega od kotwicy albo przestaje iść razem z nią
PEG_MAX_DEV = 0.03
PEG_MIN_CORR = 0.95

_MEMBER = {m: a for a, ms in BLOCS.items() for m in ms}


def bloc_of(code: str) -> str:
    """Kotwica bloku dla członka (HKD → USD), inaczej sama waluta."""
    return _MEMBER.get(code, code)


def members(anchor: str, admitted: Iterable[str]) -> list[str]:
    adm = set(admitted)
    return [m for m in BLOCS.get(anchor, ()) if m in adm]


def baskets(admitted: Iterable[str]) -> list[str]:
    """Koszyki REV: przyjęte waluty poza członkami bloków (blok = kotwica) + PLN na końcu.
    Członek bloku bez przyjętej kotwicy nie jest koszykiem (sam nic nie dywersyfikuje)."""
    adm = sorted(set(admitted) - {BASE})
    return [c for c in adm if c not in _MEMBER] + [BASE]
