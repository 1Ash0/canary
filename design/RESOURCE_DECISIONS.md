# D1 — Resource decisions

Status: **awaiting owner approval** · 2026-10-20.
Every resource below was fetched and read first-hand on 2026-10-20 (Firecrawl scrape or `npm view`). Licences were read from the licence text or the registry field, not from summaries. Sizes come from bundlephobia (a third-party measurement) or `npm view`. **No package has been installed yet**: the trial build runs right after this gate.

## Summary

| Resource | Verdict | One-line reason |
|---|---|---|
| GSAP (core + ScrollTrigger) | **Adopt, limited** | Delivers the "premium like GSAP" motion you asked for; limited to the site, core + ScrollTrigger only |
| Lenis | **Reject** (revisit at D8 QA) | Smooth scroll adds input lag to the scrubber and is a template tell; ScrollTrigger's `scrub` smoothing gives weight where it matters |
| React Bits (+ Center Stage, Background Studio) | **Reject** | Needs React, which we won't ship; MIT + Commons Clause; backgrounds and device mockups are banned decoration |
| ThreeUI | **Reject** (not even as reference) | Three.js/WebGL showpieces; nothing to take that fits the brief |
| Taste Skill | **Limit**: borrow 7 rules, don't install | Some rules are good; its direction-dealing and its bans on mono labels and thin rules would override our identity |
| Web Interface Guidelines | **Adopt** | MIT; the right final audit gate; vendor a pinned copy |
| Awesome DESIGN.md | **Limit**: grammar only | MIT; borrow the structure (named type roles, spacing scale, colour roles), never values |
| Video method doc (Google Doc) | **Adopt the method** | `seek(t)` contract, stacked closed-form springs, contact-sheet critique loop; we write our own code |
| Skillry Opus 5.5 gallery | **Reference only (anti-reference)** | Mostly 3D launch films; useful for the genericness test |
| awesome-opus5-5-videos | **Limit**: structure only | MIT; the strong prompts share a `direction / structure / build / gotchas` layout |
| Remotion vs HyperFrames | **Reject both** | The handoff fixes Node + Playwright + ffmpeg; a ~150-line renderer meets the contract. HyperFrames (Apache-2.0) is the fallback |
| Playwright vs playwright-cli | **Adopt `playwright`**, reject `playwright-cli` | One scriptable dependency serves both QA and the renderer; the CLI is pre-1.0 and records in real time |
| **Framework (delegated to me)** | **Vite + vanilla TypeScript**, replacing Next.js and Tailwind | Smallest JS for a mostly static site with one hand-built SVG instrument; needs ADR-015 |

---

## Per resource

### GSAP — https://github.com/greensock/GSAP, gsap.com docs
1. **What:** a timeline animation library; ScrollTrigger ties animations to scroll (scrub, pin, snap); `gsap.matchMedia()` reverts animations when a media query stops matching, including `prefers-reduced-motion`.
2. **For us:** the site only. Pinned strata section that scrubs through steps as you scroll, line-level heading reveals, seam "drop" choreography. The **video does not use it**: the renderer is `seek(t)` with closed-form springs.
3. **Cost:**
   - Size: 69 kB min / 26.7 kB gzip for `gsap@3.15.0` (bundlephobia). ScrollTrigger's size was not listed, so it gets measured in the trial build.
   - Accessibility: there's a risk only if motion ignores reduced-motion. Mitigation: every GSAP setup goes through `matchMedia` with a reduced-motion branch that shows the final state.
   - **Licence:** "Standard No Charge GSAP License" (Webflow, effective 2025-04-30). It permits use "on any website, web application, or digital interface". It prohibits use in visual no-code animation builders that compete with Webflow. It is **not OSI open source**, and Webflow can revise it, but earlier versions stay usable under their original terms. Our use (a project website) is a Permitted Use.
   - Maintenance: mature, actively maintained.
4. **Alternative:** CSS scroll-driven animations (`animation-timeline: view()`) plus `transition`. That works for simple reveals, but there's no robust pinning with scrub smoothing, no timeline sequencing, and support is uneven in Safari.
5. **Verdict: adopt, limited.**
   - Allowed: `gsap` core + `ScrollTrigger` only.
   - SplitText only for **line-level** reveals of at most one heading per page. No character-level text effects.
   - Not used: ScrollSmoother, MorphSVG, ScrambleText, Physics.
   - **Deviation from the prior** ("possibly only if CSS can't"): you asked for a GSAP-grade feel, and pin + scrub of the strata section is the one thing CSS can't do reliably.

