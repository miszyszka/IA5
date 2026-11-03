// Zakładka FOREST v2 (D-049). Prosto: co teraz, dlaczego, jaki wynik, czego system się nauczył; szczegóły schowane głębiej.
// Wszystko liczy Mac przy ia5 start; strona czyta forest/ z gałęzi data (0 odczytów Firestore).
import { disposeAll, equityLines } from './charts.js';
import { getJSON, getText, readRows } from './data.js';
import { filterJournal, forestReason, forestStatus, PAIRS, toCSV } from './metrics.js';
import { heartbeatState } from './status.js';
import { $, ago, cls, copy, dateUTC, download, h, local, num, signed, store, toast } from './util.js';

const SEG = { HISTORIA: 'Historia', TEST: 'Test', LIVE: 'Na żywo' };
const SEG_NOTE = { HISTORIA: 'na tych świecach ustalono zasady', TEST: 'świece, których zasady nie widziały', LIVE: 'nowe świece: to rozstrzyga' };
const ui = { only: true, pair: '', wynik: '', month: null, open: null, band: null, more: 40 };
const rowsCache = new Map();
let invP = null, invKey = null;

export async function loadForest() {
  try {
    const st = await getJSON('forest/state.json');
    store.set('forestError', null);
    if (!st || st.computedAt !== store.state.forest?.computedAt) store.set('forest', st);
  } catch (e) {
    store.set('forestError', e.message || String(e));
    store.set('forest', null);
  }
}

function investors(st) {
  if (invKey !== st.computedAt) { invKey = st.computedAt; invP = getJSON('forest/investors.json').catch(() => null); }
  return invP;
}

const kpi = (label, val, c = '') => h('div', { class: 'kpi' }, h('small', {}, label), h('b', { class: c }, val));
const pairName = (p) => PAIRS[p]?.label || p;
const side = (d) => (d > 0 ? 'BUY' : 'SELL');
const panel = (title, hint, ...body) => h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, title), hint ? h('span', { class: 'hint' }, hint) : null), ...body);

function statTable(st) {
  const rows = [];
  for (const s of ['LIVE', 'TEST', 'HISTORIA']) {
    for (const b of ['m', 'k']) {
      const v = st.books[b].seg[s];
      if (!v?.n) continue;
      rows.push(h('tr', {}, h('td', { class: 'txt' }, SEG[s]), h('td', { class: 'txt' }, st.books[b].name), h('td', { class: 'r' }, num(v.n, 0)), h('td', { class: 'r' }, `${num(v.win, 1)}%`),
        h('td', { class: `r ${cls(v.net)}` }, signed(v.net, 2)), h('td', { class: `r ${cls(v.swap)}` }, signed(v.swap, 2)), h('td', { class: 'r' }, num(v.t, 1)), h('td', { class: `r ${cls(v.usd)}` }, signed(v.usd, 0))));
    }
  }
  return h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
    h('thead', {}, h('tr', {}, ...['odcinek', 'kto', 'transakcje', 'wygrane', 'netto pips', 'po nocach', 'pewność t', 'wynik USD'].map((l) => h('th', {}, l)))), h('tbody', {}, ...rows)));
}

function nowPanel(st) {
  const p = st.params;
  const rows = st.now.map((n) => {
    const r = forestReason(n, p);
    const open = st.open.find((x) => x.pair === n.pair);
    return h('tr', { class: r.enter ? 'sel' : '' }, h('td', { class: 'txt' }, h('b', {}, pairName(n.pair))), h('td', { class: 'r' }, n.n), h('td', { class: 'r' }, n.up), h('td', { class: 'r' }, n.dn),
      h('td', { class: 'r' }, n.n ? `${Math.round(n.cons * 100)}%` : '—'), h('td', { class: 'txt' }, r.enter ? h('b', {}, r.text) : r.text),
      h('td', { class: `txt ${cls(open?.wycena)}` }, open ? `${side(open.dir)} od ${local(open.entry_ts)}, ${signed(open.wycena, 1)} pips` : '—'));
  });
  return panel('Teraz', `ostatnia świeca do ${local(st.dataTo)} · Manager wchodzi przy co najmniej ${p.QUORUM} głosach i ${Math.round(p.CONSENSUS * 100)}% zgody`,
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['para', 'głosuje', 'BUY', 'SELL', 'zgoda', 'decyzja Managera', 'otwarta pozycja'].map((l) => h('th', {}, l)))), h('tbody', {}, ...rows))));
}

