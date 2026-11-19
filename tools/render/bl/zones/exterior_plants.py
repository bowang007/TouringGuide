"""Planting for the exterior zone (runs inside Blender).

* Lawns: geometry-nodes instanced blade clumps (procedural, ~1300 blades / sq ft) on the lawn surfaces.
* River-pebble borders: geometry-nodes instanced pebbles on the pebble surfaces.
* Ornamental grasses / phormium: procedural clump meshes (shared mesh data = instanced).
* Trees and shrubs: Poly Haven CC0 models (island_tree_01 as olive, island_tree_02 multi-stem,
  tree_small_02 shade/street tree, searsia_lucida + shrub_02 Mediterranean shrubs), imported once
  into an excluded library collection and placed as collection instances.
"""
import math
import zlib

import bmesh
import bpy
from mathutils import Vector

from ..common import FT, ft2bl
from .. import assets
from . import exterior_layout as L
from .exterior_util import GRADE, coll, exclude_collection, flat_mat, instance, mesh_tris, rng

SUB = 'plants'
_LIB = {}


# =============================================================================== library
def _lib_root(ctx):
    return coll(ctx, 'library')


def _bbox_local(me):
    import numpy as np
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    return co.min(0), co.max(0)


def _leafify(mat, amount=0.32, hue=0.5, sat=1.0, val=1.0):
    """Add back-light translucency to an alpha-cut leaf material (keeps the cut-out)."""
    if mat is None or not mat.use_nodes or mat.get('tg_leafified'):
        return
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if bsdf is None or out is None:
        return
    a_in = bsdf.inputs['Alpha']
    c_in = bsdf.inputs['Base Color']
    col_src = c_in.links[0].from_socket if c_in.is_linked else None
    if col_src is not None and (hue != 0.5 or sat != 1.0 or val != 1.0):
        hs = nt.nodes.new('ShaderNodeHueSaturation')
        hs.inputs['Hue'].default_value = hue
        hs.inputs['Saturation'].default_value = sat
        hs.inputs['Value'].default_value = val
        nt.links.new(col_src, hs.inputs['Color'])
        nt.links.new(hs.outputs['Color'], c_in)
        col_src = hs.outputs['Color']
    if not a_in.is_linked:
        mat['tg_leafified'] = 1
        return
    a_src = a_in.links[0].from_socket
    nt.links.remove(a_in.links[0])
    a_in.default_value = 1.0
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    if col_src is not None:
        nt.links.new(col_src, tl.inputs['Color'])
    m1 = nt.nodes.new('ShaderNodeMixShader')
    m1.inputs['Fac'].default_value = amount
    nt.links.new(bsdf.outputs[0], m1.inputs[1])
    nt.links.new(tl.outputs[0], m1.inputs[2])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    m2 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(a_src, m2.inputs['Fac'])
    nt.links.new(tr.outputs[0], m2.inputs[1])
    nt.links.new(m1.outputs[0], m2.inputs[2])
    nt.links.new(m2.outputs[0], out.inputs['Surface'])
    mat['tg_leafified'] = 1


def load(ctx, asset_id, res='1k', leaf=None):
    """Import a Poly Haven model once; returns {variant_suffix: collection}. Each variant collection
    has its instance offset at the plant's base centre so instances stand on their placement point."""
    if asset_id in _LIB:
        return _LIB[asset_id]
    path = assets.model(asset_id, res=res)
    roots = ctx.link_asset(path)
    lib = _lib_root(ctx)
    out = {}
    stack = list(roots)
    obs = []
    while stack:
        o = stack.pop()
        obs.append(o)
        stack.extend(o.children)
    for ob in obs:
        if ob.type != 'MESH':
            continue
        ob.parent = None
        ob.location = (0, 0, 0)
        ob.rotation_euler = (0, 0, 0)
        ob.scale = (1, 1, 1)
        suffix = ob.name.replace(asset_id, '').replace('_LOD0', '').strip('_') or 'main'
        c = bpy.data.collections.new(f'lib {asset_id} {suffix}')
        lib.children.link(c)
        for uc in list(ob.users_collection):
            uc.objects.unlink(ob)
        c.objects.link(ob)
        lo, hi = _bbox_local(ob.data)
        c.instance_offset = (float(lo[0] + hi[0]) / 2, float(lo[1] + hi[1]) / 2, float(lo[2]))
        c['height_m'] = float(hi[2] - lo[2])
        c['width_m'] = float(max(hi[0] - lo[0], hi[1] - lo[1]))
        out[suffix] = c
        for m in ob.data.materials:
            if m and leaf is not None and ('leaf' in m.name.lower() or 'leaves' in m.name.lower() or
                                           'twig' in m.name.lower() or asset_id.startswith('shrub')):
                _leafify(m, **leaf)
    for o in obs:
        if o.type != 'MESH' and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)
    exclude_collection(lib)
    _LIB[asset_id] = out
    ctx.stats.setdefault('exterior_assets', []).append(asset_id)
    return out


