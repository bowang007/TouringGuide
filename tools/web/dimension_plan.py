#!/usr/bin/env python3
"""Regenerate the Dimensions plan drawing, assets/plans/dimension-plan.svg.

The page fetches that file and puts the <svg> into <div id="dimensionPlan"> (it is no longer inlined in
index.html, which this tool never touches). The drawing is built only from the site data files
(tools/web/sitedata.py):
  * tools/render/data/scene.json         walls (objects with group 'walls', shape 'box', standing on the
                          floor), door leaves (group 'door'), the foundation footprint (group 'base'),
                          tour stops (tour.nodes) for the living / kitchen / garage labels and
                          for deciding which side of a wall is "inside" for a window tag;
  * tools/render/data/measurements.json  rooms (id, name, bounds_ft [x0,x1,z0,z1], width_ft, depth_ft,
                          area_sqft, basis), windows and doors (axis 'x' = along x on the wall z=c,
                          'z' = along z on the wall x=c, start/end in feet) and the skylights
                          (axis 'roof', p).

Coordinates are feet: x runs west -> east, z rear (north, garden) -> street (south).

What it draws: the floor footprint, room fills, walls cut at 4 ft (dark) and floor-level pieces
below the cut such as sills and the bay base (light), door leaves, window and skylight symbols,
room labels with clear sizes in feet-inches (a door tag that would cover a room's label moves
across its wall, away from that room: the laundry closet is no bigger than its label; with a label
on both sides, as between the walk-in closet and the vestibule, it slides along the wall), chains of
clear interior dimensions on all four sides (found by scanning the walls), overall outside-face
dimensions, and one hit rect per room, window, skylight and door:
    <rect ... class="review-hit" data-measure="M01" tabindex="0" role="button" aria-label="..."/>
(openings carry class="review-hit opening-hit"), which the page's measurementDetail() /
click handlers use to select an item.

Usage (python3, standard library only), from anywhere:
    python3 tools/web/dimension_plan.py            # rewrite assets/plans/dimension-plan.svg
    python3 tools/web/dimension_plan.py --check    # exit 1 if the file is out of date (no writes)
    python3 tools/web/dimension_plan.py --stdout   # print the SVG only
    python3 tools/web/dimension_plan.py --svg-out other.svg

The file is the bare <svg>...</svg> preceded by an XML declaration line; a page that inserts the text
with innerHTML should drop that first line (or parse the file with DOMParser).

Idempotent: the output depends only on the scene and the measurements, so re-running it after the data
changes replaces the old drawing and re-running it without changes rewrites nothing.
"""
import argparse
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

# Drawing scale and palette (the page's dimension-sheet language).
S = 26.0                      # px per foot
CUT = 4.0                     # plan cut height, ft
INK, GREEN, MUTED, PAPER = '#263c35', '#39755b', '#68786f', '#fbfaf6'
WALL, WALL_LOW = '#4c5952', '#b9c2bb'
FOOT, ROOM, WET, CLOSET = '#f0ede5', '#f2eee3', '#e8ece6', '#ece8dc'
GLASS, LEAF, LEAF_LINE = '#6e9d9d', '#c9b78f', '#8f8062'
TAG_FILL, TAG_LINE = '#fffef8', '#97aca1'

# Spaces the schedule does not measure, labelled at their tour stop: (node, title, subtitle, place),
# place = (dx, dz) feet from the stop, or 'span' to centre the label between the walls around the stop.
EXTRA_LABELS = [('L0', 'LIVING ROOM', 'Open plan', (0, 0)), ('K0', 'KITCHEN + DINING', 'Open plan', (0, -3)),
                ('G0', 'GARAGE', '17′7⅜″ × 20′11″', 'span')]   # relayout X_GARAGE / Z_RIGHT (the plan's 17'-7" x 20'-11")
SOURCE_LINE = "Architect's plan · sizes/sizes.pdf, sheet SKA002 (Nov 13 2026) · clear interior sizes"


