'use strict';
// Loading: what a visitor on a slow line sees. Files are held back with request interception (the
// server is local), so every test here states its own "network".
//   * a landing button pressed before the page has wired itself is honoured;
//   * the inside view opens on its panorama while the 3D model is still downloading: no rings yet,
//     moves are dissolves, the other views wait and open when the model is in;
//   * nothing is fetched for closed sheets, the closed reel or a view nobody chose while the model loads;
//   * with panorama files seconds late the bare baked model is never shown: not in a flight through
//     several sweeps, not by a far jump, not by a fly-in from the dollhouse;
//   * sharper levels of a sweep the visitor has left are not downloaded to the end, decoded or uploaded;
//   * a WebGL context lost while the model downloads leaves the fallback page, for good.

const { suite, assert, sleep, get, config } = require('./lib/harness');
const { test } = suite(__filename);

// Holds back the requests whose URL matches one of `rules` ([RegExp, ms] pairs; the first match counts).
// Returns the log of what was asked for: [{url, at (ms since the hold was set up), held}].
async function hold(page, rules) {
  const seen = [], t0 = Date.now();
  await page.setRequestInterception(true);
  page.on('request', async (req) => {
    const url = req.url(), rule = rules.find(([re]) => re.test(url));
    seen.push({ url, at: Date.now() - t0, held: rule ? rule[1] : 0 });
    if (rule && rule[1] > 0) await sleep(rule[1]);
    req.continue().catch(() => {});                      // (the page may have dropped the request meanwhile)
  });
  return seen;
}
const MODEL = /assets\/model\/house\.glb/;
const PANO = /assets\/panos\/(2k|4k|8k)\//;
const byId = (list) => new Map(list.map((x) => [x.id, x]));
// tour.json, read before the page is opened (to decide what to hold back)
const tourFile = async () => JSON.parse((await get(config.base + 'assets/data/tour.json')).body.toString('utf8'));
// Counts, for every frame the page draws, how much of it is the bare bake (the engine's test hook paints
// it magenta) and what the engine projects. stop() returns {frames, bare (frames with more than 2 % bake),
// worst (largest share), rows: [{t, mode, tr, flight, slots, has, bake}]}; `watch` = a sweep id whose
// presence in the engine is recorded with each frame.
async function watchBake(s, watch = null) {
  await s.page.evaluate((watch) => {
    const v = window.TOUR.viewer, e = v.engine, c = document.createElement('canvas');
    c.width = 96; c.height = 54;
    const g = c.getContext('2d', { willReadFrequently: true });
    const W = window.__bake = { rows: [] };
    e.setDebug({ bake: true });
    W.off = v.on('frame', () => {
      const st = v.state(), own = st[st.mode], info = e.projectionInfo();
      g.drawImage(v.canvas, 0, 0, 96, 54);
      const d = g.getImageData(0, 0, 96, 54).data;
      let n = 0;
      for (let i = 0; i < d.length; i += 4) if (d[i] > 200 && d[i + 1] < 70 && d[i + 2] > 200) n++;
      W.rows.push({
        t: Math.round(performance.now()), mode: st.mode, tr: st.transition ? { from: st.transition.from, to: st.transition.to, fade: !!st.transition.fade } : null,
        flight: own && own.flight ? own.flight.t : null, slots: info.slots.map((x) => x.id), on: info.on, has: watch ? !!e.hasPanorama(watch) : null, bake: n / (d.length / 4),
      });
    });
  }, watch);
  return async () => {
    const rows = await s.page.evaluate(() => { const W = window.__bake; W.off(); window.TOUR.viewer.engine.setDebug({}); window.TOUR.viewer.engine.invalidate(); return W.rows; });
    return { rows, frames: rows.length, bare: rows.filter((r) => r.bake > 0.02).length, worst: Math.max(0, ...rows.map((r) => r.bake)) };
  };
}

