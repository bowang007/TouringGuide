'use strict';
// The photoreal exterior orbit (ported unchanged from the old page, design section 2 item 8): the
// side buttons put the view on their rendered frame, a drag orbits and the view settles on the nearest
// frame, zoom keeps the frame, "Enter the home" goes inside.
//
// State used: TOUR.getState().exterior = {view, garden, photo: {frames, on, at, weight, zoom, settling}}.
// Expected frames are worked out from assets/exterior/manifest.json (ring 'o' around the house at eye
// level, ring 'h' from above), not written here.

const { suite, assert, panoref, sleep } = require('./lib/harness');
const { test } = suite(__filename);

const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const PRESET = { front: ['o', 0], right: ['o', Math.PI / 2], rear: ['o', Math.PI], left: ['o', -Math.PI / 2], roof: ['h', -Math.PI / 4] };
const frameOf = (m, view) => { const [ring, theta] = PRESET[view]; return m.frames.filter((f) => f.ring === ring).reduce((a, b) => (Math.abs(wrap(a.theta - theta)) <= Math.abs(wrap(b.theta - theta)) ? a : b)).id; };
// On a frame: one rendered frame at full weight, nothing moving any more. Returns the exterior state.
const settled = (s, timeout = 15000) => s.waitFor(() => { const x = window.TOUR.getState(), e = x.exterior; return x.mode === 'exterior' && e && e.photo && e.photo.on && e.photo.weight > 0.999 && !e.photo.settling ? e : false; }, { what: 'the exterior to settle on a frame', timeout });
async function openExterior(s) {
  await s.open();
  await s.press(s.testid('landing-exterior'));
  const e = await settled(s);
  return { e, manifest: await s.json('assets/exterior/manifest.json') };
}

test('landing -> Exterior: the front view rests on its rendered frame', async (s) => {
  const { e, manifest } = await openExterior(s);
  assert.equal(e.view, 'front');
  assert.equal(e.photo.at, frameOf(manifest, 'front'));
  assert.equal(e.photo.frames, manifest.frames.length);
  const ui = await s.page.evaluate(() => ({
    panel: getComputedStyle(document.getElementById('exteriorControls')).display !== 'none',
    front: document.querySelector('[data-exterior="front"]').getAttribute('aria-pressed'),
    button: document.querySelector('[data-testid="btn-exterior"]').getAttribute('aria-pressed'),
  }));
  assert.deepEqual(ui, { panel: true, front: 'true', button: 'true' }, 'the exterior panel is up with Front pressed');
  await s.settle(8000);
  const img = await s.thumb(200);
  assert.ok(panoref.frameStats(img).std > 20, 'the frame shows a picture');
  await s.shot('front');
});

test('the side buttons go to their frames', async (s) => {
  const { manifest } = await openExterior(s);
  for (const view of ['rear', 'right', 'left', 'roof', 'front']) {
    await s.press('[data-exterior="' + view + '"]');
    await s.waitFor((v) => window.TOUR.getState().exterior.view === v, { what: 'view ' + view }, view);
    const e = await s.waitFor((id) => { const x = window.TOUR.getState().exterior; return x.photo.at === id && x.photo.weight > 0.999 && !x.photo.settling ? x : false; }, { what: view + ' on frame ' + frameOf(manifest, view), timeout: 15000 }, frameOf(manifest, view));
    assert.equal(e.view, view);
    assert.equal(await s.page.$eval('[data-exterior="' + view + '"]', (b) => b.getAttribute('aria-pressed')), 'true');
  }
  await s.press('[data-exterior="roof"]');
  await settled(s);
  await s.settle(8000);
  await s.shot('roof');
});

