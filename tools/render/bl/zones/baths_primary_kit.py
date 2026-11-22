"""Fixtures of the primary bath (stop A0): brushed-nickel exposed shower set, low-iron shower glass, deck taps,
oak-framed mirrors, enamel wall lamps, towel bar, iron shelf brackets, hewn beams, stone wall mesh, the shelf's
still life and the plants.

Same conventions as baths_kit (SCENE feet; a wall Frame has u = distance out of the wall face,
v = along the wall, y = height). The room is built after the warp, in plan feet (baths_primary.py),
so nothing here depends on how bl/warp.py reads names; bake_web.py still classes objects by name.
"""
import math

import bmesh
import bpy

from .. import lighting
from ..common import FT, ft2bl
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


def grid_wall_z(ctx, name, z, x0, x1, y0, y1, nx, ny, mat, coll, facing=-1):
    """Dense flat grid in the plane z = const (normal facing `facing` along SCENE z), for true displacement."""
    verts = []
    for j in range(ny + 1):
        y = y0 + (y1 - y0) * j / ny
        for i in range(nx + 1):
            verts.append((x0 + (x1 - x0) * i / nx, y, z))
    faces = []
    w = nx + 1
    for j in range(ny):
        for i in range(nx):
            a = j * w + i
            faces.append((a, a + 1, a + 1 + w, a + w))
    ob = K.mesh_ft(ctx, name, verts, faces, mat, coll)
    me = ob.data
    me.update()
    nz = -me.polygons[0].normal.y               # SCENE z = -Blender y
    if (nz > 0) != (facing > 0):
        me.flip_normals()
    me.shade_smooth()
    return ob


def _wob(k, j, seed):
    """Smooth pseudo-random value in -1..1 for ring k, corner j."""
    return (math.sin(k * 0.71 + j * 2.3 + seed) + 0.6 * math.sin(k * 0.23 + j * 1.1 + seed * 1.7) +
            0.4 * math.sin(k * 1.93 + j * 4.1 + seed * 0.3)) / 2.0


def hewn_beam(ctx, name, axis, a0, a1, c, y0, y1, w, mat, coll, seed=0.0, step=0.22, wob=0.022, cham=0.06):
    """Hand-hewn timber beam running a0..a1 along SCENE `axis` ('x' or 'z'), centred at c on the other plan axis,
    y0..y1 high, w wide. Its section is a rectangle with worn, uneven arrises (chamfers that come and go), and the
    faces wander a little along the length, as an adzed beam does; smooth-shaded with the arrises kept sharp."""
    n = max(2, int(round((a1 - a0) / step)))
    hw, hh, cy = w / 2, (y1 - y0) / 2, (y0 + y1) / 2
    verts, faces = [], []
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        e = 0.0 if k in (0, n) else 1.0
        ring = []
        for j, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            ch = cham * (0.55 + 0.45 * _wob(k, j, seed + 5.0)) * (1.0 if e else 0.6)
            fx = wob * _wob(k, j + 4, seed) * e           # the two faces meeting at this corner wander
            fy = wob * _wob(k, j + 8, seed) * e
            px, py = sx * (hw + fx), sy * (hh + fy)
            # two points per corner (the chamfer), in ring order
            p1 = (px, py - sy * ch) if sx * sy > 0 else (px - sx * ch, py)
            p2 = (px - sx * ch, py) if sx * sy > 0 else (px, py - sy * ch)
            ring += [p1, p2]
        for (o, yy) in ring:
            verts.append((a, cy + yy, c + o) if axis == 'x' else (c + o, cy + yy, a))
    m = 8
    for k in range(n):
        for j in range(m):
            p, q = k * m + j, k * m + (j + 1) % m
            faces.append((p, q, q + m, p + m))
    faces.append(tuple(reversed(range(m))))
    faces.append(tuple(range(n * m, (n + 1) * m)))
    return K.mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True, sharp_deg=28, recalc=True)


def revolve(ctx, name, prof, x, y, z, mat, coll, seg=40, cap0=True, cap1=True, sharp_deg=50):
    """Turned shape about the vertical through (x, z): prof = [(radius, height above y), ...] bottom to top."""
    f = K.Frame(x, z, 1.0, 0.0)
    rings = [K.R(y + h, -r, r, r, 2, 2, 0.0) for r, h in prof]
    return K.loft(ctx, f, name, rings, mat, coll, seg=seg, cap0=cap0, cap1=cap1, sharp_deg=sharp_deg)


