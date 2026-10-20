// Hero rules from SITE_RULES §2, measured: headline ≤ 2 lines at every width, and at 1280×720 the
// claim, primary action and the whole player (readout to controls) sit inside the first view.
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';
import { serveDir, ORIGIN } from './lib/serve.mjs';

const page_ = process.argv[2] ?? 'd4/mockup.html';
const browser = await chromium.launch();
const results = [];
for (const [w, h] of [[1440, 900], [1280, 720], [768, 1024], [390, 844]]) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  await serveDir(page, DESIGN);
  await page.goto(`${ORIGIN}/${page_}`);
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
  await page.evaluate(() => document.fonts.ready);
  const m = await page.evaluate(() => {
    const h1 = document.querySelector('h1');
    const lh = parseFloat(getComputedStyle(h1).lineHeight);
    const bottom = (sel) => document.querySelector(sel).getBoundingClientRect().bottom;
    return { lines: Math.round(h1.getBoundingClientRect().height / lh), ctaBottom: bottom('.btn'), playerBottom: bottom('.controls'), overflowX: document.documentElement.scrollWidth > innerWidth };
  });
  const firstView = w === 1280 ? m.ctaBottom <= h && m.playerBottom <= h : null;
  results.push({ viewport: `${w}x${h}`, ...m, headlineOk: m.lines <= 2, firstView });
  await page.close();
}
await browser.close();
console.table(results.map((r) => ({ viewport: r.viewport, lines: r.lines, headlineOk: r.headlineOk, firstView: r.firstView, overflowX: r.overflowX, playerBottom: Math.round(r.playerBottom) })));
process.exit(results.every((r) => r.headlineOk && r.firstView !== false && !r.overflowX) ? 0 : 1);
