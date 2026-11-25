'use strict';
// The chrome around the picture (design section 2, items 7 and 8): the dark round toolbar, the
// highlight reel, the room-name chip, the Dimensions and Design sheets and the menu.
// Item ids (rooms, doors, design views) are read from the page's data; only the ids the design names
// are written here (M13 and D17 of the laundry closet, M05, M14 and D18 of the primary suite).

const { suite, assert, sleep } = require('./lib/harness');
const { test } = suite(__filename);

const BUTTONS = ['btn-rooms', 'btn-dollhouse', 'btn-floorplan', 'btn-inside', 'btn-exterior', 'btn-dimensions', 'btn-design'];
const modal = (s) => s.page.evaluate(() => { const m = document.querySelector('.modal.open'); return m ? m.id : null; });
const luma = (rgb) => { const m = /rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?/.exec(rgb) || []; return { l: 0.2126 * m[1] + 0.7152 * m[2] + 0.0722 * m[3], a: m[4] === undefined ? 1 : Number(m[4]) }; };

test('minimal dark chrome: title top left, round dark buttons bottom left and right, the active view white', async (s) => {
  await s.open();
  await s.enter();
  await s.waitSharp();
  // the buttons change colour over 150 ms when the view changes: look once that is over
  await s.page.evaluate(() => Promise.all(document.getAnimations().filter((a) => a instanceof CSSTransition).map((a) => a.finished.catch(() => {}))));
  const { width: W, height: H } = s.viewport;
  const ui = await s.page.evaluate((ids) => {
    const box = (e) => { const b = e.getBoundingClientRect(), c = getComputedStyle(e); return { x: b.left, y: b.top, w: b.width, h: b.height, bg: c.backgroundColor, radius: parseFloat(c.borderTopLeftRadius), color: c.color, shown: c.display !== 'none' && c.visibility !== 'hidden' && b.width > 0 }; };
    const out = { buttons: {}, scroll: document.documentElement.scrollWidth - innerWidth };
    for (const id of ids) { const e = document.querySelector('[data-testid="' + id + '"]'); out.buttons[id] = e ? Object.assign(box(e), { label: e.getAttribute('aria-label') || e.textContent.trim() }) : null; }
    const t = [...document.querySelectorAll('h1')].find((e) => e.getBoundingClientRect().width > 0 && !e.closest('#landing, .modal, #fallback'));
    out.title = t ? Object.assign(box(t), { text: t.textContent.trim() }) : null;
    return out;
  }, BUTTONS);
  const tour = await s.tour();
  assert.ok(ui.title, 'a title is shown');
  assert.equal(ui.title.text, tour.title);
  assert.ok(ui.title.x < W * 0.2 && ui.title.y < H * 0.12, 'the title sits top left');
  assert.ok(ui.title.h <= 40, 'the title is small (' + ui.title.h + ' px high)');
  assert.ok(ui.scroll <= 0, 'no horizontal scroll');
  const bad = [];
  for (const [id, b] of Object.entries(ui.buttons)) {
    if (!b || !b.shown) { bad.push(id + ': not shown'); continue; }
    if (b.x < 0 || b.y < 0 || b.x + b.w > W || b.y + b.h > H) bad.push(id + ': outside the viewport');
    if (Math.abs(b.w - b.h) > 1.5 || b.radius < b.w / 2 - 1) bad.push(id + ': not round (' + b.w + ' x ' + b.h + ', radius ' + b.radius + ')');
    if (b.w < 32 || b.w > 56) bad.push(id + ': ' + b.w + ' px (32-56 expected)');
    if (b.y < H * 0.8) bad.push(id + ': not at the bottom');
    if (!b.label) bad.push(id + ': no accessible name');
    const left = ['btn-rooms', 'btn-dollhouse', 'btn-floorplan', 'btn-inside'].includes(id);
    if (left ? b.x > W * 0.4 : b.x < W * 0.6) bad.push(id + ': on the wrong side');
  }
  assert.deepEqual(bad, []);
  const active = luma(ui.buttons['btn-inside'].bg), idle = luma(ui.buttons['btn-dollhouse'].bg);
  assert.ok(active.l > 200 && active.a > 0.8, 'the active view\'s button is white (' + ui.buttons['btn-inside'].bg + ')');
  assert.ok(idle.l < 90 || idle.a < 0.3, 'the other buttons are dark or clear (' + ui.buttons['btn-dollhouse'].bg + ')');
  await s.shot('chrome');
});

test('the highlight reel opens, shows the rooms and a thumbnail goes to its sweep', async (s) => {
  await s.open();
  await s.enter();
  const tour = await s.tour();
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => { const r = document.getElementById('reel'); if (!r) return false; const b = r.getBoundingClientRect(), c = getComputedStyle(r); return r.classList.contains('open') && b.top < innerHeight - 20 && Number(c.opacity) > 0.95; }, { what: 'the reel to slide up' });
  const cards = await s.page.evaluate(() => [...document.querySelectorAll('[data-testid^="reel-"]')].map((e) => { const i = e.querySelector('img'), b = e.getBoundingClientRect(); return { id: e.dataset.testid.slice(5), text: e.textContent.trim(), onScreen: b.left >= 0 && b.right <= innerWidth, loaded: !!i && i.complete && i.naturalWidth > 0 }; }));
  assert.deepEqual(cards.map((c) => c.id), tour.highlights, 'one card per highlight, in the order of tour.json');
  const labels = new Map(tour.sweeps.map((x) => [x.id, x.label]));
  assert.deepEqual(cards.filter((c) => c.text !== labels.get(c.id)).map((c) => c.id + ': "' + c.text + '"'), [], 'cards carry the sweep labels');
  await s.waitFor(() => [...document.querySelectorAll('[data-testid^="reel-"]')].filter((e) => { const b = e.getBoundingClientRect(); return b.left >= 0 && b.right <= innerWidth; }).every((e) => { const i = e.querySelector('img'); return i && i.complete && i.naturalWidth > 0; }), { what: 'the thumbnails on screen to load' });
  if ('reel' in (await s.state())) assert.equal((await s.state()).reel, true, 'getState().reel');
  await s.shot('reel');
  const id = tour.highlights.find((h) => h !== tour.start && cards.find((c) => c.id === h).onScreen);
  await s.press(s.testid('reel-' + id));
  const st = await s.waitRest(id, 15000);
  assert.equal(st.sweep, id);
  await s.waitFor((id) => document.querySelector('[data-testid="reel-' + id + '"]').classList.contains('active'), { what: 'the card of the current room to be marked' }, id);
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => !document.getElementById('reel').classList.contains('open'), { what: 'the reel to close' });
});

