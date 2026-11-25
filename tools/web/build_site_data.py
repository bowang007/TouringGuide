#!/usr/bin/env python3
"""Write the page's runtime data files (assets/data/*.json) from the pipeline's site data.

  python3 tools/web/build_site_data.py [--version V] [--check] [--out DIR] [--quiet]

Reads tools/render/data/{scene,measurements,design,scene_classification}.json through tools/web/sitedata.py
and writes (only when the bytes change):

  assets/data/tour.json          what the viewer needs of the scene, without its objects (about 13 kB)
  assets/data/measurements.json  the dimension schedule (rooms, windows, doors, source, precision,
                                 basis_legend) plus `audit`, the room table of the About sheet
  assets/data/design.json        the Design window: order, views {label, title, text, refs, node, opening,
                                 image}, references, and `owner_changes` [{round, date, changes}]

tour.json (SCENE feet: x west -> east, y up, z rear/north -> street/south):
  version    release label, also in the other two files. --version V sets it; otherwise the version of the
             existing tour.json is kept (first run: today's date + 'a').
  title, subtitle, units 'ft', angles 'deg'
  eye        camera height of the sweeps
  extent     [x, z] size of the scene's interior box (scene.extent)
  start      id of the first sweep
  footprint  [[x0, z0, x1, z1], ...] non-overlapping rectangles, largest first, whose union is the outline
             of the heated house plus garage at the outer wall faces. Derived from the Foundation objects of
             the scene and the room bounds, grown by half an exterior wall; checked against the walls, rooms
             and sweeps on every run (see the printout). A foundation that is not a rectangle (the canted
             Bedroom 3 bay) becomes a staircase of strips, cut as finely as the engine's limit of 16
             rectangles allows (FOOT_MAX in assets/js/tour/engine.js): the page clips walls and floors to
             these rectangles in the dollhouse and the floor plan, so coarse steps show.
  sweeps     [{id, label, room, p [x, y, z], floor, yaw, pitch, links, visible, outdoor}] from scene.tour:
             yaw / pitch in DEGREES (the scene's nodes hold radians; yaw 0 looks toward -z, positive
             clockwise seen from above); links = tour.edges in both directions; visible, floor, outdoor are
             copied when the node has them, else visible = links, floor = 0.02, outdoor = false;
             room = id of the entry of `rooms` the sweep stands in (the smallest one containing it),
             'outside' for outdoor sweeps. A sweep that stands in no room stands in a doorway, in the
             thickness of the wall between two rooms (Y0 and Z0 in the doors of Bedrooms 3 and 4 since
             the eighth round): it belongs to the room it is named after when that is one of the two,
             else to the nearest. A room nobody can stand in (the laundry closet) owns the sweep in
             front of it: the stop it names, unless that is another room's own stop.
             p[1] is the sweep's own eye height, 5.0853 ft above the level it stands on (the garage
             floor is 11 in below the house floor, the porch slab and the rear landings are lower too);
             `eye` is the median of the indoor sweeps, and floor is the surface under the stop, where
             the page draws its ring.
  rooms      [{id, label, bounds [x0, z0, x1, z1], at [x, z], sweep, tag}]: the measured rooms of the
             schedule (tag = its M-number, bounds = clear interior, at = centre of the bounds, sweep = the
             sweep to enter the room) followed by the open spaces the schedule does not measure (living,
             kitchen + dining, hall, garage; tag null; bounds from scene_classification.json). An open
             space is entered on its card of the highlight reel when it has one: the stop of
             scene.tour.highlights that carries the room's name and stands in it (the living room's is
             L8 since the seventh round), else the stop OPEN_ROOMS names. So a click on a room's name
             on the floor plan opens the picture the reel shows for that room.
             The bounds are rectangles and may lie inside one another: the laundry closet is cut out of
             Bedroom 4's rectangle, and an open space's rectangle reaches over its neighbours. A point
             belongs to the SMALLEST room that contains it: room_of() here, roomAt() in
             assets/js/tour/viewer.js (a click in the dollhouse or on the floor plan), and the tests.
             The page takes a room with a tag for a walled room, because its bounds are the clear faces
             of its own walls: a click inside it enters one of its own sweeps, never the sweep that
             stands a foot away in the room next door (walledOff() in viewer.js). The walk-in closet
             (M05) and the vestibule (M14) of the primary suite are two such rooms side by side.
  highlights sweep ids of the highlight reel, one card per place: scene.tour.highlights when present, else
             the old page's `roomIDs` order; the start sweep (the entrance) always comes first, and a sweep
             or a caption (sweep label) that is already in the reel is left out.
  files      {model, plan, code}: content hashes (12 hex digits) of assets/model/house.glb, of the plan
             drawing and of the page's code (assets/js/tour/*.js + assets/css/tour.css). The page asks for
             the model and the plan with their own hash as `?v=`, so a re-bake or a new plan reaches a
             returning visitor without a new release label. The code is stamped with the release label
             (index.html), so when `code` changes while the label stays, the printout says that
             `--version` is needed. A file that does not exist has no entry.

With --version every file of the site that index.html names in a `src=` or `href=` attribute gets the release
label: `assets/...?v=V` (today main.js, tour.css and the landing picture assets/design/front.webp, which is also
the <noscript> link). main.js hands the label on to the modules, the data, the model and the sheets' pictures,
and the panoramas and exterior frames carry the content hash of their manifests, so a new release never shows
a visitor a cached file of the last one. The import map (the vendored three.js, which only changes with its
own folder) and links to other sites are left alone. That is the only access to index.html any tool keeps;
without --version the page is not opened, and neither is it with --out DIR (a rehearsal into another directory
never stamps the site's page). --check writes nothing and exits 1 when a file is out of date, index.html included.
"""
import argparse
import datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