function learnPanel(st) {
  const g = st.generations;
  const last = g[g.length - 1];
  const next = last ? last.ts + 4 * 7 * 86400 : null;
  const tab = h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['odświeżenie', 'spełniło warunki', 'w lesie', 'doszło', 'odpadło'].map((l) => h('th', {}, l)))),
    h('tbody', {}, ...[...g].reverse().slice(0, 8).map((x) => h('tr', {}, h('td', { class: 'txt' }, dateUTC(x.ts)), h('td', { class: 'r' }, x.passed), h('td', { class: 'r' }, x.kept), h('td', { class: 'r' }, `+${x.added}`), h('td', { class: 'r' }, `−${x.retired}`)))));
  return panel('Czego się uczy', last ? `co 4 tygodnie las wybierany jest od nowa · następne odświeżenie ${dateUTC(next)}` : '',
    h('p', { class: 'muted small' }, `Inwestor wchodzi do lasu, gdy na wszystkich zamkniętych danych ma zysk po spreadzie, co najmniej ${st.params.MIN_EVENTS} oddzielnych zdarzeń i stabilny wynik. Gdy to straci, wypada.`),
    h('div', { class: 'tablewrap' }, tab));
}

function bandPanel(st) {
  const segs = Object.keys(st.bands);
  if (!segs.length) return '';
  const s = segs.includes(ui.band) ? ui.band : segs.includes('LIVE') ? 'LIVE' : segs.includes('TEST') ? 'TEST' : segs[0];
  return panel('Co znaczy zgoda', 'każda decyzja, także niewykonana; pipsy na transakcję',
    h('div', { class: 'row wrap' }, ...segs.map((x) => h('button', { class: `chip toggle ${x === s ? 'on' : ''}`, onclick: () => { ui.band = x; render(); } }, SEG[x] || 'Razem'))),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['zgoda', 'decyzje', 'wygrane', 'netto', 'po nocach'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...st.bands[s].filter((r) => r.n).map((r) => h('tr', {}, h('td', { class: 'txt' }, r.band), h('td', { class: 'r' }, num(r.n, 0)), h('td', { class: 'r' }, `${num(r.win, 1)}%`), h('td', { class: `r ${cls(r.net)}` }, signed(r.net, 2)), h('td', { class: `r ${cls(r.swap)}` }, signed(r.swap, 2))))))));
}

const J = [['ts', 'decyzja'], ['pair', 'para'], ['side', 'kierunek'], ['h', 'świec'], ['n', 'głosów'], ['cons', 'zgoda'], ['why', 'co zrobił'], ['net', 'netto'], ['status', 'status']];
const WHY = { go: 'wejście', few: 'za mało głosów', split: 'za mała zgoda', busy: 'para zajęta' };

async function votersBox(st, r) {
  const inv = await investors(st);
  const map = new Map((inv?.investors || []).map((x) => [x.id, x]));
  const list = r.voters.split(',').filter(Boolean).map((v) => ({ s: v[0], x: map.get(+v.slice(1)), id: v.slice(1) }));
  return h('div', { class: 'fvoters' }, h('b', {}, `Kto głosował (${list.length})`), h('ul', { class: 'plain small' }, ...list.slice(0, 60).map((v) => h('li', {}, `${v.s === '+' ? 'BUY' : 'SELL'} · #${v.id} · ${v.x?.rule || ''} · ${v.x?.h || ''} świec`))));
}

