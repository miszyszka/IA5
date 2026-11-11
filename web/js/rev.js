// Zakładka REV (D-063): wirtualne 10 000 zł rozkładane co wtorek 08:00 na przecenione waluty (limit 50% na koszyk).
// Wszystko liczy Mac (badanie) i GitHub Actions (portfel); strona czyta rev/ z gałęzi data — 0 odczytów Firestore (R8).
import { bars, disposeAll, plnLines } from './charts.js';
import { getJSON, getText } from './data.js';
import { allocation, basketLabel, candleDay, countdown, fmtWarsaw, ledgerByDecision, ledgerCSV, liveSummary, nextDecisionMs, rankingRows, VERDICT_ICON, verdictBadge } from './revlogic.js';
import { $, ago, cls, copy, download, h, num, signed, store, toast } from './util.js';

const ui = { more: 6, allVariants: false };
const kpi = (label, val, c = '') => h('div', { class: 'kpi' }, h('small', {}, label), h('b', { class: c }, val));
const panel = (title, hint, ...body) => h('section', { class: 'panel' }, h('div', { class: 'phead' }, h('h3', {}, title), hint ? h('span', { class: 'hint' }, hint) : null), ...body);
const day = (ts) => (ts ? fmtWarsaw(ts).slice(0, 10) : '—');
const zl = (x, d = 2) => `${num(x, d)} zł`;
const CHECK = {
  oos_excess: 'Nadwyżka nad równym podziałem na sprawdzianie (OOS), % rocznie', random: 'Percentyl wobec 1000 losowych podziałów (OOS)',
  dsr: 'DSR — czy to nie szczęście wśród wszystkich prób (IS)', pbo: 'PBO — ryzyko przeuczenia (cała historia)', lag: 'Wymiana dzień później (OOS), % rocznie',
};

export async function loadRev() {
  try {
    const [st, res] = await Promise.all([getJSON('rev/state.json'), getJSON('rev/research.json')]);
    store.set('revError', null);
    if (st?.computedAt !== store.state.rev?.computedAt) store.set('rev', st);
    if (res?.computedAt !== store.state.revResearch?.computedAt) store.set('revResearch', res);
  } catch (e) {
    store.set('revError', e.message || String(e));
  }
}

function header(st, res) {
  const b = verdictBadge(res);
  const s = liveSummary(st);
  const now = Date.now();
  const next = st?.next_rebalance ? st.next_rebalance * 1000 : nextDecisionMs(now);
  const nextText = !next ? '—' : next <= now ? `${fmtWarsaw(next / 1000).slice(5)} · czeka na kursy z poniedziałku (najpóźniej 20:00)`
    : `${fmtWarsaw(next / 1000).slice(5)} · ${countdown(next - now)}`;
  const started = st && st.rebalances?.length;
  return h('div', { class: 'ihead panel' }, h('h2', {}, 'REV'),
    h('div', { class: 'istatus', 'data-state': { green: 'ok', yellow: 'warn', red: 'bad' }[b.color] || 'mute' }, h('i', { class: 'dot flat' }),
      h('b', {}, res ? res.frozen.label : 'brak badania'), h('span', {}, res ? `werdykt badania ${b.text}` : ''),
      st ? h('span', { class: 'muted' }, ` · ostatnia zmiana stanu ${ago(st.computedAt)}`) : ''),
    h('p', { class: 'muted small' }, 'Pierwszy podział od razu po badaniu, potem co wtorek o 08:00 (cena z zamknięcia poniedziałku) cały kapitał jest dzielony na waluty proporcjonalnie do tego, jak bardzo są teraz tanie wobec złotego. Żaden koszyk — waluta, blok o sztywnym kursie ani PLN — nie ma więcej niż 50%; PLN do 75%, gdy metoda ma zawór złotówkowy albo hamulec i właśnie działa. Bez spreadów i opłat.'),
    h('div', { class: 'kpis small' },
      kpi('Kapitał teraz', zl(s.total), cls(s.change)), kpi('Od startu', `${signed(s.change, 2)} zł (${signed(s.pct, 2)}%)`, cls(s.change)),
      kpi('Równy podział', `${zl(s.equal)} (${signed(s.equalPct, 2)}%)`, cls(s.equalPct)),
      kpi('Następne przeliczenie', nextText),
      kpi('Przewalutowania', started ? `${st.rebalances.length} wtorków, ${st.ledger.length} zmian` : '—')));
}

