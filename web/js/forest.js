// Zakładka FOREST (D-048): 1000 wirtualnych inwestorów, Manager, mapy głosów. Wszystko liczy Mac przy ia5 start i publikuje
// na gałęzi data (forest/state.json, forest/investors.json, forest/report.md, forest/journal/{RRRR-MM}.parquet) — 0 odczytów Firestore.
import { disposeAll, equityLines } from './charts.js';
import { collapsible } from './collapse.js';
import { getJSON, getText, readRows } from './data.js';
import { filterJournal, forestStatus, PAIRS, toCSV, votesFromHex } from './metrics.js';
import { heartbeatState } from './status.js';
import { $, ago, cls, copy, dateUTC, download, h, local, num, signed, store, toast } from './util.js';

const SEG_NAME = { MAPY: 'MAPY (rozgrzewka, część IS)', OOS: 'OOS (ostatnie 25%)', LIVE: 'LIVE (nowe świece)', RAZEM: 'razem' };
const BOOK_COLOR = { a: '--muted', b: '--accent', c: '--text' };
const BOOK_NOTE = {
  a: 'Grupa kontrolna: 1 inwestor = 1 głos, handluje zawsze, gdy para jest wolna. Nic się nie uczy.',
  b: 'Decyzja jak w A, ale wejście tylko gdy podobne mapy dają z ≥ próg. Horyzont: najlepsze z.',
  c: 'Głos waży tyle, ile inwestor zarobił punktów na mapach ponad średnią. Handluje jak A.',
};
const ui = { seg: null, focus: null, month: null, book: 'a', only: false, pair: '', dir: 0, status: '', wynik: '', famF: '', sort: 'punkty', show: 40 };
const rowsCache = new Map();   // `${id}:${month}:${computedAt}` → wiersze dziennika
let invP = null;               // obietnica katalogu inwestorów (klucz: computedAt)
let invKey = null;

