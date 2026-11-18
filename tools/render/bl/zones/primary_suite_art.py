"""Procedural abstract painting for the primary suite (original, generated at build time).

paint(): the hero canvas above the bed, a neutral colour-field abstract (oat and greige fields with
ragged, scumbled dry-brush edges, white overpaint, a charcoal bar, a small ochre patch, graphite
lines, canvas tooth). paint_wash(): a small watercolour-on-paper print (two glazed arches, an ochre
sun, a charcoal ground line) for the matted east-wall frame. Pure numpy so it runs inside Blender;
images are packed into the .blend. No reference imagery is used.
"""
import math

import numpy as np


def _value_noise(h, w, cells, rng):
    g = rng.random((cells + 2, int(cells * w / h) + 3))
    ys = np.linspace(0, cells, h)
    xs = np.linspace(0, g.shape[1] - 3, w)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    ty = ys - y0
    tx = xs - x0
    ty = ty * ty * (3 - 2 * ty)
    tx = tx * tx * (3 - 2 * tx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * tx[None, :]
    bot = c + (d - c) * tx[None, :]
    return top + (bot - top) * ty[:, None]


def fbm(h, w, base_cells, octaves, rng, gain=0.5):
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    cells = base_cells
    for _ in range(octaves):
        out += amp * _value_noise(h, w, cells, rng)
        tot += amp
        amp *= gain
        cells *= 2
    return out / tot


def brushy(h, w, rng, horizontal=True, stretch=14, cells=55, octaves=4):
    """Multi-octave dry-brush streak texture in [0,1]: fbm that is fine across the stroke and
    stretched `stretch`x along it (horizontal or vertical strokes)."""
    if horizontal:
        n = fbm(h, max(4, w // stretch), cells, octaves, rng)
        xs = np.linspace(0, n.shape[1] - 1.001, w)
        i0 = xs.astype(int)
        t = xs - i0
        return n[:, i0] * (1 - t) + n[:, i0 + 1] * t
    return brushy(w, h, rng, True, stretch, cells, octaves).T


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _catmull(pts, n):
    pts = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = (np.array(p, float) for p in pts[i - 1:i + 3])
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(np.array(pts[-2], float))
    return np.array(out)


def brush_stroke(cov, pts, width, rng, dry=0.35, taper=(0.25, 0.4), bristles=None, pressure=None):
    """Stamp a dry-brush stroke along a catmull-rom path into coverage array `cov` (H, W)."""
    H, W = cov.shape
    path = _catmull(pts, 60)
    seg = np.diff(path, axis=0)
    lens = np.hypot(seg[:, 0], seg[:, 1])
    total = lens.sum()
    if bristles is None:
        b = rng.random(160)
        k = np.ones(3) / 3
        bristles = np.convolve(b, k, mode='same')
    acc = 0.0
    step = max(1.0, width * 0.08)
    i = 0
    pos = path[0].copy()
    while i < len(seg):
        if lens[i] < 1e-6:
            i += 1
            continue
        d = seg[i] / lens[i]
        nrm = np.array([-d[1], d[0]])
        t = acc / total
        tw = min(1.0, t / taper[0]) if taper[0] > 0 else 1.0
        tw = min(tw, (1 - t) / taper[1]) if taper[1] > 0 else tw
        tw = max(tw, 0.08) ** 0.6
        pw = pressure(t) if pressure else 1.0
        r = width * 0.5 * tw * pw
        x0, x1 = int(max(0, pos[0] - r - 2)), int(min(W, pos[0] + r + 3))
        y0, y1 = int(max(0, pos[1] - r - 2)), int(min(H, pos[1] + r + 3))
        if x1 > x0 and y1 > y0:
            yy, xx = np.mgrid[y0:y1, x0:x1]
            dx, dy = xx - pos[0], yy - pos[1]
            perp = (dx * nrm[0] + dy * nrm[1]) / max(r, 1e-3)
            along = dx * d[0] + dy * d[1]
            disc = (np.abs(perp) <= 1.0) & (np.abs(along) <= step * 1.2)
            bi = np.clip(((perp + 1) * 0.5 * (len(bristles) - 1)).astype(int), 0, len(bristles) - 1)
            thr = dry * (0.4 + 1.2 * t ** 2)
            paint = _smooth(thr, thr + 0.18, bristles[bi]) * (1 - _smooth(0.85, 1.0, np.abs(perp)))
            region = cov[y0:y1, x0:x1]
            np.maximum(region, np.where(disc, paint, 0), out=region)
        acc += step
        pos = pos + d * step
        while i < len(seg) and np.dot(pos - path[i], seg[i]) > lens[i] ** 2:
            i += 1
        if i < len(seg):
            # snap to segment
            proj = np.dot(pos - path[i], seg[i]) / lens[i] ** 2
            pos = path[i] + seg[i] * max(0.0, proj)
    return cov


def _srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def paint(w=1800, h=1000, seed=7):
    """Large neutral colour-field abstract (acrylic on canvas): overlapping oat and greige fields with
    ragged, scumbled edges, a white overpaint, one heavy charcoal bar, a small ochre patch and a few
    graphite lines. Returns float32 RGBA (h, w, 4) in sRGB values, top row first."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    u, v = xx / w, yy / h
    img = np.ones((h, w, 3)) * np.array([0.928, 0.910, 0.868])
    mott = fbm(h, w, 3, 5, rng)
    img *= (0.975 + 0.05 * (mott[..., None] - 0.5))

    def lay(color, alpha):
        nonlocal img
        img = img * (1 - alpha[..., None]) + np.array(color) * alpha[..., None]

    def field(x0, x1, y0, y1, color, op, horizontal=True, rag=0.045, edge=0.022, scumble=0.3, tone=0.06):
        en = fbm(h, w, 7, 5, rng)
        st = brushy(h, w, rng, horizontal)
        sdf = np.minimum(np.minimum(u - x0, x1 - u) * (w / h), np.minimum(v - y0, y1 - v))
        sdf = sdf + rag * (en - 0.5) + 0.6 * rag * (st - 0.5)
        a = _smooth(0.0, edge, sdf)
        body = np.clip(1 - scumble * _smooth(0.58, 0.82, st) * (1 - _smooth(0.02, 0.12, sdf) * 0.5), 0, 1)
        col = np.array(color)[None, None, :] * (1 + tone * (st[..., None] - 0.5) * 2)
        nonlocal img
        al = (op * a * body)[..., None]
        img = img * (1 - al) + np.clip(col, 0, 1) * al

    field(0.05, 0.57, 0.30, 0.93, (0.835, 0.785, 0.700), 0.88)
    field(0.45, 0.95, 0.07, 0.56, (0.705, 0.680, 0.635), 0.82)
    field(0.50, 0.71, 0.41, 0.80, (0.935, 0.922, 0.890), 0.72, horizontal=False, scumble=0.4)
    field(0.205, 0.335, 0.14, 0.37, (0.765, 0.565, 0.285), 0.92, rag=0.03, scumble=0.22)
    field(0.635, 0.705, 0.17, 0.89, (0.165, 0.160, 0.152), 0.93, horizontal=False, rag=0.03, scumble=0.38,
          tone=0.12)
    # graphite lines (hand drawn)
    cov = np.zeros((h, w))
    brush_stroke(cov, [(0.08 * w, 0.625 * h), (0.22 * w, 0.615 * h), (0.36 * w, 0.632 * h), (0.43 * w, 0.62 * h)],
                 0.005 * h, rng, dry=0.2, taper=(0.06, 0.1))
    brush_stroke(cov, [(0.86 * w, 0.62 * h), (0.865 * w, 0.75 * h), (0.858 * w, 0.88 * h)], 0.004 * h, rng, dry=0.2,
                 taper=(0.05, 0.1))
    lay((0.30, 0.29, 0.28), 0.75 * cov)
    # short charcoal dry-brush mark low right
    cov2 = np.zeros((h, w))
    brush_stroke(cov2, [(0.74 * w, 0.83 * h), (0.80 * w, 0.815 * h), (0.90 * w, 0.825 * h)], 0.035 * h, rng, dry=0.45,
                 taper=(0.1, 0.35))
    lay((0.2, 0.19, 0.18), 0.8 * cov2)
    # canvas tooth: fine cross weave + grain
    weave = 0.5 + 0.25 * (np.sin(xx * 2.1) + np.sin(yy * 2.1))
    img *= (1 + 0.016 * (weave[..., None] - 0.5))
    grain = rng.random((h, w)) * 0.024 - 0.012
    img = np.clip(img + grain[..., None], 0, 1)
    return np.concatenate([img, np.ones((h, w, 1))], axis=2).astype(np.float32)


def paint_wash(w=700, h=1020, seed=33):
    """Watercolour-on-paper print (for a matted, glazed frame): two overlapping soft arches in greige
    and sage, a small muted ochre sun and a fine charcoal ground line. Washes are glazed
    multiplicatively, with granulation and the darker dried edge typical of watercolour."""
    rng = np.random.default_rng(seed)
    paper = np.array([0.952, 0.944, 0.922])
    img = np.ones((h, w, 3)) * paper
    yy, xx = np.mgrid[0:h, 0:w]
    X, Y = xx / h, yy / h                       # isotropic units (height = 1)
    asp = w / h

    def glaze(sdf, color, strength):
        nonlocal img
        tn = fbm(h, w, 3, 5, rng)
        gr = fbm(h, w, 60, 2, rng)
        en = fbm(h, w, 9, 4, rng)
        sdf = sdf + 0.010 * (en - 0.5)
        inside = _smooth(0.0, 0.010, sdf)
        rim = _smooth(0.0, 0.004, sdf) * (1 - _smooth(0.004, 0.022, sdf))
        a = strength * (inside * (0.78 + 0.32 * (tn - 0.5) + 0.22 * (gr - 0.5)) + 0.28 * rim)
        a = np.clip(a, 0, 1)[..., None]
        img = img * (1 - a * (1 - np.array(color)))

    def arch(cx, base, R, top):
        vc = top + R
        dx = np.abs(X - cx)
        rect = np.minimum(R - dx, base - Y)
        circ = np.minimum(R - np.hypot(X - cx, Y - vc), base - Y)
        return np.where(Y >= vc, rect, circ)

    glaze(arch(0.40 * asp, 0.855, 0.25 * asp, 0.25), (0.76, 0.69, 0.60), 0.95)
    glaze(arch(0.63 * asp, 0.855, 0.15 * asp, 0.47), (0.64, 0.71, 0.62), 0.9)
    glaze(0.065 - np.hypot(X - 0.73 * asp, Y - 0.21), (0.84, 0.64, 0.42), 0.88)
    cov = np.zeros((h, w))
    brush_stroke(cov, [(0.10 * w, 0.866 * h), (0.40 * w, 0.862 * h), (0.70 * w, 0.866 * h), (0.90 * w, 0.863 * h)],
                 0.0075 * h, rng, dry=0.25, taper=(0.08, 0.12))
    img = img * (1 - 0.8 * cov[..., None] * (1 - np.array((0.2, 0.19, 0.18))))
    fib = fbm(h, w, 120, 2, rng)
    img *= (1 + 0.02 * (fib[..., None] - 0.5))
    grain = rng.random((h, w)) * 0.016 - 0.008
    img = np.clip(img + grain[..., None], 0, 1)
    return np.concatenate([img, np.ones((h, w, 1))], axis=2).astype(np.float32)


def to_blender_image(name, w=1800, h=1000, seed=7, variant='gesture'):
    import bpy
    img = bpy.data.images.get(name)
    if img is not None:
        return img
    arr = {'gesture': paint, 'wash': paint_wash}[variant](w, h, seed)
    # byte images store display (sRGB) values directly
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    img.pixels.foreach_set(np.flipud(arr).ravel())
    img.update()
    img.pack()
    return img
