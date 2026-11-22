// Zakładka Stocks (D-071): cotygodniowe rebalansowanie portfela spółek w paśmie ±B wokół udziałów docelowych.
// Ustawienia (spółki, udziały, kapitał, pasmo) idą do Firestore stocks/config po „Policz backtest”; wyniki (badanie i portfel
// na żywo) strona czyta ze stocks/ na gałęzi data.
import { disposeAll, moneyLines, stockBars, yearBars } from './charts.js';
import { getJSON, getText, refreshData } from './data.js';
import { saveStocksConfig, watchStocksConfig } from './fb.js';
import { countdown, fmtWarsaw, VERDICT_ICON } from './revlogic.js';
import { heartbeatState } from './status.js';
import { addTicker, currentPlan, draftFrom, equalize, fitTo100, holdingsWithCash, ledgerByDay, ledgerCSV, liveSummary, nextRebalance, orderSentence, removeTicker, runStatus, sameConfig, setWeight, sumW, validateDraft, yearRows } from './stklogic.js';
import { $, ago, cls, copy, download, h, num, signed, store, toast } from './util.js';

const DRAFT_KEY = 'ia5.stocks.draft';
const ui = { more: 4, allTop: false };
const kpi = (label, val, c = '') => h('div', { class: 'kpi' }, h('small', {}, label), h('b', { class: c }, val));
const panel = (title, hint, ...body) => h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, title), hint ? h('span', { class: 'hint' }, hint) : null), ...body);
const usd = (x, d = 2) => (x == null ? '—' : `${num(x, d)} USD`);
const pctf = (x, d = 1) => (x == null ? '—' : `${num(x, d)}%`);
const CHECK = {
  oos_excess: 'Nadwyżka nad stałym podziałem na sprawdzianie (OOS), % rocznie', random: 'Percentyl wobec 1000 losowych przesunięć w tym samym paśmie (OOS)',
  dsr: 'DSR — czy to nie szczęście wśród wszystkich prób (IS)', pbo: 'PBO — ryzyko przeuczenia (cała historia)', cost2: 'Nadwyżka OOS przy podwójnym koszcie, % rocznie',
};

// ---------- dane ----------

export async function loadStocks() {
  try {
    const [st, res, cfg] = await Promise.all([getJSON('stocks/state.json'), getJSON('stocks/research.json'), getJSON('stocks/config.json')]);
    store.set('stocksError', null);
    if (st?.computedAt !== store.state.stocks?.computedAt) store.set('stocks', st);
    if (res?.computedAt !== store.state.stocksResearch?.computedAt) store.set('stocksResearch', res);
    if (JSON.stringify(cfg) !== JSON.stringify(store.state.stocksCfgData)) store.set('stocksCfgData', cfg);
  } catch (e) {
    store.set('stocksError', e.message || String(e));
  }
}

function savedConfig() {
  return store.state.stocksDoc || store.state.stocksCfgData || store.state.stocksResearch?.config || null;
}

function readDraft() {
  try { return JSON.parse(localStorage.getItem(DRAFT_KEY) || 'null'); } catch { return null; }
}
function writeDraft(d) {
  try { if (d) localStorage.setItem(DRAFT_KEY, JSON.stringify(d)); else localStorage.removeItem(DRAFT_KEY); } catch { /* tryb prywatny */ }
}
function draft() {
  if (!store.state.stocksDraft) store.state.stocksDraft = readDraft() || draftFrom(savedConfig());
  return store.state.stocksDraft;
}
function setDraft(d, rerender = true) {
  store.state.stocksDraft = d;
  writeDraft(sameConfig(d, draftFrom(savedConfig())) ? null : d);
  if (rerender) render();
}

// ---------- nagłówek ----------

