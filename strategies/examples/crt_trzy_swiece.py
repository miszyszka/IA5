HYPOTHESIS = """CRT (Candle Range Theory, „Nitro Trades”), przeniesione na H1 i FX. Świeca 1 wyznacza zakres (high–low).
Świeca 2 wybija jego dołek (zbiera zlecenia kupujących), ale zamyka się z powrotem w zakresie — sprzedający nie
mieli siły. Świeca 3 wybija szczyt świecy 2: potwierdzenie, że rynek „dowozi” zlecenia na drugą stronę zakresu,
do szczytu świecy 1. Lustrzanie dla short. Autor: cel = przeciwny koniec zakresu świecy 1, stop tak, by zysk/ryzyko
= 1,5, sesja Nowy Jork 9:30–12:00 ET, tylko pierwszy układ dnia, kierunek zgodny z ostatnim zebraniem płynności H1.
Różnice (ograniczenia IA5): tylko H1 (bez 15/30 min i bez „rebreak” na 1 min); wejście na open świecy po zamknięciu
świecy 3 ponad szczytem świecy 2 (silnik nie zna zleceń stop w trakcie świecy); cel i stop jako wielokrotności ATR14
w proporcji 1,5 : 1 zamiast poziomów ceny (silnik nie przyjmuje TP/SL z sygnału)."""

import numpy as np
import pandas as pd

HOURS = (15, 18)   # wejścia 15:00–17:59 czasu polskiego ≈ 9:00–11:59 ET (sesja Nowy Jork autora)

PARAMS = {
    "bias": ["brak", "zebranie"],   # zebranie = ostatnie 24 h zebrały dołek/szczyt poprzednich 24 h i cena wróciła
    "pierwsza": [True, False],      # tylko pierwszy układ dnia (jak autor) albo każdy
}

# zysk / ryzyko = 1,5 (cel 1,5 × stop), bez innych wyjść; limit 24 świec
EXITS = [{"kind": "atr", "n": 14, "tp": tp, "sl": round(tp / 1.5, 3), "cap": 24} for tp in (0.75, 1.0, 1.5, 2.0)]


def signals(df, p, ind):
    h, lo, c = df.high, df.low, df.close
    h1, l1 = h.shift(2), lo.shift(2)                 # świeca 1
    h2, l2, c2 = h.shift(1), lo.shift(1), c.shift(1)  # świeca 2
    inside = (c2 > l1) & (c2 < h1)
    bull = (l2 < l1) & inside & (c > h2)             # świeca 2 zebrała dołek, świeca 3 zamknęła ponad jej szczytem
    bear = (h2 > h1) & inside & (c < l2)
    if p["bias"] == "zebranie":
        prev_low = lo.shift(24).rolling(24).min()     # dołek poprzednich 24 h
        prev_high = h.shift(24).rolling(24).max()
        swept_low = (lo.rolling(24).min() < prev_low) & (c > prev_low)
        swept_high = (h.rolling(24).max() > prev_high) & (c < prev_high)
        bull &= swept_low & ~swept_high
        bear &= swept_high & ~swept_low
    s = bull.astype("int8") - bear.astype("int8")
    if p["pierwsza"]:                                # pierwszy układ w oknie danego dnia (wejście na następnej świecy)
        nxt = (df.index + pd.Timedelta(hours=1)).tz_convert("Europe/Warsaw")
        ok = (nxt.hour >= 15) & (nxt.hour < 18)
        s = s.where(ok, 0)
        day = pd.Series(nxt.normalize(), index=df.index)
        first = (s != 0).astype(int).groupby(day).cumsum() == 1
        s = s.where(first & (s != 0), 0)
    return s.astype("int8")
