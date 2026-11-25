'use strict';
// Smoke: the page loads, the 3D engine comes up, nothing is logged or fails to load, and the landing
// page's three buttons lead where they say. (Design section 6: window.TOUR, data-testid, no console
// errors, WebGL 2 required with a static fallback.)

const { suite, assert, sleep } = require('./lib/harness');
const { test } = suite(__filename);

const CONTRACT_API = ['getState', 'goTo', 'jumpTo', 'setLook', 'setMode', 'clickAt', 'sweeps', 'project', 'screenshot'];
const STATE_KEYS = ['engine', 'mode', 'sweep', 'transition', 'yaw', 'pitch', 'fov', 'pano', 'sweeps'];

test('the page loads: landing open, engine ready, window.TOUR complete', async (s) => {
  await s.open('', { ready: false });
  const first = await s.state();
  assert.equal(first.mode, 'landing', 'the tour starts on the landing page');
  assert.ok(['loading', 'ready'].includes(first.engine), 'engine is loading or ready, got ' + first.engine);
  await s.ready();
  const api = await s.page.evaluate((names) => names.filter((n) => typeof window.TOUR[n] !== 'function'), CONTRACT_API);
  assert.deepEqual(api, [], 'window.TOUR lacks ' + api.join(', '));
  const st = await s.state();
  assert.deepEqual(STATE_KEYS.filter((k) => !(k in st)), [], 'getState() lacks keys');
  assert.equal(st.engine, 'ready');
  assert.equal(st.mode, 'landing');
  assert.equal(st.transition, null);
  const tour = await s.tour();
  assert.equal(st.sweeps, tour.sweeps.length, 'getState().sweeps is the number of sweeps of tour.json');
  const list = await s.sweeps();
  assert.deepEqual(list.map((x) => x.id), tour.sweeps.map((x) => x.id), 'TOUR.sweeps() lists the sweeps of tour.json');
  for (const k of ['id', 'p', 'links', 'visible']) assert.ok(k in list[0], 'TOUR.sweeps() entries have ' + k);
  const landing = await s.page.evaluate(() => {
    const e = document.getElementById('landing'), b = e.getBoundingClientRect();
    return { covers: b.left <= 0 && b.top <= 0 && b.right >= innerWidth && b.bottom >= innerHeight, title: document.title, scroll: document.documentElement.scrollWidth <= innerWidth };
  });
  assert.ok(landing.covers, 'the landing page covers the viewport');
  assert.ok(landing.scroll, 'no horizontal scroll');
  assert.match(landing.title, /McKinley/);
  await s.shot('landing');
  s.note('gpu: ' + s.gl.renderer + ', MAX_TEXTURE_SIZE ' + s.gl.maxTextureSize);
});

test('nothing is logged and nothing fails to load on the way into the house', async (s) => {
  await s.open();
  await s.enter();
  const st = await s.waitSharp();
  assert.ok(st.pano.level, 'a panorama is on screen');
  await s.frames(30);
  assert.deepEqual(s.log.errors, [], 'console errors');
  assert.deepEqual(s.log.failed, [], 'failed requests');
  assert.deepEqual(s.log.warnings, [], 'console warnings');
  const bad = s.log.requests.filter((u) => !u.startsWith(new URL(s.page.url()).origin) && !u.startsWith('data:') && !u.startsWith('blob:'));
  assert.deepEqual(bad, [], 'the page loads everything from its own origin');
  // files of the old free walk that nothing uses any more
  assert.deepEqual(s.log.requests.filter((u) => /\/(adapt|collision)\.json/.test(u)), [], 'no request for adapt.json / collision.json');
});

test('landing: "Enter the house" opens the inside view on the start sweep', async (s) => {
  await s.open();
  const start = await s.enter();
  const st = await s.state();
  assert.equal(st.mode, 'inside');
  assert.equal(st.sweep, start);
  assert.equal(await s.page.$eval('#landing', (e) => getComputedStyle(e).display !== 'none' && getComputedStyle(e).visibility !== 'hidden' && e.classList.contains('open')), false, 'the landing page is gone');
  await s.waitSharp(start);
  await s.shot('inside-start');
});

test('landing: "Exterior" opens the exterior view', async (s) => {
  await s.open();
  await s.press(s.testid('landing-exterior'));
  await s.waitFor(() => window.TOUR.getState().mode === 'exterior', { what: "mode 'exterior'" });
});

