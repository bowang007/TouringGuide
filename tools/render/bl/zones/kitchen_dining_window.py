"""Sink window W08 dressed as in the owner's "kitchen window" references: a three-sash GRID window
(6 x 4 lites), a painted casing with back band and a deep stool, two brass gooseneck sconces with
brass dome shades on the brick piers, and cafe curtains (semi-sheer striped linen on brass clip
rings and a brass rod) over the two outer sashes, leaving the centre sash clear over the faucet.

Seventh round (2026-11-21), the owner: "Set all windows to white color, and it should have grid line
for these windows". The window was a black steel grid window in a cream casing. Now the frame and the
grid are white: bl/revisions.white_windows recolours the shell's frame and builds the bars of every
window in the house, this one with the 2 x 4 lites per sash it had (revision_spec.WINDOW_GRID_KEEP),
so this module no longer builds bars. The casing and the stool are the same satin white as the frame
(library `window_white`), so the whole window reads white against the whitewashed brick.

Shell geometry (bl/shell.py _kitchen_window, concept plan): east wall x 40.61-41.06, frame centre
x 40.8367, frame depth 0.22, face width 0.16, mullions at z 25.387 / 27.387 (+-0.06), glass
x 40.8217-40.8517, y 3.31-7.59. Wall face is clad with 0.06 thin brick (kitchen_dining_kitchen).
"""
import math

import bmesh

from . import kitchen_dining_cabs as C
from . import kitchen_dining_mats as KM
from .kitchen_dining_geo import Geo, P

WALL_E = 40.61
SPL = 0.06
Z0, Z1 = 23.387, 29.387
SILL, HEAD = 3.15, 7.75
XC = 40.8367
FW, FD = 0.16, 0.22
GY0, GY1 = SILL + FW, HEAD - FW            # visible glass
GX0, GX1 = XC - 0.015, XC + 0.015
CASE_W = 0.27                               # casing width (3-1/4in)
CASE_T = 0.06
FACE = WALL_E - SPL                         # brick face (casing sits on it)
ROD_Y = 5.30
CURTAIN_X = 40.415                          # mean plane of the cafe curtains
TOP = 3.0
WHITE = 'window_white'                      # casing and stool: the frame's satin white (cream until the sixth round)


def sashes():
    """Visible glass of each sash (z0, z1)."""
    out = []
    edges = [Z0 + FW, Z0 + 2.0 - 0.06, Z0 + 2.0 + 0.06, Z0 + 4.0 - 0.06, Z0 + 4.0 + 0.06, Z1 - FW]
    for k in range(3):
        out.append((edges[2 * k], edges[2 * k + 1]))
    return out


def build(ctx, g: Geo):
    col = g.sub('kd window')
    lights = g.sub('kd_lights')
    brass = KM.brass()
    _casing(g, WHITE, col)
    sc = _sconces(g, brass, col, lights)
    _cafe(g, brass, col)
    return {'grid': 'bl/revisions.white_windows', 'casing': WHITE, 'sconces': sc, 'cafe_panels': 2}


