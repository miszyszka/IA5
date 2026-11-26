import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058); zamknięcie dnia po naprawie D-068

HYPOTHESIS = """Księga v2 (D-075): trzy przewagi „dostarczania płynności” z d1_skladana (poniedziałek przeciw rozciągnięciu,
cofnięcie w trendzie, początek miesiąca — reguły bez zmian, nie strojone pod OOS) plus czwarty składnik o PRZECIWNEJ
skośności: wybicie 55-dniowego kanału w stronę trendu 200-dniowego (premia za trend). Powroty dają częste małe zyski
i rzadkie duże straty, trend — odwrotnie; razem krzywa ma być równiejsza niż każda część osobno.
Druga zmiana to nie sygnał, tylko portfel: stawka od ryzyka (stały % kapitału do stopu), cel zmienności kapitału 8% rocznie
i najwyżej 3 pozycje w jedną stronę na jedną walutę — spadki biorą się głównie ze skupisk tej samej ekspozycji
(long EUR/USD + GBP/USD + AUD/USD to trzy razy short USD), a nie z pojedynczej transakcji.
Parametry trendu są klasyczne (Donchian 55, stop 2,5 ATR, 20 dni) i ustalone przed liczeniem."""

# Wersje księgi: w_* = waga składnika. cfg 0 = pełna v2; cfg 1 = bez trendu (te same trzy składniki co v1, ale z nowym
# portfelem) — porównanie pokazuje, ile daje sam składnik trendowy; cfg 2 = sam trend (do oceny korelacji).
CONFIGS = [
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "w_tr": 0.5},
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "w_tr": 0.0},
    {"w_pon": 0.0, "w_trend": 0.0, "w_mies": 0.0, "w_tr": 1.0},
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

DNI_PON, DNI_TREND, DNI_MIES, DNI_TR = 1, 3, 2, 20   # ile dni trwa pozycja każdego składnika (wyjście na zamknięciu dnia)
DON, SL_TR = 55, 2.5                                 # składnik trendowy: kanał Donchiana i stop w ATR14
PYRAMID = 3
EXITS = [{"kind": "level", "cap": 25}]               # limit dni i stop każdego wejścia podaje levels() (D-057, D-070)

# --- portfel (D-075): tylko symulacja kapitału — ranking, DSR i PBO dalej na R, bez dodatkowych prób ---
SIZING_MODE = "risk"           # SIZING = % kapitału ryzykowany do stopu (bez stopu: do 1 × ATR14)
SIZING = [0.25, 0.5, 1.0]
VOL_TARGET = 8                 # % rocznie — stawka × (8% ÷ zmienność kapitału z 60 dni), w granicach 0,25–2×
MAX_CCY = 3                    # najwyżej 3 pozycje (suma wag) w jedną stronę na jedną walutę

# Miary rozciągnięcia do głosowania w poniedziałek (znak = kierunek dotychczasowego ruchu):
#   ("mom", k, próg)   ruch z k dni w ATR14·√k ponad próg
#   ("rsi", n, poziom) RSI(n) poniżej poziomu / powyżej 100 − poziom
#   ("boll", n, k)     zamknięcie poza wstęgą Bollingera(n, k)
MIARY = [("mom", 2, 0.75), ("mom", 3, 0.75), ("mom", 5, 0.5), ("rsi", 5, 30), ("boll", 20, 1.5)]

SWIETA = np.array([f"{y}-{md}" for y in range(1990, 2061) for md in ("12-25", "01-01")], dtype="datetime64[D]")


def _dzien_wejscia(idx):
    """Następny dzień handlu po dniu sygnału, z kalendarza (pon–pt bez 25.12 i 1.01): dzień tygodnia i numer dnia w miesiącu."""
    d = np.array(idx.tz_convert("Europe/London").tz_localize(None).normalize(), dtype="datetime64[D]")
    nxt = np.busday_offset(d, 1, roll="backward", holidays=SWIETA)
    dow = (nxt.astype("int64") + 3) % 7                                    # 0 = poniedziałek
    numer = np.busday_count(nxt.astype("datetime64[M]").astype("datetime64[D]"), nxt, holidays=SWIETA) + 1
    return dow, numer


def _rozciagniecie(df, ind, miara, atr):
    """+1 gdy cena odjechała w górę za próg, −1 w dół, 0 w środku."""
    kind, a, b = miara
    c = df.close
    with np.errstate(invalid="ignore"):
        if kind == "mom":
            v = np.array((c - c.shift(a)) / (atr * a ** 0.5), dtype=float)
            return (v > b).astype(int) - (v < -b).astype(int)
        if kind == "rsi":
            r = np.array(ind.rsi(c, a), dtype=float)
            return (r > 100 - b).astype(int) - (r < b).astype(int)
        bb = ind.bollinger(c, a, b)
        px = np.array(c, dtype=float)
        return (px > np.array(bb.upper, dtype=float)).astype(int) - (px < np.array(bb.lower, dtype=float)).astype(int)


