// A compact survival grid for the landing page: three deterministic policies x five budgets, rule at
// turn 1. From survival/grid.json only. Cells fill one by one (--stagger-cells) as the block enters.
import { onEnterOnce, ms } from './motion-kit.js';
import { motion } from './data.js';

const NAMES = { recency_truncate: 'Recency truncate', head_tail: 'Head and tail', observation_mask: 'Observation mask' };

export function mountSurvivalMini(root, grid, position = 1) {
  const at = (p, b) => grid.cells.find((c) => c.policy === p && c.position === position && c.budget === b);
  const head = grid.budgets.map((b) => `<th scope="col">${b.toLocaleString('en')}</th>`).join('');
  const rows = grid.policies.map((p) => `<tr><th scope="row">${NAMES[p] ?? p}</th>${grid.budgets.map((b) => {
    const c = at(p, b);
    if (!c || !c.n) return '<td class="empty">n/a</td>';
    const gone = c.k_kept === 0;
    return `<td class="${gone ? 'is-gone' : ''}"><span class="mini-fill" data-fill style="--rate:${c.rate}"></span><span class="v">${c.k_kept}/${c.n}</span>${gone ? '<span class="g">gone ↓</span>' : ''}</td>`;
  }).join('')}</tr>`).join('');
  root.innerHTML = `
    <div class="table-scroll" tabindex="0" role="region" aria-label="Policy survival table"><table class="surv-grid mini">
      <caption class="visually-hidden">Rule at turn ${position}: histories in which it is still in the window, by policy and window budget in tokens</caption>
      <thead><tr><th scope="col"><span class="visually-hidden">Policy</span>budget →</th>${head}</tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
    <p class="caveat"><span class="tag">${grid.epistemic}</span> ${grid.description} ${grid.seeds_per_cell} seeded histories per cell; every budget is smaller than the full history, so each one forces a compaction.</p>`;
  onEnterOnce(root, (tl) => {
    tl.from(root.querySelectorAll('[data-fill]'), { scaleY: 0, duration: ms('base'), ease: 'power2.out', stagger: motion.stagger.cells / 1000 });
    tl.from(root.querySelectorAll('td .v, td .g'), { autoAlpha: 0, duration: ms('micro'), stagger: motion.stagger.cells / 2000 }, 0.3);
  });
}
