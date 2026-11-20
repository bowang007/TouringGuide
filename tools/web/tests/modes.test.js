'use strict';
// The four views and the ways between them (design section 2, items 5-7): inside, dollhouse, floor
// plan and exterior, through the toolbar buttons and through TOUR.setMode; a click in the dollhouse
// or on the floor plan flies into the sweep there.

const { suite, assert, panoref, sleep } = require('./lib/harness');
const { test } = suite(__filename);

const byId = (list) => new Map(list.map((x) => [x.id, x]));
const mode = (s, m, timeout = 8000) => s.waitFor((m) => window.TOUR.getState().mode === m, { what: "mode '" + m + "'", timeout }, m);
// The toolbar marks the active view: which mode buttons are pressed.
const pressed = (s) => s.page.evaluate(() => ['inside', 'dollhouse', 'floorplan', 'exterior'].filter((m) => {
  const b = document.querySelector('[data-testid="btn-' + m + '"]');
  return b && (b.getAttribute('aria-pressed') === 'true' || b.classList.contains('active'));
}));
// A sweep that stands in its room's bounds and in no other room's: a click on it has one meaning.
function clearSweeps(tour) {
  const inside = (r, s) => s.p[0] > r.bounds[0] + 1 && s.p[0] < r.bounds[2] - 1 && s.p[2] > r.bounds[1] + 1 && s.p[2] < r.bounds[3] - 1;
  const area = (r) => (r.bounds[2] - r.bounds[0]) * (r.bounds[3] - r.bounds[1]);
  return tour.rooms.slice().sort((a, b) => area(b) - area(a))
    .map((r) => ({ room: r, sweep: tour.sweeps.find((s) => s.id === r.sweep) }))
    .filter((x) => x.sweep && !x.sweep.outdoor && inside(x.room, x.sweep) && tour.rooms.filter((r) => inside(r, x.sweep)).length === 1);
}
const corners = (img) => {                              // mean luma of the four 8 % corners
  const w = Math.max(2, Math.round(img.width * 0.08)), h = Math.max(2, Math.round(img.height * 0.08));
  return [[0, 0], [img.width - w, 0], [0, img.height - h], [img.width - w, img.height - h]].map(([x, y]) => panoref.frameStats(panoref.cropImage(img, x, y, w, h)).mean);
};

test('the toolbar buttons switch inside -> dollhouse -> floor plan -> exterior -> inside', async (s) => {
  await s.open();
  const start = await s.enter();
  assert.deepEqual(await pressed(s), ['inside']);
  for (const m of ['dollhouse', 'floorplan', 'exterior', 'inside']) {
    await s.press(s.testid('btn-' + m));
    await mode(s, m);
    assert.deepEqual(await pressed(s), [m], 'the ' + m + ' button is the pressed one');
    await s.settle(8000);
    await s.shot(m);
  }
  const st = await s.waitRest(null, 8000);
  assert.ok(st.sweep, 'back inside on a sweep');
  s.note('back inside on ' + st.sweep + ' (entered on ' + start + ')');
});

test('TOUR.setMode reaches every mode from every other', { timeout: 120000 }, async (s) => {
  await s.open();
  await s.enter();
  const order = ['dollhouse', 'floorplan', 'exterior', 'inside', 'floorplan', 'dollhouse', 'exterior', 'floorplan', 'inside', 'exterior', 'dollhouse', 'inside'];
  for (const m of order) {
    const r = await s.page.evaluate(async (m) => { const t0 = performance.now(); const ok = await window.TOUR.setMode(m); return { ok, ms: Math.round(performance.now() - t0), mode: window.TOUR.getState().mode }; }, m);
    assert.equal(r.mode, m, 'setMode(' + m + ') resolved in mode ' + r.mode);
    assert.ok(r.ms <= 4000, 'setMode(' + m + ') took ' + r.ms + ' ms');
    assert.deepEqual(await pressed(s), [m]);
  }
  const st = await s.waitRest(null, 8000);
  assert.equal(st.transition, null);
});

