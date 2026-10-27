// Stan pobieracza `ia5 fetch` (D-031) — czyste funkcje (testy: tests/web). Źródło: runner/heartbeat.fetch.
import { PAIRS } from './metrics.js';
import { ago, esc, num } from './util.js';

const HEARTBEAT_OK_S = 90; // jak config.HEARTBEAT_OK_S (config.js czyta adres strony, więc nie da się go zaimportować w Node)

/** Pobieracz `ia5 fetch` (D-031): pole `fetch` w runner/heartbeat. { online, state, pair, progress, pairs, until, seen }. */
export function fetchState(b, now = Date.now() / 1000) {
  const f = b?.fetch;
  const seen = f?.lastSeen?.seconds ?? 0;
  const online = !!seen && now - seen < HEARTBEAT_OK_S && f.state !== 'offline';
  return { online, seen, state: f?.state, pair: f?.pair, progress: f?.progress, pairs: f?.pairs || {}, until: f?.until, sync: f?.sync };
}

export const pairLabel = (p) => PAIRS[p]?.label || p;

/** Tekst wskaźnika pobierania: co teraz robi i jak daleko. */
export function fetchText(f, now = Date.now() / 1000) {
  if (!f.online) return { state: 'mute', sub: `wyłączone${f.seen ? ' · ' + ago(f.seen) : ''}` };
  const pct = f.progress != null ? ` <span class="mono">${num(f.progress, f.progress >= 99 && f.progress < 100 ? 1 : 0)}%</span>` : '';
  if (f.state === 'komplet') return { state: 'ok', sub: 'komplet · czeka na nowe dni' };
  if (f.state === 'czeka') {
    const left = f.until ? Math.max(0, Math.round((f.until - now) / 60)) : null;
    return { state: 'warn', sub: `${f.pair ? esc(pairLabel(f.pair)) + pct + ' · ' : ''}przerwa${left != null ? ` ${left} min` : ''}` };
  }
  return { state: 'ok', sub: `${esc(pairLabel(f.pair || ''))}${pct}${f.state === 'naprawia' ? ' · dociąga braki' : ''}` };
}

