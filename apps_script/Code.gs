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
const REPAIR_EVERY_S = 6 * H;  // D-060: co 6 h samonaprawa — ponowne pobranie ostatnich REPAIR_DAYS dni i nadpisanie świec
const REPAIR_DAYS = 30;        // dziury, które Yahoo uzupełnił później, i świece przez niego skorygowane trafiają do bazy

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
    try { tickPLN_(); } catch (e) { log_('tickPLN', '-', 0, null, 'BŁĄD ' + e.message); } // D-063: kursy PLN nigdy nie zatrzymują H1 ani D1
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
  if (!todo.length && state.daily && state.recent) { // nic nowego — zero zapytań i zapisów…
    if (mode === 'tick') dispatchLive_(exp, true);
    if (mode === 'tick' && repairDue_(startedAt)) { // …chyba że przyszła pora samonaprawy (D-060)
      state.recent = shiftRecent_(state.recent, startedAt);
      repairH1_(state, startedAt);
      saveState_(state);
    }
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
        // D-060: korekta Yahoo jest od razu zapisana (upsert) — to informacja do logu, nie problem do naprawy
        if (nb && Math.abs(nb.c - old.c) > 0.5 * p.pip) log_(mode, p.name, 0, null, 'korekta Yahoo (zapisana) @' + old.ts);
      });
      gapFlags_(bars).forEach(f => flags.push(f));

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

/** Luki w sesji między kolejnymi świecami: 'luka@ts' (D5). ≤ 3 h przy weekendzie/święcie to granica tygodnia (D-039). */
function gapFlags_(bars) {
  const out = [];
  for (let i = 1; i < bars.length; i++) {
    const miss = [];
    for (let t = bars[i - 1].ts + H; t < bars[i].ts; t += H) if (isExpectedBar(t)) miss.push(t);
    const boundary = miss.length && miss.length <= 3 &&
      (!isExpectedBar(miss[0] - H) || !isExpectedBar(miss[miss.length - 1] + H));
    if (miss.length && !boundary) out.push('luka@' + miss[0]);
  }
  return out;
}

function repairDue_(now) {
  const last = Number(PropertiesService.getScriptProperties().getProperty('REPAIR_AT') || 0);
  return now - last >= REPAIR_EVERY_S && now % H >= BURST_S;   // nie w pierwszych 10 min godziny (wtedy pracuje tick)
}

/**
 * D-060: samonaprawa świec H1. Ponownie pobiera ostatnie REPAIR_DAYS dni każdej pary i nadpisuje wszystkie zamknięte świece
 * (upsert, D3): luki, które Yahoo uzupełnił po fakcie, i świece, które skorygował, trafiają do bazy. Flagi pary są liczone
 * od nowa z tego okna — zostaje tylko to, co w danych Yahoo wciąż jest złe (resztę obsługuje warstwa czyszczenia na Macu).
 * Koszt (Z4): 8 zapytań Yahoo i ok. 16 zapisów (2 miesiące × 8 par) + 1 zapis statusu co 6 h ≈ 70 zapisów/dobę.
 */
function repairH1_(state, now) {
  const updated = {}, errors = [];
  PAIRS.forEach(p => {
    try {
      const got = fetchYahoo(p.yahoo, 'period1=' + (now - REPAIR_DAYS * 86400) + '&period2=' + now);
      const bars = got.filter(b => b.ts % H === 0 && b.ts + H <= now - 60);
      if (!bars.length) return;
      writeBars_(p.name, bars);
      const flags = [];
      bars.forEach(b => barFlags(b).forEach(f => flags.push(f + '@' + b.ts)));
      gapFlags_(bars).forEach(f => flags.push(f));
      const ps = state.pairs[p.name] || { lastTs: 0, count: 0, last: [], latencySec: null };
      const before = (ps.flags || []).length;
      bars.forEach(b => setRecent_(state.recent, p.name, b.ts, barFlags(b).length ? 'f' : '1'));
      ps.lastTs = Math.max(ps.lastTs || 0, bars[bars.length - 1].ts);
      ps.flags = flags.slice(-20);
      ps.repairedAt = nowSec();
      state.pairs[p.name] = ps;
      updated[p.name] = { lastTs: ps.lastTs, latencySec: ps.latencySec, count: ps.count, flags: ps.flags, savedAt: ps.savedAt || null,
        repairedAt: ps.repairedAt };
      log_('repair', p.name, bars.length, null, 'samonaprawa ' + REPAIR_DAYS + ' dni: flagi ' + before + ' → ' + ps.flags.length);
    } catch (e) {
      errors.push(p.name + ': ' + e.message);
      log_('repair', p.name, 0, null, 'BŁĄD ' + e.message);
    }
  });
  writeRound_('repair', state, now, { updated: updated, errors: errors, runLatency: null });
  if (!errors.length) PropertiesService.getScriptProperties().setProperty('REPAIR_AT', String(now));
}

