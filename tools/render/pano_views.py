#!/usr/bin/env python3
"""Cut rectilinear views out of an equirectangular panorama (app convention: centre column =
yaw 0 = SCENE -z; u increases clockwise) and lay them out as a contact sheet for review.

Usage:
  python3 tools/render/pano_views.py PANO.png [--yaws 0,90,180,270] [--base-yaw RAD] \
      [--fov 90] [--pitch -5] [--size 800x500] [--out sheet.png]
Yaws are degrees relative to --base-yaw (radians, e.g. the node's yaw). Also importable:
  views(img, yaws_deg, fov_deg, pitch_deg, size) -> list of PIL images
"""
import argparse
import math

import numpy as np
from PIL import Image, ImageDraw


def view(pano, yaw, pitch, fov_deg, w, h):
    """Rectilinear view; yaw/pitch in radians (app convention)."""
    arr = np.asarray(pano)
    H, W = arr.shape[:2]
    f = (w / 2) / math.tan(math.radians(fov_deg) / 2)
    xs = (np.arange(w) - w / 2 + 0.5)
    ys = (np.arange(h) - h / 2 + 0.5)
    X, Y = np.meshgrid(xs, ys)
    # camera space: right = +x, up = +y, forward = +z
    d = np.stack([X, -Y, np.full_like(X, f)], -1)
    d /= np.linalg.norm(d, axis=-1, keepdims=True)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    # pitch about camera x, then yaw; world: x east, y up, z south; forward(yaw)=(sin y, 0, -cos y)
    dx, dy, dz = d[..., 0], d[..., 1] * cp + d[..., 2] * sp, -d[..., 1] * sp + d[..., 2] * cp
    wx = dx * cy + dz * sy
    wz = dx * sy - dz * cy
    wy = dy
    u = (np.arctan2(wx, -wz) / (2 * math.pi) + 0.5) % 1.0
    v = 0.5 - np.arcsin(np.clip(wy, -1, 1)) / math.pi
    px = np.clip((u * W).astype(int), 0, W - 1)
    py = np.clip((v * H).astype(int), 0, H - 1)
    return Image.fromarray(arr[py, px])


def views(pano, yaws_deg, fov_deg=90, pitch_deg=-5, size=(800, 500), base_yaw=0.0):
    return [view(pano, base_yaw + math.radians(y), math.radians(pitch_deg), fov_deg, *size) for y in yaws_deg]


def sheet(imgs, labels, cols=2):
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    s = Image.new('RGB', (w * cols, h * rows), 'white')
    dr = ImageDraw.Draw(s)
    for i, (im, lab) in enumerate(zip(imgs, labels)):
        x, y = (i % cols) * w, (i // cols) * h
        s.paste(im, (x, y))
        dr.rectangle([x, y, x + 9 * len(lab) + 10, y + 18], fill='black')
        dr.text((x + 5, y + 3), lab, fill='white')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pano')
    ap.add_argument('--yaws', default='0,90,180,270')
    ap.add_argument('--base-yaw', type=float, default=0.0)
    ap.add_argument('--fov', type=float, default=90)
    ap.add_argument('--pitch', type=float, default=-5)
    ap.add_argument('--size', default='800x500')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    pano = Image.open(a.pano).convert('RGB')
    yaws = [float(y) for y in a.yaws.split(',')]
    w, h = (int(x) for x in a.size.split('x'))
    ims = views(pano, yaws, a.fov, a.pitch, (w, h), a.base_yaw)
    out = a.out or a.pano.rsplit('.', 1)[0] + '_sheet.png'
    sheet(ims, [f'yaw {y:+.0f} deg' for y in yaws]).save(out)
    print(out)


if __name__ == '__main__':
    main()