def _casing(g, paint, col):
    """Flat casing with a back band on the brick face, jamb/head liners in the reveal, and a deep
    stool with an apron over the backsplash ledge, all in `paint` (cream until the sixth round, now the frame's white)."""
    F = C.Face('mx', FACE)
    acc = C.Acc()
    st_top = 3.17
    za, zb = Z0 - CASE_W, Z1 + CASE_W
    ytop = 8.0 - 0.006
    acc.box(F, za, Z0, st_top, HEAD, 0.0, CASE_T)                 # north leg
    acc.box(F, Z1, zb, st_top, HEAD, 0.0, CASE_T)                 # south leg
    acc.box(F, za, zb, HEAD, ytop, 0.0, CASE_T)                   # head (to the ceiling)
    bb = 0.07                                                      # back band (outer edge)
    acc.box(F, za - bb, za, st_top, ytop, 0.0, CASE_T + 0.03)
    acc.box(F, zb, zb + bb, st_top, ytop, 0.0, CASE_T + 0.03)
    # liners in the reveal: from the casing face to the window frame
    xi = XC - FD / 2
    acc.wbox(FACE - CASE_T, xi, st_top, HEAD, Z0, Z0 + 0.03)
    acc.wbox(FACE - CASE_T, xi, st_top, HEAD, Z1 - 0.03, Z1)
    acc.wbox(FACE - CASE_T, xi, HEAD - 0.03, HEAD, Z0 + 0.03, Z1 - 0.03)
    acc.done(g, 'kd W08 casing panel', paint, col, bevel=0.006)
    # stool (horns past the casing) and apron down to the worktop
    st = C.Acc()
    xs, h0, h1 = FACE - CASE_T - 0.09, za - bb - 0.06, zb + bb + 0.06
    st.poly_y([(xs, h0), (FACE, h0), (FACE, Z0), (xi - 0.001, Z0), (xi - 0.001, Z1), (FACE, Z1), (FACE, h1), (xs, h1)],
              3.085, st_top)
    st.wbox(FACE, WALL_E, TOP, 3.085, Z0, Z1)
    st.done(g, 'kd W08 sill return', paint, col, bevel=0.008)


def _sconces(g, brass, col, lights):
    """Brass gooseneck sconces with brass dome shades (white inside) on the two brick piers."""
    from ..lighting import emitter
    bulb = emitter('kd_sconce_bulb', 2700, 30.0)
    inner = KM.stoneware('shade_enamel', '#f1ede4', 0.3, 0.2)
    n = 0
    for z in (22.52, 30.02):
        x0 = FACE
        yb = 6.55
        g.cyl_axis('kd sconce backplate', (x0, yb, z), (x0 - 0.035, yb, z), 0.15, brass, 40, col)
        g.cyl_axis('kd sconce knuckle', (x0 - 0.035, yb, z), (x0 - 0.10, yb, z), 0.035, brass, 20, col)
        R = 0.3
        xs = x0 - 0.10
        pts = [(xs, yb, z), (xs - 0.12, yb, z)]
        cx, cy = xs - 0.12, yb - R
        for k in range(1, 13):
            a = math.pi / 2 * k / 12
            pts.append((cx - R * math.sin(a), cy + R * math.cos(a), z))
        g.tube('kd sconce arm', pts, 0.022, brass, col)
        sx, sy = cx - R, cy                           # shade fitter top (arm end)
        g.cyl('kd sconce fitter', sx, sy - 0.07, sy + 0.005, z, 0.045, brass, 24, col)
        # dome shade: brass outside, white enamel inside (two surfaces 3 mm apart)
        prof = [(0.05, 0.0), (0.09, -0.01), (0.16, -0.05), (0.22, -0.11), (0.27, -0.18), (0.30, -0.23), (0.31, -0.255)]
        g.lathe('kd sconce shade', [(r, sy - 0.07 + y) for r, y in prof], sx, z, brass, 48, col, sharp_deg=70)
        g.lathe('kd sconce shade lining', [(max(r - 0.01, 0.0), sy - 0.07 + y - 0.006) for r, y in prof], sx, z, inner, 48, col,
                sharp_deg=70)
        g.lathe('kd sconce bulb', [(0.0, 0.0), (0.035, 0.01), (0.05, 0.05), (0.045, 0.1), (0.02, 0.13), (0.0, 0.135)][::-1],
                sx, z, bulb, 24, col, y_base=sy - 0.07 - 0.20)
        g.point_light('kd sconce light', sx, sy - 0.2, z, 7.0, 2700, 0.06, lights)
        n += 1
    return n


