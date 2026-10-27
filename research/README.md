# research/ — badania przed strategią (D-036)

Hipotezę szukamy na **innych danych** niż te, na których Mac ją ocenia:

| etap | dane | rola |
|---|---|---|
| odkrycie | H1 brokera MT, 8 par, 2012-11 – 2022-03 ([ejtraderLabs/historical-data](https://github.com/ejtraderLabs/historical-data)); czas serwera = Nowy Jork + 7 h → UTC | szukanie efektu: połowa A ≤ 2017, potwierdzenie w B ≥ 2018 |
| ocena | Dukascopy M1 → H1 na Macu, 2003–2026 | niezależne źródło i 9 lat, których badanie nie widziało |

Dane tylko lokalnie (nie w repo, nie do backtestów — D7):

```bash
mkdir -p research/data && for p in EURUSD USDJPY GBPUSD EURGBP AUDUSD USDCHF USDCAD EURJPY; do
  curl -sS -o research/data/$p.csv https://raw.githubusercontent.com/ejtraderLabs/historical-data/main/$p/${p}h1.csv; done
cd research && python r1_intraday.py && python r2_europe.py && python r3_eurusd.py
```

## Wyniki 2026-10-27
- r1: ze wszystkich okien godzin × 8 par tylko EUR/USD w porannej sesji Europy ma ten sam znak w obu połowach, |t| > 2,5 / 2 i ruch > 1,5 × spread.
- r3: płaskowyż — start 06–09 czasu Londynu × 5–8 godzin dodatni w obu połowach (bez pojedynczego piku).
- r2: koszyk 6 par z USD po spreadzie ≈ 0 — efekt dotyczy euro, nie dolara.
- r3: ruch w Azji, poprzedni dzień, zmienność, dzień tygodnia — bez monotonicznej zależności → bez filtrów.
- Efekt słabnie: 2015 +4,8 pips/dzień, 2020–2021 +0,4…1,1. Dukascopy 2003–2012 to pierwszy prawdziwie niezależny test.
