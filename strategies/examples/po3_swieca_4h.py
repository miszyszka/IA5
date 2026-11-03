HYPOTHESIS = """Power of 3 / „knot świecy 4H” (wg filmu: akumulacja → manipulacja → dystrybucja). Gdy dzienny kierunek jest
wzrostowy, nowa świeca 4H zwykle najpierw robi dolny knot (fałszywy ruch w dół, który zbiera płynność pod ważnym
dołkiem), a potem zamyka się wysoko. Wchodzimy long, gdy w pierwszych godzinach nowej świecy 4H cena zebrała dołek
(poprzedniej świecy 4H albo ostatnich 24 h), a świeca H1 zamyka się z powrotem nad nim (zmiana kierunku). Lustrzanie short.
Różnice (ograniczenia IA5): tylko H1 (autor wchodzi na 1 min po luce FVG i „zmianie stanu dostawy”); stop „pod dołkiem
świecy 4H” i cel przybliżone przez ATR14 albo wyjście na koniec świecy 4H (2–4 świece H1)."""

import numpy as np
import pandas as pd

PARAMS = {
    "bias": ["dzien", "brak"],          # dzien: wczorajsza świeca dzienna wzrostowa → tylko long (spadkowa → short)
    "dolek": ["4h", "24h"],             # zebrany poziom: dołek/szczyt poprzedniej świecy 4H albo ostatnich 24 h
}

# koniec świecy 4H (po 2–4 h) albo TP/SL w ATR14 (stop pod dołkiem ≈ 1 ATR)
EXITS = [{"kind": "time", "n": n, "cap": n} for n in (2, 3, 4)] + \
        [{"kind": "atr", "n": 14, "tp": tp, "sl": 1.0, "cap": 24} for tp in (1.0, 1.5, 2.0)]


def signals(df, p, ind):
    h, lo, o, c = df.high, df.low, df.open, df.close
    blk = df.index.floor("4h")                       # świece 4H od 00:00 UTC
    pos = ((df.index - blk) / pd.Timedelta(hours=1)).astype(int)
    g = pd.Series(blk, index=df.index)
    blk_low = lo.groupby(g).cummin()                 # dołek bieżącej świecy 4H do tej godziny
    blk_high = h.groupby(g).cummax()
    if p["dolek"] == "4h":
        b4h = h.groupby(g).max().shift(1)
        b4l = lo.groupby(g).min().shift(1)
        lvl_lo = b4l.reindex(blk).set_axis(df.index)  # poprzednia, zamknięta świeca 4H
        lvl_hi = b4h.reindex(blk).set_axis(df.index)
    else:
        lvl_lo = lo.shift(1).rolling(24).min().where(pos == 0).ffill()
        lvl_hi = h.shift(1).rolling(24).max().where(pos == 0).ffill()
    early = pos <= 2                                  # pierwsze 3 godziny świecy 4H
    bull = early & (blk_low < lvl_lo) & (c > lvl_lo) & (c > o)
    bear = early & (blk_high > lvl_hi) & (c < lvl_hi) & (c < o)
    if p["bias"] == "dzien":
        day = df.index.floor("D")
        dg = pd.Series(day, index=df.index)
        d_up = (c.groupby(dg).last() > o.groupby(dg).first()).shift(1)
        up = d_up.reindex(day).set_axis(df.index).fillna(False).astype(bool)
        dn = (~up) & d_up.reindex(day).set_axis(df.index).notna()
        bull &= up
        bear &= dn
    s = bull.astype("int8") - bear.astype("int8")
    first = (s != 0).astype(int).groupby(g).cumsum() == 1   # jeden sygnał na świecę 4H
    return s.where(first & (s != 0), 0).astype("int8")
