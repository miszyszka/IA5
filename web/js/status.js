// Pasek statusu (CLAUDE.md 10.1): nasłuch 2 dokumentów — meta/status i runner/heartbeat (Z2).
import { HEARTBEAT_OK_S } from './config.js';
import { watchDoc } from './fb.js';
import { PAIRS } from './metrics.js';
import { $, ago, dateUTC, esc, local, num, store } from './util.js';

const H = 3600;
const lastClosedTs = (now) => Math.floor((now - 60 - H) / H) * H;
// ta sama logika co apps_script/Code.gs i runner/ia5/session.py
function isExpectedBar(ts) {
  const d = new Date(ts * 1000), day = d.getUTCDay(), hr = d.getUTCHours();
  if (day === 6) return false;
  if (day === 5 && hr >= 21) return false;
  if (day === 0 && hr < 22) return false;
  return true;
}
function expectedTs(now) {
  let ts = lastClosedTs(now);
  for (let i = 0; i < 80 && !isExpectedBar(ts); i++) ts -= H;
  return ts;
}
const median = (a) => { if (!a.length) return null; const s = [...a].sort((x, y) => x - y), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

let status = null, beat = null, err = null;

function set(id, text, color, sub) {
  const tile = $(`#k-${id}`);
  tile.dataset.state = color;
  $('.v', tile).textContent = text;
  if (sub !== undefined) $('.s', tile).innerHTML = sub;
}

function spark(points) {
  if (!points || points.length < 2) return '';
  const w = 120, hh = 26, max = Math.max(...points.map((p) => p.s), 1);
  const d = points.map((p, i) => `${((i / (points.length - 1)) * w).toFixed(1)},${(hh - (p.s / max) * hh).toFixed(1)}`).join(' ');
  return `<svg class="spark" width="${w}" height="${hh}" viewBox="0 0 ${w} ${hh}" aria-hidden="true"><polyline points="${d}"/></svg>`;
}

export function heartbeatState(b = beat) {
  const seen = b?.lastSeen?.seconds ?? 0;
  const online = seen && Date.now() / 1000 - seen < HEARTBEAT_OK_S && b.state !== 'offline';
  return { online, state: b?.state, job: b?.job, seen };
}

function render() {
  const now = Date.now() / 1000;
  if (!status) {
    set('data', err ? 'BRAK POŁĄCZENIA' : '…', err ? 'bad' : 'mute', err ? `Firestore: ${esc(err)}` : '');
  } else {
    const pairs = status.pairs || {};
    const exp = expectedTs(now);
    const lastTs = Math.min(...Object.keys(PAIRS).map((p) => pairs[p]?.lastTs || 0));
    const closed = !isExpectedBar(lastClosedTs(now) + H) && !isExpectedBar(lastClosedTs(now));
    const missing = lastTs >= exp ? 0 : now - (exp + H);
    const sub = `ostatnia świeca ${dateUTC(lastTs, true)} UTC`;
    if (missing <= 0) set('data', closed ? 'RYNEK ZAMKNIĘTY' : 'DZIAŁA', closed ? 'mute' : 'ok', sub);
    else if (missing < 20 * 60) set('data', 'DZIAŁA', 'ok', sub);
    else if (missing < 75 * 60) set('data', 'OPÓŹNIENIE', 'warn', `brak świecy od ${Math.round(missing / 60)} min`);
    else set('data', 'STOI', 'bad', `brak świecy od ${Math.round(missing / 60)} min`);

    const lat = status.latency24h || [];
    const last = lat.length ? lat[lat.length - 1].s : null;
    const med = median(lat.map((x) => x.s));
    set('lat', last == null ? '—' : `${num(last, 0)} s`, 'plain', `${med == null ? '' : `mediana 24 h ${num(med, 0)} s`}${spark(lat)}`);
    set('bars', num(status.totalBars || 0, 0), 'plain', `${Object.keys(pairs).length} par · Yahoo H1`);
    const flags = Object.values(pairs).reduce((s, p) => s + (p.flags || []).length, 0) + ((status.cross || {}).flags || []).length;
    set('flags', String(flags), flags ? 'warn' : 'ok', status.lastRun && !status.lastRun.ok ? `błąd: ${esc(status.lastRun.error)}` : 'kontrola jakości D5');
    $('#pairs-body').innerHTML = Object.keys(PAIRS).map((p) => {
      const s = pairs[p] || {};
      const fl = s.flags || [];
      return `<tr><td>${PAIRS[p].label}</td><td>${s.lastTs ? dateUTC(s.lastTs, true) + ' UTC' : '—'}</td><td>${s.lastTs ? local(s.lastTs) : '—'}</td>
        <td class="num">${s.latencySec ?? '—'}</td><td class="num">${num(s.count || 0, 0)}</td>
        <td class="num" title="${esc(fl.join('\n'))}">${fl.length ? '⚠ ' + fl.length : '0'}</td></tr>`;
    }).join('');
  }
  const hb = heartbeatState();
  if (hb.online) {
    const job = hb.job?.name ? `${esc(hb.job.name)} · ${hb.job.progress ?? 0}%` : hb.state === 'syncing' ? 'synchronizacja danych' : 'czeka na strategie';
    set('mac', hb.state === 'computing' ? 'LICZY' : 'POŁĄCZONY', 'ok', job);
  } else {
    set('mac', 'ROZŁĄCZONY', 'mute', hb.seen ? `ostatnio ${ago(hb.seen)} · uruchom <code>ia5 start</code>` : 'uruchom <code>ia5 start</code> na Macu');
  }
}

export function initStatus() {
  // Firestore przy braku sieci nie zgłasza błędu, tylko czeka — po 12 s mówimy to wprost
  setTimeout(() => { if (!status && !err) { err = 'brak odpowiedzi z Firestore (sieć?)'; render(); } }, 12000);
  watchDoc('meta/status', (d) => { status = d; err = null; render(); }, (e) => { err = e.code || String(e); render(); });
  watchDoc('runner/heartbeat', (d) => { beat = d; store.set('beat', d); render(); }, () => render());
  setInterval(render, 15000);
  render();
}
