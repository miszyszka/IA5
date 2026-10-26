// Zakładka Strategie: lista = wyniki z gałęzi data + kolejka w Firestore (CLAUDE.md 10.3).
import { openEditor } from './editor.js';
import { requestDelete } from './fb.js';
import { mergeStrategies } from './metrics.js';
import { heartbeatState } from './status.js';
import { $, confirmDialog, copy, dateUTC, esc, h, num, signed, store, toast } from './util.js';

const VERDICT = { green: ['ok', 'zielony'], yellow: ['warn', 'żółty'], red: ['bad', 'czerwony'] };
const SORTS = {
  created: (a, b) => (b.created || 0) - (a.created || 0),
  verdict: (a, b) => rankV(a) - rankV(b) || (b.result?.oos_mean_r ?? -9) - (a.result?.oos_mean_r ?? -9),
  oos: (a, b) => (b.result?.oos_mean_r ?? -9) - (a.result?.oos_mean_r ?? -9),
  name: (a, b) => a.name.localeCompare(b.name, 'pl'),
};
const rankV = (s) => ({ green: 0, yellow: 1, red: 2 })[s.result?.verdict] ?? 3;
let query = '', sort = 'created';

export async function deleteStrategy(s) {
  if (!store.state.user) { toast('Zaloguj się, żeby usuwać strategie.', 'warn'); return false; }
  const ok = await confirmDialog(`Usunąć „${s.name}”?`,
    'Strategia zniknie z listy od razu. Pliki wyników usunie program ia5 na Macu (od razu, jeśli działa, albo przy najbliższym uruchomieniu).',
    'Usuń', true);
  if (!ok) return false;
  try {
    await requestDelete(s.id, s.name);
    const hid = new Set(store.state.hidden || []);
    hid.add(s.id);
    store.set('hidden', hid);
    toast(`Usunięto „${s.name}” z listy.`, 'ok');
    return true;
  } catch (e) {
    toast(e.message || String(e), 'bad', 7000);
    return false;
  }
}

function stateChip(s, beat) {
  if (s.state === 'queued') return h('span', { class: 'chip warn' }, heartbeatState(beat).online ? 'w kolejce' : 'czeka na Maca');
  if (s.state === 'running') {
    const job = beat?.job?.id === s.id ? beat.job : null;
    return h('span', { class: 'chip run' }, `liczy się${job ? ` · ${job.progress ?? 0}%` : '…'}`);
  }
  if (s.state === 'error') return h('span', { class: 'chip bad' }, 'błąd');
  if (s.state === 'publishing') return h('span', { class: 'chip run' }, 'publikowanie…');
  return null;
}

function row(s, beat) {
  const r = s.result;
  const [vcls, vlabel] = VERDICT[r?.verdict] || ['mute', 'brak'];
  const open = () => { if (r) location.hash = `#/s/${encodeURIComponent(s.id)}`; };
  const del = h('button', { class: 'btn ghost icon', title: 'Usuń strategię', 'aria-label': `Usuń ${s.name}`,
    onclick: (e) => { e.stopPropagation(); deleteStrategy(s); } }, '🗑');
  const job = beat?.job?.id === s.id ? beat.job : null;
  return h('article', { class: `srow ${r ? 'clickable' : ''}`, tabindex: r ? 0 : null, onclick: open,
    onkeydown: (e) => { if (e.key === 'Enter') open(); } },
    h('div', { class: 'srow-main' },
      h('div', { class: 'row' },
        h('span', { class: `dot ${vcls}`, title: `werdykt: ${vlabel}` }),
        h('h3', {}, s.name),
        r?.demo ? h('span', { class: 'chip demo' }, 'DEMO') : null,
        s.doc?.frozenAt ? h('span', { class: 'chip frozen' }, '❄ zamrożona') : null,
        stateChip(s, beat)),
      h('p', { class: 'hyp' }, (r?.hypothesis || s.doc?.hypothesis || '').trim() || '—'),
      s.state === 'running' && job ? h('div', { class: 'progress' }, h('i', { style: { width: `${job.progress || 0}%` } }), h('span', {}, job.phase || '')) : null,
      s.state === 'error' ? h('div', { class: 'err' }, h('pre', {}, s.doc?.error || 'nieznany błąd'),
        h('button', { class: 'btn small', onclick: (e) => { e.stopPropagation(); openEditor({ id: s.id, name: s.name, hypothesis: s.doc?.hypothesis, code: s.doc?.code }); } }, 'Popraw kod')) : null),
    r ? h('dl', { class: 'srow-kpi' },
      h('div', {}, h('dt', {}, 'najlepsze wyjście'), h('dd', {}, r.best_exit || '—')),
      h('div', {}, h('dt', {}, 'IS śr. R'), h('dd', { class: 'num' }, signed(r.is_mean_r))),
      h('div', {}, h('dt', {}, 'OOS śr. R'), h('dd', { class: `num ${r.oos_mean_r > 0 ? 'pos' : r.oos_mean_r < 0 ? 'neg' : ''}` }, signed(r.oos_mean_r))),
      h('div', {}, h('dt', {}, 'OOS transakcje'), h('dd', { class: 'num' }, num(r.oos_trades, 0))),
      h('div', {}, h('dt', {}, 'warianty'), h('dd', { class: 'num' }, num(r.n_variants, 0))),
      h('div', {}, h('dt', {}, 'dane'), h('dd', {}, `${dateUTC(r.data_from)} → ${dateUTC(r.data_to)}`)))
      : h('div', { class: 'srow-kpi muted' }, s.state === 'error' ? '' : 'wyniki pojawią się po policzeniu na Macu'),
    h('div', { class: 'srow-act' }, del, r ? h('span', { class: 'go', 'aria-hidden': 'true' }, '→') : null));
}

