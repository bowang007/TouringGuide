"""Hanging garments for the primary dressing area (pure geometry; same generator as bedrooms_garments,
kept as a zone-local copy so each zone builds on its own; runs inside Blender for mathutils.noise).
Every builder returns (verts, faces) in WORLD SCENE feet (x east, y up, z south) for one garment hung
from a rail that runs along `along` ('x' or 'z') at plan point pos=(x, z). Local garment axes:
  d = across the rail (shoulder to shoulder), t = along the rail (thickness; +t is the garment's
  front, flipped by front=-1), y = up.

Shirts and jackets are built from separate closed shells so they read as clothes, not slabs:
  * body: two fabric layers whose top edge follows the hanger's contoured shoulder line (wrapping the
    hanger bar), a rounded lens section that closes at the side seams, soft independent drape folds,
    a curved shirt-tail hem (shirts) or straight hem (jackets);
  * two sleeves hanging from rounded shoulder caps along the side seams, tapering to a cuff with a few
    stacking wrinkles above it;
  * shirts: a standing collar band around the hanger neck, a raised button placket and buttons;
    jackets: notched lapel plates, two buttons and pocket flaps.
Trousers hang folded over a trouser bar: one 4-layer panel wrapping the bar, waistband end in front,
narrower hem end behind, each end at its own length.
"""
import math
import random

from mathutils import Vector, noise

TAU = math.tau


def _ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def hanger_curve(top, tip=0.62, drop=0.13, neck=0.21, neck_drop=0.112):
    """Centre line height y(d) of a contoured hanger: a rounded neck rise around d=0, straight sloped
    arms to the tips at +/-tip (drop below the neck shoulder), then the garment rolls over the end."""
    def y(d):
        a = abs(d)
        if a < neck:
            return top - neck_drop * (a / neck) ** 1.6
        if a <= tip:
            return top - neck_drop - drop * (a - neck) / (tip - neck)
        return top - neck_drop - drop - 1.1 * (a - tip)
    return y


def _xf(pos, along, yaw, front):
    x0, z0 = pos
    cy, sy = math.cos(yaw), math.sin(yaw)

    def f(t, y, d):
        t *= front
        lc, ld = t * cy + d * sy, -t * sy + d * cy      # lc: along the rail, ld: across it
        return (x0 + lc, y, z0 + ld) if along == 'x' else (x0 + ld, y, z0 + lc)
    return f


class _Mesh:
    def __init__(self):
        self.v, self.f = [], []

    def grid2(self, rows_front, rows_back):
        """Closed shell from two equally sized vertex grids (rows of points) sharing their rim."""
        nr, nc = len(rows_front), len(rows_front[0])
        b0 = len(self.v)
        for rows in (rows_front, rows_back):
            for row in rows:
                self.v.extend(row)
        nside = nr * nc
        for s in range(2):
            b = b0 + s * nside
            for j in range(nr - 1):
                for i in range(nc - 1):
                    q = (b + j * nc + i, b + j * nc + i + 1, b + (j + 1) * nc + i + 1, b + (j + 1) * nc + i)
                    self.f.append(q if s == 0 else tuple(reversed(q)))
        rim = [i for i in range(nc)] + [j * nc + nc - 1 for j in range(1, nr)] + \
              [(nr - 1) * nc + i for i in range(nc - 2, -1, -1)] + [j * nc for j in range(nr - 2, 0, -1)]
        for k in range(len(rim)):
            a, c = b0 + rim[k], b0 + rim[(k + 1) % len(rim)]
            self.f.append((a, c, c + nside, a + nside))

    def tube(self, rings, top_pole, bottom_pole):
        """Closed tube from rings (lists of points, same count) with pole caps."""
        n = len(rings[0])
        b0 = len(self.v)
        for r in rings:
            self.v.extend(r)
        for j in range(len(rings) - 1):
            for i in range(n):
                i2 = (i + 1) % n
                self.f.append((b0 + j * n + i, b0 + j * n + i2, b0 + (j + 1) * n + i2, b0 + (j + 1) * n + i))
        pt = len(self.v)
        self.v.append(top_pole)
        for i in range(n):
            self.f.append((pt, b0 + (i + 1) % n, b0 + i))
        if bottom_pole is None:
            return
        pb = len(self.v)
        self.v.append(bottom_pole)
        last = b0 + (len(rings) - 1) * n
        for i in range(n):
            self.f.append((pb, last + i, last + (i + 1) % n))

    def sheet_tube(self, rings):
        """Open tube through closed rings (equal counts); no caps (coincident points get welded)."""
        n = len(rings[0])
        b0 = len(self.v)
        for r in rings:
            self.v.extend(r)
        for j in range(len(rings) - 1):
            for i in range(n):
                i2 = (i + 1) % n
                self.f.append((b0 + j * n + i, b0 + j * n + i2, b0 + (j + 1) * n + i2, b0 + (j + 1) * n + i))

    def box(self, pts8):
        """Hexahedron from 8 points ordered (bottom 4 ccw, top 4 ccw)."""
        b = len(self.v)
        self.v.extend(pts8)
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append(tuple(b + i for i in q))


