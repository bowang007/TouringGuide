'use strict';
// The move between two sweeps (design section 2 item 4 and section 6): a single hop finishes within
// 1.2 s, getState().transition is {from, to, t} while it runs, the picture never goes black or blank
// on the way and neither the first nor the last frame of the move jumps.
//
// The page is sampled on every animation frame from inside (lib/harness.js startRecorder): state, and
// for the picture checks a 160 px copy of each frame. Times are measured in the page (performance.now()),
// from the pointerup of the click to the first frame at rest on the destination.

const { suite, assert, panoref, sleep } = require('./lib/harness');
const { test } = suite(__filename);

const HOP_LIMIT = 1200;                                // ms, click to rest, one linked hop
const byId = (list) => new Map(list.map((x) => [x.id, x]));
const dist = (a, b) => Math.hypot(a.p[0] - b.p[0], a.p[2] - b.p[2]);

// Stands on `from` with everything loaded, clicks the ring of `to` and records until at rest there.
async function hop(s, from, to, opts = {}) {
  if ((await s.state()).sweep !== from) await s.page.evaluate((id) => window.TOUR.jumpTo(id), from);
  await s.waitSharp(from);
  await sleep(900);                                     // a visitor looks before moving on: neighbours preload
  const aim = await s.aimAt(to);
  assert.ok(aim && aim.x !== null, 'ring of ' + to + ' on screen from ' + from);
  await s.settle();
  await s.startRecorder(opts);
  await s.frames(3);
  await s.clickAt(aim.x, aim.y);
  await s.waitRest(to, 10000);
  await s.frames(6);
  const rec = await s.stopRecorder();
  const moving = rec.samples.filter((x) => x.tr);
  assert.ok(moving.length > 0, 'getState().transition was never set during the move ' + from + ' -> ' + to);
  const first = rec.samples.indexOf(moving[0]), last = rec.samples.lastIndexOf(moving[moving.length - 1]);
  const end = rec.samples.slice(last + 1).find((x) => !x.tr && x.sweep === to);
  assert.ok(end, 'a frame at rest on ' + to + ' follows the move');
  return {
    rec, moving, first, last, end, distance: aim.distance,
    clickToRest: end.at - rec.input, clickToStart: moving[0].at - rec.input, duration: end.at - moving[0].at,
  };
}
const timing = (h) => 'click to rest ' + Math.round(h.clickToRest) + ' ms (' + Math.round(h.clickToStart) + ' ms until the move starts, the move itself ' + Math.round(h.duration) + ' ms, ' + h.moving.length + ' frames)';

test('a hop to a linked sweep finishes within 1.2 s of the click', async (s) => {
  await s.open();
  const start = await s.enter();
  const to = byId(await s.sweeps()).get(start).links[0];
  const h = await hop(s, start, to);
  s.note(start + ' -> ' + to + ', ' + h.distance.toFixed(1) + ' ft: ' + timing(h));
  if (s.gl.software) { s.note('software renderer: the time limit is not checked'); return; }
  assert.ok(h.clickToRest <= HOP_LIMIT, timing(h) + ' > ' + HOP_LIMIT + ' ms');
  assert.ok(h.duration >= 350, 'the move is an animation, not a cut (' + Math.round(h.duration) + ' ms)');
});

test('the longest link of the tour is still a hop of at most 1.2 s', async (s) => {
  await s.open();
  await s.enter();
  const all = byId(await s.sweeps());
  let best = null;
  for (const a of all.values()) for (const id of a.links) { const d = dist(a, all.get(id)); if (!best || d > best.d) best = { from: a.id, to: id, d }; }
  const h = await hop(s, best.from, best.to);
  s.note('longest link ' + best.from + ' -> ' + best.to + ', ' + best.d.toFixed(1) + ' ft: ' + timing(h));
  if (s.gl.software) { s.note('software renderer: the time limit is not checked'); return; }
  assert.ok(h.clickToRest <= HOP_LIMIT, timing(h) + ' > ' + HOP_LIMIT + ' ms');
});

