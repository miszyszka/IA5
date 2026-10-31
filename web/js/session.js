// Kalendarz sesji FX i dziennik świec — czyste funkcje (testy: tests/web).
// Ta sama logika sesji co apps_script/Code.gs i runner/ia5/session.py.
export const H = 3600;
const DAY = 86400;

export const lastClosedTs = (now) => Math.floor((now - 60 - H) / H) * H;

/** Czy świeca otwarta o ts musi istnieć (szerokie okno weekendu: czas letni i zimowy). */
export function isExpectedBar(ts) {
  const d = new Date(ts * 1000), day = d.getUTCDay(), hr = d.getUTCHours();
  if (day === 6) return false;
  if (day === 5 && hr >= 21) return false;
  if (day === 0 && hr < 22) return false;
  // święta FX: 24.12 od 21:00 do 25.12 22:00 UTC i 31.12 od 21:00 do 1.01 22:00 UTC — rynek nieczynny (D-028)
  const mo = d.getUTCMonth() + 1, dom = d.getUTCDate();
  if (((mo === 12 && dom === 24) || (mo === 12 && dom === 31)) && hr >= 21) return false;
  if (((mo === 12 && dom === 25) || (mo === 1 && dom === 1)) && hr < 22) return false;
  return true;
}

/** Najnowsza świeca, której oczekujemy w bazie. */
export function expectedTs(now) {
  let ts = lastClosedTs(now);
  for (let i = 0; i < 80 && !isExpectedBar(ts); i++) ts -= H;
  return ts;
}

/** Najbliższe zamknięcie świecy w godzinach rynku. */
export function nextClose(now) {
  let open = Math.floor(now / H) * H;
  for (let i = 0; i < 80 && !isExpectedBar(open); i++) open += H;
  return open + H;
}

export const dayKey = (ts) => new Date(ts * 1000).toISOString().slice(0, 10);

/** Ile zamkniętych świec danego dnia (UTC) powinno być w bazie na chwilę `now`. */
export function expectedOnDay(key, now) {
  const start = Date.parse(key + 'T00:00:00Z') / 1000;
  const last = lastClosedTs(now);
  let n = 0;
  for (let ts = start; ts < start + DAY && ts <= last; ts += H) if (isExpectedBar(ts)) n++;
  return n;
}

/**
 * Dziennik dzień po dniu, od najnowszego. daily = meta/status.daily: { 'RRRR-MM-DD': { PARA: liczba } }.
 * Zwraca [{ day, counts, total, expected, missing, open, closed }]:
 * expected = oczekiwane świece × liczba par, missing = suma braków (nadmiar nie znosi braku innej pary),
 * open = dzień w toku, closed = dzień bez handlu (sobota).
 */
export function dailyRows(daily, pairs, now, days = 30) {
  const out = [];
  const today = Date.parse(dayKey(now) + 'T00:00:00Z') / 1000;
  for (let i = 0; i < days; i++) {
    const day = dayKey(today - i * DAY);
    const exp = expectedOnDay(day, now);
    const counts = {};
    let total = 0, missing = 0;
    for (const p of pairs) {
      const c = daily?.[day]?.[p] || 0;
      counts[p] = c;
      total += c;
      missing += Math.max(0, exp - c);
    }
    out.push({ day, counts, total, expectedPerPair: exp, expected: exp * pairs.length, missing,
      open: i === 0, closed: exp === 0 && total === 0 });
  }
  return out;
}

/** Flaga z Apps Script („luka@1793016000”, „revised@…”, „ohlc@…”) → { kind, ts }. */
export function parseFlag(f) {
  const m = /^(.+)@(\d+)$/.exec(String(f));
  return m ? { kind: m[1], ts: +m[2] } : { kind: String(f), ts: null };
}

export const FLAG_LABEL = {
  luka: 'luka w sesji', revised: 'Yahoo poprawiło świecę', ohlc: 'high/low poza open/close',
  'cena<=0': 'cena ≤ 0', ts: 'czas nie na pełnej godzinie',
};

