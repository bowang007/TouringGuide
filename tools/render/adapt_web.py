"""Per-stop eye adaptation for the real-time 3D walk -> assets/model/adapt.json.

The web bake (bake_web.py) uses one interior exposure and white balance for the whole house: the
medians of the values the panorama renders chose. A dim bedroom therefore looks darker and warmer
in the 3D walk than in its own panorama, which was exposed and balanced for that stop.

This script measures how a mid-tone patch with the colour of the stop's white paint displays
through Blender's own colour pipeline (AgX, look, white balance):
  * d_house: under the bake's settings;
  * d_stop: under the stop's own settings.
It does the same for the outdoor groups ('ko'), from the bake's exterior exposure / white balance.
It stores the per-channel gain k of the highlight-preserving curve

    f(x) = k x / (1 + (k - 1) x)      (x = linear display colour; f(0) = 0, f(1) = 1)

that maps d_house to d_stop. Windows and lamps keep their highlights. In walk mode the page eases
the model towards the k of the nearest visible stop (assets/js/house3d.js, setAdaptation). That is
the real-time equivalent of a camera's (or an eye's) auto exposure, and makes every room match its
panorama.

  blender -b .cache/house.blend --python adapt_web.py -- \
      --meta .cache/panos/render_meta.json --out ../../assets/model/adapt.json

Pass the same --exposure-int as bake_web.py if you overrode it there. It only reads the colour
management settings, so it takes a few seconds.
"""
import argparse
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

from bl.common import CACHE_DIR, DATA_DIR  # noqa: E402

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
sys.argv = [sys.argv[0]]
import render_panos as rp  # noqa: E402  (TARGET_MEDIAN, set_wb, set_look; main() is guarded)

LUMA = (0.2126, 0.7152, 0.0722)
K_LIMITS = (0.25, 4.0)
KO_LIMITS = (0.25, 16.0)


def _srgb_to_linear(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def display_linear(rgb, exposure, wb, tmpdir):
    """Linear display RGB (what three.js sees after decoding the sRGB texture) of the scene-linear
    colour `rgb` under view exposure `exposure` and white balance `wb` = (kelvin, tint)."""
    import numpy as np
    import OpenImageIO as oiio
    sc = bpy.context.scene
    img = bpy.data.images.get('_tg_adapt') or bpy.data.images.new('_tg_adapt', 4, 4, float_buffer=True, alpha=False)
    try:
        img.colorspace_settings.name = 'Linear Rec.709'
    except TypeError:
        pass
    img.pixels.foreach_set(np.tile(np.r_[np.asarray(rgb, dtype=np.float64), 1.0], 16).astype(np.float32))
    st, vs = sc.render.image_settings, sc.view_settings
    st.file_format, st.color_depth = 'PNG', '16'
    vs.exposure = float(exposure)
    rp.set_wb(*wb)
    path = os.path.join(tmpdir, '_tg_adapt.png')
    img.save_render(path, scene=sc)
    inp = oiio.ImageInput.open(path)
    px = np.asarray(inp.read_image(0, 0, 0, 3, oiio.FLOAT)).reshape(-1, 3).mean(0)
    inp.close()
    return [_srgb_to_linear(float(v)) for v in px]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--meta', default=os.path.join(CACHE_DIR, 'panos', 'render_meta.json'))
    ap.add_argument('--out', default=os.path.join(HERE, '..', '..', 'assets', 'model', 'adapt.json'))
    ap.add_argument('--exposure-int', type=float, default=None, help='bake_web.py --exposure-int, if overridden')
    ap.add_argument('--exposure-ext', type=float, default=-1.2, help='bake_web.py --exposure-ext')
    ap.add_argument('--wb-ext', default='8000,-8', help='bake_web.py --wb-ext')
    ap.add_argument('--look', default='AgX - Base Contrast')
    a = ap.parse_args(ARGS)

    meta = json.load(open(a.meta))
    nodes = {n['id'] for n in json.load(open(os.path.join(DATA_DIR, 'scene.json')))['tour']['nodes']}

    def med(vals, default):                      # same rule as bake_web.py
        vals = sorted(vals)
        return vals[len(vals) // 2] if vals else default
    house_wb = (med([v['wb'][0] for v in meta.values() if 'wb' in v], 6000.0),
                med([v['wb'][1] for v in meta.values() if 'wb' in v], 0.0))
    house_ev = a.exposure_int if a.exposure_int is not None else med([v['exposure'] for v in meta.values()], 0.5)

    wb_ext = tuple(float(v) for v in a.wb_ext.split(','))
    sc = bpy.context.scene
    sc.view_settings.view_transform = 'AgX'
    rp.set_look(a.look)
    out = {'house': {'exposure': round(house_ev, 3), 'wb': [round(house_wb[0]), round(house_wb[1], 2)]},
           'curve': 'per channel on linear display colour: k*x / (1 + (k-1)*x)', 'nodes': {}}
    with tempfile.TemporaryDirectory() as tmp:
        for nid, m in sorted(meta.items()):
            if nid not in nodes or 'exposure' not in m:
                continue
            ev, wb = m['exposure'], tuple(m.get('wb') or house_wb)
            white = (m.get('probe') or {}).get('white_rgb') or [1.0, 1.0, 1.0]
            lum = sum(c * w for c, w in zip(white, LUMA))
            patch = [c * rp.TARGET_MEDIAN * 2.0 ** -ev / lum for c in white]   # the stop's median, white-paint hue
            dh = display_linear(patch, house_ev, house_wb, tmp)
            dn = display_linear(patch, ev, wb, tmp)
            k = []
            for h, n in zip(dh, dn):
                h, n = min(max(h, 0.02), 0.98), min(max(n, 0.02), 0.98)
                k.append(round(min(max(n * (1 - h) / (h * (1 - n)), K_LIMITS[0]), K_LIMITS[1]), 3))
            # outdoor groups (roof, facades, site) were baked at the exterior exposure / white balance:
            # map a sunlit mid-grey from that to this stop's settings (bright and pale through a window)
            grey = [rp.TARGET_MEDIAN * 2.0 ** -a.exposure_ext] * 3
            de = display_linear(grey, a.exposure_ext, wb_ext, tmp)
            dn = display_linear(grey, ev, wb, tmp)
            ko = []
            for h, n in zip(de, dn):
                h, n = min(max(h, 0.02), 0.98), min(max(n, 0.02), 0.98)
                ko.append(round(min(max(n * (1 - h) / (h * (1 - n)), KO_LIMITS[0]), KO_LIMITS[1]), 3))
            out['nodes'][nid] = {'k': k, 'ko': ko, 'ev': round(ev, 2), 'wb': [round(wb[0]), round(wb[1], 1)]}
            print(f'[adapt] {nid} ev {ev:+.2f} wb {wb[0]:.0f}K/{wb[1]:+.1f} -> k {k} ko {ko}')
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, 'w') as f:
        json.dump(out, f, separators=(',', ':'))
    print(f'[adapt] wrote {a.out}: {len(out["nodes"])} stops, house ev {house_ev:+.2f} wb {house_wb[0]:.0f}K/{house_wb[1]:+.1f}')


if __name__ == '__main__':
    main()
