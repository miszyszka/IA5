// Zakładka Stats: baza świec, latencja, mapa pokrycia danych, dziennik dzień po dniu, flagi jakości.
// meta/status i runner/heartbeat nagłówek i tak nasłuchuje; mapa pokrycia z gałęzi data — 0 dodatkowych odczytów Firestore (Z2, Z4).
import { biggestHoles, cellKind, EMPTY, FAILED, FULL, fmtRange, gapsInMonth, layoutBands, mergeLive, NONE, PARTIAL, STATUS_LABEL, summarize } from './coverage.js';
import { getJSON, refreshData } from './data.js';
import { healthView, problemWord, sortChecks } from './health.js';
import { PAIRS } from './metrics.js';
import { dailyRows, FLAG_LABEL, parseFlag } from './session.js';
import { flagCount, heartbeatState } from './status.js';
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
  const run = s.lastRun || {};
  const hv = healthView(s.health, Date.now() / 1000, heartbeatState(store.state.beat).online);
  const item = (label, value, sub = '') => h('div', { class: 'stat' }, h('small', {}, label), h('b', { html: value }), h('span', { class: 'hint', html: sub }));
  return h('section', { class: 'panel stats-sum' },
    item('Świece w bazie', num(s.totalBars || 0, 0), `Yahoo H1 w Firestore${run.finishedAt ? `<br>ostatnie pobranie ${local(run.finishedAt)}` : ''}${run.ok === false ? `<br><span class="neg">błąd: ${esc(run.error)}</span>` : ''}`),
    item('Latencja ostatniej świecy', last == null ? '—' : `${num(last, 0)} s`, `${med == null ? '' : `mediana 24 h ${num(med, 0)} s`}${spark(lat)}`),
    item('Przegląd zdrowia', hv.problems ? `<span class="state-${hv.state}">${hv.problems} ${problemWord(hv.problems)}</span>` : '<span class="state-ok">OK</span>',
      hv.at ? `${hv.checks.length} kontroli · ${local(hv.at)}` : 'jeszcze nie było'),
    item('Flagi jakości', String(flagCount(s)), 'kontrola D5 — lista niżej'));
}

function headline(hv) {
  if (!hv.at) return hv.summary;
  if (!hv.problems) return 'Wszystko w porządku — każda kontrola przeszła.';
  const n = (st) => hv.checks.filter((c) => c.state === st).length;
  const parts = [n('bad') && `${n('bad')} ${n('bad') === 1 ? 'błąd' : n('bad') < 5 ? 'błędy' : 'błędów'}`,
    n('warn') && `${n('warn')} ${n('warn') === 1 ? 'uwaga' : n('warn') < 5 ? 'uwagi' : 'uwag'}`].filter(Boolean);
  return `${hv.problems} ${problemWord(hv.problems)}: ${parts.join(', ')} — ${hv.checks.find((c) => c.state === hv.state).name.toLowerCase()} i inne poniżej.`;
}

