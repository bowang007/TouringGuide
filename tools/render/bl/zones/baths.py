"""Zone `baths`: primary ensuite (A0), shared bath (A1) and Bedroom 3 bath (A3).

Design (1077 W McKinley language, DESIGN.md):
  * primary - floating walnut 60in double vanity, Calacatta quartz top, two undermount basins with
    matte-black wall spouts, wide backlit LED mirror; 60x42 shower with frameless glass (inline
    panel + hinged door + return), white 3D wave tile on the shower walls with an LED niche in a
    furred wet wall, ceiling rain head + slide-bar hand shower, linear drain; wall-hung WC with a
    black flush plate side-on against the east wall (off the doorway axis) under a walnut shelf,
    black ladder towel warmer on the south wall where the doorway view from the suite lands,
    walnut linen unit with towels and a succulent; large-format porcelain elsewhere, full height.
  * shared - black fluted feature wall behind the WC and the tub end (west, from z 23.9 with a
    black edge trim), light porcelain elsewhere incl. the vanity corner, so the round backlit
    mirror reflects light tile; floating walnut vanity with a vessel basin, tall black faucet,
    tray + soap, hand towel on a short bar beside it, slim linear sconce; wall-hung WC + black
    flush plate on the flutes; wall-to-wall alcove tub with a fixed glass panel and black shower
    trim; the tub back wall is furred 3.6in for a recessed LED niche; bath towel at the tub end.
  * suite3 - compact curbless shower with a fixed walk-in panel (ceiling stay keeps the A3 camera
    clear) and a furred wet wall with a recessed LED niche over the valve, wall-hung WC, black
    fluted feature wall behind the small floating walnut vanity (undermount basin) and pill
    mirror.
  * Plain wall tile is the zone material Z_baths_porcelain (baths_kit.porcelain_material): honed
    vein-cut limestone-look 24x48 porcelain like the reference baths.

All positions follow the anchors in scene_classification / layout_revision (vanity 60x21 at the
north wall, 33in aisle, shower 60x42, WC centre x=8.3; shared WC centreline z=24.8 on the west
wall; suite3 shower at the west end, WC on the north wall, vanity on the east wall).
"""
import time

import bpy

from .. import lighting
from . import baths_kit as K

ZONE = 'zone_baths'
T = 0.065            # tile skin thickness (covers the 0.055ft painted skirting of the shell)
POR = 'tile_wall_porcelain'
WAVE = 'tile_wave_white'
WAL = 'walnut_slab'
CEIL = 7.999


def _colls(ctx):
    ctx.coll(ZONE)
    for c in ('primary', 'shared', 'suite3', 'lights'):
        ctx.coll(f'{ZONE}_{c}', ZONE)


def _bounds(ctx, mid):
    return next(r['bounds_ft'] for r in ctx.meas['rooms'] if r['id'] == mid)


# --------------------------------------------------------------------------- vanity helper
def floating_vanity(ctx, f, coll, name, v0, v1, depth, y_bot, top_mat, fronts, top_y=2.80, top_t=0.125,
                    holes=()):
    """Floating walnut vanity in wall frame f. fronts: list of (v0, v1, y0, y1) drawer/door fronts.
    holes: list of (uc, vc, a, b) undermount cut-outs in the top. Returns the top object."""
    y_top0 = top_y - top_t
    fu1 = depth - 0.02                 # front face of the fronts (top overhangs 1/4in)
    fu0 = fu1 - 0.06
    carcass = K.fbox(ctx, f, name + ' carcass', 0.0, fu0, v0, v1, y_bot, y_top0, WAL, coll, bevel=0.008)
    for i, (a, b, c, d) in enumerate(fronts):
        K.fbox(ctx, f, f'{name} front {i}', fu0, fu1, a, b, c, d, WAL, coll, bevel=0.006)
    # bevel AFTER the sink cut-outs: harden-normals then also covers the boolean's new edges
    # (otherwise smooth normals bleed across the triangulated top) and eases the cut-out rims
    top = K.fbox(ctx, f, name + ' top', 0.0, depth, v0, v1, y_top0, top_y, top_mat, coll)
    for j, (uc, vc, a, b) in enumerate(holes):
        cut = K.sink_cutter(ctx, f, coll, f'{name} cutter {j}', uc, vc, y_top0 - 0.1, top_y + 0.1, a, b, 5.5)
        K.bool_cut(top, cut)
        # the (hollow) cabinet makes room for the undermount bowl hanging below the top
        cav = K.sink_cutter(ctx, f, coll, f'{name} bowl cavity {j}', uc, vc, y_top0 - 0.6, y_top0 + 0.02,
                            a + 0.06, b + 0.06, 5.0)
        K.bool_cut(carcass, cav)
    ctx.add_bevel(top, 0.012, 3)
    # warm LED toe glow under the floating carcass (light only; the tape itself is tucked away)
    _toe_glow(ctx, f, coll, name, fu0 - 0.16, fu0 - 0.08, v0 + 0.08, v1 - 0.08, y_bot)
    return top


