// Zakładka REV (D-063, uproszczona w D-074): moje prawdziwe konto walutowe wobec systemu.
// System (podział i kursy) — rev/state.json z gałęzi data. Moje salda i moje przewalutowania — Firestore wallet/rev
// (1 odczyt przy wejściu + zmiany, 1 zapis na zmianę), kopia w przeglądarce; bez logowania albo bez reguł — tylko przeglądarka.
import { getJSON } from './data.js';
import { saveWallet, watchWallet } from './fb.js';
import {
  applyTx, candleDay, checkTx, countdown, fmtRate, fmtWarsaw, inputValue, minConversionPln, money, nextDecisionMs,
  normWallet, parseAmount, planConversions, verdictBadge, walletCSV, walletCurrencies, walletRows,
} from './revlogic.js';
import { $, download, h, num, store, toast } from './util.js';

const LS = 'ia5.rev.wallet';
const readLocal = () => { try { return JSON.parse(localStorage.getItem(LS) || 'null'); } catch { return null; } };
const writeLocal = (d) => { try { localStorage.setItem(LS, JSON.stringify(d)); } catch { /* prywatne okno */ } };
const W = { data: normWallet(readLocal()), mode: 'nologin', err: null, unsub: null, saving: false };
const keyOf = (d) => JSON.stringify({ b: d.balances, t: d.tx });
const hasData = (d) => d.tx.length > 0 || Object.values(d.balances).some((x) => x);

const ui = { form: { from: 'PLN', fromAmt: '', to: '', toAmt: '', fee: '', feeCur: '' }, toHint: '', more: 10, allCur: false };
const refs = {};   // komórki liczone na żywo (bez przebudowy pól, żeby nie gubić kursora)
const zl = (x) => `${num(x, 2)} zł`;
const day = (ts) => (ts ? fmtWarsaw(ts).slice(0, 10) : '—');
const panel = (title, hint, ...body) => h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, title), hint ? h('span', { class: 'hint' }, hint) : null), ...body);

export async function loadRev() {
  try {
    const [st, res] = await Promise.all([getJSON('rev/state.json'), getJSON('rev/research.json').catch(() => null)]);
    store.set('revError', null);
    if (st?.computedAt !== store.state.rev?.computedAt) store.set('rev', st);
    if (res?.computedAt !== store.state.revResearch?.computedAt) store.set('revResearch', res);
  } catch (e) {
    store.set('revError', e.message || String(e));
  }
}

// ---------- zapis konta ----------

const editing = () => { const a = document.activeElement; return a && a.tagName === 'INPUT' && $('#view-rev')?.contains(a); };

async function connect(user) {
  W.unsub?.();
  W.unsub = null;
  if (!user) { W.mode = 'nologin'; render(); return; }
  W.mode = 'loading';
  W.unsub = await watchWallet((doc, err) => {
    if (err) { W.mode = 'local'; W.err = err.code || err.message; render(); return; }
    W.mode = 'cloud'; W.err = null;
    if (!doc) { if (hasData(W.data)) persist(); else render(); return; }   // pierwszy raz: zapis z przeglądarki idzie do chmury
    const d = normWallet(doc);
    if (keyOf(d) === keyOf(W.data)) { saveHint(); return; }
    if (editing()) return;   // właśnie piszesz — Twoja wersja jest nowsza i zaraz się zapisze
    W.data = d; writeLocal(d); render();
  });
}

async function persist() {
  W.data = { ...W.data, updatedAt: Math.floor(Date.now() / 1000) };
  writeLocal(W.data);
  if (W.mode !== 'cloud') { saveHint(); return true; }
  W.saving = true; saveHint();
  try {
    await saveWallet(W.data);
    return true;
  } catch (e) {
    W.mode = 'local'; W.err = e.code || e.message;
    toast('Nie udało się zapisać w chmurze — zapisane w tej przeglądarce.', 'bad', 8000);
    return false;
  } finally { W.saving = false; saveHint(); }
}