function allocationPanel(st) {
  const rows = allocation(st);
  const el = h('div', { class: 'chart' });
  const list = h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
    h('thead', {}, h('tr', {}, ...['koszyk', 'wartość', 'udział'].map((l) => h('th', {}, l)))),
    h('tbody', {}, ...rows.map((r) => h('tr', {}, h('td', { class: 'txt' }, h('b', {}, r.label)), h('td', { class: 'r' }, zl(r.value)), h('td', { class: 'r' }, `${num(r.pct, 1)}%`))))));
  const valve = st.rebalances?.at(-1)?.pln_valve;
  const p = panel('Gdzie jest kapitał dziś', `wycena z zamknięcia ${candleDay(st.today?.ts)} · blok o sztywnym kursie to jeden słupek` + (valve ? ' · zawór złotówkowy włączony: PLN do 75%' : ''), el, list);
  return { p, draw: () => rows.length && bars(el, rows, 50) };
}

function equityPanel(st) {
  const v = st.valuation || [];
  const el = h('div', { class: 'chart tall' });
  const ts = [st.start_ts, ...v.map((x) => x[0])];
  const series = [
    { name: 'REV', ts, values: [st.capital0, ...v.map((x) => x[1])], color: '--accent' },
    { name: 'Równy podział', ts, values: [st.capital0, ...v.map((x) => x[2])], color: '--muted' },
    { name: '10 000 zł (wszystko w PLN)', ts, values: ts.map(() => st.capital0), color: '--dim', dash: true },
  ];
  const marks = (st.rebalances || []).filter((r) => r.changes > 0).map((r) => r.ts);
  return { p: panel('Kapitał w złotówkach', 'gdyby dziś wszystko wymienić na złote · kropki = wtorki z przewalutowaniem', el), draw: () => v.length && plnLines(el, series, marks) };
}

function rankingPanel(st) {
  const rows = rankingRows(st);
  const f = (x) => (x == null ? '—' : signed(x, 2));
  return panel('Ranking dziś', `oceny z przeliczenia ${day(st.rebalances?.at(-1)?.ts)} · dodatnia = tania (przecena) / rośnie (trend) wobec koszyka walut`,
    h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
      h('thead', {}, h('tr', {}, ...['koszyk', 'ocena metody', 'przecena 5 lat', 'trend 3 mies.', 'cel', 'teraz', 'różnica'].map((l) => h('th', {}, l)))),
      h('tbody', {}, ...rows.map((r) => h('tr', {}, h('td', { class: 'txt' }, h('b', {}, r.label)), h('td', { class: `r ${cls(r.score)}` }, f(r.score)),
        h('td', { class: `r ${cls(r.value)}` }, f(r.value)), h('td', { class: `r ${cls(r.trend)}` }, f(r.trend)), h('td', { class: 'r' }, r.target > 0 ? h('b', {}, `${num(r.target, 1)}%`) : `${num(r.target, 1)}%`),
        h('td', { class: 'r' }, `${num(r.now, 1)}%`), h('td', { class: `r ${cls(Math.abs(r.change) < 0.05 ? 0 : r.change)}` }, `${signed(Math.abs(r.change) < 0.05 ? 0 : r.change, 1)} p.p.`)))))));
}

function ledgerPanel(st) {
  const groups = ledgerByDecision(st);
  const rb = new Map((st.rebalances || []).map((r) => [r.ts, r]));
  const body = groups.slice(0, ui.more).flatMap((g) => {
    const r = rb.get(g.ts) || {};
    const note = [r.pln_valve ? 'zawór złotówkowy: PLN do 75%' : '', r.held?.length ? `nie sprzedane na stracie: ${r.held.join(', ')}` : '', r.late?.length ? `cena sprzed poniedziałku: ${r.late.join(', ')}` : '', r.frozen?.length ? `bez notowań: ${r.frozen.join(', ')}` : ''].filter(Boolean).join(' · ');
    return [h('tr', { class: 'grp' }, h('td', { colspan: 6, class: 'txt' }, h('b', {}, `${fmtWarsaw(g.ts)} · ${g.rows.filter((x) => x.basket !== 'PLN').length} zmian · przewalutowano ${zl(r.turnover_pln || 0, 0)}`), note ? h('span', { class: 'muted' }, ` · ${note}`) : '')),
      ...g.rows.map((x) => h('tr', {}, h('td', { class: 'txt' }, basketLabel(x.basket, st.blocs)), h('td', { class: 'txt' }, x.value_pln > 0 ? 'kupno' : 'sprzedaż'),
        h('td', { class: 'r' }, num(Math.abs(x.units_after - x.units_before), 2)), h('td', { class: 'r' }, num(x.price, 4)),
        h('td', { class: `r ${cls(x.value_pln)}` }, `${signed(x.value_pln, 2)} zł`), h('td', { class: 'txt' }, x.price_day || '')))];
  });
  return panel('Transakcje', 'wszystkie przewalutowania — wartość w złotych po kursie z zamknięcia poniedziałku',
    h('div', { class: 'row end' }, h('button', { class: 'btn ghost small', onclick: () => download('rev-transakcje.csv', ledgerCSV(st), 'text/csv') }, 'Pobierz CSV')),
    groups.length ? h('div', { class: 'tablewrap' }, h('table', { class: 'data compact static' },
      h('thead', {}, h('tr', {}, ...['koszyk', 'ruch', 'ilość', 'kurs (zł za 1)', 'wartość', 'dzień ceny'].map((l) => h('th', {}, l)))), h('tbody', {}, ...body))) : h('div', { class: 'empty small' }, 'Jeszcze bez przewalutowań.'),
    groups.length > ui.more ? h('button', { class: 'btn ghost small', onclick: () => { ui.more += 10; render(); } }, `Pokaż starsze (${groups.length - ui.more})`) : '');
}