def plant(ctx, asset_id, variant, x, z, height_ft=None, scale=None, rot=None, y=None, seed=0, res='1k', leaf=None,
          sub=SUB):
    lib = load(ctx, asset_id, res, leaf)
    c = lib.get(variant) or next(iter(lib.values()))
    r = rng(zlib.crc32(f'{asset_id}{variant}{x:.2f}{z:.2f}{seed}'.encode()))
    if scale is None:
        scale = (height_ft * FT) / max(c['height_m'], 1e-3) if height_ft else 1.0
    if rot is None:
        rot = r.uniform(0, 2 * math.pi)
    return instance(ctx, c, x, GRADE if y is None else y, z, rot, scale, sub=sub, name=f'ext {asset_id} {variant}')


# ====================================================================== procedural plants
def _blade(bm, uv, base, az, length, width, lean, bend, segs, twist=0.0, droop=0.0, u=0.5, taper=1.0):
    """One curved strap blade. base (x,y,z) meters; az heading; lean/bend radians."""
    d = Vector((math.cos(az), math.sin(az), 0.0))
    side = Vector((-math.sin(az + twist), math.cos(az + twist), 0.0))
    pts = [Vector(base)]
    p = Vector(base)
    ds = length / segs
    for k in range(segs):
        th = lean + bend * ((k + 0.5) / segs) ** 1.3 + droop * ((k + 0.5) / segs) ** 3
        p = p + (d * math.sin(th) + Vector((0, 0, 1)) * math.cos(th)) * ds
        pts.append(p.copy())
    verts = []
    for k, q in enumerate(pts[:-1]):
        t = k / segs
        w = width * (1 - t ** (1.6 * taper)) * (0.6 + 0.4 * min(1.0, t * 4 + 0.4))
        verts.append((bm.verts.new(q - side * w / 2), bm.verts.new(q + side * w / 2), t))
    tip = bm.verts.new(pts[-1])
    for k in range(len(verts) - 1):
        a0, a1, t0 = verts[k]
        b0, b1, t1 = verts[k + 1]
        f = bm.faces.new((a0, a1, b1, b0))
        for loop, vv in zip(f.loops, (t0, t0, t1, t1)):
            loop[uv].uv = (u, vv)
    a0, a1, t0 = verts[-1]
    f = bm.faces.new((a0, a1, tip))
    for loop, vv in zip(f.loops, (t0, t0, 1.0)):
        loop[uv].uv = (u, vv)


