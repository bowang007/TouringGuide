"""Grounds and hardscape: ground planes, foundation plinth, lawn/bed/pebble surfaces, ipe deck,
side-yard pavers, porch block + entry steps, front walk, driveway with gravel joints, sidewalk, curb,
gutter and street (runs inside Blender)."""
import math

import bpy

from ..common import FT, bl2ft
from . import exterior_layout as L
from .exterior_util import GRADE, MB, flat_mat, rng, tex_mat, varied

SUB = 'site'


def _rect(mb, r, y0, y1, mi=0):
    x0, x1, z0, z1 = r
    return mb.box(x0, x1, y0, y1, z0, z1, mi)


def _surface(ctx, name, r, top, mat, hfn=None, step=1.0, thick=0.08):
    """Flat (or height-field) surface slab over rect r. Returns the object (used for scattering)."""
    x0, x1, z0, z1 = r
    mb = MB()
    if hfn is None:
        mb.box(x0, x1, top - thick, top, z0, z1)
    else:
        mb.grid(x0, x1, z0, z1, hfn, step)
    ob = mb.obj(ctx, name, mat, SUB)
    return ob


# --------------------------------------------------------------------------------- ground
def far_lawn_mat():
    """Neighbourhood lawns (ground plane): procedural mown-grass colour with patchy variation."""
    m = bpy.data.materials.get('Z_exterior_far_lawn')
    if m:
        return m
    from .exterior_util import _srgb
    m = bpy.data.materials.new('Z_exterior_far_lawn')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 0.35
    n1.inputs['Detail'].default_value = 6.0
    nt.links.new(geo.outputs['Position'], n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position = 0.35
    cr.elements[0].color = _srgb('#3f5524')
    cr.elements[1].position = 0.7
    cr.elements[1].color = _srgb('#6a7a3c')
    nt.links.new(n1.outputs['Fac'], ramp.inputs['Fac'])
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 60.0
    n2.inputs['Detail'].default_value = 2.0
    nt.links.new(geo.outputs['Position'], n2.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.35
    nt.links.new(ramp.outputs['Color'], mix.inputs['A'])
    nt.links.new(n2.outputs['Color'], mix.inputs['B'])
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.92
    try:
        b.inputs['Specular IOR Level'].default_value = 0.3
    except KeyError:
        pass
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.01
    nt.links.new(n2.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    m.diffuse_color = _srgb('#55692f')
    return m


def ground(ctx):
    far = far_lawn_mat()
    mb = MB()
    E = 900.0
    y = GRADE - 0.02
    # the street right-of-way (sidewalk .. far park strip) is modelled separately (street())
    mb.quad((-E, y, -E), (E, y, -E), (E, y, L.SIDEWALK[0]), (-E, y, L.SIDEWALK[0]))
    mb.quad((-E, y, L.FAR_PARK[0]), (E, y, L.FAR_PARK[0]), (E, y, E), (-E, y, E))
    ob = mb.obj(ctx, 'ext ground plane', far, SUB)
    # flip so normals face up (quads were given clockwise in Blender space)
    for p in ob.data.polygons:
        if p.normal.z < 0:
            p.flip()
    return ob


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


def plinth(ctx):
    """Exposed concrete foundation band between grade and the stucco weep line (y -0.025)."""
    mb = MB()
    y0, y1 = GRADE - 0.5, -0.025
    # 0.01 ft inside the stucco faces (rear/sides, garage, porch walls + foyer wall, bedroom 3)
    e = 0.01
    outline = [(L.HX0 + e, L.HZ0 + e), (L.HX1 - e, L.HZ0 + e), (L.HX1 - e, L.GARAGE_FRONT - e),
               (21.22, L.GARAGE_FRONT - e), (21.22, 47.57), (14.31, 47.57), (14.31, L.BED3_FRONT - e),
               (L.HX0 + e, L.BED3_FRONT - e)]
    mb.box_pts(outline, y0, y1)
    # the canted bay's outline from its stucco plinth. The shell is still on the concept plan while the
    # exterior builds (bl/warp.py carries it over afterwards), so map the points the same way.
    from ..warp import R as relayout
    pts = []
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and 'Bay stucco plinth' in ob.name:
            for v in ob.data.vertices:
                x, y, z = bl2ft(ob.matrix_world @ v.co)
                x, z = relayout.remap_xz(x, z)
                pts.append((round(x, 4), round(z, 4)))
    if pts:
        hull = _hull(pts)
        mb.box_pts(hull, y0, y1)
    return mb.obj(ctx, 'ext foundation plinth', 'foundation', SUB)


# ----------------------------------------------------------------------------------- deck
SAPELE_MEAN = (0.5656, 0.2196, 0.1008)          # linear mean colour of Poly Haven sapele_veneer (2k diffuse)
IPE_GRAIN = 1.3                                   # grain contrast boost
# oiled ipe, board-to-board: a narrow band of mid browns (less red / saturation than fresh-cut ipe, as an
# oiled deck reads in sun). The value spread is about half of what reads as 'striped' in full sun.
IPE_PALETTE = ['#573823', '#5e3c26', '#633c22', '#664026', '#69452c', '#613e2a', '#6e482c', '#5b3b27', '#66432b']


def ipe_mat(ctx, along='x'):
    """Ipe for individually modelled deck boards: sapele grain running along the board, a random texture
    offset and tone per board (Object Info Random). Falls back to a per-object varied library ipe."""
    name = f'Z_exterior_ipe_{along}'
    m = bpy.data.materials.get(name)
    if m:
        return m
    from .. import assets
    from .exterior_util import _srgb
    try:
        maps = assets.texture('sapele_veneer', res='2k')
    except Exception:
        return varied(ctx, 'ipe_deck', 0.16)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    oi = nt.nodes.new('ShaderNodeObjectInfo')
    off = nt.nodes.new('ShaderNodeCombineXYZ')
    for k, f in (('X', 13.7), ('Y', 5.3), ('Z', 2.1)):
        mm = nt.nodes.new('ShaderNodeMath')
        mm.operation = 'MULTIPLY'
        mm.inputs[1].default_value = f
        nt.links.new(oi.outputs['Random'], mm.inputs[0])
        nt.links.new(mm.outputs[0], off.inputs[k])
    add = nt.nodes.new('ShaderNodeVectorMath')
    add.operation = 'ADD'
    nt.links.new(geo.outputs['Position'], add.inputs[0])
    nt.links.new(off.outputs['Vector'], add.inputs[1])
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.pi / 2 if along == 'x' else 0.0)
    mp.inputs['Scale'].default_value = (1 / 0.9, 1 / 2.2, 1 / 0.9)
    nt.links.new(add.outputs['Vector'], mp.inputs['Vector'])

    def img(key, nc):
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(maps[key], check_existing=True)
        if nc:
            t.image.colorspace_settings.name = 'Non-Color'
        t.projection = 'BOX'
        t.projection_blend = 0.15
        nt.links.new(mp.outputs['Vector'], t.inputs['Vector'])
        return t
    d = img('diffuse', False)
    # Grade the (bright orange) sapele scan to real ipe: normalise by the scan's mean colour, boost the grain
    # contrast, then multiply by a per-board colour picked from an ipe palette (Object Info Random), so the
    # deck reads as deep brown boards with the strong board-to-board variation of real ipe, not salmon.
    norm = nt.nodes.new('ShaderNodeVectorMath')
    norm.operation = 'DIVIDE'
    norm.inputs[1].default_value = SAPELE_MEAN
    nt.links.new(d.outputs['Color'], norm.inputs[0])
    con = nt.nodes.new('ShaderNodeVectorMath')
    con.operation = 'MULTIPLY_ADD'
    con.inputs[1].default_value = (IPE_GRAIN,) * 3
    con.inputs[2].default_value = (1.0 - IPE_GRAIN,) * 3
    nt.links.new(norm.outputs['Vector'], con.inputs[0])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    cr.elements[0].color = _srgb(IPE_PALETTE[0])
    cr.elements[1].position = 1.0
    cr.elements[1].color = _srgb(IPE_PALETTE[-1])
    for i, hx in enumerate(IPE_PALETTE[1:-1]):
        e = cr.elements.new((i + 1) / (len(IPE_PALETTE) - 1))
        e.color = _srgb(hx)
    nt.links.new(oi.outputs['Random'], ramp.inputs['Fac'])
    col = nt.nodes.new('ShaderNodeVectorMath')
    col.operation = 'MULTIPLY'
    nt.links.new(con.outputs['Vector'], col.inputs[0])
    nt.links.new(ramp.outputs['Color'], col.inputs[1])
    nt.links.new(col.outputs['Vector'], b.inputs['Base Color'])
    if 'rough' in maps:
        r_ = img('rough', True)
        rm = nt.nodes.new('ShaderNodeMapRange')
        rm.inputs['To Min'].default_value = 0.55
        rm.inputs['To Max'].default_value = 0.72
        nt.links.new(r_.outputs['Color'], rm.inputs['Value'])
        nt.links.new(rm.outputs['Result'], b.inputs['Roughness'])
    if 'nor_gl' in maps:
        n_ = img('nor_gl', True)
        nm = nt.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = 0.8
        nt.links.new(n_.outputs['Color'], nm.inputs['Color'])
        nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    try:
        b.inputs['Specular IOR Level'].default_value = 0.25
        b.inputs['Coat Weight'].default_value = 0.0
    except KeyError:
        pass
    m.diffuse_color = _srgb('#7a4a2d')
    return m


def deck(ctx, out):
    """The ipe deck outside the living room and the small landing outside the primary bedroom."""
    out['deck_boards'] = _platform(ctx, 'deck', L.DECK, rng(11)) + _platform(ctx, 'landing', L.LANDING, rng(12))


def _platform(ctx, tag, rect, r):
    """Ipe platform against the rear wall with a picture-frame border and a wrap-around step."""
    ipe = ipe_mat(ctx, 'x')
    ipe_z = ipe_mat(ctx, 'z')
    x0, x1, z0, z1 = rect
    top = L.DECK_TOP
    bw, gap, th = 0.458, 0.018, 0.075           # 5.5" boards, 3/16" gaps, 7/8" thick
    # dark substructure so board gaps read as shadow, not void
    sub = MB()
    sub.box(x0 - L.STEP_W + 0.05, x1 + L.STEP_W - 0.05, GRADE - 0.05, L.STEP_TOP - th - 0.01,
            z0 - L.STEP_W + 0.05, z1 - 0.01)
    sub.box(x0 + 0.05, x1 - 0.05, GRADE - 0.05, top - th - 0.01, z0 + 0.05, z1 - 0.01)
    sub.obj(ctx, f'ext {tag} substructure', flat_mat('Z_exterior_shadow', '#1d1a17', 0.95), SUB)
    n = 0

    def board(name, bx0, bx1, bz0, bz1, by):
        nonlocal n
        mb = MB()
        mb.box(bx0, bx1, by - th, by, bz0, bz1)
        mat = ipe if abs(bx1 - bx0) >= abs(bz1 - bz0) else ipe_z
        mb.obj(ctx, name, mat, SUB, bevel=0.012, segments=2)
        n += 1

    # picture-frame border boards (run along the edges), mitre simplified to butt joints
    fb = bw
    board(f'ext {tag} frame N', x0, x1, z0, z0 + fb, top)
    board(f'ext {tag} frame W', x0, x0 + fb, z0 + fb + gap, z1, top)
    board(f'ext {tag} frame E', x1 - fb, x1, z0 + fb + gap, z1, top)
    # field boards east-west, staggered butt joints
    fx0, fx1 = x0 + fb + gap, x1 - fb - gap
    z = z0 + fb + gap
    row = 0
    while z + bw <= z1 + 0.001:
        cut = fx0 + r.uniform(5.5, 12.5)
        if fx1 - fx0 < 14.0:                     # short run (landing): one board
            board(f'ext {tag} board {row}', fx0, fx1, z, z + bw, top)
        else:
            board(f'ext {tag} board {row}a', fx0, cut - gap / 2, z, z + bw, top)
            board(f'ext {tag} board {row}b', cut + gap / 2, fx1, z, z + bw, top)
        z += bw + gap
        row += 1
    # fill the last sliver against the house (ripped board)
    if z1 - z > 0.06:
        board(f'ext {tag} board rip', fx0, fx1, z, z1, top)
    # fascia (riser) boards around the platform edge, under the overhanging nosing
    fasc = MB()
    ft_ = 0.06
    fasc.box(x0 - 0.0, x1, L.STEP_TOP, top - th, z0, z0 + ft_)
    fasc.box(x0, x0 + ft_, L.STEP_TOP, top - th, z0, z1)
    fasc.box(x1 - ft_, x1, L.STEP_TOP, top - th, z0, z1)
    # wrap-around step: tread boards (2 per side) + step fascia
    sx0, sx1, sz0 = x0 - L.STEP_W, x1 + L.STEP_W, z0 - L.STEP_W
    st = L.STEP_TOP
    tb = (L.STEP_W - gap) / 2
    for k in range(2):
        a = sz0 + k * (tb + gap)
        board(f'ext {tag} step N {k}', sx0 + (k * (tb + gap)), sx1 - (k * (tb + gap)), a, a + tb, st)
        aw = sx0 + k * (tb + gap)
        board(f'ext {tag} step W {k}', aw, aw + tb, a + tb + gap, z1, st)
        ae = sx1 - k * (tb + gap) - tb
        board(f'ext {tag} step E {k}', ae, ae + tb, a + tb + gap, z1, st)
    fasc.box(sx0, sx1, GRADE - 0.02, st - th, sz0, sz0 + ft_)
    fasc.box(sx0, sx0 + ft_, GRADE - 0.02, st - th, sz0, z1)
    fasc.box(sx1 - ft_, sx1, GRADE - 0.02, st - th, sz0, z1)
    fasc.obj(ctx, f'ext {tag} fascia', ipe, SUB, bevel=0.008, segments=1)
    return n


# ---------------------------------------------------------------------------- soft surfaces
def soft_surfaces(ctx, out):
    soil = tex_mat('Z_exterior_lawn_soil', 'leafy_grass', 1.2, tint='#6f7a4a', value=0.55)   # thatch under the blades
    mulch = ctx.mat('soil_mulch')
    peb = ctx.mat('pebbles_river')
    lawns, beds, pebs = [], [], []
    top_lawn, top_bed, top_peb = GRADE, GRADE + 0.04, GRADE + 0.03
    for i, r in enumerate(L.LAWNS_REAR):
        lawns.append(_surface(ctx, f'ext lawn rear {i}', r, top_lawn, soil))
    lawns.append(_surface(ctx, 'ext lawn front', L.FRONT_LAWN, top_lawn, soil))
    for nm, r in (('rear', L.REAR_BED), ('west side', L.W_BED), ('east side', L.E_BED),
                  ('west front', L.W_FRONT_BED), ('front', L.FRONT_BED), ('east front 1', L.E_FRONT_BED1)):
        beds.append(_surface(ctx, f'ext bed {nm}', r, top_bed, mulch))
    beds.append(_surface(ctx, 'ext bed east front 2', L.E_FRONT_BED2, None, mulch,
                         hfn=lambda x, z: L.bank_top(x, z, L.E_BANK_X, L.DRIVE[1]), step=0.5))
    # pebble fields: blue-grey river pebbles in the back / side yards, black beach pebbles out front
    dark = ctx.mat('gravel_dark')
    rings = []
    for tag, (bx0, bx1, bz0, bz1), (px0, px1, pz0, _) in (('deck', L.DECK_BORDER, L.DECK),
                                                         ('landing', L.LANDING_BORDER, L.LANDING)):
        sx0, sx1, sz0 = px0 - L.STEP_W, px1 + L.STEP_W, pz0 - L.STEP_W
        rings += [(f'{tag} N', (bx0, bx1, bz0, sz0)), (f'{tag} W', (bx0, sx0, sz0, bz1)),
                  (f'{tag} E', (sx1, bx1, sz0, bz1))]
    for nm, r in rings + [('drip rear W', L.DRIPS[0]), ('drip rear E', L.DRIPS[1]), ('west side', L.W_PEB),
                          ('east side', L.E_PEB)]:
        ob = _surface(ctx, f'ext pebbles {nm}', r, top_peb, peb)
        ob['pebble'] = 'river'
        pebs.append(ob)
    for nm, r, hfn in (('walk', (L.CORRIDOR[0], L.STRIP[0], L.CORRIDOR[2], L.CORRIDOR[3]), None),
                       ('front strip', L.FRONT_STRIP, None),
                       ('bank', L.STRIP, lambda x, z: L.bank_top(x, z, L.STRIP[0], L.STRIP[1]))):
        ob = _surface(ctx, f'ext pebbles {nm}', r, top_peb, dark, hfn=hfn, step=0.5)
        ob['pebble'] = 'black'
        pebs.append(ob)
    # steel landscape edging between lawn and beds / pebbles
    steel = flat_mat('Z_exterior_steel_edging', '#2a2826', 0.55, 0.6)
    ed = MB()
    e0, e1 = GRADE - 0.06, GRADE + 0.08
    t = 0.02
    zb = L.REAR_BED[3]
    ed.box(L.REAR_BED[0], L.REAR_BED[1], e0, e1, zb - t, zb)
    for d in L.DRIPS:
        ed.box(d[0], d[1], e0, e1, d[2] - t, d[2])
    d = L.DRIPS[0]
    ed.box(d[0] - t, d[0], e0, e1, d[2], d[3])
    for (x0, x1, z0, z1) in (L.DECK_BORDER, L.LANDING_BORDER):
        ed.box(x0, x1, e0, e1, z0 - t, z0)
        ed.box(x0 - t, x0, e0, e1, z0, z1)
        ed.box(x1, x1 + t, e0, e1, z0, z1)
    # side yards: edging between pebble field and fence bed, and where lawn meets them
    ed.box(L.W_BED[1] - t / 2, L.W_BED[1] + t / 2, e0, e1, L.W_BED[2], L.W_BED[3])
    ed.box(L.E_BED[0] - t / 2, L.E_BED[0] + t / 2, e0, e1, L.E_BED[2], L.E_BED[3])
    ed.box(L.W_BED[0], L.HX0, e0, e1, L.HZ0 - t, L.HZ0)
    ed.box(L.HX1, L.E_BED[1], e0, e1, L.HZ0 - t, L.HZ0)
    fl = L.FRONT_LAWN
    ed.box(fl[0], fl[1], e0, e1, fl[2] - t, fl[2])
    ed.box(fl[1], fl[1] + t, e0, e1, fl[2], fl[3])
    ed.obj(ctx, 'ext steel edging', steel, SUB)
    out['lawns'], out['beds'], out['pebbles'] = lawns, beds, pebs


# ---------------------------------------------------------------------------- side pavers
def side_pavers(ctx):
    pav = varied(ctx, 'concrete_paver', 0.07, 'Z_exterior_paver_var')
    n = 0
    for (px0, px1), (zs, ze) in ((L.W_PAVERS_X, (L.HZ0 + 0.6, L.GATE_WZ - 0.6)),
                                 (L.E_PAVERS_X, (L.HZ0 + 0.6, L.GATE_EZ - 0.6))):
        z = zs
        while z + 2.0 <= ze:
            mb = MB()
            mb.box(px0, px1, GRADE - 0.15, GRADE + 0.09, z, z + 2.0)
            mb.obj(ctx, f'ext side paver {n}', pav, SUB, bevel=0.02, segments=2)
            n += 1
            z += 2.0 + 0.33
    return n


# ------------------------------------------------------------------------------ front walk
def porch_and_walk(ctx):
    pav = varied(ctx, 'concrete_paver', 0.06, 'Z_exterior_paver_var')
    px0, px1, pz0, pz1 = L.PORCH
    # porch slab block under the shell's porch paving (which stops ~0.4 ft short of the PDF's 7'-4"), wall to
    # wall and out under the two corner piers, with a clean front edge
    mb = MB()
    top = 0.035                                         # just under the paving top (0.04)
    mb.box(px0 - 0.17, px1 + 0.17, GRADE - 0.3, top, pz0 - 0.15, pz1)
    mb.box(L.PORCH_POSTS[0][0] - 0.05, L.PORCH_POSTS[1][1] + 0.05, GRADE - 0.3, top, L.PORCH_POSTS[0][2], pz1)
    mb.obj(ctx, 'ext porch slab', 'porch_pavers', SUB, bevel=0.015, segments=2)
    # the two 1'-5" stucco piers at the porch's front corners (SKA002), up to the eave soffit
    mb = MB()
    for (qx0, qx1, qz0, qz1) in L.PORCH_POSTS:
        mb.box(qx0, qx1, top, L.PORCH_SOFFIT, qz0, qz1)
    mb.obj(ctx, 'ext porch piers', 'stucco', SUB, bevel=0.02, segments=2)
    # covered porch (SKA001 "(N) COVERED PORCH"): a slim flat canopy on the piers, charcoal edges and a
    # standing-seam top like the house roof, warm wood soffit like the entry cladding
    x0, x1, z0, z1 = L.PORCH_ROOF
    ys, yt = L.PORCH_SOFFIT, L.PORCH_ROOF_TOP
    mb = MB()
    mb.box(x0, x1, ys, yt - 0.05, z0, z1)
    mb.obj(ctx, 'ext porch canopy fascia', 'fascia_charcoal', SUB, bevel=0.01, segments=1)
    mb = MB()
    mb.box(x0 + 0.02, x1 - 0.02, yt - 0.05, yt, z0, z1 - 0.02)
    mb.obj(ctx, 'ext porch canopy roof', 'roof_metal', SUB)
    mb = MB()
    mb.box(x0 + 0.18, x1 - 0.18, ys - 0.012, ys, z0 + 0.02, z1 - 0.18)
    mb.obj(ctx, 'ext porch canopy soffit', 'wood_cladding', SUB)
    wx0, wx1 = L.WALKWAY
    tops = [-0.21, -0.40]
    z = pz1 + 0.12
    n = 0
    for k, t in enumerate(tops):                       # two floating entry steps
        mb = MB()
        mb.box(wx0 - 0.25, wx1 + 0.25, GRADE - 0.25, t, z, z + 2.1)
        mb.obj(ctx, f'ext entry step {k}', pav, SUB, bevel=0.02, segments=2)
        z += 2.1 + 0.3
        n += 1
    while z + 2.0 <= L.SIDEWALK[0] - 0.3:              # large 4'6" x 2' pavers with pebble joints
        mb = MB()
        mb.box(wx0, wx1, GRADE - 0.2, GRADE + 0.08, z, z + 2.0)
        mb.obj(ctx, f'ext walk paver {n}', pav, SUB, bevel=0.02, segments=2)
        z += 2.0 + 0.4
        n += 1
    return n


def driveway(ctx):
    """Broom-finish concrete panels with 4" black beach-pebble joints (1077 W McKinley driveway look).
    Returns the joint surfaces (scattered with black pebbles by exterior_plants)."""
    conc = varied(ctx, 'concrete_drive', 0.05, 'Z_exterior_drive_var')
    x0, x1, z0, z1 = L.DRIVE
    joint = 0.34
    npan = 6
    pitch = (z1 - z0 + joint) / npan
    pw = pitch - joint
    joints = []
    for k in range(npan):
        a = z0 + k * pitch
        b = a + pw
        mb = MB()
        pts = [(x0, a), (x1, a), (x1, b), (x0, b)]
        mb.box_pts(pts, GRADE - 0.35, 0, ytop=[L.drive_top(a), L.drive_top(a), L.drive_top(b), L.drive_top(b)])
        mb.obj(ctx, f'ext driveway panel {k}', conc, SUB, bevel=0.02, segments=2)
        if k < npan - 1:
            j0, j1 = b, b + joint
            mb = MB()
            # pebbles (up to ~0.05 ft tall) fill the joint to just under flush, so the dark strips stay
            # visible from the street at grazing angles
            yt = [L.drive_top(j0) - 0.048] * 2 + [L.drive_top(j1) - 0.048] * 2
            mb.box_pts([(x0 + 0.01, j0 + 0.005), (x1 - 0.01, j0 + 0.005), (x1 - 0.01, j1 - 0.005),
                        (x0 + 0.01, j1 - 0.005)], GRADE - 0.3, 0, ytop=yt)
            ob = mb.obj(ctx, f'ext driveway joint {k}', 'gravel_dark', SUB)
            ob['pebble'] = 'black'
            joints.append(ob)
    return joints


# ------------------------------------------------------------------------------ street
def street(ctx, out):
    conc = varied(ctx, 'concrete_drive', 0.04, 'Z_exterior_walk_var')
    asphalt = tex_mat('Z_exterior_asphalt', 'asphalt_02', 2.5, tint='#9a9a9a', rough_mul=1.0)
    XA, XB = -420.0, 470.0
    # sidewalks: 5 ft scored panels (0.04 ft tooled gaps)
    for nm, (za, zb) in (('near', L.SIDEWALK), ('far', L.FAR_WALK)):
        mb = MB()
        x = XA
        while x < XB:
            mb.box(x + 0.02, x + 4.98, GRADE - 0.3, L.WALK_TOP, za, zb)
            x += 5.0
        mb.obj(ctx, f'ext sidewalk {nm}', conc, SUB)
    # driveway apron across the near park strip, sloping to the gutter lip
    dx0, dx1 = L.DRIVE[0] - 0.5, L.DRIVE[1] + 0.5
    mb = MB()
    a, b = L.PARK[0], L.CURB[1]
    mb.box_pts([(dx0, a), (dx1, a), (dx1, b), (dx0, b)], L.STREET_TOP - 0.4, 0,
               ytop=[L.WALK_TOP, L.WALK_TOP, L.STREET_TOP + 0.02, L.STREET_TOP + 0.02])
    mb.obj(ctx, 'ext driveway apron', conc, SUB, bevel=0.01, segments=1)
    # curbs + gutters (near: cut at the apron)
    cg = MB()
    for (xa, xb) in ((XA, dx0), (dx1, XB)):
        cg.box(xa, xb, L.STREET_TOP - 0.4, L.WALK_TOP, L.CURB[0], L.CURB[1])
    cg.box(XA, XB, L.STREET_TOP - 0.4, L.WALK_TOP, L.FAR_CURB[0], L.FAR_CURB[1])
    for (za, zb) in (L.GUTTER, L.FAR_GUTTER):
        cg.box(XA, XB, L.STREET_TOP - 0.4, L.STREET_TOP - 0.03, za, zb)
    cg.obj(ctx, 'ext curb and gutter', conc, SUB, bevel=0.03, segments=2)
    # asphalt with a gentle crown
    zc = (L.STREET[0] + L.STREET[1]) / 2
    mb = MB()
    mb.grid(XA, XB, L.STREET[0], L.STREET[1],
            lambda x, z: L.STREET_TOP + 0.15 * (1 - ((z - zc) / ((L.STREET[1] - L.STREET[0]) / 2)) ** 2),
            step=4.0)
    st = mb.obj(ctx, 'ext street asphalt', asphalt, SUB)
    for p in st.data.polygons:
        if p.normal.z < 0:
            p.flip()
    # park strips: dark gravel along our frontage, lawn elsewhere (gaps at driveway aprons)
    mb = MB()
    mb.box(L.FW, dx0, GRADE - 0.1, GRADE + 0.03, L.PARK[0], L.PARK[1])
    mb.box(dx1, L.FE, GRADE - 0.1, GRADE + 0.03, L.PARK[0], L.PARK[1])
    mb.obj(ctx, 'ext park strip gravel', 'gravel_dark', SUB)
    lawn = MB()
    near = (NEAR_LAWN_X[0], NEAR_LAWN_X[1])
    lawn.box(XA, near[0], GRADE - 0.1, GRADE + 0.0, L.PARK[0], L.PARK[1])
    lawn.box(near[1], XB, GRADE - 0.1, GRADE + 0.0, L.PARK[0], L.PARK[1])
    lawn.box(XA, XB, GRADE - 0.1, GRADE + 0.0, L.FAR_PARK[0], L.FAR_PARK[1])
    lawn.obj(ctx, 'ext park strip lawn', far_lawn_mat(), SUB)
    # real (instanced) grass where hero shots and the front windows see it up close: the neighbours'
    # park strips next to ours and the two side neighbours' front lawns
    soil = tex_mat('Z_exterior_lawn_soil', 'leafy_grass', 1.2, tint='#6f7a4a', value=0.55)
    for i, r in enumerate([(near[0], L.FW, L.PARK[0], L.PARK[1]), (L.FE, near[1], L.PARK[0], L.PARK[1])] +
                          NEIGHBOUR_LAWNS):
        out.setdefault('lawns', []).append(_surface(ctx, f'ext lawn neighbour {i}', r, GRADE, soil))
    return 1


NEAR_LAWN_X = (-60.0, 110.0)
_F, _S = L.FRONT_DZ, L.SIDEWALK[0] - 0.1
NEIGHBOUR_LAWNS = [(-55.0, -31.0, 44.6 + _F, _S), (-15.0, L.FW - 0.15, 50.3 + _F, _S),     # west neighbour front yard
                   (L.FE + 0.1, 55.0, 50.3 + _F, _S), (71.0, 100.0, 45.6 + _F, _S)]      # east neighbour front yard


# extra x-ranges to leave open in the near park strip (neighbour aprons sit on top of the lawn instead)
APRONS = []


def build(ctx):
    out = {}
    ground(ctx)
    plinth(ctx)
    deck(ctx, out)
    soft_surfaces(ctx, out)
    out['side_pavers'] = side_pavers(ctx)
    out['walk'] = porch_and_walk(ctx)
    out['pebbles'] = out.get('pebbles', []) + driveway(ctx)
    street(ctx, out)
    return out
