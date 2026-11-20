'use strict';
// Test harness of the tour page: one headless Chrome per test file, one fresh page per test.
//
//   const { suite, assert } = require('./lib/harness');
//   const { test } = suite(__filename, { preset: 'desktop' });
//   test('the page opens', async (s, t) => { await s.open(); ... });
//
// What it takes care of
//   * Chrome: TOUR_CHROME (default /usr/bin/google-chrome), flags from TOUR_CHROME_ARGS (default the
//     Vulkan set; use '--use-angle=gl-egl' for the integrated GPU), headless 'new', and a throwaway
//     page that creates a WebGL 2 context before the tour is loaded (without it the first launch after
//     an idle pause can lose the tour's context).
//   * The page: TOUR_BASE (default http://127.0.0.1:8765/). If TOUR_BASE is not set and nothing answers
//     there, a `python3 -m http.server` on the repository root is started on a free port for the run
//     and stopped afterwards.
//   * Every test gets a session `s` on a new page: console errors, page errors and failed requests are
//     collected and the test fails on any of them (s.allow(/pattern/) for the ones a test provokes).
//   * Waiting is on the page's state (window.TOUR.getState()), never on fixed sleeps.
//   * A failing test leaves a screenshot, the state and the console in out/<file>/.
//
// The page contract the helpers rely on is section 6 of the design (window.TOUR, data-testid).

const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const https = require('node:https');
const { spawn } = require('node:child_process');
const nodeTest = require('node:test');
const assert = require('node:assert/strict');
const panoref = require('./panoref');

const TESTS = path.resolve(__dirname, '..');
const ROOT = path.resolve(TESTS, '../../..');
const DEFAULT_BASE = 'http://127.0.0.1:8765/';
const DEFAULT_ARGS = '--use-angle=vulkan --enable-gpu --ignore-gpu-blocklist --enable-features=Vulkan';
const config = {
  root: ROOT,
  base: (process.env.TOUR_BASE && process.env.TOUR_BASE !== 'auto' ? process.env.TOUR_BASE : DEFAULT_BASE).replace(/\/?$/, '/'),
  ownServer: process.env.TOUR_BASE === 'auto',         // TOUR_BASE=auto: always serve the repository ourselves
  chrome: process.env.TOUR_CHROME || process.env.CHROME_PATH || '/usr/bin/google-chrome',
  args: (process.env.TOUR_CHROME_ARGS || DEFAULT_ARGS).split(/\s+/).filter(Boolean),
  out: path.resolve(process.env.TOUR_OUT || path.join(TESTS, 'out')),
  // extra URL parameters for every page load, e.g. TOUR_QUERY='engine=v3' or 'pano=2k'
  query: (process.env.TOUR_QUERY || '').replace(/^[?&]/, ''),
};
const PRESETS = {
  desktop: { viewport: { width: 1400, height: 850, deviceScaleFactor: 1 }, touch: false },
  phone: { viewport: { width: 390, height: 844, deviceScaleFactor: 2, isMobile: true, hasTouch: true }, touch: true },
};
// Console noise that is not the page's fault: reading the canvas back makes Chrome warn.
const NOISE = [/GPU stall due to ReadPixels/i];
const LEVELS = ['8k', '4k', '2k'];                       // best first

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const slug = (s) => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 70) || 'test';
const short = (v, n = 600) => { const s = typeof v === 'string' ? v : JSON.stringify(v); return s && s.length > n ? s.slice(0, n) + '…' : s; };