### Lenis — https://github.com/darkroomengineering/lenis
1. **What:** smooth-scroll library on top of native scroll (MIT, v1.3.27, 458 kB unpacked). Honours reduced motion by default.
2. **For us:** it would smooth wheel scrolling sitewide.
3. **Cost:** an extra rAF loop. The README lists known limits: capped at 60 fps on Safari, no CSS scroll-snap, iframes break smoothing, `position: fixed` lag on older Macs. It adds latency between input and the strata scrubber.
4. **Alternative:** native scroll, plus `scrub: 0.5` smoothing on the one choreographed section.
5. **Verdict: reject** (prior confirmed). Revisit at the D8 QA round if the pinned section feels cheap without it.

### React Bits — https://github.com/DavidHDev/react-bits
1. **What:** 215+ animated React components and backgrounds. Its tools are Background Studio (tune and export animated backgrounds) and Center Stage (screenshots into 3D device mockups).
2. **For us:** nothing. We don't ship React (ADR-015), and the signature views are hand-built.
3. **Licence:** MIT + Commons Clause, which restricts selling the software itself.
4. **Alternative:** hand-built SVG, plain CSS.
5. **Verdict: reject.** Device mockups are banned in VIDEO_RULES, and animated backgrounds are decoration with no data.

### ThreeUI — https://threeui.com/browse
1. **What:** a gallery of Three.js components, WebGL backgrounds and 3D product scenes.
2. **For us:** nothing. 3D fails the desired-feel test.
5. **Verdict: reject**, even as a reference.

### Taste Skill — https://github.com/Leonxlnx/taste-skill, https://www.tasteskill.dev
1. **What:** agent skills for art direction (MIT). The main skill deals 3 of 20 directions and runs a browser lint and screenshot loop at 1440, 768 and 390 px. The site adds a desktop app (TasteCode) and a gallery.
2. **For us:** a constraint layer only. Rules I'll borrow into SITE_RULES:
   - no eyebrow pills or small badges above headings
   - headlines at most two lines at every width
   - one ground, one ink, one accent
   - equal outer margins
   - section gap clearly larger than any internal gap
   - motion uses only `transform` and `opacity`
   - screenshot gate at 1440, 768 and 390 px
3. **Conflicts:**
   - It bans monospace outside code blocks and bans thin rules. Our mono labels and 1 px point-of-observation rule are identity invariants.
   - `soft-skill` uses `transition-all`, which the Vercel rules ban.
   - `minimalist-skill` bans Inter (moot: our font choice comes at D2).
4. **Status of the named sub-skills:**
   - `redesign-skill` is retired (folded into `design-taste-frontend`).
   - `image-to-code-skill` has moved to a separate repo (`Leonxlnx/imagegen-skills`).
   - `output-skill` isn't in the repo tree as of 2026-10-20.
5. **Verdict: limit.** Don't install it. Borrow the seven rules above with credit. Its "mockup before building" idea is covered by the D4 static mockup, with no image generation (prior confirmed).

### Web Interface Guidelines — vercel-labs/web-interface-guidelines `command.md`
1. **What:** a review checklist covering accessibility, focus, forms, animation, typography, content, images, performance, URL state, touch, theming, i18n, and anti-patterns.
2. **For us:** the final audit gate at D8, and the motion rules for SITE_RULES.
3. **Licence:** MIT (Vercel Labs, 2025), verified from the LICENSE file through the GitHub API.
5. **Verdict: adopt.**
   - Vendor a pinned copy to `design/vendor/web-interface-guidelines/command.md`, recording the source URL, date and blob sha.
   - **Planned conscious skips** (to confirm at D8):
     - "Title Case for headings": we use editorial sentence case.
     - Tailwind/React-specific phrasing (`focus-visible:ring-*`, `nuqs`, hydration): mapped to plain-CSS and vanilla-TS equivalents.

### Awesome DESIGN.md — https://github.com/VoltAgent/awesome-design-md (studied: Linear, Vercel, Claude)
1. **What:** DESIGN.md write-ups of brand systems (MIT).
2. **For us:** the grammar for `tokens.json` and the type spec:
   - named type roles (display, heading, body, label, mono), each with size, weight, line-height and tracking
   - a named spacing scale on a 4 px base with a separate `section` token
   - a radius scale
   - colour roles grouped as accent, surface ladder, hairline, text, semantic
   - none of the three studied files has an explicit do/don't section; ours will (SITE_RULES)
5. **Verdict: limit**, grammar only. No values copied.

### Video method — Google Doc "How to Build a Motion Design Studio with Opus 5.5"
1. **What:** a pipeline guide covering the `seek(t)` render contract, a CLAUDE.md banned list, a Playwright → ffmpeg renderer with subframe blending (`tmix`), closed-form springs with stacked `track()`, ffmpeg contact sheet, strip and phone checks, a 3-round critique loop, and reference → style guide → shotlist.
2. **For us:** the core of D5–D7, and it matches the handoff almost line for line.
3. **Licence:** none stated (a public guide with a community upsell). We reimplement the ideas. The spring is the standard damped-oscillator formula.
4. **Not taken:**
   - music and beat-sync (out of scope)
   - voiceover and API keys
   - 9:16 and 16:9 variants (out of scope)
   - "real product screenshots" (our product view *is* the scene)
   - the paid community
