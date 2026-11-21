// The viewer: the mode machine, the one requestAnimationFrame loop and the input router of the tour.
//
// A MODE is a controller registered by name ('inside', 'dollhouse', 'floorplan', 'exterior'). Exactly one
// is active; it owns the camera and draws the frame through viewer.render(view). The viewer owns
// everything the modes share: the canvas size, pointer / wheel / key routing, events, the sweep graph,
// panorama URLs and the calls into the engine (assets/js/tour/engine.js).
//
// Controller interface (every member is optional except frame):
//   enter(from, opts)      become active; `from` = previous mode name or null. May return a Promise that
//                          resolves when the mode shows what was asked for. Also called while already
//                          active (from === own name) to apply new opts, e.g. {sweep: 'K0'}.
//   leave(to)              stop being active (cancel animations, hide own DOM).
//   depart(to, opts)       asked before leave(): return a Promise to make the way out itself (a flight
//                          into the next view) and call viewer.setMode(to, {..., direct: true}) at its
//                          end; return nothing to be left at once.
//   frame(dt, size, now)   draw one frame: dt seconds (<= 0.05), size = {w, h, cssW, cssH, dpr} (w, h in
//                          drawing-buffer pixels), now = performance.now() of the frame. Return false
//                          when nothing changed and nothing was drawn (the canvas keeps its picture and
//                          no 'frame' event goes out); anything else counts as a drawn frame.
//   onPointerDown(p, e)    p = {id, x, y, startX, startY, dx, dy, button, shift, type, dragged, started}
//   onDrag(p, e)           one pointer moving while down; p.dx / p.dy = CSS px since the last event;
//                          p.dragged turns true once it has left the click slop (5 px, 9 px for touch)
//   onPinch(scale, p, e)   two pointers: scale = previous distance / new distance (> 1 = fingers closing);
//                          p.dx / p.dy = movement of the pointer that moved
//   onPointerUp(p, e)      also on pointercancel (p.cancelled = true)
//   onClick(p, e)          primary button released without a drag within 600 ms; p = {x, y}
//   onHover(p, e)          mouse moving with no button down; p = {x, y}, or null when it leaves
//   onWheel(e)             the wheel event (already preventDefault-ed)
//   onKey(e)               keydown; return true when handled (the viewer then calls preventDefault).
//                          Held keys are in viewer.keys (a Set of lower-case names).
//   onResize(size)
//   state()                plain object for viewer.state() / window.TOUR.getState()
//   busy()                 true while the mode is waiting for something that no event announces (a timer of
//                          its own, a file on its way): the loop then keeps its full rate although nothing
//                          is drawn (see "loop" below)
//   early                  true: the mode can show its picture before the 3D model has arrived (the inside
//                          view: at rest it needs the panorama alone). Such a mode is entered while the engine
//                          is still 'loading'; the others wait for 'ready'.
//
// Events (viewer.on(type, fn) returns an unsubscribe function):
//   'progress' {loaded: 0..1}             model download
//   'ready'    {}                         the 3D model is in: every mode can run (a mode asked for meanwhile
//                                         enters now)
//   'failed'   {error}                    the engine could not start, or lost its WebGL context (final)
//   'parked'   {mode}                     a mode was asked for that has to wait for the 3D model
//   'mode'     {mode, from, opts}         a mode became active (before its enter() resolves)
//   'sweep'    {id, from, sweep, room}    arrived at a sweep (inside)
//   'transition' {from, to, t, done}      a move between sweeps started (t 0) or ended (t 1, done)
//   'hover'    {x, y, sweep, point}|null  what is under the cursor (inside): a floor ring's sweep, else the
//                                         surface point in feet
//   'place'    {label}                    a short caption for the chip (exterior views)
//   'flight'   {active, from, to, sweep}  a flight between two views started / ended (dollhouse.js)
//   'insets'   {bottom}                   the part of the screen the chrome covers changed (ui.js)
//   'busy'     {active}                   the view asked for is still loading (a far jump, a fly-in): the old
//                                         picture stays up meanwhile
//   'frame'    {dt, size, now}            after every drawn frame (overlays follow the camera with it); a
//                                         view that stands still draws nothing and sends none
//   'error'    {error, where}             an exception caught in the loop (reported once per message)
//
// Coordinates: SCENE feet, x west -> east, y up, z rear (north) -> street (south). Yaw 0 looks toward
// -z; positive is clockwise seen from above. Angles are radians inside the code; tour.json holds degrees.

import * as THREE from 'three';

