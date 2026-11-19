"""Site plan of the exterior zone (SCENE feet: x west->east, z garden(north, -) -> street(south, +)).

Built directly on the architect's plan (sizes/sizes.pdf): the house's outer faces come from the converted
SCENE (tools/render/relayout.py OUTER), the lot from sheet SKA001 "(N) SITE PLAN" (52'-0" x 100'-0" lot,
5'-7" / 6'-6" side yards, 23'-0" rear yard, 22'-8" front setback to the bedroom-3 face), the covered
porch and the two rear landings from SKA002 "(N) FLOOR PLAN". The exterior is not warped (bl/warp.py
skips it). Rectangles are (x0, x1, z0, z1).
"""
from .exterior_util import GRADE

# ---- property lines / fences ------------------------------------------------------------
FW, FE, FN = -5.808, 46.192, -23.225    # west / east side lot lines (fences), rear lot line (fence)
GATE_WZ = 50.5                           # west side-yard return fence + gate (south of bedroom-3 window)
GATE_EZ = 48.0                           # east side-yard return fence + gate (~4'-10" behind the garage face)
FENCE_TOP = 5.6                          # top of the 6'-2" slat fence (grade is -0.6)

# ---- house outer faces ------------------------------------------------------------------
HX0, HX1, HZ0 = -0.225, 39.645, -0.225  # west, east, rear wall outer faces
GARAGE_FRONT = 52.85                     # garage stucco face (wall 52.335..52.785 + skin)
BED3_FRONT = 53.96                       # bedroom 3 stucco face (wall 53.442..53.892 + skin); bay to ~56.0
PORCH = (14.218, 21.218, 47.47, 54.80)   # covered porch, 7'-0" x 7'-4" (foyer wall face .. porch front)
PORCH_POST = 1.417                       # 1'-5" square stucco piers at the porch's front corners
# flat porch canopy: under the high entry window (sill 7.5 ft), over the front door (head 6.67 ft)
PORCH_ROOF = (PORCH[0] - 1.62, PORCH[1] + 1.62, PORCH[2], PORCH[3] + 0.35)   # x0, x1, z0, z1 (outer edges)
PORCH_SOFFIT, PORCH_ROOF_TOP = 6.95, 7.45
PORCH_POSTS = [(PORCH[0] - PORCH_POST, PORCH[0], 53.5, PORCH[3]),           # against the bedroom-3 face
               (PORCH[1], PORCH[1] + PORCH_POST, GARAGE_FRONT - 0.2, PORCH[3])]  # against the garage face
GARAGE_DOOR = (22.957, 37.816)           # 14'-10" vehicle door opening, 7 ft high

# ---- shifts against the original (concept) site, for the context / far-neighbourhood modules -----
FRONT_DZ = 76.559 - 66.5                 # street side moved south: old sidewalk z 66.5 -> new property line
REAR_DZ = FN - (-12.4)                   # rear lot line moved north: old rear fence z -12.4

# ---- back garden ------------------------------------------------------------------------
DECK = (21.85, HX1, -6.5, HZ0)           # ipe platform outside the living room = its (N) LANDING
DECK_TOP = -0.05                         # just below the oak floor / door threshold
STEP_W = 1.0                             # wrap-around step tread width
STEP_TOP = -0.33
PEB_W = 0.75                             # river-pebble border around the step
LANDING = (2.1, 9.45, -3.225, HZ0)       # (N) LANDING outside the primary bedroom's sliding door (x 2.45..9.10)
REAR_BED = (FW + 0.12, FE - 0.12, FN + 0.12, FN + 2.4)
_B = STEP_W + PEB_W
DECK_BORDER = (DECK[0] - _B, DECK[1] + _B, DECK[2] - _B, HZ0)
LANDING_BORDER = (LANDING[0] - _B, LANDING[1] + _B, LANDING[2] - _B, HZ0)
DRIPS = [(-1.225, LANDING_BORDER[0], -1.23, HZ0),                     # pebble drip strips along the rear wall
         (LANDING_BORDER[1], DECK_BORDER[0], -1.23, HZ0)]

