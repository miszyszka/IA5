HYPOTHESIS = """FX-POWRÓT z celem w cenie (D-057). Po impulsie (zamknięcie ≥ imp × ATR100 dalej niż zamknięcie 3 świece wcześniej)
pierwsza świeca przeciwna w ciągu 3 świec po impulsie pokazuje wyczerpanie — wejście przeciw impulsowi z celem w POŁOWIE
drogi od skrajnej ceny impulsu (P: najwyższe high / najniższe low z 4 świec) do bazy sprzed impulsu (B: zamknięcie 3 świece
przed świecą impulsu), stop ¼ zakresu za P. Poziomy są cenami policzonymi na świecy sygnału — silnik egzekwuje tę regułę
dokładnie, zamiast przybliżać ją wielokrotnościami ATR (tak było w powrot_v2.py)."""

PARAMS = {"imp": [2.0, 2.5]}
HOURS = False

EXITS = [
    {"kind": "level", "cap": 60},     # TP/SL z levels(), limit 60 świec (B7)
    {"kind": "level", "cap": 120},
]


def _setup(df, p, ind):
    atr = ind.atr(df, 100)
    base = df.close.shift(3)                                   # B: zamknięcie sprzed impulsu
    up = (df.close - base) >= p["imp"] * atr                   # świeca kończąca impuls w górę
    dn = (base - df.close) >= p["imp"] * atr
    red, green = df.close < df.open, df.close > df.open
    # zdarzenie: pierwsza czerwona (zielona) świeca w ciągu 3 świec po impulsie — nie stan
    after_up = (up.shift(1) | up.shift(2) | up.shift(3)).fillna(False).astype(bool)
    after_dn = (dn.shift(1) | dn.shift(2) | dn.shift(3)).fillna(False).astype(bool)
    short = after_up & red & ~(after_up & red).shift(1).fillna(False).astype(bool)
    long_ = after_dn & green & ~(after_dn & green).shift(1).fillna(False).astype(bool)
    # P: skrajna cena impulsu i świec po nim (ostatnie 6 świec obejmują impuls + do 3 świece po nim)
    peak, trough = df.high.rolling(6).max(), df.low.rolling(6).min()
    # B przeniesiona na świecę sygnału: najstarsza z możliwych baz (impuls 1–3 świece temu → baza 4–6 świec temu)
    base_sig = df.close.shift(6)
    return short, long_, peak, trough, base_sig


def signals(df, p, ind):
    short, long_, *_ = _setup(df, p, ind)
    return long_.astype("int8") - short.astype("int8")


def levels(df, p, ind):
    short, long_, peak, trough, base_sig = _setup(df, p, ind)
    tp = pd.Series(np.nan, index=df.index)
    sl = pd.Series(np.nan, index=df.index)
    rng_s = (peak - base_sig).clip(lower=0)
    tp[short] = (peak - 0.5 * rng_s)[short]
    sl[short] = (peak + 0.25 * rng_s)[short]
    rng_l = (base_sig - trough).clip(lower=0)
    tp[long_] = (trough + 0.5 * rng_l)[long_]
    sl[long_] = (trough - 0.25 * rng_l)[long_]
    return pd.DataFrame({"tp": tp, "sl": sl})