function header(st, res, doc) {
  const s = liveSummary(st);
  const mac = heartbeatState(store.state.beat);
  const rs = runStatus(doc, mac);
  const v = res?.verdict;
  const state = rs.state !== 'mute' && doc?.status !== 'policzony' ? rs.state : v ? { green: 'ok', yellow: 'warn', red: 'bad' }[v.color] : 'mute';
  const now = Date.now();
  const pend = currentPlan(st)?.status === 'zaplanowane';
  return h('div', { class: 'ihead panel' }, h('h2', {}, 'Stocks'),
    h('div', { class: 'istatus', 'data-state': state }, h('i', { class: 'dot flat' }),
      h('b', {}, res ? res.frozen.label : 'brak backtestu'), res ? h('span', {}, `werdykt ${VERDICT_ICON[v.color]} ${v.passed}/${v.of}`) : '',
      rs.text && doc?.status !== 'policzony' ? h('span', { class: 'muted' }, ` · ${rs.text}`) : st ? h('span', { class: 'muted' }, ` · ostatnie przeliczenie ${ago(Math.min(st.computedAt, Date.now() / 1000))}`) : ''),
    h('p', { class: 'muted small' }, 'Co tydzień we wtorek o 08:00 system liczy zlecenia z zamknięcia poprzedniej sesji, a wykonuje je na otwarciu sesji we wtorek (15:30 czasu polskiego; w święto — następny dzień sesji). Każda spółka może mieć od −20% do +20% swojego udziału docelowego: więcej tam, gdzie metoda widzi przecenę, mniej tam, gdzie spółka jest droga. Metodę wybrał backtest spośród tysięcy konfiguracji.'),
    st?.plans?.length ? h('div', { class: 'kpis small' },
      kpi('Kapitał teraz', usd(s.total), cls(s.change)), kpi('Od startu', `${signed(s.change, 2)} USD (${signed(s.pct, 2)}%)`, cls(s.change)),
      kpi('Stały podział', `${usd(s.fixed, 0)} (${signed(s.fixedPct, 2)}%)`, cls(s.fixedPct)), kpi('Kup i trzymaj', `${usd(s.hold, 0)} (${signed(s.holdPct, 2)}%)`, cls(s.holdPct)),
      kpi('Gotówka', usd(s.cash))) : '',
    st?.plans?.length ? countdownBox(st, now, pend) : '');
}

function countdownBox(st, now, pend) {
  const r = nextRebalance(st, now);
  if (!r.execMs) return '';
  const when = (ms) => fmtWarsaw(ms / 1000);
  return h('div', { class: 'stk-next' },
    h('div', {}, h('small', {}, pend ? 'Zlecenia czekają na otwarcie sesji' : 'Do następnego rebalansu'), h('b', { class: 'stk-cd' }, countdown(r.execMs - now))),
    h('div', { class: 'muted small' }, pend
      ? `Wykonanie: ${when(r.execMs)} czasu polskiego (otwarcie sesji w Nowym Jorku) · lista zleceń niżej`
      : `Plan zleceń: ${when(r.planMs)} (z zamknięcia poprzedniej sesji) · wykonanie: ${when(r.execMs)} czasu polskiego (otwarcie sesji w Nowym Jorku)`));
}

function reconcile(sm, exec) {
  if (!sm) return '';
  const line = (label, v, c = '') => h('tr', {}, h('td', { class: 'txt' }, label), h('td', { class: `r ${c}` }, v));
  return h('table', { class: 'data compact static stk-rec' }, h('tbody', {},
    sm.value != null ? line('Kapitał przed rebalansem (akcje + gotówka)', usd(sm.value)) : '',
    line('Gotówka przed', usd(sm.cash_before)),
    line(`+ sprzedaż (${sm.n_sell})`, `+${num(sm.sold, 2)} USD`, sm.sold ? 'pos' : ''),
    line(`− kupno (${sm.n_buy})`, `−${num(sm.bought, 2)} USD`, sm.bought ? 'neg' : ''),
    line('− koszty transakcji (0,10%)', `−${num(sm.cost, 2)} USD`, sm.cost ? 'neg' : ''),
    h('tr', { class: 'sum' }, h('td', { class: 'txt' }, h('b', {}, exec ? 'Gotówka po wykonaniu' : 'Gotówka po zleceniach (reszta z zaokrągleń do całych akcji)')), h('td', { class: 'r' }, h('b', {}, usd(sm.cash_after)))),
    sm.value_after != null ? line('Kapitał po wykonaniu (ceny otwarcia)', usd(sm.value_after)) : ''));
}