function saveHint() {
  const el = refs.save;
  if (!el) return;
  const t = W.saving ? ['zapisuję…', ''] : W.mode === 'cloud' ? ['zapisane na Twoim koncie', 'ok']
    : W.mode === 'loading' ? ['wczytuję…', '']
      : W.mode === 'nologin' ? ['zapisane tylko w tej przeglądarce — zaloguj się, żeby mieć to wszędzie', 'warn']
        : [/permission/i.test(W.err || '') ? 'zapisane tylko w tej przeglądarce — wklej nowe reguły Firestore (docs/SETUP.md)' : `zapisane tylko w tej przeglądarce (${W.err})`, 'warn'];
  el.textContent = t[0];
  el.dataset.state = t[1];
}

// ---------- nagłówek ----------

function header(st, res) {
  const b = verdictBadge(res);
  const last = st?.rebalances?.at(-1);
  refs.cd = h('b', { class: 'mono' }, '');
  const head = h('section', { class: 'panel rev-head' },
    h('div', { class: 'rev-title' }, h('h2', {}, 'REV'),
      h('span', { class: 'muted' }, st?.method?.label || 'brak metody'), res ? h('span', { class: 'muted' }, `· werdykt badania ${b.text}`) : ''),
    h('div', { class: 'rev-facts' },
      h('div', {}, h('small', {}, 'Podział systemu z'), h('b', {}, last ? day(last.ts) : '—')),
      h('div', {}, h('small', {}, 'Kursy z zamknięcia'), h('b', {}, candleDay(st?.today?.ts))),
      h('div', {}, h('small', {}, 'Następne przeliczenie'), h('span', {}, h('b', {}, nextLabel(st)), ' ', refs.cd))));
  tick(st);
  return head;
}

const nextMs = (st) => (st?.next_rebalance ? st.next_rebalance * 1000 : nextDecisionMs(Date.now()));
const nextLabel = (st) => { const t = nextMs(st); return t ? `wt ${fmtWarsaw(t / 1000).slice(8, 10)}.${fmtWarsaw(t / 1000).slice(5, 7)} 08:00` : '—'; };
function tick(st = store.state.rev) {
  if (!refs.cd) return;
  const t = nextMs(st), now = Date.now();
  refs.cd.textContent = !t ? '' : t <= now ? '· czeka na kursy z poniedziałku' : `· ${countdown(t - now)}`;
}

// ---------- moje konto ----------

