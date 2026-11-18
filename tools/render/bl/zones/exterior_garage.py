"""Modern full-view sectional garage door (matte black aluminium + frosted glass), its inside
hardware (tracks, torsion spring, opener), exterior wall sconces and the "1095" house number
(runs inside Blender)."""
import math

import bpy

from ..common import FT, ft2bl
from . import exterior_layout as L
from .exterior_util import MB, coll, emit_mat, flat_mat
from .. import lighting

SUB = 'garage_door'

# D15 opening: x 23.402..38.259, y 0..7.0 in the garage front wall (z 50.83..51.28)
OX0, OX1, OH = 23.402, 38.259, 7.0
WALL_IN = 50.83                          # interior face of the garage front wall
DZ0, DZ1 = 50.595, 50.775                # door leaf thickness (sits just inside the jambs)
DX0, DX1 = OX0 - 0.15, OX1 + 0.15        # 1-3/4" overlap on the jambs
DY0, DY1 = 0.03, OH + 0.10
NSEC, NLITE = 4, 5


def garage_glass():
    """Smoky satin-etched lites without refraction (DESIGN.md glass rule): Fresnel glossy outer face over a
    mix of diffuse surface scatter (the etch), grey diffuse transmission and a little straight-through
    transparency. Shadow rays pass as grey transparency. From the street it reads as neutral grey glass in
    black frames instead of glowing with the garage's warm LEDs; from inside it glows softly with daylight."""
    from .exterior_util import _srgb
    m = bpy.data.materials.get('Z_exterior_garage_glass')
    if m:
        return m
    m = bpy.data.materials.new('Z_exterior_garage_glass')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    dot = nt.nodes.new('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0])
    nt.links.new(geo.outputs['Incoming'], dot.inputs[1])
    ab = nt.nodes.new('ShaderNodeMath')
    ab.operation = 'ABSOLUTE'
    nt.links.new(dot.outputs['Value'], ab.inputs[0])
    om = nt.nodes.new('ShaderNodeMath')
    om.operation = 'SUBTRACT'
    om.inputs[0].default_value = 1.0
    nt.links.new(ab.outputs[0], om.inputs[1])
    p5 = nt.nodes.new('ShaderNodeMath')
    p5.operation = 'POWER'
    p5.inputs[1].default_value = 5.0
    nt.links.new(om.outputs[0], p5.inputs[0])
    fr = nt.nodes.new('ShaderNodeMath')
    fr.operation = 'MULTIPLY_ADD'
    fr.inputs[1].default_value = 0.93
    fr.inputs[2].default_value = 0.07
    nt.links.new(p5.outputs[0], fr.inputs[0])
    gl = nt.nodes.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.08
    df = nt.nodes.new('ShaderNodeBsdfDiffuse')
    df.inputs['Color'].default_value = _srgb('#8c9093')
    tl = nt.nodes.new('ShaderNodeBsdfTranslucent')
    tl.inputs['Color'].default_value = (0.42, 0.44, 0.45, 1.0)
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    tr.inputs['Color'].default_value = (0.4, 0.42, 0.42, 1.0)
    m1 = nt.nodes.new('ShaderNodeMixShader')          # transmission: mostly diffuse, a little see-through
    m1.inputs['Fac'].default_value = 0.2
    nt.links.new(tl.outputs[0], m1.inputs[1])
    nt.links.new(tr.outputs[0], m1.inputs[2])
    m2 = nt.nodes.new('ShaderNodeMixShader')          # etched surface scatter
    m2.inputs['Fac'].default_value = 0.22
    nt.links.new(m1.outputs[0], m2.inputs[1])
    nt.links.new(df.outputs[0], m2.inputs[2])
    m3 = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fr.outputs[0], m3.inputs['Fac'])
    nt.links.new(m2.outputs[0], m3.inputs[1])
    nt.links.new(gl.outputs[0], m3.inputs[2])
    lp = nt.nodes.new('ShaderNodeLightPath')
    sh = nt.nodes.new('ShaderNodeBsdfTransparent')
    sh.inputs['Color'].default_value = (0.5, 0.51, 0.51, 1.0)
    fin = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Shadow Ray'], fin.inputs['Fac'])
    nt.links.new(m3.outputs[0], fin.inputs[1])
    nt.links.new(sh.outputs[0], fin.inputs[2])
    nt.links.new(fin.outputs[0], out.inputs['Surface'])
    m.diffuse_color = (0.3, 0.32, 0.33, 0.6)
    return m