for (const [button, mode] of [['landing-enter', 'inside'], ['landing-plan', 'floorplan']]) {
  test('landing: "' + button + '" pressed before the page has wired itself opens the ' + mode + ' view, not the exterior', {
    before: (page) => hold(page, [[/assets\/data\/tour\.json/, 1500]]),
  }, async (s) => {
    await s.page.goto(config.base, { waitUntil: 'domcontentloaded' });
    // ui.js is in (the landing buttons work from then on), the data is not: window.TOUR does not exist yet
    await s.waitFor(() => performance.getEntriesByType('resource').some((r) => /\/tour\/ui\.js/.test(r.name)), { what: 'ui.js loaded' });
    await sleep(250);
    assert.equal(await s.page.evaluate(() => typeof window.TOUR), 'undefined', 'the page has not wired itself yet when the button is pressed');
    await s.press(s.testid(button));
    assert.equal(await s.page.evaluate(() => document.getElementById('landing').classList.contains('open')), false, 'the landing page closes at once');
    await s.waitFor(() => !!window.TOUR && window.TOUR.getState().engine === 'ready', { what: 'engine ready', timeout: 60000 });
    const st = await s.waitFor((m) => { const x = window.TOUR.getState(); return x.mode === m && (m !== 'inside' || (!x.transition && x.pano.level)) ? x : null; }, { what: 'mode ' + mode, timeout: 20000 }, mode);
    await sleep(600);                                    // nothing may take the choice back afterwards
    const end = await s.state(), tour = await s.tour();
    assert.equal(end.mode, mode, 'the visitor is where the button said, not in the ' + end.mode + ' view');
    if (mode === 'inside') assert.equal(st.sweep, tour.start, 'on the start sweep');
  });
}

test('the inside view opens on its panorama while the 3D model still downloads; rings, glides and the other views follow when it is in', {
  timeout: 120000, before: (page) => hold(page, [[MODEL, 5000]]),
}, async (s) => {
  await s.open('', { ready: false });
  const tour = await s.tour(), all = byId(await s.sweeps());
  const t0 = Date.now();
  await s.press(s.testid('landing-enter'));
  const st = await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'inside' && x.resting && x.pano.level ? x : null; }, { what: 'the first panorama', timeout: 4000 });
  const took = Date.now() - t0;
  assert.equal(st.engine, 'loading', 'the panorama is up while the model is still loading');
  assert.equal(st.sweep, tour.start);
  assert.ok(took < 3000, 'first panorama ' + took + ' ms after the click (the model is held back 5 s)');
  await s.frames(4);
  const early = await s.page.evaluate(() => ({
    rings: window.TOUR.rings().length, note: document.getElementById('modelNote').classList.contains('show'), text: document.getElementById('modelNote').textContent,
    hint: document.getElementById('hint').classList.contains('show'), loading: getComputedStyle(document.getElementById('loading')).visibility,
  }));
  assert.equal(early.rings, 0, 'no floor rings before the model is in (they lie on its surfaces)');
  assert.ok(early.note && /3D model/.test(early.text), 'a small note says the model is loading: "' + early.text + '"');
  assert.equal(early.hint, false, 'the hint about the rings waits for the rings');
  await s.shot('inside-before-the-model');
  // looking around works
  await s.drag([700, 400], [520, 410]);
  const turned = await s.state();
  assert.ok(Math.abs(turned.yaw - st.yaw) > 0.1, 'a drag looks around');
  // a step key moves, as a dissolve (a glide needs the model)
  const b = all.get(all.get(tour.start).links[0]).p, a = all.get(tour.start).p;
  await s.page.evaluate((yaw) => window.TOUR.setLook(yaw, 0), Math.atan2(b[0] - a[0], -(b[2] - a[2])));
  await s.frames(2);
  await s.page.evaluate(() => { window.__tr = []; window.TOUR.viewer.on('frame', () => { const t = window.TOUR.getState().transition; if (t) window.__tr.push(!!t.fade); }); });
  await s.page.keyboard.press('ArrowUp');
  const moved = await s.waitFor((id) => { const x = window.TOUR.getState(); return x.sweep !== id && !x.transition && x.pano.level ? x : null; }, { what: 'a step forward from ' + tour.start, timeout: 6000 }, tour.start);
  assert.equal(moved.engine, 'loading', 'the step was made before the model arrived');
  const at = moved.sweep;
  const kinds = await s.page.evaluate(() => window.__tr);
  assert.ok(kinds.length > 0 && kinds.every(Boolean), 'the move is a dissolve, not a glide (' + kinds.filter((k) => !k).length + ' of ' + kinds.length + ' frames gliding)');
  // another view has to wait, and says so
  await s.press(s.testid('btn-dollhouse'));
  await s.frames(3);
  const parked = await s.page.evaluate(() => ({ mode: window.TOUR.getState().mode, toast: document.getElementById('toast').classList.contains('show') ? document.getElementById('toast').textContent : '' }));
  assert.equal(parked.mode, 'inside', 'the dollhouse waits for the model');
  assert.match(parked.toast, /dollhouse.*3D model/i, 'a message says why: "' + parked.toast + '"');
  await s.ready(60000);
  await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'dollhouse' && x.dollhouse && !x.dollhouse.flight; }, { what: 'the dollhouse, once the model is in', timeout: 20000 });
  assert.equal(await s.page.evaluate(() => document.getElementById('modelNote').classList.contains('show')), false, 'the note is gone');
  // back inside: rings, and a glide
  await s.press(s.testid('btn-inside'));
  await s.waitRest(at, 20000);
  const back = all.get(at).links[0];
  const aim = await s.aimAt(back);
  assert.ok(aim && aim.x !== null, 'with the model in, the ring of ' + back + ' is on screen');
  await s.page.evaluate(() => { window.__tr.length = 0; });
  await s.clickAt(aim.x, aim.y);
  await s.waitRest(back, 8000);
  const glide = await s.page.evaluate(() => window.__tr);
  assert.ok(glide.length > 0 && glide.every((k) => !k), 'and a click on it glides there');
  s.note('first panorama ' + took + ' ms after the click with the model 5 s late');
});