test('a room-name chip fades in on arrival and out again', async (s) => {
  await s.open();
  const start = await s.enter();
  const tour = await s.tour();
  const roomLabel = (id) => { const sw = tour.sweeps.find((x) => x.id === id), r = tour.rooms.find((x) => x.id === sw.room); return r ? r.label : sw.label; };
  const chipText = () => s.waitFor(() => { const c = document.getElementById('chip'); if (!c) return false; const st = getComputedStyle(c); return c.classList.contains('show') && Number(st.opacity) > 0.6 && c.textContent.trim() ? c.textContent.trim() : false; }, { what: 'the room chip', timeout: 4000 });
  assert.equal(await chipText(), roomLabel(start), 'the chip names the room of the start sweep');
  await s.waitFor(() => Number(getComputedStyle(document.getElementById('chip')).opacity) < 0.05, { what: 'the chip to fade out', timeout: 6000 });
  // walk to the nearest sweep that stands in another room
  const all = new Map(tour.sweeps.map((x) => [x.id, x]));
  const seen = new Set([start]), q = [start];
  let other = null;
  while (q.length && !other) { const a = q.shift(); for (const b of all.get(a).links) { if (seen.has(b)) continue; seen.add(b); q.push(b); if (roomLabel(b) !== roomLabel(start)) { other = b; break; } } }
  assert.ok(other, 'a sweep in another room');
  await s.page.evaluate((id) => { window.TOUR.goTo(id); }, other);
  await s.waitRest(other, 15000);
  assert.equal(await chipText(), roomLabel(other), 'the chip names the new room on arrival');
});

test('Dimensions: select a room and a door on the plan, lists, units, CSV, Visit in 3D', async (s) => {
  await s.open();
  await s.enter();
  const dir = await s.downloads();
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  const data = await s.page.evaluate(() => ({ rooms: window.MEASURE.data.rooms.map((x) => ({ id: x.id, name: x.name, node: x.node })), doors: window.MEASURE.data.doors.map((x) => ({ id: x.id, name: x.name, node: x.node })), windows: window.MEASURE.data.windows.length }));
  const total = data.rooms.length + data.doors.length + data.windows;
  const hits = await s.page.$$eval('#dimensionPlan [data-measure]', (e) => new Set(e.map((x) => x.dataset.measure)).size);
  assert.equal(hits, total, 'the plan has one target per room, window and door');
  const pick = async (item) => {
    await s.press('#dimensionPlan [data-measure="' + item.id + '"]');
    await s.waitFor((id) => window.MEASURE.selected === id, { what: item.id + ' to be selected' }, item.id);
    return s.page.evaluate((id) => ({ title: document.getElementById('dimensionDetailTitle').textContent, marked: [...document.querySelectorAll('#dimensionPlan [data-measure="' + id + '"]')].some((e) => e.classList.contains('selected')), detail: document.getElementById('dimensionDetail').textContent }), item.id);
  };
  const room = data.rooms[Math.min(6, data.rooms.length - 1)];
  let r = await pick(room);
  assert.equal(r.title, room.name);
  assert.ok(r.marked, 'the room is highlighted on the plan');
  assert.match(r.detail, /Clear width/);
  const start = (await s.tour()).start;
  const door = data.doors.find((d) => d.node !== start) || data.doors[0];
  r = await pick(door);
  assert.equal(r.title, door.name);
  assert.match(r.detail, /Opening width/);
  await s.shot('door-selected');
  // schedules
  await s.page.$eval('#planmodal', (e) => { e.scrollTop = 0; });
  await s.press('[data-dimension-tab="doors"]');
  assert.equal(await s.page.$$eval('#dimensionListing tbody tr', (e) => e.length), data.doors.length, 'the Doors tab lists every door');
  await s.page.select('#dimensionUnits', 'mm');
  assert.match(await s.page.$eval('#dimensionDetail', (e) => e.textContent), /\d mm/, 'millimetres');
  await s.page.select('#dimensionUnits', 'ft');
  // CSV
  await s.press('#dimensionCsv');
  const csv = (await s.waitFile(dir + '/1095-mckinley-review-dimensions.csv')).toString('utf8');
  const lines = csv.split('\r\n');
  assert.equal(lines.length, total + 1, 'the CSV has a header and one line per item');
  assert.match(lines[0], /^"Category","ID","Description"/);
  assert.ok(lines.some((l) => l.includes('"' + door.id + '"')), 'the CSV contains ' + door.id);
  // Visit in 3D
  await s.press('#dimensionVisit');
  const st = await s.waitRest(door.node, 15000);
  assert.equal(await modal(s), null, 'the sheet closes');
  assert.equal(st.sweep, door.node, '"Visit in 3D" stands on the sweep of ' + door.id);
});

// The laundry closet (M13) is drawn inside Bedroom 4 and its doors (D17) on the foyer side of the wall
// between them: three targets on a few square inches of the plan, each of which has to take its own click.
test('Dimensions: the laundry closet M13 inside Bedroom 4 and its doors D17 are picked by their own clicks', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  const data = await s.page.evaluate(() => { const M = window.MEASURE.data, pick = (x) => x && { id: x.id, name: x.name, node: x.node, bounds: x.bounds_ft }; return { room: pick(M.rooms.find((x) => x.id === 'M13')), door: pick(M.doors.find((x) => x.id === 'D17')), rooms: M.rooms.map(pick) }; });
  assert.ok(data.room && data.door, 'the schedule has M13 and D17');
  const pick = async (id) => {
    await s.press('#dimensionPlan [data-measure="' + id + '"]');           // (fails when another target covers its middle)
    await s.waitFor((id) => window.MEASURE.selected === id, { what: id + ' to be selected' }, id);
    return s.page.evaluate((id) => ({ title: document.getElementById('dimensionDetailTitle').textContent, detail: document.getElementById('dimensionDetail').textContent, marked: [...document.querySelectorAll('#dimensionPlan .selected')].map((e) => e.dataset.measure) }), id);
  };
  // the room the closet is cut out of: the measured room whose rectangle holds the closet's
  const [x0, x1, z0, z1] = data.room.bounds;
  const host = data.rooms.find((r) => r.id !== 'M13' && r.bounds[0] <= x0 + 0.01 && r.bounds[1] >= x1 - 0.01 && r.bounds[2] <= z0 + 0.01 && r.bounds[3] >= z1 - 0.01);
  if (host) {
    const h = await pick(host.id);
    assert.equal(h.title, host.name, 'a click in the middle of ' + host.name + ' still selects it');
  } else s.note('the closet does not lie inside another measured room in this data');
  const r = await pick('M13');
  assert.equal(r.title, data.room.name);
  assert.deepEqual(r.marked, ['M13'], 'the closet alone is highlighted on the plan');
  assert.match(r.detail, /Clear width/);
  await s.shot('M13-selected');
  const d = await pick('D17');
  assert.equal(d.title, data.door.name);
  assert.deepEqual(d.marked, ['D17']);
  assert.match(d.detail, /Opening width/);
  await s.shot('D17-selected');
  await s.press('#dimensionVisit');
  const st = await s.waitRest(data.door.node, 15000);
  assert.equal(await modal(s), null, 'the sheet closes');
  const sw = (await s.tour()).sweeps.find((x) => x.id === data.door.node);
  assert.ok(Math.abs(Math.atan2(Math.sin(st.yaw - sw.yaw * Math.PI / 180), Math.cos(st.yaw - sw.yaw * Math.PI / 180))) < 0.02, '"Visit in 3D" opens ' + sw.id + ' on its own direction, toward the doors');
  await s.settle(8000);
  await s.shot('D17-visit');
});