def _toe_glow(ctx, f, coll, name, u0, u1, v0, v1, y_bot):
    ob = K.fbox(ctx, f, name + ' toe glow', u0, u1, v0, v1, y_bot - 0.012, y_bot - 0.002, None, coll)
    ob.data.materials.append(lighting.emitter('vanity_glow', 3500, 6.0))
    ob.visible_camera = False
    return ob


# ------------------------------------------------------------------------------- primary
def build_primary(ctx):
    c = f'{ZONE}_primary'
    X0, X1, Z0, Z1 = _bounds(ctx, 'M03')
    FL = 0.028
    XW, ZN, XE, ZS = X0 + T, Z0 + T, X1 - T, Z1 - T
    XF = 0.55                                  # furred shower wet wall face (3.9in build-out)
    SH_X1, SH_Z0, SH_Y = 5.30, 25.78, 0.09     # shower floor slab (shell): x 0.30-5.30, z 25.78-29.28
    NZ0, NZ1, NY0, NY1 = 26.65, 28.35, 4.30, 5.30   # LED niche
    por, wave = K.porcelain_material(ctx), ctx.mat(WAVE)

    # --- wall tile ---------------------------------------------------------------------
    K.skin(ctx, 'A0 tile north', 'z', Z0, ZN, XW, XE, FL, CEIL, por, c, holes=[(6.3135, 9.125, 0.0, 6.67)])
    K.skin(ctx, 'A0 tile west', 'x', X0, XW, Z0, SH_Z0, FL, CEIL, por, c, holes=[(22.40, 25.40, 5.0, 7.0)])
    K.skin(ctx, 'A0 tile east', 'x', XE, X1, Z0, Z1, FL, CEIL, por, c)
    K.skin(ctx, 'A0 tile south', 'z', ZS, Z1, SH_X1, XE, FL, CEIL, por, c)
    K.skin(ctx, 'A0 wave south', 'z', ZS, Z1, XF, SH_X1, FL, CEIL, wave, c)
    K.skin(ctx, 'A0 wave wetwall', 'x', X0, XF, SH_Z0, Z1, FL, CEIL, wave, c, holes=[(NZ0, NZ1, NY0, NY1)])
    K.box(ctx, 'A0 niche back', X0, 0.30, NY0, NY1, NZ0, NZ1, por, c)
    K.box(ctx, 'A0 niche sill', 0.30, XF + 0.004, NY0 - 0.03, NY0 + 0.012, NZ0, NZ1, 'quartz_calacatta', c, bevel=0.004)
    em = lighting.emitter('niche_led', 3500, 16.0)
    s = K.box(ctx, 'A0 niche led', 0.31, XF - 0.03, NY1 - 0.022, NY1 - 0.004, NZ0 + 0.02, NZ1 - 0.02, None, c)
    s.data.materials.append(em)
    K.bottle(ctx, c, 'A0 niche bottle 1', 0.42, NY0 + 0.012, 27.25, r=0.085, h=0.55)
    K.bottle(ctx, c, 'A0 niche bottle 2', 0.42, NY0 + 0.012, 27.55, r=0.085, h=0.55,
             mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))

    # --- vanity: 60 x 21in floating walnut, Calacatta top, 2 undermount basins -----------------
    fv = K.Frame(0.0, ZN, 0.0, 1.0)            # u = z - ZN, v = x
    depth = 23.03 - ZN
    vc = (XW + 5.30) / 2
    sinks = [(0.92, vc - 1.25), (0.92, vc + 1.25)]
    fronts = [(XW + 0.006, vc - 0.006, 1.0, 1.82), (vc + 0.006, 5.30 - 0.006, 1.0, 1.82),
              (XW + 0.006, vc - 0.006, 1.86, 2.58), (vc + 0.006, 5.30 - 0.006, 1.86, 2.58)]
    floating_vanity(ctx, fv, c, 'A0 vanity', XW, 5.30, depth, 1.0, 'quartz_calacatta', fronts,
                    holes=[(u, v, 0.44, 0.68) for u, v in sinks])
    for i, (u, v) in enumerate(sinks):
        K.undermount_bowl(ctx, fv, c, f'A0 basin {i}', u, v, 2.675, a=0.46, b=0.70, depth=0.45)
        K.wall_faucet(ctx, fv, c, f'A0 faucet {i}', v, 3.22, reach=0.64)
    K.backlit_rect_mirror(ctx, fv, c, 'A0 mirror', vc - 2.2, vc + 2.2, 3.85, 6.55)
    K.outlet(ctx, fv, c, 'A0 outlet', 5.78, 3.55)
    K.exhaust_grille(ctx, c, 'A0 exhaust', 5.6, 25.4)
    K.fbox(ctx, fv, 'A0 tray', 0.22, 0.62, vc - 0.32, vc + 0.32, 2.80, 2.83, K.BLACK, c, bevel=0.01)
    x, z = fv.w(0.42, vc - 0.12)
    K.bottle(ctx, c, 'A0 soap', x, 2.83, z, r=0.1, h=0.5, mat=K.matte_material('bottle_amber', (0.30, 0.17, 0.08), 0.35))
    x, z = fv.w(0.42, vc + 0.15)
    cand = ctx.cylinder('A0 candle', (x, 2.83 + 0.16, z), 0.11, 0.32, None, c, verts=40)
    cand.data.materials.append(K.matte_material('candle_jar', (0.70, 0.66, 0.60), 0.45))

    # --- linen unit (24 x 12in) under the privacy window ------------------------------------
    L0, L1 = 23.44, 25.44
    K.box(ctx, 'A0 linen carcass', XW, 1.24, 1.0, 2.675, L0, L1, WAL, c, bevel=0.008)
    for i, (a, b) in enumerate(((L0 + 0.005, (L0 + L1) / 2 - 0.006), ((L0 + L1) / 2 + 0.006, L1 - 0.005))):
        K.box(ctx, f'A0 linen door {i}', 1.24, 1.30, 1.0, 2.58, a, b, WAL, c, bevel=0.006)
    K.box(ctx, 'A0 linen top', XW, 1.32, 2.675, 2.80, L0, L1, 'quartz_calacatta', c, bevel=0.012)
    _toe_glow(ctx, K.Frame(XW, 0, 1, 0), c, 'A0 linen', 0.6, 0.7, -L1 + 0.08, -L0 - 0.08, 1.0)
    terry = K.towel_band_material('towel_white', K.WHITE_TOWEL)
    y = 2.80
    for i, (dw, rr) in enumerate(((0.0, 0.0), (-0.02, 0.035), (0.01, -0.02))):
        K.folded_towel(ctx, c, f'A0 linen towel {i}', 0.80, y, 23.98, 0.78 + dw, 0.62, 0.115, rr, terry)
        y += 0.115
    K.asset_prop(ctx, c, 'potted_plant_04', 0.80, 2.80, 24.92, rot=0.6, name='A0 succulent')

    # --- shower: frameless glass, rain head, hand shower, linear drain ------------------------
    gz = SH_Z0 + 0.03
    gy0, gy1 = SH_Y + 0.02, SH_Y + 0.02 + 6.5
    K.glass_panel(ctx, c, 'A0 glass inline', (XF + 0.008, gz), (1.30, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 glass door', (1.325, gz), (3.325, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 glass fixed', (3.35, gz), (5.27, gz), gy0, gy1)
    K.glass_panel(ctx, c, 'A0 glass return', (5.285, gz + 0.035), (5.285, ZS - 0.008), gy0, gy1)
    K.u_channel(ctx, c, 'A0 channel inline', (XF + 0.004, gz), (1.30, gz), SH_Y)
    K.u_channel(ctx, c, 'A0 channel fixed', (3.35, gz), (5.27 + 0.03, gz), SH_Y)
    K.u_channel(ctx, c, 'A0 channel return', (5.285, gz + 0.04), (5.285, ZS - 0.004), SH_Y)
    for yy in (gy0 + 0.9, gy1 - 0.9):
        K.clamp(ctx, c, 'A0 wall clamp', XF + 0.07, yy, gz, 'x')
        K.clamp(ctx, c, 'A0 hinge', 1.3125, yy, gz, 'x', size=(0.30, 0.2, 0.085))
        K.clamp(ctx, c, 'A0 corner clamp', 5.27, yy, gz + 0.015, 'z', size=(0.12, 0.10, 0.07))
        K.clamp(ctx, c, 'A0 return clamp', 5.285, yy, ZS - 0.07, 'z')
    for dz in (-0.1, 0.1):
        ctx.cylinder('A0 door pull', (3.12, 3.65, gz + dz), 0.026, 1.05, K.BLACK, c, verts=24)
        for yy in (3.25, 4.05):
            ctx.cylinder('A0 door pull post', (3.12, yy, gz + dz / 2), 0.016, 0.1, K.BLACK, c, verts=16, axis='Z')
    K.rain_head_ceiling(ctx, c, 'A0 rain', 2.15, 27.55, drop=0.42, size=0.83)
    ff = K.Frame(XF, 0.0, 1.0, 0.0)            # wet wall: u = x - XF, v = -z
    K.valve_trim(ctx, ff, c, 'A0 valve', -27.50, 3.55)
    K.hand_shower(ctx, ff, c, 'A0 hand', -28.78, 3.75, 6.10, 3.30)
    K.linear_drain(ctx, c, 'A0 drain', 'x', 0.85, 4.95, ZS - 0.17, SH_Y)

    # --- wall-hung WC on the east wall (off the doorway axis), flush plate, paper holder ----
    # The doorway (north wall x 6.31-9.13) frames the south wall from P0 / P1 / S0, so the WC sits
    # side-on against the east wall and the doorway view lands on the towel warmer instead.
    fe = K.Frame(XE, 0.0, -1.0, 0.0)           # east wall: u = XE - x, v = z
    fw = K.Frame(XE, 27.55, -1.0, 0.0)
    K.wall_hung_wc(ctx, fw, c, 'A0 WC')
    K.flush_plate(ctx, fw, c, 0.0, 3.45, 'A0 flush plate')
    K.tp_holder(ctx, fe, c, 'A0 paper', 26.30, 2.25)
    # floating walnut shelf over the WC: rolled guest towels + a small plant (styles the east wall)
    K.fbox(ctx, fw, 'A0 shelf', 0.0, 0.62, -0.95, 0.95, 4.62, 4.74, WAL, c, bevel=0.01)
    oat = K.towel_band_material('towel_A0_guest', K.OAT_TOWEL)
    for i, dv in enumerate((-0.66, -0.36)):
        x, z = fw.w(0.31, dv)
        tw = ctx.cylinder(f'A0 shelf towel {i}', (x, 4.74 + 0.14, z), 0.14, 0.55, None, c, verts=32, axis='X')
        tw.data.materials.append(oat)
        ctx.add_bevel(tw, 0.03, 2)
    x, z = fw.w(0.3, 0.45)
    K.asset_prop(ctx, c, 'potted_plant_04', x, 4.74, z, rot=2.2, name='A0 shelf plant')

    # --- towel warmer with a draped bath towel, centred in the doorway view (south wall) ----
    fs = K.Frame(0.0, ZS, 0.0, -1.0)           # south wall: u = ZS - z, v = -x
    wv0, wv1 = -7.86, -6.20
    u, rb = K.towel_warmer(ctx, fs, c, 'A0 warmer', wv0, wv1, 1.65, 4.65, bars=7)
    top_bar = 1.65 + 0.12 + (4.65 - 1.65 - 0.2)
    yb = top_bar + rb - 1.17
    K.draped(ctx, fs, c, 'A0 bath towel', u, u, wv0 + 0.16, wv1 - 0.16, top_bar + rb, 1.30, 1.17,
             K.towel_band_material('towel_A0', K.OAT_TOWEL, (yb + 0.16, yb + 0.30)), th=0.055, rc=rb)

    return None


# -------------------------------------------------------------------------------- shared
def build_shared(ctx):
    c = f'{ZONE}_shared'
    X0, X1, Z0, Z1 = _bounds(ctx, 'M04')
    FL = 0.028
    FB, FD = 0.055, 0.035                      # fluted tile: bed + rib depth
    FC = X0 + FB + FD                          # rib crest plane
    ZN, XE, ZS = Z0 + T, X1 - T, Z1 - T
    XW = X0 + T
    por = K.porcelain_material(ctx)

    # black fluted feature behind the WC and the tub end only; the vanity corner stays light
    # porcelain so the round mirror (seen from A1 at ~45 deg) reflects light tile, not a black wall.
    ZF0 = 23.90                                # fluted panel north edge (black metal edge trim)
    K.fluted_wall(ctx, 'A1 fluted west', 'x', X0, +1, ZF0, Z1, FL, CEIL, FB, FD, 0.10, K.fluted_material(ctx), c)
    K.box(ctx, 'A1 fluted edge trim', X0, FC + 0.006, FL, CEIL, ZF0 - 0.022, ZF0 + 0.004, K.BLACK, c, bevel=0.003)
    K.skin(ctx, 'A1 tile west', 'x', X0, XW, Z0, ZF0 - 0.022, FL, CEIL, por, c)
    K.skin(ctx, 'A1 tile north', 'z', Z0, ZN, XW, XE, FL, CEIL, por, c, holes=[(13.0113, 15.4800, 0.0, 6.67)])
    K.skin(ctx, 'A1 tile east', 'x', XE, X1, Z0, Z1, FL, CEIL, por, c)
    # tub back wall furred 3.6in (the shell wall cannot be cut) for a recessed LED niche at the shower end
    ZT = ZS - 0.30                             # finished tile face of the tub back wall
    NX0, NX1, NY0, NY1 = 11.20, 13.05, 3.95, 4.95
    K.skin(ctx, 'A1 tile south', 'z', ZT, Z1, FC, XE, FL, CEIL, por, c, holes=[(NX0, NX1, NY0, NY1)])
    K.box(ctx, 'A1 niche back', NX0 + 0.001, NX1 - 0.001, NY0, NY1, Z1 - 0.03, Z1, por, c)
    K.box(ctx, 'A1 niche sill', NX0 + 0.002, NX1 - 0.002, NY0 - 0.03, NY0 + 0.012, ZT - 0.004, Z1 - 0.03,
          'quartz_white', c, bevel=0.004)
    s = K.box(ctx, 'A1 niche led', NX0 + 0.02, NX1 - 0.02, NY1 - 0.022, NY1 - 0.004, ZT + 0.03, ZT + 0.14, None, c)
    s.data.materials.append(lighting.emitter('niche_led', 3500, 16.0))
    K.bottle(ctx, c, 'A1 niche bottle 1', 11.62, NY0 + 0.012, Z1 - 0.20, r=0.085, h=0.55)
    K.bottle(ctx, c, 'A1 niche bottle 2', 11.90, NY0 + 0.012, Z1 - 0.20, r=0.085, h=0.55,
             mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))

    # --- vanity with vessel basin -------------------------------------------------------
    fv = K.Frame(0.0, ZN, 0.0, 1.0)
    v0, v1 = XW, 12.93
    vc = (v0 + v1) / 2
    depth = 1.60
    floating_vanity(ctx, fv, c, 'A1 vanity', v0, v1, depth, 1.05, 'quartz_white',
                    [(v0 + 0.006, v1 - 0.006, 1.05, 2.58)])
    K.vessel_sink(ctx, fv, c, 'A1 vessel', 0.86, vc + 0.08, 2.80, a=0.47, b=0.62, h=0.36)
    K.deck_faucet(ctx, fv, c, 'A1 faucet', 0.21, vc + 0.08, 2.80, height=1.0, reach=0.5)
    K.backlit_round_mirror(ctx, fv, c, 'A1 mirror', vc + 0.08, 5.0, 0.84)
    K.exhaust_grille(ctx, c, 'A1 exhaust', 14.7, 25.6)
    # slim linear sconce above the mirror
    K.fbox(ctx, fv, 'A1 sconce plate', 0.0, 0.03, vc + 0.08 - 0.08, vc + 0.08 + 0.08, 6.33, 6.47, K.BLACK, c, bevel=0.006)
    K.fbox(ctx, fv, 'A1 sconce arm', 0.03, 0.2, vc + 0.08 - 0.02, vc + 0.08 + 0.02, 6.38, 6.42, K.BLACK, c)
    K.fbox(ctx, fv, 'A1 sconce bar', 0.17, 0.27, vc + 0.08 - 0.62, vc + 0.08 + 0.62, 6.34, 6.43, K.BLACK, c, bevel=0.01)
    led = K.fbox(ctx, fv, 'A1 sconce diffuser', 0.18, 0.26, vc + 0.08 - 0.6, vc + 0.08 + 0.6, 6.335, 6.342, None, c)
    led.data.materials.append(lighting.emitter('sconce_diffuser', 3500, 22.0))
    # small black tray with the soap at the west end of the top
    K.fbox(ctx, fv, 'A1 tray', 0.14, 0.56, v0 + 0.05, v0 + 0.42, 2.80, 2.83, K.BLACK, c, bevel=0.01)
    x, z = fv.w(0.32, v0 + 0.235)
    K.bottle(ctx, c, 'A1 soap', x, 2.83, z, r=0.09, h=0.5, mat=K.matte_material('bottle_amber', (0.30, 0.17, 0.08), 0.35))
    # hand towel on a short black bar on the (porcelain) west wall above the vanity
    fwt = K.Frame(XW, 0.0, 1.0, 0.0)             # west tile face: u = x - XW, v = -z
    hv0, hv1, hy = -22.86, -22.12, 4.40
    u = K.towel_bar(ctx, fwt, c, 'A1 hand towel bar', hv0, hv1, hy, u=0.2)
    K.draped(ctx, fwt, c, 'A1 hand towel', u, u, hv0 + 0.07, hv1 - 0.07, hy + 0.026, 0.92, 0.86,
             K.towel_band_material('towel_A1_hand', K.WHITE_TOWEL), th=0.045, rc=0.026)

    # --- wall-hung WC on the fluted west wall facing east (centreline z = 24.8) -------------
    fw = K.Frame(FC, 24.8, 1.0, 0.0)
    K.wall_hung_wc(ctx, fw, c, 'A1 WC')
    K.flush_plate(ctx, fw, c, 0.0, 3.40, 'A1 flush plate')
    fwest = K.Frame(FC, 0.0, 1.0, 0.0)           # u = x - FC, v = -z
    K.tp_holder(ctx, K.Frame(XW, 0.0, 1.0, 0.0), c, 'A1 paper', -23.45, 2.25)

    # --- alcove tub, wall to wall --------------------------------------------------------
    xc = (FC + XE) / 2
    hb = (XE - FC) / 2 - 0.002
    fb = K.Frame(xc, ZT, 0.0, -1.0)            # u = ZT - z, v = xc - x
    D, TOP = 2.66, 1.62
    n_o, n_i = 22, 5
    rings = [
        K.R(FL, 0.0, D, hb, n_o, n_o),
        K.R(TOP - 0.035, 0.0, D, hb, n_o, n_o),
        K.R(TOP - 0.01, 0.003, D - 0.003, hb - 0.003, n_o, n_o),
        K.R(TOP, 0.012, D - 0.012, hb - 0.012, n_o, n_o),
        K.R(TOP, 0.22 - 0.012, D - 0.30 + 0.012, hb - 0.29 + 0.012, n_i, n_i),
        K.R(TOP - 0.012, 0.22, D - 0.30, hb - 0.29, n_i, n_i),
        K.R(TOP - 0.07, 0.235, D - 0.315, hb - 0.305, n_i, n_i),
        K.R(0.95, 0.30, D - 0.39, hb - 0.47, 4.5, 4.5),
        K.R(0.48, 0.38, D - 0.48, hb - 0.70, 4.0, 4.0),
        K.R(0.37, 0.45, D - 0.56, hb - 0.84, 3.6, 3.6),
        K.R(0.335, 0.55, D - 0.66, hb - 0.98, 3.2, 3.2),
    ]
    K.loft(ctx, fb, 'A1 tub', rings, K.CERAMIC, c, seg=96)
    ux = (0.55 + D - 0.66) / 2
    x, z = fb.w(ux, hb - 1.25)
    ctx.cylinder('A1 tub drain', (x, 0.338, z), 0.11, 0.008, K.BLACK, c, verts=32)
    # tub / shower trim on the fluted wall
    tz = ZT - D / 2 - 0.04
    K.valve_trim(ctx, fwest, c, 'A1 valve', -tz, 3.45)
    K.fcyl(ctx, fwest, 'A1 spout plate', 0.012, -tz, 2.08, 0.09, 0.024, 'u', K.BLACK, c)
    K.fcyl(ctx, fwest, 'A1 spout', 0.27, -tz, 2.08, 0.045, 0.5, 'u', K.BLACK, c)
    K.rain_head_wall(ctx, fwest, c, 'A1 rain', -tz, 6.70, arm=1.15, dia=0.70)
    # fixed glass panel on the tub rim with a stay to the back wall
    gz = ZT - D + 0.15
    K.glass_panel(ctx, c, 'A1 glass', (FC + 0.006, gz), (13.32, gz), TOP + 0.015, 6.95)
    K.u_channel(ctx, c, 'A1 channel', (FC + 0.004, gz), (13.32, gz), TOP)
    for yy in (TOP + 0.7, 6.25):
        K.clamp(ctx, c, 'A1 wall clamp', FC + 0.07, yy, gz, 'x')
    ctx.cylinder('A1 stay', (13.24, 6.88, (gz + ZT) / 2), 0.025, ZT - gz - 0.02, K.BLACK, c, verts=24, axis='Z')
    K.clamp(ctx, c, 'A1 stay clamp', 13.24, 6.88, gz, 'x', size=(0.12, 0.10, 0.08))
    ctx.cylinder('A1 stay rose', (13.24, 6.88, ZT - 0.012), 0.055, 0.024, K.BLACK, c, verts=24, axis='Z')

    # --- towel bar on the east wall at the tub end (out of the A1 lens's face) ---------------
    fe = K.Frame(XE, 0.0, -1.0, 0.0)
    u = K.towel_bar(ctx, fe, c, 'A1 towel bar', 25.35, 26.95, 4.15)
    yb = 4.15 + 0.026 - 1.04
    K.draped(ctx, fe, c, 'A1 bath towel', u, u, 25.55, 26.75, 4.15 + 0.026, 1.16, 1.04,
             K.towel_band_material('towel_A1', K.CHARCOAL_TOWEL, (yb + 0.16, yb + 0.30)), th=0.05, rc=0.026)
    return None


