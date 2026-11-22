"""Dining set of the kitchen / open area.

Default (kitchen_dining.DINING_RECT): build_rect() puts a warm white-oak farmhouse table with turned
legs in line with the island at its WEST end (the shared-bathroom / hall side, owner's correction of 2026-11-20),
six oak chairs with cream pin-striped linen seats and backs on its two long sides and a brass lantern
over it (owner's vintage-kitchen references). The floor between the island and the family room, where
the table stood before, is open.

build() is the older alternative (off): a 42in round walnut pedestal table beside window W07 with
four boucle barrel chairs and a double-ring LED chandelier.
"""
import math
import sys

from ..common import RENDER_DIR
from .kitchen_dining_geo import Geo, principled, srgb

if RENDER_DIR not in sys.path:
    sys.path.insert(0, RENDER_DIR)
import relayout as R  # noqa: E402  (the concept -> architect's plan maps that bl/warp.py applies to this zone)

TABLE_C = (35.55, 17.45)      # (x, z) centre (NE chair clears the living ledge at x>=38.25, z<=16.9)
TABLE_R = 1.75                # 42in round
TABLE_TOP = 2.5               # 30in
CHAIR_R = 2.20                # chair centre distance from table centre
CHAIR_OUT = 0.93              # chair outer radius (barrel)
CHAIR_ANGLES = (45, 135, 225, 315)   # degrees, measured in plan from +x toward +z
CEIL = 8.0
RUG_R = 2.9                   # 5.8 ft round wool rug under the set (stays south of z=14.5)
RUG_T = 0.04


def footprint():
    """Plan circles (x, z, r) of the dining set, for clearance checks."""
    cx, cz = TABLE_C
    out = [(cx, cz, TABLE_R)]
    for a in CHAIR_ANGLES:
        r = math.radians(a)
        out.append((cx + CHAIR_R * math.cos(r), cz + CHAIR_R * math.sin(r), CHAIR_OUT))
    return out


def build(ctx, g: Geo):
    col = g.sub('kd dining')
    lights = g.sub('kd_lights')
    cx, cz = TABLE_C
    # ---------------------------------------------------------------- table
    # walnut top: 1.25in slab with a softened, slightly undercut edge
    top_prof = [(0.0, 0.0), (TABLE_R - 0.12, 0.0), (TABLE_R - 0.02, 0.05), (TABLE_R, 0.075),
                (TABLE_R, 0.095), (TABLE_R - 0.012, 0.104), (0.0, 0.104)]
    g.lathe('kd dining table top', top_prof, cx, cz, 'walnut_slab', 128, col, y_base=TABLE_TOP - 0.104, sharp_deg=60)
    # round cream-grey wool rug (soft bevelled edge)
    rug = [(0.0, 0.0), (RUG_R - 0.03, 0.0), (RUG_R, 0.012), (RUG_R, RUG_T - 0.012), (RUG_R - 0.03, RUG_T), (0.0, RUG_T)]
    g.lathe('kd dining rug', rug, cx, cz, 'rug_wool_grey', 160, col, y_base=0.001, sharp_deg=80)
    # sculptural pedestal: flared foot, waisted column, flared head (all walnut)
    ped = [(0.0, RUG_T), (0.92, RUG_T), (0.93, RUG_T + 0.02), (0.90, RUG_T + 0.065), (0.62, 0.24), (0.42, 0.55), (0.34, 1.0),
           (0.34, 1.4), (0.40, 1.85), (0.55, 2.2), (0.62, 2.36), (0.62, TABLE_TOP - 0.104), (0.0, TABLE_TOP - 0.104)]
    g.lathe('kd dining pedestal', ped, cx, cz, 'walnut_slab', 96, col, sharp_deg=55)

    # --------------------------------------------------------------- chairs
    chair = _chair(g, col)
    for i, a in enumerate(CHAIR_ANGLES):
        r = math.radians(a)
        x, z = cx + CHAIR_R * math.cos(r), cz + CHAIR_R * math.sin(r)
        # chair local front faces local +z; rotate so it faces the table centre
        face = math.atan2(cx - x, cz - z)          # plan heading (x over z) toward the table
        rot = face
        for p in chair:
            if i == 0:
                q = p
            else:
                q = p.copy()
                g._link(q, col)
            q.name = f'{p.name.split(" #")[0]} #{i}'
            q.location = (x * 0.3048, -z * 0.3048, RUG_T * 0.3048)
            q.rotation_euler = (0, 0, rot)

    # ----------------------------------------------------------- chandelier
    _chandelier(g, cx, cz, col, lights)
    return {'table': 1, 'chairs': len(CHAIR_ANGLES), 'chandelier': 1}