const DEG = Math.PI / 180;
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const angleDelta = (a, b) => Math.atan2(Math.sin(b - a), Math.cos(b - a));
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const d = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / d, a[1] / d, a[2] / d]; };
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// A wheel event's vertical travel in pixels, whatever unit the device reports (pixels, lines, pages).
// A pinch on a trackpad arrives as wheel events with ctrlKey and small steps (Chromium and Firefox:
// deltaY about -100 ln(scale)); PINCH scales them so that the modes' wheel factors (about 0.0011 per
// pixel) turn a pinch into that scale: fingers twice as far apart, twice as close.
const PINCH = 9;
const wheelPixels = (e) => {
  const px = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaMode === 2 ? e.deltaY * 400 : e.deltaY;
  return clamp(e.ctrlKey && e.deltaMode === 0 && Math.abs(px) < 50 ? px * PINCH : px, -400, 400);
};
// `calm.matches`: the visitor asked the system for less motion; flights and glides then cut or fade.
const calm = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };

// Column-major 4x4 helpers, the layout of the engine's pv() and of the exterior frame matrices.
function mul(a, b) {
  const c = new Float32Array(16);
  for (let j = 0; j < 4; j++) for (let i = 0; i < 4; i++) for (let k = 0; k < 4; k++) c[j * 4 + i] += a[k * 4 + i] * b[j * 4 + k];
  return c;
}
function lookAt(e, t) {
  const z = norm(sub(e, t)), x = norm(cross([0, 1, 0], z)), y = cross(z, x);
  return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, e), -dot(y, e), -dot(z, e), 1]);
}
function perspective(fov, aspect) {
  const f = 1 / Math.tan(fov / 2), near = 0.10, far = 350;
  return new Float32Array([f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 2 * far * near / (near - far), 0]);
}
// Unit view direction of a yaw / pitch pair.
const lookDir = (yaw, pitch) => [Math.cos(pitch) * Math.sin(yaw), Math.sin(pitch), -Math.cos(pitch) * Math.cos(yaw)];

// Image loading shared by the panoramas and the exterior frames: a small LRU of blob promises.
const blobs = new Map();
function fetchBlob(url) {
  let p = blobs.get(url);
  if (p) { blobs.delete(url); blobs.set(url, p); return p; }
  p = fetch(url).then((r) => { if (!r.ok) throw Error('HTTP ' + r.status + ' ' + url); return r.blob(); });
  blobs.set(url, p);
  p.catch(() => { if (blobs.get(url) === p) blobs.delete(url); });
  while (blobs.size > 10) blobs.delete(blobs.keys().next().value);
  return p;
}
async function decodeImage(blob) {
  if (window.createImageBitmap) { try { return await createImageBitmap(blob); } catch (e) { /* fall through */ } }
  const url = URL.createObjectURL(blob), img = new Image();
  img.decoding = 'async';
  img.src = url;
  try { await img.decode(); } finally { setTimeout(() => URL.revokeObjectURL(url), 4000); }
  return img;
}

const util = {
  DEG, clamp, lerp, smooth, angleDelta, sub, dot, cross, norm, distance, mul, lookAt, perspective, lookDir,
  sleep, wheelPixels, calm,
  fetchBlob, decodeImage, blobCached: (url) => blobs.has(url),
};

const LEVELS = ['8k', '4k', '2k'];                    // best first

