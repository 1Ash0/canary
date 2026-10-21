// Header and footer shared by every page. `base` is the page's depth ('./' or '../').
// The site reads as four chapters (lab, compare, results, method); each page ends by pointing at the
// next one, so the pages form one argument rather than a set of tabs. The shared episode (?seed=,
// ?a=, ?b=, ?canary=) travels with the chapter links, so a choice made on one page carries on.
export const CHAPTERS = [
  { key: 'lab', href: 'lab/', label: 'Lab', title: 'You are the harness', line: 'Compact a real history yourself and watch what survives.' },
  { key: 'compare', href: 'compare/', label: 'Compare', title: 'Two ways to make room', line: 'The same recorded history, compacted two ways, and what each agent did next.' },
  { key: 'results', href: 'results/', label: 'Results', title: 'What the experiments found', line: 'Four preregistered experiments, every seed one click from its episode.' },
  { key: 'about', href: 'about/', label: 'Method', title: 'How it is judged', line: 'The grade, the conditions, the statistics, the limits and the prior art.' },
];
const EPISODE_KEYS = ['canary', 'seed', 'a', 'b'];

// the current episode's query string, for links between chapters
export function episodeQuery() {
  const q = new URLSearchParams(location.search);
  const out = new URLSearchParams();
  EPISODE_KEYS.forEach((k) => { if (q.get(k)) out.set(k, q.get(k)); });
  const s = out.toString();
  return s ? `?${s}` : '';
}

export function shell(base, current) {
  const link = (href, text, key) =>
    `<a href="${href}"${current === key ? ' aria-current="page"' : ''}>${text}</a>`;
  const q = episodeQuery();
  document.querySelector('[data-header]').innerHTML = `
    <a class="wordmark" href="${base}${q}" translate="no">canary</a>
    <nav aria-label="Primary">
      ${CHAPTERS.map((c) => link(`${base}${c.href}${c.key === 'about' ? '' : q}`, c.label, c.key)).join('')}
      ${link(`${base}run/`, 'Recorder', 'run')}
      <a href="https://github.com/1Ash0/canary">GitHub</a>
    </nav>`;
  const at = CHAPTERS.findIndex((c) => c.key === current);
  const next = at >= 0 ? CHAPTERS[at + 1] : current === 'home' ? CHAPTERS[0] : null;
  const nextEl = document.querySelector('[data-next]');
  if (nextEl && next) {
    nextEl.innerHTML = `<a class="next-chapter" href="${base}${next.href}${next.key === 'about' ? '' : q}">
      <span class="lab-label">Next · ${CHAPTERS.indexOf(next) + 1} of ${CHAPTERS.length}</span>
      <span class="next-title">${next.title} →</span>
      <span class="note">${next.line}</span></a>`;
  }
  document.querySelector('[data-footer]').innerHTML = `
    <span><span translate="no">canary</span> · the <code translate="no">ctxcheck</code> toolkit</span>
    <span><a href="https://github.com/1Ash0/canary">Source on GitHub</a> · MIT licence</span>`;
}

export function fail(el, error) {
  el.innerHTML = `<p class="note">Could not load the data: ${String(error.message ?? error)}</p>`;
}
