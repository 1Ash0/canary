// The landing page mounts each section when it comes near the viewport (main-home.js). QA that
// inspects final states first walks the page so every section mounts, then returns to the top.
// Pages without lazy sections (no <html data-sections>) are left as they are.
export async function mountAll(page) {
  const total = await page.evaluate(() => Number(document.documentElement.dataset.sections ?? 0));
  if (!total) return;
  // the page grows as sections mount, so measure again at every step
  for (let y = 0; y <= await page.evaluate(() => document.documentElement.scrollHeight); y += 500) {
    await page.evaluate((top) => window.scrollTo(0, top), y);
    await page.waitForTimeout(60);
  }
  await page.waitForFunction(() => document.documentElement.dataset.mounted === document.documentElement.dataset.sections,
    null, { timeout: 10000 });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(200);
}