def _chair(g, col):
    """Curved bouclé barrel dining chair built at the local origin, front toward local +z.
    One continuous outer shell (floor to back top, sloping into the arms) wraps an inner skirt
    and a loose seat cushion. Returns the parts (each with a custom 'y0' = base height)."""
    parts = []
    seat_h = 1.52                      # 18.2in seat height
    R = 0.93
    # inner skirt (visible only between the arm ends at the front)
    body = [(0.0, 0.05), (0.62, 0.05), (0.70, 0.10), (0.76, 0.30), (0.78, 1.30), (0.74, 1.38), (0.0, 1.38)]
    ob = g.lathe('kd dining chair body', body, 0, 0, 'fabric_boucle', 64, col)
    g.subsurf(ob, 1)
    parts.append(ob)
    # recessed black glide ring: reads as a shadow gap under the upholstery
    parts.append(g.lathe('kd dining chair plinth', [(0.0, 0.0), (0.55, 0.0), (0.55, 0.05), (0.0, 0.05)], 0, 0,
                         'paint_black', 48, col))
    # seat cushion
    cush = [(0.0, 1.34), (0.70, 1.34), (0.76, 1.37), (0.78, 1.44), (0.76, seat_h - 0.01), (0.68, seat_h + 0.02), (0.0, seat_h + 0.03)]
    parts.append(g.lathe('kd dining chair cushion', cush, 0, 0, 'fabric_boucle', 64, col))

    # continuous outer shell: 2.5 ft at the back, ~26in arms at the sides, sloping to the front
    def ytop(a):
        return 1.70 + 0.80 * (0.5 + 0.5 * math.cos(a)) ** 0.85
    shell = g.arc_wall('kd dining chair shell', R - 0.22, R, -2.25, 2.25, 0.05, ytop, 'fabric_boucle', 64, col)
    g.bevel_mod(shell, 0.09, 4)
    g.subsurf(shell, 2)
    parts.append(shell)
    for p in parts:
        p['y0'] = RUG_T
    return parts


def _chandelier(g, cx, cz, col, lights):
    """Double-ring LED chandelier: two slim matte-black rings with opal diffusers on their
    undersides, on fine steel cables from a round ceiling canopy."""
    from ..lighting import emitter
    led = emitter('kd_ring_led', 3000, 40.0)
    rings = ((1.22, 5.62), (0.80, 5.92))         # (radius ft, bottom height)
    for k, (R, y) in enumerate(rings):
        g.ring_rect(f'chandelier ring {k}', cx, cz, R, 0.09, y, y + 0.075, ['black_metal', led], 192, col)
        for j in range(3):
            a = 2 * math.pi * j / 3 + (0.5 if k else 0.0)
            x, z = cx + R * math.cos(a), cz + R * math.sin(a)
            g.cyl_axis(f'chandelier cable {k}{j}', (x, y + 0.075, z), (cx + 0.15 * math.cos(a), CEIL - 0.04, cz + 0.15 * math.sin(a)),
                       0.005, 'chrome', 6, col)
    g.cyl('chandelier canopy', cx, CEIL - 0.05, CEIL - 0.001, cz, 0.24, 'black_metal', 48, col, bevel=0.01)
    # light emitted by the rings: soft point lights at the ring centres + small area downlight
    g.point_light('chandelier glow 0', cx, 5.66, cz, 22.0, 3000, 1.0, lights)
    g.point_light('chandelier glow 1', cx, 5.96, cz, 14.0, 3000, 0.7, lights)


