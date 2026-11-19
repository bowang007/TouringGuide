"""Far neighbourhood for the exterior orbit renders (runs inside Blender).

The near context (exterior_context) was built for what the windows and the hero stills see. From the
drone-height orbit (render_exterior.py) the whole neighbourhood is in view, so this module fills it out
the way the user's aerial photo of the street shows it (assets/references/img-3202.webp):

- parallel streets every ~219 ft (two ~81 ft deep lots back to back + a 56 ft right of way), a few cross
  streets, sidewalks, curbs and street trees;
- ~60 ft ranch lots on both sides: single-storey house (hip or gable roof, windows, garage door, front
  door), driveway and walk, side and rear board fences, backyard trees, patios, dry lawn patches and the
  odd pool;
- a belt of mature trees out to ~4000 ft so the horizon reads as a leafy suburb, and the hills around
  the valley (Santa Cruz Mountains south-west, the East Bay hills north-east, the Diablo Range east).

Everything is in its own collection (ext_far), excluded from the view layer at build time, so the
panoramas, hero stills and the web bake are unchanged; render_exterior.py includes it.
"""
import math

import bpy

from . import exterior_layout as L
from .exterior_context import (_facade_windows, _fbox, _garage_door, _house_mats, _roof, board_fence_mat,
                               drive_mat)
from .exterior_plants import _gn_scatter, load, plant, scatter
from .exterior_util import GRADE, MB, _srgb, coll, exclude_collection, flat_mat, rng, tex_mat, varied

SUB = 'far'

# ---- street grid (pure geometry; exterior_context uses spine_z to keep its trees in the backyards) -----
STREET_Z0 = (L.STREET[0] + L.STREET[1]) / 2     # our street's centre line (94.5)
PITCH_Z = 219.0                                  # street spacing
STREETS_Z = [STREET_Z0 + PITCH_Z * k for k in range(-5, 6)]
OURS = 5                                         # index of our street in STREETS_Z
CROSS_X = (-1320.0, -700.0, 760.0, 1380.0)
ROW = 28.0                                       # half right of way (walk + park strip + curb + street)
GRID_X = (-1900.0, 1900.0)
GRID_Z = (STREETS_Z[0] - 110.0, STREETS_Z[-1] + 110.0)
LOT_D = 81.0
# x ranges already built in detail by exterior_context, per (street index, side): side -1 = lots north of
# the street (front faces +z), +1 = lots south of it (front faces -z)
NEAR = {(OURS, -1): (-245.0, 282.0), (OURS, 1): (-258.0, 322.0), (OURS - 1, 1): (-82.0, 142.0)}
BELT = (-4200.0, 4200.0, -2600.0, 2800.0)        # tree belt outer rectangle (x0, x1, z0, z1)
FAR_E = 15000.0                                  # outer ground edge
HILLS_R = 12000.0


def spine_z(z):
    """z of the nearest block spine (the line where two rows of back fences meet)."""
    k = round((z - STREET_Z0 - PITCH_Z / 2) / PITCH_Z)
    return STREET_Z0 + PITCH_Z / 2 + k * PITCH_Z


def in_backyards(z, half=12.0):
    return abs(z - spine_z(z)) <= half


def _segments():
    edges = [GRID_X[0]] + [v for xc in CROSS_X for v in (xc - ROW, xc + ROW)] + [GRID_X[1]]
    return list(zip(edges[0::2], edges[1::2]))


# ------------------------------------------------------------------------------------------ build
class _Bins:
    """Shared mesh builders keyed by material, so ~1300 houses become ~100 objects."""

    def __init__(self):
        self.d = {}

    def __call__(self, key):
        mb = self.d.get(key)
        if mb is None:
            mb = self.d[key] = MB()
        return mb

    def emit(self, ctx, mats):
        n = 0
        for key, mb in self.d.items():
            if mb.f:
                mb.obj(ctx, f'ext far {key[0]} {n}', mats[key], SUB)
                n += 1
        return n


