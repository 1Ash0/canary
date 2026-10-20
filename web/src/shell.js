// Header and footer shared by every page. `base` is the page's depth ('./' or '../').
// No repository link yet: the repo has no remote. Add one when it is published.
export function shell(base, current) {
  const link = (href, text, key) =>
    `<a href="${href}"${current === key ? ' aria-current="page"' : ''}>${text}</a>`;
  document.querySelector('[data-header]').innerHTML = `
    <a class="wordmark" href="${base}" translate="no">canary</a>
    <nav aria-label="Primary">
      ${link(`${base}run/?run=synthetic-001`, 'Recorder', 'run')}
      ${link(`${base}survival/`, 'Survival', 'survival')}
      ${link(`${base}about/`, 'About', 'about')}
    </nav>`;
  document.querySelector('[data-footer]').innerHTML = `
    <span><span translate="no">canary</span> · the <code translate="no">ctxcheck</code> toolkit</span>
    <span>MIT licence</span>`;
}

export function fail(el, error) {
  el.innerHTML = `<p class="note">Could not load the data: ${String(error.message ?? error)}</p>`;
}