def _seria(mask):
    """Która z kolei świeca w serii True (0 poza serią)."""
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def _ksiega(df, c, ind):
    """Sygnał (± stawka), liczba dni pozycji i stop (w ATR14, NaN = bez stopu) dla każdej świecy; na zamknięciu dnia sygnału."""
    n = len(df)
    atr = ind.atr(df, 14)
    a = np.array(atr, dtype=float)
    px = np.array(df.close, dtype=float)
    zakres = np.array(df.high - df.low, dtype=float)
    sma200 = np.array(ind.sma(df.close, 200), dtype=float)
    dow, numer = _dzien_wejscia(df.index)
    skladniki = []

    # 1. poniedziałek: przeciw rozciągnięciu, gdy zgadzają się co najmniej 2 z 5 miar
    glosy = np.zeros(n)
    for miara in MIARY:
        glosy += _rozciagniecie(df, ind, miara, atr)
    kier = np.where((dow == 0) & (np.abs(glosy) >= 2), -np.sign(glosy), 0)
    skladniki.append((kier, DNI_PON, c["w_pon"]))

    # 2. cofnięcie w trendzie: od 2. dnia z rzędu RSI5 < 25 nad SMA200 (short lustrzanie), bez dnia-szoku
    rsi5 = np.array(ind.rsi(df.close, 5), dtype=float)
    with np.errstate(invalid="ignore"):
        lo, hi = (px > sma200) & (rsi5 < 25), (px < sma200) & (rsi5 > 75)
        spokojny = zakres < 1.5 * a
        kier = ((lo & (_seria(lo) >= 2)).astype(int) - (hi & (_seria(hi) >= 2)).astype(int)) * spokojny
    skladniki.append((kier, DNI_TREND, c["w_trend"]))

    # 3. początek miesiąca: pierwsze 2 dni handlu (nie poniedziałek), przeciw 10-dniowemu ruchowi zgodnemu z trendem
    if c["w_mies"] > 0:
        ruch = _rozciagniecie(df, ind, ("mom", 10, 0.0), atr)
        with np.errstate(invalid="ignore"):
            z_trendem = ruch * np.sign(px - sma200) > 0
        kier = np.where((numer <= 2) & (dow != 0) & z_trendem, -ruch, 0)
        skladniki.append((kier, DNI_MIES, c["w_mies"]))

    # 4. trend (NOWE w v2): wybicie 55-dniowego kanału Donchiana w stronę SMA200 — rzadkie, długie, dodatnia skośność;
    #    równoważy trzy składniki powrotu (ujemna skośność). Stop 2,5 × ATR14, wyjście po 20 dniach.
    trend_kier = np.zeros(n)
    if c["w_tr"] > 0:
        hi55 = np.array(ind.highest(df.high, DON).shift(1), dtype=float)
        lo55 = np.array(ind.lowest(df.low, DON).shift(1), dtype=float)
        with np.errstate(invalid="ignore"):
            up = (px > hi55) & (np.r_[np.nan, px[:-1]] <= np.r_[np.nan, hi55[:-1]]) & (px > sma200)
            dn = (px < lo55) & (np.r_[np.nan, px[:-1]] >= np.r_[np.nan, lo55[:-1]]) & (px < sma200)
        trend_kier = up.astype(int) - dn.astype(int)
        skladniki.append((trend_kier, DNI_TR, c["w_tr"]))
    skladniki = [x for x in skladniki if x[2] > 0]      # składnik z wagą 0 nie wpływa ani na kierunek, ani na liczbę dni

    sig = np.zeros(n)
    for kier, _, w in skladniki:
        sig += w * kier
    dni = np.zeros(n)
    for kier, k, _ in skladniki:                      # liczba dni = najdłuższy ze składników zgodnych z kierunkiem sumy
        dni = np.where((kier != 0) & (np.sign(sig) == kier), np.maximum(dni, k), dni)
    # stop tylko dla wejść prowadzonych przez trend (jego kierunek = kierunek sumy); reszta wychodzi po czasie
    stop = np.where((trend_kier != 0) & (np.sign(sig) == trend_kier), SL_TR, np.nan)
    # Stawka: przy SIZING_MODE = "risk" silnik sam dzieli ryzyko przez odległość do SL (bez SL — przez 1 × ATR14),
    # więc nie trzeba już ręcznie skalować odwrotnie do zmienności (to robiło zm = True w v1).
    sig = np.where(np.abs(sig) < 1e-9, 0.0, np.sign(sig) * np.clip(np.abs(sig), 0.1, 10.0))
    return sig, dni, a, px, stop


def signals(df, p, ind):
    sig, _, _, _, _ = _ksiega(df, CONFIGS[p["cfg"]], ind)
    return pd.Series(sig, index=df.index)


def levels(df, p, ind):
    sig, dni, a, px, stop = _ksiega(df, CONFIGS[p["cfg"]], ind)
    return pd.DataFrame({"bars": np.where(sig != 0, dni, np.nan),
                         "sl": np.where((sig != 0) & np.isfinite(stop), px - np.sign(sig) * stop * a, np.nan)}, index=df.index)
