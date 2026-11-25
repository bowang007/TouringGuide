"""Grounds and hardscape: ground planes, foundation plinth, lawn/bed/pebble surfaces, the two rear landings
(a platform and one step at each sliding door; the ipe deck until the seventh round), side-yard pavers, the
porch slab with one riser to the walk, front walk, driveway with gravel joints, sidewalk, curb, gutter and
street (runs inside Blender).   (v7 final: comment, it listed the deck and a porch block with entry steps)"""
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


# v7 site: the ground follows sheet A1.3 (L.grade: 1'-2" below the floor behind the house, 11 in in front of it,
# a 3 in rise along both sides). What lies on the ground is built against that line.
_BREAKS = (L.HZ0, L.GARAGE_FRONT)          # where the ground line bends


def _gbox(mb, x0, x1, d0, d1, z0, z1, mi=0):
    """Box lying on the ground: its top is d1 above the ground line and follows it (the box is split where the
    line bends), its bottom is level, d0 above the lowest ground under it."""
    x0, x1 = min(x0, x1), max(x0, x1)
    z0, z1 = min(z0, z1), max(z0, z1)
    zs = [z0] + [b for b in _BREAKS if z0 + 1e-6 < b < z1 - 1e-6] + [z1]
    y0 = min(L.grade(z0), L.grade(z1)) + d0
    for a, b in zip(zs[:-1], zs[1:]):
        ta, tb = L.grade(a) + d1, L.grade(b) + d1
        mb.box_pts([(x0, a), (x1, a), (x1, b), (x0, b)], y0, 0, mi, ytop=[ta, ta, tb, tb])


def _ground_surface(ctx, name, r, d, mat, thick=0.08):
    """Surface slab over rect r whose top is d above the ground line. Returns the object (used for scattering)."""
    x0, x1, z0, z1 = r
    mb = MB()
    _gbox(mb, x0, x1, d - thick, d, z0, z1)
    return mb.obj(ctx, name, mat, SUB)


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
    d = -0.02
    # v7 site: three strips along the ground line (level behind the house, the 3 in rise beside it, level in
    # front), 0.02 ft under it behind the house and 0.09 ft in front, where the gravel round the walk and in the
    # driveway's joints lies 0.05 ft under the line. The street right-of-way (sidewalk .. far park strip) is
    # modelled separately (street()); what lies south of it sits as far below the sidewalk as before (L.ROW_DROP).
    zs = [(-E, d), (L.HZ0, d), (L.GARAGE_FRONT, -0.09), (L.SIDEWALK[0], -0.09)]
    for (a, da), (b, db) in zip(zs[:-1], zs[1:]):
        ya, yb = L.grade(a) + da, L.grade(b) + db
        mb.quad((-E, ya, a), (E, ya, a), (E, yb, b), (-E, yb, b))
    y = L.FLAT + L.ROW_DROP + d
    mb.quad((-E, y, L.FAR_PARK[0]), (E, y, L.FAR_PARK[0]), (E, y, E), (-E, y, E))
    # v7 repair: ground under the street right-of-way too, below everything that is modelled there (the curbs'
    # feet are at -1.767). There was nothing: the sidewalk's tooled joints were slots open through to the void.
    yr = L.STREET_Y - 0.45
    mb.quad((-E, yr, L.SIDEWALK[0]), (E, yr, L.SIDEWALK[0]), (E, yr, L.FAR_PARK[0]), (-E, yr, L.FAR_PARK[0]))
    y0 = L.grade(L.SIDEWALK[0]) - 0.09                  # ... closed against the ground on both sides
    mb.quad((-E, y0, L.SIDEWALK[0]), (E, y0, L.SIDEWALK[0]), (E, yr, L.SIDEWALK[0]), (-E, yr, L.SIDEWALK[0]))
    mb.quad((-E, yr, L.FAR_PARK[0]), (E, yr, L.FAR_PARK[0]), (E, y, L.FAR_PARK[0]), (-E, y, L.FAR_PARK[0]))
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


def bay_outline():
    """Plan outline (convex, [(x, z), ...]) of Bedroom 3's canted bay, from its stucco plinth. The shell is still
    on the concept plan while the exterior builds (bl/warp.py carries it over afterwards), so the points are
    mapped the same way. [] when the shell has no bay."""
    from ..warp import R as relayout
    pts = []
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and 'Bay stucco plinth' in ob.name:
            for v in ob.data.vertices:
                x, y, z = bl2ft(ob.matrix_world @ v.co)
                x, z = relayout.remap_xz(x, z)
                pts.append((round(x, 4), round(z, 4)))
    return _hull(pts) if pts else []


