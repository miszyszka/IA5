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

test('dziennik świec: oczekiwane wg kalendarza sesji, braki, dzień w toku i sobota', async () => {
  const { dailyRows, expectedOnDay, parseFlag } = await import('../../web/js/session.js');
  const now = Date.UTC(2026, 9, 26, 17, 5) / 1000; // pn 17:05 UTC → zamknięte świece 00:00…16:00 = 17
  assert.equal(expectedOnDay('2026-10-26', now), 17);
  assert.equal(expectedOnDay('2026-10-23', now), 21); // piątek do 20:00
  assert.equal(expectedOnDay('2026-10-24', now), 0); // sobota
  assert.equal(expectedOnDay('2026-10-25', now), 2); // niedziela od 22:00
  const rows = dailyRows({ '2026-10-26': { EURUSD: 17, USDJPY: 16 }, '2026-10-23': { EURUSD: 21, USDJPY: 22 } }, ['EURUSD', 'USDJPY'], now, 4);
  assert.deepEqual(rows.map((r) => r.day), ['2026-10-26', '2026-10-25', '2026-10-24', '2026-10-23']);
  assert.equal(rows[0].open, true);
  assert.equal(rows[0].missing, 1);
  assert.equal(rows[1].missing, 4); // niedziela bez świec w dzienniku
  assert.equal(rows[2].closed, true);
  assert.equal(rows[3].missing, 0); // nadmiar jednej pary nie znosi braków — tu brak braków
  assert.deepEqual(parseFlag('luka@1793016000'), { kind: 'luka', ts: 1793016000 });
});

test('mapa pokrycia: statusy na żywo, podsumowanie, luki w miesiącu', async () => {
  const c = await import('../../web/js/coverage.js');
  assert.deepEqual(c.monthKeys('2003-11', 3), ['2003-11', '2003-12', '2004-01']);
  assert.equal(c.monthIndex('2003-05', '2004-02'), 9);
  const src = { start: '2024-01', pairs: { EURUSD: { m: [[1, 500, 495, 2, 3, 1], [0, 480, 0, 0, 0, 0], [2, 100, 100, 0, 0, 0]],
    gaps: [[Date.UTC(2024, 0, 31, 22) / 1000, Date.UTC(2024, 1, 1, 2) / 1000, 4, 'p', -1]] } } };
  // bez heartbeatu: opublikowana mapa
  let m = c.mergeLive(src, null, ['EURUSD']);
  assert.deepEqual(m.keys, ['2024-01', '2024-02', '2024-03']);
  assert.equal(c.cellKind(m.pairs.EURUSD.m[0]), 'holes1');
  // heartbeat: luty właśnie pobrany (jeszcze bez liczb), marzec w toku, a dla USDJPY jest tylko heartbeat
  m = c.mergeLive(src, { start: '2024-01', pairs: { EURUSD: 'oo~', USDJPY: 'x.~' } }, ['EURUSD', 'USDJPY']);
  assert.equal(m.live, true);
  assert.equal(c.cellKind(m.pairs.EURUSD.m[1]), 'fresh');
  assert.deepEqual(m.pairs.EURUSD.m[2], [2, 100, 100, 0, 0, 0]);
  assert.equal(c.cellKind(m.pairs.USDJPY.m[0]), 'failed');
  const s = c.summarize(m.pairs.EURUSD.m);
  assert.equal(s.done, 3); assert.equal(s.left, 0); assert.equal(s.uncounted, 1);
  assert.equal(s.exp, 600); assert.equal(s.pres, 595); assert.equal(s.holes, 2);
  const s0 = c.summarize(src.pairs.EURUSD.m); // bez heartbeatu: luty niepobrany = brakuje 480 h
  assert.equal(s0.left, 1); assert.equal(s0.leftHours, 480); assert.ok(Math.abs(s0.pct - 595 / (1080 - 3)) < 1e-12); // wspólne luki nie obniżają pokrycia
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

test('mapa pokrycia: miesiąc pobrany częściowo (D-025)', async () => {
  const c = await import('../../web/js/coverage.js');
  const m = c.mergeLive({ start: '2024-01', pairs: { EURUSD: { m: [[5, 480, 470, 0, 0, 0, 24]], gaps: [] } } }, null, ['EURUSD']);
  assert.equal(c.cellKind(m.pairs.EURUSD.m[0]), 'incomplete');
  const s = c.summarize(m.pairs.EURUSD.m);
  assert.equal(s.done, 1); assert.equal(s.incomplete, 1); assert.equal(s.leftHours, 24);
  const live = c.mergeLive(null, { start: '2024-01', pairs: { EURUSD: '!' } }, ['EURUSD']);
  assert.equal(c.cellKind(live.pairs.EURUSD.m[0]), 'incomplete');
});

test('audyt Yahoo świeca po świecy (D-027)', async () => {
  const { recentCells } = await import('../../web/js/session.js');
  const start = Date.UTC(2026, 9, 23, 18) / 1000; // pt 18:00
  const now = start + 6 * 3600 + 60;               // sb 00:01 → zamknięte świece 18…23
  const r = recentCells({ start, pairs: { EURUSD: '1l....' } }, now);
  assert.equal(r.hours.length, 6);
  assert.deepEqual(r.pairs.EURUSD, ['ok', 'late', 'missing', 'closed', 'closed', 'closed']);
  const fresh = recentCells({ start, pairs: { EURUSD: '1l' } }, start + 3 * 3600 + 120);
  assert.deepEqual(fresh.pairs.EURUSD, ['ok', 'late', 'pending']); // 20:00 zamknięta 2 min temu
  const pend = recentCells({ start, pairs: { EURUSD: '1l.' } }, start + 3 * 3600 + 300 + 3600);
  assert.equal(pend.pairs.EURUSD[2], 'missing');
  assert.equal(recentCells({ start: start - 3600, pairs: { EURUSD: '11.' } }, start + 2 * 3600 + 600).pairs.EURUSD[2], 'pending');
});

test('mapa: wypełnienie = ile pobrano, kolor = dziury; audyt: brak we wszystkich parach to nie brak pary (D-028)', async () => {
  const c = await import('../../web/js/coverage.js');
  assert.deepEqual(c.cellView([1, 500, 500, 0, 0, 0, 0]), { fill: 1, color: 'ok', outline: '' });
  assert.equal(c.cellView([1, 500, 450, 50, 0, 0, 0]).color, 'h3');
  const inc = c.cellView([5, 300, 300, 2, 0, 0, 100]);
  assert.equal(inc.outline, 'incomplete'); assert.equal(inc.fill, 0.75); assert.equal(inc.color, 'h1');
  assert.equal(c.cellView([0, 500, 0, 0, 0, 0, 0]).fill, 0);
  const { recentCells } = await import('../../web/js/session.js');
  const start = Date.UTC(2026, 9, 21, 10) / 1000; // śr 10:00
  const r = recentCells({ start, pairs: { A: '1.1', B: '..1', C: '1.1', D: '1.1' } }, start + 3 * 3600 + 3600);
  assert.deepEqual(r.pairs.A.slice(0, 3), ['ok', 'allgap', 'ok']);
  assert.equal(r.pairs.B[0], 'missing');
});