test('a drag orbits freely and the view settles on the nearest frame; a short drag is one frame', async (s) => {
  const { e, manifest } = await openExterior(s);
  const { width: W, height: H } = s.viewport;
  await s.drag([W * 0.6, H * 0.45], [W * 0.6 - (s.touch ? 150 : 260), H * 0.45], { steps: 14, hold: 120 });
  const mid = (await s.state()).exterior;
  assert.equal(mid.view, 'free', 'a drag leaves the preset');
  const a = await settled(s);
  assert.notEqual(a.photo.at, e.photo.at, 'the orbit came to rest on another frame');
  assert.ok(manifest.frames.some((f) => f.id === a.photo.at));
  // exactly one frame further for a short drag
  await sleep(400);
  await s.drag([W * 0.5, H * 0.45], [W * 0.5 - 14, H * 0.45], { steps: 5 });
  await sleep(450);
  const b = await settled(s);
  const ring = manifest.frames.filter((f) => f.ring === a.photo.at[0]).sort((x, y) => x.theta - y.theta).map((f) => f.id);
  const step = (ring.indexOf(b.photo.at) - ring.indexOf(a.photo.at) + ring.length) % ring.length;
  assert.ok(b.photo.at[0] === a.photo.at[0] && (step === 1 || step === ring.length - 1), 'short drag: ' + a.photo.at + ' -> ' + b.photo.at);
  s.note('long drag: ' + e.photo.at + ' -> ' + a.photo.at + '; short drag -> ' + b.photo.at);
});

test('the wheel zooms without leaving the frame and an arrow key steps one frame', async (s) => {
  const { e } = await openExterior(s);
  await s.wheel(-400);
  await s.frames(20);
  const z = await settled(s);
  assert.ok(z.photo.zoom < 0.95, 'zoomed in (zoom ' + z.photo.zoom.toFixed(2) + ')');
  assert.equal(z.photo.at, e.photo.at, 'still on the same frame');
  await s.page.keyboard.press('ArrowRight');
  await sleep(250);
  const k = await settled(s);
  assert.notEqual(k.photo.at, e.photo.at, 'ArrowRight moved to the next frame');
  assert.equal(k.photo.at[0], e.photo.at[0], 'on the same ring');
});

test('"Hide garden" shows the model alone and "Show garden" brings the frame back', async (s) => {
  await openExterior(s);
  await s.press('#exteriorGarden');
  await s.waitFor(() => { const e = window.TOUR.getState().exterior; return e.garden === false && e.photo.on === false; }, { what: 'the garden to hide' });
  assert.match(await s.page.$eval('#exteriorGarden', (b) => b.textContent), /Show garden/);
  await s.press('#exteriorGarden');
  const e = await settled(s);
  assert.equal(e.garden, true);
});

test('"Enter the home" goes inside on the start sweep', async (s) => {
  await openExterior(s);
  await s.press(s.testid('exterior-enter'));
  const tour = await s.tour();
  const st = await s.waitRest(tour.start, 15000);
  assert.equal(st.mode, 'inside');
  assert.equal(await s.page.$eval('#exteriorControls', (e) => getComputedStyle(e).display), 'none', 'the exterior panel is gone inside');
  await s.waitSharp(tour.start);
});