def clump_mesh(name, seed, n, len_rng, width, radius, lean_rng, bend_rng, segs=4, droop=0.0, spread='disc', taper=1.0):
    me = bpy.data.meshes.get(name)
    if me:
        return me
    r = rng(seed)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    for i in range(n):
        a = r.uniform(0, 2 * math.pi)
        rr = radius * math.sqrt(r.random())
        base = (rr * math.cos(a), rr * math.sin(a), 0.0)
        az = a + r.gauss(0, 0.5) if spread == 'disc' else r.uniform(0, 2 * math.pi)
        lean = r.uniform(*lean_rng) * (0.4 + 0.6 * rr / max(radius, 1e-6) if spread == 'disc' else 1.0)
        _blade(bm, uv, base, az, r.uniform(*len_rng), width * r.uniform(0.75, 1.2), lean, r.uniform(*bend_rng),
               segs, twist=r.gauss(0, 0.35), droop=droop * r.uniform(0.5, 1.3), u=r.random(), taper=taper)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def blade_mat(name, base_hex, tip_hex, dark=0.45, vary=0.18, trans=0.28, rough=0.5):
    """Grass / leaf blade material: base->tip gradient (UV v), per-blade + per-instance variation,
    translucency for back-light."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    from .exterior_util import _srgb
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    uvn = nt.nodes.new('ShaderNodeUVMap')
    uvn.uv_map = 'UVMap'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uvn.outputs['UV'], sep.inputs['Vector'])
    grad = nt.nodes.new('ShaderNodeMix')
    grad.data_type = 'RGBA'
    grad.inputs['A'].default_value = _srgb(base_hex)
    grad.inputs['B'].default_value = _srgb(tip_hex)
    pw = nt.nodes.new('ShaderNodeMath')
    pw.operation = 'POWER'
    pw.inputs[1].default_value = 0.8
    nt.links.new(sep.outputs['Y'], pw.inputs[0])
    nt.links.new(pw.outputs[0], grad.inputs['Factor'])
    # darken toward the base (self-shadowing of a dense sward)
    ao = nt.nodes.new('ShaderNodeMapRange')
    ao.inputs['To Min'].default_value = dark
    ao.inputs['To Max'].default_value = 1.0
    ao.inputs['From Max'].default_value = 0.6
    nt.links.new(sep.outputs['Y'], ao.inputs['Value'])
    # per-blade (UV u) and per-instance random variation
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'ADD'
    nt.links.new(sep.outputs['X'], add.inputs[0])
    nt.links.new(oi.outputs['Random'], add.inputs[1])
    fr = nt.nodes.new('ShaderNodeMath')
    fr.operation = 'FRACT'
    nt.links.new(add.outputs[0], fr.inputs[0])
    vr = nt.nodes.new('ShaderNodeMapRange')
    vr.inputs['To Min'].default_value = 1 - vary
    vr.inputs['To Max'].default_value = 1 + vary
    nt.links.new(fr.outputs[0], vr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(ao.outputs['Result'], mul.inputs[0])
    nt.links.new(vr.outputs['Result'], mul.inputs[1])
    hsv = nt.nodes.new('ShaderNodeHueSaturation')
    nt.links.new(grad.outputs['Result'], hsv.inputs['Color'])
    nt.links.new(mul.outputs[0], hsv.inputs['Value'])
    hue = nt.nodes.new('ShaderNodeMapRange')
    hue.inputs['To Min'].default_value = 0.5 - vary * 0.12
    hue.inputs['To Max'].default_value = 0.5 + vary * 0.12
    nt.links.new(fr.outputs[0], hue.inputs['Value'])
    nt.links.new(hue.outputs['Result'], hsv.inputs['Hue'])
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = rough
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.35
    except KeyError:
        pass
    nt.links.new(hsv.outputs['Color'], bsdf.inputs['Base Color'])
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    nt.links.new(hsv.outputs['Color'], tl.inputs['Color'])
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = trans
    nt.links.new(bsdf.outputs[0], mix.inputs[1])
    nt.links.new(tl.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.diffuse_color = _srgb(base_hex)
    return m


def proc_plant(ctx, kind):
    """Shared-mesh source object for a procedural plant kind (kept in the excluded library)."""
    key = f'ext src {kind}'
    ob = bpy.data.objects.get(key)
    if ob:
        return ob
    M = 1.0                       # meters
    if kind == 'lawn':
        me = clump_mesh('ext lawn clump', 7, 22, (0.055, 0.095), 0.0042, 0.03, (0.05, 0.45), (0.1, 0.5), segs=3)
        mat = blade_mat('Z_exterior_lawn_blade', '#3d5a1c', '#7d9a3a', dark=0.35, vary=0.22, trans=0.3, rough=0.42)
    elif kind == 'lomandra':
        me = clump_mesh('ext lomandra', 11, 150, (0.45, 0.8), 0.008, 0.07, (0.05, 0.7), (0.4, 1.3), segs=6, droop=0.6)
        mat = blade_mat('Z_exterior_lomandra', '#2f4419', '#6f8a3c', dark=0.4, vary=0.15, trans=0.3, rough=0.45)
    elif kind == 'fescue':
        me = clump_mesh('ext blue fescue', 13, 230, (0.18, 0.3), 0.0028, 0.05, (0.0, 1.2), (0.1, 0.6), segs=4,
                        spread='disc')
        mat = blade_mat('Z_exterior_fescue', '#4c6066', '#9fb2b0', dark=0.5, vary=0.1, trans=0.25, rough=0.5)
    elif kind == 'feather':
        me = clump_mesh('ext feather grass', 17, 320, (0.4, 0.62), 0.0016, 0.06, (0.05, 0.5), (0.5, 1.4), segs=6,
                        droop=0.8)
        mat = blade_mat('Z_exterior_feather', '#6d7a45', '#d2c690', dark=0.5, vary=0.12, trans=0.35, rough=0.55)
    elif kind == 'phormium':
        me = clump_mesh('ext phormium', 19, 22, (0.7, 1.15), 0.045, 0.06, (0.05, 0.45), (0.05, 0.5), segs=6,
                        droop=0.3, taper=0.6)
        mat = blade_mat('Z_exterior_phormium', '#3a1e1c', '#7a4636', dark=0.55, vary=0.12, trans=0.18, rough=0.38)
    else:
        raise KeyError(kind)
    me.materials.clear()
    me.materials.append(mat)
    ob = bpy.data.objects.new(key, me)
    src = coll(ctx, 'library_proc')
    src.objects.link(ob)
    exclude_collection(src)
    return ob


def place_proc(ctx, kind, x, z, scale=1.0, rot=None, y=None, seed=0):
    src = proc_plant(ctx, kind)
    r = rng(zlib.crc32(f'{kind}{x:.2f}{z:.2f}{seed}'.encode()))
    ob = bpy.data.objects.new(f'ext {kind}', src.data)
    ob.location = ft2bl(x, GRADE + 0.03 if y is None else y, z)
    ob.rotation_euler = (r.gauss(0, 0.04), r.gauss(0, 0.04), r.uniform(0, 2 * math.pi) if rot is None else rot)
    s = scale * r.uniform(0.85, 1.15)
    ob.scale = (s, s, s * r.uniform(0.9, 1.1))
    coll(ctx, SUB).objects.link(ob)
    return ob


# ======================================================================= GN scatter
def _gn_scatter(name, source, density_m2, smin, smax, seed, pick=False, zrot=True, tilt=0.06,
                flatten=None):
    ng = bpy.data.node_groups.get(name)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, Lk = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    dist.inputs['Density'].default_value = density_m2
    dist.inputs['Seed'].default_value = seed
    Lk.new(gi.outputs[0], dist.inputs['Mesh'])
    nrm = N.new('GeometryNodeInputNormal')
    sxyz = N.new('ShaderNodeSeparateXYZ')
    cmp = N.new('FunctionNodeCompare')
    cmp.data_type = 'FLOAT'
    cmp.operation = 'GREATER_THAN'
    cmp.inputs['B'].default_value = 0.5
    Lk.new(nrm.outputs['Normal'], sxyz.inputs['Vector'])
    Lk.new(sxyz.outputs['Z'], cmp.inputs['A'])
    Lk.new(cmp.outputs['Result'], dist.inputs['Selection'])
    iop = N.new('GeometryNodeInstanceOnPoints')
    Lk.new(dist.outputs['Points'], iop.inputs['Points'])
    if isinstance(source, bpy.types.Collection):
        ci = N.new('GeometryNodeCollectionInfo')
        ci.inputs['Collection'].default_value = source
        ci.inputs['Separate Children'].default_value = True
        ci.inputs['Reset Children'].default_value = True
        Lk.new(ci.outputs[0], iop.inputs['Instance'])
        if pick:
            iop.inputs['Pick Instance'].default_value = True
            ri = N.new('FunctionNodeRandomValue')
            ri.data_type = 'INT'
            ri.inputs['Min'].default_value = 0
            ri.inputs['Max'].default_value = max(0, len(source.all_objects) - 1)
            ri.inputs['Seed'].default_value = seed + 3
            Lk.new(ri.outputs['Value'], iop.inputs['Instance Index'])
    else:
        oi = N.new('GeometryNodeObjectInfo')
        oi.inputs['Object'].default_value = source
        oi.inputs['As Instance'].default_value = True
        Lk.new(oi.outputs['Geometry'], iop.inputs['Instance'])
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    rr.inputs['Min'].default_value = (-tilt, -tilt, 0.0)
    rr.inputs['Max'].default_value = (tilt, tilt, 2 * math.pi if zrot else 0.0)
    rr.inputs['Seed'].default_value = seed + 1
    e2r = N.new('FunctionNodeEulerToRotation')
    Lk.new(rr.outputs['Value'], e2r.inputs['Euler'])
    Lk.new(e2r.outputs['Rotation'], iop.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT'
    rs.inputs['Min'].default_value = smin
    rs.inputs['Max'].default_value = smax
    rs.inputs['Seed'].default_value = seed + 2
    if flatten:
        # non-uniform scale (pebbles: x,y ~ s, z ~ s*flatten)
        rf = N.new('FunctionNodeRandomValue')
        rf.data_type = 'FLOAT'
        rf.inputs['Min'].default_value = flatten[0]
        rf.inputs['Max'].default_value = flatten[1]
        rf.inputs['Seed'].default_value = seed + 5
        rx = N.new('FunctionNodeRandomValue')
        rx.data_type = 'FLOAT'
        rx.inputs['Min'].default_value = 0.7
        rx.inputs['Max'].default_value = 1.0
        rx.inputs['Seed'].default_value = seed + 6
        mz = N.new('ShaderNodeMath')
        mz.operation = 'MULTIPLY'
        Lk.new(rs.outputs['Value'], mz.inputs[0])
        Lk.new(rf.outputs['Value'], mz.inputs[1])
        my = N.new('ShaderNodeMath')
        my.operation = 'MULTIPLY'
        Lk.new(rs.outputs['Value'], my.inputs[0])
        Lk.new(rx.outputs['Value'], my.inputs[1])
        cx = N.new('ShaderNodeCombineXYZ')
        Lk.new(rs.outputs['Value'], cx.inputs['X'])
        Lk.new(my.outputs[0], cx.inputs['Y'])
        Lk.new(mz.outputs[0], cx.inputs['Z'])
        Lk.new(cx.outputs['Vector'], iop.inputs['Scale'])
    else:
        Lk.new(rs.outputs['Value'], iop.inputs['Scale'])
    j = N.new('GeometryNodeJoinGeometry')
    Lk.new(gi.outputs[0], j.inputs[0])
    Lk.new(iop.outputs[0], j.inputs[0])
    Lk.new(j.outputs[0], go.inputs[0])
    return ng


def scatter(objs, ng):
    n = 0
    for ob in objs:
        md = ob.modifiers.new('scatter', 'NODES')
        md.node_group = ng
        n += 1
    return n


PEBBLE_RAMPS = {
    'river': ['#4a4e55', '#5d6168', '#6f6e6a', '#575553', '#7c7a74', '#8a857b'],
    'black': ['#1f1f20', '#2a2a2b', '#353534', '#262524', '#40403e', '#4a4946'],
}


def pebble_source(ctx, kind='river'):
    """A few smooth pebble meshes with a per-instance colour ramp (river: blue-grey, black: Mexican beach)."""
    name = f'lib_pebbles_{kind}'
    c = bpy.data.collections.get('ext_' + name)
    if c and len(c.objects):
        return c
    c = coll(ctx, name)
    from .exterior_util import _srgb
    m = bpy.data.materials.new(f'Z_exterior_pebble_{kind}')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cols = PEBBLE_RAMPS[kind]
    cr.elements[0].color = _srgb(cols[0])
    cr.elements[1].color = _srgb(cols[-1])
    for i, hx in enumerate(cols[1:-1]):
        e = cr.elements.new((i + 1) / (len(cols) - 1))
        e.color = _srgb(hx)
    cr.interpolation = 'CONSTANT'
    nt.links.new(oi.outputs['Random'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.38 if kind == 'black' else 0.5
    m.diffuse_color = _srgb(cols[2])
    r = rng(5 if kind == 'river' else 8)
    for k in range(5):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
        ax, ay = 1.0 + r.uniform(-0.15, 0.2), 0.75 + r.uniform(-0.12, 0.12)
        for v in bm.verts:
            v.co.x *= ax
            v.co.y *= ay
            v.co.z = max(v.co.z * 0.75, -0.18)            # flat-ish base so pebbles sit, not float
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.12))
        me = bpy.data.meshes.new(f'ext pebble {kind} {k}')
        bm.to_mesh(me)
        bm.free()
        me.shade_smooth()
        me.materials.append(m)
        ob = bpy.data.objects.new(f'ext pebble {kind} {k}', me)
        c.objects.link(ob)
    exclude_collection(c)
    return c


# ============================================================================ placement
HOUSE_RECTS = [(L.HX0 - 0.08, L.HX1 + 0.08, L.HZ0 - 0.08, L.GARAGE_FRONT + 0.05),        # main house + garage
               (L.HX0 - 0.08, 14.4, 47.0, L.BED3_FRONT + 0.05),                         # bedroom 3
               (2.7, 11.4, L.BED3_FRONT, 56.1),                                         # its canted bay
               (L.PORCH_POSTS[0][0], L.PORCH_POSTS[1][1], 47.4, L.PORCH[3] + 0.05)]      # covered porch


def _check_clear(inst, x, z, eave=0.7):
    """Warn when a plant's canopy (bbox radius) would reach into the house / under the eaves."""
    c = inst.instance_collection
    rad = c['width_m'] / 2 * inst.scale[0] / FT
    for (x0, x1, z0, z1) in HOUSE_RECTS:
        dx = max(x0 - eave - x, 0, x - x1 - eave)
        dz = max(z0 - eave - z, 0, z - z1 - eave)
        if math.hypot(dx, dz) < rad * 0.92:
            print(f'[exterior] WARNING canopy of {c.name} at ({x:.1f},{z:.1f}) r={rad:.1f}ft reaches the house')
    return inst


