"""Old concept plan -> architect's plan (sizes/sizes.pdf, sheet SKA002 "(N) FLOOR PLAN", Option A).

The tour model was drawn from an earlier concept with the same rooms in the same arrangement as the
architect's plan but different sizes. This module maps every old SCENE coordinate (feet; x west->east,
z rear(north)->street(south)) onto the architect's sheet, region by region, with 1-D piecewise linear
maps whose breakpoints are wall faces.

THE SHEET'S FRAME (eighth round, 2026-11-24). The model's coordinate system IS the sheet's:
x = (X - 1107.075) / 18, z = (Y - 361.808) / 18 in PDF points of SKA002, so the west wall's interior face
is x 0.225 and the rear wall's interior face is z 0.225. Every wall, inside and outside, is 5 in thick
(WALL) as the sheet draws it, and every room's clear rectangle is the sheet's (ROOMS, built from the
printed dimensions; they agree with the sheet's line work, the audit's ska002_geometry.json, to 0.001 ft,
the walk-in closet's east wall to 0.010 ft because the sheet draws 6'-0 7/8" where it prints 6'-1"). A
number read off the sheet is a number of the model. (Until the seventh round the walls kept the concept's
thicknesses, exterior 0.45 ft and interior 0.36 ft, so wall faces drifted from the sheet's by up to 0.11 ft
in x and 0.28 ft in z and the house measured 39.870 x 54.117 ft instead of 39'-11" x 54'-4".)

  rear row      primary 11'-1" x 12'-3", bedroom 2 (PDF "Bedroom #1") 10'-6" x 12'-3", living 16'-8" wide
  left column   walk-in closet 8'-0", primary bath 9'-6" x 7'-2", office (tour "Bedroom 4") 8'-0",
                front bath 5'-0" (8'-3" wide) + two closets, front bedroom (tour "Bedroom 3",
                PDF "Bedroom #2") 11'-0" deep
  middle        shared bath 5'-0" x 7'-2", foyer 18'-6" long, covered porch 7'-4" deep
  owner's change (2026-11-19): the foyer-side wall of the office and the front bedroom lines up with the
                shared bath's east wall (FOYER_WALL, x 15.142..15.558) instead of the sheet's 1'-3" jog, so
                both rooms are 14'-11" wide, the closets between them 6'-3", and the foyer and the porch
                5'-9" instead of 7'-0". (With the concept's thinner walls the same alignment gave 5'-9 1/4"
                and 14'-10 5/16".) The front door keeps its 3'-0" and stays centred.
  right         living + kitchen & dining 30'-10" deep, garage 17'-7" x 20'-11"
  Bedroom 2's closet block and the hall: the maps still carry the concept's entry alcove, its closet (4'-9" clear)
                and the wall south of them (on the line of the sheet's closet wall, z 14.808..15.225) to where
                they stood until the seventh round; after the warp bl/revisions.hall_block rebuilds the block
                to the sheet (the "v7 hall" lines below: hall 3'-3" beside a 7'-8" x 4'-8" block, hall 3'-4"
                south of it, closet 6'-10", furnace and storage closets 1'-11" deep)

Outer size: 39'-11" x 54'-4" (39.917 x 54.333 ft), 53'-0" on the garage side; the porch slab ends 7'-4"
in front of the front door wall (5'-0" beside the garage + 2'-4" beyond it). The three front faces
(Bedroom 3, garage, front door wall) carry a stucco skin (STUCCO, 0.065 ft): the skin's face is the
sheet's outer line and the shell wall behind it is thinner by the skin, so the finished wall is 5 in.

remap_xz(x, z) maps a point; remap_box(...) maps an axis-aligned box (its two corners, by the region
of its centre); remap_mesh(...) maps mesh vertices one by one (a vertex always maps the same way,
so shared edges stay closed).
"""
import bisect
import re

# ---------------------------------------------------------------------------------- the sheet's frame
# SCENE feet. Chains of the printed dimensions from the two interior faces at 0.225; every wall is WALL.
WALL = 5.0 / 12.0                       # every wall on the sheet, inside and outside: 5 in
STUCCO = 0.065                          # the stucco skin on the three front faces (inside the 5 in)
ORIGIN = 0.225                          # the west wall's and the rear wall's interior faces


def _ft(feet, inches=0.0):
    return feet + inches / 12.0


