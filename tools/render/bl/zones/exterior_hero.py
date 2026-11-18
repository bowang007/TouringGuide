"""Exterior hero stills (2-point perspective) for checking the exterior zone and for the listing.

  blender -b tools/render/.cache/dev_exterior/scene.blend --python tools/render/bl/zones/exterior_hero.py -- \
      [--shots front,front34,back,backdeck] [--width 1600] [--samples 128] [--out DIR]

Camera rigs are in SCENE feet (x east, y up, z south) like the rest of the pipeline; vertical lines are
kept vertical (pitch 0) and framing is done with lens shift, as an architectural photographer would.
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from bl.common import CACHE_DIR, FT, ft2bl  # noqa: E402

# name: (camera (x, y, z) ft, target (x, z) ft for the yaw, horizontal FOV deg, shift_y)
SHOTS = {
    # straight-on street elevation from the far side of the street
    'front': ((20.0, 4.4, 104.0), (20.0, 40.0), 58.0, 0.10),
    # three-quarter street view from the south-east (garage door, drive, entry, bay)
    'front34': ((60.0, 4.6, 100.0), (20.0, 48.0), 60.0, 0.08),
    # back garden from the rear planting bed toward the deck and the living-room glazing
    'back': ((16.2, 5.2, -12.0), (31.0, -1.0), 84.0, 0.02),
    # back garden, full rear elevation from the same spot
    'backwide': ((16.2, 5.2, -12.0), (16.2, 0.0), 100.0, 0.04),
}


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', default='front34,front,back,backwide')
    ap.add_argument('--width', type=int, default=1600)
    ap.add_argument('--height', type=int, default=0)
    ap.add_argument('--samples', type=int, default=128)
    ap.add_argument('--out', default=os.path.join(CACHE_DIR, 'dev_exterior'))
    ap.add_argument('--exposure', default='auto')
    return ap.parse_args(argv)


def setup(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    cy = sc.cycles
    cy.device = 'GPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.01
    cy.use_denoising = True
    cy.max_bounces = 12
    cy.transparent_max_bounces = 24
    cy.sample_clamp_indirect = 12.0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Base Contrast'
    except TypeError:
        pass
    try:
        sc.view_settings.use_white_balance = True
        sc.view_settings.white_balance_temperature = 7600
        sc.view_settings.white_balance_tint = 10.0
    except AttributeError:
        pass
    sc.render.image_settings.file_format = 'PNG'


def camera(pos, target, hfov, shift_y):
    cd = bpy.data.cameras.get('TG HeroCam') or bpy.data.cameras.new('TG HeroCam')
    cam = bpy.data.objects.get('TG HeroCam') or bpy.data.objects.new('TG HeroCam', cd)
    if cam.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(cam)
    cd.type = 'PERSP'
    cd.sensor_fit = 'HORIZONTAL'
    cd.angle = math.radians(hfov)
    cd.shift_y = shift_y
    cd.clip_start = 0.05
    cd.clip_end = 1000
    cam.location = ft2bl(*pos)
    tx, tz = target
    yaw = math.atan2(tx - pos[0], -(tz - pos[2]))           # app convention: 0 = north (-z), +pi/2 = east
    d = Vector((math.sin(yaw), math.cos(yaw), 0.0))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.camera = cam
    return cam, math.degrees(yaw)


def render(path, w, h):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def auto_ev(out):
    sc = bpy.context.scene
    keep = sc.cycles.samples, sc.view_settings.view_transform
    sc.cycles.samples = 16
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0
    sc.render.image_settings.file_format = 'OPEN_EXR'
    p = os.path.join(out, '_hero_probe.exr')
    render(p, 320, 200)
    img = bpy.data.images.load(p)
    px = list(img.pixels)
    lum = sorted(0.2126 * px[i] + 0.7152 * px[i + 1] + 0.0722 * px[i + 2] for i in range(0, len(px), 4))
    bpy.data.images.remove(img)
    os.remove(p)
    sc.cycles.samples, sc.view_settings.view_transform = keep
    sc.render.image_settings.file_format = 'PNG'
    med = max(lum[len(lum) // 2], 1e-5)
    return max(-4.0, min(4.0, math.log2(0.30 / med)))


def main():
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    setup(a.samples)
    h = a.height or int(a.width * 2 / 3)
    for s in a.shots.split(','):
        pos, tgt, fov, shift = SHOTS[s]
        cam, yaw = camera(pos, tgt, fov, shift)
        ev = auto_ev(a.out) if a.exposure == 'auto' else float(a.exposure)
        bpy.context.scene.view_settings.exposure = ev
        p = os.path.join(a.out, f'hero_{s}.png')
        render(p, a.width, h)
        print(f'[hero] {s}: cam {pos} yaw {yaw:.1f} deg hfov {fov} shift_y {shift} ev {ev:+.2f} -> {p}', flush=True)


if __name__ == "__main__":
    main()