function healthPanel(s) {
  const hv = healthView(s.health, Date.now() / 1000, heartbeatState(store.state.beat).online);
  const MARK = { ok: '✓', warn: '!', bad: '✕' };
  const rows = sortChecks(hv.checks).map((c) => {
    const more = (c.detail || []).length || c.fix;
    const head = [h('i', { class: `hk-mark ${c.state}`, 'aria-label': c.state }, MARK[c.state]), h('b', {}, c.name), h('span', {}, c.text)];
    return more
      ? h('li', { class: `hk ${c.state}` }, h('details', { open: c.state === 'bad' },
        h('summary', {}, ...head),
        (c.detail || []).length ? h('ul', { class: 'hk-detail' }, ...c.detail.map((d) => h('li', {}, d))) : '',
        c.fix ? h('p', { class: 'hk-fix' }, 'Co zrobić: ', c.fix) : ''))
      : h('li', { class: `hk ${c.state}` }, h('div', { class: 'hk-row' }, ...head));
  });
  return h('section', { class: 'panel health' },
    h('div', { class: 'phead' }, h('h3', {}, 'Stan systemu'),
      h('span', { class: 'hint' }, hv.at ? `przegląd ${local(hv.at)} · co godzinę na Macu · ręcznie: ia5 health` : 'przegląd robi Mac co godzinę')),
    h('p', { class: `hsum state-${hv.state}`, title: hv.summary }, headline(hv)),
    hv.facts.length ? h('ul', { class: 'hfacts' }, ...hv.facts.map((f) => h('li', {}, f))) : '',
    h('ul', { class: 'hklist' }, ...rows));
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


// ---------- mapa pokrycia (D-022) ----------

let cov; // undefined = jeszcze nie wczytano, null = Mac jeszcze nie opublikował
let covErr = null, covSrc = 'dukascopy', sel = null, covLoading = false;
const ROW = 18, CELL = 12, AXIS = 18;
const KIND_LABEL = { p: 'tylko ta para', w: 'wspólna' };
const MONTHS = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru'];
const monthName = (key) => `${MONTHS[+key.slice(5, 7) - 1]} ${key.slice(0, 4)}`;
const hours = (n) => `${num(n, 0)} h`;

async function loadCoverage() {
  if (covLoading) return;
  covLoading = true;
  try { cov = await getJSON('coverage/coverage.json'); covErr = null; } catch (e) { covErr = e.message || String(e); cov = cov ?? null; }
  covLoading = false;
  renderCoverage();
}

/** Źródło do narysowania: opublikowana mapa + statusy na żywo, gdy Mac właśnie pobiera Dukascopy. */
function currentSource() {
  const pairs = Object.keys(PAIRS);
  const src = cov?.sources?.[covSrc];
  const beat = store.state.beat;
  const syncing = covSrc === 'dukascopy' && heartbeatState(beat).online && beat?.state === 'syncing' && beat?.sync?.pairs;
  const merged = mergeLive(src, syncing ? beat.sync : null, pairs);
  return merged && { ...merged, meta: src || {} };
}

function cellTitle(pair, key, r) {
  const parts = [`${PAIRS[pair].label} · ${monthName(key)}`, STATUS_LABEL[r[0]]];
  if (r[3] != null && r[0] !== EMPTY) {
    parts.push(`${num(r[2], 0)} z ${num(r[1], 0)} h`);
    if (r[3]) parts.push(`dziury ${hours(r[3])}`);
    if (r[4]) parts.push(`wspólne luki ${hours(r[4])}`);
    if (r[5]) parts.push(`cienkie ${num(r[5], 0)}`);
  } else if (r[0] === FULL || r[0] === PARTIAL) parts.push('luki policzone po synchronizacji');
  return parts.join(' · ');
}

const BAND_GAP = 14;

function drawMap(box, data, lay) {
  const pairs = Object.keys(PAIRS);
  const { cw } = lay;
  const yg = cw >= 6 ? 3 : 2, inner = cw >= 6 ? 2 : 1;
  const bandH = AXIS + pairs.length * ROW;
  let width = 0, svg = '';
  lay.bands.forEach(([from, to], bi) => {
    const top = bi * (bandH + BAND_GAP);
    let x = 0, lastLabel = -99;
    const xs = {};
    for (let i = from; i < to; i++) {
      const k = data.keys[i];
      if (i > from && k.endsWith('-01')) x += yg;
      xs[i] = x;
      if ((i === from || k.endsWith('-01')) && x - lastLabel >= 34) { svg += `<text class="covyear" x="${x}" y="${top + 11}">${k.slice(0, 4)}</text>`; lastLabel = x; }
      x += cw;
    }
    width = Math.max(width, x);
    pairs.forEach((p, r) => {
      const y = top + AXIS + r * ROW + (ROW - CELL) / 2;
      for (let i = from; i < to; i++) {
        const row = data.pairs[p].m[i];
        const on = sel && sel.pair === p && sel.i === i;
        svg += `<rect x="${xs[i] + 0.5}" y="${y + 0.5}" width="${cw - inner}" height="${CELL - 1}" class="c-${cellKind(row)}${on ? ' sel' : ''}" data-p="${p}" data-i="${i}"><title>${esc(cellTitle(p, data.keys[i], row))}</title></rect>`;
      }
    });
  });
  const height = lay.bands.length * (bandH + BAND_GAP) - BAND_GAP;
  box.innerHTML = `<svg class="covsvg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Mapa pokrycia: pary × miesiące">${svg}</svg>`;
}

function gapRow(g, pair, other) {
  const [a, b, n, kind, conf] = g;
  const confText = conf < 0 ? `${other}: poza zakresem` : `${other} ma ${conf} z ${n} h`;
  return h('li', { class: `gap ${kind}` },
    h('span', { class: 'mono' }, fmtRange(a, b)),
    pair ? h('b', {}, PAIRS[pair]?.label || pair) : '',
    h('span', { class: 'mono r' }, hours(n)),
    h('span', {}, KIND_LABEL[kind]),
    h('span', { class: conf > 0 && kind === 'p' ? 'warn' : 'dimmed' }, confText));
}

function covDetail(data) {
  const other = data.meta.other || 'drugie źródło';
  const title = (t, sub) => h('div', { class: 'phead' }, h('h3', {}, t), sub ? h('span', { class: 'hint' }, sub) : '');
  if (sel && sel.i != null) {
    const key = data.keys[sel.i], row = data.pairs[sel.pair].m[sel.i];
    const gaps = gapsInMonth(data.pairs[sel.pair].gaps, key);
    let note;
    if (row[0] === NONE) note = 'Jeszcze nie pobrany — ia5 start na Macu dociągnie go przy najbliższym uruchomieniu.';
    else if (row[0] === FAILED) note = 'Pobieranie nie powiodło się (sieć albo serwer Dukascopy). Ponowi się przy następnym ia5 start.';
    else if (row[0] === EMPTY) note = 'Dukascopy nie ma notowań tej pary w tym miesiącu — to nie jest luka do uzupełnienia.';
    else if (row[3] == null) note = 'Pobrany przed chwilą — luki policzy Mac po zakończeniu synchronizacji.';
    else if (!gaps.length) note = 'Wszystkie godziny sesji są na miejscu.';
    const facts = row[3] != null && row[0] !== EMPTY
      ? `${STATUS_LABEL[row[0]]} · ${num(row[2], 0)} z ${num(row[1], 0)} godzin sesji · dziury ${hours(row[3])} · wspólne ${hours(row[4])}${data.meta.thin ? ` · cienkie ${num(row[5], 0)}` : ''}`
      : STATUS_LABEL[row[0]];
    return [title(`${PAIRS[sel.pair].label} · ${monthName(key)}`, facts),
      note ? h('p', { class: 'hint' }, note) : '',
      gaps.length ? h('ul', { class: 'gaplist' }, ...gaps.map((g) => gapRow(g, null, other))) : ''];
  }
  if (sel) {
    const gaps = data.pairs[sel.pair].gaps;
    const holes = gaps.filter((g) => g[3] === 'p').sort((x, y) => y[0] - x[0]);
    const common = gaps.filter((g) => g[3] === 'w');
    const s = summarize(data.pairs[sel.pair].m);
    return [title(`${PAIRS[sel.pair].label} · wszystkie dziury`, `${holes.length} dziur, ${hours(s.holes)} · wspólne luki: ${common.length}, ${hours(s.common)}`),
      holes.length ? h('ul', { class: 'gaplist' }, ...holes.slice(0, 200).map((g) => gapRow(g, null, other)))
        : h('p', { class: 'hint' }, 'Ta para nie ma dziur w pobranych miesiącach.')];
  }
  const top = biggestHoles(data.pairs);
  return [title('Największe dziury', 'tylko jednej pary — kliknij miesiąc albo parę, żeby zobaczyć szczegóły'),
    top.length ? h('ul', { class: 'gaplist' }, ...top.map(({ pair, g }) => gapRow(g, pair, other)))
      : h('p', { class: 'hint' }, 'Brak dziur w pobranych miesiącach.')];
}

function renderCoverage() {
  const panel = $('#covpanel');
  if (!panel) return;
  const keepScroll = $('.covscroll', panel)?.scrollLeft;
  const seg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Źródło danych' },
    ...[['dukascopy', 'Dukascopy · backtesty'], ['yahoo', 'Yahoo · monitoring']].map(([v, l]) =>
      h('button', { class: covSrc === v ? 'on' : '', 'aria-pressed': covSrc === v, onclick: () => { covSrc = v; sel = null; renderCoverage(); } }, l)));
  const head = h('div', { class: 'phead' }, h('h3', {}, 'Mapa pokrycia danych'), seg);
  const data = currentSource();
  if (!data) {
    const msg = cov === undefined && !covErr ? 'Wczytywanie mapy…'
      : covErr ? `Nie udało się wczytać mapy z GitHub: ${covErr}`
        : 'Mapy jeszcze nie ma. Policzy ją i opublikuje Mac przy najbliższym ia5 start (po git pull). W trakcie pierwszego pobierania wypełnia się na żywo.';
    panel.replaceChildren(head, h('p', { class: 'hint' }, msg));
    return;
  }
  const pairs = Object.keys(PAIRS);
  const per = Object.fromEntries(pairs.map((p) => [p, summarize(data.pairs[p].m)]));
  const all = summarize(pairs.flatMap((p) => data.pairs[p].m));
  const line = [
    `${covSrc === 'yahoo' ? 'w bazie' : 'pobrane'} ${num(all.done, 0)} z ${num(all.months, 0)} miesięcy`,
    all.left ? `brakuje ${num(all.left, 0)} mies. (${hours(all.leftHours)} sesji)` : 'niczego nie brakuje',
    all.failed ? `<span class="neg">błędy ${num(all.failed, 0)}</span>` : '',
    `dziury ${hours(all.holes)} w ${num(all.holeMonths, 0)} mies.`,
    `wspólne luki ${hours(all.common)}`,
    data.meta.thin ? `cienkie godziny ${num(all.thin, 0)}` : '',
  ].filter(Boolean).join(' · ');
  const live = data.live ? h('p', { class: 'covlive' }, h('i', { class: 'dot ok' }), 'Mac pobiera teraz — mapa wypełnia się na żywo',
    all.uncounted ? h('span', { class: 'dimmed' }, ` · ${num(all.uncounted, 0)} świeżo pobranych miesięcy czeka na policzenie luk`) : '') : '';
  const gen = cov?.generated ? h('span', { class: 'hint' }, `policzone ${local(cov.generated)}`) : '';

  const labels = h('div', { class: 'covlabels' });
  const labelBlock = (bi) => [h('div', { style: { height: `${AXIS + (bi ? BAND_GAP : 0)}px` } }),
    ...pairs.map((p) => h('button', { class: `covpair ${sel?.pair === p && sel.i == null ? 'on' : ''}`, style: { height: `${ROW}px` },
      title: `Wszystkie dziury ${PAIRS[p].label}`, onclick: () => { sel = sel?.pair === p && sel.i == null ? null : { pair: p }; renderCoverage(); } }, PAIRS[p].label))];
  const sums = h('div', { class: 'covsums' }, h('div', { class: 'hint', style: { height: `${AXIS}px` } }, 'pokrycie · dziury'),
    ...pairs.map((p) => h('div', { class: 'mono', style: { height: `${ROW}px` }, title: per[p].left ? `brakuje ${per[p].left} miesięcy` : '' },
      per[p].pct == null ? '—' : `${num(per[p].pct * 100, per[p].pct > 0.999 && per[p].pct < 1 ? 2 : 1)}%`,
      h('span', { class: 'dimmed' }, '\u00a0·\u00a0'), h('span', { class: per[p].holes ? 'warn' : 'dimmed' }, hours(per[p].holes)))));
  const scroll = h('div', { class: 'covscroll', onclick: (e) => {
    const t = e.target.closest('rect');
    if (!t) return;
    const s2 = { pair: t.dataset.p, i: +t.dataset.i };
    sel = sel && sel.pair === s2.pair && sel.i === s2.i ? null : s2;
    renderCoverage();
  } });
  const legend = h('div', { class: 'covlegend' },
    ...[['full', 'pełny'], ...(data.live ? [['fresh', 'pobrany przed chwilą']] : []), ['holes1', 'dziury 1–5 h'], ['holes2', '6–47 h'], ['holes3', '≥ 48 h'], ['partial', 'w toku'],
      ['none', 'nie pobrany'], ['failed', 'błąd'], ...(covSrc === 'dukascopy' ? [['empty', 'Dukascopy nie ma']] : [])]
      .map(([k, l]) => h('span', {}, h('i', { class: `sw c-${k}` }), l)));
  panel.replaceChildren(head, h('p', { class: 'covsum', html: line }), live,
    h('div', { class: 'covmap' }, labels, scroll, sums), legend,
    h('div', { class: 'covdetail' }, ...covDetail(data)),
    h('p', { class: 'hint' }, 'Liczone na Macu z surowych danych wobec kalendarza sesji. Dziura = brakuje godziny tylko tej parze. ',
      'Wspólna luka = brakuje jej co najmniej połowie par (święto, krótka sesja albo przerwa źródła). ',
      data.meta.thin ? `Cienka godzina = świeca z mniej niż ${cov?.thin_minutes ?? 30} minut z notowaniami. ` : '', gen));
  const lay = layoutBands(data.keys, scroll.clientWidth);
  labels.replaceChildren(...lay.bands.flatMap((_, bi) => labelBlock(bi)));
  drawMap(scroll, data, lay);
  if (keepScroll) scroll.scrollLeft = keepScroll;
}

