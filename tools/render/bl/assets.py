"""Download-and-cache helper for CC0 assets from Poly Haven (https://polyhaven.com, CC0 1.0).

Pure Python (urllib) so it works both inside Blender and from system Python.
Files land in CACHE_DIR/polyhaven/<kind>/<asset_id>/... and each asset gets an info.json
sidecar; `write_manifest()` collects them into tools/render/ASSETS.md for attribution.

    from bl import assets
    gltf = assets.model('modern_arm_chair_01', res='2k')          # path to .gltf
    maps = assets.texture('wool_boucle', res='2k')                 # {'diff': path, 'nor_gl': ..., 'rough': ...}
    hdr  = assets.hdri('kloofendal_48d_partly_cloudy_puresky', res='4k')
"""
import json
import os
import time
import urllib.request

try:
    from .common import CACHE_DIR, RENDER_DIR
except ImportError:  # system python
    RENDER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CACHE_DIR = os.environ.get('TG_CACHE', os.path.join(RENDER_DIR, '.cache'))

API = 'https://api.polyhaven.com'
UA = {'User-Agent': 'TouringGuide-render-pipeline/1.0'}
ROOT = os.path.join(CACHE_DIR, 'polyhaven')


def _get(url, dest=None, tries=4):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if dest:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                tmp = dest + '.part'
                with open(tmp, 'wb') as f:
                    f.write(data)
                os.replace(tmp, dest)
            return data
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(1.5 * (k + 1))


def files(asset_id):
    return json.loads(_get(f'{API}/files/{asset_id}'))


def info(asset_id):
    return json.loads(_get(f'{API}/info/{asset_id}'))


def _sidecar(kind, asset_id, extra):
    d = os.path.join(ROOT, kind, asset_id)
    p = os.path.join(d, 'info.json')
    if not os.path.exists(p):
        try:
            meta = info(asset_id)
        except Exception:
            meta = {}
        meta = {'id': asset_id, 'kind': kind, 'name': meta.get('name', asset_id),
                'authors': list((meta.get('authors') or {}).keys()), 'license': 'CC0 1.0',
                'url': f'https://polyhaven.com/a/{asset_id}', **extra}
        os.makedirs(d, exist_ok=True)
        with open(p, 'w') as f:
            json.dump(meta, f, indent=1)


def model(asset_id, res='2k', fmt='gltf'):
    """Download a model (glTF + textures, or .blend) and return the main file path."""
    d = os.path.join(ROOT, 'models', asset_id, res)
    f = files(asset_id) if not os.path.isdir(d) else None
    if f is not None:
        entry = f[fmt][res][fmt]
        main = os.path.join(d, os.path.basename(entry['url']))
        _get(entry['url'], main)
        for rel, inc in (entry.get('include') or {}).items():
            _get(inc['url'], os.path.join(d, rel))
        _sidecar('models', asset_id, {'res': res, 'format': fmt})
    for name in os.listdir(d):
        if name.endswith('.' + ('gltf' if fmt == 'gltf' else fmt)):
            return os.path.join(d, name)
    raise FileNotFoundError(d)


TEX_MAPS = ('Diffuse', 'nor_gl', 'Rough', 'AO', 'Displacement', 'arm', 'Metal', 'Translucent')


def texture(asset_id, res='2k', ext='jpg', maps=TEX_MAPS):
    """Download PBR maps of a texture; returns {map_key_lowercase: path}."""
    d = os.path.join(ROOT, 'textures', asset_id, res)
    index = os.path.join(d, f'maps_{ext}.json')
    if os.path.exists(index):
        out = json.load(open(index))
        if all(os.path.exists(p) for p in out.values()):
            return {k: v for k, v in out.items() if k in {m.lower() for m in maps}}
    out = {}
    f = files(asset_id)
    for m in TEX_MAPS:
        if m not in f or res not in f[m]:
            continue
        e = f[m][res].get(ext) or f[m][res].get('png') or next(iter(f[m][res].values()))
        p = os.path.join(d, os.path.basename(e['url']))
        _get(e['url'], p)
        out[m.lower()] = p
    os.makedirs(d, exist_ok=True)
    with open(index, 'w') as fh:
        json.dump(out, fh, indent=1)
    _sidecar('textures', asset_id, {'res': res})
    return {k: v for k, v in out.items() if k in {m.lower() for m in maps}}


def hdri(asset_id, res='4k', ext='exr'):
    d = os.path.join(ROOT, 'hdris', asset_id)
    if os.path.isdir(d):
        for name in os.listdir(d):
            if name.endswith(('.exr', '.hdr')) and f'_{res}' in name:
                return os.path.join(d, name)
    f = files(asset_id)
    e = f['hdri'][res].get(ext) or f['hdri'][res]['hdr']
    p = os.path.join(d, os.path.basename(e['url']))
    _get(e['url'], p)
    _sidecar('hdris', asset_id, {'res': res})
    return p


def write_manifest(path=None):
    """Collect every downloaded asset into a Markdown attribution list."""
    path = path or os.path.join(RENDER_DIR, 'ASSETS.md')
    rows = []
    for kind in ('textures', 'models', 'hdris'):
        base = os.path.join(ROOT, kind)
        if not os.path.isdir(base):
            continue
        for a in sorted(os.listdir(base)):
            p = os.path.join(base, a, 'info.json')
            if os.path.exists(p):
                m = json.load(open(p))
                rows.append(f"| {kind[:-1]} | [{m['name']}]({m['url']}) | {', '.join(m.get('authors') or []) or '-'} | {m['license']} |")
    with open(path, 'w') as f:
        f.write('# Third-party assets used by the render pipeline\n\n'
                'All assets are from [Poly Haven](https://polyhaven.com) under CC0 1.0 (public domain). '
                'They are downloaded on demand into `tools/render/.cache/` and are not committed.\n\n'
                '| Type | Asset | Authors | License |\n|---|---|---|---|\n' + '\n'.join(rows) + '\n')
    return path
