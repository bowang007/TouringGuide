#!/usr/bin/env python3
"""Record the owner's design changes (bl/revisions.py) in the web tour's data.

  python3 tools/render/apply_revisions_web.py

Updates the measurements (opening list and room notes used by the Dimensions sheet) and notes the changes
in the scene's design_revision. Reads and writes tools/render/data/measurements.json and scene.json through
tools/web/sitedata.py (no index.html). Run it after apply_relayout.py, which resets both files to the
relaid concept data. Idempotent: running it again rewrites the same values.

Fourth round (laundry closet, numbers from bl/revision_spec.py): room M13 and door D17 in the measurements, the
closet's wall boxes and its open door leaf APPENDED to scene.objects (existing objects keep their index, which
bake_web.py's `scene_index` relies on; a re-run updates them in place by name), a scene.audit row, the change
list `design_revision.owner_changes_4`, `tour.highlights` (the reel, with the sweep facing the closet) and, in
tools/render/data/design.json, the Design view `LC` plus one sentence in the kitchen view. design.json is
hand-edited and not rebuilt by apply_relayout.py, so an existing `LC` view is left as it is.

The kitchen stop K0 moves 1 ft east, clear of the closet's open door leaf (NODE_MOVES); place_sweeps.py keeps a
stop where the scene has it. The sweep that faces the closet is `LC` (place_sweeps.py); it joins the tour when
apply_sweeps.py runs, which is the next step of the sequence
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
    'Dining: 6\'-6" x 3\'-2" table in line with the island, four chairs, no island stools (warm oak under a brass '
    'lantern since the third round)',
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
    'Laundry closet in the kitchen\'s south-west corner, where the architect\'s sheet SKA002 draws "W / D" (across '
    'the foyer\'s north end from Bedroom 4): 3\'-10" x 3\'-5" over its walls, 3\'-1 3/8" x 3\'-0 5/8" clear, a '
    'stacked front-load washer and dryer behind a 2\'-6" x 6\'-8" door that is hinged on the east jamb and opens '
    'north',
    'Kitchen south wall re-planned to match the sheet: laundry closet, refrigerator, wall ovens, a short counter '
    'with one glass-front upper, then the cooktop under the hood',
]
LIVING_W = 39.195 - 22.528      # relayout.X_REAR: living room clear width, the plan's 16'-8"
GARAGE_W, GARAGE_D = 39.195 - 21.578, 52.335 - 31.418   # relayout.X_GARAGE / Z_RIGHT: the plan's 17'-7" x 20'-11"


# H1 stands in the plan's foyer (z 28.7 .. 47.2); H2, north of it between the shared bath and the kitchen,
# is the hall
NODE_NAMES = {'H1': 'Foyer', 'H2': 'Hall'}

# ---------------------------------------------------------------------------------------------------------------------
# Fourth round: the laundry closet (bl/revision_spec.py LAUNDRY_*; Blender side: bl/revisions.laundry_closet)
LAUNDRY_ROOM, LAUNDRY_DOOR, LAUNDRY_VIEW = 'M13', 'D17', 'LC'
LAUNDRY_NODE = 'LC'             # the sweep facing the closet's door (place_sweeps.py LAUNDRY['id'])
# what the existing wall and door-leaf boxes of the scene look like (painted partition, painted flush door)
WALL_LOOK = {'color': '#f8f6f0', 'group': 'walls'}
LEAF_LOOK = {'color': '#eeece6', 'group': 'door'}
BOX_LOOK = {'shape': 'box', 'alpha': 1, 'collision': True, 'material': 'paint', 'roughness': 0.86}
LEAF_NAME = 'Laundry closet door — hinged east, open 90 degrees to the north'
# The open door leaf (x 24.22..24.34, z 25.17..27.59) stands 1.3 ft west of the concept's kitchen stop (25.63, 26.00)
# and would fill a quarter of its panorama. The stop moves 1 ft to the middle of the aisle between the island and
# the refrigerator, the most open cell of place_sweeps.py's clearance grid there (2.05 ft); view direction kept.
NODE_MOVES = {'K0': (26.5, 26.5)}
# the highlight reel: the old page's room stops (tools/web/build_site_data.py HIGHLIGHTS) plus the laundry sweep
HIGHLIGHTS = ['E0', 'L0', 'D0', 'K0', LAUNDRY_NODE, 'P0', 'B2', 'B3', 'B4', 'A0', 'A1', 'A3', 'S0', 'C0', 'C3', 'G0']
# design.json, kitchen view: the sentence about the pantry wall and the one that follows it now
KITCHEN_PANTRY = 'a greige pantry wall with a panelled fridge and stainless wall ovens.'
KITCHEN_CLOSET = ('The pantry wall now starts at the new laundry closet in the kitchen\'s south-west corner: closet, '
                  'fridge, ovens, a short counter under one glass-front upper, then the cooktop.')


def ft(v):
    """Feet-inches to the nearest 1/8 inch (tools/web/dimension_plan.py ft())."""
    n = round(v * 96)
    return '%d′%d%s″' % (n // 96, n % 96 // 8, ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞'][n % 8])


def size_labels(meas):
    """Tour-stop size captions from the Dimensions sheet's clear room sizes (so they follow the plan)."""
    rooms = {r['id']: r for r in meas['rooms']}

    def wd(mid, extra=''):
        r = rooms[mid]
        return f"{ft(r['width_ft'])} × {ft(r['depth_ft'])}{extra} · {r.get('basis', 'P')}"
    f = rooms['M11']
    return {
        'P0': wd('M01'), 'B2': wd('M02'), 'A0': wd('M03') + ' · skylight over the shower', 'A1': wd('M04'),
        'C0': wd('M05'), 'B4': wd('M07', ' + separate reach-in closet'), 'B3': wd('M08'), 'A3': wd('M09'),
        'C3': wd('M10'), 'L0': f'{ft(LIVING_W)} living-room width · R',
        'E0': f"3′0″ entrance · {ft(f['width_ft'])} × {ft(f['depth_ft'])} foyer · P",
        'K0': '3′6″ × 4′ skylight · dining table at the island',
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
    """Room M13: the closet's clear inside (between the new side walls, door wall to the kitchen / garage wall)."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    ox0, ox1, oz0, oz1 = RV.LAUNDRY_OUTER
    w, d = x1 - x0, z1 - z0
    uw, ud, uh = (inches(v) for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {'id': LAUNDRY_ROOM, 'kind': 'room', 'basis': 'P', 'name': 'Laundry closet',
            'bounds_ft': [r4(x0), r4(x1), r4(z0), r4(z1)], 'width_ft': r4(w), 'depth_ft': r4(d),
            'area_sqft': round(w * d, 2),
            'note': 'Clear interior size between the new side walls, from the door wall to the kitchen / garage wall; '
                    f'{ft(ox1 - ox0)} × {ft(oz1 - oz0)} over the walls, as printed on the architect\'s sheet. Stacked '
                    f'front-load washer and dryer, each {uw} × {ud} × {uh} in (width × depth × height), under the '
                    f'{RV.LAUNDRY_CEILING:g} ft ceiling.',
            'node': LAUNDRY_NODE}


def laundry_door():
    """Door D17 in the closet's north face (axis 'x': the opening runs along x on the wall line z = c)."""
    d0, d1 = RV.LAUNDRY_DOOR_X
    return {'id': LAUNDRY_DOOR, 'name': 'Laundry closet', 'axis': 'x', 'c': r4(RV.LAUNDRY_DOOR_C), 'start': r4(d0),
            'end': r4(d1), 'width': r4(d1 - d0), 'height': RV.LAUNDRY_DOOR_HEAD, 'sill': 0,
            'head': RV.LAUNDRY_DOOR_HEAD,
            'type': f'Hinged on the {RV.LAUNDRY_DOOR_HINGE} jamb, opens {RV.LAUNDRY_DOOR_SWING} toward the kitchen; '
                    'shown open',
            'node': LAUNDRY_NODE, 'kind': 'door', 'basis': 'P'}


def laundry_objects():
    """SCENE boxes of the closet: its walls (the header over the door included) and the open door leaf."""
    out = []
    for name, x0, x1, y0, y1, z0, z1 in RV.laundry_walls():
        out.append(dict({'name': name, 'p': [r4((x0 + x1) / 2), r4((y0 + y1) / 2), r4((z0 + z1) / 2)],
                         's': [r4(x1 - x0), r4(y1 - y0), r4(z1 - z0)]}, **WALL_LOOK, rot=0, **BOX_LOOK))
    leaf = RV.laundry_leaf()        # at run time: the leaf box follows the hinge geometry of the spec
    out.append(dict({'name': LEAF_NAME, 'p': [r4(v) for v in leaf['center']], 's': [r4(v) for v in leaf['size']]},
                    **LEAF_LOOK, rot=round(leaf['rot'], 6), **BOX_LOOK))
    return out


def laundry_view():
    """The Design window's view of the closet (tools/render/data/hero_cameras.json key LC)."""
    x0, x1, z0, z1 = RV.LAUNDRY_CLEAR
    ox0, ox1, oz0, oz1 = RV.LAUNDRY_OUTER
    uw, ud, uh = (inches(v) + '″' for v in (RV.LAUNDRY_UNIT_W, RV.LAUNDRY_UNIT_D, RV.LAUNDRY_UNIT_H))
    return {
        'label': 'Laundry closet',
        'title': 'A stacked washer and dryer behind one door.',
        'text': 'The architect\'s plan draws a washer / dryer closet in the kitchen\'s south-west corner, across the '
                'foyer\'s north end from Bedroom 4, and it is built there as drawn. A front-load washer with the dryer '
                f'stacked on top stands centred behind a {ft(RV.LAUNDRY_DOOR_W)} × {ft(RV.LAUNDRY_DOOR_HEAD)} door, '
                f'hinged on the {RV.LAUNDRY_DOOR_HINGE} jamb and shown open toward the kitchen. The closet is '
                f'{ft(ox1 - ox0)} × {ft(oz1 - oz0)} over its walls and {ft(x1 - x0)} × {ft(z1 - z0)} clear, under '
                f'the {RV.LAUNDRY_CEILING:g} ft ceiling; the oak floor runs in, a recessed outlet box and the dryer '
                'vent are on the back wall, and a flush light sits in the ceiling. The refrigerator now stands directly '
                f'east of it. The units are generic models of a typical stacked pair ({uw} wide, {ud} deep, {uh} '
                'high each), not a selected product: connections, vent route and clearances need to '
                'be confirmed for the appliances you choose.',
        'refs': [],
        'node': LAUNDRY_NODE,
        'opening': LAUNDRY_ROOM,
        'image': f'assets/design/{LAUNDRY_VIEW}.webp',
    }


def update_design(design):
    """Add the laundry view (when absent) and the kitchen view's sentence about the closet; returns notes."""
    notes = []
    views = design.setdefault('views', {})
    if LAUNDRY_VIEW not in views:
        views[LAUNDRY_VIEW] = laundry_view()
    order = design.setdefault('order', list(views))
    if LAUNDRY_VIEW not in order:
        order.insert(order.index('K0') + 1 if 'K0' in order else len(order), LAUNDRY_VIEW)
    kitchen = views.get('K0')
    if kitchen and KITCHEN_CLOSET not in kitchen.get('text', ''):
        if KITCHEN_PANTRY in kitchen['text']:
            kitchen['text'] = kitchen['text'].replace(KITCHEN_PANTRY, KITCHEN_PANTRY + ' ' + KITCHEN_CLOSET, 1)
        else:
            notes.append('design view K0: the pantry-wall sentence was edited by hand; the laundry closet is not '
                         'mentioned in the kitchen text')
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
    for r in meas['rooms']:
        if r['id'] == 'M07':
            r['note'] = 'Clear interior size; excludes walls. Flat 8 ft ceiling (no vault).'
        if r['id'] == 'M08':
            r['note'] = 'Clear interior size; excludes walls and the bay, which is glazed to the floor.'
        if r['id'] == 'M11':
            r['name'] = 'Foyer'
            r['note'] = ('Clear interior size, from the shared bath\'s south wall to the front wall. The west wall '
                         'lines up with the shared bath\'s east wall.')
    room = laundry_room()
    upsert(meas['rooms'], room)
    upsert(meas['doors'], laundry_door())
    scene = sitedata.load_scene()
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
    upsert(scene.setdefault('audit', []), dict(room))
    design = sitedata.load_design()
    notes = update_design(design)
    for name, changed in (('measurements', sitedata.save_measurements(meas)), ('scene', sitedata.save_scene(scene)),
                          ('design', sitedata.save_design(design))):
        print('updated' if changed else 'unchanged', sitedata.rel(sitedata.path(name)))
    print('windows:', [w['id'] for w in meas['windows']])
    first = min(i for i, o in enumerate(scene['objects']) if o['name'].startswith('Laundry closet'))
    print('laundry closet: room %s %s x %s clear, door %s, scene objects %d..%d (%d), design view %s, sweep %s%s'
          % (room['id'], ft(room['width_ft']), ft(room['depth_ft']), LAUNDRY_DOOR, first, len(scene['objects']) - 1,
             len(scene['objects']) - first, LAUNDRY_VIEW, LAUNDRY_NODE,
             '' if any(n.get('id') == LAUNDRY_NODE for n in scene['tour']['nodes'])
             else ' (not in the tour yet: run apply_sweeps.py)'))
    for line in notes:
        print('note:', line)


if __name__ == '__main__':
    main()
