# IA5 — gałąź `data`

Tylko dane, bez kodu (CLAUDE.md, sekcja 4). Zapisuje ją program `ia5` na Macu; dashboard czyta stąd świece i wyniki.

- `candles/{PARA}/{RRRR}.parquet` — świece H1 z Yahoo (D-010)
- `results/index.json` — lista policzonych strategii
- `results/{id}/` — wyniki strategii: manifest, warianty, transakcje, walidacja, raport, kod

`results/demo-sma200-rsi/` to DEMO policzone na przykładowych świecach EUR/USD 2017–2018 z pakietu backtesting.py (AGPL-3.0) — usuwa się je w dashboardzie jak każdą strategię.
