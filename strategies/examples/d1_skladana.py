import numpy as np
import pandas as pd

TIMEFRAME = "D1"   # świece dzienne Yahoo, cała historia (D-058); zamknięcie dnia po naprawie D-068

HYPOTHESIS = """Strategia składana na świecach dziennych: trzy małe, niezależne przewagi tego samego rodzaju — dostarczanie
płynności, gdy inni muszą handlować — zebrane w jedną księgę, bo razem rosną równiej niż każda osobno.
1. Poniedziałek: kto był po złej stronie ruchu, zamyka pozycje przed weekendem i dopycha kurs za daleko; w poniedziałek ten
   ruch się cofa. Wejście przeciw rozciągnięciu, gdy zgadzają się co najmniej 2 z 5 miar; wyjście tego samego dnia na zamknięciu.
2. Cofnięcie w trendzie: drugi i kolejny dzień wyprzedania (RSI5 < 25) nad średnią 200-dniową (short lustrzanie), bez dni-szoków;
   sprzedający się wyczerpują, trend wraca w 3 dni.
3. Początek miesiąca: przepływy z końca miesiąca (rebalansowanie funduszy) pchają kurs z trendem; w pierwszych 2 dniach
   handlu nowego miesiąca ten ruch się cofa — wejście przeciw 10-dniowemu ruchowi zgodnemu z trendem, wyjście po 2 dniach.
Wybór na IS: ok. 267 tys. reguł strukturalnych (dwie połowy IS i niezależne dane brokera), potem ok. 6,3 tys. konfiguracji
składników policzonych silnikiem; z każdej rodziny środek płaskowyżu, nie szczyt (research/d1/README.md, D-070)."""

# Miary rozciągnięcia do głosowania w poniedziałek (znak = kierunek dotychczasowego ruchu):
#   ("mom", k, próg)   ruch z k dni w ATR14·√k ponad próg
#   ("rsi", n, poziom) RSI(n) poniżej poziomu / powyżej 100 − poziom
#   ("boll", n, k)     zamknięcie poza wstęgą Bollingera(n, k)
MIARY = [("mom", 2, 0.75), ("mom", 3, 0.75), ("mom", 5, 0.5), ("rsi", 5, 30), ("boll", 20, 1.5)]

# Każda konfiguracja = jedna wersja księgi. w_* = waga składnika (stawka), zm = stawka odwrotnie do zmienności pary,
# sl = ochronny stop w ATR14 od zamknięcia dnia sygnału (None = wyjście tylko po czasie).
CONFIGS = [
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "zm": True, "sl": None},    # 0 = wybór po IS (środek płaskowyżu)
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "zm": False, "sl": None},   # 1 = ta sama księga, stała stawka
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "zm": True, "sl": 2.0},     # 2 = z ochronnym stopem 2 × ATR
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.5, "zm": True, "sl": 3.0},     # 3 = z ochronnym stopem 3 × ATR
    {"w_pon": 1.0, "w_trend": 0.5, "w_mies": 0.0, "zm": True, "sl": None},    # 4 = bez początku miesiąca (najsłabsze ogniwo)
]
PARAMS = {"cfg": list(range(len(CONFIGS)))}

DNI_PON, DNI_TREND, DNI_MIES = 1, 3, 2          # ile dni trwa pozycja każdego składnika (wyjście na zamknięciu dnia)
PYRAMID = 3                                     # do 3 pozycji naraz w parze, jeden kierunek — składniki mogą się nakładać
EXITS = [{"kind": "level", "cap": 5}]           # limit dni każdego wejścia podaje levels() w kolumnie bars (D-070)
SIZING = [1, 2, 3, 5]                           # % kapitału jako depozyt na jednostkę wagi; w poniedziałek bywa 8 pozycji naraz

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
    """Sygnał (± stawka) i liczba dni pozycji dla każdej świecy; liczone na zamknięciu dnia sygnału."""
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

    sig = np.zeros(n)
    for kier, _, w in skladniki:
        sig += w * kier
    dni = np.zeros(n)
    for kier, k, _ in skladniki:                      # liczba dni = najdłuższy ze składników zgodnych z kierunkiem sumy
        dni = np.where((kier != 0) & (np.sign(sig) == kier), np.maximum(dni, k), dni)
    if c["zm"]:                                       # stawka odwrotnie do zmienności pary: równe ryzyko na transakcję
        with np.errstate(invalid="ignore", divide="ignore"):
            sig = sig * np.nan_to_num(np.clip(0.006 / (a / px), 0.5, 2.0), nan=1.0)
    sig = np.where(np.abs(sig) < 1e-9, 0.0, np.sign(sig) * np.clip(np.abs(sig), 0.1, 10.0))
    return sig, dni, a, px


def signals(df, p, ind):
    sig, _, _, _ = _ksiega(df, CONFIGS[p["cfg"]], ind)
    return pd.Series(sig, index=df.index)


def levels(df, p, ind):
    c = CONFIGS[p["cfg"]]
    sig, dni, a, px = _ksiega(df, c, ind)
    out = pd.DataFrame({"bars": np.where(sig != 0, dni, np.nan)}, index=df.index)
    if c["sl"] is not None:
        out["sl"] = np.where(sig != 0, px - np.sign(sig) * c["sl"] * a, np.nan)
    return out
