'use strict';
// Moving through the house (design section 2, items 1-4, and section 6): the camera rests on sweeps
// only; a click on a floor ring moves there; every sweep can be reached by ring clicks; the arrow keys
// step and turn; dragging looks and never moves; the look direction survives a move.
//
// Ring positions come from TOUR.project(id) (the page's own answer to "where is the ring of this
// sweep on screen") and are clicked with the real mouse. Sweep ids are read from the page.

const { suite, assert, sleep, panoref, get, config } = require('./lib/harness');
const { test } = suite(__filename);

const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const bearing = (a, b) => Math.atan2(b.p[0] - a.p[0], -(b.p[2] - a.p[2]));     // yaw from sweep a toward sweep b
const byId = (list) => new Map(list.map((x) => [x.id, x]));
const mode = (s, m, timeout = 8000) => s.waitFor((m) => window.TOUR.getState().mode === m, { what: "mode '" + m + "'", timeout }, m);

test('a click on the ring of a visible sweep moves there', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const to = all.get(start).visible[0];
  const aim = await s.clickRing(to);
  await s.frames(3);
  const mid = await s.state();
  const st = await s.waitRest(to, 8000);
  assert.equal(st.sweep, to);
  s.note('ring of ' + to + ' at (' + Math.round(aim.x) + ', ' + Math.round(aim.y) + '), ' + aim.distance.toFixed(1) + ' ft away; three frames after the click: transition ' + JSON.stringify(mid.transition));
  await s.shot('arrived');
});

test('every sweep can be reached by ring clicks (breadth first from the start)', { timeout: 480000 }, async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const reached = new Set([start]), queue = [start], failed = [];
  let clicks = 0, slowest = { ms: 0 };
  while (queue.length) {
    const a = queue.shift(), A = all.get(a);
    // linked sweeps first (single hops), then the other visible ones, nearest first
    const far = A.visible.filter((id) => !A.links.includes(id)).sort((x, y) => Math.hypot(all.get(x).p[0] - A.p[0], all.get(x).p[2] - A.p[2]) - Math.hypot(all.get(y).p[0] - A.p[0], all.get(y).p[2] - A.p[2]));
    for (const b of [...A.links, ...far]) {
      if (reached.has(b) || !all.has(b)) continue;
      if ((await s.state()).sweep !== a) { await s.page.evaluate((id) => window.TOUR.jumpTo(id), a); }
      await s.waitRest(a, 8000);
      const aim = await s.aimAt(b);
      if (!aim || aim.x === null) { failed.push(a + ' -> ' + b + ': ring not on screen'); continue; }
      const t0 = Date.now();
      await s.clickAt(aim.x, aim.y);
      clicks++;
      const ok = await s.waitRest(b, 8000).then(() => true, () => false);
      if (ok) {
        const ms = Date.now() - t0;
        if (ms > slowest.ms) slowest = { ms, hop: a + ' -> ' + b };
        reached.add(b); queue.push(b);
      } else {
        const st = await s.state();
        failed.push(a + ' -> ' + b + ': the click at (' + Math.round(aim.x) + ', ' + Math.round(aim.y) + ') ended on ' + st.sweep + (st.transition ? ' (still moving)' : ''));
        await s.waitRest(null, 8000).catch(() => {});
      }
    }
  }
  const lost = [...all.keys()].filter((id) => !reached.has(id));
  s.note(reached.size + ' of ' + all.size + ' sweeps reached with ' + clicks + ' ring clicks; slowest arrival ' + JSON.stringify(slowest) + (failed.length ? '; clicks that did not arrive: ' + failed.join('; ') : ''));
  assert.deepEqual(lost, [], 'sweeps no ring click led to (' + failed.join('; ') + ')');
});