test('landing: "Floor plan" opens the floor plan', async (s) => {
  await s.open();
  await s.press(s.testid('landing-plan'));
  await s.waitFor(() => window.TOUR.getState().mode === 'floorplan', { what: "mode 'floorplan'" });
  await s.frames(20);
  await s.shot('floorplan');
});

test('landing: a button pressed while the model still loads is honoured', async (s) => {
  await s.open('', { ready: false });
  await s.press(s.testid('landing-enter'));
  const tour = await s.tour();
  await s.waitRest(tour.start, 60000);
});

test('the controls of the contract carry their data-testid', async (s) => {
  await s.open();
  const ids = ['btn-rooms', 'btn-dollhouse', 'btn-floorplan', 'btn-inside', 'btn-exterior', 'btn-dimensions', 'btn-design', 'landing-enter', 'landing-exterior', 'landing-plan'];
  const found = await s.page.evaluate((ids) => Object.fromEntries(ids.map((k) => [k, document.querySelectorAll('[data-testid="' + k + '"]').length])), ids);
  assert.deepEqual(Object.entries(found).filter(([, n]) => n !== 1), [], 'each data-testid exists exactly once');
  const old = await s.page.evaluate(() => ['landing', 'planmodal', 'designmodal'].filter((id) => !document.getElementById(id)));
  assert.deepEqual(old, [], 'ids kept from the old page');
});

test('a link with ?sweep=ID opens the inside view on that sweep', async (s) => {
  const tour = await (async () => { await s.open(); return s.tour(); })();
  const id = tour.highlights.find((h) => h !== tour.start) || tour.sweeps[1].id;
  await s.open('?sweep=' + id);
  const st = await s.waitRest(id, 20000);
  assert.equal(st.sweep, id);
  assert.equal(st.mode, 'inside');
});

// The address bar hands out links to sweeps, and a round of changes can remove one (L5 stood where the
// living room's sofa is since the owner's seventh round). Such a link opens the front page like a plain
// visit: no error, and the way into the house works.
test('a link to a sweep that has left the tour opens the front page', async (s) => {
  const tour = await (async () => { await s.open(); return s.tour(); })();
  const gone = ['L5', 'ZZ'].find((id) => !tour.sweeps.some((x) => x.id === id));
  await s.open('?sweep=' + gone + '&yaw=40&pitch=-5');
  assert.equal(await s.page.$eval('#landing', (e) => e.classList.contains('open')), true, 'the landing page is up');
  const st = await s.state();
  assert.notEqual(st.sweep, gone);
  assert.notEqual(st.mode, 'inside', 'not inside on a sweep the link did not name');
  const start = await s.enter();
  assert.equal((await s.state()).sweep, start, '"Enter the house" opens on the start sweep');
  s.note('?sweep=' + gone + ' -> the front page, then ' + start);
});

