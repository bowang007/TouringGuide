// Browser checks of assets/js/tour/engine.js through tools/web/dev/engine_harness.html.
//
//   NODE_PATH=<dir with puppeteer-core>/node_modules node tools/web/dev/run_engine_checks.js \
//       --out <dir for screenshots + report.json> [--base http://127.0.0.1:8765] [--only rest,blend,...]
//       [--gpu egl|vulkan|swiftshader] [--size 1600x900] [--depth 1024]
//
// Needs the repo served by a static server (python3 -m http.server 8765 --bind 127.0.0.1 from the repo
// root) and Chrome at /usr/bin/google-chrome (CHROME overrides). Sections:
//   rest      (a) frame at rest vs the view cut from the panorama file, PSNR >= 40 dB
//   blend     (b) K0 -> D0 at t = 0 .. 1: no bake, no black holes; continuity with the rest state
//   pick      (c) depth-cube pick: floor below the eye, horizontal wall normal, agreement with ray casts
//   doll      (d) dollhouse from four azimuths   plan  (e) orthographic floor plan
//   exterior  (f) the legacy exterior API: on a frame the view is that frame's file (PSNR >= 32 dB with
//                 the full frame, >= 28 dB with the half-size one); between two frames the picture stays whole
//   perf      (g) frame times and memory        overlay, levels, fly, dirty: the other additions
// Exit code 1 when a numeric check fails. The screenshots still have to be looked at.
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; };
const OUT = path.resolve(arg('out', 'engine_checks_out'));
const BASE = arg('base', 'http://127.0.0.1:8765');
const ONLY = (arg('only', '') || '').split(',').filter(Boolean);
const GPU = arg('gpu', 'egl');
const [W, Hh] = arg('size', '1600x900').split('x').map(Number);
const DEPTH = arg('depth', '');
const HARNESS = BASE + '/tools/web/dev/engine_harness.html';
const GPU_ARGS = {
  egl: ['--use-angle=gl-egl'],
  vulkan: ['--use-angle=vulkan', '--enable-gpu', '--ignore-gpu-blocklist', '--enable-features=Vulkan'],
  swiftshader: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
}[GPU];
const want = (s) => !ONLY.length || ONLY.includes(s);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const report = { gpu: GPU, size: [W, Hh], depth: DEPTH || '1024', checks: {}, failures: [] };
const fail = (msg) => { report.failures.push(msg); console.log('FAIL', msg); };
const round = (v, n = 3) => Math.round(v * 10 ** n) / 10 ** n;

async function open(browser, query = '') {
  const page = await browser.newPage();
  const errors = [];
  page.on('console', (m) => { if ((m.type() === 'error' || m.type() === 'warning') && !/Failed to load resource/.test(m.text())) errors.push(m.type() + ': ' + m.text().slice(0, 300)); });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message.slice(0, 300)));
  page.on('response', (r) => { if (r.status() >= 400 && !/favicon/.test(r.url())) errors.push(`http ${r.status()} ${r.url()}`); });
  await page.setViewport({ width: W, height: Hh });
  await page.goto(HARNESS + '?quiet=1' + (DEPTH && !/depth=/.test(query) ? '&depth=' + DEPTH : '') + query, { waitUntil: 'load' });
  await page.waitForFunction(() => window.H && window.H.ready, { timeout: 120000 });
  page.errors = errors;
  return page;
}

