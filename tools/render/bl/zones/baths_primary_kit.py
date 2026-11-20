"""Fixtures of the primary bath (stop A0): aged-brass exposed shower set, wall spouts, brass-framed
mirrors, opal-glass sconces, towel warmer, iron shelf brackets, stone wall mesh.

Same conventions as baths_kit (SCENE feet; a wall Frame has u = distance out of the wall face,
v = along the wall, y = height). Names matter: bl/warp.py classifies objects by name (see the
LOOSE / FITTED regexes there), so every builder takes the full object name from the caller.
"""
import math

from .. import lighting
from . import baths_kit as K
from . import baths_primary_mats as M


# ------------------------------------------------------------------------------------ meshes
def _frames(pts):
    """Parallel-transport frames (t, n, b) along a polyline of 3D points."""
    import mathutils
    V = mathutils.Vector
    P = [V(p) for p in pts]
    T = []
    for i in range(len(P)):
        a = P[max(i - 1, 0)]
        b = P[min(i + 1, len(P) - 1)]
        T.append((b - a).normalized())
    ref = V((0, 1, 0)) if abs(T[0].y) < 0.9 else V((1, 0, 0))
    n = T[0].cross(ref).normalized()
    out = []
    for i, t in enumerate(T):
        if i:
            n = (n - t * n.dot(t)).normalized()
        out.append((t, n, t.cross(n).normalized()))
    return P, out


def catmull(pts, per=8):
    """Smooth Catmull-Rom curve through the control points (3-tuples)."""
    if len(pts) < 3:
        return list(pts)
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                                    (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    out.append(tuple(pts[-1]))
    return out


def tube(ctx, name, pts, r, mat, coll, seg=16, caps=True):
    """Round tube (SCENE-ft polyline pts, radius r ft) as a smooth mesh."""
    P, F = _frames(pts)
    verts, faces = [], []
    for p, (t, n, b) in zip(P, F):
        for k in range(seg):
            a = 2 * math.pi * k / seg
            q = p + (n * math.cos(a) + b * math.sin(a)) * r
            verts.append((q.x, q.y, q.z))
    m = len(P)
    for i in range(m - 1):
        for k in range(seg):
            a, c = i * seg + k, i * seg + (k + 1) % seg
            faces.append((a, c, c + seg, a + seg))
    if caps:
        faces.append(tuple(reversed(range(seg))))
        faces.append(tuple(range((m - 1) * seg, m * seg)))
    return K.mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True, sharp_deg=None, recalc=caps)


def arc(c, r, a0, a1, n=10):
    """Points of an arc in a 2D plane: centre c=(u, y), radius r, angles a0..a1 (rad)."""
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def fpts(f, uvy):
    """Wall-frame (u, v, y) points -> SCENE (x, y, z)."""
    out = []
    for u, v, y in uvy:
        x, z = f.w(u, v)
        out.append((x, y, z))
    return out


def side_prism(ctx, f, name, pts_uy, v0, v1, mat, coll, smooth=False):
    """Prism: polygon in the (u, y) plane of wall frame f, extruded along v from v0 to v1."""
    n = len(pts_uy)
    verts = []
    for v in (v0, v1):
        for u, y in pts_uy:
            x, z = f.w(u, v)
            verts.append((x, y, z))
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(k, (k + 1) % n, (k + 1) % n + n, k + n) for k in range(n)]
    return K.mesh_ft(ctx, name, verts, faces, mat, coll, smooth=smooth, sharp_deg=35, recalc=True)


def grid_wall(ctx, name, x, z0, z1, y0, y1, nz, ny, mat, coll, facing=-1):
    """Dense flat grid in the plane x = const (normal facing `facing` along x), for true displacement."""
    verts = []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nz + 1):
            verts.append((x, y, z0 + (z1 - z0) * i / nz))
    faces = []
    w = nz + 1
    for j in range(ny):
        for i in range(nz):
            a = j * w + i
            faces.append((a, a + 1, a + 1 + w, a + w))
    ob = K.mesh_ft(ctx, name, verts, faces, mat, coll)
    me = ob.data
    me.update()
    nx = me.polygons[0].normal.x
    if (nx > 0) != (facing > 0):
        me.flip_normals()
    me.shade_smooth()
    return ob


