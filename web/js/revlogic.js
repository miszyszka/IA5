// REV (D-063, D-074): czyste funkcje zakładki (bez DOM) — testowane w Node (tests/web/rev.test.mjs).
const WAW = 'Europe/Warsaw';

function parts(ms, tz = WAW) {
  const f = new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  const o = {};
  for (const p of f.formatToParts(new Date(ms))) if (p.type !== 'literal') o[p.type] = +p.value;
  return o;
}

/** Przesunięcie strefy (ms) w chwili `ms`: czas lokalny − UTC. */
function offset(ms, tz = WAW) {
  const p = parts(ms, tz);
  return Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute) - Math.floor(ms / 60000) * 60000;
}

/** Czas lokalny w Warszawie → ms UTC (także w tygodniach zmiany czasu). */
export function warsawToUtc(y, m, d, hh = 0, mm = 0) {
  const guess = Date.UTC(y, m - 1, d, hh, mm);
  let t = guess - offset(guess);
  t = guess - offset(t);
  return t;
}

/** Najbliższy wtorek 08:00 czasu polskiego ≥ teraz (R2). */
export function nextDecisionMs(nowMs) {
  const p = parts(nowMs);
  for (let k = 0; k < 9; k++) {
    const day = new Date(Date.UTC(p.year, p.month - 1, p.day + k));
    if (day.getUTCDay() !== 2) continue;
    const t = warsawToUtc(day.getUTCFullYear(), day.getUTCMonth() + 1, day.getUTCDate(), 8, 0);
    if (t >= nowMs) return t;
  }
  return null;
}

/** 'RRRR-MM-DD HH:mm' czasu polskiego. */
export function fmtWarsaw(ts) {
  const p = parts(ts * 1000);
  const z = (x) => String(x).padStart(2, '0');
  return `${p.year}-${z(p.month)}-${z(p.day)} ${z(p.hour)}:${z(p.minute)}`;
}

/** Dzień świecy D1 po jej czasie zamknięcia (północ w Londynie) — 'RRRR-MM-DD'. */
export function candleDay(closeTs) {
  if (!closeTs) return '—';
  const p = parts((closeTs - 1) * 1000, 'Europe/London');
  const z = (x) => String(x).padStart(2, '0');
  return `${p.year}-${z(p.month)}-${z(p.day)}`;
}

export function countdown(ms) {
  if (ms == null) return '—';
  if (ms <= 0) return 'teraz';
  const min = Math.floor(ms / 60000), hh = Math.floor(min / 60), dd = Math.floor(hh / 24);
  if (dd >= 1) return `za ${dd} d ${hh % 24} h`;
  if (hh >= 1) return `za ${hh} h ${min % 60} min`;
  return `za ${min} min`;
}

export function basketLabel(code, blocs = {}) {
  const m = blocs?.[code];
  return m && m.length ? `${code} (+${m.join(', ')})` : code;
}

export const VERDICT_ICON = { green: '🟢', yellow: '🟡', red: '🔴' };

export function verdictBadge(research) {
  const v = research?.verdict;
  if (!v) return { color: 'mute', text: '—' };
  return { color: v.color, text: `${VERDICT_ICON[v.color] || ''} ${v.passed}/${v.of}` };
}

// ---------- Moje konto (D-074): prawdziwe salda Michała, plan przewalutowań i dziennik jego transakcji ----------

const DEC0 = new Set(['JPY', 'HUF']);
/** Ile miejsc po przecinku ma kwota w danej walucie (JPY, HUF — bez groszy). */
export const decimals = (code) => (DEC0.has(code) ? 0 : 2);
export const roundTo = (x, d) => Math.round(x * 10 ** d) / 10 ** d;
const r6 = (x) => Math.round(x * 1e6) / 1e6;

/** Kwota wpisana ręcznie: „1 234,56”, „1234.56”, „1.234,56” → liczba; puste → null; śmieci → NaN. */
export function parseAmount(v) {
  if (typeof v === 'number') return v;
  let s = String(v ?? '').replace(/[\s  ]/g, '');
  if (!s) return null;
  if (s.includes(',')) s = s.replace(/\./g, '').replace(',', '.');
  if (!/^-?\d*\.?\d+$|^-?\d+\.$/.test(s)) return NaN;
  return Number(s);
}

