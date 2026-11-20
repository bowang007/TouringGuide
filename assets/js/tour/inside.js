// INSIDE view: sweep navigation in the manner of a Matterport tour.
//
// The camera only ever rests on a sweep, and there the frame is that sweep's path-traced panorama
// (engine.setSweepBlend(id)). Dragging looks around (with inertia), the wheel / a pinch / + and - zoom the
// field of view. Soft white rings lie on the floor at the sweeps one can go to; a ring under the mouse
// lies on whatever surface the cursor is over. A click or tap moves: the camera glides to the other sweep
// while the engine cross-fades the two panoramas projected on the model, and the direction one is looking
// in is kept. A double click is one click (the move it starts is never taken back or carried on).
//
// The view is `early` (viewer.js): at rest it needs the panorama alone, so it opens while the 3D model is
// still downloading. Until the model is in there are no rings and no cursor ring (both lie on its
// surfaces), and a move is a dissolve instead of a glide.
//
// Parts of this file: panorama loading (levels, neighbours ahead of time) / the sweep graph helpers /
// flights (one hop or a chain of hops flown without stopping, and the dissolve of far jumps) / the
// overlay (rings, reticle) / the controller the viewer calls.
//
// Public, besides the controller interface (see viewer.js):
//   goTo(id, opts) -> Promise<boolean>   move there: a direct glide when the sweep is in view, a flight
//                                        along the links otherwise, a dissolve when it is far (more than
//                                        FAR_HOPS hops) or opts.instant is set. Resolves true on arrival,
//                                        false when another destination replaced it.
//                                        opts.reset = arrive facing the sweep's own direction,
//                                        opts.yaw / opts.pitch (radians) = arrive facing that direction
//                                        (a flight turns on the way, a dissolve arrives turned).
//   jumpTo(id, opts) -> Promise<boolean> cut, no animation; resolves when the panorama is on screen
//   setLook(yaw, pitch)                  radians
//   state() -> {sweep, yaw, pitch, fov (degrees, the landscape value), vfov (degrees, as drawn),
//               transition: null | {from, to, t, route, target}, pano: {id, level}, resting, reticle, hover}
//   ringPoint(id) -> {x, y} | null       where the floor ring of a sweep is on screen (CSS px): null when it
//                                        is not shown from here, off screen, or hidden behind something
//   rings() -> [{id, x, y, rx, ry, seen, alpha}]    the rings on screen (tests)
//   reticle() -> {x, y, point, normal, cls} | null  the cursor ring (tests)
//   setOverlay(on)                       rings and reticle on / off (tests: comparing the frame with the file)
//   preload(id) -> Promise<boolean>      panorama + depth cube of a sweep ready for a move (dollhouse fly-in)
//   view() -> {eye, aim, fovY}           the camera of the inside view right now (dollhouse fly-out)

import * as THREE from 'three';

