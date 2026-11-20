'use strict';
// At rest the frame IS the panorama (design section 6: PSNR >= 40 dB against the published file).
//
// The canvas (TOUR.screenshot()) is compared with the same view cut out of the published panorama
// file by lib/panoref.js: same yaw / pitch / field of view as TOUR.getState() reports, bilinear lookup,
// nothing of the page's engine involved. Two references are tried (interpolated on the stored values
// and in linear light, the two ways a GPU samples the texture) and the better one counts.
// Standing 1.5 ft off a sweep gave 15-19 dB on the old page; exactly on it 48-57 dB.

const { suite, assert, panoref } = require('./lib/harness');
const { test } = suite(__filename);

const MIN_PSNR = 40;                                   // dB, the requirement
const MAX_MEAN_ABS = 1.5;                              // of 255
// yaw / pitch (radians) the sweeps are looked at with; the third looks straight at the wrap column of
// the file (yaw 180 deg), where a seam would show.
const LOOKS = [{ yaw: 0.7, pitch: -0.1 }, { yaw: -2.2, pitch: 0.06 }, { yaw: Math.PI, pitch: -0.18 }, { yaw: 1.9, pitch: -0.3 }];

// Compares what is on the canvas now with the published panorama of the sweep the page rests on.
async function measure(s, tag, lookError = 0) {
  await s.settle();
  const st = await s.state();
  assert.equal(st.transition, null, 'at rest');
  assert.ok(st.pano && st.pano.id === st.sweep && st.pano.level, 'getState().pano names the sweep and its level: ' + JSON.stringify(st.pano));
  const shot = await s.canvas();
  assert.ok(shot.width > shot.height, 'landscape canvas (getState().fov is the vertical field of view there)');
  const m = await s.manifest();
  const view = { yaw: st.yaw + lookError, pitch: st.pitch, fovY: st.fov * Math.PI / 180, width: shot.width, height: shot.height, offset: m.nodes[st.sweep].offset || 0 };
  const ref = await panoref.reference(s.ctx.helper, await s.panoUrl(st.sweep, st.pano.level), view);
  assert.equal(ref.srgb.missed, 0, 'the reference found every pixel in the file');
  // The floor rings and the cursor ring are drawn over the panorama on purpose: their boxes are left out.
  const mask = panoref.boxMask(shot.width, shot.height, await s.overlayBoxes([s.pointer]));
  const a = panoref.compare(shot, ref.srgb, mask), b = panoref.compare(shot, ref.linear, mask);
  const best = a.psnr >= b.psnr ? a : b, picture = a.psnr >= b.psnr ? ref.srgb : ref.linear;
  const whole = panoref.compare(shot, picture);
  const file = s.savePng(tag, panoref.sideBySide([shot, picture, panoref.diffImage(shot, picture, 8)]));
  s.note(tag + ': sweep ' + st.sweep + ' level ' + st.pano.level + ', yaw ' + (st.yaw * 180 / Math.PI).toFixed(1) + ' pitch ' + (st.pitch * 180 / Math.PI).toFixed(1) + ' fov ' + st.fov.toFixed(1) +
    ' -> PSNR ' + best.psnr.toFixed(1) + ' dB (stored values ' + a.psnr.toFixed(1) + ', linear light ' + b.psnr.toFixed(1) + '; ' + (best.masked * 100).toFixed(1) + ' % of the frame left out around rings and cursor, whole frame ' + whole.psnr.toFixed(1) +
    ' dB), mean abs diff ' + best.meanAbs.toFixed(2) + ', p99 ' + best.p99 + ', off by > 24: ' + (best.over24 * 100).toFixed(3) + ' %  [frame | file | difference x8: ' + file + ']');
  assert.ok(best.masked < 0.6, 'the rings leave enough of the frame to compare (' + (best.masked * 100).toFixed(0) + ' % left out)');
  return Object.assign({ state: st, whole: whole.psnr }, best);
}
// The sweeps to test: the start and the first highlights, as many as there are looks.
const targets = (tour) => [tour.start, ...tour.highlights.filter((id) => id !== tour.start)].slice(0, LOOKS.length);

