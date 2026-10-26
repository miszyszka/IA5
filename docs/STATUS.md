# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

## 2026-10-26 — sesja 1

**Zrobione**
- E0: `CLAUDE.md` v0.2, dziennik decyzji, szkielet repo, CI, Pages, reguły Firestore, `docs/SETUP.md`. Michał wykonał kroki z SETUP.
- E1 (kod): `apps_script/Code.gs` — backfill 730 dni, `tick()` co 5 min, upsert przez `commit`, kontrola jakości (OHLC, ts, luki, korekty, test krzyżowy), `meta/status` z latencją, log w arkuszu.
- Dashboard: pasek statusu na żywo (dane, latencja + mediana 24 h + wykres, liczba świec, Mac, flagi) i tabela par.
- E1 uruchomione przez Michała (Apps Script, reguły, wyjątek indeksu) — „wszystko jest".
- E2 (kod): `ia5 start` / `ia5 sync` — Dukascopy M1 → H1, sync Yahoo z Firestore, kontrole (OHLC, luki, trójkąty, Dukascopy vs Yahoo), publikacja świec Yahoo na gałąź `data`, heartbeat, caffeinate, nasłuch kolejki z kontrolą właściciela. 13 testów.

**Następne**
1. Michał: instalacja `ia5` na Macu (docs/SETUP.md, sekcja E2) i pierwsze `ia5 start` — potwierdzić format Dukascopy (D-011) na wynikach kontroli.
2. Zalogowanie przez Google na stronie → UID do `firestore.rules` i `~/.ia5/config.json`.
3. E3: silnik.

**Znane problemy / ryzyka**
- Yahoo bez oficjalnego API (tylko monitoring).
- Święta nie są w kalendarzu sesji (D-009).
- `clasp` jeszcze nieustawiony — na razie kod wklejany z repo; repo pozostaje źródłem prawdy.
- O5 (swapy) otwarte.
- Format plików Dukascopy sprawdzony tylko na danych syntetycznych (D-011).
