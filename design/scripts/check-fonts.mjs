// Verifies the self-hosted woff2 fonts load from disk, with all remote font hosts blocked.
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';

const browser = await chromium.launch();
const page = await browser.newPage();
const remote = [];
await page.route(/^https?:\/\//, (route) => { remote.push(route.request().url()); return route.abort(); });
await page.goto(pathToFileURL(join(DESIGN, 'd2', 'fontcheck.html')).href);
await page.evaluate(() => document.fonts.ready);
const result = await page.evaluate(() => ({
  sans: document.fonts.check('500 32px "Instrument Sans"'),
  mono: document.fonts.check('400 13px "JetBrains Mono"'),
  faces: [...document.fonts].map((f) => `${f.family} ${f.status}`),
}));
await browser.close();
console.log(JSON.stringify({ ...result, remoteRequests: remote }, null, 2));
const ok = result.faces.length === 2 && result.faces.every((f) => f.endsWith('loaded')) && remote.length === 0;
process.exit(ok ? 0 : 1);
