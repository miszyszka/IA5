// Karta strategii (CLAUDE.md 10.5). Wszystkie liczby z plików wyników na gałęzi data.
import { candles, disposeAll, equityChart, heatmap, lines } from './charts.js';
import { getJSON, getText, readRows } from './data.js';
import { openEditor } from './editor.js';
import { freeze, unfreeze } from './fb.js';
import { deleteStrategy } from './list.js';
import {
  PAIRS, SIZING, breakdown, drawdown, equityStats, filterTrades, sessionOf, simulateEquity, summarize, toCSV, weekdayOf, yearOf,
} from './metrics.js';
import { $, $$, cls, confirmDialog, copy, dateUTC, download, esc, h, num, pct, signed, store, toast } from './util.js';

const VERDICT = { green: ['ok', 'ZIELONY'], yellow: ['warn', 'ŻÓŁTY'], red: ['bad', 'CZERWONY'] };
const MIN_TRADES = 30;
const PAGE = 50;
const RANK_COLS = [
  ['rank_is', '#', (v) => num(v.rank_is, 0)],
  ['exit', 'wyjście', (v) => esc(v.exit)],
  ['params', 'parametry', (v) => esc(paramsLabel(v.params))],
  ['is_trades', 'IS trans.', (v) => num(v.is_trades, 0)],
  ['is_exp_r', 'IS śr. R', (v) => bar(v.is_exp_r)],
  ['is_exp_pips', 'IS śr. pips', (v) => `<span class="${cls(v.is_exp_pips)}">${signed(v.is_exp_pips)}</span>`],
  ['is_win_rate', 'IS win', (v) => pct(v.is_win_rate)],
  ['is_profit_factor', 'IS PF', (v) => num(v.is_profit_factor)],
  ['oos_trades', 'OOS trans.', (v) => num(v.oos_trades, 0)],
  ['oos_exp_r', 'OOS śr. R', (v) => `<span class="${cls(v.oos_exp_r)}">${signed(v.oos_exp_r)}</span>`],
  ['oos_exp_pips', 'OOS śr. pips', (v) => `<span class="${cls(v.oos_exp_pips)}">${signed(v.oos_exp_pips)}</span>`],
];
let maxAbsR = 1;
const bar = (x) => {
  if (x == null) return '—';
  const w = Math.min(100, (Math.abs(x) / maxAbsR) * 100);
  return `<span class="mbar ${x >= 0 ? 'pos' : 'neg'}"><i style="width:${w}%"></i><b>${signed(x)}</b></span>`;
};
const paramsLabel = (p) => {
  const o = typeof p === 'string' ? JSON.parse(p || '{}') : p || {};
  return Object.entries(o).map(([k, v]) => `${k}=${v}`).join(', ') || '—';
};

let S = null; // stan otwartej karty

export async function openCard(id) {
  disposeAll();
  candleView = null;
  const root = $('#view-card');
  root.replaceChildren(h('div', { class: 'empty' }, 'Wczytywanie wyników…'));
  const base = `results/${id}/`;
  try {
    const [manifest, variants, validation] = await Promise.all([getJSON(base + 'manifest.json'), getJSON(base + 'variants.json'), getJSON(base + 'validation.json')]);
    if (!manifest) throw new Error('Nie ma wyników tej strategii (usunięta albo jeszcze nie opublikowana).');
    variants.forEach((v) => { v.params = typeof v.params === 'string' ? JSON.parse(v.params || '{}') : v.params || {}; });
    const best = validation.best_variant_id ?? variants.find((v) => v.rank_is === 1)?.variant_id ?? variants[0]?.variant_id;
    S = {
      id, base, manifest, variants, validation,
      byId: new Map(variants.map((v) => [v.variant_id, v])),
      selected: best, trades: [], tradesCache: new Map(), candlesCache: new Map(),
      f: { pairs: new Set(manifest.pairs), dir: 'all', sample: 'all', sizing: String(manifest.sizing?.[1] ?? 10), family: 'all', forward: false },
      rankSort: { key: 'is_exp_r', desc: true }, rankLimit: PAGE, page: 0, chartPair: manifest.pairs[0],
      heat: { metric: 'is_exp_r' },
    };
    const elig = variants.filter((v) => (v.is_trades ?? 0) >= MIN_TRADES).map((v) => Math.abs(v.is_exp_r ?? 0)).filter(Number.isFinite);
    maxAbsR = Math.max(0.1, ...elig);
    render();
    await selectVariant(best);
  } catch (e) {
    root.replaceChildren(h('div', { class: 'empty' }, h('p', {}, e.message || String(e)), h('a', { class: 'btn', href: '#/' }, '← Wróć do listy')));
  }
}

