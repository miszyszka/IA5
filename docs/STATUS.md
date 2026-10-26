# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

## 2026-10-26 — sesja 1

**Zrobione**
- E0: `CLAUDE.md` v0.2, dziennik decyzji, szkielet repo, CI, Pages, reguły Firestore, `docs/SETUP.md`. Michał wykonał kroki z SETUP.
- E1 (kod): `apps_script/Code.gs` — backfill 730 dni, `tick()` co 5 min, upsert przez `commit`, kontrola jakości (OHLC, ts, luki, korekty, test krzyżowy), `meta/status` z latencją, log w arkuszu.
- Dashboard: pasek statusu na żywo (dane, latencja + mediana 24 h + wykres, liczba świec, Mac, flagi) i tabela par.

**Następne**
1. Michał: reguły Firestore, wyjątek indeksu `bars`, wklejenie skryptu, `setup()`.
2. Sprawdzić backfill i tickery Yahoo (zwłaszcza `JPY=X`, `CHF=X`, `CAD=X`), wyrównanie ts do pełnej godziny.
3. Zalogowanie przez Google na stronie → UID do `firestore.rules`.
4. E2: program na Macu.

**Znane problemy / ryzyka**
- Yahoo bez oficjalnego API (tylko monitoring).
- Święta nie są w kalendarzu sesji (D-009).
- `clasp` jeszcze nieustawiony — na razie kod wklejany z repo; repo pozostaje źródłem prawdy.
- O5 (swapy), O6 (warunki Dukascopy) otwarte.