test('inside -> dollhouse -> floor plan -> inside comes back to the same sweep', async (s) => {
  await s.open();
  const tour = await s.tour();
  const id = tour.highlights.find((h) => h !== tour.start);
  await s.inside(id);
  await s.page.evaluate(() => window.TOUR.setLook(1.1, -0.1));
  for (const m of ['dollhouse', 'floorplan', 'inside']) { await s.press(s.testid('btn-' + m)); await mode(s, m); await sleep(300); }
  const st = await s.waitRest(null, 8000);
  assert.equal(st.sweep, id, 'the Inside button returns to where the visitor stood');
  await s.waitSharp(id);
});

test('dollhouse: the house on a dark background; drag orbits, wheel zooms', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-dollhouse'));
  await mode(s, 'dollhouse');
  await s.settle(8000);
  const a = await s.thumb(200);
  const whole = panoref.frameStats(a), edge = corners(a);
  assert.ok(whole.std > 12, 'the dollhouse shows a picture (luma deviation ' + whole.std.toFixed(1) + ')');
  assert.ok(Math.max(...edge) < 60, 'dark background in all four corners (luma ' + edge.map((x) => x.toFixed(0)).join(', ') + ')');
  const { width: W, height: H } = s.viewport;
  await s.drag([W * 0.5, H * 0.5], [W * 0.5 + 240, H * 0.5 - 40], { steps: 12 });
  await s.settle(6000);
  const b = await s.thumb(200);
  assert.ok(panoref.meanAbsDiff(a, b) > 2, 'a drag turns the model (picture change ' + panoref.meanAbsDiff(a, b).toFixed(1) + ' / 255)');
  await s.wheel(-500);
  await s.settle(6000);
  const c = await s.thumb(200);
  assert.ok(panoref.meanAbsDiff(b, c) > 1, 'the wheel zooms (picture change ' + panoref.meanAbsDiff(b, c).toFixed(1) + ' / 255)');
  assert.equal((await s.state()).mode, 'dollhouse', 'orbiting does not leave the dollhouse');
  await s.shot('dollhouse-orbited');
  s.note('corner luma ' + edge.map((x) => x.toFixed(0)).join(', ') + '; picture change by drag ' + panoref.meanAbsDiff(a, b).toFixed(1) + ', by wheel ' + panoref.meanAbsDiff(b, c).toFixed(1));
});

test('a click in the dollhouse flies into the sweep there', async (s) => {
  await s.open();
  const tour = await s.tour();
  await s.inside(tour.start);
  await s.press(s.testid('btn-dollhouse'));
  await mode(s, 'dollhouse');
  await s.settle(8000);
  // a sweep in a large room whose floor point the page puts on screen, away from the toolbar
  let pick = null;
  for (const c of clearSweeps(tour)) {
    const p = await s.page.evaluate((id) => window.TOUR.project(id), c.sweep.id);
    if (p && p.x > 80 && p.x < s.viewport.width - 80 && p.y > 90 && p.y < s.viewport.height - 110) { pick = Object.assign({ p }, c); break; }
  }
  assert.ok(pick, 'TOUR.project(id) puts a room\'s sweep on screen in the dollhouse');
  await s.startRecorder({ thumb: 160, modes: 'inside' });
  await s.clickAt(pick.p.x, pick.p.y);
  const st = await s.waitRest(null, 10000);
  await s.frames(5);
  const rec = await s.stopRecorder();
  const all = byId(tour.sweeps), got = all.get(st.sweep);
  const d = Math.hypot(got.p[0] - pick.sweep.p[0], got.p[2] - pick.sweep.p[2]);
  s.note('clicked the floor of ' + pick.room.label + ' at sweep ' + pick.sweep.id + ' (' + Math.round(pick.p.x) + ', ' + Math.round(pick.p.y) + '); arrived inside on ' + st.sweep + ', ' + d.toFixed(1) + ' ft from it, ' +
    Math.round(rec.samples[rec.samples.length - 1].at - rec.input) + ' ms after the click');
  assert.ok(st.sweep === pick.sweep.id || got.room === pick.sweep.room || d <= 8, 'the fly-in ends on the sweep clicked or next to it, got ' + st.sweep);
  const frames = rec.samples.filter((x) => x.frame).map((x) => panoref.frameStats(x.frame));
  if (frames.length) assert.ok(Math.min(...frames.map((f) => f.std)) > 6, 'no blank frame during the fly-in');
  await s.waitSharp(st.sweep);
});

