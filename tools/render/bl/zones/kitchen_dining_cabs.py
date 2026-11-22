"""Cabinetry helpers for the vintage kitchen (runs inside Blender; SCENE feet).

* Face frames map a cabinet front's local (u along the face, v up, w out of the face) to SCENE:
  'mz' faces -z (south-wall runs), 'pz' faces +z, 'mx' faces -x (east-wall run), 'px' faces +x.
* Acc accumulates many pieces (shaker doors and drawers, boxes, glazed frames) into ONE mesh per
  material, so a whole run is a single object. Each piece is a closed solid and the normals are
  recalculated per piece, then a small angle-limited bevel softens every edge.
* sweep() runs a moulding profile along a plan polyline with true mitres (crown mouldings).
* Hardware (knobs, cup pulls, appliance pulls) is built once at the origin and instanced.
* PlanFace is a face frame in feet on the ARCHITECT'S plan (for fitted pieces that must be true to size
  there, e.g. the refrigerator); tube_handle() is an appliance handle whose part names the caller chooses.

Warp classes (bl/warp.py): run meshes are named '... panel ...' / '... cove ...' (fitted: reshaped with
the room). Knobs and cup pulls on the fitted fronts are named '... hardware panel' (fitted too), so
each one follows the exact point of the front it is mounted on: as loose pieces they were clustered
with whatever their plan box touched (the olive canopy over the east run end carried one drawer pull
1in off its drawer). The ~3.5% x/z scale this gives a 1in knob is invisible. Long appliance pulls stay
loose ('... pull').
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common import FT, ft2bl
from .kitchen_dining_geo import P


class Face:
    def __init__(self, facing, plane):
        self.facing, self.plane = facing, plane

    def __call__(self, u, v, w):
        f, p = self.facing, self.plane
        if f == 'mz':
            return (u, v, p - w)
        if f == 'pz':
            return (u, v, p + w)
        if f == 'mx':
            return (p - w, v, u)
        return (p + w, v, u)

    @property
    def rot(self):
        """Blender Euler that turns a +Z-axis (Blender up) hardware model to face out of this face."""
        return {'mz': (-math.pi / 2, 0, 0), 'pz': (math.pi / 2, 0, 0),
                'mx': (0, -math.pi / 2, 0), 'px': (0, math.pi / 2, 0)}[self.facing]


class PlanFace(Face):
    """A Face whose plane, u and w are feet on the ARCHITECT'S plan instead of the concept plan. xinv / zinv
    carry a built x / z back to the concept plan the zone is built on (the inverses of the relayout maps that
    bl/warp.py applies to the zone), so a FITTED piece built in this frame has exactly these numbers after the
    warp. Used where a piece has to be true to size and symmetric on the built plan although a breakpoint of
    the map runs through it (the refrigerator: the map's slope changes at concept x 23.278, inside its bay)."""

    def __init__(self, facing, plane, xinv, zinv):
        super().__init__(facing, plane)
        self.xinv, self.zinv = xinv, zinv

    def __call__(self, u, v, w):
        x, y, z = super().__call__(u, v, w)
        return (self.xinv(x), y, self.zinv(z))


class Acc:
    """Accumulates closed solids into one bmesh."""

    def __init__(self):
        self.bm = bmesh.new()
        self.pieces = 0

    def _v(self, p):
        return self.bm.verts.new(P(*p))

    def _f(self, vs):
        try:
            return self.bm.faces.new(vs)
        except ValueError:
            return None

    def _close(self, verts):
        faces = list({f for v in verts for f in v.link_faces})
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        self.pieces += 1

    def box(self, F, u0, u1, v0, v1, w0, w1):
        """Box in a face frame (w0 < w1; w=0 is the face plane, +w out of it)."""
        vs = [self._v(F(u, v, w)) for w in (w0, w1) for v in (v0, v1) for u in (u0, u1)]
        # index: w*4 + v*2 + u
        quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        for q in quads:
            self._f([vs[i] for i in q])
        self._close(vs)

    def wbox(self, x0, x1, y0, y1, z0, z1):
        """World (SCENE) axis-aligned box."""
        self.box(Face('pz', 0.0), x0, x1, y0, y1, z0, z1)

    def shaker(self, F, u0, u1, v0, v1, t=0.0625, sw=0.19, rw=None, recess=0.022, glass=False, slab=False):
        """Five-piece shaker front: outer face at w=0, back at w=-t, centre panel recessed by
        `recess` (or open when glass=True: the frame is a ring and the glass is separate).
        sw = stile width, rw = rail width (default sw). Narrow fronts fall back to a slab."""
        rw = sw if rw is None else rw
        if slab or (u1 - u0) < 2 * sw + 0.12 or (v1 - v0) < 2 * rw + 0.08:
            self.box(F, u0, u1, v0, v1, -t, 0.0)
            return
        iu0, iu1, iv0, iv1 = u0 + sw, u1 - sw, v0 + rw, v1 - rw
        O = [self._v(F(u, v, 0.0)) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        Bk = [self._v(F(u, v, -t)) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        I = [self._v(F(u, v, 0.0)) for u, v in ((iu0, iv0), (iu1, iv0), (iu1, iv1), (iu0, iv1))]
        wp = -t if glass else -recess
        Ip = [self._v(F(u, v, wp)) for u, v in ((iu0, iv0), (iu1, iv0), (iu1, iv1), (iu0, iv1))]
        for i in range(4):
            j = (i + 1) % 4
            self._f([O[i], O[j], Bk[j], Bk[i]])          # outer edges
            self._f([O[i], O[j], I[j], I[i]])            # front ring
            self._f([I[i], I[j], Ip[j], Ip[i]])          # pocket walls
        if glass:
            for i in range(4):
                j = (i + 1) % 4
                self._f([Bk[i], Bk[j], Ip[j], Ip[i]])    # back ring
        else:
            self._f(Ip)                                  # recessed panel
            self._f(Bk)                                  # back
        self._close(O + Bk + I + Ip)

    def poly_x(self, pts_zy, x0, x1):
        """Elevation polygon [(z, y), ...] extruded along x."""
        a = [self._v((x0, y, z)) for z, y in pts_zy]
        b = [self._v((x1, y, z)) for z, y in pts_zy]
        self._f(a)
        self._f(list(reversed(b)))
        n = len(pts_zy)
        for i in range(n):
            j = (i + 1) % n
            self._f([a[i], a[j], b[j], b[i]])
        self._close(a + b)

    def poly_u(self, F, pts_wv, u0, u1):
        """Section polygon [(w, v), ...] in a face frame, extruded along the face from u0 to u1."""
        a = [self._v(F(u0, v, w)) for w, v in pts_wv]
        b = [self._v(F(u1, v, w)) for w, v in pts_wv]
        self._f(a)
        self._f(list(reversed(b)))
        n = len(pts_wv)
        for i in range(n):
            j = (i + 1) % n
            self._f([a[i], a[j], b[j], b[i]])
        self._close(a + b)

    def poly_z(self, pts_xy, z0, z1):
        a = [self._v((x, y, z0)) for x, y in pts_xy]
        b = [self._v((x, y, z1)) for x, y in pts_xy]
        self._f(a)
        self._f(list(reversed(b)))
        n = len(pts_xy)
        for i in range(n):
            j = (i + 1) % n
            self._f([a[i], a[j], b[j], b[i]])
        self._close(a + b)

    def poly_y(self, pts_xz, y0, y1):
        """Plan polygon [(x, z), ...] extruded from y0 to y1."""
        a = [self._v((x, y0, z)) for x, z in pts_xz]
        b = [self._v((x, y1, z)) for x, z in pts_xz]
        self._f(a)
        self._f(list(reversed(b)))
        n = len(pts_xz)
        for i in range(n):
            j = (i + 1) % n
            self._f([a[i], a[j], b[j], b[i]])
        self._close(a + b)

    def done(self, g, name, mat, coll, bevel=0.004, seg=2, smooth_deg=35):
        if not self.bm.faces:
            self.bm.free()
            return None
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        me.materials.append(g._mat(mat))
        ob = bpy.data.objects.new(name, me)
        g._link(ob, coll)
        if bevel:
            m = ob.modifiers.new('Bevel', 'BEVEL')
            m.width = bevel * FT
            m.segments = seg
            m.limit_method = 'ANGLE'
            m.harden_normals = True
        me.shade_smooth()
        try:
            me.set_sharp_from_angle(angle=math.radians(smooth_deg))
        except Exception:
            pass
        return ob


# ------------------------------------------------------------------------------- mouldings
def cyma(w0, w1, y0, y1, n=12):
    """Ogee / cyma-recta curve from (w0, y0) to (w1, y1)."""
    out = []
    for k in range(n + 1):
        t = k / n
        out.append((w0 + (w1 - w0) * (t - math.sin(2 * math.pi * t) / (2 * math.pi)), y0 + (y1 - y0) * t))
    return out


def crown_profile(proj=0.24, h=0.445):
    """Cabinet crown (w out of the face, y up from the base): fillet, cyma, top fillet."""
    pts = [(0.0, 0.0), (0.035, 0.0), (0.035, 0.06), (0.055, 0.08)]
    pts += cyma(0.055, proj - 0.025, 0.09, h - 0.07)[1:]
    pts += [(proj, h - 0.06), (proj, h), (0.0, h)]
    return pts


def sweep(g, name, path, profile, y0, mat, coll, closed_ends=True):
    """Sweep a closed profile [(w, y), ...] (w = projection outward) along a plan polyline
    [(x, z), ...] whose outward side is to the LEFT walking from point to point when viewed from
    above with +x right and +z down (i.e. outward normal = (dz, -dx) normalised ... see code).
    Corners are true mitres."""
    n = len(path)
    segs = []
    for i in range(n - 1):
        (x0, z0), (x1, z1) = path[i], path[i + 1]
        L = math.hypot(x1 - x0, z1 - z0)
        segs.append(((x1 - x0) / L, (z1 - z0) / L))
    norms = [(d[1], -d[0]) for d in segs]          # outward (left-hand) normal in plan
    offs = []
    for i in range(n):
        if i == 0:
            nx, nz = norms[0]
        elif i == n - 1:
            nx, nz = norms[-1]
        else:
            a, b = norms[i - 1], norms[i]
            s = 1.0 + a[0] * b[0] + a[1] * b[1]
            nx, nz = (a[0] + b[0]) / s, (a[1] + b[1]) / s
        offs.append((nx, nz))
    bm = bmesh.new()
    rings = []
    for (x, z), (nx, nz) in zip(path, offs):
        rings.append([bm.verts.new(P(x + nx * w, y0 + y, z + nz * w)) for w, y in profile])
    m = len(profile)
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(m):
            k2 = (k + 1) % m
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    if closed_ends:
        bm.faces.new(rings[0])
        bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(g._mat(mat))
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    ob = bpy.data.objects.new(name, me)
    return g._link(ob, coll)


# -------------------------------------------------------------------------------- hardware
def _revolve(profile, segs=32):
    """Surface of revolution about Blender +Z at the origin, profile [(r, h), ...] in feet."""
    bm = bmesh.new()
    rings = []
    for r, h in profile:
        if r <= 1e-6:
            rings.append([bm.verts.new((0.0, 0.0, h * FT))])
        else:
            rings.append([bm.verts.new((r * FT * math.cos(2 * math.pi * k / segs), r * FT * math.sin(2 * math.pi * k / segs), h * FT))
                          for k in range(segs)])
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(segs):
            k2 = (k + 1) % segs
            if len(A) == 1 and len(B) == 1:
                continue
            if len(A) == 1:
                bm.faces.new((A[0], B[k2], B[k]))
            elif len(B) == 1:
                bm.faces.new((A[k], A[k2], B[0]))
            else:
                bm.faces.new((A[k], A[k2], B[k2], B[k]))
    return bm


def _mesh(name, bm, mat, smooth_deg=50):
    me = bpy.data.meshes.new(name)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(smooth_deg))
    except Exception:
        pass
    return me


_SRC = {}


def knob_mesh(mat):
    """1-1/4in mushroom knob with a round back rose, ~1-1/8in projection (axis +Z)."""
    if 'knob' not in _SRC:
        prof = [(0.0, 0.0), (0.042, 0.0), (0.042, 0.008), (0.03, 0.016), (0.019, 0.03), (0.017, 0.055),
                (0.03, 0.068), (0.048, 0.08), (0.053, 0.088), (0.05, 0.096), (0.035, 0.1), (0.0, 0.102)]
        _SRC['knob'] = _mesh('kd knob', _revolve(prof, 32), mat)
    return _SRC['knob']


def cup_pull_mesh(mat):
    """3in unlacquered-brass bin (cup) pull: a curved hood open underneath, on two flat end ears.
    Local frame: X along the face, Z out of the face, Y up."""
    if 'cup' not in _SRC:
        bm = bmesh.new()
        half, depth, top, bot = 0.135, 0.062, 0.045, -0.035
        th = 0.008
        nu, nv = 24, 12
        grid_o, grid_i = [], []
        for i in range(nu + 1):
            s = -1 + 2 * i / nu
            ex = max(1 - abs(s) ** 6, 0.0) ** 0.5
            ro, ri = [], []
            for j in range(nv + 1):
                t = j / nv
                ang = t * math.radians(115)
                y = top + (bot - top) * (1 - math.cos(ang * 0.9)) / (1 - math.cos(math.radians(115) * 0.9))
                z = depth * math.sin(min(ang, math.pi / 2)) * ex
                x = s * half * (0.82 + 0.18 * ex)
                ro.append(bm.verts.new((x * FT, y * FT, (z + th * ex) * FT)))
                ri.append(bm.verts.new((x * FT, y * FT, z * FT)))
            grid_o.append(ro)
            grid_i.append(ri)
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((grid_o[i][j], grid_o[i + 1][j], grid_o[i + 1][j + 1], grid_o[i][j + 1]))
                bm.faces.new((grid_i[i][j], grid_i[i][j + 1], grid_i[i + 1][j + 1], grid_i[i + 1][j]))
        for i in range(nu):               # close the rim (bottom lip) and the top edge
            for j in (0, nv):
                bm.faces.new((grid_o[i][j], grid_i[i][j], grid_i[i + 1][j], grid_o[i + 1][j]))
        for i in (0, nu):
            for j in range(nv):
                bm.faces.new((grid_o[i][j], grid_o[i][j + 1], grid_i[i][j + 1], grid_i[i][j]))
        # mounting ears (flat plates on the face at both ends)
        for sx in (-1, 1):
            x0, x1 = sorted((sx * (half - 0.02), sx * (half + 0.018)))
            y0, y1 = top - 0.03, top + 0.012
            vs = [bm.verts.new((x * FT, y * FT, z * FT)) for z in (0.0, 0.012) for y in (y0, y1) for x in (x0, x1)]
            for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
                bm.faces.new([vs[i] for i in q])
        _SRC['cup'] = _mesh('kd cup pull', bm, mat, 60)
    return _SRC['cup']


def place_hw(g, me, name, F, u, v, coll, rot_local=0.0, w=0.0):
    """Instance a hardware mesh (axis +Z out of the face, local Y up) at face point (u, v), seated at
    depth w (0 = the front's outer face; -recess on a shaker front's recessed centre panel)."""
    ob = bpy.data.objects.new(name, me)
    x, y, z = F(u, v, w)
    ob.location = ft2bl(x, y, z)
    # local: X along u, Y up (v), Z out (w)
    ux = Vector(P(*F(1, 0, 0))) - Vector(P(*F(0, 0, 0)))
    vy = Vector(P(*F(0, 1, 0))) - Vector(P(*F(0, 0, 0)))
    wz = Vector(P(*F(0, 0, 1))) - Vector(P(*F(0, 0, 0)))
    M = Matrix((ux.normalized(), vy.normalized(), wz.normalized())).transposed()
    if M.determinant() < 0:              # keep a proper rotation (mirror the local X)
        M = Matrix((-ux.normalized(), vy.normalized(), wz.normalized())).transposed()
    ob.rotation_euler = M.to_euler()
    return g._link(ob, coll)


def knob(g, mat, F, u, v, coll, name='kd brass door hardware panel', w=0.0):
    return place_hw(g, knob_mesh(mat), name, F, u, v, coll, w=w)


def cup_pull(g, mat, F, u, v, coll, name='kd brass drawer hardware panel', w=0.0):
    return place_hw(g, cup_pull_mesh(mat), name, F, u, v, coll, w=w)


def bar_pull(g, mat, F, u0, v0, u1, v1, coll, name='kd appliance pull', r=0.028, standoff=0.12):
    """Long round appliance pull on two posts from (u0, v0) to (u1, v1) on face F."""
    out = []
    a = F(u0, v0, standoff)
    b = F(u1, v1, standoff)
    du, dv = u1 - u0, v1 - v0
    L = math.hypot(du, dv)
    inset = min(0.12, L * 0.12)
    ext = 0.06
    a2 = F(u0 - du / L * ext, v0 - dv / L * ext, standoff)
    b2 = F(u1 + du / L * ext, v1 + dv / L * ext, standoff)
    out.append(g.cyl_axis(name, a2, b2, r, mat, 20, coll))
    for t in (inset / L, 1 - inset / L):
        uu, vv = u0 + du * t, v0 + dv * t
        out.append(g.cyl_axis(name + ' post', F(uu, vv, 0.0), F(uu, vv, standoff), r * 0.6, mat, 16, coll))
        out.append(g.cyl_axis(name + ' post foot', F(uu, vv, 0.0), F(uu, vv, 0.018), r * 1.25, mat, 20, coll))
    for p in (a2, b2):                   # rounded end caps
        pass
    return out


def tube_handle(g, mat, F, u0, v0, u1, v1, coll, names, r=0.033, standoff=0.165, post_r=0.02, foot_r=0.04,
                inset=0.14):
    """Appliance handle: a round bar from (u0, v0) to (u1, v1) on face F (w=0 is the door's face), its axis
    `standoff` in front of the face, on two posts `inset` from its ends, each on a round foot.
    names = (bar, post, foot): the caller chooses them by warp class (bl/warp.py). bar_pull()'s '... pull' /
    '... post' names are loose; a handle on a FITTED front needs fitted names to stay on it."""
    du, dv = u1 - u0, v1 - v0
    L = math.hypot(du, dv)
    bar = g.cyl_axis(names[0], F(u0, v0, standoff), F(u1, v1, standoff), r, mat, 28, coll)
    g.bevel_mod(bar, r * 0.3, 3)         # eased ends
    out = [bar]
    for t in (inset / L, 1 - inset / L):
        uu, vv = u0 + du * t, v0 + dv * t
        out.append(g.cyl_axis(names[1], F(uu, vv, 0.0), F(uu, vv, standoff), post_r, mat, 20, coll))
        out.append(g.cyl_axis(names[2], F(uu, vv, 0.0), F(uu, vv, 0.014), foot_r, mat, 28, coll))
    return out
