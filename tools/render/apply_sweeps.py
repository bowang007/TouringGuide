#!/usr/bin/env python3
"""Install the sweeps of tools/render/data/sweeps.json (place_sweeps.py) as the tour of the scene.

  python3 tools/render/apply_sweeps.py [--sweeps FILE] [--root DIR] [--check]

Replaces `tour.nodes` and `tour.edges` of tools/render/data/scene.json (read and written through
tools/web/sitedata.py) with the sweeps; `tour.start` stays 'E0' and other keys of `tour` are kept. A node keeps
today's shape plus three keys:

  id, label, name (= label), room, p [x, y, z], look (p + 8 ft along yaw / pitch), neighbors (= links),
  yaw, pitch (RADIANS, as the scene's nodes always were; sweeps.json holds degrees), size (the caption of
  an old stop that keeps its id and label, else ''), visible, floor, outdoor

`tour.edges` = every link once, as [a, b] in sweep order. The scene's `rooms` list, a mirror of `tour.nodes`
since the first version of the page, is updated with it (left alone when it holds something else).
An old stop that the sweeps leave in place (within 1e-4 ft / 1e-6 rad) keeps its exact numbers, so
re-installing changes nothing and a seed's authored view survives bit for bit.

It reports the kept / new / removed / moved ids against the scene it writes into (after apply_relayout.py that
is the concept's 27 stops) and, when the sweeps were placed with `place_sweeps.py --keep` (the file's "keep"
block), against that kept layout: the moved and new sweeps there are the ones that need a new panorama (a
renamed sweep does not: its label follows the scene file).

The script is idempotent (a second run writes nothing) and refuses to write, with exit status 1, when
  * two sweeps share an id, or an id is not 2 characters,
  * a link or a visible entry names an unknown sweep, a sweep links to itself, or a link is one-way,
  * the link graph is not one connected component,
  * the start sweep 'E0' is missing, or a sweep has no position.

Run it after apply_relayout.py / apply_revisions_web.py (apply_relayout.py rebuilds the scene from the
concept plan and drops the sweeps) and before extract_scene.py (the check), tools/web/dimension_plan.py and
tools/web/build_site_data.py. --root DIR works on another tree with the repository's layout (sitedata's
$SITEDATA_ROOT), which is how it is tested without touching the working files; --check validates only.
"""
import argparse
import collections
import copy
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SWEEPS = 'tools/render/data/sweeps.json'
SCENE = 'tools/render/data/scene.json'
START = 'E0'
LOOK_FT = 8.0
SAME_FT, SAME_RAD = 1e-4, 1e-6
# Opening views chosen by eye on the rendered panoramas (degrees; None keeps the value of sweeps.json). They
# override place_sweeps.py's automatic yaw / pitch every time the sweeps are installed:
#   G0  look into the garage, not back at the foyer door
#   H2  toward the dining table, the island and the living room beyond
# Sixth round (the primary suite laid out as on the architect's sheet; a kept layout keeps the views of the rooms
# as they were before):
#   C0  the walk-in closet: the double-hung north wall with its rod and shelf, the drawer and shelf tower at the left
#   S1  in the vestibule, through the bathroom door: the stone vanity wall, both mirrors, the beam and its lamps
#   A0  from the door side of the bath across the vanity: stone wall, mirror, beam and lamp, the shelf, the toilet,
#       the west window, the shower's glass at the right edge
#   P5  at the foot of the bed: the bed on the west wall between the two west windows
# (LC, the laundry sweep, has no entry any more: its view is place_sweeps.py LAUNDRY['pitch'].)
OPENING = {'G0': (105.0, -3.0), 'H2': (40.0, -2.0),
           'C0': (-30.0, -4.0), 'S1': (-170.0, -4.0), 'A0': (-138.0, -5.0), 'P5': (-90.0, -3.0),
           'A3': (-75.0, -3.0)}      # A3: face the taller shower window (sixth round)

sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, os.path.join(REPO, 'tools', 'web'))
try:
    import sitedata  # noqa: E402
except ImportError:                 # the helper is part of v3; without it the files are read and written directly
    sitedata = None