function accountPanel(st) {
  const codes = walletCurrencies(st);
  const w = st.today?.weights || {};
  // tylko to, co ważne: PLN, waluty systemu i te, które masz; resztę pokazuje „Pozostałe waluty”
  const extra = codes.filter((c) => c !== 'PLN' && !((w[c] || 0) > 1e-9) && !(Number(W.data.balances[c]) > 0));
  refs.cells = {};
  const rows = codes.map((code) => {
    const inp = h('input', {
      type: 'text', inputmode: 'decimal', class: 'amt', 'aria-label': `Ile masz ${code}`, placeholder: '0',
      value: W.data.balances[code] ? inputValue(W.data.balances[code], code) : '',
      oninput: (e) => {
        const v = parseAmount(e.target.value);
        const bad = Number.isNaN(v) || v < 0;
        e.target.classList.toggle('bad', bad);
        if (bad) return;
        W.data = { ...W.data, balances: { ...W.data.balances, [code]: v ?? 0 } };
        updateCalc(st);
      },
      onchange: (e) => { if (!e.target.classList.contains('bad')) persist(); },
      onkeydown: (e) => { if (e.key === 'Enter') e.target.blur(); },
    });
    const c = { val: h('td', { class: 'r' }), my: h('td', { class: 'r' }), sys: h('td', { class: 'r' }), diff: h('td', { class: 'r todo' }) };
    refs.cells[code] = c;
    return h('tr', { hidden: !ui.allCur && extra.includes(code) }, h('td', { class: 'txt' }, h('b', {}, code)),
      h('td', {}, h('span', { class: 'amt-wrap' }, inp, h('span', { class: 'cur' }, code))), c.val, c.my, c.sys, c.diff);
  });
  const more = extra.length ? h('button', { class: 'link small', onclick: () => { ui.allCur = !ui.allCur; render(); } },
    ui.allCur ? 'Ukryj waluty, których nie masz i system nie trzyma' : `Pozostałe waluty (${extra.join(', ')}) — system ich teraz nie trzyma`) : '';
  refs.foot = { total: h('td', { class: 'r' }), match: h('td', { class: 'r' }) };
  refs.plan = h('div', { class: 'rev-plan' });
  refs.save = h('span', { class: 'hint save' });
  const p = h('section', { class: 'panel' },
    h('div', { class: 'phead' }, h('h3', {}, 'Moje konto'), refs.save),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data static rev-wallet' },
      h('thead', {}, h('tr', {}, ...['waluta', 'mam na koncie', 'w złotych', 'mam', 'system', 'do wyrównania'].map((l, i) => h('th', { class: i > 1 ? 'r' : '' }, l)))),
      h('tbody', {}, ...rows),
      h('tfoot', {}, h('tr', {}, h('td', { class: 'txt' }, 'razem'), h('td', {}), refs.foot.total, h('td', { class: 'r' }, '100%'), h('td', { class: 'r' }, '100%'), refs.foot.match)))),
    more ? h('div', { class: 'more-cur' }, more) : '',
    h('h3', { class: 'sub' }, 'Przewalutuj teraz'), refs.plan);
  saveHint();
  updateCalc(st);
  return p;
}

function updateCalc(st) {
  const v = walletRows(st, W.data.balances);
  const min = minConversionPln(v.total);
  for (const r of v.rows) {
    const c = refs.cells?.[r.code];
    if (!c) continue;
    c.val.textContent = r.px ? (r.value ? zl(r.value) : '—') : 'brak kursu';
    c.my.textContent = v.total > 0 ? `${num(r.myPct, 1)}%` : '—';
    c.sys.textContent = `${num(r.sysPct, 1)}%`;
    const ok = v.total <= 0 || Math.abs(r.diff) < min;
    c.diff.textContent = v.total <= 0 ? '' : ok ? '✓' : `${r.diff > 0 ? 'kup' : 'sprzedaj'} ${money(Math.abs(r.diffUnits), r.code)}`;
    c.diff.dataset.state = ok ? 'ok' : r.diff > 0 ? 'buy' : 'sell';
  }
  refs.foot.total.textContent = zl(v.total);
  refs.foot.match.textContent = v.match == null ? '' : `zgodność ${num(v.match, 1)}%`;
  const plan = v.total > 0 ? planConversions(v, min) : [];
  refs.plan.replaceChildren(
    v.total <= 0 ? h('p', { class: 'muted' }, 'Wpisz, ile masz teraz w każdej walucie (puste = 0). Obok od razu pojawi się, co i na co wymienić, żeby konto było jak u systemu.')
      : !plan.length ? h('p', { class: 'okline' }, '✓ Konto zgadza się z systemem. Nic nie wymieniaj do następnego przeliczenia.')
        : h('ol', {}, ...plan.map((c) => h('li', {},
          h('span', { class: 'leg' }, h('b', {}, money(c.fromAmt, c.from)), h('span', { class: 'arrow', 'aria-hidden': 'true' }, '→'), h('span', {}, `ok. ${money(c.toAmt, c.to)}`),
            h('span', { class: 'muted' }, ` · ${zl(c.pln)}`)),
          h('button', { class: 'btn small', onclick: () => prefill(c) }, 'Wpisz wykonanie')))));
  quote();
}

