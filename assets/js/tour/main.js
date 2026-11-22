// Boot of the tour: loads the modules and the data, creates the engine and the viewer, wires the
// chrome, and opens the mode the URL asks for (or the landing page).
//
// URL parameters
//   ?sweep=ID                 open the inside view on that sweep (&yaw=&pitch=&fov= in degrees, optional)
//   ?mode=inside|dollhouse|floorplan|exterior      open that view (&view=front|left|rear|right|roof for exterior)
//   ?pano=2k|4k|8k            pin the panorama level;  ?exterior=model  exterior without the rendered frames
//   ?webgl=off                show the page as a browser without WebGL 2 gets it (the fallback)
// While the tour runs the address bar is kept in step with the place the visitor is at (the first two
// lines above, written with history.replaceState, so no history entries pile up): a copied link, a
// bookmark or a reload opens the same view.
//
// Order of loading: the landing page works from the first module on (a button pressed before the
// rest has arrived is remembered and wins over the default). The inside view needs only the engine
// and its first panorama, so it opens while the 3D model (the largest file) is still downloading;
// the dollhouse, the floor plan, the exterior, the floor rings and the glide between sweeps follow
// when the model is in. Nothing is fetched for a closed sheet, the closed reel or a view nobody chose.
//
// The modules of this folder do not import each other: each exports one create* function and gets what
// it needs handed in here (the viewer carries util, panos, the sweep graph and the engine). That way this
// file can load them all with the release label (?v=...) that index.html put on main.js.

// The mirror on netlify.app (tools/web/deploy_mirror.sh) carries the host's badge in the lower right corner on its
// free plan; the chrome moves up clear of it (tour.css .host-badge).
if (/\.netlify\.app$/.test(location.hostname)) document.documentElement.classList.add('host-badge');

const ENGINE = './engine.js';
const FILES = {
  tour: 'assets/data/tour.json',
  measurements: 'assets/data/measurements.json',
  design: 'assets/data/design.json',
  panos: 'assets/panos/manifest.json',
  plan: 'assets/plans/dimension-plan.svg',
  model: 'assets/model/house.glb',
  exterior: 'assets/exterior/manifest.json',
};
// The look of the dollhouse and the floor plan: where the walls are cut (ft: under the skylight wells,
// which start at 7.5), the colour of the cut (a neutral dark grey), and the house-wide gain of the baked
// textures (engine.setAdaptation; 1 = the bake as it is).
const DOLL_CUT = 7.45, DOLL_CAP = 0x3a3c40, DOLL_TONE = [1.2, 1.2, 1.2];
// The inside view's field of view (degrees, vertical, on a landscape screen); a link to the current place
// names another one only when the visitor has zoomed. And the exterior views a link can name.
const INSIDE_FOV = 68, EXTERIOR_VIEWS = ['front', 'left', 'rear', 'right', 'roof'];
const RELEASE = new URL(import.meta.url).searchParams.get('v') || '';
const stamp = (v) => (v ? '?v=' + encodeURIComponent(v) : '');
const load = (name) => import(new URL(name + stamp(RELEASE), import.meta.url).href);
const json = (url, init) => fetch(url, init).then((r) => { if (!r.ok) throw Error('HTTP ' + r.status + ' ' + url); return r.json(); });
const quiet = (p) => p.catch((e) => { console.warn(e); return null; });