# --------------------------------------------------------- rectangular set at the island's west end
# Owner's correction of 2026-11-20: the table stood north of the island, between the island and the family
# room, and crowded it. It now continues the island's WEST end (the shared-bathroom / hall side), long axis
# east-west on the island's centre line, three chairs on each long side and none at the ends (the west end
# faces the hall, the east end is the island). No rug: the set stands on the oak floor like the island, so
# nothing runs into the hall or the kitchen aisle. The floor north of the island stays open.
#
# The set is loose furniture: bl/warp.py moves the whole cluster (table, chairs, lantern, centrepiece) by the
# shift of its plan centre and keeps its size. The plan numbers are therefore given on the ARCHITECT'S plan
# and the cluster centre is carried back to the concept plan with the inverse of the kitchen's maps
# (relayout.X_HALL / Z_RIGHT, region 'kitchen + dining'). Built (new-plan feet): island worktop x 27.453..33.222,
# z 21.754..24.720; table x 21.433..27.433, z 21.862..24.612; chairs x 21.838..27.028, their backs at z 20.80
# (north) and 25.67 (south); pantry-wall fronts z 28.882 (3.21 ft south of the chair backs; refrigerator doors
# 3.01, its handles 2.81, oven handle 3.01); hall line x 21.2 (0.23 ft west of the table's end).
RECT_LEN = 6.0                # 72in: three chairs a side between the legs
RECT_W = 2.75                 # 33in, a little narrower than the island's worktop (2.97 ft built)
RECT_TOP = 2.5                # 30in
RECT_GAP = 0.02               # between the table's east end and the island worktop's west edge (built feet)
RECT_CHAIR_OUT = 0.20         # chair centre beyond the table's long edge: seats pushed well in, which keeps
                              # 3 ft and more between the south chairs' backs and the oven handles
RECT_CHAIR_DX = 1.82          # chair centres along the table: 0 and +- this (chairs are 1.55 wide)
RECT_CHAIR_BACK = 0.86        # the raked back's top rail behind the chair centre
RECT_LANTERN = 2.80           # lantern's underside above the table top (34in: standing in the hall one
                              # looks along the table under it; it was 2.55 north of the island)


def _concept(f, v):
    """Concept coordinate that the piecewise-linear relayout map `f` carries to the new-plan value v."""
    ps = f.pairs
    if v <= ps[0][1]:
        return ps[0][0] + (v - ps[0][1])
    if v >= ps[-1][1]:
        return ps[-1][0] + (v - ps[-1][1])
    for (a0, b0), (a1, b1) in zip(ps, ps[1:]):
        if b0 <= v <= b1:
            return a0 + (v - b0) / (b1 - b0) * (a1 - a0)


def _rect_centre():
    """Concept (x, z) of the table's centre: its east end RECT_GAP short of the island worktop's west edge
    on the built plan, its long axis on the island's centre line."""
    from . import kitchen_dining_kitchen as K
    ix0, _, iz0, iz1 = K.ISLAND
    east_new = R.X_HALL(ix0) - RECT_GAP
    return _concept(R.X_HALL, east_new - RECT_LEN / 2), (iz0 + iz1) / 2


RECT_CX, RECT_CZ = _rect_centre()


def rect_seats():
    """Concept (x, z, rot) of the six chairs: three north of the table facing south, three south facing north."""
    out = []
    for sz, rot in ((-1, 0.0), (1, math.pi)):          # chair front is local +z: rot 0 faces south
        for dx in (-RECT_CHAIR_DX, 0.0, RECT_CHAIR_DX):
            out.append((RECT_CX + dx, RECT_CZ + sz * (RECT_W / 2 + RECT_CHAIR_OUT), rot))
    return out


def rect_footprint():
    """Concept (x0, x1, z0, z1) of the table plus chairs (the cluster bl/warp.py moves as one)."""
    half = RECT_W / 2 + RECT_CHAIR_OUT + RECT_CHAIR_BACK
    return RECT_CX - RECT_LEN / 2, RECT_CX + RECT_LEN / 2, RECT_CZ - half, RECT_CZ + half


def rect_plan():
    """The set on the built (architect's) plan, new-plan feet: what the build log and the notes report."""
    x0, x1, z0, z1 = rect_footprint()
    dx = R.X_HALL(RECT_CX) - RECT_CX
    dz = R.Z_RIGHT(RECT_CZ) - RECT_CZ
    r = lambda v: round(v, 3)                                            # noqa: E731
    return {'table_x': [r(x0 + dx), r(x1 + dx)],
            'table_z': [r(RECT_CZ - RECT_W / 2 + dz), r(RECT_CZ + RECT_W / 2 + dz)],
            'chair_backs_z': [r(z0 + dz), r(z1 + dz)],
            'chairs_x': [r(RECT_CX - RECT_CHAIR_DX - 0.775 + dx), r(RECT_CX + RECT_CHAIR_DX + 0.775 + dx)],
            'lantern_xz': [r(RECT_CX + dx), r(RECT_CZ + dz)],
            'lantern_y': [RECT_TOP + RECT_LANTERN, CEIL]}


