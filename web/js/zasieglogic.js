// Zakładka Zasięg (D-076) — czyste obliczenia do widoku (bez DOM), testowane w Node (tests/web/zasieg.test.mjs).

export const LABEL = { EURUSD: 'EUR/USD', USDJPY: 'USD/JPY', GBPUSD: 'GBP/USD', EURGBP: 'EUR/GBP', AUDUSD: 'AUD/USD', USDCHF: 'USD/CHF', USDCAD: 'USD/CAD', EURJPY: 'EUR/JPY' };

/** Liczba miejsc po przecinku ceny pary (JPY: 3, reszta: 5). */
export const priceDecimals = (pair) => (pair.endsWith('JPY') ? 3 : 5);

export function fmtPrice(pair, x) {
  if (x == null || !Number.isFinite(x)) return '—';
  return x.toLocaleString('pl-PL', { minimumFractionDigits: priceDecimals(pair), maximumFractionDigits: priceDecimals(pair) });
}

export const fmtPips = (x, d = 0) => (x == null || !Number.isFinite(x) ? '—' : `${x.toLocaleString('pl-PL', { maximumFractionDigits: d, minimumFractionDigits: d })} pips`);

/** Przedział w pipsach: „147–327 pips”. */
export const fmtRange = (a, b) => (a == null || b == null ? '—' : `${Math.round(a).toLocaleString('pl-PL')}–${Math.round(b).toLocaleString('pl-PL')} pips`);

/** Stan pary w jednym słowie: czeka na wybicie / ściśnięcie (cel za daleko) / normalnie. */
export function boxState(box) {
  if (!box) return { key: 'none', word: 'brak H1', tone: 'mute' };
  if (box.armed) return { key: 'armed', word: 'ściśnięcie — czeka na wybicie', tone: 'warn' };
  if (box.squeezed) return { key: 'squeezed', word: 'ściśnięcie — cel poza zasięgiem', tone: 'mute' };
  return { key: 'normal', word: 'bez ściśnięcia', tone: 'mute' };
}

/** Zdanie poziomu wybicia: „Kupno po zamknięciu godziny nad X · SL Y · TP Z (+a / −b pips)”. */
export function sideLine(pair, side, dir) {
  if (!side) return '';
  const verb = dir > 0 ? 'Kupno po zamknięciu godziny nad' : 'Sprzedaż po zamknięciu godziny pod';
  return `${verb} ${fmtPrice(pair, side.trigger)} · SL ${fmtPrice(pair, side.sl)}${side.sl_mid ? ' (połowa pudełka)' : ''} · TP ${fmtPrice(pair, side.tp)}`
    + ` (+${fmtPips(side.tp_pips)} / −${fmtPips(side.risk_pips)})`;
}

/** Pary posortowane: najpierw gotowe do wybicia, potem najciaśniejsze pudełka. */
export function orderPairs(pairs) {
  const rank = (x) => (x.box?.armed ? 0 : x.box?.squeezed ? 1 : 2);
  return Object.values(pairs || {}).sort((a, b) => rank(a) - rank(b) || (a.box?.pct ?? 101) - (b.box?.pct ?? 101) || a.pair.localeCompare(b.pair));
}

/** Jakość modelu w jednym zdaniu (OOS). */
export function qualityLine(q) {
  if (!q || !q.n) return 'Jakość modelu: za mało historii do oceny.';
  const better = q.better_pct >= 0 ? `o ${Math.round(q.better_pct)}% mniejszy błąd niż „średni zakres z 20 dni”` : `o ${Math.round(-q.better_pct)}% większy błąd niż „średni zakres z 20 dni”`;
  return `Na ostatnich 25% historii (${q.n.toLocaleString('pl-PL')} dni × pary): ${better}; rzeczywisty zasięg 3 dni mieścił się w paśmie 80% w ${Math.round(q.band80)}% dni.`;
}

/** Wynik sygnału do kolumny tabeli. */
export function signalTone(s) {
  if (s.status === 'TP') return 'pos';
  if (s.status === 'SL') return 'neg';
  return '';
}
