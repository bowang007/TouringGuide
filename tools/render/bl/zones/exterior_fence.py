"""Charcoal horizontal-slat fences and gates on the lot lines of the site plan (runs inside Blender).

Design (1077 W McKinley): square charcoal posts ~7'-6" o.c., 5-1/2" horizontal boards with tight
1/4" reveals, a semi-open top band of narrow slats and a flat cap. Boards sit between the posts.
"""
import math

from . import exterior_layout as L
from .exterior_util import GRADE, MB, flat_mat, mul_copy

SUB = 'fence'
POST = 0.29          # 3-1/2" posts
BOARD_T = 0.065      # board thickness
CAP_H = 0.10
# cool slate charcoal like the 1077 W McKinley fence (the library charcoal reads brown in warm sun)
SLATE = (1.22, 1.36, 1.55)


def fence_mat(ctx):
    return mul_copy(ctx, 'fence_charcoal', SLATE, 'Z_exterior_fence_slate')


def _profile(y_bot, y_top, top_band=True):
    """List of (y0, y1, thickness) slats from bottom to top."""
    out = []
    cap0 = y_top - CAP_H
    band = 0.95 if top_band else 0.0
    main_top = cap0 - band - (0.06 if top_band else 0.02)
    h = main_top - y_bot
    n = max(1, int((h + 0.02) / 0.478))
    gap = 0.014
    bh = (h - gap * (n - 1)) / n
    y = y_bot
    for _ in range(n):
        out.append((y, y + bh, BOARD_T))
        y += bh + gap
    if top_band:
        k = 5
        sh = 0.1
        g = (band - k * sh) / k
        y = main_top + 0.06 + g
        for _ in range(k):
            out.append((y, y + sh, BOARD_T * 0.8))
            y += sh + g
    out.append((cap0, y_top, POST + 0.05))         # flat cap rail
    return out


def run(ctx, name, p0, p1, y_top, top_band=True, spacing=7.6, gate=None, end_posts=(True, True)):
    """Fence from p0 to p1 (x, z). gate: (t0, t1) fractions of the run occupied by a gate leaf."""
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0
    length = math.hypot(dx, dz)
    ux, uz = dx / length, dz / length
    rot = math.atan2(-dz, dx)         # SCENE rot about +Y that maps local +x onto the run
    y_bot = GRADE + 0.16
    prof = _profile(y_bot, y_top, top_band)
    posts = []
    if gate:
        a, b = gate
        segs = [(0.0, a), (b, 1.0)]
    else:
        segs = [(0.0, 1.0)]
    stations = set()
    for (s0, s1) in segs:
        l0, l1 = s0 * length, s1 * length
        if l1 - l0 < 0.5:
            stations.update([l0, l1])
            continue
        n = max(1, int(math.ceil((l1 - l0) / spacing)))
        for k in range(n + 1):
            stations.add(round(l0 + (l1 - l0) * k / n, 4))
    stations = sorted(stations)
    post_st = stations
    if not end_posts[0]:          # corner post already built by the adjoining run: boards still start here
        post_st = [s for s in post_st if s > 0.01]
    if not end_posts[1]:
        post_st = [s for s in post_st if s < length - 0.01]
    mb = MB()
    for s in post_st:
        cx, cz = x0 + ux * s, z0 + uz * s
        mb.box_c(cx, (GRADE - 0.4 + y_top + 0.02) / 2, cz, POST, y_top + 0.02 - (GRADE - 0.4), POST, rot)
    # boards between consecutive posts (skip the gate opening)
    gate_span = (gate[0] * length, gate[1] * length) if gate else None
    for i in range(len(stations) - 1):
        a, b = stations[i] + POST / 2, stations[i + 1] - POST / 2
        if gate_span and a >= gate_span[0] - 0.01 and b <= gate_span[1] + 0.01 + POST:
            continue
        if b - a < 0.05:
            continue
        mid = (a + b) / 2
        cx, cz = x0 + ux * mid, z0 + uz * mid
        for (ya, yb, t) in prof:
            if t > POST:         # cap rail runs over the posts
                continue
            mb.box_c(cx, (ya + yb) / 2, cz, b - a, yb - ya, t, rot)
    # continuous cap rail over everything except the gate
    cap = prof[-1]
    caps = [(0.0, length)] if not gate_span else [(0.0, gate_span[0]), (gate_span[1], length)]
    for (a, b) in caps:
        if b - a < 0.1:
            continue
        a2 = a - (POST / 2 if a < 0.01 else 0)
        b2 = b + (POST / 2 if b > length - 0.01 else 0)
        mid = (a2 + b2) / 2
        mb.box_c(x0 + ux * mid, (cap[0] + cap[1]) / 2, z0 + uz * mid, b2 - a2, cap[1] - cap[0], cap[2], rot)
    ob = mb.obj(ctx, f'ext fence {name}', fence_mat(ctx), SUB, bevel=0.012, segments=1)
    if gate_span:
        _gate(ctx, name, x0, z0, ux, uz, rot, gate_span, prof, y_bot)
    return ob


