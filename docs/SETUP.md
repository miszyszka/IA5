# SETUP — kroki do kliknięcia (E0)

1. **GitHub Pages:** repo → Settings → Pages → Source: **GitHub Actions**.
2. **Firestore:** Firebase Console → projekt `project-ia5` → Build → Firestore Database → Create database (tryb produkcyjny, region `eur3`).
3. **Logowanie:** Build → Authentication → Sign-in method → **Google** → włącz. W Settings → Authorized domains dodaj `miszyszka.github.io`.
4. **Klucz dla Maca:** Project settings → Service accounts → Generate new private key → zapisz jako `~/.ia5/service-account.json`. Nigdy do repo ani do czatu (S3).
5. **Ograniczenie klucza API:** Google Cloud Console → APIs & Services → Credentials → klucz „Browser key" → HTTP referrers: `https://miszyszka.github.io/*`.
6. **Apps Script:** w arkuszu Google → Rozszerzenia → Apps Script. Kod wgram w E1 (przez `clasp`).
7. Po pierwszym logowaniu na stronie podam Ci, jak odczytać swój UID — wpiszemy go do `firestore.rules` i wdrożymy reguły.
