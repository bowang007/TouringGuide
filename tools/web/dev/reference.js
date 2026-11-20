// Independent reference for the rest-state test: the view a camera on a sweep must see, taken
// straight from the panorama file (decoded by the browser, resampled here on the CPU). Nothing of the
// engine is used. Conventions (assets/panos/manifest.json): equirectangular 2:1, top row = up, centre
// column = world yaw `offset`, yaw 0 = SCENE -z, clockwise seen from above.

const TO_LINEAR = new Float32Array(256);
for (let i = 0; i < 256; i++) {
  const c = i / 255;
  TO_LINEAR[i] = c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}
const toSrgb = (v) => {
  const c = v <= 0.0031308 ? v * 12.92 : 1.055 * Math.pow(v, 1 / 2.4) - 0.055;
  return Math.min(255, Math.max(0, Math.round(c * 255)));
};

export async function panoPixels(url) {
  const blob = await (await fetch(url)).blob();
  const bmp = await createImageBitmap(blob);
  const c = new OffscreenCanvas(bmp.width, bmp.height);
  const g = c.getContext('2d', { willReadFrequently: true });
  g.drawImage(bmp, 0, 0);
  const d = g.getImageData(0, 0, bmp.width, bmp.height);
  bmp.close();
  return { width: d.width, height: d.height, data: d.data };
}

// view: {yaw, pitch (radians), fovY (radians), width, height, offset = 0}. Returns RGBA, rows top-down.
// Bilinear in linear light, as a GPU does with an sRGB texture (the panorama is magnified in the test).
export function extractView(pano, view) {
  const { yaw, pitch, fovY, width, height } = view;
  const offset = view.offset || 0;
  const out = new Uint8ClampedArray(width * height * 4);
  const f = [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];
  // right = f x up, up' = right x f
  let r = [f[1] * 0 - f[2] * 1, f[2] * 0 - f[0] * 0, f[0] * 1 - f[1] * 0];
  const rl = Math.hypot(r[0], r[1], r[2]);
  r = r.map((v) => v / rl);
  const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
  const ty = Math.tan(fovY / 2), tx = ty * width / height;
  const W = pano.width, H = pano.height, src = pano.data;
  for (let j = 0; j < height; j++) {
    const y = (1 - (j + 0.5) / height * 2) * ty;
    for (let i = 0; i < width; i++) {
      const x = ((i + 0.5) / width * 2 - 1) * tx;
      let dx = f[0] + r[0] * x + u[0] * y, dy = f[1] + r[1] * x + u[1] * y, dz = f[2] + r[2] * x + u[2] * y;
      const l = Math.hypot(dx, dy, dz);
      dx /= l; dy /= l; dz /= l;
      let s = (Math.atan2(dx, -dz) - offset) / (2 * Math.PI) + 0.5;
      s -= Math.floor(s);
      const v = 0.5 - Math.asin(Math.min(1, Math.max(-1, dy))) / Math.PI;
      const px = s * W - 0.5, py = v * H - 0.5;
      const x0 = Math.floor(px), y0 = Math.floor(py);
      const fx = px - x0, fy = py - y0;
      const xa = ((x0 % W) + W) % W, xb = (xa + 1) % W;
      const ya = Math.min(H - 1, Math.max(0, y0)), yb = Math.min(H - 1, Math.max(0, y0 + 1));
      const o = (j * width + i) * 4;
      for (let k = 0; k < 3; k++) {
        const a = TO_LINEAR[src[(ya * W + xa) * 4 + k]], b = TO_LINEAR[src[(ya * W + xb) * 4 + k]];
        const c = TO_LINEAR[src[(yb * W + xa) * 4 + k]], d = TO_LINEAR[src[(yb * W + xb) * 4 + k]];
        out[o + k] = toSrgb((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy);
      }
      out[o + 3] = 255;
    }
  }
  return out;
}

// PSNR over RGB of two RGBA buffers of the same size, in dB.
export function psnr(a, b) {
  let se = 0, n = 0;
  for (let i = 0; i < a.length; i += 4) {
    for (let k = 0; k < 3; k++) { const d = a[i + k] - b[i + k]; se += d * d; n++; }
  }
  const mse = se / n;
  return mse === 0 ? 99 : 10 * Math.log10(255 * 255 / mse);
}