# v7 site: the walls below the floor line. The floor is 11 in (front) to 1'-2" (rear) above the ground now, so the
# stucco is carried down from the walls' feet (y 0) to a level screed line 6 in above the front grade, flush with
# the wall faces all round, and the concrete foundation shows below it, 0.01 ft back: 6 in of it at the front,
# 9 in at the rear. Both are bands under the outer half of the walls (the floor slabs end on the walls' centre
# lines), mitred at the corners. The garage's floor is 11 in below the house's: bl/garage.py carries the inside
# finish of its walls down on bases under their inner half and cuts away whatever of the site stands in the
# lowered room (a boolean, so every piece here is an object of its own, one closed prism). The bands stop at
# the vehicle door (15'-0", sheet DR19) and at the side door (2'-8", sheet DR18); a sill 0.03 ft under the
# garage floor runs through under both.
SCREED_Y = L.GRADE_FRONT + 0.5            # -0.417: foot of the stucco (weep screed), level all round
PLINTH_E = 0.01                           # the concrete stands this far behind the stucco face
BASE_W = 0.2                              # depth of the bands behind the outer face (just short of the wall's middle)
VEHICLE_DOOR = (min(L.GARAGE_DOOR[0], L.R.X_GAR_W + 1.25), max(L.GARAGE_DOOR[1], L.R.X_GAR_W + 16.25))   # 22.975..37.975
SIDE_DOOR_Z = (L.R.Z_GAR_N + 4.0 + 2.0 / 12.0, L.R.Z_GAR_N + 6.0 + 10.0 / 12.0)                       # 35.642..38.308


def _inset(poly, e):
    """Plan polygon [(x, z), ...] with every edge moved inwards by e (outwards when e is negative)."""
    n = len(poly)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        d1 = (p1[0] - p0[0], p1[1] - p0[1])
        d2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*d1), math.hypot(*d2)
        n1 = (-d1[1] / l1 * sgn, d1[0] / l1 * sgn)          # inward normals of the two edges at p1
        n2 = (-d2[1] / l2 * sgn, d2[0] / l2 * sgn)
        k = e / max(1.0 + n1[0] * n2[0] + n1[1] * n2[1], 1e-6)
        out.append((p1[0] + (n1[0] + n2[0]) * k, p1[1] + (n1[1] + n2[1]) * k))
    return out


def _ring(poly, w0, w1, cuts=None):
    """Band along the plan polygon `poly`, between its edges moved inwards by w0 and by w1, mitred at the
    corners: a list of four-sided plan pieces, one per edge. cuts {edge index: (c0, c1)}: the band is left open
    between c0 and c1 of the coordinate that runs along that (axis-parallel) edge, with square ends."""
    a, b = (_inset(poly, w0) if w0 else list(poly)), _inset(poly, w1)
    n = len(poly)
    out = []
    for i in range(n):
        j = (i + 1) % n
        A, B, C, D = a[i], a[j], b[i], b[j]
        cut = (cuts or {}).get(i)
        if not cut:
            out.append([A, B, D, C])
            continue
        k = 0 if abs(poly[j][0] - poly[i][0]) > abs(poly[j][1] - poly[i][1]) else 1    # coordinate along the edge
        c0, c1 = cut if poly[j][k] > poly[i][k] else (cut[1], cut[0])

        def at(q, c):
            return (c, q[1]) if k == 0 else (q[0], c)
        out += [[A, at(A, c0), at(C, c0), C], [at(B, c1), B, D, at(D, c1)]]
    return out


def house_outline():
    """Outer faces of the house and the garage: rear west corner, rear east corner, on round the garage, the
    porch recess and Bedroom 3's front. Edge 1 is the east wall (with the garage's side door), edge 2 the garage
    front (with the vehicle door)."""
    return [(L.HX0, L.HZ0), (L.HX1, L.HZ0), (L.HX1, L.GARAGE_FRONT), (L.PORCH[1], L.GARAGE_FRONT),
            (L.PORCH[1], L.PORCH[2]), (L.PORCH[0], L.PORCH[2]), (L.PORCH[0], L.BED3_FRONT), (L.HX0, L.BED3_FRONT)]