// The walk-in closet (M05) and the vestibule (M14) of the owner's sixth round stand side by side, the
// pocket door (D18) in the 5 inch wall between them: its tag must not lie under either room's name, and
// each of the three takes its own click. The sizes are the ones on the architect's sheet.
test('Dimensions: the walk-in closet M05, the vestibule M14 and the pocket door D18 between them are picked by their own clicks', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  const data = await s.page.evaluate(() => { const M = window.MEASURE.data, pick = (x) => x && { id: x.id, name: x.name, node: x.node, bounds: x.bounds_ft }; return { closet: pick(M.rooms.find((x) => x.id === 'M05')), vestibule: pick(M.rooms.find((x) => x.id === 'M14')), door: pick(M.doors.find((x) => x.id === 'D18')) }; });
  assert.ok(data.closet && data.vestibule && data.door, 'the schedule has M05, M14 and D18');
  const pick = async (id) => {
    await s.press('#dimensionPlan [data-measure="' + id + '"]');           // (fails when another target or a name covers its middle)
    await s.waitFor((id) => window.MEASURE.selected === id, { what: id + ' to be selected' }, id);
    return s.page.evaluate((id) => ({ title: document.getElementById('dimensionDetailTitle').textContent, detail: document.getElementById('dimensionDetail').textContent, marked: [...document.querySelectorAll('#dimensionPlan .selected')].map((e) => e.dataset.measure) }), id);
  };
  const c = await pick('M05');
  assert.equal(c.title, data.closet.name);
  assert.match(c.title, /walk-in closet/i);
  assert.deepEqual(c.marked, ['M05'], 'the closet alone is highlighted on the plan');
  assert.match(c.detail, /Clear width\s*6′1″/, 'clear width 6\'-1"');
  assert.match(c.detail, /Clear depth\s*8′0″/, 'clear depth 8\'-0"');
  await s.shot('M05-selected');
  const v = await pick('M14');
  assert.equal(v.title, data.vestibule.name);
  assert.deepEqual(v.marked, ['M14'], 'the vestibule alone is highlighted');
  assert.match(v.detail, /Clear width\s*4′7″/, 'clear width 4\'-7"');
  await s.shot('M14-selected');
  const d = await pick('D18');
  assert.equal(d.title, data.door.name);
  assert.deepEqual(d.marked, ['D18'], 'the pocket door alone is highlighted');
  assert.match(d.detail, /Opening width/);
  assert.match(d.detail, /pocket/i, 'the detail says what kind of door it is');
  await s.shot('D18-selected');
  // "Visit in 3D" from the closet stands inside it
  await pick('M05');
  await s.press('#dimensionVisit');
  const st = await s.waitRest(data.closet.node, 15000);
  assert.equal(await modal(s), null, 'the sheet closes');
  const sw = (await s.tour()).sweeps.find((x) => x.id === st.sweep), [x0, x1, z0, z1] = data.closet.bounds;
  assert.ok(sw.p[0] > x0 && sw.p[0] < x1 && sw.p[2] > z0 && sw.p[2] < z1, '"Visit in 3D" of M05 stands inside the closet (' + sw.id + ')');
  assert.equal(await s.page.$eval('#chip', (e) => e.textContent), data.closet.name, 'the room chip names the closet');
  await s.settle(8000);
  await s.shot('M05-visit');
});

test('Design: the tabs follow design.json and each shows its picture and text', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-design'));
  await s.waitFor(() => !!document.querySelector('#designmodal.open'), { what: 'the Design sheet' });
  const design = await s.json('assets/data/design.json');
  const tabs = await s.page.$$eval('#designmodal [data-design]', (e) => e.map((b) => ({ id: b.dataset.design, text: b.textContent.trim() })));
  assert.deepEqual(tabs.map((t) => t.id), design.order, 'tab order');
  assert.deepEqual(tabs.map((t) => t.text), design.order.map((k) => design.views[k].label), 'tab labels');
  for (const k of design.order) {
    await s.press('#designmodal [data-design="' + k + '"]');
    const seen = await s.waitFor((title) => { const i = document.getElementById('designHero'); return document.getElementById('designTitle').textContent === title && i.complete && i.naturalWidth > 0 ? { src: i.getAttribute('src'), text: document.getElementById('designText').textContent.length } : false; }, { what: 'the picture of design view ' + k, timeout: 10000 }, design.views[k].title);
    assert.ok(seen.src.startsWith(design.views[k].image), k + ' shows ' + design.views[k].image);
    assert.ok(seen.text > 20, k + ' has its text');
  }
  await s.shot('design');
  // into the 3D view from a room's tab
  const k = design.order.find((x) => design.views[x].node && !['front', 'roof'].includes(x));
  await s.press('#designmodal [data-design="' + k + '"]');
  await s.press('#designVisit');
  const st = await s.waitRest(design.views[k].node, 15000);
  assert.equal(st.sweep, design.views[k].node);
  assert.equal(await modal(s), null);
});

