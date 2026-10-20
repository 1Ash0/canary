# D0 — Orientation report

Status: **awaiting owner approval** · 2026-10-20 · no code written.
Read: `CLAUDE.md`, `docs/DESIGN.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `src/ctxcheck/schema/events.py`, `web/`.

---

## 1. Base identity values

**Found in `docs/DESIGN.md`:** descriptions only, no hex values, no font files, no spacing scale or line weights.
- Warm off-white ground, near-black text, one deep-teal accent, vermilion only for real loss. No blue except hyperlinks and syntax highlighting.
- Sans for text (Inter / IBM Plex Sans / Geist suggested), mono for labels, numbers, ids.
- Signature device: the "point of observation" marker.
- Epistemic tags: `recorded`, `simulated`, `measured n=…`, `reproduced`, `reasoned`, `broke`.

**Proposed base identity (decide at D2; every value will be re-checked by script):**

| Token | Value | Note |
|---|---|---|
| ground | `#F5F1E8` | warm off-white |
| surface | `#FBF9F4` | panels, code |
| ink | `#1A1814` | near-black, warm |
| ink-2 | `#5A554B` | secondary text |
| hairline | ink at 20% | rules, layer separators |
| accent (teal) | `#0F5E5C` | ≈6.7:1 on ground [hand-computed, verify at D2] |
| loss (vermilion) | `#B83A1B` | ≈5.1:1 on ground [hand-computed, verify at D2] |
| link | `#1F4FA8` | the one allowed blue, links only |

- **Fonts:** IBM Plex Sans + IBM Plex Mono (SIL OFL 1.1, verify at D2). Reason: one family with tabular numerals and a drawn, engineering feel. Inter reads as default SaaS. Fallback pair: Inter + JetBrains Mono.
- **Spacing:** 4 px base, scale 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96. 12-column grid, 1120 px max content width, prose measure about 68ch.
- **Line weights:** 1 px hairline, 1.5 px rule, 2 px emphasis or marker stem.
- **Point of observation:** a 1 px teal vertical rule, a small downward notch at the top and a mono label (`step 31`). It is locked base chrome and appears in every view.

## 2. Trace schema

**Implemented** (`src/ctxcheck/schema/events.py`): only `run_start` (scenario_id, seed, policy, provider, model, harness_git_sha) and `run_end` (status).
**Documented but not built** (ARCHITECTURE "Trace schema v0"): `message`, `model_call`, `tool_call` / `tool_result`, `compaction`, `canary_planted`, `canary_probe`.

| Scene needs | Source in documented v0 | Gap |
|---|---|---|
| per-step tokens per layer | `message.tokens_est` grouped by `role`/`origin` | no **step** index (only `seq`); no token count for **tool specs**; no window **limit** field |
| compaction | `compaction` (tokens_before/after, kept/dropped/added ids, summary_message_id) | step is derivable from `seq` once "step" is defined |
| canary plants | `canary_planted` (message_id, value) | none |
| fates kept / changed / gone | none | **missing.** `canary_probe` grades behaviour, not survival |
| consequence (with vs after) | `tool_call` events | the "with fact" side is a **paired run**; there is no pairing key on `run_start` |
| survival grid | `results/*.json` (n, k, intervals) | none; adapter reads results, not the trace |

**Proposed schema additions (for the owner, not applied; `src/ctxcheck/` is the Teach-First lane):**
1. Define a step: either add `step: int` to `message`/`model_call`, or document "step = index of the nth `model_call`" (no schema change).
2. `limit_tokens` (budget) on `run_start`.
3. `tools_tokens_est` on `model_call`.
4. A `canary_fate` event: canary_id, compaction_seq, fate (`kept|changed|gone`), after_text, method (`verbatim|normalized|judge`).
5. `trial_index` and `pair_id` on `run_start` so control and treatment runs can be joined.

Until then, the scene reads only the synthetic fixture through the adapter. The adapter is the one place that will change when the real schema lands.

## 3. Repo state

- **Web:** no framework. `web/index.html` is a single static file (about 900 lines, inline CSS and JS) served by `npx serve`. `vercel.json` points at `web/`. No Next.js, Tailwind or d3, despite ADR-003 and ARCHITECTURE.
- **Current site:** a dark "Canary" landing page with a canary-yellow accent, an animated dither hero, cursor glow, 3D card tilt and a terminal demo. It includes an **uncommitted** edit to the dither hands. See conflict C1.
- **M1 strata view:** not reserved for the owner. ADR-010 puts web/CSS in the light lane. The current page has a mock strata animation that is not built from a run file.
- **Core:** `src/ctxcheck/` modules are empty stubs. The learning units (U2–U5) live in `learn/`. `results/` and `runs/` are empty.
- **`design/` location:** repo root, as proposed. It will be self-contained so it can be lifted out later: `identity/`, `themes/ctxcheck/`, `video/`, `fixtures/`, `scripts/`, plus its own `package.json` for Playwright.

## 4. Tooling