# ---------------------------------------------------------------------------------------------
def ft(v):
    """Feet-inches to the nearest 1/8 inch; same output as the page's ft()."""
    n = round(v * 96)
    return '%d′%d%s″' % (n // 96, n % 96 // 8, ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][n % 8])


def f(v):
    return ('%.2f' % v).rstrip('0').rstrip('.')


def attrs(**kw):
    out = []
    for k, v in kw.items():
        if v is None:
            continue
        k = k.rstrip('_').replace('_', '-')
        out.append('%s="%s"' % (k, escape(f(v) if isinstance(v, float) else str(v), {'"': '&quot;'})))
    return ' '.join(out)


class Svg:
    def __init__(self):
        self.parts = []
        self.box = [math.inf, math.inf, -math.inf, -math.inf]

    def grow(self, x0, y0, x1, y1):
        b = self.box
        b[0], b[1], b[2], b[3] = min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)

    def add(self, s, bbox=None):
        self.parts.append(s)
        if bbox:
            self.grow(*bbox)

    def rect(self, x, y, w, h, track=True, **kw):
        self.add('<rect %s/>' % attrs(x=float(x), y=float(y), width=float(w), height=float(h), **kw),
                 (x, y, x + w, y + h) if track else None)

    def line(self, x1, y1, x2, y2, **kw):
        self.add('<line %s/>' % attrs(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2), **kw),
                 (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def text(self, x, y, s, size, fill=INK, weight=400, anchor='middle', rotate=None, track=True, **kw):
        tr = 'rotate(%s %s %s)' % (f(rotate), f(x), f(y)) if rotate else None
        self.add('<text %s>%s</text>' % (attrs(x=float(x), y=float(y), font_size=size, fill=fill, font_weight=weight,
                                                text_anchor=anchor, transform=tr, **kw), escape(s)))
        if track:
            w = text_w(s, size, weight)
            x0 = x - w / 2 if anchor == 'middle' else x - w if anchor == 'end' else x
            if rotate:
                self.grow(x - size, y - w / 2, x + size, y + w / 2)
            else:
                self.grow(x0, y - size, x0 + w, y + size * .3)


def text_w(s, size, weight=400):
    return len(s) * size * (0.62 if int(weight) >= 600 else 0.55)


# ---------------------------------------------------------------------------------------------
def floor_pieces(objs, groups):
    """Axis-aligned or rotated boxes in `groups` that stand on the floor: (obj, cut) pairs, where
    cut is True when the piece reaches the 4 ft plan cut."""
    out = []
    for o in objs:
        if o.get('group') not in groups or o.get('shape') != 'box':
            continue
        bottom, top = o['p'][1] - o['s'][1] / 2, o['p'][1] + o['s'][1] / 2
        if bottom > 1.5:
            continue          # headers, transoms, gables: above the cut
        out.append((o, top >= CUT))
    return out


def box_corners(o):
    (cx, _, cz), (sx, _, sz), r = o['p'], o['s'], o.get('rot') or 0
    c, s = math.cos(r), math.sin(r)
    pts = []
    for dx, dz in ((-sx / 2, -sz / 2), (sx / 2, -sz / 2), (sx / 2, sz / 2), (-sx / 2, sz / 2)):
        # rotation about the vertical axis, as three.js applies rotation.y (x' = x c + z s, z' = -x s + z c)
        pts.append((cx + dx * c + dz * s, cz - dx * s + dz * c))
    return pts


def aabb(o):
    if abs(o.get('rot') or 0) > 1e-6:
        return None
    (cx, _, cz), (sx, _, sz) = o['p'], o['s']
    return cx - sx / 2, cx + sx / 2, cz - sz / 2, cz + sz / 2


def chain(walls, axis, at, merge=0.6):
    """Clear spans between walls along a scan line. axis 'x': line z=at, spans along x;
    axis 'z': line x=at, spans along z. Returns [(a, b)] inner faces."""
    hits = []
    for o in walls:
        b = aabb(o)
        if not b:
            continue
        x0, x1, z0, z1 = b
        if axis == 'x' and z0 <= at <= z1 and (x1 - x0) < 1.0:
            hits.append([x0, x1])
        if axis == 'z' and x0 <= at <= x1 and (z1 - z0) < 1.0:
            hits.append([z0, z1])
    hits.sort()
    merged = []
    for h in hits:
        if merged and h[0] - merged[-1][1] < merge:
            merged[-1][1] = max(merged[-1][1], h[1])
        else:
            merged.append(h)
    return [(merged[i][1], merged[i + 1][0]) for i in range(len(merged) - 1)]


# ---------------------------------------------------------------------------------------------
def build(scene, meas):
    objs = scene['objects']
    X = lambda v: v * S          # noqa: E731  (feet -> px)
    svg = Svg()
    walls = floor_pieces(objs, ('walls',))
    cut_walls = [o for o, c in walls if c]
    # overall extents: straight wall runs only (the bay's short piers and angled faces project beyond)
    straight = [b for b in (aabb(o) for o in cut_walls) if b and max(b[1] - b[0], b[3] - b[2]) >= 1.0]
    ox0, ox1 = min(b[0] for b in straight), max(b[1] for b in straight)      # outside faces
    oz0, oz1 = min(b[2] for b in straight), max(b[3] for b in straight)
    nodes = {n['id']: n for n in (scene.get('tour') or {}).get('nodes', [])}
    rooms, windows, doors = meas['rooms'], meas['windows'], meas['doors']
    node_room = {}
    for r in rooms:
        node_room.setdefault(r.get('node'), r)

    # Footprint and room fills.
    for o in objs:
        if o.get('group') == 'base' and o.get('shape') == 'box' and 'oundation' in o.get('name', ''):
            pts = box_corners(o)
            svg.add('<polygon %s/>' % attrs(points=' '.join('%s,%s' % (f(X(a)), f(X(b))) for a, b in pts), fill=FOOT))
    for r in rooms:
        x0, x1, z0, z1 = r['bounds_ft']
        low = r['name'].lower()
        fill = WET if 'bath' in low else CLOSET if 'closet' in low else ROOM
        svg.rect(X(x0), X(z0), X(x1 - x0), X(z1 - z0), fill=fill)

    # Floor-level pieces below the cut (sills, bay base), door leaves, then the cut walls.
    for o, c in walls:
        if not c:
            svg.add('<polygon %s/>' % attrs(points=' '.join('%s,%s' % (f(X(a)), f(X(b))) for a, b in box_corners(o)),
                                            fill=WALL_LOW, stroke=WALL_LOW, stroke_width=0.6))
    for o, _ in floor_pieces(objs, ('door', 'garageDoor')):
        svg.add('<polygon %s/>' % attrs(points=' '.join('%s,%s' % (f(X(a)), f(X(b))) for a, b in box_corners(o)),
                                        fill=LEAF, stroke=LEAF_LINE, stroke_width=0.7))
    for o in cut_walls:
        svg.add('<polygon %s/>' % attrs(points=' '.join('%s,%s' % (f(X(a)), f(X(b))) for a, b in box_corners(o)),
                                        fill=WALL, stroke=WALL, stroke_width=0.5))

    # Room labels are laid out first (and drawn after the openings), so that a door tag can keep off them.
    def room_label(r):
        """Centre, size, scale and lines of a room's label: name, clear size, area; scaled down to fit the room."""
        x0, x1, z0, z1 = r['bounds_ft']
        lines = [(r['name'].upper(), 15, 700, INK), ('%s × %s' % (ft(r['width_ft']), ft(r['depth_ft'])), 14, 400, INK),
                 ('%.1f sq ft · %s' % (r['area_sqft'], r.get('basis', '')), 12, 400, MUTED)]
        rw, rh = X(x1 - x0) - 10, X(z1 - z0) - 8
        for keep in (3, 2):
            ls = lines[:keep]
            w = max(text_w(s, sz, wt) for s, sz, wt, _ in ls) + 14
            h = sum(sz * 1.3 for _, sz, _, _ in ls) + 8
            k = min(1.0, rw / w, rh / h)
            if k >= .72 or keep == 2:
                break
        k = max(k, .55)
        return X((x0 + x1) / 2), X((z0 + z1) / 2), w * k, h * k, k, ls

    room_labels = [room_label(r) for r in rooms]

    # Openings: symbol on the wall, a tag, and a hit rect around both.
    hits = []

    def node_xz(o):
        n = nodes.get(o.get('node'))
        if n:
            return n['p'][0], n['p'][2]
        return (ox0 + ox1) / 2, (oz0 + oz1) / 2

    def tag_size(label, size=10):
        return text_w(label, size, 600) + 10, size + 8

    def tag(cx, cy, label, size=10):
        w, h = tag_size(label, size)
        svg.rect(cx - w / 2, cy - h / 2, w, h, fill=TAG_FILL, stroke=TAG_LINE, stroke_width=0.8, rx=4)
        svg.text(cx, cy + size * .36, label, size, fill=GREEN, weight=600)
        return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2

    def overlaps_door(w):
        return any(d['axis'] == w['axis'] and abs(d['c'] - w['c']) < .3 and
                   min(d['end'], w['end']) - max(d['start'], w['start']) > .3 for d in doors)

    for w in windows:
        if w['axis'] == 'roof':
            cx, cz = (w['p'][0], w['p'][2]) if w.get('p') else ((w['start'] + w['end']) / 2, w['c'])
            ww, dd = w['width'], w['height']
            svg.rect(X(cx - ww / 2), X(cz - dd / 2), X(ww), X(dd), fill='#d1e1dc88', stroke=GLASS,
                     stroke_width=1.2, stroke_dasharray='6 4')
            svg.line(X(cx - ww / 2), X(cz - dd / 2), X(cx + ww / 2), X(cz + dd / 2), stroke=GLASS, stroke_width=.7,
                     stroke_dasharray='6 4')
            svg.line(X(cx - ww / 2), X(cz + dd / 2), X(cx + ww / 2), X(cz - dd / 2), stroke=GLASS, stroke_width=.7,
                     stroke_dasharray='6 4')
            t = tag(X(cx), X(cz), w['id'] + ' skylight', 10)
            hits.append((w, (X(cx - ww / 2), X(cz - dd / 2), X(cx + ww / 2), X(cz + dd / 2)), t))
            continue
        above = overlaps_door(w)
        a, b, c, th = w['start'], w['end'], w['c'], 0.45
        nx, nz = node_xz(w)
        if w['axis'] == 'x':
            out = 1 if nz < c else -1            # tag on the side away from the room
            r = (X(a), X(c - th / 2), X(b), X(c + th / 2))
            if above:
                svg.line(X(a), X(c + out * .55), X(b), X(c + out * .55), stroke=GLASS, stroke_width=1.6, stroke_dasharray='5 4')
            else:
                svg.rect(r[0], r[1], r[2] - r[0], r[3] - r[1], fill=PAPER, stroke=GLASS, stroke_width=1)
                svg.line(X(a), X(c), X(b), X(c), stroke=GLASS, stroke_width=1.4)
            t = tag(X((a + b) / 2), X(c) + out * (46 if above else 24), w['id'] + (' above' if above else ''), 11)
        else:
            out = 1 if nx < c else -1
            r = (X(c - th / 2), X(a), X(c + th / 2), X(b))
            if above:
                svg.line(X(c + out * .55), X(a), X(c + out * .55), X(b), stroke=GLASS, stroke_width=1.6, stroke_dasharray='5 4')
            else:
                svg.rect(r[0], r[1], r[2] - r[0], r[3] - r[1], fill=PAPER, stroke=GLASS, stroke_width=1)
                svg.line(X(c), X(a), X(c), X(b), stroke=GLASS, stroke_width=1.4)
            t = tag(X(c) + out * 30, X((a + b) / 2), w['id'], 11)
        hits.append((w, r, t))

    for d in doors:
        a, b, c = d['start'], d['end'], d['c']
        if d['axis'] == 'x':
            r = (X(a), X(c - .3), X(b), X(c + .3))
            svg.line(X(a), X(c), X(b), X(c), stroke=LEAF_LINE, stroke_width=1, stroke_dasharray='3 3')
        else:
            r = (X(c - .3), X(a), X(c + .3), X(b))
            svg.line(X(c), X(a), X(c), X(b), stroke=LEAF_LINE, stroke_width=1, stroke_dasharray='3 3')
        # The tag sits on the opening. Where that would cover a room's label (a closet as small as its own label,
        # with the door in the wall beside it), it moves across the wall to the side away from that room.
        cx, cy = ox, oy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        w, h = tag_size(d['id'], 10)

        def covered(x, y):
            return [(lx, ly, lw, lh) for lx, ly, lw, lh, _, _ in room_labels
                    if abs(x - lx) < (w + lw) / 2 and abs(y - ly) < (h + lh) / 2]
        for lx, ly, lw, lh, _, _ in room_labels:
            if abs(cx - lx) < (w + lw) / 2 and abs(cy - ly) < (h + lh) / 2:
                if d['axis'] == 'x':
                    cy = ly + (1 if cy >= ly else -1) * ((h + lh) / 2 + 3)
                else:
                    cx = lx + (1 if cx >= lx else -1) * ((w + lw) / 2 + 3)
        if covered(cx, cy):
            # A label on each side of the wall, both in line with the door (the walk-in closet and the vestibule
            # beside it): there is no free side, so the tag stays on the wall line and slides along it, to the
            # nearer end of the labels in its way.
            hit = covered(ox, oy)
            if d['axis'] == 'x':
                ends = (min(lx - (w + lw) / 2 for lx, _, lw, _ in hit) - 3, max(lx + (w + lw) / 2 for lx, _, lw, _ in hit) + 3)
                spots = [(x, oy) for x in sorted(ends, key=lambda x: abs(x - ox))]
            else:
                ends = (min(ly - (h + lh) / 2 for _, ly, _, lh in hit) - 3, max(ly + (h + lh) / 2 for _, ly, _, lh in hit) + 3)
                spots = [(ox, y) for y in sorted(ends, key=lambda y: abs(y - oy))]
            cx, cy = next((p for p in spots if not covered(*p)), (cx, cy))
        t = tag(cx, cy, d['id'], 10)
        hits.append((d, r, t))

    # Labels for spaces outside the schedule.
    every_wall = cut_walls + [o for o, c in walls if not c]
    for nid, title, sub, place in EXTRA_LABELS:
        n = nodes.get(nid)
        if not n:
            continue
        lx, lz = n['p'][0], n['p'][2]
        if place == 'span':
            sx = [s for s in chain(every_wall, 'x', lz) if s[0] <= lx <= s[1]]
            sz = [s for s in chain(every_wall, 'z', lx) if s[0] <= lz <= s[1]]
            lx = sum(sx[0]) / 2 if sx else lx
            lz = sum(sz[0]) / 2 if sz else lz
        else:
            lx, lz = lx + place[0], lz + place[1]
        x, y = X(lx), X(lz)
        w = max(text_w(title, 17, 700), text_w(sub, 13)) + 24
        svg.rect(x - w / 2, y - 24, w, 48, fill=PAPER, fill_opacity='.85', rx=4)
        svg.text(x, y - 3, title, 17, weight=700)
        svg.text(x, y + 16, sub, 13, fill=MUTED)

    # Room labels: name, clear size, area; scaled down to fit the room.
    for cx, cy, w, h, k, ls in room_labels:
        svg.rect(cx - w / 2, cy - h / 2, w, h, fill='#fffdf7', fill_opacity='.88', rx=4)
        y = cy - h / 2 + 4 * k
        for s, sz, wt, col in ls:
            y += sz * 1.3 * k
            svg.text(cx, y - sz * .3 * k, s, round(sz * k, 1), fill=col, weight=wt)

    # Dimensions: clear-span chains (scanned from the walls) and overall outside faces.
    def dim(a, b, at, axis, label, size=13):
        if axis == 'x':
            svg.line(a, at, b, at, stroke=GREEN, stroke_width=1)
            for v in (a, b):
                svg.line(v, at - 7, v, at + 7, stroke=GREEN, stroke_width=.8)
                svg.line(v - 4, at + 4, v + 4, at - 4, stroke=GREEN, stroke_width=1.6)
            svg.text((a + b) / 2, at - 5, label, size, fill=GREEN, weight=600)
        else:
            svg.line(at, a, at, b, stroke=GREEN, stroke_width=1)
            for v in (a, b):
                svg.line(at - 7, v, at + 7, v, stroke=GREEN, stroke_width=.8)
                svg.line(at - 4, v + 4, at + 4, v - 4, stroke=GREEN, stroke_width=1.6)
            svg.text(at - 5, (a + b) / 2, label, size, fill=GREEN, weight=600, rotate=-90)

    cw = every_wall
    for axis, at, pos, short in (('x', oz0 + 3.0, X(oz0) - 64, None), ('x', oz1 - 3.5, X(oz1) + 112, None),
                                 ('z', ox0 + 1.0, X(ox0) - 68, None), ('z', ox1 - 1.0, X(ox1) + 74, None)):
        for a, b in chain(cw, axis, at):
            if b - a < 1.2:
                continue
            dim(X(a), X(b), pos, axis, ft(b - a), 12 if X(b - a) < 70 else 13)
    dim(X(ox0), X(ox1), X(oz0) - 100, 'x', ft(ox1 - ox0) + ' overall', 14)
    dim(X(ox0), X(ox1), X(oz1) + 148, 'x', ft(ox1 - ox0) + ' overall', 14)
    dim(X(oz0), X(oz1), X(ox0) - 104, 'z', ft(oz1 - oz0) + ' overall', 14)
    svg.text(X((ox0 + ox1) / 2), X(oz0) - 128, 'BACKYARD / GARDEN · NORTH', 15, fill=MUTED, weight=600, letter_spacing='1')
    svg.text(X((ox0 + ox1) / 2), X(oz1) + 182, 'STREET · W MCKINLEY AVE · SOUTH', 15, fill=MUTED, weight=600, letter_spacing='1')

    # Hit rects last so they sit on top: rooms, then openings (smaller, so they win where they overlap).
    for r in rooms:
        x0, x1, z0, z1 = r['bounds_ft']
        svg.add('<rect %s/>' % attrs(x=float(X(x0)), y=float(X(z0)), width=float(X(x1 - x0)), height=float(X(z1 - z0)),
                                     fill='transparent', stroke='none', stroke_width=1, class_='review-hit',
                                     data_measure=r['id'], tabindex=0, role='button', aria_label=r['name']))
    for o, r, t in hits:
        x0, y0 = min(r[0], t[0]) - 3, min(r[1], t[1]) - 3
        x1, y1 = max(r[2], t[2]) + 3, max(r[3], t[3]) + 3
        svg.add('<rect %s/>' % attrs(x=float(x0), y=float(y0), width=float(x1 - x0), height=float(y1 - y0),
                                     fill='transparent', stroke='none', stroke_width=1, class_='review-hit opening-hit',
                                     data_measure=o['id'], tabindex=0, role='button', aria_label=o['name']))

    # Title block and legend, placed from the drawing's extent.
    bx0, by0, bx1, by1 = svg.box
    top = by0 - 120
    head = Svg()
    head.text(bx0, top + 18, '1095 W MCKINLEY', 18, fill=GREEN, weight=700, anchor='start')
    head.text(bx0, top + 58, 'Room dimensions + opening details', 34, weight=650, anchor='start')
    head.text(bx0, top + 88, SOURCE_LINE, 16, fill=MUTED, anchor='start')
    head.line(bx0, top + 104, max(bx1, bx0 + 900), top + 104, stroke='#d7dfd5', stroke_width=1.4)
    ly = by1 + 34
    lx = bx0
    for kind in ('wall', 'low', 'window', 'door', 'skylight'):
        if kind == 'wall':
            head.rect(lx, ly - 9, 26, 9, fill=WALL)
            label = 'Wall (cut at 4 ft)'
        elif kind == 'low':
            head.rect(lx, ly - 9, 26, 9, fill=WALL_LOW)
            label = 'Below cut: sill / bay base'
        elif kind == 'window':
            head.rect(lx, ly - 9, 26, 9, fill=PAPER, stroke=GLASS, stroke_width=1)
            head.line(lx, ly - 4.5, lx + 26, ly - 4.5, stroke=GLASS, stroke_width=1.4)
            label = 'Window (W)'
        elif kind == 'door':
            head.rect(lx, ly - 7, 26, 5, fill=LEAF, stroke=LEAF_LINE, stroke_width=.7)
            label = 'Door leaf / opening (D)'
        else:
            head.rect(lx, ly - 11, 26, 13, fill='#d1e1dc88', stroke=GLASS, stroke_width=1.2, stroke_dasharray='6 4')
            label = 'Skylight'
        head.text(lx + 34, ly, label, 13, fill=MUTED, anchor='start')
        lx += 34 + text_w(label, 13) + 26
    head.text(bx0, ly + 26, 'Sizes are clear interior dimensions (walls excluded). P = proposed, R = retained original. '
              'Select a room or a W / D tag for its details.', 13, fill=MUTED, anchor='start')

    pad = 24
    vb0, vb1 = min(bx0, head.box[0]) - pad, min(by0, head.box[1]) - pad
    vb2, vb3 = max(bx1, head.box[2]) + pad, max(by1, head.box[3]) + pad
    W, H = vb2 - vb0, vb3 - vb1
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="%s %s %s %s" role="img" '
           'aria-label="Dimensioned floor plan: rooms, windows and doors">' % (round(W), round(H), f(vb0), f(vb1), f(W), f(H)),
           '<style>text{font-family:Arial,DejaVu Sans,sans-serif}</style>',
           '<rect %s/>' % attrs(x=float(vb0), y=float(vb1), width=float(W), height=float(H), fill=PAPER)]
    out += head.parts + svg.parts
    out.append('</svg>')
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--html', help=argparse.SUPPRESS)
    ap.add_argument('--svg-out', default=str(sitedata.path('plan')))
    ap.add_argument('--check', action='store_true', help='report whether the file is up to date; write nothing')
    ap.add_argument('--stdout', action='store_true', help='print the SVG and exit')
    a = ap.parse_args()
    if a.html:
        ap.error('--html is gone: the drawing is built from tools/render/data/*.json and written to '
                 'assets/plans/dimension-plan.svg only (see tools/web/sitedata.py)')
    svg = build(sitedata.load_scene(), sitedata.load_measurements())
    if a.stdout:
        sys.stdout.write(svg + '\n')
        return 0
    svg_path = Path(a.svg_out)
    stale = not svg_path.exists() or svg_path.read_text(encoding='utf-8') != sitedata.plan_svg_file(svg)
    if a.check:
        if stale:
            print('out of date:', svg_path)
        return 1 if stale else 0
    if sitedata.save_plan_svg(svg, out=svg_path):
        print('wrote', svg_path, '(%d bytes of SVG)' % len(svg))
    else:
        print('up to date')
    return 0


if __name__ == '__main__':
    sys.exit(main())
