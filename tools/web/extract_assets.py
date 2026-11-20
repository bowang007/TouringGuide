#!/usr/bin/env python3
"""Move the embedded (base64) assets of a LEGACY single-file tour page into assets/.

History: the tour used to be one HTML file with every image, panorama and model embedded. This tool
externalised them once (2026-11-17) and patched that page to load them by URL. Since v3 `index.html`
is a slim shell without data, so the tool never reads or writes it: the legacy page must be named
(--source FILE, or --from-head [--rev REV] for `git show REV:index.html`; the last embedded page is
commit ce0b1f9), and a patched copy of the legacy page is written only on request (--out FILE).

What it does
  * Decodes every embedded asset of the legacy page and writes it under <repo>/assets/:
      assets/panos/<ID>.webp           equirect panoramas (the old AI placeholders)       } only while
      assets/panos/manifest.json       old-format pano metadata {version, nodes: {ID:     } the manifest
                                       {offset, width, height, full, half, thumb, source}}} } is NOT in the
      assets/thumbs/<ID>.webp          scene-strip thumbnails                              } v3 format
      assets/plans/dimensioned-layout.png, layout-refinements.png
      assets/references/<slug>.webp    the user's own reference photos (DESIGN_REFERENCES)
      assets/design/<key>.webp|svg     design-modal hero images (DESIGN_VIEWS)
      assets/model/house-editable.glb  the "Download 3D model" file
  * Records the reference / design image URLs in tools/render/data/design.json (views[key].image,
    references) through tools/web/sitedata.py, where the page's runtime data comes from.
  * With --out FILE: writes the legacy page with its constants rewritten to relative URLs and the
    old inline-script patches for URL loading applied (never to <repo>/index.html).

Left to their owners in v3: assets/panos/manifest.json in the `levels` format, the panoramas and the
thumbnails (tools/web/publish_panos.py; a v3 manifest is never rewritten here and
--force-placeholders refuses to run against it), and assets/plans/dimension-plan.svg
(tools/web/dimension_plan.py; the legacy page's embedded drawing is no longer exported).

Idempotent: every write happens only when the bytes change, and each JS patch is skipped when
it is already applied. With an old-format manifest, panoramas/thumbnails marked as rendered
("source": "render") are never overwritten unless --force-placeholders is given.

Usage (system python3 is enough; it only needs Pillow for image sizes):
  python3 tools/web/extract_assets.py --source legacy.html --dry-run
  python3 tools/web/extract_assets.py --from-head --rev ce0b1f9
  python3 tools/web/extract_assets.py --source legacy.html --out legacy-urls.html
"""
import argparse
import base64
import hashlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # sizes are optional; the manifest then omits nothing but width/height
    Image = None

sys.dont_write_bytecode = True      # keep tools/web free of __pycache__
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sitedata  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ASSETS = 'assets'

