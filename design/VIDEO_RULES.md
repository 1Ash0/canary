# VIDEO_RULES — Canary pilot video

Status: **approved (owner, D3 gate, 2026-10-20)**. The video is a headless render of the strata scene (ADR-016): one continuous 4:5 diagram, 28 s, every pixel from a run file.

## Banned
- Cuts, fades between scenes, fade-everything.
- Glow, particles, gradients, 3D, device mockups, frame borders, corner labels.
- Large kinetic type; a centred title on a gradient.
- Decorative music (no audio in this pilot).
- Stock dashboard cards; any redrawn product UI.

## Motion physics
- Closed-form springs only (`motion.spring.*` in `identity/base.tokens.json`). A value with several targets uses one stacked spring per change, so any frame can be computed directly.
- **Step arrivals:** `spring.step` (snappy, slight overshoot). The cadence accelerates as the window fills, which builds tension toward the limit.
- **The seam:** one `spring.seam` (heavy, critically damped) with a hold before and after it.
- **Gone markers** leave the frame on `spring.fall`.
- No linear slides. Something new happens every 2–4 s.
- Text explaining a state enters after the state changes and leaves before the next one. It never overlaps during swaps.

## Legibility (from D2's 360 px check)
- The 1080-wide frame is seen at about 360 px on phones (a third of full size).
- On-screen text is **≥ 24 px at 1080 width** (about 8 px on a phone); mono readouts are ≥ 26 px.
- Fewer, larger labels than the site player. Leader-line labels show the canary id and fate only, not the full fact text.

## Honesty
- `synthetic fixture` is visible in **every frame** until real runs exist (M2). Checked on sampled frames.
- Every number on screen comes from the run file through the adapter. No literal numbers in scene code.
- Captions make no result claims. They describe what the fixture shows ("3 facts planted"), not what models do.

## Render contract (D5)
- **Page API:** `window.seek(t)`, `window.__duration`, and a `window.__ready` promise.
- **Inputs:** run from `?run=`, theme from `?theme=`.
- **Purity:** `seek(t)` is a pure function of `(t, runData)`.
- **Forbidden in render mode:** `Date.now`, `Math.random` (use a seeded PRNG from `meta.seed`), CSS transitions and animations, rAF-driven state, `<video>`/GIF, and network access.
- **Fonts:** local woff2; await `document.fonts.ready` before capture.
- **Encoding:** H.264 `yuv420p`, CRF 16–18, `-movflags +faststart`.

## Critique loop (D7)
- At most 3 rounds.
- Score 1–10 on the handoff rubric, looking at the contact sheet, a strip around the seam, and the 360 px phone sheet.
- Fix the 3 worst problems per round. Hunt specifically for overlaps during swaps, sliding, blurry scaled text, dead beats, and decoration that carries no data.
