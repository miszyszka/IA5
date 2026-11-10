/**
 * IA5 — pobieranie świec H1 z Yahoo do Firestore (CLAUDE.md, sekcja 5).
 * Uruchom raz: setup()  (backfill 730 dni + wyzwalacz co 1 min). Po wklejeniu nowej wersji: installTrigger().
 * Świece dzienne (D-053): raz backfillD1() — potem tick() dopisuje je sam.
 * Źródło prawdy tego pliku: repo miszyszka/IA5, katalog apps_script/.
 *
 * Budżet Firestore (Z4): ok. 8 zapisów świec + 1–4 zapisy statusu na godzinę (po każdej rundzie z nową świecą)
 * ≈ 300 zapisów/dobę, 0 odczytów.
 * Budżet Apps Script (D-033): wyzwalacz co 1 min; gdy wszystko jest — koniec po odczycie Script Properties (< 0,5 s).
 * Tuż po pełnej godzinie skrypt czeka na zamknięcie świecy (D2: +60 s) i ponawia brakujące pary co 15 s,
 * najwyżej ok. 100 s na uruchomienie → ok. 30–40 min czasu wykonania na dobę (limit konta: 90 min).
 * Dziennik (meta/status.daily) i audyt świeca po świecy z 3 tygodni (meta/status.recent, ok. 4 KB): bez dodatkowych zapisów — jadą w zapisie statusu;
 * jednorazowo 16 odczytów (2 miesiące × 8 par) przy pierwszym uruchomieniu i przy rebuildDaily().
 *
 * Świece dzienne (D1, D-053): backfillD1() raz — cała historia Yahoo (interval=1d, od 1970: Yahoo zwraca od pierwszej
 * notowanej daty, dla par FX ok. 2003), zapis w candles_d1/{PARA}_{RRRR}: ok. 200 zapisów jednorazowo.
 * Potem tick() po północy w Londynie dopisuje zamkniętą świecę dnia: ok. 8 zapisów świec + 1 statusu na dobę,
 * ponawia brakujące pary co 15 min. 0 odczytów.
 */
const PROJECT_ID = 'project-ia5';
const DB = 'projects/' + PROJECT_ID + '/databases/(default)';
const API = 'https://firestore.googleapis.com/v1/' + DB;
const H = 3600;
const DAILY_DAYS = 60; // tyle dni trzyma dziennik świec w meta/status
const RECENT_H = 21 * 24; // audyt świeca po świecy: ostatnie 3 tygodnie (meta/status.recent, D-027)
const LATE_S = 20 * 60;   // świeca zapisana później niż 20 min po zamknięciu = spóźniona
const RETRY_S = 15;       // D-033: ponowienie brakujących par co 15 s…
const BURST_S = 10 * 60;  // …przez pierwsze 10 min po zamknięciu świecy…
const RUN_MAX_S = 100;    // …i najwyżej tyle sekund jednego uruchomienia (wyzwalacz co 1 min, blokada nie dubluje)

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

function tick() {
  withLock_(() => {
    run_('tick');
    try { tickD1_(); } catch (e) { log_('tickD1', '-', 0, null, 'BŁĄD ' + e.message); } // D1 nigdy nie zatrzymuje H1
  });
}

/** Ręcznie, raz (D-053): cała historia świec dziennych Yahoo dla 8 par → candles_d1/*, meta/status.d1. Można powtórzyć (upsert). */
function backfillD1() { withLock_(() => runD1_('backfill', PAIRS, loadD1_(), nowSec())); }

/** Ręcznie: przelicza dziennik świec (meta/status.daily) z dokumentów candles/* w Firestore. */
function rebuildDaily() {
  withLock_(() => {
    const state = loadState_();
    delete state.daily;
    delete state.recent;
    saveState_(state);
    run_('tick');
  });
}

function installTrigger() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'tick')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('tick').timeBased().everyMinutes(1).create(); // D-033: najszybciej, jak pozwala Apps Script
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
  // święta FX: 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC — rynek nieczynny (D-028)
  const mo = d.getUTCMonth() + 1, dom = d.getUTCDate();
  if (((mo === 12 && dom === 24) || (mo === 12 && dom === 31)) && hr >= 21) return false;
  if (((mo === 12 && dom === 25) || (mo === 1 && dom === 1)) && hr < 22) return false;
  return true;
}

