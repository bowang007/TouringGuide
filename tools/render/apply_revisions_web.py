#!/usr/bin/env python3
"""Record the owner's design changes (bl/revisions.py) in the web tour's data.

  python3 tools/render/apply_revisions_web.py

Updates the measurements (opening list and room notes used by the Dimensions sheet) and notes the changes
in the scene's design_revision. Reads and writes tools/render/data/measurements.json and scene.json through
tools/web/sitedata.py (no index.html). Run it after apply_relayout.py, which resets both files to the
relaid concept data. Idempotent: running it again rewrites the same values.

Laundry closet (fourth round, moved by the owner in the fifth; all numbers from bl/revision_spec.py): the closet
is carved out of Bedroom 4's north-east corner and opens east onto the foyer.
  * measurements.json: room M13 (the clear inside), door D17 (a pair of leaves), and Bedroom 4 (M07), which keeps
    its overall size and loses the closet and its two walls from its area (an L now);
  * scene.objects: the host wall (Bedroom 4's east wall north of the bedroom door, an existing object) is shortened
    IN PLACE to its part south of the opening, which is what leaves the door gap in the plan drawing; the closet's
    wall boxes (west and south walls, the return north of the opening, the door header) and its two open leaves
    are APPENDED. Existing objects keep their index, which bake_web.py's `scene_index` relies on; a re-run updates
    the appended ones in place by name;
  * scene.audit rows, the change lists `design_revision.owner_changes*` (the fifth round, and the fourth marked as
    superseded), `tour.highlights` (the reel, with the sweep facing the closet) and, in
    tools/render/data/design.json, the Design view `LC`. design.json is hand-edited and not rebuilt by
    apply_relayout.py, so an existing `LC` view is left as it is; the tool only prints a note when a view still
    carries a sentence of a superseded layout (SUPERSEDED).

The kitchen stop K0 moves to the west end of the work aisle, clear of the dining chairs that now stand where the
concept had it (NODE_MOVES); place_sweeps.py keeps a stop where the scene has it. The sweep that faces the closet
is `LC` (place_sweeps.py); it joins the tour when apply_sweeps.py runs, which is the next step of the sequence
  apply_relayout.py -> apply_revisions_web.py -> apply_sweeps.py -> extract_scene.py -> tools/web/dimension_plan.py
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'web'))
import sitedata  # noqa: E402
from bl import revision_spec as RV  # noqa: E402

# the dining table's size is the kitchen zone's (bl/zones/kitchen_dining_dining.py RECT_LEN x RECT_W, six chairs)
DINING_TABLE = '6\'-0" x 2\'-9"'
CHANGES = [
    'Bedroom 4 (plan: office): flat 8 ft ceiling instead of the vault',
    'Front bedroom bay (tour: Bedroom 3, plan: Bedroom #2): glazed down to the floor; window seat removed',
    'Foyer: two skylights on the entry roof\'s east slope (hall section and vaulted entry)',
    'Primary bedroom: the 7 ft rear window becomes a two-panel sliding door to the garden (landing outside)',
    'Bedroom 2 (next to the primary): rear window runs to the ceiling (sill 2\'-0" since the third round)',
    'Primary bathroom: tall west window in clear glass, between vanity and shower, sill 2\'-0" since the third round '
    '(an evergreen screen in the fenced side yard outside)',
    'Kitchen skylight: 3\'-6" x 4\'-0" on the continuous east roof plane over the sink / dishwasher '
    '(the concept unit straddled the garage-gable ridge)',
    'Dining: table in line with the island, no island stools (warm oak under a brass lantern since the third round; '
    f'moved to the island\'s west end, {DINING_TABLE} for six, in the fifth round)',
]
CHANGES_2 = [
    'Primary bathroom: a 2\'-0" x 2\'-6" skylight over the shower',
    'The foyer-side wall of Bedroom 4 (office) and Bedroom 3 lines up with the shared bath\'s east wall: both '
    'rooms and the closets between them are 1\'-2 3/4" wider; foyer and covered porch 5\'-9 1/4" wide; '
    'foyer 18\'-6" long as on the plan; the 3\'-0" front door stays centred',
    'Rear landing outside the living room sized as on the plan (3\'-0" deep, garden door to x 38\'-3")',
]
CHANGES_3 = [
    'Bedroom 2 rear window and the primary bathroom window: a 2\'-0" sill instead of glass to the floor (heads stay '
    'at the 8 ft ceiling)',
    'Bedroom 4: the bed is turned across the room, headboard on the north wall, so the room\'s length stays open',
    'Kitchen, primary bathroom, shared bathroom and garage door restyled from the owner\'s style images (styles/)',
]
CHANGES_4 = [
    'Laundry closet with a stacked front-load washer and dryer behind a 2\'-6" x 6\'-8" door opening. It was first '
    'built in the kitchen\'s south-west corner, where the architect\'s sheet SKA002 draws "W / D": superseded by the '
    'fifth round, which moves it to Bedroom 4',
    'Kitchen south wall re-planned around that closet (closet, refrigerator, wall ovens, a short counter, the '
    'cooktop): superseded by the fifth round, the wall is back to its third-round layout',
]
LIVING_W = 39.195 - 22.528      # relayout.X_REAR: living room clear width, the plan's 16'-8"
GARAGE_W, GARAGE_D = 39.195 - 21.578, 52.335 - 31.418   # relayout.X_GARAGE / Z_RIGHT: the plan's 17'-7" x 20'-11"


# H1 stands in the plan's foyer (z 28.7 .. 47.2); H2, north of it between the shared bath and the kitchen,
# is the hall
NODE_NAMES = {'H1': 'Foyer', 'H2': 'Hall'}

# ---------------------------------------------------------------------------------------------------------------------
# The laundry closet in Bedroom 4's north-east corner (bl/revision_spec.py LAUNDRY_*; Blender side:
# bl/revisions.laundry_closet). Fourth round, moved here from the kitchen's south-west corner in the fifth.
LAUNDRY_ROOM, LAUNDRY_DOOR, LAUNDRY_VIEW = 'M13', 'D17', 'LC'
LAUNDRY_NODE = 'LC'             # the sweep facing the closet's doors (place_sweeps.py LAUNDRY['id'])
BEDROOM_4, BEDROOM_4_CLOSET = 'M07', 'M12'
# what the existing wall and door-leaf boxes of the scene look like (painted partition, painted flush door)
WALL_LOOK = {'color': '#f8f6f0', 'group': 'walls'}
LEAF_LOOK = {'color': '#eeece6', 'group': 'door'}
BOX_LOOK = {'shape': 'box', 'alpha': 1, 'collision': True, 'material': 'paint', 'roughness': 0.86}
HOST_TOL = 0.01                 # ft: how far the scene's host wall may be from the spec before the cut is refused
# The concept's kitchen stop (25.63, 26.00) stands 0.4 ft from the south chairs of the dining table since the fifth
# round (the set occupies x 21.43..27.43, z 20.80..25.67: bl/zones/kitchen_dining_dining.py). The stop moves to the
# west end of the work aisle between the island and the cooktop counter, on the runner just east of the table:
# 1.5 ft from the nearest chair, 2.0 ft from the oven tower's end panel, 1.9 ft from the counter (rays on the built
# model), which place_sweeps.py accepts as it is (>= 1.2 ft). Its view direction, east along the aisle, is kept: the
# look point travels with it.
NODE_MOVES = {'K0': (27.6, 26.9)}
# the highlight reel: the old page's room stops (tools/web/build_site_data.py HIGHLIGHTS) plus the laundry sweep,
# after Bedroom 4, which the closet stands next to
HIGHLIGHTS = ['E0', 'L0', 'D0', 'K0', 'P0', 'B2', 'B3', 'B4', LAUNDRY_NODE, 'A0', 'A1', 'A3', 'S0', 'C0', 'C3', 'G0']
# design.json is edited by hand: words of a layout the owner has replaced, reported when a view still has them
SUPERSEDED = ('kitchen\'s south-west corner', 'behind one door', 'table for four')


def ft(v):
    """Feet-inches to the nearest 1/8 inch (tools/web/dimension_plan.py ft())."""
    n = round(v * 96)
    return '%d′%d%s″' % (n // 96, n % 96 // 8, ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][n % 8])


def fi(v):
    """Feet-inches as the change lists write them, to the nearest 1/8 inch: 2'-10", 3'-4 3/8"."""
    n = round(v * 96)
    return '%d\'-%d%s"' % (n // 96, n % 96 // 8, ['', ' 1/8', ' 1/4', ' 3/8', ' 1/2', ' 5/8', ' 3/4', ' 7/8'][n % 8])


def size_labels(meas):
    """Tour-stop size captions from the Dimensions sheet's clear room sizes (so they follow the plan)."""
    rooms = {r['id']: r for r in meas['rooms']}

    def wd(mid, extra=''):
        r = rooms[mid]
        return f"{ft(r['width_ft'])} × {ft(r['depth_ft'])}{extra} · {r.get('basis', 'P')}"
    f = rooms['M11']
    return {
        'P0': wd('M01'), 'B2': wd('M02'), 'A0': wd('M03') + ' · skylight over the shower', 'A1': wd('M04'),
        'C0': wd('M05'), 'B4': wd(BEDROOM_4, ' overall, L-shaped + separate reach-in closet'), 'B3': wd('M08'),
        'A3': wd('M09'), 'C3': wd('M10'), 'L0': f'{ft(LIVING_W)} living-room width · R',
        'E0': f"3′0″ entrance · {ft(f['width_ft'])} × {ft(f['depth_ft'])} foyer · P",
        'K0': '3′6″ × 4′ skylight · dining table at the island\'s west end',
        'G0': f'{ft(GARAGE_W)} × {ft(GARAGE_D)} · R',
    }


def r4(v):
    return round(float(v), 4)


def inches(feet):
    """Inches to the nearest quarter, as '27', '30¼'."""
    n = round(feet * 48)
    return '%d%s' % (n // 4, ['', '¼', '½', '¾'][n % 4])


def upsert(rows, entry, key='id'):
    """Replace the row of `rows` with the same `key` in place, else append; returns the row's index."""
    for i, r in enumerate(rows):
        if r.get(key) == entry[key]:
            rows[i] = entry
            return i
    rows.append(entry)
    return len(rows) - 1


def laundry_room():
    """Room M13: the closet's clear inside. Its width is the north-south size, across the doors, and its depth the
    east-west size, from the door wall to the back wall (the owner's 2'-10" x 3'-0"); bounds_ft stays x0 x1 z0 z1."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    w, d = z1 - z0, x1 - x0
    uw, ud, uh = (inches(v) for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {'id': LAUNDRY_ROOM, 'kind': 'room', 'basis': 'P', 'name': 'Laundry closet',
            'bounds_ft': [r4(x0), r4(x1), r4(z0), r4(z1)], 'width_ft': r4(w), 'depth_ft': r4(d),
            'area_sqft': round(w * d, 2),
            'note': f'Clear interior size: {ft(w)} wide (north to south, across the doors) and {ft(d)} deep (door wall '
                    'to back wall). Carved out of Bedroom 4\'s north-east corner; it opens east onto the foyer through '
                    f'the doors {LAUNDRY_DOOR}. Stacked front-load washer and dryer, each {uw} × {ud} × {uh} in (width '
                    f'× depth × height), facing the foyer, under the {RV.LAUNDRY_CEILING:g} ft ceiling.',
            'node': LAUNDRY_NODE}


def bedroom_4(room):
    """Bedroom 4 (M07) after the cut, in place: the overall clear size stays; the area leaves out the corner the
    closet takes with its two new walls (east-west from the closet's west wall face to the room's east wall,
    north-south from the room's north wall to the closet's south wall face). Returns that corner's size."""
    bx0, bx1, bz0, bz1 = room['bounds_ft']
    cut_w, cut_d = bx1 - RV.LAUNDRY_OUTER[0], RV.LAUNDRY_OUTER[3] - bz0
    if not (0 < cut_w < bx1 - bx0 and 0 < cut_d < bz1 - bz0):
        raise SystemExit('the laundry closet (bl/revision_spec.py LAUNDRY_OUTER) does not lie in the north-east corner '
                         'of %s %s' % (room['id'], room['bounds_ft']))
    room['area_sqft'] = round(room['width_ft'] * room['depth_ft'] - cut_w * cut_d, 2)
    room['note'] = ('Clear interior size overall; excludes walls. L-shaped: the laundry closet is taken out of the '
                    f'north-east corner, and the area leaves out {ft(cut_w)} × {ft(cut_d)} for the closet and its two '
                    'walls. Flat 8 ft ceiling (no vault).')
    return cut_w, cut_d


def laundry_door():
    """Door D17 in the host wall (axis 'z': the opening runs along z on the wall line x = c)."""
    d0, d1 = RV.LAUNDRY_DOOR_Z
    north, south = RV.LAUNDRY_DOOR_HINGES
    return {'id': LAUNDRY_DOOR, 'name': 'Laundry closet doors (pair)', 'axis': RV.LAUNDRY_DOOR_AXIS,
            'c': r4(RV.LAUNDRY_DOOR_C), 'start': r4(d0), 'end': r4(d1), 'width': r4(d1 - d0),
            'height': RV.LAUNDRY_DOOR_HEAD, 'sill': 0, 'head': RV.LAUNDRY_DOOR_HEAD,
            'type': f'Pair of hinged leaves, one on the {north} jamb and one on the {south} jamb, opening '
                    f'{RV.LAUNDRY_DOOR_SWING} into the foyer; shown open {RV.LAUNDRY_DOOR_OPEN_DEG:g} degrees',
            'node': LAUNDRY_NODE, 'kind': 'door', 'basis': 'P'}


def laundry_objects():
    """SCENE boxes to append: the closet's wall pieces (the header over the doors included) and its two open leaves."""
    out = []
    for name, x0, x1, y0, y1, z0, z1 in RV.laundry_walls():
        out.append(dict({'name': name, 'p': [r4((x0 + x1) / 2), r4((y0 + y1) / 2), r4((z0 + z1) / 2)],
                         's': [r4(x1 - x0), r4(y1 - y0), r4(z1 - z0)]}, **WALL_LOOK, rot=0, **BOX_LOOK))
    for leaf in RV.laundry_leaves():    # at run time: the leaf boxes follow the hinge geometry of the spec
        out.append(dict({'name': leaf['name'], 'p': [r4(v) for v in leaf['center']], 's': [r4(v) for v in leaf['size']]},
                        **LEAF_LOOK, rot=round(leaf['rot'], 6), **BOX_LOOK))
    return out


def cut_host_wall(objs):
    """The door opening: shorten the host wall, an existing SCENE object (Bedroom 4's east wall north of the bedroom
    door), to the part the opening leaves of it, from the south jamb to the bedroom door. Only its z extent changes;
    index, name, thickness and look stay. The return north of the opening and the header are among the appended
    boxes. Refuses when the object is not where the spec expects the wall. Returns the object's index."""
    name, x0, x1, _, _, z0, z1 = RV.laundry_host_wall()
    found = [i for i, o in enumerate(objs) if o.get('name') == name and o.get('group') == 'walls']
    if len(found) != 1 or RV.LAUNDRY_DOOR_AXIS != 'z':
        raise SystemExit('laundry closet: expected one wall object named %r running along z, found %d'
                         % (name, len(found)))
    o = objs[found[0]]
    oz0, oz1 = o['p'][2] - o['s'][2] / 2, o['p'][2] + o['s'][2] / 2
    uncut = abs(oz0 - RV.LAUNDRY_HOST_WALL_Z[0]) <= HOST_TOL      # as apply_relayout.py leaves it
    if (abs(o['p'][0] - (x0 + x1) / 2) > HOST_TOL or abs(oz1 - z1) > HOST_TOL
            or not (uncut or abs(oz0 - z0) <= HOST_TOL) or abs(o.get('rot') or 0) > 1e-6):
        raise SystemExit('laundry closet: wall %r is at x %.4f, z %.4f..%.4f in the scene; bl/revision_spec.py expects '
                         'x %.4f, z %.4f..%.4f' % (name, o['p'][0], oz0, oz1, (x0 + x1) / 2,
                                                   RV.LAUNDRY_HOST_WALL_Z[0], z1))
    o['p'] = [o['p'][0], o['p'][1], r4((z0 + z1) / 2)]
    o['s'] = [o['s'][0], o['s'][1], r4(z1 - z0)]
    return found[0]


def changes_5(bed4, cut):
    """The fifth round (2026-11-20), with the closet's and Bedroom 4's numbers from the spec and the schedule."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    return [
        'Laundry closet moved out of the kitchen: it is carved out of Bedroom 4\'s north-east corner and opens east '
        'onto the foyer, on the foyer\'s west side next to the bedroom door. '
        f'{fi(z1 - z0)} wide x {fi(x1 - x0)} deep clear, the stacked front-load washer and dryer behind a pair of doors '
        f'in a {fi(RV.LAUNDRY_DOOR_W)} x {fi(RV.LAUNDRY_DOOR_HEAD)} opening, shown open',
        f'Bedroom 4 is L-shaped after the cut: {fi(bed4["width_ft"])} x {fi(bed4["depth_ft"])} overall as before, less '
        f'{fi(cut[0])} x {fi(cut[1])} for the closet and its two walls ({bed4["area_sqft"]:.1f} sq ft); the desk stands '
        'in the niche between the nightstand and the closet\'s back wall',
        'Dining table moved from the family-room side of the island to the island\'s west end, the shared-bathroom '
        f'side, in line with the island: {DINING_TABLE}, three chairs on each long side, none at the ends, no rug; the '
        'floor between the island and the family room is open',
        'Kitchen south wall back to its third-round layout: refrigerator and double ovens at the west (hall) end, then '
        'the counter under three glass-front uppers and the cooktop under the hood',
    ]


def laundry_view():
    """The Design window's view of the closet (tools/render/data/hero_cameras.json key LC)."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    uw, ud, uh = (inches(v) + '″' for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {
        'label': 'Laundry closet',
        'title': 'A stacked washer and dryer off the foyer, next to Bedroom 4.',
        'text': 'The laundry closet is carved out of Bedroom 4\'s north-east corner and opens onto the foyer, on its '
                'west side right next to the bedroom door. A front-load washer with the dryer stacked on top stands '
                f'centred behind a pair of narrow doors in a {ft(RV.LAUNDRY_DOOR_W)} × {ft(RV.LAUNDRY_DOOR_HEAD)} '
                'opening; the doors are hinged on the two jambs and shown wide open against the foyer wall. The closet '
                f'is {ft(z1 - z0)} wide and {ft(x1 - x0)} deep inside, under the {RV.LAUNDRY_CEILING:g} ft ceiling; the '
                'oak floor runs in from the foyer, a recessed outlet box and the dryer vent are on the back wall, and a '
                'flush light sits in the ceiling. Bedroom 4 keeps its overall size and is L-shaped around the closet. '
                f'The units are generic models of a typical stacked pair ({uw} wide, {ud} deep, {uh} high each), not a '
                'selected product: connections, vent route and clearances need to be confirmed for the appliances you '
                'choose.',
        'refs': [],
        'node': LAUNDRY_NODE,
        'opening': LAUNDRY_ROOM,
        'image': f'assets/design/{LAUNDRY_VIEW}.webp',
    }


def update_design(design):
    """Add the laundry view when it is absent (after Bedroom 4 in the tab order); returns notes about views that
    still carry words of a superseded layout. Nothing a person wrote in design.json is changed."""
    notes = []
    views = design.setdefault('views', {})
    if LAUNDRY_VIEW not in views:
        views[LAUNDRY_VIEW] = laundry_view()
    order = design.setdefault('order', list(views))
    if LAUNDRY_VIEW not in order:
        order.insert(order.index('B4') + 1 if 'B4' in order else len(order), LAUNDRY_VIEW)
    for key, v in views.items():
        for words in SUPERSEDED:
            if words in '%s %s' % (v.get('title', ''), v.get('text', '')):
                notes.append('design view %s still says "%s" (a layout the owner replaced): edit '
                             'tools/render/data/design.json' % (key, words))
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.html:
        ap.error('--html is gone: the data lives in tools/render/data/*.json (see tools/web/sitedata.py)')
    meas = sitedata.load_measurements()
    win = {w['id']: w for w in meas['windows']}

    w = win['W01']
    w.update(name='Primary bedroom / rear sliding door', sill=0, head=RV.SLIDER_HEAD, height=RV.SLIDER_HEAD,
             start=RV.SLIDER_X[0], end=RV.SLIDER_X[1], width=round(RV.SLIDER_X[1] - RV.SLIDER_X[0], 4),
             type='Two-panel sliding glass door to the garden (one fixed, one sliding); landing outside')
    w = win['W02']
    w.update(sill=RV.TALL_SILL, head=8.0, height=round(8.0 - RV.TALL_SILL, 4),
             type='Tall glazing, two panes, from a 2\'-0" sill to the ceiling')
    w = win['W09']
    w.update(sill=0, height=w.get('head', 7.5), type='Three-sided canted bay glazed to the floor; 8 ft wall opening; '
                                                   '2 ft projection')
    w = win['W13']
    z0, z1 = RV.BATH_WIN_Z
    w.update(start=z0, end=z1, width=round(z1 - z0, 4), sill=RV.TALL_SILL, head=8.0, height=round(8.0 - RV.TALL_SILL, 4),
             type='Tall clear glazing from a 2\'-0" sill to the ceiling, with a transom at 6 ft')
    x0, x1, k0, k1 = RV.KITCHEN_SKY
    w = win['W16']
    w.update(start=x0, end=x1, width=round(x1 - x0, 4), height=round(k1 - k0, 4), c=9.4,
             p=[round((x0 + x1) / 2, 3), 9.4, round((k0 + k1) / 2, 3)],
             type='Roof glazing on the east-facing roof plane, 3\'-6" x 4\'-0", over the sink / dishwasher run')
    for i, (sx0, sx1, sz0, sz1) in enumerate(RV.FOYER_SKY):
        wid = f'W{18 + i}'
        entry = win.get(wid) or {'id': wid}
        entry.update(name=f'Foyer skylight {"(hall)" if i == 0 else "(vaulted entry)"}', axis='roof', c=10.9,
                     start=sx0, end=sx1, width=round(sx1 - sx0, 4), height=round(sz1 - sz0, 4), sill=None, head=None,
                     type='Roof glazing on the entry roof\'s east slope', node='H1' if i == 0 else 'E0', kind='skylight',
                     basis='P', p=[round((sx0 + sx1) / 2, 3), 10.9, round((sz0 + sz1) / 2, 3)])
        if wid not in win:
            meas['windows'].append(entry)
            win[wid] = entry
    sx0, sx1, sz0, sz1 = RV.PRIMARY_BATH_SKY
    entry = win.get('W20') or {'id': 'W20'}
    entry.update(name='Primary bathroom skylight (over the shower)', axis='roof', c=9.9, start=sx0, end=sx1,
                 width=round(sx1 - sx0, 4), height=round(sz1 - sz0, 4), sill=None, head=None,
                 type='Roof glazing on the west roof plane, 2\'-0" x 2\'-6", over the shower', node='A0',
                 kind='skylight', basis='P', p=[round((sx0 + sx1) / 2, 3), 9.9, round((sz0 + sz1) / 2, 3)])
    if 'W20' not in win:
        meas['windows'].append(entry)
    bed4 = cut = None
    for r in meas['rooms']:
        if r['id'] == BEDROOM_4:
            bed4, cut = r, bedroom_4(r)
        if r['id'] == 'M08':
            r['note'] = 'Clear interior size; excludes walls and the bay, which is glazed to the floor.'
        if r['id'] == 'M11':
            r['name'] = 'Foyer'
            r['note'] = ('Clear interior size, from the shared bath\'s south wall to the front wall. The west wall '
                         'lines up with the shared bath\'s east wall.')
        if r['id'] == BEDROOM_4_CLOSET:     # the concept's note still gave the closet the vault Bedroom 4 lost
            r['note'] = r['note'].replace(' Cathedral ceiling: 8 ft eaves / 11 ft 6 in ridge, proposed.',
                                          ' Flat 8 ft ceiling.')
    if bed4 is None:
        raise SystemExit('measurements.json has no room %s (Bedroom 4)' % BEDROOM_4)
    room = laundry_room()
    upsert(meas['rooms'], room)
    upsert(meas['doors'], laundry_door())
    scene = sitedata.load_scene()
    host = cut_host_wall(scene['objects'])
    for obj in laundry_objects():       # appended on a freshly relaid scene, updated in place on a re-run
        upsert(scene['objects'], obj, key='name')
    dr = scene.setdefault('design_revision', {})
    vaults = dr.get('vaults', {})
    if 'bedrooms_3_4' in vaults:
        vaults['bedroom_3'] = vaults.pop('bedrooms_3_4')
    dr['owner_changes'] = {'date': '2026-11-18', 'changes': CHANGES}
    dr['owner_changes_2'] = {'date': '2026-11-19', 'changes': CHANGES_2}
    dr['owner_changes_3'] = {'date': '2026-11-19', 'changes': CHANGES_3}
    dr['owner_changes_4'] = {'date': '2026-11-19', 'changes': CHANGES_4}
    dr['owner_changes_5'] = {'date': '2026-11-20', 'changes': changes_5(bed4, cut)}
    ids = scene.get('layout_revision', {}).get('dimension_review', {}).get('room_ids')
    if isinstance(ids, list) and LAUNDRY_ROOM not in ids:
        ids.append(LAUNDRY_ROOM)
    scene.setdefault('tour', {})['highlights'] = list(HIGHLIGHTS)
    labels = size_labels(meas)
    for n in scene['tour']['nodes'] + scene.get('rooms', []):
        if n.get('id') in labels:
            n['size'] = labels[n['id']]
        if n.get('id') in NODE_NAMES:
            n['label'] = n['name'] = NODE_NAMES[n['id']]
        if n.get('id') in NODE_MOVES:
            x, z = NODE_MOVES[n['id']]
            dx, dz = x - n['p'][0], z - n['p'][2]
            if abs(dx) > 1e-4 or abs(dz) > 1e-4:     # the look point travels with the stop: same yaw and pitch
                n['p'] = [x, n['p'][1], z]
                if len(n.get('look') or []) == 3:
                    n['look'] = [n['look'][0] + dx, n['look'][1], n['look'][2] + dz]
    for au in scene.get('audit', []):
        if au.get('id') == 'M11':
            au['name'] = 'Foyer'
            au['note'] = next(r['note'] for r in meas['rooms'] if r['id'] == 'M11')
        if au.get('id') == BEDROOM_4:       # the About sheet's room table: Bedroom 4's reduced area
            au['area_sqft'], au['note'] = bed4['area_sqft'], bed4['note']
    upsert(scene.setdefault('audit', []), dict(room))
    design = sitedata.load_design()
    notes = update_design(design)
    for name, changed in (('measurements', sitedata.save_measurements(meas)), ('scene', sitedata.save_scene(scene)),
                          ('design', sitedata.save_design(design))):
        print('updated' if changed else 'unchanged', sitedata.rel(sitedata.path(name)))
    print('windows:', [w['id'] for w in meas['windows']])
    first = min(i for i, o in enumerate(scene['objects']) if o['name'].startswith('Laundry closet'))
    print('laundry closet: room %s %s x %s clear, doors %s, scene objects %d..%d (%d) appended and wall %d cut, '
          'design view %s, sweep %s%s'
          % (room['id'], ft(room['width_ft']), ft(room['depth_ft']), LAUNDRY_DOOR, first, len(scene['objects']) - 1,
             len(scene['objects']) - first, host, LAUNDRY_VIEW, LAUNDRY_NODE,
             '' if any(n.get('id') == LAUNDRY_NODE for n in scene['tour']['nodes'])
             else ' (not in the tour yet: run apply_sweeps.py)'))
    print('bedroom 4: room %s %s x %s overall, %.2f sq ft without the closet corner %s x %s'
          % (bed4['id'], ft(bed4['width_ft']), ft(bed4['depth_ft']), bed4['area_sqft'], ft(cut[0]), ft(cut[1])))
    for line in notes:
        print('note:', line)


if __name__ == '__main__':
    main()