def _cafe(g, brass, col):
    """Brass cafe rod on two brackets across the window, two gathered linen panels on clip rings
    over the outer sashes (bottom hem just above the stool)."""
    sheer = KM.linen_sheer()
    rx = CURTAIN_X - 0.005
    zr0, zr1 = Z0 - CASE_W / 2 - 0.05, Z1 + CASE_W / 2 + 0.05
    g.cyl_axis('kd cafe curtain rod', (rx, ROD_Y, zr0), (rx, ROD_Y, zr1), 0.02, brass, 20, col)
    for z in (Z0 - CASE_W / 2, Z1 + CASE_W / 2):
        g.cyl_axis('kd cafe curtain rod bracket', (FACE - CASE_T, ROD_Y, z), (rx, ROD_Y, z), 0.016, brass, 12, col)
        g.cyl_axis('kd cafe curtain rod bracket rose', (FACE - CASE_T, ROD_Y, z), (FACE - CASE_T - 0.02, ROD_Y, z), 0.045, brass, 24, col)
    for zz in (zr0, zr1):
        g.cyl_axis('kd cafe curtain rod finial', (rx, ROD_Y, zz), (rx, ROD_Y, zz + (0.05 if zz > Z1 else -0.05)),
                   0.032, brass, 20, col)
    top, hem = ROD_Y - 0.085, 3.215
    s = sashes()
    n = 8
    for i, (za, zb) in enumerate(((s[0][0] - 0.12, s[0][1] + 0.06), (s[2][0] - 0.06, s[2][1] + 0.12))):
        clips = [za + 0.05 + (zb - za - 0.1) * k / (n - 1) for k in range(n)]
        _panel(g, f'kd cafe curtain panel {i}', za, zb, top, hem, sheer, col, clips, seed=i)
        for zc in clips:
            g.cyl_axis('kd cafe curtain ring', (rx, ROD_Y, zc - 0.007), (rx, ROD_Y, zc + 0.007), 0.034, brass, 20, col)
            g.cyl_axis('kd cafe curtain clip', (rx, ROD_Y - 0.034, zc), (rx, top - 0.004, zc), 0.006, brass, 8, col)


def _panel(g, name, z0, z1, y0, y1, mat, col, clips, seed=0):
    """Gathered linen panel hung from clip rings: the classic ring-top ripple, the cloth passing
    through the clip plane at each clip and bellying alternately in and out between clips (so every
    clip grips the cloth), each fold with its own depth. Toward the hem the folds soften and drift a
    little, with a finer irregular gather mixed in, and the panel sways slightly."""
    import random
    rnd = random.Random(31 + seed)
    nz, ny = 160, 26
    span = z1 - z0
    # fold anchors: the panel edges and the clips; each interval between anchors is one fold
    anchors = [z0] + list(clips) + [z1]
    amps = [rnd.uniform(0.75, 1.0) * (1 if k % 2 else -1) for k in range(len(anchors) - 1)]
    drift = [rnd.uniform(-0.12, 0.12) for _ in amps]
    fine = [(rnd.uniform(0.06, 0.1), rnd.uniform(0, 2 * math.pi)) for _ in range(3)]

    def ripple(zz, t):
        for k in range(len(anchors) - 1):
            a, b = anchors[k], anchors[k + 1]
            if zz <= b or k == len(anchors) - 2:
                # the fold's crest slides a little along z toward the hem (cloth relaxes unevenly)
                u = (zz - a) / max(b - a, 1e-6)
                u = min(max(u + drift[k] * t * math.sin(math.pi * u), 0.0), 1.0)
                return amps[k] * math.sin(math.pi * u)
        return 0.0
    bm = bmesh.new()
    grid = []
    for j in range(ny + 1):
        t = j / ny
        y = y0 + (y1 - y0) * t
        amp = 0.052 - 0.014 * t                    # ~5/8in folds at the clips, softer at the hem
        row = []
        for i in range(nz + 1):
            s = i / nz
            zz = z0 + span * s
            edge = min(s, 1 - s) * span
            fade = min(1.0, 0.45 + edge / 0.2)
            irr = sum(0.004 * t * math.sin(2 * math.pi * zz / p + ph) for p, ph in fine)
            x = CURTAIN_X + amp * fade * ripple(zz, t) + irr + 0.004 * math.sin(2.3 * t + seed) * t
            row.append(bm.verts.new(P(x, y, zz)))
        grid.append(row)
    for j in range(ny):
        for i in range(nz):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    ob = g.from_bmesh(name, bm, mat, col, smooth=True)
    m = ob.modifiers.new('Solidify', 'SOLIDIFY')
    m.thickness = 0.004 * 0.3048
    m.offset = 0.0
    return ob