/** Najnowsza świeca, której oczekujemy w bazie. */
function expectedTs(now) {
  let ts = lastClosedTs(now);
  for (let i = 0; i < 80 && !isExpectedBar(ts); i++) ts -= H;
  return ts;
}

function dayKey(ts) { return new Date(ts * 1000).toISOString().slice(0, 10); }

/** Zostawia w dzienniku tylko ostatnie DAILY_DAYS dni. */
function pruneDaily_(daily, now) {
  const from = dayKey(now - (DAILY_DAYS - 1) * 86400);
  Object.keys(daily).forEach(d => { if (d < from) delete daily[d]; });
  return daily;
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
  let startedAt = nowSec();
  // D-033: tuż po pełnej godzinie świeca jeszcze nie jest „zamknięta” (D2: +60 s) — czekamy, zamiast odpuszczać minutę
  const hourStart = Math.floor(startedAt / H) * H;
  if (mode === 'tick' && startedAt - hourStart < 60 && isExpectedBar(hourStart - H)) {
    const st0 = loadState_();
    const waiting = PAIRS.some(p => !(st0.pairs[p.name] && st0.pairs[p.name].lastTs >= hourStart - H));
    if (waiting) {
      Utilities.sleep((hourStart + 61 - startedAt) * 1000);
      startedAt = nowSec();
    }
  }
  const state = loadState_();
  const exp = expectedTs(startedAt);
  let todo = PAIRS.filter(p => mode === 'backfill' ||
    !(state.pairs[p.name] && state.pairs[p.name].lastTs >= exp));
  if (!todo.length && state.daily && state.recent) { // nic nowego — zero zapytań i zapisów
    if (mode === 'tick') dispatchLive_(exp, true);
    return;
  }
  if (!state.daily || !state.recent) { // jednorazowo: dziennik i audyt z tego, co już jest w bazie
    const seed = seedFromDb_(startedAt);
    state.daily = state.daily || seed.daily;
    state.recent = state.recent || seed.recent;
  }
  state.recent = shiftRecent_(state.recent, startedAt);

  // rundy: każda pyta Yahoo tylko o brakujące pary i od razu zapisuje status (dashboard zatrzymuje zegar tej pary)
  for (let round = 0; ; round++) {
    const r = fetchRound_(mode, todo, state, startedAt, round);
    todo = todo.filter(p => !(state.pairs[p.name] && state.pairs[p.name].lastTs >= exp));
    const now = nowSec();
    const more = mode === 'tick' && todo.length && now - (exp + H) < BURST_S && now - startedAt + RETRY_S < RUN_MAX_S;
    if (Object.keys(r.updated).length || r.errors.length || !more) writeRound_(mode, state, startedAt, r);
    if (!more) break;
    Utilities.sleep(RETRY_S * 1000);
  }
  saveState_(state);
  if (mode === 'tick') dispatchLive_(exp, !todo.length);
}

/**
 * D-052: komplet świec (albo koniec prób po 10 min) → GitHub Actions liczy inwestorów i wysyła maile.
 * Raz na świecę; nieudane wywołanie ponowi następny tick. Token: Script Properties → GITHUB_TOKEN.
 */
function dispatchLive_(exp, complete) {
  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty('GITHUB_TOKEN');
  if (!token || Number(props.getProperty('LIVE_TS') || 0) >= exp) return;
  if (!complete && nowSec() - (exp + H) < BURST_S) return;
  const r = UrlFetchApp.fetch('https://api.github.com/repos/miszyszka/IA5/dispatches', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json' },
    payload: JSON.stringify({ event_type: 'candles', client_payload: { ts: exp } }),
  });
  if (r.getResponseCode() === 204) props.setProperty('LIVE_TS', String(exp));
  else console.warn('GitHub dispatch: ' + r.getResponseCode());
}