function prefill(c) {
  ui.form = { from: c.from, fromAmt: inputValue(c.fromAmt, c.from), to: c.to, toAmt: '', fee: '', feeCur: c.from };
  ui.toHint = `ok. ${inputValue(c.toAmt, c.to)}`;
  render();
  const el = refs.toAmt;
  el?.scrollIntoView({ block: 'center' });
  el?.focus();
}

// ---------- zapis przewalutowania ----------

function formTx(st) {
  const f = ui.form;
  const t = { from: f.from, fromAmt: parseAmount(f.fromAmt) ?? 0, to: f.to, toAmt: parseAmount(f.toAmt) ?? 0, fee: parseAmount(f.fee) ?? 0, feeCur: f.feeCur || f.from };
  return { t, c: checkTx(t, W.data.balances, st.last_px) };
}

function formPanel(st) {
  const codes = walletCurrencies(st);
  if (!ui.form.to) ui.form.to = codes.find((c) => c !== ui.form.from) || '';
  const sel = (key, label) => h('select', { 'aria-label': label, onchange: (e) => { ui.form[key] = e.target.value; if (key === 'from' && !ui.form.feeTouched) ui.form.feeCur = e.target.value; syncFee(); quote(); } },
    ...codes.map((c) => h('option', { value: c, selected: (ui.form[key] || (key === 'feeCur' ? ui.form.from : '')) === c }, c)));
  const amt = (key, label, ph = '0,00') => h('input', { type: 'text', inputmode: 'decimal', class: 'amt', 'aria-label': label, placeholder: ph, value: ui.form[key],
    oninput: (e) => { ui.form[key] = e.target.value; e.target.classList.toggle('bad', Number.isNaN(parseAmount(e.target.value))); quote(); },
    onkeydown: (e) => { if (e.key === 'Enter') submit(st); } });
  refs.toAmt = amt('toAmt', 'Ile dostajesz', ui.toHint || '0,00');
  refs.feeSel = sel('feeCur', 'Waluta opłaty');
  refs.feeSel.addEventListener('change', () => { ui.form.feeTouched = true; });
  refs.quote = h('div', { class: 'rev-quote' });
  return panel('Zapisz przewalutowanie', 'wpisz dokładnie to, co pokazał bank',
    h('div', { class: 'txform' },
      h('label', {}, 'Sprzedaję', h('span', { class: 'pair' }, amt('fromAmt', 'Ile sprzedajesz'), sel('from', 'Waluta, którą sprzedajesz'))),
      h('span', { class: 'arrow big', 'aria-hidden': 'true' }, '→'),
      h('label', {}, 'Dostaję na konto', h('span', { class: 'pair' }, refs.toAmt, sel('to', 'Waluta, którą dostajesz'))),
      h('label', { class: 'fee' }, 'Opłata (pobrana osobno)', h('span', { class: 'pair' }, amt('fee', 'Opłata', '0'), refs.feeSel)),
      h('button', { class: 'btn accent', onclick: () => submit(st) }, 'Zapisz…')),
    refs.quote);
}

function syncFee() {
  if (refs.feeSel && !ui.form.feeTouched) { ui.form.feeCur = ui.form.from; refs.feeSel.value = ui.form.from; }
}

function quote() {
  const st = store.state.rev;
  if (!refs.quote || !st) return;
  const f = ui.form;
  if (!f.fromAmt && !f.toAmt) { refs.quote.replaceChildren(h('span', { class: 'muted' }, 'Kurs, koszt wobec rynku i salda po transakcji pojawią się tutaj.')); return; }
  const { t, c } = formTx(st);
  const bits = [];
  if (c.rate) bits.push(h('span', {}, 'kurs ', h('b', {}, fmtRate(t.from, t.to, c.rate))));
  if (c.mktRate) bits.push(h('span', { class: 'muted' }, `rynek ${fmtRate(t.from, t.to, c.mktRate)}`));
  if (c.costPln != null) bits.push(h('span', {}, 'koszt ', h('b', {}, `${num(c.costPln, 2)} zł`), h('span', { class: 'muted' }, ` (${num(c.costPct, 2)}%)`)));
  const msgs = c.ok || !t.fromAmt || !t.toAmt ? c.warnings : c.errors;
  refs.quote.replaceChildren(h('div', { class: 'row wrap' }, ...bits), ...msgs.map((m) => h('div', { class: 'warnline' }, m)));
}

