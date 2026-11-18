"""Zone: kitchen + dining/open area (kitchen x 22.5-40.61, z 20.8-31.41; open area x 23.28-40.61,
z 14.5-20.8). Camera stops K0, D0, H2 (also seen from L2, H3).

Modern 1077-W-McKinley language: walnut flat-slab cabinetry with finger-pull channels and
toe-kick LED, Calacatta quartz worktops with full-height backsplash, integrated stainless
column fridge + stacked wall ovens, induction cooktop under a white plaster hood, floating
walnut shelves with LED, undermount sink with matte-black faucet, waterfall island with
saddle-tan leather stools and a linear LED pendant, 4in recessed cans. The open strip north of
the island stays open for circulation (layout_revision: no dining table on the island's north
side; a set there cannot keep 36in to the stools). Its only styling is a tall indoor olive tree in a
charcoal stone planter beside window W07, next to the kitchen run end (kitchen_dining_olive.py), so
the east wall reads fireplace -> window -> tree -> kitchen instead of a chain of walnut boxes. The
42in round walnut dining set (INCLUDE_DINING) and the older W07 sideboard (INCLUDE_CONSOLE) remain
available but are off.

build(ctx) -> dict of counts / notes. Helpers live in kitchen_dining_*.py.
"""
import math
import time

import bpy

from .. import lighting
from . import kitchen_dining_console as console
from . import kitchen_dining_decor as decor
from . import kitchen_dining_dining as dining
from . import kitchen_dining_kitchen as kitchen
from . import kitchen_dining_olive as olive
from .kitchen_dining_geo import ZONE, Geo

# Recessed 4in cans (x, z): tidy grid aligned to the room, clear of the skylight shaft
# (x 29.24-33.56, z 25.39-28.71), the tall units (x<28.16, z>29.21) and the pendant line.
CANS_KITCHEN = [
    (26.2, 22.6), (26.2, 26.9),            # west aisle (by K0 / tall bank), in line with living cans
    (36.4, 22.6), (36.4, 26.4),            # east aisle (island <-> sink run)
    (30.0, 29.55), (32.8, 29.55),          # south counter, aligned with the pendant ends
    (38.6, 29.55),                         # south-east counter / shelves
    (39.45, 24.1), (39.45, 28.6),          # over the sink run, flanking the window centre
]
CANS_DINING = [(26.2, 17.6), (30.2, 17.6)]   # x matches the living zone's can columns
# Open strip without a dining set: the living zone's can columns (x 26.2 / 30.2 / 34.2) carried one
# row south, plus a can on the living zone's wall-wash column (x 38.45) that accents the olive tree.
CANS_OPEN = [(26.2, 17.6), (30.2, 17.6), (34.2, 17.6), (38.45, 19.8)]

CAMERAS = ('K0', 'D0', 'H2', 'L2', 'H3')

# The open strip (z 14.5-20.8) is only ~6.3 ft deep: a dining set there leaves ~1.1 ft between its
# chairs and the island stools (the brief requires >= 36in, and layout_revision.kitchen_island keeps
# the island's north side open). Default: no dining set; a low walnut sideboard under W07 instead
# (kitchen_dining_console.py). Set INCLUDE_DINING = True to build the 42in round set + chandelier.
# Default styling is a single olive tree by the window (the sideboard read as a stray cabinet beside
# the run end and crowded the east wall).
INCLUDE_DINING = False
INCLUDE_CONSOLE = False
INCLUDE_OLIVE = not INCLUDE_DINING


def _tri_count(coll):
    dg = bpy.context.evaluated_depsgraph_get()
    tris, seen = 0, set()
    for ob in coll.all_objects:
        if ob.type != 'MESH':
            continue
        key = (ob.data.name, tuple(m.type for m in ob.modifiers))
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        ev.to_mesh_clear()
        seen.add(key)
    return tris


def _console_clearances(ctx):
    """Plan clearance report (feet) for the W07 sideboard vs stools, kitchen run end, cameras."""
    x0, x1, z0, z1 = console.footprint()

    def rect_dist(x, z):
        dx = max(x0 - x, 0, x - x1)
        dz = max(z0 - z, 0, z - z1)
        return math.hypot(dx, dz)
    out = {'sideboard_xz': [round(v, 2) for v in (x0, x1, z0, z1)]}
    out['stool3_to_sideboard_ft'] = round(rect_dist(33.4, 21.7) - 0.70, 2)
    out['sideboard_to_east_run_end_ft'] = round(21.84 - z1, 2)
    out['sideboard_to_living_ledge_ft'] = round(z0 - 16.9, 2)
    out['east_aisle_open_width_ft'] = round(x0 - 34.4, 2)
    out['camera_to_sideboard_ft'] = {nid: round(rect_dist(ctx.nodes[nid]['p'][0], ctx.nodes[nid]['p'][2]), 2)
                                     for nid in CAMERAS if nid in ctx.nodes}
    return out


