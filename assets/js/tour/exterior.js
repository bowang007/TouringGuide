// EXTERIOR: the photoreal orbit around the house (ported from the single-file page, behaviour unchanged).
//
// Path-traced frames rendered from orbit positions around the house (tools/render/render_exterior.py,
// assets/exterior/manifest.json) are projected onto the model (engine.setPanorama with a frame matrix).
// On a frame the view is that render; orbiting blends the two nearest frames, and the camera settles on
// a frame when you let go (a short drag moves one frame that way). Zoom narrows the field of view from
// the frame position, so it stays exact. ?exterior=model shows the baked model alone.
// deps.background() -> true while the view only stands behind the landing page: it then loads the one
// frame it stands on at half size and nothing ahead, since the visitor has not chosen this view yet.
//
// Public (besides the controller interface, see viewer.js; enter() takes {view: 'front' | 'left' | 'rear' |
// 'right' | 'roof'}):
//   frameTo(id)     put the orbit on frame `id` of the manifest (tests)
//   state() -> {view, photo: null | {frames, on, at, weight, zoom, settling}, target, theta, phi, radius, garden}

export function createExterior(viewer, deps = {}) {
  const { engine, util, tour } = viewer;
  const { clamp, angleDelta, mul, perspective, lookAt, wheelPixels } = util;
  const background = deps.background || (() => false);
  const $ = (id) => document.getElementById(id);
  const MANIFEST_URL = deps.manifestUrl || 'assets/exterior/manifest.json';
  const PHOTO = viewer.query.get('exterior') !== 'model';
  const PRESETS = { front: ['o', 0], right: ['o', Math.PI / 2], rear: ['o', Math.PI], left: ['o', -Math.PI / 2], roof: ['h', -Math.PI / 4] };
  // labels, and the cameras used while the frames are not there (model only)
  const VIEWS = {
    front: { label: 'Front exterior', target: [19.71, 4.6, 27.8], theta: -0.10, phi: 0.20, radius: 84 },
    left: { label: 'Left side · bedroom addition', target: [19.71, 4.6, 27.3], theta: -Math.PI / 2, phi: 0.30, radius: 91 },
    rear: { label: 'Rear exterior · garden side', target: [19.71, 4.6, 20], theta: Math.PI, phi: 0.32, radius: 77 },
    right: { label: 'Right side · garage and kitchen', target: [19.71, 4.6, 27.3], theta: Math.PI / 2, phi: 0.30, radius: 91 },
    roof: { label: 'Roof overview', target: [19.71, 4.6, 30.5], theta: -0.48, phi: 1.03, radius: 105 },
  };

  let active = false, garden = true, viewId = 'front';
  let target = VIEWS.front.target.slice(), theta = VIEWS.front.theta, phi = VIEWS.front.phi, radius = VIEWS.front.radius;
  let EXT = null, list = [], key = '', since = 0, touch = 0, snap = null, gesture = null, zoom = 1;
  let sent = null;                                     // the projection the engine was last given (see project())
  let hold = 0;                                        // entering: nothing is drawn until the frame the view stands on is in (or this time)
  let drawn = [];                                      // the view of the last drawn frame
  const loads = new Map();

  const dir = (t, p) => [Math.sin(t) * Math.cos(p), Math.sin(p), Math.cos(t) * Math.cos(p)];
  const angle = (a, b) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return Math.acos(clamp((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / l, -1, 1)); };
  const eyeOf = () => [target[0] + radius * Math.sin(theta) * Math.cos(phi), target[1] + radius * Math.sin(phi), target[2] + radius * Math.cos(theta) * Math.cos(phi)];

  // the frames' manifest: the view stands on the model alone until it is in
  (PHOTO ? fetch(MANIFEST_URL, { cache: 'no-cache' }).then((r) => (r.ok ? r.json() : null)) : Promise.resolve(null)).then((m) => {
    if (!m || !Array.isArray(m.frames) || !m.frames.length || !Array.isArray(m.target)) return;
    m.vfov = 2 * Math.atan(Math.tan(m.hfov * Math.PI / 360) / m.aspect);
    m.byId = {};
    for (const f of m.frames) {
      f.dir = dir(f.theta, f.phi);
      f.eye = m.target.map((v, i) => v + f.radius * f.dir[i]);
      f.matrix = Array.from(mul(perspective(m.vfov, m.aspect), lookAt(f.eye, m.target)));
      m.byId[f.id] = f;
    }
    EXT = m;
    if (active && VIEWS[viewId] && garden) applyPreset(viewId);
    viewer.wake();
  }).catch(() => {});

  const photoOn = () => active && !!EXT && garden;
  function orbitFov(w, h) {
    if (!photoOn()) return Math.PI * 0.255;
    const a = w / Math.max(1, h), cap = Math.min(EXT.vfov * 0.96, 2 * Math.atan(Math.tan(EXT.hfov * Math.PI / 360 * 0.96) / a));
    const base = Math.min(cap, Math.PI * 0.255 * (a < 1 ? Math.pow(1 / a, 0.6) : 1));
    return 2 * Math.atan(Math.tan(base / 2) * zoom);
  }
  function url(f, full) {
    const u = new URL(full ? f.full : f.half, new URL(MANIFEST_URL, location.href));
    if (EXT.version) u.searchParams.set('v', EXT.version);
    return u.href;
  }
  const nearest = (v) => EXT.frames.reduce((a, b) => (angle(v, a.dir) <= angle(v, b.dir) ? a : b));
  function step(f, k) { const r = EXT.frames.filter((x) => x.ring === f.ring).sort((a, b) => a.theta - b.theta), i = r.indexOf(f); return r[(i + k + r.length) % r.length]; }
  function other(f) {
    const o = EXT.frames.filter((x) => x.ring !== f.ring);
    return o.length ? o.reduce((a, b) => (Math.abs(angleDelta(a.theta, f.theta)) <= Math.abs(angleDelta(b.theta, f.theta)) ? a : b)) : null;
  }
  function presetFrame(id) {
    const p = PRESETS[id];
    if (!EXT || !p) return null;
    const r = EXT.frames.filter((f) => f.ring === p[0]);
    return r.length ? r.reduce((a, b) => (Math.abs(angleDelta(a.theta, p[1])) <= Math.abs(angleDelta(b.theta, p[1])) ? a : b)) : null;
  }
  function applyPreset(id) {
    const f = presetFrame(id);
    if (!f) return false;
    target = EXT.target.slice(); theta = f.theta; phi = f.phi; radius = f.radius; zoom = 1; snap = null; gesture = null;
    return true;
  }
  function weights() {
    const v = dir(theta, phi), near = EXT.frames.map((f) => ({ f, a: angle(v, f.dir) })).sort((x, y) => x.a - y.a).slice(0, 3);
    if (near[0].a < 0.003) return [{ id: near[0].f.id, weight: 1 }];
    const cut = near.length > 2 ? 1 / (near[2].a * near[2].a) : 0;
    const ws = near.slice(0, 2).map((x) => ({ id: x.f.id, weight: Math.max(0, 1 / (x.a * x.a) - cut) }));
    const sum = ws.reduce((s, x) => s + x.weight, 0) || 1;
    return ws.map((x) => ({ id: x.id, weight: x.weight / sum })).filter((x) => x.weight > 0.001);
  }
  function ensure(id, full) {
    const f = EXT.byId[id];
    if (!f) return;
    full = !!full && f.width <= viewer.caps.maxTextureSize && (navigator.deviceMemory || 8) > 2;
    const have = engine.hasPanorama(id);
    if (have && (have.full || !full)) return;
    const u = url(f, full), k = id + '|' + u, busy = loads.get(k);
    if (busy === true || (busy && performance.now() < busy)) return;
    loads.set(k, true);
    util.fetchBlob(u).then(util.decodeImage).then((img) => {
      loads.delete(k);
      // (the frame a held view waits for comes in at full strength, not faded in over the bare model)
      if (viewer.engineState === 'ready') engine.setPanorama(id, img, f.eye, 0, full, !!hold, { matrix: f.matrix });
      else if (img.close) img.close();
    }, (err) => {
      console.warn('Exterior frame ' + id + ' is unavailable.', err);
      loads.set(k, performance.now() + 15000);
    });
  }
  function go(f, now) {
    if (!f) return;
    const a = angle(dir(theta, phi), f.dir);
    snap = { f, t0: theta, t1: theta + angleDelta(theta, f.theta), p0: phi, p1: f.phi, r0: radius, r1: f.radius, g0: target.slice(), start: now, dur: clamp(260 + a * 1500, 260, 1100) };
  }
  function landed(f) {
    const id = Object.keys(PRESETS).find((k) => presetFrame(k) === f);
    if (id && id !== viewId) { viewId = id; syncButtons(); viewer.emit('place', { label: VIEWS[id].label }); }
  }
  function settle(now) {
    if (viewer.pointers.size) { snap = null; return; }
    if (snap) {
      const s = snap, t = clamp((now - s.start) / s.dur, 0, 1), e = t * t * (3 - 2 * t);
      theta = s.t0 + (s.t1 - s.t0) * e; phi = s.p0 + (s.p1 - s.p0) * e; radius = s.r0 + (s.r1 - s.r0) * e;
      target = s.g0.map((v, i) => v + (EXT.target[i] - v) * e);
      if (t >= 1) { theta = s.f.theta; phi = s.f.phi; radius = s.f.radius; target = EXT.target.slice(); snap = null; landed(s.f); }
      return;
    }
    if (now - touch < 320) return;
    let v = dir(theta, phi);
    const g = gesture;
    gesture = null;
    if (g) {
      // a short drag moves exactly one frame that way
      const m = angle(v, g.v), f0 = nearest(g.v), sp = angle(f0.dir, step(f0, 1).dir);
      if (m > 0.035 && m < sp * 0.5) {
        const k = sp * 1.03 / m;
        v = v.map((x, i) => g.v[i] + (x - g.v[i]) * k);
        const l = Math.hypot(v[0], v[1], v[2]);
        v = v.map((x) => x / l);
      }
    }
    const f = nearest(v);
    if (angle(dir(theta, phi), f.dir) < 1e-5 && Math.abs(radius - f.radius) < 1e-4 && target.every((x, i) => Math.abs(x - EXT.target[i]) < 1e-4)) return;
    go(f, now);
  }
  // Hands the engine its projection targets only when they change: every call makes the engine redraw,
  // and a view that stands still should draw nothing.
  function project(targets, ahead) {
    const sig = targets ? targets.map((x) => x.id + ':' + x.weight.toFixed(4)).join(' ') + '|' + ahead.join(' ') : '';
    if (sig === sent) return;
    sent = sig;
    engine.setProjection(targets, ahead);
  }
  function photo(now) {
    if (!photoOn()) { project(null); key = ''; snap = null; return; }
    settle(now);
    const k = theta.toFixed(4) + ',' + phi.toFixed(4);
    if (k !== key) { key = k; list = weights(); since = now; }
    const top = list[0], rest = !!top && top.weight > 0.98 && !snap && !viewer.pointers.size, settled = rest && now - since > 300;
    const quiet = background();
    for (const x of list) { const f = EXT.byId[x.id]; ensure(x.id, !quiet && rest && x === top && (settled || util.blobCached(url(f, true)))); }
    let ahead = [];
    if (top && !quiet) { const f = EXT.byId[top.id]; ahead = [step(f, 1), step(f, -1)].filter((n) => n && !list.some((x) => x.id === n.id)).map((n) => n.id); }
    for (const id of ahead) ensure(id, false);
    project(list, ahead);
  }

  // ---- views and the control panel -----------------------------------------------------------
  function syncButtons() {
    document.querySelectorAll('[data-exterior]').forEach((b) => {
      const selected = b.dataset.exterior === viewId;
      b.classList.toggle('active', selected);
      b.setAttribute('aria-pressed', String(selected));
    });
    const g = $('exteriorGarden');
    if (g) { g.textContent = garden ? 'Hide garden' : 'Show garden'; g.setAttribute('aria-pressed', String(garden)); }
  }
  function setView(id = 'front') {
    const preset = VIEWS[id];
    if (!preset) return false;
    viewId = id;
    target = preset.target.slice(); theta = preset.theta; phi = preset.phi;
    radius = preset.radius * (innerWidth < 650 ? 1.7 : innerWidth / innerHeight < 1 ? 1.2 : 1);
    if (PHOTO && garden) applyPreset(id);
    syncButtons();
    viewer.wake();
    viewer.emit('place', { label: preset.label });
    return true;
  }
  function free() {
    if (!active || viewId === 'free') return;
    viewId = 'free';
    syncButtons();
  }
  function frameTo(id) {
    const f = EXT && EXT.byId[id];
    if (!f) return false;
    target = EXT.target.slice(); theta = f.theta; phi = f.phi; radius = f.radius; snap = null; gesture = null;
    viewer.wake();
    return true;
  }
  const show = (id) => (active ? setView(id) : viewer.setMode('exterior', { view: id }));
  document.querySelectorAll('[data-exterior]').forEach((b) => b.addEventListener('click', () => show(b.dataset.exterior)));
  if ($('exteriorEnter')) $('exteriorEnter').addEventListener('click', () => viewer.goTo(tour.start));
  if ($('exteriorPhoto')) $('exteriorPhoto').addEventListener('click', () => deps.onFrontImage && deps.onFrontImage());
  if ($('exteriorGarden')) $('exteriorGarden').addEventListener('click', () => {
    garden = !garden;
    syncButtons();
    viewer.wake();
    if (active) engine.applyVisibility({ garden });
  });

  return {
    frameTo,
    enter(from, o = {}) {
      active = true;
      if (from && from !== 'exterior') viewer.crossfade();       // the view left behind dissolves into this one
      viewer.setEngineMode('exterior');
      viewer.setBackground(null);
      engine.applyVisibility({ garden });
      if (engine.setAdaptation) engine.setAdaptation(null, null);
      setView(VIEWS[o.view] ? o.view : 'front');
      if (o.frame) frameTo(o.frame);
      sent = null;
      drawn = [];
      // The rendered frame may still be loading (the first visit, or after the inside view took its
      // place on the GPU). Until it is in, the picture on the canvas stays: the view left behind or the
      // loading screen, not the bare model.
      hold = PHOTO && garden ? performance.now() + 1500 : 0;
    },
    leave() {
      active = false;
      snap = null; gesture = null; key = '';
      sent = null;
      engine.setProjection(null);
      engine.applyVisibility({ garden: true });        // the other modes always show the grounds
    },
    frame(dt, size, now) {
      photo(now);                                      // may move the orbit (settling on a frame)
      if (hold) {
        if (!garden || now > hold || (list[0] && engine.hasPanorama(list[0].id))) hold = 0;
        else return false;
      }
      const view = { eye: eyeOf(), aim: target.slice(), fovY: orbitFov(size.w, size.h) };
      const at = [...view.eye, ...view.aim, view.fovY, size.w, size.h];
      // nothing moved and the engine has nothing new (a frame arriving, weights easing): the picture holds
      if (at.length === drawn.length && at.every((x, i) => x === drawn[i]) && !engine.dirty()) return false;
      drawn = at;
      viewer.render(view);
      return true;
    },
    // waiting for something no event announces (the viewer's loop keeps its full rate meanwhile)
    busy: () => active && (hold > 0 || !!snap || !!gesture || performance.now() - touch < 500 || performance.now() - since < 500),
    onPointerDown() {
      if (photoOn()) { snap = null; if (viewer.pointers.size === 1) gesture = { v: dir(theta, phi) }; }
    },
    onDrag(p) {
      const pan = p.button === 2 || p.shift;
      if (pan && !photoOn()) {
        const scale = radius * 0.0009;
        target[0] -= p.dx * scale * Math.cos(theta); target[2] += p.dx * scale * Math.sin(theta);
        target[0] -= p.dy * scale * Math.sin(theta); target[2] -= p.dy * scale * Math.cos(theta);
      } else if (!pan) {
        theta -= p.dx * 0.006;
        phi = clamp(phi + p.dy * 0.005, 0.08, 1.565);
        if (p.dragged) free();
        touch = performance.now();
      }
    },
    onPinch(scale) {
      if (photoOn()) { zoom = clamp(zoom * scale, 0.4, 1); touch = performance.now(); }
      else radius = clamp(radius * scale, 29, 180);
    },
    onWheel(e) {
      const k = Math.exp(wheelPixels(e) * 0.001);      // (pixels, whatever unit the device reports; a pinch scaled up)
      if (photoOn()) { zoom = clamp(zoom * k, 0.4, 1); touch = performance.now(); }
      else radius = clamp(radius * k, 29, 180);
    },
    onKey(e) {
      const k = e.key.toLowerCase();
      if (!['arrowup', 'arrowdown', 'arrowleft', 'arrowright', 'w', 'a', 's', 'd'].includes(k)) return false;
      if (photoOn()) {
        const now = performance.now(), cur = snap ? snap.f : nearest(dir(theta, phi));
        if (k === 'arrowleft' || k === 'a') go(step(cur, -1), now);
        else if (k === 'arrowright' || k === 'd') go(step(cur, 1), now);
        else if (k === 'arrowup' && cur.ring === 'o') go(other(cur), now);
        else if (k === 'arrowdown' && cur.ring !== 'o') go(other(cur), now);
        else if (k === 'w') zoom = clamp(zoom * 0.9, 0.4, 1);
        else if (k === 's') zoom = clamp(zoom / 0.9, 0.4, 1);
        else return true;
        if (k !== 'w' && k !== 's') free();
        return true;
      }
      if (k === 'arrowleft' || k === 'a') theta -= 0.12;
      if (k === 'arrowright' || k === 'd') theta += 0.12;
      if (k === 'arrowup') phi = clamp(phi + 0.08, 0.08, 1.565);
      if (k === 'arrowdown') phi = clamp(phi - 0.08, 0.08, 1.565);
      if (k === 'w') radius = clamp(radius * 0.92, 29, 180);
      if (k === 's') radius = clamp(radius * 1.08, 29, 180);
      free();
      return true;
    },
    state() {
      return {
        view: viewId, garden,
        photo: EXT ? { frames: EXT.frames.length, on: photoOn(), at: list[0] ? list[0].id : null, weight: list[0] ? list[0].weight : 0, zoom, settling: !!snap } : null,
        target: target.slice(), theta, phi, radius,
      };
    },
  };
}
