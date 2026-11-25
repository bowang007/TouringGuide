"""Old concept plan -> architect's plan (sizes/sizes.pdf, sheet SKA002 "(N) FLOOR PLAN", Option A).

The tour model was drawn from an earlier concept with the same rooms in the same arrangement as the
architect's plan but different sizes. This module maps every old SCENE coordinate (feet; x west->east,
z rear(north)->street(south)) onto the architect's dimensions, region by region, with 1-D piecewise
linear maps whose breakpoints are wall faces. Walls keep their thickness (exterior 0.45 ft, interior
0.36 ft), rooms take the PDF's clear sizes:

  rear row      primary 11'-1" x 12'-3", bedroom 2 (PDF "Bedroom #1") 10'-6" x 12'-3", living 16'-8" wide
  left column   walk-in closet 8'-0", primary bath 9'-6" x 7'-2", office (tour "Bedroom 4") 8'-0",
                front bath 5'-0" (8'-3" wide) + two closets, front bedroom (tour "Bedroom 3",
                PDF "Bedroom #2") 11'-0" deep
  middle        shared bath 5'-0" x 7'-2", foyer 18'-6" long, covered porch 7'-4" deep
  owner's change (2026-11-19): the foyer-side wall of the office and the front bedroom lines up with
                the shared bath's east wall (x 15.085..15.445) instead of the PDF's 1'-2 3/4" jog, so
                both rooms (and the closets between them) are 1'-2 3/4" wider and the foyer and porch
                5'-9 1/4" instead of 7'-0". The front door keeps its 3'-0" and stays centred.
  right         living + kitchen & dining 30'-10" deep, garage 17'-7" x 20'-11"

Outer size: 39.87 ft wide (the site plan's 52 ft lot less 5'-7" + 6'-6" side yards).

remap_xz(x, z) maps a point; remap_box(...) maps an axis-aligned box (its two corners, by the region
of its centre); remap_mesh(...) maps mesh vertices one by one (a vertex always maps the same way,
so shared edges stay closed).
"""
import bisect
import re

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


# exterior wall: centred on x = 0 / z = 0, 0.45 thick; interior partitions 0.36
X_REAR = _pl([(-0.225, -0.225), (0.225, 0.225), (11.892, 11.308), (12.252, 11.668), (17.558, 17.058),
              (17.918, 17.418), (22.918, 22.168), (23.278, 22.528), (40.612, 39.195), (41.062, 39.645)])
X_PRIMARY = _pl([(-0.225, -0.225), (0.225, 0.225), (11.892, 11.308), (12.252, 11.668)])
X_BATHS = _pl([(-0.225, -0.225), (0.225, 0.225), (10.392, 9.725), (10.752, 10.085), (16.002, 15.085),
               (16.362, 15.445), (23.278, 22.528), (40.612, 39.195), (41.062, 39.645)])
X_HALL = _pl([(-0.225, -0.225), (0.225, 0.225), (11.892, 11.308), (12.252, 11.668), (16.002, 15.085),
              (16.362, 15.445), (23.278, 22.528), (40.612, 39.195), (41.062, 39.645)])
# the foyer-side wall of the office / front bedroom, aligned with the shared bath's east wall (X_BATHS)
FOYER_WALL = (15.085, 15.445)
X_FRONT_LEFT = _pl([(-0.225, -0.225), (0.225, 0.225), (7.725, 8.475), (8.085, 8.835), (13.892, FOYER_WALL[0]),
                    (14.252, FOYER_WALL[1]), (14.342, FOYER_WALL[1] + 0.09)])
X_FRONT_ROOMS = _pl([(-0.225, -0.225), (0.225, 0.225), (13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]),
                     (14.342, FOYER_WALL[1] + 0.09)])
# foyer: the 3'-0" front door (old jambs 15.86 / 18.86) keeps its width, centred between the walls
_DOOR_C = (FOYER_WALL[1] + 21.218) / 2
X_FRONT = _pl([(13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]), (15.86, _DOOR_C - 1.5), (18.86, _DOOR_C + 1.5),
               (20.465, 21.218), (20.915, 21.578), (40.612, 39.195), (41.062, 39.645)])

# garage: the 14'-10" vehicle door keeps its width, centred in the narrower garage
_GC = (21.578 + 39.195) / 2
X_GARAGE = _pl([(13.892, FOYER_WALL[0]), (14.252, FOYER_WALL[1]), (20.465, 21.218), (20.915, 21.578), (23.40155, _GC - 7.4289),
                (38.25925, _GC + 7.4289), (40.612, 39.195), (41.062, 39.645)])

# garage north wall: the fitted cabinet run spanned the old garage wall to wall (x 21.1 .. 40.50); the plan's
# garage is 2'-1" narrower inside, so the run is scaled to fit (cabinets ~10% narrower), wall faces as X_GARAGE
X_GARAGE_RUN = _pl([(20.465, 21.218), (20.915, 21.578), (21.1, 21.763), (40.50, 39.085), (40.612, 39.195),
                    (41.062, 39.645)])