test('floor plan: straight down, north up, room names; a click on a name or on the floor enters', async (s) => {
  await s.open();
  const tour = await s.tour();
  await s.inside(tour.start);
  await s.press(s.testid('btn-floorplan'));
  await mode(s, 'floorplan');
  await s.settle(8000);
  await s.shot('floorplan');
  const img = await s.thumb(200);
  assert.ok(panoref.frameStats(img).std > 12, 'the floor plan shows a picture');
  assert.ok(Math.max(...corners(img)) < 60, 'dark background in the corners');
  // screen position is a uniform scale of plan position: x right = east, y down = south
  const pts = (await s.page.evaluate(() => window.TOUR.sweeps().map((x) => ({ id: x.id, x: x.p[0], z: x.p[2], q: window.TOUR.project(x.id) })))).filter((p) => p.q);
  assert.ok(pts.length >= Math.min(12, tour.sweeps.length), 'TOUR.project(id) places the sweeps on the plan (' + pts.length + ')');
  const fit = (u, v) => { const n = u.length, mu = u.reduce((a, b) => a + b) / n, mv = v.reduce((a, b) => a + b) / n; let c = 0, d = 0; for (let i = 0; i < n; i++) { c += (u[i] - mu) * (v[i] - mv); d += (u[i] - mu) ** 2; } return { k: c / d, o: mv - c / d * mu }; };
  const fx = fit(pts.map((p) => p.x), pts.map((p) => p.q.x)), fz = fit(pts.map((p) => p.z), pts.map((p) => p.q.y));
  const off = Math.max(...pts.map((p) => Math.hypot(fx.k * p.x + fx.o - p.q.x, fz.k * p.z + fz.o - p.q.y)));
  s.note('plan scale ' + fx.k.toFixed(2) + ' px/ft east, ' + fz.k.toFixed(2) + ' px/ft south; largest deviation from a straight-down view ' + off.toFixed(1) + ' px');
  assert.ok(fx.k > 0 && fz.k > 0, 'east is right and north is up');
  assert.ok(Math.abs(fx.k - fz.k) / fx.k < 0.03, 'the same scale in both directions');
  assert.ok(off < 4, 'seen straight down (largest deviation ' + off.toFixed(1) + ' px)');
  // room names
  const names = await s.page.evaluate(() => [...document.querySelectorAll('[data-testid^="plan-label-"]')].filter((e) => { const b = e.getBoundingClientRect(), c = getComputedStyle(e); return b.width > 4 && b.height > 4 && c.visibility !== 'hidden' && Number(c.opacity) > 0.5; }).map((e) => ({ id: e.dataset.testid.slice(11), text: e.textContent.trim() })));
  assert.ok(names.length >= 6, 'room names on the plan: ' + names.map((n) => n.text).join(', '));
  const label = names.find((n) => tour.rooms.some((r) => r.id === n.id && r.sweep !== tour.start));
  const room = tour.rooms.find((r) => r.id === label.id);
  assert.equal(label.text, room.label, 'the name is the room\'s label');
  await s.press(s.testid('plan-label-' + label.id));
  let st = await s.waitRest(room.sweep, 10000);
  s.note('click on the name "' + label.text + '" -> inside on ' + st.sweep);
  // back to the plan, then a click on the floor
  await s.press(s.testid('btn-floorplan'));
  await mode(s, 'floorplan');
  await s.settle(8000);
  const c = clearSweeps(tour).find((x) => x.sweep.id !== room.sweep);
  const p = await s.page.evaluate((id) => window.TOUR.project(id), c.sweep.id);
  assert.ok(p, 'the sweep of ' + c.room.label + ' is on the plan');
  // not on a name: a few pixels beside the point if a label covers it
  const free = await s.page.evaluate((p) => { for (const dx of [0, 14, -14, 24, -24]) { const e = document.elementFromPoint(p.x + dx, p.y); if (e && e.tagName === 'CANVAS') return { x: p.x + dx, y: p.y }; } return null; }, p);
  assert.ok(free, 'the floor at the sweep of ' + c.room.label + ' can be clicked');
  await s.clickAt(free.x, free.y);
  st = await s.waitRest(null, 10000);
  const got = tour.sweeps.find((x) => x.id === st.sweep);
  assert.ok(st.sweep === c.sweep.id || got.room === c.sweep.room, 'a click on the floor of ' + c.room.label + ' enters it, got ' + st.sweep);
  s.note('click on the floor of ' + c.room.label + ' -> inside on ' + st.sweep);
});