# --------------------------------------------------------------------------------------------
# JS patches: (name, old, new). `new` already present -> skipped; else `old` must occur once.
# --------------------------------------------------------------------------------------------
PANO_BLOCK = r'''let PANO_MANIFEST=null;const panoReady=PANO_MANIFEST_FETCH.then(m=>{if(m){PANO_MANIFEST=m;for(const [id,e] of Object.entries(m.nodes)){if(e&&Number.isFinite(e.offset)&&(PHOTO_VIEWS[id]||e.offset))PHOTO_VIEWS[id]={...(PHOTO_VIEWS[id]||{}),offset:e.offset};}}return m;});const panoQuery=new URLSearchParams(location.search).get('pano');function panoResolve(path,fallback){const u=path?new URL(path,new URL(PANO_MANIFEST_URL,location.href)):new URL(fallback,location.href);if(PANO_MANIFEST&&PANO_MANIFEST.version)u.searchParams.set('v',PANO_MANIFEST.version);return u.href;}function panoUseHalf(e){if(!e||!e.half||e.half===e.full||panoQuery==='full')return false;if(panoQuery==='half'||panoQuery==='2k')return true;return (e.width||0)>panoMaxTexture||(navigator.deviceMemory||8)<=2||!!(navigator.connection&&navigator.connection.saveData);}function panoUrl(id,full=false){const e=PANO_MANIFEST&&PANO_MANIFEST.nodes[id];return panoResolve(e&&(!full&&panoUseHalf(e)?e.half:e.full),PANOS[id]);}function panoThumbUrl(id){const e=PANO_MANIFEST&&PANO_MANIFEST.nodes[id];return panoResolve(e&&e.thumb,PHOTO_THUMBS[id]);}const panoBlobs=new Map();function fetchPanoBlob(url){let p=panoBlobs.get(url);if(p){panoBlobs.delete(url);panoBlobs.set(url,p);return p;}p=fetch(url).then(r=>{if(!r.ok)throw Error('HTTP '+r.status+' '+url);return r.blob();});panoBlobs.set(url,p);p.catch(()=>{if(panoBlobs.get(url)===p)panoBlobs.delete(url);});while(panoBlobs.size>10)panoBlobs.delete(panoBlobs.keys().next().value);return p;}async function decodePano(blob){if(window.createImageBitmap){try{return await createImageBitmap(blob);}catch(e){}}const url=URL.createObjectURL(blob),img=new Image();img.decoding='async';img.src=url;try{await img.decode();}finally{setTimeout(()=>URL.revokeObjectURL(url),4000);}return img;}function isPow2(v){return v>0&&(v&(v-1))===0;}function createPanoTexture(src){let w=src.width,h=src.height,source=src;if(w>panoMaxTexture||h>panoMaxTexture){const s=Math.min(panoMaxTexture/w,panoMaxTexture/h);let nw=Math.max(1,Math.floor(w*s)),nh=Math.max(1,Math.floor(h*s));if(isPow2(w)&&isPow2(h)){nw=2**Math.floor(Math.log2(nw));nh=2**Math.floor(Math.log2(nh));}const c=document.createElement('canvas');c.width=nw;c.height=nh;const x=c.getContext('2d');x.imageSmoothingEnabled=true;x.imageSmoothingQuality='high';x.drawImage(src,0,0,nw,nh);source=c;w=nw;h=nh;}const mip=panoSeamless&&isPow2(w)&&isPow2(h),tex=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,source);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);if(mip){gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);if(panoAniso)gl.texParameterf(gl.TEXTURE_2D,panoAniso.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(8,gl.getParameter(panoAniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));}else{gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);}panoTexInfo.set(tex,{wrap:mip?1:0,mipmaps:mip,width:w,height:h,sourceWidth:src.width,sourceHeight:src.height});if(source!==src){source.width=source.height=0;}if(src.close)src.close();return tex;}let panoPreloadTimer=0;function preloadPanos(id){clearTimeout(panoPreloadTimer);if(navigator.connection&&navigator.connection.saveData)return;panoPreloadTimer=setTimeout(async()=>{const queue=[];if(photoGuidePlaying)queue.push(...photoGuideRoute.slice(photoGuideIndex+1,photoGuideIndex+3));queue.push(...(neighbors[id]||[]));for(const n of new Set(queue)){if(mode!=='photo'||currentNode!==id)return;if(n===id||!PANOS[n])continue;try{await fetchPanoBlob(panoUrl(n));}catch(e){}}},350);}'''

