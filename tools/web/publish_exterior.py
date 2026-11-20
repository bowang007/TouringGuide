#!/usr/bin/env python3
"""Publish the path-traced exterior orbit frames (tools/render/render_exterior.py) into the web tour.

Input: a directory holding frames.json and <id>.png for every frame. Writes
  assets/exterior/<id>.webp        full resolution (normally 3000x2000, WebP q84, method 6)
  assets/exterior/half/<id>.webp   half resolution (shown while orbiting and on low-memory devices)
  assets/exterior/manifest.json    {version, target, hfov, aspect, frames: [{id, ring, theta, phi, radius,
                                    width, height, full, half}]}; paths are relative to the manifest and
                                    version is a content hash (the page appends ?v=<version>).

The page reproduces each frame's camera exactly (eye = target + radius * (sin theta cos phi, sin phi,
cos theta cos phi), looking at target, up +y, horizontal FOV hfov at aspect width/height).

Frame files of an earlier run that the new frames.json no longer names are reported; --prune deletes them.
A folder that mixes two runs is refused before anything is written: frames of different sizes, or frames newer
than frames.json (the render writes it last, so that is a render still running or interrupted; --force).

Run with the render venv (Pillow):
  tools/render/.cache/venv/bin/python tools/web/publish_exterior.py tools/render/.cache/exterior [--prune]
  ... --repo ROOT    publish into another root with the repository layout (default: $SITEDATA_ROOT when set,
                     else the repository), as the other tools of tools/web do
"""
import argparse
import hashlib
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from PIL import Image

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

REPO = Path(__file__).resolve().parents[1].parent
OUT = 'assets/exterior'


def webp(im, quality, method):
    buf = io.BytesIO()
    im.save(buf, format='WEBP', quality=quality, method=method)
    return buf.getvalue()


def process(job):
    fid, src, q, method, half_div = job
    im = Image.open(src)
    im.load()
    im = im.convert('RGB')
    w, h = im.size
    half = im.resize((w // half_div, h // half_div), Image.LANCZOS)
    return fid, w, h, webp(im, q, method), webp(half, q - 4, method)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('renders', help='directory with frames.json and <id>.png')
    ap.add_argument('--repo', help='root to publish into (default: $SITEDATA_ROOT or the repository)')
    ap.add_argument('--prune', action='store_true', help='delete frame files the new frames.json does not name')
    ap.add_argument('--force', action='store_true', help='publish although frames are newer than frames.json')
    ap.add_argument('--quality', type=int, default=84)
    ap.add_argument('--method', type=int, default=6)
    ap.add_argument('--half', type=int, default=2, help='half rung divisor')
    ap.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    a = ap.parse_args()
    src = Path(a.renders)
    meta = json.loads((src / 'frames.json').read_text())
    frames = meta['frames']
    missing = [f['id'] for f in frames if not (src / f'{f["id"]}.png').exists()]
    if missing:
        raise SystemExit(f'missing renders: {", ".join(missing)}')
    # render_exterior.py writes frames.json after the last frame: a frame newer than it is a render that is
    # still running or was interrupted, i.e. frames of two runs side by side
    stamp = (src / 'frames.json').stat().st_mtime
    newer = [f['id'] for f in frames if (src / f'{f["id"]}.png').stat().st_mtime > stamp + 2]
    if newer and not a.force:
        raise SystemExit('%d frames are newer than frames.json (%s): the exterior render is still running or was '
                         'interrupted; publish when it has finished (--force publishes anyway)'
                         % (len(newer), ' '.join(newer[:8]) + (' ...' if len(newer) > 8 else '')))
    found = {}
    for f in frames:                                      # PNG headers only: nothing is written when the folder is mixed
        with Image.open(src / f'{f["id"]}.png') as im:
            found.setdefault(im.size, []).append(f['id'])
    if len(found) != 1:
        raise SystemExit('frames of different sizes (two runs mixed in %s?): %s'
                         % (src, '; '.join(f'{w}x{ht}: {" ".join(ids)}' for (w, ht), ids in found.items())))
    root = sitedata.site_root(a.repo)
    out = root / OUT
    if root != REPO:
        print(f'publishing into {root}')
    (out / 'half').mkdir(parents=True, exist_ok=True)
    jobs = [(f['id'], src / f'{f["id"]}.png', a.quality, a.method, a.half) for f in frames]
    h = hashlib.sha1()
    sizes = {}
    total = 0
    with ProcessPoolExecutor(a.jobs) as ex:
        for fid, w, ht, full, half in ex.map(process, jobs):
            (out / f'{fid}.webp').write_bytes(full)
            (out / 'half' / f'{fid}.webp').write_bytes(half)
            h.update(full)
            sizes[fid] = (w, ht)
            total += len(full) + len(half)
            print(f'{fid}: {w}x{ht} full {len(full) / 1e6:.2f} MB, half {len(half) / 1e6:.2f} MB', flush=True)
    listed = {f'{f["id"]}.webp' for f in frames}
    stale = [p for d in (out, out / 'half') for p in sorted(d.glob('*.webp')) if p.name not in listed]
    if stale and a.prune:
        for p in stale:
            p.unlink()
        print(f'pruned {len(stale)} stale frame files')
    elif stale:
        print(f'{len(stale)} stale frame files left in place (use --prune to delete them): '
              + ', '.join(p.relative_to(out).as_posix() for p in stale[:8]) + (' ...' if len(stale) > 8 else ''))
    keys = ('id', 'ring', 'theta', 'phi', 'radius')
    man = {
        'version': h.hexdigest()[:12],
        'target': meta['target'],
        'hfov': frames[0]['hfov'],
        'aspect': frames[0]['aspect'],
        'frames': [dict({k: f[k] for k in keys}, width=sizes[f['id']][0], height=sizes[f['id']][1],
                        full=f'{f["id"]}.webp', half=f'half/{f["id"]}.webp') for f in frames],
    }
    (out / 'manifest.json').write_text(json.dumps(man, indent=1) + '\n')
    print(f'wrote {len(frames)} frames ({total / 1e6:.1f} MB) and {OUT}/manifest.json version {man["version"]}')


if __name__ == '__main__':
    main()