export function createInside(viewer, deps = {}) {
  const { engine, util, panos, tour, canvas } = viewer;
  const { DEG, clamp, lerp, smooth, angleDelta, lookDir, distance, norm, sleep, calm } = util;
  const layer = deps.markers || document.getElementById('markers');
  const PREPARE = Number.isFinite(deps.prepare) ? deps.prepare : 2;   // neighbours given a depth cube ahead of a move
  const HOLD = Number.isFinite(deps.hold) ? deps.hold : 4;            // neighbours whose 2k level is kept on the GPU

  // ---- numbers -------------------------------------------------------------------------------
  const FOV_MIN = 35 * DEG, FOV_MAX = 80 * DEG;        // vertical, landscape screen
  const FOV = clamp((deps.fov || 68) * DEG, FOV_MIN, FOV_MAX);       // the view one enters with (main.js names it)
  const PITCH_MAX = 80 * DEG;
  const RING = 0.75;                                   // ft, outer radius of a floor ring (1.5 ft across)
  const RING_LIFT = 0.06;                              // ft above the floor
  const RING_BAND = 0.62;                              // inner radius of the band as a share of the outer
  const RING_ALPHA = 0.42, RING_HALO = 0.1;            // a ring at rest: soft and translucent (the one under the cursor is full white); its dark halo
  const RING_NEAR = 9, RING_FAR = [0.32, 0.35, 28];    // rings beyond RING_NEAR ft: [faintest opacity, growth, distance (ft) where both are reached]
  const RETICLE_PX = 23;                               // CSS px, radius of the cursor ring
  const hopSeconds = (d) => clamp(350 + 55 * d, 550, 1100) / 1000;   // one hop of d feet
  const ACC = 50;                                      // ft/s^2 in a chain of hops (one hop derives its own)
  const CRUISE = 16, CRUISE_UP = 1.12, CRUISE_MAX = 24;   // ft/s between the hops of a chain: each one a little faster
  const FAR_HOPS = 5;                                  // more hops than this: fade instead of flying
  const WAIT_MS = 300;                                 // longest a move waits for its destination to load
  const HOLD_MS = 1500;                                // longest a cut keeps the old picture up while the new panorama loads
  const JUMP_WAIT = 12, DISSOLVE = 0.4;                // s: longest a far jump waits for its panorama; the dissolve (tour.css .xfade)
  const DWELL_8K = 1000;                               // ms of rest before the 8k level is asked for: a visitor walking through never needs it
  const VIEW_CONE = 35 * DEG, LINK_CONE = 60 * DEG;    // a click: sweeps in view / linked sweeps count within these of its direction
  const KEY_CONE = 45 * DEG;                           // a step key: the four quarters around the view direction
  const DOUBLE_MS = 450, DOUBLE_PX = [18, 34];         // clicks this close in time and place (mouse, touch) are one click

  // ---- state ---------------------------------------------------------------------------------
  let active = false, overlayOn = true;
  let cur = tour.start && viewer.sweep(tour.start) ? tour.start : (viewer.sweeps[0] || {}).id;
  let yaw = 0, pitch = 0, fov = FOV, fovGoal = FOV;
  let vel = [0, 0], lastDrag = 0;                      // look inertia (rad/s)
  let turnLeft = 0, turnVel = 0;                       // a turn still to make (arrow keys, goTo with a direction)
  let tiltLeft = 0;
  let flight = null;                                   // a move under way (see "flights")
  let veil = null;                                     // a far jump under way: {id, o, phase (0 loading, 2 dissolving), t, ready, waiters}
  let late = null;                                     // {from, t}: arrived before the panorama did; `from` stays on screen
  let hold = 0;                                        // cut to a sweep whose panorama is not in yet: nothing is drawn until then (or this time)
  let pointer = null;                                  // the mouse over the canvas: {x, y}
  let hot = null, focused = null;                      // ring under the cursor / ring with keyboard focus
  let hoverRetry = 0;
  let lastClick = null;                                // {t, x, y, flight}: the last click and the move it set off
  let shake = 0;                                       // s left of the reticle's "nothing there" wobble
  let restAt = 0, busyAt = 0, viewAt = 0, clock = 0;
  let plan = 0;                                        // token of the loading plan of the current rest
  let markersDue = false;
  const drawn = [];                                    // the view of the last drawn frame
  if (cur) { yaw = viewer.sweep(cur).look.yaw; pitch = clampPitch(viewer.sweep(cur).look.pitch); }

  function clampPitch(p) { return clamp(p, -PITCH_MAX, PITCH_MAX); }
  const planDist = (a, b) => Math.hypot(a[0] - b[0], a[2] - b[2]);
  const bearing = (a, b) => Math.atan2(b[0] - a[0], -(b[2] - a[2]));          // yaw of b seen from a
  const finite = Number.isFinite;

  // Vertical field of view actually drawn: `fov` is the landscape value; a portrait screen widens it so
  // the picture does not turn into a slit (a phone held upright sees about 53 x 94 degrees by default).
  function viewFov(size, f = fov) {
    const a = size.w / Math.max(1, size.h);
    return Math.min(112 * DEG, 2 * Math.atan(Math.tan(f / 2) * (a < 1 ? Math.pow(1 / a, 0.6) : 1)));
  }
  // ---- panoramas -----------------------------------------------------------------------------
  // Levels come from the manifest (2k / 4k / 8k, a sweep may lack some). On arrival the best level the
  // engine already holds is shown at once; then the sweep climbs 2k -> 4k -> 8k as far as this device goes
  // (panos.best: no 8k on phones, small GPUs or little memory; 8k only after DWELL_8K of rest).
  // Meanwhile the line is used in the order the visitor waits for things: the 2k level of the sweeps one
  // step away (a hop to them must start at once), the sharper levels of this sweep (while one of those
  // downloads, the other rings wait), the 2k of the other sweeps in view, with the nearest ones getting
  // their depth cube, and last the 2k files of the rest of the house. A ring under the cursor is loaded
  // at once. A file that fails is skipped for another level.
  // While the 3D model is still downloading (the view is up before it) the line belongs to the model:
  // only the 4k level of the sweep and the 2k of the sweeps one step away are fetched beside it; the
  // rest of the plan runs when the model is in.
  // A sharper level belongs to the rest it was asked for: when the visitor moves on, its download is
  // aborted, a file that is already in is not decoded, and an upload under way is dropped (leaveBehind).
  const quick = (id) => panos.quick(id);
  function climb(id) {                                 // levels above the quick one up to the best, lowest first
    const all = panos.levels(id).slice().reverse(), best = panos.best(id), q = quick(id), out = [];
    if (!best || best === q) return out;
    for (const l of all) {
      if (panos.rank(l) <= panos.rank(q)) continue;
      out.push(l);
      if (l === best) break;
    }
    return out;
  }
  function shownLevel(id) { const h = engine.hasPanorama(id); return h ? (h.pending ? h.shown : h.level) : null; }
  // The sweep a sharper level is still wanted for: the one the visitor rests on or is on the way to.
  const sharpFor = (id) => active && id === (flight ? flight.route[flight.route.length - 1] : veil ? veil.id : cur);
  const aborted = (err) => !!err && err.name === 'AbortError';
  // The visitor's line is slow or metered (where the browser says so): nothing is fetched on spec.
  function frugal() {
    const c = navigator.connection;
    return !!c && (c.saveData || /(^|-)2g$|^3g$/.test(c.effectiveType || '') || (c.downlink > 0 && c.downlink < 1.5));
  }

  const failed = new Map();                            // id|level or url -> time after which it may be tried again
  const blobs = new Map();                             // url -> Promise<Blob>; the quick level stays, others: last 4
  // low: a file nobody is waiting for (fetch priority 'low', where the browser knows it).
  function blobOf(id, lvl, low) {
    const url = panos.url(id, lvl);
    if (!url) return Promise.reject(new Error('no ' + lvl + ' panorama for ' + id));
    let p = blobs.get(url);
    if (p) return p;
    if ((failed.get(url) || 0) > performance.now()) return Promise.reject(new Error('unavailable ' + url));
    const keep = lvl === quick(id), init = {};
    const stop = !keep && typeof AbortController === 'function' ? new AbortController() : null;
    if (stop) init.signal = stop.signal;
    if (low) init.priority = 'low';
    p = fetch(url, init).then((r) => { if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url); return r.blob(); });
    Object.assign(p, { keep, id, done: false, abort: stop ? () => stop.abort() : null });
    blobs.set(url, p);
    p.then(() => { p.done = true; }, (err) => { if (!aborted(err)) failed.set(url, performance.now() + 20000); if (blobs.get(url) === p) blobs.delete(url); });
    let extra = [...blobs].filter(([, v]) => !v.keep).length - 4;
    for (const [k, v] of blobs) { if (extra <= 0) break; if (!v.keep && v !== p) { blobs.delete(k); extra--; } }
    return p;
  }
  // The visitor leaves a sweep: the sharper levels still downloading for any sweep but `keep` end here,
  // and so does a level of `left` that is still being uploaded.
  function leaveBehind(left, keep) {
    for (const [url, p] of blobs) if (!p.keep && !p.done && p.abort && p.id !== keep) { blobs.delete(url); p.abort(); }
    if (left && left !== keep) engine.dropUpgrade(left);
  }

  const jobs = new Map();                              // id|level -> Promise<boolean> while it loads
  const queue = [];                                    // background loads wait their turn here (two at a time)
  let running = 0, sharpBusy = 0;                      // sharpBusy: sharper levels of the resting sweep on the line
  // bg: a load that also waits while a sharper level of the resting sweep is downloading.
  function turn(key, bg) {
    if (running < 2 && !(bg && sharpBusy)) { running++; return Promise.resolve(); }
    return new Promise((go) => queue.push({ key, go, bg }));
  }
  function pump() {
    while (running < 2) {
      const i = queue.findIndex((q) => !(q.bg && sharpBusy));
      if (i < 0) return;
      running++;
      queue.splice(i, 1)[0].go();
    }
  }
  function next() { running--; pump(); }
  function hurry(key) { const i = queue.findIndex((q) => q.key === key); if (i >= 0) { running++; queue.splice(i, 1)[0].go(); } }
  // One level of one panorama into the engine. urgent = the sweep the camera is on or moving to (or the
  // ring under the cursor); bg = see turn(); sharp = a level above the quick one, wanted only while the
  // visitor rests on the sweep or is on the way to it.
  function ensure(id, lvl, urgent, o = {}) {
    if (!lvl || !panos.has(id) || !viewer.sweep(id)) return Promise.resolve(false);
    if (engine.hasPanorama(id, lvl)) return Promise.resolve(true);
    const key = id + '|' + lvl, busy = jobs.get(key);
    if (busy) { if (urgent) hurry(key); return busy; }
    if ((failed.get(key) || 0) > performance.now()) return Promise.resolve(false);
    const job = (async () => {
      let queued = !urgent, onLine = false;
      if (queued) await turn(key, o.bg);
      const offLine = () => { if (onLine) { onLine = false; sharpBusy--; pump(); } };
      try {
        if (o.sharp && !sharpFor(id)) return false;
        if (o.sharp) { onLine = true; sharpBusy++; }
        const blob = await blobOf(id, lvl, !urgent);
        offLine();
        if (o.sharp && !sharpFor(id)) return false;    // the visitor has moved on: the file stays, nothing is decoded
        const img = await util.decodeImage(blob);
        if (viewer.engineState === 'failed' || (o.sharp && !sharpFor(id))) { if (img.close) img.close(); return false; }
        engine.setPanorama(id, img, lvl);              // refused when the engine already holds a better one
        return engine.hasPanorama(id, lvl);
      } catch (err) {
        if (aborted(err)) return false;                // (leaveBehind: not a failure, it may be asked for again)
        console.warn('[tour] panorama ' + id + ' (' + lvl + ') is unavailable: ' + (err && err.message ? err.message : err));
        failed.set(key, performance.now() + 20000);
        return false;
      } finally {
        offLine();
        if (queued) next();
        jobs.delete(key);
      }
    })();
    jobs.set(key, job);
    return job;
  }
  // Any level at all, the quick one first: what a sweep needs before it can be shown.
  async function ensureSome(id, urgent, bg) {
    if (engine.hasPanorama(id)) return true;
    const q = quick(id);
    for (const l of [q, ...panos.levels(id).slice().reverse().filter((x) => x !== q)]) if (l && await ensure(id, l, urgent, { bg })) return true;
    return !!engine.hasPanorama(id);
  }
  // The quick level's file alone (a click on that sweep then costs a decode, not a download).
  async function fileOf(id) {
    const key = id + '|file';
    await turn(key, true);
    try { await blobOf(id, quick(id), true); } catch (e) { /* tried again when it is needed */ } finally { next(); }
  }
  // Panorama and depth cube of a sweep, ready for a move to it.
  function preload(id) {
    return ensureSome(id, true).then((ok) => (ok ? engine.prepare(id, null, { pick: false }) : false)).catch(() => false);
  }
  // Resolves once nothing has moved for `ms` (false when the plan it belongs to is over).
  async function idle(t, ms = 150) {
    for (;;) {
      if (t !== plan || !active) return false;
      if (!flight && !veil && performance.now() - busyAt >= ms) return true;
      await sleep(50);
    }
  }
  // The loading plan of a rest; restarted on every arrival, dropped when a move starts.
  async function settle() {
    const t = ++plan, id = cur;
    const fresh = () => t === plan && active && cur === id;
    try {
      let ok = await ensureSome(id, true);
      while (!ok && fresh()) {                         // nothing could be loaded: keep trying while standing here
        await sleep(4000);
        if (!fresh()) return;
        failed.clear();
        ok = await ensureSome(id, true);
      }
      if (!fresh()) return;
      const links = viewer.sweep(id).links, near = around(id), model = viewer.modelReady;
      const order = model ? [...near.filter((n) => links.includes(n)), ...near.filter((n) => !links.includes(n))] : near.filter((n) => links.includes(n));
      const sharpen = (async () => {
        for (const l of climb(id)) {
          if (engine.hasPanorama(id, l)) continue;
          if (!model && panos.rank(l) >= 3) return;      // (the 8k level waits for the model: 'ready' runs this plan again)
          const wait = (panos.rank(l) >= 3 ? DWELL_8K : 80) - (performance.now() - restAt);   // 8k only for a real stop
          if (wait > 0) await sleep(wait);
          if (!fresh()) return;
          await ensure(id, l, true, { sharp: true });
        }
      })();
      const ahead = async () => {
        // the nearest ones into the engine, the linked sweeps first and regardless of what else is on the
        // line; the others as files only (a click on one costs a decode)
        await Promise.all(order.slice(0, HOLD).map((n) => (fresh() ? ensureSome(n, false, !links.includes(n)) : false)));
        if (!fresh()) return;
        let k = 0;
        for (const n of order) {
          if (k >= PREPARE) break;
          if (!(await idle(t))) return;
          if (!engine.hasPanorama(n)) continue;
          await engine.prepare(n, null, { pick: false });
          k++;
        }
        await Promise.all(order.slice(HOLD).map((n) => (fresh() ? fileOf(n) : null)));
      };
      await Promise.all([sharpen, ahead()]);
      if (!fresh()) return;
      await ahead();                                   // a sharper level may have pushed a neighbour out of the budget
      if (frugal() || !model) return;
      for (const n of spread(id)) {                    // the rest of the house: the files only, one at a time
        if (!(await idle(t, 400))) return;
        await fileOf(n);
      }
    } catch (e) { viewer.report(e, 'inside:settle'); }
  }

  // ---- the sweep graph -----------------------------------------------------------------------
  // Sweeps one can go to directly from a sweep: those in view (rings) and the linked ones, nearest first.
  const aroundCache = new Map();
  function around(id) {
    let list = aroundCache.get(id);
    if (list) return list;
    const s = viewer.sweep(id);
    list = s ? [...new Set([...s.visible, ...s.links])].filter((x) => x !== id && viewer.sweep(x)) : [];
    list.sort((a, b) => planDist(s.p, viewer.sweep(a).p) - planDist(s.p, viewer.sweep(b).p));
    aroundCache.set(id, list);
    return list;
  }
  // Every other sweep, by walking order from `id` (breadth first over the links).
  function spread(id) {
    const seen = new Set([id]), q = [id], out = [];
    while (q.length) {
      for (const y of viewer.sweep(q.shift()).links) if (!seen.has(y) && viewer.sweep(y)) { seen.add(y); q.push(y); out.push(y); }
    }
    for (const s of viewer.sweeps) if (!seen.has(s.id)) out.push(s.id);
    return out;
  }
  // The way from a to b: direct when b is in view of a, otherwise the shortest chain of links, with the
  // sweeps skipped that a later one in direct view makes unnecessary. null when there is no way.
  function routeTo(a, b) {
    if (a === b) return [a];
    if (around(a).includes(b)) return [a, b];
    const path = viewer.path(a, b);
    if (!path) return null;
    const out = [path[0]];
    for (let i = 0; i < path.length - 1;) {
      let j = path.length - 1;
      while (j > i + 1 && !around(path[i]).includes(path[j])) j--;
      out.push(path[j]);
      i = j;
    }
    return out;
  }
  // The sweep of `pool` that best continues from `base` along a heading (radians): well aligned and near.
  function toward(heading, base, cone, pool) {
    const s = viewer.sweep(base);
    let best = null, bestCost = Infinity;
    for (const id of pool) {
      const o = viewer.sweep(id);
      if (!o || id === base) continue;
      const a = Math.abs(angleDelta(heading, bearing(s.p, o.p)));
      if (a > cone) continue;
      const cost = a / cone + planDist(s.p, o.p) * 0.04;
      if (cost < bestCost) { bestCost = cost; best = id; }
    }
    return best;
  }
  // Where a click at a screen point leads: the ring under it; else the sweep in view nearest to the
  // surface point clicked, if it lies in that direction and not beyond the surface; else the nearest
  // linked sweep in that direction. During a move the choice is made from the sweep the hop ends on.
  function targetAt(p, touch) {
    const ring = ringAt(p.x, p.y, touch);
    if (ring) return ring;
    const r = viewer.ray(p.x, p.y);
    if (!r || Math.hypot(r.dir[0], r.dir[2]) < 0.2) return null;            // straight up or down: no direction
    const heading = Math.atan2(r.dir[0], -r.dir[2]);
    if (flight) {
      const base = flight.route[flight.i + 1];
      return toward(heading, base, LINK_CONE, around(base).filter((id) => id !== flight.route[flight.i]));
    }
    const here = viewer.sweep(cur), hit = viewer.pick(p.x, p.y);
    if (hit) {
      const reach = planDist(here.p, hit.point), margin = Math.max(2, reach * 0.25);
      let best = null, bestD = Infinity;
      for (const id of around(cur)) {
        const o = viewer.sweep(id), d = planDist(here.p, o.p);
        if (d > reach + margin || Math.abs(angleDelta(heading, bearing(here.p, o.p))) > VIEW_CONE) continue;
        const dp = planDist(o.p, hit.point);
        if (dp < bestD) { bestD = dp; best = id; }
      }
      if (best) return best;
    }
    return toward(heading, cur, LINK_CONE, here.links);
  }

  // ---- flights -------------------------------------------------------------------------------
  // A flight is a route [from, ..., to] of sweeps flown as one motion: the camera runs along the straight
  // segments between them with a speed that eases in at the start, eases out at the end, slows for corners
  // and never stops in between. One hop takes hopSeconds(distance) (0.55-1.1 s, constant acceleration and
  // braking = ease in-out); in a chain each hop cruises a little faster than the one before. Within a hop
  // the engine cross-fades the two panoramas over the middle of the way (smoothstep 0.2..0.8 of the
  // distance). A click during a flight changes the route after the hop under way.
  function measure(f) {
    f.pts = f.route.map((id) => viewer.sweep(id).p);
    f.cum = [0];
    for (let k = 1; k < f.pts.length; k++) f.cum.push(f.cum[k - 1] + Math.max(0.05, distance(f.pts[k - 1], f.pts[k])));
    const n = f.pts.length - 1;
    // share of the cruise speed allowed at each sweep passed: all on a straight run, little around a corner
    f.pass = f.pts.map((p, k) => {
      if (k === 0 || k === n) return 0;
      const a = bearing(f.pts[k - 1], p), b = bearing(p, f.pts[k + 1]);
      return clamp(0.5 + 0.5 * Math.cos(angleDelta(a, b)), 0.2, 1);
    });
  }
  function newFlight(route) {
    // shown: the last sweep of the route whose panorama was in the engine when the camera left it
    const f = { route, i: 0, s: 0, v: 0, passed: 0, single: route.length === 2, acc: ACC, started: false, clock: 0, blend: 0, e: 0, origin: route[0], shown: route[0], waiters: [], walked: -1, born: performance.now() };
    measure(f);
    if (f.single) { const d = f.cum[1], T = hopSeconds(d); f.acc = 4 * d / (T * T); }
    return f;
  }
  function loadAhead(f) {
    engine.setWanted(f.route.slice(f.i + 1, f.i + 4));
    for (const id of f.route.slice(f.i + 1, f.i + 3)) preload(id);
    const last = f.route[f.route.length - 1], up = climb(last)[0];
    if (up) blobOf(last, up).catch(() => {});          // the sharper level's file is there when the camera lands
  }
  function launch(f) {
    flight = f;
    plan++;                                            // the rest's loading plan is over
    late = null;
    leaveBehind(f.route[0], f.route[f.route.length - 1]);
    const first = f.route[1];
    engine.setSweepBlend(f.route[0], first, 0);        // declared before loading: neither is evicted now
    loadAhead(f);
    const go = () => {
      if (flight !== f || f.started) return;
      f.started = true;
      f.clock = performance.now();
      // time spent waiting comes off the hop (a little), so a click-to-rest stays within its bound
      if (f.single) { const d = f.cum[1], T = Math.max(hopSeconds(d) * 0.75, hopSeconds(d) - (performance.now() - f.born) / 1000); f.acc = 4 * d / (T * T); }
      viewer.emit('transition', { from: f.route[0], to: f.route[f.route.length - 1], route: f.route.slice(), t: 0, done: false });
    };
    const h = engine.hasPanorama(first);
    if (h && h.depth) go();
    else Promise.race([preload(first), sleep(WAIT_MS)]).then(go);     // never wait longer: move with what is there
    return new Promise((r) => f.waiters.push(r));
  }
  // A new destination for a flight under way: the hop being flown is finished, the rest is replaced.
  function retarget(f, id) {
    const base = f.route[f.i + 1];
    const tail = id === base ? [base] : routeTo(base, id);
    if (!tail) return null;
    const old = f.waiters;
    f.waiters = [];
    for (const r of old) r(false);
    f.route = f.route.slice(0, f.i + 2).concat(tail.slice(1));
    if (f.route.length > 2) { f.single = false; f.acc = Math.min(f.acc, ACC * 1.3); }
    measure(f);
    leaveBehind(null, f.route[f.route.length - 1]);
    loadAhead(f);
    return new Promise((r) => f.waiters.push(r));
  }
  // Held arrow / WASD keys walk on: the heading (relative to the view) of the key held, or null.
  const STEP = { arrowup: 0, w: 0, arrowdown: Math.PI, s: Math.PI, a: -Math.PI / 2, d: Math.PI / 2 };
  function heldStep() { for (const k in STEP) if (viewer.keys.has(k)) return STEP[k]; return null; }

  // One time step of a flight; returns the eye point. Lands (flight = null) at the end of the route.
  function fly(f, dt) {
    const n = f.route.length - 1, L = f.cum[n];
    if (f.started && !f.frozen) {
      const cruise = f.single ? Infinity : Math.min(CRUISE_MAX, CRUISE * Math.pow(CRUISE_UP, f.passed));
      const top = Math.min(CRUISE_MAX, cruise * CRUISE_UP);
      // The fastest speed at the end of this step from which braking at `acc` still reaches speed vj
      // after the distance R (exact for the step: v1^2 = vj^2 + 2 acc (R - (v0 + v1) dt / 2)); <= 0 = too late.
      const brake = (R, vj) => {
        const b = f.acc * dt, disc = b * b - 4 * (b * f.v - 2 * f.acc * R - vj * vj);
        return disc <= 0 ? -1 : (Math.sqrt(disc) - b) / 2;
      };
      let v = f.v > cruise ? Math.max(cruise, f.v - f.acc * dt) : Math.min(cruise, f.v + f.acc * dt);
      const end = brake(L - f.s, 0);                                           // stop at the end of the route
      if (end <= 0) { f.s = L; v = 0; } else v = Math.min(v, end);
      for (let j = f.i + 1; j < n && v > 0; j++) {                             // ... and take the corners ahead
        const vj = top * f.pass[j], c = brake(f.cum[j] - f.s, vj);
        v = Math.min(v, c > 0 ? c : Math.max(vj, f.v - f.acc * dt));
      }
      f.s = clamp(f.s + (f.v + v) / 2 * dt, 0, L);
      f.v = v;
      while (f.i < n - 1 && f.s >= f.cum[f.i + 1]) {                           // passed a sweep without stopping
        f.i++;
        f.passed++;
        cur = f.route[f.i];
        loadAhead(f);
      }
    }
    const a = f.cum[f.i], b = f.cum[f.i + 1];
    f.e = clamp((f.s - a) / (b - a), 0, 1);
    f.blend = smooth((f.e - 0.2) / 0.6);
    // a step key still held when the last hop is well under way: walk on without stopping
    if (f.started && !f.frozen && f.i === n - 1 && f.e > 0.55 && f.walked !== f.i) {
      f.walked = f.i;
      const step = heldStep();
      if (step !== null) {
        const base = f.route[n], id = toward(yaw + step, base, KEY_CONE, around(base).filter((x) => x !== f.route[n - 1] || Math.abs(step) > 2));
        if (id) retarget(f, id);
      }
    }
    if (f.started && !f.frozen && L - f.s < 0.004) return land(f);
    // A sweep passed before its panorama arrived (a slow line) is not shown as the bare model: the last
    // one that was there stays projected until the next one is in.
    const from = f.route[f.i];
    if (engine.hasPanorama(from)) f.shown = from;
    engine.setSweepBlend(f.shown, f.route[f.i + 1], f.blend);
    const p = f.pts[f.i], q = f.pts[f.i + 1];
    return [lerp(p[0], q[0], f.e), lerp(p[1], q[1], f.e), lerp(p[2], q[2], f.e)];
  }
  function land(f) {
    const n = f.route.length - 1, from = f.route[n - 1], prev = f.origin;
    flight = null;
    cur = f.route[n];
    engine.setWanted(hot ? [hot] : []);
    late = engine.hasPanorama(cur) ? null : { from: engine.hasPanorama(from) ? from : f.shown, t: 0 };
    showRest();
    viewer.emit('transition', { from, to: cur, route: f.route.slice(), t: 1, done: true, cancelled: false });
    arrived(prev);
    for (const r of f.waiters) r(true);
    return viewer.sweep(cur).p;
  }
  // What the engine shows while standing: the sweep's panorama; if that has not arrived yet, the one the
  // camera came from stays (projected on the model) and the new one fades in when it is there.
  function showRest(dt = 0) {
    if (late && !engine.hasPanorama(late.from)) late = null;
    if (late && engine.hasPanorama(cur)) { late.t += dt / 0.3; if (late.t >= 1) late = null; }
    if (late) engine.setSweepBlend(late.from, cur, clamp(late.t, 0, 0.998));
    else engine.setSweepBlend(cur);
  }
  function arrived(from) {
    restAt = performance.now();
    viewer.emit('sweep', { id: cur, from, sweep: viewer.sweep(cur), room: viewer.roomOf(cur) });
    settle();
  }
  // Ends whatever move is under way without arriving anywhere new.
  function halt() {
    if (flight) {
      const f = flight;
      if (f.started && f.e >= 0.5) cur = f.route[f.i + 1];                     // end on the nearer sweep of the hop
      flight = null;
      engine.setWanted([]);
      if (f.started) viewer.emit('transition', { from: f.route[f.i], to: cur, route: f.route.slice(), t: 1, done: true, cancelled: true });
      for (const r of f.waiters) r(false);
    }
    if (veil) { const w = veil.waiters; endVeil(); for (const r of w) r(false); }
    late = null;
  }
  // Instant change of sweep (the look is kept unless the options say otherwise).
  function cut(id, o = {}) {
    const from = cur, s = viewer.sweep(id);
    if (from !== id) leaveBehind(from, id);
    cur = id;
    if (o.reset) { yaw = s.look.yaw; pitch = clampPitch(s.look.pitch); }
    if (finite(o.yaw)) yaw = o.yaw;
    if (finite(o.pitch)) pitch = clampPitch(o.pitch);
    if (finite(o.fov)) fov = fovGoal = clamp(o.fov * DEG, FOV_MIN, FOV_MAX);
    vel = [0, 0];
    turnLeft = turnVel = tiltLeft = 0;
    late = null;
    drawn.length = 0;
    if (active) { engine.setSweepBlend(cur); holdFor(cur); arrived(from); }
  }
  // A cut shows a sweep at once, but its panorama may still be on its way (a few frames when the file
  // is there, longer on a slow line). Until it is in, the picture on the canvas stays as it is: the
  // view left behind, not the bare model.
  // (Before the 3D model is in there is no model to fall back on: the picture waits for the panorama.)
  function holdFor(id) { hold = engine.hasPanorama(id) ? 0 : viewer.modelReady ? performance.now() + HOLD_MS : Infinity; }
  // Resolves true once a panorama of the sweep is in the engine (or after 4 s, whatever is there).
  function onScreen(id) {
    return Promise.race([ensureSome(id, true), sleep(4000)]).then(() => true);
  }
  // A far jump (and every move when the visitor has asked for less motion, or while the 3D model is not
  // in yet): a dissolve. The picture stays as it is until the destination's panorama is in the engine (a
  // moment on a slow line: the viewer's 'busy' mark shows), then the camera cuts and the old picture
  // fades out over the new one (viewer.crossfade).
  function fadeTo(id, o = {}) {
    if (veil) {                                        // a jump under way gets the new destination
      const w = veil.waiters;
      veil.waiters = [];
      for (const r of w) r(false);
    } else {
      halt();
      veil = { waiters: [] };
    }
    const v = veil;
    Object.assign(v, { id, o, phase: 0, t: 0, ready: false });
    plan++;
    leaveBehind(null, id);
    const there = !!engine.hasPanorama(id);
    if (!there) viewer.emit('busy', { active: true });
    ensureSome(id, true).catch(() => false).then(() => { if (veil === v && v.id === id) v.ready = true; });     // in, or not to be had
    return new Promise((r) => v.waiters.push(r));
  }
  function endVeil() {
    veil = null;
    viewer.emit('busy', { active: false });
  }
  function stepVeil(dt) {
    const v = veil;
    v.t += dt;
    if (v.phase === 0) {
      if (!engine.hasPanorama(v.id) && !v.ready && v.t < JUMP_WAIT) return;
      viewer.emit('busy', { active: false });
      v.phase = 2;
      v.t = 0;
      if (drawn.length) viewer.crossfade();
      if (v.id !== cur || v.o.reset || finite(v.o.yaw)) cut(v.id, v.o);
    } else if (v.t >= DISSOLVE) {
      veil = null;
      for (const r of v.waiters) r(true);
    }
  }
  // A smooth turn to a direction (the short way round).
  function turnTo(y, p) {
    if (finite(y)) { turnLeft = angleDelta(yaw, y); vel[0] = 0; }
    if (finite(p)) { tiltLeft = clampPitch(p) - pitch; vel[1] = 0; }
  }

  function goTo(id, o = {}) {
    if (!viewer.sweep(id) || !active) return Promise.resolve(false);
    viewer.wake();
    if (o.instant && id === cur && !flight && !veil) {         // already there: only the direction can change
      const s = viewer.sweep(id);
      setLook(finite(o.yaw) ? o.yaw : o.reset ? s.look.yaw : undefined, finite(o.pitch) ? o.pitch : o.reset ? s.look.pitch : undefined);
      return Promise.resolve(true);
    }
    if (o.instant) return document.visibilityState === 'visible' && drawn.length ? fadeTo(id, o) : jumpTo(id, o);
    if (veil) return fadeTo(id, o);
    // on the way (or standing there already) the view turns to the direction asked for, if any
    const s = viewer.sweep(id), toYaw = finite(o.yaw) ? o.yaw : o.reset ? s.look.yaw : undefined, toPitch = finite(o.pitch) ? o.pitch : o.reset ? s.look.pitch : undefined;
    if (flight) {
      const last = flight.route[flight.route.length - 1];
      if (id === last) { turnTo(toYaw, toPitch); return new Promise((r) => flight.waiters.push(r)); }
      const on = retarget(flight, id);
      if (on) turnTo(toYaw, toPitch);
      return on || Promise.resolve(false);
    }
    if (id === cur) { turnTo(toYaw, toPitch); return Promise.resolve(true); }
    const route = routeTo(cur, id);
    // (a glide projects the panoramas on the model: without the model, or without motion, a dissolve)
    if (!route || route.length - 1 > FAR_HOPS || calm.matches || !viewer.modelReady) return fadeTo(id, o);
    turnTo(toYaw, toPitch);
    return launch(newFlight(route));
  }
  function jumpTo(id, o = {}) {
    if (!viewer.sweep(id)) return Promise.resolve(false);
    viewer.wake();
    halt();
    plan++;
    cut(id, o);
    return active ? onScreen(id) : Promise.resolve(true);
  }
  function setLook(y, p) {
    viewer.wake();
    if (finite(y)) yaw = y;
    if (finite(p)) pitch = clampPitch(p);
    vel = [0, 0];
    turnLeft = turnVel = tiltLeft = 0;
  }

  // ---- overlay: floor rings, cursor reticle, veil ---------------------------------------------
  // All of it lives in one group of engine.overlay (feet), so the engine's depth test hides a ring behind
  // a wall or a sofa: against the sweep's depth cube at rest, against the model during a move.
  const group = new THREE.Group();
  group.name = 'inside';
  group.visible = false;
  engine.overlay.add(group);
  const ringGeo = engine.ring(RING * RING_BAND, RING, 72), haloGeo = engine.ring(RING * 0.5, RING * 1.3, 72);
  const rings = new Map();                             // id -> {mesh, halo, alpha, goal, heat, el, on}
  for (const s of viewer.sweeps) {
    const y = (s.floor || 0) + RING_LIFT;
    const halo = new THREE.Mesh(haloGeo, engine.overlayMaterial({ color: 0x000000, opacity: 0, soft: [0.5, 0.5] }));
    halo.position.set(s.p[0], y - 0.01, s.p[2]);
    halo.renderOrder = 1;
    const mesh = new THREE.Mesh(ringGeo, engine.overlayMaterial({ color: 0xffffff, opacity: 0, soft: [0.3, 0.3] }));
    mesh.position.set(s.p[0], y, s.p[2]);
    mesh.renderOrder = 2;
    halo.visible = mesh.visible = false;
    group.add(halo, mesh);
    // the keyboard way to a ring: a focusable button that follows it (drawn by the 3D ring itself)
    const el = document.createElement('button');
    el.className = 'sweep-marker';
    el.dataset.sweep = s.id;
    el.dataset.testid = 'marker-' + s.id;
    el.setAttribute('aria-label', 'Go to ' + s.label);
    el.hidden = true;
    el.addEventListener('click', () => goTo(s.id));
    el.addEventListener('focus', () => { focused = s.id; preload(s.id); });
    el.addEventListener('blur', () => { if (focused === s.id) focused = null; });
    if (layer) layer.appendChild(el);
    rings.set(s.id, { mesh, halo, alpha: 0, goal: 0, heat: 0, far: 0, size: 1, el, on: false, c: [s.p[0], y, s.p[2]] });
  }
  const reticle = viewer.cursorRing();
  group.add(reticle.object);
  let retHit = null, retSize = 1;                      // what the cursor ring lies on; its radius in feet

  // Where a ring is on screen (CSS px): centre, half axes of its ellipse, distance; null when off screen.
  function ringBox(id) {
    const r = rings.get(id), v = viewer.view;
    if (!r || !v || !v.fovY) return null;
    const p = viewer.project(r.c, 1.0);
    if (!p) return null;
    const d = Math.max(0.5, distance(v.eye, r.c));
    const rx = RING * r.size * (viewer.size.cssH / 2 / Math.tan(v.fovY / 2)) / d;
    return { x: p.x, y: p.y, rx, ry: rx * clamp((v.eye[1] - r.c[1]) / d, 0.08, 1), d };
  }
  // How much of a ring the things in front of it leave visible, 0..1 (eight points on it against the
  // resting sweep's depth; unknown counts as visible).
  function ringSeen(id) {
    const r = rings.get(id), v = viewer.view;
    if (!r || !v || flight || engine.resting !== cur) return 1;
    let n = 0, seen = 0;
    for (let k = 0; k < 8; k++) {
      const a = k * Math.PI / 4, rad = RING * r.size * 0.87, pt = [r.c[0] + Math.cos(a) * rad, r.c[1], r.c[2] + Math.sin(a) * rad];
      const q = engine.project(pt);
      if (q.behind || Math.abs(q.x) > 1 || Math.abs(q.y) > 1) continue;
      n++;
      const hit = engine.pick(q.x, q.y);
      if (!hit || distance(v.eye, pt) <= hit.distance * 1.035 + 0.3) seen++;
    }
    return n ? seen / n : 0;
  }
  // The ring under a screen point: inside its ellipse (at least a fingertip wide) and not hidden.
  function ringAt(x, y, touch) {
    const minX = touch ? 26 : 15, minY = touch ? 22 : 11;
    let best = null, bestD = Infinity;
    for (const [id, r] of rings) {
      if (r.goal < 0.05) continue;
      const b = ringBox(id);
      if (!b) continue;
      if (((x - b.x) / Math.max(b.rx, minX)) ** 2 + ((y - b.y) / Math.max(b.ry, minY)) ** 2 > 1) continue;
      const d = Math.hypot(x - b.x, y - b.y);
      if (d >= bestD || ringSeen(id) < 0.25) continue;
      bestD = d;
      best = id;
    }
    return best;
  }
  function ringPoint(id) {
    const r = rings.get(id);
    if (!r || !active || r.goal < 0.05) return null;
    const b = ringBox(id);
    return b && ringAt(b.x, b.y, false) === id ? { x: b.x, y: b.y } : null;
  }
  // Ring brightness: the sweeps around the one the camera is on (during a hop: around both ends, weighted
  // like the panoramas), fading with distance, none under the feet. At rest a ring is a soft translucent
  // band that sits back in the floor; the one under the cursor (or focused, or being walked to) is full
  // white, so the cursor ring stays the one crisp mark of the picture. A ring is 1.5 ft across: 25 ft
  // away its band is a pixel or two thick. So far rings fade only to RING_FAR[0], grow by up to
  // RING_FAR[1] and get a crisper edge; they still read as rings down a long hall.
  const weights = new Map();
  function stepRings(eye, dt) {
    weights.clear();
    let target = null;
    if (active && flight) {
      const f = flight, a = f.route[f.i], b = f.route[f.i + 1];
      for (const id of around(a)) weights.set(id, 1 - f.blend);
      for (const id of around(b)) weights.set(id, Math.max(weights.get(id) || 0, f.blend));
      target = f.route[f.route.length - 1];
      weights.set(target, 1);
    } else if (active) for (const id of around(cur)) weights.set(id, 1);
    const k = 1 - Math.exp(-dt * 14);
    let changed = false;
    for (const [id, r] of rings) {
      const w = weights.get(id) || 0, d = w ? distance(eye, r.c) : 0;
      const warm = id === hot || id === focused || id === target ? 1 : 0;
      const far = w ? smooth((d - RING_NEAR) / (RING_FAR[2] - RING_NEAR)) : r.far;
      r.goal = w * smooth((planDist(eye, r.c) - 0.8) / 1.0) * lerp(lerp(RING_ALPHA, RING_FAR[0], far), 1, warm);
      const heat = r.heat + (warm - r.heat) * k, alpha = r.alpha + (r.goal - r.alpha) * k;
      const a = Math.abs(alpha - r.goal) < 0.004 ? r.goal : alpha, h = Math.abs(heat - warm) < 0.004 ? warm : heat;
      if (a === r.alpha && h === r.heat && far === r.far) continue;
      r.alpha = a;
      r.heat = h;
      r.far = far;
      r.size = (1 + RING_FAR[1] * far) * (1 + 0.16 * h);
      changed = true;
      r.mesh.visible = r.halo.visible = a > 0.004;
      r.mesh.material.opacity = a;
      r.halo.material.opacity = a * RING_HALO;
      r.mesh.material.userData.soft.value.setScalar(lerp(0.3, 0.14, far));
      r.mesh.scale.setScalar(r.size);
      r.halo.scale.setScalar(r.size);
    }
    return changed;
  }
  // The cursor ring: flat on the surface under the mouse, the same size on screen wherever it lies.
  function placeReticle(hit) {
    const v = viewer.view, on = !!(hit && v && v.fovY);
    if (on || reticle.shown) engine.invalidate();
    if (on) {
      const depth = Math.max(0.2, util.dot(norm(util.sub(v.aim, v.eye)), util.sub(hit.point, v.eye)));
      retSize = depth * Math.tan(v.fovY / 2) * RETICLE_PX / (viewer.size.cssH / 2);
      reticle.place(hit.point, hit.normal, retSize, 0.02 + retSize * 0.04);
    } else reticle.hide();
    retHit = on ? hit : null;
  }
  // What the mouse is over: a ring (it lights up), else a surface (the reticle lies on it).
  // The picture on the canvas is this view's own (not the one a cut still holds while its panorama
  // loads): only then do screen points mean anything here.
  const onView = () => !hold && drawn.length > 0;
  function hover(emit) {
    const p = pointer;
    let ring = null, hit = null;
    hoverRetry = 0;
    if (p && active && overlayOn && viewer.pointers.size === 0 && !veil && onView()) {
      ring = ringAt(p.x, p.y, false);
      if (!ring && !flight) {
        hit = viewer.pick(p.x, p.y);
        if (hit && hit.distance > 120) hit = null;
        if (!hit) hoverRetry = 90;                     // the depth copy of a fresh sweep arrives a few frames late
      }
    }
    if (ring !== hot) {
      hot = ring;
      canvas.style.cursor = ring ? 'pointer' : '';
      // the visitor points at it: its panorama and depth cube are fetched now, ahead of the click
      if (ring) preload(ring);
      if (!flight) engine.setWanted(ring ? [ring] : []);
    }
    placeReticle(hit);
    if (emit) viewer.emit('hover', p ? { x: p.x, y: p.y, sweep: ring, point: hit ? hit.point.slice() : null } : null);
  }
  // The buttons that shadow the rings (keyboard, tests) follow once the view stands still.
  function placeMarkers() {
    markersDue = false;
    for (const [id, r] of rings) {
      const p = active && !flight && onView() ? ringPoint(id) : null;
      if (!!p !== r.on) {
        r.on = !!p;
        // a ring that goes (the visitor moved onto it by keyboard) hands the focus to the view
        if (!p && document.activeElement === r.el) canvas.focus({ preventScroll: true });
        r.el.hidden = !p;
      }
      if (!p) continue;
      const b = ringBox(id), w = Math.max(b.rx, 15) * 2, h = Math.max(b.ry, 11) * 2;
      r.el.style.transform = 'translate(' + (p.x - w / 2).toFixed(1) + 'px,' + (p.y - h / 2).toFixed(1) + 'px)';
      r.el.style.width = w.toFixed(1) + 'px';
      r.el.style.height = h.toFixed(1) + 'px';
    }
  }

  // ---- zoom ----------------------------------------------------------------------------------
  function zoomBy(factor) { fovGoal = clamp(fovGoal * factor, FOV_MIN, FOV_MAX); }

  // ---- controller ----------------------------------------------------------------------------
  // The first panorama's file comes while the model loads. And while another view is on, the panorama of
  // the sweep the visitor comes back to is kept in the engine, so "Enter the house" and the Inside button
  // open on it at once.
  if (cur && panos.has(cur) && quick(cur)) blobOf(cur, quick(cur)).catch(() => {});
  // While another view is on (also behind the landing page): the files the way in will ask for first,
  // the next level of that sweep and the 2k of the sweeps one step from it.
  viewer.on('mode', (e) => {
    if (e.mode === 'inside' || !cur) return;
    const id = cur, up = climb(id)[0];
    ensureSome(id, true).then(() => {
      if (active || cur !== id || frugal()) return;
      if (up) blobOf(id, up, true).catch(() => {});
      for (const n of viewer.sweep(id).links) fileOf(n);
    });
  });
  // The 3D model has arrived while the visitor already stood inside: the rings come up, the sweeps
  // around get their depth cubes, and moves glide from now on.
  viewer.on('ready', () => {
    if (!active) return;
    group.visible = overlayOn;
    if (hold === Infinity) hold = performance.now() + HOLD_MS;
    engine.invalidate();
    if (!flight && !veil) settle();
  });

  return {
    early: true,
    goTo, jumpTo, setLook, ringPoint, preload,
    enter(from, o = {}) {
      const again = active && from === 'inside';
      const named = !!(o.sweep && viewer.sweep(o.sweep)), id = named ? o.sweep : cur;
      if (again) {
        if (finite(o.fov)) fovGoal = clamp(o.fov * DEG, FOV_MIN, FOV_MAX);
        // no sweep named (the Inside button pressed again): a move under way goes on as it is
        if (!named || (id === cur && !flight && !veil && !o.instant)) { turnTo(o.yaw, o.pitch); return Promise.resolve(true); }
        return goTo(id, o);
      }
      active = true;
      halt();
      // from another view the picture changes with a dissolve; a fly-in (landed) has brought the camera here itself
      if (from && !o.landed) viewer.crossfade();
      viewer.setEngineMode('inside');
      viewer.setBackground(null);
      group.visible = overlayOn && viewer.modelReady;  // rings and the cursor ring lie on the model's surfaces
      const s = viewer.sweep(id);
      cur = id;
      // A named sweep opens on its own direction unless one is given. Without a name (the Inside button)
      // the visitor comes back to the sweep and the view they left.
      if (finite(o.yaw)) yaw = o.yaw; else if (named || o.reset) yaw = s.look.yaw;
      pitch = clampPitch(finite(o.pitch) ? o.pitch : named || o.reset ? s.look.pitch : pitch);
      if (finite(o.fov)) fov = fovGoal = clamp(o.fov * DEG, FOV_MIN, FOV_MAX);
      vel = [0, 0];
      turnLeft = turnVel = tiltLeft = 0;
      drawn.length = 0;
      clock = 0;
      engine.setSweepBlend(cur);
      engine.invalidate();
      holdFor(cur);
      arrived(null);
      return onScreen(cur);
    },
    leave() {
      halt();                                          // mid-move: the nearer sweep of the hop counts
      active = false;
      plan++;
      hold = 0;
      leaveBehind(cur, null);
      pointer = null;
      hot = null;
      canvas.style.cursor = '';
      reticle.hide();
      retHit = null;
      group.visible = false;
      for (const r of rings.values()) if (r.on) { r.on = false; r.el.hidden = true; }
      engine.setSweepBlend(cur);                       // the fly-out of the dollhouse starts from this picture
      engine.setWanted([]);
      engine.invalidate();
    },
    frame(dt, size, now) {
      const s0 = viewer.sweep(cur);
      if (!s0) return false;
      // flights run on the real clock (a slow frame must not stretch a hop), in steps of 1/60 s
      const real = clock ? clamp((now - clock) / 1000, 0, 0.25) : dt;
      clock = now;

      // look: key turns, inertia, zoom
      let moving = !!flight || !!veil || viewer.pointers.size > 0;
      if (turnLeft || turnVel) {
        turnVel += (81 * turnLeft - 18 * turnVel) * dt;                        // critically damped (9 rad/s)
        const step = turnVel * dt;
        yaw += step;
        turnLeft -= step;
        if (Math.abs(turnLeft) < 0.0008 && Math.abs(turnVel) < 0.02) { yaw += turnLeft; turnLeft = turnVel = 0; }
        moving = true;
      }
      if (tiltLeft) {
        const step = Math.abs(tiltLeft) < 0.001 ? tiltLeft : tiltLeft * (1 - Math.exp(-dt * 7));
        pitch = clampPitch(pitch + step);
        tiltLeft -= step;
        moving = true;
      }
      if (viewer.pointers.size === 0 && (vel[0] || vel[1])) {
        yaw += vel[0] * dt;
        pitch = clampPitch(pitch + vel[1] * dt);
        const k = Math.exp(-dt * 6);
        vel = [vel[0] * k, vel[1] * k];
        if (Math.hypot(vel[0], vel[1]) < 0.02) vel = [0, 0];
        moving = true;
      }
      if (fov !== fovGoal) {
        fov += (fovGoal - fov) * (1 - Math.exp(-dt * 13));
        if (Math.abs(fov - fovGoal) < 0.0006) fov = fovGoal;
        moving = true;
      }
      const vfov = viewFov(size);
      if (moving) busyAt = now;

      // position
      let eye = s0.p;
      if (veil) stepVeil(real);
      if (flight) {
        // a flight runs on its own clock, from the moment it started (not from the frame before)
        const f = flight, span = f.started ? clamp((now - f.clock) / 1000, 0, 0.25) : 0;
        if (f.started) f.clock = Math.max(f.clock, now);
        eye = fly(f, Math.min(span, 1 / 60));
        for (let left = span - 1 / 60; flight === f && left > 1e-5; left -= 1 / 60) eye = fly(f, Math.min(left, 1 / 60));
        if (!flight) eye = viewer.sweep(cur).p;
      } else {
        showRest(real);
        eye = viewer.sweep(cur).p;
      }

      // overlay
      let touched = stepRings(eye, real);
      if (shake > 0) {
        shake = Math.max(0, shake - real);
        if (reticle.shown) reticle.object.scale.setScalar(retSize * (1 + 0.28 * Math.sin(shake * 42) * (shake / 0.32)));
        touched = true;
      }
      if (touched) engine.invalidate();

      if (hold) {                                      // (a move has its own fallback)
        if (engine.hasPanorama(cur) || flight || now > hold) hold = 0;
        else return false;
      }
      // draw only when the picture would differ
      const view = [eye[0], eye[1], eye[2], yaw, pitch, vfov, size.w, size.h];
      const same = drawn.length === view.length && view.every((x, i) => x === drawn[i]);
      if (same && !engine.dirty()) {
        if (hoverRetry > 0 && pointer) { const left = hoverRetry - 1; hover(false); if (hoverRetry) hoverRetry = left; }
        if (markersDue && now - viewAt > 150) placeMarkers();
        return false;
      }
      const d = lookDir(yaw, pitch);
      viewer.render({ eye, aim: [eye[0] + d[0], eye[1] + d[1], eye[2] + d[2]], fovY: vfov });
      if (!same) {
        drawn.length = 0;
        drawn.push(...view);
        viewAt = now;
        markersDue = true;
        if (pointer || reticle.shown || hot) hover(false);         // the view moved under a still mouse
      } else if (!markersDue && now - viewAt < 1500) markersDue = true;   // a level or the depth copy arrived
      return true;
    },
    onPointerDown() {
      vel = [0, 0];
      turnLeft = turnVel = tiltLeft = 0;
      fovGoal = fov;
      hover(false);                                    // the reticle hides while a button or finger is down
    },
    onDrag(p) {
      if (!p.dragged) return;
      const k = viewFov(viewer.size) / viewer.size.cssH;          // the picture follows the pointer
      const dy = -p.dx * k, dp = p.dy * k, now = performance.now(), dt = Math.max(0.004, (now - lastDrag) / 1000);
      yaw += dy;
      pitch = clampPitch(pitch + dp);
      vel = dt < 0.1 ? [lerp(vel[0], clamp(dy / dt, -6, 6), 0.5), lerp(vel[1], clamp(dp / dt, -6, 6), 0.5)] : [0, 0];
      lastDrag = now;
    },
    onPinch(scale) { fov = fovGoal = clamp(fov * scale, FOV_MIN, FOV_MAX); vel = [0, 0]; },
    onPointerUp(p, e) {
      if (performance.now() - lastDrag > 90) vel = [0, 0];        // the pointer had stopped: no coasting
      pointer = e && e.pointerType === 'mouse' && !p.cancelled ? { x: e.clientX, y: e.clientY } : null;
      if (viewer.pointers.size === 0) hover(false);
    },
    onClick(p, e) {
      const now = performance.now(), touch = !!(e && e.pointerType === 'touch');
      // A double click (or a burst of clicks on one spot) is one click: while the move the first one set
      // off is under way the others change nothing. So the camera is never sent back to where it came
      // from, and never on to the sweep beyond the one that was clicked. (Zooming is the wheel, a pinch
      // and the + / - keys: a double-click zoom would always start a move with its first click.)
      if (!p.synthetic && lastClick && lastClick.flight && lastClick.flight === flight && now - lastClick.t < DOUBLE_MS
        && Math.hypot(p.x - lastClick.x, p.y - lastClick.y) < DOUBLE_PX[touch ? 1 : 0]) {
        lastClick.t = now;
        return flight.route[flight.route.length - 1];
      }
      lastClick = { t: now, x: p.x, y: p.y, flight: null };
      // (while a cut still holds the picture of the view left behind, a point of it means nothing here)
      if (veil || !onView()) return false;
      const id = targetAt(p, touch);
      if (!id) { shake = 0.32; return false; }
      goTo(id);
      lastClick.flight = flight;
      return id;
    },
    onHover(p) {
      pointer = p ? { x: p.x, y: p.y } : null;
      hover(true);
    },
    onWheel(e) { zoomBy(Math.exp(util.wheelPixels(e) * 0.0011)); },
    onKey(e) {
      const k = e.key.toLowerCase();
      if (k === 'arrowleft' || k === 'arrowright') {
        const dir = k === 'arrowright' ? 1 : -1;
        if (turnLeft * dir < 0) turnLeft = 0;                     // the other way: from here
        if (!e.repeat || Math.abs(turnLeft) < 8 * DEG) turnLeft += dir * 45 * DEG;
        vel[0] = 0;
        return true;
      }
      if (k === '+' || k === '=') { zoomBy(1 / 1.22); return true; }
      if (k === '-' || k === '_') { zoomBy(1.22); return true; }
      if (!(k in STEP)) return false;
      if (veil || e.repeat) return true;               // a held key walks on from within the flight (fly)
      if (flight) {
        const base = flight.route[flight.i + 1];
        const id = toward(yaw + STEP[k], base, KEY_CONE, around(base));
        if (id) goTo(id);
        return true;
      }
      const id = toward(yaw + STEP[k], cur, KEY_CONE, around(cur));
      if (id) goTo(id);
      return true;
    },
    onResize() { drawn.length = 0; },
    // Waiting for something no event announces (the viewer's loop keeps its full rate meanwhile).
    busy() {
      return !!flight || !!veil || !!late || (hold > 0 && hold !== Infinity) || (hoverRetry > 0 && !!pointer) || markersDue || shake > 0
        || turnLeft !== 0 || turnVel !== 0 || tiltLeft !== 0 || vel[0] !== 0 || vel[1] !== 0 || fov !== fovGoal;
    },
    // ---- for tests and the other modes ----
    rings() {
      const out = [];
      for (const [id, r] of rings) {
        if (r.goal < 0.05) continue;
        const b = ringBox(id);
        if (b) out.push({ id, x: b.x, y: b.y, rx: b.rx, ry: b.ry, seen: ringSeen(id), alpha: r.alpha });
      }
      return out;
    },
    reticle() {
      if (!retHit || !reticle.shown) return null;
      const p = viewer.project(retHit.point, 1.2);
      return p ? { x: p.x, y: p.y, point: retHit.point.slice(), normal: retHit.normal.slice(), cls: retHit.cls, radius: retSize } : null;
    },
    setOverlay(on) {
      overlayOn = !!on;
      group.visible = active && overlayOn && viewer.modelReady;
      if (!overlayOn) { reticle.hide(); retHit = null; }
      engine.invalidate();
    },
    // Test hook: hold the camera at fraction e (0..1) of the hop a -> b, drawn exactly as a move draws it;
    // pose() lets go (the camera is back on the sweep it was on). Resolves when both panoramas are loaded.
    pose(a, b, e) {
      halt();
      plan++;
      if (!viewer.sweep(a) || !viewer.sweep(b)) { if (active) { showRest(); arrived(cur); } return Promise.resolve(true); }
      if (cur !== a) cut(a);
      const f = newFlight([a, b]);
      f.started = f.frozen = true;
      f.s = clamp(e, 0, 1) * f.cum[1];
      flight = f;
      engine.setSweepBlend(a, b, 0);
      return Promise.all([preload(a), preload(b)]).then(() => { engine.invalidate(); return true; });
    },
    view() {
      const size = viewer.size, eye = (viewer.view && active && viewer.view.eye) || viewer.sweep(cur).p, d = lookDir(yaw, pitch);
      return { eye: eye.slice(), aim: [eye[0] + d[0], eye[1] + d[1], eye[2] + d[2]], fovY: viewFov(size), yaw, pitch };
    },
    state() {
      const f = flight;
      return {
        sweep: cur, yaw, pitch, fov: fov / DEG, vfov: viewFov(viewer.size) / DEG,
        transition: f ? { from: f.route[f.i], to: f.route[f.i + 1], t: f.e, route: f.route.slice(), target: f.route[f.route.length - 1], started: f.started }
          : veil ? { from: cur, to: veil.id, t: veil.phase === 0 ? 0 : 1, fade: true, target: veil.id, loading: veil.phase === 0 } : null,
        pano: { id: cur, level: cur && !hold ? shownLevel(cur) : null },     // null until a frame of it has been drawn
        resting: !f && !veil && engine.resting === cur,
        hover: hot,
        reticle: reticle.shown,
      };
    },
  };
}
