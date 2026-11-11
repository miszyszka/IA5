// node --test tests/web/rev.test.mjs — logika zakładki REV (D-063)
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { allocation, candleDay, countdown, fmtWarsaw, ledgerByDecision, ledgerCSV, liveSummary, nextDecisionMs, rankingRows, verdictBadge, warsawToUtc } from '../../web/js/revlogic.js';

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

const state = {
  capital0: 10000, blocs: { USD: ['HKD'], EUR: [] },
  today: { values: { USD: 3000, CHF: 2500, PLN: 4900, NOK: 0 }, total: 10400, equal_total: 10100,
    weights: { USD: 0.288, CHF: 0.24, PLN: 0.471, NOK: 0 }, targets: { USD: 0.3, CHF: 0.25, PLN: 0.45, NOK: 0 },
    scores: { USD: 1.2, CHF: 0.8, PLN: 0.5, NOK: -1 }, value_score: {}, trend_score: {} },
  ledger: [
    { ts: 1794898800, basket: 'USD', units_before: 0, units_after: 750, price: 4.0, price_day: '2026-11-16', value_pln: 3000 },
    { ts: 1794898800, basket: 'PLN', units_before: 10000, units_after: 7000, price: 1, price_day: '2026-11-16', value_pln: -3000 },
    { ts: 1795503600, basket: 'CHF', units_before: 0, units_after: 500, price: 5.0, price_day: '2026-11-23', value_pln: 2500 },
  ],
};

test('podział: suma 100%, blok z członkami w etykiecie, bez pustych koszyków', () => {
  const a = allocation(state);
  assert.ok(Math.abs(a.reduce((s, r) => s + r.pct, 0) - 100) < 0.01);
  assert.equal(a[0].code, 'PLN');
  assert.equal(a.find((r) => r.code === 'USD').label, 'USD (+HKD)');
  assert.ok(!a.find((r) => r.code === 'NOK'));
});

test('ranking i podsumowanie', () => {
  const r = rankingRows(state);
  assert.equal(r[0].code, 'PLN');
  assert.ok(Math.abs(r.find((x) => x.code === 'USD').change - 1.2) < 1e-9);
  const s = liveSummary(state);
  assert.equal(s.change, 400); assert.ok(Math.abs(s.pct - 4) < 1e-9); assert.ok(Math.abs(s.equalPct - 1) < 1e-9);
});

test('CSV dziennika i grupy po wtorkach', () => {
  const csv = ledgerCSV(state).trim().split('\n');
  assert.equal(csv[0], 'data;koszyk;jednostki_przed;jednostki_po;kurs_pln;wartosc_zl;dzien_ceny');
  assert.equal(csv.length, 4);
  assert.ok(csv[1].startsWith('2026-11-17 08:00;USD;'));
  const g = ledgerByDecision(state);
  assert.equal(g.length, 2); assert.equal(g[0].rows[0].basket, 'CHF');
});

test('werdykt', () => {
  assert.deepEqual(verdictBadge({ verdict: { color: 'yellow', passed: 3, of: 5 } }), { color: 'yellow', text: '🟡 3/5' });
  assert.equal(verdictBadge(null).text, '—');
});