// ---------- ustawienia ----------

function settingsPanel() {
  const d = draft();
  const user = store.state.user;
  const doc = store.state.stocksDoc;
  const status = store.state.status?.stk || {};
  const have = status.tickers || {}, rej = status.rejected || {};
  const saved = draftFrom(savedConfig());
  const dirty = !sameConfig(d, saved);
  const sumEl = h('b', {});
  const errEl = h('div', { class: 'small' });
  const go = h('button', { class: 'btn accent', onclick: () => submit() }, 'Policz backtest');
  const band = Number(d.band) / 100;
  const refresh = () => {
    const s = sumW(d);
    sumEl.textContent = `Suma udziałów: ${num(s, 2)}%`;
    sumEl.className = Math.abs(s - 100) <= 0.05 ? 'pos' : 'neg';
    const errs = validateDraft(d);
    errEl.replaceChildren(...errs.map((e) => h('div', { class: 'neg' }, e)));
    go.disabled = !!errs.length || !user || ['do_policzenia', 'liczy_sie', 'czeka_na_dane'].includes(doc?.status);
    go.title = !user ? 'Zaloguj się (prawy górny róg)' : '';
  };
  const dataCell = (t) => {
    if (rej[t]) return h('span', { class: 'neg' }, `odrzucona: ${rej[t]}`);
    if (have[t]) return h('span', { class: 'muted' }, `${have[t].name ? have[t].name + ' · ' : ''}od ${have[t].firstDay || '—'}`);
    return h('span', { class: 'warn-t' }, 'nowa — Apps Script pobierze ją po zapisie');
  };
  const rows = d.tickers.map((r) => {
    const loHi = h('span', { class: 'muted mono' }, `${num(r.w * (1 - band), 2)} – ${num(r.w * (1 + band), 2)}%`);
    const inp = h('input', { type: 'number', min: '0', step: '0.01', value: String(Math.round(Number(r.w) * 100) / 100), class: 'num w-pct', 'aria-label': `Udział ${r.t} w %` });
    inp.addEventListener('input', () => {
      const w = Number(inp.value);
      Object.assign(d, setWeight(d, r.t, Number.isFinite(w) ? w : 0));
      loHi.textContent = `${num((Number.isFinite(w) ? w : 0) * (1 - band), 2)} – ${num((Number.isFinite(w) ? w : 0) * (1 + band), 2)}%`;
      setDraft(d, false);
      refresh();
    });
    return h('tr', {}, h('td', { class: 'txt' }, h('b', {}, r.t)), h('td', { class: 'r' }, inp, ' %'), h('td', { class: 'r' }, loHi), h('td', { class: 'txt small' }, dataCell(r.t)),
      h('td', { class: 'r' }, h('button', { class: 'btn ghost small', title: `Usuń ${r.t}`, 'aria-label': `Usuń ${r.t}`, onclick: () => setDraft(removeTicker(d, r.t)) }, '✕')));
  });
  const addInp = h('input', { type: 'text', placeholder: 'symbol z Yahoo, np. KO', maxlength: '12', class: 'mono', 'aria-label': 'Nowa spółka' });
  const add = () => {
    const r = addTicker(d, addInp.value);
    if (r.error) { toast(r.error, 'bad'); return; }
    setDraft(r.draft);
    setTimeout(() => $('#stk-add')?.focus(), 0);
  };
  addInp.id = 'stk-add';
  addInp.addEventListener('keydown', (e) => { if (e.key === 'Enter') add(); });
  const cap = h('input', { type: 'number', min: '100', step: '100', value: String(d.capital), class: 'num big', 'aria-label': 'Kapitał w USD' });
  cap.addEventListener('input', () => { d.capital = Number(cap.value); setDraft(d, false); refresh(); });
  const bandInp = h('input', { type: 'number', min: '0', max: '50', step: '1', value: String(d.band), class: 'num w-pct', 'aria-label': 'Pasmo w %' });
  bandInp.addEventListener('change', () => { d.band = Number(bandInp.value); setDraft(d); });
  async function submit() {
    const errs = validateDraft(d);
    if (errs.length) { toast(errs[0], 'bad'); return; }
    go.disabled = true;
    try {
      await saveStocksConfig(d);
      setDraft(d, false);
      writeDraft(null);
      toast('Zapisane — Mac policzy backtest (zwykle kilka minut; nowe spółki najpierw pobiera Apps Script).', 'ok', 8000);
    } catch (e) {
      toast(e.message || String(e), 'bad', 10000);
      go.disabled = false;
    }
  }
  const el = h('section', { class: 'panel', id: 'stk-settings' },
    h('div', { class: 'phead' }, h('h3', {}, 'Portfel'), h('span', { class: 'hint' }, dirty ? 'masz niezapisane zmiany' : doc?.result?.at ? `ostatni backtest ${ago(doc.result.at)}` : '')),
    h('div', { class: 'stk-capital' }, h('label', {}, h('span', {}, 'Kapitał na inwestycje'), h('span', { class: 'row' }, cap, h('b', {}, 'USD'))),
      h('label', {}, h('span', {}, 'Pasmo wokół udziału docelowego'), h('span', { class: 'row' }, '±', bandInp, '%'))),
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static stk-table' },
      h('thead', {}, h('tr', {}, ...['spółka', 'udział docelowy', 'system może trzymać', 'dane', ''].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...rows,
        h('tr', { class: 'addrow' }, h('td', { colspan: 4, class: 'txt' }, h('span', { class: 'row' }, addInp, h('button', { class: 'btn small', onclick: add, title: 'Dodaj spółkę' }, '+ Dodaj'))), h('td', {}))))),
    h('div', { class: 'row wrap between' }, h('span', { class: 'row wrap' }, sumEl,
      h('button', { class: 'btn ghost small', onclick: () => setDraft(equalize(d)) }, 'Rozłóż równo'),
      h('button', { class: 'btn ghost small', onclick: () => setDraft(fitTo100(d)) }, 'Dopasuj do 100%'),
      dirty ? h('button', { class: 'btn ghost small', onclick: () => { writeDraft(null); store.state.stocksDraft = null; render(); } }, 'Cofnij zmiany') : ''),
    h('span', { class: 'row' }, !user ? h('span', { class: 'hint' }, 'Zaloguj się, żeby zapisać') : '', go)),
    errEl);
  refresh();
  return el;
}

