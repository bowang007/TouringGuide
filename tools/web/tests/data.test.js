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

// ---- the primary suite as on the architect's sheet (owner's sixth round, 2026-11-20) -------------------
// The 8 ft zone between the primary bedroom and its bathroom was one open dressing area. It is two rooms
// now: the walk-in closet, an enclosed room behind a pocket door, and the vestibule east of it, which is
// open to the bedroom and leads to the hall, the closet and the bathroom. The ids the design names are
// M05 (closet), M14 (vestibule), D18 (pocket door) and the windows W11, W13, W14; rooms are also found by
// their names, sweeps and the other doors by where they stand. Sizes are held to the sheet's figures
// within a tenth of a foot, positions to the rule (which side, which room beyond), not to coordinates.
const primarySuite = () => {
  const m = (id) => measurements.rooms.find((r) => r.id === id), t = (tag) => tour.rooms.find((r) => r.tag === tag);
  return { closet: m('M05'), vestibule: m('M14'), tCloset: t('M05'), tVestibule: t('M14'), door: measurements.doors.find((d) => d.id === 'D18') };
};
const sides = (r) => [r.bounds_ft[1] - r.bounds_ft[0], r.bounds_ft[3] - r.bounds_ft[2]];          // bounds_ft [x0, x1, z0, z1] -> [east-west, north-south]
const standing = (room) => tour.sweeps.filter((s) => !s.outdoor && holds(room, s.p[0], s.p[2]));    // sweeps that stand in a room of tour.json
const named = (re) => tour.rooms.find((r) => re.test(r.label));
// doors of the schedule in one side of a room (bounds_ft), in the wall just outside its clear face
function doorsIn(room, side) {
  const [x0, x1, z0, z1] = room.bounds_ft;
  const axis = side === 'east' || side === 'west' ? 'z' : 'x', face = { west: x0, east: x1, north: z0, south: z1 }[side], out = side === 'east' || side === 'south' ? 1 : -1;
  const along = axis === 'z' ? [z0, z1] : [x0, x1];
  return measurements.doors.filter((d) => d.axis === axis && (d.c - face) * out > 0 && (d.c - face) * out <= 0.5 && d.start >= along[0] - 0.05 && d.end <= along[1] + 0.05);
}

test('primary suite: the walk-in closet M05 is a room of about 6\'-1" x 8\'-0" with the pocket door D18 in its east side', () => {
  const { closet, tCloset, door } = primarySuite();
  assert.ok(closet, 'measurements.json has room M05');
  assert.match(closet.name, /walk-in closet/i, 'M05 is named after what it is');
  assert.doesNotMatch(closet.name + ' ' + closet.note, /dressing area|open wardrobe/i, 'nothing of the open dressing area is left in its entry');
  const [sx, sz] = sides(closet);
  assert.ok(Math.abs(sx - 6.083) <= 0.1 && Math.abs(sz - 8) <= 0.1, 'clear size about 6\'-1" x 8\'-0" (the sheet), got ' + sx.toFixed(3) + ' x ' + sz.toFixed(3));
  assert.ok(Math.abs(closet.width_ft - sx) < 0.02 && Math.abs(closet.depth_ft - sz) < 0.02, 'width and depth are the sides of the bounds');
  assert.ok(Math.abs(closet.area_sqft - sx * sz) < 0.15, 'area ' + closet.area_sqft + ' sq ft is width x depth');
  assert.ok((measurements.audit || []).some((a) => a.id === 'M05' && /walk-in closet/i.test(a.name)), 'the room table (audit) lists it under that name');
  // the same room in tour.json
  assert.ok(tCloset, 'tour.json has a room with tag M05');
  assert.match(tCloset.label, /^walk-in closet$/i);
  const [x0, x1, z0, z1] = closet.bounds_ft;
  assert.deepEqual(tCloset.bounds.map((v) => v.toFixed(3)), [x0, z0, x1, z1].map((v) => v.toFixed(3)), 'tour.json and the schedule give the closet the same bounds');
  // a small room has a door: D18, a sliding pocket door in the east side
  assert.ok(door, 'measurements.json has door D18');
  assert.match(door.name, /closet/i);
  assert.match(door.name + ' ' + door.type, /pocket/i, 'a pocket door');
  assert.ok(doorsIn(closet, 'east').includes(door), 'D18 lies in the closet\'s east side, in the wall just outside its clear face (axis ' + door.axis + ', line ' + door.c + ', ' + door.start + ' .. ' + door.end + ')');
  assert.ok(door.width >= 2.3 && door.width <= 3 && Math.abs(door.end - door.start - door.width) < 0.02, 'a single door, 2\'-4" to 3\'-0" wide, got ' + door.width);
  assert.ok(Math.abs(door.height - 6.67) < 0.1, 'head at 6\'-8"');
  for (const side of ['west', 'north', 'south']) assert.deepEqual(doorsIn(closet, side).map((d) => d.id), [], 'no other way in: no door in the ' + side + ' side');
  assert.deepEqual(doorsIn(closet, 'east').map((d) => d.id), ['D18'], 'D18 is the only door of the east side');
  // no window (the sheet shows none): no opening of the west wall meets the closet
  const lit = measurements.windows.filter((w) => w.axis === 'z' && Math.abs(w.c - x0) < 0.6 && w.end > z0 && w.start < z1).map((w) => w.id);
  assert.deepEqual(lit, [], 'windows in the closet\'s west wall');
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  for (const id of ['M05', 'D18']) assert.ok(svg.includes('data-measure="' + id + '"'), 'dimension-plan.svg has a target for ' + id);
});

