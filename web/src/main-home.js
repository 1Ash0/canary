import { loadRun, loadExperiment, loadJson } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail } from './shell.js';
import { splitHeading, riseOnEnter, gsap, MOTION, REDUCE, springEase, ms } from './motion-kit.js';

shell('./', 'home');
const $ = (sel) => document.querySelector(sel);
const playerEl = $('[data-player]');
playerEl.innerHTML = playerMarkup;
const deep = Number(new URLSearchParams(location.search).get('step'));

// Hero choreography: the claim rises line by line; the run starts as the first line lands; the lede
// and action follow. One moving picture at a time: the copy settles before the bars get busy.
let player = null;
const startPlayer = () => player?.start({ step: deep });
const heroRise = document.querySelectorAll('[data-hero-rise]');
gsap.matchMedia().add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
  if (ctx.conditions.reduce) return;
  gsap.from(heroRise, { y: 14, autoAlpha: 0, duration: ms('slow'), ease: springEase('ui', ms('slow')), stagger: 0.1, delay: 0.55 });
});

try {
  const run = await loadRun('./', 'exp001-s19-nvidia');
  player = mountPlayer({ root: playerEl, run, height: { wide: 340, compact: 440 } });
  splitHeading($('[data-split]'), { onFirstLine: startPlayer });
} catch (e) {
  fail(playerEl, e);
  splitHeading($('[data-split]'));
}

// Below the fold: each section's module and data load on demand (ADR-022 point 5), so the first
// view ships only the hero.
const sections = [
  ['[data-lab]', async (el) => {
    const [{ mountLab }, lab, summaries, exp] = await Promise.all([
      import('./lab.js'), loadJson('./data/lab/constraint.json'), loadJson('./data/lab/summaries.json'),
      loadExperiment('./', 'exp001')]);
    const floors = exp.models.filter((m) => m.usable).map((m) => m.floor);
    mountLab(el, lab, summaries, { k: floors.reduce((a, f) => a + f.k, 0), n: floors.reduce((a, f) => a + f.n, 0) });
  }],
  ['[data-compare]', async (el) => {
    const [{ mountCompare }, pair] = await Promise.all([import('./compare.js'), loadExperiment('./', 'exp001_pair')]);
    const runs = await Promise.all(pair.sides.map((s) => loadRun('./', s.run)));
    mountCompare(el, pair, runs);
  }],
  ['[data-consequence]', async (el) => {
    const [{ mountConsequence }, pair] = await Promise.all([import('./consequence.js'), loadExperiment('./', 'exp001_pair')]);
    mountConsequence(el, pair);
  }],
  ['[data-results]', async (el) => {
    // later experiments are optional: a missing file drops its tab, never the section
    const soft = (id) => loadExperiment('./', id).catch(() => null);
    const [{ mountResults }, exp001, exp001b, exp002] = await Promise.all([
      import('./results.js'), loadExperiment('./', 'exp001'), soft('exp001b'), soft('exp002')]);
    mountResults(el, { exp001, exp001b, exp002 });
  }],
  ['[data-survival-mini]', async (el) => {
    const [{ mountSurvivalMini }, grid] = await Promise.all([import('./survival-mini.js'), loadJson('./data/survival/grid.json')]);
    mountSurvivalMini(el, grid);
  }],
];
for (const [sel, mount] of sections) {
  try { await mount($(sel)); } catch (e) { fail($(sel), e); }
}
riseOnEnter(document.querySelectorAll('[data-rise]'));
document.documentElement.dataset.ready = 'true';
