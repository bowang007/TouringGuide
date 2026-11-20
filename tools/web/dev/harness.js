// Test harness of the tour engine (assets/js/tour/engine.js). Not part of the site.
//
// Query parameters:
//   depth=1024        depth cube size        pool=4   depth cube pool
//   dpr=1             canvas pixels per CSS pixel
//   quiet=1           hide the status line (screenshots)
//   demo=inside|doll|plan|exterior   interactive demo (drag = look / orbit, wheel = zoom, click = pick
//                     and move); sweep=K0 start sweep
//
// window.H is the test API (tools/web/dev/run_engine_checks.js). H.ready resolves when the model, the
// sweeps, the panorama manifest and the footprint are loaded.
import * as THREE from 'three';
import { panoPixels, extractView, psnr } from './reference.js';

const q = new URLSearchParams(location.search);
const ROOT = new URL('../../../', import.meta.url);
const url = (p) => new URL(p, ROOT).href;
const { createEngine } = await import(url('assets/js/tour/engine.js'));
const canvas = document.getElementById('c');
const statusEl = document.getElementById('s');
if (q.get('quiet')) document.body.classList.add('quiet');
const dpr = parseFloat(q.get('dpr') || '1');
const size = () => ({ width: Math.round(innerWidth * dpr), height: Math.round(innerHeight * dpr) });
canvas.width = size().width;
canvas.height = size().height;

const getJson = (p) => fetch(url(p), { cache: 'no-cache' }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
const status = (t) => { statusEl.textContent = t; };

// ---- data ------------------------------------------------------------------------------------
const tour = await getJson('assets/data/tour.json');
const scene = tour ? null : await getJson('tools/render/data/scene.json');
const manifest = await getJson('assets/panos/manifest.json');
// sweeps: {id, p, yaw (radians), label}; tour.json has degrees, scene.json radians
const sweeps = tour
  ? tour.sweeps.map((s) => ({ id: s.id, p: s.p, yaw: (s.yaw || 0) * Math.PI / 180, label: s.label, floor: s.floor, visible: s.visible, links: s.links }))
  : scene.tour.nodes.map((n) => ({ id: n.id, p: n.p, yaw: n.yaw || 0, label: n.label }));
for (const s of sweeps) s.offset = (manifest && manifest.nodes[s.id] && manifest.nodes[s.id].offset) || 0;
const byId = Object.fromEntries(sweeps.map((s) => [s.id, s]));
// footprint: tour.json's, else the foundation slabs (and the garage slab) of the scene
let footprint = tour && tour.footprint;
if (!footprint) {
  footprint = scene.objects
    .filter((o) => /foundation/i.test(o.name || '') || o.name === 'Garage concrete floor')
    .map((o) => [o.p[0] - o.s[0] / 2, o.p[2] - o.s[2] / 2, o.p[0] + o.s[0] / 2, o.p[2] + o.s[2] / 2].map((v) => Math.round(v * 1000) / 1000));
}
const extent = (tour && tour.extent) || (scene && scene.extent) || [39.42, 55.9];

// ---- engine ----------------------------------------------------------------------------------
const opts = {
  depthSize: parseInt(q.get('depth') || '1024', 10),
  depthPool: parseInt(q.get('pool') || '4', 10),
  interior: [0, 0, extent[0], extent[1]],
  footprint, sweeps, mipmap8k: q.get('mip8k') === '1',
};
const E = createEngine(canvas, opts);
const gl = E.gl;
status('loading model…');
const t0 = performance.now();
await E.load(url('assets/model/house.glb'), (p) => status('loading model ' + Math.round(p * 100) + '%'));
const loadMs = performance.now() - t0;

const dir = (yaw, pitch = 0) => [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];
const add = (a, b, k = 1) => [a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k];
const lerp = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const blobs = new Map();
function panoBlob(id, level) {
  const node = manifest.nodes[id];
  const rel = node.levels[level];
  if (!rel) throw new Error(`no ${level} panorama for ${id}`);
  const u = url('assets/panos/' + rel);
  if (!blobs.has(u)) blobs.set(u, fetch(u).then((r) => r.blob()));
  return blobs.get(u);
}

async function loadPano(id, level = '4k') {
  if (E.hasPanorama(id, level)) return true;
  const bmp = await createImageBitmap(await panoBlob(id, level));
  return E.setPanorama(id, bmp, level);
}

// An 8192 x 4096 image made from the 4K file (no 8K renders yet): exercises the 8K path.
async function fake8k(id) {
  const t = performance.now();
  const bmp = await createImageBitmap(await panoBlob(id, '4k'));
  const c = new OffscreenCanvas(bmp.width * 2, bmp.height * 2);
  c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
  bmp.close();
  const big = await createImageBitmap(c);
  const decodeMs = performance.now() - t;
  const ok = E.setPanorama(id, big, '8k');
  return { ok, width: c.width, decodeMs };
}

function view(eye, yaw, pitch, fovY, extra = {}) {
  return Object.assign({ eye, aim: add(eye, dir(yaw, pitch)), fovY, ...size() }, extra);
}

let last = null;
function render(v) {
  last = v;
  return E.render(Object.assign({}, size(), v));
}

// The frame as RGBA rows top-down (the context keeps its drawing buffer).
function pixels() {
  const { width, height } = size();
  const buf = new Uint8Array(width * height * 4);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, buf);
  const out = new Uint8Array(buf.length);
  const row = width * 4;
  for (let y = 0; y < height; y++) out.set(buf.subarray((height - 1 - y) * row, (height - y) * row), y * row);
  return out;
}