Z_LEFT = _pl([(-0.225, -0.225), (0.225, 0.225), (15.142, 12.475), (15.502, 12.835), (20.918, 20.835),
              (21.278, 21.195), (29.278, 28.362), (29.638, 28.722), (37.472, 36.722), (37.832, 37.082),
              (39.832, 39.402), (40.192, 39.762), (42.832, 42.082), (43.192, 42.442), (53.832, 53.442),
              (54.282, 53.892)])
Z_MID = _pl([(-0.225, -0.225), (0.225, 0.225), (12.725, 12.475), (13.085, 12.835), (15.142, 14.75),
             (15.502, 15.11), (20.918, 20.835), (21.278, 21.195), (29.278, 28.362), (29.638, 28.722),
             (46.722, 47.222), (47.082, 47.582), (51.30, 54.915)])   # foyer 18'-6", porch 7'-4"
Z_RIGHT = _pl([(-0.225, -0.225), (0.225, 0.225), (31.411, 31.058), (31.771, 31.418), (50.832, 52.335),
               (51.282, 52.785)])

# Regions (old coordinates): (x0, x1, z0, z1, X map, Z map, name); the first match wins.
INF = 1e9
REGIONS = [
    (-INF, 12.26, -INF, 21.098, X_PRIMARY, Z_LEFT, 'primary suite'),   # incl. its east wall
    (-INF, 10.572, 21.098, 29.458, X_BATHS, Z_LEFT, 'primary bath'),
    (-INF, 14.65, 37.45, 43.2, X_FRONT_LEFT, Z_LEFT, 'front bath + closets'),
    (-INF, 14.65, 29.458, INF, X_FRONT_ROOMS, Z_LEFT, 'office + front bedroom'),   # incl. the porch wall + gable overhang
    (10.572, 16.182, 21.098, 29.458, X_BATHS, Z_MID, 'shared bath'),
    (12.26, 23.098, -INF, 15.322, X_REAR, Z_MID, 'bedroom 2'),
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
_BAND = [(v, Z_MID(v)) for v in (47.082, ROOF_LINE, 47.562)]   # gable cheek .. bargeboards: one flat front
Z_LEFT_ROOF = _pl(Z_LEFT.pairs + _BAND)
Z_RIGHT_ROOF = _pl(Z_RIGHT.pairs + _BAND)
_ROOF_Z = {'office + front bedroom': Z_LEFT_ROOF, 'front bath + closets': Z_LEFT_ROOF, 'garage': Z_RIGHT_ROOF}
# The bedroom-wing gable ridge (old x 7.036) runs from the main roof over the primary bath to the front
# gable of bedroom 3. The wing is wider now, so over the primary bath the ridge follows the office /
# bedroom-3 map and stays one straight line (the front gable stays centred on bedroom 3).
WING_RIDGE = 7.036
X_BATHS_ROOF = _pl(X_BATHS.pairs + [(WING_RIDGE, X_FRONT_ROOMS(WING_RIDGE))])
X_PRIMARY_RIDGE = _pl(X_PRIMARY.pairs + [(WING_RIDGE, X_FRONT_ROOMS(WING_RIDGE))])   # its end at the main roof
_ROOF_X = {'primary bath': X_BATHS_ROOF}


# Pieces whose centre falls on the wrong side of a region edge but belong to the room on the other side.
REGION_BY_NAME = [(re.compile(r'entry vault knee wall', re.I), 'foyer + porch'),
                  # the office's north wall east of the shared bath wall's centre line used to continue into
                  # the old foyer; it ends at the shared bath's east wall like the bath above it
                  (re.compile(r'Old front wall below shared bath', re.I), 'shared bath')]


def pinned_region(name):
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
    r = pinned_region(name)
    if r:
        return min(r[4](x0), r[4](x1)), max(r[4](x0), r[4](x1)), min(r[5](z0), r[5](z1)), max(r[5](z0), r[5](z1))
    at = ((x0 + x1) / 2, (z0 + z1) / 2)
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


# Old -> new outer faces used by the site / exterior modules
OUTER = dict(west=-0.225, east_old=41.062, east=39.645, rear=-0.225,
             front_bed_old=54.282, front_bed=53.892, garage_front_old=51.282, garage_front=52.785,
             porch_front=54.915, front_wall=47.582, foyer_wall=FOYER_WALL[1])

if __name__ == '__main__':
    for name, (x, z) in {'primary SE': (11.892, 15.142), 'bed2 NE': (22.918, 0.225),
                         'living E': (40.612, 10), 'garage front': (30, 51.282),
                         'bed3 front': (5, 54.282), 'foyer front': (17, 46.722),
                         'office N': (5, 29.638)}.items():
        print(f'{name:14s} {x:7.3f},{z:7.3f} -> {remap_xz(x, z)}')