function banner() {
  const { user, docsError } = store.state;
  if (!user) {
    return h('div', { class: 'banner' }, 'Bez logowania widzisz wyniki. Żeby dodawać, poprawiać i usuwać strategie — ',
      h('button', { class: 'link', onclick: () => $('#login')?.click() }, 'zaloguj się kontem Google'), '.');
  }
  if (docsError?.code === 'permission-denied') {
    return h('div', { class: 'banner warn' },
      h('b', {}, 'Firestore nie wpuszcza tego konta. '),
      'Wpisz swój UID do reguł: Firebase → Firestore → Rules → zamień ', h('code', {}, '<OWNER_UID>'), ' na ',
      h('code', {}, user.uid), ' → Publish. Ten sam UID wpisz na Macu do ', h('code', {}, '~/.ia5/config.json'), ' jako ',
      h('code', {}, `{"owner_uid": "${user.uid}"}`), '. ',
      h('button', { class: 'btn small', onclick: async () => toast((await copy(user.uid)) ? 'Skopiowano UID.' : 'Nie udało się skopiować.', 'ok') }, 'Kopiuj UID'));
  }
  return null;
}

export function renderList() {
  const root = $('#view-list');
  const { index, docs, hidden, beat, indexError } = store.state;
  let items = mergeStrategies(index || [], docs || {}, hidden || new Set());
  const total = items.length;
  if (query) items = items.filter((s) => (s.name + ' ' + (s.result?.hypothesis || '')).toLowerCase().includes(query));
  items.sort(SORTS[sort]);

  const search = h('input', { type: 'search', placeholder: 'Szukaj…', value: query, 'aria-label': 'Szukaj strategii',
    oninput: (e) => { query = e.target.value.toLowerCase(); renderList(); $('#view-list input[type=search]').focus(); } });
  const sortSel = h('select', { 'aria-label': 'Sortowanie', onchange: (e) => { sort = e.target.value; renderList(); } },
    ...[['created', 'najnowsze'], ['verdict', 'werdykt'], ['oos', 'OOS śr. R'], ['name', 'nazwa']].map(([v, l]) => h('option', { value: v, selected: v === sort }, l)));
  const list = h('div', { class: 'slist' }, ...items.map((s) => row(s, beat)));
  const empty = index == null && !indexError ? h('div', { class: 'empty' }, 'Wczytywanie wyników…')
    : !total ? h('div', { class: 'empty' }, h('p', {}, 'Nie ma jeszcze żadnej strategii.'),
      h('button', { class: 'btn accent', onclick: () => openEditor() }, '+ Nowa strategia')) : null;
  root.replaceChildren(
    h('div', { class: 'toolbar' },
      h('h2', {}, 'Strategie ', h('span', { class: 'count' }, total)),
      h('div', { class: 'row' }, search, sortSel, h('button', { class: 'btn accent', onclick: () => openEditor() }, '+ Nowa strategia'))),
    banner() || '',
    indexError ? h('div', { class: 'banner warn' }, `Nie udało się wczytać wyników z GitHub: ${esc(indexError)}`) : '',
    empty || list);
}

export function initList() {
  for (const k of ['index', 'docs', 'hidden', 'beat', 'user', 'docsError', 'indexError']) store.on(k, () => { if (store.state.route?.view === 'list') renderList(); });
}