export async function loadForest() {
  try {
    const st = await getJSON('forest/state.json');
    store.set('forestError', null);
    if (!st || st.computedAt !== store.state.forest?.computedAt) store.set('forest', st);   // ten sam stan = bez przerysowania
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
const word = (d) => (d > 0 ? 'BUY' : 'SELL');
const pairName = (p) => PAIRS[p]?.label || p;
const pill = (s) => h('span', { class: 'ipill', 'data-state': s.state, title: s.detail }, h('i', { class: 'dot flat' }), h('b', {}, s.word));

// ---------- mapa głosów: kratka za inwestora, układ po rodzinach ----------

function mapGrid(st, hex, dir, meta) {
  const m = st.n_investors;
  const votes = votesFromHex(hex, m);
  const fams = st.families;
  const groups = fams.map(() => []);
  st.order.forEach((k) => groups[st.fam[k]].push(k));
  const camp = (k) => (dir > 0 ? votes[k] : !votes[k]);
  const box = h('div', { class: 'fmap', role: 'img', 'aria-label': meta || 'Mapa głosów 1000 inwestorów' });
  groups.forEach((g, i) => {
    if (!g.length) return;
    const za = g.filter(camp).length;
    const cells = h('div', { class: 'fcells' });
    const frag = document.createDocumentFragment();
    for (const k of g) { const c = document.createElement('i'); c.dataset.k = k + 1; if (camp(k)) c.className = 'on'; frag.append(c); }
    cells.append(frag);
    box.append(h('div', { class: 'ffam' }, h('div', { class: 'row between' }, h('b', {}, fams[i]), h('span', { class: 'mono hint' }, `${za}/${g.length} za`)), cells));
  });
  box.addEventListener('mousemove', async (e) => {
    const k = e.target?.dataset?.k;
    if (!k || e.target.title) return;
    const inv = await investors(st);
    const x = inv?.investors?.[k - 1];
    if (x) e.target.title = `#${x.id} · ${x.fam} · ${x.rule}`;
  });
  return box;
}

function focusPanel(st) {
  const f = ui.focus;
  const head = h('div', { class: 'phead' }, h('h3', {}, 'Mapa głosów'),
    h('span', { class: 'hint' }, 'pomarańczowe = obóz „za” decyzją, szare = „przeciw”; kolumny = rodziny inwestorów; najedź na kratkę: reguła inwestora'));
  const tabs = h('div', { class: 'row wrap' },
    ...st.now.map((n) => h('button', { class: `chip toggle ${f?.kind === 'now' && f.pair === n.pair ? 'on' : ''}`, onclick: () => { ui.focus = { kind: 'now', pair: n.pair }; render(); } }, pairName(n.pair))),
    h('button', { class: `chip toggle ${f?.kind === 'zysk' ? 'on' : ''}`, onclick: () => { ui.focus = { kind: 'zysk' }; render(); } }, 'Mapa Zysku'),
    h('button', { class: `chip toggle ${f?.kind === 'strata' ? 'on' : ''}`, onclick: () => { ui.focus = { kind: 'strata' }; render(); } }, 'Mapa Straty'));
  let body;
  if (f?.kind === 'zysk' || f?.kind === 'strata') {
    const zysk = f.kind === 'zysk';
    body = [h('p', { class: 'muted small' }, zysk
      ? `Mapa Zysku: po której stronie inwestor bywał częściej, gdy transakcja kończyła się zyskiem (${num(st.counts.zyskowne, 0)} map).`
      : `Mapa Straty: to samo dla transakcji stratnych (${num(st.counts.stratne, 0)} map). Gdy obie mapy wyglądają tak samo, układ głosów nie odróżnia zysku od straty.`),
    mapGrid(st, zysk ? st.mapa_zysku : st.mapa_straty, 1, zysk ? 'Mapa Zysku' : 'Mapa Straty')];
  } else if (f?.kind === 'row') {
    const r = f.row;
    body = [h('p', { class: 'muted small' }, `Decyzja #${r.seq} · ${pairName(r.pair)} · ${word(r.b_dir)} na ${r.b_h} św. · ${local(r.ts + 3600)} · za ${r.za}, przeciw ${r.przeciw}`
      + (r.net == null ? '' : ` · wynik ${signed(r.net, 1)} pips netto`)), f.hex ? mapGrid(st, f.hex, r.b_dir, `Mapa decyzji ${r.seq}`) : h('div', { class: 'empty small' }, 'Wczytywanie mapy…')];
  } else {
    const n = st.now.find((x) => x.pair === (f?.pair || st.now[0]?.pair));
    body = n ? [h('p', { class: 'muted small' }, `${pairName(n.pair)} · świeca zamknięta ${local(n.ts + 3600)} · ${word(n.dir)}, BUY ${n.buy} : SELL ${n.sell}${n.okno ? '' : ' · poza oknem 07–17, bez wejścia'}`),
      mapGrid(st, n.votes, n.dir, `Mapa głosów ${n.pair}`)] : [];
  }
  return h('section', { class: 'panel', id: 'f-map' }, head, tabs, ...body);
}

// ---------- teraz ----------

function nowPanel(st, trades) {
  const rows = st.now.map((n) => {
    const open = trades.filter((p) => p.pair === n.pair);
    const share = n.buy / (n.buy + n.sell) * 100;
    return h('tr', { class: ui.focus?.pair === n.pair ? 'sel' : '', onclick: () => { ui.focus = { kind: 'now', pair: n.pair }; render(); $('#f-map')?.scrollIntoView({ block: 'nearest' }); } },
      h('td', { class: 'txt' }, h('b', {}, pairName(n.pair))),
      h('td', { class: 'txt' }, local(n.ts + 3600)),
      h('td', { class: 'r' }, n.buy),
      h('td', { class: 'fbarcell' }, h('div', { class: 'fbar', title: `BUY ${n.buy} : SELL ${n.sell}` }, h('i', { style: { width: `${share}%` } }))),
      h('td', { class: 'r' }, n.sell),
      h('td', { class: 'txt' }, n.okno ? h('b', {}, word(n.dir)) : h('span', { class: 'muted' }, `${word(n.dir)} · poza oknem`)),
      h('td', { class: 'r' }, n.okno ? `${n.h} św.` : '—'),
      h('td', { class: `r ${cls(n.f[n.h - 1])}` }, signed(n.f[n.h - 1], 1)),
      h('td', { class: 'r' }, n.k ? `${n.w}:${n.l}` : '—'),
      h('td', { class: `r ${cls(n.z)}` }, n.k ? signed(n.z, 2) : '—'),
      h('td', { class: 'r' }, n.k ? `${num(n.dop * 100, 1)}%` : '—'),
      h('td', { class: 'txt' }, n.take_b ? `wchodzi, ${n.h_b} św.` : 'czeka'),
      h('td', { class: 'txt' }, `${word(n.dir_c)}, ${n.h_c} św.`),
      h('td', { class: 'txt' }, open.length ? open.map((p) => `${p.book.toUpperCase()} ${word(p.dir)} ${signed(p.wycena, 1)}`).join(' · ') : '—'));
  });
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Teraz: głos 1000 inwestorów i decyzja Managera'),
      h('span', { class: 'hint' }, `kolejne głosowanie po następnej świecy · prognoza = średni prognozowany zysk obozu po spreadzie, w pipsach`)),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact fnow' },
      h('thead', {}, h('tr', {}, ...['para', 'świeca do', 'BUY', '', 'SELL', 'Manager', 'horyzont', 'prognoza', 'mapy W:L', 'z', 'dopasowanie', 'księga B', 'księga C', 'otwarte'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...rows))));
}

