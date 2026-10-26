// Wykresy: ECharts (kapitał, heatmapa, krzywe) i Lightweight Charts (świece z transakcjami).
// Zasada uczciwości (CLAUDE.md 11): bez wygładzania linii, osie z rzeczywistych wartości. Płasko, bez gradientów (D-019).
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

/** Świece z transakcjami. Zwraca { focus(from, to) }. */
export function candles(el, bars, trades) {
  const LW = window.LightweightCharts;
  const ch = LW.createChart(el, {
    autoSize: true,
    layout: { background: { color: 'transparent' }, textColor: css('--muted'), fontFamily: 'Inter, system-ui, sans-serif' },
    grid: { vertLines: { color: css('--line') }, horzLines: { color: css('--line') } },
    timeScale: { timeVisible: true, secondsVisible: false, borderColor: css('--line') },
    rightPriceScale: { borderColor: css('--line') },
    crosshair: { mode: LW.CrosshairMode.Normal },
    // czas zawsze w UTC (D1) i bez zależności od języka systemu
    localization: { locale: 'pl-PL', timeFormatter: (t) => new Date(t * 1000).toISOString().slice(0, 16).replace('T', ' ') + ' UTC',
      priceFormatter: (p) => p.toFixed(bars[0]?.close > 20 ? 3 : 5) },
  });
  ch.applyOptions({ timeScale: { tickMarkFormatter: (t, type) => {
    const d = new Date(t * 1000).toISOString();
    return type <= 1 ? d.slice(0, 7) : type === 2 ? d.slice(5, 10) : d.slice(11, 16);
  } } });
  instances.add(ch);
  const s = ch.addCandlestickSeries({ upColor: css('--ok'), downColor: css('--bad'), borderVisible: false,
    wickUpColor: css('--ok'), wickDownColor: css('--bad'), priceFormat: { type: 'price', precision: bars[0]?.close > 20 ? 3 : 5, minMove: bars[0]?.close > 20 ? 0.001 : 0.00001 } });
  s.setData(bars.map((b) => ({ time: b.ts, open: b.open, high: b.high, low: b.low, close: b.close })));
  const times = bars.map((b) => b.ts);
  const snap = (t) => { // marker musi wskazywać istniejącą świecę
    let lo = 0, hi = times.length - 1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (times[mid] <= t) lo = mid; else hi = mid - 1; }
    return times[lo];
  };
  const markers = [];
  for (const t of trades) {
    markers.push({ time: snap(t.entry_ts), position: t.dir > 0 ? 'belowBar' : 'aboveBar', color: css('--accent'),
      shape: t.dir > 0 ? 'arrowUp' : 'arrowDown', text: t.dir > 0 ? 'L' : 'S' });
    markers.push({ time: snap(t.exit_ts - 1), position: t.dir > 0 ? 'aboveBar' : 'belowBar', color: t.pips_net > 0 ? css('--ok') : css('--bad'),
      shape: 'circle', text: `${t.pips_net > 0 ? '+' : ''}${t.pips_net.toFixed(1)}` });
  }
  markers.sort((a, b) => a.time - b.time);
  s.setMarkers(markers);
  ch.timeScale().fitContent();
  return {
    focus: (from, to) => ch.timeScale().setVisibleRange({ from: snap(from), to: snap(to) }),
    remove: () => { instances.delete(ch); ch.remove(); },
  };
}
