// Symulacja samonaprawy Apps Script (D-060) w Node — atrapy usług Google, Yahoo z dziurą. Uruchamia tests/test_apps_script.py.
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const props = {}, writes = [], logs = [];
const H = 3600;
const NOW = Date.UTC(2026, 10, 11, 10, 30) / 1000;     // środa 10:30 UTC (po pierwszych 10 min godziny)
let yahooHasHole = false;
function bars(ticker) {
  const out = [];
  for (let t = Math.floor((NOW - 30 * 86400) / H) * H; t + H <= NOW - 60; t += H) {
    const d = new Date(t * 1000), wd = d.getUTCDay();
    if (wd === 6 || (wd === 5 && d.getUTCHours() >= 21) || (wd === 0 && d.getUTCHours() < 22)) continue;
    if (yahooHasHole && t >= Date.UTC(2026, 10, 10, 8) / 1000 && t < Date.UTC(2026, 10, 10, 14) / 1000) continue;
    const base = ticker === 'JPY=X' ? 150 : 1.1;
    out.push([t, base, base * 1.001, base * 0.999, base]);
  }
  return out;
}
const ctx = {
  console, Math, JSON, Date, Number, String, Object, Array, Error, encodeURIComponent,
  PropertiesService: { getScriptProperties: () => ({ getProperty: k => props[k] ?? null, setProperty: (k, v) => { props[k] = v; }, deleteProperty: k => { delete props[k]; } }) },
  UrlFetchApp: { fetch: (url, opt) => {
    if (url.includes('finance/chart')) {
      const tk = decodeURIComponent(url.split('/chart/')[1].split('?')[0]);
      const b = bars(tk);
      const body = { chart: { result: [{ timestamp: b.map(x => x[0]), indicators: { quote: [{ open: b.map(x => x[1]), high: b.map(x => x[2]), low: b.map(x => x[3]), close: b.map(x => x[4]) }] } }] } };
      return { getResponseCode: () => 200, getContentText: () => JSON.stringify(body) };
    }
    writes.push(JSON.parse(opt.payload)); return { getResponseCode: () => 200, getContentText: () => '{}' };
  } },
  ScriptApp: { getOAuthToken: () => 'tok' },
  Utilities: { sleep: () => {}, formatDate: () => '' },
  SpreadsheetApp: { getActive: () => ({ getSheetByName: () => ({ getLastRow: () => 1, appendRow: r => logs.push(r) }) }) },
  LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }) },
};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[2], 'utf8') + '\nthis.__ = { repairH1_, repairDue_, shiftRecent_, PAIRS, setRecent_, gapFlags_ };', ctx);
const G = ctx.__;
// stan „przed”: para ma stare flagi, w audycie dziura i flaga
const state = { pairs: {}, latency24h: [], daily: {}, recent: null };
G.PAIRS.forEach(p => { state.pairs[p.name] = { lastTs: NOW - 2 * H, count: 500, flags: ['luka@1', 'revised@2', 'ohlc@3'], last: [] }; });
state.recent = G.shiftRecent_(null, NOW);
const p0 = G.PAIRS[0].name;
const idx = state.recent.pairs[p0].length - 30;
state.recent.pairs[p0] = state.recent.pairs[p0].slice(0, idx) + 'f.l' + state.recent.pairs[p0].slice(idx + 3);
assert.ok(G.repairDue_(NOW), 'naprawa należna, gdy nigdy jej nie było');
G.repairH1_(state, NOW);
// 1) bez dziur w Yahoo: flagi znikają, audyt: '.'/'f' → '1', 'l' zostaje
G.PAIRS.forEach(p => assert.strictEqual(state.pairs[p.name].flags.length, 0, p.name));
assert.strictEqual(state.recent.pairs[p0].slice(idx, idx + 3), '11l');
// 2) zapis: świece 8 par (po ≤ 2 miesiące) + status w jednym commicie na końcu
const candleDocs = writes.flatMap(w => w.writes).filter(w => w.update.name.includes('/candles/'));
assert.ok(candleDocs.length >= 8 && candleDocs.length <= 16, 'dokumenty świec: ' + candleDocs.length);
const st = writes[writes.length - 1].writes[0];
assert.ok(st.update.name.endsWith('meta/status') && st.updateMask.fieldPaths.includes('pairs.' + p0));
assert.ok(props.REPAIR_AT == String(NOW) && !G.repairDue_(NOW + 3600), 'następna naprawa za 6 h');
assert.ok(G.repairDue_(NOW + 6 * H), 'po 6 h znowu');
// 3) Yahoo wciąż nie ma 6 godzin → zostaje jedna flaga luki na parę (Mac ją uzupełni)
yahooHasHole = true; writes.length = 0;
G.repairH1_(state, NOW + 6 * H + 900);
G.PAIRS.forEach(p => assert.strictEqual(state.pairs[p.name].flags.filter(f => f.startsWith('luka')).length, 1, p.name));
console.log('OK: samonaprawa — flagi skasowane, audyt poprawiony, koszt', candleDocs.length, 'dokumentów świec + 1 status; luka bez danych Yahoo zostaje 1 flagą');
