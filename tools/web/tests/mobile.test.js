'use strict';
// The tour on a phone (design section 6: "works at 390x844 touch"): 390 x 844 CSS px, device pixel
// ratio 2, touch input only. Taps, one-finger drags and two-finger pinches are sent as real touch
// events; nothing here uses the mouse.

const { suite, assert, sleep } = require('./lib/harness');
const { test } = suite(__filename, { preset: 'phone' });

const BUTTONS = ['btn-rooms', 'btn-dollhouse', 'btn-floorplan', 'btn-inside', 'btn-exterior', 'btn-dimensions', 'btn-design'];
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a));
const boxes = (s, ids) => s.page.evaluate((ids) => ids.map((id) => { const e = document.querySelector('[data-testid="' + id + '"]'); if (!e) return { id, missing: true }; const b = e.getBoundingClientRect(), c = getComputedStyle(e); return { id, x: b.left, y: b.top, w: b.width, h: b.height, shown: c.display !== 'none' && c.visibility !== 'hidden' }; }), ids);
function layoutProblems(list, W, H, min) {
  const bad = [];
  for (const b of list) {
    if (b.missing || !b.shown || !b.w) { bad.push(b.id + ': not shown'); continue; }
    if (b.x < 0 || b.y < 0 || b.x + b.w > W + 0.5 || b.y + b.h > H + 0.5) bad.push(b.id + ': outside the screen (' + Math.round(b.x) + ', ' + Math.round(b.y) + ', ' + Math.round(b.w) + ' x ' + Math.round(b.h) + ')');
    if (b.w < min || b.h < min) bad.push(b.id + ': ' + Math.round(b.w) + ' x ' + Math.round(b.h) + ' px is too small to tap (' + min + ' px)');
  }
  for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
    const a = list[i], b = list[j];
    if (a.w && b.w && a.x < b.x + b.w - 1 && b.x < a.x + a.w - 1 && a.y < b.y + b.h - 1 && b.y < a.y + a.h - 1) bad.push(a.id + ' overlaps ' + b.id);
  }
  return bad;
}

test('phone: the landing page fits and its buttons can be tapped', async (s) => {
  await s.open();
  const { width: W, height: H } = s.viewport;
  const env = await s.page.evaluate(() => ({ w: innerWidth, h: innerHeight, dpr: devicePixelRatio, coarse: matchMedia('(pointer:coarse)').matches, scroll: document.documentElement.scrollWidth }));
  assert.deepEqual([env.w, env.h, env.dpr, env.coarse], [W, H, 2, true], 'the phone preset is in effect');
  assert.ok(env.scroll <= W, 'no horizontal scroll');
  assert.deepEqual(layoutProblems(await boxes(s, ['landing-enter', 'landing-exterior', 'landing-plan']), W, H, 40), []);
  await s.shot('landing');
  await s.enter();
  assert.equal((await s.state()).mode, 'inside');
});

test('phone: every control is on screen, large enough to tap and reachable', async (s) => {
  await s.open();
  await s.enter();
  await s.waitSharp();
  const { width: W, height: H } = s.viewport;
  assert.deepEqual(layoutProblems(await boxes(s, BUTTONS), W, H, 36), []);
  assert.ok(await s.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth && document.documentElement.scrollHeight <= innerHeight + 1), 'the page does not scroll');
  for (const id of BUTTONS) await s.target(s.testid(id));              // none is covered by something else
  await s.shot('inside');
  // each mode button works by tap
  for (const m of ['dollhouse', 'floorplan', 'exterior', 'inside']) {
    await s.press(s.testid('btn-' + m));
    await s.waitFor((m) => window.TOUR.getState().mode === m, { what: "mode '" + m + "' after a tap" }, m);
    assert.deepEqual(layoutProblems(await boxes(s, BUTTONS), W, H, 36), [], 'the toolbar in the ' + m + ' view');
    await s.settle(8000);
    await s.shot(m);
  }
});

