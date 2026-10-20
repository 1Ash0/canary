// "What the agent did next": the two summaries side by side, then the tool call each agent emitted.
// Built only from experiments/exp001_pair.json. Choreography (SITE_RULES §4.3): the columns rise,
// the tool calls type in line by line, and "behaviour changed" lands once on the seam spring.
import { onEnterOnce, springEase, ms } from './motion-kit.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

// Summaries arrive with markdown emphasis; the page shows plain text and marks the channel name.
function quote(text, channel) {
  const plain = esc(text.replace(/\*\*/g, '')).replace(/[‐-―−]/g, '-');
  return channel && plain.includes(channel) ? plain.split(channel).join(`<mark>${esc(channel)}</mark>`) : plain;
}

function column(side, rightRule) {
  const lost = side.fate === 'gone';
  const ch = side.call.channel;
  const broke = side.grade === 'violated';
  return `
    <article class="cons-col${lost ? ' is-lost' : ''}" data-cons-col>
      <header class="cons-head">
        <span class="panel-host">${esc(side.host)}</span>
        <span class="mono">${esc(side.model)}</span>
      </header>
      <p class="cons-label">Its summary of the earlier turns</p>
      <blockquote class="cons-quote">${quote(side.summary, rightRule)}</blockquote>
      <p class="cons-check">${lost ? 'Names no channel.' : `Names <span class="mono">${esc(rightRule)}</span>.`}</p>
      <p class="cons-label">The tool call it emitted next</p>
      <pre class="cons-call"><code><span class="cons-line" data-line>post_status(</span><span class="cons-line" data-line>  channel=<span class="${broke ? 'is-loss' : 'is-ok'}">"${esc(ch)}"</span>,</span><span class="cons-line" data-line>  text="${esc(side.call.text)}"</span><span class="cons-line" data-line>)</span></code></pre>
      <p class="cons-verdict ${broke ? 'is-loss' : ''}" data-verdict>${broke ? `behaviour changed ↓ <span class="dim">the rule said ${esc(rightRule)}</span>` : 'rule followed'}</p>
    </article>`;
}

export function mountConsequence(root, pair) {
  const rule = pair.sides[0].channel;
  root.innerHTML = `
    <p class="exp-intro">Then each agent was asked to post this week's status. The request lists four channels, the right one among them, and says nothing about the rule.</p>
    <div class="cons-grid">${pair.sides.map((s) => column(s, rule)).join('')}</div>
    <p class="caveat"><span class="tag">${esc(pair.label)}</span> EXP-001, seed ${pair.seed}, treatment condition, prompt v1. Both summaries are complete (neither was cut off). Source: <span class="mono">${esc(pair.source)}</span> and the traces it names.</p>`;

  const cols = root.querySelectorAll('[data-cons-col]');
  onEnterOnce(root, (tl) => {
    tl.from(cols, { y: 16, autoAlpha: 0, duration: ms('slow'), ease: 'power2.out', stagger: 0.12 });
    cols.forEach((col, i) => {
      tl.from(col.querySelectorAll('[data-line]'), {
        autoAlpha: 0, x: -6, duration: ms('micro'), ease: 'power1.out', stagger: 0.09,
      }, 0.5 + i * 0.35);
    });
    const verdicts = root.querySelectorAll('[data-verdict]');
    tl.from(verdicts[0], { autoAlpha: 0, duration: ms('base') }, 1.3);
    // it drops into place like the seam: the same spring, the same direction, once
    tl.from(verdicts[1], { autoAlpha: 0, y: -14, duration: 1.1, ease: springEase('seam', 1.1) }, 1.75);
  }, { start: 'top 70%' });
}
