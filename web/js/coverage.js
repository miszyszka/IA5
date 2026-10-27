// Mapa pokrycia danych — czyste funkcje (testy: tests/web). Dane: coverage/coverage.json z gałęzi data
// (liczy Mac, runner/ia5/coverage.py) + statusy na żywo z runner/heartbeat.sync w trakcie pobierania.
export const NONE = 0, FULL = 1, PARTIAL = 2, EMPTY = 3, FAILED = 4, INCOMPLETE = 5;
const LIVE = { '.': NONE, o: FULL, '~': PARTIAL, '-': EMPTY, x: FAILED, '!': INCOMPLETE };
export const STATUS_LABEL = { [NONE]: 'nie pobrany', [FULL]: 'pełny', [PARTIAL]: 'w toku', [EMPTY]: 'Dukascopy nie ma danych', [FAILED]: 'błąd pobierania', [INCOMPLETE]: 'pobrany częściowo — brakujące dni dociągną się' };

/** ['2003-05', '2003-06', …] — n miesięcy od start. */
export function monthKeys(start, n) {
  let y = +start.slice(0, 4), m = +start.slice(5, 7);
  const out = [];
  for (let i = 0; i < n; i++) {
    out.push(`${y}-${String(m).padStart(2, '0')}`);
    if (++m === 13) { y++; m = 1; }
  }
  return out;
}

export function monthBounds(key) {
  const y = +key.slice(0, 4), m = +key.slice(5, 7);
  return [Date.UTC(y, m - 1, 1) / 1000, Date.UTC(y + (m === 12), m % 12, 1) / 1000];
}

/**
 * Jedno źródło gotowe do rysowania: { start, keys, pairs: { PARA: { m: [[status, exp, pres, holes, common, thin]], gaps, live } } }.
 * live = statusy z heartbeatu (napis, 1 znak = 1 miesiąc) — mają pierwszeństwo przed opublikowaną mapą,
 * bo opisują stan na dysku Maca teraz. Miesiąc pobrany na żywo, a jeszcze niepoliczony, nie ma liczb luk (null).
 */
export function mergeLive(src, live, pairs) {
  if (!src && !live?.pairs) return null;
  const start = live?.start || src.start;
  const n = Math.max(...pairs.map((p) => Math.max(src?.pairs?.[p]?.m?.length || 0, live?.pairs?.[p]?.length || 0)), 0);
  // opublikowana mapa może zaczynać się od innego miesiąca niż heartbeat — wyrównanie po kluczu
  const offset = src ? monthIndex(src.start, start) : 0;
  const out = {};
  for (const p of pairs) {
    const base = src?.pairs?.[p]?.m || [];
    const lv = live?.pairs?.[p];
    const m = [];
    for (let i = 0; i < n; i++) {
      const row = base[i - offset];
      const ls = lv ? LIVE[lv[i]] : undefined;
      if (ls === undefined) m.push(row ? [...row] : [NONE, null, 0, null, null, null]);
      else if (row && row[0] === ls) m.push([...row]);
      else if (row && ls === PARTIAL && row[0] === FULL) m.push([...row]);
      else m.push([ls, row?.[1] ?? null, (ls === FULL || ls === PARTIAL) ? null : 0, null, null, null]);
    }
    out[p] = { m, gaps: src?.pairs?.[p]?.gaps || [], live: !!lv };
  }
  return { start, keys: monthKeys(start, n), pairs: out, live: !!live?.pairs };
}

/** Ile miesięcy od a do b ('RRRR-MM'). */
export function monthIndex(a, b) {
  return (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7));
}

/** Klasa komórki: stan pliku albo — dla pobranych — natężenie dziur (tylko tej pary). */
export function cellKind(row) {
  const [st, , , holes] = row;
  if (st === NONE) return 'none';
  if (st === FAILED) return 'failed';
  if (st === EMPTY) return 'empty';
  if (st === INCOMPLETE) return 'incomplete';
  if (holes == null) return st === PARTIAL ? 'partial' : 'fresh'; // pobrany na żywo, luki policzy Mac po synchronizacji
  if (holes >= 48) return 'holes3';
  if (holes >= 6) return 'holes2';
  if (holes > 0) return 'holes1';
  return st === PARTIAL ? 'partial' : 'full';
}

/**
 * Wygląd komórki mapy (D-028): wysokość wypełnienia = ile miesiąca jest pobrane, kolor = jak duże dziury.
 * { fill: 0…1, color: ok | h1 (1–5 h) | h2 (6–47 h) | h3 (≥ 48 h) | fresh (pobrany, luki jeszcze niepoliczone),
 *   outline: '' | none (nie pobrany) | failed | incomplete (brakujące dni) | partial (bieżący miesiąc) | empty (brak u Dukascopy) }
 */