// ---------- plan, portfel, transakcje ----------

function planPanel(st) {
  const pl = currentPlan(st);
  if (!pl) return '';
  const pend = pl.status === 'zaplanowane';
  const rows = pend ? pl.orders : (pl.fills || []).filter((f) => f.filled);
  const title = pend ? `Zlecenia do wykonania — otwarcie sesji ${pl.exec_from} (15:30 czasu polskiego)` : `Ostatni rebalans — wykonany ${pl.exec_day}`;
  const hint = `plan ${fmtWarsaw(pl.plan_ts)} z cen zamknięcia ${pl.signal_day}` + (pl.late ? ' (świeca poprzedniej sesji spóźniona — użyta starsza)' : '');
  const sorted = [...rows].sort((a, b) => (a.side === b.side ? Math.abs(b.value ?? b.value_plan) - Math.abs(a.value ?? a.value_plan) : a.side === 'sprzedaż' ? -1 : 1));
  const notFilled = pend ? [] : (pl.fills || []).filter((f) => !f.filled);
  return panel(title, hint,
    sorted.length ? h('ol', { class: 'stk-orders' }, ...sorted.map((o) => h('li', { class: o.side === 'kupno' ? 'buy' : 'sell' }, orderSentence(o, pend))))
      : h('div', { class: 'empty small' }, 'Bez transakcji — różnice między stanem a celem są mniejsze niż próg metody.'),
    notFilled.length ? h('p', { class: 'neg small' }, `Niewykonane: ${notFilled.map((f) => `${f.t} (${f.why || 'brak ceny otwarcia'})`).join(', ')}`) : '',
    !pend && rows.some((f) => f.planned_shares) ? h('p', { class: 'muted small' }, `Zmniejszone przy wykonaniu (cena otwarcia wyższa niż w planie, zabrakło gotówki): ${rows.filter((f) => f.planned_shares).map((f) => `${f.t} ${f.shares} zamiast ${f.planned_shares}`).join(', ')}`) : '',
    h('h3', {}, 'Rozliczenie gotówki'),
    reconcile(pend ? pl.summary_plan : pl.summary_exec || pl.summary_plan, !pend));
}

