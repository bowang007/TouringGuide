// DOLLHOUSE and FLOOR PLAN: the baked model seen from outside, and the flights between these two views
// and the inside view.
//
// Dollhouse: the house alone on a dark background, ceilings and roof gone, the walls on the viewer's
// side culled by the engine. Drag orbits (yaw free, elevation 15..85 degrees, inertia), the wheel or a
// pinch dollies (toward the point under the cursor), right-drag / Shift-drag / two fingers slide the
// model over its footprint; arrow keys turn and tilt, + / - zoom, 0 frames the house again. Floor plan:
// the same model straight down in orthographic projection, north up, the street at the bottom; drag
// slides, wheel / pinch zooms. In both, small dots mark the sweeps, the cursor shows the surface point
// and the sweep a click would enter, and a click flies in.
//
// Framing: on entering (and on a resize) the whole house is put in the middle of the part of the screen
// the chrome leaves free. The dollhouse frames the cylinder around the house, so the model keeps its
// size while it is turned and follows the elevation smoothly; it stays framed until the visitor zooms
// or slides it. Coming out of the inside view it is seen from the 3/4 direction nearest to where the
// visitor was looking; by default from the north-east, which puts the living room, the dining table
// and the kitchen in front (from the street side the garage would fill the foreground).
//
// One camera serves both views: a point looked at (the focus), a heading, an elevation, the half
// height of the picture at the focus, and a flattening factor z. z = 1 is the dollhouse lens (38
// degrees); a larger z pulls the eye back z times and narrows the lens z times (a dolly zoom, the picture
// at the focus keeps its size); at z = Z_FLAT (a 0.8 degree lens) the view is drawn with the
// orthographic camera instead, which differs by less than a pixel. So dollhouse <-> floor plan is one
// move without a jump.
//
// Flights:
//   inside -> dollhouse / floor plan   one move of 1.2 s. The engine goes to the dollhouse visibility
//       with the sweep's panorama still projected and the ceilings still up (the same picture as the
//       inside view), the ceilings fade first, the eye rises through where they were and swings out to
//       the orbit pose, always looking at a point that glides from in front of the visitor to the
//       middle of the house, while the projection fades into the baked textures. The eye goes slowly
//       near the sweep and fast far out, which spreads the change on screen evenly over the flight.
//   dollhouse / floor plan -> inside   the same path backwards, started once the sweep's panorama and
//       depth cube are loaded (inside.preload; on a slow line the camera stays where it is meanwhile and
//       the viewer's 'busy' mark shows). It ends exactly on the sweep with the panorama projected, then
//       the inside view takes over with the same camera: the pure panorama. A panorama that cannot be
//       had at all is entered with a cut (the dissolve of a change of view), never flown into bare.
//   dollhouse <-> floor plan            0.9 s along the orbit (heading, elevation, lens).
//   exterior <-> these views            a dissolve of the two pictures (0.4 s, viewer.crossfade).
// A new request during a flight starts from wherever the camera is. With prefers-reduced-motion nothing
// flies: every change of view is that dissolve.
//
// The viewer asks a mode before leaving it (controller.depart, see viewer.js): that is how a request
// for the inside view (toolbar, a room name on the plan, the reel, viewer.goTo) becomes a fly-in here.
//
// Public: createDollhouse(viewer, {tone}) -> {dollhouse, floorplan}, two controllers for
// viewer.register(); tone = [r, g, b] house-wide gain of the baked textures in these views.
//   markerPoint(id)   where a sweep's dot is on screen (viewer.project(id) in these views): {x, y} CSS
//                     px, null when it is off screen or hidden behind a wall or furniture
//   state()           dollhouse {target, pivot, yaw, theta, phi, half, radius, auto, hover, flight}
//                     floorplan {x, z, halfHeight, fov: 0, auto, hover, flight}
//                     flight = null | {to: 'dollhouse' | 'floorplan' | 'inside', sweep, t: 0..1}
//                     hover = id of the sweep a click at the cursor would enter; auto = still as framed
// Events: 'flight' {active, from, to, sweep} at the start and the end of every flight.

import * as THREE from 'three';