def _olive_clearances(ctx):
    """Plan clearance report (feet) for the olive planter vs kitchen run end, east aisle, cameras."""
    x0, x1, z0, z1 = olive.footprint()
    cx, cz = olive.CENTER
    r = (x1 - x0) / 2
    out = {'planter_xz': [round(v, 2) for v in (x0, x1, z0, z1)]}
    out['planter_to_east_run_end_ft'] = round(21.84 - z1, 2)
    out['planter_to_living_ledge_end_ft'] = round(z0 - 16.4, 2)
    out['planter_west_of_counter_front_ft'] = round(38.405 - x0, 2)   # >0: pokes into the aisle line
    out['camera_to_planter_ft'] = {nid: round(math.hypot(ctx.nodes[nid]['p'][0] - cx, ctx.nodes[nid]['p'][2] - cz) - r, 2)
                                   for nid in CAMERAS if nid in ctx.nodes}
    return out


def _clearances(ctx):
    """Plan clearance report (feet) for the dining set vs stools, cameras and zone edges."""
    out = {}
    fp = dining.footprint()
    stools = [(29.4, 21.7, 0.70), (31.4, 21.7, 0.70), (33.4, 21.7, 0.70)]
    d = min(math.hypot(a[0] - b[0], a[1] - b[1]) - a[2] - b[2] for a in fp[1:] for b in stools)
    out['dining_chairs_to_stools_ft'] = round(d, 2)
    out['dining_north_edge_z'] = round(min(c[1] - c[2] for c in fp), 2)
    out['dining_south_edge_z'] = round(max(c[1] + c[2] for c in fp), 2)
    out['dining_east_edge_x'] = round(max(c[0] + c[2] for c in fp), 2)
    tx, tz = dining.TABLE_C
    out['table_edge_to_east_wall_ft'] = round(40.61 - (tx + dining.TABLE_R), 2)
    cams = {}
    for nid in CAMERAS:
        n = ctx.nodes.get(nid)
        if not n:
            continue
        x, _, z = n['p']
        cams[nid] = round(min(math.hypot(x - c[0], z - c[1]) - c[2] for c in fp), 2)
    out['camera_to_dining_set_ft'] = cams
    return out


def build(ctx):
    t0 = time.time()
    g = Geo(ctx)
    res = {}
    res['kitchen'] = kitchen.build(ctx, g)
    if INCLUDE_DINING:
        res['dining'] = dining.build(ctx, g)
    if INCLUDE_CONSOLE:
        res['console'] = console.build(ctx, g)
    if INCLUDE_OLIVE:
        res['olive'] = olive.build(ctx, g)
    try:
        res['decor'] = decor.build(ctx, g, dining=INCLUDE_DINING, herb=not INCLUDE_OLIVE)
    except Exception as e:                      # styling must never break the build
        import traceback
        traceback.print_exc()
        res['decor_error'] = repr(e)
    # recessed downlights
    lc = g.sub('kd_lights')
    cans = CANS_KITCHEN + (CANS_DINING if INCLUDE_DINING else CANS_OPEN)
    for x, z in cans:
        lighting.can(ctx, x, z, coll=lc)
    res['cans'] = len(cans)
    bpy.context.view_layer.update()
    root = ctx.coll(ZONE)
    res['objects'] = len([o for o in root.all_objects])
    res['triangles'] = _tri_count(root)
    if INCLUDE_DINING:
        res['clearance'] = _clearances(ctx)
    elif INCLUDE_CONSOLE:
        res['clearance'] = _console_clearances(ctx)
    elif INCLUDE_OLIVE:
        res['clearance'] = _olive_clearances(ctx)
    try:                                        # CC0 attribution list (tools/render/ASSETS.md)
        from .. import assets
        assets.write_manifest()
    except Exception as e:
        res['manifest_error'] = repr(e)
    res['seconds'] = round(time.time() - t0, 1)
    ctx.stats['kitchen_dining'] = res
    return res