store.on('docs', () => { if (S && store.state.route?.view === 'card') renderHead(); });

function doc() { return store.state.docs?.[S.id] || null; }

async function selectVariant(vid) {
  S.selected = vid;
  S.page = 0;
  const v = S.byId.get(vid);
  $$('#rank tbody tr').forEach((tr) => tr.classList.toggle('sel', +tr.dataset.id === vid));
  if (!S.tradesCache.has(vid)) {
    S.tradesCache.set(vid, v?.row_end > v?.row_start ? await readRows(S.base + 'trades.parquet', v.row_start, v.row_end) : []);
  }
  S.trades = S.tradesCache.get(vid);
  renderVariant();
  renderHeat();
}

function filtered() {
  const d = doc();
  const from = S.f.forward && d?.frozenAt ? d.frozenAt : null;
  return filterTrades(S.trades, { pairs: S.f.pairs, dir: S.f.dir, sample: S.f.sample, from });
}

// ---------- układ ----------

function render() {
  const m = S.manifest;
  $('#view-card').replaceChildren(
    h('a', { class: 'back', href: '#/' }, '← Strategie'),
    h('section', { id: 'card-head', class: 'card-head' }),
    h('section', { class: 'grid2' }, h('div', { id: 'verdict', class: 'panel' }), h('div', { id: 'valid', class: 'panel' })),
    h('section', { id: 'filters', class: 'filters panel' }),
    h('section', { class: 'panel' },
      h('div', { class: 'phead' }, h('h3', {}, 'Ranking wariantów'), h('span', { class: 'hint' },
        `${num(m.n_variants, 0)} wariantów · ranking po IS (min. ${MIN_TRADES} transakcji) · liczby dla wszystkich par · kliknij wiersz, żeby go zbadać`)),
      h('div', { class: 'rank-tools row' }),
      h('div', { class: 'tablewrap' }, h('table', { id: 'rank', class: 'data' })),
      h('button', { class: 'btn ghost small more', onclick: () => { S.rankLimit += PAGE; renderRank(); } }, 'Pokaż więcej')),
    h('section', { class: 'grid2' },
      h('div', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Stabilność TP × SL (rodzina ATR)'), h('div', { id: 'heat-tools', class: 'row' })),
        h('div', { id: 'heat', class: 'chart' }), h('p', { class: 'hint' }, 'Szukaj płaskowyżu podobnych wyników, nie pojedynczego jasnego pola. Kliknij pole, żeby wybrać wariant.')),
      h('div', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Wyjście po N świecach')), h('div', { id: 'timecurve', class: 'chart' }),
        h('p', { class: 'hint' }, 'Średnie R w IS i OOS dla wyjść czasowych przy wybranych parametrach wejścia.'))),
    h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', { id: 'eq-title' }, 'Kapitał od początku')), h('div', { id: 'eq-kpi', class: 'kpis small' }),
      h('div', { id: 'equity', class: 'chart tall' })),
    h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Transakcje na świecach'), h('div', { id: 'cd-tools', class: 'row' })),
      h('div', { id: 'candles', class: 'chart tall' }), h('p', { id: 'cd-note', class: 'hint' })),
    h('section', { id: 'breakdowns', class: 'grid3' }),
    h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Transakcje'), h('div', { id: 'tr-tools', class: 'row' })),
      h('div', { class: 'tablewrap' }, h('table', { id: 'trades', class: 'data' })), h('div', { id: 'tr-pager', class: 'row center' })),
    h('section', { class: 'panel' }, h('details', { id: 'code', ontoggle: loadCode }, h('summary', {}, 'Kod strategii'), h('pre', { class: 'codeview' }, 'Wczytywanie…'))));
  renderHead();
  renderVerdict();
  renderFilters();
  renderRank();
  renderTimeCurve();
}