// The owner's rounds of changes (design.json `owner_changes`) are listed under the tabs, newest first, each
// under its own heading: "Seventh round · 2026-11-21", never "Round 7 round".
test('Design: the owner\'s rounds are listed newest first, each under its ordinal and date, with every entry', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-design'));
  await s.waitFor(() => !!document.querySelector('#designmodal.open'), { what: 'the Design sheet' });
  const design = await s.json('assets/data/design.json'), rounds = design.owner_changes || [];
  assert.ok(rounds.length >= 1, 'design.json has the owner\'s rounds');
  await s.press('#designChanges summary');
  await s.waitFor(() => document.getElementById('designChanges').open, { what: 'the list of changes to open' });
  const shown = await s.page.$$eval('#designChangeList h4', (hs) => hs.map((h) => ({ head: h.textContent.trim(), items: [...h.nextElementSibling.querySelectorAll('li')].map((li) => li.textContent) })));
  assert.equal(shown.length, rounds.length, 'one heading per round');
  const words = ['', 'First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh', 'Eighth', 'Ninth', 'Tenth'];
  rounds.slice().reverse().forEach((r, i) => {
    assert.equal(shown[i].head, (words[r.round] ? words[r.round] + ' round' : 'Round ' + r.round) + (r.date ? ' · ' + r.date : ''), 'heading of round ' + r.round);
    assert.deepEqual(shown[i].items, r.changes, 'the entries of round ' + r.round);
  });
  assert.deepEqual(shown.filter((x) => /^Round \d+ round/.test(x.head)).map((x) => x.head), [], 'headings that say "round" twice');
  // the newest round is readable: its heading and first entry are inside the sheet when scrolled to
  await s.page.$eval('#designChangeList h4', (h) => h.scrollIntoView({ block: 'start', behavior: 'instant' }));
  await s.frames(2);
  const box = await s.page.$eval('#designChangeList h4', (h) => { const b = h.getBoundingClientRect(); return { top: b.top, bottom: b.bottom, h: innerHeight }; });
  assert.ok(box.top >= -1 && box.bottom <= box.h + 1, 'the newest round\'s heading is on screen (top ' + box.top.toFixed(1) + ', bottom ' + box.bottom.toFixed(1) + ' of ' + box.h + ' px)');
  await s.shot('design-changes');
  s.note('rounds shown: ' + shown.map((x) => x.head + ' (' + x.items.length + ')').join(', '));
});

test('menu: opens, "Controls & about" lists the rooms, Escape closes', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-menu'));
  await s.waitFor(() => { const m = document.getElementById('menu'); return m && m.classList.contains('open') && m.getBoundingClientRect().height > 20; }, { what: 'the menu' });
  await s.shot('menu');
  await s.press(s.testid('menu-help'));
  await s.waitFor(() => !!document.querySelector('#infomodal.open'), { what: 'the about sheet' });
  const m = await s.json('assets/data/measurements.json');
  assert.equal(await s.page.$$eval('#modelAudit tbody tr', (e) => e.length), m.audit.length, 'the room table lists every measured room');
  await s.page.keyboard.press('Escape');
  await s.waitFor(() => !document.querySelector('.modal.open'), { what: 'Escape to close the sheet' });
  assert.equal((await s.state()).mode, 'inside', 'and the tour is where it was');
});

test('menu: "Save screenshot" downloads the view as a PNG', async (s) => {
  await s.open();
  await s.enter();
  await s.waitSharp();
  const dir = await s.downloads();
  await s.press(s.testid('btn-menu'));
  await s.press(s.testid('menu-screenshot'));
  const png = await s.waitFile(dir + '/1095-mckinley-view.png');
  const img = require('./lib/panoref').decodePng(png);
  assert.ok(img.width >= s.viewport.width && img.height >= s.viewport.height, 'a picture of the view (' + img.width + ' x ' + img.height + ')');
  assert.ok(require('./lib/panoref').frameStats(img).std > 12, 'not blank');
});

test('keys are left alone while a sheet is open', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  const before = await s.state();
  await s.page.keyboard.press('ArrowUp');
  await s.page.keyboard.down('ArrowRight');
  await sleep(300);
  await s.page.keyboard.up('ArrowRight');
  await sleep(500);
  const after = await s.state();
  assert.equal(after.sweep, start, 'the arrow keys do not move the tour behind a sheet');
  assert.equal(after.transition, null);
  assert.ok(Math.abs(after.yaw - before.yaw) < 1e-6, 'nor turn it');
});

// ---- keyboard and focus -----------------------------------------------------------------------
const focused = (s) => s.page.evaluate(() => {
  const a = document.activeElement, m = a && a.closest('.modal.open');
  return { tag: a ? a.tagName : null, id: a ? a.id : null, testid: a && a.dataset ? a.dataset.testid || null : null, modal: m ? m.id : null, menu: !!(a && a.closest('#menu')), reel: !!(a && a.closest('#reel')) };
});

test('a sheet keeps the keyboard: the page behind is out of reach and Escape gives the focus back', async (s) => {
  await s.open();
  await s.enter();
  for (const [button, sheet] of [['btn-design', 'designmodal'], ['btn-dimensions', 'planmodal']]) {
    await s.page.focus(s.testid(button));
    await s.page.keyboard.press('Enter');
    await s.waitFor((id) => !!document.querySelector('#' + id + '.open'), { what: 'the sheet ' + sheet }, sheet);
    assert.equal((await focused(s)).modal, sheet, 'the focus moves into the sheet');
    // Tab through more stops than the sheet has: the focus may pass the browser's own controls
    // (<body> here) but never lands on the page behind
    const stops = await s.page.$$eval('#' + sheet + ' button, #' + sheet + ' a[href], #' + sheet + ' input, #' + sheet + ' select, #' + sheet + ' summary, #' + sheet + ' [tabindex]', (e) => e.length);
    const outside = [];
    for (let i = 0; i < stops + 6; i++) {
      await s.page.keyboard.press('Tab');
      const f = await focused(s);
      if (f.modal !== sheet && f.tag !== 'BODY') outside.push(f.testid || f.id || f.tag);
    }
    assert.deepEqual(outside, [], sheet + ': Tab reached the page behind the sheet');
    const behind = await s.page.evaluate((id) => [...document.body.children].filter((e) => e.id !== id && !e.inert && !['SCRIPT', 'NOSCRIPT'].includes(e.tagName) && !['toast', 'error'].includes(e.id) && e.querySelector('button, a[href], canvas, input')).map((e) => e.id || e.className), sheet);
    assert.deepEqual(behind, [], sheet + ': everything behind the sheet is inert');
    await s.page.keyboard.press('Escape');
    await s.waitFor(() => !document.querySelector('.modal.open'), { what: 'Escape to close the sheet' });
    assert.equal((await focused(s)).testid, button, 'the focus returns to the button that opened the sheet');
    assert.equal(await s.page.evaluate(() => [...document.body.children].filter((e) => e.inert && e.id !== 'reel').length), 0, 'and the page is usable again');
  }
});

