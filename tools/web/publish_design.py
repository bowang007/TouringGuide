#!/usr/bin/env python3
"""Publish path-traced hero stills (tools/render/render_heroes.py) as the Design window images.

  tools/render/.cache/venv/bin/python tools/web/publish_design.py [tools/render/.cache/heroes] [--repo ROOT]

Writes assets/design/<key>.webp (WebP q88, 1600 px wide, 3:2) for the design keys the page uses: the views of
tools/render/data/design.json whose `image` is assets/design/<key>.webp (today front, B3, B4, K0, LC = the
laundry closet, A0, A1; the roof keeps its plan drawing, roof.svg). The other stills of the folder (back,
living, primary) are written to assets/design/extra/ for reuse; the page does not load them. A copy in extra/
of a still that is now a design view (extra/A0.webp from an earlier layout) is deleted.

Afterwards every image a design view names must exist: a view without its picture is reported as MISSING and
the exit code is 1 (a still that was not rendered keeps the previous image, which is only a note).

--repo ROOT publishes into another root with the repository layout (default: $SITEDATA_ROOT when set, else
the repository), as the other tools of tools/web do. The stills are always read from the folder given.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
DESIGN = 'assets/design'
KEYS = ['front', 'B3', 'B4', 'K0', 'LC', 'A0', 'A1']        # used when design.json cannot be read
WIDTH = 1600


def design_images(root):
    """{key: image path} of the design views whose picture is a published still (assets/design/<key>.webp)."""
    p = sitedata.path('design', root)
    if not p.exists():
        return {k: f'{DESIGN}/{k}.webp' for k in KEYS}
    views = sitedata.read_json(p).get('views', {})
    return {k: v['image'] for k, v in views.items() if v.get('image') == f'{DESIGN}/{k}.webp'}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('renders', nargs='?', default=str(REPO / 'tools' / 'render' / '.cache' / 'heroes'),
                    help='directory with <key>.png hero stills')
    ap.add_argument('--repo', help='root to publish into (default: $SITEDATA_ROOT or the repository)')
    a = ap.parse_args()
    src = Path(a.renders)
    root = sitedata.site_root(a.repo)
    out = root / DESIGN
    wanted = design_images(root)
    if root != REPO:
        print(f'publishing into {root}')
    done = []
    for png in sorted(src.glob('*.png')):
        key = png.stem
        if key.startswith('_'):
            continue
        dest = out / f'{key}.webp' if key in wanted else out / 'extra' / f'{key}.webp'
        dest.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(png).convert('RGB')
        h = round(WIDTH * im.height / im.width)
        im.resize((WIDTH, h), Image.LANCZOS).save(dest, 'WEBP', quality=88, method=6)
        done.append(f'{dest.relative_to(root).as_posix()} ({WIDTH}x{h}, {dest.stat().st_size / 1024:.0f} KB)')
        twin = out / 'extra' / f'{key}.webp'             # a still that became a design view: drop its copy in extra/
        if key in wanted and twin.exists():
            twin.unlink()
            done.append(f'removed stale {twin.relative_to(root).as_posix()}')
    print('published:', ', '.join(done) or 'nothing')
    kept = [k for k in wanted if not (src / f'{k}.png').exists() and (root / wanted[k]).exists()]
    lost = [k for k in wanted if not (root / wanted[k]).exists()]
    if kept:
        print('no new hero still (kept the previous image):', ', '.join(kept))
    if lost:
        print('MISSING: design views without their picture:', ', '.join(f'{k} ({wanted[k]})' for k in lost))
        return 1
    print(f'design views with a published still: {len(wanted)} of {len(wanted)} present ({", ".join(wanted)})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
