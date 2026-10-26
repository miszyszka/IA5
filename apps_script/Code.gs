/**
 * IA5 — pobieranie świec H1 z Yahoo do Firestore (CLAUDE.md, sekcja 5).
 * Uruchom raz: setup()  (backfill 730 dni + wyzwalacz co 5 min).
 * Źródło prawdy tego pliku: repo miszyszka/IA5, katalog apps_script/.
 *
 * Budżet Firestore (Z4): ok. 8 zapisów świec + 1 zapis statusu na godzinę ≈ 220 zapisów/dobę, 0 odczytów.
 */
const PROJECT_ID = 'project-ia5';
const DB = 'projects/' + PROJECT_ID + '/databases/(default)';
const API = 'https://firestore.googleapis.com/v1/' + DB;
const H = 3600;

const PAIRS = [
  { name: 'EURUSD', yahoo: 'EURUSD=X', pip: 0.0001 },
  { name: 'USDJPY', yahoo: 'JPY=X', pip: 0.01 },
  { name: 'GBPUSD', yahoo: 'GBPUSD=X', pip: 0.0001 },
  { name: 'EURGBP', yahoo: 'EURGBP=X', pip: 0.0001 },
  { name: 'AUDUSD', yahoo: 'AUDUSD=X', pip: 0.0001 },
  { name: 'USDCHF', yahoo: 'CHF=X', pip: 0.0001 },
  { name: 'USDCAD', yahoo: 'CAD=X', pip: 0.0001 },
  { name: 'EURJPY', yahoo: 'EURJPY=X', pip: 0.01 },
];

// ---------- punkty wejścia ----------

function setup() {
  backfill();
  installTrigger();
}

function backfill() { withLock_(() => run_('backfill')); }

function tick() { withLock_(() => run_('tick')); }

function installTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'tick')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('tick').timeBased().everyMinutes(5).create();
}

function healthcheck() {
  Logger.log('Stan: ' + JSON.stringify(loadState_()));
  Logger.log('Oczekiwana ostatnia świeca: ' + new Date(expectedTs(nowSec()) * 1000).toISOString());
  const bars = fetchYahoo('EURUSD=X', 'range=1d');
  Logger.log('Yahoo EURUSD, ostatnia doba: ' + bars.length + ' świec, ostatnia ' +
    (bars.length ? new Date(bars[bars.length - 1].ts * 1000).toISOString() : '—'));
}

// ---------- czas i sesja FX (czyste funkcje, ta sama logika w web/status.js) ----------

function nowSec() { return Math.floor(Date.now() / 1000); }

/** Najnowsza świeca, która jest już zamknięta (D2): ts + 3600 <= teraz - 60. */
function lastClosedTs(now) { return Math.floor((now - 60 - H) / H) * H; }

/** Czy świeca otwarta o ts musi istnieć. Okno zamknięcia szerokie, żeby objąć czas letni i zimowy. */
function isExpectedBar(ts) {
  const d = new Date(ts * 1000);
  const day = d.getUTCDay();
  const hr = d.getUTCHours();
  if (day === 6) return false;              // sobota
  if (day === 5 && hr >= 21) return false;  // piątek wieczór
  if (day === 0 && hr < 22) return false;   // niedziela przed otwarciem
  return true;
}

/** Najnowsza świeca, której oczekujemy w bazie. */
function expectedTs(now) {
  let ts = lastClosedTs(now);
  for (let i = 0; i < 80 && !isExpectedBar(ts); i++) ts -= H;
  return ts;
}

function monthKey(ts) {
  const d = new Date(ts * 1000);
  return d.getUTCFullYear() + '-' + String(d.getUTCMonth() + 1).padStart(2, '0');
}

/** Kontrola jakości pojedynczej świecy (D5). Zwraca listę naruszeń, nic nie naprawia. */
function barFlags(b) {
  const f = [];
  if (b.ts % H !== 0) f.push('ts');
  if (!(b.o > 0 && b.h > 0 && b.l > 0 && b.c > 0)) f.push('cena<=0');
  if (b.h < Math.max(b.o, b.c) || b.l > Math.min(b.o, b.c)) f.push('ohlc');
  return f;
}

// ---------- główna praca ----------