# ------------------------------------------------------------------------------ shower set
def exposed_shower(ctx, f, coll, name, v, y_valve=3.6, y_top=6.72, reach=1.2, head_r=0.36, hand_y=4.55):
    """Aged-brass exposed thermostatic shower set on a wall (frame f): bar valve with cross handles on two
    wall unions, rigid riser with a wall bracket, swan-neck arm to an 8.6in round rain head, and a stick
    hand shower in a holder on the riser with a hose from the valve's bottom outlet."""
    br = M.brass()
    ur = 0.17                                   # riser / bar centre distance from the wall
    rb, L = 0.068, 0.98                         # bar valve radius and length
    parts = []
    parts.append(K.fcyl(ctx, f, name + ' valve bar', ur, v, y_valve, rb, L, 'v', br, coll, verts=40))
    for s in (-1, 1):
        vv = v + s * 0.30
        parts.append(K.fcyl(ctx, f, name + ' valve union', ur / 2, vv, y_valve, 0.034, ur, 'u', br, coll))
        parts.append(K.fcyl(ctx, f, name + ' valve union nut', ur - 0.07, vv, y_valve, 0.05, 0.06, 'u', br, coll))
        parts.append(K.fcyl(ctx, f, name + ' valve rose', 0.015, vv, y_valve, 0.10, 0.03, 'u', br, coll, verts=40))
        ve = v + s * (L / 2 + 0.04)
        parts.append(K.fcyl(ctx, f, name + ' valve hub', ur, ve, y_valve, 0.045, 0.08, 'v', br, coll))
        vh = v + s * (L / 2 + 0.085)
        parts.append(K.fbox(ctx, f, name + ' valve lever', ur - 0.13, ur + 0.13, vh - 0.018, vh + 0.018,
                            y_valve - 0.022, y_valve + 0.022, br, coll, bevel=0.012))
        parts.append(K.fbox(ctx, f, name + ' valve lever', ur - 0.022, ur + 0.022, vh - 0.018, vh + 0.018,
                            y_valve - 0.13, y_valve + 0.13, br, coll, bevel=0.012))
    # riser up from the bar, wall bracket near the top
    y_r0 = y_valve + rb - 0.01
    yb = y_top - 0.55
    parts.append(K.fcyl(ctx, f, name + ' riser', ur, v, (y_r0 + y_top) / 2, 0.042, y_top - y_r0, 'y', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' riser bracket', ur / 2, v, yb, 0.026, ur, 'u', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' riser bracket rose', 0.012, v, yb, 0.07, 0.024, 'u', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' riser collar', ur, v, yb, 0.056, 0.08, 'y', br, coll))
    # swan-neck arm: up, bend out (r 0.22), across, bend down (r 0.14) onto the head
    rc1, rc2 = 0.22, 0.14
    u_end = ur + reach
    path = [(ur, y_top - 0.02)]
    path += [p for p in arc((ur + rc1, y_top), rc1, math.pi, math.pi / 2, 10)]
    path += [p for p in arc((u_end - rc2, y_top + rc1 - rc2), rc2, math.pi / 2, 0.0, 8)]
    yh = y_top + rc1 - rc2 - 0.10
    path += [(u_end, yh + 0.005)]
    parts.append(tube(ctx, name + ' rain arm', fpts(f, [(u, v, y) for u, y in path]), 0.036, br, coll, seg=20))
    # round rain head: shallow dome, flat face with a dark nozzle disc
    rings = [K.R(yh - 0.075, u_end - head_r, u_end + head_r, head_r, 2, 2, v),
             K.R(yh - 0.055, u_end - head_r, u_end + head_r, head_r, 2, 2, v),
             K.R(yh - 0.035, u_end - head_r * 0.93, u_end + head_r * 0.93, head_r * 0.93, 2, 2, v),
             K.R(yh - 0.012, u_end - head_r * 0.55, u_end + head_r * 0.55, head_r * 0.55, 2, 2, v),
             K.R(yh, u_end - 0.07, u_end + 0.07, 0.07, 2, 2, v)]
    parts.append(K.loft(ctx, f, name + ' rain head', rings, br, coll, seg=72, sharp_deg=None))
    noz = K.fcyl(ctx, f, name + ' rain nozzles', u_end, v, yh - 0.0765, head_r - 0.04, 0.003, 'y',
                 K.matte_material('primary_nozzles', (0.16, 0.12, 0.07), 0.55, 0.6), coll, verts=72)
    parts.append(noz)
    # hand shower: holder on the riser, stick handset, hose from the bar's bottom outlet
    uh = ur + 0.15
    parts.append(K.fcyl(ctx, f, name + ' hand holder collar', ur, v, hand_y + 0.5, 0.054, 0.09, 'y', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' hand holder arm', (ur + uh) / 2, v, hand_y + 0.5, 0.022, uh - ur, 'u', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' hand holder cup', uh, v, hand_y + 0.5, 0.05, 0.08, 'y', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' handle', uh, v, hand_y + 0.25, 0.034, 0.5, 'y', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' handset', uh, v, hand_y + 0.6, 0.075, 0.12, 'y', br, coll, verts=40))
    parts.append(K.fcyl(ctx, f, name + ' outlet', ur, v, y_valve - rb - 0.03, 0.03, 0.07, 'y', br, coll))
    yo = y_valve - rb - 0.065
    ctrl = [(ur, v, yo), (ur + 0.02, v + 0.04, yo - 0.25), (ur + 0.07, v + 0.10, yo - 0.62), (ur + 0.13, v + 0.12, yo - 0.78),
            (ur + 0.17, v + 0.09, yo - 0.62), (uh + 0.01, v + 0.04, hand_y - 0.25), (uh, v, hand_y - 0.02)]
    parts.append(tube(ctx, name + ' hose', fpts(f, catmull(ctrl, 8)), 0.024, br, coll, seg=12))
    return parts


