"""Owner's design changes: plan positions shared by bl/revisions.py (Blender) and
apply_revisions_web.py (web data). SCENE feet on the architect's plan (x west->east, z rear->street).

Eighth round (2026-11-24): the model's frame is the sheet's and every wall is 5 in (tools/render/relayout.py,
"The sheet's frame"). Nothing here is an absolute number any more: every position is written from the wall
faces of relayout (R.XW, R.Z_PBATH_N, ..., R.ROOMS) as the distance it has from its own room's wall, so it keeps
its place in its room when a wall line moves, and a number read off the sheet (audit: ska002_geometry.json) can
be written here as it stands. Positions of pieces the shell builds on the concept plan are that plan's numbers
carried through relayout's maps (R.X_BATHS(6.313)), the way bl/warp.py carries the pieces themselves."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import relayout as R  # noqa: E402  (pure Python: the sheet's wall faces and the concept -> sheet maps)

WALL_T = R.WALL                         # every wall, old and new: 5 in
# centre lines of the exterior walls: the windows and glazed doors the revisions build stand on them
WEST_WALL_C, EAST_WALL_C, REAR_WALL_C = R.WEST_C, R.EAST_C, R.REAR_C
_LIV, _FOY, _B4, _PB = R.ROOMS['living'], R.ROOMS['foyer'], R.ROOMS['bed4'], R.ROOMS['primary_bath']
_FOYER_C = (_FOY[0] + _FOY[1]) / 2      # the entry roof's ridge runs down the middle of the foyer (x 18.433)

# 7. kitchen skylight opening on the east roof plane, over the sink (the owner's place: "kitchen skylight over the
#    sink").
#    v7 roof: 1'-10" x 3'-10" like the sheet's dashed outline (SK2), long side north-south.
#    (Until the seventh round 3'-6" x 4'-0": the "3'-6"" printed inside the outline is the aisle's dimension.)
#    v7 final: its EAST edge stands where the 3'-6" opening's east edge stood, 0.795 ft off the east wall's face, so
#    the narrower well lies over the sink's bowl as the published one did (well x 36.680..38.513; the bowl is
#    x 37.342..38.880, z 24.855..27.327). In the first eighth-round builds it kept the old opening's CENTRE
#    (2.545 ft off the wall: x 35.847..37.680), which put it over the aisle with 0.34 ft of it over the bowl.
#    Along the wall it is where it has always been: its centre 25.375 ft from the rear wall's face.
SKY_W, SKY_L = 22.0 / 12.0, 46.0 / 12.0
KITCHEN_SKY_EAST = 0.795                # v7 final: the well's east edge off the east wall's interior face
KITCHEN_SKY = (_LIV[1] - KITCHEN_SKY_EAST - SKY_W, _LIV[1] - KITCHEN_SKY_EAST,
               _LIV[2] + 25.375 - SKY_L / 2, _LIV[2] + 25.375 + SKY_L / 2)
# v7 roof: the sheet's living-room skylight (SK1: x 34.644..36.478, z 6.767..10.600 on ska002_geometry.json), same
# size, 2.830 ft off the east wall's face and 6.542 ft from the rear wall's
LIVING_SKY = (_LIV[1] - 2.830 - SKY_W, _LIV[1] - 2.830, _LIV[2] + 6.542, _LIV[2] + 6.542 + SKY_L)
# 3. foyer skylights on the entry roof's east slope, 0.42 ft east of the ridge: one over the hall section (2.68 ft
#    from the foyer's north end), one in the vaulted entry (2.52 ft from the front wall)
FOYER_SKY = [(_FOYER_C + 0.4185, _FOYER_C + 2.4185, _FOY[2] + 2.678, _FOY[2] + 5.678),
             (_FOYER_C + 0.4185, _FOYER_C + 2.4185, _FOY[3] - 5.322, _FOY[3] - 2.522)]
# 1. Bedroom 4 (office) flat ceiling: west wall centre .. foyer-side wall centre, north .. south wall centre
OFFICE_CEILING = (WEST_WALL_C, sum(R.FOYER_WALL) / 2, _B4[2] - WALL_T / 2, _B4[3] + WALL_T / 2)
# 4. primary bedroom sliding door (the old window W01 opening), in the rear wall on its centre line
# v7 glazing: the WALL opening as the sheet draws it, 6'-4" at x 2.439..8.772 (ska002_geometry.json DR01; 6'-0" clear
# between the door's 2 in frames). It was 6'-7 13/16" at x 2.450..9.100 until the seventh round (audit F14).
SLIDER_X = (R.XW + 2.214, R.XW + 2.214 + 6.0 + 4.0 / 12.0)
SLIDER_HEAD = 7.0
# Bedroom 2's rear window (5.): the wall pieces below and above it, as the shell builds them
BED2_WIN_X = (R.X_BED2(14.940), R.X_BED2(20.335))
# the kitchen's ceiling east of the original house's central panel (bl/revisions.kitchen_skylight rebuilds it in one
# piece): from that panel's east edge to the east wall's centre line, rear wall's to the kitchen / garage wall's
KITCHEN_CEILING = (R.X_HALL(29.400), EAST_WALL_C, REAR_WALL_C, (R.Z_KIT_S + R.Z_GAR_N) / 2)
# 6. primary bathroom window W13. Sixth round (2026-11-20): at the architect's position (sheet SKA002: 3'-0" wide,
#    read off the 300 dpi sheet as z 22.89..25.89), with a mullion on the shower's south glass line (BATH_WIN_MULLION_Z):
#    the north lite is inside the shower, the south lite in the room. (Rounds one to five: z 22.85..24.85, between a
#    vanity on the north wall and a shower in the south-west corner, the layout the owner replaced.)
BATH_WIN_Z = (_PB[2] + 1.695, _PB[2] + 4.695)     # 1.695 ft from the bath's north wall (the sheet: 1.675)
# owner's change 2026-11-19 (third round): Bedroom 2's rear window and the primary bath window no longer run to the
# floor; both stop at a 2'-0" sill and keep their heads at the 8 ft ceiling
TALL_SILL = 2.0
# the concept bath window opening the shell builds (sill 5'-0", head 7'-0"); bl/revisions.bath_window removes it.
# (Until the fifth round the bath's wall finish was built around this hole and re-cut; since the sixth round the room
# is fitted out after the warp, straight around BATH_WIN_Z, and nothing reads this number any more.)
BATH_OLD_HOLE_Y = (5.0, 7.0)
# owner's change 2026-11-19: a skylight "over the shower", 2'-0" x 2'-6" (W20). Sixth round: it moves with the shower
# into the north-west corner (BATH_SHOWER), on the single west roof plane of the bedroom wing, clear of the rain head
# (x <= 1.70) and of the shower's glass. (Rounds two to five: x 2.7..4.7, z 25.55..28.05, over the old shower.)
PRIMARY_BATH_SKY = (_PB[0] + 1.975, _PB[0] + 3.975, _PB[2] + 0.305, _PB[2] + 2.805)

# ---------------------------------------------------------------------------------------------------------------------
# Sixth round (2026-11-20), the owner: "Refer to the sizes and floor plans for the primary bedroom, bathroom and the
# walk in closet to make it more accurate", and, asked directly: "follow the sheet (shower north-west, toilet
# south-west, double vanity on the south wall, door at the east end of the north wall; skylight moves with the shower;
# west window to the sheet's position, 3 ft wide)". The primary bath (room M03, sweep A0) on sheet SKA002, read off the
# 300 dpi sheet (75 px per foot in the suite crop). Until the fifth round the room was mirrored north-south (vanity on
# the north wall, shower in the south-west corner, door D08 0.98 ft further west).
# bl/revisions.py (bath_door, bath_window, primary_bath_skylight, primary_bath_fit_out) and
# bl/zones/baths_primary.py read these numbers; the web data (apply_revisions_web.py) should read them too.
PRIMARY_BATH_CLEAR = _PB                               # x0, x1, z0, z1 between the wall faces: 9'-6" x 7'-2"
PRIMARY_BATH_NORTH_WALL_Z = (R.Z_WIC_S, R.Z_PBATH_N)  # the wall the door is in: vestibule / closet face, bath face
# door D08: the opening in the north wall, hinged on the EAST jamb, swinging into the bath, shown open at 90 degrees
# against the east wall. (The shell builds the concept opening at x 5.914..8.516.)
BATH_DOOR_X = (_PB[1] - 2.835, _PB[1] - 0.275)    # west jamb, east jamb: 2'-6 3/4", 0.275 ft off the east wall
BATH_DOOR_OLD_X = (R.X_BATHS(6.313), R.X_BATHS(9.098))    # the opening as the shell builds it (bl/revisions.bath_door
#                                                           checks it): 5.914..8.516
BATH_DOOR_HEAD = 6.67
BATH_DOOR_AXIS = 'x'                      # the opening runs along x in the wall z = BATH_DOOR_C
BATH_DOOR_C = (PRIMARY_BATH_NORTH_WALL_Z[0] + PRIMARY_BATH_NORTH_WALL_Z[1]) / 2      # the wall's centre line, z 21.100
BATH_DOOR_HINGE = 'east'
BATH_DOOR_SWING = 'south'                 # into the bath
BATH_DOOR_OPEN_DEG = 90.0                 # 0 = closed, 90 = square to the wall = parallel to the east wall
BATH_DOOR_LINER = 0.03                    # painted jamb liner: this far into the opening (and into the wall) on each side
BATH_DOOR_LINER_PROUD = (0.035, 0.085)    # liners / head trim proud of the wall: vestibule face (the house's casing), bath
#                                           face (in front of the bath's 0.065 ft wainscot and its plaster)
BATH_DOOR_HINGE_GAP = 0.01
BATH_DOOR_HINGE_PIN = 0.012
BATH_DOOR_LEAF_W = BATH_DOOR_X[1] - BATH_DOOR_X[0] - 2 * BATH_DOOR_LINER - 2 * BATH_DOOR_HINGE_GAP     # 2.48: a 2'-6" leaf
BATH_DOOR_LEAF_T = 0.115                  # 1 3/8" flush slab like the other interior doors
BATH_DOOR_LEAF_Y = (0.045, 6.575)         # clear of the bath's tile floor (y 0.028) and the saddle; v7 repair: its top
#                                           is 3/16 in under the head liner (6.590) like every other hinged leaf (the
#                                           shell's 6.625 stood 0.42 in above the liner: the door could not close)
BATH_DOOR_HINGE_Y = (0.75, 3.30, 5.85)
BATH_DOOR_LEVER = (0.23, 3.0)             # lever handle: inset from the free edge, height
BATH_DOOR_SADDLE_Y = 0.04                 # oak saddle across the opening (the bath's tile floor is 0.028 above the oak)
# shower in the north-west corner, 5'-0" x 3'-0": x0, x1 (centre line of the east glass), z0, z1 (centre line of the
# south glass = the window mullion)
BATH_SHOWER = (_PB[0], _PB[0] + 5.0, _PB[2], _PB[2] + 3.015)
BATH_WIN_MULLION_Z = BATH_SHOWER[3]       # W13's mullion: the shower's south glass meets the west wall on it
BATH_WIN_TRANSOM_Y = 6.0                  # W13's transom (third round)
# recessed niche in the shower's north wall (the wall between bath and walk-in closet, 5 in thick):
# x0, x1, y0, y1, depth into the wall from its bath face
BATH_NICHE = (_PB[0] + 2.325, _PB[0] + 3.725, 4.03, 5.23, 0.25)      # its sill on a tile joint (two 24 in courses above
#                                                                      the floor)
# toilet in the south-west corner, its back to the south wall, facing north; the sheet's dashed box (x 0.225..3.225)
# is its clear floor space
BATH_TOILET_X = _PB[0] + 1.255
BATH_TOILET_CLEAR_X = (_PB[0], _PB[0] + 3.0)
# double vanity along the south wall: 6'-6" x 1'-9" (x0, x1, z0, z1 to the wall's face), basins centred at
BATH_VANITY = (_PB[0] + 3.0, _PB[1], _PB[3] - 1.742, _PB[3])
BATH_BASINS_X = (_PB[0] + 4.345, _PB[0] + 8.175)
# Repair, not a design change: the garage's west wall (x 21.308..21.725) starts at z 31.267 and the kitchen / garage
# wall (z 31.058..31.475) at x 21.517, each on the other's centre line, which leaves a 0.21 x 0.21 ft notch, floor to
# ceiling, in the outside corner where the foyer's east wall turns into the kitchen's south wall (beside the
# refrigerator's end panel; the two baseboards bridge it with nothing behind them). x0, x1, z0, z1 of the infill
# (bl/revisions.foyer_corner builds it from the two walls as built and checks them against these numbers):
FOYER_CORNER_INFILL = (R.X_FOYER_E, (R.X_FOYER_E + R.X_GAR_W) / 2, R.Z_KIT_S, (R.Z_KIT_S + R.Z_GAR_N) / 2)
# Sixth round (2026-11-20), the owner: "the bathroom in the front bedroom suite, the window in the shower is too small,
# make it vertically larger". Window W11 (tour: Bedroom 3 bathroom; the shell's "Ensuite privacy window") on the west
# wall, inside the shower. Its width and place stay (3'-0", the jambs as built on the architect's plan), and so do the
# frosted glazing and the black frame with a centre mullion; the sill drops from 5'-0" to 3'-0" and the head rises from
# 7'-0" to 7'-6" (heights confirmed by the owner, above the house's floor datum y = 0; the bath's tile floor is 0.1 ft
# higher). bl/revisions.bedroom3_bath_window reshapes the wall, the frame and the pane; bl/zones/baths.py (build_suite3)
# builds the wall tile, the tiled jamb returns and the quartz sill around the opening from the same heights.
BED3_BATH_WIN_Z = (R.Z_B3BATH(38.700), R.Z_B3BATH(41.700))  # north jamb, south jamb, as the shell builds them (the
#                                                             bath's own map): 38.315..41.314, 3'-0" (the sheet:
#                                                             38.308..41.308)
BED3_BATH_WIN_Y = (3.0, 7.5)            # sill, head of the opening (the frame stands inside it)
BED3_BATH_WIN_OLD_Y = (5.0, 7.0)        # the concept window the shell builds (bl/shell.py)

# ---------------------------------------------------------------------------------------------------------------------
# Fourth round, as corrected by the owner on 2026-11-20: the laundry closet. (The first attempt, 2026-11-19, built it in
# the kitchen's south-west corner after the architect's sheet SKA002; the owner rejected that. Nothing of it is left.)
# "Put washer and dryer right next to bedroom 4 ... take a space of bedroom 4 out ... on the left side of the passway":
# the closet is carved out of Bedroom 4's north-east corner and opens EAST onto the foyer, on the foyer's west side.
#   * north side = Bedroom 4's existing north wall, east side = the existing Bedroom 4 / foyer wall (the "host" wall,
#     shell piece 3338) with the door opening cut into it;
#   * two new full-height walls: a WEST wall (the units' back wall) and a SOUTH wall;
#   * door D17: a PAIR of narrow leaves in a 2'-6" x 6'-8" opening, hinged on the two jambs, swung out into the foyer
#     and standing wide open (LAUNDRY_DOOR_OPEN_DEG), nearly flat against the foyer wall on each side;
#   * the stacked pair faces east, its back to the west wall.
# Blender geometry (bl/revisions.laundry_closet, bl/laundry.py) and the web data (apply_revisions_web.py: room M13,
# door D17, wall boxes, leaves) all read these numbers. Everything is SCENE feet on the architect's plan.
import math

# x0, x1, z0, z1 inside: 3'-0" deep (east-west) x 2'-10" wide (north-south), in the corner of Bedroom 4's east and
# north walls
LAUNDRY_CLEAR = (_B4[1] - 3.0, _B4[1], _B4[2], _B4[2] + 2.0 + 10.0 / 12.0)
LAUNDRY_WALL_T = WALL_T                            # the two new walls (and the existing ones): 5 in
LAUNDRY_CEILING = 8.0                              # flat ceiling above (Bedroom 4's flat ceiling, OFFICE_CEILING)
# the host wall: Bedroom 4's east wall = the foyer's west wall north of the bedroom door D04 (relayout.FOYER_WALL)
LAUNDRY_HOST_WALL = 'Bedroom 4 revised 32 inch entry north jamb'   # SCENE / shell name (object 3338)
LAUNDRY_HOST_WALL_X = R.FOYER_WALL                 # its faces: Bedroom 4 / closet side, foyer side
LAUNDRY_HOST_WALL_Z = (R.Z_LEFT(29.458), R.Z_LEFT(34.250))    # its ends before the cut, as the shell builds it
#                                                    (28.683..33.601; the south end is D04's north jamb)
# over the walls: x from the new west wall's Bedroom 4 face to the host wall's foyer face, z from the north wall's
# far face to the new south wall's Bedroom 4 face (11.725..15.558 x 28.475..32.142)
LAUNDRY_OUTER = (LAUNDRY_CLEAR[0] - LAUNDRY_WALL_T, LAUNDRY_HOST_WALL_X[1],
                 LAUNDRY_CLEAR[2] - LAUNDRY_WALL_T, LAUNDRY_CLEAR[3] + LAUNDRY_WALL_T)
# door D17: the opening in the host wall, 2'-6" x 6'-8", centred on the closet's width (= on the units)
LAUNDRY_DOOR_W = 2.5
LAUNDRY_DOOR_HEAD = 6.67
LAUNDRY_DOOR_AXIS = 'z'                            # the opening runs along z in the wall x = LAUNDRY_DOOR_C
_LCZ = (LAUNDRY_CLEAR[2] + LAUNDRY_CLEAR[3]) / 2   # 30.308
LAUNDRY_DOOR_Z = (_LCZ - LAUNDRY_DOOR_W / 2, _LCZ + LAUNDRY_DOOR_W / 2)     # 29.058..31.558 (north jamb, south jamb)
LAUNDRY_DOOR_C = (LAUNDRY_HOST_WALL_X[0] + LAUNDRY_HOST_WALL_X[1]) / 2      # the host wall's centre line x (15.350)
LAUNDRY_DOOR_HINGES = ('north', 'south')           # one leaf on each jamb
LAUNDRY_DOOR_SWING = 'east'                        # out into the foyer
# Shown wide open, nearly flat on the foyer wall (0 = closed, 180 = flat). The owner's brief says "about 150 degrees";
# at 160 the leaves stand 0.58 ft into the foyer instead of 0.76 and hide less of the units from the foyer's two ends
# (seen from the foyer's centre line 7 ft away, 150 leaves 4 % of the unit fronts in view, 160 a third).
LAUNDRY_DOOR_OPEN_DEG = 160.0
LAUNDRY_DOOR_LINER = 0.03          # painted jamb liner: this far into the opening (and into the wall) on each side
LAUNDRY_DOOR_LINER_PROUD = 0.035   # the liners and the head trim stand this far off both wall faces (the house's casing)
LAUNDRY_HINGE_GAP = 0.01           # between a leaf's hinge edge and its liner (the hinge pins sit on this joint)
LAUNDRY_HINGE_PIN = 0.012          # the pins' axis stands this far off the leaf's outer (foyer) face
LAUNDRY_MEET_GAP = 0.012           # between the two leaves' meeting edges when closed
LAUNDRY_LEAF_W = (LAUNDRY_DOOR_W - 2 * LAUNDRY_DOOR_LINER - 2 * LAUNDRY_HINGE_GAP - LAUNDRY_MEET_GAP) / 2   # 1.204 each
LAUNDRY_LEAF_T = 0.115             # 1 3/8" flush slab like the other interior doors
LAUNDRY_LEAF_Y = (0.02, 6.60)
LAUNDRY_HINGE_Y = (0.75, 3.30, 5.85)               # three knuckle hinges per leaf (centre heights)
LAUNDRY_PULL = (0.16, 3.0, 3.5)                    # bar pull on each leaf's outer face: inset from the meeting edge, y0, y1
LAUNDRY_THRESHOLD_Y = 0.018                        # oak threshold strip across the opening (under the closed leaves)
# stacked front-load pair (washer below, dryer above), centred in the closet's width, facing east
LAUNDRY_UNIT_W, LAUNDRY_UNIT_D, LAUNDRY_UNIT_H = 2.25, 2.52, 3.25   # 27 x 30 1/4 x 39 in each (bodies)
LAUNDRY_UNIT_FRONT = 'east'
LAUNDRY_UNIT_BACK_GAP = 0.38       # hoses and the 4 in vent duct between the bodies and the back (west) wall
LAUNDRY_STACK_TRIM = 0.04          # stacking kit between the two bodies
LAUNDRY_LIGHT = (LAUNDRY_CLEAR[1] - 0.45, _LCZ)    # (x, z) of the flush ceiling light, just inside the door head
# recessed washer outlet box in the back (west) wall: z0, z1, y0, y1, depth into the wall from its closet face.
# It sits behind the stack's north edge, above the washer.
LAUNDRY_HOOKUP_RECESS = (LAUNDRY_CLEAR[2] + 0.12, LAUNDRY_CLEAR[2] + 0.78, 3.50, 4.10, 0.24)


def laundry_walls():
    """Wall boxes of the closet [(name, x0, x1, y0, y1, z0, z1)], floor to the flat ceiling:
    the two NEW walls (west = the back wall, full length; south, butting into it) and the two pieces of the HOST wall
    around the door opening (the return north of it and the header above it). The host wall itself
    (LAUNDRY_HOST_WALL) keeps its part south of the opening: see laundry_host_wall(). The opening is LAUNDRY_DOOR_Z
    up to LAUNDRY_DOOR_HEAD."""
    cx0, cx1, cz0, cz1 = LAUNDRY_CLEAR
    t, top = LAUNDRY_WALL_T, LAUNDRY_CEILING
    hx0, hx1 = LAUNDRY_HOST_WALL_X
    d0, d1 = LAUNDRY_DOOR_Z
    return [('Laundry closet west wall', cx0 - t, cx0, 0.0, top, cz0, cz1 + t),
            ('Laundry closet south wall', cx0, cx1, 0.0, top, cz1, cz1 + t),
            ('Laundry closet door wall north return', hx0, hx1, 0.0, top, LAUNDRY_HOST_WALL_Z[0], d0),
            ('Laundry closet door header', hx0, hx1, LAUNDRY_DOOR_HEAD, top, d0, d1)]


def laundry_host_wall():
    """What is left of the host wall after the cut: (name, x0, x1, y0, y1, z0, z1), from the opening's south jamb to
    the bedroom door D04. In the web SCENE the existing object of that name is shortened to this box."""
    hx0, hx1 = LAUNDRY_HOST_WALL_X
    return (LAUNDRY_HOST_WALL, hx0, hx1, 0.0, LAUNDRY_CEILING, LAUNDRY_DOOR_Z[1], LAUNDRY_HOST_WALL_Z[1])


def laundry_leaf(side='north', open_deg=None):
    """One leaf of the pair, `side` = the jamb it is hinged on ('north' | 'south'), at `open_deg` (default
    LAUNDRY_DOOR_OPEN_DEG; 0 = closed, 90 = square to the wall, 180 = flat on the foyer wall).

    The leaf turns about its hinge pins: closed, its outer face is flush with the jamb liners' outer (foyer) edge and
    its hinge edge stands LAUNDRY_HINGE_GAP off the liner; the pins' axis is on that joint, LAUNDRY_HINGE_PIN proud of
    the leaf's face, so the knuckles stay in the corner between the leaf and the jamb at every angle.
    Returns a dict: `side`, `name`, the pin axis `pivot` (x, z), unit vectors in plan `along` (hinge -> free edge) and
    `through` (outer face -> inner face), `corner` (x, z) = the leaf's hinge-edge / outer-face corner, `rot` (radians
    about +Y, the SCENE object / ctx.box_c convention), the leaf box as `center` (x, y, z) + `size` (width, height,
    thickness) and its axis-aligned bounds `aabb` (x0, x1, y0, y1, z0, z1)."""
    a = math.radians(LAUNDRY_DOOR_OPEN_DEG if open_deg is None else open_deg)
    s = 1.0 if side == 'north' else -1.0            # the closed leaf runs from its hinge toward the other jamb
    jamb = LAUNDRY_DOOR_Z[0] + LAUNDRY_DOOR_LINER if side == 'north' else LAUNDRY_DOOR_Z[1] - LAUNDRY_DOOR_LINER   # liner face
    px = LAUNDRY_HOST_WALL_X[1] + LAUNDRY_DOOR_LINER_PROUD + LAUNDRY_HINGE_PIN
    pz = jamb + s * LAUNDRY_HINGE_GAP / 2
    along = (math.sin(a), s * math.cos(a))
    through = (-math.cos(a), s * math.sin(a))
    u0, v0 = LAUNDRY_HINGE_GAP / 2, LAUNDRY_HINGE_PIN     # the leaf's corner, measured from the pin axis
    w, th = LAUNDRY_LEAF_W, LAUNDRY_LEAF_T
    y0, y1 = LAUNDRY_LEAF_Y

    def at(u, v):
        return px + along[0] * (u0 + u) + through[0] * (v0 + v), pz + along[1] * (u0 + u) + through[1] * (v0 + v)
    cx, cz = at(w / 2, th / 2)
    cs = [at(u, v) for u in (0.0, w) for v in (0.0, th)]
    xs, zs = [c[0] for c in cs], [c[1] for c in cs]
    return {'side': side, 'name': f'Laundry closet door leaf {side} (open)',
            'pivot': (px, pz), 'corner': at(0.0, 0.0), 'along': along, 'through': through,
            'rot': math.atan2(-along[1], along[0]), 'center': (cx, (y0 + y1) / 2, cz), 'size': (w, y1 - y0, th),
            'aabb': (min(xs), max(xs), y0, y1, min(zs), max(zs))}


def laundry_leaves(open_deg=None):
    """Both leaves of door D17 (north-hinged, south-hinged), each as laundry_leaf() returns it."""
    return [laundry_leaf(side, open_deg) for side in LAUNDRY_DOOR_HINGES]


def laundry_units():
    """Body boxes (x0, x1, y0, y1, z0, z1) of the stacked pair. The fronts are the x1 faces and look east
    (LAUNDRY_UNIT_FRONT); the round doors stand about 0.09 ft proud of x1."""
    cz = (LAUNDRY_CLEAR[2] + LAUNDRY_CLEAR[3]) / 2
    z0, z1 = cz - LAUNDRY_UNIT_W / 2, cz + LAUNDRY_UNIT_W / 2
    x0 = LAUNDRY_CLEAR[0] + LAUNDRY_UNIT_BACK_GAP
    x1 = x0 + LAUNDRY_UNIT_D
    h, tr = LAUNDRY_UNIT_H, LAUNDRY_STACK_TRIM
    return {'washer': (x0, x1, 0.0, h, z0, z1), 'dryer': (x0, x1, h + tr, 2 * h + tr, z0, z1)}


def bath_door_leaf(open_deg=None):
    """The leaf of the primary bath door D08 at `open_deg` (default BATH_DOOR_OPEN_DEG; 0 = closed, 90 = square to
    the north wall, lying along the east wall), hinged on the east jamb and swinging south into the bath.

    Like laundry_leaf(): the leaf turns about its hinge pins, which stand on the joint between its hinge edge and the
    east jamb liner, BATH_DOOR_HINGE_PIN proud of its bath-side face; closed, that face is flush with the liners'
    bath-side edge. Returns a dict: `name`, the pin axis `pivot` (x, z), unit vectors in plan `along` (hinge -> free
    edge) and `through` (bath-side face -> vestibule-side face), `corner` (x, z) = the leaf's hinge-edge / bath-face
    corner, `rot` (radians about +Y, the SCENE object / ctx.box_c convention), the leaf box as `center` (x, y, z) +
    `size` (width, height, thickness) and its axis-aligned bounds `aabb` (x0, x1, y0, y1, z0, z1)."""
    a = math.radians(BATH_DOOR_OPEN_DEG if open_deg is None else open_deg)
    px = BATH_DOOR_X[1] - BATH_DOOR_LINER - BATH_DOOR_HINGE_GAP / 2
    pz = PRIMARY_BATH_NORTH_WALL_Z[1] + BATH_DOOR_LINER_PROUD[1] + BATH_DOOR_HINGE_PIN
    along = (-math.cos(a), math.sin(a))             # closed: west, toward the other jamb; open: south, into the bath
    through = (-math.sin(a), -math.cos(a))          # closed: north, into the wall; open: west, into the room
    u0, v0 = BATH_DOOR_HINGE_GAP / 2, BATH_DOOR_HINGE_PIN
    w, th = BATH_DOOR_LEAF_W, BATH_DOOR_LEAF_T
    y0, y1 = BATH_DOOR_LEAF_Y

    def at(u, v):
        return px + along[0] * (u0 + u) + through[0] * (v0 + v), pz + along[1] * (u0 + u) + through[1] * (v0 + v)
    cx, cz = at(w / 2, th / 2)
    cs = [at(u, v) for u in (0.0, w) for v in (0.0, th)]
    xs, zs = [c[0] for c in cs], [c[1] for c in cs]
    return {'name': 'Primary bath door leaf (open)', 'pivot': (px, pz), 'corner': at(0.0, 0.0), 'along': along,
            'through': through, 'rot': math.atan2(-along[1], along[0]), 'center': (cx, (y0 + y1) / 2, cz),
            'size': (w, y1 - y0, th), 'aabb': (min(xs), max(xs), y0, y1, min(zs), max(zs))}


# ---------------------------------------------------------------------------------------------------------------------
# Sixth round (2026-11-20): the primary suite's 8 ft zone between the bedroom and the bath, divided as on sheet SKA002.
# The owner: "The walk in closet in the primary bedroom is not correct, you should refer to the floor plan of sizes.pdf
# last page for that, there should be a door since it's a small room for walk in closet". Until the fifth round the
# zone was ONE open dressing area with fitted wardrobes. Read off the sheet at 300 and 1200 dpi (x from the west
# wall's inside face 0.225, z from the closet's north face 12.835):
#   * WALK-IN CLOSET "(E) W.I.C": an enclosed room, clear 6'-1" x 8'-0", behind a new 5 in east wall.
#   * Its door: a sliding POCKET door in that wall. The sheet draws a full jamb at z 15.39..15.58, a split jamb at
#     z 18.07..18.27 and the leaf inside a pocket sleeve z 18.27..20.60 with its nose out to z 17.80. So the clear
#     opening is the 2'-6" between the two jambs, centred on the closet (z 16.835), and the leaf slides SOUTH into the
#     wall. (The wall hatch and the wall's face lines run through every door opening on this sheet, the bath's hinged
#     door included, so they do not show where an opening is; the jambs and the pocket do. The hanging rods the sheet
#     draws along the closet's north and south walls end 2 in off this wall at z 13.75 and z 19.9: a door at the
#     wall's south end would open onto the south rod.)
#   * VESTIBULE: clear 4'-7" x 8'-0", open to the bedroom over its whole width (no door; the existing header at
#     6'-8" stays), with the "(E) 30X22 ATTIC ACCESS" hatch in its ceiling.
#   * SUITE ENTRY (door D09) in the vestibule's east wall: about 2'-8" clear with a SLIDING panel on the hall side
#     that parks south of the opening. The sheet draws the opening at z 13.56..16.20 (SUITE_ENTRY_SHEET_Z), beside
#     its hall alcove. In this model that stretch of the wall backs onto Bedroom 2's entry alcove (x 11.668..17.058,
#     z 12.835..14.75, the concept's layout, behind the framed opening D12 in the wall z 14.75..15.11): the hall only
#     begins at z 15.11 on that side. The opening is therefore built as far north as the hall allows (SUITE_ENTRY_Z),
#     and the panel parks on the wall between it and the shared bath's north wall. Moving it to the sheet's place
#     needs Bedroom 2's entry re-planned first (its door on the line z 12.475..12.835, the alcove given to the hall).
#     (v7 hall, eighth round: that is done. Bedroom 2 is entered through a door in its south wall, the alcove is
#     hall, and the entry is built at SUITE_ENTRY_SHEET_Z; see the constants below and the block "v7 hall".)
# bl/revisions.py (suite_rooms, suite_fit_out) and bl/zones/primary_suite.py read these numbers; the web data
# (apply_revisions_web.py) should read them too. Everything is SCENE feet on the architect's plan.
SUITE_ZONE_Z = (R.Z_WIC_N, R.Z_WIC_S)                     # the 8'-0" between the bedroom's south wall and the bath's north wall
SUITE_CEILING = 8.0
SUITE_CLOSET_CLEAR = R.ROOMS['closet']                   # x0, x1, z0, z1 inside the walk-in closet: 6'-1" x 8'-0"
SUITE_CLOSET_WALL_X = (R.X_WIC_E, R.X_VEST_W)            # the new east wall of the closet (5 in): closet face, vestibule face
SUITE_VESTIBULE_CLEAR = R.ROOMS['vestibule']             # 4'-7" x 8'-0"
# the wall between bedroom and closet (shell piece 1836, was x 0..5.922) runs on to the new wall's vestibule face;
# the header over the bedroom opening (shell piece 1901, was x 5.922..11.488) starts there
SUITE_NORTH_WALL = 'Retained wall over primary closet'
SUITE_NORTH_HEADER = 'Retained overhead header at open primary bedroom connection'
SUITE_NORTH_WALL_Z = (R.Z_PRI_S, R.Z_WIC_N)
SUITE_NORTH_WALL_OLD_X1 = R.X_PRIMARY(6.223)             # 5.923: the wall's east end as the shell builds it
# door D10, the open connection bedroom <-> vestibule (no leaf): x0, x1 in the wall z = 12.683, head
SUITE_BED_OPENING_X = (SUITE_CLOSET_WALL_X[1], SUITE_VESTIBULE_CLEAR[1])    # 6.725..11.308 = 4'-7"
SUITE_BED_OPENING_HEAD = 6.67
# the closet's pocket door (a new door: the schedule's next free id)
SUITE_CLOSET_DOOR_W = 2.5                                # v7 hall (F15): the CLEAR width, between the two jamb liners
SUITE_CLOSET_DOOR_HEAD = 6.67
SUITE_CLOSET_DOOR_AXIS = 'z'                             # the opening runs along z in the wall x = SUITE_CLOSET_DOOR_C
SUITE_CLOSET_DOOR_C = (SUITE_CLOSET_WALL_X[0] + SUITE_CLOSET_WALL_X[1]) / 2          # 6.5167
_SCZ = (SUITE_ZONE_Z[0] + SUITE_ZONE_Z[1]) / 2           # 16.892: the closet's centre line
SUITE_CLOSET_DOOR_LINER = 0.03          # painted jamb liners: this far into the opening (and into the wall) on each side
# v7 hall (F15): the sheet's 2'-6" is the clear width between the linings (ska002_geometry.json DR05: 15.638..18.138).
# Until the seventh round the WALL opening was 2'-6" and the liners left 2'-5 1/4". Now the clear opening is 2'-6",
# centred on the closet (15.642..18.142), and the wall opening is one liner wider on each side.
SUITE_CLOSET_DOOR_CLEAR_Z = (_SCZ - SUITE_CLOSET_DOOR_W / 2, _SCZ + SUITE_CLOSET_DOOR_W / 2)   # between the liners
SUITE_CLOSET_DOOR_Z = (SUITE_CLOSET_DOOR_CLEAR_Z[0] - SUITE_CLOSET_DOOR_LINER,
                       SUITE_CLOSET_DOOR_CLEAR_Z[1] + SUITE_CLOSET_DOOR_LINER)   # the wall opening, 15.612..18.172: strike
#                                                                                  jamb, pocket jamb
SUITE_CLOSET_DOOR_POCKET = 'south'                       # the leaf slides south, into the wall z 18.172..20.892
SUITE_CLOSET_DOOR_LINER_PROUD = 0.035   # liners and head trim stand this far off both wall faces (the house's casing)
SUITE_CLOSET_LEAF_W = 2.78              # 2'-9 3/8" leaf for the 2'-6" clear opening (the sheet draws 2.78), flush slab
SUITE_CLOSET_LEAF_T = 0.115             # 1 3/8"
SUITE_CLOSET_LEAF_Y = (0.02, 6.60)
SUITE_CLOSET_SLOT = 0.0695              # half width of the pocket slot between the split jambs (leaf + 0.012 each side)
# Shown open, the leaf standing this far out of its pocket (the sheet draws it 0.27 ft out), which leaves 2.23 ft
# between its edge and the strike jamb's liner (2.17 ft until the seventh round). The brief asked for "about one third out (about 0.8 ft)"; that would
# leave 1.67 ft, and place_sweeps.py floods the walkable floor with a 0.9 ft body radius on a 0.25 ft grid, so a
# passage under about 2.05 ft cuts the closet off the tour.
SUITE_CLOSET_LEAF_SHOWN = 0.30
SUITE_CLOSET_PULL = (0.14, 2.95, 3.55)  # flush pull on both faces: its centre's inset from the leading edge, y0, y1
# door D09, the suite entry: opening in the wall x 11.308..11.725 (shell pieces 3153 north, 3155 header, 3154 south)
SUITE_ENTRY_WALL_X = (R.X_PRI_E, R.X_BED2_W)             # vestibule face, hall face
SUITE_ENTRY_SHEET_Z = (13.610, 16.277)                   # where the sheet draws its 2'-8" clear (ska002_geometry.json
#                                                          DR04). v7 hall: BUILT there since the eighth round, when
#                                                          Bedroom 2's entry alcove became hall (bl/zones/hall_block.py)
SUITE_ENTRY_OLD_Z = (R.Z_LEFT(16.800), R.Z_LEFT(19.600))  # the concept's 4.1 ft opening with a hinged leaf, as the
#                                                          shell builds it (14.809..18.945)
SUITE_ENTRY_W = 2.667                                    # 2'-8": the CLEAR width, between the two jamb liners
SUITE_ENTRY_LINER = 0.03
# v7 hall: the clear opening is the sheet's, and the wall opening is one liner wider on each side (13.580..16.307).
# (Sixth and seventh round: a 2'-8" WALL opening 2.375 ft from the vestibule's north end, 15.267..17.934, 1'-8" south
# of the sheet's place, beside the wall of Bedroom 2's entry alcove.)
SUITE_ENTRY_CLEAR_Z = SUITE_ENTRY_SHEET_Z                # between the liners
SUITE_ENTRY_Z = (SUITE_ENTRY_CLEAR_Z[0] - SUITE_ENTRY_LINER, SUITE_ENTRY_CLEAR_Z[1] + SUITE_ENTRY_LINER)   # the wall opening
SUITE_ENTRY_HEAD = 6.67
SUITE_ENTRY_AXIS = 'z'
SUITE_ENTRY_C = (SUITE_ENTRY_WALL_X[0] + SUITE_ENTRY_WALL_X[1]) / 2                  # 11.517
SUITE_ENTRY_LINER_PROUD = 0.035
SUITE_ENTRY_PANEL_SIDE = 'east'                          # the panel hangs on the hall face
SUITE_ENTRY_PANEL_W = 10.0 / 3.0       # v7 hall: 3'-4", as the sheet draws it: 4 in past the clear opening on each side
#                                        when closed
SUITE_ENTRY_PANEL_T = 0.13             # 1 1/2" flush panel
SUITE_ENTRY_PANEL_Y = (0.04, 6.82)      # its top covers the head trim; the track sits right above it
SUITE_ENTRY_PANEL_GAP = 0.075          # between the hall wall face and the panel (clears the baseboard and the liners)
SUITE_ENTRY_PANEL_CLOSED_Z0 = SUITE_ENTRY_CLEAR_Z[0] - (SUITE_ENTRY_PANEL_W - SUITE_ENTRY_W) / 2   # 13.277 (v7 hall)
SUITE_ENTRY_PANEL_OPEN_Z0 = SUITE_ENTRY_CLEAR_Z[1]       # 16.277: parked south, its edge on the south liner's face, so the
#                                                          whole 2'-8" is clear (the sheet's track ends where it then ends)
SUITE_ENTRY_TRACK_Y = (6.84, 6.99)     # slim black top track on the hall face (kept under 7 ft: check_holes.py casts its
#                                        ceiling rays up from 7 ft through everything in the `openings` collection)
SUITE_ENTRY_TRACK_Z = (SUITE_ENTRY_PANEL_CLOSED_Z0 - 0.04,           # v7 hall: 13.237..19.650, the panel's travel plus a
                       SUITE_ENTRY_PANEL_OPEN_Z0 + SUITE_ENTRY_PANEL_W + 0.04)   # stop at each end (the sheet: 13.277..19.610)
SUITE_ENTRY_PULL = (0.22, 2.75, 4.25)  # bar pull on the hall face: inset from the leading (north) edge, y0, y1
# Repair at the hall face of the suite entry wall (not a design change): Bedroom 2's doorless entry D12 (header shell
# piece 'Bedroom 2 entry', z 14.808..15.225) has no west jamb; its opening runs to this wall's hall face, but the
# header stopped 0.112 ft short of it (x 11.837), a slot from the head to the ceiling. Until the fifth round the old
# suite entry's casing stood on that corner; now the wall runs past it. The header is carried to the wall, and the
# wall's hall-side baseboard, which the shell builds in two pieces with a 0.04 ft joint at z 14.93, is closed.
SUITE_BED2_HEADER = 'Bedroom 2 entry'                    # shell piece 1902: its west end goes to SUITE_ENTRY_WALL_X[1]
SUITE_BED2_HEADER_OLD_X0 = R.X_REAR(12.363)             # 11.837: its west end as the shell builds it
# attic access hatch in the vestibule's ceiling (sheet: "(E) 30X22 ATTIC ACCESS"): x0, x1, z0, z1
SUITE_ATTIC_HATCH = (R.X_PRI_E - 2.658, R.X_PRI_E - 0.818, SUITE_ZONE_Z[0] + 0.495, SUITE_ZONE_Z[0] + 2.985)


def suite_closet_walls():
    """The three pieces of the walk-in closet's new east wall [(name, x0, x1, y0, y1, z0, z1)]: north of the door,
    the header over it, and the pocket wall south of it (the leaf slides into that one)."""
    x0, x1 = SUITE_CLOSET_WALL_X
    z0, z1 = SUITE_ZONE_Z
    d0, d1 = SUITE_CLOSET_DOOR_Z
    return [('Primary closet east wall north of the door', x0, x1, 0.0, SUITE_CEILING, z0, d0),
            ('Primary closet east wall door header', x0, x1, SUITE_CLOSET_DOOR_HEAD, SUITE_CEILING, d0, d1),
            ('Primary closet east wall door pocket', x0, x1, 0.0, SUITE_CEILING, d1, z1)]


def suite_existing_walls():
    """Existing shell / SCENE wall objects the round reshapes: {name: (x0, x1, y0, y1, z0, z1)} as they are afterwards."""
    ex0, ex1 = SUITE_ENTRY_WALL_X
    e0, e1 = SUITE_ENTRY_Z
    n0, n1 = SUITE_NORTH_WALL_Z
    top = SUITE_CEILING
    # the pieces run between the centre lines of the walls they meet (west wall, suite entry wall, the bedroom's
    # south wall, the bath's north wall)
    return {SUITE_NORTH_WALL: (WEST_WALL_C, SUITE_CLOSET_WALL_X[1], 0.0, top, n0, n1),
            SUITE_NORTH_HEADER: (SUITE_CLOSET_WALL_X[1], SUITE_ENTRY_C, SUITE_BED_OPENING_HEAD, top, n0, n1),
            'Aligned primary-suite east wall — north': (ex0, ex1, 0.0, top, (n0 + n1) / 2, e0),
            'Aligned primary-suite entry header': (ex0, ex1, SUITE_ENTRY_HEAD, top, e0, e1),
            'Aligned primary-suite east wall — south': (ex0, ex1, 0.0, top, e1, BATH_DOOR_C)}


def suite_closet_leaf(shown=None):
    """The closet's pocket door leaf with `shown` ft of it out of the pocket (default SUITE_CLOSET_LEAF_SHOWN; the
    leaf's width = closed, 0 = flush with the pocket jamb): dict with `name`, `center` (x, y, z), `size` (along x,
    height, along z), `rot` 0 and `aabb` (x0, x1, y0, y1, z0, z1)."""
    s = SUITE_CLOSET_LEAF_SHOWN if shown is None else shown
    z0 = SUITE_CLOSET_DOOR_Z[1] - s                     # leading edge
    z1 = z0 + SUITE_CLOSET_LEAF_W
    y0, y1 = SUITE_CLOSET_LEAF_Y
    x0, x1 = SUITE_CLOSET_DOOR_C - SUITE_CLOSET_LEAF_T / 2, SUITE_CLOSET_DOOR_C + SUITE_CLOSET_LEAF_T / 2
    return {'name': 'Primary closet pocket door leaf (open)', 'center': ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
            'size': (x1 - x0, y1 - y0, z1 - z0), 'rot': 0.0, 'aabb': (x0, x1, y0, y1, z0, z1)}


def suite_entry_panel(closed=False):
    """The suite entry's sliding panel on the hall face, parked open south of the opening (or closed): dict with
    `name`, `center`, `size` (along x, height, along z), `rot` 0 and `aabb`."""
    z0 = SUITE_ENTRY_PANEL_CLOSED_Z0 if closed else SUITE_ENTRY_PANEL_OPEN_Z0
    z1 = z0 + SUITE_ENTRY_PANEL_W
    y0, y1 = SUITE_ENTRY_PANEL_Y
    x0 = SUITE_ENTRY_WALL_X[1] + SUITE_ENTRY_PANEL_GAP
    x1 = x0 + SUITE_ENTRY_PANEL_T
    return {'name': 'Primary suite entry sliding panel (open)', 'center': ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
            'size': (x1 - x0, y1 - y0, z1 - z0), 'rot': 0.0, 'aabb': (x0, x1, y0, y1, z0, z1)}


# ---------------------------------------------------------------------------------------------------------------------
# Seventh round (2026-11-21), the owner: "Set all windows to white color, and it should have grid line for these
# windows". bl/revisions.white_windows reads these numbers and works on every window and glazed door of the built
# model (the windows W01, W02, W05, W07..W09, W11..W15, W17, the two sliding doors and the front door's two
# sidelights; the five skylights W16, W18..W21 are left alone).   # v7 final: comment (it named the garden door D14
# and the windows W03 / W04 / W06 / W10, which the eighth round removed, and four skylights)
WINDOW_WHITE = 'window_white'             # bl/materials.py: satin white frames, sashes and grid bars
WINDOW_FRAME_WAS = 'black_aluminum'       # the frame material until the sixth round (the skylights keep it)
WINDOW_GLASS = ('M_glass_clear', 'M_glass_frosted')      # a window pane: an upright piece of this glass in `openings`
WINDOW_SKIP = r'skylight'                 # objects of `openings` that are no window (names)
# Grid bars (simulated divided lites): 7/8 in wide, on both faces of the glass and 0.03 ft proud of each (less where
# a sash is shallower than that, e.g. the slider's panels), with a small chamfer.
WINDOW_BAR_W = 0.073
WINDOW_BAR_PROUD = 0.03
WINDOW_BAR_BEVEL = 0.006
# The house's lite: 14 in wide x 16 1/2 in tall (width : height = 0.85). Every sash is divided into the whole number
# of columns and rows that brings its lites closest to it; no lite may be wider than 1.2 x its height. An upper tier
# lower than 0.6 x the tier under it is a transom: one row, the columns of the sash below.
WINDOW_LITE = (14.0 / 12.0, 16.5 / 12.0)
WINDOW_LITE_MAX_RATIO = 1.2
WINDOW_TRANSOM_RATIO = 0.6
# The kitchen's W08 keeps the grid it had as a black steel window, 2 x 4 lites in each of its three sashes: the
# owner's own kitchen-window picture (styles/kitchen window.jpg), and the house's proportion at a smaller size
# (10.5 x 12.8 in). Pane name -> (columns, rows) per sash.
WINDOW_GRID_KEEP = {r'^W08 glass$': (2, 4)}
# The black bars the kitchen zone built until the sixth round (removed if an old zone still builds them).
WINDOW_OLD_BARS = r'^kd W08 muntin panel'
# Window pieces of the room zones that take the frames' white: the primary bath's stool under W13's dry lite (oak
# until the sixth round) and the post on W13's mullion that carries the shower glass. Also the pull bar on the
# primary bedroom slider's meeting stile (1.6 ft of matte black metal until the review of the seventh round: on the
# white door it read, from across the room and from the garden, as one frame piece left black).
WINDOW_WHITE_ALSO = (r'^A0 window stool', r'^A0 window mullion post$', r'^Primary slider pull$')
# Centre mullions that bl/warp.py left off centre (it maps each piece with the room its own centre lies in): Bedroom
# 2's rear window W02 (0.13 ft east of the middle) and the Bedroom 3 bathroom's W11 (0.18 ft south). Pane names.
WINDOW_MULLION_CENTRE = (r'^\d+ Bedroom 2 — rear wall$', r'^\d+ Ensuite privacy window glazing$')
# Roller shades: "<tag> cassette / fabric / hem bar / bar". A shade that stands in or beyond its window's bars is put
# back square to the pane, 0.01 ft on the room side of the bars (the bay's three shades stood outside the glass and
# 2.4 degrees off its canted sides since the conversion; W10's and W12's cassettes reached 0.003 ft into the bars).
# A shade that had to be turned is set back in the middle of its pane as well (the bay's two side shades stood 0.19 ft
# toward the corner piers, 0.26 ft with the 5 in walls, and their cassettes ran into the piers).
WINDOW_SHADES = r'^(.*\bshade\b.*?) (cassette|fabric|hem bar|bar)$'
WINDOW_HOUSE_CENTRE = (20.0, 27.0)        # a point inside the house (plan x, z): tells a pane's room side (the hall
#                                           between the shared bath and the kitchen; any point well inside will do)


# ---------------------------------------------------------------------------------------------------------------------
# v7 glazing
# Eighth round (2026-11-24), stage B, track "glazing": the door and window openings of the rear wall and of the east
# wall north of the garage, and the primary bedroom's north west window, at the sheet's widths and places (audit F13,
# F14, F16, F17, F20, F21; the sheet as data: ska002_geometry.json DR01, DR02, WN01, WN02, WN07, WN08). bl/revisions.py
# (primary_slider, bedroom2_tall_window, living_slider, primary_west_window, living_east_windows) builds them after
# the warp from these numbers and SLIDER_X above; bl/zones/primary_suite.py (the shades, what stands under W15),
# bl/zones/living.py (what stands at the new openings) and bl/zones/exterior_garage.py (the rear sconces) read them,
# and the web data should too. SCENE feet on the architect's plan, written from relayout's wall faces. Owner's
# decisions that stay: W14 (the primary bedroom's second west window), Bedroom 2's rear window tall (TALL_SILL to the
# ceiling), every unit white with grid bars (bl/revisions.white_windows finds them like any other window).
#
# Sliding glass doors (the sheet's DR01, DR02): the sheet's width is the WALL opening; the door's frame is 2 in on
# each jamb and at the head, so the clear width between the jambs is 4 in less (6'-0", 12'-0"). As the sheet draws
# them, the fixed panels stand on the INNER (room side) track against the jambs and the sliding panels on the OUTER
# track; interlocking stiles cover each other, so a panel is 3'-1 5/16" wide (the sheet's schematic panels: 3'-2").
GLAZING_FRAME = 2.0 / 12.0              # a sliding door's frame members (jambs, head)
GLAZING_STILE = 0.22                    # a sliding panel's stiles and top rail (2 5/8 in)
GLAZING_RAIL_BOTTOM = 0.30              # ... its bottom rail
GLAZING_PANEL_T = 0.125                 # ... its thickness (1 1/2 in)
GLAZING_TRACK = 0.07                    # the two tracks' centre planes off the wall's centre line (inner = room side)
GLAZING_THRESHOLD = 0.055               # top of a sliding door's threshold above the floor: 5/8 in, flush enough to step
#                                         out (the glazing it replaces stood on a 0.2 ft kerb)
# the living room's rear wall (DR02): ONE four-panel sliding door, 12'-4" wall opening, x 25.528..37.861. It replaces
# the garden door D14 (x 24.568..27.046) and the two fixed lights W03 / W04 (x 27.921..33.052, 33.664..38.883). Head as
# the glazing it replaces (the fixed lights' frames ended at 7'-6").
LIVING_SLIDER_X = (R.X_LIV_W + 2.886, R.X_LIV_W + 2.886 + 12.0 + 4.0 / 12.0)
LIVING_SLIDER_HEAD = 7.5
# Shown with ONE centre panel open: the east one, slid east over the fixed east panel by 2'-3", which leaves a 2'-3"
# way (place_sweeps.py needs about 2.05 ft for a passage; the walk-in closet's door shows 2.17 for the same reason).
LIVING_SLIDER_OPEN = ('centre E', 2.25)
# windows rebuilt at the sheet's places (jambs = the wall opening; sill, head)
BED2_REAR_WIN_X = (R.X_BED2_W + 2.198, R.X_BED2_W + 2.198 + 6.0)      # W02 (WN01): 6'-0", x 13.923..19.923; the sill is
#                                                                       TALL_SILL and the head the ceiling (owner)
PRIMARY_WEST_WIN_Z = (R.ZN + 1.0, R.ZN + 4.0)                         # W15 (WN02): 3'-0", z 1.225..4.225
# v7 final: W14, the primary bedroom's second (south) west window. It is the owner's, not the sheet's, and it stays
# in its opening, which the shell builds on the concept plan (z 11.150..14.650) and the warp carries: z 9.197..12.071,
# 2'-10 1/2" wide, sill and head GLAZING_WIN_Y like W15's. bl/revisions.primary_west_window_south rebuilds the UNIT
# in it with the kit of W15 (frame, two sashes side by side, stool), so the two west windows are a pair; until then
# it kept the shell's unit (two lights one above the other with a meeting rail, flush painted jambs, a stone sill).
PRIMARY_WEST_WIN_S_Z = (R.Z_LEFT(11.150), R.Z_LEFT(14.650))           # W14: its jambs as the shell builds them
LIVING_EAST_WIN_Z = (R.ZN + 0.143, R.ZN + 6.143)                      # W05 (WN07): ONE 6'-0" unit, z 0.368..6.368 (it
#                                                                       replaces W05 and W06 and the 9 in pier between)
DINING_EAST_WIN_Z = (R.ZN + 15.841, R.ZN + 20.841)                    # W07 (WN08): 5'-0", z 16.066..21.066
DINING_EAST_WIN_MULLION = R.ZN + 19.215                               # ... its two lights are unequal on the sheet:
#                                                                       the mullion's centre line, z 19.440 (drawn
#                                                                       19.38..19.50)
GLAZING_WIN_Y = (2.5, 7.0)              # sill and head of W15, W05 and W07, as built since the first round
# A rebuilt window: a frame as deep as the wall (it stands 0.015 ft proud of both wall faces, like the shell's heads
# and sills) and inside it two sashes side by side, their meeting stiles one mullion (in the middle, as the sheet
# draws W02, W15 and W05, unless a place is given: W07).
GLAZING_WIN_FRAME = 0.06                # the frame's thickness, all round
GLAZING_WIN_SASH = 0.09                 # sash stiles and rails
GLAZING_WIN_SASH_D = 0.11               # ... their depth (the shell's jamb sections)
GLAZING_WIN_MULLION = 0.14              # the two meeting stiles
# W15's painted stool (the shell's "deep painted sill"): section as built, 0.071 ft past each jamb
GLAZING_STOOL = dict(y=(2.442, 2.506), out=0.03, room=0.133, past=0.071)
# Bedroom 2's ceiling-track drapes at W02: each stack's width and how far it covers the glass from the jamb
BED2_DRAPE = dict(stack=1.35, over=0.33, track_past=0.10)
# The sliders' pulls take the frames' white like the first one (WINDOW_WHITE_ALSO above).
WINDOW_WHITE_ALSO = WINDOW_WHITE_ALSO + (r'^(Primary|Living) slider .*\bpull\b',)


def slider_clear(x):
    """Clear width between a sliding door's jambs: (x0, x1) of the wall opening less the 2 in frame on each side."""
    return x[0] + GLAZING_FRAME, x[1] - GLAZING_FRAME


