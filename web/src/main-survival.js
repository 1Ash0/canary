import { loadJson } from './data.js';
import { renderSurvival } from './survival.js';
import { shell, fail } from './shell.js';

shell('../', 'survival');
const root = document.querySelector('[data-grids]');
try {
  const grid = await loadJson('../data/survival/grid.json');
  document.querySelector('[data-tag]').textContent = grid.epistemic;
  document.querySelector('[data-desc]').textContent =
    `${grid.description} ${grid.seeds_per_cell} seeded histories per cell, ${grid.n_filler_turns} filler turns, pack: ${grid.pack}.`;
  renderSurvival(root, grid);
} catch (e) {
  fail(root, e);
}
document.documentElement.dataset.ready = 'true';