STYLES = 16
# roof tints read off the aerial photo: mostly light grey / warm grey composition shingle, some brown,
# terracotta and orange-tan tile, a few dark roofs
STYLE_ROOFS = ['#b0aba3', '#a89a88', '#8c7f71', '#c0b6a6', '#9d9a95', '#6d6b69', '#b86a52', '#a9a49c',
               '#c99068', '#958a7e', '#bdb2a0', '#9a5a48', '#a7a199', '#7d7974', '#b4a690', '#aca8a1']


def _styles(ctx):
    out = []
    for s in range(STYLES):
        M = _house_mats(ctx, 40 + s, rng(40 + s), STYLE_ROOFS[s])
        st = dict(grids=(s % 5 == 2), shutters=(M['clad'] == 'siding' and s % 4 == 1))
        out.append((M, st, s))
    return out


def _house(B, mats, ctx, r, lx0, lx1, zc, side, style, trees, foot):
    M, st, si = style
    sk = id(M['wall'])
    zf = zc + side * ROW                      # lot front line (back of the sidewalk)
    sgn = -side                               # facade normal along z: +1 faces +z (north-side lots)
    lw = lx1 - lx0
    hw = min(lw - r.uniform(9.0, 16.0), 50.0)
    x0 = lx0 + r.uniform(4.5, max(4.6, lw - hw - 4.5))
    x1 = x0 + hw
    hd, sb = r.uniform(30.0, 42.0), r.uniform(18.0, 26.0)
    if side < 0:
        z1 = zf - sb
        z0 = z1 - hd
        cz = z1
    else:
        z0 = zf + sb
        z1 = z0 + hd
        cz = z0
    floor = 0.5
    yw = floor + r.uniform(8.0, 8.9)
    pitch = r.choice((4.0, 4.5, 5.0, 5.5, 6.0)) / 12
    kind = 'hip' if r.random() < 0.62 else 'gable'
    right = r.random() < 0.5
    gwing = r.choice((0.0, 0.0, 0.0, 7.0, 9.0))
    wing = None
    if gwing > 0:
        wx = (x1 - 22.0, x1) if right else (x0, x0 + 22.0)
        wz = (cz - 16.0, cz + gwing) if side < 0 else (cz - gwing, cz + 16.0)
        wing = (wx[0], wx[1], min(wz), max(wz))
        gx = (wx[0] + 3.0, wx[1] - 3.0)
    else:
        gx = (x1 - 18.0, x1 - 2.0) if right else (x0 + 2.0, x0 + 18.0)
    gcz = cz + sgn * gwing
    boxes = [(x0, x1, z0, z1)] + ([wing] if wing else [])
    for b in boxes:
        B(('walls', sk)).box(b[0], b[1], GRADE - 0.3, yw, b[2], b[3])
        mats[('walls', sk)] = M['wall']
        foot.append((b[0] - 2.0, b[1] + 2.0, b[2] - 2.0, b[3] + 2.0))
    rk = ('roof', id(M['roof']), id(M['trim']))
    mats[rk] = [M['roof'], M['trim']]
    gk = ('gutter', id(M['gutter']))
    mats[gk] = M['gutter']
    _roof(B(rk), B(gk), B(('walls', sk)), (x0, x1, z0, z1), kind, hw >= hd, 1.6, yw, pitch)
    if wing:
        _roof(B(rk), B(gk), B(('walls', sk)), wing, 'gable', False, 1.6, yw, pitch)
    # front door beside the garage; windows everywhere else
    dx = (gx[0] - 6.0 if right else gx[1] + 6.0) if not wing else (wing[0] - 5.0 if right else wing[1] + 5.0)
    dx = min(max(dx, x0 + 3.0), x1 - 3.0)
    dk = ('door', id(M['door']))
    mats[dk] = M['door']
    _fbox(B(dk), 'z', cz, sgn, dx - 1.5, dx + 1.5, floor - 0.12, floor + 6.7, 0.0, 0.08)
    win, fk = B(('glass',)), ('frame', id(M['trim']), id(M['shutter']))
    mats[('glass',)] = [M['glass'], M['blind'], M['curtain']]
    mats[fk] = [M['trim'], M['shutter']]
    skips = [(dx - 2.4, dx + 2.4), ((wing[0], wing[1]) if wing else gx)]
    skips = [(a - 0.8, b + 0.8) for a, b in skips]
    for ax, c, s, a, b, isf in (('z', z1, 1, x0, x1, side < 0), ('z', z0, -1, x0, x1, side > 0),
                                ('x', x1, 1, z0, z1, False), ('x', x0, -1, z0, z1, False)):
        sk2 = list(skips) if isf else []
        if wing and ax == 'x' and ((s > 0) == right):
            sk2 = [(wing[2] - 0.8, wing[3] + 0.8)]
        _facade_windows(win, B(fk), ax, c, s, a, b, sk2, floor, r, st, front=isf)
    gdk, gtk = ('gdoor', id(M['gdoor'])), ('gtrim', id(M['trim']))
    mats[gdk], mats[gtk], mats[('dark',)] = [M['gdoor'], M['glass']], M['trim'], M['dark']
    _garage_door(B(gdk), B(gtk), B(('dark',)), gx[0], gx[1], gcz, sgn, GRADE + 0.05, floor + 7.0, si % 3)
    # driveway + apron, front walk
    drv = B(('drive',))
    za, zb = sorted((gcz, zf))
    drv.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, GRADE + 0.08, za, zb)
    pa, pb = sorted((zc + side * 23.5, zc + side * 19.0))
    drv.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, GRADE + 0.07, pa, pb)
    wa, wb = sorted((cz, cz + sgn * 6.5))
    drv.box(dx - 1.75, dx + 1.75, GRADE - 0.3, GRADE + 0.08, wa, wb)
    ex = gx[0] + 0.5 if dx < gx[0] else gx[1] - 0.5
    wa, wb = sorted((cz + sgn * 3.0, cz + sgn * 6.5))
    drv.box(min(dx, ex), max(dx, ex), GRADE - 0.3, GRADE + 0.08, wa, wb)
    # fences: west lot line from just behind the front face to the rear line; rear line on north-side lots
    rear = zf - LOT_D if side < 0 else zf + LOT_D
    fa, fb = sorted((cz - sgn * 3.0, rear))
    fen = B(('fence',))
    fen.box(lx0 - 0.08, lx0 + 0.08, GRADE - 0.1, GRADE + 6.0, fa, fb)
    if side < 0:
        fen.box(lx0, lx1, GRADE - 0.1, GRADE + 6.0, rear - 0.08, rear + 0.08)
    # backyard: patio, dry lawn, pool; trees
    back = z0 if side < 0 else z1                 # house rear face
    by0, by1 = sorted((back - sgn * 1.0, rear + sgn * 1.0))
    if by1 - by0 > 12.0:
        k = r.random()
        if k < 0.09 and by1 - by0 > 21.0 and lw > 50:
            px0 = lx0 + r.uniform(5.0, lw - 34.0)
            pz0 = (by0 + by1) / 2 - 7.5
            cop = B(('drive',))                   # coping ring around the water
            for q in ((px0 - 2.0, px0 + 30.0, pz0 - 2.0, pz0), (px0 - 2.0, px0 + 30.0, pz0 + 15.0, pz0 + 17.0),
                      (px0 - 2.0, px0, pz0, pz0 + 15.0), (px0 + 28.0, px0 + 30.0, pz0, pz0 + 15.0)):
                cop.box(q[0], q[1], GRADE - 0.3, GRADE + 0.1, q[2], q[3])
            B(('pool',)).box(px0, px0 + 28.0, GRADE - 0.3, GRADE + 0.0, pz0, pz0 + 15.0)   # over the lawn quad (GRADE - .02)
            foot.append((px0 - 3.0, px0 + 31.0, pz0 - 3.0, pz0 + 18.0))
        elif k < 0.45:
            pz = sorted((back, back - sgn * r.uniform(8.0, 12.0)))
            B(('drive',)).box(x0 + 2.0, x0 + 2.0 + hw * r.uniform(0.35, 0.6), GRADE - 0.3, GRADE + 0.06, pz[0], pz[1])
        if r.random() < 0.4:
            B(('dry',)).box(lx0 + 1.0, lx1 - 1.0, GRADE - 0.1, GRADE + 0.015, by0 + 1.0, by1 - 1.0)
        for _ in range(r.choice((0, 1, 1, 2, 2, 3))):
            trees.append(('back', r.uniform(lx0 + 4.0, lx1 - 4.0), r.uniform(by0 + 3.0, by1 - 3.0), r.random()))
    if r.random() < 0.5:                          # front-yard tree, on the side away from the driveway
        fx = r.uniform(x0 + 4.0, gx[0] - 6.0) if right else r.uniform(gx[1] + 6.0, x1 - 4.0)
        if (gx[0] - fx > 5.0 or fx - gx[1] > 5.0) and abs(fx - dx) > 4.0:
            trees.append(('front', fx, (cz + zf) / 2 + r.uniform(-2.0, 2.0), r.random()))
    if r.random() < 0.55:                         # street tree in the park strip
        sx = (lx0 + lx1) / 2 + r.uniform(-12.0, 12.0)
        if sx < gx[0] - 6.0 or sx > gx[1] + 6.0:
            trees.append(('street', sx, zc + side * 21.25, r.random()))


