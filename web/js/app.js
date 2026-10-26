// IA5 — dashboard. Router: #/ (strategie), #/s/{id} (karta), #/inwestorzy.
import { openCard } from './card.js';
import { getJSON, refreshData } from './data.js';
import { login, logout, onUser, watchStrategies } from './fb.js';
import { initList, renderList } from './list.js';
import { initStatus } from './status.js';
import { $, $$, copy, h, store, toast } from './util.js';

function route() {
  const hash = location.hash || '#/';
  const m = hash.match(/^#\/s\/(.+)$/);
  const r = m ? { view: 'card', id: decodeURIComponent(m[1]) } : hash.startsWith('#/inwestorzy') ? { view: 'investors' } : { view: 'list' };
  store.set('route', r);
  $$('.view').forEach((v) => { v.hidden = v.id !== `view-${r.view}`; });
  $$('nav [data-tab]').forEach((b) => b.classList.toggle('on', b.dataset.tab === (r.view === 'investors' ? 'investors' : 'strategies')));
  if (r.view === 'list') renderList();
  if (r.view === 'card') openCard(r.id);
  window.scrollTo(0, 0);
}

async function loadIndex() {
  try {
    const idx = await getJSON('results/index.json');
    store.set('indexError', null);
    store.set('index', idx?.strategies || []);
  } catch (e) {
    store.set('indexError', e.message || String(e));
    store.set('index', []);
  }
}

function renderAuth(user) {
  const box = $('#auth');
  if (!user) {
    box.replaceChildren(h('button', { id: 'login', class: 'btn', onclick: () => login().catch((e) => toast(e.message || String(e), 'bad', 7000)) }, 'Zaloguj (Google)'));
    return;
  }
  const menu = h('div', { class: 'menu', hidden: true },
    h('div', { class: 'hint' }, user.email),
    h('button', { class: 'btn ghost small', onclick: async () => toast((await copy(user.uid)) ? `Skopiowano UID: ${user.uid}` : user.uid, 'ok', 7000) }, 'Kopiuj mój UID'),
    h('button', { class: 'btn ghost small', onclick: () => logout() }, 'Wyloguj'));
  const btn = h('button', { class: 'avatar', 'aria-label': 'Konto', onclick: () => { menu.hidden = !menu.hidden; } },
    user.photoURL ? h('img', { src: user.photoURL, alt: '', referrerpolicy: 'no-referrer' }) : (user.email || '?')[0].toUpperCase());
  box.replaceChildren(btn, menu);
}

let unsubDocs = null;
async function start() {
  initStatus();
  initList();
  window.addEventListener('hashchange', route);
  route();
  loadIndex();
  onUser(async (user) => {
    store.set('user', user);
    renderAuth(user);
    unsubDocs?.();
    unsubDocs = null;
    store.set('docs', null);
    store.set('docsError', null);
    if (!user) return;
    let lastResults = '';
    unsubDocs = await watchStrategies((docs, err) => {
      if (err) { store.set('docsError', err); return; }
      store.set('docsError', null);
      store.set('docs', docs);
      // nowy wynik na gałęzi data → odśwież indeks (adres z nowym SHA)
      const sig = Object.entries(docs).map(([id, d]) => `${id}:${d.status}:${d.result?.sha || ''}`).join('|');
      if (sig !== lastResults) {
        const changed = lastResults && Object.values(docs).some((d) => d.status === 'policzona');
        lastResults = sig;
        if (changed) { refreshData(); loadIndex(); }
      }
    });
  });
  // gdy Mac skończy liczyć, heartbeat wraca do „idle” — odśwież wyniki
  let prev = null;
  store.on('beat', (b) => { if (prev === 'computing' && b?.state === 'idle') { refreshData(); loadIndex(); } prev = b?.state; });
}

start();