# x lines: wall faces, west -> east
XW_OUT = ORIGIN - WALL                  # -0.1917  west wall, outer face
XW = ORIGIN                             #  0.2250  west wall, interior face
X_WIC_E = XW + _ft(6, 1)                #  6.3083  walk-in closet, east face (printed 6'-1"; the sheet's line is at 6.298)
X_VEST_W = X_WIC_E + WALL               #  6.7250  primary vestibule, west face
X_B3BATH_E = XW + _ft(8, 3)             #  8.4750  Bedroom 3 bath, east face
X_CLO_W = X_B3BATH_E + WALL             #  8.8917  the two closets between Bedroom 4 and Bedroom 3, west face
X_PBATH_E = XW + _ft(9, 6)              #  9.7250  primary bath, east face
X_SBATH_W = X_PBATH_E + WALL            # 10.1417  shared bath, west face
X_PRI_E = XW + _ft(11, 1)               # 11.3083  primary bedroom / vestibule, east face
X_BED2_W = X_PRI_E + WALL               # 11.7250  Bedroom 2 and the hall, west face
X_SBATH_E = X_SBATH_W + _ft(5, 0)       # 15.1417  shared bath, east face = Bedroom 4 / Bedroom 3 / closets, east face
X_FOYER_W = X_SBATH_E + WALL            # 15.5583  foyer and porch, west face (owner: on the shared bath's wall line)
X_BED2_E = X_BED2_W + _ft(10, 6)        # 22.2250  Bedroom 2, east face
X_LIV_W = X_BED2_E + WALL               # 22.6417  living room, west face
X_LIV_E = X_LIV_W + _ft(16, 8)          # 39.3083  east wall, interior face (living, kitchen, garage)
XE_OUT = X_LIV_E + WALL                 # 39.7250  east wall, outer face
X_GAR_W = X_LIV_E - _ft(17, 7)          # 21.7250  garage, west face
X_FOYER_E = X_GAR_W - WALL              # 21.3083  foyer and porch, east face
X_FOYER_W_SHEET = X_FOYER_E - _ft(7, 0)  # 14.3083  where the SHEET has the foyer's west face (7'-0" foyer): not built
# z lines: wall faces, rear -> street
ZN_OUT = ORIGIN - WALL                  # -0.1917  rear wall, outer face
ZN = ORIGIN                             #  0.2250  rear wall, interior face
Z_PRI_S = ZN + _ft(12, 3)               # 12.4750  primary bedroom and Bedroom 2, south face
Z_WIC_N = Z_PRI_S + WALL                # 12.8917  walk-in closet, vestibule, hall and Bedroom 2's closet block, north face
Z_WIC_S = Z_WIC_N + _ft(8, 0)           # 20.8917  walk-in closet, vestibule and hall, south face
Z_PBATH_N = Z_WIC_S + WALL              # 21.3083  primary bath and shared bath, north face
Z_PBATH_S = Z_PBATH_N + _ft(7, 2)       # 28.4750  primary bath and shared bath, south face
Z_B4_N = Z_PBATH_S + WALL               # 28.8917  Bedroom 4 (office), north face; the foyer's north end
Z_B4_S = Z_B4_N + _ft(8, 0)             # 36.8917  Bedroom 4, south face
Z_B3BATH_N = Z_B4_S + WALL              # 37.3083  Bedroom 3 bath and Bedroom 4's closet, north face
Z_B3BATH_S = Z_B3BATH_N + _ft(5, 0)     # 42.3083  Bedroom 3 bath and Bedroom 3's closet, south face
Z_CLO_DIV = ((Z_B3BATH_N + Z_B3BATH_S - WALL) / 2, (Z_B3BATH_N + Z_B3BATH_S + WALL) / 2)   # 39.6000, 40.0167
Z_B3_N = Z_B3BATH_S + WALL              # 42.7250  Bedroom 3, north face
Z_B3_S = Z_B3_N + _ft(11, 0)            # 53.7250  Bedroom 3, south (front) face
Z_B3_OUT = Z_B3_S + WALL                # 54.1417  Bedroom 3 front wall, outer face
Z_FOYER_S = Z_B4_N + _ft(18, 6)         # 47.3917  foyer, south face (front door wall, inside)
Z_PORCH_N = Z_FOYER_S + WALL            # 47.8083  front door wall, outer face = the porch's north face
Z_PORCH_S = Z_PORCH_N + _ft(7, 4)       # 55.1417  porch slab, front edge
Z_KIT_S = ZN + _ft(30, 10)              # 31.0583  kitchen, south face
Z_GAR_N = Z_KIT_S + WALL                # 31.4750  garage, north face
Z_GAR_S = Z_GAR_N + _ft(20, 11)         # 52.3917  garage, south face
Z_GAR_OUT = Z_GAR_S + WALL              # 52.8083  garage front wall, outer face
# kept from the concept (a later stage rebuilds Bedroom 2's entry / closet block to the sheet): the alcove's
# wall to the closet, whose closet keeps its 4'-9" clear, and the wall south of both, 1'-11" from the bedroom's
# south wall like the sheet's closet wall (WL27, z 14.809..15.226)
X_B2CLO_W = X_BED2_E - _ft(4, 9)        # 17.4750  Bedroom 2 closet, west face
X_B2ALC_E = X_B2CLO_W - WALL            # 17.0583  Bedroom 2 entry alcove, east face
Z_B2ALC_S = Z_WIC_N + _ft(1, 11)        # 14.8083  alcove and closet, south face
Z_HALL_N = Z_B2ALC_S + WALL             # 15.2250  hall, north face
# v7 hall (eighth round, stage B): Bedroom 2's closet block and the hall as the SHEET draws them. The four lines
# above are where the shell still builds the concept's alcove, closet and hall wall (the maps carry them there);
# bl/revisions.hall_block (bl/zones/hall_block.py) rebuilds the block after the warp on the lines below:
# hall 3'-3" wide beside a block 7'-8" wide over its walls and 4'-8" deep, its south face 17'-4" from the rear
# wall's interior face, the hall 3'-4" clear south of it; inside the block Bedroom 2's closet (6'-10" x 1'-11")
# and, behind a 5 in wall, the furnace closet (3'-2") and the storage closet (3'-3"), each 1'-11" deep.
X_BLOCK_W = X_BED2_W + _ft(3, 3)        # 14.9750  closet block, west face = the hall's west leg, east face
X_BLOCK_IN = X_BLOCK_W + WALL           # 15.3917  Bedroom 2's closet and the furnace closet, west face
X_FAU_E = X_BLOCK_IN + _ft(3, 2)        # 18.5583  furnace (FAU) closet, east face
X_STO_W = X_FAU_E + WALL                # 18.9750  storage closet, west face (its east face is X_BED2_E)
Z_B2CLO_S = Z_WIC_N + _ft(1, 11)        # 14.8083  Bedroom 2's closet, south face
Z_FAU_N = Z_B2CLO_S + WALL              # 15.2250  furnace and storage closets, north face
Z_FAU_S = Z_FAU_N + _ft(1, 11)          # 17.1417  furnace and storage closets, south face
Z_BLOCK_S = Z_FAU_S + WALL              # 17.5583  closet block, south face = the hall's east leg, north face
#                                         (= ZN + 17'-4"; the block is Z_WIC_N .. Z_BLOCK_S = 4'-8" deep)