| Tool | Status |
|---|---|
| node / npm | v22.17.0 / 10.9.2 |
| python | 3.12 via uv 0.11.3 (system Python is 3.13.5) |
| ffmpeg | 8.1.2 full build (gyan.dev) |
| Playwright browsers | cached (chromium-1228, headless shell, firefox, webkit) |
| Playwright package | **not installed** (no npm or Python package in the repo). Will be added as a dev dependency at D5 (handoff allows it) |
| Fonts | **no local font files** anywhere in the repo or system. D2 needs to download woff2 files (needs your OK) |

## 5. Conflicts (handoff vs existing docs/repo)

| # | Conflict | Recommendation |
|---|---|---|
| C1 | The current `web/index.html` (dark ground, yellow accent, glow, dither, cursor glow, 3D tilt) breaks DESIGN.md's identity and the handoff's desired feel. | Treat it as a superseded experiment and keep it in git history. D8 replaces it. Don't commit the pending dither edit: stash or discard it (your call). |
| C2 | The page is branded **"Canary"**; ADR-009 says `ctxcheck`. | Use `ctxcheck`, with the name stored in one config value so it can be swapped. If you want "Canary", that needs an ADR under the pivot protocol. |
| C3 | ADR-003 / ARCHITECTURE: Next.js static export + Tailwind + d3-scale. Repo: plain HTML. The handoff says "follow the framework from D0". | Decide at D1. Lean: **Next.js static export** per ADR-003, because `/run/[id]` and generated TS types need it later. Write the strata scene as a framework-free ES module shared by the site and the video page. **Drop Tailwind** for `tokens.css` (needs an ADR line, since ARCHITECTURE names Tailwind). |
| C4 | DESIGN.md's device is the "point of observation"; the handoff's theme device is the "compaction seam". | The point of observation is locked base chrome. The seam is the ctxcheck theme's device, built from the same grammar (1 px rule, notch, mono label). |
| C5 | The handoff lives at `docs/design/DESIGN_SUBSYSTEM_HANDOFF.md`; its resume steps say `docs/design/HANDOFF.md`. | Rename it to `HANDOFF.md`. |
| C6 | DESIGN.md keeps the component register; the handoff wants it in `design/README.md`. | DESIGN.md stays authoritative ("existing docs win"). `design/README.md` holds the font register and links to the component register. |
| C7 | DESIGN.md's epistemic tag set doesn't include `synthetic fixture`. | Add `synthetic fixture` as a tag in DESIGN.md at D3 (an addition, not a conflict). |
| C8 | M1 exit 3 asks for a mock experiment (control vs recency_truncate, 10 trials, Wilson). The handoff fixture uses `llm_summary` and a policy × canary grid. | Compatible. The fixture grid includes `recency_truncate` with n=10 so the same file satisfies M1 exit 3. |

## 6. References (none supplied yet; candidates, all outside the AI-demo genre)

Pick 2 or 3. **D4 will not start without approved references.**

| Candidate | Take | Don't take |
|---|---|---|
| **Bartosz Ciechanowski's interactive essays** (ciechanow.ski) | one object explained by one continuous figure; controls directly under the figure; light ground; precise, weighty motion | the 3D renders, the subjects, essay length |
| **Tufte's small multiples and sparklines** (*Envisioning Information*) | data-ink discipline, hairlines, labels sitting on the data, small multiples for the survival grid | serif book typography, the print layout as a whole |
| **Lab instrument panels** (oscilloscope or field-recorder front panels) | a mono status strip, hard-stop motion, units on every number, a grid of readouts | skeuomorphism, product branding, hardware textures |
| **Distill.pub figures** | figure and caption as one unit, inline interactive figures in prose, margin notes | its fonts, the long-paper format (banned in SITE_RULES) |
| **Newspaper graphics desks** (NYT / FT data-journalism explainers) | one diagram transforming in steps, annotation leader lines, restrained palette | scroll-hijacking length, map or news subjects |

**Recommendation:** Ciechanowski + Tufte + instrument panels. Together they cover motion, data grammar and chrome.

## 7. Site scope check

- The roadmap does **not** reserve the strata view for you, so D8 keeps its full scope (shell, `/`, `/about`, embeddable strata player).
- **Gap to flag:** M1's exit ("a stranger opens a run, scrubs steps, copies a permalink") needs `/run/[id]` and a deployed URL. The handoff puts both out of scope. The `?step=` deep-link on the embedded player covers scrubbing and permalinks, but M1 stays open until `/run/[id]` and a deploy happen in a later task.

## Decisions needed at this gate

1. Approve the base identity as Proposed for D2 testing (or adjust).
2. C1: stash or discard the pending dither edit to `web/index.html`.
3. C2: `ctxcheck` or `Canary`.
4. C3 lean (Next.js static export, no Tailwind, framework-free scene module) to carry into D1.
5. References: choose 2–3, or supply your own with take / don't-take notes.
6. OK to rename the handoff file (C5).
