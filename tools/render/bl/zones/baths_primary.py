"""Primary ensuite (tour stop A0) of zone `baths`; see baths.py for the shared helpers.

Sixth round (2026-11-20). Two things changed at once:

LAYOUT = the architect's sheet SKA002 (the owner: "follow the sheet"): door D08 at the east end of the north
wall, the shower (5'-0" x 3'-0") in the north-west corner, the toilet in the south-west corner facing north,
the double vanity (6'-6" x 1'-9") along the south wall, window W13 on the west wall with its mullion on the
shower's south glass line, skylight W20 over the shower. All numbers are in bl/revision_spec.py (BATH_*,
PRIMARY_BATH_*). Until the fifth round the room was mirrored north-south.

STYLE = styles/primary bathroom wall style.jpg (rustic, warm, low saturation), the stone where the owner put it:
  * south (vanity) wall - stacked natural stone with true relief, full width and height: the feature wall,
    the first thing seen from the door. On it: the floating solid-oak slab with two carved troughs (the owner's
    sink image, kept), two oak-framed mirrors, a rough dark timber beam across the wall above them with two
    enamel-shade wall lamps (clear bulbs), deck taps in brushed nickel; the toilet stands in front of its west end.
  * shower - plain honed cream stone-look tile (24x48in, quiet joints) on its two solid walls, cream mosaic floor
    with a linear drain behind a flush cream-stone threshold (curbless), frameless glass on the east side (door,
    hinged on the north wall, and a short fixed return) and the south side (fixed, into a channel on the window
    mullion), an exposed brushed-nickel set with rain head and hand shower at the west end, a tiled niche.
  * other walls (east, north beside the door, west outside the shower) - muted grey-green tongue-and-groove
    wainscot to 3'-8" with a plain cap rail, warm cream plaster above; cream plaster ceiling with one timber beam.
  * floor - quiet warm-grey honed stone, 24x24in, no pattern.
  * on the west wall's plaster beside the stone: a reclaimed-timber shelf on black iron brackets with stoneware
    and glass bottles, a framed botanical print and a trailing succulent; a striped bath towel on a nickel bar
    (east wall), a barrel cactus in a galvanised bucket and striped hand towels on the slab, a seagrass basket of
    rolled towels under it, a fringed woven mat in front.

BUILT AFTER THE WARP, IN PLAN FEET. The other zone modules are written on the concept plan and carried onto the
architect's plan by bl/warp.py. This room has to sit on the sheet's numbers, to the window mullion and the
glass line, and the warp moves loose fixtures in clusters; so the room is fitted out by build_room(), which
bl/revisions.primary_bath_fit_out calls after the warp and after the revisions that prepare the architecture:
bath_door (the opening, the niche recess in the north wall, the leaf), bath_window (W13's opening, frame and
glass) and primary_bath_skylight (W20). build_primary(), called with the other baths before the warp, only
makes sure the collection exists. Everything goes into collection zone_baths_primary as before.

Names matter to bake_web.py (README, "Web model contract"): wall finishes carry tg_class = 'wall'.
"""
import math
import re

import bpy

from .. import lighting
from .. import revision_spec as S
from . import baths_kit as K
from . import baths_primary_kit as Q
from . import baths_primary_mats as M
from .baths import CAN_K, T, ZONE

C = f'{ZONE}_primary'
X0, X1, Z0, Z1 = S.PRIMARY_BATH_CLEAR          # wall faces (structure)
FL = 0.028                                     # top of the shell's floor slab
CEIL = 7.985                                   # underside of the cream plaster on the ceiling (shell ceiling: 8.0)
TP = 0.03                                      # cream plaster skin over the shell wall
WAIN, CAP1, CAPD = 3.667, 3.767, 0.115         # panelling top (3'-8"), cap top, cap depth from the wall
XW, XE, ZN = X0 + T, X1 - T, Z0 + T            # faces of the west / east / north wall finish (tile, wainscot)
ZSP = Z1 - 0.06                                # the stone wall's mesh plane (mortar bed), in front of the shell skirting
GX, GZ = S.BATH_SHOWER[1], S.BATH_SHOWER[3]    # centre lines of the shower's east and south glass
TILE_E = GX + 0.075                            # the shower tile runs this far east on the north wall (the hinge side)
WZ0, WZ1 = S.BATH_WIN_Z                        # window W13
SILL = S.TALL_SILL
D0, D1 = S.BATH_DOOR_X
DL0, DL1 = D0 - S.BATH_DOOR_LINER, D1 + S.BATH_DOOR_LINER      # outer edges of the door's jamb liners
DHEAD = S.BATH_DOOR_HEAD + 0.06                # top of the head trim
THR = FL + 0.03                                # top of the shower's stone threshold
GY0, GY1 = THR + 0.02, 6.6                     # shower glass: bottom, top
BEAM_Y = (6.72, 7.32)                          # the wall beam
BEAM_D = 0.52                                  # ... and its depth from the stone's mesh plane


