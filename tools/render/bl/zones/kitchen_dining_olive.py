"""Indoor olive tree in a large cream stoneware crock planter on the east wall's pier north of window W07 (v7
repair; under W07 until then) (kitchen_dining zone). Replaces the earlier walnut sideboard: one calm, tall living element between the
living room's sofa wall (the fireplace until the seventh round) and the kitchen run.

Procedural (no third-party model): three slender, gently twisting trunks (~2in) rise from the planter
and fork at ~4.1-4.6 ft into tapering branches and twigs that carry ~5000 narrow, opposite olive leaves
(2-3in, dark grey-green and silvery) in a loose, see-through canopy up to ~7 ft. Everything stays clear
of the east wall glass (x <= 40.35) and well above the kitchen worktop where the canopy reaches over it.
All dimensions SCENE feet.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

from . import kitchen_dining_kitchen as _K
from .kitchen_dining_geo import Geo, P, principled, srgb

COLL = 'kd olive'
P_H, P_RT, P_RB = 1.72, 0.86, 0.70   # planter height, top and bottom radius (21in x 20.6in)
WALL_LIMIT_X = 40.35           # nothing beyond this (window glass / wall face at 40.61)
RUN_END_Z = _K.RUN_E0          # kitchen east base run end panel; worktop at 3.0 ft (21.84 until the eighth round,
#                                when the run grew to the sheet's 10'-0" and the tree moved north with its end)
# v7 repair: the tree stands on the east wall's pier north of W07, between the sofa's south side table and the
# window's north jamb (plan z 14.45: planter z 13.59..15.31, 0.59 ft from the table, 0.76 ft from the jamb at
# 16.066). Until now it stood in the strip under W07 (0.26 ft off the kitchen run's end) and its crown covered 73 %
# of the window's width. No branch reaches south of WIN_LIMIT_Z, 0.30 ft north of the window's opening (a leaf is up to
# 0.26 ft long), so nothing stands in front of the window.
PLAN_CENTER_Z = 14.45
CENTER = (39.42, _K._pz(PLAN_CENTER_Z))     # planter centre (x, z): 0.33 ft off the east wall
WIN_LIMIT_Z = _K._pz(_K._W07_Z[0] - 0.30)   # concept z of the line the branches stay north of


def footprint():
    x, z = CENTER
    return (x - P_RT, x + P_RT, z - P_RT, z + P_RT)


# ----------------------------------------------------------------------------- materials
def _planter_material():
    name = 'Z_kitchen_dining_planter_crock'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 9.0
    nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = srgb('#d3c8b4') + (1,)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = srgb('#e2d9c8') + (1,)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    fine = nt.nodes.new('ShaderNodeTexNoise')
    fine.inputs['Scale'].default_value = 300.0
    fine.inputs['Detail'].default_value = 2.0
    nt.links.new(tc.outputs['Object'], fine.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    bump.inputs['Distance'].default_value = 0.0005
    nt.links.new(fine.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.42
    try:
        b.inputs['Coat Weight'].default_value = 0.25
        b.inputs['Coat Roughness'].default_value = 0.15
    except KeyError:
        pass
    m.diffuse_color = srgb('#dad0bd') + (1,)
    return m


def _bark_material():
    name = 'Z_kitchen_dining_olive_bark'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60.0, 60.0, 14.0)     # fissures run along the stems (mostly vertical)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.0
    nz.inputs['Detail'].default_value = 8.0
    nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = srgb('#4d463c') + (1,)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = srgb('#8a8273') + (1,)
    nt.links.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(nz.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.85
    m.diffuse_color = srgb('#6b6355') + (1,)
    return m


def _soil_material():
    name = 'Z_kitchen_dining_planter_mulch'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 140.0
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = srgb('#1f1914') + (1,)
    ramp.color_ramp.elements[1].color = srgb('#4a3d30') + (1,)
    nt.links.new(vo.outputs['Distance'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.8
    bump.inputs['Distance'].default_value = 0.003
    nt.links.new(vo.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.95
    m.diffuse_color = srgb('#2d241b') + (1,)
    return m


# ----------------------------------------------------------------------------- geometry
def _frame(t):
    """Two unit vectors perpendicular to t."""
    a = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
    s = t.cross(a).normalized()
    return s, t.cross(s).normalized()


def _tapered_tube(bm, pts, radii, sides=7):
    """Closed-ish tapered tube along SCENE points (bmesh, Blender coords)."""
    rings = []
    for i, p in enumerate(pts):
        if i == 0:
            t = (Vector(pts[1]) - Vector(pts[0]))
        elif i == len(pts) - 1:
            t = (Vector(pts[-1]) - Vector(pts[-2]))
        else:
            t = (Vector(pts[i + 1]) - Vector(pts[i - 1]))
        t.normalize()
        s, u = _frame(t)
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides
            q = Vector(p) + (s * math.cos(a) + u * math.sin(a)) * radii[i]
            ring.append(bm.verts.new(P(*q)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(sides):
            k2 = (k + 1) % sides
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    tip = bm.verts.new(P(*pts[-1]))
    for k in range(sides):
        bm.faces.new((rings[-1][k], rings[-1][(k + 1) % sides], tip))


def _limit(p):
    """Keep a SCENE point clear of the east wall glass and the kitchen worktop / run end."""
    x, y, z = p
    if x > WALL_LIMIT_X:
        x = WALL_LIMIT_X - (x - WALL_LIMIT_X) * 0.3
    if z > RUN_END_Z - 0.3 and y < 4.1:          # leaves stay well above the worktop
        z = RUN_END_Z - 0.3
    if z > 21.95 and y > 5.6 and x > 39.4:       # clear of the brass sconce on the pier beside W08
        z = 21.95
    if z > WIN_LIMIT_Z:                          # v7 repair: nothing in front of W07 (folded back like the wall limit)
        z = WIN_LIMIT_Z - (z - WIN_LIMIT_Z) * 0.3
    return (x, y, z)


def _branch(rnd, p0, d, L, r0, r1, n=8, droop=0.0, wig=0.03, curl=0.0):
    """Polyline + radii for a gently wandering branch from p0 along unit direction d."""
    pts, rad = [], []
    d = Vector(d).normalized()
    s, u = _frame(d)
    ph1, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
    f1, f2 = rnd.uniform(1.5, 3.0), rnd.uniform(2.0, 4.0)
    for i in range(n + 1):
        t = i / n
        q = Vector(p0) + d * (L * t)
        q += s * (wig * L * math.sin(f1 * t * math.pi + ph1) * t)
        q += u * (wig * L * math.sin(f2 * t * math.pi + ph2) * t)
        q.y -= droop * L * t * t
        q += s * (curl * L * t * t)
        pts.append(_limit(tuple(q)))
        rad.append(r0 + (r1 - r0) * (t ** 0.8))
    return pts, rad


def _leaf(bm, rnd, p, tang, side, L, mats_idx, faces_out):
    """Narrow lanceolate olive leaf at SCENE point p, angled out from the stem toward its tip."""
    up = Vector((0, 1, 0))
    axis = (tang * rnd.uniform(0.55, 0.8) + side * rnd.uniform(0.6, 0.85))
    axis.y -= rnd.uniform(0.0, 0.25)
    axis.normalize()
    nrm = (up - axis * up.dot(axis))
    if nrm.length < 1e-3:
        nrm = side.cross(axis)
    nrm.normalize()
    tw = rnd.uniform(-0.6, 0.6)                      # twist about the leaf axis
    wdir = nrm.cross(axis).normalized()
    nrm, wdir = (nrm * math.cos(tw) + wdir * math.sin(tw)), (wdir * math.cos(tw) - nrm * math.sin(tw))
    W = L * rnd.uniform(0.18, 0.24)
    base = Vector(p) + axis * 0.012
    sec = ((0.18, 0.75), (0.45, 1.0), (0.72, 0.75))
    vb = bm.verts.new(P(*base))
    curl = rnd.uniform(0.05, 0.16)
    rows = []
    for uu, ww in sec:
        c = base + axis * (uu * L) - nrm * (curl * L * uu * uu)
        fold = nrm * (0.04 * W)
        rows.append((bm.verts.new(P(*(c + wdir * (ww * W / 2) - fold))),
                     bm.verts.new(P(*(c + fold))),
                     bm.verts.new(P(*(c - wdir * (ww * W / 2) - fold)))))
    tip = bm.verts.new(P(*(base + axis * L - nrm * (curl * L))))
    fs = [(vb, rows[0][0], rows[0][1]), (vb, rows[0][1], rows[0][2])]
    for a, b in zip(rows, rows[1:]):
        fs += [(a[0], b[0], b[1], a[1]), (a[1], b[1], b[2], a[2])]
    fs += [(rows[-1][0], tip, rows[-1][1]), (rows[-1][1], tip, rows[-1][2])]
    for f in fs:
        face = bm.faces.new(f)
        face.material_index = mats_idx
        faces_out.append(face)


def _leaves_along(bm, rnd, pts, start, spacing, Lrange, counter):
    """Opposite, decussate leaf pairs along the polyline from fraction `start`."""
    seg = [(Vector(pts[i]), Vector(pts[i + 1])) for i in range(len(pts) - 1)]
    total = sum((b - a).length for a, b in seg)
    dist = start * total + rnd.uniform(0, spacing)
    rot = rnd.uniform(0, math.pi)
    faces = []
    acc = 0.0
    for a, b in seg:
        ln = (b - a).length
        while dist <= acc + ln and ln > 1e-6:
            f = (dist - acc) / ln
            p = a.lerp(b, f)
            t = (b - a).normalized()
            s, u = _frame(t)
            frac = dist / total
            Lf = rnd.uniform(*Lrange) * (1.0 - 0.3 * frac)
            for k in (0, 1):
                ang = rot + k * math.pi + rnd.uniform(-0.3, 0.3)
                side = (s * math.cos(ang) + u * math.sin(ang)).normalized()
                if rnd.random() < 0.9:
                    _leaf(bm, rnd, p, t, side, Lf, 0 if rnd.random() < 0.62 else 1, faces)
                    counter[0] += 1
            rot += math.pi / 2 + rnd.uniform(-0.25, 0.25)
            dist += spacing * rnd.uniform(0.8, 1.25)
        acc += ln
    # terminal leaf cluster
    tip = Vector(pts[-1])
    t = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
    s, _ = _frame(t)
    _leaf(bm, rnd, tip - t * 0.01, t, (t * 0.9 + s * 0.3).normalized(), rnd.uniform(*Lrange) * 0.7, 0, faces)
    counter[0] += 1


def build(ctx, g: Geo, seed=7):
    col = g.sub(COLL)
    cx, cz = CENTER
    rnd = random.Random(seed)
    # ---------------------------------------------------------------- planter (lathe) + mulch
    H, Rt, Rb = P_H, P_RT, P_RB
    prof = [(0.0, 0.0), (Rb - 0.03, 0.0), (Rb, 0.025), (Rb + 0.004, 0.06),
            (Rt - 0.004, H - 0.03), (Rt, H - 0.008), (Rt - 0.012, H), (Rt - 0.055, H),
            (Rt - 0.062, H - 0.02), (Rt - 0.07, H - 0.16), (0.0, H - 0.16)]
    g.lathe('kd olive planter', prof, cx, cz, _planter_material(), 96, col, y_base=0.0, sharp_deg=40)
    soil_y = H - 0.13
    g.lathe('kd olive mulch', [(0.0, soil_y + 0.012), (Rt * 0.5, soil_y + 0.008), (Rt - 0.066, soil_y)],
            cx, cz, _soil_material(), 64, col, y_base=0.0, sharp_deg=80)
    # ---------------------------------------------------------------- trunks, branches, twigs
    bm_wood = bmesh.new()
    bm_leaf = bmesh.new()
    nleaf = [0]
    twigs = []
    lean_dir = Vector((-0.35, 0.0, -0.1))           # the crown leans a little into the room
    for i in range(3):
        phi = 2 * math.pi * i / 3 + rnd.uniform(-0.3, 0.3) + 0.6
        out = Vector((math.cos(phi), 0.0, math.sin(phi)))
        base = Vector((cx, soil_y - 0.02, cz)) + out * rnd.uniform(0.07, 0.12)
        d = (Vector((0, 1, 0)) + out * rnd.uniform(0.1, 0.2) + lean_dir * 0.3).normalized()
        top = rnd.uniform(4.1, 4.6)                  # trunk fork height above the floor
        trunk, rad = _branch(rnd, base, d, top - soil_y, rnd.uniform(0.08, 0.095), 0.03, n=14, wig=0.035)
        _tapered_tube(bm_wood, trunk, rad, sides=9)
        # branches from the upper part of the trunk
        nb = rnd.randint(4, 5)
        for j in range(nb):
            k = int(len(trunk) * rnd.uniform(0.6, 0.95))
            k = min(k, len(trunk) - 2)
            p0 = Vector(trunk[k])
            az = phi + (j - (nb - 1) / 2) * rnd.uniform(0.9, 1.3) + rnd.uniform(-0.3, 0.3)
            outj = Vector((math.cos(az), 0.0, math.sin(az)))
            bd = (Vector((0, 1, 0)) * rnd.uniform(1.1, 1.8) + outj * rnd.uniform(0.5, 0.9) + lean_dir * 0.4).normalized()
            BL = rnd.uniform(1.6, 2.5)
            bp, br = _branch(rnd, p0, bd, BL, rad[k] * 0.7, 0.012, n=9, droop=0.13, wig=0.05)
            _tapered_tube(bm_wood, bp, br, sides=6)
            twigs.append((bp, 0.35))
            for q in range(rnd.randint(4, 6)):
                kk = int(len(bp) * rnd.uniform(0.25, 0.92))
                kk = min(kk, len(bp) - 2)
                tp0 = Vector(bp[kk])
                aq = az + rnd.uniform(-1.4, 1.4)
                tq = (Vector((0, 1, 0)) * rnd.uniform(0.0, 0.8) + Vector((math.cos(aq), 0, math.sin(aq)))).normalized()
                TL = rnd.uniform(0.5, 1.1)
                tp, tr = _branch(rnd, tp0, tq, TL, br[kk] * 0.7, 0.005, n=6, droop=0.35, wig=0.06)
                _tapered_tube(bm_wood, tp, tr, sides=5)
                twigs.append((tp, 0.08))
                for _ in range(rnd.randint(1, 2)):       # side shoots fill the crown
                    k3 = min(int(len(tp) * rnd.uniform(0.3, 0.75)), len(tp) - 2)
                    a3 = aq + rnd.choice((-1, 1)) * rnd.uniform(0.5, 1.2)
                    d3 = (Vector((0, 1, 0)) * rnd.uniform(0.1, 0.7) + Vector((math.cos(a3), 0, math.sin(a3)))).normalized()
                    sp_, sr_ = _branch(rnd, tp[k3], d3, rnd.uniform(0.3, 0.55), tr[k3] * 0.7, 0.003, n=4, droop=0.3, wig=0.06)
                    _tapered_tube(bm_wood, sp_, sr_, sides=4)
                    twigs.append((sp_, 0.05))
        # trunk leader continues into the crown
        lp, lr = _branch(rnd, trunk[-1], (d + Vector((0, 0.6, 0))).normalized(), rnd.uniform(1.5, 2.1),
                         rad[-1], 0.008, n=7, droop=0.05, wig=0.05)
        _tapered_tube(bm_wood, lp, lr, sides=6)
        twigs.append((lp, 0.3))
    for pts, start in twigs:
        _leaves_along(bm_leaf, rnd, pts, start, 0.038, (0.18, 0.26), nleaf)
    wood = g.from_bmesh('kd olive wood', bm_wood, _bark_material(), col, smooth=True)
    leaf_a = principled('olive_leaf_top', srgb('#626c52'), 0.5, transl=srgb('#8f9a6e'))
    leaf_b = principled('olive_leaf_silver', srgb('#949c86'), 0.55, transl=srgb('#a8b090'))
    leaves = g.from_bmesh('kd olive leaves', bm_leaf, [leaf_a, leaf_b], col, smooth=False)
    for ob in (wood, leaves):
        ob.data.update()
    bpy.context.view_layer.update()
    return {'olive_leaves': nleaf[0], 'olive_tris': sum(len(p.vertices) - 2 for o in (wood, leaves) for p in o.data.polygons),
            'planter_xz': [round(v, 2) for v in footprint()]}
