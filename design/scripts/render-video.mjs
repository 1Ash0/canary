// Render the Canary video (D5, ADR-016): a static server over the repo, Playwright calls
// window.seek(t) for every frame, ffmpeg encodes. Deterministic: the same inputs give the same
// frames (checked with --check, which hashes one frame from two separate page loads).
// Usage: node design/scripts/render-video.mjs [--format portrait|square|safe] [--fps 30] [--check]
//        [--sheet] -> design/video/out/canary-<format>.mp4 (+ contact sheet)
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, extname, resolve } from 'node:path';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';

const ROOT = resolve(import.meta.dirname, '..', '..');
const arg = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
const FORMAT = arg('format', 'portrait');
const FPS = Number(arg('fps', '30'));
const H = FORMAT === 'square' ? 1080 : 1350;
const OUT = join(ROOT, 'design', 'video', 'out');
mkdirSync(OUT, { recursive: true });

const TYPES = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.html': 'text/html', '.json': 'application/json', '.woff2': 'font/woff2' };
const server = createServer((req, res) => {
  const p = join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !existsSync(p)) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { 'content-type': TYPES[extname(p)] ?? 'application/octet-stream' });
  res.end(readFileSync(p));
}).listen(4175);
const URL_ = `http://localhost:4175/design/video/index.html?format=${FORMAT}`;

const browser = await chromium.launch();
async function open() {
  const page = await browser.newPage({ viewport: { width: 1080, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(URL_, { waitUntil: 'networkidle' });
  await page.evaluate(() => window.__ready);
  if (errors.length) throw new Error(errors.join('\n'));
  return page;
}
const frame = async (page, t) => { await page.evaluate((x) => window.seek(x), t); return page.screenshot({ type: 'png' }); };

if (process.argv.includes('--check')) {
  const hashes = [];
  for (let i = 0; i < 2; i++) {
    const page = await open();
    await frame(page, 3.1);  // visit another time first: seek must not depend on history
    hashes.push(createHash('sha256').update(await frame(page, 11.37)).digest('hex'));
    await page.close();
  }
  console.log(hashes[0] === hashes[1] ? `deterministic: ${hashes[0].slice(0, 16)}` : `NOT deterministic: ${hashes.join(' ')}`);
  await browser.close(); server.close();
  process.exit(hashes[0] === hashes[1] ? 0 : 1);
}

const page = await open();
const duration = await page.evaluate(() => window.__duration);
// subtitles from the same caption beats the frame shows (LinkedIn accepts an .srt upload)
const caps = await page.evaluate(() => window.__captions);
const ts = (x) => { const ms = Math.round(x * 1000); const p = (n, w = 2) => String(n).padStart(w, '0');
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`; };
const plain = (s) => s.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
writeFileSync(join(OUT, `canary-${FORMAT}.srt`),
  caps.map((c, i) => [i + 1, `${ts(c.from)} --> ${ts(c.to)}`, plain(c.text), ''].join('\n')).join('\n'));
const frames = Math.ceil(duration * FPS);
const mp4 = join(OUT, `canary-${FORMAT}.mp4`);
// a silent stereo track: some players and feeds handle video-only files badly
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest',
  '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '17', '-preset', 'slow', '-movflags', '+faststart',
  '-c:a', 'aac', '-b:a', '96k', mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
for (let i = 0; i < frames; i++) {
  const png = await frame(page, i / FPS);
  if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once('drain', r));
  if (i % (FPS * 5) === 0) console.log(`frame ${i}/${frames}`);
}
ff.stdin.end();
await new Promise((r) => ff.on('close', r));
console.log(`wrote ${mp4} (${duration.toFixed(1)} s, ${frames} frames)`);

if (process.argv.includes('--sheet')) {
  // contact sheet: one frame per second, for the critique loop (VIDEO_RULES D7)
  const sheet = join(OUT, `sheet-${FORMAT}.png`);
  await new Promise((r) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-i', mp4, '-vf',
    `fps=1,scale=270:-1,tile=8x${Math.ceil(duration / 8)}`, '-frames:v', '1', sheet], { stdio: 'inherit' }).on('close', r));
  console.log(`wrote ${sheet}`);
}
await browser.close(); server.close();
