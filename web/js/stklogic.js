// Stocks (D-071): czyste funkcje zakładki (bez DOM) — testowane w Node (tests/web/stocks.test.mjs).
import { fmtWarsaw, nextDecisionMs } from './revlogic.js';

export const TICKER_RE = /^[A-Z0-9][A-Z0-9.-]{0,11}$/;   // ten sam wzór co w Apps Script (STK_RE)
export const DEFAULT_TICKERS = ['MU', 'MSFT', 'AAPL', 'MO', 'CVX', 'JPM', 'PM', 'JNJ', 'AMZN', 'FE', 'KO', 'MMM', 'NVDA', 'MRK', 'SO',
  'SYY', 'PPL', 'DUK', 'GPC', 'VZ', 'NEE', 'USB', 'AMT', 'FRT', 'GOOGL', 'PEP', 'O'];
export const DEFAULTS = { capital: 10000, band: 20 };
const r2 = (x) => Math.round(x * 100) / 100;

export function cleanTicker(t) { return String(t ?? '').trim().toUpperCase(); }

/** Szkic ustawień z dokumentu stocks/config (albo z config.json z gałęzi data, albo domyślny). */
export function draftFrom(cfg) {
  const rows = [];
  for (const x of cfg?.tickers || []) {
    const t = cleanTicker(x?.t ?? x);
    if (t && !rows.some((r) => r.t === t)) rows.push({ t, w: Number(x?.w ?? 0) });
  }
  if (!rows.length && !cfg) return equalize({ tickers: DEFAULT_TICKERS.map((t) => ({ t, w: 0 })), ...DEFAULTS });
  return { tickers: rows, capital: Number(cfg?.capital ?? DEFAULTS.capital), band: Number(cfg?.band ?? DEFAULTS.band) };
}

export const sumW = (d) => r2((d?.tickers || []).reduce((a, r) => a + (Number(r.w) || 0), 0));

/** Równe udziały, suma dokładnie 100 (reszta z zaokrągleń na ostatniej spółce). */
export function equalize(d) {
  const n = d.tickers.length;
  if (!n) return { ...d };
  const w = Math.floor((100 / n) * 100) / 100;
  const tickers = d.tickers.map((r, i) => ({ ...r, w: i === n - 1 ? r2(100 - w * (n - 1)) : w }));
  return { ...d, tickers };
}

/** Proporcjonalnie do 100% (spółki z 0% zostają z 0%). */
export function fitTo100(d) {
  const s = d.tickers.reduce((a, r) => a + (Number(r.w) || 0), 0);
  if (s <= 0) return equalize(d);
  const tickers = d.tickers.map((r) => ({ ...r, w: r2(((Number(r.w) || 0) * 100) / s) }));
  const diff = r2(100 - tickers.reduce((a, r) => a + r.w, 0));
  const big = tickers.reduce((b, r, i) => (r.w > tickers[b].w ? i : b), 0);
  tickers[big] = { ...tickers[big], w: r2(tickers[big].w + diff) };
  return { ...d, tickers };
}

/** Dodanie spółki: zwraca { draft, error }. Nowa spółka dostaje średni udział (potem „Dopasuj do 100%”). */
export function addTicker(d, raw) {
  const t = cleanTicker(raw);
  if (!t) return { draft: d, error: 'Wpisz symbol spółki (np. KO).' };
  if (!TICKER_RE.test(t)) return { draft: d, error: `„${t}” to nie jest symbol z Yahoo (litery, cyfry, kropka, myślnik).` };
  if (d.tickers.some((r) => r.t === t)) return { draft: d, error: `${t} już jest na liście.` };
  const avg = d.tickers.length ? r2(100 / (d.tickers.length + 1)) : 100;
  return { draft: { ...d, tickers: [...d.tickers, { t, w: avg }] }, error: null };
}

export function removeTicker(d, t) { return { ...d, tickers: d.tickers.filter((r) => r.t !== t) }; }

export function setWeight(d, t, w) { return { ...d, tickers: d.tickers.map((r) => (r.t === t ? { ...r, w: Number(w) } : r)) }; }

