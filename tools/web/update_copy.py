#!/usr/bin/env python3
"""One-off copy update for the modern, path-traced version of the tour (historical; idempotent).

On 2026-11-17 this script replaced the text that described the earlier AI concept images and the
traditional styling by text matching the path-traced renders of the modern design. Geometry facts
(sizes, sills, heads, ridge heights) were kept verbatim.

Since v3 it edits the site data files through tools/web/sitedata.py and never index.html:
  * tools/render/data/design.json   `title` and `text` of the design views listed in DESIGN, and the
                                    roof text's standing-seam sentence
  * tools/render/data/scene.json    `styling` (palette, visualization, outdoor)
then run tools/web/build_site_data.py to refresh assets/data/. The page chrome it also patched in the
single-file page (title, badges, hints, the Info / Welcome / Design windows: the old PLAIN list, see
git history) is ordinary markup in index.html and module code in assets/js/tour/ now and is edited there.

CAUTION: the texts below are those of the FIRST modern restyle. The owner's second and third rounds
rewrote most of them (design.json holds the current copy), and apply_relayout.py resets `styling`
from the concept data on every run. Today the script therefore reports pending changes, and applying
them would put the older copy back. So it only reports unless --force is given.

  python3 tools/web/update_copy.py            # report what would change; write nothing (exit 0)
  python3 tools/web/update_copy.py --check    # the same, one line
  python3 tools/web/update_copy.py --force    # write the texts below into design.json and scene.json
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

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
    check, force = '--check' in sys.argv, '--force' in sys.argv
    design = sitedata.load_design()
    scene = sitedata.load_scene()
    pending = []
    views = design['views']
    for k, (title, text) in DESIGN.items():
        if k not in views:
            print('design view not found:', k)
            continue
        for field, value in (('title', title), ('text', text)):
            if views[k].get(field) != value:
                pending.append('design.json views.%s.%s' % (k, field))
                views[k][field] = value
    roof = views.get('roof')
    if roof and 'standing-seam' not in roof['text'] and 'This is a concept roof model;' in roof['text']:
        roof['text'] = roof['text'].replace(
            'This is a concept roof model;', 'The roof is shown in charcoal standing-seam metal. This is a concept roof model;')
        pending.append('design.json views.roof.text')
    st = scene.setdefault('styling', {})
    for k, v in STYLING.items():
        if st.get(k) != v:
            pending.append('scene.json styling.%s' % k)
            st[k] = v
    if check:
        print('changes pending' if pending else 'up to date')
        return
    if not pending:
        print('up to date')
        return
    if not force:
        print('would change %d fields (nothing written; these texts predate the current copy, see the docstring; '
              '--force writes them):' % len(pending))
        for line in pending:
            print('  ' + line)
        return
    for name, changed in (('design', sitedata.save_design(design)), ('scene', sitedata.save_scene(scene))):
        print('updated' if changed else 'unchanged', sitedata.rel(sitedata.path(name)))


if __name__ == '__main__':
    main()
