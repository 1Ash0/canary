// M1 exit test for the recorder: open a run, scrub, step by keyboard, copy a permalink to one step,
// and open that permalink fresh. node scripts/check-recorder.mjs [baseUrl]
import { chromium } from 'playwright';

const base = process.argv[2] ?? 'http://localhost:3000';
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, permissions: ['clipboard-read', 'clipboard-write'] });
const page = await ctx.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

const title = () => page.locator('[data-detail-title]').textContent();
const step = () => new URL(page.url()).searchParams.get('step');
const results = {};

await page.goto(`${base}/run/?run=synthetic-001`);
await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
results.opens_before_compaction = (await title()) === 'Step 31 of 40';

await page.keyboard.press('ArrowLeft');
await page.keyboard.press('ArrowLeft');
results.arrows_step_back = (await title()) === 'Step 29 of 40' && step() === '29';

await page.keyboard.press('c');
results.c_jumps_after_compaction = (await title()) === 'Step 32 of 40' && step() === '32';
const facts = await page.locator('[data-facts]').innerText();
results.after_compaction_shows_fates = /C1[\s\S]*kept/.test(facts) && /C2[\s\S]*gone/.test(facts) && /C3[\s\S]*gone/.test(facts);

await page.keyboard.press('Home');
results.home_goes_to_first = (await title()) === 'Step 1 of 40' && /No facts planted yet/.test(await page.locator('[data-facts]').innerText());
await page.keyboard.press('End');
results.end_goes_to_last = (await title()) === 'Step 40 of 40';

await page.locator('[data-scrub]').fill('14');
results.scrubber_steps = (await title()) === 'Step 14 of 40' && step() === '14';
results.planted_by_step_14 = (await page.locator('[data-facts] li').count()) === 3;

await page.getByRole('button', { name: 'Copy link to this step' }).click();
const link = await page.evaluate(() => navigator.clipboard.readText());
results.permalink_points_at_the_step = new URL(link).searchParams.get('step') === '14' && new URL(link).searchParams.get('run') === 'synthetic-001';

const fresh = await ctx.newPage();
await fresh.goto(link);
await fresh.waitForFunction(() => document.documentElement.dataset.ready === 'true');
results.permalink_opens_the_same_moment = (await fresh.locator('[data-detail-title]').textContent()) === 'Step 14 of 40';

results.no_console_errors = errors.length === 0;
await browser.close();
console.log(results, errors);
process.exit(Object.values(results).every(Boolean) ? 0 : 1);