// ---- the local server -----------------------------------------------------------------------------
function get(url, method = 'GET') {
  return new Promise((resolve, reject) => {
    const req = (String(url).startsWith('https:') ? https : http).request(url, { method }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
    });
    req.on('error', reject);
    req.setTimeout(15000, () => req.destroy(new Error('timeout ' + url)));
    req.end();
  });
}
let server = null;
// Makes sure the page is served. The address of TOUR_BASE is used when it answers. When TOUR_BASE is
// not set and nothing answers at the default address (or TOUR_BASE=auto), this process starts its own
// `python3 -m http.server` on the repository root, on a free port of its own (so test files running
// side by side never share or stop each other's server), and config.base points there for the run.
async function ensureServer() {
  const up = (base) => get(base + 'assets/data/tour.json', 'HEAD').then((r) => r.status === 200, () => false);
  if (server || (!config.ownServer && await up(config.base))) return;
  if (process.env.TOUR_BASE && !config.ownServer) throw new Error('The tour does not answer at ' + config.base + ' (TOUR_BASE). Start it with `npm run serve`, or unset TOUR_BASE to let the tests serve the repository themselves.');
  const child = spawn('python3', ['-u', '-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', ROOT], { stdio: ['ignore', 'pipe', 'pipe'] });
  server = child;
  process.on('exit', () => { try { child.kill(); } catch (e) { /* gone */ } });
  const port = await new Promise((resolve, reject) => {
    let text = '';
    const seen = (chunk) => { text += chunk; const m = /port (\d+)/.exec(text); if (m) resolve(Number(m[1])); };
    child.stdout.on('data', seen);
    child.stderr.on('data', seen);
    child.once('error', reject);
    child.once('exit', (code) => reject(new Error('python3 -m http.server ended with code ' + code + ': ' + text.trim())));
    setTimeout(() => reject(new Error('python3 -m http.server did not start: ' + text.trim())), 8000);
  }).catch(async (e) => { await stopServer(); throw new Error('Could not serve the repository for the tests (' + e.message + ').'); });
  config.base = 'http://127.0.0.1:' + port + '/';
  for (let k = 0; k < 50; k++) { if (await up(config.base)) return; await sleep(100); }
  await stopServer();
  throw new Error('The local server on port ' + port + ' does not hand out assets/data/tour.json.');
}
// Resolves when the server this process started has really gone.
function stopServer() {
  const child = server;
  server = null;
  if (!child || child.exitCode !== null) return Promise.resolve();
  return new Promise((resolve) => {
    child.once('exit', resolve);
    try { child.kill(); } catch (e) { resolve(); }
    setTimeout(resolve, 3000);
  });
}

// ---- Chrome ---------------------------------------------------------------------------------------
async function launchChrome() {
  let puppeteer;
  try { puppeteer = require('puppeteer-core'); } catch (e) {
    throw new Error('puppeteer-core is not installed: run `npm install` in tools/web/tests (or set NODE_PATH to a node_modules that has it).');
  }
  if (!fs.existsSync(config.chrome)) throw new Error('Chrome not found at ' + config.chrome + ' (set TOUR_CHROME).');
  return puppeteer.launch({
    executablePath: config.chrome, headless: 'new',
    args: ['--no-first-run', '--hide-scrollbars', ...config.args],
  });
}
// The throwaway WebGL page; it also tells which GPU the run is on.
async function warmUp(browser) {
  const warm = await browser.newPage();
  await warm.goto('about:blank');
  return warm.evaluate(() => {
    const gl = document.createElement('canvas').getContext('webgl2');
    if (!gl) return { webgl2: false, renderer: 'none', maxTextureSize: 0, software: true };
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    const renderer = String(ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER));
    return { webgl2: true, renderer, maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE), software: /swiftshader|llvmpipe|software/i.test(renderer) };
  });
}

// ---- a session: one page of the tour --------------------------------------------------------------
class Session {
  constructor(ctx, page, preset, dir, name) {
    this.ctx = ctx; this.page = page; this.preset = preset; this.dir = dir; this.name = name;
    this.touch = PRESETS[preset].touch;
    this.viewport = PRESETS[preset].viewport;
    this.gl = ctx.gl;
    this.log = { errors: [], warnings: [], failed: [], aborted: [], requests: [] };
    this.notes = [];
    this.allowed = [];
    this.pointer = null;                                 // last mouse position (CSS px), null = never over the page
    this._cache = {};
    this._pending = [];
    page.on('console', (m) => {
      const text = m.text(), type = m.type();
      if (NOISE.some((re) => re.test(text)) || (type !== 'error' && type !== 'warning')) return;
      const into = type === 'error' ? this.log.errors : this.log.warnings, at = into.push(text) - 1;
      if (!/JSHandle@/.test(text)) return;
      // console.error('...', errorObject): fetch the object's own text
      this._pending.push(Promise.all(m.args().map((a) => a.evaluate((v) => (v instanceof Error ? v.stack || v.message : typeof v === 'object' ? JSON.stringify(v) : String(v))).catch(() => '?')))
        .then((parts) => { into[at] = parts.join(' ').split('\n').slice(0, 4).join(' | '); }, () => {}));
    });
    page.on('pageerror', (e) => this.log.errors.push('uncaught: ' + (e && e.message ? e.message : String(e))));
    page.on('requestfailed', (r) => {
      const why = r.failure() ? r.failure().errorText : '';
      (why === 'net::ERR_ABORTED' ? this.log.aborted : this.log.failed).push(why + ' ' + r.url());
    });
    page.on('response', (r) => {
      this.log.requests.push(r.url());
      if (r.status() >= 400) this.log.failed.push(r.status() + ' ' + r.url());
    });
  }