// ---------- księgi ----------

function booksPanel(st) {
  const box = h('div', { id: 'f-eq', class: 'chart tall' });
  const seg = ['MAPY', 'OOS', 'LIVE'];
  const rows = [];
  for (const [b, x] of Object.entries(st.books)) {
    for (const s of seg) {
      const v = x.seg[s];
      if (!v?.n) continue;
      rows.push(h('tr', {}, h('td', { class: 'txt', title: BOOK_NOTE[b] }, `${b.toUpperCase()} ${x.name}`), h('td', { class: 'txt' }, s), h('td', { class: 'r' }, num(v.n, 0)),
        h('td', { class: 'r' }, `${num(v.win, 1)}%`), h('td', { class: `r ${cls(v.gross)}` }, signed(v.gross, 2)), h('td', { class: `r ${cls(v.net)}` }, signed(v.net, 2)),
        h('td', { class: 'r' }, signed(v.t, 1)), h('td', { class: `r ${cls(v.usd)}` }, signed(v.usd, 0))));
    }
  }
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Księgi: czy nauka cokolwiek daje'),
      h('span', { class: 'hint' }, `start ${num(st.params.START_CAPITAL, 0)} USD · depozyt ${st.params.BOOK_PCT}% · ${st.params.LEVERAGE}:1 · księga B rusza po ${num(st.params.MIN_MAPS, 0)} mapach`)),
    h('div', { class: 'kpis small' }, ...Object.entries(st.books).map(([b, x]) => kpi(`${b.toUpperCase()} ${x.name}`, `${num(x.equity, 0)} USD (${signed(x.return_pct, 1)}%)`, cls(x.return_pct)))),
    box,
    h('ul', { class: 'plain muted small' }, ...Object.entries(BOOK_NOTE).map(([b, t]) => h('li', {}, h('b', {}, `${b.toUpperCase()}: `), t))),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
      h('thead', {}, h('tr', {}, ...['księga', 'odcinek', 'transakcje', 'wygrane', 'brutto pips', 'netto pips', 't netto', 'wynik USD'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...rows))));
}

// ---------- co znaczy głos ----------

function cellTable(t) {
  return h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
    h('thead', {}, h('tr', {}, h('th', {}, t.name), ...['n', 'wygrane', 'brutto', 'netto', 't netto'].map((l) => h('th', { class: 'r' }, l)))),
    h('tbody', {}, ...t.rows.filter((r) => r.n).map((r) => h('tr', {}, h('td', { class: 'txt' }, r.band), h('td', { class: 'r' }, num(r.n, 0)), h('td', { class: 'r' }, `${num(r.win, 1)}%`),
      h('td', { class: `r ${cls(r.gross)}` }, signed(r.gross, 2)), h('td', { class: `r ${cls(r.net)}` }, signed(r.net, 2)), h('td', { class: 'r' }, signed(r.t, 1)))))));
}

