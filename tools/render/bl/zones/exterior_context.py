"""Distant context so window views read as a lived-in Sunnyvale street (runs inside Blender).

Neighbouring single-storey ranch houses with real-house detail where the tour sees them (the front door
E0/H1/H2/GA, the bedroom-3 bay B3/T4/A3, the garden L0/L1/P0/B2 and the hero stills):

- walls: horizontal lap siding (a bevelled course profile with drip-edge shadow lines and per-board tone)
  or sand-finish stucco, colour varied per house; gable ends; foundation band.
- roofs: hip or gable, shingle texture tinted per house, fascia, boxed soffits, rake boards, ridge caps,
  K-style gutters and downspouts; eave height and pitch vary per house.
- openings: windows with a projecting casing (so the dark reflective glass reads ~3in recessed), vinyl
  frames, meeting rails, colonial grids / shutters on some houses; sectional garage doors with raised
  panels, recessed behind jamb trim and weathered at the bottom; front doors in a recessed porch.
- massing: some houses get a front-projecting garage wing with a street-facing gable.
- across-the-street lots: concrete driveway (stained) and walk, mulched foundation beds with evergreen
  shrubs and grasses, real instanced lawn where the windows see it, a front-yard tree, side-yard fences
  with gates between the houses, a couple of parked cars and bins.
- neighbourhood trees (backyards, street, far canopy).
"""
import math

import bpy

from ..common import FT
from . import exterior_layout as L
from .exterior_context_car import place_car
from .exterior_plants import _gn_scatter, place_proc, plant, proc_plant, scatter
from .exterior_util import GRADE, MB, _srgb, flat_mat, mul_copy, rng, tex_mat, varied

SUB = 'context'

SIDING = ['#8e9ba2', '#a5ab93', '#b8b1a2', '#e2e0d8', '#a39889', '#75838a', '#d3cbb0', '#c3c6c1']
STUCCO = ['#ddd4c2', '#e6e2d7', '#cbbea6', '#c9c3b5', '#d7cab1']
TRIMS = ['#efede7', '#e8e4d9', '#f2f1ed', '#3c3e40']
ROOFS = ['#626262', '#8d8a86', '#7a6c60', '#4a4a4c']
GDOORS = ['#ebe8e1', '#ddd6c8', '#4a3f37', '#3a3c3e', '#f0efeb']
DOORS = ['#2e3a44', '#5a4433', '#6b2b27', '#2f3b31', '#1f2123', '#7b6a55']
SHUTTERS = ['#2b3530', '#22272c', '#3a3f45']
# houses whose front yards the windows look into get instanced lawn (others: lawn-coloured ground)
GRASS_X = (-80.0, 112.0)