# the foyer-side wall of the office / front bedroom, aligned with the shared bath's east wall (owner, 2026-11-19)
FOYER_WALL = (X_SBATH_E, X_FOYER_W)

# Clear rectangles between wall faces (x0, x1, z0, z1): the sheet's, with the owner's foyer-side wall.
ROOMS = {
    'primary': (XW, X_PRI_E, ZN, Z_PRI_S),                       # 11'-1" x 12'-3"
    'closet': (XW, X_WIC_E, Z_WIC_N, Z_WIC_S),                   # walk-in closet, 6'-1" x 8'-0"
    'vestibule': (X_VEST_W, X_PRI_E, Z_WIC_N, Z_WIC_S),          # 4'-7" x 8'-0"
    'primary_bath': (XW, X_PBATH_E, Z_PBATH_N, Z_PBATH_S),       # 9'-6" x 7'-2"
    'shared_bath': (X_SBATH_W, X_SBATH_E, Z_PBATH_N, Z_PBATH_S),  # 5'-0" x 7'-2"
    'bed2': (X_BED2_W, X_BED2_E, ZN, Z_PRI_S),                   # main room, 10'-6" x 12'-3"
    'hall': (X_BED2_W, X_BLOCK_W, Z_WIC_N, Z_WIC_S),             # v7 hall: west leg, 3'-3" x 8'-0"
    'hall_east': (X_BLOCK_W, X_LIV_W, Z_BLOCK_S, Z_WIC_S),       # v7 hall: east leg, 7'-8" x 3'-4", open to the living room
    'bed2_closet': (X_BLOCK_IN, X_BED2_E, Z_WIC_N, Z_B2CLO_S),   # v7 hall: 6'-10" x 1'-11"
    'fau': (X_BLOCK_IN, X_FAU_E, Z_FAU_N, Z_FAU_S),              # v7 hall: furnace closet, 3'-2" x 1'-11"
    'sto': (X_STO_W, X_BED2_E, Z_FAU_N, Z_FAU_S),                # v7 hall: storage closet, 3'-3" x 1'-11"
    'living': (X_LIV_W, X_LIV_E, ZN, Z_KIT_S),                   # living + kitchen & dining, 16'-8" x 30'-10"
    'bed4': (XW, X_SBATH_E, Z_B4_N, Z_B4_S),                     # office, 14'-11" x 8'-0" (sheet 13'-8")
    'bed4_closet': (X_CLO_W, X_SBATH_E, Z_B3BATH_N, Z_CLO_DIV[0]),
    'bed3_bath': (XW, X_B3BATH_E, Z_B3BATH_N, Z_B3BATH_S),       # 8'-3" x 5'-0"
    'bed3_closet': (X_CLO_W, X_SBATH_E, Z_CLO_DIV[1], Z_B3BATH_S),
    'bed3': (XW, X_SBATH_E, Z_B3_N, Z_B3_S),                     # 14'-11" x 11'-0" (sheet 13'-8")
    'foyer': (X_FOYER_W, X_FOYER_E, Z_B4_N, Z_FOYER_S),          # 5'-9" x 18'-6" (sheet 7'-0")
    'porch': (X_FOYER_W, X_FOYER_E, Z_PORCH_N, Z_PORCH_S),       # 5'-9" x 7'-4"
    'garage': (X_GAR_W, X_LIV_E, Z_GAR_N, Z_GAR_S),              # 17'-7" x 20'-11"
}
# centre lines of the exterior walls (windows and glazed doors stand on them)
WEST_C, EAST_C, REAR_C = (XW_OUT + XW) / 2, (X_LIV_E + XE_OUT) / 2, (ZN_OUT + ZN) / 2

