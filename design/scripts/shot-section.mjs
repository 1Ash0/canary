// Screenshot one section of a page: node design/scripts/shot-section.mjs <url> <selector> <out.png> [width] [height] [reduce]
import { chromium } from 'playwright';
import { mountAll } from './lib/mount.mjs';
const [, , url, sel, out, w = '1440', h = '900', rm = 'no-preference'] = process.argv;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: +w, height: +h }, reducedMotion: rm });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForFunction(() => document.documentElement.dataset.ready === 'true', null, { timeout: 10000 });
await mountAll(page);
await page.evaluate((s) => document.querySelector(s).scrollIntoView({ block: 'start' }), sel);
await page.waitForTimeout(1500);
await page.locator(sel).screenshot({ path: out });
await browser.close();
console.log(out, errors.length ? 'ERRORS ' + errors.join(' | ') : 'ok');
