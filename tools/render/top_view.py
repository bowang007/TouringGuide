"""Orthographic top-down layout check for a SCENE-feet rectangle. North (SCENE -z) is up, east (+x)
is right. The camera sits high above the house; every mesh lying entirely above --cut ft (ceilings,
roof, wardrobe tops, ceiling fixtures) is hidden from the camera but still casts light.

  blender -b <scene.blend> --python tools/render/top_view.py -- --rect=x0,x1,z0,z1 --out top.png \
      [--px-per-ft 30] [--cut 7.5]

Write the rectangle as --rect=... (with '='): a leading minus sign would otherwise read as an option.
Run it on the .blend in place: textures are referenced relative to the .blend.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from bl.common import FT, ft2bl  # noqa: E402

HIDE = ('ceiling', 'roof', 'fascia', 'ridge', 'flashing', 'canopy', 'cricket', 'gable joined', 'hip joined',
        'soffit', 'skylight', 'vault')


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--rect', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--px-per-ft', type=float, default=30)
    ap.add_argument('--samples', type=int, default=48)
    ap.add_argument('--cut', type=float, default=7.5, help='hide meshes whose lowest point is above this (ft)')
    a = ap.parse_args(argv)
    x0, x1, z0, z1 = (float(v) for v in a.rect.split(','))
    sc = bpy.context.scene
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        low = min((o.matrix_world @ Vector(c)).z for c in o.bound_box) / FT
        if low > a.cut or any(h in o.name.lower() for h in HIDE):
            o.visible_camera = False
    sc.render.engine = 'CYCLES'
    p = bpy.context.preferences.addons['cycles'].preferences
    p.compute_device_type = 'OPTIX'
    p.get_devices()
    for d in p.devices:
        d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = a.samples
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = 1.0
    cd = bpy.data.cameras.new('top')
    cd.type = 'ORTHO'
    w, h = x1 - x0, z1 - z0
    cd.ortho_scale = max(w, h) * FT
    cd.clip_start = 0.1
    cd.clip_end = 100
    cam = bpy.data.objects.new('top', cd)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.location = ft2bl((x0 + x1) / 2, 40.0, (z0 + z1) / 2)
    cam.rotation_euler = (0, 0, 0)
    sc.render.resolution_x = int(w * a.px_per_ft) if w >= h else int(h * a.px_per_ft * w / h)
    sc.render.resolution_y = int(h * a.px_per_ft) if h >= w else int(w * a.px_per_ft * h / w)
    sc.render.filepath = a.out
    bpy.ops.render.render(write_still=True)
    print('top view:', a.out)


main()