function meaningPanel(st) {
  const segs = Object.keys(st.meaning).filter((s) => st.meaning[s].wszystkie.n);
  if (!segs.length) return '';
  const seg = segs.includes(ui.seg) ? ui.seg : segs.includes('LIVE') ? 'LIVE' : segs.includes('OOS') ? 'OOS' : segs[0];
  const t = st.meaning[seg];
  const u = t.uczenie;
  const line = (label, x) => h('li', {}, `${label}: `, x?.rho == null ? 'za mało danych' : h('b', { class: 'mono' }, `ρ ${signed(x.rho, 3)}, p ${num(x.p, 3)}`), x?.n ? ` (${num(x.n, 0)} decyzji)` : '');
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Co znaczy głos'),
      h('span', { class: 'hint' }, 'każda decyzja Managera, także niewykonana, liczona wirtualnie na swoim horyzoncie; pipsy na transakcję')),
    h('div', { class: 'row wrap' }, ...segs.map((s) => h('button', { class: `chip toggle ${s === seg ? 'on' : ''}`, onclick: () => { ui.seg = s; render(); } }, SEG_NAME[s]))),
    h('ul', { class: 'plain muted small' }, line('Czy z przewiduje wynik', u.z_vs_wynik), line('Czy przewaga głosów przewiduje wynik', u.przewaga_vs_wynik), line('Czy zysk podobnych map przewiduje wynik', u.g_map_vs_wynik),
      h('li', {}, 'p z obrotów w czasie; p ≥ 0,05 znaczy: nie da się odróżnić od przypadku.')),
    h('div', { class: 'grid2' }, ...['przewaga', 'z', 'z_b', 'dop', 'horyzont', 'kierunek', 'para'].map((k) => cellTable(t[k]))));
}

// ---------- las ----------

function qualityRows(q, label) {
  return Object.entries(q || {}).map(([seg, v]) => h('tr', {}, h('td', { class: 'txt' }, label), h('td', { class: 'txt' }, seg), h('td', { class: 'r' }, num(v.decyzje, 0)),
    ...v.trafnosc_srednia.map((x) => h('td', { class: 'r' }, `${num(x, 2)}%`)), h('td', { class: 'r' }, v.ponad_51)));
}

function catalogPanel(st) {
  const list = h('div', {}, h('div', { class: 'empty small' }, 'Wczytywanie inwestorów…'));
  const seg = st.quality.LIVE ? 'LIVE' : st.quality.OOS ? 'OOS' : 'MAPY';
  const avg = (a) => (a?.length ? a.reduce((x, y) => x + (y ?? 0), 0) / a.length : null);
  const draw = async () => {
    const inv = await investors(st);
    if (!inv) { list.replaceChildren(h('div', { class: 'empty small' }, 'Brak katalogu inwestorów.')); return; }
    let x = inv.investors.filter((i) => !ui.famF || i.fam === ui.famF).map((i) => ({ ...i, h: avg(i.hit[seg]) }));
    x = x.sort((a, b) => (ui.sort === 'hit' ? (b.h ?? 0) - (a.h ?? 0) : ui.sort === 't_cv' ? b.t_cv - a.t_cv : b.punkty - a.punkty));
    list.replaceChildren(
      h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
        h('thead', {}, h('tr', {}, ...['#', 'rodzina', 'reguła', 'stany', 'siła w kuciu', `trafność ${seg}`, 'punkty map', 'waga głosu'].map((l) => h('th', {}, l)))),
        h('tbody', {}, ...x.slice(0, ui.show).map((i) => h('tr', {}, h('td', { class: 'r' }, i.id), h('td', { class: 'txt' }, i.fam), h('td', { class: 'txt frule' }, i.rule), h('td', { class: 'r' }, i.stany),
          h('td', { class: 'r' }, num(i.t_cv, 2)), h('td', { class: 'r' }, i.h == null ? '—' : `${num(i.h, 2)}%`), h('td', { class: `r ${cls(i.punkty)}` }, signed(i.punkty, 0)), h('td', { class: 'r' }, i.waga == null ? '—' : num(i.waga, 2))))))),
      x.length > ui.show ? h('button', { class: 'btn ghost small', onclick: () => { ui.show += 100; draw(); } }, `Pokaż więcej (${x.length - ui.show})`) : '');
  };
  draw();
  const sortBtn = (k, l) => h('button', { class: `chip toggle ${ui.sort === k ? 'on' : ''}`, onclick: () => { ui.sort = k; render(); } }, l);
  const famSel = h('select', { 'aria-label': 'Rodzina', onchange: (e) => { ui.famF = e.target.value; ui.show = 40; render(); } }, h('option', { value: '' }, 'wszystkie rodziny'),
    ...st.families.map((f) => h('option', { value: f, selected: ui.famF === f }, f)));
  return h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, '1000 inwestorów')),
    h('div', { class: 'row wrap' }, famSel, sortBtn('punkty', 'wg punktów map'), sortBtn('hit', 'wg trafności'), sortBtn('t_cv', 'wg siły w kuciu')), list);
}

