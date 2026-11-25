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

Eighth round (2026-11-24): the model brought to the architect's sheet SKA002 (walls 5 in and the sheet's frame in
relayout.py; Bedroom 2's closet block and the hall, the kitchen island and counters, Bedroom 3's bath, closet and
doors, the sheet's door and window openings, the living room's skylight, the garage's floor, doors and water heater,
the roof, the ground, the landings and the porch). Everything below "Eighth round" in this file; all numbers from
relayout.py, bl/revision_spec.py and bl/garage_spec.py, and from the Blender-side modules bl/roof.py,
bl/zones/exterior_layout.py and bl/zones/kitchen_dining_kitchen.py, whose plain constants blender_spec() reads
without importing them (they import bpy).
  * measurements.json. A DOOR's `start` / `end` / `width` are now its CLEAR opening, between the jamb liners, frames
    or jamb boards: the size the sheet gives a door, and the size of the door that hangs in it. `wall_start` /
    `wall_end` keep the cut in the wall boxes, which `start` / `end` were until the seventh round (3/4 in more for
    an interior door, 4 in for the two garage doors with their 2 in frames). A glazed unit (a window, a sidelight,
    the two sliding glass doors W01 and D14) keeps the unit's wall opening, as the sheet dimensions it. `sill` and
    `head` are measured from the floor the opening stands on; `floor` gives that floor's level when it is not the
    house floor (the garage's vehicle door and side door). New rows: doors D19 (furnace closet), D20 (storage
    closet), D21 (garage side door); windows W21 (living room skylight), W22 / W23 (the front door's sidelights);
    room M15 (Bedroom 2's closet). Gone: W03, W04 and the garden door, which are one four-panel sliding door now
    (it keeps the id D14); W06 (W05 is one 6'-0" unit); W10 while revision_spec.BED3_WEST_WINDOW is False. `spaces`
    lists what the schedule does not measure as a room but the plan shows: the two closets nobody enters, the hall's
    two legs, the garage with its floor level and step, the porch and the two rear landings. `overall` holds the
    outside sizes.
  * scene.objects. Wall boxes follow the built model piece by piece: existing objects are reshaped in place BY INDEX
    (ROUND8 tables; the name is checked), pieces the build no longer has are marked `removed` and move to the group
    'removed' (an index may not shift, and no tool draws that group; the old group is kept in `group_was`), new
    pieces are appended by name. Door leaves take their successors' places; the sliding panels, the new glass and
    the five skylights are appended; the garage's slab goes down 11 in and gets its step. The concept's roof and
    the old windows' frames are marked removed (the new roof is not copied into the scene: nothing on the web
    side reads a roof). Baseboards and casings of the scene are not re-cut.
  * scene_classification.json: `meta.rooms` follows the hall and Bedroom 2 (tools/web/build_site_data.py and
    place_sweeps.py read it), and every scene object has a record with the box it has now.
  * the tour's seeds: C3 (the stop inside Bedroom 3's old step-in closet) leaves the scene; H3, A3 and G0 move to
    where the rebuilt rooms leave room (NODE_MOVES). place_sweeps.py and apply_sweeps.py do the rest.
  * the round's last builds (repairs and the final model changes): the porch slab half way between the front walk
    and the floor (two equal risers; the texts read bl/zones/exterior_layout.py PORCH_TOP), the kitchen skylight
    with its east edge where the wider opening's was (revision_spec.KITCHEN_SKY), and W14, the primary bedroom's
    second west window, with W15's unit in its own opening (PRIMARY_WEST_WIN_S_Z; WINDOW_GRIDS, its `type` and
    `panes`; the old unit's scene objects are marked removed and its two panes appended last, so that no earlier
    index shifts; round8_west_window_south). The porch side's two baseboards of the front door wall are marked
    removed (no baseboard outdoors).
