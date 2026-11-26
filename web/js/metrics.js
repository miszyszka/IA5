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

// D-075: cel zmienności — te same stałe co runner/ia5/portfolio.py
const VOL_WINDOW_DAYS = 60, VOL_MIN_DAYS = 20, VOL_SCALE = [0.25, 2.0];

/** Skala stawki z celu zmienności (jak portfolio.vol_scale): zmienność dziennych zmian kapitału z 60 dni przed dniem wejścia. */
export function volScale(days, eqs, now, targetPct) {
  if (!days.length) return 1;
  const today = Math.floor(now / DAY), first = days[0];
  if (today - first < VOL_MIN_DAYS) return 1;
  const lo = Math.max(first, today - VOL_WINDOW_DAYS);
  let j = 0;
  { let a = 0, b = days.length; while (a < b) { const mid = (a + b) >> 1; if (days[mid] <= lo - 1) a = mid + 1; else b = mid; } j = a; }
  let last = j > 0 ? eqs[j - 1] : null;
  const vals = [];
  for (let dd = lo - 1; dd < today; dd++) {
    while (j < days.length && days[j] <= dd) { last = eqs[j]; j++; }
    if (last != null) vals.push(last);
  }
  if (vals.length < 3) return 1;
  const r = [];
  for (let i = 1; i < vals.length; i++) r.push(vals[i] / vals[i - 1] - 1);
  if (r.length < 2) return 1;
  const mean = r.reduce((a, b) => a + b, 0) / r.length;
  const sd = Math.sqrt(r.reduce((a, b) => a + (b - mean) ** 2, 0) / (r.length - 1));
  if (!(sd > 0)) return 1;
  return Math.min(VOL_SCALE[1], Math.max(VOL_SCALE[0], targetPct / 100 / (sd * Math.sqrt(365))));
}

/** Zasady portfela strategii z manifestu (D-075). */
export function rulesFrom(manifest) {
  const r = manifest?.rules || {};
  return { sizingMode: r.sizing_mode || 'margin', volTarget: r.vol_target ?? null, maxCcy: r.max_ccy ?? null, brake: r.brake ?? null };
}

/** Depozyt = pct% kapitału przy wejściu, nominał = dźwignia × depozyt, suma depozytów ≤ kapitał (B4).
 *  rules (D-075, jak portfolio.simulate_equity): sizingMode 'risk' (pct = % kapitału ryzykowany do SL), volTarget (% rocznie),
 *  maxCcy (limit pozycji na walutę), brake [spadek %, dni]. */