def plinth(ctx):
    """The walls below the floor line: stucco down to the screed line, the concrete foundation below it."""
    yb = L.GRADE_REAR - 0.5
    sill = L.GRADE_FRONT - 0.03
    out = house_outline()
    cuts = {1: SIDE_DOOR_Z, 2: VEHICLE_DOOR}
    # v7 repair: in the porch's recess the stucco runs down to the porch slab, which lies below the screed line
    # since the slab stands half way between walk and floor (the concrete would show for 1/2 in above the slab)
    px0, px1, pz0, _pz1 = L.PORCH

    def in_porch(q):
        return all(px0 - BASE_W - 0.01 < x < px1 + BASE_W + 0.01 and z > pz0 - BASE_W - 0.01 for x, z in q)

    def base_y(q):
        return min(SCREED_Y, L.PORCH_TOP - 0.03) if in_porch(q) else SCREED_Y
    # ... and the two side walls' bands end where the piers begin: they ran on to the front corners, IN the plane of
    # the piers' porch faces (two stucco faces in one plane at each pier's foot, a patch that showed once the
    # baseboards were gone). The piers stand in those corners down to the slab.
    zp_w, zp_e = L.PORCH_POSTS[0][2], L.PORCH_POSTS[1][2]

    def porch_clip(q):
        if not in_porch(q):
            return q
        return [(x, min(z, zp_w if x < (px0 + px1) / 2 else zp_e)) for x, z in q]
    pieces = [('ext wall base', 'stucco', porch_clip(q), base_y(q), 0.0) for q in _ring(out, 0.0, BASE_W, cuts)]
    pieces += [('ext foundation plinth', 'foundation', q, sill, SCREED_Y) for q in _ring(out, PLINTH_E, BASE_W, cuts)]
    pieces += [('ext foundation plinth low', 'foundation', q, yb, sill) for q in _ring(out, PLINTH_E, BASE_W)]
    hull = bay_outline()                  # the canted bay's outline from its stucco plinth
    if hull:
        pieces.append(('ext wall base bay', 'stucco', hull, SCREED_Y, -0.025))
        pieces.append(('ext foundation plinth bay', 'foundation', _inset(hull, PLINTH_E), yb, SCREED_Y))
    for i, (name, mat, pts, y0, y1) in enumerate(pieces):
        mb = MB()
        mb.box_pts(pts, y0, y1)
        mb.obj(ctx, f'{name} {i:02d}', mat, SUB)
    return len(pieces)


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
    """The two ipe landings of the sheet: outside the living room's sliding door ('deck', 13'-0" x 3'-0") and
    outside the primary bedroom's ('landing', 7'-0" x 3'-0"). v7 site: tops 1 in below the floor, one step
    all round, two risers of 6 1/2 in down to the rear ground."""
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
    g = L.GRADE_REAR                                # v7 site: the landings stand on the rear ground
    sub.box(x0 - L.STEP_W + 0.05, x1 + L.STEP_W - 0.05, g - 0.05, L.STEP_TOP - th - 0.01,
            z0 - L.STEP_W + 0.05, z1 - 0.01)
    sub.box(x0 + 0.05, x1 - 0.05, g - 0.05, top - th - 0.01, z0 + 0.05, z1 - 0.01)
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
    fasc.box(sx0, sx1, g - 0.02, st - th, sz0, sz0 + ft_)
    fasc.box(sx0, sx0 + ft_, g - 0.02, st - th, sz0, z1)
    fasc.box(sx1 - ft_, sx1, g - 0.02, st - th, sz0, z1)
    fasc.obj(ctx, f'ext {tag} fascia', ipe, SUB, bevel=0.008, segments=1)
    return n


