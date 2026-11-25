// node --test tests/web/rev.test.mjs — logika zakładki REV (D-063, D-074: moje konto)
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { applyTx, candleDay, checkTx, countdown, fmtRate, fmtWarsaw, inputValue, nextDecisionMs, normWallet, parseAmount, planConversions, verdictBadge, walletCSV, walletCurrencies, walletRows, warsawToUtc } from '../../web/js/revlogic.js';

const utc = (s) => Date.parse(s);

test('najbliższy wtorek 08:00 czasu polskiego, także przez zmianę czasu', () => {
  assert.equal(nextDecisionMs(utc('2026-11-10T06:59:00Z')), utc('2026-11-10T07:00:00Z'));          // wt 07:59 Warszawa
  assert.equal(nextDecisionMs(utc('2026-11-10T07:01:00Z')), utc('2026-11-17T07:00:00Z'));          // wt 08:01 → za tydzień
  assert.equal(nextDecisionMs(utc('2026-03-28T12:00:00Z')), utc('2026-03-31T06:00:00Z'));          // po zmianie na czas letni
  assert.equal(nextDecisionMs(utc('2026-10-24T12:00:00Z')), utc('2026-10-27T07:00:00Z'));          // po zmianie na zimowy
  assert.equal(warsawToUtc(2026, 7, 7, 8, 0), utc('2026-07-07T06:00:00Z'));
  assert.equal(fmtWarsaw(utc('2026-11-17T07:00:00Z') / 1000), '2026-11-17 08:00');
  assert.equal(candleDay(utc('2026-11-11T00:00:00Z') / 1000), '2026-11-10');   // zamknięcie wtorku = północ w Londynie
  assert.equal(candleDay(utc('2026-07-07T23:00:00Z') / 1000), '2026-07-07');   // latem: 23:00 UTC
});

test('odliczanie', () => {
  assert.equal(countdown(3 * 3600e3 + 12 * 60e3), 'za 3 h 12 min');
  assert.equal(countdown(5 * 86400e3 + 20 * 3600e3 + 5e3), 'za 5 d 20 h');
  assert.equal(countdown(9 * 60e3), 'za 9 min');
  assert.equal(countdown(-1), 'teraz');
});

test('werdykt', () => {
  assert.deepEqual(verdictBadge({ verdict: { color: 'yellow', passed: 3, of: 5 } }), { color: 'yellow', text: '🟡 3/5' });
  assert.equal(verdictBadge(null).text, '—');
});

// Stan systemu jak w rev/state.json: kursy w zł za 1 jednostkę, udziały portfela REV dziś.
const sys = {
  last_px: { PLN: 1, CHF: 5, EUR: 4, JPY: 0.025, USD: 4 },
  today: { weights: { CHF: 0.3, EUR: 0.2, JPY: 0, USD: 0, PLN: 0.5 } },
};

test('kwoty wpisane ręcznie', () => {
  assert.equal(parseAmount('1 234,56'), 1234.56);
  assert.equal(parseAmount('1234.5'), 1234.5);
  assert.equal(parseAmount('1.234,56'), 1234.56);
  assert.equal(parseAmount('\u00a0 10 '), 10);
  assert.equal(parseAmount(''), null);
  assert.ok(Number.isNaN(parseAmount('abc')));
  assert.equal(inputValue(4890.7722, 'PLN'), '4890,77');
  assert.equal(inputValue(12345.6, 'JPY'), '12346');
});

test('kolejność walut: PLN, trzymane przez system, reszta alfabetycznie', () => {
  assert.deepEqual(walletCurrencies(sys), ['PLN', 'CHF', 'EUR', 'JPY', 'USD']);
});

