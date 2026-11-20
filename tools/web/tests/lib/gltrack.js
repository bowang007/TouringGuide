'use strict';
// Counts the texture memory a page holds, from outside the page's own code: the WebGL 2 calls that
// create, size and delete textures are wrapped before any page script runs, and every live texture is
// kept in a table with its size. The numbers are computed from sizes and formats (what the driver
// really allocates is not visible to a page), mip chains count as one third on top.
//
//   await gltrack.install(page)        before the page is loaded (use it in a test's `before`)
//   await gltrack.report(page) -> {bytes, count, renderbufferBytes, panoramas: {'8k': n, '4k': n, '2k': n},
//                                  largest: [{width, height, bytes, faces, mips}], peakBytes}
//
// A panorama is recognised by its shape: a 2D texture twice as wide as high, at least 2048 px wide.

function instrument() {
  if (window.__gl || typeof WebGL2RenderingContext === 'undefined') return;
  const P = WebGL2RenderingContext.prototype;
  const BPP = {
    0x1908: 4, 0x1907: 4, 0x1909: 1, 0x1906: 1, 0x190a: 2,                 // RGBA RGB LUMINANCE ALPHA LUMINANCE_ALPHA
    0x8058: 4, 0x8c43: 4, 0x8051: 4, 0x8c41: 4, 0x8229: 1, 0x822b: 2,       // RGBA8 SRGB8_ALPHA8 RGB8 SRGB8 R8 RG8
    0x822d: 2, 0x822f: 4, 0x881a: 8, 0x881b: 8,                             // R16F RG16F RGBA16F RGB16F
    0x822e: 4, 0x8230: 8, 0x8814: 16, 0x8815: 16,                           // R32F RG32F RGBA32F RGB32F
    0x81a5: 2, 0x81a6: 4, 0x8cac: 4, 0x88f0: 4, 0x8cad: 8, 0x1902: 4, 0x84f9: 4,   // depth formats
    0x8c3a: 4, 0x8059: 4, 0x8c3d: 4, 0x8d62: 2, 0x8056: 2, 0x8057: 2,       // R11F_G11F_B10F RGB10_A2 RGB9_E5 RGB565 RGBA4 RGB5_A1
  };
  const bpp = (f) => {
    if (BPP[f]) return BPP[f];
    if ((f >= 0x83f0 && f <= 0x83f1) || f === 0x9274 || f === 0x9275) return 0.5;          // DXT1, ETC2 RGB
    if ((f >= 0x83f2 && f <= 0x83f3) || (f >= 0x9270 && f <= 0x9279) || (f >= 0x93b0 && f <= 0x93bd) || (f >= 0x8e8c && f <= 0x8e8f)) return 1;
    return 4;
  };
  const CUBE = 0x8513, FACE0 = 0x8515, T2D = 0x0de1, T3D = 0x806f, T2DA = 0x8c1a;
  const live = new Map();                               // WebGLTexture -> {target, width, height, depth, bpp, faces, mips}
  const state = new WeakMap();                          // context -> {unit, bound: Map(unit|target -> texture)}
  const rb = new Map();                                 // WebGLRenderbuffer -> bytes
  const rbBound = new WeakMap();
  const T = window.__gl = { peakBytes: 0, live };
  const st = (gl) => { let s = state.get(gl); if (!s) { s = { unit: 0, bound: new Map() }; state.set(gl, s); } return s; };
  const slot = (target) => (target >= FACE0 && target < FACE0 + 6 ? CUBE : target);
  const current = (gl, target) => st(gl).bound.get(st(gl).unit + '|' + slot(target));
  const bytesOf = (t) => t.width * t.height * Math.max(1, t.depth) * t.bpp * (t.target === CUBE ? 6 : 1) * (t.mips ? 4 / 3 : 1);
  const total = () => { let b = 0; for (const t of live.values()) b += bytesOf(t); return b; };
  const touch = () => { const b = total(); if (b > T.peakBytes) T.peakBytes = b; };
  const size = (gl, target, level, internal, width, height, depth) => {
    const tex = current(gl, target);
    if (!tex) return;
    let t = live.get(tex);
    if (!t) { t = { target: slot(target), width: 0, height: 0, depth: 1, bpp: 4, mips: false }; live.set(tex, t); }
    if (level > 0) { t.mips = true; return; }
    Object.assign(t, { width: width || 0, height: height || 0, depth: depth || 1, bpp: bpp(internal) });
    touch();
  };
  const wrap = (name, fn) => { const real = P[name]; if (typeof real === 'function') P[name] = function (...a) { try { fn(this, a); } catch (e) { /* counting never breaks the page */ } return real.apply(this, a); }; };
  const dim = (src) => (src ? [src.videoWidth || src.naturalWidth || src.displayWidth || src.width || 0, src.videoHeight || src.naturalHeight || src.displayHeight || src.height || 0] : [0, 0]);

  wrap('activeTexture', (gl, a) => { st(gl).unit = a[0]; });
  wrap('bindTexture', (gl, a) => { st(gl).bound.set(st(gl).unit + '|' + a[0], a[1]); });
  wrap('deleteTexture', (gl, a) => { live.delete(a[0]); });
  wrap('texImage2D', (gl, a) => {
    if (a.length >= 9) size(gl, a[0], a[1], a[2], a[3], a[4], 1);
    else { const [w, h] = dim(a[5]); size(gl, a[0], a[1], a[2], w, h, 1); }
  });
  wrap('texStorage2D', (gl, a) => { size(gl, a[0], 0, a[2], a[3], a[4], 1); if (a[1] > 1) { const t = live.get(current(gl, a[0])); if (t) { t.mips = true; touch(); } } });
  wrap('texImage3D', (gl, a) => { size(gl, a[0], a[1], a[2], a[3], a[4], a[5]); });
  wrap('texStorage3D', (gl, a) => { size(gl, a[0], 0, a[2], a[3], a[4], a[5]); if (a[1] > 1) { const t = live.get(current(gl, a[0])); if (t) { t.mips = true; touch(); } } });
  wrap('compressedTexImage2D', (gl, a) => { size(gl, a[0], a[1], a[2], a[3], a[4], 1); });
  wrap('copyTexImage2D', (gl, a) => { size(gl, a[0], a[1], a[2], a[5], a[6], 1); });
  wrap('generateMipmap', (gl, a) => { const t = live.get(current(gl, a[0])); if (t) { t.mips = true; touch(); } });
  wrap('bindRenderbuffer', (gl, a) => { rbBound.set(gl, a[1]); });
  wrap('deleteRenderbuffer', (gl, a) => { rb.delete(a[0]); });
  wrap('renderbufferStorage', (gl, a) => { const r = rbBound.get(gl); if (r) rb.set(r, a[2] * a[3] * bpp(a[1])); });
  wrap('renderbufferStorageMultisample', (gl, a) => { const r = rbBound.get(gl); if (r) rb.set(r, a[3] * a[4] * bpp(a[2]) * Math.max(1, a[1])); });

  T.report = () => {
    const list = [...live.values()].filter((t) => t.width > 0).map((t) => ({ width: t.width, height: t.height, depth: t.depth, cube: t.target === CUBE, mips: t.mips, bytes: Math.round(bytesOf(t)) }));
    const panoramas = { '8k': 0, '4k': 0, '2k': 0, other: 0 };
    for (const t of list) {
      if (t.cube || t.depth > 1 || t.width !== t.height * 2 || t.width < 2048) continue;
      if (t.width >= 8192) panoramas['8k']++; else if (t.width >= 4096) panoramas['4k']++; else if (t.width === 2048) panoramas['2k']++; else panoramas.other++;
    }
    let renderbufferBytes = 0;
    for (const b of rb.values()) renderbufferBytes += b;
    list.sort((a, b) => b.bytes - a.bytes);
    return { bytes: Math.round(total()), count: list.length, renderbufferBytes, panoramas, widest: list.reduce((m, t) => Math.max(m, t.width), 0), largest: list.slice(0, 8), peakBytes: Math.round(T.peakBytes) };
  };
}

const install = (page) => page.evaluateOnNewDocument(instrument);
const report = (page) => page.evaluate(() => (window.__gl ? window.__gl.report() : null));

module.exports = { install, report };