function holdingsPanel(st) {
  const H = holdingsWithCash(st);
  const rows = H.rows;
  if (!rows.length) return { p: '', draw: () => {} };
  const el = h('div', { class: 'chart tall' });
  const t = h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
    h('thead', {}, h('tr', {}, ...['spółka', 'sztuk', 'cena', 'wartość USD', 'udział', 'docelowo', 'pasmo', 'cel metody', 'przecena'].map((l) => h('th', {}, l)))),
    h('tbody', {}, ...rows.map((r) => h('tr', {}, h('td', { class: 'txt' }, h('b', {}, r.t)), h('td', { class: 'r' }, num(r.shares, 0)), h('td', { class: 'r' }, num(r.price, 2)),
      h('td', { class: 'r' }, num(r.value, 2)), h('td', { class: 'r' }, h('b', {}, pctf(r.weightPct, 2))), h('td', { class: 'r' }, pctf(r.basePct, 2)),
      h('td', { class: 'r muted' }, `${num(r.loPct, 2)} – ${num(r.hiPct, 2)}%`), h('td', { class: `r ${cls(r.targetPct - r.basePct)}` }, pctf(r.targetPct, 2)),
      h('td', { class: `r ${cls(r.score)}` }, signed(r.score, 2)))),
      h('tr', {}, h('td', { class: 'txt' }, h('b', {}, 'Gotówka')), h('td', {}), h('td', {}), h('td', { class: 'r' }, num(H.cash, 2)), h('td', { class: 'r' }, h('b', {}, pctf(H.cashPct, 2))),
        h('td', { colspan: 4, class: 'txt muted' }, 'reszta z zaokrągleń do całych akcji i dywidendy — wchodzi do następnego rebalansu')),
      h('tr', { class: 'sum' }, h('td', { class: 'txt' }, h('b', {}, 'Razem')), h('td', {}), h('td', {}), h('td', { class: 'r' }, h('b', {}, num(H.total, 2))),
        h('td', { class: `r ${Math.abs(H.sumPct - 100) < 0.01 ? '' : 'neg'}` }, h('b', {}, pctf(H.sumPct, 2))),
        h('td', { colspan: 4, class: `txt ${H.ok ? 'muted' : 'neg'}` }, H.ok ? `akcje ${num(H.invested, 2)} + gotówka ${num(H.cash, 2)} = ${num(H.total, 2)} USD ✓` : 'suma się nie zgadza — zgłoś Claude\'owi')))));
  const p = panel('Portfel dziś', `wycena z zamknięcia ${st.today.day} · słupek = udział teraz, kreski = pasmo, romb = cel metody · przecena > 0 = tania`, el, t);
  return { p, draw: () => stockBars(el, rows) };
}

function livePanel(st) {
  const v = st.valuation || [];
  if (v.length < 2) return { p: '', draw: () => {} };
  const el = h('div', { class: 'chart' });
  const ts = v.map((x) => x[0]);
  const series = [{ name: 'metoda', ts, values: v.map((x) => x[1]), color: '--accent' }, { name: 'stały podział', ts, values: v.map((x) => x[2]), color: '--muted' },
    { name: 'kup i trzymaj', ts, values: v.map((x) => x[3]), color: '--dim', dash: true }];
  return { p: panel('Kapitał na żywo', `od ${fmtWarsaw(st.start_ts).slice(0, 10)} · ${num(st.capital0, 0)} USD na start`, el), draw: () => moneyLines(el, series) };
}

