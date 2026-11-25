#!/usr/bin/env python3
"""Check the tour's site data files (and, on request, re-extract them from a legacy single-file page).

  python3 tools/render/extract_scene.py              # consistency check; writes nothing; exit 1 on an error
  python3 tools/render/extract_scene.py legacy.html  # extract SCENE, PRIMITIVES, MEASUREMENTS, the Design
                                                     # data and the plan SVG from a pre-v3 page (or git:REV)

Until v3 this script copied the SCENE, PRIMITIVES and MEASUREMENTS constants out of index.html into
tools/render/data/. The page no longer holds data: apply_relayout.py and apply_revisions_web.py write
tools/render/data/scene.json and measurements.json directly (tools/web/sitedata.py), so in the pipeline
this step is a check only. It keeps its place in the sequence
  apply_relayout.py -> apply_revisions_web.py -> extract_scene.py -> tools/web/dimension_plan.py
and fails when the files would break a later step:
  * scene.json: SCENE object indices are stable (object i has the name of concept object i; new objects
    may only be appended; a few renames in place only warn), which bake_web.py (`scene_index`) and the
    build's classification rely on;
    tour node ids are unique, edges and `start` name existing nodes, every node has a position;
  * measurements.json: ids are unique; `node` names a tour node (warning);
  * design.json: every view's `node` / `opening` exists and its image file is there (warnings);
  * primitives.json: the four unit primitives are present (static file; bl/common.py still reads it to
    rebuild cylinder / sphere / rounded SCENE originals, so it stays, but nothing regenerates it).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, os.path.join(HERE, '..', 'web'))
import sitedata  # noqa: E402

CONCEPT_SCENE = os.path.join(HERE, 'data', 'concept', 'scene.json')


def check():
    """Returns (errors, warnings, summary lines)."""
    err, warn, info = [], [], []
    scene = sitedata.load_scene()
    objs = scene['objects']
    concept = json.load(open(CONCEPT_SCENE))['objects']
    if len(objs) < len(concept):
        err.append('scene.json has %d objects, the concept scene %d: indices shifted' % (len(objs), len(concept)))
    moved = [i for i, (a, b) in enumerate(zip(objs, concept)) if a.get('name') != b.get('name')]
    if moved:       # a few renames in place are harmless; many mean an object was inserted or removed
        (err if len(moved) > 20 else warn).append(
            'scene.json object %d is %r, concept object %d is %r (%d names differ): existing objects must keep '
            'their index, new ones are appended' % (moved[0], objs[moved[0]].get('name'), moved[0],
                                                    concept[moved[0]].get('name'), len(moved)))
    tour = scene.get('tour') or {}
    nodes = tour.get('nodes') or []
    ids = [n.get('id') for n in nodes]
    if len(set(ids)) != len(ids):
        err.append('duplicate tour node ids: %s' % sorted({i for i in ids if ids.count(i) > 1}))
    for n in nodes:
        p = n.get('p')
        if not (isinstance(p, list) and len(p) == 3 and all(isinstance(v, (int, float)) for v in p)):
            err.append('tour node %s has no position' % n.get('id'))
    known = set(ids)
    for e in tour.get('edges') or []:
        if len(e) != 2 or e[0] not in known or e[1] not in known or e[0] == e[1]:
            err.append('tour edge %s does not join two tour nodes' % (e,))
    if tour.get('start') not in known:
        err.append('tour.start %r is not a tour node' % tour.get('start'))
    if not (isinstance(scene.get('extent'), list) and len(scene['extent']) == 2):
        err.append('scene.extent is missing')
    info.append('scene.json         %d objects (%d appended to the concept\'s %d), %d tour nodes, %d edges, extent %s'
                % (len(objs), max(0, len(objs) - len(concept)), len(concept), len(nodes),
                   len(tour.get('edges') or []), scene.get('extent')))

    meas = sitedata.load_measurements()
    rows = meas['rooms'] + meas['windows'] + meas['doors']
    mids = [r['id'] for r in rows]
    if len(set(mids)) != len(mids):
        err.append('duplicate measurement ids: %s' % sorted({i for i in mids if mids.count(i) > 1}))
    for r in rows:
        if r.get('node') and r['node'] not in known:
            warn.append('measurement %s names tour node %s, which does not exist' % (r['id'], r['node']))
    info.append('measurements.json  %d rooms, %d windows, %d doors'
                % (len(meas['rooms']), len(meas['windows']), len(meas['doors'])))

    if sitedata.path('design').exists():
        design = sitedata.load_design()
        for key in design.get('order', []):
            if key not in design['views']:
                err.append('design.json order names %r, which is not a view' % key)
        for key, v in design['views'].items():
            if v.get('node') and v['node'] not in known:
                warn.append('design view %s names tour node %s, which does not exist' % (key, v['node']))
            if v.get('opening') and v['opening'] not in mids:
                warn.append('design view %s names measurement %s, which does not exist' % (key, v['opening']))
            if v.get('image') and not (sitedata.site_root() / v['image']).exists():
                warn.append('design view %s: image %s is missing' % (key, v['image']))
            for ref in v.get('refs', []):
                if ref not in design.get('references', {}):
                    warn.append('design view %s: reference %r has no image' % (key, ref))
        info.append('design.json        %d views: %s' % (len(design['views']), ' '.join(design.get('order', []))))
    else:
        err.append('%s is missing (python3 tools/web/sitedata.py --seed git:ed664e0)' % sitedata.path('design'))

    prims = sitedata.load_primitives()
    lost = [k for k in ('box', 'cylinder', 'sphere', 'rounded') if not (prims.get(k) or {}).get('v')]
    if lost:
        err.append('primitives.json lacks %s' % ', '.join(lost))
    info.append('primitives.json    %s (static)' % ' '.join(prims))
    return err, warn, info


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 0
    if len(sys.argv) > 1:
        done = sitedata.seed(sys.argv[1], force=True)
        print('extracted from %s: %s' % (sys.argv[1], ', '.join(done) or 'nothing changed'))
    err, warn, info = check()
    for line in info:
        print(line)
    for line in warn:
        print('warning:', line)
    for line in err:
        print('ERROR:', line)
    print('site data check: %s' % ('FAILED' if err else 'ok' + (' (%d warnings)' % len(warn) if warn else '')))
    return 1 if err else 0


if __name__ == '__main__':
    sys.exit(main())
