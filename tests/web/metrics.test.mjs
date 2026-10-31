// node --test tests/web — logika dashboardu bez przeglądarki
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { checkStrategyCode, filterTrades, mergeStrategies, simulateEquity, summarize } from '../../web/js/metrics.js';

test('kapitał = Python (runner/ia5/portfolio.py) dla każdego depozytu', () => {
  const fx = JSON.parse(readFileSync(process.env.IA5_EQUITY_FIXTURE, 'utf8'));
  for (const [pct, expected] of Object.entries(fx.expected)) {
    const c = simulateEquity(fx.trades, +pct);
    assert.ok(Math.abs(c.final - expected.final) < 1e-6, `depozyt ${pct}%: ${c.final} != ${expected.final}`);
    assert.equal(c.skipped, expected.skipped);
  }
});

test('filtry i podsumowanie', () => {
  const t = [{ pair: 'EURUSD', dir: 1, sample: 'IS', entry_ts: 1, pips_net: 10, r_net: 1 },
    { pair: 'USDJPY', dir: -1, sample: 'OOS', entry_ts: 2, pips_net: -5, r_net: -0.5 }];
  assert.equal(filterTrades(t, { pairs: new Set(['EURUSD']) }).length, 1);
  assert.equal(filterTrades(t, { dir: 'short' })[0].pair, 'USDJPY');
  assert.equal(filterTrades(t, { sample: 'OOS' }).length, 1);
  const s = summarize(t);
  assert.equal(s.trades, 2); assert.equal(s.winRate, 0.5); assert.equal(s.expPips, 2.5); assert.equal(s.pf, 2);
});

test('lista: kolejka Firestore + wyniki, usunięte znikają od razu', () => {
  const idx = [{ id: 'a', name: 'A', created: 10 }, { id: 'b', name: 'B', created: 20 }];
  const docs = { b: { status: 'do_usuniecia' }, c: { name: 'C', status: 'liczy_sie', createdAt: 30 }, a: { status: 'do_policzenia' } };
  const out = mergeStrategies(idx, docs);
  assert.deepEqual(out.map((s) => [s.id, s.state]), [['c', 'running'], ['a', 'queued']]);
  assert.equal(mergeStrategies(idx, {}, new Set(['a'])).length, 1);
});

test('kontrola kodu w przeglądarce', () => {
  const ok = 'HYPOTHESIS = "x"\ndef signals(df, p, ind):\n    return ind.cross_above(df.close, ind.sma(df.close, 20)).astype("int8")\n';
  assert.deepEqual(checkStrategyCode(ok), { errors: [], warnings: [] });
  const bad = checkStrategyCode('import os\ndef signals(df, p, ind):\n    return df.close.shift(-1) > df.close.mean()\n');
  assert.equal(bad.errors.length, 2);
  assert.ok(bad.warnings.some((w) => w.includes('HYPOTHESIS')) && bad.warnings.some((w) => w.includes('całej serii')));
});