test('floor rings mark the sweeps visible from here', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const all = byId(await s.sweeps());
  await s.aimAt(all.get(start).visible[0]);
  await s.moveTo(6, 6);                                 // the cursor ring out of the way
  await s.settle();
  const st = await s.state(), m = await s.manifest();
  // the page as a visitor sees it (rings may be DOM elements or part of the 3D picture) against the bare panorama
  const page = panoref.decodePng(await s.page.screenshot({ type: 'png' }));
  const view = { yaw: st.yaw, pitch: st.pitch, fovY: st.fov * Math.PI / 180, width: page.width, height: page.height, offset: m.nodes[start].offset || 0 };
  const ref = await panoref.reference(s.ctx.helper, await s.panoUrl(start, st.pano.level), view);
  const bare = panoref.compare(page, ref.linear).psnr >= panoref.compare(page, ref.srgb).psnr ? ref.linear : ref.srgb;
  const luma = (img, x, y) => { const i = (y * img.width + x) * 4; return 0.2126 * img.data[i] + 0.7152 * img.data[i + 1] + 0.0722 * img.data[i + 2]; };
  const brighter = (x0, y0, x1, y1) => { let n = 0; for (let y = Math.max(0, y0); y <= Math.min(page.height - 1, y1); y++) for (let x = Math.max(0, x0); x <= Math.min(page.width - 1, x1); x++) if (luma(page, x, y) - luma(bare, x, y) > 14) n++; return n; };
  // the rings whose middle is on screen, clear of the title and the toolbar
  const boxes = (await s.overlayBoxes()).filter((b) => b.y > 70 && b.y < page.height - 100 && b.x > 20 && b.x < page.width - 20);
  assert.ok(boxes.length > 0, 'a visible sweep is on screen');
  const found = boxes.map((b) => ({ id: b.id, pixels: brighter(Math.round(b.x - b.rx), Math.round(b.y - b.ry), Math.round(b.x + b.rx), Math.round(b.y + b.ry)) }));
  // elsewhere in the picture (above the floor, clear of the chrome) nothing is drawn over the panorama
  const sky = brighter(Math.round(page.width * 0.25), 80, Math.round(page.width * 0.75), Math.round(Math.min(...boxes.map((b) => b.y - b.ry)) - 10));
  s.savePng('rings', panoref.sideBySide([page, bare, panoref.diffImage(page, bare, 4)]));
  s.note('rings from ' + start + ': ' + found.map((f) => f.id + ' ' + f.pixels + ' px').join(', ') + '; brighter pixels elsewhere: ' + sky);
  const shown = found.filter((f) => f.pixels >= 12);
  assert.ok(shown.length >= Math.max(1, Math.ceil(found.length * 0.7)), 'a white ring is drawn at ' + shown.length + ' of the ' + found.length + ' visible sweeps on screen');
  assert.ok(sky < 200, 'nothing else is painted over the panorama (' + sky + ' brighter pixels above the rings)');
});

