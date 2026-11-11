// Symulacja serii kursów PLN w Apps Script (D-063) w Node — atrapy usług Google i Yahoo (interval=1d).
// Uruchamia tests/test_apps_script.py. Sprawdza: regułę przyjęcia przy backfillPLN(), zapis candles_pln/*,
// meta/status.pln, tickPLN_ tylko dla przyjętych walut, oraz że backfillD1() działa jak dotąd.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const props = {}, writes = [], urls = [];
const DAY = 86400;
let NOW = Date.UTC(2026, 10, 11, 10, 30) / 1000;     // środa 11.11.2026 10:30 UTC

const fmt = new Map();
function stamp(ts, tz) {
  if (!fmt.has(tz)) fmt.set(tz, new Intl.DateTimeFormat('sv-SE', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }));
  return fmt.get(tz).format(new Date(ts * 1000)).replace('T', ' ');
}
function londonMidnight(day) {               // ts, o którym w Londynie jest 00:00 danego dnia
  const t = Date.UTC(+day.slice(0, 4), +day.slice(5, 7) - 1, +day.slice(8, 10)) / 1000;
  return stamp(t, 'Europe/London').slice(11, 13) === '00' ? t : t - 3600;
}
const START = { QARPLN: '2023-11-01', DEFAULT: '2005-01-03' };
function bars(ticker, params) {
  const name = ticker.replace('=X', '');
  const first = name.endsWith('PLN') ? (START[name] || (/^(EUR|USD|CHF)PLN$/.test(name) ? '2003-01-02' : START.DEFAULT)) : '2003-01-02';
  const today = stamp(NOW - 60, 'Europe/London').slice(0, 10);
  let last = today;
  if (name === 'SARPLN') last = new Date((NOW - 20 * DAY) * 1000).toISOString().slice(0, 10);
  const out = [];
  const from = params.includes('range=10d') ? new Date((NOW - 10 * DAY) * 1000).toISOString().slice(0, 10) : first;
  for (let d = new Date(from + 'T12:00:00Z'); ; d = new Date(d.getTime() + DAY * 1000)) {
    const day = d.toISOString().slice(0, 10);
    if (day > today || day > last) break;
    if (day < first || d.getUTCDay() === 0 || d.getUTCDay() === 6) continue;
    const i = Math.round(d.getTime() / 864e5);
    let c = 4 * (1 + 0.05 * Math.sin(i * 0.013) + 0.004 * Math.sin(i * 1.7) + 0.001 * Math.cos(i * 0.91));
    if (name === 'THBPLN' && day >= '2021-01-01') c = 0.11;      // stoi od 5 lat — „dni bez ruchu”
    out.push([londonMidnight(day), c * 0.999, c * 1.003, c * 0.997, c]);
  }
  if (!params.includes('range=10d')) out.push([NOW - 3600, 4, 4, 4, 4]);   // dzień w trakcie — nie może trafić do bazy
  return out;
}
const ctx = {
  console, Math, JSON, Date, Number, String, Object, Array, Error, encodeURIComponent, decodeURIComponent,
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] ?? null, setProperty: (k, v) => { props[k] = v; }, deleteProperty: k => { delete props[k]; } }) },
  UrlFetchApp: { fetch: (url, opt) => {
    if (url.includes('finance/chart')) {
      urls.push(url);
      const tk = decodeURIComponent(url.split('/chart/')[1].split('?')[0]);
      if (/^(AED|HUF|MXN)PLN=X$/.test(tk)) return { getResponseCode: () => 404, getContentText: () => '{"chart":{"error":"Not Found"}}' };
      const b = bars(tk, url.split('?')[1]);
      const body = { chart: { result: [{ meta: { exchangeTimezoneName: 'Europe/London', dataGranularity: '1d' }, timestamp: b.map(x => x[0]),
        indicators: { quote: [{ open: b.map(x => x[1]), high: b.map(x => x[2]), low: b.map(x => x[3]), close: b.map(x => x[4]) }] } }] } };
      return { getResponseCode: () => 200, getContentText: () => JSON.stringify(body) };
    }
    writes.push(JSON.parse(opt.payload)); return { getResponseCode: () => 200, getContentText: () => '{}' };
  } },
  ScriptApp: { getOAuthToken: () => 'tok' },
  Utilities: { sleep: () => {}, formatDate: (d, tz) => stamp(d.getTime() / 1000, tz) },
  SpreadsheetApp: { getActive: () => ({ getSheetByName: () => ({ getLastRow: () => 1, appendRow: () => {} }) }) },
  LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }) },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8') + '\nthis.__ = { backfillPLN, tickPLN_, backfillD1, PLN_CANDIDATES, nowSec };', ctx);