# ----------------------------------------------------------------------------------- materials
def _tinted(ctx, key, hexcol, name):
    """Library material copy with its base colour multiplied by a tint (keeps any texture detail)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = ctx.mat(key).copy()
    m.name = name
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if b is None:
        return m
    s = b.inputs['Base Color']
    t = _srgb(hexcol)
    if s.is_linked:
        mix = nt.nodes.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs['Factor'].default_value = 1.0
        nt.links.new(s.links[0].from_socket, mix.inputs['A'])
        # stucco base is ~ #eeece6: normalise so the tint is the final colour
        mix.inputs['B'].default_value = tuple(min(1.0, c / 0.85) for c in t[:3]) + (1,)
        nt.links.new(mix.outputs['Result'], s)
    else:
        s.default_value = t
    m.diffuse_color = t
    return m


def _math(nt, op, a, b=None):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _maprange(nt, v, f0, f1, t0, t1, smooth=False):
    n = nt.nodes.new('ShaderNodeMapRange')
    if smooth:
        n.interpolation_type = 'SMOOTHSTEP'
    n.inputs['From Min'].default_value = f0
    n.inputs['From Max'].default_value = f1
    n.inputs['To Min'].default_value = t0
    n.inputs['To Max'].default_value = t1
    nt.links.new(v, n.inputs['Value'])
    return n.outputs['Result']


def _mulcol(nt, col, fac):
    """colour (socket or rgba) * scalar socket."""
    n = nt.nodes.new('ShaderNodeVectorMath')
    n.operation = 'SCALE'
    if isinstance(col, tuple):
        n.inputs[0].default_value = col[:3]
    else:
        nt.links.new(col, n.inputs[0])
    nt.links.new(fac, n.inputs['Scale'])
    return n.outputs['Vector']


def siding_mat(name, hexcol, expo=0.58, rough=0.72):
    """Painted horizontal lap siding (world-space, any wall): each course is thickest at its drip edge
    and thins upward (bump), with a soft shadow band under every drip edge, a per-board tone and a
    large-scale weathering noise. expo = course exposure in ft (7in)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    dv = _math(nt, 'DIVIDE', sep.outputs['Z'], expo * FT)
    fr = _math(nt, 'FRACT', dv)
    fl = _math(nt, 'FLOOR', dv)
    h = _math(nt, 'SUBTRACT', 1.0, fr)
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = 0.012
    nt.links.new(h, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    shade = _maprange(nt, fr, 0.78, 1.0, 1.0, 0.6, smooth=True)
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.noise_dimensions = '1D'
    nt.links.new(fl, wn.inputs['W'])
    tone = _maprange(nt, wn.outputs['Value'], 0.0, 1.0, 0.955, 1.045)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.7
    nz.inputs['Detail'].default_value = 3.0
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    weather = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0.93, 1.03)
    f = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', shade, tone), weather)
    nt.links.new(_mulcol(nt, _srgb(hexcol), f), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    try:
        b.inputs['Specular IOR Level'].default_value = 0.4
    except KeyError:
        pass
    m.diffuse_color = _srgb(hexcol)
    return m


def board_fence_mat(name='Z_exterior_nb_fence', hexcol='#7d6a55', width=0.47):
    """Weathered vertical-board wood fence: board stripes along x+y (works for fences running along x or z),
    dark gaps between boards, per-board tone and grain noise."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    u = _math(nt, 'DIVIDE', _math(nt, 'ADD', sep.outputs['X'], sep.outputs['Y']), width * FT)
    fr = _math(nt, 'FRACT', u)
    gap = _maprange(nt, fr, 0.9, 0.97, 1.0, 0.35, smooth=True)
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.noise_dimensions = '1D'
    nt.links.new(_math(nt, 'FLOOR', u), wn.inputs['W'])
    tone = _maprange(nt, wn.outputs['Value'], 0.0, 1.0, 0.82, 1.12)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 4.0
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (6.0, 6.0, 0.4)
    nt.links.new(geo.outputs['Position'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    grain = _maprange(nt, nz.outputs['Fac'], 0.3, 0.7, 0.85, 1.08)
    f = _math(nt, 'MULTIPLY', _math(nt, 'MULTIPLY', gap, tone), grain)
    nt.links.new(_mulcol(nt, _srgb(hexcol), f), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    m.diffuse_color = _srgb(hexcol)
    return m


def gdoor_mat(hexcol, k):
    """Painted steel garage door, a little grimy toward the bottom."""
    name = f'Z_exterior_nb_garage_{k}'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = flat_mat(name, hexcol, 0.42, 0.0, spec=0.5)
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    dirt = _maprange(nt, sep.outputs['Z'], (GRADE + 0.1) * FT, (GRADE + 1.6) * FT, 0.8, 1.0, smooth=True)
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 3.0
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    mott = _maprange(nt, nz.outputs['Fac'], 0.35, 0.65, 0.95, 1.02)
    nt.links.new(_mulcol(nt, _srgb(hexcol), _math(nt, 'MULTIPLY', dirt, mott)), b.inputs['Base Color'])
    return m


def drive_mat(ctx):
    """Neighbours' concrete: the library broom-finish concrete with large blotchy oil/tyre staining."""
    name = 'Z_exterior_nb_drive'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = varied(ctx, 'concrete_drive', 0.05, 'Z_exterior_walk_var').copy()
    m.name = name
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    s = b.inputs['Base Color']
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.9
    nz.inputs['Detail'].default_value = 5.0
    nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    st = _maprange(nt, nz.outputs['Fac'], 0.55, 0.72, 1.0, 0.78, smooth=True)
    if s.is_linked:
        nt.links.new(_mulcol(nt, s.links[0].from_socket, st), s)
    return m


def _house_mats(ctx, seed, r):
    clad = 'siding' if r.random() < 0.6 else 'stucco'
    if clad == 'siding':
        k = seed % len(SIDING)
        wall = siding_mat(f'Z_exterior_nb_siding_{k}', SIDING[k])
    else:
        k = seed % len(STUCCO)
        wall = _tinted(ctx, 'stucco', STUCCO[k], f'Z_exterior_nb_wall_{k}')
    ti = 3 if (clad == 'siding' and SIDING[seed % len(SIDING)] in ('#e2e0d8', '#d3cbb0') and seed % 2) else seed % 3
    trim = flat_mat(f'Z_exterior_nb_trim_{ti}', TRIMS[ti], 0.5)
    rk = (seed * 7 + 3) % len(ROOFS)
    roof = tex_mat(f'Z_exterior_nb_shingles_{rk}', 'grey_roof_01', 2.2, tint=ROOFS[rk], random_hue=0.06)
    gk = (seed * 5 + 1) % len(GDOORS)
    return dict(
        clad=clad, wall=wall, trim=trim, roof=roof,
        gutter=trim if seed % 4 else flat_mat('Z_exterior_nb_gutter_brown', '#4b3f35', 0.45),
        glass=flat_mat('Z_exterior_nb_glass', '#10151a', 0.03, 0.0, spec=1.0),
        blind=flat_mat('Z_exterior_nb_glass_blind', '#77726a', 0.06, 0.0, spec=0.9),
        curtain=flat_mat('Z_exterior_nb_glass_curtain', '#3b3833', 0.05, 0.0, spec=0.95),
        gdoor=gdoor_mat(GDOORS[gk], gk),
        door=flat_mat(f'Z_exterior_nb_door_{seed % len(DOORS)}', DOORS[seed % len(DOORS)], 0.38),
        shutter=flat_mat(f'Z_exterior_nb_shutter_{seed % 3}', SHUTTERS[seed % 3], 0.5),
        dark=flat_mat('Z_exterior_nb_dark', '#141414', 0.8),
        lamp=flat_mat('Z_exterior_nb_lamp', '#1c1c1c', 0.4, 0.6),
    )


# ----------------------------------------------------------------------------------- geometry helpers
def _fbox(mb, ax, c, sgn, a0, a1, y0, y1, n0, n1, mi=0):
    """Box on a facade. ax 'z': facade plane z=c running along x; 'x': plane x=c running along z.
    n0..n1 = distance out from the facade (sgn = outward direction along the facade normal axis)."""
    if ax == 'z':
        mb.box(a0, a1, y0, y1, c + sgn * n0, c + sgn * n1, mi)
    else:
        mb.box(c + sgn * n0, c + sgn * n1, y0, y1, a0, a1, mi)


def _panel(mb, ax, c, sgn, a0, a1, y0, y1, n0, n1, inset, mi=0):
    """Raised panel: back face a0..a1 x y0..y1 at n0, chamfered to a smaller front face at n1."""
    def P(a, y, n):
        return mb.vert(a, y, c + sgn * n) if ax == 'z' else mb.vert(c + sgn * n, y, a)
    bk = [P(a0, y0, n0), P(a1, y0, n0), P(a1, y1, n0), P(a0, y1, n0)]
    ft = [P(a0 + inset, y0 + inset, n1), P(a1 - inset, y0 + inset, n1), P(a1 - inset, y1 - inset, n1),
          P(a0 + inset, y1 - inset, n1)]
    mb.face(ft, mi)
    for i in range(4):
        j = (i + 1) % 4
        mb.face([bk[i], bk[j], ft[j], ft[i]], mi)


def _rect_sub(rects, holes):
    """Axis-aligned rectangle subtraction: rects - holes -> list of (x0, x1, z0, z1)."""
    out = list(rects)
    for hx0, hx1, hz0, hz1 in holes:
        nxt = []
        for x0, x1, z0, z1 in out:
            if hx1 <= x0 or hx0 >= x1 or hz1 <= z0 or hz0 >= z1:
                nxt.append((x0, x1, z0, z1))
                continue
            if hx0 > x0:
                nxt.append((x0, hx0, z0, z1))
            if hx1 < x1:
                nxt.append((hx1, x1, z0, z1))
            ix0, ix1 = max(x0, hx0), min(x1, hx1)
            if hz0 > z0:
                nxt.append((ix0, ix1, z0, hz0))
            if hz1 < z1:
                nxt.append((ix0, ix1, hz1, z1))
        out = [q for q in nxt if q[1] - q[0] > 0.05 and q[3] - q[2] > 0.05]
    return out


def _zr(a, b):
    return (min(a, b), max(a, b))


# ----------------------------------------------------------------------------------- roofs
def _roof(rf, gu, gw, box, kind, along_u_is_x, o, yw, pitch, thick=0.35, gable_walls=True):
    """Hip or gable roof over the wall rectangle box=(x0,x1,z0,z1) whose walls top out at yw.
    rf: roof MB (mi 0 shingles, 1 fascia/soffit trim), gu: gutter MB, gw: gable-wall MB.
    Local frame: u along the ridge, v across. Returns the ridge height."""
    x0, x1, z0, z1 = box
    if along_u_is_x:
        u0, u1, v0, v1 = x0, x1, z0, z1

        def P(u, y, v):
            return (u, y, v)
    else:
        u0, u1, v0, v1 = z0, z1, x0, x1

        def P(u, y, v):
            return (v, y, u)

    def V(mb, u, y, v):
        return mb.vert(*P(u, y, v))

    def gbox(mb, ua, ub, ya, yb, va, vb, mi=0):
        p0, p1 = P(ua, ya, va), P(ub, yb, vb)
        mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], mi)

    vc = (v0 + v1) / 2
    ye = yw - o * pitch + 0.15                     # roof plane at the eave edge
    yr = ye + (vc - v0 + o) * pitch
    U0, U1, V0, V1 = u0 - o, u1 + o, v0 - o, v1 + o
    if kind == 'hip':
        half = (v1 - v0) / 2 + o
        ra, rb = (U0 + half, vc), (U1 - half, vc)
        if ra[0] > rb[0]:
            ra = rb = ((U0 + U1) / 2, vc)
        c = [V(rf, U0, ye, V0), V(rf, U1, ye, V0), V(rf, U1, ye, V1), V(rf, U0, ye, V1)]
        A, B = V(rf, ra[0], yr, vc), V(rf, rb[0], yr, vc)
        rf.face([c[0], c[1], B, A])
        rf.face([c[2], c[3], A, B])
        rf.face([c[3], c[0], A])
        rf.face([c[1], c[2], B])
        cb = [V(rf, U0, ye - thick, V0), V(rf, U1, ye - thick, V0), V(rf, U1, ye - thick, V1),
              V(rf, U0, ye - thick, V1)]
        for i in range(4):
            j = (i + 1) % 4
            rf.face([cb[i], cb[j], c[j], c[i]], 1)
        rf.face([cb[3], cb[2], cb[1], cb[0]], 1)
        if rb[0] - ra[0] > 0.5:
            gbox(rf, ra[0] - 0.2, rb[0] + 0.2, yr - 0.06, yr + 0.1, vc - 0.38, vc + 0.38)
        gbox(gu, U0 - 0.36, U1 + 0.36, ye - 0.42, ye - 0.04, V0 - 0.36, V0)
        gbox(gu, U0 - 0.36, U1 + 0.36, ye - 0.42, ye - 0.04, V1, V1 + 0.36)
        gbox(gu, U0 - 0.36, U0, ye - 0.42, ye - 0.04, V0, V1)
        gbox(gu, U1, U1 + 0.36, ye - 0.42, ye - 0.04, V0, V1)
        return yr
    # gable: slopes, eave fascia + soffits, rake boards + rake soffits, gable-end wall triangles
    ra, rb = V(rf, U0, yr, vc), V(rf, U1, yr, vc)
    c = [V(rf, U0, ye, V0), V(rf, U1, ye, V0), V(rf, U1, ye, V1), V(rf, U0, ye, V1)]
    rf.face([c[0], c[1], rb, ra])
    rf.face([c[2], c[3], ra, rb])
    for vv in (V0, V1):                               # eave fascia
        rf.face([V(rf, U0, ye - thick, vv), V(rf, U1, ye - thick, vv), V(rf, U1, ye, vv), V(rf, U0, ye, vv)], 1)
    for va, vb in ((V0, v0), (v1, V1)):              # eave soffits (back to the wall line)
        rf.face([V(rf, U0, ye - thick, va), V(rf, U1, ye - thick, va), V(rf, U1, ye - thick, vb),
                 V(rf, U0, ye - thick, vb)], 1)
    for uu, ui in ((U0, u0), (U1, u1)):
        for va in (V0, V1):                           # rake board (follows each slope) + rake soffit
            rf.face([V(rf, uu, ye, va), V(rf, uu, yr, vc), V(rf, uu, yr - thick, vc), V(rf, uu, ye - thick, va)], 1)
            rf.face([V(rf, uu, ye - thick, va), V(rf, ui, ye - thick, va), V(rf, ui, yr - thick, vc),
                     V(rf, uu, yr - thick, vc)], 1)
        if gable_walls:
            gw.face([V(gw, ui, yw, v0), V(gw, ui, yw + (vc - v0) * pitch, vc), V(gw, ui, yw, v1)])
    gbox(rf, U0, U1, yr - 0.06, yr + 0.1, vc - 0.38, vc + 0.38)
    gbox(gu, U0 - 0.05, U1 + 0.05, ye - 0.42, ye - 0.04, V0 - 0.36, V0)
    gbox(gu, U0 - 0.05, U1 + 0.05, ye - 0.42, ye - 0.04, V1, V1 + 0.36)
    return yr


