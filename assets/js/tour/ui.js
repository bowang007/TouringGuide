// The chrome of the tour: toolbar, highlight reel, room chip, first-run hint, floor-plan labels, toasts,
// the loading states (the full screen before the first picture, the small note while the 3D model is
// still on its way, the wait mark of a view that is loading) and the fallback page, the landing page,
// the menu and the sheet (modal) helpers.
//
// createUI() works on the markup alone, so the landing page and the loading state are alive before any
// data has arrived; bind(ctx) connects it to the viewer and the data once they exist.

export function createUI() {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const canvas = $('view');

  // ---- small helpers the other modules use ---------------------------------------------------
  let toastTimer = 0;
  function toast(text) {
    closeMenu();                                       // a message outranks the menu (on a small screen they would share a corner)
    $('toast').textContent = text;
    $('toast').classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $('toast').classList.remove('show'), 2800);
  }
  function downloadBlob(blob, name) {
    const a = document.createElement('a'), url = URL.createObjectURL(blob);
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  }
  // feet -> 12′3½″ (eighths of an inch)
  function ft(v) {
    const n = Math.round(v * 96);
    return Math.floor(n / 96) + '′' + Math.floor(n % 96 / 8) + ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][n % 8] + '″';
  }

  // ---- what may take focus and clicks --------------------------------------------------------
  // Only the landing page while it is open, only the sheet while one is open, and never the closed
  // reel. This one function decides for all three, so they cannot disagree. (The toast and the error
  // message stay announced.)
  const landing = $('landing');
  const landingOpen = () => landing.classList.contains('open');
  const modalOpen = () => !!document.querySelector('.modal.open');
  const reelOpen = () => $('reel').classList.contains('open');
  function syncInert() {
    const top = landingOpen() ? landing : document.querySelector('.modal.open');
    for (const el of document.body.children) {
      if (el.tagName === 'SCRIPT' || el.id === 'toast' || el.id === 'error') continue;
      el.inert = top ? el !== top : el.id === 'reel' && !reelOpen();
    }
  }

  // ---- sheets --------------------------------------------------------------------------------
  let opener = null;                                   // what had the focus when the sheet opened
  // refocus = false when the caller puts the focus somewhere itself
  function closeModals(refocus = true) {
    if (!modalOpen()) return;
    document.querySelectorAll('.modal.open').forEach((e) => e.classList.remove('open'));
    syncInert();
    // the focus goes back to where it came from, or to the view: never to "the top of the page"
    const back = opener && opener.isConnected && !opener.closest('[inert]') && opener.getClientRects().length ? opener : canvas;
    opener = null;
    if (refocus) back.focus({ preventScroll: true });
  }
  function openModal(id) {
    const had = document.activeElement;
    // one sheet opened from another keeps the first one's way back; a menu item stands for the menu button
    const from = modalOpen() ? opener : had && had.closest('#menu') ? $('btnMenu') : had;
    closeModals(false);
    closeMenu();
    opener = from && from !== document.body ? from : null;
    $(id).classList.add('open');
    syncInert();
    $(id).scrollTop = 0;
    const b = $(id).querySelector('button');
    if (b) b.focus();
  }
  document.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => closeModals()));
  document.querySelectorAll('.modal').forEach((m) => m.addEventListener('click', (e) => { if (e.target === m) closeModals(); }));

  // ---- landing page --------------------------------------------------------------------------
  // It sits above the loading screen and below the error message.
  function openLanding() {
    closeModals(false);
    landing.classList.add('open');
    syncInert();
    $('landingTour').focus({ preventScroll: true });
  }
  function closeLanding() {
    if (!landingOpen()) return;
    landing.classList.remove('open');
    syncInert();
    canvas.focus({ preventScroll: true });
  }
  let choose = null, chosen = null;                    // the landing buttons work before bind(): the choice waits
  function landingGo(choice) {
    closeLanding();
    closeModals(false);
    if (choose) choose(choice); else chosen = choice;
  }
  $('landingExterior').addEventListener('click', () => landingGo('exterior'));
  $('landingTour').addEventListener('click', () => landingGo('inside'));
  $('landingPlan').addEventListener('click', () => landingGo('floorplan'));
  // Keys stay with the landing page while it is open (Enter / Space press the focused button, Escape = Exterior).
  window.addEventListener('keydown', (e) => {
    if (!landingOpen()) return;
    if (e.key === 'Escape') { e.stopImmediatePropagation(); e.preventDefault(); landingGo('exterior'); }
    else if (e.key !== 'Tab') e.stopImmediatePropagation();
  }, true);

  // ---- loading, error, fallback --------------------------------------------------------------
  // The loading screen is up from the start (markup) until the first frame is drawn. It shows the
  // front of the house (the landing page's own picture: the same file, fetched once) under a shade,
  // and how much of the 3D model is in (loaded: 0..1; without it the bar runs to and fro).
  {
    const bg = landing.querySelector('.landing-bg'), url = bg && (bg.currentSrc || bg.src);
    if (url) $('loading').style.backgroundImage = 'linear-gradient(#0c1712b0,#0c1712d6),url("' + url.replace(/["\\\n]/g, '') + '")';
  }
  function setLoading(text, loaded) {
    if (text) $('loadingText').textContent = text;
    const known = Number.isFinite(loaded);
    $('loadingBar').classList.toggle('roll', !known);
    $('loadingBar').firstElementChild.style.width = known ? Math.round(loaded * 100) + '%' : '';
  }
  function hideLoading() {
    if ($('loading').classList.contains('hide')) return;
    $('loading').classList.add('hide');
    setTimeout(() => { $('loading').hidden = true; }, 600);       // gone for real once it has faded: nothing of it animates on
  }
  // No WebGL 2 (or the model could not be loaded): the design stills, with the two sheets still usable.
  // suffix: the release label as '?v=...' for the pictures.
  function showFallback(design, note, suffix = '') {
    hideLoading();
    closeLanding();
    document.body.classList.add('no-webgl');
    if (note) $('fallbackNote').textContent = note;
    const stills = design ? design.order.map((k) => design.views[k]).filter((x) => x && /\.(webp|jpe?g|png|avif)$/i.test(x.image || '')) : [{ image: 'assets/design/front.webp', label: 'Front' }];
    $('fallbackStills').innerHTML = stills.map((s) => '<figure><img src="' + esc(s.image + suffix) + '" alt="' + esc(s.title || s.label || '') + '" loading="lazy"><figcaption>' + esc(s.label || '') + '</figcaption></figure>').join('');
    $('fallback').hidden = false;
  }

  // ---- menu and reel (open / close only; content comes with bind) ----------------------------
  function closeMenu() { $('menu').classList.remove('open'); $('btnMenu').setAttribute('aria-expanded', 'false'); $('btnMenu').classList.remove('active'); }
  // The menu opens just above its button. Where something else stands there (on a phone the exterior
  // panel, on any screen the open reel) it opens above that, never over it.
  function placeMenu() {
    const m = $('menu');
    m.style.bottom = '';
    if (!m.classList.contains('open')) return;
    const r = m.getBoundingClientRect();
    let top = Infinity;
    for (const el of [$('exteriorControls'), $('reelStrip')]) {
      const b = el.getBoundingClientRect();
      if (!b.width || !b.height || (el.id === 'reelStrip' && !reelOpen())) continue;
      if (b.left < r.right && r.left < b.right && b.top < r.bottom && r.top < b.bottom) top = Math.min(top, b.top);
    }
    if (top < Infinity) m.style.bottom = Math.round(innerHeight - top + 8) + 'px';
  }
  function toggleMenu() {
    const open = !$('menu').classList.contains('open');
    $('menu').classList.toggle('open', open);
    $('btnMenu').setAttribute('aria-expanded', String(open));
    $('btnMenu').classList.toggle('active', open);
    // a room name or a message still fading would stand in the menu's way on a small screen
    if (open) { chip(''); $('toast').classList.remove('show'); }
    placeMenu();
    if (open) $('menu').querySelector('button').focus();
  }
  window.addEventListener('resize', placeMenu);
  $('reel').addEventListener('transitionend', placeMenu);      // the reel slides: its place is final when it has arrived
  // Arrow keys walk the menu's items (and do not reach the view behind it); it closes when the focus
  // arrives on another control (a click elsewhere closes it through the pointerdown handler below).
  $('menu').addEventListener('keydown', (e) => {
    const items = [...$('menu').querySelectorAll('[role=menuitem]')], i = items.indexOf(document.activeElement), n = items.length;
    const to = { ArrowDown: items[(i + 1) % n], ArrowUp: items[(i - 1 + n) % n], Home: items[0], End: items[n - 1] }[e.key];
    if (!to) return;
    e.preventDefault();
    e.stopPropagation();
    to.focus();
  });
  document.addEventListener('focusin', (e) => { if (!e.target.closest('#menu,#btnMenu')) closeMenu(); });
  let onReel = null;                                   // bind() listens: the reel takes room from the picture
  // The cards' pictures are fetched when the reel first opens (or once the 3D model is in, whichever
  // comes first): until then the line belongs to what is on screen.
  function loadThumbs() { for (const i of $('reelStrip').querySelectorAll('img[data-src]')) { i.src = i.dataset.src; delete i.dataset.src; } }
  // byKey: opened from the keyboard (the focus then goes into the strip)
  function setReel(open, byKey = false) {
    const inside = $('reel').contains(document.activeElement);
    if (open) loadThumbs();
    $('reel').classList.toggle('open', open);
    document.body.classList.toggle('reel-open', open);
    $('btnRooms').classList.toggle('active', open);
    $('btnRooms').setAttribute('aria-expanded', String(open));
    syncInert();
    // the strip stands before the toolbar in the page: Tab from the button would never reach it
    const card = open && byKey ? $('reel').querySelector('.reel-card.active') || $('reel').querySelector('.reel-card') : null;
    if (card) card.focus();
    else if (!open && inside) $('btnRooms').focus({ preventScroll: true });
    placeMenu();
    if (onReel) onReel(open);
  }
  $('btnMenu').addEventListener('click', toggleMenu);
  $('btnRooms').addEventListener('click', (e) => setReel(!reelOpen(), e.detail === 0));      // detail 0 = Enter / Space
  syncInert();
  document.addEventListener('pointerdown', (e) => { if (!e.target.closest('#menu,#btnMenu')) closeMenu(); });
  window.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape' || landingOpen()) return;
    if (modalOpen()) closeModals();
    else if ($('menu').classList.contains('open')) { closeMenu(); $('btnMenu').focus(); }
    else if (reelOpen()) setReel(false);
  });
  $('btnFullscreen').addEventListener('click', async () => {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch (e) { toast('Use your browser’s full-screen option.'); }
  });
  if (!document.documentElement.requestFullscreen) $('btnFullscreen').hidden = true;
  document.addEventListener('fullscreenchange', () => {
    const on = !!document.fullscreenElement, label = on ? 'Exit fullscreen' : 'Fullscreen';
    $('btnFullscreen').dataset.tip = label;
    $('btnFullscreen').setAttribute('aria-label', label);
    $('btnFullscreen').querySelector('path').setAttribute('d', on ? 'M3 8h5V3M21 8h-5V3M16 21v-5h5M8 21v-5H3' : 'M8 3H3v5M16 3h5v5M21 16v5h-5M3 16v5h5');
  });

  // ---- chip ----------------------------------------------------------------------------------
  let chipTimer = 0;
  function chip(text, ms = 2000) {
    clearTimeout(chipTimer);
    if (!text) { $('chip').classList.remove('show'); return; }
    $('chip').textContent = text;
    $('chip').classList.add('show');
    chipTimer = setTimeout(() => $('chip').classList.remove('show'), ms);
  }

  // ---- everything that needs the viewer and the data -----------------------------------------
  // ctx: viewer, tour, measurements, modelUrl, openDesign(id), openDimensions(), onFailed(error)
  function bind(ctx) {
    const { viewer, tour } = ctx;
    if (tour.title) { $('tourTitle').textContent = tour.title; $('landingTitle').textContent = tour.title; }
    if (tour.subtitle) { $('tourSubtitle').textContent = tour.subtitle; landing.querySelector('.eyebrow').textContent = tour.subtitle; }

    // toolbar
    document.querySelectorAll('.bar [data-mode]').forEach((b) => b.addEventListener('click', () => {
      closeMenu();
      viewer.setMode(b.dataset.mode);
    }));
    $('btnDimensions').addEventListener('click', () => ctx.openDimensions());
    $('btnDesign').addEventListener('click', () => ctx.openDesign());
    $('infoDesign').addEventListener('click', () => ctx.openDesign('front'));
    $('menuHelp').addEventListener('click', () => openModal('infomodal'));
    const shot = () => { closeModals(); closeMenu(); requestAnimationFrame(() => canvas.toBlob((b) => b && downloadBlob(b, '1095-mckinley-view.png'), 'image/png')); };
    $('menuShot').addEventListener('click', shot);
    $('screenshot').addEventListener('click', shot);
    $('download').addEventListener('click', async () => {
      try {
        const r = await fetch(ctx.modelUrl);
        if (!r.ok) throw Error('HTTP ' + r.status);
        downloadBlob(new Blob([await r.arrayBuffer()], { type: 'model/gltf-binary' }), '1095-mckinley-home.glb');
      } catch (e) { toast('The 3D model could not be downloaded. Open the tour from its web address and try again.'); }
    });
    $('savePano').addEventListener('click', async () => {
      const s = viewer.state();
      const id = s.mode === 'inside' && s.sweep ? s.sweep : viewer.sweep('L0') ? 'L0' : tour.start;
      const url = viewer.panos.url(id);
      if (!url) { toast('A 360° render is not available at this location.'); return; }
      try {
        const blob = await viewer.util.fetchBlob(url);
        const ext = ((new URL(url).pathname.match(/\.(webp|jpe?g|png|avif)$/i) || [])[1] || 'webp').toLowerCase();
        downloadBlob(blob, '1095-mckinley-' + id + '-360.' + ext);
      } catch (e) { console.warn(e); toast('The 360° image could not be downloaded.'); }
    });
    const audit = (ctx.measurements && ctx.measurements.audit) || [];
    if (audit.length) $('modelAudit').innerHTML = '<table><thead><tr><th>Room</th><th>Clear width × depth</th><th>Room sq ft</th><th>Basis</th></tr></thead><tbody>' + audit.map((r) => '<tr><td>' + esc(r.name) + '</td><td>' + ft(r.width_ft) + ' × ' + ft(r.depth_ft) + '</td><td>' + r.area_sqft.toFixed(1) + '</td><td>' + esc(r.basis) + '</td></tr>').join('') + '</tbody></table>';

    // highlight reel; while it is open the dollhouse and the floor plan frame the house above it
    onReel = (open) => viewer.setInsets({ bottom: open ? $('reel').offsetHeight + 6 : 0 });
    window.addEventListener('resize', () => onReel(reelOpen()));
    const cards = new Map();
    for (const id of tour.highlights || []) {
      const s = viewer.sweep(id);
      if (!s) continue;
      const b = document.createElement('button');
      b.className = 'reel-card';
      b.dataset.sweep = id;
      b.dataset.testid = 'reel-' + id;
      b.innerHTML = '<img data-src="' + esc(viewer.panos.thumb(id)) + '" alt="" decoding="async" draggable="false"><span>' + esc(s.label) + '</span>';
      b.setAttribute('aria-label', 'Go to ' + s.label);
      b.addEventListener('click', () => {
        // A card is a view: the visitor arrives looking the way its picture shows. A place in plain view
        // or next door is a walk (turning on the way), anything farther a dissolve; from the dollhouse
        // or the floor plan the camera flies in.
        const here = viewer.state(), inside = here.mode === 'inside', from = inside ? viewer.sweep(here.sweep) : null;
        const route = inside ? viewer.path(here.sweep, id) : null;
        const near = (route && route.length <= 3) || (from && from.visible.includes(id)) || here.mode === 'dollhouse' || here.mode === 'floorplan';
        viewer.goTo(id, { reset: true, instant: !near });
      });
      $('reelStrip').appendChild(b);
      cards.set(id, b);
    }
    function markReel(id) {
      const room = viewer.sweep(id) ? viewer.sweep(id).room : null;
      const pick = cards.has(id) ? id : [...cards.keys()].find((k) => viewer.sweep(k).room === room);
      for (const [k, b] of cards) b.classList.toggle('active', viewer.mode === 'inside' && k === pick);
      const el = pick && cards.get(pick);
      if (el && reelOpen()) el.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: viewer.util.calm.matches ? 'auto' : 'smooth' });
    }

    // floor-plan room labels, placed by viewer.project() every frame; a name shows when its room is
    // large enough on screen to hold it (zooming in brings the small rooms' names out)
    const labels = (tour.rooms || []).map((r) => {
      const b = document.createElement('button');
      b.className = 'plan-label off';
      b.textContent = r.label;
      b.dataset.room = r.id;
      b.dataset.testid = 'plan-label-' + r.id;
      b.addEventListener('click', () => {
        // the room's own sweep, on its own direction; a room nobody can stand in (the laundry closet) is
        // seen from the sweep in front of it, looking at the room
        const yaw = viewer.lookInto(r, viewer.sweep(r.sweep));
        viewer.setMode('inside', yaw === undefined ? { sweep: r.sweep } : { sweep: r.sweep, yaw });
      });
      $('planLabels').appendChild(b);
      return { r, el: b, shown: false, w: 0, h: 0, fits: true };
    });
    // the wheel over a name zooms the plan under it
    $('planLabels').addEventListener('wheel', (e) => {
      e.preventDefault();
      canvas.dispatchEvent(new WheelEvent('wheel', { deltaX: e.deltaX, deltaY: e.deltaY, deltaMode: e.deltaMode, clientX: e.clientX, clientY: e.clientY, ctrlKey: e.ctrlKey, cancelable: true }));
    }, { passive: false });
    function placeLabels() {
      if (viewer.mode !== 'floorplan') return;         // the layer itself is hidden in the other modes
      for (const l of labels) {
        const [x0, z0, x1, z1] = l.r.bounds;
        const p = viewer.project([l.r.at[0], 0, l.r.at[1]], 1.0);
        const a = p && viewer.project([x0, 0, z0], 60), b = p && viewer.project([x1, 0, z1], 60);
        const width = a && b ? Math.abs(b.x - a.x) : 0, depth = a && b ? Math.abs(b.y - a.y) : 0;
        let shown = width >= 54;
        if (shown) {
          const w = Math.round(Math.max(54, width - 6));
          if (w !== l.w) { l.w = w; l.el.style.maxWidth = w + 'px'; l.h = l.el.offsetHeight; l.fits = l.el.scrollWidth <= l.el.clientWidth; }
          shown = l.h <= depth + 4 && l.fits;           // (a word wider than the room would run over its wall)
        }
        if (shown !== l.shown) { l.shown = shown; l.el.classList.toggle('off', !shown); l.el.tabIndex = shown ? 0 : -1; }
        if (shown) l.el.style.transform = 'translate(' + p.x.toFixed(1) + 'px,' + p.y.toFixed(1) + 'px) translate(-50%,-50%)';
      }
    }

    // First-run hint: how to move, shown once when the visitor first stands inside. It goes after a few
    // seconds or with the first thing the visitor does, and does not come back in this browser session.
    const HINT_MS = 6000, HINT_KEY = 'tour.hint', HINT_ENDS = ['pointerdown', 'keydown', 'wheel'];
    let hint = 0, hintTimer = 0;                       // 0 not shown yet, 1 up, 2 done
    try { if (sessionStorage.getItem(HINT_KEY)) hint = 2; } catch (e) { /* no storage: once per page load */ }
    function endHint() {
      if (hint !== 1) return;
      hint = 2;
      clearTimeout(hintTimer);
      $('hint').classList.remove('show');
      for (const type of HINT_ENDS) window.removeEventListener(type, endHint, true);
    }
    function showHint() {
      if (hint !== 0 || viewer.mode !== 'inside' || !viewer.modelReady || landingOpen() || modalOpen()) return;      // (no rings before the model is in)
      hint = 1;
      try { sessionStorage.setItem(HINT_KEY, '1'); } catch (e) { /* see above */ }
      $('hint').textContent = (matchMedia('(pointer:coarse)').matches ? 'Tap' : 'Click') + ' a ring to move · drag to look';
      $('hint').classList.add('show');
      hintTimer = setTimeout(endHint, HINT_MS);
      for (const type of HINT_ENDS) window.addEventListener(type, endHint, true);
    }

    // viewer events
    let lastRoom = null, started = false;
    function markMode(name) {
      document.querySelectorAll('.bar [data-mode]').forEach((b) => {
        const on = b.dataset.mode === name;
        b.classList.toggle('active', on);
        b.setAttribute('aria-pressed', String(on));
      });
    }
    // The 3D model on its way. Before the first picture that is the loading screen; a visitor who is
    // already inside (the first panorama needs no model) gets a small note instead, until the rings,
    // the other views and the walk between the sweeps are there.
    let loaded = 0;
    const modelText = () => 'Loading the 3D model… ' + Math.round(loaded * 100) + '%';
    function modelNote() {
      const on = started && viewer.engineState === 'loading' && !!viewer.mode;
      if (on) $('modelNote').textContent = modelText();
      $('modelNote').classList.toggle('show', on);
    }
    viewer.on('progress', (e) => { loaded = e.loaded || 0; setLoading(modelText(), loaded); modelNote(); });
    viewer.on('ready', () => { setLoading('Opening the home'); modelNote(); loadThumbs(); showHint(); });
    viewer.on('failed', (e) => { modelNote(); setBusy(false); if (ctx.onFailed) ctx.onFailed(e.error); });
    viewer.on('parked', (e) => {
      if (!viewer.mode) return;                        // nothing on screen yet: the loading screen says it
      const name = { dollhouse: 'The dollhouse', floorplan: 'The floor plan', exterior: 'The exterior' }[e.mode] || 'That view';
      toast(name + ' opens when the 3D model has loaded (' + Math.round(loaded * 100) + '%).');
    });
    // A view that is still loading (a far jump, a fly-in on a slow line): the old picture stays and a
    // small mark shows after a moment that something is on its way.
    let busyTimer = 0;
    function setBusy(on) {
      clearTimeout(busyTimer);
      if (on) busyTimer = setTimeout(() => $('wait').classList.add('show'), 350);
      else $('wait').classList.remove('show');
    }
    viewer.on('busy', (e) => setBusy(!!e.active));
    viewer.on('frame', () => {
      if (!started) { started = true; hideLoading(); modelNote(); }
      placeLabels();
    });
    viewer.on('mode', (e) => {
      document.body.dataset.mode = e.mode;
      for (const c of [...document.body.classList]) if (c.indexOf('mode-') === 0) document.body.classList.remove(c);
      document.body.classList.add('mode-' + e.mode);
      document.body.classList.remove('flying', 'fly-in');       // (a flight that goes on in the new view says so itself)
      setBusy(false);
      markMode(e.mode);
      placeMenu();                                     // the exterior panel came or went
      if (e.mode !== 'inside') { lastRoom = null; chip(''); markReel(null); endHint(); }
    });
    // A flight between two views (dollhouse.js): the toolbar shows where it goes at once, the plan's
    // names and the vignette step aside (tour.css: .flying, .fly-in) until it has arrived.
    viewer.on('flight', (e) => {
      document.body.classList.toggle('flying', !!e.active);
      document.body.classList.toggle('fly-in', !!e.active && e.to === 'inside');
      markMode(e.active ? e.to : viewer.mode);
    });
    viewer.on('sweep', (e) => {
      markReel(e.id);
      const room = e.room ? e.room.label : e.sweep.label;
      if (room !== lastRoom) { lastRoom = room; chip(room); }
      showHint();
    });
    viewer.on('transition', endHint);                  // the visitor is moving: they know how
    viewer.on('place', (e) => chip(e.label));
    viewer.on('error', (e) => { if (/^(frame|enter)/.test(e.where)) toast('Something went wrong in the 3D view; it keeps running.'); });

    // the landing page's three ways in
    choose = (choice) => {
      if (choice === 'inside') viewer.setMode('inside', { sweep: tour.start });
      else if (choice === 'floorplan') viewer.setMode('floorplan');
      else viewer.setMode('exterior', { view: 'front' });
    };
    if (chosen) { const c = chosen; chosen = null; choose(c); }
  }

  return {
    $, esc, canvas, toast, downloadBlob, ft,
    openModal, closeModals, modalOpen,
    landingOpen, openLanding, closeLanding,
    showFallback, reelOpen, bind,
  };
}
