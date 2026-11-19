#!/usr/bin/env python3
"""Apply relayout.py (old concept plan -> architect's plan) to the tour's frozen data.

  python3 tools/render/apply_relayout.py [--html index.html] [--dry-run]

Reads SCENE and MEASUREMENTS from index.html and the room regions from
tools/render/data/scene_classification.json, maps every coordinate, and writes them back (index.html
constants, then tools/render/data/ via extract_scene.py). Architecture (walls, floors, ceilings,
openings, roof, facade) is mapped corner by corner, so rooms take their new sizes; movable things
(furniture, decor, lights, landscape) are translated, keeping their size. Run once, on the old plan:
it records the conversion in SCENE.layout_revision.architect_plan and refuses to run twice.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import relayout as R  # noqa: E402

DATA = os.path.join(HERE, 'data')
MOVABLE = {'furniture', 'decor', 'landscape'}


def _grab(src, marker):
    i = src.find(marker)
    if i < 0:
        raise SystemExit(f'{marker!r} not found')
    obj, end = json.JSONDecoder().raw_decode(src, i + len(marker))
    return obj, i + len(marker), end


def _rot_quarter(rot):
    k = round(rot / (math.pi / 2))
    return k if abs(rot - k * math.pi / 2) < 1e-3 else None


def _aabb(o):
    """World AABB (x0, x1, z0, z1) of a SCENE box/primitive, or None for a free rotation."""
    p, s = o['p'], o['s']
    k = _rot_quarter(o.get('rot', 0) or 0)
    if k is None:
        return None
    sx, sz = (s[0], s[2]) if k % 2 == 0 else (s[2], s[0])
    return p[0] - sx / 2, p[0] + sx / 2, p[2] - sz / 2, p[2] + sz / 2


def _mesh_world(o):
    p, s, rot = o['p'], o['s'], o.get('rot', 0) or 0
    c, sn = math.cos(rot), math.sin(rot)
    v = o['geometry']['v']
    out = []
    for i in range(0, len(v), 3):
        lx, ly, lz = v[i] * s[0], v[i + 1] * s[1], v[i + 2] * s[2]
        # rotation about +y (three.js convention): x' = x cos + z sin, z' = -x sin + z cos
        out.append([p[0] + lx * c + lz * sn, p[1] + ly, p[2] - lx * sn + lz * c])
    return out


def _mesh_set(o, world):
    """Store world vertices back as unit-box local vertices (rot reset to 0), normals recomputed."""
    xs = [w[0] for w in world]
    ys = [w[1] for w in world]
    zs = [w[2] for w in world]
    lo = [min(xs), min(ys), min(zs)]
    hi = [max(xs), max(ys), max(zs)]
    size = [max(h - l, 1e-6) for l, h in zip(lo, hi)]
    ctr = [(h + l) / 2 for l, h in zip(lo, hi)]
    loc = []
    for w in world:
        loc += [(w[k] - ctr[k]) / size[k] for k in range(3)]
    nrm = []
    for i in range(0, len(world), 3):               # flat normals per triangle (world space)
        a, b, c = world[i], world[i + 1], world[i + 2]
        u = [b[k] - a[k] for k in range(3)]
        w2 = [c[k] - a[k] for k in range(3)]
        n = [u[1] * w2[2] - u[2] * w2[1], u[2] * w2[0] - u[0] * w2[2], u[0] * w2[1] - u[1] * w2[0]]
        ln = math.sqrt(sum(x * x for x in n)) or 1.0
        n = [x / ln for x in n]
        nrm += n * 3
    o['p'], o['s'], o['rot'] = ctr, size, 0
    o['geometry']['v'] = loc
    if 'n' in o['geometry']:
        o['geometry']['n'] = nrm


def remap_object(o, role):
    if o.get('shape') == 'mesh' and o.get('geometry'):
        world = _mesh_world(o)
        per_vertex = o['group'] in ('roof',) or role == 'exterior'
        if role in MOVABLE or o['group'] in MOVABLE:
            dx, dz = R.shift_xz(o['p'][0], o['p'][2])
            world = [[w[0] + dx, w[1], w[2] + dz] for w in world]
        else:
            at = None if per_vertex else (o['p'][0], o['p'][2])
            new = []
            for w in world:
                nx, nz = R.remap_xz(w[0], w[2], at)
                new.append([nx, w[1], nz])
            world = new
        _mesh_set(o, world)
        return 'mesh'
    box = _aabb(o)
    movable = role in MOVABLE or o['group'] in MOVABLE or o['group'] in ('lighting', 'mirror')
    if box is None or movable:
        dx, dz = R.shift_xz(o['p'][0], o['p'][2])
        o['p'] = [o['p'][0] + dx, o['p'][1], o['p'][2] + dz]
        return 'moved'
    x0, x1, z0, z1 = R.remap_box(*box)
    k = _rot_quarter(o.get('rot', 0) or 0)
    sx, sz = x1 - x0, z1 - z0
    if k % 2:
        sx, sz = sz, sx
    o['p'] = [(x0 + x1) / 2, o['p'][1], (z0 + z1) / 2]
    o['s'] = [sx, o['s'][1], sz]
    return 'box'


def remap_point(p):
    x, z = R.remap_xz(p[0], p[2])
    return [x, p[1], z]


def remap_measurements(m):
    for r in m.get('rooms', []):
        b = r.get('bounds_ft')
        if b:
            nb = R.remap_box(*b)
            r['bounds_ft'] = [round(v, 4) for v in nb]
            r['width_ft'] = round(nb[1] - nb[0], 4)
            r['depth_ft'] = round(nb[3] - nb[2], 4)
            r['area_sqft'] = round(r['width_ft'] * r['depth_ft'], 2)
            if 'target_ft' in r:
                r['target_ft'] = [r['width_ft'], r['depth_ft']]
    for w in m.get('windows', []) + m.get('doors', []):
        ax, c = w.get('axis'), w.get('c')
        if ax == 'x':                                  # along x on the wall z = c
            mid = ((w['start'] + w['end']) / 2, c)
            a = R.remap_xz(w['start'], c, mid)
            b = R.remap_xz(w['end'], c, mid)
            w['start'], w['end'], w['c'] = round(a[0], 4), round(b[0], 4), round(a[1], 4)
        elif ax == 'z':                                # along z on the wall x = c
            mid = (c, (w['start'] + w['end']) / 2)
            a = R.remap_xz(c, w['start'], mid)
            b = R.remap_xz(c, w['end'], mid)
            w['start'], w['end'], w['c'] = round(a[1], 4), round(b[1], 4), round(a[0], 4)
        elif ax == 'roof' and w.get('p'):
            mid = (w['p'][0], w['p'][2])
            a = R.remap_xz(w['start'], w['p'][2], mid)
            b = R.remap_xz(w['end'], w['p'][2], mid)
            w['start'], w['end'] = round(a[0], 4), round(b[0], 4)
            w['p'] = remap_point(w['p'])
        if w.get('start') is not None and w.get('end') is not None and isinstance(w.get('width'), (int, float)):
            w['width'] = round(abs(w['end'] - w['start']), 4)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', default=os.path.join(HERE, '..', '..', 'index.html'))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-cls', action='store_true', help='do not rewrite data/scene_classification.json')
    a = ap.parse_args()
    src = open(a.html, encoding='utf-8').read()
    scene, s0, s1 = _grab(src, 'const SCENE=')
    if scene.get('layout_revision', {}).get('architect_plan'):
        raise SystemExit('already converted to the architect plan')
    cls_path = os.path.join(DATA, 'scene_classification.json')
    cls = json.load(open(cls_path))
    if len(cls['objects']) != len(scene['objects']):
        raise SystemExit('classification does not match SCENE.objects')
    counts = {}
    for i, o in enumerate(scene['objects']):
        c = cls['objects'][str(i)]
        old = (o['p'][0], o['p'][2])
        k = remap_object(o, c.get('role'))
        counts[k] = counts.get(k, 0) + 1
        bb = c.get('aabb_ft')
        if bb:                                     # x0 x1 y0 y1 z0 z1
            if k == 'moved':
                dx, dz = o['p'][0] - old[0], o['p'][2] - old[1]
                c['aabb_ft'] = [bb[0] + dx, bb[1] + dx, bb[2], bb[3], bb[4] + dz, bb[5] + dz]
            elif k == 'mesh':
                p, sz = o['p'], o['s']
                c['aabb_ft'] = [p[0] - sz[0] / 2, p[0] + sz[0] / 2, bb[2], bb[3], p[2] - sz[2] / 2, p[2] + sz[2] / 2]
            else:
                q = _aabb(o)
                c['aabb_ft'] = [q[0], q[1], bb[2], bb[3], q[2], q[3]]
            c['aabb_ft'] = [round(v, 4) for v in c['aabb_ft']]
    for n in scene['tour']['nodes']:
        look = n.get('look')
        n['p'] = remap_point(n['p'])
        if look:
            n['look'] = remap_point(look)
    for r in scene.get('rooms', []):
        if r.get('p'):
            r['p'] = remap_point(r['p'])
        if r.get('look'):
            r['look'] = remap_point(r['look'])
    for li in scene.get('lights', []):
        li['p'] = remap_point(li['p'])
    for au in scene.get('audit', []):
        if au.get('bounds_ft'):
            nb = R.remap_box(*au['bounds_ft'])
            au['bounds_ft'] = [round(v, 4) for v in nb]
            au['width_ft'] = round(nb[1] - nb[0], 4)
            au['depth_ft'] = round(nb[3] - nb[2], 4)
            au['area_sqft'] = round(au['width_ft'] * au['depth_ft'], 2)
            if 'target_ft' in au:
                au['target_ft'] = [au['width_ft'], au['depth_ft']]
    ex = scene['extent']
    scene['extent'] = [round(R.X_REAR(ex[0]), 6), round(R.Z_LEFT(ex[1]), 6)]
    scene.setdefault('layout_revision', {})['architect_plan'] = {
        'source': 'sizes/sizes.pdf, sheet SKA002 (N) FLOOR PLAN, Option A (HW Architecture, Nov 13 2026)',
        'method': 'tools/render/relayout.py: old wall faces mapped to the plan\'s clear dimensions',
        'outer_width_ft': 39.87,
    }
    meas, m0, m1 = _grab(src, 'const MEASUREMENTS=')
    remap_measurements(meas)
    for k, v in cls['meta']['rooms'].items():
        b = v.get('bounds_ft_x0x1z0z1')
        if b:
            v['bounds_ft_x0x1z0z1'] = [round(x, 4) for x in R.remap_box(*b)]
    print('objects:', counts, 'extent', scene['extent'])
    if a.dry_run:
        return
    sj = json.dumps(scene, separators=(',', ':'), ensure_ascii=False)
    mj = json.dumps(meas, separators=(',', ':'), ensure_ascii=False)
    if m0 > s0:
        src = src[:s0] + sj + src[s1:m0 - len('const MEASUREMENTS=')] + 'const MEASUREMENTS=' + mj + src[m1:]
    else:
        src = src[:m0] + mj + src[m1:s0 - len('const SCENE=')] + 'const SCENE=' + sj + src[s1:]
    open(a.html, 'w', encoding='utf-8').write(src)
    if not a.no_cls:
        json.dump(cls, open(cls_path, 'w'), separators=(',', ':'))
    print('wrote', a.html, cls_path)


if __name__ == '__main__':
    main()