test('phone: a tap on a floor ring moves there', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.waitSharp(start);
  const to = (await s.sweeps()).find((x) => x.id === start).links[0];
  await sleep(800);
  const aim = await s.aimAt(to);
  assert.ok(aim && aim.x !== null, 'the ring of ' + to + ' is on screen');
  await s.startRecorder();
  await s.clickAt(aim.x, aim.y);
  await s.waitRest(to, 8000);
  await s.frames(4);
  const rec = await s.stopRecorder();
  const moving = rec.samples.filter((x) => x.tr), end = rec.samples.find((x) => !x.tr && x.sweep === to);
  s.note('tap -> rest on ' + to + ' in ' + Math.round(end.at - rec.input) + ' ms, ' + moving.length + ' frames');
  if (!s.gl.software) assert.ok(end.at - rec.input <= 1200, 'a hop takes at most 1.2 s on the phone, took ' + Math.round(end.at - rec.input) + ' ms');
});

test('phone: one finger looks around and never moves', async (s) => {
  await s.open();
  const start = await s.enter();
  const { width: W, height: H } = s.viewport;
  const a = await s.state();
  await s.drag([W * 0.75, H * 0.5], [W * 0.2, H * 0.55], { steps: 12, hold: 150 });
  await sleep(1500);
  const b = await s.state();
  assert.ok(wrap(b.yaw - a.yaw) > 0.3, 'dragging left turns the view right (yaw ' + a.yaw.toFixed(2) + ' -> ' + b.yaw.toFixed(2) + ')');
  assert.equal(b.sweep, start);
  assert.equal(b.transition, null);
  assert.ok(await s.page.evaluate(() => scrollX === 0 && scrollY === 0), 'the page itself did not scroll');
});

test('phone: a pinch zooms the field of view', async (s) => {
  await s.open();
  const start = await s.enter();
  const { width: W, height: H } = s.viewport;
  const f0 = (await s.state()).fov;
  await s.pinch(W / 2, H * 0.45, 90, 280);                            // fingers apart: zoom in
  await s.frames(10);
  const zoomIn = (await s.state()).fov;
  assert.ok(zoomIn < f0 - 5, 'spreading two fingers narrows the field of view (' + f0.toFixed(1) + ' -> ' + zoomIn.toFixed(1) + ' deg)');
  await s.pinch(W / 2, H * 0.45, 280, 70);                            // fingers together: zoom out
  await s.frames(10);
  const zoomOut = (await s.state()).fov;
  assert.ok(zoomOut > zoomIn + 5, 'pinching widens it again (' + zoomIn.toFixed(1) + ' -> ' + zoomOut.toFixed(1) + ' deg)');
  const st = await s.state();
  assert.equal(st.sweep, start, 'a pinch does not move');
  assert.equal(st.transition, null);
  assert.equal(await s.page.evaluate(() => (window.visualViewport ? window.visualViewport.scale : 1)), 1, 'the page itself is not zoomed');
});

test('phone: the reel slides up and a tap on a room goes there', async (s) => {
  await s.open();
  await s.enter();
  const tour = await s.tour();
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => { const r = document.getElementById('reel'); return r && r.classList.contains('open') && Number(getComputedStyle(r).opacity) > 0.95; }, { what: 'the reel' });
  await s.shot('reel');
  const { width: W, height: H } = s.viewport;
  assert.deepEqual(layoutProblems(await boxes(s, BUTTONS), W, H, 36), [], 'the toolbar stays usable with the reel open');
  const id = tour.highlights.find((h) => h !== tour.start);
  await s.press(s.testid('reel-' + id));
  const st = await s.waitRest(id, 15000);
  assert.equal(st.sweep, id);
});

test('phone: floor plan and Dimensions work by touch', async (s) => {
  await s.open();
  const tour = await s.tour();
  await s.press(s.testid('landing-plan'));
  await s.waitFor(() => window.TOUR.getState().mode === 'floorplan', { what: 'the floor plan' });
  await s.settle(8000);
  const names = await s.page.evaluate(() => [...document.querySelectorAll('[data-testid^="plan-label-"]')].filter((e) => { const b = e.getBoundingClientRect(), c = getComputedStyle(e); return b.width > 4 && c.visibility !== 'hidden' && Number(c.opacity) > 0.5; }).map((e) => e.dataset.testid.slice(11)));
  assert.ok(names.length >= 4, 'room names on the phone plan: ' + names.join(', '));
  const room = tour.rooms.find((r) => names.includes(r.id));
  await s.press(s.testid('plan-label-' + room.id));
  await s.waitRest(room.sweep, 10000);
  // Dimensions sheet: tap a room on the plan
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  const item = await s.page.evaluate(() => { const r = window.MEASURE.data.rooms; return r[Math.min(5, r.length - 1)]; });
  await s.press('#dimensionPlan [data-measure="' + item.id + '"]');
  await s.waitFor((id) => window.MEASURE.selected === id, { what: item.id + ' selected by a tap' }, item.id);
  assert.equal(await s.page.$eval('#dimensionDetailTitle', (e) => e.textContent), item.name);
  assert.ok(await s.page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'the sheet does not widen the page');
  await s.shot('dimensions');
});