// Records every frame from a button press until the picture has settled in the view it leads to.
async function fly(s, button, arrived) {
  await s.settle(8000);
  await s.startRecorder({ thumb: 120, modes: 'none' });       // 'none' is never the mode: every frame is kept
  await s.frames(3);
  const t0 = Date.now();
  await s.press(s.testid(button));
  await arrived();
  await s.settle(8000);
  const ms = Date.now() - t0;
  await s.frames(3);
  const rec = await s.stopRecorder();
  const kept = rec.samples.filter((x) => x.frame && x.at >= rec.input - 60), frames = kept.map((x) => x.frame);
  // The change of the picture from one frame to the next, and the same per 1/60 s: when the browser
  // drops a frame, two steps of the flight arrive as one, which is a late frame, not a cut. (A real cut
  // comes between two frames 1/60 s apart and counts in full; a freeze is caught by `gap`.)
  const steps = frames.slice(1).map((f, i) => panoref.meanAbsDiff(frames[i], f));
  const dts = kept.slice(1).map((x, i) => x.at - kept[i].at);
  const paced = steps.map((d, i) => d * Math.min(1, (1000 / 60) / Math.max(1, dts[i])));
  const moving = steps.map((d, i) => (d > 0.3 ? i : -1)).filter((i) => i >= 0), gaps = moving.map((i) => dts[i]).sort((a, b) => a - b);
  return {
    ms, frames, steps, moving: moving.length, raw: Math.max(...steps), jump: Math.max(...paced),
    gap: gaps.length ? gaps[gaps.length - 1] : 0, pace: gaps.length ? gaps[Math.floor(gaps.length / 2)] : 0,
    blank: Math.min(...frames.map((f) => panoref.frameStats(f).std)),
  };
}

test('flying between inside and the dollhouse is one continuous move, never blank', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const out = await fly(s, 'btn-dollhouse', () => mode(s, 'dollhouse'));
  const back = await fly(s, 'btn-inside', () => s.waitRest(start, 8000));
  const pick = (f) => Array.from({ length: 8 }, (_, i) => f[Math.round(i * (f.length - 1) / 7)]);
  const sheet = s.savePng('fly-frames', panoref.sheet([...pick(out.frames), ...pick(back.frames)], 8));
  const tell = (name, f) => name + ': ' + f.ms + ' ms until the picture settles, ' + f.moving + ' frames in motion (typically ' + f.pace.toFixed(0) + ' ms apart, at most ' + f.gap.toFixed(0) + '), largest change per 1/60 s ' + f.jump.toFixed(1) + ' / 255 (between two frames as they came: ' + f.raw.toFixed(1) + '), lowest contrast ' + f.blank.toFixed(1);
  s.note(tell('out to the dollhouse', out) + '; ' + tell('back inside', back) + '  [sheet, top row out, bottom row back: ' + sheet + ']');
  for (const [name, f] of [['out to the dollhouse', out], ['back inside', back]]) {
    assert.ok(f.blank > 6, name + ': no blank frame');
    assert.ok(f.ms <= 4000, name + ': at most 4 s, took ' + f.ms + ' ms');
    assert.ok(f.moving >= 10 && f.jump < 40, name + ' is a cut, not a flight: ' + f.moving + ' frames in motion, the picture changes by ' + f.jump.toFixed(1) + ' / 255 in 1/60 s');
    if (!s.gl.software) {
      assert.ok(f.gap <= 150, name + ': the flight freezes for ' + f.gap.toFixed(0) + ' ms between two frames');
      assert.ok(f.pace <= 34, name + ': the flight runs below 30 frames a second (frames typically ' + f.pace.toFixed(0) + ' ms apart)');
    }
  }
});

