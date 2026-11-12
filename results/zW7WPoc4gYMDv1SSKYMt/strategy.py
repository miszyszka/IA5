import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo (D-058); wejście na open następnego dnia, wyjście po X dniach

HYPOTHESIS = """Wersja 2 strategii RSI na D1, z diagnozy stratnych i zyskownych wejść wersji 1 (research/rsi_d1/README.md).
Straty łączyło: pierwszy dzień wyprzedania (spadek często trwa dalej), dzień-szok z bardzo szerokim zakresem i głęboki krach
przeciw trendowi. Zyski łączyło: trend 200-dniowy po stronie transakcji i KOLEJNY dzień wyprzedania z rzędu — sprzedający
się wyczerpują, a trend wraca w 3–4 dni. Wzmacniamy to: wejście dopiero od 2. (albo 3.) dnia z rzędu z RSI za progiem,
nad SMA200 (short lustrzanie pod), bez dni-szoków; wyjście po 3–5 dniach na zamknięciu. Konfiguracje wybrane na IS:
odporne w obu połowach IS (1996–2011, 2012–2019) i na obu wersjach zamknięć D1 Yahoo (zob. D-068 — zamknięcia D1 Yahoo)."""

# Każda konfiguracja = jedna wersja (wariant wejścia) × 3 limity dni z EXITS.
#   rsi:    (okres, próg wyprzedania); wykupienie = 100 − próg
#   od:     od którego dnia z rzędu za progiem (i po stronie trendu) wchodzimy: 1 = od pierwszego, 2 = od drugiego, …
#   zakres: pomiń dzień-szok, gdy (high − low) dnia sygnału ≥ zakres × ATR14; None = bez cięcia
#   sl:     None albo k × ATR14 od zamknięcia dnia sygnału
#   waga:   "stala" 1; "seria" = 1 w dniu „od”, 2 dzień później, 3 od trzeciego (dokładanie przy przedłużonym wyprzedaniu)
CONFIGS = [
    # 0 = wybór po IS: najbardziej odporna (min. Sharpe z 4 prób: 2 połowy IS × 2 wersje zamknięć D1)
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": None, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": None, "waga": "seria"},
    {"rsi": (5, 25), "od": 1, "zakres": 1.5, "sl": None, "waga": "seria"},   # 4 = od pierwszego dnia (więcej transakcji)
    {"rsi": (5, 25), "od": 3, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (5, 20), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (3, 15), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (3, 15), "od": 2, "zakres": 2.0, "sl": None, "waga": "stala"},
    {"rsi": (2, 15), "od": 2, "zakres": 1.5, "sl": None, "waga": "stala"},
    {"rsi": (2, 15), "od": 3, "zakres": 1.5, "sl": 2.0, "waga": "seria"},
    {"rsi": (5, 25), "od": 2, "zakres": 2.0, "sl": 2.0, "waga": "stala"},
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

PYRAMID = 3   # do 3 pozycji naraz w parze, jeden kierunek — kolejne dni wyprzedania dokładają (D-034)
EXITS = [{"kind": "level", "cap": c} for c in (3, 4, 5)]   # wyjście po 3 / 4 / 5 dniach na zamknięciu (albo wcześniej na SL)
# Stawka bazowa (% kapitału jako depozyt, × 30 nominału): do 3 pozycji w parze × 8 par z USD poruszających się razem.
SIZING = [1, 2, 3, 5]


def _streak(mask):
    """Która z kolei świeca w serii True (0 poza serią)."""
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def _setup(df, c, ind):
    close = df.close
    period, level = c["rsi"]
    r = np.array(ind.rsi(close, period), dtype=float)
    s200 = np.array(ind.sma(close, 200), dtype=float)
    px = np.array(close, dtype=float)
    with np.errstate(invalid="ignore"):
        zone_lo = (px > s200) & (r < level)            # wyprzedanie w trendzie wzrostowym
        zone_hi = (px < s200) & (r > 100 - level)      # wykupienie w trendzie spadkowym
    st_lo, st_hi = _streak(zone_lo), _streak(zone_hi)
    long_ = zone_lo & (st_lo >= c["od"])
    short = zone_hi & (st_hi >= c["od"])
    if c["zakres"] is not None:
        atr = np.array(ind.atr(df, 14), dtype=float)
        with np.errstate(invalid="ignore"):
            calm = np.array(df.high - df.low, dtype=float) < c["zakres"] * atr
        long_ &= calm
        short &= calm
    direction = long_.astype(int) - short.astype(int)
    streak = np.where(direction > 0, st_lo, np.where(direction < 0, st_hi, 0))
    return direction, streak


def signals(df, p, ind):
    c = CONFIGS[p["cfg"]]
    direction, streak = _setup(df, c, ind)
    w = np.clip(streak - c["od"] + 1, 1, 3).astype(float) if c["waga"] == "seria" else np.ones(len(df))
    return pd.Series(np.where(direction != 0, direction * w, 0.0), index=df.index)


def levels(df, p, ind):
    c = CONFIGS[p["cfg"]]
    tp = pd.Series(np.nan, index=df.index)
    sl = pd.Series(np.nan, index=df.index)
    if c["sl"] is None:                       # wyjście tylko po limicie dni (na zamknięciu)
        return pd.DataFrame({"tp": tp, "sl": sl})
    direction, _ = _setup(df, c, ind)
    d = pd.Series(np.where(direction != 0, direction, np.nan), index=df.index)
    sl = df.close - d * c["sl"] * ind.atr(df, 14)
    return pd.DataFrame({"tp": tp, "sl": sl})