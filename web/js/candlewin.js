// Wycinki świec wokół transakcji (D-010) — czyste funkcje (testy: tests/web).
// Wynik ma tylko ±24 świece wokół transakcji, więc kolejne wycinki dzielą tygodnie albo lata. Narysowane jedno
// za drugim wyglądały jak skoki ceny (D-033) — tu dzielimy je na okna i zaznaczamy przerwę między nimi.
import { H, isExpectedBar } from './session.js';

/** Ile godzin sesji brakuje między świecami a i b (weekend i święta się nie liczą). */
export function sessionHoursBetween(a, b, limit = 4) {
  let n = 0;
  for (let t = a + H; t < b && n < limit; t += H) if (isExpectedBar(t)) n++;
  return n;
}

/** Okna ciągłych świec: [{ from, to }] (indeksy w bars, to wyłącznie). Przerwa = ≥ 4 brakujące godziny sesji. */
export function splitWindows(bars) {
  const out = [];
  let from = 0;
  for (let i = 1; i <= bars.length; i++) {
    if (i === bars.length || sessionHoursBetween(bars[i - 1].ts, bars[i].ts) >= 4) {
      if (i > from) out.push({ from, to: i });
      from = i;
    }
  }
  return out;
}

/**
 * Transakcje, które da się narysować: wejście na istniejącej świecy i wyjście w tym samym oknie.
 * Zwraca { shown: [{ trade, entry, exit, from, to }], hidden } — entry/exit = czas świecy markera, from/to = granice okna.
 */
export function placeTrades(bars, windows, trades) {
  const times = bars.map((b) => b.ts);
  const winOf = new Int32Array(bars.length);
  windows.forEach((w, k) => { for (let i = w.from; i < w.to; i++) winOf[i] = k; });
  const idxAtOrBefore = (t) => {
    let lo = 0, hi = times.length - 1;
    if (!times.length || t < times[0]) return -1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (times[mid] <= t) lo = mid; else hi = mid - 1; }
    return lo;
  };
  const shown = [];
  let hidden = 0;
  for (const tr of trades) {
    const ie = idxAtOrBefore(tr.entry_ts), ix = idxAtOrBefore(tr.exit_ts - 1);
    if (ie < 0 || times[ie] !== tr.entry_ts || ix < 0 || winOf[ie] !== winOf[ix]) { hidden++; continue; }
    shown.push({ trade: tr, entry: times[ie], exit: times[ix], from: times[windows[winOf[ie]].from], to: times[windows[winOf[ie]].to - 1] });
  }
  shown.sort((a, b) => a.entry - b.entry);
  return { shown, hidden };
}

/** Dane dla serii: świece + puste miejsca (whitespace) między oknami, żeby przerwa była widoczna. */
export function seriesData(bars, windows, gapBars = 8) {
  const out = [];
  windows.forEach((w, k) => {
    for (let i = w.from; i < w.to; i++) {
      const b = bars[i];
      out.push({ time: b.ts, open: b.open, high: b.high, low: b.low, close: b.close });
    }
    const next = windows[k + 1];
    if (next) {
      const end = bars[w.to - 1].ts, start = bars[next.from].ts;
      for (let j = 1; j <= gapBars && end + j * H < start; j++) out.push({ time: end + j * H });
    }
  });
  return out;
}
