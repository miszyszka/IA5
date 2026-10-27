// Czyste obliczenia dashboardu (bez DOM) — testowane w Node (tests/test_web_metrics.py).
// Symulacja kapitału = ta sama logika co runner/ia5/portfolio.py (zmiany w obu miejscach).

export const LEVERAGE = 30; // B4, D-024: zawsze 30:1
export const START_CAPITAL = 10000;
export const SIZING = [5, 10, 15, 20, 30];

export const PAIRS = {
  EURUSD: { pip: 0.0001, spread: 0.9, label: 'EUR/USD' },
  USDJPY: { pip: 0.01, spread: 1.4, label: 'USD/JPY' },
  GBPUSD: { pip: 0.0001, spread: 1.5, label: 'GBP/USD' },
  EURGBP: { pip: 0.0001, spread: 1.7, label: 'EUR/GBP' },
  AUDUSD: { pip: 0.0001, spread: 1.7, label: 'AUD/USD' },
  USDCHF: { pip: 0.0001, spread: 1.9, label: 'USD/CHF' },
  USDCAD: { pip: 0.0001, spread: 2.0, label: 'USD/CAD' },
  EURJPY: { pip: 0.01, spread: 2.1, label: 'EUR/JPY' },
};

const DAY = 86400;

export function sessionOf(ts) {
  const h = new Date(ts * 1000).getUTCHours();
  return h < 7 ? 'Azja' : h < 13 ? 'Europa' : h < 21 ? 'USA' : 'poza sesją';
}
export const WEEKDAYS = ['nd', 'pn', 'wt', 'śr', 'cz', 'pt', 'sb'];
export const weekdayOf = (ts) => WEEKDAYS[new Date(ts * 1000).getUTCDay()];
export const yearOf = (ts) => new Date(ts * 1000).getUTCFullYear();

/** Filtry karty: pary (Set), kierunek ('all'|'long'|'short'), próba ('all'|'IS'|'OOS'), od daty (forward). */
export function filterTrades(trades, { pairs = null, dir = 'all', sample = 'all', from = null } = {}) {
  return trades.filter((t) =>
    (!pairs || pairs.has(t.pair)) &&
    (dir === 'all' || (dir === 'long' ? t.dir > 0 : t.dir < 0)) &&
    (sample === 'all' || t.sample === sample) &&
    (from == null || t.entry_ts >= from));
}

export function tradeReturn(t) {
  return (t.pips_net * PAIRS[t.pair].pip) / t.entry_px;
}

/** Depozyt = pct% kapitału przy wejściu, nominał = dźwignia × depozyt, suma depozytów ≤ kapitał (B4). */
export function simulateEquity(trades, pct, capital = START_CAPITAL, leverage = LEVERAGE) {
  if (!trades.length) return { ts: [], equity: [], taken: 0, skipped: 0, final: capital };
  const ev = [];
  trades.forEach((t, k) => { ev.push([t.entry_ts, 1, k]); ev.push([t.exit_ts, 0, k]); });
  ev.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  let eq = capital, used = 0, skipped = 0;
  const open = new Map();
  const ts = [Math.min(...trades.map((t) => t.entry_ts))], equity = [capital];
  for (const [time, kind, k] of ev) {
    if (kind === 1) {
      const m = ((eq * pct) / 100) * (trades[k].weight ?? 1); // D-034: waga pozycji mnoży depozyt
      if (used + m > eq + 1e-9 || eq <= 0) { skipped++; continue; }
      open.set(k, m); used += m;
    } else if (open.has(k)) {
      const m = open.get(k); open.delete(k); used -= m;
      eq += m * leverage * tradeReturn(trades[k]);
      ts.push(time); equity.push(eq);
    }
  }
  return { ts, equity, taken: trades.length - skipped, skipped, final: eq };
}

export function drawdown(equity) {
  let peak = -Infinity;
  return equity.map((e) => { peak = Math.max(peak, e); return ((e - peak) / peak) * 100; });
}

export function equityStats(curve, capital = START_CAPITAL) {
  const { ts, equity } = curve;
  if (equity.length < 2) return null;
  const dd = drawdown(equity);
  const years = Math.max((ts[ts.length - 1] - ts[0]) / (365.25 * DAY), 1e-9);
  const final = equity[equity.length - 1];
  const cagr = final > 0 ? Math.pow(final / capital, 1 / years) - 1 : -1;
  const maxDd = Math.min(...dd);
  // Sharpe z dziennych zwrotów (ostatnia wartość dnia, przeniesiona na dni bez zmian)
  const daily = [];
  let day = Math.floor(ts[0] / DAY), last = equity[0], k = 0;
  const endDay = Math.floor(ts[ts.length - 1] / DAY);
  for (let d = day; d <= endDay; d++) {
    while (k < ts.length && Math.floor(ts[k] / DAY) <= d) { last = equity[k]; k++; }
    daily.push(last);
  }
  const r = [];
  for (let i = 1; i < daily.length; i++) r.push(daily[i] / daily[i - 1] - 1);
  const mean = r.reduce((a, b) => a + b, 0) / (r.length || 1);
  const sd = Math.sqrt(r.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(r.length - 1, 1));
  return {
    final, returnPct: (final / capital - 1) * 100, cagrPct: cagr * 100, maxDdPct: maxDd,
    sharpe: r.length > 2 && sd > 0 ? (mean / sd) * Math.sqrt(252) : null,
    calmar: maxDd < 0 ? (cagr * 100) / -maxDd : null,
  };
}

