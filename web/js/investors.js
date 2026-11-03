// Zakładka Inwestorzy (E6, D-045): wirtualni inwestorzy — paper trading na żywych świecach Yahoo.
// Lista i dodawanie/usuwanie: Firestore `investors` (tylko właściciel). Stan, kapitał i transakcje liczy Mac co godzinę
// i publikuje na gałęzi data (investors/index.json, investors/{id}/state.json) — Z2: bez cen z Firestore.
import { disposeAll, equityChart } from './charts.js';
import { getJSON, getText } from './data.js';
import { createInvestor, deleteInvestor } from './fb.js';
import { drawdown, investorStatus, investorTrades, mergeInvestors, mergeStrategies, PAIRS, SIZING, toCSV, validateInvestor, variantChoices } from './metrics.js';
import { heartbeatState } from './status.js';
import { $, ago, cls, confirmDialog, download, h, local, num, signed, store, toast } from './util.js';

const STATE_CACHE = new Map();   // id → { key, data } (klucz = computedAt z indeksu, nowy stan → nowy odczyt)

export async function loadInvestors() {
  try {
    const idx = await getJSON('investors/index.json');
    store.set('invIndexError', null);
    store.set('invIndex', idx?.investors || []);
  } catch (e) {
    store.set('invIndexError', e.message || String(e));
    store.set('invIndex', []);
  }
}

function items() {
  const { invDocs, invIndex, invHidden } = store.state;
  const hidden = invHidden || new Set();
  if (invDocs) return mergeInvestors(invDocs, invIndex).filter((x) => !hidden.has(x.id));
  // bez logowania: tylko to, co Mac opublikował na gałęzi data (O3 — wyniki są publiczne)
  return (invIndex || []).filter((e) => !hidden.has(e.id)).map((e) => ({ id: e.id, doc: null, st: e }));
}

function pill(s) {
  return h('span', { class: 'ipill', 'data-state': s.state, title: s.detail }, h('i', { class: 'dot flat' }), h('b', {}, s.word));
}

const fmtUSD = (x) => (x == null ? '—' : `${num(x, 2)} USD`);
const dirWord = (d) => (d > 0 ? 'long' : 'short');

// ---------- lista ----------

function row(x, mac) {
  const st = x.st, d = x.doc;
  const s = investorStatus(d, st, mac);
  const name = d?.name || st?.name || x.id;
  const ret = st?.return_pct;
  const strategies = d?.strategies?.map((y) => y.name) || st?.strategies || [];
  const open = () => { location.hash = `#/inwestorzy/${encodeURIComponent(x.id)}`; };
  return h('article', { class: 'srow clickable', tabindex: 0, onclick: open, onkeydown: (e) => { if (e.key === 'Enter') open(); } },
    h('div', { class: 'srow-main' },
      h('div', { class: 'row' }, pill(s), h('h3', {}, name)),
      h('p', { class: 'hyp' }, strategies.length ? strategies.join(' · ') : '—')),
    h('dl', { class: 'srow-kpi' },
      h('div', {}, h('dt', {}, 'kapitał teraz'), h('dd', { class: 'num' }, st ? fmtUSD(st.equity) : '—')),
      h('div', {}, h('dt', {}, 'wynik'), h('dd', { class: `num ${cls(ret)}` }, ret == null ? '—' : `${signed(ret, 2)}%`)),
      h('div', {}, h('dt', {}, 'start'), h('dd', {}, local(d?.createdAt || st?.start))),
      h('div', {}, h('dt', {}, 'kapitał początkowy'), h('dd', { class: 'num' }, fmtUSD(d?.capital ?? st?.capital))),
      h('div', {}, h('dt', {}, 'depozyt na wejście'), h('dd', { class: 'num' }, `${num(d?.pct ?? st?.pct, 1)}%`)),
      h('div', {}, h('dt', {}, 'transakcje / otwarte'), h('dd', { class: 'num' }, st ? `${st.closed} / ${st.open}` : '—'))),
    h('div', { class: 'srow-act' },
      d ? h('button', { class: 'btn ghost icon', title: 'Usuń inwestora', 'aria-label': `Usuń ${name}`,
        onclick: (e) => { e.stopPropagation(); removeInvestor(x.id, name); } }, '🗑') : null,
      h('span', { class: 'go', 'aria-hidden': 'true' }, '→')));
}