# ---------------------------------------------------------------------------- soft surfaces
def soft_surfaces(ctx, out):
    soil = tex_mat('Z_exterior_lawn_soil', 'leafy_grass', 1.2, tint='#6f7a4a', value=0.55)   # thatch under the blades
    mulch = ctx.mat('soil_mulch')
    peb = ctx.mat('pebbles_river')
    lawns, beds, pebs = [], [], []
    # v7 site: heights above the ground line (L.grade). The front walk and the driveway lie on the line itself,
    # so the gravel between them and along the sidewalk lies 0.05 ft under it (the stones come up to it).
    top_lawn, top_bed, top_peb, top_joint = 0.0, 0.04, 0.03, -0.05
    for i, r in enumerate(L.LAWNS_REAR):
        lawns.append(_ground_surface(ctx, f'ext lawn rear {i}', r, top_lawn, soil))
    to_fence = L.SURFACE_TO_FENCE                       # v7 repair: surfaces run on under the fences
    lawns.append(_ground_surface(ctx, 'ext lawn front', to_fence.get('lawn front', L.FRONT_LAWN), top_lawn, soil))
    for nm, r in (('rear', L.REAR_BED), ('west side', L.W_BED), ('east side', L.E_BED),
                  ('west front', L.W_FRONT_BED), ('front', L.FRONT_BED), ('east front 1', L.E_FRONT_BED1),
                  ('east front 2', L.E_FRONT_BED2)):       # (east front 2 banked up to the driveway's edge)
        beds.append(_ground_surface(ctx, f'ext bed {nm}', to_fence.get(f'bed {nm}', r), top_bed, mulch))
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
        ob = _ground_surface(ctx, f'ext pebbles {nm}', to_fence.get(f'pebbles {nm}', r), top_peb, peb)
        ob['pebble'] = 'river'
        pebs.append(ob)
    for nm, r in (('walk', (L.CORRIDOR[0], L.STRIP[0], L.CORRIDOR[2], L.CORRIDOR[3])),
                  ('front strip', L.FRONT_STRIP),
                  ('bank', L.STRIP)):                      # (the strip between walk and driveway: level now)
        ob = _ground_surface(ctx, f'ext pebbles {nm}', to_fence.get(f'pebbles {nm}', r), top_joint, dark)
        ob['pebble'] = 'black'
        pebs.append(ob)
    # steel landscape edging between lawn and beds / pebbles
    steel = flat_mat('Z_exterior_steel_edging', '#2a2826', 0.55, 0.6)
    ed = MB()
    e0, e1 = -0.06, 0.08                              # (against the ground line)
    t = 0.02
    zb = L.REAR_BED[3]
    _gbox(ed, L.REAR_BED[0], L.REAR_BED[1], e0, e1, zb - t, zb)
    for d in L.DRIPS:
        _gbox(ed, d[0], d[1], e0, e1, d[2] - t, d[2])
    d = L.DRIPS[0]
    _gbox(ed, d[0] - t, d[0], e0, e1, d[2], d[3])
    for (x0, x1, z0, z1) in (L.DECK_BORDER, L.LANDING_BORDER):
        _gbox(ed, x0, x1, e0, e1, z0 - t, z0)
        _gbox(ed, x0 - t, x0, e0, e1, z0, z1)
        _gbox(ed, x1, x1 + t, e0, e1, z0, z1)
    # side yards: edging between pebble field and fence bed, and where lawn meets them
    _gbox(ed, L.W_BED[1] - t / 2, L.W_BED[1] + t / 2, e0, e1, L.W_BED[2], L.W_BED[3])
    _gbox(ed, L.E_BED[0] - t / 2, L.E_BED[0] + t / 2, e0, e1, L.E_BED[2], L.E_BED[3])
    _gbox(ed, L.W_BED[0], L.HX0, e0, e1, L.HZ0 - t, L.HZ0)
    _gbox(ed, L.HX1, L.E_BED[1], e0, e1, L.HZ0 - t, L.HZ0)
    fl = L.FRONT_LAWN
    _gbox(ed, fl[0], fl[1], e0, e1, fl[2] - t, fl[2])
    _gbox(ed, fl[1], fl[1] + t, e0, e1, fl[2], fl[3])
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
            _gbox(mb, px0, px1, -0.15, 0.09, z, z + 2.0)
            mb.obj(ctx, f'ext side paver {n}', pav, SUB, bevel=0.02, segments=2)
            n += 1
            z += 2.0 + 0.33
    return n


