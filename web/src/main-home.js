import { loadRun, loadExperiment } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { renderExperiment } from './experiment.js';
import { shell, fail } from './shell.js';

shell('./', 'home');
const playerEl = document.querySelector('[data-player]');
const expEl = document.querySelector('[data-experiment]');
playerEl.innerHTML = playerMarkup;

const deep = Number(new URLSearchParams(location.search).get('step'));

try {
  const run = await loadRun('./', 'synthetic-001');
  const player = mountPlayer({ root: playerEl, run, height: { wide: 340, compact: 460 } });
  player.start({ step: deep });
  document.documentElement.dataset.ready = 'true';
} catch (e) {
  fail(playerEl, e);
}
try {
  renderExperiment(expEl, await loadExperiment('./', 'mock_exp_001'));
} catch (e) {
  fail(expEl, e);
}
document.documentElement.dataset.ready = 'true';