def build_rect(ctx, g: Geo):
    """Warm white-oak farmhouse table (6'-0" x 2'-9", turned legs, apron) continuing the island's west end,
    six oak chairs with cream pin-striped upholstery and a brass lantern over the middle of the table
    (vintage restyle; owner's 'kitchen cloest style' reference)."""
    from . import kitchen_dining_lights as KL
    from . import kitchen_dining_mats as KM
    col = g.sub('kd dining')
    lights = g.sub('kd_lights')
    oak = KM.oak_island()
    cx, cz = RECT_CX, RECT_CZ
    x0, x1 = cx - RECT_LEN / 2, cx + RECT_LEN / 2
    z0, z1 = cz - RECT_W / 2, cz + RECT_W / 2
    # 1.5in oak top with an eased edge, grain along the table (east-west: the wood maps' default)
    g.box('kd dining table top', x0, x1, RECT_TOP - 0.125, RECT_TOP, z0, z1, oak, 0.025, coll=col)
    # apron (inset 2in) and four turned legs standing on the floor
    ins = 0.17
    ay0 = RECT_TOP - 0.125 - 0.33
    for (ax0, ax1, az0, az1) in ((x0 + ins, x0 + ins + 0.07, z0 + ins, z1 - ins), (x1 - ins - 0.07, x1 - ins, z0 + ins, z1 - ins),
                                 (x0 + ins, x1 - ins, z0 + ins, z0 + ins + 0.07), (x0 + ins, x1 - ins, z1 - ins - 0.07, z1 - ins)):
        a = g.box('kd dining table apron', ax0, ax1, ay0, RECT_TOP - 0.125, az0, az1, oak, 0.006, coll=col)
        if az1 - az0 > ax1 - ax0:
            a['tg_grain'] = 1
    leg = [(0.0, 0.0), (0.085, 0.0), (0.095, 0.03), (0.08, 0.08), (0.075, 0.25), (0.11, 0.33),
           (0.075, 0.43), (0.08, 0.6), (0.12, 0.85), (0.125, 0.98), (0.09, 1.12), (0.07, 1.2), (0.085, 1.28),
           (0.12, 1.36), (0.12, 1.4), (0.105, 1.45), (0.13, 1.5), (0.13, ay0 - 0.0), (0.0, ay0)]
    for lx in (x0 + ins + 0.035, x1 - ins - 0.035):
        for lz in (z0 + ins + 0.035, z1 - ins - 0.035):
            g.lathe('kd dining table leg', leg, lx, lz, oak, 40, col, sharp_deg=55)
            g.box('kd dining table leg block', lx - 0.13, lx + 0.13, ay0, RECT_TOP - 0.125, lz - 0.13, lz + 0.13, oak, 0.008,
                  coll=col)
    # chairs: three along each long side, facing the table, on the floor
    parts = _oak_chair(g, col, oak, KM.fabric_stripe(), y0=0.0)
    seats = rect_seats()
    for i, (x, z, rot) in enumerate(seats):
        for p in parts:
            q = p if i == 0 else p.copy()
            if i:
                g._link(q, col)
            q.name = f'{p.name.split(" #")[0]} #{i}'
            q.location = (x * 0.3048, -z * 0.3048, 0.0)
            q.rotation_euler = (0, 0, rot)
    # brass lantern over the middle of the table
    KL.lantern(g, 'kd dining lantern', cx, cz, RECT_TOP + RECT_LANTERN, col, lights)
    return {'table': 1, 'chairs': len(seats), 'lantern': 1, 'rug': 0, 'plan': rect_plan()}