def door(ctx):
    alu = 'black_aluminum'
    frame = MB()
    glass = MB()
    hw = MB()
    seal = MB()
    zc = (DZ0 + DZ1) / 2
    sh = (DY1 - DY0 - 0.012 * (NSEC - 1)) / NSEC
    stile, mull, rail = 0.21, 0.11, 0.16
    w = DX1 - DX0
    lite_w = (w - 2 * stile - (NLITE - 1) * mull) / NLITE
    for s in range(NSEC):
        y0 = DY0 + s * (sh + 0.012)
        y1 = y0 + sh
        # rails (top/bottom of section) with a meeting profile
        frame.box(DX0, DX1, y0, y0 + rail, DZ0, DZ1)
        frame.box(DX0, DX1, y1 - rail, y1, DZ0, DZ1)
        frame.box(DX0, DX0 + stile, y0 + rail, y1 - rail, DZ0, DZ1)
        frame.box(DX1 - stile, DX1, y0 + rail, y1 - rail, DZ0, DZ1)
        for k in range(1, NLITE):
            xm = DX0 + stile + k * lite_w + (k - 0.5) * mull
            frame.box(xm - mull / 2, xm + mull / 2, y0 + rail, y1 - rail, DZ0, DZ1)
        for k in range(NLITE):
            gx0 = DX0 + stile + k * (lite_w + mull)
            glass.box(gx0 - 0.02, gx0 + lite_w + 0.02, y0 + rail - 0.02, y1 - rail + 0.02, zc - 0.012, zc + 0.012)
            # thin glazing beads both faces (reads as a real pressed-in lite)
            for zf in (DZ0 + 0.03, DZ1 - 0.03):
                frame.box(gx0, gx0 + lite_w, y0 + rail, y0 + rail + 0.03, zf - 0.02, zf + 0.02)
                frame.box(gx0, gx0 + lite_w, y1 - rail - 0.03, y1 - rail, zf - 0.02, zf + 0.02)
        # inside hardware: hinges at every stile/mullion at section joints, roller brackets at ends
        if s > 0:
            for k in range(NLITE + 1):
                if k == 0:
                    xh = DX0 + stile / 2
                elif k == NLITE:
                    xh = DX1 - stile / 2
                else:
                    xh = DX0 + stile + k * lite_w + (k - 0.5) * mull
                hw.box(xh - 0.13, xh + 0.13, y0 - 0.2, y0 + 0.2, DZ0 - 0.035, DZ0)
        for xe, sgn in ((DX0, -1), (DX1, 1)):
            yr = y0 + (0.25 if s == 0 else 0.0)
            hw.box(xe - sgn * 0.3, xe + sgn * 0.02, yr - 0.12, yr + 0.12, DZ0 - 0.05, DZ0)
    # bottom astragal seal + top weather seal
    seal.box(DX0 + 0.02, DX1 - 0.02, 0.0, DY0 + 0.02, DZ0 + 0.02, DZ1 - 0.02)
    # inside lift handle on the bottom section
    hw.box(30.6, 31.06, 1.0, 1.06, DZ0 - 0.11, DZ0 - 0.05)
    hw.box(30.6, 30.66, 1.0, 1.06, DZ0 - 0.05, DZ0)
    hw.box(31.0, 31.06, 1.0, 1.06, DZ0 - 0.05, DZ0)
    frame.obj(ctx, 'ext garage door frame', alu, SUB, bevel=0.012, segments=2)
    glass.obj(ctx, 'ext garage door glass', garage_glass(), SUB)
    hw.obj(ctx, 'ext garage door hinges', 'black_metal', SUB, bevel=0.008, segments=1)
    seal.obj(ctx, 'ext garage door seal', flat_mat('Z_exterior_rubber', '#121212', 0.8), SUB)