function journalPanel(st) {
  const months = st.months || [];
  const month = months.includes(ui.month) ? ui.month : months[months.length - 1];
  ui.month = month;
  const box = h('div', {}, h('div', { class: 'empty small' }, 'Wczytywanie…'));
  const sel = (label, val, opts, on) => h('select', { 'aria-label': label, onchange: (e) => on(e.target.value) }, ...opts.map(([v, t]) => h('option', { value: v, selected: String(val) === String(v) }, t)));
  const f = h('div', { class: 'row wrap' }, sel('Miesiąc', month, [...months].reverse().map((m) => [m, m]), (v) => { ui.month = v; render(); }),
    sel('Zakres', ui.only ? 1 : 0, [[1, 'transakcje Managera'], [0, 'wszystkie decyzje']], (v) => { ui.only = v === '1'; render(); }),
    sel('Para', ui.pair, [['', 'wszystkie pary'], ...st.pairs.map((p) => [p, pairName(p)])], (v) => { ui.pair = v; render(); }),
    sel('Wynik', ui.wynik, [['', 'zysk i strata'], ['zysk', 'zysk'], ['strata', 'strata']], (v) => { ui.wynik = v; render(); }));
  (async () => {
    if (!month) { box.replaceChildren(h('div', { class: 'empty small' }, 'Jeszcze bez decyzji.')); return; }
    const key = `${st.computedAt}:${month}`;
    if (!rowsCache.has(key)) rowsCache.set(key, readRows(`forest/journal/${month}.parquet`));
    try {
      const rows = filterJournal(await rowsCache.get(key), ui).reverse();
      const tr = rows.slice(0, 300).flatMap((r) => {
        const row = h('tr', { class: r.ex_m ? '' : 'thin', onclick: () => { ui.open = ui.open === r.seq ? null : r.seq; render(); } },
          h('td', {}, local(r.ts + 3600)), h('td', { class: 'txt' }, pairName(r.pair)), h('td', { class: 'txt' }, r.dir ? side(r.dir) : '—'), h('td', { class: 'r' }, r.h || '—'), h('td', { class: 'r' }, r.n), h('td', { class: 'r' }, `${Math.round(r.cons * 100)}%`),
          h('td', { class: 'txt' }, r.ex_m ? 'wejście' : WHY[r.why] || r.why), h('td', { class: `r ${cls(r.net)}` }, r.net == null ? '—' : signed(r.net, 1)), h('td', { class: 'txt' }, r.status));
        if (ui.open !== r.seq) return [row];
        const cellBox = h('td', { colspan: J.length }, 'Wczytywanie…');
        votersBox(st, r).then((x) => cellBox.replaceChildren(x));
        return [row, h('tr', {}, cellBox)];
      });
      const csv = () => download(`forest-${month}.csv`, toCSV(rows.map((r) => ({ ...r, ts: local(r.ts + 3600), side: r.dir ? side(r.dir) : '' })), J.map(([k]) => k).concat('voters')), 'text/csv');
      box.replaceChildren(h('div', { class: 'row end' }, h('button', { class: 'btn ghost small', onclick: csv }, 'Eksport CSV')),
        rows.length ? h('div', { class: 'tablewrap fjournal' }, h('table', { class: 'data compact' }, h('thead', {}, h('tr', {}, ...J.map(([, l]) => h('th', {}, l)))), h('tbody', {}, ...tr))) : h('div', { class: 'empty small' }, 'Brak pozycji dla tych filtrów.'));
    } catch (e) { box.replaceChildren(h('div', { class: 'banner warn' }, `Dziennik: ${e.message || e}`)); }
  })();
  return panel('Dziennik', 'klik w wiersz: kto głosował', f, box);
}

function details(st) {
  const inv = h('div', {}, 'Wczytywanie…');
  investors(st).then((x) => {
    const act = (x?.investors || []).filter((i) => i.aktywny);
    inv.replaceChildren(h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['#', 'reguła (strona BUY, SELL to lustro)', 'horyzont', 'zdarzenia', 't', 'w lesie od'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...act.slice(0, ui.more).map((i) => h('tr', {}, h('td', { class: 'r' }, i.id), h('td', { class: 'txt frule' }, i.rule), h('td', { class: 'r' }, i.h), h('td', { class: 'r' }, i.ev), h('td', { class: 'r' }, num(i.t, 2)), h('td', { class: 'txt' }, dateUTC(i.od))))))),
    act.length > ui.more ? h('button', { class: 'btn ghost small', onclick: () => { ui.more += 100; render(); } }, `Pokaż więcej (${act.length - ui.more})`) : '');
  });
  const grid = Object.entries(st.grid).map(([s, rows]) => {
    const ns = [...new Set(rows.map((r) => r.n_min))], cs = [...new Set(rows.map((r) => r.c_min))];
    return h('div', {}, h('b', {}, SEG[s] || 'Razem'), h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, h('th', {}, 'głosy ≥ / zgoda ≥'), ...cs.map((c) => h('th', { class: 'r' }, `${Math.round(c * 100)}%`)))),
      h('tbody', {}, ...ns.map((a) => h('tr', {}, h('td', { class: 'txt' }, a), ...cs.map((c) => { const r = rows.find((x) => x.n_min === a && x.c_min === c); return h('td', { class: `r ${cls(r.net)}`, title: `${r.n} transakcji, t ${r.t}` }, r.n ? signed(r.net, 1) : '—'); })))))));
  });
  return h('details', { class: 'panel fdetails' }, h('summary', {}, h('b', {}, 'Szczegóły: inwestorzy, wszystkie progi, dane bez przewagi')),
    h('h3', {}, `Inwestorzy w lesie (${st.counts.las})`), inv,
    h('h3', {}, 'Wszystkie progi: netto w pipsach na transakcję'), h('p', { class: 'muted small' }, 'Nie wybieraj najlepszej kratki po fakcie: przy tylu kratkach któraś zawsze wygląda dobrze.'), ...grid,
    h('h3', {}, 'Dane bez przewagi'), h('ul', { class: 'plain small' }, ...(st.zero || []).map((z) => h('li', {}, `Przebieg ${z.seed}: średnio ${z.passed} reguł spełnia warunki, ${z.kept} w lesie; Manager: ` + Object.entries(z.seg).filter(([, v]) => v.n).map(([k, v]) => `${SEG[k]} ${v.n} transakcji, ${signed(v.net, 2)} pips`).join(' · ')))),
    h('div', { class: 'row' }, h('button', { class: 'btn ghost small', onclick: async () => toast((await copy(await getText('forest/report.md'))) ? 'Skopiowano raport dla Claude.' : 'Nie udało się skopiować.', 'ok') }, 'Kopiuj raport dla Claude')));
}

