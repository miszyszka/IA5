// Zakładka Stats: baza świec, latencja, dziennik dzień po dniu, flagi jakości.
// Wszystko z meta/status, który nagłówek i tak nasłuchuje — 0 dodatkowych odczytów Firestore (Z2, Z4).
import { PAIRS } from './metrics.js';
import { dailyRows, FLAG_LABEL, parseFlag } from './session.js';
import { flagCount } from './status.js';
import { $, dateUTC, esc, h, local, num, store } from './util.js';

const DAYS = 30;
const median = (a) => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
const WD = ['nd', 'pn', 'wt', 'śr', 'cz', 'pt', 'sb'];

function spark(points) {
  if (!points || points.length < 2) return '';
  const w = 160, hh = 28, max = Math.max(...points.map((p) => p.s), 1);
  const d = points.map((p, i) => `${((i / (points.length - 1)) * w).toFixed(1)},${(hh - 2 - (p.s / max) * (hh - 4)).toFixed(1)}`).join(' ');
  return `<svg class="spark" width="${w}" height="${hh}" viewBox="0 0 ${w} ${hh}" role="img" aria-label="latencja z 24 h"><polyline points="${d}"/></svg>`;
}

function summary(s) {
  const lat = s.latency24h || [];
  const last = lat.length ? lat[lat.length - 1].s : null;
  const med = median(lat.map((x) => x.s));
  const cross = s.cross || {};
  const run = s.lastRun || {};
  const item = (label, value, sub = '') => h('div', { class: 'stat' }, h('small', {}, label), h('b', { html: value }), h('span', { class: 'hint', html: sub }));
  return h('section', { class: 'panel stats-sum' },
    item('Świece w bazie', num(s.totalBars || 0, 0), `Yahoo H1 w Firestore${run.finishedAt ? `<br>ostatnie pobranie ${local(run.finishedAt)}` : ''}${run.ok === false ? `<br><span class="neg">błąd: ${esc(run.error)}</span>` : ''}`),
    item('Latencja ostatniej świecy', last == null ? '—' : `${num(last, 0)} s`, `${med == null ? '' : `mediana 24 h ${num(med, 0)} s`}${spark(lat)}`),
    item('Kontrola krzyżowa', `${cross.eurjpyPips == null ? '—' : num(cross.eurjpyPips, 1)} / ${cross.eurgbpPips == null ? '—' : num(cross.eurgbpPips, 1)} pips`,
      'odchyłka trójkątów EUR/JPY i EUR/GBP'),
    item('Flagi jakości', String(flagCount(s)), 'kontrola D5 — lista niżej'));
}

function pairsTable(s) {
  const pairs = s.pairs || {};
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Pary'), h('span', { class: 'hint' }, 'świece Yahoo zapisane w Firestore')),
    h('div', { class: 'tablewrap', html: `<table class="data compact static">
      <thead><tr><th>Para</th><th>Ostatnia świeca (UTC)</th><th>Czas lokalny</th><th class="r">Latencja s</th><th class="r">Świece</th><th class="r">Flagi</th></tr></thead>
      <tbody>${Object.keys(PAIRS).map((p) => {
        const x = pairs[p] || {}, fl = x.flags || [];
        return `<tr><td class="txt">${PAIRS[p].label}</td><td>${x.lastTs ? dateUTC(x.lastTs, true) : '—'}</td><td>${x.lastTs ? local(x.lastTs) : '—'}</td>
          <td class="r">${x.latencySec ?? '—'}</td><td class="r">${num(x.count || 0, 0)}</td><td class="r ${fl.length ? 'warn' : ''}">${fl.length}</td></tr>`;
      }).join('')}</tbody></table>` }));
}