// Fractions of the frame that are (near) black, magenta (the debug bake colour) or the background.
function frameStats(bg) {
  const p = pixels();
  let black = 0, magenta = 0, back = 0;
  const n = p.length / 4;
  for (let i = 0; i < p.length; i += 4) {
    const r = p[i], g = p[i + 1], b = p[i + 2];
    if (r < 6 && g < 6 && b < 6) black++;
    if (r > 235 && g < 25 && b > 235) magenta++;
    if (bg && Math.abs(r - bg[0]) < 3 && Math.abs(g - bg[1]) < 3 && Math.abs(b - bg[2]) < 3) back++;
  }
  return { black: black / n, magenta: magenta / n, background: back / n };
}

// (a) Rest state: the frame against the same view taken from the panorama file.
async function restPsnr(id, o = {}) {
  const s = byId[id];
  const level = o.level || '4k';
  E.setMode('inside');
  E.setSweepBlend(id, null, 0);
  await loadPano(id, level);
  await E.prepare(id);
  const yaw = o.yaw !== undefined ? o.yaw : s.yaw, pitch = o.pitch || 0, fovY = o.fovY || 64 * Math.PI / 180;
  render(view(s.p, yaw, pitch, fovY));
  const frame = pixels();
  const info = E.projectionInfo();
  const pano = await panoPixels(url('assets/panos/' + manifest.nodes[id].levels[level]));
  const ref = extractView(pano, { yaw, pitch, fovY, ...size(), offset: s.offset });
  return { id, psnr: psnr(frame, ref), pure: info.pure, calls: E.stats().calls, resting: E.resting, yaw, pitch };
}

// (b) A move from A to B: camera on the straight line, blend t.
async function blendFrame(a, b, t, o = {}) {
  E.setMode('inside');
  E.setSweepBlend(a, b, t);          // first: the two sweeps of a move are never evicted
  await Promise.all([loadPano(a, o.level || '4k'), loadPano(b, o.level || '4k')]);
  if (!o.noPrepare) await Promise.all([E.prepare(a), E.prepare(b)]);
  const yaw = o.yaw !== undefined ? o.yaw : Math.atan2(byId[b].p[0] - byId[a].p[0], -(byId[b].p[2] - byId[a].p[2]));
  const eye = lerp(byId[a].p, byId[b].p, o.s !== undefined ? o.s : t);
  render(view(eye, yaw, o.pitch || 0, o.fovY || 64 * Math.PI / 180));
  return { t, eye, yaw, info: E.projectionInfo(), calls: E.stats().calls };
}

// Orbit camera around the house (dollhouse): azimuth clockwise from south, elevation above the horizon.
const houseCenter = [extent[0] / 2, 3, extent[1] / 2];
function orbitView(azimuth, elevation, radius, fovY = 0.8, target = houseCenter) {
  const eye = [target[0] + radius * Math.sin(azimuth) * Math.cos(elevation), target[1] + radius * Math.sin(elevation), target[2] + radius * Math.cos(azimuth) * Math.cos(elevation)];
  return { eye, aim: target, fovY, near: 0.5, far: 1200, ...size() };
}