test('primary suite: a sweep stands in the walk-in closet and is reached from the vestibule through the door', (t) => {
  const { closet, tCloset, tVestibule, door } = primarySuite();
  const inCloset = standing(tCloset);
  assert.ok(inCloset.length >= 1, 'a sweep stands inside the closet (a room one can walk into)');
  for (const s of inCloset) {
    assert.equal(s.room, tCloset.id, s.id + ' belongs to the closet');
    assert.match(s.label, /walk-in closet/i, s.id + ' is named after it (the room chip, the reel)');
  }
  assert.ok(inCloset.some((s) => s.id === tCloset.sweep), 'the closet is entered on a sweep that stands in it (' + tCloset.sweep + ')');
  assert.ok(inCloset.some((s) => s.id === closet.node), '"Visit in 3D" of M05 stands in the closet (' + closet.node + ')');
  const beside = byId.get(door.node), at = beside && roomAt(beside.p[0], beside.p[2]);
  assert.ok(at && (at.id === tCloset.id || at.id === tVestibule.id), '"Visit in 3D" of D18 stands on one side of the door, got ' + door.node + ' in ' + (at && at.label));
  // the only way in is the door: every link of a closet sweep that leaves the room goes to the vestibule and crosses the opening
  const out = [];
  for (const s of inCloset) for (const id of s.links) {
    const o = byId.get(id);
    if (holds(tCloset, o.p[0], o.p[2])) continue;
    const far = roomAt(o.p[0], o.p[2]), k = (door.c - s.p[0]) / (o.p[0] - s.p[0]), z = s.p[2] + (o.p[2] - s.p[2]) * k;
    assert.equal(far && far.id, tVestibule.id, 'the link ' + s.id + '-' + id + ' leads to the vestibule');
    assert.ok(k > 0 && k < 1 && z > door.start + 0.3 && z < door.end - 0.3, 'the link ' + s.id + '-' + id + ' passes through the opening of D18, clear of its jambs (it crosses the wall line at z ' + z.toFixed(2) + ', opening ' + door.start + ' .. ' + door.end + ')');
    out.push(s.id + '-' + id + ' at z ' + z.toFixed(2));
  }
  assert.ok(out.length >= 1, 'the closet is linked to the vestibule');
  t.diagnostic('sweeps in the closet: ' + inCloset.map((s) => s.id).join(', ') + '; through the door: ' + out.join(', '));
});

