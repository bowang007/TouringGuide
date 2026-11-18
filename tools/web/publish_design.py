#!/usr/bin/env python3
"""Publish path-traced hero stills (tools/render/render_heroes.py) as the Design window images.

  tools/render/.cache/venv/bin/python tools/web/publish_design.py tools/render/.cache/heroes

Writes assets/design/<key>.webp (WebP q88, 1600 px wide, 3:2) for the design keys the page uses:
front, B3, B4, K0, A1 (the roof keeps its plan drawing, roof.svg). The extra stills (back, living,
primary, A0) are written to assets/design/extra/ for reuse.
"""
import sys
from pathlib import Path

from PIL import Image

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'assets' / 'design'
KEYS = ['front', 'B3', 'B4', 'K0', 'A1']
WIDTH = 1600


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / 'tools' / 'render' / '.cache' / 'heroes'
    done = []
    for png in sorted(src.glob('*.png')):
        key = png.stem
        if key.startswith('_'):
            continue
        dest = OUT / f'{key}.webp' if key in KEYS else OUT / 'extra' / f'{key}.webp'
        dest.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(png).convert('RGB')
        h = round(WIDTH * im.height / im.width)
        im.resize((WIDTH, h), Image.LANCZOS).save(dest, 'WEBP', quality=88, method=6)
        done.append(dest.relative_to(REPO).as_posix())
    missing = [k for k in KEYS if not (src / f'{k}.png').exists()]
    print('published:', ', '.join(done) or 'nothing')
    if missing:
        print('missing hero stills (kept the previous images):', ', '.join(missing))


if __name__ == '__main__':
    main()
