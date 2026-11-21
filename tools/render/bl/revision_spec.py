"""Owner's design changes: plan positions shared by bl/revisions.py (Blender) and
apply_revisions_web.py (web data). SCENE feet on the architect's plan (x west->east, z rear->street)."""

# 7. kitchen skylight opening (plan's 3'-6" x 4'-0", next to the dishwasher) on the east roof plane
KITCHEN_SKY = (34.9, 38.4, 23.6, 27.6)
# 3. foyer skylights on the entry roof's east slope (its ridge runs down the middle of the foyer, x ~18.33
#    since the foyer-side wall lines up with the shared bath, relayout.FOYER_WALL)
FOYER_SKY = [(18.75, 20.75, 31.4, 34.4), (18.75, 20.75, 41.9, 44.7)]
# 1. Bedroom 4 (office) flat ceiling: west wall centre .. foyer-side wall centre, north .. south wall centre
OFFICE_CEILING = (0.0, 15.265, 28.54, 36.90)
# 4. primary bedroom sliding door (the old window W01 opening)
SLIDER_X = (2.45, 9.10)
SLIDER_HEAD = 7.0
# 6. primary bathroom window W13. Sixth round (2026-11-20): at the architect's position (sheet SKA002: 3'-0" wide,
#    read off the 300 dpi sheet as z 22.89..25.89), with a mullion on the shower's south glass line (BATH_WIN_MULLION_Z):
#    the north lite is inside the shower, the south lite in the room. (Rounds one to five: z 22.85..24.85, between a
#    vanity on the north wall and a shower in the south-west corner, the layout the owner replaced.)
BATH_WIN_Z = (22.89, 25.89)
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
PRIMARY_BATH_SKY = (2.2, 4.2, 21.5, 24.0)

# ---------------------------------------------------------------------------------------------------------------------
# Sixth round (2026-11-20), the owner: "Refer to the sizes and floor plans for the primary bedroom, bathroom and the
# walk in closet to make it more accurate", and, asked directly: "follow the sheet (shower north-west, toilet
# south-west, double vanity on the south wall, door at the east end of the north wall; skylight moves with the shower;
# west window to the sheet's position, 3 ft wide)". The primary bath (room M03, sweep A0) on sheet SKA002, read off the
# 300 dpi sheet (75 px per foot in the suite crop). Until the fifth round the room was mirrored north-south (vanity on
# the north wall, shower in the south-west corner, door D08 0.98 ft further west).
# bl/revisions.py (bath_door, bath_window, primary_bath_skylight, primary_bath_fit_out) and
# bl/zones/baths_primary.py read these numbers; the web data (apply_revisions_web.py) should read them too.
PRIMARY_BATH_CLEAR = (0.225, 9.725, 21.195, 28.362)   # x0, x1, z0, z1 between the wall faces: 9'-6" x 7'-2"
PRIMARY_BATH_NORTH_WALL_Z = (20.835, 21.195)          # the wall the door is in: vestibule / closet face, bath face
# door D08: the opening in the north wall, hinged on the EAST jamb, swinging into the bath, shown open at 90 degrees
# against the east wall. (The shell builds the concept opening at x 5.914..8.516.)
BATH_DOOR_X = (6.89, 9.45)                # west jamb, east jamb: 2'-6 3/4"
BATH_DOOR_OLD_X = (5.914, 8.516)          # the opening as the shell builds it (bl/revisions.bath_door checks it)
BATH_DOOR_HEAD = 6.67
BATH_DOOR_AXIS = 'x'                      # the opening runs along x in the wall z = BATH_DOOR_C
BATH_DOOR_C = (PRIMARY_BATH_NORTH_WALL_Z[0] + PRIMARY_BATH_NORTH_WALL_Z[1]) / 2      # the wall's centre line, z 21.015
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
BATH_DOOR_LEAF_Y = (0.045, 6.625)         # as the shell's leaf: clear of the bath's tile floor (y 0.028) and the saddle
BATH_DOOR_HINGE_Y = (0.75, 3.30, 5.85)
BATH_DOOR_LEVER = (0.23, 3.0)             # lever handle: inset from the free edge, height
BATH_DOOR_SADDLE_Y = 0.04                 # oak saddle across the opening (the bath's tile floor is 0.028 above the oak)
# shower in the north-west corner, 5'-0" x 3'-0": x0, x1 (centre line of the east glass), z0, z1 (centre line of the
# south glass = the window mullion)
BATH_SHOWER = (0.225, 5.225, 21.195, 24.21)
BATH_WIN_MULLION_Z = BATH_SHOWER[3]       # W13's mullion: the shower's south glass meets the west wall on it
BATH_WIN_TRANSOM_Y = 6.0                  # W13's transom (third round)
# recessed niche in the shower's north wall (the wall between bath and walk-in closet, 0.36 thick):
# x0, x1, y0, y1, depth into the wall from its bath face
BATH_NICHE = (2.55, 3.95, 4.03, 5.23, 0.25)      # its sill on a tile joint (two 24 in courses above the floor)
# toilet in the south-west corner, its back to the south wall, facing north; the sheet's dashed box (x 0.225..3.225)
# is its clear floor space
BATH_TOILET_X = 1.48
BATH_TOILET_CLEAR_X = (0.225, 3.225)
# double vanity along the south wall: 6'-6" x 1'-9" (x0, x1, z0, z1 to the wall's face), basins centred at
BATH_VANITY = (3.225, 9.725, 26.62, 28.362)
BATH_BASINS_X = (4.57, 8.40)
# Repair, not a design change: the garage's west wall (x 21.218..21.578) starts at z 31.238 and the kitchen / garage
# wall (z 31.058..31.418) at x 21.398, each on the other's centre line, which leaves a 0.18 x 0.18 ft notch, floor to
# ceiling, in the outside corner where the foyer's east wall turns into the kitchen's south wall (beside the
# refrigerator's end panel; the two baseboards bridge it with nothing behind them). x0, x1, z0, z1 of the infill
# (bl/revisions.foyer_corner builds it from the two walls as built and checks them against these numbers):
FOYER_CORNER_INFILL = (21.218, 21.398, 31.058, 31.238)
# Sixth round (2026-11-20), the owner: "the bathroom in the front bedroom suite, the window in the shower is too small,
# make it vertically larger". Window W11 (tour: Bedroom 3 bathroom; the shell's "Ensuite privacy window") on the west
# wall, inside the shower. Its width and place stay (3'-0", the jambs as built on the architect's plan), and so do the
# frosted glazing and the black frame with a centre mullion; the sill drops from 5'-0" to 3'-0" and the head rises from
# 7'-0" to 7'-6" (heights confirmed by the owner, above the house's floor datum y = 0; the bath's tile floor is 0.1 ft
# higher). bl/revisions.bedroom3_bath_window reshapes the wall, the frame and the pane; bl/zones/baths.py (build_suite3)
# builds the wall tile, the tiled jamb returns and the quartz sill around the opening from the same heights.
BED3_BATH_WIN_Z = (38.089, 41.087)      # north jamb, south jamb
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