# ---------------------------------------------------------------------------------- 1-D maps
# (old, new) breakpoints; linear in between, extrapolated with the end slopes.


def _pl(pairs):
    pairs = sorted(pairs)
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]

    def f(v):
        if v <= xs[0]:                           # beyond the end walls: plain translation
            return ys[0] + (v - xs[0])
        if v >= xs[-1]:
            return ys[-1] + (v - xs[-1])
        i = bisect.bisect_right(xs, v) - 1
        t = (v - xs[i]) / (xs[i + 1] - xs[i])
        return ys[i] + t * (ys[i + 1] - ys[i])
    f.pairs = pairs
    return f


# Old side: the concept's exterior walls are centred on x = 0 / z = 0 and 0.45 thick, its partitions 0.36.
# New side: the sheet's lines above.
_W = [(-0.225, XW_OUT), (0.225, XW)]                 # the west wall
_E = [(40.612, X_LIV_E), (41.062, XE_OUT)]           # the east wall
X_REAR = _pl(_W + [(11.892, X_PRI_E), (12.252, X_BED2_W), (17.558, X_B2ALC_E), (17.918, X_B2CLO_W),
                   (22.918, X_BED2_E), (23.278, X_LIV_W)] + _E)
# Bedroom 2's main room (and the rear wall along it). No wall crosses it: the two middle breakpoints are the line
# of the alcove / closet wall as the concept's 0.36 partition, which the seventh round's map had here too, so the
# room's furniture and its rear window stand where they stood, measured from the room's own walls.
X_BED2 = _pl(_W + [(11.892, X_PRI_E), (12.252, X_BED2_W), (17.558, X_BED2_W + 5.390), (17.918, X_BED2_W + 5.750),
                   (22.918, X_BED2_E), (23.278, X_LIV_W)] + _E)
