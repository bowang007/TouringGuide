'use strict';
// Data checks, no browser: the runtime files the page loads (design sections 4.1 and 4.2) agree with
// each other and with what is on disk and what the server hands out.
//
//   assets/data/tour.json           sweeps, links, rooms, footprint, highlights
//   assets/panos/manifest.json      panorama levels per sweep
//   assets/data/measurements.json   Dimensions sheet        assets/plans/dimension-plan.svg
//   assets/data/design.json         Design sheet            assets/exterior/manifest.json

const fs = require('node:fs');
const path = require('node:path');
const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { config, ROOT, get, ensureServer, stopServer, LEVELS } = require('./lib/harness');

const disk = (rel) => path.join(ROOT, rel);
const read = (rel) => JSON.parse(fs.readFileSync(disk(rel), 'utf8'));
const exists = (rel) => fs.existsSync(disk(rel)) && fs.statSync(disk(rel)).size > 0;
const list = (v) => (v.length > 12 ? v.slice(0, 12).join(', ') + ' … (' + v.length + ')' : v.join(', '));
const isNum = (x) => typeof x === 'number' && Number.isFinite(x);

// Pixel size of a WebP file from its header (VP8, VP8L or VP8X chunk).
function webpSize(file) {
  const fd = fs.openSync(file, 'r'), b = Buffer.alloc(32);
  fs.readSync(fd, b, 0, 32, 0);
  fs.closeSync(fd);
  if (b.toString('latin1', 0, 4) !== 'RIFF' || b.toString('latin1', 8, 12) !== 'WEBP') return null;
  const kind = b.toString('latin1', 12, 16);
  if (kind === 'VP8 ') return { width: b.readUInt16LE(26) & 0x3fff, height: b.readUInt16LE(28) & 0x3fff };
  if (kind === 'VP8L') { const n = b.readUInt32LE(21); return { width: (n & 0x3fff) + 1, height: ((n >> 14) & 0x3fff) + 1 }; }
  if (kind === 'VP8X') return { width: b.readUIntLE(24, 3) + 1, height: b.readUIntLE(27, 3) + 1 };
  return null;
}

let tour, manifest, measurements, design, byId;
before(async () => {
  tour = read('assets/data/tour.json');
  manifest = read('assets/panos/manifest.json');
  measurements = read('assets/data/measurements.json');
  design = read('assets/data/design.json');
  byId = new Map(tour.sweeps.map((s) => [s.id, s]));
  await ensureServer();
});
after(() => stopServer());

test('tour.json has the fields of the contract', () => {
  for (const k of ['version', 'title', 'subtitle', 'start']) assert.equal(typeof tour[k], 'string', k);
  assert.equal(tour.units, 'ft');
  assert.ok(isNum(tour.eye) && tour.eye > 4 && tour.eye < 6.5, 'eye height in feet');
  assert.ok(Array.isArray(tour.extent) && tour.extent.length === 2 && tour.extent.every(isNum), 'extent [x, z]');
  assert.ok(Array.isArray(tour.footprint) && tour.footprint.length > 0, 'footprint rectangles');
  for (const r of tour.footprint) assert.ok(r.length === 4 && r.every(isNum) && r[0] < r[2] && r[1] < r[3], 'footprint rectangle [x0, z0, x1, z1]: ' + r);
  assert.ok(Array.isArray(tour.sweeps) && tour.sweeps.length >= 20, 'sweeps');
  assert.ok(Array.isArray(tour.rooms) && tour.rooms.length >= 10, 'rooms');
  assert.ok(Array.isArray(tour.highlights) && tour.highlights.length >= 5, 'highlights');
  assert.ok(byId.has(tour.start), 'start "' + tour.start + '" is a sweep');
});

test('sweeps: unique two-character ids and complete entries', () => {
  const ids = tour.sweeps.map((s) => s.id);
  assert.deepEqual(ids.filter((id, i) => ids.indexOf(id) !== i), [], 'duplicate sweep ids');
  assert.deepEqual(ids.filter((id) => !/^[A-Za-z0-9]{2}$/.test(id)), [], 'ids that are not two characters');
  const rooms = new Set(tour.rooms.map((r) => r.id));
  const bad = [];
  for (const s of tour.sweeps) {
    if (typeof s.label !== 'string' || !s.label) bad.push(s.id + ': label');
    if (!Array.isArray(s.p) || s.p.length !== 3 || !s.p.every(isNum)) bad.push(s.id + ': p');
    if (!isNum(s.yaw) || !isNum(s.pitch) || Math.abs(s.pitch) > 60) bad.push(s.id + ': yaw / pitch (degrees)');
    if (!isNum(s.floor)) bad.push(s.id + ': floor');
    if (typeof s.outdoor !== 'boolean') bad.push(s.id + ': outdoor');
    if (!Array.isArray(s.links) || !Array.isArray(s.visible)) bad.push(s.id + ': links / visible');
    if (typeof s.room !== 'string' || !s.room || (!s.outdoor && !rooms.has(s.room))) bad.push(s.id + ': room "' + s.room + '" is not in rooms');
    if (Array.isArray(s.p) && Math.abs(s.p[1] - tour.eye) > 0.01) bad.push(s.id + ': eye height ' + s.p[1]);
  }
  assert.deepEqual(bad, []);
});

