"""Site plan of the exterior zone (SCENE feet: x west->east, z garden(north, -) -> street(south, +)).

Built directly on the architect's plan (sizes/sizes.pdf): the house's outer faces are the sheet's
(tools/render/relayout.py: the model's frame is sheet SKA002's and every wall is 5 in, so the house is
39'-11" x 54'-4" outside), the lot is sheet SKA001's "(N) SITE PLAN" laid round them (52'-0" x 100'-0" lot,
5'-7" / 6'-6" side yards, 23'-0" rear yard, 22'-8" front setback to the bedroom-3 face), the covered
porch and the two rear landings are SKA002's. The exterior is not warped (bl/warp.py skips it).
Rectangles are (x0, x1, z0, z1). Nothing here is an absolute number: every line is written from the
house's faces, so the site follows the house.
"""
import os
import sys

from .exterior_util import GRADE

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import relayout as R  # noqa: E402  (the sheet's wall faces)

# ---- house outer faces ------------------------------------------------------------------
HX0, HX1, HZ0 = R.XW_OUT, R.XE_OUT, R.ZN_OUT   # west, east, rear wall outer faces (-0.192, 39.725, -0.192)
GARAGE_FRONT = R.Z_GAR_OUT               # garage stucco face, 52.808 (the 5 in wall with its skin: 52.392..52.808)
BED3_FRONT = R.Z_B3_OUT                  # bedroom 3 stucco face, 54.142 (wall 53.725..54.142); bay to ~56.2

# ---- v7 site: levels (sheet A1.3; the house floor is y 0) -----------------------------------------
GRADE_FRONT = -11.0 / 12.0               # natural grade and the garage floor at the front: 11 in below the floor
GRADE_REAR = -14.0 / 12.0                # natural grade at the rear: 1'-2" below the floor
# v7 repair: the porch slab stands half way between the front walk and the house floor: two equal risers of 5 1/2 in
# (walk -> slab, slab -> floor), as DESIGN_V7 H asks for the front entry ("proper equal risers") and as the garage's
# step at the house door is. It stood at A1.3's -0.336, the level of the EXISTING porch, which gave 6.97 in + 4.03 in;
# the set gives no level for the new covered porch.
PORCH_TOP = GRADE_FRONT / 2.0            # -0.4583: porch slab, 5 1/2 in above the front walk, 5 1/2 in below the floor
FLAT = GRADE                             # -0.60: the level site the fences, plants, street and the neighbourhood
#                                          are modelled on; exterior_site.settle() sets them down on the ground


def grade(z):
    """The ground line (y) at plan z: level behind the rear wall, rising 3 in along both sides of the house
    to the garage front (A1.3's side elevations, 53'-0"), level from there to the street."""
    t = (z - HZ0) / (GARAGE_FRONT - HZ0)
    return GRADE_REAR + (GRADE_FRONT - GRADE_REAR) * min(max(t, 0.0), 1.0)


# ---- property lines / fences (SKA001) ----------------------------------------------------
FW = HX0 - (5.0 + 7.0 / 12.0)            # west side lot line (fence): 5'-7" side yard
FE = FW + 52.0                           # east side lot line (fence): 52'-0" lot, which leaves the 6'-6" side yard
FN = HZ0 - 23.0                          # rear lot line (fence): 23'-0" rear yard
FRONT_LINE = BED3_FRONT + (22.0 + 8.0 / 12.0)   # front property line: 22'-8" setback; FN + 100'-0"
GATE_WZ = BED3_FRONT - 3.46              # west side-yard return fence + gate (south of bedroom-3 window)
GATE_EZ = GARAGE_FRONT - 4.85            # east side-yard return fence + gate (~4'-10" behind the garage face)
FENCE_TOP = 5.6                          # top of the 6'-2" slat fence on the level site (FLAT -0.6); settle()
#                                          rakes it with the ground: 6'-2" above it everywhere