function confirmBox(t, c) {
  return new Promise((resolve) => {
    const done = (v) => { dlg.close(); resolve(v); };
    const fee = t.fee > 0 ? money(t.fee, t.feeCur) : 'brak';
    const dlg = h('dialog', { class: 'modal small rev-confirm' },
      h('h3', {}, 'Zapisać to przewalutowanie?'),
      h('div', { class: 'leg big' }, h('b', {}, money(t.fromAmt, t.from)), h('span', { class: 'arrow' }, '→'), h('b', {}, money(t.toAmt, t.to))),
      h('dl', {},
        h('dt', {}, 'kurs'), h('dd', {}, fmtRate(t.from, t.to, c.rate)),
        h('dt', {}, 'opłata'), h('dd', {}, fee),
        h('dt', {}, 'koszt wobec rynku'), h('dd', {}, c.costPln == null ? '—' : `${num(c.costPln, 2)} zł (${num(c.costPct, 2)}%)`),
        ...c.changed.flatMap((code) => [h('dt', {}, `stan ${code}`), h('dd', {}, `${money(Number(W.data.balances[code]) || 0, code)} → ${money(c.after[code], code)}`)])),
      ...c.warnings.map((m) => h('p', { class: 'warnline' }, m)),
      h('div', { class: 'row end' }, h('button', { class: 'btn ghost', onclick: () => done(false) }, 'Wróć'), h('button', { class: 'btn accent', onclick: () => done(true) }, 'Potwierdź i zapisz')));
    dlg.addEventListener('close', () => { dlg.remove(); resolve(false); });
    document.body.append(dlg);
    dlg.showModal();
  });
}

async function submit(st) {
  const { t, c } = formTx(st);
  if (!c.ok) { quote(); toast(c.errors[0], 'bad', 6000); return; }
  if (!(await confirmBox(t, c))) return;
  const px = st.last_px || {};
  const mkt = Object.fromEntries([t.from, t.to, t.feeCur].filter((x) => px[x]).map((x) => [x, px[x]]));
  const tx = { id: `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`, at: Math.floor(Date.now() / 1000), from: t.from, fromAmt: t.fromAmt,
    to: t.to, toAmt: t.toAmt, fee: t.fee, feeCur: t.feeCur, mkt, pxDay: candleDay(st.today?.ts), costPln: c.costPln == null ? null : Math.round(c.costPln * 100) / 100 };
  W.data = { ...W.data, balances: c.after, tx: [...W.data.tx, tx] };
  ui.form = { from: t.from, fromAmt: '', to: t.to, toAmt: '', fee: '', feeCur: t.from };
  ui.toHint = '';
  render();
  if (await persist()) toast('Zapisano. Stan konta zaktualizowany.', 'ok');
}

// ---------- moje przewalutowania ----------

