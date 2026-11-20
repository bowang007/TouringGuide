'use strict';
// Memory and panorama levels (design section 4.2 and section 5: "a byte budget (max one 8k, two 4k)";
// phones stop at 4k).
//
// Texture memory is counted from outside the page's code (lib/gltrack.js wraps the WebGL calls that
// size and delete textures); the JavaScript heap is read from Chrome after a forced collection.
// The limits below are the stated budget of the page:
//
//                          desktop        phone (touch / low memory)
//   textures alive         <= 800 MB      <= 420 MB      after resting on ten sweeps
//   panoramas alive        1 x 8k, 2 x 4k    0 x 8k, 1 x 4k   (plus small 2k ones)
//   JavaScript heap        <= 300 MB      <= 250 MB
//
// (Bake atlases are 186 MB of that, depth cubes 104 MB on a desktop and 26 MB on a phone, panoramas up
// to 313 MB with one 8k without mipmaps and two 4k; see the engine notes.)
// No 8k panorama exists yet, so the level rules are tested with a stand-in: the start sweep's 4k file
// enlarged to 8192 x 4096 by Chrome and offered as its 8k level through a rewritten manifest.

const { suite, assert, config, get, panoref, sleep } = require('./lib/harness');
const gltrack = require('./lib/gltrack');
const { test } = suite(__filename);

const MB = 1024 * 1024;
const LIMITS = {
  desktop: { textures: 800 * MB, heap: 300 * MB, panos: { '8k': 1, '4k': 2 } },
  phone: { textures: 420 * MB, heap: 250 * MB, panos: { '8k': 0, '4k': 1 } },
};
const mb = (b) => (b / MB).toFixed(0) + ' MB';

async function heap(s) {
  const cdp = await s.page.target().createCDPSession();
  await cdp.send('HeapProfiler.enable');
  await cdp.send('HeapProfiler.collectGarbage');
  const u = await cdp.send('Runtime.getHeapUsage');
  await cdp.detach();
  return u.usedSize + (u.embedderHeapUsedSize || 0) + (u.backingStorageSize || 0);
}
// The first `n` sweeps in walking order from the start (breadth first over links).
function route(sweeps, start, n) {
  const all = new Map(sweeps.map((x) => [x.id, x])), seen = [start], q = [start];
  while (q.length && seen.length < n) { const a = q.shift(); for (const b of all.get(a).links) if (!seen.includes(b) && seen.length < n) { seen.push(b); q.push(b); } }
  return seen;
}
// Walks to each sweep of the route, rests there until the sharp level is on screen, and records the
// levels seen and the texture memory after each stop.
async function visit(s, ids) {
  const levels = new Set(), trace = [];
  for (const id of ids) {
    await s.page.evaluate((id) => { window.TOUR.goTo(id); }, id);
    const st = await s.waitSharp(id, 30000);
    await s.settle(8000);
    levels.add(st.pano.level);
    const r = await gltrack.report(s.page);
    trace.push({ id, level: st.pano.level, bytes: r.bytes, panoramas: r.panoramas });
  }
  return { levels: [...levels], trace };
}
async function check(s, preset, trace) {
  const lim = LIMITS[preset], r = await gltrack.report(s.page), js = await heap(s);
  s.note(preset + ': after ' + trace.length + ' sweeps ' + mb(r.bytes) + ' in ' + r.count + ' textures (peak ' + mb(r.peakBytes) + ', renderbuffers ' + mb(r.renderbufferBytes) + '), panoramas alive ' + JSON.stringify(r.panoramas) +
    ', JavaScript heap ' + mb(js) + '; per stop: ' + trace.map((t) => t.id + ' ' + mb(t.bytes)).join(', '));
  s.note('largest textures: ' + r.largest.map((t) => t.width + 'x' + t.height + (t.cube ? ' cube' : '') + (t.mips ? ' +mips' : '') + ' ' + mb(t.bytes)).join(', '));
  assert.ok(r.count > 3 && r.bytes > 8 * MB, 'the counter sees the page\'s textures (' + r.count + ', ' + mb(r.bytes) + ')');
  assert.ok(r.bytes <= lim.textures, 'textures alive: ' + mb(r.bytes) + ' > ' + mb(lim.textures));
  assert.ok(r.peakBytes <= lim.textures * 1.15, 'texture peak: ' + mb(r.peakBytes) + ' > ' + mb(lim.textures * 1.15));
  for (const [level, max] of Object.entries(lim.panos)) {
    const worst = Math.max(...trace.map((t) => t.panoramas[level]), r.panoramas[level]);
    assert.ok(worst <= max, level + ' panoramas alive at once: ' + worst + ' > ' + max);
  }
  assert.ok(js <= lim.heap, 'JavaScript heap: ' + mb(js) + ' > ' + mb(lim.heap));
  // nothing piles up: the last stops hold no more than the earlier ones did at their worst, plus one panorama
  const half = Math.max(...trace.slice(0, Math.ceil(trace.length / 2)).map((t) => t.bytes)), end = Math.max(...trace.slice(-2).map((t) => t.bytes));
  assert.ok(end <= half + 64 * MB, 'texture memory keeps growing with every sweep (' + mb(half) + ' in the first half, ' + mb(end) + ' at the end)');
  return r;
}