test('primary suite: the vestibule M14 is about 4\'-7" wide, beside the closet, between the bedroom, the hall and the bathroom', (t) => {
  const { closet, vestibule, tVestibule, door } = primarySuite();
  assert.ok(vestibule && tVestibule, 'measurements.json and tour.json have room M14');
  assert.match(vestibule.name, /^primary vestibule$/i);
  assert.match(tVestibule.label, /vestibule/i);
  const [sx, sz] = sides(vestibule);
  assert.ok(Math.abs(sx - 4.583) <= 0.1, 'about 4\'-7" wide (the sheet), got ' + sx.toFixed(3) + ' ft');
  assert.ok(Math.abs(sz - 8) <= 0.1, 'and 8\'-0" long, got ' + sz.toFixed(3) + ' ft');
  assert.ok(Math.abs(vestibule.area_sqft - sx * sz) < 0.15, 'area ' + vestibule.area_sqft + ' sq ft is width x depth');
  // closet and vestibule stand side by side in the same 8 ft zone, a partition wall between them
  const [cx0, cx1, cz0, cz1] = closet.bounds_ft, [x0, x1, z0, z1] = vestibule.bounds_ft, wall = x0 - cx1;
  assert.ok(Math.abs(cz0 - z0) < 0.02 && Math.abs(cz1 - z1) < 0.02, 'the same north and south faces as the closet');
  assert.ok(wall >= 0.3 && wall <= 0.6, 'east of the closet, a wall of 4 to 7 inches between them (' + wall.toFixed(3) + ' ft)');
  assert.ok(door.c > cx1 && door.c < x0, 'the pocket door D18 is in that wall');
  // around it: the bedroom to the north over the whole width (no door), the bathroom to the south, the hall to the east
  const bed = named(/^primary bedroom$/i), bath = named(/^primary bathroom$/i);
  assert.ok(bed && bath, 'tour.json has the rooms "Primary bedroom" and "Primary bathroom"');
  assert.ok(Math.abs(cx0 - bed.bounds[0]) < 0.02 && Math.abs(x1 - bed.bounds[2]) < 0.02, 'closet + wall + vestibule are as wide as the bedroom (' + cx0 + ' .. ' + x1 + ' against ' + bed.bounds[0] + ' .. ' + bed.bounds[2] + ')');
  for (const x of [(cx0 + cx1) / 2, (x0 + x1) / 2]) {
    assert.equal(roomAt(x, z0 - 1).id, bed.id, 'one foot north of the zone is the primary bedroom');
    assert.equal(roomAt(x, z1 + 1).id, bath.id, 'one foot south of it the primary bathroom');
  }
  const open = doorsIn(vestibule, 'north');
  assert.ok(open.length === 1 && /no door/i.test(open[0].type) && Math.abs(open[0].width - sx) < 0.1, 'open to the bedroom over its full width, no door (' + open.map((d) => d.id + ' ' + d.width + ' ft: ' + d.type).join('; ') + ')');
  const south = doorsIn(vestibule, 'south'), east = doorsIn(vestibule, 'east');
  assert.ok(south.length === 1 && /bath/i.test(south[0].name), 'the bathroom door is at its south end (' + south.map((d) => d.id + ' ' + d.name).join(', ') + ')');
  assert.ok(east.length === 1 && /entry|entrance/i.test(east[0].name) && /sliding/i.test(east[0].type), 'the suite entry, a sliding panel, is in its east side (' + east.map((d) => d.id + ' ' + d.name).join(', ') + ')');
  const beyond = roomAt(east[0].c + 1.5, (east[0].start + east[0].end) / 2);
  assert.ok(beyond && /hall/i.test(beyond.label), 'beyond the suite entry is the hall, got ' + (beyond && beyond.label));
  // sweeps: at least one stands in it, named after it, and from the vestibule one steps into all four neighbours
  const here = standing(tVestibule);
  assert.ok(here.length >= 1 && here.some((s) => s.id === tVestibule.sweep), 'a sweep stands in the vestibule and the room is entered on it (' + tVestibule.sweep + ')');
  for (const s of here) assert.ok(s.room === tVestibule.id && /vestibule/i.test(s.label), s.id + ' belongs to the vestibule and is named after it ("' + s.label + '")');
  const next = new Set(here.flatMap((s) => s.links).map((id) => byId.get(id).room));
  for (const r of [bed, bath, tour.rooms.find((q) => q.tag === 'M05'), beyond]) assert.ok(next.has(r.id), 'a link leads from the vestibule to ' + r.label);
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  assert.ok(svg.includes('data-measure="M14"'), 'dimension-plan.svg has a target for M14');
  t.diagnostic('vestibule ' + sx.toFixed(3) + ' x ' + sz.toFixed(3) + ' ft, sweeps ' + here.map((s) => s.id).join(', ') + '; doors: north ' + open[0].id + ', east ' + east[0].id + ', south ' + south[0].id + ', west D18');
});

test('primary suite: the reel offers the bedroom, the walk-in closet and the bathroom once each; no place is still called a dressing area', () => {
  const cards = tour.highlights.map((id) => byId.get(id));
  for (const [name, re] of [['Primary bedroom', /^primary bedroom$/i], ['Walk-in closet', /^walk-in closet$/i], ['Primary bathroom', /^primary bathroom$/i]]) {
    const mine = cards.filter((s) => re.test(s.label));
    assert.equal(mine.length, 1, 'one card "' + name + '" in the reel (' + mine.map((s) => s.id).join(', ') + ')');
    const room = named(re);
    assert.ok(room && holds(room, mine[0].p[0], mine[0].p[2]), 'its sweep ' + mine[0].id + ' stands in that room');
  }
  const stale = [...tour.sweeps, ...tour.rooms, ...measurements.rooms.map((r) => ({ id: r.id, label: r.name })), ...measurements.doors.map((d) => ({ id: d.id, label: d.name + ' ' + d.type }))]
    .filter((x) => /dressing/i.test(x.label)).map((x) => x.id + ' "' + x.label + '"');
  assert.deepEqual(stale, [], 'sweeps, rooms and doors still named after the open dressing area');
});

