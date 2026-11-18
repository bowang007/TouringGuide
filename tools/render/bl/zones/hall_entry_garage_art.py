"""Procedural artwork + woven-cane textures for the hall_entry_garage zone (numpy, inside Blender).

Everything here is generated from seeded noise and simple shapes: original abstract pieces in
the 1077 W McKinley palette (warm white, charcoal, ochre, sage, sand). No external images.
Painted pieces (`Paint`) keep their colour fields nearly flat and put the canvas tooth and brush
ridges into a separate height map (bump), so texture reads as relief under light, not as printed
streaks.
"""
import math

import bpy
import numpy as np

from . import hall_entry_garage_lib as L


def _hex(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def _to_lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4).astype(np.float32)


def smooth_noise(h, w, cell, rng, octaves=1):
    """Bilinear value noise in [0,1], feature size `cell` px."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cell / (2 ** o)))
        gh, gw = h // c + 3, w // c + 3
        g = rng.random((gh, gw)).astype(np.float32)
        ys = np.arange(h) / c
        xs = np.arange(w) / c
        y0 = ys.astype(int)
        x0 = xs.astype(int)
        fy = (ys - y0)[:, None]
        fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy)
        fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]
        b = g[y0][:, x0 + 1]
        cc = g[y0 + 1][:, x0]
        d = g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (cc * (1 - fx) + d * fx) * fy)
        tot += amp
        amp *= 0.5
    return out / tot


def canvas_grain(h, w, rng, strength=0.035):
    """Linen-canvas weave + fine grain multiplier around 1."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    weave = 0.5 * (np.sin(xx * 1.9) * np.sin(yy * 1.9))
    grain = rng.random((h, w)).astype(np.float32) - 0.5
    blot = smooth_noise(h, w, 60, rng, 3) - 0.5
    return 1.0 + strength * (0.6 * weave + 0.5 * grain + 0.8 * blot)


def _soft(mask_dist, edge):
    """signed distance (negative inside) -> soft 0..1 coverage."""
    return np.clip(0.5 - mask_dist / edge, 0, 1)


