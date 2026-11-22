"""Living zone: the living room at the rear of the open plan (runs inside Blender).

Seventh round (2026-11-21), the owner: "Seal off the fireplace so that we could put sofa on the fireplace side, and
put a TV on the other side of the wall so that we could watch TV." The fireplace that stood in front of the east
wall (stone mass, firebox, flames, the walnut hearth ledge and everything on it) is no longer built. The wall behind
it was never cut: it is the plain painted wall with its baseboard. The room is furnished as sheet SKA002 draws it:
the sofa on the east wall with a table at each end, a round rug and a round coffee table in front of it, one
armchair to the north-west, the television on the west wall opposite the sofa.

PLAN FEET. Unlike the zones written on the concept plan, every number here is SCENE feet on the architect's plan
(x west->east, y up, z rear->street), measured on the built model. bl/warp.py must therefore leave the room alone:
everything hangs under one root Empty (ROOT, at the SCENE origin). The warp skips objects named 'TG ...' and objects
that have a parent, so nothing here is moved or reshaped.

Room as built: west wall face x 22.528 (the Bedroom 2 divider, z 0.225..15.151; the hall opens south of it), east
wall face x 39.195, rear wall face z 0.225, ceiling 8.0, open to the dining area in the south.
  rear wall   deck door x 24.454..26.933 (its glass leaf stands open into the room along x 24.45, z 0..2.56),
              glass x 27.807..32.939 and x 33.551..38.770, y 0.2..7.5
  east wall   windows z 0.481..3.349 and z 4.096..6.965, sill 2.5, head 7.0; solid from z 6.965 to 17.615

Layout (the sofa / television axis is z 8.05, as on the sheet):
  sofa        x 35.80..39.05, z 4.40..11.70, back to the east wall, faces west. Its back ends below the sill of the
              window it stands under, and the pillows on that half are a low lumbar and the throw
  side tables round, r 0.62, at (38.35, 3.72) and (38.35, 12.38), a lamp on each; the north lamp stands in front of
              the pier between the two east windows
  art         canvas z 7.55..11.55, y 3.55..5.95 on the east wall above the sofa, clear of the window (jamb 6.965)
  rug         round, r 4.6, centre (33.1, 7.45), drawn north of the axis toward the armchair like the sheet's
  coffee tbl  round, r 1.42 (34 in), centre (33.0, 8.05), top 15 in
  armchair    barrel chair at (30.4, 3.75), turned between the coffee table and the television; its front stands
              on the rug's edge
  television  75 in on the west wall, z 5.308..10.792, y 2.321..5.435, screen face x 22.681
  console     white oak, 7'-6" x 1'-4 3/4" x 1'-8 1/2", x 22.603..24.003, z 4.30..11.80, on black steel legs
  tree        money tree, 4.6 ft, in the fluted planter at (23.7, 13.0): on the west wall beside the console's
              south end, its crown 0.8 ft short of the corner where the hall opens
  lights      the 3 x 3 grid of 4 in cans as before (CANS_X / CANS_Z, in line with the dining area's cans) and
              three cans over the sofa side on the old wall-wash column, on the grid's rows (SOFA_CANS): one even
              4 x 3 field; a lamp on each side table
Kept clear: 7.6 ft of floor between the coffee table and the console for the walk from the dining area to the deck
door, 4.5 ft between the console and the rug, 2.3 ft between the armchair and the rear glass; the armchair stands
north of every line from a sofa seat to the screen. build() checks these on the built meshes and lists, with the
tour stops of data/sweeps.json that stand closer than 1.2 ft to a piece of furniture, what does not hold.

Helpers: living_geo (mesh primitives), living_furniture (sofa, armchair, tables, lamps, throw, rug),
living_media (television, console), living_decor (art, planter + tree, vases).
"""
import json
import math
import os
import time

import bpy
import numpy as np

from .. import lighting
from ..common import DATA_DIR, FT, place
from . import living_decor as DEC
from . import living_furniture as F
from . import living_geo as G
from . import living_media as M

