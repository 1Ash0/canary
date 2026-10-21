// Site QA across the chapter pages (/, /lab/, /compare/, /results/): final states with reduced motion
// at three widths, the pinned comparison scrubbing in order, every entry animation settling, and the
// lazy-loading check (home ships only the hero; each chapter fetches its own sections, and only on
// approach). Needs the dev server: npm --prefix web run dev.
// Usage: node design/scripts/check-landing.mjs [base-url]
import { mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { chromium } from 'playwright';
import { mountAll } from './lib/mount.mjs';
import { DESIGN } from './lib/palettes.mjs';

const BASE = process.argv[2] ?? 'http://localhost:3000';
const out = join(DESIGN, 'web-qa', 'landing');
mkdirSync(out, { recursive: true });
const browser = await chromium.launch();
const failures = [];
const check = (ok, msg) => { if (!ok) failures.push(msg); console.log(`${ok ? 'ok  ' : 'FAIL'} ${msg}`); };
const PAGES = ['/', '/lab/', '/compare/', '/results/'];

async function open(path, width, height, reducedMotion) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(BASE + path, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true', null, { timeout: 8000 });
  await page.evaluate(() => document.fonts.ready);
  await mountAll(page);
  return { page, errors };
}

// 0. lazy loading: home fetches no section module at all; a chapter fetches its own, after scrolling
{
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const scripts = [];
  page.on('request', (r) => { if (r.resourceType() === 'script') scripts.push(r.url()); });
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  const sectionMod = /\/(lab|compare|consequence|results|survival-mini)[.-]/;
  check(!scripts.some((u) => sectionMod.test(u)), 'home: no section module fetched');
  for (const [path, mods, below] of [['/lab/', ['lab', 'survival-mini'], ['survival-mini']],
    // on /compare/ the consequence sits within half a screen of the comparison before it is drawn
    ['/compare/', ['compare', 'consequence'], []], ['/results/', ['results'], []]]) {
    scripts.length = 0;
    await page.goto(BASE + path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(800);
    const early = below.filter((n) => scripts.some((u) => new RegExp(`/${n}[.-]`).test(u)));
    check(early.length === 0, `${path}: nothing below the fold fetched before scrolling (${early.join(', ') || 'none'})`);
    await mountAll(page);
    const missing = mods.filter((n) => !scripts.some((u) => new RegExp(`/${n}[.-]`).test(u)));
    check(missing.length === 0, `${path}: its sections fetched after scrolling (${missing.join(', ') || 'all'})`);
  }
  await page.close();
}

// 1. reduced motion: every page in its final state, nothing pinned, no sideways scroll
for (const [w, h] of [[1440, 900], [768, 1024], [390, 844]]) {
  for (const path of PAGES) {
    const { page, errors } = await open(path, w, h, 'reduce');
    await page.waitForTimeout(300);
    const name = path === '/' ? 'home' : path.replaceAll('/', '');
    await page.screenshot({ path: join(out, `final-${name}-${w}.png`), fullPage: true });
    const s = await page.evaluate(() => ({
      pinned: !!document.querySelector('.pin-spacer'),
      hidden: [...document.querySelectorAll('[data-rise], [data-cons-col], [data-res-row], [data-verdict]')]
        .filter((e) => getComputedStyle(e).opacity !== '1' || getComputedStyle(e).visibility === 'hidden').length,
      overflow: document.documentElement.scrollWidth > innerWidth,
      still: document.querySelector('[data-compare]')?.classList.contains('is-still') ?? true,
    }));
    check(!s.pinned && s.still, `${name} ${w}px reduce: nothing pinned`);
    check(s.hidden === 0, `${name} ${w}px reduce: no element left hidden (${s.hidden})`);
    check(!s.overflow, `${name} ${w}px reduce: no sideways scroll`);
    check(errors.length === 0, `${name} ${w}px reduce: no console errors ${errors.join(' | ')}`);
    await page.close();
  }
}

// 2. motion: the comparison pins and scrubs with its notes in order; entries settle visible
{
  const { page, errors } = await open('/compare/', 1440, 900, 'no-preference');
  const top = await page.evaluate(() => document.querySelector('[data-compare]').getBoundingClientRect().top + scrollY);
  check(await page.evaluate(() => !!document.querySelector('.pin-spacer')), 'compare 1440px motion: comparison is pinned');
  const notes = [];
  for (const [i, p] of [0, 0.2, 0.4, 0.55, 0.7, 0.85, 1].entries()) {
    await page.evaluate((y) => window.scrollTo(0, y), top + p * 900 * 1.6);
    await page.waitForTimeout(700);
    notes.push(await page.evaluate(() => [...document.querySelectorAll('[data-note]')].findIndex((e) => e.classList.contains('is-current'))));
    await page.screenshot({ path: join(out, `compare-${String(i).padStart(2, '0')}.png`) });
  }
  check(notes[0] === 0 && notes.at(-1) === 2 && notes.every((n, i) => i === 0 || n >= notes[i - 1]),
    `compare 1440px motion: notes advance in order as you scroll (${notes.join(',')})`);
  check(errors.length === 0, `compare 1440px motion: no console errors ${errors.join(' | ')}`);
  await page.close();
}
for (const [path, sel] of [['/compare/', '#consequence'], ['/results/', '#result'], ['/lab/', '#policies']]) {
  const { page, errors } = await open(path, 1440, 900, 'no-preference');
  // walk through the section so every block crosses its trigger, then let the longest animation end
  const blocks = await page.evaluate((s) => document.querySelectorAll(`${s} [data-res-model], ${s}`).length, sel);
  for (let b = 0; b < blocks; b++) {
    await page.evaluate(([s, i]) => [...document.querySelectorAll(`${s} [data-res-model], ${s}`)][i].scrollIntoView({ block: 'center' }), [sel, b]);
    await page.waitForTimeout(400);
  }
  await page.evaluate((s) => document.querySelector(s).scrollIntoView({ block: 'start' }), sel);
  await page.waitForTimeout(3200);
  const hidden = await page.evaluate((s) => [...document.querySelectorAll(`${s} [data-cons-col], ${s} [data-res-row], ${s} [data-verdict], ${s} [data-fill]`)]
    .filter((e) => getComputedStyle(e).opacity !== '1').length, sel);
  check(hidden === 0, `${path}${sel} 1440px motion: settles fully visible after entering (${hidden} hidden)`);
  check(errors.length === 0, `${path}${sel}: no console errors ${errors.join(' | ')}`);
  await page.screenshot({ path: join(out, `enter-${sel.slice(1)}.png`) });
  await page.close();
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failure(s)` : '\nall landing checks passed');
process.exit(failures.length ? 1 : 0);