test('kalendarz sesji i flagi Yahoo', async () => {
  const { isExpectedBar, parseFlag } = await import('../../web/js/session.js');
  assert.equal(isExpectedBar(Date.UTC(2026, 9, 31, 12) / 1000), false); // sobota
  assert.equal(isExpectedBar(Date.UTC(2026, 9, 30, 12) / 1000), true);
  assert.deepEqual(parseFlag('luka@1793016000'), { kind: 'luka', ts: 1793016000 });
});
test('mapa pokrycia: widok źródła, podsumowanie, luki w miesiącu', async () => {
  const c = await import('../../web/js/coverage.js');
  assert.deepEqual(c.monthKeys('2003-11', 3), ['2003-11', '2003-12', '2004-01']);
  assert.equal(c.monthIndex('2003-05', '2004-02'), 9);
  const src = { start: '2024-01', pairs: { EURUSD: { m: [[1, 500, 495, 2, 3, 0, 0], [0, 480, 0, 0, 0, 0, 0], [2, 100, 100, 0, 0, 0, 0]],
    gaps: [[Date.UTC(2024, 0, 31, 22) / 1000, Date.UTC(2024, 1, 1, 2) / 1000, 4, 'p', -1]] } } };
  const m = c.sourceView(src, ['EURUSD', 'USDJPY']);
  assert.deepEqual(m.keys, ['2024-01', '2024-02', '2024-03']);
  assert.deepEqual(m.pairs.USDJPY.m[0], [0, null, 0, 0, 0, 0, 0]);   // para bez danych w mapie — puste miesiące
  assert.equal(c.sourceView(null, ['EURUSD']), null);
  const s = c.summarize(src.pairs.EURUSD.m);
  assert.equal(s.done, 2); assert.equal(s.exp, 600); assert.equal(s.pres, 595); assert.equal(s.holes, 2);
  assert.ok(Math.abs(s.pct - 595 / (600 - 3)) < 1e-12); // wspólne luki nie obniżają pokrycia
  // luka przez północ 31.01→01.02 należy do obu miesięcy
  assert.equal(c.gapsInMonth(src.pairs.EURUSD.gaps, '2024-01').length, 1);
  assert.equal(c.gapsInMonth(src.pairs.EURUSD.gaps, '2024-02').length, 1);
  assert.equal(c.gapsInMonth(src.pairs.EURUSD.gaps, '2024-03').length, 0);
  assert.equal(c.biggestHoles(src.pairs)[0].pair, 'EURUSD');
});
test('przegląd zdrowia: brak przeglądu, nieaktualny przegląd, liczenie problemów', async () => {
  const z = await import('../../web/js/health.js');
  assert.equal(z.healthView(null, 1000, true).problems, 1);
  const health = { at: 1000, summary: 'Wszystko w porządku', facts: ['x'], checks: [
    { id: 'a', name: 'A', state: 'ok', text: '' }, { id: 'b', name: 'B', state: 'warn', text: '' }, { id: 'c', name: 'C', state: 'bad', text: '' }] };
  const fresh = z.healthView(health, 1000 + 600, true);
  assert.equal(fresh.state, 'bad'); assert.equal(fresh.problems, 2); assert.equal(fresh.checks.length, 3);
  const stale = z.healthView({ ...health, checks: [health.checks[0]] }, 1000 + 3 * 3600, false);
  assert.equal(stale.checks[0].id, 'watchdog'); assert.equal(stale.state, 'warn'); assert.match(stale.summary, /3 h temu.*Mac rozłączony/);
  assert.deepEqual(z.sortChecks(health.checks).map((c) => c.id), ['c', 'b', 'a']);
  assert.deepEqual([1, 2, 5, 12, 22].map(z.problemWord), ['problem', 'problemy', 'problemów', 'problemów', 'problemy']);
});

test('mapa: kolor = dziury, bieżący miesiąc obrysem, brak świec pusty', async () => {
  const c = await import('../../web/js/coverage.js');
  assert.deepEqual(c.cellView([1, 500, 500, 0, 0, 0, 0]), { fill: 1, color: 'ok', outline: '' });
  assert.equal(c.cellView([1, 500, 450, 50, 0, 0, 0]).color, 'h3');
  assert.deepEqual(c.cellView([2, 300, 298, 2, 0, 0, 0]), { fill: 1, color: 'h1', outline: 'partial' });
  assert.equal(c.cellView([0, 500, 0, 0, 0, 0, 0]).fill, 0);
});
test('audyt doby i zegar oczekiwania na świecę (D-033)', async () => {
  const { auditCells, waitingSince, elapsed } = await import('../../web/js/session.js');
  const H = 3600;
  const cur = Date.UTC(2026, 9, 27, 17) / 1000;   // wtorek 17:00 UTC trwa
  const now = cur + 14 * 60;                       // 17:14
  // świeca 16:00 zapisana → para nie czeka; zapisana tylko 15:00 → czeka od 17:00:00 (pełna godzina)
  assert.equal(waitingSince(cur - H, now), null);
  assert.equal(waitingSince(cur - 2 * H, now), cur);
  assert.equal(elapsed(cur, now), '14:00');
  assert.equal(elapsed(cur, cur + 3725), '1:02:05');
  // weekend: w sobotę nic nie czeka
  assert.equal(waitingSince(Date.UTC(2026, 9, 30, 20) / 1000, Date.UTC(2026, 9, 31, 12, 5) / 1000), null);
  const start = cur - 24 * H;
  const str = '1'.repeat(23) + '.';                // 24 godziny: ostatnia (16:00) jeszcze nie dotarła
  const a = auditCells({ start, pairs: { EURUSD: str, USDJPY: '1'.repeat(24) } }, { EURUSD: { lastTs: cur - 2 * H }, USDJPY: { lastTs: cur - H } }, now);
  assert.equal(a.hours.length, 25);
  assert.equal(a.hours[24], cur);
  assert.deepEqual(a.pairs.EURUSD.slice(-2), [{ st: 'wait', since: cur }, { st: 'now' }]);
  assert.deepEqual(a.pairs.USDJPY.slice(-2), [{ st: 'ok' }, { st: 'now' }]);
  // świeca nowsza niż napis audytu (status zapisany, recent jeszcze nie przesunięty) — liczy się lastTs
  const b = auditCells({ start: start - H, pairs: { EURUSD: '1'.repeat(24) } }, { EURUSD: { lastTs: cur - H } }, now);
  assert.equal(b.pairs.EURUSD[23].st, 'ok');
});