PATCHES = [
    ('manifest-fetch',
     r"""const $=id=>document.getElementById(id),canvas=$('view');""",
     r"""const $=id=>document.getElementById(id),canvas=$('view');const PANO_MANIFEST_URL='assets/panos/manifest.json',PANO_MANIFEST_FETCH=fetch(PANO_MANIFEST_URL,{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(m=>m&&m.nodes?m:null).catch(()=>null);"""),
    ('glb-download',
     r"""$('download').onclick=()=>downloadBlob(new Blob([Uint8Array.from(atob(GLB),x=>x.charCodeAt(0))],{type:'model/gltf-binary'}),'1095-mckinley-home.glb');""",
     r"""$('download').onclick=async()=>{try{const r=await fetch(GLB);if(!r.ok)throw Error('HTTP '+r.status);downloadBlob(new Blob([await r.arrayBuffer()],{type:'model/gltf-binary'}),'1095-mckinley-home.glb');}catch(e){toast('The 3D model could not be downloaded. Open the tour from its web address and try again.');}};"""),
    ('pano-shader-ext',
     r"""const panoProg=program('attribute vec2 p;varying vec2 uv;void main(){uv=p;gl_Position=vec4(p,0.,1.);}',`precision highp float;""",
     r"""const panoSeamless=!!gl.getExtension('OES_standard_derivatives'),panoAniso=gl.getExtension('EXT_texture_filter_anisotropic')||gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic'),panoMaxTexture=gl.getParameter(gl.MAX_TEXTURE_SIZE),panoTexInfo=new WeakMap();const panoProg=program('attribute vec2 p;varying vec2 uv;void main(){uv=p;gl_Position=vec4(p,0.,1.);}',(panoSeamless?'#extension GL_OES_standard_derivatives : enable\n#define SEAMLESS 1\n':'')+`precision highp float;"""),
    ('pano-shader-uniforms',
     r"""uniform float aspect,fade;const float PI=3.14159265359;vec2 sphereUV(vec3 v){""",
     r"""uniform float aspect,fade,imageWrap,oldWrap;const float PI=3.14159265359;vec2 sphereUV(vec3 v,float wrap){"""),
    ('pano-shader-seam',
     r"""return vec2(fract(atan(d.x,-d.z)/(2.*PI)+.5),.5-asin(clamp(d.y,-1.,1.))/PI);}void main(){gl_FragColor=mix(texture2D(oldImage,sphereUV(oldView)),texture2D(image,sphereUV(view)),fade);}""",
     r"""float s=atan(d.x,-d.z)/(2.*PI)+.5,a=fract(s);\n#ifdef SEAMLESS\nif(wrap>.5){float b=fract(s+.5)-.5;if(fwidth(a)>fwidth(b)+.25)a=b;}\n#endif\nreturn vec2(a,.5-asin(clamp(d.y,-1.,1.))/PI);}void main(){gl_FragColor=mix(texture2D(oldImage,sphereUV(oldView,oldWrap)),texture2D(image,sphereUV(view,imageWrap)),fade);}"""),
    ('pano-uniform-locations',
     r"""['image','oldImage','view','oldView','aspect','fade'].forEach(""",
     r"""['image','oldImage','view','oldView','aspect','fade','imageWrap','oldWrap'].forEach("""),
    ('pano-loader-block',
     r"""function photoPitch(id){return PHOTO_VIEWS[id]?.pitch??(id==='B4'?.10:id==='A1'?-.22:Math.max(nodePitch(nodeMap[id]),-.1));}""",
     r"""function photoPitch(id){return PHOTO_VIEWS[id]?.pitch??(id==='B4'?.10:id==='A1'?-.22:Math.max(nodePitch(nodeMap[id]),-.1));}""" + PANO_BLOCK),
    ('scene-thumbs',
     r"""img.src='data:image/webp;base64,'+PHOTO_THUMBS[id];img.alt='';img.width=128;img.height=72;img.decoding='async';""",
     r"""img.alt='';img.width=128;img.height=72;img.decoding='async';img.loading='lazy';panoReady.then(()=>{img.src=panoThumbUrl(id);});"""),
    ('open-pano-stale-texture',
     r"""mode='photo';activeMode();const token=++panoRequest,""",
     r"""mode='photo';activeMode();if(priorMode!=='photo'){if(oldPanoTexture){gl.deleteTexture(oldPanoTexture);oldPanoTexture=null;}if(panoTexture){gl.deleteTexture(panoTexture);panoTexture=null;}}const token=++panoRequest,"""),
    ('open-pano-upload',
     r"""const image=new Image();image.decoding='async';image.onload=()=>{if(token!==panoRequest||mode!=='photo')return;try{if(image.width>gl.getParameter(gl.MAX_TEXTURE_SIZE))throw Error('Panorama exceeds this device’s texture size.');const tex=gl.createTexture();gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,tex);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);if(oldPanoTexture)""",
     r"""const show=image=>{if(token!==panoRequest||mode!=='photo'){if(image.close)image.close();return;}try{const tex=createPanoTexture(image);if(oldPanoTexture)"""),
    ('open-pano-preload',
     r"""if(!document.querySelector('.modal.open'))canvas.focus({preventScroll:true});}catch(e){stopAuto();""",
     r"""if(!document.querySelector('.modal.open'))canvas.focus({preventScroll:true});preloadPanos(id);}catch(e){stopAuto();"""),
    ('open-pano-error',
     r"""toast(e.message);}};image.onerror=()=>{if(token!==panoRequest)return;photoLoading=false;updatePhotoControls();photoError='Embedded panorama could not load';""",
     r"""toast(e.message);}};const fail=err=>{if(token!==panoRequest)return;console.warn('Panorama '+id+' could not load',err);photoLoading=false;updatePhotoControls();photoError='Panorama could not load';"""),
    ('open-pano-fetch',
     r"""$('roomsButton').setAttribute('aria-expanded',String(innerWidth>640));};image.src='data:image/webp;base64,'+PANOS[id];return true;}""",
     r"""$('roomsButton').setAttribute('aria-expanded',String(innerWidth>640));toast(location.protocol==='file:'?'Open the tour from a web server (for example python3 -m http.server) to load the 360° views.':'This 360° view could not load, so you are in 3D Walk at the same spot.');};panoReady.then(()=>fetchPanoBlob(panoUrl(id))).then(blob=>token===panoRequest?decodePano(blob):null).then(image=>{if(image)show(image);},fail);return true;}"""),
    ('render-pano-wrap',
     r"""gl.uniform1i(panoUniforms.image,0);gl.uniform1i(panoUniforms.oldImage,1);""",
     r"""gl.uniform1i(panoUniforms.image,0);gl.uniform1i(panoUniforms.oldImage,1);gl.uniform1f(panoUniforms.imageWrap,panoTexInfo.get(panoTexture)?.wrap||0);gl.uniform1f(panoUniforms.oldWrap,panoTexInfo.get(oldPanoTexture||panoTexture)?.wrap||0);"""),
    ('context-lost-copy',
     r"""Reload this local file to continue the tour.""",
     r"""Reload the page to continue the tour."""),
    ('save-pano',
     r"""$('savePano').onclick=()=>{const id=(mode==='walk'||mode==='photo')?currentNode:'L0',data=PANOS[id];if(!data){toast('A styled panorama is not available at this location.');return;}downloadBlob(new Blob([Uint8Array.from(atob(data),x=>x.charCodeAt(0))],{type:'image/webp'}),'1095-mckinley-'+id+'-styled-360.webp');};""",
     r"""$('savePano').onclick=async()=>{const id=(mode==='walk'||mode==='photo')?currentNode:'L0';if(!PANOS[id]){toast('A styled panorama is not available at this location.');return;}try{await panoReady;const url=panoUrl(id,true),blob=await fetchPanoBlob(url),ext=(new URL(url).pathname.match(/\.(webp|jpe?g|png|avif)$/i)?.[1]||({'image/jpeg':'jpg','image/png':'png','image/avif':'avif'})[blob.type]||'webp').toLowerCase();downloadBlob(blob,'1095-mckinley-'+id+'-styled-360.'+ext);}catch(e){console.warn(e);toast('The 360° image could not be downloaded.');}};"""),
    ('draw-hold-frame',
     r"""gl.clearColor(.79,.88,.94,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);if(mode==='photo'){renderPanorama(time,w,h);""",
     r"""gl.clearColor(.79,.88,.94,1);if(mode!=='photo'||panoTexture||!photoLoading)gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);if(mode==='photo'){renderPanorama(time,w,h);"""),
    ('state-pano-info',
     r"""panoramaCount:Object.keys(PANOS).length,""",
     r"""panoramaCount:Object.keys(PANOS).length,panoramaVersion:PANO_MANIFEST?PANO_MANIFEST.version:null,panoramaTexture:panoTexture?panoTexInfo.get(panoTexture)||null:null,"""),
    ('refinements-lazy',
     r"""$('refinementsImage').src=REFINEMENTS_PNG;""",
     r"""$('refinementsImage').loading='lazy';$('refinementsImage').src=REFINEMENTS_PNG;"""),
    ('design-hero-fallback',
     r"""$('designHero').src=DESIGN_VIEWS[id]||('data:image/webp;base64,'+PANOS[id]);""",
     r"""$('designHero').src=DESIGN_VIEWS[id]||PHOTO_THUMBS[id]||'';"""),
]