function banner() {
  const { user, invDocsError } = store.state;
  if (!user) {
    return h('div', { class: 'banner' }, 'Bez logowania widzisz tylko policzonych inwestorów. Żeby dodawać i usuwać — ',
      h('button', { class: 'link', onclick: () => $('#login')?.click() }, 'zaloguj się kontem Google'), '.');
  }
  if (invDocsError?.code === 'permission-denied') {
    return h('div', { class: 'banner warn' }, h('b', {}, 'Firestore nie wpuszcza do inwestorów. '),
      'Wklej nowe reguły z pliku ', h('code', {}, 'firestore.rules'), ' (Firebase → Firestore → Rules → Publish) — mają sekcję ',
      h('code', {}, 'investors'), '.');
  }
  return null;
}

function renderList(root) {
  const list = items();
  const mac = heartbeatState(store.state.beat);
  const { invIndex, invIndexError } = store.state;
  const empty = invIndex == null && !invIndexError ? h('div', { class: 'empty' }, 'Wczytywanie…')
    : !list.length ? h('div', { class: 'empty' },
      h('h3', {}, 'Nie ma jeszcze żadnego inwestora'),
      h('p', {}, 'Inwestor to wirtualne konto (paper trading): od chwili dodania handluje wybranymi strategiami na nowych świecach, '
        + 'z własnym kapitałem i stałym % kapitału na każde wejście.'),
      h('button', { class: 'btn accent', onclick: openInvestorEditor }, '+ Nowy inwestor')) : null;
  root.replaceChildren(
    h('div', { class: 'toolbar' },
      h('h2', {}, 'Inwestorzy ', h('span', { class: 'count' }, list.length)),
      h('button', { class: 'btn accent', onclick: openInvestorEditor }, '+ Nowy inwestor')),
    banner() || '',
    invIndexError ? h('div', { class: 'banner warn' }, `Nie udało się wczytać stanu inwestorów z GitHub: ${invIndexError}`) : '',
    empty || h('div', { class: 'slist' }, ...list.map((x) => row(x, mac))));
}

// ---------- karta inwestora ----------

async function stateOf(id, entry) {
  const key = entry?.computedAt ?? 0;
  const c = STATE_CACHE.get(id);
  if (c && c.key === key) return c.data;
  const data = await getJSON(`investors/${encodeURIComponent(id)}/state.json`);
  STATE_CACHE.set(id, { key, data });
  return data;
}

function kpi(label, val, c = '') {
  return h('div', { class: 'kpi' }, h('small', {}, label), h('b', { class: c }, val));
}

const TRADE_COLS = [
  ['n', '#'], ['entry_ts', 'wejście (czas PL)'], ['strategyName', 'strategia'], ['pair', 'para'], ['dir', 'kierunek'],
  ['entry_px', 'cena wejścia'], ['exit_ts', 'wyjście (czas PL)'], ['exit_px', 'cena wyjścia / wycena'], ['reason', 'powód'],
  ['status', 'status'], ['pips_net', 'pipsy netto'], ['margin_usd', 'depozyt USD'], ['pnl_usd', 'wynik USD'], ['equity_after', 'kapitał po'],
];

