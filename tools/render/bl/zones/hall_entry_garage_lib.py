"""Geometry + material helpers for the hall_entry_garage zone (runs inside Blender).

All coordinates are SCENE feet (x east, y up, z south). `Frame` describes a wall face: an
origin on the face, U = unit vector along the wall (to the right when facing the wall from the
room), N = unit normal pointing into the room. Local (u, v, n) = (along, up, out-of-wall).
"""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

from ..common import FT, ft2bl

ZONE = 'zone_hall_entry_garage'
PFX = 'Z_hall_entry_garage_'


# ----------------------------------------------------------------------------- materials
def _srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def principled(name, color, rough=0.5, metal=0.0, coat=0.0, sss=0.0, spec=0.5, sheen=0.0):
    """Zone-local Principled material (cached by name)."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = _srgb(color) if isinstance(color, str) else color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Specular IOR Level'].default_value = spec
    if sss:
        b.inputs['Subsurface Weight'].default_value = sss
        b.inputs['Subsurface Radius'].default_value = (0.4, 0.3, 0.25)
        b.inputs['Subsurface Scale'].default_value = 0.004
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
    m.diffuse_color = _srgb(color) if isinstance(color, str) else color
    return m


def image_from_array(name, arr):
    """(H, W, 3|4) float array in sRGB-ish display values 0..1 (row 0 = TOP) -> packed bpy image."""
    full = PFX + name
    img = bpy.data.images.get(full)
    if img:
        return img
    h, w = arr.shape[:2]
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones((h, w, 1), arr.dtype)], 2)
    img = bpy.data.images.new(full, w, h, alpha=False)
    img.pixels.foreach_set(np.ascontiguousarray(arr[::-1]).astype(np.float32).ravel())
    img.pack()
    return img


def image_material(name, img, rough=0.75, bump_img=None, bump_strength=0.15, coat=0.0, non_color=False,
                   mapping='UV', scale=(1, 1, 1), extra_color=None):
    """Material sampling `img` with UV (or object-xz) coordinates."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    if mapping == 'UV':
        tc = nt.nodes.new('ShaderNodeTexCoord')
        vec = tc.outputs['UV']
    else:                                  # object coords, face lies in local XZ (u, v)
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs[0])
        com = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(sep.outputs['X'], com.inputs['X'])
        nt.links.new(sep.outputs['Z'], com.inputs['Y'])
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale
        nt.links.new(com.outputs[0], mp.inputs['Vector'])
        vec = mp.outputs['Vector']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Cubic' if mapping == 'UV' else 'Linear'
    nt.links.new(vec, tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Coat Weight'].default_value = coat
    if bump_img is not None:
        bt = nt.nodes.new('ShaderNodeTexImage')
        bt.image = bump_img
        bump_img.colorspace_settings.name = 'Non-Color'
        nt.links.new(vec, bt.inputs['Vector'])
        bn = nt.nodes.new('ShaderNodeBump')
        bn.inputs['Strength'].default_value = bump_strength
        bn.inputs['Distance'].default_value = 0.002
        nt.links.new(bt.outputs['Color'], bn.inputs['Height'])
        nt.links.new(bn.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = (0.8, 0.78, 0.74, 1)
    return m


def emit_mat(name, color=(1.0, 0.78, 0.55), strength=8.0):
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = tuple(color) + (1,)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs[0], out.inputs['Surface'])
    return m


def diffuser_mat(name, strength=6.0, color=(1.0, 0.8, 0.6)):
    """Frosted LED diffuser: lit white plastic that glows (emission + diffuse white)."""
    full = PFX + name
    m = bpy.data.materials.get(full)
    if m:
        return m
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (0.9, 0.9, 0.88, 1)
    b.inputs['Roughness'].default_value = 0.4
    b.inputs['Emission Color'].default_value = tuple(color) + (1,)
    b.inputs['Emission Strength'].default_value = strength
    return m


# ----------------------------------------------------------------------------- frames
class Frame:
    def __init__(self, x, z, U, N):
        self.o = (x, z)
        self.U = U
        self.N = N
        self.rot = math.atan2(-U[1], U[0])

    def xz(self, u, n):
        return (self.o[0] + u * self.U[0] + n * self.N[0], self.o[1] + u * self.U[1] + n * self.N[1])

    def pt(self, u, v, n):
        x, z = self.xz(u, n)
        return (x, v, z)

    def box(self, ctx, name, u0, u1, v0, v1, n0, n1, mat, coll, bevel=0.0, segments=3):
        uc, vc, nc = (u0 + u1) / 2, (v0 + v1) / 2, (n0 + n1) / 2
        return ctx.box_c(name, self.pt(uc, vc, nc), (abs(u1 - u0), abs(v1 - v0), abs(n1 - n0)), self.rot,
                         mat, coll, bevel, segments)

    def place(self, ob, u, v, n, extra_rot=0.0):
        ob.location = ft2bl(*self.pt(u, v, n))
        ob.rotation_euler = (ob.rotation_euler.x, ob.rotation_euler.y, self.rot + extra_rot)
        return ob


WEST_FACING_EAST = lambda x: Frame(x, 0.0, (0, -1), (1, 0))     # wall at x, room to the east
EAST_FACING_WEST = lambda x: Frame(x, 0.0, (0, 1), (-1, 0))     # wall at x, room to the west
NORTH_FACING_SOUTH = lambda z: Frame(0.0, z, (1, 0), (0, 1))    # wall at z, room to the south
SOUTH_FACING_NORTH = lambda z: Frame(0.0, z, (-1, 0), (0, -1))  # wall at z, room to the north


# ----------------------------------------------------------------------------- meshes
def to_bl_local(p):
    """SCENE-feet local (x, y, z) -> Blender local meters."""
    return (p[0] * FT, -p[2] * FT, p[1] * FT)


def mesh_from(ctx, name, verts_ft, faces, coll, mats=(), mat_idx=None, uvs=None, smooth=False,
              sharp_deg=None):
    """verts in SCENE-feet LOCAL coords (x along U, y up, z along N). mats: list of materials/keys."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([to_bl_local(v) for v in verts_ft], [], faces)
    if uvs is not None:
        uvl = me.uv_layers.new(name='UVMap')
        k = 0
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = uvs[k]
                k += 1
    for m in mats:
        me.materials.append(ctx.mat(m) if isinstance(m, str) else m)
    if mat_idx is not None:
        for poly, mi in zip(me.polygons, mat_idx):
            poly.material_index = mi
    me.validate()
    if smooth:
        me.shade_smooth()
        if sharp_deg:
            try:
                me.set_sharp_from_angle(angle=math.radians(sharp_deg))
            except Exception:
                pass
    ob = bpy.data.objects.new(name, me)
    ctx.coll(coll).objects.link(ob)
    return ob


def ring_mesh(ctx, name, radius, width, height, coll, mats, seg=96, inner_mat=1, bottom_mat=1, outer_mat=0,
              top_mat=0):
    """Horizontal ring (rectangular section) centred at local origin, axis = +Y (up).
    radius = centreline radius, width = radial thickness, height = vertical thickness (ft)."""
    r0, r1 = radius - width / 2, radius + width / 2
    h0, h1 = -height / 2, height / 2
    verts, faces, mi = [], [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        for r, h in ((r0, h0), (r1, h0), (r1, h1), (r0, h1)):
            verts.append((r * c, h, r * s))
    for i in range(seg):
        j = (i + 1) % seg
        a, b = 4 * i, 4 * j
        faces += [(a + 0, a + 1, b + 1, b + 0),   # bottom
                  (a + 1, a + 2, b + 2, b + 1),   # outer
                  (a + 2, a + 3, b + 3, b + 2),   # top
                  (a + 3, a + 0, b + 0, b + 3)]   # inner
        mi += [bottom_mat, outer_mat, top_mat, inner_mat]
    ob = mesh_from(ctx, name, verts, faces, coll, mats, mi, smooth=True, sharp_deg=50)
    return ob


def catmull(pts, sub=6):
    """Catmull-Rom densify a polyline of tuples (keeps the end points)."""
    P = [Vector(p) for p in pts]
    if len(P) < 3:
        return [tuple(p) for p in P]
    P = [P[0] + (P[0] - P[1])] + P + [P[-1] + (P[-1] - P[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                                    (-p0 + 3 * p1 - 3 * p2 + p3) * t3)))
    out.append(tuple(P[-2]))
    return out


def lathe(ctx, name, profile, coll, mats, seg=64, cap_bottom=True, smooth_profile=True):
    """Solid of revolution about local +Y. profile: [(r, y), ...] bottom -> top (feet)."""
    if smooth_profile:
        profile = [(max(r, 0.0), y) for r, y in catmull(profile, 5)]
    verts, faces = [], []
    n = len(profile)
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        for r, y in profile:
            verts.append((r * c, y, r * s))
    for i in range(seg):
        j = (i + 1) % seg
        for k in range(n - 1):
            faces.append((i * n + k, i * n + k + 1, j * n + k + 1, j * n + k))
    if cap_bottom and profile[0][0] > 1e-4:
        verts.append((0, profile[0][1], 0))
        cidx = len(verts) - 1
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((i * n, j * n, cidx))
    return mesh_from(ctx, name, verts, faces, coll, mats, smooth=True, sharp_deg=60)


def tube(ctx, name, pts_ft, radii_ft, coll, mat, bevel_res=3, world=True):
    """Poly-curve tube through SCENE-feet world points with per-point radius (feet)."""
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 1.0 * FT
    cu.bevel_resolution = bevel_res
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts_ft) - 1)
    for p, (pt, r) in enumerate(zip(pts_ft, radii_ft)):
        v = ft2bl(*pt)
        sp.points[p].co = (v.x, v.y, v.z, 1.0)
        sp.points[p].radius = r
    m = ctx.mat(mat) if isinstance(mat, str) else mat
    cu.materials.append(m)
    ob = bpy.data.objects.new(name, cu)
    ctx.coll(coll).objects.link(ob)
    return ob


def cyl_between(ctx, name, p0, p1, radius, coll, mat, verts=16):
    """Cylinder between two SCENE-feet points."""
    a, b = ft2bl(*p0), ft2bl(*p1)
    d = b - a
    L = d.length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius * FT, radius2=radius * FT, depth=L)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    ob = bpy.data.objects.new(name, me)
    ob.location = (a + b) / 2
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    me.materials.append(ctx.mat(mat) if isinstance(mat, str) else mat)
    ctx.coll(coll).objects.link(ob)
    return ob


def ceiling_y(x, z, y0=6.0, default=8.0):
    """Height (ft) of the first surface above SCENE (x, y0, z)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    hit, loc, nor, idx, ob, mw = bpy.context.scene.ray_cast(dg, ft2bl(x, y0, z), Vector((0, 0, 1)))
    if not hit:
        return default, Vector((0, 0, -1))
    return loc.z / FT, nor
