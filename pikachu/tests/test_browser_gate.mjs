import assert from 'node:assert/strict';
import { chromium } from '../../src/mjswan/template/node_modules/playwright/index.mjs';

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage();
// Simulate a stale pre-GateTwist module cached at the old unversioned URL.
await page.route('**/assets/plugins.js', route => route.fulfill({
  contentType: 'application/javascript', body: 'export const observations = {};',
}));
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
const pluginRequests = [];
page.on('request', request => {
  if (/\/assets\/plugins[^/]*\.js/.test(new URL(request.url()).pathname)) pluginRequests.push(request.url());
});
try {
  const base = process.env.PIKACHU_TEST_URL || 'http://127.0.0.1:8765/';
  await page.goto(`${base}?pikachu_debug=1`);
  await page.waitForFunction(() => window.__pikachuGate, {timeout: 30000});
  assert.ok(pluginRequests.some(url => /plugins-[a-f0-9]{16}\.js/.test(url)), 'expected versioned plugin');
  const velocityBounds = async () => page.locator('[role="slider"]').evaluateAll(
    sliders => sliders.slice(0, 3).map(slider => [
      Number(slider.getAttribute('aria-valuemin')), Number(slider.getAttribute('aria-valuemax')),
    ]),
  );
  assert.deepEqual(await velocityBounds(), [[-.6, .8], [-.5, .5], [-.5, .5]]);
  const speed = page.locator('input[inputmode="decimal"]').first();
  await speed.fill('0.1'); await speed.press('Tab');
  await page.waitForTimeout(1200);
  const posture = page.getByRole('button', {name: '切换四足'});
  await posture.click();
  await page.waitForFunction(() => document.querySelector('button[aria-label="切换四足"]')?.disabled);
  await page.waitForFunction(() => /切换四足 [1-9]\d?%/.test(document.querySelector('button[aria-label="切换四足"]')?.textContent || ''));
  await page.waitForFunction(() => window.__pikachuGate?.phase === 0, {timeout: 30000});
  const down = await page.evaluate(() => window.__pikachuGate);
  assert.deepEqual(await velocityBounds(), [[-.3, .3], [-.3, .3], [-.3, .3]]);
  assert.equal(await speed.inputValue(), '0');
  assert.ok(down.rootPos[2] > 0.17, `crawl root height: ${down.rootPos[2]}`);
  await page.getByRole('button', {name: '切换双足'}).click();
  await page.waitForFunction(() => document.querySelector('button[aria-label="切换双足"]')?.disabled);
  await page.waitForFunction(() => window.__pikachuGate?.phase === 1, {timeout: 30000});
  await page.waitForTimeout(500);
  const up = await page.evaluate(() => window.__pikachuGate);
  assert.deepEqual(await velocityBounds(), [[-.6, .8], [-.5, .5], [-.5, .5]]);
  const [w, x, y, z] = up.rootQuat;
  const upright = 1 - 2 * (x*x + y*y);
  assert.ok(up.rootPos[2] > 0.19, `biped root height: ${up.rootPos[2]}`);
  assert.ok(upright > 0.8, `biped upright projection: ${upright}, quat ${[w,x,y,z]}`);
  await page.getByRole('button', {name: '切换四足'}).click();
  await page.waitForFunction(() => document.querySelector('button[aria-label="切换四足"]')?.disabled);
  await page.keyboard.press('r');
  await page.waitForFunction(() => {
    const button = document.querySelector('button[aria-label="切换四足"]');
    return button && !button.disabled;
  });
  await page.goto(`${base}?scene=quadruped_crawling`);
  await page.waitForFunction(() => document.querySelectorAll('[role="slider"]').length >= 3, {timeout: 30000});
  assert.deepEqual(await velocityBounds(), [[-.3, .3], [-.3, .3], [-.3, .3]]);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({downHeight: down.rootPos[2], upHeight: up.rootPos[2], upright, errors}));
} finally {
  await browser.close();
}