test('the Inside button brings the visitor back to the sweep and the direction they left', { timeout: 120000 }, async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const to = all.get(start).links[0];
  await s.page.evaluate((id) => window.TOUR.goTo(id), to);
  await s.waitRest(to, 8000);
  // a direction that is neither the sweep's own nor the one it was entered with
  const look = { yaw: ((all.get(to).yaw || 0) * Math.PI / 180) + 2.2, pitch: -0.31 };
  const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
  for (const via of ['exterior', 'dollhouse', 'floorplan']) {
    await s.page.evaluate((l) => window.TOUR.setLook(l.yaw, l.pitch), look);
    await s.frames(3);
    await s.press(s.testid('btn-' + via));
    await mode(s, via);
    await s.settle(8000);
    await s.press(s.testid('btn-inside'));
    const st = await s.waitRest(to, 12000);
    assert.ok(Math.abs(wrap(st.yaw - look.yaw)) < 0.02 && Math.abs(st.pitch - look.pitch) < 0.02,
      'back from the ' + via + ' looking where the visitor looked: yaw ' + wrap(st.yaw).toFixed(3) + ' pitch ' + st.pitch.toFixed(3) + ', left with ' + wrap(look.yaw).toFixed(3) + ' / ' + look.pitch.toFixed(3));
  }
});

test('the open reel does not cover the house: dollhouse and floor plan frame it above the strip', async (s) => {
  await s.open();
  await s.enter();
  const flown = () => s.waitFor(() => { const x = window.TOUR.getState(), m = x[x.mode]; return !!m && !m.flight; }, { what: 'the view to stand still', timeout: 8000 });
  // the house on screen, from the corners of the footprint at floor and wall-top height
  const house = () => s.page.evaluate(() => {
    const v = window.TOUR.viewer, box = { x0: 1e9, y0: 1e9, x1: -1e9, y1: -1e9 };
    for (const r of v.tour.footprint) for (const y of [0, 7.4]) for (const p of [[r[0], y, r[1]], [r[2], y, r[1]], [r[0], y, r[3]], [r[2], y, r[3]]]) {
      const q = window.TOUR.viewer.project(p, 50);
      if (!q) continue;
      box.x0 = Math.min(box.x0, q.x); box.x1 = Math.max(box.x1, q.x); box.y0 = Math.min(box.y0, q.y); box.y1 = Math.max(box.y1, q.y);
    }
    const reel = document.getElementById('reel');
    return Object.assign(box, { reelTop: reel.classList.contains('open') ? document.getElementById('reelStrip').getBoundingClientRect().top : null });
  });
  for (const m of ['floorplan', 'dollhouse']) {
    await s.press(s.testid('btn-' + m));
    await mode(s, m);
    await flown();
    await s.settle(8000);
    const free = await house();
    await s.press(s.testid('btn-rooms'));
    await s.waitFor(() => document.getElementById('reel').classList.contains('open'), { what: 'the reel' });
    await sleep(450);
    await flown();
    const open = await house();
    await s.shot('reel-' + m);
    assert.ok(open.reelTop !== null && open.y1 <= open.reelTop, m + ': the house ends at ' + Math.round(open.y1) + ' px, the reel starts at ' + Math.round(open.reelTop) + ' (without the reel the house ended at ' + Math.round(free.y1) + ')');
    assert.ok(open.x0 >= 0 && open.x1 <= s.viewport.width && open.y0 >= 0, m + ': the house is still whole on screen');
    await s.press(s.testid('btn-rooms'));
    await s.waitFor(() => !document.getElementById('reel').classList.contains('open'), { what: 'the reel to close' });
    await sleep(450);
    await flown();
    const again = await house();
    assert.ok(Math.abs(again.y1 - free.y1) < 2 && Math.abs(again.x0 - free.x0) < 2, m + ': closing the reel gives the room back');
  }
});