def slider_panels(x, n, open_panel=None, open_by=0.0):
    """The panels of a sliding glass door in the wall opening x = (x0, x1), west to east: [(tag, x0, x1, track)].
    n = 2: a fixed west panel and a sliding east panel. n = 4: fixed end panels and two sliding centre panels that
    meet in the middle. Fixed panels are on the 'inner' track, sliding panels on the 'outer' one; interlocking stiles
    cover each other. `open_panel` (a tag) is shown slid by `open_by` ft over the fixed panel behind it."""
    c0, c1 = slider_clear(x)
    st = GLAZING_STILE
    if n == 2:
        p = (c1 - c0 + st) / 2
        out = [('fixed', c0, c0 + p, 'inner'), ('sliding', c1 - p, c1, 'outer')]
        away = {'sliding': -1.0}
    else:
        p = (c1 - c0 + 2 * st) / 4
        cm = (c0 + c1) / 2
        out = [('fixed W', c0, c0 + p, 'inner'), ('centre W', cm - p, cm, 'outer'),
               ('centre E', cm, cm + p, 'outer'), ('fixed E', c1 - p, c1, 'inner')]
        away = {'centre W': -1.0, 'centre E': 1.0}
    return [(t, a + away.get(t, 0.0) * open_by * (t == open_panel), b + away.get(t, 0.0) * open_by * (t == open_panel), tr)
            for t, a, b, tr in out]