function ledgerPanel(st) {
  const groups = ledgerByDay(st);
  const plans = new Map((st.plans || []).filter((p) => p.exec_day).map((p) => [p.exec_day, p]));
  const blocks = groups.slice(0, ui.more).map((g) => {
    const sm = plans.get(g.day)?.summary_exec;
    return h('div', { class: 'stk-day' },
      h('div', { class: 'row between' }, h('b', {}, `Rebalans ${g.day} (otwarcie sesji) · ${g.rows.length} transakcji`),
        sm ? h('span', { class: 'muted small' }, `gotówka ${num(sm.cash_before, 2)} + sprzedaż ${num(sm.sold, 2)} − kupno ${num(sm.bought, 2)} − koszty ${num(sm.cost, 2)} = ${num(sm.cash_after, 2)} USD`) : ''),
      h('ol', { class: 'stk-orders' }, ...g.rows.map((r) => h('li', { class: r.side === 'kupno' ? 'buy' : 'sell' }, orderSentence(r, false),
        h('span', { class: 'muted' }, ` · plan po ${num(r.price_plan, 2)} · koszt ${num(r.cost, 2)}`)))));
  });
  const divs = (st.dividends || []).slice(-8).reverse();
  return panel('Historia transakcji', 'każdy rebalans: co system kupił i sprzedał, po jakiej cenie i jak zmieniła się gotówka',
    h('div', { class: 'row end' }, h('button', { class: 'btn ghost small', onclick: () => download('stocks-transakcje.csv', ledgerCSV(st), 'text/csv') }, 'Pobierz CSV')),
    groups.length ? h('div', { class: 'stk-days' }, ...blocks) : h('div', { class: 'empty small' }, 'Jeszcze bez transakcji — pierwsze zakupy na najbliższym otwarciu sesji.'),
    groups.length > ui.more ? h('button', { class: 'btn ghost small', onclick: () => { ui.more += 8; render(); } }, `Pokaż starsze (${groups.length - ui.more})`) : '',
    divs.length ? h('p', { class: 'muted small' }, 'Ostatnie dywidendy (do gotówki): ' + divs.map((x) => `${x.day} ${x.t} ${num(x.amount, 2)} USD`).join(' · ')) : '');
}

// ---------- backtest ----------