function fetchRound_(mode, todo, state, startedAt, round) {
  const updated = {};
  const errors = [];
  let runLatency = null;

  todo.forEach(p => {
    try {
      const params = mode === 'backfill'
        ? 'period1=' + (startedAt - 729 * 86400) + '&period2=' + startedAt
        : round ? 'range=1d' : 'range=5d';
      const now = nowSec();
      const got = fetchYahoo(p.yahoo, params);
      // D2/D5: Yahoo czasem zwraca pojedyncze notowania z czasem nie na pełnej godzinie (np. 30.10.2026 17:59–18:25
      // dla USD/CAD i USD/CHF) — to nie są świece H1: nie zapisujemy ich, zostaje flaga i wpis w logu (nie cicha naprawa)
      // bieżące notowanie świecy w trakcie (czas np. 09:00:27) Yahoo dołącza zawsze — to nie błąd; flagujemy tylko
      // notowania spoza pełnej godziny w czasie już zamkniętym (jak 30.10.2026 17:59–18:25), D-047
      const offGrid = got.filter(b => b.ts % H !== 0 && b.ts + H <= now - 60);
      const closed = got.filter(b => b.ts % H === 0 && b.ts + H <= now - 60);
      const ps = state.pairs[p.name] || { lastTs: 0, count: 0, last: [], latencySec: null };
      ps.lastTs = Math.floor((ps.lastTs || 0) / H) * H;   // stary stan mógł mieć czas notowania zamiast świecy
      const from = mode === 'backfill' || !ps.lastTs ? 0 : ps.lastTs - 3 * H;
      const bars = closed.filter(b => b.ts >= from);
      if (offGrid.length) log_(mode, p.name, 0, null, 'pominięte notowania poza pełną godziną: ' + offGrid.length +
        ' (' + new Date(offGrid[0].ts * 1000).toISOString() + ' …)');
      if (!bars.length) return;
      const fresh = bars.filter(b => b.ts > ps.lastTs);
      if (round && !fresh.length) return; // ponowienie bez nowej świecy — bez zapisu

      const flags = offGrid.slice(0, 3).map(b => 'ts@' + b.ts);
      bars.forEach(b => barFlags(b).forEach(f => flags.push(f + '@' + b.ts)));
      (ps.last || []).forEach(old => {
        const nb = bars.find(b => b.ts === old.ts);
        if (nb && Math.abs(nb.c - old.c) > 0.5 * p.pip) flags.push('revised@' + old.ts);
      });
      for (let i = 1; i < bars.length; i++) {
        const miss = [];
        for (let t = bars[i - 1].ts + H; t < bars[i].ts; t += H) if (isExpectedBar(t)) miss.push(t);
        // D-039: ≤ 3 h tuż przy weekendzie/święcie to granica tygodnia (Yahoo otwiera tydzień później niż kalendarz), nie luka
        const boundary = miss.length && miss.length <= 3 &&
          (!isExpectedBar(miss[0] - H) || !isExpectedBar(miss[miss.length - 1] + H));
        if (miss.length && !boundary) flags.push('luka@' + miss[0]);
      }

      writeBars_(p.name, bars);
      const writtenAt = nowSec();
      const newest = bars[bars.length - 1];
      // dziennik: liczba świec w bazie wg dnia świecy (UTC); backfill przelicza, tick dolicza nowe
      const counted = mode === 'backfill' ? bars : fresh;
      if (mode === 'backfill') {
        const days = {};
        bars.forEach(b => { days[dayKey(b.ts)] = true; });
        Object.keys(days).forEach(d => { if (state.daily[d]) delete state.daily[d][p.name]; });
      }
      counted.forEach(b => {
        const d = dayKey(b.ts);
        const row = state.daily[d] = state.daily[d] || {};
        row[p.name] = (row[p.name] || 0) + 1;
      });
      const lat = fresh.length ? writtenAt - (newest.ts + H) : null;
      // audyt świeca po świecy: 1 = jest, l = spóźniona, f = z flagą jakości
      const flagged = {};
      flags.forEach(f => { const t = Number(f.split('@')[1]); if (!f.startsWith('luka')) flagged[t] = true; });
      bars.forEach(b => {
        const late = mode === 'tick' && b.ts > ps.lastTs && writtenAt - (b.ts + H) > LATE_S;
        markRecent_(state.recent, p.name, b.ts, flagged[b.ts] ? 'f' : late ? 'l' : '1');
      });

      ps.count = mode === 'backfill' ? bars.length : ps.count + fresh.length;
      ps.lastTs = Math.max(ps.lastTs, newest.ts);
      ps.last = bars.slice(-3);
      ps.flags = flags.slice(-20);
      if (lat !== null) ps.latencySec = lat;
      ps.savedAt = writtenAt;
      state.pairs[p.name] = ps;
      updated[p.name] = { lastTs: ps.lastTs, latencySec: ps.latencySec, count: ps.count, flags: ps.flags, savedAt: writtenAt };
      if (lat !== null && mode === 'tick') runLatency = Math.max(runLatency || 0, lat);
      if (fresh.length || flags.length) log_(mode, p.name, fresh.length, lat, flags.slice(0, 5).join(' '));
    } catch (e) {
      errors.push(p.name + ': ' + e.message);
      log_(mode, p.name, 0, null, 'BŁĄD ' + e.message);
    }
  });
  return { updated: updated, errors: errors, runLatency: runLatency };
}