function planView(halfHeight = 31, center = [extent[0] / 2, extent[1] / 2]) {
  return { ortho: { halfHeight }, eye: [center[0], 60, center[1]], aim: [center[0], 0, center[1]], up: [0, 0, -1], near: 1, far: 200, ...size() };
}

// (c) pick against a brute-force ray cast of the same view (every inside class, no glass).
function pickCompare(n = 200, seed = 7) {
  let s = seed;
  const rnd = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  const out = { n: 0, miss: 0, maxErr: 0, meanErr: 0, bad: [], normalDot: 0, cls: {} };
  for (let i = 0; i < n; i++) {
    const x = rnd() * 1.9 - 0.95, y = rnd() * 1.9 - 0.95;
    const a = E.pick(x, y);
    const b = E.pick(x, y, { raycast: true, classes: ['base', 'wall', 'ceiling', 'furniture', 'decor_high', 'landscape'] });
    if (!a || !b) { out.miss++; continue; }
    const err = Math.abs(a.distance - b.distance);
    out.n++;
    out.meanErr += err;
    out.maxErr = Math.max(out.maxErr, err);
    out.normalDot += a.normal[0] * b.normal[0] + a.normal[1] * b.normal[1] + a.normal[2] * b.normal[2];
    out.cls[a.cls === b.cls ? 'same' : 'diff'] = (out.cls[a.cls === b.cls ? 'same' : 'diff'] || 0) + 1;
    if (err > 0.25) out.bad.push({ x, y, depth: a.distance, ray: b.distance, a: a.cls, b: b.cls });
  }
  out.meanErr /= Math.max(1, out.n);
  out.normalDot /= Math.max(1, out.n);
  out.bad = out.bad.slice(0, 12);
  return out;
}

// (g) Average wall-clock time of a render, forcing completion with a one-pixel readback.
function timeFrames(n, make) {
  const px = new Uint8Array(4);
  const times = [];
  for (let i = 0; i < n; i++) {
    const v = make(i);
    const t = performance.now();
    render(v);
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
    times.push(performance.now() - t);
  }
  times.sort((a, b) => a - b);
  return { n, median: times[Math.floor(n / 2)], p90: times[Math.floor(n * 0.9)], max: times[n - 1], min: times[0] };
}

// Frame intervals of a requestAnimationFrame loop that renders every frame.
function rafLoop(ms, make) {
  return new Promise((resolve) => {
    const stamps = [];
    const start = performance.now();
    const tick = (now) => {
      stamps.push(now);
      render(make((now - start) / ms));
      if (now - start < ms) requestAnimationFrame(tick);
      else {
        const d = stamps.slice(1).map((t, i) => t - stamps[i]).sort((a, b) => a - b);
        resolve({ frames: d.length, fps: 1000 * d.length / (stamps[stamps.length - 1] - stamps[0]), median: d[Math.floor(d.length / 2)], p95: d[Math.floor(d.length * 0.95)], max: d[d.length - 1] });
      }
    };
    requestAnimationFrame(tick);
  });
}

// ---- legacy exterior API (exactly what the page's ext* functions do) ---------------------------
const ext = { manifest: null };
function mul(a, b) { const c = new Float32Array(16); for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) for (let k = 0; k < 4; k++) c[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k]; return c; }
function lookAt(e, t) {
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const z = norm(sub(e, t)), x = norm(cross([0, 1, 0], z)), y = cross(z, x);
  return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, e), -dot(y, e), -dot(z, e), 1]);
}
function perspective(fov, aspect) { const f = 1 / Math.tan(fov / 2), near = 0.10, far = 350; return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0]); }
const extDir = (t, p) => [Math.sin(t) * Math.cos(p), Math.sin(p), Math.cos(t) * Math.cos(p)];

async function extLoad() {
  if (ext.manifest) return ext.manifest;
  const m = await getJson('assets/exterior/manifest.json');
  m.vfov = 2 * Math.atan(Math.tan(m.hfov * Math.PI / 360) / m.aspect);
  m.byId = {};
  for (const f of m.frames) {
    f.dir = extDir(f.theta, f.phi);
    f.eye = m.target.map((v, i) => v + f.radius * f.dir[i]);
    f.matrix = Array.from(mul(perspective(m.vfov, m.aspect), lookAt(f.eye, m.target)));
    m.byId[f.id] = f;
  }
  ext.manifest = m;
  return m;
}

