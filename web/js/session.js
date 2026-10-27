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

/**
 * Audyt świeca po świecy z meta/status.recent (D-027): { start, pairs: { PARA: napis, 1 znak = 1 godzina } }.
 * Znaki z Apps Script: '1' jest, 'l' spóźniona (> 20 min po zamknięciu), 'f' z flagą jakości, '.' brak.
 * Zwraca { hours: [ts…], pairs: { PARA: [stan…] } } tylko do ostatniej zamkniętej godziny;
 * stany: ok, late, flag, missing (oczekiwana, a brak > 20 min po zamknięciu), pending (zamknięta < 20 min temu), closed (poza sesją).
 */
export function recentCells(recent, now, graceS = 20 * 60) {
  if (!recent?.pairs) return null;
  const last = lastClosedTs(now);
  const hours = [];
  for (let ts = recent.start; ts <= last; ts += H) hours.push(ts);
  const pairs = {};
  for (const [p, str] of Object.entries(recent.pairs)) {
    pairs[p] = hours.map((ts, i) => {
      const c = str[i] ?? '.';
      if (c === '1') return 'ok';
      if (c === 'l') return 'late';
      if (c === 'f') return 'flag';
      if (!isExpectedBar(ts)) return 'closed';
      return now - (ts + H) > graceS ? 'missing' : 'pending';
    });
  }
  return { hours, pairs };
}
