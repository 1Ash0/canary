# D4 — Static mockup: choices and checks

Status: **awaiting owner approval of the look** · 2026-10-20. No motion yet; that's D4b.

## Files
| View | File |
|---|---|
| First view at 1280×720 (the hero rule) | `d4/png/first-view-1280x720.png` |
| Full page at 1440 / 768 / 390 | `d4/png/mockup-1440.png`, `mockup-768.png`, `mockup-390.png` |
| Phone hero, closer | `d4/png/hero-390.png` |
| Source | `d4/mockup.{html,css,js}`, `scene/strata.{js,css}` (the shared scene module, ADR-016) |

## Choices
- **Hero layout:**
  - The title spans full width on one line ("What compaction forgets."); below it, lede and action on the left (4 columns) and the instrument on the right (8 columns).
  - **Changed from the style guide's 5/7 split:** measured, the claim could not fit 2 lines in 5 columns at display size (it wrapped to 5 lines).
  - The longer sentence moved into the lede, which now carries the full claim, including "whether the agent acts differently afterwards".
- **Title copy:** "What compaction forgets." reads as an essay title, in Ciechanowski's grammar. The draft "See what your agent forgets…" is retired because it cannot meet the 2-line rule. Say if you want a different title; the constraint is about 24 characters for 2 lines on a phone.
- **The instrument:**
  - A readout strip (step · tokens · data) with small labels over large values, from the instrument-panel reference.
  - Hairline axes, a limit rule, and the seam with notch ticks.
  - Labels sit on the data with elbowed leaders that never overlap (Tufte).
  - On phones the figure keeps short id labels and lists the fates underneath.
- **The accent stays rare:** teal only on canary markers and their leaders; the scrubber is a hairline with a square ink thumb, and the button is cream on ink (gsap.com's square primary).
- **No cards:** the content section is a definition list on hairlines, with prior art as mono arXiv citations taken from `docs/PRIOR_ART.md`. ConstraintRot's headline percentage is left out because PRIOR_ART flags it as not yet confirmed from the PDF.
- **Honesty:** `synthetic fixture` appears in the readout and is explained in "Where the data comes from". Every number in the figure comes from `d2/strata_sample.json`.

## Checks (scripted)
- `node scripts/check-hero.mjs` passes:
  - headline 1 line at 1440, 1280 and 768, and 2 lines at 390
  - at 1280×720, claim, action and the whole player end at 710 px (inside 720)
  - no horizontal overflow at any width
- `node scripts/shoot.mjs … --serve` reports no page or console errors at any width.
- **Raw values grep:** none in scene or mockup code except three documented exceptions:
  - media-query breakpoints (CSS variables don't work in media queries; they mirror `layout.breakpoints`)
  - the `theme-color` meta (templated from tokens at D8)
  - SVG geometry numbers, which are drawing coordinates, not styling
- **Token change made here:** the display minimum moved from 44 to 42 px, so the title fits 2 lines on a 390 phone with a 16 px gutter.

## Critique rounds
- **Round 1:**
  - headline 5 lines → full-width one-line title
  - fate labels overlapping → collision-avoiding callouts
  - step numbers colliding at the seam → hidden near the seam
  - teal scrubber dominating → hairline track with an ink thumb
- **Round 2:**
  - player 22 px below the fold at 1280×720 → tighter top padding and figure height
  - title 3 lines on phone → 16 px phone gutter and the 42 px minimum
  - the hidden data table overflowing at 390 → wrapped
- **Round 3:**
  - kept and changed markers touching → spacing derived from marker size
  - phone readouts wrapping mid-number → nowrap at data size
  - seam label over the step-31 bar on phone → placed under the seam
  - footer phrase split by flex → wrapped
- **Genericness test:** with the name removed, is this any AI-made site? It has no gradient, glow, cards, pills or stock imagery. The hero is a working data instrument with provenance on screen. **Watch at D4b:** this layout depends on the motion being instrument-like (springs, the seam event), not decorative.

## Not in this mockup (by design)
- Motion (D4b).
- The consequence, compaction close-up and survival-grid sections (D8).
- Real routes, and the vendored-guidelines audit (D8).