def _gate(ctx, name, x0, z0, ux, uz, rot, span, prof, y_bot):
    a, b = span[0] + POST / 2 + 0.04, span[1] - POST / 2 - 0.04
    mid = (a + b) / 2
    cx, cz = x0 + ux * mid, z0 + uz * mid
    w = b - a
    mb = MB()
    top = prof[-1][1] - 0.02
    # frame
    for (ya, yb, t) in prof[:-1]:
        mb.box_c(cx, (ya + yb) / 2, cz, w - 0.1, yb - ya, t + 0.02, rot)
    for s in (-1, 1):
        ox = s * (w / 2 - 0.05)
        mb.box_c(cx + ux * ox, (y_bot + top) / 2, cz + uz * ox, 0.1, top - y_bot, BOARD_T + 0.05, rot)
    mb.box_c(cx, top - 0.05, cz, w, 0.1, BOARD_T + 0.05, rot)
    mb.obj(ctx, f'ext gate {name}', fence_mat(ctx), SUB, bevel=0.01, segments=1)
    # black pull handle + latch on the latch side, hinges on the hinge side
    hw = MB()
    lx = w / 2 - 0.35
    nx, nz = -uz, ux                 # fence normal
    for side in (-1, 1):
        hx, hz = cx + ux * lx + nx * side * 0.09, cz + uz * lx + nz * side * 0.09
        hw.box_c(hx, GRADE + 3.6, hz, 0.06, 1.0, 0.06, rot)
        hw.box_c(hx - nx * side * 0.04, GRADE + 3.15, hz - nz * side * 0.04, 0.05, 0.05, 0.06, rot)
        hw.box_c(hx - nx * side * 0.04, GRADE + 4.05, hz - nz * side * 0.04, 0.05, 0.05, 0.06, rot)
    for yh in (y_bot + 0.6, top - 0.6):
        hx, hz = cx - ux * (w / 2 - 0.15), cz - uz * (w / 2 - 0.15)
        hw.box_c(hx + nx * 0.07, yh, hz + nz * 0.07, 0.5, 0.12, 0.02, rot)
    hw.obj(ctx, f'ext gate {name} hardware', 'black_metal', SUB, bevel=0.008, segments=1)


def build(ctx):
    top = L.FENCE_TOP
    n = 0
    run(ctx, 'rear', (L.FW, L.FN), (L.FE, L.FN), top); n += 1
    run(ctx, 'west', (L.FW, L.FN), (L.FW, L.GATE_WZ), top, end_posts=(False, True)); n += 1
    run(ctx, 'east', (L.FE, L.FN), (L.FE, L.GATE_EZ), top, end_posts=(False, True)); n += 1
    # side returns with gates (gate on the house side, a post fixed against the stucco)
    wl = L.HX0 - 0.16 - L.FW
    run(ctx, 'west return', (L.FW, L.GATE_WZ), (L.HX0 - 0.16, L.GATE_WZ), top,
        gate=(1 - 3.6 / wl, 1.0), end_posts=(False, True)); n += 1
    el = L.FE - (L.HX1 + 0.16)
    run(ctx, 'east return', (L.HX1 + 0.16, L.GATE_EZ), (L.FE, L.GATE_EZ), top,
        gate=(0.0, 3.6 / el), end_posts=(True, False)); n += 1
    # low front fence on the west front lawn (3 ft)
    run(ctx, 'front low', (L.FW, L.FRONT_FENCE_Z), (L.PORCH[0] - 0.3, L.FRONT_FENCE_Z), GRADE + 3.0,
        top_band=False, spacing=6.8); n += 1
    return {'runs': n}