class Refused(Exception):
    pass


# ----------------------------------------------------------------------------------------------- files
def load_scene(root):
    if sitedata is not None:
        return sitedata.load_scene(root)
    with open(os.path.join(root or REPO, SCENE), encoding='utf-8') as f:
        return json.load(f)


def save_scene(scene, root):
    """Write the scene; True when the file changed."""
    if sitedata is not None:
        return sitedata.save_scene(scene, root)
    path = os.path.join(root or REPO, SCENE)
    data = json.dumps(scene, separators=(',', ':')).encode('utf-8')
    if os.path.exists(path) and open(path, 'rb').read() == data:
        return False
    tmp = '%s.tmp%d' % (path, os.getpid())
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)
    return True


def optional(name, root):
    """measurements / design, for the reference warnings only."""
    try:
        if sitedata is not None:
            return sitedata.read_json(sitedata.path(name, root))
        with open(os.path.join(root or REPO, 'tools/render/data/%s.json' % name), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError, KeyError):
        return None


# ----------------------------------------------------------------------------------------------- checks
def validate(doc, start=START):
    """Raise Refused with every problem of a sweeps document; returns (sweeps, warnings)."""
    bad, warn = [], []
    sweeps = doc.get('sweeps') if isinstance(doc, dict) else None
    if not isinstance(sweeps, list) or not sweeps:
        raise Refused('no "sweeps" list in the file')
    ids = [s.get('id') for s in sweeps]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        bad.append('duplicate sweep ids: %s' % ' '.join(map(str, dup)))
    for i in ids:
        if not isinstance(i, str) or len(i) != 2:
            bad.append('sweep id %r is not 2 characters' % (i,))
    known = set(ids)
    for s in sweeps:
        sid = s.get('id')
        p = s.get('p')
        if not (isinstance(p, list) and len(p) == 3 and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                                           and math.isfinite(v) for v in p)):
            bad.append('sweep %s has no position p [x, y, z]' % sid)
        for key in ('yaw', 'pitch'):
            if not isinstance(s.get(key, 0.0), (int, float)) or not math.isfinite(s.get(key, 0.0)):
                bad.append('sweep %s: %s is not a number' % (sid, key))
        for key in ('links', 'visible'):
            v = s.get(key, [])
            if not isinstance(v, list):
                bad.append('sweep %s: %s is not a list' % (sid, key))
                continue
            for o in v:
                if o == sid:
                    bad.append('sweep %s names itself in %s' % (sid, key))
                elif o not in known:
                    bad.append('sweep %s: %s names unknown sweep %r' % (sid, key, o))
            if len(set(map(str, v))) != len(v):
                bad.append('sweep %s: %s repeats an id' % (sid, key))
    if start not in known:
        bad.append('the start sweep %s is missing' % start)
    if bad:
        raise Refused('; '.join(bad))
    links = {s['id']: list(s.get('links', [])) for s in sweeps}
    oneway = sorted('%s->%s' % (a, b) for a in links for b in links[a] if a not in links[b])
    if oneway:
        raise Refused('one-way links: %s' % ' '.join(oneway))
    seen, queue = {start}, collections.deque([start])
    while queue:
        for o in links[queue.popleft()]:
            if o not in seen:
                seen.add(o)
                queue.append(o)
    if len(seen) != len(ids):
        raise Refused('the link graph is not connected: %d of %d sweeps cannot be reached from %s: %s'
                      % (len(ids) - len(seen), len(ids), start, ' '.join(i for i in ids if i not in seen)))
    for s in sweeps:
        missing = [o for o in s.get('links', []) if o not in s.get('visible', s.get('links', []))]
        if missing:
            warn.append('sweep %s: links %s are not in `visible`; added' % (s['id'], ' '.join(missing)))
    eye = doc.get('eye')
    if isinstance(eye, (int, float)):
        off = [s['id'] for s in sweeps if abs(s['p'][1] - eye) > 0.01]
        if off:
            warn.append('sweeps not at the eye height %.4f: %s' % (eye, ' '.join(off)))
    return sweeps, warn