test('a message raised from a sheet shows above it', async (s) => {
  await s.open();
  await s.enter();
  await s.press(s.testid('btn-dimensions'));
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet' });
  await s.page.evaluate(() => { window.open = () => null; });            // a blocked pop-up
  await s.press('#dimensionPrint');
  const t = await s.waitFor(() => {
    const e = document.getElementById('toast'), c = getComputedStyle(e), m = getComputedStyle(document.querySelector('.modal.open')), b = e.getBoundingClientRect();
    return e.classList.contains('show') && Number(c.opacity) > 0.9 ? { text: e.textContent, z: Number(c.zIndex), sheet: Number(m.zIndex), top: b.top, bottom: b.bottom, left: b.left, right: b.right } : false;
  }, { what: 'the message about the blocked pop-up' });
  assert.match(t.text, /new tab/i);
  assert.ok(t.z > t.sheet, 'the message is stacked above the sheet (z-index ' + t.z + ' over ' + t.sheet + ')');
  assert.ok(t.top >= 0 && t.left >= 0 && t.right <= s.viewport.width && t.bottom <= s.viewport.height, 'and on screen');
  await s.shot('toast-over-sheet');
});

test('menu and reel by keyboard: arrows walk the menu, Escape and Tab close it, the reel takes the focus', async (s) => {
  await s.open();
  const start = await s.enter();
  await s.page.focus(s.testid('btn-menu'));
  await s.page.keyboard.press('Enter');
  assert.equal((await focused(s)).testid, 'menu-help', 'the menu opens on its first item');
  const before = await s.state();
  await s.page.keyboard.press('ArrowDown');
  assert.equal((await focused(s)).testid, 'menu-screenshot', 'ArrowDown goes to the next item');
  await s.page.keyboard.press('ArrowDown');
  assert.equal((await focused(s)).testid, 'menu-help', 'and wraps');
  await s.page.keyboard.press('ArrowUp');
  assert.equal((await focused(s)).testid, 'menu-screenshot');
  await sleep(400);
  const after = await s.state();
  assert.ok(after.sweep === before.sweep && after.transition === null, 'the arrow keys stay in the menu: the view behind does not move');
  await s.page.keyboard.press('Escape');
  assert.equal(await s.page.$eval('#menu', (m) => m.classList.contains('open')), false, 'Escape closes the menu');
  assert.equal((await focused(s)).testid, 'btn-menu', 'and the focus is back on its button');
  await s.page.keyboard.press('Enter');
  await s.page.keyboard.down('Shift'); await s.page.keyboard.press('Tab'); await s.page.keyboard.press('Tab'); await s.page.keyboard.up('Shift');
  assert.equal(await s.page.$eval('#menu', (m) => m.classList.contains('open')), false, 'the menu closes when the focus moves on');
  // the reel: opened by keyboard the focus goes to its cards, Escape brings it back to the button
  await s.page.focus(s.testid('btn-rooms'));
  await s.page.keyboard.press('Enter');
  await s.waitFor(() => document.getElementById('reel').classList.contains('open'), { what: 'the reel' });
  assert.equal((await focused(s)).reel, true, 'the focus is on a card of the reel');
  await s.page.keyboard.press('Escape');
  await s.waitFor(() => !document.getElementById('reel').classList.contains('open'), { what: 'Escape to close the reel' });
  assert.equal((await focused(s)).testid, 'btn-rooms');
  assert.equal((await s.state()).sweep, start);
});

test('a sheet opened from the menu gives the focus back to the menu button; Escape closes a reel opened with the mouse', async (s) => {
  await s.open();
  await s.enter();
  await s.page.focus(s.testid('btn-menu'));
  await s.page.keyboard.press('Enter');
  await s.page.keyboard.press('Enter');                 // "Controls & about", the menu's first item
  await s.waitFor(() => !!document.querySelector('#infomodal.open'), { what: 'the about sheet' });
  assert.equal((await focused(s)).modal, 'infomodal', 'the focus is in the sheet');
  assert.equal(await s.page.$eval('#menu', (m) => m.classList.contains('open')), false, 'the menu has closed');
  await s.page.keyboard.press('Escape');
  await s.waitFor(() => !document.querySelector('.modal.open'), { what: 'Escape to close the sheet' });
  assert.equal((await focused(s)).testid, 'btn-menu', 'the focus returns to the menu button');
  // a sheet opened from another sheet: Escape goes back to where the first one came from
  await s.page.focus(s.testid('btn-design'));
  await s.page.keyboard.press('Enter');
  await s.waitFor(() => !!document.querySelector('#designmodal.open'), { what: 'the Design sheet' });
  await s.page.evaluate(() => document.getElementById('designMeasure').click());
  await s.waitFor(() => !!document.querySelector('#planmodal.open'), { what: 'the Dimensions sheet from the Design sheet' });
  await s.page.keyboard.press('Escape');
  await s.waitFor(() => !document.querySelector('.modal.open'), { what: 'Escape to close the sheet' });
  assert.equal((await focused(s)).testid, 'btn-design', 'the focus returns to the button that opened the first sheet');
  // the reel, opened with the mouse
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => document.getElementById('reel').classList.contains('open'), { what: 'the reel' });
  await s.page.keyboard.press('Escape');
  await s.waitFor(() => !document.getElementById('reel').classList.contains('open'), { what: 'Escape to close the reel' });
  assert.equal(await s.page.$eval('[data-testid="btn-rooms"]', (b) => b.getAttribute('aria-expanded')), 'false');
});

