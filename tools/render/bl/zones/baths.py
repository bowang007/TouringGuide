"""Zone `baths`: primary ensuite (A0), shared bath (A1) and Bedroom 3 bath (A3).

Design:
  * primary (baths_primary.py) - laid out on the architect's sheet and styled after the owner's image
    (styles/primary bathroom wall style.jpg): stacked-stone vanity wall with the floating solid-oak slab,
    oak-framed mirrors, a timber beam and enamel lamps; white-tiled shower in the north-west corner;
    every other wall plain white with a low white tile base (seventh round; v7 final: comment, it still
    described the sixth round's cream tile and grey-green wainscot); grey stone floor; brushed nickel.
    Unlike the other two
    it is fitted out AFTER the warp, in plan feet (baths_primary.build_room, called by
    bl/revisions.primary_bath_fit_out); build_primary() below only makes its collection.
  * shared (baths_shared.py) - the owner's restyle: rustic-oak wood-look tile feature wall with a lit
    niche behind the WC, warm Spanish-cream stone-look porcelain, light-oak vanity with a travertine
    trough basin, backlit mirror, limestone-look floor; the alcove tub keeps its glass screen.
  * suite3 (baths_suite3.py) - laid out on the architect's sheet and, like the primary bath, fitted out
    AFTER the warp in plan feet: compact curbless shower across the west end with a fixed walk-in panel
    (ceiling stay) and a furred wet wall with a recessed LED niche over the valve, wall-hung WC and the
    small floating walnut vanity (undermount basin, pill mirror) on the north wall, a black fluted
    panel behind the vanity.
  * suite3's plain wall tile is the zone material Z_baths_porcelain (baths_kit.porcelain_material):
    honed vein-cut limestone-look 24x48 porcelain (1077 W McKinley language, DESIGN.md).

The shared bath follows the anchors in scene_classification / layout_revision (WC centreline z=24.8 on
the west wall); the primary bath and suite3 follow the architect's sheet (bl/revision_spec.py, BATH_* /
PRIMARY_BATH_* and BED3_BATH_*).
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
    """Called by build() with the other baths, before the warp. Since the eighth round (v7 bedrooms) the Bedroom 3
    bath is laid out on the architect's sheet and fitted out AFTER the warp, in plan feet, by
    baths_suite3.build_room (called by bl/revisions.bedroom3_fit_out), like the primary bath; here only its
    collection is made, which is also the mark that tells the revision that the baths zone was asked for."""
    ctx.coll(f'{ZONE}_suite3', ZONE)
    return None


# --------------------------------------------------------------------------------- lights
# The baths are lit almost entirely by their own fixtures (one frosted window each, none in the shared
# bath). render_panos white-balances every pano for daylight (9000K + tint), under which a 4000K can
# renders deep orange (measured wall r/g ~1.45, b/g ~0.6). 6000K cans and mirrors give the clean cream
# white of the reference baths (wall r/g ~1.1, b/g ~0.8); the LED accents stay warmer (3500K).
CAN_K = 6000
CANS = [                                                            # (primary: baths_primary._ceiling, after the warp)
        (13.4, 23.6), (13.4, 27.9)]                                 # shared (suite 3: baths_suite3.build_room, after the warp)


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