# ------------------------------------------------------------------------------ shower set
def exposed_shower(ctx, f, coll, name, v, y_valve=3.6, y_top=6.72, reach=1.2, head_r=0.36, hand_y=4.55):
    """Brushed-nickel exposed thermostatic shower set on a wall (frame f): bar valve with cross handles on two
    wall unions, rigid riser with a wall bracket, swan-neck arm to an 8.6in round rain head, and a stick
    hand shower in a holder on the riser with a hose from the valve's bottom outlet."""
    br = M.nickel()
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
                 K.matte_material('primary_nozzles', (0.10, 0.10, 0.10), 0.55, 0.3), coll, verts=72)
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
    """Nickel linear drain flush with the shower floor, running a0..a1 along `axis` at c on the other axis."""
    br = M.nickel()
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


def glass_panel(ctx, coll, name, a, b, y0, y1, t=0.031):
    """Frameless 3/8in shower glass from plan point a=(x, z) to b=(x, z), like baths_kit.glass_panel but in low-iron
    glass (M.glass: neutral faces, a pale edge), so the white tile behind it stays white."""
    ob = K.glass_panel(ctx, coll, name, a, b, y0, y1, t)
    ob.data.materials[0] = M.glass()
    ob.data.materials[1] = M.glass_edge()
    return ob


def clamp(ctx, coll, name, x, y, z, along, size=(0.16, 0.10, 0.075)):
    l, h, d = size
    br = M.nickel()
    if along == 'x':
        return K.box(ctx, name, x - l / 2, x + l / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2, br, coll, bevel=0.012)
    return K.box(ctx, name, x - d / 2, x + d / 2, y - h / 2, y + h / 2, z - l / 2, z + l / 2, br, coll, bevel=0.012)


def u_channel(ctx, coll, name, a, b, y, w=0.075, h=0.05):
    (ax, az), (bx, bz) = a, b
    br = M.nickel()
    if abs(az - bz) < 1e-6:
        return K.box(ctx, name, min(ax, bx), max(ax, bx), y, y + h, az - w / 2, az + w / 2, br, coll, bevel=0.006)
    return K.box(ctx, name, ax - w / 2, ax + w / 2, y, y + h, min(az, bz), max(az, bz), br, coll, bevel=0.006)


# ------------------------------------------------------------------------------------ vanity
def deck_tap(ctx, f, coll, name, u, v, y_deck, height=0.62, reach=0.50, r=0.036, lever=1):
    """Deck-mounted brushed-nickel basin tap (the owner's sink image): a round column, a tube spout that leaves
    its top in a quarter bend and runs out level over the basin, and a pin lever on the column's side."""
    br = M.nickel()
    parts = [K.fcyl(ctx, f, name + ' base', u, v, y_deck + 0.012, r + 0.022, 0.024, 'y', br, coll, verts=40)]
    parts.append(K.fcyl(ctx, f, name + ' column', u, v, y_deck + height / 2, r, height, 'y', br, coll, verts=40))
    rb = 0.11
    yt = y_deck + height
    path = [(u, yt - 0.02)] + arc((u + rb, yt), rb, math.pi, math.pi / 2, 8) + [(u + reach, yt + rb)]
    path += [(u + reach + 0.03, yt + rb - 0.012), (u + reach + 0.045, yt + rb - 0.05)]
    parts.append(tube(ctx, name + ' spout', fpts(f, [(uu, v, yy) for uu, yy in path]), r * 0.72, br, coll, seg=20))
    parts.append(K.fcyl(ctx, f, name + ' aerator', u + reach + 0.045, v, yt + rb - 0.065, r * 0.66, 0.02, 'y',
                        K.matte_material('primary_aerator', (0.08, 0.08, 0.08), 0.6), coll))
    vl = v + lever * (r + 0.05)
    parts.append(K.fcyl(ctx, f, name + ' lever hub', u, v + lever * (r + 0.012), y_deck + height * 0.62, 0.024, 0.05, 'v', br, coll))
    parts.append(K.fcyl(ctx, f, name + ' lever', u, vl + lever * 0.05, y_deck + height * 0.62, 0.013, 0.15, 'v', br, coll))
    return parts