/** Lista błędów szkicu (pusta = można liczyć). */
export function validateDraft(d) {
  const e = [];
  if ((d?.tickers || []).length < 2) e.push('Potrzeba co najmniej 2 spółek.');
  if ((d?.tickers || []).some((r) => !(Number(r.w) > 0))) e.push('Każda spółka musi mieć udział większy od 0% (albo ją usuń).');
  if (Math.abs(sumW(d) - 100) > 0.05) e.push(`Udziały sumują się do ${sumW(d).toLocaleString('pl-PL')}%, a muszą do 100%.`);
  if (!(Number(d?.capital) >= 100)) e.push('Kapitał musi wynosić co najmniej 100 USD.');
  if (!(Number(d?.band) >= 0 && Number(d?.band) <= 50)) e.push('Pasmo: od 0 do 50%.');
  return e;
}

export function sameConfig(a, b) {
  const k = (d) => JSON.stringify({ t: (d?.tickers || []).map((r) => [r.t, r2(Number(r.w) || 0)]), c: Number(d?.capital), b: Number(d?.band) });
  return k(a) === k(b);
}

/** Stan liczenia z dokumentu stocks/config (pisze Mac). */
export function runStatus(doc, mac) {
  const s = doc?.status;
  if (s === 'do_policzenia') return { state: 'warn', text: mac?.online ? 'W kolejce — Mac zaraz zacznie liczyć.' : 'Czeka na Maca — uruchom ia5 start.' };
  if (s === 'liczy_sie') return { state: 'ok', text: 'Mac liczy backtest (tysiące konfiguracji — zwykle kilka minut).' };
  if (s === 'czeka_na_dane') return { state: 'warn', text: `Czekam na dane nowych spółek: ${(doc.waiting || []).join(', ')} (Apps Script pobiera je co kilka minut).` };
  if (s === 'blad') return { state: 'bad', text: `Błąd liczenia: ${doc.error || '—'}` };
  if (s === 'policzony') return { state: 'ok', text: 'Backtest policzony.' };
  return { state: 'mute', text: '' };
}

/** Plan zleceń do pokazania: oczekujący, inaczej ostatni wykonany. */
export function currentPlan(st) {
  const plans = st?.plans || [];
  return plans.find((p) => p.status === 'zaplanowane') || plans.at(-1) || null;
}

/** Transakcje pogrupowane po dniu wykonania (od najnowszego), w grupie: sprzedaże, potem kupna. */
export function ledgerByDay(st) {
  const by = new Map();
  for (const r of st?.ledger || []) {
    if (!by.has(r.exec_day)) by.set(r.exec_day, []);
    by.get(r.exec_day).push(r);
  }
  return [...by.entries()].sort((a, b) => (a[0] < b[0] ? 1 : -1))
    .map(([day, rows]) => ({ day, rows: rows.sort((a, b) => a.value - b.value), bought: rows.filter((r) => r.value > 0).reduce((s, r) => s + r.value, 0),
      sold: -rows.filter((r) => r.value < 0).reduce((s, r) => s + r.value, 0), cost: rows.reduce((s, r) => s + (r.cost || 0), 0) }));
}

const f = (x, d) => (x == null ? '' : Number(x).toFixed(d));

export function ledgerCSV(st) {
  const head = 'dzien_wykonania;spolka;ruch;sztuk;cena_wykonania;cena_z_planu;wartosc_usd;koszt_usd';
  const rows = (st?.ledger || []).map((r) => [r.exec_day, r.t, r.side, r.shares, f(r.price, 4), f(r.price_plan, 4), f(r.value, 2), f(r.cost, 2)].join(';'));
  return [head, ...rows].join('\n') + '\n';
}

/** Wynik od startu: metoda, stały podział, kup i trzymaj. */
export function liveSummary(st) {
  const c0 = st?.capital0 ?? 0;
  const v = st?.valuation?.at(-1);
  const m = st?.today?.total ?? v?.[1] ?? c0, fx = st?.today?.fixed_total ?? v?.[2] ?? c0, hd = st?.today?.hold_total ?? v?.[3] ?? c0;
  const p = (x) => (c0 ? (x / c0 - 1) * 100 : 0);
  return { capital0: c0, total: m, change: m - c0, pct: p(m), fixed: fx, fixedPct: p(fx), hold: hd, holdPct: p(hd), cash: st?.today?.cash ?? null };
}

/** Wiersze „portfel dziś” (udział, cel bazowy, pasmo, cel metody) w % — malejąco po celu bazowym. */
export function holdingRows(st) {
  return (st?.today?.rows || []).map((r) => ({ ...r, weightPct: r.weight * 100, basePct: r.base * 100, loPct: r.lo * 100, hiPct: r.hi * 100, targetPct: r.target * 100 }))
    .sort((a, b) => b.basePct - a.basePct || a.t.localeCompare(b.t));
}