test('getState().transition is {from, to, t} while moving and null at rest', async (s) => {
  await s.open();
  const start = await s.enter();
  const to = byId(await s.sweeps()).get(start).links[0];
  const h = await hop(s, start, to);
  const { rec, moving } = h;
  assert.equal(rec.samples[0].tr, null, 'null before the click');
  assert.equal(h.end.tr, null, 'null on arrival');
  const bad = moving.filter((x) => x.tr.from !== start || x.tr.to !== to || !(x.tr.t >= 0 && x.tr.t <= 1));
  assert.deepEqual(bad.map((x) => x.tr), [], 'every sample is {from: ' + start + ', to: ' + to + ', t in 0..1}');
  for (let i = 1; i < moving.length; i++) assert.ok(moving[i].tr.t >= moving[i - 1].tr.t - 1e-9, 't never runs backwards (' + moving[i - 1].tr.t + ' -> ' + moving[i].tr.t + ')');
  assert.ok(moving[0].tr.t <= 0.35, 't starts near 0 (first sample ' + moving[0].tr.t.toFixed(3) + ')');
  assert.ok(moving[moving.length - 1].tr.t >= 0.65, 't ends near 1 (last sample ' + moving[moving.length - 1].tr.t.toFixed(3) + ')');
  if (!s.gl.software) assert.ok(moving.length >= 12, 'the move is drawn in at least 12 frames, got ' + moving.length);
  const sweeps = [...new Set(rec.samples.map((x) => x.sweep))];
  assert.deepEqual(sweeps.filter((id) => id !== start && id !== to), [], 'getState().sweep is the origin or the destination throughout');
  // the look direction does not swing during the move
  const yaw = moving.map((x) => x.yaw), turn = Math.max(...yaw) - Math.min(...yaw);
  assert.ok(turn < 0.02, 'the view does not turn during the move (yaw range ' + turn.toFixed(4) + ' rad)');
  s.note(moving.length + ' samples, t ' + moving[0].tr.t.toFixed(3) + ' .. ' + moving[moving.length - 1].tr.t.toFixed(3));
});

test('no frame of a hop is black or blank, and the move starts and ends without a jump', async (s) => {
  await s.open();
  const start = await s.enter();
  const to = byId(await s.sweeps()).get(start).links[0];
  const h = await hop(s, start, to, { thumb: 160, full: true });
  const { rec } = h;
  const frames = rec.samples.filter((x) => x.frame);
  const moving = frames.filter((x) => x.tr);
  const before = frames.filter((x) => !x.tr && x.at < h.moving[0].at).pop();
  const after = frames.find((x) => !x.tr && x.at > h.moving[h.moving.length - 1].at);
  assert.ok(before && after && moving.length >= 4, 'frames were captured before, during (' + moving.length + ') and after the move');
  const sb = panoref.frameStats(before.frame), sa = panoref.frameStats(after.frame);
  assert.ok(sb.std > 8 && sa.std > 8, 'the frames at rest show a picture (the recorder can read the canvas)');
  const base = Math.max(sb.black, sa.black);
  let worst = { black: 0, std: 1e9, step: 0 };
  const stats = moving.map((x, i) => {
    const st = panoref.frameStats(x.frame);
    const step = panoref.meanAbsDiff(i ? moving[i - 1].frame : before.frame, x.frame);
    worst = { black: Math.max(worst.black, st.black), std: Math.min(worst.std, st.std), step: Math.max(worst.step, step) };
    return Object.assign(st, { t: x.tr.t, step });
  });
  const lastStep = panoref.meanAbsDiff(moving[moving.length - 1].frame, after.frame);
  // evidence: eight frames across the move, and one full-size frame from the middle
  const pick = Array.from({ length: 6 }, (_, i) => moving[Math.round(i * (moving.length - 1) / 5)].frame);
  const sheet = s.savePng('hop-frames', panoref.sheet([before.frame, ...pick, after.frame], 4));
  const mid = rec.full ? s.savePng('hop-middle', rec.full) : null;
  s.note(start + ' -> ' + to + ': ' + moving.length + ' frames; darkest frame ' + (worst.black * 100).toFixed(1) + ' % black (at rest ' + (base * 100).toFixed(1) + ' %), lowest contrast ' + worst.std.toFixed(1) +
    ', largest change between two frames ' + worst.step.toFixed(1) + ' / 255, first frame vs rest ' + stats[0].step.toFixed(1) + ', last frame vs rest ' + lastStep.toFixed(1) + '  [sheet: ' + sheet + (mid ? ', middle frame: ' + mid : '') + ']');
  assert.ok(worst.black < 0.5, 'a frame of the move is mostly black (' + (worst.black * 100).toFixed(0) + ' %)');
  assert.ok(worst.black <= base + 0.1, 'black holes during the move: ' + (worst.black * 100).toFixed(1) + ' % of a frame is black, at rest ' + (base * 100).toFixed(1) + ' %');
  assert.ok(worst.std > 8, 'a frame of the move is blank (luma deviation ' + worst.std.toFixed(1) + ')');
  assert.ok(stats[0].step < 12, 'the first frame of the move jumps away from the picture at rest (mean change ' + stats[0].step.toFixed(1) + ' / 255)');
  assert.ok(lastStep < 12, 'the picture jumps when the move ends (mean change ' + lastStep.toFixed(1) + ' / 255)');
  const steps = stats.map((x) => x.step).sort((x, y) => x - y), median = steps[Math.floor(steps.length / 2)];
  assert.ok(worst.step <= Math.max(25, 3 * median), 'the picture jumps between two frames of the move (mean change ' + worst.step.toFixed(1) + ' / 255, typical ' + median.toFixed(1) + ')');
});

