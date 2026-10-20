// Serve a local directory to Playwright through request routing, so module scripts load
// over http (Chromium blocks ES modules from file://). No server process, no network.
import { readFileSync, existsSync } from 'node:fs';
import { join, extname, normalize } from 'node:path';

const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2' };
export const ORIGIN = 'http://local.test';

export async function serveDir(page, dir) {
  await page.route(`${ORIGIN}/**`, (route) => {
    const path = decodeURIComponent(new URL(route.request().url()).pathname);
    const file = normalize(join(dir, path.endsWith('/') ? path + 'index.html' : path));
    if (!file.startsWith(normalize(dir)) || !existsSync(file)) return route.fulfill({ status: 404, body: 'not found' });
    return route.fulfill({ status: 200, contentType: TYPES[extname(file)] ?? 'application/octet-stream', body: readFileSync(file) });
  });
}
