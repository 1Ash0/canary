# Design subsystem — progress

Handoff: `docs/design/HANDOFF.md`.

## Gates
| Gate | Status | Date |
|---|---|---|
| D0 Orientation | **approved** | 2026-10-20 |
| D1 Resource evaluation | **approved** | 2026-10-20 |
| D2 Tokens and type | **approved** | 2026-10-20 |
| D3 Rules files | **approved**; CLAUDE.md pointer applied | 2026-10-20 |
| D4 Site mockup (static look) | **approved** (title "What compaction forgets.") | 2026-10-20 |
| **D4b Hero motion prototype** (added at owner's request, 2026-10-20) | **approved** | 2026-10-20 |
| D5 Renderer | not started; **unblocked** (needs no data) | |
| D6 Video keyframes | not started; **unblocked** (recorded runs exist) | |
| D7 Full video | not started; **unblocked** after D5 and D6 | |
| D8 Site build | **core built 2026-10-21** (landing on recorded data, recorder on recorded runs); polish and deploy left | 2026-10-21 |

**Why D4b exists.** The owner asked that the landing page and the rest of the site be dynamic and moving, not just look right in stills. The handoff defers all site motion to D8, so the owner would only see motion at the very end. D4b builds the hero alone (claim reveal + strata player playthrough + seam + fates) after the static look is approved, renders it as a frame strip and a short screen recording, and gets the motion feel approved before D5–D8 build on it. Motion rules: `SITE_RULES.md` §4.

## Decisions made
**D0** (owner, 2026-10-20):
1. Identity: "premium like GSAP"; all D1 resources used as references.
2. Pending dither edit discarded.
3. Public name Canary; package/CLI `ctxcheck` (ADR-013, Accepted).
4. Framework delegated → ADR-015.
5. References delegated to Claude.
6. Handoff renamed to `docs/design/HANDOFF.md`.

**D1** (approved 2026-10-20; ADR-015 Accepted): Vite + vanilla TS; GSAP core + ScrollTrigger (limited); Web Interface Guidelines vendored; `playwright` for QA and the renderer. Rejected: Lenis, React Bits, ThreeUI, Remotion/HyperFrames, playwright-cli. Details: `RESOURCE_DECISIONS.md`.

**D2** (approved 2026-10-20; ADR-014 Accepted):
- Candidate B (warm near-black `#0E0D0B`, cream ink, teal `#45AE9F`, vermilion `#EE6240`).
- Instrument Sans + JetBrains Mono, self-hosted (`identity/fonts/`; loads with the network blocked, `scripts/check-fonts.mjs`).
- Motion tokens added to the base identity.
- DESIGN.md identity and epistemic tags updated.
- Report: `d2/D2_REPORT.md`.

## Tooling state
- `design/package.json`: vite 8.3.4, typescript 7.0.2, playwright 1.64.1, @fontsource-variable/* 5.3.0 (dev); gsap 3.15.0 (dependency).
- Playwright headless shell 1248 installed.
- Trial build: 44,350 B gzip; reduced-motion checks pass both ways (`trial/RESULT.json`).
- Scripts: `build-tokens`, `contrast`, `check-fonts`, `d2-pages`, `shoot`, `trial-measure`.

## Open items
- **Copy debt, fix when M5 is reached (owner, 2026-10-20):** the sentence "It makes no new claims: the first experiment replicates published work..." on `/` and `/about/` becomes untrue once EXP-002/003 produce extension results. Replace with: "The first experiment replicates published work on our own harness. Later experiments extend it with other policies and fact types, and every result is reported with its interval, nulls included." Also sharpen "Not a framework for building agents" to add "The harness exists only to run test scenarios."
- ADR-016 (video = headless render of the scene) and ADR-017 (theme = ground + ramp + device): still Proposed.
- D0 schema additions (step index, limit_tokens, tools_tokens_est, canary_fate, pair_id) await the owner (Teach-First lane).
- Committed as of 2026-10-20 (see `git log`); nothing is pushed (no remote).

## Site build status (2026-10-20, after the data layer)
Built in `web/` (Vite multi-page, imports the scene, tokens and fonts from `design/`): `/` (hero player + mock experiment + what this is), `/run/` (recorder: scrubber, ← → Home End c, `?run=&step=` permalinks, copy link), `/about/`. The old dark `web/index.html` is gone.
Checks (all scripted, against dev and the production build): `scripts/check-site.mjs` (12 page x width combinations: no console errors, no sideways scroll, headline <= 2 lines, 1280x720 first-view rule), `scripts/check-recorder.mjs` (11 recorder behaviours, the M1 exit test). Initial JS on `/` is about 35.5 kB gzip (budget 60 kB).
**Deferred, on purpose:**
- The pinned, scroll-scrubbed "what compaction does" section (D8 polish).
- The "consequence" section: it needs a probe in the trace (the synthetic run has none), and showing it now would mean inventing data. It arrives with M2.
- The `?` shortcut overlay (the shortcuts are listed in text on the recorder).
- A GitHub link: the repo has no remote yet.
- Deploy, per the owner ("not yet").
- The full guidelines audit (D8): so far only a scripted scan for the guideline anti-patterns, none found.

## Sequencing change (owner, 2026-10-20)
The D gates **pause after D4b**. The owner's reasoning: the site and the video should show a mostly implemented project, not a fixture. Order from here:
1. M1 completion: schema, token ledger, real-tokenized fixture, export pipeline. The M1 recorder view and the landing page are built on this design system (they absorb most of D8).
2. M2–M4: a real recorded run, then real policies and the first measurement.
3. Then D5–D7: the video renders a recorded run and real results through the same `scene/timeline.js`.

D5 (the renderer) doesn't depend on data and can slot in anywhere if useful. See the ROADMAP status check.

## Status refresh (2026-10-21, after the live EXP-001 runs)
The reason for the pause is gone: M1 to M4 are built and EXP-001 has recorded data. What is left on the design side, in the order I would do it:
1. **D8 core (most value):** replace the mock experiment on `/` with the real EXP-001 results, labelled `recorded` (per-model cells with intervals, the 27-seed table, Gemini shown as excluded and why). Export recorded runs to the recorder (a kept and a dropped episode for the same seed), so `/run/` shows a real run, with the consequence section now that a probe exists. The export judges survival at the probe (fixed 2026-10-21).
2. **D8 polish:** the pinned scroll-scrubbed "what compaction does" section, the `?` shortcut overlay, a GitHub link once a remote exists, the full guidelines audit, then the deploy decision (owner: "not yet").
3. **D5 renderer:** deterministic `window.seek(t)` page over `scene/timeline.js`; exit test is the SHA-256 of frame t=11.37 identical across random-order renders.
4. **D6 keyframes, D7 video:** render a recorded run (the same seed kept versus dropped is the natural story), after D5.
5. **Proposed ADRs 016 and 017** (video as headless scene render; theme = ground + ramp + device) still need the owner's acceptance. D0 schema additions: step index, `limit_tokens`, `tools_tokens_est` and derived fate are done in schema 0.3; `pair_id` is still deferred.
**Copy debt:** the home page sentence is rewritten (2026-10-21) to say the first experiment tried to reproduce published work and came out split; the sharpened "not a framework" wording is in. Re-check it when EXP-002 or EXP-003 produce results.

## D8 core, built 2026-10-21
- **Landing (`/`)**, all from exported recorded data (`experiments/exp001.json`, `exp001_pair.json`, `runs/exp001-s19-*.json`):
  1. Hero: the claim rises line by line (SplitText masks, the one split heading allowed); the strata player plays a **recorded** run (NVIDIA gpt-oss-20b, seed 19: the rule is planted, the window passes the limit, the seam drops, the rule falls out as `gone ↓`), starting as the claim's first line lands; lede and action follow on the `ui` spring.
  2. "Same history. Two summaries.": the pinned, scroll-scrubbed section of SITE_RULES 4.3, reworked to scrub **two** recorded runs of the same seed in sync (Mistral kept the rule, NVIDIA dropped it). One moving picture; notes enter after the state they describe (driven by scene state, not scroll fraction). Pinned only at >= 1024 x 680 with motion allowed; otherwise static final state with every note visible.
  3. "What the agent did next": both summaries (channel marked where named), the tool call each agent emitted typing in line by line, and `behaviour changed ↓` dropping in once on the seam spring.
  4. "What the experiment found": per-model control and treatment rows with Wilson whiskers drawing out from their centre; the audit statement ("42 of 42 summaries read by hand") and every caveat (no cross-model replication; NVIDIA truncation; excluded models) come from the exported JSON.
  5. "Without a model": a compact deterministic survival grid; cells fill one by one.
- **Recorder (`/run/`)**: opens the recorded NVIDIA run by default, lists all runs with their epistemic tags, and shows the probe outcome after the compaction step.
- **Scene fixes found on the way**: the strata layout scales to the window when a recorded run passes the limit before its single compaction; the timeline now lasts until the fates settle when compaction is at the last step; a kept fact reads "named in the summary" (the owner's audit showed most are reworded, not verbatim).
- **QA**: `scripts/check-landing.mjs` (reduced-motion final states at 1440/768/390, pin and scrub with notes advancing in order, every entry animation settling fully visible); `check-site.mjs` now includes the recorded run page; `check-hero.mjs` and `check-recorder.mjs` pass. Initial JS on `/` about 59 kB gzip of the 60 kB budget, so there is little headroom.
- **Left for D8 polish**: the `?` shortcut overlay, a GitHub link once a remote exists, the full guidelines audit, OG images, then deploy (owner).

## Site rework, 2026-10-21 (ADR-022: the site becomes an instrument)
- **The Lab** (`#lab`, "You are the harness."): pick a policy, drag the budget and the rule's position, and the window recompacts on every input as an ASCII view (bright = in the window, dim = gone). Deterministic policies run a JS port of the Python policies, pinned by 540 parity cases in `design/tests/lab-parity.test.mjs`; the summary policy shows recorded summaries (EXP-001b for gpt-oss-20b). At EXP-002's settings it also lists what each recorded model did with that exact window, linked to the episode.
- **Results** are one tab per experiment, rendered from one block shape: EXP-001 (two models), EXP-001b (the clean rerun), EXP-002 (four policies, both canaries). One mark per seed; every treatment mark opens its episode in the recorder (EXP-001b and EXP-002 runs exported as compact JSON).
- **Recorder**: grouped run picker, bars or text view (`t`), transcript up to the step (stand-ins sit in their own turn), `?` help dialog.
- **/about**: four beats drawn as text from a recorded run; copyable commands; limits now include the rule's early position.
- **Copy pass**: turns counted from 1 on every page; the hero no longer equates compaction with summarising.
- **Performance**: sections mount as they approach (half a screen ahead); first-view JS 61.7 kB gzip at 1280x800, where the Lab is on screen. **1.7 kB over the 60 kB budget**; the rest is GSAP core plus ScrollTrigger and SplitText (47 kB). Trimming SplitText from the first view is the obvious next cut.
- **QA**: `check-landing` (now with a two-sided lazy-loading check), `check-site` (no sideways scroll at any width after the /about fix), `check-hero`, `check-recorder`, design tests 16 of 16. All pass.

## Exact next step
D4b approved 2026-10-20. Design is unblocked (2026-10-21): next is D8 core above (real results on `/`, recorded run in `/run/`). D5 is the deterministic renderer: its page calls `scene/timeline.js` `frameAt` through `window.seek(t)`; exit test: SHA-256 of frame t=11.37 identical across random-order renders.

Dev server: `canary-design` in `.claude/launch.json` (Vite, root `design/`). If an edit doesn't show up, restart it: the watcher missed one change on 2026-10-20.

## Landing round-out, 2026-10-21 (after a design critique)
Critique findings and what changed:
- **One example only** → a shared episode (canary, seed, two recorded choices) drives the hero, the comparison and the consequence, kept in the URL.
- **Four names for one policy** (Lab, grid, survival page, results) → one vocabulary from `episode.js`: drop oldest, keep head and tail, mask tool output, model summary.
- **Dead ends between sections** → the grid's cells load that policy and budget into the Lab; the Lab's "Compare this history" loads its seed and policy into the comparison; results marks load into the comparison; the consequence has its own seed stepper.
- **One canary only** → the comparison switches between the channel rule and the account code; presets are offered only where both sides were recorded.
- **The test's request was invisible** → the consequence quotes it.
- **Locked sliders in summary mode, unexplained** → the help line says why.
- **Marks under 24 px** → hit areas grow to 24 px without changing the drawing.
- Lab histories extended from 10 to all 27 seeds, so every Lab seed has recorded counterparts.
