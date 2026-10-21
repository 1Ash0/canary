import { loadRun } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail, CHAPTERS, episodeQuery } from './shell.js';
import { splitHeading, riseOnEnter, gsap, MOTION, REDUCE, springEase, ms } from './motion-kit.js';

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

// The chapters: each one a link carrying the current episode, with the line that says what it holds.
document.querySelector('[data-chapters]').innerHTML = CHAPTERS.map((c, n) => `
  <li data-rise><a class="chapter" href="./${c.href}${c.key === 'about' ? '' : episodeQuery()}">
    <span class="chapter-n">${n + 1}</span>
    <span class="chapter-title">${c.title}</span>
    <span class="chapter-line">${c.line}</span>
    <span class="chapter-go" aria-hidden="true">→</span></a></li>`).join('');
riseOnEnter(document.querySelectorAll('[data-rise]'));
document.documentElement.dataset.ready = 'true';