PLAN_FILES = {'REVIEW_PNG': 'plans/dimensioned-layout.png', 'REFINEMENTS_PNG': 'plans/layout-refinements.png'}
EXT = {'image/webp': 'webp', 'image/png': 'png', 'image/svg+xml': 'svg', 'image/jpeg': 'jpg'}


def log(*a):
    print(*a, file=sys.stderr)


def slug(name):
    stem = re.sub(r'\.(png|jpe?g|webp)$', '', name, flags=re.I)
    return re.sub(r'[^a-z0-9]+', '-', stem.lower()).strip('-')


def find_value(text, name):
    """Return (start, end, value) of the JSON literal assigned to `name` (`const NAME=` or `,NAME=`)."""
    m = re.search(r'(?:\bconst |,)' + re.escape(name) + r'=', text)
    if not m:
        return None
    value, end = json.JSONDecoder().raw_decode(text, m.end())
    return m.end(), end, value


def data_uri(uri):
    m = re.match(r'data:([\w/+.-]+);base64,(.*)$', uri, re.S)
    if not m:
        return None, None
    return m.group(1), base64.b64decode(m.group(2))


def is_embedded(s):
    return isinstance(s, str) and (s.startswith('data:') or len(s) > 2000)


def image_size(data):
    if Image is None:
        return None
    try:
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:
        return None


