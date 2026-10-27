// Zakładka Stats: baza świec, latencja, mapa pokrycia danych, dziennik dzień po dniu, flagi jakości.
// meta/status i runner/heartbeat nagłówek i tak nasłuchuje; mapa pokrycia z gałęzi data — 0 dodatkowych odczytów Firestore (Z2, Z4).
import { biggestHoles, cellView, EMPTY, FAILED, INCOMPLETE, FULL, fmtRange, gapsInMonth, layoutBands, mergeLive, NONE, PARTIAL, STATUS_LABEL, summarize } from './coverage.js';
import { getJSON, refreshData } from './data.js';
import { healthView, problemWord, sortChecks } from './health.js';
import { PAIRS } from './metrics.js';
import { dailyRows, recentCells } from './session.js';
import { heartbeatState } from './status.js';
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
      healthTile(hv)));
}

/** Kafelek przeglądu: każdy problem z nazwy i jednym zdaniem, a gdy jest dobrze — ile kontroli i kiedy. */
function healthTile(hv) {
  if (!hv.at && !hv.problems) return 'jeszcze nie było';
  const MARK = { warn: '!', bad: '✕' };
  const probs = sortChecks(hv.checks).filter((c) => c.state !== 'ok');
  const list = probs.map((c) => `<span class="ht-row"><i class="hk-mark ${c.state}">${MARK[c.state]}</i><b>${esc(c.name)}</b> ${esc(c.text)}</span>`).join('');
  const when = hv.at ? `${hv.checks.length} kontroli · ${local(hv.at)} · <a href="#/stats" onclick="document.querySelector('.panel.health')?.scrollIntoView({behavior:'smooth'});return false">szczegóły</a>` : '';
  return probs.length ? `<span class="ht">${list}</span>${when}` : `wszystkie kontrole przeszły · ${when}`;
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
      <thead><tr><th>Para</th><th>Ostatnia świeca (UTC)</th><th>Czas lokalny</th><th class="r">Latencja s</th><th class="r">Świece</th></tr></thead>
      <tbody>${Object.keys(PAIRS).map((p) => {
        const x = pairs[p] || {};
        return `<tr><td class="txt">${PAIRS[p].label}</td><td>${x.lastTs ? dateUTC(x.lastTs, true) : '—'}</td><td>${x.lastTs ? local(x.lastTs) : '—'}</td>
          <td class="r">${x.latencySec ?? '—'}</td><td class="r">${num(x.count || 0, 0)}</td></tr>`;
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



// ---------- mapa pokrycia (D-022) ----------

let cov; // undefined = jeszcze nie wczytano, null = Mac jeszcze nie opublikował
let covErr = null, covSrc = 'dukascopy', sel = null, covLoading = false;
const ROW = 18, CELL = 12, AXIS = 18;
const KIND_LABEL = { p: 'dziura', w: 'rynek nieczynny', q: 'bez ruchu ceny' };
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
  if (r[0] === INCOMPLETE) parts.push(`pobrano ${num(100 * (r[1] || 0) / Math.max(1, (r[1] || 0) + (r[6] || 0)), 0)}% godzin sesji, brakuje ${num(r[6] || 0, 0)} h`);
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
        const v = cellView(row), w = cw - inner, hh = CELL - 1, fh = Math.max(v.fill ? 1 : 0, Math.round(hh * v.fill));
        const tip = `<title>${esc(cellTitle(p, data.keys[i], row))}</title>`;
        svg += `<rect x="${xs[i] + 0.5}" y="${y + 0.5}" width="${w}" height="${hh}" class="c-bg o-${v.outline || 'in'}${on ? ' sel' : ''}" data-p="${p}" data-i="${i}">${tip}</rect>`;
        if (fh) svg += `<rect x="${xs[i] + 0.5}" y="${y + 0.5 + hh - fh}" width="${w}" height="${fh}" class="f-${v.color}" data-p="${p}" data-i="${i}">${tip}</rect>`;
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
    else if (row[0] === INCOMPLETE) note = `Pobrany częściowo: brakuje ${hours(row[6] || 0)} sesji w dniach, których nie udało się pobrać. Pobrane dni są już zapisane i używane; resztę dociągnie ia5 start.`;
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
  if (covSrc === 'yahoo') { renderYahooAudit(panel, head); return; }
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
    all.left || all.incomplete ? `brakuje ${all.left ? `${num(all.left, 0)} mies.` : ''}${all.left && all.incomplete ? ' + ' : ''}${all.incomplete ? `dni w ${num(all.incomplete, 0)} mies.` : ''} (${hours(all.leftHours)} sesji)` : 'niczego nie brakuje',
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
    ...[['f-ok', 'bez dziur'], ['f-h1', 'dziury 1–5 h'], ['f-h2', '6–47 h'], ['f-h3', '≥ 48 h'], ...(data.live ? [['f-fresh', 'pobrany, luki po synchronizacji']] : []),
      ['o-incomplete', 'pobrany częściowo (wysokość = ile)'], ['o-partial', 'bieżący miesiąc'], ['o-none', 'nie pobrany'], ['o-failed', 'błąd'],
      ['o-empty', 'Dukascopy nie ma']]
      .map(([k, l]) => h('span', {}, h('i', { class: `sw ${k}` }), l)));
  panel.replaceChildren(head, h('p', { class: 'covsum', html: line }), live,
    h('div', { class: 'covmap' }, labels, scroll, sums), legend,
    h('div', { class: 'covdetail' }, ...covDetail(data)),
    h('p', { class: 'hint' }, 'Liczone na Macu z surowych danych wobec kalendarza sesji (weekendy i święta 25.12, 1.01 nie są oczekiwane). ',
      'Wysokość kafelka = ile miesiąca pobrano, kolor = jak duże dziury. Dziura = brakuje godziny, w której rynek działał (inne pary mają notowania) i cena się ruszała. ',
      'Nie są dziurami: rynek nieczynny (brakuje jej co najmniej połowie par) i luka bez ruchu ceny (≤ 3 h, cena po niej taka sama jak przed). ',
      data.meta.thin ? `Cienka godzina = świeca z mniej niż ${cov?.thin_minutes ?? 30} minut z notowaniami. ` : '', gen));
  const lay = layoutBands(data.keys, scroll.clientWidth);
  labels.replaceChildren(...lay.bands.flatMap((_, bi) => labelBlock(bi)));
  drawMap(scroll, data, lay);
  if (keepScroll) scroll.scrollLeft = keepScroll;
}

// ---------- audyt Yahoo świeca po świecy (D-027) ----------

const AUDIT_LABEL = { ok: 'jest', late: 'spóźniona (> 20 min po zamknięciu)', flag: 'z flagą jakości (korekta Yahoo albo zła świeca)',
  missing: 'brak', pending: 'w drodze (zamknięta < 20 min temu)', closed: 'rynek zamknięty (weekend, święto)',
  allgap: 'brak we wszystkich parach — rynek nieczynny albo przerwa Yahoo' };
const WDAY = ['nd', 'pn', 'wt', 'śr', 'cz', 'pt', 'sb'];
let auditSel = null;

function renderYahooAudit(panel, head) {
  const now = Date.now() / 1000;
  const cells = recentCells(store.state.status?.recent, now);
  if (!cells) {
    panel.replaceChildren(head, h('p', { class: 'hint' },
      'Audyt świeca po świecy pojawi się po wklejeniu nowego apps_script/Code.gs do Apps Script (najbliższy tick sam go zasieje z bazy).'));
    return;
  }
  const pairs = Object.keys(PAIRS).filter((p) => cells.pairs[p]);
  const count = (p, k) => cells.pairs[p].filter((x) => x === k).length;
  const tot = (k) => pairs.reduce((n, p) => n + count(p, k), 0);
  const present = tot('ok') + tot('late') + tot('flag');
  const line = [`ostatnie 3 tygodnie: ${num(present, 0)} świec`,
    tot('missing') ? `<span class="neg">brak ${num(tot('missing'), 0)}</span>` : 'bez braków',
    tot('late') ? `<span class="warn">spóźnione ${num(tot('late'), 0)}</span>` : 'bez spóźnień',
    tot('flag') ? `<span class="warn">z flagą ${num(tot('flag'), 0)}</span>` : '',
    tot('pending') ? `w drodze ${num(tot('pending'), 0)}` : ''].filter(Boolean).join(' · ');

  const scroll = h('div', { class: 'covscroll', onclick: (e) => {
    const t = e.target.closest('rect');
    if (!t) return;
    const s2 = { pair: t.dataset.p, i: +t.dataset.i };
    auditSel = auditSel && auditSel.pair === s2.pair && auditSel.i === s2.i ? null : s2;
    renderCoverage();
  } });
  const labels = h('div', { class: 'covlabels' });
  const sums = h('div', { class: 'covsums' }, h('div', { class: 'hint', style: { height: `${AXIS}px` } }, 'brak · spóźn.'),
    ...pairs.map((p) => h('div', { class: 'mono', style: { height: `${ROW}px` } },
      h('span', { class: count(p, 'missing') ? 'neg' : 'dimmed' }, String(count(p, 'missing'))), h('span', { class: 'dimmed' }, '\u00a0·\u00a0'),
      h('span', { class: count(p, 'late') ? 'warn' : 'dimmed' }, String(count(p, 'late'))))));
  const legend = h('div', { class: 'covlegend' }, ...[['a-ok', 'jest'], ['a-late', 'spóźniona'], ['a-flag', 'z flagą'], ['a-missing', 'brak'],
    ['a-pending', 'w drodze'], ['a-allgap', 'brak we wszystkich parach'], ['a-closed', 'rynek zamknięty']].map(([k, l]) => h('span', {}, h('i', { class: `sw ${k}` }), l)));

  // lista: wybrana świeca albo ostatnie problemy (braki, spóźnienia, flagi), od najnowszych
  const fmt = (ts) => { const d = new Date(ts * 1000); return `${WDAY[d.getUTCDay()]} ${dateUTC(ts, true).slice(8, 10)}.${dateUTC(ts).slice(5, 7)} ${dateUTC(ts, true).slice(11)} UTC`; };
  let detail;
  if (auditSel) {
    const st = cells.pairs[auditSel.pair][auditSel.i], ts = cells.hours[auditSel.i];
    detail = [h('div', { class: 'phead' }, h('h3', {}, `${PAIRS[auditSel.pair].label} · świeca ${dateUTC(ts, true)}–${dateUTC(ts + 3600, true).slice(11)} UTC`),
      h('span', { class: 'hint' }, AUDIT_LABEL[st]))];
  } else {
    const probs = [];
    for (const p of pairs) cells.pairs[p].forEach((st, i) => { if (st === 'missing' || st === 'late' || st === 'flag') probs.push({ p, st, ts: cells.hours[i] }); });
    probs.sort((a, b) => b.ts - a.ts);
    detail = [h('div', { class: 'phead' }, h('h3', {}, 'Ostatnie problemy'), h('span', { class: 'hint' }, 'kliknij świecę, żeby zobaczyć jej stan')),
      probs.length ? h('ul', { class: 'gaplist audit' }, ...probs.slice(0, 40).map((x) => h('li', { class: x.st },
        h('span', { class: 'mono', title: `u Ciebie ${local(x.ts)}` }, fmt(x.ts)), h('b', {}, PAIRS[x.p].label), h('span', { class: x.st === 'missing' ? 'neg' : 'warn' }, AUDIT_LABEL[x.st]))))
        : h('p', { class: 'hint' }, 'Każda oczekiwana świeca z ostatnich 3 tygodni dotarła na czas.')];
  }
  panel.replaceChildren(head, h('p', { class: 'covsum', html: line }), h('div', { class: 'covmap' }, labels, scroll, sums), legend,
    h('div', { class: 'covdetail' }, ...detail),
    h('p', { class: 'hint' }, '1 kafelek = 1 świeca H1, na bieżąco z Apps Script (co 5 min). Brak = świeca w godzinach rynku nie dotarła 20 min po zamknięciu. ',
      'Yahoo dociąga ostatnie 5 dni przy każdym pobraniu, więc krótkie braki zwykle uzupełniają się same.'));

  // pasy tygodniowe; przerwa przed każdą północą UTC
  const n = cells.hours.length, W = Math.max(scroll.clientWidth, 240);
  // tydzień na pas, na wąskim ekranie mniej dni (kafelek min. 4 px, bez przewijania)
  const perBand = Math.max(24, Math.min(168, Math.floor((W - 12) / (5 * 24 + 3)) * 24));
  const bands = [];
  for (let a = 0; a < n; a += perBand) bands.push([a, Math.min(n, a + perBand)]);
  const cw = Math.max(3, Math.min(12, Math.floor((W - (perBand / 24) * 3) / perBand)));
  const inner = cw >= 6 ? 2 : 1, bandH = AXIS + pairs.length * ROW;
  let svg = '', width = 0;
  bands.forEach(([from, to], bi) => {
    const top = bi * (bandH + BAND_GAP);
    let x = 0;
    for (let i = from; i < to; i++) {
      const ts = cells.hours[i];
      if (i > from && ts % 86400 === 0) x += 3;
      if (ts % 86400 === 0 || i === from) {
        const d = new Date(ts * 1000);
        svg += `<text class="covyear" x="${x}" y="${top + 11}">${WDAY[d.getUTCDay()]} ${d.getUTCDate()}.${String(d.getUTCMonth() + 1).padStart(2, '0')}</text>`;
      }
      pairs.forEach((p, r) => {
        const st = cells.pairs[p][i];
        const y = top + AXIS + r * ROW + (ROW - CELL) / 2;
        const on = auditSel && auditSel.pair === p && auditSel.i === i;
        svg += `<rect x="${x + 0.5}" y="${y + 0.5}" width="${cw - inner}" height="${CELL - 1}" class="a-${st}${on ? ' sel' : ''}" data-p="${p}" data-i="${i}"><title>${PAIRS[p].label} · ${dateUTC(ts, true)} UTC · ${AUDIT_LABEL[st]}</title></rect>`;
      });
      x += cw;
    }
    width = Math.max(width, x);
  });
  const height = bands.length * (bandH + BAND_GAP) - BAND_GAP;
  scroll.innerHTML = `<svg class="covsvg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-label="Audyt świec Yahoo">${svg}</svg>`;
  labels.replaceChildren(...bands.flatMap((_, bi) => [h('div', { style: { height: `${AXIS + (bi ? BAND_GAP : 0)}px` } }),
    ...pairs.map((p) => h('div', { class: 'covpair', style: { height: `${ROW}px` } }, PAIRS[p].label))]));
}

export function renderStats() {
  const root = $('#view-stats');
  const s = store.state.status;
  if (!s) {
    root.replaceChildren(h('div', { class: 'empty' }, store.state.statusError ? `Firestore: ${store.state.statusError}` : 'Wczytywanie stanu…'));
    return;
  }
  root.replaceChildren(h('div', { class: 'toolbar' }, h('h2', {}, 'Stats')), healthPanel(s), summary(s),
    h('section', { id: 'covpanel', class: 'panel' }), dailyLog(s), pairsTable(s));
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
  // audyt Yahoo: co minutę świeca „w drodze” może stać się „brak”
  setInterval(() => { if (onStats() && covSrc === 'yahoo') renderCoverage(); }, 60000);
  let t;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => { if (onStats()) renderCoverage(); }, 150); });
}