function render() {
  const root = $('#view-forest');
  if (store.state.route?.view !== 'forest') return;
  const st = store.state.forest;
  const s = forestStatus(st, heartbeatState(store.state.beat));
  disposeAll();
  if (!st?.generations) {
    root.replaceChildren(h('div', { class: 'toolbar' }, h('h2', {}, 'FOREST')), store.state.forestError ? h('div', { class: 'banner warn' }, `GitHub: ${store.state.forestError}`) : '',
      h('div', { class: 'empty' }, h('h3', {}, st ? 'Na stronie jest jeszcze stary las' : 'Las jeszcze nie jest zbudowany'), h('p', {}, 'Po git pull, uv tool install -e runner --force i restarcie ia5 start Mac zbuduje nową wersję sam.')));
    return;
  }
  const m = st.books.m, c = st.books.k;
  const head = h('div', { class: 'ihead panel' }, h('h2', {}, 'FOREST'),
    h('div', { class: 'istatus', 'data-state': s.state }, h('i', { class: 'dot flat' }), h('b', {}, s.word), h('span', {}, s.detail), h('span', { class: 'muted' }, ` · liczony ${ago(st.computedAt)}`)),
    h('p', { class: 'muted small' }, `Inwestorzy mówią tylko wtedy, gdy spełniona jest ich reguła. Manager wchodzi, gdy odezwie się co najmniej ${st.params.QUORUM} i ${Math.round(st.params.CONSENSUS * 100)}% jest po jednej stronie. Pozycja trwa ${st.horizons.join(' albo ')} świec. Co 4 tygodnie las jest wybierany od nowa.`),
    h('div', { class: 'kpis small' }, kpi('Manager', `${num(m.equity, 0)} USD (${signed(m.return_pct, 1)}%)`, cls(m.return_pct)), kpi('Kontrola bez progów', `${num(c.equity, 0)} USD (${signed(c.return_pct, 1)}%)`, cls(c.return_pct)), kpi('inwestorów w lesie', num(st.counts.las, 0)), kpi('otwarte pozycje', st.open.length)));
  const concl = st.conclusions.length ? panel('Co wiadomo', '', h('ul', { class: 'fconcl' }, ...st.conclusions.map((x) => h('li', { 'data-state': x.state }, h('i', { class: 'dot flat' }), x.text)))) : '';
  const eq = h('div', { class: 'chart tall' });
  const result = panel('Wynik', `start ${num(st.params.START_CAPITAL, 0)} USD · ${SEG_NOTE.TEST}: od ${dateUTC(st.design_end)}`, eq, statTable(st));
  root.replaceChildren(head, nowPanel(st), concl, result, journalPanel(st), learnPanel(st), bandPanel(st), details(st));
  const series = [['m', '--accent'], ['k', '--muted']].filter(([b]) => st.books[b].curve.ts.length > 1).map(([b, color]) => ({ name: st.books[b].name, ts: st.books[b].curve.ts, equity: st.books[b].curve.equity, color }));
  if (series.length) equityLines(eq, series, [{ ts: st.design_end, label: 'Test' }, { ts: st.built_to, label: 'Na żywo' }]);
}

export function renderForest() { render(); }

export function initForest() {
  store.on('forest', () => render());
  store.on('forestError', () => render());
  let prev = '';
  store.on('beat', () => {
    const w = forestStatus(store.state.forest, heartbeatState(store.state.beat)).word;
    if (w !== prev) { prev = w; render(); }
  });
}