async function boot() {
  const query = new URLSearchParams(location.search);
  const { createUI } = await load('./ui.js');
  const ui = createUI();
  const deep = query.has('sweep') || query.has('mode');
  if (deep) ui.closeLanding(); else ui.openLanding();

  // WebGL 2 first: without it there is no engine to wait for.
  const canvas = ui.canvas;
  const gl = query.get('webgl') === 'off' ? null : canvas.getContext('webgl2', { antialias: true, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });

  // Data. tour.json is always revalidated and names the release; everything else is fetched with it
  // (`v` is the ?v=... suffix; the sheets get it for their images).
  const modules = Promise.all(['./viewer.js', './inside.js', './dollhouse.js', './exterior.js', './dimensions.js', './design.js', './testapi.js'].map(load));
  const engineModule = gl ? load(ENGINE).catch((e) => e) : null;
  const tour = await json(FILES.tour, { cache: 'no-cache' });
  const v = stamp(tour.version || RELEASE);
  // The model and the plan carry their own content hash (tour.json `files`), so a re-bake reaches a
  // returning visitor without a new release label; the release label stands in where there is none.
  const own = (key) => (tour.files && tour.files[key] ? stamp(tour.files[key]) : v);
  const [measurements, design, manifest, planSvg] = await Promise.all([
    quiet(json(FILES.measurements + v)),
    quiet(json(FILES.design + v)),
    quiet(json(FILES.panos, { cache: 'no-cache' })),
    quiet(fetch(FILES.plan + own('plan')).then((r) => (r.ok ? r.text() : null))),
  ]);
  const [viewerM, insideM, dollhouseM, exteriorM, dimensionsM, designM, testM] = await modules;

  // The 3D part, when there is one.
  let viewer = null, exterior = null;
  // The link to the place the visitor is at: ?sweep=ID&yaw=&pitch= (whole degrees; &fov= when zoomed)
  // inside, ?mode=dollhouse|floorplan|exterior (&view= on an exterior preset) otherwise, neither while
  // the landing page is up. The other parameters of the address (?pano=...) are kept.
  function placeUrl() {
    const url = new URL(location.href), q = url.searchParams, at = viewer ? viewer.state() : null;
    for (const k of ['sweep', 'yaw', 'pitch', 'fov', 'mode', 'view']) q.delete(k);
    if (!at || !at.mode || ui.landingOpen()) return url;
    if (at.mode === 'inside' && at.sweep) {
      const deg = (r) => String(Math.round(Math.atan2(Math.sin(r), Math.cos(r)) * 180 / Math.PI) || 0);
      q.set('sweep', at.sweep);
      q.set('yaw', deg(at.yaw));
      q.set('pitch', deg(at.pitch));
      if (Math.abs(at.fov - INSIDE_FOV) > 0.5) q.set('fov', String(Math.round(at.fov)));
    } else {
      q.set('mode', at.mode);
      const view = at.exterior && at.exterior.view;
      if (at.mode === 'exterior' && EXTERIOR_VIEWS.includes(view) && view !== 'front') q.set('view', view);
    }
    return url;
  }
  const fail = (error) => {
    console.error('[tour] 3D view unavailable:', error);
    const lost = error && error.contextLost;
    const back = placeUrl();                           // where the visitor was, so "Reload the tour" brings them back to it
    ui.showFallback(design, !gl ? null : (lost ? 'The browser paused the graphics renderer. Reload the page to continue the tour.' : 'The 3D model could not be loaded. Reload the page to try the tour again.') + ' Meanwhile the design renders are below; the dimensioned plan and the design notes work as usual.', v);
    if (gl && !document.getElementById('fallbackReload')) {
      const b = document.createElement('button');
      b.id = 'fallbackReload';
      b.dataset.testid = 'fallback-reload';
      b.textContent = 'Reload the tour';
      b.addEventListener('click', () => { location.href = back.href; });
      ui.$('fallbackDimensions').parentNode.prepend(b);
    }
  };
  const eng = await engineModule;
  if (gl && eng && typeof eng.createEngine === 'function') {
    const lite = (navigator.deviceMemory || 8) < 8 || matchMedia('(pointer:coarse)').matches;
    const offsets = (manifest && manifest.nodes) || {};
    let engine = null;
    try {
      engine = eng.createEngine(canvas, Object.assign({
        context: gl,
        interior: [0, 0, tour.extent[0], tour.extent[1]],
        footprint: tour.footprint,
        sweeps: tour.sweeps.map((s) => ({ id: s.id, p: s.p, offset: (offsets[s.id] && offsets[s.id].offset) || 0 })),
        // dollhouse / floor plan: the walls are cut just under the skylight wells, their tops a neutral dark grey
        clipY: DOLL_CUT, capColor: DOLL_CAP,
        // GPU budget: panoramas held per level and depth cubes (the sweep the camera is on, the one it moves
        // to, and the neighbours prepared ahead of a move). A phone gets the small set and no 8k.
      }, lite ? { depthSize: 512, depthPool: 4, budget: { max8k: 0, max4k: 1, max2k: 6 } }
        : { depthSize: 1024, depthPool: 6, budget: { max8k: 1, max4k: 2, max2k: 12 } }));
    } catch (e) { fail(e); }
    if (engine) {
      viewer = viewerM.createViewer({
        canvas, engine, tour, manifest, manifestUrl: FILES.panos, lite, query,
        gate: () => !ui.landingOpen() && !ui.modalOpen(),
      });
      viewer.register('inside', insideM.createInside(viewer, Object.assign({ fov: INSIDE_FOV }, lite ? { prepare: 2, hold: 4 } : { prepare: 4, hold: 9 })));
      const doll = dollhouseM.createDollhouse(viewer, { tone: DOLL_TONE });
      viewer.register('dollhouse', doll.dollhouse);
      viewer.register('floorplan', doll.floorplan);
      exterior = viewer.register('exterior', exteriorM.createExterior(viewer, {
        manifestUrl: FILES.exterior,
        onFrontImage: () => designSheet.open('front'),
        // behind the landing page the view only gets the one frame it stands on: the visitor has not chosen yet
        background: () => ui.landingOpen(),
      }));
    }
  } else if (gl) fail(eng instanceof Error ? eng : new Error('engine module missing'));

  // Sheets (they work without the 3D view).
  // "Visit" from a sheet: stand on that sweep, facing its own direction. When the 3D view has stopped
  // (the browser took the WebGL context away) the fallback page is up: the buttons say so.
  const stopped = () => {
    if (viewer.engineState !== 'failed') return false;
    ui.toast('The 3D view has stopped. Reload the page to continue the tour.');
    return true;
  };
  const visit = viewer ? (node) => { if (!stopped()) viewer.goTo(viewer.sweep(node) ? node : tour.start, { instant: true, reset: true }); } : null;
  const dimensions = dimensionsM.createDimensions({ data: measurements, planSvg, ui, visit });
  const designSheet = designM.createDesign({
    data: design, ui, suffix: v, dimensions, visit,
    thumb: viewer ? (id) => viewer.panos.thumb(id) : null,
    exterior: viewer ? (view) => { if (!stopped()) viewer.setMode('exterior', { view }); } : null,
  });
  ui.$('fallbackDimensions').addEventListener('click', () => dimensions.open());
  ui.$('fallbackDesign').addEventListener('click', () => designSheet.open('front'));
  testM.createTestApi({ viewer, ui, exterior });
  if (!viewer) { if (!gl) ui.showFallback(design, null, v); return; }

  ui.bind({
    viewer, tour, measurements, modelUrl: FILES.model + own('model'),
    openDimensions: () => dimensions.open(),
    openDesign: (id = 'front') => designSheet.open(id),
    onFailed: fail,
  });

  // The address bar follows the visitor: rewritten in place a moment after the view has come to rest
  // (never during a move, and not before the view the page was opened with is up).
  let linkDue = 0, linkTimer = 0;
  const writeLink = () => {
    linkTimer = 0;
    const wait = linkDue - performance.now(), at = viewer.state();
    if (wait > 0) { linkTimer = setTimeout(writeLink, wait + 4); return; }
    if (viewer.engineState === 'failed' || !at.mode || (at.mode === 'inside' && at.transition)) return;
    const url = placeUrl();
    if (url.href === location.href) return;
    try { history.replaceState(history.state, '', url); } catch (e) { /* a sandboxed frame may refuse: the tour goes on */ }
  };
  const syncLink = () => { linkDue = performance.now() + 250; if (!linkTimer) linkTimer = setTimeout(writeLink, 254); };
  for (const type of ['mode', 'sweep', 'transition', 'flight', 'place', 'frame']) viewer.on(type, syncLink);

  // Start: the loop runs at once. The inside view opens as soon as its first panorama is in; the other
  // views (and the rings and the walk between the sweeps) wait for the model.
  viewer.start();
  viewer.engine.load(FILES.model + own('model'), (p) => viewer.emit('progress', { loaded: p }))
    .then(() => viewer.setEngineState('ready'), (e) => viewer.setEngineState('failed', e));
  const num = (k) => { const x = parseFloat(query.get(k)); return Number.isFinite(x) ? x : undefined; };
  const rad = (k) => { const x = num(k); return x === undefined ? undefined : x * Math.PI / 180; };
  const mode = query.get('mode'), sweep = viewer.sweep(query.get('sweep')) ? query.get('sweep') : null;
  if (sweep && (!mode || mode === 'inside')) viewer.setMode('inside', { sweep, yaw: rad('yaw'), pitch: rad('pitch'), fov: num('fov') });
  else if (mode && viewer.controllers[mode]) viewer.setMode(mode, mode === 'exterior' ? { view: query.get('view') || 'front' } : mode === 'inside' ? { yaw: rad('yaw'), pitch: rad('pitch'), fov: num('fov') } : {});
  else {
    if (deep) ui.openLanding();                        // the link named nothing we have: start as usual
    // Behind the landing page the exterior waits (the model and its front frame load meanwhile). A visitor
    // who has already pressed one of the landing buttons gets what they chose (ui.bind above), not this.
    if (ui.landingOpen()) viewer.setMode('exterior', { view: 'front' });
  }
}

boot().catch((e) => {
  console.error('[tour] could not start:', e);
  const el = document.getElementById('error'), loading = document.getElementById('loading'), landing = document.getElementById('landing');
  if (loading) loading.classList.add('hide');
  if (landing) { landing.classList.remove('open'); for (const c of document.body.children) c.inert = false; }
  if (el) { el.textContent = 'The tour could not be loaded. Check the connection and reload the page.'; el.style.display = 'block'; }
});
