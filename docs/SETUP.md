# SETUP — kroki do kliknięcia (E0)

1. **GitHub Pages:** repo → Settings → Pages → Source: **GitHub Actions**.
2. **Firestore:** Firebase Console → projekt `project-ia5` → Build → Firestore Database → Create database (tryb produkcyjny, region `eur3`).
3. **Logowanie:** Build → Authentication → Sign-in method → **Google** → włącz. W Settings → Authorized domains dodaj `miszyszka.github.io`.
4. **Klucz dla Maca:** Project settings → Service accounts → Generate new private key → zapisz jako `~/.ia5/service-account.json`. Nigdy do repo ani do czatu (S3).
5. **Ograniczenie klucza API:** Google Cloud Console → APIs & Services → Credentials → klucz „Browser key" → HTTP referrers: `https://miszyszka.github.io/*`.
6. **Apps Script:** w arkuszu Google → Rozszerzenia → Apps Script. Kod wgram w E1 (przez `clasp`).
7. **UID właściciela:** zaloguj się na stronie (prawy górny róg) → kliknij avatar → „Kopiuj mój UID”.
   - Firebase → Firestore → **Rules**: wklej aktualny [`firestore.rules`](../firestore.rules), zamień `<OWNER_UID>` na swój UID → **Publish**.
   - Na Macu utwórz `~/.ia5/config.json` z treścią `{"owner_uid": "TWÓJ_UID"}` — bez tego `ia5` nie policzy strategii z dashboardu (S1).

## E2 — program na Macu lub Windows

### Mac

```bash
# raz: narzędzia (Homebrew: https://brew.sh)
brew install uv git
git clone https://github.com/miszyszka/IA5.git ~/IA5
cd ~/IA5 && uv tool install -e runner        # komenda `ia5` w terminalu

# klucz z kroku 4 musi leżeć w ~/.ia5/service-account.json
ia5 status                                   # sprawdzenie instalacji
ia5 start                                    # pierwszy raz: pobieranie Dukascopy trwa kilka godzin
```

- Aktualizacja programu: `cd ~/IA5 && git pull`.
- Pierwsze `ia5 start` można przerwać (Ctrl+C) i wznowić — gotowe miesiące się nie powtarzają.
- Push na gałąź `data` używa Twoich danych logowania do GitHub (np. `gh auth login`).

### Windows (wiersz poleceń `cmd`)

```bat
:: raz: uv (git już jest)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
:: zamknij i otwórz nowe okno cmd, potem:
git clone https://github.com/miszyszka/IA5.git %USERPROFILE%\IA5
cd /d %USERPROFILE%\IA5
uv tool install -e runner
:: klucz Firebase: %USERPROFILE%\.ia5\service-account.json
ia5 status
ia5 start
```

- Repo i dane trzymamy poza OneDrive (`%USERPROFILE%\IA5`, `%USERPROFILE%\.ia5`) — kilka GB danych nie powinno się synchronizować.
- Aktualizacja: `cd /d %USERPROFILE%\IA5 && git pull`.
