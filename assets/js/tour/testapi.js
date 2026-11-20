// window.TOUR: the page's contract with the browser tests (tools/web/tests) and the console.
//
//   getState()            {engine: 'loading'|'ready'|'failed', mode: 'landing'|'exterior'|'inside'|'dollhouse'|
//                          'floorplan', sweep, transition: null|{from, to, t, route, target} (from / to = the
//                          hop under way, t = how far along it, target = where the move ends), yaw, pitch
//                          (radians), fov (degrees, vertical, landscape value), vfov (degrees, as drawn),
//                          pano: {id, level (the one on screen)}, resting (the frame is the pure panorama),
//                          hover (ring under the cursor), reticle (shown), sweeps: N, frame (animation
//                          ticks), draws (frames drawn: stands still when nothing changes), size, reel,
//                          modal, and the active mode's own state under its name, e.g.
//                          exterior: {view, photo: {frames, on, at, weight, zoom, settling}, theta, phi, ...}}
//   goTo(id, opts)        animated move (a glide, a flight through the sweeps between, or a quick fade when
//                         far / opts.instant); Promise resolved on arrival (true) or when replaced (false)
//   jumpTo(id, opts)      cut; Promise resolved when the panorama is on screen
//   setLook(yaw, pitch)   radians; yaw 0 = north (-z), positive clockwise from above
//   setMode(mode, opts)   'inside' | 'dollhouse' | 'floorplan' | 'exterior' (| 'landing'); Promise
//   clickAt(x, y)         a click at CSS pixels of the canvas, as the active mode gets it; returns what it
//                         did (inside: the sweep it goes to, or false)
//   sweeps()              [{id, label, room, p, links, visible}]
//   project(id | [x,y,z]) {x, y} in CSS pixels. A sweep id inside = its floor ring as the visitor sees it:
//                         null when the ring is not shown from here, off screen or hidden behind something.
//                         A point in feet, or a sweep id in the other modes = plain projection.
//   rings()               inside: [{id, x, y, rx, ry, seen (0..1 not hidden), alpha}] of the rings on screen
//   reticle()             inside: {x, y, point, normal, cls, radius} of the cursor ring, or null
//   pick(x, y)            {point, normal, distance, cls} of the surface under a CSS-pixel point, or null
//   setOverlay(on)        inside: rings and reticle on / off (to compare the frame with the panorama file)
//   pose(a, b, e)         inside: hold the camera at fraction e of the hop a -> b, drawn as a move draws it
//                         (Promise, resolved when both panoramas are loaded); pose() lets go
//   nextFrame(n = 2)      Promise resolved after n animation ticks (the view has been redrawn if it had to be)
//   screenshot()          PNG data URL of the canvas
//   exterior(view), exteriorFrame(id)   exterior presets / a frame of assets/exterior/manifest.json
//   viewer                the viewer object itself (debugging)

export function createTestApi({ viewer, ui, exterior }) {
  const none = { engine: 'failed', mode: 'landing', sweep: null, transition: null, yaw: 0, pitch: 0, fov: 0, pano: { id: null, level: null }, sweeps: 0 };
  const api = {
    getState() {
      const s = viewer ? viewer.state() : Object.assign({}, none);
      if (ui.landingOpen() || !s.mode) s.mode = 'landing';
      s.reel = ui.reelOpen();
      const m = document.querySelector('.modal.open');
      s.modal = m ? m.id : null;
      return s;
    },
    goTo: (id, o) => (viewer ? viewer.goTo(id, o) : Promise.resolve(false)),
    jumpTo: (id, o) => (viewer ? viewer.jumpTo(id, o) : Promise.resolve(false)),
    setLook: (yaw, pitch) => { if (viewer) viewer.setLook(yaw, pitch); },
    setMode(mode, o) {
      if (!viewer) return Promise.resolve(false);
      if (mode === 'landing') { ui.openLanding(); return Promise.resolve(true); }
      ui.closeLanding();
      ui.closeModals();
      return viewer.setMode(mode, o);
    },
    clickAt: (x, y) => (viewer ? viewer.clickAt(x, y) : false),
    sweeps: () => (viewer ? viewer.sweeps.map((s) => ({ id: s.id, label: s.label, room: s.room, p: s.p.slice(), links: s.links.slice(), visible: s.visible.slice() })) : []),
    project(point) { const p = viewer ? viewer.project(point) : null; return p ? { x: p.x, y: p.y } : null; },
    rings: () => (viewer && viewer.mode === 'inside' ? viewer.controllers.inside.rings() : []),
    reticle: () => (viewer && viewer.mode === 'inside' ? viewer.controllers.inside.reticle() : null),
    pick(x, y) { const h = viewer ? viewer.pick(x, y) : null; return h ? { point: h.point.slice(), normal: h.normal.slice(), distance: h.distance, cls: h.cls } : null; },
    setOverlay: (on) => { if (viewer) viewer.controllers.inside.setOverlay(on); },
    pose: (a, b, e) => (viewer ? viewer.controllers.inside.pose(a, b, e) : Promise.resolve(false)),
    nextFrame: (n = 2) => new Promise((resolve) => { const step = () => (n-- > 0 ? requestAnimationFrame(step) : resolve(true)); step(); }),
    screenshot: () => ui.canvas.toDataURL('image/png'),
    exterior(view = 'front') { return api.setMode('exterior', { view }); },
    exteriorFrame(id) {
      if (!viewer || !exterior) return false;
      if (viewer.mode !== 'exterior') { ui.closeLanding(); viewer.setMode('exterior'); }
      return exterior.frameTo(id);
    },
    viewer,
  };
  window.TOUR = api;
  return api;
}