function researchPanel(res) {
  const p = res.periods, v = res.validation, ver = res.verdict;
  const pctf = (x, d = 2) => (x == null ? '—' : signed(x, d));
  const sh = (x) => x?.sharpe ?? x?.ir ?? null;   // D-065: wybór po Sharpe w PLN (REV 1: IR wobec równego podziału)
  const all = [...res.variants].sort((a, b) => (sh(b.is) ?? -9) - (sh(a.is) ?? -9));
  const shown = ui.allVariants ? all : all.filter((x, i) => i < 12 || x.id === res.winner);
  const vt = h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['wariant', 'Sharpe IS', 'CAGR IS', 'Sharpe OOS', 'CAGR OOS', 'nadwyżka OOS % r.', 'wzrost w 52 tyg. (OOS)', 'maks. spadek OOS', 'PLN 75% (tyg.)'].map((l) => h('th', {}, l)))),
    h('tbody', {}, ...shown.map((x) => h('tr', { class: x.id === res.winner ? 'sel' : '' }, h('td', { class: 'txt' }, x.id === res.winner ? h('b', {}, `${x.label} ← zwycięzca`) : x.label),
      h('td', { class: 'r' }, num(sh(x.is), 2)), h('td', { class: `r ${cls(x.is.cagr_pct)}` }, pctf(x.is.cagr_pct)),
      h('td', { class: 'r' }, num(sh(x.oos), 2)), h('td', { class: `r ${cls(x.oos.cagr_pct)}` }, pctf(x.oos.cagr_pct)), h('td', { class: `r ${cls(x.oos.excess_pct_yr)}` }, pctf(x.oos.excess_pct_yr)),
      h('td', { class: 'r' }, x.oos.up52 == null ? '—' : `${num(x.oos.up52, 0)}%`),
      h('td', { class: 'r neg' }, x.oos.max_dd_pct == null ? '—' : `${num(x.oos.max_dd_pct, 1)}%`), h('td', { class: 'r' }, x.pln75_pct ? `${num(x.pln75_pct, 0)}%` : '—')))));
  const more = all.length > shown.length || ui.allVariants ? h('button', { class: 'btn ghost small', onclick: () => { ui.allVariants = !ui.allVariants; render(); } },
    ui.allVariants ? 'Pokaż mniej' : `Pokaż wszystkie (${all.length})`) : '';
  const ct = h('table', { class: 'data compact static' }, h('thead', {}, h('tr', {}, ...['test', 'wynik', 'próg', ''].map((l) => h('th', {}, l)))),
    h('tbody', {}, ...ver.checks.map((c) => h('tr', {}, h('td', { class: 'txt' }, CHECK[c.id] || c.id), h('td', { class: 'r' }, c.value == null ? '—' : num(c.value, 2)), h('td', { class: 'txt' }, c.need),
      h('td', { class: c.ok ? 'pos' : 'neg' }, c.ok ? '✓' : '✗')))));
  const el = h('div', { class: 'chart' });
  const hist = res.history;
  const series = [{ name: `${res.winner} (zwycięzca)`, ts: hist.ts, values: hist.winner, color: '--accent' }, { name: 'Równy podział', ts: hist.ts, values: hist.equal, color: '--muted' }];
  const draw = () => hist.ts.length > 1 && plnLines(el, series, [], [{ ts: p.is_end_ts, label: 'sprawdzian (OOS)' }]);
  const body = h('details', { class: 'panel fdetails', open: true }, h('summary', {}, h('b', {}, 'Badanie metody'), h('span', { class: 'hint' }, ' — historia, nie wynik na żywo')),
    h('p', { class: 'muted small' }, `${res.variants.length} metod sprawdzonych na tych samych wtorkach od ${day(p.start_ts)}. Wybór tylko na pierwszych 75% (IS, do ${day(p.is_end_ts)}) — ${v.selection === 'sharpe_pln' ? 'najrówniejszy wzrost kapitału w złotych (Sharpe)' : 'najlepszy wynik wobec równego podziału'}; dalej sprawdzian, którego wybór nie widział (OOS, do ${day(p.oos_end_ts)}). Werdykt ${VERDICT_ICON[ver.color]} ${ver.passed}/${ver.of}. Koszyki: ${res.universe.map((c) => basketLabel(c, res.blocs)).join(', ')}.` + (Object.keys(res.rejected || {}).length ? ` Pominięte (rzadkie kursy): ${Object.keys(res.rejected).join(', ')}.` : '')),
    h('div', { class: 'tablewrap' }, vt), more, h('h3', {}, 'Czy to nie przypadek'), h('div', { class: 'tablewrap' }, ct),
    h('p', { class: 'muted small' }, `Losowe podziały: ${v.random_paths} ścieżek. Bootstrap nadwyżki OOS: ${pctf(v.boot?.low)} … ${pctf(v.boot?.high)}% rocznie. Największy spadek (wycena dzienna): metoda ${num(v.max_dd_daily_pct?.winner, 1)}%, równy podział ${num(v.max_dd_daily_pct?.equal, 1)}%. Zmian koszyka rocznie: ${num(v.trades_per_year, 0)}.`),
    h('h3', {}, 'Jak metoda działałaby w przeszłości'), el,
    h('div', { class: 'row' }, h('button', { class: 'btn ghost small', onclick: async () => toast((await copy(await getText('rev/report.md'))) ? 'Skopiowano raport dla Claude.' : 'Nie udało się skopiować.', 'ok') }, 'Kopiuj raport dla Claude')));
  return { p: body, draw };
}

