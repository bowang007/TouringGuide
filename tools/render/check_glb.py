"""Render a baked web GLB unlit (exactly what three.js shows) from a dollhouse camera.
  blender -b --factory-startup --python tools/render/check_glb.py -- <house.glb> <out.png> [hide_classes=ceiling,exterior] [view=dollhouse|top|front]
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
glb, out = argv[0], argv[1]
hide = set((argv[2] if len(argv) > 2 else 'ceiling,exterior').split(','))
view = argv[3] if len(argv) > 3 else 'dollhouse'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for o in bpy.data.objects:
    cls = o.get('tg_class')
    if cls in hide:
        o.hide_render = True
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'FLAT'
sh.color_type = 'TEXTURE'
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
cd = bpy.data.cameras.new('c')
cam = bpy.data.objects.new('c', cd)
sc.collection.objects.link(cam)
sc.camera = cam
FT = 0.3048
c = Vector((20.4 * FT, -27.5 * FT, 0))
if view == 'top':
    cd.type = 'ORTHO'
    cd.ortho_scale = 62 * FT
    cam.location = c + Vector((0, 0, 30))
    cam.rotation_euler = (0, 0, 0)
else:
    cd.lens = 32
    d = Vector((-0.55, -0.75, 0.62)) if view == 'dollhouse' else Vector((0.0, -1.0, 0.18))
    cam.location = c + d.normalized() * (26 if view == 'dollhouse' else 30)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