def living_slider_way():
    """(x0, x1) of the clear way through the living room's sliding door as shown: between the stiles of the two
    centre panels."""
    ps = {t: (a, b) for t, a, b, _ in slider_panels(LIVING_SLIDER_X, 4, *LIVING_SLIDER_OPEN)}
    return ps['centre W'][1], ps['centre E'][0]


# ---------------------------------------------------------------------------------------------------------------------
# v7 bedrooms
# Eighth round (2026-11-24), stage B, track "bedrooms": Bedroom 3's bath, closet and doors and the west windows of
# Bedroom 3 and Bedroom 4 as sheet SKA002 draws them (audit F30, F31, F33, F34, F35, F60, P1; the sheet as data:
# ska002_geometry.json FX07..FX09, DR11..DR15, WN04, WN05). bl/zones/bedrooms_rooms.py (walls, doors, windows, the
# closet's fit-out) and bl/zones/baths_suite3.py (the bath's fit-out) build from these numbers after the warp, called
# by bl/revisions.bedrooms_west_windows / bedroom3_rooms / bedroom3_fit_out; the web data should read them too.
# Everything is SCENE feet on the architect's plan, written from relayout's wall faces. The owner's decisions stay:
# the foyer-side wall on the shared bath's wall line (rooms 14'-11", closets 6'-3"), Bedroom 3's bay glazed to the
# floor, Bedroom 4's door at the south end of the foyer wall, the laundry closet, W11's sill and head.
_B3, _B3B, _B3C = R.ROOMS['bed3'], R.ROOMS['bed3_bath'], R.ROOMS['bed3_closet']

