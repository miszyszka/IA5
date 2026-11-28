// Zakładka Zasięg (D-076): jak daleko rynek może dojść w 1 / 3 / 5 dni (prognoza zmienności, nie kierunku) i gdzie stoją
// poziomy wybicia z ściśnięcia na H1 z TP = 3 × SL. Dane: range/state.json z gałęzi data (0 odczytów Firestore).
import { rangeBand } from './charts.js';
import { getJSON } from './data.js';
import { LABEL, boxState, fmtPips, fmtPrice, fmtRange, orderPairs, qualityLine, sideLine, signalTone } from './zasieglogic.js';
import { $, h, local, store } from './util.js';

const ui = { pick: null };
const panel = (title, hint, ...body) => h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, title), hint ? h('span', { class: 'hint' }, hint) : null), ...body);

export async function loadZasieg() {
  try {
    const st = await getJSON('range/state.json');
    if (!st) { store.set('zasiegError', 'brak range/state.json'); return; }
    store.set('zasiegError', null);
    if (st?.computedAt !== store.state.zasieg?.computedAt) store.set('zasieg', st);
  } catch (e) {
    store.set('zasiegError', e.message || String(e));
  }
}

export function initZasieg() {
  store.on('zasieg', () => { if (store.state.route?.view === 'zasieg') renderZasieg(); });
  store.on('zasiegError', () => { if (store.state.route?.view === 'zasieg') renderZasieg(); });
}

function card(x) {
  const f3 = x.forecast?.find((f) => f.h === 3) || {};
  const st = boxState(x.box);
  const on = ui.pick === x.pair;
  const others = (x.forecast || []).filter((f) => f.h !== 3).map((f) => `${f.h} ${f.h === 1 ? 'dzień' : 'dni'}: ${fmtRange(f.low, f.high)}`).join(' · ');
  const b = x.box;
  const last = (x.signals || []).slice(-1)[0];
  return h('button', { class: `zcard ${on ? 'on' : ''}`, 'aria-pressed': on, onclick: () => { ui.pick = x.pair; renderZasieg(); } },
    h('div', { class: 'row between' }, h('b', {}, LABEL[x.pair] || x.pair), h('span', { class: `chip ${st.tone}` }, st.word)),
    h('div', { class: 'zbig' }, h('small', {}, 'zasięg 3 dni (80%)'), h('span', { class: 'mono' }, fmtRange(f3.low, f3.high))),
    h('div', { class: 'hint' }, `mediana ${fmtPips(f3.mid)} · ${f3.mood || '—'} (zwykle ${fmtPips(f3.typical)})`),
    h('div', { class: 'hint' }, others),
    b ? h('div', { class: 'hint' }, `Pudełko 24 h: ${fmtPrice(x.pair, b.lower)} – ${fmtPrice(x.pair, b.upper)} (${fmtPips(b.height_pips)}, ${Math.round(b.pct ?? 0)}. percentyl)`) : null,
    b?.armed ? h('div', { class: 'zlevels' },
      b.long.reachable ? h('div', {}, '▲ ', sideLine(x.pair, b.long, 1)) : null,
      b.short.reachable ? h('div', {}, '▼ ', sideLine(x.pair, b.short, -1)) : null) : null,
    last ? h('div', { class: 'hint' }, `Ostatni sygnał: ${last.dir > 0 ? 'long' : 'short'} ${local(last.signal_ts + 3600)} — `,
      h('span', { class: signalTone(last) }, last.status), last.pips != null ? ` (${last.pips > 0 ? '+' : ''}${Math.round(last.pips)} pips)` : '') : null);
}

function detail(x) {
  const rows = [...(x.signals || [])].reverse();
  return [
    panel(`${LABEL[x.pair] || x.pair} — prognoza 3 dni a to, co się stało`, 'ostatnie 120 dni; ostatnie 3 dni jeszcze bez wyniku',
      h('div', { id: 'zchart', class: 'chart' })),
    panel('Sygnały z ostatnich 7 dni', `ściśnięcie → zamknięcie godziny za pudełkiem → wejście na open następnej; TP = ${store.state.zasieg?.params?.tp_mult ?? 3} × SL`,
      rows.length ? h('table', { class: 'data compact' },
        h('thead', {}, h('tr', {}, ...['sygnał', 'kierunek', 'wejście', 'SL', 'TP', 'wynik', 'pips'].map((t) => h('th', {}, t)))),
        h('tbody', {}, ...rows.map((s) => h('tr', {},
          h('td', {}, local(s.signal_ts + 3600)), h('td', {}, s.dir > 0 ? '▲ long' : '▼ short'),
          h('td', { class: 'num' }, fmtPrice(x.pair, s.entry)), h('td', { class: 'num' }, fmtPrice(x.pair, s.sl)),
          h('td', { class: 'num' }, fmtPrice(x.pair, s.tp)), h('td', { class: signalTone(s) }, s.status),
          h('td', { class: `num ${signalTone(s)}` }, s.pips == null ? '—' : `${s.pips > 0 ? '+' : ''}${Math.round(s.pips)}`)))))
        : h('p', { class: 'hint' }, 'Brak sygnałów w ostatnich 7 dniach.')),
  ];
}

export function renderZasieg() {
  const root = $('#view-zasieg');
  const st = store.state.zasieg;
  if (!st) {
    const err = store.state.zasiegError;
    root.replaceChildren(panel('Zasięg ruchu', null, h('p', { class: 'hint' }, err
      ? 'Jeszcze nie ma danych zakładki — policzy je GitHub Actions po najbliższej pełnej godzinie (albo Mac po `git pull` i restarcie `ia5 start`).'
      : 'Wczytuję…')));
    return;
  }
  const list = orderPairs(st.pairs);
  if (!ui.pick || !st.pairs[ui.pick]) ui.pick = list[0]?.pair;
  const pick = st.pairs[ui.pick];
  root.replaceChildren(
    h('div', { class: 'phead page' }, h('h2', {}, 'Zasięg ruchu'),
      h('span', { class: 'hint' }, `kierunku nie prognozujemy — tylko jak daleko rynek może dojść · stan z ${local(st.computedAt)}`)),
    h('p', { class: 'hint' }, qualityLine(st.quality), ' Reguła wybicia do backtestu: ', h('code', {}, 'strategies/examples/zasieg_wybicie.py'), '.'),
    h('div', { class: 'zgrid' }, ...list.map(card)),
    ...(pick ? detail(pick) : []));
  if (pick?.history) rangeBand($('#zchart'), pick.history);
}