def linear_drain(ctx, coll, name, a0, a1, c, y, axis='x'):
    """Brass linear drain flush with the shower floor, running a0..a1 along `axis` at c on the other axis."""
    br = M.brass()
    slot = K.matte_material('primary_drain_slot', (0.03, 0.03, 0.03), 0.8)
    n = int((a1 - a0) / 0.09)

    def bx(nm, p0, p1, y0, y1, q0, q1, mat, **kw):
        if axis == 'x':
            return K.box(ctx, nm, p0, p1, y0, y1, q0, q1, mat, coll, **kw)
        return K.box(ctx, nm, q0, q1, y0, y1, p0, p1, mat, coll, **kw)
    bx(name, a0, a1, y - 0.01, y + 0.003, c - 0.06, c + 0.06, br, bevel=0.004)
    for k in range(n):
        p = a0 + 0.06 + (a1 - a0 - 0.12) * (k + 0.5) / n
        bx(f'{name} grate slot {k}', p - 0.012, p + 0.012, y + 0.003, y + 0.0035, c - 0.035, c + 0.035, slot)


def clamp(ctx, coll, name, x, y, z, along, size=(0.16, 0.10, 0.075)):
    l, h, d = size
    br = M.brass()
    if along == 'x':
        return K.box(ctx, name, x - l / 2, x + l / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2, br, coll, bevel=0.012)
    return K.box(ctx, name, x - d / 2, x + d / 2, y - h / 2, y + h / 2, z - l / 2, z + l / 2, br, coll, bevel=0.012)


def u_channel(ctx, coll, name, a, b, y, w=0.075, h=0.05):
    (ax, az), (bx, bz) = a, b
    br = M.brass()
    if abs(az - bz) < 1e-6:
        return K.box(ctx, name, min(ax, bx), max(ax, bx), y, y + h, az - w / 2, az + w / 2, br, coll, bevel=0.006)
    return K.box(ctx, name, ax - w / 2, ax + w / 2, y, y + h, min(az, bz), max(az, bz), br, coll, bevel=0.006)


# ------------------------------------------------------------------------------------ vanity
def wall_spout(ctx, f, coll, name, v, y, reach=0.55, handle_dv=0.36):
    """Wall-mount brass basin spout (round plate, 3/4in tube, slight down-turned tip) with a separate
    wall handle (plate + short lever) beside it."""
    br = M.brass()
    parts = [K.fcyl(ctx, f, name + ' plate', 0.012, v, y, 0.1, 0.024, 'u', br, coll, verts=40)]
    parts.append(K.fcyl(ctx, f, name + ' spout', 0.02 + (reach - 0.03) / 2, v, y, 0.034, reach - 0.03, 'u', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' spout tip', reach - 0.02, v, y - 0.02, 0.034, 0.075, 'y', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' aerator', reach - 0.02, v, y - 0.06, 0.028, 0.012, 'y',
                        K.matte_material('primary_aerator', (0.08, 0.07, 0.06), 0.6), coll))
    vh = v + handle_dv
    parts.append(K.fcyl(ctx, f, name + ' handle plate', 0.012, vh, y, 0.075, 0.024, 'u', br, coll, verts=40))
    parts.append(K.fcyl(ctx, f, name + ' handle hub', 0.06, vh, y, 0.034, 0.09, 'u', br, coll))
    parts.append(K.fbox(ctx, f, name + ' handle lever', 0.085, 0.115, vh - 0.018, vh + 0.018, y - 0.01, y + 0.21,
                        br, coll, bevel=0.012))
    return parts