# Bedroom 3's west window W10 (the shell's "Bedroom 3 side window"). The sheet has a solid wall behind the bed (F31:
# the window was never decided). False: the opening is closed, plaster and baseboard inside, the wall's stucco
# outside, and a picture hangs over the bed. True: the window builds as it did until the seventh round (4'-1 5/8"
# wide, sill 2'-6", head 7'-0", white frame with grid bars, roller shade).
BED3_WEST_WINDOW = False
BED3_WEST_WIN_Z = (R.Z_LEFT(44.650), R.Z_LEFT(48.650))     # its jambs as the shell builds them: 44.232..48.368
BED3_WEST_WIN_Y = (2.5, 7.0)

# Bedroom 4's west window W12: 5'-0" wide, centred on the room's west wall (z 28.892..36.892; the laundry closet is
# cut from the east end and leaves this wall whole). The sheet's window WN04 is z 30.392..35.392, centre 32.892: the
# same. Sill and head as built since the first round.
BED4_WEST_WIN_W = 5.0
BED4_WEST_WIN_Z = ((_B4[2] + _B4[3]) / 2 - BED4_WEST_WIN_W / 2, (_B4[2] + _B4[3]) / 2 + BED4_WEST_WIN_W / 2)
BED4_WEST_WIN_OLD_Z = (R.Z_LEFT(30.46365), R.Z_LEFT(34.59935))   # the opening the shell builds: 29.735..33.958
BED4_WEST_WIN_Y = (2.5, 7.0)
BED4_WEST_WIN_SHADE_DROP = 0.45        # the roller shade's fabric below its cassette, as before

