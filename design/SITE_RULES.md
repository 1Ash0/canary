# SITE_RULES — Canary site

Status: **approved (owner, D3 gate, 2026-10-20); amended by ADR-022 (2026-10-21)**. Applies to everything under `web/`. Values come from `design/themes/canary/tokens.css` only; no raw hex or px in site code.

The goal is a site that feels **alive and premium, like the best GSAP showcase work, without looking AI-made**. The difference is choreography: every motion carries data or meaning, one thing moves at a time, and nothing loops for decoration.

---

## 1. Banned
- Gradient hero with a generic tagline.
- Stock dashboard cards with numbers and no provenance.
- A paper-style PDF rendered as a page.
- Large logos.
- Animated everything. One moving picture per viewport (see §4.1).
- Cards inside cards inside cards; giant rounded wrapper sections.
- Decorative pills and badges, eyebrow labels above headings, fake system labels, invented status jargon.
- Default purple/blue AI gradients, glassmorphism, glowing edges, glow of any kind.
- Identical card rows repeated section after section.
- Hero headlines of 3 or more lines at any width (stricter than "4 or more"; borrowed from Taste Skill: two lines max).
- Cursor followers or glows, particle fields, 3D tilt, dither or noise backgrounds, smooth-scroll hijacking.
- Decorative ASCII art and character-scramble text effects (ASCII is allowed only as a data view, §4.7).
- `transition: all`, `outline: none` without a replacement, animated GIFs.

**Borrowed constraints** (Taste Skill, MIT, credited):
- one ground, one ink, one accent
- equal outer margins
- the gap between sections is clearly larger than any gap inside a section
- screenshot gate at 1440, 768 and 390 px

## 2. Hero (first view)
At 1280×720 the first view shows **one claim, one primary action, and the strata player running**. It must be readable without scrolling and not crowded.
- **Claim:** at most 2 lines, `type-display`.
- **Primary action:** "Open the recorder" (placeholder route).
- **Secondary:** the player's own pause/replay control. This is not a second CTA.
- **Honesty:** the `synthetic fixture` label is visible in the player readout wherever fixture data is shown.
- **Ruled out:** a background video, an illustration, a mock UI screenshot. The hero visual *is* the instrument.

## 3. Layout and type
- 12-column grid, `--max-content` 1120 px, `--gutter` 24 px; prose at `--measure`.
- **Section rhythm:** `--space-section` between sections, ≤ `--space-3xl` inside a section.
- **Type roles:** `display / h1 / h2 / body / small` for prose (Instrument Sans), and `label / data` for anything numeric or an identifier (JetBrains Mono, `tabular-nums`).
- **Sentence case** everywhere. This is a conscious skip of the vendored guidelines' Title Case rule.
- `text-wrap: balance` on headings.

## 4. Motion system
### 4.1 Principles
1. **Motion carries data or meaning.** If removing an animation loses no information and no cause-and-effect, remove it.
2. **One moving picture per viewport.** At any moment, at most one region animates. Everything else is still.
3. **Weight, not slides.** Arrivals use closed-form springs (`motion.spring.*` in tokens); CSS transitions use `--ease-out`. No linear easing except scroll scrub.
4. **Choreograph cause → effect.**
   - The limit fills, then the seam drops, then the fates resolve.
   - Text that explains a state enters *after* the state changes and leaves *before* the next one (from the video method doc).
5. **The seam is the signature.** It's the single heaviest motion on any page (`spring.seam`, hard stop) and happens once per playthrough.
6. **Animate `transform` and `opacity` only.** SVG transforms go on a `<g>` with `transform-box: fill-box`.

### 4.2 Tokens
- **Durations:** `--duration-micro` 160 · `base` 320 · `slow` 700 · `reveal` 900 ms.
- **Easings:** `--ease-out`, `--ease-in-out`.
- **Staggers:** `--stagger-lines` 80, `--stagger-cells` 60 ms.
- **Springs** (JS, from `base.tokens.json`):
  - `step` k210/d24: slight overshoot
  - `seam` k90/d19: critically damped
  - `ui` k300/d30
  - `fall` k60/d14

