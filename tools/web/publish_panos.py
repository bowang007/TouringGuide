#!/usr/bin/env python3
"""Publish path-traced equirectangular renders into the web tour as a three-rung resolution ladder.

Input: a directory of renders named <ID>.png (2:1 equirect, normally 8192x4096, rendered from tour
sweep <ID> with the app convention: centre column = world yaw 0 = SCENE -z, top row = up). Files that
are not sweep ids of the scene tour are ignored (`_*.png` scratch files and `*_view.png` silently).
For every render it writes, relative to the assets directory:

  panos/8k/<ID>.webp    8192x4096, only when the source is at least 8192 px wide   (--quality, default 84)
  panos/4k/<ID>.webp    4096x2048, when the source is at least 4096 px wide        (--quality-low, default 88)
  panos/2k/<ID>.webp    2048x1024 (a smaller source is published here as it is, with a warning)
  thumbs/<ID>.webp      ~512x320 rectilinear view at the sweep's yaw/pitch (75 deg h-FOV), as before

Seam: the renderer leaves a faint column at the 0/360 wrap (its edge handling touches the outermost 3-4
columns of an 8192 px render by 1-2.5 of 255 levels, tinted; on a plain wall it shows on the page as a thin
vertical line when looking straight at the wrap, world yaw +-180 degrees = due south). Before anything is
encoded the source is repaired (`repair_seam`): the low-frequency part of what the 6 columns on each side of
the wrap differ from the clean columns beyond them is taken out; detail and real edges that stand in the band
are left alone. The printout gives the step before and after ("seam 1.4 > 0.2"); --no-seam-fix publishes the
render as it is. Smaller rungs are Lanczos-downsampled from the repaired source with the wrap continued, so the
seam stays invisible at every level. Then it updates panos/manifest.json (design contract section 4.2):

  { "version": "<content hash>", "convention": "...", "widths": {"8k": 8192, "4k": 4096, "2k": 2048},
    "nodes": { "<ID>": { "offset": 0, "levels": {"8k": "8k/<ID>.webp", "4k": "4k/<ID>.webp", "2k": "2k/<ID>.webp"},
                         "thumb": "../thumbs/<ID>.webp", "source": "render" } } }

A node lists only the levels that exist; the page uses the best one present. Sweeps that are not in
the input keep their current entry ('convention', 'offset' and 'source' are preserved; entries in the
old full/half format are converted). Entries whose id is no longer a sweep of the scene tour are
dropped from the manifest; their files, level files a re-published sweep no longer lists, and stray
.webp files in the level folders and in thumbs/ (they belong to this tool) are deleted only with --prune.

Thumbnails show the view the page opens the sweep with: the sweep's own yaw and pitch (a sweep that looks
down at a vanity or at the laundry pair has that in its thumbnail). --level-thumbs clamps the pitch at
-5.7 degrees, as the page before v3 did.

The exit code is 1 when a sweep of the tour has no panorama afterwards (the page would show the bare model
there); --allow-missing makes that a note, for publishing while a render is still running.

Run with the render venv (numpy + Pillow):
  tools/render/.cache/venv/bin/python tools/web/publish_panos.py RENDER_DIR [--only L0,B3] [--prune]
  ... --repo ROOT            another root with the repository layout: its tools/render/data/scene.json is
                             read and its assets/ written (default: $SITEDATA_ROOT when set, else the
                             repository), as the other tools of tools/web do
  ... --assets /tmp/out      publish somewhere else than <root>/assets (tests)
"""
import argparse
import hashlib
import io
import json
import math
import os
import sys
import time
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
import sitedata  # noqa: E402