function forgePanel(st) {
  const f = st.forge;
  const z = st.zero?.[0];
  return h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Las: skąd 1000 inwestorów i czy naprawdę się różnią'),
      h('span', { class: 'hint' }, `reguły z pierwszych 50% historii, ocena poza próbą blokami czasu · las ${st.id}`)),
    h('div', { class: 'kpis small' },
      kpi('sprawdzeni kandydaci', num(f.candidates, 0)), kpi('po bramkach kucia', num(f.passed, 0)),
      kpi('niezależne głosy (N_eff)', num(f.n_eff, 1)), kpi('średnia |korelacja|', num(f.srednia_abs_rho, 3)), kpi('limit korelacji', num(f.rho_cap, 2)),
      kpi('siła w kuciu: średnia', num(f.t_cv_mean, 2)), kpi('na danych bez przewagi', z ? num(z.forge.t_cv_mean, 2) : '—'),
      kpi('po bramkach bez przewagi', z ? num(z.forge.passed, 0) : '—')),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
      h('thead', {}, h('tr', {}, ...['dane', 'odcinek', 'decyzje', 'trafność 1 św.', '2 św.', '3 św.', '4 św.', '5 św.', 'ponad 51%'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...qualityRows(st.quality, 'prawdziwe'), ...(st.zero || []).flatMap((x) => qualityRows(x.quality, 'bez przewagi'))))),
    h('p', { class: 'muted small' }, `Rodziny głównych reguł: ${Object.entries(f.rodziny || {}).map(([k, v]) => `${k} ${v}`).join(' · ')}.`));
}

function mapsPanel(st) {
  const line = (x) => h('tr', { }, h('td', { class: 'r' }, `#${x.seq}`), h('td', { class: 'txt' }, pairName(x.pair)), h('td', { class: 'txt' }, `${word(x.dir)}, ${x.h} św.`), h('td', { class: 'txt' }, local(x.ts + 3600)),
    h('td', { class: 'r' }, `${x.za}:${x.przeciw}`), h('td', { class: `r ${cls(x.punkty)}` }, signed(x.punkty, 0)));
  const tab = (rows, name) => h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
    h('thead', {}, h('tr', {}, ...[name, 'para', 'decyzja', 'czas', 'za : przeciw', 'punkty'].map((l) => h('th', {}, l)))), h('tbody', {}, ...rows.map(line))));
  if (!st.maps?.zysk?.length && !st.maps?.strata?.length) return '';
  return h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Najsilniejsze mapy'),
    h('span', { class: 'hint' }, 'punkty = wynik własnej transakcji + punkty od podobnych transakcji zamkniętych później')),
  h('div', { class: 'grid2' }, tab(st.maps.zysk, 'zyskowne'), tab(st.maps.strata, 'stratne')));
}