# ------------------------------------------------------------------------------ front walk
def porch_and_walk(ctx):
    pav = varied(ctx, 'concrete_paver', 0.06, 'Z_exterior_paver_var')
    px0, px1, pz0, pz1 = L.PORCH
    # v7 site: the porch slab is the porch's floor (A1.3: 4 in below the house floor; the shell's porch paving
    # at floor level is taken out by bl/revisions.site_shell): wall to wall on the sheet's lines (5'-0" beside
    # the garage + 2'-4" in front of it) and out under the two corner piers, one piece with a clean front edge
    # that is the entry's single riser, 7 in down to the front walk
    mb = MB()
    top = L.PORCH_TOP                                   # -0.458 (v7 repair: was -0.336); the piers stand on it
    wx0p, ex1p = L.PORCH_POSTS[0][0] - 0.05, L.PORCH_PAD[1]
    # v7 integrate: under the two piers the slab runs 0.03 ft into the front walls' line. It ended ON the line, and
    # the foundation band beside it stands 0.01 ft behind that line: a 1/8 in dark slit showed at each pad's outer
    # corner (beside the driveway and beside the bay's bed).
    lap = 0.03
    mb.box_pts([(px0 - 0.17, pz0 - 0.15), (px1 + 0.17, pz0 - 0.15), (px1 + 0.17, L.PORCH_PAD[2] - lap),
                (ex1p, L.PORCH_PAD[2] - lap), (ex1p, pz1), (wx0p, pz1), (wx0p, L.BED3_FRONT - lap),
                (px0 - 0.17, L.BED3_FRONT - lap)],
               L.GRADE_FRONT - 0.3, top)
    # v7 repair: pavers on the top only; the slab's edge (the riser, the pads' sides) is plain concrete. The paver
    # texture's grout lines ran down the vertical faces as dark lines.
    mb.mi = [0 if k == 1 else 1 for k in range(len(mb.f))]         # box_pts: face 0 bottom, 1 top, then the sides
    mb.obj(ctx, 'ext porch slab', ['porch_pavers', 'foundation'], SUB, bevel=0.015, segments=2)
    # the two 1'-5" stucco piers at the porch's front corners (SKA002), up to the eave soffit
    mb = MB()
    for (qx0, qx1, qz0, qz1) in L.PORCH_POSTS:
        mb.box(qx0, qx1, top, L.PORCH_SOFFIT, qz0, qz1)
    mb.obj(ctx, 'ext porch piers', 'stucco', SUB, bevel=0.02, segments=2)
    # v7 roof: no flat canopy any more. The covered porch (SKA001 "(N) COVERED PORCH") is under the entry gable,
    # which runs on to 1'-0" past the slab's front edge (bl/roof.py, after the warp): it raises these two piers to
    # the roof's underside (their tops here are only where they start from) and builds the tie beam, the king post
    # and the wood soffit.
    wx0, wx1 = L.WALKWAY
    # v7 site: the walk lies on the front ground line (-0.917), one 7 in riser below the porch. A 5'-0" x 2'-1"
    # landing paver at the foot of the porch's edge (it runs under the edge; the two floating entry pads with
    # their 3.0 / 2.3 / 1.4 in risers are gone), then the 4'-6" x 2'-0" pavers with pebble joints.
    z = pz1
    mb = MB()
    _gbox(mb, wx0 - 0.25, wx1 + 0.25, -0.25, 0.0, z - 0.05, z + 2.1)
    mb.obj(ctx, 'ext walk paver 0', pav, SUB, bevel=0.02, segments=2)
    z += 2.1 + 0.4
    n = 1
    while z + 2.0 <= L.SIDEWALK[0] - 0.3:              # large 4'6" x 2' pavers with pebble joints
        mb = MB()
        _gbox(mb, wx0, wx1, -0.2, 0.0, z, z + 2.0)
        mb.obj(ctx, f'ext walk paver {n}', pav, SUB, bevel=0.02, segments=2)
        z += 2.0 + 0.4
        n += 1
    return n


