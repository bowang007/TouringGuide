"""Place the tour's panorama sweeps automatically on a built scene (runs inside Blender, CPU only, ~70-90 s).

  blender -b tools/render/.cache/house.blend -noaudio --python tools/render/place_sweeps.py -- \
      --out tools/render/data/sweeps.json [--overlay sweeps.png] [--scene tools/render/data/scene.json] \
      [--keep tools/render/data/sweeps.json]

Reads the old stops from the scene file (`tour.nodes`), ray-casts the built model and writes the sweeps of the
Matterport-style tour: where the camera may rest, which sweeps are joined by a walkable straight line
(`links`) and which can see each other (`visible`). tools/render/apply_sweeps.py then installs the file into
the scene (`tour.nodes` / `tour.edges`). Nothing in the .blend is changed or saved.

How the layout is found (all distances in SCENE feet; x west->east, z north->south, y up):

 1. One BVH over the interior (collections shell, openings, exterior_shell, the interior zone_* trees and
    the garage door) and a second one over the site objects around the front porch and the rear landings.
 2. A 0.25 ft grid. A cell is standable when a ray down from eye height lands on the floor (-0.03 .. 0.15 ft
    against the level of the place: floor, rug, tile; anything higher is furniture) and a ray up hits a
    ceiling. Its clearance is the nearest surface in 16 directions at 0.6 / 2.0 / 3.5 ft and eye height, and
    not more than the distance to the nearest cell that has furniture below the eye (low tables, beds, benches
    that the rays can miss).
    Levels (LEVELS, read from bl/garage_spec.py and bl/zones/exterior_layout.py): the house floor is y 0, the
    garage floor is 11 in lower, the porch slab 5 1/2 in, the two rear landings 1 in. Every height above is counted
    from the level of the place, and a sweep's eye is EYE above the level it stands on (its `p[1]`; `level`
    says which). The step at the door between the house and the garage is furniture for a sweep (nobody stands
    on it) and floor for a walking line (STEPS).
 3. Reachable floor: flood fill over cells with >= 0.9 ft clearance from the old stops (no pockets behind
    furniture).
 4. Seeds (E0 H1 H2 H3 B3 B4 K0 D0 L0 L1 L2 P0 S0 C0 A0 B2 A1 G0 A3) keep their id and position. A seed
    with less than 1.2 ft clearance is nudged by up to 1.5 ft to the best clear cell it can see; where there
    is none it stays (>= 0.8 ft is accepted in rooms that would otherwise have no sweep). Only a seed that
    the model no longer leaves standing room for (< 0.8 ft) goes to the nearest clear cell of its room, with
    a warning, so that an id the measurements and design views name is not lost.
    The walk-in closet's stop C0 is the exception: its authored place is under the south rod of the closet
    the owner's sixth round built (bl/revision_spec.py SUITE_CLOSET_*), so it goes to the most open cell
    of the aisle between the three hanging walls, which is on the axis of the pocket door (WALKIN).
    Before the seeds, the stops set by hand (PLACED: id -> place written from relayout's wall faces, with the
    reason) are put down where their place is standable with --keep-clear of clearance: one stop in front of
    two doors, the corner of the L-shaped hall, the middle of a doorway beside an open leaf, a stop the grid's
    coarse measure had left too near a table. Where the place is not free the rules of this list decide, with
    a note. A seed set by hand keeps aiming at the look point of its stop in the scene file.
 5. The laundry closet, when the model has one (a mesh named laundry / washer / dryer inside the closet's
    rectangle, bl/revision_spec.py): one sweep in the foyer on the axis of the closet's doors, 4 ft in front
    of the door wall (3.4 ft from the open leaves), facing the stacked units and looking 14 degrees down so
    that both are in the picture (the nearest clear cell that sees the opening when that point is not
    free); id LC. Otherwise a warning and no sweep.
 6. The old approach stops (T1 T2 T3 T4 T6 P1 GA) are candidates: one is kept when it joins parts of the
    walk graph that the sweeps placed so far do not join and stands >= 3 ft from every sweep it sees
    (connectivity), or when it stands >= 4 ft from every sweep it sees (spacing). Then every interior
    doorway of the dimension schedule (measurements.json `doors`) that has no sweep within 3 ft gets one in
    or just inside the opening, and parts of the graph that are still separate are joined by one sweep each,
    placed where its legs to both sides are shortest (near the doorway between them).
 7. Greedy fill of the reachable floor with >= 1.2 ft clearance: repeatedly take the cell farthest from the
    sweeps it can see, distances beyond 5.5 ft counting the same so that among far cells the most open one
    wins, until no cell is >= 4 ft from every sweep it sees. A cell with less than 1.5 ft clearance is used
    only when it is >= 5 ft away (a pocket that needs its own sweep; this keeps sweeps off the walls). At
    most 4 sweeps in the garage, and no second sweep in a bathroom (FILL_ONE: the only floor 4 ft from the
    first one is inside the shower). A room region left without a sweep gets one at its most open cell
    (>= 0.8 ft); bed3_bay, bed4_closet and the reach-in closets of Bedrooms 2 and 3 (bed2_closet, suite3_wic)
    count as covered by their rooms.
 8. Two outdoor sweeps (OP on the front porch facing the entry, OD on the rear landing outside the open way
    of the living room's sliding door: the schedule's way_start .. way_end of D14), each on the porch slab /
    the landing's boards and only when a walkable straight line through the open door joins it to an indoor
    sweep; a closed door or panel blocks that line. By default both or none (--outdoor each / off).
 9. Graph: `links` = walkable straight segments up to 11 ft (rays at 0.5 / 2.0 / 3.5 ft and eye height, each
    at -0.45 / 0 / +0.45 ft sideways, and bare floor under the same three lines every 0.4 ft, so a link
    never crosses a coffee table or the corner of a bed; between two levels the lines slope from one end's
    height to the other's and the floor under them may be either level or the step), minus a link that a third
    sweep replaces with two shorter legs and < 20 % detour. `visible` = sweeps within 40 ft with a clear
    line at eye height and 1 ft below it (clear glass does not block), always including the links. The
    links must form one connected graph.

New ids are a letter for the room region and the first free character: L living, D dining strip, K kitchen,
G garage, F foyer, H halls, P primary bedroom, S primary dressing, A baths, C closets, X / Y / Z bedroom
2 / 3 / 4; no new id repeats one of the old stops' ids, kept or not, or an id an earlier round retired
(RETIRED: L5, C3; their panoramas were published). A new sweep takes the label and room id of
its region's seed (the nearest of H2 / H3 in the halls). Re-running on a scene that already holds the
sweeps gives the same layout and the same ids.

Keeping an installed layout (--keep SWEEPS.json, e.g. the file this run overwrites): after a change to part of
the model the panoramas of the untouched rooms stay valid only while their sweeps do not move, so
 * every sweep of that file stays exactly where it is, with its id, yaw, pitch, label and room, while the
   new model leaves it standable with >= --keep-clear (0.9 ft) of clearance; steps 4 and 6 do not run for
   them and the approach stops that layout had dropped stay dropped;
 * a name follows the scene file: a seed takes the label its stop has there now, and the other sweeps that
   carried a renamed seed's old label and room take the new one with it (the sixth round renamed S0
   "Primary vestibule" and C0 "Walk-in closet"; S1 had S0's old label). An outdoor sweep takes the label
   OUTDOOR gives its id (the eighth round renamed OD "Rear landing": the model has a landing there, not a deck;
   its id and its room key 'deck' stay). The panorama is not affected;
 * a seed that stood on its authored position follows the scene file when the scene has moved it since
   (apply_revisions_web.py NODE_MOVES), by the rule of step 4;
 * a sweep the model no longer leaves room for goes to the best clear cell within --nudge (1.5 ft) that it
   sees, is >= 3 ft from the sweeps it sees and joins the walk graph (a seed: the rule of step 4, from its
   stop in the scene file, which is its place in today's model), or is dropped; every such decision is a note;
 * a stop set by hand (PLACED) goes to its place whether the kept layout had it elsewhere or not at all;
 * --keep-clear 1.2 (the clearance a new sweep needs) is the value to use when every panorama is rendered
   again anyway: it moves the kept sweeps a changed model has left with less than a new one would get;
 * the laundry sweep is always placed by step 5 (it follows the closet; its old place is released);
 * steps 6 (doorways, bridges), 7 and 8 then add sweeps only where the kept ones leave floor uncovered; a
   new sweep never takes an id of the kept file, used or dropped;
 * links and visible are computed afresh for all sweeps.
The file gets a "keep" block: {from, unchanged, moved {id: ft}, reaimed, new, removed, renamed {id: label}}
against the kept layout (apply_sweeps.py prints it; moved and new sweeps need a panorama, and so does every
kept sweep that sees a changed part of the model). The overlay rings the moved and new sweeps in red.

Output: {"eye", "generated_from", "units", "params", "stats", "notes", ["keep",] "sweeps": [{"id", "label", "room",
"p", "level", "floor", "yaw", "pitch", "links", "visible", "outdoor", "origin", "clearance"}]}. p = [x, level + eye,
z]; `level` is the level the sweep stands on (0 = the house floor), `floor` the surface under it. Angles are DEGREES
(yaw 0 = looking toward -z / north, positive clockwise seen from above; the convention of
assets/data/tour.json); apply_sweeps.py converts them to the radians that scene.json nodes use. A seed that
did not move keeps its authored yaw / pitch, a moved one keeps aiming at its old look point, the others
look toward the most open direction (LC and the outdoor sweeps at their door; LC also looks down at the
stacked pair); a sweep of a kept layout keeps the yaw / pitch of that file. `origin` says why a sweep
exists: seed, seed-moved, placed, approach, laundry, door, bridge, fill, region, outdoor. `notes` lists every
decision (moved seeds, kept / dropped approach stops, doorway and bridge sweeps, outdoor sweeps, what
became of a kept layout).

With --overlay a top-down picture is drawn from the same rays (no rendering): floor tinted by clearance
(green >= 1.2 ft, yellow reachable but tighter), furniture footprint, a section cut at 4 ft (walls black,
glass blue), links, and the sweeps with their ids and yaw. North is up. Review it before installing.

Exit status: 0 written; 2 the layout is not one connected graph or has a bad id (the overlay is still
drawn, the JSON is not written); 1 any other error (Blender itself would exit 0 after a Python error).

Development: --mesh-cache FILE keeps the collected triangles between runs (the collection of ~400 000
depsgraph instances is 60 of the ~75 seconds); the cache is rebuilt when the .blend changed.
"""
import argparse
import collections
import json
import math
import os
import re
import struct
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

from bl import garage_spec as GS  # noqa: E402  (pure Python: the garage's floor level and its step)
from bl import revision_spec as RS  # noqa: E402  (pure Python: the laundry closet's rectangle and opening)
from bl.common import FT, ft2bl  # noqa: E402
from bl.zones import exterior_layout as XL  # noqa: E402  (the porch slab and the rear landings: rectangles, levels)
from bl.zones import kitchen_dining_kitchen as KK  # noqa: E402  (the island and the counters on the plan)

EYE = 5.0853
SEEDS = 'E0 H1 H2 H3 B3 B4 K0 D0 L0 L1 L2 P0 S0 C0 A0 B2 A1 G0 A3'.split()
# ids of earlier rounds that no sweep may take again (panoramas were published under them): L5 stood where the sofa
# is since the seventh round; C3 was the stop inside Bedroom 3's step-in closet, which the eighth round rebuilt as
# the sheet's reach-in closet behind two sliding panels (nowhere to stand; B3 looks into it)
RETIRED = ('L5', 'C3')
# old approach stops: id -> position on the architect's plan (used when the scene file no longer lists them,
# i.e. on a re-run after apply_sweeps.py; the positions in the scene file win). They are the concept's stops
# carried through relayout's maps, as apply_relayout.py carries tour.nodes: T1 (13.044, 18.048), T2 (13.044, 16.374),
# T3 (13.500, 19.827), T4 (5.273, 43.767), T6 (12.968, 43.922), P1 (8.086, 11.537), GA (19.123, 38.272)
APPROACH = {k: RS.R.remap_xz(*v) for k, v in {
    'T1': (13.7, 18.2), 'T2': (13.7, 16.6), 'T3': (14.2, 19.9), 'T4': (4.85, 44.2), 'T6': (11.9, 44.35),
    'P1': (8.5, 14.0), 'GA': (18.05, 38.3)}.items()}
OLD_IDS = set(SEEDS) | set(APPROACH) | set(RETIRED)

