// Kalendarz danych dzień po dniu (Stats) — czyste funkcje (testy: tests/web).
// Dane: coverage.json → sources.yahoo.days = { start: 'RRRR-MM-DD', pairs: { PARA: [wartość dnia, …] } } (runner/ia5/coverage.day_map):
//   -1 dzień bez sesji (weekend, święto, sama granica tygodnia) · -2 brak danych · n = brakujące godziny w dziurach ≤ 3 h
//   (uzupełniane do liczenia) · 100 + n = dzień w przerwie w danych (dziura > 3 h, transakcje anulowane — B12).
export const NO_SESSION = -1, NO_DATA = -2, BARRIER = 100;
const RANK = { off: 0, ok: 1, fill: 2, none: 3, gap: 4 };
const DAY = 86400;
const SHORT = ['sty', 'lut', 'mar', 'kwi', 'maj', 'cze', 'lip', 'sie', 'wrz', 'paź', 'lis', 'gru'];
const MONTHS = ['styczeń', 'luty', 'marzec', 'kwiecień', 'maj', 'czerwiec', 'lipiec', 'sierpień', 'wrzesień', 'październik', 'listopad', 'grudzień'];

/** Stan jednego dnia jednej pary: off | ok | fill | gap | none. */
export function dayState(v) {
  if (v == null || v === NO_SESSION) return 'off';
  if (v === NO_DATA) return 'none';
  if (v >= BARRIER) return 'gap';
  return v > 0 ? 'fill' : 'ok';
}

const missingHours = (v) => (v >= BARRIER ? v - BARRIER : v > 0 ? v : 0);

/**
 * Miesiące od najnowszego: [{ key: 'RRRR-MM', label, first: dzień tygodnia 1. dnia (0 = pn), cells: [{ dom, ts, state, pairs: [{ pair, state, hours }] }] }].
 * Stan dnia dla kilku par = najgorszy (przerwa > brak danych > uzupełnione > pełny > bez sesji).
 */
export function calendarMonths(days, pairs) {
  if (!days?.start) return [];
  const t0 = Date.parse(days.start + 'T00:00:00Z') / 1000;
  const n = Math.max(0, ...pairs.map((p) => days.pairs?.[p]?.length || 0));
  const byMonth = new Map();
  for (let i = 0; i < n; i++) {
    const ts = t0 + i * DAY, d = new Date(ts * 1000);
    const key = d.toISOString().slice(0, 7);
    if (!byMonth.has(key)) byMonth.set(key, []);
    const per = pairs.map((p) => {
      const v = days.pairs?.[p]?.[i];
      return { pair: p, state: dayState(v), hours: missingHours(v ?? 0) };
    });
    const state = per.reduce((w, x) => (RANK[x.state] > RANK[w] ? x.state : w), 'off');
    byMonth.get(key).push({ dom: d.getUTCDate(), ts, state, pairs: per.filter((x) => x.state !== 'ok' && x.state !== 'off') });
  }
  return [...byMonth.entries()].reverse().map(([key, cells]) => {
    const y = +key.slice(0, 4), m = +key.slice(5, 7);
    return { key, label: `${MONTHS[m - 1]} ${y}`, short: `${SHORT[m - 1]} ${String(y).slice(2)}`, first: (new Date(Date.UTC(y, m - 1, 1)).getUTCDay() + 6) % 7, cells };
  });
}

/** Podsumowanie: od kiedy dane, ile dni sesji pełnych / z uzupełnieniem / w przerwie / bez danych. */
export function calendarSummary(months) {
  const s = { from: null, to: null, session: 0, ok: 0, fill: 0, gap: 0, none: 0 };
  for (const m of months) for (const c of m.cells) {
    if (c.state === 'off') continue;
    s.session++;
    s[c.state]++;
    if (s.from == null || c.ts < s.from) s.from = c.ts;
    if (s.to == null || c.ts > s.to) s.to = c.ts;
  }
  return s;
}