export function createDollhouse(viewer, deps = {}) {
  const { engine, util, tour, canvas } = viewer;
  const { DEG, clamp, lerp, smooth, angleDelta, lookDir, sleep, calm } = util;
  const finite = Number.isFinite;
  const ease = (t) => t * t * t * (t * (6 * t - 15) + 10);          // ease in-out with a soft start and end
  // The way between a sweep and the orbit (0 = on the sweep, 1 = out) against time: the picture changes
  // most near the sweep, where a foot of travel is a lot, so the camera goes slowly there and fast far
  // out; then the change on screen is spread evenly over the flight, eased at both ends.
  const reach = (x) => Math.pow(smooth(x), 1.6);

  // ---- numbers -------------------------------------------------------------------------------
  const DARK = 0x16181b;                               // the page background (--bg)
  const FOV = 38 * DEG, K = Math.tan(FOV / 2);         // the dollhouse lens
  const Z_FLAT = K / Math.tan(0.4 * DEG);              // flattening at which the view counts as orthographic
  const PHI_MIN = 15 * DEG, PHI_MAX = 85 * DEG, PHI = 40 * DEG;     // elevation limits and default
  const YAW = -135 * DEG;                              // default heading: seen from the north-east (the living spaces in front)
  const FOCUS_Y = 3.5;                                 // ft, height of the point the orbit turns about
  const WALL = 8;                                      // ft, wall height (framing)
  const EYE_MIN = 10;                                  // ft, the orbiting eye stays above the cut walls
  const HALF_MIN = 5, ZOOM_OUT = 1.6;                  // closest picture half-height (ft); farthest = fit x this
  const FLY = 1.2, SWITCH = 0.9, REFRAME = 0.5;        // s: inside <-> outside, dollhouse <-> plan, back to the framed view
  const MAKE_ROOM = 0.3;                               // s: the framed house steps aside for the reel
  const PRELOAD_MS = 12000;                            // longest a fly-in waits for its panorama
  const AHEAD = 8;                                     // ft in front of the inside camera: where its focus starts
  const ORBIT = 0.0055;                                // rad per CSS px of drag
  const DOT_FT = 0.3, DOT_PX = 4.5;                    // sweep dot radius: feet, and at least this many px
  const RING_FT = 0.75, RING_PX = 10;                  // the ring around the sweep a click would enter
  const RETICLE_PX = 13;                               // cursor ring radius
  const PICK = ['base', 'wall', 'furniture', 'decor_high'];         // what the cursor lands on
  const TONE = deps.tone || [1, 1, 1];                 // house-wide gain of the bake in these views (engine.setAdaptation)

  // ---- the house -----------------------------------------------------------------------------
  const ext = tour.extent || [40, 56];
  const rects = (tour.footprint && tour.footprint.length ? tour.footprint : [[0, 0, ext[0], ext[1]]])
    .map((r) => [Math.min(r[0], r[2]), Math.min(r[1], r[3]), Math.max(r[0], r[2]), Math.max(r[1], r[3])]);
  const box = [Math.min(...rects.map((r) => r[0])), Math.min(...rects.map((r) => r[1])), Math.max(...rects.map((r) => r[2])), Math.max(...rects.map((r) => r[3]))];
  const centre = [(box[0] + box[2]) / 2, FOCUS_Y, (box[1] + box[3]) / 2];
  const corners = [];                                  // what the framed plan has to hold: the house
  for (const r of rects) for (const y of [0, WALL]) corners.push([r[0], y, r[1]], [r[2], y, r[1]], [r[0], y, r[3]], [r[2], y, r[3]]);
  // ... and the framed dollhouse: the upright cylinder around the house, so the framing does not depend
  // on the heading (the model keeps its size while it is turned) and follows the elevation smoothly
  const round = [];
  const radius = Math.max(...corners.map((c) => Math.hypot(c[0] - centre[0], c[2] - centre[2])));
  for (let i = 0; i < 32; i++) for (const y of [0, WALL]) round.push([centre[0] + radius * Math.cos(i * Math.PI / 16), y, centre[2] + radius * Math.sin(i * Math.PI / 16)]);
  const hull = [];                                     // what the near and far planes have to hold (vaults included)
  for (const y of [-0.5, 17]) hull.push([box[0] - 1, y, box[1] - 1], [box[2] + 1, y, box[1] - 1], [box[0] - 1, y, box[3] + 1], [box[2] + 1, y, box[3] + 1]);

  // ---- camera --------------------------------------------------------------------------------
  // A rig is the orbit camera: {pivot (the point of the house it turns about), off ([right, forward] ft:
  // the point looked at lies this far beside the pivot, in the camera's own directions, so the house can
  // sit in the middle of the free part of the screen and still turn about its own middle), yaw (heading
  // of the view, 0 = north), phi (elevation), half (half height of the picture at the point looked at,
  // ft), z (flattening), fit (the framed half), auto (still as framed: no zoom or slide by the visitor)}.
  // A node is any camera: {P (eye before flattening), F (focus), psi (heading used when the view is too
  // steep to have one), ku (tan of half the lens before flattening), z}.
  function basis(yaw, phi) {
    const sy = Math.sin(yaw), cy = Math.cos(yaw), sp = Math.sin(phi), cp = Math.cos(phi);
    return { f: [cp * sy, -sp, -cp * cy], r: [cy, 0, sy], u: [sp * sy, cp, -sp * cy], h: [sy, 0, -cy] };
  }
  function targetOf(g, b = basis(g.yaw, g.phi)) {
    return [g.pivot[0] + b.r[0] * g.off[0] + b.h[0] * g.off[1], g.pivot[1], g.pivot[2] + b.r[2] * g.off[0] + b.h[2] * g.off[1]];
  }
  function rigNode(g) {
    const b = basis(g.yaw, g.phi), f = b.f, d = g.half / K, t = targetOf(g, b);
    return { P: [t[0] - f[0] * d, t[1] - f[1] * d, t[2] - f[2] * d], F: t, psi: g.yaw, ku: K, z: g.z };
  }
  function insideNode(eye, yaw, pitch, fovY) {
    const f = lookDir(yaw, pitch);
    return { P: eye.slice(), F: [eye[0] + f[0] * AHEAD, eye[1] + f[1] * AHEAD, eye[2] + f[2] * AHEAD], psi: yaw, ku: Math.tan(fovY / 2), z: 1 };
  }
  function mixRig(a, b, e) {
    return {
      pivot: [lerp(a.pivot[0], b.pivot[0], e), lerp(a.pivot[1], b.pivot[1], e), lerp(a.pivot[2], b.pivot[2], e)],
      off: [lerp(a.off[0], b.off[0], e), lerp(a.off[1], b.off[1], e)],
      yaw: a.yaw + angleDelta(a.yaw, b.yaw) * e,
      phi: lerp(a.phi, b.phi, e),
      half: Math.exp(lerp(Math.log(a.half), Math.log(b.half), e)),
      z: 1 / lerp(1 / a.z, 1 / b.z, e),                // the perspective itself changes evenly
    };
  }
  // The engine view of a node: eye, aim, an up vector without roll, lens or orthographic size, and near /
  // far planes that hold the house (and the panorama backdrop while that still shows).
  function viewOf(q, backdrop) {
    const vx = q.F[0] - q.P[0], vy = q.F[1] - q.P[1], vz = q.F[2] - q.P[2], d0 = Math.hypot(vx, vy, vz) || 1e-6;
    const dir = [vx / d0, vy / d0, vz / d0], dist = d0 * q.z, k = q.ku / q.z;
    const eye = [q.F[0] - dir[0] * dist, q.F[1] - dir[1] * dist, q.F[2] - dir[2] * dist];
    // heading: the view's own, or psi where the view is (nearly) vertical
    const hl = Math.hypot(dir[0], dir[2]);
    let hx = Math.sin(q.psi), hz = -Math.cos(q.psi);
    if (hl > 1e-5) {
      const w = smooth((hl - 0.02) / 0.23), mx = lerp(hx, dir[0] / hl, w), mz = lerp(hz, dir[2] / hl, w), n = Math.hypot(mx, mz);
      if (n > 1e-3) { hx = mx / n; hz = mz / n; } else { hx = dir[0] / hl; hz = dir[2] / hl; }
    }
    const up = [-dir[1] * hx, hl, -dir[1] * hz];
    let n0 = 1e9, n1 = -1e9;
    for (const c of hull) {
      const t = (c[0] - eye[0]) * dir[0] + (c[1] - eye[1]) * dir[1] + (c[2] - eye[2]) * dir[2];
      if (t < n0) n0 = t;
      if (t > n1) n1 = t;
    }
    const near = Math.max(0.08, n0 - 0.5), far = Math.max(n1 + 2, near + 20, backdrop ? 420 : 0);
    const flat = q.z >= Z_FLAT * 0.999;
    const view = flat ? { ortho: { halfHeight: d0 * q.ku }, eye, aim: q.F.slice(), up, near, far }
      : { eye, aim: q.F.slice(), up, fovY: 2 * Math.atan(k), near, far };
    return { view, eye, dir, k, flat, half: d0 * q.ku };
  }

  // Framing: the smallest picture that holds the whole house inside the part of the screen the chrome
  // leaves free, centred there.
  function safeArea(size) {
    const W = size.cssW, H = size.cssH, side = Math.max(14, W * 0.045), top = Math.min(64, H * 0.1), fill = 0.9;
    // the toolbar row, and whatever stands on it (the open highlight reel), but never more than 45 % of the height
    const bottom = Math.min(Math.min(78, H * 0.12) + viewer.insets.bottom, H * 0.45);
    return { cx: 0, cy: (bottom - top) / H, w: (2 - 4 * side / W) * fill, h: (2 - 2 * (top + bottom) / H) * fill };
  }
  function extent(g, aspect) {                          // the house in NDC for a rig, or null when it does not fit at all
    const b = basis(g.yaw, g.phi), kz = K / g.z, t = targetOf(g, b);
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (const c of g.z > 1 ? corners : round) {
      const dx = c[0] - t[0], dy = c[1] - t[1], dz = c[2] - t[2];
      const w = g.half + (dx * b.f[0] + dy * b.f[1] + dz * b.f[2]) * kz;      // half height of the picture at that depth
      if (w <= g.half * 0.05) return null;
      const x = (dx * b.r[0] + dz * b.r[2]) / (w * aspect), y = (dx * b.u[0] + dy * b.u[1] + dz * b.u[2]) / w;
      if (x < x0) x0 = x;
      if (x > x1) x1 = x;
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
    }
    return { x0, x1, y0, y1 };
  }
  // Moves the point looked at so the house sits in the middle of the free part of the screen.
  function centreRig(g, size, rounds = 2) {
    const aspect = size.cssW / Math.max(1, size.cssH), s = safeArea(size);
    for (let i = 0; i < rounds; i++) {
      const e = extent(g, aspect);
      if (!e) return;
      g.off[0] += ((e.x0 + e.x1) / 2 - s.cx) * g.half * aspect;
      g.off[1] += ((e.y0 + e.y1) / 2 - s.cy) * g.half / Math.max(0.3, Math.sin(g.phi));
    }
  }
  function frameRig(g, size) {
    const aspect = size.cssW / Math.max(1, size.cssH), s = safeArea(size);
    g.pivot = centre.slice();
    g.off = [0, 0];
    for (let i = 0; i < 5; i++) {
      let lo = 1, hi = 600;
      for (let j = 0; j < 32; j++) {
        g.half = (lo + hi) / 2;
        const e = extent(g, aspect);
        if (!e || e.x1 - e.x0 > s.w || e.y1 - e.y0 > s.h) lo = g.half; else hi = g.half;
      }
      g.half = hi;
      centreRig(g, size, 1);
    }
    g.fit = g.half;
    g.auto = true;
    g.framed = g.phi;
    return g;
  }
  // The heading for a fly-out: the 3/4 view nearest to where the visitor looks (so the house hardly
  // turns on the way out); of two that are equally near, the default one or the one opposite it (the
  // other two have the garage or a side wall in front).
  function diagonal(yaw) {
    let best = YAW, bd = 1e9;
    for (const c of [YAW, YAW + Math.PI, YAW - Math.PI / 2, YAW + Math.PI / 2]) {
      const d = Math.abs(angleDelta(yaw, c));
      if (d < bd - 1e-3) { bd = d; best = c; }
    }
    return best;
  }

  // ---- state ---------------------------------------------------------------------------------
  const rigs = {
    dollhouse: { pivot: centre.slice(), off: [0, 0], yaw: YAW, phi: PHI, half: 34, z: 1, fit: 34, auto: true },
    floorplan: { pivot: centre.slice(), off: [0, 0], yaw: 0, phi: Math.PI / 2, half: 32, z: Z_FLAT, fit: 32, auto: true },
  };
  let mode = null;                                     // 'dollhouse' | 'floorplan' while one of the two is the active mode
  let rig = null;                                      // rigs[mode] while the visitor has the camera
  let flight = null;                                   // a move under way (see "flights")
  let request = null;                                  // a fly-in asked for: {id, o, promise, resolve}
  let node = rigNode(rigs.dollhouse);                  // the camera now
  let fades = { pf: 0, co: 0 }, engFades = { pf: -1, co: -1 };     // projection / ceilings: wanted, and what the engine has
  let tone = null;                                     // what setAdaptation was last given
  let velYaw = 0, velPhi = 0, velPan = [0, 0], lastDrag = 0;
  let zoomGoal = 0, zoomAt = null;                     // wheel zoom still to do, and the ground point it holds in place
  let pointer = null, hoverDue = false, hot = null;
  let dotAlpha = 0, clock = 0;
  const drawn = [];
  let last = null;                                     // viewOf() of the last frame
  let shown = false;                                   // a frame of these views has been drawn since entering

  const insideCtl = () => viewer.controllers.inside;
  const copyRig = (g) => ({ pivot: g.pivot.slice(), off: g.off.slice(), yaw: g.yaw, phi: g.phi, half: g.half, z: g.z });
  function setFades(pf, co) { fades = { pf: clamp(pf, 0, 1), co: clamp(co, 0, 1) }; }
  function pushFades() {
    if (fades.pf !== engFades.pf) { engine.setProjectionFade(fades.pf); engFades.pf = fades.pf; }
    if (fades.co !== engFades.co) { engine.setClassOpacity('ceiling', fades.co); engFades.co = fades.co; }
  }
  function engineMode(name) {                          // resets the engine's fades to the mode's own (0, 0)
    viewer.setEngineMode(name);
    engFades = { pf: 0, co: 0 };
  }
  // The bake's exposure in these views: one house-wide value, applied at once (no easing: the baked
  // textures only come into view as the projection fades).
  function setTone() {
    if (tone === TONE) return;
    tone = TONE;
    engine.setAdaptation(TONE, null, true);
  }

  // ---- limits --------------------------------------------------------------------------------
  function halfMin(g) {
    if (g.z > 1) return HALF_MIN + 1;
    return Math.max(HALF_MIN, (EYE_MIN - g.pivot[1]) / Math.sin(g.phi) * K);
  }
  const clampHalf = (g, h) => clamp(h, halfMin(g), Math.max(halfMin(g), g.fit * ZOOM_OUT));
  function clampTarget(g) {
    g.pivot[0] = clamp(g.pivot[0], box[0] - 2, box[2] + 2);
    g.pivot[2] = clamp(g.pivot[2], box[1] - 2, box[3] + 2);
  }
  // The point of the focus plane (the horizontal plane through the target) under a CSS-pixel point.
  function groundAt(x, y) {
    const r = rig && viewer.view ? viewer.ray(x, y) : null;
    if (!r || r.dir[1] > -0.03) return null;
    const t = (rig.pivot[1] - r.origin[1]) / r.dir[1];
    return [r.origin[0] + r.dir[0] * t, rig.pivot[1], r.origin[2] + r.dir[2] * t];
  }
  function slide(from, to) {                           // the model follows the pointer
    const a = groundAt(from[0], from[1]), b = groundAt(to[0], to[1]);
    if (!a || !b) return;
    const lim = rig.half * 3, dx = clamp(a[0] - b[0], -lim, lim), dz = clamp(a[2] - b[2], -lim, lim);
    rig.pivot[0] += dx;
    rig.pivot[2] += dz;
    clampTarget(rig);
  }
  function zoomTo(h, at) {                             // new picture size; `at` (a ground point) stays where it is on screen
    h = clampHalf(rig, h);
    if (at) {
      const s = h / rig.half, t = targetOf(rig);
      rig.pivot[0] += (at[0] - t[0]) * (1 - s);
      rig.pivot[2] += (at[2] - t[2]) * (1 - s);
      clampTarget(rig);
    }
    rig.half = h;
  }

  // ---- overlay: sweep dots, the ring of the sweep under the cursor, the cursor ring ------------
  const group = new THREE.Group();
  group.name = 'outside';
  group.visible = false;
  engine.overlay.add(group);
  const dotGeo = viewer.disc(1), haloGeo = viewer.disc(1.9);
  const dots = new Map();                              // id -> {s, dot, halo, heat, size}
  for (const s of viewer.sweeps) {
    if (s.outdoor) continue;
    const y = (s.floor || 0) + 0.07;
    const halo = new THREE.Mesh(haloGeo, engine.overlayMaterial({ color: 0x000000, opacity: 0, soft: [0, 0.9] }));
    const dot = new THREE.Mesh(dotGeo, engine.overlayMaterial({ color: 0xffffff, opacity: 0, soft: [0, 0.3] }));
    halo.position.set(s.p[0], y - 0.01, s.p[2]);
    dot.position.set(s.p[0], y, s.p[2]);
    halo.renderOrder = 1;
    dot.renderOrder = 2;
    halo.visible = dot.visible = false;
    group.add(halo, dot);
    dots.set(s.id, { s, dot, halo, heat: 0, size: 0, c: [s.p[0], y, s.p[2]] });
  }
  const hotRing = new THREE.Mesh(engine.ring(0.8, 1, 64), engine.overlayMaterial({ color: 0xffffff, opacity: 0, soft: [0.3, 0.3] }));
  hotRing.renderOrder = 3;
  hotRing.visible = false;
  group.add(hotRing);
  const reticle = viewer.cursorRing();
  group.add(reticle.object);
  let hotAlpha = 0, hotId = null;

  // feet per CSS pixel at a point, for the camera of the last frame
  function feetPerPx(p) {
    if (!last) return 0.1;
    if (last.flat) return 2 * last.half / viewer.size.cssH;
    const d = (p[0] - last.eye[0]) * last.dir[0] + (p[1] - last.eye[1]) * last.dir[1] + (p[2] - last.eye[2]) * last.dir[2];
    return 2 * Math.max(0.5, d) * last.k / viewer.size.cssH;
  }
  // radius of a sweep's dot as drawn (feet): DOT_FT, and never smaller than DOT_PX on screen
  const dotRadius = (d) => Math.max(DOT_FT, DOT_PX * feetPerPx(d.c));
  // The plan point [x, z] a surface point stands for: a wall counts for the room on the side it is seen from.
  function planPoint(hit) {
    const n = hit.normal, flatOn = Math.abs(n[1]) > 0.7;
    return [hit.point[0] + (flatOn ? 0 : n[0] * 0.6), hit.point[2] + (flatOn ? 0 : n[2] * 0.6)];
  }
  // The sweep a click on a surface point enters: the one standing right there, else the nearest one of
  // the room the point lies in (viewer.nearestSweep: the smallest room that contains the point).
  // "Right there" is within 1.5 ft of the sweep's dot. Not through the walls of a measured room: a point
  // of such a room beside the dot of a sweep that stands in another room, beyond a wall or a doorway
  // (viewer.walledOff), belongs to its own room, and only a click on the dot itself still means the dot.
  function sweepAt(hit) {
    const [x, z] = planPoint(hit);
    let best = null, bd = 1e9;
    for (const d of dots.values()) {
      const dd = Math.hypot(d.s.p[0] - x, d.s.p[2] - z);
      if (dd < bd) { bd = dd; best = d.s; }
    }
    if (best && bd <= (viewer.walledOff(x, z, best) ? dotRadius(dots.get(best.id)) : 1.5)) return best;
    const s = viewer.nearestSweep(x, z);
    return s && dots.has(s.id) ? s : best;
  }
  function pickAt(x, y) { return viewer.pick(x, y, { classes: PICK }); }
  // Where the dot of a sweep is on screen as the visitor sees it (viewer.project(id) in these views):
  // {x, y} in CSS px, or null when it is off screen or hidden behind a wall or furniture.
  function markerPoint(id) {
    const d = dots.get(id), size = viewer.size;
    if (!d || !last || !shown || !mode) return null;
    const p = viewer.project(d.c, 1);
    if (!p || p.x < 0 || p.y < 0 || p.x > size.cssW || p.y > size.cssH) return null;
    const hit = pickAt(p.x, p.y);
    if (hit && Math.hypot(hit.point[0] - d.c[0], hit.point[1] - d.c[1], hit.point[2] - d.c[2]) > 0.8) {
      const depth = (q) => (q[0] - last.eye[0]) * last.dir[0] + (q[1] - last.eye[1]) * last.dir[1] + (q[2] - last.eye[2]) * last.dir[2];
      if (depth(hit.point) < depth(d.c) - 0.3) return null;      // something stands in front of it
    }
    return p;
  }
  function hover() {
    hoverDue = false;
    const hit = pointer && rig && !flight && !request && viewer.pointers.size === 0 && last ? pickAt(pointer.x, pointer.y) : null;
    const s = hit ? sweepAt(hit) : null;
    const was = hot;
    hot = s ? s.id : null;
    canvas.style.cursor = s ? 'pointer' : '';
    if (s) reticle.place(hit.point, hit.normal, RETICLE_PX * feetPerPx(hit.point), 0.05);
    else reticle.hide();
    if (hot !== was) viewer.emit('hover', s ? { x: pointer.x, y: pointer.y, sweep: s.id, point: hit.point.slice() } : null);
    engine.invalidate();
  }
  function stepOverlay(dt) {
    let touched = false;
    const goal = !flight || flight.kind === 'rig' ? 1 : 0;
    if (dotAlpha !== goal) {
      dotAlpha = goal > dotAlpha ? Math.min(goal, dotAlpha + dt / 0.3) : Math.max(goal, dotAlpha - dt / 0.15);
      touched = true;
    }
    for (const d of dots.values()) {
      const hg = d.s.id === hot ? 1 : 0;
      if (d.heat !== hg) { d.heat = hg > d.heat ? Math.min(1, d.heat + dt / 0.12) : Math.max(0, d.heat - dt / 0.2); touched = true; }
      const size = dotRadius(d) * (1 + 0.35 * d.heat);
      if (Math.abs(size - d.size) > 1e-4 * size) { d.size = size; d.dot.scale.setScalar(size); d.halo.scale.setScalar(size); touched = true; }
      const a = (0.84 + 0.16 * d.heat) * dotAlpha, h = 0.34 * dotAlpha;
      if (d.dot.material.opacity !== a) { d.dot.material.opacity = a; d.halo.material.opacity = h; d.dot.visible = d.halo.visible = a > 0.004; touched = true; }
    }
    // the ring stays on the last sweep while it fades
    if (hot) hotId = hot;
    const ha = hot ? Math.min(1, hotAlpha + dt / 0.12) : Math.max(0, hotAlpha - dt / 0.2);
    if (ha !== hotAlpha) { hotAlpha = ha; touched = true; }
    const hd = hotId && dots.get(hotId);
    if (hd && hotAlpha > 0) {
      const r = Math.max(RING_FT, RING_PX * feetPerPx(hd.c));
      hotRing.visible = true;
      hotRing.position.set(hd.c[0], hd.c[1] + 0.01, hd.c[2]);
      hotRing.scale.setScalar(r);
      hotRing.material.opacity = 0.95 * hotAlpha * dotAlpha;
    } else if (hotRing.visible) { hotRing.visible = false; touched = true; }
    if (reticle.shown && (flight || !pointer)) { reticle.hide(); touched = true; }
    return touched;
  }

  // ---- flights -------------------------------------------------------------------------------
  // rig flight   {kind: 'rig', a, b, t, dur, to}: between two orbit poses, along the orbit.
  // free flight  {kind: 'free', path, dir (+1: path start -> end, -1: back), t, dur, to, look, req}.
  // A path runs from node A to node B. When A is an inside pose (path.inside) the eye rises from it
  // before it swings out, the focus glides over to the middle of the house (the room stays in view while
  // the eye is low), the lens flattens late and the engine's fades follow the way: the ceilings go while
  // the eye is still under them, the projection over the first half.
  function makePath(A, B, inside, from) {
    const rise = clamp(0.5 * (B.P[1] - A.P[1]), 6, 50);
    return { A, B, inside, C: inside ? [A.P[0], A.P[1] + rise, A.P[2]] : null, from: from || { pf: 0, co: 0 } };
  }
  function along(path, u) {
    const { A, B, C } = path, v = 1 - u;
    const P = C ? [0, 1, 2].map((i) => v * v * A.P[i] + 2 * u * v * C[i] + u * u * B.P[i]) : [0, 1, 2].map((i) => lerp(A.P[i], B.P[i], u));
    const sf = path.inside ? smooth(u) : u;
    const sz = path.inside ? smooth((u - 0.3) / 0.7) : u;
    const q = {
      P, F: [0, 1, 2].map((i) => lerp(A.F[i], B.F[i], sf)),
      psi: A.psi + angleDelta(A.psi, B.psi) * u,
      ku: lerp(A.ku, B.ku, u),
      z: 1 / lerp(1 / A.z, 1 / B.z, sz),
    };
    let pf, co;
    if (path.inside) {
      // what the far end still showed (a flight interrupted on its way out) fades over the first part
      const rest = smooth((u - 0.4) / 0.6);
      co = Math.max(1 - smooth(u / 0.03), path.from.co * rest);
      pf = Math.max(1 - smooth((u - 0.03) / 0.45), path.from.pf * rest);
    } else {
      const go = 1 - smooth(u / 0.5);
      co = path.from.co * go;
      pf = path.from.pf * go;
    }
    return { q, pf, co };
  }
  function announce(active, from, to, sweep) { viewer.emit('flight', { active, from: from || mode, to: to || mode, sweep: sweep || null }); }
  // Where the camera is now, as the start of the next flight: on the orbit (a rig), or anywhere (a node:
  // in a flight from or to a sweep, or held still between two such flights).
  function nowRig() { return flight && flight.kind === 'rig' ? flight.cur || copyRig(flight.a) : rig ? copyRig(rig) : null; }
  function nowNode() { const g = nowRig(); return g ? rigNode(g) : { P: node.P.slice(), F: node.F.slice(), psi: node.psi, ku: node.ku, z: node.z }; }
  function endFlight(ok) {
    const f = flight;
    flight = null;
    if (f && f.resolve) f.resolve(ok);
  }
  function startRig(a, b, dur, to) {
    endFlight(false);
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    flight = { kind: 'rig', a, b, t: 0, dur: calm.matches ? 0.001 : dur, to, resolve, promise, started: false };      // (less motion: there at once)
    rig = null;
    announce(true, mode, to);
    return promise;
  }
  function startFree(path, dir, dur, to, extra) {
    endFlight(false);
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    flight = Object.assign({ kind: 'free', path, dir, t: 0, dur, to, resolve, promise, started: false, u: dir > 0 ? 0 : 1 }, extra || {});
    rig = null;
    return promise;
  }
  function stepFlight(real) {
    const f = flight;
    if (!f.started) { f.started = true; real = 0; }    // the clock starts with the first frame
    f.t = Math.min(1, f.t + real / f.dur);
    if (f.kind === 'rig') {
      f.cur = mixRig(f.a, f.b, ease(f.t));
      node = rigNode(f.cur);
    } else {
      f.u = f.path.inside ? reach(f.dir > 0 ? f.t : 1 - f.t) : smooth(f.t);
      const r = along(f.path, f.u);
      node = r.q;
      setFades(r.pf, r.co);
    }
    if (f.t >= 1) {
      if (f.to === 'inside') land(f);
      else settle(f);
    }
  }
  // A flight to the dollhouse or the plan is over: the visitor has the camera.
  function settle(f) {
    flight = null;
    rig = rigs[mode];
    node = rigNode(rig);
    zoomGoal = rig.half;
    setFades(0, 0);
    hoverDue = true;
    announce(false);
    if (f && f.resolve) f.resolve(true);
  }
  // A fly-in is over: the camera stands on the sweep, the inside view takes over with the same view.
  function land(f) {
    const req = f.req;
    flight = null;
    if (request === req) request = null;
    const done = (ok) => { if (req) req.resolve(ok); if (f.resolve) f.resolve(ok); };
    viewer.setMode('inside', { sweep: f.sweep, yaw: f.look.yaw, pitch: f.look.pitch, direct: true, landed: true }).then(done, () => done(false));
    announce(false, 'inside', 'inside', f.sweep);
  }
  function dropRequest() {
    const req = request;
    if (!req) return;
    request = null;
    req.resolve(false);
    viewer.emit('busy', { active: false });
    announce(false);
  }

  // The direction to arrive in: the one asked for; the sweep's own (reset, or coming from the plan);
  // the visitor's last one when the Inside button brings them back; otherwise away from the camera's side.
  function arrival(id, o, back) {
    const s = viewer.sweep(id), ins = insideCtl().state();
    let yaw, pitch;
    if (finite(o.yaw)) yaw = o.yaw;
    else if (o.reset) yaw = s.look.yaw;
    else if (o.heading !== undefined) yaw = o.heading;
    else if (back) yaw = ins.yaw;
    else yaw = mode === 'dollhouse' && rigs.dollhouse ? node.psi : s.look.yaw;
    if (finite(o.pitch)) pitch = o.pitch;
    else if (back && !o.reset && !finite(o.yaw)) pitch = ins.pitch;
    else pitch = s.look.pitch;
    return { yaw, pitch: clamp(pitch, -80 * DEG, 80 * DEG) };
  }
  // Fly into a sweep. Resolves true once the inside view stands there, false when something else was
  // asked for meanwhile.
  function flyIn(id, o = {}) {
    if (request && request.id === id && !o.force) return request.promise;
    const old = request;
    request = null;
    if (old) {
      old.resolve(false);
      if (flight && flight.req === old) endFlight(false);       // the camera waits where it is for the new one
    }
    const back = !o.sweep && !o.clicked;                // "Inside": back to where the visitor stood
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    const req = request = { id, o, back, promise, resolve };
    announce(true, mode, 'inside', id);
    hoverDue = true;
    // What the engine projects is the engine's to say (the inside view and the exterior set it too).
    // Declared before it loads, so the engine keeps it (not while another sweep's panorama still shows).
    if (engine.blend.a !== id && fades.pf < 0.02) engine.setSweepBlend(id);
    const ready = insideCtl().preload ? insideCtl().preload(id) : Promise.resolve(false);
    if (!engine.hasPanorama(id)) viewer.emit('busy', { active: true });
    Promise.race([ready, sleep(PRELOAD_MS)]).catch(() => false).then(() => {
      if (request !== req || !mode) return;
      viewer.emit('busy', { active: false });
      const look = arrival(id, o, back);
      if (!engine.hasPanorama(id)) {
        // nothing to fly into (the file cannot be had, or not in time): a cut, which keeps this picture
        // up until the panorama is in, instead of a flight into the bare model
        request = null;
        announce(false);
        viewer.setMode('inside', { sweep: id, yaw: look.yaw, pitch: look.pitch, direct: true }).then(resolve, () => resolve(false));
        return;
      }
      if (engine.blend.a !== id || engine.blend.b !== null) { engine.setSweepBlend(id); setFades(0, fades.co); }
      const s = viewer.sweep(id), vfov = (insideCtl().state().vfov || 68) * DEG;
      const A = insideNode(s.p, look.yaw, look.pitch, vfov);
      startFree(makePath(A, nowNode(), true, { pf: fades.pf, co: fades.co }), -1, FLY, 'inside', { req, sweep: id, look });
    });
    return promise;
  }

  // Asked by the viewer before it leaves this mode (see viewer.setMode): a Promise = this module makes
  // the way out itself and switches at the end; null = switch at once.
  function depart(to, o = {}) {
    if (to !== 'inside' || o.instant || calm.matches || !mode) { dropRequest(); return null; }
    const id = o.sweep && viewer.sweep(o.sweep) ? o.sweep : insideCtl().state().sweep;
    if (!id || !viewer.sweep(id)) { dropRequest(); return null; }
    return flyIn(id, o);
  }

  // ---- entering and leaving ------------------------------------------------------------------
  function enter(which, from, o = {}) {
    const prev = mode, g = rigs[which], size = viewer.size;
    if (!prev) shown = false;
    mode = which;
    group.visible = true;
    viewer.setBackground(DARK);
    setTone();
    drawn.length = 0;
    clock = 0;
    velYaw = velPhi = 0;
    velPan = [0, 0];
    zoomAt = null;
    if (from === which && prev === which) {
      // asked for again while active: a fly-in under way turns back, anything else stays as it is
      const had = request;
      dropRequest();
      if ((flight && flight.to === 'inside') || (!flight && !rig)) {
        const p = startFree(makePath(nowNode(), rigNode(g), false, { pf: fades.pf, co: fades.co }), 1, FLY * 0.7, which);
        announce(true, which, which);
        return p;
      }
      if (!flight && !had && o.frame) return startRig(copyRig(g), copyRig(frameRig(g, size)), REFRAME, which);
      return flight ? flight.promise : Promise.resolve(true);
    }
    dropRequest();
    const cameFrom = nowRig();
    if (which === 'dollhouse') {
      g.yaw = from === 'inside' ? diagonal(insideCtl().view().yaw) : g.yaw;
      g.phi = PHI;
    }
    frameRig(g, size);
    zoomGoal = g.half;
    if (from === 'inside' && !calm.matches && insideCtl().view) {
      // the same picture as the inside view, then out
      const v = insideCtl().view(), id = insideCtl().state().sweep;
      engineMode(which);
      setFades(1, 1);
      pushFades();
      engine.setSweepBlend(id);                        // (inside.leave() left it so: the panorama the flight starts in)
      node = insideNode(v.eye, v.yaw, v.pitch, v.fovY);
      const p = startFree(makePath(node, rigNode(g), true), 1, FLY, which, { sweep: id });
      announce(true, 'inside', which, id);
      return p;
    }
    if (prev && prev !== which && !calm.matches) {
      // from the other one of the two views, wherever its camera is
      engineMode(which);
      pushFades();
      if (!cameFrom) {                                  // in a flight from or to a sweep
        const p = startFree(makePath(nowNode(), rigNode(g), false, { pf: fades.pf, co: fades.co }), 1, SWITCH, which);
        announce(true, prev, which);
        return p;
      }
      return startRig(cameFrom, copyRig(g), SWITCH, which);
    }
    // from the exterior, the landing page or a link; or from anywhere without motion: a dissolve, no flight
    if (from === 'exterior' || (from && calm.matches)) viewer.crossfade();
    endFlight(false);
    engineMode(which);
    setFades(0, 0);
    pushFades();
    rig = g;
    node = rigNode(g);
    dotAlpha = 1;
    hoverDue = true;
    return Promise.resolve(true);
  }
  function leave(which, to) {
    if (to === 'dollhouse' || to === 'floorplan') return;      // the other half of this module goes on with the camera
    // (the view that comes next dissolves from this picture itself: inside.js, exterior.js)
    const flying = !!flight;
    dropRequest();
    endFlight(false);
    if (flying) viewer.emit('flight', { active: false, from: which, to, sweep: null });       // a flight cut short has ended too
    mode = null;
    rig = null;
    pointer = null;
    hot = null;
    last = null;
    shown = false;
    reticle.hide();
    hotRing.visible = false;
    group.visible = false;
    canvas.style.cursor = '';
    tone = null;
    engine.setAdaptation(null, null, true);
    engine.invalidate();
  }

  // ---- the frame -----------------------------------------------------------------------------
  function frame(dt, size, now) {
    if (!mode) return false;
    const real = clock ? clamp((now - clock) / 1000, 0, 0.1) : dt;
    clock = now;
    if (flight) stepFlight(real);
    if (!mode) return false;                            // landed: the inside view draws from the next frame on
    if (rig) {
      const free = viewer.pointers.size === 0;
      if (free && (velYaw || velPhi)) {
        rig.yaw += velYaw * dt;
        rig.phi = clamp(rig.phi + velPhi * dt, PHI_MIN, PHI_MAX);
        const k = Math.exp(-dt * 5);
        velYaw *= k;
        velPhi *= k;
        if (Math.hypot(velYaw, velPhi) < 0.01) velYaw = velPhi = 0;
      }
      if (free && (velPan[0] || velPan[1])) {
        rig.pivot[0] += velPan[0] * dt;
        rig.pivot[2] += velPan[1] * dt;
        clampTarget(rig);
        const k = Math.exp(-dt * 6);
        velPan = [velPan[0] * k, velPan[1] * k];
        if (Math.hypot(velPan[0], velPan[1]) < 0.05) velPan = [0, 0];
      }
      if (zoomGoal && rig.half !== zoomGoal) {
        let h = rig.half + (zoomGoal - rig.half) * (1 - Math.exp(-dt * 13));
        if (Math.abs(h - zoomGoal) < 0.002 * zoomGoal) h = zoomGoal;
        zoomTo(h, zoomAt);
        if (rig.half !== h) zoomGoal = rig.half;       // a limit was reached
      }
      const h = clampHalf(rig, rig.half);              // the lower limit follows the elevation
      if (h !== rig.half) { rig.half = h; zoomGoal = h; }
      // as framed: the house keeps filling the free part of the screen while it is tilted
      if (rig.auto && rig.z === 1 && rig.phi !== rig.framed) { frameRig(rig, size); zoomGoal = rig.half; }
      node = rigNode(rig);
    }
    pushFades();
    const v = viewOf(node, fades.pf > 0.001);
    last = v;
    const key = [v.eye[0], v.eye[1], v.eye[2], v.dir[0], v.dir[1], v.dir[2], v.view.up[0], v.view.up[2], v.flat ? -v.half : v.k, size.w, size.h];
    const same = drawn.length === key.length && key.every((x, i) => x === drawn[i]);
    if (!same) hoverDue = true;                         // the view moved under a still mouse
    if (hoverDue && shown && (pointer || hot)) hover(); // (the engine picks with the camera of its last frame)
    if (stepOverlay(real)) engine.invalidate();
    if (same && !engine.dirty()) return false;
    viewer.render(v.view);
    shown = true;
    drawn.length = 0;
    drawn.push(...key);
    return true;
  }

  // ---- input ---------------------------------------------------------------------------------
  const busy = () => !!flight || !rig;
  function touch() { rig.auto = false; }
  function onPointerDown() {
    velYaw = velPhi = 0;
    velPan = [0, 0];
    if (rig) zoomGoal = rig.half;
    zoomAt = null;
    hoverDue = true;
  }
  function onDrag(p) {
    if (!p.dragged || busy()) return;
    if (mode === 'floorplan') {
      touch();
      const k = 2 * rig.half / viewer.size.cssH;        // feet per CSS pixel
      rig.pivot[0] -= p.dx * k;
      rig.pivot[2] -= p.dy * k;
      clampTarget(rig);
      return;
    }
    if (p.button === 2 || p.button === 1 || p.shift) { touch(); slide([p.x - p.dx, p.y - p.dy], [p.x, p.y]); return; }
    const now = performance.now(), dt = Math.max(0.004, (now - lastDrag) / 1000);
    const dy = p.dx * ORBIT, dp = p.dy * ORBIT;
    rig.yaw += dy;
    rig.phi = clamp(rig.phi + dp, PHI_MIN, PHI_MAX);
    if (dt < 0.1) { velYaw = lerp(velYaw, clamp(dy / dt, -5, 5), 0.5); velPhi = lerp(velPhi, clamp(dp / dt, -5, 5), 0.5); } else velYaw = velPhi = 0;
    lastDrag = now;
  }
  function onPinch(scale, p) {
    if (busy()) return;
    touch();
    const other = [...viewer.pointers.values()].find((q) => q !== p);
    const c = other ? [(p.x + other.x) / 2, (p.y + other.y) / 2] : [p.x, p.y], was = [c[0] - p.dx / 2, c[1] - p.dy / 2];
    zoomTo(rig.half * scale, groundAt(was[0], was[1]));
    zoomGoal = rig.half;
    if (mode === 'floorplan') {
      const k = 2 * rig.half / viewer.size.cssH;
      rig.pivot[0] -= p.dx / 2 * k;
      rig.pivot[2] -= p.dy / 2 * k;
      clampTarget(rig);
    } else slide(was, c);
    velYaw = velPhi = 0;
  }
  function onPointerUp(p, e) {
    if (performance.now() - lastDrag > 90) velYaw = velPhi = 0;       // the pointer had stopped: no coasting
    pointer = e && e.pointerType === 'mouse' && !p.cancelled ? { x: e.clientX, y: e.clientY } : null;
    hoverDue = true;
  }
  function onHover(p) {
    pointer = p ? { x: p.x, y: p.y } : null;
    hoverDue = true;
  }
  function onWheel(e) {
    if (busy()) return;
    touch();
    zoomGoal = clampHalf(rig, (zoomGoal || rig.half) * Math.exp(util.wheelPixels(e) * 0.0012));
    zoomAt = groundAt(e.clientX, e.clientY);
  }
  function onClick(p) {
    if (!mode || !last || !shown) return false;
    if (flight && flight.kind === 'free' && flight.to !== 'inside') return false;      // still on the way out
    const hit = pickAt(p.x, p.y), s = hit ? sweepAt(hit) : null;
    if (!s) return false;
    // facing away from the camera's side; on the plan, toward the point clicked when it is not the sweep
    // itself. A room nobody can stand in (the laundry closet behind its doors, a reach-in closet) is
    // entered on the sweep in front of it, looking at the room (viewer.lookInto).
    const at = planPoint(hit), into = viewer.lookInto(viewer.roomAt(at[0], at[1]), s);
    const d = [hit.point[0] - s.p[0], hit.point[2] - s.p[2]];
    const heading = into !== undefined ? into : mode === 'dollhouse' ? node.psi : Math.hypot(d[0], d[1]) > 2.5 ? Math.atan2(d[0], -d[1]) : s.look.yaw;
    viewer.setMode('inside', { sweep: s.id, clicked: true, heading });
    return s.id;
  }
  function onKey(e) {
    if (busy()) return false;
    const k = e.key.toLowerCase(), plan = mode === 'floorplan';
    const step = rig.half * 1.6;                        // ft/s of pan impulse
    if (k === 'arrowleft') { if (plan) { touch(); velPan[0] = -step; } else velYaw = -1.1; }
    else if (k === 'arrowright') { if (plan) { touch(); velPan[0] = step; } else velYaw = 1.1; }
    else if (k === 'arrowup') { if (plan) { touch(); velPan[1] = -step; } else velPhi = 0.7; }
    else if (k === 'arrowdown') { if (plan) { touch(); velPan[1] = step; } else velPhi = -0.7; }
    else if (k === '+' || k === '=') { touch(); zoomGoal = clampHalf(rig, (zoomGoal || rig.half) / 1.25); zoomAt = null; }
    else if (k === '-' || k === '_') { touch(); zoomGoal = clampHalf(rig, (zoomGoal || rig.half) * 1.25); zoomAt = null; }
    else if (k === '0' || k === 'home') {               // back to the framed view
      const a = copyRig(rig), g = rig;
      if (!plan) g.phi = PHI;
      startRig(a, copyRig(frameRig(g, viewer.size)), REFRAME, mode);
    } else return false;
    return true;
  }
  function onResize(size) {
    drawn.length = 0;
    for (const name of ['dollhouse', 'floorplan']) {
      const g = rigs[name];
      if (g.auto) frameRig(g, size);
      else { const keep = copyRig(g); frameRig(g, size); Object.assign(g, { pivot: keep.pivot, off: keep.off, auto: false }); g.half = clampHalf(g, keep.half); }
    }
    if (rig) zoomGoal = rig.half;
    if (flight && flight.to !== 'inside' && mode) {     // a flight under way ends on the new framing
      if (flight.kind === 'rig') flight.b = copyRig(rigs[mode]);
      else if (flight.dir > 0) flight.path.B = rigNode(rigs[mode]);
    }
  }
  // The reel opened or closed: a house that is still as framed glides into the part of the screen that
  // is left; one the visitor has zoomed or slid stays where they put it.
  viewer.on('insets', () => {
    if (!mode) return;
    const size = viewer.size;
    if (flight || !rig || calm.matches) { onResize(size); return; }      // a flight ends on the new framing
    const other = rigs[mode === 'dollhouse' ? 'floorplan' : 'dollhouse'];
    if (other.auto) frameRig(other, size);
    if (rig.auto) startRig(copyRig(rig), copyRig(frameRig(rig, size)), MAKE_ROOM, mode);
  });
  const flightState = () => (flight ? { to: flight.to, sweep: flight.sweep || null, t: flight.t } : request ? { to: 'inside', sweep: request.id, t: 0 } : null);

  function controller(which) {
    return {
      enter: (from, o) => enter(which, from, o),
      leave: (to) => leave(which, to),
      depart,
      markerPoint,
      frame,
      // waiting for something no event announces (the viewer's loop keeps its full rate meanwhile)
      busy: () => !!flight || !!request || (hoverDue && !!(pointer || hot)) || velYaw !== 0 || velPhi !== 0 || velPan[0] !== 0 || velPan[1] !== 0 || (!!rig && !!zoomGoal && rig.half !== zoomGoal),
      onPointerDown, onDrag, onPinch, onPointerUp, onHover, onWheel, onClick, onKey, onResize,
      state() {
        const g = flight && flight.kind === 'rig' && flight.cur ? flight.cur : rigs[which];
        const base = { auto: !!rigs[which].auto, hover: hot, flight: flightState() };
        return which === 'dollhouse'
          ? Object.assign(base, { target: targetOf(g), pivot: g.pivot.slice(), yaw: g.yaw, theta: -g.yaw, phi: g.phi, half: g.half, radius: g.half / K })
          : Object.assign(base, { x: targetOf(g)[0], z: targetOf(g)[2], halfHeight: g.half, fov: 0 });
      },
    };
  }
  return { dollhouse: controller('dollhouse'), floorplan: controller('floorplan') };
}
