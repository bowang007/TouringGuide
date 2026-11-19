"""Render the path-traced exterior orbit: perspective frames on rings around the house (runs in Blender).

  blender -b tools/render/.cache/house.blend --python tools/render/render_exterior.py -- \
      [--only o00,h03] [--width 3000] [--samples 512] [--out tools/render/.cache/exterior] [--ev -1.9]

The site's Exterior view orbits a fixed target. Each frame is rendered from an orbit position the page can
reach exactly (eye = target + radius * (sin t cos p, sin p, cos t cos p), aiming at the target, up = +y),
so on a frame the page shows the render pixel for pixel, and between frames it projects the two nearest
frames onto the baked model (assets/js/house3d.js). Frames are wider than the screen (90 deg horizontal,
3:2) so any window shape is a crop of the frame.

All frames share one exposure and white balance (probed once at the front frame), so neighbouring frames
blend without a step. Writes <out>/<id>.png and <out>/frames.json; existing frames are skipped unless
--force.
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from bl.common import CACHE_DIR, ft2bl  # noqa: E402

sys.argv = [sys.argv[0]] + (['--'] + sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
import render_panos as rp  # noqa: E402  (re-uses setup_cycles / set_look / probe)

# Orbit target (SCENE feet): the middle of the house footprint at about window-head height.
TARGET = (19.71, 4.6, 27.8)
# Rings: (prefix, elevation phi (rad), radius (ft), frames, first theta (rad)). theta 0 looks at the street
# front (from +z), +pi/2 from the east (garage side), pi from the garden, -pi/2 from the west.
RINGS = (
    ('o', 0.50, 95.0, 24, 0.0),           # drone height (~50 ft, sees past the side neighbours' roofs), every 15 deg
    ('h', 1.05, 105.0, 8, -math.pi / 4),  # roof overview (~95 ft), every 45 deg
)
HFOV_DEG = 90.0
ASPECT = 1.5
WB = (6300.0, 4.0)          # the hero stills' daylight balance
EV_BIAS = 0.5               # (the street-level hero still uses -0.6; from the air the probe sees bright sky
                            #  over dark roofs and lawns, which reads underexposed without a lift)


def frames():
    out = []
    for prefix, phi, radius, n, t0 in RINGS:
        for k in range(n):
            th = t0 + 2 * math.pi * k / n
            th = math.atan2(math.sin(th), math.cos(th))
            eye = [TARGET[0] + radius * math.sin(th) * math.cos(phi), TARGET[1] + radius * math.sin(phi),
                   TARGET[2] + radius * math.cos(th) * math.cos(phi)]
            out.append(dict(id=f'{prefix}{k:02d}', ring=prefix, theta=round(th, 6), phi=phi, radius=radius,
                            target=list(TARGET), eye=[round(v, 4) for v in eye], aim=list(TARGET),
                            hfov=HFOV_DEG, aspect=ASPECT))
    return out


def aim_camera(cam, eye, aim, hfov_deg):
    cam.location = ft2bl(*eye)
    cam.data.type = 'PERSP'
    cam.data.sensor_fit = 'HORIZONTAL'
    cam.data.angle = math.radians(hfov_deg)
    cam.data.shift_x = cam.data.shift_y = 0.0
    d = (ft2bl(*aim) - ft2bl(*eye)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def _include_far():
    """Turn on the far neighbourhood (bl/zones/exterior_far.py), excluded from the view layer by default."""
    def walk(lc):
        if lc.collection.name == 'ext_far':
            lc.exclude = False
            return True
        return any(walk(ch) for ch in lc.children)
    if not any(walk(vl.layer_collection) for vl in bpy.context.scene.view_layers):
        print('[exterior] WARNING: no ext_far collection (scene built before exterior_far existed)', flush=True)


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default=None)
    ap.add_argument('--width', type=int, default=3000)
    ap.add_argument('--samples', type=int, default=512)
    ap.add_argument('--out', default=os.path.join(CACHE_DIR, 'exterior'))
    ap.add_argument('--ev', type=float, default=None, help='fixed exposure (default: probe at the front frame)')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    rp.setup_cycles(a.samples)
    rp.set_look('AgX - Base Contrast')
    from bl import lighting
    lighting.apply_balance(None, None, None, None)
    cam = rp.make_camera()
    cam.data.clip_end = 6000.0              # the far neighbourhood's hills stand ~2.5 miles out
    sc = bpy.context.scene
    _include_far()
    sc.render.image_settings.file_format = 'PNG'
    fr = frames()
    if a.ev is None:
        front = fr[0]
        cam.location = ft2bl(*front['eye'])
        rp.as_pano(cam)
        ev, _, _ = rp.probe(cam, front['id'], a.out, None)
        ev += EV_BIAS
    else:
        ev = a.ev
    rp.set_wb(*WB)
    sc.view_settings.exposure = ev
    w = a.width
    h = int(round(w / ASPECT))
    print(f'[exterior] {len(fr)} frames {w}x{h} ev={ev:+.2f} wb={WB[0]:.0f}K/{WB[1]:+.1f}', flush=True)
    only = set(a.only.split(',')) if a.only else None
    for f in fr:
        f.update(width=w, height=h, ev=round(ev, 3), wb=list(WB))
        path = os.path.join(a.out, f'{f["id"]}.png')
        if (only and f['id'] not in only) or (os.path.exists(path) and not a.force):
            continue
        aim_camera(cam, f['eye'], f['aim'], f['hfov'])
        t = time.time()
        rp.render_to(path, w, h)
        print(f'[exterior] {f["id"]} theta={math.degrees(f["theta"]):+.0f} phi={math.degrees(f["phi"]):.0f} '
              f'{time.time() - t:.1f}s', flush=True)
    with open(os.path.join(a.out, 'frames.json'), 'w') as fh:
        json.dump({'target': list(TARGET), 'frames': fr}, fh, indent=1)


main()