def _streets(ctx):
    asphalt = bpy.data.materials.get('Z_exterior_asphalt') or tex_mat('Z_exterior_asphalt', 'asphalt_02', 2.5,
                                                                      tint='#9a9a9a')
    conc = varied(ctx, 'concrete_drive', 0.04, 'Z_exterior_walk_var')
    a, c = MB(), MB()
    top = GRADE + 0.03
    lawn = MB()
    for i, zc in enumerate(STREETS_Z):
        spans = [(GRID_X, top)]
        if i == OURS:   # our street: the near model covers -420..470 inside a cut in the +-900 ft ground plane
            spans = [((GRID_X[0], -900.0), top), ((900.0, GRID_X[1]), top),
                     ((-900.0, -420.0), L.STREET_TOP), ((470.0, 900.0), L.STREET_TOP)]
        for (xa, xb), t in spans:
            near = t != top
            wt = L.WALK_TOP if near else top + 0.08
            a.box(xa, xb, t - 0.3, t, zc - 18.5, zc + 18.5)
            for s in (-1, 1):
                za, zb = sorted((zc + s * 18.5, zc + s * 19.0))
                c.box(xa, xb, t - 0.3, wt + 0.05, za, zb)                       # curb
                za, zb = sorted((zc + s * 23.5, zc + s * 28.0))
                c.box(xa, xb, t - 0.3, wt, za, zb)                              # sidewalk
                if near:                                                        # park strip inside the cut
                    za, zb = sorted((zc + s * 19.0, zc + s * 23.5))
                    lawn.box(xa, xb, GRADE - 0.3, GRADE, za, zb)
    edges = [GRID_Z[0]] + [v for zc in STREETS_Z for v in (zc - ROW, zc + ROW)] + [GRID_Z[1]]
    for xc in CROSS_X:
        for za, zb in zip(edges[0::2], edges[1::2]):
            a.box(xc - 18.5, xc + 18.5, top - 0.3, top, za, zb)
            for s in (-1, 1):
                xa, xb = sorted((xc + s * 18.5, xc + s * 19.0))
                c.box(xa, xb, top - 0.3, top + 0.4, za, zb)
                xa, xb = sorted((xc + s * 23.5, xc + s * 28.0))
                c.box(xa, xb, top - 0.3, top + 0.08, za, zb)
    a.obj(ctx, 'ext far street asphalt', asphalt, SUB)
    c.obj(ctx, 'ext far curbs and sidewalks', conc, SUB)
    from .exterior_site import far_lawn_mat
    lawn.obj(ctx, 'ext far park strips', far_lawn_mat(), SUB)


