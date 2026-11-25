#!/usr/bin/env python3
"""Regenerate the Design sheet's roof drawing, assets/design/roof.svg (the picture of the view `roof`).

  python3 tools/web/roof_drawing.py              # writes the file when its bytes change
  python3 tools/web/roof_drawing.py --check      # exit 1 when the file is out of date; writes nothing
  python3 tools/web/roof_drawing.py --out FILE [--lines LINES.json]

A plan of the roof as the model builds it: the ten planes of tools/render/bl/roof.py with their ridges, hips and
valleys, the eaves and rakes, the walls' outer faces under the roof (dashed) and the five skylights. Every number
comes from the model's own modules, read without Blender through apply_revisions_web.blender_spec(): bl/roof.py
(plane outlines, the points where planes meet, pitch, overhang, ridge heights), relayout.py (the walls' outer
faces), bl/revision_spec.py (the skylights' wells) and bl/zones/exterior_layout.py (the porch's piers). Run it
after a change to the roof or to a skylight, like tools/web/dimension_plan.py after a change to the plan.

A valley is drawn as far as it is seen from above: the entry roof lies over the roofs beside it, and its eaves
cover the lower ends of their valleys. The wing's west plane and the garage's east plane are the main roof's
planes carried on; they are tinted where they lie over the wing and the garage.

--lines writes what is drawn (planes with their fall, ridges, hips, valleys, skylights, walls; SCENE feet) as JSON,
for a check against the built roof. The eighth round's check cast rays down on the built planes of house_v7d.blend
on a 0.05 ft grid: every plane falls the way it is drawn at 5 in 12, every drawn ridge and hip is a crest and
every drawn valley a trough of the built surface, the built roof has no crest or trough the drawing lacks, the
eaves stand 1'-0" outside the walls and the skylights' glass is where the rectangles are.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True      # keep tools/ free of __pycache__
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'render'))
import sitedata  # noqa: E402
import apply_revisions_web as A  # noqa: E402  (blender_spec: the roof's, the site's and the kitchen's plain numbers)

F, R, RV, SITE, ft = A.ROOF, A.R, A.RV, A.SITE, A.ft
OUT = 'assets/design/roof.svg'
MAIN, WING, GAR, ENTRY, INK, LINE = '#dde2d8', '#9bb0a0', '#c6cfc0', '#cdb595', '#244b3b', '#586a60'
VALLEY, WALL, GLASS, GLASS_LINE = '#a8673d', '#7a857d', '#eef6f8', '#5f8f96'
S_ = 8.6                            # px per foot; the sheet is 1200 x 700 like the stills' frame


def geometry():
    """What the drawing shows, in SCENE feet (x west -> east, z rear -> street)."""
    pw, pe = SITE.PORCH_POSTS
    ex0, ex1 = F.ENTRY_X            # the entry roof's eaves: the lower roofs' valleys run on under them, unseen
    return {
        # the ten planes of bl/roof.planes(), in its order (the entry's two are drawn last: they lie over the others)
        'planes': {
            'N': [(F.XW_E, F.ZN_E), (F.XE_E, F.ZN_E), F.M2, F.M1],
            'W': [(F.XW_E, F.ZN_E), F.M1, F.A_W, (F.WING_X, F.ZW_R), (F.XW_E, F.ZW_R)],
            'E': [(F.XE_E, F.ZN_E), (F.XE_E, F.ZG_R), (F.GAR_X, F.ZG_R), F.B3, F.B2, F.B1, F.M2],
            'S': [F.M1, F.M2, F.B1, F.T1, F.TP, F.Q_W, F.R_W, F.A_W],
            'WB': [F.B1, F.B2, F.T2, F.T1],
            'SB': [F.B2, F.B3, F.C_E, F.Q_E, F.T2],
            'GW': [F.B3, (F.GAR_X, F.ZG_R), (pe[1], F.ZG_R), (pe[1], R.Z_GAR_OUT), (F.XCE, R.Z_GAR_OUT), F.C_E],
            'WE': [F.A_W, F.R_W, (F.XCW, pw[2]), (pw[0], pw[2]), (pw[0], F.ZW_R), (F.WING_X, F.ZW_R)],
            'EnW': [F.TP, F.V_W, (ex0, F.ENTRY_FRONT), (F.ENTRY_C, F.ENTRY_FRONT)],
            'EnE': [F.TP, (F.ENTRY_C, F.ENTRY_FRONT), (ex1, F.ENTRY_FRONT), F.T3, F.T2, F.T1],
        },
        'fill': {'N': MAIN, 'W': MAIN, 'E': MAIN, 'S': MAIN, 'WB': MAIN, 'SB': MAIN, 'GW': GAR, 'WE': WING,
                 'EnW': ENTRY, 'EnE': ENTRY},
        # the same lines as bl/roof.caps() covers with ridge caps and valley flashing
        'ridges': {'main': (F.M1, F.M2), 'wing': (F.A_W, (F.WING_X, F.ZW_R)), 'garage': (F.B3, (F.GAR_X, F.ZG_R)),
                   'old entry': (F.B1, F.B2), 'entry': (F.TP, (F.ENTRY_C, F.ENTRY_FRONT))},
        'hips': {'north-west': ((F.XW_E, F.ZN_E), F.M1), 'north-east': ((F.XE_E, F.ZN_E), F.M2),
                 'south-west': (F.M1, F.A_W), 'south-east': (F.M2, F.B1), 'old entry east': (F.B2, F.B3),
                 'old entry': (F.B2, F.T2)},
        'valleys': {'wing': (F.A_W, (ex0, F.A_W[1] + (ex0 - F.WING_X))), 'old entry': (F.B1, F.T1),
                    'garage': (F.B3, (ex1, F.B3[1] + (F.GAR_X - ex1))), 'entry west': (F.TP, F.V_W),
                    'entry east': (F.TP, F.T1), 'entry WB': (F.T1, F.T2), 'entry SB': (F.T2, F.T3)},
        # eaves and rakes: the lower roofs' outline as far as it is seen, and the entry roof's
        'edges': [[(ex0, pw[2]), (pw[0], pw[2]), (pw[0], F.ZW_R), (F.XW_E, F.ZW_R), (F.XW_E, F.ZN_E),
                   (F.XE_E, F.ZN_E), (F.XE_E, F.ZG_R), (pe[1], F.ZG_R), (pe[1], R.Z_GAR_OUT), (ex1, R.Z_GAR_OUT)],
                  [F.V_W, (ex0, F.ENTRY_FRONT), (ex1, F.ENTRY_FRONT), F.T3]],
        'skylights': {'kitchen': RV.KITCHEN_SKY, 'living room': RV.LIVING_SKY, 'primary bathroom': RV.PRIMARY_BATH_SKY,
                      'foyer north': RV.FOYER_SKY[0], 'foyer south': RV.FOYER_SKY[1]},
        'walls': [(R.XW_OUT, R.ZN_OUT), (R.XE_OUT, R.ZN_OUT), (R.XE_OUT, R.Z_GAR_OUT), (R.X_FOYER_E, R.Z_GAR_OUT),
                  (R.X_FOYER_E, R.Z_PORCH_N), (R.X_FOYER_W, R.Z_PORCH_N), (R.X_FOYER_W, R.Z_B3_OUT),
                  (R.XW_OUT, R.Z_B3_OUT)],
        # tints: the west plane over the wing (south of the main block's eave line), the east plane over the garage
        'tints': {'W': ([(F.XW_E, F.ZS_E), (F.WING_X, F.ZS_E), (F.WING_X, F.ZW_R), (F.XW_E, F.ZW_R)], WING),
                  'E': ([(F.GAR_X, F.B3[1]), (F.XE_E, F.B3[1] + (F.XE_E - F.GAR_X)), (F.XE_E, F.ZG_R),
                         (F.GAR_X, F.ZG_R)], GAR)},
    }


def X(x):
    return 62 + (x - F.XW_E) * S_


def Y(z):
    return 78 + (z - F.ZN_E) * S_


def pts(poly):
    return ' '.join('%.2f,%.2f' % (X(p[0]), Y(p[1])) for p in poly)


def build():
    """The drawing as one line of SVG."""
    g = geometry()
    o = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700">',
         '<rect width="1200" height="700" fill="#f8f6ee"/>',
         '<text x="52" y="40" font-family="Arial" font-size="21" fill="%s">One roof at %g in 12</text>' % (INK, F.P * 12)]
    for k, poly in g['planes'].items():
        o.append('<polygon points="%s" fill="%s"/>' % (pts(poly), g['fill'][k]))
        if k in g['tints']:
            tint, colour = g['tints'][k]
            o.append('<polygon points="%s" fill="%s" fill-opacity=".85"/>' % (pts(tint), colour))
    o.append('<polygon points="%s" fill="none" stroke="%s" stroke-width="1" stroke-dasharray="5 4"/>' % (pts(g['walls']), WALL))
    for line in g['edges']:
        o.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linejoin="round"/>' % (pts(line), LINE))
    for kind, colour, width in (('hips', LINE, 1.4), ('valleys', VALLEY, 2.2), ('ridges', INK, 2.6)):
        for a, b in g[kind].values():
            o.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s" stroke-linecap="round"/>'
                     % (X(a[0]), Y(a[1]), X(b[0]), Y(b[1]), colour, width))
    for x0, x1, z0, z1 in g['skylights'].values():
        o.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
            X(x0), Y(z0), (x1 - x0) * S_, (z1 - z0) * S_, GLASS, GLASS_LINE))

    def label(x, z, s, size=11, weight=700, fill='#1f3a2f'):
        o.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-family="Arial" font-size="%d" font-weight="%d" '
                 'fill="%s">%s</text>' % (X(x), Y(z), size, weight, fill, s))
    mid = (F.M1[0] + F.M2[0]) / 2
    label(mid, F.ZR - 5.5, 'MAIN HOUSE')
    label(mid, F.ZR - 0.9, 'ridge %s' % ft(A.nominal(F.MAIN_Y)), 10, 400)
    west = (F.XW_E + F.WING_X) / 2      # the room names stand on the wing's west plane, clear of its ridge
    label(west, (F.ZS_E + R.Z_B4_S) / 2 + 1.0, 'BEDROOM 4', 10)
    label(west, (R.Z_B3_N + R.Z_B3_S) / 2, 'BEDROOM 3', 10)
    label(F.GAR_X + 5.1, 42.0, 'GARAGE')
    label(F.GAR_X + 5.1, 44.0, 'ridge %s' % ft(F.GAR_Y), 10, 400)
    label(F.ENTRY_C, F.ENTRY_FRONT + 2.4, 'ENTRY + PORCH', 10)
    label((F.XW_E + F.XE_E) / 2, F.ZW_R + 6.2, 'FRONT / STREET', 12, 400, '#586a60')

    def text(x, y, s, size=15, fill='#2b3a33', weight=400):
        o.append('<text x="%d" y="%d" font-family="Arial" font-size="%d" font-weight="%d" fill="%s">%s</text>'
                 % (x, y, size, weight, fill, s))
    text(570, 104, 'The roof of the architect\'s sheets.', 26, INK)
    text(570, 140, 'Every plane is %g in 12 with %s eaves and a charcoal fascia.' % (F.P * 12, ft(F.OVH)))
    text(570, 166, 'Main ridge %s and garage ridge %s above the floor.' % (ft(A.nominal(F.MAIN_Y)), ft(F.GAR_Y)))
    o.append('<rect x="570" y="204" width="16" height="16" fill="%s"/>' % WING)
    text(598, 218, 'Gable roof over Bedrooms 3 and 4', 18, INK)
    text(598, 246, 'Its west plane is the main roof\'s west plane, carried to the front gable.')
    o.append('<rect x="570" y="284" width="16" height="16" fill="%s"/>' % ENTRY)
    text(598, 298, 'Raised entry gable, level ridge', 18, INK)
    text(598, 326, 'It runs on over the covered porch, %s past the slab.' % ft(F.ENTRY_FRONT - R.Z_PORCH_S))
    o.append('<line x1="570" y1="364" x2="596" y2="364" stroke="%s" stroke-width="2.6"/>' % INK)
    text(610, 369, 'Ridges')
    o.append('<line x1="690" y1="364" x2="716" y2="364" stroke="%s" stroke-width="1.4"/>' % LINE)
    text(730, 369, 'Hips, eaves and rakes')
    o.append('<line x1="570" y1="398" x2="596" y2="398" stroke="%s" stroke-width="2.2"/>' % VALLEY)
    text(610, 403, 'Valleys')
    o.append('<rect x="570" y="424" width="22" height="14" fill="%s" stroke="%s" stroke-width="1.2"/>' % (GLASS, GLASS_LINE))
    text(610, 437, 'Skylights: living room, kitchen, foyer (two), primary bathroom')
    o.append('<line x1="570" y1="468" x2="596" y2="468" stroke="%s" stroke-width="1" stroke-dasharray="5 4"/>' % WALL)
    text(610, 473, 'Outside faces of the walls under the roof')
    text(570, 548, 'ROOF AS ON SHEETS A1.2, A1.3 AND SKA001 · NOT A FRAMING PLAN', 12, '#6b665c')
    text(570, 572, 'The entry roof\'s height follows from the site plan; framing, loads and drainage remain to be '
         'designed.', 12, '#6b665c')
    o.append('</svg>')
    return ''.join(o) + '\n'


def lines():
    """The drawn geometry as plain data (SCENE feet), for a check against the built roof."""
    g = geometry()
    return {'pitch': F.P, 'overhang': F.OVH, 'eave_y': F.EAVE_Y,
            'planes': {k: [list(p) for p in v] for k, v in g['planes'].items()},
            'grad': {k: [F.PL[k][1], F.PL[k][2]] for k in g['planes']},
            'ridges': {k: [list(a), list(b)] for k, (a, b) in g['ridges'].items()},
            'hips': {k: [list(a), list(b)] for k, (a, b) in g['hips'].items()},
            'valleys': {k: [list(a), list(b)] for k, (a, b) in g['valleys'].items()},
            'skylights': {k: list(v) for k, v in g['skylights'].items()}, 'walls': [list(p) for p in g['walls']],
            'entry_x': list(F.ENTRY_X), 'entry_front': F.ENTRY_FRONT,
            'heights': {'main': F.MAIN_Y, 'garage': F.GAR_Y, 'wing': F.WING_Y, 'entry': F.ENTRY_Y}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=str(sitedata.site_root() / OUT))
    ap.add_argument('--check', action='store_true', help='report whether the file is up to date; write nothing')
    ap.add_argument('--lines', metavar='JSON', help='also write the drawn geometry (SCENE feet) to this file')
    a = ap.parse_args()
    svg, out = build(), Path(a.out)
    if a.lines:
        with open(a.lines, 'w', encoding='utf-8') as f:
            json.dump(lines(), f, indent=1)
    if a.check:
        stale = not out.exists() or out.read_text(encoding='utf-8') != svg
        if stale:
            print('out of date:', out)
        return 1 if stale else 0
    print('wrote %s (%d bytes of SVG)' % (out, len(svg)) if sitedata.write_text(out, svg) else 'up to date')
    return 0


if __name__ == '__main__':
    sys.exit(main())
