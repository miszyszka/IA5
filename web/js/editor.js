// Okno nowej / poprawianej strategii (CLAUDE.md 10.4). Kontrakt kodu: sekcja 7 i docs/STRATEGIE.md.
import { createStrategy, requestRecalc } from './fb.js';
import { checkStrategyCode } from './metrics.js';
import { $, esc, h, toast } from './util.js';

export const TEMPLATE = `HYPOTHESIS = """Dlaczego ta strategia ma działać — 1–3 zdania, spisane PRZED liczeniem."""

PARAMS = {
    "rsi_level": [25, 30],    # każda wartość = osobny wariant wejścia
}

def signals(df, p, ind):
    # df: świece H1 jednej pary (open, high, low, close), indeks = czas otwarcia UTC
    # zwróć +1 (long) / -1 (short) / 0 na świecy, której ZAMKNIĘCIE daje sygnał
    rsi = ind.rsi(df.close, 14)
    trend = ind.rising(ind.sma(df.close, 200), 5)
    return (trend & ind.cross_below(rsi, p["rsi_level"])).astype("int8")
`;

export function openEditor({ id = null, name = '', hypothesis = '', code = '' } = {}) {
  const codeArea = h('textarea', { class: 'code', spellcheck: 'false', autocapitalize: 'off', autocomplete: 'off', 'aria-label': 'Kod strategii' });
  codeArea.value = code || TEMPLATE;
  const nameIn = h('input', { type: 'text', value: name, placeholder: 'np. Wybicie z zakresu Azji', 'aria-label': 'Nazwa' });
  const hypIn = h('textarea', { rows: 2, placeholder: 'Opcjonalnie — możesz też wpisać HYPOTHESIS w kodzie', 'aria-label': 'Hipoteza' });
  hypIn.value = hypothesis;
  const checks = h('div', { class: 'checks' });
  const submit = h('button', { class: 'btn accent', type: 'submit' }, id ? 'Zapisz i policz ponownie' : 'Wyślij do policzenia');

  const runCheck = () => {
    const { errors, warnings } = checkStrategyCode(codeArea.value);
    checks.innerHTML = [...errors.map((e) => `<div class="chk bad">✘ ${esc(e)}</div>`), ...warnings.map((w) => `<div class="chk warn">⚠ ${esc(w)}</div>`)].join('')
      || '<div class="chk ok">✔ Kontrakt wygląda dobrze. Look-ahead i liczbę sygnałów sprawdzi jeszcze program na Macu.</div>';
    submit.disabled = errors.length > 0;
    return errors.length === 0;
  };
  let t;
  codeArea.addEventListener('input', () => { clearTimeout(t); t = setTimeout(runCheck, 250); });
  codeArea.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const s = codeArea.selectionStart;
      codeArea.setRangeText('    ', s, codeArea.selectionEnd, 'end');
    }
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) form.requestSubmit();
  });

  const form = h('form', { method: 'dialog', class: 'editor' },
    h('div', { class: 'row between' }, h('h2', {}, id ? 'Popraw strategię' : 'Nowa strategia'),
      h('button', { type: 'button', class: 'btn ghost icon', 'aria-label': 'Zamknij', onclick: () => dlg.close() }, '✕')),
    h('label', {}, 'Nazwa', nameIn),
    h('label', {}, 'Hipoteza', hypIn),
    h('label', { class: 'grow' }, h('span', { class: 'row between' }, 'Kod Python',
      h('span', { class: 'hint' }, 'Tab = 4 spacje · Ctrl/⌘+Enter = wyślij · ',
        h('a', { href: 'https://github.com/miszyszka/IA5/blob/main/docs/STRATEGIE.md', target: '_blank', rel: 'noopener' }, 'jak pisać strategie'))), codeArea),
    checks,
    h('div', { class: 'row between' },
      h('button', { type: 'button', class: 'btn ghost', onclick: () => { codeArea.value = TEMPLATE; runCheck(); } }, 'Wstaw szablon'),
      h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn ghost', onclick: () => dlg.close() }, 'Anuluj'), submit)));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!runCheck()) return;
    const n = nameIn.value.trim();
    if (!n) { nameIn.focus(); toast('Podaj nazwę strategii.', 'warn'); return; }
    const hyp = hypIn.value.trim() || (codeArea.value.match(/^HYPOTHESIS\s*=\s*"""([\s\S]*?)"""/m)?.[1] || '').trim();
    submit.disabled = true;
    try {
      if (id) await requestRecalc(id, { name: n, hypothesis: hyp, code: codeArea.value });
      else await createStrategy({ name: n, hypothesis: hyp, code: codeArea.value });
      dlg.close();
      toast(id ? 'Wysłano do ponownego policzenia.' : 'Strategia w kolejce „do policzenia”.', 'ok');
    } catch (err) {
      toast(err.message || String(err), 'bad', 7000);
      submit.disabled = false;
    }
  });

  const dlg = h('dialog', { class: 'modal wide' }, form);
  dlg.addEventListener('close', () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
  runCheck();
  (name ? codeArea : nameIn).focus();
}