# ----------------------------------------------------------------------------------- openings
def _window(win, fr, ax, c, sgn, pos, ww, sill, head, r, st):
    """Glass (win mi 0 clear / 1 blind / 2 curtain) in a vinyl frame inside a projecting casing
    (fr mi 0 trim, 1 shutter)."""
    k = r.random()
    mi = 1 if k < 0.22 else (2 if k < 0.36 else 0)
    _fbox(win, ax, c, sgn, pos, pos + ww, sill, head, -0.05, 0.02, mi)
    fw, fp = 0.13, 0.08                                 # vinyl frame face / projection
    for a0, a1, y0, y1 in ((pos, pos + ww, head - fw, head), (pos, pos + ww, sill, sill + fw),
                           (pos, pos + fw, sill, head), (pos + ww - fw, pos + ww, sill, head)):
        _fbox(fr, ax, c, sgn, a0, a1, y0, y1, 0.0, fp)
    if ww >= 4.5:                                        # slider: meeting stile
        mid = pos + ww / 2
        _fbox(fr, ax, c, sgn, mid - 0.07, mid + 0.07, sill, head, 0.0, fp)
    else:                                                # single hung: meeting rail
        ym = sill + (head - sill) * 0.52
        _fbox(fr, ax, c, sgn, pos, pos + ww, ym - 0.06, ym + 0.06, 0.0, fp)
    if st['grids']:
        for k2 in (1, 2):
            yg = sill + (head - sill) * (0.26 if k2 == 1 else 0.78)
            _fbox(fr, ax, c, sgn, pos + fw, pos + ww - fw, yg - 0.03, yg + 0.03, 0.0, 0.05)
        nv = 2 if ww < 4.5 else 4
        for k2 in range(1, nv + 1):
            xg = pos + ww * k2 / (nv + 1)
            _fbox(fr, ax, c, sgn, xg - 0.03, xg + 0.03, sill + fw, head - fw, 0.0, 0.05)
    tw, tp = 0.32, 0.26                                  # casing face width / projection
    _fbox(fr, ax, c, sgn, pos - tw, pos + ww + tw, head, head + tw, 0.0, tp)
    _fbox(fr, ax, c, sgn, pos - tw, pos, sill, head, 0.0, tp)
    _fbox(fr, ax, c, sgn, pos + ww, pos + ww + tw, sill, head, 0.0, tp)
    _fbox(fr, ax, c, sgn, pos - tw - 0.12, pos + ww + tw + 0.12, sill - 0.18, sill, 0.0, tp + 0.12)
    if st['shutters'] and ww <= 6.0:
        sw = min(1.5, ww * 0.36)
        for a0 in (pos - tw - 0.08 - sw, pos + ww + tw + 0.08):
            _fbox(fr, ax, c, sgn, a0, a0 + sw, sill, head + tw, 0.0, 0.1, 1)