test('the cursor ring lies on the surface under the mouse: flat on the floor, upright on a wall', async (s) => {
  await s.open();
  await s.enter();
  const tour = await s.tour();
  const all = byId(await s.sweeps());
  // a sweep with a long clear link: the floor halfway along it is certainly floor
  let best = null;
  for (const a of all.values()) for (const id of a.links) { const d = Math.hypot(all.get(id).p[0] - a.p[0], all.get(id).p[2] - a.p[2]); if (!best || d > best.d) best = { from: a.id, to: id, d }; }
  await s.page.evaluate((id) => window.TOUR.jumpTo(id), best.from);
  await s.waitSharp(best.from);
  const yaw = bearing(all.get(best.from), all.get(best.to));
  const cx = Math.round(s.viewport.width / 2), cy = Math.round(s.viewport.height / 2), R = 130;
  // the shape of what the page draws at the cursor: the picture with the mouse in the middle against the mouse parked in a corner
  const ringAt = async (look, tag) => {
    await s.page.evaluate((l) => window.TOUR.setLook(l.yaw, l.pitch), look);
    await s.moveTo(8, s.viewport.height - 8);
    await s.settle();
    const clip = { x: cx - R, y: cy - R, width: 2 * R, height: 2 * R };
    const off = panoref.decodePng(await s.page.screenshot({ type: 'png', clip }));
    await s.moveTo(cx, cy);
    await s.frames(8);
    await s.settle();
    const on = panoref.decodePng(await s.page.screenshot({ type: 'png', clip }));
    let x0 = 1e9, x1 = -1, y0 = 1e9, y1 = -1, n = 0;
    for (let y = 0; y < on.height; y++) for (let x = 0; x < on.width; x++) {
      const i = (y * on.width + x) * 4;
      if (Math.abs(on.data[i] - off.data[i]) + Math.abs(on.data[i + 1] - off.data[i + 1]) + Math.abs(on.data[i + 2] - off.data[i + 2]) > 30) { n++; x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
    }
    s.savePng('cursor-' + tag, panoref.sideBySide([off, on, panoref.diffImage(off, on, 4)]));
    return { pixels: n, width: n ? x1 - x0 + 1 : 0, height: n ? y1 - y0 + 1 : 0 };
  };
  const L = Math.min(best.d * 0.55, 8);
  const floor = await ringAt({ yaw, pitch: -Math.atan2(tour.eye, L) }, 'floor');
  s.note('cursor over the floor ' + L.toFixed(1) + ' ft ahead of ' + best.from + ': ' + JSON.stringify(floor));
  assert.ok(floor.pixels >= 40, 'a cursor ring is drawn where the mouse rests on the floor (' + floor.pixels + ' changed pixels)');
  assert.ok(floor.height / floor.width <= 0.85, 'on the floor the ring lies flat: ' + floor.width + ' x ' + floor.height + ' px');
  // level views to the sides: walls, doors, cabinets
  const walls = [];
  for (const turn of [Math.PI / 2, -Math.PI / 2, 2.4, -2.4]) walls.push(await ringAt({ yaw: yaw + turn, pitch: 0.05 }, 'wall' + walls.length));
  s.note('cursor over upright surfaces: ' + JSON.stringify(walls));
  const upright = walls.filter((w) => w.pixels >= 40 && w.height / w.width >= 0.9);
  assert.ok(upright.length >= 2, 'on a wall the ring stands upright (as tall as wide or taller) in ' + upright.length + ' of 4 level views');
});

test('a click toward a sweep, not on its ring, moves to a sweep in that direction', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const target = all.get(start).links[0];
  await s.aimAt(target, { level: true });              // look level: the ring is below the middle of the screen
  const yaw = (await s.state()).yaw;
  await s.clickAt(s.viewport.width / 2, s.viewport.height * 0.46);
  const st = await s.waitFor((from) => { const x = window.TOUR.getState(); return x.mode === 'inside' && !x.transition && x.sweep !== from ? x : false; }, { what: 'a move away from ' + start, timeout: 8000 }, start);
  const dev = Math.abs(wrap(bearing(all.get(start), all.get(st.sweep)) - yaw));
  s.note('clicked toward ' + target + ', arrived on ' + st.sweep + ' (' + (dev * 180 / Math.PI).toFixed(0) + ' deg off the click direction)');
  assert.ok(all.get(start).visible.includes(st.sweep), st.sweep + ' is visible from ' + start);
  assert.ok(dev <= Math.PI / 3, 'the sweep reached lies within 60 deg of the click direction');
});

test('keyboard: the forward key steps to the sweep ahead, left and right turn in place', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const target = all.get(start).links[0];
  await s.aimAt(target, { level: true });
  const before = await s.state();
  await s.page.keyboard.press('ArrowUp');
  const st = await s.waitFor((from) => { const x = window.TOUR.getState(); return !x.transition && x.sweep !== from ? x : false; }, { what: 'a step forward from ' + start, timeout: 8000 }, start);
  const dev = Math.abs(wrap(bearing(all.get(start), all.get(st.sweep)) - before.yaw));
  assert.ok(dev <= Math.PI / 4, 'ArrowUp went to ' + st.sweep + ', ' + (dev * 180 / Math.PI).toFixed(0) + ' deg off the view direction');
  s.note('ArrowUp: ' + start + ' -> ' + st.sweep);
  // turning
  const y0 = (await s.state()).yaw;
  await s.page.keyboard.down('ArrowRight');
  await sleep(450);
  await s.page.keyboard.up('ArrowRight');
  await s.frames(3);
  const right = await s.state();
  assert.ok(wrap(right.yaw - y0) > 0.15, 'ArrowRight turns to the right (yaw ' + y0.toFixed(2) + ' -> ' + right.yaw.toFixed(2) + ')');
  assert.equal(right.sweep, st.sweep, 'turning does not move');
  await s.page.keyboard.down('ArrowLeft');
  await sleep(450);
  await s.page.keyboard.up('ArrowLeft');
  await s.frames(3);
  const left = await s.state();
  assert.ok(wrap(left.yaw - right.yaw) < -0.15, 'ArrowLeft turns to the left');
  assert.equal(left.sweep, st.sweep);
  assert.equal(left.transition, null);
});