async function extFrame(id, full = false) {
  const m = await extLoad();
  const f = m.byId[id];
  const have = E.hasPanorama(id);
  if (have && (have.full || !full)) return;
  const blob = await (await fetch(url('assets/exterior/' + (full ? f.full : f.half)))).blob();
  const img = await createImageBitmap(blob);
  E.setPanorama(id, img, f.eye, 0, full, false, { matrix: f.matrix });
}

// Renders the exterior orbit the legacy way: targets [{id, weight}], camera at theta / phi / radius
// around the manifest target, repeated frames until the eased weights and the fade-in have settled.
async function extRender(targets, theta, phi, radius, o = {}) {
  const m = await extLoad();
  for (const t of targets) await extFrame(t.id, !!o.full);
  E.applyVisibility({ mode: 'exterior', cut: true, furniture: true, garden: true });
  E.setAdaptation(null, null);
  E.setProjection(targets, []);
  const d = extDir(theta, phi);
  const eye = m.target.map((v, i) => v + radius * d[i]);
  const { width, height } = size();
  const fov = o.fov || Math.min(m.vfov * 0.96, Math.PI * 0.255);
  for (let i = 0; i < (o.frames || 40); i++) {
    E.resetState();
    E.render(eye, m.target, fov, width, height, 1);
    E.resetState();
    await sleep(25);
  }
  return { info: E.projectionInfo(), stats: E.stats(), eye, fov };
}

// The canvas against the frame file itself: with the camera on frame `id` (extRender on its theta / phi /
// radius, weight 1) the view is the middle of that picture, a plain crop. Both are scaled to `width` px
// with the 2D canvas, so nothing of the engine is used for the reference. -> PSNR in dB.
async function extPsnr(id, fov, width = 700) {
  const m = await extLoad(), f = m.byId[id];
  const img = await createImageBitmap(await (await fetch(url('assets/exterior/' + f.full))).blob());
  const w = width, h = Math.round(width * canvas.height / canvas.width);
  const hy = Math.tan(fov / 2) / Math.tan(m.vfov / 2), hx = hy * (canvas.width / canvas.height) / m.aspect;
  const scaled = (source, sx, sy, sw, sh) => {
    const g = new OffscreenCanvas(w, h).getContext('2d', { willReadFrequently: true });
    g.drawImage(source, sx, sy, sw, sh, 0, 0, w, h);
    return g.getImageData(0, 0, w, h).data;
  };
  const a = scaled(canvas, 0, 0, canvas.width, canvas.height);
  const b = scaled(img, img.width / 2 * (1 - hx), img.height / 2 * (1 - hy), img.width * hx, img.height * hy);
  img.close();
  let se = 0;
  for (let i = 0; i < a.length; i += 4) for (let k = 0; k < 3; k++) { const d = a[i + k] - b[i + k]; se += d * d; }
  return se === 0 ? 99 : 10 * Math.log10(255 * 255 / (se / (a.length / 4 * 3)));
}

// ---- demo ------------------------------------------------------------------------------------
const demo = q.get('demo');
const H = {
  E, THREE, tour, manifest, sweeps, byId, footprint, extent, loadMs, size, dir, view, render, pixels, frameStats,
  loadPano, fake8k, restPsnr, blendFrame, orbitView, planView, pickCompare, timeFrames, rafLoop, sleep,
  extLoad, extFrame, extRender, extPsnr, lerp,
  get last() { return last; },
};
window.H = H;
window.E = E;
status(`engine.js · model ${Math.round(loadMs)} ms · ${sweeps.length} sweeps · ${footprint.length} footprint rects`);
H.ready = true;
document.title = 'READY';