# region of tools/render/data/scene_classification.json meta.rooms -> (seeds whose label / room id a new
# sweep in that region takes: the nearest one, letter of new ids, region that also counts as covered)
REGIONS = {
    'primary': (['P0'], 'P', None), 'primary_dressing': (['S0'], 'S', None),
    'ensuite': (['A0'], 'A', None), 'shared_bath': (['A1'], 'A', None), 'bed2': (['B2'], 'X', None),
    'common_hall': (['H2', 'H3'], 'H', None), 'living': (['L0'], 'L', None), 'dining': (['D0'], 'D', None),
    'kitchen': (['K0'], 'K', None), 'bed4': (['B4'], 'Z', None), 'bed4_closet': (['B4'], 'Z', 'bed4'),
    'suite3_bath': (['A3'], 'A', None), 'suite3_wic': (['B3'], 'C', 'bed3'), 'bed3': (['B3'], 'Y', None),
    'bed2_closet': (['B2'], 'X', 'bed2'),     # eighth round: reach-in closets behind sliding panels, seen from the room
    'bed3_bay': (['B3'], 'Y', 'bed3'), 'front_hall': (['H1'], 'F', None), 'garage': (['G0'], 'G', None),
}
OUTDOOR_REGIONS = ('porch',)          # roofed but outdoors: never filled, only the porch sweep of step 8
FILL_ONE = ('ensuite', 'shared_bath', 'suite3_bath')   # bathrooms: the fill adds no second sweep (the only floor
#                                                        4 ft from the first one is inside the shower)
ID_CHARS = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'

# laundry closet of the owner's fifth round (bl/revision_spec.py): carved out of Bedroom 4's north-east corner, a
# pair of doors in its EAST face that stand open onto the foyer, the stacked washer + dryer facing east
LAUNDRY = {'id': 'LC', 'label': 'Laundry closet', 'names': ('laundry', 'washer', 'dryer'),
           'outer': RS.LAUNDRY_OUTER,               # x0, x1, z0, z1 over the walls: the units stand in here
           'clear': RS.LAUNDRY_CLEAR,               # inside
           'door_face': RS.LAUNDRY_HOST_WALL_X[1],  # x of the door wall's foyer face
           'door_c': RS.LAUNDRY_DOOR_C,             # x of the door wall's centre line
           'door_z': RS.LAUNDRY_DOOR_Z,             # the opening, north jamb .. south jamb
           'out': (1.0, 0.0),                       # the doors open east
           # How far in front of the door wall the sweep stands, and its own view. The units' fronts are 0.46 ft
           # behind that wall and reach from the floor to 6.5 ft. From 3 ft that is 79 degrees from foot to top,
           # more than the page's 68 degree picture holds: whatever the pitch, one unit is cut in half (looked at
           # on renders from 3.0, 3.55, 4.0 and 4.05 ft). From 4 ft it is 67 degrees; 14 degrees down shows the lit
           # door head, the dryer with its panel and the washer down to its plinth, and the reel thumbnail
           # (51 degrees) the dryer's door, the washer's panel and the top of its door. 4 ft from the wall is
           # 3.4 ft from the open leaves and leaves 2.4 ft to the refrigerator's end panel behind the camera.
           'dist': 4.0,
           'pitch': -14.0}
# walk-in closet of the owner's sixth round (bl/revision_spec.py): a 6'-1" x 8'-0" room of its own behind a pocket
# door in its east wall, rods and shelves on the north, west and south walls. The concept's stop C0 stood where the
# south rod hangs now (0.6 ft of clearance). A nudge of the usual 1.5 ft would leave it at the south-west edge of
# the aisle with 1.7 ft of clearance, on a line through the door that passes 0.2 ft from the leaf's nose (after the
# body's half width); the most open cell of the aisle has 2.4 ft all round and stands on the door's axis.
WALKIN = {'id': 'C0',
          'clear': RS.SUITE_CLOSET_CLEAR,           # x0, x1, z0, z1 inside the closet
          'door_z': RS.SUITE_CLOSET_DOOR_Z}         # the pocket door's opening, strike jamb .. pocket jamb
# Stops set by hand, id -> (x, z, why). The rules find the rooms; they do not know that one stop in front of two
# doors reads better than a stop beside each, or that the corner of an L-shaped hall wants a stop of its own. The
# positions are written from relayout's wall faces. An entry is used while the model leaves its place standable with
# --keep-clear of clearance; a kept sweep of that id moves there, another id is a new sweep. Where the place is not
# free the usual rules decide and a note says so. Links, visibility and the opening view are found as for any sweep.
_HALL_X = (RS.R.X_BED2_W + RS.R.X_BLOCK_W) / 2          # centre line of the hall's west leg (3'-3" wide), 13.35
_HALL_Z = (RS.R.Z_BLOCK_S + RS.R.Z_WIC_S) / 2           # centre line of its east leg (3'-4" wide), 19.225
_FOYER_WALL_C = sum(RS.R.FOYER_WALL) / 2                # centre line of the wall between the foyer and Bedrooms 3 / 4
PLACED = {
    # eighth round: the hall beside Bedroom 2's closet block, as on the architect's sheet
    'T2': (_HALL_X, RS.SUITE_ENTRY_Z[0] + 1.02,
           'in front of the primary suite entry and Bedroom 2\'s door (it stood beside the entry\'s parked panel; '
           'from here the line to S0 in the vestibule passes the opening with 0.45 ft to spare)'),
    'H5': (_HALL_X + 0.15, _HALL_Z,
           'where the hall\'s two legs meet, in front of the shared bath\'s door, on the centre line of the east '
           'leg and 0.15 ft off that of the west leg (the suite entry\'s parked panel stands 0.2 ft into it)'),
    'H0': (RS.R.X_LIV_W - 1.39, _HALL_Z,
           'on the centre line of the hall\'s east leg, 1.4 ft inside its open end (the dining table moved west '
           'with the island: its north-west chair was 0.88 ft from the old place)'),
    # eighth round: the two bedroom doors have leaves now, standing open at 90 degrees inside the rooms
    'Y0': (_FOYER_WALL_C, sum(RS.BED3_ENTRY_Z) / 2,
           'in the middle of Bedroom 3\'s doorway: 1.33 ft from each jamb, 1.24 ft from the open leaf'),
    'Z0': (_FOYER_WALL_C, sum(RS.BED4_ENTRY_Z) / 2,
           'in the middle of Bedroom 4\'s doorway: 1.33 ft from each jamb, 1.23 ft from the open leaf'),
    # eighth round: the garage floor is 11 in lower, with a step at the house door, whose leaf stands open at 90
    # degrees into the garage. On the door's axis (the scene file's stop) the leaf is 1.3 ft from the camera and its
    # lever 1.2 ft
    'G0': (GS.STEP[1] + 1.775, GS.leaf(GS.HOUSE_DOOR)['aabb'][5] + 2.0,
           'on the garage floor 1.8 ft past the step and 2 ft clear of the open leaf of the door to the house'),
    # the living room's stop in front of the sofa: since the seventh round's round coffee table its rim was 0.93 ft
    # from the stop (the grid's low-furniture measure, one cell coarse, read 1.38). 0.6 ft further south it is 1.5 ft
    'L0': (RS.R.X_LIV_W + 10.213, RS.R.ZN + 10.775,
           'in front of the sofa\'s south half, 1.5 ft clear of the round coffee table'),
    # eighth round: the island at the sheet's place
    'K2': (KK.PLAN_CT_E - KK.PLAN_AISLE_E / 2, KK.PLAN_ISLAND[2] + 0.94,
           'in the mouth of the aisle between the island and the east counter, on its centre line (the island\'s '
           'corner was 1.2 ft from the old place)'),
}

# outdoor sweeps: door id of the dimension schedule (centre used when the schedule lacks it), outward
# direction (dx, dz), distance from the door plane, id, label, tour room id
OUTDOOR = [
    # (centres: the front door in the middle of the foyer on the front wall's centre line, 18.43, 47.60; the open
    # way of the living room's four-panel sliding door on the rear wall's centre line, 32.82, 0.02. The schedule's
    # row D14 is the whole 12'-4" unit, whose middle is the edge of a closed panel: door_frames() takes the row's
    # way_start .. way_end)
    {'id': 'OP', 'label': 'Front porch', 'room': 'porch', 'door': 'D01',
     'centre': ((RS.R.X_FOYER_W + RS.R.X_FOYER_E) / 2, (RS.R.Z_FOYER_S + RS.R.Z_PORCH_N) / 2),
     'out': (0.0, 1.0), 'dist': 4.5},
    # (OD was labelled "Rear deck" until the eighth round, whose model has the sheet's landing there. The id and
    # the room key stay: panoramas, pins and the published data are filed under them.)
    {'id': 'OD', 'label': 'Rear landing', 'room': 'deck', 'door': 'D14',
     'centre': (sum(RS.living_slider_way()) / 2, RS.REAR_WALL_C),
     'out': (0.0, -1.0), 'dist': 1.7},
]

STEP = 0.25                            # grid
GRID = (0.25, 39.5, 0.25, 56.0)        # x0, x1, z0, z1 of the indoor grid (inside faces 0.225..39.308; the bay's
#                                        glass stands at z 55.85)
FLOOR_BAND = (-0.03, 0.15)             # floor / rug / tile under a standable cell, against the level of its place
OUT_BAND = (-0.06, 0.15)               # the same for the porch slab and the landings' boards
# Levels (eighth round: sheet A1.3). The house floor is y 0. The first rectangle (x0, x1, z0, z1) that holds a point
# gives the level a person stands on there; everywhere else it is the house floor. A sweep's eye is EYE above its
# level, and every height of a ray (clearance, walking, seeing) is counted from the level of its place.
LEVELS = [
    (tuple(RS.R.ROOMS['garage']), GS.FLOOR_Y),       # garage floor, 11 in below the house floor
    (tuple(XL.PORCH), XL.PORCH_TOP),                 # porch slab
    (tuple(XL.DECK), XL.DECK_TOP),                   # rear landing outside the living room
    (tuple(XL.LANDING), XL.DECK_TOP),                # rear landing outside the primary bedroom
]
# what a walking line may cross besides those levels: the step at the door between the house and the garage (two
# risers of 5 1/2 in). Nobody stands on it: for a sweep it is furniture on the garage floor.
STEPS = [(tuple(GS.STEP), GS.STEP_Y)]
LEVEL_NEAR = 0.3                       # ft: a walking line accepts the level this near (a nosing, a threshold)
CLEAR_HEIGHTS = (0.6, 2.0, 3.5, EYE)
WALK_HEIGHTS = (0.5, 2.0, 3.5, EYE)
WALK_OFFSETS = (-0.45, 0.0, 0.45)
KEEP_SAME = 1e-3                       # ft: --keep, a seed this near its place in the scene file has not been moved
NDIR = 16
DIRS = [(math.sin(2 * math.pi * k / NDIR), -math.cos(2 * math.pi * k / NDIR)) for k in range(NDIR)]
ARCH, FURN, EXT = 0, 1, 2


def P(*a):
    print('[sweeps]', *a, flush=True)


def level(x, z):
    """The level (y) a person stands on at (x, z): LEVELS, else the house floor."""
    for (x0, x1, z0, z1), y in LEVELS:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return y
    return 0.0


def walk_levels(x, z):
    """The levels a walking line may find under (x, z): the level there and within LEVEL_NEAR of it, and a step."""
    r = LEVEL_NEAR
    out = {level(x + dx, z + dz) for dx, dz in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))}
    for (x0, x1, z0, z1), y in STEPS:
        if x0 - r <= x <= x1 + r and z0 - r <= z <= z1 + r:
            out.add(y)
    return out


def on_level(y, x, z, band=FLOOR_BAND, tol=0.0):
    """True when a floor found at height y under (x, z) is the level of that place (floor, rug, tile, boards)."""
    return band[0] - tol <= y - level(x, z) <= band[1] + tol


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--out', required=True, help='sweeps JSON to write')
    ap.add_argument('--overlay', help='top-down review picture (PNG)')
    ap.add_argument('--scene', default=os.path.join(HERE, 'data', 'scene.json'))
    ap.add_argument('--classification', default=os.path.join(HERE, 'data', 'scene_classification.json'))
    ap.add_argument('--measurements', default=os.path.join(HERE, 'data', 'measurements.json'))
    ap.add_argument('--min-clear', type=float, default=1.2)
    ap.add_argument('--relaxed-clear', type=float, default=0.8,
                    help='accepted in rooms that would otherwise have no sweep')
    ap.add_argument('--min-sep', type=float, default=4.0, help='between sweeps that see each other')
    ap.add_argument('--nudge', type=float, default=1.5, help='how far a seed may move to reach clearance')
    ap.add_argument('--garage-max', type=int, default=4)
    ap.add_argument('--max-sweeps', type=int, default=52, help='indoor sweeps; the fill stops there')
    ap.add_argument('--link-max', type=float, default=11.0)
    ap.add_argument('--visible-max', type=float, default=40.0)
    ap.add_argument('--door-radius', type=float, default=3.0, help='a doorway is served by a sweep this near')
    ap.add_argument('--door-sep', type=float, default=3.0, help='spacing accepted for doorway / bridge sweeps')
    ap.add_argument('--tight-clear', type=float, default=1.5,
                    help='fill: a cell with less clearance than this that is not the middle of a passage is used '
                         'only when ...')
    ap.add_argument('--tight-sep', type=float, default=5.0,
                    help='... the nearest sweep it sees is at least this far (a pocket that needs its own sweep)')
    ap.add_argument('--far-cap', type=float, default=5.5,
                    help='fill: distances beyond this count the same, so the most open far cell wins')
    ap.add_argument('--clear-weight', type=float, default=0.8, help='fill: weight of clearance (capped at 3 ft)')
    ap.add_argument('--laundry', choices=('auto', 'on', 'off'), default='auto',
                    help='auto: add the laundry sweep when the model has laundry / washer / dryer objects')
    ap.add_argument('--outdoor', choices=('both', 'each', 'off'), default='both',
                    help='both: porch and landing sweeps only when both qualify; each: independently')
    ap.add_argument('--keep', metavar='SWEEPS.json',
                    help='keep the layout of this sweeps file: its sweeps stay where they are while the model '
                         'leaves them standable, only uncovered floor gets new ones (see the docstring)')
    ap.add_argument('--keep-clear', type=float, default=0.9,
                    help='--keep: a sweep stays in place with at least this clearance')
    ap.add_argument('--mesh-cache', help='npz file that keeps the collected triangles between runs (development)')
    ap.add_argument('--px-per-ft', type=float, default=25.0, help='overlay scale')
    return ap.parse_args(argv)


