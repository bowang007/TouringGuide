"""Zone `baths`: primary ensuite (A0), shared bath (A1) and Bedroom 3 bath (A3).

Design:
  * primary (baths_primary.py) - the owner's warm rustic-modern restyle (styles/ references): sage subway
    tile shower with aged-brass fittings, floating solid-oak double vanity with carved basins, brass
    mirrors and sconces, sage V-groove wainscot under cream plaster, a stacked-stone wall, encaustic
    floor. Its west-wall finish ('A0 tile west ...') is cut around the window by revisions.bath_window.
  * shared (baths_shared.py) - the owner's restyle: rustic-oak wood-look tile feature wall with a lit
    niche behind the WC, warm Spanish-cream stone-look porcelain, light-oak vanity with a travertine
    trough basin, backlit mirror, limestone-look floor; the alcove tub keeps its glass screen.
  * suite3 - compact curbless shower with a fixed walk-in panel (ceiling stay keeps the A3 camera
    clear) and a furred wet wall with a recessed LED niche over the valve, wall-hung WC, black
    fluted feature wall behind the small floating walnut vanity (undermount basin) and pill
    mirror.
  * suite3's plain wall tile is the zone material Z_baths_porcelain (baths_kit.porcelain_material):
    honed vein-cut limestone-look 24x48 porcelain (1077 W McKinley language, DESIGN.md).

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
    from .baths_primary import build_primary       # lazy: the room modules import this module's helpers
    from .baths_shared import build_shared
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