if (demo) {
  let id = q.get('sweep') || (tour && tour.start) || 'K0';
  let yaw = byId[id].yaw, pitch = 0, fov = 64 * Math.PI / 180;
  let az = 0.6, el = 0.75, rad = 95, half = 31;
  let mode = demo === 'doll' ? 'dollhouse' : demo === 'plan' ? 'floorplan' : 'inside';
  let move = null;
  E.setBackground(0x16181d);
  // rings on the floor at every other sweep, a reticle under the cursor
  const ringGeo = E.ring(0.55, 0.95);
  const rings = sweeps.map((s) => {
    const m = new THREE.Mesh(ringGeo, E.overlayMaterial({ color: 0xffffff, opacity: 0.55, soft: 0.3 }));
    m.position.set(s.p[0], (s.floor !== undefined ? s.floor : 0.02) + 0.06, s.p[2]);
    m.userData.id = s.id;
    E.overlay.add(m);
    return m;
  });
  const reticle = new THREE.Mesh(E.ring(0.28, 0.42), E.overlayMaterial({ color: 0xffffff, opacity: 0.9, soft: 0.2 }));
  reticle.visible = false;
  E.overlay.add(reticle);
  await loadPano(id, '4k');
  E.setMode(mode);
  E.setSweepBlend(id, null, 0);
  const current = () => {
    if (mode === 'dollhouse') return orbitView(az, el, rad);
    if (mode === 'floorplan') return planView(half);
    const eye = move ? lerp(byId[move.a].p, byId[move.b].p, move.s) : byId[id].p;
    return view(eye, yaw, pitch, fov);
  };
  let viewDirty = true;
  const loop = (now) => {
    if (move) {
      const u = Math.min(1, (now - move.start) / move.dur);
      move.s = u * u * (3 - 2 * u);
      E.setSweepBlend(move.a, move.b, move.s);
      viewDirty = true;
      if (u >= 1) { id = move.b; move = null; E.setSweepBlend(id, null, 0); }
    }
    for (const r of rings) r.visible = mode === 'inside' && r.userData.id !== id;
    if (viewDirty || E.dirty()) {
      render(current());
      viewDirty = false;
      const i = E.projectionInfo();
      status(`${mode} · ${id} · ${i.pure ? 'pure panorama' : i.on ? 'projected' : 'bake'} · calls ${E.stats().calls} · drag / wheel / click, keys 1 2 3 = inside / dollhouse / plan`);
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
  const ndc = (e) => [e.clientX / innerWidth * 2 - 1, 1 - e.clientY / innerHeight * 2];
  const go = async (to) => {
    if (move || to === id) return;
    await loadPano(to, '4k');
    await E.prepare(to);
    move = { a: id, b: to, s: 0, start: performance.now(), dur: 900 };
  };
  let drag = null;
  canvas.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY, moved: false }; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', (e) => {
    if (drag) {
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
      drag.x = e.clientX; drag.y = e.clientY;
      if (mode === 'inside') { yaw -= dx * 0.0035; pitch = Math.max(-1.4, Math.min(1.4, pitch + dy * 0.0035)); }
      else if (mode === 'dollhouse') { az -= dx * 0.006; el = Math.max(0.12, Math.min(1.5, el + dy * 0.005)); }
      viewDirty = true;
      return;
    }
    const hit = E.pick(...ndc(e));
    reticle.visible = !!hit && mode === 'inside';
    if (hit) {
      reticle.position.set(hit.point[0] + hit.normal[0] * 0.04, hit.point[1] + hit.normal[1] * 0.04, hit.point[2] + hit.normal[2] * 0.04);
      reticle.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(...hit.normal));
    }
    E.invalidate();
  });
  canvas.addEventListener('pointerup', (e) => {
    const was = drag;
    drag = null;
    if (!was || was.moved) return;
    const hit = E.pick(...ndc(e));
    if (!hit) return;
    let best = null;
    for (const s of sweeps) {
      const d = Math.hypot(s.p[0] - hit.point[0], s.p[2] - hit.point[2]);
      if (!best || d < best.d) best = { s, d };
    }
    if (mode !== 'inside') {
      mode = 'inside'; id = best.s.id; yaw = byId[id].yaw; pitch = 0;
      loadPano(id, '4k').then(() => { E.setMode('inside'); E.setSweepBlend(id, null, 0); viewDirty = true; });
    } else go(best.s.id);
  });
  canvas.addEventListener('wheel', (e) => {
    const k = Math.exp(e.deltaY * 0.001);
    if (mode === 'inside') fov = Math.max(0.5, Math.min(1.7, fov * k));
    else if (mode === 'dollhouse') rad = Math.max(30, Math.min(200, rad * k));
    else half = Math.max(8, Math.min(60, half * k));
    viewDirty = true;
    e.preventDefault();
  }, { passive: false });
  addEventListener('keydown', (e) => {
    const m = { 1: 'inside', 2: 'dollhouse', 3: 'floorplan' }[e.key];
    if (!m) return;
    mode = m;
    E.setMode(m);
    viewDirty = true;
  });
  addEventListener('resize', () => { viewDirty = true; });
}
