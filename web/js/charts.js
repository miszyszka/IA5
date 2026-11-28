// Wykresy: ECharts (kapitał, heatmapa, krzywe) i Lightweight Charts (świece z transakcjami).
// Zasada uczciwości (CLAUDE.md 11): bez wygładzania linii, osie z rzeczywistych wartości. Płasko, bez gradientów (D-019).
import { barStep, placeTrades, seriesData, splitWindows } from './candlewin.js';

const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const instances = new Set();

export function disposeAll() {
  for (const c of instances) { try { c.dispose ? c.dispose() : c.remove(); } catch { /* już usunięty */ } }
  instances.clear();
}
window.addEventListener('resize', () => instances.forEach((c) => c.resize && c.resize()));

function base() {
  const text = css('--muted'), line = css('--line');
  return {
    backgroundColor: 'transparent', animation: false,
    textStyle: { color: css('--text'), fontFamily: 'Inter, system-ui, sans-serif' },
    tooltip: { backgroundColor: css('--raised'), borderColor: line, textStyle: { color: css('--text') }, confine: true },
    grid: { left: 64, right: 24, top: 24, bottom: 36 },
    axisDefaults: { axisLine: { lineStyle: { color: line } }, splitLine: { lineStyle: { color: line } }, axisLabel: { color: text } },
  };
}

export function chart(el, option) {
  const old = window.echarts.getInstanceByDom(el);
  if (old) { old.dispose(); instances.delete(old); }
  const c = window.echarts.init(el, null, { renderer: 'canvas' });
  c.setOption(option);
  instances.add(c);
  return c;
}

const fmtDate = (ms) => new Date(ms).toISOString().slice(0, 10);

/** Kapitał (góra) + obsunięcie (dół). marks: [{ts, label}] — pionowe linie (granica IS/OOS, zamrożenie). */
export function equityChart(el, curve, dd, marks = []) {
  const b = base();
  const ax = b.axisDefaults;
  const accent = css('--accent'), bad = css('--bad');
  const x = curve.ts.map((t) => t * 1000);
  return chart(el, {
    ...b,
    grid: [{ left: 72, right: 24, top: 20, height: '58%' }, { left: 72, right: 24, top: '72%', bottom: 32 }],
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : v.toLocaleString('pl-PL', { maximumFractionDigits: 2 })) },
    xAxis: [
      { type: 'time', gridIndex: 0, ...ax, axisLabel: { show: false }, splitLine: { show: false } },
      { type: 'time', gridIndex: 1, ...ax, splitLine: { show: false }, axisLabel: { ...ax.axisLabel, formatter: (v) => fmtDate(v) } },
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true, ...ax, name: 'USD', nameTextStyle: { color: ax.axisLabel.color },
        axisLabel: { ...ax.axisLabel, formatter: (v) => v.toLocaleString('pl-PL', { maximumFractionDigits: 0 }) } },
      { type: 'value', gridIndex: 1, max: 0, ...ax, name: 'DD %', nameTextStyle: { color: ax.axisLabel.color } },
    ],
    series: [
      { name: 'Kapitał', type: 'line', step: 'end', showSymbol: false, xAxisIndex: 0, yAxisIndex: 0,
        data: x.map((t, i) => [t, +curve.equity[i].toFixed(2)]),
        lineStyle: { color: accent, width: 1.75 },
        markLine: { symbol: 'none', label: { color: css('--muted'), formatter: '{b}' }, lineStyle: { color: css('--muted'), type: 'dashed' },
          data: marks.map((m) => ({ name: m.label, xAxis: m.ts * 1000 })) } },
      { name: 'Obsunięcie %', type: 'line', step: 'end', showSymbol: false, xAxisIndex: 1, yAxisIndex: 1,
        data: x.map((t, i) => [t, +dd[i].toFixed(2)]), lineStyle: { color: bad, width: 1 }, areaStyle: { color: bad, opacity: 0.18 } },
    ],
  });
}

