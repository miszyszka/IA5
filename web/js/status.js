// Stan systemu w nagłówku (CLAUDE.md 10.1): Dane i Mac obok siebie, jeden kafelek par, flagi tylko gdy są.
// Nasłuch 2 dokumentów — meta/status i runner/heartbeat (Z2). Szczegóły: zakładka Stats (stats.js).
import { HEARTBEAT_OK_S } from './config.js';
import { watchDoc } from './fb.js';
import { fetchState, fetchText, pairLabel } from './downloader.js';
import { healthView, problemWord } from './health.js';
import { PAIRS } from './metrics.js';
import { elapsed, expectedTs, H, isExpectedBar, lastClosedTs, nextClose, waitingSince } from './session.js';
import { $, ago, dateUTC, esc, num, store } from './util.js';

export { fetchState };

const hm = (ts) => new Date(ts * 1000).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' });
function dayWord(ts) {
  const d = new Date(ts * 1000), y = new Date(Date.now() - 864e5);
  const same = (a, b) => a.toDateString() === b.toDateString();
  return same(d, new Date()) ? '' : same(d, y) ? 'wczoraj ' : d.toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' }) + ' ';
}
const clock = (left) => {
  const hh = Math.floor(left / 3600), mm = Math.floor((left % 3600) / 60), ss = left % 60;
  return `${hh ? hh + ':' + String(mm).padStart(2, '0') : mm}:${String(ss).padStart(2, '0')}`;
};

let status = null, beat = null, err = null;

export function heartbeatState(b = beat) {
  const seen = b?.lastSeen?.seconds ?? 0;
  const online = seen && Date.now() / 1000 - seen < HEARTBEAT_OK_S && b.state !== 'offline';
  return { online, state: b?.state, job: b?.job, seen };
}

/** Stan danych: { state: ok|warn|bad|mute, word, lastTs, missingMin }. */
export function dataState(s = status, now = Date.now() / 1000) {
  if (!s) return { state: err ? 'bad' : 'mute', word: err ? 'brak połączenia' : '…' };
  const pairs = s.pairs || {};
  const lastTs = Math.min(...Object.keys(PAIRS).map((p) => pairs[p]?.lastTs || 0));
  const exp = expectedTs(now);
  const closed = !isExpectedBar(lastClosedTs(now) + H) && !isExpectedBar(lastClosedTs(now));
  const missing = lastTs >= exp ? 0 : now - (exp + H);
  if (missing <= 0 && closed) return { state: 'mute', word: 'rynek zamknięty', lastTs };
  if (missing < 20 * 60) return { state: 'ok', word: 'działa', lastTs };
  if (missing < 75 * 60) return { state: 'warn', word: 'opóźnienie', lastTs, missingMin: Math.round(missing / 60) };
  return { state: 'bad', word: 'stoi', lastTs, missingMin: Math.round(missing / 60) };
}

export const flagCount = (s = status) => !s ? 0
  : Object.values(s.pairs || {}).reduce((n, p) => n + (p.flags || []).length, 0) + ((s.cross || {}).flags || []).length;

function setInd(id, state, sub, title) {
  const el = $(`#ind-${id}`);
  el.dataset.state = state;
  $('.s', el).innerHTML = sub;
  el.title = title;
}