# ----------------------------------------------------------------------------------------------- geometry
def _collect(want_ext):
    """Triangles of the interior and of the site objects near the porch / the landings, in Blender metres."""
    parents = {ch.name: p.name for p in bpy.data.collections for ch in p.children}

    def chain(name):
        out, k = [name], 0
        while name in parents and k < 12:
            name, k = parents[name], k + 1
            out.append(name)
        return out

    def category(ob):
        cat = None
        for c in ob.users_collection:
            ch = chain(c.name)
            top = ch[-1]
            if top in ('shell', 'openings', 'exterior_shell') or 'ext_garage_door' in ch:
                return ARCH
            if top.startswith('zone_') and top != 'zone_exterior':
                cat = FURN
            elif top == 'zone_exterior' and cat is None:
                cat = EXT
        return cat

    dg = bpy.context.evaluated_depsgraph_get()
    V, T, OWN, names, cats, glass = [], [], [], [], [], []
    base = 0
    for inst in dg.object_instances:
        ob = inst.object
        if ob.type != 'MESH':
            continue
        orig = inst.parent.original if inst.is_instance else ob.original
        if orig.hide_render:
            continue
        cat = category(orig)
        if cat is None:
            continue
        mw = np.array(inst.matrix_world)
        if cat == EXT:
            bb = np.array(ob.bound_box) @ mw[:3, :3].T + mw[:3, 3]
            x0, x1 = bb[:, 0].min() / FT, bb[:, 0].max() / FT
            z0, z1 = -bb[:, 1].max() / FT, -bb[:, 1].min() / FT
            if not any(x1 >= r[0] and x0 <= r[1] and z1 >= r[2] and z0 <= r[3] for r in want_ext):
                continue
            if len(ob.data.polygons) > 150000:      # a whole tree: not an obstacle on the porch or a landing
                continue
        me = ob.to_mesh()
        nv = len(me.vertices)
        if nv == 0:
            ob.to_mesh_clear()
            continue
        co = np.empty(nv * 3, np.float64)
        me.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        me.calc_loop_triangles()
        nt = len(me.loop_triangles)
        tri = np.empty(nt * 3, np.int32)
        me.loop_triangles.foreach_get('vertices', tri)
        mats = [s.material.name.lower() for s in ob.material_slots if s.material]
        ob.to_mesh_clear()
        if nt == 0:
            continue
        V.append(co)
        T.append(tri.reshape(-1, 3) + base)
        OWN.append(np.full(nt, len(names), np.int32))
        names.append(orig.name)
        cats.append(cat)
        glass.append(bool(mats) and all('glass' in m and not any(k in m for k in ('black', 'picture', 'fire'))
                                        for m in mats))
        base += nv
    return {'V': np.concatenate(V), 'T': np.concatenate(T), 'OWN': np.concatenate(OWN),
            'names': np.array(names), 'cats': np.array(cats, np.int8), 'glass': np.array(glass, bool)}


def load_mesh(a, want_ext):
    blend = bpy.data.filepath
    stamp = ''
    if blend:
        st = os.stat(blend)
        stamp = '%s|%d|%d|%s' % (os.path.abspath(blend), st.st_size, int(st.st_mtime), json.dumps(want_ext))
    if a.mesh_cache and os.path.exists(a.mesh_cache):
        z = np.load(a.mesh_cache, allow_pickle=False)
        if not blend or str(z['stamp']) == stamp:
            P('mesh cache', a.mesh_cache)
            return {k: z[k] for k in ('V', 'T', 'OWN', 'names', 'cats', 'glass')}, str(z['blend'])
        P('mesh cache is stale, collecting again')
    if not blend:
        raise SystemExit('place_sweeps: open the built .blend (blender -b <house.blend> --python ...)')
    t = time.time()
    m = _collect(want_ext)
    P('collected %d objects, %d triangles in %.1f s' % (len(m['names']), len(m['T']), time.time() - t))
    if a.mesh_cache:
        os.makedirs(os.path.dirname(os.path.abspath(a.mesh_cache)), exist_ok=True)
        np.savez(a.mesh_cache, stamp=stamp, blend=os.path.basename(blend), **m)
    return m, os.path.basename(blend)


class World:
    """Ray queries in SCENE feet over the interior BVH (and, on request, the site BVH)."""

    def __init__(self, m):
        self.names = [str(n) for n in m['names']]
        self.cats = m['cats']
        self.glass = m['glass']
        own, tri = m['OWN'], m['T']
        ext = self.cats[own] == EXT
        self.own_in, self.own_ext = own[~ext], own[ext]
        verts = m['V'].tolist()
        t = time.time()
        self.bvh_in = BVHTree.FromPolygons(verts, tri[~ext].tolist(), all_triangles=True)
        self.bvh_ext = BVHTree.FromPolygons(verts, tri[ext].tolist(), all_triangles=True) if ext.any() else None
        self.rays = 0
        P('BVH: interior %d triangles, site %d, built in %.1f s' % ((~ext).sum(), ext.sum(), time.time() - t))

    def cast(self, o, d, maxd, site=False):
        """Nearest hit from Blender point o along unit d within maxd ft: (distance ft, owner index) or None."""
        self.rays += 1
        best = None
        loc, _n, idx, dist = self.bvh_in.ray_cast(o, d, maxd * FT)
        if loc is not None:
            best = (dist / FT, int(self.own_in[idx]))
        if site and self.bvh_ext is not None:
            loc, _n, idx, dist = self.bvh_ext.ray_cast(o, d, maxd * FT)
            if loc is not None and (best is None or dist / FT < best[0]):
                best = (dist / FT, int(self.own_ext[idx]))
        return best

    def down(self, x, z, site=False, top=EYE):
        """(floor y, owner) under (x, z) seen from `top`, or None."""
        h = self.cast(ft2bl(x, top, z), Vector((0, 0, -1)), top + 3.0, site)
        return None if h is None else (top - h[0], h[1])

    def ceiling(self, x, z):
        return self.cast(ft2bl(x, EYE, z), Vector((0, 0, 1)), 14.0) is not None

    def ray_clear(self, x, z, cap=4.0, site=False):
        w = cap
        y0 = level(x, z)
        for h in CLEAR_HEIGHTS:
            o = ft2bl(x, y0 + h, z)
            for dx, dz in DIRS:
                hit = self.cast(o, Vector((dx, -dz, 0)), w, site)
                if hit is not None and hit[0] < w:
                    w = hit[0]
        return w

    def los(self, a, b, h, off=0.0, glass_ok=False, site=False):
        """None when the straight line a -> b at height h above the level of each end (shifted `off` ft
        sideways) is clear, else the owner index of the first blocker. Between two levels the line slopes; a line
        below 1 ft runs level, above the higher floor (the lower one's edge is not in the way of a foot)."""
        ax, az = a
        bx, bz = b
        if math.hypot(bx - ax, bz - az) < 1e-6:
            return None
        ya, yb = level(ax, az) + h, level(bx, bz) + h
        if ya != yb and h < 1.0:
            ya = yb = max(ya, yb)
        n = math.hypot(bx - ax, bz - az)
        ux, uz = (bx - ax) / n, (bz - az) / n
        o = ft2bl(ax - uz * off, ya, az + ux * off)
        d = ft2bl(bx - uz * off, yb, bz + ux * off) - o
        L = d.length / FT
        d.normalize()
        t = 0.0
        for _ in range(64):
            hit = self.cast(o + d * (t * FT), d, L - t, site)
            if hit is None or t + hit[0] >= L - 1e-4:
                return None
            if not (glass_ok and self.glass[hit[1]]):
                return hit[1]
            t += hit[0] + 0.01
        return -1

    def see(self, a, b, site=False):
        return self.los(a, b, EYE, site=site) is None

    def visible(self, a, b, site=False):
        return all(self.los(a, b, h, glass_ok=True, site=site) is None for h in (EYE, EYE - 1.0))

    def walk(self, a, b, site=False):
        """'' when a person can walk the straight line a -> b, else what is in the way."""
        for h in WALK_HEIGHTS:
            for off in WALK_OFFSETS:
                k = self.los(a, b, h, off, site=site)
                if k is not None:
                    return '%s at %.1f ft' % (self.names[k] if k >= 0 else 'glass', h)
        # nothing between the floor and the eye in the body's width: low tables, beds and benches, which the
        # rays above can pass over or under
        L = math.dist(a, b)
        if L < 1e-6:
            return ''
        n = max(1, int(math.ceil(L / 0.4)))
        px, pz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        lo, hi = FLOOR_BAND
        for k in range(1, n):
            for off in WALK_OFFSETS:
                x = a[0] + (b[0] - a[0]) * k / n + px * off
                z = a[1] + (b[1] - a[1]) * k / n + pz * off
                f = self.down(x, z, site)
                if f is None:
                    return 'no floor at %.1f, %.1f' % (x, z)
                if not any(lo - 0.07 <= f[0] - y <= hi + 0.07 for y in walk_levels(x, z)):
                    return '%s on the way (top %.2f ft)' % (self.names[f[1]], f[0])
        return ''


# ----------------------------------------------------------------------------------------------- grid
class Grid:
    def __init__(self, w, rooms):
        t = time.time()
        self.w = w
        self.xs = np.arange(GRID[0], GRID[1] + 1e-6, STEP)
        self.zs = np.arange(GRID[2], GRID[3] + 1e-6, STEP)
        nx, nz = len(self.xs), len(self.zs)
        self.rooms = rooms
        self.outdoor_rects = [rooms[k] for k in OUTDOOR_REGIONS if k in rooms]
        self.fy = np.full((nx, nz), np.nan)
        self.stand = np.zeros((nx, nz), bool)
        low = np.zeros((nx, nz), bool)            # furniture below the eye
        for i, x in enumerate(self.xs):
            for j, z in enumerate(self.zs):
                f = w.down(float(x), float(z))
                if f is None:
                    continue
                self.fy[i, j] = f[0]
                if not w.ceiling(float(x), float(z)) or self.is_outdoor(float(x), float(z)):
                    continue
                if on_level(f[0], float(x), float(z)):
                    self.stand[i, j] = True
                else:
                    low[i, j] = True
        # distance to the nearest cell with low furniture (cells), brute force over a 4 ft window
        r = int(round(4.0 / STEP))
        dt = np.full((nx, nz), 4.0 + STEP)
        pad = np.pad(low, r)
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                d = math.hypot(di, dj) * STEP
                if d > 4.0:
                    continue
                sh = pad[r + di:r + di + nx, r + dj:r + dj + nz]
                np.minimum(dt, np.where(sh, d, 99.0), out=dt)
        self.low_dist = dt
        self.cl = np.full((nx, nz), -1.0)
        for i, j in zip(*np.nonzero(self.stand)):
            self.cl[i, j] = min(w.ray_clear(float(self.xs[i]), float(self.zs[j])), max(0.0, dt[i, j] - STEP / 2))
        # ridge: no cell within 0.75 ft is clearly more open (the middle of a passage, not the edge of a room)
        r = int(round(0.75 / STEP))
        pad = np.pad(self.cl, r, constant_values=-1.0)
        top = np.full((nx, nz), -1.0)
        for di in range(-r, r + 1):
            for dj in range(-r, r + 1):
                if math.hypot(di, dj) <= r + 1e-6:
                    np.maximum(top, pad[r + di:r + di + nx, r + dj:r + dj + nz], out=top)
        self.ridge = self.cl >= top - 0.15
        self.reach = np.zeros((nx, nz), bool)
        P('grid %dx%d: standable %.0f sq ft, clearance >= 1.2: %.0f sq ft, %.1f s' % (
            nx, nz, self.stand.sum() * STEP * STEP, (self.cl >= 1.2).sum() * STEP * STEP, time.time() - t))

    def is_outdoor(self, x, z):
        return any(r[0] - 0.2 <= x <= r[1] + 0.2 and r[2] - 0.2 <= z <= r[3] + 0.2 for r in self.outdoor_rects)

    def cell(self, x, z):
        return int(round((x - self.xs[0]) / STEP)), int(round((z - self.zs[0]) / STEP))

    def inside(self, i, j):
        return 0 <= i < self.cl.shape[0] and 0 <= j < self.cl.shape[1]

    def flood(self, points, body=0.9):
        free = self.cl >= body
        stack = []
        for x, z in points:
            i, j = self.cell(x, z)
            best = None
            for di in range(-4, 5):
                for dj in range(-4, 5):
                    if self.inside(i + di, j + dj) and free[i + di, j + dj]:
                        d = di * di + dj * dj
                        if best is None or d < best[0]:
                            best = (d, i + di, j + dj)
            if best:
                stack.append(best[1:])
        while stack:
            i, j = stack.pop()
            if self.reach[i, j]:
                continue
            self.reach[i, j] = True
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if self.inside(i + di, j + dj) and free[i + di, j + dj] and not self.reach[i + di, j + dj]:
                        stack.append((i + di, j + dj))

    def clearance_at(self, x, z):
        """Clearance of an arbitrary point (an old stop): 0 when it is not standable, else the rays' result,
        limited by the low-furniture distance of its grid cell (one cell of tolerance)."""
        f = self.w.down(x, z)
        if f is None or not on_level(f[0], x, z):
            return 0.0
        c = self.w.ray_clear(x, z)
        i, j = self.cell(x, z)
        if self.inside(i, j) and self.stand[i, j]:
            c = min(c, self.low_dist[i, j] + STEP / 2)
        return c

    def cells(self, min_clear, near=None, radius=None):
        """Reachable cells with clearance >= min_clear as (x, z, clearance), optionally within radius of near."""
        ok = self.reach & (self.cl >= min_clear)
        i0 = j0 = 0
        if near is not None:
            ci, cj = self.cell(*near)
            r = int(radius / STEP) + 2
            i0, j0 = max(0, ci - r), max(0, cj - r)
            ok = ok[i0:max(0, ci + r + 1), j0:max(0, cj + r + 1)]
        out = []
        for i, j in zip(*np.nonzero(ok)):
            x, z = float(self.xs[i + i0]), float(self.zs[j + j0])
            if near is None or math.hypot(x - near[0], z - near[1]) <= radius:
                out.append((x, z, float(self.cl[i + i0, j + j0])))
        return out

    def region(self, x, z, slack=0.75):
        """Key of the smallest room rectangle that holds (x, z); the nearest one within `slack` for a point
        in a wall or a doorway; else 'none'."""
        best = None
        for k, (x0, x1, z0, z1) in self.rooms.items():
            d = math.hypot(max(x0 - x, 0, x - x1), max(z0 - z, 0, z - z1))
            if d <= slack:
                key = (d > 0, d, (x1 - x0) * (z1 - z0))
                if best is None or key < best[0]:
                    best = (key, k)
        return best[1] if best else 'none'