def _row(a, b, step, jitter, r):
    out = []
    n = max(1, int(round((b - a) / step)))
    for k in range(n):
        out.append(a + (k + 0.5) * (b - a) / n + r.uniform(-jitter, jitter))
    return out


def build(ctx, surfaces):
    r = rng(2024)
    res = {}
    leaf_tree = dict(amount=0.3)
    leaf_olive = dict(amount=0.28, hue=0.49, sat=0.62, val=0.95)     # grey-green olive foliage
    # ---- lawns: GN instanced blade clumps
    lawn_src = proc_plant(ctx, 'lawn')
    ng = _gn_scatter('ext GN lawn', lawn_src, density_m2=640.0, smin=0.8, smax=1.25, seed=3, tilt=0.12)
    res['lawn_surfaces'] = scatter(surfaces.get('lawns', []), ng)
    # ---- pebbles on borders / drip strips / walk corridor
    for kind, dens, smin, smax in (('river', 900.0, 0.03, 0.058), ('black', 1100.0, 0.022, 0.045)):
        objs = [o for o in surfaces.get('pebbles', []) if o.get('pebble', 'river') == kind]
        ngp = _gn_scatter(f'ext GN pebbles {kind}', pebble_source(ctx, kind), density_m2=dens, smin=smin, smax=smax,
                          seed=9 if kind == 'river' else 13, pick=True, tilt=0.25, flatten=(0.45, 0.7))
        res[f'pebble_surfaces_{kind}'] = scatter(objs, ngp)

    # ---- trees (Poly Haven): olive-like island_tree_01, multi-stem island_tree_02
    fn = L.FN                                     # rear planting is placed relative to the rear fence
    trees = [
        ('island_tree_01', 'main', 6.0, fn + 1.4, 15.0, '2k', leaf_olive),     # rear bed, behind primary/bed2
        ('island_tree_01', 'main', 31.0, fn + 1.2, 16.0, '2k', leaf_olive),    # rear bed, living-room hero
        ('island_tree_02', 'main', -3.4, fn + 1.8, 11.0, '1k', leaf_tree),     # NW corner
        ('island_tree_02', 'main', 43.8, fn + 2.0, 12.0, '1k', leaf_tree),     # NE corner
        ('island_tree_01', 'main', -2.8, 64.5, 11.5, '2k', leaf_olive),        # front lawn, west of the bay
        ('island_tree_02', 'main', 43.6, 61.5, 10.5, '1k', leaf_tree),         # front, east of the drive
    ]
    for aid, var, x, z, h, rs, lf in trees:
        _check_clear(plant(ctx, aid, var, x, z, height_ft=h, res=rs, leaf=lf), x, z)
    # narrow evergreen screens in the side yards (outside the primary's added west window and kitchen W08)
    for x, z, h in ((L.FW + 0.95, 10.6, 7.5), (L.FE - 1.2, 26.1, 8.0)):
        _check_clear(plant(ctx, 'searsia_lucida', 'b', x, z, height_ft=h, res='2k',
                           leaf=dict(amount=0.25, hue=0.5, sat=0.8)), x, z)
    # street trees in our park strip
    for x in (4.0, 48.5):
        plant(ctx, 'tree_small_02', 'main', x, (L.PARK[0] + L.PARK[1]) / 2, height_ft=r.uniform(19, 22),
              leaf=leaf_tree)
    # ---- shrubs (searsia_lucida variants = Mediterranean evergreen shrubs; shrub_02 small)
    sv = ['d', 'e', 'f']
    sl = dict(amount=0.25, hue=0.5, sat=0.8)
    # rear bed: shrub / grass rhythm along the fence, kept low under the trees
    # (art direction: the bed read sparse from L0/L1/B2/P0 -> tighter shrub rhythm, taller back row,
    #  lomandra fill between shrubs and a denser front row of grasses)
    xs = _row(L.REAR_BED[0] + 1.0, L.REAR_BED[1] - 1.0, 3.3, 0.35, r)
    for i, x in enumerate(xs):
        z = fn + 0.85 + r.uniform(-0.15, 0.15)
        if abs(x - 6.0) < 2.2 or abs(x - 31.0) < 2.2 or x < -2.0 or x > 42.4:
            place_proc(ctx, 'lomandra', x, z, scale=r.uniform(1.0, 1.2))
            continue
        if i % 3 == 1:
            place_proc(ctx, 'phormium', x, z, scale=r.uniform(0.95, 1.15))
        else:
            plant(ctx, 'searsia_lucida', sv[i % 3], x, z, height_ft=r.uniform(3.6, 4.8), res='2k', leaf=sl)
        if i + 1 < len(xs):                      # low fill between the back-row plants
            xm = (x + xs[i + 1]) / 2 + r.uniform(-0.2, 0.2)
            if not (abs(xm - 6.0) < 1.6 or abs(xm - 31.0) < 1.6):
                place_proc(ctx, 'lomandra', xm, fn + 1.4 + r.uniform(-0.15, 0.15), scale=r.uniform(0.8, 0.95))
    for x in _row(L.REAR_BED[0] + 0.8, L.REAR_BED[1] - 0.8, 1.6, 0.2, r):
        k = 'feather' if int(x * 7) % 3 else 'fescue'
        place_proc(ctx, k, x, fn + 1.9 + r.uniform(-0.1, 0.1), scale=r.uniform(0.9, 1.1))
    # side-yard fence beds
    for (bx0, bx1, bz0, bz1), skip in ((L.W_BED, (10.6,)), (L.E_BED, (26.1,))):
        xc = (bx0 + bx1) / 2
        for i, z in enumerate(_row(bz0 + 1.2, bz1 - 1.0, 3.0, 0.3, r)):
            if any(abs(z - s) < 3.0 for s in skip):
                place_proc(ctx, 'fescue', xc + r.uniform(-0.2, 0.2), z, scale=0.9)
                continue
            if i % 4 == 0:
                plant(ctx, 'searsia_lucida', 'f' if i % 8 else 'e', xc, z, height_ft=r.uniform(2.6, 3.4), res='2k',
                      leaf=sl)
            else:
                place_proc(ctx, 'lomandra' if i % 2 else 'feather', xc + r.uniform(-0.15, 0.15), z,
                           scale=r.uniform(0.85, 1.0))
    # front: bed along bedroom 3 / bay, west corner bed, bank between walk and drive, east beds
    fb = L.FRONT_BED
    for i, x in enumerate(_row(fb[0] + 0.8, L.PORCH_POSTS[0][0] - 0.6, 2.3, 0.2, r)):
        b3 = L.BED3_FRONT
        if abs(x + 2.6) < 1.6:
            place_proc(ctx, 'fescue', x, b3 + 1.65, scale=0.9)
            continue
        zz = b3 + 1.05 if not (2.6 < x < 11.5) else 57.15          # clear of the bay (to z ~56.0)
        if i % 3 == 0:
            plant(ctx, 'searsia_lucida', 'e' if i % 2 else 'f', x, zz, height_ft=r.uniform(2.4, 3.0), res='2k',
                  leaf=sl)
        else:
            place_proc(ctx, 'lomandra' if i % 3 == 1 else 'feather', x, zz, scale=r.uniform(0.8, 0.95))
        place_proc(ctx, 'fescue', x + 0.9, 58.35 + r.uniform(-0.1, 0.1), scale=r.uniform(0.85, 1.0))
    for z in _row(L.W_FRONT_BED[2] + 0.6, L.W_FRONT_BED[3] - 0.4, 2.0, 0.15, r):
        place_proc(ctx, 'lomandra', -3.2 + r.uniform(-0.4, 0.4), z, scale=0.9)
    for z in _row(L.STRIP[2] + 1.0, L.STRIP[3] - 0.8, 1.7, 0.1, r):
        x = (L.STRIP[0] + L.STRIP[1]) / 2 + r.uniform(-0.15, 0.15)
        place_proc(ctx, 'fescue' if int(z) % 2 else 'feather', x, z, y=L.bank_top(x, z, L.STRIP[0], L.STRIP[1]),
                   scale=0.85)
    for z in _row(L.E_FRONT_BED1[2] + 0.8, L.E_FRONT_BED1[3] - 0.5, 2.2, 0.2, r):
        place_proc(ctx, 'lomandra', (L.E_FRONT_BED1[0] + L.E_FRONT_BED1[1]) / 2 + r.uniform(-0.6, 0.6), z,
                   scale=0.95)
    for i, z in enumerate(_row(L.E_FRONT_BED2[2] + 1.0, L.E_FRONT_BED2[3] - 0.8, 2.6, 0.2, r)):
        x = L.DRIVE[1] + 2.3 + r.uniform(-0.2, 0.2)
        place_proc(ctx, 'feather' if i % 2 else 'fescue', x, z, y=L.bank_top(x, z, L.E_BANK_X, L.DRIVE[1]) - 0.0,
                   scale=0.85)
        if abs(z - 60.5) > 3.0:                  # (clear of the front tree)
            place_proc(ctx, 'lomandra', L.FE - 0.75 + r.uniform(-0.25, 0.25), z + 1.2, scale=0.9)
    # our park strip: grasses in gravel either side of the street trees
    for x in _row(L.FW + 1.0, L.DRIVE[0] - 1.5, 3.2, 0.3, r) + _row(L.DRIVE[1] + 1.5, L.FE - 1.0, 3.2, 0.3, r):
        if abs(x - 4.0) < 1.6 or abs(x - 48.5) < 1.6:
            continue
        place_proc(ctx, 'fescue', x, (L.PARK[0] + L.PARK[1]) / 2 + r.uniform(-0.6, 0.6), y=GRADE + 0.03,
                   scale=0.9)
    # a tall charcoal fibre-cement planter on the deck beside the garden door
    from .exterior_util import MB
    from .exterior_util import mul_copy
    pm = mul_copy(ctx, 'foundation', (0.14, 0.145, 0.15), 'Z_exterior_planter')     # dark fibre-cement
    for (x, z, w, h, kind, sc) in ((23.25, -1.25, 1.7, 2.3, 'phormium', 1.0),):     # west of the door (24.45)
        mb = MB()
        t = 0.08
        y0, y1 = L.DECK_TOP, L.DECK_TOP + h
        mb.box(x - w / 2, x + w / 2, y0, y1, z - w / 2, z - w / 2 + t)
        mb.box(x - w / 2, x + w / 2, y0, y1, z + w / 2 - t, z + w / 2)
        mb.box(x - w / 2, x - w / 2 + t, y0, y1, z - w / 2 + t, z + w / 2 - t)
        mb.box(x + w / 2 - t, x + w / 2, y0, y1, z - w / 2 + t, z + w / 2 - t)
        mb.box(x - w / 2 + t, x + w / 2 - t, y0, y1 - 0.12, z - w / 2 + t, z + w / 2 - t)
        mb.obj(ctx, f'ext deck planter {kind}', pm, SUB, bevel=0.02, segments=2)
        sm = MB()
        sm.box(x - w / 2 + t, x + w / 2 - t, y1 - 0.13, y1 - 0.1, z - w / 2 + t, z + w / 2 - t)
        sm.obj(ctx, f'ext deck planter soil', ctx.mat('soil_mulch'), SUB)
        place_proc(ctx, kind, x, z, y=y1 - 0.1, scale=sc)
    res['proc_plants'] = len([o for o in coll(ctx, SUB).objects if o.type == 'MESH'])
    res['instances'] = len([o for o in coll(ctx, SUB).objects if o.type == 'EMPTY'])
    return res
