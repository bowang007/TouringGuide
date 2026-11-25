"""Shared helpers for the exterior zone (runs inside Blender).

All coordinates are SCENE feet (x east, y up, z south/street) unless a name says otherwise.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from ..common import FT, ft2bl

ROOT = 'zone_exterior'
GRADE = -0.60          # soil level of the LEVEL SITE the fences, the planting, the street and the neighbourhood are
#                        modelled on (ft; floors are at y=0). v7 site: the real ground is exterior_layout.grade(z)
#                        (sheet A1.3: -0.917 in front of the house, -1.167 behind it); exterior_site.settle() sets
#                        everything built with GRADE down on it.


def coll(ctx, sub=None):
    """zone_exterior or one of its children (ext_<sub>)."""
    if sub is None:
        return ctx.coll(ROOT)
    return ctx.coll(f'ext_{sub}', ROOT)


def coll_name(ctx, sub):
    return coll(ctx, sub).name


# --------------------------------------------------------------------------- mesh building
class MB:
    """Accumulates geometry in SCENE feet and emits one Blender object (meters, world space)."""

    def __init__(self):
        self.v = []
        self.f = []
        self.mi = []

    def _p(self, x, y, z):
        return (x * FT, -z * FT, y * FT)

    def vert(self, x, y, z):
        self.v.append(self._p(x, y, z))
        return len(self.v) - 1

    def face(self, idx, mi=0):
        self.f.append(tuple(idx))
        self.mi.append(mi)

    def box(self, x0, x1, y0, y1, z0, z1, mi=0):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        return self.box_pts([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, mi)

    def box_c(self, cx, cy, cz, sx, sy, sz, rot=0.0, mi=0):
        """Box by SCENE center/size, rot radians about +Y (same sense as SCENE `rot`)."""
        c, s = math.cos(rot), math.sin(rot)
        pts = []
        for dx, dz in ((-sx / 2, -sz / 2), (sx / 2, -sz / 2), (sx / 2, sz / 2), (-sx / 2, sz / 2)):
            pts.append((cx + dx * c + dz * s, cz - dx * s + dz * c))
        return self.box_pts(pts, cy - sy / 2, cy + sy / 2, mi)

    def box_pts(self, pts, y0, y1, mi=0, ytop=None):
        """Prism from a plan polygon (x, z) list (any winding), y0..y1. ytop: optional per-point top y."""
        n = len(pts)
        # make winding counter-clockwise seen from above in Blender (x, -z) space
        area = 0.0
        for i in range(n):
            x0, z0 = pts[i]
            x1, z1 = pts[(i + 1) % n]
            area += x0 * (-z1) - x1 * (-z0)
        if area < 0:
            pts = pts[::-1]
            if ytop is not None:
                ytop = ytop[::-1]
        b = len(self.v)
        for (x, z) in pts:
            self.vert(x, y0, z)
        for i, (x, z) in enumerate(pts):
            self.vert(x, ytop[i] if ytop is not None else y1, z)
        self.face([b + i for i in range(n)][::-1], mi)            # bottom
        self.face([b + n + i for i in range(n)], mi)               # top
        for i in range(n):
            j = (i + 1) % n
            self.face([b + i, b + j, b + n + j, b + n + i], mi)
        return b

    def quad(self, p0, p1, p2, p3, mi=0):
        b = len(self.v)
        for p in (p0, p1, p2, p3):
            self.vert(*p)
        self.face([b, b + 1, b + 2, b + 3], mi)

    def grid(self, x0, x1, z0, z1, hfn, step=1.0, mi=0):
        """Height-field quad grid over a rectangle, y = hfn(x, z)."""
        nx = max(1, int(math.ceil((x1 - x0) / step)))
        nz = max(1, int(math.ceil((z1 - z0) / step)))
        b = len(self.v)
        for j in range(nz + 1):
            z = z0 + (z1 - z0) * j / nz
            for i in range(nx + 1):
                x = x0 + (x1 - x0) * i / nx
                self.vert(x, hfn(x, z), z)
        for j in range(nz):
            for i in range(nx):
                a = b + j * (nx + 1) + i
                # CCW seen from above in Blender (z grows -> Blender y shrinks): normal +Z
                self.face([a, a + nx + 1, a + nx + 2, a + 1], mi)

    def obj(self, ctx, name, mats, sub, bevel=0.0, segments=2, smooth=False):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        if not isinstance(mats, (list, tuple)):
            mats = [mats]
        for m in mats:
            me.materials.append(ctx.mat(m) if isinstance(m, str) else m)
        if len(mats) > 1:
            for p, mi in zip(me.polygons, self.mi):
                p.material_index = mi
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(name, me)
        coll(ctx, sub).objects.link(ob)
        if bevel > 0:
            ctx.add_bevel(ob, bevel, segments)
        return ob


# --------------------------------------------------------------------------- materials
def _srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def flat_mat(name, color, rough=0.8, metal=0.0, spec=0.5):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = _srgb(color) if isinstance(color, str) else tuple(color) + (1,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    try:
        b.inputs['Specular IOR Level'].default_value = spec
    except KeyError:
        pass
    m.diffuse_color = b.inputs['Base Color'].default_value
    return m


def _world_mapping(nt, scale_m, rot_z=0.0):
    """Geometry.Position (meters) -> Mapping scaled so 1 texture tile = scale_m meters."""
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / scale_m, 1 / scale_m, 1 / scale_m)
    mp.inputs['Rotation'].default_value = (0, 0, rot_z)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    return mp


def tex_mat(name, tex_id, scale_m, res='2k', tint=None, rough_mul=1.0, bump=0.3, value=1.0, rot_z=0.0,
            random_hue=0.0):
    """World-space box-mapped Poly Haven PBR material (zone-specific). Falls back to flat grey."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    from .. import assets
    try:
        maps = assets.texture(tex_id, res=res)
    except Exception as e:  # offline: plain material
        print('[exterior] texture fetch failed', tex_id, e)
        return flat_mat(name, tint or '#888888', 0.8)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    mp = _world_mapping(nt, scale_m, rot_z)

    def img(key, non_color):
        p = maps.get(key)
        if not p:
            return None
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(p, check_existing=True)
        if non_color:
            t.image.colorspace_settings.name = 'Non-Color'
        t.projection = 'BOX'
        t.projection_blend = 0.2
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
        return t

    d = img('diffuse', False)
    col_out = d.outputs['Color'] if d else None
    if col_out is not None and (tint is not None or value != 1.0):
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(col_out, mix.inputs['A'])
        tc = _srgb(tint) if tint else (1, 1, 1, 1)
        mix.inputs['B'].default_value = tuple(c * value for c in tc[:3]) + (1,)
        col_out = mix.outputs['Result']
    if col_out is not None and random_hue > 0:
        oi = nt.nodes.new('ShaderNodeObjectInfo')
        hsv = nt.nodes.new('ShaderNodeHueSaturation')
        rm = nt.nodes.new('ShaderNodeMapRange')
        rm.inputs['To Min'].default_value = 1 - random_hue
        rm.inputs['To Max'].default_value = 1 + random_hue
        nt.links.new(oi.outputs['Random'], rm.inputs['Value'])
        nt.links.new(rm.outputs['Result'], hsv.inputs['Value'])
        nt.links.new(col_out, hsv.inputs['Color'])
        col_out = hsv.outputs['Color']
    if col_out is not None:
        nt.links.new(col_out, bsdf.inputs['Base Color'])
    r = img('rough', True)
    if r:
        if rough_mul != 1.0:
            mm = nt.nodes.new('ShaderNodeMath')
            mm.operation = 'MULTIPLY'
            mm.inputs[1].default_value = rough_mul
            nt.links.new(r.outputs['Color'], mm.inputs[0])
            nt.links.new(mm.outputs[0], bsdf.inputs['Roughness'])
        else:
            nt.links.new(r.outputs['Color'], bsdf.inputs['Roughness'])
    n = img('nor_gl', True)
    if n:
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = 1.0
        nt.links.new(n.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.4
    except KeyError:
        pass
    m.diffuse_color = _srgb(tint) if tint else (0.4, 0.4, 0.4, 1)
    return m


def varied(ctx, key, amount=0.12, name=None):
    """Copy of a library material whose base colour value varies per object (Object Info Random).
    Used for deck boards, pavers etc. so repeated pieces don't look cloned."""
    name = name or f'Z_exterior_{key}_var'
    m = bpy.data.materials.get(name)
    if m:
        return m
    src = ctx.mat(key)
    m = src.copy()
    m.name = name
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return m
    sock = bsdf.inputs['Base Color']
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    rm = nt.nodes.new('ShaderNodeMapRange')
    rm.inputs['To Min'].default_value = 1 - amount
    rm.inputs['To Max'].default_value = 1 + amount
    nt.links.new(oi.outputs['Random'], rm.inputs['Value'])
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    nt.links.new(rm.outputs['Result'], hsv.inputs['Value'])
    if sock.is_linked:
        nt.links.new(sock.links[0].from_socket, hsv.inputs['Color'])
    else:
        hsv.inputs['Color'].default_value = sock.default_value
    nt.links.new(hsv.outputs['Color'], sock)
    return m


def mul_copy(ctx, key, mul, name, rough=None):
    """Copy of a library material with its base colour multiplied by `mul` (linear RGB factors); keeps the
    library's texture detail. Optional roughness override."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = ctx.mat(key).copy()
    m.name = name
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bsdf is None:
        return m
    s = bsdf.inputs['Base Color']
    if s.is_linked:
        vm = nt.nodes.new('ShaderNodeVectorMath')
        vm.operation = 'MULTIPLY'
        vm.inputs[1].default_value = tuple(mul)
        nt.links.new(s.links[0].from_socket, vm.inputs[0])
        nt.links.new(vm.outputs['Vector'], s)
    else:
        c = s.default_value
        s.default_value = (c[0] * mul[0], c[1] * mul[1], c[2] * mul[2], 1.0)
    if rough is not None and not bsdf.inputs['Roughness'].is_linked:
        bsdf.inputs['Roughness'].default_value = rough
    d = m.diffuse_color
    m.diffuse_color = (d[0] * mul[0], d[1] * mul[1], d[2] * mul[2], d[3])
    return m


def emit_mat(name, rgb, strength):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple(rgb) + (1,)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


# --------------------------------------------------------------------------- instancing
def instance(ctx, src_coll, x, y, z, rot=0.0, scale=1.0, sub='plants', name=None, tilt=(0.0, 0.0)):
    """Collection instance (empty) at SCENE feet; rot radians about +Y; scale uniform or (sx,sy,sz)."""
    e = bpy.data.objects.new(name or f'{src_coll.name} inst', None)
    e.instance_type = 'COLLECTION'
    e.instance_collection = src_coll
    e.location = ft2bl(x, y, z)
    e.rotation_euler = (tilt[0], tilt[1], rot)
    e.scale = (scale, scale, scale) if not isinstance(scale, (tuple, list)) else scale
    e.empty_display_size = 0.3
    coll(ctx, sub).objects.link(e)
    return e


def linked_copy(ctx, src_ob, x, y, z, rot=0.0, scale=1.0, sub='plants', name=None):
    ob = bpy.data.objects.new(name or src_ob.name + ' inst', src_ob.data)
    ob.location = ft2bl(x, y, z)
    ob.rotation_euler = (0, 0, rot)
    ob.scale = (scale, scale, scale) if not isinstance(scale, (tuple, list)) else scale
    coll(ctx, sub).objects.link(ob)
    return ob


def exclude_collection(c):
    """Exclude a (source/library) collection from every view layer so only its instances render."""
    def walk(lc):
        if lc.collection == c:
            lc.exclude = True
            return True
        return any(walk(ch) for ch in lc.children)
    for vl in bpy.context.scene.view_layers:
        walk(vl.layer_collection)


def mesh_tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def rng(seed):
    return random.Random(seed)