test('links are symmetric, without loops or duplicates, and point at sweeps', () => {
  const bad = [];
  for (const s of tour.sweeps) {
    if (new Set(s.links).size !== s.links.length) bad.push(s.id + ': duplicate links');
    for (const t of s.links) {
      if (t === s.id) bad.push(s.id + ': links to itself');
      else if (!byId.has(t)) bad.push(s.id + ' -> ' + t + ': unknown sweep');
      else if (!byId.get(t).links.includes(s.id)) bad.push(s.id + ' -> ' + t + ': not linked back');
    }
  }
  assert.deepEqual(bad, []);
});

test('visible contains links, is symmetric and points at sweeps', () => {
  const bad = [];
  for (const s of tour.sweeps) {
    for (const t of s.links) if (!s.visible.includes(t)) bad.push(s.id + ': link ' + t + ' is not in visible');
    for (const t of s.visible) {
      if (t === s.id) bad.push(s.id + ': sees itself');
      else if (!byId.has(t)) bad.push(s.id + ' sees unknown ' + t);
      else if (!byId.get(t).visible.includes(s.id)) bad.push(s.id + ' sees ' + t + ' but not the other way round');
    }
  }
  assert.deepEqual(bad, []);
});

test('the graph is connected from the start sweep', (t) => {
  const seen = new Map([[tour.start, 0]]), queue = [tour.start];
  while (queue.length) {
    const a = queue.shift();
    for (const b of byId.get(a).links) if (byId.has(b) && !seen.has(b)) { seen.set(b, seen.get(a) + 1); queue.push(b); }
  }
  const lost = tour.sweeps.map((s) => s.id).filter((id) => !seen.has(id));
  assert.deepEqual(lost, [], 'sweeps that cannot be reached over links');
  t.diagnostic(tour.sweeps.length + ' sweeps, farthest is ' + Math.max(...seen.values()) + ' hops from ' + tour.start);
});

test('a link is a short straight step', (t) => {
  const lens = [];
  for (const s of tour.sweeps) for (const id of s.links) if (byId.has(id) && s.id < id) lens.push({ pair: s.id + '-' + id, d: Math.hypot(s.p[0] - byId.get(id).p[0], s.p[2] - byId.get(id).p[2]) });
  const long = lens.filter((l) => l.d > 14).map((l) => l.pair + ' ' + l.d.toFixed(1) + ' ft');
  const tiny = lens.filter((l) => l.d < 1.5).map((l) => l.pair + ' ' + l.d.toFixed(1) + ' ft');
  assert.deepEqual(long, [], 'links longer than 14 ft');
  assert.deepEqual(tiny, [], 'links shorter than 1.5 ft');
  t.diagnostic(lens.length + ' links, ' + Math.min(...lens.map((l) => l.d)).toFixed(2) + ' .. ' + Math.max(...lens.map((l) => l.d)).toFixed(2) + ' ft');
});

test('indoor sweeps stand inside the footprint', () => {
  const inside = (x, z) => tour.footprint.some((r) => x >= r[0] - 0.05 && x <= r[2] + 0.05 && z >= r[1] - 0.05 && z <= r[3] + 0.05);
  const out = tour.sweeps.filter((s) => !s.outdoor && !inside(s.p[0], s.p[2])).map((s) => s.id + ' (' + s.p[0] + ', ' + s.p[2] + ')');
  assert.deepEqual(out, []);
});

