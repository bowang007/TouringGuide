#!/usr/bin/env python3
"""Site data of the tour: the canonical files and the helpers every tool uses to read and write them.

Since v3 `index.html` holds no data. The pipeline's working files (source of truth, edited by the tools) are

  tools/render/data/scene.json          'scene'         the FULL scene, exactly what `const SCENE=` held in the old
                                                        page: objects, rooms, tour {nodes, edges, start}, height,
                                                        extent, audit, notes, lights, styling, layout_revision,
                                                        design_revision
  tools/render/data/measurements.json   'measurements'  dimension schedule: rooms, windows, doors, source, precision,
                                                        basis_legend (the old `const MEASUREMENTS=`)
  tools/render/data/design.json         'design'        Design window: {order, views, references} (see below)
  tools/render/data/primitives.json     'primitives'    unit primitives box / cylinder / sphere / rounded (the old
                                                        `PRIMITIVES=`); static, read by bl/common.py for the build
  tools/render/data/scene_classification.json  'classification'  per-object classification on the architect's plan
  assets/plans/dimension-plan.svg       'plan'          Dimensions sheet drawing; the page fetches it

and the page's runtime files, generated from the files above by tools/web/build_site_data.py:

  assets/data/tour.json, assets/data/measurements.json, assets/data/design.json

design.json merges the old page's DESIGN_DATA, DESIGN_VIEWS, DESIGN_REFERENCES and the Design tabs:
  {"order": ["front", "roof", "B3", ...],                       tab order
   "views": {"front": {"label": "Front addition",               tab label
                       "title": ..., "text": ..., "refs": ["front.PNG", ...], "node": "E0", "opening": "W17",
                       "image": "assets/design/front.webp"}, ...},
   "references": {"front.PNG": "assets/references/front.webp", ...}}

Pipeline order (seconds, standard library only):
  python3 tools/render/apply_relayout.py        concept plan -> scene.json, measurements.json, classification
  python3 tools/render/apply_revisions_web.py   owner's changes -> scene.json, measurements.json
  python3 tools/render/extract_scene.py         consistency check of the files (writes nothing)
  python3 tools/web/dimension_plan.py           scene + measurements -> assets/plans/dimension-plan.svg
  python3 tools/web/build_site_data.py          -> assets/data/*.json

Use from a tool:
    sys.dont_write_bytecode = True              # keep tools/web free of __pycache__
    sys.path.insert(0, <repo>/tools/web)
    import sitedata
    scene = sitedata.load_scene(); ...; sitedata.save_scene(scene)

Saving is atomic (temp file + rename) and happens only when the bytes change, so re-running a tool on unchanged
data touches nothing. The scene / measurements / primitives / classification files keep the compact ASCII form
they always had (no diff noise); design.json is indented because people edit it.

Another root: every function takes `root=` and the default root is $SITEDATA_ROOT when set (a directory with
the same layout as the repository). That is how the conversion is tested without touching the working files.

Legacy single-file pages (the page before v3 embedded all of this as JS constants):
    python3 tools/web/sitedata.py                     # status: files, sizes, counts
    python3 tools/web/sitedata.py --seed PAGE         # write the files that do not exist yet from PAGE
    python3 tools/web/sitedata.py --seed PAGE --force # ... and overwrite the existing ones
    python3 tools/web/sitedata.py --compare PAGE      # deep-compare the files with PAGE's data (exit 1 if not equal)
PAGE is a file, or `git:REV` for `git show REV:index.html`; the last commit with the single-file page is
ed664e0, so `--seed git:ed664e0` recreates a lost file and `--compare git:ed664e0` checks the conversion.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

FILES = {
    'scene': 'tools/render/data/scene.json',
    'measurements': 'tools/render/data/measurements.json',
    'design': 'tools/render/data/design.json',
    'primitives': 'tools/render/data/primitives.json',
    'classification': 'tools/render/data/scene_classification.json',
    'plan': 'assets/plans/dimension-plan.svg',
    # runtime files of the page (tools/web/build_site_data.py)
    'site_tour': 'assets/data/tour.json',
    'site_measurements': 'assets/data/measurements.json',
    'site_design': 'assets/data/design.json',
    'index': 'index.html',
}
PRETTY = {'design'}                       # hand-edited: indented UTF-8; the others stay compact ASCII
SVG_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
PLAN_OPEN = '<div id="dimensionPlan">'
DESIGN_FIELDS = ('title', 'text', 'refs', 'node', 'opening')


# ------------------------------------------------------------------------------------------- paths
def site_root(root=None):
    """The directory that holds index.html, assets/ and tools/: `root`, else $SITEDATA_ROOT, else the repo."""
    return Path(root or os.environ.get('SITEDATA_ROOT') or REPO).resolve()


def path(name, root=None):
    return site_root(root) / FILES[name]


def rel(p, root=None):
    try:
        return Path(p).resolve().relative_to(site_root(root)).as_posix()
    except ValueError:
        return str(p)


# ------------------------------------------------------------------------------------------- files
def write_bytes(p, data):
    """Atomic write, skipped when the file already holds `data`. Returns True when the file changed."""
    p = Path(p)
    if p.exists() and p.read_bytes() == data:
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.tmp%d' % os.getpid())
    tmp.write_bytes(data)
    os.replace(tmp, p)
    return True


def write_text(p, text):
    return write_bytes(p, text.encode('utf-8'))


def dumps(obj, pretty=False):
    if pretty:
        return json.dumps(obj, indent=1, ensure_ascii=False) + '\n'
    return json.dumps(obj, separators=(',', ':'))


def read_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def write_json(p, obj, pretty=False):
    return write_text(p, dumps(obj, pretty))


def load(name, root=None):
    p = path(name, root)
    if not p.exists():
        raise SystemExit('%s is missing. Recreate it from the last single-file page with\n'
                         '  python3 tools/web/sitedata.py --seed git:ed664e0' % p)
    return read_json(p)


def save(name, obj, root=None):
    """Write one of the JSON files; returns True when it changed."""
    return write_json(path(name, root), obj, pretty=name in PRETTY)


def load_scene(root=None):
    return load('scene', root)


def save_scene(scene, root=None):
    return save('scene', scene, root)


def load_measurements(root=None):
    return load('measurements', root)


def save_measurements(meas, root=None):
    return save('measurements', meas, root)


def load_design(root=None):
    return load('design', root)


def save_design(design, root=None):
    return save('design', design, root)


def load_primitives(root=None):
    return load('primitives', root)


def load_classification(root=None):
    return load('classification', root)


def save_classification(cls, root=None):
    return save('classification', cls, root)


def plan_svg_file(svg):
    """The file form of the plan drawing: XML declaration + the bare <svg>...</svg> + newline."""
    return SVG_HEAD + svg + '\n'


def bare_svg(text):
    """The <svg>...</svg> element of an SVG file's text (drops the XML declaration and the final newline)."""
    i = text.find('<svg')
    j = text.rfind('</svg>')
    if i < 0 or j < 0:
        raise ValueError('no <svg> element')
    return text[i:j + len('</svg>')]