COLL = 'zone_living'
LIGHTS = 'zone_living_lights'
ROOT = 'TG living root'

# ---- the room as built (plan feet)
WEST_X, EAST_X = 22.528, 39.195
REAR_Z = 0.225
WEST_WALL_END_Z = 15.151
EAST_WINDOWS = ((0.481, 3.349), (4.096, 6.965))      # z extents; sill 2.5, head 7.0
EAST_SILL = 2.5
REAR_GLASS = ((27.807, 32.939), (33.551, 38.770))    # x extents
DECK_DOOR = (24.454, 26.933)                         # x extent of the opening

# ---- layout
AXIS_Z = 8.05                                        # sofa and television centre line (sheet: sofa z 4.4..11.7)
RUG_T = 0.045
SOFA = dict(back_x=39.05, z=AXIS_Z, L=7.3, D=3.25)   # its puffed base ends 0.02 ft before the baseboard
SIDE_R = 0.62
SIDE_X = 38.35
SIDE_N = (SIDE_X, AXIS_Z - SOFA['L'] / 2 - 0.06 - SIDE_R)     # z 3.72: the pier between the east windows
SIDE_S = (SIDE_X, AXIS_Z + SOFA['L'] / 2 + 0.06 + SIDE_R)     # z 12.38
SIDE_H = 1.85
LAMP_SHADE_R = 0.45
RUG = dict(x=33.1, z=7.45, r=4.6)
TABLE = dict(x=33.0, z=AXIS_Z, r=1.42, top=1.25)
CHAIR = dict(x=30.4, z=3.75, aim=(29.6, 8.0))
TV = dict(diag_in=75.0, yc=3.885)
CONSOLE = dict(L=7.5, D=1.4, top=1.7, leg_h=0.5)
ART_Z, ART_Y = (7.55, 11.55), (3.55, 5.95)
TREE = (23.7, 13.0)                                  # beside the console's south end, clear of the hall corner
TREE_ROT = math.radians(215.0)                       # the crown's fuller side toward the room
TREE_H = 4.6
CANS_X = (25.338, 29.184, 33.030)                    # the concept's 26.2 / 30.2 / 34.2 on the plan (kitchen zone's too)
CANS_Z = (2.969, 7.517, 12.064)                      # the concept's 3.0 / 7.6 / 12.2
# The concept's wall-wash column x 38.45, on the grid's three rows: with the 3 x 3 grid the ceiling carries one
# even 4 x 3 field of cans (two cans here left the north-east corner of the field empty).
SOFA_CANS = ((37.116, 2.969), (37.116, 7.517), (37.116, 12.064))

EYE_Y = 3.6                                          # seated eye height for the sightline check
STOP_CLEAR = 1.2


def _zone_points(coll, skip=('can ', 'living rug')):
    """World vertices (plan feet: x, y, z) of the zone's meshes, per object name."""
    out = {}
    for o in coll.all_objects:
        if o.type != 'MESH' or o.name.startswith(skip) or not len(o.data.vertices):
            continue
        co = np.empty(len(o.data.vertices) * 3, np.float32)
        o.data.vertices.foreach_get('co', co)
        mw = np.array(o.matrix_world)
        w = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        out[o.name] = np.stack([w[:, 0] / FT, w[:, 2] / FT, -w[:, 1] / FT], 1)
    return out