function renderHead() {
  const m = S.manifest, v = S.validation, d = doc();
  const [vc, vl] = VERDICT[v.verdict?.color] || ['mute', '—'];
  const loggedIn = !!store.state.user;
  const act = (label, fn, cls2 = '', title = '') => h('button', { class: `btn ${cls2}`, title, onclick: fn }, label);
  const frozen = d?.frozenAt;
  $('#card-head').replaceChildren(
    h('div', { class: 'title-row' },
      h('div', {},
        h('h2', {}, m.name, m.demo ? h('span', { class: 'chip demo' }, 'DEMO') : null, frozen ? h('span', { class: 'chip frozen' }, `❄ zamrożona ${dateUTC(frozen)}`) : null,
          d?.status === 'liczy_sie' ? h('span', { class: 'chip run' }, 'przeliczanie…') : d?.status === 'do_policzenia' ? h('span', { class: 'chip warn' }, 'w kolejce do przeliczenia') : null),
        h('p', { class: 'meta' }, `${m.pairs.map((p) => PAIRS[p]?.label || p).join(', ')} · ${dateUTC(m.data_from)} → ${dateUTC(m.data_to)} · OOS od ${dateUTC(m.oos_cutoff)} · `,
          `źródło: ${m.data_source} · silnik ${m.engine_version} · kod ${m.code_hash} · dane ${m.data_hash} · policzono ${dateUTC(m.created, true)} UTC`)),
      h('div', { class: `verdict-badge ${vc}` }, h('small', {}, 'werdykt'), h('b', {}, vl), h('span', {}, v.verdict?.note || ''))),
    m.hypothesis ? h('blockquote', { class: 'hyp' }, m.hypothesis) : h('p', { class: 'hint' }, 'Brak hipotezy.'),
    h('div', { class: 'row wrap actions' },
      act('Kopiuj raport dla Claude', async () => toast((await copy(await getText(S.base + 'report.md'))) ? 'Raport skopiowany — wklej go Claude.' : 'Nie udało się skopiować.', 'ok'), 'accent'),
      act('Pobierz report.md', async () => download(`${S.id}-report.md`, await getText(S.base + 'report.md'), 'text/markdown')),
      act('Pobierz kod', async () => download(`${S.id}.py`, await getText(S.base + 'strategy.py'), 'text/x-python')),
      act('Policz ponownie / popraw', async () => openEditor({ id: S.id, name: m.name, hypothesis: m.hypothesis || '', code: await getText(S.base + 'strategy.py') }), '',
        'Otwiera kod w edytorze; po zapisaniu Mac policzy strategię od nowa'),
      frozen
        ? act('Odmroź', async () => { try { await unfreeze(S.id); toast('Odmrożono.', 'ok'); } catch (e) { toast(e.message, 'bad'); } })
        : act('❄ Zamroź wybrany wariant', async () => {
          if (!loggedIn) return toast('Zaloguj się, żeby zamrozić strategię.', 'warn');
          if (!d || d.status !== 'policzona') return toast('Zamrożenie działa dla strategii policzonych na Macu (z Twoich danych).', 'warn');
          const vv = S.byId.get(S.selected);
          if (!(await confirmDialog('Zamrozić strategię?', `Od dziś Mac będzie co 6 h dopisywał nowe transakcje wariantu „${vv.exit}” (${paramsLabel(vv.params)}). To prawdziwy test: przyszłość, której strategia nie widziała.`, 'Zamroź'))) return;
          try { await freeze(S.id, S.selected); toast('Zamrożono — forward test liczy się od teraz.', 'ok'); } catch (e) { toast(e.message, 'bad'); }
        }, '', 'Forward test (W4): od tej chwili liczą się tylko nowe świece'),
      act('Usuń', async () => { if (await deleteStrategy({ id: S.id, name: m.name })) location.hash = '#/'; }, 'danger ghost')));
}