const shot = (page, name) => page.screenshot({ path: path.join(OUT, name) });

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || '/usr/bin/google-chrome', headless: 'new',
    args: ['--no-first-run', '--hide-scrollbars', ...GPU_ARGS],
  });
  const warm = await browser.newPage();
  await warm.goto('about:blank');
  await warm.evaluate(() => !!document.createElement('canvas').getContext('webgl2'));
  const page = await open(browser);
  report.renderer = await page.evaluate(() => E.caps);
  report.footprint = await page.evaluate(() => H.footprint.length);

  // (a) ---------------------------------------------------------------------------------------
  if (want('rest')) {
    const res = [];
    // The reference is a bilinear lookup. `min` is 40 dB except for the last view: steeply down on the
    // patterned bathroom tile, where the GPU's anisotropic filter and a bilinear tap legitimately differ
    // (the panorama is minified along u near the pole); reported, with a lower bar.
    const views = [['K0', {}], ['L0', { pitch: -0.25 }], ['E0', { yaw: 0.6, pitch: 0.2 }], ['B3', { yaw: -2.2 }], ['D0', { fovY: 1.3 }], ['K0', { pitch: -1.2 }, 'K0_down'], ['A0', {}], ['A0', { pitch: -0.9 }, 'A0_down', 34]];
    for (const [id, o, name = id, min = 40] of views) {
      const r = await page.evaluate((id, o) => H.restPsnr(id, o), id, o);
      await shot(page, `a_rest_${name}.png`);
      res.push({ id: name, psnr: round(r.psnr, 2), pure: r.pure, calls: r.calls });
      if (!(r.psnr >= min)) fail(`rest ${name}: PSNR ${r.psnr.toFixed(2)} dB < ${min}`);
      if (!r.pure || r.calls !== 1) fail(`rest ${id}: not the pure fast path (pure ${r.pure}, calls ${r.calls})`);
    }
    report.checks.rest = res;
    console.log('rest', JSON.stringify(res));
  }

  // (b) ---------------------------------------------------------------------------------------
  if (want('blend')) {
    const res = [];
    for (const pair of [['K0', 'D0'], ['H2', 'K0'], ['L0', 'L1']]) {
      for (const t of [0, 0.25, 0.5, 0.75, 1]) {
        const r = await page.evaluate(async (a, b, t) => {
          E.setDebug({ bake: false });
          const info = await H.blendFrame(a, b, t);
          const clean = H.frameStats();
          const frame = H.pixels();
          E.setDebug({ bake: true });
          H.render(H.last);
          const dbg = H.frameStats();
          E.setDebug({ bake: false });
          H.render(H.last);
          // the same frame again must be identical (deterministic, no easing)
          const again = H.pixels();
          let diff = 0;
          for (let i = 0; i < frame.length; i++) if (frame[i] !== again[i]) diff++;
          return { t, black: clean.black, bake: dbg.magenta, pure: info.info.pure, slots: info.info.slots, repeatDiff: diff, calls: info.calls };
        }, pair[0], pair[1], t);
        await shot(page, `b_blend_${pair[0]}_${pair[1]}_${String(t).replace('.', '')}.png`);
        res.push({ pair: pair.join('>'), t, black: round(r.black, 5), bake: round(r.bake, 6), pure: r.pure, repeatDiff: r.repeatDiff, calls: r.calls, slots: r.slots.map((s) => `${s.id}:${s.weight}/${s.occlusion}`).join(' ') });
        if (r.bake > 0) fail(`blend ${pair.join('>')} t=${t}: bake visible on ${(r.bake * 100).toFixed(3)}% of the frame`);
        if (r.black > 0.002) fail(`blend ${pair.join('>')} t=${t}: ${(r.black * 100).toFixed(2)}% black`);
        if (r.repeatDiff) fail(`blend ${pair.join('>')} t=${t}: not deterministic (${r.repeatDiff} bytes differ)`);
      }
    }
    // Leaving the rest state must not pop: the pure panorama against the projected model from the
    // same camera (test hook noRest), and against the first frames of the move.
    const cont = await page.evaluate(async () => {
      const out = {};
      const cmp = (p, q) => { let se = 0; for (let i = 0; i < p.length; i += 4) for (let k = 0; k < 3; k++) { const d = p[i + k] - q[i + k]; se += d * d; } return se === 0 ? 99 : 10 * Math.log10(255 * 255 / (se / (p.length / 4 * 3))); };
      for (const [a, b] of [['K0', 'D0'], ['L0', 'L1'], ['E0', 'H1']]) {
        await H.blendFrame(a, b, 0);
        const pure = H.pixels();
        const wasPure = E.projectionInfo().pure;
        E.setDebug({ noRest: true });
        H.render(H.last);
        const mesh = H.pixels();
        const meshPure = E.projectionInfo().pure;
        E.setDebug({});
        await H.blendFrame(a, b, 0.01);
        const step = H.pixels();
        out[a + '>' + b] = { same: cmp(pure, mesh), step: cmp(mesh, step), wasPure, meshPure };
      }
      return out;
    });
    for (const [k, v] of Object.entries(cont)) {
      if (!v.wasPure || v.meshPure) fail(`continuity ${k}: wrong paths (${JSON.stringify(v)})`);
      if (v.same < 42) fail(`continuity ${k}: the projected model differs from the pure panorama at the same camera (${v.same.toFixed(1)} dB)`);
    }
    report.checks.blend = res;
    report.checks.continuity = cont;
    console.log('blend', JSON.stringify(res));
    console.log('continuity', JSON.stringify(cont));
  }

  // (c) ---------------------------------------------------------------------------------------
  if (want('pick')) {
    const r = await page.evaluate(async () => {
      const out = {};
      E.setMode('inside');
      E.setSweepBlend('K0', null, 0);
      await H.loadPano('K0', '4k');
      const before = E.pick(0, 0);                       // nothing rendered at rest yet: no pick
      await E.prepare('K0');
      const p = H.byId.K0.p;
      H.render(H.view(p, H.byId.K0.yaw, -Math.PI / 2 + 0.02, 1.1));
      out.down = E.pick(0, 0);
      out.downRay = E.pick(0, 0, { raycast: true, classes: ['base', 'furniture'] });
      out.eye = p;
      H.render(H.view(p, Math.PI, 0.05, 1.1));            // towards the south wall of the kitchen
      out.wall = E.pick(0, 0);
      out.wallRay = E.pick(0, 0, { raycast: true, classes: ['base', 'wall', 'furniture', 'decor_high'] });
      H.render(H.view(p, H.byId.K0.yaw, 1.2, 1.1));
      out.up = E.pick(0, 0);
      out.early = before;
      out.compare = {};
      for (const id of ['K0', 'L0', 'B3', 'E0']) {
        E.setSweepBlend(id, null, 0);
        await H.loadPano(id, '4k');
        await E.prepare(id);
        H.render(H.view(H.byId[id].p, H.byId[id].yaw, -0.3, 1.2));
        const t = performance.now();
        for (let i = 0; i < 2000; i++) E.pick((i % 50) / 25 - 1, Math.floor(i / 50) / 20 - 1);
        const us = (performance.now() - t) / 2000 * 1000;
        out.compare[id] = Object.assign(H.pickCompare(300), { microsPerPick: us });
      }
      // during a move there is no depth pick
      await H.blendFrame('K0', 'D0', 0.5);
      out.moving = E.pick(0, 0);
      return out;
    });
    const c = {
      down: r.down && { y: round(r.down.point[1]), below: round(r.eye[1] - r.down.point[1]), distance: round(r.down.distance), normal: r.down.normal.map((v) => round(v)), cls: r.down.cls },
      downRay: r.downRay && { y: round(r.downRay.point[1]), distance: round(r.downRay.distance), cls: r.downRay.cls },
      wall: r.wall && { point: r.wall.point.map((v) => round(v)), normal: r.wall.normal.map((v) => round(v)), distance: round(r.wall.distance), cls: r.wall.cls },
      wallRay: r.wallRay && { distance: round(r.wallRay.distance), normal: r.wallRay.normal.map((v) => round(v)), cls: r.wallRay.cls },
      up: r.up && { y: round(r.up.point[1]), normal: r.up.normal.map((v) => round(v)), cls: r.up.cls },
      early: r.early, moving: r.moving,
      compare: Object.fromEntries(Object.entries(r.compare).map(([k, v]) => [k, { n: v.n, miss: v.miss, meanErr: round(v.meanErr), maxErr: round(v.maxErr), normalDot: round(v.normalDot), cls: v.cls, micros: round(v.microsPerPick, 1), bad: v.bad.length }])),
    };
    report.checks.pick = c;
    report.checks.pickBad = Object.fromEntries(Object.entries(r.compare).map(([k, v]) => [k, v.bad]));
    console.log('pick', JSON.stringify(c));
    if (!r.down) fail('pick: nothing below the eye');
    else {
      if (Math.abs(r.eye[1] - r.down.point[1] - 5.085) > 0.12) fail(`pick: floor is ${(r.eye[1] - r.down.point[1]).toFixed(3)} ft below the eye, expected about 5.085`);
      if (r.down.normal[1] < 0.99) fail(`pick: floor normal ${r.down.normal}`);
    }
    if (!r.wall) fail('pick: no wall hit');
    else if (Math.abs(r.wall.normal[1]) > 0.03) fail(`pick: wall normal not horizontal ${r.wall.normal}`);
    if (r.moving !== null) fail('pick: a depth pick was returned during a move');
    for (const [k, v] of Object.entries(r.compare)) {
      if (v.n < 250) fail(`pick ${k}: only ${v.n} of 300 points comparable`);
      if (v.bad.length > v.n * 0.08) fail(`pick ${k}: ${v.bad.length} of ${v.n} points differ from the ray cast by more than 0.25 ft`);
    }
  }

  // (d) (e) -----------------------------------------------------------------------------------
  if (want('doll') || want('plan')) {
    const res = {};
    await page.evaluate(() => { E.setBackground(0x16181d); E.setMode('dollhouse'); });
    if (want('doll')) {
      for (const [name, az, el] of [['se', 0.75, 0.62], ['sw', -0.75, 0.62], ['nw', -2.4, 0.62], ['ne', 2.4, 0.62], ['low_s', 0.0, 0.3], ['high', 0.4, 1.25]]) {
        const st = await page.evaluate((az, el) => {
          E.setMode('dollhouse');
          H.render(H.orbitView(az, el, 92));
          return Object.assign(H.frameStats([22, 24, 29]), { calls: E.stats().calls, drawn: E.stats().drawn });
        }, az, el);
        await shot(page, `d_doll_${name}.png`);
        res['doll_' + name] = { background: round(st.background), black: round(st.black, 4), calls: st.calls, tris: st.drawn };
        if (st.background < (W > Hh ? 0.45 : 0.25)) fail(`dollhouse ${name}: only ${(st.background * 100).toFixed(0)}% background (stray geometry?)`);
      }
    }
    if (want('plan')) {
      const st = await page.evaluate(() => {
        E.setMode('floorplan');
        H.render(H.planView(31));
        const s = Object.assign(H.frameStats([22, 24, 29]), { calls: E.stats().calls });
        // click in the middle of the living room and on a wall top
        const pv = E.pv();
        const proj = (p) => E.project(p);
        const room = H.tour ? H.tour.rooms.find((r) => r.id === 'living') : null;
        const at = room ? room.at : [32, 8];
        const n = proj([at[0], 0, at[1]]);
        s.pick = E.pick(n.x, n.y);
        s.pickWalls = E.pick(n.x, n.y, { walls: true });
        s.at = at;
        s.pvLen = pv.length;
        const t = performance.now();
        for (let i = 0; i < 100; i++) E.pick((i % 10) / 10 - 0.45, Math.floor(i / 10) / 10 - 0.45);
        s.msPerPick = (performance.now() - t) / 100;
        return s;
      });
      await shot(page, 'e_plan.png');
      res.plan = { background: round(st.background), calls: st.calls, pick: st.pick && { point: st.pick.point.map((v) => round(v, 2)), cls: st.pick.cls, normal: st.pick.normal.map((v) => round(v, 2)) }, at: st.at, msPerPick: round(st.msPerPick, 2) };
      if (!st.pick) fail('floor plan: pick returned nothing in the living room');
      else if (Math.hypot(st.pick.point[0] - st.at[0], st.pick.point[2] - st.at[1]) > 0.05) fail('floor plan: pick is not under the clicked point');
      // a closer look for the caps
      await page.evaluate(() => H.render(H.planView(9, [8, 20])));
      await shot(page, 'e_plan_zoom.png');
    }
    report.checks.doll = res;
    console.log('doll/plan', JSON.stringify(res));
  }

  // fly-out: inside -> dollhouse as one camera move --------------------------------------------
  if (want('fly')) {
    const res = [];
    for (let i = 0; i <= 6; i++) {
      const s = i / 6;
      const r = await page.evaluate(async (s) => {
        E.setSweepBlend('K0', null, 0);
        await H.loadPano('K0', '4k');
        E.setBackground(0x16181d);
        const from = H.byId.K0;
        const to = H.orbitView(0.75, 0.62, 92);
        const e = s * s * (3 - 2 * s);
        if (s === 0) { E.setMode('inside'); E.setSweepBlend('K0', null, 0); await E.prepare('K0'); }
        else {
          E.setMode('dollhouse');
          E.setSweepBlend('K0', null, 0);
          E.setProjectionFade(1 - Math.min(1, s * 1.6));
          E.setClassOpacity('ceiling', 1 - Math.min(1, s * 2.5));
        }
        const eye = H.lerp(from.p, to.eye, e);
        const aim0 = [from.p[0] + H.dir(from.yaw, 0)[0], from.p[1], from.p[2] + H.dir(from.yaw, 0)[2]];
        const aim = H.lerp(aim0, to.aim, Math.min(1, e * 1.5));
        H.render({ eye, aim, fovY: 64 * Math.PI / 180 + (0.8 - 64 * Math.PI / 180) * e, near: 0.08 + 0.42 * e, far: 1200 });
        return { s, info: E.projectionInfo(), calls: E.stats().calls };
      }, s);
      await shot(page, `fly_${i}.png`);
      res.push({ s: round(s, 2), pure: r.info.pure, on: r.info.on, fade: round(r.info.fade, 2), calls: r.calls });
    }
    report.checks.fly = res;
    console.log('fly', JSON.stringify(res));
  }

  // overlay: rings at rest are hidden by walls, shown on the open floor --------------------------
  if (want('overlay')) {
    const r = await page.evaluate(async () => {
      const THREE = H.THREE;
      E.setMode('inside');
      E.setSweepBlend('K0', null, 0);
      await H.loadPano('K0', '4k');
      await E.prepare('K0');
      while (E.overlay.children.length) E.overlay.remove(E.overlay.children[0]);
      const geo = E.ring(0.55, 0.95);
      const marks = {};
      for (const s of H.sweeps) {
        const m = new THREE.Mesh(geo, E.overlayMaterial({ color: 0xff00ff, opacity: 1, soft: 0.25 }));
        m.position.set(s.p[0], (s.floor !== undefined ? s.floor : 0.02) + 0.06, s.p[2]);
        E.overlay.add(m);
        marks[s.id] = m;
      }
      E.invalidate();
      const count = () => { const p = H.pixels(); let n = 0; for (let i = 0; i < p.length; i += 4) if (p[i] > 150 && p[i + 1] < 110 && p[i + 2] > 150 && p[i] - p[i + 1] > 90) n++; return n; };
      const yaw = Math.atan2(H.byId.D0.p[0] - H.byId.K0.p[0], -(H.byId.D0.p[2] - H.byId.K0.p[2]));
      const out = {};
      const v = H.view(H.byId.K0.p, yaw, -0.45, 1.25);
      // every ring: the page would only add the visible ones; here the depth test has to hide the rest
      H.render(v);
      out.restAll = count();
      for (const m of Object.values(marks)) m.visible = false;
      marks.D0.visible = true;                 // in the open, straight ahead
      E.invalidate(); H.render(v);
      out.restD0 = count();
      marks.D0.visible = false;
      for (const id of ['A1', 'A0', 'B4', 'G0', 'E0', 'P0']) marks[id].visible = true;   // behind walls
      E.invalidate(); H.render(H.view(H.byId.K0.p, -Math.PI / 2, -0.35, 1.5));
      out.restHidden = count();
      out.pure = E.projectionInfo().pure;
      // every sweep on its own: pixels drawn against rays cast from the eye to 12 points of the ring
      const list = [];
      E.scene.traverse((o) => { if (o.isMesh && o.userData.tg_class && !['glass', 'exterior', 'cap'].includes(o.userData.tg_class) && !o.userData.tg_outside) list.push(o); });
      const rc = new THREE.Raycaster();
      out.each = {};
      out.wrong = [];
      for (const m of Object.values(marks)) m.visible = false;
      for (const s of H.sweeps) {
        if (s.id === 'K0') continue;
        marks[s.id].visible = true;
        E.invalidate();
        H.render(H.view(H.byId.K0.p, Math.atan2(s.p[0] - H.byId.K0.p[0], -(s.p[2] - H.byId.K0.p[2])), -0.3, 1.2));
        const px = count();
        let vis = 0;
        for (let k = 0; k < 12; k++) {
          const a = k / 12 * Math.PI * 2;
          const o = new THREE.Vector3(...H.byId.K0.p);
          const d = new THREE.Vector3(s.p[0] + Math.cos(a) * 0.75, marks[s.id].position.y, s.p[2] + Math.sin(a) * 0.75).sub(o);
          rc.set(o, d.clone().normalize());
          rc.far = d.length() - 0.12;
          if (!rc.intersectObjects(list, false).length) vis++;
        }
        out.each[s.id] = [px, vis];
        if ((vis === 0 && px > 30) || (vis === 12 && px < 100)) out.wrong.push(s.id);
        marks[s.id].visible = false;
      }
      // the same during a move (depth of the model)
      for (const m of Object.values(marks)) m.visible = true;
      E.invalidate();
      await H.blendFrame('K0', 'D0', 0.3, { pitch: -0.45, fovY: 1.25 });
      out.moveAll = count();
      return out;
    });
    await page.evaluate(async () => { for (const m of E.overlay.children) m.visible = true; E.setSweepBlend('K0', null, 0); H.render(H.view(H.byId.K0.p, Math.atan2(H.byId.D0.p[0] - H.byId.K0.p[0], -(H.byId.D0.p[2] - H.byId.K0.p[2])), -0.45, 1.25)); });
    await shot(page, 'overlay_rest.png');
    await page.evaluate(async () => { await H.blendFrame('K0', 'D0', 0.3, { pitch: -0.45, fovY: 1.25 }); });
    await shot(page, 'overlay_move.png');
    await page.evaluate(() => { while (E.overlay.children.length) E.overlay.remove(E.overlay.children[0]); E.invalidate(); });
    report.checks.overlay = r;
    console.log('overlay', JSON.stringify(r));
    if (!(r.restD0 > 300)) fail(`overlay: the ring on the open floor is not drawn (${r.restD0} px)`);
    if (r.restHidden > 30) fail(`overlay: rings behind walls show at rest (${r.restHidden} px)`);
    if (!r.pure) fail('overlay: the rest frame with rings left the pure path');
    if (r.wrong.length) fail(`overlay: ring occlusion at rest disagrees with ray casts for ${r.wrong.join(' ')}`);
  }

  // levels, budget, prepare ---------------------------------------------------------------------
  if (want('levels')) {
    const p2 = await open(browser, '&depth=512');
    const r = await p2.evaluate(async () => {
      const out = {};
      E.setMode('inside');
      // 2k then 4k then a lower level again
      await H.loadPano('K0', '2k');
      out.k0_2k = E.hasPanorama('K0');
      out.has4kBefore = E.hasPanorama('K0', '4k');
      await H.loadPano('K0', '4k');
      out.k0_4k = E.hasPanorama('K0');
      const bmp = await createImageBitmap(await (await fetch(new URL('../../../assets/panos/2k/K0.webp', location.href))).blob());
      out.downgradeTaken = E.setPanorama('K0', bmp, '2k');
      out.afterDowngrade = E.hasPanorama('K0').level;
      out.legacyBoolean = E.hasPanorama('K0').full;
      // prepare: texture + depth cube + pick copy before the first frame
      E.setSweepBlend('K0', null, 0);
      const t0 = performance.now();
      out.prepared = await E.prepare('K0');
      out.prepareMs = performance.now() - t0;
      out.afterPrepare = E.hasPanorama('K0');
      out.prepareMissing = await E.prepare('ZZ');
      out.prepareLevel = await E.prepare('K0', '8k');
      // 8k: one at a time
      // an 8k upgrade while the camera keeps turning: the 4k stays on screen, the 8k arrives in slices
      H.render(H.view(H.byId.K0.p, H.byId.K0.yaw, 0, 1.1));
      const a = await H.fake8k('K0');
      out.pending8k = E.hasPanorama('K0');
      const t1 = performance.now();
      const stamps = [];
      await new Promise((resolve) => {
        const tick = (now) => {
          stamps.push(now);
          H.render(H.view(H.byId.K0.p, H.byId.K0.yaw + (now - t1) / 2000, 0, 1.1));
          E.gl.readPixels(0, 0, 1, 1, E.gl.RGBA, E.gl.UNSIGNED_BYTE, new Uint8Array(4));
          if (!E.hasPanorama('K0').pending && now - t1 > 100 || now - t1 > 4000) resolve();
          else requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      });
      const gaps = stamps.slice(1).map((v, i) => v - stamps[i]);
      out.upgrade8k = { ms: performance.now() - t1, frames: gaps.length, maxGap: Math.max(...gaps), over34: gaps.filter((g) => g > 34).length };
      await E.prepare('K0');
      H.render(H.view(H.byId.K0.p, H.byId.K0.yaw, 0, 1.1));
      out.gl8kError = E.gl.getError();
      out.k0_8k = E.hasPanorama('K0');
      out.mem8k = E.memory();
      // a second 8k while resting on the first: both protected (resting, just set) ...
      const b = await H.fake8k('D0');
      out.grace8k = { K0: E.hasPanorama('K0') && E.hasPanorama('K0').level, D0: E.hasPanorama('D0') && E.hasPanorama('D0').level };
      // ... until the camera rests on the new one
      E.setSweepBlend('D0', null, 0);
      H.render(H.view(H.byId.D0.p, 0, 0, 1.1));
      out.two8k = { K0: E.hasPanorama('K0') && E.hasPanorama('K0').level, D0: E.hasPanorama('D0') && E.hasPanorama('D0').level };
      // budget: many sweeps, the resting and the transition target stay
      E.setSweepBlend('D0', 'L2', 0.5);
      for (const id of ['L2', 'L0', 'L1', 'H2', 'H3']) await H.loadPano(id, '4k');
      out.after4k = Object.fromEntries(H.sweeps.map((s) => [s.id, E.hasPanorama(s.id) && E.hasPanorama(s.id).level]).filter((x) => x[1]));
      for (const s of H.sweeps.slice(0, 16)) if (!E.hasPanorama(s.id)) await H.loadPano(s.id, '2k');
      out.after2k = Object.fromEntries(H.sweeps.map((s) => [s.id, E.hasPanorama(s.id) && E.hasPanorama(s.id).level]).filter((x) => x[1]));
      out.memEnd = E.memory();
      out.fake = [a, b];
      return out;
    });
    report.checks.levels = r;
    console.log('levels', JSON.stringify(r));
    const lv = (o) => Object.values(o);
    if (r.k0_2k.level !== '2k' || r.k0_4k.level !== '4k' || r.has4kBefore) fail('levels: 2k -> 4k upgrade wrong');
    if (r.downgradeTaken || r.afterDowngrade !== '4k') fail('levels: a lower level replaced a higher one');
    if (!r.prepared || !r.afterPrepare.depth || !r.afterPrepare.uploaded) fail('prepare: not ready after resolving');
    if (r.prepareMissing !== false || r.prepareLevel !== false) fail('prepare: should resolve false for a missing panorama / level');
    if (r.k0_8k.level !== '8k' || r.k0_8k.pending || r.gl8kError) fail('levels: 8k not accepted');
    if (!r.pending8k.pending || r.pending8k.shown !== '4k' || r.pending8k.level !== '8k') fail(`levels: the 8k upgrade did not go through the pending path (${JSON.stringify(r.pending8k)})`);
    if (r.upgrade8k.maxGap > 120) fail(`levels: the 8k upgrade froze the frame loop for ${r.upgrade8k.maxGap.toFixed(0)} ms`);
    if (lv(r.two8k).filter((x) => x === '8k').length !== 1) fail(`levels: more than one 8k kept (${JSON.stringify(r.two8k)})`);
    if (lv(r.after4k).filter((x) => x === '4k').length > 2 + 2) fail('levels: 4k cap not applied');
    if (!r.after4k.D0 || !r.after4k.L2 || !r.after2k.D0 || !r.after2k.L2) fail('levels: the resting / transition sweep was evicted');
    if (lv(r.after2k).filter((x) => x === '2k').length > 8) fail('levels: 2k cap not applied');
    await p2.close();
  }

  // render on demand ----------------------------------------------------------------------------
  if (want('dirty')) {
    const r = await page.evaluate(async () => {
      const out = [];
      E.setMode('inside'); E.setSweepBlend('K0', null, 0);
      await H.loadPano('K0', '4k');
      await E.prepare('K0');
      const v = H.view(H.byId.K0.p, 1, 0, 1.1);
      H.render(v);
      out.push(['after render', E.dirty()]);
      E.setSweepBlend('K0', null, 0);
      out.push(['same blend again', E.dirty()]);
      E.setSweepBlend('K0', 'D0', 0.2);
      out.push(['new blend', E.dirty()]);
      H.render(v);
      E.invalidate();
      out.push(['invalidate', E.dirty()]);
      H.render(v);
      E.setBackground(0x101216);
      out.push(['background', E.dirty()]);
      H.render(v);
      await H.loadPano('L0', '2k');
      out.push(['panorama arrived', E.dirty()]);
      H.render(v);
      E.setMode('dollhouse');
      out.push(['mode', E.dirty()]);
      H.render(v);
      out.push(['after render', E.dirty()]);
      E.setMode('inside'); E.setSweepBlend('K0', null, 0);
      return out;
    });
    report.checks.dirty = r;
    console.log('dirty', JSON.stringify(r));
    const expect = [false, false, true, true, true, true, true, false];
    r.forEach((x, i) => { if (x[1] !== expect[i]) fail(`dirty: "${x[0]}" gave ${x[1]}`); });
  }

  // (g) ---------------------------------------------------------------------------------------
  if (want('perf')) {
    const r = await page.evaluate(async () => {
      const out = {};
      const k = H.byId.K0, d = H.byId.D0;
      const yaw = Math.atan2(d.p[0] - k.p[0], -(d.p[2] - k.p[2]));
      E.setMode('inside'); E.setBackground(0x16181d);
      E.setSweepBlend('K0', 'D0', 0);
      await H.loadPano('K0', '4k'); await H.loadPano('D0', '4k');
      const tp = performance.now();
      await E.prepare('K0'); await E.prepare('D0');
      out.prepareBothMs = performance.now() - tp;
      E.setSweepBlend('K0', null, 0);
      out.rest = H.timeFrames(60, (i) => H.view(k.p, yaw + i * 0.01, 0, 1.117));
      await H.sleep(600);           // let the compositor swallow the 60 synchronous frames above
      out.restRaf = await H.rafLoop(2000, (u) => H.view(k.p, yaw + u, 0, 1.117));
      E.setSweepBlend('K0', 'D0', 0.5);
      out.move = H.timeFrames(60, (i) => { const t = i / 59; E.setSweepBlend('K0', 'D0', t); return H.view(H.lerp(k.p, d.p, t), yaw, 0, 1.117); });
      E.setSweepBlend('K0', 'D0', 0.5); H.render(H.view(H.lerp(k.p, d.p, 0.5), yaw, 0, 1.117));
      out.moveCalls = E.stats().calls; out.moveTris = E.stats().drawn;
      await H.sleep(600);
      out.moveRaf = await H.rafLoop(2000, (u) => { const t = Math.min(1, u); E.setSweepBlend('K0', 'D0', t); return H.view(H.lerp(k.p, d.p, t), yaw, 0, 1.117); });
      E.setMode('dollhouse');
      out.doll = H.timeFrames(40, (i) => H.orbitView(0.75 + i * 0.02, 0.62, 92));
      out.dollCalls = E.stats().calls; out.dollTris = E.stats().drawn;
      await H.sleep(600);
      out.dollRaf = await H.rafLoop(2000, (u) => H.orbitView(0.75 + u, 0.62, 92));
      E.setMode('floorplan');
      out.plan = H.timeFrames(40, () => H.planView(31));
      // a depth cube from cold: a sweep never prepared
      E.setMode('inside');
      E.setSweepBlend('K0', 'B3', 0);
      await H.loadPano('B3', '4k');
      const t0 = performance.now();
      await E.prepare('B3');
      out.prepareColdMs = performance.now() - t0;
      out.memory = E.memory();
      out.three = { geometries: E.renderer.info.memory.geometries, textures: E.renderer.info.memory.textures, programs: E.renderer.info.programs.length };
      out.depth = { size: new URLSearchParams(location.search).get('depth') || '1024' };
      E.setSweepBlend('K0', null, 0);
      return out;
    });
    report.checks.perf = r;
    console.log('perf', JSON.stringify(r));
  }

  // (f) ---------------------------------------------------------------------------------------
  if (want('exterior')) {
    const cases = [
      ['on_o00', [{ id: 'o00', weight: 1 }], 0.0, 0.5, 95],
      ['between_o00_o01', [{ id: 'o00', weight: 0.5 }, { id: 'o01', weight: 0.5 }], 0.1309, 0.5, 95],
      ['on_o06', [{ id: 'o06', weight: 1 }], Math.PI / 2, 0.5, 95],
      ['off_o12', [{ id: 'o12', weight: 0.7 }, { id: 'o13', weight: 0.3 }], Math.PI + 0.08, 0.42, 88],
      ['full_o00', [{ id: 'o00', weight: 1 }], 0.0, 0.5, 95, true],        // half -> full swap on a frame shown before
      ['full_h00', [{ id: 'h00', weight: 1 }], -0.785398, 1.05, 105, true],
    ];
    // On a frame (one target at weight 1, the camera where the frame was rendered from) the canvas is
    // compared with the frame file; a blend of two frames has no file to compare with and must only
    // stay a whole picture (no black, no background showing through).
    const res = {};
    const p = await open(browser);
    for (const [name, targets, theta, phi, radius, full] of cases) {
      const r = await p.evaluate(async (targets, theta, phi, radius, full) => {
        const o = await H.extRender(targets, theta, phi, radius, { full: !!full });
        const stats = H.frameStats();
        const psnr = targets.length === 1 ? await H.extPsnr(targets[0].id, o.fov) : null;
        return { slots: o.info.slots, calls: o.stats.calls, black: stats.black, psnr };
      }, targets, theta, phi, radius, full);
      await shot(p, `f_ext_${name}.png`);
      res[name] = { psnr: r.psnr === null ? null : round(r.psnr, 2), black: round(r.black, 5), slots: r.slots };
      if (r.psnr !== null && r.psnr < (full ? 32 : 28)) fail(`exterior ${name}: the view differs from the frame file (${r.psnr.toFixed(1)} dB)`);
      if (r.black > 0.02) fail(`exterior ${name}: ${(r.black * 100).toFixed(1)} % black pixels`);
    }
    if (p.errors.length) fail(`exterior: console ${p.errors.slice(0, 3).join(' | ')}`);
    await p.close();
    report.checks.exterior = res;
    console.log('exterior', JSON.stringify(res));
  }

  if (page.errors.length) fail('console: ' + page.errors.slice(0, 5).join(' | '));
  report.console = page.errors;
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 1));
  console.log(report.failures.length ? `${report.failures.length} FAILED` : 'ALL PASSED', '->', path.join(OUT, 'report.json'));
  await browser.close();
  process.exit(report.failures.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