const nf = (d) => new Intl.NumberFormat('pl-PL', { minimumFractionDigits: d, maximumFractionDigits: d });
/** Kwota z walutą: „4 890,77 PLN”. */
export const money = (x, code) => `${nf(decimals(code)).format(x)} ${code}`;
/** Wartość do pola edycji (bez spacji tysięcy, z przecinkiem). */
export const inputValue = (x, code) => (x == null || !Number.isFinite(x) ? '' : roundTo(x, decimals(code)).toFixed(decimals(code)).replace('.', ','));

/** Waluty konta: PLN, potem te, które system trzyma (od największego udziału), potem reszta alfabetycznie. */
export function walletCurrencies(state) {
  const w = state?.today?.weights || {};
  const codes = Object.keys(w).length ? Object.keys(w) : Object.keys(state?.last_px || {});
  const rest = codes.filter((c) => c !== 'PLN');
  const held = rest.filter((c) => (w[c] || 0) > 1e-9).sort((a, b) => w[b] - w[a]);
  const other = rest.filter((c) => !held.includes(c)).sort();
  return [...(codes.includes('PLN') ? ['PLN'] : []), ...held, ...other];
}

/**
 * Moje salda wobec systemu. System = dzisiejsze udziały portfela REV (te same jednostki co system →
 * między wtorkami udziały zmieniają się tak samo jak u systemu, więc raz wyrównane konto zostaje zgodne).
 * diff > 0: dokup (zł), diff < 0: sprzedaj.
 */
export function walletRows(state, balances = {}) {
  const px = state?.last_px || {}, w = state?.today?.weights || {};
  const codes = walletCurrencies(state);
  const base = codes.map((code) => {
    const have = Number(balances[code]) || 0, p = px[code];
    return { code, have, px: p ?? null, value: p ? have * p : null };
  });
  const total = base.reduce((a, r) => a + (r.value || 0), 0);
  const rows = base.map((r) => {
    const sysPct = (w[r.code] || 0) * 100;
    const target = total * (w[r.code] || 0);
    const diff = r.px ? target - r.value : 0;
    return { ...r, myPct: total > 0 && r.value != null ? (r.value / total) * 100 : 0, sysPct, target, diff, diffUnits: r.px ? diff / r.px : 0 };
  });
  const match = total > 0 ? 100 - rows.reduce((a, r) => a + Math.abs(r.myPct - r.sysPct), 0) / 2 : null;
  return { rows, total, match };
}

/** Próg, poniżej którego różnicy nie wyrównujemy (opłata byłaby większa niż pożytek): 0,1% konta, najmniej 1 zł. */
export const minConversionPln = (total) => Math.max(1, total * 0.001);

/**
 * Najmniej przewalutowań, które wyrównują konto do systemu: nadwyżki (od największej) łączone z brakami (od największego).
 * Zwraca [{ from, to, pln, fromAmt, toAmt }] — fromAmt nigdy większe niż saldo.
 */
export function planConversions(view, minPln = minConversionPln(view.total)) {
  const byCode = Object.fromEntries(view.rows.map((r) => [r.code, r]));
  const sur = view.rows.filter((r) => r.px && r.diff < 0).map((r) => ({ code: r.code, left: -r.diff })).sort((a, b) => b.left - a.left);
  const def = view.rows.filter((r) => r.px && r.diff > 0).map((r) => ({ code: r.code, left: r.diff })).sort((a, b) => b.left - a.left);
  const out = [];
  let i = 0, j = 0;
  while (i < sur.length && j < def.length) {
    const amt = Math.min(sur[i].left, def[j].left);
    out.push({ from: sur[i].code, to: def[j].code, pln: amt });
    sur[i].left -= amt; def[j].left -= amt;
    if (sur[i].left <= 1e-9) i++;
    if (def[j].left <= 1e-9) j++;
  }
  return out.filter((c) => c.pln >= minPln).map((c) => {
    const f = byCode[c.from], t = byCode[c.to];
    const fromAmt = Math.min(roundTo(c.pln / f.px, decimals(c.from)), f.have);
    return { ...c, fromAmt, toAmt: roundTo(c.pln / t.px, decimals(c.to)) };
  });
}

/** Salda po transakcji (sign = −1 cofa transakcję). */
export function applyTx(balances, tx, sign = 1) {
  const b = { ...balances };
  const add = (c, x) => { b[c] = r6((Number(b[c]) || 0) + x); };
  add(tx.from, -sign * tx.fromAmt);
  if (tx.fee) add(tx.feeCur || tx.from, -sign * tx.fee);
  add(tx.to, sign * tx.toAmt);
  return b;
}

