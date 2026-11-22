#!/usr/bin/env python3
"""Record the owner's design changes (bl/revisions.py) in the web tour's data.

  python3 tools/render/apply_revisions_web.py

Updates the measurements (opening list and room notes used by the Dimensions sheet) and notes the changes
in the scene's design_revision. Reads and writes tools/render/data/measurements.json and scene.json through
tools/web/sitedata.py (no index.html). Run it after apply_relayout.py, which resets both files to the
relaid concept data. Idempotent: running it again rewrites the same values.

Laundry closet (fourth round, moved by the owner in the fifth; all numbers from bl/revision_spec.py): the closet
is carved out of Bedroom 4's north-east corner and opens east onto the foyer.
  * measurements.json: room M13 (the clear inside), door D17 (a pair of leaves), and Bedroom 4 (M07), which keeps
    its overall size and loses the closet and its two walls from its area (an L now);
  * scene.objects: the host wall (Bedroom 4's east wall north of the bedroom door, an existing object) is shortened
    IN PLACE to its part south of the opening, which is what leaves the door gap in the plan drawing; the closet's
    wall boxes (west and south walls, the return north of the opening, the door header) and its two open leaves
    are APPENDED. Existing objects keep their index, which bake_web.py's `scene_index` relies on; a re-run updates
    the appended ones in place by name;
  * scene.audit rows, the change lists `design_revision.owner_changes*` (the fifth round, and the fourth marked as
    superseded), `tour.highlights` (the reel, with the sweep facing the closet) and, in
    tools/render/data/design.json, the Design view `LC`. design.json is hand-edited and not rebuilt by
    apply_relayout.py, so an existing `LC` view is left as it is; the tool only prints a note when a view still
    carries a sentence of a superseded layout (SUPERSEDED).

The kitchen stop K0 moves to the west end of the work aisle, clear of the dining chairs that now stand where the
concept had it (NODE_MOVES); place_sweeps.py keeps a stop where the scene has it. The sweep that faces the closet
is `LC` (place_sweeps.py); it joins the tour when apply_sweeps.py runs, which is the next step of the sequence
  apply_relayout.py -> apply_revisions_web.py -> apply_sweeps.py -> extract_scene.py -> tools/web/dimension_plan.py

Primary suite and the Bedroom 3 bathroom's shower window (sixth round; all numbers from bl/revision_spec.py SUITE_*,
BATH_*, PRIMARY_BATH_*, BED3_BATH_WIN_*): the 8 ft zone between the primary bedroom and the primary bath, one open
dressing area until the fifth round, is divided as on the architect's sheet.
  * measurements.json: room M05 becomes the walk-in closet (it keeps its tag), the vestibule is the new room M14;
    door D18 is the closet's pocket door; D10 (bedroom / vestibule), D09 (suite entry, a sliding panel on the hall
    side) and D08 (bath door) get their new extents; W13 and the skylight W20 follow BATH_WIN_Z and
    PRIMARY_BATH_SKY, W11 its new sill and head; notes of the primary bedroom, the primary bath and the Bedroom 3
    bathroom;
  * scene.objects, IN PLACE (index and name stay; reshape() refuses an object that is not where the spec has it):
    the wall between bedroom and closet and the header beside it, the three pieces of the suite entry wall, the
    three pieces of the bath's north wall around D08, the bath's west wall around W13, the wall below and above
    W11 with its frame and pane, and the two old door leaves, which take the place of their successors (the suite
    entry's hinged leaf becomes the sliding panel, the bath door's leaf moves with its door);
  * scene.objects, APPENDED (by name, updated in place on a re-run): the three pieces of the closet's new east
    wall and the pocket door's leaf;
  * tour stops S0 and C0 are named after the two rooms; the change list `owner_changes_6`, and the entries of
    earlier rounds that the round overtakes; `layout_revision` entries of the concept's open dressing area and
    bath layout are marked as superseded. The Design view A0 is hand-edited in design.json (SUPERSEDED reports
    words of the earlier bath).

Seventh round (2026-11-21): the refrigerator visible beside the microwave, every window white with grid lines, the
primary bath's walls white, the fireplace sealed with the sofa on its wall and the television opposite, the daylight
for a yard that faces north. No wall and no opening moves, so every size of the schedule stays; the round is texts.
  * measurements.json: the `type` text of every window and glazed door (W01..W15, W17 and the garden door D14; not
    the skylights) says what it is and adds the white frame and the grid, as lites wide x high per sash from
    WINDOW_GRIDS. The kitchen window W08 loses the concept's "segmental arch" (the build has made it flat-headed
    since the first restyle). The primary bath's note (M03) names its walls. A window without a text stops the tool.
  * WINDOW_GRIDS repeats what bl/revisions.white_windows lays out on the BUILT model (it divides each sash by the
    rule of revision_spec.WINDOW_LITE and prints the result as `grids` on the build log's `revisions:` line), because
    the rule needs the built frame members. `--check-grids BUILD_LOG` compares the table with such a log and writes
    nothing; run it after the final build.
  * scene.json: the change list `owner_changes_7` and the entries of earlier rounds that the round overtakes. The
    concept's fireplace (brick mass, mantel, hearth, logs) is still in scene.objects, as is all the concept's
    furniture: an object may not be removed (indices are fixed) and nothing on the web side draws either. The tool
    checks that at every run (fireplace_objects) and stops if one of them is in a group the plan or the page uses.
  * design.json is hand-edited (views front, B3, K0, A0); SUPERSEDED reports words of the earlier windows, kitchen,
    bath and living room.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'web'))
import sitedata  # noqa: E402
from bl import revision_spec as RV  # noqa: E402

# the dining table's size is the kitchen zone's (bl/zones/kitchen_dining_dining.py RECT_LEN x RECT_W, six chairs)
DINING_TABLE = '6\'-0" x 2\'-9"'
CHANGES = [
    'Bedroom 4 (plan: office): flat 8 ft ceiling instead of the vault',
    'Front bedroom bay (tour: Bedroom 3, plan: Bedroom #2): glazed down to the floor; window seat removed',
    'Foyer: two skylights on the entry roof\'s east slope (hall section and vaulted entry)',
    'Primary bedroom: the 7 ft rear window becomes a two-panel sliding door to the garden (landing outside)',
    'Bedroom 2 (next to the primary): rear window runs to the ceiling (sill 2\'-0" since the third round)',
    'Primary bathroom: tall west window in clear glass, sill 2\'-0" since the third round (an evergreen screen in the '
    'fenced side yard outside). It stood between the vanity and the shower of the earlier layout; the sixth round '
    'moves it to the architect\'s position and widens it to 3\'-0"',
    'Kitchen skylight: 3\'-6" x 4\'-0" on the continuous east roof plane over the sink / dishwasher '
    '(the concept unit straddled the garage-gable ridge)',
    'Dining: table in line with the island, no island stools (warm oak under a brass lantern since the third round; '
    f'moved to the island\'s west end, {DINING_TABLE} for six, in the fifth round)',
]
CHANGES_2 = [
    'Primary bathroom: a 2\'-0" x 2\'-6" skylight over the shower (in the sixth round it moves with the shower to the '
    'room\'s north-west corner)',
    'The foyer-side wall of Bedroom 4 (office) and Bedroom 3 lines up with the shared bath\'s east wall: both '
    'rooms and the closets between them are 1\'-2 3/4" wider; foyer and covered porch 5\'-9 1/4" wide; '
    'foyer 18\'-6" long as on the plan; the 3\'-0" front door stays centred',
    'Rear landing outside the living room sized as on the plan (3\'-0" deep, garden door to x 38\'-3")',
]
CHANGES_3 = [
    'Bedroom 2 rear window and the primary bathroom window: a 2\'-0" sill instead of glass to the floor (heads stay '
    'at the 8 ft ceiling)',
    'Bedroom 4: the bed is turned across the room, headboard on the north wall, so the room\'s length stays open',
    'Kitchen, primary bathroom, shared bathroom and garage door restyled from the owner\'s style images (styles/); '
    'the primary bathroom\'s finishes of this round (green shower tile, patterned floor) are superseded by the sixth '
    'round, the oak trough vanity stays; the kitchen\'s black steel grid window and its refrigerator behind cabinet '
    'panels are superseded by the seventh round (a white grid window, a visible stainless-steel refrigerator)',
]
CHANGES_4 = [
    'Laundry closet with a stacked front-load washer and dryer behind a 2\'-6" x 6\'-8" door opening. It was first '
    'built in the kitchen\'s south-west corner, where the architect\'s sheet SKA002 draws "W / D": superseded by the '
    'fifth round, which moves it to Bedroom 4',
    'Kitchen south wall re-planned around that closet (closet, refrigerator, wall ovens, a short counter, the '
    'cooktop): superseded by the fifth round, the wall is back to its third-round layout',
]
LIVING_W = 39.195 - 22.528      # relayout.X_REAR: living room clear width, the plan's 16'-8"
GARAGE_W, GARAGE_D = 39.195 - 21.578, 52.335 - 31.418   # relayout.X_GARAGE / Z_RIGHT: the plan's 17'-7" x 20'-11"


# H1 stands in the plan's foyer (z 28.7 .. 47.2); H2, north of it between the shared bath and the kitchen,
# is the hall. S0 and C0 are the stops of the primary suite's vestibule and walk-in closet (sixth round; the concept
# called them "Open primary dressing area" and "Primary dressing storage"). place_sweeps.py gives a new sweep the
# label of the nearest of these stops.
NODE_NAMES = {'H1': 'Foyer', 'H2': 'Hall', 'S0': 'Primary vestibule', 'C0': 'Walk-in closet'}

# ---------------------------------------------------------------------------------------------------------------------
# The laundry closet in Bedroom 4's north-east corner (bl/revision_spec.py LAUNDRY_*; Blender side:
# bl/revisions.laundry_closet). Fourth round, moved here from the kitchen's south-west corner in the fifth.
LAUNDRY_ROOM, LAUNDRY_DOOR, LAUNDRY_VIEW = 'M13', 'D17', 'LC'
LAUNDRY_NODE = 'LC'             # the sweep facing the closet's doors (place_sweeps.py LAUNDRY['id'])
BEDROOM_4, BEDROOM_4_CLOSET = 'M07', 'M12'
# what the existing wall and door-leaf boxes of the scene look like (painted partition, painted flush door)
WALL_LOOK = {'color': '#f8f6f0', 'group': 'walls'}
LEAF_LOOK = {'color': '#eeece6', 'group': 'door'}
BOX_LOOK = {'shape': 'box', 'alpha': 1, 'collision': True, 'material': 'paint', 'roughness': 0.86}
HOST_TOL = 0.01                 # ft: how far the scene's host wall may be from the spec before the cut is refused
# The concept's kitchen stop (25.63, 26.00) stands 0.4 ft from the south chairs of the dining table since the fifth
# round (the set occupies x 21.43..27.43, z 20.80..25.67: bl/zones/kitchen_dining_dining.py). The stop moves to the
# west end of the work aisle between the island and the cooktop counter, on the runner just east of the table:
# 1.5 ft from the nearest chair, 2.0 ft from the oven tower's end panel, 1.9 ft from the counter (rays on the built
# model), which place_sweeps.py accepts as it is (>= 1.2 ft). Its view direction, east along the aisle, is kept: the
# look point travels with it.
NODE_MOVES = {'K0': (27.6, 26.9)}
# the highlight reel: the old page's room stops (tools/web/build_site_data.py HIGHLIGHTS) plus the laundry sweep,
# after Bedroom 4, which the closet stands next to
HIGHLIGHTS = ['E0', 'L8', 'D0', 'K0', 'P0', 'B2', 'B3', 'B4', LAUNDRY_NODE, 'A0', 'A1', 'A3', 'S0', 'C0', 'C3', 'G0']
# L8 (seventh round): the living room card opens on the television wall, the rear glass and the sofa in one view
# design.json is edited by hand: words of a layout the owner has replaced, reported when a view still has them
# (the kitchen-corner laundry closet and the small dining table of the fourth round; the primary bath and the open
# dressing area as they were until the fifth; black window frames without grids, the panelled refrigerator beside two
# wall ovens, the primary bath's wainscot, plaster and cream tile, and the fireplace as they were until the sixth)
SUPERSEDED = ('kitchen\'s south-west corner', 'behind one door', 'table for four',
              'Sage tile', 'sage-green', 'encaustic', 'between the vanity and the shower', 'dressing area',
              'black frame', 'black grid', 'large clear panes', 'panelled fridge', 'wall ovens',
              'wainscot', 'cream plaster above', 'cream tile', 'cream ceiling', 'fireplace', 'hearth')

# ---------------------------------------------------------------------------------------------------------------------
# Sixth round (2026-11-20): the primary suite as the architect's sheet divides it, and the taller shower window of the
# Bedroom 3 bathroom (bl/revision_spec.py; Blender side: bl/revisions.suite_rooms, bath_door, bath_window,
# primary_bath_skylight, bedroom3_bath_window).
PRIMARY_BEDROOM, PRIMARY_BATH, BEDROOM_3_BATH = 'M01', 'M03', 'M09'
SUITE_CLOSET_ROOM = 'M05'           # the walk-in closet keeps the tag of the open dressing area it replaces
SUITE_VESTIBULE_ROOM = 'M14'        # new: the next free M tag
SUITE_CLOSET_DOOR = 'D18'           # new: the next free D tag
BATH_DOOR, SUITE_ENTRY, BED_OPENING = 'D08', 'D09', 'D10'
SUITE_CLOSET_NODE, SUITE_VESTIBULE_NODE = 'C0', 'S0'
SUITE_CLOSET_NAMES = ('Primary dressing + storage', 'Walk-in closet')   # room M05 before / after the round
# existing SCENE objects the round reshapes in place, besides RV.suite_existing_walls(): the bath's north wall around
# D08 (west of the door, header, east of it), the bath's west wall around W13, the wall below / above W11 and its
# frame, and the two old leaves
BATH_NORTH_WALLS = ('Ensuite north / closet south', 'Ensuite entry', 'Shared bathroom north / walk-in south')
BATH_WEST_WALLS = ('Primary bathroom west wall — north solid', 'Primary bathroom west wall — below privacy window',
                   'Primary bathroom west wall — south solid')
BED3_BATH_WIN_WALLS = ('Ensuite privacy window sill wall', 'Ensuite privacy window head wall')
BED3_BATH_WIN_PARTS = ('Ensuite privacy window frame', 'Ensuite privacy window mullion',
                       'Ensuite privacy window glazing')
BED3_BATH_WIN_RAIL = 0.1            # bl/revisions.bedroom3_bath_window: this much above the sill / below the head keeps
#                                     its section when the frame is stretched onto the new opening
BED3_BATH_WIN_GLASS_IN = 0.01       # ... and the pane ends this far inside the opening's jambs
SUITE_ENTRY_OLD_LEAF = 'Primary suite entrance door — south hinged, open inward'
BATH_DOOR_OLD_LEAF = 'Primary bathroom privacy door — shown open'
FACES = ('x0', 'x1', 'y0', 'y1', 'z0', 'z1')
SAME = 1e-4                         # ft: a face this near its new place has been moved already (a re-run)

# ---------------------------------------------------------------------------------------------------------------------
# Seventh round (2026-11-21): white windows with grid lines (bl/revision_spec.py WINDOW_*; Blender side:
# bl/revisions.white_windows), the visible refrigerator beside the microwave (bl/zones/kitchen_dining_kitchen.py), the
# primary bath's white walls (bl/zones/baths_primary.py), the living room without its fireplace (bl/zones/living.py)
# and the sky turned to the sun (bl/lighting.py). Nothing in it moves a wall or an opening.
#
# The grid of each window and glazed door: (lites wide, lites high) of each sash, in the order of the build log (along
# the wall, the lower tier before the transom). It repeats what white_windows lays out on the built model and prints
# as `grids` on the build log's `revisions:` line, where the bay's three sashes are W09a, W09b, W09c;
# `--check-grids BUILD_LOG` compares the two.
WINDOW_GRIDS = {
    'W01': ((3, 5), (3, 5)), 'W02': ((2, 4), (2, 4)), 'W03': ((4, 5),), 'W04': ((4, 5),),
    'W05': ((1, 3), (1, 3)), 'W06': ((1, 3), (1, 3)), 'W07': ((2, 3), (2, 3)), 'W08': ((2, 4), (2, 4), (2, 4)),
    'W09': ((2, 5), (3, 5), (2, 5)), 'W10': ((2, 3), (2, 3)), 'W11': ((1, 3), (1, 3)), 'W12': ((2, 3), (2, 3)),
    'W13': ((1, 3), (1, 3), (1, 1), (1, 1)), 'W14': ((2, 1), (2, 1)), 'W15': ((1, 3), (1, 3)), 'W17': ((3, 2),),
    'D14': ((2, 5),),
}
GARDEN_DOOR = 'D14'                 # the living room's glazed door to the deck: white with a grid, like the windows.
#                                     Its `type` keeps the word "Glazed": white_windows finds the door by it.
WINDOW_FINISH = 'white frame, white grid bars'
# The primary bath's walls (a sentence of the room's note): the board wainscot, its cap rail and the plaster are gone.
PRIMARY_BATH_WALLS = ('Walls: natural stacked stone on the vanity wall (south); every other wall plain white from the '
                      'floor to the ceiling above a white tile base; matte white tile in the shower; white ceiling.')
# The concept's fireplace on the living room's east wall (names in scene.objects), and the groups of scene.objects
# that the web side reads: tools/web/dimension_plan.py (walls, door leaves, foundations) and
# tools/web/build_site_data.py (walls, foundations).
FIREPLACE = r'fireplace|hearth|mantel|painted brick'
DRAWN_GROUPS = ('walls', 'door', 'garageDoor', 'base')


def ft(v):
    """Feet-inches to the nearest 1/8 inch (tools/web/dimension_plan.py ft())."""
    n = round(v * 96)
    return '%d′%d%s″' % (n // 96, n % 96 // 8, ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][n % 8])


def fi(v):
    """Feet-inches as the change lists write them, to the nearest 1/8 inch: 2'-10", 3'-4 3/8"."""
    n = round(v * 96)
    return '%d\'-%d%s"' % (n // 96, n % 96 // 8, ['', ' 1/8', ' 1/4', ' 3/8', ' 1/2', ' 5/8', ' 3/4', ' 7/8'][n % 8])


def size_labels(meas):
    """Tour-stop size captions from the Dimensions sheet's clear room sizes (so they follow the plan)."""
    rooms = {r['id']: r for r in meas['rooms']}

    def wd(mid, extra=''):
        r = rooms[mid]
        return f"{ft(r['width_ft'])} × {ft(r['depth_ft'])}{extra} · {r.get('basis', 'P')}"
    f = rooms['M11']
    return {
        'P0': wd('M01'), 'B2': wd('M02'), 'A0': wd('M03') + ' · skylight over the shower', 'A1': wd('M04'),
        SUITE_CLOSET_NODE: wd(SUITE_CLOSET_ROOM), SUITE_VESTIBULE_NODE: wd(SUITE_VESTIBULE_ROOM),
        'B4': wd(BEDROOM_4, ' overall, L-shaped + separate reach-in closet'), 'B3': wd('M08'),
        'A3': wd('M09'), 'C3': wd('M10'), 'L0': f'{ft(LIVING_W)} living-room width · R',
        'E0': f"3′0″ entrance · {ft(f['width_ft'])} × {ft(f['depth_ft'])} foyer · P",
        'K0': '3′6″ × 4′ skylight · dining table at the island\'s west end',
        'G0': f'{ft(GARAGE_W)} × {ft(GARAGE_D)} · R',
    }


def r4(v):
    return round(float(v), 4)


def inches(feet):
    """Inches to the nearest quarter, as '27', '30¼'."""
    n = round(feet * 48)
    return '%d%s' % (n // 4, ['', '¼', '½', '¾'][n % 4])


def upsert(rows, entry, key='id'):
    """Replace the row of `rows` with the same `key` in place, else append; returns the row's index."""
    for i, r in enumerate(rows):
        if r.get(key) == entry[key]:
            rows[i] = entry
            return i
    rows.append(entry)
    return len(rows) - 1


def laundry_room():
    """Room M13: the closet's clear inside. Its width is the north-south size, across the doors, and its depth the
    east-west size, from the door wall to the back wall (the owner's 2'-10" x 3'-0"); bounds_ft stays x0 x1 z0 z1."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    w, d = z1 - z0, x1 - x0
    uw, ud, uh = (inches(v) for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {'id': LAUNDRY_ROOM, 'kind': 'room', 'basis': 'P', 'name': 'Laundry closet',
            'bounds_ft': [r4(x0), r4(x1), r4(z0), r4(z1)], 'width_ft': r4(w), 'depth_ft': r4(d),
            'area_sqft': round(w * d, 2),
            'note': f'Clear interior size: {ft(w)} wide (north to south, across the doors) and {ft(d)} deep (door wall '
                    'to back wall). Carved out of Bedroom 4\'s north-east corner; it opens east onto the foyer through '
                    f'the doors {LAUNDRY_DOOR}. Stacked front-load washer and dryer, each {uw} × {ud} × {uh} in (width '
                    f'× depth × height), facing the foyer, under the {RV.LAUNDRY_CEILING:g} ft ceiling.',
            'node': LAUNDRY_NODE}


def bedroom_4(room):
    """Bedroom 4 (M07) after the cut, in place: the overall clear size stays; the area leaves out the corner the
    closet takes with its two new walls (east-west from the closet's west wall face to the room's east wall,
    north-south from the room's north wall to the closet's south wall face). Returns that corner's size."""
    bx0, bx1, bz0, bz1 = room['bounds_ft']
    cut_w, cut_d = bx1 - RV.LAUNDRY_OUTER[0], RV.LAUNDRY_OUTER[3] - bz0
    if not (0 < cut_w < bx1 - bx0 and 0 < cut_d < bz1 - bz0):
        raise SystemExit('the laundry closet (bl/revision_spec.py LAUNDRY_OUTER) does not lie in the north-east corner '
                         'of %s %s' % (room['id'], room['bounds_ft']))
    room['area_sqft'] = round(room['width_ft'] * room['depth_ft'] - cut_w * cut_d, 2)
    room['note'] = ('Clear interior size overall; excludes walls. L-shaped: the laundry closet is taken out of the '
                    f'north-east corner, and the area leaves out {ft(cut_w)} × {ft(cut_d)} for the closet and its two '
                    'walls. Flat 8 ft ceiling (no vault).')
    return cut_w, cut_d


def laundry_door():
    """Door D17 in the host wall (axis 'z': the opening runs along z on the wall line x = c)."""
    d0, d1 = RV.LAUNDRY_DOOR_Z
    north, south = RV.LAUNDRY_DOOR_HINGES
    return {'id': LAUNDRY_DOOR, 'name': 'Laundry closet doors (pair)', 'axis': RV.LAUNDRY_DOOR_AXIS,
            'c': r4(RV.LAUNDRY_DOOR_C), 'start': r4(d0), 'end': r4(d1), 'width': r4(d1 - d0),
            'height': RV.LAUNDRY_DOOR_HEAD, 'sill': 0, 'head': RV.LAUNDRY_DOOR_HEAD,
            'type': f'Pair of hinged leaves, one on the {north} jamb and one on the {south} jamb, opening '
                    f'{RV.LAUNDRY_DOOR_SWING} into the foyer; shown open {RV.LAUNDRY_DOOR_OPEN_DEG:g} degrees',
            'node': LAUNDRY_NODE, 'kind': 'door', 'basis': 'P'}


def laundry_objects():
    """SCENE boxes to append: the closet's wall pieces (the header over the doors included) and its two open leaves."""
    out = []
    for name, x0, x1, y0, y1, z0, z1 in RV.laundry_walls():
        out.append(dict({'name': name, 'p': [r4((x0 + x1) / 2), r4((y0 + y1) / 2), r4((z0 + z1) / 2)],
                         's': [r4(x1 - x0), r4(y1 - y0), r4(z1 - z0)]}, **WALL_LOOK, rot=0, **BOX_LOOK))
    for leaf in RV.laundry_leaves():    # at run time: the leaf boxes follow the hinge geometry of the spec
        out.append(dict({'name': leaf['name'], 'p': [r4(v) for v in leaf['center']], 's': [r4(v) for v in leaf['size']]},
                        **LEAF_LOOK, rot=round(leaf['rot'], 6), **BOX_LOOK))
    return out


def cut_host_wall(objs):
    """The door opening: shorten the host wall, an existing SCENE object (Bedroom 4's east wall north of the bedroom
    door), to the part the opening leaves of it, from the south jamb to the bedroom door. Only its z extent changes;
    index, name, thickness and look stay. The return north of the opening and the header are among the appended
    boxes. Refuses when the object is not where the spec expects the wall. Returns the object's index."""
    name, x0, x1, _, _, z0, z1 = RV.laundry_host_wall()
    found = [i for i, o in enumerate(objs) if o.get('name') == name and o.get('group') == 'walls']
    if len(found) != 1 or RV.LAUNDRY_DOOR_AXIS != 'z':
        raise SystemExit('laundry closet: expected one wall object named %r running along z, found %d'
                         % (name, len(found)))
    o = objs[found[0]]
    oz0, oz1 = o['p'][2] - o['s'][2] / 2, o['p'][2] + o['s'][2] / 2
    uncut = abs(oz0 - RV.LAUNDRY_HOST_WALL_Z[0]) <= HOST_TOL      # as apply_relayout.py leaves it
    if (abs(o['p'][0] - (x0 + x1) / 2) > HOST_TOL or abs(oz1 - z1) > HOST_TOL
            or not (uncut or abs(oz0 - z0) <= HOST_TOL) or abs(o.get('rot') or 0) > 1e-6):
        raise SystemExit('laundry closet: wall %r is at x %.4f, z %.4f..%.4f in the scene; bl/revision_spec.py expects '
                         'x %.4f, z %.4f..%.4f' % (name, o['p'][0], oz0, oz1, (x0 + x1) / 2,
                                                   RV.LAUNDRY_HOST_WALL_Z[0], z1))
    o['p'] = [o['p'][0], o['p'][1], r4((z0 + z1) / 2)]
    o['s'] = [o['s'][0], o['s'][1], r4(z1 - z0)]
    return found[0]


def changes_5(bed4, cut):
    """The fifth round (2026-11-20), with the closet's and Bedroom 4's numbers from the spec and the schedule."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    return [
        'Laundry closet moved out of the kitchen: it is carved out of Bedroom 4\'s north-east corner and opens east '
        'onto the foyer, on the foyer\'s west side next to the bedroom door. '
        f'{fi(z1 - z0)} wide x {fi(x1 - x0)} deep clear, the stacked front-load washer and dryer behind a pair of doors '
        f'in a {fi(RV.LAUNDRY_DOOR_W)} x {fi(RV.LAUNDRY_DOOR_HEAD)} opening, shown open',
        f'Bedroom 4 is L-shaped after the cut: {fi(bed4["width_ft"])} x {fi(bed4["depth_ft"])} overall as before, less '
        f'{fi(cut[0])} x {fi(cut[1])} for the closet and its two walls ({bed4["area_sqft"]:.1f} sq ft); the desk stands '
        'in the niche between the nightstand and the closet\'s back wall',
        'Dining table moved from the family-room side of the island to the island\'s west end, the shared-bathroom '
        f'side, in line with the island: {DINING_TABLE}, three chairs on each long side, none at the ends, no rug; the '
        'floor between the island and the family room is open',
        'Kitchen south wall back to its third-round layout: refrigerator and oven tower at the west (hall) end, then '
        'the counter under three glass-front uppers and the cooktop under the hood (until the seventh round the '
        'refrigerator stood behind cabinet panels and the tower held two wall ovens)',
    ]


# ------------------------------------------------------------------------------------------- sixth round: SCENE objects
def box_of(o):
    """(x0, x1, y0, y1, z0, z1) of a SCENE box that is not turned."""
    p, s = o['p'], o['s']
    return (p[0] - s[0] / 2, p[0] + s[0] / 2, p[1] - s[1] / 2, p[1] + s[1] / 2, p[2] - s[2] / 2, p[2] + s[2] / 2)


def named(objs, name, group):
    """Indices of the SCENE boxes of `group` called `name`."""
    return [i for i, o in enumerate(objs)
            if o.get('name') == name and o.get('group') == group and o.get('shape') == 'box']


def reshape(objs, name, at=None, group='walls', **faces):
    """Move faces of an existing SCENE box IN PLACE: `faces` (x0=..., z1=...) are the faces the round moves, `at` the
    faces the spec says it must already have (within HOST_TOL; else the scene is not the one bl/revision_spec.py
    describes and the change is refused). Index, name and look stay, and so does every axis whose faces are where
    they should be already, so a re-run writes nothing new. Returns the object's index."""
    found = named(objs, name, group)
    if len(found) != 1:
        raise SystemExit('sixth round: expected one %s box named %r in the scene, found %d' % (group, name, len(found)))
    o = objs[found[0]]
    old = dict(zip(FACES, box_of(o)))
    off = ['%s %.4f (spec %.4f)' % (f, old[f], v) for f, v in (at or {}).items() if abs(old[f] - v) > HOST_TOL]
    if off or abs(o.get('rot') or 0) > 1e-6:
        raise SystemExit('sixth round: %r is not where bl/revision_spec.py expects it: %s'
                         % (name, ', '.join(off) or 'it is turned'))
    for k, ax in enumerate('xyz'):
        lo, hi = faces.get(ax + '0', old[ax + '0']), faces.get(ax + '1', old[ax + '1'])
        if abs(lo - old[ax + '0']) < SAME and abs(hi - old[ax + '1']) < SAME:
            continue
        if hi - lo < 0.01:
            raise SystemExit('sixth round: %r would be %.4f ft long along %s' % (name, hi - lo, ax))
        o['p'][k], o['s'][k] = r4((lo + hi) / 2), r4(hi - lo)
    return found[0]


def suite_walls(objs):
    """The walls of the primary suite. Existing pieces are reshaped in place: the wall between bedroom and closet runs
    on to the closet's new east wall and the header over the bedroom opening starts there; the suite entry's wall
    pieces close on the narrower opening; the bath's north wall opens for D08 at its new place. Each piece keeps the
    faces across its thickness and its height, only its ends along the wall move. The closet's new east wall (north
    of the door, the header, the pocket) is appended. Returns (indices reshaped, indices appended)."""
    done, new = [], []
    for name, box in RV.suite_existing_walls().items():
        run = 'x' if box[1] - box[0] >= box[5] - box[4] else 'z'
        full = dict(zip(FACES, box))
        done.append(reshape(objs, name, at={f: v for f, v in full.items() if f[0] != run},
                            **{f: v for f, v in full.items() if f[0] == run}))
    d0, d1 = RV.BATH_DOOR_X
    zn, zs = RV.PRIMARY_BATH_NORTH_WALL_Z
    west, header, east = BATH_NORTH_WALLS
    line = {'z0': zn, 'z1': zs}
    done.append(reshape(objs, west, at=dict(line, y0=0.0), x1=d0))
    done.append(reshape(objs, header, at=dict(line, y0=RV.BATH_DOOR_HEAD), x0=d0, x1=d1))
    done.append(reshape(objs, east, at=dict(line, y0=0.0), x0=d1))
    for name, x0, x1, y0, y1, z0, z1 in RV.suite_closet_walls():
        new.append(upsert(objs, dict({'name': name, 'p': [r4((x0 + x1) / 2), r4((y0 + y1) / 2), r4((z0 + z1) / 2)],
                                      's': [r4(x1 - x0), r4(y1 - y0), r4(z1 - z0)]}, **WALL_LOOK, rot=0, **BOX_LOOK),
                          key='name'))
    return done, new


def move_leaf(objs, name, leaf):
    """An existing door leaf of the scene (group 'door') takes the place of its successor `leaf` (a dict of
    bl/revision_spec.py with `center`, `size` and `rot`), in place: the plan draws every box of that group, so the
    old leaf may not stay where its door was. Returns the object's index."""
    found = named(objs, name, 'door')
    if len(found) != 1:
        raise SystemExit('sixth round: expected one door leaf named %r in the scene, found %d' % (name, len(found)))
    o = objs[found[0]]
    o['p'], o['s'] = [r4(v) for v in leaf['center']], [r4(v) for v in leaf['size']]
    o['rot'] = round(leaf['rot'], 6) or 0
    return found[0]


def suite_leaves(objs):
    """Door leaves: the suite entry's old hinged leaf becomes the sliding panel parked on the hall face, the bath
    door's leaf moves with its door (hinged east, open against the east wall); the closet's pocket leaf is new and
    appended. Returns (indices moved, index appended)."""
    moved = [move_leaf(objs, SUITE_ENTRY_OLD_LEAF, RV.suite_entry_panel()),
             move_leaf(objs, BATH_DOOR_OLD_LEAF, RV.bath_door_leaf())]
    leaf = RV.suite_closet_leaf()
    box = {'name': leaf['name'], 'p': [r4(v) for v in leaf['center']], 's': [r4(v) for v in leaf['size']]}
    new = upsert(objs, dict(box, **LEAF_LOOK, rot=round(leaf['rot'], 6) or 0, **BOX_LOOK), key='name')
    return moved, new


def bath_window_walls(objs):
    """Primary bath west wall around W13 (BATH_WIN_Z): the solid walls north and south of the window end on its new
    jambs and the wall below it, the concept's 5 ft sill wall, becomes the wall below the 2'-0" sill. (The concept's
    header and frame pieces stay as they are: the glass runs to the ceiling, and nothing draws them.)"""
    z0, z1 = RV.BATH_WIN_Z
    north, below, south = BATH_WEST_WALLS
    floor = {'y0': 0.0}
    return [reshape(objs, north, at=floor, z1=z0), reshape(objs, below, at=floor, y1=RV.TALL_SILL, z0=z0, z1=z1),
            reshape(objs, south, at=floor, z0=z1)]


def bed3_bath_window(objs):
    """Bedroom 3 bathroom, shower window W11 (BED3_BATH_WIN_*): the wall below ends at the new sill, the wall above
    starts at the new head, and frame, mullions and pane are stretched onto the new opening as
    bl/revisions.bedroom3_bath_window does it (the rails keep their section; the pane runs into the jamb sections).
    Returns the pane's (width, height)."""
    z0, z1 = RV.BED3_BATH_WIN_Z
    (s, h), (so, ho) = RV.BED3_BATH_WIN_Y, RV.BED3_BATH_WIN_OLD_Y
    line = {'z0': z0, 'z1': z1}
    low, high = BED3_BATH_WIN_WALLS
    reshape(objs, low, at=dict(line, y0=0.0), y1=s)
    reshape(objs, high, at=line, y0=h)
    a, b = so + BED3_BATH_WIN_RAIL, ho - BED3_BATH_WIN_RAIL

    def up(y):          # the concept's height -> the new one: sill and head move, in between the frame stretches
        if y <= a:
            return y + s - so
        if y >= b:
            return y + h - ho
        return s + BED3_BATH_WIN_RAIL + (y - a) * (h - s - 2 * BED3_BATH_WIN_RAIL) / (b - a)
    pane = None
    for o in objs:
        if o.get('name') not in BED3_BATH_WIN_PARTS or o.get('shape') != 'box':
            continue
        _, _, y0, y1, _, _ = box_of(o)
        if y0 >= so - HOST_TOL and y1 <= ho + HOST_TOL:         # still the concept's 5'-0" .. 7'-0" window
            y0, y1 = up(y0), up(y1)
            o['p'][1], o['s'][1] = r4((y0 + y1) / 2), r4(y1 - y0)
        if o.get('group') == 'glass':
            g0, g1 = z0 + BED3_BATH_WIN_GLASS_IN, z1 - BED3_BATH_WIN_GLASS_IN
            o['p'][2], o['s'][2] = r4((g0 + g1) / 2), r4(g1 - g0)
            pane = (o['s'][2], o['s'][1])
    if pane is None:
        raise SystemExit('sixth round: the scene has no pane %r' % BED3_BATH_WIN_PARTS[2])
    return pane


# ------------------------------------------------------------------------------------------- sixth round: the schedule
def room_row(rid, name, clear, node, note):
    """A room of the schedule from its clear rectangle (x0, x1, z0, z1): width along x, depth along z."""
    x0, x1, z0, z1 = clear
    return {'id': rid, 'kind': 'room', 'basis': 'P', 'name': name, 'bounds_ft': [r4(x0), r4(x1), r4(z0), r4(z1)],
            'width_ft': r4(x1 - x0), 'depth_ft': r4(z1 - z0), 'area_sqft': round((x1 - x0) * (z1 - z0), 2),
            'note': note, 'node': node}


def suite_rooms(rooms):
    """Rooms M05 (walk-in closet, in place of the open dressing area) and M14 (vestibule), and the notes of the
    primary bedroom, the primary bath and the Bedroom 3 bathroom. Returns the rows that changed, by id."""
    by_id = {r['id']: r for r in rooms}
    old = by_id.get(SUITE_CLOSET_ROOM)
    if old is None or old['name'] not in SUITE_CLOSET_NAMES:
        raise SystemExit('measurements.json: room %s is %r, expected the primary suite\'s dressing area or walk-in '
                         'closet' % (SUITE_CLOSET_ROOM, old and old['name']))
    taken = by_id.get(SUITE_VESTIBULE_ROOM)
    if taken is not None and taken['name'] != 'Primary vestibule':
        raise SystemExit('measurements.json: room tag %s is taken by %r' % (SUITE_VESTIBULE_ROOM, taken['name']))
    for need in (PRIMARY_BEDROOM, PRIMARY_BATH, BEDROOM_3_BATH):
        if need not in by_id:
            raise SystemExit('measurements.json has no room %s' % need)
    hx0, hx1, hz0, hz1 = RV.SUITE_ATTIC_HATCH
    hatch = ' × '.join(str(round(v * 12)) for v in sorted((hx1 - hx0, hz1 - hz0), reverse=True))
    bx0, bx1 = RV.SUITE_BED_OPENING_X
    sx0, sx1, sz0, sz1 = RV.BATH_SHOWER
    vx0, vx1, _, _ = RV.BATH_VANITY
    (ws, wh), (wz0, wz1) = RV.BED3_BATH_WIN_Y, RV.BED3_BATH_WIN_Z
    door = f'{ft(RV.SUITE_CLOSET_DOOR_W)} × {ft(RV.SUITE_CLOSET_DOOR_HEAD)}'
    closet = room_row(
        SUITE_CLOSET_ROOM, 'Walk-in closet', RV.SUITE_CLOSET_CLEAR, SUITE_CLOSET_NODE,
        'Clear interior size; excludes walls. An enclosed room off the primary suite\'s vestibule, behind the sliding '
        f'pocket door {SUITE_CLOSET_DOOR} ({door}) in its east wall. Hanging rods and shelves on the north, west and '
        'south walls, with a drawer and shelf tower on the west wall; no window; flush ceiling light.')
    vestibule = room_row(
        SUITE_VESTIBULE_ROOM, 'Primary vestibule', RV.SUITE_VESTIBULE_CLEAR, SUITE_VESTIBULE_NODE,
        'Clear interior size; excludes walls. The passage of the primary suite: open to the bedroom over its full '
        f'width ({BED_OPENING}, {ft(bx1 - bx0)}, no door), entered from the hall through {SUITE_ENTRY} in its east '
        f'wall, with the walk-in closet\'s pocket door {SUITE_CLOSET_DOOR} in its west wall and the bathroom door '
        f'{BATH_DOOR} at its south end. Attic access hatch ({hatch} in) in the ceiling.')
    upsert(rooms, closet)
    upsert(rooms, vestibule)
    by_id[PRIMARY_BEDROOM]['note'] = (
        'Clear interior size; excludes walls. King bed with a low headboard on the west wall, centred between the two '
        'west windows (W15 and W14, both kept), with a nightstand under each; the rear sliding door W01 opens to the '
        f'garden. Open to the vestibule at the south-east corner ({BED_OPENING}, {ft(bx1 - bx0)} wide, no door).')
    by_id[PRIMARY_BATH]['note'] = (
        'Clear interior size; excludes walls. Laid out as on the architect\'s sheet: a '
        f'{ft(nominal(sx1 - sx0))} × {ft(nominal(sz1 - sz0))} curbless shower in the north-west corner under the '
        f'skylight W20, the toilet in the south-west corner, a {ft(vx1 - vx0)} double vanity along the south wall, '
        f'the door {BATH_DOOR} at the east end of the north wall and the window W13 on the west wall, its mullion on '
        'the shower\'s glass line. ' + PRIMARY_BATH_WALLS)        # the walls: seventh round
    by_id[BEDROOM_3_BATH]['note'] = (
        f'Clear interior size; excludes walls. The shower window W11 on the west wall is {ft(wz1 - wz0)} wide and runs '
        f'from a {ft(ws)} sill to a {ft(wh)} head ({ft(wh - ws)} tall), in obscured glass with a white frame and '
        'white grid bars.')
    return {r['id']: r for r in (closet, vestibule, by_id[PRIMARY_BEDROOM], by_id[PRIMARY_BATH], by_id[BEDROOM_3_BATH])}


def entry_offset():
    """How far south of the sheet's position the suite entry is built (ft, centre to centre), 0 when it is there."""
    (b0, b1), (s0, s1) = RV.SUITE_ENTRY_Z, RV.SUITE_ENTRY_SHEET_Z
    off = (b0 + b1) / 2 - (s0 + s1) / 2
    return off if abs(off) > 0.05 else 0.0


def suite_doors(doors):
    """Doors D08 (bath), D09 (suite entry), D10 (bedroom / vestibule) at their new extents and the closet's pocket
    door D18 (new)."""
    by_id = {d['id']: d for d in doors}
    for need in (BATH_DOOR, SUITE_ENTRY, BED_OPENING):
        if need not in by_id:
            raise SystemExit('measurements.json has no door %s' % need)
    name = 'Walk-in closet pocket door'
    taken = by_id.get(SUITE_CLOSET_DOOR)
    if taken is not None and taken['name'] != name:
        raise SystemExit('measurements.json: door tag %s is taken by %r' % (SUITE_CLOSET_DOOR, taken['name']))

    def span(d, c, a, b, head, kind):
        d.update(c=r4(c), start=r4(a), end=r4(b), width=r4(b - a), height=head, sill=0, head=head, type=kind)
    d0, d1 = RV.BATH_DOOR_X
    span(by_id[BATH_DOOR], RV.BATH_DOOR_C, d0, d1, RV.BATH_DOOR_HEAD,
         f'Hinged privacy door on the {RV.BATH_DOOR_HINGE} jamb, opening into the bathroom; shown open '
         f'{RV.BATH_DOOR_OPEN_DEG:g} degrees, against the bathroom\'s east wall')
    e0, e1 = RV.SUITE_ENTRY_Z
    off = entry_offset()
    side = {'east': 'hall', 'west': 'vestibule'}[RV.SUITE_ENTRY_PANEL_SIDE]
    parked = 'south' if RV.SUITE_ENTRY_PANEL_OPEN_Z0 > RV.SUITE_ENTRY_PANEL_CLOSED_Z0 else 'north'
    span(by_id[SUITE_ENTRY], RV.SUITE_ENTRY_C, e0, e1, RV.SUITE_ENTRY_HEAD,
         f'Sliding panel on the {side} side of the wall, parked {parked} of the opening; shown open'
         + (f'. The opening stands {ft(abs(off))} {"south" if off > 0 else "north"} of its place on the architect\'s '
            'sheet, where this model has Bedroom 2\'s entry alcove on the hall side' if off else ''))
    b0, b1 = RV.SUITE_BED_OPENING_X
    span(by_id[BED_OPENING], sum(RV.SUITE_NORTH_WALL_Z) / 2, b0, b1, RV.SUITE_BED_OPENING_HEAD,
         'Open connection between the bedroom and the vestibule beneath the retained header; no door')
    c0, c1 = RV.SUITE_CLOSET_DOOR_Z
    pocket = {'id': SUITE_CLOSET_DOOR, 'name': name, 'axis': RV.SUITE_CLOSET_DOOR_AXIS}
    span(pocket, RV.SUITE_CLOSET_DOOR_C, c0, c1, RV.SUITE_CLOSET_DOOR_HEAD,
         f'Sliding pocket door; the leaf slides {RV.SUITE_CLOSET_DOOR_POCKET} into the wall; shown open')
    pocket.update(node=SUITE_CLOSET_NODE, kind='door', basis='P')
    upsert(doors, pocket)
    if by_id[BATH_DOOR]['axis'] != RV.BATH_DOOR_AXIS or by_id[SUITE_ENTRY]['axis'] != RV.SUITE_ENTRY_AXIS \
            or by_id[BED_OPENING]['axis'] != 'x':
        raise SystemExit('measurements.json: doors %s / %s / %s do not run along the walls bl/revision_spec.py puts '
                         'them in' % (BATH_DOOR, SUITE_ENTRY, BED_OPENING))
    return pocket


def nominal(v):
    """Feet to the nearest inch (a nominal size: the shower's rectangle is measured to its glass lines)."""
    return round(v * 12) / 12


def changes_6(rows):
    """The sixth round (2026-11-20) in the owner's terms, with the numbers of the spec and the schedule."""
    closet, vest = rows[SUITE_CLOSET_ROOM], rows[SUITE_VESTIBULE_ROOM]
    (ws, wh), (wso, who), (wz0, wz1) = RV.BED3_BATH_WIN_Y, RV.BED3_BATH_WIN_OLD_Y, RV.BED3_BATH_WIN_Z
    sx0, sx1, sz0, sz1 = RV.BATH_SHOWER
    vx0, vx1, _, _ = RV.BATH_VANITY
    bz0, bz1 = RV.BATH_WIN_Z
    kx0, kx1, kz0, kz1 = RV.PRIMARY_BATH_SKY
    off = entry_offset()
    return [
        'Front bedroom suite bathroom (tour: Bedroom 3 bathroom): the window in the shower is vertically larger, '
        f'from a {fi(ws)} sill to a {fi(wh)} head ({fi(wh - ws)} tall; it was {fi(who - wso)} tall above a {fi(wso)} '
        f'sill). Its {fi(wz1 - wz0)} width and the obscured glass stay (the frame, black in this round, is white with '
        'grid bars since the seventh)',
        'Primary walk-in closet: a small room with a door, as on the last page of sizes.pdf (sheet SKA002). '
        f'{fi(closet["width_ft"])} x {fi(closet["depth_ft"])} clear behind a new wall, entered from the suite\'s '
        f'vestibule through a sliding pocket door ({fi(RV.SUITE_CLOSET_DOOR_W)} x {fi(RV.SUITE_CLOSET_DOOR_HEAD)}, the '
        f'leaf slides {RV.SUITE_CLOSET_DOOR_POCKET} into the wall, shown open), with hanging rods and shelves on three '
        'sides. The open dressing area with its wardrobes is gone',
        f'Primary suite as on the sheet: a vestibule between the closet and the hall, {fi(vest["width_ft"])} x '
        f'{fi(vest["depth_ft"])} clear, open to the bedroom over its full width (no door), with the attic access hatch '
        f'in its ceiling. The suite entry from the hall is a {fi(RV.SUITE_ENTRY_W)} opening with a sliding panel on '
        'the hall side, shown open'
        + (f'; it stands {fi(abs(off))} {"south" if off > 0 else "north"} of its place on the sheet, where this model '
           'has Bedroom 2\'s entry alcove on the hall side' if off else ''),
        'Primary bedroom as on the sheet: king bed on the west wall, centred between the two west windows, with a '
        'nightstand on each side; both west windows are kept (the sheet draws only the north one), and so is the rear '
        'sliding door',
        f'Primary bathroom laid out as on the sheet: a {fi(nominal(sx1 - sx0))} x {fi(nominal(sz1 - sz0))} curbless '
        f'shower in the north-west corner, the toilet in the south-west corner, a {fi(vx1 - vx0)} double vanity along '
        f'the south wall, the door at the east end of the north wall. The west window is at the sheet\'s position, '
        f'{fi(bz1 - bz0)} wide from the {fi(RV.TALL_SILL)} sill to the ceiling, its mullion on the shower\'s glass '
        f'line, and the {fi(kx1 - kx0)} x {fi(kz1 - kz0)} skylight moved with the shower',
        'Primary bathroom in the style of the owner\'s image "primary bathroom wall style" (styles/): natural stacked '
        'stone on the vanity wall, behind the floating oak vanity with its two wooden troughs and the oak-framed '
        'mirrors, under a dark timber beam with enamel lamps; a quiet grey stone floor; brushed nickel fittings. The '
        'green shower tile and the blue patterned floor are gone. The grey-green board wainscot with cream plaster '
        'above it on the other walls and the cream shower tile of this round are superseded by the seventh round '
        '(white walls, white tile)',
    ]


# ------------------------------------------------------------------------------------------------- seventh round
def in8(feet):
    """Inches to the nearest eighth, as the change lists write them: 7/8, 14, 16 1/2."""
    n = round(feet * 96)
    whole, frac = n // 8, ['', '1/8', '1/4', '3/8', '1/2', '5/8', '3/4', '7/8'][n % 8]
    return ' '.join(s for s in (str(whole) if whole or not frac else '', frac) if s)


def lites(cell):
    """One sash's grid in words: '3 lites wide × 5 high'."""
    c, r = cell
    return f'{c} {"lite" if c == 1 else "lites"} wide × {r} high'


def grid_words(wid, unit='sash'):
    """The grid of a window or glazed door in words, from WINDOW_GRIDS: one sash, equal sashes, the bay (a centre
    sash between two equal side sashes) or equal sashes under undivided transom lites."""
    g = WINDOW_GRIDS[wid]
    if len(set(g)) == 1:
        return lites(g[0]) + (f' in each {unit}' if len(g) > 1 else '')
    if len(g) == 3 and g[0] == g[2]:
        return f'{lites(g[1])} in the centre {unit} and {lites(g[0])} in each side {unit}'
    half = len(g) // 2
    if len(g) % 2 == 0 and len(set(g[:half])) == 1 and set(g[half:]) == {(1, 1)}:
        return f'{lites(g[0])} in each {unit} below the transom, one lite in each above it'
    raise SystemExit('seventh round: WINDOW_GRIDS[%r] = %r has no wording in grid_words()' % (wid, g))


def window_types(meas):
    """The `type` text of every window and of the glazed garden door: what it is, then the white frame and the grid
    (the owner: "Set all windows to white color, and it should have grid line for these windows"). The sizes are the
    schedule's numbers and stay as they are; the skylights keep their texts. A text ends without a full stop (the
    page adds one). Stops when the schedule has a window without a text here, or the other way round. Returns the
    ids written."""
    def fin(wid, unit='sash'):
        return f'{WINDOW_FINISH}, {grid_words(wid, unit)}'
    two = 'Clear glazing, two sashes; '
    text = {
        'W01': f'Two-panel sliding glass door to the garden (one fixed, one sliding); {fin("W01", "panel")}; landing '
               'outside',
        'W02': f'Tall glazing, two sashes, from a {fi(RV.TALL_SILL)} sill to the ceiling; {fin("W02")}',
        'W03': f'Fixed glazing; {fin("W03")}',
        'W04': f'Fixed glazing; {fin("W04")}',
        'W05': two + fin('W05'), 'W06': two + fin('W06'), 'W07': two + fin('W07'),
        # the concept's text was a segmental arch; bl/shell.py has built a flat-headed three-sash window since the
        # first restyle (black steel with a grid in the third round), and its sizes are the schedule's
        'W08': 'Three-sash window with a flat head, over the sink; white frame, casing and stool, white grid bars, '
               f'{grid_words("W08")}',
        'W09': f'Three-sided canted bay glazed to the floor; 8 ft wall opening; 2 ft projection; {fin("W09")}',
        'W10': two + fin('W10'),
        'W11': f'Obscured privacy glazing, two sashes; {fin("W11")}',
        'W12': two + fin('W12'),
        'W13': f'Tall clear glazing from a {fi(RV.TALL_SILL)} sill to the ceiling, with a transom at '
               f'{RV.BATH_WIN_TRANSOM_Y:g} ft and a mullion on the shower\'s glass line: the north sash is inside the '
               f'shower; {fin("W13")}',
        'W14': f'Two sashes, one above the other; {fin("W14")}',
        'W15': two + fin('W15'),
        'W17': f'High window above the front door, 3 ft × 2 ft 3 in; {fin("W17")}; height coordinated with the '
               'lowered entry roof. Proposed; reference front.PNG',
        GARDEN_DOOR: f'Glazed hinged door; {fin(GARDEN_DOOR)}',
    }
    rows = {w['id']: w for w in meas['windows'] if w.get('kind') != 'skylight'}
    rows.update({d['id']: d for d in meas['doors'] if d['id'] == GARDEN_DOOR})
    if set(rows) != set(text) or set(text) != set(WINDOW_GRIDS):
        odd = sorted((set(rows) ^ set(text)) | (set(text) ^ set(WINDOW_GRIDS)))
        raise SystemExit('seventh round: every window and the garden door %s get a white frame and a grid, but the '
                         'schedule, window_types() and WINDOW_GRIDS do not list the same ones: %s'
                         % (GARDEN_DOOR, ', '.join(odd)))
    for wid, words in text.items():
        rows[wid]['type'] = words
    return sorted(text)


def fireplace_objects(objs):
    """The concept's fireplace in scene.objects (the owner had the fireplace sealed). Its objects stay where they
    are: an index may not shift (extract_scene.py checks it), and they are furniture and decor like the rest of
    the concept's furnishing, which neither the plan drawing nor the page's data reads. Stops when one of them is
    in a group that is drawn or measured: there it would show. Returns their indices."""
    found = [i for i, o in enumerate(objs) if re.search(FIREPLACE, o.get('name', ''), re.I)]
    drawn = [i for i in found if objs[i].get('group') in DRAWN_GROUPS]
    if drawn:
        o = objs[drawn[0]]
        raise SystemExit('seventh round: fireplace object %d %r is in group %r, which the plan drawing or the site '
                         'data reads; the fireplace is gone' % (drawn[0], o.get('name'), o.get('group')))
    return found


def changes_7():
    """The seventh round (2026-11-21) in the owner's terms: the five items, and the exterior the owner set aside."""
    lw, lh = RV.WINDOW_LITE
    return [
        'Refrigerator next to the microwave: the refrigerator stood behind cabinet panels and read as a pantry. It is '
        'now a visible stainless-steel French-door refrigerator with a bottom freezer drawer, in the same bay at the '
        'hall end of the kitchen\'s tall wall, under a two-door cabinet. The unit directly beside it, above the wall '
        'oven, is a built-in microwave (it was a second wall oven). Nothing else in the kitchen changes',
        'All windows white, with grid lines: every window frame, sash, mullion and transom bar is white, inside and '
        f'outside, and every window and glazed door has white grid bars ({in8(RV.WINDOW_BAR_W)} in wide, on both '
        f'faces of the glass) with lites as near {in8(lw)} x {in8(lh)} in as each sash allows, the bars in line '
        'across sashes and transoms. That includes the primary bedroom\'s sliding door, the living room\'s rear '
        'glazing and garden door, the bay, the tall windows of Bedroom 2 and the primary bathroom, the obscured '
        'bathroom window, the window above the front door and the kitchen window, which was a black steel grid '
        f'window and keeps its {" x ".join(str(v) for v in WINDOW_GRIDS["W08"][0])} lites per sash, now white. The '
        'skylights, the shower glass, the garage door and the front door are as they were, shades and curtains stay '
        'in front of the grids, and no window opening changes its place or size',
        'Primary bathroom walls coherent and white: the grey-green board wainscot, its cap rail and the cream plaster '
        'are removed. Every wall except the vanity wall is plain white from the floor to the ceiling, above a white '
        'tile base; the ceiling is white and the shower tile is matte white (it was cream). The stacked stone on the '
        'vanity wall stays as the one feature wall, with the timber beams, the oak vanity and mirrors, the lamps, '
        'the shelf, the grey stone floor, the fittings and the layout',
        'Fireplace sealed, sofa on that side, television opposite: the living room\'s fireplace is removed with its '
        'stone surround, firebox and hearth ledge, and the east wall is a plain white wall with its baseboard; the '
        'east windows are untouched. The sofa stands against that wall, facing west, with a side table and a lamp at '
        'each end, a round rug and a round coffee table in front of it and an armchair to the north-west, as the '
        'architect\'s sheet draws it. A 75 in television hangs on the opposite wall, the west wall shared with '
        'Bedroom 2, centred on the sofa, over a low oak media console. The way from the dining area to the rear '
        'glass and the garden door stays open',
        'Daylight corrected for the yard, which faces north: the sun was already in the south-east (late morning), '
        'but the sky was turned half a circle, with its bright side over the garden. The sky\'s glow now stands at '
        'the sun, over the street side, and its deep-blue side over the garden. The rear of the house, the deck by '
        'the house and the near lawn are in the house\'s shade; no direct sun comes in through the north-facing '
        'glass (the primary bedroom\'s sliding door, Bedroom 2\'s rear window, the living room\'s rear glazing), and '
        'sun patches fall only through the east windows, the front bay, the window above the front door and the '
        'skylights',
        'Exterior: the redesign of the exterior that the owner raised with this round was set aside by the owner. '
        'Roof, massing, entry and facade are as they were; only the white window frames and grid bars show outside',
    ]


def build_grids(log):
    """{window id: grid} as bl/revisions.white_windows printed it (`grids`) on the `revisions:` line of a build log.
    The sashes of a window the build lists in parts (the bay: W09a, W09b, W09c) are joined in that order."""
    with open(log, encoding='utf-8', errors='replace') as f:
        found = re.search(r"'white_windows': \{.*?'grids': \{(.*?)\}", f.read(), re.S)
    if not found:
        raise SystemExit('%s: no `grids` of white_windows on a `revisions:` line (not a build log, or the revision '
                         'failed)' % log)
    out = {}
    for tag, words in re.findall(r"'([^']+)': '([^']*)'", found.group(1)):
        wid = re.sub(r'(?<=\d)[a-h]$', '', tag)
        cells = re.findall(r'(\d+)x(\d+)', words.split(' lites')[0])
        out[wid] = out.get(wid, ()) + tuple((int(c), int(r)) for c, r in cells)
    return out


def check_grids(log):
    """--check-grids: WINDOW_GRIDS against the grids of a build. Prints the differences; returns the exit code."""
    built = build_grids(log)
    odd = [k for k in sorted(set(built) | set(WINDOW_GRIDS)) if built.get(k) != WINDOW_GRIDS.get(k)]
    for k in odd:
        print('DIFFERENT %s: the build has %s, WINDOW_GRIDS has %s'
              % (k, built.get(k, 'no such window'), WINDOW_GRIDS.get(k, 'no entry')))
    print('window grids: %d in the build log, %d in WINDOW_GRIDS: %s'
          % (len(built), len(WINDOW_GRIDS), 'DIFFERENT. Bring WINDOW_GRIDS in %s in line and run the sequence again'
             % os.path.basename(__file__) if odd else 'the same'))
    return 1 if odd else 0


def laundry_view():
    """The Design window's view of the closet (tools/render/data/hero_cameras.json key LC)."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    uw, ud, uh = (inches(v) + '″' for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {
        'label': 'Laundry closet',
        'title': 'A stacked washer and dryer off the foyer, next to Bedroom 4.',
        'text': 'The laundry closet is carved out of Bedroom 4\'s north-east corner and opens onto the foyer, on its '
                'west side right next to the bedroom door. A front-load washer with the dryer stacked on top stands '
                f'centred behind a pair of narrow doors in a {ft(RV.LAUNDRY_DOOR_W)} × {ft(RV.LAUNDRY_DOOR_HEAD)} '
                'opening; the doors are hinged on the two jambs and shown wide open against the foyer wall. The closet '
                f'is {ft(z1 - z0)} wide and {ft(x1 - x0)} deep inside, under the {RV.LAUNDRY_CEILING:g} ft ceiling; the '
                'oak floor runs in from the foyer, a recessed outlet box and the dryer vent are on the back wall, and a '
                'flush light sits in the ceiling. Bedroom 4 keeps its overall size and is L-shaped around the closet. '
                f'The units are generic models of a typical stacked pair ({uw} wide, {ud} deep, {uh} high each), not a '
                'selected product: connections, vent route and clearances need to be confirmed for the appliances you '
                'choose.',
        'refs': [],
        'node': LAUNDRY_NODE,
        'opening': LAUNDRY_ROOM,
        'image': f'assets/design/{LAUNDRY_VIEW}.webp',
    }


def update_design(design):
    """Add the laundry view when it is absent (after Bedroom 4 in the tab order); returns notes about views that
    still carry words of a superseded layout or finish. Nothing a person wrote in design.json is changed."""
    notes = []
    views = design.setdefault('views', {})
    if LAUNDRY_VIEW not in views:
        views[LAUNDRY_VIEW] = laundry_view()
    order = design.setdefault('order', list(views))
    if LAUNDRY_VIEW not in order:
        order.insert(order.index('B4') + 1 if 'B4' in order else len(order), LAUNDRY_VIEW)
    for key, v in views.items():
        for words in SUPERSEDED:
            if words in '%s %s' % (v.get('title', ''), v.get('text', '')):
                notes.append('design view %s still says "%s" (a layout or finish the owner replaced): edit '
                             'tools/render/data/design.json' % (key, words))
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', help=argparse.SUPPRESS)
    ap.add_argument('--check-grids', metavar='BUILD_LOG',
                    help='compare the window grids of the schedule\'s texts (WINDOW_GRIDS) with the `grids` a build '
                         'printed on its `revisions:` line; writes nothing; exit code 1 when they differ')
    a = ap.parse_args()
    if a.html:
        ap.error('--html is gone: the data lives in tools/render/data/*.json (see tools/web/sitedata.py)')
    if a.check_grids:
        raise SystemExit(check_grids(a.check_grids))
    meas = sitedata.load_measurements()
    win = {w['id']: w for w in meas['windows']}

    # (the `type` texts of the windows are written further down, by window_types)
    w = win['W01']
    w.update(name='Primary bedroom / rear sliding door', sill=0, head=RV.SLIDER_HEAD, height=RV.SLIDER_HEAD,
             start=RV.SLIDER_X[0], end=RV.SLIDER_X[1], width=round(RV.SLIDER_X[1] - RV.SLIDER_X[0], 4))
    w = win['W02']
    w.update(sill=RV.TALL_SILL, head=8.0, height=round(8.0 - RV.TALL_SILL, 4))
    w = win['W09']
    w.update(sill=0, height=w.get('head', 7.5))
    w = win['W13']
    z0, z1 = RV.BATH_WIN_Z
    w.update(start=z0, end=z1, width=round(z1 - z0, 4), sill=RV.TALL_SILL, head=8.0, height=round(8.0 - RV.TALL_SILL, 4))
    x0, x1, k0, k1 = RV.KITCHEN_SKY
    w = win['W16']
    w.update(start=x0, end=x1, width=round(x1 - x0, 4), height=round(k1 - k0, 4), c=9.4,
             p=[round((x0 + x1) / 2, 3), 9.4, round((k0 + k1) / 2, 3)],
             type='Roof glazing on the east-facing roof plane, 3\'-6" x 4\'-0", over the sink / dishwasher run')
    for i, (sx0, sx1, sz0, sz1) in enumerate(RV.FOYER_SKY):
        wid = f'W{18 + i}'
        entry = win.get(wid) or {'id': wid}
        entry.update(name=f'Foyer skylight {"(hall)" if i == 0 else "(vaulted entry)"}', axis='roof', c=10.9,
                     start=sx0, end=sx1, width=round(sx1 - sx0, 4), height=round(sz1 - sz0, 4), sill=None, head=None,
                     type='Roof glazing on the entry roof\'s east slope', node='H1' if i == 0 else 'E0', kind='skylight',
                     basis='P', p=[round((sx0 + sx1) / 2, 3), 10.9, round((sz0 + sz1) / 2, 3)])
        if wid not in win:
            meas['windows'].append(entry)
            win[wid] = entry
    sx0, sx1, sz0, sz1 = RV.PRIMARY_BATH_SKY
    entry = win.get('W20') or {'id': 'W20'}
    entry.update(name='Primary bathroom skylight (over the shower)', axis='roof', c=9.9, start=sx0, end=sx1,
                 width=round(sx1 - sx0, 4), height=round(sz1 - sz0, 4), sill=None, head=None,
                 type='Roof glazing on the west roof plane, 2\'-0" x 2\'-6", over the shower', node='A0',
                 kind='skylight', basis='P', p=[round((sx0 + sx1) / 2, 3), 9.9, round((sz0 + sz1) / 2, 3)])
    if 'W20' not in win:
        meas['windows'].append(entry)
        win['W20'] = entry
    bed4 = cut = None
    for r in meas['rooms']:
        if r['id'] == BEDROOM_4:
            bed4, cut = r, bedroom_4(r)
        if r['id'] == 'M08':
            r['note'] = 'Clear interior size; excludes walls and the bay, which is glazed to the floor.'
        if r['id'] == 'M11':
            r['name'] = 'Foyer'
            r['note'] = ('Clear interior size, from the shared bath\'s south wall to the front wall. The west wall '
                         'lines up with the shared bath\'s east wall.')
        if r['id'] == BEDROOM_4_CLOSET:     # the concept's note still gave the closet the vault Bedroom 4 lost
            r['note'] = r['note'].replace(' Cathedral ceiling: 8 ft eaves / 11 ft 6 in ridge, proposed.',
                                          ' Flat 8 ft ceiling.')
    if bed4 is None:
        raise SystemExit('measurements.json has no room %s (Bedroom 4)' % BEDROOM_4)
    room = laundry_room()
    upsert(meas['rooms'], room)
    upsert(meas['doors'], laundry_door())
    suite = suite_rooms(meas['rooms'])  # sixth round: walk-in closet, vestibule, the notes of three rooms
    pocket = suite_doors(meas['doors'])
    scene = sitedata.load_scene()
    objs = scene['objects']
    host = cut_host_wall(objs)
    for obj in laundry_objects():       # appended on a freshly relaid scene, updated in place on a re-run
        upsert(objs, obj, key='name')
    walls, new_walls = suite_walls(objs)
    leaves, new_leaf = suite_leaves(objs)
    walls += bath_window_walls(objs)
    w = win['W11']                      # the Bedroom 3 bathroom's shower window: taller, same width
    sill, head = RV.BED3_BATH_WIN_Y
    pane = bed3_bath_window(objs)
    w.update(sill=sill, head=head, height=round(head - sill, 4), panes=[{'width': pane[0], 'height': pane[1]}])
    typed = window_types(meas)          # seventh round: white frames and grids, in every window's `type`
    fire = fireplace_objects(objs)      # ... and the concept's fireplace, which stays in the scene undrawn
    dr = scene.setdefault('design_revision', {})
    vaults = dr.get('vaults', {})
    if 'bedrooms_3_4' in vaults:
        vaults['bedroom_3'] = vaults.pop('bedrooms_3_4')
    dr['owner_changes'] = {'date': '2026-11-18', 'changes': CHANGES}
    dr['owner_changes_2'] = {'date': '2026-11-19', 'changes': CHANGES_2}
    dr['owner_changes_3'] = {'date': '2026-11-19', 'changes': CHANGES_3}
    dr['owner_changes_4'] = {'date': '2026-11-19', 'changes': CHANGES_4}
    dr['owner_changes_5'] = {'date': '2026-11-20', 'changes': changes_5(bed4, cut)}
    dr['owner_changes_6'] = {'date': '2026-11-20', 'changes': changes_6(suite)}
    dr['owner_changes_7'] = {'date': '2026-11-21', 'changes': changes_7()}
    lr = scene.get('layout_revision', {})
    ids = lr.get('dimension_review', {}).get('room_ids')
    for rid in (LAUNDRY_ROOM, SUITE_VESTIBULE_ROOM):
        if isinstance(ids, list) and rid not in ids:
            ids.append(rid)
    for key in ('primary_suite_internal_layout', 'primary_bathroom'):   # the concept's own record of the two layouts
        if isinstance(lr.get(key), dict):
            lr[key]['superseded'] = ('Sixth round (2026-11-20): the suite follows the architect\'s sheet; see '
                                     'design_revision.owner_changes_6 and the dimension schedule')
    scene.setdefault('tour', {})['highlights'] = list(HIGHLIGHTS)
    labels = size_labels(meas)
    for n in scene['tour']['nodes'] + scene.get('rooms', []):
        if n.get('id') in labels:
            n['size'] = labels[n['id']]
        if n.get('id') in NODE_NAMES:
            n['label'] = n['name'] = NODE_NAMES[n['id']]
        if n.get('id') in NODE_MOVES:
            x, z = NODE_MOVES[n['id']]
            dx, dz = x - n['p'][0], z - n['p'][2]
            if abs(dx) > 1e-4 or abs(dz) > 1e-4:     # the look point travels with the stop: same yaw and pitch
                n['p'] = [x, n['p'][1], z]
                if len(n.get('look') or []) == 3:
                    n['look'] = [n['look'][0] + dx, n['look'][1], n['look'][2] + dz]
    for au in scene.get('audit', []):
        if au.get('id') == 'M11':
            au['name'] = 'Foyer'
            au['note'] = next(r['note'] for r in meas['rooms'] if r['id'] == 'M11')
        if au.get('id') == BEDROOM_4:       # the About sheet's room table: Bedroom 4's reduced area
            au['area_sqft'], au['note'] = bed4['area_sqft'], bed4['note']
        if au.get('id') in (PRIMARY_BEDROOM, PRIMARY_BATH, BEDROOM_3_BATH):
            au['note'] = suite[au['id']]['note']
    upsert(scene.setdefault('audit', []), dict(room))
    for rid in (SUITE_CLOSET_ROOM, SUITE_VESTIBULE_ROOM):
        upsert(scene['audit'], dict(suite[rid]))
    design = sitedata.load_design()
    notes = update_design(design)
    for name, changed in (('measurements', sitedata.save_measurements(meas)), ('scene', sitedata.save_scene(scene)),
                          ('design', sitedata.save_design(design))):
        print('updated' if changed else 'unchanged', sitedata.rel(sitedata.path(name)))
    print('windows:', [w['id'] for w in meas['windows']])
    own = [i for i, o in enumerate(objs) if o['name'].startswith('Laundry closet')]
    print('laundry closet: room %s %s x %s clear, doors %s, scene objects %d..%d (%d) appended and wall %d cut, '
          'design view %s, sweep %s%s'
          % (room['id'], ft(room['width_ft']), ft(room['depth_ft']), LAUNDRY_DOOR, own[0], own[-1], len(own), host,
             LAUNDRY_VIEW, LAUNDRY_NODE,
             '' if any(n.get('id') == LAUNDRY_NODE for n in scene['tour']['nodes'])
             else ' (not in the tour yet: run apply_sweeps.py)'))
    print('bedroom 4: room %s %s x %s overall, %.2f sq ft without the closet corner %s x %s'
          % (bed4['id'], ft(bed4['width_ft']), ft(bed4['depth_ft']), bed4['area_sqft'], ft(cut[0]), ft(cut[1])))
    closet, vest = suite[SUITE_CLOSET_ROOM], suite[SUITE_VESTIBULE_ROOM]
    print('primary suite: room %s %s %s x %s, room %s %s %s x %s, pocket door %s %s wide; scene walls %s reshaped and '
          '%s appended, leaves %s moved and %d appended'
          % (closet['id'], closet['name'], ft(closet['width_ft']), ft(closet['depth_ft']), vest['id'], vest['name'],
             ft(vest['width_ft']), ft(vest['depth_ft']), pocket['id'], ft(pocket['width']), walls, new_walls, leaves,
             new_leaf))
    doors = {d['id']: d for d in meas['doors']}
    print('               %s' % ', '.join('%s %s %.3f..%.3f' % (i, doors[i]['axis'], doors[i]['start'], doors[i]['end'])
                                         for i in (BATH_DOOR, SUITE_ENTRY, BED_OPENING, SUITE_CLOSET_DOOR)))
    print('               W13 z %.3f..%.3f, W20 x %.3f..%.3f z %.3f..%.3f, W11 sill %.3f head %.3f (pane %.3f x %.3f)'
          % (win['W13']['start'], win['W13']['end'], win['W20']['start'], win['W20']['end'],
             win['W20']['p'][2] - win['W20']['height'] / 2, win['W20']['p'][2] + win['W20']['height'] / 2, sill, head,
             pane[0], pane[1]))
    print('seventh round: %d window and door texts with the white frame and the grid (%s .. %s, %s); note of room %s; '
          'change list owner_changes_7 (%d entries)'
          % (len(typed), typed[1], typed[-1], typed[0], PRIMARY_BATH, len(dr['owner_changes_7']['changes'])))
    print('               the concept\'s fireplace, scene objects %s (%d), stays in the scene: groups %s, which the '
          'plan drawing and the site data do not read'
          % ('%d..%d' % (fire[0], fire[-1]) if fire else 'none', len(fire),
             ' / '.join(sorted({objs[i].get('group') for i in fire})) or '-'))
    for line in notes:
        print('note:', line)


if __name__ == '__main__':
    main()