# -------------------------------------------------------------------------------- suite 3
def build_suite3(ctx):
    c = f'{ZONE}_suite3'
    X0, X1, Z0, Z1 = _bounds(ctx, 'M09')
    FL = 0.10
    XW, ZN, XE, ZS = X0 + T, Z0 + T, X1 - T, Z1 - T
    SX = 3.23
    FB, FD = 0.055, 0.035                      # fluted tile: bed + rib depth (as in the shared bath)
    FCE = X1 - FB - FD                         # rib crest plane of the fluted east (vanity) wall
    ZNF = ZN + 0.30                            # furred shower wet wall (3.6in) for the LED niche
    NX0, NX1, NY0, NY1 = 1.15, 2.35, 4.30, 5.25
    por = K.porcelain_material(ctx)

    K.skin(ctx, 'A3 tile west', 'x', X0, XW, Z0, Z1, FL, CEIL, por, c, holes=[(38.70, 41.70, 5.0, 7.0)])
    # shower back wall: furred wet wall with a recessed LED niche over the valve
    K.skin(ctx, 'A3 wetwall', 'z', Z0, ZNF, XW, SX, FL, CEIL, por, c, holes=[(NX0, NX1, NY0, NY1)])
    K.box(ctx, 'A3 niche back', NX0 + 0.001, NX1 - 0.001, NY0, NY1, Z0, ZN + 0.02, por, c)
    K.box(ctx, 'A3 niche sill', NX0 + 0.002, NX1 - 0.002, NY0 - 0.03, NY0 + 0.012, ZN + 0.02, ZNF + 0.004,
          'quartz_white', c, bevel=0.004)
    s = K.box(ctx, 'A3 niche led', NX0 + 0.02, NX1 - 0.02, NY1 - 0.022, NY1 - 0.004, ZNF - 0.14, ZNF - 0.03, None, c)
    s.data.materials.append(lighting.emitter('niche_led', 3500, 16.0))
    K.bottle(ctx, c, 'A3 niche bottle 1', 1.58, NY0 + 0.012, ZN + 0.17, r=0.075, h=0.5)
    K.bottle(ctx, c, 'A3 niche bottle 2', 1.90, NY0 + 0.012, ZN + 0.17, r=0.075, h=0.5,
             mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))
    K.skin(ctx, 'A3 tile north', 'z', Z0, ZN, SX, FCE, FL, CEIL, por, c)
    # feature wall: black fluted porcelain behind the floating vanity and pill mirror (east)
    K.fluted_wall(ctx, 'A3 fluted east', 'x', X1, -1, Z0, Z1, FL, CEIL, FB, FD, 0.10, K.fluted_material(ctx), c)
    K.skin(ctx, 'A3 tile south', 'z', ZS, Z1, XW, FCE, FL, CEIL, por, c, holes=[(3.42, 6.15, 0.0, 6.72)])
    # W11 sits inside the shower: tiled reveal returns and a quartz stool over the frame's inner rail
    K.box(ctx, 'A3 window stool', 0.08, XW + 0.012, 5.0, 5.09, 38.70, 41.70, 'quartz_white', c, bevel=0.006)
    for z0, z1 in ((38.70, 38.735), (41.665, 41.70)):
        K.box(ctx, 'A3 window return', 0.08, XW, 5.09, 7.0, z0, z1, por, c)

    # --- curbless shower: mosaic floor, walk-in fixed panel, black trim -------------------
    K.box(ctx, 'A3 shower floor', X0, SX, FL, FL + 0.015, Z0, Z1, 'tile_shower_floor', c)
    sy = FL + 0.015
    K.linear_drain(ctx, c, 'A3 drain', 'z', ZNF + 0.15, 42.45, XW + 0.18, sy)
    gx = SX - 0.016
    K.glass_panel(ctx, c, 'A3 glass', (gx, ZNF + 0.006), (gx, 40.40), sy + 0.02, 6.75)
    K.u_channel(ctx, c, 'A3 channel', (gx, ZNF + 0.004), (gx, 40.40), sy)
    for yy in (1.1, 5.9):
        K.clamp(ctx, c, 'A3 wall clamp', gx, yy, ZNF + 0.07, 'z')
    K.clamp(ctx, c, 'A3 post clamp', gx, 6.72, 40.30, 'z', size=(0.10, 0.08, 0.07))
    ctx.cylinder('A3 ceiling stay', (gx, (6.76 + 8.0) / 2, 40.30), 0.025, 8.0 - 6.76, K.BLACK, c, verts=24)
    ctx.cylinder('A3 ceiling stay rose', (gx, 7.99, 40.30), 0.055, 0.02, K.BLACK, c, verts=24)
    fn = K.Frame(0.0, ZN, 0.0, 1.0)            # north wall: u = z - ZN, v = x
    fnf = K.Frame(0.0, ZNF, 0.0, 1.0)          # furred shower wall
    K.valve_trim(ctx, fnf, c, 'A3 valve', 1.75, 3.65)
    K.rain_head_wall(ctx, fnf, c, 'A3 rain', 1.75, 6.72, arm=1.1, dia=0.70)

    # --- wall-hung WC on the north wall ----------------------------------------------------
    fw = K.Frame(4.78, ZN, 0.0, 1.0)
    K.wall_hung_wc(ctx, fw, c, 'A3 WC')
    K.flush_plate(ctx, fw, c, 0.0, 3.45, 'A3 flush plate')
    K.tp_holder(ctx, fn, c, 'A3 paper', 5.95, 2.25)

    # --- floating vanity on the fluted east wall, pill mirror -------------------------------
    fv = K.Frame(FCE, 0.0, -1.0, 0.0)           # u = FCE - x (from the rib crests), v = z
    v0, v1 = 40.28, 42.70
    vc = (v0 + v1) / 2
    sv = vc + 0.12                             # basin nudged south: hand towels sit at the north end
    floating_vanity(ctx, fv, c, 'A3 vanity', v0, v1, FCE - 6.22, 1.30, 'quartz_white',
                    [(v0 + 0.006, v1 - 0.006, 1.30, 2.58)], holes=[(0.80, sv, 0.36, 0.50)])
    K.undermount_bowl(ctx, fv, c, 'A3 basin', 0.80, sv, 2.675, a=0.38, b=0.52, depth=0.42)
    K.deck_faucet(ctx, fv, c, 'A3 faucet', 0.21, sv, 2.80, height=0.72, reach=0.44, r=0.035)
    K.pill_mirror(ctx, fv, c, 'A3 mirror', sv, 5.0, 1.55, 2.6)
    K.outlet(ctx, fv, c, 'A3 outlet', 40.06, 3.45)
    K.exhaust_grille(ctx, c, 'A3 exhaust', 4.4, 41.4)
    x, z = fv.w(0.74, v0 + 0.30)
    sage = K.towel_band_material('towel_sage', K.SAGE_TOWEL)
    K.folded_towel(ctx, c, 'A3 hand towel 0', x, 2.80, z, 0.70, 0.42, 0.075, 0.0, sage)
    K.folded_towel(ctx, c, 'A3 hand towel 1', x, 2.875, z, 0.68, 0.40, 0.075, 0.03, sage)
    x, z = fv.w(0.32, v1 - 0.17)
    K.bottle(ctx, c, 'A3 soap', x, 2.80, z, r=0.09, h=0.5, mat=K.matte_material('bottle_white', (0.80, 0.79, 0.76), 0.5))
    u = K.towel_bar(ctx, fv, c, 'A3 towel bar', 38.35, 39.85, 3.95)
    yb = 3.95 + 0.026 - 0.98
    K.draped(ctx, fv, c, 'A3 bath towel', u, u, 38.55, 39.65, 3.95 + 0.026, 1.10, 0.98,
             K.towel_band_material('towel_A3', K.SAGE_TOWEL, (yb + 0.16, yb + 0.30)), th=0.05, rc=0.026)
    return None


