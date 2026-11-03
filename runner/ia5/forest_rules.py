"""FOREST (D-048): cechy rynku, z których inwestorzy budują swoje reguły.

Każda cecha to liczba znana na zamknięciu świecy t (tylko przeszłość, wskaźniki z `ia5.indicators` — B9).
Cechy są zorientowane na parę (dodatnia = za bazą) i w jednostkach ATR, więc ta sama reguła działa na 8 parach.

Osiem rodzin — osiem różnych źródeł informacji, bo las z jednego źródła głosuje jak jeden inwestor:
  trend, momentum, odwrócenie, zmienność, struktura (poziomy i kształt świec), kalendarz,
  międzyrynkowe (siła walut liczona z 8 par — tego nie widzi strategia jednej pary), sezonowość.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import indicators as ind
from .config import PAIRS

FAMILIES = ("trend", "momentum", "odwrócenie", "zmienność", "struktura", "kalendarz", "międzyrynkowe", "sezonowość")
CURRENCIES = ("USD", "EUR", "JPY", "GBP", "AUD", "CHF", "CAD")
WARMUP = 500  # świec na rozgrzewkę najdłuższych wskaźników (SMA/EMA 480)
EPS = 1e-12


def frame_index(raw: pd.DataFrame) -> pd.DataFrame:
    """Świece z indeksem UTC (czas otwarcia), jak w strategiach."""
    return raw.set_index(pd.to_datetime(raw["ts"], unit="s", utc=True))[["open", "high", "low", "close"]]


def _streak_signed(d: np.ndarray) -> np.ndarray:
    """Długość bieżącej serii zamknięć w jednym kierunku, ze znakiem kierunku."""
    out = np.zeros(len(d), np.int32)
    run = 0
    for k, v in enumerate(d):
        s = 1 if v > 0 else -1 if v < 0 else 0
        run = run + s if s and (run == 0 or (run > 0) == (s > 0)) else s
        out[k] = run
    return out


def _same_hour_memory(ret: np.ndarray, hour: np.ndarray, next_hour: np.ndarray, days: int) -> np.ndarray:
    """Średni ruch świec o godzinie wejścia z ostatnich `days` dni (dla każdej świecy t widzimy tylko świece ≤ t)."""
    n = len(ret)
    mem = pd.Series(ret).groupby(hour).transform(lambda s: s.rolling(days, min_periods=days).mean()).to_numpy()
    m = np.full((n, 24), np.nan)
    m[np.arange(n), hour] = mem
    m = pd.DataFrame(m).ffill().to_numpy()
    return m[np.arange(n), next_hour]


def _range_position(c: pd.Series, hi: pd.Series, lo: pd.Series) -> pd.Series:
    return (c - lo) / (hi - lo).where((hi - lo) > 0)


def currency_panel(frames: dict[str, pd.DataFrame], ks=(1, 3, 6, 12, 24, 48, 96)) -> dict:
    """Siła walut z wszystkich par na wspólnej siatce czasu (brakująca świeca = ostatnie znane zamknięcie — przeszłość).
    strength[(waluta, k)] = średni log-ruch waluty z k świec względem pozostałych; breadth[waluta] = ile par jest za nią."""
    close = (
        pd.DataFrame({p: pd.Series(df["close"].to_numpy(float), index=df["ts"].to_numpy()) for p, df in frames.items()})
        .sort_index()
        .ffill()
    )
    logc = np.log(close)
    strength, breadth = {}, {}
    trend = np.sign(close - close.ewm(span=50, adjust=False, min_periods=50).mean())
    legs = {c: [(p, 1.0 if p[:3] == c else -1.0) for p in close.columns if c in (p[:3], p[3:])] for c in CURRENCIES}
    for c, pl in legs.items():
        if not pl:
            continue
        breadth[c] = sum(trend[p] * s for p, s in pl) / len(pl)
        for k in ks:
            strength[(c, k)] = sum((logc[p] - logc[p].shift(k)) * s for p, s in pl) / len(pl)
    return {"grid": close.index.to_numpy(), "strength": strength, "breadth": breadth, "logc": logc, "ks": ks}


def pair_features(pair: str, raw: pd.DataFrame, cur: dict) -> dict[str, tuple[str, str, np.ndarray]]:
    """nazwa → (rodzina, opis, wartości). Wartość w świecy t używa wyłącznie świec ≤ t (test: dane obcięte = te same)."""
    df = frame_index(raw)
    o, hi, lo, c = df["open"], df["high"], df["low"], df["close"]
    a = ind.atr(df, 14)
    pip = PAIRS[pair].pip if pair in PAIRS else 0.0001
    out: dict[str, tuple[str, str, np.ndarray]] = {}

    def add(name, fam, label, x):
        out[name] = (fam, label, np.asarray(x, dtype=np.float32))

    # ---------- trend ----------
    ema = {n: ind.ema(c, n) for n in (5, 10, 20, 50, 100, 200, 480)}
    for n in (10, 20, 50, 100, 200, 480):
        add(f"cena_ema{n}", "trend", f"cena − EMA{n}", (c - ema[n]) / a)
    for f, s in ((5, 20), (10, 50), (20, 100), (50, 200)):
        add(f"ema{f}_{s}", "trend", f"EMA{f} − EMA{s}", (ema[f] - ema[s]) / a)
    for n, k in ((20, 5), (50, 10), (100, 24), (200, 48)):
        add(f"nachylenie{n}_{k}", "trend", f"nachylenie EMA{n} ({k} św.)", (ema[n] - ema[n].shift(k)) / (a * math.sqrt(k)))
    ribbon = sum(np.sign(ema[x] - ema[y]) for x, y in ((5, 10), (10, 20), (20, 50), (50, 100), (100, 200)))
    add("wstega", "trend", "ułożenie wstęgi EMA", ribbon)
    dx = ind.adx(df, 14)
    add("di", "trend", "+DI − −DI", dx["plus_di"] - dx["minus_di"])
    add("adx_kier", "trend", "ADX ze znakiem DI", dx["adx"] * np.sign(dx["plus_di"] - dx["minus_di"]))
    add("sma_cena480", "trend", "cena − SMA480", (c - ind.sma(c, 480)) / a)

    # ---------- momentum ----------
    for k in (1, 2, 3, 5, 8, 12, 24, 48, 96, 240):
        add(f"ruch{k}", "momentum", f"ruch z {k} św.", (c - c.shift(k)) / (a * math.sqrt(k)))
    m1, m2 = ind.macd(c, 12, 26, 9), ind.macd(c, 5, 35, 5)
    add("macd_hist", "momentum", "histogram MACD 12/26/9", m1["hist"] / a)
    add("macd_linia", "momentum", "linia MACD 12/26", m1["macd"] / a)
    add("macd_szybki", "momentum", "histogram MACD 5/35/5", m2["hist"] / a)
    day = df.index.floor("D")
    week = (df.index.tz_localize(None) + pd.Timedelta(hours=3)).to_period("W-SUN").start_time  # tydzień FX: od niedzieli wieczór
    add("ruch_dnia", "momentum", "ruch od otwarcia dnia", (c - o.groupby(day).transform("first")) / a)
    add("ruch_tygodnia", "momentum", "ruch od otwarcia tygodnia", (c - o.groupby(week).transform("first")) / a)
    up = (c.diff() > 0).astype(float)
    for n in (12, 24, 48):
        add(f"udzial_wzrostow{n}", "momentum", f"udział świec wzrostowych z {n}", up.rolling(n, min_periods=n).mean())

    # ---------- odwrócenie ----------
    for n in (2, 3, 5, 9, 14, 21, 30):
        add(f"rsi{n}", "odwrócenie", f"RSI({n})", ind.rsi(c, n))
    for k in (5, 14, 21):
        add(f"stoch{k}", "odwrócenie", f"stochastyk %K({k})", ind.stoch(df, k, 3, 3)["k"])
    for n in (10, 20, 50, 100):
        s = c.rolling(n, min_periods=n).std(ddof=0)
        add(f"z{n}", "odwrócenie", f"odchylenie od SMA{n} (σ)", (c - ind.sma(c, n)) / s.where(s > 0))
    add("seria", "odwrócenie", "seria zamknięć ze znakiem", _streak_signed(c.diff().fillna(0).to_numpy()))
    add("korpus1", "odwrócenie", "korpus ostatniej świecy", (c - o) / a)
    add("korpus3", "odwrócenie", "suma korpusów 3 świec", (c - o).rolling(3, min_periods=3).sum() / a)

    # ---------- zmienność ----------
    a5, a50, a100, a480 = ind.atr(df, 5), ind.atr(df, 50), ind.atr(df, 100), ind.atr(df, 480)
    add("atr5_50", "zmienność", "ATR5 / ATR50", a5 / a50)
    add("atr14_100", "zmienność", "ATR14 / ATR100", a / a100)
    add("atr14_480", "zmienność", "ATR14 / ATR480", a / a480)
    add("szer_boll", "zmienność", "szerokość wstęgi Bollingera", 4 * c.rolling(20, min_periods=20).std(ddof=0) / a)
    add("zakres1", "zmienność", "zakres ostatniej świecy", (hi - lo) / a)
    add("zakres3", "zmienność", "zakres 3 świec", (ind.highest(hi, 3) - ind.lowest(lo, 3)) / a)
    add("zmien_kier", "zmienność", "wzrost zmienności × kierunek ruchu", (a5 / a50 - 1) * np.sign(c - c.shift(12)))

    # ---------- struktura ----------
    for n in (12, 24, 48, 96, 240, 480):
        add(f"donchian{n}", "struktura", f"pozycja w kanale {n} św.", _range_position(c, ind.highest(hi, n), ind.lowest(lo, n)))
    d_hi, d_lo = hi.groupby(day).max().shift(1), lo.groupby(day).min().shift(1)
    y_hi, y_lo = d_hi.reindex(day).set_axis(df.index), d_lo.reindex(day).set_axis(df.index)
    add("wczoraj_poz", "struktura", "pozycja w zakresie wczoraj", _range_position(c, y_hi, y_lo))
    add("wczoraj_max", "struktura", "cena − wczorajsze maksimum", (c - y_hi) / a)
    add("wczoraj_min", "struktura", "cena − wczorajsze minimum", (c - y_lo) / a)
    add("tydzien_poz", "struktura", "pozycja w zakresie tygodnia", _range_position(c, hi.groupby(week).cummax(), lo.groupby(week).cummin()))
    w_hi, w_lo = hi.groupby(week).max().shift(1), lo.groupby(week).min().shift(1)
    add(
        "zeszly_tydz_poz",
        "struktura",
        "pozycja w zakresie zeszłego tygodnia",
        _range_position(c, w_hi.reindex(week).set_axis(df.index), w_lo.reindex(week).set_axis(df.index)),
    )
    pl = df.index.tz_convert("Europe/Warsaw")
    plday = pd.Series(pl.normalize(), index=df.index)
    night = pd.Series(pl.hour < 7, index=df.index)
    n_hi = hi.where(night).groupby(plday).cummax().groupby(plday).ffill()
    n_lo = lo.where(night).groupby(plday).cummin().groupby(plday).ffill()
    add("azja_poz", "struktura", "pozycja w zakresie nocy", _range_position(c, n_hi, n_lo))
    for lvl in (100, 50):
        step = lvl * pip
        add(f"okragla{lvl}", "struktura", f"odległość od poziomu co {lvl} pips", (c - (c / step).round() * step) / a)
    rng = (hi - lo).where((hi - lo) > 0)
    add("cien_gora", "struktura", "górny cień świecy", (hi - np.maximum(o, c)) / rng)
    add("cien_dol", "struktura", "dolny cień świecy", (np.minimum(o, c) - lo) / rng)
    add("poz_zamkniecia", "struktura", "zamknięcie w zakresie świecy", (c - lo) / rng)
    add("wewnetrzna", "struktura", "świeca wewnętrzna", ((hi < hi.shift(1)) & (lo > lo.shift(1))).astype(float))
    body, pbody = c - o, (c - o).shift(1)
    eng = (np.sign(body) != np.sign(pbody)) & (body.abs() > pbody.abs())
    add("objecie", "struktura", "objęcie ze znakiem", (eng.astype(float) * np.sign(body)).fillna(0.0))

    # ---------- kalendarz (godzina i dzień świecy wejścia, czas polski) ----------
    nxt = (df.index + pd.Timedelta(hours=1)).tz_convert("Europe/Warsaw")
    hour, wd = np.asarray(nxt.hour), np.asarray(nxt.day_of_week)
    for hh in range(7, 17):
        add(f"godz{hh}", "kalendarz", f"wejście o {hh}:00", (hour == hh).astype(float))
    for x, y in ((7, 10), (10, 13), (13, 15), (15, 17)):
        add(f"pora{x}_{y}", "kalendarz", f"wejście {x}–{y}", ((hour >= x) & (hour < y)).astype(float))
    for k, nm in enumerate(("pn", "wt", "śr", "czw", "pt")):
        add(f"dzien_{nm}", "kalendarz", f"dzień: {nm}", (wd == k).astype(float))
    dom = np.asarray(nxt.day)
    dim = np.asarray(nxt.days_in_month)
    add("koniec_mies", "kalendarz", "ostatnie 3 dni miesiąca", (dom > dim - 3).astype(float))
    add("poczatek_mies", "kalendarz", "pierwsze 3 dni miesiąca", (dom <= 3).astype(float))
    add("pierwszy_tydz", "kalendarz", "pierwszy tydzień miesiąca", (dom <= 7).astype(float))
    add("pt_popoludnie", "kalendarz", "piątek po południu", ((wd == 4) & (hour >= 13)).astype(float))

    # ---------- międzyrynkowe (siła walut z 8 par, tylko świece ≤ t) ----------
    base, quote = pair[:3], pair[3:]
    ts = raw["ts"].to_numpy()
    pos = np.searchsorted(cur["grid"], ts)
    rel = (a / c).to_numpy()
    st = cur["strength"]
    for k in cur["ks"]:
        sb = st[(base, k)].to_numpy()[pos] if (base, k) in st else np.zeros(len(ts))
        sq = st[(quote, k)].to_numpy()[pos] if (quote, k) in st else np.zeros(len(ts))
        den = rel * math.sqrt(k)
        add(f"sila_roznica{k}", "międzyrynkowe", f"siła baza − kwotowana ({k} św.)", (sb - sq) / den)
        add(f"sila_baza{k}", "międzyrynkowe", f"siła waluty bazowej ({k} św.)", sb / den)
        add(f"sila_kwota{k}", "międzyrynkowe", f"siła waluty kwotowanej ({k} św.)", sq / den)
        lp = cur["logc"][pair].to_numpy() if pair in cur["logc"] else np.log(c.to_numpy())
        move = (lp - pd.Series(lp).shift(k).to_numpy())[pos] if pair in cur["logc"] else lp - pd.Series(lp).shift(k).to_numpy()
        add(f"rezyduum{k}", "międzyrynkowe", f"ruch pary ponad siłę walut ({k} św.)", (move - (sb - sq)) / den)
    br = cur["breadth"]
    bb = br[base].to_numpy()[pos] if base in br else np.zeros(len(ts))
    bq = br[quote].to_numpy()[pos] if quote in br else np.zeros(len(ts))
    add("szerokosc", "międzyrynkowe", "szerokość trendu baza − kwotowana", bb - bq)

    # ---------- sezonowość (ruch tej samej godziny i dnia w przeszłości) ----------
    ret = ((c - c.shift(1)) / a).to_numpy()
    hu = np.asarray(df.index.hour)
    nh = np.asarray((df.index + pd.Timedelta(hours=1)).hour)
    for d in (1, 5, 10, 20, 40):
        add(f"sez_godzina{d}", "sezonowość", f"ruch godziny wejścia, średnia {d} dni", _same_hour_memory(ret, hu, nh, d))
    dc = c.groupby(day).last()
    dret = (dc - dc.shift(1)).shift(1)  # wynik wczorajszego dnia (dziś jeszcze nieznany)
    add("wczoraj_ruch", "sezonowość", "ruch wczorajszego dnia", dret.reindex(day).set_axis(df.index) / (a * math.sqrt(24)))
    wc = c.groupby(week).last()
    wret = (wc - wc.shift(1)).shift(1)
    add("zeszly_tydz_ruch", "sezonowość", "ruch zeszłego tygodnia", wret.reindex(week).set_axis(df.index) / (a * math.sqrt(120)))
    return out
