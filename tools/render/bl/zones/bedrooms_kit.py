"""Procedural modelling kit for the bedrooms zone (runs inside Blender).

Everything here works in SCENE feet (x east, y up, z south) like `common.Ctx`. A `Frame` gives a
local placement (origin + yaw about +Y) so a bed, desk or closet can be modelled once in its own
coordinates (local +z = "forward", e.g. from the headboard toward the foot of the bed) and dropped
into any room. Soft goods (pillows, duvets, throws, cushions, drapes) are generated as real
meshes with seams, drape and gentle wrinkles; hard goods get bevelled edges.

Zone-specific materials are named `Z_bedrooms_<name>`; shared finishes come from `ctx.mat(key)`.
"""
import math
import random

import bmesh
import bpy
import numpy as np

from ..common import FT, ft2bl
from .. import lighting

TAU = math.tau


# ----------------------------------------------------------------------------------- placement
class Frame:
    """Local frame: origin (ox, oy, oz) SCENE feet, yaw `rot` radians about +Y.
    local +z -> SCENE (sin rot, 0, cos rot); local +x -> SCENE (cos rot, 0, -sin rot)."""

    def __init__(self, ox, oz, rot=0.0, oy=0.0):
        self.ox, self.oy, self.oz, self.rot = ox, oy, oz, rot
        self.c, self.s = math.cos(rot), math.sin(rot)

    def p(self, lx, ly, lz):
        return (self.ox + lx * self.c + lz * self.s, self.oy + ly, self.oz - lx * self.s + lz * self.c)

    def r(self, lrot=0.0):
        return self.rot + lrot

    def sub(self, lx, lz, lrot=0.0, ly=0.0):
        """Child frame at local (lx, ly, lz), additionally yawed by lrot."""
        x, y, z = self.p(lx, ly, lz)
        return Frame(x, z, self.rot + lrot, y)


# ---------------------------------------------------------------------------------- geometry
def _merge(verts, faces, dist=1e-6):
    """Weld coincident vertices (pillow seams) and recompute outward normals."""
    me = bpy.data.meshes.new('_tmp')
    me.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    out_v = [tuple(v.co) for v in bm.verts]
    out_f = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    bpy.data.meshes.remove(me)
    return out_v, out_f


def pillow_geo(w, d, t, n=18, pinch=0.07, puff=2.6):
    """Stuffed pillow lying flat: width w (local x), depth d (local z), thickness t (y), centred.
    Top and bottom panels meet at a sewn seam; the outline pinches in between the corners."""
    us = np.linspace(-1.0, 1.0, n + 1)
    verts, faces = [], []

    def g(s):
        return max(0.0, 1.0 - abs(s) ** puff) ** 0.55

    for side in (1, -1):
        base = len(verts)
        for u in us:
            for v in us:
                px = u * w / 2 * (1 - pinch * (1 - v * v))
                pz = v * d / 2 * (1 - pinch * (1 - u * u))
                h = side * t / 2 * g(u) * g(v)
                verts.append((px, h, pz))
        m = n + 1
        for i in range(n):
            for j in range(n):
                a, b, c, e = base + i * m + j, base + i * m + j + 1, base + (i + 1) * m + j + 1, base + (i + 1) * m + j
                faces.append((a, b, c, e) if side > 0 else (a, e, c, b))
    return _merge(verts, faces, 1e-5)


def drape_geo(W, L, top_y, r, hem_y, sides='lrf', step=0.09, folds=0.0, corner_drop=0.25, seed=1, z0=0.0):
    """Cloth sheet lying on the rectangle x in [-W/2, W/2], z in [z0, z0+L] at height top_y and
    hanging over the listed sides ('l' = -x, 'r' = +x, 'f' = +z foot, 'h' = -z head) around a
    rounded edge of radius r down to hem_y. Returns the OUTER surface (normals up/out)."""
    rng = random.Random(seed)
    arc = math.pi * r / 2
    D = arc + max(0.0, (top_y - hem_y) - r)
    x0 = -W / 2 - (D if 'l' in sides else 0)
    x1 = W / 2 + (D if 'r' in sides else 0)
    za = z0 - (D if 'h' in sides else 0)
    zb = z0 + L + (D if 'f' in sides else 0)
    nx = max(2, int(round((x1 - x0) / step)))
    nz = max(2, int(round((zb - za) / step)))
    ph = [rng.uniform(0, TAU) for _ in range(4)]
    lam = [rng.uniform(0.55, 0.8) for _ in range(4)]
    verts = []
    for i in range(nx + 1):
        u = x0 + (x1 - x0) * i / nx
        for j in range(nz + 1):
            v = za + (zb - za) * j / nz
            cx = min(max(u, -W / 2), W / 2)
            cz = min(max(v, z0), z0 + L)
            dx, dz = u - cx, v - cz
            d = math.hypot(dx, dz)
            if d < 1e-9:
                verts.append((u, top_y, v))
                continue
            nxx, nzz = dx / d, dz / d
            if d > D:
                d = D + (d - D) * corner_drop
            if d <= arc:
                th = d / r
                off, drop = r * math.sin(th), r * (1 - math.cos(th))
            else:
                off, drop = r, r + (d - arc)
                if folds > 0:
                    k = min(1.0, (d - arc) / 0.45)
                    tang = cz if abs(nxx) > abs(nzz) else cx
                    side_i = (0 if nxx < -0.5 else 1 if nxx > 0.5 else 2 if nzz > 0 else 3)
                    off += folds * k * (0.6 * math.sin(TAU * tang / lam[side_i] + ph[side_i])
                                        + 0.4 * math.sin(TAU * tang / (lam[side_i] * 0.43) + 2 * ph[side_i]))
            verts.append((cx + nxx * off, top_y - drop, cz + nzz * off))
    faces = []
    m = nz + 1
    for i in range(nx):
        for j in range(nz):
            a, b, c, e = i * m + j, i * m + j + 1, (i + 1) * m + j + 1, (i + 1) * m + j
            faces.append((a, b, c, e))      # +x by +z -> normal +y (up)
    return verts, faces