test('a link to a sweep shows its panorama before the 3D model is in, and the address keeps the place', {
  before: (page) => hold(page, [[MODEL, 4000]]),
}, async (s) => {
  const tour = await tourFile();
  const id = tour.highlights.find((x) => x !== tour.start) || tour.start;
  const t0 = Date.now();
  await s.open('?sweep=' + id, { ready: false });
  const st = await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'inside' && x.resting && x.pano.level ? x : null; }, { what: 'the panorama of the link', timeout: 3500 });
  assert.equal(st.engine, 'loading');
  assert.equal(st.sweep, id);
  s.note('panorama of ?sweep=' + id + ' after ' + (Date.now() - t0) + ' ms, the model 4 s late');
  await s.ready(60000);
  await s.waitFor(() => document.getElementById('hint').classList.contains('show'), { what: 'the hint, now that the rings are there', timeout: 5000 });
  const end = await s.state();
  assert.equal(end.sweep, id);
  assert.ok(end.resting, 'still at rest on the pure panorama');
  assert.match(await s.page.evaluate(() => location.search), new RegExp('sweep=' + id), 'the address still names the sweep');
});

test('while the model downloads nothing is fetched for closed sheets, the closed reel or a view nobody chose', {
  before: async (page, s) => { s.asked = await hold(page, [[MODEL, 3000]]); },
}, async (s) => {
  await s.open('', { ready: false });
  await s.ready(60000);
  await sleep(1200);                                     // what the page does behind the landing page once the model is in
  const urls = s.asked.map((r) => r.url.replace(/^https?:\/\/[^/]+\//, '').split('?')[0]);
  const early = s.asked.filter((r) => r.at < 3000).map((r) => r.url.replace(/^https?:\/\/[^/]+\//, ''));
  assert.deepEqual(early.filter((u) => /assets\/references\//.test(u)), [], 'the Design sheet is closed: no reference photo before the model is in');
  assert.deepEqual(early.filter((u) => /assets\/thumbs\//.test(u)), [], 'the reel is closed: no thumbnail before the model is in');
  assert.deepEqual(early.filter((u) => /assets\/exterior\/.*\.(webp|jpe?g|png|avif)/.test(u)), [], 'no exterior frame before the model is in');
  const front = early.filter((u) => /assets\/design\/front\./.test(u));
  assert.ok(front.length <= 1, 'the front render is fetched once (the landing picture), not a second time for the closed Design sheet: ' + front.join(', '));
  assert.deepEqual(urls.filter((u) => /assets\/references\//.test(u)), [], 'still no reference photo behind the landing page');
  const frames = urls.filter((u) => /assets\/exterior\/.*\.(webp|jpe?g|png|avif)/.test(u));
  assert.ok(frames.length <= 1, 'behind the landing page the exterior loads the one frame it stands on, got ' + frames.length + ': ' + frames.join(', '));
  // the visitor chooses the exterior: now it loads what it needs, and the Design sheet its pictures when opened
  await s.press(s.testid('landing-exterior'));
  await s.waitFor(() => { const e = window.TOUR.getState().exterior; return e && e.photo && e.photo.on && e.photo.weight > 0.98 && !e.photo.settling; }, { what: 'the exterior on its frame', timeout: 20000 });
  await s.settle(8000);
  await s.press(s.testid('btn-design'));
  await s.waitFor(() => { const i = document.getElementById('designHero'); return i.complete && i.naturalWidth > 0; }, { what: 'the Design sheet shows its picture' });
  s.note('requests before the model was in: ' + early.length + '; exterior frames behind the landing page: ' + frames.length);
});

test('panorama files seconds late: a flight through several sweeps and a far jump never show the bare model', {
  timeout: 150000,
}, async (s) => {
  const tour = await tourFile();
  const asked = await hold(s.page, [[new RegExp('assets/panos/(2k|4k|8k)/' + tour.start + '\\.'), 0], [PANO, 2500]]);
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  // the farthest sweep the page still flies to (not more than five hops over the links), and one beyond for the jump
  const hops = new Map([[start, 0]]), q = [start];
  while (q.length) { const a = q.shift(); for (const b of all.get(a).links) if (!hops.has(b)) { hops.set(b, hops.get(a) + 1); q.push(b); } }
  const near = [...hops].filter(([id, n]) => n >= 3 && n <= 4 && !all.get(start).visible.includes(id)).sort((x, y) => y[1] - x[1])[0];
  assert.ok(near, 'the tour has a sweep three or four hops from the start');
  const stop = await watchBake(s);
  const ok = await s.page.evaluate((id) => window.TOUR.goTo(id), near[0]);
  assert.equal(ok, true, 'the flight arrives');
  await s.waitFor((id) => { const x = window.TOUR.getState(); return x.sweep === id && !x.transition && x.resting; }, { what: 'the late panorama of ' + near[0] + ' on screen', timeout: 15000 }, near[0]);
  let r = await stop();
  const flown = r.rows.filter((x) => x.tr && !x.tr.fade).length;
  assert.ok(flown >= 20, 'the move was a flight (' + flown + ' frames)');
  assert.equal(r.bare, 0, 'flight to ' + near[0] + ' (' + near[1] + ' hops, files 2.5 s late): ' + r.bare + ' of ' + r.frames + ' frames showed the bare model (up to ' + (r.worst * 100).toFixed(0) + ' % of the frame)');
  s.note('flight over ' + near[1] + ' hops with files 2.5 s late: ' + r.frames + ' frames, none of the bare model');
  // a far jump (a reel card, "Visit in 3D"): the old picture stays until the new panorama is in
  const far = [...hops].filter(([id]) => id !== near[0] && !asked.some((r) => r.url.includes('/' + id + '.webp'))).sort((x, y) => y[1] - x[1])[0];
  assert.ok(far, 'a sweep whose panorama has not been asked for yet');
  const stop2 = await watchBake(s, far[0]);
  const jump = s.page.evaluate((id) => window.TOUR.viewer.goTo(id, { instant: true, reset: true }), far[0]);
  jump.catch(() => {});
  await sleep(900);
  const mid = await s.page.evaluate(() => ({ st: window.TOUR.getState(), wait: document.getElementById('wait').classList.contains('show') }));
  assert.equal(mid.st.sweep, near[0], 'while the file is on its way the visitor still stands on ' + near[0]);
  assert.ok(mid.st.transition && mid.st.transition.fade && mid.st.transition.loading, 'the jump is waiting for its panorama: ' + JSON.stringify(mid.st.transition));
  assert.ok(mid.st.resting === false && mid.st.pano.level, 'with the old panorama still on screen');
  assert.ok(mid.wait, 'and a mark shows that the next view is loading');
  assert.equal(await jump, true);
  await s.waitRest(far[0], 10000);
  await s.settle(8000);
  r = await stop2();
  assert.equal(r.bare, 0, 'far jump to ' + far[0] + ': ' + r.bare + ' of ' + r.frames + ' frames showed the bare model');
  assert.ok(r.rows.filter((x) => x.slots.includes(far[0])).every((x) => x.has), 'the camera cut only when the panorama was there');
  assert.equal(await s.page.evaluate(() => document.getElementById('wait').classList.contains('show')), false, 'the loading mark is gone');
});

test('panorama files seconds late: a fly-in from the dollhouse waits for its panorama instead of flying into the bare model', {
  timeout: 120000,
}, async (s) => {
  const tour = await tourFile();
  await hold(s.page, [[new RegExp('assets/panos/(2k|4k|8k)/' + tour.start + '\\.'), 0], [PANO, 3200]]);
  await s.open('?mode=dollhouse');
  await s.waitFor(() => { const x = window.TOUR.getState(); return x.mode === 'dollhouse' && x.dollhouse && !x.dollhouse.flight; }, { what: 'the dollhouse', timeout: 30000 });
  await s.settle(8000);
  const id = tour.highlights.find((x) => x !== tour.start);
  const stop = await watchBake(s, id);
  const t0 = Date.now();
  const fly = s.page.evaluate((id) => window.TOUR.goTo(id), id);
  fly.catch(() => {});
  await sleep(1200);
  const mid = await s.page.evaluate(() => ({ d: window.TOUR.getState().dollhouse, wait: document.getElementById('wait').classList.contains('show') }));
  assert.ok(mid.d.flight && mid.d.flight.to === 'inside' && mid.d.flight.t === 0, 'the camera waits where it is: ' + JSON.stringify(mid.d.flight));
  assert.ok(mid.wait, 'a mark shows that the view is loading');
  assert.equal(await fly, true, 'the fly-in arrives');
  const st = await s.waitRest(id, 10000);
  const took = Date.now() - t0;
  await s.settle(8000);
  const r = await stop();
  const flight = r.rows.filter((x) => x.mode === 'dollhouse' && x.flight > 0);
  assert.ok(flight.length >= 20, 'the camera flew in (' + flight.length + ' frames)');
  assert.ok(flight.every((x) => x.has), 'the flight started only when the panorama of ' + id + ' was in the engine');
  assert.ok(flight.slice(-8).every((x) => x.on && x.slots.includes(id)), 'and its last frames project that panorama');
  const inside = r.rows.filter((x) => x.mode === 'inside');
  assert.ok(inside.length > 0 && inside.every((x) => x.bake < 0.02), 'inside, no frame shows the bare model');
  assert.equal(st.sweep, id);
  assert.equal(await s.page.evaluate(() => document.getElementById('wait').classList.contains('show')), false, 'the loading mark is gone');
  s.note('fly-in to ' + id + ' with its file 3.2 s late: landed after ' + took + ' ms');
});

test('a visitor who walks on does not pay for sharper levels of the sweep left behind', {
  timeout: 120000,
}, async (s) => {
  const asked = await hold(s.page, [[/assets\/panos\/(4k|8k)\//, 2000]]);
  await s.open();
  const start = await s.enter();
  const all = byId(await s.sweeps());
  const quick = await s.page.evaluate((id) => window.TOUR.viewer.panos.quick(id), start), best = await s.bestLevel(start);
  if (quick === best) { s.note('this device rests on the ' + quick + ' level: nothing sharper to drop'); return; }
  // rest long enough for the next level to be asked for, not long enough for it to arrive, then walk on
  const sharp = (id) => new RegExp('/panos/(4k|8k)/' + id + '\\.');
  const t0 = Date.now();
  while (!asked.some((r) => sharp(start).test(r.url)) && Date.now() - t0 < 3000) await sleep(20);
  assert.ok(asked.some((r) => sharp(start).test(r.url)), 'at rest the next level of ' + start + ' is asked for');
  await sleep(200);
  const to = all.get(start).links[0];
  assert.equal(await s.page.evaluate((id) => window.TOUR.goTo(id), to), true, 'walked on to ' + to);
  await s.waitSharp(to, 30000);
  await sleep(1500);                                     // anything still on its way for the sweep left behind would land now
  const left = await s.page.evaluate((id) => { const h = window.TOUR.viewer.engine.hasPanorama(id); return h ? { level: h.level, pending: h.pending } : null; }, start);
  assert.ok(left, 'the sweep left behind keeps its quick level for the way back');
  assert.equal(left.level, quick, 'the sweep left behind stays on ' + quick + ' (it holds ' + left.level + ')');
  assert.equal(left.pending, false, 'and no upload is under way for it');
  assert.ok(s.log.aborted.some((u) => sharp(start).test(u)), 'the download of its sharper level was aborted: ' + JSON.stringify(s.log.aborted.map((u) => u.replace(/^.*\/panos\//, ''))));
  const levels = await s.page.evaluate(() => window.TOUR.viewer.engine.memory().panoramaLevels);
  const high = Object.entries(levels).filter(([l]) => l !== quick).reduce((n, [, c]) => n + c, 0);
  assert.equal(high, 1, 'one sweep is sharp, the one the visitor stands on: ' + JSON.stringify(levels));
  // back on the first sweep its sharp level is asked for again and arrives
  assert.equal(await s.page.evaluate((id) => window.TOUR.goTo(id), start), true);
  const st = await s.waitSharp(start, 30000);
  assert.equal(st.pano.level, best, 'back on ' + start + ' the ' + best + ' level comes after all');
});

test('the WebGL context lost while the model downloads: the fallback page stays and the sheets say why they cannot go to 3D', {
  timeout: 120000, before: (page) => hold(page, [[MODEL, 2500]]),
}, async (s) => {
  s.allow(/3D view unavailable|context lost|CONTEXT_LOST/i);
  await s.open('', { ready: false });
  await s.press(s.testid('landing-enter'));
  await s.waitFor(() => window.TOUR.getState().mode === 'inside', { what: 'inside' });
  await s.page.evaluate(() => window.TOUR.viewer.engine.gl.getExtension('WEBGL_lose_context').loseContext());
  await s.waitFor(() => window.TOUR.getState().engine === 'failed', { what: "engine 'failed'" });
  await sleep(4500);                                     // the model arrives meanwhile: that must not bring 'ready' back
  const st = await s.page.evaluate(() => ({ engine: window.TOUR.getState().engine, fallback: !document.getElementById('fallback').hidden, note: document.getElementById('fallbackNote').textContent, reload: !!document.getElementById('fallbackReload') }));
  assert.equal(st.engine, 'failed', "the engine stays 'failed' when the model arrives after the context was lost");
  assert.ok(st.fallback && st.reload, 'the fallback page with its reload button is up');
  assert.match(st.note, /Reload the page/);
  // the sheets still open; their way into the 3D view says that it has stopped, without an error
  await s.press('#fallbackDimensions');
  await s.waitFor(() => document.getElementById('planmodal').classList.contains('open'), { what: 'the Dimensions sheet' });
  await s.press('#dimensionVisit');
  const toast = await s.waitFor(() => { const t = document.getElementById('toast'); return t.classList.contains('show') ? t.textContent : null; }, { what: 'a message' });
  assert.match(toast, /3D view has stopped.*Reload/i, 'the message: "' + toast + '"');
  assert.equal(await s.page.evaluate(() => window.TOUR.goTo(window.TOUR.sweeps()[0].id).then((v) => v, () => 'rejected')), false, 'TOUR.goTo resolves false, it does not hang or reject');
  assert.equal(await s.page.evaluate(() => window.TOUR.setMode('exterior').then((v) => v, () => 'rejected')), false, 'TOUR.setMode resolves false');
});