test('a drag looks around with a little inertia and never moves', async (s) => {
  await s.open();
  const start = await s.enter();
  const { width: W, height: H } = s.viewport;
  const a = await s.state();
  await s.startRecorder();
  await s.drag([W * 0.62, H * 0.5], [W * 0.62 - 320, H * 0.5 + 60], { steps: 14 });
  const released = await s.state();
  await sleep(350);
  const coasting = await s.state();
  await sleep(2200);
  const b = await s.state();
  await sleep(200);
  const c = await s.state();
  const rec = await s.stopRecorder();
  assert.ok(wrap(released.yaw - a.yaw) > 0.2, 'dragging left turns the view right, the picture follows the pointer (yaw ' + a.yaw.toFixed(3) + ' -> ' + released.yaw.toFixed(3) + ')');
  assert.ok(released.pitch - a.pitch > 0.03, 'dragging down tilts the view up (pitch ' + a.pitch.toFixed(3) + ' -> ' + released.pitch.toFixed(3) + ')');
  assert.ok(Math.abs(wrap(coasting.yaw - released.yaw)) > 0.004, 'the view coasts on after the pointer lets go (inertia)');
  assert.ok(Math.abs(wrap(c.yaw - b.yaw)) < 1e-4 && Math.abs(c.pitch - b.pitch) < 1e-4, 'and comes to a stop within 2.5 s');
  assert.deepEqual([...new Set(rec.samples.map((x) => x.sweep))], [start], 'the sweep never changed');
  assert.equal(rec.samples.filter((x) => x.tr).length, 0, 'no transition started');
  s.note('yaw ' + a.yaw.toFixed(3) + ' -> ' + released.yaw.toFixed(3) + ' at release -> ' + c.yaw.toFixed(3) + ' at rest');
});

test('the wheel zooms the field of view within limits and never moves', async (s) => {
  await s.open();
  const start = await s.enter();
  const f0 = (await s.state()).fov;
  await s.wheel(-600);
  await s.frames(20);
  const zoomedIn = (await s.state()).fov;
  assert.ok(zoomedIn < f0 - 3, 'wheel up narrows the field of view (' + f0.toFixed(1) + ' -> ' + zoomedIn.toFixed(1) + ' deg)');
  for (let i = 0; i < 12; i++) await s.wheel(-900);
  await s.frames(20);
  const min = (await s.state()).fov;
  for (let i = 0; i < 24; i++) await s.wheel(900);
  await s.frames(20);
  const max = (await s.state()).fov;
  assert.ok(min >= 20 && min < f0, 'zooming in stops at a sensible limit (' + min.toFixed(1) + ' deg)');
  assert.ok(max <= 110 && max > f0, 'zooming out stops at a sensible limit (' + max.toFixed(1) + ' deg)');
  const st = await s.state();
  assert.equal(st.sweep, start);
  assert.equal(st.transition, null);
  s.note('field of view ' + min.toFixed(1) + ' .. ' + max.toFixed(1) + ' deg, default ' + f0.toFixed(1));
});

test('the look direction is kept across a hop', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const to = all.get(start).links[0];
  const aim = await s.aimAt(to);
  assert.ok(aim.x !== null, 'ring of ' + to + ' on screen');
  // click the ring off-centre: look a little to the side first, so "kept" cannot mean "re-aimed at the target"
  await s.page.evaluate((y, p) => window.TOUR.setLook(y, p), aim.yaw + 0.22, aim.pitch + 0.05);
  await s.frames(3);
  const before = await s.state();
  const p = await s.page.evaluate((id) => window.TOUR.project(id), to);
  assert.ok(p, 'ring still on screen');
  await s.clickAt(p.x, p.y);
  const after = await s.waitRest(to, 8000);
  await s.frames(5);
  const rest = await s.state();
  assert.ok(Math.abs(wrap(rest.yaw - before.yaw)) < 0.02, 'yaw kept: ' + before.yaw.toFixed(3) + ' -> ' + rest.yaw.toFixed(3) + ' (the sweep\'s own direction is ' + ((all.get(to).yaw || 0)) + ')');
  assert.ok(Math.abs(rest.pitch - before.pitch) < 0.02, 'pitch kept: ' + before.pitch.toFixed(3) + ' -> ' + rest.pitch.toFixed(3));
  assert.equal(after.sweep, to);
});