export function summarize(trades) {
  const n = trades.length;
  if (!n) return { trades: 0 };
  let win = 0, gw = 0, gl = 0, sp = 0, sr = 0, rn = 0;
  for (const t of trades) {
    if (t.pips_net > 0) { win++; gw += t.pips_net; } else gl -= t.pips_net;
    sp += t.pips_net;
    if (Number.isFinite(t.r_net)) { sr += t.r_net; rn++; }
  }
  return { trades: n, winRate: win / n, expPips: sp / n, expR: rn ? sr / rn : null, sumPips: sp, pf: gl > 0 ? gw / gl : null };
}

export function breakdown(trades, keyFn) {
  const groups = new Map();
  for (const t of trades) {
    const k = keyFn(t);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(t);
  }
  return [...groups.entries()].map(([key, g]) => ({ key, ...summarize(g) }));
}

export function toCSV(rows, cols) {
  const esc = (v) => (v == null ? '' : /[",;\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  return [cols.join(';'), ...rows.map((r) => cols.map((c) => esc(r[c])).join(';'))].join('\n');
}

/**
 * Lista strategii = wyniki z gałęzi data (index.json) + dokumenty Firestore (kolejka, błędy, usuwanie).
 * Strategia oznaczona do usunięcia znika od razu, zanim Mac posprząta pliki.
 */
export function mergeStrategies(indexEntries, docs, hidden = new Set()) {
  const byId = new Map();
  for (const e of indexEntries || []) byId.set(e.id, { id: e.id, name: e.name, result: e, doc: null });
  for (const [id, d] of Object.entries(docs || {})) {
    const cur = byId.get(id) || { id, name: d.name, result: null, doc: null };
    cur.doc = d;
    if (d.name) cur.name = d.name;
    byId.set(id, cur);
  }
  const out = [];
  for (const s of byId.values()) {
    if (hidden.has(s.id) || s.doc?.status === 'do_usuniecia') continue;
    const st = s.doc?.status;
    s.state = st === 'do_policzenia' ? 'queued' : st === 'liczy_sie' ? 'running' : st === 'blad' ? 'error'
      : s.result ? 'done' : st === 'policzona' ? 'publishing' : 'queued';
    s.created = s.result?.created ?? s.doc?.createdAt ?? 0;
    out.push(s);
  }
  return out.sort((a, b) => (b.created || 0) - (a.created || 0));
}

const ALLOWED = new Set(['numpy', 'pandas', 'math']);

/** Szybka kontrola kodu w przeglądarce. Pełna (look-ahead, sygnały) robi `ia5` na Macu. */
export function checkStrategyCode(code) {
  const errors = [], warnings = [];
  if (!/^def\s+signals\s*\(\s*df\s*,\s*p\s*,\s*ind\s*\)\s*:/m.test(code)) errors.push('Brak funkcji signals(df, p, ind) na początku linii.');
  for (const m of code.matchAll(/^\s*(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import)/gm)) {
    const mod = (m[1] || m[2]).split('.')[0];
    if (!ALLOWED.has(mod)) errors.push(`Niedozwolony import „${mod}” (dozwolone: numpy, pandas, math).`);
  }
  for (const f of ['open(', 'exec(', 'eval(', '__import__', 'compile(']) {
    if (code.includes(f)) errors.push(`Niedozwolone: ${f.replace('(', '')}.`);
  }
  if (/shift\(\s*-\s*\d/.test(code)) errors.push('shift(-N) patrzy w przyszłość (look-ahead, B2).');
  if (/center\s*=\s*True/.test(code)) errors.push('rolling(..., center=True) używa przyszłych świec (look-ahead, B2).');
  if (!/^HYPOTHESIS\s*=/m.test(code)) warnings.push('Brak HYPOTHESIS — spisz, dlaczego strategia ma działać, zanim zobaczysz wynik.');
  if (/\.(mean|std|max|min|quantile)\(\)/.test(code) && !/rolling|groupby|expanding/.test(code)) {
    warnings.push('Statystyka z całej serii (np. df.close.mean()) zna przyszłość — użyj rolling(...).');
  }
  return { errors, warnings };
}
