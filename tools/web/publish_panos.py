#!/usr/bin/env python3
"""Publish path-traced equirectangular renders into the web tour.

Input: a directory of renders named <ID>.png (2:1 equirect, normally 4096x2048, rendered from
tour node <ID> with the app convention: centre column = world yaw 0 = SCENE -z, top row = up,
i.e. PHOTO_VIEWS offset 0). For every render it writes

  assets/panos/<ID>.webp       full resolution (WebP q88, method 6, GPano XMP)
  assets/panos/2k/<ID>.webp    2048x1024 rung of the resolution ladder (low-memory devices,
                               MAX_TEXTURE_SIZE < full width, ?pano=2k)
  assets/thumbs/<ID>.webp      ~512x320 rectilinear view at the node's yaw/pitch (75 deg h-FOV)

and updates assets/panos/manifest.json: offset 0, sizes, paths, source "render" and a new
content-hash version (the page appends ?v=<version> to every pano/thumb URL). Nodes that are
not in the input keep their current manifest entry.

Run with the render venv (numpy + Pillow):
  tools/render/.cache/venv/bin/python tools/web/publish_panos.py RENDER_DIR [--only L0,B3]
Undo (back to the embedded placeholders):
  python3 tools/web/extract_assets.py --from-head --force-placeholders
"""
import argparse
import io
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image

sys.dont_write_bytecode = True  # keep tools/web free of __pycache__
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools' / 'render'))
sys.path.insert(0, str(HERE))
from pano_views import view  # noqa: E402  rectilinear cut-out in the app convention
from extract_assets import ASSETS, dump_manifest  # noqa: E402

GPANO = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
         '<rdf:Description rdf:about="" xmlns:GPano="http://ns.google.com/photos/1.0/panorama/" '
         'GPano:ProjectionType="equirectangular" GPano:UsePanoramaViewer="True" '
         'GPano:FullPanoWidthPixels="{w}" GPano:FullPanoHeightPixels="{h}" '
         'GPano:CroppedAreaImageWidthPixels="{w}" GPano:CroppedAreaImageHeightPixels="{h}" '
         'GPano:CroppedAreaLeftPixels="0" GPano:CroppedAreaTopPixels="0"/></rdf:RDF></x:xmpmeta>')


def webp_bytes(im, quality, method, xmp=None):
    buf = io.BytesIO()
    kw = dict(format='WEBP', quality=quality, method=method)
    if xmp:
        try:
            im.save(buf, xmp=xmp.encode(), **kw)
            return buf.getvalue()
        except TypeError:  # older Pillow without xmp support for WebP
            buf = io.BytesIO()
    im.save(buf, **kw)
    return buf.getvalue()


def seam_score(arr):
    """Mean abs difference across the 0/360 seam relative to a typical interior column step."""
    a = arr.astype(np.float32)
    seam = np.abs(a[:, 0] - a[:, -1]).mean()
    mid = a.shape[1] // 2
    interior = np.abs(a[:, mid] - a[:, mid + 1]).mean()
    return float(seam), float(interior)