/** Następny plan: wtorek 08:00 czasu polskiego; wykonanie na otwarciu sesji (15:30 czasu polskiego, zwykle). */
export function nextPlanText(st, nowMs) {
  const t = st?.next?.plan_ts ? st.next.plan_ts * 1000 : nextDecisionMs(nowMs);
  return t ? fmtWarsaw(t / 1000) : '—';
}

/** Lata backtestu: nadwyżka metody nad stałym podziałem (p.p.). */
export function yearRows(res) {
  return (res?.years || []).map((y) => ({ ...y, excess: y.winner - y.fixed }));
}

// ---------- odliczanie do rebalansu (D-071, prośba Michała 2026-11-22) ----------

function zoneParts(ms, tz) {
  const f = new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short', hourCycle: 'h23' });
  const o = {};
  for (const p of f.formatToParts(new Date(ms))) if (p.type !== 'literal') o[p.type] = p.type === 'weekday' ? p.value : +p.value;
  return o;
}

/** Czas lokalny w strefie tz → ms UTC. */
export function zonedToUtc(tz, y, m, d, hh = 0, mm = 0) {
  const guess = Date.UTC(y, m - 1, d, hh, mm);
  const off = (t) => { const p = zoneParts(t, tz); return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - Math.floor(t / 60000) * 60000; };
  let t = guess - off(guess);
  t = guess - off(t);
  return t;
}

/** Otwarcie sesji (09:30 w Nowym Jorku) w dniu 'RRRR-MM-DD' albo w najbliższy następny dzień roboczy. */
export function nyOpenMs(day) {
  let d = new Date(`${day}T12:00:00Z`);
  while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d = new Date(d.getTime() + 86400000);
  return zonedToUtc('America/New_York', d.getUTCFullYear(), d.getUTCMonth() + 1, d.getUTCDate(), 9, 30);
}

/** Najbliższy rebalans: { planMs, execMs, pending }. pending = zlecenia już policzone, czekają na otwarcie sesji. */
export function nextRebalance(st, nowMs) {
  const pend = (st?.plans || []).find((p) => p.status === 'zaplanowane');
  if (pend) return { planMs: pend.plan_ts * 1000, execMs: nyOpenMs(pend.exec_from), pending: true };
  const planMs = st?.next?.plan_ts ? st.next.plan_ts * 1000 : null;
  if (!planMs) return { planMs: null, execMs: null, pending: false };
  const p = zoneParts(planMs, 'America/New_York');
  const day = `${p.year}-${String(p.month).padStart(2, '0')}-${String(p.day).padStart(2, '0')}`;
  let exec = nyOpenMs(day);
  if (exec <= planMs) exec = nyOpenMs(new Date(Date.parse(`${day}T12:00:00Z`) + 86400000).toISOString().slice(0, 10));
  return { planMs, execMs: exec, pending: false };
}

/** Zdanie o transakcji: „Kup 3 akcje KO po 61,20 USD = 183,60 USD”. */
export function orderSentence(o, pending) {
  const px = pending ? o.price_plan : (o.price ?? o.price_plan);
  const val = Math.abs(pending ? o.value_plan : (o.value ?? o.value_plan));
  const n = o.shares;
  const word = n === 1 ? 'akcję' : (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) ? 'akcje' : 'akcji';
  const fmt = (x) => x.toLocaleString('pl-PL', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  return `${o.side === 'kupno' ? 'Kup' : 'Sprzedaj'} ${n} ${word} ${o.t} po ${fmt(px)} USD = ${fmt(val)} USD`;
}

/** Tabela portfela dziś z gotówką i sumą — udziały + gotówka = 100%, wartości = kapitał. */
export function holdingsWithCash(st) {
  const rows = holdingRows(st);
  const t = st?.today || {};
  const cash = t.cash ?? 0, total = t.total ?? 0;
  const inv = rows.reduce((s, r) => s + r.value, 0);
  return { rows, cash, cashPct: total > 0 ? (cash / total) * 100 : 0, invested: inv, total,
    sumPct: rows.reduce((s, r) => s + r.weightPct, 0) + (total > 0 ? (cash / total) * 100 : 0), ok: Math.abs(inv + cash - total) < 0.01 };
}
