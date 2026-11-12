import numpy as np
import pandas as pd

HYPOTHESIS = """Poniedziałkowy powrót. Przed weekendem rynek pozbywa się ryzyka: kto jest po złej stronie ruchu, zamyka pozycje
do piątkowego zamknięcia i dopycha kurs dalej, niż uzasadniają to informacje. W poniedziałek ten wymuszony ruch się cofa.
Wejście: para rozciągnięta na zamknięciu piątku (RSI2 dziennych zamknięć z 16:00 w Nowym Jorku poniżej progu → kupno,
powyżej 100 − próg → sprzedaż), wejście w poniedziałek o 01:00 czasu Londynu (rynek w Tokio już otwarty), wyjście po czasie.
Efekt znaleziony na danych niezależnych od danych IA5 (świece dzienne 2003–2019 i świece godzinowe brokera 2012–2022);
w inne dni tygodnia go nie ma. Lista wariantów ustalona przed pierwszym policzeniem na świecach Yahoo H1 (research/rynek/)."""

PARAMS = {"prog": [10, 15, 20]}          # RSI2 < próg → long; RSI2 > 100 − próg → short
EXITS = [{"kind": "time", "n": n, "cap": n} for n in (12, 20, 30)]   # wyjście po 12 / 20 / 30 godzinach od wejścia
HOURS = False                             # wejście o 01:00 Londynu (02:00 czasu polskiego) — poza oknem 07–17 (B11)


def signals(df, p, ind):
    ny = df.index.tz_convert("America/New_York")
    lon = df.index.tz_convert("Europe/London")
    # dzienne zamknięcie = ostatnia świeca przed 16:00 w Nowym Jorku (przed godziną rolowania), dni pon–pt
    sesja = np.asarray((ny.hour <= 15) & (ny.dayofweek < 5))
    dzien = ny.normalize().tz_localize(None)
    zamkniecia = df.close[sesja].groupby(dzien[sesja]).last()
    rsi = ind.rsi(zamkniecia, 2)
    piatki = rsi[rsi.index.dayofweek == 4]
    # świeca sygnału: poniedziałek 00:00 Londynu (wejście na open świecy 01:00); piątek = 3 dni wcześniej
    sygnal = np.asarray((lon.dayofweek == 0) & (lon.hour == 0))
    piatek = lon.normalize().tz_localize(None) - pd.Timedelta(days=3)
    r = pd.Series(piatki.reindex(piatek).to_numpy(), index=df.index)
    long_ = sygnal & (r < p["prog"])
    short = sygnal & (r > 100 - p["prog"])
    return long_.astype("int8") - short.astype("int8")
