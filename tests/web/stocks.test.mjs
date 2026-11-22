// node --test tests/web/stocks.test.mjs — logika zakładki Stocks (D-071)
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { addTicker, currentPlan, draftFrom, equalize, fitTo100, holdingRows, ledgerByDay, ledgerCSV, liveSummary, removeTicker, runStatus, sameConfig, setWeight, sumW, validateDraft } from '../../web/js/stklogic.js';

test('szkic domyślny: 27 spółek Michała, równo, suma 100', () => {
  const d = draftFrom(null);
  assert.equal(d.tickers.length, 27);
  assert.equal(sumW(d), 100);
  assert.deepEqual(validateDraft(d), []);
  assert.equal(d.capital, 10000);
  assert.equal(d.band, 20);
});

test('dodawanie, usuwanie, dopasowanie do 100%', () => {
  let d = draftFrom({ tickers: [{ t: 'ko', w: 50 }, { t: 'PEP', w: 50 }], capital: 5000, band: 20 });
  assert.deepEqual(d.tickers.map((r) => r.t), ['KO', 'PEP']);
  let r = addTicker(d, ' msft ');
  assert.equal(r.error, null);
  d = r.draft;
  assert.equal(d.tickers.at(-1).t, 'MSFT');
  assert.notEqual(sumW(d), 100);
  assert.ok(validateDraft(d).some((e) => e.includes('100%')));
  d = fitTo100(d);
  assert.equal(sumW(d), 100);
  assert.ok(addTicker(d, 'KO').error.includes('już'));
  assert.ok(addTicker(d, 'K O!').error);
  assert.ok(addTicker(d, 'BRK-B').error === null);
  d = removeTicker(d, 'PEP');
  assert.deepEqual(d.tickers.map((x) => x.t), ['KO', 'MSFT']);
  d = setWeight(equalize(d), 'KO', 0);
  assert.ok(validateDraft(d).some((e) => e.includes('większy od 0')));
  assert.ok(sameConfig(draftFrom({ tickers: [{ t: 'A', w: 50 }, { t: 'B', w: 50 }], capital: 1, band: 2 }),
    { tickers: [{ t: 'A', w: 50.001 }, { t: 'B', w: 50 }], capital: 1, band: 2 }));
});

test('stan liczenia i plan', () => {
  assert.equal(runStatus({ status: 'czeka_na_dane', waiting: ['XYZ'] }).state, 'warn');
  assert.ok(runStatus({ status: 'czeka_na_dane', waiting: ['XYZ'] }).text.includes('XYZ'));
  assert.equal(runStatus({ status: 'blad', error: 'x' }).state, 'bad');
  assert.ok(runStatus({ status: 'do_policzenia' }, { online: false }).text.includes('ia5 start'));
  const st = { plans: [{ status: 'wykonane', exec_day: '2026-11-17' }, { status: 'zaplanowane', exec_day: null }] };
  assert.equal(currentPlan(st).status, 'zaplanowane');
  assert.equal(currentPlan({ plans: [{ status: 'wykonane' }] }).status, 'wykonane');
});

test('transakcje, CSV, wynik od startu', () => {
  const st = { capital0: 1000, ledger: [{ exec_day: '2026-11-16', t: 'KO', side: 'kupno', shares: 3, price: 60, price_plan: 59, value: 180, cost: 0.18 },
    { exec_day: '2026-11-17', t: 'KO', side: 'sprzedaż', shares: 1, price: 61, price_plan: 60, value: -61, cost: 0.06 },
    { exec_day: '2026-11-17', t: 'PEP', side: 'kupno', shares: 1, price: 150, price_plan: 151, value: 150, cost: 0.15 }],
  today: { total: 1100, fixed_total: 1050, hold_total: 990, cash: 12, rows: [{ t: 'KO', weight: 0.5, base: 0.4, lo: 0.32, hi: 0.48, target: 0.45 }, { t: 'PEP', weight: 0.5, base: 0.6, lo: 0.48, hi: 0.72, target: 0.55 }] } };
  const g = ledgerByDay(st);
  assert.deepEqual(g.map((x) => x.day), ['2026-11-17', '2026-11-16']);
  assert.equal(g[0].rows[0].t, 'KO');            // najpierw sprzedaż
  assert.equal(g[0].bought, 150); assert.equal(g[0].sold, 61);
  const csv = ledgerCSV(st).trim().split('\n');
  assert.equal(csv.length, 4);
  assert.equal(csv[1], '2026-11-16;KO;kupno;3;60.0000;59.0000;180.00;0.18');
  const s = liveSummary(st);
  assert.ok(Math.abs(s.pct - 10) < 1e-9 && Math.abs(s.fixedPct - 5) < 1e-9 && Math.abs(s.holdPct + 1) < 1e-9);
  assert.deepEqual(holdingRows(st).map((r) => r.t), ['PEP', 'KO']);
});

test('odliczanie do rebalansu i zdania transakcji', async () => {
  const { nextRebalance, nyOpenMs, orderSentence, holdingsWithCash } = await import('../../web/js/stklogic.js');
  assert.equal(nyOpenMs('2026-11-24'), Date.parse('2026-11-24T14:30:00Z'));          // zimą 09:30 NY = 14:30 UTC
  assert.equal(nyOpenMs('2026-07-07'), Date.parse('2026-07-07T13:30:00Z'));          // latem 13:30 UTC
  assert.equal(nyOpenMs('2026-11-21'), Date.parse('2026-11-23T14:30:00Z'));          // sobota → poniedziałek
  const r = nextRebalance({ plans: [{ status: 'wykonane' }], next: { plan_ts: Date.parse('2026-11-24T07:00:00Z') / 1000 } }, 0);
  assert.equal(r.execMs, Date.parse('2026-11-24T14:30:00Z'));
  assert.equal(r.pending, false);
  const p = nextRebalance({ plans: [{ status: 'zaplanowane', plan_ts: 1, exec_from: '2026-11-24' }] }, 0);
  assert.equal(p.pending, true);
  assert.equal(orderSentence({ side: 'kupno', t: 'KO', shares: 3, price_plan: 61.2, value_plan: 183.6 }, true), 'Kup 3 akcje KO po 61,20 USD = 183,60 USD');
  assert.equal(orderSentence({ side: 'sprzedaż', t: 'MU', shares: 5, price: 100, value: -500 }, false), 'Sprzedaj 5 akcji MU po 100,00 USD = 500,00 USD');
  const h = holdingsWithCash({ today: { total: 1000, cash: 100, rows: [{ t: 'A', value: 900, weight: 0.9, base: 1, lo: 0.8, hi: 1.2, target: 1 }] } });
  assert.ok(h.ok && Math.abs(h.sumPct - 100) < 1e-9 && h.cashPct === 10);
});