function renderData() {
  const d = dataState();
  const now = Date.now() / 1000;
  if (!status) { setInd('data', d.state, d.word, err ? `Firestore: ${err}` : 'Łączenie z Firestore…'); return; }
  const last = d.lastTs ? `${dayWord(d.lastTs)}${hm(d.lastTs)}–${hm(d.lastTs + H)}` : '—';
  let sub;
  // D-033: gdy wybije pełna godzina — czerwony zegar, dopóki wszystkie pary nie mają nowej świecy
  const since = Math.min(...Object.keys(PAIRS).map((p) => waitingSince(status.pairs?.[p]?.lastTs, now) ?? Infinity));
  const waitN = Object.keys(PAIRS).filter((p) => waitingSince(status.pairs?.[p]?.lastTs, now) != null).length;
  if (d.state === 'ok' && Number.isFinite(since)) sub = `${last}<span class="wait"> · czeka ${waitN}/${Object.keys(PAIRS).length} <span class="mono">${elapsed(since, now)}</span></span>`;
  else if (d.state === 'ok') sub = `${last}<span class="cd"> · nowa za <span class="mono">${clock(Math.max(0, Math.round(nextClose(now) - now)))}</span></span>`;
  else if (d.state === 'mute') sub = `rynek zamknięty · ${last}`;
  else sub = `${d.word} · brak świecy od ${d.missingMin} min`;
  setInd('data', d.state, sub,
    `Dane (Yahoo → Firestore): ${d.word}\nostatnia świeca ${d.lastTs ? dateUTC(d.lastTs, true) + ' UTC' : '—'}\nszczegóły: zakładka Stats`);
}

function renderMac() {
  const hb = heartbeatState();
  if (hb.online) {
    const what = hb.state === 'computing' ? `liczy${hb.job?.name ? ` · ${esc(hb.job.name)}` : ''} · <span class="mono">${hb.job?.progress ?? 0}%</span>`
      : hb.state === 'syncing' ? 'przygotowuje dane' : 'połączony · liczy na pobranych';
    setInd('mac', 'ok', what, `Mac (ia5 start — liczenie strategii): połączony\n${beat?.host ? 'host ' + beat.host : ''}`);
  } else {
    setInd('mac', 'mute', `rozłączony${hb.seen ? ' · ' + ago(hb.seen) : ''}`, 'Mac rozłączony — uruchom „ia5 start” w terminalu');
  }
}

function renderFetch() {
  const f = fetchState(beat);
  const t = fetchText(f);
  const per = Object.entries(f.pairs).map(([p, v]) => `${pairLabel(p)} ${num(v, 1)}%`).join('\n');
  setInd('fetch', t.state, t.sub, f.online
    ? `Pobieranie Dukascopy (ia5 fetch): para po parze do końca\n${per || ''}\nliczenie bierze tylko zatwierdzone miesiące`
    : 'Pobieracz wyłączony — uruchom „ia5 fetch” w osobnym terminalu');
}

function renderFlags() {
  const el = $('#ind-flags');
  if (status?.health) { // przegląd zdrowia z Maca (D-023) — problemy zamiast samych flag Yahoo
    const hv = healthView(status.health, Date.now() / 1000, heartbeatState().online);
    el.hidden = !hv.problems;
    el.dataset.state = hv.state;
    el.textContent = hv.problems ? `${hv.problems} ${problemWord(hv.problems)}` : '';
    el.title = hv.summary;
    return;
  }
  el.hidden = true; // bez przeglądu zdrowia nic nie pokazujemy (flagi Yahoo są w audycie świec, D-027)
}

function renderPairs() {
  const codes = [...new Set(Object.keys(PAIRS).flatMap((p) => [p.slice(0, 3), p.slice(3)]))];
  const tile = $('#pairs-tile');
  tile.title = Object.values(PAIRS).map((p) => p.label).join(', ');
  tile.innerHTML = `<b>${Object.keys(PAIRS).length} par</b><span class="ccy">${codes.join(' ')}</span>`;
}

function render() {
  renderData();
  renderMac();
  renderFetch();
  renderFlags();
}

export function initStatus() {
  renderPairs();
  // Firestore przy braku sieci nie zgłasza błędu, tylko czeka — po 12 s mówimy to wprost
  setTimeout(() => { if (!status && !err) { err = 'brak odpowiedzi z Firestore (sieć?)'; render(); } }, 12000);
  watchDoc('meta/status', (d) => { status = d; err = null; store.set('status', d); render(); },
    (e) => { err = e.code || String(e); store.set('statusError', err); render(); });
  watchDoc('runner/heartbeat', (d) => { beat = d; store.set('beat', d); render(); }, () => render());
  setInterval(render, 15000);
  setInterval(renderData, 1000);
  render();
}