test('TOUR.goTo reaches a far sweep and resolves on arrival; jumpTo is instant', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  // the sweep the most hops away over links
  const hops = new Map([[start, 0]]), q = [start];
  while (q.length) { const a = q.shift(); for (const b of all.get(a).links) if (!hops.has(b)) { hops.set(b, hops.get(a) + 1); q.push(b); } }
  const [far, n] = [...hops.entries()].sort((x, y) => y[1] - x[1])[0];
  const r = await s.page.evaluate(async (id) => {
    const t0 = performance.now();
    const ok = await window.TOUR.goTo(id);
    const st = window.TOUR.getState();
    return { ok, ms: Math.round(performance.now() - t0), sweep: st.sweep, transition: st.transition };
  }, far);
  s.note('goTo(' + far + '): ' + n + ' hops in ' + r.ms + ' ms');
  assert.equal(r.sweep, far, 'the promise resolves on arrival');
  assert.equal(r.transition, null);
  assert.ok(r.ms <= n * 1200 + 2500, 'a route of ' + n + ' hops takes at most ' + (n * 1200 + 2500) + ' ms, took ' + r.ms);
  const j = await s.page.evaluate(async (id) => {
    const t0 = performance.now();
    await window.TOUR.jumpTo(id);
    const st = window.TOUR.getState();
    return { ms: Math.round(performance.now() - t0), sweep: st.sweep, transition: st.transition };
  }, start);
  assert.equal(j.sweep, start, 'jumpTo stands on the sweep at once');
  assert.equal(j.transition, null);
  assert.ok(j.ms < 600, 'jumpTo took ' + j.ms + ' ms');
  await s.waitSharp(start);
});

test('an interrupted move still ends at rest on a sweep', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const [a, b] = [all.get(start).links[0], all.get(start).links[1] || all.get(all.get(start).links[0]).links.find((x) => x !== start)];
  // a second destination while the first move is under way
  await s.clickRing(a);
  await s.waitFor(() => !!window.TOUR.getState().transition, { what: 'the move to start', timeout: 4000 });
  await s.page.evaluate((id) => { window.TOUR.goTo(id); }, b);
  let st = await s.waitRest(b, 12000);
  assert.equal(st.sweep, b, 'the later destination wins');
  // a mode switch in the middle of a move, and back
  const back = all.get(b).links[0];
  await s.clickRing(back);
  await s.waitFor(() => !!window.TOUR.getState().transition, { what: 'the move to start', timeout: 4000 });
  await s.page.evaluate(() => window.TOUR.setMode('floorplan'));
  await s.waitFor(() => window.TOUR.getState().mode === 'floorplan', { what: 'floor plan' });
  await s.page.evaluate(() => { window.TOUR.setMode('inside'); });
  st = await s.waitRest(null, 12000);
  assert.ok([b, back].includes(st.sweep), 'after the interruption the camera rests on ' + st.sweep + ' (expected ' + b + ' or ' + back + ')');
  await s.frames(30);
  st = await s.state();
  assert.equal(st.transition, null);
  assert.ok(all.has(st.sweep));
});

test('the Inside button pressed again during a move lets the move finish', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const to = all.get(start).links[0];
  await s.clickRing(to);
  await s.waitFor(() => { const t = window.TOUR.getState().transition; return !!t && t.t > 0.15; }, { what: 'the move to be under way', timeout: 4000 });
  await s.press(s.testid('btn-inside'));
  await s.waitRest(null, 8000);
  await s.frames(30);
  const st = await s.state();
  assert.equal(st.transition, null);
  assert.equal(st.sweep, to, 'the camera arrives where it was going and stays (not back to ' + start + ')');
});