def _arc_track(mb, xc, z_vert, y_v_top, y_h, z_back, w=0.2, d=0.12, segs=7):
    """Vertical track (y 0.3..y_v_top) + radius + horizontal track at y_h back to z_back."""
    r = y_h - y_v_top
    mb.box(xc - w / 2, xc + w / 2, 0.5, y_v_top, z_vert - d / 2, z_vert + d / 2)
    pz, py = z_vert, y_v_top
    for k in range(1, segs + 1):
        a = (math.pi / 2) * k / segs
        nz = z_vert - r + r * math.cos(a)
        ny = y_v_top + r * math.sin(a)
        cz, cy = (pz + nz) / 2, (py + ny) / 2
        seg_len = math.hypot(nz - pz, ny - py) + 0.02
        ang = math.atan2(ny - py, pz - nz)          # angle of the segment in the y/z plane
        # build an oriented box: along the segment in (z,y), width in x
        hl, hd = seg_len / 2, d / 2
        dz_, dy_ = -math.cos(ang), math.sin(ang)    # unit along segment (z,y)
        nz_, ny_ = -dy_, dz_                        # normal in (z,y)
        pts = []
        for (u, v) in ((-hl, -hd), (hl, -hd), (hl, hd), (-hl, hd)):
            pts.append((cz + dz_ * u + nz_ * v, cy + dy_ * u + ny_ * v))
        b = len(mb.v)
        for (zz, yy) in pts:
            mb.vert(xc - w / 2, yy, zz)
        for (zz, yy) in pts:
            mb.vert(xc + w / 2, yy, zz)
        for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            mb.face([b + i for i in f])
        pz, py = nz, ny
    mb.box(xc - w / 2, xc + w / 2, y_h - d / 2, y_h + d / 2, z_back, pz)


