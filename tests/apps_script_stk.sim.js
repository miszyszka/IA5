// Symulacja spółek (Stocks, D-071) w Apps Script w Node — atrapy usług Google i Yahoo (interval=1d, events=div,split).
// Uruchamia tests/test_apps_script.py. Sprawdza: lista z stocks/config, cała historia nowych spółek z dywidendami i splitami,
// znacznik = północ w Nowym Jorku, odrzucenie spółki spoza USD i nieznanego tickera, tick tylko z nowym dniem, święto,
// nowy split = cała historia od nowa.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const props = {}, writes = [], urls = [];
let propReads = 0;
const DAY = 86400;
let NOW = Date.UTC(2026, 10, 11, 12, 0) / 1000;     // środa 11.11.2026 12:00 UTC (07:00 w Nowym Jorku)
let CONFIG = ['MU', 'KO', 'CDR.WA', 'NOPE'];
let HOLIDAY = null, NEW_SPLIT = false;

const fmt = new Map();
function stamp(ts, tz) {
  if (!fmt.has(tz)) fmt.set(tz, new Intl.DateTimeFormat('sv-SE', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }));
  return fmt.get(tz).format(new Date(ts * 1000)).replace('T', ' ');
}
function nyOpen(day) {                     // 09:30 w Nowym Jorku danego dnia (tak Yahoo stempluje świece spółek)
  const t = Date.UTC(+day.slice(0, 4), +day.slice(5, 7) - 1, +day.slice(8, 10), 14, 30) / 1000;
  return stamp(t, 'America/New_York').slice(11, 13) === '09' ? t : t - 3600;
}
function yahoo(tk, params) {
  const nyToday = stamp(NOW, 'America/New_York').slice(0, 10);
  const first = tk === 'KO' ? '1990-01-02' : '2010-01-04';
  const from = params.includes('range=10d') ? new Date((NOW - 10 * DAY) * 1000).toISOString().slice(0, 10) : first;
  const ts = [], o = [], h = [], l = [], c = [];
  for (let d = new Date(from + 'T12:00:00Z'); ; d = new Date(d.getTime() + DAY * 1000)) {
    const day = d.toISOString().slice(0, 10);
    if (day > nyToday) break;
    if (d.getUTCDay() === 0 || d.getUTCDay() === 6 || day === HOLIDAY) continue;
    const i = Math.round(d.getTime() / 864e5);
    const p = 50 * (1 + 0.1 * Math.sin(i * 0.01));
    ts.push(nyOpen(day)); o.push(p); h.push(p * 1.01); l.push(p * 0.99); c.push(p * 1.002);
  }
  const ev = { dividends: {}, splits: {} };
  const dts = nyOpen('2026-11-02');
  ev.dividends[dts] = { amount: 0.51, date: dts };
  const sts = nyOpen('2020-06-01');
  ev.splits[sts] = { numerator: 2, denominator: 1, date: sts };
  if (NEW_SPLIT) { const n = nyOpen('2026-11-12'); ev.splits[n] = { numerator: 3, denominator: 1, date: n }; }
  return { chart: { result: [{ meta: { exchangeTimezoneName: 'America/New_York', dataGranularity: '1d', currency: tk === 'CDR.WA' ? 'PLN' : 'USD', longName: tk + ' Inc.' },
    timestamp: ts, events: ev, indicators: { quote: [{ open: o, high: h, low: l, close: c }] } }] } };
}
const ctx = {
  console, Math, JSON, Date, Number, String, Object, Array, Error, encodeURIComponent, decodeURIComponent,
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => { propReads++; return props[k] ?? null; }, setProperty: (k, v) => { props[k] = v; }, deleteProperty: k => { delete props[k]; } }) },
  UrlFetchApp: { fetch: (url, opt) => {
    if (url.includes('finance/chart')) {
      urls.push(url);
      const tk = decodeURIComponent(url.split('/chart/')[1].split('?')[0]);
      if (tk === 'NOPE') return { getResponseCode: () => 404, getContentText: () => '{}' };
      return { getResponseCode: () => 200, getContentText: () => JSON.stringify(yahoo(tk, url.split('?')[1])) };
    }
    if (url.endsWith('/documents/stocks/config')) {
      urls.push(url);
      const body = { fields: { tickers: { arrayValue: { values: CONFIG.map(t => ({ mapValue: { fields: { t: { stringValue: t }, w: { doubleValue: 25 } } } })) } } } };
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
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8') + '\nthis.__ = { tickSTK_, midnightTs_, STK_DEFAULT };', ctx);
const G = ctx.__;
ctx.Date.now = () => NOW * 1000;
const all = () => writes.flatMap(w => w.writes);
const stkDocs = () => all().filter(w => w.update.name.includes('/candles_stk/'));
const lastStatus = () => all().filter(w => w.update.name.endsWith('/meta/status')).pop().update.fields.stk.mapValue.fields;

assert.strictEqual(G.STK_DEFAULT.length, 27);
assert.strictEqual(stamp(G.midnightTs_('2026-07-01', 'America/New_York'), 'America/New_York'), '2026-07-01 00:00:00');
assert.strictEqual(stamp(G.midnightTs_('2026-01-05', 'America/New_York'), 'America/New_York'), '2026-01-05 00:00:00');

// 1) pierwszy tick: lista z config, cała historia nowych spółek
G.tickSTK_();
assert.ok(urls.some(u => u.endsWith('/documents/stocks/config')), 'czyta stocks/config');
const names = stkDocs().map(w => w.update.name.split('/').pop());
assert.ok(names.includes('KO_1990') && names.includes('KO_2026') && names.includes('MU_2010'), 'cała historia');
assert.ok(!names.some(n => n.startsWith('CDR.WA_') || n.startsWith('NOPE_')), 'odrzucone bez zapisu');
const st1 = lastStatus();
const rej = st1.rejected.mapValue.fields;
assert.ok(/PLN/.test(rej['CDR.WA'].stringValue) && /nie zna/.test(rej.NOPE.stringValue), 'powody odrzucenia');
const ko = stkDocs().filter(w => w.update.name.endsWith('/KO_2026'))[0].update.fields;
const keys = Object.keys(ko.bars.mapValue.fields).map(Number);
assert.ok(keys.every(t => stamp(t, 'America/New_York').endsWith('00:00:00')), 'znacznik = północ w Nowym Jorku');
const nyToday = stamp(NOW - 60, 'America/New_York').slice(0, 10);
assert.ok(keys.every(t => stamp(t, 'America/New_York').slice(0, 10) < nyToday), 'dzień w trakcie nie trafia do bazy');
assert.ok(Object.keys(ko.div.mapValue.fields).length === 1, 'dywidenda zapisana');
assert.ok(stkDocs().some(w => w.update.name.endsWith('/KO_2020') && Object.keys(w.update.fields.split.mapValue.fields).length === 1), 'split zapisany');
assert.ok(st1.tickers.mapValue.fields.KO.mapValue.fields.lastDay.stringValue === '2026-11-10');

// 2) ten sam dzień — bez zapytań i zapisów
let n = writes.length, nu = urls.length;
NOW += 600;
G.tickSTK_();
assert.strictEqual(writes.length, n, 'bez nowego dnia — bez zapisu');
propReads = 0;
NOW += 60;
G.tickSTK_();
assert.ok(propReads <= 1, 'tick co minutę: jeden odczyt Script Properties (limit dzienny), było ' + propReads);

// 3) następny dzień: tick pobiera 10 dni i dopisuje dzień
NOW = Date.UTC(2026, 10, 12, 12, 0) / 1000;
G.tickSTK_();
const st3 = lastStatus();
assert.strictEqual(st3.tickers.mapValue.fields.MU.mapValue.fields.lastDay.stringValue, '2026-11-11');
assert.ok(urls.slice(nu).some(u => u.includes('range=10d')), 'tick: 10 dni');

// 4) święto: żadna spółka nie ma dnia → jedno pobranie, potem cisza do następnego dnia
HOLIDAY = '2026-11-12';
NOW = Date.UTC(2026, 10, 13, 12, 0) / 1000;
nu = urls.length;
G.tickSTK_();
const after = urls.length;
assert.ok(after > nu, 'pobrał');
NOW += 2 * 3600;
G.tickSTK_();
assert.strictEqual(urls.filter((u, i) => i >= after && u.includes('finance/chart')).length, 0, 'święto — bez ponowień');

// 5) nowy split → spółka pobierana od nowa w całości
HOLIDAY = null; NEW_SPLIT = true;
NOW = Date.UTC(2026, 10, 14, 12, 0) / 1000;   // sobota; oczekiwany piątek 13.11
G.tickSTK_();                                  // tick widzi split → spółki do pobrania od nowa
nu = urls.length;
NOW += 120;
G.tickSTK_();
assert.ok(urls.slice(nu).some(u => u.includes('period1=0')), 'cała historia po splicie');

// 6) spółka usunięta z listy — tick przestaje ją pobierać
CONFIG = ['KO'];
NOW = Date.UTC(2026, 10, 17, 12, 0) / 1000;
nu = urls.length;
G.tickSTK_();
assert.ok(!urls.slice(nu).some(u => u.includes('/chart/MU')), 'MU poza listą');
console.log('OK stk');
