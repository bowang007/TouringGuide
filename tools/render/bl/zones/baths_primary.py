"""Primary ensuite (tour stop A0) of zone `baths`; see baths.py for the shared helpers.

Warm rustic-modern restyle after the owner's references (styles/: primary bathroom wall style, primary
bathroom sink, 132684, pr):
  * shower - glossy sage-green 3x12in subway tile, running bond, light grout, full height on the wet
    wall and the shower's south wall; frameless glass (inline panel, hinged door, fixed panel, return)
    with aged-brass hinges, clamps, channel and pull; aged-brass exposed thermostatic shower set on the
    shower's long back wall, west of the skylight (bar valve, rigid riser, swan-neck arm, round rain head
    centred in the shower's depth, stick hand shower on the riser); brass linear drain along the wet
    wall; cream 2x2in mosaic floor.
  * vanity wall - floating solid-oak slab (5.4in thick) with two rectangular basins carved into it,
    wall-mounted brass spouts with side handles, two brass-framed mirrors and three brass sconces with
    opal bell shades; a seagrass basket of rolled towels under the slab, a jute mat in front.
  * walls - sage-grey V-groove panelling to 42in with a small cap, warm cream plaster above (north,
    west and the room part of the south wall); the east (WC) wall is the feature: floor-to-ceiling
    stacked natural stone with true displacement, the wall-hung WC with a round brass flush plate, and
    a reclaimed timber shelf on black iron brackets with a framed print, a jug and a succulent.
  * floor - 8in indigo-and-cream encaustic cement tile (the shell's floor slab gets the zone material).
  * a brass ladder towel warmer with an oat bath towel on the south wall (the doorway view from S0).

Contract with bl/revisions.py: the west-wall finish is only plain boxes named 'A0 tile west ...' (lower
panelling, cap, upper plaster), built with the concept window's hole; nothing else sits on the west
wall between concept z 22.4 and 25.4; the shower ceiling (skylight) stays clear.

Warp (bl/warp.py): wall finishes, the slab, glass panels ('A0 shower glass ...') and channels are
fitted (reshaped with the room); fixtures and decor are loose and move in plan clusters. The vanity
wall's loose pieces are symmetric about the slab centre and clear of the walls' TOUCH band, so they
land symmetric on the reshaped slab (the basin cutters move with their spouts and mirrors). Fixtures
on the shower walls and the stone wall touch those walls, so their clusters stay on the wall faces.
"""
import re

import bpy

from . import baths_kit as K
from . import baths_primary_kit as Q
from . import baths_primary_mats as M
from .baths import CEIL, T, ZONE, _bounds

HOLE_W = [(22.40, 25.40, 5.0, 7.0)]          # concept window in the west wall (revisions re-cuts it)
DOOR_N = [(6.3135, 9.125, 0.0, 6.67)]        # doorway in the north wall
TP = 0.03                                    # cream plaster skin over the shell wall
WAIN, CAP1, CAPD = 3.5, 3.6, 0.115           # panelling top (42in), cap top, cap depth from the wall


def _restyle_shell(ctx):
    """Zone materials for the room's shell floor and the shower floor slab."""
    out = {}
    for pat, mat in ((r'Primary ensuite porcelain floor$', M.encaustic()),
                     (r'Primary shower stone floor', M.shower_mosaic())):
        for ob in bpy.data.objects:
            if ob.type == 'MESH' and re.search(pat, ob.name):
                if ob.data.users > 1:
                    ob.data = ob.data.copy()
                if len(ob.data.materials):
                    for i in range(len(ob.data.materials)):
                        ob.data.materials[i] = mat
                else:
                    ob.data.materials.append(mat)
                out[ob.name] = mat.name
    return out


