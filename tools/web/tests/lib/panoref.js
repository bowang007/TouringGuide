'use strict';
// Reference pictures for the tests, computed in Node with no native dependency.
//
// The requirement "at rest the frame equals the panorama" is checked against the PUBLISHED file: the
// view a camera standing on the sweep must see is cut out of the equirectangular image here, on the
// CPU, with nothing of the page's engine involved. Chrome is used only as the WebP decoder (a helper
// page on the tour's origin draws the needed rectangle of the file into a 2D canvas and hands it over
// as a PNG); the resampling, the PSNR and the PNG codec below are plain JavaScript.
//
// Conventions (assets/panos/manifest.json): equirectangular 2:1, top row = up (+y), centre column =
// world yaw `offset`, yaw 0 = SCENE -z (plan north), u grows clockwise seen from above. The camera of
// the inside view: yaw / pitch in radians (TOUR.getState()), vertical field of view, square pixels,
// no roll.
//
// Exports
//   decodePng(buffer) -> {width, height, data}        data = RGBA, rows top-down (8-bit RGB / RGBA, not interlaced)
//   encodePng({width, height, data}) -> Buffer
//   projectPoint(view, eye, point) -> {x, y, depth} | null             a point in feet in the picture of a view
//   cropFor(view, panoWidth, panoHeight) -> {x0, y0, width, height}   rectangle of the file a view needs
//   loadPanorama(page, url, view?) -> pano             decoded by `page` (must be same-origin with url)
//   extractView(pano, view, {linear}) -> image         view = {yaw, pitch, fovY, width, height, offset?}
//   compare(a, b, mask?) -> {psnr, meanAbs, p99, over24, masked}   over RGB; boxMask(w, h, boxes) makes a mask
//   reference(page, url, view) -> {srgb, linear}       the two references used by rest.test.js
//   frameStats(image) -> {mean, std, black, white}     luma statistics (black = share of pixels < 12)
//   meanAbsDiff(a, b), sideBySide(images), sheet(images, cols), diffImage(a, b, gain)

const zlib = require('node:zlib');

// ---- PNG ------------------------------------------------------------------------------------------
const CRC = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function decodePng(input) {
  const buf = Buffer.isBuffer(input) ? input : Buffer.from(input);
  if (buf.length < 33 || buf.readUInt32BE(0) !== 0x89504e47 || buf.readUInt32BE(4) !== 0x0d0a1a0a) throw new Error('not a PNG file');
  let pos = 8, width = 0, height = 0, depth = 0, type = 0, interlace = 0;
  const idat = [];
  while (pos + 8 <= buf.length) {
    const len = buf.readUInt32BE(pos), name = buf.toString('latin1', pos + 4, pos + 8);
    const data = buf.subarray(pos + 8, pos + 8 + len);
    if (name === 'IHDR') {
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      depth = data[8]; type = data[9]; interlace = data[12];
    } else if (name === 'IDAT') idat.push(data);
    else if (name === 'IEND') break;
    pos += 12 + len;
  }
  if (depth !== 8 || interlace !== 0 || (type !== 2 && type !== 6)) {
    throw new Error('unsupported PNG (bit depth ' + depth + ', colour type ' + type + ', interlace ' + interlace + ')');
  }
  const bpp = type === 6 ? 4 : 3, stride = width * bpp;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  if (raw.length < (stride + 1) * height) throw new Error('PNG data is truncated');
  const out = new Uint8Array(width * height * 4);
  let prev = -1;                                         // offset of the previous (already unfiltered) row in raw
  for (let y = 0; y < height; y++) {
    const f = raw[y * (stride + 1)], cur = y * (stride + 1) + 1;
    if (f === 1) {
      for (let i = bpp; i < stride; i++) raw[cur + i] = (raw[cur + i] + raw[cur + i - bpp]) & 255;
    } else if (f === 2) {
      if (prev >= 0) for (let i = 0; i < stride; i++) raw[cur + i] = (raw[cur + i] + raw[prev + i]) & 255;
    } else if (f === 3) {
      for (let i = 0; i < stride; i++) {
        const a = i >= bpp ? raw[cur + i - bpp] : 0, b = prev >= 0 ? raw[prev + i] : 0;
        raw[cur + i] = (raw[cur + i] + ((a + b) >> 1)) & 255;
      }
    } else if (f === 4) {
      for (let i = 0; i < stride; i++) {
        const a = i >= bpp ? raw[cur + i - bpp] : 0, b = prev >= 0 ? raw[prev + i] : 0, c = i >= bpp && prev >= 0 ? raw[prev + i - bpp] : 0;
        const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        raw[cur + i] = (raw[cur + i] + (pa <= pb && pa <= pc ? a : pb <= pc ? b : c)) & 255;
      }
    } else if (f !== 0) throw new Error('bad PNG filter ' + f);
    let o = y * width * 4;
    if (bpp === 4) for (let i = 0; i < stride; i++) out[o + i] = raw[cur + i];
    else for (let i = 0; i < stride; i += 3) { out[o++] = raw[cur + i]; out[o++] = raw[cur + i + 1]; out[o++] = raw[cur + i + 2]; out[o++] = 255; }
    prev = cur;
  }
  return { width, height, data: out };
}

