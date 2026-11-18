"""Geometry helpers for the kitchen_dining zone (runs inside Blender).

Everything takes SCENE feet (x east, y up, z south). Meshes are created directly in world
space (object at the origin) unless a helper says otherwise, so box-mapped library materials
line up across neighbouring parts.
"""
import math

import bmesh
import bpy
from mathutils import Vector

from ..common import FT, ft2bl

ZONE = 'zone_kitchen_dining'


def P(x, y, z):
    """SCENE feet -> Blender-local meters tuple."""
    return (x * FT, -z * FT, y * FT)


class Geo:
    def __init__(self, ctx, coll=ZONE):
        self.ctx = ctx
        self.root = ctx.coll(ZONE)
        self.coll_name = coll
        self.n_objects = 0

    # -------------------------------------------------------------- collections
    def sub(self, name):
        """Child collection of the zone collection; returns its name."""
        self.ctx.coll(name, ZONE)
        return name

    def _mat(self, mat):
        if mat is None:
            return None
        if isinstance(mat, str):
            return self.ctx.mat(mat)
        return mat

    def _link(self, ob, coll):
        self.ctx.coll(coll or self.coll_name).objects.link(ob)
        self.n_objects += 1
        return ob

    # -------------------------------------------------------------- primitives
    def box(self, name, x0, x1, y0, y1, z0, z1, mat=None, bevel=0.0, seg=2, coll=None):
        ob = self.ctx.box(name, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1),
                          mat, coll or self.coll_name, bevel, seg)
        self.n_objects += 1
        return ob

    def from_bmesh(self, name, bm, mats, coll=None, smooth=False, sharp_deg=None, loc=None, rot=0.0):
        me = bpy.data.meshes.new(name)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(me)
        bm.free()
        for m in (mats if isinstance(mats, (list, tuple)) else [mats]):
            if m is not None:
                me.materials.append(self._mat(m))
        if smooth:
            me.shade_smooth()
            if sharp_deg is not None:
                try:
                    me.set_sharp_from_angle(angle=math.radians(sharp_deg))
                except Exception:
                    pass
        ob = bpy.data.objects.new(name, me)
        if loc is not None:
            ob.location = ft2bl(*loc)
            ob.rotation_euler = (0, 0, rot)
        return self._link(ob, coll)

    def instance(self, src, name, loc, rot=0.0, coll=None):
        """Linked duplicate (shared mesh data) placed at SCENE loc, rotated about +Y."""
        ob = src.copy()
        ob.name = name
        ob.location = ft2bl(*loc)
        ob.rotation_euler = (0, 0, rot)
        return self._link(ob, coll)

    def poly_prism(self, name, pts_xz, y0, y1, mat, bevel=0.0, seg=2, coll=None):
        """Extrude a plan polygon [(x, z), ...] from y0 to y1."""
        bm = bmesh.new()
        bot = [bm.verts.new(P(x, y0, z)) for x, z in pts_xz]
        top = [bm.verts.new(P(x, y1, z)) for x, z in pts_xz]
        bm.faces.new(bot)
        bm.faces.new(list(reversed(top)))
        n = len(pts_xz)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((bot[i], bot[j], top[j], top[i]))
        ob = self.from_bmesh(name, bm, mat, coll)
        if bevel > 0:
            self.ctx.add_bevel(ob, bevel, seg)
        return ob

    def section_prism_z(self, name, pts_xy, z0, z1, mat, bevel=0.0, seg=2, coll=None):
        """Extrude an elevation polygon [(x, y), ...] along z from z0 to z1."""
        bm = bmesh.new()
        a = [bm.verts.new(P(x, y, z0)) for x, y in pts_xy]
        b = [bm.verts.new(P(x, y, z1)) for x, y in pts_xy]
        bm.faces.new(a)
        bm.faces.new(list(reversed(b)))
        n = len(pts_xy)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
        ob = self.from_bmesh(name, bm, mat, coll)
        if bevel > 0:
            self.ctx.add_bevel(ob, bevel, seg)
        return ob

    def cyl(self, name, x, y0, y1, z, r, mat, verts=40, coll=None, bevel=0.0):
        ob = self.ctx.cylinder(name, (x, (y0 + y1) / 2, z), r, abs(y1 - y0), mat, coll or self.coll_name, verts=verts)
        self.n_objects += 1
        if bevel > 0:
            self.ctx.add_bevel(ob, bevel, 2)
        return ob

    def cyl_axis(self, name, p0, p1, r, mat, verts=16, coll=None):
        """Cylinder between two SCENE points."""
        a, b = Vector(P(*p0)), Vector(P(*p1))
        d = b - a
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r * FT, radius2=r * FT, depth=d.length)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        if mat is not None:
            me.materials.append(self._mat(mat))
        ob = bpy.data.objects.new(name, me)
        ob.location = (a + b) / 2
        ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
        return self._link(ob, coll)

    def lathe(self, name, profile, cx, cz, mat, segs=48, coll=None, y_base=0.0, smooth=True, sharp_deg=50, build_only=False):
        """Surface of revolution about the vertical axis at (cx, cz).
        profile: [(r, y), ...] from bottom to top; r==0 points collapse onto the axis."""
        bm = bmesh.new()
        rings = []
        for r, y in profile:
            if r <= 1e-6:
                rings.append([bm.verts.new(P(cx, y_base + y, cz))])
            else:
                ring = []
                for k in range(segs):
                    a = 2 * math.pi * k / segs
                    ring.append(bm.verts.new(P(cx + r * math.cos(a), y_base + y, cz + r * math.sin(a))))
                rings.append(ring)
        for i in range(len(rings) - 1):
            A, B = rings[i], rings[i + 1]
            if len(A) == 1 and len(B) == 1:
                continue
            for k in range(segs):
                k2 = (k + 1) % segs
                if len(A) == 1:
                    bm.faces.new((A[0], B[k2], B[k]))
                elif len(B) == 1:
                    bm.faces.new((A[k], A[k2], B[0]))
                else:
                    bm.faces.new((A[k], A[k2], B[k2], B[k]))
        if build_only:
            return bm
        return self.from_bmesh(name, bm, mat, coll, smooth=smooth, sharp_deg=sharp_deg)

    def torus(self, name, cx, y, cz, R, r, mat, segs=96, rsegs=16, coll=None):
        bm = bmesh.new()
        rings = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ring = []
            for j in range(rsegs):
                b = 2 * math.pi * j / rsegs
                rr = R + r * math.cos(b)
                ring.append(bm.verts.new(P(cx + rr * math.cos(a), y + r * math.sin(b), cz + rr * math.sin(a))))
            rings.append(ring)
        for i in range(segs):
            A, B = rings[i], rings[(i + 1) % segs]
            for j in range(rsegs):
                j2 = (j + 1) % rsegs
                bm.faces.new((A[j], A[j2], B[j2], B[j]))
        return self.from_bmesh(name, bm, mat, coll, smooth=True)

    def ring_rect(self, name, cx, cz, R, w, y0, y1, mats, segs=128, coll=None, bottom_mat=1):
        """Flat ring of rectangular section (radial width w, height y1-y0). Bottom face uses
        material index `bottom_mat`, the rest index 0 (LED ring chandeliers, diffusers)."""
        bm = bmesh.new()
        prof = [(R - w / 2, y0), (R + w / 2, y0), (R + w / 2, y1), (R - w / 2, y1)]
        rings = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            ca, sa = math.cos(a), math.sin(a)
            rings.append([bm.verts.new(P(cx + r * ca, y, cz + r * sa)) for r, y in prof])
        for i in range(segs):
            A, B = rings[i], rings[(i + 1) % segs]
            for j in range(4):
                j2 = (j + 1) % 4
                f = bm.faces.new((A[j], A[j2], B[j2], B[j]))
                f.material_index = bottom_mat if j == 0 else 0
        return self.from_bmesh(name, bm, mats, coll, smooth=True, sharp_deg=45)

    def arc_wall(self, name, r_in, r_out, a0, a1, y0, ytop, mat, segs=40, coll=None, loc=None, rot=0.0):
        """Curved upholstered wall around the local origin: angles in radians measured from the
        local -z axis (the 'back'), sweeping toward +x then +z. ytop(angle) gives the top height.
        Returned object is placed at loc (SCENE) and rotated by rot."""
        bm = bmesh.new()
        rings = []
        for i in range(segs + 1):
            a = a0 + (a1 - a0) * i / segs
            dx, dz = math.sin(a), -math.cos(a)
            yt = ytop(a)
            rings.append([bm.verts.new(P(r * dx, y, r * dz)) for r, y in
                          ((r_in, y0), (r_out, y0), (r_out, yt), (r_in, yt))])
        for i in range(segs):
            A, B = rings[i], rings[i + 1]
            for j in range(4):
                j2 = (j + 1) % 4
                bm.faces.new((A[j], A[j2], B[j2], B[j]))
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
        return self.from_bmesh(name, bm, mat, coll, smooth=True, loc=loc, rot=rot)

    def tube(self, name, pts, r, mat, coll=None, res=12):
        """Round tube through SCENE points (poly spline), converted to a mesh."""
        cu = bpy.data.curves.new(name + '_c', 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = r * FT
        cu.bevel_resolution = 4
        cu.use_fill_caps = True
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            v = P(*p)
            sp.points[i].co = (v[0], v[1], v[2], 1.0)
        tmp = bpy.data.objects.new(name + '_tmp', cu)
        bpy.context.scene.collection.objects.link(tmp)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        bpy.data.objects.remove(tmp, do_unlink=True)
        bpy.data.curves.remove(cu)
        me.name = name
        me.shade_smooth()
        if mat is not None:
            me.materials.append(self._mat(mat))
        ob = bpy.data.objects.new(name, me)
        return self._link(ob, coll)

    @staticmethod
    def subsurf(ob, levels=2):
        m = ob.modifiers.new('Subsurf', 'SUBSURF')
        m.levels = levels
        m.render_levels = levels
        return m

    @staticmethod
    def bevel_mod(ob, width_ft, seg=3, limit='ANGLE', harden=False):
        m = ob.modifiers.new('Bevel', 'BEVEL')
        m.width = width_ft * FT
        m.segments = seg
        m.limit_method = limit
        m.harden_normals = harden
        return m

    def boolean_cut(self, ob, cutter):
        m = ob.modifiers.new('cut', 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.solver = 'EXACT'
        m.object = cutter
        bpy.context.view_layer.objects.active = ob
        with bpy.context.temp_override(object=ob, active_object=ob):
            bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
        self.n_objects -= 1
        return ob

    # ------------------------------------------------------------------ lights
    def area_light(self, name, x, y, z, size_x, size_z, watts, kelvin=3000, coll=None, facing='down', spread_deg=None):
        """Rectangular area light at SCENE point, sizes in feet along x / z, facing down
        (or 'up', '+x', '-x', '+z', '-z'). Invisible to camera and glossy rays."""
        from ..lighting import kelvin_rgb
        ld = bpy.data.lights.new(name, 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size = max(size_x, 0.01) * FT
        ld.size_y = max(size_z, 0.01) * FT
        ld.energy = watts
        ld.color = kelvin_rgb(kelvin)
        if spread_deg is not None:
            try:
                ld.spread = math.radians(spread_deg)
            except AttributeError:
                pass
        lo = bpy.data.objects.new(name, ld)
        lo.location = ft2bl(x, y, z)
        # Area lights emit along local -Z.
        rot = {'down': (0, 0, 0), 'up': (math.pi, 0, 0),
               '+x': (0, -math.pi / 2, 0), '-x': (0, math.pi / 2, 0),
               '+z': (-math.pi / 2, 0, 0), '-z': (math.pi / 2, 0, 0)}[facing]
        lo.rotation_euler = rot
        try:
            lo.visible_camera = False
            lo.visible_glossy = False
        except AttributeError:
            pass
        return self._link(lo, coll)

    def point_light(self, name, x, y, z, watts, kelvin=2700, radius_ft=0.15, coll=None):
        from ..lighting import kelvin_rgb
        ld = bpy.data.lights.new(name, 'POINT')
        ld.energy = watts
        ld.color = kelvin_rgb(kelvin)
        ld.shadow_soft_size = radius_ft * FT
        lo = bpy.data.objects.new(name, ld)
        lo.location = ft2bl(x, y, z)
        try:
            lo.visible_camera = False
        except AttributeError:
            pass
        return self._link(lo, coll)


# ---------------------------------------------------------------- zone materials
def principled(name, color, rough, metal=0.0, coat=0.0, sss=0.0, transl=None, emission=None, strength=0.0):
    """Zone-specific material Z_kitchen_dining_<name> (created once)."""
    full = 'Z_kitchen_dining_' + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = color + (1,) if len(color) == 3 else color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if coat:
        try:
            b.inputs['Coat Weight'].default_value = coat
            b.inputs['Coat Roughness'].default_value = 0.03
        except KeyError:
            pass
    if sss:
        try:
            b.inputs['Subsurface Weight'].default_value = sss
            b.inputs['Subsurface Radius'].default_value = (0.4, 0.3, 0.15)
            b.inputs['Subsurface Scale'].default_value = 0.004
        except KeyError:
            pass
    if emission is not None:
        b.inputs['Emission Color'].default_value = emission + (1,)
        b.inputs['Emission Strength'].default_value = strength
    if transl is not None:
        # leaf: mix principled with translucent for back-lit glow
        out = nt.nodes.get('Material Output')
        tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
        tl.inputs['Color'].default_value = transl + (1,)
        mix = nt.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = 0.22
        nt.links.new(b.outputs[0], mix.inputs[1])
        nt.links.new(tl.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (color[0], color[1], color[2], 1)
    return m


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)