# Hinged doors of this track. An opening is given by its CLEAR width, between the faces of the two painted jamb
# liners (the sheet's "clear" between its 2 in frames = the leaf it draws); the wall opening is DOOR_LINER wider on
# each side, the liners stand DOOR_LINER into the opening and DOOR_LINER into the wall, like the house's other doors.
# A leaf is DOOR_LEAF_GAP narrower than its clear opening on each side (F60: the Bedroom 3 and Bedroom 4 leaves were
# 2.7 in wider than their doorways).
DOOR_HEAD = 6.67
DOOR_LINER = 0.03
DOOR_LINER_PROUD = 0.035               # liners and head trim stand this far off a painted wall face
DOOR_LEAF_GAP = 0.25 / 12.0            # 1/4 in
CLOSET_LEAF_GAP = 0.125 / 12.0         # v7 repair: 1/8 in each side for the two leaves that are shown CLOSED in the hall
#                                        (furnace and storage closets): nobody looks past them into the closets
DOOR_LEAF_T = 0.115                    # 1 3/8" flush slab
DOOR_LEAF_Y = (0.02, DOOR_HEAD - 0.08 - DOOR_LEAF_GAP)    # under the head liner (its underside is 0.08 below the wall's head)
DOOR_HINGE_PIN = 0.012                 # the pins' axis stands this far off the leaf's face on the swing side
DOOR_HINGE_Y = (0.75, 3.30, 5.85)
DOOR_LEVER = (0.23, 3.0)               # lever handle: inset from the free edge, height