def driveway(ctx):
    """Broom-finish concrete panels with 4" black beach-pebble joints (1077 W McKinley driveway look).
    Returns the joint surfaces (scattered with black pebbles by exterior_plants).
    v7 site: 18'-1" wide (L.DRIVE) and level on the front ground line, from the garage slab to the sidewalk. The
    first panel runs in under the vehicle door between its jambs, to where the garage's slab ends (bl/garage.py
    ends it on L.DRIVE[2]), and round the porch slab under the east pier."""
    conc = varied(ctx, 'concrete_drive', 0.05, 'Z_exterior_drive_var')
    x0, x1, z0, z1 = L.DRIVE
    joint = 0.34
    npan = 6
    pitch = (z1 - z0 + joint) / npan
    pw = pitch - joint
    joints = []
    gb = L.GRADE_FRONT
    for k in range(npan):
        a = z0 + k * pitch
        b = a + pw
        mb = MB()
        if k == 0:
            jw, je = VEHICLE_DOOR
            gf, pad_x1, pad_z1 = L.GARAGE_FRONT, L.PORCH_PAD[1], L.PORCH_PAD[3]
            pts = [(jw, a), (je, a), (je, gf), (x1, gf), (x1, b), (x0, b), (x0, pad_z1), (pad_x1, pad_z1),
                   (pad_x1, gf), (jw, gf)]
            mb.box_pts(pts, gb - 0.35, 0, ytop=[L.drive_top(q[1]) for q in pts])
        else:
            pts = [(x0, a), (x1, a), (x1, b), (x0, b)]
            mb.box_pts(pts, gb - 0.35, 0, ytop=[L.drive_top(a), L.drive_top(a), L.drive_top(b), L.drive_top(b)])
        mb.obj(ctx, f'ext driveway panel {k}', conc, SUB, bevel=0.02, segments=2)
        if k < npan - 1:
            j0, j1 = b, b + joint
            mb = MB()
            # pebbles (up to ~0.05 ft tall) fill the joint to just under flush, so the dark strips stay
            # visible from the street at grazing angles
            yt = [L.drive_top(j0) - 0.048] * 2 + [L.drive_top(j1) - 0.048] * 2
            mb.box_pts([(x0 + 0.01, j0 + 0.005), (x1 - 0.01, j0 + 0.005), (x1 - 0.01, j1 - 0.005),
                        (x0 + 0.01, j1 - 0.005)], gb - 0.3, 0, ytop=yt)
            ob = mb.obj(ctx, f'ext driveway joint {k}', 'gravel_dark', SUB)
            ob['pebble'] = 'black'
            joints.append(ob)
    return joints


# ------------------------------------------------------------------------------ street
def street(ctx, out):
    # (v7 site: modelled on the level site, L.FLAT / L.WALK_TOP / L.STREET_TOP; settle() sets it down)
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


# ------------------------------------------------------------------------------ v7 site: settle
# What is modelled on the level site (L.FLAT, -0.60): the street, the fences and gates, the planting, the
# mailbox and the whole neighbourhood. settle() sets all of it down on the real ground (L.settle_dy): 6.8 in
# behind the house, 3.8 in in front of it, 4.4 in from the sidewalk on, with the 3 in rise in between.
SETTLE_SITE = r'^ext (sidewalk|driveway apron|curb and gutter|street asphalt|park strip|lawn neighbour)'
SETTLE_LIGHTS = r'^ext mailbox'


def settle(ctx):
    """Runs last in the exterior zone. A mesh of its own is lowered vertex by vertex (it follows the rise beside
    the house), an instance or a shared mesh as a whole, by the ground under its origin."""
    import re

    import numpy as np

    from .exterior_util import coll
    todo = []
    for sub, pat in (('fence', None), ('plants', None), ('context', None), ('far', None),
                     ('site', SETTLE_SITE), ('lights', SETTLE_LIGHTS)):
        rx = re.compile(pat) if pat else None
        todo += [ob for ob in coll(ctx, sub).all_objects if rx is None or rx.search(ob.name)]
    row_z = L.SIDEWALK[0] + 1e-3
    out = {'meshes': 0, 'placed': 0}
    for ob in todo:
        if ob.parent is not None:
            continue
        own = ob.type == 'MESH' and ob.data.users == 1 and len(ob.data.vertices) and not ob.get('tg_settled')
        if not own:
            if ob.get('tg_settled'):
                continue
            ob.location.z += L.settle_dy(-ob.location.y / FT) * FT
            ob['tg_settled'] = 1
            out['placed'] += 1
            continue
        me = ob.data
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        m = np.array(ob.matrix_basis)
        w = co @ m[:3, :3].T + m[:3, 3]
        z = -w[:, 1] / FT
        t = np.clip((z - L.HZ0) / (L.GARAGE_FRONT - L.HZ0), 0.0, 1.0)
        dy = L.GRADE_REAR + (L.GRADE_FRONT - L.GRADE_REAR) * t - L.FLAT
        if z.min() >= L.SIDEWALK[0] - 1e-3:                 # wholly in the right-of-way or south of it
            dy[:] = L.ROW_DROP
        else:
            dy = np.where(z > row_z, L.ROW_DROP, dy)
        w[:, 2] += dy * FT
        inv = np.linalg.inv(m)
        me.vertices.foreach_set('co', (w @ inv[:3, :3].T + inv[:3, 3]).ravel())
        me.update()
        ob['tg_settled'] = 1
        out['meshes'] += 1
    return out


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
