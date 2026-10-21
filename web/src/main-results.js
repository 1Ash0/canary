// Chapter 3, Results: one tab per preregistered experiment. A mark on an EXP-002 row opens that
// episode in chapter 2 (the comparison); a modified click opens it in the recorder.
import { loadExperiment, BASE } from './data.js';
import { shell } from './shell.js';
import { splitHeading } from './motion-kit.js';
import { getEpisodes, lazySections } from './sections.js';

shell(BASE, 'results');
splitHeading(document.querySelector('[data-split]'));

lazySections([
  ['[data-results]', async (el) => {
    // later experiments are optional: a missing file drops its tab, never the page
    const soft = (id) => loadExperiment(BASE, id).catch(() => null);
    const [{ mountResults }, exp001, exp001b, exp002, exp004] = await Promise.all([
      import('./results.js'), loadExperiment(BASE, 'exp001'), soft('exp001b'), soft('exp002'), soft('exp004')]);
    mountResults(el, { exp001, exp001b, exp002, exp004 }, exp002 ? await getEpisodes() : null);
  }],
]);
document.documentElement.dataset.ready = 'true';