// A visitor who has asked the system for less motion (prefers-reduced-motion) gets no flights: a move
// between sweeps is a quick fade through dark, a change of view a cross-fade of the two pictures.
test('with prefers-reduced-motion nothing flies: moves between sweeps and changes of view are fades', {
  before: (page) => page.emulateMediaFeatures([{ name: 'prefers-reduced-motion', value: 'reduce' }]),
}, async (s) => {
  await s.open();
  const start = await s.enter();
  assert.equal(await s.page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches), true, 'the page sees the preference');
  const all = byId(await s.sweeps());
  // every animation frame: the state, how far the camera is from the nearest sweep, and the cross-fade layer
  const record = () => s.page.evaluate(() => {
    const R = window.__calm = { on: true, rows: [] }, V = window.TOUR.viewer;
    const tick = () => {
      if (!R.on) return;
      const st = window.TOUR.getState(), e = V.view && V.view.eye, own = st[st.mode], x = document.querySelector('.xfade');
      let off = null;
      if (e) { off = Infinity; for (const w of V.sweeps) off = Math.min(off, Math.hypot(w.p[0] - e[0], w.p[1] - e[1], w.p[2] - e[2])); }
      R.rows.push({ at: performance.now(), mode: st.mode, sweep: st.sweep, tr: st.transition ? { fade: !!st.transition.fade, t: st.transition.t } : null, off, flight: own && own.flight ? own.flight.to : null, pose: own && own.phi !== undefined ? [own.yaw, own.phi, own.half] : null, fade: x && !x.hidden ? Number(getComputedStyle(x).opacity) : null });
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    return performance.now();
  });
  const stop = () => s.page.evaluate(() => { window.__calm.on = false; return window.__calm.rows; });
  // 1. a ring click: a fade, never a glide
  const to = all.get(start).visible[0];
  const aim = await s.aimAt(to);
  assert.ok(aim && aim.x !== null, 'the ring of ' + to + ' is on screen');
  let t0 = await record();
  await s.clickAt(aim.x, aim.y);
  await s.waitRest(to, 8000);
  await s.frames(4);
  let rows = await stop();
  const moving = rows.filter((r) => r.tr);
  assert.ok(moving.length > 0 && moving.every((r) => r.tr.fade), 'the move to ' + to + ' is a fade (' + moving.length + ' frames, ' + moving.filter((r) => !r.tr.fade).length + ' of them gliding)');
  assert.ok(rows.every((r) => r.off === null || r.off < 0.01), 'the camera is never between two sweeps (farthest ' + Math.max(...rows.map((r) => r.off || 0)).toFixed(2) + ' ft)');
  const rest = rows.find((r) => r.sweep === to && !r.tr);
  assert.ok(rest.at - t0 <= 1000, 'the fade is short: at rest on ' + to + ' after ' + Math.round(rest.at - t0) + ' ms');
  // 2. into the dollhouse, on to the floor plan and back inside: the view changes at once, the old picture fades out over it
  const took = {};
  for (const m of ['dollhouse', 'floorplan', 'inside']) {
    t0 = await record();
    await s.press(s.testid('btn-' + m));
    await mode(s, m);
    await sleep(700);                                   // the cross-fade
    rows = await stop();
    const first = rows.find((r) => r.mode === m);
    took[m] = Math.round(first.at - t0);
    assert.deepEqual([...new Set(rows.map((r) => r.flight).filter(Boolean))], [], 'no flight into the ' + m + ' view');
    const poses = rows.filter((r) => r.mode === m && r.pose).map((r) => r.pose.map((v) => v.toFixed(4)).join(' '));
    assert.ok(new Set(poses).size <= 1, 'the ' + m + ' camera stands still from its first frame (' + new Set(poses).size + ' poses)');
    assert.ok(rows.every((r) => r.mode !== 'inside' || r.off === null || r.off < 0.01), 'inside, the camera is on a sweep in every frame');
    const fading = rows.filter((r) => r.fade !== null && r.fade > 0.02 && r.fade < 0.98).length;
    assert.ok(fading >= 3, 'the picture left behind fades out over the ' + m + ' view (' + fading + ' frames of the fade seen)');
    assert.ok(rows[rows.length - 1].fade === null || rows[rows.length - 1].fade < 0.02, 'and is gone after the fade');
  }
  const st = await s.waitRest(to, 8000);
  assert.equal(st.sweep, to, 'back on the sweep the visitor left');
  // the chrome does not slide either
  const slides = await s.page.evaluate(() => ['#reel', '#chip', '#hint', '.rb'].filter((sel) => { const c = getComputedStyle(document.querySelector(sel)); return c.transitionProperty !== 'none' && c.transitionDuration.split(',').some((d) => parseFloat(d) > 0); }));
  assert.deepEqual(slides, [], 'chrome that still animates');
  s.note('ring click: ' + moving.length + ' frames of fade, never off a sweep; view changes switched after ' + JSON.stringify(took) + ' ms');
});