LAWNS_REAR = [
    (FW + 0.12, LANDING_BORDER[0], REAR_BED[3], DRIPS[0][2]),                     # west lawn (L-shaped with next)
    (FW + 0.12, DRIPS[0][0], DRIPS[0][2], HZ0),
    (LANDING_BORDER[0], LANDING_BORDER[1], REAR_BED[3], LANDING_BORDER[2]),        # north of the landing
    (LANDING_BORDER[1], DECK_BORDER[0], REAR_BED[3], DRIPS[1][2]),               # between landing and deck
    (DECK_BORDER[0], DECK_BORDER[1], REAR_BED[3], DECK_BORDER[2]),               # north of the deck
    (DECK_BORDER[1], FE - 0.12, REAR_BED[3], HZ0),                               # east lawn
]

# ---- side yards (fence bed | pebble zone with pavers | house) ------------------------------
W_BED = (FW + 0.12, -4.05, HZ0, GATE_WZ - 0.12)
W_PEB = (-4.05, HX0, HZ0, GATE_WZ - 0.12)
W_PAVERS_X = (-3.75, -1.15)
E_PEB = (HX1, 43.45, HZ0, GATE_EZ - 0.12)
E_BED = (43.45, FE - 0.12, HZ0, GATE_EZ - 0.12)
E_PAVERS_X = (40.24, 42.59)

# ---- front ------------------------------------------------------------------------------
SIDEWALK = (76.559, 81.059)              # z band from the front property line, top -0.55
PARK = (SIDEWALK[1], SIDEWALK[1] + 4.5)  # planting strip between sidewalk and curb
CURB = (PARK[1], PARK[1] + 0.5)
GUTTER = (CURB[1], CURB[1] + 1.5)
STREET = (GUTTER[1], GUTTER[1] + 34.0)
FAR_GUTTER = (STREET[1], STREET[1] + 1.5)
FAR_CURB = (FAR_GUTTER[1], FAR_GUTTER[1] + 0.5)
FAR_PARK = (FAR_CURB[1], FAR_CURB[1] + 4.5)
FAR_WALK = (FAR_PARK[1], FAR_PARK[1] + 4.5)
WALK_TOP = -0.55
STREET_TOP = -1.0
FRONT_FENCE_Z = SIDEWALK[0] - 0.45       # low front fence line (west front lawn only)

DRIVE = (PORCH_POSTS[1][1] + 0.12, GARAGE_DOOR[1] + 1.64, 52.56, SIDEWALK[0])   # garage slab edge .. sidewalk
DRIVE_TOP0, DRIVE_TOP1 = 0.0, WALK_TOP    # at the garage / at the sidewalk
WALKWAY = (15.47, 19.97)                 # paver x extents, centred on the porch
CORRIDOR = (PORCH[0], DRIVE[0], PORCH[3], SIDEWALK[0])     # dark pebble field around the walk
W_FRONT_BED = (FW + 0.12, -0.26, GATE_WZ + 0.12, BED3_FRONT)
FRONT_BED = (FW + 0.12, PORCH[0], BED3_FRONT, 59.0)        # (runs under the west pier)
FRONT_LAWN = (FW + 0.12, PORCH[0], 59.0, FRONT_FENCE_Z - 0.2)
FRONT_STRIP = (FW + 0.12, PORCH[0], FRONT_FENCE_Z + 0.12, SIDEWALK[0])
E_FRONT_BED1 = (HX1 + 0.04, FE - 0.12, GATE_EZ + 0.12, GARAGE_FRONT)
E_FRONT_BED2 = (DRIVE[1], FE - 0.12, GARAGE_FRONT, SIDEWALK[0])
E_BANK_X = DRIVE[1] + 2.7                # east bank: grade at this x, rising to the driveway edge


def drive_top(z):
    t = (z - DRIVE[2]) / (DRIVE[3] - DRIVE[2])
    t = min(max(t, 0.0), 1.0)
    return DRIVE_TOP0 + (DRIVE_TOP1 - DRIVE_TOP0) * t


STRIP = (WALKWAY[1] + 0.4, DRIVE[0], PORCH[3], SIDEWALK[0])     # planted bank between walk and driveway


def bank_top(x, z, x_low, x_high):
    """Soil bank that rises from grade (at x_low) to just under the sloped driveway edge (x_high)."""
    lo = GRADE + 0.04
    hi = max(lo, drive_top(z) - 0.05)
    t = (x - x_low) / (x_high - x_low)
    t = min(max(t, 0.0), 1.0)
    t = t * t * (3 - 2 * t)
    return lo + (hi - lo) * t