// The engine clips the dollhouse and the floor plan to these rectangles and takes at most 16 of them
// (FOOT_MAX in assets/js/tour/engine.js). A wall that is not parallel to an axis (the canted sides of
// the Bedroom 3 bay) is a staircase of rectangles: its steps have to be fine, or the cut shows.
test('footprint: at most 16 rectangles, none overlapping, a canted wall in steps of a third of a foot at most', (t) => {
  const fp = tour.footprint;
  assert.ok(fp.length <= 16, fp.length + ' rectangles: the engine ignores all but the 16 largest');
  const over = [];
  for (let i = 0; i < fp.length; i++) for (let j = i + 1; j < fp.length; j++) {
    const a = fp[i], b = fp[j];
    if (Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > 1e-6 && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > 1e-6) over.push(i + ' and ' + j);
  }
  assert.deepEqual(over, [], 'rectangles that overlap');
  // The outline south of the widest front wall face (the bay): its west and east edges against z.
  const front = Math.max(...fp.filter((r) => r[2] - r[0] > 10).map((r) => r[3])), south = Math.max(...fp.map((r) => r[3]));
  if (south - front < 0.5) { t.diagnostic('no bay beyond the front wall in this footprint'); return; }
  const edge = (z) => { const row = fp.filter((r) => r[1] <= z && z < r[3]); return row.length ? [Math.min(...row.map((r) => r[0])), Math.max(...row.map((r) => r[2]))] : null; };
  const steps = { west: [], east: [] };
  let last = null, lastZ = front;
  for (let z = front + 0.001; z < south; z += 0.002) {
    const e = edge(z);
    if (!e) continue;
    if (last) for (const [side, k] of [['west', 0], ['east', 1]]) if (Math.abs(e[k] - last[k]) > 1e-6) { steps[side].push({ dx: Math.abs(e[k] - last[k]), dz: z - lastZ[side] }); lastZ[side] = z; }
    if (!last) lastZ = { west: z, east: z };
    last = e;
  }
  for (const side of ['west', 'east']) {
    const st = steps[side];
    assert.ok(st.length >= 5, 'the ' + side + ' side of the bay is cut in ' + st.length + ' steps (a canted wall needs at least 5)');
    const big = st.filter((x) => x.dx > 0.34 || x.dz > 0.34);
    assert.deepEqual(big.map((x) => x.dx.toFixed(3) + ' x ' + x.dz.toFixed(3) + ' ft'), [], 'steps of the ' + side + ' side larger than a third of a foot');
  }
  t.diagnostic(fp.length + ' rectangles; bay ' + (south - front).toFixed(2) + ' ft deep in ' + steps.west.length + ' + ' + steps.east.length + ' steps of ' + Math.max(...steps.west.map((x) => x.dx)).toFixed(3) + ' x ' + Math.max(...steps.west.map((x) => x.dz)).toFixed(3) + ' ft at most');
});

test('every room has a sweep, bounds and a label point', (t) => {
  const ids = tour.rooms.map((r) => r.id);
  assert.deepEqual(ids.filter((id, i) => ids.indexOf(id) !== i), [], 'duplicate room ids');
  const tags = new Set(measurements.rooms.map((r) => r.id));
  const bad = [];
  for (const r of tour.rooms) {
    if (typeof r.label !== 'string' || !r.label) bad.push(r.id + ': label');
    if (!byId.has(r.sweep)) bad.push(r.id + ': sweep "' + r.sweep + '" does not exist');
    const b = r.bounds;
    if (!Array.isArray(b) || b.length !== 4 || !b.every(isNum) || b[0] >= b[2] || b[1] >= b[3]) bad.push(r.id + ': bounds');
    else if (!Array.isArray(r.at) || r.at[0] < b[0] || r.at[0] > b[2] || r.at[1] < b[1] || r.at[1] > b[3]) bad.push(r.id + ': label point outside the bounds');
    if (r.tag && !tags.has(r.tag)) bad.push(r.id + ': tag ' + r.tag + ' is not a measured room');
  }
  assert.deepEqual(bad, []);
  const empty = tour.rooms.filter((r) => !tour.sweeps.some((s) => s.room === r.id)).map((r) => r.id);
  if (empty.length) t.diagnostic('rooms seen only from a neighbouring sweep: ' + empty.join(', '));
});

test('highlights are sweeps, each once', () => {
  assert.deepEqual(tour.highlights.filter((id) => !byId.has(id)), [], 'unknown sweeps in highlights');
  assert.equal(new Set(tour.highlights).size, tour.highlights.length, 'duplicates in highlights');
});

// The reel shows one card per highlight, captioned with the sweep's label. Several sweeps of a room share
// a label ("Kitchen", "Living room", "Garage"): the reel must not show the same name twice.
test('the highlight reel starts at the entrance and names each place once', (t) => {
  assert.equal(tour.highlights[0], tour.start, 'the first highlight is the start sweep');
  const names = tour.highlights.map((id) => byId.get(id).label);
  assert.deepEqual(names.filter((n, i) => names.indexOf(n) !== i), [], 'captions that appear twice in the reel');
  assert.deepEqual(tour.highlights.filter((id) => byId.get(id).outdoor), [], 'highlights are rooms of the house');
  const shared = [...new Set(tour.sweeps.map((x) => x.label).filter((n, i, all) => all.indexOf(n) !== i))];
  t.diagnostic(tour.highlights.length + ' cards: ' + names.join(' | ') + (shared.length ? '; labels several sweeps share: ' + shared.join(', ') : ''));
});

