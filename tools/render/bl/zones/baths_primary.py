"""Primary ensuite (tour stop A0) of zone `baths`; see baths.py for the shared helpers.

Seventh round (2026-11-21), the owner: "The walls in primary bathroom, it's not coherent, some of the wall are
green, make it coherent be removing these green walls and set it to white". The grey-green board wainscot, its cap
rail and the cream plaster skins are gone. Every wall except the stone wall is plain white: the shell's own painted
wall (the house's `paint_wall`), full height, with a low white tile base at the floor; the ceiling is the shell's
white ceiling; the shower's tile, mosaic and stone trims are white. One white room with one stone wall. Layout,
stone, beams, vanity, mirrors, lamps, shelf, floor and fixtures are the sixth round's.

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
  * shower - plain matte white tile (24x48in, quiet joints) on its two solid walls, white mosaic floor with a
    linear drain behind a flush off-white stone threshold (curbless), frameless glass on the east side (door,
    hinged on the north wall, and a short fixed return) and the south side (fixed, into a channel on the window
    mullion), an exposed brushed-nickel set with rain head and hand shower at the west end, a tiled niche. The
    tile ends on a white edge profile just outside each glass line; the glass is low-iron, so the white tile
    behind it stays white.
  * other walls (east, north beside the door, west outside the shower) - plain white painted wall, floor to
    ceiling (the shell's wall, nothing on it), with a 5 5/8in base of the shower's white tile at the floor; white
    ceiling (the shell's) with one timber beam. (The sixth round had grey-green wainscot under cream plaster.)
  * floor - quiet warm-grey honed stone, 24x24in, no pattern.
  * on the west wall beside the stone: a reclaimed-timber shelf on black iron brackets with stoneware
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

Names matter to bake_web.py (README, "Web model contract"): wall finishes (stone, tile, tile base) carry
tg_class = 'wall'.
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
CEIL = 8.0                                     # the shell's white ceiling (no skin under it since the seventh round)
BASE_Y = 0.5                                   # top of the white tile base on the painted walls (5 5/8in above the floor)
XW, XE, ZN = X0 + T, X1 - T, Z0 + T            # faces of the tile on the west / north wall and of the tile base (T thick:
#                                                it covers the shell's 0.05 ft painted skirting); the painted walls' own
#                                                faces are X0, X1, Z0
ZSP = Z1 - 0.06                                # the stone wall's mesh plane (mortar bed), in front of the shell skirting
GX, GZ = S.BATH_SHOWER[1], S.BATH_SHOWER[3]    # centre lines of the shower's east and south glass
TILE_E = GX + 0.075                            # the shower tile runs this far east on the north wall (the hinge side)
TILE_S = GZ + 0.05                             # ... and this far south on the west wall: to the window mullion's south face
TRIM = 0.012                                   # width of the white edge profile that ends the tile there
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
    """Shower: white tile, full height. Every other wall except the stone wall is the shell's painted wall as it
    stands (the house's wall white, floor to ceiling): this room adds nothing to it but a low white tile base. The
    ceiling is the shell's white ceiling."""
    nx0, nx1, ny0, ny1, dep = S.BATH_NICHE
    tile = M.shower_tile(a0_ft=(nx0 + nx1) / 2, floor_ft=FL)     # a vertical joint on the niche's centre line
    door = [(DL0, DL1, -1.0, DHEAD)]
    # --- shower: white tile, full height, on the north wall (with the niche) and the west wall (with W13's north
    # lite). On each wall the tile runs a little past the glass line and ends on a white edge profile (satin white
    # like the trim; it was nickel, which mirrored the stone as a brown line on the white wall): on the north wall
    # behind the door's hinges, on the west wall under the glass channel, to the mullion's south face
    _skin(ctx, 'A0 tile shower north', 'z', Z0, ZN, X0, TILE_E, FL, CEIL, tile, C, holes=[(nx0, nx1, ny0, ny1)])
    _skin(ctx, 'A0 tile shower west', 'x', X0, XW, ZN, TILE_S, FL, CEIL, tile, C, holes=[(WZ0, TILE_S + 1.0, SILL, 99.0)])
    _box(ctx, 'A0 tile shower edge trim', TILE_E, TILE_E + TRIM, FL, CEIL, Z0, ZN + 0.004, 'paint_trim', C)
    _box(ctx, 'A0 tile shower edge trim W', X0, XW + 0.004, FL, SILL - 0.035, TILE_S, TILE_S + TRIM, 'paint_trim', C)
    # niche lining: tiled back, sides and head, a stone sill a little proud of the wall
    zb = Z0 - dep                              # the recess's back (shell)
    lt = 0.02
    _box(ctx, 'A0 tile niche back', nx0, nx1, ny0, ny1, zb, zb + lt, tile, C)
    _box(ctx, 'A0 tile niche side W', nx0, nx0 + lt, ny0 + 0.035, ny1 - lt, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche side E', nx1 - lt, nx1, ny0 + 0.035, ny1 - lt, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche head', nx0, nx1, ny1 - lt, ny1, zb + lt, ZN, tile, C)
    _box(ctx, 'A0 tile niche sill', nx0, nx1, ny0, ny0 + 0.035, zb + lt, ZN + 0.012, M.sill(), C, bevel=0.004)
    # --- the painted walls' base: the shower's white tile, BASE_Y high and as thick as the tile (flush with it; it
    # covers the shell's painted skirting, which has gaps at the old door and the old window): north wall from the
    # shower's edge trim to the door's liner and from the liner to the east wall, the east wall to the stone, the
    # west wall from the shower's edge trim to the stone
    _skin(ctx, 'A0 tile base north', 'z', Z0, ZN, TILE_E, X1, FL, BASE_Y, tile, C, holes=door)
    _skin(ctx, 'A0 tile base east', 'x', XE, X1, ZN, Z1, FL, BASE_Y, tile, C)
    _skin(ctx, 'A0 tile base west', 'x', X0, XW, TILE_S + TRIM, Z1, FL, BASE_Y, tile, C)
    # --- south wall: stacked stone, full width and height: a dense grid (~1cm) the material displaces in world
    # space; its ends stand a hair inside the painted east and west walls
    x0, x1 = X0 - 0.01, X1 + 0.01
    nx = int(round((x1 - x0) / 0.034))
    ny = int(round((CEIL - FL) / 0.034))
    _wall(Q.grid_wall_z(ctx, 'A0 tile south stone', ZSP, x0, x1, FL, CEIL, nx, ny, M.stone(), C, facing=-1))


def _window(ctx):
    """W13's finish: the shower lite (north of the mullion) gets a tiled reveal and a stone sill, the dry lite an oak
    stool on the painted wall, a painted reveal and a linen roman shade; a post on the mullion carries the shower's
    south glass. Seventh round (every window white): the post is satin white here, and bl/revisions.white_windows,
    which runs after this, gives the post, the stool and its lip the windows' own white by name
    (revision_spec.WINDOW_WHITE_ALSO), so in the built house the stool is white, not oak."""
    fx = S.WEST_WALL_C + 0.11                  # room face of the window frame (bl/revisions.bath_window: 0.22 ft deep
    #                                            on the centre line of the 5 in wall)
    m0, m1 = GZ - 0.05, GZ + 0.05              # the mullion
    post = _box(ctx, 'A0 window mullion post', fx, XW + 0.015, SILL, 8.0, m0, m1, 'paint_trim', C)
    _box(ctx, 'A0 tile window return N', fx, XW, SILL + 0.035, 8.0, WZ0, WZ0 + 0.03, M.shower_tile(), C)
    _box(ctx, 'A0 window sill stone', fx, XW + 0.02, SILL, SILL + 0.035, WZ0, m0, M.sill(), C, bevel=0.006)
    _box(ctx, 'A0 window return S', fx, X0, SILL + 0.04, 8.0, WZ1 - 0.03, WZ1, 'paint_wall', C)
    oak = M.oak()
    _box(ctx, 'A0 window stool', fx, X0, SILL, SILL + 0.04, m1, WZ1, oak, C)
    _box(ctx, 'A0 window stool lip', X0, X0 + 0.07, SILL - 0.035, SILL + 0.04, m1, WZ1 + 0.07, oak, C, bevel=0.008)
    # roman shade over the dry lite, inside-mounted under the head (the reveal is 0.098 ft deep), drawn up to
    # about 6'-4"
    a, b = m1 + 0.02, WZ1 - 0.05
    K.box(ctx, 'A0 roman shade headrail', fx + 0.015, X0, 7.74, 7.88, a, b, 'paint_trim', C)
    K.box(ctx, 'A0 roman shade fabric', X0 - 0.04, X0 - 0.02, 6.62, 7.74, a + 0.01, b - 0.01, 'fabric_linen_white', C)
    for i, yb in enumerate((6.30, 6.47)):
        fold = K.box(ctx, f'A0 roman shade fold {i}', X0 - 0.055, X0 + 0.045 - 0.025 * i, yb, yb + 0.19, a + 0.01, b - 0.01,
                     'fabric_linen_white', C)
        ctx.add_bevel(fold, 0.06, 4)
    return post


# ------------------------------------------------------------------------------------ shower
def _shower(ctx):
    ni = M.nickel()
    t = 0.0155                                 # half the glass thickness
    # south side: one fixed panel from the channel on the window mullion to the corner
    Q.glass_panel(ctx, C, 'A0 shower glass south', (XW + 0.03, GZ), (GX - t - 0.004, GZ), GY0, GY1)
    Q.u_channel(ctx, C, 'A0 shower channel south', (XW + 0.02, GZ), (GX - 0.04, GZ), THR)
    K.box(ctx, 'A0 shower channel wall', XW, XW + 0.065, THR, GY1, GZ - 0.0375, GZ + 0.0375, ni, C, bevel=0.006)
    # east side: the door, hinged on the north wall, and a short fixed return that closes the corner
    zr = Z0 + 2.425                            # the door's free edge / the return's north end
    Q.glass_panel(ctx, C, 'A0 shower glass return', (GX, zr), (GX, GZ + t), GY0, GY1)
    Q.u_channel(ctx, C, 'A0 shower channel return', (GX, zr - 0.01), (GX, GZ + 0.0375), THR)
    Q.glass_panel(ctx, C, 'A0 shower glass door', (GX, ZN + 0.05), (GX, zr - 0.02), GY0 + 0.02, GY1)
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
    Q.exposed_shower(ctx, fn, C, 'A0 shower set', X0 + 1.075, y_valve=3.6, y_top=6.72, reach=(GZ - ZN) / 2 - 0.17,
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
    vx1 = min(vx1, X1)                         # the slab's east end meets the painted east wall: 6'-6" as on the sheet
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
    Q.hewn_beam(ctx, 'A0 wall beam', 'x', X0 - 0.02, X1 + 0.02, zb, BEAM_Y[0], BEAM_Y[1], BEAM_D, M.beam(), C, seed=1.3)
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
    fww = K.Frame(X0, 0.0, 1.0, 0.0)           # the painted west wall: u = x - X0, v = -z
    Q.tp_holder(ctx, fww, C, 'A0 paper', -(Z1 - 1.842), 2.2)


def _shelf(ctx):
    """West wall, on the painted wall between W13 and the stone: a reclaimed-timber shelf on forged iron brackets
    with a small still life (stoneware and glass bottles, a framed botanical print, a trailing succulent)."""
    xp = X0                                    # the painted wall's face
    fp = K.Frame(xp, 0.0, 1.0, 0.0)            # u = x - xp, v = -z
    ys, z0, z1, dep, th = 4.75, Z1 - 2.062, Z1 - 0.442, 0.55, 0.14
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
    fe = K.Frame(X1, 0.0, -1.0, 0.0)           # the painted east wall: u = X1 - x, v = z
    yb = 4.45
    u, rb = Q.towel_bar(ctx, fe, C, 'A0 towel bar', Z0 + 3.255, Z0 + 4.905, yb)
    K.draped(ctx, fe, C, 'A0 bath towel', u, u, Z0 + 3.425, Z0 + 4.735, yb + rb, 1.55, 1.95,
             M.striped('striped_bath', base='#a79d7e', stripe='#3c3b33', pitch_in=1.6, duty=0.34, axis='z'), th=0.055, rc=rb)
    K.outlet(ctx, fe, C, 'A0 outlet', Z1 - 1.112, 4.2)
    fn = K.Frame(0.0, Z0, 0.0, 1.0)            # the painted north wall: u = z - Z0, v = x
    xs = DL0 - 0.42
    K.fbox(ctx, fn, 'A0 switch plate', 0.0, 0.018, xs - 0.19, xs + 0.19, 4.0, 4.38, 'paint_trim', C, bevel=0.006)
    for k in (-1, 1):
        K.fbox(ctx, fn, f'A0 switch rocker {k}', 0.018, 0.026, xs + k * 0.085 - 0.05, xs + k * 0.085 + 0.05, 4.08, 4.30,
               K.CERAMIC, C, bevel=0.004)


def _ceiling(ctx):
    """One hewn beam on the shell's white ceiling, from the door's wall to the stone, between the shower and the
    door (its north end and its top stand a little inside the wall and the ceiling slab); cans, the fan grille."""
    xb = (TILE_E + DL0) / 2 - 0.2
    Q.hewn_beam(ctx, 'A0 ceiling beam', 'z', Z0 - 0.02, ZSP - 0.02, xb, 7.50, CEIL + 0.03, 0.46, M.beam(), C, seed=4.1)
    cans = [(X0 + 7.375, Z0 + 1.805), (X0 + 7.375, Z0 + 4.255), (X0 + 2.975, Z0 + 4.255), (X0 + 4.575, Z0 + 1.505)]
    for x, z in cans:
        lighting.can(ctx, x, z, ceil=CEIL, coll=f'{ZONE}_lights', watts=9.0, kelvin=CAN_K)
    K.exhaust_grille(ctx, C, 'A0 exhaust', X0 + 1.275, Z0 + 4.105, ceil=CEIL)
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
