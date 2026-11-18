#!/usr/bin/env python3
"""Extract the SCENE, PRIMITIVES and MEASUREMENTS constants from a tour HTML file
into tools/render/data/ so the Blender pipeline has frozen, reproducible inputs.

Usage: python3 tools/render/extract_scene.py [path/to/index.html]
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')


def grab(src, marker):
    i = src.find(marker)
    if i < 0:
        raise SystemExit(f'{marker!r} not found')
    obj, _ = json.JSONDecoder().raw_decode(src, i + len(marker))
    return obj


def main():
    html = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', 'index.html')
    src = open(html, encoding='utf-8').read()
    os.makedirs(DATA, exist_ok=True)
    for name, marker in (('scene', 'const SCENE='), ('primitives', 'PRIMITIVES='), ('measurements', 'const MEASUREMENTS=')):
        obj = grab(src, marker)
        with open(os.path.join(DATA, name + '.json'), 'w') as f:
            json.dump(obj, f, separators=(',', ':'))
        print(f'{name}.json written')


if __name__ == '__main__':
    main()
