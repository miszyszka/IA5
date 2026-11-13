"""Szkic strategii składanej na D1 (kod sygnałów = ten sam, który trafi do strategii). build(df, cfg, ind) → (sygnał ±waga, dni)."""
import paths  # noqa: F401  (ścieżki + research/rynek/lib.py)
import numpy as np
import pandas as pd

HOL = np.array([f"{y}-{md}" for y in range(1990, 2041) for md in ("12-25", "01-01")], dtype="datetime64[D]")


def entry_day(idx):
    """Dzień wejścia = następny dzień handlu po dniu sygnału (pon–pt bez 25.12 i 1.01) — z kalendarza, nie z danych."""
    d = np.array(idx.tz_convert("Europe/London").tz_localize(None).normalize(), dtype="datetime64[D]")
    nxt = np.busday_offset(d, 1, roll="backward", holidays=HOL)
    dow = (nxt.astype("int64") + 3) % 7                                   # 0 = poniedziałek
    first = nxt.astype("datetime64[M]").astype("datetime64[D]")
    rank = np.busday_count(first, nxt, holidays=HOL) + 1                  # który dzień handlu miesiąca
    return dow, rank


def stretch(df, ind, m, atr):
    """Znak rozciągnięcia: +1 gdy cena odjechała w górę za próg, −1 w dół, 0 w środku."""
    kind, a, b = m
    c = df.close
    if kind == "mom":
        v, thr = (c - c.shift(a)) / (atr * a ** 0.5), b
    elif kind == "rsi":
        v, thr = ind.rsi(c, a) - 50.0, 50.0 - b
    elif kind == "boll":
        v, thr = (c - ind.sma(c, a)) / c.rolling(a).std(), b
    else:
        raise ValueError(kind)
    v = np.array(v, dtype=float)
    with np.errstate(invalid="ignore"):
        return (v > thr).astype(int) - (v < -thr).astype(int)


def votes(df, ind, ms, atr):
    """Suma znaków kilku miar rozciągnięcia (głosowanie): od −len(ms) do +len(ms)."""
    v = np.zeros(len(df))
    for m in ms:
        v += stretch(df, ind, m, atr)
    return v


def streak(mask):
    m = mask.astype(np.int64)
    c = np.cumsum(m)
    return c - np.maximum.accumulate(np.where(m == 0, c, 0))


def build(df, cfg, ind):
    n = len(df)
    atr = ind.atr(df, 14)
    a = np.array(atr, dtype=float)
    px = np.array(df.close, dtype=float)
    rng = np.array(df.high - df.low, dtype=float)
    dow, rank = entry_day(df.index)
    sig, bars = np.zeros(n), np.zeros(n, dtype=np.int64)
    comps = []
    c = cfg.get("pon")
    if c:                                             # 1. poniedziałek: przeciw rozciągnięciu z końca tygodnia
        if "ms" in c:                                 # głosowanie kilku miar; stawka rośnie z liczbą zgodnych głosów
            v = votes(df, ind, c["ms"], atr)
            s = np.where(np.abs(v) >= c["min"], np.sign(v), 0)
            wv = np.abs(v) / len(c["ms"]) if c.get("skala") else np.ones(n)
        else:
            s, wv = stretch(df, ind, c["m"], atr), np.ones(n)
        ok = dow == 0
        if c.get("calm"):
            with np.errstate(invalid="ignore"):
                ok = ok & (rng < c["calm"] * a)
        comps.append((np.where(ok, -s, 0), c["dni"], c["w"] * wv))
    c = cfg.get("mies")
    if c:                                             # 2. początek miesiąca: przeciw ruchowi z końca poprzedniego
        s = stretch(df, ind, c["m"], atr)
        ok = rank <= c["ile"]
        if c.get("trend"):
            with np.errstate(invalid="ignore"):
                tr = np.sign(px - np.array(ind.sma(df.close, c["trend"]), dtype=float))
            ok = ok & (s * tr > 0)                    # tylko ruch zgodny z trendem (wtedy cofnięcie)
        if c.get("calm"):
            with np.errstate(invalid="ignore"):
                ok = ok & (rng < c["calm"] * a)
        if c.get("bez_pon"):
            ok = ok & (dow != 0)
        comps.append((np.where(ok, -s, 0), c["dni"], c["w"]))
    c = cfg.get("trend")
    if c:                                             # 3. cofnięcie w trendzie: seria dni wyprzedania nad średnią (short lustrzanie)
        per, lv = c["rsi"]
        r = np.array(ind.rsi(df.close, per), dtype=float)
        s_ = np.array(ind.sma(df.close, c["sma"]), dtype=float)
        with np.errstate(invalid="ignore"):
            lo, hi = (px > s_) & (r < lv), (px < s_) & (r > 100 - lv)
            L, S = lo & (streak(lo) >= c["od"]), hi & (streak(hi) >= c["od"])
            if c.get("calm"):
                calm = rng < c["calm"] * a
                L, S = L & calm, S & calm
        d = L.astype(int) - S.astype(int)
        if c.get("bez_pon"):
            d = np.where(dow == 0, 0, d)
        comps.append((d, c["dni"], c["w"]))
    for d, _, w in comps:
        sig += w * d
    for d, k, _ in comps:                             # dni = najdłuższy ze składników zgodnych z kierunkiem sumy
        bars = np.where((d != 0) & (np.sign(sig) == d), np.maximum(bars, k), bars)
    if cfg.get("zm"):                                 # stawka odwrotnie do zmienności pary (równe ryzyko na transakcję)
        with np.errstate(invalid="ignore", divide="ignore"):
            f = np.clip(cfg["zm"] / (a / px), 0.5, 2.0)
        sig = sig * np.nan_to_num(f, nan=1.0)
    sig = np.where(np.abs(sig) < 1e-9, 0.0, np.sign(sig) * np.clip(np.abs(sig), 0.1, 10.0))
    d = np.sign(sig)
    tp = np.where(d != 0, px + d * cfg["tp"] * a, np.nan) if cfg.get("tp") else np.full(n, np.nan)
    sl = np.where(d != 0, px - d * cfg["sl"] * a, np.nan) if cfg.get("sl") else np.full(n, np.nan)
    return sig, bars, tp, sl
