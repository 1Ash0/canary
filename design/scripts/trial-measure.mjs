// Measures the GSAP trial build (JS size raw/gzip) and checks reduced-motion behaviour both ways.
// Run after `npx vite build trial`. Writes trial/RESULT.json.
import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { gzipSync } from 'node:zlib';
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';
import { serveDir, ORIGIN } from './lib/serve.mjs';

const dist = join(DESIGN, 'trial', 'dist');
const assets = readdirSync(join(dist, 'assets')).filter((f) => f.endsWith('.js'));
const js = assets.map((f) => {
  const buf = readFileSync(join(dist, 'assets', f));
  return { file: f, bytes: buf.length, gzip: gzipSync(buf, { level: 9 }).length };
});
const total = js.reduce((a, f) => ({ bytes: a.bytes + f.bytes, gzip: a.gzip + f.gzip }), { bytes: 0, gzip: 0 });

const browser = await chromium.launch();
async function probe(reducedMotion) {
  const ctx = await browser.newContext({ reducedMotion, viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  await serveDir(page, dist);
  await page.goto(`${ORIGIN}/index.html`);
  await page.waitForFunction(() => window.__trial);
  const state = await page.evaluate(() => {
    const t = getComputedStyle(document.querySelector('#title'));
    const b = getComputedStyle(document.querySelector('#bar'));
    return { ...window.__trial, titleOpacity: +t.opacity, titleTransform: t.transform, barTransform: b.transform };
  });
  await ctx.close();
  return state;
}
const reduce = await probe('reduce');
const motion = await probe('no-preference');
await browser.close();

// Two-sided: reduced motion must show the final state with no triggers; motion must set up the animation.
const checks = {
  reduce_final_state: reduce.mode === 'reduce' && reduce.triggers === 0 && reduce.titleOpacity === 1 && reduce.barTransform === 'none',
  motion_animates: motion.mode === 'motion' && motion.triggers === 1 && motion.titleOpacity < 1,
};
const result = { date: new Date().toISOString().slice(0, 10), js, total, reduce, motion, checks };
writeFileSync(join(DESIGN, 'trial', 'RESULT.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify({ total, checks }, null, 2));
process.exit(Object.values(checks).every(Boolean) ? 0 : 1);