def aniso_noise(h, w, cy, cx, rng, octaves=2):
    """Bilinear value noise in [0,1] with separate feature sizes along y (cy px) and x (cx px):
    long thin features = bristle streaks of a brush stroke."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        sy, sx = max(1.0, cy / (2 ** o)), max(1.0, cx / (2 ** o))
        gh, gw = int(h / sy) + 3, int(w / sx) + 3
        g = rng.random((gh, gw)).astype(np.float32)
        ys, xs = np.arange(h) / sy, np.arange(w) / sx
        y0, x0 = ys.astype(int), xs.astype(int)
        fy = (ys - y0)[:, None]
        fx = (xs - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy)
        fx = fx * fx * (3 - 2 * fx)
        a, b = g[y0][:, x0], g[y0][:, x0 + 1]
        c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
        out += amp * ((a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy)
        tot += amp
        amp *= 0.5
    return out / tot


class Paint:
    """Acrylic-on-canvas painter: flat colour fields (tiny tonal variation only) and a separate
    height map carrying the canvas tooth and the brush ridges, so the texture shows up as real
    relief under the hall lights instead of as printed streaks."""

    def __init__(self, w, h, ground, seed):
        self.w, self.h = w, h
        self.rng = np.random.default_rng(seed)
        r = self.rng
        tooth = smooth_noise(h, w, 2.2, r, 2) - 0.5
        mott = smooth_noise(h, w, 160, r, 3) - 0.5
        self.img = np.ones((h, w, 3), np.float32) * _hex(ground) * (1 + 0.010 * tooth + 0.018 * mott)[..., None]
        self.hgt = 0.30 + 0.22 * tooth + 0.06 * (aniso_noise(h, w, 3, 26, r) - 0.5)

    def stroke_tex(self, direction):
        h, w, r = self.h, self.w, self.rng
        if direction == 'h':
            return aniso_noise(h, w, 2.5, 34, r, 3)
        return aniso_noise(h, w, 34, 2.5, r, 3)

    def fill(self, cov, color, direction='h', tone=0.025, ridge=0.55, body=0.18):
        st = self.stroke_tex(direction)
        lo = smooth_noise(self.h, self.w, 70, self.rng, 2) - 0.5
        c = _hex(color)[None, None] * (1 + tone * (st - 0.5) + 0.02 * lo)[..., None]
        m = cov[..., None]
        self.img = self.img * (1 - m) + c * m
        # paint body sits on the canvas; ridges follow the brush direction; a slight lip at the edge
        edge = np.clip(cov * (1 - cov) * 4, 0, 1)
        self.hgt = self.hgt * (1 - 0.6 * cov) + cov * (body + 0.42 + ridge * 0.35 * (st - 0.5)) + 0.08 * edge

    def result(self):
        return _to_lin(np.clip(self.img, 0, 1)), np.clip(self.hgt, 0, 1)


# ----------------------------------------------------------------------------- pieces
def art_scribble(w=900, h=1180, seed=7):
    """Black continuous looping brush line on a warm white canvas (gestural line art)."""
    rng = np.random.default_rng(seed)
    bg = _hex('#efebe4')
    img = np.ones((h, w, 3), np.float32) * bg
    img *= canvas_grain(h, w, rng, 0.03)[..., None]
    ink = np.zeros((h, w), np.float32)
    t = np.linspace(0, 1, 9000)
    # sum of sinusoids -> a few big loose loops
    x = 0.50 + 0.26 * np.sin(2 * np.pi * (1.0 * t) + 0.4) + 0.12 * np.sin(2 * np.pi * (3.0 * t) + 1.7) \
        + 0.035 * np.sin(2 * np.pi * 7 * t + 0.3)
    y = 0.52 + 0.30 * np.sin(2 * np.pi * (1.5 * t) + 2.1) + 0.10 * np.cos(2 * np.pi * (4.0 * t) + 0.2) \
        + 0.03 * np.sin(2 * np.pi * 9 * t + 1.1)
    x = 0.14 + 0.72 * (x - x.min()) / (x.max() - x.min())
    y = 0.12 + 0.76 * (y - y.min()) / (y.max() - y.min())
    px, py = x * w, y * h
    taper = np.clip(np.minimum(t, 1 - t) / 0.04, 0.25, 1.0)
    rad = (5.0 + 2.2 * np.sin(2 * np.pi * 5 * t + 0.6) + 1.2 * np.sin(2 * np.pi * 13 * t)) * taper
    R = 10
    oy, ox = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
    for cx, cy, r in zip(px, py, rad):
        ix, iy = int(cx), int(cy)
        if ix < R or iy < R or ix >= w - R or iy >= h - R:
            continue
        d = np.sqrt((ox + ix - cx) ** 2 + (oy + iy - cy) ** 2)
        cov = np.clip(r + 0.7 - d, 0, 1)
        sl = ink[iy - R:iy + R + 1, ix - R:ix + R + 1]
        np.maximum(sl, cov, out=sl)
    dry = smooth_noise(h, w, 6, rng, 2)
    ink *= np.clip(0.75 + 0.6 * dry, 0, 1)
    col = _hex('#1c1b1a')
    img = img * (1 - ink[..., None]) + col * ink[..., None]
    tooth = smooth_noise(h, w, 2.2, rng, 2) - 0.5
    hgt = np.clip(0.3 + 0.2 * tooth + 0.45 * ink, 0, 1)
    return _to_lin(np.clip(img, 0, 1)), hgt


def art_arches(w=1100, h=1450, seed=11):
    """Mid-century abstract: ochre arch, charcoal half disc, terracotta dot, sage block on cream."""
    P = Paint(w, h, '#ece6da', seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # sage block lower right
    d = np.maximum(np.abs(xx - 0.66 * w) - 0.22 * w, np.abs(yy - 0.73 * h) - 0.17 * h)
    P.fill(_soft(d, 1.6), '#a3aa95', 'h')
    # ochre arch (thick ring, upper half + legs)
    cx, cy = 0.42 * w, 0.50 * h
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ring = np.abs(r - 0.25 * w) - 0.075 * w
    arch = np.where(yy < cy, ring, np.minimum(np.abs(np.abs(xx - cx) - 0.25 * w) - 0.075 * w, 1e3))
    arch = np.where(yy > 0.80 * h, 1e3, arch)
    P.fill(_soft(arch, 1.6), '#c7a05a', 'v')
    # charcoal half disc on the base line
    r2 = np.sqrt((xx - 0.30 * w) ** 2 + (yy - 0.80 * h) ** 2)
    hd = np.where(yy <= 0.80 * h, r2 - 0.17 * w, 1e3)
    P.fill(_soft(hd, 1.6), '#33312e', 'h')
    # small terracotta dot
    r3 = np.sqrt((xx - 0.73 * w) ** 2 + (yy - 0.24 * h) ** 2) - 0.07 * w
    P.fill(_soft(r3, 1.6), '#b26a50', 'v')
    # thin charcoal base line
    ln = np.maximum(np.abs(yy - 0.80 * h) - 2.5, np.abs(xx - 0.5 * w) - 0.40 * w)
    P.fill(_soft(ln, 1.2), '#33312e', 'h', ridge=0.2)
    return P.result()


def art_horizon(w=1700, h=1130, seed=23):
    """Horizontal abstract landscape: layered sand / sage / charcoal bands with soft brushed edges."""
    P = Paint(w, h, '#eee9df', seed)
    rng = P.rng
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    # a barely-there warm wash in the sky so the top is not a flat blank
    sky = np.clip((yy / h - 0.15) / 0.35, 0, 1) * 0.35
    P.fill(sky, '#e6dccb', 'h', tone=0.012, ridge=0.25, body=0.0)
    layers = [
        (0.46, 0.035, 2.0, '#dacbae'),   # sand haze
        (0.58, 0.045, 1.4, '#adb29d'),   # pale sage hills
        (0.68, 0.035, 2.6, '#828c77'),   # deep sage
        (0.79, 0.025, 3.3, '#3d3c39'),   # charcoal ground
        (0.90, 0.018, 1.7, '#c8a462'),   # ochre foreground stroke
    ]
    for base, amp, freq, color in layers:
        ph = rng.random() * 6.28
        edge = (base + amp * np.sin(xx / w * 2 * np.pi * freq + ph) +
                0.4 * amp * np.sin(xx / w * 2 * np.pi * freq * 2.7 + ph * 1.7)) * h
        jag = (smooth_noise(h, w, 30, rng, 3) - 0.5) * 0.016 * h
        mask = np.clip((yy - edge + jag) / 2.5 + 0.5, 0, 1)
        P.fill(mask, color, 'h')
    # ochre sun
    r = np.sqrt((xx - 0.71 * w) ** 2 + (yy - 0.30 * h) ** 2) - 0.065 * h
    P.fill(_soft(r, 1.6), '#c2934a', 'v')
    return P.result()


def cane_tile(n=256):
    """One period of 6-way woven rattan cane: (color sRGB-linear, height) arrays."""
    yy, xx = (np.mgrid[0:n, 0:n].astype(np.float32) + 0.5) / n
    def strand(t, width):
        d = np.abs((t % 1.0) - 0.5) * 2                     # 0 at strand centre
        prof = np.clip(1 - (d / width) ** 2, 0, 1)
        return prof
    w = 0.30
    sh = strand(yy + 0.5, w)                    # horizontal pair
    sv = strand(xx + 0.5, w)
    s1 = strand((xx + yy), w * 0.85)            # diagonals through the crossings
    s2 = strand((xx - yy), w * 0.85)
    height = np.maximum.reduce([sh * 1.0, sv * 0.95, s1 * 0.8, s2 * 0.85])
    cover = np.clip(height * 4, 0, 1)
    cane = _hex('#c7a36b')
    dark = _hex('#1e1712')
    shade = 0.70 + 0.30 * height
    col = dark[None, None] * (1 - cover[..., None]) + (cane[None, None] * shade[..., None]) * cover[..., None]
    return _to_lin(np.clip(col, 0, 1)), np.repeat(height[..., None], 3, 2)


# ----------------------------------------------------------------------------- materials
def art_material(name, kind):
    full = L.PFX + 'art_' + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    col, hgt = {'scribble': art_scribble, 'arches': art_arches, 'horizon': art_horizon}[kind]()
    img = L.image_from_array('img_' + name, col)
    ih = L.image_from_array('img_' + name + '_h', np.repeat(hgt[..., None], 3, 2))
    m = L.image_material('art_' + name, img, rough=0.8, bump_img=ih, bump_strength=0.35)
    for n in m.node_tree.nodes:
        if n.type == 'BUMP':
            n.inputs['Distance'].default_value = 0.0012
    return m


def cane_material():
    full = L.PFX + 'cane'
    m = bpy.data.materials.get(full)
    if m:
        return m
    col, hgt = cane_tile()
    ic = L.image_from_array('img_cane', col)
    ih = L.image_from_array('img_cane_h', hgt)
    period_m = 0.55 * 0.0254 * 1.0          # ~0.55in hole pitch
    s = 1.0 / period_m
    return L.image_material('cane', ic, rough=0.6, bump_img=ih, bump_strength=0.6,
                            mapping='OBJECT', scale=(s, s, 1))


def plaster_relief(w=1050, h=1400, seed=31):
    """Hand-worked plaster relief: vertical columns of short palette-knife strokes laid top to bottom.
    Each stroke starts thick with a knife lip, carries raised side ridges and drag streaks, and thins
    out into a dragged tail that the next stroke overlaps. Returns a height map 0..1 (row 0 = top)."""
    rng = np.random.default_rng(seed)
    hgt = 0.16 + 0.05 * (smooth_noise(h, w, 40, rng, 3) - 0.5)
    margin = int(0.06 * w)
    cols = 15
    pitch = (w - 2 * margin) / cols

    def sstep(e0, e1, x):
        t = np.clip((x - e0) / (e1 - e0), 0, 1)
        return t * t * (3 - 2 * t)

    for c in range(cols):
        cx0 = margin + (c + 0.5) * pitch
        y = margin * 0.7 + rng.uniform(-25, 35)
        while y < h - margin * 0.7:
            L = rng.uniform(95, 160)                      # stroke length px (~3.5-5.5in)
            W = pitch * rng.uniform(0.95, 1.15)           # stroke width (overlaps neighbours a little)
            cx = cx0 + rng.normal(0, pitch * 0.06)
            ang = rng.normal(0, 0.05)
            y0, y1 = int(max(0, y - 6)), int(min(h, y + L + 6))
            x0, x1 = int(max(0, cx - W)), int(min(w, cx + W))
            if y1 <= y0 + 6:
                break
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            v = (yy - y) / L * 2 - 1                      # -1 start .. +1 end
            tw = 1 - 0.22 * (v + 1) / 2                   # narrows toward the tail
            uu = np.abs(((xx - cx) - ang * (yy - y - L / 2)) / (W / 2)) / tw
            # rounded head: an elliptical cap over the first 30% of the stroke
            cap = np.clip((-0.4 - v) / 0.6, 0, None)
            uu = np.sqrt(uu ** 2 + cap ** 2)
            e = 1 - sstep(0.15, 1.0, v)                   # 1 = full body, 0 = dragged-out tail
            cov = np.clip((1.0 - uu) / 0.14, 0, 1) * (v < 1.0)
            ridge = np.exp(-((uu - 0.82) / 0.17) ** 2) * (0.18 + 0.2 * e)
            lip = 0.12 * np.exp(-((uu - 0.8) / 0.15) ** 2) * (cap > 0)
            streak = (0.08 + 0.1 * (1 - e)) * (aniso_noise(y1 - y0, x1 - x0, 26, 2.0, rng, 2) - 0.5)
            hs = 0.36 + 0.22 * e * (1 - 0.6 * uu ** 2) + ridge + lip + streak
            alpha = cov * (0.35 + 0.65 * e)
            win = hgt[y0:y1, x0:x1]
            hgt[y0:y1, x0:x1] = win * (1 - alpha) + np.maximum(hs, win) * alpha
            y += L * rng.uniform(0.62, 0.78)
    hgt += 0.025 * (smooth_noise(h, w, 2.5, rng, 2) - 0.5)
    return np.clip(hgt, 0, 1).astype(np.float32)


def plaster_relief_material():
    """Textured white plaster relief canvas: grooves slightly darker + strong bump."""
    full = L.PFX + 'art_plaster'
    m = bpy.data.materials.get(full)
    if m:
        return m
    hgt = plaster_relief()
    base = _hex('#f4f2ed')
    col = base[None, None] * (0.90 + 0.10 * hgt[..., None])
    ic = L.image_from_array('img_plaster', _to_lin(np.clip(col, 0, 1)))
    ih = L.image_from_array('img_plaster_h', np.repeat(hgt[..., None], 3, 2))
    m = L.image_material('art_plaster', ic, rough=0.92, bump_img=ih, bump_strength=0.55)
    nt = m.node_tree
    for n in nt.nodes:
        if n.type == 'BUMP':
            n.inputs['Distance'].default_value = 0.006
    return m
