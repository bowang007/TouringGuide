"""Build the modern, path-traceable house scene and save it as a .blend.

Usage (headless):
  blender -b --factory-startup --python tools/render/build_scene.py -- \
      [--out tools/render/.cache/house.blend] [--zones all|none|kitchen,living,...] [--no-exterior]

Zone modules live in bl/zones/<name>.py and expose build(ctx).
"""
import argparse
import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from bl import common, lighting, shell  # noqa: E402

ZONES = ['kitchen_dining', 'living', 'primary_suite', 'bedrooms', 'baths', 'hall_entry_garage', 'exterior']


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(common.CACHE_DIR, 'house.blend'))
    ap.add_argument('--zones', default='all')
    ap.add_argument('--hdri', default=None)
    ap.add_argument('--strict', action='store_true', help='fail on a zone error (final builds)')
    return ap.parse_args(argv)


def main():
    a = parse()
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ctx = common.Ctx()
    print('shell:', shell.build(ctx))
    zones = ZONES if a.zones == 'all' else ([] if a.zones == 'none' else a.zones.split(','))
    zones = list(dict.fromkeys(z.strip() for z in zones if z.strip()))     # building a zone twice duplicates it
    for z in zones:
        path = os.path.join(HERE, 'bl', 'zones', z + '.py')
        if not os.path.exists(path):
            print(f'zone {z}: module missing, skipped')
            continue
        tz = time.time()
        try:
            mod = importlib.import_module(f'bl.zones.{z}')
            res = mod.build(ctx)
        except Exception:
            if a.strict:
                raise
            import traceback
            traceback.print_exc()
            print(f'zone {z}: FAILED, skipped (use --strict to stop on errors)')
            continue
        print(f'zone {z}: {res} ({time.time() - tz:.1f}s)')
    from bl import warp
    print('warp:', warp.warp())               # concept plan -> architect's plan (sizes/sizes.pdf)
    from bl import revisions
    print('revisions:', revisions.apply(ctx))   # owner's design changes on the new plan
    lighting.setup_daylight(ctx, a.hdri)
    print('portals:', lighting.add_window_portals(ctx))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=False)
    print(f'saved {a.out} in {time.time() - t0:.1f}s; objects={len(bpy.data.objects)}')


main()