# covered porch (foyer-side wall face .. garage wall face, front door wall's stucco face .. slab front): the
# plan's 7'-4" deep (5'-0" beside the garage + 2'-4" beyond it); 5'-9" wide since the office / bedroom-3 wall
# lines up with the shared bath's east wall (owner's change, relayout.FOYER_WALL). The wall beside the porch is
# the same 5 in wall as beside the foyer, so the porch's west face is the foyer's.
PORCH = R.ROOMS['porch']
PORCH_POST = 1.0 + 5.0 / 12.0            # 1'-5" square stucco piers at the porch's front corners
# v7 integrate: the flat porch canopy is gone (v7 roof: the entry gable runs on over the porch), and with it the
# constants PORCH_ROOF / PORCH_ROOF_TOP. PORCH_SOFFIT is only the height exterior_site first builds the two piers
# to; bl/roof.porch() then raises them to the entry roof's underside.
PORCH_SOFFIT = 6.95
# v7 integrate: both piers start 0.2 ft inside the front wall they stand against. The west one started on the line
# of bedroom 3's front wall's ROOM face (z 53.725, the sheet's pier outline): its stucco lay in the plane of the
# room's painted wall for 1 ft at the south-east corner, and in the plane of the porch wall's wood cladding.
PORCH_POSTS = [(PORCH[0] - PORCH_POST, PORCH[0], BED3_FRONT - 0.2, PORCH[3]),        # against the bedroom-3 face
               (PORCH[1], PORCH[1] + PORCH_POST, GARAGE_FRONT - 0.2, PORCH[3])]      # against the garage face
GARAGE_DOOR = (R.X_GARAGE(23.40155), R.X_GARAGE(38.25925))    # the vehicle door's WALL opening as the shell builds it
#                                                               since v7 garage: the sheet's 15'-0", x 22.975..37.975
#                                                               (relayout.GARAGE_DOOR_RO); the 14'-10" door between
#                                                               its jamb boards is bl/garage_spec.VEHICLE_DOOR_X
GARAGE_WALL_IN = R.Z_GAR_S               # interior face of the garage front wall

# ---- shifts against the original (concept) site, for the context / far-neighbourhood modules -----
FRONT_DZ = FRONT_LINE - 66.5             # street side moved south: old sidewalk z 66.5 -> new property line
REAR_DZ = FN - (-12.4)                   # rear lot line moved north: old rear fence z -12.4

# ---- back garden ------------------------------------------------------------------------
# v7 site: the two ipe landings are SKA002's "(N) LANDING"s, 3'-0" deep and 4 in wider than their sliding door
# on each side: 13'-0" outside the living room's 12'-4" four-panel door (x 25.195..38.195; the owner's wish of
# the second round, that the landing reaches the door, holds by itself now) and 7'-0" outside the primary
# bedroom's 6'-4" door (x 2.106..9.106). Top 1 in below the floor; one step, two equal risers of 6 1/2 in.
DECK = (R.X_LIV_E - 14.113, R.X_LIV_E - 1.113, HZ0 - 3.0, HZ0)      # LD2, living room
LIVING_SLIDER = (DECK[0] + 1.0 / 3.0, DECK[1] - 1.0 / 3.0)          # the door's wall opening, x 25.528..37.861
GARDEN_DOOR = LIVING_SLIDER              # (the two rear sconces of exterior_garage flank this opening)
DECK_TOP = -1.0 / 12.0                   # landing top: 1 in below the oak floor / door threshold
STEP_W = 1.0                             # wrap-around step tread width (12 in; at least 11 in)
STEP_RISERS = 2                          # equal risers from the landing down to the rear ground (at most 7 3/4 in)
STEP_RISE = (DECK_TOP - GRADE_REAR) / STEP_RISERS                   # 0.5417 ft = 6 1/2 in
STEP_TOP = DECK_TOP - STEP_RISE          # -0.625
PEB_W = 0.75                             # river-pebble border around the step
LANDING = (R.XW + 1.881, R.XW + 8.881, HZ0 - 3.0, HZ0)             # LD1, primary bedroom
REAR_BED = (FW + 0.12, FE - 0.12, FN + 0.12, FN + 2.4)
_B = STEP_W + PEB_W
DECK_BORDER = (DECK[0] - _B, DECK[1] + _B, DECK[2] - _B, HZ0)
LANDING_BORDER = (LANDING[0] - _B, LANDING[1] + _B, LANDING[2] - _B, HZ0)
DRIPS = [(HX0 - 1.0, LANDING_BORDER[0], HZ0 - 1.005, HZ0),             # pebble drip strips along the rear wall
         (LANDING_BORDER[1], DECK_BORDER[0], HZ0 - 1.005, HZ0)]

