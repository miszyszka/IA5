// REV (D-063): czyste funkcje zakładki (bez DOM) — testowane w Node (tests/web/rev.test.mjs).
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

/** Gdzie jest kapitał dziś: koszyki z wartością > 0, malejąco; suma pct = 100. */
export function allocation(state, blocs = state?.blocs || {}) {
  const vals = state?.today?.values || {};
  const total = Object.values(vals).reduce((a, b) => a + b, 0);
  return Object.entries(vals).filter(([, v]) => v > 0.005)
    .map(([code, value]) => ({ code, label: basketLabel(code, blocs), value, pct: total > 0 ? (value / total) * 100 : 0 }))
    .sort((a, b) => b.value - a.value);
}

/** Ranking dziś: ocena metody, przecena (5 lat), trend (3 mies.), cel i udział teraz. */
export function rankingRows(state, blocs = state?.blocs || {}) {
  const t = state?.today || {};
  const codes = Object.keys(t.targets || t.values || {});
  return codes.map((code) => ({
    code, label: basketLabel(code, blocs), score: t.scores?.[code] ?? null, value: t.value_score?.[code] ?? null,
    trend: t.trend_score?.[code] ?? null, target: (t.targets?.[code] ?? 0) * 100, now: (t.weights?.[code] ?? 0) * 100,
  })).map((r) => ({ ...r, change: r.target - r.now }))
    .sort((a, b) => b.target - a.target || (b.score ?? -1e9) - (a.score ?? -1e9));
}

const n = (x, d) => (x == null ? '' : Number(x).toFixed(d));

export function ledgerCSV(state) {
  const head = 'data;koszyk;jednostki_przed;jednostki_po;kurs_pln;wartosc_zl;dzien_ceny';
  const rows = (state?.ledger || []).map((r) => [fmtWarsaw(r.ts), r.basket, n(r.units_before, 6), n(r.units_after, 6), n(r.price, 6), n(r.value_pln, 2), r.price_day || ''].join(';'));
  return [head, ...rows].join('\n') + '\n';
}

export function variantLabel(research, id) {
  return (research?.variants || []).find((v) => v.id === id)?.label || id;
}

export const VERDICT_ICON = { green: '🟢', yellow: '🟡', red: '🔴' };

export function verdictBadge(research) {
  const v = research?.verdict;
  if (!v) return { color: 'mute', text: '—' };
  return { color: v.color, text: `${VERDICT_ICON[v.color] || ''} ${v.passed}/${v.of}` };
}

/** Wynik od startu: kapitał, zmiana w zł i %, równy podział. */
export function liveSummary(state) {
  const c0 = state?.capital0 ?? 10000;
  const tot = state?.today?.total ?? c0;
  const eq = state?.today?.equal_total ?? c0;
  return { total: tot, change: tot - c0, pct: (tot / c0 - 1) * 100, equal: eq, equalPct: (eq / c0 - 1) * 100 };
}

/** Przewalutowania pogrupowane po wtorku (od najnowszego). */
export function ledgerByDecision(state) {
  const by = new Map();
  for (const r of state?.ledger || []) {
    if (!by.has(r.ts)) by.set(r.ts, []);
    by.get(r.ts).push(r);
  }
  return [...by.entries()].sort((a, b) => b[0] - a[0]).map(([ts, rows]) => ({ ts, rows: rows.sort((a, b) => a.value_pln - b.value_pln) }));
}
