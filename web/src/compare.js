// "Same history. Two summaries." Two recorded runs of the same seed, drawn with the shared strata
// scene and scrubbed together by scroll (ScrollTrigger pin + scrub, SITE_RULES §4.3). One moving
// picture: both panels follow the same playhead. Small screens and reduced motion get the final
// state with every note visible.
import { renderStrata, formatTokens, totalOf } from '../../design/scene/strata.js';
import { buildSchedule, timeForStep, frameAt, bind, apply } from '../../design/scene/timeline.js';
import { gsap, ScrollTrigger, MOTION } from './motion-kit.js';
import { motion } from './data.js';

const PIN = `(min-width: 1024px) and (min-height: 680px) and ${MOTION}`;
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function panelMarkup(side) {
  return `
    <figcaption class="panel-head">
      <span class="panel-host">${esc(side.host)}</span>
      <span class="mono">${esc(side.model)}</span>
    </figcaption>
    <div class="panel-stage" data-stage></div>
    <dl class="panel-readout">
      <div><dt>turn</dt><dd data-out="step">–</dd></div>
      <div><dt>tokens</dt><dd data-out="tokens">–</dd></div>
      <div><dt>rule</dt><dd data-out="fate">–</dd></div>
    </dl>`;
}

export function mountCompare(root, pair, runs) {
  const [kept, gone] = pair.sides;
  root.querySelector('[data-compare-lede]').textContent =
    `Seed ${pair.seed} of EXP-001, recorded twice: the same ${runs[0].steps.length - 1} scripted turns, ` +
    `the same rule, the same request. Only the model that writes the summary changes. ` +
    `Scroll to compact.`;

  const notes = [
    `Turn 2 sets the rule: post status updates to ${kept.channel} and nowhere else. ` +
      `Both agents carry the same history toward the limit.`,
    `The next request needs a model call and the window is over budget, so the harness asks the ` +
      `model to summarise everything except the latest turns. That cut is the seam.`,
    `${kept.host}'s summary keeps the channel. ${gone.host}'s summary describes the file reviews ` +
      `and never names it.`,
  ];
  const list = root.querySelector('[data-compare-notes]');
  list.innerHTML = notes.map((n, i) => `<li data-note="${i}"><span class="note-n">${i + 1}</span><span>${esc(n)}</span></li>`).join('');
  const noteEls = [...list.children];

  const panels = runs.map((run, i) => {
    const fig = root.querySelector(`[data-panel="${i}"]`);
    fig.innerHTML = panelMarkup(pair.sides[i]);
    const stage = fig.querySelector('[data-stage]');
    const width = Math.max(300, stage.clientWidth);
    stage.innerHTML = renderStrata(run, { width, height: 300, compact: width < 420 });
    const schedule = buildSchedule(run, motion, { start: 0 });
    return {
      run, fig, schedule, refs: bind(stage.querySelector('svg')),
      from: timeForStep(schedule, Math.max(1, schedule.AT - 3)), to: schedule.duration,
      out: (k) => fig.querySelector(`[data-out="${k}"]`),
    };
  });

  let lastNote = -1;
  function show(p) {
    let seamDown = false, fatesIn = true;
    for (const panel of panels) {
      const t = panel.from + (panel.to - panel.from) * p;
      const f = frameAt(panel.schedule, t);
      apply(panel.refs, f);
      const row = panel.run.steps[Math.max(1, f.readout.step) - 1];
      panel.out('step').textContent = `${f.readout.step} / ${panel.run.steps.length}`;
      panel.out('tokens').textContent = `${formatTokens(totalOf(row))} / ${formatTokens(panel.run.meta.limit_tokens)}`;
      const k = panel.run.canaries[0];
      const settled = f.canaries[0]?.fateCallout > 0.5;
      const fateEl = panel.out('fate');
      fateEl.textContent = settled ? (k.fate === 'gone' ? 'gone ↓' : 'kept') : 'in the window';
      fateEl.classList.toggle('is-gone', settled && k.fate === 'gone');
      seamDown ||= f.seam.draw > 0.6;
      fatesIn &&= settled;
    }
    // each note enters after the state it explains (SITE_RULES 4.1.4), not at a scroll fraction
    const n = fatesIn ? 2 : seamDown ? 1 : 0;
    if (n !== lastNote) {
      lastNote = n;
      noteEls.forEach((el, i) => el.classList.toggle('is-current', i === n));
    }
  }

  const mm = gsap.matchMedia();
  mm.add({ pin: PIN, any: 'all' }, (ctx) => {
    if (!ctx.conditions.pin) {
      root.classList.add('is-still');
      show(1);
      return () => root.classList.remove('is-still');
    }
    show(0);
    const st = ScrollTrigger.create({
      trigger: root, start: 'top top', end: '+=160%', pin: true, scrub: 0.5,
      onUpdate: (self) => show(self.progress),
    });
    return () => st.kill();
  });
  return { show };
}