class Writer:
    def __init__(self, root, dry):
        self.root, self.dry, self.changed, self.kept = root, dry, [], []

    def write(self, rel, data):
        p = self.root / rel
        if p.exists() and p.read_bytes() == data:
            self.kept.append(rel)
            return
        self.changed.append(rel)
        if not self.dry:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)

    def remove(self, rel):
        p = self.root / rel
        if p.exists():
            self.changed.append('-' + rel)
            if not self.dry:
                p.unlink()


def manifest_version(nodes, root):
    h = hashlib.sha1()
    for nid, e in nodes.items():
        h.update(json.dumps([nid, e], sort_keys=True).encode())
        for key in ('full', 'half', 'thumb'):
            f = (root / ASSETS / 'panos' / e[key]).resolve() if e.get(key) else None
            if f and f.exists():
                h.update(hashlib.sha1(f.read_bytes()).digest())
    return h.hexdigest()[:12]


def dump_manifest(nodes, root):
    return {
        'version': manifest_version(nodes, root),
        'convention': 'Equirectangular 2:1, top row = up (+y). Centre column = world yaw `offset` '
                      '(yaw 0 = SCENE -z, plan north); u increases clockwise seen from above. '
                      'Paths are relative to this file.',
        'nodes': nodes,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--repo', default=str(REPO))
    ap.add_argument('--source', help='legacy single-file HTML to read')
    ap.add_argument('--from-head', action='store_true', help='read `git show REV:index.html` (see --rev)')
    ap.add_argument('--rev', default='HEAD', help='revision for --from-head (default HEAD; the last page with '
                                                  'embedded assets is ce0b1f9)')
    ap.add_argument('--out', help='write the patched legacy page here (default: no page is written)')
    ap.add_argument('--force-placeholders', action='store_true',
                    help='overwrite rendered panos/thumbs with the embedded placeholders (old-format manifest only)')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    root = Path(a.repo).resolve()
    out = Path(a.out).resolve() if a.out else None
    if out is not None and out == root / 'index.html':
        ap.error('--out must not be index.html: the v3 page holds no data and is not patched by tools')
    if a.from_head:
        text = subprocess.run(['git', '-C', str(root), 'show', a.rev + ':index.html'], check=True,
                              capture_output=True).stdout.decode('utf-8')
        src_label = a.rev + ':index.html'
    elif a.source:
        text = Path(a.source).read_text(encoding='utf-8')
        src_label = str(a.source)
    else:
        ap.error('name the legacy page: --source FILE, or --from-head [--rev REV] '
                 '(index.html holds no data since v3)')
    size_before = len(text.encode('utf-8'))
    w = Writer(root, a.dry_run)
    replacements = []  # (start, end, new_literal)

    manifest_path = root / ASSETS / 'panos' / 'manifest.json'
    old_manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {'nodes': {}}
    old_nodes = old_manifest.get('nodes', {})
    # the v3 manifest ({widths, nodes: {ID: {levels: {...}}}}) belongs to publish_panos.py: hands off
    v3_manifest = 'widths' in old_manifest or any('levels' in e for e in old_nodes.values())
    if v3_manifest and a.force_placeholders:
        sys.exit(f'{manifest_path} is in the v3 `levels` format (tools/web/publish_panos.py); the embedded '
                 'placeholders cannot be restored into it')
    pv = find_value(text, 'PHOTO_VIEWS')
    photo_views = pv[2] if pv else {}

    # --- panoramas -------------------------------------------------------------------------
    panos = find_value(text, 'PANOS')
    if not panos:
        sys.exit('PANOS not found in ' + src_label + ' (not a legacy single-file page?)')
    ids = list(panos[2].keys())
    nodes = {}
    embedded_panos = any(is_embedded(v) for v in panos[2].values())
    for nid, b64 in ([] if v3_manifest else panos[2].items()):
        prev = old_nodes.get(nid)
        rendered = prev and prev.get('source') == 'render' and not a.force_placeholders
        if rendered:
            nodes[nid] = prev
            continue
        rel = f'panos/{nid}.webp'
        if embedded_panos:
            data = base64.b64decode(b64)
            if data[:4] != b'RIFF' or data[8:12] != b'WEBP':
                sys.exit(f'pano {nid}: not a WebP')
            w.write(f'{ASSETS}/{rel}', data)
        else:
            p = root / ASSETS / rel
            if not p.exists():
                sys.exit(f'{p} missing and the source has no embedded copy; rerun with --from-head')
            data = p.read_bytes()
        size = image_size(data)
        if not size and prev and prev.get('width'):
            size = (prev['width'], prev['height'])
        nodes[nid] = {
            'offset': photo_views.get(nid, {}).get('offset', 0),
            'width': size[0] if size else None, 'height': size[1] if size else None,
            'full': f'{nid}.webp', 'half': f'{nid}.webp', 'thumb': f'../thumbs/{nid}.webp',
            'source': 'placeholder',
        }
        if prev and prev.get('source') == 'render':  # reset: drop the render's 2k copy
            w.remove(f'{ASSETS}/panos/2k/{nid}.webp')
    replacements.append((panos[0], panos[1], json.dumps({i: f'{ASSETS}/panos/{i}.webp' for i in ids},
                                                         separators=(',', ':'))))

    # --- thumbnails ------------------------------------------------------------------------
    thumbs = find_value(text, 'PHOTO_THUMBS')
    if thumbs and any(is_embedded(v) for v in thumbs[2].values()):
        for nid, b64 in ([] if v3_manifest else thumbs[2].items()):
            if nodes.get(nid, {}).get('source') == 'render':
                continue
            w.write(f'{ASSETS}/thumbs/{nid}.webp', base64.b64decode(b64))
        replacements.append((thumbs[0], thumbs[1], json.dumps(
            {i: f'{ASSETS}/thumbs/{i}.webp' for i in thumbs[2]}, separators=(',', ':'))))

    # --- single blobs: GLB + plan PNGs -----------------------------------------------------
    glb = find_value(text, 'GLB')
    if glb and is_embedded(glb[2]):
        data = base64.b64decode(glb[2])
        if data[:4] != b'glTF':
            sys.exit('GLB constant is not a glTF binary')
        w.write(f'{ASSETS}/model/house-editable.glb', data)
        replacements.append((glb[0], glb[1], json.dumps(f'{ASSETS}/model/house-editable.glb')))
    for name, rel in PLAN_FILES.items():
        v = find_value(text, name)
        if v and is_embedded(v[2]):
            mime, data = data_uri(v[2])
            w.write(f'{ASSETS}/{rel}', data)
            replacements.append((v[0], v[1], json.dumps(f'{ASSETS}/{rel}')))

    # --- design references and hero views ---------------------------------------------------
    design_urls = {}
    for name, folder, keyfn in (('DESIGN_REFERENCES', 'references', slug), ('DESIGN_VIEWS', 'design', lambda k: k)):
        v = find_value(text, name)
        if not v or not any(is_embedded(x) for x in v[2].values()):
            continue
        urls = {}
        for key, uri in v[2].items():
            mime, data = data_uri(uri)
            rel = f'{folder}/{keyfn(key)}.{EXT[mime]}'
            w.write(f'{ASSETS}/{rel}', data)
            urls[key] = f'{ASSETS}/{rel}'
        design_urls[name] = urls
        replacements.append((v[0], v[1], json.dumps(urls, ensure_ascii=False, separators=(',', ':'))))

    # --- site data: the image URLs of the Design window live in design.json ---------------------
    design_note = 'no embedded design images in the source'
    if design_urls:
        dpath = sitedata.path('design', root)
        design = sitedata.read_json(dpath) if dpath.exists() else sitedata.parse_page(text).get('design')
        if design is None:
            design_note = 'design.json missing and the source has no DESIGN_DATA: URLs not recorded'
        else:
            before = sitedata.dumps(design, pretty=True)
            for key, url in design_urls.get('DESIGN_VIEWS', {}).items():
                if key in design['views']:
                    design['views'][key]['image'] = url
            for key, v in design['views'].items():            # a seeded file may still hold data: URIs
                if is_embedded(v.get('image')):
                    v.pop('image')
            refs = design.setdefault('references', {})
            refs.update(design_urls.get('DESIGN_REFERENCES', {}))
            for key in [k for k, v in refs.items() if is_embedded(v)]:
                refs.pop(key)
            changed = sitedata.dumps(design, pretty=True) != before or not dpath.exists()
            if changed and not a.dry_run:
                sitedata.save_design(design, root)
            design_note = f'{sitedata.rel(dpath, root)} {"updated" if changed else "unchanged"}'

    # --- the patched legacy page (only with --out) ---------------------------------------------
    applied, skipped, html_note = [], [], 'not written (no --out)'
    if out is not None:
        for start, end, lit in sorted(replacements, reverse=True):      # back to front: offsets stay valid
            text = text[:start] + lit + text[end:]
        for name, old, new in PATCHES:
            if new in text:
                skipped.append(name)
                continue
            n = text.count(old)
            if n != 1:
                sys.exit(f'patch {name}: expected 1 match of the original code, found {n}')
            text = text.replace(old, new)
            applied.append(name)
        leftover = [m.group(0)[:40] for m in re.finditer(r'data:[\w/+.-]+;base64,[A-Za-z0-9+/=]{4096,}', text)]
        if leftover:
            sys.exit(f'large data URIs remain: {leftover}')
        data = text.encode('utf-8')
        html_changed = not out.exists() or out.read_bytes() != data
        if html_changed and not a.dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, encoding='utf-8')
        html_note = (f'{out} ({len(data) / 1e6:.2f} MB, {"updated" if html_changed else "unchanged"}'
                     f'{", dry run" if a.dry_run else ""})')

    # --- manifest (old format only) ----------------------------------------------------------
    if v3_manifest:
        manifest_note = (f'{old_manifest.get("version")} kept: v3 `levels` manifest, panoramas and thumbnails '
                         'belong to tools/web/publish_panos.py')
    else:
        half_dir = root / ASSETS / 'panos' / '2k'
        if not a.dry_run and half_dir.is_dir() and not any(half_dir.iterdir()):
            half_dir.rmdir()
        # The version hashes the pano/thumb files on disk, which were written above.
        manifest = dump_manifest({i: nodes[i] for i in ids}, root)
        w.write(f'{ASSETS}/panos/manifest.json', (json.dumps(manifest, indent=1, ensure_ascii=False) + '\n').encode())
        manifest_note = (f'{manifest["version"]} '
                         f'({sum(1 for e in nodes.values() if e["source"] == "render")} rendered, '
                         f'{sum(1 for e in nodes.values() if e["source"] != "render")} placeholder)')

    log(f'source            {src_label} ({size_before / 1e6:.2f} MB)')
    log(f'patched page      {html_note}')
    log(f'patches applied   {len(applied)}: {", ".join(applied) or "-"}')
    log(f'patches present   {len(skipped)}')
    log(f'assets written    {len(w.changed)}' + (': ' + ', '.join(w.changed[:12]) + (' …' if len(w.changed) > 12 else '') if w.changed else '')
        + (' (dry run)' if a.dry_run else ''))
    log(f'assets unchanged  {len(w.kept)}')
    log(f'design data       {design_note}')
    log(f'manifest version  {manifest_note}')


if __name__ == '__main__':
    main()
