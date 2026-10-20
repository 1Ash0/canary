// Site QA against a running server (default http://localhost:3000): for every page and width it checks
// console errors, horizontal overflow, headline length and (home, 1280x720) the first-view rule, then
// writes screenshots to web-qa/. node scripts/check-site.mjs [baseUrl]
import { mountAll } from './lib/mount.mjs';
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';

const base = process.argv[2] ?? 'http://localhost:3000';
const out = join(DESIGN, 'web-qa');
mkdirSync(out, { recursive: true });
const pages = [['home', '/'], ['run', '/run/?run=synthetic-001&step=31'], ['recorded', '/run/?run=exp001-s19-nvidia&step=20'], ['survival', '/survival/'], ['about', '/about/']];
const widths = [[1440, 900], [1280, 720], [768, 1024], [390, 844]];

const browser = await chromium.launch();
const rows = [];
for (const [name, path] of pages) {
  for (const [w, h] of widths) {
    const page = await browser.newPage({ viewport: { width: w, height: h } });
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('requestfailed', (r) => errors.push(`failed: ${r.url()}`));
    await page.goto(base + path, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
    await page.evaluate(() => document.fonts.ready);
    await mountAll(page);
    if (name === 'home') await page.evaluate(() => window.__seek(window.__duration)); // settled final state
    await page.waitForTimeout(200);
    const m = await page.evaluate(() => {
      const h = document.querySelector('h1, h2');
      const lh = parseFloat(getComputedStyle(h).lineHeight);
      const bottom = (sel) => document.querySelector(sel)?.getBoundingClientRect().bottom ?? null;
      return {
        lines: Math.round(h.getBoundingClientRect().height / lh),
        overflowX: document.documentElement.scrollWidth > innerWidth,
        ctaBottom: bottom('.btn'), controlsBottom: bottom('.controls'),
        labelVisible: [...document.querySelectorAll('.tag')].some((t) => /synthetic fixture|mock data|deterministic|simulated/.test(t.textContent)) || /synthetic fixture/.test(document.body.innerText),
      };
    });
    const firstView = name === 'home' && w === 1280 ? m.ctaBottom <= h && m.controlsBottom <= h : null;
    await page.screenshot({ path: join(out, `${name}-${w}.png`), fullPage: !(name === 'home' && w === 1280) });
    rows.push({ page: name, width: w, lines: m.lines, overflowX: m.overflowX, firstView, label: m.labelVisible || name === 'about', errors: errors.length });
    if (errors.length) console.log(name, w, errors);
    await page.close();
  }
}
await browser.close();
console.table(rows);
const bad = rows.filter((r) => r.errors || r.overflowX || r.lines > 2 || r.firstView === false || !r.label);
process.exit(bad.length ? 1 : 0);