LAUNDRY_CLEAR = (12.085, 15.085, 28.72, 31.553)    # x0, x1, z0, z1 inside: 3'-0" deep (east-west) x 2'-10" wide (north-south)
LAUNDRY_WALL_T = 0.36                              # the two new walls (and the existing ones)
LAUNDRY_CEILING = 8.0                              # flat ceiling above (Bedroom 4's flat ceiling, OFFICE_CEILING)
# the host wall: Bedroom 4's east wall = the foyer's west wall north of the bedroom door D04 (relayout.FOYER_WALL)
LAUNDRY_HOST_WALL = 'Bedroom 4 revised 32 inch entry north jamb'   # SCENE / shell name (object 3338)
LAUNDRY_HOST_WALL_X = (15.085, 15.445)             # its faces: Bedroom 4 / closet side, foyer side
LAUNDRY_HOST_WALL_Z = (28.5423, 33.4317)           # its ends before the cut (the south end is D04's north jamb)
# over the walls: x from the new west wall's Bedroom 4 face to the host wall's foyer face, z from the north wall's
# far face to the new south wall's Bedroom 4 face (11.725..15.445 x 28.36..31.913)
LAUNDRY_OUTER = (LAUNDRY_CLEAR[0] - LAUNDRY_WALL_T, LAUNDRY_HOST_WALL_X[1],
                 LAUNDRY_CLEAR[2] - LAUNDRY_WALL_T, LAUNDRY_CLEAR[3] + LAUNDRY_WALL_T)
