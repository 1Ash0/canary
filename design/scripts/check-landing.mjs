// Landing page QA (D8): final states with reduced motion at three widths, a frame strip of the
// pinned comparison while scrolling, and the two-sided reduced-motion check (reduce -> final state,
// no pin; no-preference -> pinned and scrubbing). Needs the dev server: npm --prefix web run dev.
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

async function open(width, height, reducedMotion) {
  const page = await browser.newPage({ viewport: { width, height }, reducedMotion });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true', null, { timeout: 8000 });
  await page.evaluate(() => document.fonts.ready);
  await mountAll(page);
  return { page, errors };
}

// 0. lazy sections: none of their code is fetched before scrolling, all of it after
{
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const scripts = [];
  page.on('request', (r) => { if (r.resourceType() === 'script') scripts.push(r.url()); });
  await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
  await page.waitForTimeout(800);
  // the Lab sits right under the hero, so it may load at once; nothing further down may
  const lazy = /\/(compare|consequence|results|survival-mini)[.-]/;
  check(!scripts.some((u) => lazy.test(u)), 'first view: no module below the Lab fetched before scrolling');
  await mountAll(page);
  const names = ['lab', 'compare', 'consequence', 'results', 'survival-mini'];
  const missing = names.filter((n) => !scripts.some((u) => new RegExp(`/${n}[.-]`).test(u)));
  check(missing.length === 0, `after scrolling: every section module fetched (${missing.join(', ') || 'all'})`);
  await page.close();
}

// 1. reduced motion: every section in its final state, nothing pinned
for (const [w, h] of [[1440, 900], [768, 1024], [390, 844]]) {
  const { page, errors } = await open(w, h, 'reduce');
  await page.waitForTimeout(300);
  await page.screenshot({ path: join(out, `final-${w}.png`), fullPage: true });
  const s = await page.evaluate(() => ({
    pinned: !!document.querySelector('.pin-spacer'),
    hidden: [...document.querySelectorAll('[data-rise], [data-cons-col], [data-res-row], [data-verdict]')]
      .filter((e) => getComputedStyle(e).opacity !== '1' || getComputedStyle(e).visibility === 'hidden').length,
    overflow: document.documentElement.scrollWidth > innerWidth,
    still: document.querySelector('[data-compare]').classList.contains('is-still'),
  }));
  check(!s.pinned && s.still, `${w}px reduce: comparison is static, not pinned`);
  check(s.hidden === 0, `${w}px reduce: no element left hidden (${s.hidden})`);
  check(!s.overflow, `${w}px reduce: no sideways scroll`);
  check(errors.length === 0, `${w}px reduce: no console errors ${errors.join(' | ')}`);
  await page.close();
}

// 2. motion: the comparison pins and scrubs; frame strip through the seam
{
  const { page, errors } = await open(1440, 900, 'no-preference');
  const top = await page.evaluate(() => document.querySelector('[data-compare]').getBoundingClientRect().top + scrollY);
  const pinned = await page.evaluate(() => !!document.querySelector('.pin-spacer'));
  check(pinned, '1440px motion: comparison is pinned');
  const frames = [0, 0.2, 0.4, 0.55, 0.7, 0.85, 1];
  const notes = [];
  for (const [i, p] of frames.entries()) {
    await page.evaluate((y) => window.scrollTo(0, y), top + p * 900 * 1.6);
    await page.waitForTimeout(700);
    notes.push(await page.evaluate(() => [...document.querySelectorAll('[data-note]')].findIndex((e) => e.classList.contains('is-current'))));
    await page.screenshot({ path: join(out, `compare-${String(i).padStart(2, '0')}.png`) });
  }
  check(notes[0] === 0 && notes.at(-1) === 2 && notes.every((n, i) => i === 0 || n >= notes[i - 1]),
    `1440px motion: notes advance in order as you scroll (${notes.join(',')})`);
  // the consequence and results animate in when scrolled to, then settle fully visible
  for (const sel of ['#consequence', '#result', '#policies']) {
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
    check(hidden === 0, `1440px motion: ${sel} settles fully visible after entering (${hidden} hidden)`);
    await page.screenshot({ path: join(out, `enter-${sel.slice(1)}.png`) });
  }
  check(errors.length === 0, `1440px motion: no console errors ${errors.join(' | ')}`);
  await page.close();
}

await browser.close();
console.log(failures.length ? `\n${failures.length} failure(s)` : '\nall landing checks passed');
process.exit(failures.length ? 1 : 0);