// ---------- dziennik ----------

const J_COLS = [['seq', '#'], ['ts', 'decyzja (czas PL)'], ['pair', 'para'], ['b_dir', 'kierunek'], ['b_h', 'horyzont'], ['za', 'za'], ['przeciw', 'przeciw'], ['przewaga', 'przewaga'],
  ['forecast', 'prognoza'], ['maps', 'mapy w pamięci'], ['wl', 'W:L'], ['sila', 'siła'], ['z', 'z'], ['dop', 'dopasowanie'], ['m_zysk', 'do Mapy Zysku'], ['m_strata', 'do Mapy Straty'],
  ['gross', 'brutto'], ['net', 'netto'], ['pkt', 'punkt mapy za'], ['punkty', 'punkty mapy'], ['ks', 'księgi'], ['status', 'status']];

async function journalRows(st, month) {
  const key = `${st.id}:${month}:${st.computedAt}`;
  if (!rowsCache.has(key)) {
    rowsCache.set(key, readRows(`forest/journal/${month}.parquet`).catch((e) => { rowsCache.delete(key); throw e; }));
  }
  return rowsCache.get(key);
}

function jRow(r) {
  const pc = (x) => (x == null || Number.isNaN(x) ? '—' : `${num(x * 100, 1)}%`);
  const ks = ['a', 'b', 'c'].filter((b) => r[`ex_${b}`]).map((b) => b.toUpperCase()).join(' ') || '—';
  const pick = () => { ui.focus = { kind: 'row', row: r, hex: r.votes }; render(); $('#f-map')?.scrollIntoView({ block: 'nearest' }); };
  return h('tr', { class: `${r.executed ? '' : 'thin'} ${ui.focus?.row?.seq === r.seq ? 'sel' : ''}`, onclick: pick },
    h('td', { class: 'r' }, r.seq), h('td', {}, local(r.ts + 3600)), h('td', { class: 'txt' }, pairName(r.pair)), h('td', { class: 'txt' }, r.b_dir > 0 ? 'long (BUY)' : 'short (SELL)'),
    h('td', { class: 'r' }, r.b_h), h('td', { class: 'r' }, r.za), h('td', { class: 'r' }, r.przeciw), h('td', { class: 'r' }, pc(r.przewaga)), h('td', { class: `r ${cls(r.forecast)}` }, signed(r.forecast, 1)),
    h('td', { class: 'r' }, num(r.maps, 0)), h('td', { class: 'r' }, r.k ? `${r.w}:${r.l}` : '—'), h('td', { class: `r ${cls(r.sila)}` }, r.k ? signed(r.sila, 3) : '—'), h('td', { class: `r ${cls(r.z)}` }, r.k ? signed(r.z, 2) : '—'),
    h('td', { class: 'r' }, r.k ? pc(r.dop) : '—'), h('td', { class: 'r' }, pc(r.m_zysk)), h('td', { class: 'r' }, pc(r.m_strata)),
    h('td', { class: `r ${cls(r.gross)}` }, r.gross == null ? '—' : signed(r.gross, 1)), h('td', { class: `r ${cls(r.net)}` }, r.net == null ? '—' : signed(r.net, 1)),
    h('td', { class: `r ${cls(r.pkt)}` }, r.pkt ? signed(r.pkt, 0) : '—'), h('td', { class: `r ${cls(r.punkty)}` }, r.known >= 5 ? signed(r.punkty, 0) : '—'), h('td', { class: 'txt' }, ks),
    h('td', { class: `txt ${r.status === 'otwarta' ? 'run' : r.status === 'anulowana' ? 'warn' : ''}` }, r.status));
}