TITLE = '1095 W McKinley'
SUBTITLE = 'Proposed remodel · 4 bedrooms · 3 full bathrooms'
FLOOR = 0.02
# the reel when the scene names none: the tour's highlights as of the eighth round
HIGHLIGHTS = ['E0', 'L8', 'D0', 'K0', 'P0', 'B2', 'B3', 'B4', 'LC', 'A0', 'A1', 'A3', 'S0', 'C0', 'G0']
# spaces the schedule does not measure: (id, label, scene_classification room keys, preferred sweep).
# The preferred sweep is the fallback: a space with a card of its own name in the reel is entered there.
OPEN_ROOMS = [('living', 'Living room', ('living', 'dining'), 'L0'),
              ('kitchen', 'Kitchen + dining', ('kitchen',), 'K0'),
              ('hall', 'Hall', ('common_hall',), 'H2'),
              ('garage', 'Garage', ('garage',), 'G0')]
MAX_RECTS = 16      # footprint rectangles the engine's shaders accept (FOOT_MAX in assets/js/tour/engine.js)
MIN_STRIP = 0.1     # ft: the strips that approximate a foundation that is not a rectangle (the bay) get no finer
TOL = 0.06          # ft: tolerance of the footprint checks
DOORWAY = 0.5       # ft: a sweep in no room is in a doorway of a room this near (a wall is 5 in thick)
MODEL = 'assets/model/house.glb'                        # fetched by the page with its content hash (tour.json `files`)
CODE = ('assets/js/tour', 'assets/css/tour.css')        # the page's code: stamped with the release label by index.html


def r4(v):
    return round(float(v), 4)


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


# ------------------------------------------------------------------------------------------- geometry
def _quarter(rot):
    k = round((rot or 0) / (math.pi / 2))
    return k if abs((rot or 0) - k * math.pi / 2) < 1e-3 else None


def box_rect(o):
    """(x0, z0, x1, z1) of a SCENE box, or None when it is turned by something else than quarter turns."""
    k = _quarter(o.get('rot'))
    if k is None:
        return None
    sx, sz = (o['s'][0], o['s'][2]) if k % 2 == 0 else (o['s'][2], o['s'][0])
    return o['p'][0] - sx / 2, o['p'][2] - sz / 2, o['p'][0] + sx / 2, o['p'][2] + sz / 2


