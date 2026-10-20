// Motion QA for a page exposing window.__seek(t) / window.__duration (served by the canary-design Vite server).
// Writes deterministic frames → contact sheet + seam strip (ffmpeg tile), and a real-time recording (mp4).
// node scripts/motion-review.mjs [url] [outDir]
import { mkdirSync, rmSync, readdirSync, renameSync } from 'node:fs';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';
import { DESIGN } from './lib/palettes.mjs';

const url = process.argv[2] ?? 'http://localhost:5173/d4b/';
const out = join(DESIGN, process.argv[3] ?? 'd4b/review');
const [vw, vh] = (process.argv[4] ?? '1280x720').split('x').map(Number);
const frames = join(out, 'frames');
rmSync(frames, { recursive: true, force: true });
mkdirSync(frames, { recursive: true });

const browser = await chromium.launch();

// 1. deterministic frames of the player
const page = await browser.newPage({ viewport: { width: vw, height: vh } });
await page.goto(url);
await page.waitForFunction(() => document.documentElement.dataset.ready === 'true');
await page.evaluate(() => document.fonts.ready);
const duration = await page.evaluate(() => window.__duration);
const player = page.locator('.player');
async function grab(t, name) {
  await page.evaluate((x) => window.__seek(x), t);
  await player.screenshot({ path: join(frames, name) });
}
let n = 0;
for (let t = 0; t <= duration + 1e-6; t += 0.5) await grab(t, `sheet_${String(n++).padStart(3, '0')}.png`);
// seam strip: 12 frames across the seam and the collapse (times from the schedule)
const { seam } = await page.evaluate(() => ({ seam: window.__schedule?.seam }));
const s0 = (seam ?? duration * 0.6) - 0.2;
for (let i = 0; i < 12; i++) await grab(s0 + i * 0.12, `strip_${String(i).padStart(2, '0')}.png`);
await page.close();

const ff = (args) => execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...args]);
ff(['-framerate', '1', '-i', join(frames, 'sheet_%03d.png'), '-vf', 'scale=420:-1,tile=6x5:padding=8:color=0x0E0D0B', '-frames:v', '1', join(out, 'contact.png')]);
ff(['-framerate', '1', '-i', join(frames, 'strip_%02d.png'), '-vf', 'scale=320:-1,tile=4x3:padding=8:color=0x0E0D0B', '-frames:v', '1', join(out, 'seam-strip.png')]);

// 2. real-time recording of the actual GSAP playback, as a visitor sees it
const ctx = await browser.newContext({ viewport: { width: vw, height: vh }, recordVideo: { dir: out, size: { width: vw, height: vh } } });
const rec = await ctx.newPage();
await rec.goto(url);
await rec.waitForTimeout((duration + 2.5) * 1000);
await ctx.close();
const webm = readdirSync(out).find((f) => f.endsWith('.webm'));
renameSync(join(out, webm), join(out, 'playthrough.webm'));
ff(['-i', join(out, 'playthrough.webm'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', join(out, 'playthrough.mp4')]);
rmSync(join(out, 'playthrough.webm'));
await browser.close();
console.log(`duration ${duration.toFixed(2)}s · ${n} sheet frames · wrote contact.png, seam-strip.png, playthrough.mp4 in ${out}`);