# ----------------------------------------------------------------------------------------------- placement
class Layout:
    def __init__(self, w, g, a):
        self.w, self.g, self.a = w, g, a
        self.sw = []                       # dicts: id (or None), x, z, origin, clearance, region, outdoor, ...
        self.adj = []                      # walk adjacency (sets of indices), all walkable pairs <= link_max
        self.parent = []
        self.notes = []

    # union-find over walk links
    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def components(self):
        return len({self.find(i) for i in range(len(self.sw))})

    def linked(self, x, z, site=False):
        """Indices of placed sweeps joined to (x, z) by a walkable line."""
        out = []
        for i, s in enumerate(self.sw):
            if math.hypot(s['x'] - x, s['z'] - z) <= self.a.link_max:
                if not self.w.walk((x, z), (s['x'], s['z']), site or s['outdoor']):
                    out.append(i)
        return out

    def seen_sep(self, x, z):
        """Distance to the nearest placed sweep that (x, z) sees (or that is within 1 ft)."""
        best = 99.0
        for s in self.sw:
            d = math.hypot(s['x'] - x, s['z'] - z)
            if d < best and (d < 1.0 or self.w.see((x, z), (s['x'], s['z']))):
                best = d
        return best

    def add(self, x, z, origin, sid=None, links=None, **kw):
        g = self.g
        i, j = g.cell(x, z)
        s = {'id': sid, 'x': float(x), 'z': float(z), 'origin': origin, 'outdoor': False,
             'region': g.region(x, z), 'clearance': kw.pop('clearance', None)}
        s.update(kw)
        if s['clearance'] is None:
            s['clearance'] = float(g.cl[i, j]) if g.inside(i, j) and g.cl[i, j] >= 0 else self.w.ray_clear(x, z)
        if links is None:
            links = self.linked(x, z, s['outdoor'])
        k = len(self.sw)
        self.sw.append(s)
        self.adj.append(set(links))
        self.parent.append(k)
        for m in links:
            self.adj[m].add(k)
            self.parent[self.find(m)] = self.find(k)
        return k

    def count(self, region):
        return sum(1 for s in self.sw if s['region'] == region and not s['outdoor'])


def place_seed(L, sid, x, z):
    """One of the 19 kept stops at its authored position (x, z), nudged only where clearance fails."""
    w, g, a = L.w, L.g, L.a
    c = g.clearance_at(x, z)
    if c >= a.min_clear:
        return L.add(x, z, 'seed', sid, clearance=c)
    if sid == WALKIN['id']:
        k = place_walkin(L, x, z, c)
        if k is not None:
            return k
    # nudge: the best clear cell within reach that the seed position can see
    best = None
    for cx, cz, cc in g.cells(a.relaxed_clear, (x, z), a.nudge):
        if not w.see((x, z), (cx, cz)):
            continue
        d = math.hypot(cx - x, cz - z)
        key = (cc >= a.min_clear, min(cc, a.min_clear + 0.4) - 0.35 * d)
        if best is None or key > best[0]:
            best = (key, cx, cz, cc, d)
    if best and (best[3] >= a.min_clear or best[3] >= c + 0.15 or c < a.relaxed_clear):
        _, cx, cz, cc, d = best
        L.notes.append('seed %s: clearance %.2f ft, moved %.2f ft to (%.2f, %.2f), clearance %.2f ft%s' % (
            sid, c, d, cx, cz, cc, '' if cc >= a.min_clear else ' (no cell with %.1f ft within %.1f ft)'
            % (a.min_clear, a.nudge)))
        return L.add(cx, cz, 'seed-moved', sid, clearance=cc, moved=round(d, 2))
    if c >= a.relaxed_clear:
        L.notes.append('seed %s: clearance %.2f ft, kept (no better cell within %.1f ft; >= %.1f ft is accepted '
                       'in a room that would otherwise have no sweep)' % (sid, c, a.nudge, a.relaxed_clear))
        return L.add(x, z, 'seed', sid, clearance=c)
    # the model changed under the stop (it stands in or against something): rather than lose an id
    # that measurements, design views and highlights name, take the nearest clear cell of its room
    here = g.region(x, z)
    far = [(math.hypot(cx - x, cz - z), cx, cz, cc) for cx, cz, cc in g.cells(a.min_clear, (x, z), 6.0)
           if g.region(cx, cz) == here]
    k = None
    if far:
        d, cx, cz, cc = min(far)
        L.notes.append('seed %s: clearance %.2f ft and no clear cell within %.1f ft; MOVED %.2f ft to '
                       '(%.2f, %.2f), clearance %.2f ft: check it' % (sid, c, a.nudge, d, cx, cz, cc))
        k = L.add(cx, cz, 'seed-moved', sid, clearance=cc, moved=round(d, 2))
    else:
        L.notes.append('seed %s: clearance %.2f ft and no clear cell of its room within 6 ft: DROPPED'
                       % (sid, c))
    P('WARNING:', L.notes[-1])
    return k


def place_walkin(L, x, z, c):
    """The walk-in closet's stop when its place (x, z) has lost its clearance c: the most open reachable cell
    inside the closet (clearance compared in tenths of a foot), among equals the one nearest the axis of the pocket
    door and then the closet's middle. None when the closet has no clear cell (the seed rule then decides)."""
    g, a = L.g, L.a
    x0, x1, z0, z1 = WALKIN['clear']
    if not (x0 <= x <= x1 and z0 <= z <= z1):
        return None                               # the stop is not in the closet: an older plan
    zc = (WALKIN['door_z'][0] + WALKIN['door_z'][1]) / 2
    cells = [((round(cc, 1), -abs(cz - zc), -abs(cx - (x0 + x1) / 2)), cx, cz, cc)
             for cx, cz, cc in g.cells(a.min_clear) if x0 < cx < x1 and z0 < cz < z1]
    if not cells:
        return None
    _, cx, cz, cc = max(cells)
    d = math.hypot(cx - x, cz - z)
    L.notes.append('walk-in closet: seed %s has %.2f ft of clearance at (%.2f, %.2f) (the south rod hangs there); '
                   'moved %.2f ft to the most open cell of the aisle, (%.2f, %.2f), clearance %.2f ft, %.2f ft '
                   'off the axis of the pocket door' % (WALKIN['id'], c, x, z, d, cx, cz, cc, abs(cz - zc)))
    return L.add(cx, cz, 'seed-moved', WALKIN['id'], clearance=cc, moved=round(d, 2))


def place_hand(L, kept=None):
    """The stops of PLACED whose place is free. Returns their ids (the other rules leave those ids alone)."""
    g, a = L.g, L.a
    was = {k['id']: k for k in kept or ()}
    done = set()
    for sid, (x, z, why) in PLACED.items():
        c = g.clearance_at(x, z)
        i, j = g.cell(x, z)
        near = [(di * di + dj * dj) for di in range(-2, 3) for dj in range(-2, 3)
                if g.inside(i + di, j + dj) and g.reach[i + di, j + dj]]
        k = was.get(sid)
        if c < a.keep_clear or not near:
            L.notes.append('placed %s: (%.2f, %.2f) has %.2f ft of clearance%s: not used, the usual rules decide'
                           % (sid, x, z, c, '' if near else ' and is not on reachable floor'))
            P('WARNING:', L.notes[-1])
            continue
        done.add(sid)
        if k is not None and math.hypot(k['x'] - x, k['z'] - z) <= 1e-4:
            L.add(x, z, k['origin'], sid, clearance=c, keep=k)          # it stands there already
            continue
        kw = {'label': k['label'], 'room': k['room']} if k is not None and k['room'] else {}
        L.add(x, z, 'placed', sid, clearance=c, **kw)
        L.notes.append('placed %s at (%.2f, %.2f), clearance %.2f ft%s: %s' % (
            sid, x, z, c, '' if k is None else ', %.2f ft from (%.2f, %.2f)' % (
                math.hypot(k['x'] - x, k['z'] - z), k['x'], k['z']), why))
    return done


def place_seeds(L, old, kept=None, skip=()):
    """The 19 kept stops, nudged only where clearance fails. With a kept layout (--keep) only the seeds that
    layout does not list (place_kept dealt with the others, also with those it dropped)."""
    listed = {k['id'] for k in kept or ()} | set(skip)
    for sid in SEEDS:
        if sid in listed:
            continue
        n = old.get(sid)
        if n is None:
            P('WARNING: seed %s is not in the scene file; skipped' % sid)
            continue
        if kept is not None:
            L.notes.append('seed %s is not in the kept layout: placed from the scene file' % sid)
        place_seed(L, sid, n['p'][0], n['p'][2])


def load_keep(path):
    """The sweeps of an installed layout (--keep) as dicts id, x, z, yaw, pitch (degrees), label, room, outdoor,
    origin, links; and the file's own description of where it came from."""
    try:
        doc = json.load(open(path))
        rows = doc['sweeps']
        deg = (doc.get('units') or {}).get('angle', 'deg') != 'rad'
        ang = (lambda v: float(v)) if deg else (lambda v: math.degrees(float(v)))
        out = [{'id': r['id'], 'x': float(r['p'][0]), 'z': float(r['p'][2]), 'yaw': ang(r.get('yaw', 0.0)),
                'pitch': ang(r.get('pitch', 0.0)), 'label': r.get('label') or r['id'], 'room': r.get('room') or '',
                'outdoor': bool(r.get('outdoor', False)), 'origin': r.get('origin') or 'keep',
                'links': list(r.get('links', []))} for r in rows]
    except (OSError, ValueError, KeyError, TypeError, IndexError) as e:
        raise SystemExit('place_sweeps: cannot read the layout to keep, %s: %r' % (path, e))
    if not out or len({k['id'] for k in out}) != len(out):
        raise SystemExit('place_sweeps: %s has no sweeps or repeats an id' % path)
    return out, '%s (%s)' % (os.path.basename(path), doc.get('generated_from', '?'))