test('wycinki świec: okna, przerwy i transakcje tylko w swoim oknie (D-033)', async () => {
  const { splitWindows, placeTrades, seriesData } = await import('../../web/js/candlewin.js');
  const H = 3600;
  const t0 = Date.UTC(2025, 4, 14, 0) / 1000;   // środa
  const mk = (a, n) => Array.from({ length: n }, (_, i) => ({ ts: a + i * H, open: 1, high: 1.1, low: 0.9, close: 1 }));
  const fri = Date.UTC(2025, 4, 16, 10) / 1000, sun = Date.UTC(2025, 4, 18, 22) / 1000;
  const far = Date.UTC(2025, 6, 1, 8) / 1000;
  const bars = [...mk(t0, 10), ...mk(fri, 11), ...mk(sun, 5), ...mk(far, 6)];
  const w = splitWindows(bars);
  // weekend (pt 20:00 → nd 22:00) nie dzieli okna; luka środa → piątek i maj → lipiec dzielą
  assert.deepEqual(w.map((x) => [x.from, x.to]), [[0, 10], [10, 26], [26, 32]]);
  const trades = [
    { entry_ts: fri + 9 * H, exit_ts: sun + 3 * H },   // przez weekend — w jednym oknie
    { entry_ts: t0 + 8 * H, exit_ts: far + 2 * H },    // wyjście w innym oknie — nie rysujemy
    { entry_ts: t0 + 30 * H, exit_ts: t0 + 31 * H },   // wejścia nie ma wśród świec
  ];
  const p = placeTrades(bars, w, trades);
  assert.equal(p.shown.length, 1);
  assert.equal(p.hidden, 2);
  assert.equal(p.shown[0].exit, sun + 2 * H);
  const d = seriesData(bars, w);
  assert.equal(d.filter((x) => x.open === undefined).length, 16);   // 8 pustych miejsc po każdym z dwóch okien
  assert.ok(d.every((x, i) => i === 0 || x.time > d[i - 1].time));
});

test('otwarcie tygodnia: Yahoo zaczyna później niż kalendarz — bez czerwonego zegara (D-039)', async () => {
  const { weekOpenGrace, waitingSince } = await import('../../web/js/session.js');
  const H = 3600, fri20 = Date.UTC(2025, 9, 31, 20) / 1000, sun22 = Date.UTC(2025, 10, 2, 22) / 1000;
  assert.equal(weekOpenGrace(fri20, sun22 + 2 * H + 120), true);
  assert.equal(waitingSince(fri20, sun22 + 2 * H + 120), null);
  assert.equal(weekOpenGrace(fri20, sun22 + 4 * H + 120), false);
  assert.equal(waitingSince(fri20, sun22 + 4 * H + 120), sun22 + H);
});

test('kalendarz danych dzień po dniu: stany, najgorszy z par, miesiące od najnowszego', async () => {
  const c = await import('../../web/js/calendar.js');
  assert.deepEqual([-1, -2, 0, 2, 105].map(c.dayState), ['off', 'none', 'ok', 'fill', 'gap']);
  // 2026-01-29 (cz) … 2026-02-02 (pn)
  const days = { start: '2026-01-29', pairs: { EURUSD: [0, 105, -1, 102, 119], USDJPY: [2, 0, -1, 0, -2] } };
  const m = c.calendarMonths(days, ['EURUSD', 'USDJPY']);
  assert.deepEqual(m.map((x) => x.key), ['2026-02', '2026-01']);
  assert.equal(m[1].first, 3);                                        // 1.01.2026 to czwartek
  assert.deepEqual(m[1].cells.map((x) => x.state), ['fill', 'gap', 'off']);
  assert.deepEqual(m[1].cells[1].pairs, [{ pair: 'EURUSD', state: 'gap', hours: 5 }]);
  assert.deepEqual(m[0].cells.map((x) => x.state), ['gap', 'gap']); // przerwa ma pierwszeństwo przed brakiem danych
  const only = c.calendarMonths(days, ['USDJPY']);
  assert.equal(only[0].cells[1].state, 'none');
  const s = c.calendarSummary(m);
  assert.equal(s.session, 4); assert.equal(s.gap, 3); assert.equal(s.fill, 1);
  assert.equal(new Date(s.from * 1000).toISOString().slice(0, 10), '2026-01-29');
});