def garment(kind, pos, along, hanger_y, length, shoulder, seed=1, yaw=0.0, sway_off=None, front=1,
            gap=None, fold=None):
    """Shirt or jacket on a contoured hanger (hanger_y = hanger_curve(...), tube radius ~0.021 ft).
    length: centre-back length from the neck; shoulder: shoulder seam width (ft)."""
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 40, rnd.random() * 40, rnd.random() * 40))
    so = sway_off if sway_off is not None else off
    xf = _xf(pos, along, yaw, front)
    jacket = kind == 'jacket'
    gap = gap if gap is not None else (rnd.uniform(0.07, 0.085) if jacket else rnd.uniform(0.036, 0.048))
    fold = fold if fold is not None else (0.016 if jacket else 0.034)
    half_sh = shoulder / 2
    half_b = half_sh * (1.0 if jacket else rnd.uniform(1.02, 1.06))
    lift = 0.021 + (0.02 if jacket else 0.012)                       # fabric sits on the hanger bar
    y_neck = hanger_y(0.0) + lift
    tail = rnd.uniform(0.15, 0.22) if not jacket else 0.02
    sway_amp = 0.018

    def shoulder_y(d):
        y = hanger_y(d) + lift
        if jacket:                                                   # padded, squarer shoulders
            y = max(y, hanger_y(0.0) + lift - 0.16 - 0.5 * max(0.0, abs(d) - 0.6))
        return y

    def gap_at(u, v):
        """Separation of the front and back layers: closes to a sharp fold at the side seams, wraps
        the hanger bar along the shoulders."""
        au = abs(u)
        lens = max(0.0, 1.0 - au ** 2.2) ** 0.5
        g = gap * lens * (0.55 + 0.45 * _ss(0.0, 0.14, v))
        wrap = 0.056 * (1.0 - _ss(0.0, 0.06, v)) * lens ** 0.3
        return max(g, wrap)

    def body(u, v, side):
        au = abs(u)
        hb = half_sh + (half_b - half_sh) * _ss(0.0, 0.25, v)
        d = u * hb
        y_top = shoulder_y(d)
        y_hem = y_neck - length + tail * au ** 2
        y = y_top + (y_hem - y_top) * v
        g = gap_at(u, v)
        # drape folds: each layer waves on its own (few, soft, growing toward the hem), never
        # crossing the other layer; the side seams stay pinned
        fo = off + Vector((0.0, 0.0, 11.0 if side > 0 else 23.0))
        # (a couple of soft vertical folds below the chest + diagonal drag lines off the shoulders)
        fn = 0.6 * noise.noise(Vector((u * 2.8 + 0.3 * v, v * 0.6, 0.0)) + fo) + \
            0.25 * noise.noise(Vector((u * 6.0, v * 1.4, 3.0)) + fo) + \
            0.15 * math.sin(10.0 * (au - 0.55 * v) + fo.x) * (1 - _ss(0.2, 0.5, v)) * _ss(0.3, 0.8, au)
        pin = max(0.0, 1.0 - au ** 6)
        amp = fold * (0.25 + 0.75 * _ss(0.1, 0.7, v)) * pin
        c = side * g / 2 + amp * fn
        if side * c < 0.3 * g / 2 + 0.002 * pin:
            c = side * (0.3 * g / 2 + 0.002 * pin)
        c += sway_amp * noise.noise(Vector((0.3, v * 0.8, 7.0)) + so) * v ** 1.3
        if v > 0.97:                                                 # hem edge is never ruler straight
            y += 0.012 * noise.noise(Vector((u * 3.0, 1.0, 2.0)) + off)
        return c, y, d

    def ring_at(v, squeeze=0.0, rise=0.0):
        """Closed section loop: front layer left->right, back layer right->left (side-seam points
        shared). squeeze=1 collapses both layers onto the shoulder seam."""
        ring = []
        for side in (1, -1):
            seq = us if side > 0 else us[-2:0:-1]
            for u in seq:
                c, y, d = body(u, v, side)
                ring.append(xf(c * (1.0 - squeeze), y + rise * (1 - abs(u) ** 4), d))
        return ring

    m = _Mesh()
    # ---- body: a fabric tube open at the hem (front + back layers meeting in sharp side-seam folds),
    # closed over the shoulders by a seam ring where both layers meet (welded later)
    nu, nv = 24, 32
    us = [-1 + 2 * i / nu for i in range(nu + 1)]
    rings = [ring_at(0.0, 1.0, 0.012), ring_at(0.0, 0.5, 0.0085)]
    rings += [ring_at((j / nv) ** 1.15) for j in range(nv + 1)]
    m.sheet_tube(rings)

    # ---- sleeves: open-cuffed tubes hanging from rounded shoulder caps along the side seams
    sl_len = length * (rnd.uniform(0.74, 0.8) if not jacket else rnd.uniform(0.76, 0.8))
    w_top, w_cuff = (0.36, 0.23) if jacket else (0.3, 0.18)
    t_half = 0.045 if jacket else 0.026
    nr, ns = 14, 24
    for sd in (-1, 1):
        d_s = sd * (half_sh - w_top * 0.34)
        y_s = shoulder_y(sd * half_sh * 0.92) - 0.005
        t_bias = (0.5 if (sd > 0) == (seed % 2 == 0) else 0.3) * gap / 2 + t_half * 0.5
        ph = rnd.uniform(0, TAU)
        srings = []
        cap = 0.13
        for k in range(ns + 1):
            s_ = k / ns
            y = y_s - s_ * sl_len
            d_c = d_s + sd * (0.035 * math.sin(math.pi * s_ * 0.8)) - sd * 0.05 * _ss(0.4, 1.0, s_)
            w = w_top + (w_cuff - w_top) * _ss(0.0, 1.0, s_)
            sc = 1.0
            ds = s_ * sl_len
            if ds < cap:                                             # shoulder roll (dome)
                sc = math.sqrt(max(0.0, 1.0 - ((cap - ds) / cap) ** 2)) * 0.85 + 0.15
            sc *= 1.0 + 0.08 * math.sin(s_ * 34.0 + ph) * _ss(0.6, 0.88, s_) * (1 - _ss(0.92, 0.96, s_))
            ring = []
            for i in range(nr):
                a = TAU * i / nr
                ca, sa = math.cos(a), math.sin(a)
                # flattened sleeve: crisp folded edges at the sides, flat faces
                tt = t_bias + math.copysign(abs(sa) ** 0.8, sa) * t_half * sc
                ring.append(xf(tt, y, d_c + ca * w / 2 * sc))
            srings.append(ring)
        m.tube(srings, xf(t_bias, y_s + 0.012, d_s), None)

    def front_at(d, v):
        """Point just proud of the front surface at lateral d, fraction v."""
        u = max(-1.0, min(1.0, d / half_b))
        c, y, dd = body(u, v, 1)
        return c, y, dd

    if not jacket:
        # ---- collar band: an oval ring standing around the hanger neck, lower at the front
        nc = 28
        ra_d, ra_t = 0.2, max(gap / 2 + 0.035, 0.06)
        ring_o, ring_i = [], []
        for i in range(nc):
            a = TAU * i / nc
            fr = max(0.0, math.sin(a))                               # 1 at the front (+t)
            h0 = shoulder_y(math.cos(a) * ra_d) - 0.03               # sits on the (saddle) neckline
            h1 = h0 + 0.15 - 0.06 * fr
            for r_, lst in ((1.0, ring_o), (0.88, ring_i)):
                dd = math.cos(a) * ra_d * r_
                tt = math.sin(a) * ra_t * r_
                lst.append((tt, h0, h1, dd))
        b = len(m.v)
        for (tt, h0, h1, dd) in ring_o + ring_i:
            m.v.append(xf(tt, h0, dd))
            m.v.append(xf(tt, h1, dd))
        oi = nc * 2
        for i in range(nc):
            i2 = (i + 1) % nc
            o0, o1 = b + 2 * i, b + 2 * i2
            n0, n1 = b + oi + 2 * i, b + oi + 2 * i2
            m.f.append((o0, o1, o1 + 1, o0 + 1))                     # outer wall
            m.f.append((n0 + 1, n1 + 1, n1, n0))                     # inner wall
            m.f.append((o0 + 1, o1 + 1, n1 + 1, n0 + 1))             # top edge
            m.f.append((n0, n1, o1, o0))                             # bottom edge
        # ---- button placket + buttons down the centre front
        nv_p = 24
        rows_f, rows_b = [], []
        for j in range(nv_p + 1):
            v = 0.06 + 0.93 * j / nv_p
            rf, rb_ = [], []
            for dd in (-0.06, 0.06):
                c, y, d_ = front_at(dd, v)
                rf.append(xf(c + 0.008, y, d_))
                rb_.append(xf(c - 0.004, y, d_))
            rows_f.append(rf)
            rows_b.append(rb_)
        m.grid2(rows_f, rows_b)
        for k in range(7):
            v = 0.1 + 0.125 * k
            if v > 0.92:
                break
            c, y, d_ = front_at(0.0, v)
            pts = []
            for (yy, tt) in ((y, c + 0.008), (y, c + 0.016)):
                for a in range(4):
                    ang = TAU * (a + 0.5) / 4
                    pts.append(xf(tt, yy + 0.022 * math.sin(ang), d_ + 0.022 * math.cos(ang)))
            m.box(pts)
    else:
        # ---- lapels: two notched plates from the collar to the top button, buttons, pocket flaps
        for sd in (-1, 1):
            outline = [(0.03, 0.0), (0.2, 0.02), (0.26, 0.09), (0.21, 0.12), (0.24, 0.16), (0.05, 0.36)]
            rf, rb_ = [], []
            for (dd, v) in outline:
                c, y, d_ = front_at(sd * dd, max(v, 0.012))
                rf.append(xf(c + 0.012, y, d_))
                rb_.append(xf(c - 0.002, y, d_))
            b = len(m.v)
            m.v.extend(rf + rb_)
            n = len(outline)
            ctr_f, ctr_b = len(m.v), len(m.v) + 1
            cf = [sum(p[i] for p in rf) / n for i in range(3)]
            cb = [sum(p[i] for p in rb_) / n for i in range(3)]
            m.v.extend([tuple(cf), tuple(cb)])
            for i in range(n):
                i2 = (i + 1) % n
                m.f.append((ctr_f, b + i, b + i2) if sd > 0 else (ctr_f, b + i2, b + i))
                m.f.append((ctr_b, b + n + i2, b + n + i) if sd > 0 else (ctr_b, b + n + i, b + n + i2))
                m.f.append((b + i, b + n + i, b + n + i2, b + i2))
        for k, v in enumerate((0.42, 0.56)):
            c, y, d_ = front_at(0.03, v)
            pts = []
            for tt in (c + 0.006, c + 0.016):
                for a in range(4):
                    ang = TAU * (a + 0.5) / 4
                    pts.append(xf(tt, y + 0.03 * math.sin(ang), d_ + 0.03 * math.cos(ang)))
            m.box(pts)
        for sd in (-1, 1):
            pts = []
            for (dd, v, tt) in ((0.22, 0.64, 0.0), (0.52, 0.64, 0.0), (0.52, 0.69, 0.0), (0.22, 0.69, 0.0)):
                c, y, d_ = front_at(sd * dd, v)
                pts.append((c, y, d_))
            box = [xf(c + 0.004, y, d_) for (c, y, d_) in pts] + [xf(c + 0.016, y, d_) for (c, y, d_) in pts]
            if sd < 0:
                box = [box[i] for i in (1, 0, 3, 2, 5, 4, 7, 6)]
            m.box(box)
    return m.v, m.f