def place_kept(L, kept, old, skip=()):
    """--keep: the indoor sweeps of an installed layout stay exactly where they are while the model leaves them
    standable; the others follow the scene (a seed the scene moved), are nudged, or are dropped with a note.
    The laundry sweep and the outdoor sweeps are left to place_laundry / place_outdoor."""
    w, g, a = L.w, L.g, L.a
    later = []
    for k in kept:
        sid, x, z = k['id'], k['x'], k['z']
        if k['outdoor'] or sid == LAUNDRY['id'] or sid in skip:
            continue
        n = old.get(sid)
        if sid in SEEDS and k['origin'] == 'seed' and n is not None \
                and math.hypot(n['p'][0] - x, n['p'][2] - z) > KEEP_SAME:
            later.append((k, None))
            continue
        c = g.clearance_at(x, z)
        if c < a.keep_clear:
            later.append((k, c))
            continue
        # the number a sweep on a grid cell was given when it was placed, so an untouched room reads the same
        i, j = g.cell(x, z)
        on_cell = g.inside(i, j) and g.cl[i, j] >= 0 and abs(g.xs[i] - x) < 1e-6 and abs(g.zs[j] - z) < 1e-6
        L.add(x, z, k['origin'], sid, clearance=float(g.cl[i, j]) if on_cell and k['origin'] not in (
            'seed', 'approach') else c, keep=k)
    stay = len(L.sw)
    for k, c in later:
        sid, x, z = k['id'], k['x'], k['z']
        if c is None:                              # a seed on its authored position, and the scene moved it
            n = old[sid]
            sx, sz = n['p'][0], n['p'][2]
            L.notes.append('keep %s: the scene file has moved this seed %.2f ft, from (%.2f, %.2f) to (%.2f, %.2f) '
                           '(clearance at the old place now %.2f ft): it follows the scene'
                           % (sid, math.hypot(sx - x, sz - z), x, z, sx, sz, g.clearance_at(x, z)))
            place_seed(L, sid, sx, sz)
            continue
        if sid in SEEDS:                           # never lose an id the measurements and design views name
            n = old.get(sid)                       # its stop in the scene file is its place in today's model
            sx, sz = (n['p'][0], n['p'][2]) if n is not None else (x, z)
            L.notes.append('keep %s: clearance %.2f ft < %.1f ft at (%.2f, %.2f): the seed rule decides, from the '
                           'scene file\'s stop (%.2f, %.2f)' % (sid, c, a.keep_clear, x, z, sx, sz))
            i = place_seed(L, sid, sx, sz)
            if i is not None:
                L.sw[i]['keep'] = k
            continue
        best = None
        for cx, cz, cc in g.cells(a.min_clear, (x, z), a.nudge):
            if not w.see((x, z), (cx, cz)) or L.seen_sep(cx, cz) < a.door_sep:
                continue
            d = math.hypot(cx - x, cz - z)
            key = min(cc, a.min_clear + 0.4) - 0.35 * d
            if (best is None or key > best[0]) and L.linked(cx, cz):
                best = (key, cx, cz, cc, d)
        if best is None:
            L.notes.append('keep %s: clearance %.2f ft < %.1f ft at (%.2f, %.2f) and no clear cell within %.1f ft '
                           'that it sees, >= %.1f ft from the other sweeps and joined to them: DROPPED'
                           % (sid, c, a.keep_clear, x, z, a.nudge, a.door_sep))
        else:
            _, cx, cz, cc, d = best
            L.add(cx, cz, k['origin'], sid, clearance=cc, keep=k, moved=round(d, 2))
            L.notes.append('keep %s: clearance %.2f ft < %.1f ft at (%.2f, %.2f), moved %.2f ft to (%.2f, %.2f), '
                           'clearance %.2f ft' % (sid, c, a.keep_clear, x, z, d, cx, cz, cc))
    P('keep: %d sweeps stay in place, %d decided otherwise' % (stay, len(later)))


def has_laundry(a):
    """True when the model has the laundry closet: a mesh named laundry / washer / dryer (whole words, so
    not the dishwasher) standing inside the closet's rectangle."""
    if a.laundry != 'auto':
        return a.laundry == 'on'
    x0, x1, z0, z1 = LAUNDRY['outer']
    pat = re.compile(r'(?<![a-z])(%s)(?![a-z])' % '|'.join(LAUNDRY['names']))
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render or not pat.search(ob.name.lower()):
            continue
        c = sum((ob.matrix_world @ Vector(v) for v in ob.bound_box), Vector()) / 8
        if x0 - 1 <= c.x / FT <= x1 + 1 and z0 - 1 <= -c.y / FT <= z1 + 1:
            return True
    return False


def place_laundry(L):
    """One sweep facing the laundry closet's open doors, when the model has the closet: on the axis of the
    opening, LAUNDRY['dist'] in front of the door wall; the nearest clear cell that sees the opening when that
    point is not free."""
    w, g, a = L.w, L.g, L.a
    sid = LAUNDRY['id']
    if not has_laundry(a):
        L.notes.append('laundry closet: no laundry / washer / dryer object in the model, sweep %s skipped' % sid)
        P('WARNING:', L.notes[-1])
        return
    ox, oz = LAUNDRY['out']
    zc = (LAUNDRY['door_z'][0] + LAUNDRY['door_z'][1]) / 2
    face = (LAUNDRY['door_face'], zc)                     # middle of the opening on the foyer side
    opening = (LAUNDRY['door_c'], zc)                     # ... inside the wall's thickness
    units = ((LAUNDRY['clear'][0] + LAUNDRY['clear'][1]) / 2, zc)
    tx, tz = face[0] + ox * LAUNDRY['dist'], face[1] + oz * LAUNDRY['dist']
    c = g.clearance_at(tx, tz)
    if c >= a.min_clear and w.see((tx, tz), opening):
        best = (0.0, tx, tz, c)
    else:
        best = None
        for cx, cz, cc in g.cells(a.min_clear, (tx, tz), 2.5):
            if (cx - face[0]) * ox + (cz - face[1]) * oz < 1.5 or not w.see((cx, cz), opening):
                continue
            d = math.hypot(cx - tx, cz - tz)
            if best is None or d < best[0]:
                best = (d, cx, cz, cc)
    if best is None:
        L.notes.append('laundry closet: (%.2f, %.2f) has %.2f ft of clearance and no clear cell within 2.5 ft sees '
                       'the opening, sweep %s skipped' % (tx, tz, c, sid))
        P('WARNING:', L.notes[-1])
        return
    d, cx, cz, cc = best
    near = [s for s in L.sw if math.hypot(s['x'] - cx, s['z'] - cz) < a.door_sep]
    L.add(cx, cz, 'laundry', sid, clearance=cc, aim=units, pitch=LAUNDRY['pitch'], label=LAUNDRY['label'])
    L.notes.append('laundry closet: sweep %s at (%.2f, %.2f), %.2f ft in front of the door wall%s, clearance %.2f ft%s'
                   % (sid, cx, cz, (cx - face[0]) * ox + (cz - face[1]) * oz,
                      '' if d < 1e-6 else ' (%.2f ft from the opening\'s axis point)' % d, cc,
                      '' if not near else '; closer than %.1f ft to %s' % (a.door_sep, ' '.join(
                          str(s['id']) for s in near))))


def place_approach(L, old):
    """Old approach stops: kept for connectivity (joins separate parts of the walk graph) or spacing."""
    g, a = L.g, L.a
    cand = {}
    for sid, xz in APPROACH.items():
        if any(s['id'] == sid for s in L.sw):
            continue                              # set by hand (PLACED)
        x, z = (old[sid]['p'][0], old[sid]['p'][2]) if sid in old else xz
        c = g.clearance_at(x, z)
        if c < a.min_clear:
            L.notes.append('approach %s: clearance %.2f ft < %.1f ft, dropped' % (sid, c, a.min_clear))
            continue
        cand[sid] = (x, z, c)
    while cand:
        best = None
        for sid, (x, z, c) in cand.items():
            links = L.linked(x, z)
            comps = len({L.find(i) for i in links})
            sep = L.seen_sep(x, z)
            if comps >= 2 and sep >= a.door_sep:
                key = (comps, sep)
                if best is None or key > best[0]:
                    best = (key, sid, links)
        if best is None:
            break
        (comps, sep), sid, links = best
        x, z, c = cand.pop(sid)
        L.add(x, z, 'approach', sid, links, clearance=c)
        L.notes.append('approach %s: kept for connectivity (joins %d parts of the walk graph; %.2f ft from the '
                       'nearest sweep it sees)' % (sid, comps, sep))
    for sid in sorted(cand, key=lambda s: -L.seen_sep(*cand[s][:2])):
        x, z, c = cand[sid]
        sep = L.seen_sep(x, z)
        links = L.linked(x, z)
        if sep >= a.min_sep and links:
            L.add(x, z, 'approach', sid, links, clearance=c)
            L.notes.append('approach %s: kept for spacing (%.2f ft from the nearest sweep it sees)' % (sid, sep))
        else:
            L.notes.append('approach %s: dropped (%.2f ft from the nearest sweep it sees, joins nothing new)'
                           % (sid, sep))


def door_frames(meas):
    """Doors of the dimension schedule as (id, name, centre x, centre z, normal (dx, dz), half width)."""
    out = []
    for d in (meas or {}).get('doors', []):
        if not all(isinstance(d.get(k), (int, float)) for k in ('c', 'start', 'end')):
            continue
        s0, s1 = d['start'], d['end']
        if all(isinstance(d.get(k), (int, float)) for k in ('way_start', 'way_end')):
            s0, s1 = d['way_start'], d['way_end']     # a sliding unit: the way its open panel leaves
        mid, half = (s0 + s1) / 2, abs(s1 - s0) / 2
        if d.get('axis') == 'x':                  # the wall runs along x at z = c
            out.append((d.get('id', '?'), d.get('name', ''), mid, d['c'], (0.0, 1.0), half))
        elif d.get('axis') == 'z':                # the wall runs along z at x = c
            out.append((d.get('id', '?'), d.get('name', ''), d['c'], mid, (1.0, 0.0), half))
    return out


def place_doors(L, meas):
    """A sweep in or just inside every interior doorway that no sweep serves yet."""
    w, g, a = L.w, L.g, L.a
    for did, name, cx, cz, (nx, nz), half in door_frames(meas):
        tx, tz = -nz, nx                          # along the wall
        zone, sides = [], set()
        for x, z, c in g.cells(a.min_clear, (cx, cz), 3.2):
            off = (x - cx) * nx + (z - cz) * nz
            lat = (x - cx) * tx + (z - cz) * tz
            if abs(off) <= 2.5 and abs(lat) <= max(0.3, half - 0.3):
                zone.append((x, z, c, off, lat))
        for x, z, c in g.cells(0.9, (cx, cz), 3.2):
            off = (x - cx) * nx + (z - cz) * nz
            if abs((x - cx) * tx + (z - cz) * tz) <= half and 0.4 < abs(off) <= 2.5 and w.see((x, z), (cx, cz)):
                sides.add(off > 0)
        if len(sides) < 2:
            continue                              # closet, vehicle door, exterior door: nothing to walk to
        served = [s for s in L.sw if math.hypot(s['x'] - cx, s['z'] - cz) <= a.door_radius
                  and w.see((s['x'], s['z']), (cx, cz))]
        if served:
            continue
        best = None
        for x, z, c, off, lat in zone:
            if L.seen_sep(x, z) < a.door_sep:
                continue
            key = -abs(off) + 0.5 * min(c, 2.0) - 0.3 * abs(lat)
            if best is None or key > best[0]:
                best = (key, x, z, c, off)
        if best is None:
            L.notes.append('door %s (%s): no sweep within %.1f ft and no clear cell >= %.1f ft from the others'
                           % (did, name, a.door_radius, a.door_sep))
            continue
        _, x, z, c, off = best
        links = L.linked(x, z)
        if not links:
            L.notes.append('door %s (%s): best cell (%.2f, %.2f) has no walkable link, skipped' % (did, name, x, z))
            continue
        L.add(x, z, 'door', None, links, clearance=c)
        L.notes.append('door %s (%s): sweep {ids:%d} at (%.2f, %.2f), %.2f ft from the door plane, clearance '
                       '%.2f ft' % (did, name, len(L.sw) - 1, x, z, abs(off), c))


def bridge(L, min_clear, tag):
    """Join separate parts of the walk graph with one sweep each where a single cell can."""
    w, g, a = L.w, L.g, L.a
    guard = 0
    while L.components() > 1 and guard < 12:
        guard += 1
        comps = collections.defaultdict(list)
        for i in range(len(L.sw)):
            comps[L.find(i)].append(i)
        order = sorted(comps.values(), key=len)
        done = False
        for comp in order[:-1]:
            best = None
            seen = set()
            for i in comp:
                s = L.sw[i]
                for x, z, c in g.cells(min_clear, (s['x'], s['z']), 7.0):
                    if (x, z) in seen:
                        continue
                    seen.add((x, z))
                    if w.walk((x, z), (s['x'], s['z'])):
                        continue
                    sep = L.seen_sep(x, z)
                    if sep < 2.0:
                        continue
                    links = L.linked(x, z)
                    n = len({L.find(k) for k in links})
                    if n < 2 or i not in links:
                        continue
                    # short legs to both sides (a sweep near the doorway), not too close to the others
                    here = L.find(i)
                    legs = [min(math.hypot(L.sw[k]['x'] - x, L.sw[k]['z'] - z) for k in links if side(L.find(k)))
                            for side in (lambda r: r == here, lambda r: r != here)]
                    key = (n, sep >= a.door_sep, -max(legs) + 0.3 * min(c, 2.0))
                    if best is None or key > best[0]:
                        best = (key, x, z, c, links, sep)
            if best:
                _, x, z, c, links, sep = best
                L.add(x, z, tag, None, links, clearance=c)
                L.notes.append('bridge: sweep {ids:%d} at (%.2f, %.2f) joins %d parts of the walk graph ({ids:%s}), '
                               'clearance %.2f ft, %.2f ft from the nearest sweep it sees' % (
                                   len(L.sw) - 1, x, z, best[0][0], ','.join(map(str, comp)), c, sep))
                done = True
                break
        if not done:
            break