/** „1 CHF = 4,8412 PLN” — w kierunku, w którym liczba jest ≥ 1. */
export function fmtRate(from, to, rate) {
  if (!(rate > 0) || !Number.isFinite(rate)) return '—';
  return rate >= 1 ? `1 ${from} = ${nf(4).format(rate)} ${to}` : `1 ${to} = ${nf(4).format(1 / rate)} ${from}`;
}

/**
 * Sprawdzenie transakcji przed zapisem: błędy (blokują), uwagi, kurs, kurs rynkowy z zamknięcia,
 * koszt wobec rynku w zł (różnica kursu + opłata) i salda przed → po.
 */
export function checkTx(tx, balances, px) {
  const errors = [], warnings = [];
  const fee = tx.fee || 0, feeCur = tx.feeCur || tx.from;
  if (!tx.from || !tx.to) errors.push('Wybierz obie waluty.');
  else if (tx.from === tx.to) errors.push('Waluta sprzedawana i kupowana muszą być różne.');
  if (!(tx.fromAmt > 0)) errors.push('Wpisz, ile sprzedajesz.');
  if (!(tx.toAmt > 0)) errors.push('Wpisz, ile dostajesz (kwotę, która wpadła na konto).');
  if (!(fee >= 0) || !Number.isFinite(fee)) errors.push('Opłata musi być liczbą ≥ 0.');
  const have = (c) => Number(balances?.[c]) || 0;
  const spend = { [tx.from]: tx.fromAmt || 0 };
  if (fee > 0) spend[feeCur] = (spend[feeCur] || 0) + fee;
  for (const [c, x] of Object.entries(spend)) {
    if (c && x > have(c) + 0.005) errors.push(`Na koncie masz ${money(have(c), c)}, a ta transakcja zabiera ${money(x, c)}. Popraw kwotę albo stan konta wyżej.`);
  }
  const rate = tx.fromAmt > 0 && tx.toAmt > 0 ? tx.toAmt / tx.fromAmt : null;
  const pf = px?.[tx.from], pt = px?.[tx.to], pfee = px?.[feeCur];
  const mktRate = pf && pt ? pf / pt : null;
  const costPln = rate && pf && pt ? tx.fromAmt * pf - tx.toAmt * pt + (fee && pfee ? fee * pfee : 0) : null;
  const costPct = costPln != null && tx.fromAmt * pf > 0 ? (costPln / (tx.fromAmt * pf)) * 100 : null;
  if (rate && mktRate && Math.abs(rate / mktRate - 1) > 0.03) warnings.push(`Kurs różni się od rynkowego o ${nf(1).format(Math.abs(rate / mktRate - 1) * 100)}% — sprawdź, czy kwoty i waluty są dobre.`);
  const after = errors.length ? null : applyTx(balances, { ...tx, fee, feeCur });
  const changed = [...new Set([tx.from, tx.to, feeCur].filter(Boolean))];
  return { ok: !errors.length, errors, warnings, rate, mktRate, costPln, costPct, changed, after };
}

const n2 = (x, d) => (x == null ? '' : Number(x).toFixed(d));
export function walletCSV(tx) {
  const head = 'data;sprzedane;waluta;otrzymane;waluta;oplata;waluta_oplaty;kurs;kurs_rynkowy;koszt_zl';
  const rows = [...(tx || [])].sort((a, b) => a.at - b.at).map((t) => {
    const rate = t.toAmt / t.fromAmt, mkt = t.mkt?.[t.from] && t.mkt?.[t.to] ? t.mkt[t.from] / t.mkt[t.to] : null;
    return [fmtWarsaw(t.at), n2(t.fromAmt, decimals(t.from)), t.from, n2(t.toAmt, decimals(t.to)), t.to, n2(t.fee || 0, 2), t.feeCur || t.from,
      n2(rate, 6), n2(mkt, 6), n2(t.costPln, 2)].join(';');
  });
  return [head, ...rows].join('\n') + '\n';
}

/** Pusty / uszkodzony zapis konta → poprawny kształt { balances, tx }. */
export function normWallet(w) {
  const balances = {};
  for (const [k, v] of Object.entries(w?.balances || {})) if (/^[A-Z]{3}$/.test(k) && Number.isFinite(Number(v))) balances[k] = Number(v);
  const tx = (Array.isArray(w?.tx) ? w.tx : []).filter((t) => t && t.from && t.to && t.fromAmt > 0 && t.toAmt > 0 && t.at);
  return { balances, tx, updatedAt: w?.updatedAt || 0 };
}
