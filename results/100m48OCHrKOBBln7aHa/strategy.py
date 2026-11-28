import numpy as np
import pandas as pd

HYPOTHESIS = """Wybicie z ściśnięcia z celem dopasowanym do prognozy zasięgu (D-076, zakładka Zasięg).
Kierunku nie przewidujemy — przewidujemy, JAK DALEKO rynek może dojść: zmienność skupia się w czasie i wraca do średniej,
więc zasięg najbliższych 3 dni da się prognozować (model HAR na dziennych zakresach, ind.range_forecast). Gdy na H1 rynek
stoi w wąskim pudełku z 24 godzin (wysokość w dolnych 20% z ostatnich 500 godzin), zlecenia stoją po obu stronach i to
wybicie wybiera kierunek: zamknięcie godziny nad pudełkiem = long, pod nim = short. Stop za drugą stroną pudełka
(gdy cel byłby wtedy nieosiągalny — w połowie pudełka), cel = 2 / 3 / 4 × stop. Wejście tylko wtedy, gdy cel mieści się
w prognozowanym zasięgu 3 dni — inaczej TP 3 × SL i tak zwykle by nie padł. Płatnik: uczestnicy, których stopy i zlecenia
stoją tuż za granicą konsolidacji, a po wybiciu muszą gonić cenę."""

PARAMS = {"tp": [2, 3, 4]}     # TP = tyle × odległość do SL (3 = reguła Michała, 2 i 4 — porównanie)
BOX, REF, PCT = 24, 500, 20    # pudełko z 24 godzin; ściśnięte = wysokość w dolnych 20% z ostatnich 500 godzin
H = 3                          # prognoza zasięgu na 3 najbliższe dni
EXITS = [{"kind": "level", "cap": 72}]   # TP i SL z levels(); najwyżej 72 godziny (horyzont prognozy)


def _ksiega(df, p, ind):
    """Kierunek (+1/−1/0) i ceny SL/TP na zamknięciu świecy sygnału."""
    n = len(df)
    zero = np.zeros(n)
    d = ind.d1(df)
    if d is None or len(d) < 300:
        return zero, np.full(n, np.nan), np.full(n, np.nan)
    zasieg = ind.d1_to_h1(df, ind.range_forecast(d, H)["mid"]).to_numpy(float)   # prognoza 3 dni, znana od zamknięcia dnia
    sq = ind.squeeze(df, BOX, REF)
    up, lo, pct = (sq[k].shift(1).to_numpy(float) for k in ("upper", "lower", "pct"))   # pudełko SPRZED świecy wybicia
    c = df["close"].to_numpy(float)
    m = float(p["tp"])
    with np.errstate(invalid="ignore"):
        scisk = pct <= PCT
        dlugi = scisk & (c > up)
        krotki = scisk & (c < lo)
        srodek = (up + lo) / 2
        sl = np.where(dlugi, lo, np.where(krotki, up, np.nan))
        # stop za drugą stroną; gdy cel byłby poza prognozą zasięgu — stop w połowie pudełka
        za_daleko = m * np.abs(c - sl) > zasieg
        sl = np.where(za_daleko, srodek, sl)
        ryzyko = np.abs(c - sl)
        ok = (dlugi | krotki) & (ryzyko > 0) & (m * ryzyko <= zasieg)
    kier = np.where(ok, np.where(dlugi, 1, -1), 0)
    tp = np.where(ok, c + kier * m * ryzyko, np.nan)
    return kier, np.where(ok, sl, np.nan), tp


def signals(df, p, ind):
    kier, _, _ = _ksiega(df, p, ind)
    return pd.Series(kier, index=df.index).astype("int8")


def levels(df, p, ind):
    _, sl, tp = _ksiega(df, p, ind)
    return pd.DataFrame({"tp": tp, "sl": sl}, index=df.index)