function historyPanel() {
  const tx = [...W.data.tx].sort((a, b) => b.at - a.at);
  const shown = tx.slice(0, ui.more);
  const del = async (t) => {
    const back = applyTx(W.data.balances, t, -1);
    const ok = await new Promise((resolve) => {
      const done = (v) => { dlg.close(); resolve(v); };
      const dlg = h('dialog', { class: 'modal small' }, h('h3', {}, 'Usunąć tę transakcję?'),
        h('p', {}, `${money(t.fromAmt, t.from)} → ${money(t.toAmt, t.to)} z ${fmtWarsaw(t.at)}. Salda wrócą do stanu sprzed niej: `
          + [...new Set([t.from, t.to, t.feeCur || t.from])].map((c) => money(back[c], c)).join(', ') + '.'),
        h('div', { class: 'row end' }, h('button', { class: 'btn ghost', onclick: () => done(false) }, 'Anuluj'), h('button', { class: 'btn danger', onclick: () => done(true) }, 'Usuń')));
      dlg.addEventListener('close', () => { dlg.remove(); resolve(false); });
      document.body.append(dlg);
      dlg.showModal();
    });
    if (!ok) return;
    W.data = { ...W.data, balances: back, tx: W.data.tx.filter((x) => x.id !== t.id) };
    render();
    persist();
  };
  return panel('Moje przewalutowania', tx.length ? `${tx.length} · tylko to, co zapisałeś` : '',
    tx.length ? h('div', { class: 'tablewrap' }, h('table', { class: 'data static compact' },
      h('thead', {}, h('tr', {}, ...['data', 'sprzedane', 'otrzymane', 'kurs', 'opłata', 'koszt wobec rynku', ''].map((l, i) => h('th', { class: i && i < 6 ? 'r' : '' }, l)))),
      h('tbody', {}, ...shown.map((t) => h('tr', {},
        h('td', { class: 'txt' }, fmtWarsaw(t.at)), h('td', { class: 'r' }, money(t.fromAmt, t.from)), h('td', { class: 'r' }, money(t.toAmt, t.to)),
        h('td', { class: 'r' }, fmtRate(t.from, t.to, t.toAmt / t.fromAmt)), h('td', { class: 'r' }, t.fee ? money(t.fee, t.feeCur || t.from) : '—'),
        h('td', { class: 'r' }, t.costPln == null ? '—' : `${num(t.costPln, 2)} zł`),
        h('td', { class: 'r' }, h('button', { class: 'btn ghost small icon', title: 'Usuń (cofa zmianę salda)', 'aria-label': 'Usuń transakcję', onclick: () => del(t) }, '✕'))))))) : h('p', { class: 'muted' }, 'Jeszcze nic. Po wymianie w banku wpisz ją wyżej — tu zostanie ślad z kursem i opłatą.'),
    h('div', { class: 'row between' },
      tx.length > ui.more ? h('button', { class: 'btn ghost small', onclick: () => { ui.more += 20; render(); } }, `Pokaż starsze (${tx.length - ui.more})`) : h('span'),
      tx.length ? h('button', { class: 'btn ghost small', onclick: () => download('rev-moje-przewalutowania.csv', walletCSV(W.data.tx), 'text/csv') }, 'Pobierz CSV') : ''));
}

// ---------- całość ----------

function render() {
  const root = $('#view-rev');
  if (store.state.route?.view !== 'rev' || !root) return;
  const st = store.state.rev, res = store.state.revResearch;
  const err = store.state.revError ? h('div', { class: 'banner warn' }, `GitHub: ${store.state.revError}`) : '';
  if (!st?.last_px || !st?.today?.weights) {
    root.replaceChildren(header(st, res), err, h('div', { class: 'empty' }, h('h3', {}, 'System REV jeszcze nie ma podziału'),
      h('p', {}, 'Podział pojawi się po pierwszym badaniu na Macu (docs/SETUP.md, „Kursy złotówkowe”).')));
    return;
  }
  const red = res?.verdict?.color === 'red' ? h('div', { class: 'banner warn' }, 'Metoda nie pokonała równego podziału na sprawdzianie — kieruj się nią ostrożnie.') : '';
  root.replaceChildren(header(st, res), err, red, accountPanel(st), formPanel(st), historyPanel());
  quote();
}

export function renderRev() { render(); }

export function initRev() {
  store.on('rev', () => render());
  store.on('revResearch', () => render());
  store.on('revError', () => render());
  store.on('user', (u) => connect(u));
  setInterval(() => { if (store.state.route?.view === 'rev') tick(); }, 30 * 1000);   // tylko odliczanie — bez przebudowy pól
}