function tradeRow(t) {
  const px = (v) => num(v, v > 20 ? 3 : 5);
  const inactive = t.status.startsWith('pominięta') || t.status.startsWith('anulowana');
  return h('tr', { class: inactive ? 'thin' : t.status === 'otwarta' ? 'open' : '' },
    h('td', { class: 'r' }, t.n),
    h('td', {}, local(t.entry_ts)),
    h('td', { class: 'txt' }, t.strategyName),
    h('td', { class: 'txt' }, PAIRS[t.pair]?.label || t.pair),
    h('td', { class: 'txt' }, dirWord(t.dir) + (t.weight && t.weight !== 1 ? ` ×${num(t.weight, 2)}` : '')),
    h('td', { class: 'r' }, px(t.entry_px)),
    h('td', {}, t.exit_ts ? local(t.exit_ts) : '—'),
    h('td', { class: 'r' }, px(t.exit_px)),
    h('td', { class: 'txt' }, t.reason || '—'),
    h('td', { class: `txt ${t.status === 'otwarta' ? 'run' : inactive ? 'warn' : ''}` }, t.status),
    h('td', { class: `r ${cls(t.pips_net)}` }, signed(t.pips_net, 1)),
    h('td', { class: 'r' }, t.margin_usd == null ? '—' : num(t.margin_usd, 2)),
    h('td', { class: `r ${cls(t.pnl_usd)}` }, t.pnl_usd == null ? '—' : signed(t.pnl_usd, 2)),
    h('td', { class: 'r' }, t.equity_after == null ? '—' : num(t.equity_after, 2)));
}

