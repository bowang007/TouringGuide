#!/usr/bin/env python3
"""One-off copy update for the modern, path-traced version of the tour (idempotent).

Rewrites the on-page text that described the earlier AI concept images and the traditional
styling (title, badges, hints, Info/Welcome/Design windows, DESIGN_DATA, SCENE.styling) so it
matches the path-traced renders of the modern design. Geometry facts (sizes, sills, heads, ridge
heights) are kept verbatim.

  python3 tools/web/update_copy.py [--check]
"""
import json
import re
import sys
from pathlib import Path

INDEX = Path(__file__).resolve().parents[1].parent / 'index.html'

PLAIN = [
    ('<title>1095 W McKinley — White stucco front · home tour</title>',
     '<title>1095 W McKinley — Modern remodel · home tour</title>'),
    ('<span class="concept" id="modeBadge">CONCEPT · STYLED TOUR</span>',
     '<span class="concept" id="modeBadge">RENDERED · STYLED TOUR</span>'),
    ("mode==='photo'?'CONCEPT · STYLED TOUR'", "mode==='photo'?'RENDERED · STYLED TOUR'"),
    ("'Drag to look · AI concept view'", "'Drag to look · path-traced 360° render'"),
    ('<small>AI concept views · Drag to look', '<small>Path-traced 360° renders · Drag to look'),
    ('photorealistic concept viewpoints guided by the corrected model.',
     'path-traced 360° viewpoints, rendered from the same measured model as the 3D walk.'),
    ('<p>Explore 27 photorealistic 360° concept views with natural daylight, textured oak, soft fabrics and garden '
     'outlooks. Select Play tour to follow the connected route, or Browse scenes to jump to a room. The images are AI '
     'interpretations guided by the corrected model; use Dimensions and 3D Walk for geometry and measurements. '
     'Materials, furnishings, reflections and landscaping are illustrative.',
     '<p>Explore 27 path-traced 360° views of the modern design: late-morning daylight, white oak floors, walnut '
     'and Calacatta quartz, soft fabrics and garden outlooks. Select Play tour to follow the connected route, or '
     'Browse scenes to jump to a room. Every view is rendered from the measured model, and the 3D Walk, Dollhouse and '
     'Floor plan show the same model with its lighting baked in; use Dimensions for exact measurements. Furnishings, '
     'decor and landscaping are illustrative staging.'),
    ('The revised design features vaulted front bedrooms, a tall canted bay, a high entry window, an arched kitchen '
     'window, cream traditional cabinetry and oak-look porcelain in the shared bathroom.',
     'The revised design features vaulted front bedrooms, a tall canted bay, a high entry window, a black-framed '
     'kitchen window over walnut and quartz cabinetry, and a black fluted feature wall in the shared bathroom.'),
    ('<p>A warm-white stucco exterior, a warm wood entrance door and a solid gable above Bedroom 3’s bay. Explore '
     'the simpler front finish alongside your vaulted bedrooms and approved interior design.',
     '<p>Smooth warm-white stucco, a wood-clad entry, slim black windows and a charcoal standing-seam roof, with '
     'white oak, walnut and Calacatta quartz inside. Explore the modern finishes alongside your vaulted bedrooms '
     'and approved layout.'),
    ('id="designCaption">Updated concept view</span>', 'id="designCaption">Path-traced render</span>'),
    ("id==='front'?'Front elevation · concept':'Revised room · concept'",
     "id==='front'?'Front elevation · render':'Revised room · render'"),
    ("The concept images are illustrative.", "The renders show illustrative furnishings."),
    ("'-styled-360.'", "'-360.'"),
    ('White stucco front, solid bedroom gable and coordinated entry glazing',
     'Modern warm-white stucco front, solid bedroom gable and coordinated entry glazing'),
]

