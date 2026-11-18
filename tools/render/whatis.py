"""Identify what is seen at points of a tour panorama: object, material, owning collection/zone,
distance. Ray-casts the built scene from the node's camera position.

  blender -b <scene.blend> --python tools/render/whatis.py -- --node K0 --at 0.42,0.55 --at y=90,p=-10 ...

Points: 'u,v' = fractions of the equirect image (u=0 left edge, v=0 top), or 'y=<deg>,p=<deg>' =
yaw relative to the node's opening yaw (clockwise, same as the review sheets' 'yaw+N' labels) and
pitch (up positive; the sheets are cut at p=-8 with a 90deg FOV).
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from bl.common import DATA_DIR, FT, ft2bl  # noqa: E402


def owner(ob):
    """Collection paths of an object, e.g. ['zone_living/living_lights']."""
    parents = {ch.name: p.name for p in bpy.data.collections for ch in p.children}
    out = []
    for c in ob.users_collection:
        chain = [c.name]
        while chain[-1] in parents and len(chain) < 8:
            chain.append(parents[chain[-1]])
        out.append('/'.join(reversed(chain)))
    return out


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--node', required=True)
    ap.add_argument('--at', action='append', required=True)
    a = ap.parse_args(argv)
    scene = json.load(open(os.path.join(DATA_DIR, 'scene.json')))
    node = next(n for n in scene['tour']['nodes'] if n['id'] == a.node)
    origin = ft2bl(*node['p'])
    dg = bpy.context.evaluated_depsgraph_get()
    for spec in a.at:
        if spec.startswith('y='):
            kv = dict(x.split('=') for x in spec.split(','))
            th = node['yaw'] + math.radians(float(kv['y']))
            el = math.radians(float(kv.get('p', 0)))
        else:
            u, v = (float(x) for x in spec.split(','))
            th = (u - 0.5) * 2 * math.pi
            el = (0.5 - v) * math.pi
        d_scene = (math.sin(th) * math.cos(el), math.sin(el), -math.cos(th) * math.cos(el))
        d = Vector((d_scene[0], -d_scene[2], d_scene[1]))
        hit, loc, nrm, idx, ob, _ = bpy.context.scene.ray_cast(dg, origin, d)
        if not hit:
            print(f'[whatis] {spec}: nothing (sky)')
            continue
        mat = None
        if ob.type == 'MESH' and ob.data.polygons and idx < len(ob.data.polygons):
            mi = ob.data.polygons[idx].material_index
            if mi < len(ob.material_slots) and ob.material_slots[mi].material:
                mat = ob.material_slots[mi].material.name
        p = loc / FT
        print(f'[whatis] {spec}: {ob.name!r} mat={mat} coll={owner(ob)} dist={(loc - origin).length / FT:.2f}ft '
              f'at SCENE x={p.x:.2f} y={p.z:.2f} z={-p.y:.2f} scene_index={ob.get("scene_index")}')


main()
