// Firebase ładowane dynamicznie: gdy SDK albo sieć zawiedzie, dashboard nadal pokazuje wyniki z GitHub.
import { FIREBASE_SDK, NO_FIREBASE, firebaseConfig } from './config.js';

let apiP = null;

export function firebase() {
  if (NO_FIREBASE) return Promise.resolve(null);
  if (!apiP) {
    apiP = (async () => {
      try {
        const [App, A, F] = await Promise.all([
          import(`${FIREBASE_SDK}/firebase-app.js`),
          import(`${FIREBASE_SDK}/firebase-auth.js`),
          import(`${FIREBASE_SDK}/firebase-firestore.js`),
        ]);
        const app = App.initializeApp(firebaseConfig);
        return { auth: A.getAuth(app), db: F.getFirestore(app), A, F };
      } catch (e) {
        console.warn('Firebase niedostępne:', e);
        return null;
      }
    })();
  }
  return apiP;
}

export async function onUser(cb) {
  const fb = await firebase();
  if (!fb) return cb(null);
  fb.A.onAuthStateChanged(fb.auth, cb);
}

export async function login() {
  const fb = await firebase();
  if (!fb) throw new Error('Firebase niedostępne');
  await fb.A.signInWithPopup(fb.auth, new fb.A.GoogleAuthProvider());
}

export async function logout() {
  const fb = await firebase();
  if (fb) await fb.A.signOut(fb.auth);
}

/** Nasłuch jednego dokumentu (meta/status, runner/heartbeat) — Z2. */
export async function watchDoc(path, cb, onErr) {
  const fb = await firebase();
  if (!fb) return onErr?.({ code: 'brak-firebase' });
  const [col, id] = path.split('/');
  return fb.F.onSnapshot(fb.F.doc(fb.db, col, id), (s) => cb(s.exists() ? s.data() : null), (e) => onErr?.(e));
}

/** Nasłuch kolejki strategii (tylko właściciel — reguły S1). cb(docs | null, błąd). */
export async function watchStrategies(cb) {
  const fb = await firebase();
  if (!fb) return cb(null, { code: 'brak-firebase' });
  return fb.F.onSnapshot(fb.F.collection(fb.db, 'strategies'), (snap) => {
    const docs = {};
    snap.forEach((d) => {
      const v = d.data();
      if (v.createdAt?.seconds) v.createdAt = v.createdAt.seconds;
      docs[d.id] = v;
    });
    cb(docs, null);
  }, (e) => cb(null, e));
}

async function need() {
  const fb = await firebase();
  if (!fb) throw new Error('Firebase niedostępne — sprawdź połączenie.');
  const u = fb.auth.currentUser;
  if (!u) throw new Error('Zaloguj się (prawy górny róg).');
  return { fb, u };
}

export async function createStrategy({ name, hypothesis, code }) {
  const { fb, u } = await need();
  const ref = await fb.F.addDoc(fb.F.collection(fb.db, 'strategies'), {
    name, hypothesis, code, status: 'do_policzenia', createdBy: u.uid, createdAt: fb.F.serverTimestamp(),
  });
  return ref.id;
}

/** Zmiana dokumentu, a gdy go nie ma (np. strategia tylko z gałęzi data) — utworzenie z dozwolonym statusem. */
async function upsert(id, fields, createExtra) {
  const { fb, u } = await need();
  const ref = fb.F.doc(fb.db, 'strategies', id);
  const snap = await fb.F.getDoc(ref);
  if (snap.exists()) await fb.F.updateDoc(ref, fields);
  else await fb.F.setDoc(ref, { ...createExtra, ...fields, createdBy: u.uid, createdAt: fb.F.serverTimestamp() });
}

export const requestDelete = (id, name) => upsert(id, { status: 'do_usuniecia' }, { name });
export const requestRecalc = (id, { name, hypothesis, code }) => upsert(id, { status: 'do_policzenia', code, hypothesis }, { name });

export async function freeze(id, variantId) {
  const { fb } = await need();
  await fb.F.updateDoc(fb.F.doc(fb.db, 'strategies', id), { frozenAt: Math.floor(Date.now() / 1000), frozenVariant: variantId });
}

export async function unfreeze(id) {
  const { fb } = await need();
  await fb.F.updateDoc(fb.F.doc(fb.db, 'strategies', id), { frozenAt: null, frozenVariant: null });
}