X_PRIMARY = _pl(_W + [(11.892, X_PRI_E), (12.252, X_BED2_W)])
X_BATHS = _pl(_W + [(10.392, X_PBATH_E), (10.752, X_SBATH_W), (16.002, X_SBATH_E), (16.362, X_FOYER_W),
                    (23.278, X_LIV_W)] + _E)
X_HALL = _pl(_W + [(11.892, X_PRI_E), (12.252, X_BED2_W), (16.002, X_SBATH_E), (16.362, X_FOYER_W),
                   (23.278, X_LIV_W)] + _E)
# The office / front bedroom wing. Its foyer-side wall is a 0.36 partition in the concept (13.892..14.252)
# beside the foyer and a 0.45 exterior wall (13.892..14.342) beside the porch; both are FOYER_WALL now.
X_FRONT_LEFT = _pl(_W + [(7.725, X_B3BATH_E), (8.085, X_CLO_W), (13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]),
                         (14.342, FOYER_WALL[1] + 0.09)])
X_FRONT_ROOMS = _pl(_W + [(13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]), (14.342, FOYER_WALL[1] + 0.09)])
# ... beside the porch. The wing's foundation, its floor slab and its front wall end on the partition's centre
# line (14.072) along the whole wall, the floor of its front extension on the exterior wall's (14.117). Both lines
# are the 5 in wall's centre line here, as the first is beside the foyer: a slab's edge stays one straight line
# under the wall, and a box mapped by its centre (the web scene) ends where the slab mapped corner by corner does.
_FOYER_WALL_C = (FOYER_WALL[0] + FOYER_WALL[1]) / 2
X_FRONT_PORCH = _pl(_W + [(13.892, FOYER_WALL[0]), (14.072, _FOYER_WALL_C), (14.117, _FOYER_WALL_C),
                          (14.342, FOYER_WALL[1])])
# foyer: the 3'-0" front door (old jambs 15.86 / 18.86) keeps its width, centred between the walls
_DOOR_C = (X_FOYER_W + X_FOYER_E) / 2
X_FRONT = _pl([(13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]), (15.86, _DOOR_C - 1.5), (18.86, _DOOR_C + 1.5),
               (20.465, X_FOYER_E), (20.915, X_GAR_W)] + _E)

# v7 garage: the vehicle door's wall opening is the sheet's (DR19): 15'-0" between the wall's ends, 1'-3" from the
# garage's west face (x 22.975..37.975; the 14'-10" door stands between two 1 in jamb boards, bl/garage_spec.py).
# (Until the seventh round the concept's 14'-10 1/4" opening kept its width, centred in the garage.)
GARAGE_DOOR_RO = (X_GAR_W + 1.25, X_GAR_W + 16.25)
X_GARAGE = _pl([(13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]), (20.465, X_FOYER_E), (20.915, X_GAR_W),
                (23.40155, GARAGE_DOOR_RO[0]), (38.25925, GARAGE_DOOR_RO[1])] + _E)

# garage north wall: the fitted cabinet run spanned the old garage wall to wall (x 21.1 .. 40.50); the plan's
# garage is 2'-1" narrower inside, so the run is scaled to fit (cabinets ~10% narrower), wall faces as X_GARAGE
X_GARAGE_RUN = _pl([(20.465, X_FOYER_E), (20.915, X_GAR_W), (21.1, X_GAR_W + 0.185), (40.50, X_LIV_E - 0.11)] + _E)

_N = [(-0.225, ZN_OUT), (0.225, ZN)]                 # the rear wall
Z_LEFT = _pl(_N + [(15.142, Z_PRI_S), (15.502, Z_WIC_N), (20.918, Z_WIC_S), (21.278, Z_PBATH_N),
                   (29.278, Z_PBATH_S), (29.638, Z_B4_N), (37.472, Z_B4_S), (37.832, Z_B3BATH_N),
                   (39.832, Z_CLO_DIV[0]), (40.192, Z_CLO_DIV[1]), (42.832, Z_B3BATH_S), (43.192, Z_B3_N),
                   (53.832, Z_B3_S), (54.282, Z_B3_OUT - STUCCO), (54.347, Z_B3_OUT)])   # shell face, stucco face
