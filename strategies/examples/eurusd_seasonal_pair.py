HYPOTHESIS = """Dwie sezonowości EUR/USD, obie wskazane przez skaner hipotez (D-037) na latach 2003–2020 i obie z
mechanizmem znanym z literatury: (1) euro słabnie w porannej sesji europejskiej (Breedon i Ranaldo 2013) —
short 07:00–13:00 Londynu, każdy dzień roboczy, dodatni w 15 z 18 lat; (2) dolar słabnie w nocy w grudniu
(koniec roku: zamykanie pozycji i finansowanie dolarowe przed bilansami) — long 01:00–07:00 Londynu tylko w grudniu,
dodatni w 17 z 18 lat. Ostatnie 25% historii (2021–2026) skaner pominął — to prawdziwy test."""

HOURS = False   # grudniowe wejście o 01:00 Londynu jest poza oknem B11 — wyjątek tylko za zgodą Michała (D-034)

PARAMS = {"grudzien": [False, True]}       # bez / z grudniowym składnikiem — porównanie w jednym liczeniu
EXITS = [{"kind": "time", "n": 6, "cap": 6}]   # oba składniki: 6 godzin (grudzień kończy się o 07:00, zanim rusza poranek)


def signals(df, p, ind):
    out = df.close * 0
    if df.attrs.get("pair") != "EURUSD":       # reguły znalezione tylko dla EUR/USD
        return out.astype("int8")
    london = df.index.tz_convert("Europe/London")
    weekday = london.dayofweek < 5
    # sygnał na zamknięciu świecy godzinę wcześniej → wejście na open świecy o pełnej godzinie (B1)
    morning = weekday & (london.hour == 6)                       # wejście 07:00, short
    out[morning] = -1
    if p["grudzien"]:
        december = weekday & (london.month == 12) & (london.hour == 0)   # wejście 01:00, long
        out[december] = 1
    return out.astype("int8")
