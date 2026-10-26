// Drobne narzędzia: DOM, formatowanie, powiadomienia, magazyn stanu.

export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'html') el.innerHTML = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat()) if (c != null && c !== false) el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return el;
}

export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

const nf = (d) => new Intl.NumberFormat('pl-PL', { minimumFractionDigits: d, maximumFractionDigits: d });
export function num(x, d = 2) {
  if (x == null || Number.isNaN(x)) return '—';
  if (!Number.isFinite(x)) return '∞';
  return nf(d).format(x);
}
export const signed = (x, d = 2) => (x == null || Number.isNaN(x) ? '—' : (x > 0 ? '+' : '') + num(x, d));
export const pct = (x, d = 1) => (x == null ? '—' : num(x * 100, d) + '%');
export const cls = (x) => (x == null || Number.isNaN(x) ? '' : x > 0 ? 'pos' : x < 0 ? 'neg' : '');

export function dateUTC(ts, time = false) {
  if (!ts) return '—';
  const s = new Date(ts * 1000).toISOString();
  return time ? s.slice(0, 16).replace('T', ' ') : s.slice(0, 10);
}
export function local(ts) {
  return ts ? new Date(ts * 1000).toLocaleString('pl-PL', { dateStyle: 'short', timeStyle: 'short' }) : '—';
}
export function ago(ts) {
  const s = Date.now() / 1000 - ts;
  if (s < 90) return `${Math.round(s)} s temu`;
  if (s < 5400) return `${Math.round(s / 60)} min temu`;
  if (s < 129600) return `${Math.round(s / 3600)} h temu`;
  return `${Math.round(s / 86400)} dni temu`;
}

export function toast(msg, kind = 'info', ms = 4000) {
  const box = $('#toasts');
  const el = h('div', { class: `toast ${kind}`, role: 'status' }, msg);
  box.append(el);
  setTimeout(() => el.classList.add('out'), ms);
  setTimeout(() => el.remove(), ms + 400);
}

export function download(name, text, type = 'text/plain') {
  const a = h('a', { href: URL.createObjectURL(new Blob([text], { type: `${type};charset=utf-8` })), download: name });
  document.body.append(a); a.click(); a.remove();
}

export async function copy(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch { return false; }
}

/** Okno potwierdzenia. Zwraca Promise<boolean>. */
export function confirmDialog(title, body, okLabel = 'Tak', danger = false) {
  return new Promise((resolve) => {
    const dlg = h('dialog', { class: 'modal small' },
      h('h3', {}, title), h('p', {}, body),
      h('div', { class: 'row end' },
        h('button', { class: 'btn ghost', onclick: () => { dlg.close(); resolve(false); } }, 'Anuluj'),
        h('button', { class: `btn ${danger ? 'danger' : 'accent'}`, onclick: () => { dlg.close(); resolve(true); } }, okLabel)));
    dlg.addEventListener('close', () => { dlg.remove(); resolve(false); });
    document.body.append(dlg);
    dlg.showModal();
  });
}

/** Minimalny magazyn stanu z subskrypcjami. */
const subs = new Map();
export const store = {
  state: {},
  set(key, value) { this.state[key] = value; (subs.get(key) || []).forEach((f) => f(value)); (subs.get('*') || []).forEach((f) => f(key, value)); },
  on(key, fn) { if (!subs.has(key)) subs.set(key, []); subs.get(key).push(fn); return () => subs.set(key, subs.get(key).filter((f) => f !== fn)); },
};