def _facade_windows(win, fr, ax, c, sgn, a, b, skips, floor, r, st, front=False):
    pos = a + r.uniform(3.0, 5.0)
    while pos < b - 4.0:
        ww = r.choice((4.0, 5.0, 6.0, 7.0) if front else (3.0, 4.0, 5.0, 6.0))
        if pos + ww > b - 2.5:
            break
        hit = next((s for s in skips if not (pos + ww + 0.6 < s[0] or pos - 0.6 > s[1])), None)
        if hit:
            pos = hit[1] + 1.2
            continue
        sill = floor + (r.choice((2.6, 3.0)) if front else r.choice((2.8, 3.2, 3.5, 4.2)))
        _window(win, fr, ax, c, sgn, pos, ww, sill, floor + 6.9, r, st)
        pos += ww + r.uniform(4.5, 8.0)


def _garage_door(g, tr, dk, gx0, gx1, c, sgn, yb, top, style):
    """Sectional door (g: mi 0 door, 1 glass) recessed behind jamb/head trim (tr), dark opening (dk)."""
    _fbox(dk, 'z', c, sgn, gx0, gx1, yb, top, -0.4, -0.02)
    rows, gap = 4, 0.035
    sh = (top - yb) / rows
    ncol = 8 if style == 0 else 4
    for k in range(rows):
        y0, y1 = yb + k * sh + gap / 2, yb + (k + 1) * sh - gap / 2
        _fbox(g, 'z', c, sgn, gx0 + 0.04, gx1 - 0.04, y0, y1, 0.0, 0.06)
        st_ = 0.3
        pw = (gx1 - gx0 - 0.08 - (ncol + 1) * st_) / ncol
        for j in range(ncol):
            a0 = gx0 + 0.04 + st_ + j * (pw + st_)
            if style == 2 and k == rows - 1:
                _fbox(g, 'z', c, sgn, a0, a0 + pw, y0 + 0.28, y1 - 0.28, 0.02, 0.07, 1)
            else:
                _panel(g, 'z', c, sgn, a0, a0 + pw, y0 + 0.24, y1 - 0.24, 0.06, 0.1, 0.07)
    t = 0.38
    _fbox(tr, 'z', c, sgn, gx0 - t, gx0, yb, top + t, 0.0, 0.3)
    _fbox(tr, 'z', c, sgn, gx1, gx1 + t, yb, top + t, 0.0, 0.3)
    _fbox(tr, 'z', c, sgn, gx0, gx1, top, top + t, 0.0, 0.3)