async function renderCard(root, id) {
  const x = items().find((y) => y.id === id) || { id, doc: store.state.invDocs?.[id] || null, st: null };
  const d = x.doc;
  const name = d?.name || x.st?.name || id;
  const back = h('a', { href: '#/inwestorzy', class: 'back' }, '← Inwestorzy');
  root.replaceChildren(back, h('div', { class: 'empty' }, 'Wczytywanie…'));
  let st = null;
  try { st = x.st ? await stateOf(id, x.st) : null; } catch (e) { toast(`Stan inwestora: ${e.message || e}`, 'bad', 7000); }
  if (store.state.route?.view !== 'investors' || store.state.route?.id !== id) return;   // użytkownik przeszedł dalej
  disposeAll();
  const mac = heartbeatState(store.state.beat);
  const s = investorStatus(d, st, mac);
  const strategies = st?.strategies || (d?.strategies || []).map((y) => ({ name: y.name, variantLabel: y.variantLabel }));
  const capital = d?.capital ?? st?.capital;
  const e = st?.equity;
  const c = st?.counts || {};

  const head = h('div', { class: 'ihead panel' },
    h('div', { class: 'row between wrap' },
      h('div', { class: 'row wrap' }, h('h2', {}, name)),
      d ? h('button', { class: 'btn danger small', onclick: () => removeInvestor(id, name, true) }, 'Usuń inwestora') : null),
    h('div', { class: `istatus`, 'data-state': s.state },
      h('i', { class: 'dot flat' }), h('b', {}, s.word), h('span', {}, s.detail),
      st ? h('span', { class: 'muted' }, ` · ostatnie liczenie ${ago(st.computedAt)} · dane do ${local(st.dataTo)}`) : null),
    h('p', { class: 'muted small' },
      `Paper trading od ${local(d?.createdAt || st?.start)} · kapitał początkowy ${fmtUSD(capital)} · depozyt ${num(d?.pct ?? st?.pct, 1)}% kapitału `
      + `na każde wejście (nominał = 30 × depozyt, suma depozytów ≤ 100% kapitału) · ustawienia stałe.`));

  const kpis = h('div', { class: 'kpis small' },
    kpi('kapitał teraz', fmtUSD(e?.now)),
    kpi('wynik', e ? `${signed(e.return_pct, 2)}%` : '—', cls(e?.return_pct)),
    kpi('zrealizowany', fmtUSD(e?.realized)),
    kpi('wycena otwartych', e ? `${signed(e.unrealized, 2)} USD` : '—', cls(e?.unrealized)),
    kpi('maks. obsunięcie', e ? `${num(e.max_dd_pct, 2)}%` : '—'),
    kpi('zajęty depozyt', fmtUSD(e?.margin_used)),
    kpi('zamknięte / otwarte', st ? `${c.closed} / ${c.open}` : '—'),
    kpi('pominięte / anulowane', st ? `${c.skipped_margin} / ${c.cancelled}` : '—'));

  const strat = h('div', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Strategie inwestora')),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
      h('thead', {}, h('tr', {}, ...['strategia', 'wariant', 'wyjście', 'transakcje', 'otwarte', 'wynik USD', ''].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...strategies.map((y) => h('tr', {},
        h('td', { class: 'txt' }, y.strategyId ? h('a', { href: `#/s/${encodeURIComponent(y.strategyId)}` }, y.name) : y.name),
        h('td', { class: 'txt' }, y.variantLabel || '—'),
        h('td', { class: 'txt' }, y.exit || '—'),
        h('td', { class: 'r' }, y.trades ?? '—'),
        h('td', { class: 'r' }, y.open ?? '—'),
        h('td', { class: `r ${cls(y.pnl_usd)}` }, y.pnl_usd == null ? '—' : signed(y.pnl_usd, 2)),
        h('td', { class: 'txt bad' }, y.error || '')))))));

  const pending = (st?.pending || []).map((p) => h('li', {},
    `${strategies[p.strategy]?.name || '#' + (p.strategy + 1)} · ${PAIRS[p.pair]?.label || p.pair} · ${dirWord(p.dir)} — sygnał na świecy ${local(p.signal_ts)}, wejście na open następnej świecy`));

  const chartBox = h('div', { id: 'inv-eq', class: 'chart tall' });
  const eqPanel = h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, 'Kapitał od startu'),
    h('span', { class: 'hint' }, 'punkty = zamknięte transakcje; ostatni punkt = teraz, z wyceną otwartych pozycji')),
  st?.curve?.ts?.length > 1 ? chartBox : h('div', { class: 'empty small' }, st ? 'Wykres pojawi się po pierwszej nowej świecy od startu.' : 'Wykres pojawi się po pierwszym liczeniu na Macu.'));

  const trades = investorTrades(st);
  const csv = () => download(`inwestor-${name}.csv`, toCSV(trades.map((t) => ({ ...t, entry_ts: local(t.entry_ts), exit_ts: t.exit_ts ? local(t.exit_ts) : '' })),
    TRADE_COLS.map(([k]) => k)), 'text/csv');
  const tPanel = h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, `Transakcje (chronologicznie) · ${trades.length}`),
      trades.length ? h('button', { class: 'btn ghost small', onclick: csv }, 'Eksport CSV') : null),
    pending.length ? h('div', { class: 'banner' }, h('b', {}, 'Czeka na wejście: '), h('ul', { class: 'plain' }, ...pending)) : '',
    trades.length ? h('div', { class: 'tablewrap' }, h('table', { class: 'data static itrades' },
      h('thead', {}, h('tr', {}, ...TRADE_COLS.map(([, l]) => h('th', {}, l)))),
      h('tbody', {}, ...trades.map(tradeRow))))
      : h('div', { class: 'empty small' }, st ? 'Jeszcze bez transakcji — pierwsza pojawi się, gdy któraś strategia da sygnał na nowej świecy.' : '—'));

  head.append(kpis);
  root.replaceChildren(back, head, eqPanel, strat, tPanel);
  if (st?.curve?.ts?.length > 1) {
    const marks = [{ ts: st.start, label: 'start' }];
    equityChart(chartBox, st.curve, drawdown(st.curve.equity), marks);
  }
}

export function renderInvestors() {
  const root = $('#view-investors');
  const id = store.state.route?.id;
  if (id) renderCard(root, id);
  else { disposeAll(); renderList(root); }
}