test('windows of the sixth round: W11 from a 3\'-0" sill to a 7\'-6" head, W13 three feet wide, W14 kept', () => {
  const win = (id) => measurements.windows.find((w) => w.id === id), room = (re) => measurements.rooms.find((r) => re.test(r.name));
  const inWestWall = (w, r) => w.axis === 'z' && Math.abs(w.c - r.bounds_ft[0]) < 0.6 && w.start >= r.bounds_ft[2] - 0.05 && w.end <= r.bounds_ft[3] + 0.05;
  // 1. the shower window of the front bedroom suite's bathroom: vertically larger, width and place as they were
  const w11 = win('W11'), bath3 = room(/^bedroom 3 bathroom$/i);
  assert.ok(w11 && bath3, 'the schedule has W11 and the Bedroom 3 bathroom');
  assert.ok(inWestWall(w11, bath3), 'W11 is in the west wall of the Bedroom 3 bathroom');
  assert.ok(Math.abs(w11.sill - 3.0) < 0.01 && Math.abs(w11.head - 7.5) < 0.01, 'sill 3\'-0", head 7\'-6" (the owner\'s answer), got ' + w11.sill + ' / ' + w11.head);
  assert.ok(Math.abs(w11.height - (w11.head - w11.sill)) < 0.01 && Math.abs(w11.height - 4.5) < 0.01, '4\'-6" tall, got ' + w11.height);
  assert.ok(Math.abs(w11.width - 3) < 0.05 && Math.abs(w11.end - w11.start - w11.width) < 0.02, 'still 3\'-0" wide, got ' + w11.width);
  assert.ok(w11.head <= 8 && (w11.panes || []).every((p) => p.height <= w11.height && p.width <= w11.width + 0.01), 'its panes fit the opening');
  // 2. the primary bathroom's west window: 3 ft wide as on the sheet, the owner's 2 ft sill kept
  const w13 = win('W13'), bath = room(/^primary bathroom$/i);
  assert.ok(w13 && bath, 'the schedule has W13 and the primary bathroom');
  assert.ok(inWestWall(w13, bath), 'W13 is in the west wall of the primary bathroom');
  assert.ok(Math.abs(w13.width - 3) < 0.02 && Math.abs(w13.end - w13.start - 3) < 0.02, 'three feet wide, got ' + w13.width + ' (' + w13.start + ' .. ' + w13.end + ')');
  assert.ok(Math.abs(w13.sill - 2) < 0.01 && w13.head >= 7.9, 'from the 2\'-0" sill of the third round to the ceiling, got ' + w13.sill + ' / ' + w13.head);
  // the skylight moved with the shower, to the bath's north-west corner (west and north of the room's middle)
  const sky = measurements.windows.find((w) => w.kind === 'skylight' && /primary bath/i.test(w.name));
  assert.ok(sky && Array.isArray(sky.p), 'the primary bathroom has its skylight');
  const [bx0, bx1, bz0, bz1] = bath.bounds_ft;
  assert.ok(sky.p[0] > bx0 && sky.p[0] < (bx0 + bx1) / 2 && sky.p[2] > bz0 && sky.p[2] < (bz0 + bz1) / 2, 'over the shower in the north-west corner, got (' + sky.p[0] + ', ' + sky.p[2] + ') in ' + bath.bounds_ft);
  // 3. the primary bedroom keeps both west windows: W14, which the sheet omits, south of the other one
  const w14 = win('W14'), bed = room(/^primary bedroom$/i);
  assert.ok(w14, 'the schedule still has W14 (the owner keeps the second west window)');
  assert.ok(inWestWall(w14, bed), 'W14 is in the west wall of the primary bedroom');
  const west = measurements.windows.filter((w) => inWestWall(w, bed)).sort((a, b) => a.start - b.start);
  assert.ok(west.length === 2 && west[1] === w14 && west[0].end < w14.start, 'the bedroom has two west windows, W14 the southern one (' + west.map((w) => w.id + ' ' + w.start + ' .. ' + w.end).join(', ') + ')');
  const svg = fs.readFileSync(disk('assets/plans/dimension-plan.svg'), 'utf8');
  for (const id of ['W11', 'W13', 'W14']) assert.ok(svg.includes('data-measure="' + id + '"'), 'dimension-plan.svg has a target for ' + id);
});