/** REV (D-063): gdzie jest kapitał — słupki pionowe obok siebie (% kapitału), linia limitu `cap` (%). rows: [{label, value, pct}]. */
export function bars(el, rows, cap = 50) {
  const b = base();
  const ax = b.axisDefaults;
  const accent = css('--accent'), muted = css('--muted');
  return chart(el, {
    ...b,
    grid: { left: 48, right: 16, top: 24, bottom: 56 },
    tooltip: { ...b.tooltip, trigger: 'item', formatter: (p) => `${p.name}<br>${rows[p.dataIndex].value.toLocaleString('pl-PL', { maximumFractionDigits: 2 })} zł · ${p.value.toLocaleString('pl-PL', { maximumFractionDigits: 1 })}%` },
    xAxis: { type: 'category', data: rows.map((r) => r.label), ...ax, axisLabel: { ...ax.axisLabel, interval: 0, rotate: rows.length > 8 || el.clientWidth < 560 ? 35 : 0 } },
    yAxis: { type: 'value', min: 0, max: Math.max(cap + 5, Math.ceil(Math.max(0, ...rows.map((r) => r.pct)) / 10) * 10), ...ax,
      axisLabel: { ...ax.axisLabel, formatter: (v) => `${v}%` } },
    series: [{ type: 'bar', barMaxWidth: 44, data: rows.map((r) => +r.pct.toFixed(2)), itemStyle: { color: accent, borderRadius: [3, 3, 0, 0] },
      label: { show: true, position: 'top', color: css('--text'), fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
        formatter: (p) => `${p.value.toLocaleString('pl-PL', { maximumFractionDigits: 1 })}%` },
      markLine: { symbol: 'none', silent: true, label: { color: muted, formatter: `limit ${cap}%`, position: 'insideEndTop' },
        lineStyle: { color: muted, type: 'dashed' }, data: [{ yAxis: cap }] } }],
  });
}

/** REV (D-063): kapitał w złotówkach dzień po dniu. series: [{name, ts, values, color, dash?}], marks: ts przewalutowań. */
export function plnLines(el, series, rebalances = [], marks = [], unit = 'zł') {
  const b = base();
  const ax = b.axisDefaults;
  const first = series[0];
  const valueAt = (t) => { let v = null; for (let i = 0; i < first.ts.length && first.ts[i] <= t; i++) v = first.values[i]; return v; };
  return chart(el, {
    ...b,
    grid: { left: 72, right: 24, top: 36, bottom: 36 },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color } },
    tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : `${v.toLocaleString('pl-PL', { maximumFractionDigits: 2 })} ${unit}`) },
    xAxis: { type: 'time', ...ax, splitLine: { show: false }, axisLabel: { ...ax.axisLabel, formatter: (v) => fmtDate(v) } },
    yAxis: { type: 'value', scale: true, ...ax, name: unit, nameTextStyle: { color: ax.axisLabel.color },
      axisLabel: { ...ax.axisLabel, formatter: (v) => v.toLocaleString('pl-PL', { maximumFractionDigits: 0 }) } },
    series: [
      ...series.map((s, i) => ({ name: s.name, type: 'line', showSymbol: false, data: s.ts.map((t, k) => [t * 1000, s.values[k]]),
        lineStyle: { color: css(s.color), width: i === 0 ? 1.75 : 1.25, type: s.dash ? 'dashed' : 'solid' }, itemStyle: { color: css(s.color) },
        markLine: i === 0 && marks.length ? { symbol: 'none', silent: true, label: { color: css('--muted'), formatter: '{b}' },
          lineStyle: { color: css('--muted'), type: 'dashed' }, data: marks.map((m) => ({ name: m.label, xAxis: m.ts * 1000 })) } : undefined })),
      ...(rebalances.length ? [{ name: 'przewalutowanie', type: 'scatter', symbolSize: 6, itemStyle: { color: css('--accent'), borderColor: css('--bg'), borderWidth: 1 },
        data: rebalances.map((t) => [t * 1000, valueAt(t)]).filter((p) => p[1] != null), tooltip: { valueFormatter: () => 'wtorek 08:00' } }] : []),
    ],
  });
}

