"""Look for holes in the built shell: ceilings that open into the attic, floors that open to the plinth.

  $BLENDER -b tools/render/.cache/house.blend --python tools/render/check_holes.py

Casts a grid of rays (every 0.2 ft over the house footprint) up from 7 ft and down from 1 ft against the
`shell`, `openings` and `exterior_shell` collections only, so furniture and rugs can't hide a hole. An
upward ray must stop on a ceiling-like surface (or on a wall top at 8 ft); a downward ray must stop on
a floor at grade. Prints one line per object hit instead, with the area it covers. Rays that start
inside a wall's thickness report the wall's head at 7 ft: those lines are expected.
"""
import collections
import json
import os
import re
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

FT = 0.3048
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import relayout as R  # noqa: E402

KEEP = {'shell', 'openings', 'exterior_shell'}
CEILING = re.compile(r'ceiling|vault|skylight|lining|infill|soffit', re.I)


def shell_bvh():
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, owner = [], [], []
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render or not ({c.name for c in ob.users_collection} & KEEP):
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        mw, base = ob.matrix_world, len(verts)
        verts += [mw @ v.co for v in me.vertices]
        for p in me.polygons:
            polys.append([base + i for i in p.vertices])
            owner.append(ob.name)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), owner


def main():
    bvh, owner = shell_bvh()
    ex = json.load(open(os.path.join(HERE, 'data', 'scene.json')))['extent'][0]
    o, wall = R.OUTER, 0.45
    foyer = (R.FOYER_WALL[0], R.FOYER_WALL[0] + 6.5)

    def front(x):                                   # inside face of the front wall at x
        if x < foyer[0]:
            return o['front_bed'] - wall
        return o['front_wall'] - wall if x < foyer[1] else o['garage_front'] - wall
    out = []

    def scan(y0, d, bad, tag, step=0.2):
        found = collections.defaultdict(list)
        x = 0.35
        while x < ex - 0.3:
            z = 0.35
            while z < front(x) - 0.1:
                loc, _, i, _ = bvh.ray_cast(Vector((x * FT, -z * FT, y0 * FT)), Vector((0, 0, d)), 10 * FT)
                name = owner[i] if loc is not None else 'nothing'
                y = loc.z / FT if loc is not None else None
                if bad(name, y):
                    found[name].append((x, z, y))
                z += step
            x += step
        for name, v in sorted(found.items(), key=lambda kv: -len(kv[1])):
            xs = [p[0] for p in v]
            zs = [p[1] for p in v]
            y = '-' if v[0][2] is None else f'{v[0][2]:.2f}'
            out.append(f'{tag:7s} {name[:48]:48s} {len(v):5d} rays  x {min(xs):6.2f}-{max(xs):6.2f}  '
                       f'z {min(zs):6.2f}-{max(zs):6.2f}  y {y}')

    scan(7.0, 1, lambda n, y: y is None or not (CEILING.search(n) or abs(y - 8.0) < 0.05), 'ceiling')
    scan(1.0, -1, lambda n, y: y is None or y < -0.06, 'floor')
    print('\n'.join(out) if out else 'no holes', flush=True)


main()