// opts: canvas, engine (createEngine result, the model may still be loading), tour (assets/data/tour.json),
// manifest (assets/panos/manifest.json or null), manifestUrl, gate() -> false while the page wants the
// keys for itself (a modal or the landing is open), lite (small GPU budget), query (URLSearchParams).
export function createViewer(opts) {
  const { canvas, engine, tour } = opts;
  const manifest = opts.manifest && opts.manifest.nodes ? opts.manifest : null;
  const manifestUrl = new URL(opts.manifestUrl || 'assets/panos/manifest.json', location.href);
  const gate = opts.gate || (() => true);
  const query = opts.query || new URLSearchParams(location.search);
  const gl = engine.gl;
  const caps = { maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE), lite: !!opts.lite };

  // ---- sweep graph ---------------------------------------------------------------------------
  const sweeps = (tour.sweeps || []).map((s) => Object.assign({}, s, {
    look: { yaw: (s.yaw || 0) * DEG, pitch: (s.pitch || 0) * DEG },
    links: s.links || [], visible: s.visible || s.links || [],
  }));
  const sweepMap = new Map(sweeps.map((s) => [s.id, s]));
  const rooms = tour.rooms || [];
  const roomMap = new Map(rooms.map((r) => [r.id, r]));
  const sweep = (id) => sweepMap.get(id) || null;
  const roomOf = (id) => { const s = sweep(id); return (s && roomMap.get(s.room)) || null; };
  // Shortest route over `links` (breadth first): [a, ..., b] or null.
  function path(a, b) {
    if (!sweepMap.has(a) || !sweepMap.has(b)) return null;
    const prev = new Map([[a, null]]), q = [a];
    while (q.length) {
      const x = q.shift();
      if (x === b) { const out = []; for (let p = b; p !== null; p = prev.get(p)) out.unshift(p); return out; }
      for (const y of sweepMap.get(x).links) if (!prev.has(y) && sweepMap.has(y)) { prev.set(y, x); q.push(y); }
    }
    return null;
  }
  // The room a plan point lies in, or null: the SMALLEST one whose bounds contain it. The bounds are
  // rectangles and may lie inside one another (the laundry closet is cut out of Bedroom 4's rectangle;
  // the hall's rectangle reaches over its neighbours), and the smallest is the room meant. The same
  // rule as room_of() in tools/web/build_site_data.py, which gives every sweep its `room`.
  const within = (r, x, z) => x >= r.bounds[0] && x <= r.bounds[2] && z >= r.bounds[1] && z <= r.bounds[3];
  const floorArea = (r) => (r.bounds[2] - r.bounds[0]) * (r.bounds[3] - r.bounds[1]);
  function roomAt(x, z) {
    let best = null;
    for (const r of rooms) if (within(r, x, z) && (!best || floorArea(r) < floorArea(best))) best = r;
    return best;
  }
  // The room each indoor sweep stands in. That is its `room`, except for the sweep in front of a room
  // nobody can stand in (the laundry closet): it belongs to that room and stands in the one before it.
  const standsIn = new Map(sweeps.map((s) => [s.id, s.outdoor ? null : roomAt(s.p[0], s.p[2])]));
  // A room no sweep stands in (a closet behind its doors) is entered on the sweep in front of it, looking
  // at the room: the direction (yaw, radians) from sweep `s` to the room's label point. undefined for a
  // room somebody can stand in, where the visitor keeps the direction the view gives them.
  const stoodIn = new Set(standsIn.values());
  function lookInto(room, s) {
    const r = room && roomMap.get(room.id);            // (a room of tour.json, by id)
    if (!r || !s || stoodIn.has(r)) return undefined;
    const dx = r.at[0] - s.p[0], dz = r.at[1] - s.p[2];
    return Math.hypot(dx, dz) > 0.5 ? Math.atan2(dx, -dz) : undefined;
  }
  // A sweep is one of a room's when it belongs to the room or stands in it.
  const sweepOf = (room, s) => s.room === room.id || standsIn.get(s.id) === room;
  // A measured room (one with a `tag`, its number in the schedule) is bounded by the clear faces of its
  // own walls; the open spaces (living, kitchen, hall, garage: no tag) are rectangles that reach over
  // their neighbours. So a plan point inside a measured room lies beyond a wall, or beyond a doorway,
  // from a sweep that stands in another room and is not one of this room's: true for such a pair. The
  // dollhouse and the floor plan then do not let the dot of that sweep catch a click beside it (the
  // floor of the primary bath just inside its door is a foot from the sweep that stands in the
  // vestibule). A sweep in a doorway stands in no room and is walled off from neither side.
  function walledOff(x, z, s) {
    const room = roomAt(x, z), other = standsIn.get(s.id);
    return !!room && !!room.tag && !!other && other !== room && !sweepOf(room, s);
  }
  // The sweep a plan point leads to: the nearest of the sweeps of the point's room (the ones that belong
  // to it and the ones that stand in it); the room's own sweep when it has none of either; the nearest
  // sweep of all for a point outside every room.
  function nearestSweep(x, z) {
    const room = roomAt(x, z);
    let list = room ? sweeps.filter((s) => sweepOf(room, s)) : [];
    if (!list.length && room && sweepMap.has(room.sweep)) return sweepMap.get(room.sweep);
    if (!list.length) list = sweeps;
    return list.reduce((a, b) => Math.hypot(a.p[0] - x, a.p[2] - z) <= Math.hypot(b.p[0] - x, b.p[2] - z) ? a : b, list[0]) || null;
  }

  // ---- panorama files (assets/panos/manifest.json) -------------------------------------------
  const widths = (manifest && manifest.widths) || { '8k': 8192, '4k': 4096, '2k': 2048 };
  const forced = query.get('pano');                   // ?pano=2k|4k|8k pins the level
  const saveData = !!(navigator.connection && navigator.connection.saveData);
  const panos = {
    has: (id) => !!(manifest && manifest.nodes[id]),
    // level names this sweep has, best first, that the GPU can hold
    levels(id) {
      const e = manifest && manifest.nodes[id];
      if (!e || !e.levels) return [];
      return LEVELS.filter((l) => e.levels[l] && (widths[l] || 0) <= caps.maxTextureSize);
    },
    // the level to rest on: the best one, 4k at most on small devices, 2k when the user saves data
    best(id) {
      const all = panos.levels(id);
      if (!all.length) return null;
      if (forced && all.includes(forced)) return forced;
      if (saveData || (navigator.deviceMemory || 8) <= 2) return all[all.length - 1];
      if (caps.lite && all.length > 1 && all[0] === '8k') return all[1];
      return all[0];
    },
    // the level to show first and during a move: the smallest
    quick(id) { const all = panos.levels(id); return forced && all.includes(forced) ? forced : all[all.length - 1] || null; },
    url(id, level) {
      const e = manifest && manifest.nodes[id];
      const file = e && e.levels && e.levels[level || panos.best(id)];
      if (!file) return null;
      const u = new URL(file, manifestUrl);
      if (manifest.version) u.searchParams.set('v', manifest.version);
      return u.href;
    },
    thumb(id) {
      const e = manifest && manifest.nodes[id];
      const u = new URL(e && e.thumb ? e.thumb : '../thumbs/' + id + '.webp', manifestUrl);
      if (manifest && manifest.version) u.searchParams.set('v', manifest.version);
      return u.href;
    },
    rank: (level) => LEVELS.length - LEVELS.indexOf(level),      // 2k 1, 4k 2, 8k 3
  };

  // ---- events --------------------------------------------------------------------------------
  const listeners = new Map();
  const reported = new Set();
  function on(type, fn) {
    if (!listeners.has(type)) listeners.set(type, new Set());
    listeners.get(type).add(fn);
    return () => off(type, fn);
  }
  function off(type, fn) { const s = listeners.get(type); if (s) s.delete(fn); }     // (on() hands it out)
  function emit(type, detail) {
    const s = listeners.get(type);
    if (!s) return;
    for (const fn of [...s]) { try { fn(detail); } catch (e) { report(e, 'listener:' + type); } }
  }
  // An exception never stops the loop: it is logged (once per message and place) and the next frame runs.
  function report(error, where) {
    const key = where + '|' + (error && error.message ? error.message : String(error));
    if (reported.has(key)) return;
    reported.add(key);
    console.error('[tour] ' + where + ':', error);
    if (where.indexOf('listener:error') !== 0) emit('error', { error, where });
  }

  // ---- engine calls --------------------------------------------------------------------------
  let engineState = 'loading';                        // 'loading' | 'ready' | 'failed'
  let lastView = null;
  const size = { w: 1, h: 1, cssW: 1, cssH: 1, dpr: 1 };

  // 'inside' | 'dollhouse' | 'floorplan' | 'exterior'. Not cached: every call resets the mode's fly-out
  // controls (projection fade, class opacity), as engine.setMode does.
  function setEngineMode(name) { engine.setMode(name); }
  // color: 0xRRGGBB (sRGB), or null for the engine's own sky colour (what it clears with at start).
  let sky = null;
  engine.renderer.getClearColor({ copy(c) { sky = c.clone(); return this; } });
  function setBackground(color) {
    engine.setBackground(color === null || color === undefined ? sky : color);
  }
  // view = {eye, aim, fovY, up?, near?, far?} | {ortho: {halfHeight}, eye, aim, up?}; feet and radians.
  function render(view) {
    lastView = view;
    return engine.render(Object.assign({ width: size.w, height: size.h, pixelRatio: 1 }, view));
  }
  // point: [x, y, z] in feet, or a sweep id (its ring on the floor). -> {x, y} in CSS px, or null when
  // behind the camera or clearly off screen. In the inside view a sweep id means the ring as the
  // visitor sees it: null when that ring is not shown from here or is hidden behind something. The
  // dollhouse and the floor plan answer the same way for their sweep dots (controller.markerPoint).
  function project(point, margin = 1.15) {
    if (typeof point === 'string') {
      const s = sweep(point);
      if (!s) return null;
      if (mode === 'inside' && controllers.inside && controllers.inside.ringPoint) return controllers.inside.ringPoint(point);
      if (mode && controllers[mode] && controllers[mode].markerPoint) return controllers[mode].markerPoint(point);
      point = [s.p[0], (s.floor || 0) + 0.02, s.p[2]];
    }
    if (!lastView || engineState !== 'ready') return null;
    const m = engine.pv(), x = point[0], y = point[1], z = point[2];
    const w = m[3] * x + m[7] * y + m[11] * z + m[15];
    if (w <= 1e-6) return null;
    const nx = (m[0] * x + m[4] * y + m[8] * z + m[12]) / w, ny = (m[1] * x + m[5] * y + m[9] * z + m[13]) / w;
    if (Math.abs(nx) > margin || Math.abs(ny) > margin) return null;
    return { x: (nx + 1) * size.cssW / 2, y: (1 - ny) * size.cssH / 2, w };
  }
  // The view ray through a CSS-pixel point of the last perspective render: {origin, dir}.
  function ray(x, y) {
    const v = lastView;
    if (!v) return null;
    const f = norm(sub(v.aim, v.eye));
    let r = cross(f, v.up || [0, 1, 0]);
    if (Math.hypot(r[0], r[1], r[2]) < 1e-6) r = cross(f, [0, 0, -1]);
    r = norm(r);
    const u = cross(r, f);
    const nx = x / size.cssW * 2 - 1, ny = 1 - y / size.cssH * 2, aspect = size.cssW / size.cssH;
    if (v.ortho) {
      const hh = v.ortho.halfHeight;
      return { origin: v.eye.map((e, i) => e + r[i] * nx * hh * aspect + u[i] * ny * hh), dir: f };
    }
    const t = Math.tan(v.fovY / 2);
    return { origin: v.eye.slice(), dir: norm(f.map((c, i) => c + r[i] * nx * aspect * t + u[i] * ny * t)) };
  }

  // CSS pixels of the canvas -> the engine's NDC (-1..1, y up).
  const ndc = (x, y) => [x / size.cssW * 2 - 1, 1 - y / size.cssH * 2];
  // What lies under a CSS-pixel point of the last render: engine.pick() -> {point, normal, distance,
  // cls, source} or null (inside: the resting sweep's depth cube; dollhouse / floor plan: a ray cast).
  function pick(x, y, o) {
    if (!lastView || engineState !== 'ready') return null;
    const n = ndc(x, y);
    return engine.pick(n[0], n[1], o);
  }

  // ---- overlay parts the modes share (meshes for engine.overlay, in feet) ---------------------
  // A disc whose soft edge is its rim only (engine.ring feathers the inner edge too, which on a disc
  // is the centre point).
  function disc(radius, segments = 40) {
    const g = engine.ring(0, radius, segments), uv = g.attributes.uv;
    for (let i = 0; i < uv.count; i++) uv.setX(i, 0.5 + 0.5 * uv.getX(i));
    return g;
  }
  // The cursor ring: a white ring with a faint disc and a soft dark halo that lies on the surface under
  // the mouse. One look for the inside view and for the dollhouse / floor plan.
  //   object                              the THREE.Group to add to the mode's overlay group
  //   place(point, normal, radius, lift)  lay it on a surface point (feet; unit normal), radius in feet,
  //                                       lifted off the surface by `lift` feet; shows it
  //   hide(), shown
  function cursorRing() {
    const object = new THREE.Group(), up = new THREE.Vector3(0, 1, 0), n = new THREE.Vector3();
    const parts = [
      [engine.ring(0.55, 1.3, 64), { color: 0x000000, opacity: 0.2, soft: [0.5, 0.5] }],      // halo
      [disc(0.8, 64), { color: 0xffffff, opacity: 0.15, soft: [0, 0.2] }],                     // disc
      [engine.ring(0.76, 1, 64), { color: 0xffffff, opacity: 0.92, soft: [0.22, 0.22] }],     // ring
    ];
    parts.forEach(([geometry, look], i) => {
      const mesh = new THREE.Mesh(geometry, engine.overlayMaterial(look));
      mesh.renderOrder = 4 + i;                       // above the floor rings and sweep dots of the modes
      object.add(mesh);
    });
    object.visible = false;
    return {
      object,
      get shown() { return object.visible; },
      place(point, normal, radius, lift = 0.02) {
        object.position.set(point[0] + normal[0] * lift, point[1] + normal[1] * lift, point[2] + normal[2] * lift);
        object.quaternion.setFromUnitVectors(up, n.set(normal[0], normal[1], normal[2]));
        object.scale.setScalar(radius);
        object.visible = true;
      },
      hide() { object.visible = false; },
    };
  }

  // ---- the free part of the screen -----------------------------------------------------------
  // CSS px of the picture that chrome covers beyond the toolbar rows (the open highlight reel). ui.js
  // sets it; the dollhouse and the floor plan frame the house in what is left ('insets' event).
  const insets = { bottom: 0 };
  function setInsets(next) {
    const bottom = Math.max(0, Math.round((next && next.bottom) || 0));
    if (bottom === insets.bottom) return;
    insets.bottom = bottom;
    wake();
    emit('insets', Object.assign({}, insets));
  }

  // ---- the picture left behind ---------------------------------------------------------------
  // Two views that show different things (the exterior and the house, two far-apart sweeps) change
  // with a dissolve: crossfade() lays a copy of the picture on the canvas over it; the copy fades out
  // (0.4 s, tour.css .xfade) once the next frame has been drawn under it, so a view that is still
  // loading never shows through early. The same fade stands in for every flight when the visitor has
  // asked the system for less motion.
  let fadeEl = null, fadeTimer = 0, fadeDue = 0;      // fadeDue: time after which the copy fades anyway
  function crossfade() {
    try {
      if (!drawCount) return false;
      if (!fadeEl) {
        fadeEl = document.createElement('canvas');
        fadeEl.className = 'xfade';
        fadeEl.setAttribute('aria-hidden', 'true');
        canvas.insertAdjacentElement('afterend', fadeEl);
      }
      const w = Math.max(1, Math.round(size.cssW)), h = Math.max(1, Math.round(size.cssH));
      fadeEl.width = w;
      fadeEl.height = h;
      fadeEl.getContext('2d').drawImage(canvas, 0, 0, w, h);
      fadeEl.classList.remove('out');
      fadeEl.hidden = false;
      void fadeEl.offsetWidth;                          // the opaque state first
      clearTimeout(fadeTimer);
      fadeDue = performance.now() + 4000;
      wake();
      return true;
    } catch (e) { return false; }                       // a picture that cannot be copied simply cuts
  }
  function fadeOut() {
    fadeDue = 0;
    const el = fadeEl;
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add('out')));
    clearTimeout(fadeTimer);
    fadeTimer = setTimeout(() => { el.hidden = true; }, 800);
  }

  // ---- modes ---------------------------------------------------------------------------------
  const controllers = {};
  let mode = null;
  let pending = null;                                 // setMode() asked for a mode that waits for the model
  let frameCount = 0, drawCount = 0;                  // animation ticks; frames actually drawn

  function register(name, controller) { controllers[name] = controller; return controller; }
  // A mode can run when the model is in; one that needs only its panorama (`early`) as soon as the
  // engine exists.
  const usable = (name) => !!controllers[name] && (engineState === 'ready' || (engineState === 'loading' && !!controllers[name].early));

  // Resolves true once the mode is on, false when the request was dropped (another one replaced it,
  // or the engine has failed). The latest request wins, parked or not.
  function setMode(name, o = {}) {
    if (!controllers[name]) return Promise.reject(new Error('Unknown mode "' + name + '"'));
    if (engineState === 'failed') return Promise.resolve(false);
    wake();
    if (pending) { pending.resolve(false); pending = null; }
    if (!usable(name)) {
      emit('parked', { mode: name });
      return new Promise((resolve) => { pending = { name, o, resolve }; });
    }
    const from = mode;
    // A mode may make its own way out (the dollhouse flies into the sweep): depart() then returns a
    // Promise and calls setMode(name, {..., direct: true}) itself when it has arrived. Until then the
    // mode stays what it is. The Promise resolves true once the new mode is on, false when dropped.
    if (from && from !== name && !o.direct && typeof controllers[from].depart === 'function') {
      let own = null;
      try { own = controllers[from].depart(name, o); } catch (e) { report(e, 'depart:' + from); }
      if (own) return Promise.resolve(own).then((ok) => ok !== false, (e) => { report(e, 'depart:' + from); return false; });
    }
    if (from && from !== name) { try { if (controllers[from].leave) controllers[from].leave(name); } catch (e) { report(e, 'leave:' + from); } }
    if (from !== name) lastView = null;                // the camera of the view left behind says nothing about the new one
    mode = name;
    for (const p of pointers.values()) p.dragged = true;      // a gesture never carries over into the next mode
    emit('mode', { mode: name, from, opts: o });
    let entered;
    try { entered = controllers[name].enter ? controllers[name].enter(from, o) : null; } catch (e) { report(e, 'enter:' + name); }
    return Promise.resolve(entered).then(() => true, (e) => { report(e, 'enter:' + name); return false; });
  }

  // Called by main.js when the model has loaded (or failed). 'failed' is final: a model that arrives
  // after the WebGL context was lost does not bring the view back.
  function setEngineState(s, error) {
    if (s === engineState || engineState === 'failed') return;
    engineState = s;
    wake();
    if (s === 'ready') {
      emit('ready', {});
      if (pending) { const p = pending; pending = null; setMode(p.name, p.o).then(p.resolve, () => p.resolve(false)); }
    } else if (s === 'failed') {
      if (pending) { pending.resolve(false); pending = null; }
      emit('failed', { error });
    }
  }

  // ---- loop ----------------------------------------------------------------------------------
  // One tick per animation frame while anything moves. A view that stands still draws nothing (the
  // modes' frame() returns false), and after PARK ticks of that the loop goes to sleep: it then looks
  // in only every NAP ms (a safety net: a resize, a timer of a mode that did not say busy()). wake()
  // brings the full rate back at once; it is called for every input, for every request to the viewer
  // and whenever the engine has something new to draw (engine.onDirty: a panorama arrived, a level
  // swapped, the model came in).
  const PARK = 45, NAP = 250;
  let last = 0, raf = 0, nap = 0, still = 0, running = false;
  function plan() {
    if (!running || raf || nap) return;
    if (still < PARK) raf = requestAnimationFrame(tick);
    else nap = setTimeout(() => tick(performance.now()), NAP);
  }
  function wake() {
    still = 0;
    if (nap) { clearTimeout(nap); nap = 0; }
    plan();
  }
  function measure() {
    const cssW = canvas.clientWidth || innerWidth, cssH = canvas.clientHeight || innerHeight;
    const dpr = Math.min(devicePixelRatio || 1, 1.75);
    const w = Math.max(1, Math.round(cssW * dpr)), h = Math.max(1, Math.round(cssH * dpr));
    if (w === size.w && h === size.h && cssW === size.cssW && cssH === size.cssH) return false;
    Object.assign(size, { w, h, cssW, cssH, dpr });
    return true;
  }
  function tick(now) {
    raf = nap = 0;
    still++;                                          // (set back by whatever is going on)
    try { step(now); } finally { plan(); }            // whatever happens in a frame, the next one is planned
  }
  function step(now) {
    const dt = clamp((now - last) / 1000, 0, 0.05) || 0.016;
    last = now;
    frameCount++;
    const c = controllers[mode];
    let resized = false;
    try {
      resized = measure();
      if (resized && c && c.onResize) c.onResize(size);
    } catch (e) { report(e, 'resize:' + mode); }
    if (resized || pointers.size || keys.size || fadeDue) still = 0;
    if (!c || !usable(mode)) return;
    let drawn, busy = false;
    try { drawn = c.frame(dt, size, now); } catch (e) { report(e, 'frame:' + mode); }
    try { busy = !!c.busy && c.busy() === true; } catch (e) { report(e, 'busy:' + mode); }
    if (drawn !== false || busy || engine.dirty()) still = 0;
    if (fadeDue && (drawn !== false || now > fadeDue)) fadeOut();     // the new picture is under the copy
    if (drawn === false) return;                      // render on demand: the picture on the canvas still holds
    drawCount++;
    emit('frame', { dt, size, now });
  }
  function start() { if (!running) { running = true; measure(); wake(); } }
  function stop() { running = false; cancelAnimationFrame(raf); clearTimeout(nap); raf = nap = 0; }
  engine.onDirty = wake;
  window.addEventListener('resize', wake);

  // ---- input ---------------------------------------------------------------------------------
  const pointers = new Map();
  const keys = new Set();
  const active = () => (mode && usable(mode) ? controllers[mode] : null);
  const call = (name, ...args) => {
    wake();                                           // every input (and clickAt): the loop is up for what it sets off
    const c = active();
    if (!c || typeof c[name] !== 'function') return undefined;
    try { return c[name](...args); } catch (e) { report(e, name + ':' + mode); return undefined; }
  };

  canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  canvas.addEventListener('pointerdown', (e) => {
    wake();
    const p = {
      id: e.pointerId, x: e.clientX, y: e.clientY, startX: e.clientX, startY: e.clientY, dx: 0, dy: 0,
      button: e.button, shift: e.shiftKey, type: e.pointerType, dragged: false, started: performance.now(),
    };
    pointers.set(e.pointerId, p);
    try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* synthetic events have no capture */ }
    canvas.focus({ preventScroll: true });
    if (pointers.size > 1) pointers.forEach((q) => { q.dragged = true; });
    call('onPointerDown', p, e);
  });
  canvas.addEventListener('pointermove', (e) => {
    const p = pointers.get(e.pointerId);
    if (!p) { if (e.pointerType !== 'touch') call('onHover', { x: e.clientX, y: e.clientY }, e); return; }
    const slop = p.type === 'touch' ? 9 : 5;
    if (Math.hypot(e.clientX - p.startX, e.clientY - p.startY) > slop) p.dragged = true;
    p.dx = e.clientX - p.x;
    p.dy = e.clientY - p.y;
    p.shift = e.shiftKey;
    if (pointers.size === 2) {
      const other = [...pointers.values()].find((q) => q !== p);
      const before = Math.hypot(p.x - other.x, p.y - other.y), after = Math.hypot(e.clientX - other.x, e.clientY - other.y);
      p.x = e.clientX; p.y = e.clientY;
      call('onPinch', before / Math.max(1, after), p, e);
    } else {
      p.x = e.clientX; p.y = e.clientY;
      call('onDrag', p, e);
    }
  });
  const release = (e, cancelled) => {
    const p = pointers.get(e.pointerId);
    if (!p) return;
    pointers.delete(e.pointerId);
    p.cancelled = !!cancelled;
    call('onPointerUp', p, e);
    if (!cancelled && !p.dragged && p.button === 0 && performance.now() - p.started < 600) call('onClick', { x: e.clientX, y: e.clientY }, e);
  };
  canvas.addEventListener('pointerup', (e) => release(e, false));
  canvas.addEventListener('pointercancel', (e) => release(e, true));
  canvas.addEventListener('pointerleave', (e) => { if (!pointers.has(e.pointerId)) call('onHover', null, e); });
  canvas.addEventListener('wheel', (e) => { e.preventDefault(); call('onWheel', e); }, { passive: false });
  canvas.addEventListener('webglcontextlost', (e) => {
    e.preventDefault();
    stop();
    setEngineState('failed', Object.assign(new Error('WebGL context lost'), { contextLost: true }));
  });
  const typing = (t) => t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName));
  window.addEventListener('keydown', (e) => {
    // (an event named keydown / keyup may carry no key: Chrome sends one when an autofill entry is picked)
    if (!e.key || !gate() || typing(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
    wake();
    const k = e.key.toLowerCase();
    if (k === 'enter' || k === ' ' || k === 'tab' || k === 'escape') return;       // buttons and the page keep these
    keys.add(k);
    if (call('onKey', e) === true) e.preventDefault();
  });
  window.addEventListener('keyup', (e) => { if (e.key) keys.delete(e.key.toLowerCase()); });
  window.addEventListener('blur', () => { keys.clear(); pointers.clear(); });

  // ---- public --------------------------------------------------------------------------------
  const viewer = {
    canvas, engine, tour, util, caps, panos, size, pointers, keys, query,
    sweeps, sweep, roomOf, roomAt, lookInto, path, nearestSweep, walledOff,
    on, emit, report,
    register, controllers, setMode, setEngineState, start,
    setEngineMode, setBackground, render, project, ray, ndc, pick,
    disc, cursorRing, insets, setInsets, crossfade, wake,
    get mode() { return mode; },
    get engineState() { return engineState; },
    get modelReady() { return engineState === 'ready'; },
    get drawCount() { return drawCount; },
    // the camera of the last frame the active mode has drawn (null until it has drawn one)
    get view() { return lastView; },
    // Animated move to a sweep; from another mode it enters the inside view there. Resolves on arrival.
    goTo(id, o = {}) {
      if (!sweepMap.has(id)) return Promise.resolve(false);
      if (mode !== 'inside' || !usable('inside')) return setMode('inside', Object.assign({ sweep: id }, o));
      if (pending) { pending.resolve(false); pending = null; }       // the latest request wins
      wake();
      return controllers.inside.goTo(id, o);
    },
    // The same without animation.
    jumpTo(id, o = {}) {
      if (!sweepMap.has(id)) return Promise.resolve(false);
      if (mode !== 'inside' || !usable('inside')) return setMode('inside', Object.assign({ sweep: id, instant: true }, o));
      if (pending) { pending.resolve(false); pending = null; }
      wake();
      return controllers.inside.jumpTo(id, o);
    },
    setLook(yaw, pitch) { wake(); if (controllers.inside && controllers.inside.setLook) controllers.inside.setLook(yaw, pitch); },
    // A click at a CSS-pixel point of the canvas, as the active mode would get it (tests).
    clickAt(x, y) { return call('onClick', { x, y, synthetic: true }, null); },
    // {engine, mode, sweep, transition, yaw, pitch, fov, pano} (the inside view's values, kept in every
    // mode) plus the active mode's own state under its name.
    state() {
      const s = { engine: engineState, mode, frame: frameCount, draws: drawCount, size: Object.assign({}, size), sweeps: sweeps.length };
      const inside = controllers.inside && controllers.inside.state ? controllers.inside.state() : {};
      Object.assign(s, { sweep: null, transition: null, yaw: 0, pitch: 0, fov: 0, pano: { id: null, level: null } }, inside);
      if (mode && mode !== 'inside' && controllers[mode] && controllers[mode].state) {
        try { s[mode] = controllers[mode].state(); } catch (e) { report(e, 'state:' + mode); }
      }
      return s;
    },
  };
  return viewer;
}