def fill(L):
    """Greedy fill: the cell farthest from the sweeps it sees, the most open one among the far ones."""
    w, g, a = L.w, L.g, L.a
    pool = [c for c in g.cells(a.min_clear) if not g.is_outdoor(c[0], c[1])]
    px = np.array([c[0] for c in pool])
    pz = np.array([c[1] for c in pool])
    clr = np.minimum(np.array([c[2] for c in pool]), 3.0)
    # a tight cell is fine in the middle of a passage; at the edge of a room it must be a pocket of its own
    tight = np.array([c[2] < a.tight_clear and not g.ridge[g.cell(c[0], c[1])] for c in pool])
    region = [g.region(c[0], c[1]) for c in pool]
    score = np.full(len(pool), 30.0)
    alive = np.ones(len(pool), bool)

    def update(sx, sz):
        d = np.hypot(px - sx, pz - sz)
        for i in np.nonzero((d < score) & (d < 25.0))[0]:
            if d[i] < 1.0 or w.see((float(px[i]), float(pz[i])), (sx, sz)):
                score[i] = d[i]

    for s in L.sw:
        update(s['x'], s['z'])
    n0 = len(L.sw)
    while sum(1 for s in L.sw if not s['outdoor']) < a.max_sweeps:
        ok = alive & (score >= np.where(tight, a.tight_sep, a.min_sep))
        key = np.where(ok, np.minimum(score, a.far_cap) + a.clear_weight * clr + 0.02 * np.minimum(score, 25.0), -1.0)
        i = int(np.argmax(key))
        if key[i] < 0:
            break
        x, z = float(px[i]), float(pz[i])
        if (region[i] == 'garage' and L.count('garage') >= a.garage_max) or (
                region[i] in FILL_ONE and L.count(region[i]) >= 1):
            alive[i] = False
            continue
        links = L.linked(x, z)
        if not links:
            alive[i] = False
            continue
        L.add(x, z, 'fill', None, links, clearance=float(pool[i][2]))
        update(x, z)
    P('fill: %d sweeps added' % (len(L.sw) - n0))


def cover_regions(L):
    """Every room region with reachable floor gets a sweep (clearance down to --relaxed-clear)."""
    g, a = L.g, L.a
    have = {s['region'] for s in L.sw}
    for k in list(have):
        if REGIONS.get(k, (None, None, None))[2]:
            have.add(REGIONS[k][2])
    report = {}
    for key in g.rooms:
        if key in OUTDOOR_REGIONS:
            continue
        parent = REGIONS.get(key, (None, None, None))[2]
        if key in have or (parent and parent in have):
            continue
        cells = [c for c in g.cells(a.relaxed_clear) if g.region(c[0], c[1]) == key]
        best = None
        for x, z, c in sorted(cells, key=lambda c: -c[2])[:60]:
            links = L.linked(x, z)
            if links:
                best = (x, z, c, links)
                break
        if best is None:
            report[key] = 'no reachable floor with %.1f ft clearance' % a.relaxed_clear
            continue
        x, z, c, links = best
        L.add(x, z, 'region', None, links, clearance=c)
        L.notes.append('region %s had no sweep: added {ids:%d} at (%.2f, %.2f), clearance %.2f ft'
                       % (key, len(L.sw) - 1, x, z, c))
    for key, why in report.items():
        L.notes.append('region %s: no sweep (%s)' % (key, why))


def place_outdoor(L, meas, kept=None):
    """Porch and landing sweeps, each only when a walkable line through its open door reaches an indoor sweep.
    An outdoor sweep of a kept layout (--keep) stays where it is while it still stands free and that line
    exists; otherwise it is looked for again."""
    w, g, a = L.w, L.g, L.a
    if a.outdoor == 'off':
        L.notes.append('outdoor sweeps: switched off')
        return
    doors = {d[0]: d for d in door_frames(meas)}
    stay = {k['id']: k for k in kept or () if k['outdoor']}
    plans, why = [], []
    for o in OUTDOOR:
        k = stay.get(o['id'])
        if k is not None:
            f = w.down(k['x'], k['z'], site=True)
            c = w.ray_clear(k['x'], k['z'], site=True) if f is not None and level(k['x'], k['z']) != 0.0 \
                and on_level(f[0], k['x'], k['z'], OUT_BAND) else 0.0
            links = L.linked(k['x'], k['z'], site=True) if c >= a.keep_clear else []
            if links:
                L.add(k['x'], k['z'], 'outdoor', o['id'], links, clearance=c, outdoor=True, floor=f[0], keep=k)
                L.sw[-1]['region'] = k['room'] or o['room']
                continue
            L.notes.append('keep %s (%s): %s at (%.2f, %.2f); looked for again' % (
                o['id'], o['label'], 'clearance %.2f ft < %.1f ft' % (c, a.keep_clear) if c < a.keep_clear
                else 'no walkable straight line to an indoor sweep', k['x'], k['z']))
        cx, cz = (doors[o['door']][2], doors[o['door']][3]) if o['door'] in doors else o['centre']
        ox, oz = o['out']
        tx, tz = cx + ox * o['dist'], cz + oz * o['dist']
        cells = []
        for i in range(-12, 13):
            for j in range(-12, 13):
                x, z = tx + i * STEP, tz + j * STEP
                off = (x - cx) * ox + (z - cz) * oz
                if off < 1.0 or math.hypot(x - tx, z - tz) > 3.0:
                    continue
                f = w.down(x, z, site=True)
                if f is None or level(x, z) == 0.0 or not on_level(f[0], x, z, OUT_BAND):
                    continue                      # not on the porch slab or a landing
                c = w.ray_clear(x, z, site=True)
                if c >= a.min_clear:
                    cells.append((math.hypot(x - tx, z - tz) - 0.3 * min(c, 2.5), x, z, c, f[0]))
        if not cells:
            why.append('%s (%s): no outdoor floor with %.1f ft clearance near (%.1f, %.1f)'
                       % (o['id'], o['label'], a.min_clear, tx, tz))
            continue
        found, blocked = None, ''
        for _, x, z, c, fy in sorted(cells)[:40]:
            links = L.linked(x, z, site=True)
            if links:
                found = (x, z, c, fy, links, None)
                break
            if not blocked:
                near = min((s for s in L.sw if not s['outdoor']), key=lambda s: math.hypot(s['x'] - x, s['z'] - z))
                blocked = '%s -> %s: %s' % (near['id'] or 'new sweep', o['id'],
                                            w.walk((near['x'], near['z']), (x, z), site=True))
        if found is None:
            # an indoor sweep just inside the door that joins the outdoor cell to the tour
            x, z, c, fy = sorted(cells)[0][1:]
            best = None
            for ix, iz, ic in g.cells(a.min_clear, (cx, cz), 4.5):
                if (ix - cx) * ox + (iz - cz) * oz > -0.3 or L.seen_sep(ix, iz) < a.door_sep:
                    continue
                if w.walk((ix, iz), (x, z), site=True):
                    continue
                links = L.linked(ix, iz)
                if links:
                    key = min(ic, 2.0) - 0.3 * math.hypot(ix - cx, iz - cz)
                    if best is None or key > best[0]:
                        best = (key, ix, iz, ic, links)
            if best:
                found = (x, z, c, fy, None, best[1:])
        if found is None:
            why.append('%s (%s): no walkable straight line from an indoor sweep through the door (%s)'
                       % (o['id'], o['label'], blocked or 'no indoor sweep within %.0f ft' % a.link_max))
            continue
        plans.append((o, (cx, cz), found))
    if why and (a.outdoor == 'both' or not plans):
        L.notes.append('outdoor sweeps: none added. ' + '; '.join(why)
                       + ('' if not plans else '; %s would qualify (use --outdoor each)'
                          % ', '.join(p[0]['id'] for p in plans)))
        P('WARNING:', L.notes[-1])
        return
    for o, centre, (x, z, c, fy, links, inner) in plans:
        if inner:
            ix, iz, ic, ilinks = inner
            L.add(ix, iz, 'door', None, ilinks, clearance=ic)
            L.notes.append('outdoor %s: indoor sweep {ids:%d} added just inside the door at (%.2f, %.2f)'
                           % (o['id'], len(L.sw) - 1, ix, iz))
        L.add(x, z, 'outdoor', o['id'], links, clearance=c, outdoor=True, floor=fy, aim=centre,
              label=o['label'], room=o['room'])
        L.sw[-1]['region'] = o['room']
        L.notes.append('outdoor %s (%s): sweep at (%.2f, %.2f), clearance %.2f ft, floor %.2f ft, walkable from '
                       '{ids:%s}' % (o['id'], o['label'], x, z, c, fy, ','.join(map(str, sorted(L.adj[-1])))))
    for y in why:
        L.notes.append('outdoor: ' + y)