function renderVerdict() {
  const v = S.validation, b = v.benchmark || {};
  const checks = (v.verdict?.checks || []).map((c) =>
    h('li', { class: c.ok ? 'ok' : 'bad' }, h('span', { class: 'mark' }, c.ok ? '✔' : '✘'), c.test,
      h('b', { class: 'num' }, c.value == null ? '—' : num(c.value, Math.abs(c.value) < 10 ? 3 : 1))));
  const p = b.percentile ?? null;
  $('#verdict').replaceChildren(
    h('div', { class: 'phead' }, h('h3', {}, 'Werdykt — testy z góry ustalone (sekcja 9)')),
    h('ul', { class: 'checks-list' }, ...checks),
    h('div', { class: 'gauge' },
      h('div', { class: 'gauge-label row between' }, h('span', {}, 'Benchmark losowych wejść — percentyl wyniku'), h('b', {}, p == null ? '—' : `${num(p, 1)}`)),
      h('div', { class: 'track' }, h('i', { style: { width: `${p ?? 0}%` } }), h('em', { style: { left: '95%' }, title: 'próg 95' })),
      h('p', { class: 'hint' }, `${num(b.sims, 0)} losowań z tymi samymi parami, kierunkami i wyjściem. Losowe wejścia: 5% = ${signed(b.p5)}, mediana = ${signed(b.p50)}, 95% = ${signed(b.p95)} pips/transakcję; strategia: ${signed(b.actual_mean_pips)}.`)));
  const wf = v.walk_forward || {}, ds = v.dsr || {}, pb = v.pbo || {}, bs = v.bootstrap || {}, sp = v.spread || {};
  const rowKV = (k, val, hint) => h('tr', {}, h('th', {}, k), h('td', { class: 'num' }, val), h('td', { class: 'hint' }, hint || ''));
  $('#valid').replaceChildren(
    h('div', { class: 'phead' }, h('h3', {}, `Najlepszy wariant IS: ${v.best_exit || '—'}`), h('span', { class: 'hint' }, paramsLabel(v.best_params))),
    h('table', { class: 'kv' }, h('tbody', {},
      rowKV('IS śr. R → OOS śr. R', `${signed(v.is_mean_r)} → ${signed(v.oos_mean_r)}`, `${num(v.oos_trades, 0)} transakcji OOS`),
      rowKV('Deflated Sharpe', num(ds.dsr, 3), `po korekcie za ${num(ds.trials, 0)} prób; ≥ 0,95 = przewaga mało prawdopodobna jako przypadek`),
      rowKV('PBO', num(pb.pbo, 3), `szansa, że najlepszy IS wypada poniżej mediany poza próbą (${num(pb.variants, 0)} wariantów, ${num(pb.combinations, 0)} podziałów)`),
      rowKV('Walk-forward', `${signed(wf.mean_r)} R`, `${num(wf.trades, 0)} transakcji; wariant wybierany tylko z przeszłości`),
      rowKV('Bootstrap 95% (OOS)', `[${signed(bs.oos?.low)}; ${signed(bs.oos?.high)}]`, 'pips/transakcję'),
      rowKV('Spread ×1 / ×1,5 / ×2', `${signed(sp.x1)} / ${signed(sp.x1_5)} / ${signed(sp.x2)}`, sp.real != null ? `faktyczny: ${signed(sp.real)}` : 'pips/transakcję'),
      rowKV('TP i SL w tej samej świecy', `${num(v.ambiguous_pct)}%`, S.manifest.m1_resolver ? 'nierozstrzygnięte na M1 → SL' : 'bez M1 → zawsze SL'))));
  if ((wf.windows || []).length) {
    $('#valid').append(h('table', { class: 'data compact' },
      h('thead', {}, h('tr', {}, ...['okno', 'wybrany wariant', 'R w nauce', 'transakcje', 'R w oknie'].map((x) => h('th', {}, x)))),
      h('tbody', {}, ...wf.windows.map((w) => h('tr', {}, h('td', {}, `${dateUTC(w.from)} → ${dateUTC(w.to)}`),
        h('td', {}, S.byId.get(w.variant_id)?.exit || w.variant_id), h('td', { class: 'num' }, signed(w.train_r)),
        h('td', { class: 'num' }, num(w.test_trades, 0)), h('td', { class: `num ${cls(w.test_r)}` }, signed(w.test_r)))))));
  }
}

