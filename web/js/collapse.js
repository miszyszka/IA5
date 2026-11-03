// Zwijane panele (karta strategii, karta inwestora): klik w nagłówek panelu zwija albo rozwija jego treść.
// Stan zapamiętany w tej przeglądarce (localStorage — tylko wygoda jednego widza, strona działa i bez niego).
const KEY = 'ia5.collapsed';

function load() {
  try { return new Set(JSON.parse(localStorage.getItem(KEY) || '[]')); } catch { return new Set(); }
}
function save(set) {
  try { localStorage.setItem(KEY, JSON.stringify([...set].slice(-200))); } catch { /* prywatne okno */ }
}

/** Nagłówek panelu: pierwszy element, jeśli to .phead albo h3. */
export function headOf(panel) {
  const f = panel.firstElementChild;
  if (!f) return null;
  return f.classList.contains('phead') || f.tagName === 'H3' ? f : null;
}

/** Klucz panelu — id albo tytuł bez liczb (np. „Transakcje · 76” → „Transakcje · #”), w zakresie widoku. */
export function panelKey(scope, id, title) {
  return `${scope}:${id || String(title || '').trim().replace(/\d[\d\s,.]*/g, '#')}`;
}

const keyOf = (scope, p) => {
  const hd = headOf(p);
  return panelKey(scope, p.id, (hd?.querySelector('h3') || hd)?.textContent);
};

/**
 * Włącza zwijanie paneli w `root`. Panele dorysowane później (po filtrach, po wczytaniu) dostają stan automatycznie.
 * Zwraca { setAll(collapsed) } — „zwiń / rozwiń wszystko”.
 */
export function collapsible(root, scope) {
  const set = load();
  const apply = () => {
    for (const p of root.querySelectorAll('.panel')) {
      const hd = headOf(p);
      if (!hd) continue;
      if (!hd.classList.contains('ctoggle')) {
        hd.classList.add('ctoggle');
        hd.setAttribute('tabindex', '0');
        hd.setAttribute('role', 'button');
      }
      const c = set.has(keyOf(scope, p));
      if (p.classList.contains('collapsed') !== c) p.classList.toggle('collapsed', c);
      if (hd.getAttribute('aria-expanded') !== String(!c)) hd.setAttribute('aria-expanded', String(!c));
    }
  };
  const toggle = (hd) => {
    const p = hd.parentElement;
    const k = keyOf(scope, p);
    if (set.has(k)) set.delete(k); else set.add(k);
    save(set);
    apply();
    if (!set.has(k)) window.dispatchEvent(new Event('resize'));   // wykresy w rozwiniętym panelu dostają rozmiar
  };
  if (!root.dataset.collapsible) {
    root.dataset.collapsible = '1';
    root.addEventListener('click', (e) => {
      const hd = e.target.closest('.ctoggle');
      if (!hd || !root.contains(hd)) return;
      const ctl = e.target.closest('button, select, input, a, label, textarea');
      if (ctl && hd.contains(ctl)) return;   // przyciski i filtry w nagłówku działają normalnie
      toggle(hd);
    });
    root.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && e.target.classList?.contains('ctoggle')) { e.preventDefault(); toggle(e.target); }
    });
    let raf = 0;
    new MutationObserver(() => { cancelAnimationFrame(raf); raf = requestAnimationFrame(apply); })
      .observe(root, { childList: true, subtree: true });
  }
  apply();
  return {
    setAll(collapsed) {
      for (const p of root.querySelectorAll('.panel')) {
        if (!headOf(p)) continue;
        const k = keyOf(scope, p);
        if (collapsed) set.add(k); else set.delete(k);
      }
      save(set);
      apply();
      if (!collapsed) window.dispatchEvent(new Event('resize'));
    },
  };
}
