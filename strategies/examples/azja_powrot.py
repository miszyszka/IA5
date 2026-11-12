import numpy as np
import pandas as pd

HYPOTHESIS = """Powrót w sesji azjatyckiej. Po zamknięciu Londynu płynność spada, a późnym popołudniem w Nowym Jorku (godzina
rolowania pozycji) wystarczy niewielki przepływ, żeby przesunąć kurs. Gdy rynek w Tokio się otwiera i płynność wraca, ruch
z ostatnich 4 godzin przed północą w Londynie częściowo się cofa — do otwarcia Londynu. Wejście przeciw temu ruchowi o 00:00
czasu Londynu, tylko gdy był wyraźny (próg w ATR), wyjście po czasie. Efekt słabszy niż poniedziałkowy powrót i wąski
(działa dla okna 4 godzin, nie dla 2 ani 6) — znaleziony na niezależnych świecach brokera 2012–2022 (research/rynek/)."""

PARAMS = {"prog": [0.5, 0.75, 1.0]}       # ruch z 4 godzin większy niż próg × ATR24 × 2
EXITS = [{"kind": "time", "n": n, "cap": n} for n in (4, 8, 10)]     # wyjście po 4 / 8 / 10 godzinach (8 h = otwarcie Londynu)
HOURS = False                              # wejście o 00:00 Londynu (01:00 czasu polskiego) — poza oknem 07–17 (B11)


def signals(df, p, ind):
    lon = df.index.tz_convert("Europe/London")
    ruch = (df.close - df.close.shift(4)) / (ind.atr(df, 24) * 2)
    sygnal = pd.Series(np.asarray(lon.hour == 23), index=df.index)       # świeca 23:00 → wejście na open świecy 00:00
    long_ = sygnal & (ruch < -p["prog"])
    short = sygnal & (ruch > p["prog"])
    return long_.astype("int8") - short.astype("int8")
