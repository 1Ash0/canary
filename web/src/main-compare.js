// Chapter 2, Compare: the shared episode (canary, seed, two recorded ways of making room) as a
// scrubbed pair of windows, then the request and the tool call each agent made. Both follow the
// episode in the URL, so a link from the Lab or the results opens on exactly that choice.
import { loadRun, BASE } from './data.js';
import { shell } from './shell.js';
import { splitHeading } from './motion-kit.js';
import { getEpisodes, lazySections } from './sections.js';

shell(BASE, 'compare');
splitHeading(document.querySelector('[data-split]'));

lazySections([
  ['[data-compare]', async (el) => {
    const [{ mountCompare }, ep] = await Promise.all([import('./compare.js'), getEpisodes()]);
    await mountCompare(el, ep, loadRun).ready;
  }],
  ['[data-consequence]', async (el) => {
    const [{ mountConsequence }, ep] = await Promise.all([import('./consequence.js'), getEpisodes()]);
    await mountConsequence(el, ep, loadRun);
  }],
]);
document.documentElement.dataset.ready = 'true';