// Offers an 8k level for one sweep: its 4k file (the 2k one where there is no 4k) enlarged to
// 8192 x 4096 (made by Chrome in the helper page, also kept there as the reference for lib/panoref.js).
// Must run before the page is loaded.
async function offer8k(page, s, id) {
  const manifest = JSON.parse((await get(config.base + 'assets/panos/manifest.json')).body.toString('utf8'));
  const base = new URL('assets/panos/manifest.json', config.base), levels = manifest.nodes[id].levels;
  const src = new URL(levels['4k'] || levels['2k'], base).href, url8k = new URL('8k/' + id + '.webp', base).href;
  const b64 = await s.ctx.helper.evaluate(async (src, url8k) => {
    const bmp = await createImageBitmap(await (await fetch(src)).blob());
    const c = document.createElement('canvas');
    c.width = 8192; c.height = 4096;
    const g = c.getContext('2d');
    g.imageSmoothingQuality = 'high';
    g.drawImage(bmp, 0, 0, 8192, 4096);
    bmp.close();
    const blob = await new Promise((r) => c.toBlob(r, 'image/webp', 0.92));
    c.width = c.height = 1;
    window.__panoref = window.__panoref || new Map();
    for (const [k, old] of window.__panoref) { old.close(); window.__panoref.delete(k); }
    window.__panoref.set(url8k, await createImageBitmap(blob));
    const d = new Uint8Array(await blob.arrayBuffer());
    let str = '';
    for (let i = 0; i < d.length; i += 0x8000) str += String.fromCharCode.apply(null, d.subarray(i, i + 0x8000));
    return btoa(str);
  }, src, url8k);
  const file = Buffer.from(b64, 'base64');
  manifest.nodes[id].levels = Object.assign({ '8k': '8k/' + id + '.webp' }, manifest.nodes[id].levels);
  const asked = [];
  await page.setRequestInterception(true);
  page.on('request', (req) => {
    const u = req.url().split('?')[0];
    if (u === base.href) req.respond({ status: 200, contentType: 'application/json', body: JSON.stringify(manifest) });
    else if (u === url8k) { asked.push(req.url()); req.respond({ status: 200, contentType: 'image/webp', body: file }); }
    else req.continue();
  });
  return { url8k, asked, bytes: file.length };
}