# ----------------------------------------------------------------------------------- house
def house(ctx, name, x0, x1, z0, z1, seed, front='S', garage=True, eave=None, pitch=None, floor=0.5,
          wings=(), roof_type=None, shrubs=True, gwing=None, yard=None, porch=True):
    """Single-storey ranch: main box (+ optional side wings), hip or gable roof, optional front-projecting
    garage wing, recessed entry porch, windows, garage door, driveway; returns a dict describing the lot."""
    r = rng(seed)
    M = _house_mats(ctx, seed, r)
    st = dict(grids=(seed % 5 == 2), shutters=(M['clad'] == 'siding' and seed % 4 == 1))
    eave = eave if eave is not None else round(8.0 + r.uniform(0.0, 0.9), 2)
    pitch = pitch if pitch is not None else r.choice((4.0, 4.5, 5.0, 5.5, 6.0)) / 12
    roof_type = roof_type or ('gable' if seed % 3 == 1 else 'hip')
    if yard is None:
        yard = front == 'N' and z0 > L.FAR_WALK[1]
    sgn = 1 if front == 'S' else -1
    cz = z1 if front == 'S' else z0
    yw = floor + eave
    right = seed % 2 == 1
    gx = wing = None
    proj = 0.0
    if garage:
        if gwing is None:
            gwing = r.choice((0.0, 0.0, 7.0, 9.0))
        proj = gwing
        if gwing > 0:
            wx = (x1 - 22.0, x1) if right else (x0, x0 + 22.0)
            wing = (wx[0], wx[1]) + (_zr(z1 - 16.0, z1 + gwing) if front == 'S' else _zr(z0 - gwing, z0 + 16.0))
            gx = (wx[0] + 3.0, wx[1] - 3.0)
        else:
            gx = (x1 - 18.0, x1 - 2.0) if right else (x0 + 2.0, x0 + 18.0)
    gcz = cz + sgn * proj
    # recessed porch beside the garage (or off-centre) with the front door at its back wall
    pw_, pd = 9.0, 5.0
    if gx:                                             # porch right beside the garage (wing)
        px0 = ((wing[0] if wing else gx[0] - 1.5) - pw_) if right else (wing[1] if wing else gx[1] + 1.5)
    else:
        px0 = (x0 + x1) / 2 + (-6.0 if right else 6.0) - pw_ / 2
    for w in wings:                                   # keep the entry clear of side wings that cover the front
        if w[2] < cz < w[3] and px0 < w[1] + 1.0 and px0 + pw_ > w[0] - 1.0:
            px0 = w[1] + 1.5 if (w[0] + w[1]) / 2 < (x0 + x1) / 2 else w[0] - 1.5 - pw_
    px1 = px0 + pw_
    if not porch:
        pd = 0.0
    main = (x0, x1, z0, z1)
    roof_boxes = [main] + list(wings) + ([wing] if wing else [])
    if pd > 0:
        zr = _zr(cz - sgn * pd, z1 if front == 'N' else z0)
        wall_boxes = [(x0, px0, z0, z1), (px1, x1, z0, z1), (px0, px1, zr[0], zr[1])] + list(wings) + \
            ([wing] if wing else [])
    else:
        wall_boxes = list(roof_boxes)
    wall_boxes = [b for b in wall_boxes if b[1] - b[0] > 0.1]

    # ---- walls, foundation band
    mb = MB()
    for (a, b, c, d) in wall_boxes:
        mb.box(a, b, GRADE - 0.3, yw, c, d)
    mb.obj(ctx, f'ext nb {name} walls', M['wall'], SUB)
    fb = MB()
    for (a, b, c, d) in wall_boxes:
        fb.box(a - 0.03, b + 0.03, GRADE - 0.1, floor - 0.42, c - 0.03, d + 0.03)
    fb.obj(ctx, f'ext nb {name} plinth', 'foundation', SUB)
    # ---- roofs (+ gutters, gable walls)
    rf, gu, gwm = MB(), MB(), MB()
    o = 1.6
    for i, bx in enumerate(roof_boxes):
        a, b, c, d = bx
        if bx is wing:
            _roof(rf, gu, gwm, bx, 'gable', False, o, yw, pitch)            # street-facing gable
        else:
            _roof(rf, gu, gwm, bx, roof_type, (b - a) >= (d - c), o, yw, pitch)
    rf.obj(ctx, f'ext nb {name} roof', [M['roof'], M['trim']], SUB)
    if gwm.f:
        gwm.obj(ctx, f'ext nb {name} gable walls', M['wall'], SUB)
    # downspouts at the outer corners of the front
    soff = yw - o * pitch + 0.15 - 0.35
    for xc in (x0 + 0.12, x1 - 0.34):
        zf = gcz if (wing and wing[0] <= xc <= wing[1]) else cz
        _fbox(gu, 'z', zf, sgn, xc, xc + 0.22, GRADE + 0.05, soff - 0.2, 0.03, 0.22)
        _fbox(gu, 'z', zf, sgn, xc, xc + 0.22, soff - 0.42, soff - 0.2, 0.03, o)
    gu.obj(ctx, f'ext nb {name} gutters', M['gutter'], SUB)

    # ---- windows on the main box (front skips the wing, the porch and the garage door)
    win, fr = MB(), MB()
    front_skips = [(px0 - 0.6, px1 + 0.6)]
    if wing:
        front_skips.append((wing[0] - 0.8, wing[1] + 0.8))
    elif gx:
        front_skips.append((gx[0] - 0.8, gx[1] + 0.8))
    facades = {'S': ('z', z1, 1, x0, x1), 'N': ('z', z0, -1, x0, x1), 'E': ('x', x1, 1, z0, z1),
               'W': ('x', x0, -1, z0, z1)}
    for key, (ax, c, s, a, b) in facades.items():
        isf = key == front
        skips = list(front_skips) if isf else []
        for w in wings:                               # facade stretches buried inside a side wing
            if ax == 'z' and w[2] < c < w[3]:
                skips.append((w[0] - 0.8, w[1] + 0.8))
            elif ax == 'x' and w[0] < c < w[1]:
                skips.append((w[2] - 0.8, w[3] + 0.8))
        if wing and not isf and ax == 'x' and ((key == 'E') == right):
            skips = [_zr(wing[2] - 0.8, wing[3] + 0.8)]
        _facade_windows(win, fr, ax, c, s, a, b, skips, floor, r, st, front=isf)
    if wing:                                              # one window on the wing's free side
        ax_side = wing[0] if right else wing[1]
        zs = _zr(gcz, cz)
        if zs[1] - zs[0] > 6.0:
            _window(win, fr, 'x', ax_side, -1 if right else 1, zs[0] + 1.6, 3.0, floor + 3.2, floor + 6.9, r, st)
    win.obj(ctx, f'ext nb {name} glass', [M['glass'], M['blind'], M['curtain']], SUB)
    fr.obj(ctx, f'ext nb {name} trim', [M['trim'], M['shutter']], SUB)

    # ---- garage door, driveway
    lot = dict(name=name, x0=x0, x1=x1, z0=z0, z1=z1, front=front, cz=cz, gcz=gcz, gx=gx, wing=wing,
               porch=(px0, px1, pd), seed=seed, yard=yard)
    dmat = drive_mat(ctx)
    if gx:
        g, tr, dk = MB(), MB(), MB()
        _garage_door(g, tr, dk, gx[0], gx[1], gcz, sgn, GRADE + 0.05, floor + 7.0, seed % 3)
        g.obj(ctx, f'ext nb {name} garage door', [M['gdoor'], M['glass']], SUB)
        tr.obj(ctx, f'ext nb {name} garage trim', M['trim'], SUB)
        dk.obj(ctx, f'ext nb {name} garage opening', M['dark'], SUB)
        d = MB()
        if front == 'S':
            d.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, -0.45, gcz, L.SIDEWALK[0])
            d.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, -0.52, L.PARK[0], L.CURB[1])
        elif z0 > L.FAR_WALK[1]:                     # across our street, garage facing us
            d.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, -0.5, L.FAR_WALK[1], gcz)
            d.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, -0.52, L.FAR_GUTTER[1], L.FAR_WALK[0])
        else:                                         # rear neighbours: driveway runs north to their own street
            d.box(gx[0] + 0.5, gx[1] - 0.5, GRADE - 0.3, -0.5, gcz - 22.0, gcz)
        d.obj(ctx, f'ext nb {name} driveway', dmat, SUB)

    # ---- recessed porch: header, floor slab + step, door with casing (and sidelight), porch light
    po = MB()
    dz = cz - sgn * pd                                 # door wall plane
    dx = (px0 + px1) / 2 + (1.2 if right else -1.2)
    if pd > 0:
        hd = MB()
        _fbox(hd, 'z', cz, sgn, px0, px1, yw - 1.15, yw, -0.55, 0.0)
        hd.obj(ctx, f'ext nb {name} porch header', M['wall'], SUB)
        _fbox(po, 'z', cz, sgn, px0, px1, GRADE - 0.2, floor - 0.12, -pd, 0.0)
        _fbox(po, 'z', cz, sgn, px0 + 1.0, px1 - 1.0, GRADE - 0.2, floor - 0.6, 0.0, 1.3)
        po.obj(ctx, f'ext nb {name} porch slab', dmat, SUB)
    dm = MB()
    _fbox(dm, 'z', dz, sgn, dx - 1.5, dx + 1.5, floor - 0.12, floor + 6.7, -0.05, 0.06)
    dt = MB()
    for a0, a1, y0, y1 in ((dx - 1.85, dx - 1.5, floor - 0.12, floor + 7.05), (dx + 1.5, dx + 1.85, floor - 0.12, floor + 7.05),
                           (dx - 1.85, dx + 1.85, floor + 6.7, floor + 7.05)):
        _fbox(dt, 'z', dz, sgn, a0, a1, y0, y1, 0.0, 0.16)
    if seed % 3 != 1:                                  # sidelight
        sx = dx + (2.0 if right else -3.1)
        win2 = MB()
        _fbox(win2, 'z', dz, sgn, sx, sx + 1.1, floor + 0.6, floor + 6.7, -0.05, 0.02)
        win2.obj(ctx, f'ext nb {name} sidelight', M['curtain'], SUB)
        for a0, a1 in ((sx - 0.18, sx), (sx + 1.1, sx + 1.28)):
            _fbox(dt, 'z', dz, sgn, a0, a1, floor + 0.45, floor + 6.85, 0.0, 0.14)
        _fbox(dt, 'z', dz, sgn, sx - 0.18, sx + 1.28, floor + 0.45, floor + 0.6, 0.0, 0.14)
    dm.obj(ctx, f'ext nb {name} door', M['door'], SUB)
    dt.obj(ctx, f'ext nb {name} door trim', M['trim'], SUB)
    lp = MB()
    lx = dx + (-2.3 if right else 2.3)
    _fbox(lp, 'z', dz, sgn, lx - 0.22, lx + 0.22, floor + 5.6, floor + 6.5, 0.0, 0.32)
    lp.obj(ctx, f'ext nb {name} porch light', M['lamp'], SUB)
    lot.update(door_x=dx, door_z=dz)

    if yard:
        _front_yard(ctx, lot, r)
    elif shrubs:
        zf = cz + sgn * 2.4
        x = x0 + r.uniform(1.5, 3.0)
        while x < x1 - 1.5:
            if (gx and gx[0] - 1.5 < x < gx[1] + 1.5) or (wing and wing[0] - 1.5 < x < wing[1] + 1.5):
                x = max(gx[1], wing[1] if wing else gx[1]) + 2.0
                continue
            wb = next((w for w in wings if w[0] - 1.5 < x < w[1] + 1.5 and w[2] <= zf <= w[3]), None)
            if wb:
                x = wb[1] + 2.0
                continue
            if px0 - 0.5 < x < px1 + 0.5:
                x = px1 + 1.5
                continue
            plant(ctx, 'searsia_lucida', r.choice('abc'), x, zf + r.uniform(-0.3, 0.3),
                  height_ft=r.uniform(2.8, 3.8), res='2k', leaf=dict(amount=0.25, hue=0.5, sat=0.8), sub=SUB)
            x += r.uniform(3.2, 5.0)
    return lot