def wood_mirror(ctx, f, coll, name, v0, v1, y0, y1, fw=0.15, depth=0.09, mat=None):
    """Rectangular mirror in a plain solid-wood frame (square stock, eased edges), hung on the wall face (u = 0)."""
    wood = mat or M.oak()
    parts = []
    for nm, a, b, c, d in (('top', v0, v1, y1 - fw, y1), ('bottom', v0, v1, y0, y0 + fw),
                           ('left', v0, v0 + fw, y0 + fw - 0.002, y1 - fw + 0.002),
                           ('right', v1 - fw, v1, y0 + fw - 0.002, y1 - fw + 0.002)):
        parts.append(K.fbox(ctx, f, f'{name} frame {nm}', 0.0, depth, a, b, c, d, wood, coll, bevel=0.012, seg=2))
    parts.append(K.fbox(ctx, f, name + ' glass', depth - 0.04, depth - 0.025, v0 + fw - 0.03, v1 - fw + 0.03,
                        y0 + fw - 0.03, y1 - fw + 0.03, 'mirror', coll))
    parts.append(K.fbox(ctx, f, name + ' backing', 0.0, depth - 0.04, v0 + fw - 0.03, v1 - fw + 0.03, y0 + fw - 0.03,
                        y1 - fw + 0.03, K.matte_material('primary_mirror_backing', (0.1, 0.09, 0.08), 0.8), coll))
    return parts


def enamel_lamp(ctx, f, coll, name, v, y, reach=0.55, shade_r=0.34, watts=10.0, kelvin=2900):
    """Vintage enamel wall lamp on frame f: a black iron backplate, a gooseneck arm that rises, arches over and
    comes down into a cream enamel coolie shade with a rolled rim, a porcelain lampholder and a clear bulb with a
    glowing filament (a point light does the lighting). Returns the height of the shade's rim."""
    iron = ctx.mat('black_metal')
    en = M.enamel()
    parts = [K.fcyl(ctx, f, name + ' plate', 0.02, v, y, 0.11, 0.04, 'u', iron, coll, verts=40)]
    uc = reach
    path = [(0.04, y)] + arc((0.13, y + 0.15), 0.15, -math.pi / 2, 0.0, 8)[1:]
    path += arc((0.28 + (uc - 0.28) / 2, y + 0.15), (uc - 0.28) / 2, math.pi, 0.0, 14)[1:]
    path += [(uc, y + 0.05)]
    parts.append(tube(ctx, name + ' arm', fpts(f, [(u, v, yy) for u, yy in path]), 0.026, iron, coll, seg=14))
    yt = y + 0.06                                # top of the shade's neck
    parts.append(K.fcyl(ctx, f, name + ' neck', uc, v, yt - 0.02, 0.06, 0.1, 'y', iron, coll))
    # coolie shade: neck, shoulder, a straight cone to the rim, rolled rim; open below (the inside is enamel too)
    R = shade_r
    rings = [K.R(yt - 0.30, uc - R, uc + R, R, 2, 2, v),
             K.R(yt - 0.315, uc - R - 0.012, uc + R + 0.012, R + 0.012, 2, 2, v),
             K.R(yt - 0.30, uc - R - 0.02, uc + R + 0.02, R + 0.02, 2, 2, v),
             K.R(yt - 0.285, uc - R - 0.008, uc + R + 0.008, R + 0.008, 2, 2, v),
             K.R(yt - 0.13, uc - R * 0.42, uc + R * 0.42, R * 0.42, 2, 2, v),
             K.R(yt - 0.085, uc - 0.085, uc + 0.085, 0.085, 2, 2, v),
             K.R(yt - 0.06, uc - 0.07, uc + 0.07, 0.07, 2, 2, v)]
    parts.append(K.loft(ctx, f, name + ' shade', rings, en, coll, seg=64, cap0=False, cap1=True, sharp_deg=None))
    y_rim = yt - 0.315
    # porcelain holder and a clear pear bulb whose crown just shows below the rim
    parts.append(K.fcyl(ctx, f, name + ' holder', uc, v, yt - 0.14, 0.05, 0.13, 'y', K.CERAMIC, coll))
    yb = yt - 0.205                              # bulb neck top
    br = 0.105
    bulb = [K.R(yb - 0.02 - br * 2.0, uc - 0.02, uc + 0.02, 0.02, 2, 2, v),
            K.R(yb - 0.02 - br * 1.85, uc - br * 0.6, uc + br * 0.6, br * 0.6, 2, 2, v),
            K.R(yb - 0.02 - br * 1.45, uc - br * 0.94, uc + br * 0.94, br * 0.94, 2, 2, v),
            K.R(yb - 0.02 - br, uc - br, uc + br, br, 2, 2, v),
            K.R(yb - 0.02 - br * 0.5, uc - br * 0.85, uc + br * 0.85, br * 0.85, 2, 2, v),
            K.R(yb - 0.02, uc - 0.045, uc + 0.045, 0.045, 2, 2, v),
            K.R(yb, uc - 0.04, uc + 0.04, 0.04, 2, 2, v)]
    b = K.loft(ctx, f, name + ' bulb', bulb, M.bulb(), coll, seg=32, sharp_deg=None)
    b.visible_shadow = False
    parts.append(b)
    fil = K.fcyl(ctx, f, name + ' filament', uc, v, yb - 0.02 - br, 0.012, 0.11, 'y', None, coll, verts=12)
    fil.data.materials.append(lighting.emitter('primary_filament', kelvin, 90.0))
    parts.append(fil)
    x, z = f.w(uc, v)
    lighting.point_light(ctx, x, yb - 0.02 - br, z, watts=watts, kelvin=kelvin, radius_ft=0.05, coll=coll,
                         name=name + ' lamp')
    return y_rim


