"""Stained-cedar carriage-house sectional garage door (owner's reference: a framed grid of 4 x 4
panels with vertical V-groove plank infill, a top row of 3 x 2 glass lites per panel column, black
pulls), its inside hardware (tracks, torsion spring, opener), the black lantern sconces flanking the
door, the other exterior wall sconces and the "1095" house number (runs inside Blender)."""
import math
import random

import bmesh
import bpy

from ..common import FT, ft2bl
from . import exterior_layout as L
from .exterior_util import MB, coll, emit_mat, flat_mat
from .. import lighting

SUB = 'garage_door'

# vehicle door opening: x 22.957..37.816 (14'-10", centred in the garage), y 0..7.0 in the garage front wall
# (z 52.335..52.785)
OX0, OX1 = L.GARAGE_DOOR
OH = 7.0
XC = (OX0 + OX1) / 2                     # door centre line (torsion shaft, opener rail)
WALL_IN = 52.335                         # interior face of the garage front wall
DZ0, DZ1 = WALL_IN - 0.235, WALL_IN - 0.055   # door leaf thickness (sits just inside the jambs); DZ1 = street face
DX0, DX1 = OX0 - 0.15, OX1 + 0.15        # 1-3/4" overlap on the jambs
DY0, DY1 = 0.03, OH + 0.10
ZC = (DZ0 + DZ1) / 2
NSEC = 4                                 # sections (unchanged: same track, rollers and opener)
GAP = 0.012                              # section joint (sealed by a recessed rubber tongue)
SH = (DY1 - DY0 - GAP * (NSEC - 1)) / NSEC
# carriage-house frame-and-panel grid (feet): 4 panel columns, stiles and rails ~4-5" like the reference
NCOL = 4
LITES = (3, 2)                           # glass lites per column in the top section (across, up)
STILE_O = 0.15 + 0.36                    # outer stiles: 0.15 behind the jamb + 4 1/4" visible
STILE_I = 0.40                           # intermediate stiles (4 3/4")
RAIL_J = 0.19                            # rail on each side of a section joint (band ~4 3/4" with the joint)
RAIL_B = 0.34                            # bottom rail of the bottom section
RAIL_T = DY1 - OH + 0.22                 # top rail of the top section (0.10 hidden behind the head)
PW = (DX1 - DX0 - 2 * STILE_O - (NCOL - 1) * STILE_I) / NCOL     # panel / window width (~3'-2 3/4")
PANEL_REC = 0.055                        # panel faces sit 2/3" behind the frame faces (both sides)
PLANK = 0.46                             # ~5 1/2" V-groove planks
MUNTIN = 0.075                           # 7/8" grilles
MOULD = (0.06, 0.035)                    # panel moulding: 3/4" wide, 7/16" proud of the planks
CEDAR = '#987452'                        # warm honey-brown semi-transparent stain on western red cedar
FRAME_TONE = 0.84                        # stiles / rails take the stain a little darker (reference)


def _col_x(c):
    """x range of panel column c (0 = west)."""
    x0 = DX0 + STILE_O + c * (PW + STILE_I)
    return x0, x0 + PW


def _sec_y(s):
    y0 = DY0 + s * (SH + GAP)
    return y0, y0 + SH


def _rails(s):
    return (RAIL_B if s == 0 else RAIL_J), (RAIL_T if s == NSEC - 1 else RAIL_J)


class _Wood(MB):
    """MB that records a per-face 'gd' attribute (random, grain direction, tone) for the cedar shader:
    each board gets its own cut of the veneer and its own tone; rails run their grain horizontally."""

    def __init__(self, seed):
        super().__init__()
        self.gd = []
        self.rng = random.Random(seed)

    def piece(self, x0, x1, y0, y1, z0, z1, horizontal, tone, rnd=None):
        n = len(self.f)
        self.box(x0, x1, y0, y1, z0, z1)
        v = (self.rng.random() if rnd is None else rnd, 1.0 if horizontal else 0.0, tone)
        self.gd.extend([v] * (len(self.f) - n))

    def emit(self, ctx, name, mat, bevel, segments=2):
        ob = self.obj(ctx, name, mat, SUB, bevel=bevel, segments=segments)
        me = ob.data
        if len(me.polygons) == len(self.gd):
            at = me.attributes.new('gd', 'FLOAT_VECTOR', 'FACE')
            at.data.foreach_set('vector', [c for v in self.gd for c in v])
        else:
            print(f'[exterior] {name}: face count changed ({len(me.polygons)} != {len(self.gd)}); no grain attribute')
        return ob