export function renderStats() {
  const root = $('#view-stats');
  const s = store.state.status;
  if (!s) {
    root.replaceChildren(h('div', { class: 'empty' }, store.state.statusError ? `Firestore: ${store.state.statusError}` : 'Wczytywanie stanu…'));
    return;
  }
  root.replaceChildren(h('div', { class: 'toolbar' }, h('h2', {}, 'Stats')), healthPanel(s), summary(s),
    h('section', { id: 'covpanel', class: 'panel' }), dailyLog(s), h('div', { class: 'grid2' }, pairsTable(s), flagsList(s)));
  renderCoverage();
  if (cov === undefined) loadCoverage();
}

export function initStats() {
  const onStats = () => store.state.route?.view === 'stats';
  for (const k of ['status', 'statusError']) store.on(k, () => { if (onStats()) renderStats(); });
  // heartbeat: statusy na żywo w trakcie pobierania; po końcu synchronizacji Mac publikuje nową mapę
  let prev = null;
  store.on('beat', (b) => {
    if (prev === 'syncing' && b?.state !== 'syncing') { refreshData(); cov = undefined; if (onStats()) loadCoverage(); }
    prev = b?.state;
    if (onStats() && (b?.sync || b?.state === 'syncing')) renderCoverage();
  });
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => { if (onStats()) renderCoverage(); }, 150); });
}