/** Audyt po samonaprawie: świeca jest → '1' (albo 'f', gdy Yahoo wciąż podaje ją błędnie); „spóźniona” zostaje (to historia). */
function setRecent_(recent, pair, ts, ch) {
  const i = Math.round((ts - recent.start) / H);
  const str = recent.pairs[pair];
  if (i < 0 || i >= RECENT_H || !str || str[i] === 'l') return;
  recent.pairs[pair] = str.slice(0, i) + ch + str.slice(i + 1);
}

/** Ręcznie (D-060): samonaprawa od razu, bez czekania 6 h. */
function repair() {
  withLock_(() => {
    const state = loadState_();
    const now = nowSec();
    state.recent = shiftRecent_(state.recent, now);
    repairH1_(state, now);
    saveState_(state);
  });
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
      if (r.getResponseCode() === 404) {                 // D-063: Yahoo nie zna tego tickera — ponawianie nic nie da
        const nf = new Error('Yahoo ' + ticker + ': HTTP 404');
        nf.notFound = true;
        throw nf;
      }
      lastErr = 'HTTP ' + r.getResponseCode();
    } catch (e) {
      if (e.notFound) throw e;
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

// ---------- serie dzienne: D1 FX (D-053) i kursy złotówkowe REV (D-063) — ta sama droga, inne listy i kolekcje ----------

const PLN_CODES = ['AED', 'AUD', 'CAD', 'CHF', 'CZK', 'DKK', 'EUR', 'GBP', 'HKD', 'HUF', 'ILS', 'JPY',
  'MXN', 'NOK', 'NZD', 'QAR', 'RON', 'SAR', 'SEK', 'SGD', 'THB', 'TRY', 'USD', 'ZAR'];   // bez RUB (D-063)
const PLN_CANDIDATES = PLN_CODES.map(c => ({ name: c, yahoo: c + 'PLN=X', pip: 0.0001 }));
const PLN_MIN_YEARS = 10;    // R1: „rzadki kurs” — krótsza historia odpada
const PLN_FRESH_WD = 5;      // ostatnia świeca nie starsza niż 5 dni roboczych od oczekiwanej
const PLN_FLAT_MAX = 0.05;   // < 5% dni bez ruchu (zamknięcie = poprzednie albo O=H=L=C) w ostatnich 5 latach
const PLN_FLAT_YEARS = 5;

const SERIES_D1 = { prop: 'd1', collection: 'candles_d1', field: 'd1', key: 'pairs', list: PAIRS, admit: null, slim: false };
// Z4 (D-063): backfill ≈ 20 walut × ~22 lata ≈ 450 zapisów raz; potem ≈ 20 zapisów dziennie + status
const SERIES_PLN = { prop: 'pln', collection: 'candles_pln', field: 'pln', key: 'currencies', list: PLN_CANDIDATES, admit: plnAdmission_, slim: true };

function loadSeries_(series) {
  const raw = PropertiesService.getScriptProperties().getProperty(series.prop);
  const st = raw ? JSON.parse(raw) : { tz: D1_TZ };
  st[series.key] = st[series.key] || {};
  if (series.admit) st.rejected = st.rejected || {};
  return st;
}

/** Script Properties: limit 9 KB na wartość — przy 24 walutach flagi i czas zapisu idą tylko do meta/status (slim). */
function saveSeries_(series, st) {
  let out = st;
  if (series.slim) {
    out = Object.assign({}, st);
    out[series.key] = {};
    Object.keys(st[series.key]).forEach(k => {
      const v = Object.assign({}, st[series.key][k]);
      delete v.flags; delete v.savedAt;
      out[series.key][k] = v;
    });
  }
  PropertiesService.getScriptProperties().setProperty(series.prop, JSON.stringify(out));
}

function loadD1_() { return loadSeries_(SERIES_D1); }
function saveD1_(st) { saveSeries_(SERIES_D1, st); }

/** Ręcznie, raz (D-063): cała historia kursów {WALUTA}PLN=X; waluta bez ≥ 10 lat historii, świeżych notowań albo ruchu
 *  nie jest zapisywana (powód w meta/status.pln.rejected). Można powtórzyć (upsert, reguła liczona od nowa). */
function backfillPLN() { withLock_(() => runSeriesD1_(SERIES_PLN, 'backfill', PLN_CANDIDATES, loadSeries_(SERIES_PLN), nowSec())); }

/** Ręcznie (D-063), tylko odczyt: dlaczego waluta wyszła „Yahoo nie zwraca notowań”. Dla każdej odrzuconej waluty zapisuje w
 *  arkuszu `log` (tryb „PLN diagnoza”): kod HTTP, strefę, liczbę dni, ile ma zamknięcie, ile pełne OHLC, ile o północy,
 *  pierwszy i ostatni dzień oraz godzinę trzech ostatnich znaczników. Bez zapisu do Firestore. */
function diagnosePLN() {
  const st = loadSeries_(SERIES_PLN);
  const names = Object.keys(st.rejected || {});
  const list = PLN_CANDIDATES.filter(p => !names.length || names.indexOf(p.name) >= 0);
  list.forEach(p => {
    let msg;
    try {
      const url = 'https://query1.finance.yahoo.com/v8/finance/chart/' + encodeURIComponent(p.yahoo) + '?interval=1d&range=20y';
      const r = UrlFetchApp.fetch(url, { muteHttpExceptions: true, headers: { 'User-Agent': 'Mozilla/5.0' } });
      if (r.getResponseCode() !== 200) {
        msg = 'HTTP ' + r.getResponseCode();
      } else {
        const res = JSON.parse(r.getContentText()).chart.result[0];
        const tz = (res.meta || {}).exchangeTimezoneName || D1_TZ;
        const ts = res.timestamp || [];
        const q = (res.indicators && res.indicators.quote && res.indicators.quote[0]) || {};
        const has = (a, i) => a && a[i] !== null && a[i] !== undefined;
        let close = 0, full = 0, midnight = 0;
        ts.forEach((t, i) => {
          if (has(q.close, i)) close++;
          if (has(q.open, i) && has(q.high, i) && has(q.low, i) && has(q.close, i)) full++;
          if (localStamp_(t, tz).slice(11) === '00:00:00') midnight++;
        });
        const tail = ts.slice(-3).map(t => localStamp_(t, tz).slice(0, 16)).join(', ');
        msg = 'tz ' + tz + ' · dni ' + ts.length + ' · z zamknięciem ' + close + ' · pełne OHLC ' + full + ' · o północy ' + midnight +
          (ts.length ? ' · od ' + localStamp_(ts[0], tz).slice(0, 10) + ' · ostatnie: ' + tail : '') + ' · powód: ' + ((st.rejected || {})[p.name] || '—');
      }
    } catch (e) {
      msg = 'BŁĄD ' + e.message;
    }
    log_('PLN diagnoza', p.name, 0, null, msg);
  });
}

/** Z tick(): tanio — bez zapytań, gdy każda para ma świecę oczekiwanego dnia albo ostatnia próba była < 15 min temu. */
function tickD1_() { tickSeries_(SERIES_D1); }

/** Z tick() (D-063): to samo dla przyjętych walut REV (tylko te z meta/status.pln.currencies). */
function tickPLN_() { tickSeries_(SERIES_PLN); }

function tickSeries_(series) {
  const st = loadSeries_(series);
  if (!st.backfilled) return;            // najpierw backfill — inaczej liczniki świec nie miałyby sensu
  const now = nowSec();
  const exp = expectedDayD1_(now, st.tz || D1_TZ);
  const items = st[series.key];
  const list = series.admit ? series.list.filter(p => items[p.name]) : series.list;
  const todo = list.filter(p => !(items[p.name] && items[p.name].lastDay >= exp));
  if (!todo.length || now - (st.triedAt || 0) < D1_RETRY_S) return;
  st.triedAt = now;
  saveSeries_(series, st);
  runSeriesD1_(series, 'tick', todo, st, now);
}

function runD1_(mode, todo, st, now) { runSeriesD1_(SERIES_D1, mode, todo, st, now); }

/** Dni robocze między dwoma dniami 'RRRR-MM-DD' (od a wyłącznie do b włącznie). */
function workdaysBetween_(a, b) {
  let n = 0;
  for (let d = b; d > a && n < 400; d = prevDay_(d)) if (isExpectedDay_(d)) n++;
  return n;
}

/** R1 (D-063): czy kurs nie jest „rzadki”. null = przyjęty, inaczej powód po polsku. bars: zamknięte dni (b.day, b.o…b.c). */
function plnAdmission_(bars, now, tz) {
  if (!bars.length) return 'Yahoo nie zwraca notowań';
  const today = localStamp_(now - 60, tz).slice(0, 10);
  const limit = (Number(today.slice(0, 4)) - PLN_MIN_YEARS) + today.slice(4);
  const first = bars[0].day, last = bars[bars.length - 1].day;
  if (first > limit) return 'historia od ' + first + ' — krótsza niż ' + PLN_MIN_YEARS + ' lat';
  const behind = workdaysBetween_(last, expectedDayD1_(now, tz));
  if (behind > PLN_FRESH_WD) return 'brak świeżych notowań (ostatni dzień ' + last + ')';
  const since = (Number(today.slice(0, 4)) - PLN_FLAT_YEARS) + today.slice(4);
  let n = 0, flat = 0;
  for (let i = 1; i < bars.length; i++) {
    if (bars[i].day < since) continue;
    n++;
    const b = bars[i];
    if (b.c === bars[i - 1].c || (b.o === b.h && b.h === b.l && b.l === b.c)) flat++;
  }
  if (n && flat / n >= PLN_FLAT_MAX) return 'dni bez ruchu ' + Math.round(100 * flat / n) + '% w ostatnich ' + PLN_FLAT_YEARS + ' latach';
  return null;
}

function runSeriesD1_(series, mode, todo, st, now) {
  const errors = [];
  const updated = {};
  const dropped = [];
  const items = st[series.key];
  const rejectedBefore = JSON.stringify(st.rejected || {});
  todo.forEach(p => {
    try {
      const params = 'interval=1d&' + (mode === 'backfill' ? 'period1=0&period2=' + now : 'range=10d');
      const got = fetchYahooRaw_(p.yahoo, params, parseYahooD1_);
      const tz = st.tz = got.tz;
      const today = localStamp_(now - 60, tz).slice(0, 10);
      const ps = mode === 'backfill' ? { lastTs: 0, count: 0, last: [] } : (items[p.name] || { lastTs: 0, count: 0, last: [] });
      const flags = [];
      const bars = [];
      got.bars.forEach(b => {
        const loc = localStamp_(b.ts, tz);
        b.day = loc.slice(0, 10);
        if (b.day >= today) return;                                   // dzień w trakcie (D2) — nigdy do bazy
        if (loc.slice(11) !== '00:00:00') { flags.push('ts@' + b.day); return; } // nie świeca dnia — flaga, nie cicha naprawa
        bars.push(b);
      });
      if (series.admit && mode === 'backfill') {                    // D-063: rzadki kurs — bez zapisu, powód w statusie
        const why = series.admit(bars, now, tz);
        if (why) {
          st.rejected[p.name] = why;
          if (items[p.name]) dropped.push(p.name);   // wcześniej przyjęta, teraz odrzucona — znika też z meta/status
          delete items[p.name];
          log_('PLN ' + mode, p.name, 0, null, 'odrzucona: ' + why);
          return;
        }
        delete st.rejected[p.name];
      }
      const from = mode === 'backfill' ? 0 : ps.lastTs - D1_KEEP * 86400;
      const keep = bars.filter(b => b.ts >= from);
      if (!keep.length) { if (flags.length) log_(series.field + ' ' + mode, p.name, 0, null, flags.slice(0, 5).join(' ')); return; }
      keep.forEach(b => {
        if (!(b.o > 0 && b.h > 0 && b.l > 0 && b.c > 0)) flags.push('cena<=0@' + b.day);
        if (b.h < Math.max(b.o, b.c) || b.l > Math.min(b.o, b.c)) flags.push('ohlc@' + b.day);
        const old = (ps.last || []).find(x => x.ts === b.ts);
        if (old && Math.abs(old.c - b.c) > 0.5 * p.pip) flags.push('revised@' + b.day);
      });
      const fresh = keep.filter(b => b.ts > ps.lastTs);
      // ponowienie bez nowego dnia i bez korekty Yahoo — bez zapisu (Z4)
      if (mode === 'tick' && !fresh.length && !flags.some(f => f.startsWith('revised'))) return;
      writeBarsSeries_(series.collection, p.name, keep, tz);
      const newest = keep[keep.length - 1];
      ps.count = mode === 'backfill' ? keep.length : ps.count + fresh.length;
      if (mode === 'backfill' || !ps.firstDay) ps.firstDay = keep[0].day;
      ps.lastTs = Math.max(ps.lastTs, newest.ts);
      ps.lastDay = ps.lastDay && ps.lastDay > newest.day ? ps.lastDay : newest.day;
      ps.last = keep.slice(-D1_KEEP).map(b => ({ ts: b.ts, c: b.c }));
      ps.flags = flags.slice(-10);
      ps.savedAt = nowSec();
      items[p.name] = ps;
      updated[p.name] = { firstDay: ps.firstDay, lastTs: ps.lastTs, lastDay: ps.lastDay, count: ps.count, flags: ps.flags, savedAt: ps.savedAt };
      log_(series.field + ' ' + mode, p.name, fresh.length, null, (ps.firstDay + ' – ' + ps.lastDay + ' ' + flags.slice(0, 5).join(' ')).trim());
    } catch (e) {
      if (e.notFound && series.admit && mode === 'backfill') {   // D-063: Yahoo nie ma kursu do PLN — odrzucona jak rzadki kurs
        st.rejected[p.name] = 'Yahoo nie ma kursu ' + p.yahoo;
        if (items[p.name]) dropped.push(p.name);
        delete items[p.name];
        log_(series.field + ' ' + mode, p.name, 0, null, 'odrzucona: ' + st.rejected[p.name]);
        return;
      }
      errors.push(p.name + ': ' + e.message);
      log_(series.field + ' ' + mode, p.name, 0, null, 'BŁĄD ' + e.message);
    }
  });
  if (mode === 'backfill' && !errors.length) st.backfilled = true;
  saveSeries_(series, st);
  const rejectedChanged = series.admit && JSON.stringify(st.rejected) !== rejectedBefore;
  if (mode === 'tick' && !Object.keys(updated).length && !dropped.length && !errors.length) return;
  const total = Object.keys(items).reduce((s, k) => s + ((items[k] || {}).count || 0), 0);
  const fields = { tz: st.tz || D1_TZ, totalBars: total,
    lastRun: { mode: mode, at: nowSec(), ok: !errors.length, error: errors.join('; ') || null } };
  fields[series.key] = updated;
  const f = series.field;
  const paths = [f + '.tz', f + '.totalBars', f + '.lastRun'].concat(Object.keys(updated).map(k => f + '.' + series.key + '.' + k))
    .concat(dropped.map(k => f + '.' + series.key + '.' + k));   // pole w masce bez wartości = usunięcie (Firestore)
  if (series.admit && (mode === 'backfill' || rejectedChanged)) { fields.rejected = st.rejected; paths.push(f + '.rejected'); }
  const value = {};
  value[f] = toValue_(fields);
  commit_([{ update: { name: DB + '/documents/meta/status', fields: value }, updateMask: { fieldPaths: paths } }]);
  if (errors.length && mode === 'backfill') throw new Error('backfill ' + f + ': ' + errors.join('; '));
}

/** {kolekcja}/{NAZWA}_{RRRR} (rok wg dnia w strefie Yahoo): pola pair, year, tz, bars { ts: [o, h, l, c] } — upsert (D3). */
function writeBarsSeries_(collection, pair, bars, tz) {
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
        name: DB + '/documents/' + collection + '/' + pair + '_' + y,
        fields: { pair: { stringValue: pair }, year: { stringValue: y }, tz: { stringValue: tz }, bars: { mapValue: { fields: fields } } },
      },
      updateMask: { fieldPaths: paths },
      updateTransforms: [{ fieldPath: 'updatedAt', setToServerValue: 'REQUEST_TIME' }],
    };
  }));
}

function writeBarsD1_(pair, bars, tz) { writeBarsSeries_('candles_d1', pair, bars, tz); }

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
