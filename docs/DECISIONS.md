# DECISIONS — dziennik decyzji IA5

Każda decyzja architektoniczna: data, decyzja, powód, odrzucone alternatywy (zasada G5 w `CLAUDE.md`).
Najnowsze na górze.

---

### D-011 · 2026-10-26 · E2: zależności i układ plików M1
- **Decyzja:** runner używa `numpy`, `pandas`, `pyarrow`, `firebase-admin`; pobieranie Dukascopy własnym czytnikiem plików `bi5` (stdlib: `urllib`, `lzma`, `struct`), bez `dukascopy-node`. M1 zapisywane per miesiąc (`{RRRR-MM}.parquet`), żeby pierwsze pobieranie dało się przerwać i wznowić.
- **Powód:** mniej zależności (bez Node), wznawialność kilkugodzinnego pierwszego pobrania.
- **Do potwierdzenia na Macu:** kolejność pól w rekordzie (open, close, low, high) i punkt (1000 dla JPY, 100 000 dla reszty) — sprawdzone tylko na danych syntetycznych, bo serwer Dukascopy jest niedostępny z sesji Claude.

### D-010 · 2026-10-26 · O6: dane Dukascopy nie trafiają na publiczny GitHub
- **Decyzja:** M1 i H1 z Dukascopy zostają na Macu. Gałąź `data` dostaje świece H1 z Yahoo; wyniki strategii — tylko wycinki świec wokół transakcji.
- **Powód:** okno pobierania danych Dukascopy określa je jako użytek osobisty; publiczne repo to redystrybucja.
- **Odrzucone:** publikacja pełnej historii H1 z Dukascopy.

### D-009 · 2026-10-26 · Apps Script: zapis przez `documents:commit`, nie `PATCH`
- **Decyzja:** świece i status zapisywane przez endpoint `commit` z `updateMask` w treści żądania, nagłówek `x-goog-user-project: project-ia5`.
- **Powód:** `PATCH` wymaga listy pól w adresie URL — przy ~740 świecach w miesiącu adres przekracza limit długości UrlFetch. Nagłówek kieruje limity na projekt Firebase, a nie domyślny projekt skryptu.
- **Ograniczenie:** święta (np. 25 grudnia) nie są w kalendarzu sesji — tego dnia status pokaże STOI. Do poprawy, gdy będzie przeszkadzać.

### D-008 · 2026-10-26 · Wielkość pozycji: % kapitału jako depozyt, domyślnie 5/10/15/20/30%
- **Decyzja:** depozyt = X% kapitału, nominał = 5 × depozyt (dźwignia 1:5). Domyślnie liczymy X ∈ {5, 10, 15, 20, 30}%; strategia może podać własne (`SIZING`). Suma depozytów otwartych pozycji ≤ 100% kapitału; sygnał bez wolnego depozytu pomijany i liczony.
- **Powód:** Michał: „zależy od strategii, domyślnie zawsze kilka opcji 5, 10, 15, 20, 30% kapitału". Limit depozytu utrzymuje łączną ekspozycję ≤ 1:5.
- **Interpretacja do potwierdzenia:** „X% kapitału" rozumiane jako depozyt (nominał 5 × X%). Jeśli Michał miał na myśli nominał — zmienić B4 i 8.5.
- **Odrzucone:** sloty po równo; pełna dźwignia na każdą pozycję (łamie 1:5 przy nakładaniu); stałe ryzyko na SL.
- Wielkość pozycji to przełącznik w karcie, nie wariant w rankingu — nie mnoży liczby prób w DSR/PBO.

### D-007 · 2026-10-26 · Dwa źródła danych o rozdzielonych rolach
- **Decyzja:** Dukascopy M1 bid/ask = jedyne źródło do backtestów i forward testów (świece H1 budowane lokalnie z M1). Yahoo → Apps Script → Firestore = monitoring na żywo i niezależna kontrola danych.
- **Powód:** Yahoo daje świece 1h tylko z ostatnich 730 dni i bez bid/ask. Dukascopy daje kilkanaście lat historii i M1, co pozwala rozstrzygnąć kolejność TP/SL wewnątrz świecy H1.
- **Odrzucone:** tylko Yahoo (za krótka historia, brak rozstrzygania wewnątrz świecy); sklejanie obu źródeł w jedną serię (szew między różnymi feedami fałszuje wyniki).
- **Otwarte (O6):** czy warunki Dukascopy pozwalają publikować zbudowane świece H1 na publicznej gałęzi `data`.

### D-006 · 2026-10-26 · Wyniki i kod strategii publiczne
- **Decyzja:** wyniki na publicznej gałęzi `data` repo IA5.
- **Powód:** Michał: „publiczne są OK". Najprostsze, bez kosztów.
- **Odrzucone:** wyniki w Firestore za logowaniem (koszt odczytów); Firebase Storage (wymaga planu Blaze).

### D-005 · 2026-10-26 · Waluta konta USD
- **Decyzja:** kapitał i wyniki w USD, start 10 000 USD.
- **Powód:** wszystkie przeliczenia możliwe z naszych 8 par, bez dodatkowej serii.

### D-004 · 2026-10-26 · Model wykonania
- **Decyzja:** sygnał na zamknięciu świecy, wejście na open następnej; TP/SL w tej samej świecy rozstrzygane na M1, w tej samej minucie → SL; luki: SL po open, TP po poziomie; spread raz na transakcję.
- **Powód:** brak look-ahead i konserwatywne założenia tam, gdzie dane nie rozstrzygają.

### D-003 · 2026-10-26 · Dashboard czyta świece i wyniki z GitHub, nie z Firestore
- **Decyzja:** gałąź `data` (Parquet, JSON, raport) czytana przez `raw.githubusercontent.com` z SHA w adresie. Z Firestore dashboard czyta tylko `meta/status`, `runner/heartbeat`, `strategies`.
- **Powód:** darmowy plan Firebase (50 000 odczytów / 20 000 zapisów dziennie); pliki z wynikami przekraczają limit 1 MiB na dokument.

### D-002 · 2026-10-26 · Świece w Firestore: 1 dokument = 1 para × 1 miesiąc
- **Decyzja:** mapa `bars` kluczowana `ts`, zapis `PATCH` z `updateMask` (idempotentnie, bez odczytu), wyłączone indeksowanie `bars`.
- **Powód:** backfill ok. 200 zapisów zamiast ok. 100 tys.; bieżąca praca ok. 200 zapisów dziennie.
- **Odrzucone:** 1 świeca = 1 dokument (limit zapisów); tablice z `arrayUnion` (usuwa powtarzające się ceny).

### D-001 · 2026-10-26 · Apps Script co 5 min zamiast co godzinę
- **Decyzja:** wyzwalacz co 5 min; skrypt kończy bez zapytań, gdy oczekiwana świeca jest już zapisana.
- **Powód:** wyzwalacz godzinowy odpala się w dowolnej minucie godziny, więc pomiar latencji w sekundach nie miałby sensu.
