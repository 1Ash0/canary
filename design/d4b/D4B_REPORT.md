# D4b — Hero motion prototype

Status: **awaiting owner approval of the motion** · 2026-10-20.
Run it: start `canary-design` (`.claude/launch.json`), then open `http://localhost:5173/d4b/`.

## Watch
| What | File |
|---|---|
| Real-time playthrough at 1280×720, as a visitor sees it (GSAP playback, 14.5 s recording) | `d4b/review/playthrough.mp4` |
| Same at phone width 390×844 | `d4b/review-390/playthrough.mp4` |
| Frames every 0.5 s (from the pure timeline) | `d4b/review/contact.png` |
| 12 frames across the seam and the collapse | `d4b/review/seam-strip.png` |
| Phone frames around the seam | `d4b/review-390/phone-seam.png` |

## The choreography (12.3 s, plays once)
1. **0–0.9 s:** the title rises out of a line mask (GSAP SplitText, line level). The instrument waits empty at `0 / 40`. Only one thing moves at a time.
2. **~1–7 s, the window fills:** each step's bar snaps in on `spring.step` (slight overshoot) and the readout updates on arrival. The cadence speeds up, from 0.34 s per step down to 0.11 s.
   - Each canary pops in when planted (steps 3, 9, 14); its leader and label follow 0.18 s later.
3. **Approaching the limit:** past 85% full, the limit rule warms from grey to full ink. The tension comes from the data, not decoration.
4. **~7.7 s, the seam:** a 0.8 s hold at the limit, then the compaction line sweeps across on `spring.seam` (critically damped, hard stop). The notch ticks appear as the line passes them, then `compaction @ step 31`.
5. **The collapse:** step 32 arrives at step 31's full width and shrinks onto its own on the heavy spring. The window visibly compacts.
6. **Fates, staggered 0.45 s:** each marker travels from where it was planted, through the seam, into the summary band. x and y use different springs, so the path curves rather than sliding.
   - **Kept** lands solid; **changed** lands as a dashed ring with `→ deploy target: EU region`.
   - **Gone** turns vermilion and falls out past the axis on `spring.fall`, along a dotted drop line, with the label `gone ↓`.
7. **Tail:** steps 33–40 arrive quickly, then the playback settles on the final state and the button becomes **Replay**.

## Architecture (why the site and video can't drift)
- **`scene/strata.js`** renders the final state as SVG with animatable groups. With no JS, or with reduced motion, the page is already complete.
- **`scene/timeline.js`** has `frameAt(schedule, t)`, a pure function of time built on closed-form springs (`scene/motion.js`, with parameters from `identity/base.tokens.json`); `apply()` writes only `transform` and `opacity`.
- **The site** (`d4b/main.js`): GSAP plays a playhead through `frameAt`. **The video (D5–D7)** will call the same `frameAt` through `seek(t)`. One function serves both.

## Controls
- **Play/pause/resume/replay** button; any scrubber input interrupts playback.
- **Scrubber:** native keyboard support (← →, Home/End), and the step is written to the URL as `?step=`.
- **Shortcut:** `c` jumps to the compaction.
- **Deep links:** `?step=12` opens as a still at step 12 with no autoplay.
- **Reduced motion:** final state, no autoplay, controls still work.
- **Phone:** the fate list under the figure follows the same frame. Facts appear when planted, fates when resolved, and vermilion only once loss has happened.

## Checks
- `npm test` passes 9/9:
  - all three spring regimes start at 0 and settle at 1, with no jump at critical damping; only the underdamped one overshoots; `track` stacks
  - `timeForStep(i)` shows exactly step *i* for all 40 steps
  - frames are pure functions of time
  - the seam is ordered between steps 31 and 32
  - the limit heat rises near the limit and resets after compaction
- `node scripts/check-motion.mjs` passes, two-sided: reduce → final state; motion → autoplays; scrub → interrupts and writes `?step=`; `?step=12` → a still at 12.
- Console is clean in the browser pane.

## Critique rounds (harsh, from contact sheets, strips and the recording)
1. **Round 1:**
   - The deep link and scrubber landed on the wrong step (late steps arrive faster than they settle) → `timeForStep` clamps before the next arrival, with a test covering every step.
   - The button showed both icons → SVG `hidden` handled via the attribute.
2. **Round 2:**
   - The first frame read `1 / 40` with the button on "Replay" → a beat of empty instrument at `0 / 40`, and "Pause" set immediately.
   - On the phone, the fate list was visible from frame 0 (it gave away the ending) → synced to the timeline.
   - The phone seam label sat over the collapsing bar → delayed until the collapse settles.
3. **Round 3:**
   - "C3" was vermilion before its fate resolved → vermilion only on the resolved fate.
   - Vite's file watcher served a stale module (found by comparing the served file with the source) → server restarted and verified.
- **Genericness test:** no glow, particles, kinetic type, parallax or decorative loops. Every moving thing is a measurement arriving or a fact changing state. **The one risk I'd watch:** at about 12 s, a first-time visitor may not wait for the fates. Option: start the playthrough at step ~20 on repeat visits. That's not built; it's your call.

## Not in D4b (by design)
- The scroll-pinned "what compaction does" section, the consequence section, the survival grid (D8).
- The `?` shortcut help overlay (D8).
- Real run data (M2).
- The video renderer (D5).