# Bedroom 3 bath (room M09), as the sheet: x0, x1, z0, z1 between the wall faces, 8'-3" x 5'-0"
BED3_BATH_CLEAR = _B3B
BED3_BATH_FLOOR_Y = 0.10               # the tile floor's top above the house's floor datum (as before)
BED3_BATH_SHOWER = (_B3B[0], _B3B[0] + 3.0, _B3B[2], _B3B[3])     # 3'-0" wide at the west end: x1 = the glass line
BED3_BATH_TOILET_BAY_X = (_B3B[0] + 3.0, _B3B[0] + 5.5)           # 2'-6": glass line .. the vanity's west edge
BED3_BATH_TOILET_X = sum(BED3_BATH_TOILET_BAY_X) / 2              # its centre line, 4.475 (sheet FX08: 4.474); the
#                                                                   toilet hangs on the NORTH wall
BED3_BATH_VANITY = (_B3B[0] + 5.5, _B3B[1], _B3B[2], _B3B[2] + 1.75)   # 2'-9" x 1'-9" on the north wall, against
#                                                                   the east wall (sheet FX09: 5.725..8.475 x 37.308..39.058)
BED3_BATH_BASIN_X = (BED3_BATH_VANITY[0] + BED3_BATH_VANITY[1]) / 2    # 7.100 (the sheet's basin: 6.348..7.857)
# The wall between the bath / Bedroom 3's closet and Bedroom 3 (sheet WL26): bath and closet face, bedroom face
BED3_NORTH_WALL_Z = (R.Z_B3BATH_S, R.Z_B3_N)
BED3_NORTH_WALL_C = (R.Z_B3BATH_S + R.Z_B3_N) / 2
# door D05, bath <-> Bedroom 3 (sheet DR13): hinged 2'-4", at the east end of the bath's south wall, hinged on the
# EAST jamb, swinging north into the bath, shown open at 90 degrees along the bath's east wall. (Until the seventh
# round: a pocket door 2'-10 7/16" wide, 1.73 ft further west.)
BED3_BATH_DOOR_X = (_B3B[1] - R._ft(2, 8), _B3B[1] - R._ft(0, 4))      # clear: 5.808..8.142
BED3_BATH_DOOR_OPEN_DEG = 90.0
BED3_BATH_DOOR_LINER_PROUD = (0.085, DOOR_LINER_PROUD)   # bath face (in front of the 0.065 ft wall tile), bedroom face
BED3_BATH_DOOR_LEAF_Y = (0.125, DOOR_LEAF_Y[1])          # the leaf swings over the bath's tile floor and the saddle
BED3_BATH_DOOR_SADDLE_Y = 0.105                          # quartz saddle across the opening, ramped to the oak floor
# door D06, Bedroom 3's closet (sheet DR15): two bypass sliding panels of 2'-6" in a 4'-8" clear opening that starts
# 2 in from the closet's west end, as on the sheet (9.058..13.725; the closet itself is the owner's 6'-3", so 1'-5"
# of wall is left at its east end, where the sheet has 2 in). Both panels are shown parked at the east end, as the
# sheet draws them. (Until the seventh round: one pocket door, 2'-9 11/16".)
BED3_CLOSET_DOOR_X = (_B3C[0] + R._ft(0, 2), _B3C[0] + R._ft(0, 2) + R._ft(4, 8))     # clear: 9.058..13.725
BED3_CLOSET_PANEL_W = 2.5
BED3_CLOSET_PANEL_T = 0.081            # as Bedroom 4's bypass panels
BED3_CLOSET_PANEL_Y = (0.03, 6.61)
BED3_CLOSET_PANEL_TRACK = 0.055        # each panel's centre plane off the wall's centre line
BED3_CLOSET_PANEL_SHOWN = 0.14         # the rear panel stands this far out behind the front one
BED3_CLOSET_PULL = (0.08, 2.95, 3.55)  # flush pull on each panel's bedroom face: inset from its west edge, y0, y1
BED3_CLOSET_TRACK_Y = (6.625, 6.73)    # the black top track between the two halves of the head trim
# door D03, Bedroom 3's entry in the foyer-side wall (sheet DR12): 2'-8" clear, 4 in from the room's north wall,
# hinged on the NORTH jamb, swinging west into the room, shown open at 90 degrees along the room's north wall.
# (Until the seventh round: 2'-9 9/16" between the casings, hinged on the south jamb.)
BED3_ENTRY_WALL_X = R.FOYER_WALL                         # bedroom face, foyer face
BED3_ENTRY_Z = (_B3[2] + R._ft(0, 4), _B3[2] + R._ft(0, 4) + R._ft(2, 8))          # clear: 43.058..45.725
BED3_ENTRY_OLD_Z = (R.Z_LEFT(43.500), R.Z_LEFT(46.2919))   # the wall opening as the shell builds it: 43.043..45.930
BED3_ENTRY_OPEN_DEG = 90.0
# door D04, Bedroom 4's entry (the owner's place at the south end of the foyer wall): the opening stays as the shell
# builds it, 2'-8" between its liners; only the leaf is new, sized to it, hinged on the north jamb as before.
BED4_ENTRY_WALL_Z = (R.Z_LEFT(34.250), R.Z_LEFT(34.250 + 8.0 / 3.0))     # wall opening: 33.601..36.325
BED4_ENTRY_Z = (BED4_ENTRY_WALL_Z[0] + DOOR_LINER, BED4_ENTRY_WALL_Z[1] - DOOR_LINER)   # clear: 33.631..36.295
BED4_ENTRY_OPEN_DEG = 90.0


