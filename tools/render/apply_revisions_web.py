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
    'Primary bathroom: west window runs floor to ceiling, obscured glass, between vanity and shower',
    'Kitchen skylight: 3\'-6" x 4\'-0" on the continuous east roof plane over the sink / dishwasher '
    '(the concept unit straddled the garage-gable ridge)',
    'Dining: 6\'-6" x 3\'-2" walnut table in line with the island, four chairs, linear pendant; no island stools',
]


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
             type='Floor-to-ceiling obscured glazing with a transom at 6 ft')
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
    for r in meas['rooms']:
        if r['id'] == 'M07':
            r['note'] = 'Clear interior size; excludes walls. Flat 8 ft ceiling (no vault).'
        if r['id'] == 'M08':
            r['note'] = 'Clear interior size; excludes walls and the bay, which is glazed to the floor.'
    scene, s0, s1 = _grab(src, 'const SCENE=')
    dr = scene.setdefault('design_revision', {})
    vaults = dr.get('vaults', {})
    if 'bedrooms_3_4' in vaults:
        vaults['bedroom_3'] = vaults.pop('bedrooms_3_4')
    dr['owner_changes'] = {'date': '2026-11-18', 'changes': CHANGES}
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