const G = ctx.__;
ctx.Date.now = () => NOW * 1000;   // nowSec() z atrapą zegara

assert.strictEqual(G.PLN_CANDIDATES.length, 24);
assert.ok(!G.PLN_CANDIDATES.some(c => c.name === 'RUB'));
assert.ok(G.PLN_CANDIDATES.every(c => c.yahoo === c.name + 'PLN=X'));

// 1) backfillPLN: przyjęte zapisane, rzadkie odrzucone bez zapisu
G.backfillPLN();
const docs = writes.flatMap(w => w.writes).map(w => w.update.name);
const pln = docs.filter(n => n.includes('/documents/candles_pln/'));
assert.ok(pln.some(n => n.endsWith('/candles_pln/EUR_2003')), 'EUR od 2003');
assert.ok(pln.some(n => n.endsWith('/candles_pln/USD_2026')), 'USD bieżący rok');
['QAR_', 'THB_', 'SAR_', 'AED_', 'HUF_', 'MXN_'].forEach(p => assert.ok(!pln.some(n => n.includes('/candles_pln/' + p)), 'odrzucona ' + p));
const todayLondon = stamp(NOW - 60, 'Europe/London').slice(0, 10);
const allBars = writes.flatMap(w => w.writes).filter(w => w.update.name.includes('/candles_pln/'))
  .flatMap(w => Object.keys(w.update.fields.bars.mapValue.fields).map(Number));
assert.ok(allBars.every(ts => stamp(ts, 'Europe/London').slice(0, 10) < todayLondon), 'dzień w trakcie nie trafia do bazy (D2)');
const status = writes.flatMap(w => w.writes).filter(w => w.update.name.endsWith('/meta/status')).pop();
const paths = status.updateMask.fieldPaths;
assert.ok(paths.includes('pln.currencies.EUR') && paths.includes('pln.rejected'), paths.join(','));
const rej = status.update.fields.pln.mapValue.fields.rejected.mapValue.fields;
assert.ok(/10 lat/.test(rej.QAR.stringValue), rej.QAR.stringValue);
assert.ok(/bez ruchu/.test(rej.THB.stringValue), rej.THB.stringValue);
assert.ok(/świeżych/.test(rej.SAR.stringValue), rej.SAR.stringValue);
assert.ok(/nie ma kursu HUFPLN=X/.test(rej.HUF.stringValue), rej.HUF.stringValue);   // 404 Yahoo = rzadki kurs, nie błąd
assert.strictEqual(urls.filter(u => u.includes('HUFPLN')).length, 1, '404 bez ponawiania');
const st = JSON.parse(props.pln);
assert.strictEqual(st.backfilled, true);
assert.strictEqual(Object.keys(st.currencies).length, 18);
assert.ok(props.pln.length < 9000, 'Script Properties: limit 9 KB na wartość (' + props.pln.length + ')');

// 2) tickPLN_ dzień później: tylko przyjęte, range=10d, nowy dzień zapisany
NOW += DAY; writes.length = 0; urls.length = 0;
G.tickPLN_();
assert.strictEqual(urls.length, 18, 'zapytania tylko o przyjęte waluty');
assert.ok(urls.every(u => u.includes('range=10d')));
assert.ok(!urls.some(u => /QARPLN|THBPLN|SARPLN|AEDPLN|HUFPLN|MXNPLN/.test(u)));
const nd = writes.flatMap(w => w.writes).filter(w => w.update.name.includes('/candles_pln/EUR_2026'));
const newest = Math.max(...nd.flatMap(w => Object.keys(w.update.fields.bars.mapValue.fields).map(Number)));
assert.strictEqual(stamp(newest, 'Europe/London').slice(0, 10), '2026-11-11');
// drugi tick od razu: bez zapytań (wszystko jest)
urls.length = 0; G.tickPLN_(); assert.strictEqual(urls.length, 0);

// 3) D1 FX bez zmian
writes.length = 0;
G.backfillD1();
assert.ok(writes.flatMap(w => w.writes).some(w => w.update.name.includes('/documents/candles_d1/EURUSD_')), 'backfillD1 pisze candles_d1');
console.log('OK');