test('every button, link and field has an accessible name, in every state of the page', async (s) => {
  await s.open();
  const audit = (where) => s.page.evaluate((where) => {
    const text = (e) => (e ? e.textContent : '') || '';
    const name = (e) => {
      const by = (e.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean).map((id) => text(document.getElementById(id))).join(' ');
      const alt = [...e.querySelectorAll('img[alt]')].map((i) => i.alt).join(' ');
      const label = e.labels && e.labels.length ? text(e.labels[0]) : '';
      return (e.getAttribute('aria-label') || by || label || text(e) || alt || e.getAttribute('title') || '').replace(/\s+/g, ' ').trim();
    };
    const tag = (e) => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.dataset && e.dataset.testid ? '[' + e.dataset.testid + ']' : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/).join('.') : '');
    const heard = (e) => !e.closest('[aria-hidden="true"]');         // what assistive technology is told about
    const controls = [...document.querySelectorAll('button, [role="button"], [role="menuitem"], a[href], select, input, textarea, summary')].filter(heard);
    return {
      count: controls.length,
      nameless: controls.filter((e) => !name(e)).map((e) => where + ': ' + tag(e)),
      // an icon in a named control is decoration: it must not be read out as an unnamed graphic
      icons: [...document.querySelectorAll('button svg, [role="menuitem"] svg')].filter((v) => v.getAttribute('aria-hidden') !== 'true').map((v) => where + ': icon in ' + tag(v.closest('button, [role="menuitem"]'))),
      // dialogs and landmark groups say what they are
      regions: [...document.querySelectorAll('[role="dialog"], [role="menu"], [role="group"], nav, section[aria-label], canvas')].filter(heard).filter((e) => !name(e) || (e.hasAttribute('aria-label') && !e.getAttribute('role') && !/^(NAV|SECTION|HEADER|MAIN|ASIDE|FORM|BUTTON|A|INPUT|SELECT|IMG|CANVAS)$/.test(e.tagName))).map((e) => where + ': ' + tag(e)),
    };
  }, where);
  const bad = [];
  let most = 0;
  const look = async (where) => { const a = await audit(where); bad.push(...a.nameless, ...a.icons, ...a.regions); most = Math.max(most, a.count); };
  await look('landing');
  await s.enter();
  await s.waitSharp();
  await s.frames(20);                                   // the ring buttons are placed once the view stands still
  await look('inside');
  await s.press(s.testid('btn-rooms'));
  await look('reel');
  await s.press(s.testid('btn-rooms'));
  await s.press(s.testid('btn-menu'));
  await look('menu');
  await s.press(s.testid('menu-help'));
  await s.waitFor(() => !!document.querySelector('#infomodal.open'), { what: 'the about sheet' });
  await look('about');
  await s.page.evaluate(() => { window.MEASURE.open(); window.MEASURE.list('doors'); });
  await look('dimensions');
  await s.page.evaluate(() => { window.DESIGN.open('front'); });
  await look('design');
  await s.page.keyboard.press('Escape');
  for (const m of ['dollhouse', 'floorplan', 'exterior']) {
    await s.page.evaluate((m) => window.TOUR.setMode(m, { instant: true }), m);
    await s.settle(8000);
    await look(m);
  }
  assert.deepEqual([...new Set(bad)], []);
  // the canvas itself: focusable, named, and told to pass the keys on
  const view = await s.page.$eval('#view', (c) => ({ label: c.getAttribute('aria-label'), role: c.getAttribute('role'), tab: c.tabIndex }));
  assert.ok(view.label && view.tab === 0, 'the view can take the focus and has a name');
  assert.equal(view.role, 'application', 'the view passes the arrow keys to the tour');
  s.note('up to ' + most + ' controls on the page, all named');
});

// ---- first-run hint ---------------------------------------------------------------------------
const hintState = (s) => s.page.evaluate(() => {
  const h = document.getElementById('hint');
  if (!h) return null;
  const c = getComputedStyle(h), r = h.getBoundingClientRect();
  return { text: h.textContent.trim(), up: h.classList.contains('show') && c.visibility !== 'hidden' && c.display !== 'none' && Number(c.opacity) > 0.9, opacity: Number(c.opacity), events: c.pointerEvents, box: [r.left, r.top, r.right, r.bottom] };
});
const hintUp = (s) => s.waitFor(() => { const h = document.getElementById('hint'), c = h && getComputedStyle(h); return !!h && h.classList.contains('show') && c.visibility !== 'hidden' && Number(c.opacity) > 0.9; }, { what: 'the first-run hint', timeout: 5000 });
const hintGone = (s, timeout) => s.waitFor(() => { const h = document.getElementById('hint'); return !h.classList.contains('show') && Number(getComputedStyle(h).opacity) < 0.05; }, { what: 'the hint to go', timeout });

test('first-run hint: shown when the visitor first stands inside, gone with their first move, never again in the session', async (s) => {
  await s.open();
  assert.equal((await hintState(s)).up, false, 'no hint on the landing page');
  await s.enter();
  await hintUp(s);
  const h = await hintState(s), { width: W, height: H } = s.viewport;
  assert.match(h.text, /^Click a ring to move\b.*\bdrag to look$/i, 'the hint says how to move and how to look: "' + h.text + '"');
  assert.equal(h.events, 'none', 'the hint lets clicks through to the view');
  assert.ok(h.box[0] >= 0 && h.box[1] >= 0 && h.box[2] <= W && h.box[3] <= H, 'the hint is on screen');
  assert.ok(h.box[3] - h.box[1] <= 44 && h.box[2] - h.box[0] <= 360, 'one small line (' + Math.round(h.box[2] - h.box[0]) + ' x ' + Math.round(h.box[3] - h.box[1]) + ' px)');
  const others = await s.page.evaluate(() => ['.bar-left', '.bar-right', '#title', '#chip'].map((sel) => { const r = document.querySelector(sel).getBoundingClientRect(); return [sel, r.left, r.top, r.right, r.bottom]; }));
  for (const [sel, l, t, r, b] of others) assert.ok(h.box[2] <= l || h.box[0] >= r || h.box[3] <= t || h.box[1] >= b, 'the hint keeps clear of ' + sel);
  await s.shot('hint');
  // the first thing the visitor does: a drag to look
  await s.drag([W * 0.5, H * 0.4], [W * 0.5 - 140, H * 0.4], { steps: 6 });
  await hintGone(s, 1500);
  // not again: another sweep, another view and back
  const start = (await s.tour()).start, to = (await s.sweeps()).find((x) => x.id === start).visible[0];
  await s.clickRing(to);
  await s.waitRest(to, 8000);
  await s.press(s.testid('btn-dollhouse'));
  await s.waitFor(() => window.TOUR.getState().mode === 'dollhouse', { what: 'the dollhouse' });
  await s.press(s.testid('btn-inside'));
  await s.waitRest(null, 15000);
  await sleep(1500);
  assert.equal((await hintState(s)).up, false, 'the hint does not come back on the next visit to the inside view');
  // nor after a reload in the same tab (the session remembers)
  await s.page.reload({ waitUntil: 'domcontentloaded' });
  await s.waitFor(() => !!window.TOUR, { what: 'window.TOUR after the reload', timeout: 30000 });
  await s.ready();
  await s.page.evaluate(() => window.TOUR.setMode('inside'));
  await s.waitRest(null, 20000);
  await sleep(1800);
  assert.equal((await hintState(s)).up, false, 'the hint does not come back after a reload in the same session');
});

test('first-run hint: fades by itself after a few seconds', async (s) => {
  await s.open();
  const start = (await s.tour()).start;
  await s.open('?sweep=' + start);                      // a link straight into the house
  await s.waitRest(start, 20000);
  await hintUp(s);
  const t0 = Date.now();
  await hintGone(s, 10000);
  const ms = Date.now() - t0;
  assert.ok(ms >= 2500 && ms <= 9000, 'the hint stays a few seconds, then goes without anything being done (' + ms + ' ms)');
  const st = await s.state();
  assert.equal(st.mode, 'inside');
  assert.equal(st.transition, null);
});