// ---- pop-ups and drawers --------------------------------------------------------------------
// What can stand over the picture at the same time on a phone, held upright and on its side: the
// title, the room chip, a message, the first-run hint, the two toolbars, the exterior panel, the
// reel and the menu. None of them may cover another or leave the screen.
const LANDSCAPE = { width: 844, height: 390, deviceScaleFactor: 2, isMobile: true, hasTouch: true };
const overlay = (s) => s.page.evaluate(() => {
  const out = {};
  const box = (r) => [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)];
  const text = (el) => { const g = document.createRange(); g.selectNodeContents(el); return g.getBoundingClientRect(); };
  const a = text(document.querySelector('#title h1')), b = text(document.querySelector('#title p'));
  out.title = box({ left: Math.min(a.left, b.left), top: a.top, right: Math.max(a.right, b.right), bottom: b.bottom });
  for (const [k, sel] of Object.entries({ chip: '#chip', message: '#toast', hint: '#hint', 'left bar': '.bar-left', 'right bar': '.bar-right', 'exterior panel': '#exteriorControls', menu: '#menu', reel: '#reelStrip' })) {
    const e = document.querySelector(sel), c = getComputedStyle(e), r = e.getBoundingClientRect();
    if (c.display === 'none' || c.visibility === 'hidden' || Number(c.opacity) < 0.05 || !r.width || !r.height) continue;
    if (k === 'reel' && !document.getElementById('reel').classList.contains('open')) continue;
    out[k] = box(r);
  }
  return out;
});
function overlaps(b, W, H) {
  const keys = Object.keys(b), bad = [];
  const area = (p, q) => Math.max(0, Math.min(p[2], q[2]) - Math.max(p[0], q[0])) * Math.max(0, Math.min(p[3], q[3]) - Math.max(p[1], q[1]));
  for (const k of keys) if (k !== 'reel' && (b[k][0] < 0 || b[k][1] < 0 || b[k][2] > W || b[k][3] > H)) bad.push(k + ' leaves the screen ' + b[k]);
  for (let i = 0; i < keys.length; i++) for (let j = i + 1; j < keys.length; j++) if (area(b[keys[i]], b[keys[j]]) > 0) bad.push(keys[i] + ' ' + b[keys[i]] + ' overlaps ' + keys[j] + ' ' + b[keys[j]]);
  return bad;
}