function journalPanel(st) {
  const months = st.months || [];
  const month = months.includes(ui.month) ? ui.month : months[months.length - 1];
  ui.month = month;
  const box = h('div', {}, h('div', { class: 'empty small' }, 'Wczytywanie dziennika…'));
  const sel = (label, val, opts, on) => h('select', { 'aria-label': label, onchange: (e) => on(e.target.value) }, ...opts.map(([v, t]) => h('option', { value: v, selected: String(val) === String(v) }, t)));
  const filters = h('div', { class: 'row wrap' },
    sel('Miesiąc', month, [...months].reverse().map((m) => [m, m]), (v) => { ui.month = v; render(); }),
    sel('Księga', ui.book, [['a', 'księga A'], ['b', 'księga B'], ['c', 'księga C']], (v) => { ui.book = v; render(); }),
    h('label', { class: 'row small' }, h('input', { type: 'checkbox', checked: ui.only, onchange: (e) => { ui.only = e.target.checked; render(); } }), 'tylko wykonane'),
    sel('Para', ui.pair, [['', 'wszystkie pary'], ...st.pairs.map((p) => [p, pairName(p)])], (v) => { ui.pair = v; render(); }),
    sel('Kierunek', ui.dir, [[0, 'long i short'], [1, 'long'], [-1, 'short']], (v) => { ui.dir = +v; render(); }),
    sel('Wynik', ui.wynik, [['', 'zysk i strata'], ['zysk', 'tylko zysk'], ['strata', 'tylko strata']], (v) => { ui.wynik = v; render(); }));
  const panel = h('section', { class: 'panel', id: 'f-journal' },
    h('div', { class: 'phead' }, h('h3', {}, 'Dziennik decyzji'),
      h('span', { class: 'hint' }, 'każda decyzja z mapą głosów; wiersze szare: wirtualne (para zajęta); klik = mapa głosów')), filters, box);
  (async () => {
    if (!month) { box.replaceChildren(h('div', { class: 'empty small' }, 'Dziennik pojawi się po pierwszej decyzji.')); return; }
    try {
      const raw = await journalRows(st, month);
      const rows = filterJournal(raw, { book: ui.book, only: ui.only, pair: ui.pair, dir: ui.dir, wynik: ui.wynik }).reverse();
      const csv = () => download(`forest-${st.id}-${month}.csv`, toCSV(rows.map((r) => ({ ...r, ts: local(r.ts + 3600), wl: r.k ? `${r.w}:${r.l}` : '', ks: ['a', 'b', 'c'].filter((b) => r[`ex_${b}`]).join('') })), J_COLS.map(([k]) => k)), 'text/csv');
      const done = rows.filter((r) => r.net != null);
      const win = done.filter((r) => r.net > 0).length;
      box.replaceChildren(
        h('div', { class: 'row between wrap' }, h('span', { class: 'hint' }, `${num(rows.length, 0)} decyzji · zamknięte ${num(done.length, 0)} · wygrane ${done.length ? num(win / done.length * 100, 1) : '—'}% · netto razem ${signed(done.reduce((a, r) => a + r.net, 0), 0)} pips`),
          h('button', { class: 'btn ghost small', onclick: csv }, 'Eksport CSV')),
        h('div', { class: 'tablewrap fjournal' }, h('table', { class: 'data compact' },
          h('thead', {}, h('tr', {}, ...J_COLS.map(([, l]) => h('th', {}, l)))),
          h('tbody', {}, ...rows.slice(0, 400).map(jRow)))),
        rows.length > 400 ? h('p', { class: 'hint' }, `Widać 400 najnowszych z ${num(rows.length, 0)}; całość w eksporcie CSV.`) : '');
    } catch (e) {
      box.replaceChildren(h('div', { class: 'banner warn' }, `Nie udało się wczytać dziennika: ${e.message || e}`));
    }
  })();
  return panel;
}

// ---------- całość ----------

function timeline(st) {
  const c = st.cuts;
  const part = (cl, label, a, b) => h('div', { class: `fseg ${cl}` }, h('b', {}, label), h('span', { class: 'mono hint' }, b ? `${dateUTC(a)} – ${dateUTC(b)}` : `od ${dateUTC(a)}`));
  return h('div', { class: 'ftime' }, part('', 'KUCIE', c.t0, c.forge), part('', 'MAPY', c.forge, c.oos), part('', 'OOS', c.oos, c.t1), part('on', 'LIVE', c.t1, null));
}

