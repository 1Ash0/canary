// Screenshot a local HTML page: node scripts/shoot.mjs <file.html> <out.png> [--width 1440] [--height 900] [--full] [--serve]
// --serve routes design/ over http://local.test so ES modules and fetch() work. Waits for web fonts and,
// if the page sets <html data-ready>, for that. window.__tnum, if set, is saved as <out>.tnum.json.
import { writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';
import { serveDir, ORIGIN } from './lib/serve.mjs';

const [, , input, output, ...rest] = process.argv;
const opt = (k, d) => (rest.includes(`--${k}`) ? Number(rest[rest.indexOf(`--${k}`) + 1]) : d);
const width = opt('width', 1440), height = opt('height', 900), full = rest.includes('--full'), serve = rest.includes('--serve');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
let url = pathToFileURL(resolve(input)).href;
if (serve) {
  await serveDir(page, DESIGN);
  url = `${ORIGIN}/${relative(DESIGN, resolve(input)).replace(/\\/g, '/')}`;
}
await page.goto(url, { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
if (await page.evaluate(() => 'ready' in document.documentElement.dataset || !!document.querySelector('script[type=module]'))) {
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true', null, { timeout: 5000 }).catch(() => errors.push('page never set data-ready'));
}
await page.waitForTimeout(150);
await page.screenshot({ path: output, fullPage: full });
const tnum = await page.evaluate(() => window.__tnum ?? null);
if (tnum) writeFileSync(output.replace(/\.png$/, '.tnum.json'), JSON.stringify(tnum, null, 2));
await browser.close();
console.log(`${output} (${width}x${height}${full ? ', full page' : ''})${errors.length ? ' ERRORS: ' + errors.join(' | ') : ''}`);
process.exit(errors.length ? 1 : 0);