def _ring(mb, outer, inner, y):
    """Four quads covering rectangle `outer` minus rectangle `inner` (x0, x1, z0, z1), facing up."""
    X0, X1, Z0, Z1 = outer
    x0, x1, z0, z1 = inner
    for q in ((X0, X1, Z0, z0), (X0, X1, z1, Z1), (X0, x0, z0, z1), (x1, X1, z0, z1)):
        mb.quad((q[0], y, q[3]), (q[1], y, q[3]), (q[1], y, q[2]), (q[0], y, q[2]))


def _flip_up(ob):
    for p in ob.data.polygons:
        if p.normal.z < 0:
            p.flip()


def _suburb_mat():
    """Distant ground: canopy, roofs and lawns mottled together at a few hundred feet."""
    name = 'Z_exterior_far_suburb'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.03
    nz.inputs['Detail'].default_value = 8.0
    nz.inputs['Roughness'].default_value = 0.7
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.35, _srgb('#3a4a2e')
    el[1].position, el[1].color = 0.65, _srgb('#6f6c60')
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    return m


WOODED, DRY, MID = '#7c8a8a', '#aa9f8b', '#959488'     # hazed: Santa Cruz Mountains / East Bay hills / between


def _hills_mat():
    name = 'Z_exterior_far_hills'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'hill'
    nt.links.new(at.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    return m


def _hills(ctx):
    """Low-poly ridges around the valley at ~2.3 miles, coloured with distance haze (blended by direction)."""

    def g(a, c, s):
        d = math.atan2(math.sin(a - c), math.cos(a - c))
        return math.exp(-(d / s) ** 2)

    n = 720
    mb = MB()
    rows = []
    for i in range(n):
        a = 2 * math.pi * i / n                     # direction (cos a, sin a) in (x, z); +z is south
        h = (720 * g(a, math.radians(135), math.radians(55)) + 520 * g(a, math.radians(-45), math.radians(60)) +
             640 * g(a, math.radians(20), math.radians(35)) + 70)
        h *= 0.78 + 0.14 * math.sin(7 * a + 1.3) * math.sin(13 * a + 0.4) + 0.08 * math.sin(31 * a + 2.0)
        r0, r1 = HILLS_R, HILLS_R + 2.4 * h
        ca, sa = math.cos(a), math.sin(a)
        rows.append([mb.vert(r0 * ca, GRADE, r0 * sa), mb.vert((r0 + r1) / 2 * ca, h * 0.55, (r0 + r1) / 2 * sa),
                     mb.vert(r1 * ca, h, r1 * sa), mb.vert((r1 + 1800) * ca, GRADE, (r1 + 1800) * sa)])
        rows[-1].append(a)
    for i in range(n):
        p, q = rows[i], rows[(i + 1) % n]
        for k in range(3):
            mb.face((p[k], q[k], q[k + 1], p[k + 1]))
    ob = mb.obj(ctx, 'ext far hills', _hills_mat(), SUB)
    ca = ob.data.color_attributes.new('hill', 'FLOAT_COLOR', 'POINT')
    cw, cd, cm = (_srgb(h)[:3] for h in (WOODED, DRY, MID))
    for i, row in enumerate(rows):
        a = row[4]
        ww = g(a, math.radians(135), math.radians(55))
        wd = max(g(a, math.radians(-45), math.radians(60)), g(a, math.radians(20), math.radians(35)))
        wm = max(0.0, 1.0 - ww - wd)
        t = ww + wd + wm
        col = [(ww * cw[j] + wd * cd[j] + wm * cm[j]) / t for j in range(3)] + [1.0]
        for v in row[:4]:
            ca.data[v].color = col
    # faces must look toward the valley
    for pl in ob.data.polygons:
        c = pl.center
        if pl.normal.dot(c.normalized()) > 0:
            pl.flip()
    return ob


def build(ctx):
    from .exterior_site import far_lawn_mat
    c = coll(ctx, SUB)
    r = rng(4242)
    styles = _styles(ctx)
    B = _Bins()
    mats = {('drive',): drive_mat(ctx), ('fence',): board_fence_mat(),
            ('pool',): flat_mat('Z_exterior_far_pool', '#3d93b8', 0.06, 0.0, spec=1.0),
            ('dry',): flat_mat('Z_exterior_far_dry_lawn', '#8f8a62', 0.95)}
    trees, foot = [], []
    nh = 0
    for i, zc in enumerate(STREETS_Z):
        for side in (-1, 1):
            near = NEAR.get((i, side))
            for sa, sb in _segments():
                x = sa + r.uniform(0.0, 6.0)
                while x < sb - 50.0:
                    w = r.uniform(56.0, 64.0)
                    lx0, lx1 = x, min(x + w, sb)
                    x += w
                    if near and lx1 > near[0] and lx0 < near[1]:
                        continue
                    _house(B, mats, ctx, r, lx0, lx1, zc, side, styles[r.randrange(STYLES)], trees, foot)
                    nh += 1
    nobj = B.emit(ctx, mats)
    _streets(ctx)
    # ground beyond the near ground plane (+-900 ft): lots, tree belt, far suburb
    g = MB()
    _ring(g, (GRID_X[0], GRID_X[1], GRID_Z[0], GRID_Z[1]), (-900.0, 900.0, -900.0, 900.0), GRADE - 0.02)
    _flip_up(g.obj(ctx, 'ext far ground lots', far_lawn_mat(), SUB))
    belt = MB()
    _ring(belt, BELT, (GRID_X[0], GRID_X[1], GRID_Z[0], GRID_Z[1]), GRADE - 0.02)
    belt_ob = belt.obj(ctx, 'ext far ground belt', far_lawn_mat(), SUB)
    _flip_up(belt_ob)
    outer = MB()
    _ring(outer, (-FAR_E, FAR_E, -FAR_E, FAR_E), BELT, GRADE - 0.05)
    _flip_up(outer.obj(ctx, 'ext far ground suburb', _suburb_mat(), SUB))
    _hills(ctx)
    # trees: lots and park strips (instances), then the belt (geometry-nodes scatter)
    leaf = dict(amount=0.3)
    nt = 0
    for kind, x, z, k in trees:
        if any(a < x < b and c_ < z < d for a, b, c_, d in foot):
            continue
        if kind == 'back':
            if k < 0.7:
                plant(ctx, 'tree_small_02', 'main', x, z, height_ft=22.0 + 18.0 * k, leaf=leaf, sub=SUB)
            else:
                plant(ctx, 'island_tree_01' if k < 0.85 else 'island_tree_02', 'main', x, z,
                      height_ft=11.0 + 20.0 * (k - 0.7), leaf=leaf, sub=SUB)
        elif kind == 'front':
            plant(ctx, 'tree_small_02' if k < 0.75 else 'island_tree_02', 'main', x, z,
                  height_ft=16.0 + 12.0 * k, leaf=leaf, sub=SUB)
        else:
            plant(ctx, 'tree_small_02', 'main', x, z, height_ft=18.0 + 12.0 * k, leaf=leaf, sub=SUB)
        nt += 1
    src = load(ctx, 'tree_small_02', '1k', leaf)
    tree_coll = src.get('main') or next(iter(src.values()))
    tree_ob = tree_coll.objects[0]
    hm = max(float(tree_coll.get('height_m', 8.0)), 1.0)
    ng = _gn_scatter('ext GN far tree belt', tree_ob, density_m2=1.0 / 190.0, smin=26 * 0.3048 / hm,
                     smax=46 * 0.3048 / hm, seed=91, tilt=0.03)
    scatter([belt_ob], ng)
    exclude_collection(c)
    return {'houses': nh, 'objects': nobj, 'trees': nt}