export function initInvestors() {
  for (const k of ['invDocs', 'invIndex', 'invHidden', 'user', 'invDocsError', 'invIndexError']) {
    store.on(k, () => { if (store.state.route?.view === 'investors') renderInvestors(); });
  }
  // stan Maca zmienia wskaźnik „DZIAŁA” — odśwież listę (karty nie przerysowujemy co 30 s)
  store.on('beat', () => { if (store.state.route?.view === 'investors' && !store.state.route?.id) renderInvestors(); });
}

async function removeInvestor(id, name, goBack = false) {
  if (!store.state.user) { toast('Zaloguj się, żeby usuwać inwestorów.', 'warn'); return; }
  const ok = await confirmDialog(`Usunąć inwestora „${name}”?`,
    'Inwestor zniknie z listy od razu, a jego stan i transakcje usunie program ia5 na Macu. Tego nie da się cofnąć.', 'Usuń', true);
  if (!ok) return;
  try {
    await deleteInvestor(id);
    const hid = new Set(store.state.invHidden || []);
    hid.add(id);
    store.set('invHidden', hid);
    toast(`Usunięto inwestora „${name}”.`, 'ok');
    if (goBack) location.hash = '#/inwestorzy';
  } catch (e) {
    toast(e.message || String(e), 'bad', 7000);
  }
}

// ---------- nowy inwestor ----------

const VARIANTS = new Map();
async function variantsOf(sid) {
  if (!VARIANTS.has(sid)) VARIANTS.set(sid, getJSON(`results/${encodeURIComponent(sid)}/variants.json`).catch(() => null));
  return VARIANTS.get(sid);
}