LAWNS_REAR = [
    (FW + 0.12, LANDING_BORDER[0], REAR_BED[3], DRIPS[0][2]),                     # west lawn (L-shaped with next)
    (FW + 0.12, DRIPS[0][0], DRIPS[0][2], HZ0),
    (LANDING_BORDER[0], LANDING_BORDER[1], REAR_BED[3], LANDING_BORDER[2]),        # north of the landing
    (LANDING_BORDER[1], DECK_BORDER[0], REAR_BED[3], DRIPS[1][2]),               # between landing and deck
    (DECK_BORDER[0], DECK_BORDER[1], REAR_BED[3], DECK_BORDER[2]),               # north of the deck
    (DECK_BORDER[1], FE - 0.12, REAR_BED[3], HZ0),                               # east lawn
]

# ---- side yards (fence bed | pebble zone with pavers | house) ------------------------------
W_BED = (FW + 0.12, HX0 - 3.825, HZ0, GATE_WZ - 0.12)
W_PEB = (HX0 - 3.825, HX0, HZ0, GATE_WZ - 0.12)
W_PAVERS_X = (HX0 - 3.525, HX0 - 0.925)
E_PEB = (HX1, HX1 + 3.805, HZ0, GATE_EZ - 0.12)
E_BED = (HX1 + 3.805, FE - 0.12, HZ0, GATE_EZ - 0.12)
E_PAVERS_X = (HX1 + 0.595, HX1 + 2.945)

# ---- front ------------------------------------------------------------------------------
SIDEWALK = (FRONT_LINE, FRONT_LINE + 4.5)   # z band from the front property line (76.808); its top is WALK_Y,
#                                             -0.917 (v7 final: comment; -0.55 is WALK_TOP, the level site's)
PARK = (SIDEWALK[1], SIDEWALK[1] + 4.5)  # planting strip between sidewalk and curb
CURB = (PARK[1], PARK[1] + 0.5)
GUTTER = (CURB[1], CURB[1] + 1.5)
STREET = (GUTTER[1], GUTTER[1] + 34.0)
FAR_GUTTER = (STREET[1], STREET[1] + 1.5)
FAR_CURB = (FAR_GUTTER[1], FAR_GUTTER[1] + 0.5)
FAR_PARK = (FAR_CURB[1], FAR_CURB[1] + 4.5)
FAR_WALK = (FAR_PARK[1], FAR_PARK[1] + 4.5)
WALK_TOP = -0.55                         # sidewalk and street on the level site (FLAT); the neighbourhood modules
STREET_TOP = -1.0                        # build to these and settle() sets them down
# v7 site: the real levels. The sidewalk lies on the front grade line, so the driveway is level from the garage
# slab to the sidewalk; the street right-of-way and everything beyond it keeps its height against the sidewalk.
WALK_Y = GRADE_FRONT                     # sidewalk top, -0.917
ROW_DROP = WALK_Y - WALK_TOP             # -0.367: how far settle() lowers the right-of-way and what lies south of it
STREET_Y = STREET_TOP + ROW_DROP         # gutter line of the street, -1.367


def settle_dy(z):
    """How far a point of the level site (FLAT) at plan z is lowered onto the real ground."""
    if z > SIDEWALK[0] + 1e-3:
        return ROW_DROP
    return grade(z) - FLAT


FRONT_FENCE_Z = SIDEWALK[0] - 0.45       # low front fence line (west front lawn only)

