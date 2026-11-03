// IA5 — dashboard. Router: #/ (strategie), #/s/{id} (karta), #/stats, #/inwestorzy, #/inwestorzy/{id} (D-045), #/forest (D-048).
import { openCard } from './card.js';
import { getJSON, refreshData } from './data.js';
import { login, logout, onUser, watchInvestors, watchStrategies } from './fb.js';
import { initForest, loadForest, renderForest } from './forest.js';
import { initInvestors, loadInvestors, renderInvestors } from './investors.js';
import { initList, renderList } from './list.js';
import { initStats, renderStats } from './stats.js';
import { initStatus } from './status.js';
import { $, $$, copy, h, store, toast } from './util.js';

function route() {
  const hash = location.hash || '#/';
  const m = hash.match(/^#\/s\/(.+)$/);
  const mi = hash.match(/^#\/inwestorzy\/(.+)$/);
  const r = m ? { view: 'card', id: decodeURIComponent(m[1]) }
    : mi ? { view: 'investors', id: decodeURIComponent(mi[1]) }
      : hash.startsWith('#/inwestorzy') ? { view: 'investors' } : hash.startsWith('#/forest') ? { view: 'forest' }
        : hash.startsWith('#/stats') ? { view: 'stats' } : { view: 'list' };
  store.set('route', r);
  $$('.view').forEach((v) => { v.hidden = v.id !== `view-${r.view}`; });
  const tab = { investors: 'investors', stats: 'stats', forest: 'forest' }[r.view] || 'strategies';
  $$('nav [data-tab]').forEach((b) => { b.classList.toggle('on', b.dataset.tab === tab); if (b.dataset.tab === tab) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
  if (r.view === 'list') renderList();
  if (r.view === 'card') openCard(r.id);
  if (r.view === 'stats') renderStats();
  if (r.view === 'investors') renderInvestors();
  if (r.view === 'forest') renderForest();
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
    box.replaceChildren(h('button', { id: 'login', class: 'btn', onclick: () => login().catch((e) => toast(e.message || String(e), 'bad', 15000)), title: 'Zaloguj kontem Google' }, 'Zaloguj'));
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

let unsubDocs = null, unsubInv = null;
async function start() {
  initStatus();
  initList();
  initStats();
  initInvestors();
  initForest();
  window.addEventListener('hashchange', route);
  route();
  loadIndex();
  loadInvestors();
  loadForest();
  onUser(async (user) => {
    store.set('user', user);
    renderAuth(user);
    unsubDocs?.();
    unsubInv?.();
    unsubDocs = unsubInv = null;
    store.set('docs', null);
    store.set('docsError', null);
    store.set('invDocs', null);
    store.set('invDocsError', null);
    if (!user) return;
    unsubInv = await watchInvestors((docs, err) => {
      if (err) { store.set('invDocsError', err); return; }
      store.set('invDocsError', null);
      store.set('invDocs', docs);
    });
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
  store.on('beat', (b) => { if (prev === 'computing' && b?.state === 'idle') { refreshData(); loadIndex(); loadInvestors(); loadForest(); } prev = b?.state; });
  // inwestorzy przeliczani co godzinę po kopii świec — co 10 min sprawdzamy, czy na gałęzi data jest nowy stan
  setInterval(() => { refreshData(); loadInvestors(); loadForest(); }, 10 * 60 * 1000);
}

start();