def process(job):
    nid, src, out, o = job
    im = Image.open(src)
    im.load()
    im = im.convert('RGB')
    W, H = im.size
    if abs(W - 2 * H) > 1:
        raise SystemExit(f'{nid}: {src} is {W}x{H}, not a 2:1 equirect')
    arr = np.asarray(im)
    seam, interior = seam_score(arr)
    res = {'id': nid, 'width': W, 'height': H, 'seam': round(seam, 2), 'interior': round(interior, 2), 'files': {}}

    full = webp_bytes(im, o['quality'], o['method'], GPANO.format(w=W, h=H))
    res['files']['full'] = (f'{ASSETS}/panos/{nid}.webp', full)

    if W > o['half_width']:
        hw = o['half_width']
        half_im = im.resize((hw, hw // 2), Image.LANCZOS)
        res['files']['half'] = (f'{ASSETS}/panos/2k/{nid}.webp', webp_bytes(half_im, o['quality'], o['method']))

    tw, th = o['thumb_size']
    big = view(im, o['yaw'], o['pitch'], o['thumb_fov'], tw * 2, th * 2)  # nearest sampling, 2x
    thumb = big.resize((tw, th), Image.LANCZOS)
    res['files']['thumb'] = (f'{ASSETS}/thumbs/{nid}.webp', webp_bytes(thumb, o['thumb_quality'], o['method']))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('renders', help='directory with <ID>.png equirect renders')
    ap.add_argument('--repo', default=str(REPO))
    ap.add_argument('--scene', help='scene.json with tour.nodes (default tools/render/data/scene.json)')
    ap.add_argument('--only', help='comma-separated node ids to publish')
    ap.add_argument('--quality', type=int, default=88)
    ap.add_argument('--method', type=int, default=6)
    ap.add_argument('--half-width', type=int, default=2048)
    ap.add_argument('--thumb-size', default='512x320')
    ap.add_argument('--thumb-fov', type=float, default=75, help='horizontal FOV of the thumbnail (deg)')
    ap.add_argument('--thumb-quality', type=int, default=82)
    ap.add_argument('--raw-pitch', action='store_true',
                    help="use node pitch as-is (default clamps like the app's opening view: max(pitch,-0.1))")
    ap.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    root = Path(a.repo).resolve()
    scene = Path(a.scene) if a.scene else root / 'tools' / 'render' / 'data' / 'scene.json'
    nodes = {n['id']: n for n in json.loads(scene.read_text())['tour']['nodes']}
    src_dir = Path(a.renders)
    only = set(a.only.split(',')) if a.only else None
    tw, th = (int(v) for v in a.thumb_size.lower().split('x'))

    jobs = []
    for p in sorted(src_dir.glob('*.png')):
        nid = p.stem
        if nid not in nodes:
            print(f'skip {p.name}: not a tour node id', file=sys.stderr)
            continue
        if only and nid not in only:
            continue
        n = nodes[nid]
        yaw = float(n.get('yaw') or 0.0)
        pitch = float(n.get('pitch') or 0.0)
        if not a.raw_pitch:
            pitch = max(pitch, -0.1)
        jobs.append((nid, p, root, dict(quality=a.quality, method=a.method, half_width=a.half_width,
                                         thumb_size=(tw, th), thumb_fov=a.thumb_fov,
                                         thumb_quality=a.thumb_quality, yaw=yaw, pitch=pitch)))
    if not jobs:
        sys.exit(f'no <ID>.png renders found in {src_dir}')

    manifest_path = root / ASSETS / 'panos' / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'nodes': {}}
    entries = dict(manifest.get('nodes', {}))

    with ProcessPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        results = list(ex.map(process, jobs))

    total = 0
    for r in results:
        nid = r['id']
        warn = ''
        if r['seam'] > 3 * r['interior'] + 4:
            warn = f'  WARNING seam step {r["seam"]} vs interior {r["interior"]}: check the 0/360 wrap'
        if r['width'] & (r['width'] - 1):
            warn += '  note: width is not a power of two (no mipmaps in WebGL1)'
        for key, (rel, data) in r['files'].items():
            total += len(data)
            if not a.dry_run:
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
        full_kb = len(r['files']['full'][1]) / 1024
        half_kb = len(r['files']['half'][1]) / 1024 if 'half' in r['files'] else 0
        print(f'{nid}: {r["width"]}x{r["height"]}  full {full_kb:.0f} KB  2k {half_kb:.0f} KB  '
              f'thumb {len(r["files"]["thumb"][1]) / 1024:.0f} KB{warn}')
        entries[nid] = {
            'offset': 0, 'width': r['width'], 'height': r['height'],
            'full': f'{nid}.webp', 'half': f'2k/{nid}.webp' if 'half' in r['files'] else f'{nid}.webp',
            'thumb': f'../thumbs/{nid}.webp', 'source': 'render',
        }

    order = [nid for nid in nodes if nid in entries] + [nid for nid in entries if nid not in nodes]
    out = dump_manifest({nid: entries[nid] for nid in order}, root)
    rendered = sum(1 for e in out['nodes'].values() if e.get('source') == 'render')
    print(f'published {len(results)} panos ({total / 1e6:.1f} MB); manifest {manifest.get("version")} -> '
          f'{out["version"]}; {rendered}/{len(out["nodes"])} nodes rendered'
          + (' (dry run, nothing written)' if a.dry_run else ''))
    if not a.dry_run:
        manifest_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
