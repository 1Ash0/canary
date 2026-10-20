// Renders the mechanical survival grid as one accessible table per policy. Values come only from the
// exported grid JSON. A cell where the rule never survived says "gone ↓" in words, never colour alone.
const NAMES = {
  recency_truncate: 'Recency truncate',
  head_tail: 'Head and tail',
  observation_mask: 'Observation mask',
};
const BLURB = {
  recency_truncate: 'Drops the oldest turns first. Anything planted early is the first to go.',
  head_tail: 'Keeps the start and the newest turns, drops the middle. The start is small.',
  observation_mask: 'Hides old tool outputs but keeps what was said, until that is not enough.',
};
const pct = (x) => `${Math.round(x * 100)}%`;

function cell(c) {
  if (!c.n) return '<td class="empty"><span class="v">n/a</span></td>';
  const gone = c.k_kept === 0;
  const title = `${c.k_kept} of ${c.n} kept, ${pct(c.rate)}, interval ${pct(c.wilson_lo)} to ${pct(c.wilson_hi)}`;
  return `<td class="${gone ? 'is-gone' : ''}" style="--rate:${c.rate}" title="${title}">
    <span class="v">${c.k_kept}/${c.n}</span>${gone ? '<span class="g">gone ↓</span>' : ''}</td>`;
}

function table(grid, policy) {
  const at = (position, budget) =>
    grid.cells.find((c) => c.policy === policy && c.position === position && c.budget === budget);
  const head = grid.budgets.map((b) => `<th scope="col">${b.toLocaleString('en')}</th>`).join('');
  const rows = grid.positions
    .map((p) => `<tr><th scope="row">turn ${p}</th>${grid.budgets.map((b) => cell(at(p, b))).join('')}</tr>`)
    .join('');
  return `<section class="grid-block" aria-labelledby="g-${policy}">
    <h2 id="g-${policy}">${NAMES[policy] ?? policy}</h2>
    <p class="note">${BLURB[policy] ?? ''}</p>
    <table class="surv-grid">
      <caption class="visually-hidden">Rule survival for ${NAMES[policy] ?? policy}: planted turn by window budget in tokens</caption>
      <thead><tr><th scope="col"><span class="visually-hidden">Planted at</span></th>${head}</tr></thead>
      <tbody>${rows}</tbody>
    </table>
  </section>`;
}

export function renderSurvival(root, grid) {
  root.innerHTML = grid.policies.map((p) => table(grid, p)).join('');
}