def hinged_leaf(name, jamb, a_dir, n_dir, clear, open_deg, proud=DOOR_LINER_PROUD, y=DOOR_LEAF_Y, gap=None):
    """A hinged flush leaf, like bath_door_leaf() for any wall. `jamb` = (x, z) of the hinge jamb's liner face on the
    wall face of the room the door swings into; `a_dir` = unit plan vector from the hinge jamb to the strike jamb,
    `n_dir` = unit plan vector into that room; `clear` = the opening between the liners; `proud` = how far the liners
    stand off that wall face. The leaf is DOOR_LEAF_GAP narrower than `clear` on each side and turns about its hinge
    pins, which stand on the joint between its hinge edge and the liner, DOOR_HINGE_PIN proud of its room-side face;
    closed (open_deg 0), that face is flush with the liners' edge. Returns the dict bath_door_leaf() returns."""
    a = math.radians(open_deg)
    g, pin, th = (DOOR_LEAF_GAP if gap is None else gap), DOOR_HINGE_PIN, DOOR_LEAF_T     # v7 repair: `gap`
    w = clear - 2 * g
    px = jamb[0] + a_dir[0] * g / 2 + n_dir[0] * (proud + pin)
    pz = jamb[1] + a_dir[1] * g / 2 + n_dir[1] * (proud + pin)
    ca, sa = math.cos(a), math.sin(a)
    along = (ca * a_dir[0] + sa * n_dir[0], ca * a_dir[1] + sa * n_dir[1])
    through = (-ca * n_dir[0] + sa * a_dir[0], -ca * n_dir[1] + sa * a_dir[1])
    u0, v0 = g / 2, pin

    def at(u, v):
        return px + along[0] * (u0 + u) + through[0] * (v0 + v), pz + along[1] * (u0 + u) + through[1] * (v0 + v)
    cx, cz = at(w / 2, th / 2)
    cs = [at(u, v) for u in (0.0, w) for v in (0.0, th)]
    xs, zs = [c[0] for c in cs], [c[1] for c in cs]
    return {'name': name, 'pivot': (px, pz), 'corner': at(0.0, 0.0), 'along': along, 'through': through,
            'rot': math.atan2(-along[1], along[0]), 'center': (cx, (y[0] + y[1]) / 2, cz), 'size': (w, y[1] - y[0], th),
            'aabb': (min(xs), max(xs), y[0], y[1], min(zs), max(zs)), 'clear': clear}


def bed3_bath_door_leaf(open_deg=None):
    """Leaf of D05 (2'-4" less 1/4 in each side), hinged on the east jamb, swinging north into the bath."""
    d0, d1 = BED3_BATH_DOOR_X
    return hinged_leaf('Bedroom 3 bath door leaf (open)', (d1, BED3_NORTH_WALL_Z[0]), (-1.0, 0.0), (0.0, -1.0), d1 - d0,
                       BED3_BATH_DOOR_OPEN_DEG if open_deg is None else open_deg, BED3_BATH_DOOR_LINER_PROUD[0],
                       BED3_BATH_DOOR_LEAF_Y)


def bed3_entry_leaf(open_deg=None):
    """Leaf of D03 (2'-8" less 1/4 in each side), hinged on the north jamb, swinging west into Bedroom 3."""
    d0, d1 = BED3_ENTRY_Z
    return hinged_leaf('Bedroom 3 entry door leaf (open)', (BED3_ENTRY_WALL_X[0], d0), (0.0, 1.0), (-1.0, 0.0), d1 - d0,
                       BED3_ENTRY_OPEN_DEG if open_deg is None else open_deg)


def bed4_entry_leaf(open_deg=None):
    """Leaf of D04, sized to its opening, hinged on the north jamb, swinging west into Bedroom 4."""
    d0, d1 = BED4_ENTRY_Z
    return hinged_leaf('Bedroom 4 entry door leaf (open)', (R.FOYER_WALL[0], d0), (0.0, 1.0), (-1.0, 0.0), d1 - d0,
                       BED4_ENTRY_OPEN_DEG if open_deg is None else open_deg)


def bed3_closet_panels():
    """The two bypass panels of D06 as shown: [front (bedroom side), rear (closet side)], each a dict with `name`,
    `center`, `size` (along x, height, along z), `rot` 0 and `aabb`. The front panel stands in its closed place over
    the opening's east half; the rear one, whose closed place is the west half, is slid east behind it."""
    d0, d1 = BED3_CLOSET_DOOR_X
    w, t, k = BED3_CLOSET_PANEL_W, BED3_CLOSET_PANEL_T, BED3_CLOSET_PANEL_TRACK
    y0, y1 = BED3_CLOSET_PANEL_Y
    out = []
    for tag, x1, zc in (('front', d1, BED3_NORTH_WALL_C + k), ('rear', d1 - BED3_CLOSET_PANEL_SHOWN, BED3_NORTH_WALL_C - k)):
        x0 = x1 - w
        out.append({'name': f'Bedroom 3 closet sliding panel {tag}', 'center': ((x0 + x1) / 2, (y0 + y1) / 2, zc),
                    'size': (w, y1 - y0, t), 'rot': 0.0, 'aabb': (x0, x1, y0, y1, zc - t / 2, zc + t / 2)})
    return out


def bed3_north_walls():
    """The five pieces of the wall between the bath / closet and Bedroom 3 after the round, west to east:
    {shell name: (x0, x1, y0, y1, z0, z1)}. The four pocket-cavity faces of the old pocket doors are removed."""
    z0, z1 = BED3_NORTH_WALL_Z
    b0, b1 = BED3_BATH_DOOR_X[0] - DOOR_LINER, BED3_BATH_DOOR_X[1] + DOOR_LINER
    c0, c1 = BED3_CLOSET_DOOR_X[0] - DOOR_LINER, BED3_CLOSET_DOOR_X[1] + DOOR_LINER
    return {'Suite service wall west end': (WEST_WALL_C, b0, 0.0, 8.0, z0, z1),
            'Ensuite pocket header': (b0, b1, DOOR_HEAD, 8.0, z0, z1),
            'Suite service wall middle': (b1, c0, 0.0, 8.0, z0, z1),
            'Walk-in closet pocket header': (c0, c1, DOOR_HEAD, 8.0, z0, z1),
            'Suite service wall east end': (c1, sum(R.FOYER_WALL) / 2, 0.0, 8.0, z0, z1)}


# ---------------------------------------------------------------------------------------------------------------------
# v7 hall
# Eighth round (2026-11-24), stage B, track "hall": Bedroom 2's closet block, the hall and the doors around it as
# sheet SKA002 draws them (audit F08, F09, F10, F11, F42, P3; the sheet as data: ska002_geometry.json WL14, WL16, WL19,
# WL21, WL27..WL30, R07..R11, DR03, DR07..DR10). Until the seventh round this corner kept the concept plan: an entry
# alcove 5'-4" wide open to Bedroom 2 behind a doorless opening one wall further south, a 4'-9" closet, a hall
# 5'-8" deep, and no furnace or storage closet. bl/zones/hall_block.py builds from these numbers after the warp,
# called by bl/revisions.hall_block / hall_block_fit_out; the web data should read them too. Everything is SCENE feet
# on the architect's plan, written from relayout's wall faces (R.X_BLOCK_W ... R.Z_BLOCK_S, R.ROOMS). The suite entry
# and the walk-in closet's pocket door are SUITE_ENTRY_* / SUITE_CLOSET_DOOR_* above. The doors follow DOOR_* ("v7
# bedrooms"): an opening is given by its CLEAR width between the two jamb liners (the sheet's leaf), the wall opening
# is DOOR_LINER wider on each side, a leaf is DOOR_LEAF_GAP narrower than its clear opening on each side.
HALL_WEST = R.ROOMS['hall']                   # the hall's west leg, clear: 3'-3" x 8'-0" (x 11.725..14.975, z 12.892..20.892)
HALL_EAST = R.ROOMS['hall_east']              # its east leg, clear: 7'-8" x 3'-4" (x 14.975..22.642, z 17.558..20.892), open
#                                               to the living room at its east end and to the foyer passage on its south side
HALL_CEILING = 8.0
BED2_CLOSET_CLEAR = R.ROOMS['bed2_closet']    # 6'-10" x 1'-11" (x 15.392..22.225, z 12.892..14.808)
FAU_CLEAR = R.ROOMS['fau']                    # furnace closet, 3'-2" x 1'-11"
STO_CLEAR = R.ROOMS['sto']                    # storage closet, 3'-3" x 1'-11"
HALL_BLOCK = (R.X_BLOCK_W, R.X_LIV_W, R.Z_WIC_N, R.Z_BLOCK_S)    # the closet block over its walls: 7'-8" x 4'-8"
BED2_SOUTH_WALL_Z = (R.Z_PRI_S, R.Z_WIC_N)    # Bedroom 2's south wall (sheet WL16): bedroom face, hall / closet face
BLOCK_WEST_WALL_X = (R.X_BLOCK_W, R.X_BLOCK_IN)       # sheet WL28: hall face, closet face
BLOCK_MID_WALL_Z = (R.Z_B2CLO_S, R.Z_FAU_N)           # sheet WL27: Bedroom 2's closet face, furnace / storage face
BLOCK_SOUTH_WALL_Z = (R.Z_FAU_S, R.Z_BLOCK_S)         # sheet WL30: closet face, hall face
BLOCK_DIVIDER_X = (R.X_FAU_E, R.X_STO_W)              # sheet WL29, between the furnace and the storage closet
SHARED_BATH_NORTH_WALL_Z = (R.Z_WIC_S, R.Z_PBATH_N)   # sheet WL19: hall face, bath face
# door D12, Bedroom 2's entry (sheet DR03): hinged 2'-8", in the bedroom's SOUTH wall, 4 in from the hall's west wall,
# hinged on the WEST jamb, swinging north into the bedroom, shown open at 90 degrees along the bedroom's west wall.
# (Until the seventh round: a doorless opening 2'-11 3/8" wide in the wall one bay further south, z 14.808..15.225.)
BED2_DOOR_X = (HALL_WEST[0] + R._ft(0, 4), HALL_WEST[0] + R._ft(0, 4) + R._ft(2, 8))          # clear: 12.058..14.725
BED2_DOOR_OPEN_DEG = 90.0
# door D13, Bedroom 2's closet (sheet DR08): two bypass sliding panels in a 6'-0" clear opening, 5 in from each end
# of the closet, in the bedroom's south wall. Shown as the sheet draws them: both at the west end, the rear (closet
# side) panel in its closed place over the west half, the front (bedroom side) panel slid west in front of it, its
# east edge BED2_CLOSET_PANEL_SHOWN east of the rear panel's; the east half of the closet stands open. (Until the
# seventh round: a 4'-1 1/2" opening.)
BED2_CLOSET_DOOR_X = (BED2_CLOSET_CLEAR[0] + R._ft(0, 5), BED2_CLOSET_CLEAR[1] - R._ft(0, 5))  # clear: 15.808..21.808
BED2_CLOSET_PANEL_W = 3.0 + 0.06        # 3'-0" each as drawn, plus the lap of the two meeting stiles when closed
BED2_CLOSET_PANEL_T = 0.081             # as Bedroom 4's and Bedroom 3's bypass panels
BED2_CLOSET_PANEL_Y = (0.03, 6.61)
BED2_CLOSET_PANEL_TRACK = 0.055         # each panel's centre plane off the wall's centre line
BED2_CLOSET_PANEL_SHOWN = 0.28          # the front panel's east edge stands this far east of the rear panel's (sheet: 0.29)
BED2_CLOSET_PULL = (0.08, 2.95, 3.55)   # flush pull on each panel's bedroom face: inset from its east edge, y0, y1
BED2_CLOSET_TRACK_Y = (6.625, 6.73)     # the black top track between the two halves of the head trim
# the furnace (FAU) closet's door (sheet DR09; a new door: the schedule's next free id): hinged 1'-8", centred on the
# closet's depth in the block's WEST wall, hinged on the NORTH jamb, swinging west into the hall. A louvred leaf
# (combustion air), shown closed.
_FAU_C = (FAU_CLEAR[2] + FAU_CLEAR[3]) / 2
FAU_DOOR_Z = (_FAU_C - R._ft(0, 10), _FAU_C + R._ft(0, 10))                                    # clear: 15.350..17.017
FAU_DOOR_OPEN_DEG = 0.0
# the storage closet's door (sheet DR10; a new door): hinged 2'-4", in the block's SOUTH wall, 7 in from the closet's
# east wall, hinged on the EAST jamb, swinging south into the hall. A flush leaf, shown closed.
STO_DOOR_X = (STO_CLEAR[1] - R._ft(0, 7) - R._ft(2, 4), STO_CLEAR[1] - R._ft(0, 7))            # clear: 19.308..21.642
STO_DOOR_OPEN_DEG = 0.0
# door D07, the shared bath (sheet DR07): hinged 2'-4", its east liner 2 in west of the line of the closet block's
# west face, hinged on the EAST jamb, swinging south into the bath, shown open at 90 degrees along the bath's east
# wall. (Until the seventh round: a 2'-4 3/16" wall opening 2 in further west, 2'-3 1/4" between its casings, no leaf.)
SHARED_BATH_DOOR_X = (R.X_BLOCK_W - R._ft(0, 2) - R._ft(2, 4), R.X_BLOCK_W - R._ft(0, 2))      # clear: 12.475..14.808
SHARED_BATH_DOOR_OLD_X = (R.X_BATHS(13.01125), R.X_BATHS(15.47995))   # the wall opening as the shell builds it: 12.293..14.645
SHARED_BATH_DOOR_OPEN_DEG = 90.0
SHARED_BATH_DOOR_LINER_PROUD = (DOOR_LINER_PROUD, 0.085)   # hall face, bath face (in front of the 0.058 ft wall tile)
SHARED_BATH_DOOR_LEAF_Y = (0.045, DOOR_HEAD - 0.08 - 0.015)   # v7 final: (0.045, 6.575), the leaf as built. Its foot
#                                                               as the primary bath's, over the tile floor and the
#                                                               saddle; its top 3/16 in under the head liner (6.590)
#                                                               like every hinged leaf (hall_block.LEAF_TOP, which
#                                                               the build has used since the repair; the 6.625 that
#                                                               stood here was the primary bath's old leaf top)
SHARED_BATH_DOOR_SADDLE_Y = 0.04                           # oak saddle across the opening (the tile floor is at 0.028)
# P3: the shared bath's north wall (sheet WL19) runs through to the foyer passage's face and the bath's east wall
# (WL21) butts against its bath face. (The shell ends each on the other's centre line, which left a 0.208 ft square
# open, floor to ceiling, in the outside corner.)
SHARED_BATH_NE_CORNER = (R.X_FOYER_W, R.Z_WIC_S)           # (x, z) of the closed outside corner


