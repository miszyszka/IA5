import assert from 'node:assert/strict';
import { test } from 'node:test';
import { boxState, fmtPrice, fmtRange, orderPairs, priceDecimals, qualityLine, sideLine } from '../../web/js/zasieglogic.js';

test('ceny i stan pudełka', () => {
  assert.equal(priceDecimals('USDJPY'), 3);
  assert.equal(priceDecimals('EURUSD'), 5);
  assert.equal(fmtPrice('EURUSD', 1.0845), '1,08450');
  assert.equal(fmtRange(147.2, 327.4), '147–327 pips');
  assert.equal(boxState({ armed: true, squeezed: true }).key, 'armed');
  assert.equal(boxState({ armed: false, squeezed: true }).key, 'squeezed');
  assert.equal(boxState({ armed: false, squeezed: false }).key, 'normal');
  assert.equal(boxState(null).key, 'none');
});

test('zdanie wybicia i kolejność par', () => {
  const s = sideLine('EURUSD', { trigger: 1.0845, sl: 1.0812, tp: 1.0944, tp_pips: 99, risk_pips: 33, sl_mid: false }, 1);
  assert.match(s, /^Kupno po zamknięciu godziny nad 1,08450 · SL 1,08120 · TP 1,09440/);
  assert.match(s, /\+99 pips \/ −33 pips/);
  const o = orderPairs({ A: { pair: 'A', box: { pct: 50 } }, B: { pair: 'B', box: { armed: true, pct: 10 } }, C: { pair: 'C', box: { squeezed: true, pct: 5 } } });
  assert.deepEqual(o.map((x) => x.pair), ['B', 'C', 'A']);
  assert.match(qualityLine({ n: 4000, better_pct: 21.4, band80: 79.6 }), /o 21% mniejszy błąd.*w 80% dni/);
  assert.match(qualityLine({}), /za mało historii/);
});
