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

# ---------------------------------------------------------------------------------------------------------------------
# Fourth round (2026-11-19): laundry closet. The architect's sheet SKA002 draws "W / D" in the kitchen's south-west
# corner: north of the kitchen / garage wall, its west wall continuing the garage west wall's line, "REF." directly
# east of it, the door in its north face (hinged east, swinging north). Printed sizes: 3'-10" x 3'-5" over the walls.
# Blender geometry (bl/revisions.laundry_closet, bl/laundry.py), the kitchen's pantry wall (bl/zones/kitchen_dining_
# kitchen.py) and the web data (apply_revisions_web.py: room M13, door D17, wall boxes) all read these numbers.
import math

LAUNDRY_OUTER = (21.218, 25.051, 27.641, 31.058)   # x0, x1, z0, z1 over the walls; z1 = the kitchen / garage wall's north face
LAUNDRY_WALL_T = 0.36                              # west, east and north (door) walls
LAUNDRY_CEILING = 8.0                              # flat ceiling above (the original house's central panel)
LAUNDRY_CLEAR = (LAUNDRY_OUTER[0] + LAUNDRY_WALL_T, LAUNDRY_OUTER[1] - LAUNDRY_WALL_T,
                 LAUNDRY_OUTER[2] + LAUNDRY_WALL_T, LAUNDRY_OUTER[3])   # 21.578..24.691 x 28.001..31.058 = 3'-1 3/8" x 3'-0 5/8"
# door D17 in the north face: 2'-6" x 6'-8", centred, hinged on the east jamb, swinging north, shown open
LAUNDRY_DOOR_W = 2.5
LAUNDRY_DOOR_HEAD = 6.67
_LCX = (LAUNDRY_OUTER[0] + LAUNDRY_OUTER[1]) / 2
LAUNDRY_DOOR_X = (_LCX - LAUNDRY_DOOR_W / 2, _LCX + LAUNDRY_DOOR_W / 2)   # 21.8845..24.3845 (the opening in the wall)
LAUNDRY_DOOR_C = LAUNDRY_OUTER[2] + LAUNDRY_WALL_T / 2                    # the door wall's centre line z (27.821)
LAUNDRY_DOOR_HINGE = 'east'
LAUNDRY_DOOR_SWING = 'north'
LAUNDRY_DOOR_OPEN_DEG = 90.0
LAUNDRY_DOOR_LINER = 0.03          # painted jamb liner: this far into the opening (and into the wall) on each side
LAUNDRY_DOOR_LINER_PROUD = 0.035   # the liners and the head trim stand this far off both wall faces
LAUNDRY_HINGE_GAP = 0.01           # between the leaf's hinge edge and the liner (the hinge pins sit on this joint)
LAUNDRY_HINGE_PIN = 0.012          # the pins' axis stands this far off the leaf's outer face
LAUNDRY_LEAF_W = LAUNDRY_DOOR_W - 2 * LAUNDRY_DOOR_LINER - 0.02   # 2.42: 1/8" clear of each liner
LAUNDRY_LEAF_T = 0.115             # 1 3/8" flush slab like the other interior doors
LAUNDRY_LEAF_Y = (0.02, 6.60)
# the garage west wall (x 21.218..21.578) starts at z 31.238 and the kitchen / garage wall at x 21.398: the closet's
# west wall would leave this notch open in the foyer's east face, so it is filled
LAUNDRY_CORNER_INFILL = (21.218, 21.398, 31.058, 31.238)
# stacked front-load pair (washer below, dryer above), centred between the side walls
LAUNDRY_UNIT_W, LAUNDRY_UNIT_D, LAUNDRY_UNIT_H = 2.25, 2.52, 3.25   # 27 x 30 1/4 x 39 in each (bodies)
LAUNDRY_UNIT_BACK_GAP = 0.40       # hoses and the 4 in vent duct between the bodies and the back wall
LAUNDRY_STACK_TRIM = 0.04          # stacking kit between the two bodies
LAUNDRY_LIGHT = (_LCX, LAUNDRY_CLEAR[2] + 0.50)    # (x, z) of the flush ceiling light
# recessed washer outlet box in the back wall (the kitchen / garage wall, 0.36 thick): x0, x1, y0, y1, depth.
# It sits behind the stack's west edge, so its cold valve and hose show in the gap beside the units.
LAUNDRY_HOOKUP_RECESS = (21.70, 22.36, 3.50, 4.10, 0.24)


