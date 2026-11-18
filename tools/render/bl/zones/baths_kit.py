"""Parametric bathroom fixture kit for the `baths` zone (runs inside Blender).

Everything is in SCENE feet (x east, y up, z south). Fixtures are placed in a wall `Frame`:
u = distance out from the wall face (into the room), v = lateral position along the wall
(the user's right when facing the wall is +v), y = height.

Soft/organic porcelain (WCs, basins, tub) is built from superellipse lofts with tight support
rings so silhouettes stay crisp under smooth shading without subdivision.
"""
import math

import bmesh
import bpy

from .. import lighting
from ..common import FT, ft2bl, move_to_collection, world_bbox_ft

BLACK = 'black_metal'
MIRROR_K = 6000       # LED mirror colour (see CAN_K in baths.py)
CERAMIC = 'ceramic_white'


# ----------------------------------------------------------------------------- materials
def zmat(name, build):
    """Zone-local material `Z_baths_<name>` built once by `build(material)`."""
    full = f'Z_baths_{name}'
    m = bpy.data.materials.get(full)
    if m is None:
        m = bpy.data.materials.new(full)
        m.use_nodes = True
        build(m)
    return m


def _principled(m):
    return m.node_tree.nodes.get('Principled BSDF')


def towel_band_material(name, rgb, band=None):
    """Cotton terry with an optional woven dobby border band between world heights band=(y0, y1) ft:
    slightly deeper tone + fine horizontal ribs, the detail that makes a hung towel read as cloth."""
    def build(m):
        nt = m.node_tree
        b = _principled(m)
        b.inputs['Roughness'].default_value = 1.0
        for k, v in (('Sheen Weight', 0.9), ('Sheen Roughness', 0.45)):
            if k in b.inputs:
                b.inputs[k].default_value = v
        if 'Sheen Tint' in b.inputs:
            b.inputs['Sheen Tint'].default_value = tuple(min(1.0, 0.35 + c) for c in rgb) + (1,)
        # world-space pile (loops ~3 mm) and soft tufting tone so every towel is not one flat value
        wpos = nt.nodes.new('ShaderNodeNewGeometry')
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 330.0
        noise.inputs['Detail'].default_value = 3.0
        noise.inputs['Roughness'].default_value = 0.6
        nt.links.new(wpos.outputs['Position'], noise.inputs['Vector'])
        tone = nt.nodes.new('ShaderNodeTexNoise')
        tone.inputs['Scale'].default_value = 28.0
        tone.inputs['Detail'].default_value = 2.0
        nt.links.new(wpos.outputs['Position'], tone.inputs['Vector'])
        tmap = nt.nodes.new('ShaderNodeMapRange')
        tmap.inputs['From Min'].default_value = 0.3
        tmap.inputs['From Max'].default_value = 0.7
        tmap.inputs['To Min'].default_value = 0.93
        tmap.inputs['To Max'].default_value = 1.03
        nt.links.new(tone.outputs['Fac'], tmap.inputs['Value'])
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.6
        bump.inputs['Distance'].default_value = 0.002
        rgbn = nt.nodes.new('ShaderNodeRGB')
        rgbn.outputs[0].default_value = rgb + (1,)
        base = nt.nodes.new('ShaderNodeVectorMath')
        base.operation = 'SCALE'
        nt.links.new(rgbn.outputs[0], base.inputs[0])
        nt.links.new(tmap.outputs['Result'], base.inputs['Scale'])
        if band is None:
            nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
            nt.links.new(base.outputs[0], b.inputs['Base Color'])
        else:
            geo = nt.nodes.new('ShaderNodeNewGeometry')
            sep = nt.nodes.new('ShaderNodeSeparateXYZ')
            nt.links.new(geo.outputs['Position'], sep.inputs[0])
            gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'
            gt.inputs[1].default_value = band[0] * FT
            lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'
            lt.inputs[1].default_value = band[1] * FT
            nt.links.new(sep.outputs['Z'], gt.inputs[0])
            nt.links.new(sep.outputs['Z'], lt.inputs[0])
            mask = nt.nodes.new('ShaderNodeMath'); mask.operation = 'MULTIPLY'
            nt.links.new(gt.outputs[0], mask.inputs[0])
            nt.links.new(lt.outputs[0], mask.inputs[1])
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
            nt.links.new(mask.outputs[0], mix.inputs['Factor'])
            nt.links.new(base.outputs[0], mix.inputs['A'])
            mix.inputs['B'].default_value = tuple(c * 0.9 for c in rgb) + (1,)
            nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
            # fine horizontal ribs inside the band
            wave = nt.nodes.new('ShaderNodeTexWave')
            wave.wave_type = 'BANDS'
            wave.bands_direction = 'Z'
            wave.inputs['Scale'].default_value = 140.0
            rib = nt.nodes.new('ShaderNodeMath'); rib.operation = 'MULTIPLY'
            nt.links.new(wave.outputs['Fac'], rib.inputs[0])
            nt.links.new(mask.outputs[0], rib.inputs[1])
            h = nt.nodes.new('ShaderNodeMath'); h.operation = 'MULTIPLY_ADD'
            nt.links.new(rib.outputs[0], h.inputs[0])
            h.inputs[1].default_value = 0.35
            nt.links.new(noise.outputs['Fac'], h.inputs[2])
            nt.links.new(h.outputs[0], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
        m.diffuse_color = rgb + (1,)
    return zmat(name, build)


WHITE_TOWEL = (0.80, 0.785, 0.75)
GREY_TOWEL = (0.30, 0.29, 0.275)
SAGE_TOWEL = (0.47, 0.52, 0.43)
OAT_TOWEL = (0.60, 0.56, 0.49)
CHARCOAL_TOWEL = (0.13, 0.125, 0.117)


def matte_material(name, rgb, rough=0.55, metal=0.0):
    def build(m):
        b = _principled(m)
        b.inputs['Base Color'].default_value = rgb + (1,)
        b.inputs['Roughness'].default_value = rough
        b.inputs['Metallic'].default_value = metal
        m.diffuse_color = rgb + (1,)
    return zmat(name, build)


def fluted_material(ctx):
    """Library `tile_fluted_black` with its normal-mapped flutes unplugged: the flutes are real
    geometry here, so only the colour / coat / tile variation of the library material is kept."""
    m = bpy.data.materials.get('Z_baths_fluted_black')
    if m is not None:
        return m
    m = ctx.mat('tile_fluted_black').copy()
    m.name = 'Z_baths_fluted_black'
    if m.node_tree:
        for n in m.node_tree.nodes:
            if n.type == 'BSDF_PRINCIPLED':
                for key in ('Normal', 'Coat Normal'):
                    if key in n.inputs:
                        for l in list(n.inputs[key].links):
                            m.node_tree.links.remove(l)
    return m


def porcelain_material(ctx):
    """Z_baths_porcelain: large-format 24x48in (stack bond) honed porcelain with a vein-cut
    limestone / travertine look like the 1077 W McKinley baths: warm white, soft horizontal
    bedding striations, sparse intermittent hairlines, slight tone shift per tile, 1/16in grout.
    Replaces the library's tile_wall_porcelain in the baths, whose bold S-curve veins repeat tile
    to tile and read artificial at 5-8 ft. Built with the library's graph helper (world-space
    planar mapping, no UVs); falls back to the library key if anything fails."""
    name = 'Z_baths_porcelain'
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    g = None
    try:
        from .. import materials_pbr as P
        IN = 0.0254
        g = P._G('tile_wall_porcelain')
        g.m.name = name
        a, b, A, B = g.planar()
        tid, d, _, _ = P._grid(g, a, b, 48 * IN, 24 * IN)
        _, rc = g.white(tid)
        r0, r1, r2 = g.sep(rc)
        # every tile is cut from a different part of the slab
        qx, qy, qz = g.mad(r0, 7.0, a), g.mad(r1, 5.0, b), g.mul(r2, 3.0)
        n1, _ = g.noise(g.vec(g.mul(qx, 0.9), g.mul(qy, 15.0), qz), 1.0, detail=6.0, rough=0.62, distortion=0.35)
        n2, _ = g.noise(g.vec(g.mul(qx, 0.45), g.mul(qy, 3.6), g.add(qz, 3.0)), 1.0, detail=3.0, rough=0.5)
        n3, _ = g.noise(g.vec(g.mul(qx, 0.6), g.mul(qy, 5.5), g.add(qz, 7.0)), 1.0, detail=4.0, rough=0.55,
                        distortion=0.5)
        mk, _ = g.noise(g.vec(g.mul(qx, 1.3), g.mul(qy, 2.0), g.add(qz, 11.0)), 1.0, detail=1.0)
        speck, _ = g.noise(g.frame()['P'], 420.0, detail=1.0)
        base = P._hexlin('#e9e6e0')
        beige = P._hexlin('#d9d1c4')
        hair = P._hexlin('#bdb5a9')
        col = g.vscale(base, g.remap(n2, 0.3, 0.7, 0.965, 1.02))
        col = g.vscale(col, g.remap(n1, 0.25, 0.75, 0.978, 1.018))
        col = g.cmix(col, beige, g.mul(g.ss(n1, 0.56, 0.76), 0.42))
        line = g.sub(1.0, g.ss(g.absf(g.sub(n3, 0.5)), 0.0, 0.008))
        line = g.mul(line, g.ss(mk, 0.52, 0.68))
        col = g.cmix(col, hair, g.mul(line, 0.3))
        col = g.vscale(col, g.mul(g.remap(r2, 0.0, 1.0, 0.986, 1.012), g.remap(speck, 0.3, 0.7, 0.988, 1.01)))
        grout = g.sub(1.0, g.ss(d, 0.0007, 0.001))
        col = g.cmix(col, P._hexlin('#d4d0c9'), grout)
        rough = g.lerp(g.add(0.27, g.mul(g.sub(n2, 0.5), 0.1)), 0.8, grout)
        height = g.add(g.ss(d, 0.0006, 0.0022), g.mul(n1, 0.04))
        nrm = g.normal(height=height, dist=0.0008)
        return g.finish(g.bsdf(col, rough, 0.0, nrm))
    except Exception as e:
        print('[baths] porcelain material fallback:', repr(e))
        if g is not None and g.m is not None:
            bpy.data.materials.remove(g.m)
        return ctx.mat('tile_wall_porcelain')


def glass_edge_material(ctx):
    """Green-tinted edge of 3/8in tempered glass (thin-glass shader, never refractive)."""
    m = bpy.data.materials.get('Z_baths_glass_edge')
    if m is not None:
        return m
    try:
        from .. import materials
        return materials.thin_glass('Z_baths_glass_edge', tint=(0.42, 0.62, 0.55))
    except Exception:
        return ctx.mat('glass_clear')


def as_mat(ctx, mat):
    if mat is None or isinstance(mat, bpy.types.Material):
        return mat
    return ctx.mat(mat)


# ------------------------------------------------------------------------------- frames
class Frame:
    """Wall frame: origin (ox, oz) on the finished wall face, d = unit plan direction out of
    the wall. v grows to the user's right when they face the wall."""

    def __init__(self, ox, oz, dx, dz):
        self.ox, self.oz, self.dx, self.dz = ox, oz, dx, dz
        self.lx, self.lz = dz, -dx
        self.rot = math.atan2(-self.lz, self.lx)

    def w(self, u, v):
        return (self.ox + u * self.dx + v * self.lx, self.oz + u * self.dz + v * self.lz)

    def axis(self, a):
        if a == 'y':
            return 'Y'
        vec = (self.dx, self.dz) if a == 'u' else (self.lx, self.lz)
        return 'X' if abs(vec[0]) > 0.5 else 'Z'


def mesh_ft(ctx, name, verts, faces, mat=None, coll='zone_baths', smooth=False, sharp_deg=None, recalc=False):
    """Mesh object from SCENE-feet vertices (object origin at the world origin)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(ft2bl(*p)) for p in verts], [], faces)
    me.validate()
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    if smooth:
        me.shade_smooth()
        if sharp_deg:
            try:
                me.set_sharp_from_angle(angle=math.radians(sharp_deg))
            except Exception:
                pass
    ob = bpy.data.objects.new(name, me)
    if mat is not None:
        me.materials.append(as_mat(ctx, mat))
    ctx.coll(coll).objects.link(ob)
    return ob


def fbox(ctx, f, name, u0, u1, v0, v1, y0, y1, mat, coll, bevel=0.0, seg=3):
    x, z = f.w((u0 + u1) / 2, (v0 + v1) / 2)
    ob = ctx.box_c(name, (x, (y0 + y1) / 2, z), (abs(v1 - v0), abs(y1 - y0), abs(u1 - u0)), f.rot,
                   None, coll, bevel, seg)
    if mat is not None:
        ob.data.materials.append(as_mat(ctx, mat))
    return ob


def fcyl(ctx, f, name, u, v, y, r, h, axis, mat, coll, verts=32):
    x, z = f.w(u, v)
    ob = ctx.cylinder(name, (x, y, z), r, h, None, coll, verts=verts, axis=f.axis(axis))
    if mat is not None:
        ob.data.materials.append(as_mat(ctx, mat))
    return ob


def box(ctx, name, x0, x1, y0, y1, z0, z1, mat, coll, bevel=0.0, seg=3):
    ob = ctx.box(name, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1),
                 None, coll, bevel, seg)
    if mat is not None:
        ob.data.materials.append(as_mat(ctx, mat))
    return ob


# ----------------------------------------------------------------------- superellipse loft
def R(y, u0, u1, b, nf=2.0, nb=None, vc=0.0):
    """Loft ring at height y spanning u0..u1 (depth) and vc +/- b (lateral). nf / nb are the
    superellipse exponents of the front (u1) and back (u0) halves (2 = ellipse, big = square)."""
    return (y, u0, u1, b, nf, nb if nb is not None else nf, vc)


def _ring(r, seg):
    y, u0, u1, b, nf, nb, vc = r
    uc, a = (u0 + u1) / 2, (u1 - u0) / 2
    out = []
    for k in range(seg):
        t = 2 * math.pi * k / seg
        c, s = math.cos(t), math.sin(t)
        n = nf if c >= 0 else nb
        e = 2.0 / n
        out.append((uc + a * math.copysign(abs(c) ** e, c), vc + b * math.copysign(abs(s) ** e, s), y))
    return out


def loft(ctx, f, name, rings, mat, coll, seg=64, cap0=True, cap1=True, sharp_deg=50):
    verts, faces = [], []
    for r in rings:
        for (u, v, y) in _ring(r, seg):
            x, z = f.w(u, v)
            verts.append((x, y, z))
    for i in range(len(rings) - 1):
        for k in range(seg):
            a, b = i * seg + k, i * seg + (k + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    if cap0:
        faces.append(tuple(reversed(range(seg))))
    if cap1:
        last = (len(rings) - 1) * seg
        faces.append(tuple(range(last, last + seg)))
    return mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True, sharp_deg=sharp_deg, recalc=cap0 and cap1)


def wall_prism(ctx, f, name, pts_vy, u0, u1, mat, coll, smooth=False):
    """Prism standing off a wall: convex polygon in the wall plane (v, y), extruded u0..u1."""
    n = len(pts_vy)
    verts = []
    for u in (u0, u1):
        for v, y in pts_vy:
            x, z = f.w(u, v)
            verts.append((x, y, z))
    faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    faces += [(k, (k + 1) % n, (k + 1) % n + n, k + n) for k in range(n)]
    return mesh_ft(ctx, name, verts, faces, mat, coll, smooth=smooth, sharp_deg=30, recalc=True)


def stadium_vy(vc, yc, w, h, seg=24):
    """Pill (stadium) outline in the wall plane, vertical: width w, height h."""
    r = w / 2
    pts = []
    for k in range(seg + 1):                     # top arc
        t = math.pi * k / seg
        pts.append((vc + r * math.cos(t), yc + h / 2 - r + r * math.sin(t)))
    for k in range(seg + 1):                     # bottom arc
        t = math.pi + math.pi * k / seg
        pts.append((vc + r * math.cos(t), yc - h / 2 + r + r * math.sin(t)))
    return pts


def circle_vy(vc, yc, r, seg=64):
    return [(vc + r * math.cos(2 * math.pi * k / seg), yc + r * math.sin(2 * math.pi * k / seg)) for k in range(seg)]


def annulus(ctx, f, name, u, outer, inner, mat, coll):
    """Flat ring in the wall plane at depth u between two outlines with equal point counts."""
    n = len(outer)
    verts = []
    for v, y in list(outer) + list(inner):
        x, z = f.w(u, v)
        verts.append((x, y, z))
    faces = [(k, (k + 1) % n, (k + 1) % n + n, k + n) for k in range(n)]
    return mesh_ft(ctx, name, verts, faces, mat, coll)


def bool_cut(ob, cutter, solver='EXACT'):
    m = ob.modifiers.new('cut ' + cutter.name[:20], 'BOOLEAN')
    m.operation = 'DIFFERENCE'
    try:
        m.solver = solver
    except TypeError:
        pass
    m.object = cutter
    cutter.hide_render = True
    cutter.hide_viewport = True
    cutter.display_type = 'WIRE'
    return m


# ---------------------------------------------------------------------------- tile skins
def skin(ctx, name, axis, plane0, plane1, a0, a1, y0, y1, mat, coll, holes=()):
    """Wall tile skin: a slab between plane0..plane1 on `axis` ('x' or 'z'), spanning a0..a1 on
    the other plan axis and y0..y1, with rectangular holes [(a0, a1, y0, y1), ...]."""
    cuts = sorted({a0, a1} | {h[0] for h in holes} | {h[1] for h in holes})
    cuts = [c for c in cuts if a0 <= c <= a1]
    pieces = []
    for s0, s1 in zip(cuts, cuts[1:]):
        if s1 - s0 < 1e-4:
            continue
        mid = (s0 + s1) / 2
        spans = [(y0, y1)]
        for h in holes:
            if h[0] <= mid <= h[1]:
                nxt = []
                for (p, q) in spans:
                    if h[3] <= p or h[2] >= q:
                        nxt.append((p, q))
                        continue
                    if h[2] > p:
                        nxt.append((p, h[2]))
                    if h[3] < q:
                        nxt.append((h[3], q))
                spans = nxt
        for (p, q) in spans:
            if q - p < 1e-4:
                continue
            nm = f'{name} {len(pieces)}'
            if axis == 'x':
                pieces.append(box(ctx, nm, plane0, plane1, p, q, s0, s1, mat, coll))
            else:
                pieces.append(box(ctx, nm, s0, s1, p, q, plane0, plane1, mat, coll))
    return pieces


def fluted_wall(ctx, name, axis, plane, sign, a0, a1, y0, y1, base, depth, pitch, mat, coll, seg=8):
    """Corrugated (fluted) tile surface on a wall. `plane` = wall face coordinate on `axis`,
    `sign` = +1/-1 direction into the room. Ribs run vertically; crest at plane + sign*(base+depth)."""
    n = max(1, int(round((a1 - a0) / pitch)))
    p = (a1 - a0) / n
    prof = []
    for i in range(n):
        for k in range(seg):
            s = k / seg
            prof.append((a0 + p * (i + s), base + depth * (math.sin(math.pi * s) ** 0.55)))
    prof.append((a1, base))
    verts = []
    for y in (y0, y1):
        for a, d in prof:
            c = plane + sign * d
            verts.append((c, y, a) if axis == 'x' else (a, y, c))
    m = len(prof)
    faces = [(k, k + 1, k + 1 + m, k + m) for k in range(m - 1)]
    return mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True, sharp_deg=70)


# --------------------------------------------------------------------------- fixtures
def wall_hung_wc(ctx, f, coll, name='WC', mat=CERAMIC):
    """Wall-hung WC: pan 21in deep x 14.4in wide, rim at 15.6in, seat+lid closed (top 16.8in)."""
    rings = [
        R(0.90, 0.10, 1.30, 0.34, 2.3, 7),
        R(0.925, 0.04, 1.50, 0.46, 2.3, 7),
        R(0.98, 0.012, 1.62, 0.54, 2.3, 7),
        R(1.08, 0.0, 1.71, 0.59, 2.3, 7),
        R(1.20, 0.0, 1.745, 0.60, 2.3, 7),
        R(1.275, 0.0, 1.75, 0.60, 2.3, 7),
        R(1.293, 0.004, 1.74, 0.592, 2.3, 7),
        R(1.30, 0.012, 1.725, 0.578, 2.3, 7),
    ]
    pan = loft(ctx, f, f'{name} pan', rings, mat, coll)
    lid = seat_lid(ctx, f, coll, name, 0.19, 1.765, 0.60, 1.30, mat)
    return [pan, lid]


def seat_lid(ctx, f, coll, name, u0, u1, b, y0, mat):
    rings = [
        R(y0 + 0.002, u0 + 0.03, u1 - 0.03, b - 0.03, 2.3, 4),
        R(y0 + 0.012, u0, u1, b, 2.3, 4),
        R(y0 + 0.032, u0, u1, b, 2.3, 4),
        R(y0 + 0.039, u0 + 0.008, u1 - 0.012, b - 0.012, 2.3, 4),     # seat / lid seam
        R(y0 + 0.047, u0, u1 - 0.002, b - 0.002, 2.3, 4),
        R(y0 + 0.080, u0, u1 - 0.002, b - 0.002, 2.3, 4),
        R(y0 + 0.094, u0 + 0.03, u1 - 0.035, b - 0.035, 2.3, 4),
        R(y0 + 0.098, u0 + 0.07, u1 - 0.075, b - 0.075, 2.3, 4),
    ]
    return loft(ctx, f, f'{name} seat+lid', rings, mat, coll)


def skirted_wc(ctx, f, coll, name='WC', mat=CERAMIC, floor=0.028, length=2.25):
    """One-piece skirted WC: `length` ft deep overall (27in default), 15in wide, seat ~16.5in,
    tank top 28.5in."""
    k = length / 2.36

    def S(y, u0, u1, b):
        return R(y, u0 * k, u1 * k, b, 2.4, 4)
    rings = [
        S(floor, 0.56, 2.00, 0.43),
        S(floor + 0.012, 0.545, 2.02, 0.445),
        S(0.45, 0.52, 2.12, 0.50),
        S(0.85, 0.50, 2.25, 0.57),
        S(1.15, 0.50, 2.32, 0.605),
        S(1.255, 0.50, 2.33, 0.61),
        S(1.28, 0.505, 2.322, 0.603),
        S(1.29, 0.515, 2.305, 0.588),
    ]
    body = loft(ctx, f, f'{name} body', rings, mat, coll)
    tank = loft(ctx, f, f'{name} tank', [
        R(1.10, 0.02, 0.66 * k, 0.55, 6, 6),
        R(2.28, 0.02, 0.66 * k, 0.55, 6, 6),
        R(2.335, 0.03, 0.65 * k, 0.54, 6, 6),
        R(2.36, 0.055, 0.625 * k, 0.515, 6, 6),
        R(2.37, 0.09, 0.59 * k, 0.48, 6, 6),
    ], mat, coll)
    lid = seat_lid(ctx, f, coll, name, 0.70 * k, 2.36 * k, 0.60, 1.29, mat)
    btn = fcyl(ctx, f, f'{name} flush button', 0.34 * k, 0.0, 2.375, 0.075, 0.012, 'y', 'chrome', coll)
    return [body, tank, lid, btn]


def flush_plate(ctx, f, coll, v, y, name='flush plate'):
    """Matte black dual-flush actuator plate (9.75 x 6.5in) on the wall."""
    pl = fbox(ctx, f, name, 0.0, 0.035, v - 0.41, v + 0.41, y - 0.27, y + 0.27, BLACK, coll, bevel=0.008)
    fbox(ctx, f, name + ' btn L', 0.035, 0.042, v - 0.36, v - 0.02, y - 0.21, y + 0.21, BLACK, coll, bevel=0.004)
    fbox(ctx, f, name + ' btn R', 0.035, 0.042, v + 0.02, v + 0.36, y - 0.21, y + 0.21, BLACK, coll, bevel=0.004)
    return pl


def undermount_bowl(ctx, f, coll, name, uc, vc, y_top, a=0.5, b=0.72, depth=0.46):
    """Undermount basin (open top) hanging under a counter of underside y_top."""
    rings = [
        R(y_top + 0.004, uc - a, uc + a, b, 5, 5, vc),
        R(y_top - 0.04, uc - a + 0.01, uc + a - 0.01, b - 0.01, 5, 5, vc),
        R(y_top - depth * 0.6, uc - a + 0.05, uc + a - 0.05, b - 0.06, 4.2, 4.2, vc),
        R(y_top - depth * 0.92, uc - a + 0.10, uc + a - 0.10, b - 0.13, 3.6, 3.6, vc),
        R(y_top - depth, uc - a + 0.17, uc + a - 0.17, b - 0.21, 3.2, 3.2, vc),
    ]
    bowl = loft(ctx, f, name, rings, CERAMIC, coll, cap0=False, cap1=True, sharp_deg=None)
    drain = fcyl(ctx, f, name + ' drain', uc, vc, y_top - depth + 0.004, 0.065, 0.008, 'y', 'chrome', coll)
    return bowl, drain


def sink_cutter(ctx, f, coll, name, uc, vc, y0, y1, a, b, n=5):
    return loft(ctx, f, name, [R(y0, uc - a, uc + a, b, n, n, vc), R(y1, uc - a, uc + a, b, n, n, vc)],
                None, coll, sharp_deg=None)


def vessel_sink(ctx, f, coll, name, uc, vc, y0, a=0.5, b=0.66, h=0.37, wall=0.028):
    """Thin-walled rectangular vessel basin standing on the counter at y0."""
    rings = [
        R(y0, uc - a + 0.05, uc + a - 0.05, b - 0.05, 5, 5, vc),
        R(y0 + 0.02, uc - a + 0.015, uc + a - 0.015, b - 0.015, 5, 5, vc),
        R(y0 + 0.08, uc - a, uc + a, b, 5, 5, vc),
        R(y0 + h - 0.012, uc - a, uc + a, b, 5, 5, vc),
        R(y0 + h, uc - a + 0.008, uc + a - 0.008, b - 0.008, 5, 5, vc),
        R(y0 + h, uc - a + wall - 0.006, uc + a - wall + 0.006, b - wall + 0.006, 5, 5, vc),
        R(y0 + h - 0.012, uc - a + wall, uc + a - wall, b - wall, 5, 5, vc),
        R(y0 + 0.14, uc - a + wall + 0.01, uc + a - wall - 0.01, b - wall - 0.01, 4.5, 4.5, vc),
        R(y0 + 0.06, uc - a + wall + 0.08, uc + a - wall - 0.08, b - wall - 0.09, 3.6, 3.6, vc),
        R(y0 + 0.045, uc - a + wall + 0.17, uc + a - wall - 0.17, b - wall - 0.19, 3.0, 3.0, vc),
    ]
    vs = loft(ctx, f, name, rings, CERAMIC, coll)
    fcyl(ctx, f, name + ' drain', uc, vc, y0 + 0.047, 0.06, 0.006, 'y', BLACK, coll)
    return vs


def wall_faucet(ctx, f, coll, name, v, y, reach=0.62, lever_dv=0.0):
    """Wall-mount matte black basin spout (round plate + 3/4in tube) with a lever above it."""
    parts = [fcyl(ctx, f, name + ' plate', 0.012, v, y, 0.105, 0.024, 'u', BLACK, coll)]
    parts.append(fcyl(ctx, f, name + ' spout', 0.02 + reach / 2, v, y, 0.034, reach, 'u', BLACK, coll))
    parts.append(fcyl(ctx, f, name + ' aerator', reach - 0.01, v, y - 0.035, 0.03, 0.012, 'y', BLACK, coll))
    yl = y + 0.33
    parts.append(fcyl(ctx, f, name + ' lever plate', 0.012, v + lever_dv, yl, 0.08, 0.024, 'u', BLACK, coll))
    parts.append(fcyl(ctx, f, name + ' lever hub', 0.06, v + lever_dv, yl, 0.035, 0.08, 'u', BLACK, coll))
    parts.append(fbox(ctx, f, name + ' lever', 0.085, 0.11, v + lever_dv - 0.016, v + lever_dv + 0.016,
                      yl - 0.01, yl + 0.20, BLACK, coll, bevel=0.006))
    return parts


def deck_faucet(ctx, f, coll, name, u, v, y_deck, height=0.75, reach=0.48, r=0.04):
    """Single-hole matte black faucet: round column, horizontal spout, side lever."""
    parts = [fcyl(ctx, f, name + ' base', u, v, y_deck + 0.01, r + 0.022, 0.02, 'y', BLACK, coll)]
    parts.append(fcyl(ctx, f, name + ' column', u, v, y_deck + height / 2, r, height, 'y', BLACK, coll))
    yt = y_deck + height - r
    parts.append(fcyl(ctx, f, name + ' spout', u + reach / 2, v, yt, r * 0.8, reach, 'u', BLACK, coll))
    parts.append(fcyl(ctx, f, name + ' cap', u, v, y_deck + height, r, 0.012, 'y', BLACK, coll))
    parts.append(fcyl(ctx, f, name + ' aerator', u + reach - 0.03, v, yt - r * 0.8, r * 0.7, 0.015, 'y', BLACK, coll))
    parts.append(fcyl(ctx, f, name + ' lever', u, v + r + 0.07, y_deck + height * 0.55, 0.018, 0.16, 'v', BLACK, coll))
    return parts


def valve_trim(ctx, f, coll, name, v, y, r=0.27):
    """Round thermostatic valve trim with a lever (shower / tub)."""
    fcyl(ctx, f, name + ' plate', 0.012, v, y, r, 0.024, 'u', BLACK, coll, verts=48)
    fcyl(ctx, f, name + ' hub', 0.06, v, y, 0.06, 0.08, 'u', BLACK, coll)
    fbox(ctx, f, name + ' lever', 0.09, 0.115, v - 0.02, v + 0.02, y - 0.02, y + 0.26, BLACK, coll, bevel=0.007)


def rain_head_ceiling(ctx, coll, name, x, z, ceil=8.0, drop=0.45, size=0.83):
    fl = ctx.cylinder(name + ' flange', (x, ceil - 0.01, z), 0.1, 0.02, None, coll, verts=32)
    fl.data.materials.append(ctx.mat(BLACK))
    arm = ctx.cylinder(name + ' arm', (x, ceil - drop / 2, z), 0.035, drop, None, coll, verts=24)
    arm.data.materials.append(ctx.mat(BLACK))
    head = box(ctx, name + ' head', x - size / 2, x + size / 2, ceil - drop - 0.035, ceil - drop, z - size / 2, z + size / 2,
               BLACK, coll, bevel=0.01)
    box(ctx, name + ' nozzle face', x - size / 2 + 0.05, x + size / 2 - 0.05, ceil - drop - 0.037,
               ceil - drop - 0.034, z - size / 2 + 0.05, z + size / 2 - 0.05, matte_material('nozzles', (0.05, 0.05, 0.05), 0.7),
               coll)
    return head


def rain_head_wall(ctx, f, coll, name, v, y, arm=1.25, dia=0.75):
    fcyl(ctx, f, name + ' flange', 0.012, v, y, 0.1, 0.024, 'u', BLACK, coll)
    fcyl(ctx, f, name + ' arm', arm / 2, v, y, 0.035, arm, 'u', BLACK, coll)
    fcyl(ctx, f, name + ' drop', arm, v, y - 0.06, 0.035, 0.12, 'y', BLACK, coll)
    fcyl(ctx, f, name + ' head', arm, v, y - 0.14, dia / 2, 0.035, 'y', BLACK, coll, verts=64)


def hand_shower(ctx, f, coll, name, v, y0, y1, outlet_y):
    """Slide bar with a stick hand shower, wall outlet elbow and a drooping black hose."""
    ub = 0.13
    fcyl(ctx, f, name + ' bar', ub, v, (y0 + y1) / 2, 0.028, y1 - y0, 'y', BLACK, coll)
    for yy in (y0, y1):
        fcyl(ctx, f, name + ' bracket', ub / 2, v, yy, 0.03, ub, 'u', BLACK, coll)
        fcyl(ctx, f, name + ' rose', 0.01, v, yy, 0.06, 0.02, 'u', BLACK, coll)
    yh = y1 - 0.55
    fbox(ctx, f, name + ' holder', ub - 0.04, ub + 0.08, v - 0.05, v + 0.05, yh - 0.06, yh + 0.06, BLACK, coll, bevel=0.01)
    fcyl(ctx, f, name + ' handle', ub + 0.12, v, yh + 0.12, 0.045, 0.62, 'y', BLACK, coll)
    fcyl(ctx, f, name + ' head', ub + 0.12, v, yh + 0.47, 0.055, 0.14, 'y', BLACK, coll)
    fcyl(ctx, f, name + ' outlet', 0.04, v, outlet_y, 0.045, 0.08, 'u', BLACK, coll)
    # hose: from the outlet down in a soft loop and up into the handle bottom
    pts = [(0.08, outlet_y), (0.16, outlet_y - 0.35), (0.22, outlet_y - 0.75), (0.25, outlet_y - 0.85),
           (0.26, outlet_y - 0.55), (ub + 0.12, yh - 0.35), (ub + 0.12, yh - 0.19)]
    cu = bpy.data.curves.new(name + ' hose', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = 0.022 * FT
    cu.bevel_resolution = 3
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for p, (u, y) in zip(sp.points, pts):
        x, z = f.w(u, v + 0.02)
        co = ft2bl(x, y, z)
        p.co = (co.x, co.y, co.z, 1.0)
    sp.use_endpoint_u = True
    sp.order_u = 4
    sp.resolution_u = 12
    ob = bpy.data.objects.new(name + ' hose', cu)
    cu.materials.append(ctx.mat(BLACK))
    ctx.coll(coll).objects.link(ob)
    return ob


def linear_drain(ctx, coll, name, axis, a0, a1, c, y):
    """Matte black linear drain grate flush with the floor at y (axis = run direction)."""
    if axis == 'x':
        box(ctx, name, a0, a1, y - 0.01, y + 0.003, c - 0.06, c + 0.06, 'stainless', coll, bevel=0.004)
        box(ctx, name + ' grate', a0 + 0.03, a1 - 0.03, y + 0.003, y + 0.004, c - 0.04, c + 0.04, BLACK, coll)
    else:
        box(ctx, name, c - 0.06, c + 0.06, y - 0.01, y + 0.003, a0, a1, 'stainless', coll, bevel=0.004)
        box(ctx, name + ' grate', c - 0.04, c + 0.04, y + 0.003, y + 0.004, a0 + 0.03, a1 - 0.03, BLACK, coll)


def glass_panel(ctx, coll, name, a, b, y0, y1, t=0.031):
    """Frameless 3/8in glass panel from plan point a=(x,z) to b=(x,z). Faces: thin-glass, edges
    green-tinted."""
    (ax, az), (bx, bz) = a, b
    L = math.hypot(bx - ax, bz - az)
    rot = math.atan2(-(bz - az), bx - ax)
    ob = ctx.box_c(name, ((ax + bx) / 2, (y0 + y1) / 2, (az + bz) / 2), (L, y1 - y0, t), rot, None, coll)
    ob.data.materials.append(ctx.mat('glass_clear'))
    ob.data.materials.append(glass_edge_material(ctx))
    for i, p in enumerate(ob.data.polygons):
        p.material_index = 0 if i in (2, 4) else 1
    ob.visible_shadow = True
    return ob


def clamp(ctx, coll, name, x, y, z, along, size=(0.16, 0.10, 0.075)):
    """Small black glass clamp / hinge block centred on the glass (along = 'x' or 'z' run)."""
    l, h, d = size
    if along == 'x':
        return box(ctx, name, x - l / 2, x + l / 2, y - h / 2, y + h / 2, z - d / 2, z + d / 2, BLACK, coll, bevel=0.008)
    return box(ctx, name, x - d / 2, x + d / 2, y - h / 2, y + h / 2, z - l / 2, z + l / 2, BLACK, coll, bevel=0.008)


def towel_warmer(ctx, f, coll, name, v0, v1, y0, y1, bars=7, u=0.24):
    """Matte black electric ladder towel warmer standing off the wall."""
    r_rail, r_bar = 0.045, 0.03
    for v in (v0, v1):
        fcyl(ctx, f, name + ' rail', u, v, (y0 + y1) / 2, r_rail, y1 - y0, 'y', BLACK, coll)
        fcyl(ctx, f, name + ' rail cap', u, v, y1 + 0.005, r_rail, 0.01, 'y', BLACK, coll)
        for yy in (y0 + 0.25, y1 - 0.25):
            fcyl(ctx, f, name + ' standoff', u / 2, v, yy, 0.022, u, 'u', BLACK, coll)
            fcyl(ctx, f, name + ' rose', 0.008, v, yy, 0.055, 0.016, 'u', BLACK, coll)
    for k in range(bars):
        yy = y0 + 0.12 + (y1 - y0 - 0.2) * k / (bars - 1)
        fcyl(ctx, f, name + f' bar {k}', u, (v0 + v1) / 2, yy, r_bar, v1 - v0, 'v', BLACK, coll)
    return u, r_bar


def draped(ctx, f, coll, name, u0, u1, v0, v1, y_top, drop_back, drop_front, mat, th=0.05, rc=0.04):
    """Towel draped over a rail or ledge whose top spans u0..u1 at y_top (round bar: u0 == u1,
    rc = bar radius). Profile sheet in (u, y) extruded along v, softly displaced, then given
    thickness and eased hems (no subdivision, so the hems stay straight like real terry)."""
    h = th / 2
    pts = []
    for k in range(14):                                      # back drop, bottom -> top
        pts.append((u0 - rc - h, y_top - drop_back + (drop_back - rc) * k / 14))
    for k in range(0, 9):
        t = math.pi - (math.pi / 2) * k / 8
        pts.append((u0 + (rc + h) * math.cos(t), y_top - rc + (rc + h) * math.sin(t)))
    if u1 > u0 + 1e-4:
        pts.append(((u0 + u1) / 2, y_top + h))
    for k in range(0, 9):
        t = math.pi / 2 - (math.pi / 2) * k / 8
        pts.append((u1 + (rc + h) * math.cos(t), y_top - rc + (rc + h) * math.sin(t)))
    for k in range(1, 15):                                   # front drop, top -> bottom
        pts.append((u1 + rc + h, y_top - rc - (drop_front - rc) * k / 14))
    # dedupe consecutive points
    clean = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - clean[-1][0]) + abs(p[1] - clean[-1][1]) > 1e-5:
            clean.append(p)
    pts = clean
    nv = 22
    verts, faces = [], []
    ucen = (u0 + u1) / 2
    vc = (v0 + v1) / 2
    for j in range(nv + 1):
        t = j / nv
        v = v0 + (v1 - v0) * t
        # folded layers make the middle of each hanging panel puff out and the folded sides roll
        puff = 0.022 * math.sin(math.pi * t) ** 0.6
        for (u, y) in pts:
            below = max(0.0, (y_top - rc) - y)                 # depth below the bar / ledge top
            s = min(1.0, below / 0.35)
            out = 1.0 if u > ucen else -1.0
            du = out * puff * s
            # the hem kicks out slightly (thickness of the folded hem) and its edge is not ruler straight
            ybot = y_top - (drop_front if out > 0 else drop_back)
            hem = max(0.0, 1.0 - (y - ybot) / 0.25) if below > 0 else 0.0
            du += out * 0.012 * hem
            dy = 0.0
            if below > 0.5:
                dy = 0.008 * math.sin(2 * math.pi * (1.3 * t + (0.17 if out > 0 else 0.61))) * min(1.0, (below - 0.5) / 0.4)
            # fabric bunches into a slight waist just under the bar and flares toward the hem
            k = 1.0 - 0.035 * max(0.0, 1.0 - below / 0.45) * min(1.0, below / 0.08) + 0.02 * max(0.0, below - 0.5)
            x, z = f.w(u + du, vc + (v - vc) * k)
            verts.append((x, y + dy, z))
    m = len(pts)
    for j in range(nv):
        for i in range(m - 1):
            a = j * m + i
            faces.append((a, a + 1, a + 1 + m, a + m))
    ob = mesh_ft(ctx, name, verts, faces, mat, coll, smooth=True)
    tex = bpy.data.textures.get('Z_baths_towel_clouds') or bpy.data.textures.new('Z_baths_towel_clouds', 'CLOUDS')
    tex.noise_scale = 0.16
    tex.noise_depth = 1
    dm = ob.modifiers.new('soft', 'DISPLACE')
    dm.texture = tex
    dm.strength = 0.055 * FT
    dm.mid_level = 0.5
    dm.texture_coords = 'GLOBAL'
    so = ob.modifiers.new('thick', 'SOLIDIFY')
    so.thickness = th * FT
    so.offset = 0.0
    so.use_rim = True
    bv = ob.modifiers.new('hem', 'BEVEL')
    bv.width = th * 0.42 * FT
    bv.segments = 3
    bv.limit_method = 'ANGLE'
    return ob


def folded_towel(ctx, coll, name, x, y, z, w, d, h, rot, mat):
    """Neatly folded towel: soft rounded slab (w along x before rotation)."""
    ob = ctx.box_c(name, (x, y + h / 2, z), (w, h, d), rot, None, coll, bevel=h * 0.42, segments=4)
    ob.data.materials.append(mat)
    return ob


def tp_holder(ctx, f, coll, name, v, y):
    fcyl(ctx, f, name + ' rose', 0.01, v, y, 0.07, 0.02, 'u', BLACK, coll)
    fcyl(ctx, f, name + ' arm', 0.13, v, y, 0.022, 0.24, 'u', BLACK, coll)
    fcyl(ctx, f, name + ' bar', 0.25, v + 0.22, y, 0.02, 0.44, 'v', BLACK, coll)
    fcyl(ctx, f, name + ' roll', 0.25, v + 0.24, y, 0.19, 0.36, 'v', matte_material('paper', (0.86, 0.85, 0.82), 0.95), coll)
    fcyl(ctx, f, name + ' roll core', 0.25, v + 0.24, y, 0.07, 0.362, 'v', matte_material('paper_core', (0.45, 0.38, 0.30), 0.9), coll)


def towel_bar(ctx, f, coll, name, v0, v1, y, u=0.24):
    for v in (v0, v1):
        fcyl(ctx, f, name + ' rose', 0.01, v, y, 0.06, 0.02, 'u', BLACK, coll)
        fcyl(ctx, f, name + ' post', u / 2, v, y, 0.022, u, 'u', BLACK, coll)
    fcyl(ctx, f, name + ' bar', u, (v0 + v1) / 2, y, 0.026, (v1 - v0) + 0.06, 'v', BLACK, coll)
    return u


def bottle(ctx, coll, name, x, y, z, r=0.1, h=0.62, mat=None):
    """Refillable matte bottle with a black pump."""
    mat = mat or matte_material('bottle_stone', (0.62, 0.60, 0.56), 0.6)
    b = ctx.cylinder(name, (x, y + h / 2, z), r, h, None, coll, verts=32)
    b.data.materials.append(mat)
    ctx.add_bevel(b, 0.02, 3)
    p = ctx.cylinder(name + ' pump', (x, y + h + 0.05, z), r * 0.32, 0.1, None, coll, verts=24)
    p.data.materials.append(ctx.mat(BLACK))
    hd = ctx.box_c(name + ' pump head', (x + 0.04, y + h + 0.115, z), (0.16, 0.035, 0.05), 0.0, None, coll, bevel=0.01)
    hd.data.materials.append(ctx.mat(BLACK))
    return b


# --------------------------------------------------------------------------- mirrors
def backlit_rect_mirror(ctx, f, coll, name, v0, v1, y0, y1, standoff=0.09, glow=14.0, band=1.3):
    """Frameless mirror floating off the wall with an LED backlight halo and a frosted LED band."""
    fbox(ctx, f, name + ' glass', standoff - 0.02, standoff, v0, v1, y0, y1, 'mirror', coll, bevel=0.006, seg=2)
    em = lighting.emitter('bath_mirror_back', MIRROR_K, glow)
    back = fbox(ctx, f, name + ' backlight', 0.01, standoff - 0.022, v0 + 0.14, v1 - 0.14, y0 + 0.14, y1 - 0.14, None, coll)
    back.data.materials.append(em)
    back.visible_camera = False
    # frosted LED band, 0.1ft inside the edge
    eb = lighting.emitter('bath_mirror_band', MIRROR_K, band)
    i, w = 0.10, 0.028
    u0, u1 = standoff, standoff + 0.002
    for nm, a, b, c, d in (('top', v0 + i, v1 - i, y1 - i - w, y1 - i), ('bottom', v0 + i, v1 - i, y0 + i, y0 + i + w),
                           ('left', v0 + i, v0 + i + w, y0 + i + w, y1 - i - w), ('right', v1 - i - w, v1 - i, y0 + i + w, y1 - i - w)):
        o = fbox(ctx, f, f'{name} band {nm}', u0, u1, a, b, c, d, None, coll)
        o.data.materials.append(eb)


def backlit_round_mirror(ctx, f, coll, name, v, yc, r, standoff=0.09, glow=22.0):
    """Frameless round mirror with an LED halo washing the wall behind it."""
    fcyl(ctx, f, name + ' glass', standoff - 0.01, v, yc, r, 0.02, 'u', 'mirror', coll, verts=96)
    back = fcyl(ctx, f, name + ' backlight', (standoff - 0.02) / 2 + 0.005, v, yc, r - 0.10, standoff - 0.03, 'u', None, coll, verts=64)
    back.data.materials.append(lighting.emitter('bath_mirror_back', MIRROR_K, glow))
    back.visible_camera = False


def pill_mirror(ctx, f, coll, name, v, yc, w, h, standoff=0.09, glow=14.0):
    """Capsule mirror with a slim matte black frame and an LED backlight halo."""
    wall_prism(ctx, f, name + ' frame', stadium_vy(v, yc, w + 0.05, h + 0.05), standoff - 0.035, standoff, BLACK, coll, smooth=True)
    wall_prism(ctx, f, name + ' glass', stadium_vy(v, yc, w, h), standoff - 0.03, standoff + 0.004, 'mirror', coll, smooth=True)
    back = wall_prism(ctx, f, name + ' backlight', stadium_vy(v, yc, w - 0.25, h - 0.25), 0.01, standoff - 0.04, None, coll)
    back.data.materials.append(lighting.emitter('bath_mirror_back', MIRROR_K, glow))
    back.visible_camera = False


# ---------------------------------------------------------------------- Poly Haven props
_ASSET_CACHE = {}


def asset_prop(ctx, coll, asset_id, x, y, z, rot=0.0, height=None, name=None):
    """Import (once) a Poly Haven model and place an instance with its bottom centre at
    (x, y, z) SCENE ft, rotated about +Y (optionally scaled to `height` ft). Later instances are
    linked duplicates that share mesh data."""
    from .. import assets
    root = bpy.data.objects.new(name or asset_id, None)
    ctx.coll(coll).objects.link(root)
    first = asset_id not in _ASSET_CACHE
    if first:
        roots = ctx.link_asset(assets.model(asset_id, res='2k'))
        bpy.context.view_layer.update()
        x0, x1, y0, y1, z0, z1 = world_bbox_ft(roots)
        off = ft2bl((x0 + x1) / 2, y0, (z0 + z1) / 2)
        for r in roots:
            r.location = r.location - off
        move_to_collection(roots, ctx.coll(coll))
        _ASSET_CACHE[asset_id] = (roots, (x1 - x0, y1 - y0, z1 - z0))
    roots, dims = _ASSET_CACHE[asset_id]

    def clone(ob, parent):
        c = ob if first else ob.copy()
        if not first:
            ctx.coll(coll).objects.link(c)
        c.parent = parent
        for ch in list(ob.children):
            clone(ch, c)

    for r in roots:
        clone(r, root)
    s = (height / dims[1]) if height else 1.0
    root.scale = (s, s, s)
    root.location = ft2bl(x, y, z)
    root.rotation_euler = (0, 0, rot)
    return root, (dims[0] * s, dims[1] * s, dims[2] * s)


def exhaust_grille(ctx, coll, name, x, z, size=0.78, ceil=8.0):
    """Flush white bath-fan grille with dark louvre slots on the ceiling."""
    box(ctx, name, x - size / 2, x + size / 2, ceil - 0.018, ceil, z - size / 2, z + size / 2, 'paint_trim', coll, bevel=0.006)
    dark = matte_material('grille_slot', (0.06, 0.06, 0.06), 0.8)
    n = 7
    for k in range(n):
        zz = z - size / 2 + 0.12 + (size - 0.24) * k / (n - 1)
        box(ctx, f'{name} slot {k}', x - size / 2 + 0.1, x + size / 2 - 0.1, ceil - 0.0195, ceil - 0.0182,
            zz - 0.012, zz + 0.012, dark, coll)


def outlet(ctx, f, coll, name, v, y):
    """White GFCI duplex outlet with a Decora plate (2.75 x 4.5in)."""
    fbox(ctx, f, name + ' plate', 0.0, 0.018, v - 0.115, v + 0.115, y - 0.19, y + 0.19, 'paint_trim', coll, bevel=0.006)
    fbox(ctx, f, name + ' face', 0.018, 0.026, v - 0.056, v + 0.056, y - 0.11, y + 0.11, CERAMIC, coll, bevel=0.004)
    for dy in (-0.012, 0.012):
        fbox(ctx, f, name + ' btn', 0.026, 0.03, v - 0.03, v + 0.03, y + dy - 0.008, y + dy + 0.008, 'paint_trim', coll)


def u_channel(ctx, coll, name, a, b, y, w=0.075, h=0.055):
    """Low-profile matte black U-channel the fixed glass stands in (plan points a -> b)."""
    (ax, az), (bx, bz) = a, b
    if abs(az - bz) < 1e-6:
        return box(ctx, name, min(ax, bx), max(ax, bx), y, y + h, az - w / 2, az + w / 2, BLACK, coll, bevel=0.006)
    return box(ctx, name, ax - w / 2, ax + w / 2, y, y + h, min(az, bz), max(az, bz), BLACK, coll, bevel=0.006)
