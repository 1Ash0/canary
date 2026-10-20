// Two-sided motion checks for the hero (SITE_RULES §4.5):
//   reduce        → final state immediately, no autoplay (playhead stays at the end)
//   no-preference → autoplay runs (mid-run the player shows fewer than N steps, button says Pause)
//   ?step=12      → still state at step 12, no autoplay, even with motion allowed
//   scrub input   → interrupts playback and writes ?step= to the URL
import { chromium } from 'playwright';

const url = process.argv[2] ?? 'http://localhost:5173/d4b/';
const browser = await chromium.launch();
const readout = (page) => page.evaluate(() => ({
  step: document.querySelector('[data-out="step"]').textContent,
  button: document.querySelector('[data-play-label]').textContent,
  url: location.search,
}));
async function open(reducedMotion, query = '') {
  const ctx = await browser.newContext({ reducedMotion, viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  await page.goto(url + query);
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
  return { ctx, page };
}

const results = {};
{
  const { ctx, page } = await open('reduce');
  await page.waitForTimeout(1500);
  const r = await readout(page);
  results.reduce_final_state = r.step === '40 / 40' && r.button === 'Replay';
  await ctx.close();
}
{
  const { ctx, page } = await open('no-preference');
  await page.waitForTimeout(3000);
  const r = await readout(page);
  const s = parseInt(r.step, 10);
  results.motion_autoplays = s > 0 && s < 40 && r.button === 'Pause';
  // scrubbing interrupts playback and deep-links the step
  await page.locator('[data-scrub]').fill('20');
  await page.waitForTimeout(400);
  const after = await readout(page);
  results.scrub_interrupts = after.step === '20 / 40' && after.button !== 'Pause' && after.url.includes('step=20');
  await ctx.close();
}
{
  const { ctx, page } = await open('no-preference', '?step=12');
  await page.waitForTimeout(1500);
  const r = await readout(page);
  results.deep_link_still = r.step === '12 / 40' && r.button === 'Replay';
  await ctx.close();
}
await browser.close();
console.log(results);
process.exit(Object.values(results).every(Boolean) ? 0 : 1);
