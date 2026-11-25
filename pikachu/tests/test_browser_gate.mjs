import assert from 'node:assert/strict';
import { chromium } from '../../src/mjswan/template/node_modules/playwright/index.mjs';

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
const page = await browser.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
try {
  const base = process.env.PIKACHU_TEST_URL || 'http://127.0.0.1:8765/';
  await page.goto(`${base}?project=pikachu_v0375&scene=gated_posture_transition&pikachu_debug=1`);
  await page.waitForFunction(() => window.__pikachuGate, {timeout: 30000});
  const speed = page.locator('input[inputmode="decimal"]').first();
  await speed.fill('0.1'); await speed.press('Tab');
  await page.waitForTimeout(1200);
  await page.locator('#posture\\:biped').uncheck();
  await page.waitForFunction(() => window.__pikachuGate?.phase === 0, {timeout: 30000});
  const down = await page.evaluate(() => window.__pikachuGate);
  assert.equal(await speed.inputValue(), '0');
  assert.ok(down.rootPos[2] > 0.17, `crawl root height: ${down.rootPos[2]}`);
  await page.locator('#posture\\:biped').check();
  await page.waitForFunction(() => window.__pikachuGate?.phase === 1, {timeout: 30000});
  await page.waitForTimeout(500);
  const up = await page.evaluate(() => window.__pikachuGate);
  const [w, x, y, z] = up.rootQuat;
  const upright = 1 - 2 * (x*x + y*y);
  assert.ok(up.rootPos[2] > 0.19, `biped root height: ${up.rootPos[2]}`);
  assert.ok(upright > 0.8, `biped upright projection: ${upright}, quat ${[w,x,y,z]}`);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({downHeight: down.rootPos[2], upHeight: up.rootPos[2], upright, errors}));
} finally {
  await browser.close();
}