function encodePng(image) {
  const { width, height, data } = image;
  const stride = width * 4, raw = Buffer.alloc((stride + 1) * height);
  for (let y = 0; y < height; y++) {
    raw[y * (stride + 1)] = 0;
    Buffer.from(data.buffer, data.byteOffset + y * stride, stride).copy(raw, y * (stride + 1) + 1);
  }
  const chunk = (name, body) => {
    const b = Buffer.alloc(12 + body.length);
    b.writeUInt32BE(body.length, 0);
    b.write(name, 4, 'latin1');
    body.copy(b, 8);
    b.writeUInt32BE(crc32(b.subarray(4, 8 + body.length)), 8 + body.length);
    return b;
  };
  const head = Buffer.alloc(13);
  head.writeUInt32BE(width, 0); head.writeUInt32BE(height, 4);
  head[8] = 8; head[9] = 6; head[10] = 0; head[11] = 0; head[12] = 0;
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', head), chunk('IDAT', zlib.deflateSync(raw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}

const fromDataUrl = (url) => Buffer.from(String(url).slice(String(url).indexOf(',') + 1), 'base64');

// ---- the camera -----------------------------------------------------------------------------------
// Basis of a view: forward, right, up (unit vectors) and the half extents of the image plane.
function basis(view) {
  const { yaw, pitch } = view;
  const f = [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];
  let r = [-f[2], 0, f[0]];                              // f x (0, 1, 0)
  const rl = Math.hypot(r[0], r[1], r[2]) || 1;
  r = [r[0] / rl, r[1] / rl, r[2] / rl];
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  const ty = Math.tan(view.fovY / 2), tx = ty * view.width / view.height;
  return { f, r, u, tx, ty };
}

// Where a point in feet lands in the picture of a camera standing at `eye` with this view:
// {x, y} in pixels of the view, depth (feet along the view direction); null when behind the camera.
function projectPoint(view, eye, point) {
  const { f, r, u, tx, ty } = basis(view);
  const v = [point[0] - eye[0], point[1] - eye[1], point[2] - eye[2]];
  const depth = v[0] * f[0] + v[1] * f[1] + v[2] * f[2];
  if (depth <= 0.05) return null;
  const x = (v[0] * r[0] + v[1] * r[1] + v[2] * r[2]) / depth, y = (v[0] * u[0] + v[1] * u[1] + v[2] * u[2]) / depth;
  return { x: (x / tx + 1) / 2 * view.width, y: (1 - y / ty) / 2 * view.height, depth };
}

// The rectangle of the panorama file a view needs, in file pixels, with a margin. x0 may be negative
// and x0 + width may pass the file's width: the picture wraps around there.
function cropFor(view, W, H, margin = 8) {
  const { f, r, u, tx, ty } = basis(view);
  const offset = view.offset || 0;
  const N = 64;
  let dMin = Infinity, dMax = -Infinity, vMin = Infinity, vMax = -Infinity;
  for (let j = 0; j <= N; j++) {
    for (let i = 0; i <= N; i++) {
      const x = (i / N * 2 - 1) * tx, y = (1 - j / N * 2) * ty;
      const dx = f[0] + r[0] * x + u[0] * y, dy = f[1] + r[1] * x + u[1] * y, dz = f[2] + r[2] * x + u[2] * y;
      let d = Math.atan2(dx, -dz) - view.yaw;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      const v = Math.asin(Math.max(-1, Math.min(1, dy / Math.hypot(dx, dy, dz))));
      if (d < dMin) dMin = d;
      if (d > dMax) dMax = d;
      if (v < vMin) vMin = v;
      if (v > vMax) vMax = v;
    }
  }
  const col = (d) => ((view.yaw - offset + d) / (2 * Math.PI) + 0.5) * W - 0.5;
  const row = (v) => (0.5 - v / Math.PI) * H - 0.5;
  let x0 = Math.floor(col(dMin)) - margin, x1 = Math.ceil(col(dMax)) + 1 + margin;
  const pole = Math.abs(view.pitch) + Math.atan(Math.hypot(tx, ty)) >= Math.PI / 2 - 0.02;   // a pole is in the picture
  if (pole || x1 - x0 >= W) { x0 = 0; x1 = W; }
  const y0 = pole && view.pitch > 0 ? 0 : Math.max(0, Math.floor(row(vMax)) - margin);
  const y1 = pole && view.pitch < 0 ? H : Math.min(H, Math.ceil(row(vMin)) + 1 + margin);
  return { x0, y0, width: x1 - x0, height: y1 - y0 };
}

// Decodes a panorama file in `page` (any page on the same origin as `url`) and returns the pixels a
// view needs: {fullWidth, fullHeight, x0, y0, width, height, data}. Without a view: the whole file
// (fine for 2k / 4k; an 8k file is 134 MB of pixels, so pass the view).
async function loadPanorama(page, url, view) {
  const dims = await page.evaluate(async (url) => {
    window.__panoref = window.__panoref || new Map();
    let bmp = window.__panoref.get(url);
    if (!bmp) {
      const r = await fetch(url);
      if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + url);
      bmp = await createImageBitmap(await r.blob());
      for (const [k, old] of window.__panoref) { old.close(); window.__panoref.delete(k); }      // one at a time
      window.__panoref.set(url, bmp);
    }
    return { W: bmp.width, H: bmp.height };
  }, url);
  const rect = view ? cropFor(view, dims.W, dims.H) : { x0: 0, y0: 0, width: dims.W, height: dims.H };
  const png = await page.evaluate((url, q, W) => {
    const bmp = window.__panoref.get(url);
    const c = document.createElement('canvas');
    c.width = q.width; c.height = q.height;
    const g = c.getContext('2d');
    g.imageSmoothingEnabled = false;
    let sx = ((q.x0 % W) + W) % W, dx = 0;
    while (dx < q.width) {
      const n = Math.min(q.width - dx, W - sx);
      g.drawImage(bmp, sx, q.y0, n, q.height, dx, 0, n, q.height);
      dx += n; sx = 0;
    }
    return c.toDataURL('image/png');
  }, url, rect, dims.W);
  const img = decodePng(fromDataUrl(png));
  if (img.width !== rect.width || img.height !== rect.height) throw new Error('panorama crop came back as ' + img.width + 'x' + img.height);
  return { fullWidth: dims.W, fullHeight: dims.H, x0: rect.x0, y0: rect.y0, width: img.width, height: img.height, data: img.data };
}