def laundry_walls():
    """New wall boxes [(name, x0, x1, y0, y1, z0, z1)], floor to the flat ceiling; the opening in the north face is
    LAUNDRY_DOOR_X up to LAUNDRY_DOOR_HEAD."""
    x0, x1, z0, z1 = LAUNDRY_OUTER
    t, top = LAUNDRY_WALL_T, LAUNDRY_CEILING
    d0, d1 = LAUNDRY_DOOR_X
    ix0, ix1, iz0, iz1 = LAUNDRY_CORNER_INFILL
    return [('Laundry closet west wall', x0, x0 + t, 0.0, top, z0, z1),
            ('Laundry closet east wall', x1 - t, x1, 0.0, top, z0, z1),
            ('Laundry closet door wall west return', x0 + t, d0, 0.0, top, z0, z0 + t),
            ('Laundry closet door wall east return', d1, x1 - t, 0.0, top, z0, z0 + t),
            ('Laundry closet door header', d0, d1, LAUNDRY_DOOR_HEAD, top, z0, z0 + t),
            ('Laundry closet corner infill', ix0, ix1, 0.0, top, iz0, iz1)]


def laundry_leaf(open_deg=None):
    """The door leaf at `open_deg` (default LAUNDRY_DOOR_OPEN_DEG). The leaf turns about the hinge pins: closed, its
    outer face is flush with the jamb liners' outer (north) edge and its hinge edge stands LAUNDRY_HINGE_GAP off the
    liner; the pins' axis is on that joint, LAUNDRY_HINGE_PIN proud of the leaf's face, so the knuckles stay in the
    corner between the leaf and the jamb at every angle. Returns the pin axis `pivot` (x, z), unit vectors in plan
    `along` (hinge -> free edge) and `through` (outer face -> inner face), `corner` (x, z) = the leaf's hinge-edge /
    outer-face corner, `rot` (radians about +Y, the SCENE object / ctx.box_c convention), the leaf box as `center`
    (x, y, z) + `size` (width, height, thickness) and its axis-aligned bounds `aabb` (x0, x1, y0, y1, z0, z1)."""
    a = math.radians(LAUNDRY_DOOR_OPEN_DEG if open_deg is None else open_deg)
    east = LAUNDRY_DOOR_HINGE == 'east'
    s = -1.0 if east else 1.0                       # the closed leaf runs from the hinge toward -x (east hinge)
    jamb = LAUNDRY_DOOR_X[1] - LAUNDRY_DOOR_LINER if east else LAUNDRY_DOOR_X[0] + LAUNDRY_DOOR_LINER   # liner face
    px = jamb + s * LAUNDRY_HINGE_GAP / 2
    pz = LAUNDRY_OUTER[2] - LAUNDRY_DOOR_LINER_PROUD - LAUNDRY_HINGE_PIN
    along = (s * math.cos(a), -math.sin(a))
    through = (s * math.sin(a), math.cos(a))
    u0, v0 = LAUNDRY_HINGE_GAP / 2, LAUNDRY_HINGE_PIN     # the leaf's corner, measured from the pin axis
    w, th = LAUNDRY_LEAF_W, LAUNDRY_LEAF_T
    y0, y1 = LAUNDRY_LEAF_Y

    def at(u, v):
        return px + along[0] * (u0 + u) + through[0] * (v0 + v), pz + along[1] * (u0 + u) + through[1] * (v0 + v)
    cx, cz = at(w / 2, th / 2)
    cs = [at(u, v) for u in (0.0, w) for v in (0.0, th)]
    xs, zs = [c[0] for c in cs], [c[1] for c in cs]
    return {'pivot': (px, pz), 'corner': at(0.0, 0.0), 'along': along, 'through': through,
            'rot': math.atan2(-along[1], along[0]), 'center': (cx, (y0 + y1) / 2, cz), 'size': (w, y1 - y0, th),
            'aabb': (min(xs), max(xs), y0, y1, min(zs), max(zs))}


def laundry_units():
    """Body boxes (x0, x1, y0, y1, z0, z1) of the stacked pair; the round doors stand about 0.09 ft proud of z0."""
    cx = (LAUNDRY_CLEAR[0] + LAUNDRY_CLEAR[1]) / 2
    x0, x1 = cx - LAUNDRY_UNIT_W / 2, cx + LAUNDRY_UNIT_W / 2
    z1 = LAUNDRY_CLEAR[3] - LAUNDRY_UNIT_BACK_GAP
    z0 = z1 - LAUNDRY_UNIT_D
    h, tr = LAUNDRY_UNIT_H, LAUNDRY_STACK_TRIM
    return {'washer': (x0, x1, 0.0, h, z0, z1), 'dryer': (x0, x1, h + tr, 2 * h + tr, z0, z1)}