function writeRound_(mode, state, startedAt, r) {
  state.latency24h = (state.latency24h || []).filter(x => x.at > startedAt - 86400);
  if (r.runLatency !== null) state.latency24h.push({ at: nowSec(), s: r.runLatency });
  state.latency24h = state.latency24h.slice(-300);

  const totalBars = PAIRS.reduce((s, p) => s + ((state.pairs[p.name] || {}).count || 0), 0);
  const status = {
    daily: pruneDaily_(state.daily, startedAt),
    recent: state.recent,
    lastRun: { mode: mode, startedAt: startedAt, finishedAt: nowSec(), ok: !r.errors.length, error: r.errors.join('; ') || null },
    totalBars: totalBars,
    latency24h: state.latency24h,
    cross: crossCheck_(state),
  };
  writeStatus_(status, r.updated);
}

/** Okno audytu przesunięte do teraz: { start, pairs: { PARA: napis RECENT_H znaków } }, '.' = brak świecy. */
function shiftRecent_(recent, now) {
  const start = Math.floor(now / H) * H - RECENT_H * H;
  const out = { start: start, pairs: {} };
  PAIRS.forEach(p => {
    const old = (recent && recent.pairs && recent.pairs[p.name]) || '';
    const off = recent ? Math.round((start - recent.start) / H) : RECENT_H;
    let str = '';
    for (let i = 0; i < RECENT_H; i++) {
      const j = i + off;
      str += j >= 0 && j < old.length ? old[j] : '.';
    }
    out.pairs[p.name] = str;
  });
  return out;
}

function markRecent_(recent, pair, ts, ch) {
  const i = Math.round((ts - recent.start) / H);
  const str = recent.pairs[pair];
  if (i < 0 || i >= RECENT_H || !str) return;
  const rank = { '.': 0, '1': 1, l: 2, f: 3 }; // ponowny zapis tej samej świecy nie kasuje „spóźniona” ani flagi
  if (rank[ch] < rank[str[i]]) return;
  recent.pairs[pair] = str.slice(0, i) + ch + str.slice(i + 1);
}

/** Dziennik i audyt z dokumentów candles/* (bieżący i poprzedni miesiąc). */
function seedFromDb_(now) {
  const daily = {};
  const recent = shiftRecent_(null, now);
  const months = [monthKey(now), monthKey(now - 32 * 86400)];
  PAIRS.forEach(p => months.forEach(m => {
    const r = UrlFetchApp.fetch(API + '/documents/candles/' + p.name + '_' + m + '?mask.fieldPaths=bars', {
      headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT_ID },
      muteHttpExceptions: true,
    });
    if (r.getResponseCode() === 404) return;
    if (r.getResponseCode() !== 200) throw new Error('Firestore ' + r.getResponseCode() + ': ' + r.getContentText().slice(0, 200));
    const doc = JSON.parse(r.getContentText());
    const bars = (doc.fields && doc.fields.bars && doc.fields.bars.mapValue.fields) || {};
    Object.keys(bars).forEach(ts => {
      const d = dayKey(Number(ts));
      const row = daily[d] = daily[d] || {};
      row[p.name] = (row[p.name] || 0) + 1;
      markRecent_(recent, p.name, Number(ts), '1');
    });
  }));
  return { daily: pruneDaily_(daily, now), recent: recent };
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