def trousers(pos, along, y_bar, l_front, l_back, half_w=0.31, seed=1, yaw=0.0, sway_off=None, front=1,
             bar_r=0.018, thick=0.035):
    """Trousers folded over a trouser bar (centre height y_bar): the waistband end hangs in front
    (wider), the hem end behind (narrower), as one closed 4-layer panel wrapping the bar."""
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 40, rnd.random() * 40, rnd.random() * 40))
    so = sway_off if sway_off is not None else off
    xf = _xf(pos, along, yaw, front)
    R = bar_r + thick / 2 + 0.004
    # path along the panel's mid-surface in (t, y): back end (bottom) -> over the bar -> front end
    path = []
    nb, nf, na = 20, 18, 9
    for k in range(nb + 1):
        s = 1.0 - k / nb
        path.append((-R - 0.012 * s, y_bar - l_back * s, 'b', s))
    for k in range(1, na):
        a = math.pi - math.pi * k / na
        path.append((R * math.cos(a), y_bar + R * math.sin(a), 'top', 0.0))
    for k in range(nf + 1):
        s = k / nf
        path.append((R + 0.01 * s, y_bar - l_front * s, 'f', s))
    rows_o, rows_i = [], []
    nw = 10
    for idx, (t, y, part, s) in enumerate(path):
        t0, y0 = path[max(0, idx - 1)][:2]
        t1, y1 = path[min(len(path) - 1, idx + 1)][:2]
        tx, ty = t1 - t0, y1 - y0
        ln = math.hypot(tx, ty) or 1.0
        nx, ny = ty / ln, -tx / ln                                   # outward normal of the U
        if part == 'b':
            hw = half_w * (1.0 - 0.28 * s)                           # leg tapers to the hem
        elif part == 'f':
            hw = half_w * (1.0 + 0.1 * _ss(0.0, 0.9, s))             # up toward the seat / waist
        else:
            hw = half_w
        th = thick * (1.25 if (part == 'f' and s > 0.92) else 1.0)  # waistband
        ro, ri = [], []
        for i in range(nw + 1):
            u = -1 + 2 * i / nw
            d = u * hw
            fo = off + Vector((0.0, 0.0, 5.0 if part == 'f' else 17.0))
            fd = 0.012 * noise.noise(Vector((u * 2.4, s * 1.2, 0.0)) + fo) * _ss(0.05, 0.6, s)
            sway = 0.016 * noise.noise(Vector((0.3, s * 0.8, 7.0)) + so) * s if part != 'top' else 0.0
            edge = max(0.0, 1.0 - abs(u) ** 6) ** 0.5
            hh = th / 2 * max(0.35, edge)
            cx, cy = t + nx * fd + sway, y + ny * fd
            if part != 'top' and s > 0.985:
                cy += 0.01 * noise.noise(Vector((u * 3.0, 2.0, 1.0)) + off)
            ro.append(xf(cx + nx * hh, cy + ny * hh, d))
            ri.append(xf(cx - nx * hh, cy - ny * hh, d))
        rows_o.append(ro)
        rows_i.append(ri)
    m = _Mesh()
    m.grid2(rows_o, rows_i)
    return m.v, m.f