test('a move over several sweeps flies through without stopping on the way', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  // a sweep two links away that is not linked to the start
  let via = null, far = null;
  for (const a of all.get(start).links) { const b = all.get(a).links.find((x) => x !== start && !all.get(start).links.includes(x)); if (b) { via = a; far = b; break; } }
  assert.ok(far, 'the tour has a sweep two links from the start');
  await s.waitSharp(start);
  await sleep(900);
  await s.startRecorder();
  const r = await s.page.evaluate(async (id) => { const t0 = performance.now(); const ok = await window.TOUR.goTo(id); return { ok, ms: performance.now() - t0 }; }, far);
  await s.waitRest(far, 10000);
  await s.frames(4);
  const rec = await s.stopRecorder();
  const i0 = rec.samples.findIndex((x) => x.tr), i1 = rec.samples.length - 1 - [...rec.samples].reverse().findIndex((x) => x.tr);
  assert.ok(i0 >= 0, 'a transition ran');
  // the longest pause (no transition) between the first and the last moving frame
  let pause = 0, since = null;
  for (let i = i0; i <= i1; i++) {
    const x = rec.samples[i];
    if (!x.tr) { if (since === null) since = rec.samples[i - 1].at; pause = Math.max(pause, x.at - since); } else since = null;
  }
  s.note('goTo(' + far + ') from ' + start + ' via ' + via + ': ' + Math.round(r.ms) + ' ms, longest pause on the way ' + Math.round(pause) + ' ms');
  assert.ok(pause <= 120, 'the camera stopped for ' + Math.round(pause) + ' ms on the way (it must fly through)');
  if (!s.gl.software) assert.ok(r.ms <= 2 * HOP_LIMIT, 'two hops in at most ' + 2 * HOP_LIMIT + ' ms, took ' + Math.round(r.ms));
});

// Entering a view is a cut. The picture that replaces the old one must be the new view itself, not the
// bare baked model that the engine can draw before the panorama (or the exterior frame) has arrived.
// The engine's test hook paints the bake magenta wherever it shows; every frame the page draws is sampled.
test('entering a view cuts straight to its picture, never to the bare model', async (s) => {
  await s.open();
  // counts the frames of view `to` (the view left behind may be the model itself: the dollhouse)
  const watch = (to) => s.page.evaluate((to) => {
    const c = document.getElementById('view'), k = document.createElement('canvas');
    k.width = 96; k.height = 54;
    const g = k.getContext('2d', { willReadFrequently: true });
    const W = window.__watch = { frames: 0, bake: 0, worst: 0 };
    W.off = window.TOUR.viewer.on('frame', () => {
      if (window.TOUR.viewer.mode !== to) return;
      g.drawImage(c, 0, 0, 96, 54);
      const d = g.getImageData(0, 0, 96, 54).data;
      let n = 0;
      for (let i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] < 70 && d[i + 2] > 200) n++;
      W.frames++;
      W.worst = Math.max(W.worst, n / (d.length / 4));
      if (n / (d.length / 4) > 0.01) W.bake++;
    });
    window.TOUR.viewer.engine.setDebug({ bake: true });
  }, to);
  const seen = () => s.page.evaluate(() => { const W = window.__watch; W.off(); window.TOUR.viewer.engine.setDebug({}); window.TOUR.viewer.engine.invalidate(); return { frames: W.frames, bake: W.bake, worst: W.worst }; });
  const tour = await s.tour();
  // the front page -> "Enter the house"
  await watch('inside');
  await s.press(s.testid('landing-enter'));
  await s.waitSharp(tour.start);
  let r = await seen();
  assert.ok(r.frames >= 1, 'frames were drawn on the way in');
  assert.equal(r.bake, 0, 'Enter the house: ' + r.bake + ' of ' + r.frames + ' frames showed the bare model (up to ' + (r.worst * 100).toFixed(0) + ' % of the frame)');
  s.note('Enter the house: ' + r.frames + ' frames, none of the bare model');
  // back inside from the exterior, and into the exterior from the dollhouse
  for (const [from, to] of [['exterior', 'inside'], ['dollhouse', 'exterior']]) {
    await s.page.evaluate((m) => window.TOUR.setMode(m, { instant: true }), from);
    await s.settle(8000);
    await watch(to);
    await s.press(s.testid('btn-' + to));
    await s.waitFor((m) => window.TOUR.getState().mode === m, { what: 'mode ' + to }, to);
    await s.settle(8000);
    r = await seen();
    assert.ok(r.frames >= 1, from + ' -> ' + to + ': frames were drawn');
    assert.equal(r.bake, 0, from + ' -> ' + to + ': ' + r.bake + ' of ' + r.frames + ' frames showed the bare model (up to ' + (r.worst * 100).toFixed(0) + ' % of the frame)');
  }
});