def _wall(obs):
    """Mark wall-finish pieces for the web bake (class 'wall' whatever their size or name)."""
    for ob in obs if isinstance(obs, (list, tuple)) else [obs]:
        ob['tg_class'] = 'wall'
    return obs


def _skin(*a, **kw):
    return _wall(K.skin(*a, **kw))


def _box(*a, **kw):
    return _wall(K.box(*a, **kw))


# ------------------------------------------------------------------------------------ floor
def _floor(ctx):
    """The shell's floor slab gets the room's stone; the shower floor and its flush threshold lie on it."""
    stone = M.floor_stone((X0 + X1) / 2, (Z0 + Z1) / 2)
    n = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and re.search(r'^\d+ Primary ensuite porcelain floor$', ob.name):
            if ob.data.users > 1:
                ob.data = ob.data.copy()
            if len(ob.data.materials):
                for i in range(len(ob.data.materials)):
                    ob.data.materials[i] = stone
            else:
                ob.data.materials.append(stone)
            n += 1
    e = 0.06                                   # half width of the threshold strips under the glass
    K.box(ctx, 'A0 shower floor', X0, GX - e, FL, FL + 0.012, Z0, GZ - e, M.shower_mosaic(), C)
    K.box(ctx, 'A0 shower threshold E', GX - e, GX + e, FL, THR, ZN, GZ - e, M.sill(), C, bevel=0.006)
    K.box(ctx, 'A0 shower threshold S', XW, GX + e, FL, THR, GZ - e, GZ + e, M.sill(), C, bevel=0.006)
    Q.linear_drain(ctx, C, 'A0 shower drain', X0 + 0.5, GX - 0.55, ZN + 0.17, FL + 0.012, axis='x')
    return n