function dailyLog(s) {
  const pairs = Object.keys(PAIRS);
  const head = h('div', { class: 'phead' }, h('h3', {}, 'Dziennik — świece dzień po dniu'),
    h('span', { class: 'hint' }, `ostatnie ${DAYS} dni (UTC) · dodane / oczekiwane`));
  if (!s.daily) {
    return h('section', { class: 'panel' }, head, h('p', { class: 'hint' },
      'Dziennik pojawi się po wklejeniu nowego Code.gs do Apps Script — pierwsze uruchomienie policzy ostatnie 2 miesiące z bazy.'));
  }
  const rows = dailyRows(s.daily, pairs, Date.now() / 1000, DAYS);
  const max = Math.max(1, ...rows.map((r) => r.expected));
  const body = rows.map((r) => {
    const d = new Date(r.day + 'T00:00:00Z');
    const state = r.closed ? 'closed' : r.missing ? 'short' : 'full';
    const note = r.closed ? 'bez handlu' : r.open ? 'w toku' : r.missing ? `brak ${r.missing}` : '';
    const cells = pairs.map((p) => {
      const c = r.counts[p];
      const miss = !r.closed && c < r.expectedPerPair;
      return `<td class="r ${miss ? 'warn' : c ? '' : 'dimmed'}" title="${PAIRS[p].label}: ${c} z ${r.expectedPerPair}">${c}</td>`;
    }).join('');
    return `<tr class="${state}"><td>${r.day.slice(5)} <span class="dimmed">${WD[d.getUTCDay()]}</span></td>
      <td class="r">${num(r.total, 0)}<span class="dimmed"> / ${num(r.expected, 0)}</span></td>
      <td class="fill"><span class="meter"><i style="width:${(r.total / max) * 100}%"></i></span></td>
      ${cells}<td class="txt note">${note}</td></tr>`;
  }).join('');
  return h('section', { class: 'panel' }, head,
    h('div', { class: 'tablewrap', html: `<table class="data compact static daily">
      <thead><tr><th>Dzień</th><th class="r">Razem</th><th></th>${pairs.map((p) => `<th class="r">${PAIRS[p].label}</th>`).join('')}<th></th></tr></thead>
      <tbody>${body}</tbody></table>` }),
    h('p', { class: 'hint' }, 'Liczone wg dnia świecy (UTC). Święta nie są w kalendarzu sesji, więc tego dnia pokażą się jako braki (D-009).'));
}

function flagsList(s) {
  const items = [];
  for (const [p, x] of Object.entries(s.pairs || {})) {
    for (const f of x.flags || []) items.push({ pair: PAIRS[p]?.label || p, ...parseFlag(f) });
  }
  for (const f of (s.cross || {}).flags || []) items.push({ pair: 'trójkąt', kind: f, ts: s.cross.ts });
  items.sort((a, b) => (b.ts || 0) - (a.ts || 0));
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Flagi jakości'), h('span', { class: 'hint' }, 'zgłaszane, nigdy naprawiane po cichu (D5)')),
    items.length
      ? h('ul', { class: 'flaglist' }, ...items.map((f) => h('li', {},
        h('span', { class: 'mono' }, f.ts ? dateUTC(f.ts, true) : '—'), h('b', {}, f.pair), h('span', {}, FLAG_LABEL[f.kind] || f.kind))))
      : h('p', { class: 'hint' }, 'Brak flag. Ostatnie pobrania przeszły kontrolę.'));
}

export function renderStats() {
  const root = $('#view-stats');
  const s = store.state.status;
  if (!s) {
    root.replaceChildren(h('div', { class: 'empty' }, store.state.statusError ? `Firestore: ${store.state.statusError}` : 'Wczytywanie stanu…'));
    return;
  }
  root.replaceChildren(h('div', { class: 'toolbar' }, h('h2', {}, 'Stats')), summary(s), dailyLog(s), h('div', { class: 'grid2' }, pairsTable(s), flagsList(s)));
}

export function initStats() {
  for (const k of ['status', 'statusError']) store.on(k, () => { if (store.state.route?.view === 'stats') renderStats(); });
}