function render() {
  const root = $('#view-forest');
  if (store.state.route?.view !== 'forest') return;
  const st = store.state.forest;
  const mac = heartbeatState(store.state.beat);
  const s = forestStatus(st, mac);
  disposeAll();
  if (!st) {
    root.replaceChildren(h('div', { class: 'toolbar' }, h('h2', {}, 'FOREST')),
      store.state.forestError ? h('div', { class: 'banner warn' }, `Nie udało się wczytać lasu z GitHub: ${store.state.forestError}`) : '',
      h('div', { class: 'empty' }, pill(s), h('h3', {}, 'Las jeszcze nie jest zbudowany'),
        h('p', {}, s.detail),
        h('p', { class: 'muted' }, '1000 wirtualnych inwestorów głosuje po każdej świecy: BUY albo SELL. Manager decyduje większością, wybiera horyzont i uczy się, które układy głosów kończyły się zyskiem.')));
    return;
  }
  const head = h('div', { class: 'ihead panel' },
    h('div', { class: 'row between wrap' }, h('h2', {}, 'FOREST'),
      h('div', { class: 'row' },
        h('button', { class: 'btn ghost small', onclick: async () => { const t = await getText('forest/report.md'); toast((await copy(t)) ? 'Skopiowano raport dla Claude.' : 'Nie udało się skopiować.', 'ok'); } }, 'Kopiuj raport dla Claude'),
        h('button', { class: 'btn ghost small', onclick: async () => download(`forest-${st.id}.md`, await getText('forest/report.md')) }, 'Pobierz report.md'))),
    h('div', { class: 'istatus', 'data-state': s.state }, h('i', { class: 'dot flat' }), h('b', {}, s.word), h('span', {}, s.detail),
      h('span', { class: 'muted' }, ` · ostatnie liczenie ${ago(st.computedAt)} · dane do ${local(st.dataTo)}`)),
    timeline(st),
    h('div', { class: 'kpis small' }, kpi('decyzje Managera', num(st.counts.decyzje, 0)), kpi('mapy w pamięci', num(st.counts.mapy, 0)), kpi('zyskowne / stratne', `${num(st.counts.zyskowne, 0)} / ${num(st.counts.stratne, 0)}`),
      kpi('inwestorzy', num(st.n_investors, 0)), kpi('niezależne głosy', num(st.forge.n_eff, 0)), kpi('otwarte pozycje', num(st.open.length, 0))));
  const concl = st.conclusions?.length ? h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Co na razie wiadomo'), h('span', { class: 'hint' }, 'wnioski liczone automatycznie, z tych samych progów przy każdym przeliczeniu')),
    h('ul', { class: 'fconcl' }, ...st.conclusions.map((c) => h('li', { 'data-state': c.state }, h('i', { class: 'dot flat' }), c.text)))) : '';
  if (!ui.focus) ui.focus = { kind: 'now', pair: st.now[0]?.pair };
  root.replaceChildren(head, concl, nowPanel(st, st.open), focusPanel(st), booksPanel(st), meaningPanel(st), journalPanel(st), mapsPanel(st), forgePanel(st), catalogPanel(st));
  collapsible(root, 'forest');
  const eq = $('#f-eq', root);
  const series = Object.entries(st.books).filter(([, x]) => x.curve.ts.length > 1).map(([b, x]) => ({ name: `${b.toUpperCase()} ${x.name}`, ts: x.curve.ts, equity: x.curve.equity, color: BOOK_COLOR[b] }));
  if (eq && series.length) equityLines(eq, series, [{ ts: st.cuts.oos, label: 'OOS' }, { ts: st.cuts.t1, label: 'LIVE' }]);
}

export function renderForest() { render(); }

export function initForest() {
  store.on('forest', () => render());
  store.on('forestError', () => render());
  let prev = '';
  store.on('beat', () => {   // zmiana stanu Maca zmienia wskaźnik; pełnego widoku nie przerysowujemy co 30 s
    const w = forestStatus(store.state.forest, heartbeatState(store.state.beat)).word;
    if (w !== prev) { prev = w; render(); }
  });
}