# ------------------------------------------------------------------------------------ walls
def _walls(ctx):
    nx0, nx1, ny0, ny1, dep = S.BATH_NICHE
    tile = M.shower_tile(a0_ft=(nx0 + nx1) / 2, floor_ft=FL)     # a vertical joint on the niche's centre line
    vg, cap, pl = M.vgroove(), M.sage_paint(), M.plaster()
    door = [(DL0, DL1, -1.0, DHEAD)]
    # --- shower: cream tile, full height, on the north wall (with the niche) and the west wall (with W13's north lite)
    _skin(ctx, 'A0 tile shower north', 'z', Z0, ZN, X0, TILE_E, FL, CEIL, tile, C, holes=[(nx0, nx1, ny0, ny1)])
    _skin(ctx, 'A0 tile shower west', 'x', X0, XW, ZN, GZ, FL, CEIL, tile, C, holes=[(WZ0, GZ + 1.0, SILL, 99.0)])
    _box(ctx, 'A0 tile shower edge trim', TILE_E, TILE_E + 0.012, FL, CEIL, Z0, ZN + 0.004, M.nickel(), C)
    # niche lining: tiled back, sides and head, a stone sill a little proud of the wall
    zb = Z0 - dep                              # the recess's back (shell)
    lt = 0.02
    _box(ctx, 'A0 tile niche back', nx0, nx1, ny0, ny1, zb, zb + lt, tile, C)
    _box(ctx, 'A0 tile niche side W', nx0, nx0 + lt, ny0 + 0.035, ny1 - lt, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche side E', nx1 - lt, nx1, ny0 + 0.035, ny1 - lt, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche head', nx0, nx1, ny1 - lt, ny1, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche sill', nx0, nx1, ny0, ny0 + 0.035, zb + lt, ZN + 0.012, M.sill(), C, bevel=0.004)
    # --- north wall east of the shower (the door's wall): wainscot, cap, plaster; over the door plaster only
    _skin(ctx, 'A0 tile north wainscot', 'z', Z0, ZN, TILE_E, X1, FL, WAIN, vg, C, holes=door)
    _skin(ctx, 'A0 tile north cap', 'z', Z0, Z0 + CAPD, TILE_E, X1 - CAPD, WAIN, CAP1, cap, C, holes=door)
    _skin(ctx, 'A0 tile north upper', 'z', Z0, Z0 + TP, TILE_E, X1, CAP1, CEIL, pl, C, holes=door)
    # --- east wall, full length (it runs into the stone at its south end)
    _skin(ctx, 'A0 tile east wainscot', 'x', XE, X1, ZN, Z1, FL, WAIN, vg, C)
    _skin(ctx, 'A0 tile east cap', 'x', X1 - CAPD, X1, Z0, Z1, WAIN, CAP1, cap, C)
    _skin(ctx, 'A0 tile east upper', 'x', X1 - TP, X1, Z0 + TP, Z1, CAP1, CEIL, pl, C)
    # --- west wall south of the shower's glass line: wainscot under W13's south lite and beside it, plaster above
    _skin(ctx, 'A0 tile west wainscot', 'x', X0, XW, GZ, Z1, FL, WAIN, vg, C, holes=[(GZ - 1.0, WZ1, SILL, 99.0)])
    _skin(ctx, 'A0 tile west cap', 'x', X0, X0 + CAPD, WZ1, Z1, WAIN, CAP1, cap, C)
    _skin(ctx, 'A0 tile west upper', 'x', X0, X0 + TP, WZ1, Z1, CAP1, CEIL, pl, C)
    # --- south wall: stacked stone, full width and height: a dense grid (~1cm) the material displaces in world space
    x0, x1 = X0 + 0.004, X1 - 0.004
    nx = int(round((x1 - x0) / 0.034))
    ny = int(round((CEIL - FL) / 0.034))
    _wall(Q.grid_wall_z(ctx, 'A0 tile south stone', ZSP, x0, x1, FL, CEIL, nx, ny, M.stone(), C, facing=-1))
    # --- ceiling: cream plaster under the shell's white ceiling, around the skylight's shaft
    sx0, sx1, sz0, sz1 = S.PRIMARY_BATH_SKY
    for tag, a, b, c0, c1 in (('W', X0, sx0, Z0, Z1), ('E', sx1, X1, Z0, Z1), ('N', sx0, sx1, Z0, sz0), ('S', sx0, sx1, sz1, Z1)):
        K.box(ctx, f'A0 ceiling plaster {tag}', a, b, CEIL, 8.0, c0, c1, pl, C)


def _window(ctx):
    """W13's finish: the shower lite (north of the mullion) gets a tiled reveal and a stone sill, the dry lite an oak
    stool, a plaster reveal and a linen roman shade; a post on the mullion carries the shower's south glass."""
    fx = 0.11                                  # room face of the window frame (bl/revisions.bath_window)
    m0, m1 = GZ - 0.05, GZ + 0.05              # the mullion
    post = _box(ctx, 'A0 window mullion post', fx, XW + 0.015, SILL, 8.0, m0, m1, 'black_aluminum', C)
    _box(ctx, 'A0 tile window return N', fx, XW, SILL + 0.035, 8.0, WZ0, WZ0 + 0.03, M.shower_tile(), C)
    _box(ctx, 'A0 window sill stone', fx, XW + 0.02, SILL, SILL + 0.035, WZ0, m0, M.sill(), C, bevel=0.006)
    _box(ctx, 'A0 window return S', fx, XW, SILL + 0.04, 8.0, WZ1 - 0.03, WZ1, M.plaster(), C)
    oak = M.oak()
    _box(ctx, 'A0 window stool', fx, XW, SILL, SILL + 0.04, m1, WZ1, oak, C)
    _box(ctx, 'A0 window stool lip', XW, XW + 0.07, SILL - 0.035, SILL + 0.04, m1, WZ1 + 0.07, oak, C, bevel=0.008)
    # roman shade over the dry lite, inside-mounted under the head, drawn up to about 6'-4"
    a, b = m1 + 0.02, WZ1 - 0.05
    K.box(ctx, 'A0 roman shade headrail', 0.13, 0.27, 7.74, 7.88, a, b, 'paint_trim', C)
    K.box(ctx, 'A0 roman shade fabric', 0.215, 0.235, 6.62, 7.74, a + 0.01, b - 0.01, 'fabric_linen_white', C)
    for i, yb in enumerate((6.30, 6.47)):
        fold = K.box(ctx, f'A0 roman shade fold {i}', 0.20, 0.30 - 0.025 * i, yb, yb + 0.19, a + 0.01, b - 0.01,
                     'fabric_linen_white', C)
        ctx.add_bevel(fold, 0.06, 4)
    return post


# ------------------------------------------------------------------------------------ shower
def _shower(ctx):
    ni = M.nickel()
    t = 0.0155                                 # half the glass thickness
    # south side: one fixed panel from the channel on the window mullion to the corner
    K.glass_panel(ctx, C, 'A0 shower glass south', (XW + 0.03, GZ), (GX - t - 0.004, GZ), GY0, GY1)
    Q.u_channel(ctx, C, 'A0 shower channel south', (XW + 0.02, GZ), (GX - 0.04, GZ), THR)
    K.box(ctx, 'A0 shower channel wall', XW, XW + 0.065, THR, GY1, GZ - 0.0375, GZ + 0.0375, ni, C, bevel=0.006)
    # east side: the door, hinged on the north wall, and a short fixed return that closes the corner
    zr = 23.62
    K.glass_panel(ctx, C, 'A0 shower glass return', (GX, zr), (GX, GZ + t), GY0, GY1)
    Q.u_channel(ctx, C, 'A0 shower channel return', (GX, zr - 0.01), (GX, GZ + 0.0375), THR)
    K.glass_panel(ctx, C, 'A0 shower glass door', (GX, ZN + 0.05), (GX, zr - 0.02), GY0 + 0.02, GY1)
    for i, yy in enumerate((GY0 + 0.95, GY1 - 0.95)):
        Q.clamp(ctx, C, f'A0 shower hinge {i}', GX, yy, ZN + 0.11, 'z', size=(0.24, 0.26, 0.09))
        K.box(ctx, f'A0 shower hinge {i} plate', GX - 0.1, GX + 0.1, yy - 0.16, yy + 0.16, ZN, ZN + 0.018, ni, C, bevel=0.006)
        Q.clamp(ctx, C, f'A0 shower corner clamp {i}', GX - 0.04, yy, GZ - 0.04, 'x', size=(0.085, 0.12, 0.085))
    # pull: a bar on each face of the door, on two posts through the glass
    zp = zr - 0.26
    for dx in (-0.1, 0.1):
        ctx.cylinder('A0 shower door pull', (GX + dx, 3.7, zp), 0.026, 1.1, ni, C, verts=24)
    for yy in (3.3, 4.1):
        ctx.cylinder('A0 shower door pull post', (GX, yy, zp), 0.016, 0.2, ni, C, verts=16, axis='X')
    # exposed nickel set on the north wall at the west end: the rain head centred in the shower's depth, west of
    # the skylight; the hand shower on its riser
    fn = K.Frame(0.0, ZN, 0.0, 1.0)            # u = z - ZN, v = x
    Q.exposed_shower(ctx, fn, C, 'A0 shower set', 1.30, y_valve=3.6, y_top=6.72, reach=(GZ - ZN) / 2 - 0.17,
                     head_r=0.36, hand_y=4.55)
    # the niche's bottles (its sill top is the shelf)
    nx0, nx1, ny0, ny1, dep = S.BATH_NICHE
    ys, zc = ny0 + 0.035, Z0 - dep / 2 + 0.035
    Q.bottle(ctx, C, 'A0 niche bottle 0', nx0 + 0.3, ys, zc, 0.085, 0.56, M.flat('stoneware', '#d9d2c2', 0.45), neck=0.36,
             stopper=ni)
    Q.bottle(ctx, C, 'A0 niche bottle 1', nx0 + 0.56, ys, zc + 0.01, 0.075, 0.48, M.flat('amber', '#3a1c08', 0.1), neck=0.4,
             stopper=ni)
    K.box(ctx, 'A0 niche soap', nx1 - 0.48, nx1 - 0.2, ys, ys + 0.07, zc - 0.07, zc + 0.08, M.flat('soap', '#e6dcc6', 0.6), C,
          bevel=0.025)


# ------------------------------------------------------------------------------------ vanity wall
def _vanity(ctx):
    """South wall: the floating oak slab with two carved troughs, deck taps, oak-framed mirrors on the stone, the
    timber beam above them with two enamel lamps, and what stands on and under the slab."""
    vx0, vx1, vz0, _ = S.BATH_VANITY
    vx1 = min(vx1, XE)                         # the slab's east end meets the wainscot
    yb, yt = 2.38, 2.83                        # 5.4in thick, top at 34in
    oak = M.oak()
    fv = K.Frame(0.0, ZSP, 0.0, -1.0)          # the stone's mesh plane: u = ZSP - z, v = -x
    top = K.fbox(ctx, fv, 'A0 vanity top', -0.008, ZSP - vz0, -vx1, -vx0, yb, yt, oak, C)
    zf = ZSP - M.stone_relief_ft(1.0)          # the proudest stones' faces
    a, b, bd = 0.46, 0.62, 0.36                # basins 14.9 x 11in, 4.3in deep
    zc = (vz0 + zf) / 2 - 0.05                 # basins a little forward of the middle: the taps stand behind them
    for i, xb in enumerate(S.BATH_BASINS_X):
        cut = K.sink_cutter(ctx, fv, C, f'A0 vanity cutter {i}', ZSP - zc, -xb, yt - bd, yt + 0.12, a, b, 9)
        K.bool_cut(top, cut)
        K.fcyl(ctx, fv, f'A0 basin {i} drain', ZSP - zc, -xb, yt - bd + 0.004, 0.065, 0.008, 'y', M.nickel(), C, verts=40)
        Q.deck_tap(ctx, fv, C, f'A0 tap {i}', ZSP - (zf - 0.13), -xb, yt, lever=1 if i else -1)
    ctx.add_bevel(top, 0.012, 3)
    # mirrors, hung on the stone (their backs touch the proudest stones)
    fm = K.Frame(0.0, zf - 0.006, 0.0, -1.0)
    for i, xb in enumerate(S.BATH_BASINS_X):
        Q.wood_mirror(ctx, fm, C, f'A0 mirror {i}', -(xb + 1.0), -(xb - 1.0), 3.85, 6.35)
    # the beam across the wall above the mirrors, let into the stone; a lamp over each basin on its face
    zb = ZSP + 0.01 - BEAM_D / 2
    Q.hewn_beam(ctx, 'A0 wall beam', 'x', X0 + 0.004, X1 - 0.004, zb, BEAM_Y[0], BEAM_Y[1], BEAM_D, M.beam(), C, seed=1.3)
    fl = K.Frame(0.0, zb - BEAM_D / 2 + 0.01, 0.0, -1.0)
    for i, xb in enumerate(S.BATH_BASINS_X):
        Q.enamel_lamp(ctx, fl, C, f'A0 lamp {i}', -xb, (BEAM_Y[0] + BEAM_Y[1]) / 2)
    # on the slab, between the basins: a barrel cactus in a galvanised bucket, two folded striped hand towels, soap
    xm = (S.BATH_BASINS_X[0] + S.BATH_BASINS_X[1]) / 2
    Q.bucket(ctx, C, 'A0 cactus pot', xm + 0.35, yt, zf - 0.36, 0.25, 0.40, M.galvanised())
    Q.revolve(ctx, 'A0 cactus soil', [(0.225, 0.345), (0.02, 0.355)], xm + 0.35, yt, zf - 0.36, M.flat('soil', '#3a2e24', 0.95), C,
              seg=32, cap0=False, cap1=True)
    Q.barrel_cactus(ctx, C, 'A0 cactus', xm + 0.35, yt + 0.33, zf - 0.36, 0.2, 0.78)
    st = M.striped('striped_hand', base='#cfc4a8', stripe='#4a4a40', pitch_in=1.25, duty=0.3, axis='x')
    K.folded_towel(ctx, C, 'A0 hand towel 0', xm - 0.5, yt, zc - 0.02, 0.62, 0.5, 0.06, 0.0, st)
    K.folded_towel(ctx, C, 'A0 hand towel 1', xm - 0.5, yt + 0.06, zc - 0.02, 0.6, 0.48, 0.06, 0.04, st)
    K.bottle(ctx, C, 'A0 soap', S.BATH_BASINS_X[0] + b + 0.22, yt, zf - 0.2, r=0.1, h=0.5, mat=M.flat('amber', '#3a1c08', 0.1))
    for nm in ('A0 soap pump', 'A0 soap pump head'):         # nickel pump to match the fittings
        ob = bpy.data.objects.get(nm)
        if ob is not None and len(ob.data.materials):
            ob.data.materials[0] = M.nickel()
    # seagrass basket with rolled towels under the slab
    bx, bz = S.BATH_BASINS_X[1] - 0.9, zc + 0.05
    K.asset_prop(ctx, C, 'wicker_basket_01', bx, FL, bz, rot=0.0, height=0.5, name='A0 basket')
    terry = K.towel_band_material('primary_towel_white', K.WHITE_TOWEL)
    for i, (dx, dy) in enumerate(((-0.315, 0.0), (0.0, 0.0), (0.315, 0.0), (-0.1575, 0.268), (0.1575, 0.268))):
        tw = ctx.cylinder(f'A0 basket towel {i}', (bx + dx, FL + 0.216 + dy, bz), 0.155, 0.66, None, C, verts=32, axis='Z')
        tw.data.materials.append(terry)
        ctx.add_bevel(tw, 0.035, 2)
    # fringed woven mat in front of the vanity
    mx0, mx1, mz0, mz1 = xm - 1.7, xm + 1.7, vz0 - 2.05, vz0 - 0.15
    K.box(ctx, 'A0 rug woven', mx0, mx1, FL, FL + 0.03, mz0, mz1, M.jute(), C, bevel=0.01)
    Q.fringe(ctx, C, 'A0 rug fringe W', mx0 + 0.01, mz0 + 0.02, mz1 - 0.02, FL + 0.012, -1, seed=1.0)
    Q.fringe(ctx, C, 'A0 rug fringe E', mx1 - 0.01, mz0 + 0.02, mz1 - 0.02, FL + 0.012, 1, seed=4.0)
    return zf


def _toilet(ctx, zf):
    """South-west corner: a floor-standing one-piece WC, its tank to the stone, facing north; paper on the west wall."""
    fw = K.Frame(S.BATH_TOILET_X, zf - 0.02, 0.0, -1.0)      # u = out of the stone (north), v = -x
    K.skirted_wc(ctx, fw, C, 'A0 WC', floor=FL, length=2.15)      # compact: 21in stay clear to the shower glass
    fww = K.Frame(XW, 0.0, 1.0, 0.0)           # west wainscot face: u = x - XW, v = -z
    Q.tp_holder(ctx, fww, C, 'A0 paper', -26.52, 2.2)


def _shelf(ctx):
    """West wall, on the plaster between W13 and the stone: a reclaimed-timber shelf on forged iron brackets with
    a small still life (stoneware and glass bottles, a framed botanical print, a trailing succulent)."""
    xp = X0 + TP                               # plaster face
    fp = K.Frame(xp, 0.0, 1.0, 0.0)            # u = x - xp, v = -z
    ys, z0, z1, dep, th = 4.75, 26.30, 27.92, 0.55, 0.14
    K.fbox(ctx, fp, 'A0 shelf timber', 0.0, dep, -z1, -z0, ys, ys + th, M.timber(), C, bevel=0.012)
    for i, zz in enumerate((z0 + 0.3, z1 - 0.3)):
        Q.iron_bracket(ctx, fp, C, f'A0 shelf bracket {i}', -zz, ys, depth=0.46, drop=0.44)
    y = ys + th
    ware = M.flat('stoneware', '#d9d2c2', 0.45)
    Q.bottle(ctx, C, 'A0 shelf flagon', xp + 0.27, y, z0 + 0.2, 0.095, 0.5, ware, neck=0.34)
    Q.revolve(ctx, 'A0 shelf flagon glaze', [(0.0955, 0.31), (0.087, 0.335), (0.04, 0.385), (0.0335, 0.40), (0.0335, 0.475)],
              xp + 0.27, y, z0 + 0.2, M.flat('ochre_glaze', '#8a6234', 0.25), C, seg=32, cap0=False, cap1=False)
    Q.bottle(ctx, C, 'A0 shelf bottle green', xp + 0.36, y, z0 + 0.42, 0.055, 0.36, M.flat('green_glass', '#2f4a3c', 0.08), neck=0.45)
    w, h, lean = 0.5, 0.66, 7.0
    Q.framed_print(ctx, C, 'A0 shelf print', xp + 0.05 + h * math.sin(math.radians(lean)) + 0.012, y, z0 + 0.78, w, h, lean, 'east')
    Q.jar(ctx, C, 'A0 shelf jar', xp + 0.38, y, z0 + 1.08, 0.075, 0.2, ware)
    Q.bottle(ctx, C, 'A0 shelf bottle amber', xp + 0.22, y, z0 + 1.2, 0.07, 0.6, M.flat('amber', '#3a1c08', 0.1), neck=0.42,
             stopper=M.flat('cork', '#9c7a52', 0.9))
    Q.trailing_plant(ctx, C, 'A0 shelf trailing plant', xp + 0.3, y, z1 - 0.2, heading=0.25, fan=(-1.0, 1.25))


def _east(ctx):
    """East wall: a nickel towel bar with a striped bath towel between the door's leaf and the vanity, an outlet;
    the light switch beside the door."""
    fe = K.Frame(X1 - TP, 0.0, -1.0, 0.0)      # east plaster face: u = (X1 - TP) - x, v = z
    yb = 4.45
    u, rb = Q.towel_bar(ctx, fe, C, 'A0 towel bar', 24.45, 26.10, yb)
    K.draped(ctx, fe, C, 'A0 bath towel', u, u, 24.62, 25.93, yb + rb, 1.55, 1.95,
             M.striped('striped_bath', base='#a79d7e', stripe='#3c3b33', pitch_in=1.6, duty=0.34, axis='z'), th=0.055, rc=rb)
    K.outlet(ctx, fe, C, 'A0 outlet', 27.25, 4.2)
    fn = K.Frame(0.0, Z0 + TP, 0.0, 1.0)       # north plaster face: u = z - (Z0 + TP), v = x
    xs = DL0 - 0.42
    K.fbox(ctx, fn, 'A0 switch plate', 0.0, 0.018, xs - 0.19, xs + 0.19, 4.0, 4.38, 'paint_trim', C, bevel=0.006)
    for k in (-1, 1):
        K.fbox(ctx, fn, f'A0 switch rocker {k}', 0.018, 0.026, xs + k * 0.085 - 0.05, xs + k * 0.085 + 0.05, 4.08, 4.30,
               K.CERAMIC, C, bevel=0.004)


def _ceiling(ctx):
    """One hewn beam on the ceiling, from the door's wall to the stone, between the shower and the door; cans, the
    fan grille."""
    xb = (TILE_E + DL0) / 2 - 0.2
    Q.hewn_beam(ctx, 'A0 ceiling beam', 'z', Z0 + 0.01, ZSP - 0.02, xb, 7.50, 7.995, 0.46, M.beam(), C, seed=4.1)
    cans = [(7.6, 23.0), (7.6, 25.45), (3.2, 25.45), (4.8, 22.7)]
    for x, z in cans:
        lighting.can(ctx, x, z, ceil=CEIL, coll=f'{ZONE}_lights', watts=9.0, kelvin=CAN_K)
    K.exhaust_grille(ctx, C, 'A0 exhaust', 1.5, 25.3, ceil=CEIL)
    return len(cans)


# ------------------------------------------------------------------------------- entry points
def build_primary(ctx):
    """Called by baths.build() with the other baths, before the warp. The room itself is built by build_room()
    after the warp (see the module docstring); here only its collection is made, which is also the mark that
    tells bl/revisions.primary_bath_fit_out that the baths zone was asked for."""
    ctx.coll(C, ZONE)
    return None


def build_room(ctx):
    """Fit out the primary bath on the built model, in plan feet (called by bl/revisions.primary_bath_fit_out)."""
    ctx.coll(C, ZONE)
    out = {'floor slabs restyled': _floor(ctx)}
    _walls(ctx)
    _window(ctx)
    _shower(ctx)
    zf = _vanity(ctx)
    _toilet(ctx, zf)
    _shelf(ctx)
    _east(ctx)
    out['cans'] = _ceiling(ctx)
    out['objects'] = len(ctx.coll(C).all_objects)
    out['stone face z'] = round(zf, 3)
    return out