# --------------------------------------------------------------------------------- towels
def towel_bar(ctx, f, coll, name, v0, v1, y, u=0.24):
    br = M.nickel()
    for v in (v0, v1):
        K.fcyl(ctx, f, name + ' rose', 0.012, v, y, 0.065, 0.024, 'u', br, coll, verts=40)
        K.fcyl(ctx, f, name + ' post', u / 2, v, y, 0.022, u, 'u', br, coll)
    K.fcyl(ctx, f, name + ' bar', u, (v0 + v1) / 2, y, 0.026, (v1 - v0) + 0.07, 'v', br, coll)
    return u, 0.026


def tp_holder(ctx, f, coll, name, v, y, embed=0.0):
    br = M.nickel()
    K.fcyl(ctx, f, name + ' rose', (0.024 - embed) / 2, v, y, 0.075, 0.024 + embed, 'u', br, coll, verts=40)
    K.fcyl(ctx, f, name + ' arm', 0.13, v, y, 0.022, 0.24, 'u', br, coll)
    K.fcyl(ctx, f, name + ' bar', 0.25, v + 0.22, y, 0.02, 0.44, 'v', br, coll)
    K.fcyl(ctx, f, name + ' roll', 0.25, v + 0.24, y, 0.19, 0.36, 'v', K.matte_material('primary_paper', (0.86, 0.85, 0.82), 0.95), coll)
    K.fcyl(ctx, f, name + ' roll core', 0.25, v + 0.24, y, 0.07, 0.362, 'v',
           K.matte_material('primary_paper_core', (0.45, 0.38, 0.30), 0.9), coll)


def fringe(ctx, coll, name, x_edge, z0, z1, y, out, n=70, length=0.2, seed=1.0):
    """Knotted fringe along a mat's short edge at x = x_edge, strands pointing out (`out` = +1 east / -1 west):
    one mesh of flat strands lying on the floor, each a little askew."""
    verts, faces = [], []
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        ang = 0.22 * _wob(k, 3, seed)
        ln = length * (0.85 + 0.15 * _wob(k, 7, seed))
        dx, dz = out * math.cos(ang) * ln, math.sin(ang) * ln
        hw = 0.006
        b = len(verts)
        verts += [(x_edge, y, z - hw), (x_edge, y, z + hw), (x_edge + dx, y - 0.004, z + dz + hw * 1.6),
                  (x_edge + dx, y - 0.004, z + dz - hw * 1.6)]
        faces.append((b, b + 1, b + 2, b + 3))
    return K.mesh_ft(ctx, name, verts, faces, M.fringe(), coll)


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


