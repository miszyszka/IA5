# STATUS — stan prac IA5

Aktualizowany na koniec każdej sesji (zasada G5 w `CLAUDE.md`).

## 2026-10-26 — sesja 1

**Zrobione**
- `CLAUDE.md` v0.2: cel, żelazne zasady, architektura, model danych, kontrakt strategii, silnik, walidacja, dashboard, design, etapy.
- Decyzje O1–O4 zapisane (`docs/DECISIONS.md`).
- Repo: `CLAUDE.md`, `docs/`, `.gitignore`, `README.md`.

**Następne (E0 → E1)**
1. Szkielet repo (sekcja 12): `web/`, `apps_script/`, `runner/`, `tests/`, `firestore.rules`, CI (`pytest`, lint) i wdrażanie Pages przez Actions.
2. Kroki do kliknięcia przez Michała (Firebase: Firestore, Auth Google, service account, ograniczenie klucza API; Apps Script; Pages) — Claude prowadzi krok po kroku.
3. E1: Apps Script — backfill 730 dni, `tick()` co 5 min, `meta/status`, log w arkuszu, kontrola jakości.

**Znane problemy / ryzyka**
- Yahoo nie ma oficjalnego API; nieoficjalne zapytania bywają przycinane (dotyczy tylko monitoringu, nie backtestów).
- O6: warunki Dukascopy co do publikowania świec zbudowanych z ich danych — sprawdzić w E2.
- O5: swapy pominięte (0).