// A double click is one click. The first click starts the move; the second one, on the same spot while
// the camera is on its way, must not take the move back, must not send the camera on to the sweep beyond,
// and does not zoom (zooming is the wheel, a pinch and the + / - keys).
test('a double click moves once: the camera goes to the ring, never back and never beyond, and the view is not zoomed', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const all = byId(await s.sweeps());
  const to = all.get(start).visible[0];
  const record = () => s.page.evaluate(() => {
    const R = window.__dbl = { on: true, rows: [] };
    const tick = () => { if (!R.on) return; const st = window.TOUR.getState(), tr = st.transition; R.rows.push({ sweep: st.sweep, fov: st.fov, tr: tr ? { from: tr.from, to: tr.to, t: tr.t } : null }); requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  });
  const stop = () => s.page.evaluate(() => { window.__dbl.on = false; return window.__dbl.rows; });
  for (const gap of [70, 200, 400]) {
    await s.page.evaluate((id) => window.TOUR.jumpTo(id), start);
    await s.waitRest(start, 8000);
    const aim = await s.aimAt(to);
    assert.ok(aim && aim.x !== null, 'the ring of ' + to + ' is on screen');
    const before = await s.state();
    await record();
    await s.page.mouse.click(aim.x, aim.y);
    await sleep(gap);
    await s.page.mouse.click(aim.x, aim.y);
    const st = await s.waitRest(null, 8000);
    await sleep(700);                                   // a second move would have begun by now
    const rows = await stop(), after = await s.state();
    const moves = rows.filter((r) => r.tr);
    assert.ok(moves.length > 5, 'the first click starts a move');
    assert.deepEqual([...new Set(moves.map((r) => r.tr.from + '>' + r.tr.to))], [start + '>' + to], 'clicks ' + gap + ' ms apart: the only hop flown is ' + start + ' > ' + to);
    const back = moves.findIndex((r, i) => i > 0 && r.tr.t < moves[i - 1].tr.t - 1e-6);
    assert.equal(back, -1, 'clicks ' + gap + ' ms apart: the camera never moves back along the hop (t ' + (back > 0 ? moves[back - 1].tr.t.toFixed(3) + ' -> ' + moves[back].tr.t.toFixed(3) : '') + ')');
    assert.equal(st.sweep, to, 'clicks ' + gap + ' ms apart: the camera arrives on the ring that was clicked');
    assert.equal(after.sweep, to, 'and stays there');
    assert.equal(after.transition, null);
    assert.ok(rows.every((r) => Math.abs(r.fov - before.fov) < 0.01), 'clicks ' + gap + ' ms apart: the field of view stays ' + before.fov.toFixed(1) + ' deg (no double-click zoom)');
    assert.ok(Math.abs(wrap(after.yaw - before.yaw)) < 0.01 && Math.abs(after.pitch - before.pitch) < 0.01, 'the look direction is kept');
  }
  // the same toward a place (no ring under the cursor): a double click ends where a single click does
  const target = all.get(start).links[0];
  const look = async () => { await s.page.evaluate((id) => window.TOUR.jumpTo(id), start); await s.waitRest(start, 8000); await s.aimAt(target, { level: true }); };
  const at = [s.viewport.width / 2, s.viewport.height * 0.46];
  await look();
  await s.page.mouse.click(at[0], at[1]);
  const single = await s.waitFor((from) => { const x = window.TOUR.getState(); return x.mode === 'inside' && !x.transition && x.sweep !== from ? x.sweep : false; }, { what: 'a move away from ' + start, timeout: 8000 }, start);
  await look();
  await s.page.mouse.click(at[0], at[1]);
  await sleep(150);
  await s.page.mouse.click(at[0], at[1]);
  await s.waitFor((from) => { const x = window.TOUR.getState(); return x.mode === 'inside' && !x.transition && x.sweep !== from; }, { what: 'a move away from ' + start, timeout: 8000 }, start);
  await sleep(700);
  const twice = await s.state();
  assert.equal(twice.sweep, single, 'a double click toward a place ends on the sweep a single click reaches');
  assert.equal(twice.transition, null);
  s.note('double clicks 70 / 200 / 400 ms apart on the ring of ' + to + ': one hop each; toward ' + target + ': single and double click both end on ' + single);
});

test('a ring reached by the keyboard moves there and hands the focus to the view', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const marker = await s.waitFor(() => { const m = [...document.querySelectorAll('.sweep-marker')].find((e) => !e.hidden); return m ? m.dataset.sweep : false; }, { what: 'a ring button to be placed', timeout: 6000 });
  await s.page.focus('[data-testid="marker-' + marker + '"]');
  await s.page.keyboard.press('Enter');
  const st = await s.waitRest(marker, 8000);
  assert.equal(st.sweep, marker);
  const focus = await s.waitFor(() => (document.activeElement && document.activeElement.id === 'view' ? 'view' : false), { what: 'the focus to go to the view once the ring under the feet is gone', timeout: 4000 });
  assert.equal(focus, 'view');
});