function run_(mode) {
  const startedAt = nowSec();
  const state = loadState_();
  const exp = expectedTs(startedAt);
  const todo = PAIRS.filter(p => mode === 'backfill' ||
    !(state.pairs[p.name] && state.pairs[p.name].lastTs >= exp));
  if (!todo.length) return; // nic nowego — zero zapytań i zapisów

  const updated = {};
  const errors = [];
  let runLatency = null;

  todo.forEach(p => {
    try {
      const params = mode === 'backfill'
        ? 'period1=' + (startedAt - 729 * 86400) + '&period2=' + startedAt
        : 'range=5d';
      const now = nowSec();
      const closed = fetchYahoo(p.yahoo, params).filter(b => b.ts + H <= now - 60);
      const ps = state.pairs[p.name] || { lastTs: 0, count: 0, last: [], latencySec: null };
      const from = mode === 'backfill' || !ps.lastTs ? 0 : ps.lastTs - 3 * H;
      const bars = closed.filter(b => b.ts >= from);
      if (!bars.length) return;

      const flags = [];
      bars.forEach(b => barFlags(b).forEach(f => flags.push(f + '@' + b.ts)));
      (ps.last || []).forEach(old => {
        const nb = bars.find(b => b.ts === old.ts);
        if (nb && Math.abs(nb.c - old.c) > 0.5 * p.pip) flags.push('revised@' + old.ts);
      });
      for (let i = 1; i < bars.length; i++) {
        for (let t = bars[i - 1].ts + H; t < bars[i].ts; t += H) {
          if (isExpectedBar(t)) { flags.push('luka@' + t); break; }
        }
      }

      writeBars_(p.name, bars);
      const writtenAt = nowSec();
      const fresh = bars.filter(b => b.ts > ps.lastTs);
      const newest = bars[bars.length - 1];
      const lat = fresh.length ? writtenAt - (newest.ts + H) : null;

      ps.count = mode === 'backfill' ? bars.length : ps.count + fresh.length;
      ps.lastTs = Math.max(ps.lastTs, newest.ts);
      ps.last = bars.slice(-3);
      ps.flags = flags.slice(-20);
      if (lat !== null) ps.latencySec = lat;
      state.pairs[p.name] = ps;
      updated[p.name] = { lastTs: ps.lastTs, latencySec: ps.latencySec, count: ps.count, flags: ps.flags };
      if (lat !== null && mode === 'tick') runLatency = Math.max(runLatency || 0, lat);
      log_(mode, p.name, fresh.length, lat, flags.slice(0, 5).join(' '));
    } catch (e) {
      errors.push(p.name + ': ' + e.message);
      log_(mode, p.name, 0, null, 'BŁĄD ' + e.message);
    }
  });

  state.latency24h = (state.latency24h || []).filter(x => x.at > startedAt - 86400);
  if (runLatency !== null) state.latency24h.push({ at: startedAt, s: runLatency });
  state.latency24h = state.latency24h.slice(-300);

  const totalBars = PAIRS.reduce((s, p) => s + ((state.pairs[p.name] || {}).count || 0), 0);
  const status = {
    lastRun: { mode: mode, startedAt: startedAt, finishedAt: nowSec(), ok: !errors.length, error: errors.join('; ') || null },
    totalBars: totalBars,
    latency24h: state.latency24h,
    cross: crossCheck_(state),
  };
  writeStatus_(status, updated);
  saveState_(state);
}

/** Test krzyżowy par na ostatniej wspólnej świecy (D5). Zwraca odchyłki w pipsach. */
function crossCheck_(state) {
  const close = (pair, ts) => {
    const b = ((state.pairs[pair] || {}).last || []).find(x => x.ts === ts);
    return b ? b.c : null;
  };
  const ts = Math.min.apply(null, ['EURUSD', 'USDJPY', 'EURJPY', 'GBPUSD', 'EURGBP']
    .map(p => (state.pairs[p] || {}).lastTs || 0));
  const eu = close('EURUSD', ts), uj = close('USDJPY', ts), ej = close('EURJPY', ts);
  const gu = close('GBPUSD', ts), eg = close('EURGBP', ts);
  const out = { ts: ts, eurjpyPips: null, eurgbpPips: null, flags: [] };
  if (eu && uj && ej) {
    out.eurjpyPips = Math.round(Math.abs(ej - eu * uj) / 0.01 * 10) / 10;
    if (out.eurjpyPips > 20) out.flags.push('EURJPY≠EURUSD×USDJPY');
  }
  if (eu && gu && eg) {
    out.eurgbpPips = Math.round(Math.abs(eg - eu / gu) / 0.0001 * 10) / 10;
    if (out.eurgbpPips > 10) out.flags.push('EURGBP≠EURUSD÷GBPUSD');
  }
  return out;
}

// ---------- Yahoo ----------

