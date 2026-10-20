# D2 — Tokens and type

Status: **awaiting owner approval** · 2026-10-20.

## Recommendation
**Candidate B: warm near-black ground with cream ink**, plus **Instrument Sans + JetBrains Mono**.

This is the GSAP-grade direction from ADR-014. It is premium through restraint: a warm ground, cream type, one teal accent, vermilion only for loss, hairlines, and no glow, gradients or 3D.

| Look at | File |
|---|---|
| Strata frame, candidate B (1080×1350, the real layout) | `d2/png/strata-B.png` |
| Same frame, A and B2 | `d2/png/strata-A.png`, `d2/png/strata-B2.png` |
| Swatch + contrast sheet | `d2/png/swatches-1440.png`, `d2/png/swatches-360.png` |
| Type specimen (both pairs) | `d2/png/specimen.png` |
| Contrast numbers (script output) | `d2/contrast.md` |

## Why B over A and B2
- **A (warm off-white notebook)** is honest and calm, but it reads as a notebook, not the premium feel you asked for. It also fails one check: the `ink3` tick is 2.99:1 against the 3:1 minimum.
- **B2 (cooler graphite-green)** passes every check. Its green-tinted ramp clashes with the ochre summary band, though, and the cool cast loses the warm, human-made quality.
- **B** passes every check with margin:
  - ink 16.62:1, ink2 7.83:1
  - teal 7.22:1, vermilion 5.97:1
  - link 9.12:1, ink3 tick 3.99:1
  - Adjacent strata layers range 1.20–1.79:1, all at or above the 1.15 threshold, so no separator lines are needed.
  - Layer labels reach at least 4.65:1 when they use the better of ink or ground.

## Theme "canary" (ADR-017: ground + ramp + device)
- **Ground:** `#0E0D0B`, one step deeper than base `#121110`. Surface `#181613`.
- **Ramp:** system `#2B2722` → tools `#39342C` → history `#4A4337` → tool output `#5D5444`, then a summary band in ochre `#8C7A55`. The summary is the brightest layer on purpose: it is what compaction produced.
- **Device:** the compaction seam. A 1 px ink rule with 6 px notch ticks every 48 px and the mono label `compaction @ step 31`.
- **Fate encoding (invariant):**
  - kept = solid teal marker
  - changed = dashed teal ring, with the new text after `→`
  - gone = vermilion marker that falls from the seam, out past the axis, labelled `gone ↓` (text, not colour alone)
  - Every marker carries a ground-coloured halo, so it reads on any layer.

## Fonts
| Pair | Licence | Tabular figures (measured) | Note |
|---|---|---|---|
| **Instrument Sans + JetBrains Mono** (recommended) | OFL 1.1, no Reserved Font Name | both equal-width (`d2/png/specimen.tnum.json`) | Contemporary, slightly condensed display; less "default SaaS" than Inter; free to subset |
| IBM Plex Sans + Plex Mono | OFL 1.1, Reserved Font Name "Plex" | both equal-width | Reads more corporate; subsetting would require renaming |

The renders loaded fonts from Google Fonts, **for preview only**. Hosting them locally needs a download; see the decisions below.

## Critique log (2 rounds on strata frame B)
- **Round 1:**
  - "synthetic fixture" square overlapped its text, and the step and token readouts ran together → replaced with labelled readouts.
  - "Gone" stayed inside the bars and fate markers sat at arbitrary rows → fates now resolve inside the summary band, and gone drops below the axis.
  - With no scale it read as a generic chart → added a hairline token axis with 10k ticks.
  - The specimen used invented numbers → now pulled from `strata_sample.json`.
- **Round 2:**
  - The changed marker sat outside the summary band → moved inside it.
  - The gone line started at an arbitrary x → it now falls from the fact's position at the seam.
- **Genericness test:** with the name removed, could this be any AI demo? I don't think so. It is a data instrument with provenance on screen and no glow, gradient, particles or kinetic type.
  - **Residual risk:** dark + mono edges toward a "hacker terminal" cliché. The cream sans headline and the warm ground are what hold it off. Watch this at D4.
- **Known risk carried to D6/D7:** at 360 px phone width, the 1080 frame scales to a third, so 12 px labels become about 4 px. The video needs labels of 24 px or more and fewer of them. The site player is unaffected, because it is laid out per viewport rather than scaled.

## Trial build (D1 follow-up)
`trial/RESULT.json`:
- **Size:** GSAP core + ScrollTrigger + trial code = 113,993 bytes raw, **44,350 bytes gzip** (level 9; Vite reports 44.86 kB). Under the proposed 60 kB budget for `/`.
- **Reduced motion (two-sided check):**
  - `reduce`: final state, 0 ScrollTriggers.
  - `no-preference`: animation set up, 1 ScrollTrigger.
  - Both pass.

## Deliverables in place
- `identity/base.tokens.json`, `themes/canary/tokens.json` (both "proposed" until approved)
- `scripts/build-tokens.mjs` → `themes/canary/tokens.css` (75 variables, `color-scheme: dark`)
- `scripts/contrast.mjs` (exit 1 if the recommended palette fails)
- `scripts/d2-pages.mjs`, `scripts/shoot.mjs`, `scripts/trial-measure.mjs`

## Decisions needed at this gate
1. Approve **ground B** and the base identity (or pick A or B2).
2. Approve **Instrument Sans + JetBrains Mono**.
3. Permission to download the fonts for local hosting:
   - `@fontsource-variable/instrument-sans` v5.3.0 (424 kB unpacked, OFL-1.1)
   - `@fontsource-variable/jetbrains-mono` v5.3.0 (204 kB unpacked, OFL-1.1)
   - Both from the npm registry. I copy only the Latin woff2 files into `design/identity/fonts/`.
4. On approval I also update DESIGN.md's identity line, the palette now being dark (ADR-014 → Accepted).