test('panorama manifest: every sweep has an entry with at least one level', () => {
  assert.ok(manifest.nodes && typeof manifest.nodes === 'object', 'manifest.nodes');
  for (const l of LEVELS) assert.ok(isNum(manifest.widths[l]), 'manifest.widths.' + l);
  const bad = [];
  for (const s of tour.sweeps) {
    const e = manifest.nodes[s.id];
    if (!e) { bad.push(s.id + ': no manifest entry'); continue; }
    const levels = Object.keys(e.levels || {});
    if (!levels.length) bad.push(s.id + ': no level');
    for (const l of levels) if (!LEVELS.includes(l)) bad.push(s.id + ': unknown level ' + l);
    if (!isNum(e.offset)) bad.push(s.id + ': offset');
  }
  assert.deepEqual(bad, [], list(bad));
  const stale = Object.keys(manifest.nodes).filter((id) => !byId.has(id));
  assert.deepEqual(stale, [], 'manifest entries without a sweep');
});

test('panorama files exist on disk with the declared width and a 2:1 picture', (t) => {
  const bad = [];
  let files = 0;
  const count = {};
  for (const s of tour.sweeps) {
    const e = manifest.nodes[s.id];
    if (!e) continue;
    for (const [level, rel] of Object.entries(e.levels || {})) {
      const file = 'assets/panos/' + rel;
      if (!exists(file)) { bad.push(file + ': missing'); continue; }
      const size = webpSize(disk(file));
      if (!size) bad.push(file + ': not a WebP file');
      else if (size.width !== manifest.widths[level] || size.width !== size.height * 2) bad.push(file + ': ' + size.width + 'x' + size.height + ', expected ' + manifest.widths[level] + ' wide, 2:1');
      files++;
      count[level] = (count[level] || 0) + 1;
    }
    const thumb = path.posix.normalize('assets/panos/' + (e.thumb || '../thumbs/' + s.id + '.webp'));
    if (!exists(thumb)) bad.push(thumb + ': missing thumbnail');
  }
  assert.deepEqual(bad, [], list(bad));
  assert.ok(files >= tour.sweeps.length, 'at least one file per sweep');
  t.diagnostic('levels on disk: ' + JSON.stringify(count));
});

test('the server hands out the data files and every panorama level', { timeout: 120000 }, async () => {
  const urls = ['index.html', 'assets/data/tour.json', 'assets/data/measurements.json', 'assets/data/design.json', 'assets/panos/manifest.json', 'assets/plans/dimension-plan.svg', 'assets/model/house.glb', 'assets/exterior/manifest.json'];
  for (const s of tour.sweeps) {
    const e = manifest.nodes[s.id];
    if (!e) continue;
    for (const rel of Object.values(e.levels || {})) urls.push('assets/panos/' + rel);
    urls.push(path.posix.normalize('assets/panos/' + (e.thumb || '../thumbs/' + s.id + '.webp')));
  }
  const bad = [];
  for (const u of urls) {
    const r = await get(config.base + u, 'HEAD').catch((e) => ({ status: e.message }));
    if (r.status !== 200) bad.push(u + ': ' + r.status);
    else if (!(Number(r.headers['content-length']) > 0)) bad.push(u + ': empty');
  }
  assert.deepEqual(bad, [], list(bad));
  const served = JSON.parse((await get(config.base + 'assets/data/tour.json')).body.toString('utf8'));
  if (/^http:\/\/(127\.0\.0\.1|localhost)[:/]/.test(config.base)) assert.equal(served.version, tour.version, 'the server serves this checkout (tour.json version)');
});