test('design sheet: the primary bathroom\'s view and the sixth round tell of the stone vanity wall, the closet with its door and the taller window', () => {
  const key = design.order.find((k) => /^primary bathroom$/i.test(design.views[k].label));
  assert.ok(key, 'the Design sheet has a tab "Primary bathroom"');
  const v = design.views[key], text = v.title + ' ' + v.text;
  const bath = tour.rooms.find((r) => /^primary bathroom$/i.test(r.label));
  assert.ok(byId.has(v.node) && holds(bath, byId.get(v.node).p[0], byId.get(v.node).p[2]), '"Walk into this room" stands in the primary bathroom (' + v.node + ')');
  assert.match(text, /stone[^.]*(vanity|south) wall|(vanity|south) wall[^.]*stone/i, 'the stone is on the vanity wall');
  assert.match(text, /shower[^.]*north-west|north-west[^.]*shower/i, 'the shower stands in the north-west corner');
  // the finishes of the third round are gone (the walls of the seventh round have a test of their own below)
  assert.doesNotMatch(text, /sage|subway|encaustic|brass|blue-and-cream/i, 'no word of the green shower tile, the brass or the patterned floor');
  // no view describes the open dressing area or its wardrobes any more
  const stale = Object.entries(design.views).filter(([, o]) => /dressing area|open wardrobe/i.test(o.title + ' ' + o.text)).map(([k]) => k);
  assert.deepEqual(stale, [], 'views that still describe the open dressing area');
  // the owner's sixth round
  const round = (design.owner_changes || []).find((r) => r.round === 6);
  assert.ok(round && round.changes.length >= 4, 'design.json has the sixth round of the owner\'s changes');
  const says = (...res) => round.changes.some((c) => res.every((re) => re.test(c)));
  assert.ok(says(/walk-in closet/i, /door/i), 'the walk-in closet is a room with a door');
  assert.ok(says(/shower/i, /window/i, /3'-0"/, /7'-6"/), 'the front suite\'s shower window runs from a 3\'-0" sill to a 7\'-6" head');
  assert.ok(says(/stone/i, /vanity wall/i), 'the stone is on the vanity wall');
  assert.ok(says(/primary bedroom/i, /both west windows/i), 'both west windows of the primary bedroom are kept');
});

// ---- the owner's seventh round (2026-11-21) -------------------------------------------------------------
// The refrigerator stands in view beside the microwave, every window is white with grid bars, the primary
// bathroom's walls are white, the living room's fireplace is sealed with the sofa on that wall and the
// television opposite, and the sky is turned so that the yard faces north. No wall and no opening moves:
// the round is texts, and in the living room new sweeps around the new furniture for one that went (L5
// stood where the sofa is now). The only id written here is L5; rooms, cards, windows and views are found
// by their names, and places are held to the rule (which room, which side), not to coordinates.
const cardNamed = (re) => tour.highlights.map((id) => byId.get(id)).filter((s) => s && re.test(s.label));
// Where the line of sight of a sweep (its opening yaw) leaves a room's rectangle: {x, z, side} or null
// when it never enters the room.
function leaves(room, s) {
  const a = s.yaw * Math.PI / 180, d = [Math.sin(a), -Math.cos(a)], o = [s.p[0], s.p[2]], [x0, z0, x1, z1] = room.bounds;
  let t0 = 0, t1 = Infinity, side = null;
  for (const [k, lo, hi, low, high] of [[0, x0, x1, 'west', 'east'], [1, z0, z1, 'north', 'south']]) {
    if (Math.abs(d[k]) < 1e-9) { if (o[k] < lo || o[k] > hi) return null; continue; }
    const ta = (lo - o[k]) / d[k], tb = (hi - o[k]) / d[k], out = Math.max(ta, tb);
    t0 = Math.max(t0, Math.min(ta, tb));
    if (out < t1) { t1 = out; side = d[k] > 0 ? high : low; }
  }
  return t0 <= t1 ? { x: o[0] + d[0] * t1, z: o[1] + d[1] * t1, side } : null;
}

test('seventh round: sweep L5 is gone; the reel\'s "Living room" card stands in the living room and looks at the rear glass', (t) => {
  // the sweep that stood where the sofa is now: no sweep, and nothing still names it
  assert.ok(!byId.has('L5'), 'tour.json has no sweep L5');
  const naming = [...tour.sweeps.flatMap((s) => [...s.links, ...s.visible].map((id) => [s.id, id])), ...tour.highlights.map((id) => ['highlights', id]), ...tour.rooms.map((r) => [r.id, r.sweep]),
    ...[...measurements.rooms, ...measurements.windows, ...measurements.doors].map((x) => [x.id, x.node]), ...Object.entries(design.views).map(([k, v]) => ['view ' + k, v.node]), ...Object.keys(manifest.nodes).map((id) => ['panorama manifest', id])];
  assert.deepEqual([...new Set(naming.filter(([, id]) => id === 'L5').map(([who]) => who))], [], 'still naming L5');
  // one card "Living room", on a sweep that exists and stands in the living room
  const room = named(/^living room$/i);
  assert.ok(room, 'tour.json has the room "Living room"');
  const cards = cardNamed(/^living room$/i);
  assert.equal(cards.length, 1, 'one card "Living room" in the reel (' + tour.highlights.filter((id) => !byId.has(id) || /^living room$/i.test(byId.get(id).label)).join(', ') + ')');
  const card = cards[0];
  assert.ok(!card.outdoor && holds(room, card.p[0], card.p[2]) && card.room === room.id, 'its sweep ' + card.id + ' stands in the living room');
  assert.equal(room.sweep, card.id, 'a click on the room\'s name on the floor plan enters where the card does');
  // it shows the room at a glance: the rear glass ahead, so the television wall and the sofa wall are left and right of it
  const rear = [...measurements.windows, ...measurements.doors].filter((o) => /^living\b/i.test(o.name) && o.axis === 'x' && Math.abs(o.c - room.bounds[1]) < 1);
  assert.ok(rear.filter((o) => o.kind === 'window').length >= 2 && rear.some((o) => o.kind === 'door'), 'the schedule has the living room\'s rear glazing and its garden door (' + rear.map((o) => o.id).join(', ') + ')');
  const glass = rear.filter((o) => o.kind === 'window'), mid = (Math.min(...glass.map((o) => o.start)) + Math.max(...glass.map((o) => o.end))) / 2, wall = glass[0].c;
  const off = turn(card.yaw, bearing(card, mid, wall)), back = card.p[2] - wall, across = (card.p[0] - room.bounds[0]) / (room.bounds[2] - room.bounds[0]);
  assert.ok(off <= 30, 'the card opens looking at the rear glass (' + off.toFixed(1) + ' degrees off its middle)');
  assert.ok(back >= 10, 'from far enough back to have the room in the picture (' + back.toFixed(1) + ' ft from the glass)');
  assert.ok(across > 0.3 && across < 0.7, 'from the middle of the room\'s width, a side wall to its left and to its right (at ' + (across * 100).toFixed(0) + ' % of the width)');
  assert.ok(card.pitch <= 0 && card.pitch >= -10, 'level or a little down (pitch ' + card.pitch + ')');
  t.diagnostic('Living room card ' + card.id + ' at (' + card.p[0] + ', ' + card.p[2] + '), yaw ' + card.yaw + ', ' + back.toFixed(1) + ' ft from the rear glass');
});

test('seventh round: the living room\'s sweeps are one piece, with a stop in front of each opening of the rear wall', (t) => {
  const room = named(/^living room$/i), here = standing(room).filter((s) => s.room === room.id);
  assert.ok(here.length >= 6, 'sweeps stand in the living room (' + here.map((s) => s.id).join(', ') + ')');
  // from the dining end to the rear glass and to every other stop without leaving the room
  const mine = new Set(here.map((s) => s.id)), start = cardNamed(/^open living area$/i)[0] || here[0];
  assert.ok(mine.has(start.id), 'the card "Open living area" stands in the room (' + start.id + ')');
  const seen = new Set([start.id]), queue = [start.id];
  while (queue.length) for (const id of byId.get(queue.shift()).links) if (mine.has(id) && !seen.has(id)) { seen.add(id); queue.push(id); }
  assert.deepEqual([...mine].filter((id) => !seen.has(id)), [], 'sweeps of the living room that cannot be reached from ' + start.id + ' over links inside the room');
  // the rear wall: a stop within 3 ft of each of its openings, in front of it
  const rear = [...measurements.windows, ...measurements.doors].filter((o) => /^living\b/i.test(o.name) && o.axis === 'x' && Math.abs(o.c - room.bounds[1]) < 1);
  const at = rear.map((o) => [o, here.filter((s) => s.p[0] >= o.start && s.p[0] <= o.end && s.p[2] - o.c <= 3)]);
  assert.deepEqual(at.filter(([, list]) => !list.length).map(([o]) => o.id + ' ' + o.name), [], 'openings of the rear wall without a stop in front of them');
  // and the stop the schedule names for them is still one of the room's
  for (const o of rear) assert.ok(mine.has(o.node), '"Visit in 3D" of ' + o.id + ' stands in the living room (' + o.node + ')');
  t.diagnostic(here.length + ' sweeps: ' + here.map((s) => s.id).join(' ') + '; at the rear wall: ' + at.map(([o, list]) => o.id + ' ' + list.map((s) => s.id).join('+')).join(', '));
});

test('seventh round: the card of the open living area looks at the kitchen\'s tall wall at its hall end, where the refrigerator stands beside the microwave', (t) => {
  const cards = cardNamed(/^open living area$/i);
  assert.equal(cards.length, 1, 'one card "Open living area" in the reel');
  const card = cards[0], kitchen = named(/^kitchen/i), hall = named(/^hall$/i), garage = named(/^garage$/i);
  assert.ok(kitchen && hall && garage, 'tour.json has the kitchen, the hall and the garage');
  // the tall cabinet wall is the wall the kitchen shares with the garage; its hall end is the end nearest the hall
  const out = leaves(kitchen, card);
  assert.ok(out, 'the card\'s line of sight (yaw ' + card.yaw + ') crosses the kitchen');
  const beyond = { north: [out.x, out.z - 1.5], south: [out.x, out.z + 1.5], west: [out.x - 1.5, out.z], east: [out.x + 1.5, out.z] }[out.side], behind = roomAt(beyond[0], beyond[1]);
  assert.ok(behind && behind.id === garage.id, 'it ends on the wall between the kitchen and the garage (the ' + out.side + ' side; beyond it: ' + (behind && behind.label) + ')');
  const along = out.side === 'north' || out.side === 'south' ? [out.x, kitchen.bounds[0], kitchen.bounds[2], hall.at[0]] : [out.z, kitchen.bounds[1], kitchen.bounds[3], hall.at[1]];
  const share = (along[0] - along[1]) / (along[2] - along[1]), fromHall = Math.abs(along[3] - along[1]) < Math.abs(along[3] - along[2]) ? share : 1 - share;
  assert.ok(fromHall <= 1 / 3, 'in the third of that wall nearest the hall (' + (fromHall * 100).toFixed(0) + ' % along it from the hall end)');
  assert.ok(card.pitch <= 0 && card.pitch >= -15, 'level or a little down (pitch ' + card.pitch + ')');
  // the Design sheet's kitchen says what stands there
  const key = design.order.find((k) => /^kitchen$/i.test(design.views[k].label));
  assert.ok(key, 'the Design sheet has a tab "Kitchen"');
  const text = design.views[key].title + ' ' + design.views[key].text;
  assert.ok(text.split(/\.\s/).some((c) => /refrigerator/i.test(c) && /microwave/i.test(c) && /beside|next to/i.test(c)), 'the kitchen\'s view puts the refrigerator beside the microwave');
  assert.doesNotMatch(text, /pantry|behind (cabinet )?panels|panel-ready|integrated refrigerator|double (wall )?ovens?/i, 'no word of the refrigerator behind panels or of the second oven');
  t.diagnostic('card ' + card.id + ' yaw ' + card.yaw + ': its view meets the ' + out.side + ' wall at (' + out.x.toFixed(1) + ', ' + out.z.toFixed(1) + '), ' + (fromHall * 100).toFixed(0) + ' % from the hall end');
});

test('seventh round: every window and glazed door of the schedule has a white frame and grid bars; the skylights are as they were', (t) => {
  const glazed = [...measurements.windows.filter((w) => w.kind !== 'skylight'), ...measurements.doors.filter((d) => /glazed|glass/i.test(d.type))];
  assert.ok(glazed.length >= 15 && glazed.some((o) => o.kind === 'door'), 'the schedule lists the windows and the glazed garden door (' + glazed.length + ')');
  assert.deepEqual(glazed.filter((o) => !/white frame/i.test(o.type)).map((o) => o.id + ': ' + o.type), [], 'type texts that do not say "white frame"');
  assert.deepEqual(glazed.filter((o) => !/\bgrid\b/i.test(o.type)).map((o) => o.id + ': ' + o.type), [], 'type texts that do not mention the grid');
  // the grid is given as lites wide x high, so that a reader can count them on the picture
  assert.deepEqual(glazed.filter((o) => !/\d+ lites? wide\s*[×x]\s*\d+ high|one lite/i.test(o.type)).map((o) => o.id + ': ' + o.type), [], 'type texts without the number of lites');
  const sky = measurements.windows.filter((w) => w.kind === 'skylight');
  assert.deepEqual(sky.filter((w) => /grid|white frame/i.test(w.type)).map((w) => w.id), [], 'skylights have no grid');
  // nothing in the schedule or on the Design sheet still tells of black or steel frames, or of a picture window
  const all = [...measurements.windows, ...measurements.doors, ...measurements.rooms];
  assert.deepEqual(all.filter((o) => /black|steel|picture (window|glazing)/i.test((o.type || '') + ' ' + (o.note || '') + ' ' + o.name)).map((o) => o.id), [], 'schedule entries that mention black or steel frames');
  const dark = Object.entries(design.views).filter(([, v]) => (v.title + '. ' + v.text).split(/\.\s/).some((c) => /black|steel/i.test(c) && /window|frame|sash|mullion|grid|glazing/i.test(c))).map(([k]) => k);
  assert.deepEqual(dark, [], 'Design views with a sentence about black or steel windows');
  const says = (re) => design.order.filter((k) => (design.views[k].title + '. ' + design.views[k].text).split(/\.\s/).some((c) => /white/i.test(c) && /grid/i.test(c) && re.test(c)));
  assert.ok(says(/window|frame/i).length >= 3, 'the Design views that describe a window say white and grid (' + says(/window|frame/i).join(', ') + ')');
  t.diagnostic(glazed.length + ' glazed openings, ' + sky.length + ' skylights; views telling of white grid windows: ' + says(/window|frame/i).join(', '));
});

test('seventh round: the primary bathroom is white, no text tells of a fireplace, and the change list has the owner\'s five items', (t) => {
  // the bath: white walls and one stone wall, in the view and in the schedule's note
  const key = design.order.find((k) => /^primary bathroom$/i.test(design.views[k].label)), bath = design.views[key].title + ' ' + design.views[key].text;
  assert.match(bath, /wall[^.]*\bwhite\b|\bwhite\b[^.]*wall/i, 'the primary bathroom\'s view says its walls are white');
  assert.match(bath, /stone[^.]*(vanity|south) wall|(vanity|south) wall[^.]*stone/i, 'and keeps the stone on the vanity wall');
  assert.doesNotMatch(bath, /wainscot|grey-green|gray-green|green|cap rail|cream/i, 'no word of the green board wainscot, its cap rail or the cream plaster and tile');
  for (const [where, rows] of [['schedule', measurements.rooms], ['room table', measurements.audit || []]]) {
    const row = rows.find((r) => /^primary bathroom$/i.test(r.name));
    assert.ok(row && /\bwhite\b/i.test(row.note || '') && !/wainscot|green|cream/i.test(row.note || ''), 'the ' + where + '\'s note of the primary bathroom tells of white walls');
  }
  // the fireplace: sealed without a trace, so only the change list speaks of it
  const texts = [...Object.entries(design.views).map(([k, v]) => ['view ' + k, v.label + ' ' + v.title + ' ' + v.text]), ...tour.sweeps.map((s) => ['sweep ' + s.id, s.label]), ...tour.rooms.map((r) => ['room ' + r.id, r.label]),
    ...[...measurements.rooms, ...measurements.windows, ...measurements.doors, ...(measurements.audit || [])].map((o) => [o.id, o.name + ' ' + (o.type || '') + ' ' + (o.note || '')])];
  assert.deepEqual(texts.filter(([, text]) => /fire ?place|hearth|firebox|mantel/i.test(text)).map(([who]) => who), [], 'texts that still tell of a fireplace');
  // a view of the living room, when the sheet has one, shows the new arrangement from inside the room
  const living = design.order.filter((k) => /living/i.test(design.views[k].label));
  for (const k of living) {
    const v = design.views[k], room = named(/^living room$/i);
    assert.match(v.title + ' ' + v.text, /sofa/i, 'view ' + k + ' tells of the sofa');
    assert.match(v.title + ' ' + v.text, /television|\bTV\b/, 'view ' + k + ' tells of the television');
    assert.ok(byId.has(v.node) && holds(room, byId.get(v.node).p[0], byId.get(v.node).p[2]), '"Walk into this room" of view ' + k + ' stands in the living room (' + v.node + ')');
  }
  // the owner's seventh round: the five items, in the owner's order, one entry each
  const rounds = design.owner_changes || [], round = rounds.find((r) => r.round === 7);
  assert.ok(round, 'design.json has the seventh round of the owner\'s changes (rounds: ' + rounds.map((r) => r.round).join(', ') + ')');
  assert.match(String(round.date), /^\d{4}-\d{2}-\d{2}$/, 'with its date');
  const items = [
    ['the refrigerator beside the microwave', [/refrigerator/i, /microwave/i]],
    ['white windows with grid lines', [/window/i, /\bwhite\b/i, /\bgrid\b/i]],
    ['the primary bathroom\'s white walls', [/primary bath/i, /\bwhite\b/i, /wall/i]],
    ['the fireplace sealed, the sofa on that side, the television opposite', [/fireplace/i, /sofa/i, /television|\bTV\b/]],
    ['daylight for a yard that faces north', [/north/i, /yard|garden/i, /sun|sky|daylight/i]],
  ];
  assert.ok(round.changes.length >= items.length, 'it lists the owner\'s five items (' + round.changes.length + ' entries)');
  items.forEach(([what, res], i) => assert.ok(res.every((re) => re.test(round.changes[i])), 'entry ' + (i + 1) + ' is about ' + what + ': "' + String(round.changes[i]).slice(0, 80) + '…"'));
  // an entry beyond the five is not a sixth change: it says what was set aside or stays as it was
  const more = round.changes.slice(items.length);
  assert.deepEqual(more.filter((c) => !/set aside|as (they|it) (were|was)|not part of this round|unchanged/i.test(c)).map((c) => c.slice(0, 80)), [], 'entries beyond the five that read as further changes');
  if (more.length) t.diagnostic('beyond the five items: ' + more.map((c) => '"' + c.slice(0, 70) + '…"').join(', '));
  if (!living.length) t.diagnostic('the Design sheet has no tab for the living room: the sealed fireplace, the sofa and the television are told in the change list only');
});
