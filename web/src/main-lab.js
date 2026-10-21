// Chapter 1, the Lab: compact a real seeded history yourself (simulated: real policy code, no model),
// with the recorded outcome for the same window, and the deterministic policy grid beneath it. A grid
// cell loads its policy and budget into the Lab; "Compare this history" opens chapter 2 on that seed.
import { loadJson, loadExperiment, BASE } from './data.js';
import { shell } from './shell.js';
import { splitHeading, riseOnEnter } from './motion-kit.js';
import { getEpisodes, goTo, lazySections } from './sections.js';

shell(BASE, 'lab');
splitHeading(document.querySelector('[data-split]'));
let labApi = null;

lazySections([
  ['[data-lab]', async (el) => {
    const [{ mountLab }, lab, summaries, exp, exp002, multi, exp004] = await Promise.all([
      import('./lab.js'), loadJson(`${BASE}data/lab/constraint.json`), loadJson(`${BASE}data/lab/summaries.json`),
      loadExperiment(BASE, 'exp001'), loadExperiment(BASE, 'exp002').catch(() => null),
      loadJson(`${BASE}data/lab/multi.json`).catch(() => null), loadExperiment(BASE, 'exp004').catch(() => null)]);
    // the floor from the same experiment as the recorded lines below (EXP-002), both models
    const floors = (exp002?.blocks ?? []).filter((b) => b.pack === 'constraint')
      .map((b) => b.rows.find((r) => r.label === 'floor')).filter(Boolean);
    if (!floors.length) floors.push(...exp.models.filter((m) => m.usable).map((m) => m.floor));
    // one rule: the same policy for both models; three facts (Mistral only): this policy against
    // masking, which keeps every fact, on the middle fact's request
    const toCompare = exp002 ? async (seed, policy, mode) => {
      const ep = await getEpisodes();
      if (mode === 'three' && exp004) {
        const other = policy === 'observation_mask' ? 'head_tail' : 'observation_mask';
        ep.set({ canary: 'multi_code', seed, a: `mistral.${other}`, b: `mistral.${policy}` });
      } else {
        ep.set({ canary: 'constraint', seed, a: `mistral.${policy}`, b: `nvidia.${policy}` });
      }
      goTo('#compare', 'compare');
    } : null;
    labApi = mountLab(el, lab, summaries, { k: floors.reduce((a, f) => a + f.k, 0), n: floors.reduce((a, f) => a + f.n, 0) }, exp002, toCompare, multi, exp004);
  }],
  ['[data-survival-mini]', async (el) => {
    const [{ mountSurvivalMini }, grid] = await Promise.all([import('./survival-mini.js'), loadJson(`${BASE}data/survival/grid.json`)]);
    mountSurvivalMini(el, grid, 1, (policy, budget) => {
      if (!labApi) return;
      labApi.set({ policy, limit: budget, position: 1 });
      goTo('#lab', 'lab');
    });
  }],
]);
riseOnEnter(document.querySelectorAll('[data-rise]'));
document.documentElement.dataset.ready = 'true';