test('desktop: texture memory and heap stay within the budget after resting on ten sweeps', { timeout: 240000, before: (page) => gltrack.install(page) }, async (s) => {
  await s.open();
  const start = await s.enter();
  const ids = route(await s.sweeps(), start, 10);
  const { levels, trace } = await visit(s, ids);
  assert.equal(trace.length, 10);
  await check(s, 'desktop', trace);
  s.note('levels rested on: ' + levels.join(', '));
});

test('phone: texture memory and heap stay within the phone budget, no level above 4k', { preset: 'phone', timeout: 240000, before: (page) => gltrack.install(page) }, async (s) => {
  await s.open();
  const start = await s.enter();
  const ids = route(await s.sweeps(), start, 10);
  const { levels, trace } = await visit(s, ids);
  const r = await check(s, 'phone', trace);
  assert.ok(!levels.includes('8k'), 'the phone never rests on 8k (levels: ' + levels.join(', ') + ')');
  assert.ok(r.largest.every((t) => t.cube || t.width <= 4096), 'no texture wider than 4096 px on the phone');
  assert.deepEqual(s.log.requests.filter((u) => /\/panos\/8k\//.test(u)), [], 'no 8k file was requested');
});

test('phone: an 8k level in the manifest is never downloaded', { preset: 'phone', timeout: 120000, before: (page) => gltrack.install(page) }, async (s) => {
  const tourStart = JSON.parse((await get(config.base + 'assets/data/tour.json')).body.toString('utf8')).start;
  const fake = await offer8k(s.page, s, tourStart);
  await s.open();
  const start = await s.enter();
  assert.equal(start, tourStart);
  assert.ok((await s.manifest()).nodes[start].levels['8k'], 'the page was offered an 8k level for ' + start);
  const st = await s.waitSharp(start, 30000);
  await s.settle(8000);
  await new Promise((r) => setTimeout(r, 1500));
  const r = await gltrack.report(s.page);
  const below = await s.bestLevel(start);              // the best level of the manifest under 8k (4k today)
  assert.ok(below && below !== '8k', 'a small device has a level to rest on below 8k');
  assert.equal(st.pano.level, below, 'the phone rests on ' + below);
  assert.deepEqual(fake.asked, [], 'the 8k file was not requested');
  assert.equal(r.panoramas['8k'], 0, 'no 8k texture');
  assert.ok(r.widest <= 4096, 'widest texture ' + r.widest + ' px');
});

test('desktop: the best level offered is used (8k), one at a time, and it is the picture at rest', { timeout: 180000, before: (page) => gltrack.install(page) }, async (s) => {
  if (s.gl.maxTextureSize < 8192) { s.note('MAX_TEXTURE_SIZE ' + s.gl.maxTextureSize + ': this GPU cannot hold 8k, nothing to test'); return; }
  const tourStart = JSON.parse((await get(config.base + 'assets/data/tour.json')).body.toString('utf8')).start;
  const fake = await offer8k(s.page, s, tourStart);
  await s.open();
  const start = await s.enter();
  await s.page.evaluate(() => window.TOUR.setLook(0.5, -0.05));
  const st = await s.waitSharp(start, 40000);
  assert.equal(st.pano.level, '8k', 'a desktop rests on the 8k level when the manifest has one');
  assert.equal(fake.asked.length, 1, 'the 8k file is downloaded once');
  // zoom in until the 8k picture is about 1:1 on screen, then compare with the file
  for (let i = 0; i < 6; i++) await s.wheel(-900);
  await s.settle(8000);
  const z = await s.state();
  const shot = await s.canvas();
  const view = { yaw: z.yaw, pitch: z.pitch, fovY: z.fov * Math.PI / 180, width: shot.width, height: shot.height };
  const ref = await panoref.reference(s.ctx.helper, fake.url8k, view);
  const mask = panoref.boxMask(shot.width, shot.height, await s.overlayBoxes([s.pointer]));
  const a = panoref.compare(shot, ref.srgb, mask), b = panoref.compare(shot, ref.linear, mask), best = a.psnr >= b.psnr ? a : b;
  const r = await gltrack.report(s.page);
  s.note('8k stand-in (' + (fake.bytes / MB).toFixed(1) + ' MB file) at fov ' + z.fov.toFixed(1) + ': PSNR ' + best.psnr.toFixed(1) + ' dB against the 8192 px file; textures ' + mb(r.bytes) + ', panoramas ' + JSON.stringify(r.panoramas));
  assert.equal(r.panoramas['8k'], 1, 'one 8192 px texture is alive');
  assert.ok(best.psnr >= 40, 'the frame at rest equals the 8k file: ' + best.psnr.toFixed(1) + ' dB');
  // walking on: the next sweep rests on the best level the manifest has for it (no 8k file exists for
  // it today), and the budget holds
  const to = (await s.sweeps()).find((x) => x.id === start).links[0];
  await s.page.evaluate((id) => { window.TOUR.goTo(id); }, to);
  const next = await s.waitSharp(to, 30000);
  assert.equal(next.pano.level, await s.bestLevel(to), 'the next sweep rests on its best level');
  const after = await gltrack.report(s.page);
  assert.ok(after.panoramas['8k'] <= 1 && after.bytes <= LIMITS.desktop.textures, 'still within the budget: ' + mb(after.bytes) + ', ' + JSON.stringify(after.panoramas));
});

// The 8k level is for a visitor who stops and looks. One who walks through the house (a new sweep
// about every second) must not download, decode and upload 2 MB files they never see: the budget's
// "one 8k" would hold two, and the uploads would land in the moves.
test('desktop: walking on about once a second asks for no 8k level; stopping brings it', { timeout: 240000, before: (page) => gltrack.install(page) }, async (s) => {
  if (s.gl.maxTextureSize < 8192) { s.note('MAX_TEXTURE_SIZE ' + s.gl.maxTextureSize + ': this GPU cannot hold 8k, nothing to test'); return; }
  await s.open();
  const start = await s.enter();
  const m = await s.manifest(), ids = route(await s.sweeps(), start, 9);
  if (!ids.every((id) => m.nodes[id] && m.nodes[id].levels['8k'])) { s.note('the published panoramas have no 8k level (yet): nothing to test'); return; }
  const asked8k = () => s.log.requests.concat(s.log.aborted).filter((u) => /\/panos\/8k\//.test(u)).map((u) => u.replace(/^.*\/panos\//, '').split('?')[0]);
  const peak = { '8k': 0, '4k': 0 };
  for (const id of ids.slice(1)) {
    await s.page.evaluate((id) => window.TOUR.goTo(id), id);
    await sleep(900);                                    // 0.9 s of rest on every sweep
    const r = await gltrack.report(s.page);
    for (const l of ['8k', '4k']) peak[l] = Math.max(peak[l], r.panoramas[l]);
  }
  const during = asked8k();
  assert.deepEqual(during, [], '8k files asked for while walking with 0.9 s rests');
  assert.equal(peak['8k'], 0, 'no 8k texture during the walk');
  assert.ok(peak['4k'] <= LIMITS.desktop.panos['4k'], '4k panoramas alive at once during the walk: ' + peak['4k']);
  const last = ids[ids.length - 1];
  const st = await s.waitSharp(last, 40000);
  assert.equal(st.pano.level, '8k', 'standing still, the visitor gets the 8k level');
  assert.deepEqual(asked8k(), ['8k/' + last + '.webp'], 'and it is the only 8k file of the visit');
  const r = await gltrack.report(s.page);
  assert.equal(r.panoramas['8k'], 1, 'one 8k texture');
  s.note('walk over ' + ids.length + ' sweeps with 0.9 s rests: no 8k request, at most ' + peak['4k'] + ' 4k textures; after stopping on ' + last + ' its 8k arrived, textures ' + mb(r.bytes) + ' (peak ' + mb(r.peakBytes) + ')');
});