def framed_print(ctx, coll, name, x, y, z, w, h, lean_deg=7.0, face='east'):
    """Small framed print standing on a shelf, leaning back against the wall behind it: black frame, cream mount,
    the botanical drawing. (x, z) = the middle of its foot, y = the shelf top; it faces `face`."""
    rot = {'south': 0.0, 'east': math.pi / 2, 'north': math.pi, 'west': -math.pi / 2}[face]
    lean = math.radians(lean_deg)
    root = bpy.data.objects.new(name, None)
    ctx.coll(coll).objects.link(root)
    root.location = ft2bl(x, y, z)
    root.rotation_euler = (0.0, 0.0, rot)
    tilt = bpy.data.objects.new(name + ' tilt', None)       # leans back about the foot
    ctx.coll(coll).objects.link(tilt)
    tilt.parent = root
    tilt.rotation_euler = (-lean, 0.0, 0.0)             # the top goes back, away from the face

    def part(nm, x0, x1, y0, y1, d0, d1, mat):
        # local box: x across, y up from the foot, d = depth behind the face (the face looks along local -y)
        ob = ctx.box_c(nm, (0.0, 0.0, 0.0), (x1 - x0, y1 - y0, d1 - d0), 0.0, mat, coll)
        ob.parent = tilt
        ob.location = ((x0 + x1) / 2 * FT, (d0 + d1) / 2 * FT, (y0 + y1) / 2 * FT)
        return ob
    fr, d = 0.035, 0.05
    blk = ctx.mat('paint_black')
    part(name + ' frame top', -w / 2, w / 2, h - fr, h, 0.0, d, blk)
    part(name + ' frame bottom', -w / 2, w / 2, 0.0, fr, 0.0, d, blk)
    part(name + ' frame left', -w / 2, -w / 2 + fr, fr, h - fr, 0.0, d, blk)
    part(name + ' frame right', w / 2 - fr, w / 2, fr, h - fr, 0.0, d, blk)
    part(name + ' mount', -w / 2 + fr, w / 2 - fr, fr, h - fr, 0.03, d - 0.004, M.flat('print_mount', '#e9e3d4', 0.9))
    mg = 0.075
    part(name + ' sheet', -w / 2 + fr + mg, w / 2 - fr - mg, fr + mg, h - fr - mg, 0.026, 0.03, M.botanical())
    return root


def bottle(ctx, coll, name, x, y, z, r, h, mat, neck=0.4, lip=True, stopper=None):
    """Turned bottle standing at (x, y, z): body radius r, height h, a shoulder and a neck (`neck` x r wide)."""
    rn = r * neck
    prof = [(r * 0.92, 0.0), (r, h * 0.04), (r, h * 0.56), (r * 0.9, h * 0.66), (rn * 1.15, h * 0.76), (rn, h * 0.8), (rn, h * 0.95)]
    if lip:
        prof += [(rn * 1.25, h * 0.96), (rn * 1.25, h)]
    else:
        prof += [(rn, h)]
    ob = revolve(ctx, name, prof, x, y, z, mat, coll, seg=32, sharp_deg=60)
    if stopper is not None:
        revolve(ctx, name + ' stopper', [(rn * 0.8, h), (rn * 0.95, h + 0.03), (rn * 0.6, h + 0.06)], x, y, z, stopper, coll,
                seg=20)
    return ob


def jar(ctx, coll, name, x, y, z, r, h, mat):
    prof = [(r * 0.8, 0.0), (r, h * 0.12), (r, h * 0.7), (r * 0.78, h * 0.88), (r * 0.84, h * 0.94), (r * 0.84, h)]
    return revolve(ctx, name, prof, x, y, z, mat, coll, seg=32, sharp_deg=60)


# ----------------------------------------------------------------------------------- plants
def bucket(ctx, coll, name, x, y, z, r, h, mat):
    """Small galvanised florist's bucket: tapered wall, a rolled rim, two swaged beads."""
    prof = [(r * 0.74, 0.0), (r * 0.76, 0.012), (r * 0.83, h * 0.33), (r * 0.85, h * 0.36), (r * 0.84, h * 0.39),
            (r * 0.93, h * 0.72), (r * 0.95, h * 0.75), (r * 0.94, h * 0.78), (r * 0.985, h * 0.96), (r * 1.02, h * 0.985),
            (r * 1.0, h)]
    return revolve(ctx, name, prof, x, y, z, mat, coll, seg=48, sharp_deg=None)


def barrel_cactus(ctx, coll, name, x, y, z, r, h, ribs=18, mat=None):
    """Barrel cactus: a ribbed, slightly flattened column with a dimpled crown; ribs are real geometry."""
    prof = [(0.62, 0.0), (0.86, 0.1), (0.98, 0.3), (1.0, 0.5), (0.97, 0.7), (0.86, 0.86), (0.62, 0.95), (0.34, 0.995), (0.08, 0.98)]
    seg = ribs * 6
    verts, faces = [], []
    for i, (rr, hh) in enumerate(prof):
        for k in range(seg):
            a = 2 * math.pi * k / seg
            rib = 0.5 + 0.5 * math.cos(ribs * a)
            rad = r * rr * (0.80 + 0.20 * rib ** 0.7)
            verts.append((x + rad * math.cos(a), y + h * hh, z + rad * math.sin(a)))
    for i in range(len(prof) - 1):
        for k in range(seg):
            p, q = i * seg + k, i * seg + (k + 1) % seg
            faces.append((p, q, q + seg, p + seg))
    faces.append(tuple(reversed(range(seg))))
    faces.append(tuple(range((len(prof) - 1) * seg, len(prof) * seg)))
    return K.mesh_ft(ctx, name, verts, faces, mat or M.cactus(), coll, smooth=True, sharp_deg=None, recalc=True)