export const BOUNDARY_H = 3; // D-039: Yahoo otwiera tydzień 1–2 h później niż kalendarz — to nie brak danych

/** Czy brakuje tylko pierwszych ≤ 3 zamkniętych godzin po weekendzie albo święcie (granica tygodnia, jak clean.py). */
export function weekOpenGrace(lastTs, now) {
  if (!lastTs || now - lastTs > 5 * DAY) return false;
  const missing = [];
  for (let t = lastTs + H; t <= Math.floor((now - H) / H) * H && missing.length <= BOUNDARY_H; t += H) if (isExpectedBar(t)) missing.push(t);
  return missing.length > 0 && missing.length <= BOUNDARY_H && !isExpectedBar(missing[0] - H);
}

/**
 * Od kiedy para czeka na świecę (D-033): moment zamknięcia najstarszej oczekiwanej świecy po lastTs, która już się
 * zamknęła (pełna godzina wybiła). null = para ma wszystko. Zegar startuje równo o pełnej godzinie, nie po 60 s z D2.
 */
export function waitingSince(lastTs, now) {
  if (weekOpenGrace(lastTs, now)) return null;
  const cur = Math.floor(now / H) * H; // otwarcie trwającej świecy
  let ts = Math.max((lastTs || 0) + H, cur - 14 * 24 * H);
  for (; ts < cur; ts += H) if (isExpectedBar(ts)) return ts + H;
  return null;
}

/** Czas od `since` do `now` krótko: 0:42, 12:05, 1:07:12; short=true powyżej godziny: 1h07. */
export function elapsed(since, now, short = false) {
  const s = Math.max(0, Math.floor(now - since));
  const hh = Math.floor(s / 3600), mm = Math.floor((s % 3600) / 60), ss = s % 60;
  if (short && hh) return `${hh}h${String(mm).padStart(2, '0')}`;
  return hh ? `${hh}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}` : `${mm}:${String(ss).padStart(2, '0')}`;
}

/**
 * Audyt ostatniej doby (D-033): n zamkniętych godzin + trwająca godzina, dla każdej pary.
 * recent = meta/status.recent, pairsSt = meta/status.pairs (lastTs — gdy świeca jest nowsza niż napis audytu).
 * Zwraca { hours: [ts…], pairs: { PARA: [{ st, since }] } }; stany: ok, late, flag, closed (rynek zamknięty),
 * now (godzina trwa), wait (pełna godzina wybiła, świecy jeszcze nie ma — czerwony zegar od `since`),
 * allgap (brak we ≥ 75% par dłużej niż 20 min — rynek nieczynny albo przerwa Yahoo; zegar też biegnie).
 */
export function auditCells(recent, pairsSt, now, n = 24, graceS = 20 * 60) {
  if (!recent?.pairs) return null;
  const cur = Math.floor(now / H) * H;
  const hours = [];
  for (let k = n; k >= 0; k--) hours.push(cur - k * H);
  const names = Object.keys(recent.pairs);
  const code = (p, ts) => {
    const i = Math.round((ts - recent.start) / H);
    const c = i >= 0 ? recent.pairs[p][i] : undefined;
    if (c && c !== '.') return c;
    return (pairsSt?.[p]?.lastTs ?? 0) >= ts && (c === undefined || ts > (pairsSt?.[p]?.lastTs ?? 0) - 3 * H) ? '1' : '.';
  };
  const allGap = hours.map((ts) => names.length >= 3 && names.filter((p) => code(p, ts) === '.').length >= 0.75 * names.length);
  const pairs = {};
  for (const p of names) {
    pairs[p] = hours.map((ts, i) => {
      if (ts === cur) return { st: 'now' };
      const c = code(p, ts);
      if (c === '1') return { st: 'ok' };
      if (c === 'l') return { st: 'late' };
      if (c === 'f') return { st: 'flag' };
      if (!isExpectedBar(ts)) return { st: 'closed' };
      return { st: allGap[i] && now - (ts + H) > graceS ? 'allgap' : 'wait', since: ts + H };
    });
  }
  return { hours, pairs };
}
