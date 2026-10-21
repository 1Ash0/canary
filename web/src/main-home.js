import { loadRun, loadExperiment, loadJson } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail } from './shell.js';
import { splitHeading, riseOnEnter, gsap, ScrollTrigger, MOTION, REDUCE, springEase, ms } from './motion-kit.js';

shell('./', 'home');
const $ = (sel) => document.querySelector(sel);
const playerEl = $('[data-player]');
playerEl.innerHTML = playerMarkup;
const deep = Number(new URLSearchParams(location.search).get('step'));

// Hero choreography: the claim rises line by line; the run starts as the first line lands; the lede
// and action follow. One moving picture at a time: the copy settles before the bars get busy.
// The hero plays the shared episode's second panel when the URL names one (a shared link opens on
// that run), else EXP-002 seed 19 with gpt-oss-20b's summary: the run the comparison starts on.
function heroRunId() {
  const q = new URLSearchParams(location.search);
  const seed = Number(q.get('seed') ?? 19);
  const [tag, policy] = (q.get('b') ?? 'nvidia.llm_summary').split('.');
  const ok = Number.isInteger(seed) && seed >= 1 && seed <= 27 && /^(mistral|nvidia)$/.test(tag)
    && /^(recency_truncate|head_tail|observation_mask|llm_summary)$/.test(policy ?? '');
  return ok ? `exp002-s${seed}-${tag}-${policy}-constraint` : 'exp002-s19-nvidia-llm_summary-constraint';
}

let player = null;
const startPlayer = () => player?.start({ step: deep });
const heroRise = document.querySelectorAll('[data-hero-rise]');
gsap.matchMedia().add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
  if (ctx.conditions.reduce) return;
  gsap.from(heroRise, { y: 14, autoAlpha: 0, duration: ms('slow'), ease: springEase('ui', ms('slow')), stagger: 0.1, delay: 0.55 });
});

try {
  const run = await loadRun('./', heroRunId());
  document.querySelector('[data-hero-recorder]')?.setAttribute('href', `./run/?run=${run.meta.run_id}`);
  player = mountPlayer({ root: playerEl, run, height: { wide: 340, compact: 440 } });
  splitHeading($('[data-split]'), { onFirstLine: startPlayer });
} catch (e) {
  fail(playerEl, e);
  splitHeading($('[data-split]'));
}

// Below the fold: each section's module and data load on demand (ADR-022 point 5), so the first
// view ships only the hero.
// One shared episode for the comparison, the consequence and the results (episode.js), built on
// first use from EXP-002's file.
let episodes = null;
const getEpisodes = () => (episodes ??= Promise.all([import('./episode.js'), loadExperiment('./', 'exp002')])
  .then(([{ createEpisodes }, exp]) => createEpisodes(exp)));

const sections = [
  ['[data-lab]', async (el) => {
    const [{ mountLab }, lab, summaries, exp, exp002] = await Promise.all([
      import('./lab.js'), loadJson('./data/lab/constraint.json'), loadJson('./data/lab/summaries.json'),
      loadExperiment('./', 'exp001'), loadExperiment('./', 'exp002').catch(() => null)]);
    const floors = exp.models.filter((m) => m.usable).map((m) => m.floor);
    mountLab(el, lab, summaries, { k: floors.reduce((a, f) => a + f.k, 0), n: floors.reduce((a, f) => a + f.n, 0) }, exp002);
  }],
  ['[data-compare]', async (el) => {
    const [{ mountCompare }, ep] = await Promise.all([import('./compare.js'), getEpisodes()]);
    await mountCompare(el, ep, loadRun).ready;
  }],
  ['[data-consequence]', async (el) => {
    const [{ mountConsequence }, ep] = await Promise.all([import('./consequence.js'), getEpisodes()]);
    await mountConsequence(el, ep, loadRun);
  }],
  ['[data-results]', async (el) => {
    // later experiments are optional: a missing file drops its tab, never the section
    const soft = (id) => loadExperiment('./', id).catch(() => null);
    const [{ mountResults }, exp001, exp001b, exp002] = await Promise.all([
      import('./results.js'), loadExperiment('./', 'exp001'), soft('exp001b'), soft('exp002')]);
    mountResults(el, { exp001, exp001b, exp002 }, exp002 ? await getEpisodes() : null);
  }],
  ['[data-survival-mini]', async (el) => {
    const [{ mountSurvivalMini }, grid] = await Promise.all([import('./survival-mini.js'), loadJson('./data/survival/grid.json')]);
    mountSurvivalMini(el, grid);
  }],
];
// A section's code and data are fetched when it comes within half a screen of the viewport, not at
// load, so the first view ships only the hero. <html data-mounted> counts mounted sections for QA.
const root = document.documentElement;
root.dataset.sections = String(sections.length);
root.dataset.mounted = '0';
const pending = new Map(sections.map(([sel, mount]) => [$(sel), mount]));
const io = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting || !pending.has(entry.target)) continue;
    const mount = pending.get(entry.target);
    pending.delete(entry.target);
    io.unobserve(entry.target);
    mount(entry.target).catch((e) => fail(entry.target, e)).finally(() => {
      root.dataset.mounted = String(+root.dataset.mounted + 1);
      ScrollTrigger.refresh();  // a mounted section changes the page height under every trigger
    });
  }
}, { rootMargin: '50% 0px' });
pending.forEach((_, el) => io.observe(el));
riseOnEnter(document.querySelectorAll('[data-rise]'));
root.dataset.ready = 'true';