def hardware(ctx):
    trk = MB()
    zt = DZ0 - 0.09                         # track centre line just inside the door face
    y_vt, y_h = 6.45, 7.35
    z_back = DZ0 - (OH + 1.6)
    for xc in (DX0 - 0.13, DX1 + 0.13):
        _arc_track(trk, xc, zt, y_vt, y_h, z_back)
        # jamb angle (flag) bolted to the wall face
        side = -1 if xc < 30 else 1
        trk.box(xc + side * 0.1, xc + side * 0.16, 0.55, y_vt, zt, WALL_IN - 0.002)
        # rear hanger strap to the ceiling + diagonal brace
        trk.box(xc - 0.03, xc + 0.03, y_h + 0.06, 7.995, z_back + 0.2, z_back + 0.35)
        # rollers (stem into track) at each section
        sh = (DY1 - DY0) / NSEC
        for s in range(NSEC):
            yr = DY0 + s * sh + (0.25 if s == 0 else 0.0)
            trk.box(min(xc, (DX0 if side < 0 else DX1)), max(xc, (DX0 if side < 0 else DX1)), yr - 0.03, yr + 0.03,
                    zt - 0.03, zt + 0.03)
    trk.obj(ctx, 'ext garage door tracks', flat_mat('Z_exterior_galv', '#9a9c9c', 0.45, 0.9), SUB, bevel=0.006,
            segments=1)
    # torsion spring assembly above the door (shaft, drums, springs, bearing plates)
    ys, zs = 7.62, WALL_IN - 0.33
    parts = []
    shaft = ctx.cylinder('ext garage torsion shaft', (30.83, ys, zs), 0.045, DX1 - DX0 + 0.7, 'black_metal',
                         'ext_garage_door', verts=16, axis='X')
    parts.append(shaft)
    for xd in (DX0 - 0.13, DX1 + 0.13):
        parts.append(ctx.cylinder('ext garage cable drum', (xd, ys, zs), 0.2, 0.28, 'black_metal', 'ext_garage_door',
                                  verts=24, axis='X'))
    for xs in (30.83 - 1.45, 30.83 + 1.45):
        parts.append(ctx.cylinder('ext garage torsion spring', (xs, ys, zs), 0.115, 2.6,
                                  flat_mat('Z_exterior_spring', '#2c2c2c', 0.35, 0.8), 'ext_garage_door', verts=20,
                                  axis='X'))
    bp = MB()
    for xb in (DX0 - 0.13, 30.83, DX1 + 0.13):
        bp.box(xb - 0.06, xb + 0.06, 7.45, ys + 0.25, zs - 0.08, WALL_IN - 0.002)
    bp.obj(ctx, 'ext garage spring plates', 'black_metal', SUB)
    # opener: T-rail under the torsion tube, header bracket on the wall above the door, motor head
    op = MB()
    xr = 30.83
    zr0, zr1 = WALL_IN - 0.002, DZ0 - 11.0
    op.box(xr - 0.06, xr + 0.06, 7.28, 7.40, zr1, zr0 - 0.05)
    op.box(xr - 0.15, xr + 0.15, 7.18, 7.48, zr0 - 0.05, zr0)              # header bracket
    op.box(xr - 0.07, xr + 0.07, 7.17, 7.28, DZ0 - 1.4, DZ0 - 1.1)       # trolley
    arm_pts = [(DZ0 - 1.25, 7.2), (DZ0 - 0.55, 7.05), (DZ0 - 0.06, 6.88)]
    for (za, ya), (zb, yb) in zip(arm_pts[:-1], arm_pts[1:]):
        L_ = math.hypot(zb - za, yb - ya)
        n = max(2, int(L_ / 0.08))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            ya0, ya1 = ya + (yb - ya) * t0, ya + (yb - ya) * t1
            op.box(xr - 0.03, xr + 0.03, min(ya0, ya1) - 0.03, max(ya0, ya1) + 0.03,
                   min(za + (zb - za) * t0, za + (zb - za) * t1) - 0.01,
                   max(za + (zb - za) * t0, za + (zb - za) * t1) + 0.01)
    op.box(xr - 0.12, xr + 0.12, 6.75, 7.0, DZ0 - 0.06, DZ0)               # door bracket
    for xs in (xr - 0.42, xr + 0.42):                                        # ceiling hanger straps
        op.box(xs - 0.03, xs + 0.03, 7.6, 7.995, zr1 + 0.25, zr1 + 0.32)
    op.obj(ctx, 'ext garage opener rail', 'black_metal', SUB, bevel=0.006, segments=1)
    head = MB()
    head.box(xr - 0.55, xr + 0.55, 7.05, 7.6, zr1 - 0.2, zr1 + 1.2)
    head.obj(ctx, 'ext garage opener head', flat_mat('Z_exterior_opener', '#d9d8d4', 0.4), SUB, bevel=0.06,
             segments=3)
    lens = MB()
    lens.box(xr - 0.35, xr + 0.35, 7.03, 7.06, zr1 + 0.1, zr1 + 0.6)
    lens.obj(ctx, 'ext garage opener lens', flat_mat('Z_exterior_opener_lens', '#efefe9', 0.3), SUB)


def sconce(ctx, name, x, y, z, nx, nz, watts=6.0):
    """Modern up/down cylinder sconce on a wall with outward normal (nx, nz)."""
    rot = math.atan2(nx, nz)                      # local +z (SCENE) -> outward normal
    r, h = 0.16, 0.85
    off = 0.32
    cx, cz = x + nx * off, z + nz * off
    body = ctx.cylinder(f'ext sconce {name} body', (cx, y, cz), r, h, 'black_metal', 'ext_lights', verts=32)
    mb = MB()
    mb.box_c(x + nx * 0.025, y, z + nz * 0.025, 0.36, 0.62, 0.05, rot)            # backplate
    mb.box_c(x + nx * (off - r) / 2, y, z + nz * (off - r) / 2, 0.12, 0.14, off - r + 0.04, rot)   # arm
    mb.obj(ctx, f'ext sconce {name} plate', 'black_metal', 'lights', bevel=0.01, segments=2)
    glow = emit_mat('Z_exterior_sconce_glow', lighting.kelvin_rgb(2700), 6.0)
    for sgn in (-1, 1):
        d = ctx.cylinder(f'ext sconce {name} lens', (cx, y + sgn * (h / 2 - 0.03), cz), r * 0.82, 0.01, None,
                         'ext_lights', verts=24)
        d.data.materials.append(glow)
        ld = bpy.data.lights.new(f'ext sconce {name} {"up" if sgn > 0 else "down"}', 'SPOT')
        ld.energy = watts
        ld.color = lighting.kelvin_rgb(2700)
        ld.spot_size = math.radians(55)
        ld.spot_blend = 0.6
        ld.shadow_soft_size = 0.04
        lo = bpy.data.objects.new(ld.name, ld)
        lo.location = ft2bl(cx, y + sgn * (h / 2 + 0.02), cz)
        lo.rotation_euler = (0 if sgn < 0 else math.pi, 0, 0)
        coll(ctx, 'lights').objects.link(lo)
    return body