def trailing_plant(ctx, coll, name, x, y, z, pot_r=0.14, pot_h=0.26, strands=11, fan=(-1.35, 1.35), heading=0.0,
                   drop=(0.45, 0.95), seed=2.0, pot_mat=None):
    """Trailing succulent (burro's tail) in a small pot at (x, y, z): strands rise a little from the pot, arch
    over its rim and hang, each strung with plump bead leaves. Strand directions fan over `fan` (radians) about
    `heading` (0 = SCENE +x, pi/2 = SCENE +z), so none grows into the wall behind. One mesh for the strands and
    one for the leaves."""
    pot_mat = pot_mat or M.flat('stoneware', '#d9d2c2', 0.45)
    revolve(ctx, name + ' pot', [(pot_r * 0.72, 0.0), (pot_r * 0.8, 0.02), (pot_r, pot_h * 0.9), (pot_r * 1.04, pot_h * 0.94),
                                 (pot_r * 1.04, pot_h), (pot_r * 0.9, pot_h), (pot_r * 0.88, pot_h * 0.86)], x, y, z, pot_mat,
            coll, seg=40, cap1=False, sharp_deg=60)
    revolve(ctx, name + ' soil', [(pot_r * 0.89, pot_h * 0.86), (0.02, pot_h * 0.88)], x, y, z,
            M.flat('soil', '#3a2e24', 0.95), coll, seg=24, cap0=False, cap1=True)
    green = M.sedum()
    bm_s, bm_l = bmesh.new(), bmesh.new()
    import mathutils
    for s in range(strands):
        t0 = (s + 0.5) / strands
        ang = heading + fan[0] + (fan[1] - fan[0]) * t0 + 0.12 * _wob(s, 1, seed)
        L = drop[0] + (drop[1] - drop[0]) * (0.5 + 0.5 * _wob(s, 5, seed))
        r0 = pot_r * (0.25 + 0.5 * abs(_wob(s, 9, seed)))
        pts = []
        n = 26
        for k in range(n + 1):
            t = k / n
            d = r0 + (pot_r * 1.25 + 0.16 - r0) * (1 - math.exp(-4.2 * t))
            yy = y + pot_h * 0.9 + 0.07 * math.sin(math.pi * min(1.0, t * 2.2)) - L * max(0.0, t - 0.16) ** 1.35 / (0.84 ** 1.35)
            sway = 0.035 * math.sin(6.0 * t + s) * t
            pts.append((x + d * math.cos(ang) - sway * math.sin(ang), yy, z + d * math.sin(ang) + sway * math.cos(ang)))
        # strand: a thin 4-sided tube
        P, F = _frames(pts)
        rings = []
        for p, (tt, nn, bb) in zip(P, F):
            rings.append([bm_s.verts.new(ft2bl(*(p + (nn * math.cos(a) + bb * math.sin(a)) * 0.006)))
                          for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)])
        for A, B in zip(rings, rings[1:]):
            for j in range(4):
                bm_s.faces.new([A[j], A[(j + 1) % 4], B[(j + 1) % 4], B[j]])
        # leaves: beads along the hanging part, plumper toward the middle of the strand
        for k in range(3, n + 1):
            t = k / n
            rad = 0.021 * (0.55 + 0.75 * math.sin(math.pi * min(1.0, 0.15 + t * 0.85)) ** 0.8)
            for j in range(2):
                a = k * 2.4 + j * math.pi + s
                p = P[k] + (F[k][1] * math.cos(a) + F[k][2] * math.sin(a)) * (rad * 0.75) + F[k][0] * (j * 0.012)
                mat = mathutils.Matrix.Translation(ft2bl(p.x, p.y, p.z))
                bmesh.ops.create_icosphere(bm_l, subdivisions=1, radius=rad * FT, matrix=mat)
    out = []
    for bm, nm in ((bm_s, name + ' strands'), (bm_l, name + ' leaves')):
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        me.materials.append(green)
        ob = bpy.data.objects.new(nm, me)
        ctx.coll(coll).objects.link(ob)
        out.append(ob)
    return out