function renderFilters() {
  const m = S.manifest, d = doc();
  const pairChip = (p) => h('button', { class: `chip toggle ${S.f.pairs.has(p) ? 'on' : ''}`, 'aria-pressed': S.f.pairs.has(p),
    onclick: () => { S.f.pairs.has(p) ? S.f.pairs.delete(p) : S.f.pairs.add(p); renderFilters(); renderVariant(); } }, PAIRS[p]?.label || p);
  const seg = (key, opts) => h('div', { class: 'seg', role: 'group' }, ...opts.map(([v, l]) =>
    h('button', { class: S.f[key] === v ? 'on' : '', 'aria-pressed': S.f[key] === v, onclick: () => { S.f[key] = v; renderFilters(); renderVariant(); } }, l)));
  const sizing = (m.sizing || SIZING).map(String);
  $('#filters').replaceChildren(
    h('div', { class: 'fgroup' }, h('span', { class: 'flabel' }, 'Pary'), ...m.pairs.map(pairChip),
      m.pairs.length > 1 ? h('button', { class: 'link small', onclick: () => { S.f.pairs = new Set(m.pairs); renderFilters(); renderVariant(); } }, 'wszystkie') : ''),
    h('div', { class: 'fgroup' }, h('span', { class: 'flabel' }, 'Kierunek'), seg('dir', [['all', 'oba'], ['long', 'long'], ['short', 'short']])),
    h('div', { class: 'fgroup' }, h('span', { class: 'flabel' }, 'Próba'), seg('sample', [['all', 'całość'], ['IS', 'IS'], ['OOS', 'OOS']])),
    h('div', { class: 'fgroup' }, h('span', { class: 'flabel' }, 'Depozyt'), seg('sizing', sizing.map((s) => [s, `${s}%`]))),
    d?.frozenAt ? h('label', { class: 'fgroup check' }, h('input', { type: 'checkbox', checked: S.f.forward, onchange: (e) => { S.f.forward = e.target.checked; renderVariant(); } }), 'tylko forward (od zamrożenia)') : '');
}