def load_plan_svg(root=None):
    p = path('plan', root)
    if not p.exists():
        raise SystemExit('%s is missing; run python3 tools/web/dimension_plan.py' % p)
    return bare_svg(p.read_text(encoding='utf-8'))


def save_plan_svg(svg, root=None, out=None):
    return write_text(out or path('plan', root), plan_svg_file(svg))


# ------------------------------------------------------------------------------------------- design
def design_from_legacy(data, views, references, tabs=None):
    """DESIGN_DATA + DESIGN_VIEWS + DESIGN_REFERENCES (+ the tab buttons [(key, label)]) -> design.json."""
    labels = dict(tabs or [])
    out = {'order': [k for k, _ in (tabs or []) if k in data] + [k for k in data if k not in labels],
           'views': {}, 'references': dict(references or {})}
    for key, d in data.items():
        v = {'label': labels.get(key, key)}
        v.update({k: d[k] for k in DESIGN_FIELDS if k in d})
        v.update({k: d[k] for k in d if k not in v})
        if views.get(key):
            v['image'] = views[key]
        out['views'][key] = v
    return out


def design_legacy(design):
    """design.json -> (DESIGN_DATA, DESIGN_VIEWS, DESIGN_REFERENCES) as the old page held them."""
    data = {k: {f: v[f] for f in v if f not in ('label', 'image')} for k, v in design['views'].items()}
    views = {k: v['image'] for k, v in design['views'].items() if v.get('image')}
    return data, views, dict(design.get('references', {}))


