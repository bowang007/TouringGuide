'use strict';
// The test tools themselves, no browser: the PNG codec and the panorama reference of lib/panoref.js.
// If these fail, a failing rest.test.js says nothing about the page.

const { test } = require('node:test');
const assert = require('node:assert/strict');
const panoref = require('./lib/panoref');

// A synthetic panorama whose colour tells where a pixel is: red = column, green = row, blue = 77.
function synthetic(W, H) {
  const data = new Uint8Array(W * H * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const i = (y * W + x) * 4; data[i] = Math.round(x / (W - 1) * 255); data[i + 1] = Math.round(y / (H - 1) * 255); data[i + 2] = 77; data[i + 3] = 255; }
  return { width: W, height: H, data };
}
const pixel = (img, x, y) => Array.from(img.data.subarray((y * img.width + x) * 4, (y * img.width + x) * 4 + 3));

test('PNG: what is encoded comes back the same', () => {
  const img = synthetic(97, 41);
  const back = panoref.decodePng(panoref.encodePng(img));
  assert.equal(back.width, 97);
  assert.equal(back.height, 41);
  assert.deepEqual(Buffer.from(back.data), Buffer.from(img.data));
  assert.throws(() => panoref.decodePng(Buffer.from('not a png at all, just some text to be long enough')), /not a PNG/);
});

test('reference: the middle of the view is the panorama at that yaw and pitch', () => {
  const W = 2048, H = 1024, pano = synthetic(W, H);
  for (const [yaw, pitch] of [[0, 0], [Math.PI / 2, 0], [-Math.PI / 2, 0.3], [2.5, -0.4], [-3.0, 0.1]]) {
    const view = { yaw, pitch, fovY: 1.1, width: 201, height: 121 };
    const out = panoref.extractView(pano, view);
    const got = pixel(out, 100, 60);
    // yaw 0 is the centre column, u grows clockwise (toward +yaw); pitch up is toward the top row
    const u = ((yaw / (2 * Math.PI) + 0.5) % 1 + 1) % 1, v = 0.5 - pitch / Math.PI;
    assert.ok(Math.abs(got[0] - u * 255) <= 1.5, 'column at yaw ' + yaw + ': ' + got[0] + ' vs ' + (u * 255).toFixed(1));
    assert.ok(Math.abs(got[1] - v * 255) <= 1.5, 'row at pitch ' + pitch + ': ' + got[1] + ' vs ' + (v * 255).toFixed(1));
    assert.equal(got[2], 77);
    assert.equal(out.missed, 0);
  }
});

test('reference: right of the middle is a larger yaw, above the middle a larger pitch', () => {
  const pano = synthetic(2048, 1024);
  const out = panoref.extractView(pano, { yaw: 0.4, pitch: 0, fovY: 1.0, width: 200, height: 120 });
  assert.ok(pixel(out, 180, 60)[0] > pixel(out, 20, 60)[0], 'u grows to the right');
  assert.ok(pixel(out, 100, 10)[1] < pixel(out, 100, 110)[1], 'the top of the view is higher up in the file');
});

test('reference: a cropped panorama gives the same picture as the whole file, also across the wrap column', () => {
  const W = 1024, H = 512, pano = synthetic(W, H);
  for (const view of [{ yaw: 1.0, pitch: -0.2, fovY: 1.1, width: 160, height: 100 }, { yaw: Math.PI, pitch: 0.1, fovY: 1.2, width: 160, height: 100 }, { yaw: -3.1, pitch: 0, fovY: 0.7, width: 120, height: 90 }]) {
    const rect = panoref.cropFor(view, W, H);
    assert.ok(rect.width < W && rect.height < H, 'the crop is smaller than the file');
    const data = new Uint8Array(rect.width * rect.height * 4);
    for (let y = 0; y < rect.height; y++) for (let x = 0; x < rect.width; x++) {
      const sx = (((rect.x0 + x) % W) + W) % W, sy = rect.y0 + y;
      data.set(pano.data.subarray((sy * W + sx) * 4, (sy * W + sx) * 4 + 4), (y * rect.width + x) * 4);
    }
    const crop = { fullWidth: W, fullHeight: H, x0: rect.x0, y0: rect.y0, width: rect.width, height: rect.height, data };
    const a = panoref.extractView(pano, view), b = panoref.extractView(crop, view);
    assert.equal(b.missed, 0, 'every lookup falls inside the crop');
    assert.deepEqual(Buffer.from(b.data), Buffer.from(a.data));
  }
  const pole = panoref.cropFor({ yaw: 0, pitch: 1.3, fovY: 1.2, width: 160, height: 100 }, W, H);
  assert.deepEqual([pole.x0, pole.width, pole.y0], [0, W, 0], 'a view that contains the zenith takes the full width from the top row');
});

test('projectPoint agrees with the reference camera', () => {
  const view = { yaw: 0.8, pitch: -0.3, fovY: 1.1, width: 400, height: 300 };
  const eye = [10, 5, 20];
  const d = [Math.sin(0.8) * Math.cos(-0.3), Math.sin(-0.3), -Math.cos(0.8) * Math.cos(-0.3)];
  const mid = panoref.projectPoint(view, eye, eye.map((e, i) => e + d[i] * 7));
  assert.ok(Math.abs(mid.x - 200) < 1e-6 && Math.abs(mid.y - 150) < 1e-6 && Math.abs(mid.depth - 7) < 1e-9, 'a point straight ahead is the middle of the picture');
  assert.equal(panoref.projectPoint(view, eye, eye.map((e, i) => e - d[i] * 7)), null, 'a point behind the camera has no place in it');
  const floor = panoref.projectPoint(view, eye, [10 + Math.sin(0.8) * 6, 0, 20 - Math.cos(0.8) * 6]);
  assert.ok(Math.abs(floor.x - 200) < 1e-6 && floor.y > 150, 'the floor ahead is below the middle');
});

test('compare: PSNR, masks and frame statistics', () => {
  const a = synthetic(64, 32), b = synthetic(64, 32);
  assert.equal(panoref.compare(a, b).psnr, 99);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 8; x++) b.data[(y * 64 + x) * 4] = 255 - b.data[(y * 64 + x) * 4];
  const whole = panoref.compare(a, b);
  assert.ok(whole.psnr < 30 && whole.over24 > 0.02, 'a changed corner lowers the PSNR (' + whole.psnr.toFixed(1) + ' dB)');
  const masked = panoref.compare(a, b, panoref.boxMask(64, 32, [{ x: 4, y: 4, rx: 5, ry: 5 }]));
  assert.equal(masked.psnr, 99, 'and is ignored under a mask');
  assert.ok(masked.masked > 0.03 && masked.masked < 0.08);
  const black = { width: 8, height: 8, data: new Uint8Array(8 * 8 * 4) };
  const st = panoref.frameStats(black);
  assert.deepEqual([st.mean, st.std, st.black], [0, 0, 1]);
});
