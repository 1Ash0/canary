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
| D5 Renderer | not started | |
| D6 Video keyframes | not started | |
| D7 Full video | not started | |
| D8 Site build | not started | |

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

## Exact next step
D4b approved 2026-10-20. Design waits for M1 (ROADMAP). When it resumes, D5 is the deterministic renderer: its page calls `scene/timeline.js` `frameAt` through `window.seek(t)`; exit test: SHA-256 of frame t=11.37 identical across random-order renders.

Dev server: `canary-design` in `.claude/launch.json` (Vite, root `design/`). If an edit doesn't show up, restart it: the watcher missed one change on 2026-10-20.