function backtestPanel(res) {
  const p = res.periods, v = res.validation, ver = res.verdict, w = res.winner_detail, b = res.baselines;
  const hist = res.history;
  const el = h('div', { class: 'chart tall' }), yel = h('div', { class: 'chart' });
  const series = [{ name: 'metoda (zwycięzca)', ts: hist.ts, values: hist.winner, color: '--accent' }, { name: 'stały podział (co tydzień do celu)', ts: hist.ts, values: hist.fixed, color: '--muted' },
    { name: 'kup i trzymaj', ts: hist.ts, values: hist.hold, color: '--dim', dash: true }];
  const draw = () => { moneyLines(el, series, [{ ts: p.is_end_ts, label: 'sprawdzian (OOS)' }]); yearBars(yel, yearRows(res)); };
  const cmp = (label, m, mo) => h('tr', {}, h('td', { class: 'txt' }, label), h('td', { class: `r ${cls(m.cagr_pct)}` }, signed(m.cagr_pct, 2)), h('td', { class: `r ${cls(mo.cagr_pct)}` }, signed(mo.cagr_pct, 2)),
    h('td', { class: 'r' }, num(mo.sharpe, 2)), h('td', { class: 'r neg' }, pctf(mo.max_dd_pct, 1)), h('td', { class: 'r' }, pctf(mo.turnover_yr, 0)));
  const top = ui.allTop ? res.top : res.top.slice(0, 8);
  const head = `${res.trials.toLocaleString('pl-PL')} konfiguracji sprawdzonych na tych samych tygodniach od ${fmtWarsaw(p.start_ts).slice(0, 10)}. Wybór tylko na pierwszych 75% (IS, do ${fmtWarsaw(p.is_end_ts).slice(0, 10)}); dalej sprawdzian, którego wybór nie widział (OOS, ${p.oos_weeks} tygodni). Werdykt ${VERDICT_ICON[ver.color]} ${ver.passed}/${ver.of}.`
    + (res.missing?.length ? ` Bez danych (pominięte): ${res.missing.join(', ')}.` : '') + ` Koszt ${num(res.cost * 100, 2)}% od każdej transakcji, dywidendy wliczone.`;
  return {
    p: h('details', { class: 'panel fdetails', open: true }, h('summary', {}, h('b', {}, 'Backtest metody'), h('span', { class: 'hint' }, ' — historia, nie wynik na żywo')),
      h('p', { class: 'muted small' }, head),
      h('p', {}, h('b', {}, 'Zwycięzca: '), w.label),
      h('div', { class: 'kpis small' }, kpi('Nadwyżka OOS', `${signed(w.oos.excess_pct_yr, 2)}% rocznie`, cls(w.oos.excess_pct_yr)), kpi('IR nadwyżki IS / OOS', `${num(w.is.ir, 2)} / ${num(w.oos.ir, 2)}`),
        kpi('Lepsze od losowych', pctf(v.random_pct, 0)), kpi('Konfiguracji z OOS > 0', pctf(res.distribution.oos_positive_pct, 0)), kpi('Otwarcia OOS', res.oos_openings ?? '—')),
      h('h3', {}, `Skuteczność w backteście (${num(res.config.capital, 0)} USD na start, dane od ${res.data_from || '2010-01-01'})`),
      el,
      h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['', 'CAGR IS %', 'CAGR OOS %', 'Sharpe OOS', 'maks. spadek OOS', 'obrót OOS / rok'].map((l) => h('th', {}, l)))),
        h('tbody', {}, cmp('metoda', w.is, w.oos), cmp('stały podział', b.fixed.is, b.fixed.oos), cmp('kup i trzymaj', b.hold.is, b.hold.oos)))),
      h('h3', {}, 'Rok po roku'), yel,
      h('h3', {}, 'Czy to nie przypadek'),
      h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['test', 'wynik', 'próg', ''].map((l) => h('th', {}, l)))),
        h('tbody', {}, ...ver.checks.map((c) => h('tr', {}, h('td', { class: 'txt' }, CHECK[c.id] || c.id), h('td', { class: 'r' }, c.value == null ? '—' : num(c.value, 2)), h('td', { class: 'txt' }, c.need),
          h('td', { class: c.ok ? 'pos' : 'neg' }, c.ok ? '✓' : '✗')))))),
      h('p', { class: 'muted small' }, `Bootstrap nadwyżki OOS: ${signed(v.boot?.low, 2)} … ${signed(v.boot?.high, 2)}% rocznie. Losowe przesunięcia (mediana OOS): ${signed(v.random_oos_median, 2)}% rocznie.`),
      h('h3', {}, 'Najlepsze konfiguracje (ranking po IS)'),
      h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['#', 'konfiguracja', 'IR IS', 'IR OOS', 'nadwyżka OOS % r.'].map((l) => h('th', {}, l)))),
        h('tbody', {}, ...top.map((r) => h('tr', { class: r.id === res.winner ? 'sel' : '' }, h('td', { class: 'r' }, r.rank_is), h('td', { class: 'txt' }, r.label),
          h('td', { class: 'r' }, num(r.is.ir, 2)), h('td', { class: 'r' }, num(r.oos.ir, 2)), h('td', { class: `r ${cls(r.oos.excess_pct_yr)}` }, signed(r.oos.excess_pct_yr, 2))))))),
      h('button', { class: 'btn ghost small', onclick: () => { ui.allTop = !ui.allTop; render(); } }, ui.allTop ? 'Pokaż mniej' : `Pokaż ${res.top.length}`),
      h('div', { class: 'row' }, h('button', { class: 'btn ghost small', onclick: async () => toast((await copy(await getText('stocks/report.md'))) ? 'Skopiowano raport dla Claude.' : 'Nie udało się skopiować.', 'ok') }, 'Kopiuj raport dla Claude'))),
    draw,
  };
}

// ---------- całość ----------