// The address bar is a link to the place the visitor is at: ?sweep=ID&yaw=&pitch= (degrees) at rest inside,
// ?mode=dollhouse|floorplan|exterior otherwise. It is rewritten in place (history.replaceState), so the
// tour never piles up history entries, and other parameters of the address stay.
test('the address bar follows the visitor without adding history entries, and its link opens the same view', async (s) => {
  const deg = (r) => Math.round(Math.atan2(Math.sin(r), Math.cos(r)) * 180 / Math.PI);
  const params = () => s.page.evaluate(() => Object.fromEntries(new URLSearchParams(location.search)));
  const until = async (ok, what) => {
    for (const t0 = Date.now(); ;) {
      const q = await params();
      if (ok(q)) return q;
      if (Date.now() - t0 > 6000) assert.fail('timed out waiting for ' + what + '; the address has ' + JSON.stringify(q));
      await sleep(50);
    }
  };
  await s.open('?pano=2k');                             // a parameter of another kind: it must survive
  const history0 = await s.page.evaluate(() => history.length);
  assert.deepEqual(await params(), { pano: '2k' }, 'on the landing page the address names no place');
  const start = await s.enter();
  let q = await until((q) => q.sweep === start, 'the address to name the start sweep');
  assert.ok(!('mode' in q), 'inside, the address names the sweep, not a mode: ' + JSON.stringify(q));
  // a move by a ring click
  const all = await s.sweeps(), to = all.find((x) => x.id === start).visible[0];
  await s.clickRing(to);
  await s.waitRest(to, 8000);
  await until((q) => q.sweep === to, 'the address to follow the move to ' + to);
  // looking around
  await s.page.evaluate(() => window.TOUR.setLook(2.0, -0.2));
  q = await until((q) => q.yaw === String(deg(2.0)) && q.pitch === String(deg(-0.2)), 'the address to carry the view direction');
  assert.equal(q.sweep, to);
  // the other views
  for (const m of ['dollhouse', 'floorplan', 'exterior']) {
    await s.press(s.testid('btn-' + m));
    q = await until((q) => q.mode === m, 'the address to name the ' + m + ' view');
    assert.ok(!('sweep' in q) && !('yaw' in q) && !('pitch' in q), 'outside the inside view the address names the mode only: ' + JSON.stringify(q));
  }
  await s.press('[data-exterior="rear"]');
  await until((q) => q.mode === 'exterior' && q.view === 'rear', 'the address to name the exterior view');
  // back inside: the sweep and the direction the visitor left
  await s.press(s.testid('btn-inside'));
  await s.waitRest(to, 15000);
  q = await until((q) => q.sweep === to && !('mode' in q) && !('view' in q), 'the address to name the sweep again');
  assert.deepEqual([q.yaw, q.pitch, q.pano], [String(deg(2.0)), String(deg(-0.2)), '2k'], 'direction and the other parameter are in the address: ' + JSON.stringify(q));
  assert.equal(await s.page.evaluate(() => history.length), history0, 'no history entry was added (history.replaceState)');
  // the link opens the same view
  const link = await s.page.evaluate(() => location.search);
  await s.open(link);
  const st = await s.waitRest(to, 20000);
  assert.equal(st.mode, 'inside');
  assert.ok(Math.abs(deg(st.yaw) - deg(2.0)) <= 1 && Math.abs(deg(st.pitch) - deg(-0.2)) <= 1, 'the link opens on the same direction: yaw ' + deg(st.yaw) + ', pitch ' + deg(st.pitch) + ' deg');
  s.note('link: ' + link);
  // a link with yaw and pitch of its own
  await s.open('?sweep=' + start + '&yaw=-120&pitch=12');
  const own = await s.waitRest(start, 20000);
  assert.ok(Math.abs(deg(own.yaw) + 120) <= 1 && Math.abs(deg(own.pitch) - 12) <= 1, '&yaw=&pitch= are honoured on load: yaw ' + deg(own.yaw) + ', pitch ' + deg(own.pitch) + ' deg');
  // and a link to a view
  await s.open('?mode=floorplan');
  await s.waitFor(() => window.TOUR.getState().mode === 'floorplan', { what: "mode 'floorplan' from the link" });
});

test('without WebGL 2 the page shows the static fallback with the design stills', {
  before: (page) => page.evaluateOnNewDocument(() => {
    const real = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type, ...rest) { return /^(webgl|experimental-webgl)/.test(type) ? null : real.call(this, type, ...rest); };
  }),
}, async (s) => {
  s.allow(/3D view unavailable|WebGL/i);
  await s.open('', { ready: false });
  await s.waitFor(() => window.TOUR.getState().engine === 'failed', { what: "engine === 'failed'", timeout: 20000 });
  const view = await s.waitFor(() => {
    const stills = [...document.querySelectorAll('img')].filter((i) => /assets\/design\//.test(i.src) && i.complete && i.naturalWidth > 0 && i.getBoundingClientRect().width > 40 && !i.closest('#landing'));
    const note = [...document.querySelectorAll('p, div, section')].find((e) => /WebGL/i.test(e.textContent) && e.getBoundingClientRect().height > 0 && !e.closest('#landing, .modal'));
    return stills.length >= 3 && note ? { stills: stills.length, landing: document.getElementById('landing').classList.contains('open') } : false;
  }, { what: 'a visible fallback message and at least three design stills', timeout: 20000 });
  assert.equal(view.landing, false, 'the landing page does not hide the fallback');
  await s.shot('fallback');
  // the two sheets work without the 3D view
  const sheets = await s.page.evaluate(() => { window.MEASURE.open(); const a = !!document.querySelector('#planmodal.open'); window.DESIGN.open(); return a && !!document.querySelector('#designmodal.open'); });
  assert.ok(sheets, 'Dimensions and Design open without WebGL');
  s.note(view.stills + ' design stills shown');
});
