// "What the agent did next": for the two runs in the comparison, what the window still held about
// the rule (the summary itself, or whether the rule's turn survived the policy), then the tool call
// each agent emitted. Follows the shared episode, from the recorded run files only. Choreography
// (SITE_RULES §4.3): the columns rise, the tool calls type in line by line, and "behaviour changed"
// lands once on the seam spring. A later pick swaps the columns without replaying that entrance.
import { onEnterOnce, springEase, ms, gsap, REDUCE } from './motion-kit.js';
import { POLICY_NAME } from './episode.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Summaries arrive with markdown emphasis and dash variants; show plain text and mark the channel.
function quote(text, channel) {
  const plain = esc(text.replace(/^\[Summary of earlier conversation\]\s*/, '').replace(/\*\*/g, '')).replace(/[‐-―−]/g, '-');
  return channel && plain.includes(channel) ? plain.split(channel).join(`<mark>${esc(channel)}</mark>`) : plain;
}

// The agent's reply after the request: "[tool_call post_status {json}]" in the transcript.
function callOf(run) {
  const probeStep = run.steps.length;
  const reply = run.transcript.find((m) => m.role === 'assistant' && m.step === probeStep && m.text.startsWith('[tool_call'));
  if (!reply) return null;
  try { return JSON.parse(reply.text.slice(reply.text.indexOf('{'), reply.text.lastIndexOf('}') + 1)); } catch { return null; }
}

function column(side, run, outcome, rule) {
  const lost = run.canaries[0].fate === 'gone';
  const call = callOf(run);
  const broke = outcome.grade === 'violated';
  const summary = run.transcript.find((m) => m.origin === 'summary');
  const held = side.policy === 'llm_summary' && summary
    ? `<p class="cons-label">Its summary of the earlier turns</p>
       <blockquote class="cons-quote">${quote(summary.text, rule)}</blockquote>
       <p class="cons-check">${lost ? 'Names no channel.' : `Names <span class="mono">${esc(rule)}</span>.`}</p>`
    : `<p class="cons-label">What ${esc(POLICY_NAME[side.policy])} left in the window</p>
       <p class="cons-check">${lost ? 'The rule\'s turn was cut. Nothing in the window names the channel.' : `The rule's turn is still there, word for word: <span class="mono">${esc(rule)}</span>.`}</p>`;
  const verdict = outcome.grade === 'not_applicable'
    ? 'no post'
    : broke ? `behaviour changed ↓ <span class="dim">the rule said ${esc(rule)}</span>` : 'rule followed';
  return `
    <article class="cons-col${lost ? ' is-lost' : ''}" data-cons-col>
      <header class="cons-head">
        <span class="panel-host">${esc(side.host)}</span>
        <span class="mono">${esc(POLICY_NAME[side.policy])}</span>
      </header>
      ${held}
      <p class="cons-label">The tool call it emitted next</p>
      ${call ? `<pre class="cons-call"><code><span class="cons-line" data-line>post_status(</span><span class="cons-line" data-line>  channel=<span class="${broke ? 'is-loss' : 'is-ok'}">"${esc(call.channel)}"</span>,</span><span class="cons-line" data-line>  text="${esc(call.text ?? '')}"</span><span class="cons-line" data-line>)</span></code></pre>`
        : '<p class="cons-check">It made no post.</p>'}
      <p class="cons-verdict ${broke ? 'is-loss' : ''}" data-verdict>${verdict}</p>
      <p class="note"><a href="./run/?run=${encodeURIComponent(outcome.run)}">Open this episode in the recorder</a></p>
    </article>`;
}

export function mountConsequence(root, ep, loadRun) {
  const cache = new Map();
  const getRun = (id) => { if (!cache.has(id)) cache.set(id, loadRun('./', id)); return cache.get(id); };
  let token = 0, entered = false;

  async function draw(state) {
    const mine = ++token;
    const keys = [state.a, state.b];
    const outcomes = keys.map((k) => ep.outcome(k, state.seed));
    const runs = await Promise.all(outcomes.map((o) => getRun(o.run)));
    if (mine !== token) return;
    const rule = runs[0].canaries[0].text;
    root.innerHTML = `
      <p class="exp-intro">Then each agent was asked to post this week's status. The request lists four channels, the right one among them, and says nothing about the rule.</p>
      <div class="cons-grid">${keys.map((k, i) => column(ep.side(k), runs[i], outcomes[i], rule)).join('')}</div>
      <p class="caveat"><span class="tag">recorded</span> EXP-002, seed ${state.seed}, treatment condition, prompt v1 for summaries. Sources: <span class="mono">${esc(runs.map((r) => r.meta.source).join(', '))}</span>.</p>`;
    if (entered && !matchMedia(REDUCE).matches) {
      gsap.from(root.querySelectorAll('[data-cons-col]'), { autoAlpha: 0, y: 6, duration: ms('base'), ease: 'power2.out', stagger: 0.06 });
    }
    return root;
  }

  ep.on(draw);
  return draw(ep.get()).then(() => {
    onEnterOnce(root, (tl) => {
      entered = true;
      const cols = root.querySelectorAll('[data-cons-col]');
      tl.from(cols, { y: 16, autoAlpha: 0, duration: ms('slow'), ease: 'power2.out', stagger: 0.12 });
      cols.forEach((col, i) => {
        tl.from(col.querySelectorAll('[data-line]'), {
          autoAlpha: 0, x: -6, duration: ms('micro'), ease: 'power1.out', stagger: 0.09,
        }, 0.5 + i * 0.35);
      });
      const verdicts = [...root.querySelectorAll('[data-verdict]')];
      const loss = verdicts.find((v) => v.classList.contains('is-loss'));
      verdicts.filter((v) => v !== loss).forEach((v) => tl.from(v, { autoAlpha: 0, duration: ms('base') }, 1.3));
      // a broken rule drops into place like the seam: the same spring, the same direction, once
      if (loss) tl.from(loss, { autoAlpha: 0, y: -14, duration: 1.1, ease: springEase('seam', 1.1) }, 1.75);
    }, { start: 'top 70%' });
    // later picks redraw instantly; the entrance belongs to the first view only
    setTimeout(() => { entered = true; }, 0);
  });
}