# ----------------------------------------------------------------------------------------------- graph, metadata
def build_graph(L):
    """(links, visible) as index sets per sweep, the kept links {(i, j): ft}, number of walkable pairs."""
    w, a = L.w, L.a
    n = len(L.sw)
    pts = [(s['x'], s['z']) for s in L.sw]
    E = {}
    for i in range(n):
        for j in L.adj[i]:
            if i < j:
                E[(i, j)] = math.dist(pts[i], pts[j])
    adj = [set(L.adj[i]) for i in range(n)]
    keep = {}
    for (i, j), d in E.items():
        via = any(c in adj[j] and math.dist(pts[i], pts[c]) + math.dist(pts[c], pts[j]) < 1.2 * d
                  and max(math.dist(pts[i], pts[c]), math.dist(pts[c], pts[j])) < d for c in adj[i])
        if not via:
            keep[(i, j)] = d
    links = [set() for _ in range(n)]
    for i, j in keep:
        links[i].add(j)
        links[j].add(i)
    vis = [set(links[i]) for i in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if j in vis[i] or math.dist(pts[i], pts[j]) > a.visible_max:
                continue
            if w.visible(pts[i], pts[j], site=L.sw[i]['outdoor'] or L.sw[j]['outdoor']):
                vis[i].add(j)
                vis[j].add(i)
    return links, vis, keep, len(E)


def bfs(links, s):
    dist = {s: 0}
    q = collections.deque([s])
    while q:
        v = q.popleft()
        for u in links[v]:
            if u not in dist:
                dist[u] = dist[v] + 1
                q.append(u)
    return dist


def open_yaw(w, x, z, extent):
    """Yaw (deg) of the most open direction at eye height, limited to the house's extent."""
    n = 72
    free = []
    for k in range(n):
        ang = 2 * math.pi * k / n
        dx, dz = math.sin(ang), -math.cos(ang)
        lim = 30.0
        if dx > 1e-6:
            lim = min(lim, (extent[1] - x) / dx)
        elif dx < -1e-6:
            lim = min(lim, (extent[0] - x) / dx)
        if dz > 1e-6:
            lim = min(lim, (extent[3] - z) / dz)
        elif dz < -1e-6:
            lim = min(lim, (extent[2] - z) / dz)
        lim = max(lim, 0.1)
        hit = w.cast(ft2bl(x, level(x, z) + EYE, z), Vector((dx, -dz, 0)), lim)
        free.append(min(lim if hit is None else hit[0], 20.0))
    half = 5                                      # +-25 degrees
    best = max(range(n), key=lambda k: sum(free[(k + d) % n] for d in range(-half, half + 1)))
    yaw = 360.0 * best / n
    return yaw - 360.0 if yaw > 180.0 else yaw


def yaw_to(x, z, tx, tz):
    return math.degrees(math.atan2(tx - x, -(tz - z)))


def assign_ids(L, kept=None):
    """Ids for the new sweeps; never one of the old stops or of a kept layout, whether that sweep is still there
    or not (its panorama exists under that name)."""
    used = set(OLD_IDS) | {s['id'] for s in L.sw if s['id']} | {k['id'] for k in kept or ()}
    for s in L.sw:
        if s['id']:
            continue
        letter = REGIONS.get(s['region'], (None, 'N', None))[1]
        sid = next((letter + c for c in ID_CHARS if letter + c not in used), None)
        if sid is None:
            sid = next(a + b for a in 'NQUVW' for b in ID_CHARS if a + b not in used)
        used.add(sid)
        s['id'] = sid


def kept_renames(kept, old):
    """--keep: {(label, room) in the kept layout: label in the scene file} for the seeds the scene file has renamed
    since. Left out when seeds that shared a label and a room no longer agree on one."""
    votes = collections.defaultdict(set)
    for k in kept or ():
        n = old.get(k['id'])
        if k['id'] in SEEDS and n is not None:
            votes[(k['label'], k['room'])].add(n.get('label') or n.get('name') or k['label'])
    return {key: next(iter(v)) for key, v in votes.items() if len(v) == 1 and next(iter(v)) != key[0]}


def describe(L, old, extent, kept=None):
    """label, room, yaw, pitch, floor for every sweep."""
    w = L.w
    renames = kept_renames(kept, old)
    outdoor = {o['id']: o['label'] for o in OUTDOOR}
    for s in L.sw:
        x, z = s['x'], s['z']
        if s.get('keep'):                         # a sweep of the kept layout: its view and its room stay,
            k = s['keep']                         # its name follows the scene file (a seed's own stop, or the
            n = old.get(s['id']) if s['id'] in SEEDS else None          # renamed seed whose label it carried)
            label = (n.get('label') or n.get('name') or k['label']) if n is not None \
                else renames.get((k['label'], k['room']), k['label'])
            if s['outdoor'] and s['id'] in outdoor:                     # an outdoor sweep: OUTDOOR names it
                label = outdoor[s['id']]
            if label != k['label']:
                s['renamed'] = k['label']
            s['label'], s['room'], s['yaw'], s['pitch'] = label, k['room'] or s['region'], k['yaw'], k['pitch']
            if 'floor' not in s:
                f = w.down(x, z, s['outdoor'])
                s['floor'] = f[0] if f else level(x, z)
            continue
        n = old.get(s['id']) if s['origin'] in ('seed', 'seed-moved') or (
            s['origin'] == 'placed' and s['id'] in SEEDS) else None
        princ = [old[k] for k in REGIONS.get(s['region'], ([], None, None))[0] if k in old]
        near = min(princ, key=lambda p: math.hypot(p['p'][0] - x, p['p'][2] - z)) if princ else None
        if n is not None:
            s['label'], s['room'] = n.get('label') or n.get('name') or s['id'], n.get('room', s['region'])
        else:
            s.setdefault('label', near['label'] if near else s['region'].replace('_', ' ').capitalize())
            s.setdefault('room', near['room'] if near else s['region'])
        if s['origin'] == 'seed' and n is not None and 'yaw' in n:
            s['yaw'], s['pitch'] = math.degrees(n['yaw']), math.degrees(n.get('pitch', 0.0))
        elif s['origin'] in ('seed-moved', 'placed') and n is not None and n.get('look'):
            s['yaw'], s['pitch'] = yaw_to(x, z, n['look'][0], n['look'][2]), math.degrees(n.get('pitch', 0.0))
        elif s.get('aim'):
            s['yaw'], s['pitch'] = yaw_to(x, z, *s['aim']), s.get('pitch', 0.0)
        else:
            s['yaw'], s['pitch'] = open_yaw(w, x, z, extent), 0.0
        if 'floor' not in s:
            f = w.down(x, z, s['outdoor'])
            s['floor'] = f[0] if f else level(x, z)


# ----------------------------------------------------------------------------------------------- overlay
FONT = {
    'A': '0E11111F111111', 'B': '1E11111E11111E', 'C': '0E11101010110E', 'D': '1E11111111111E',
    'E': '1F10101E10101F', 'F': '1F10101E101010', 'G': '0E11101711110F', 'H': '1111111F111111',
    'I': '0E04040404040E', 'J': '0702020202120C', 'K': '11121418141211', 'L': '1010101010101F',
    'M': '111B1515111111', 'N': '11191513111111', 'O': '0E11111111110E', 'P': '1E11111E101010',
    'Q': '0E11111115120D', 'R': '1E11111E141211', 'S': '0F10100E01011E', 'T': '1F040404040404',
    'U': '1111111111110E', 'V': '11111111110A04', 'W': '11111115151B11',
    'X': '11110A040A1111', 'Y': '11110A04040404', 'Z': '1F01020408101F', '0': '0E11131519110E',
    '1': '040C040404040E', '2': '0E11010204081F', '3': '1F02040201110E', '4': '02060A121F0202',
    '5': '1F101E0101110E', '6': '0608101E11110E', '7': '1F010204080808', '8': '0E11110E11110E',
    '9': '0E11110F01020C', ' ': '00000000000000', '.': '00000000000C0C', '-': '0000001F000000',
    ':': '000C0C000C0C00', '=': '00001F001F0000', '/': '01010204081010', ',': '000000000C0408',
    '+': '0004041F040400', '(': '02040808080402', ')': '08040202020408', '>': '08040201020408',
    '?': '0E110102040004', '%': '18190204081303', "'": '04040800000000',
}


def _glyph(ch):
    rows = FONT.get(ch, FONT['?'])
    return np.array([[(int(rows[2 * r:2 * r + 2], 16) >> (4 - c)) & 1 for c in range(5)] for r in range(7)], bool)


class Canvas:
    def __init__(self, wpx, hpx, bg):
        self.img = np.empty((hpx, wpx, 3), np.uint8)
        self.img[:] = bg

    def rect(self, x0, y0, x1, y1, col):
        h, w = self.img.shape[:2]
        x0, x1, y0, y1 = max(0, int(x0)), min(w, int(x1)), max(0, int(y0)), min(h, int(y1))
        if x1 > x0 and y1 > y0:
            self.img[y0:y1, x0:x1] = col

    def disc(self, cx, cy, r, col):
        h, w = self.img.shape[:2]
        x0, x1 = max(0, int(cx - r - 1)), min(w, int(cx + r + 2))
        y0, y1 = max(0, int(cy - r - 1)), min(h, int(cy + r + 2))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.ogrid[y0:y1, x0:x1]
        self.img[y0:y1, x0:x1][(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = col

    def line(self, x0, y0, x1, y1, col, width=2):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        xs = np.linspace(x0, x1, n)
        ys = np.linspace(y0, y1, n)
        h, w = self.img.shape[:2]
        xi0 = np.floor(xs + 0.5).astype(int)
        yi0 = np.floor(ys + 0.5).astype(int)
        for ox in range(-(width // 2), width - width // 2):
            for oy in range(-(width // 2), width - width // 2):
                xi, yi = xi0 + ox, yi0 + oy
                ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
                self.img[yi[ok], xi[ok]] = col

    def text(self, x, y, s, col, scale=2, halo=None):
        x, y = int(x), int(y)
        if halo is not None:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if ox or oy:
                        self.text(x + ox, y + oy, s, halo, scale)
        h, w = self.img.shape[:2]
        for k, ch in enumerate(s.upper()):
            gl = np.kron(_glyph(ch), np.ones((scale, scale), bool))
            gx, gy = x + k * 6 * scale, y
            x0, y0 = max(0, gx), max(0, gy)
            x1, y1 = min(w, gx + gl.shape[1]), min(h, gy + gl.shape[0])
            if x1 > x0 and y1 > y0:
                self.img[y0:y1, x0:x1][gl[y0 - gy:y1 - gy, x0 - gx:x1 - gx]] = col

    def save(self, path):
        h, w = self.img.shape[:2]
        raw = b''.join(b'\x00' + self.img[y].tobytes() for y in range(h))

        def chunk(tag, data):
            return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                    + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


ORIGIN_COLOR = {'seed': (235, 130, 20), 'seed-moved': (200, 60, 30), 'approach': (150, 70, 190),
                'placed': (150, 70, 190),
                'laundry': (220, 40, 150), 'door': (20, 150, 90), 'bridge': (20, 150, 90),
                'fill': (30, 110, 230), 'region': (0, 160, 190), 'outdoor': (200, 30, 30)}


def draw_overlay(path, L, links, title, a, extent):
    w, g = L.w, L.g
    t = time.time()
    S = a.px_per_ft
    X0, X1, Z0, Z1 = -1.5, 41.0, -6.0, 59.0
    top = 44
    wpx, hpx = int((X1 - X0) * S), int((Z1 - Z0) * S) + top
    cv = Canvas(wpx, hpx, (226, 230, 236))
    fx = lambda x: (x - X0) * S                    # noqa: E731
    fz = lambda z: (z - Z0) * S + top              # noqa: E731
    # 1. floor / furniture footprint, one ray down per 0.1 ft
    fine = 0.1
    for x in np.arange(X0 + fine / 2, X1, fine):
        for z in np.arange(Z0 + fine / 2, Z1, fine):
            x, z = float(x), float(z)
            f = w.down(x, z, site=True)
            if f is None:
                continue
            indoor = (0 <= x <= extent[1] and 0 <= z <= extent[3] and w.ceiling(x, z)
                      and not g.is_outdoor(x, z))
            y = f[0]
            if not indoor:
                name = w.names[f[1]].lower()
                paved = any(k in name for k in ('deck', 'landing', 'step', 'porch', 'paving', 'walk', 'drive'))
                col = (176, 184, 192) if y > 0.5 else (198, 205, 214) if paved else (214, 220, 226)
            elif on_level(y, x, z):
                i, j = g.cell(x, z)
                col = (244, 244, 244)
                if g.inside(i, j) and g.reach[i, j]:
                    col = (214, 238, 202) if g.cl[i, j] >= a.min_clear else (246, 240, 200)
            else:
                col = (232, 212, 176) if y < 1.5 else (214, 184, 136) if y < 3.5 else (188, 152, 104)
            cv.rect(fx(x - fine / 2), fz(z - fine / 2), fx(x + fine / 2) + 1, fz(z + fine / 2) + 1, col)
    # 2. section cut at 4 ft: scan lines along x and along z, every hit is a surface crossing
    cut = 4.0
    colors = {ARCH: (20, 20, 24), FURN: (120, 88, 56), EXT: (120, 128, 136)}

    def scan(o, d, length):
        hits, tt = [], 0.0
        while tt < length and len(hits) < 4000:
            first = None
            for bvh, own in ((w.bvh_in, w.own_in), (w.bvh_ext, w.own_ext)):
                if bvh is None:
                    continue
                loc, nrm, idx, dist = bvh.ray_cast(o + d * (tt * FT), d, (length - tt) * FT)
                if loc is not None and (first is None or dist < first[0]):
                    first = (dist, int(own[idx]), nrm.dot(d))
            if first is None:
                break
            tt += first[0] / FT
            hits.append((tt, first[1], first[2]))
            tt += 0.002
        return hits

    step = 1.0 / S
    for horizontal in (True, False):
        rng = np.arange(Z0, Z1, step) if horizontal else np.arange(X0, X1, step)
        for v in rng:
            v = float(v) + step / 2
            if horizontal:
                hits = scan(ft2bl(X0, cut, v), Vector((1, 0, 0)), X1 - X0)
            else:
                hits = scan(ft2bl(v, cut, Z0), Vector((0, -1, 0)), Z1 - Z0)
            for k, (tt, own, nd) in enumerate(hits):
                cat = w.cats[own]
                col = (40, 140, 230) if w.glass[own] else colors[int(cat)]
                # a thin architectural solid (wall, jamb, door leaf): fill between entry and exit
                end = tt
                if cat == ARCH and not w.glass[own] and nd < 0 and k + 1 < len(hits):
                    nxt = hits[k + 1]
                    if nxt[2] > 0 and w.cats[nxt[1]] == ARCH and nxt[0] - tt < 1.3:
                        end = nxt[0]
                if horizontal:
                    cv.rect(fx(X0 + tt), fz(v) - 0.5, fx(X0 + end) + 1.5, fz(v) + 0.5, col)
                else:
                    cv.rect(fx(v) - 0.5, fz(Z0 + tt), fx(v) + 0.5, fz(Z0 + end) + 1.5, col)
    # 3. links, sweeps, ids
    for (i, j) in links:
        cv.line(fx(L.sw[i]['x']), fz(L.sw[i]['z']), fx(L.sw[j]['x']), fz(L.sw[j]['z']), (40, 70, 200), 2)
    for s in L.sw:
        cx, cy = fx(s['x']), fz(s['z'])
        dx, dz = math.sin(math.radians(s['yaw'])), -math.cos(math.radians(s['yaw']))
        cv.line(cx, cy, cx + dx * 20, cy + dz * 20, (255, 255, 255), 5)
        cv.line(cx, cy, cx + dx * 19, cy + dz * 19, (0, 0, 0), 3)       # where the sweep's yaw looks
        if s.get('fresh'):                        # --keep: not where the kept layout had it (moved or new)
            cv.disc(cx, cy, 13.5, (225, 20, 20))
            cv.disc(cx, cy, 10.5, (255, 255, 255))
        cv.disc(cx, cy, 8.5, (255, 255, 255))
        cv.disc(cx, cy, 6.5, ORIGIN_COLOR.get(s['origin'], (90, 90, 90)))
    for s in L.sw:
        dx, dz = math.sin(math.radians(s['yaw'])), -math.cos(math.radians(s['yaw']))
        ox = -33 if dx > 0 else 10                # the label goes to the side the yaw tick does not use
        oy = 4 if dz < 0 else -18
        cv.text(fx(s['x']) + ox, fz(s['z']) + oy, s['id'], (0, 0, 0), 2, halo=(255, 255, 255))
    # 4. header: title, legend, scale bar
    cv.rect(0, 0, wpx, top, (255, 255, 255))
    cv.text(8, 5, title, (0, 0, 0), 2)
    x = 8
    for name in ('seed', 'seed-moved', 'approach/placed', 'door/bridge', 'fill', 'region', 'laundry', 'outdoor'):
        cv.disc(x + 6, 31, 6, ORIGIN_COLOR[name.split('/')[0]])
        cv.text(x + 16, 25, name, (0, 0, 0), 2)
        x += 16 + 12 * len(name) + 14
    if any(s.get('fresh') for s in L.sw):
        cv.disc(x + 6, 31, 8, (225, 20, 20))
        cv.disc(x + 6, 31, 5.5, (255, 255, 255))
        cv.text(x + 18, 25, 'moved/new', (0, 0, 0), 2)
    cv.rect(wpx - 12 - 5 * S, 19, wpx - 12, 22, (0, 0, 0))
    cv.text(wpx - 12 - 5 * S, 3, '5 FT  N UP', (0, 0, 0), 2)
    cv.save(path)
    P('overlay %s (%dx%d) in %.1f s' % (path, wpx, hpx, time.time() - t))


# ----------------------------------------------------------------------------------------------- main
def main():
    a = parse()
    t0 = time.time()
    scene = json.load(open(a.scene))
    old = {n['id']: n for n in scene['tour']['nodes']}
    rooms = {k: tuple(v['bounds_ft_x0x1z0z1'])
             for k, v in json.load(open(a.classification))['meta']['rooms'].items()
             if len(v.get('bounds_ft_x0x1z0z1') or []) == 4}
    meas = json.load(open(a.measurements)) if os.path.exists(a.measurements) else None
    doors = {d[0]: d for d in door_frames(meas)}
    want_ext = []
    for o in OUTDOOR:
        cx, cz = (doors[o['door']][2], doors[o['door']][3]) if o['door'] in doors else o['centre']
        tx, tz = cx + o['out'][0] * o['dist'], cz + o['out'][1] * o['dist']
        want_ext.append([round(tx - 9, 2), round(tx + 9, 2), round(tz - 7, 2), round(tz + 7, 2)])
    kept, kept_from = load_keep(a.keep) if a.keep else (None, None)
    mesh, blend = load_mesh(a, want_ext)
    w = World(mesh)
    g = Grid(w, rooms)
    g.flood([(n['p'][0], n['p'][2]) for n in old.values()]
            + [(k['x'], k['z']) for k in kept or () if not k['outdoor']])
    P('reachable floor (clearance >= 0.9 ft): %.0f sq ft; with clearance >= %.1f ft: %.0f sq ft' % (
        g.reach.sum() * STEP * STEP, a.min_clear, (g.reach & (g.cl >= a.min_clear)).sum() * STEP * STEP))

    L = Layout(w, g, a)
    hand = place_hand(L, kept)
    if kept is not None:
        place_kept(L, kept, old, hand)
    place_seeds(L, old, kept, hand)
    place_laundry(L)
    if kept is None:                   # a kept layout has made its choice among the old approach stops
        place_approach(L, old)
    place_doors(L, meas)
    bridge(L, a.min_clear, 'bridge')
    fill(L)
    cover_regions(L)
    bridge(L, a.min_clear, 'bridge')
    bridge(L, a.relaxed_clear, 'bridge')
    place_outdoor(L, meas, kept)
    assign_ids(L, kept)
    L.notes = [re.sub(r'\{ids:([0-9,]*)\}', lambda m: ' '.join(L.sw[int(k)]['id'] for k in m.group(1).split(',') if k),
                      line) for line in L.notes]
    extent = (0.0, float(scene.get('extent', [39.42, 55.9])[0]), 0.0, float(scene.get('extent', [39.42, 55.9])[1]))
    describe(L, old, extent, kept)

    # order: old stops in their old order, then the new ones by id
    order = {k: i for i, k in enumerate(old)}
    idx = sorted(range(len(L.sw)), key=lambda i: (order.get(L.sw[i]['id'], 10 ** 6) if L.sw[i]['id'] in OLD_IDS
                                                  else 10 ** 6, L.sw[i]['outdoor'], L.sw[i]['id']))
    links, vis, keep, npairs = build_graph(L)
    n = len(L.sw)
    at = {s['id']: i for i, s in enumerate(L.sw)}
    keep_block = None
    if kept is None:
        gone = sorted('%s-%s' % (e[0], e[1]) for e in scene['tour'].get('edges', [])
                      if e[0] in at and e[1] in at and at[e[1]] not in L.adj[at[e[0]]])
        if gone:
            L.notes.append('old edges between kept sweeps that are not walkable straight lines: ' + ' '.join(gone))
    else:
        # what became of the kept layout: the sweeps that are not where it had them need a new panorama
        was = {k['id']: k for k in kept}
        keep_block = {'from': kept_from, 'unchanged': [], 'moved': {}, 'reaimed': [], 'new': [],
                      'removed': [k['id'] for k in kept if k['id'] not in at],
                      'renamed': {L.sw[i]['id']: L.sw[i]['label'] for i in idx if L.sw[i].get('renamed')}}
        for i in idx:
            if L.sw[i].get('renamed'):
                L.notes.append('keep %s: named "%s" as %s has it now (was "%s")'
                               % (L.sw[i]['id'], L.sw[i]['label'],
                                  'OUTDOOR' if L.sw[i]['outdoor'] else 'the scene file', L.sw[i]['renamed']))
        for i in idx:
            s = L.sw[i]
            k = was.get(s['id'])
            d = None if k is None else math.hypot(s['x'] - k['x'], s['z'] - k['z'])
            if k is None:
                keep_block['new'].append(s['id'])
            elif d > 1e-4:
                keep_block['moved'][s['id']] = round(d, 2)
            elif abs(s['yaw'] - k['yaw']) > 1e-6 or abs(s['pitch'] - k['pitch']) > 1e-6:
                keep_block['reaimed'].append(s['id'])      # same panorama, another opening view
            else:
                keep_block['unchanged'].append(s['id'])
            s['fresh'] = k is None or d > 1e-4
        gone = sorted({'%s-%s' % tuple(sorted((k['id'], o), key=lambda v: at[v])) for k in kept for o in k['links']
                       if k['id'] in at and o in at and not (L.sw[at[k['id']]]['fresh'] or L.sw[at[o]]['fresh'])
                       and at[o] not in L.adj[at[k['id']]]})
        if gone:
            L.notes.append('links of the kept layout between sweeps that did not move which are no longer '
                           'walkable straight lines: ' + ' '.join(gone))
        L.notes.append('kept layout %s: %d sweeps unchanged; moved %s; new %s; removed %s%s' % (
            kept_from, len(keep_block['unchanged']),
            ', '.join('%s %.2f ft' % kv for kv in keep_block['moved'].items()) or '-',
            ' '.join(keep_block['new']) or '-', ' '.join(keep_block['removed']) or '-',
            '; view changed in place: ' + ' '.join(keep_block['reaimed']) if keep_block['reaimed'] else ''))
    comps = len({min(bfs(links, i)) for i in range(n)})
    ecc = [max(bfs(links, i).values()) for i in range(n)] if comps == 1 else []
    pts = [(s['x'], s['z']) for s in L.sw]
    nn = sorted(min(math.dist(pts[i], pts[j]) for j in range(n) if j != i) for i in range(n))
    nnv = sorted(min([math.dist(pts[i], pts[j]) for j in vis[i]] or [float('nan')]) for i in range(n))
    el = sorted(keep.values())
    deg = sorted(len(links[i]) for i in range(n))
    per_room = collections.Counter(s['room'] for s in L.sw)
    per_region = collections.Counter(s['region'] for s in L.sw)
    per_origin = collections.Counter(s['origin'] for s in L.sw)
    med = lambda v: round(v[len(v) // 2], 2)       # noqa: E731
    stats = {
        'sweeps': n, 'indoor': sum(1 for s in L.sw if not s['outdoor']),
        'outdoor': sum(1 for s in L.sw if s['outdoor']),
        'per_room': dict(sorted(per_room.items())), 'per_region': dict(sorted(per_region.items())),
        'per_origin': dict(sorted(per_origin.items())),
        'links': len(keep), 'walkable_pairs': npairs, 'components': comps,
        'diameter_hops': max(ecc) if ecc else None,
        'degree_min_median_max': [deg[0], deg[len(deg) // 2], deg[-1]],
        'link_ft_min_median_max': [round(el[0], 2), med(el), round(el[-1], 2)] if el else None,
        'nearest_sweep_ft_min_median_max': [round(nn[0], 2), med(nn), round(nn[-1], 2)],
        'nearest_visible_sweep_ft_min_median_max': [round(nnv[0], 2), med(nnv), round(nnv[-1], 2)],
        'visible_per_sweep_min_median_max': [min(len(v) for v in vis), sorted(len(v) for v in vis)[n // 2],
                                             max(len(v) for v in vis)],
        'clearance_ft_min_median': [round(min(s['clearance'] for s in L.sw), 2),
                                    med(sorted(s['clearance'] for s in L.sw))],
        'reachable_sqft': round(float(g.reach.sum()) * STEP * STEP, 1),
    }
    out = {
        'eye': EYE, 'generated_from': blend,
        'units': {'length': 'ft', 'angle': 'deg',
                  'yaw': '0 = toward -z (north), positive clockwise seen from above'},
        'params': {'min_clear': a.min_clear, 'relaxed_clear': a.relaxed_clear, 'min_sep': a.min_sep,
                   'nudge': a.nudge, 'garage_max': a.garage_max, 'max_sweeps': a.max_sweeps,
                   'link_max': a.link_max, 'visible_max': a.visible_max, 'door_radius': a.door_radius,
                   'door_sep': a.door_sep, 'tight_clear': a.tight_clear, 'tight_sep': a.tight_sep,
                   'far_cap': a.far_cap, 'clear_weight': a.clear_weight,
                   'laundry': a.laundry, 'outdoor': a.outdoor, 'grid_step': STEP,
                   'keep': os.path.basename(a.keep) if a.keep else None, 'keep_clear': a.keep_clear,
                   'seeds': SEEDS, 'approach_candidates': sorted(APPROACH),
                   'placed': {k: [round(v[0], 4), round(v[1], 4)] for k, v in PLACED.items()},
                   'id_letters': {k: v[1] for k, v in REGIONS.items()}},
        'stats': stats, 'notes': L.notes,
        **({'keep': keep_block} if keep_block else {}),
        'sweeps': [{
            'id': s['id'], 'label': s['label'], 'room': s['room'],
            'p': [round(s['x'], 4), round(level(s['x'], s['z']) + EYE, 4), round(s['z'], 4)],
            'level': round(level(s['x'], s['z']), 4) + 0.0, 'floor': round(s['floor'], 3) + 0.0,
            'yaw': round(s['yaw'], 6) + 0.0, 'pitch': round(s['pitch'], 6) + 0.0,
            'links': [L.sw[j]['id'] for j in idx if j in links[i]],
            'visible': [L.sw[j]['id'] for j in idx if j in vis[i]],
            'outdoor': bool(s['outdoor']), 'origin': s['origin'], 'clearance': round(s['clearance'], 2),
        } for i in idx for s in [L.sw[i]]],
    }
    for line in L.notes:
        P('note:', line)
    P('sweeps %d (indoor %d, outdoor %d); by origin %s' % (n, stats['indoor'], stats['outdoor'], dict(per_origin)))
    P('per room:', stats['per_room'])
    P('per region:', stats['per_region'])
    P('links %d of %d walkable pairs <= %g ft; components %d; diameter %s hops; degree min/median/max %s' % (
        len(keep), npairs, a.link_max, comps, stats['diameter_hops'], stats['degree_min_median_max']))
    P('link length min/median/max %s ft; nearest sweep %s ft; nearest visible sweep %s ft; visible per sweep %s' % (
        stats['link_ft_min_median_max'], stats['nearest_sweep_ft_min_median_max'],
        stats['nearest_visible_sweep_ft_min_median_max'], stats['visible_per_sweep_min_median_max']))
    ids = [s['id'] for s in L.sw]
    problems = []
    if len(set(ids)) != len(ids):
        problems.append('duplicate ids')
    if any(len(i) != 2 for i in ids):
        problems.append('ids must have 2 characters')
    if comps != 1:
        parts = collections.defaultdict(list)
        for i in range(n):
            parts[min(bfs(links, i))].append(L.sw[i]['id'])
        problems.append('the link graph has %d parts: %s' % (comps, ' | '.join(' '.join(p) for p in parts.values())))
    if a.overlay:
        title = '%s: %d sweeps, %d links, diameter %s hops%s' % (
            blend, n, len(keep), stats['diameter_hops'], '   NOT CONNECTED' if comps != 1 else '')
        draw_overlay(a.overlay, L, keep, title, a, extent)
    if problems:
        P('ERROR: ' + '; '.join(problems) + '. Nothing written to ' + a.out)
        sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    P('wrote %s; %d rays, %.1f s' % (a.out, w.rays, time.time() - t0))


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except BaseException:            # Blender exits with status 0 after a Python error: make it a failure
        import traceback
        traceback.print_exc()
        sys.exit(1)
