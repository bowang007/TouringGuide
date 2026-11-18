"""Site plan of the exterior zone (SCENE feet: x west->east, z garden(north, -) -> street(south, +)).

Anchors come from the original landscape objects (rear lawn z -12.4..0, side yards x -6.75..-0.25 and
41.05..47.55 with side fences at x -6.1 / 47.0, front garden z 52.5..71.5, front walk x 15.35..19.35,
driveway x 21.9..39.9 z 51.3..66.3). Rectangles are (x0, x1, z0, z1).
"""
from .exterior_util import GRADE

# ---- property lines / fences ------------------------------------------------------------
FW, FE, FN = -6.1, 47.0, -12.4          # west / east side fences, rear fence
GATE_WZ = 50.5                           # west side-yard return fence + gate (south of B3 window W10)
GATE_EZ = 46.5                           # east side-yard return fence + gate
FENCE_TOP = 5.6                          # top of the 6'-2" slat fence (grade is -0.6)
FRONT_FENCE_Z = 66.05                    # low front fence line (west front lawn only)

# ---- house outer faces ------------------------------------------------------------------
HX0, HX1, HZ0 = -0.225, 41.06, -0.23     # west, east, rear wall outer faces
GARAGE_FRONT = 51.35                     # garage stucco face
BED3_FRONT = 54.35                       # bedroom 3 stucco face
PORCH = (14.34, 20.46, 47.15, 51.36)     # recessed porch clear area

# ---- back garden ------------------------------------------------------------------------
DECK = (22.6, 41.06, -6.5, HZ0)          # ipe platform
DECK_TOP = -0.05                         # just below the oak floor / door threshold
STEP_W = 1.0                             # wrap-around step tread width
STEP_TOP = -0.33
PEB_W = 0.75                             # river-pebble border around the step
REAR_BED = (FW + 0.12, FE - 0.12, FN + 0.12, -10.0)
DRIP = (-1.225, DECK[0] - STEP_W - PEB_W, -1.23, HZ0)       # pebble drip strip along the rear wall
DECK_BORDER = (DECK[0] - STEP_W - PEB_W, DECK[1] + STEP_W + PEB_W, DECK[2] - STEP_W - PEB_W, HZ0)

LAWNS_REAR = [
    (FW + 0.12, DRIP[1], REAR_BED[3], DRIP[2]),              # west lawn (L-shaped with next)
    (FW + 0.12, DRIP[0], DRIP[2], HZ0),
    (DRIP[1], DECK_BORDER[1], REAR_BED[3], DECK_BORDER[2]),  # strip north of the deck
    (DECK_BORDER[1], FE - 0.12, REAR_BED[3], HZ0),           # east lawn
]

# ---- side yards (fence bed | pebble zone with pavers | house) ------------------------------
W_BED = (FW + 0.12, -4.3, HZ0, GATE_WZ - 0.12)
W_PEB = (-4.3, HX0, HZ0, GATE_WZ - 0.12)
W_PAVERS_X = (-3.95, -1.25)
E_PEB = (HX1, 44.3, HZ0, GATE_EZ - 0.12)
E_BED = (44.3, FE - 0.12, HZ0, GATE_EZ - 0.12)
E_PAVERS_X = (41.65, 44.0)

# ---- front ------------------------------------------------------------------------------
SIDEWALK = (66.5, 71.0)                  # z band, top -0.55
PARK = (71.0, 75.5)                      # planting strip between sidewalk and curb
CURB = (75.5, 76.0)
GUTTER = (76.0, 77.5)
STREET = (77.5, 111.5)
FAR_GUTTER = (111.5, 113.0)
FAR_CURB = (113.0, 113.5)
FAR_PARK = (113.5, 118.0)
FAR_WALK = (118.0, 122.5)
WALK_TOP = -0.55
STREET_TOP = -1.0

DRIVE = (21.9, 39.9, 51.06, SIDEWALK[0])
DRIVE_TOP0, DRIVE_TOP1 = 0.0, WALK_TOP    # at the garage / at the sidewalk
WALKWAY = (15.1, 19.6)                   # paver x extents
CORRIDOR = (PORCH[0], DRIVE[0], PORCH[3], SIDEWALK[0])     # dark pebble field around the walk
W_FRONT_BED = (FW + 0.12, -0.26, GATE_WZ + 0.12, BED3_FRONT)
FRONT_BED = (FW + 0.12, PORCH[0], BED3_FRONT, 59.0)
FRONT_LAWN = (FW + 0.12, PORCH[0], 59.0, FRONT_FENCE_Z - 0.2)
FRONT_STRIP = (FW + 0.12, PORCH[0], FRONT_FENCE_Z + 0.12, SIDEWALK[0])
E_FRONT_BED1 = (41.10, FE - 0.12, GATE_EZ + 0.12, GARAGE_FRONT)
E_FRONT_BED2 = (DRIVE[1], FE - 0.12, GARAGE_FRONT, SIDEWALK[0])


def drive_top(z):
    t = (z - DRIVE[2]) / (DRIVE[3] - DRIVE[2])
    t = min(max(t, 0.0), 1.0)
    return DRIVE_TOP0 + (DRIVE_TOP1 - DRIVE_TOP0) * t


STRIP = (20.0, DRIVE[0], PORCH[3], SIDEWALK[0])     # planted bank between walk and driveway


def bank_top(x, z, x_low, x_high):
    """Soil bank that rises from grade (at x_low) to just under the sloped driveway edge (x_high)."""
    lo = GRADE + 0.04
    hi = max(lo, drive_top(z) - 0.05)
    t = (x - x_low) / (x_high - x_low)
    t = min(max(t, 0.0), 1.0)
    t = t * t * (3 - 2 * t)
    return lo + (hi - lo) * t
