"""Mesh helpers for the living zone (runs inside Blender).

All generators work in SCENE feet in a *local* frame (x east, y up, z south) and return
(verts, faces); `obj()` converts to Blender meters and creates the object. Furniture is built
around a local origin and parented to an Empty (`group()`), which is then placed with
common.place(). Local "front" of every piece is +x (SCENE east); rot = facing(dx, dz) turns it.
"""
import math

import bpy
import numpy as np

from ..common import FT


# ----------------------------------------------------------------------------- objects
def to_bl(v):
    x, y, z = v
    return (x * FT, -z * FT, y * FT)


def obj(ctx, name, verts, faces, mat=None, coll='zone_living', parent=None, smooth=True,
        subsurf=0, uvs=None, weld=False):
    """Object from SCENE-feet local verts. mat: key str or bpy Material (or list of them)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([to_bl(v) for v in verts], [], faces)
    if weld:
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bm.to_mesh(me)
        bm.free()
    if uvs is not None:
        uvl = me.uv_layers.new(name='UVMap')
        loops_uv = []
        for poly in me.polygons:
            for li in poly.loop_indices:
                loops_uv.append(uvs[me.loops[li].vertex_index])
        uvl.data.foreach_set('uv', [c for uv in loops_uv for c in uv])
    me.validate()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    for m in (mat if isinstance(mat, (list, tuple)) else [mat]):
        if m is not None:
            me.materials.append(ctx.mat(m) if isinstance(m, str) else m)
    ctx.coll(coll).objects.link(ob)
    if parent is not None:
        ob.parent = parent
    if subsurf:
        sm = ob.modifiers.new('Subsurf', 'SUBSURF')
        sm.levels = min(subsurf, 2)
        sm.render_levels = subsurf
    return ob


def group(ctx, name, coll='zone_living'):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.3
    ctx.coll(coll).objects.link(e)
    return e


def parent_to(objs, parent):
    for o in objs:
        o.parent = parent


def facing(dx, dz):
    """rot (radians about +Y) that turns local +x toward SCENE direction (dx, dz)."""
    return math.atan2(-dz, dx)


def bevel(ob, width_ft, segments=3, angle=30.0, harden=True):
    m = ob.modifiers.new('Bevel', 'BEVEL')
    m.width = width_ft * FT
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = harden
    m.use_clamp_overlap = True
    ob.data.shade_smooth()
    try:
        ob.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass
    return m


def translate(verts, dx=0.0, dy=0.0, dz=0.0):
    return [(x + dx, y + dy, z + dz) for x, y, z in verts]


def rot_y(verts, a, cx=0.0, cz=0.0):
    """Rotate SCENE-feet verts by a radians about +Y (same sense as `rot`) around (cx, cz)."""
    c, s = math.cos(a), math.sin(a)
    out = []
    for x, y, z in verts:
        px, pz = x - cx, z - cz
        # Blender rotation about Z by a: (bx, by) -> (bx c - by s, bx s + by c) with bx=x, by=-z
        bx, by = px * c - (-pz) * s, px * s + (-pz) * c
        out.append((bx + cx, y, -by + cz))
    return out


def rot_z_scene(verts, a, cx=0.0, cy=0.0):
    """Tilt verts about the SCENE z axis (in the x-y plane) by a radians (positive: +x toward +y)."""
    c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c, z) for x, y, z in verts]


def rot_x_scene(verts, a, cy=0.0, cz=0.0):
    """Rotate verts about the SCENE x axis (in the y-z plane); positive: +y toward +z."""
    c, s = math.cos(a), math.sin(a)
    return [(x, cy + (y - cy) * c - (z - cz) * s, cz + (y - cy) * s + (z - cz) * c) for x, y, z in verts]


# ------------------------------------------------------------------------ primitives
def _axis_coords(h, r, n, nmid):
    core = max(h - r, 0.0)
    band = [core + (h - core) * math.sin(k / n * math.pi / 2) for k in range(1, n + 1)]
    if core > 1e-6:
        mids = [-core + 2 * core * i / nmid for i in range(nmid + 1)]
    else:
        mids = [0.0]
    return [-b for b in reversed(band)] + mids + band


def rounded_box(hx, hy, hz, r, n=5, nmid=6, puff=0.0, puff_axis=1, rx=None, ry=None, rz=None):
    """Closed rounded box centred at the origin (half sizes hx, hy, hz feet, edge radius r).
    puff>0 inflates the faces normal to `puff_axis` (0=x, 1=y, 2=z) like a cushion.
    rx/ry/rz optionally override the radius per axis (elliptic rounding)."""
    rr = [rx if rx is not None else r, ry if ry is not None else r, rz if rz is not None else r]
    hs = [hx, hy, hz]
    rr = [min(rr[i], hs[i] * 0.999) for i in range(3)]
    cs = [_axis_coords(hs[i], rr[i], n, nmid) for i in range(3)]
    nx, ny, nz = (len(c) for c in cs)
    index = {}
    verts = []

    def vid(i, j, k):
        key = (i, j, k)
        if key not in index:
            index[key] = len(verts)
            verts.append((cs[0][i], cs[1][j], cs[2][k]))
        return index[key]

    faces = []
    # six faces, outward winding
    for i in (0, nx - 1):
        for j in range(ny - 1):
            for k in range(nz - 1):
                q = [vid(i, j, k), vid(i, j + 1, k), vid(i, j + 1, k + 1), vid(i, j, k + 1)]
                faces.append(q if i == nx - 1 else q[::-1])
    for j in (0, ny - 1):
        for i in range(nx - 1):
            for k in range(nz - 1):
                q = [vid(i, j, k), vid(i, j, k + 1), vid(i + 1, j, k + 1), vid(i + 1, j, k)]
                faces.append(q if j == ny - 1 else q[::-1])
    for k in (0, nz - 1):
        for i in range(nx - 1):
            for j in range(ny - 1):
                q = [vid(i, j, k), vid(i + 1, j, k), vid(i + 1, j + 1, k), vid(i, j + 1, k)]
                faces.append(q if k == nz - 1 else q[::-1])
    # round: clamp to the core box and push out by the (elliptic) radius
    core = [hs[a] - rr[a] for a in range(3)]
    out = []
    for p in verts:
        q = [max(-core[a], min(core[a], p[a])) for a in range(3)]
        d = [(p[a] - q[a]) / rr[a] if rr[a] > 1e-9 else 0.0 for a in range(3)]
        ln = math.sqrt(sum(c * c for c in d))
        if ln > 1e-9:
            p2 = [q[a] + rr[a] * d[a] / ln for a in range(3)]
        else:
            p2 = list(p)
        if puff:
            o = [a for a in range(3) if a != puff_axis]
            f = max(0.0, 1 - (p2[o[0]] / hs[o[0]]) ** 2) * max(0.0, 1 - (p2[o[1]] / hs[o[1]]) ** 2)
            p2[puff_axis] *= 1 + puff * f
        out.append(tuple(p2))
    return out, faces


def pillow(w, h, t, sq=None, n=30, pull=0.07, sag=0.12, chop=0.0, fill=0.55):
    """Throw pillow: in-plane size w (z) x h (y), thickness t (x), centred at the origin.
    Front and back grids meet at a seam along the outline (corners form soft 'ears'); the
    outline is pulled in at mid-edges and the fill sags slightly toward the bottom. `fill` is the
    dome exponent (lower = boxier); `chop` (fraction of h) pinches a V dent into the top edge."""
    verts, faces = [], []
    us = [-1 + 2 * i / (n - 1) for i in range(n)]
    for side in (1, -1):
        for r in us:                      # vertical
            for s_ in us:                 # horizontal
                z = w / 2 * s_ * (1 - pull * (1 - r * r))
                y = h / 2 * r * (1 - pull * (1 - s_ * s_))
                th = t / 2 * ((1 - s_ * s_) * (1 - r * r)) ** fill * (1 - sag * r)
                if chop:
                    dent = math.exp(-(s_ / 0.3) ** 2) * max(r, 0.0) ** 3
                    y -= chop * h * dent
                    th *= 1 - 0.35 * dent
                verts.append((side * th, y, z))
    for side in range(2):
        o = side * n * n
        for i in range(n - 1):
            for j in range(n - 1):
                a_, b_ = o + i * n + j, o + i * n + j + 1
                c_, d_ = o + (i + 1) * n + j + 1, o + (i + 1) * n + j
                # front (+x): seen from +x, z increases to the left... keep winding by orient below
                faces.append((a_, b_, c_, d_) if side == 0 else (a_, d_, c_, b_))
    return _orient_outward(verts, faces)


def rounded_rect_outline(w, d, r, n=10):
    """Plan outline (x, z) of a w (x) by d (z) rectangle with corner radius r, CCW from above
    (SCENE: x right, z down -> we just need a consistent order)."""
    r = min(r, w / 2 - 1e-4, d / 2 - 1e-4)
    cx, cz = w / 2 - r, d / 2 - r
    pts = []
    for (sx, sz, a0) in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append((sx * cx + r * math.cos(a), sz * cz + r * math.sin(a)))
    return pts


def prism(outline, y0, y1):
    """Extrude a plan outline [(x, z), ...] between heights y0..y1. Returns verts, faces."""
    n = len(outline)
    verts = [(x, y0, z) for x, z in outline] + [(x, y1, z) for x, z in outline]
    # determine winding so that the top face points up (+y). Signed area in (x, -z) plane.
    area = 0.0
    for i in range(n):
        x0, z0 = outline[i]
        x1, z1 = outline[(i + 1) % n]
        area += x0 * (-z1) - x1 * (-z0)
    top = list(range(n, 2 * n))
    bot = list(range(n))[::-1]
    if area < 0:
        top, bot = top[::-1], bot[::-1]
    faces = [tuple(top), tuple(bot)]
    for i in range(n):
        j = (i + 1) % n
        q = (i, j, n + j, n + i)
        faces.append(q if area >= 0 else q[::-1])
    return verts, faces


def lathe(profile, n=48, cap_bottom=True, cap_top=False, mod=None):
    """Revolve a profile [(r, y), ...] (bottom to top) about the local y axis.
    mod(theta, r, y) -> r lets callers add flutes. Returns verts, faces (outward normals)."""
    verts, faces = [], []
    m = len(profile)
    for j in range(n):
        th = 2 * math.pi * j / n
        c, s = math.cos(th), math.sin(th)
        for (r, y) in profile:
            rr = mod(th, r, y) if mod else r
            verts.append((rr * c, y, rr * s))
    for j in range(n):
        j2 = (j + 1) % n
        for i in range(m - 1):
            a, b = j * m + i, j * m + i + 1
            c_, d = j2 * m + i + 1, j2 * m + i
            faces.append((a, b, c_, d))
    if cap_bottom and profile[0][0] > 1e-6:
        verts.append((0.0, profile[0][1], 0.0))
        ci = len(verts) - 1
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((ci, j2 * m, j * m))
    if cap_top and profile[-1][0] > 1e-6:
        verts.append((0.0, profile[-1][1], 0.0))
        ci = len(verts) - 1
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((ci, j * m + m - 1, j2 * m + m - 1))
    # make winding outward: check one face normal against radial direction
    return _orient_outward(verts, faces)


def _orient_outward(verts, faces):
    V = np.array(verts)
    cen = V.mean(axis=0)
    flip_votes = 0
    for f in faces[:: max(1, len(faces) // 50)]:
        p = V[list(f)]
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(nrm, p.mean(axis=0) - cen) < 0:
            flip_votes += 1
        else:
            flip_votes -= 1
    if flip_votes > 0:
        faces = [tuple(reversed(f)) for f in faces]
    return verts, faces


def sweep_ring(sections):
    """Loft closed cross-section loops (list of lists of (x, y, z), same length) into a tube,
    capping both ends. Returns verts, faces."""
    k = len(sections[0])
    verts = [p for sec in sections for p in sec]
    faces = []
    for s in range(len(sections) - 1):
        for i in range(k):
            a = s * k + i
            b = s * k + (i + 1) % k
            faces.append((a, b, b + k, a + k))
    faces.append(tuple(range(k))[::-1])
    last = (len(sections) - 1) * k
    faces.append(tuple(range(last, last + k)))
    return _orient_outward(verts, faces)


def tube_along(points, radius, n=10):
    """Thin round tube following a polyline of SCENE-feet points (for stems, lamp arcs)."""
    P = np.array(points, dtype=float)
    verts, faces = [], []
    m = len(P)
    up = np.array([0.0, 0.0, 1.0])
    for i in range(m):
        t = P[min(i + 1, m - 1)] - P[max(i - 1, 0)]
        t /= np.linalg.norm(t) + 1e-12
        a = np.cross(t, up)
        if np.linalg.norm(a) < 1e-6:
            a = np.cross(t, np.array([1.0, 0.0, 0.0]))
        a /= np.linalg.norm(a)
        b = np.cross(t, a)
        rr = radius(i / (m - 1)) if callable(radius) else radius
        for j in range(n):
            th = 2 * math.pi * j / n
            verts.append(tuple(P[i] + rr * (math.cos(th) * a + math.sin(th) * b)))
    for i in range(m - 1):
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((i * n + j, i * n + j2, (i + 1) * n + j2, (i + 1) * n + j))
    faces.append(tuple(range(n))[::-1])
    faces.append(tuple(range((m - 1) * n, m * n)))
    return _orient_outward(verts, faces)


def box_verts(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    # outward winding in SCENE coords (to_bl is a proper rotation so winding is preserved)
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    return _orient_outward(v, f)


def merge(*parts):
    verts, faces = [], []
    for v, f in parts:
        o = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + o for i in face) for face in f)
    return verts, faces


def sock(sockets, name, typ='RGBA'):
    """Socket by name and type (ShaderNodeMix has same-named sockets for each data type)."""
    for x in sockets:
        if x.name == name and x.type == typ:
            return x
    return sockets[name]
