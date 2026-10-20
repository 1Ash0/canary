# Style guide — Canary site (D4, step 1)

Status: **awaiting owner OK before any mockup is built** · 2026-10-20.
This takes the **grammar** of each reference (layout logic, type behaviour, spacing, texture, ordering, how things enter and exit), never its content, logos or characters. Values come only from `themes/canary/tokens.css`.

## References
| Reference | How I read it | Take | Don't take |
|---|---|---|---|
| **gsap.com** (home, `/scroll`) | Firecrawl branding + page-structure read, 2026-10-20 | Restraint on a warm dark ground; cream type; very short headlines followed by a working demo; sparse copy; generous vertical whitespace; square primary button; one accent used rarely | Its green, its 3D/cartoon showcase assets, its proprietary font, "animate anything" energy |
| **Bartosz Ciechanowski's essays** (`/mechanical-watch/`) | page read + branding, 2026-10-20 | **The figure is the explanation**: no hero image, the page opens straight into the subject; controls sit directly under or beside the figure they drive; figures span the text column or slightly wider; labels on the figure itself; almost no decoration | The light grey ground, blue links, 3D renders, essay length |
| **Tufte** (small multiples, sparklines, data-ink) | established principles, not fetched | Labels sit on the data, not in legends; hairlines instead of boxes; small multiples for comparison (the survival grid); every mark carries information | Serif book typography, print layout, wide margins as a style |
| **Lab instrument front panels** (oscilloscopes, field recorders) | established conventions, not fetched | A readout strip with a **small label over a large value**; units on every number; a scale on every axis; hard-stop motion; a physical, exact, quiet feel | Skeuomorphic knobs, brushed metal, product branding |
| *Anti-reference:* Skillry Opus 5.5 gallery | D1 read | What to avoid: glow, particles, kinetic type, launch-film cuts, 3D product spins | Everything |

## Grammar

### 1. Ordering: the instrument leads, words follow
- The strata player is the hero visual from the first frame, as in Ciechanowski, where the figure *is* the page. No illustration or background media.
- Each section follows GSAP's pattern: **short headline (≤ 7 words) → one or two sentences → the working figure**. No section is text-only except `/about` prose and the "what this is" block.
- The page is a sequence of *states of one run*: filling → compaction → consequence → aggregate. One continuous story, like the video.

### 2. Layout logic
- 12-column grid, 1120 px max. The asymmetric hero has the claim in columns 1–5 and the player in columns 6–12. Below 768 px it stacks: claim, action, player.
- Figures use the full content width (Ciechanowski: figure ≥ text column). Prose stays at 68ch.
- **Controls sit under the figure they drive** (scrubber, step readout, pause/replay), never in a toolbar elsewhere.
- **No cards.** Content blocks are separated by hairlines (`--hairline`) and space. Where several items compare, use a table or a small-multiples grid (Tufte), not a row of identical boxes.

### 3. Type behaviour
- **Display headlines** in Instrument Sans 500, tight tracking (`-0.025em`), at most 2 lines, `text-wrap: balance`. Big but not shouting: the claim is a sentence, not a slogan.
- **Instrument readouts** (from panels): mono `label` (12 px, ink2) above a mono value (15–20 px, ink, tabular). Units are always shown: `26,530 / 73,000 tokens`, `step 31`.
- **On-figure labels** (Tufte): mono, placed at the mark, joined by a 1 px leader line. A legend only where on-mark labels are impossible.
- **Voice:** plain and specific; numbers in mono; lowercase mono labels (`compaction @ step 31`), never tracked-out uppercase.
  - Banned words: revolutionary, unlock, supercharge, seamless, effortless, next-gen, AI-powered, magic.

### 4. Spacing and texture
- Section gap `--space-section` (160 px desktop, scaling down on mobile), internal gaps ≤ `--space-3xl`. Whitespace is the luxury signal (gsap.com).
- **Texture comes only from data:** the strata ramp, hairlines, notch ticks on the seam and axes. No noise, grain, gradients or glow.
- Colour discipline: cream and ink2 for almost everything; teal only on markers, links-in-figures and the primary focus state; vermilion only for `gone` and `behaviour changed`.

### 5. How things enter and exit
Mirrors SITE_RULES §4, in instrument terms.
- **Things arrive like measurements:** a step snaps in on a spring and settles (slight overshoot), and the readout value updates at the same instant.
- **The seam is a mechanical event:** a hold, one heavy drop with a hard stop, then a hold. Nothing else moves during it.
- **Exit is meaningful or absent:** only `gone` markers leave the frame (they fall). Nothing else fades out for effect.
- **Copy enters after its state and leaves before the next one.** Annotations never overlap during swaps.
- **Scrolling** scrubs the same scene (pinned section) rather than revealing unrelated decorations.

## Landing page composition (`/`), for the D4 mockup and D4b
1. **Header:** wordmark `canary` (sans 600, small), three text links (Recorder, About, GitHub), hairline under. No logo mark.
2. **Hero** (first view, 1280×720):
   - Left: the claim, one supporting sentence, the primary action.
   - Right: the strata player with a readout strip on top (step · tokens · data `synthetic fixture`) and the scrubber + pause/replay underneath.
3. **What compaction does:** a pinned, scroll-scrubbed close-up around the seam, with one annotation per state.
4. **The consequence:** two columns, `with fact` / `after compaction`; the tool calls in mono; `behaviour changed` in vermilion.
5. **Survival grid:** policy × canary type as small multiples; each cell shows a rate, an interval whisker and n.
6. **What this is / what it isn't / prior art:** two-column definition list on hairlines, plus a numbered prior-art list with mono citations.
7. **Footer:** project name and the `ctxcheck` toolkit line, licence, repo link, hairline above.

**The D4 static mockup covers items 1, 2 and 6** (hero + one content section), at 1440, 768 and 390 px, from the fixture.

## Draft copy (to approve with the mockup)
- **Claim:** "See what your agent forgets when its context is compacted."
- **Supporting:** "Canary plants facts in an agent run, compacts the context, and records which facts survive, change or disappear."
- **Primary action:** "Open the recorder"
- **Alternative claim:** "Compaction keeps the window small. Canary shows what it threw away."