// The view against the frame file itself. On a frame the camera stands where that frame was rendered
// from and looks at the same point with a narrower lens, so the canvas must be the middle of the file,
// a plain crop: both are scaled to 700 px by the 2D canvas, nothing of the engine makes the reference.
test('on a frame the picture is the path-traced frame', { timeout: 120000 }, async (s) => {
  const { manifest } = await openExterior(s);
  const found = [];
  for (const view of ['front', 'roof', 'left']) {
    await s.press('[data-exterior="' + view + '"]');
    const id = frameOf(manifest, view);
    await s.waitFor((id) => { const x = window.TOUR.getState().exterior; return x.photo.at === id && x.photo.weight > 0.999 && !x.photo.settling; }, { what: view + ' on frame ' + id, timeout: 15000 }, id);
    await s.waitFor((id) => { const h = window.TOUR.viewer.engine.hasPanorama(id); return !!h && h.full && !h.pending; }, { what: 'the full-size frame ' + id, timeout: 15000 }, id);
    await s.settle(8000);
    const psnr = await s.page.evaluate(async (id) => {
      const m = await fetch('assets/exterior/manifest.json', { cache: 'no-cache' }).then((r) => r.json()), f = m.frames.find((x) => x.id === id);
      const img = new Image();
      img.src = new URL(f.full, new URL('assets/exterior/manifest.json', location.href)).href;
      await img.decode();
      const c = document.getElementById('view'), w = 700, h = Math.round(700 * c.height / c.width);
      const vfov = 2 * Math.atan(Math.tan(m.hfov * Math.PI / 360) / m.aspect);
      const hy = Math.tan(window.TOUR.viewer.view.fovY / 2) / Math.tan(vfov / 2), hx = hy * (c.width / c.height) / m.aspect;
      const scaled = (src, sx, sy, sw, sh) => { const k = document.createElement('canvas'); k.width = w; k.height = h; const g = k.getContext('2d', { willReadFrequently: true }); g.drawImage(src, sx, sy, sw, sh, 0, 0, w, h); return g.getImageData(0, 0, w, h).data; };
      const a = scaled(c, 0, 0, c.width, c.height), b = scaled(img, img.width / 2 * (1 - hx), img.height / 2 * (1 - hy), img.width * hx, img.height * hy);
      let se = 0;
      for (let i = 0; i < a.length; i += 4) for (let k = 0; k < 3; k++) { const d = a[i + k] - b[i + k]; se += d * d; }
      return 10 * Math.log10(255 * 255 / Math.max(1e-9, se / (a.length / 4 * 3)));
    }, id);
    found.push(view + ' (' + id + ') ' + psnr.toFixed(1) + ' dB');
    assert.ok(psnr >= 30, view + ': the view differs from ' + id + '.webp (PSNR ' + psnr.toFixed(1) + ' dB, at least 30 expected)');
  }
  s.note('exterior against the frame files: ' + found.join(', '));
});

test('a view that stands still draws nothing: behind the landing page, in the exterior, inside', async (s) => {
  await s.open();
  const draws = async (ms) => { const a = (await s.state()).draws; await sleep(ms); return (await s.state()).draws - a; };
  // the landing page is up; behind it the exterior loads the frame it stands on, at half size (the
  // visitor has not chosen this view yet), and then rests
  await s.waitFor(() => { const e = window.TOUR.viewer.state().exterior; return !!e && !!e.photo && e.photo.weight > 0.999 && !e.photo.settling; }, { what: 'the exterior behind the landing page to settle', timeout: 20000 });
  const front = await s.waitFor(() => { const v = window.TOUR.viewer, id = v.state().exterior.photo.at, h = v.engine.hasPanorama(id); return !!h && !h.pending ? { id, full: h.full } : null; }, { what: 'the front frame', timeout: 15000 });
  await sleep(1500);
  assert.equal(await draws(1000), 0, 'frames drawn in a second behind the landing page');
  const behind = await s.page.evaluate((id) => ({ full: window.TOUR.viewer.engine.hasPanorama(id).full, frames: performance.getEntriesByType('resource').filter((r) => /assets\/exterior\/.*\.(webp|jpe?g|png|avif)/.test(r.name)).length }), front.id);
  assert.equal(behind.full, false, 'behind the landing page the front frame is the half-size one');
  assert.equal(behind.frames, 1, 'and it is the only frame fetched');
  await s.press(s.testid('landing-exterior'));
  await settled(s);
  await s.waitFor((id) => { const h = window.TOUR.viewer.engine.hasPanorama(id); return !!h && h.full && !h.pending; }, { what: 'the full-size front frame, now that the visitor chose the exterior', timeout: 15000 }, front.id);
  await sleep(1500);
  assert.equal(await draws(1000), 0, 'frames drawn in a second of standing still in the exterior');
  // and it wakes up: a drag draws again
  const before = (await s.state()).draws;
  await s.drag([s.viewport.width * 0.6, s.viewport.height * 0.45], [s.viewport.width * 0.6 - 120, s.viewport.height * 0.45], { steps: 8 });
  assert.ok((await s.state()).draws - before >= 5, 'a drag draws frames again');
  await s.press(s.testid('exterior-enter'));
  const tour = await s.tour();
  await s.waitSharp(tour.start);
  await sleep(1500);
  assert.equal(await draws(1000), 0, 'frames drawn in a second at rest inside');
});