def framed_mirror(ctx, f, coll, name, v0, v1, y0, y1, fw=0.12, depth=0.075):
    """Rectangular mirror in a rounded brass frame, hung on the wall face (u = 0)."""
    br = M.brass()
    parts = []
    for nm, a, b, c, d in (('top', v0, v1, y1 - fw, y1), ('bottom', v0, v1, y0, y0 + fw),
                           ('left', v0, v0 + fw, y0 + fw - 0.002, y1 - fw + 0.002), ('right', v1 - fw, v1, y0 + fw - 0.002, y1 - fw + 0.002)):
        parts.append(K.fbox(ctx, f, f'{name} frame {nm}', 0.0, depth, a, b, c, d, br, coll, bevel=0.022, seg=4))
    parts.append(K.fbox(ctx, f, name + ' glass', 0.02, 0.035, v0 + fw - 0.03, v1 - fw + 0.03, y0 + fw - 0.03, y1 - fw + 0.03,
                        'mirror', coll))
    parts.append(K.fbox(ctx, f, name + ' backing', 0.0, 0.02, v0 + fw - 0.03, v1 - fw + 0.03, y0 + fw - 0.03, y1 - fw + 0.03,
                        K.matte_material('primary_mirror_backing', (0.1, 0.1, 0.1), 0.8), coll))
    return parts


def sconce(ctx, f, coll, name, v, y, watts=22.0, kelvin=3000):
    """Brass wall sconce: round backplate, an arm that rises and arches over into a downward opal-glass
    bell shade (with a lamp in it), so the arm never passes through the shade. 3000K, not 2700K: under
    the daylight white balance of the bath a 2700K lamp turned the cream plaster and the oak orange."""
    br = M.brass()
    parts = [K.fcyl(ctx, f, name + ' plate', 0.015, v, y, 0.1, 0.03, 'u', br, coll, verts=40)]
    uc = 0.40
    path = [(0.03, y)] + arc((0.10, y + 0.12), 0.12, -math.pi / 2, 0.0, 8)[1:]
    path += arc((0.10 + 0.12 + 0.09, y + 0.24), 0.09, math.pi, 0.0, 10)[1:]
    path += [(uc, y + 0.17)]
    parts.append(tube(ctx, name + ' arm', fpts(f, [(u, v, yy) for u, yy in path]), 0.022, br, coll, seg=14))
    yt = y + 0.16
    parts.append(K.fcyl(ctx, f, name + ' cup', uc, v, yt + 0.02, 0.05, 0.06, 'y', br, coll))
    rings = [K.R(yt - 0.30, uc - 0.165, uc + 0.165, 0.165, 2, 2, v),
             K.R(yt - 0.27, uc - 0.16, uc + 0.16, 0.16, 2, 2, v),
             K.R(yt - 0.16, uc - 0.12, uc + 0.12, 0.12, 2, 2, v),
             K.R(yt - 0.05, uc - 0.075, uc + 0.075, 0.075, 2, 2, v),
             K.R(yt - 0.005, uc - 0.05, uc + 0.05, 0.05, 2, 2, v)]
    parts.append(K.loft(ctx, f, name + ' shade', rings, M.opal(), coll, seg=48, cap0=False, cap1=True, sharp_deg=None))
    x, z = f.w(uc, v)
    lighting.point_light(ctx, x, yt - 0.14, z, watts=watts, kelvin=kelvin, radius_ft=0.06, coll=coll,
                         name=name + ' lamp')
    return parts


