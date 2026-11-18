"""Render perspective hero stills (landing hero, design panel) with the panorama look.

  blender -b tools/render/.cache/house.blend --python tools/render/render_heroes.py -- \
      [--only front,K0] [--width 2400] [--samples 1024] [--out tools/render/.cache/heroes]

Cameras live in data/hero_cameras.json: {key: {eye:[x,y,z] ft, aim:[x,y,z] ft, fov_deg (horizontal),
aspect, exposure ('auto' or stops), exposure_bias, optional wb [kelvin, tint]}}. Exposure and white
balance come from the same probe as the panoramas.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from bl.common import CACHE_DIR, DATA_DIR, ft2bl  # noqa: E402

sys.argv = [sys.argv[0]] + (['--'] + sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
import render_panos as rp  # noqa: E402  (re-uses setup_cycles / set_look / auto exposure)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None)
    ap.add_argument('--width', type=int, default=2400)
    ap.add_argument('--samples', type=int, default=1024)
    ap.add_argument('--out', default=os.path.join(CACHE_DIR, 'heroes'))
    ap.add_argument('--interior-gain', type=float, default=None)
    ap.add_argument('--sky-gain', type=float, default=None)
    ap.add_argument('--sun-gain', type=float, default=None)
    ap.add_argument('--emission-gain', type=float, default=None)
    a = ap.parse_args(argv)
    cams = json.load(open(os.path.join(DATA_DIR, 'hero_cameras.json')))
    if a.only:
        cams = {k: v for k, v in cams.items() if k in a.only.split(',')}
    os.makedirs(a.out, exist_ok=True)
    rp.setup_cycles(a.samples)
    rp.set_look('AgX - Base Contrast')
    from bl import lighting
    lighting.apply_balance(a.interior_gain, a.sky_gain, a.sun_gain, a.emission_gain)
    cam = rp.make_camera()
    sc = bpy.context.scene
    for key, c in cams.items():
        eye, aim = c['eye'], c['aim']
        cam.location = ft2bl(*eye)
        cam.data.type = 'PERSP'
        cam.data.sensor_fit = 'HORIZONTAL'
        cam.data.angle = math.radians(c.get('fov_deg', 70))
        d = (ft2bl(*aim) - ft2bl(*eye)).normalized()
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        try:
            cam.data.shift_y = c.get('shift_y', 0.0)
        except AttributeError:
            pass
        sc.render.image_settings.file_format = 'PNG'
        # probe with the pano camera at the eye (exposure + white balance), then restore the camera
        loc, rot, typ, ang = cam.location.copy(), cam.rotation_euler.copy(), cam.data.type, cam.data.angle
        rp.as_pano(cam)
        mask = rp.white_masks(cam, {key: cam.location.copy()}, a.out)[key] if 'wb' not in c else None
        rp.as_pano(cam)
        ev, wb, _ = rp.probe(cam, key, a.out, mask)
        cam.data.type, cam.data.angle = typ, ang
        cam.location, cam.rotation_euler = loc, rot
        ev = ev + c.get('exposure_bias', 0.0) if c.get('exposure', 'auto') == 'auto' else float(c['exposure'])
        wb = tuple(c['wb']) if 'wb' in c else (wb or rp.WB_DEFAULT)
        rp.set_wb(*wb)
        sc.view_settings.exposure = ev
        h = int(a.width / c.get('aspect', 1.5))
        rp.render_to(os.path.join(a.out, f'{key}.png'), a.width, h)
        print(f'[hero] {key} ev={ev:+.2f} wb={wb[0]:.0f}K/{wb[1]:+.1f}', flush=True)


main()
