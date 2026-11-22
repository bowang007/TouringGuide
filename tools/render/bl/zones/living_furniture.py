"""Procedural modern furniture for the living zone (runs inside Blender).

Every builder works in a local SCENE-feet frame with its origin on the floor (y = 0) and its
front facing +x, creates its pieces parented to `parent` (an Empty) and returns them.
"""
import math

import bpy

from ..common import FT
from .. import lighting
from . import living_geo as G

COLL = 'zone_living'
ARM_T = 0.6          # sofa track-arm thickness (ft)
ARM_TOP = 1.98       # arm top height above the sofa base (ft)
ARM_R = 0.13         # arm top edge radius (ft): crisp modern track arm, not a rolled arm


# --------------------------------------------------------------------------- materials
def _principled(name, color, rough=0.5, sheen=0.0, coat=0.0, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = color + (1,)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if sheen:
        b.inputs['Sheen Weight'].default_value = sheen
        b.inputs['Sheen Roughness'].default_value = 0.5
    if coat:
        b.inputs['Coat Weight'].default_value = coat
        b.inputs['Coat Roughness'].default_value = 0.05
    m.diffuse_color = color + (1,)
    return m


def shade_material():
    """Warm linen lamp shade: diffuse outside + translucent so the bulb inside makes it glow."""
    name = 'Z_living_lampshade'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    tex = nt.nodes.new('ShaderNodeTexNoise')
    tex.inputs['Scale'].default_value = 900.0
    tex.inputs['Detail'].default_value = 2.0
    ramp = nt.nodes.new('ShaderNodeMapRange')
    ramp.inputs['To Min'].default_value = 0.92
    ramp.inputs['To Max'].default_value = 1.0
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Value'])
    base = (0.86, 0.80, 0.70)
    mulc = nt.nodes.new('ShaderNodeMix')
    mulc.data_type = 'RGBA'
    mulc.blend_type = 'MULTIPLY'
    mulc.inputs['Factor'].default_value = 1.0
    G.sock(mulc.inputs, 'A').default_value = base + (1,)
    nt.links.new(ramp.outputs['Result'], G.sock(mulc.inputs, 'B'))
    dif = nt.nodes.new('ShaderNodeBsdfDiffuse')
    nt.links.new(G.sock(mulc.outputs, 'Result'), dif.inputs['Color'])
    tr = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tr.inputs['Color'].default_value = (0.90, 0.82, 0.70, 1)
    mix = nt.nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.4
    nt.links.new(dif.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    m.diffuse_color = base + (1,)
    return m


def knit_material():
    """Chunky oatmeal knit for the throw: V-stitch columns from the throw's UVs (u across, v along the
    drape, both in feet), as bump plus a slight tone change in the grooves."""
    name = 'Z_living_knit'
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    col = (0.66, 0.60, 0.51)
    b.inputs['Roughness'].default_value = 0.95
    b.inputs['Sheen Weight'].default_value = 0.7
    b.inputs['Sheen Roughness'].default_value = 0.35

    def mth(op, a, bv=None, c=None):
        n = nt.nodes.new('ShaderNodeMath')
        n.operation = op
        for i, v in enumerate((a, bv, c)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                nt.links.new(v, n.inputs[i])
            else:
                n.inputs[i].default_value = v
        return n.outputs[0]
    uvn = nt.nodes.new('ShaderNodeUVMap')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(uvn.outputs['UV'], sep.inputs[0])
    cu = mth('DIVIDE', sep.outputs['X'], 0.125)                # ~1.5in chunky stitch columns
    cv = mth('DIVIDE', sep.outputs['Y'], 0.085)                # ~1in stitch rows
    a_ = mth('ABSOLUTE', mth('SUBTRACT', mth('FRACT', cu), 0.5))
    chev = mth('FRACT', mth('MULTIPLY_ADD', a_, 1.3, cv))
    loop = mth('SINE', mth('MULTIPLY', chev, 3.14159))
    groove = nt.nodes.new('ShaderNodeMapRange')
    groove.interpolation_type = 'SMOOTHSTEP'
    groove.inputs['From Min'].default_value = 0.5
    groove.inputs['From Max'].default_value = 0.36
    nt.links.new(a_, groove.inputs['Value'])
    h = mth('MULTIPLY', loop, groove.outputs['Result'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 1.0
    bump.inputs['Distance'].default_value = 0.006
    nt.links.new(h, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    tone = nt.nodes.new('ShaderNodeMapRange')
    tone.inputs['To Min'].default_value = 0.72
    tone.inputs['To Max'].default_value = 1.0
    nt.links.new(h, tone.inputs['Value'])
    cm = nt.nodes.new('ShaderNodeVectorMath')
    cm.operation = 'SCALE'
    cm.inputs[0].default_value = col
    nt.links.new(tone.outputs['Result'], cm.inputs['Scale'])
    nt.links.new(cm.outputs[0], b.inputs['Base Color'])
    m.diffuse_color = col + (1,)
    return m


def mat_ceramic_white():
    return _principled('Z_living_ceramic_glaze', (0.86, 0.84, 0.80), rough=0.22, coat=0.4)


# ------------------------------------------------------------------------------- sofa
def sofa(ctx, parent, L=7.9, D=3.25, rug_x=None, rug_t=0.045):
    """Low modern boucle sofa on a recessed black plinth; back at local x=0, front at x=D."""
    fab = 'fabric_boucle'
    out = []
    leg_h = 0.2
    ta = ARM_T                          # arm thickness
    # recessed plinth (reads as a shadow gap; sits on floor/rug)
    v, f = G.box_verts(0.22, D - 0.22, 0.0, leg_h + 0.03, -(L / 2 - 0.22), L / 2 - 0.22)
    o = G.obj(ctx, 'sofa plinth', v, f, 'paint_black', COLL, parent, smooth=False)
    G.bevel(o, 0.01, 1)
    out.append(o)
    deck_top = leg_h + 0.66
    # deck / base
    v, f = G.rounded_box(D / 2, (deck_top - leg_h) / 2, L / 2, 0.14, n=5, nmid=6, puff=0.04, puff_axis=0)
    out.append(G.obj(ctx, 'sofa base', G.translate(v, D / 2, (deck_top + leg_h) / 2, 0), f, fab, COLL, parent))
    # arms (soft, rounded tops)
    arm_top = ARM_TOP
    for s_ in (-1, 1):
        v, f = G.rounded_box(D / 2, (arm_top - leg_h) / 2, ta / 2, 0.1, n=5, nmid=6, ry=ARM_R, rz=ARM_R, rx=0.12,
                             puff=0.025, puff_axis=2)
        out.append(G.obj(ctx, 'sofa arm', G.translate(v, D / 2, (arm_top + leg_h) / 2, s_ * (L / 2 - ta / 2)),
                         f, fab, COLL, parent))
    # back frame
    back_top = 2.12
    bt = 0.6
    v, f = G.rounded_box(bt / 2, (back_top - leg_h) / 2, L / 2 - ta + 0.03, 0.2, n=5, nmid=6, ry=0.26)
    out.append(G.obj(ctx, 'sofa back', G.translate(v, bt / 2, (back_top + leg_h) / 2, 0), f, fab, COLL, parent))
    # seat cushions: crowned, soft front roll
    seat_top = 1.47
    inner = L / 2 - ta
    n_seat = 2
    w = (2 * inner - 0.025 * (n_seat - 1)) / n_seat
    for i in range(n_seat):
        zc = -inner + w / 2 + i * (w + 0.025)
        v, f = G.rounded_box((D - bt) / 2 + 0.01, (seat_top - deck_top) / 2 + 0.02, w / 2, 0.2, n=6, nmid=7,
                             puff=0.16, puff_axis=1, rz=0.16)
        out.append(G.obj(ctx, 'sofa seat cushion', G.translate(v, bt + (D - bt) / 2 + 0.01,
                                                               (seat_top + deck_top) / 2 - 0.02, zc), f, fab, COLL, parent))
    # back cushions: plump, leaning back ~15 deg, resting on the seat against the frame
    for i in range(n_seat):
        zc = -inner + w / 2 + i * (w + 0.025)
        hb, tb = 1.08, 0.66
        v, f = G.rounded_box(tb / 2, hb / 2, w / 2 - 0.005, 0.26, n=6, nmid=7, puff=0.2, puff_axis=0, rz=0.2)
        v = G.translate(v, bt + tb / 2 - 0.06, seat_top - 0.08 + hb / 2, zc)
        v = G.rot_z_scene(v, math.radians(15), cx=bt, cy=seat_top)
        out.append(G.obj(ctx, 'sofa back cushion', v, f, fab, COLL, parent))
    return out


def sofa_pillow(ctx, parent, x, z, size, mat, tilt_deg=16.0, seat_top=1.47, thick=0.56, yaw=0.0, name='pillow',
                h=None, chop=0.0):
    """Throw pillow standing on the seat (bottom at seat_top) leaning back by tilt_deg. chop>0 gives the
    stylist's 'karate chop' dent in the top edge."""
    h = h or size
    v, f = G.pillow(size, h, thick, chop=chop)
    v = G.translate(v, 0, h / 2 - 0.07, 0)             # bottom edge (slightly squashed in)
    v = G.rot_z_scene(v, math.radians(tilt_deg), 0, 0)
    if yaw:
        v = G.rot_y(v, yaw)
    v = G.translate(v, x, seat_top, z)
    return G.obj(ctx, name, v, f, mat, COLL, parent, weld=True)


def throw_over_arm(ctx, parent, L=7.9, D=3.25, mat=None, side=-1, ta=ARM_T, arm_top=ARM_TOP, seat_top=1.47,
                   x_range=(0.75, 2.75)):
    """Knit throw draped over one sofa arm: a fold lies on the seat, wraps over the arm and the
    end hangs down the outside. Built as a ribbon offset clear of the (puffed) arm surface.
    x_range: the stretch of the arm it covers, measured from the sofa's back."""
    import numpy as np
    o = 0.06                                    # clearance from the upholstery
    zc = side * (L / 2 - ta / 2)                # arm centre line
    hw = ta / 2 + 0.02                          # arm half width incl. side puff
    R = ARM_R + o                               # offset radius around the arm's top edges
    cy = arm_top - ARM_R
    czi, czo = zc - side * (hw - ARM_R), zc + side * (hw - ARM_R)
    path = []
    for t in np.linspace(0, 1, 7):              # lying on the seat, running toward the arm
        path.append((side * (L / 2 - ta - 1.0 + 1.0 * t) - side * o, seat_top + 0.03 + 0.05 * t * t))
    for t in np.linspace(0, 1, 6)[1:]:          # up the inner face of the arm
        path.append((zc - side * (hw + o), seat_top + 0.08 + (cy - seat_top - 0.08) * t))
    for t in np.linspace(0, 1, 6)[1:]:          # over the inner top edge
        a = math.pi / 2 * t
        path.append((czi - side * R * math.cos(a), cy + R * math.sin(a)))
    for t in np.linspace(0, 1, 4)[1:-1]:        # across the flat top
        path.append((czi + (czo - czi) * t, cy + R))
    for t in np.linspace(0, 1, 6):              # over the outer top edge
        a = math.pi / 2 * (1 - t)
        path.append((czo + side * R * math.cos(a), cy + R * math.sin(a)))
    for t in np.linspace(0, 1, 9)[1:]:          # hanging outside, drifting slightly out
        path.append((zc + side * (hw + o + 0.02 * t), cy - 1.0 * t))
    path = np.array(path)
    xs = np.linspace(x_range[0], x_range[1], 28)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    s_hang = seg[-9]
    verts, faces, uvs = [], [], []
    nx = len(xs)
    for i, (zz, yy) in enumerate(path):
        for j, xx in enumerate(xs):
            u = (xx - xs[0]) / (xs[-1] - xs[0])
            hang = max(0.0, seg[i] - s_hang) / (seg[-1] - s_hang)
            amp = 0.02 + 0.07 * hang
            ripple = amp * math.sin(u * 9.0 + seg[i] * 1.7) * math.sin(math.pi * u)
            drop = 0.14 * math.sin(math.pi * u) * hang
            normal_dir = side if (hang > 0 or seg[i] < seg[6]) else 0.0
            # hand-finished hems: the side edges wander a little instead of running dead straight
            ew = max(0.0, 1.0 - min(j, nx - 1 - j) / 3.0)
            xj = xx + ew * 0.035 * math.sin(seg[i] * 4.3 + (0.0 if j < nx / 2 else 2.1)) * (1 if j < nx / 2 else -1)
            verts.append((xj, yy - drop, zz + normal_dir * abs(ripple) + (side * ripple * 0.3 if hang > 0 else 0.0)))
            uvs.append((xx, seg[i]))
    for i in range(len(path) - 1):
        for j in range(nx - 1):
            faces.append((i * nx + j, i * nx + j + 1, (i + 1) * nx + j + 1, (i + 1) * nx + j))
    ob = G.obj(ctx, 'sofa throw', verts, faces, mat or knit_material(), COLL, parent, uvs=uvs)
    so = ob.modifiers.new('Solidify', 'SOLIDIFY')
    so.thickness = 0.065 * FT
    so.offset = 0.0
    sub = ob.modifiers.new('Subsurf', 'SUBSURF')
    sub.levels = 1
    sub.render_levels = 2
    return ob


# ------------------------------------------------------------------------- lounge chair
def barrel_chair(ctx, parent, base_y=0.0, R_out=1.2, R_in=0.8, back_h=2.32, arm_h=1.88):
    """Sculptural boucle barrel lounge chair centred on the local origin, front toward +x."""
    fab = 'fabric_boucle'
    out = []
    plinth_h = 0.12
    v, f = G.lathe([(0.0, base_y), (0.82, base_y), (0.82, base_y + plinth_h), (0.0, base_y + plinth_h)],
                   n=48, cap_bottom=False)
    po = G.obj(ctx, 'chair plinth', v, f, 'paint_black', COLL, parent)
    out.append(po)
    yb = base_y + plinth_h - 0.02
    th0, th1 = math.radians(48), math.radians(312)
    secs = []
    N = 30

    def section(th, r_in, r_out, y0, y1, shrink=0.0):
        c1, c2 = 0.12, 0.17
        cr, cy = (r_in + r_out) / 2, (y0 + y1) / 2
        pts = [(r_in + c1, y0), (r_out - c1, y0), (r_out, y0 + c1), (r_out, y1 - c2),
               (r_out - c2, y1), (r_in + c2, y1), (r_in, y1 - c2), (r_in, y0 + c1)]
        res = []
        for r, y in pts:
            r = cr + (r - cr) * (1 - shrink)
            y = cy + (y - cy) * (1 - shrink)
            res.append((r * math.cos(th), y, r * math.sin(th)))
        return res

    def top(th):
        u = (th - th0) / (th1 - th0)
        return arm_h + (back_h - arm_h) * math.sin(math.pi * u) ** 1.4

    ths = [th0 + (th1 - th0) * i / N for i in range(N + 1)]
    d = math.radians(3.5)
    secs.append(section(th0 - d, R_in, R_out, yb, base_y + top(th0), shrink=0.55))
    for th in ths:
        secs.append(section(th, R_in, R_out, yb, base_y + top(th)))
    secs.append(section(th1 + d, R_in, R_out, yb, base_y + top(th1), shrink=0.55))
    v, f = G.sweep_ring(secs)
    out.append(G.obj(ctx, 'chair shell', v, f, fab, COLL, parent, subsurf=2))
    # seat drum (front of the base) and seat cushion
    v, f = G.lathe([(0.0, yb), (0.93, yb), (0.98, yb + 0.06), (0.99, yb + 0.5), (0.97, base_y + 1.0),
                    (0.90, base_y + 1.06), (0.0, base_y + 1.06)], n=56, cap_bottom=False)
    out.append(G.obj(ctx, 'chair seat base', G.translate(v, 0.12, 0, 0), f, fab, COLL, parent, subsurf=1))
    st = base_y + 1.44
    v, f = G.lathe([(0.0, base_y + 1.04), (0.80, base_y + 1.04), (0.93, base_y + 1.1), (0.97, base_y + 1.25),
                    (0.93, st - 0.05), (0.80, st), (0.4, st + 0.02), (0.0, st + 0.025)], n=56, cap_bottom=False)
    out.append(G.obj(ctx, 'chair seat cushion', G.translate(v, 0.1, 0, 0), f, fab, COLL, parent, subsurf=1))
    return out


# ------------------------------------------------------------------------- tables
def coffee_table(ctx, parent, r=1.42, top_y=1.25, t=0.15, base_y=0.0):
    """Round walnut coffee table on a black steel cross base (two flat-bar hoops at right angles), centred on the
    local origin."""
    out = []
    v, f = G.prism(G.circle_outline(r, 96), top_y - t, top_y)
    o = G.obj(ctx, 'coffee table top', v, f, 'walnut_slab', COLL, parent)
    G.bevel(o, 0.045, 4, angle=40)
    out.append(o)
    reach = r - 0.36                    # the legs stand well inside the top's edge
    y_top = top_y - t
    parts = []
    for k, a in enumerate((math.radians(45), math.radians(135))):
        tw = 0.07 - 0.004 * k           # the second hoop a hair slimmer: no coincident faces where the two cross
        hoop = [G.box_verts(-reach, reach, base_y, base_y + tw, -tw / 2, tw / 2),
                G.box_verts(-reach, reach, y_top - tw, y_top, -tw / 2, tw / 2),
                G.box_verts(-reach, -reach + tw, base_y, y_top, -tw / 2, tw / 2),
                G.box_verts(reach - tw, reach, base_y, y_top, -tw / 2, tw / 2)]
        v, f = G.merge(*hoop)
        parts.append((G.rot_y(v, a), f))
    v, f = G.merge(*parts)
    o = G.obj(ctx, 'coffee table frame', v, f, 'black_metal', COLL, parent, smooth=False)
    G.bevel(o, 0.008, 2)
    out.append(o)
    return out


def side_table(ctx, parent, r=0.68, h=1.85, base_y=0.0):
    out = []
    v, f = G.lathe([(0.0, h - 0.11), (r - 0.03, h - 0.11), (r, h - 0.08), (r, h - 0.03), (r - 0.03, h), (0.0, h)],
                   n=64, cap_bottom=False)
    out.append(G.obj(ctx, 'side table top', G.translate(v, 0, base_y, 0), f, 'walnut_slab', COLL, parent))
    v, f = G.lathe([(0.0, 0.0), (0.4, 0.0), (0.41, 0.02), (0.4, 0.05), (0.06, 0.07), (0.045, 0.12),
                    (0.045, h - 0.13), (0.09, h - 0.11), (0.0, h - 0.11)], n=48, cap_bottom=False)
    out.append(G.obj(ctx, 'side table pedestal', G.translate(v, 0, base_y, 0), f, 'black_metal', COLL, parent))
    return out


# ------------------------------------------------------------------------- lamps
def table_lamp(ctx, parent, world_xyz, base_y, lights_coll, shade_r=0.62):
    """Ceramic gourd base + linen drum shade (bottom radius shade_r), bulb inside. world_xyz=(x, z) for the light."""
    out = []
    prof = [(0.0, 0.0), (0.16, 0.0), (0.2, 0.03), (0.27, 0.2), (0.29, 0.38), (0.25, 0.58), (0.16, 0.74),
            (0.07, 0.83), (0.055, 0.9), (0.0, 0.9)]
    v, f = G.lathe([(r, y + base_y) for r, y in prof], n=56, cap_bottom=False)
    out.append(G.obj(ctx, 'table lamp base', v, f, mat_ceramic_white(), COLL, parent))
    v, f = G.lathe([(0.0, base_y + 0.9), (0.025, base_y + 0.9), (0.025, base_y + 1.62), (0.0, base_y + 1.62)],
                   n=16, cap_bottom=False)
    out.append(G.obj(ctx, 'table lamp neck', v, f, 'black_metal', COLL, parent))
    y0, y1 = base_y + 1.12, base_y + 1.95
    rb, rt = shade_r, shade_r - 0.04
    v, f = G.lathe([(rb, y0), (rt, y1), (rt - 0.012, y1), (rb - 0.012, y0), (rb, y0)], n=64,
                   cap_bottom=False)
    out.append(G.obj(ctx, 'table lamp shade', v, f, shade_material(), COLL, parent))
    x, z = world_xyz
    lighting.point_light(ctx, x, (y0 + y1) / 2 - 0.05, z, watts=9.0, kelvin=2700, radius_ft=0.12,
                         coll=lights_coll, name='living table lamp')
    return out


# ------------------------------------------------------------------------- rug, books
def rug(ctx, cx, cz, r, t=0.045):
    """Round cream wool rug of radius r centred on (cx, cz)."""
    v, f = G.prism(G.circle_outline(r, 128), 0.002, t)
    o = G.obj(ctx, 'living rug', G.translate(v, cx, 0, cz), f, 'rug_wool_cream', COLL)
    G.bevel(o, 0.018, 3, angle=40)
    return o


BOOK_COLORS = [(0.78, 0.72, 0.62), (0.23, 0.23, 0.22), (0.62, 0.64, 0.56), (0.88, 0.86, 0.82),
               (0.55, 0.42, 0.30)]


def book(ctx, parent, x, y, z, w, d, t, color, yaw=0.0, name='book'):
    """Hardcover book lying flat; w along x, d along z, t thick. Bottom at y."""
    cover = _principled(f'Z_living_bookcloth_{int(color[0]*100)}_{int(color[1]*100)}_{int(color[2]*100)}',
                        color, rough=0.75, sheen=0.3)
    pages = _principled('Z_living_pages', (0.84, 0.81, 0.74), rough=0.9)
    ct = 0.012
    parts_c = [G.box_verts(-w / 2, w / 2, 0, ct, -d / 2, d / 2),
               G.box_verts(-w / 2, w / 2, t - ct, t, -d / 2, d / 2),
               G.box_verts(-w / 2, -w / 2 + ct, 0, t, -d / 2, d / 2)]
    v, f = G.merge(*parts_c)
    v = G.translate(G.rot_y(v, yaw), x, y, z)
    o1 = G.obj(ctx, name + ' cover', v, f, cover, COLL, parent, smooth=False)
    G.bevel(o1, 0.004, 1)
    v, f = G.box_verts(-w / 2 + ct, w / 2 - 0.012, ct, t - ct, -d / 2 + 0.012, d / 2 - 0.012)
    v = G.translate(G.rot_y(v, yaw), x, y, z)
    o2 = G.obj(ctx, name + ' pages', v, f, pages, COLL, parent, smooth=False)
    return [o1, o2]