function render() {
  const root = $('#view-stocks');
  if (store.state.route?.view !== 'stocks') return;
  const st = store.state.stocks, res = store.state.stocksResearch, doc = store.state.stocksDoc;
  disposeAll();
  const err = store.state.stocksError ? h('div', { class: 'banner warn' }, `GitHub: ${store.state.stocksError}`) : '';
  const rs = runStatus(doc, heartbeatState(store.state.beat));
  const runBanner = doc && doc.status !== 'policzony' && rs.text ? h('div', { class: `banner ${rs.state === 'bad' ? 'warn' : ''}` }, rs.text) : '';
  const settings = settingsPanel();
  if (!res) {
    root.replaceChildren(header(st, null, doc), err, runBanner, settings, h('div', { class: 'empty' }, h('h3', {}, 'Backtestu jeszcze nie ma'),
      h('p', {}, 'Mac policzy go sam po starcie (ia5 start) — dla listy powyżej. Świece spółek pobiera Apps Script: wklej nowy Code.gs (docs/SETUP.md, „Spółki”).')));
    return;
  }
  const partial = res.missing?.length ? h('div', { class: 'banner warn' }, `Ten backtest liczono bez: ${res.missing.join(', ')} (brak danych) — policzy się od nowa, gdy dane będą.`) : '';
  const red = res.verdict.color === 'red' ? h('div', { class: 'banner warn' }, 'Werdykt 🔴: backtest nie potwierdził przewagi metody nad stałym podziałem — portfel działa, ale traktuj go ostrożnie; obok widać stały podział i „kup i trzymaj”.') : '';
  const hp = st ? holdingsPanel(st) : { p: '', draw: () => {} };
  const lp = st ? livePanel(st) : { p: '', draw: () => {} };
  const bp = backtestPanel(res);
  const waiting = !st?.plans?.length ? h('div', { class: 'empty small' }, 'Portfel na żywo wystartuje po najbliższym przeliczeniu (Mac albo GitHub Actions) — pierwsze zakupy na otwarciu najbliższej sesji.') : '';
  root.replaceChildren(header(st, res, doc), err, runBanner, partial, red, settings, st ? planPanel(st) : '', waiting, hp.p, lp.p, st ? ledgerPanel(st) : '', bp.p,
    (st?.archive || []).length ? panel('Poprzednie portfele', 'po zmianie metody albo ustawień portfel startuje od nowa', h('ul', { class: 'plain small' },
      ...st.archive.map((x) => h('li', {}, `${x.method?.label || x.method?.id}: ${fmtWarsaw(x.start_ts).slice(0, 10)} – ${x.end_ts ? fmtWarsaw(x.end_ts).slice(0, 10) : '—'}, ${usd(x.final, 0)} z ${usd(x.capital0, 0)} (stały podział ${usd(x.fixed_final, 0)})`)))) : '');
  hp.draw(); lp.draw(); bp.draw();
}

export function renderStocks() { render(); }

let unsub = null;
export function initStocks() {
  store.on('stocks', () => render());
  store.on('stocksResearch', () => render());
  store.on('stocksError', () => render());
  store.on('stocksCfgData', () => { if (!readDraft()) store.state.stocksDraft = null; render(); });
  store.on('user', async (u) => {
    unsub?.(); unsub = null;
    store.state.stocksDoc = null;
    if (!u) { render(); return; }
    let prev = null;
    unsub = await watchStocksConfig((doc, e) => {
      if (e) return;
      store.state.stocksDoc = doc;
      if (!readDraft()) store.state.stocksDraft = null;   // bez niezapisanych zmian szkic = zapisane ustawienia
      if (prev === 'liczy_sie' && doc?.status === 'policzony') { refreshData(); loadStocks(); }
      prev = doc?.status;
      render();
    });
  });
  store.on('status', () => { if (store.state.route?.view === 'stocks' && !document.activeElement?.closest?.('#stk-settings')) render(); });
  setInterval(() => { if (store.state.route?.view === 'stocks' && !document.activeElement?.closest?.('#stk-settings')) render(); }, 60 * 1000);
}