/** Stocks (D-071): kapitał w czasie, oś logarytmiczna opcjonalnie (długa historia backtestu). series jak w plnLines. */
export function moneyLines(el, series, marks = [], { unit = 'USD', log = false } = {}) {
  const b = base();
  const ax = b.axisDefaults;
  return chart(el, {
    ...b,
    grid: { left: 80, right: 24, top: 36, bottom: 36 },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color } },
    tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : `${v.toLocaleString('pl-PL', { maximumFractionDigits: 0 })} ${unit}`) },
    xAxis: { type: 'time', ...ax, splitLine: { show: false }, axisLabel: { ...ax.axisLabel, formatter: (v) => fmtDate(v) } },
    yAxis: { type: log ? 'log' : 'value', scale: true, min: log ? (v) => v.min * 0.9 : undefined, ...ax, name: unit + (log ? ' (skala log.)' : ''), nameTextStyle: { color: ax.axisLabel.color },
      axisLabel: { ...ax.axisLabel, formatter: (v) => v.toLocaleString('pl-PL', { maximumFractionDigits: 0 }) } },
    series: series.map((s, i) => ({ name: s.name, type: 'line', showSymbol: false, data: s.ts.map((t, k) => [t * 1000, s.values[k]]),
      lineStyle: { color: css(s.color), width: i === 0 ? 1.75 : 1.25, type: s.dash ? 'dashed' : 'solid' }, itemStyle: { color: css(s.color) },
      markLine: i === 0 && marks.length ? { symbol: 'none', silent: true, label: { color: css('--muted'), formatter: '{b}' },
        lineStyle: { color: css('--muted'), type: 'dashed' }, data: marks.map((m) => ({ name: m.label, xAxis: m.ts * 1000 })) } : undefined })),
  });
}

/** Stocks (D-071): udział spółki teraz (słupek), pasmo ±B wokół udziału docelowego (kreski) i cel metody (romb). rows w %. */
export function stockBars(el, rows) {
  const b = base();
  const ax = b.axisDefaults;
  const accent = css('--accent'), muted = css('--muted'), text = css('--text');
  const fmt = (v) => `${v.toLocaleString('pl-PL', { maximumFractionDigits: 2 })}%`;
  const dash = (key, name) => ({ name, type: 'scatter', symbol: 'rect', symbolSize: [18, 2], itemStyle: { color: muted }, data: rows.map((r) => +r[key].toFixed(3)), z: 3 });
  return chart(el, {
    ...b,
    grid: { left: 48, right: 16, top: 36, bottom: 64 },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color }, data: ['udział teraz', 'cel metody', 'pasmo'] },
    tooltip: { ...b.tooltip, trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (ps) => { const r = rows[ps[0].dataIndex]; return `<b>${r.t}</b><br>teraz ${fmt(r.weightPct)} · cel metody ${fmt(r.targetPct)}<br>docelowo ${fmt(r.basePct)} (pasmo ${fmt(r.loPct)} – ${fmt(r.hiPct)})`; } },
    xAxis: { type: 'category', data: rows.map((r) => r.t), ...ax, axisLabel: { ...ax.axisLabel, interval: 0, rotate: rows.length > 12 || el.clientWidth < 560 ? 45 : 0 } },
    yAxis: { type: 'value', min: 0, ...ax, axisLabel: { ...ax.axisLabel, formatter: (v) => `${v}%` } },
    series: [
      { name: 'udział teraz', type: 'bar', barMaxWidth: 26, data: rows.map((r) => +r.weightPct.toFixed(3)), itemStyle: { color: accent, borderRadius: [3, 3, 0, 0] } },
      { name: 'cel metody', type: 'scatter', symbol: 'diamond', symbolSize: 9, itemStyle: { color: text }, data: rows.map((r) => +r.targetPct.toFixed(3)), z: 4 },
      { ...dash('hiPct', 'pasmo') }, { ...dash('loPct', 'pasmo') },
    ],
  });
}

/** Stocks (D-071): wynik roczny metody i porównań (słupki obok siebie, %). years: [{year, winner, fixed, hold}]. */
export function yearBars(el, years) {
  const b = base();
  const ax = b.axisDefaults;
  const ser = [['winner', 'metoda', '--accent'], ['fixed', 'stały podział', '--muted'], ['hold', 'kup i trzymaj', '--dim']];
  return chart(el, {
    ...b,
    grid: { left: 48, right: 16, top: 36, bottom: 36 },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color } },
    tooltip: { ...b.tooltip, trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (v) => `${v > 0 ? '+' : ''}${v.toLocaleString('pl-PL', { maximumFractionDigits: 1 })}%` },
    xAxis: { type: 'category', data: years.map((y) => String(y.year)), ...ax },
    yAxis: { type: 'value', ...ax, axisLabel: { ...ax.axisLabel, formatter: (v) => `${v}%` } },
    series: ser.map(([k, name, color]) => ({ name, type: 'bar', barMaxWidth: 10, data: years.map((y) => +(y[k] ?? 0).toFixed(2)), itemStyle: { color: css(color) } })),
  });
}