  note(text) { this.notes.push(typeof text === 'string' ? text : JSON.stringify(text)); }
  // Console errors / failed requests matching `pattern` are expected in this test.
  allow(pattern) { this.allowed.push(pattern); }
  problems() {
    const ok = (x) => this.allowed.some((re) => re.test(x));
    return { errors: this.log.errors.filter((x) => !ok(x)), failed: this.log.failed.filter((x) => !ok(x)) };
  }
  async assertClean() {
    await Promise.all(this._pending);
    const p = this.problems();
    assert.deepEqual(p.errors, [], 'console errors: ' + short(p.errors));
    assert.deepEqual(p.failed, [], 'failed requests: ' + short(p.failed));
  }

  // ---- loading -----------------------------------------------------------------------------
  // Opens the tour (query like '?sweep=K0'), waits for window.TOUR and, unless ready is false, for the
  // 3D engine. The landing page is still open afterwards.
  async open(query = '', opts = {}) {
    const params = [String(query).replace(/^\?/, ''), config.query].filter(Boolean).join('&');
    await this.page.goto(config.base + (params ? '?' + params : ''), { waitUntil: 'domcontentloaded' });
    await this.waitFor(() => !!window.TOUR && typeof window.TOUR.getState === 'function', { what: 'window.TOUR', timeout: 30000 });
    if (opts.ready === false) return;
    try {
      await this.ready();
    } catch (e) {
      // A lost WebGL context at start-up is a known hiccup of headless Chrome after an idle pause: one more try.
      const st = await this.state().catch(() => null);
      if (!st || st.engine !== 'failed' || this._retried) throw e;
      this._retried = true;
      this.note('engine "failed" on the first load (' + short(this.log.errors, 200) + '); the page was reloaded once');
      this.log.errors.length = 0; this.log.failed.length = 0; this.log.warnings.length = 0;
      await this.page.reload({ waitUntil: 'domcontentloaded' });
      await this.waitFor(() => !!window.TOUR, { what: 'window.TOUR after the reload', timeout: 30000 });
      await this.ready();
    }
  }
  async ready(timeout = 60000) {
    await this.waitFor(() => { const e = window.TOUR.getState().engine; if (e === 'failed') throw new Error('engine failed'); return e === 'ready'; }, { what: "engine === 'ready'", timeout });
  }
  state() { return this.page.evaluate(() => window.TOUR.getState()); }

  // Waits until fn (run in the page) returns something truthy and returns it.
  async waitFor(fn, opts = {}, ...args) {
    const timeout = opts.timeout || 10000;
    try {
      const h = await this.page.waitForFunction(fn, { timeout, polling: 40 }, ...args);
      return await h.jsonValue().catch(() => true);
    } catch (e) {
      const st = await this.page.evaluate(() => (window.TOUR ? window.TOUR.getState() : null)).catch(() => null);
      const brief = st && { engine: st.engine, mode: st.mode, sweep: st.sweep, transition: st.transition, pano: st.pano, modal: st.modal };
      const why = /timeout|timed out|exceeded/i.test(e.message) ? 'timed out after ' + timeout + ' ms' : e.message;
      throw new Error(why + ' waiting for ' + (opts.what || String(fn).slice(0, 160)) + '; state: ' + JSON.stringify(brief));
    }
  }
  // n animation frames of the page.
  frames(n = 2) {
    return this.page.evaluate((n) => new Promise((done) => { let k = 0; const f = () => (++k > n ? done(true) : requestAnimationFrame(f)); requestAnimationFrame(f); }), n);
  }