Z_MID = _pl(_N + [(12.725, Z_PRI_S), (13.085, Z_WIC_N), (15.142, Z_B2ALC_S), (15.502, Z_HALL_N),
                  (20.918, Z_WIC_S), (21.278, Z_PBATH_N), (29.278, Z_PBATH_S), (29.638, Z_B4_N),
                  (46.722, Z_FOYER_S), (47.082, Z_PORCH_N - STUCCO), (47.147, Z_PORCH_N),   # foyer 18'-6"
                  (51.30, Z_PORCH_S)])                                                    # porch 7'-4"
Z_RIGHT = _pl(_N + [(31.411, Z_KIT_S), (31.771, Z_GAR_N), (50.832, Z_GAR_S), (51.282, Z_GAR_OUT - STUCCO),
                    (51.347, Z_GAR_OUT)])
# Bedroom 3's bath. The wall between the two closets stands beside it, not in it: in the bath the two breakpoints
# of that wall are its line as the concept's 0.36 partition, centred where the 5 in wall is (as in X_BED2), which
# the seventh round's map had here too. So the bath's tiles and fixtures and its window W11 stand where they
# stood, measured from the room's own walls (with Z_LEFT the 5 in wall stretched the bath it does not cross:
# its loose fixtures slid 0.026 ft along the fitted ones and W11 came out 3.023 ft wide instead of 3'-0").
_ZC = (Z_CLO_DIV[0] + Z_CLO_DIV[1]) / 2
Z_B3BATH = _pl([p for p in Z_LEFT.pairs if p[0] not in (39.832, 40.192)]
               + [(39.832, _ZC - 0.18), (40.192, _ZC + 0.18)])
# The hall's north-east corner. In the concept the wall between Bedroom 2 and the living room (x 22.918..23.278)
# ends on the centre line of the wall south of Bedroom 2's closet (z 15.322) and that wall ends on the first one's
# centre line (x 23.098): each stops half-way into the other. The first wall's centre lies in 'living', whose Z
# map has no wall there, so its end stood where that map happened to put it: 0.041 ft proud of the hall's north
# face until the seventh round, 0.074 ft short of it with the 5 in walls (an open rebate, floor to ceiling).
# The corner is a butt joint, as the sheet draws it (WL14 runs through, WL27 ends on it at x 22.225): the wall
# between the rooms runs to the hall's north face (Z_B2_LIV, with its baseboards), the closet's wall and the
# baseboard on its closet side end on that wall's west face (X_B2CLO_S: 0.005 ft into it, so that no hairline is
# left between the two boxes; the baseboard on its hall side runs on across the joint as before). Both go with
# Z_HALL_N when the Bedroom 2 block is rebuilt (the sheet's WL14 runs on to z 17.559).
Z_B2_LIV = _pl(_N + [(15.322, Z_HALL_N)])
X_B2CLO_S = _pl([p for p in X_REAR.pairs if p[0] < 22.9] + [(23.098, X_BED2_E + 0.005)])

# Regions (old coordinates): (x0, x1, z0, z1, X map, Z map, name); the first match wins.
INF = 1e9
REGIONS = [
    (-INF, 12.26, -INF, 21.098, X_PRIMARY, Z_LEFT, 'primary suite'),   # incl. its east wall
    (-INF, 10.572, 21.098, 29.458, X_BATHS, Z_LEFT, 'primary bath'),
    (-INF, 7.9, 37.45, 43.2, X_FRONT_LEFT, Z_B3BATH, 'front bath'),    # the bath; its east wall goes with the closets
    (-INF, 14.65, 37.45, 43.2, X_FRONT_LEFT, Z_LEFT, 'front bath + closets'),   # the two closets
    (-INF, 14.65, 29.458, 46.902, X_FRONT_ROOMS, Z_LEFT, 'office + front bedroom'),
    (-INF, 14.65, 46.902, INF, X_FRONT_PORCH, Z_LEFT, 'front bedroom beside the porch'),   # incl. the porch wall + gable overhang
    (10.572, 16.182, 21.098, 29.458, X_BATHS, Z_MID, 'shared bath'),
    (12.26, 23.098, -INF, 12.725, X_BED2, Z_MID, 'bedroom 2'),          # the main room and its rear wall
    (12.26, 23.098, 12.725, 15.322, X_REAR, Z_MID, 'bedroom 2 entry + closet'),   # from the room's south wall
    (12.26, 20.690, 15.322, 29.458, X_HALL, Z_MID, 'hall'),
    (14.65, 20.60, 29.458, INF, X_FRONT, Z_MID, 'foyer + porch'),
    (20.60, INF, 31.40, 34.30, X_GARAGE_RUN, Z_RIGHT, 'garage north run'),   # cabinet wall (see X_GARAGE_RUN)
    (20.60, INF, 31.40, INF, X_GARAGE, Z_RIGHT, 'garage'),         # from the kitchen/garage wall; incl. its west wall
    (23.098, INF, -INF, 15.322, X_REAR, Z_RIGHT, 'living'),
    (-INF, INF, -INF, INF, X_HALL, Z_RIGHT, 'kitchen + dining'),
]