export function cellView(row) {
  const [st, exp, , holes, , , skipped] = row;
  if (st === NONE) return { fill: 0, color: 'ok', outline: 'none' };
  if (st === FAILED) return { fill: 0, color: 'ok', outline: 'failed' };
  if (st === EMPTY) return { fill: 0, color: 'ok', outline: 'empty' };
  const color = holes == null ? 'fresh' : holes >= 48 ? 'h3' : holes >= 6 ? 'h2' : holes > 0 ? 'h1' : 'ok';
  if (st === INCOMPLETE) {
    const total = (exp || 0) + (skipped || 0);
    return { fill: total ? Math.max(0.08, (exp || 0) / total) : 0.5, color, outline: 'incomplete' };
  }
  return { fill: 1, color, outline: st === PARTIAL ? 'partial' : '' };
}

/** Podsumowanie pary albo całego źródła (rows = sklejone wiersze miesięcy). pct = obecne / oczekiwane,
 * gdzie oczekiwane obejmują też miesiące niepobrane — to jest „ile jeszcze brakuje”. */
export function summarize(rows) {
  const s = { months: 0, done: 0, incomplete: 0, left: 0, failed: 0, uncounted: 0, exp: 0, pres: 0, holes: 0, common: 0, thin: 0, holeMonths: 0, leftHours: 0, firstData: -1 };
  rows.forEach((r, i) => {
    const [st, exp, pres, holes, common, thin] = r;
    if (st === EMPTY) return;
    s.months++;
    if (s.firstData < 0 && st !== NONE && st !== FAILED) s.firstData = i;
    if (st === INCOMPLETE) { s.incomplete++; s.leftHours += r[6] || 0; }
    if (st === FULL || st === PARTIAL || st === INCOMPLETE) s.done++;
    else { s.left++; s.leftHours += exp || 0; if (st === FAILED) s.failed++; }
    if ((st === FULL || st === PARTIAL || st === INCOMPLETE) && holes == null) { s.uncounted++; return; } // pobrany na żywo, jeszcze bez liczb
    s.exp += exp || 0;
    s.pres += pres || 0;
    s.holes += holes || 0;
    s.common += common || 0;
    s.thin += thin || 0;
    if (holes) s.holeMonths++;
  });
  // wspólne luki (święta, krótkie sesje) to nie brak danych tej pary — nie obniżają pokrycia
  s.pct = s.exp - s.common > 0 ? s.pres / (s.exp - s.common) : null;
  return s;
}

/** Luki zachodzące na miesiąc (klucz 'RRRR-MM'). gaps: [[od, do, godzin, 'w'|'p', w drugim źródle]]. */
export function gapsInMonth(gaps, key) {
  const [a, b] = monthBounds(key);
  return gaps.filter((g) => g[0] < b && g[1] > a);
}

/** Zakres luki krótko: koniec bez daty, gdy ten sam dzień; bez roku, gdy ten sam rok. Czas UTC. */
export function fmtRange(a, b) {
  const iso = (t) => new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' ');
  const A = iso(a), B = iso(b);
  const end = A.slice(0, 10) === iso(b - 1).slice(0, 10) && B.slice(11) !== '00:00' ? B.slice(11) : A.slice(0, 4) === B.slice(0, 4) ? B.slice(5) : B;
  return `${A} → ${end}`;
}

/** Największe dziury (tylko jednej pary) ze wszystkich par. */
export function biggestHoles(pairs, limit = 12) {
  const all = [];
  for (const [p, v] of Object.entries(pairs)) for (const g of v.gaps) if (g[3] === 'p') all.push({ pair: p, g });
  return all.sort((x, y) => y.g[2] - x.g[2] || x.g[0] - y.g[0]).slice(0, limit);
}

/**
 * Podział osi czasu na pasy (od stycznia do grudnia), żeby komórka miała ≥ 7 px tam, gdzie się da.
 * Zwraca { bands: [[od, do)], cw } — indeksy miesięcy i szerokość komórki w px (min. 4, wtedy przewijanie).
 */
export function layoutBands(keys, width, maxBands = 6) {
  const n = keys.length;
  const want = Math.max(1, Math.min(maxBands, Math.ceil((n * 7) / Math.max(width, 1))));
  const jan = keys.map((k, i) => (i === 0 || k.endsWith('-01') ? i : -1)).filter((i) => i >= 0);
  const bands = [];
  let from = 0;
  for (let b = 1; b < want; b++) { // cięcie na styczniu najbliższym równemu podziałowi
    const target = Math.round((n * b) / want);
    const cut = jan.reduce((best, i) => (Math.abs(i - target) < Math.abs(best - target) ? i : best), jan[0]);
    if (cut > from) { bands.push([from, cut]); from = cut; }
  }
  bands.push([from, n]);
  const longest = Math.max(...bands.map(([a, b]) => b - a));
  const years = Math.max(...bands.map(([a, b]) => new Set(keys.slice(a, b).map((k) => k.slice(0, 4))).size));
  const cw = Math.max(4, Math.min(26, Math.floor((width - years * 3) / longest)));
  return { bands, cw };
}
