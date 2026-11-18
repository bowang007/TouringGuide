"""Living zone: modern living room north of z=14.5 plus the stone fireplace feature wall
(runs inside Blender).

Design (1077 W McKinley language): book-matched green-grey stone feature wall with a 5 ft linear
gas fireplace and a floating walnut ledge on the east wall; a low white boucle sofa against the
west wall facing it, ochre accent pillows and a cream knit throw; two sculptural boucle barrel
chairs closing a U around a walnut coffee table on a large cream wool rug; large gestural
abstract canvas over the sofa; money tree in a fluted stoneware planter in the garden corner;
dried pampas in a white ceramic vase; table + floor lamps; a tidy grid of 4" warm cans.

Plan (SCENE ft, x west->east, z north->south). Room x 23.28..40.61, z 0.23..~17.
  sofa        x 23.42..26.67  z 4.00..11.90   faces east (on the rug, recessed black plinth)
  coffee tbl  centre (29.42, 7.95) 2.6 x 5.0, top 15.5"
  chair A     (31.55, 3.45)  chair B (31.35, 12.40)   barrel chairs facing the table (U opens east)
  rug         x 23.95..37.45  z 2.35..13.35 (sofa, chairs, side table, floor lamp all on it)
  stone wall  x 39.75..40.61 z 8.2..15.0 floor to ceiling; firebox 5 ft x 15" at y 1.55..2.85
  ledge       x 38.25..(39.75 | 40.61) z 8.2..16.4, top 16.2" (scribed around the stone bump-out)
  tree        fluted planter (38.95, 1.85); art 6 x 3.6 ft over the sofa on the west wall
Camera stops L0 (33.9, 10.5), L1 (34.4, 4.0), L2 (27.6, 13.0) keep >= 1.2 ft clear (checked on
mesh vertices below 6.5 ft at build time; any violation is listed in the returned notes).
Set TG_LIVING_STONE=own to use this zone's veined slab shader instead of the library onyx 'stone_feature' (default).
Helpers: living_geo (mesh primitives), living_furniture (sofa, chairs, tables, lamps, throw), living_fireplace
(stone mass, firebox, ledge), living_fire_mats (stone, flame, ember and media shaders), living_decor (art,
pampas, planter + tree, vases).
"""
import math
import os
import time

import bpy
import numpy as np

from .. import lighting
from ..common import place
from . import living_decor as DEC
from . import living_fireplace as FP
from . import living_furniture as F
from . import living_geo as G

COLL = 'zone_living'
LIGHTS = 'zone_living_lights'

WEST_X, EAST_X = 23.28, 40.61
RUG = (23.95, 37.45, 2.35, 13.35)
RUG_T = 0.045
SOFA = dict(x=23.42, z=7.95, L=7.9, D=3.25)
TABLE = dict(x=29.42, z=7.95, W=2.6, Lz=5.0, top=1.29)
CHAIR_A = (31.55, 3.45)
CHAIR_B = (31.35, 12.40)
SIDE_TABLE = (24.42, 12.78)
FLOOR_LAMP = (24.42, 3.35)
PLANTER = (38.95, 1.85)
STONE_Z = (8.2, 15.0)
STONE_FACE_X = 39.75
LEDGE_Z1 = 16.4
CANS_X = (26.2, 30.2, 34.2)
CANS_Z = (3.0, 7.6, 12.2)
WASH = ((38.45, 9.0), (38.45, 14.2))         # cans grazing the stone feature wall
STOPS = {'L0': (33.9, 10.5), 'L1': (34.4, 4.0), 'L2': (27.6, 13.0)}


def _on_rug(x, z):
    return RUG[0] <= x <= RUG[1] and RUG[2] <= z <= RUG[3]