DESIGN = {
    'front': ('A modern warm-white front.',
              'Smooth warm-white stucco wraps the front walls, gables, bay base and corner returns, under a charcoal '
              'standing-seam roof with charcoal fascia. Slim matte-black frames hold large clear panes. Warm vertical '
              'wood cladding lines the recessed entry around the walnut front door, and a black aluminium garage door '
              'with frosted lites completes the front. Bedroom 3 keeps its tall bay window and a solid gable above it. '
              'The rectangular high window over the entrance, vaulted bedrooms and coordinated rooflines are retained. '
              'Roof forms are inferred from your aerial photo; dimensions remain proposed.'),
    'B3': ('A tall bay beneath a solid vaulted gable.',
           'Slim black frames with large clear panes replace the divided-light sashes, and a built-in window seat with '
           'an oak top and linen cushion fills the bay. The floor extends into the bay. The bed sits on the west wall '
           'to keep it open. Proposed bay: 8′ wall opening, 2′ projection, 1′ sill and 7′6″ window head. The main '
           'room rectangle retains its size; the bay adds a separately noted 12 sq ft. Above the bay is a continuous '
           'plaster gable. The vaulted bedroom ceiling remains 11′6″ at the ridge, lit by a ring pendant. The opening '
           'view takes in the bay and bed together. The bathroom and compact closet remain on the opposite wall, with '
           'the hall entrance at the side.'),
    'B4': ('The same vaulted roofline continues to Bedroom 4.',
           'A straight cathedral ridge and smooth white plaster slopes replace the flat ceiling. The room, separate '
           'reach-in closet and existing west-facing window keep their positions; the window gets a slim black frame. '
           'The proposed section rises from 8′ at the sides to 11′6″ at the ridge.'),
    'K0': ('Walnut, quartz and a wide black-framed window.',
           'The arched window becomes a flat-headed three-panel window in slim matte-black frames over the sink. '
           'Flat-slab walnut cabinetry with integrated finger-pull channels runs to the ceiling beside a white plaster '
           'hood. Calacatta-look quartz covers the worktops and the full-height backsplash and wraps the island as a '
           'waterfall. An integrated stainless fridge column, stacked wall ovens, an induction cooktop, a linear LED '
           'pendant and leather counter stools complete it. The island remains 6′ × 3′ and the 4′ × 3′ skylight is '
           'retained. Proposed window: 6′ wide, 3′1¾″ sill, 7′9″ head.'),
    'A1': ('A black fluted wall in the shared bath.',
           'A black fluted feature wall rises behind the toilet and tub end, with light large-format porcelain on the '
           'other walls. A floating walnut vanity with a white quartz top and vessel basin, a round LED-haloed mirror, '
           'a skirted one-piece toilet and a glass-screened alcove tub with matte-black fittings complete the room. '
           'The existing tub, vanity, toilet orientation and room footprint remain.'),
}

STYLING = {
    'palette': 'Warm white, white oak, walnut, Calacatta quartz, matte black, ochre and sage accents',
    'visualization': '27 path-traced 360-degree panoramas rendered in Blender Cycles from the measured model, plus a '
                     'lightmapped real-time model baked from the same scene. Use Dimensions for geometry; furnishings '
                     'and landscaping are illustrative staging.',
    'outdoor': 'Illustrative modern landscape: ipe deck, lawn, ornamental grasses and Mediterranean shrubs, charcoal '
               'slat fences; not a surveyed landscape design.',
}


def main():
    check = '--check' in sys.argv
    s = INDEX.read_text(encoding='utf-8')
    orig = s
    for old, new in PLAIN:
        if new in s and old not in s:
            continue
        n = s.count(old)
        if n == 0:
            print('not found:', old[:70])
            continue
        s = s.replace(old, new)
    m = re.search(r'const DESIGN_DATA=(\{.*?\});', s)
    data = json.loads(m.group(1))
    for k, (title, text) in DESIGN.items():
        data[k]['title'], data[k]['text'] = title, text
    if 'standing-seam' not in data['roof']['text']:
        data['roof']['text'] = data['roof']['text'].replace(
            'This is a concept roof model;', 'The roof is shown in charcoal standing-seam metal. This is a concept roof model;')
    s = s[:m.start(1)] + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + s[m.end(1):]
    m = re.search(r'"styling":(\{[^{}]*\})', s)
    st = json.loads(m.group(1))
    st.update(STYLING)
    s = s[:m.start(1)] + json.dumps(st, ensure_ascii=False, separators=(',', ':')) + s[m.end(1):]
    if check:
        print('changes pending' if s != orig else 'up to date')
        return
    if s != orig:
        INDEX.write_text(s, encoding='utf-8')
        print('updated', INDEX)
    else:
        print('up to date')


if __name__ == '__main__':
    main()