Image.MAX_IMAGE_PIXELS = None    # 8192x4096 and larger sources are expected
LEVELS = (('8k', 8192), ('4k', 4096), ('2k', 2048))          # best first
# Seam repair (measured on the 8192 px renders of 2026-11-20: 3-4 columns on each side, 0.7-2.5 levels):
SEAM_BAND = 6            # columns on each side of the wrap that are corrected
SEAM_REF = 4             # clean columns beyond the band, on each side, that say what the band should look like
SEAM_ROWS = 129          # rows (of 4096) of the vertical median: only what stays the same over 5.7 deg is an error
SEAM_KEEP = (3.5, 7.0)   # 8-bit levels: a deviation up to the first is removed in full, none beyond the second
CONVENTION = ('Equirectangular 2:1, top row = up (+y). Centre column = world yaw `offset` '
              '(yaw 0 = SCENE -z, plan north); u increases clockwise seen from above. '
              'Paths are relative to this file. Each node lists the resolution levels that exist; '
              'widths are in `widths`.')
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
    seam = np.abs(arr[:, 0].astype(np.float32) - arr[:, -1].astype(np.float32)).mean()
    mid = arr.shape[1] // 2
    interior = np.abs(arr[:, mid].astype(np.float32) - arr[:, mid + 1].astype(np.float32)).mean()
    return float(seam), float(interior)