def build(ctx):
    t0 = time.time()
    coll = ctx.coll(COLL)
    ctx.coll(LIGHTS, COLL)
    notes = []

    # ---------------------------------------------------------------- rug
    F.rug(ctx, *RUG, t=RUG_T)

    # ---------------------------------------------------------------- sofa + soft goods
    sg = G.group(ctx, 'living sofa')
    F.sofa(ctx, sg, L=SOFA['L'], D=SOFA['D'])
    L = SOFA['L']
    inner = L / 2 - F.ARM_T
    # pillows: ochre at the arms, textured cream inside (leaning on the back cushions), chopped tops
    F.sofa_pillow(ctx, sg, 1.62, -inner + 0.98, 1.72, 'fabric_mustard', tilt_deg=18, yaw=math.radians(10), name='pillow ochre N', chop=0.1)
    F.sofa_pillow(ctx, sg, 1.55, -inner + 2.5, 1.8, 'fabric_linen_white', tilt_deg=16, yaw=math.radians(-5), name='pillow cream N', chop=0.08)
    F.sofa_pillow(ctx, sg, 1.55, inner - 2.5, 1.8, 'fabric_linen_white', tilt_deg=16, yaw=math.radians(5), name='pillow cream S', chop=0.08)
    F.sofa_pillow(ctx, sg, 1.62, inner - 0.98, 1.72, 'fabric_mustard', tilt_deg=18, yaw=math.radians(-10), name='pillow ochre S', chop=0.1)
    F.throw_over_arm(ctx, sg, L=L, D=SOFA['D'], side=-1)
    place(sg, SOFA['x'], RUG_T, SOFA['z'], 0)

    # ---------------------------------------------------------------- coffee table + styling
    tg = G.group(ctx, 'living coffee table')
    F.coffee_table(ctx, tg, W=TABLE['W'], Lz=TABLE['Lz'], top_y=TABLE['top'] + RUG_T, base_y=RUG_T)
    ty = TABLE['top'] + RUG_T
    F.book(ctx, tg, -0.15, ty, 1.15, 1.0, 1.3, 0.12, F.BOOK_COLORS[0], yaw=0.05, name='book 1')
    F.book(ctx, tg, -0.12, ty + 0.12, 1.12, 0.85, 1.12, 0.1, F.BOOK_COLORS[3], yaw=-0.12, name='book 2')
    F.book(ctx, tg, -0.1, ty + 0.22, 1.1, 0.7, 0.95, 0.08, F.BOOK_COLORS[1], yaw=0.2, name='book 3')
    place(tg, TABLE['x'], 0, TABLE['z'], 0)
    DEC.vase(ctx, 'ceramic_vase_02', TABLE['x'] + 0.1, ty, TABLE['z'] - 1.2, 0.82, rot=0.6)
    bowl_prof = [(0.0, 0.0), (0.18, 0.0), (0.32, 0.06), (0.42, 0.17), (0.40, 0.18), (0.30, 0.09), (0.0, 0.05)]
    v, f = G.lathe([(r, y + ty + 0.30) for r, y in bowl_prof], n=48, cap_bottom=False)
    G.obj(ctx, 'living bowl', G.translate(v, TABLE['x'] - 0.1, 0, TABLE['z'] + 1.1), f, F.mat_ceramic_white(), COLL)

    # ---------------------------------------------------------------- lounge chairs
    for name, (cx, cz) in (('A', CHAIR_A), ('B', CHAIR_B)):
        cg = G.group(ctx, f'living lounge chair {name}')
        F.barrel_chair(ctx, cg, base_y=RUG_T if _on_rug(cx, cz) else 0.0)
        # ochre lumbar pillow on chair A
        if name == 'A':
            F.sofa_pillow(ctx, cg, -0.38, 0.0, 1.45, 'fabric_mustard', tilt_deg=22, seat_top=1.46 + RUG_T,
                          thick=0.4, name='chair pillow', h=0.95)
        rot = G.facing(TABLE['x'] - cx, TABLE['z'] - cz)
        place(cg, cx, 0, cz, rot)

    # ---------------------------------------------------------------- side table + lamp
    sx, sz = SIDE_TABLE
    stg = G.group(ctx, 'living side table')
    F.side_table(ctx, stg, base_y=RUG_T)
    F.table_lamp(ctx, stg, (sx, sz), 1.85 + RUG_T, LIGHTS)
    place(stg, sx, 0, sz, 0)

    # ---------------------------------------------------------------- floor lamp
    flg = G.group(ctx, 'living floor lamp')
    F.floor_lamp(ctx, flg, FLOOR_LAMP, LIGHTS, base_y=RUG_T)
    place(flg, FLOOR_LAMP[0], 0, FLOOR_LAMP[1], 0)

    # ---------------------------------------------------------------- feature wall + fireplace
    fp = FP.build(ctx, LIGHTS, stone_z=STONE_Z, face_x=STONE_FACE_X, wall_x=EAST_X, ledge_z1=LEDGE_Z1,
                  stone=os.environ.get('TG_LIVING_STONE', 'library'))
    ly = fp['ledge_top']
    # ledge styling: tall vase with pampas at the south end, small ochre jug, books at the north end
    _, vtop, _ = DEC.vase(ctx, 'ceramic_vase_01', 39.6, ly, 15.82, 1.85, rot=0.3)
    DEC.pampas(ctx, (39.6, vtop - 0.05, 15.82), seed=5)
    DEC.vase(ctx, 'ceramic_vase_04', 38.95, ly, 15.25, 0.85, rot=2.2, recolor=(0.62, 0.40, 0.14))
    lg = G.group(ctx, 'living ledge books')
    F.book(ctx, lg, 0, ly, 0, 0.95, 0.7, 0.1, F.BOOK_COLORS[3], yaw=0.0, name='ledge book 1')
    F.book(ctx, lg, 0.02, ly + 0.1, 0.02, 0.8, 0.62, 0.08, F.BOOK_COLORS[2], yaw=0.1, name='ledge book 2')
    place(lg, 39.05, 0, 9.0, 0)

    # ---------------------------------------------------------------- art over the sofa
    DEC.wall_art(ctx, WEST_X, SOFA['z'] - 3.0, SOFA['z'] + 3.0, 3.4, 7.0)

    # ---------------------------------------------------------------- tree in the garden corner
    DEC.planter_with_tree(ctx, PLANTER[0], PLANTER[1], rot=math.radians(35))

    # ---------------------------------------------------------------- lights
    n_cans = 0
    for x in CANS_X:
        for z in CANS_Z:
            lighting.can(ctx, x, z, coll=LIGHTS)
            n_cans += 1
    for x, z in WASH:
        lighting.can(ctx, x, z, coll=LIGHTS, beam_deg=55.0)
        n_cans += 1

    # ---------------------------------------------------------------- checks
    bpy.context.view_layer.update()
    tris = 0
    nobj = 0
    for o in coll.all_objects:
        nobj += 1
        if o.type == 'MESH':
            tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
    for o in coll.all_objects:
        if o.type != 'MESH' or o.name.startswith(('can ', 'living flame')):
            continue
        n = len(o.data.vertices)
        if n == 0:
            continue
        co = np.empty(n * 3, np.float32)
        o.data.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        M = np.array(o.matrix_world)
        w = co @ M[:3, :3].T + M[:3, 3]
        xs, ys, zs = w[:, 0] / 0.3048, w[:, 2] / 0.3048, -w[:, 1] / 0.3048
        low = ys < 6.5
        if not low.any():
            continue
        for sid, (cx, cz) in STOPS.items():
            d = float(np.min(np.hypot(xs[low] - cx, zs[low] - cz)))
            if d < 1.2 and ys[low].max() > 0.1:
                notes.append(f'{sid} clearance {d:.2f} ft to {o.name}')
    ctx.stats['living'] = {'objects': nobj, 'base_tris': tris, 'cans': n_cans}
    return {'objects': nobj, 'base_tris': tris, 'cans': n_cans, 'notes': notes[:12],
            'seconds': round(time.time() - t0, 1)}
