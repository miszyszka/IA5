// Przegląd zdrowia (D-023) — czyste funkcje (testy: tests/web). Dane: meta/status.health, zapisywane przez Maca co godzinę.
export const STALE_S = 2 * 3600;
const RANK = { ok: 0, warn: 1, bad: 2 };

/**
 * Widok przeglądu: dokłada kontrolę „samo sprawdzanie”, bo cisza nie może wyglądać jak „wszystko OK”.
 * Zwraca { state, summary, facts, checks, problems, at } albo null, gdy przeglądu jeszcze nie było.
 */
export function healthView(health, now, macOnline) {
  if (!health?.checks) {
    return {
      state: 'warn', at: null, facts: [], problems: 1,
      summary: 'Przegląd zdrowia jeszcze się nie odbył — zrobi go Mac po ia5 start (albo ręcznie: ia5 health).',
      checks: [{ id: 'watchdog', name: 'Sprawdzanie', state: 'warn', text: 'Brak pierwszego przeglądu.', detail: [], fix: 'Na Macu: git pull, potem ia5 start.' }],
    };
  }
  const age = now - health.at;
  const checks = [...health.checks];
  if (age > STALE_S) {
    checks.unshift({
      id: 'watchdog', name: 'Sprawdzanie', state: 'warn',
      text: `Ostatni przegląd ${Math.round(age / 3600)} h temu — poniższe wyniki mogą być nieaktualne${macOnline ? '' : ' (Mac rozłączony)'}.`,
      detail: [], fix: macOnline ? 'Przegląd odbywa się co godzinę; jeśli stoi — zrestartuj ia5 start.' : 'Uruchom ia5 start na Macu.',
    });
  }
  const problems = checks.filter((c) => c.state !== 'ok').length;
  const state = checks.reduce((s, c) => (RANK[c.state] > RANK[s] ? c.state : s), 'ok');
  const summary = age > STALE_S ? `${checks[0].text} Ostatnio: ${health.summary}` : health.summary;
  return { state, summary, facts: health.facts || [], checks, problems, at: health.at };
}

/** Kontrole posortowane: najpierw błędy, potem uwagi, potem OK (kolejność z Maca wewnątrz grupy). */
export function sortChecks(checks) {
  return checks.map((c, i) => [c, i]).sort((a, b) => RANK[b[0].state] - RANK[a[0].state] || a[1] - b[1]).map(([c]) => c);
}

export const problemWord = (n) => (n === 1 ? 'problem' : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14) ? 'problemy' : 'problemów');