export function simulateEquity(trades, pct, capital = START_CAPITAL, leverage = LEVERAGE, rules = null) {
  const R = rules || {};
  const mode = R.sizingMode || 'margin', vt = R.volTarget, mcc = R.maxCcy, brake = R.brake;
  if (!trades.length) return { ts: [], equity: [], taken: 0, skipped: 0, final: capital, skippedCcy: 0, skippedBrake: 0, capped: 0 };
  const ev = [];
  trades.forEach((t, k) => { ev.push([t.entry_ts, 1, k]); ev.push([t.exit_ts, 0, k]); });
  ev.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  let eq = capital, used = 0, skipped = 0, skippedCcy = 0, skippedBrake = 0, capped = 0;
  const open = new Map();
  const ts = [Math.min(...trades.map((t) => t.entry_ts))], equity = [capital];
  let peak = capital, worst = 0; // D-055: obsunięcie z otwartymi pozycjami w ich najgorszym punkcie (MAE)
  const maeRet = (t) => ((t.mae || 0) * PAIRS[t.pair].pip) / t.entry_px;
  const expo = new Map();
  let pauseUntil = -1, brakePeak = capital;
  const eqDays = [], eqVals = [];
  for (const [time, kind, k] of ev) {
    const t = trades[k];
    if (kind === 1) {
      if (brake && time < pauseUntil) { skippedBrake++; continue; }
      const scale = vt ? volScale(eqDays, eqVals, time, +vt) : 1;
      const w = t.weight ?? 1;
      let m;
      if (mode === 'risk') {
        const rr = (t.risk_pips * PAIRS[t.pair].pip) / t.entry_px;
        m = rr > 0 ? (((eq * pct) / 100) * w * scale) / rr / leverage : ((eq * pct) / 100) * w * scale;
      } else m = ((eq * pct) / 100) * w * scale; // D-034: waga pozycji mnoży depozyt
      let b, q, sgn;
      if (mcc) {
        b = t.pair.slice(0, 3); q = t.pair.slice(3); sgn = (t.dir ?? 1) * w;
        if (Math.abs((expo.get(b) || 0) + sgn) > mcc + 1e-9 || Math.abs((expo.get(q) || 0) - sgn) > mcc + 1e-9) { skippedCcy++; continue; }
      }
      if (eq <= 0) { skipped++; continue; }
      if (used + m > eq + 1e-9) {
        if (mode === 'risk' && eq - used > 1e-9) { m = eq - used; capped++; } else { skipped++; continue; }
      }
      open.set(k, m); used += m;
      if (mcc) { expo.set(b, (expo.get(b) || 0) + sgn); expo.set(q, (expo.get(q) || 0) - sgn); }
    } else if (open.has(k)) {
      const m = open.get(k); open.delete(k); used -= m;
      eq += m * leverage * tradeReturn(t);
      ts.push(time); equity.push(eq);
      if (mcc) {
        const b = t.pair.slice(0, 3), q = t.pair.slice(3), sgn = (t.dir ?? 1) * (t.weight ?? 1);
        expo.set(b, (expo.get(b) || 0) - sgn); expo.set(q, (expo.get(q) || 0) + sgn);
      }
      if (vt) {
        const dday = Math.floor(time / DAY);
        if (eqDays.length && eqDays[eqDays.length - 1] === dday) eqVals[eqVals.length - 1] = eq;
        else {
          if (!eqDays.length) { eqDays.push(dday - 1); eqVals.push(capital); }
          eqDays.push(dday); eqVals.push(eq);
        }
      }
      if (brake) {
        brakePeak = Math.max(brakePeak, eq);
        if (brakePeak > 0 && ((brakePeak - eq) / brakePeak) * 100 >= +brake[0] - 1e-12) {
          pauseUntil = time + Math.round(+brake[1] * DAY); brakePeak = eq;
        }
      }
    }
    peak = Math.max(peak, eq);
    let floor = eq;
    for (const [j, mm] of open) floor -= mm * leverage * maeRet(trades[j]);
    if (peak > 0) worst = Math.min(worst, (floor - peak) / peak);
  }
  return { ts, equity, taken: trades.length - skipped - skippedCcy - skippedBrake, skipped, final: eq, maxDdMae: worst,
    skippedCcy, skippedBrake, capped };
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
  const maxDdMae = Math.min((curve.maxDdMae ?? 0) * 100, maxDd); // D-055: nigdy łagodniejsze niż zrealizowane
  return {
    final, returnPct: (final / capital - 1) * 100, cagrPct: cagr * 100, maxDdPct: maxDd, maxDdMaePct: maxDdMae,
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

// ---------- wirtualni inwestorzy (D-045) ----------

export const INVESTOR_STALE_S = 2 * 3600 + 900;   // liczenie co godzinę po kopii świec — po ponad 2 h coś stoi

/**
 * Stan inwestora do wskaźnika „INWESTOR DZIAŁA”.
 * doc — dokument Firestore, st — stan z gałęzi data (investors/{id}/state.json albo wpis indeksu), mac — {online, state, job}.
 * Zwraca { state: ok|warn|bad|mute, word, detail }.
 */
export function investorStatus(doc, st, mac, now = Date.now() / 1000) {
  if (doc?.status === 'do_usuniecia') return { state: 'mute', word: 'USUWANIE', detail: 'Mac usunie inwestora przy najbliższym przebiegu.' };
  const busy = mac?.online && mac.state === 'computing' && mac.job?.name?.startsWith('Inwestor');
  if (!st) {
    return { state: 'warn', word: 'URUCHAMIANIE', detail: busy ? 'Trwa liczenie inwestorów…' : 'Pierwsze liczenie w chmurze nastąpi w ciągu godziny.' };
  }
  const errs = (st.strategies || []).filter((s) => s.error).length + (st.errors || 0);
  const all = (st.strategies || []).length;
  if (all && errs >= all) return { state: 'bad', word: 'BŁĄD', detail: 'Żadna strategia inwestora nie daje się policzyć — szczegóły przy strategiach.' };
  if (now - (st.computedAt || 0) > INVESTOR_STALE_S) {
    return { state: 'warn', word: 'OPÓŹNIONY', detail: 'Ostatnie liczenie ponad 2 h temu.' };
  }
  return { state: 'ok', word: 'INWESTOR DZIAŁA', detail: errs ? `Uwaga: ${errs} z ${all} strategii z błędem.` : 'Liczony po każdej nowej świecy, także bez Maca.' };
}

/** Lista inwestorów = dokumenty Firestore (źródło prawdy o istnieniu) + stan z gałęzi data. */
export function mergeInvestors(docs, indexEntries) {
  const idx = new Map((indexEntries || []).map((e) => [e.id, e]));
  return Object.entries(docs || {})
    .filter(([, d]) => d.status !== 'do_usuniecia')
    .map(([id, d]) => ({ id, doc: d, st: idx.get(id) || null }))
    .sort((a, b) => (b.doc.createdAt || 0) - (a.doc.createdAt || 0));
}

/** Kontrola formularza nowego inwestora (te same granice co reguły Firestore). */
export function validateInvestor({ name, capital, pct, strategies }) {
  const errors = [];
  if (!name || !name.trim()) errors.push('Podaj nazwę inwestora.');
  else if (name.trim().length > 80) errors.push('Nazwa może mieć najwyżej 80 znaków.');
  if (!(capital >= 100 && capital <= 1e8)) errors.push('Kapitał początkowy: od 100 do 100 000 000 USD.');
  if (!(pct > 0 && pct <= 100)) errors.push('Depozyt na wejście: więcej niż 0% i najwyżej 100% kapitału.');
  if (!strategies?.length) errors.push('Wybierz co najmniej jedną strategię.');
  if (strategies?.length > 10) errors.push('Najwyżej 10 strategii na inwestora.');
  if (strategies?.some((s) => !s.code)) errors.push('Nie udało się wczytać kodu którejś strategii — spróbuj ponownie.');
  return errors;
}

/** Transakcje inwestora chronologicznie (po czasie wejścia), z numerem i nazwą strategii. */
export function investorTrades(st) {
  const names = (st?.strategies || []).map((s) => s.name);
  return (st?.trades || []).slice().sort((a, b) => a.entry_ts - b.entry_ts || a.strategy - b.strategy)
    .map((t, i) => ({ ...t, n: i + 1, strategyName: names[t.strategy] ?? `#${t.strategy + 1}` }));
}

const paramsLabel = (p) => (p && Object.keys(p).length ? Object.entries(p).map(([k, v]) => `${k}=${v}`).join(', ') : 'bez parametrów');

/** Warianty do wyboru: zamrożony (jeśli jest), potem 10 najlepszych w IS. Domyślny = zamrożony albo #1 IS. */
export function variantChoices(variants, frozenId = null) {
  const ranked = (variants || []).filter((v) => v.rank_is != null).sort((a, b) => a.rank_is - b.rank_is);
  const top = ranked.slice(0, 10);
  const frozen = frozenId != null ? (variants || []).find((v) => v.variant_id === frozenId) : null;
  const list = frozen ? [frozen, ...top.filter((v) => v.variant_id !== frozen.variant_id)] : top;
  return list.map((v) => ({
    id: v.variant_id, frozen: frozen?.variant_id === v.variant_id,
    label: `${frozen?.variant_id === v.variant_id ? '❄ zamrożony · ' : ''}#${v.rank_is ?? '—'} IS · ${v.exit} · ${paramsLabel(v.params)}`
      + ` · OOS ${v.oos_exp_pips == null ? '—' : `${v.oos_exp_pips > 0 ? '+' : ''}${v.oos_exp_pips.toFixed(1)} pips`}`,
  }));
}