# ------------------------------------------------------------------------------------------- legacy page
def grab(src, marker, start=0):
    """The JSON literal that follows `marker` in a legacy page: (value, literal start, literal end)."""
    i = src.find(marker, start)
    if i < 0:
        raise SystemExit('%r not found' % marker)
    obj, end = json.JSONDecoder().raw_decode(src, i + len(marker))
    return obj, i + len(marker), end


def read_page(page, root=None):
    """Text of a legacy single-file page: a path, or 'git:REV' for `git show REV:index.html`."""
    if str(page).startswith('git:'):
        out = subprocess.run(['git', '-C', str(site_root(root)), 'show', str(page)[4:] + ':index.html'],
                             check=True, capture_output=True).stdout
        return out.decode('utf-8')
    return Path(page).read_text(encoding='utf-8')


def parse_page(text):
    """Everything a legacy page embedded: {'scene', 'primitives', 'measurements', 'design', 'plan'}.
    Parts the page does not have are left out."""
    out = {}
    for name, marker in (('scene', 'const SCENE='), ('primitives', 'PRIMITIVES='),
                         ('measurements', 'const MEASUREMENTS=')):
        if marker in text:
            out[name] = grab(text, marker)[0]
    if 'const DESIGN_DATA=' in text:
        data = grab(text, 'const DESIGN_DATA=')[0]
        views = grab(text, 'const DESIGN_VIEWS=')[0] if 'const DESIGN_VIEWS=' in text else {}
        refs = grab(text, 'const DESIGN_REFERENCES=')[0] if 'const DESIGN_REFERENCES=' in text else {}
        tabs = re.findall(r'<button data-design="([^"]+)"[^>]*>([^<]*)</button>', text)
        out['design'] = design_from_legacy(data, views, refs, tabs)
    i = text.find(PLAN_OPEN)
    if i >= 0 and text.startswith('<svg', i + len(PLAN_OPEN)):
        i += len(PLAN_OPEN)
        out['plan'] = text[i:text.index('</svg>', i) + len('</svg>')]
    return out


def seed(page, root=None, force=False):
    """Write the data files from a legacy page; without `force` only the files that do not exist yet.
    Returns the names written."""
    parts = parse_page(read_page(page, root))
    done = []
    for name in ('scene', 'measurements', 'primitives', 'design', 'plan'):
        if name not in parts or (path(name, root).exists() and not force):
            continue
        changed = save_plan_svg(parts[name], root) if name == 'plan' else save(name, parts[name], root)
        if changed:
            done.append(name)
    return done


