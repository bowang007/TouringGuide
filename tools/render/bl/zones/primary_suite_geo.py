"""Geometry helpers for the primary_suite zone (soft goods, lathe shapes, drapes, folded items).

All helpers take SCENE feet (x east, y up, z south) and build objects whose origin is the
world origin, so procedural textures driven by Object/Position coordinates stay in world space.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector, noise

from ..common import FT, ft2bl


def _mat(ctx, mat):
    if mat is None:
        return None
    return ctx.mat(mat) if isinstance(mat, str) else mat


def mesh_ft(ctx, name, verts, faces, mat=None, coll='zone', smooth=False):
    """Object from SCENE-feet world-space vertices (origin at world origin)."""
    vb = [tuple(ft2bl(*v)) for v in verts]
    me = bpy.data.meshes.new(name)
    me.from_pydata(vb, [], faces)
    me.validate()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    m = _mat(ctx, mat)
    if m is not None:
        me.materials.append(m)
    ctx.coll(coll).objects.link(ob)
    return ob


def grid_faces(nu, nv, closed_u=False):
    faces = []
    cu = nu if closed_u else nu - 1
    for j in range(nv - 1):
        for i in range(cu):
            i2 = (i + 1) % nu
            faces.append((j * nu + i, j * nu + i2, (j + 1) * nu + i2, (j + 1) * nu + i))
    return faces


def subsurf(ob, levels=1, render=None):
    m = ob.modifiers.new('Subsurf', 'SUBSURF')
    m.levels = levels
    m.render_levels = levels if render is None else render
    return m


def solidify(ob, thick_ft, offset=1.0):
    m = ob.modifiers.new('Solidify', 'SOLIDIFY')
    m.thickness = thick_ft * FT
    m.offset = offset
    m.use_even_offset = True
    m.use_quality_normals = True
    return m


def smooth_all(ob):
    ob.data.shade_smooth()


# ------------------------------------------------------------------------------ lathe
def lathe(ctx, name, profile, center, mat=None, coll='zone', segs=64, cap_top=True, cap_bottom=True):
    """Surface of revolution about the vertical axis through `center` (x, y0, z).
    profile: list of (radius_ft, height_ft) from bottom to top (heights relative to y0)."""
    cx, cy, cz = center
    verts, faces = [], []
    n = len(profile)
    for (r, h) in profile:
        for k in range(segs):
            a = 2 * math.pi * k / segs
            verts.append((cx + r * math.cos(a), cy + h, cz + r * math.sin(a)))
    for j in range(n - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            # outward-facing winding (SCENE right-handed, y up)
            faces.append((j * segs + k, (j + 1) * segs + k, (j + 1) * segs + k2, j * segs + k2))
    if cap_bottom and profile[0][0] > 1e-6:
        verts.append((cx, cy + profile[0][1], cz))
        c = len(verts) - 1
        for k in range(segs):
            faces.append((c, k, (k + 1) % segs))
    if cap_top and profile[-1][0] > 1e-6:
        verts.append((cx, cy + profile[-1][1], cz))
        c = len(verts) - 1
        base = (n - 1) * segs
        for k in range(segs):
            faces.append((c, base + (k + 1) % segs, base + k))
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    _fix_normals(ob)
    return ob


def _fix_normals(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.shade_smooth()


# ------------------------------------------------------------------------------ pillow
def pillow(ctx, name, w, h, t, origin, U, V, N, mat=None, coll='zone', n=22, seed=0, pinch=0.07,
           squash=0.0, wrinkle=0.02):
    """Pillow/cushion: w along U, h along V, thickness t along N (unit SCENE vectors).
    origin = centre of the pillow. Seam edge with pinched ('eared') corners."""
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 50, rnd.random() * 50, rnd.random() * 50))
    U, V, N = Vector(U).normalized(), Vector(V).normalized(), Vector(N).normalized()
    O = Vector(origin)
    verts = []
    idx = {}

    def surf(i, j, side):
        s = -1 + 2 * i / n
        r = -1 + 2 * j / n
        x = s * w / 2 * (1 - pinch * (1 - r * r))
        y = r * h / 2 * (1 - pinch * (1 - s * s))
        prof = max(0.0, (1 - abs(s) ** 2.6) * (1 - abs(r) ** 2.6)) ** 0.55
        z = side * t / 2 * prof
        # gentle crumple
        p = Vector((x, y, z)) * 1.7 + off
        z += side * wrinkle * prof * noise.noise(p)
        x += wrinkle * 0.6 * noise.noise(p + Vector((7, 0, 0))) * prof
        if side < 0:
            z -= squash * prof * t
        return O + U * x + V * y + N * z

    def vid(i, j, side):
        edge = i in (0, n) or j in (0, n)
        key = (i, j, 0 if edge else side)
        if key not in idx:
            idx[key] = len(verts)
            verts.append(tuple(surf(i, j, side if not edge else 1)))
        return idx[key]

    faces = []
    for side in (1, -1):
        for j in range(n):
            for i in range(n):
                q = [vid(i, j, side), vid(i + 1, j, side), vid(i + 1, j + 1, side), vid(i, j + 1, side)]
                faces.append(tuple(q) if side > 0 else tuple(reversed(q)))
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    _fix_normals(ob)
    subsurf(ob, 1)
    return ob


# ------------------------------------------------------------------------------ drape
def drape_sheet(ctx, name, x0, x1, z0, z1, ytop, *, head=None, drape_side=0.7, drape_foot=0.7,
                radius=0.12, step=0.08, mat=None, coll='zone', thick=0.06, seed=1, fold_amp=0.035,
                top_amp=0.025, foot_dir=1, skew=0.0):
    """A cloth sheet lying on the rectangle x0..x1 (length, head->foot when foot_dir=+1),
    z0..z1 (width) at height ytop, hanging over both long sides and the foot edge with rounded
    edges, natural pointed corners and soft vertical folds. head: x where the sheet starts
    (defaults x0, no drape there). Returns the object (solidified outward, subdivided)."""
    rnd = random.Random(seed)
    off = Vector((rnd.random() * 90, rnd.random() * 90, rnd.random() * 90))
    W = z1 - z0
    zc = (z0 + z1) / 2
    hx = x0 if head is None else head
    L = (x1 - hx) if foot_dir > 0 else (hx - x0)
    us = []          # along length p (0..L+drape_foot)
    p = 0.0
    while p < L + drape_foot - 1e-6:
        us.append(p)
        p += step if p < L - 0.3 or p > L + 0.4 else step * 0.5
    us.append(L + drape_foot)
    qs = []
    q = -W / 2 - drape_side
    while q < W / 2 + drape_side - 1e-6:
        qs.append(q)
        near_edge = abs(abs(q) - W / 2) < 0.35
        q += step * 0.5 if near_edge else step
    qs.append(W / 2 + drape_side)
    arc = math.pi * radius / 2

    def bend(e):
        """overhang e beyond an edge -> (outward offset, drop)."""
        if e <= 0:
            return e, 0.0
        if e < arc:
            th = e / radius
            return radius * math.sin(th), radius * (1 - math.cos(th))
        return radius, radius + (e - arc)

    verts = []
    for pv in us:
        for qv in qs:
            ep = pv - L
            eq = abs(qv) - W / 2
            sq = 1 if qv >= 0 else -1
            if ep > 0 and eq > 0:
                e = math.hypot(ep, eq)
                dp, dq = ep / e, eq / e
                o, d = bend(e)
                P = L + dp * o
                Q = sq * (W / 2 + dq * o)
                drop = d
            elif ep > 0:
                o, d = bend(ep)
                P, Q, drop = L + o, qv, d
            elif eq > 0:
                o, d = bend(eq)
                P, Q, drop = pv, sq * (W / 2 + o), d
            else:
                P, Q, drop = pv, qv, 0.0
            # folds grow with the drop; gentle puff on top
            nv = noise.noise(Vector((pv * 1.3, qv * 1.3, 0)) + off)
            hang = max(0.0, drop - radius)
            fold = fold_amp * (0.3 + hang * 1.6) * noise.noise(Vector((pv * 2.2 + qv * 2.2, hang * 0.6, 3.0)) + off)
            if drop < 1e-6:
                cr = 1.0 - abs(noise.noise(Vector((pv * 1.9 + qv * 0.6, qv * 2.3, 7.0)) + off))
                y = ytop + top_amp * nv + top_amp * 0.9 * (cr ** 4) - top_amp * 0.3
            else:
                y = ytop - drop
            X = hx + foot_dir * P
            Z = zc + Q
            if drop > 1e-6:
                # push folds outward from the bed along the local edge normal
                if ep > 0 and eq <= 0:
                    X += foot_dir * fold
                elif eq > 0 and ep <= 0:
                    Z += sq * fold
                else:
                    X += foot_dir * fold * 0.7
                    Z += sq * fold * 0.7
            if skew:
                Z += skew * (X - (x0 + x1) / 2)
            verts.append((X, y, Z))
    nu = len(qs)
    nv = len(us)
    faces = grid_faces(nu, nv)
    if foot_dir < 0:
        faces = [tuple(reversed(f)) for f in faces]
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    # make normals point up (outward)
    me = ob.data
    me.update()
    up = sum((p.normal.z for p in me.polygons), 0.0)
    if up < 0:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    me.shade_smooth()
    solidify(ob, thick, offset=1.0)
    subsurf(ob, 1)
    return ob


# ------------------------------------------------------------------------------ curtain
def wave_curtain(ctx, name, axis_pts, y0, y1, amp=0.14, wavelength=0.42, mat=None, coll='zone',
                 thick=0.012, seed=3, along='x', fixed=0.0, normal_sign=1):
    """Sheer wave-fold curtain panel: runs along `along` from axis_pts[0] to axis_pts[1] at the
    other horizontal coordinate `fixed`, from y0 (hem) to y1 (heading). Folds deepen slightly
    toward the hem; the hem has a soft irregularity."""
    rnd = random.Random(seed)
    a0, a1 = axis_pts
    n_u = max(8, int(abs(a1 - a0) / 0.035))
    n_v = 40
    verts = []
    for j in range(n_v + 1):
        v = j / n_v
        y = y0 + (y1 - y0) * v
        for i in range(n_u + 1):
            u = i / n_u
            a = a0 + (a1 - a0) * u
            ph = 2 * math.pi * (a - a0) / wavelength
            depth = amp * (1.0 + 0.25 * (1 - v)) * (0.85 + 0.3 * noise.noise(Vector((a * 3, 0.5, seed))))
            o = depth * math.sin(ph) + 0.02 * noise.noise(Vector((a * 2.5, y * 0.4, seed + 9)))
            yy = y + (0.015 * noise.noise(Vector((a * 4, 0, seed))) if j == 0 else 0)
            if along == 'x':
                verts.append((a, yy, fixed + normal_sign * o))
            else:
                verts.append((fixed + normal_sign * o, yy, a))
    faces = grid_faces(n_u + 1, n_v + 1)
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    solidify(ob, thick, offset=0.0)
    return ob


def folded_item(ctx, name, cx, y0, cz, w, d, h, rot, mat, coll):
    """Folded knit / tee: two soft layers so the fold seam reads; w along x, d along z."""
    h1 = h * 0.56
    ctx.box_c(name + ' a', (cx, y0 + h1 / 2, cz), (w, h1, d), rot, mat, coll, bevel=min(0.045, h1 * 0.45), segments=4)
    h2 = h - h1 + 0.006
    ctx.box_c(name + ' b', (cx - 0.012, y0 + h1 - 0.006 + h2 / 2, cz + 0.006), (w - 0.025, h2, d - 0.03), rot + 0.01,
              mat, coll, bevel=min(0.05, h2 * 0.48), segments=4)


def arch_outline(z0, z1, y0, y1, n_arc=40):
    """Closed outline (z, y) of an arch-top rectangle, counter-clockwise seen from +x."""
    r = (z1 - z0) / 2
    zc = (z0 + z1) / 2
    yc = y1 - r
    pts = [(z1, y0), (z1, yc)]
    for k in range(1, n_arc):
        a = math.pi * k / n_arc
        pts.append((zc + r * math.cos(a), yc + r * math.sin(a)))
    pts += [(z0, yc), (z0, y0)]
    return pts


def uv_project(ob, axis_u, axis_v, u0, u1, v0, v1):
    """Planar UVs from SCENE-feet world coords: axis_* in 'x','y','z'."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name='UVMap')
    uv = me.uv_layers.active.data
    comp = {'x': lambda p: p.x / FT, 'y': lambda p: p.z / FT, 'z': lambda p: -p.y / FT}
    fu, fv = comp[axis_u], comp[axis_v]
    # matrix_world of a just-created object is still identity until the depsgraph updates; the basis
    # matrix is computed from loc/rot/scale immediately (objects here are unparented)
    mw = ob.matrix_basis if ob.parent is None else ob.matrix_world
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = mw @ me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = ((fu(p) - u0) / (u1 - u0), (fv(p) - v0) / (v1 - v0))