// What the engine projects belongs to the engine: the inside view and the exterior set it too. A
// fly-in must project the sweep it flies into whatever was projected last, or the picture pops when
// the inside view takes over.
test('a fly-in projects the panorama of the sweep it lands on, whatever view the visitor came through', { timeout: 150000 }, async (s) => {
  await s.open('?mode=dollhouse');
  await mode(s, 'dollhouse');
  const tour = await s.tour(), all = byId(await s.sweeps());
  const a = tour.highlights.find((id) => id !== tour.start), b = all.get(a).links.find((id) => id !== tour.start) || all.get(a).links[0];
  // every frame: what flies, what the engine projects, and a small copy of the picture
  const record = () => s.page.evaluate(() => {
    const v = window.TOUR.viewer, c = document.createElement('canvas');
    c.width = 120; c.height = 72;
    const g = c.getContext('2d', { willReadFrequently: true }), R = window.__fly = { rows: [] };
    R.off = v.on('frame', () => {
      const st = v.state(), own = st[st.mode], info = v.engine.projectionInfo();
      g.drawImage(v.canvas, 0, 0, 120, 72);
      const d = g.getImageData(0, 0, 120, 72).data;
      let str = '';
      for (let i = 0; i < d.length; i += 0x8000) str += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000));
      R.rows.push({ mode: st.mode, flight: own && own.flight ? own.flight.t : null, on: info.on, slots: info.slots.map((x) => x.id), px: btoa(str) });
    });
  });
  const stop = async () => (await s.page.evaluate(() => { window.__fly.off(); return window.__fly.rows; }))
    .map((r) => Object.assign(r, { frame: { width: 120, height: 72, data: new Uint8Array(Buffer.from(r.px, 'base64')) } }));
  const landing = (rows) => {
    const fl = rows.filter((r) => r.mode !== 'inside' && r.flight > 0), ins = rows.filter((r) => r.mode === 'inside');
    assert.ok(fl.length >= 20 && ins.length >= 1, 'a fly-in was recorded (' + fl.length + ' frames in flight, ' + ins.length + ' inside)');
    return { projected: [...new Set(fl.filter((r) => r.on).flatMap((r) => r.slots))], step: panoref.meanAbsDiff(fl[fl.length - 1].frame, ins[0].frame) };
  };
  // 1. the first fly-in of the visit
  await record();
  await s.press(s.testid('btn-rooms'));
  await s.press(s.testid('reel-' + a));
  await s.waitRest(a, 20000);
  await s.frames(3);
  const first = landing(await stop());
  assert.deepEqual(first.projected, [a], 'the fly-in to ' + a + ' projects ' + a);
  // 2. walk on, look at the house from outside, come back over the floor plan and fly into the first sweep again
  await s.press(s.testid('btn-rooms'));
  assert.equal(await s.page.evaluate((id) => window.TOUR.goTo(id), b), true, 'walked on to ' + b);
  await s.press(s.testid('btn-exterior'));
  await mode(s, 'exterior');
  await s.settle(8000);
  await s.press(s.testid('btn-floorplan'));
  await mode(s, 'floorplan');
  await s.settle(8000);
  await record();
  const fly = s.page.evaluate((id) => window.TOUR.goTo(id, { reset: true }), a);
  fly.catch(() => {});
  await s.waitRest(a, 20000);
  assert.equal(await fly, true);
  await s.frames(3);
  const second = landing(await stop());
  assert.deepEqual(second.projected, [a], 'after a walk to ' + b + ' and a look at the exterior the fly-in to ' + a + ' still projects ' + a + ', not ' + second.projected.join(', '));
  assert.ok(second.step < 6, 'and the picture does not pop when the inside view takes over: last flight frame vs first inside frame ' + second.step.toFixed(1) + ' / 255 (first fly-in ' + first.step.toFixed(1) + ')');
  s.note('last flight frame vs first inside frame: ' + first.step.toFixed(2) + ' / 255 on the first fly-in, ' + second.step.toFixed(2) + ' after walking on and coming back through the exterior');
});