const TO_LINEAR = new Float32Array(256);
for (let i = 0; i < 256; i++) { const c = i / 255; TO_LINEAR[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
const toSrgb = (v) => {
  const c = v <= 0.0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
  return Math.min(255, Math.max(0, Math.round(c * 255)));
};

// The picture a camera with this view sees in the panorama: bilinear lookup, u wraps, v clamps.
// linear = true interpolates in linear light, as a GPU does with an sRGB texture; false interpolates
// the stored values (a plain RGBA texture). Returns {width, height, data, missed} (missed = lookups
// that fell outside a cropped panorama; 0 when the crop was made for this view).
function extractView(pano, view, opts = {}) {
  const { width, height } = view;
  const offset = view.offset || 0, linear = !!opts.linear;
  const { f, r, u, tx, ty } = basis(view);
  const W = pano.fullWidth || pano.width, H = pano.fullHeight || pano.height;
  const cx = pano.x0 || 0, cy = pano.y0 || 0, cw = pano.width, ch = pano.height, src = pano.data;
  const out = new Uint8Array(width * height * 4);
  const TWO_PI = 2 * Math.PI;
  let missed = 0;
  for (let j = 0; j < height; j++) {
    const y = (1 - (j + 0.5) / height * 2) * ty;
    const bx = f[0] + u[0] * y, by = f[1] + u[1] * y, bz = f[2] + u[2] * y;
    for (let i = 0; i < width; i++) {
      const x = ((i + 0.5) / width * 2 - 1) * tx;
      const dx = bx + r[0] * x, dy = by + r[1] * x, dz = bz + r[2] * x;
      let s = (Math.atan2(dx, -dz) - offset) / TWO_PI + 0.5;
      s -= Math.floor(s);
      const v = 0.5 - Math.asin(dy / Math.sqrt(dx * dx + dy * dy + dz * dz)) / Math.PI;
      const px = s * W - 0.5, py = v * H - 0.5;
      const x0 = Math.floor(px), y0 = Math.floor(py), fx = px - x0, fy = py - y0;
      let xa = (((x0 - cx) % W) + W) % W, xb = (((x0 + 1 - cx) % W) + W) % W;
      let ya = Math.min(H - 1, Math.max(0, y0)) - cy, yb = Math.min(H - 1, Math.max(0, y0 + 1)) - cy;
      if (xa >= cw || xb >= cw || ya < 0 || yb < 0 || ya >= ch || yb >= ch) {
        missed++;
        xa = Math.min(xa, cw - 1); xb = Math.min(xb, cw - 1);
        ya = Math.min(ch - 1, Math.max(0, ya)); yb = Math.min(ch - 1, Math.max(0, yb));
      }
      const a = (ya * cw + xa) * 4, b = (ya * cw + xb) * 4, c = (yb * cw + xa) * 4, d = (yb * cw + xb) * 4;
      const w00 = (1 - fx) * (1 - fy), w10 = fx * (1 - fy), w01 = (1 - fx) * fy, w11 = fx * fy;
      const o = (j * width + i) * 4;
      if (linear) {
        for (let k = 0; k < 3; k++) out[o + k] = toSrgb(TO_LINEAR[src[a + k]] * w00 + TO_LINEAR[src[b + k]] * w10 + TO_LINEAR[src[c + k]] * w01 + TO_LINEAR[src[d + k]] * w11);
      } else {
        for (let k = 0; k < 3; k++) out[o + k] = Math.round(src[a + k] * w00 + src[b + k] * w10 + src[c + k] * w01 + src[d + k] * w11);
      }
      out[o + 3] = 255;
    }
  }
  return { width, height, data: out, missed };
}

// Both references of a view of the file at `url`: interpolated on the stored values and in linear light.
async function reference(page, url, view) {
  const pano = await loadPanorama(page, url, view);
  return { srgb: extractView(pano, view, { linear: false }), linear: extractView(pano, view, { linear: true }), pano };
}

// ---- comparing pictures ---------------------------------------------------------------------------
function sameSize(a, b) {
  if (a.width !== b.width || a.height !== b.height) throw new Error('pictures differ in size: ' + a.width + 'x' + a.height + ' vs ' + b.width + 'x' + b.height);
}
// PSNR (dB), mean absolute difference, 99th percentile of the difference (0..255) and the share of
// pixels with a channel off by more than 24, over RGB. mask (Uint8Array, one entry per pixel, from
// boxMask) leaves the pixels marked 1 out; `masked` is their share of the picture.
function compare(a, b, mask) {
  sameSize(a, b);
  const A = a.data, B = b.data, hist = new Uint32Array(256);
  let se = 0, n = 0, sum = 0, over = 0, pixels = 0;
  for (let i = 0; i < A.length; i += 4) {
    if (mask && mask[i >> 2]) continue;
    pixels++;
    let worst = 0;
    for (let k = 0; k < 3; k++) {
      const d = Math.abs(A[i + k] - B[i + k]);
      se += d * d; sum += d; hist[d]++; n++;
      if (d > worst) worst = d;
    }
    if (worst > 24) over++;
  }
  const mse = se / n;
  let p99 = 0;
  for (let acc = 0; p99 < 256; p99++) { acc += hist[p99]; if (acc >= n * 0.99) break; }
  return { psnr: mse === 0 ? 99 : 10 * Math.log10(255 * 255 / mse), meanAbs: sum / n, p99, over24: over / Math.max(1, pixels), masked: 1 - pixels / (A.length / 4) };
}
// A mask for compare(): 1 inside any of the boxes [{x, y, rx, ry}] (centre and half sizes, in pixels).
function boxMask(width, height, boxes) {
  const m = new Uint8Array(width * height);
  for (const b of boxes) {
    const x0 = Math.max(0, Math.floor(b.x - b.rx)), x1 = Math.min(width - 1, Math.ceil(b.x + b.rx));
    const y0 = Math.max(0, Math.floor(b.y - b.ry)), y1 = Math.min(height - 1, Math.ceil(b.y + b.ry));
    for (let y = y0; y <= y1; y++) m.fill(1, y * width + x0, y * width + x1 + 1);
  }
  return m;
}
// A rectangle cut out of a picture.
function cropImage(image, x, y, w, h) {
  x = Math.max(0, Math.min(image.width - 1, Math.round(x))); y = Math.max(0, Math.min(image.height - 1, Math.round(y)));
  w = Math.min(w, image.width - x); h = Math.min(h, image.height - y);
  const out = new Uint8Array(w * h * 4);
  for (let j = 0; j < h; j++) out.set(image.data.subarray(((y + j) * image.width + x) * 4, ((y + j) * image.width + x + w) * 4), j * w * 4);
  return { width: w, height: h, data: out };
}
function meanAbsDiff(a, b) {
  sameSize(a, b);
  let sum = 0;
  for (let i = 0; i < a.data.length; i += 4) sum += Math.abs(a.data[i] - b.data[i]) + Math.abs(a.data[i + 1] - b.data[i + 1]) + Math.abs(a.data[i + 2] - b.data[i + 2]);
  return sum / (a.data.length / 4 * 3);
}
// Luma statistics of a picture: mean and standard deviation (0..255), share of nearly black (< 12)
// and nearly white (> 250) pixels. A blank frame has std near 0.
function frameStats(image) {
  const d = image.data, n = d.length / 4;
  let sum = 0, sq = 0, black = 0, white = 0;
  for (let i = 0; i < d.length; i += 4) {
    const l = 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2];
    sum += l; sq += l * l;
    if (l < 12) black++;
    if (l > 250) white++;
  }
  const mean = sum / n;
  return { mean, std: Math.sqrt(Math.max(0, sq / n - mean * mean)), black: black / n, white: white / n };
}
function diffImage(a, b, gain = 4) {
  sameSize(a, b);
  const out = new Uint8Array(a.data.length);
  for (let i = 0; i < out.length; i += 4) {
    for (let k = 0; k < 3; k++) out[i + k] = Math.min(255, Math.abs(a.data[i + k] - b.data[i + k]) * gain);
    out[i + 3] = 255;
  }
  return { width: a.width, height: a.height, data: out };
}
// Pictures of the same size in a grid (cols per row), for a failure report one can look at.
function sheet(images, cols = images.length) {
  const w = images[0].width, h = images[0].height, rows = Math.ceil(images.length / cols);
  const out = new Uint8Array(w * cols * h * rows * 4);
  for (let i = 3; i < out.length; i += 4) out[i] = 255;
  images.forEach((img, n) => {
    if (img.width !== w || img.height !== h) throw new Error('sheet: pictures differ in size');
    const ox = (n % cols) * w, oy = Math.floor(n / cols) * h;
    for (let y = 0; y < h; y++) out.set(img.data.subarray(y * w * 4, (y + 1) * w * 4), ((oy + y) * w * cols + ox) * 4);
  });
  return { width: w * cols, height: h * rows, data: out };
}
const sideBySide = (images) => sheet(images, images.length);

module.exports = {
  decodePng, encodePng, fromDataUrl, projectPoint, cropFor, loadPanorama, extractView, reference,
  compare, boxMask, cropImage, meanAbsDiff, frameStats, diffImage, sheet, sideBySide,
};