function fetchYahoo(ticker, params) {
  const url = 'https://query1.finance.yahoo.com/v8/finance/chart/' +
    encodeURIComponent(ticker) + '?interval=1h&' + params;
  let lastErr = '';
  for (let i = 0; i < 3; i++) {
    try {
      const r = UrlFetchApp.fetch(url, { muteHttpExceptions: true, headers: { 'User-Agent': 'Mozilla/5.0' } });
      if (r.getResponseCode() === 200) return parseYahoo(JSON.parse(r.getContentText()));
      lastErr = 'HTTP ' + r.getResponseCode();
    } catch (e) {
      lastErr = e.message;
    }
    if (i < 2) Utilities.sleep(1000 * Math.pow(2, i + 1));
  }
  throw new Error('Yahoo ' + ticker + ': ' + lastErr);
}

function parseYahoo(j) {
  const res = j && j.chart && j.chart.result && j.chart.result[0];
  if (!res || !res.timestamp) return [];
  const q = res.indicators.quote[0];
  const out = [];
  for (let i = 0; i < res.timestamp.length; i++) {
    const o = q.open[i], h = q.high[i], l = q.low[i], c = q.close[i];
    if ([o, h, l, c].some(v => v === null || v === undefined)) continue;
    out.push({ ts: res.timestamp[i], o: o, h: h, l: l, c: c });
  }
  return out;
}

// ---------- Firestore (REST, upsert przez commit z updateMask — D3, bez odczytów) ----------

function writeBars_(pair, bars) {
  const groups = {};
  bars.forEach(b => { const m = monthKey(b.ts); (groups[m] = groups[m] || []).push(b); });
  const writes = Object.keys(groups).map(m => {
    const fields = {};
    const paths = ['pair', 'month'];
    groups[m].forEach(b => {
      fields[String(b.ts)] = { arrayValue: { values: [b.o, b.h, b.l, b.c].map(v => ({ doubleValue: v })) } };
      paths.push('bars.`' + b.ts + '`');
    });
    return {
      update: {
        name: DB + '/documents/candles/' + pair + '_' + m,
        fields: { pair: { stringValue: pair }, month: { stringValue: m }, bars: { mapValue: { fields: fields } } },
      },
      updateMask: { fieldPaths: paths },
      updateTransforms: [{ fieldPath: 'updatedAt', setToServerValue: 'REQUEST_TIME' }],
    };
  });
  commit_(writes);
}

function writeStatus_(status, updatedPairs) {
  const fields = {};
  Object.keys(status).forEach(k => { fields[k] = toValue_(status[k]); });
  fields.pairs = toValue_(updatedPairs);
  const paths = Object.keys(status).concat(Object.keys(updatedPairs).map(p => 'pairs.' + p));
  commit_([{
    update: { name: DB + '/documents/meta/status', fields: fields },
    updateMask: { fieldPaths: paths },
    updateTransforms: [{ fieldPath: 'updatedAt', setToServerValue: 'REQUEST_TIME' }],
  }]);
}

function commit_(writes) {
  for (let i = 0; i < writes.length; i += 400) {
    const r = UrlFetchApp.fetch(API + '/documents:commit', {
      method: 'post',
      contentType: 'application/json',
      headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT_ID },
      payload: JSON.stringify({ writes: writes.slice(i, i + 400) }),
      muteHttpExceptions: true,
    });
    if (r.getResponseCode() !== 200) {
      throw new Error('Firestore ' + r.getResponseCode() + ': ' + r.getContentText().slice(0, 300));
    }
  }
}

function toValue_(v) {
  if (v === null || v === undefined) return { nullValue: null };
  if (Array.isArray(v)) return { arrayValue: { values: v.map(toValue_) } };
  if (typeof v === 'number') return Number.isInteger(v) ? { integerValue: String(v) } : { doubleValue: v };
  if (typeof v === 'boolean') return { booleanValue: v };
  if (typeof v === 'object') {
    const f = {};
    Object.keys(v).forEach(k => { f[k] = toValue_(v[k]); });
    return { mapValue: { fields: f } };
  }
  return { stringValue: String(v) };
}

// ---------- stan, blokada, log ----------

function loadState_() {
  const raw = PropertiesService.getScriptProperties().getProperty('state');
  return raw ? JSON.parse(raw) : { pairs: {}, latency24h: [] };
}

function saveState_(s) {
  PropertiesService.getScriptProperties().setProperty('state', JSON.stringify(s));
}

function withLock_(fn) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(1000)) return;
  try { fn(); } finally { lock.releaseLock(); }
}

function log_(mode, pair, fresh, lat, msg) {
  const ss = SpreadsheetApp.getActive();
  if (!ss) return;
  const sh = ss.getSheetByName('log') || ss.insertSheet('log');
  if (sh.getLastRow() === 0) sh.appendRow(['czas UTC', 'tryb', 'para', 'nowe świece', 'latencja s', 'uwagi']);
  sh.appendRow([new Date().toISOString(), mode, pair, fresh, lat === null ? '' : lat, msg]);
}
