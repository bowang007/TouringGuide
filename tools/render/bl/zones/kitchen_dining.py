"""Zone: kitchen + dining/open area (kitchen x 22.5-40.61, z 20.8-31.41; open area x 23.28-40.61,
z 14.5-20.8). Camera stops K0, D0, H2 (also seen from L2, H3).

Warm vintage-American kitchen from the owner's style images (styles/kitchen *.jpg): soft layered
neutrals, no heavy dark masses. Cream painted shaker base and glass-front upper cabinets with
unlacquered-brass cup pulls and knobs and crown moulding; the tall wall as a greige "pantry wall"
holding a stainless-steel French-door refrigerator in its bay beside a built-in microwave over a wall
oven (owner's seventh round: the panelled fridge read as a pantry); a walnut open-shelf bay with brass
gallery rails on whitewashed brick; honed grey-veined marble worktops and a scalloped marble slab
with a brass pot filler behind the gas cooktop; a cream plaster hood with a dentil band; a fireclay
apron sink and brass bridge faucet under the white grid-glazed window W08 with a white casing, brass
gooseneck sconces and cafe curtains; a white-oak drawer island with a thick quartzite top under two
brass-and-glass bell pendants (7'-0" x 4'-0" at the architect's place since the eighth round, the counters
2'-0" deep); a madder-red Persian runner in the work aisle; the dining table in
line with the island at its west end (the shared-bathroom / hall side; owner's correction of 2026-11-20: it
stood north of the island before and crowded the family room) in warm oak with six striped-linen
oak chairs and a brass lantern; the indoor olive tree by W07 in a cream crock. The floor between
the island and the living room is open.

build(ctx) -> dict of counts / notes. Helpers live in kitchen_dining_*.py.
"""
import math
import time

import bpy

from .. import lighting
from .. import revision_spec as RS
from . import kitchen_dining_console as console
from . import kitchen_dining_decor as decor
from . import kitchen_dining_dining as dining
from . import kitchen_dining_kitchen as kitchen
from . import kitchen_dining_lights as kd_lights
from . import kitchen_dining_mats as kd_mats
from . import kitchen_dining_olive as olive
from . import kitchen_dining_window as window
from .kitchen_dining_geo import ZONE, Geo

# Recessed 4in cans (x, z): tidy grid aligned to the room, clear of the tall units (x<28.16, z>29.3) and the
# pendant line. The dining table at the island's west end (concept x 21.47-27.47, z 21.94-24.69) is lit by
# its lantern: no can over it (cans are loose: one over the table would join its cluster in bl/warp.py); two
# cans light the walkway between its south chairs and the pantry wall.
# Eighth round: the island is 7'-0" x 4'-0" on the sheet's place, so the east aisle is 3'-6" wide (built
# x 33.808-37.308) and its can stands on the aisle's centre line. The aisle's second can (36.4, 26.4) is gone
# from the list: the skylight revision has removed it since the first round (it stood in the shaft over the
# sink run), and beside the 1'-10" skylight of this round it would stand on the shaft's west edge. The north
# can over the sink run (39.45, 24.1) was removed by that revision too; beside the narrower well (built
# x 35.73-37.80, z 23.56-27.64) it would stand 4in off the well's east edge, so it moved 0.94 ft north, as far
# beyond the well's north end (0.67 ft) as its twin stands beyond the south end (0.64 ft).
# v7 final: the well moved east over the sink (revision_spec.KITCHEN_SKY; its lining is x 36.56-38.63,
# z 23.56-27.64 on the built plan), over the two sink-run cans' column (built x 38.19; they stood 0.67 / 0.64 ft
# beyond the lining's ends). The cans of the east side now stand on ONE line through the living room, the open
# strip and the kitchen: the living room's east column (bl/zones/living.SOFA_CANS, x 37.980 on the built plan,
# 1.33 ft off the east wall's face), at the living room's three rows, on the open strip's row (below) and one
# beyond each end of the kitchen's well, the same distance from it: the south one on the south counter's row
# (z 29.218 built), the north one on that row's mirror image about the well's centre (z 21.982), each 1.58 ft from
# the lining (1.41 ft from the can's trim). The east aisle's can moved 0.37 ft north onto the north one's row (it
# stood at 22.6 = z 22.347 built). The south-east counter's can (38.6, 29.55) and the sink run's south can
# (39.45, 28.6) became the one south can: they would stand 0.7 ft apart. Along the column the cans are 4.55,
# 4.55, 4.17, 4.58 ft apart, then 7.24 ft across the well. The line passes 0.38 ft east of the well's centre line
# (the well is 1.83 ft wide; the living room's column was laid out about the living room's well).
_AISLE_E_X = (kitchen.ISLAND[1] + kitchen.CT_FRONT_E) / 2
_EAST_COL_X = kitchen._px(RS.LIVING_SKY[0] + RS.LIVING_SKY[1] - kitchen.R.X_REAR(34.2))   # v7 final: living.SOFA_CANS' x
#                                                                 (the third column's mirror image about the living
#                                                                 room's well), carried back to the concept plan: 39.231
_ROW_S_Z = 29.55                                                 # the south counter's row
_ROW_N_Z = kitchen._pz(RS.KITCHEN_SKY[2] + RS.KITCHEN_SKY[3] - kitchen.R.Z_RIGHT(_ROW_S_Z))   # v7 final: its mirror image
#                                                                 about the well's centre z 25.600, concept 22.231
CANS_KITCHEN = [
    (24.14, 27.5), (26.89, 27.5),          # walkway hall -> kitchen: centred on the fridge and on the ovens
    (_AISLE_E_X, _ROW_N_Z),                # east aisle (island <-> sink run), north of the skylight
    (30.0, _ROW_S_Z), (32.8, _ROW_S_Z),    # south counter
    (_EAST_COL_X, _ROW_N_Z), (_EAST_COL_X, _ROW_S_Z),   # v7 final: the east column, one beyond each end of the well
]
CANS_DINING = [(26.2, 17.6), (30.2, 17.6)]   # x matches the living zone's can columns
# Open strip without a dining set: the living zone's can columns (x 26.2 / 30.2 / 34.2) carried one
# row south, plus a can on the living zone's wall-wash column (x 38.45) that accents the olive tree.
# (the olive's can stands 0.92 ft north of the planter's centre, as before the tree moved with the run's end)
# v7 repair: the tree moved to the pier north of W07 (kitchen_dining_olive.CENTER), under the living zone's own
# sofa-side can; this can stays where it has been, over the strip in front of W07 (0.92 ft north of the centre of
# the planter's old place 0.26 ft off the run's end).
# v7 final: that can is the fourth of this row now, on the living room's east column (_EAST_COL_X): the living
# room's 4 x 3 field of cans runs on one row south as 4 x 4. It stood alone at (37.230, 19.074) on the built plan,
# 0.75 ft west of the column the repair moved and 1.67 ft south of this row; at (37.980, 17.404) it is 1.34 ft
# south of W07's north jamb and 1.33 ft off the east wall, over the strip in front of that window.
CANS_OPEN = [(26.2, 17.6), (30.2, 17.6), (34.2, 17.6), (_EAST_COL_X, 17.6)]

