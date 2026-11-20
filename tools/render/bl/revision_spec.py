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
# 6. primary bathroom window: between the vanity front (z 22.76) and the shower wet wall (z 25.23)
BATH_WIN_Z = (22.85, 24.85)
# owner's change 2026-11-19 (third round): Bedroom 2's rear window and the primary bath window no longer run to the
# floor; both stop at a 2'-0" sill and keep their heads at the 8 ft ceiling
TALL_SILL = 2.0
# the concept bath window opening (warped to the new plan) that the bath's wall finish is built around
BATH_OLD_HOLE_Y = (5.0, 7.0)
# owner's change 2026-11-19: a skylight over the shower (x 0.36..4.97, z 25.27..28.30), clear of the rain
# head (x <= 2.44) and on the single west roof plane, 2'-0" x 2'-6"
PRIMARY_BATH_SKY = (2.7, 4.7, 25.55, 28.05)
# Repair, not a design change: the garage's west wall (x 21.218..21.578) starts at z 31.238 and the kitchen / garage
# wall (z 31.058..31.418) at x 21.398, each on the other's centre line, which leaves a 0.18 x 0.18 ft notch, floor to
# ceiling, in the outside corner where the foyer's east wall turns into the kitchen's south wall (beside the
# refrigerator's end panel; the two baseboards bridge it with nothing behind them). x0, x1, z0, z1 of the infill
# (bl/revisions.foyer_corner builds it from the two walls as built and checks them against these numbers):
FOYER_CORNER_INFILL = (21.218, 21.398, 31.058, 31.238)

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