def repair_seam(arr):
    """Take the renderer's faint column at the 0/360 wrap out of an equirect (H x W x 3, uint8).

    The band (SEAM_BAND columns on each side of the wrap) is compared with a straight line between the mean
    of the SEAM_REF clean columns to its left and to its right. What the band differs from that line by,
    per column and channel, is smoothed along the column with a median over SEAM_ROWS rows: on a plain
    surface that is the renderer's error (constant along the column), while texture, noise and anything
    that crosses the wrap at an angle average out. The smoothed deviation is subtracted; where it is larger
    than the renderer's error can be (SEAM_KEEP) a real vertical edge stands in the band (a door jamb, a
    mullion) and nothing is changed. Fractional corrections are dithered with a fixed seed, so the mean is
    exact and a re-run gives the same bytes.

    Returns (array, before, after): mean absolute low-frequency deviation of the band in 8-bit levels, where
    it is small enough to be the renderer's error, before and after the repair."""
    H, W = arr.shape[:2]
    band, ref = SEAM_BAND, SEAM_REF                                  # the renderer's edge is a matter of pixels
    rows = max(33, round(SEAM_ROWS * H / 4096)) | 1                  # ... the window along it one of angle
    blur = max(9, rows // 4) | 1
    if W < 8 * (band + ref) or H < 2 * rows:
        return arr, 0.0, 0.0
    idx = np.r_[W - band - ref:W, 0:band + ref]                      # the columns across the wrap, left to right
    strip = arr[:, idx].astype(np.float32)
    n = strip.shape[1]
    left, right = strip[:, :ref].mean(1), strip[:, -ref:].mean(1)
    xl, xr = (ref - 1) / 2, n - 1 - (ref - 1) / 2
    t = ((np.arange(ref, n - ref) - xl) / (xr - xl))[None, :, None]
    inner = strip[:, ref:n - ref]
    dev = inner - (left[:, None, :] * (1 - t) + right[:, None, :] * t)

    def along(v, size, fn):                                          # running fn over `size` rows, edges repeated
        pad = size // 2
        win = np.lib.stride_tricks.sliding_window_view(np.pad(v, ((pad, pad), (0, 0), (0, 0)), mode='edge'),
                                                       size, axis=0)
        return fn(win, axis=-1)
    low = along(dev, rows, np.median)
    weight = np.clip((SEAM_KEEP[1] - np.abs(low)) / (SEAM_KEEP[1] - SEAM_KEEP[0]), 0.0, 1.0)
    corr = along(low * weight, blur, np.mean)
    dither = (np.random.default_rng(0).random(corr.shape, dtype=np.float32) - 0.5) * (np.abs(corr) > 1e-3)
    out = arr.copy()
    out[:, idx[ref:n - ref]] = np.clip(np.rint(inner - corr + dither), 0, 255).astype(np.uint8)
    mine = weight > 0                                                # where the deviation can be the renderer's
    count = max(1, int(mine.sum()))
    return out, float(np.abs(low)[mine].sum() / count), float(np.abs(low - corr)[mine].sum() / count)


def resize_wrapped(im, w):
    """Lanczos-resize an equirect to width `w` (height w/2). The image is extended with wrapped columns
    first and only the original region is scaled (`box`), so the filter reads across the 0/360 seam
    instead of clamping at the image edge."""
    W, H = im.size
    if W == w:
        return im
    pad = int(math.ceil(3.0 * max(1.0, W / w))) + 2           # Lanczos support is 3 output pixels
    wide = Image.new('RGB', (W + 2 * pad, H))
    wide.paste(im.crop((W - pad, 0, W, H)), (0, 0))
    wide.paste(im, (pad, 0))
    wide.paste(im.crop((0, 0, pad, H)), (pad + W, 0))
    return wide.resize((w, w // 2), Image.LANCZOS, box=(pad, 0, pad + W, H))


def process(job):
    nid, src, o = job
    t0 = time.time()
    with open(src, 'rb') as f:                           # PNG IHDR: Pillow reports 16-bit RGB as plain 'RGB'
        head = f.read(26)
    bits = head[24] if head[:8] == b'\x89PNG\r\n\x1a\n' and len(head) >= 26 else 8
    im = Image.open(src)
    im.load()
    im = im.convert('RGB')
    W, H = im.size
    if abs(W - 2 * H) > 1:
        raise SystemExit(f'{nid}: {src} is {W}x{H}, not a 2:1 equirect')
    arr = np.asarray(im)
    seam, interior = seam_score(arr)
    fix = None
    if o['seam_fix']:
        arr, before, after = repair_seam(arr)
        fix = (round(before, 2), round(after, 2))
        im = Image.fromarray(arr)
    res = {'id': nid, 'width': W, 'height': H, 'bits': bits, 'seam': round(seam, 2), 'interior': round(interior, 2),
           'fix': fix, 'files': {}, 'levels': {}, 'sizes': {}, 'note': ''}
    rungs = [(name, w) for name, w in LEVELS if W >= w]
    if not rungs:                                          # test renders: publish the source as the smallest rung
        rungs = [(LEVELS[-1][0], W)]
        res['note'] = f'  WARNING source is only {W} px wide: published as it is in {LEVELS[-1][0]}/'
    thumb_src = None
    for name, w in rungs:
        lvl = resize_wrapped(im, w)
        q = o['quality'] if name == '8k' else o['quality_low']
        data = webp_bytes(lvl, q, o['method'], GPANO.format(w=lvl.size[0], h=lvl.size[1]))
        res['files'][name] = (f'panos/{name}/{nid}.webp', data)
        res['levels'][name] = f'{name}/{nid}.webp'
        res['sizes'][name] = lvl.size[0]
        if thumb_src is None or name == '4k':             # thumbnails are cut from the 4k rung, as before
            thumb_src = lvl
    tw, th = o['thumb_size']
    big = view(thumb_src, o['yaw'], o['pitch'], o['thumb_fov'], tw * 2, th * 2)  # nearest sampling, 2x
    thumb = big.resize((tw, th), Image.LANCZOS)
    res['files']['thumb'] = (f'thumbs/{nid}.webp', webp_bytes(thumb, o['thumb_quality'], o['method']))
    res['seconds'] = round(time.time() - t0, 1)
    return res


def upgrade_entry(e):
    """A manifest entry in the section 4.2 shape; converts the old {full, half, width} format."""
    out = {'offset': e.get('offset', 0)}
    if isinstance(e.get('levels'), dict):
        out['levels'] = {k: v for k, _ in LEVELS for v in [e['levels'].get(k)] if v}
    else:
        lv = {}
        width = int(e.get('width') or 4096)
        name = next((n for n, w in LEVELS if width >= w), LEVELS[-1][0])
        if e.get('full'):
            lv[name] = e['full']
        if e.get('half') and e.get('half') != e.get('full'):
            lv.setdefault('2k', e['half'])
        out['levels'] = {k: lv[k] for k, _ in LEVELS if k in lv}
    out['thumb'] = e.get('thumb')
    out['source'] = e.get('source', 'render')
    for k, v in e.items():                                # keep anything else another tool stored
        if k not in out and k not in ('width', 'height', 'full', 'half'):
            out[k] = v
    return out


def entry_files(e):
    """Paths (relative to the panos directory) an entry refers to."""
    return [v for v in list((e.get('levels') or {}).values()) + [e.get('thumb')] if v]


def manifest_version(nodes, panos_dir):
    h = hashlib.sha1()
    for nid, e in nodes.items():
        h.update(json.dumps([nid, e], sort_keys=True).encode())
        for rel in entry_files(e):
            f = (panos_dir / rel).resolve()
            if f.exists():
                h.update(hashlib.sha1(f.read_bytes()).digest())
    return h.hexdigest()[:12]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('renders', help='directory with <ID>.png equirect renders')
    ap.add_argument('--repo', help='root with the repository layout (default: $SITEDATA_ROOT or the repository)')
    ap.add_argument('--assets', help='assets directory to publish into (default <root>/assets)')
    ap.add_argument('--scene', help='scene.json with tour.nodes (default <root>/tools/render/data/scene.json)')
    ap.add_argument('--only', help='comma-separated sweep ids to publish')
    ap.add_argument('--quality', type=int, default=84, help='WebP quality of the 8k rung')
    ap.add_argument('--quality-low', type=int, default=88, help='WebP quality of the 4k and 2k rungs')
    ap.add_argument('--method', type=int, default=6, help='WebP effort 0-6')
    ap.add_argument('--thumb-size', default='512x320')
    ap.add_argument('--thumb-fov', type=float, default=75, help='horizontal FOV of the thumbnail (deg)')
    ap.add_argument('--thumb-quality', type=int, default=82)
    ap.add_argument('--level-thumbs', action='store_true',
                    help="clamp the thumbnail's pitch at -5.7 deg (max(pitch, -0.1 rad), the page before v3); "
                         "default: the sweep's own pitch, which is the view the page opens the sweep with")
    ap.add_argument('--raw-pitch', action='store_true', help=argparse.SUPPRESS)       # the default since v3
    ap.add_argument('--no-seam-fix', action='store_true',
                    help='publish the renders as they are, without the repair of the 0/360 wrap column')
    ap.add_argument('--allow-missing', action='store_true',
                    help='exit 0 although sweeps of the tour have no panorama (a render that is still running)')
    ap.add_argument('--prune', action='store_true',
                    help='delete the files of sweeps that left the tour and level files no entry lists any more')
    ap.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    root = sitedata.site_root(a.repo)
    assets = Path(a.assets).resolve() if a.assets else root / 'assets'
    if assets != REPO / 'assets':
        print(f'publishing into {assets}')
    panos_dir = assets / 'panos'
    scene = Path(a.scene) if a.scene else root / 'tools' / 'render' / 'data' / 'scene.json'
    nodes = {n['id']: n for n in json.loads(scene.read_text())['tour']['nodes']}
    src_dir = Path(a.renders)
    only = set(a.only.split(',')) if a.only else None
    tw, th = (int(v) for v in a.thumb_size.lower().split('x'))

    jobs = []
    for p in sorted(src_dir.glob('*.png')):
        nid = p.stem
        if nid not in nodes:
            if not (nid.startswith('_') or nid.endswith(('_view', '_sheet'))):
                print(f'skip {p.name}: not a sweep id of the tour', file=sys.stderr)
            continue
        if only and nid not in only:
            continue
        n = nodes[nid]
        yaw = float(n.get('yaw') or 0.0)
        pitch = float(n.get('pitch') or 0.0)
        if a.level_thumbs:
            pitch = max(pitch, -0.1)
        jobs.append((nid, p, dict(quality=a.quality, quality_low=a.quality_low, method=a.method,
                                  thumb_size=(tw, th), thumb_fov=a.thumb_fov, seam_fix=not a.no_seam_fix,
                                  thumb_quality=a.thumb_quality, yaw=yaw, pitch=pitch)))
    if not jobs:
        sys.exit(f'no <ID>.png renders of tour sweeps found in {src_dir}')

    manifest_path = panos_dir / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    old_entries = {nid: upgrade_entry(e) for nid, e in (manifest.get('nodes') or {}).items()}
    entries = dict(old_entries)

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=max(1, min(a.jobs, len(jobs)))) as ex:
        results = list(ex.map(process, jobs))

    total = 0
    per_level = {}
    for r in results:
        nid = r['id']
        warn = r['note']
        if r['seam'] > 3 * r['interior'] + 4:
            warn += f'  WARNING seam step {r["seam"]} vs interior {r["interior"]}: check the 0/360 wrap'
        for key, (rel, data) in r['files'].items():
            total += len(data)
            per_level[key] = per_level.get(key, 0) + len(data)
            if not a.dry_run:
                p = assets / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
        sizes = '  '.join(f'{k} {len(r["files"][k][1]) / 1024:.0f} KB' for k, _ in LEVELS if k in r['files'])
        seam = f'  seam {r["fix"][0]} > {r["fix"][1]}' if r['fix'] else ''
        print(f'{nid}: {r["width"]}x{r["height"]} {r["bits"]}-bit  {sizes}  '
              f'thumb {len(r["files"]["thumb"][1]) / 1024:.0f} KB{seam}  ({r["seconds"]} s){warn}')
        prev = old_entries.get(nid, {})
        entries[nid] = {'offset': 0, 'levels': {k: r['levels'][k] for k, _ in LEVELS if k in r['levels']},
                        'thumb': f'../thumbs/{nid}.webp', 'source': 'render'}
        for k, v in prev.items():                         # fields other tools added survive a re-publish
            entries[nid].setdefault(k, v)

    dropped = [nid for nid in entries if nid not in nodes]
    kept = {nid: entries[nid] for nid in nodes if nid in entries}          # tour order
    # files that no entry lists any more: dropped sweeps, and levels a re-published sweep lost
    listed = {rel for e in kept.values() for rel in entry_files(e)}
    stale = sorted({rel for e in old_entries.values() for rel in entry_files(e)} - listed)
    # strays in the level folders and the thumbnail folder (they belong to this tool)
    for name in [n for n, _ in LEVELS] + ['../thumbs']:
        d = panos_dir / name
        if d.is_dir():
            stale += [f'{name}/{f.name}' for f in sorted(d.glob('*.webp')) if f'{name}/{f.name}' not in listed
                      and f'{name}/{f.name}' not in stale]
    if dropped:
        print(f'dropped from the manifest (not in the scene tour): {", ".join(dropped)}')
    removed = 0
    if stale:
        if a.prune:
            for rel in stale:
                f = (panos_dir / rel).resolve()
                if f.is_file() and assets in f.parents:
                    removed += 1
                    if not a.dry_run:
                        f.unlink()
            print(f'pruned {removed} stale files' + (' (dry run)' if a.dry_run else ''))
        else:
            print(f'{len(stale)} stale files left in place (use --prune to delete them): '
                  + ', '.join(stale[:8]) + (' ...' if len(stale) > 8 else ''))

    out = {'version': manifest_version(kept, panos_dir),
           'convention': manifest.get('convention') if 'levels' in str(manifest.get('convention', '')) else CONVENTION,
           'widths': {name: w for name, w in LEVELS},
           'nodes': kept}
    for k, v in manifest.items():                         # keep top-level fields other tools added
        out.setdefault(k, v)
    have = {name: sum(1 for e in kept.values() if name in e['levels']) for name, _ in LEVELS}
    print(f'published {len(results)} panos in {time.time() - t0:.0f} s ({total / 1e6:.1f} MB: '
          + ', '.join(f'{k} {v / 1e6:.1f} MB' for k, v in per_level.items()) + '); '
          f'manifest {manifest.get("version")} -> {out["version"]}; {len(kept)} sweeps, levels '
          + ', '.join(f'{k}: {v}' for k, v in have.items())
          + (' (dry run, nothing written)' if a.dry_run else ''))
    missing = [nid for nid in nodes if nid not in kept]
    partial = [nid for nid in kept if list(kept[nid]['levels']) != [name for name, _ in LEVELS]]
    if not a.dry_run:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    if partial:
        print(f'note: {len(partial)} sweeps do not have all three levels: {", ".join(partial)}')
    if missing:
        print(('note' if a.allow_missing else 'MISSING') + f': {len(missing)} sweeps of the tour have no panorama: '
              + ', '.join(missing))
        return 0 if a.allow_missing else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
