# SETUP — kroki do kliknięcia (E0)

1. **GitHub Pages:** repo → Settings → Pages → Source: **GitHub Actions**.
2. **Firestore:** Firebase Console → projekt `project-ia5` → Build → Firestore Database → Create database (tryb produkcyjny, region `eur3`).
3. **Logowanie:** Build → Authentication → Sign-in method → **Google** → włącz. W Settings → Authorized domains dodaj `miszyszka.github.io`.
4. **Klucz dla Maca:** Project settings → Service accounts → Generate new private key → zapisz jako `~/.ia5/service-account.json`. Nigdy do repo ani do czatu (S3).
5. **Ograniczenie klucza API:** Google Cloud Console → APIs & Services → Credentials → klucz „Browser key" → HTTP referrers: `https://miszyszka.github.io/*`.
6. **Apps Script:** w arkuszu Google → Rozszerzenia → Apps Script. Kod wgram w E1 (przez `clasp`).
7. Po pierwszym logowaniu na stronie podam Ci, jak odczytać swój UID — wpiszemy go do `firestore.rules` i wdrożymy reguły.

## E2 — program na Macu

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