def lathe_geo(profile, segs=48, closed=False):
    """Revolve [(r, y), ...] (bottom -> top) about local +Y. closed=True treats the profile as a
    closed loop (e.g. a lamp shade with thickness). Open ends with r>0 are capped."""
    verts, faces = [], []
    n = len(profile)
    for (r, y) in profile:
        for k in range(segs):
            a = TAU * k / segs
            verts.append((r * math.cos(a), y, r * math.sin(a)))
    rings = n if closed else n - 1
    for i in range(rings):
        i2 = (i + 1) % n
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i2 * segs + k, i2 * segs + k2, i * segs + k2))
    if not closed:
        for idx, (r, y) in ((0, profile[0]), (n - 1, profile[-1])):
            if r > 1e-6:
                c = len(verts)
                verts.append((0.0, y, 0.0))
                for k in range(segs):
                    k2 = (k + 1) % segs
                    faces.append((idx * segs + k, idx * segs + k2, c))
    return _merge(verts, faces, 1e-7)


def prism_geo(poly, y0, y1):
    """Vertical prism from a plan polygon [(x, z), ...]."""
    n = len(poly)
    verts = [(x, y0, z) for x, z in poly] + [(x, y1, z) for x, z in poly]
    faces = [tuple(range(n)), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    return _merge(verts, faces, 1e-7)


def rounded_rect(w, d, r, seg=8):
    """Plan outline of a rounded rectangle centred at the origin."""
    r = min(r, w / 2 - 1e-4, d / 2 - 1e-4)
    pts = []
    for cx, cz, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90 * k / seg)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def frustum_geo(bx, bz, tx, tz, h):
    """Tapered leg / block: bottom size (bx, bz) at y=0, top size (tx, tz) at y=h, centred."""
    v = [(-bx / 2, 0, -bz / 2), (bx / 2, 0, -bz / 2), (bx / 2, 0, bz / 2), (-bx / 2, 0, bz / 2),
         (-tx / 2, h, -tz / 2), (tx / 2, h, -tz / 2), (tx / 2, h, tz / 2), (-tx / 2, h, tz / 2)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _merge(v, f, 1e-7)


# ---------------------------------------------------------------------------------- materials
def _hex(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _new_mat(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m, False
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, True


def principled(name, color, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, spec=0.5, bump=None):
    """Simple Principled material. bump = (scale_per_m, strength, detail) of a noise bump."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = _hex(color) if isinstance(color, str) else color
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
        b.inputs['Sheen Roughness'].default_value = 0.45
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.08
    if bump:
        sc, st, det = bump
        tc = nt.nodes.new('ShaderNodeTexCoord')
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = sc
        nz.inputs['Detail'].default_value = det
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = st
        bp.inputs['Distance'].default_value = 0.002
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = _hex(color) if isinstance(color, str) else color
    return m


def fabric(name, color, rough=0.92, sheen=0.6, weave=420.0, strength=0.25, slub=True, crumple=0.0):
    """Woven fabric: base colour with slubby tonal variation, sheen and a fine weave bump.
    crumple > 0 adds soft slept-in creases (ridged low-frequency noise) for washed-linen bedding."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    col = _hex(color)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Sheen Weight'].default_value = sheen
    b.inputs['Sheen Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.35
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # tonal slub variation
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 18.0
    n1.inputs['Detail'].default_value = 4.0
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = tuple(c * 0.9 for c in col[:3]) + (1,)
    mix.inputs['B'].default_value = tuple(min(1.0, c * 1.06) for c in col[:3]) + (1,)
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
    nt.links.new(n1.outputs['Fac'], mix.inputs['Factor'])
    if slub:
        nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = col
    # weave bump: two crossed wave textures
    w1 = nt.nodes.new('ShaderNodeTexWave')
    w1.inputs['Scale'].default_value = weave
    w1.inputs['Distortion'].default_value = 2.0
    w1.wave_type = 'BANDS'
    w1.bands_direction = 'X'
    w2 = nt.nodes.new('ShaderNodeTexWave')
    w2.inputs['Scale'].default_value = weave
    w2.inputs['Distortion'].default_value = 2.0
    w2.wave_type = 'BANDS'
    w2.bands_direction = 'Z'
    for w in (w1, w2):
        nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    add = nt.nodes.new('ShaderNodeMath')
    add.operation = 'MULTIPLY'
    nt.links.new(w1.outputs['Fac'], add.inputs[0])
    nt.links.new(w2.outputs['Fac'], add.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = strength
    bp.inputs['Distance'].default_value = 0.0015
    nt.links.new(add.outputs['Value'], bp.inputs['Height'])
    if crumple > 0:
        # creases: valleys where a distorted low-frequency noise crosses 0.5 (|n - 0.5|)
        cn = nt.nodes.new('ShaderNodeTexNoise')
        cn.inputs['Scale'].default_value = 4.5
        cn.inputs['Detail'].default_value = 4.0
        cn.inputs['Roughness'].default_value = 0.55
        cn.inputs['Distortion'].default_value = 1.4
        nt.links.new(tc.outputs['Object'], cn.inputs['Vector'])
        sub = nt.nodes.new('ShaderNodeMath')
        sub.operation = 'SUBTRACT'
        sub.inputs[1].default_value = 0.5
        nt.links.new(cn.outputs['Fac'], sub.inputs[0])
        ab = nt.nodes.new('ShaderNodeMath')
        ab.operation = 'ABSOLUTE'
        nt.links.new(sub.outputs[0], ab.inputs[0])
        sq = nt.nodes.new('ShaderNodeMath')
        sq.operation = 'POWER'
        sq.inputs[1].default_value = 0.5
        nt.links.new(ab.outputs[0], sq.inputs[0])
        bc = nt.nodes.new('ShaderNodeBump')
        bc.inputs['Strength'].default_value = crumple
        bc.inputs['Distance'].default_value = 0.012
        nt.links.new(sq.outputs[0], bc.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], bc.inputs['Normal'])
        nt.links.new(bc.outputs['Normal'], b.inputs['Normal'])
    else:
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = col
    return m


def stripe(m, color, axis='X', period_in=0.5, duty=0.4):
    """Overlay woven vertical stripes on a fabric() material (bengal stripe shirting). axis: Blender
    object axis the stripes alternate along (the garment's width direction). Applied once."""
    nt = m.node_tree
    if m.get('striped'):
        return m
    b = nt.nodes['Principled BSDF']
    if not b.inputs['Base Color'].links:
        return m
    src = b.inputs['Base Color'].links[0].from_socket
    tc = nt.nodes.new('ShaderNodeTexCoord')
    w = nt.nodes.new('ShaderNodeTexWave')
    w.wave_type = 'BANDS'
    w.bands_direction = axis
    w.wave_profile = 'SAW'
    w.inputs['Scale'].default_value = 0.31416 / (period_in * 0.0254)
    w.inputs['Distortion'].default_value = 0.0
    nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    mk = nt.nodes.new('ShaderNodeMapRange')
    mk.inputs['From Min'].default_value = duty - 0.04
    mk.inputs['From Max'].default_value = duty + 0.04
    mk.inputs['To Min'].default_value = 1.0
    mk.inputs['To Max'].default_value = 0.0
    nt.links.new(w.outputs['Fac'], mk.inputs['Value'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    sk = {x.identifier: x for x in mix.inputs}
    nt.links.new(src, sk['A_Color'])
    sk['B_Color'].default_value = _hex(color)
    nt.links.new(mk.outputs[0], sk['Factor_Float'])
    nt.links.new([o for o in mix.outputs if o.identifier == 'Result_Color'][0], b.inputs['Base Color'])
    m['striped'] = 1
    return m


def boucle(name, color):
    """Looped boucle: strong small-scale nubby bump (Voronoi) with sheen."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    col = _hex(color)
    b.inputs['Roughness'].default_value = 0.95
    b.inputs['Sheen Weight'].default_value = 0.9
    b.inputs['Sheen Roughness'].default_value = 0.55
    b.inputs['Specular IOR Level'].default_value = 0.3
    tc = nt.nodes.new('ShaderNodeTexCoord')
    # loops ~7 mm with lumpy ~2 cm clusters: fine enough to read as boucle, coarse enough to survive
    # a 4k panorama (a 4 mm loop is sub-pixel at 2 m and averages away)
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 140.0
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 45.0
    nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(vo.outputs['Distance'], mul.inputs[0])
    nt.links.new(nz.outputs['Fac'], mul.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.75
    bp.inputs['Distance'].default_value = 0.004
    nt.links.new(mul.outputs['Value'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = tuple(c * 0.78 for c in col[:3]) + (1,)
    mix.inputs['B'].default_value = col
    nt.links.new(mul.outputs['Value'], mix.inputs['Factor'])
    # tonal clusters (~3 cm) so the nubby surface reads even where the bump is sub-pixel
    cl = nt.nodes.new('ShaderNodeTexNoise')
    cl.inputs['Scale'].default_value = 30.0
    cl.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], cl.inputs['Vector'])
    mix2 = nt.nodes.new('ShaderNodeMix')
    mix2.data_type = 'RGBA'
    mix2.blend_type = 'MULTIPLY'
    mix2.inputs['Factor'].default_value = 0.12
    nt.links.new(mix.outputs['Result'], mix2.inputs['A'])
    nt.links.new(cl.outputs['Color'], mix2.inputs['B'])
    nt.links.new(mix2.outputs['Result'], b.inputs['Base Color'])
    m.diffuse_color = col
    return m


def knit(name, color, scale=60.0):
    """Chunky knit throw: rib bands + stitch bumps."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    col = _hex(color)
    b.inputs['Roughness'].default_value = 0.96
    b.inputs['Sheen Weight'].default_value = 0.8
    b.inputs['Sheen Roughness'].default_value = 0.5
    b.inputs['Specular IOR Level'].default_value = 0.25
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'X'
    wv.wave_profile = 'SIN'
    wv.inputs['Scale'].default_value = scale
    wv2 = nt.nodes.new('ShaderNodeTexWave')
    wv2.wave_type = 'BANDS'
    wv2.bands_direction = 'Y'
    wv2.wave_profile = 'SIN'
    wv2.inputs['Scale'].default_value = scale * 1.6
    for w in (wv, wv2):
        nt.links.new(tc.outputs['Object'], w.inputs['Vector'])
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    nt.links.new(wv.outputs['Fac'], mul.inputs[0])
    nt.links.new(wv2.outputs['Fac'], mul.inputs[1])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.8
    bp.inputs['Distance'].default_value = 0.006
    nt.links.new(mul.outputs['Value'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.inputs['A'].default_value = tuple(c * 0.7 for c in col[:3]) + (1,)
    mix.inputs['B'].default_value = col
    nt.links.new(mul.outputs['Value'], mix.inputs['Factor'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    m.diffuse_color = col
    return m


def translucent_fabric(name, color, trans=0.45, rough=0.9):
    """Lamp shade / roller shade / sheer: diffuse + translucent so light glows through."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    col = _hex(color)
    df = nt.nodes.new('ShaderNodeBsdfDiffuse')
    df.inputs['Color'].default_value = col
    df.inputs['Roughness'].default_value = rough
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = tuple(min(1.0, c * 1.02) for c in col[:3]) + (1,)
    mx = nt.nodes.new('ShaderNodeMixShader')
    mx.inputs['Fac'].default_value = trans
    nt.links.new(df.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs['Surface'])
    m.diffuse_color = col
    return m


def sheer(name, color, opacity=0.55):
    """Sheer curtain: partly transparent translucent linen (lets daylight and view through)."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    col = _hex(color)
    df = nt.nodes.new('ShaderNodeBsdfDiffuse')
    df.inputs['Color'].default_value = col
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = col
    mx = nt.nodes.new('ShaderNodeMixShader')
    mx.inputs['Fac'].default_value = 0.5
    nt.links.new(df.outputs[0], mx.inputs[1])
    nt.links.new(tl.outputs[0], mx.inputs[2])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx2 = nt.nodes.new('ShaderNodeMixShader')
    mx2.inputs['Fac'].default_value = opacity
    nt.links.new(tr.outputs[0], mx2.inputs[1])
    nt.links.new(mx.outputs[0], mx2.inputs[2])
    nt.links.new(mx2.outputs[0], out.inputs['Surface'])
    m.diffuse_color = col
    return m


def image_material(name, img, rough=0.85, coat=0.0):
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = rough
    b.inputs['Specular IOR Level'].default_value = 0.3
    if coat:
        b.inputs['Coat Weight'].default_value = coat
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = img
    tex.interpolation = 'Cubic'
    uv = nt.nodes.new('ShaderNodeUVMap')
    nt.links.new(uv.outputs['UV'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], b.inputs['Base Color'])
    # canvas / paper tooth
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 900.0
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.12
    bp.inputs['Distance'].default_value = 0.0005
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


def rug_material(name, palette, scale=1.4, pattern='watercolor', border=None):
    """Low-pile wool rug. palette: list of hex colours light -> dark.
    pattern: 'watercolor' (abstract marbled), 'lattice' (tone-on-tone diamond), 'heather'.
    border: optional (half_w_ft, half_d_ft, colour, ((d0, d1), ...)) woven bands at distances d0..d1 ft
    from the rug edge (needs the rug object's origin at its centre, as Kit.wbox makes it)."""
    m, new = _new_mat(name)
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.97
    b.inputs['Sheen Weight'].default_value = 0.7
    b.inputs['Sheen Roughness'].default_value = 0.6
    b.inputs['Specular IOR Level'].default_value = 0.2
    tc = nt.nodes.new('ShaderNodeTexCoord')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    els = ramp.color_ramp.elements
    cols = [_hex(c) for c in palette]
    if pattern == 'watercolor':
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = 7.0
        nz.inputs['Roughness'].default_value = 0.62
        nz.inputs['Distortion'].default_value = 0.9
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        src = nz.outputs['Fac']
        stops = [0.0, 0.37, 0.48, 0.58, 0.68][:len(cols)]
    elif pattern == 'lattice':
        # two diagonal band sets -> diamond lattice, softened by noise
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Rotation'].default_value = (0, 0, math.radians(45))
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(mp.outputs['Vector'], sep.inputs['Vector'])
        outs = []
        for comp in ('X', 'Y'):
            s1 = nt.nodes.new('ShaderNodeMath')
            s1.operation = 'MULTIPLY'
            s1.inputs[1].default_value = scale
            nt.links.new(sep.outputs[comp], s1.inputs[0])
            fr = nt.nodes.new('ShaderNodeMath')
            fr.operation = 'PINGPONG'
            fr.inputs[1].default_value = 0.5
            nt.links.new(s1.outputs[0], fr.inputs[0])
            outs.append(fr)
        mn = nt.nodes.new('ShaderNodeMath')
        mn.operation = 'MINIMUM'
        nt.links.new(outs[0].outputs[0], mn.inputs[0])
        nt.links.new(outs[1].outputs[0], mn.inputs[1])
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = 9.0
        nz.inputs['Detail'].default_value = 3.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        jit = nt.nodes.new('ShaderNodeMath')
        jit.operation = 'MULTIPLY_ADD'
        jit.inputs[1].default_value = 0.08
        jit.inputs[2].default_value = -0.04
        nt.links.new(nz.outputs['Fac'], jit.inputs[0])
        ad = nt.nodes.new('ShaderNodeMath')
        ad.operation = 'ADD'
        nt.links.new(mn.outputs[0], ad.inputs[0])
        nt.links.new(jit.outputs[0], ad.inputs[1])
        src = ad.outputs[0]
        stops = [0.0, 0.06, 0.1][:len(cols)]
    else:
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = scale
        nz.inputs['Detail'].default_value = 10.0
        nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
        src = nz.outputs['Fac']
        stops = [0.3, 0.5, 0.7][:len(cols)]
    while len(els) < len(cols):
        els.new(0.5)
    for e, c, s in zip(els, cols, stops):
        e.position = s
        e.color = c
    if pattern == 'lattice':
        els[0].position, els[1].position = 0.04, 0.09
        if len(els) > 2:
            els[2].position = 0.5
    nt.links.new(src, ramp.inputs['Fac'])
    # pile: fine fibre noise modulates colour and bump
    fib = nt.nodes.new('ShaderNodeTexNoise')
    fib.inputs['Scale'].default_value = 520.0
    fib.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], fib.inputs['Vector'])
    mixc = nt.nodes.new('ShaderNodeMix')
    mixc.data_type = 'RGBA'
    mixc.blend_type = 'MULTIPLY'
    mixc.inputs['Factor'].default_value = 0.18
    col_out = ramp.outputs['Color']
    if border:
        hw, hd, bcol, bands = border
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
        dists = []
        for comp, h in (('X', hw), ('Y', hd)):
            ab = nt.nodes.new('ShaderNodeMath')
            ab.operation = 'ABSOLUTE'
            nt.links.new(sep.outputs[comp], ab.inputs[0])
            sb = nt.nodes.new('ShaderNodeMath')
            sb.operation = 'SUBTRACT'
            sb.inputs[0].default_value = h * 0.3048
            nt.links.new(ab.outputs[0], sb.inputs[1])
            dists.append(sb)
        dm = nt.nodes.new('ShaderNodeMath')
        dm.operation = 'MINIMUM'
        nt.links.new(dists[0].outputs[0], dm.inputs[0])
        nt.links.new(dists[1].outputs[0], dm.inputs[1])
        # slight hand-woven wobble of the band edges
        wob = nt.nodes.new('ShaderNodeTexNoise')
        wob.inputs['Scale'].default_value = 12.0
        nt.links.new(tc.outputs['Object'], wob.inputs['Vector'])
        wj = nt.nodes.new('ShaderNodeMath')
        wj.operation = 'MULTIPLY_ADD'
        wj.inputs[1].default_value = 0.006
        wj.inputs[2].default_value = -0.003
        nt.links.new(wob.outputs['Fac'], wj.inputs[0])
        dd = nt.nodes.new('ShaderNodeMath')
        dd.operation = 'ADD'
        nt.links.new(dm.outputs[0], dd.inputs[0])
        nt.links.new(wj.outputs[0], dd.inputs[1])
        mask = None
        for d0, d1 in bands:
            lo = nt.nodes.new('ShaderNodeMath')
            lo.operation = 'GREATER_THAN'
            lo.inputs[1].default_value = d0 * 0.3048
            nt.links.new(dd.outputs[0], lo.inputs[0])
            hi = nt.nodes.new('ShaderNodeMath')
            hi.operation = 'LESS_THAN'
            hi.inputs[1].default_value = d1 * 0.3048
            nt.links.new(dd.outputs[0], hi.inputs[0])
            band = nt.nodes.new('ShaderNodeMath')
            band.operation = 'MULTIPLY'
            nt.links.new(lo.outputs[0], band.inputs[0])
            nt.links.new(hi.outputs[0], band.inputs[1])
            if mask is None:
                mask = band
            else:
                mx = nt.nodes.new('ShaderNodeMath')
                mx.operation = 'MAXIMUM'
                nt.links.new(mask.outputs[0], mx.inputs[0])
                nt.links.new(band.outputs[0], mx.inputs[1])
                mask = mx
        bm = nt.nodes.new('ShaderNodeMix')
        bm.data_type = 'RGBA'
        bm.inputs['B'].default_value = _hex(bcol)
        nt.links.new(mask.outputs[0], bm.inputs['Factor'])
        nt.links.new(ramp.outputs['Color'], bm.inputs['A'])
        col_out = bm.outputs['Result']
    nt.links.new(col_out, mixc.inputs['A'])
    nt.links.new(fib.outputs['Color'], mixc.inputs['B'])
    nt.links.new(mixc.outputs['Result'], b.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.6
    bp.inputs['Distance'].default_value = 0.002
    nt.links.new(fib.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = cols[0]
    return m


# ---------------------------------------------------------------------------------- artwork
def _fbm(h, w, cells, rng, octaves=4):
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cy, cx = max(2, int(cells * h / max(h, w) * 2 ** o)), max(2, int(cells * w / max(h, w) * 2 ** o))
        g = rng.random((cy + 1, cx + 1)).astype(np.float32)
        ys = np.linspace(0, cy, h)
        xs = np.linspace(0, cx, w)
        y0 = np.clip(ys.astype(int), 0, cy - 1)
        x0 = np.clip(xs.astype(int), 0, cx - 1)
        fy = ys - y0
        fx = xs - x0
        fy = fy * fy * (3 - 2 * fy)
        fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]
        b = g[y0][:, x0 + 1]
        c = g[y0 + 1][:, x0]
        d = g[y0 + 1][:, x0 + 1]
        top = a + (b - a) * fx[None, :]
        bot = c + (d - c) * fx[None, :]
        out += amp * (top + (bot - top) * fy[:, None])
        tot += amp
        amp *= 0.5
    return out / tot


def _paper(h, w, base, rng, grain=0.018):
    n = _fbm(h, w, 6, rng, 3) - 0.5
    f = rng.random((h, w)).astype(np.float32) - 0.5
    img = np.empty((h, w, 3), np.float32)
    for k in range(3):
        img[..., k] = base[k] + n * 0.03 + f * grain
    return img


def _bezier(p0, p1, p2, p3, n=260):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def _stroke_alpha(h, w, pts, widths, rng, rough=0.35):
    """Signed-distance brush stroke with dry, bristly edges."""
    x0 = int(max(0, pts[:, 0].min() - widths.max() - 4))
    x1 = int(min(w, pts[:, 0].max() + widths.max() + 4))
    y0 = int(max(0, pts[:, 1].min() - widths.max() - 4))
    y1 = int(min(h, pts[:, 1].max() + widths.max() + 4))
    alpha = np.zeros((h, w), np.float32)
    if x1 <= x0 or y1 <= y0:
        return alpha
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dmin = np.full(yy.shape, 1e9, np.float32)
    tpar = np.zeros(yy.shape, np.float32)
    n = len(pts)
    for i in range(n):
        d = np.hypot(xx - pts[i, 0], yy - pts[i, 1]) - widths[i]
        better = d < dmin
        dmin = np.where(better, d, dmin)
        tpar = np.where(better, i / max(1, n - 1), tpar)
    # bristle streaks run along the stroke: noise indexed by (distance-from-centre, t)
    streak = _fbm(64, 64, 24, rng, 2)
    si = np.clip(((dmin + widths.max()) / (2 * widths.max()) * 63).astype(int), 0, 63)
    ti = np.clip((tpar * 8).astype(int), 0, 63)
    s = streak[si, ti]
    edge = -dmin / np.maximum(widths.max(), 1) + (s - 0.5) * rough
    a = np.clip(edge * 6.0 + 0.5, 0, 1)
    # dry-brush gaps near the end of the stroke
    a *= np.clip(1.0 - np.maximum(0, tpar - 0.75) * 3.0 * (s > 0.55), 0, 1)
    alpha[y0:y1, x0:x1] = a
    return alpha


def art_brush(w, h, seed=3, palette=None):
    """Gestural charcoal / warm-grey / ochre brushwork over a soft wash on warm paper
    (original procedural composition, different per seed)."""
    rng = np.random.default_rng(seed)
    img = _paper(h, w, (0.93, 0.915, 0.885), rng)
    n = _fbm(h, w, 3, rng, 5)
    wash = np.clip((n - 0.5) * 5.0, 0, 1) * 0.42
    wc = np.array((0.74, 0.71, 0.66), np.float32)
    img = img * (1 - wash[..., None]) + wc * wash[..., None]
    char, grey, ochre = (0.11, 0.105, 0.10), (0.46, 0.44, 0.41), (0.75, 0.56, 0.27)
    strokes = []
    for k in range(2):           # two bold sweeping charcoal strokes
        y0 = rng.uniform(0.25, 0.75)
        strokes.append(((rng.uniform(0.02, 0.15), y0), (rng.uniform(0.25, 0.45), y0 + rng.uniform(-0.45, 0.45)),
                        (rng.uniform(0.55, 0.75), y0 + rng.uniform(-0.45, 0.45)), (rng.uniform(0.85, 0.98), rng.uniform(0.2, 0.8)),
                        rng.uniform(0.035, 0.06), char))
    strokes.append(((rng.uniform(0.4, 0.6), rng.uniform(0.6, 0.9)), (rng.uniform(0.5, 0.8), rng.uniform(0.3, 0.9)),
                    (rng.uniform(0.6, 0.9), rng.uniform(0.3, 0.9)), (rng.uniform(0.8, 0.97), rng.uniform(0.5, 0.95)),
                    rng.uniform(0.03, 0.045), ochre))
    for k in range(3):           # thin calligraphic lines
        strokes.append(((rng.uniform(0.05, 0.9), rng.uniform(0.05, 0.95)), (rng.uniform(0, 1), rng.uniform(0, 1)),
                        (rng.uniform(0, 1), rng.uniform(0, 1)), (rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95)),
                        rng.uniform(0.004, 0.008), grey if k else char))
    for p0, p1, p2, p3, wd, col in strokes:
        pts = _bezier(*(np.array([p[0] * w, p[1] * h], np.float32) for p in (p0, p1, p2, p3)))
        t = np.linspace(0, 1, len(pts))
        prof = np.clip(t / 0.06, 0, 1) ** 0.5 * (0.88 + 0.12 * np.sin(t * 9.0 + seed)) * (1 - 0.55 * np.clip((t - 0.7) / 0.3, 0, 1))
        widths = (wd * w) * prof + 0.8
        a = _stroke_alpha(h, w, pts, widths.astype(np.float32), rng)
        for k in range(3):
            img[..., k] = img[..., k] * (1 - a * 0.96) + col[k] * a * 0.96
    return np.clip(img, 0, 1)


def art_fields(w, h, seed=7, bands=None):
    """Soft colour-field painting: stacked bands (default sand, sage, ochre) with brushy borders."""
    rng = np.random.default_rng(seed)
    img = _paper(h, w, (0.90, 0.875, 0.83), rng, 0.012)
    yy = np.linspace(0, 1, h)[:, None]
    n = _fbm(h, w, 5, rng, 4)
    bands = bands or [(0.08, 0.40, (0.80, 0.74, 0.63)), (0.43, 0.70, (0.60, 0.64, 0.55)), (0.73, 0.93, (0.76, 0.58, 0.33))]
    for a0, a1, col in bands:
        edge0 = a0 + (n - 0.5) * 0.05
        edge1 = a1 + (n - 0.5) * 0.05
        m = np.clip((yy - edge0) * 60, 0, 1) * np.clip((edge1 - yy) * 60, 0, 1)
        xx = np.linspace(0, 1, w)[None, :]
        m *= np.clip((xx - 0.07 - (n - 0.5) * 0.04) * 60, 0, 1) * np.clip((0.93 + (n - 0.5) * 0.04 - xx) * 60, 0, 1)
        tex = 0.92 + 0.16 * _fbm(h, w, 40, rng, 2)
        for k in range(3):
            img[..., k] = img[..., k] * (1 - m * 0.92) + col[k] * tex * m * 0.92
    return np.clip(img, 0, 1)


def art_line(w, h, seed=11):
    """Single continuous ink line drawing with a soft ochre disc."""
    rng = np.random.default_rng(seed)
    img = _paper(h, w, (0.95, 0.94, 0.915), rng, 0.008)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy, r = 0.62 * w, 0.40 * h, 0.17 * w
    disc = np.clip((r - np.hypot(xx - cx, yy - cy)) / 2.0, 0, 1) * (0.85 + 0.15 * _fbm(h, w, 30, rng, 2))
    for k, c in enumerate((0.80, 0.62, 0.36)):
        img[..., k] = img[..., k] * (1 - disc) + c * disc
    t = np.linspace(0, TAU, 1400)
    x = 0.5 + 0.28 * np.sin(t + 0.3) + 0.12 * np.sin(3 * t + 1.1) + 0.05 * np.cos(5 * t)
    y = 0.5 + 0.30 * np.cos(2 * t) * 0.8 + 0.12 * np.sin(4 * t + 0.4) + 0.04 * np.sin(7 * t)
    pts = np.stack([x * w, y * h], 1).astype(np.float32)
    ink = np.zeros((h, w), np.float32)
    lw = max(1.4, w / 420)
    for i in range(0, len(pts) - 1):
        px, py = pts[i]
        x0, x1 = int(max(0, px - 4)), int(min(w, px + 5))
        y0, y1 = int(max(0, py - 4)), int(min(h, py + 5))
        d = np.hypot(xx[y0:y1, x0:x1] - px, yy[y0:y1, x0:x1] - py)
        ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], np.clip(lw - d + 0.5, 0, 1))
    for k in range(3):
        img[..., k] = img[..., k] * (1 - ink * 0.95) + 0.08 * ink * 0.95
    return np.clip(img, 0, 1)


def to_image(name, arr):
    h, w = arr.shape[:2]
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr
    img.pixels.foreach_set(rgba[::-1].ravel())
    try:
        img.pack()
    except Exception:
        pass
    return img


# ---------------------------------------------------------------------------------- the kit
class Kit:
    """Object factory bound to a Ctx and a target collection (children of zone_bedrooms)."""

    def __init__(self, ctx, root='zone_bedrooms'):
        self.ctx = ctx
        self.root = root
        ctx.coll(root)
        self.cname = root
        self.n = 0
        self.lights = 0
        self._wrinkle = None
        self.lcoll = f'{root}_lights'
        ctx.coll(self.lcoll, root)

    def use(self, sub):
        self.cname = f'{self.root}_{sub}'
        self.ctx.coll(self.cname, self.root)
        return self

    def mat(self, m):
        return self.ctx.mat(m) if isinstance(m, str) else m

    # ---- raw objects -------------------------------------------------------------------
    def mesh(self, name, verts, faces, mat=None, loc=(0, 0, 0), rot=0.0, tilt=0.0, roll=0.0, smooth=False, uvs=None):
        """Object from local SCENE-feet verts, placed at SCENE `loc`, Euler (tilt about x, roll about
        -z, yaw `rot` about +Y)."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([(x * FT, -z * FT, y * FT) for x, y, z in verts], [], faces)
        if uvs is not None:
            uvl = me.uv_layers.new(name='UVMap')
            for poly in me.polygons:
                for li in poly.loop_indices:
                    uvl.data[li].uv = uvs[me.loops[li].vertex_index]
        me.validate()
        if smooth:
            me.shade_smooth()
        ob = bpy.data.objects.new(name, me)
        if mat is not None:
            me.materials.append(self.mat(mat))
        ob.location = ft2bl(*loc)
        ob.rotation_euler = (tilt, roll, rot)
        self.ctx.coll(self.cname).objects.link(ob)
        self.n += 1
        return ob

    def box(self, name, fr, c, size, mat, bevel=0.0, seg=3, lrot=0.0):
        ob = self.ctx.box_c(name, fr.p(*c), size, fr.r(lrot), self.mat(mat), self.cname, bevel, seg)
        self.n += 1
        return ob

    def wbox(self, name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0, seg=3):
        """World-aligned box from SCENE bounds."""
        ob = self.ctx.box(name, x0, x1, y0, y1, z0, z1, self.mat(mat), self.cname, bevel, seg)
        self.n += 1
        return ob

    def cyl(self, name, fr, c, radius, height, mat, verts=32, axis='Y', lrot=0.0):
        ob = self.ctx.cylinder(name, fr.p(*c), radius, height, self.mat(mat), self.cname, verts, axis)
        ob.rotation_euler.z += fr.r(lrot)
        self.n += 1
        return ob

    # ---- modifiers ---------------------------------------------------------------------
    @staticmethod
    def soften(ob, bevel=0.0, seg=3, sub=1, render_sub=None):
        if bevel > 0:
            m = ob.modifiers.new('Bevel', 'BEVEL')
            m.width = bevel * FT
            m.segments = seg
            m.limit_method = 'NONE'
        if sub:
            s = ob.modifiers.new('Subsurf', 'SUBSURF')
            s.levels = sub
            s.render_levels = render_sub if render_sub is not None else sub
        ob.data.shade_smooth()
        return ob

    def wrinkle(self, ob, strength=0.006, size=0.18, sub=0):
        if self._wrinkle is None:
            t = bpy.data.textures.new('Z_bedrooms_wrinkle', 'CLOUDS')
            t.noise_scale = size
            t.noise_depth = 2
            self._wrinkle = t
        if sub:
            s = ob.modifiers.new('PreSub', 'SUBSURF')
            s.levels = s.render_levels = sub
        d = ob.modifiers.new('Wrinkle', 'DISPLACE')
        d.texture = self._wrinkle
        d.texture_coords = 'GLOBAL'
        d.strength = strength
        d.mid_level = 0.5
        return ob

    @staticmethod
    def solidify(ob, thick_ft, offset=-1.0):
        m = ob.modifiers.new('Solidify', 'SOLIDIFY')
        m.thickness = thick_ft * FT
        m.offset = offset
        m.use_even_offset = True
        m.use_rim = True
        return ob

    # ---- composite primitives ----------------------------------------------------------
    def soft(self, name, fr, c, size, mat, radius=0.08, seg=3, sub=1, lrot=0.0, tilt=0.0, wrinkle=0.0):
        """Upholstered / cushioned block with soft rounded edges."""
        sx, sy, sz = size
        hx, hy, hz = sx / 2, sy / 2, sz / 2
        v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz),
             (-hx, hy, -hz), (hx, hy, -hz), (hx, hy, hz), (-hx, hy, hz)]
        f = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        v, f = _merge(v, f)
        ob = self.mesh(name, v, f, mat, fr.p(*c), fr.r(lrot), tilt)
        self.soften(ob, radius, seg, sub)
        if wrinkle:
            self.wrinkle(ob, wrinkle)
        return ob

    def pillow(self, name, fr, c, w, d, t, mat, tilt=0.0, lrot=0.0, roll=0.0, pinch=0.07, wrinkle=0.004):
        v, f = pillow_geo(w, d, t, 16, pinch)
        ob = self.mesh(name, v, f, mat, fr.p(*c), fr.r(lrot), tilt, roll, smooth=True)
        s = ob.modifiers.new('Subsurf', 'SUBSURF')
        s.levels, s.render_levels = 1, 2
        if wrinkle:
            self.wrinkle(ob, wrinkle)
        return ob

    def lathe(self, name, fr, c, profile, mat, segs=48, closed=False, smooth=True, lrot=0.0):
        v, f = lathe_geo(profile, segs, closed)
        ob = self.mesh(name, v, f, mat, fr.p(*c), fr.r(lrot), smooth=smooth)
        if smooth:
            try:
                ob.data.set_sharp_from_angle(angle=math.radians(50))
            except Exception:
                pass
        return ob

    def prism(self, name, fr, c, poly, y0, y1, mat, bevel=0.0, seg=3, sub=0, lrot=0.0):
        v, f = prism_geo(poly, y0, y1)
        ob = self.mesh(name, v, f, mat, fr.p(*c), fr.r(lrot))
        if bevel or sub:
            self.soften(ob, bevel, seg, sub)
            if not sub:
                try:
                    ob.data.set_sharp_from_angle(angle=math.radians(35))
                except Exception:
                    pass
                ob.modifiers['Bevel'].harden_normals = True
        return ob

    def drape(self, name, fr, c, W, L, top_y, r, hem_y, mat, sides='lrf', thick=0.1, folds=0.03, seed=1,
              wrinkle=0.005, step=0.09, corner_drop=0.25):
        v, f = drape_geo(W, L, top_y, r, hem_y, sides, step, folds, corner_drop, seed)
        ob = self.mesh(name, v, f, mat, fr.p(*c), fr.r(), smooth=True)
        if wrinkle:
            self.wrinkle(ob, wrinkle)
        self.solidify(ob, thick, -1.0)
        s = ob.modifiers.new('Subsurf', 'SUBSURF')
        s.levels, s.render_levels = 1, 1
        return ob

    # ---- lights ------------------------------------------------------------------------
    def point(self, x, y, z, watts, kelvin=2700, radius=0.12, name='bedroom lamp'):
        self.lights += 1
        return lighting.point_light(self.ctx, x, y, z, watts, kelvin, radius, self.lcoll, name)

    def can(self, x, z, ceil=8.0, watts=4.0, lens=None):
        """lighting.can() downlight; `lens` optionally dims the glowing lens emitter so that very
        low-power cans (daylight-dominated rooms) don't get most of their light from the lens."""
        self.lights += 1
        lo = lighting.can(self.ctx, x, z, ceil, watts, coll=self.lcoll)
        if lens is not None:
            ob = bpy.data.objects.get(f'can lens {x:.1f},{z:.1f}')
            if ob is not None:
                ob.data.materials.clear()
                ob.data.materials.append(lighting.emitter('bed_can_lens', lighting.WARM_K, lens))
        return lo

    def emitter(self, name, kelvin=3000, strength=12.0):
        return lighting.emitter(name, kelvin, strength)


# ---------------------------------------------------------------------------------- more geometry
def tube_geo(pts, r, segs=8, caps=True):
    """Round tube along a polyline of WORLD SCENE-feet points (wire hooks, contoured hanger bars).
    Parallel-transported frame so the tube never twists."""
    from mathutils import Vector
    verts, faces = [], []
    npt = len(pts)
    prev = None
    for i, p in enumerate(pts):
        p = Vector(p)
        t = (Vector(pts[min(i + 1, npt - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
        if prev is None:
            a = t.cross(Vector((1, 0, 0)))
            if a.length < 1e-3:
                a = t.cross(Vector((0, 1, 0)))
        else:
            a = prev - t * prev.dot(t)
        a.normalize()
        prev = a
        b = t.cross(a)
        for k in range(segs):
            th = TAU * k / segs
            verts.append(tuple(p + (a * math.cos(th) + b * math.sin(th)) * r))
    for i in range(npt - 1):
        for k in range(segs):
            k2 = (k + 1) % segs
            faces.append((i * segs + k, i * segs + k2, (i + 1) * segs + k2, (i + 1) * segs + k))
    if caps:
        faces.append(tuple(range(segs - 1, -1, -1)))
        faces.append(tuple((npt - 1) * segs + k for k in range(segs)))
    return _merge(verts, faces, 1e-7)


def hook_pts(pos, along, rod_y, rod_r, neck_y, n=14):
    """Wire hanger hook in the plane across the rail: a '?' wrapped over the rod (centre rod_y,
    radius rod_r) dropping to the hanger body at neck_y."""
    x0, z0 = pos
    R = rod_r + 0.014
    pts = []
    a0, a1 = math.radians(205), math.radians(-25)
    for k in range(n + 1):
        a = a0 + (a1 - a0) * k / n
        pts.append((R * math.cos(a), rod_y + R * math.sin(a)))
    start = pts[0]
    loc = [(0.0, neck_y), (start[0] * 0.6, (neck_y + start[1]) / 2 - 0.01)] + pts
    if along == 'x':
        return [(x0, y, z0 + d) for d, y in loc]
    return [(x0 + d, y, z0) for d, y in loc]


def blade_geo(L, w, lean, twist, curl, seed=1, n=10):
    """Sansevieria-style leaf blade standing up from the origin (slight V section, tapered tip)."""
    rng = random.Random(seed)
    verts, faces = [], []
    for i in range(n + 1):
        s = i / n
        y = L * s
        hw = w / 2 * (1 - s ** 2.2) * (0.75 + 0.25 * math.sin(math.pi * min(1, s * 1.4)))
        hw = max(hw, 0.004)
        off = lean * y + curl * y * y / L
        a = twist * s
        for k, u in enumerate((-1, 0, 1)):
            px = u * hw * math.cos(a)
            pz = u * hw * math.sin(a) + off
            dep = -0.025 * (1 - abs(u)) * (1 - s)
            verts.append((px + dep * math.sin(a), y, pz + dep * math.cos(a)))
    for i in range(n):
        for k in range(2):
            a, b = i * 3 + k, i * 3 + k + 1
            faces.append((a, b, b + 3, a + 3))
    return verts, faces


def snake_plant_material():
    m, new = _new_mat('Z_bedrooms_sansevieria')
    if not new:
        return m
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value = 0.42
    b.inputs['Specular IOR Level'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wv = nt.nodes.new('ShaderNodeTexWave')
    wv.wave_type = 'BANDS'
    wv.bands_direction = 'Z'
    wv.inputs['Scale'].default_value = 9.0
    wv.inputs['Distortion'].default_value = 9.0
    wv.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], wv.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = _hex('#24391f')
    ramp.color_ramp.elements[1].color = _hex('#6f8358')
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(wv.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    m.diffuse_color = _hex('#3a5232')
    return m


def import_asset(kit, aid, res='1k', keep=None, hide=None, recolor=None):
    """Import a Poly Haven model into the current collection under an Empty placed at the base
    centre of the kept parts. keep/hide: name substrings; recolor: {substring: material}."""
    from .. import assets
    from ..common import world_bbox_ft, move_to_collection
    from mathutils import Matrix
    roots = kit.ctx.link_asset(assets.model(aid, res))
    allobs = []
    st = list(roots)
    while st:
        o = st.pop()
        allobs.append(o)
        st.extend(o.children)
    kept = []
    for r in roots:
        drop = (keep and not any(k in r.name for k in keep)) or (hide and any(h in r.name for h in hide))
        if drop:
            sub = [r]
            while sub:
                o = sub.pop()
                sub.extend(o.children)
                bpy.data.objects.remove(o, do_unlink=True)
        else:
            kept.append(r)
    bpy.context.view_layer.update()
    bb = world_bbox_ft(kept)
    emp = bpy.data.objects.new(f'Z_bedrooms {aid}', None)
    emp.location = ft2bl((bb[0] + bb[1]) / 2, bb[2], (bb[4] + bb[5]) / 2)
    kit.ctx.coll(kit.cname).objects.link(emp)
    inv = Matrix.Translation(emp.location).inverted()
    for r in kept:
        r.parent = emp
        r.matrix_parent_inverse = inv
    move_to_collection(kept, kit.ctx.coll(kit.cname))
    if recolor:
        st = list(kept)
        while st:
            o = st.pop()
            st.extend(o.children)
            if o.type == 'MESH':
                for sub_name, mat in recolor.items():
                    if sub_name in o.name:
                        o.data.materials.clear()
                        o.data.materials.append(mat)
    kit.n += len(kept)
    return emp, bb


def duplicate_tree(kit, root):
    """Linked duplicate of an Empty-rooted asset hierarchy (shares mesh data)."""
    new_root = root.copy()
    kit.ctx.coll(kit.cname).objects.link(new_root)
    st = [(root, new_root)]
    while st:
        src, dst = st.pop()
        for ch in src.children:
            c = ch.copy()
            kit.ctx.coll(kit.cname).objects.link(c)
            c.parent = dst
            c.matrix_parent_inverse = ch.matrix_parent_inverse.copy()
            st.append((ch, c))
    return new_root