function fetchYahoo(ticker, params) { return fetchYahooRaw_(ticker, 'interval=1h&' + params, parseYahoo); }

function fetchYahooRaw_(ticker, params, parse) {
  const url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + encodeURIComponent(ticker) + '?' + params;
  let lastErr = '';
  for (let i = 0; i < 3; i++) {
    try {
      const r = UrlFetchApp.fetch(url, { muteHttpExceptions: true, headers: { 'User-Agent': 'Mozilla/5.0' } });
      if (r.getResponseCode() === 200) return parse(JSON.parse(r.getContentText()));
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

// ---------- świece dzienne D1 (D-053) ----------
// Ta sama logika dnia co runner/ia5/daily.py. Znacznik = czas otwarcia = północ dnia w strefie Yahoo (dla par FX
// Europe/London). Świeca dnia d jest zamknięta, gdy w tej strefie zaczął się dzień d+1 (+60 s, jak D2).

const D1_TZ = 'Europe/London';
const D1_RETRY_S = 15 * 60;   // brakująca świeca dnia: ponowienie co 15 min
const D1_KEEP = 4;            // tyle ostatnich zamkniętych dni nadpisujemy przy każdym pobraniu (Yahoo je koryguje)

function localStamp_(ts, tz) { return Utilities.formatDate(new Date(ts * 1000), tz, 'yyyy-MM-dd HH:mm:ss'); }

function isExpectedDay_(day) {           // 'RRRR-MM-DD': dzień roboczy, bez 25.12 i 1.01 (D-028)
  const d = new Date(day + 'T12:00:00Z');
  const md = day.slice(5);
  return d.getUTCDay() >= 1 && d.getUTCDay() <= 5 && md !== '12-25' && md !== '01-01';
}

function prevDay_(day) { return new Date(new Date(day + 'T12:00:00Z').getTime() - 86400000).toISOString().slice(0, 10); }

/** Najnowszy dzień, którego zamkniętej świecy oczekujemy: ostatni dzień roboczy przed dzisiejszym w strefie Yahoo. */
function expectedDayD1_(now, tz) {
  let d = prevDay_(localStamp_(now - 60, tz).slice(0, 10));
  for (let i = 0; i < 10 && !isExpectedDay_(d); i++) d = prevDay_(d);
  return d;
}

function parseYahooD1_(j) {
  const res = j && j.chart && j.chart.result && j.chart.result[0];
  if (!res) throw new Error('brak danych w odpowiedzi');
  const meta = res.meta || {};
  if (meta.dataGranularity && meta.dataGranularity !== '1d') throw new Error('Yahoo zwróciło interwał ' + meta.dataGranularity + ' zamiast 1d');
  const tz = meta.exchangeTimezoneName || D1_TZ;
  if (!res.timestamp) return { tz: tz, bars: [] };
  const q = res.indicators.quote[0];
  const bars = [];
  for (let i = 0; i < res.timestamp.length; i++) {
    const o = q.open[i], h = q.high[i], l = q.low[i], c = q.close[i];
    if ([o, h, l, c].some(v => v === null || v === undefined)) continue;
    bars.push({ ts: res.timestamp[i], o: o, h: h, l: l, c: c });
  }
  return { tz: tz, bars: bars };
}

function loadD1_() {
  const raw = PropertiesService.getScriptProperties().getProperty('d1');
  return raw ? JSON.parse(raw) : { pairs: {}, tz: D1_TZ };
}

function saveD1_(st) { PropertiesService.getScriptProperties().setProperty('d1', JSON.stringify(st)); }

/** Z tick(): tanio — bez zapytań, gdy każda para ma świecę oczekiwanego dnia albo ostatnia próba była < 15 min temu. */
function tickD1_() {
  const st = loadD1_();
  if (!st.backfilled) return;            // najpierw backfillD1() — inaczej liczniki świec nie miałyby sensu
  const now = nowSec();
  const exp = expectedDayD1_(now, st.tz || D1_TZ);
  const todo = PAIRS.filter(p => !(st.pairs[p.name] && st.pairs[p.name].lastDay >= exp));
  if (!todo.length || now - (st.triedAt || 0) < D1_RETRY_S) return;
  st.triedAt = now;
  saveD1_(st);
  runD1_('tick', todo, st, now);
}

function runD1_(mode, todo, st, now) {
  const errors = [];
  const updated = {};
  todo.forEach(p => {
    try {
      const params = 'interval=1d&' + (mode === 'backfill' ? 'period1=0&period2=' + now : 'range=10d');
      const got = fetchYahooRaw_(p.yahoo, params, parseYahooD1_);
      const tz = st.tz = got.tz;
      const today = localStamp_(now - 60, tz).slice(0, 10);
      const ps = mode === 'backfill' ? { lastTs: 0, count: 0, last: [] } : (st.pairs[p.name] || { lastTs: 0, count: 0, last: [] });
      const flags = [];
      const bars = [];
      got.bars.forEach(b => {
        const loc = localStamp_(b.ts, tz);
        b.day = loc.slice(0, 10);
        if (b.day >= today) return;                                   // dzień w trakcie (D2) — nigdy do bazy
        if (loc.slice(11) !== '00:00:00') { flags.push('ts@' + b.day); return; } // nie świeca dnia — flaga, nie cicha naprawa
        bars.push(b);
      });
      const from = mode === 'backfill' ? 0 : ps.lastTs - D1_KEEP * 86400;
      const keep = bars.filter(b => b.ts >= from);
      if (!keep.length) { if (flags.length) log_('D1 ' + mode, p.name, 0, null, flags.slice(0, 5).join(' ')); return; }
      keep.forEach(b => {
        if (!(b.o > 0 && b.h > 0 && b.l > 0 && b.c > 0)) flags.push('cena<=0@' + b.day);
        if (b.h < Math.max(b.o, b.c) || b.l > Math.min(b.o, b.c)) flags.push('ohlc@' + b.day);
        const old = (ps.last || []).find(x => x.ts === b.ts);
        if (old && Math.abs(old.c - b.c) > 0.5 * p.pip) flags.push('revised@' + b.day);
      });
      const fresh = keep.filter(b => b.ts > ps.lastTs);
      // ponowienie bez nowego dnia i bez korekty Yahoo — bez zapisu (Z4)
      if (mode === 'tick' && !fresh.length && !flags.some(f => f.startsWith('revised'))) return;
      writeBarsD1_(p.name, keep, tz);
      const newest = keep[keep.length - 1];
      ps.count = mode === 'backfill' ? keep.length : ps.count + fresh.length;
      if (mode === 'backfill' || !ps.firstDay) ps.firstDay = keep[0].day;
      ps.lastTs = Math.max(ps.lastTs, newest.ts);
      ps.lastDay = ps.lastDay && ps.lastDay > newest.day ? ps.lastDay : newest.day;
      ps.last = keep.slice(-D1_KEEP).map(b => ({ ts: b.ts, c: b.c }));
      ps.flags = flags.slice(-10);
      ps.savedAt = nowSec();
      st.pairs[p.name] = ps;
      updated[p.name] = { firstDay: ps.firstDay, lastTs: ps.lastTs, lastDay: ps.lastDay, count: ps.count, flags: ps.flags, savedAt: ps.savedAt };
      log_('D1 ' + mode, p.name, fresh.length, null, (ps.firstDay + ' – ' + ps.lastDay + ' ' + flags.slice(0, 5).join(' ')).trim());
    } catch (e) {
      errors.push(p.name + ': ' + e.message);
      log_('D1 ' + mode, p.name, 0, null, 'BŁĄD ' + e.message);
    }
  });
  if (mode === 'backfill' && !errors.length) st.backfilled = true;
  saveD1_(st);
  if (mode === 'tick' && !Object.keys(updated).length && !errors.length) return;
  const total = PAIRS.reduce((s, p) => s + ((st.pairs[p.name] || {}).count || 0), 0);
  const fields = { tz: st.tz || D1_TZ, totalBars: total,
    lastRun: { mode: mode, at: nowSec(), ok: !errors.length, error: errors.join('; ') || null }, pairs: updated };
  const paths = ['d1.tz', 'd1.totalBars', 'd1.lastRun'].concat(Object.keys(updated).map(p => 'd1.pairs.' + p));
  commit_([{ update: { name: DB + '/documents/meta/status', fields: { d1: toValue_(fields) } }, updateMask: { fieldPaths: paths } }]);
  if (errors.length && mode === 'backfill') throw new Error('backfillD1: ' + errors.join('; '));
}

/** candles_d1/{PARA}_{RRRR} (rok wg dnia w strefie Yahoo): pola pair, year, tz, bars { ts: [o, h, l, c] } — upsert (D3). */
function writeBarsD1_(pair, bars, tz) {
  const groups = {};
  bars.forEach(b => { const y = b.day.slice(0, 4); (groups[y] = groups[y] || []).push(b); });
  commit_(Object.keys(groups).map(y => {
    const fields = {};
    const paths = ['pair', 'year', 'tz'];
    groups[y].forEach(b => {
      fields[String(b.ts)] = { arrayValue: { values: [b.o, b.h, b.l, b.c].map(v => ({ doubleValue: v })) } };
      paths.push('bars.`' + b.ts + '`');
    });
    return {
      update: {
        name: DB + '/documents/candles_d1/' + pair + '_' + y,
        fields: { pair: { stringValue: pair }, year: { stringValue: y }, tz: { stringValue: tz }, bars: { mapValue: { fields: fields } } },
      },
      updateMask: { fieldPaths: paths },
      updateTransforms: [{ fieldPath: 'updatedAt', setToServerValue: 'REQUEST_TIME' }],
    };
  }));
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

// Script Properties mają limit 9 KB na wartość — dziennik i audyt trzymamy w osobnych właściwościach.
function loadState_() {
  const props = PropertiesService.getScriptProperties();
  const raw = props.getProperty('state');
  const s = raw ? JSON.parse(raw) : { pairs: {}, latency24h: [] };
  ['daily', 'recent'].forEach(k => {
    const v = props.getProperty(k);
    if (v) s[k] = JSON.parse(v);
  });
  return s;
}

function saveState_(s) {
  const props = PropertiesService.getScriptProperties();
  const rest = Object.assign({}, s);
  ['daily', 'recent'].forEach(k => {
    delete rest[k];
    if (s[k]) props.setProperty(k, JSON.stringify(s[k])); else props.deleteProperty(k);
  });
  props.setProperty('state', JSON.stringify(rest));
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

/**
 * Ręcznie, jednorazowo (D-042, zgoda Michała 2026-10-31): usuwa z candles/* wpisy, których czas nie jest pełną
 * godziną — to pojedyncze notowania Yahoo, nie świece H1 (np. 30.10.2026 17:59–18:25 dla USD/CAD i USD/CHF).
 * Świece godzinowe zostają nietknięte. Koszt: ok. 200 odczytów (wszystkie dokumenty) + 1 zapis na dokument z błędem.
 */
function removeOffGrid() {
  withLock_(() => {
    let total = 0;
    let pageToken = '';
    do {
      const url = API + '/documents/candles?pageSize=50&mask.fieldPaths=bars' +
        (pageToken ? '&pageToken=' + encodeURIComponent(pageToken) : '');
      const r = UrlFetchApp.fetch(url, {
        headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken(), 'x-goog-user-project': PROJECT_ID },
        muteHttpExceptions: true,
      });
      if (r.getResponseCode() !== 200) throw new Error('Firestore ' + r.getResponseCode() + ': ' + r.getContentText().slice(0, 300));
      const j = JSON.parse(r.getContentText());
      (j.documents || []).forEach(d => {
        const bars = (d.fields && d.fields.bars && d.fields.bars.mapValue && d.fields.bars.mapValue.fields) || {};
        const bad = Object.keys(bars).filter(k => Number(k) % H !== 0);
        if (!bad.length) return;
        // pole w updateMask, którego nie ma w `fields` → Firestore je usuwa; świece godzinowe zostają
        commit_([{ update: { name: d.name, fields: {} }, updateMask: { fieldPaths: bad.map(k => 'bars.`' + k + '`') } }]);
        const doc = d.name.split('/').pop();
        total += bad.length;
        log_('removeOffGrid', doc.split('_')[0], 0, null, 'usunięte notowania poza pełną godziną: ' + bad.length + ' w ' + doc);
      });
      pageToken = j.nextPageToken || '';
    } while (pageToken);
    Logger.log('removeOffGrid: usunięto ' + total + ' wpisów poza pełną godziną');
  });
}