// ---- layout -----------------------------------------------------------------------------------
test('from 320 px to 2560 px nothing of the chrome overlaps or leaves the window, in every view', { timeout: 240000 }, async (s) => {
  await s.open();
  await s.enter();
  // the first-run hint is put up by this test wherever the inside view is on: the page's own has to be over
  await s.page.keyboard.press('Shift');
  await s.page.addStyleTag({ content: '#hint{transition:none!important}' });
  const tour = await s.tour();
  const longest = [...tour.rooms.map((r) => r.label), ...tour.sweeps.map((x) => x.label)].sort((a, b) => b.length - a.length)[0];
  // boxes of everything that sits over the picture, with the longest room name in the chip and a long message up
  const boxes = () => s.page.evaluate((longest) => {
    const chip = document.getElementById('chip'), toast = document.getElementById('toast');
    chip.textContent = longest; chip.classList.add('show');
    toast.textContent = 'Something went wrong in the 3D view; it keeps running.'; toast.classList.add('show');
    const text = (el) => { const g = document.createRange(); g.selectNodeContents(el); return g.getBoundingClientRect(); };
    const out = {}, round = (r) => [Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)];
    const a = text(document.querySelector('#title h1')), b = text(document.querySelector('#title p'));
    out.title = round({ left: Math.min(a.left, b.left), top: a.top, right: Math.max(a.right, b.right), bottom: b.bottom });
    const hint = document.getElementById('hint');
    hint.textContent = 'Click a ring to move · drag to look'; hint.classList.toggle('show', document.body.classList.contains('mode-inside'));
    for (const [k, sel] of Object.entries({ chip: '#chip', toast: '#toast', hint: '#hint', 'left bar': '.bar-left', 'right bar': '.bar-right', 'exterior panel': '#exteriorControls', reel: '#reelStrip' })) {
      const e = document.querySelector(sel), c = getComputedStyle(e), r = e.getBoundingClientRect();
      if (c.display === 'none' || c.visibility === 'hidden' || !r.width || !r.height) continue;
      if (k === 'reel' && !document.getElementById('reel').classList.contains('open')) continue;
      out[k] = round(r);
    }
    return out;
  }, longest);
  const area = (a, b) => Math.max(0, Math.min(a[2], b[2]) - Math.max(a[0], b[0])) * Math.max(0, Math.min(a[3], b[3]) - Math.max(a[1], b[1]));
  const bad = [];
  for (const [w, h] of [[320, 568], [360, 740], [390, 844], [600, 900], [641, 800], [700, 800], [768, 1024], [844, 390], [1024, 768], [1280, 720], [1281, 720], [1920, 1080], [2560, 1440]]) {
    await s.page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
    for (const m of ['inside', 'dollhouse', 'floorplan', 'exterior']) {
      await s.page.evaluate((m) => window.TOUR.setMode(m, { instant: true }), m);
      for (const reel of [false, true]) {
        await s.page.evaluate((on) => { if (document.getElementById('reel').classList.contains('open') !== on) document.getElementById('btnRooms').click(); }, reel);
        await sleep(330);                                // the reel's slide
        const b = await boxes(), keys = Object.keys(b), where = w + 'x' + h + ' ' + m + (reel ? ' + reel' : '');
        for (const k of keys) if (k !== 'reel' && (b[k][0] < 0 || b[k][1] < 0 || b[k][2] > w || b[k][3] > h)) bad.push(where + ': ' + k + ' leaves the window ' + b[k]);
        for (let i = 0; i < keys.length; i++) for (let j = i + 1; j < keys.length; j++) if (area(b[keys[i]], b[keys[j]]) > 0) bad.push(where + ': ' + keys[i] + ' ' + b[keys[i]] + ' overlaps ' + keys[j] + ' ' + b[keys[j]]);
      }
    }
  }
  assert.deepEqual(bad, []);
});

test('the open reel stands where the toolbar tips would show: they are not drawn', async (s) => {
  await s.open();
  await s.enter();
  const tip = () => s.page.$eval('[data-testid="btn-dollhouse"]', (b) => { const c = getComputedStyle(b, '::after'); return { content: c.content, shown: c.display !== 'none' }; });
  // a device without hover (headless Chrome is one) never shows the tips: undo that rule, so that the
  // reel's own rule is what this test sees
  await s.page.addStyleTag({ content: '.rb[data-tip]::after{display:block}' });
  const closed = await tip();
  assert.match(closed.content, /Dollhouse/, 'the button carries its tip');
  assert.equal(closed.shown, true, 'with the reel closed the tip can show');
  await s.press(s.testid('btn-rooms'));
  await s.waitFor(() => document.getElementById('reel').classList.contains('open'), { what: 'the reel' });
  assert.equal((await tip()).shown, false, 'no tip while the reel is open');
});

test('floor plan: a room name never runs over its pill, at any zoom', async (s) => {
  for (const size of [{ width: 1400, height: 850 }, { width: 1920, height: 1080 }, { width: 1024, height: 700 }]) {
    await s.page.setViewport(Object.assign({ deviceScaleFactor: 1 }, size));
    await s.open('?mode=floorplan');
    await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'floorplan' && x.floorplan && !x.floorplan.flight; }, { what: 'the floor plan', timeout: 30000 });
    await s.settle(8000);
    for (let step = 0; step < 4; step++) {
      const names = await s.page.evaluate(() => [...document.querySelectorAll('#planLabels .plan-label:not(.off)')].map((e) => ({ text: e.textContent, need: e.scrollWidth, has: e.clientWidth })));
      assert.ok(step > 0 || names.length >= 4, 'the framed plan shows room names (' + names.length + ')');
      assert.deepEqual(names.filter((n) => n.need > n.has).map((n) => n.text + ' needs ' + n.need + ' px, has ' + n.has), [], size.width + ' x ' + size.height + ', zoom step ' + step + ': names wider than their pill');
      await s.wheel(-160);
      await sleep(700);
    }
  }
});