def cedar_material(ctx):
    """Z_garage_cedar: semi-transparent warm-brown stain on clear vertical-grain western red cedar.
    World-space planar mapping (no UVs, MATERIALS.md); the per-face 'gd' attribute picks the grain
    direction (planks and stiles vertical, rails horizontal), a different cut of the veneer per board
    and the board's tone. Ash (fine straight grain, the clear boards) and teak (some figure and small
    knots) veneers graded to the stain colour; satin oil finish."""
    name = 'Z_garage_cedar'
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    g = None
    try:
        from .. import materials_pbr as P
        g = P._G('wood_cladding')
        g.m.name = name
        fr = g.frame()
        a, b, A, B = g.planar()
        at = g.new('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='gd')
        rnd, hdir, tone = g.sep(at.outputs['Vector'])
        h = fr['horiz']
        al = g.lerp(g.lerp(b, a, hdir), a, h)          # along the grain
        ac = g.lerp(g.lerp(a, b, hdir), b, h)          # across the grain
        Al = g.vmix(g.vmix(B, A, hdir), A, h)
        Ac = g.vmix(g.vmix(A, B, hdir), B, h)
        al = g.mad(rnd, 23.7, al)
        ac = g.mad(rnd, 11.3, ac)
        target = P._hexlin(CEDAR)
        # clear boards: ash's fine straight grain (as the house's cedar cladding) - sapele's wide pale
        # ribbon band made whole planks read ~25% lighter; figured boards: teak
        sS = g.sample('ash_veneer', al, ac, Al, Ac, 0.8, grain='u', stretch=1.6)
        sT = g.sample('teak_veneer', al, ac, Al, Ac, 0.8, grain='u', stretch=1.5)
        if sS and sT:
            pick = g.gt(g.fract(g.mul(rnd, 7.13)), 0.62)
            col = g.cmix(g.grade(sS['color'], sS['mean'], target, 1.9, sat=0.7),
                         g.grade(sT['color'], sT['mean'], target, 1.2, sat=0.9), pick)
            rough = g.lerp(g.rough_from(sS, 0.5, 0.35), g.rough_from(sT, 0.5, 0.35), pick)
            pert = g.vmix(sS['pert'], sT['pert'], pick)
        else:
            n, _ = g.noise(g.vec(g.mul(al, 3.0), g.mul(ac, 60.0), 0.0), 1.0, detail=6.0, rough=0.6)
            col = g.vscale(target, g.remap(n, 0.2, 0.8, 0.82, 1.15))
            rough, pert = 0.5, None
        col = g.vscale(col, tone)
        # slight per-board warmth and a soft weathering cloud so the stain is not paint-flat
        q = g.fract(g.mul(rnd, 3.71))
        col = g.cmix(col, g.vm('MULTIPLY', col, (1.06, 0.98, 0.9)), g.mul(q, 0.5))
        cl, _ = g.noise(fr['P'], 0.9, detail=3.0)
        col = g.vscale(col, g.remap(cl, 0.3, 0.7, 0.95, 1.04))
        nrm = g.normal(pert, 0.45)
        return g.finish(g.bsdf(col, rough, 0.0, nrm, **{'Coat Weight': 0.1, 'Coat Roughness': 0.3}))
    except Exception as e:
        print('[exterior] cedar material fallback:', repr(e))
        if g is not None and g.m is not None:
            bpy.data.materials.remove(g.m)
        return flat_mat('Z_garage_cedar_flat', CEDAR, 0.5)


def _glass(name, tint, f0=0.04):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    from .. import materials
    return materials.thin_glass(name, tint=tint, f0=f0)


def door(ctx):
    frame = _Wood(11)
    panel = _Wood(23)
    grille = _Wood(37)
    mould = _Wood(41)
    glass = MB()
    hw = MB()
    seal = MB()
    pulls = MB()
    zp0, zp1 = DZ0 + PANEL_REC, DZ1 - PANEL_REC          # panel faces (inside / street)
    nlx, nly = LITES
    for s in range(NSEC):
        y0, y1 = _sec_y(s)
        rb, rt = _rails(s)
        py0, py1 = y0 + rb, y1 - rt
        # frame: full-width rails (horizontal grain) and stiles between them (vertical grain)
        frame.piece(DX0, DX1, y0, py0, DZ0, DZ1, True, FRAME_TONE * frame.rng.uniform(0.95, 1.05))
        frame.piece(DX0, DX1, py1, y1, DZ0, DZ1, True, FRAME_TONE * frame.rng.uniform(0.95, 1.05))
        stiles = [(DX0, DX0 + STILE_O), (DX1 - STILE_O, DX1)]
        for c in range(1, NCOL):
            xs = _col_x(c)[0] - STILE_I
            stiles.append((xs, xs + STILE_I))
        for xs0, xs1 in stiles:
            frame.piece(xs0, xs1, py0, py1, DZ0, DZ1, False, FRAME_TONE * frame.rng.uniform(0.95, 1.05))
        for c in range(NCOL):
            px0, px1 = _col_x(c)
            if s < NSEC - 1:
                # recessed panel: flat back board (garage side) + vertical V-groove planks (street side),
                # both let 0.03 ft into the frame's grooves
                panel.piece(px0 - 0.03, px1 + 0.03, py0 - 0.03, py1 + 0.03, zp0, ZC, False, 1.0)
                n = max(1, round(PW / PLANK))
                w = PW / n
                for k in range(n):
                    xa = px0 + k * w - (0.03 if k == 0 else 0.0)
                    xb = px0 + (k + 1) * w + (0.03 if k == n - 1 else 0.0)
                    panel.piece(xa, xb, py0 - 0.03, py1 + 0.03, ZC, zp1, False, panel.rng.uniform(0.93, 1.05))
                # street side: a small rounded panel moulding inside the frame (butt-jointed, no overlaps)
                t = FRAME_TONE * 1.04
                mould.piece(px0, px1, py0, py0 + MOULD[0], zp1, zp1 + MOULD[1], True, t)
                mould.piece(px0, px1, py1 - MOULD[0], py1, zp1, zp1 + MOULD[1], True, t)
                mould.piece(px0, px0 + MOULD[0], py0 + MOULD[0], py1 - MOULD[0], zp1, zp1 + MOULD[1], False, t)
                mould.piece(px1 - MOULD[0], px1, py0 + MOULD[0], py1 - MOULD[0], zp1, zp1 + MOULD[1], False, t)
            else:
                # top section: 3 x 2 lites with 7/8" grilles; one pane per lite, set into grille and frame
                lw = (PW - (nlx - 1) * MUNTIN) / nlx
                lh = (py1 - py0 - (nly - 1) * MUNTIN) / nly
                gz0, gz1 = ZC - 0.06, ZC + 0.06
                for i in range(1, nlx):
                    xm = px0 + i * lw + (i - 1) * MUNTIN
                    grille.piece(xm, xm + MUNTIN, py0 - 0.02, py1 + 0.02, gz0, gz1, False, FRAME_TONE)
                for i in range(nlx):
                    lx0 = px0 + i * (lw + MUNTIN)
                    for j in range(1, nly):
                        ym = py0 + j * lh + (j - 1) * MUNTIN
                        grille.piece(lx0, lx0 + lw, ym, ym + MUNTIN, gz0, gz1, True, FRAME_TONE)
                    for j in range(nly):
                        ly0 = py0 + j * (lh + MUNTIN)
                        glass.box(lx0 - 0.015, lx0 + lw + 0.015, ly0 - 0.015, ly0 + lh + 0.015, ZC - 0.006, ZC + 0.006)
        # section joint: recessed rubber tongue in the gap (no daylight through the joint)
        if s < NSEC - 1:
            seal.box(DX0 + 0.02, DX1 - 0.02, y1 - 0.01, y1 + GAP + 0.01, DZ0 + 0.04, DZ1 - 0.04)
        # inside hardware: hinges on the intermediate stiles across each joint; at the ends the end
        # hinge doubles as the roller bracket
        if s > 0:
            for xs0, xs1 in stiles[2:]:
                xh = (xs0 + xs1) / 2
                hw.box(xh - 0.13, xh + 0.13, y0 - 0.2, y0 + 0.2, DZ0 - 0.035, DZ0)
        for xe, sgn in ((DX0, -1), (DX1, 1)):
            yr = y0 + (0.25 if s == 0 else 0.0)
            hw.box(xe - sgn * 0.32, xe + sgn * 0.02, yr - 0.14, yr + 0.14, DZ0 - 0.05, DZ0)
    # bottom astragal seal
    seal.box(DX0 + 0.02, DX1 - 0.02, 0.0, DY0 + 0.02, DZ0 + 0.02, DZ1 - 0.02)
    # inside lift handle on the bottom section's centre stile
    hw.box(XC - 0.14, XC + 0.14, 1.0, 1.06, DZ0 - 0.11, DZ0 - 0.05)
    hw.box(XC - 0.14, XC - 0.08, 1.0, 1.06, DZ0 - 0.05, DZ0)
    hw.box(XC + 0.08, XC + 0.14, 1.0, 1.06, DZ0 - 0.05, DZ0)
    # street side: a pair of black wrought bar pulls on the panels either side of the centre stile
    # (second section), low enough in profile to pass behind the header
    y0, y1 = _sec_y(1)
    yc = (y0 + RAIL_J + y1 - RAIL_J) / 2 + 0.12
    for sgn in (-1, 1):
        xp = XC + sgn * (STILE_I / 2 + 0.36)
        for yy in (yc - 0.3, yc + 0.3):
            pulls.box(xp - 0.045, xp + 0.045, yy - 0.065, yy + 0.065, zp1, zp1 + 0.016)      # rosette plates
            pulls.box(xp - 0.022, xp + 0.022, yy - 0.025, yy + 0.025, zp1 + 0.016, zp1 + 0.075)  # posts
        pulls.box(xp - 0.024, xp + 0.024, yc - 0.36, yc + 0.36, zp1 + 0.075, zp1 + 0.105)       # grip
    frame.emit(ctx, 'ext garage door frame', cedar_material(ctx), bevel=0.014, segments=2)
    panel.emit(ctx, 'ext garage door panels', cedar_material(ctx), bevel=0.011, segments=1)
    grille.emit(ctx, 'ext garage door grilles', cedar_material(ctx), bevel=0.008, segments=1)
    mould.emit(ctx, 'ext garage door mouldings', cedar_material(ctx), bevel=0.012, segments=2)
    glass.obj(ctx, 'ext garage door glass', _glass('Z_garage_door_glass', (0.86, 0.89, 0.88), f0=0.09), SUB)
    hw.obj(ctx, 'ext garage door hinges', 'black_metal', SUB, bevel=0.008, segments=1)
    seal.obj(ctx, 'ext garage door seal', flat_mat('Z_exterior_rubber', '#121212', 0.8), SUB)
    pulls.obj(ctx, 'ext garage door pulls', 'black_metal', SUB, bevel=0.008, segments=2)


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
        side = -1 if xc < XC else 1
        trk.box(xc + side * 0.1, xc + side * 0.16, 0.55, y_vt, zt, WALL_IN - 0.002)
        # rear hanger strap to the ceiling + diagonal brace
        trk.box(xc - 0.03, xc + 0.03, y_h + 0.06, 7.995, z_back + 0.2, z_back + 0.35)
        # rollers (stem into track) at each section
        for s in range(NSEC):
            yr = _sec_y(s)[0] + (0.25 if s == 0 else 0.0)
            # (the stem reaches back into the end hinge / roller bracket on the door's inside face)
            trk.box(min(xc, (DX0 if side < 0 else DX1)), max(xc, (DX0 if side < 0 else DX1)), yr - 0.03, yr + 0.03,
                    zt - 0.03, DZ0 - 0.045)
    trk.obj(ctx, 'ext garage door tracks', flat_mat('Z_exterior_galv', '#9a9c9c', 0.45, 0.9), SUB, bevel=0.006,
            segments=1)
    # torsion spring assembly above the door (shaft, drums, springs, bearing plates)
    ys, zs = 7.62, WALL_IN - 0.33
    parts = []
    shaft = ctx.cylinder('ext garage torsion shaft', (XC, ys, zs), 0.045, DX1 - DX0 + 0.7, 'black_metal',
                         'ext_garage_door', verts=16, axis='X')
    parts.append(shaft)
    for xd in (DX0 - 0.13, DX1 + 0.13):
        parts.append(ctx.cylinder('ext garage cable drum', (xd, ys, zs), 0.2, 0.28, 'black_metal', 'ext_garage_door',
                                  verts=24, axis='X'))
    for xs in (XC - 1.45, XC + 1.45):
        parts.append(ctx.cylinder('ext garage torsion spring', (xs, ys, zs), 0.115, 2.6,
                                  flat_mat('Z_exterior_spring', '#2c2c2c', 0.35, 0.8), 'ext_garage_door', verts=20,
                                  axis='X'))
    bp = MB()
    for xb in (DX0 - 0.13, XC, DX1 + 0.13):
        bp.box(xb - 0.06, xb + 0.06, 7.45, ys + 0.25, zs - 0.08, WALL_IN - 0.002)
    bp.obj(ctx, 'ext garage spring plates', 'black_metal', SUB)
    # opener: T-rail under the torsion tube, header bracket on the wall above the door, motor head
    op = MB()
    xr = XC
    zr0, zr1 = WALL_IN - 0.002, DZ0 - 11.0
    op.box(xr - 0.06, xr + 0.06, 7.28, 7.40, zr1, zr0 - 0.05)
    op.box(xr - 0.15, xr + 0.15, 7.18, 7.48, zr0 - 0.05, zr0)              # header bracket
    op.box(xr - 0.07, xr + 0.07, 7.17, 7.28, DZ0 - 1.4, DZ0 - 1.1)       # trolley
    # bent door arm: two straight flat bars (oriented in the y/z plane, overlapping at the bend)
    arm_pts = [(DZ0 - 1.25, 7.2), (DZ0 - 0.55, 7.05), (DZ0 - 0.06, 6.88)]
    for (za, ya), (zb, yb) in zip(arm_pts[:-1], arm_pts[1:]):
        L_ = math.hypot(zb - za, yb - ya)
        uz, uy = (zb - za) / L_, (yb - ya) / L_          # along the bar
        nz, ny = -uy, uz                                  # across the bar (in the y/z plane)
        hl, hd = L_ / 2 + 0.03, 0.035
        cz, cy = (za + zb) / 2, (ya + yb) / 2
        pts = [(cz + uz * u + nz * v, cy + uy * u + ny * v) for u, v in ((-hl, -hd), (hl, -hd), (hl, hd), (-hl, hd))]
        b = len(op.v)
        for xx in (xr - 0.03, xr + 0.03):
            for zz, yy in pts:
                op.vert(xx, yy, zz)
        for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            op.face([b + i for i in f])
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


def _sphere(ctx, name, center, radius, squash=1.0, mat=None, coll_name='ext_lights', segs=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=max(6, segs // 2), radius=radius * FT)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location = ft2bl(*center)
    ob.scale = (1.0, 1.0, squash)
    if mat is not None:
        me.materials.append(ctx.mat(mat) if isinstance(mat, str) else mat)
    ctx.coll(coll_name).objects.link(ob)
    return ob


def lantern(ctx, name, x, yc, z, nx, nz, watts=30.0):
    """Black square coach lantern (owner's garage reference) on a wall with outward normal (nx, nz):
    wall plate, square arm into a back strap, bottom pan, four corner posts with clear panes, a top
    band, pyramid roof with cap and finial, and a candelabra bulb on a cream candle sleeve (a small
    point lamp inside). yc = centre height of the glass cage (feet); ~14" tall x 7" wide overall."""
    rot = math.atan2(nx, nz)                      # local +z (SCENE) -> outward normal
    tx, tz = nz, -nx                              # along the wall (local +x)
    OFF, A = 0.46, 0.25                           # cage centre out from the wall, cage half-width
    P = 0.045                                     # corner post section

    def at(du, dv):
        return x + tx * du + nx * dv, z + tz * du + nz * dv

    mb = MB()
    cx, cz = at(0.0, OFF)
    mb.box_c(cx, yc - 0.40, cz, 0.58, 0.08, 0.58, rot)                          # bottom pan
    mb.box_c(cx, yc + 0.39, cz, 0.58, 0.06, 0.58, rot)                          # top band
    for du in (-1, 1):
        for dv in (-1, 1):
            px, pz = at(du * (A - P / 2), OFF + dv * (A - P / 2))
            mb.box_c(px, yc, pz, P, 0.72, P, rot)                               # corner posts
    # pyramid roof (square, so no rotation needed) + cap
    b = len(mb.v)
    for (h, yy) in ((0.32, yc + 0.42), (0.075, yc + 0.62)):
        for (du, dv) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            mb.vert(cx + du * h, yy, cz + dv * h)
    mb.face([b + 3, b + 2, b + 1, b + 0])
    mb.face([b + 4, b + 5, b + 6, b + 7])
    for i in range(4):
        j = (i + 1) % 4
        mb.face([b + i, b + j, b + 4 + j, b + 4 + i])
    mb.box_c(cx, yc + 0.64, cz, 0.17, 0.04, 0.17, rot)                          # cap
    sx, sz = at(0.0, OFF - A - 0.0005)
    mb.box_c(sx, yc, sz, 0.07, 0.72, 0.03, rot)                                 # back strap
    ax, az = at(0.0, (0.04 + OFF - A - 0.015) / 2)
    mb.box_c(ax, yc + 0.14, az, 0.06, 0.06, OFF - A - 0.015 - 0.04 + 0.02, rot)  # arm
    wx, wz = at(0.0, 0.02)
    mb.box_c(wx, yc + 0.06, wz, 0.34, 0.78, 0.04, rot)                          # wall plate
    mb.obj(ctx, f'ext lantern {name} body', 'black_metal', 'lights', bevel=0.008, segments=2)
    ctx.cylinder(f'ext lantern {name} finial', (cx, yc + 0.7, cz), 0.026, 0.08, 'black_metal', 'ext_lights', verts=12)
    ctx.cylinder(f'ext lantern {name} drop', (cx, yc - 0.48, cz), 0.032, 0.08, 'black_metal', 'ext_lights', verts=12)
    # clear panes between the posts, let into the pan and the band
    gl = MB()
    w = 2 * (A - P) + 0.02
    for dv in (-1, 1):
        gx, gz = at(0.0, OFF + dv * (A - P / 2))
        gl.box_c(gx, yc, gz, w, 0.73, 0.01, rot)
        gx, gz = at(dv * (A - P / 2), OFF)
        gl.box_c(gx, yc, gz, 0.01, 0.73, w, rot)
    gl.obj(ctx, f'ext lantern {name} glass', _glass('Z_garage_lantern_glass', (0.93, 0.93, 0.9)), 'lights')
    # candelabra bulb on a candle sleeve
    ctx.cylinder(f'ext lantern {name} sleeve', (cx, yc - 0.25, cz), 0.034, 0.22,
                 flat_mat('Z_garage_lantern_sleeve', '#ece3cf', 0.45), 'ext_lights', verts=16)
    bulb = _sphere(ctx, f'ext lantern {name} bulb', (cx, yc - 0.075, cz), 0.045, squash=1.6,
                   mat=emit_mat('Z_garage_lantern_bulb', lighting.kelvin_rgb(2400), 30.0))
    bulb.visible_shadow = False                   # the lamp sits inside it
    ld = bpy.data.lights.new(f'ext lantern {name}', 'POINT')
    ld.energy = watts
    ld.color = lighting.kelvin_rgb(2400)
    ld.shadow_soft_size = 0.035 * FT
    lo = bpy.data.objects.new(ld.name, ld)
    lo.location = ft2bl(cx, yc - 0.07, cz)
    coll(ctx, 'lights').objects.link(lo)
    return lo


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
    mailbox(ctx, L.WALKWAY[0] - 0.35, L.SIDEWALK[0] - 1.1)
    door(ctx)
    hardware(ctx)
    gf = L.GARAGE_FRONT
    # black coach lanterns flanking the door (owner's reference). The porch's east pier stands on the
    # garage face just west of the door: the west lantern goes on the pier's side facing the driveway
    # (under the canopy edge, clear of the soffit), the house number on the pier's street face
    px0, px1, pz0, pz1 = L.PORCH_POSTS[1]
    lantern(ctx, 'garage W', px1, 5.95, (max(pz0, gf) + pz1) / 2, 1.0, 0.0)
    lantern(ctx, 'garage E', (OX1 + L.HX1) / 2, 5.95, gf, 0.0, 1.0)
    # on the foyer front wall between the porch-side wall's stucco and the 3'-0" door (centred, relayout)
    door_w = (L.PORCH[0] + L.PORCH[1]) / 2 - 1.5
    sconce(ctx, 'entry', (L.PORCH[0] + 0.09 + door_w) / 2, 5.95, L.PORCH[2] + 0.112, 0.0, 1.0)
    # rear: a pair flanking the living-room garden door (x 24.45..26.93), as on the 1077 patio
    sconce(ctx, 'rear W', 23.85, 6.3, L.HZ0, 0.0, -1.0)
    sconce(ctx, 'rear E', 27.39, 6.3, L.HZ0, 0.0, -1.0)
    house_number(ctx, '1095', (px0 + px1) / 2, 5.25, pz1)
    return {'door_sections': NSEC, 'lites': NCOL * LITES[0] * LITES[1], 'lanterns': 2}