# Roofs: the entry gable's front line (old z 47.45) is shared by the entry gable, the bedroom-3 gable
# behind its front gable and the garage gable. The three columns map it differently (Z_LEFT 46.85,
# Z_MID 48.22, Z_RIGHT 48.63) because the rooms under them took different plan sizes, which folded the
# roof planes where they meet. Roof vertices beside the foyer follow the foyer's map on that line; there
# is no wall under it in bedroom 3 or the garage, so nothing else moves.
ROOF_LINE = 47.45
# (47.082 and 47.147 are the front door wall's shell face and stucco face, breakpoints of Z_MID: without both the
# gable's stucco, which stands between them and ROOF_LINE, is twisted where it passes from one column to the next)
_BAND = [(v, Z_MID(v)) for v in (47.082, 47.147, ROOF_LINE, 47.562)]   # gable cheek .. bargeboards: one flat front
Z_LEFT_ROOF = _pl(Z_LEFT.pairs + _BAND)
Z_RIGHT_ROOF = _pl(Z_RIGHT.pairs + _BAND)
_ROOF_Z = {'office + front bedroom': Z_LEFT_ROOF, 'front bedroom beside the porch': Z_LEFT_ROOF,
           'front bath': Z_LEFT_ROOF, 'front bath + closets': Z_LEFT_ROOF, 'garage': Z_RIGHT_ROOF}
# The bedroom-wing gable ridge (old x 7.036) runs from the main roof over the primary bath to the front
# gable of bedroom 3. The wing is wider now, so over the primary bath the ridge follows the office /
# bedroom-3 map and stays one straight line (the front gable stays centred on bedroom 3).
WING_RIDGE = 7.036
X_BATHS_ROOF = _pl(X_BATHS.pairs + [(WING_RIDGE, X_FRONT_ROOMS(WING_RIDGE))])
X_PRIMARY_RIDGE = _pl(X_PRIMARY.pairs + [(WING_RIDGE, X_FRONT_ROOMS(WING_RIDGE))])   # its end at the main roof
# The wing's roof is mapped vertex by vertex: along its whole length its east edge follows the wall as it is
# beside the porch (X_FRONT_PORCH), so the eave stays one straight line where the wall turns from partition to
# exterior wall.
_ROOF_X = {'primary bath': X_BATHS_ROOF, 'office + front bedroom': X_FRONT_PORCH,
           'front bedroom beside the porch': X_FRONT_PORCH}


# Pieces whose centre falls on the wrong side of a region edge but belong to the room on the other side.
REGION_BY_NAME = [(re.compile(r'entry vault knee wall', re.I), 'foyer + porch'),
                  # the office's north wall east of the shared bath wall's centre line used to continue into
                  # the old foyer; it ends at the shared bath's east wall like the bath above it
                  (re.compile(r'Old front wall below shared bath', re.I), 'shared bath')]


# Pieces with maps of their own (no plan area: a name picks them, and where two pieces share a name, the side of
# a line their centre lies on): (name, test of the old centre (x, z) or None, region). See Z_B2_LIV / X_B2CLO_S.
PINNED = [(re.compile(r'Bedroom 2 / living divider'), None,        # the wall and its two baseboards
           (None, None, None, None, X_REAR, Z_B2_LIV, 'bedroom 2 / living wall')),
          (re.compile(r'Upper closet — bottom wall KEPT'), lambda x, z: z < 15.4,   # the wall (centre z 15.322) and
           (None, None, None, None, X_B2CLO_S, Z_MID, 'bedroom 2 closet south wall'))]   # the closet's baseboard


def pinned_region(name, at=None):
    """The region a piece is pinned to by its name (and, for PINNED entries with a test, its old centre `at`)."""
    for rx, test, r in PINNED:
        if name and rx.search(name) and (test is None or (at is not None and test(*at))):
            return r
    for rx, nm in REGION_BY_NAME:
        if name and rx.search(name):
            return next(r for r in REGIONS if r[6] == nm)
    return None


