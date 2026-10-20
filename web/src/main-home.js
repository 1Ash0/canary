import { loadRun, loadExperiment, loadJson } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail } from './shell.js';
import { splitHeading, riseOnEnter, gsap, MOTION, REDUCE, springEase, ms } from './motion-kit.js';
import { mountCompare } from './compare.js';
import { mountConsequence } from './consequence.js';
import { mountResults } from './results.js';
import { mountSurvivalMini } from './survival-mini.js';

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

const sections = [
  ['[data-compare]', async (el) => {
    const pair = await loadExperiment('./', 'exp001_pair');
    const runs = await Promise.all(pair.sides.map((s) => loadRun('./', s.run)));
    mountCompare(el, pair, runs);
  }],
  ['[data-consequence]', async (el) => mountConsequence(el, await loadExperiment('./', 'exp001_pair'))],
  ['[data-results]', async (el) => mountResults(el, await loadExperiment('./', 'exp001'))],
  ['[data-survival-mini]', async (el) => mountSurvivalMini(el, await loadJson('./data/survival/grid.json'))],
];
for (const [sel, mount] of sections) {
  try { await mount($(sel)); } catch (e) { fail($(sel), e); }
}
riseOnEnter(document.querySelectorAll('[data-rise]'));
document.documentElement.dataset.ready = 'true';