# ----------------------------------------------------------------------------------------------- nodes
def _same(a, b, tol):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol


def build_tour(doc, scene, start=START):
    """(nodes, edges, warnings, summary) for a validated sweeps document and the scene it goes into."""
    sweeps, warn = validate(doc, start)
    rad = (lambda v: v) if (doc.get('units') or {}).get('angle', 'deg') == 'rad' else math.radians
    old = {n.get('id'): n for n in (scene.get('tour') or {}).get('nodes') or []}
    order = {s['id']: k for k, s in enumerate(sweeps)}
    nodes, moved = [], []
    for s in sweeps:
        o = old.get(s['id'])
        p = [float(v) for v in s['p']]
        yaw, pitch = rad(float(s.get('yaw', 0.0))), rad(float(s.get('pitch', 0.0)))
        oy, op_ = OPENING.get(s['id'], (None, None))
        if oy is not None:
            yaw = math.radians(oy)
        if op_ is not None:
            pitch = math.radians(op_)
        if o is not None:
            op = o.get('p') or []
            if len(op) == 3 and all(_same(a, b, SAME_FT) for a, b in zip(op, p)):
                p = list(op)
            elif len(op) == 3:
                moved.append('%s %.2f ft' % (s['id'], math.hypot(op[0] - p[0], op[2] - p[2])))
            if _same(o.get('yaw'), yaw, SAME_RAD):
                yaw = o['yaw']
            if _same(o.get('pitch'), pitch, SAME_RAD):
                pitch = o['pitch']
        label = s.get('label') or (o or {}).get('label') or s['id']
        cp = math.cos(pitch)
        look = [p[0] + LOOK_FT * math.sin(yaw) * cp, p[1] + LOOK_FT * math.sin(pitch),
                p[2] - LOOK_FT * math.cos(yaw) * cp]
        links = sorted(s.get('links', []), key=order.get)
        visible = sorted(set(s.get('visible', [])) | set(links), key=order.get)
        nodes.append({
            'id': s['id'], 'label': label, 'name': label,
            'room': s.get('room') or (o or {}).get('room') or '',
            'p': p, 'look': [round(v, 4) for v in look], 'neighbors': links,
            'yaw': yaw, 'pitch': pitch,
            'size': o.get('size', '') if o is not None and o.get('label') == label else '',
            'visible': visible, 'floor': float(s.get('floor', 0.0)) + 0.0, 'outdoor': bool(s.get('outdoor', False)),
        })
    edges = [[n['id'], b] for n in nodes for b in n['neighbors'] if order[b] > order[n['id']]]
    new = set(order)
    summary = {
        'sweeps': len(nodes), 'edges': len(edges), 'outdoor': sum(1 for n in nodes if n['outdoor']),
        'kept': sorted(new & set(old), key=order.get), 'added': sorted(new - set(old), key=order.get),
        'removed': [i for i in old if i not in new], 'moved': moved,
    }
    return nodes, edges, warn, summary


def keep_report(doc):
    """Lines about the kept layout the sweeps were placed on (place_sweeps.py --keep), checked against the
    sweeps themselves; [] when the file has no such block."""
    k = doc.get('keep') if isinstance(doc, dict) else None
    if not isinstance(k, dict):
        return []
    ids = {s.get('id') for s in doc.get('sweeps', [])}
    moved = k.get('moved') if isinstance(k.get('moved'), dict) else {}

    def lst(key):
        return [i for i in (k.get(key) or []) if isinstance(i, str)]
    out = ['against the kept layout %s:' % k.get('from', '?'),
           '  unchanged   %d sweeps' % len(lst('unchanged')),
           '  moved       %s' % (', '.join('%s %.2f ft' % (i, d) for i, d in moved.items()) or '-'),
           '  new ids     %s' % (' '.join(lst('new')) or '-'),
           '  removed ids %s' % (' '.join(lst('removed')) or '-')]
    if lst('reaimed'):
        out.append('  view only   %s' % ' '.join(lst('reaimed')))
    renamed = k.get('renamed') if isinstance(k.get('renamed'), dict) else {}
    if renamed:
        out.append('  renamed     %s' % ', '.join('%s "%s"' % kv for kv in renamed.items()))
    stale = sorted((set(lst('unchanged')) | set(moved) | set(lst('new')) | set(lst('reaimed'))) ^ ids, key=str)
    back = sorted(set(lst('removed')) & ids)
    if stale or back:
        out.append('  warning: the "keep" block does not match the sweeps (%s): the file was edited after it was '
                   'placed' % ' '.join(map(str, stale + back)))
    return out