test('a flight cut short leaves nothing behind: the floor plan shows its room names', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-dollhouse'));
  await mode(s, 'dollhouse');
  await s.waitFor(() => { const d = window.TOUR.getState().dollhouse; return d && d.flight && d.flight.t > 0.15; }, { what: 'the fly-out to be under way' });
  assert.ok(await s.page.evaluate(() => document.body.classList.contains('flying')), 'the page knows a flight is on');
  await s.press(s.testid('btn-exterior'));                 // leave in the middle of the flight
  await mode(s, 'exterior');
  assert.equal(await s.page.evaluate(() => document.body.classList.contains('flying')), false, 'the flight ended with the view it belonged to');
  await s.press(s.testid('btn-floorplan'));
  await mode(s, 'floorplan');
  await s.settle(8000);
  const plan = await s.page.evaluate(() => {
    const layer = document.getElementById('planLabels'), names = [...layer.querySelectorAll('.plan-label:not(.off)')];
    const hit = names.filter((e) => { const b = e.getBoundingClientRect(), t = document.elementFromPoint(b.left + b.width / 2, b.top + b.height / 2); return t === e; });
    return { body: document.body.className, opacity: Number(getComputedStyle(layer).opacity), names: names.length, hit: hit.length };
  });
  assert.ok(!/\bflying\b|\bfly-in\b/.test(plan.body), 'no flight state is left on the page: "' + plan.body + '"');
  assert.equal(plan.opacity, 1, 'the room names are visible');
  assert.ok(plan.names >= 6 && plan.hit === plan.names, plan.hit + ' of ' + plan.names + ' room names can be clicked');
  // the same when a sheet's "Visit in 3D" cuts into a flight
  await s.press(s.testid('btn-dollhouse'));
  await mode(s, 'dollhouse');
  await s.waitFor(() => { const d = window.TOUR.getState().dollhouse; return d && d.flight && d.flight.t > 0.1; }, { what: 'the flight to the dollhouse' });
  const tour = await s.tour();
  await s.page.evaluate((id) => window.TOUR.viewer.goTo(id, { instant: true, reset: true }), tour.start);
  await s.waitRest(tour.start, 15000);
  assert.equal(await s.page.evaluate(() => /\bflying\b|\bfly-in\b/.test(document.body.className)), false, 'a cut into the inside view ends the flight too');
});

test('inside <-> exterior: the two pictures dissolve into each other, like every other change of view', async (s) => {
  await s.open();
  await s.enter();
  await s.waitSharp();
  const record = () => s.page.evaluate(() => {
    const R = window.__x = { on: true, rows: [] };
    const tick = () => {
      if (!R.on) return;
      const x = document.querySelector('.xfade');
      R.rows.push({ mode: window.TOUR.getState().mode, fade: x && !x.hidden ? Number(getComputedStyle(x).opacity) : null });
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
  const stop = () => s.page.evaluate(() => { window.__x.on = false; return window.__x.rows; });
  for (const m of ['exterior', 'inside']) {
    await record();
    await s.press(s.testid('btn-' + m));
    await mode(s, m);
    // (the fade starts when the new view has drawn its first frame: its picture may still be loading)
    await s.waitFor(() => { const x = document.querySelector('.xfade'); return window.__x.rows.some((r) => r.fade !== null && r.fade < 0.9) && (!x || x.hidden || Number(getComputedStyle(x).opacity) < 0.02); }, { what: 'the dissolve into the ' + m + ' view to run and end', timeout: 8000 });
    const rows = await stop(), seen = rows.filter((r) => r.mode === m && r.fade !== null && r.fade > 0.02 && r.fade < 0.98).length;
    assert.ok(seen >= 3, 'into the ' + m + ' view the picture left behind fades out over the new one (' + seen + ' frames of the fade seen)');
    assert.ok(rows[rows.length - 1].fade === null || rows[rows.length - 1].fade < 0.02, 'and is gone afterwards');
  }
});

