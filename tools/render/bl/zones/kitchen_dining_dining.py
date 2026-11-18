"""Dining set for the open area between the living room and the kitchen (z 14.5-20.8).

The open strip is only ~6.3 ft deep between the living zone (z<14.5) and the island stools
(z>=21.0), and the main walk-through (hall H3 -> D0 -> kitchen K0 / living L2) runs along
x 23-29. The set therefore sits at the east end, beside window W07 (x 40.84, z 17.81-21.81),
clear of the traffic line: a 48in round walnut pedestal table with four curved bouclé
barrel chairs set on the diagonals (a 42in round table: the 48in variant crowded the stools), and a double-ring LED chandelier above it.
"""
import math

from .kitchen_dining_geo import Geo, principled, srgb

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