# ----------------------------------------------------------------------------------- front yards
def _front_yard(ctx, lot, r):
    """Across-the-street lot (front faces north toward us): walk, mulched foundation beds with shrubs and
    grasses, lawn (instanced grass where our windows see it), a front-yard tree."""
    x0, x1, cz, gcz, gx, wing = lot['x0'], lot['x1'], lot['cz'], lot['gcz'], lot['gx'], lot['wing']
    px0, px1, pd = lot['porch']
    dx = lot['door_x']
    za = L.FAR_WALK[1]
    lx0, lx1 = x0 - 8.0, x1 + 8.0                       # half of the 16 ft side gaps
    drive = (gx[0] + 0.5, gx[1] - 0.5, za, gcz) if gx else None
    BD = 3.6                                             # bed depth
    # walk: from the porch step straight out past the bed, then across to the driveway edge
    walks = []
    wz1 = cz - 1.3
    if drive:
        wz0 = min(gcz, cz - BD) - 3.4
        walks.append((dx - 1.75, dx + 1.75, wz0, wz1))
        if dx < drive[0]:
            walks.append((dx - 1.75, drive[0], wz0, wz0 + 3.4))
        else:
            walks.append((drive[1], dx + 1.75, wz0, wz0 + 3.4))
    else:
        walks.append((dx - 1.75, dx + 1.75, za, wz1))
    wk = MB()
    for (a, b, c, d) in walks:
        wk.box(a, b, GRADE - 0.3, GRADE + 0.12, c, d)
    wk.obj(ctx, f'ext nb {lot["name"]} walk', drive_mat(ctx), SUB)
    # beds along the main front (and the inside corner in front of a projecting wing's side)
    foot = [(x0, x1, cz, lot['z1'])] + ([wing] if wing else [])
    beds = _rect_sub([(x0 - 1.0, x1 + 1.0, cz - BD, cz)], walks + ([drive] if drive else []) +
                     ([(gx[0] - 0.4, gx[1] + 0.4, cz - BD - 1, cz)] if gx and not wing else []) +
                     ([(px0, px1, cz - BD, cz)]) + foot)
    if wing:                                             # deeper bed in the inside corner beside the wing
        right = lot['seed'] % 2 == 1
        corner = (wing[0] - 2 * BD, wing[0], gcz, cz - BD) if right else (wing[1], wing[1] + 2 * BD, gcz, cz - BD)
        beds += _rect_sub([corner], walks)
    beds = [b for b in beds if (b[1] - b[0]) > 1.2 and (b[3] - b[2]) > 1.2]
    bm, ed = MB(), MB()
    for (a, b, c, d) in beds:
        bm.box(a, b, GRADE - 0.2, GRADE + 0.07, c, d)
        ed.box(a, b, GRADE - 0.2, GRADE + 0.1, c - 0.12, c + 0.02)          # concrete mow strip on the lawn side
    mulch = mul_copy(ctx, 'soil_mulch', (0.62, 0.55, 0.5), 'Z_exterior_nb_mulch')
    if beds:
        bm.obj(ctx, f'ext nb {lot["name"]} beds', mulch, SUB)
        ed.obj(ctx, f'ext nb {lot["name"]} edging', drive_mat(ctx), SUB)
    sl = dict(amount=0.25, hue=0.5, sat=0.8)
    for (a, b, c, d) in beds:
        zc = (c + d) / 2
        x = a + r.uniform(0.9, 1.6)
        k = 0
        while x < b - 0.8:
            if (d - c) > 2.0 and k % 3 != 2:
                plant(ctx, 'searsia_lucida', r.choice('abc'), x, zc + r.uniform(-0.25, 0.25),
                      height_ft=r.uniform(2.8, 4.0), res='2k', leaf=sl, sub=SUB)
                x += r.uniform(3.4, 4.4)
            else:
                place_proc(ctx, r.choice(('lomandra', 'lomandra', 'fescue')), x, zc + r.uniform(-0.2, 0.2),
                           scale=r.uniform(0.9, 1.15), y=GRADE + 0.07)
                x += r.uniform(1.8, 2.6)
            k += 1
    # lawn
    holes = walks + beds + foot + ([drive] if drive else []) + [(px0 + 0.9, px1 - 0.9, cz - 1.35, cz)]
    lawns = _rect_sub([(lx0, lx1, za, cz)], holes)
    lm = MB()
    for (a, b, c, d) in lawns:
        lm.box(a, b, GRADE - 0.15, GRADE, c, d)
    near = GRASS_X[0] < (x0 + x1) / 2 < GRASS_X[1]
    if near:
        soil = tex_mat('Z_exterior_lawn_soil', 'leafy_grass', 1.2, tint='#6f7a4a', value=0.55)
        ob = lm.obj(ctx, f'ext nb {lot["name"]} lawn', soil, SUB)
        scatter([ob], _gn_scatter('ext GN lawn context', proc_plant(ctx, 'lawn'), density_m2=520.0, smin=0.9,
                                  smax=1.35, seed=21, tilt=0.12))
    else:
        from .exterior_site import far_lawn_mat
        lm.obj(ctx, f'ext nb {lot["name"]} lawn', far_lawn_mat(), SUB)
    # one front-yard tree in the lawn, clear of the walk and drive
    if lot['seed'] % 4 != 3:
        big = [q for q in lawns if (q[1] - q[0]) > 8 and (q[3] - q[2]) > 8]
        if big:
            q = max(big, key=lambda q: (q[1] - q[0]) * (q[3] - q[2]))
            tx = r.uniform(q[0] + 3.5, q[1] - 3.5)
            tz = r.uniform(q[2] + 4.0, min(q[3] - 4.0, q[2] + 12.0))
            if lot['seed'] % 2:
                plant(ctx, 'island_tree_02', 'main', tx, tz, height_ft=r.uniform(11.0, 14.0), leaf=dict(amount=0.3),
                      sub=SUB)
            else:
                plant(ctx, 'tree_small_02', 'main', tx, tz, height_ft=r.uniform(15.0, 20.0), leaf=dict(amount=0.3),
                      sub=SUB)


