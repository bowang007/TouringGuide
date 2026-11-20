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

// Design section 3: the laundry closet and what the web data must say about it.
test('laundry closet: room M13, door D17, plan targets, a sweep in front of it', () => {
  const room = measurements.rooms.find((r) => r.id === 'M13');
  assert.ok(room, 'measurements.json has room M13');
  assert.match(room.name, /laundry/i);
  assert.ok(Math.abs(room.width_ft - 3.08) < 0.2 && Math.abs(room.depth_ft - 3.0) < 0.2, 'clear size about 3\'-1" x 3\'-0", got ' + room.width_ft + ' x ' + room.depth_ft);
  const door = measurements.doors.find((d) => d.id === 'D17');
  assert.ok(door, 'measurements.json has door D17');
  assert.ok(Math.abs(door.width - 2.5) < 0.1 && Math.abs(door.height - 6.67) < 0.1, 'door 2\'-6" x 6\'-8", got ' + door.width + ' x ' + door.height);
  assert.ok((measurements.audit || []).some((a) => /laundry/i.test(a.name)), 'the room table (audit) lists the laundry closet');
  const tr = tour.rooms.find((r) => r.tag === 'M13');
  assert.ok(tr, 'tour.json has a room with tag M13');
  assert.match(tr.label, /laundry/i);
  const cx = (21.218 + 25.051) / 2, cz = (27.641 + 31.058) / 2;
  assert.ok(Math.abs(tr.at[0] - cx) < 1.5 && Math.abs(tr.at[1] - cz) < 1.5, 'the room sits in the kitchen\'s south-west corner');
  const near = tour.sweeps.filter((s) => Math.hypot(s.p[0] - cx, s.p[2] - cz) < 8);
  assert.ok(near.length > 0, 'a sweep stands within 8 ft of the closet');
  assert.ok(byId.has(tr.sweep) && Math.hypot(byId.get(tr.sweep).p[0] - cx, byId.get(tr.sweep).p[2] - cz) < 8, 'the room\'s own sweep faces the closet');
  // nobody can stand in the closet: the sweep in front of it is its sweep (room chip, reel, a click on the room)
  assert.equal(byId.get(tr.sweep).room, tr.id, 'the sweep in front of the closet belongs to the closet');
  assert.ok(tour.highlights.includes(tr.sweep), 'the highlight reel has the laundry closet');
  assert.match(byId.get(tr.sweep).label, /laundry/i, 'and names it');
});

test('laundry closet: design view "LC" and the fourth round of owner\'s changes', () => {
  assert.ok(design.order.includes('LC') && design.views.LC, 'design.json has the view LC in its tab order');
  assert.match(design.views.LC.label, /laundry/i);
  assert.ok(exists(design.views.LC.image), 'the Laundry still exists: ' + design.views.LC.image);
  const rounds = (design.owner_changes || []).map((r) => r.round);
  assert.ok(rounds.includes(4), 'owner_changes has a fourth round (rounds: ' + rounds.join(', ') + ')');
  const fourth = design.owner_changes.find((r) => r.round === 4);
  assert.ok(fourth.changes.some((c) => /laundry|washer/i.test(c)), 'the fourth round mentions the laundry closet');
});