# ------------------------------------------------------------------------------------------- comparison
def diff(a, b, tol=1e-9, where='', out=None, limit=20):
    """Deep comparison with a float tolerance; returns up to `limit` differences as text."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    num = (int, float)
    if isinstance(a, bool) or isinstance(b, bool):
        if a is not b:
            out.append('%s: %r != %r' % (where, a, b))
    elif isinstance(a, num) and isinstance(b, num):
        if abs(a - b) > tol * max(1.0, abs(a), abs(b)):
            out.append('%s: %r != %r' % (where, a, b))
    elif isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():
            if k not in a or k not in b:
                out.append('%s.%s: only in %s' % (where, k, 'files' if k in a else 'page'))
            else:
                diff(a[k], b[k], tol, '%s.%s' % (where, k), out, limit)
        if list(a) != list(b) and not out:
            out.append('%s: key order differs' % where)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append('%s: length %d != %d' % (where, len(a), len(b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diff(x, y, tol, '%s[%d]' % (where, i), out, limit)
    elif a != b:
        out.append('%s: %r != %r' % (where, str(a)[:80], str(b)[:80]))
    return out


def compare(page, root=None, tol=1e-9):
    """Compare the data files with what a legacy page embedded. Returns [(name, equal, detail)]."""
    parts = parse_page(read_page(page, root))
    rows = []
    for name in ('scene', 'measurements', 'primitives', 'design'):
        if name not in parts:
            rows.append((name, None, 'not in the page'))
            continue
        if not path(name, root).exists():
            rows.append((name, False, 'file missing'))
            continue
        mine = load(name, root)
        d = diff(mine, parts[name], tol, name)
        exact = mine == parts[name]
        rows.append((name, not d, 'identical values' if exact else 'equal within %g' % tol if not d else '; '.join(d)))
        if name == 'design' and not d:
            legacy = design_legacy(mine)
            page_text = read_page(page, root)
            want = tuple(grab(page_text, 'const %s=' % k)[0]
                         for k in ('DESIGN_DATA', 'DESIGN_VIEWS', 'DESIGN_REFERENCES'))
            rows.append(('design -> DESIGN_DATA / DESIGN_VIEWS / DESIGN_REFERENCES', legacy == want,
                         'identical values' if legacy == want else 'reconstruction differs'))
    if 'plan' in parts:
        p = path('plan', root)
        if not p.exists():
            rows.append(('plan', False, 'file missing'))
        else:
            raw = p.read_text(encoding='utf-8')
            same = bare_svg(raw) == parts['plan']
            rows.append(('plan', same, ('byte-identical <svg> (%d bytes); the file adds the XML declaration and a '
                                        'final newline' % len(parts['plan'].encode('utf-8'))) if same else
                         'SVG differs (%d vs %d bytes)' % (len(bare_svg(raw)), len(parts['plan']))))
    return rows


def status(root=None):
    lines = ['site data under %s' % site_root(root)]
    for name in FILES:
        if name == 'index':
            continue
        p = path(name, root)
        if not p.exists():
            lines.append('  %-18s %-48s missing' % (name, FILES[name]))
            continue
        note = ''
        if p.suffix == '.json':
            obj = read_json(p)
            if name == 'scene':
                note = '%d objects, %d tour nodes, %d edges' % (len(obj['objects']), len(obj['tour']['nodes']),
                                                                 len(obj['tour']['edges']))
            elif name in ('measurements', 'site_measurements'):
                note = '%d rooms, %d windows, %d doors' % (len(obj['rooms']), len(obj['windows']), len(obj['doors']))
            elif name in ('design', 'site_design'):
                note = '%d views: %s' % (len(obj['views']), ' '.join(obj['order']))
            elif name == 'site_tour':
                note = 'version %s, %d sweeps, %d footprint rects, %d rooms' % (
                    obj.get('version'), len(obj['sweeps']), len(obj['footprint']), len(obj['rooms']))
            elif name == 'classification':
                note = '%d objects' % len(obj['objects'])
            elif name == 'primitives':
                note = ' '.join(obj)
        lines.append('  %-18s %-48s %9d bytes  %s' % (name, FILES[name], p.stat().st_size, note))
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description='Site data files of the tour (see the module docstring).')
    ap.add_argument('--root', help='another root with the repository layout (default: $SITEDATA_ROOT or the repo)')
    ap.add_argument('--seed', metavar='PAGE', help='write the missing data files from a legacy single-file page '
                                                   '(a path, or git:REV)')
    ap.add_argument('--force', action='store_true', help='with --seed: overwrite existing files too')
    ap.add_argument('--compare', metavar='PAGE', help='deep-compare the files with a legacy page (exit 1 if not equal)')
    ap.add_argument('--tol', type=float, default=1e-9, help='relative float tolerance of --compare')
    a = ap.parse_args()
    if a.seed:
        done = seed(a.seed, a.root, a.force)
        print('seeded from %s: %s' % (a.seed, ', '.join(done) or 'nothing (all files exist; --force overwrites)'))
    if a.compare:
        rows = compare(a.compare, a.root, a.tol)
        for name, ok, detail in rows:
            print('%-8s %s: %s' % ('EQUAL' if ok else 'n/a' if ok is None else 'DIFFERENT', name, detail))
        if any(ok is False for _, ok, _ in rows):
            return 1
    if not a.seed and not a.compare:
        print(status(a.root))
    return 0


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    sys.exit(main())
