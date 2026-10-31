// Mapa pokrycia danych — czyste funkcje (testy: tests/web). Dane: coverage/coverage.json z gałęzi data
// (liczy Mac, runner/ia5/coverage.py) — świece Yahoo, jedyne źródło (D-039).
export const NONE = 0, FULL = 1, PARTIAL = 2;
export const STATUS_LABEL = { [NONE]: 'brak świec', [FULL]: 'pełny', [PARTIAL]: 'w toku' };

/** ['2024-11', '2024-12', …] — n miesięcy od start. */
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

/** Źródło gotowe do rysowania: { start, keys, pairs: { PARA: { m: [[status, exp, pres, holes, common, 0, 0]], gaps } } }. */
export function sourceView(src, pairs) {
  if (!src?.pairs) return null;
  const n = Math.max(0, ...pairs.map((p) => src.pairs[p]?.m?.length || 0));
  const out = {};
  for (const p of pairs) {
    const m = src.pairs[p]?.m || [];
    out[p] = { m: Array.from({ length: n }, (_, i) => (m[i] ? [...m[i]] : [NONE, null, 0, 0, 0, 0, 0])), gaps: src.pairs[p]?.gaps || [] };
  }
  return { start: src.start, keys: monthKeys(src.start, n), pairs: out };
}

/** Ile miesięcy od a do b ('RRRR-MM'). */
export function monthIndex(a, b) {
  return (+b.slice(0, 4) - +a.slice(0, 4)) * 12 + (+b.slice(5, 7) - +a.slice(5, 7));
}

/**
 * Wygląd komórki mapy: kolor = jak duże dziury (tylko tej pary).
 * { fill: 0…1, color: ok | h1 (1–5 h) | h2 (6–47 h) | h3 (≥ 48 h), outline: '' | none (brak świec) | partial (bieżący miesiąc) }
 */
export function cellView(row) {
  const [st, , , holes] = row;
  if (st === NONE) return { fill: 0, color: 'ok', outline: 'none' };
  const color = holes >= 48 ? 'h3' : holes >= 6 ? 'h2' : holes > 0 ? 'h1' : 'ok';
  return { fill: 1, color, outline: st === PARTIAL ? 'partial' : '' };
}

/** Podsumowanie pary albo całego źródła (rows = sklejone wiersze miesięcy). pct = obecne / oczekiwane bez luk wspólnych. */
export function summarize(rows) {
  const s = { months: 0, done: 0, exp: 0, pres: 0, holes: 0, common: 0, holeMonths: 0 };
  for (const [st, exp, pres, holes, common] of rows) {
    if (st === NONE) continue;
    s.months++;
    s.done++;
    s.exp += exp || 0;
    s.pres += pres || 0;
    s.holes += holes || 0;
    s.common += common || 0;
    if (holes) s.holeMonths++;
  }
  // granica tygodnia i luki bez ruchu to nie brak danych — nie obniżają pokrycia
  s.pct = s.exp - s.common > 0 ? s.pres / (s.exp - s.common) : null;
  return s;
}

/** Luki zachodzące na miesiąc (klucz 'RRRR-MM'). gaps: [[od, do, godzin, 'w'|'q'|'p', -1]]. */
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

/** Największe dziury (brak danych) ze wszystkich par. */
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
