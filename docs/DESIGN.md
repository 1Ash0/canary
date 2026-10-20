# DESIGN — the web playground

Goal: someone lands from a LinkedIn post, usually on a phone, and within 30 seconds sees something real, interactive and unmistakably made by a person. It must not look like a templated dashboard or a paper in a dull wrapper.

## Identity
- Feel: premium technical instrument: restraint on a warm near-black ground, cream text, one teal accent (ADR-014; values in `design/identity/base.tokens.json` and `design/themes/canary/tokens.json`, which are the source of truth). **Vermilion only for genuine loss or failure.** No blue (except hyperlinks and syntax highlighting, where semantic blue is expected by engineers). No glow, gradients or 3D.
- Type: Instrument Sans for text, JetBrains Mono for labels, numbers and ids (both OFL 1.1, self-hosted woff2).
- Signature device: the **point of observation**: one consistent marker that shows the reader where and when to look (the compaction event, the step where a canary vanished). It appears in every view and every post image.
- **Epistemic tags** on every number and figure: `recorded`, `simulated`, `measured n=…`, `reproduced`, `reasoned`, `broke`, `synthetic fixture` (generated test data, shown until real runs exist). A viewer must never have to guess whether they are looking at a real model output or a transform of one.
- This matches the LinkedIn visual identity already planned, so posts and site look like the same hand.

## Pages
- `/` the playground: a short, auto-playing strata view of a sample run (plays once, respects reduced motion), then "open the recorder".
- `/run/[id]` the flight recorder (main view).
- `/lab` the survival matrix across policy × canary type × model, with intervals.
- `/lab/[exp]` one experiment: preregistration, results, deviations, links to runs.
- `/notebook` lab notebook entries, failures included.
- `/about` what this is, what it is not, prior art credited up front.

## Signature views (hand-built; no component library for these)

1. **Context strata** (M1). The window drawn as a stacked horizontal bar per step: system / tools / history / tool output / summary, stepping like geological layers. Scrub or arrow-key through steps. This is the first screenshot people will remember.
2. **Loss lens** (M3-M4). Before/after compaction diff. Each planted canary is highlighted and marked `kept verbatim`, `changed`, or `gone` (verbatim check; paraphrase only if a labelled judge is added). Vermilion appears here and only here.
3. **Survival heatmap** (M4). Policy × canary type grid. Each cell shows the rate with a whisker for its interval, not just a colour; click opens the underlying runs. Colour is never the only channel.
4. **Counterfactual fork** (M5). Select a step; show what the agent did with the canary present versus after compaction, side by side, from paired runs.
5. **Budget scrubber** (M3). Slider that re-applies deterministic policies to a recorded session and shows what each would have kept. Always labelled **simulated**. LLM-summary outcomes are shown only from recordings.
6. **Permalinks and OG images** (permalink M1, OG M5). Every step has a URL. Build-time generated preview images so a post's link card shows the exact moment being discussed.

## Interaction rules
- Keyboard first: ← / → step, j / k next/previous event, `?` shortcut help, `c` jump to the compaction event.
- Deep link state in the URL (run, step, view).
- Mobile first for reading: legible labels, large tap targets, thin lines that survive compression, strong contrast.
- Respect `prefers-reduced-motion`. Vermilion plus an icon for loss (never colour alone).
- User-supplied traces are parsed in the browser. Show a clear "this file never leaves your browser" note. Nothing uploads.

## Performance and durability
- Static export; run JSON lazy-loaded; virtualize long event lists; keep initial JS small (set a budget in CI once there is a baseline and treat regressions as bugs).
- No server, no database, no API keys. A recorded run works forever.

## Using 21st.dev and other component sources
- **Use for chrome only:** tabs, tables, dialogs, command palette, tooltip, slider, toggles, layout primitives. **Never** for the signature views above; those must be hand-built so the project does not look templated.
- Workflow: search with the 21st tools, preview, then adapt the component to the identity (colours, type, spacing). Do not leave default styling.
- Check licence and attribution for every component. Record each in a table at the bottom of this file: component, source URL, licence, where used, how modified.
- Retrieving full component code may consume a daily quota on a free plan. Search first, retrieve only what you will use.
- Keep the dependency count low; prefer copying a small component and owning it over adding a heavy library (needs an ADR line if it is a core dependency).

### Component register
| Component | Source | Licence | Used in | Modified how |
|---|---|---|---|---|
| (fill as used) | | | | |

## Accessibility baseline
Contrast meets WCAG AA for text; focus states visible; all interactions reachable by keyboard; charts have text alternatives (the numbers are in a table underneath).

## Things that would make this look bad (avoid)
Gradient hero with a generic tagline; stock dashboard cards with numbers and no provenance; a paper-style PDF rendered as a page; big logos; animated everything. Prefer one beautiful, honest view.