def hall_block_walls():
    """The wall pieces of the block and of the walls around the hall after the round:
    {name: (shell piece it is, or None for a new piece, (x0, x1, y0, y1, z0, z1))}. A shell piece named here is
    reshaped onto its box (bl/zones/hall_block.py checks where it finds it); a new piece is a copy of a wall.
    Removed: 'Bedroom 2 entry return' (the wall south of the old alcove). Wall ends that butt into another wall's
    side run 0.01 ft into it (not listed here)."""
    top, hd, ln = HALL_CEILING, DOOR_HEAD, DOOR_LINER
    n0, n1 = BED2_SOUTH_WALL_Z
    b0, b1 = BED2_DOOR_X[0] - ln, BED2_DOOR_X[1] + ln
    c0, c1 = BED2_CLOSET_DOOR_X[0] - ln, BED2_CLOSET_DOOR_X[1] + ln
    wx0, wx1 = BLOCK_WEST_WALL_X
    f0, f1 = FAU_DOOR_Z[0] - ln, FAU_DOOR_Z[1] + ln
    m0, m1 = BLOCK_MID_WALL_Z
    s0, s1 = BLOCK_SOUTH_WALL_Z
    t0, t1 = STO_DOOR_X[0] - ln, STO_DOOR_X[1] + ln
    v0, v1 = BLOCK_DIVIDER_X
    h0, h1 = SHARED_BATH_NORTH_WALL_Z
    d0, d1 = SHARED_BATH_DOOR_X[0] - ln, SHARED_BATH_DOOR_X[1] + ln
    return {
        # Bedroom 2's south wall (WL16), west to east
        'Bedroom 2 south wall west of the entry': (None, (HALL_WEST[0], b0, 0.0, top, n0, n1)),
        'Bedroom 2 entry': ('Bedroom 2 entry', (b0, b1, hd, top, n0, n1)),                       # the header over D12
        'Bedroom 2 upper closet — north (pier)': ('Bedroom 2 upper closet — north', (b1, c0, 0.0, top, n0, n1)),
        'Bedroom 2 upper closet — north (header)': ('Bedroom 2 upper closet — north', (c0, c1, hd, top, n0, n1)),
        'Bedroom 2 upper closet — north (east)': ('Bedroom 2 upper closet — north', (c1, R.X_BED2_E, 0.0, top, n0, n1)),
        # the block's west wall (WL28), north to south
        'Bedroom 2 upper closet — west': ('Bedroom 2 upper closet — west', (wx0, wx1, 0.0, top, n1, f0)),
        'Furnace closet door header': (None, (wx0, wx1, hd, top, f0, f1)),
        'Closet block west wall south of the furnace door': (None, (wx0, wx1, 0.0, top, f1, s1)),
        # the wall between Bedroom 2's closet and the furnace / storage closets (WL27)
        'Upper closet — bottom wall KEPT': ('Upper closet — bottom wall KEPT', (wx1, R.X_BED2_E, 0.0, top, m0, m1)),
        # the divider between the furnace and the storage closet (WL29)
        'Furnace / storage closet divider': (None, (v0, v1, 0.0, top, m1, s0)),
        # the block's south wall (WL30), west to east
        'Closet block south wall west of the storage door': (None, (wx1, t0, 0.0, top, s0, s1)),
        'Storage closet door header': (None, (t0, t1, hd, top, s0, s1)),
        'Closet block south wall east of the storage door': (None, (t1, R.X_BED2_E, 0.0, top, s0, s1)),
        # the wall between Bedroom 2 / the block and the living room (WL14) runs on to the block's south face
        'Bedroom 2 / living divider': ('Bedroom 2 / living divider', (R.X_BED2_E, R.X_LIV_W, 0.0, top, REAR_WALL_C, s1)),
        # the shared bath's north wall (WL19) with D07, and its east wall (WL21)
        'Shared bathroom north / walk-in south': ('Shared bathroom north / walk-in south',
                                                  (BATH_DOOR_X[1], d0, 0.0, top, h0, h1)),
        'Original shared bath — north (header)': ('Original shared bath — north', (d0, d1, hd, top, h0, h1)),
        'Original shared bath — north (east)': ('Original shared bath — north', (d1, R.X_FOYER_W, 0.0, top, h0, h1)),
        'Original shared bath — east': ('Original shared bath — east',
                                        (R.X_SBATH_E, R.X_FOYER_W, 0.0, top, h1, (R.Z_PBATH_S + R.Z_B4_N) / 2)),
    }


def bed2_door_leaf(open_deg=None):
    """Leaf of D12 (2'-8" less 1/4 in each side), hinged on the west jamb, swinging north into Bedroom 2."""
    d0, d1 = BED2_DOOR_X
    return hinged_leaf('Bedroom 2 entry door leaf (open)', (d0, BED2_SOUTH_WALL_Z[0]), (1.0, 0.0), (0.0, -1.0), d1 - d0,
                       BED2_DOOR_OPEN_DEG if open_deg is None else open_deg)


def shared_bath_door_leaf(open_deg=None):
    """Leaf of D07 (2'-4" less 1/4 in each side), hinged on the east jamb, swinging south into the shared bath."""
    d0, d1 = SHARED_BATH_DOOR_X
    return hinged_leaf('Shared bath door leaf (open)', (d1, SHARED_BATH_NORTH_WALL_Z[1]), (-1.0, 0.0), (0.0, 1.0), d1 - d0,
                       SHARED_BATH_DOOR_OPEN_DEG if open_deg is None else open_deg, SHARED_BATH_DOOR_LINER_PROUD[1],
                       SHARED_BATH_DOOR_LEAF_Y)


def fau_door_leaf(open_deg=None):
    """Leaf of the furnace closet's door (1'-8" less 1/8 in each side, CLOSET_LEAF_GAP), hinged on the north jamb,
    swinging west into the hall."""                                   # v7 final: comment (it said 1/4 in)
    d0, d1 = FAU_DOOR_Z
    return hinged_leaf('Furnace closet door leaf', (BLOCK_WEST_WALL_X[0], d0), (0.0, 1.0), (-1.0, 0.0), d1 - d0,
                       FAU_DOOR_OPEN_DEG if open_deg is None else open_deg, gap=CLOSET_LEAF_GAP)


def sto_door_leaf(open_deg=None):
    """Leaf of the storage closet's door (2'-4" less 1/8 in each side, CLOSET_LEAF_GAP), hinged on the east jamb,
    swinging south into the hall."""                                  # v7 final: comment (it said 1/4 in)
    d0, d1 = STO_DOOR_X
    return hinged_leaf('Storage closet door leaf', (d1, BLOCK_SOUTH_WALL_Z[1]), (-1.0, 0.0), (0.0, 1.0), d1 - d0,
                       STO_DOOR_OPEN_DEG if open_deg is None else open_deg, gap=CLOSET_LEAF_GAP)


def bed2_closet_panels():
    """The two bypass panels of D13 as shown: [front (bedroom side), rear (closet side)], each a dict with `name`,
    `center`, `size` (along x, height, along z), `rot` 0 and `aabb`. The rear panel stands in its closed place over
    the opening's west half; the front one, whose closed place is the east half, is slid west in front of it."""
    d0, d1 = BED2_CLOSET_DOOR_X
    w, t, k = BED2_CLOSET_PANEL_W, BED2_CLOSET_PANEL_T, BED2_CLOSET_PANEL_TRACK
    y0, y1 = BED2_CLOSET_PANEL_Y
    zc = (BED2_SOUTH_WALL_Z[0] + BED2_SOUTH_WALL_Z[1]) / 2
    out = []
    for tag, x0, z in (('front', d0 + BED2_CLOSET_PANEL_SHOWN, zc - k), ('rear', d0, zc + k)):
        x1 = x0 + w
        out.append({'name': f'Bedroom 2 closet sliding panel {tag}', 'center': ((x0 + x1) / 2, (y0 + y1) / 2, z),
                    'size': (w, y1 - y0, t), 'rot': 0.0, 'aabb': (x0, x1, y0, y1, z - t / 2, z + t / 2)})
    return out


# v7 garage: the front door unit with its sidelights, the door between house and garage, the garage's side door, the
# vehicle door's opening, the garage floor with its step and the water heater have their numbers in bl/garage_spec.py
# (pure Python like this module; bl/garage.py builds from it, after the warp)
from . import garage_spec as GARAGE  # noqa: E402,F401