  // ---- data --------------------------------------------------------------------------------
  json(file) {
    if (!this._cache[file]) this._cache[file] = this.page.evaluate((f) => fetch(f, { cache: 'no-cache' }).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + f); return r.json(); }), file);
    return this._cache[file];
  }
  tour() { return this.json('assets/data/tour.json'); }
  manifest() { return this.json('assets/panos/manifest.json'); }
  sweeps() { return this.page.evaluate(() => window.TOUR.sweeps()); }
  // true when the page runs with the small GPU budget (touch or low memory): panoramas stop at 4k there.
  lite() { return this.page.evaluate(() => (navigator.deviceMemory || 8) < 8 || matchMedia('(pointer:coarse)').matches); }
  // The level a sweep must rest on: the best one of the manifest the GPU can hold (4k at most when lite).
  async bestLevel(id) {
    const m = await this.manifest(), e = m.nodes[id], lite = await this.lite();
    const have = LEVELS.filter((l) => e && e.levels && e.levels[l] && (m.widths[l] || 0) <= this.gl.maxTextureSize);
    if (lite && have.length > 1 && have[0] === '8k') have.shift();
    return have[0] || null;
  }
  async panoUrl(id, level) {
    const m = await this.manifest();
    return new URL(m.nodes[id].levels[level], new URL('assets/panos/manifest.json', config.base)).href;
  }

  // ---- input -------------------------------------------------------------------------------
  // The centre of an element that a user can actually hit, in CSS px.
  async target(selector, opts = {}) {
    const el = await this.page.waitForSelector(selector, { timeout: opts.timeout || 5000 }).catch(() => null);
    assert.ok(el, 'no element ' + selector);
    const hit = await el.evaluate(async (e) => {
      e.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'instant' });
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      const b = e.getBoundingClientRect();
      if (!b.width || !b.height) return { ok: false, why: 'it has no size (hidden)' };
      const x = b.left + b.width / 2, y = b.top + b.height / 2;
      if (x < 0 || y < 0 || x > innerWidth || y > innerHeight) return { ok: false, why: 'it is outside the viewport (' + Math.round(x) + ', ' + Math.round(y) + ')' };
      const top = document.elementFromPoint(x, y);
      if (!top || !(top === e || e.contains(top) || top.contains(e))) {
        return { ok: false, why: 'it is covered by <' + (top ? top.tagName.toLowerCase() + (top.id ? '#' + top.id : '') + (top.className && top.className.baseVal === undefined ? '.' + String(top.className).trim().split(/\s+/).join('.') : '') : 'nothing') + '>' };
      }
      return { ok: true, x, y, width: b.width, height: b.height };
    });
    assert.ok(hit.ok, selector + ' cannot be pressed: ' + hit.why);
    return hit;
  }
  // Click (mouse) or tap (touch) an element the way a user does.
  async press(selector, opts) {
    const p = await this.target(selector, opts);
    await this.clickAt(p.x, p.y);
    return p;
  }
  testid(id) { return '[data-testid="' + id + '"]'; }
  async clickAt(x, y) {
    this.pointer = { x, y };
    if (this.touch) await this.page.touchscreen.tap(x, y);
    else await this.page.mouse.click(x, y);
  }
  // Moves the mouse without pressing (hover).
  async moveTo(x, y) { this.pointer = { x, y }; await this.page.mouse.move(x, y, { steps: 4 }); }
  // Drag from a to b ([x, y] in CSS px) in `steps` moves, 16 ms apart; hold = pause before letting go.
  async drag(a, b, opts = {}) {
    const steps = opts.steps || 12, hold = opts.hold || 0, button = opts.button || 'left';
    const at = (i) => [a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps];
    if (this.touch) {
      const cdp = await this.page.target().createCDPSession();
      const pt = (p) => [{ x: p[0], y: p[1], id: 1, radiusX: 4, radiusY: 4, force: 1 }];
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pt(a) });
      for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pt(at(i)) }); await sleep(16); }
      if (hold) await sleep(hold);
      await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
      await cdp.detach();
    } else {
      this.pointer = { x: b[0], y: b[1] };
      await this.page.mouse.move(a[0], a[1]);
      await this.page.mouse.down({ button });
      for (let i = 1; i <= steps; i++) { const p = at(i); await this.page.mouse.move(p[0], p[1]); await sleep(16); }
      if (hold) await sleep(hold);
      await this.page.mouse.up({ button });
    }
  }
  // Two fingers on a horizontal line through (x, y), going from `from` px apart to `to` px apart.
  async pinch(x, y, from, to, steps = 10) {
    const cdp = await this.page.target().createCDPSession();
    const pts = (d) => [{ x: x - d / 2, y, id: 1, radiusX: 4, radiusY: 4, force: 1 }, { x: x + d / 2, y, id: 2, radiusX: 4, radiusY: 4, force: 1 }];
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts(from) });
    for (let i = 1; i <= steps; i++) { await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pts(from + (to - from) * i / steps) }); await sleep(16); }
    await sleep(60);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    await cdp.detach();
  }
  async wheel(deltaY, x, y) {
    this.pointer = { x: x === undefined ? this.viewport.width / 2 : x, y: y === undefined ? this.viewport.height / 2 : y };
    await this.page.mouse.move(this.pointer.x, this.pointer.y);
    await this.page.mouse.wheel({ deltaY });
  }

  // ---- the inside view ---------------------------------------------------------------------
  // Through the landing page's own button, as a visitor does. Ends at rest on the start sweep.
  async enter() {
    await this.press(this.testid('landing-enter'));
    const tour = await this.tour();
    await this.waitRest(tour.start, 20000);
    return tour.start;
  }
  // Straight to the inside view on a sweep through the test API (no landing click).
  async inside(id) {
    await this.page.evaluate(async (id) => { await window.TOUR.setMode('inside'); if (id) await window.TOUR.jumpTo(id); }, id || null);
    return this.waitRest(id, 20000);
  }
  // At rest in the inside view (on `id` when given): no transition running. Returns the state.
  async waitRest(id, timeout = 10000) {
    await this.waitFor((id) => { const s = window.TOUR.getState(); return s.mode === 'inside' && !s.transition && !!s.sweep && (!id || s.sweep === id); },
      { what: 'rest on ' + (id || 'a sweep'), timeout }, id || null);
    return this.state();
  }
  // At rest AND showing the level the device should rest on. Returns the state.
  async waitSharp(id, timeout = 20000) {
    const st = await this.waitRest(id, timeout);
    const level = await this.bestLevel(st.sweep);
    await this.waitFor((id, level) => { const s = window.TOUR.getState(); return !s.transition && s.sweep === id && s.pano && s.pano.id === id && s.pano.level === level; },
      { what: 'panorama ' + st.sweep + ' at level ' + level, timeout }, st.sweep, level);
    return this.state();
  }
  // Turns the view toward the floor ring of sweep `id` and returns where the page says it is on
  // screen: {x, y, yaw, pitch, distance} or null (TOUR.project gave nothing / off screen).
  async aimAt(id, opts = {}) {
    const tour = await this.tour();
    const aim = await this.page.evaluate((id, eye, level) => {
      const all = window.TOUR.sweeps(), a = all.find((s) => s.id === window.TOUR.getState().sweep), b = all.find((s) => s.id === id);
      if (!a || !b) return null;
      const dx = b.p[0] - a.p[0], dz = b.p[2] - a.p[2], d = Math.hypot(dx, dz);
      const yaw = Math.atan2(dx, -dz), drop = a.p[1] - (b.p[1] - eye);
      const pitch = level ? 0 : Math.max(-1.1, -Math.atan2(drop, Math.max(d, 0.01)));
      window.TOUR.setLook(yaw, pitch);
      return { yaw, pitch, distance: d };
    }, id, tour.eye, !!opts.level);
    if (!aim) return null;
    await this.frames(3);
    const p = await this.page.evaluate((id) => window.TOUR.project(id), id);
    if (!p || !(p.x >= 4 && p.y >= 4 && p.x <= this.viewport.width - 4 && p.y <= this.viewport.height - 4)) return Object.assign(aim, { x: null, y: null, projected: p });
    return Object.assign(aim, { x: p.x, y: p.y });
  }
  // Where the page draws things over the panorama in the inside view: the floor rings of the sweeps
  // visible from the current one (worked out here from the sweep positions and the camera, so a ring
  // that is half off screen is covered too) and the cursor ring at the last mouse position. Boxes are
  // {x, y, rx, ry, id} in canvas pixels and generous; rest.test.js leaves them out when it compares the
  // frame with the panorama file.
  async overlayBoxes(extra = []) {
    const tour = await this.tour(), st = await this.state(), all = await this.sweeps();
    const dims = await this.page.evaluate(() => { const c = document.querySelector('canvas#view') || document.querySelector('canvas'); return { w: c.width, h: c.height, k: c.width / c.clientWidth }; });
    const here = all.find((x) => x.id === st.sweep);
    const view = { yaw: st.yaw, pitch: st.pitch, fovY: st.fov * Math.PI / 180, width: dims.w, height: dims.h };
    const focal = dims.h / 2 / Math.tan(view.fovY / 2);
    const boxes = [];
    for (const id of here.visible) {
      const o = all.find((x) => x.id === id);
      if (!o) continue;
      const p = panoref.projectPoint(view, here.p, [o.p[0], o.p[1] - tour.eye, o.p[2]]);
      if (!p) continue;
      const r = Math.min(dims.w, 1.6 * focal / Math.max(p.depth, 0.6));     // a ring of up to 1.6 ft radius with its glow
      if (p.x + r < 0 || p.y + r < 0 || p.x - r > dims.w || p.y - r > dims.h) continue;
      boxes.push({ x: p.x, y: p.y, rx: r, ry: r, id });
    }
    for (const e of extra) if (e) boxes.push({ x: e.x * dims.k, y: e.y * dims.k, rx: (e.r || 90) * dims.k, ry: (e.r || 90) * dims.k });
    return boxes;
  }
  // A real click / tap on the floor ring of sweep `id`. Returns the aim, or throws when the ring is not on screen.
  async clickRing(id) {
    const aim = await this.aimAt(id);
    assert.ok(aim && aim.x !== null, 'the ring of ' + id + ' is not on screen after turning toward it (TOUR.project -> ' + JSON.stringify(aim && aim.projected) + ')');
    await this.clickAt(aim.x, aim.y);
    return aim;
  }

  // ---- pictures ----------------------------------------------------------------------------
  // The canvas as the page hands it out (TOUR.screenshot()), decoded: {width, height, data}.
  async canvas() {
    const url = await this.page.evaluate(() => window.TOUR.screenshot());
    return panoref.decodePng(panoref.fromDataUrl(url));
  }
  // The canvas scaled down to `width` px (in the page, cheap): {width, height, data}.
  async thumb(width = 160) {
    const r = await this.page.evaluate((w) => {
      const c = document.querySelector('canvas#view') || document.querySelector('canvas');
      const s = document.createElement('canvas');
      s.width = w; s.height = Math.max(1, Math.round(w * c.height / c.width));
      const g = s.getContext('2d', { willReadFrequently: true });
      g.drawImage(c, 0, 0, s.width, s.height);
      const d = g.getImageData(0, 0, s.width, s.height).data;
      let str = '';
      for (let i = 0; i < d.length; i += 0x8000) str += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000));
      return { width: s.width, height: s.height, b64: btoa(str) };
    }, width);
    return { width: r.width, height: r.height, data: new Uint8Array(Buffer.from(r.b64, 'base64')) };
  }
  // A piece of the canvas, pixel for pixel: `size` px square in the middle, or (where = 'top') a strip
  // twice as wide near the top edge. {width, height, data}.
  async patch(size = 160, where = 'middle') {
    const r = await this.page.evaluate((n, where) => {
      const c = document.querySelector('canvas#view') || document.querySelector('canvas');
      const w = Math.min(where === 'top' ? 2 * n : n, c.width), h = Math.min(where === 'top' ? Math.round(n / 2) : n, c.height);
      const s = document.createElement('canvas');
      s.width = w; s.height = h;
      const g = s.getContext('2d', { willReadFrequently: true });
      g.drawImage(c, Math.floor((c.width - w) / 2), where === 'top' ? Math.floor(c.height * 0.06) : Math.floor((c.height - h) / 2), w, h, 0, 0, w, h);
      const d = g.getImageData(0, 0, w, h).data;
      let str = '';
      for (let i = 0; i < d.length; i += 0x8000) str += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000));
      return { width: w, height: h, b64: btoa(str) };
    }, size, where);
    return { width: r.width, height: r.height, data: new Uint8Array(Buffer.from(r.b64, 'base64')) };
  }
  // Waits until the picture stops changing: a panorama level may still fade in after the state names
  // it, and a fly between two views takes a moment. Inside, a strip near the top edge counts as well as
  // the middle, so a ring that animates under the middle of the screen does not hold the test up.
  async settle(timeout = 5000) {
    const t0 = Date.now();
    const where = (await this.state()).mode === 'inside' ? ['middle', 'top'] : ['middle'];
    const grab = async () => { const out = []; for (const w of where) out.push(await this.patch(160, w)); return out; };
    let prev = await grab();
    for (;;) {
      await sleep(120);
      const cur = await grab();
      // (a canvas that changed its size between the two looks, e.g. on its first frame, is still changing)
      const same = (a, b) => a.width === b.width && a.height === b.height && panoref.meanAbsDiff(a, b) < 0.01;
      if (cur.some((c, i) => same(prev[i], c))) return;
      if (Date.now() - t0 > timeout) throw new Error('the picture is still changing after ' + timeout + ' ms');
      prev = cur;
    }
  }
  file(name) { fs.mkdirSync(this.dir, { recursive: true }); return path.join(this.dir, slug(this.name) + '--' + name); }
  // Evidence to look at: a screenshot of the whole page (with the chrome) into out/<file>/.
  async shot(name) { const f = this.file(name + '.png'); await this.page.screenshot({ path: f }); return f; }
  savePng(name, image) { const f = this.file(name + '.png'); fs.writeFileSync(f, panoref.encodePng(image)); return f; }

  // ---- recording a move ----------------------------------------------------------------------
  // Samples TOUR.getState() on every animation frame until stopRecorder(): [{at, sweep, mode, tr}].
  // thumb > 0 also keeps a small copy of each frame drawn while a transition runs (plus two before and
  // three after); full = true keeps one full-size frame from the middle of the first transition.
  startRecorder(opts = {}) {
    return this.page.evaluate((o) => {
      const canvas = document.querySelector('canvas#view') || document.querySelector('canvas');
      const R = window.__rec = { on: true, input: null, samples: [], full: null, after: 0, tw: 0, th: 0 };
      R.onInput = () => { R.input = performance.now(); };
      window.addEventListener('pointerup', R.onInput, true);
      window.addEventListener('keydown', R.onInput, true);
      let small = null, g = null;
      if (o.thumb) {
        small = document.createElement('canvas');
        small.width = o.thumb; small.height = Math.max(1, Math.round(o.thumb * canvas.height / canvas.width));
        g = small.getContext('2d', { willReadFrequently: true });
        R.tw = small.width; R.th = small.height;
      }
      const tick = () => {
        if (!R.on) return;
        const s = window.TOUR.getState(), tr = s.transition;
        const rec = { at: performance.now(), sweep: s.sweep, mode: s.mode, yaw: s.yaw, pitch: s.pitch, tr: tr ? { from: tr.from, to: tr.to, t: tr.t } : null };
        const moving = !!tr || (o.modes && s.mode !== o.modes);
        const seen = R.samples.some((x) => x.moving);
        if (g && (moving || !seen || R.after < 3)) {
          g.drawImage(canvas, 0, 0, small.width, small.height);
          rec.px = g.getImageData(0, 0, small.width, small.height).data;
          if (seen && !moving) R.after++;
          if (!seen && !moving) { const old = R.samples[R.samples.length - 2]; if (old) delete old.px; }   // keep two before
        }
        rec.moving = moving;
        if (moving) R.after = 0;
        if (o.full && !R.full && tr && tr.t >= 0.45) R.full = canvas.toDataURL('image/png');
        R.samples.push(rec);
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      return true;
    }, opts);
  }
  async stopRecorder() {
    const r = await this.page.evaluate(() => {
      const R = window.__rec;
      R.on = false;
      window.removeEventListener('pointerup', R.onInput, true);
      window.removeEventListener('keydown', R.onInput, true);
      const b64 = (d) => { let s = ''; for (let i = 0; i < d.length; i += 0x8000) s += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000)); return btoa(s); };
      return {
        input: R.input, full: R.full, width: R.tw, height: R.th,
        samples: R.samples.map((x) => ({ at: x.at, sweep: x.sweep, mode: x.mode, yaw: x.yaw, pitch: x.pitch, tr: x.tr, px: x.px ? b64(x.px) : null })),
      };
    });
    for (const x of r.samples) {
      if (!x.px) { delete x.px; continue; }
      x.frame = { width: r.width, height: r.height, data: new Uint8Array(Buffer.from(x.px, 'base64')) };
      delete x.px;
    }
    if (r.full) r.full = panoref.decodePng(panoref.fromDataUrl(r.full));
    return r;
  }

  // ---- downloads -----------------------------------------------------------------------------
  // Lets the page save files into out/<file>/<test>--downloads and returns that folder.
  async downloads() {
    const dir = this.file('downloads');
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    const cdp = await this.page.target().createCDPSession();
    await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: dir, eventsEnabled: false })
      .catch(() => cdp.send('Page.setDownloadBehavior', { behavior: 'allow', downloadPath: dir }));
    return dir;
  }
  async waitFile(file, timeout = 8000) {
    const t0 = Date.now();
    while (Date.now() - t0 < timeout) {
      if (fs.existsSync(file) && fs.statSync(file).size > 0 && !fs.existsSync(file + '.crdownload')) return fs.readFileSync(file);
      await sleep(60);
    }
    throw new Error('no download ' + path.basename(file) + ' within ' + timeout + ' ms');
  }

  // What is left behind when a test fails.
  async saveFailure(error) {
    await Promise.all(this._pending);
    const lines = [String(error && error.stack ? error.stack : error), ''];
    try { await this.page.screenshot({ path: this.file('FAILED.png') }); } catch (e) { lines.push('(no screenshot: ' + e.message + ')'); }
    try { lines.push('state: ' + JSON.stringify(await this.page.evaluate(() => (window.TOUR ? window.TOUR.getState() : null)))); } catch (e) { lines.push('(no state: ' + e.message + ')'); }
    lines.push('url: ' + this.page.url(), 'gpu: ' + JSON.stringify(this.gl), '', 'console errors:', ...this.log.errors, '', 'console warnings:', ...this.log.warnings.slice(-30), '', 'failed requests:', ...this.log.failed, '', 'notes:', ...this.notes);
    fs.writeFileSync(this.file('FAILED.txt'), lines.join('\n'));
  }
}