test('moje konto wobec systemu i plan przewalutowań', () => {
  const v = walletRows(sys, { PLN: 10000 });
  assert.equal(v.total, 10000);
  assert.equal(v.match, 50);
  const plan = planConversions(v);
  assert.deepEqual(plan.map((c) => [c.from, c.to, c.fromAmt, c.toAmt]), [['PLN', 'CHF', 3000, 600], ['PLN', 'EUR', 2000, 500]]);
  // po wykonaniu planu po kursie rynkowym — konto zgodne, nic do zrobienia
  let b = { PLN: 10000 };
  for (const c of plan) b = applyTx(b, { from: c.from, fromAmt: c.fromAmt, to: c.to, toAmt: c.toAmt });
  const v2 = walletRows(sys, b);
  assert.ok(Math.abs(v2.match - 100) < 1e-9);
  assert.deepEqual(planConversions(v2), []);
});

test('plan: nadwyżka w obcej walucie idzie wprost do brakującej, nie przez złotówki', () => {
  const v = walletRows(sys, { PLN: 5000, CHF: 0, EUR: 500, USD: 375 });   // EUR 2000 zł, USD 1500 zł → razem 8500 zł
  const plan = planConversions(v);   // brakuje tylko CHF (2550 zł): USD 1500 + PLN 750 + EUR 300
  assert.deepEqual(plan.map((c) => c.from), ['USD', 'PLN', 'EUR']);
  assert.ok(plan.every((c) => c.to === 'CHF'));
  assert.ok(plan.every((c) => c.fromAmt <= v.rows.find((r) => r.code === c.from).have));
  const sum = plan.reduce((a, c) => a + c.pln, 0);
  assert.ok(Math.abs(sum - 8500 * 0.3) < 1e-6);
});

test('drobne różnice poniżej progu nie są przewalutowywane', () => {
  const v = walletRows(sys, { PLN: 5000.5, CHF: 600, EUR: 500 });
  assert.deepEqual(planConversions(v), []);
});

test('sprawdzenie transakcji: kurs, koszt wobec rynku, salda, błędy', () => {
  const bal = { PLN: 1000 };
  const t = { from: 'PLN', fromAmt: 500, to: 'CHF', toAmt: 99, fee: 2, feeCur: 'PLN' };
  const c = checkTx(t, bal, sys.last_px);
  assert.ok(c.ok);
  assert.ok(Math.abs(c.rate - 0.198) < 1e-12);
  assert.equal(fmtRate('PLN', 'CHF', c.rate), '1 CHF = 5,0505 PLN');
  assert.ok(Math.abs(c.costPln - (500 - 99 * 5 + 2)) < 1e-9);   // 5 zł różnicy kursu + 2 zł opłaty
  assert.deepEqual(c.after, { PLN: 498, CHF: 99 });
  assert.deepEqual(applyTx(c.after, t, -1), { PLN: 1000, CHF: 0 });   // cofnięcie wraca do stanu sprzed
  assert.ok(!checkTx({ ...t, fromAmt: 999 }, bal, sys.last_px).ok);  // 999 + 2 zł opłaty > 1000
  assert.ok(!checkTx({ ...t, to: 'PLN' }, bal, sys.last_px).ok);
  assert.ok(!checkTx({ ...t, toAmt: 0 }, bal, sys.last_px).ok);
  assert.equal(checkTx({ ...t, toAmt: 80 }, bal, sys.last_px).warnings.length, 1);   // kurs 20% od rynku
});

test('CSV moich przewalutowań i naprawa zapisu', () => {
  const tx = [{ id: 'a', at: 1795600000, from: 'PLN', fromAmt: 500, to: 'CHF', toAmt: 99, fee: 2, feeCur: 'PLN', mkt: { PLN: 1, CHF: 5 }, costPln: 7 }];
  const csv = walletCSV(tx).trim().split('\n');
  assert.equal(csv.length, 2);
  assert.ok(csv[1].endsWith(';500.00;PLN;99.00;CHF;2.00;PLN;0.198000;0.200000;7.00'));
  const w = normWallet({ balances: { PLN: '12.5', bad: 3, EUR: 'x' }, tx: [...tx, { from: 'PLN' }] });
  assert.deepEqual(w.balances, { PLN: 12.5 });
  assert.equal(w.tx.length, 1);
});