export function openInvestorEditor() {
  if (!store.state.user) { toast('Zaloguj się, żeby dodawać inwestorów.', 'warn'); return; }
  const strategies = mergeStrategies(store.state.index || [], store.state.docs || {}, store.state.hidden || new Set())
    .filter((s) => s.result && !s.result.demo);
  const nameIn = h('input', { type: 'text', placeholder: 'np. Konto RSI — ostrożne', maxlength: 80, 'aria-label': 'Nazwa inwestora' });
  const capIn = h('input', { type: 'number', min: 100, step: 100, value: 10000, 'aria-label': 'Kapitał początkowy USD' });
  const pctIn = h('input', { type: 'number', min: 0.5, max: 100, step: 0.5, value: 5, 'aria-label': 'Depozyt na wejście, % kapitału' });
  const pctChips = h('div', { class: 'row wrap' }, ...SIZING.map((p) => h('button', { type: 'button', class: 'chip toggle',
    onclick: () => { pctIn.value = p; check(); } }, `${p}%`)));
  const picked = new Map();   // sid → select z wariantem
  const errBox = h('div', { class: 'checks' });

  const stratRow = (s) => {
    const box = h('input', { type: 'checkbox', 'aria-label': `Strategia ${s.name}` });
    const sel = h('select', { disabled: true, 'aria-label': `Wariant strategii ${s.name}` }, h('option', {}, 'zaznacz, żeby wybrać wariant'));
    box.addEventListener('change', async () => {
      if (!box.checked) { picked.delete(s.id); sel.disabled = true; check(); return; }
      sel.replaceChildren(h('option', {}, 'wczytywanie wariantów…'));
      picked.set(s.id, { s, sel });
      check();
      const choices = variantChoices(await variantsOf(s.id), s.doc?.frozenVariant ?? null);
      if (!choices.length) {
        sel.replaceChildren(h('option', {}, 'brak wariantów z wynikiem'));
        box.checked = false; picked.delete(s.id); check(); return;
      }
      sel.replaceChildren(...choices.map((c, i) => h('option', { value: c.id, selected: i === 0 }, c.label)));
      sel.disabled = false;
      check();
    });
    const v = s.result;
    return h('div', { class: 'ipick' },
      h('label', { class: 'row' }, box, h('b', {}, s.name), s.doc?.frozenAt ? h('span', { class: 'chip frozen' }, '❄ zamrożona') : null,
        h('span', { class: `chip ${{ green: 'ok', yellow: 'warn', red: 'bad' }[v.verdict] || ''}` }, `werdykt: ${{ green: 'zielony', yellow: 'żółty', red: 'czerwony' }[v.verdict] || '—'}`)),
      sel);
  };

  const form = h('form', { method: 'dialog', class: 'editor' },
    h('div', { class: 'row between' }, h('h2', {}, 'Nowy inwestor'),
      h('button', { type: 'button', class: 'btn ghost icon', 'aria-label': 'Zamknij', onclick: () => dlg.close() }, '✕')),
    h('p', { class: 'muted small' }, 'Wirtualne konto (paper trading): handluje od chwili dodania, tylko na nowych świecach, '
      + 'wszystkimi wybranymi strategiami naraz, ze wspólnym kapitałem. Kod i wariant strategii zapisują się w obecnej wersji. '
      + 'Ustawień nie da się później zmienić — tylko usunąć inwestora.'),
    h('label', {}, 'Nazwa', nameIn),
    h('div', { class: 'grid2 tight' },
      h('label', {}, 'Kapitał początkowy (USD)', capIn),
      h('label', {}, 'Depozyt na każde wejście (% kapitału)', pctIn, pctChips)),
    h('div', {}, h('div', { class: 'lbl' }, `Strategie (${strategies.length} policzonych)`),
      strategies.length ? h('div', { class: 'ipicks' }, ...strategies.map(stratRow))
        : h('div', { class: 'banner warn' }, 'Nie ma jeszcze policzonych strategii — dodaj i policz strategię w zakładce Strategie.')),
    errBox,
    h('div', { class: 'row end' }, h('button', { type: 'button', class: 'btn ghost', onclick: () => dlg.close() }, 'Anuluj'),
      h('button', { class: 'btn accent', type: 'submit', id: 'inv-submit' }, 'Dodaj inwestora')));

  const values = () => ({ name: nameIn.value.trim(), capital: Number(capIn.value), pct: Number(pctIn.value) });
  function check(show = false) {
    const v = values();
    const errs = validateInvestor({ ...v, strategies: [...picked.values()].map(() => ({ code: 'x' })) });
    const loading = [...picked.values()].some(({ sel }) => sel.disabled);
    $('#inv-submit', form).disabled = loading || (show && errs.length > 0);
    errBox.innerHTML = '';
    if (show) errs.forEach((e) => errBox.append(h('div', { class: 'chk bad' }, `✘ ${e}`)));
    return errs.length === 0 && !loading;
  }
  [nameIn, capIn, pctIn].forEach((el) => el.addEventListener('input', () => check()));

  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    if (!check(true)) return;
    const btn = $('#inv-submit', form);
    btn.disabled = true;
    try {
      const chosen = [];
      for (const [sid, { s, sel }] of picked) {
        const code = s.doc?.code || await getText(`results/${encodeURIComponent(sid)}/strategy.py`);
        chosen.push({ strategyId: sid, name: s.name, code, variantId: Number(sel.value), variantLabel: sel.selectedOptions[0]?.textContent || '' });
      }
      const v = { ...values(), strategies: chosen };
      const errs = validateInvestor(v);
      if (errs.length) { errs.forEach((e) => errBox.append(h('div', { class: 'chk bad' }, `✘ ${e}`))); btn.disabled = false; return; }
      const id = await createInvestor(v);
      dlg.close();
      toast(`Inwestor „${v.name}” dodany — Mac zacznie go liczyć od najbliższej świecy.`, 'ok', 6000);
      location.hash = `#/inwestorzy/${encodeURIComponent(id)}`;
    } catch (e) {
      toast(e.message || String(e), 'bad', 8000);
      btn.disabled = false;
    }
  });

  const dlg = h('dialog', { class: 'modal wide' }, form);
  dlg.addEventListener('close', () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
  check();
  nameIn.focus();
}