# door D17: the opening in the host wall, 2'-6" x 6'-8", centred on the closet's width (= on the units)
LAUNDRY_DOOR_W = 2.5
LAUNDRY_DOOR_HEAD = 6.67
LAUNDRY_DOOR_AXIS = 'z'                            # the opening runs along z in the wall x = LAUNDRY_DOOR_C
_LCZ = (LAUNDRY_CLEAR[2] + LAUNDRY_CLEAR[3]) / 2   # 30.1365
LAUNDRY_DOOR_Z = (_LCZ - LAUNDRY_DOOR_W / 2, _LCZ + LAUNDRY_DOOR_W / 2)     # 28.8865..31.3865 (north jamb, south jamb)
LAUNDRY_DOOR_C = (LAUNDRY_HOST_WALL_X[0] + LAUNDRY_HOST_WALL_X[1]) / 2      # the host wall's centre line x (15.265)
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
# bl/revisions.py (suite_rooms, suite_fit_out) and bl/zones/primary_suite.py read these numbers; the web data
# (apply_revisions_web.py) should read them too. Everything is SCENE feet on the architect's plan.
SUITE_ZONE_Z = (12.835, 20.835)                          # the 8'-0" between the bedroom's south wall and the bath's north wall
SUITE_CEILING = 8.0
SUITE_CLOSET_CLEAR = (0.225, 6.308, 12.835, 20.835)      # x0, x1, z0, z1 inside the walk-in closet: 6'-1" x 8'-0"
SUITE_CLOSET_WALL_X = (6.308, 6.725)                     # the new east wall of the closet (5 in): closet face, vestibule face
SUITE_VESTIBULE_CLEAR = (6.725, 11.308, 12.835, 20.835)  # 4'-7" x 8'-0"
# the wall between bedroom and closet (shell piece 1836, was x 0..5.922) runs on to the new wall's vestibule face;
# the header over the bedroom opening (shell piece 1901, was x 5.922..11.488) starts there
SUITE_NORTH_WALL = 'Retained wall over primary closet'
SUITE_NORTH_HEADER = 'Retained overhead header at open primary bedroom connection'
SUITE_NORTH_WALL_Z = (12.475, 12.835)
SUITE_NORTH_WALL_OLD_X1 = 5.922
# door D10, the open connection bedroom <-> vestibule (no leaf): x0, x1 in the wall z = 12.655, head
SUITE_BED_OPENING_X = (SUITE_CLOSET_WALL_X[1], SUITE_VESTIBULE_CLEAR[1])    # 6.725..11.308 = 4'-7"
SUITE_BED_OPENING_HEAD = 6.67
# the closet's pocket door (a new door: the schedule's next free id)
SUITE_CLOSET_DOOR_W = 2.5
SUITE_CLOSET_DOOR_HEAD = 6.67
SUITE_CLOSET_DOOR_AXIS = 'z'                             # the opening runs along z in the wall x = SUITE_CLOSET_DOOR_C
SUITE_CLOSET_DOOR_C = (SUITE_CLOSET_WALL_X[0] + SUITE_CLOSET_WALL_X[1]) / 2          # 6.5165
_SCZ = (SUITE_ZONE_Z[0] + SUITE_ZONE_Z[1]) / 2           # 16.835: the closet's centre line
SUITE_CLOSET_DOOR_Z = (_SCZ - SUITE_CLOSET_DOOR_W / 2, _SCZ + SUITE_CLOSET_DOOR_W / 2)   # 15.585..18.085: strike jamb, pocket jamb
SUITE_CLOSET_DOOR_POCKET = 'south'                       # the leaf slides south, into the wall z 18.085..20.835
SUITE_CLOSET_DOOR_LINER = 0.03          # painted jamb liners: this far into the opening (and into the wall) on each side
SUITE_CLOSET_DOOR_LINER_PROUD = 0.035   # liners and head trim stand this far off both wall faces (the house's casing)
SUITE_CLOSET_LEAF_W = 2.75              # 2'-9" leaf for the 2'-6" opening (sheet: 2.78), flush slab
SUITE_CLOSET_LEAF_T = 0.115             # 1 3/8"
SUITE_CLOSET_LEAF_Y = (0.02, 6.60)
SUITE_CLOSET_SLOT = 0.0695              # half width of the pocket slot between the split jambs (leaf + 0.012 each side)
# Shown open, the leaf standing this far out of its pocket (the sheet draws it 0.27 ft out), which leaves 2.17 ft
# between its edge and the strike jamb's liner. The brief asked for "about one third out (about 0.8 ft)"; that would
# leave 1.67 ft, and place_sweeps.py floods the walkable floor with a 0.9 ft body radius on a 0.25 ft grid, so a
# passage under about 2.05 ft cuts the closet off the tour.
SUITE_CLOSET_LEAF_SHOWN = 0.30
SUITE_CLOSET_PULL = (0.14, 2.95, 3.55)  # flush pull on both faces: its centre's inset from the leading edge, y0, y1
# door D09, the suite entry: opening in the wall x 11.308..11.668 (shell pieces 3153 north, 3155 header, 3154 south)
SUITE_ENTRY_WALL_X = (11.308, 11.668)                    # vestibule face, hall face
SUITE_ENTRY_SHEET_Z = (13.56, 16.20)                     # where the sheet draws it (see the note above): NOT built
SUITE_ENTRY_OLD_Z = (14.752, 18.888)                     # the concept's 4.1 ft opening with a hinged leaf
SUITE_ENTRY_W = 2.667                                    # 2'-8"
SUITE_ENTRY_Z = (15.21, 15.21 + SUITE_ENTRY_W)           # 15.21..17.877: north jamb 0.10 off Bedroom 2's south wall (z 15.11)
SUITE_ENTRY_HEAD = 6.67
SUITE_ENTRY_AXIS = 'z'
SUITE_ENTRY_C = (SUITE_ENTRY_WALL_X[0] + SUITE_ENTRY_WALL_X[1]) / 2                  # 11.488
SUITE_ENTRY_LINER = 0.03
SUITE_ENTRY_LINER_PROUD = 0.035
SUITE_ENTRY_PANEL_SIDE = 'east'                          # the panel hangs on the hall face
SUITE_ENTRY_PANEL_W = 2.92             # covers the opening with 0.10 (north) and 0.15 (south) when closed
SUITE_ENTRY_PANEL_T = 0.13             # 1 1/2" flush panel
SUITE_ENTRY_PANEL_Y = (0.04, 6.82)      # its top covers the head trim; the track sits right above it
SUITE_ENTRY_PANEL_GAP = 0.075          # between the hall wall face and the panel (clears the baseboard and the liners)
SUITE_ENTRY_PANEL_CLOSED_Z0 = SUITE_ENTRY_Z[0] - 0.10    # 15.11: against Bedroom 2's south wall
SUITE_ENTRY_PANEL_OPEN_Z0 = SUITE_ENTRY_Z[1] - 0.07      # 17.807: parked south, its edge 0.07 inside the south jamb
SUITE_ENTRY_TRACK_Y = (6.84, 6.99)     # slim black top track on the hall face (kept under 7 ft: check_holes.py casts its
#                                        ceiling rays up from 7 ft through everything in the `openings` collection)
SUITE_ENTRY_TRACK_Z = (15.115, 20.74)  # from Bedroom 2's wall to the shared bath wall's baseboard
SUITE_ENTRY_PULL = (0.22, 2.75, 4.25)  # bar pull on the hall face: inset from the leading (north) edge, y0, y1
# Repair at the hall face of the suite entry wall (not a design change): Bedroom 2's doorless entry D12 (header shell
# piece 'Bedroom 2 entry', z 14.75..15.11) has no west jamb; its opening runs to this wall's hall face, but the
# header stopped 0.113 ft short of it (x 11.781), a slot from the head to the ceiling. Until the fifth round the old
# suite entry's casing stood on that corner; now the wall runs past it. The header is carried to the wall, and the
# wall's hall-side baseboard, which the shell builds in two pieces with a 0.04 ft joint at z 14.93, is closed.
SUITE_BED2_HEADER = 'Bedroom 2 entry'                    # shell piece 1902: its west end goes to SUITE_ENTRY_WALL_X[1]
SUITE_BED2_HEADER_OLD_X0 = 11.781
# attic access hatch in the vestibule's ceiling (sheet: "(E) 30X22 ATTIC ACCESS"): x0, x1, z0, z1
SUITE_ATTIC_HATCH = (8.65, 10.49, 13.33, 15.82)


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
    return {SUITE_NORTH_WALL: (0.0, SUITE_CLOSET_WALL_X[1], 0.0, top, n0, n1),
            SUITE_NORTH_HEADER: (SUITE_CLOSET_WALL_X[1], 11.488, SUITE_BED_OPENING_HEAD, top, n0, n1),
            'Aligned primary-suite east wall — north': (ex0, ex1, 0.0, top, 12.655, e0),
            'Aligned primary-suite entry header': (ex0, ex1, SUITE_ENTRY_HEAD, top, e0, e1),
            'Aligned primary-suite east wall — south': (ex0, ex1, 0.0, top, e1, 21.015)}


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
