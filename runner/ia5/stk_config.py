"""Stocks (D-071) — cotygodniowe rebalansowanie portfela spółek. Stałe: jedno źródło prawdy.

Zasady: CLAUDE.md, sekcja „Stocks (P)”. Zmiana logiki liczenia = podbicie STK_VERSION; zmiana warstwy czyszczenia =
podbicie CLEAN_STK_VERSION.
"""
from __future__ import annotations

STK_VERSION = "1"
CLEAN_STK_VERSION = "1"

TZ = "America/New_York"          # strefa giełdy: znacznik świecy = północ dnia sesji w Nowym Jorku
DECISION_TZ = "Europe/Warsaw"    # plan zleceń widać we wtorek od 08:00 czasu polskiego…
DECISION_HOUR = 8
EXEC_WEEKDAY = 1                 # …a wykonanie jest na otwarciu sesji we wtorek (święto → następny dzień sesji)

# lista startowa Michała (2026-11-15), równe udziały do czasu, aż poda własne
DEFAULT_TICKERS: tuple[str, ...] = (
    "MU", "MSFT", "AAPL", "MO", "CVX", "JPM", "PM", "JNJ", "AMZN", "FE", "KO", "MMM", "NVDA", "MRK", "SO",
    "SYY", "PPL", "DUK", "GPC", "VZ", "NEE", "USB", "AMT", "FRT", "GOOGL", "PEP", "O",
)
DEFAULT_CAPITAL = 10_000.0       # USD
DEFAULT_BAND = 20.0              # ± % docelowego udziału, w których system może przesuwać kapitał

COST = 0.001                     # koszt transakcji: 0,10% wartości każdej strony (prowizja + spread), metoda i porównania
MIN_HISTORY_DAYS = 252           # spółka wchodzi do portfela, gdy ma rok notowań (wcześniej: jej udział dzielą pozostałe)
START_WEIGHT = 0.8               # backtest startuje, gdy spółki z rokiem notowań mają ≥ 80% docelowego kapitału
IS_FRACTION = 0.75               # W1: ostatnie 25% tygodni to sprawdzian (OOS)
RANDOM_PATHS = 1000              # W3: losowe przesunięcia w tym samym paśmie
RANDOM_HOLD = 4                  # losowe oceny zmieniane co 4 tygodnie (podobna liczba transakcji co metody)
CSCV_BLOCKS = 16
BOOT_BLOCK = 8
VERDICT = {"random_pct": 95.0, "dsr": 0.95, "pbo": 0.3, "red_random_pct": 80.0}

# siatka metod (spisana przed liczeniem): ocena przeceny × normalizacja × siła × wygładzenie × filtr × próg transakcji
SIGNALS: dict[str, tuple[str, int]] = {
    **{f"dd{n}": ("dd", n) for n in (63, 126, 252, 504)},       # obsunięcie od szczytu z n dni
    **{f"ma{n}": ("ma", n) for n in (20, 50, 100, 200)},        # odległość od średniej z n dni
    **{f"rel{n}": ("rel", n) for n in (5, 21, 63, 126, 252, 756)},   # wynik z n dni względem pozostałych spółek
    **{f"z{n}": ("z", n) for n in (20, 60, 120, 250)},          # odchylenie od średniej w odchyleniach standardowych
    **{f"rsi{n}": ("rsi", n) for n in (5, 14, 30)},             # RSI
}
COMBOS: dict[str, tuple[str, str]] = {
    "dd252+rel21": ("dd252", "rel21"), "ma200+rel5": ("ma200", "rel5"), "z60+rel252": ("z60", "rel252"),
    "dd504+rsi14": ("dd504", "rsi14"), "rel756+rel21": ("rel756", "rel21"), "ma50+dd126": ("ma50", "dd126"),
}
NORMS = ("rank", "zs", "vrank")      # ranking / z-score przekroju / ranking po zmienności spółki
STRENGTHS = ("half", "full", "tails")  # połowa pasma / całe pasmo / tylko skrajne (±całe pasmo, środek bez zmian)
SMOOTH = (1, 4)                       # ocena z tego tygodnia / średnia z 4 tygodni
FILTERS = ("none", "knife", "trend")  # bez filtra / bez dokładania do spadającego noża / dokładanie tylko w trendzie
THRESHOLDS = (0.0, 0.1, 0.25)         # transakcja tylko, gdy cel odbiega od stanu o więcej niż x × docelowy udział

LABEL_SIGNAL = {"dd": "obsunięcie od szczytu {n} dni", "ma": "odległość od średniej {n} dni", "rel": "wynik {n} dni wobec reszty",
                "z": "odchylenie od średniej {n} dni (z)", "rsi": "RSI {n}"}
LABEL_NORM = {"rank": "ranking", "zs": "z-score", "vrank": "ranking / zmienność"}
LABEL_STRENGTH = {"half": "pół pasma", "full": "całe pasmo", "tails": "tylko skrajne"}
LABEL_FILTER = {"none": "bez filtra", "knife": "bez spadających noży", "trend": "dokładanie tylko w trendzie"}