def house_number(ctx, text, x, y, z, height=0.5, nx=0.0, nz=1.0):
    cu = bpy.data.curves.new('ext house number', 'FONT')
    cu.body = text
    cu.size = height * FT * 1.38           # cap height ~ 0.72 of the em size
    cu.extrude = 0.012 * FT
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    try:
        cu.space_character = 1.12
    except AttributeError:
        pass
    ob = bpy.data.objects.new('ext house number', cu)
    coll(ctx, 'lights').objects.link(ob)
    # FONT objects lie in local XY; stand it up facing the street (+z SCENE = -Y Blender)
    ob.rotation_euler = (math.pi / 2, 0, math.atan2(nx, nz) if nz < 0.99 else 0.0)
    ob.location = ft2bl(x + nx * 0.06, y, z + nz * 0.06)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    mo = bpy.data.objects.new('ext house number 1095', me)
    mo.matrix_world = ob.matrix_world.copy()
    me.materials.clear()
    me.materials.append(ctx.mat('black_metal'))
    coll(ctx, 'lights').objects.link(mo)
    bpy.data.objects.remove(ob, do_unlink=True)
    # standoff pins
    mb = MB()
    for dx in (-0.45, 0.45):
        mb.box(x + dx - 0.015, x + dx + 0.015, y - 0.015, y + 0.015, z, z + nz * 0.06 + 0.001)
    mb.obj(ctx, 'ext house number pins', 'black_metal', 'lights')
    return mo


def mailbox(ctx, x, z):
    """Modern black post-mounted mailbox at the street end of the front walk."""
    from .exterior_util import GRADE
    mb = MB()
    mb.box(x - 0.15, x + 0.15, GRADE - 0.6, GRADE + 3.35, z - 0.15, z + 0.15)          # post
    mb.box(x - 0.42, x + 0.42, GRADE + 3.35, GRADE + 4.05, z - 0.62, z + 0.62)         # box (long axis N-S)
    mb.box(x - 0.40, x + 0.40, GRADE + 3.42, GRADE + 3.98, z + 0.62, z + 0.64)         # door face
    mb.obj(ctx, 'ext mailbox', 'black_metal', 'lights', bevel=0.02, segments=2)
    return 1


def build(ctx):
    mailbox(ctx, 14.75, 65.4)
    door(ctx)
    hardware(ctx)
    gf = L.GARAGE_FRONT
    sconce(ctx, 'garage W', (20.69 + OX0) / 2, 6.35, gf, 0.0, 1.0)
    sconce(ctx, 'garage E', (OX1 + 41.10) / 2, 6.35, gf, 0.0, 1.0)
    sconce(ctx, 'entry', 15.06, 5.95, 47.15, 0.0, 1.0)
    # rear: a pair flanking the living-room garden door D14 (x 25.28..27.86), as on the 1077 patio
    sconce(ctx, 'rear W', 24.68, 6.3, L.HZ0, 0.0, -1.0)
    sconce(ctx, 'rear E', 28.32, 6.3, L.HZ0, 0.0, -1.0)
    house_number(ctx, '1095', (20.69 + OX0) / 2, 5.25, gf)
    return {'door_sections': NSEC, 'lites': NSEC * NLITE}