function render() {
  const root = $('#view-rev');
  if (store.state.route?.view !== 'rev') return;
  const st = store.state.rev, res = store.state.revResearch;
  disposeAll();
  const err = store.state.revError ? h('div', { class: 'banner warn' }, `GitHub: ${store.state.revError}`) : '';
  if (!res) {
    root.replaceChildren(header(null, null), err, h('div', { class: 'empty' }, h('h3', {}, 'Badanie metody jeszcze się nie odbyło'),
      h('p', {}, 'Krok: w Apps Script wklej nowy Code.gs i uruchom raz backfillPLN(), potem restart ia5 start (docs/SETUP.md, „Kursy złotówkowe”).')));
    return;
  }
  const red = res.verdict.color === 'red' ? h('div', { class: 'banner warn' }, 'Metoda nie pokonała równego podziału na sprawdzianie — portfel działa, ale kieruj się nim ostrożnie; obok równy podział.') : '';
  const rp = researchPanel(res);
  if (!st || !st.rebalances?.length) {
    const next = nextDecisionMs(Date.now());
    const start = st?.start_ts ? st.start_ts * 1000 : next;
    root.replaceChildren(header(st, res), err, red, h('div', { class: 'empty' }, h('h3', {}, `Portfel startuje we wtorek ${fmtWarsaw(start / 1000)} — ${countdown(start - Date.now())}`),
      h('p', {}, 'Wtedy 10 000 zł zostanie rozłożone na waluty według zamrożonej metody.')), rp.p);
    rp.draw();
    return;
  }
  const a = allocationPanel(st), e = equityPanel(st);
  root.replaceChildren(header(st, res), err, red, a.p, e.p, rankingPanel(st), ledgerPanel(st), rp.p,
    (st.archive || []).length ? panel('Poprzednie metody', 'po zmianie metody portfel startuje od nowa (R6)', h('ul', { class: 'plain small' },
      ...st.archive.map((x) => h('li', {}, `${x.method?.label || x.method?.id}: ${day(x.start_ts)} – ${day(x.end_ts)}, ${zl(x.final)} (równy podział ${zl(x.equal_final)})`)))) : '');
  a.draw(); e.draw(); rp.draw();
}

export function renderRev() { render(); }

export function initRev() {
  store.on('rev', () => render());
  store.on('revResearch', () => render());
  store.on('revError', () => render());
  setInterval(() => { if (store.state.route?.view === 'rev') render(); }, 60 * 1000);   // odliczanie do wtorku
}