def side_fence(ctx, name, xa, xb, z, gate=True, h=6.0, posts=8.0):
    """6 ft vertical-board wood fence with posts, top rail and a gate, along x at z."""
    fm = board_fence_mat()
    mb, pm = MB(), MB()
    y0, y1 = GRADE, GRADE + h
    mb.box(xa, xb, y0 + 0.15, y1, z - 0.04, z + 0.04)
    x = xa
    while x <= xb + 0.01:
        pm.box(x - 0.17, x + 0.17, y0 - 0.1, y1 + 0.08, z - 0.17, z + 0.17)
        x += posts
    pm.box(xa, xb, y1 - 0.02, y1 + 0.1, z - 0.12, z + 0.12)                   # cap rail
    if gate and xb - xa > 7:
        gx = xa + (xb - xa) * 0.35
        pm.box(gx - 0.2, gx + 0.2, y0 - 0.1, y1 + 0.15, z - 0.2, z + 0.2)
        pm.box(gx + 3.6, gx + 4.0, y0 - 0.1, y1 + 0.15, z - 0.2, z + 0.2)
        pm.box(gx + 0.2, gx + 3.6, y0 + 0.9, y0 + 1.15, z - 0.12, z - 0.04)        # gate rails (street side)
        pm.box(gx + 0.2, gx + 3.6, y1 - 1.0, y1 - 0.75, z - 0.12, z - 0.04)
    mb.obj(ctx, f'ext nb fence {name}', fm, SUB)
    pm.obj(ctx, f'ext nb fence {name} posts', board_fence_mat('Z_exterior_nb_fence_dark', '#6a5847', 0.47), SUB)


def bins(ctx, x, z, face, colours=('#3d5a3a', '#2f4f74')):
    """Wheelie bins (a pair) standing at (x, z), lids toward `face` (+1 = +z)."""
    body = flat_mat('Z_exterior_bin_body', '#2e3133', 0.55)
    lids = [flat_mat(f'Z_exterior_bin_lid_{i}', c, 0.5) for i, c in enumerate(colours)]
    mb = MB()
    for i in range(len(colours)):
        cx = x + i * 2.15
        y0 = GRADE + 0.12
        mb.box_pts([(cx - 0.8, z - 0.9), (cx + 0.8, z - 0.9), (cx + 0.8, z + 0.9), (cx - 0.8, z + 0.9)], y0, y0 + 3.2,
                   0)
        mb.box(cx - 0.92, cx + 0.92, y0 + 3.2, y0 + 3.36, z - 1.05, z + 1.0, 1 + i)
        for s in (-1, 1):
            mb.box_c(cx + s * 0.62, y0 + 0.2, z - face * 0.8, 0.18, 0.62, 0.62, mi=0)
    mb.obj(ctx, 'ext nb bins', [body] + lids, SUB)