test('measurements: unique ids, each item stands on a sweep and has a target on the plan', () => {
  const items = [...measurements.rooms, ...measurements.windows, ...measurements.doors];
  const ids = items.map((x) => x.id);
  assert.deepEqual(ids.filter((id, i) => ids.indexOf(id) !== i), [], 'duplicate measurement ids');
  assert.deepEqual(items.filter((x) => !byId.has(x.node)).map((x) => x.id + ' -> ' + x.node), [], 'items whose "Visit in 3D" sweep does not exist');
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  const hits = new Set([...svg.matchAll(/data-measure="([^"]+)"/g)].map((m) => m[1]));
  assert.deepEqual(ids.filter((id) => !hits.has(id)), [], 'items without a data-measure target in dimension-plan.svg');
  assert.deepEqual([...hits].filter((id) => !ids.includes(id)), [], 'plan targets without a measurement');
  for (const r of measurements.rooms) assert.ok(r.width_ft > 0 && r.depth_ft > 0 && r.area_sqft > 0, r.id + ' has a size');
  for (const o of [...measurements.windows, ...measurements.doors]) assert.ok(o.width > 0 && o.height > 0, o.id + ' has a size');
});

test('design views: tab order, pictures and links resolve', () => {
  const bad = [];
  const measured = new Set([...measurements.rooms, ...measurements.windows, ...measurements.doors].map((x) => x.id));
  for (const k of design.order) {
    const v = design.views[k];
    if (!v) { bad.push(k + ': in order but not in views'); continue; }
    for (const f of ['label', 'title', 'text']) if (typeof v[f] !== 'string' || !v[f]) bad.push(k + ': ' + f);
    if (v.image && !exists(v.image)) bad.push(k + ': image ' + v.image + ' missing');
    if (v.node && !byId.has(v.node)) bad.push(k + ': node ' + v.node + ' is not a sweep');
    if (v.opening && !measured.has(v.opening)) bad.push(k + ': opening ' + v.opening + ' is not measured');
    for (const ref of v.refs || []) {
      const file = design.references && design.references[ref];
      if (!file) bad.push(k + ': reference "' + ref + '" has no file');
      else if (!exists(file)) bad.push(k + ': reference file ' + file + ' missing');
    }
  }
  assert.deepEqual(bad, []);
});

test('exterior frames exist', () => {
  const m = read('assets/exterior/manifest.json');
  assert.ok(Array.isArray(m.frames) && m.frames.length >= 8, 'frames');
  const missing = [];
  for (const f of m.frames) for (const rel of [f.full, f.half]) if (!exists('assets/exterior/' + rel)) missing.push(rel);
  assert.deepEqual(missing, []);
});

test('the page is a slim shell stamped with the release of tour.json', () => {
  const html = fs.readFileSync(disk('index.html'), 'utf8');
  assert.ok(html.length < 100000, 'index.html is markup only (' + html.length + ' bytes)');
  assert.match(html, /<script type="module" src="assets\/js\/tour\/main\.js(\?v=[^"]*)?"/, 'index.html loads assets/js/tour/main.js as a module');
  const stamps = [...html.matchAll(/\?v=([^"'&\s]+)/g)].map((m) => m[1]);
  assert.ok(stamps.length >= 1, 'index.html stamps its files with ?v=');
  assert.deepEqual(stamps.filter((v) => v !== tour.version), [], 'every ?v= in index.html is tour.json version ' + tour.version);
  assert.equal(measurements.version, tour.version, 'measurements.json version');
  for (const f of ['main', 'viewer', 'inside', 'dollhouse', 'exterior', 'ui', 'dimensions', 'design', 'testapi', 'engine']) assert.ok(exists('assets/js/tour/' + f + '.js'), 'assets/js/tour/' + f + '.js');
  assert.ok(exists('assets/css/tour.css'), 'assets/css/tour.css');
});

// The model and the plan are fetched with their own content hash as ?v= (tour.json `files`, written by
// tools/web/build_site_data.py). A hash that does not match the file means the data was not rebuilt
// after the file changed: a returning visitor would keep the cached old model.
test('tour.json names the model and the plan by their content', (t) => {
  if (!tour.files) { t.diagnostic('tour.json has no `files` yet (it predates the content hashes): written by the next build_site_data.py run'); return; }
  const digest = (rel) => require('node:crypto').createHash('sha1').update(path.basename(rel) + '\0').update(fs.readFileSync(disk(rel))).digest('hex').slice(0, 12);
  for (const [key, rel] of [['model', 'assets/model/house.glb'], ['plan', 'assets/plans/dimension-plan.svg']]) {
    assert.ok(exists(rel), rel);
    assert.equal(tour.files[key], digest(rel), 'tour.json files.' + key + ' is the hash of ' + rel + ' (run tools/web/build_site_data.py after publishing it)');
  }
});

// ---- rooms inside rooms ----------------------------------------------------------------------------
// Room bounds are rectangles and may lie inside one another: the laundry closet is cut out of Bedroom 4's
// rectangle, and the rectangle of an open space reaches over its neighbours. A point belongs to the
// SMALLEST room that contains it (room_of in tools/web/build_site_data.py, roomAt in
// assets/js/tour/viewer.js).
const span = (b) => (b[2] - b[0]) * (b[3] - b[1]);                     // bounds [x0, z0, x1, z1]
const holds = (r, x, z, tol = 0) => x >= r.bounds[0] - tol && x <= r.bounds[2] + tol && z >= r.bounds[1] - tol && z <= r.bounds[3] + tol;
const roomAt = (x, z) => tour.rooms.filter((r) => holds(r, x, z)).sort((a, b) => span(a.bounds) - span(b.bounds))[0] || null;
const bearing = (from, x, z) => Math.atan2(x - from.p[0], -(z - from.p[2])) * 180 / Math.PI;      // yaw in degrees, 0 = north
const turn = (a, b) => Math.abs(((a - b + 540) % 360) - 180);                                    // degrees between two yaws

test('a sweep belongs to the smallest room that contains it; a room nobody stands in owns the sweep in front of it', (t) => {
  const stood = new Set(tour.sweeps.filter((s) => !s.outdoor).map((s) => roomAt(s.p[0], s.p[2])).filter(Boolean).map((r) => r.id));
  const bad = [];
  for (const s of tour.sweeps) {
    if (s.outdoor) continue;
    const at = roomAt(s.p[0], s.p[2]);
    if (!at || s.room === at.id) continue;             // (in a doorway, between two rooms: the nearest one)
    const own = tour.rooms.find((r) => r.id === s.room);
    // the only other case: the sweep in front of a room that holds no sweep, named by that room
    if (!own || stood.has(own.id) || own.sweep !== s.id) bad.push(s.id + ': room "' + s.room + '", stands in "' + at.id + '"');
  }
  assert.deepEqual(bad, []);
  const nested = tour.rooms.filter((r) => tour.rooms.some((o) => o !== r && span(o.bounds) > span(r.bounds) && holds(o, r.bounds[0], r.bounds[1], 0.01) && holds(o, r.bounds[2], r.bounds[3], 0.01)));
  const vacant = tour.rooms.filter((r) => !stood.has(r.id));
  t.diagnostic('rooms inside another room\'s rectangle: ' + (nested.map((r) => r.id).join(', ') || 'none') + '; rooms nobody stands in: ' + (vacant.map((r) => r.id + ' (seen from ' + r.sweep + ')').join(', ') || 'none'));
  // such a room is entered on its own sweep, which therefore has to see it: not farther than 8 ft from it
  for (const r of vacant) {
    const s = byId.get(r.sweep);
    const d = Math.hypot(Math.max(r.bounds[0] - s.p[0], 0, s.p[0] - r.bounds[2]), Math.max(r.bounds[1] - s.p[2], 0, s.p[2] - r.bounds[3]));
    assert.ok(d <= 8, r.id + ': its sweep ' + s.id + ' stands ' + d.toFixed(1) + ' ft from it');
  }
});

// A target of the Dimensions plan that lies inside a larger one (the closet inside Bedroom 4, a skylight
// inside its room) must be drawn after it, or the larger one takes its clicks.
test('plan targets: a target inside a larger one lies on top of it', () => {
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  const hits = [...svg.matchAll(/<rect\b([^>]*\bdata-measure="([^"]+)"[^>]*)>/g)].map((m) => {
    const num = (k) => Number((new RegExp('(?:^|\\s)' + k + '="(-?[\\d.]+)"').exec(m[1]) || [])[1]);      // (not stroke-width)
    return { id: m[2], x: num('x'), y: num('y'), w: num('width'), h: num('height') };
  });
  assert.ok(hits.length > 0 && hits.every((h) => [h.x, h.y, h.w, h.h].every(isNum) && h.w > 0 && h.h > 0), 'the targets are rectangles with a size');
  const under = [];
  hits.forEach((a, i) => hits.forEach((b, j) => {
    const cx = a.x + a.w / 2, cy = a.y + a.h / 2;
    if (i < j && a.w * a.h < b.w * b.h && cx > b.x && cx < b.x + b.w && cy > b.y && cy < b.y + b.h) under.push(a.id + ' lies under ' + b.id);
  }));
  assert.deepEqual(under, []);
});

// ---- the laundry closet (owner's fifth round, 2026-11-20) ---------------------------------------------
// It is cut out of Bedroom 4's north-east corner and opens east onto the foyer through a pair of doors;
// nobody can stand in it, so it is seen from the sweep LC in the foyer, in front of the doors. The ids
// the design names are M13 (room), D17 (doors) and LC (sweep and design view); everything else is read
// from the data and held to the rule, not to coordinates.
test('laundry closet: room M13 is just large enough for the stacked pair and has the doors D17 in one of its sides', () => {
  const room = measurements.rooms.find((r) => r.id === 'M13');
  assert.ok(room, 'measurements.json has room M13');
  assert.match(room.name, /laundry/i);
  const [x0, x1, z0, z1] = room.bounds_ft, sx = x1 - x0, sz = z1 - z0;
  // a stacked 27 in pair, 30 1/4 in deep with its hoses: at least 2'-6" each way, and no more than about 3.2 ft
  assert.ok(Math.min(sx, sz) >= 2.5 && Math.max(sx, sz) <= 3.2, 'clear size between 2\'-6" and about 3.2 ft each way, got ' + sx.toFixed(3) + ' x ' + sz.toFixed(3));
  // width (across the doors) and depth are the two sides of the bounds, in either order
  const named = [room.width_ft, room.depth_ft].sort(), sides = [sx, sz].sort();
  assert.ok(Math.abs(named[0] - sides[0]) < 0.02 && Math.abs(named[1] - sides[1]) < 0.02, 'width and depth are the sides of the bounds: ' + named + ' against ' + sides.map((v) => v.toFixed(3)));
  assert.ok(Math.abs(room.area_sqft - sx * sz) < 0.15, 'area ' + room.area_sqft + ' sq ft is width x depth');
  assert.ok((measurements.audit || []).some((a) => a.id === 'M13' || /laundry/i.test(a.name)), 'the room table (audit) lists the laundry closet');
  const door = measurements.doors.find((d) => d.id === 'D17');
  assert.ok(door, 'measurements.json has door D17');
  assert.match(door.name, /laundry/i);
  assert.ok(Math.abs(door.width - 2.5) < 0.1 && Math.abs(door.height - 6.67) < 0.1, 'opening 2\'-6" x 6\'-8", got ' + door.width + ' x ' + door.height);
  assert.ok(Math.abs(door.end - door.start - door.width) < 0.02, 'start and end of the opening are its width apart');
  // the opening lies in one side of the room: within that side's length, in the wall just outside it
  const along = door.axis === 'z' ? [z0, z1] : [x0, x1], across = door.axis === 'z' ? [x0, x1] : [z0, z1];
  assert.ok(door.start >= along[0] - 0.05 && door.end <= along[1] + 0.05, 'the opening (' + door.start + ' .. ' + door.end + ') lies within the side of the room (' + along + ')');
  const out = door.c < across[0] ? across[0] - door.c : door.c - across[1];
  assert.ok(out > 0 && out <= 0.5, 'the door line is in the wall of one side of the room (' + out.toFixed(3) + ' ft outside the clear face)');
  assert.ok(door.width <= (along[1] - along[0]) + 0.01, 'the doors are not wider than the closet');
  // both on the plan
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  for (const id of ['M13', 'D17']) assert.ok(svg.includes('data-measure="' + id + '"'), 'dimension-plan.svg has a target for ' + id);
});

test('laundry closet: carved out of Bedroom 4\'s north-east corner, opening east onto the foyer', () => {
  const tr = tour.rooms.find((r) => r.tag === 'M13');
  assert.ok(tr, 'tour.json has a room with tag M13');
  assert.match(tr.label, /laundry/i);
  const m = measurements.rooms.find((r) => r.id === 'M13'), [x0, x1, z0, z1] = m.bounds_ft;
  assert.deepEqual(tr.bounds.map((v) => v.toFixed(3)), [x0, z0, x1, z1].map((v) => v.toFixed(3)), 'tour.json and the schedule give the closet the same bounds');
  // inside the rectangle of the room named Bedroom 4, in its north-east corner (x east, z south)
  const host = tour.rooms.find((r) => r !== tr && /^bedroom 4$/i.test(r.label));
  assert.ok(host, 'tour.json has the room "Bedroom 4"');
  assert.ok(holds(host, tr.bounds[0], tr.bounds[1], 0.01) && holds(host, tr.bounds[2], tr.bounds[3], 0.01), 'the closet lies inside Bedroom 4\'s rectangle (' + tr.bounds + ' in ' + host.bounds + ')');
  assert.ok(Math.abs(tr.bounds[2] - host.bounds[2]) < 0.01 && Math.abs(tr.bounds[1] - host.bounds[1]) < 0.01, 'in its north-east corner: the east and north sides coincide');
  assert.ok(span(tr.bounds) < span(host.bounds) / 5, 'and takes a small part of it');
  assert.equal(roomAt(tr.at[0], tr.at[1]).id, tr.id, 'a point in the closet belongs to the closet, not to Bedroom 4 (the smallest room wins)');
  const hostM = measurements.rooms.find((r) => r.id === host.tag);
  assert.ok(hostM.area_sqft < hostM.width_ft * hostM.depth_ft - span(tr.bounds) + 0.01, 'Bedroom 4\'s area (' + hostM.area_sqft + ' sq ft) leaves the closet out');
  // the doors are in the east side, and beyond them is the foyer
  const door = measurements.doors.find((d) => d.id === 'D17');
  assert.ok(door.axis === 'z' && door.c > x1, 'the doors D17 are in the closet\'s east side');
  const beyond = roomAt(door.c + 1, (door.start + door.end) / 2);
  assert.ok(beyond && /foyer/i.test(beyond.label), 'one foot east of the doors is the foyer, got ' + (beyond && beyond.label));
});

test('laundry closet: the sweep LC stands in the foyer in front of the doors and looks at them', () => {
  const tr = tour.rooms.find((r) => r.tag === 'M13'), room = measurements.rooms.find((r) => r.id === 'M13'), door = measurements.doors.find((d) => d.id === 'D17');
  assert.equal(tr.sweep, 'LC', 'the closet is seen from the sweep LC');
  assert.equal(room.node, 'LC', '"Visit in 3D" of M13 goes to LC');
  assert.equal(door.node, 'LC', '"Visit in 3D" of D17 goes to LC');
  const s = byId.get('LC');
  assert.ok(s && !s.outdoor, 'LC is an indoor sweep');
  assert.ok(!holds(tr, s.p[0], s.p[2], 0.3), 'nobody can stand in the closet: LC stands outside it');
  // the middle of the opening on the plan, and which way is out
  const mid = (door.start + door.end) / 2, dx = door.axis === 'z' ? door.c : mid, dz = door.axis === 'z' ? mid : door.c;
  const d = Math.hypot(s.p[0] - dx, s.p[2] - dz);
  assert.ok(d >= 2 && d <= 6, 'LC stands 2 to 6 ft from the doors, got ' + d.toFixed(2) + ' ft');
  const outward = Math.sign(door.c - (door.axis === 'z' ? tr.at[0] : tr.at[1])), off = (door.axis === 'z' ? s.p[0] : s.p[2]) - door.c;
  assert.ok(off * outward > 0, 'on the side the doors open to, not behind the closet');
  const side = (door.axis === 'z' ? s.p[2] : s.p[0]) - mid;
  assert.ok(Math.abs(side) <= door.width / 2, 'in front of the opening, not beside it (' + side.toFixed(2) + ' ft off its axis)');
  const away = turn(s.yaw, bearing(s, dx, dz));
  assert.ok(away <= 15, 'LC opens looking at the doors (' + away.toFixed(1) + ' degrees off)');
  assert.ok(s.pitch <= 0 && s.pitch >= -25, 'level or a little down, so that both stacked units are in the picture (pitch ' + s.pitch + ')');
  // the sweep in front of the closet is the closet's: room chip, reel, a click on the room
  assert.equal(s.room, tr.id, 'LC belongs to the closet');
  assert.match(s.label, /laundry/i, 'and is named after it');
  assert.ok(tour.highlights.includes('LC'), 'the highlight reel has the laundry closet');
  assert.ok(s.links.length >= 2, 'it is a place on the way, not a dead end (links ' + s.links.join(', ') + ')');
  const standing = roomAt(s.p[0], s.p[2]);
  assert.ok(standing && /foyer/i.test(standing.label), 'LC stands in the foyer, got ' + (standing && standing.label));
});

test('design sheet: the view "LC" and the owner\'s rounds describe the closet at Bedroom 4 and the table at the island', () => {
  assert.ok(design.order.includes('LC') && design.views.LC, 'design.json has the view LC in its tab order');
  const v = design.views.LC;
  assert.match(v.label, /laundry/i);
  assert.ok(exists(v.image), 'the Laundry still exists: ' + v.image);
  assert.equal(v.node, 'LC', 'its "Walk into this room" goes to LC');
  assert.equal(v.opening, 'M13', 'its "Opening details" show M13');
  assert.match(v.title + ' ' + v.text, /bedroom 4/i, 'the text places the closet at Bedroom 4');
  assert.match(v.title + ' ' + v.text, /foyer/i, 'and says that it opens onto the foyer');
  // no view still tells the fourth round's story, the closet in the kitchen's corner ("dishwasher" is not a washer)
  const stale = Object.entries(design.views).filter(([, o]) => /laundry|\bwasher\b/i.test(o.title + ' ' + o.text) && /kitchen/i.test(o.title + ' ' + o.text)).map(([k]) => k);
  assert.deepEqual(stale, [], 'views that mention the laundry closet together with the kitchen');
  // the rounds of owner's changes: numbered 1.., the laundry closet in the fourth, moved to Bedroom 4 in a later one
  const rounds = design.owner_changes || [];
  assert.deepEqual(rounds.map((r) => r.round), rounds.map((_, i) => i + 1), 'rounds are numbered from 1 without a gap');
  const about = rounds.filter((r) => r.changes.some((c) => /laundry|\bwasher\b/i.test(c)));
  assert.ok(about.some((r) => r.round === 4), 'the fourth round mentions the laundry closet (rounds: ' + rounds.map((r) => r.round).join(', ') + ')');
  const last = about[about.length - 1];
  assert.ok(last.round >= 5 && last.changes.some((c) => /laundry|\bwasher\b/i.test(c) && /bedroom 4/i.test(c)), 'the latest round about the laundry closet (round ' + last.round + ') puts it at Bedroom 4');
  assert.ok(last.changes.some((c) => /dining table/i.test(c) && /island/i.test(c)), 'the same round moves the dining table to the island (round ' + last.round + ')');
});