test('whatever the input, the camera comes to rest on a sweep', { timeout: 120000 }, async (s) => {
  await s.open();
  await s.enter();
  const all = byId(await s.sweeps());
  const { width: W, height: H } = s.viewport;
  let seed = 20261119;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const visited = new Set();
  for (let i = 0; i < 24; i++) {
    const k = rnd();
    const x = W * (0.15 + 0.7 * rnd()), y = H * (0.2 + 0.55 * rnd());
    if (k < 0.45) await s.clickAt(x, y);
    else if (k < 0.7) await s.drag([x, y], [W * (0.15 + 0.7 * rnd()), H * (0.2 + 0.55 * rnd())], { steps: 6 });
    else if (k < 0.85) await s.page.keyboard.press(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'][Math.floor(rnd() * 4)]);
    else await s.wheel(rnd() < 0.5 ? -240 : 240, x, y);
    await sleep(120 + rnd() * 500);
    visited.add((await s.state()).sweep);
  }
  const st = await s.waitRest(null, 15000);
  await sleep(1200);
  const rest = await s.state();
  assert.equal(rest.mode, 'inside');
  assert.equal(rest.transition, null, 'no transition is left running');
  assert.ok(all.has(rest.sweep), 'rests on a sweep');
  assert.equal(rest.sweep, st.sweep, 'and stays there');
  assert.equal(rest.pano.id, rest.sweep, 'showing that sweep\'s panorama');
  s.note('24 random inputs passed through ' + [...visited].join(' ') + '; at rest on ' + rest.sweep);
});

test('a reel card pressed during a move still arrives on the card\'s own view', async (s) => {
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps()), data = (await s.tour()).sweeps.find((x) => x.id === start);
  const to = all.get(start).links[0], own = { yaw: (data.yaw || 0) * Math.PI / 180, pitch: (data.pitch || 0) * Math.PI / 180 };
  const look = { yaw: own.yaw + 2.5, pitch: 0.3 };
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => document.getElementById('reel').classList.contains('open'), { what: 'the reel' });
  const card = await s.target(s.testid('reel-' + start));
  await s.page.evaluate((l) => window.TOUR.setLook(l.yaw, l.pitch), look);
  await s.frames(2);
  const move = s.page.evaluate((id) => window.TOUR.goTo(id), to);
  move.catch(() => {});
  await s.waitFor(() => { const t = window.TOUR.getState().transition; return t && t.t > 0.1 && t.t < 0.6; }, { what: 'the hop to be under way' });
  await s.clickAt(card.x, card.y);
  await move;
  const st = await s.waitRest(start, 10000);
  await s.waitFor((o) => { const x = window.TOUR.getState(); return Math.abs(Math.atan2(Math.sin(x.yaw - o.yaw), Math.cos(x.yaw - o.yaw))) < 0.02 && Math.abs(x.pitch - o.pitch) < 0.02; },
    { what: 'the view to turn to the card\'s direction (yaw ' + own.yaw.toFixed(2) + ', pitch ' + own.pitch.toFixed(2) + '); it is at yaw ' + st.yaw.toFixed(2) + ', pitch ' + st.pitch.toFixed(2), timeout: 4000 }, own);
});

test('a click while a cut still holds the picture of the view left behind is not taken', async (s) => {
  const tour = JSON.parse((await get(config.base + 'assets/data/tour.json')).body.toString('utf8'));
  const id = tour.highlights.find((x) => x !== tour.start);
  await s.page.setRequestInterception(true);                // the panorama of that sweep comes 1.2 s late
  s.page.on('request', async (req) => { if (new RegExp('/panos/[248]k/' + id + '\\.').test(req.url())) await sleep(1200); req.continue().catch(() => {}); });
  await s.open('?mode=exterior');
  await mode(s, 'exterior');
  await s.settle(8000);
  const cut = s.page.evaluate((id) => window.TOUR.viewer.goTo(id, { instant: true, reset: true }), id);
  cut.catch(() => {});
  await s.waitFor(() => window.TOUR.getState().mode === 'inside', { what: 'the inside view' });
  await sleep(350);
  const held = await s.state();
  assert.equal(held.pano.level, null, 'the panorama of ' + id + ' is not in yet: the exterior picture is still up');
  const took = await s.page.evaluate((w, h) => window.TOUR.clickAt(w * 0.5, h * 0.52), s.viewport.width, s.viewport.height);
  assert.equal(took, false, 'a click on the old picture is not a click in the new view');
  await s.frames(4);
  assert.equal((await s.state()).transition, null, 'and starts no move');
  await cut;
  const st = await s.waitRest(id, 10000);
  assert.equal(st.sweep, id, 'the visitor arrives where they asked to go');
  await s.waitSharp(id);
});