CAMERAS = ('K0', 'D0', 'H2', 'L2', 'H3')

# The open strip (z 14.5-20.8) is only ~6.3 ft deep: a dining set there leaves ~1.1 ft between its
# chairs and the island stools (the brief requires >= 36in, and layout_revision.kitchen_island keeps
# the island's north side open). Default: no dining set; a low walnut sideboard under W07 instead
# (kitchen_dining_console.py). Set INCLUDE_DINING = True to build the 42in round set + chandelier.
# Default styling is a single olive tree by the window (the sideboard read as a stray cabinet beside
# the run end and crowded the east wall).
INCLUDE_DINING = False
INCLUDE_CONSOLE = False
# A rectangular table in line with the island and no stools at the island (architect's plan). The
# plan draws it running toward the living room; the owner moved it to the island's west end
# (2026-11-20): kitchen_dining_dining.build_rect().
DINING_RECT = True
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
    out['sideboard_to_east_run_end_ft'] = round(kitchen.RUN_E0 - z1, 2)
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
    out['planter_to_east_run_end_ft'] = round(kitchen.RUN_E0 - z1, 2)
    out['planter_to_living_ledge_end_ft'] = round(z0 - 16.4, 2)
    out['planter_west_of_counter_front_ft'] = round(kitchen.CT_FRONT_E - x0, 2)   # >0: pokes into the aisle line
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


# Island pendants (x, z) over the island's centre line, at the quarter points of its 7'-0" (1'-9" either
# side of the centre on the built plan), glass rim 3'-2" above the 36in worktop.
_ISL_C = ((kitchen.ISLAND[0] + kitchen.ISLAND[1]) / 2, (kitchen.ISLAND[2] + kitchen.ISLAND[3]) / 2)
PENDANT_DX = kitchen._px(kitchen.PLAN_ISLAND[0] + 0.75 * kitchen.PLAN_ISLAND_L) - _ISL_C[0]      # concept feet
PENDANTS = ((_ISL_C[0] - PENDANT_DX, _ISL_C[1]), (_ISL_C[0] + PENDANT_DX, _ISL_C[1]))
PENDANT_BOTTOM = 6.15
# Persian runner in the work aisle between the island and the cooktop run (8 ft x 2'-6"), on the centre line
# of the 4'-0" aisle.
_AISLE_S_Z = (kitchen.ISLAND[3] + kitchen.CT_FRONT_S) / 2
RUNNER = (28.5, 36.5, _AISLE_S_Z - 1.25, _AISLE_S_Z + 1.25)


def _pendants_and_runner(ctx, g):
    lc = g.sub('kd_lights')
    col = g.sub('kd pendant')
    for i, (x, z) in enumerate(PENDANTS):
        kd_lights.bell_pendant(g, f'kd island pendant {i}', x, z, PENDANT_BOTTOM, col, lc)
    x0, x1, z0, z1 = RUNNER
    L, W = (x1 - x0) * 12, (z1 - z0) * 12
    rug = g.box('kd aisle runner', x0, x1, 0.001, 0.034, z0, z1, kd_mats.rug_persian(L, W), coll=g.sub('kd decor'))
    g.bevel_mod(rug, 0.01, 2)


def build(ctx):
    t0 = time.time()
    g = Geo(ctx)
    res = {}
    kitchen.STOOLS = not DINING_RECT
    res['kitchen'] = kitchen.build(ctx, g)
    res['window'] = window.build(ctx, g)
    _pendants_and_runner(ctx, g)
    if DINING_RECT:
        res['dining'] = dining.build_rect(ctx, g)
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