# --------------------------------------------------------------------------------- lights
# The baths are lit almost entirely by their own fixtures (one frosted window each, none in the shared
# bath). render_panos white-balances every pano for daylight (9000K + tint), under which a 4000K can
# renders deep orange (measured wall r/g ~1.45, b/g ~0.6). 6000K cans and mirrors give the clean cream
# white of the reference baths (wall r/g ~1.1, b/g ~0.8); the LED accents stay warmer (3500K).
CAN_K = 6000
CANS = [(2.8, 23.4), (7.85, 23.4), (4.2, 27.5), (7.85, 27.5),      # primary
        (13.4, 23.6), (13.4, 27.9),                                 # shared
        (1.75, 39.2), (5.45, 40.35)]                                # suite 3 (shower can over the rain head)


def build_lights(ctx):
    for x, z in CANS:
        lighting.can(ctx, x, z, coll=f'{ZONE}_lights', watts=9.0, kelvin=CAN_K)
    return len(CANS)


# ---------------------------------------------------------------------------------- stats
def _stats(ctx):
    dg = bpy.context.evaluated_depsgraph_get()
    n_obj, tris = 0, 0
    for ob in ctx.coll(ZONE).all_objects:
        n_obj += 1
        if ob.type not in ('MESH', 'CURVE'):
            continue
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        if me is not None:
            me.calc_loop_triangles()
            tris += len(me.loop_triangles)
            ev.to_mesh_clear()
    return n_obj, tris


def build(ctx):
    t0 = time.time()
    _colls(ctx)
    build_primary(ctx)
    build_shared(ctx)
    build_suite3(ctx)
    out = {'cans': build_lights(ctx)}
    for room in ('primary', 'shared', 'suite3'):
        out[room] = len(ctx.coll(f'{ZONE}_{room}').all_objects)
    bpy.context.view_layer.update()
    n, tris = _stats(ctx)
    out.update(objects=n, triangles=tris, seconds=round(time.time() - t0, 1))
    return out