def _oak_chair(g, col, oak, fabric, y0=RUG_T):
    """Oak dining chair (seat 18.5in, back 33in) at the local origin, front toward local +z:
    square tapered legs, side and front stretchers, an upholstered seat cushion and a rounded
    upholstered back panel between two slightly raked back posts."""
    parts = []
    W, D = 1.55, 1.5                      # outer width (x) and depth (z)
    seat = 1.38                            # top of the seat frame
    hx, hz = W / 2, D / 2
    lw = 0.12
    for sx in (-1, 1):
        lx = sx * (hx - lw / 2)
        # front legs (taper to 0.09 at the floor)
        parts.append(_tapered(g, 'kd dining chair leg', lx, hz - lw / 2, 0.0, seat, lw, 0.09, oak, col))
        # back posts: rear leg continuing up, raked back 0.12 at the top
        parts.append(_post(g, 'kd dining chair back post', lx, -hz + lw / 2, seat, oak, col, lw))
    # seat rails (aprons) and stretchers
    for (a0, a1, b0, b1, y0, y1, grain) in ((-hx + lw, hx - lw, hz - 0.075, hz - 0.02, seat - 0.26, seat, 0),
                                            (-hx + lw, hx - lw, -hz + 0.02, -hz + 0.075, seat - 0.26, seat, 0),
                                            (-hx + 0.02, -hx + 0.075, -hz + lw, hz - lw, seat - 0.26, seat, 1),
                                            (hx - 0.075, hx - 0.02, -hz + lw, hz - lw, seat - 0.26, seat, 1),
                                            (-hx + 0.03, -hx + 0.075, -hz + lw, hz - lw, 0.42, 0.48, 1),
                                            (hx - 0.075, hx - 0.03, -hz + lw, hz - lw, 0.42, 0.48, 1),
                                            (-hx + lw, hx - lw, hz - 0.08, hz - 0.035, 0.5, 0.56, 0)):
        ob = g.box('kd dining chair rail', a0, a1, y0, y1, b0, b1, oak, 0.006, coll=col)
        if grain:
            ob['tg_grain'] = 1
        parts.append(ob)
    # upholstered seat cushion (soft rounded box on the frame)
    cu = g.box('kd dining chair cushion', -hx + 0.03, hx - 0.03, seat, seat + 0.17, -hz + lw + 0.005, hz + 0.02, fabric, coll=col)
    g.bevel_mod(cu, 0.06, 4)
    g.subsurf(cu, 1)
    parts.append(cu)
    # upholstered back panel between the posts (raked like the posts)
    bp = g.box('kd dining chair back cushion', -hx + lw + 0.01, hx - lw - 0.01, seat + 0.42, seat + 1.22,
               -hz + 0.02, -hz + 0.15, fabric, coll=col)
    g.bevel_mod(bp, 0.045, 4)
    g.subsurf(bp, 1)
    parts.append(bp)
    parts.append(g.box('kd dining chair back rail', -hx + lw - 0.01, hx - lw + 0.01, seat + 1.27, seat + 1.39,
                       -hz + lw / 2 - 0.055, -hz + lw / 2 + 0.055, oak, 0.01, coll=col))
    for p in parts:
        _bake(p)
    # rake the back cushion and top rail with the posts (pivot at the back of the seat)
    import mathutils
    pivot = mathutils.Vector((0.0, -(-hz + 0.08) * 0.3048, seat * 0.3048))
    R = mathutils.Matrix.Rotation(-math.atan2(0.12, 1.42), 4, 'X')
    for p in parts[-2:]:
        for v in p.data.vertices:
            v.co = R @ (v.co - pivot) + pivot
    for p in parts:
        p['y0'] = y0
    return parts


def _bake(ob):
    """Move the object's transform into its mesh so its origin is the chair origin."""
    import mathutils
    if ob.location.length or any(ob.rotation_euler):
        ob.data.transform(ob.matrix_basis)
        ob.location = (0.0, 0.0, 0.0)
        ob.rotation_euler = (0.0, 0.0, 0.0)


def _tapered(g, name, x, z, y0, y1, w0, w1, mat, col):
    """Square leg tapering from w1 at the floor to w0 at the top (local coordinates)."""
    import bmesh
    from .kitchen_dining_geo import P
    bm = bmesh.new()
    vs = []
    for y, w in ((y0, w1), (y1, w0)):
        h = w / 2
        vs.append([bm.verts.new(P(x + dx, y, z + dz)) for dx, dz in ((-h, -h), (h, -h), (h, h), (-h, h))])
    bm.faces.new(vs[0])
    bm.faces.new(list(reversed(vs[1])))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i]))
    ob = g.from_bmesh(name, bm, mat, col)
    g.ctx.add_bevel(ob, 0.008, 2)
    ob['tg_grain'] = 0
    return ob


def _post(g, name, x, z, seat, mat, col, w):
    """Rear leg + back post: straight to the seat, then raked back 0.12 ft over 1.4 ft."""
    import bmesh
    from .kitchen_dining_geo import P
    bm = bmesh.new()
    pts = [(0.0, z, 0.095), (seat, z, w), (seat + 1.42, z - 0.12, 0.1)]
    rings = []
    for y, zz, ww in pts:
        h = ww / 2
        rings.append([bm.verts.new(P(x + dx, y, zz + dz)) for dx, dz in ((-h, -h), (h, -h), (h, h), (-h, h))])
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    for a, b in zip(rings[:-1], rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    ob = g.from_bmesh(name, bm, mat, col)
    g.ctx.add_bevel(ob, 0.008, 2)
    return ob