test('the wheel in lines (Firefox) and a trackpad pinch zoom every view as a mouse notch does', async (s) => {
  await s.open();
  await s.enter();
  await s.waitSharp();
  // synthetic wheel events on the canvas: what a browser sends for each device
  const turn = (list) => s.page.evaluate(async (list) => {
    const c = document.getElementById('view');
    for (const init of list) c.dispatchEvent(new WheelEvent('wheel', Object.assign({ bubbles: true, cancelable: true, clientX: innerWidth / 2, clientY: innerHeight / 2 }, init)));
    await new Promise((r) => setTimeout(r, 900));
  }, list);
  const pinch = (dir) => Array.from({ length: 23 }, () => ({ deltaY: 3 * dir, ctrlKey: true }));      // sum 69 = 100 ln 2: fingers twice as far apart (dir -1) or as close
  const within = (v, lo, hi, what) => assert.ok(v >= lo && v <= hi, what + ': ' + v.toFixed(3) + ' (expected ' + lo + ' .. ' + hi + ')');
  // inside: the field of view
  const fov = async () => (await s.state()).fov;
  await s.page.evaluate(() => { for (let i = 0; i < 6; i++) window.TOUR.viewer.canvas.dispatchEvent(new WheelEvent('wheel', { deltaY: 400, bubbles: true, cancelable: true })); });
  await sleep(900);
  const wide = await fov();
  await turn([{ deltaY: -100 }]);
  const notch = wide / await fov();
  await turn([{ deltaY: 100 }]);
  await turn([{ deltaY: -3, deltaMode: 1 }]);
  const lines = wide / await fov();
  within(lines, 1 + (notch - 1) * 0.35, notch * 1.05, 'inside: three lines zoom about half a mouse notch (notch x' + notch.toFixed(3) + ')');
  await turn([{ deltaY: 3, deltaMode: 1 }]);
  await turn(pinch(-1));
  within(wide / await fov(), 1.7, 2.3, 'inside: a pinch to twice the size halves the field of view');
  // dollhouse: the size of the picture
  await s.press(s.testid('btn-dollhouse'));
  await mode(s, 'dollhouse');
  await s.waitFor(() => { const d = window.TOUR.getState().dollhouse; return d && !d.flight; }, { what: 'the dollhouse' });
  const half = async () => (await s.state()).dollhouse.half;
  let h0 = await half();
  await turn([{ deltaY: -3, deltaMode: 1 }]);
  within(h0 / await half(), 1.03, 1.12, 'dollhouse: three lines zoom in');
  h0 = await half();
  await turn(pinch(-1));
  within(h0 / await half(), 1.7, 2.4, 'dollhouse: a pinch to twice the size shows the house twice as large');
  // exterior: the zoom of the frame
  await s.press(s.testid('btn-exterior'));
  await mode(s, 'exterior');
  await s.waitFor(() => { const e = window.TOUR.getState().exterior; return e && e.photo && e.photo.on && e.photo.weight > 0.98 && !e.photo.settling; }, { what: 'the exterior on a frame', timeout: 20000 });
  const zoom = async () => (await s.state()).exterior.photo.zoom;
  let z0 = await zoom();
  await turn([{ deltaY: -3, deltaMode: 1 }]);
  within(z0 / await zoom(), 1.03, 1.12, 'exterior: three lines zoom in (a browser that reports lines is not 30 times slower)');
  z0 = await zoom();
  await turn(pinch(-1));
  within(z0 / await zoom(), 1.7, 2.3, 'exterior: a pinch to twice the size zooms in twice');
});

test('key events that carry no key (autofill) are ignored without an error', async (s) => {
  await s.open();
  await s.enter();
  await s.page.evaluate(() => {
    document.body.dispatchEvent(new Event('keydown', { bubbles: true }));
    document.body.dispatchEvent(new Event('keyup', { bubbles: true }));
    document.getElementById('dimensionSearch').dispatchEvent(new Event('keydown', { bubbles: true }));
    document.getElementById('dimensionSearch').dispatchEvent(new Event('keyup', { bubbles: true }));
  });
  await s.frames(3);
  // and the keys still work
  const before = await s.state();
  await s.page.keyboard.press('ArrowRight');
  await s.waitFor((y) => Math.abs(window.TOUR.getState().yaw - y) > 0.3, { what: 'the right arrow to turn the view' }, before.yaw);
});