/** Heatmapa TP × SL. cells: [{x, y, v, n, id}] — v = null gdy za mało transakcji. */
export function heatmap(el, xs, ys, cells, onPick, label) {
  const b = base();
  const ax = b.axisDefaults;
  const vals = cells.map((c) => c.v).filter((v) => v != null);
  const m = Math.max(0.01, ...vals.map(Math.abs));
  const c = chart(el, {
    ...b,
    grid: { left: 64, right: 24, top: 16, bottom: 72 },
    tooltip: { ...b.tooltip, formatter: (p) => { const d = cells[p.dataIndex]; return `TP ${d.x}× · SL ${d.y}×<br>${label}: <b>${d.v == null ? 'za mało transakcji' : d.v.toFixed(3)}</b><br>transakcje IS: ${d.n}`; } },
    xAxis: { type: 'category', data: xs.map(String), name: 'TP × ATR', nameLocation: 'middle', nameGap: 28, ...ax, splitArea: { show: false } },
    yAxis: { type: 'category', data: ys.map(String), name: 'SL × ATR', nameLocation: 'middle', nameGap: 40, ...ax },
    visualMap: { min: -m, max: m, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemHeight: 140,
      text: [`+${m.toFixed(2)}`, `−${m.toFixed(2)}`], textStyle: { color: ax.axisLabel.color },
      inRange: { color: [css('--bad'), css('--raised'), css('--ok')] } },
    series: [{ type: 'heatmap', data: cells.map((d) => [xs.indexOf(d.x), ys.indexOf(d.y), d.v ?? '-']),
      label: { show: true, color: css('--text'), fontSize: 10, formatter: (p) => (p.value[2] === '-' ? '·' : (+p.value[2]).toFixed(2)) },
      itemStyle: { borderColor: css('--bg'), borderWidth: 2 },
      emphasis: { itemStyle: { borderColor: css('--accent'), borderWidth: 2 } } }],
  });
  c.on('click', (p) => onPick(cells[p.dataIndex]));
  return c;
}

/** Krzywe metryki względem parametru (np. średnie R w IS i OOS względem N świec). */
export function lines(el, xs, series, xName) {
  const b = base();
  const ax = b.axisDefaults;
  const colors = [css('--accent'), css('--text'), css('--muted')];
  return chart(el, {
    ...b,
    tooltip: { ...b.tooltip, trigger: 'axis' },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color } },
    grid: { left: 56, right: 16, top: 32, bottom: 40 },
    xAxis: { type: 'category', data: xs.map(String), name: xName, nameLocation: 'middle', nameGap: 26, ...ax },
    yAxis: { type: 'value', ...ax },
    series: series.map((s, i) => ({ name: s.name, type: 'line', data: s.data, symbol: 'circle', symbolSize: 6,
      lineStyle: { color: colors[i], width: 2 }, itemStyle: { color: colors[i] },
      markLine: i === 0 ? { symbol: 'none', silent: true, lineStyle: { color: css('--line') }, data: [{ yAxis: 0 }], label: { show: false } } : undefined })),
  });
}

/**
 * Świece z transakcjami. Wycinki świec (D-010) są dzielone na okna z widoczną przerwą między nimi (D-033);
 * markery tylko dla transakcji, których wejście i wyjście leżą w jednym oknie.
 * Zwraca { shown: [{ trade, entry, exit }], hidden, focus(from, to), remove() }.
 */