test('phone, upright and on its side: the menu opens above the exterior panel and the reel, and no pop-up covers another', { timeout: 240000 }, async (s) => {
  await s.open();
  await s.enter();
  const tour = await s.tour();
  const longest = [...tour.rooms.map((r) => r.label), ...tour.sweeps.map((x) => x.label), 'Right side · garage and kitchen'].sort((a, b) => b.length - a.length)[0];
  await s.page.keyboard.press('Shift');                 // the page's own first-run hint is over; this test puts it up itself
  await s.page.addStyleTag({ content: '#hint{transition:none!important}' });
  const bad = [];
  let lifted = 0;
  for (const vp of [s.viewport, LANDSCAPE]) {
    await s.page.setViewport(vp);
    const W = vp.width, H = vp.height, where = W + 'x' + H;
    for (const m of ['exterior', 'inside', 'dollhouse', 'floorplan']) {
      await s.page.evaluate((m) => window.TOUR.setMode(m, { instant: true }), m);
      await s.settle(8000);
      for (const reel of [false, true]) {
        if (await s.page.$eval('#reel', (r) => r.classList.contains('open')) !== reel) await s.press(s.testid('btn-rooms'));
        await s.waitFor((on) => { const r = document.getElementById('reel'), c = getComputedStyle(r); return r.classList.contains('open') === on && (on ? Number(c.opacity) > 0.99 && c.transform === 'none' : c.visibility === 'hidden'); }, { what: 'the reel to ' + (reel ? 'open' : 'close') }, reel);
        // chip and message up with their longest texts, the hint where it can show (inside, no reel)
        await s.page.evaluate((longest) => {
          const chip = document.getElementById('chip'), toast = document.getElementById('toast'), hint = document.getElementById('hint');
          chip.textContent = longest; chip.classList.add('show');
          toast.textContent = 'Something went wrong in the 3D view; it keeps running.'; toast.classList.add('show');
          hint.textContent = 'Tap a ring to move · drag to look'; hint.classList.toggle('show', document.body.classList.contains('mode-inside'));
        }, longest);
        await sleep(450);                               // chip and message fade in
        const tag = where + ' ' + m + (reel ? ' + reel' : '');
        bad.push(...overlaps(await overlay(s), W, H).map((x) => tag + ': ' + x));
        // the menu, by a real tap on its button (a tap is the visitor's first move: the hint goes)
        await s.page.evaluate(() => document.getElementById('hint').classList.remove('show'));
        const plain = await s.page.evaluate(() => { const b = document.getElementById('btnMenu').getBoundingClientRect(); return innerHeight - b.top + 8; });
        await s.press(s.testid('btn-menu'));
        await s.waitFor(() => document.getElementById('menu').classList.contains('open'), { what: 'the menu' });
        const b = await overlay(s);
        assert.ok(b.menu, tag + ': the menu is shown');
        bad.push(...overlaps(b, W, H).map((x) => tag + ' + menu: ' + x));
        if (H - b.menu[3] > plain + 20) lifted++;
        for (const id of ['menu-help', 'menu-screenshot']) await s.target(s.testid(id));      // both items can be tapped
        if (m === 'exterior' || reel) await s.shot((W > H ? 'side' : 'upright') + '-' + m + (reel ? '-reel' : '') + '-menu');
        await s.page.keyboard.press('Escape');
        await s.waitFor(() => !document.getElementById('menu').classList.contains('open'), { what: 'Escape to close the menu' });
      }
    }
  }
  assert.deepEqual(bad, []);
  assert.ok(lifted >= 4, 'where the exterior panel or the reel stands above the toolbar the menu opens above it (' + lifted + ' cases)');
  // The menu and a message never show together (on a phone on its side they would share a corner): a
  // message closes the menu, and opening the menu takes a message down.
  const shown = () => s.page.evaluate(() => ({ menu: document.getElementById('menu').classList.contains('open'), message: document.getElementById('toast').classList.contains('show'), chip: document.getElementById('chip').classList.contains('show') }));
  await s.press(s.testid('btn-menu'));
  await s.waitFor(() => document.getElementById('menu').classList.contains('open'), { what: 'the menu' });
  await s.page.evaluate(() => window.TOUR.viewer.emit('error', { error: new Error('raised by the test'), where: 'frame:test' }));
  assert.deepEqual(await shown(), { menu: false, message: true, chip: false }, 'a message closes the menu');
  await s.press(s.testid('btn-menu'));
  await s.waitFor(() => document.getElementById('menu').classList.contains('open'), { what: 'the menu' });
  assert.deepEqual(await shown(), { menu: true, message: false, chip: false }, 'opening the menu takes the message down');
  await s.page.keyboard.press('Escape');
  s.note('four views, reel closed and open, at 390x844 and at 844x390, each with and without the menu; the menu opened above a panel or the reel in ' + lifted + ' of 16');
});