def prism_x(ctx, name, outline_zy, x0, x1, mat, coll, inner=None):
    """Closed prism extruded along x between x0 and x1 from a convex (z, y) outline. With `inner`
    (same point count) builds a frame ring instead of a solid."""
    n = len(outline_zy)
    verts, faces = [], []
    if inner is None:
        for xx in (x0, x1):
            for (z, y) in outline_zy:
                verts.append((xx, y, z))
        faces.append(tuple(range(n)))
        faces.append(tuple(range(2 * n - 1, n - 1, -1)))
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((k, k2, n + k2, n + k))
    else:
        for xx in (x0, x1):
            for (z, y) in outline_zy:
                verts.append((xx, y, z))
            for (z, y) in inner:
                verts.append((xx, y, z))
        o0, i0, o1, i1 = 0, n, 2 * n, 3 * n
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((o0 + k, o0 + k2, i0 + k2, i0 + k))          # face x0
            faces.append((o1 + k, i1 + k, i1 + k2, o1 + k2))          # face x1
            faces.append((o0 + k, o1 + k, o1 + k2, o0 + k2))          # outer side
            faces.append((i0 + k, i0 + k2, i1 + k2, i1 + k))          # inner side
    ob = mesh_ft(ctx, name, verts, faces, mat, coll)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def tube(ctx, name, pts, r, mat, coll, segs=8, caps=True):
    """Round wire tube along a SCENE-feet polyline (hanger hooks, rails)."""
    verts, faces = [], []
    npt = len(pts)
    prev_a = None
    for i, p in enumerate(pts):
        p = Vector(p)
        t = (Vector(pts[min(i + 1, npt - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        if prev_a is None:
            a = t.cross(Vector((1, 0, 0)))
            if a.length < 1e-3:
                a = t.cross(Vector((0, 1, 0)))
        else:                                   # parallel transport: no twisting along the path
            a = prev_a - t * prev_a.dot(t)
        a.normalize()
        prev_a = a
        b = t.cross(a)
        for k in range(segs):
            th = 2 * math.pi * k / segs
            verts.append(tuple(p + (a * math.cos(th) + b * math.sin(th)) * r))
    for i in range(npt - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    if caps:
        faces.append(tuple(range(segs - 1, -1, -1)))
        faces.append(tuple((npt - 1) * segs + k for k in range(segs)))
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    _fix_normals(ob)
    return ob


def hook_path(x, rod_y, rod_z, rod_r, neck_y, n=14):
    """Wire hanger hook in the (z, y) plane at x: a '?' that wraps over the rod (centre rod_y, rod_z,
    radius rod_r) and drops to the hanger body at neck_y below the rod centre."""
    R = rod_r + 0.014
    pts = []
    a0, a1 = math.radians(205), math.radians(-25)     # front-low -> over the top -> back-low
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        pts.append((x, rod_y + R * math.sin(a), rod_z + R * math.cos(a)))
    start = pts[0]
    neck = [(x, neck_y, rod_z), (x, (neck_y + start[1]) / 2 - 0.01, rod_z + (start[2] - rod_z) * 0.6)]
    return neck + pts