def _checks(coll, tv, con):
    """Clearances of the layout in plan feet, from the built meshes; `notes` lists what does not hold."""
    notes = []
    pts = _zone_points(coll)
    res = {}
    # nothing pokes through a wall or stands in front of the rear glass line
    for name, p in pts.items():
        if p[:, 0].min() < WEST_X - 0.01 or p[:, 0].max() > EAST_X + 0.01 or p[:, 2].min() < REAR_Z - 0.01:
            notes.append(f'{name} leaves the room: x {p[:, 0].min():.2f}..{p[:, 0].max():.2f}, z min {p[:, 2].min():.2f}')
    low = {n: p[(p[:, 1] > 0.1) & (p[:, 1] < 6.5)] for n, p in pts.items()}
    low = {n: p for n, p in low.items() if len(p)}
    table_w = TABLE['x'] - TABLE['r']
    res['coffee_table_to_tv_wall_ft'] = round(table_w - WEST_X, 2)
    res['coffee_table_to_console_ft'] = round(table_w - con['x1'], 2)
    res['rug_to_console_ft'] = round(RUG['x'] - RUG['r'] - con['x1'], 2)
    res['sofa_to_coffee_table_ft'] = round(SOFA['back_x'] - SOFA['D'] - (TABLE['x'] + TABLE['r']), 2)
    chair = np.concatenate([p for n, p in pts.items() if n.startswith(('chair ', 'chair pillow'))])
    res['armchair_xz'] = [round(float(v), 2) for v in (chair[:, 0].min(), chair[:, 0].max(), chair[:, 2].min(), chair[:, 2].max())]
    res['armchair_to_rear_glass_ft'] = round(float(chair[:, 2].min()) - REAR_Z, 2)
    res['armchair_to_deck_door_jamb_ft'] = round(float(chair[:, 0].min()) - DECK_DOOR[1], 2)
    cx0, cx1 = float(chair[:, 0].min()), float(chair[:, 0].max())
    res['armchair_before_rear_glass_x'] = [[round(max(a, cx0), 2), round(min(b, cx1), 2)] for a, b in REAR_GLASS
                                           if min(b, cx1) > max(a, cx0)]
    crown = np.concatenate([p for n, p in pts.items() if n.startswith('pachira')])
    res['tree_to_hall_corner_ft'] = round(WEST_WALL_END_Z - float(crown[:, 2].max()), 2)
    res['tree_to_console_ft'] = round(float(crown[:, 2].min()) - con['z1'], 2)
    # the sofa stands under the south-east window: nothing on that half may rise into the glass (0.1 ft above the sill)
    under = [p[p[:, 2] < EAST_WINDOWS[1][1]] for n, p in pts.items() if n.startswith(('sofa', 'pillow'))]
    top = max(float(p[:, 1].max()) for p in under if len(p))
    res['sofa_top_under_window_ft'] = round(top, 2)
    if top > EAST_SILL + 0.1:
        notes.append(f'sofa reaches y {top:.2f} under the east window (glass from {EAST_SILL + 0.1:.2f})')
    # sightlines: from three seats on the sofa to the screen's corners and centre, against everything below them
    seat_x = SOFA['back_x'] - 1.6
    half = SOFA['L'] / 2 - F.ARM_T
    hw = (tv['z1'] - tv['z0']) / 2 - 0.02
    targets = [(tv['face_x'], y, AXIS_Z + s * hw) for y in (tv['y0'] + 0.04, (tv['y0'] + tv['y1']) / 2, tv['y1'] - 0.02)
               for s in (-1, 0, 1)]
    blocked = set()
    for sz in (AXIS_Z - half + 0.75, AXIS_Z, AXIS_Z + half - 0.75):
        eye = np.array([seat_x, EYE_Y, sz])
        for tgt in targets:
            d = np.array(tgt) - eye
            for n, p in low.items():
                if n.startswith(('living tv', 'sofa', 'pillow', 'living console')):
                    continue
                t = (p[:, 0] - eye[0]) / d[0]                    # where the object's vertices sit along the line
                m = (t > 0.02) & (t < 0.98)
                if not m.any():
                    continue
                dz = np.abs(p[m, 2] - (eye[2] + t[m] * d[2]))
                above = p[m, 1] - (eye[1] + t[m] * d[1])
                if ((dz < 0.15) & (above > 0.0)).any():
                    blocked.add(n)
    res['tv_sightline_blocked_by'] = sorted(blocked)
    if blocked:
        notes.append('television sightline crossed by ' + ', '.join(sorted(blocked)))
    # the tour's stops (plan feet) against the furniture
    path = os.path.join(DATA_DIR, 'sweeps.json')
    stops = {}
    if os.path.exists(path):
        for s in json.load(open(path)).get('sweeps', []):
            x, _, z = s['p']
            if WEST_X < x < EAST_X and REAR_Z < z < 17.0:
                d, who = min((float(np.min(np.hypot(p[:, 0] - x, p[:, 2] - z))), n) for n, p in low.items())
                stops[s['id']] = round(d, 2)
                if d < STOP_CLEAR:
                    notes.append(f"stop {s['id']} ({x:.2f}, {z:.2f}): {d:.2f} ft to {who}")
    res['stop_clearance_ft'] = stops
    return res, notes