export function candles(el, bars, trades) {
  const LW = window.LightweightCharts;
  const ch = LW.createChart(el, {
    autoSize: true,
    layout: { background: { color: 'transparent' }, textColor: css('--muted'), fontFamily: 'Inter, system-ui, sans-serif', attributionLogo: false },
    grid: { vertLines: { color: css('--line') }, horzLines: { color: css('--line') } },
    timeScale: { timeVisible: true, secondsVisible: false, borderColor: css('--line') },
    rightPriceScale: { borderColor: css('--line') },
    crosshair: { mode: LW.CrosshairMode.Normal },
    // czas zawsze w UTC (D1) i bez zależności od języka systemu
    localization: { locale: 'pl-PL', timeFormatter: (t) => (barStep(bars) === 86400 ? new Date((t + 3600) * 1000).toISOString().slice(0, 10)
      : new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' ') + ' UTC'),
      priceFormatter: (p) => p.toFixed(bars[0]?.close > 20 ? 3 : 5) },
  });
  ch.applyOptions({ timeScale: { tickMarkFormatter: (t, type) => {
    const d = new Date(t * 1000).toISOString();
    return type <= 1 ? d.slice(0, 7) : type === 2 ? d.slice(5, 10) : d.slice(11, 16);
  } } });
  instances.add(ch);
  const s = ch.addCandlestickSeries({ upColor: css('--ok'), downColor: css('--bad'), borderVisible: false,
    wickUpColor: css('--ok'), wickDownColor: css('--bad'), priceFormat: { type: 'price', precision: bars[0]?.close > 20 ? 3 : 5, minMove: bars[0]?.close > 20 ? 0.001 : 0.00001 } });
  const windows = splitWindows(bars);
  s.setData(seriesData(bars, windows));
  const { shown, hidden } = placeTrades(bars, windows, trades);
  const markers = [];
  for (const { trade: t, entry, exit } of shown) {
    markers.push({ time: entry, position: t.dir > 0 ? 'belowBar' : 'aboveBar', color: css('--accent'),
      shape: t.dir > 0 ? 'arrowUp' : 'arrowDown', text: t.dir > 0 ? 'L' : 'S' });
    markers.push({ time: exit, position: t.dir > 0 ? 'aboveBar' : 'belowBar', color: t.pips_net > 0 ? css('--ok') : css('--bad'),
      shape: 'circle', text: `${t.pips_net > 0 ? '+' : ''}${t.pips_net.toFixed(1)}` });
  }
  markers.sort((a, b) => a.time - b.time);
  s.setMarkers(markers);
  const times = bars.map((b) => b.ts);
  const snap = (t) => {
    let lo = 0, hi = times.length - 1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (times[mid] <= t) lo = mid; else hi = mid - 1; }
    return times[lo];
  };
  const focus = (from, to) => ch.timeScale().setVisibleRange({ from: snap(from), to: snap(to) });
  // transakcja z otoczeniem, ale tylko w jej oknie — sąsiednie okno (inne lata) nie rozciąga skali cen
  const show = (x) => focus(Math.max(x.from, x.entry - 36 * 3600), Math.min(x.to, x.exit + 36 * 3600));
  const last = shown[shown.length - 1];
  if (last) show(last); else ch.timeScale().fitContent();
  return { shown, hidden, focus, show, remove: () => { instances.delete(ch); ch.remove(); } };
}

/** D-076: prognoza zasięgu 3 dni (mediana i pasmo 80%) obok zrealizowanego zasięgu, w pipsach. */
export function rangeBand(el, hist) {
  const b = base();
  const ax = b.axisDefaults;
  const pts = (k) => hist.ts.map((t, i) => [t * 1000, hist[k][i]]);
  return chart(el, {
    ...b,
    grid: { left: 56, right: 16, top: 32, bottom: 36 },
    legend: { top: 0, textStyle: { color: ax.axisLabel.color } },
    tooltip: { ...b.tooltip, trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : `${Math.round(v)} pips`) },
    xAxis: { type: 'time', ...ax, splitLine: { show: false }, axisLabel: { ...ax.axisLabel, formatter: (v) => fmtDate(v).slice(5) } },
    yAxis: { type: 'value', scale: true, ...ax, name: 'pips', nameTextStyle: { color: ax.axisLabel.color } },
    series: [
      { name: 'pasmo 80% (dół)', type: 'line', showSymbol: false, data: pts('low'), lineStyle: { color: css('--dim'), width: 1, type: 'dashed' }, itemStyle: { color: css('--dim') } },
      { name: 'prognoza (mediana)', type: 'line', showSymbol: false, data: pts('mid'), lineStyle: { color: css('--muted'), width: 1.5 }, itemStyle: { color: css('--muted') } },
      { name: 'pasmo 80% (góra)', type: 'line', showSymbol: false, data: pts('high'), lineStyle: { color: css('--dim'), width: 1, type: 'dashed' }, itemStyle: { color: css('--dim') } },
      { name: 'zrealizowany zasięg', type: 'line', showSymbol: false, data: pts('real'), lineStyle: { color: css('--text'), width: 1.75 }, itemStyle: { color: css('--text') } },
    ],
  });
}