def references(root, ids):
    """Warnings for measurements / design entries that name a stop the tour no longer has."""
    out = []
    meas = optional('measurements', root)
    if isinstance(meas, dict):
        for r in (meas.get('rooms') or []) + (meas.get('windows') or []) + (meas.get('doors') or []):
            if r.get('node') and r['node'] not in ids:
                out.append('measurement %s names sweep %s, which the tour no longer has' % (r.get('id'), r['node']))
    design = optional('design', root)
    if isinstance(design, dict):
        for key, v in (design.get('views') or {}).items():
            if isinstance(v, dict) and v.get('node') and v['node'] not in ids:
                out.append('design view %s names sweep %s, which the tour no longer has' % (key, v['node']))
    return out


def apply(doc, scene, start=START):
    """Put the sweeps into `scene` (in place). Returns (warnings, summary)."""
    nodes, edges, warn, summary = build_tour(doc, scene, start)
    tour = scene.setdefault('tour', {})
    mirror = scene.get('rooms')
    was_mirror = isinstance(mirror, list) and all(isinstance(r, dict) and 'id' in r and 'p' in r for r in mirror)
    tour['nodes'] = nodes
    tour['edges'] = edges
    tour['start'] = start
    if isinstance(tour.get('highlights'), list):
        lost = [i for i in tour['highlights'] if i not in {n['id'] for n in nodes}]
        if lost:
            warn.append('tour.highlights names sweeps the tour no longer has: %s' % ' '.join(lost))
    if was_mirror:
        scene['rooms'] = copy.deepcopy(nodes)
    elif mirror is not None:
        warn.append('scene.rooms is not a copy of the tour nodes; left as it is')
    return warn, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--sweeps', help='sweeps file (default: <root>/%s)' % SWEEPS)
    ap.add_argument('--root', help='another tree with the repository layout (default: $SITEDATA_ROOT or the repo)')
    ap.add_argument('--check', action='store_true', help='validate and report, write nothing')
    a = ap.parse_args(argv)
    root = a.root or os.environ.get('SITEDATA_ROOT') or None
    path = a.sweeps or os.path.join(root or REPO, SWEEPS)
    try:
        with open(path, encoding='utf-8') as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        print('apply_sweeps: cannot read %s: %s' % (path, e), file=sys.stderr)
        return 1
    scene = load_scene(root)
    try:
        warn, summary = apply(doc, scene)
    except Refused as e:
        print('apply_sweeps: REFUSED, nothing written. %s: %s' % (path, e), file=sys.stderr)
        return 1
    warn += references(root, {n['id'] for n in scene['tour']['nodes']})
    for line in warn:
        print('warning:', line)
    print('%d sweeps (%d outdoor), %d edges, start %s, from %s (%s)' % (
        summary['sweeps'], summary['outdoor'], summary['edges'], START, path, doc.get('generated_from', '?')))
    print('against the scene it is installed into:')
    print('  kept ids    %s' % (' '.join(summary['kept']) or '-'))
    print('  new ids     %s' % (' '.join(summary['added']) or '-'))
    print('  removed ids %s' % (' '.join(summary['removed']) or '-'))
    print('  moved       %s' % (', '.join(summary['moved']) or '-'))
    for line in keep_report(doc):
        print(line)
    if a.check:
        print('check only: nothing written')
        return 0
    changed = save_scene(scene, root)
    where = sitedata.rel(sitedata.path('scene', root), root) if sitedata is not None else SCENE
    print('%s %s' % (where, 'updated' if changed else 'unchanged (already installed)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