def _walls(ctx, c, X0, X1, Z0, Z1, FL, SH_Z0, SX1, XS):
    vg, cap, pl, sub = M.vgroove(), M.sage_paint(), M.plaster(), M.sage_subway()
    XW, ZS = X0 + T, Z1 - T
    # west wall, room part (window wall): three plain layers, all 'A0 tile west ...' (revisions cuts them)
    K.skin(ctx, 'A0 tile west wainscot', 'x', X0, X0 + T, Z0, SH_Z0, FL, WAIN, vg, c, holes=HOLE_W)
    K.skin(ctx, 'A0 tile west cap', 'x', X0, X0 + CAPD, Z0, SH_Z0, WAIN, CAP1, cap, c, holes=HOLE_W)
    K.skin(ctx, 'A0 tile west upper', 'x', X0, X0 + TP, Z0, SH_Z0, CAP1, CEIL, pl, c, holes=HOLE_W)
    # north wall (vanity + doorway); runs east under the stone wall's edge
    K.skin(ctx, 'A0 tile north wainscot', 'z', Z0, Z0 + T, X0 + T, X1, FL, WAIN, vg, c, holes=DOOR_N)
    K.skin(ctx, 'A0 tile north cap', 'z', Z0, Z0 + CAPD, X0 + CAPD, X1, WAIN, CAP1, cap, c, holes=DOOR_N)
    K.skin(ctx, 'A0 tile north upper', 'z', Z0, Z0 + TP, X0 + TP, X1, CAP1, CEIL, pl, c, holes=DOOR_N)
    # south wall, room part (towel warmer, seen through the doorway)
    K.skin(ctx, 'A0 tile south wainscot', 'z', Z1 - T, Z1, SX1, X1, FL, WAIN, vg, c)
    K.skin(ctx, 'A0 tile south cap', 'z', Z1 - CAPD, Z1, SX1, X1, WAIN, CAP1, cap, c)
    K.skin(ctx, 'A0 tile south upper', 'z', Z1 - TP, Z1, SX1, X1, CAP1, CEIL, pl, c)
    # shower: sage subway, full height
    K.skin(ctx, 'A0 tile shower wetwall', 'x', X0, XW, SH_Z0, Z1, FL, CEIL, sub, c)
    K.skin(ctx, 'A0 tile shower south', 'z', ZS, Z1, XW, SX1, FL, CEIL, sub, c)
    # east (WC) wall: stacked stone between the plaster faces of the north and south walls, a dense grid
    # (~1cm) that the stone material displaces in world space
    z0, z1 = Z0 + TP, Z1 - TP
    nz = int(round((z1 - z0) / 0.036))
    ny = int(round((CEIL - FL) / 0.035))
    Q.grid_wall(ctx, 'A0 tile east stone', XS, z0, z1, FL, CEIL, nz, ny, M.stone(), c, facing=-1)


def _vanity(ctx, c, X0, Z0, FL):
    """Floating solid-oak slab with two carved basins, brass spouts, mirrors and sconces (north wall)."""
    XW, ZN = X0 + T, Z0 + T
    S0, S1 = XW, 5.30                          # slab ends: west wall .. in line with the shower return
    vc = (S0 + S1) / 2
    depth, yb, yt = 1.72, 2.38, 2.83           # 20.6in deep, 5.4in thick, top at 34in
    fv = K.Frame(0.0, ZN, 0.0, 1.0)            # panelling face: u = z - ZN, v = x
    fp = K.Frame(0.0, Z0 + TP, 0.0, 1.0)       # plaster face (above the cap)
    oak = M.oak()
    top = K.fbox(ctx, fv, 'A0 vanity top', 0.0, depth, S0, S1, yb, yt, oak, c)
    uc, a, b, bd = 0.84, 0.46, 0.62, 0.36      # basins 14.9 x 11in, 4.3in deep
    sinks = [vc - 1.25, vc + 1.25]
    for i, vs in enumerate(sinks):
        cut = K.sink_cutter(ctx, fv, c, f'A0 vanity cutter {i}', uc, vs, yt - bd, yt + 0.12, a, b, 9)
        K.bool_cut(top, cut)
        K.fcyl(ctx, fv, f'A0 basin {i} drain', uc, vs, yt - bd + 0.004, 0.065, 0.008, 'y', M.brass(), c, verts=40)
        Q.wall_spout(ctx, fv, c, f'A0 spout {i}', vs, 3.12, reach=0.6, handle_dv=0.36 if i else -0.36)
    ctx.add_bevel(top, 0.012, 3)
    # mirrors over the basins (14.4in, about the basin width), three sconces (between and outside),
    # symmetric about vc; the outer plates stand ~2in off the frames (they touched them before) and
    # their shades stay ~2in clear of the west wall after the warp
    for i, vs in enumerate(sinks):
        Q.framed_mirror(ctx, fp, c, f'A0 mirror {i}', vs - 0.60, vs + 0.60, 3.95, 6.25)
    for i, dv in enumerate((-2.15, 0.0, 2.15)):
        Q.sconce(ctx, fp, c, f'A0 sconce {i}', vc + dv, 5.45, watts=5.0)
    # styling on the slab: folded linen hand towels and a soap pump between the basins
    lin = ctx.mat('fabric_linen_white')
    x, z = fv.w(0.95, vc)
    K.folded_towel(ctx, c, 'A0 hand towel 0', x, yt, z, 0.62, 0.5, 0.06, 0.0, lin)
    K.folded_towel(ctx, c, 'A0 hand towel 1', x, yt + 0.06, z, 0.6, 0.48, 0.06, 0.04, lin)
    x, z = fv.w(0.36, vc - 0.12)
    K.bottle(ctx, c, 'A0 soap', x, yt, z, r=0.1, h=0.5,
             mat=K.matte_material('primary_bottle_amber', (0.085, 0.032, 0.008), 0.12))   # glossy amber glass
    for nm in ('A0 soap pump', 'A0 soap pump head'):         # brass pump to match the fittings
        ob = bpy.data.objects.get(nm)
        if ob is not None and len(ob.data.materials):
            ob.data.materials[0] = M.brass()
    # seagrass basket with rolled towels under the slab, centred
    K.asset_prop(ctx, c, 'wicker_basket_01', vc, FL, ZN + 0.82, rot=0.0, height=0.5, name='A0 basket')
    terry = K.towel_band_material('primary_towel_white', K.WHITE_TOWEL)
    for i, (dx, dy) in enumerate(((-0.315, 0.0), (0.0, 0.0), (0.315, 0.0), (-0.1575, 0.268), (0.1575, 0.268))):
        tw = ctx.cylinder(f'A0 basket towel {i}', (vc + dx, FL + 0.216 + dy, ZN + 0.82), 0.155, 0.66, None, c,
                          verts=32, axis='Z')
        tw.data.materials.append(terry)
        ctx.add_bevel(tw, 0.035, 2)
    # jute mat in front of the vanity
    K.box(ctx, 'A0 rug jute', vc - 1.55, vc + 1.55, FL, FL + 0.035, ZN + depth + 0.35, ZN + depth + 2.35, M.jute(), c,
          bevel=0.012)
    K.outlet(ctx, fv, c, 'A0 outlet', 5.85, 3.05)
    return vc