// ---- a test file ----------------------------------------------------------------------------------
// suite(__filename, {preset}) -> {test, ctx}. test(name, [opts], fn): opts = {preset, timeout (ms,
// default 90 s), skip, todo, clean (false = do not fail on console errors / failed requests),
// before(page) (runs on the new page before anything is loaded)}; fn(session, t).
function suite(file, defaults = {}) {
  const name = path.basename(file).replace(/\.test\.js$/, '');
  const dir = path.join(config.out, name);
  const ctx = { browser: null, gl: null, helper: null, name, dir };
  nodeTest.before(async () => {
    fs.rmSync(dir, { recursive: true, force: true });
    await ensureServer();
    ctx.browser = await launchChrome();
    ctx.gl = await warmUp(ctx.browser);
    // A second page on the tour's origin that only decodes panorama files for lib/panoref.js. It is
    // opened before any test page so that the test page is always the one in front.
    ctx.helper = await ctx.browser.newPage();
    await ctx.helper.goto(config.base + 'assets/panos/manifest.json');
  }, { timeout: 90000 });
  nodeTest.after(async () => {
    if (ctx.browser) await ctx.browser.close().catch(() => {});
    await stopServer();
  });

  function test(title, opts, fn) {
    if (typeof opts === 'function') { fn = opts; opts = {}; }
    const o = Object.assign({ preset: 'desktop', timeout: 90000 }, defaults, opts);
    nodeTest.test(title, { timeout: o.timeout + 20000, skip: o.skip, todo: o.todo }, async (t) => {
      assert.ok(ctx.browser, 'Chrome did not start');
      const page = await ctx.browser.newPage();
      await page.setViewport(PRESETS[o.preset].viewport);
      await page.bringToFront();
      const s = new Session(ctx, page, o.preset, dir, title);
      let timer = null;
      try {
        if (o.before) await o.before(page, s);
        await Promise.race([
          fn(s, t),
          new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('the test did not finish within ' + o.timeout + ' ms')), o.timeout); }),
        ]);
        if (o.clean !== false) await s.assertClean();
      } catch (e) {
        await s.saveFailure(e).catch(() => {});
        throw e;
      } finally {
        clearTimeout(timer);
        for (const n of s.notes) t.diagnostic(n);
        await page.close().catch(() => {});
      }
    });
  }
  return { test, ctx };
}

module.exports = { suite, assert, config, PRESETS, LEVELS, sleep, slug, short, get, ensureServer, stopServer, panoref, ROOT };
