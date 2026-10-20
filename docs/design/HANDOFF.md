# Design subsystem handoff: tokens, site, and video pilot (ctxcheck)

## How to use

1. Save this file in the repo as `docs/design/HANDOFF.md`.
2. Open Claude Code in the repo on your strongest model setting.
3. Send this first message: *"Read docs/design/HANDOFF.md, ignore the How to use section, and do D0 only."* (Or paste everything from the `# TASK` line to the end.)
4. At each gate Claude Code shows results and a recommendation. Reply "approved" or tell it what to change.
5. To resume in a new session: *"Read docs/design/HANDOFF.md and design/PROGRESS.md, then continue at the next unapproved gate."*

---

# TASK: build the design subsystem for ctxcheck (tokens, site, video pilot)

## Role and working mode

You are implementing a reusable design subsystem, the ctxcheck site's design layer, and one motion-graphic pilot for **ctxcheck** (working name; Project 1, the Compaction Canary Lab).

The owner (Asmit) works step by step. He wants decisions presented for approval, not busywork handed to him, and honest assessments over reassurance. Keep reports concise and actionable.

**Gates.** The work is split into gates D0 to D8. At each gate, stop, show the results and any decisions, and wait for "approved". Never skip a gate or batch two together.

## Why this exists

- ctxcheck asks: when an agent harness compacts its context, what does the agent stop knowing, and does its behaviour change? Planted "canary" facts either survive compaction or don't.
- The owner publishes technical content on LinkedIn and GitHub, and his sites and videos look generic. Generic comes from three missing things: a fixed identity, a reference to copy grammar from, and a loop where the model looks at its own rendered output. Everything in this handoff exists to supply those three.
- The target audience is engineers and researchers in AI systems. The desired feel is a warm, human-made technical editorial / engineering notebook. It is **not** cinematic dark, glowing, 3D, or "AI landing page".
- The pilot video is an **instrument, not a launch film**: one continuous diagram of a single run's context window as strata, with every pixel drawn from a run file. The same scene component powers the site's "context strata" view, so the video is a headless render of the real thing.

## Decision rights (important)

**You decide, with evidence, and the owner approves at the gate:**
- Theme values (palette, strata ramp, ground tint), including base identity values if they are not already specified in the repo.
- Fonts.
- Which tools, libraries and components to adopt, limit or reject (see D1).
- Layout, composition and motion details.

**You may NOT override these invariants:**
- One accent (deep teal). Vermilion appears only for real loss or failure.
- Fate encoding (below). Colour is never the only channel.
- The `synthetic fixture` honesty label until real runs exist.
- Every number on screen is traceable to a run file.
- The scope fence below.
- Existing repo docs win on identity (`docs/DESIGN.md`) and on the trace schema (`docs/ARCHITECTURE.md`). Flag conflicts. Do not silently resolve them.

**Beware the failure mode this handoff is meant to prevent.** Every resource in D1 can pull the result toward the generic "AI landing page" look (dark, glow, gradients, 3D, animated everything). Evaluate them against the desired feel above. A tool being popular, impressive, or in a showcase is not a reason to use it.

## Scope fence

**In scope:** D0 to D8.

**Out of scope, do not start:**
- ctxcheck core (`src/ctxcheck/`)
- Data-driven product views: `/run/[id]`, `/lab`, `/lab/[exp]`, `/notebook`
- Real model runs, and any claim about results
- A 16:9 video variant
- Music
- Deploying anything
- Posting anything
- The owner's personal portfolio site (the theme system should make it possible later; do not build it)

**Site scope (D4 and D8):** the design layer plus the public front door: global tokens and CSS, app shell (header, footer, navigation), typography, the `/` playground landing page, `/about`, and the embeddable strata player (scrubber, arrow-key stepping, URL deep-link of the step, reduced-motion behaviour). If the existing roadmap makes the owner build the M1 strata view himself, D0 must report that, and D8 shrinks to the design layer and the landing/about pages.

This is the light lane (tooling, CSS, build scripts). You may implement without deep teaching gates, but you must document how everything works.

---

## D0. Orientation (first session only, no code)

Read: `CLAUDE.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`. Then report these seven things:

1. **Base identity values** found: palette hex, fonts and font files, spacing and grid, line weights. The owner's description: warm off-white ground, near-black ink, one deep-teal accent, vermilion only for real loss, a sans plus a mono for labels, a "point of observation" marker. **If exact values are missing, do not stop. Propose a concrete base identity (palette, fonts, spacing scale, line weights) matching that description, mark it Proposed, and decide it at D2.**
2. **The trace schema** as it exists. Which fields give per-step token counts per layer, compaction events, canary plants and fates, and behavioural outcome? Which fields the scene needs are missing?
3. **Repo state:** the web framework and build setup, whether the M1 strata view is started or reserved for the owner, and where `design/` should live. Proposed default: `design/` at the repo root, structured to be liftable into its own repo later.
4. **Tooling present:** node version, ffmpeg, python, Playwright browsers, and which fonts exist as local files.
5. **Conflicts** between this handoff and the existing docs, with a recommendation for each.
6. **References.** Without a reference the model falls back to generic defaults. Ask the owner for 2 or 3 references from **outside the AI-demo genre** (technical films, scientific visualisations, editorial or data-journalism motion and layout, instrument or lab-equipment interfaces), each with a "take / don't take" note: what to take (timing, type behaviour, texture, layout logic, how things enter and exit) and what not to (subject, branding, content). If he has none, propose up to 5 candidates with reasons and let him choose. **Do not start D4 without approved references.**
7. **Site scope check:** how this handoff's site scope fits the roadmap, per the Site scope paragraph above.

Stop and wait for approval.

---

## D1. Resource evaluation (decide what to use)