### 4.3 Landing page choreography (`/`)
| Section | Trigger | What moves | Length | Reduced motion |
|---|---|---|---|---|
| **Hero: claim** | load | lines reveal upward from a clip mask (line-level SplitText), staggered `--stagger-lines` | `reveal` | static |
| **Hero: strata player** | load, after the claim's first line | plays the sample run once: steps arrive on `spring.step`, cadence accelerates as the window fills toward the limit rule, the seam drops on `spring.seam`, then the fates resolve (kept holds, changed dashes in with its text diff, gone falls out on `spring.fall`); ends on the final state, then "Open the recorder" | ~14 s, with **pause/replay** control (required for autoplay over 5 s) | final state shown, no autoplay; ← / → still step |
| **What compaction does** | scroll: ScrollTrigger pin, `scrub: 0.5` | scroll scrubs the *same scene* from about 3 steps before the seam to 3 steps after; one annotation per state, swapped by rule 4.1.4 | pinned for ~1.5 viewports | unpinned; static frames before / at / after the seam |
| **The consequence** | enters viewport | two columns (`with fact` / `after compaction`); the tool-call lines reveal; `behaviour changed` lands in vermilion on `spring.seam` once | `slow` | static |
| **Survival grid** | enters viewport | cells fill one by one (`--stagger-cells`); each whisker draws via `scaleX` from its centre; the number then appears | ~1.5 s total | static |
| **What this is / isn't / prior art** | enters viewport | none beyond a single 12 px rise + fade per block | `base` | static |
| **Footer** | — | none | — | — |

`/about` uses the same prose motion only (the last two rows).

### 4.4 Interaction states (all pages)
- **Buttons:** hover raises contrast; press scales to 0.97 on `spring.ui`; focus ring is 2 px `--accent` with 2 px offset (`:focus-visible`).
- **Links:** an underline draws in with `scaleX` over `--duration-micro`; `--link` colour.
- **Scrubber:** the thumb springs to the step (`spring.ui`); ← / → step; `Home`/`End` go to first/last; the step is written to the URL `?step=` with `replaceState`.
- **Shortcuts:** `?` opens shortcut help; `c` jumps to the compaction event.
- **Interruptible:** any user input stops autoplay immediately and hands control to the user.

### 4.5 Reduced motion
Every animation is set up inside `gsap.matchMedia()` with a `(prefers-reduced-motion: reduce)` branch that shows the final state. No autoplay. Interactions still work instantly. This is verified by the two-sided Playwright check pattern from `design/trial/` (`reduce` → final state, 0 triggers; `no-preference` → animation set up).

### 4.6 Tools
- **GSAP:** core + ScrollTrigger; SplitText at line level, at most one heading per page (D1).
- **Not used:** Lenis, ScrollSmoother, MorphSVG, ScrambleText, React Bits backgrounds, WebGL.
- **The scene module is shared with the video** (ADR-016). The site player drives it from GSAP timelines; the video drives it with `seek(t)`.

### 4.7 ASCII views, brightness and the lab (ADR-022)
- **Window as text.** One monospace row per message: a role tag, then a run of glyphs whose length is the message's tokens and whose glyph is its kind (`░` history, `▒` tool output, `▓` summary, `█` the planted rule). The seam is a `═` rule with a label. Rows are `aria-hidden`; the same information is in a text alternative.
- **Brightness is presence.** In the window: `--ink`. Removed by compaction: `--ink-3`. A lost fact: `--loss` plus the words `gone ↓` or `∅`. No glow, blur or shadow.
- **Transcript replay** shows real trace text only, never invented output, and stays selectable and copyable.
- **The lab** may move while the user drives it (exempt from §4.1.2 during input). It never autoplays. Its in-browser policies are labelled `simulated`; recorded summaries are labelled `recorded`.
- **Reduced motion:** text appears whole, lab updates are instant.

## 5. Interaction and accessibility
- Keyboard-first: every control reachable, visible focus, a skip link, `scroll-margin-top` on anchors.
- The strata view has a text alternative: a table of step and layer token counts underneath (DESIGN.md).
- Vermilion always comes with text or an icon (`gone ↓`). Never colour alone.
- Contrast via `design/scripts/contrast.mjs`: text ≥ 4.5, markers ≥ 3.

## 6. Component sources
21st.dev or similar only for chrome (tabs, tables, dialogs, command palette, tooltip, slider), restyled to tokens. The strata player, seam, fate markers and survival grid are hand-built. Every borrowed component goes in the register in `docs/DESIGN.md` (source, licence, where used, how modified).

## 7. Performance
- **Budget for `/`:** ≤ 60 kB gzip initial JS, set from the measured trial baseline of 44,350 B (GSAP core + ScrollTrigger).
- **Rendering:** 60 fps on pinned and scrubbed sections; no layout reads inside animation frames.
- **Fonts:** self-hosted woff2 with `font-display: swap`, and preload of the sans.

## 8. QA gates (D8)
- Playwright screenshots at 390, 768 and 1440 px, plus 1280×720 for the first-view rule.
- Motion QA: a frame strip of the hero playthrough (12 frames around the seam), checked for overlaps, sliding and dead beats.
- Vendored Web Interface Guidelines pass over all code; conscious skips go in `design/README.md`.
- Grep: no raw hex or px outside token files. Keyboard-only walkthrough. Reduced-motion check.
