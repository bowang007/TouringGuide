#!/usr/bin/env python3
"""Record the owner's design changes (bl/revisions.py) in the web tour's data.

  python3 tools/render/apply_revisions_web.py [--html index.html]

Updates MEASUREMENTS (opening list and room notes used by the Dimensions sheet) and notes the changes
in SCENE.design_revision. Idempotent: running it again rewrites the same values.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from apply_relayout import _grab  # noqa: E402
from bl import revision_spec as RV  # noqa: E402

CHANGES = [
    'Bedroom 4 (plan: office): flat 8 ft ceiling instead of the vault',
    'Front bedroom bay (tour: Bedroom 3, plan: Bedroom #2): glazed down to the floor; window seat removed',
    'Foyer: two skylights on the entry roof\'s east slope (hall section and vaulted entry)',
    'Primary bedroom: the 7 ft rear window becomes a two-panel sliding door to the garden (landing outside)',
    'Bedroom 2 (next to the primary): rear window runs floor to ceiling',
    'Primary bathroom: west window runs floor to ceiling in clear glass, between vanity and shower '
    '(an evergreen screen in the fenced side yard outside)',
    'Kitchen skylight: 3\'-6" x 4\'-0" on the continuous east roof plane over the sink / dishwasher '
    '(the concept unit straddled the garage-gable ridge)',
    'Dining: 6\'-6" x 3\'-2" walnut table in line with the island, four chairs, linear pendant; no island stools',
]
CHANGES_2 = [
    'Primary bathroom: a 2\'-0" x 2\'-6" skylight over the shower',
    'The foyer-side wall of Bedroom 4 (office) and Bedroom 3 lines up with the shared bath\'s east wall: both '
    'rooms and the closets between them are 1\'-2 3/4" wider; foyer and covered porch 5\'-9 1/4" wide; '
    'foyer 18\'-6" long as on the plan; the 3\'-0" front door stays centred',
    'Rear landing outside the living room sized as on the plan (3\'-0" deep, garden door to x 38\'-3")',
]
LIVING_W = 39.195 - 22.528      # relayout.X_REAR: living room clear width, the plan's 16'-8"
GARAGE_W, GARAGE_D = 39.195 - 21.578, 52.335 - 31.418   # relayout.X_GARAGE / Z_RIGHT: the plan's 17'-7" x 20'-11"


# H1 stands in the plan's foyer (z 28.7 .. 47.2); H2, north of it between the shared bath and the kitchen,
# is the hall
NODE_NAMES = {'H1': 'Foyer', 'H2': 'Hall'}


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', default=os.path.join(HERE, '..', '..', 'index.html'))
    a = ap.parse_args()
    src = open(a.html, encoding='utf-8').read()
    meas, m0, m1 = _grab(src, 'const MEASUREMENTS=')
    win = {w['id']: w for w in meas['windows']}

    w = win['W01']
    w.update(name='Primary bedroom / rear sliding door', sill=0, head=RV.SLIDER_HEAD, height=RV.SLIDER_HEAD,
             start=RV.SLIDER_X[0], end=RV.SLIDER_X[1], width=round(RV.SLIDER_X[1] - RV.SLIDER_X[0], 4),
             type='Two-panel sliding glass door to the garden (one fixed, one sliding); landing outside')
    w = win['W02']
    w.update(sill=0, head=8.0, height=8.0, type='Floor-to-ceiling glazing, two panes')
    w = win['W09']
    w.update(sill=0, height=w.get('head', 7.5), type='Three-sided canted bay glazed to the floor; 8 ft wall opening; '
                                                   '2 ft projection')
    w = win['W13']
    z0, z1 = RV.BATH_WIN_Z
    w.update(start=z0, end=z1, width=round(z1 - z0, 4), sill=0, head=8.0, height=8.0,
             type='Floor-to-ceiling clear glazing with a transom at 6 ft')
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
    scene, s0, s1 = _grab(src, 'const SCENE=')
    dr = scene.setdefault('design_revision', {})
    vaults = dr.get('vaults', {})
    if 'bedrooms_3_4' in vaults:
        vaults['bedroom_3'] = vaults.pop('bedrooms_3_4')
    dr['owner_changes'] = {'date': '2026-11-18', 'changes': CHANGES}
    dr['owner_changes_2'] = {'date': '2026-11-19', 'changes': CHANGES_2}
    labels = size_labels(meas)
    for n in scene['tour']['nodes'] + scene.get('rooms', []):
        if n.get('id') in labels:
            n['size'] = labels[n['id']]
        if n.get('id') in NODE_NAMES:
            n['label'] = n['name'] = NODE_NAMES[n['id']]
    for au in scene.get('audit', []):
        if au.get('id') == 'M11':
            au['name'] = 'Foyer'
            au['note'] = next(r['note'] for r in meas['rooms'] if r['id'] == 'M11')
    mj = json.dumps(meas, separators=(',', ':'), ensure_ascii=False)
    sj = json.dumps(scene, separators=(',', ':'), ensure_ascii=False)
    # replace the later block first so the earlier offsets stay valid
    if m0 > s0:
        src = src[:m0] + mj + src[m1:]
        src = src[:s0] + sj + src[s1:]
    else:
        src = src[:s0] + sj + src[s1:]
        src = src[:m0] + mj + src[m1:]
    open(a.html, 'w', encoding='utf-8').write(src)
    print('updated', a.html, 'windows:', [w['id'] for w in meas['windows']])


if __name__ == '__main__':
    main()