# --------------------------------------------------------------------------------- towels
def towel_warmer(ctx, f, coll, name, v0, v1, y0, y1, bars=6, u=0.24, back=None):
    """Brass ladder towel warmer standing off the wall; back(y) = extra rose depth behind u=0 at height y
    (the wall face steps back where the wainscot ends)."""
    br = M.brass()
    r_rail, r_bar = 0.045, 0.03
    for v in (v0, v1):
        K.fcyl(ctx, f, name + ' rail', u, v, (y0 + y1) / 2, r_rail, y1 - y0, 'y', br, coll)
        K.fcyl(ctx, f, name + ' rail cap', u, v, y1 + 0.006, r_rail * 0.9, 0.012, 'y', br, coll)
        K.fcyl(ctx, f, name + ' rail cap', u, v, y0 - 0.006, r_rail * 0.9, 0.012, 'y', br, coll)
        for yy in (y0 + 0.3, y1 - 0.3):
            bk = back(yy) if back else 0.0
            K.fcyl(ctx, f, name + ' standoff', (u - bk) / 2, v, yy, 0.022, u + bk, 'u', br, coll)
            K.fcyl(ctx, f, name + ' rose', 0.012 - bk, v, yy, 0.06, 0.024, 'u', br, coll)
    for k in range(bars):
        yy = y0 + 0.12 + (y1 - y0 - 0.2) * k / (bars - 1)
        K.fcyl(ctx, f, name + f' bar {k}', u, (v0 + v1) / 2, yy, r_bar, v1 - v0, 'v', br, coll)
    return u, r_bar


def tp_holder(ctx, f, coll, name, v, y, embed=0.0):
    br = M.brass()
    K.fcyl(ctx, f, name + ' rose', (0.024 - embed) / 2, v, y, 0.075, 0.024 + embed, 'u', br, coll, verts=40)
    K.fcyl(ctx, f, name + ' arm', 0.13, v, y, 0.022, 0.24, 'u', br, coll)
    K.fcyl(ctx, f, name + ' bar', 0.25, v + 0.22, y, 0.02, 0.44, 'v', br, coll)
    K.fcyl(ctx, f, name + ' roll', 0.25, v + 0.24, y, 0.19, 0.36, 'v', K.matte_material('primary_paper', (0.86, 0.85, 0.82), 0.95), coll)
    K.fcyl(ctx, f, name + ' roll core', 0.25, v + 0.24, y, 0.07, 0.362, 'v',
           K.matte_material('primary_paper_core', (0.45, 0.38, 0.30), 0.9), coll)


def flush_buttons(ctx, f, coll, name, v, y, embed=0.0):
    """Round brass dual-flush push plate set into the wall (stone): ring + two half-moon buttons."""
    br = M.brass()
    K.fcyl(ctx, f, name, (0.03 - embed) / 2, v, y, 0.16, 0.03 + embed, 'u', br, coll, verts=48)
    for s in (-1, 1):
        K.fbox(ctx, f, f'{name} button', 0.03, 0.042, v + s * 0.065 - 0.05, v + s * 0.065 + 0.05, y - 0.11, y + 0.11,
               br, coll, bevel=0.012)


# ------------------------------------------------------------------------------------ shelf
def iron_bracket(ctx, f, coll, name, v, y_top, depth=0.5, drop=0.42, embed=0.0):
    """Forged black-iron shelf bracket: flat bar under the shelf, flat bar on the wall and a curved brace
    ending in a small scroll."""
    blk = 'black_metal'
    t, w = 0.03, 0.065
    K.fbox(ctx, f, name + ' arm', 0.0, depth, v - w / 2, v + w / 2, y_top - t, y_top, blk, coll, bevel=0.006)
    K.fbox(ctx, f, name + ' leg', -embed, t, v - w / 2, v + w / 2, y_top - drop, y_top - t, blk, coll, bevel=0.006)
    r = min(depth, drop) * 0.78
    # brace from the leg (low) to the arm (outer end), concave toward the corner
    brace = [(t + 0.002, y_top - t - r)] + [(t + r - r * math.cos(a), y_top - t - r + r * math.sin(a))
                                           for a in [math.pi / 2 * k / 12 for k in range(1, 13)]]
    tube(ctx, name + ' brace', fpts(f, [(u, v, yy) for u, yy in brace]), 0.016, ctx.mat(blk), coll, seg=10)
    curl = [(t + r, y_top - t - 0.002)] + [(t + r + 0.05 * math.sin(a), y_top - t - 0.05 + 0.05 * math.cos(a))
                                          for a in [math.pi * 1.6 * k / 12 for k in range(1, 13)]]
    tube(ctx, name + ' scroll', fpts(f, [(u, v, yy) for u, yy in curl]), 0.014, ctx.mat(blk), coll, seg=10)