# ----------------------------------------------------------------------------------- build
def build(ctx):
    n = 0
    lots = []
    # side neighbours (front faces on our street, garages toward the street on the front wings)
    house(ctx, 'west', -52.0, -12.5, 6.0, 44.0, 1, wings=[(-33.0, -12.5, 30.0, 50.0)], garage=False, porch=False,
          yard=False)
    house(ctx, 'east', 53.0, 93.0, 4.0, 45.0, 2, wings=[(53.0, 75.0, 28.0, 50.0)], garage=False, porch=False,
          yard=False)
    n += 2
    for nm, gxx, cz, seed in (('west', (-31.0, -15.0), 50.0, 1), ('east', (55.0, 71.0), 50.0, 2)):
        M = _house_mats(ctx, seed, rng(seed))
        g, tr, dk = MB(), MB(), MB()
        _garage_door(g, tr, dk, gxx[0], gxx[1], cz, 1, GRADE + 0.05, 7.5, seed % 3)
        g.obj(ctx, f'ext nb {nm} garage door', [M['gdoor'], M['glass']], SUB)
        tr.obj(ctx, f'ext nb {nm} garage trim', M['trim'], SUB)
        dk.obj(ctx, f'ext nb {nm} garage opening', M['dark'], SUB)
        d = MB()
        d.box(gxx[0] + 0.5, gxx[1] - 0.5, GRADE - 0.3, -0.5, cz, L.SIDEWALK[0])
        d.box(gxx[0] + 0.5, gxx[1] - 0.5, GRADE - 0.3, -0.52, L.PARK[0], L.CURB[1])
        d.obj(ctx, f'ext nb {nm} driveway', drive_mat(ctx), SUB)
    # further along our street
    house(ctx, 'west2', -112.0, -70.0, 4.0, 46.0, 3); n += 1
    house(ctx, 'east2', 110.0, 152.0, 5.0, 46.0, 4); n += 1
    # rear neighbours (their backs face our fence)
    house(ctx, 'rear1', -14.0, 24.0, -82.0, -40.0, 5, front='N', gwing=0.0); n += 1
    house(ctx, 'rear2', 34.0, 74.0, -80.0, -42.0, 6, front='N', gwing=0.0); n += 1
    house(ctx, 'rear3', -70.0, -30.0, -82.0, -42.0, 7, front='N', gwing=0.0); n += 1
    house(ctx, 'rear4', 88.0, 128.0, -80.0, -40.0, 8, front='N', gwing=0.0); n += 1
    # across the street (fronts face north toward us): the row the front door and the B3 bay look at
    across = [(-128.0, 10, 9.0), (-70.0, 11, 0.0), (-14.0, 12, 0.0), (42.0, 13, 8.0), (98.0, 14, 0.0),
              (154.0, 15, 9.0)]
    for i, (x, seed, gwing) in enumerate(across):
        lots.append(house(ctx, f'south{i}', x, x + 40.0, 143.0 + (i % 2) * 3, 186.0, seed, front='N',
                          gwing=gwing))
        n += 1
    # side-yard fences + gates between the across-street houses (hide the open ground behind)
    for a, b in zip(lots[:-1], lots[1:]):
        zf = max(a['z0'], b['z0']) + 9.0
        side_fence(ctx, f'{a["name"]}-{b["name"]}', a['x1'], b['x0'], zf)
    side_fence(ctx, 'south0-w', lots[0]['x0'] - 10.0, lots[0]['x0'], lots[0]['z0'] + 9.0, gate=False)
    side_fence(ctx, 'south5-e', lots[-1]['x1'], lots[-1]['x1'] + 10.0, lots[-1]['z0'] + 9.0, gate=False)
    # real grass on the far park strip in front of the houses our windows look at (cut at the aprons)
    aprons = [(q['gx'][0] + 0.3, q['gx'][1] - 0.3, L.FAR_PARK[0] - 1, L.FAR_PARK[1] + 1) for q in lots if q['gx']]
    strip = _rect_sub([(GRASS_X[0], GRASS_X[1], L.FAR_PARK[0] + 0.05, L.FAR_PARK[1] - 0.05)], aprons)
    pm = MB()
    for (a_, b_, c_, d_) in strip:
        pm.box(a_, b_, GRADE - 0.1, GRADE + 0.01, c_, d_)
    ob = pm.obj(ctx, 'ext nb far park strip grass', tex_mat('Z_exterior_lawn_soil', 'leafy_grass', 1.2, tint='#6f7a4a',
                                                               value=0.55), SUB)
    scatter([ob], _gn_scatter('ext GN lawn context', proc_plant(ctx, 'lawn'), density_m2=520.0, smin=0.9, smax=1.35,
                              seed=21, tilt=0.12))
    # parked cars, nose-in, in two driveways across the street (seen from ~100 ft only)
    for lot, paint, style, off in ((lots[2], 'silver', 'suv', 3.6), (lots[3], 'white', 'sedan', -3.4),
                                   (lots[1], 'blue', 'suv', -3.4)):
        if not lot['gx']:
            continue
        cx = (lot['gx'][0] + lot['gx'][1]) / 2 + off
        zf = lot['gcz'] - 2.5
        Lc = 15.8
        if zf - Lc < L.FAR_WALK[1] + 0.5:
            continue
        place_car(ctx, cx, zf, math.pi / 2, style=style, paint=paint, y=-0.5, sub=SUB)
    # bins beside one garage
    b4 = lots[4]
    if b4['gx']:
        bx = b4['gx'][1] + 1.6 if b4['gx'][1] + 6 < b4['x1'] else b4['gx'][0] - 5.6
        bins(ctx, bx, b4['gcz'] - 1.4, -1)
    # more houses down the street both ways (fill the street perspective)
    for i, x in enumerate((-172.0, 166.0, 222.0, -228.0)):
        house(ctx, f'street{i}', x, x + 42.0, 4.0 + (i % 2) * 2, 46.0, 20 + i); n += 1
    for i, x in enumerate((-186.0, 210.0, 266.0, -242.0)):
        house(ctx, f'south_far{i}', x, x + 40.0, 145.0, 186.0, 30 + i, front='N', yard=False); n += 1
    # neighbourhood trees: backyard shade trees above the fences, street trees, a few big background trees
    r = rng(77)
    leaf = dict(amount=0.3)
    spots = [(-24, -24, 24), (14, -30, 26), (52, -27, 22), (86, -28, 25), (-48, -20, 21), (-30, 22, 20),
             (70, 20, 22), (-90, 30, 24), (125, -10, 26), (-8, -110, 34), (40, -120, 36), (100, -100, 32),
             (-80, -105, 33), (160, 60, 30), (-150, 60, 30)]
    for (x, z, h) in spots:
        plant(ctx, 'tree_small_02', 'main', x, z, height_ft=h * r.uniform(0.9, 1.1), leaf=leaf, sub=SUB)
    # backyard trees behind the across-street row, so the skyline over their roofs reads leafy
    for lot in lots:
        for k in range(2):
            x = r.uniform(lot['x0'] + 4, lot['x1'] - 4)
            plant(ctx, 'tree_small_02', 'main', x, r.uniform(192.0, 206.0), height_ft=r.uniform(26, 36), leaf=leaf,
                  sub=SUB)
    # background canopy: mature trees behind the far rows so horizons read as a leafy suburb
    for k in range(46):
        side = k % 3
        if side == 0:
            x, z = r.uniform(-320, 360), r.uniform(205, 300)
        elif side == 1:
            x, z = r.uniform(-320, 360), r.uniform(-260, -95)
        else:
            x, z = r.choice((r.uniform(-330, -140), r.uniform(150, 380))), r.uniform(-60, 140)
        plant(ctx, 'tree_small_02', 'main', x, z, height_ft=r.uniform(26, 44), leaf=leaf, sub=SUB)
    for (x, z, h) in [(-34, -18, 13), (63, -24, 14), (100, -22, 13), (-60, -24, 12)]:
        plant(ctx, 'island_tree_02', 'main', x, z, height_ft=h, leaf=leaf, sub=SUB)
    # street trees along both park strips
    pz = (L.PARK[0] + L.PARK[1]) / 2
    fz = (L.FAR_PARK[0] + L.FAR_PARK[1]) / 2
    for x in (-95, -40, 82, 135, 190, -150):
        plant(ctx, 'tree_small_02', 'main', x + r.uniform(-3, 3), pz, height_ft=r.uniform(18, 26), leaf=leaf, sub=SUB)
    for x in (-110, -55, -2, 30, 70, 120, 170):
        plant(ctx, 'tree_small_02', 'main', x + r.uniform(-3, 3), fz, height_ft=r.uniform(18, 27), leaf=leaf, sub=SUB)
    return {'houses': n}