5. **Verdict: adopt the method.**

### Skillry Opus 5.5 gallery — https://skillry.dev/ai-videos/opus-5-5
- **What:** 418 videos with their prompts.
- The visible entries are mostly Three.js 3D scenes, launch films with glow, particles and kinetic type, and SaaS promos. That's the genre the handoff tells us to avoid.
- **For us:** an anti-reference for the D7 genericness test. Its paid skills are not used.
- **Verdict: reference only.**

### awesome-opus5-5-videos — https://github.com/yihui-dev/awesome-opus5-5-videos
- **What:** MIT; 703 prompt files.
- The sampled prompt (`moritzkremb-466494`) is a vague one-paragraph SaaS launch brief, which is exactly what produces generic output.
- The better entries quoted in the gallery use explicit `direction / structure / build / gotchas` blocks with hex palettes and type specs.
- **Verdict: limit.** Use that block structure for our scene spec. Don't take any look.

### Remotion vs HyperFrames — https://skillry.dev/learn/remotion-vs-hyperframes
- **Remotion:** React, source-available (free for up to 3 employees).
- **HyperFrames:** HeyGen, plain HTML, Apache-2.0, deterministic local MP4.
- **Verdict: reject both.** The handoff fixes the stack, and a framework-free scene module plus a small renderer meets the contract with zero extra dependencies.
- **Fallback:** HyperFrames, if our renderer fails the determinism or time budget at D5.

### Playwright vs playwright-cli
- **playwright-cli** (`@playwright/cli` v0.1.22, Apache-2.0): an agent-oriented interactive CLI (screenshot, resize, real-time video recording).
- **playwright** (v1.64.1, Apache-2.0): scriptable, already required for the renderer's seek loop. Browsers are already cached (chromium-1228); version match gets checked at install.
- **Verdict: adopt `playwright` only** as a dev dependency in `design/`. One dependency covers QA screenshots and frame capture.

---

## Framework decision (owner delegated: "pivot to whatever the site requires")

**Recommendation: Vite + vanilla TypeScript, multi-page, static output. No React, no Next.js, no Tailwind.** Recorded as ADR-015 (Proposed). It supersedes ADR-003's choice of Next.js, while keeping ADR-003's rule that the web reads files and never calls a model.

**Why:**
- The site is a few static pages plus **one** hand-built SVG instrument (the strata player). React adds runtime weight and buys nothing for that.
- The scene must run unchanged in the site **and** in `design/video/index.html` (a plain page with `window.seek`). A framework-free ES module is the natural shape for both.
- Later product views (`/run/[id]`, `/lab`) fit as static pages that lazy-load run JSON client-side, which DESIGN.md already specifies. Pydantic → JSON Schema → TS types (ADR-004) still works.
- Tokens come from `tokens.json` → `tokens.css` (D2). Tailwind would be a second source of truth for the same values.

**Dependencies to add after this gate:**
- `vite`, `typescript` (dev)
- `gsap` (runtime)
- `playwright` (dev, in `design/`)

**Cost to measure in the trial build:** initial JS (target: under 60 kB gzip on `/`, to be confirmed by measurement) and a reduced-motion check.

**What I'd lose vs Next.js:** file-based routing and React's ecosystem for the later views; build-time OG images become a small Node script (M5).

## Identity implication (input to D2, ADR-014)

Firecrawl's branding extraction of gsap.com on 2026-10-20:
- **Ground and text:** warm near-black ground `#0E100F`, cream primary text `#FFFCE1`, olive-grey secondary text `#7C7C6F` / `#BBBAA6`.
- **Accent:** a bright green brand accent used sparingly (`theme-color #0ae448`).
- **Type and shape:** one typeface (Mori, proprietary), square primary buttons, pill secondary buttons, 4 px spacing base. The extraction rated its energy as "low".

**Reading:** GSAP's premium feel is **restraint on a warm dark ground**, not glow. That can keep every invariant (one teal accent, vermilion only for loss, fate encoding, honesty label). D2 will render at most three grounds on the real strata frame:
- **A** — warm off-white notebook (DESIGN.md's original brief)
- **B** — warm near-black with cream ink (the GSAP-like direction; **recommended**)
- **C** — B with a light reading surface for long-form sections (`/about`)

Teal and vermilion get lifted in lightness for the dark ground until the contrast script passes.