def mesh_xz(o):
    """World (x, z) of a SCENE mesh's vertices (rotation about +y as three.js applies it)."""
    p, s, rot = o['p'], o['s'], o.get('rot') or 0
    c, sn = math.cos(rot), math.sin(rot)
    v = o['geometry']['v']
    return [(p[0] + v[i] * s[0] * c + v[i + 2] * s[2] * sn, p[2] - v[i] * s[0] * sn + v[i + 2] * s[2] * c)
            for i in range(0, len(v), 3)]


def hull(pts):
    pts = sorted(set((round(x, 5), round(z, 5)) for x, z in pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        out = []
        for q in seq:
            while len(out) >= 2 and ((out[-1][0] - out[-2][0]) * (q[1] - out[-2][1])
                                     - (out[-1][1] - out[-2][1]) * (q[0] - out[-2][0])) <= 0:
                out.pop()
            out.append(q)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def strips(poly, n):
    """A convex outline as n rectangles: equal slices along z, each as wide as the outline is at the
    slice's middle."""
    z0, z1 = min(z for _, z in poly), max(z for _, z in poly)
    out = []
    for k in range(n):
        za, zb = z0 + (z1 - z0) * k / n, z0 + (z1 - z0) * (k + 1) / n
        zm = (za + zb) / 2
        xs = []
        for (ax, az), (bx, bz) in zip(poly, poly[1:] + poly[:1]):
            if (az - zm) * (bz - zm) <= 0 and az != bz:
                xs.append(ax + (bx - ax) * (zm - az) / (bz - az))
        if len(xs) >= 2:
            out.append((min(xs), za, max(xs), zb))
    return out


def floor_walls(scene):
    """Rectangles of the wall boxes that stand on the floor (axis-aligned ones only)."""
    out = []
    for o in scene['objects']:
        if o.get('group') == 'walls' and o.get('shape') == 'box' and o['p'][1] - o['s'][1] / 2 <= 1.5:
            r = box_rect(o)
            if r:
                out.append(r)
    return out


def inside(rects, x, z, tol=0.0):
    return any(r[0] - tol <= x <= r[2] + tol and r[1] - tol <= z <= r[3] + tol for r in rects)


def partition(rects, eps=0.02):
    """Non-overlapping rectangles with the same union as `rects`, largest first (greedy largest rectangle
    on the grid of all edge coordinates; coordinates closer than `eps` are merged)."""
    def lines(vals):
        vals = sorted(vals)
        groups = [[vals[0]]]
        for v in vals[1:]:
            if v - groups[-1][-1] > eps:
                groups.append([])
            groups[-1].append(v)
        return [sum(g) / len(g) for g in groups]
    xs = lines([v for r in rects for v in (r[0], r[2])])
    zs = lines([v for r in rects for v in (r[1], r[3])])
    n, m = len(xs) - 1, len(zs) - 1
    grid = [[inside(rects, (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2) for i in range(n)] for j in range(m)]
    out = []
    while True:
        best, run = (0.0, None), [0] * n
        for j in range(m):
            for i in range(n):
                run[i] = run[i] + 1 if grid[j][i] else 0
            stack = []                                   # (first column, rows) of the open bars
            for i in range(n + 1):
                h, first = (run[i] if i < n else 0), i
                while stack and stack[-1][1] >= h:
                    first, rows = stack.pop()
                    if rows:
                        area = (xs[i] - xs[first]) * (zs[j + 1] - zs[j + 1 - rows])
                        if area > best[0]:
                            best = (area, (first, i, j + 1 - rows, j + 1))
                stack.append((first, h))
        if not best[1]:
            return out
        i0, i1, j0, j1 = best[1]
        for j in range(j0, j1):
            for i in range(i0, i1):
                grid[j][i] = False
        out.append((xs[i0], zs[j0], xs[i1], zs[j1]))


# ------------------------------------------------------------------------------------------- footprint
def footprint(scene, room_rects):
    """Returns (rectangles, report lines, problems)."""
    boxes, outlines = [], []    # foundations at the wall centre lines: rectangles, and convex outlines of the others
    for o in scene['objects']:
        if o.get('group') != 'base' or 'oundation' not in o.get('name', ''):
            continue
        r = box_rect(o) if o.get('shape') == 'box' else None
        if r:
            boxes.append(r)
        elif o.get('geometry'):
            outlines.append(hull(mesh_xz(o)))
        else:                   # a box turned by something else than a quarter turn
            c, sn = math.cos(o.get('rot') or 0), math.sin(o.get('rot') or 0)
            outlines.append(hull([(o['p'][0] + dx * c + dz * sn, o['p'][2] - dx * sn + dz * c)
                                  for dx in (-o['s'][0] / 2, o['s'][0] / 2) for dz in (-o['s'][2] / 2, o['s'][2] / 2)]))
    if not boxes and not outlines:
        raise SystemExit('no Foundation objects in the scene: cannot derive the footprint')
    walls = floor_walls(scene)
    # half an exterior wall: how far the walls stand out beyond the foundation on the west, north and east
    flat = boxes + [(min(x for x, _ in h), min(z for _, z in h), max(x for x, _ in h), max(z for _, z in h))
                    for h in outlines]
    over = [min(r[0] for r in flat) - min(r[0] for r in walls), min(r[1] for r in flat) - min(r[1] for r in walls),
            max(r[2] for r in walls) - max(r[2] for r in flat)] if walls else []
    pad = round(max(over), 3) if over and 0.1 <= max(over) <= 0.5 else 0.225

    def cut(n):
        """The footprint with every outline that is not a rectangle cut into n strips."""
        found = boxes + [r for h in outlines for r in strips(h, n)]
        src = [tuple(r4(v) for v in r) for r in found + list(room_rects)]
        return found, partition([(r[0] - pad, r[1] - pad, r[2] + pad, r[3] + pad) for r in src])
    # As fine as the engine's rectangles allow: the page clips the model to these rectangles, and a canted
    # wall cut in coarse steps shows it.
    depth = max([max(z for _, z in h) - min(z for _, z in h) for h in outlines] or [0.0])
    n = max(1, math.ceil(depth / MIN_STRIP - 1e-9))
    found, rects = cut(n)
    while len(rects) > MAX_RECTS and n > 1:
        n -= 1
        found, rects = cut(n)
    # float noise: an edge within a hair of a wall face is that wall face
    faces = (sorted({r4(v) for w in walls for v in (w[0], w[2])}), sorted({r4(v) for w in walls for v in (w[1], w[3])}))

    def snap(v, axis):
        near = min(faces[axis], key=lambda f: abs(f - v)) if faces[axis] else v
        return near if abs(near - v) <= 0.001 else r4(v)
    rects = [(snap(r[0], 0), snap(r[1], 1), snap(r[2], 0), snap(r[3], 1)) for r in rects]

    box = (min(r[0] for r in rects), min(r[1] for r in rects), max(r[2] for r in rects), max(r[3] for r in rects))
    report = ['footprint: %d rectangles, %.1f sq ft, grown by %.4f ft (half an exterior wall) from %d foundation '
              'pieces and %d rooms' % (len(rects), sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects), pad,
                                       len(found), len(room_rects))]
    if outlines:
        report.append('  %d foundation outline(s) that are not rectangles, each cut into %d strips of %.3f ft or less '
                      '(the finest that stays within the engine\'s %d rectangles)'
                      % (len(outlines), n, depth / n, MAX_RECTS))
    for r in rects:
        report.append('  x %8.4f .. %8.4f   z %8.4f .. %8.4f   (%6.3f x %6.3f ft)'
                      % (r[0], r[2], r[1], r[3], r[2] - r[0], r[3] - r[1]))
    report.append('  bounding box       x %.4f .. %.4f   z %.4f .. %.4f' % (box[0], box[2], box[1], box[3]))
    problems = []
    if len(rects) > MAX_RECTS:
        problems.append('footprint has %d rectangles, the engine accepts %d (the smallest are ignored)'
                        % (len(rects), MAX_RECTS))
    if walls:
        wbox = (min(r[0] for r in walls), min(r[1] for r in walls), max(r[2] for r in walls), max(r[3] for r in walls))
        report.append('  floor-standing walls x %.4f .. %.4f   z %.4f .. %.4f   (%d axis-aligned boxes)'
                      % (wbox[0], wbox[2], wbox[1], wbox[3], len(walls)))
        out = [w for w in walls if not all(inside(rects, x, z, TOL) for x, z in
                                           ((w[0], w[1]), (w[2], w[1]), (w[0], w[3]), (w[2], w[3]),
                                            ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)))]
        report.append('  walls reaching outside the footprint by more than %.2f ft: %d' % (TOL, len(out)))
        for w in out[:8]:
            problems.append('wall box x %.3f..%.3f z %.3f..%.3f is not inside the footprint' % (w[0], w[2], w[1], w[3]))
        for name, a, b in (('west', box[0], wbox[0]), ('north', box[1], wbox[1]), ('east', box[2], wbox[2]),
                           ('south', box[3], wbox[3])):
            if abs(a - b) > TOL:
                problems.append('footprint %s edge %.4f is %.3f ft from the outermost wall face %.4f'
                                % (name, a, abs(a - b), b))
    return rects, report, problems


# ------------------------------------------------------------------------------------------- rooms
def build_rooms(scene, meas, cls, sweep_ids, sweep_xz, cards=None):
    """`cards`: {caption: sweep id} of the highlight reel as the scene lists it (first stop per caption)."""
    by_tag = {}
    for key, v in ((cls or {}).get('meta', {}).get('rooms', {})).items():
        m = re.match(r'audit (M\d+)', v.get('source', ''))
        if m:
            by_tag.setdefault(m.group(1), key)
    reserved = {r[0] for r in OPEN_ROOMS}
    rooms, used, notes = [], set(), []

    def nearest(bounds, at, prefer=None):
        if prefer in sweep_ids:
            return prefer
        within = [i for i in sweep_ids if bounds[0] <= sweep_xz[i][0] <= bounds[2]
                  and bounds[1] <= sweep_xz[i][1] <= bounds[3]]
        pool = within or list(sweep_ids)
        pick = min(pool, key=lambda i: math.hypot(sweep_xz[i][0] - at[0], sweep_xz[i][1] - at[1]))
        notes.append('room sweep %s is not in the tour: using %s' % (prefer, pick))
        return pick

    for r in meas['rooms']:
        x0, x1, z0, z1 = r['bounds_ft']
        rid = by_tag.get(r['id']) or slug(r['name'])
        if rid in used or rid in reserved:
            rid = slug(r['name'])
        if rid in used or rid in reserved:
            rid = slug(r['id'] + ' ' + r['name'])
        used.add(rid)
        bounds = [r4(x0), r4(z0), r4(x1), r4(z1)]
        at = [r4((x0 + x1) / 2), r4((z0 + z1) / 2)]
        rooms.append({'id': rid, 'label': r['name'].split(' · ')[0], 'bounds': bounds, 'at': at,
                      'sweep': nearest(bounds, at, r.get('node')), 'tag': r['id']})
    meta = (cls or {}).get('meta', {}).get('rooms', {})
    for rid, label, keys, prefer in OPEN_ROOMS:
        bs = [meta[k]['bounds_ft_x0x1z0z1'] for k in keys if k in meta and meta[k].get('bounds_ft_x0x1z0z1')]
        if not bs:
            notes.append('open space %s: no bounds in scene_classification.json, left out' % rid)
            continue
        x0, x1 = min(b[0] for b in bs), max(b[1] for b in bs)
        z0, z1 = min(b[2] for b in bs), max(b[3] for b in bs)
        bounds = [r4(x0), r4(z0), r4(x1), r4(z1)]
        at = [r4((x0 + x1) / 2), r4((z0 + z1) / 2)]
        card = (cards or {}).get(label)                 # the reel's card of this room, when it stands in it
        if card in sweep_ids and bounds[0] <= sweep_xz[card][0] <= bounds[2] and bounds[1] <= sweep_xz[card][1] <= bounds[3]:
            prefer = card
        rooms.append({'id': rid, 'label': label, 'bounds': bounds, 'at': at,
                      'sweep': nearest(bounds, at, prefer), 'tag': None})
    return rooms, notes


def room_of(rooms, x, z, label=None):
    """Id of the smallest room containing (x, z). A point in no room is in a doorway, in the thickness of
    the wall between two rooms: it belongs to the room named `label` (the sweep's own name) when that room
    is within DOORWAY of it, else to the nearest room."""
    def area(r):
        b = r['bounds']
        return (b[2] - b[0]) * (b[3] - b[1])

    def dist(r):
        b = r['bounds']
        return math.hypot(max(b[0] - x, 0, x - b[2]), max(b[1] - z, 0, z - b[3]))
    within = [r for r in rooms if dist(r) == 0]
    if within:
        return min(within, key=area)['id']
    named = [r for r in rooms if label and r['label'] == label and dist(r) <= DOORWAY]
    if named:
        return min(named, key=dist)['id']
    return min(rooms, key=dist)['id'] if rooms else None


# ------------------------------------------------------------------------------------------- documents
def build_tour(scene, meas, cls, version):
    tour = scene['tour']
    nodes = tour['nodes']
    ids = [n['id'] for n in nodes]
    xz = {n['id']: (n['p'][0], n['p'][2]) for n in nodes}
    links = {i: [] for i in ids}
    for a, b in tour.get('edges') or tour.get('undirected_edges') or []:
        if a in links and b in links and a != b:
            if b not in links[a]:
                links[a].append(b)
            if a not in links[b]:
                links[b].append(a)
    start = tour.get('start') if tour.get('start') in links else (ids[0] if ids else None)
    wanted = tour.get('highlights') or HIGHLIGHTS
    # the reel's cards by caption, as the reel is put together below: the start first, a caption once
    caption = {n['id']: n.get('label') or n.get('name') or n['id'] for n in nodes}
    cards = {}
    for i in ([start] if start else []) + [i for i in wanted if i in links]:
        cards.setdefault(caption[i], i)
    rooms, notes = build_rooms(scene, meas, cls, ids, xz, cards)
    sweeps = []
    for n in nodes:
        nid = n['id']
        outdoor = bool(n.get('outdoor', False))
        sweeps.append({
            'id': nid, 'label': n.get('label') or n.get('name') or nid,
            'room': (n.get('room') or 'outside') if outdoor
            else room_of(rooms, *xz[nid], label=n.get('label') or n.get('name')),
            'p': [r4(v) for v in n['p']], 'floor': r4(n.get('floor', FLOOR)),
            'yaw': round(math.degrees(n.get('yaw') or 0.0), 2), 'pitch': round(math.degrees(n.get('pitch') or 0.0), 2),
            'links': links[nid],
            'visible': [i for i in n['visible'] if i in links and i != nid] if n.get('visible') is not None
            else list(links[nid]),
            'outdoor': outdoor})
    # A room nobody can stand in (a closet behind its door) is seen from the sweep in front of it: that sweep
    # belongs to the room, so the chip, the reel and a click on the room all mean it. Not when the sweep is
    # another room's own stop (the Bedroom 4 closet is seen from Bedroom 4's sweep, which stays Bedroom 4's).
    by_id = {s['id']: s for s in sweeps}
    occupied = {s['room'] for s in sweeps}
    own = {r['sweep'] for r in rooms if r['id'] in occupied}
    for r in rooms:
        s = by_id.get(r['sweep'])
        if r['id'] not in occupied and s and not s['outdoor'] and s['id'] not in own:
            notes.append('room %s has no sweep inside: sweep %s in front of it (it stands in %s) belongs to it'
                         % (r['id'], s['id'], s['room']))
            s['room'] = r['id']
    heights = sorted(n['p'][1] for n in nodes if not n.get('outdoor')) or [0.0]
    eye = heights[len(heights) // 2]
    rects, report, problems = footprint(scene, [(r['bounds'][0], r['bounds'][1], r['bounds'][2], r['bounds'][3])
                                                for r in rooms])
    for s in sweeps:
        if not s['outdoor'] and not inside(rects, s['p'][0], s['p'][2]):
            problems.append('sweep %s (%.2f, %.2f) is outside the footprint' % (s['id'], s['p'][0], s['p'][2]))
        for other in s['links']:
            if other not in ids:
                problems.append('sweep %s links to unknown sweep %s' % (s['id'], other))
    for r in rooms:
        b = r['bounds']
        if not all(inside(rects, x, z, TOL) for x in (b[0], b[2]) for z in (b[1], b[3])):
            problems.append('room %s reaches outside the footprint' % r['id'])
    # The highlight reel: one card per place, the entrance first. The cards are captioned with the sweep
    # labels, which several sweeps of a room share ("Kitchen" four times): a second card with a caption the
    # reel already has is left out.
    if len([i for i in wanted if i in links]) != len(wanted):
        notes.append('highlights not in the tour, left out: %s' % ' '.join(i for i in wanted if i not in links))
    highlights, captions = [], set()
    for i in ([start] if start else []) + [i for i in wanted if i in links]:
        if i in highlights:
            continue
        if by_id[i]['label'] in captions:
            notes.append('highlight %s left out: the reel already has a card "%s"' % (i, by_id[i]['label']))
            continue
        highlights.append(i)
        captions.add(by_id[i]['label'])
    if wanted and start and wanted[0] != start:
        notes.append('highlights: the start sweep %s comes first (the list began with %s)' % (start, wanted[0]))
    doc = {'version': version, 'title': TITLE, 'subtitle': SUBTITLE, 'units': 'ft', 'angles': 'deg',
           'eye': r4(eye), 'extent': [r4(v) for v in scene['extent']], 'start': start,
           'footprint': [list(r) for r in rects], 'sweeps': sweeps, 'rooms': rooms, 'highlights': highlights}
    report.append('sweeps: %d, start %s, eye %.4f, extent %s, links %d, highlights %d'
                  % (len(sweeps), start, doc['eye'], doc['extent'], sum(len(s['links']) for s in sweeps) // 2,
                     len(highlights)))
    report.append('rooms: %d' % len(rooms))
    for r in rooms:
        b = r['bounds']
        report.append('  %-18s %-28s x %7.4f .. %7.4f  z %7.4f .. %7.4f  at (%6.3f, %6.3f)  sweep %-3s %s  [%s]'
                      % (r['id'], r['label'], b[0], b[2], b[1], b[3], r['at'][0], r['at'][1], r['sweep'],
                         r['tag'] or '-  ', ' '.join(s['id'] for s in sweeps if s['room'] == r['id'])))
    return doc, report, problems, notes


def build_measurements(scene, meas, version):
    doc = {'version': version}
    doc.update(meas)
    doc['audit'] = scene.get('audit', [])
    return doc


def build_design(scene, design, version):
    rounds = []
    for key, v in (scene.get('design_revision') or {}).items():
        m = re.fullmatch(r'owner_changes(?:_(\d+))?', key)
        if m and isinstance(v, dict):
            rounds.append({'round': int(m.group(1) or 1), 'date': v.get('date'), 'changes': v.get('changes', [])})
    doc = {'version': version, 'order': design.get('order') or list(design['views']), 'views': design['views'],
           'references': design.get('references', {}), 'owner_changes': sorted(rounds, key=lambda r: r['round'])}
    return doc


def content_hashes():
    """tour.json `files`: what the page fetches with its own content hash, and the hash of the page's code."""
    root = sitedata.site_root()

    def digest(paths):
        h = hashlib.sha1()
        for p in paths:
            h.update(p.name.encode('utf-8') + b'\0')
            h.update(p.read_bytes())
        return h.hexdigest()[:12]
    out = {}
    for key, rel in (('model', MODEL), ('plan', sitedata.FILES['plan'])):
        if (root / rel).exists():
            out[key] = digest([root / rel])
    code = sorted((root / CODE[0]).glob('*.js')) + [root / CODE[1]]
    if all(p.exists() for p in code) and len(code) > 1:
        out['code'] = digest(code)
    return out


def dump(doc, rows=()):
    """JSON with one top-level key per line and, for the keys in `rows`, one item per line."""
    def one(v):
        return json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    lines = []
    for k, v in doc.items():
        if k in rows and isinstance(v, list) and v:
            lines.append('%s:[\n%s\n ]' % (one(k), ',\n'.join('  ' + one(x) for x in v)))
        elif k in rows and isinstance(v, dict) and v:
            lines.append('%s:{\n%s\n }' % (one(k), ',\n'.join('  %s:%s' % (one(kk), one(x)) for kk, x in v.items())))
        else:
            lines.append('%s:%s' % (one(k), one(v)))
    return '{\n' + ',\n'.join(' ' + line for line in lines) + '\n}\n'


# a file of the site in a src= / href= attribute of index.html, with or without a ?v= token
INDEX_URL = re.compile(r'''((?<![\w-])(?:src|href)=(["']))((?:\./)?assets/[^"'?#\s<>]+)(?:\?v=[^"'#\s<>&]*)?(?=#|\2)''')


def set_index_version(version, check=False):
    """Put `?v=<version>` on every assets/ file index.html names in a src= / href= attribute (main.js,
    tour.css, the landing picture). Returns (note for the printout, True when index.html is out of date)."""
    p = sitedata.path('index')
    if not p.exists():
        return 'index.html not found: no ?v= tokens set', False
    text = p.read_text(encoding='utf-8')
    found = [m.group(3) for m in INDEX_URL.finditer(text)]
    if not found:
        return 'index.html names no assets/ file in a src= or href= attribute: left untouched', False
    new = INDEX_URL.sub(lambda m: m.group(1) + m.group(3) + '?v=' + version, text)
    names = ', '.join(dict.fromkeys(f.rsplit('/', 1)[-1] for f in found))
    if new == text:
        return 'index.html: %d ?v= tokens already %s (%s)' % (len(found), version, names), False
    if not check:
        sitedata.write_text(p, new)
    return 'index.html: %d ?v= tokens %s %s (%s)' % (len(found), 'would be set to' if check else 'set to',
                                                      version, names), True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--version', help='release label for the three files and the ?v= tokens of index.html')
    ap.add_argument('--out', help='directory to write (default assets/data)')
    ap.add_argument('--check', action='store_true', help='write nothing; exit 1 when a file is out of date')
    ap.add_argument('--quiet', action='store_true', help='do not print the footprint and room tables')
    a = ap.parse_args()
    out = Path(a.out) if a.out else sitedata.path('site_tour').parent
    tour_path = out / Path(sitedata.FILES['site_tour']).name
    version = a.version
    was = sitedata.read_json(tour_path) if tour_path.exists() else {}
    if not version:
        version = was.get('version')
    version = version or datetime.date.today().isoformat() + 'a'

    scene, meas, design = sitedata.load_scene(), sitedata.load_measurements(), sitedata.load_design()
    cls = sitedata.load_classification() if sitedata.path('classification').exists() else None
    tour, report, problems, notes = build_tour(scene, meas, cls, version)
    tour['files'] = content_hashes()
    old_code = (was.get('files') or {}).get('code')
    if old_code and tour['files'].get('code') and old_code != tour['files']['code'] and version == was.get('version'):
        notes.append('the page code (%s/*.js, %s) changed since release %s was stamped: pass --version <new label>, '
                     'or returning visitors keep the cached modules' % (CODE[0], CODE[1], version))
    for key, v in design['views'].items():
        if v.get('image') and not (sitedata.site_root() / v['image']).exists():
            notes.append('design view %s: image %s does not exist' % (key, v['image']))
    files = [(tour_path, dump(tour, ('footprint', 'sweeps', 'rooms'))),
             (out / Path(sitedata.FILES['site_measurements']).name,
              dump(build_measurements(scene, meas, version), ('rooms', 'windows', 'doors', 'audit'))),
             (out / Path(sitedata.FILES['site_design']).name,
              dump(build_design(scene, design, version), ('views', 'references', 'owner_changes')))]
    if not a.quiet:
        print('\n'.join(report))
    for line in notes:
        print('note:', line)
    for line in problems:
        print('PROBLEM:', line)
    stale = 0
    for p, text in files:
        same = p.exists() and p.read_text(encoding='utf-8') == text
        stale += not same
        if not a.check and not same:
            sitedata.write_text(p, text)
        print('%-9s %s  %d bytes  version %s' % ('unchanged' if same else 'stale' if a.check else 'wrote',
                                                 sitedata.rel(p), len(text.encode('utf-8')), version))
    if a.version and out.resolve() != sitedata.path('site_tour').parent.resolve():
        print('index.html: left alone (--out writes somewhere else than the site\'s own data directory)')
    elif a.version:
        note, changed = set_index_version(a.version, a.check)
        stale += changed
        print(note)
    if problems:
        return 2
    return 1 if a.check and stale else 0


if __name__ == '__main__':
    sys.exit(main())
