"""v7 garage (owner's eighth round, 2026-11-24, stage B): the front door unit, the door between the house and the
garage, the garage's side door, the vehicle door's opening, the garage floor with its step, and the water heater.
Pure Python (no bpy), SCENE feet on the architect's sheet SKA002 (x west->east, y up, z rear->street), shared by
bl/garage.py (Blender), bl/zones/exterior_garage.py, bl/zones/hall_entry_garage.py and the web data tools.

Every number is the sheet's (audit: ska002_geometry.json DR16..DR19, FX11, ST1; A1.3 for the heights), written as
the distance from the wall face of its own room in relayout (R.X_GAR_W, R.Z_GAR_N, ...), so it keeps its place
when a wall line moves:

  * FLOOR_Y: the garage floor is 11 in below the house floor (A1.3 "G.F.F."), with a 1'-0" x 3'-8" step at the
    house door (ST1) whose top is half way: two risers of 5 1/2 in.
  * HOUSE_DOOR (DR17): 3'-4" between the wall's ends, 3'-0" between its 2 in frames, hinged on the NORTH jamb,
    swinging east into the garage, shown open at 90 degrees as drawn.
  * SIDE_DOOR (DR18): east wall, 2'-8" between the wall's ends, 2'-4" between the frames, hinged on the south jamb,
    swinging west into the garage, closed. It stands on the garage floor: head 6'-8" above it (A1.3: 5'-9" above
    the house floor).
  * VEHICLE_DOOR (DR19): 15'-0" between the wall's ends, 14'-10" between the two 1 in jamb boards (the door), 7'-0"
    high above the garage floor (A1.3).
  * FRONT_DOOR (DR16): a 3'-0" door centred on the foyer with a glazed sidelight each side. The sheet's unit is
    5'-5 1/2" in a 7'-0" foyer; the foyer is 5'-9" (owner's wall alignment, relayout.FOYER_WALL), so the unit takes
    the foyer less 3 in of wall each side (5'-3") and keeps the sheet's members (1 in outer jambs, 2 in posts beside
    the door): the sidelights are 10 1/2 in between the frames (sheet: 11 3/4 in).
  * WATER_HEATER (FX11): a 1'-8" tank in the garage's north-east corner.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import relayout as R  # noqa: E402  (pure Python: the sheet's wall faces)

IN = 1.0 / 12.0
GX0, GX1, GZ0, GZ1 = R.ROOMS['garage']          # 21.725, 39.308, 31.475, 52.392
FX0, FX1, FZ0, FZ1 = R.ROOMS['foyer']           # 15.558, 21.308, 28.892, 47.392

# ---- levels (house floor = 0)
FLOOR_Y = -11 * IN                               # garage finished floor and the ground at the front: -0.917
CEILING_Y = 8.0                                  # the garage's ceiling stays at the house's: 8'-11" above its floor
STEP_Y = FLOOR_Y / 2                             # top of the step at the house door: -0.458 (two risers of 5 1/2 in)
SLAB_T = 4 * IN                                  # the slab as built (4 in), on the lowered foundation

# ---- every hinged door here
DOOR_HEAD = 6.67                                 # the wall opening's head above the floor the door stands on (6'-8")
FRAME = 2 * IN                                   # the sheet's door frame: 2 in between the wall's end and the leaf
FRAME_PROUD = 0.035                              # frames stand this far off both wall faces (the house's casing)
HEAD_TRIM = (0.083, 0.06)                        # head member: this far below / above the opening's head
LEAF_GAP = 0.125 * IN                            # between the leaf and its frame, each side
LEAF_T = 1.75 * IN                               # solid 1 3/4 in leaves (exterior / garage doors)
HINGE_PIN = 0.012                                # pin axis proud of the leaf's swing-side face
HINGE_Y = (0.75, 3.30, 5.85)                     # hinge centres above the leaf's floor
LEVER_Y = 3.0                                    # lever height above the leaf's floor
LEVER_INSET = 0.23                               # lever axis from the leaf's free edge (2 3/4 in backset)


def _door(name, axis, wall, ro, hinge, swing, floor_y, open_deg, frame=FRAME, leaf_y=(0.065, DOOR_HEAD - 0.095)):
    c0, c1 = ro[0] + frame, ro[1] - frame
    return {'name': name, 'axis': axis, 'wall': wall, 'ro': ro, 'clear': (c0, c1), 'hinge': hinge, 'swing': swing,
            'floor_y': floor_y, 'head': floor_y + DOOR_HEAD, 'open_deg': open_deg, 'frame': frame,
            'leaf_w': c1 - c0 - 2 * LEAF_GAP, 'leaf_t': LEAF_T, 'leaf_y': (floor_y + leaf_y[0], floor_y + leaf_y[1]),
            'c': (wall[0] + wall[1]) / 2}


# DR17 house / garage door: in the garage's west wall (= the foyer's east wall), which runs along z
HOUSE_DOOR = _door('House / garage door', 'z', (R.X_FOYER_E, R.X_GAR_W), (GZ0 + 4.6875, GZ0 + 8.0208),
                   hinge='lo', swing=+1, floor_y=0.0, open_deg=90.0)             # z 36.162..39.496, clear 36.329..39.329
# DR18 garage side door: in the east wall, on the garage floor
SIDE_DOOR = _door('Garage side door', 'z', (R.X_LIV_E, R.XE_OUT), (GZ0 + 4.1667, GZ0 + 6.8333),
                  hinge='hi', swing=-1, floor_y=FLOOR_Y, open_deg=0.0)           # z 35.642..38.308, clear 35.808..38.142
# DR16 front door: in the front door wall, which runs along x; the unit is the foyer less FRONT_DOOR_SIDE each side
FRONT_DOOR_SIDE = 3 * IN                         # wall left on each side of the unit
FRONT_DOOR_JAMB = 1 * IN                         # the unit's outer jambs (sheet: 1 in)
FRONT_DOOR_UNIT = (FX0 + FRONT_DOOR_SIDE, FX1 - FRONT_DOOR_SIDE)                 # x 15.808..21.058 (5'-3")
_FC = (FX0 + FX1) / 2                            # 18.433
FRONT_DOOR = _door('Front door', 'x', (R.Z_FOYER_S, R.Z_PORCH_N), (_FC - 1.5 - FRAME, _FC + 1.5 + FRAME),
                   hinge='hi', swing=-1, floor_y=0.0, open_deg=105.0)            # posts 16.767..16.933 | 19.933..20.100
FRONT_DOOR_SIDELIGHTS = [(FRONT_DOOR_UNIT[0] + FRONT_DOOR_JAMB, FRONT_DOOR['ro'][0]),      # x 15.892..16.767
                         (FRONT_DOOR['ro'][1], FRONT_DOOR_UNIT[1] - FRONT_DOOR_JAMB)]      # x 20.100..20.975
FRONT_DOOR_SIDELIGHT_RAIL_Y = 0.5                # bottom rail of each sidelight: the glass starts here
FRONT_DOOR_SILL_Y = 0.055                        # top of the oak sill that runs under the whole unit
# the entry window above the door (W17) keeps its place: the wall's ends as the shell builds them (the old door's)
FRONT_DOOR_OLD_X = (R.X_FRONT(15.86), R.X_FRONT(18.86))                          # 16.933..19.933
FRONT_DOOR_BAND_Y = (DOOR_HEAD, 7.5, 8.0)        # the wall over the unit: to the window's sill, beside it to 8 ft

# DR19 vehicle door: in the garage's front wall
VEHICLE_RO_X = (GX0 + 1.25, GX0 + 16.25)         # 22.975..37.975: 15'-0" between the wall's ends
VEHICLE_JAMB = 1 * IN                            # jamb boards
VEHICLE_DOOR_X = (VEHICLE_RO_X[0] + VEHICLE_JAMB, VEHICLE_RO_X[1] - VEHICLE_JAMB)   # 23.058..37.892: the 14'-10" door
VEHICLE_HEIGHT = 7.0                             # opening height above the garage floor (A1.3)
VEHICLE_HEAD_Y = FLOOR_Y + VEHICLE_HEIGHT        # 6.083 above the house floor
VEHICLE_WALL_Z = (R.Z_GAR_S, R.Z_GAR_OUT)        # 52.392..52.808

# ST1 step at the house door, on the garage side
STEP = (GX0, GX0 + 1.0, GZ0 + 4.508, GZ0 + 4.508 + 3.0 + 8 * IN)                 # x 21.725..22.725, z 35.983..39.650

# FX11 water heater: centre and diameter; a 50 gallon tank on an 18 in stand
WATER_HEATER_C = (GX1 - 1.286, GZ0 + 1.438)      # 38.022, 32.913
WATER_HEATER_D = 20 * IN                         # 1'-8"
WATER_HEATER_STAND = 1.5                         # stand height (the burner 18 in above a garage floor)
WATER_HEATER_TANK = 4.75                         # tank height: its top 6'-3" above the garage floor
WATER_HEATER_STAND_HALF = 0.95                   # the stand's half side
# the north cabinet run stops short of the heater: its east end (plan x), 0.55 ft clear of the stand
CABINET_RUN_END_X = WATER_HEATER_C[0] - WATER_HEATER_STAND_HALF - 0.55            # 36.522

# ---- the garage's own walls below the house floor: the inside finish runs down to the slab on a base this thick
BASE_T = 0.2
# what must be clear of other pieces (ground, foundation plinth) for the lower floor and the two doors to show:
# (x0, x1, y0, y1, z0, z1); the vehicle opening's street end is set by the driveway (bl/garage.py)
PIT_MARGIN = 0.1                                 # the pit reaches this far into the walls, behind the bases


def leaf(d, open_deg=None):
    """The leaf of a hinged door `d` (HOUSE_DOOR, SIDE_DOOR, FRONT_DOOR) at `open_deg` (default d['open_deg'];
    0 = closed, 90 = square to its wall). The leaf turns about its hinge pins, which stand on the joint between its
    hinge edge and the frame, HINGE_PIN proud of its swing-side face; closed, that face is flush with the frame's
    swing-side edge. Returns a dict like revision_spec.bath_door_leaf(): `pivot` (x, z), unit vectors on the plan
    `along` (hinge -> free edge) and `through` (swing-side face -> other face), `corner` (the hinge-edge /
    swing-face corner), `rot` (radians about +Y, ctx.box_c), `center`, `size` (width, height, thickness), `aabb`."""
    a = math.radians(d['open_deg'] if open_deg is None else open_deg)
    c0, c1 = d['clear']
    w0, w1 = d['wall']
    lo = d['hinge'] == 'lo'
    h = (c0 + LEAF_GAP / 2) if lo else (c1 - LEAF_GAP / 2)            # pin, along the wall
    n = (w1 + FRAME_PROUD + HINGE_PIN) if d['swing'] > 0 else (w0 - FRAME_PROUD - HINGE_PIN)   # pin, across it
    sa, sn = (1.0 if lo else -1.0), float(d['swing'])
    if d['axis'] == 'z':                                             # wall along z: (x, z) = (across, along)
        a0, s = (0.0, sa), (sn, 0.0)
        px, pz = n, h
    else:                                                            # wall along x
        a0, s = (sa, 0.0), (0.0, sn)
        px, pz = h, n
    along = (a0[0] * math.cos(a) + s[0] * math.sin(a), a0[1] * math.cos(a) + s[1] * math.sin(a))
    through = (-s[0] * math.cos(a) + a0[0] * math.sin(a), -s[1] * math.cos(a) + a0[1] * math.sin(a))
    u0, v0 = LEAF_GAP / 2, HINGE_PIN
    w, th = d['leaf_w'], d['leaf_t']
    y0, y1 = d['leaf_y']

    def at(u, v):
        return px + along[0] * (u0 + u) + through[0] * (v0 + v), pz + along[1] * (u0 + u) + through[1] * (v0 + v)
    cx, cz = at(w / 2, th / 2)
    cs = [at(u, v) for u in (0.0, w) for v in (0.0, th)]
    xs, zs = [c[0] for c in cs], [c[1] for c in cs]
    return {'name': d['name'] + ' leaf', 'pivot': (px, pz), 'corner': at(0.0, 0.0), 'along': along, 'through': through,
            'rot': math.atan2(-along[1], along[0]), 'center': (cx, (y0 + y1) / 2, cz), 'size': (w, y1 - y0, th),
            'aabb': (min(xs), max(xs), y0, y1, min(zs), max(zs))}


if __name__ == '__main__':
    for d in (FRONT_DOOR, HOUSE_DOOR, SIDE_DOOR):
        lf = leaf(d)
        print('%-20s wall %s  ro %.3f..%.3f  clear %.3f..%.3f  head %.3f  leaf %.3f (%.2f in)  aabb %s' % (
            d['name'], tuple(round(v, 3) for v in d['wall']), *d['ro'], *d['clear'], d['head'], d['leaf_w'],
            d['leaf_w'] * 12, [round(v, 3) for v in lf['aabb']]))
    print('front door unit', [round(v, 3) for v in FRONT_DOOR_UNIT], 'sidelights',
          [[round(v, 3) for v in s] for s in FRONT_DOOR_SIDELIGHTS])
    print('vehicle ro', [round(v, 3) for v in VEHICLE_RO_X], 'door', [round(v, 3) for v in VEHICLE_DOOR_X],
          'head', round(VEHICLE_HEAD_Y, 3))
    print('step', [round(v, 3) for v in STEP], 'top', round(STEP_Y, 3), 'floor', round(FLOOR_Y, 3))
    print('water heater', [round(v, 3) for v in WATER_HEATER_C], 'cabinet run ends', round(CABINET_RUN_END_X, 3))