for (let i = 0; i < LOOKS.length; i++) {
  test('at rest the frame equals the published panorama (sweep ' + (i + 1) + ' of ' + LOOKS.length + ')', async (s) => {
    await s.open();
    const id = targets(await s.tour())[i];
    await s.inside(id);
    await s.page.evaluate((l) => window.TOUR.setLook(l.yaw, l.pitch), LOOKS[i]);
    const st = await s.waitSharp(id);
    const dy = Math.atan2(Math.sin(st.yaw - LOOKS[i].yaw), Math.cos(st.yaw - LOOKS[i].yaw));
    assert.ok(Math.abs(dy) < 1e-3 && Math.abs(st.pitch - LOOKS[i].pitch) < 1e-3, 'setLook(yaw, pitch) is what getState() reports (radians)');
    const r = await measure(s, 'rest-' + id);
    assert.ok(r.psnr >= MIN_PSNR, 'PSNR ' + r.psnr.toFixed(1) + ' dB < ' + MIN_PSNR + ' dB on sweep ' + id);
    assert.ok(r.meanAbs <= MAX_MEAN_ABS, 'mean abs diff ' + r.meanAbs.toFixed(2) + ' > ' + MAX_MEAN_ABS);
  });
}

test('after a real hop the frame equals the destination panorama', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const to = (await s.sweeps()).find((x) => x.id === start).links[0];
  await s.clickRing(to);
  await s.waitSharp(to);
  const r = await measure(s, 'rest-after-hop-' + to);
  assert.ok(r.psnr >= MIN_PSNR, 'PSNR ' + r.psnr.toFixed(1) + ' dB < ' + MIN_PSNR + ' dB after the hop ' + start + ' -> ' + to + ' (the camera did not come to rest exactly on the sweep, or the picture is not the pure panorama)');
});

test('the comparison notices a view that is 2 degrees off', async (s) => {
  await s.open();
  const id = targets(await s.tour())[1];
  await s.inside(id);
  await s.page.evaluate((l) => window.TOUR.setLook(l.yaw, l.pitch), LOOKS[1]);
  await s.waitSharp(id);
  const good = await measure(s, 'control-exact-' + id);
  const off = await measure(s, 'control-2deg-' + id, 2 * Math.PI / 180);
  assert.ok(good.psnr >= MIN_PSNR, 'exact view: ' + good.psnr.toFixed(1) + ' dB');
  assert.ok(off.psnr < MIN_PSNR - 8, 'a reference turned by 2 degrees must score clearly lower, got ' + off.psnr.toFixed(1) + ' dB');
});

test('the sharp level arrives and looking around loads nothing more', async (s) => {
  await s.open();
  const start = await s.enter();
  const t0 = Date.now();
  const st = await s.waitSharp(start);
  s.note('level ' + st.pano.level + ' on screen ' + (Date.now() - t0) + ' ms after arriving (limit 5000 ms)');
  assert.ok(Date.now() - t0 <= 5000, 'the resting level is on screen within 5 s');
  // let the neighbours' preloading finish: no new request for 1.5 s
  for (let quiet = 0, n = s.log.requests.length; quiet < 1500;) {
    await new Promise((r) => setTimeout(r, 250));
    if (s.log.requests.length === n) quiet += 250; else { quiet = 0; n = s.log.requests.length; }
  }
  const before = s.log.requests.length;
  const { width: W, height: H } = s.viewport;
  await s.drag([W * 0.6, H * 0.5], [W * 0.25, H * 0.56], { steps: 20 });
  await s.drag([W * 0.3, H * 0.5], [W * 0.7, H * 0.4], { steps: 20 });
  await s.wheel(-300);
  await s.frames(40);
  assert.deepEqual(s.log.requests.slice(before), [], 'requests made while only looking around');
  const after = await s.state();
  assert.equal(after.sweep, start);
  assert.equal(after.pano.level, st.pano.level);
});