"""
import argparse
import ast
import math
import os
import re
import sys
import types

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
    'Primary bedroom: the 7 ft rear window becomes a two-panel sliding door to the garden (landing outside; since '
    'the eighth round in the sheet\'s {slider} wall opening)',
    'Bedroom 2 (next to the primary): rear window runs to the ceiling (sill 2\'-0" since the third round)',
    'Primary bathroom: tall west window in clear glass, sill 2\'-0" since the third round (an evergreen screen in the '
    'fenced side yard outside). It stood between the vanity and the shower of the earlier layout; the sixth round '
    'moves it to the architect\'s position and widens it to 3\'-0"',
    'Kitchen skylight on the continuous east roof plane over the sink / dishwasher (the concept unit straddled the '
    'garage-gable ridge). It was 3\'-6" x 4\'-0" until the eighth round, which makes it {sky}, the size of the '
    'outline on the architect\'s sheet; its east edge stays where it was, {sky_east} from the east wall, so the '
    'narrower well still lies over the sink',
    'Dining: table in line with the island, no island stools (warm oak under a brass lantern since the third round; '
    f'moved to the island\'s west end, {DINING_TABLE} for six, in the fifth round)',
]       # (the {slider}, {sky} and {sky_east} of two entries are filled in by changes_1())
CHANGES_2 = [
    'Primary bathroom: a 2\'-0" x 2\'-6" skylight over the shower (in the sixth round it moves with the shower to the '
    'room\'s north-west corner)',
    # (the widths are filled in by changes_2(): they follow the sheet's 5 in walls)
    'The foyer-side wall of Bedroom 4 (office) and Bedroom 3 lines up with the shared bath\'s east wall: both '
    'rooms and the closets between them are {wider} wider; foyer and covered porch {foyer} wide; '
    'foyer {length} long as on the plan; the 3\'-0" front door stays centred (with a sidelight on each side since '
    'the eighth round)',
    'Rear landing outside the living room sized as on the plan, 3\'-0" deep (since the eighth round the sheet\'s '
    '{landing_l} landing, {landing_past} past each jamb of the living room\'s sliding door; it ends {landing} short '
    'of the east wall\'s inside face)',
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
R = RV.R                        # tools/render/relayout.py: the sheet's frame (wall faces, room rectangles)
G = RV.GARAGE                   # tools/render/bl/garage_spec.py: front door unit, garage doors, garage floor and step
_LIV, _GAR, _FOY = R.ROOMS['living'], R.ROOMS['garage'], R.ROOMS['foyer']
LIVING_W = _LIV[1] - _LIV[0]    # living room clear width, the plan's 16'-8"
GARAGE_W, GARAGE_D = _GAR[1] - _GAR[0], _GAR[3] - _GAR[2]     # the plan's 17'-7" x 20'-11"


def blender_spec(relpath, **given):
    """The plain numbers of a Blender-side module that cannot be imported here because it imports bpy: its top-level
    assignments and functions, run in file order with relayout as `R`, `math`, and whatever `given` names (what the
    module itself imports from a neighbour). A statement that needs anything else is left out, so a name it would
    have defined is simply missing (AttributeError where it is asked for). This is how the web data reads the site's,
    the roof's and the kitchen's numbers by the names the build uses, instead of keeping copies of them."""
    ns = {'R': R, 'math': math, '__name__': 'blender_spec:' + relpath}
    ns.update(given)
    with open(os.path.join(HERE, relpath), encoding='utf-8') as f:
        tree = ast.parse(f.read(), relpath)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.FunctionDef)):
            try:
                exec(compile(ast.Module([node], []), relpath, 'exec'), ns)
            except Exception:       # noqa: BLE001  (bpy, numpy, a neighbour module: not a plain number)
                pass
    return types.SimpleNamespace(**{k: v for k, v in ns.items() if not k.startswith('__')})


# bl/zones/exterior_layout.py: ground levels, the two rear landings, the porch slab, the driveway (SCENE feet)
SITE = blender_spec('bl/zones/exterior_layout.py', GRADE=blender_spec('bl/zones/exterior_util.py').GRADE)
# bl/roof.py: the roof of the architect's sheets (planes, ridges, eaves) and the two vaults that follow it
ROOF = blender_spec('bl/roof.py')
# bl/zones/kitchen_dining_kitchen.py: the island and the counters as the sheet has them (PLAN_*)
KITCHEN = blender_spec('bl/zones/kitchen_dining_kitchen.py')
# the living room's rear landing ends this far short of the east wall's inside face (1'-1 3/8"; DECK is LD2 of SKA002)
LANDING_SHORT = R.X_LIV_E - SITE.DECK[1]


# H1 stands in the plan's foyer (z 28.9 .. 47.4); H2, north of it between the shared bath and the kitchen,
# is the hall. S0 and C0 are the stops of the primary suite's vestibule and walk-in closet (sixth round; the concept
# called them "Open primary dressing area" and "Primary dressing storage"). place_sweeps.py gives a new sweep the
# label of the nearest of these stops.
NODE_NAMES = {'H1': 'Foyer', 'H2': 'Hall', 'S0': 'Primary vestibule', 'C0': 'Walk-in closet',
              'P1': 'Primary vestibule approach'}     # (the concept: "Primary dressing approach")

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
# Seed stops that the rebuilt model moves (place_sweeps.py keeps a stop where the scene has it; a stop keeps its view
# direction, the look point travels with it). The clearances are rays on the eighth round's build (48 directions at
# 0.6, 2.0, 3.5 ft and eye height above the stop's floor); place_sweeps.py accepts a seed as it is from 1.2 ft.
#   K0  The concept's kitchen stop (25.63, 26.00) stands in the south chairs of the dining table since the fifth
#       round. It stands at the west end of the work aisle between the island and the cooktop counter, on the
#       runner just east of the table. Eighth round (island 7'-0" x 4'-0" at the sheet's place, the table moved west
#       with it): 1.87 ft, to the island.
#   H3  The concept's hall stop stood in front of the wall south of Bedroom 2's entry alcove. That wall is gone:
#       the closet block's south face stands 2.3 ft further south and carries a ledge, in which the stop would
#       stand. It moves into the hall's east leg, the 3'-4" passage south of the block: 1.59 ft, to the canvas over
#       the ledge.
#   A3  Bedroom 3's bath as on the sheet: the stop stood where the towel bar on the south wall is now. It moves
#       to the floor between the vanity and the door, on the door's side of the shower glass: 1.56 ft, to the vanity.
#   G0  The garage floor is 11 in below the house floor, with a step at the house door: the stop stood on the
#       step's edge. It moves onto the garage floor, on the door's axis, clear of the step: 1.34 ft, to the open
#       leaf. (Its height is place_sweeps.py's: the eye above the floor the stop stands on.)
NODE_MOVES = {'K0': (_LIV[0] + 5.072, 26.9),       # 27.714, 26.9: 5.07 ft east of the living room's west wall line
              'H3': (R.X_BLOCK_W + 2.325, R.Z_BLOCK_S + 1.742),                 # 17.300, 19.300
              'A3': (R.ROOMS['bed3_bath'][0] + 5.975, R.ROOMS['bed3_bath'][2] + 3.292),         # 6.200, 40.600
              'G0': (_GAR[0] + 2.575, sum(G.HOUSE_DOOR['clear']) / 2)}          # 24.300, 37.829
# Seed stops that the rebuilt model has no place for: C3 stood inside Bedroom 3's step-in closet, which is a
# reach-in closet behind two sliding panels now, fitted 1.6 ft deep. The closet is seen from Bedroom 3's stop B3.
NODES_GONE = ('C3',)
# Captions of the concept's approach stops that named what the doorway was
NODE_SIZES = {'T4': 'Bathroom door', 'T6': 'Closet doors', 'GA': 'Door to the garage', 'P1': 'Open connection'}
# the highlight reel: the old page's room stops (tools/web/build_site_data.py HIGHLIGHTS) plus the laundry sweep,
# after Bedroom 4, which the closet stands next to; without C3 since the eighth round
HIGHLIGHTS = ['E0', 'L8', 'D0', 'K0', 'P0', 'B2', 'B3', 'B4', LAUNDRY_NODE, 'A0', 'A1', 'A3', 'S0', 'C0', 'G0']
# L8 (seventh round): the living room card opens on the television wall, the rear glass and the sofa in one view
# design.json is edited by hand: words of a layout the owner has replaced, reported when a view still has them
# (the kitchen-corner laundry closet and the small dining table of the fourth round; the primary bath and the open
# dressing area as they were until the fifth; black window frames without grids, the panelled refrigerator beside two
# wall ovens, the primary bath's wainscot, plaster and cream tile, and the fireplace as they were until the sixth;
# the concept's roof, the porch canopy, the garden door, Bedroom 2's entry alcove, Bedroom 3's step-in closet and
# pocket doors, the 3'-6" x 4'-0" kitchen skylight and the tankless water heater as they were until the seventh)
SUPERSEDED = ('kitchen\'s south-west corner', 'behind one door', 'table for four',
              'Sage tile', 'sage-green', 'encaustic', 'between the vanity and the shower', 'dressing area',
              'black frame', 'black grid', 'large clear panes', 'panelled fridge', 'wall ovens',
              'wainscot', 'cream plaster above', 'cream tile', 'cream ceiling', 'fireplace', 'hearth',
              '6:12', '4:12', 'provisional', 'cricket', 'slight fall', 'canopy', 'garden door', 'entry alcove',
              'compact closet', 'step-in', 'pocket opening', '3′6″ × 4′', '11′6″', 'tankless', 'clerestory')

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
# Eighth round: the openings rebuilt at the sheet's sizes have new grids (W01, W02, W05, W07, W12); W03, W04 and the
# garden door are one four-panel sliding door, which keeps the id D14 (the build lists its panes in two groups, the
# west pair and the east pair, parted by the open way: D14a, D14b); W06 is part of W05; the front door's two
# sidelights are W22 and W23; W10 exists only while revision_spec.BED3_WEST_WINDOW is True. W14, the primary
# bedroom's second west window, has W15's unit in its own opening since the round's last build (two sashes side by
# side, 1 x 3 lites each; it had two sashes one above the other, 2 x 1 each).
WINDOW_GRIDS = {
    'W01': ((2, 5), (2, 5)), 'W02': ((2, 4), (2, 4)),
    'W05': ((2, 3), (2, 3)), 'W07': ((3, 3), (1, 3)), 'W08': ((2, 4), (2, 4), (2, 4)),
    'W09': ((2, 5), (3, 5), (2, 5)), 'W11': ((1, 3), (1, 3)), 'W12': ((2, 3), (2, 3)),
    'W13': ((1, 3), (1, 3), (1, 1), (1, 1)), 'W14': ((1, 3), (1, 3)), 'W15': ((1, 3), (1, 3)), 'W17': ((3, 2),),
    'W22': ((1, 4),), 'W23': ((1, 4),),
    'D14': ((2, 5), (2, 5), (2, 5), (2, 5)),
}
if RV.BED3_WEST_WINDOW:
    WINDOW_GRIDS['W10'] = ((2, 3), (2, 3))
GARDEN_DOOR = 'D14'                 # the living room's glazed door to the rear landing (a hinged garden door until the
#                                     seventh round, the four-panel sliding door since): white with a grid, like the
#                                     windows. Its `type` keeps the word "glazed": white_windows finds the door by it.
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
    f, sky = rooms['M11'], RV.KITCHEN_SKY
    return {
        'P0': wd('M01'), 'B2': wd('M02'), 'A0': wd('M03') + ' · skylight over the shower', 'A1': wd('M04'),
        SUITE_CLOSET_NODE: wd(SUITE_CLOSET_ROOM), SUITE_VESTIBULE_NODE: wd(SUITE_VESTIBULE_ROOM),
        'B4': wd(BEDROOM_4, ' overall, L-shaped + separate reach-in closet'), 'B3': wd('M08'),
        'A3': wd('M09'), 'L0': f'{ft(LIVING_W)} living-room width · R',
        'E0': f"3′0″ entrance · {ft(f['width_ft'])} × {ft(f['depth_ft'])} foyer · P",
        'K0': f'{ft(sky[1] - sky[0])} × {ft(sky[3] - sky[2])} skylight · dining table at the island\'s west end',
        'G0': f'{ft(GARAGE_W)} × {ft(GARAGE_D)} · R',
    }


def r4(v):
    return round(float(v), 4)


def changes_1():
    """The first round (2026-11-18), with the two sizes the eighth round set to the sheet."""
    kx0, kx1, kz0, kz1 = RV.KITCHEN_SKY
    f = dict(slider=fi(RV.SLIDER_X[1] - RV.SLIDER_X[0]), sky=f'{fi(kx1 - kx0)} x {fi(kz1 - kz0)}',
             sky_east=in8(_LIV[1] - kx1) + ' in')
    return [c.format(**f) if '{' in c else c for c in CHANGES]


def changes_2():
    """The second round (2026-11-19) with its widths from the sheet's frame: how far east of the sheet's place the
    foyer-side wall stands, the foyer's width and length, the landing as the eighth round built it."""
    d0, d1, dz0, dz1 = SITE.DECK
    f = dict(wider=fi(R.X_FOYER_W - R.X_FOYER_W_SHEET), foyer=fi(_FOY[1] - _FOY[0]), length=fi(_FOY[3] - _FOY[2]),
             landing=fi(LANDING_SHORT), landing_l=f'{fi(d1 - d0)} x {fi(dz1 - dz0)}',
             landing_past=in8(RV.LIVING_SLIDER_X[0] - d0) + ' in')
    return [c.format(**f) for c in CHANGES_2]


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
        'west windows (W15 and W14, both kept, with the same two-sash unit), with a nightstand under each; the rear '
        f'sliding door W01 opens to the garden. Open to the vestibule at the south-east corner ({BED_OPENING}, '
        f'{ft(bx1 - bx0)} wide, no door).')
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
            'sheet' if off else ''))
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
        + (f'; it stands {fi(abs(off))} {"south" if off > 0 else "north"} of its place on the sheet' if off else
           ' (at the sheet\'s place since the eighth round, which made Bedroom 2\'s entry alcove part of the hall; '
           'until then it stood beside that alcove, 1\'-8" further south)'),
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
    """The `type` text of every window and of the glazed sliding door D14: what it is, then the white frame and the
    grid (the owner: "Set all windows to white color, and it should have grid line for these windows"). The sizes are
    the schedule's numbers and stay as they are; the skylights keep their texts. A text ends without a full stop (the
    page adds one). Stops when the schedule has a window without a text here, or the other way round. Returns the
    ids written. (Eighth round: the openings rebuilt at the sheet's sizes; W03, W04, W06 gone; W22, W23 new.)"""
    def fin(wid, unit='sash'):
        return f'{WINDOW_FINISH}, {grid_words(wid, unit)}'
    two = 'Clear glazing, two sashes; '
    panel = fi(RV.slider_panels(RV.SLIDER_X, 2)[0][2] - RV.slider_panels(RV.SLIDER_X, 2)[0][1])     # 3'-1 5/16" -> 1/8
    lx0, lx1 = RV.LIVING_SLIDER_X
    lc0, lc1 = RV.slider_clear(RV.LIVING_SLIDER_X)
    sx0, sx1 = RV.SLIDER_X
    sc0, sc1 = RV.slider_clear(RV.SLIDER_X)
    way = RV.living_slider_way()
    m = RV.DINING_EAST_WIN_MULLION                                   # W07: its mullion's centre line
    z0, z1 = RV.DINING_EAST_WIN_Z
    g7 = WINDOW_GRIDS['W07']
    side = f'Fixed sidelight of the front door unit, clear glass above a {in8(G.FRONT_DOOR_SIDELIGHT_RAIL_Y)} in bottom rail; '
    text = {
        'W01': f'Two-panel sliding glass door to the garden in a {fi(sx1 - sx0)} wall opening ({fi(sc1 - sc0)} clear '
               f'between the frame\'s jambs): a fixed west panel and a sliding east panel, each {panel} wide; shown '
               f'closed; {fin("W01", "panel")}; landing outside',
        'W02': f'Tall glazing, two sashes, from a {fi(RV.TALL_SILL)} sill to the ceiling; {fin("W02")}',
        'W05': f'Clear glazing, one unit with two sashes; {fin("W05")}',
        'W07': f'Clear glazing, two unequal sashes as on the architect\'s sheet (the mullion stands {fi(m - z0)} '
               f'from the north jamb and {fi(z1 - m)} from the south jamb); {WINDOW_FINISH}, {lites(g7[0])} in the '
               f'north sash and {lites(g7[1])} in the south sash',
        # the concept's text was a segmental arch; bl/shell.py has built a flat-headed three-sash window since the
        # first restyle (black steel with a grid in the third round), and its sizes are the schedule's
        'W08': 'Three-sash window with a flat head, over the sink; white frame, casing and stool, white grid bars, '
               f'{grid_words("W08")}',
        'W09': f'Three-sided canted bay glazed to the floor; 8 ft wall opening; 2 ft projection; {fin("W09")}',
        'W11': f'Obscured privacy glazing, two sashes; {fin("W11")}',
        'W12': two + fin('W12'),
        'W13': f'Tall clear glazing from a {fi(RV.TALL_SILL)} sill to the ceiling, with a transom at '
               f'{RV.BATH_WIN_TRANSOM_Y:g} ft and a mullion on the shower\'s glass line: the north sash is inside the '
               f'shower; {fin("W13")}',
        'W14': two + fin('W14'),              # the same unit as W15 (bl/revisions.primary_west_window_south)
        'W15': two + fin('W15'),
        'W17': f'High window above the front door unit, 3 ft × 2 ft 3 in; {fin("W17")}; under the entry roof\'s '
               'front gable',
        'W22': side + fin('W22'),
        'W23': side + fin('W23'),
        GARDEN_DOOR: f'Four-panel glazed sliding door to the rear landing in a {fi(lx1 - lx0)} wall opening '
                     f'({fi(lc1 - lc0)} clear between the frame\'s jambs): a fixed panel at each end and two sliding '
                     f'centre panels, each {panel} wide; shown with the east centre panel slid open, a way of '
                     f'{fi(way[1] - way[0])}; {fin(GARDEN_DOOR, "panel")}',
    }
    if RV.BED3_WEST_WINDOW:
        text['W10'] = two + fin('W10')
    rows = {w['id']: w for w in meas['windows'] if w.get('kind') != 'skylight'}
    rows.update({d['id']: d for d in meas['doors'] if d['id'] == GARDEN_DOOR})
    if set(rows) != set(text) or set(text) != set(WINDOW_GRIDS):
        odd = sorted((set(rows) ^ set(text)) | (set(text) ^ set(WINDOW_GRIDS)))
        raise SystemExit('seventh round: every window and the sliding door %s get a white frame and a grid, but the '
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
        'glazing and garden door (one four-panel sliding door since the eighth round), the bay, the tall windows of '
        'Bedroom 2 and the primary bathroom, the obscured '
        'bathroom window, the window above the front door and the kitchen window, which was a black steel grid '
        f'window and keeps its {" x ".join(str(v) for v in WINDOW_GRIDS["W08"][0])} lites per sash, now white. The '
        'skylights, the shower glass, the garage door and the front door are as they were, shades and curtains stay '
        'in front of the grids, and no window opening changes its place or size in this round (the eighth round sets '
        'the openings to the architect\'s sizes and lays their grids out again by the same rule)',
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
        'glass and its door stays open',
        'Daylight corrected for the yard, which faces north: the sun was already in the south-east (late morning), '
        'but the sky was turned half a circle, with its bright side over the garden. The sky\'s glow now stands at '
        'the sun, over the street side, and its deep-blue side over the garden. The rear of the house, the landings '
        'by the house and the near lawn are in the house\'s shade; no direct sun comes in through the north-facing '
        'glass (the primary bedroom\'s sliding door, Bedroom 2\'s rear window, the living room\'s rear glazing), and '
        'sun patches fall only through the east windows, the front bay, the window above the front door and the '
        'skylights',
        'Exterior: the redesign of the exterior that the owner raised with this round was set aside by the owner. '
        'Roof, massing, entry and facade are as they were; only the white window frames and grid bars show outside '
        '(the eighth round rebuilds the roof, the porch roof and the ground levels to the architect\'s sheets; colours '
        'and cladding stay)',
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


# ---------------------------------------------------------------------------------------------------------------------
# Eighth round (2026-11-24): the model on the architect's sheet SKA002 (bl/revision_spec.py "v7 glazing", "v7 bedrooms",
# "v7 hall"; bl/garage_spec.py; bl/roof.py; bl/zones/exterior_layout.py; bl/zones/kitchen_dining_kitchen.py).
ROUND8 = 'eighth round'
LIVING_SKYLIGHT, SIDELIGHTS = 'W21', ('W22', 'W23')         # new windows: the next free W tags
FAU_DOOR, STO_DOOR, SIDE_DOOR = 'D19', 'D20', 'D21'         # new doors: the next free D tags
BED2, BED2_CLOSET_ROOM, BED3, BED3_CLOSET_ROOM, SHARED_BATH = 'M02', 'M15', 'M08', 'M10', 'M04'
# bl/revisions.skylight: the glass lies on a 0.25 ft curb, 0.06 ft above it, 0.03 ft thick, parallel to the roof
SKY_GLASS_UP = 0.25 + 0.06 + 0.03 / 2
GLASS_LOOK = {'color': '#bcd7df', 'group': 'glass'}
FLOOR_LOOK = {'color': '#b9b6ae', 'group': 'floor'}
STUCCO_LOOK = {'color': '#f1eee6', 'group': 'facade'}
SITE_LOOK = {'color': '#8a6a4a', 'group': 'landscape'}


def deg(v):
    return f'{v:g} degrees'


def clear_span(d, clear, wall, head=None, kind=None, floor=None, **more):
    """A door row's opening: `start` / `end` / `width` are the CLEAR opening (between the jamb liners, frames or jamb
    boards), `wall_start` / `wall_end` the cut in the wall boxes; sill and head are measured from the floor the door
    stands on, `floor` is that floor's level when it is not the house floor."""
    d.update(start=r4(clear[0]), end=r4(clear[1]), width=r4(clear[1] - clear[0]), wall_start=r4(wall[0]),
             wall_end=r4(wall[1]))
    if head is not None:
        d.update(height=head, sill=0, head=head)
    if kind is not None:
        d['type'] = kind
    if floor is not None:
        d['floor'] = r4(floor)
    else:
        d.pop('floor', None)
    d.update(more)
    return d


def door_row(doors, did, name, axis, c, clear, wall, kind, node, head=RV.DOOR_HEAD, floor=None, **more):
    """The door `did` of the schedule, written in place or appended (ids are stable: a door that moves keeps its id)."""
    d = next((x for x in doors if x['id'] == did), None)
    if d is None:
        d = {'id': did}
        doors.append(d)
    d.update(name=name, axis=axis, c=r4(c), node=node, kind='door', basis='P')
    return clear_span(d, clear, wall, head, kind, floor, **more)


def round8_doors(doors):
    """Every door of the schedule after the round. Returns the rows by id."""
    by_id = {d['id']: d for d in doors}
    for need in ('D01', 'D02', 'D03', 'D04', 'D05', 'D06', 'D07', 'D12', 'D13', GARDEN_DOOR, 'D15', 'D16',
                 BATH_DOOR, SUITE_ENTRY, BED_OPENING, LAUNDRY_DOOR, SUITE_CLOSET_DOOR):
        if need not in by_id:
            raise SystemExit('measurements.json has no door %s' % need)
    for did, name in ((FAU_DOOR, 'Furnace closet door'), (STO_DOOR, 'Storage closet door'),
                      (SIDE_DOOR, 'Garage side door')):
        if did in by_id and by_id[did]['name'] != name:
            raise SystemExit('measurements.json: door tag %s is taken by %r' % (did, by_id[did]['name']))
    ln = RV.DOOR_LINER

    def wall_of(clear, by=ln):
        return clear[0] - by, clear[1] + by

    def w(span):
        return fi(span[1] - span[0])
    fd, hd, sd = G.FRONT_DOOR, G.HOUSE_DOOR, G.SIDE_DOOR
    low, rise = in8(-G.FLOOR_Y), in8(-G.STEP_Y)
    step = f'{fi(G.STEP[1] - G.STEP[0])} x {fi(G.STEP[3] - G.STEP[2])}'
    frame = in8(G.FRAME)
    # the front door unit, the two doors of the garage, the vehicle door (bl/garage_spec.py)
    door_row(doors, 'D01', 'Front entrance', fd['axis'], fd['c'], fd['clear'], G.FRONT_DOOR_UNIT,
             f'Hinged on the east post, opening into the foyer; shown open {deg(fd["open_deg"])}. A {w(fd["clear"])} '
             f'walnut door in a white unit {w(G.FRONT_DOOR_UNIT)} wide, which leaves {in8(G.FRONT_DOOR_SIDE)} in of '
             f'wall on each side of it, with a sidelight on each side of the door ({SIDELIGHTS[0]}, {SIDELIGHTS[1]})',
             'E0')
    door_row(doors, 'D02', 'Door between house and garage', hd['axis'], hd['c'], hd['clear'], hd['ro'],
             f'Hinged on the north jamb, opening east into the garage; shown open {deg(hd["open_deg"])}; self-closing. '
             f'A {w(hd["clear"])} door in {frame} in frames ({w(hd["ro"])} wall opening). The garage floor is {low} in '
             f'below the house floor: a {rise} in riser down to a step of {step}, a second one down to the floor',
             'G0')
    door_row(doors, SIDE_DOOR, 'Garage side door', sd['axis'], sd['c'], sd['clear'], sd['ro'],
             f'Hinged on the south jamb, opening west into the garage; shown closed; lever and deadbolt. A '
             f'{w(sd["clear"])} door in {frame} in frames ({w(sd["ro"])} wall opening) in the garage\'s east wall. It '
             f'stands on the garage floor, {low} in below the house floor', 'G0', head=G.DOOR_HEAD, floor=G.FLOOR_Y)
    door_row(doors, 'D15', 'Garage vehicle door', 'x', sum(G.VEHICLE_WALL_Z) / 2, G.VEHICLE_DOOR_X, G.VEHICLE_RO_X,
             f'Sectional vehicle door, shown closed: {w(G.VEHICLE_DOOR_X)} wide between two {in8(G.VEHICLE_JAMB)} in '
             f'jamb boards in the {w(G.VEHICLE_RO_X)} wall opening of the architect\'s sheet, {fi(G.VEHICLE_HEIGHT)} '
             f'high above the garage floor, which is {low} in below the house floor', 'G0', head=G.VEHICLE_HEIGHT,
             floor=G.FLOOR_Y)
    # Bedroom 3 and Bedroom 4 (v7 bedrooms)
    door_row(doors, 'D03', 'Bedroom 3 entry', 'z', sum(RV.BED3_ENTRY_WALL_X) / 2, RV.BED3_ENTRY_Z,
             wall_of(RV.BED3_ENTRY_Z),
             f'Hinged on the north jamb, opening west into Bedroom 3; shown open {deg(RV.BED3_ENTRY_OPEN_DEG)}, along '
             'the room\'s north wall', 'B3')
    door_row(doors, 'D04', 'Bedroom 4 entry', 'z', sum(R.FOYER_WALL) / 2, RV.BED4_ENTRY_Z, RV.BED4_ENTRY_WALL_Z,
             f'Hinged on the north jamb, opening west into Bedroom 4; shown open {deg(RV.BED4_ENTRY_OPEN_DEG)}', 'B4')
    door_row(doors, 'D05', 'Bedroom 3 bathroom', 'x', RV.BED3_NORTH_WALL_C, RV.BED3_BATH_DOOR_X,
             wall_of(RV.BED3_BATH_DOOR_X),
             f'Hinged on the east jamb, opening north into the bathroom; shown open {deg(RV.BED3_BATH_DOOR_OPEN_DEG)}, '
             'along the bathroom\'s east wall; quartz saddle', 'B3')
    door_row(doors, 'D06', 'Bedroom 3 closet', 'x', RV.BED3_NORTH_WALL_C, RV.BED3_CLOSET_DOOR_X,
             wall_of(RV.BED3_CLOSET_DOOR_X),
             f'Two bypass sliding panels of {fi(RV.BED3_CLOSET_PANEL_W)}; shown with both panels at the east end, the '
             'west half of the closet open', 'B3')
    # Bedroom 2, its closet, the two closets of the block and the shared bath (v7 hall)
    door_row(doors, 'D12', 'Bedroom 2 entry', 'x', sum(RV.BED2_SOUTH_WALL_Z) / 2, RV.BED2_DOOR_X,
             wall_of(RV.BED2_DOOR_X),
             f'Hinged on the west jamb, opening north into Bedroom 2; shown open {deg(RV.BED2_DOOR_OPEN_DEG)}, along '
             'the bedroom\'s west wall', 'B2')
    door_row(doors, 'D13', 'Bedroom 2 closet', 'x', sum(RV.BED2_SOUTH_WALL_Z) / 2, RV.BED2_CLOSET_DOOR_X,
             wall_of(RV.BED2_CLOSET_DOOR_X),
             f'Two bypass sliding panels of {fi(math.floor(RV.BED2_CLOSET_PANEL_W * 12) / 12)} (and the lap of their '
             'meeting stiles); shown with both panels at the west '
             'end, the east half of the closet open', 'B2')
    fx0, fx1, fz0, fz1 = RV.FAU_CLEAR
    door_row(doors, FAU_DOOR, 'Furnace closet door', 'z', sum(RV.BLOCK_WEST_WALL_X) / 2, RV.FAU_DOOR_Z,
             wall_of(RV.FAU_DOOR_Z),
             'Hinged on the north jamb, opening west into the hall; louvred leaf, shown closed. The furnace closet '
             f'behind it is {fi(fx1 - fx0)} x {fi(fz1 - fz0)} clear', 'H3')
    tx0, tx1, tz0, tz1 = RV.STO_CLEAR
    door_row(doors, STO_DOOR, 'Storage closet door', 'x', sum(RV.BLOCK_SOUTH_WALL_Z) / 2, RV.STO_DOOR_X,
             wall_of(RV.STO_DOOR_X),
             'Hinged on the east jamb, opening south into the hall; shown closed. The storage closet behind it is '
             f'{fi(tx1 - tx0)} x {fi(tz1 - tz0)} clear', 'H3')
    door_row(doors, 'D07', 'Shared bathroom entry', 'x', sum(RV.SHARED_BATH_NORTH_WALL_Z) / 2, RV.SHARED_BATH_DOOR_X,
             wall_of(RV.SHARED_BATH_DOOR_X),
             f'Hinged on the east jamb, opening south into the bathroom; shown open '
             f'{deg(RV.SHARED_BATH_DOOR_OPEN_DEG)}, along the bathroom\'s east wall; oak saddle', 'A1')
    # the living room's rear wall (v7 glazing): one four-panel sliding glass door in place of the garden door and the
    # two fixed lights. A glazed unit: its width is the unit's wall opening, as for the windows (its text: window_types)
    lx = RV.LIVING_SLIDER_X
    lc, way = RV.slider_clear(lx), RV.living_slider_way()
    door_row(doors, GARDEN_DOOR, 'Living room rear sliding door', 'x', RV.REAR_WALL_C, lx, lx,
             by_id[GARDEN_DOOR].get('type', ''), 'L1', head=RV.LIVING_SLIDER_HEAD, clear_start=r4(lc[0]),
             clear_end=r4(lc[1]), way_start=r4(way[0]), way_end=r4(way[1]))
    # the doors of earlier rounds: the same measure
    bx0, bx1 = RV.BATH_DOOR_X
    clear_span(by_id[BATH_DOOR], (bx0 + RV.BATH_DOOR_LINER, bx1 - RV.BATH_DOOR_LINER), (bx0, bx1))
    clear_span(by_id[SUITE_ENTRY], RV.SUITE_ENTRY_CLEAR_Z, RV.SUITE_ENTRY_Z)
    clear_span(by_id[BED_OPENING], RV.SUITE_BED_OPENING_X, RV.SUITE_BED_OPENING_X)       # no liners: an open connection
    clear_span(by_id[SUITE_CLOSET_DOOR], RV.SUITE_CLOSET_DOOR_CLEAR_Z, RV.SUITE_CLOSET_DOOR_Z)
    lz0, lz1 = RV.LAUNDRY_DOOR_Z
    lclear = (lz0 + RV.LAUNDRY_DOOR_LINER, lz1 - RV.LAUNDRY_DOOR_LINER)
    north, south = RV.LAUNDRY_DOOR_HINGES
    clear_span(by_id[LAUNDRY_DOOR], lclear, (lz0, lz1),
               kind=f'Pair of hinged leaves, one on the {north} jamb and one on the {south} jamb, opening '
                    f'{RV.LAUNDRY_DOOR_SWING} into the foyer; shown open {deg(RV.LAUNDRY_DOOR_OPEN_DEG)}. '
                    f'{fi(lclear[1] - lclear[0])} clear between the jamb liners of the {fi(RV.LAUNDRY_DOOR_W)} wall '
                    'opening')
    d16 = by_id['D16']                  # Bedroom 4's closet: the concept's opening, without liners (F55: not "60-inch")
    clear_span(d16, (d16['start'], d16['end']), (d16['start'], d16['end']),
               kind=f'Two bypass sliding panels in a {fi(d16["end"] - d16["start"])} opening')
    return {d['id']: d for d in doors}


def sky_y(plane, rect):
    """Height of a skylight's glass at its middle: bl/roof.py's top surface of the plane it lies in, plus the curb."""
    x0, x1, z0, z1 = rect
    return round(ROOF.top(plane, (x0 + x1) / 2, (z0 + z1) / 2) + SKY_GLASS_UP, 3)


def skylight_row(windows, wid, name, rect, plane, kind, node):
    """The skylight `wid` of the schedule over the plan rectangle `rect`, in place or appended: `start` / `end` /
    `width` along x, `height` along z, `c` and p[1] the height of the glass at its middle."""
    x0, x1, z0, z1 = rect
    y = sky_y(plane, rect)
    w = next((v for v in windows if v['id'] == wid), None)
    if w is None:
        w = {'id': wid}
        windows.append(w)
    w.update(name=name, axis='roof', c=y, start=r4(x0), end=r4(x1), width=r4(x1 - x0), height=r4(z1 - z0), sill=None,
             head=None, type=kind, node=node, kind='skylight', basis='P',
             p=[round((x0 + x1) / 2, 3), y, round((z0 + z1) / 2, 3)], ceiling=8,
             panes=[{'width': r4(x1 - x0), 'height': r4(z1 - z0)}])
    return w


def skylights(windows):
    """The five skylights (bl/revision_spec.py KITCHEN_SKY, LIVING_SKY, FOYER_SKY, PRIMARY_BATH_SKY), each on the roof
    plane bl/roof.py puts over it: 'E' the main roof's east plane, 'EnE' the entry roof's east slope, 'W' the west
    plane. The kitchen's keeps the owner's place over the sink and takes the size of the sheet's outline; the living
    room's is the sheet's own, new in the eighth round."""
    def size(rect):
        return f'{fi(rect[1] - rect[0])} x {fi(rect[3] - rect[2])}'
    taken = next((w for w in windows if w['id'] == LIVING_SKYLIGHT), None)
    if taken is not None and taken.get('kind') != 'skylight':
        raise SystemExit('measurements.json: window tag %s is taken by %r' % (LIVING_SKYLIGHT, taken['name']))
    skylight_row(windows, 'W16', 'Kitchen skylight', RV.KITCHEN_SKY, 'E',
                 f'Roof glazing on the east-facing roof plane, {size(RV.KITCHEN_SKY)}, over the sink / dishwasher run',
                 'K0')
    for i, rect in enumerate(RV.FOYER_SKY):
        skylight_row(windows, f'W{18 + i}', f'Foyer skylight {"(hall)" if i == 0 else "(vaulted entry)"}', rect, 'EnE',
                     f'Roof glazing on the entry roof\'s east slope, {size(rect)}', 'H1' if i == 0 else 'E0')
    skylight_row(windows, 'W20', 'Primary bathroom skylight (over the shower)', RV.PRIMARY_BATH_SKY, 'W',
                 f'Roof glazing on the west roof plane, {size(RV.PRIMARY_BATH_SKY)}, over the shower', 'A0')
    skylight_row(windows, LIVING_SKYLIGHT, 'Living room skylight', RV.LIVING_SKY, 'E',
                 f'Roof glazing on the east-facing roof plane, {size(RV.LIVING_SKY)}, over the sofa side of the living '
                 'room, where the architect\'s sheet draws it', 'L0')


def sash_panes(width, height, mullion=None, start=0.0):
    """Daylight of the two sashes of a window rebuilt by the eighth round (bl/revisions._glz_window): the frame and a
    sash stile at each jamb, sill and head, one mullion between the sashes (in the middle unless `mullion` gives its
    centre line, measured like `start`, the opening's first jamb)."""
    edge, half = RV.GLAZING_WIN_FRAME + RV.GLAZING_WIN_SASH, RV.GLAZING_WIN_MULLION / 2
    m = (width / 2) if mullion is None else (mullion - start)
    return [{'width': r4(m - half - edge), 'height': r4(height - 2 * edge)},
            {'width': r4(width - m - half - edge), 'height': r4(height - 2 * edge)}]


def slider_panes(x, n, head):
    """Daylight of each panel of a sliding glass door (bl/revisions._glz_slider): stiles and top rail GLAZING_STILE,
    bottom rail GLAZING_RAIL_BOTTOM, the panel standing 0.01 ft above the threshold under the 2 in head."""
    w = RV.slider_panels(x, n)[0]
    h = (head - RV.GLAZING_FRAME - RV.GLAZING_STILE) - (RV.GLAZING_THRESHOLD + 0.01 + RV.GLAZING_RAIL_BOTTOM)
    return [{'width': r4(w[2] - w[1] - 2 * RV.GLAZING_STILE), 'height': r4(h)}] * n


def round8_windows(meas):
    """The windows after the round: the openings rebuilt at the sheet's sizes, the three that are gone, the two
    sidelights of the front door. Returns the ids that left the schedule."""
    gone = ['W03', 'W04', 'W06'] + ([] if RV.BED3_WEST_WINDOW else ['W10'])
    win = {w['id']: w for w in meas['windows']}
    for need in ('W01', 'W02', 'W05', 'W07', 'W12', 'W14', 'W15', 'W17'):
        if need not in win:
            raise SystemExit('measurements.json has no window %s' % need)
    left = [g for g in gone if g in win]
    meas['windows'][:] = [w for w in meas['windows'] if w['id'] not in gone]

    def span(wid, c, ab, sill, head, **more):
        win[wid].update(c=r4(c), start=r4(ab[0]), end=r4(ab[1]), width=r4(ab[1] - ab[0]), sill=sill, head=head,
                        height=r4(head - sill))
        win[wid].update(more)
    y0, y1 = RV.GLAZING_WIN_Y
    sx, bx, pz, ez, dz = RV.SLIDER_X, RV.BED2_REAR_WIN_X, RV.PRIMARY_WEST_WIN_Z, RV.LIVING_EAST_WIN_Z, RV.DINING_EAST_WIN_Z
    span('W01', RV.REAR_WALL_C, sx, 0, RV.SLIDER_HEAD, panes=slider_panes(sx, 2, RV.SLIDER_HEAD),
         clear_start=r4(RV.slider_clear(sx)[0]), clear_end=r4(RV.slider_clear(sx)[1]))
    span('W02', RV.REAR_WALL_C, bx, RV.TALL_SILL, 8.0, panes=sash_panes(bx[1] - bx[0], 8.0 - RV.TALL_SILL))
    span('W15', RV.WEST_WALL_C, pz, y0, y1, panes=sash_panes(pz[1] - pz[0], y1 - y0))
    sz = RV.PRIMARY_WEST_WIN_S_Z        # W14, the owner's second west window: its opening stays, the unit is W15's
    span('W14', RV.WEST_WALL_C, sz, y0, y1, panes=sash_panes(sz[1] - sz[0], y1 - y0))
    span('W05', RV.EAST_WALL_C, ez, y0, y1, panes=sash_panes(ez[1] - ez[0], y1 - y0), name='Living / east')
    span('W07', RV.EAST_WALL_C, dz, y0, y1, name='Living / dining east',
         panes=sash_panes(dz[1] - dz[0], y1 - y0, RV.DINING_EAST_WIN_MULLION, dz[0]))
    b0, b1 = RV.BED4_WEST_WIN_Y
    span('W12', RV.WEST_WALL_C, RV.BED4_WEST_WIN_Z, b0, b1)
    w17 = win['W17']                    # the window over the front door keeps its place: the wall's old ends
    span('W17', G.FRONT_DOOR['c'], G.FRONT_DOOR_OLD_X, w17['sill'], w17['head'])
    for wid, (a, b), side in zip(SIDELIGHTS, G.FRONT_DOOR_SIDELIGHTS, ('west', 'east')):
        name = f'Front door sidelight ({side})'
        row = next((v for v in meas['windows'] if v['id'] == wid), None)
        if row is not None and row['name'] != name:
            raise SystemExit('measurements.json: window tag %s is taken by %r' % (wid, row['name']))
        if row is None:
            row = {'id': wid}
            meas['windows'].append(row)
        sill, head = G.FRONT_DOOR_SIDELIGHT_RAIL_Y, G.DOOR_HEAD - G.HEAD_TRIM[0]
        row.update(name=name, axis=G.FRONT_DOOR['axis'], c=r4(G.FRONT_DOOR['c']), start=r4(a), end=r4(b),
                   width=r4(b - a), height=r4(head - sill), sill=sill, head=r4(head), type='', node='E0',
                   kind='window', basis='P', panes=[{'width': r4(b - a), 'height': r4(head - sill)}])
    return left


def round8_rooms(meas, doors):
    """Rooms after the round: Bedroom 2 without its entry alcove and with its closet as a room of its own (M15),
    Bedroom 3's bath and closet as on the sheet, and the notes that quoted an old size or layout (audit F55).
    Returns the rows that changed, by id."""
    rooms = meas['rooms']
    by_id = {r['id']: r for r in rooms}
    for need in (BED2, SHARED_BATH, BED3, BEDROOM_3_BATH, BED3_CLOSET_ROOM, BEDROOM_4_CLOSET):
        if need not in by_id:
            raise SystemExit('measurements.json has no room %s' % need)
    taken = by_id.get(BED2_CLOSET_ROOM)
    if taken is not None and taken['name'] != 'Bedroom 2 closet':
        raise SystemExit('measurements.json: room tag %s is taken by %r' % (BED2_CLOSET_ROOM, taken['name']))

    def w(did):
        return ft(doors[did]['width'])
    b2 = by_id[BED2]
    b2['name'] = 'Bedroom 2'            # (the concept: "Bedroom 2 · main bay", with an entry alcove beside its closet)
    b2['note'] = ('Clear interior size; excludes walls. Entered from the hall through the hinged door D12 '
                  f'({w("D12")}) in its south wall, as on the architect\'s sheet; the reach-in closet '
                  f'{BED2_CLOSET_ROOM} opens off the same wall behind two sliding panels (D13). The rear window W02 '
                  f'runs from a {ft(RV.TALL_SILL)} sill to the ceiling.')
    cx0, cx1, cz0, cz1 = RV.BED2_CLOSET_CLEAR
    closet2 = room_row(
        BED2_CLOSET_ROOM, 'Bedroom 2 closet', RV.BED2_CLOSET_CLEAR, 'B2',
        f'Clear interior size; excludes walls. A reach-in closet along Bedroom 2\'s south wall, {ft(cx1 - cx0)} wide '
        f'and {ft(cz1 - cz0)} deep, behind two bypass sliding panels in a {w("D13")} opening (D13): shelf, hanging '
        'rod and a shelf tower at the east end. Behind it, in the same block, stand the furnace closet and the '
        f'storage closet, which open onto the hall ({FAU_DOOR}, {STO_DOOR}).')
    upsert(rooms, closet2)
    by_id[SHARED_BATH]['note'] = ('Clear interior size; excludes walls. Entered from the hall through the hinged door '
                                  f'D07 ({w("D07")}) in its north wall.')
    by_id[BED3]['note'] = ('Clear interior size; excludes walls and the bay, which is glazed to the floor. Vaulted '
                           f'ceiling, {ft(ROOF.BED3_SPRING)} at the side walls and '
                           f'{ft(ROOF.bed3_vault(ROOF.WING_X))} at the ridge. '
                           + ('' if RV.BED3_WEST_WINDOW else 'The west wall behind the bed is solid, as on the '
                              'architect\'s sheet. ')
                           + f'The room is entered through the hinged door D03 ({w("D03")}); the bathroom door D05 '
                           'and the closet\'s sliding panels D06 are in its north wall.')
    sx0, sx1, _, _ = RV.BED3_BATH_SHOWER
    t0, t1 = RV.BED3_BATH_TOILET_BAY_X
    vx0, vx1, _, _ = RV.BED3_BATH_VANITY
    (ws, wh), (wz0, wz1) = RV.BED3_BATH_WIN_Y, RV.BED3_BATH_WIN_Z
    by_id[BEDROOM_3_BATH]['note'] = (
        'Clear interior size; excludes walls. Laid out as on the architect\'s sheet: a shower '
        f'{ft(sx1 - sx0)} wide across the west end behind a fixed glass panel, the wall-hung toilet in a '
        f'{ft(t1 - t0)} bay and the vanity in a {ft(vx1 - vx0)} bay on the north wall, and the hinged door D05 '
        f'({w("D05")}) at the east end of the south wall. The shower window W11 on the west wall is {ft(wz1 - wz0)} '
        f'wide and runs from a {ft(ws)} sill to a {ft(wh)} head ({ft(wh - ws)} tall), in obscured glass with a white '
        'frame and white grid bars.')
    c3 = by_id[BED3_CLOSET_ROOM]
    c3['name'] = 'Bedroom 3 closet'      # (the concept: "Bedroom 3 compact closet", a step-in closet behind a pocket door)
    c3['node'] = 'B3'                   # nobody can stand in it: it is seen from Bedroom 3's stop, like M12 from B4
    c3['note'] = ('Clear interior size; excludes walls. A reach-in closet off Bedroom 3 behind two bypass sliding '
                  f'panels of {ft(RV.BED3_CLOSET_PANEL_W)} in a {w("D06")} opening (D06), fitted with a drawer and '
                  'shelf tower, a double-hang bay and an open shelf tower.')
    c4, d16 = by_id[BEDROOM_4_CLOSET], doors['D16']
    c4['note'] = (f'Clear interior size; excludes walls. A reach-in closet off Bedroom 4 behind two bypass sliding '
                  f'panels in a {ft(d16["width"])} opening (D16). Flat 8 ft ceiling.')
    return {r['id']: r for r in (b2, closet2, by_id[SHARED_BATH], by_id[BED3], by_id[BEDROOM_3_BATH], c3, c4)}


def porch_risers():
    """The two risers at the front entry in words: front walk -> porch slab -> house floor (the slab is
    bl/zones/exterior_layout.py PORCH_TOP; half way since the round's repairs, A1.3's existing porch was 4 in below
    the floor)."""
    up, door = in8(SITE.PORCH_TOP - SITE.GRADE_FRONT), in8(-SITE.PORCH_TOP)
    if up == door:
        return f'two equal risers of {up} in, one from the front walk up to the slab and one at the door'
    return f'a riser of {up} in from the front walk up to the slab and one of {door} in at the door'


def round8_spaces():
    """`spaces` of the schedule: what the plan shows but the schedule does not measure as a room (no tag, no sweep of
    its own). `kind`: 'closet' (drawn with a fill and a small label), 'hall' (a label), 'level' (a floor that is not
    the house floor: the garage, the porch), 'step' and 'landing' (outlines). `floor` is the level of its floor
    against the house floor."""
    def row(key, kind, name, rect, note, **more):
        x0, x1, z0, z1 = rect
        out = {'key': key, 'kind': kind, 'name': name, 'bounds_ft': [r4(x0), r4(x1), r4(z0), r4(z1)],
               'width_ft': r4(x1 - x0), 'depth_ft': r4(z1 - z0), 'area_sqft': round((x1 - x0) * (z1 - z0), 2),
               'note': note}
        out.update(more)
        return out
    hw, he = RV.HALL_WEST, RV.HALL_EAST
    low, rise = in8(-G.FLOOR_Y), in8(-G.STEP_Y)
    d0, d1, dz0, dz1 = SITE.DECK
    risers = f'{SITE.STEP_RISERS} risers of {in8(SITE.STEP_RISE)} in'
    tread = in8(SITE.STEP_W)
    porch = SITE.PORCH
    return [
        row('fau', 'closet', 'Furnace closet', RV.FAU_CLEAR,
            f'Furnace (FAU) closet in the closet block between Bedroom 2 and the hall, behind the louvred door '
            f'{FAU_DOOR} in the block\'s west wall. Shown closed; not on the tour.', label='FAU', door=FAU_DOOR),
        row('sto', 'closet', 'Storage closet', RV.STO_CLEAR,
            f'Storage closet in the same block, behind the door {STO_DOOR} in the block\'s south wall. Shown closed; '
            'not on the tour.', label='STO', door=STO_DOOR),
        row('hall_west', 'hall', 'Hall, west leg', hw,
            f'The hall beside the closet block, {ft(hw[1] - hw[0])} wide: the primary suite\'s entry D09 in its west '
            f'wall, Bedroom 2\'s door D12 at its north end, the furnace closet\'s door {FAU_DOOR} in its east wall.',
            label=f'HALL {ft(hw[1] - hw[0])}'),
        row('hall_east', 'hall', 'Hall, east leg', he,
            f'The hall south of the closet block, {ft(he[3] - he[2])} wide, open to the living room at its east end '
            'and to the passage to the foyer on its south side.', label=f'HALL {ft(he[3] - he[2])}'),
        row('garage', 'level', 'Garage', _GAR,
            f'Clear interior size. The floor is {low} in below the house floor and the ceiling {fi(G.CEILING_Y - G.FLOOR_Y)} '
            f'above it. Water heater: a {fi(G.WATER_HEATER_D)} tank on a stand in the north-east corner.',
            floor=r4(G.FLOOR_Y), ceiling=r4(G.CEILING_Y)),
        row('garage_step', 'step', 'Garage step at the house door', G.STEP,
            f'One step between the house floor and the garage floor: two risers of {rise} in.', floor=r4(G.STEP_Y)),
        row('porch', 'level', 'Covered porch', porch,
            f'Porch slab {in8(-SITE.PORCH_TOP)} in below the house floor, with {porch_risers()}, under the entry '
            f'roof\'s gable, which runs on {fi(ROOF.ENTRY_FRONT - porch[3])} past the slab.',
            floor=r4(SITE.PORCH_TOP)),
        row('landing_living', 'landing', 'Rear landing, living room', SITE.DECK,
            f'Ipe landing outside the living room\'s sliding door D14, {in8(-SITE.DECK_TOP)} in below the house '
            f'floor, with one step {tread} in deep round its three open sides ({risers} down to the garden).',
            floor=r4(SITE.DECK_TOP), step_floor=r4(SITE.STEP_TOP), step_width=r4(SITE.STEP_W)),
        row('landing_primary', 'landing', 'Rear landing, primary bedroom', SITE.LANDING,
            f'Ipe landing outside the primary bedroom\'s sliding door W01, built like the living room\'s.',
            floor=r4(SITE.DECK_TOP), step_floor=r4(SITE.STEP_TOP), step_width=r4(SITE.STEP_W)),
    ]


def round8_overall():
    """`overall` of the schedule: the house's outside sizes (relayout.OUTER_SIZE) and its levels."""
    return {'outer_width_ft': r4(R.OUTER_SIZE[0]), 'outer_depth_ft': r4(R.OUTER_SIZE[1]),
            'outer_depth_garage_side_ft': r4(R.OUTER_SIZE[2]), 'wall_thickness_ft': r4(R.WALL),
            'floor_above_ground_front_ft': r4(-SITE.GRADE_FRONT), 'floor_above_ground_rear_ft': r4(-SITE.GRADE_REAR),
            'garage_floor_ft': r4(G.FLOOR_Y), 'porch_floor_ft': r4(SITE.PORCH_TOP),
            'main_ridge_ft': r4(ROOF.MAIN_Y), 'garage_ridge_ft': r4(ROOF.GAR_Y), 'entry_ridge_ft': r4(ROOF.ENTRY_Y),
            'roof_pitch_in_12': r4(ROOF.P * 12), 'eave_overhang_ft': r4(ROOF.OVH),
            'note': f'Outside faces of the walls: {fi(R.OUTER_SIZE[0])} wide, {fi(R.OUTER_SIZE[1])} deep on the '
                    f'Bedroom 3 side and {fi(R.OUTER_SIZE[2])} on the garage side, as on the architect\'s sheet '
                    f'SKA002; every wall {in8(R.WALL)} in thick. Heights are above the house floor.'}


# ------------------------------------------------------------------------------------------- eighth round: SCENE objects
def scene_box(o):
    """(x0, x1, y0, y1, z0, z1) of a SCENE box that is not turned (reshape() works on these)."""
    if o.get('shape') != 'box' or abs(o.get('rot') or 0) > 1e-6:
        raise SystemExit('%s: %r is not an axis-aligned box' % (ROUND8, o.get('name')))
    return box_of(o)


def put_box(o, box):
    """Give a SCENE box the faces (x0, x1, y0, y1, z0, z1); an axis whose faces are there already keeps its numbers."""
    old = scene_box(o)
    for k in range(3):
        lo, hi = box[2 * k], box[2 * k + 1]
        if hi - lo < 0.005:
            raise SystemExit('%s: %r would be %.4f ft along %s' % (ROUND8, o.get('name'), hi - lo, 'xyz'[k]))
        if abs(lo - old[2 * k]) >= SAME or abs(hi - old[2 * k + 1]) >= SAME:
            o['p'][k], o['s'][k] = r4((lo + hi) / 2), r4(hi - lo)


class Round8Scene:
    """The scene's objects as the eighth round leaves them. Existing objects are addressed BY INDEX, because walls
    that are cut into several pieces share one name ("Living — rear wall" seven times); the name at that index is
    checked, so a scene that is not the concept's stops the tool. Objects keep their index: a piece the build no
    longer has is marked removed (group 'removed', the old group in `group_was`), never deleted."""

    def __init__(self, objs):
        self.objs = objs
        self.reshaped, self.gone, self.added = [], [], []

    def at(self, i, name, group=None):
        o = self.objs[i] if i < len(self.objs) else None
        if o is None or o.get('name') != name:
            raise SystemExit('%s: scene object %d is %r, expected %r' % (ROUND8, i, o and o.get('name'), name))
        g = o.get('group_was', o.get('group'))
        if group is not None and g != group:
            raise SystemExit('%s: scene object %d %r is in group %r, expected %r' % (ROUND8, i, name, g, group))
        if o.get('removed'):            # a re-run: the mark is taken back when the piece is used after all
            o['group'] = o.pop('group_was')
            del o['removed']
        return o

    def run(self, i, name, axis, a=None, b=None, y=None, group='walls'):
        """Wall piece `i`: its ends along `axis` ('x' | 'z') become a .. b (None keeps an end) and its height y."""
        o = self.at(i, name, group)
        box = list(scene_box(o))
        k = 'xyz'.index(axis) * 2
        box[k] = box[k] if a is None else a
        box[k + 1] = box[k + 1] if b is None else b
        if y is not None:
            box[2], box[3] = y
        put_box(o, box)
        self.reshaped.append(i)
        return tuple(box)

    def box(self, i, name, box, group='walls'):
        put_box(self.at(i, name, group), box)
        self.reshaped.append(i)

    def leaf(self, i, name, leaf):
        """Door leaf `i` takes the place of its successor (a dict of the spec with `center`, `size`, `rot`)."""
        o = self.at(i, name, 'door')
        o['p'], o['s'] = [r4(v) for v in leaf['center']], [r4(v) for v in leaf['size']]
        o['rot'] = round(leaf['rot'], 6) or 0
        self.reshaped.append(i)

    def remove(self, i, name, why):
        """Mark piece `i` as gone from the built model. `name`: its name, or a tuple of the names it may have."""
        o = self.objs[i] if i < len(self.objs) else None
        names = name if isinstance(name, tuple) else (name,)
        if o is None or o.get('name') not in names:
            raise SystemExit('%s: scene object %d is %r, expected %s' % (ROUND8, i, o and o.get('name'),
                                                                        ' or '.join(repr(n) for n in names)))
        if o.get('group') != 'removed':
            o['group_was'], o['group'] = o['group'], 'removed'
        o['removed'] = '%s: %s' % (ROUND8, why)
        self.gone.append(i)

    def add(self, name, box, look, rot=0, **more):
        """Append the box `name` (or update it in place on a re-run)."""
        x0, x1, y0, y1, z0, z1 = box
        row = dict({'name': name, 'p': [r4((x0 + x1) / 2), r4((y0 + y1) / 2), r4((z0 + z1) / 2)],
                    's': [r4(x1 - x0), r4(y1 - y0), r4(z1 - z0)]}, **look, rot=rot, **BOX_LOOK)
        row.update(more)
        self.added.append(upsert(self.objs, row, key='name'))

    def add_leaf(self, leaf, look=None):
        row = dict({'name': leaf['name'], 'p': [r4(v) for v in leaf['center']], 's': [r4(v) for v in leaf['size']]},
                   **(look or LEAF_LOOK), rot=round(leaf['rot'], 6) or 0, **BOX_LOOK)
        self.added.append(upsert(self.objs, row, key='name'))


def round8_walls(sc):
    """Wall boxes as built: the rear wall, the east wall and the primary bedroom's west wall around the openings of
    "v7 glazing"; Bedroom 2's closet block, the hall and the shared bath ("v7 hall"); Bedroom 3's north wall and
    entry, Bedroom 4's and Bedroom 3's west wall ("v7 bedrooms"); the garage's walls, the front door wall and their
    stucco skins (bl/garage_spec.py); the wall corners the site work closed. A window's wall is three pieces in the
    concept (the wall below it, the wall above it, the solid wall beside it); where the build made a new piece in
    place of an old one, the old object takes the new piece's box."""
    objs = sc.objs
    top = 8.0
    # ---- rear wall
    rear, prim, liv = 'Primary — rear wall', 'Bedroom 2 — rear wall', 'Living — rear wall'
    s0, s1 = RV.SLIDER_X
    sc.run(1777, rear, 'x', None, s0)
    sc.remove(1778, rear, 'the wall below the window that the first round made a sliding door')
    sc.run(1779, rear, 'x', s0, s1, (RV.SLIDER_HEAD, top))                # above the primary sliding door
    sc.run(1786, rear, 'x', s1, None)
    w0, w1 = RV.BED2_REAR_WIN_X
    sc.run(1787, prim, 'x', None, w0)
    sc.run(1788, prim, 'x', w0, w1, (0.0, RV.TALL_SILL))                  # below the rear window W02
    sc.remove(1789, prim, 'the wall above W02, which runs to the ceiling since the first round')
    sc.run(1796, prim, 'x', w1, None)
    l0, l1 = RV.LIVING_SLIDER_X
    sc.run(1797, liv, 'x', None, l0)
    sc.run(1798, liv, 'x', l0, l1, (RV.LIVING_SLIDER_HEAD, top))          # above the living room's sliding door
    for i in (1807, 1808, 1809, 1815, 1816, 1817):
        sc.remove(i, liv, 'piers, sills and heads of the garden door and the two fixed lights; one sliding door now')
    sc.run(1823, liv, 'x', l1, None)
    # ---- the primary bedroom's west wall, W15
    west = 'Primary — west wall'
    p0, p1 = RV.PRIMARY_WEST_WIN_Z
    y0, y1 = RV.GLAZING_WIN_Y
    sc.run(1824, west, 'z', None, p0)
    sc.run(1825, west, 'z', p0, p1, (0.0, y0))
    sc.run(1826, west, 'z', p0, p1, (y1, top))
    sc.run(3180, 'Primary west wall — north of added window', 'z', p1, None)
    sc.remove(3168, 'Primary bathroom west wall — above privacy window',
              'the wall above W13, which runs to the ceiling since the first round')
    # ---- east wall: W05 (one unit in place of W05, the pier and W06) and W07
    east = 'Living / kitchen — east wall'
    e0, e1 = RV.LIVING_EAST_WIN_Z
    d0, d1 = RV.DINING_EAST_WIN_Z
    sc.run(1855, east, 'z', None, e0)
    sc.run(1856, east, 'z', e0, e1, (0.0, y0))
    sc.run(1857, east, 'z', e0, e1, (y1, top))
    for i in (1864, 1865, 1866):
        sc.remove(i, east, 'the pier between W05 and W06 and the wall below and above W06; W05 is one unit now')
    sc.run(1873, east, 'z', e1, d0)
    sc.run(1874, east, 'z', d0, d1, (0.0, y0))
    sc.run(1875, east, 'z', d0, d1, (y1, top))
    sc.run(4203, 'Kitchen east wall beside arch', 'z', d1, None)
    # ---- Bedroom 2's closet block, the hall, the shared bath (RV.hall_block_walls: name -> shell piece | None, box)
    used = {}
    for key, (src, box) in RV.hall_block_walls().items():
        if src is None:
            sc.add(key, box, WALL_LOOK)
            continue
        found = named(objs, src, 'walls')
        k = used.get(src, 0)
        used[src] = k + 1
        if k >= len(found):
            raise SystemExit('%s: the scene has %d wall boxes named %r, the hall block needs %d'
                             % (ROUND8, len(found), src, k + 1))
        o = objs[found[k]]
        if (box_of(o)[2] > 1.0) != (box[2] > 1.0):                     # a header stays a header, a wall a wall
            raise SystemExit('%s: scene object %d %r is %s, the hall block wants %s there' % (
                ROUND8, found[k], src, 'a header' if box_of(o)[2] > 1.0 else 'a wall', key))
        sc.box(found[k], src, box)
    for src, k in used.items():
        if k != len(named(objs, src, 'walls')):
            raise SystemExit('%s: %d wall boxes named %r in the scene, the hall block has %d'
                             % (ROUND8, len(named(objs, src, 'walls')), src, k))
    sc.remove(1884, 'Bedroom 2 entry return', 'the wall south of the entry alcove; the alcove is hall now')
    # ---- Bedroom 3: the wall to its bath and closet, its entry
    for name, box in RV.bed3_north_walls().items():
        found = named(objs, name, 'walls')
        if len(found) != 1:
            raise SystemExit('%s: expected one wall box named %r in the scene, found %d' % (ROUND8, name, len(found)))
        sc.box(found[0], name, box)
    for i, name in ((3357, 'Ensuite pocket cavity face'), (3358, 'Ensuite pocket cavity face'),
                    (3364, 'Walk-in closet pocket cavity face'), (3365, 'Walk-in closet pocket cavity face')):
        sc.remove(i, name, 'pocket of a pocket door; the bath has a hinged door and the closet sliding panels')
    ln = RV.DOOR_LINER
    b0, b1 = RV.BED3_ENTRY_Z[0] - ln, RV.BED3_ENTRY_Z[1] + ln
    sc.run(3345, 'Suite 3 services / hall wall', 'z', None, b0)
    sc.run(3347, 'Bedroom 3 entry header', 'z', b0, b1)
    sc.run(3346, 'Bedroom 3 entry south jamb', 'z', b1, None)
    # ---- west wall of Bedroom 4 (W12, 5'-0" centred) and of Bedroom 3 (W10: no window)
    b4 = 'Bedroom 4 west addition'
    c0, c1 = RV.BED4_WEST_WIN_Z
    cy0, cy1 = RV.BED4_WEST_WIN_Y
    sc.run(1886, b4, 'z', None, c0)
    sc.run(1887, b4, 'z', c0, c1, (0.0, cy0))
    sc.run(1888, b4, 'z', c0, c1, (cy1, top))
    sc.run(1895, b4, 'z', c1, None)
    if not RV.BED3_WEST_WINDOW:
        sc.run(3381, 'Bedroom 3 side window sill wall', 'z', None, None, (0.0, top))    # the wall closes the opening
        sc.remove(3382, 'Bedroom 3 side window head wall', 'W10 is closed: the sill wall runs to the ceiling')
    # ---- garage: side door (east wall), vehicle door header, house door
    r0, r1 = G.SIDE_DOOR['ro']
    side = sc.run(1896, 'Garage — east side', 'z', r1, None)
    north = named(objs, 'Kitchen / garage separation', 'walls')
    if len(north) != 1:
        raise SystemExit('%s: expected one wall box named %r in the scene' % (ROUND8, 'Kitchen / garage separation'))
    z_n = sum(box_of(objs[north[0]])[4:6]) / 2                         # the east wall starts on that wall's centre line
    sc.add('Garage — east side (north of the side door)', (side[0], side[1], 0.0, top, z_n, r0), WALL_LOOK)
    sc.add('Garage — east side (over the side door)', (side[0], side[1], G.SIDE_DOOR['head'], top, r0, r1), WALL_LOOK)
    front = 'Garage — front / vehicle door'
    sc.run(1897, front, 'x', None, G.VEHICLE_RO_X[0])
    sc.run(1898, front, 'x', G.VEHICLE_RO_X[0], G.VEHICLE_RO_X[1], (G.VEHICLE_HEAD_Y, top))
    sc.run(1900, front, 'x', G.VEHICLE_RO_X[1], None)
    skin = 'Front stucco · ' + front
    sc.run(5339, skin, 'x', None, G.VEHICLE_RO_X[0], group='facade')
    sc.run(5340, skin, 'x', G.VEHICLE_RO_X[0], G.VEHICLE_RO_X[1], (G.VEHICLE_HEAD_Y, top), group='facade')
    sc.run(5341, skin, 'x', G.VEHICLE_RO_X[1], None, group='facade')
    door = sc.at(1899, front, 'garageDoor')                              # the door itself, between the jamb boards
    dz = scene_box(door)
    put_box(door, (G.VEHICLE_DOOR_X[0], G.VEHICLE_DOOR_X[1], G.FLOOR_Y, G.VEHICLE_HEAD_Y, dz[4], dz[5]))
    sc.reshaped.append(1899)
    h0, h1 = G.HOUSE_DOOR['ro']
    sc.run(3312, 'Garage interior access — north infill wall', 'z', None, h0)
    sc.run(3314, 'Garage interior access — header', 'z', h0, h1)
    sc.run(3313, 'Garage interior access — south wall', 'z', h1, None)
    # ---- front door wall: the unit takes the foyer less 3 in each side; the band over it runs across the unit
    u0, u1 = G.FRONT_DOOR_UNIT
    o0, o1 = G.FRONT_DOOR_OLD_X
    ya, yb, yc = G.FRONT_DOOR_BAND_Y
    west_w = sc.run(3300, 'Centered front entrance — west wall', 'x', None, u0)
    sc.run(3301, 'Centered front entrance — east wall', 'x', u1, None)
    sc.run(4136, 'Entry transom structural band', 'x', u0, u1, (ya, yb))
    sc.add('Entry transom structural band (west of the entry window)', (u0, o0, yb, yc, west_w[4], west_w[5]), WALL_LOOK)
    sc.add('Entry transom structural band (east of the entry window)', (o1, u1, yb, yc, west_w[4], west_w[5]), WALL_LOOK)
    west_s = sc.run(5342, 'Front stucco · Centered front entrance — west wall', 'x', None, u0, group='facade')
    sc.run(5343, 'Front stucco · Centered front entrance — east wall', 'x', u1, None, group='facade')
    sc.run(5344, 'Front stucco · Entry transom structural band', 'x', u0, u1, (ya, yb), group='facade')
    sc.add('Front stucco · Entry transom structural band (west of the entry window)',
           (u0, o0, yb, yc, west_s[4], west_s[5]), STUCCO_LOOK)
    sc.add('Front stucco · Entry transom structural band (east of the entry window)',
           (o1, u1, yb, yc, west_s[4], west_s[5]), STUCCO_LOOK)
    # ---- the foyer's west wall beside the porch: cut in the middle of the front door wall, where the wall's finish
    # changes from paint (foyer) to the porch's cladding (bl/revisions.site_shell)
    porch_wall = 'Bedroom 3 / recessed porch exterior'
    zc = (R.Z_FOYER_S + R.Z_PORCH_N) / 2
    pw = sc.at(3352, porch_wall, 'walls')
    pb = scene_box(pw)
    foyer_end = pb[4] if pb[4] < zc - HOST_TOL else next(
        (box_of(o)[4] for o in objs if o.get('name') == porch_wall + ' · foyer'), pb[4])
    sc.run(3352, porch_wall, 'z', zc, None)
    sc.add(porch_wall + ' · foyer', (pb[0], pb[1], pb[2], pb[3], foyer_end, zc), WALL_LOOK)
    # ---- wall corners. A wall box ends on the centre line of the wall it meets, which leaves a square open at every
    # outside corner; the build closes six of them with stucco pieces (bl/revisions.site_shell: the three "stucco
    # front corner return" pieces and three copies), and the foyer's corner at the kitchen wall with an infill.
    cz_b3 = (R.Z_B3_S + R.Z_B3_OUT - R.STUCCO) / 2                      # centre lines of the front walls' shell boxes
    cz_gar = (R.Z_GAR_S + R.Z_GAR_OUT - R.STUCCO) / 2
    ret = 'stucco front corner return'
    sc.box(5350, ret, (R.XW_OUT, R.WEST_C, 0.0, top, cz_b3, R.Z_B3_OUT), 'facade')
    sc.box(5351, ret, (sum(R.FOYER_WALL) / 2, R.X_FOYER_W, 0.0, top, cz_b3, R.Z_B3_OUT), 'facade')
    sc.box(5352, ret, (R.EAST_C, R.XE_OUT, 0.0, top, cz_gar, R.Z_GAR_OUT), 'facade')
    sc.add(ret + ' · rear west', (R.XW_OUT, R.WEST_C, 0.0, top, R.ZN_OUT, R.REAR_C), STUCCO_LOOK)
    sc.add(ret + ' · rear east', (R.EAST_C, R.XE_OUT, 0.0, top, R.ZN_OUT, R.REAR_C), STUCCO_LOOK)
    sc.add(ret + ' · garage front, porch side', (R.X_FOYER_E, (R.X_FOYER_E + R.X_GAR_W) / 2, 0.0, top, cz_gar,
                                                 R.Z_GAR_OUT), STUCCO_LOOK)
    fx0, fx1, fz0, fz1 = RV.FOYER_CORNER_INFILL
    sc.add('Foyer corner infill (garage west wall / kitchen wall)', (fx0, fx1, 0.0, top, fz0, fz1), WALL_LOOK)
    for i in range(5308, 5312):
        sc.remove(i, 'Coordinated entry high-window surround', 'the entry roof and its front gable are rebuilt')


def round8_leaves(sc):
    """Door leaves and sliding panels as shown. A door that is still there keeps its leaf object, at its new place;
    the leaves of new doors, the second panel of each pair of closet panels and the panels of the two sliding glass
    doors are appended."""
    sc.leaf(3306, 'Centered front entrance — oak door open inward', G.leaf(G.FRONT_DOOR))
    sc.leaf(3319, 'Garage interior access — solid door open into garage', G.leaf(G.HOUSE_DOOR))
    sc.leaf(3344, 'Bedroom 4 revised 32 inch entry door open inward', RV.bed4_entry_leaf())
    sc.leaf(3351, 'Bedroom 3 entry door open inward', RV.bed3_entry_leaf())
    sc.leaf(3360, 'Ensuite 32 inch pocket door open', RV.bed3_bath_door_leaf())       # the bath's hinged leaf now
    front, rear = RV.bed3_closet_panels()
    sc.leaf(3367, 'Walk-in closet 32 inch pocket door open', front)                   # one of the two sliding panels
    sc.add_leaf(rear)
    for leaf in (RV.bed2_door_leaf(), RV.shared_bath_door_leaf(), RV.fau_door_leaf(), RV.sto_door_leaf(),
                 *RV.bed2_closet_panels(), G.leaf(G.SIDE_DOOR)):
        sc.add_leaf(leaf)
    # sliding glass doors: each panel a leaf on its track (fixed panels on the room side, sliding panels outside)
    for name, x, n, head, shown in (('Living room sliding door', RV.LIVING_SLIDER_X, 4, RV.LIVING_SLIDER_HEAD,
                                     RV.LIVING_SLIDER_OPEN), ('Primary bedroom sliding door', RV.SLIDER_X, 2,
                                                              RV.SLIDER_HEAD, (None, 0.0))):
        ya, yb = RV.GLAZING_THRESHOLD + 0.01, head - RV.GLAZING_FRAME
        for tag, a, b, track in RV.slider_panels(x, n, *shown):
            zc = RV.REAR_WALL_C + (RV.GLAZING_TRACK if track == 'inner' else -RV.GLAZING_TRACK)
            sc.add(f'{name} panel {tag}', (a, b, ya, yb, zc - RV.GLAZING_PANEL_T / 2, zc + RV.GLAZING_PANEL_T / 2),
                   dict(LEAF_LOOK, color='#dfe9ea'), material='glass', alpha=0.45)


# Scene objects of openings, trims and roofs that the built model no longer has since the eighth round, as index
# ranges (first, last, the names the objects in it may have, why). Checked against the built model's `scene_index`
# values (the published house.blend has every one of them, the eighth round's build none).
ROUND8_GONE = [
    # v7 glazing: the old units' frames and panes (the new units are appended as panes; their frames are not copied)
    (1790, 1795, r'Bedroom 2 — rear wall', 'frame and pane of the old rear window W02 (rebuilt 6\'-0" wide)'),
    (1799, 1806, r'Living — rear wall|Open glass garden door|Garden door white (stile|rail)',
     'the hinged garden door: one four-panel sliding door now'),
    (1810, 1814, r'Living — rear wall', 'the west fixed light W03: one four-panel sliding door now'),
    (1818, 1822, r'Living — rear wall', 'the east fixed light W04: one four-panel sliding door now'),
    (1827, 1832, r'Primary — west wall', 'frame and pane of the old west window W15 (rebuilt 3\'-0" wide)'),
    (3224, 3224, r'Primary existing west window — deep painted sill', 'the old stool of W15 (rebuilt with the window)'),
    # W14, the primary bedroom's second west window: the shell's unit is replaced by W15's kit in the same opening
    # (bl/revisions.primary_west_window_south). The opening's wall pieces 3180..3183 stay; 3185, 3187, 3190, 3192 and
    # 3200 (casings, apron, latch) are concept pieces no build has had
    (3184, 3184, r'Primary added west window — jamb', 'W14\'s old unit: the window has W15\'s unit now'),
    (3186, 3186, r'Primary added west window — jamb', 'W14\'s old unit: the window has W15\'s unit now'),
    (3188, 3189, r'Primary added west window — head and sill reveal',
     'W14\'s old unit: the window has W15\'s unit now'),
    (3191, 3191, r'Primary added west window — limestone sill', 'W14\'s old sill: a painted stool like W15\'s now'),
    (3193, 3199, r'Primary added west window — (off-white (vertical|horizontal) sash|clear insulated glazing)',
     'W14\'s old sashes and panes (two sashes one above the other): two sashes side by side like W15\'s now'),
    (1858, 1863, r'Living / kitchen — east wall', 'frame and pane of the old W05 (one 6\'-0" unit now)'),
    (1867, 1872, r'Living / kitchen — east wall', 'W06, which is part of W05 now'),
    (1876, 1881, r'Living / kitchen — east wall', 'frame and pane of the old W07 (rebuilt 5\'-0" wide)'),
    (3937, 3937, r'Painted skirting — Bedroom 2 — rear wall', 'baseboard in a rebuilt opening'),
    (3940, 3941, r'Painted skirting — Living — rear wall', 'baseboards between the old rear openings'),
    (3944, 3944, r'Painted skirting — Primary — west wall', 'baseboard in a rebuilt opening'),
    # v7 hall
    (1839, 1841, r'Bedroom 2 upper closet — north', 'casings of the old closet opening'),
    (1847, 1849, r'Original shared bath — north', 'casings of the old doorless bath opening'),
    (3957, 3957, r'Painted skirting — Upper closet — bottom wall KEPT', 'baseboard inside the two small closets now'),
    (3982, 3983, r'Painted skirting — Bedroom 2 entry return', 'baseboards of the removed wall'),
    (3993, 3993, r'Painted skirting — Aligned primary-suite east wall — north', 'it stood in the suite entry'),
    # v7 bedrooms
    (3361, 3363, r'Ensuite pocket jamb|Ensuite head casing', 'casings of the bath\'s pocket door'),
    (3368, 3370, r'Walk-in closet pocket jamb|Walk-in closet head casing', 'casings of the closet\'s pocket door'),
    (4023, 4035, r'Painted skirting — (Suite service wall (west end|middle|east end)|Ensuite pocket cavity face|'
                 r'Walk-in closet pocket cavity face)', 'baseboards of the wall between Bedroom 3 and its bath and closet'),
    (4041, 4044, r'Bedroom door lever( rosette)?', 'levers of the two bedroom doors\' old leaves'),
    # v7 garage
    (3302, 3305, r'Centered front entrance — (west jamb|east jamb|head casing|oak threshold)',
     'casings of the old front door: a unit with sidelights now'),
    (3310, 3311, r'Centered front entrance — bronze lever( rose)?', 'lever of the old front door leaf'),
    (3315, 3318, r'Garage interior access — (north jamb|south jamb|head casing|threshold)',
     'casings of the old house / garage door'),
    (3323, 3324, r'Garage interior access — lever( rose)?', 'lever of the old house / garage door leaf'),
    # v7 site
    (1776, 1776, r'Open front porch paving', 'the porch slab is the floor (bl/zones/exterior_site.py)'),
    (4003, 4003, r'Painted skirting — Centered front entrance — west wall',
     'baseboard on the porch side of the front door wall: no baseboard outdoors (bl/revisions.site_shell)'),
    (4005, 4005, r'Painted skirting — Centered front entrance — east wall',
     'baseboard on the porch side of the front door wall: no baseboard outdoors (bl/revisions.site_shell)'),
    # v7 roof: the concept's roof, its fascia and the entry's stucco gable pieces (bl/roof.py builds the sheets' roof)
    (5124, 5159, r'.*', 'the concept\'s roof planes'),
    (5160, 5261, r'Continuous white perimeter fascia', 'the concept roof\'s fascia'),
    (5262, 5304, r'Shingle ridge / hip cap|Recessed metal valley flashing', 'the concept roof\'s caps and flashing'),
    (5322, 5338, r'Entry stucco gable / roof cheek|Entry white gable bargeboard', 'the lowered entry roof\'s front'),
]
ROUND8_GONE_W10 = [     # only while revision_spec.BED3_WEST_WINDOW is False
    (3383, 3388, r'Bedroom 3 side window (frame|mullion|glazing)', 'W10 is closed: the sheet has a solid wall'),
]


def round8_gone(sc):
    """Mark the scene objects of ROUND8_GONE as removed."""
    for a, b, names, why in ROUND8_GONE + ([] if RV.BED3_WEST_WINDOW else ROUND8_GONE_W10):
        for i in range(a, b + 1):
            o = sc.objs[i]
            if not re.fullmatch(names, o.get('name', '')):
                raise SystemExit('%s: scene object %d is %r, expected a name like %r (ROUND8_GONE)'
                                 % (ROUND8, i, o.get('name'), names))
            sc.remove(i, o['name'], why)


def sash_glass(sc, label, axis, c, span, ys, mull=None):
    """Append the two panes (daylight, sash_panes) of a window the eighth round built with bl/revisions._glz_window:
    `label` glass a / b, on the wall's centre line `c`, between the jambs `span` and sill / head `ys`; `mull` is the
    mullion's centre line when it does not stand in the middle."""
    edge = RV.GLAZING_WIN_FRAME + RV.GLAZING_WIN_SASH
    half_m, t = RV.GLAZING_WIN_MULLION / 2, 0.032
    (a, b), (ya, yb) = span, ys
    m = (a + b) / 2 if mull is None else mull
    for tag, lo, hi in (('a', a + edge, m - half_m), ('b', m + half_m, b - edge)):
        across, along = (c - t / 2, c + t / 2), (lo, hi)
        box = (*along, ya + edge, yb - edge, *across) if axis == 'x' else (*across, ya + edge, yb - edge, *along)
        sc.add(f'{label} glass {tag}', box, GLASS_LOOK, material='glass', alpha=0.35)


def round8_openings(sc):
    """What the scene keeps of the openings besides their walls: Bedroom 4's west window W12, moved and widened as
    bl/zones/bedrooms_rooms.py does it (rails and pane across the new opening, the jamb sections and the centre
    mullion at its ends and its middle); the daylight of every pane the eighth round built, appended as a glass box;
    the five skylights' panes. Returns W12's pane (width, height)."""
    name = 'Bedroom 4 west addition'
    c0, c1 = RV.BED4_WEST_WIN_Z
    for i in (1889, 1890):                                              # sill and head rail
        sc.run(i, name, 'z', c0, c1, group='windows')
    for i, at in ((1891, c0), (1892, c1), (1893, (c0 + c1) / 2)):       # jamb sections, centre mullion
        o = sc.at(i, name, 'windows')
        half = scene_box(o)[5] / 2 - scene_box(o)[4] / 2
        sc.run(i, name, 'z', at - half, at + half, group='windows')
    jamb = scene_box(sc.objs[1891])
    inset = (jamb[5] - jamb[4])                                         # the pane ends one jamb section inside each jamb
    box = sc.run(1894, name, 'z', c0 + inset, c1 - inset, group='glass')
    w12 = (box[5] - box[4], box[3] - box[2])
    # panes of the rebuilt windows: two sashes each (sash_panes), on the wall's centre line. (W14's are appended by
    # round8_west_window_south, after everything else of the round.)
    y0, y1 = RV.GLAZING_WIN_Y
    for label, axis, c, span, ys, mull in (
            ('Bedroom 2 rear window W02', 'x', RV.REAR_WALL_C, RV.BED2_REAR_WIN_X, (RV.TALL_SILL, 8.0), None),
            ('Primary west window W15', 'z', RV.WEST_WALL_C, RV.PRIMARY_WEST_WIN_Z, (y0, y1), None),
            ('Living east window W05', 'z', RV.EAST_WALL_C, RV.LIVING_EAST_WIN_Z, (y0, y1), None),
            ('Living / dining east window W07', 'z', RV.EAST_WALL_C, RV.DINING_EAST_WIN_Z, (y0, y1),
             RV.DINING_EAST_WIN_MULLION)):
        sash_glass(sc, label, axis, c, span, ys, mull)
    # the front door's sidelights
    fd = G.FRONT_DOOR
    for (a, b), side in zip(G.FRONT_DOOR_SIDELIGHTS, 'WE'):
        sc.add(f'D01 sidelight {side} glass', (a, b, G.FRONT_DOOR_SIDELIGHT_RAIL_Y, G.DOOR_HEAD - G.HEAD_TRIM[0],
                                               fd['c'] - 0.02, fd['c'] + 0.02), GLASS_LOOK, material='glass', alpha=0.35)
    # the skylights: a pane over each well, at the height of its middle (the panes lie in the roof's slope)
    for label, rect, plane in (('Kitchen skylight', RV.KITCHEN_SKY, 'E'), ('Living skylight', RV.LIVING_SKY, 'E'),
                               ('Foyer skylight 0', RV.FOYER_SKY[0], 'EnE'), ('Foyer skylight 1', RV.FOYER_SKY[1], 'EnE'),
                               ('Primary bath skylight', RV.PRIMARY_BATH_SKY, 'W')):
        y = sky_y(plane, rect)
        sc.add(f'{label} glass', (rect[0], rect[1], y - 0.015, y + 0.015, rect[2], rect[3]), GLASS_LOOK,
               material='glass', alpha=0.35)
    return w12


def round8_levels(sc):
    """Floors that are not the house floor: the garage's slab 11 in lower, running out through the vehicle opening
    to the driveway, on its lowered foundation, with the step at the house door; the porch slab; the two rear
    landings with their step. (The site itself, ground, walk and driveway, is not in the scene's data.)"""
    slab = sc.at(1775, 'Garage concrete', 'floor')
    b = scene_box(slab)
    put_box(slab, (b[0], b[1], G.FLOOR_Y - G.SLAB_T, G.FLOOR_Y, b[4], SITE.DRIVE[2]))
    sc.reshaped.append(1775)
    found = [i for i in named(sc.objs, 'Foundation', 'base') if abs(box_of(sc.objs[i])[0] - b[0]) < HOST_TOL
             and abs(box_of(sc.objs[i])[4] - b[4]) < HOST_TOL]
    if len(found) != 1:
        raise SystemExit('%s: expected one Foundation box under the garage, found %d' % (ROUND8, len(found)))
    f = scene_box(sc.objs[found[0]])
    put_box(sc.objs[found[0]], (f[0], f[1], G.FLOOR_Y - G.SLAB_T - (f[3] - f[2]), G.FLOOR_Y - G.SLAB_T, f[4], f[5]))
    sc.reshaped.append(found[0])
    sx0, sx1, sz0, sz1 = G.STEP
    sc.add('Garage step at the house door', (sx0, sx1, G.FLOOR_Y, G.STEP_Y, sz0, sz1), FLOOR_LOOK, material='concrete')
    px0, px1, pz0, pz1 = SITE.PORCH
    sc.add('Covered porch slab', (px0, px1, SITE.GRADE_FRONT, SITE.PORCH_TOP, pz0, pz1), FLOOR_LOOK, material='concrete')
    for name, (x0, x1, z0, z1) in (('Rear landing — living room', SITE.DECK), ('Rear landing — primary bedroom',
                                                                                SITE.LANDING)):
        sc.add(name, (x0, x1, SITE.STEP_TOP, SITE.DECK_TOP, z0, z1), SITE_LOOK, material='wood')
        w = SITE.STEP_W
        sc.add(name + ' step', (x0 - w, x1 + w, SITE.GRADE_REAR, SITE.STEP_TOP, z0 - w, z1), SITE_LOOK, material='wood')


def round8_west_window_south(sc):
    """W14, the primary bedroom's second west window (the owner's; the sheet has none there), after the round's
    last build: its opening and the four wall pieces round it stay where the concept's relaid scene has them, which
    is checked against the spec; the old unit's pieces are marked removed by ROUND8_GONE; its two panes are appended
    like W15's. This runs LAST of the round's scene work: an appended object's index is its place in the list, and
    the objects appended before this step keep theirs."""
    s0, s1 = RV.PRIMARY_WEST_WIN_S_Z
    y0, y1 = RV.GLAZING_WIN_Y
    for i, name, want in ((3180, 'Primary west wall — north of added window', (None, None, 0.0, 8.0, None, s0)),
                          (3181, 'Primary west wall — south of added window', (None, None, 0.0, 8.0, s1, None)),
                          (3182, 'Primary west wall — added window sill wall', (None, None, 0.0, y0, s0, s1)),
                          (3183, 'Primary west wall — added window header', (None, None, y1, 8.0, s0, s1))):
        box = scene_box(sc.at(i, name, 'walls'))
        odd = [k for k, v in zip(FACES, want) if v is not None and abs(box[FACES.index(k)] - v) > HOST_TOL]
        if odd:
            raise SystemExit('%s: scene object %d %r is not where bl/revision_spec.py PRIMARY_WEST_WIN_S_Z and '
                             'GLAZING_WIN_Y have W14\'s opening (%s)' % (ROUND8, i, name, ', '.join(odd)))
    sash_glass(sc, 'Primary west window W14', 'z', RV.WEST_WALL_C, (s0, s1), (y0, y1))


def round8_scene(objs):
    """All of the eighth round's changes to scene.objects. Returns (the Round8Scene, W12's pane)."""
    sc = Round8Scene(objs)
    round8_walls(sc)
    round8_leaves(sc)
    round8_gone(sc)
    w12 = round8_openings(sc)
    round8_levels(sc)
    round8_west_window_south(sc)        # last: W14's panes are appended after every earlier object of the round
    return sc, w12


def round8_tour(scene):
    """Seed stops the rebuilt model has no place for leave the scene's tour (NODES_GONE), with their edges; captions
    of approach stops that named a doorway's old kind are corrected (NODE_SIZES). Returns the ids that left."""
    tour = scene.setdefault('tour', {})
    scene['rooms'] = [n for n in scene.get('rooms', []) if n.get('id') not in NODES_GONE]
    left = []
    if not installed(tour):
        left = [n['id'] for n in tour.get('nodes', []) if n.get('id') in NODES_GONE]
        tour['nodes'] = [n for n in tour.get('nodes', []) if n.get('id') not in NODES_GONE]
        tour['edges'] = [e for e in tour.get('edges', []) if not (set(e) & set(NODES_GONE))]
    for n in ([] if installed(tour) else tour['nodes']) + scene['rooms']:
        for key in ('neighbors', 'visible'):
            if isinstance(n.get(key), list):
                n[key] = [i for i in n[key] if i not in NODES_GONE]
    # (seeds only, like the moves: apply_sweeps.py gives an installed sweep the caption of the seed whose id AND label
    # it keeps, and a re-run on the installed tour must leave the file as it is)
    for n in ([] if installed(tour) else tour.get('nodes', []) + scene['rooms']):
        if n.get('id') in NODE_SIZES:
            n['size'] = NODE_SIZES[n['id']]
    return left


def installed(tour):
    """True when the scene's tour is the sweeps apply_sweeps.py installed (they carry `floor` and `outdoor`), not
    the concept's stops as apply_relayout.py leaves them. Installed sweeps stand where place_sweeps.py put them and
    their panoramas were rendered there: NODE_MOVES and NODES_GONE are for the seeds only."""
    return any('floor' in n or 'outdoor' in n for n in tour.get('nodes', []))


def changes_8(doors, rooms):
    """The eighth round (2026-11-24) in the owner's terms: the model brought to the architect's sheet after the size
    audit ("can you fix all these issues?"), with the numbers of the spec modules and of the schedule."""
    def w(did):
        return fi(doors[did]['width'])

    def size(rect):
        return f'{fi(rect[1] - rect[0])} x {fi(rect[3] - rect[2])}'
    foyer, bed4 = rooms['M11'], rooms[BEDROOM_4]
    hw, he = RV.HALL_WEST, RV.HALL_EAST
    blk = RV.HALL_BLOCK
    c2 = RV.BED2_CLOSET_CLEAR
    sx0, sx1, _, _ = RV.BED3_BATH_SHOWER
    t0, t1 = RV.BED3_BATH_TOILET_BAY_X
    vx0, vx1, _, _ = RV.BED3_BATH_VANITY
    lx, px = RV.LIVING_SLIDER_X, RV.SLIDER_X
    win = lambda ab: fi(ab[1] - ab[0])      # noqa: E731
    low, rise = in8(-G.FLOOR_Y), in8(-G.STEP_Y)
    sd = G.SIDE_DOOR
    pitch = f'{ROOF.P * 12:g} in 12'
    return [
        'The model brought to the architect\'s sheet (sizes.pdf, SKA002) after the size audit: every wall is '
        f'{in8(R.WALL)} in thick, inside and outside, and every room stands on the sheet\'s lines. The house measures '
        f'{fi(R.OUTER_SIZE[0])} x {fi(R.OUTER_SIZE[1])} outside ({fi(R.OUTER_SIZE[2])} on the garage side) and the '
        f'covered porch is {fi(R.Z_GAR_OUT - R.Z_PORCH_N)} + {fi(R.Z_PORCH_S - R.Z_GAR_OUT)} deep. Your earlier '
        'decisions stay: the foyer-side wall of Bedroom 4 and Bedroom 3 on the shared bath\'s wall line (foyer and '
        f'porch {fi(foyer["width_ft"])} wide, both rooms {fi(bed4["width_ft"])}), the laundry closet, the second west '
        'window of the primary bedroom, the bay glazed to the floor, the kitchen window and the sink under it, the '
        'tall windows, the white windows with grid bars, the sealed fireplace, all finishes and furniture',
        f'Bedroom 2\'s corner and the hall as on the sheet: the hall is {fi(hw[1] - hw[0])} wide beside a closet block '
        f'of {fi(blk[1] - blk[0])} x {fi(blk[3] - blk[2])} and {fi(he[3] - he[2])} wide south of it. The block holds '
        f'Bedroom 2\'s closet ({fi(c2[1] - c2[0])} wide, two sliding panels in a {w("D13")} opening), the furnace '
        f'closet behind a louvred {w(FAU_DOOR)} door and a storage closet behind a {w(STO_DOOR)} door. Bedroom 2 is '
        f'entered through a hinged {w("D12")} door in its south wall (the entry alcove is gone), the shared bathroom '
        f'has its hinged {w("D07")} door, and the primary suite\'s entry stands at the sheet\'s place',
        f'Kitchen island {fi(KITCHEN.PLAN_ISLAND_L)} x {fi(KITCHEN.PLAN_ISLAND_D)} at the sheet\'s place, '
        f'{fi(KITCHEN.PLAN_AISLE_E)} from the sink run and {fi(KITCHEN.PLAN_AISLE_S)} from the cooktop run; both '
        f'counters {fi(KITCHEN.PLAN_COUNTER_D)} deep. The dining table moved west with the island\'s end and stays in '
        'line with it, with six chairs and 3 ft or more to walk past; the pendants hang over the island\'s quarter '
        'points. The kitchen window, the sink, the refrigerator beside the microwave and the cooktop keep the places '
        'you gave them',
        f'Bedroom 3\'s bathroom as on the sheet: a shower {fi(sx1 - sx0)} wide across the west end, the toilet in a '
        f'{fi(t1 - t0)} bay and the vanity in a {fi(vx1 - vx0)} bay on the north wall, a hinged {w("D05")} door at the '
        'east end of the south wall; the shower window stays as you set it. Bedroom 3\'s closet is a reach-in closet '
        f'behind two sliding panels in a {w("D06")} opening, and the bedroom\'s door is {w("D03")}, hinged on the north '
        'side' + ('' if RV.BED3_WEST_WINDOW else '. The window in Bedroom 3\'s west wall is removed: the sheet has a '
                  'solid wall behind the bed, where a picture hangs now'),
        f'Doors and windows at the sheet\'s sizes and places. Living room rear wall: one {win(lx)} four-panel sliding '
        f'glass door in place of the garden door and the two fixed windows, with its {size(SITE.DECK)} landing. Primary '
        f'bedroom: sliding door in a {win(px)} wall opening with a {size(SITE.LANDING)} landing; north west window '
        f'{win(RV.PRIMARY_WEST_WIN_Z)}, and your second west window, which keeps its opening, has the same two-sash '
        f'unit. Bedroom 2 rear window {win(RV.BED2_REAR_WIN_X)}. Living room east: one '
        f'{win(RV.LIVING_EAST_WIN_Z)} window in place of two; living / dining east window {win(RV.DINING_EAST_WIN_Z)}. '
        f'Bedroom 4 west window {win(RV.BED4_WEST_WIN_Z)}, centred on its wall. Front door {w("D01")} with a sidelight '
        f'on each side, in a unit {fi(G.FRONT_DOOR_UNIT[1] - G.FRONT_DOOR_UNIT[0])} wide (the sheet\'s unit fitted to '
        f'your narrower foyer). Door between house and garage {w("D02")}, hinged on the north side; a {w(SIDE_DOOR)} '
        f'side door in the garage\'s east wall ({fi(sd["ro"][1] - sd["ro"][0])} wall opening); vehicle door in a '
        f'{fi(G.VEHICLE_RO_X[1] - G.VEHICLE_RO_X[0])} opening. Every hinged door has a leaf of its opening\'s size, '
        'with hinges and a lever. All new glass is white with grid bars, like the rest',
        f'Skylights: the living room gets the sheet\'s skylight, {size(RV.LIVING_SKY)}, where the sheet draws it; the '
        f'kitchen skylight takes the same size, {size(RV.KITCHEN_SKY)}, and keeps your place over the sink (its '
        'east edge where the wider opening\'s was)',
        f'Garage: the floor is {low} in below the house floor, with a step of {size(G.STEP)} at the house door (two '
        f'risers of {rise} in); the water heater is a {fi(G.WATER_HEATER_D)} tank in the north-east corner (the '
        'wall-hung unit is gone)',
        f'Roof and levels as on the sheets: every roof plane {pitch}; main ridge {fi(nominal(ROOF.MAIN_Y))} and garage '
        f'ridge {fi(ROOF.GAR_Y)} above the house floor; the entry ridge level; eaves {fi(ROOF.OVH)} wide. The entry '
        f'gable runs on over the porch, {fi(ROOF.ENTRY_FRONT - R.Z_PORCH_S)} past the slab, in place of the flat '
        f'canopy. The house floor is {in8(-SITE.GRADE_FRONT)} in above the ground at the front and '
        f'{fi(-SITE.GRADE_REAR)} at the rear; the rear landings have one step with two risers of '
        f'{in8(SITE.STEP_RISE)} in, the porch slab is {in8(-SITE.PORCH_TOP)} in below the floor, with '
        f'{porch_risers()}, and the driveway is '
        f'{fi(SITE.DRIVE[1] - SITE.DRIVE[0])} wide and level. Bedroom 3\'s vault follows the roof: '
        f'{fi(ROOF.BED3_SPRING)} at the walls, {fi(ROOF.bed3_vault(ROOF.WING_X))} at the ridge. Colours, cladding and '
        'the garage door\'s design are unchanged',
        'The numbers of the tour follow the rebuilt model: the dimension plan and the schedule are drawn from it, and '
        'a door\'s width in the schedule is its clear opening, the size the architect\'s sheet gives it',
    ]


def round8_records(scene):
    """The scene's own records of the roof, the vaults and the concept's kitchen and doors (design_revision,
    layout_revision): the roof and the vaults as bl/roof.py builds them; concept records the round overtakes are
    marked as superseded, like the sixth round's."""
    dr = scene.setdefault('design_revision', {})
    dr['vaults'] = {'entry': {'wall_ft': r4(ROOF.entry_vault(R.X_FOYER_W)), 'ridge_ft': r4(ROOF.ENTRY_VAULT_Y),
                              'ridge_fall_ft_per_ft': 0.0},
                    'bedroom_3': {'eave_ft': r4(ROOF.BED3_SPRING), 'ridge_ft': r4(ROOF.bed3_vault(ROOF.WING_X))}}
    dr['roof'] = {'pitch': f'{ROOF.P * 12:g} in 12 on every plane', 'eave_overhang_ft': r4(ROOF.OVH),
                  'fascia_top_ft': r4(ROOF.EAVE_Y), 'main_ridge_ft': r4(ROOF.MAIN_Y), 'garage_ridge_ft': r4(ROOF.GAR_Y),
                  'addition_ridge_ft': r4(ROOF.WING_Y), 'entry_ridge_ft': r4(ROOF.ENTRY_Y),
                  'entry_ridge_fall_ft_per_ft': 0.0,
                  'entry_front': 'The entry gable runs on over the porch, %s past the slab' % fi(ROOF.ENTRY_FRONT - R.Z_PORCH_S)}
    dr['roof_reference'] = 'sizes/sizes.pdf: A1.2, A1.3 and SKA001 (tools/render/bl/roof.py)'
    dr['roof_status'] = ('Built to the architect\'s sheets since the eighth round (2026-11-24). The entry roof\'s height '
                         'follows from SKA001\'s plan lines; the set has no elevation of the addition. Framing, loads '
                         'and drainage details require design verification.')
    lr = scene.setdefault('layout_revision', {})
    for key in ('kitchen_island', 'kitchen_skylight', 'suite3', 'door_dimensions'):
        if isinstance(lr.get(key), dict):
            lr[key]['superseded'] = ('Eighth round (2026-11-24): the model follows the architect\'s sheet SKA002; see '
                                     'design_revision.owner_changes_8 and the dimension schedule')
    ids = lr.get('dimension_review', {}).get('room_ids')
    if isinstance(ids, list) and BED2_CLOSET_ROOM not in ids:
        ids.append(BED2_CLOSET_ROOM)
    isl = KITCHEN.PLAN_ISLAND
    lr['eighth_round'] = {
        'date': '2026-11-24', 'sheet': 'sizes/sizes.pdf SKA002',
        'kitchen_island': {'worktop_bounds_xz_ft': [r4(v) for v in isl], 'aisle_east_ft': r4(KITCHEN.PLAN_AISLE_E),
                           'aisle_south_ft': r4(KITCHEN.PLAN_AISLE_S), 'counter_depth_ft': r4(KITCHEN.PLAN_COUNTER_D),
                           'stool_count': 0},
        'levels_ft': {'house_floor': 0.0, 'garage_floor': r4(G.FLOOR_Y), 'garage_step': r4(G.STEP_Y),
                      'porch_slab': r4(SITE.PORCH_TOP), 'rear_landings': r4(SITE.DECK_TOP),
                      'rear_landing_step': r4(SITE.STEP_TOP), 'ground_front': r4(SITE.GRADE_FRONT),
                      'ground_rear': r4(SITE.GRADE_REAR)},
        'driveway_xz_ft': [r4(v) for v in SITE.DRIVE],
        'water_heater': {'centre_xz_ft': [r4(v) for v in G.WATER_HEATER_C], 'diameter_ft': r4(G.WATER_HEATER_D)},
    }


# ------------------------------------------------------------------------------------- eighth round: the classification
def turned_box(o):
    """(x0, x1, y0, y1, z0, z1) of a SCENE box or primitive, turned about the vertical axis or not."""
    r = o.get('rot') or 0
    c, sn = abs(math.cos(r)), abs(math.sin(r))
    hx, hz = (o['s'][0] * c + o['s'][2] * sn) / 2, (o['s'][0] * sn + o['s'][2] * c) / 2
    return (o['p'][0] - hx, o['p'][0] + hx, o['p'][1] - o['s'][1] / 2, o['p'][1] + o['s'][1] / 2,
            o['p'][2] - hz, o['p'][2] + hz)


ARCH_GROUPS = ('walls', 'door', 'garageDoor', 'windows', 'glass', 'trim', 'floor', 'ceiling', 'base', 'facade', 'roof')
CLASS_OF_GROUP = {      # an appended object's role / detail / keep in scene_classification.json (classify_scene.py's words)
    'walls': ('shell', 'wall', 'exact'), 'door': ('opening', 'door_leaf', 'exact'),
    'glass': ('opening', 'window_glass', 'exact'), 'floor': ('shell', 'floor_slab', 'exact'),
    'facade': ('exterior', 'stucco_skin', 'exact'), 'landscape': ('landscape', 'ground', 'replaceable'),
}


def update_classification(cls, scene):
    """scene_classification.json after the owner's rounds. apply_relayout.py writes it from the concept's
    classification; here its room regions follow the hall and Bedroom 2 of the eighth round (place_sweeps.py names a
    new sweep after the region it stands in, tools/web/build_site_data.py takes the open spaces' rectangles from it),
    and its object records follow scene.objects: the box of every reshaped object, the mark of every removed one, and
    a record for every appended one (the laundry closet's and the suite's of earlier rounds included). Returns
    (records updated, records added)."""
    rooms = cls['meta']['rooms']
    for need in ('bed2', 'common_hall', 'suite3_wic'):
        if need not in rooms:
            raise SystemExit('scene_classification.json has no room region %r' % need)
    b2 = R.ROOMS['bed2']
    rooms['bed2'].update(bounds_ft_x0x1z0z1=[r4(v) for v in b2], source='audit M02')
    hw, he = RV.HALL_WEST, RV.HALL_EAST
    hall = rooms['common_hall']
    # the hall's two legs and the passage south of them, one rectangle as before (it reaches over the closet block,
    # where nobody stands; a point belongs to the smallest room that holds it)
    hall['bounds_ft_x0x1z0z1'] = [r4(hw[0]), r4(he[1]), r4(hw[2]), hall['bounds_ft_x0x1z0z1'][3]]
    hall['nodes'] = sorted(set(hall.get('nodes', [])) | {'T2'})
    hall['source'] = 'walls; open to dining/kitchen (eighth round: from Bedroom 2\'s south wall, the west leg included)'
    rooms['suite3_wic']['nodes'] = ['B3']               # Bedroom 3's closet: seen from the bedroom's stop
    rooms['bed2_closet'] = {'nodes': ['B2'], 'bounds_ft_x0x1z0z1': [r4(v) for v in RV.BED2_CLOSET_CLEAR],
                            'source': 'audit %s' % BED2_CLOSET_ROOM}
    rects = {k: v['bounds_ft_x0x1z0z1'] for k, v in rooms.items()}

    def room_at(x, z):
        inside = [(( b[1] - b[0]) * (b[3] - b[2]), k) for k, b in rects.items() if b[0] <= x <= b[1] and b[2] <= z <= b[3]]
        if inside:
            return min(inside)[1]
        near = min(rects, key=lambda k: math.hypot(max(rects[k][0] - x, 0, x - rects[k][1]),
                                                   max(rects[k][2] - z, 0, z - rects[k][3])))
        b = rects[near]
        return near if math.hypot(max(b[0] - x, 0, x - b[1]), max(b[2] - z, 0, z - b[3])) <= 0.8 else 'exterior'
    recs, changed, added = cls['objects'], 0, 0
    for i, o in enumerate(scene['objects']):
        rec = recs.get(str(i))
        group = o.get('group_was', o.get('group'))
        if rec is None:
            role, detail, keep = CLASS_OF_GROUP.get(group, ('decor', 'other', 'replaceable'))
            if group == 'walls' and o['p'][1] - o['s'][1] / 2 > 1.5:
                detail = 'wall_header'
            rec = recs[str(i)] = {'room': room_at(o['p'][0], o['p'][2]), 'role': role, 'group': group,
                                  'name': o['name'], 'detail': detail, 'keep': keep, 'shape': o.get('shape', 'box'),
                                  'aabb_ft': [r4(v) for v in turned_box(o)], 'added': True}
            added += 1
        elif o.get('shape') == 'box' and 'geometry' not in o and group in ARCH_GROUPS:
            box = [r4(v) for v in turned_box(o)]
            if any(abs(a - b) > 2e-4 for a, b in zip(box, rec.get('aabb_ft', box))):
                rec['aabb_ft'] = box
                changed += 1
        if o.get('removed'):
            if rec.get('removed') != o['removed']:
                changed += 1
            rec['removed'] = o['removed']
        else:
            rec.pop('removed', None)
    cls['meta']['_about'] = ('Object index -> classification. Index == position in SCENE.objects. Records of objects '
                             'that tools/render/apply_revisions_web.py appended to the scene carry "added"; a piece the '
                             'built model no longer has carries "removed".')
    return changed, added


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
    skylights(meas['windows'])          # W16, W18..W20 and, new in the eighth round, the living room's W21
    win = {w['id']: w for w in meas['windows']}
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
    doors8 = round8_doors(meas['doors'])                # eighth round: every door, measured between its liners
    left_windows = round8_windows(meas)                 # ... the windows at the sheet's sizes, the sidelights
    rooms8 = round8_rooms(meas, doors8)                 # ... Bedroom 2 and its closet, Bedroom 3's bath and closet
    meas['spaces'], meas['overall'] = round8_spaces(), round8_overall()
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
    sc8, w12 = round8_scene(objs)       # eighth round: walls, leaves, panes, levels; what the build no longer has
    win['W12']['panes'] = [{'width': r4(w12[0]), 'height': r4(w12[1])}]
    typed = window_types(meas)          # seventh round: white frames and grids, in every window's `type`
    fire = fireplace_objects(objs)      # ... and the concept's fireplace, which stays in the scene undrawn
    dr = scene.setdefault('design_revision', {})
    vaults = dr.get('vaults', {})
    if 'bedrooms_3_4' in vaults:
        vaults['bedroom_3'] = vaults.pop('bedrooms_3_4')
    dr['owner_changes'] = {'date': '2026-11-18', 'changes': changes_1()}
    dr['owner_changes_2'] = {'date': '2026-11-19', 'changes': changes_2()}
    dr['owner_changes_3'] = {'date': '2026-11-19', 'changes': CHANGES_3}
    dr['owner_changes_4'] = {'date': '2026-11-19', 'changes': CHANGES_4}
    dr['owner_changes_5'] = {'date': '2026-11-20', 'changes': changes_5(bed4, cut)}
    dr['owner_changes_6'] = {'date': '2026-11-20', 'changes': changes_6(suite)}
    dr['owner_changes_7'] = {'date': '2026-11-21', 'changes': changes_7()}
    dr['owner_changes_8'] = {'date': '2026-11-24', 'changes': changes_8(doors8, {r['id']: r for r in meas['rooms']})}
    round8_records(scene)               # the roof, the vaults, the concept records the round overtakes
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
    left_nodes = round8_tour(scene)     # eighth round: the stop inside Bedroom 3's old closet leaves the seeds
    labels = size_labels(meas)
    seeds = not installed(scene['tour'])
    for n in scene['tour']['nodes'] + scene.get('rooms', []):
        if n.get('id') in labels:
            n['size'] = labels[n['id']]
        if n.get('id') in NODE_NAMES:
            n['label'] = n['name'] = NODE_NAMES[n['id']]
        if n.get('id') in NODE_MOVES and (seeds or 'floor' not in n):   # (never a sweep apply_sweeps.py installed)
            x, z = NODE_MOVES[n['id']]
            dx, dz = x - n['p'][0], z - n['p'][2]
            if abs(dx) > 1e-4 or abs(dz) > 1e-4:     # the look point travels with the stop: same yaw and pitch
                n['p'] = [x, n['p'][1], z]
                if len(n.get('look') or []) == 3:
                    n['look'] = [n['look'][0] + dx, n['look'][1], n['look'][2] + dz]
    # the About sheet's room table: a row for every room of the schedule, with the schedule's name, sizes and note
    # (until the seventh round only the rows a round touched were refreshed, and M08 and M12 kept the concept's notes)
    scene['audit'] = [dict(r) for r in meas['rooms']]
    cls = sitedata.load_classification()
    cls_changed, cls_added = update_classification(cls, scene)
    design = sitedata.load_design()
    notes = update_design(design)
    for name, changed in (('measurements', sitedata.save_measurements(meas)), ('scene', sitedata.save_scene(scene)),
                          ('classification', sitedata.save_classification(cls)),
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
    print('primary suite: room %s %s %s x %s, room %s %s %s x %s, pocket door %s %s clear; scene walls %s reshaped and '
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
    print('eighth round: %d doors (new %s, %s, %s), windows gone %s, new %s %s %s; rooms %s; %d spaces; '
          'change list owner_changes_8 (%d entries)'
          % (len(doors8), FAU_DOOR, STO_DOOR, SIDE_DOOR, ' '.join(left_windows) or 'none (a re-run)', LIVING_SKYLIGHT,
             *SIDELIGHTS, ' '.join(sorted(rooms8)), len(meas['spaces']), len(dr['owner_changes_8']['changes'])))
    print('              scene: %d objects reshaped in place, %d marked removed, %d appended (%d..%d); seeds gone %s, '
          'moved %s; classification: %d records updated, %d added'
          % (len(set(sc8.reshaped)), len(set(sc8.gone)), len(set(sc8.added)), min(sc8.added), max(sc8.added),
             ' '.join(left_nodes) or ('none' if seeds else 'none (the tour is installed sweeps)'),
             ' '.join(sorted(NODE_MOVES)) if seeds else 'none (the tour is installed sweeps)', cls_changed, cls_added))
    for line in notes:
        print('note:', line)


if __name__ == '__main__':
    main()