Read each resource **first-hand** (fetch the pages and files yourself; do not rely on memory or on this handoff's summaries), then produce `design/RESOURCE_DECISIONS.md`.

**Resources**

- Video prompts and method:
  - https://skillry.dev/ai-videos/opus-5-5
  - https://github.com/yihui-dev/awesome-opus5-5-videos (prompts folder; mine for structure, not look)
  - https://docs.google.com/document/d/1N2aEojHhhs98ZokIp56wiGyPBL0v9tG1o7LWWdqOYb8/mobilebasic (render contract, house rules, critique loop, springs)
  - https://skillry.dev/learn/remotion-vs-hyperframes
- Motion and scroll:
  - https://github.com/greensock/GSAP (and gsap.com docs, including ScrollTrigger and matchMedia)
  - https://github.com/darkroomengineering/lenis
- Components:
  - https://github.com/DavidHDev/react-bits (including its Center Stage and Background Studio tools)
  - https://threeui.com/browse (reference gallery only)
- Design rules and workflow:
  - https://www.tasteskill.dev/ and https://github.com/Leonxlnx/taste-skill (including `image-to-code-skill/SKILL.md`, `minimalist-skill`, `soft-skill`, `redesign-skill`, `output-skill`)
  - https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md (the rules behind the web-design-guidelines skill)
  - https://github.com/VoltAgent/awesome-design-md (study 3 to 5 files for grammar, for example Claude, Sanity, Notion, Linear, Vercel)
- QA and recording: https://github.com/microsoft/playwright-cli

**For each resource, record:**
1. What it does, in one line.
2. What it would do for ctxcheck specifically (site, video, or QA), or "nothing".
3. Cost: bundle size or runtime cost, accessibility risk, licence terms (verify the actual licence text, not summaries), maintenance risk.
4. The alternative (including "plain CSS", "closed-form springs", "no library").
5. **Verdict: adopt / limit (state the limit) / reject**, with the deciding reason. Where practical, back it with a measurement (for example a minimal trial build with bundle size and a reduced-motion check), not an opinion.

**Rules for the evaluation**
- Prefer fewer dependencies. Every adopted runtime dependency needs a written case. A "no library" outcome is a good outcome.
- The video renderer is `seek(t)`-based and does not need a motion library. Decide separately whether the site needs one.
- Anything that adds a dark/glow/gradient/3D look by default fails the desired-feel test unless you can show a restrained use.

**The orchestrator's priors (to be challenged with evidence, not followed):**
- GSAP: possibly only if the site needs scroll choreography that CSS scroll-driven animation or plain transitions cannot do. Check licence terms and bundle size.
- Lenis: lean reject. Smooth scroll with nothing choreographed under it is a template tell, and it adds scroll-hijack and accessibility risk.
- React Bits: lean reject for backgrounds and text effects. Its Center Stage tool may still be useful later for recorded demos, which are out of scope here.
- Taste Skill: use only as a constraint layer under the fixed identity, if at all. Its direction-inference should not override the identity.
- image-to-code: adapt the "mockup before building" idea without image generation. D4's static mockup replaces it.
- Web Design Guidelines: adopt as the final audit gate (vendor a pinned copy of the rules into the repo).
- Awesome DESIGN.md: use as a format and grammar reference only. Never copy a brand's file.
- Playwright CLI vs plain Playwright: decide which fits QA screenshots best.
- ThreeUI and Skillry: reference only.

**Gate:** the owner approves the decision table. If you recommend a deviation from the priors, say why.

---

## D2. Tokens and type

**Rule:** a project theme changes only three things: a ground tint, a tonal ramp, and one signature device. Everything else is locked chrome: type, grid, line weights, footer, and the vermilion rule.

**Starting hypothesis, not a decision.** The ctxcheck theme "Sediment": a ground a step deeper and greyer than base off-white (about `#ECE6D8`), surface `#F4F0E6`, a four-step sand ramp for system / tools / history / tool output (`#CFC6B2`, `#BDB29A`, `#A99C82`, `#8F8269`), and an umber summary band (`#6E6350`). Validate it, improve it, or replace it. The theme must be clearly different from base but not far from it.

**Signature device, the compaction seam:** a 1px ink rule with small notch ticks and a mono label, for example `compaction @ step 31`.

**Fate encoding (invariant).**
- **kept** = solid teal marker.
- **changed** = dashed teal marker plus a visible text diff.
- **gone** = vermilion marker that physically falls out of frame.

**Method for deciding values**
- Produce at most 3 candidate grounds (and, if base is Proposed, at most 2 candidate base identities). Render each on a swatch sheet **and on a static frame of the real strata layout**, not only as swatches. Compute contrast. Recommend one with reasons.
- **Fonts:** choose a sans plus a mono from openly licensed families (verify the licence), host them locally as woff2, and check numeral behaviour (tabular numerals) and rendering at small sizes.
- Study the grammar of 3 to 5 reference DESIGN.md files (see D1) for how they structure type scale and spacing. Do not copy values.

**Deliverables**
- `design/identity/base.tokens.json` (if base was Proposed) and `design/themes/ctxcheck/tokens.json`
- `tokens.css` (CSS variables) generated from the JSON by a script, so there is one source of truth
- A swatch and contrast contact-sheet PNG, including a 360 px-wide version
- A short type specimen PNG

**Checks, computed by script:**
- WCAG AA contrast (at least 4.5:1) for every text/ground pair used, and at least 3:1 for non-text markers.
- Adjacent strata layers must be distinguishable. Use a 1px ink hairline at about 20% between layers if tones are too close.

If vermilion on the ground fails contrast, **adjust the ground first**. Do not alter vermilion.

**Gate:** the owner approves the ground, and the base identity if it was Proposed.

---

## D3. Rules files

Create two files.

**`design/VIDEO_RULES.md`**

- **Banned:** cuts, glow, particles, device mockups, large kinetic type, fade-everything, centered title on a gradient, corner labels and frame borders, decorative music, stock dashboard cards, any redrawn product UI.
- **Motion physics:**
  - Step arrivals use snappy closed-form springs.
  - The seam uses one heavy spring with a hard stop before and after.
  - The step cadence accelerates as the window fills, which builds tension.
  - No linear slides.
  - Something new happens every 2 to 4 s.
- **Honesty rules:**
  - The label `synthetic fixture` is visible in every frame until real runs exist (M2).
  - Every number on screen is traceable to the run file.
  - No result claims in captions.

**`design/SITE_RULES.md`**

- **Banned:**
  - Gradient hero with a generic tagline.
  - Stock dashboard cards with numbers and no provenance.
  - A paper-style PDF rendered as a page.
  - Large logos.
  - Animated everything.
  - Cards inside cards inside cards, and giant rounded wrapper sections.
  - Decorative pills, badges, fake system labels and invented status jargon.
  - Default purple/blue AI gradients, stacked glassmorphism, glowing edges.
  - Identical card rows repeated section after section.
  - Hero headlines of 4 or more lines.
- **Hero rules:** the first view on a 1280×720 laptop viewport shows one claim, one primary action, and the strata visual, readable without scrolling and not crowded.
- **Motion:**
  - Animate `transform` and `opacity` only.
  - Never `transition: all`.
  - Honour `prefers-reduced-motion` (the playground shows its final state, with no autoplay).
  - No autoplay motion longer than 5 s without a pause control.
- **Interaction:** keyboard-first (← / → step, `?` help), visible focus states, step deep-linked in the URL.
- **Component sources:** 21st.dev (or similar) only for chrome (tabs, tables, dialogs, command palette, tooltip, slider). The strata view and anything signature is hand-built. Record every borrowed component in a register (source, licence, where used, how modified).
- **Performance:** keep initial JS small. Measure the baseline and set a budget.

Also propose, as a diff and without applying it, a short pointer in `CLAUDE.md` to these files. Do not paste the banned lists into `CLAUDE.md`.

**Gate:** approved.

---

## D4. Site mockup (static look approval)

**Prerequisite:** approved references (D0 item 6). Extract the grammar of each reference (layout logic, type behaviour, spacing, texture, how content is ordered) into `design/style_guide.md`. Take grammar, **never** content, logos or characters. Show it and wait for his OK before building.

Then build a **static, real-HTML mockup** (no motion) of just two things, rendered at 1440, 768 and 390 px:

1. The `/` first view (hero): the strata visual as a hand-built still (use the fixture, below), one claim, one primary action.
2. One content section below the hero (for example "what this is, what it is not, prior art credited").

Use tokens only. Screenshot with Playwright. Deliver the screenshots and a short note on the choices made.

**Gate:** the owner approves the look **before any other page or any motion**. This is a taste decision that only the owner can make. If he rejects it, iterate on the mockup. Do not build further.

---

## D5. Renderer

Build a minimal, deterministic video renderer: Node + Playwright + ffmpeg only. Justify any extra dependency in writing before adding it.

**Page contract** (`design/video/index.html`):
- Exposes `window.seek(t)`, `window.__duration`, and a `window.__ready` promise.
- Loads the run file from `?run=` and the theme from `?theme=`.
- `seek(t)` is a **pure function of `(t, runData)`**. The same `t` always yields identical pixels.

**Forbidden in render mode:**
- `Date.now`
- `Math.random` (use a seeded PRNG from `meta.seed`)
- CSS transitions and animations (enforce with `* { animation:none!important; transition:none!important }`)
- requestAnimationFrame-driven state
- `<video>` and GIF elements
- Any network access

**Springs:** closed-form damped springs. A value with several target changes uses one stacked spring per change, each starting at its own time, so any frame can be computed without replaying history.

**Fonts:** the local woff2 files from D2. Await `document.fonts.ready` before capture.

**Render script flags:** `--fps`, `--sub` (subframes blended for motion blur), `--from/--to` seconds (partial re-render), `--draft` (half resolution), `--out`.

**Defaults:**
- Draft: 540×675, 30 fps, sub 1.
- Final: 1080×1350, 30 fps. Choose `sub` after you measure render time.

Encode H.264 `yuv420p`, CRF 16 to 18, `-movflags +faststart`. Before the final encode, verify current LinkedIn video specs (aspect ratio, length, file size) and report what you found.

**Cost note:** screenshots = duration × fps × sub. Report measured draft and final render times, and propose optimizations before proceeding if the final render is slow.

**Helper scripts (ffmpeg):** a contact sheet (2 frames per second, 6 across), a strip of 12 frames around a chosen timestamp, and a phone check (sheet scaled to 360 px width).

**Exit criteria, on a trivial test scene** (colour bars plus a counter):
1. Render frame t=11.37 first and last, in random order, twice. SHA-256 of the PNGs must match.
2. Sequential and random-access renders must be identical.
3. Timings reported.

**Gate:** approved.

---

## D6. Video keyframes (look approval before motion polish)

Build the scene code against the fixture (below), with a rough timeline. If D4's strata still and the scene diverge, reconcile them so the site and video use the same component.

Render **three static frames at 1080×1350 from the real scene code**, not a separate mockup:
- **t≈1.0** (hook)
- **t≈9.5** (seam)
- **t≈20.0** (consequence)

Deliver them individually plus a contact sheet. **Gate:** the owner approves the look before any motion polish.

### Scene spec (28 s, 4:5, one continuous diagram, no cuts)

**Layout zones:** a top status strip in mono (step counter, tokens/limit, `synthetic fixture`), a main diagram area, and a bottom burned-in caption strip. Margins and grid come from the identity.

| Time | On screen |
|---|---|
| 0 to 2 s | Layers stack up fast. One small mono line: `3 facts planted. 1 compaction.` No headline. |
| 2 to 8 s | Steps arrive as layers (system / tools / history / tool output / summary) while the window fills toward a hard limit rule. Teal markers with leader lines pin the planted facts. Step cadence accelerates as the window fills. |
| 8 to 11 s | The limit is hit and the seam sweeps down. The layers collapse into one summary band on one heavy spring. |
| 11 to 17 s | Fates resolve per canary: kept, changed (dashed marker plus text diff), gone (vermilion, falls out of frame). |
| 17 to 23 s | Two columns, `with fact` and `after compaction`, same step and same question. Left: the refusal tool call. Right: the forbidden tool call in vermilion, labelled `behaviour changed`. |
| 23 to 28 s | Zoom out to the survival grid (policy × canary type). Cells fill one by one, each with a rate and an interval whisker. Ends on the permalink and project name (swappable, since the name is provisional). |

### Fixture and data contract

The scene never reads the raw trace. Build a separate **adapter** (trace schema to scene input) with its own tests, plus a generator script for a synthetic fixture (seeded, committed as `fixtures/run_synthetic_001.json`).

Scene input shape:

```json
{
  "meta": {"label": "synthetic fixture", "seed": 1, "model": null,
           "policy": "llm_summary", "limit_tokens": 0},
  "steps": [{"i": 1, "layers": {"system": 0, "tools": 0, "history": 0,
                                "toolOutput": 0, "summary": 0}}],
  "compaction": {"at_step": 31,
                 "after": {"system": 0, "tools": 0, "history": 0,
                           "toolOutput": 0, "summary": 0}},
  "canaries": [{"id": "C1", "type": "constraint", "planted_step": 3,
                "text": "", "fate": "kept|changed|gone", "after_text": null}],
  "consequence": {"canary": "C1", "step": 32,
                  "with":  {"tool_call": ""},
                  "after": {"tool_call": ""}},
  "grid": {"rows": [], "cols": [],
           "cells": [{"rate": 0, "lo": 0, "hi": 0, "n": 0}]}
}
```

**Fixture contents:**
- About 40 steps.
- Three canaries (constraint, exact identifier, failed approach) with one fate each of kept, changed and gone.
- Compaction at step 31.
- Grid intervals computed with **Wilson** from synthetic counts, to match the project's EVAL_DESIGN.

If the real trace schema lacks fields the scene needs, **propose a schema addition** to the owner. Do not change the schema yourself.

---

## D7. Full video, critique loop, final render

Implement the full storyboard, then run the critique loop for **at most 3 rounds**.

**Rubric, scored 1 to 10 by you looking at the contact sheet, a strip around the seam, and the phone sheet:**
1. Hook clarity in the first 2 s
2. Legibility at 360 px
3. Motion quality (weight, no linear slides)
4. Pace and variety (something new every 2 to 4 s)
5. Identity fidelity (tokens only)
6. Data honesty (every number traceable, synthetic label visible)
7. One-idea clarity: a viewer can say what vermilion means without reading
8. No overlaps or clipped text
9. Genericness test: if the project name and permalink were removed, could this be mistaken for any other AI-made demo? Name the specific frames that look generic.

Critique as a harsh motion director, not a proud author. Specifically hunt for: text overlapping during swaps, anything sliding instead of easing, centered-on-gradient moments, blurry scaled text, dead beats with nothing happening, and decoration that carries no data.

Fix the 3 worst problems per round. The target is at least 8 on each. If you cannot reach it, report where you got stuck rather than looping. Self-critique is biased, so also list what you would cut. The owner's judgement is final.

**Programmatic checks (all must pass):**
- No raw hex or px values outside the token files (grep).
- Contrast script passes.
- Overflow check: measure text bounding boxes at sampled times.
- Determinism test passes.
- `synthetic fixture` appears in 100% of sampled frames.

**Deliverables:**
- `out/ctxcheck_pilot_4x5.mp4`
- `out/contact.png` and `out/phone.png`
- A poster frame
- A captions text file

**Gate:** approved.

---

## D8. Site build

Build the site scope defined above, using the approved D4 mockup, the tokens, and the scene component from D6 and D7.

**Pages and parts:** the app shell, `/`, `/about`, and the embeddable strata player: a scrubber, ← / → stepping, `?step=` deep-link, reduced-motion behaviour, and the `synthetic fixture` label wherever fixture data is shown. The playground on `/` plays the sample run once, then shows "open the recorder" (link target can be a placeholder route; the recorder itself is out of scope). Where reduced motion is on, show the final state with no autoplay.

**Static export, no server, no database, no API keys** (this follows the existing DESIGN.md). Follow the framework and build setup from D0.

**QA loop (at most 3 rounds):**
1. Playwright screenshots at 390, 768 and 1440 px, plus one at 1280×720 for the first-view rule.
2. Score against this rubric, 1 to 10: hierarchy, type, spacing rhythm, identity fidelity (tokens only), first-view clarity at 1280×720, density, accessibility (focus, keyboard, contrast), and the genericness test ("with the name removed, could this be any other AI-made site?").
3. Fix the 3 worst problems per round. Target at least 8 on each. If you can't reach it, report where you got stuck.

**Gate checks (all must pass):**
- Run the Web Design Guidelines rules from the vendored copy over the code and fix every finding. Report any rule you consciously skip, and why.
- No raw hex or px values outside the token files.
- Keyboard walkthrough works without a mouse. Reduced-motion behaviour is verified.
- Set and record the initial JS budget from the measured baseline.
- Any borrowed component is in the register with its licence.

**Deliverables:** the built site (static export), screenshots at all widths, and `design/README.md` explaining how to run, build and re-render the video in three commands, with the font and component licence register.

**Then STOP.** Do not start the product views, deployment, posting, a 16:9 variant, music, or the portfolio.

---

## Definition of done

- Resource decisions recorded and approved.
- Theme tokens approved and contrast-verified, with one source of truth (JSON generating CSS).
- Rules files approved.
- The site mockup approved by the owner, and the site built to match it.
- The renderer is deterministic (the test passes).
- The pilot video renders from the fixture. Swapping the run file produces a different, correct video with no code changes.
- The honesty label is present in all frames and wherever fixture data is shown.
- Everything is reproducible from `design/README.md`.

## Unverified assumptions (confirm in D0)

- The base identity values and fonts are not in this handoff.
- The trace schema may lack some fields the scene needs.
- The repo layout, web framework and M1 state are unknown.
- Node, ffmpeg and Playwright availability.
- Current LinkedIn video specs.
- The Sediment values are an untested hypothesis, as are the orchestrator's priors in D1.
- "ctx agent" is assumed to mean ctxcheck.

## Working rules

- Keep `design/PROGRESS.md` updated after every gate: gates approved, decisions made, open items, and the exact next step. A fresh session must be able to resume from this file plus this handoff alone.
- Do not ask the owner for manual work. Present decisions and a recommendation, then wait.
- No dependency beyond Playwright and ffmpeg (plus the web framework already in the repo) without a written case approved at a gate.
- Record every font and component licence in a register in `design/README.md`.
- Propose, but mark **Proposed**, the next free ADRs: "video is a headless render of the strata scene" and "theme = ground + ramp + device".
- Never copy another brand's DESIGN.md, and never let a skill's default style override the identity.