function renderRank() {
  const fam = S.f.family;
  const tools = $('.rank-tools');
  tools.replaceChildren(h('span', { class: 'flabel' }, 'Rodzina wyjść'),
    h('div', { class: 'seg' }, ...[['all', 'wszystkie'], ['czas', 'czas'], ['ATR', 'ATR'], ['stop kroczący', 'kroczący'], ['wskaźnik', 'wskaźnik']].map(([v, l]) =>
      h('button', { class: fam === v ? 'on' : '', onclick: () => { S.f.family = v; S.rankLimit = PAGE; renderRank(); } }, l))));
  const { key, desc } = S.rankSort;
  const rows = S.variants.filter((v) => fam === 'all' || v.family === fam)
    .sort((a, b) => {
      const ea = (a.is_trades ?? 0) >= MIN_TRADES, eb = (b.is_trades ?? 0) >= MIN_TRADES;
      if (ea !== eb) return ea ? -1 : 1;
      const va = a[key], vb = b[key];
      if (va == null) return 1;
      if (vb == null) return -1;
      const c = typeof va === 'string' ? va.localeCompare(vb, 'pl') : va - vb;
      return desc ? -c : c;
    });
  const t = $('#rank');
  t.innerHTML = `<thead><tr>${RANK_COLS.map(([k, l]) => `<th data-k="${k}" class="sortable ${k === key ? (desc ? 'desc' : 'asc') : ''}">${l}</th>`).join('')}</tr></thead>
    <tbody>${rows.slice(0, S.rankLimit).map((v) => `<tr data-id="${v.variant_id}" class="${v.variant_id === S.selected ? 'sel' : ''} ${(v.is_trades ?? 0) < MIN_TRADES ? 'thin' : ''}">${RANK_COLS.map(([, , f]) => `<td>${f(v)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  $$('th.sortable', t).forEach((th) => th.addEventListener('click', () => {
    const k = th.dataset.k;
    S.rankSort = { key: k, desc: k === S.rankSort.key ? !S.rankSort.desc : !['rank_is', 'exit', 'params'].includes(k) };
    renderRank();
  }));
  $$('tbody tr', t).forEach((tr) => tr.addEventListener('click', () => selectVariant(+tr.dataset.id)));
  $('.more').hidden = rows.length <= S.rankLimit;
}

function renderHeat() {
  const v = S.byId.get(S.selected);
  const atrVs = S.variants.filter((x) => x.family === 'ATR' && x.param_id === v.param_id);
  const el = $('#heat');
  if (!atrVs.length) { el.replaceChildren(h('p', { class: 'hint' }, 'Brak wariantów ATR.')); return; }
  const ref = v.family === 'ATR' ? v : atrVs.find((x) => x.rank_is != null) || atrVs[0];
  S.heat.n = S.heat.n ?? ref.x_n;
  S.heat.cap = S.heat.cap ?? ref.x_cap;
  if (v.family === 'ATR') { S.heat.n = v.x_n; S.heat.cap = v.x_cap; }
  const ns = [...new Set(atrVs.map((x) => x.x_n))], caps = [...new Set(atrVs.map((x) => x.x_cap))];
  const sel = (label, key, opts) => h('label', { class: 'mini' }, label, h('select', { onchange: (e) => { S.heat[key] = isNaN(+e.target.value) ? e.target.value : +e.target.value; renderHeat(); } },
    ...opts.map(([val, l]) => h('option', { value: val, selected: S.heat[key] === val }, l))));
  $('#heat-tools').replaceChildren(
    sel('ATR', 'n', ns.map((n) => [n, String(n)])), sel('max', 'cap', caps.map((c) => [c, `${c} św.`])),
    sel('metryka', 'metric', [['is_exp_r', 'IS śr. R'], ['oos_exp_r', 'OOS śr. R'], ['is_exp_pips', 'IS śr. pips']]));
  const grid = atrVs.filter((x) => x.x_n === S.heat.n && x.x_cap === S.heat.cap);
  const xs = [...new Set(grid.map((x) => x.x_tp))].sort((a, b) => a - b);
  const ys = [...new Set(grid.map((x) => x.x_sl))].sort((a, b) => a - b);
  const cells = grid.map((x) => ({ x: x.x_tp, y: x.x_sl, n: x.is_trades ?? 0, id: x.variant_id,
    v: (x.is_trades ?? 0) >= MIN_TRADES && x[S.heat.metric] != null ? x[S.heat.metric] : null }));
  heatmap(el, xs, ys, cells, (c) => selectVariant(c.id), { is_exp_r: 'IS śr. R', oos_exp_r: 'OOS śr. R', is_exp_pips: 'IS śr. pips' }[S.heat.metric]);
}

function renderTimeCurve() {
  const pid = S.byId.get(S.selected)?.param_id ?? 0;
  const tv = S.variants.filter((x) => x.family === 'czas' && x.param_id === pid).sort((a, b) => a.x_n - b.x_n);
  if (!tv.length) return;
  lines($('#timecurve'), tv.map((x) => x.x_n), [
    { name: 'IS śr. R', data: tv.map((x) => x.is_exp_r) }, { name: 'OOS śr. R', data: tv.map((x) => x.oos_exp_r) }], 'N świec');
}

function renderVariant() {
  const v = S.byId.get(S.selected);
  const t = filtered();
  const pctSz = +S.f.sizing;
  $('#eq-title').textContent = `Kapitał od początku — ${v.exit} (${paramsLabel(v.params)}), depozyt ${pctSz}% × dźwignia 30:1`;
  const curve = simulateEquity(t, pctSz);
  const st = equityStats(curve);
  const sm = summarize(t);
  const k = (label, val, c = '') => h('div', { class: 'kpi' }, h('small', {}, label), h('b', { class: c }, val));
  $('#eq-kpi').replaceChildren(
    k('kapitał końcowy', st ? `${num(st.final, 0)} USD` : '—'), k('zwrot', st ? `${signed(st.returnPct, 1)}%` : '—', cls(st?.returnPct)),
    k('CAGR', st ? `${signed(st.cagrPct, 1)}%` : '—', cls(st?.cagrPct)), k('max obsunięcie', st ? `${num(st.maxDdPct, 1)}%` : '—', 'neg'),
    k('Sharpe (dzienny)', st?.sharpe == null ? '—' : num(st.sharpe)), k('transakcje', `${num(curve.taken, 0)}${curve.skipped ? ` (+${curve.skipped} bez depozytu)` : ''}`),
    k('win rate', pct(sm.winRate)), k('śr. pips netto', signed(sm.expPips), cls(sm.expPips)), k('profit factor', num(sm.pf)));
  const marks = [{ ts: S.manifest.oos_cutoff, label: 'start OOS' }];
  const d = doc();
  if (d?.frozenAt) marks.push({ ts: d.frozenAt, label: 'zamrożenie' });
  const eqEl = $('#equity');
  if (curve.ts.length > 1) equityChart(eqEl, curve, drawdown(curve.equity), marks);
  else { window.echarts.getInstanceByDom(eqEl)?.dispose(); eqEl.replaceChildren(h('p', { class: 'hint' }, 'Brak transakcji przy tych filtrach.')); }
  renderBreakdowns(t);
  renderTrades(t);
  renderCandles(t);
  renderTimeCurve();
}

function renderBreakdowns(t) {
  const table = (title, rows) => {
    const max = Math.max(1e-9, ...rows.map((r) => Math.abs(r.sumPips)));
    return h('div', { class: 'panel' }, h('h3', {}, title), h('table', { class: 'data compact' },
      h('thead', {}, h('tr', {}, ...['', 'trans.', 'win', 'śr. pips', 'suma pips'].map((x) => h('th', {}, x)))),
      h('tbody', {}, ...rows.map((r) => h('tr', {}, h('td', {}, r.key), h('td', { class: 'num' }, num(r.trades, 0)), h('td', { class: 'num' }, pct(r.winRate)),
        h('td', { class: `num ${cls(r.expPips)}` }, signed(r.expPips, 1)),
        h('td', { html: `<span class="mbar ${r.sumPips >= 0 ? 'pos' : 'neg'}"><i style="width:${(Math.abs(r.sumPips) / max) * 100}%"></i><b>${signed(r.sumPips, 0)}</b></span>` }))))));
  };
  const order = (arr, keys) => arr.sort((a, b) => keys.indexOf(a.key) - keys.indexOf(b.key));
  $('#breakdowns').replaceChildren(
    table('Według pary', breakdown(t, (x) => PAIRS[x.pair]?.label || x.pair).sort((a, b) => b.sumPips - a.sumPips)),
    table('Według roku', breakdown(t, (x) => String(yearOf(x.exit_ts))).sort((a, b) => a.key.localeCompare(b.key))),
    table('Według sesji (UTC)', order(breakdown(t, (x) => sessionOf(x.entry_ts)), ['Azja', 'Europa', 'USA', 'poza sesją'])),
    table('Według dnia wejścia', order(breakdown(t, (x) => weekdayOf(x.entry_ts)), ['pn', 'wt', 'śr', 'cz', 'pt', 'sb', 'nd'])),
    table('Według powodu wyjścia', breakdown(t, (x) => x.reason)),
    table('Według kierunku i próby', breakdown(t, (x) => `${x.dir > 0 ? 'long' : 'short'} · ${x.sample}`)));
}

const TR_COLS = [
  ['pair', 'para', (t) => PAIRS[t.pair]?.label || t.pair], ['dir', 'kier.', (t) => (t.dir > 0 ? 'long' : 'short')],
  ['entry_ts', 'wejście UTC', (t) => dateUTC(t.entry_ts, true)], ['entry_px', 'cena', (t) => t.entry_px.toFixed(t.entry_px > 20 ? 3 : 5)],
  ['exit_ts', 'wyjście UTC', (t) => dateUTC(t.exit_ts, true)], ['exit_px', 'cena', (t) => t.exit_px.toFixed(t.exit_px > 20 ? 3 : 5)],
  ['reason', 'powód', (t) => t.reason], ['weight', 'waga', (t) => num(t.weight ?? 1, 2)], ['pips_net', 'pips netto', (t) => `<span class="${cls(t.pips_net)}">${signed(t.pips_net, 1)}</span>`],
  ['r_net', 'R', (t) => `<span class="${cls(t.r_net)}">${signed(t.r_net)}</span>`], ['mae', 'MAE', (t) => num(t.mae, 1)], ['mfe', 'MFE', (t) => num(t.mfe, 1)],
  ['bars', 'świece', (t) => t.bars], ['sample', 'próba', (t) => t.sample], ['ambiguous', '', (t) => (t.ambiguous ? '<span title="TP i SL w tej samej świecy — przyjęty SL">⚑</span>' : '')],
];

function renderTrades(t) {
  const pages = Math.max(1, Math.ceil(t.length / PAGE));
  S.page = Math.min(S.page, pages - 1);
  const rows = t.slice(S.page * PAGE, (S.page + 1) * PAGE);
  const tbl = $('#trades');
  tbl.innerHTML = `<thead><tr>${TR_COLS.map(([, l]) => `<th>${l}</th>`).join('')}</tr></thead>
    <tbody>${rows.map((x, i) => `<tr data-i="${S.page * PAGE + i}">${TR_COLS.map(([, , f]) => `<td>${f(x)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  $$('tbody tr', tbl).forEach((tr) => tr.addEventListener('click', () => focusTrade(t[+tr.dataset.i])));
  $('#tr-tools').replaceChildren(h('span', { class: 'hint' }, `${num(t.length, 0)} transakcji · kliknij, żeby zobaczyć na wykresie`),
    h('button', { class: 'btn small', onclick: () => download(`${S.id}-wariant-${S.selected}.csv`, toCSV(t, TR_COLS.map(([k]) => k).filter((k) => k !== 'ambiguous').concat('ambiguous')), 'text/csv') }, 'CSV'));
  const pg = (p, l) => h('button', { class: `btn ghost small ${p === S.page ? 'on' : ''}`, disabled: p < 0 || p >= pages, onclick: () => { S.page = p; renderTrades(t); } }, l);
  $('#tr-pager').replaceChildren(pg(S.page - 1, '←'), h('span', { class: 'hint' }, `strona ${S.page + 1} z ${pages}`), pg(S.page + 1, '→'));
}

let candleView = null;
async function renderCandles(t, focus = null) {
  const pairs = [...new Set(t.map((x) => x.pair))].sort();
  if (!pairs.includes(S.chartPair)) S.chartPair = pairs[0] || S.manifest.pairs[0];
  $('#cd-tools').replaceChildren(h('label', { class: 'mini' }, 'para', h('select', { onchange: (e) => { S.chartPair = e.target.value; renderCandles(t); } },
    ...(pairs.length ? pairs : S.manifest.pairs).map((p) => h('option', { value: p, selected: p === S.chartPair }, PAIRS[p]?.label || p)))));
  const el = $('#candles');
  candleView?.remove();
  el.replaceChildren();
  candleView = null;
  const pair = S.chartPair;
  if (!S.candlesCache.has(pair)) {
    S.candlesCache.set(pair, readRows(`${S.base}candles/${pair}.parquet`).catch(() => []));
  }
  const bars = await S.candlesCache.get(pair);
  if (S.chartPair !== pair) return;
  if (!bars.length) { el.replaceChildren(h('p', { class: 'hint' }, 'Brak świec dla tej pary w wynikach.')); $('#cd-note').textContent = ''; return; }
  candleView = candles(el, bars, t.filter((x) => x.pair === pair));
  const n = candleView.shown.length;
  S.tradeIdx = focus ? candleView.shown.findIndex((x) => x.trade === focus) : n - 1;
  $('#cd-note').textContent = `${S.manifest.candles === 'pełne' ? 'Pełna historia świec.' : `Świece: ${S.manifest.candles} — dane Dukascopy nie są publikowane w całości (D-010), więc wykres składa się z osobnych okien; pusty pas między nimi = pominięty okres, nie ruch ceny.`} `
    + `Strzałka = wejście (L/S), kółko = wyjście z wynikiem w pipsach.${candleView.hidden ? ` ${candleView.hidden} transakcji wybranego wariantu nie ma na wykresie (świece opublikowane tylko dla 10 najlepszych wariantów).` : ''} Wykres: TradingView Lightweight Charts™.`;
  if (focus && S.tradeIdx < 0) candleView.focus(focus.entry_ts - 48 * 3600, focus.exit_ts + 48 * 3600);
  else if (focus) goTrade(S.tradeIdx);
  renderTradeNav();
}

function goTrade(i) {
  const x = candleView?.shown[i];
  if (!x) return;
  S.tradeIdx = i;
  candleView.show(x);
  renderTradeNav();
}

/** ← transakcja k z N → — przeskok między narysowanymi transakcjami wybranej pary. */
function renderTradeNav() {
  const n = candleView?.shown.length || 0;
  let nav = $('#cd-nav');
  if (!nav) { nav = h('span', { id: 'cd-nav', class: 'row' }); $('#cd-tools').append(nav); }
  if (!n) { nav.replaceChildren(); return; }
  const i = Math.max(0, S.tradeIdx);
  const x = candleView.shown[i];
  nav.replaceChildren(
    h('button', { class: 'btn small', disabled: i <= 0, onclick: () => goTrade(i - 1), title: 'poprzednia transakcja' }, '←'),
    h('span', { class: 'hint mono' }, `${i + 1}/${n} · ${dateUTC(x.entry, true)}`),
    h('button', { class: 'btn small', disabled: i >= n - 1, onclick: () => goTrade(i + 1), title: 'następna transakcja' }, '→'));
}

async function focusTrade(tr) {
  const el = $('#candles');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  if (tr.pair !== S.chartPair) { S.chartPair = tr.pair; await renderCandles(filtered(), tr); }
  else {
    const k = candleView?.shown.findIndex((x) => x.trade === tr) ?? -1;
    if (k >= 0) goTrade(k); else candleView?.focus(tr.entry_ts - 48 * 3600, tr.exit_ts + 48 * 3600);
  }
}

async function loadCode(e) {
  const pre = $('pre', e.target);
  if (e.target.open && pre.dataset.loaded !== '1') {
    try { pre.textContent = await getText(S.base + 'strategy.py'); pre.dataset.loaded = '1'; } catch (err) { pre.textContent = String(err); }
  }
}