def build(ctx):
    t0 = time.time()
    coll = ctx.coll(COLL)
    ctx.coll(LIGHTS, COLL)
    root = G.group(ctx, ROOT)                    # at the SCENE origin: see the module docstring

    # ---------------------------------------------------------------- rug
    F.rug(ctx, RUG['x'], RUG['z'], RUG['r'], t=RUG_T)

    # ---------------------------------------------------------------- sofa + soft goods
    # (the sofa is built facing +x and turned half round: its local +z end is the north end, under the window)
    sg = G.group(ctx, 'living sofa')
    L, D = SOFA['L'], SOFA['D']
    F.sofa(ctx, sg, L=L, D=D)
    inner = L / 2 - F.ARM_T
    F.sofa_pillow(ctx, sg, 1.62, -inner + 0.95, 1.72, 'fabric_mustard', tilt_deg=18, yaw=math.radians(10), name='pillow ochre S', chop=0.1)
    F.sofa_pillow(ctx, sg, 1.55, -inner + 2.45, 1.8, 'fabric_linen_white', tilt_deg=16, yaw=math.radians(-5), name='pillow cream S', chop=0.08)
    F.sofa_pillow(ctx, sg, 1.5, inner - 1.95, 1.9, 'fabric_linen_white', tilt_deg=14, thick=0.42, name='pillow lumbar N', h=1.0)
    F.throw_over_arm(ctx, sg, L=L, D=D, side=1, x_range=(1.5, 3.0))      # the arm's front: clear of the side table
    place(sg, SOFA['back_x'], 0, SOFA['z'], math.pi)

    # ---------------------------------------------------------------- side tables + lamps
    for tag, (sx, sz) in (('N', SIDE_N), ('S', SIDE_S)):
        stg = G.group(ctx, f'living side table {tag}')
        F.side_table(ctx, stg, r=SIDE_R, h=SIDE_H)
        F.table_lamp(ctx, stg, (sx, sz), SIDE_H, LIGHTS, shade_r=LAMP_SHADE_R)
        place(stg, sx, 0, sz, 0)

    # ---------------------------------------------------------------- coffee table + styling
    tg = G.group(ctx, 'living coffee table')
    ty = TABLE['top'] + RUG_T
    F.coffee_table(ctx, tg, r=TABLE['r'], top_y=ty, base_y=RUG_T)
    F.book(ctx, tg, -0.2, ty, 0.4, 1.0, 1.3, 0.12, F.BOOK_COLORS[0], yaw=0.05, name='book 1')
    F.book(ctx, tg, -0.17, ty + 0.12, 0.37, 0.85, 1.12, 0.1, F.BOOK_COLORS[3], yaw=-0.12, name='book 2')
    F.book(ctx, tg, -0.15, ty + 0.22, 0.35, 0.7, 0.95, 0.08, F.BOOK_COLORS[1], yaw=0.2, name='book 3')
    place(tg, TABLE['x'], 0, TABLE['z'], 0)
    DEC.vase(ctx, 'ceramic_vase_02', TABLE['x'] + 0.3, ty, TABLE['z'] - 0.6, 0.82, rot=0.6)
    bowl_prof = [(0.0, 0.0), (0.18, 0.0), (0.32, 0.06), (0.42, 0.17), (0.40, 0.18), (0.30, 0.09), (0.0, 0.05)]
    v, f = G.lathe([(r, y + ty + 0.30) for r, y in bowl_prof], n=48, cap_bottom=False)
    G.obj(ctx, 'living bowl', G.translate(v, TABLE['x'] - 0.15, 0, TABLE['z'] + 0.35), f, F.mat_ceramic_white(), COLL)

    # ---------------------------------------------------------------- armchair
    cg = G.group(ctx, 'living armchair')
    F.barrel_chair(ctx, cg)
    F.sofa_pillow(ctx, cg, -0.38, 0.0, 1.45, 'fabric_mustard', tilt_deg=22, seat_top=1.46, thick=0.4,
                  name='chair pillow', h=0.95)
    place(cg, CHAIR['x'], 0, CHAIR['z'], G.facing(CHAIR['aim'][0] - CHAIR['x'], CHAIR['aim'][1] - CHAIR['z']))

    # ---------------------------------------------------------------- television + console on the west wall
    mg = G.group(ctx, 'living media wall')
    tv = M.tv(ctx, mg, WEST_X, AXIS_Z, TV['yc'], TV['diag_in'])
    con = M.console(ctx, mg, WEST_X, AXIS_Z, **CONSOLE)
    cy, cxm = con['top'], (con['x0'] + con['x1']) / 2
    # a few things on the console: books and an ochre jug north of the screen, a low bowl under it, a white
    # vase south of it (the tall pieces stand clear of the screen's ends)
    bg = G.group(ctx, 'living console books')
    F.book(ctx, bg, 0, cy, 0, 0.72, 1.0, 0.11, F.BOOK_COLORS[2], yaw=0.0, name='console book 1')
    F.book(ctx, bg, 0.02, cy + 0.11, -0.02, 0.62, 0.86, 0.09, F.BOOK_COLORS[3], yaw=0.09, name='console book 2')
    place(bg, cxm, 0, con['z0'] + 1.25, 0)
    DEC.vase(ctx, 'ceramic_vase_04', cxm - 0.05, cy, con['z0'] + 0.48, 0.85, rot=2.2, recolor=(0.62, 0.40, 0.14))
    low_prof = [(0.0, 0.0), (0.22, 0.0), (0.42, 0.05), (0.52, 0.14), (0.50, 0.15), (0.38, 0.08), (0.0, 0.05)]
    v, f = G.lathe([(r, y + cy) for r, y in low_prof], n=56, cap_bottom=False)
    G.obj(ctx, 'living console bowl', G.translate(v, cxm, 0, AXIS_Z + 1.5), f, F.mat_ceramic_white(), COLL)
    DEC.vase(ctx, 'ceramic_vase_01', cxm, cy, con['z1'] - 0.52, 1.3, rot=0.3)

    # ---------------------------------------------------------------- art over the sofa
    DEC.wall_art(ctx, EAST_X, ART_Z[0], ART_Z[1], ART_Y[0], ART_Y[1], face=-1)

    # ---------------------------------------------------------------- tree beside the console
    DEC.planter_with_tree(ctx, TREE[0], TREE[1], rot=TREE_ROT, tree_h_ft=TREE_H)

    # ---------------------------------------------------------------- lights
    n_cans = 0
    for x in CANS_X:
        for z in CANS_Z:
            lighting.can(ctx, x, z, coll=LIGHTS)
            n_cans += 1
    for x, z in SOFA_CANS:
        lighting.can(ctx, x, z, coll=LIGHTS, beam_deg=55.0)
        n_cans += 1

    # ---------------------------------------------------------------- one root, so the warp leaves the room alone
    for o in list(coll.all_objects):
        if o is not root and o.parent is None:
            o.parent = root

    # ---------------------------------------------------------------- checks
    bpy.context.view_layer.update()
    tris = 0
    nobj = 0
    for o in coll.all_objects:
        nobj += 1
        if o.type == 'MESH':
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    clear, notes = _checks(coll, tv, con)
    ctx.stats['living'] = {'objects': nobj, 'base_tris': tris, 'cans': n_cans}
    return {'objects': nobj, 'base_tris': tris, 'cans': n_cans, 'clearances': clear, 'notes': notes[:16],
            'seconds': round(time.time() - t0, 1)}