def _shower(ctx, c, X0, Z1, SH_Z0, SH_X1):
    XW, ZS = X0 + T, Z1 - T
    SH_Y = 0.09                                # shower floor slab top (shell)
    gz = SH_Z0 + 0.03
    gy0, gy1 = SH_Y + 0.02, SH_Y + 0.02 + 6.5
    # glass: named '... shower glass ...' so the panels are fitted (reshaped with the shower)
    K.glass_panel(ctx, c, 'A0 shower glass inline', (XW + 0.008, gz), (1.30, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 shower glass door', (1.325, gz), (3.325, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 shower glass fixed', (3.35, gz), (SH_X1 - 0.03, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 shower glass return', (SH_X1 - 0.015, gz + 0.035), (SH_X1 - 0.015, ZS - 0.008), gy0, gy1)
    Q.u_channel(ctx, c, 'A0 shower channel inline', (XW + 0.004, gz), (1.30, gz), SH_Y)
    Q.u_channel(ctx, c, 'A0 shower channel fixed', (3.35, gz), (SH_X1, gz), SH_Y)
    Q.u_channel(ctx, c, 'A0 shower channel return', (SH_X1 - 0.015, gz + 0.04), (SH_X1 - 0.015, ZS - 0.004), SH_Y)
    for yy in (gy0 + 0.9, gy1 - 0.9):
        Q.clamp(ctx, c, 'A0 wall clamp', XW + 0.085, yy, gz, 'x')
        Q.clamp(ctx, c, 'A0 hinge', 1.3125, yy, gz, 'x', size=(0.30, 0.2, 0.085))
        Q.clamp(ctx, c, 'A0 corner clamp', SH_X1 - 0.03, yy, gz + 0.015, 'z', size=(0.12, 0.10, 0.07))
        Q.clamp(ctx, c, 'A0 return clamp', SH_X1 - 0.015, yy, ZS - 0.08, 'z')
    br = M.brass()
    for dz in (-0.1, 0.1):
        ctx.cylinder('A0 door pull', (3.12, 3.65, gz + dz), 0.026, 1.05, br, c, verts=24)
        for yy in (3.25, 4.05):
            ctx.cylinder('A0 door pull post', (3.12, yy, gz + dz / 2), 0.016, 0.1, br, c, verts=16, axis='Z')
    # exposed brass set on the shower's long back (south) wall, west of the skylight (final x >= 2.7), the
    # head centred in the shower's depth; seen through the door glass from the room and the A0 hero
    fsw = K.Frame(0.0, ZS, 0.0, -1.0)          # u = ZS - z, v = -x
    Q.exposed_shower(ctx, fsw, c, 'A0 brass set', -1.42, y_valve=3.6, y_top=6.72, reach=1.32, head_r=0.36, hand_y=4.55)
    Q.linear_drain(ctx, c, 'A0 shower drain', SH_Z0 + 0.4, ZS - 0.3, XW + 0.17, SH_Y, axis='z')


def _east(ctx, c, X1, XSF):
    """Feature wall: wall-hung WC, round flush plate, paper holder, timber shelf on iron brackets."""
    emb = 0.075                                # roses reach back to the stone's mortar bed
    fw = K.Frame(XSF, 27.55, -1.0, 0.0)        # u = XSF - x, v = z
    fe = K.Frame(XSF, 0.0, -1.0, 0.0)
    K.wall_hung_wc(ctx, fw, c, 'A0 WC')
    Q.flush_buttons(ctx, fw, c, 'A0 flush plate', 0.0, 3.4, embed=emb)
    Q.tp_holder(ctx, fe, c, 'A0 paper', 26.25, 2.25, embed=emb)
    ys = 4.78
    K.fbox(ctx, fw, 'A0 shelf timber', 0.0, 0.62, -1.45, 1.45, ys, ys + 0.17, M.timber(), c, bevel=0.012)
    for i, v in enumerate((-1.0, 1.0)):
        Q.iron_bracket(ctx, fw, c, f'A0 shelf bracket {i}', v, ys, depth=0.5, drop=0.44, embed=emb)
    y = ys + 0.17
    x, z = fw.w(0.23, -0.72)
    root, _ = K.asset_prop(ctx, c, 'standing_picture_frame_01', x, y, z, rot=3.1416, name='A0 shelf art frame')
    # the model's glTF glass (alpha-blended) darkens the print: use the library's anti-reflective picture glass
    for ob in [root] + list(root.children_recursive):
        for slot in getattr(ob, 'material_slots', []):
            if slot.material is not None and 'glass' in slot.material.name.lower():
                slot.material = ctx.mat('glass_picture')
    x, z = fw.w(0.30, 0.12)
    K.asset_prop(ctx, c, 'potted_plant_04', x, y, z, rot=2.2, height=0.55, name='A0 shelf plant')
    x, z = fw.w(0.32, 0.86)
    K.asset_prop(ctx, c, 'ceramic_vase_01', x, y, z, rot=0.4, height=0.72, name='A0 shelf vase')


def _towel_warmer(ctx, c, Z1):
    """Brass ladder warmer with an oat bath towel, centred in the doorway view (south wall)."""
    fs = K.Frame(0.0, Z1 - T, 0.0, -1.0)       # panelling face: u = (Z1 - T) - z, v = -x
    wv0, wv1 = -7.86, -6.20
    y0, y1 = 1.65, 4.65
    u, rb = Q.towel_warmer(ctx, fs, c, 'A0 warmer', wv0, wv1, y0, y1, bars=6,
                           back=lambda yy: (T - TP) if yy > CAP1 else 0.0)
    top_bar = y0 + 0.12 + (y1 - y0 - 0.2)
    yb = top_bar + rb - 1.17
    K.draped(ctx, fs, c, 'A0 bath towel', u - 0.045, u + 0.045, wv0 + 0.16, wv1 - 0.16, top_bar + rb, 1.30, 1.17,
             K.towel_band_material('primary_towel_oat', K.OAT_TOWEL, (yb + 0.16, yb + 0.30)), th=0.055, rc=rb)


# ------------------------------------------------------------------------------- primary
def build_primary(ctx):
    c = f'{ZONE}_primary'
    X0, X1, Z0, Z1 = _bounds(ctx, 'M03')
    FL = 0.028
    SH_X1, SH_Z0 = 5.30, 25.78                 # shower floor slab (shell): x 0.30-5.30, z 25.78-29.28
    SX1 = SH_X1 + 0.01                         # shower tile / room finish joint on the south wall
    XS = X1 - 0.06                             # stone mesh plane (mortar bed), in front of the shell skirting
    XSF = XS - M.stone_relief_ft()             # typical stone face: fixtures mount here
    _restyle_shell(ctx)
    _walls(ctx, c, X0, X1, Z0, Z1, FL, SH_Z0, SX1, XS)
    _vanity(ctx, c, X0, Z0, FL)
    _shower(ctx, c, X0, Z1, SH_Z0, SH_X1)
    _east(ctx, c, X1, XSF)
    _towel_warmer(ctx, c, Z1)
    K.exhaust_grille(ctx, c, 'A0 exhaust', 5.6, 25.4)
    return None