# v7 site: SKA001's "(E) CONCRETE DRIVE WAY", 18'-1" wide (x 21.65..39.73: from 4 1/8 in west of the garage's west
# wall face to the east wall's outer face), from under the vehicle door to the sidewalk. The porch's east pier
# stands in its north-west corner (PORCH_PAD: the porch slab under the pier).
DRIVE = (R.X_FOYER_E + 0.343, R.XE_OUT + 0.005, R.Z_GAR_S + 0.1, SIDEWALK[0])
DRIVE_TOP0, DRIVE_TOP1 = GRADE_FRONT, WALK_Y    # at the garage slab / at the sidewalk: level, -0.917
PORCH_PAD = (PORCH_POSTS[1][0], PORCH_POSTS[1][1] + 0.05, GARAGE_FRONT, PORCH[3])   # slab under the east pier
WALKWAY = ((PORCH[0] + PORCH[1]) / 2 - 2.25, (PORCH[0] + PORCH[1]) / 2 + 2.25)   # pavers, centred on the porch
CORRIDOR = (PORCH[0], DRIVE[0], PORCH[3], SIDEWALK[0])     # dark pebble field around the walk
W_FRONT_BED = (FW + 0.12, HX0 - 0.035, GATE_WZ + 0.12, BED3_FRONT)
FRONT_BED = (FW + 0.12, PORCH[0], BED3_FRONT, BED3_FRONT + 5.04)        # (runs under the west pier)
FRONT_LAWN = (FW + 0.12, PORCH[0], BED3_FRONT + 5.04, FRONT_FENCE_Z - 0.2)
FRONT_STRIP = (FW + 0.12, PORCH[0], FRONT_FENCE_Z + 0.12, SIDEWALK[0])
E_FRONT_BED1 = (HX1 + 0.04, FE - 0.12, GATE_EZ + 0.12, GARAGE_FRONT)
E_FRONT_BED2 = (DRIVE[1], FE - 0.12, GARAGE_FRONT, SIDEWALK[0])
E_BANK_X = DRIVE[1] + 2.7                # (the east bed's bank began here while the driveway sloped up to the floor)


# v7 repair: the ground SURFACES run on to the fence lines. The rectangles above stop 0.12 ft short of the two
# side-yard return fences and 0.2 / 0.12 ft short of the low front fence (the planting is laid out in them, and
# keeps to them); the bare ground plane showed in strips under both gates and along the front fence.
# exterior_site.soft_surfaces builds each surface over SURFACE_TO_FENCE.get(its name, its rectangle).
def _zspan(r, z0=None, z1=None):
    return (r[0], r[1], r[2] if z0 is None else z0, r[3] if z1 is None else z1)


SURFACE_TO_FENCE = {
    'bed west side': _zspan(W_BED, z1=GATE_WZ), 'pebbles west side': _zspan(W_PEB, z1=GATE_WZ),
    'bed east side': _zspan(E_BED, z1=GATE_EZ), 'pebbles east side': _zspan(E_PEB, z1=GATE_EZ),
    'bed west front': _zspan(W_FRONT_BED, z0=GATE_WZ), 'bed east front 1': _zspan(E_FRONT_BED1, z0=GATE_EZ),
    'lawn front': _zspan(FRONT_LAWN, z1=FRONT_FENCE_Z), 'pebbles front strip': _zspan(FRONT_STRIP, z0=FRONT_FENCE_Z),
}


def drive_top(z):
    t = (z - DRIVE[2]) / (DRIVE[3] - DRIVE[2])
    t = min(max(t, 0.0), 1.0)
    return DRIVE_TOP0 + (DRIVE_TOP1 - DRIVE_TOP0) * t


STRIP = (WALKWAY[1] + 0.4, DRIVE[0], PORCH[3], SIDEWALK[0])     # planted strip between walk and driveway


def bank_top(x, z, x_low, x_high):
    """Bed level beside the driveway, on the level site (FLAT; settle() sets the plants down). v7 site: the
    driveway lies on the ground now (it sloped up to the house floor before), so the beds beside it are level."""
    return FLAT + (0.04 if x > DRIVE[1] else -0.04)      # east bed's mulch / the gravel strip beside the walk
