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