// Room rectangles overlap: the laundry closet is cut out of Bedroom 4's, the hall's reaches over its
// neighbours. Each name sits in the middle of its own rectangle, so two of them could land on top of
// each other; and a click on the name of a room nobody can stand in has to show that room.
// namesAround zooms the floor plan in on one room, step by step, in a window of the given size: at no
// step do two names overlap; the room's own name shows from some step on, stands on its own room, and
// a click on it enters on the room's sweep. choose(tour, {size, holds}) -> {room, host}: the room, and
// the room around it whose name should stay beside it (or null). Returns a line for the report.
async function namesAround(s, view, choose) {
  const size = (r) => (r.bounds[2] - r.bounds[0]) * (r.bounds[3] - r.bounds[1]);
  const holds = (r, x, z, tol = 0) => x >= r.bounds[0] - tol && x <= r.bounds[2] + tol && z >= r.bounds[1] - tol && z <= r.bounds[3] + tol;
  const shown = () => s.page.evaluate(() => [...document.querySelectorAll('#planLabels .plan-label:not(.off)')].map((e) => { const b = e.getBoundingClientRect(); return { id: e.dataset.room, text: e.textContent, box: [b.left, b.top, b.right, b.bottom] }; }));
  await s.page.setViewport(Object.assign({ deviceScaleFactor: 1 }, view));
  await s.open('?mode=floorplan');
  await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'floorplan' && x.floorplan && !x.floorplan.flight; }, { what: 'the floor plan', timeout: 30000 });
  await s.settle(8000);
  const tour = await s.tour();
  const { room, host } = choose(tour, { size, holds });
  let own = null, together = 0;
  for (let step = 0; step < 9; step++) {
    const names = await shown(), where = view.width + ' x ' + view.height + ', zoom step ' + step;
    const over = [];
    for (let i = 0; i < names.length; i++) for (let j = i + 1; j < names.length; j++) {
      const a = names[i].box, b = names[j].box;
      if (Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > 0.5 && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > 0.5) over.push('"' + names[i].text + '" and "' + names[j].text + '"');
    }
    assert.deepEqual(over, [], where + ': names on top of each other');
    const mine = names.find((n) => n.id === room.id);
    if (mine && !own) own = Object.assign({ step }, mine);
    if (mine && host && names.some((n) => n.id === host.id)) together++;
    if (own && step >= own.step + 2) break;
    const p = await s.page.evaluate((at) => window.TOUR.viewer.project([at[0], 0, at[1]], 20), room.at);
    await s.wheel(-200, Math.max(30, Math.min(view.width - 30, p.x)), Math.max(90, Math.min(view.height - 120, p.y)));
    await s.waitFor(() => { const f = window.TOUR.getState().floorplan; return !!f && !f.flight; }, { what: 'the zoom' });
    await sleep(600);
  }
  assert.ok(own, view.width + ' x ' + view.height + ': the name of ' + room.label + ' shows once the plan is zoomed in on it');
  // the name stands on its own room
  const on = await s.page.evaluate((b) => { const v = window.TOUR.viewer, a = v.project([b[0], 0, b[1]], 60), c = v.project([b[2], 0, b[3]], 60); return a && c ? [Math.min(a.x, c.x), Math.min(a.y, c.y), Math.max(a.x, c.x), Math.max(a.y, c.y)] : null; }, room.bounds);
  const label = (await shown()).find((n) => n.id === room.id);
  assert.ok(label && on, 'the name of ' + room.label + ' is still shown after two more steps');
  const mid = [(label.box[0] + label.box[2]) / 2, (label.box[1] + label.box[3]) / 2];
  assert.ok(mid[0] >= on[0] && mid[0] <= on[2] && mid[1] >= on[1] && mid[1] <= on[3], 'the name of ' + room.label + ' stands on its own room');
  assert.ok(label.box[2] - label.box[0] <= on[2] - on[0] + 1, 'and is not wider than it (' + Math.round(label.box[2] - label.box[0]) + ' px on ' + Math.round(on[2] - on[0]) + ' px)');
  await s.shot('names-' + room.id + '-' + view.width);
  // a click on the name: the room's sweep, and for a room nobody stands in the view toward it
  await s.press(s.testid('plan-label-' + room.id));
  const st = await s.waitRest(room.sweep, 12000), sw = tour.sweeps.find((x) => x.id === room.sweep);
  if (!holds(room, sw.p[0], sw.p[2])) {
    const want = Math.atan2(room.at[0] - sw.p[0], -(room.at[1] - sw.p[2])), off = Math.abs(Math.atan2(Math.sin(st.yaw - want), Math.cos(st.yaw - want))) * 180 / Math.PI;
    assert.ok(off < 20, 'the name of ' + room.label + ' leads to ' + sw.id + ', which stands outside it, looking at the room (' + off.toFixed(1) + ' degrees off)');
  }
  return view.width + ' px: "' + own.text + '" from zoom step ' + own.step + (host ? ', together with "' + host.label + '" in ' + together + ' steps' : '') + ', click -> ' + st.sweep;
}
const VIEWS = [{ width: 1400, height: 850 }, { width: 1024, height: 700 }, { width: 390, height: 844 }];

test('floor plan: names never cover one another; a room inside another room shows its own name when zoomed in', { timeout: 240000 }, async (s) => {
  const seen = [];
  for (const view of VIEWS) {
    seen.push(await namesAround(s, view, (tour, { size, holds }) => {
      const inner = tour.rooms.filter((r) => tour.rooms.some((o) => o !== r && size(o) > size(r) && holds(o, r.bounds[0], r.bounds[1], 0.01) && holds(o, r.bounds[2], r.bounds[3], 0.01)));
      // zoom in on the smallest room inside another one (without one: on the smallest room of the house)
      const room = (inner.length ? inner : tour.rooms).slice().sort((a, b) => size(a) - size(b))[0];
      const host = inner.length ? tour.rooms.filter((o) => o !== room && holds(o, room.bounds[0], room.bounds[1], 0.01) && holds(o, room.bounds[2], room.bounds[3], 0.01)).sort((a, b) => size(a) - size(b))[0] : null;
      return { room, host };
    }));
  }
  s.note(seen.join('; '));
});

// The vestibule of the primary suite (M14, owner's sixth round) is 4'-7" wide between the walk-in closet
// and the hall, with the primary bathroom south of it: three names within a few feet. Its name may stay
// hidden while the room is too narrow for it on screen; zoomed in it shows, on its own room, beside the
// closet's name and never over it or the bathroom's.
test('floor plan: the vestibule\'s name shows when zoomed in, beside the walk-in closet\'s, and covers no other name', { timeout: 240000 }, async (s) => {
  const seen = [];
  for (const view of VIEWS) {
    seen.push(await namesAround(s, view, (tour) => {
      const room = tour.rooms.find((r) => r.tag === 'M14'), host = tour.rooms.find((r) => r.tag === 'M05');
      assert.ok(room && host, 'tour.json has the vestibule (M14) and the walk-in closet (M05)');
      assert.match(room.label, /vestibule/i);
      return { room, host };
    }));
  }
  // (on a phone the plan is zoomed about its left edge, where the suite is, and the closet may leave the screen first)
  for (const line of seen.filter((_, i) => VIEWS[i].width >= 1000)) assert.match(line, /together with "[^"]+" in [1-9]/, 'the closet\'s name shows beside the vestibule\'s at some zoom step (' + line + ')');
  s.note(seen.join('; '));
});