def region(x, z):
    for r in REGIONS:
        if r[0] <= x < r[1] and r[2] <= z < r[3]:
            return r
    return REGIONS[-1]


def remap_xz(x, z, at=None, roof=False):
    """New (x, z) of an old point; `at` = (x, z) picks the region (default: the point itself).
    roof=True for roof surfaces mapped vertex by vertex (see ROOF_LINE)."""
    r = region(*(at or (x, z)))
    if roof:
        xm = X_PRIMARY_RIDGE if r[6] == 'primary suite' and z >= 20.5 else _ROOF_X.get(r[6], r[4])
        return xm(x), _ROOF_Z.get(r[6], r[5])(z)
    return r[4](x), r[5](z)


def remap_box(x0, x1, z0, z1, name=None):
    """Axis-aligned box (old) -> new box, mapped with the region of its centre (or its pinned region)."""
    at = ((x0 + x1) / 2, (z0 + z1) / 2)
    r = pinned_region(name, at)
    if r:
        return min(r[4](x0), r[4](x1)), max(r[4](x0), r[4](x1)), min(r[5](z0), r[5](z1)), max(r[5](z0), r[5](z1))
    a = remap_xz(x0, z0, at)
    b = remap_xz(x1, z1, at)
    return min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1])


def shift_xz(x, z):
    """Translation that carries the point (x, z) to its new place (furniture keeps its size)."""
    nx, nz = remap_xz(x, z)
    return nx - x, nz - z


TOUCH = 0.2     # ft: an edge this close to a wall face stays on it


def _anchored(f, a, b):
    c = (a + b) / 2
    xs = [p[0] for p in f.pairs]
    da = min(abs(a - v) for v in xs)
    db = min(abs(b - v) for v in xs)
    if min(da, db) <= TOUCH:                     # against a wall: keep that edge on the wall
        return f(a) - a if da <= db else f(b) - b
    return f(c) - c


def shift_box(x0, x1, z0, z1):
    """Translation for a rigid thing with the plan extent x0..x1, z0..z1 (furniture keeps its size):
    its centre's, except that an edge touching a wall face (within TOUCH) stays on that face, so a
    console or a bed against a wall neither floats off it nor sinks into it where the room narrows."""
    r = region((x0 + x1) / 2, (z0 + z1) / 2)
    return _anchored(r[4], x0, x1), _anchored(r[5], z0, z1)


# Old -> new outer faces used by the site / exterior modules. The new ones are the sheet's outer lines: the
# shell's face on the west, east and rear, the stucco skin's face on the three front walls.
OUTER = dict(west=XW_OUT, east_old=41.062, east=XE_OUT, rear=ZN_OUT,
             front_bed_old=54.282, front_bed=Z_B3_OUT, garage_front_old=51.282, garage_front=Z_GAR_OUT,
             porch_front=Z_PORCH_S, front_wall=Z_PORCH_N, foyer_wall=FOYER_WALL[1])
OUTER_SIZE = (XE_OUT - XW_OUT, Z_B3_OUT - ZN_OUT, Z_GAR_OUT - ZN_OUT)     # 39'-11", 54'-4", 53'-0" (garage side)

if __name__ == '__main__':
    def fi(v):
        n = round(v * 192)
        return '%d\'-%d%s"' % (n // 192, n % 192 // 16, (' %d/16' % (n % 16)) if n % 16 else '')
    print('outside %s x %s (%s on the garage side)' % tuple(fi(v) for v in OUTER_SIZE))
    for name, (x0, x1, z0, z1) in ROOMS.items():
        print(f'{name:13s} x {x0:8.4f} .. {x1:8.4f}  z {z0:8.4f} .. {z1:8.4f}   {fi(x1 - x0):>12s} x {fi(z1 - z0)}')
    for name, (x, z) in {'primary SE': (11.892, 15.142), 'bed2 NE': (22.918, 0.225),
                         'living E': (40.612, 10), 'garage front': (30, 51.282),
                         'bed3 front': (5, 54.282), 'foyer front': (17, 46.722),
                         'office N': (5, 29.638)}.items():
        print(f'{name:14s} {x:7.3f},{z:7.3f} -> {remap_xz(x, z)}')