test('phone: the reel names each place once, the entrance first, and no caption is cut off', async (s) => {
  await s.open();
  await s.enter();
  const tour = await s.tour();
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => { const r = document.getElementById('reel'); return r.classList.contains('open') && Number(getComputedStyle(r).opacity) > 0.99; }, { what: 'the reel' });
  const cards = await s.page.evaluate(() => [...document.querySelectorAll('[data-testid^="reel-"]')].map((c) => {
    const span = c.querySelector('span'), g = document.createRange();
    g.selectNodeContents(span);
    const t = g.getBoundingClientRect(), b = c.getBoundingClientRect(), cs = getComputedStyle(span);
    return {
      id: c.dataset.testid.slice(5), text: span.textContent.trim(), lines: Math.round(t.height / parseFloat(cs.lineHeight)),
      // the words lie inside the card and nothing of them is clipped or replaced by an ellipsis
      inside: t.left >= b.left - 0.5 && t.right <= b.right + 0.5 && t.top >= b.top - 0.5 && t.bottom <= b.bottom + 0.5,
      clipped: span.scrollWidth > span.clientWidth + 1 || span.scrollHeight > span.clientHeight + 1 || cs.textOverflow === 'ellipsis' && cs.overflow !== 'visible',
      share: t.height / b.height, font: parseFloat(cs.fontSize),
    };
  }));
  assert.equal(cards[0].id, tour.start, 'the reel starts at the entrance');
  const names = cards.map((c) => c.text);
  assert.deepEqual(names.filter((n, i) => names.indexOf(n) !== i), [], 'no place is in the reel twice');
  assert.deepEqual(cards.filter((c) => !c.text).map((c) => c.id), [], 'every card has a caption');
  assert.deepEqual(cards.filter((c) => !c.inside || c.clipped).map((c) => c.id + ' "' + c.text + '"'), [], 'captions cut off at 390 px');
  assert.deepEqual(cards.filter((c) => c.lines > 2 || c.share > 0.45 || c.font < 10).map((c) => c.id + ' "' + c.text + '": ' + c.lines + ' lines, ' + c.font + ' px'), [], 'captions stay small: at most two lines of readable type');
  const laundry = tour.rooms.find((r) => /laundry/i.test(r.label));
  if (laundry) assert.ok(cards.some((c) => c.id === laundry.sweep && /laundry/i.test(c.text)), 'the laundry closet has its card');
  else s.note('this data has no laundry closet yet (it comes with the final sweeps)');
  await s.page.$eval('#reelStrip', (e) => { e.scrollLeft = e.scrollWidth; });
  await s.shot('reel-end');
  s.note(cards.length + ' cards; two-line captions: ' + (cards.filter((c) => c.lines === 2).map((c) => c.text).join(', ') || 'none'));
});

test('phone: a double tap on a ring is one move, and the hint speaks of tapping', async (s) => {
  await s.open();
  const start = await s.enter();
  const hint = await s.waitFor(() => { const h = document.getElementById('hint'); return h && h.classList.contains('show') && Number(getComputedStyle(h).opacity) > 0.9 ? h.textContent.trim() : false; }, { what: 'the first-run hint', timeout: 5000 });
  assert.match(hint, /^Tap a ring to move\b/, 'on a touch screen the hint says "Tap"');
  await s.waitSharp(start);
  const to = (await s.sweeps()).find((x) => x.id === start).links[0];
  await sleep(800);
  const aim = await s.aimAt(to);
  assert.ok(aim && aim.x !== null, 'the ring of ' + to + ' is on screen');
  const before = await s.state();
  await s.startRecorder();
  await s.page.touchscreen.tap(aim.x, aim.y);
  await sleep(160);
  await s.page.touchscreen.tap(aim.x, aim.y);
  await s.waitRest(null, 8000);
  await sleep(700);
  const rec = await s.stopRecorder(), after = await s.state();
  const hops = [...new Set(rec.samples.filter((x) => x.tr).map((x) => x.tr.from + '>' + x.tr.to))];
  assert.deepEqual(hops, [start + '>' + to], 'the only hop flown');
  assert.equal(after.sweep, to, 'the camera is on the ring that was tapped, not back and not beyond');
  assert.equal(after.transition, null);
  assert.ok(Math.abs(after.fov - before.fov) < 0.01, 'a double tap does not zoom the view (' + before.fov.toFixed(1) + ' -> ' + after.fov.toFixed(1) + ' deg)');
  assert.equal(await s.page.evaluate(() => (window.visualViewport ? window.visualViewport.scale : 1)), 1, 'nor the page');
  assert.equal(await s.page.$eval('#hint', (h) => h.classList.contains('show')), false, 'the hint went with the first tap');
});

