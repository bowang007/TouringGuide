"""Path-trace 360-degree equirectangular panoramas (and optional rectilinear previews) at the
tour's camera stops, matching the web app's panorama convention exactly.

Convention (verified): image centre column (u=0.5) faces SCENE -z (north / yaw 0), u increases
clockwise seen from above (u=0.75 faces +x/east), top row = up. Camera = SCENE node.p.
In Blender: equirect camera at ft2bl(node.p) with rotation (90deg, 0, 0).

Usage:
  blender -b tools/render/.cache/house.blend --python tools/render/render_panos.py -- \
      --nodes all|L0,K0 --width 8192 --samples 192 --out tools/render/.cache/panos \
      [--pins pins.json] [--skip-existing] [--png16] [--preview] [--preview-only | --probe-only] \
      [--exposure auto|<stops>] [--wb auto|<kelvin>[,<tint>]] [--fov 90] \
      [--adaptive-threshold 0.008] [--adaptive-min 64] [--no-adaptive] [--tile-size 2048]

Two-pass production run (tools/render/final_run.sh):
  1. probe pass   --preview-only (or --probe-only) into its own directory: per stop the white mask and the
                  low-sample probe only; render_meta.json gets the automatic exposure / white balance;
  2. smooth_exposure.py relaxes those values along the tour graph and writes a pins file;
  3. final pass   --pins pins.json --skip-existing: the pinned values win over the automatic ones, over
                  WB_NODE and over --exposure / --wb. --skip-existing makes a restart continue where it stopped.

Output: <out>/<ID>.png, 8-bit RGB (16-bit RGB with --png16; nothing downstream needs it: the publisher
converts to 8-bit RGB, bake_web.py and adapt_web.py read render_meta.json only). The image is rendered to
<out>/_part_<ID>.png and renamed when complete, so an existing <ID>.png is always a finished render.

render_meta.json, one entry per stop (read by smooth_exposure.py, bake_web.py, adapt_web.py):
  exposure (stops), wb [kelvin, tint]   the values the image was rendered with
  auto {exposure, wb | null}            what the probe chose (wb null: not enough white paint in view)
  wb_source                             'pin' | 'fixed' (--wb) | 'node' (WB_NODE) | 'probe' | 'default'
  pinned                                true when --pins supplied exposure and/or white balance
  probe {median, white_px, white_rgb}   probe measurements (adapt_web.py uses white_rgb)
  image                                 false for a probe / preview-only pass
  seconds, probe_s, render_s, width, samples, bits, adaptive [on, threshold, min samples]
  blend [file, mtime]                   the scene file the stop was rendered from (--skip-existing redoes a
                                        stop whose scene was rebuilt since)
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from bl.common import CACHE_DIR, DATA_DIR, ft2bl  # noqa: E402

TARGET_MEDIAN = 0.22       # scene-linear median luminance the exposure maps to (bright real-estate look)
# White balance. 'auto' (default) balances every stop like a listing photographer: the white painted
# surfaces seen in the low-sample exposure probe (walls, ceilings, trim, white doors, stucco) are
# brought to WB_TARGET, a slightly warm white, in the final display image. Stops without enough
# white surface fall back to WB_DEFAULT. A fixed balance is '--wb <kelvin>[,<tint>]'.
WB_DEFAULT = (6500.0, 10.0)        # (temperature K, tint)
WB_KELVIN = WB_DEFAULT[0]          # kept for older callers
WB_TARGET = (1.06, 0.88)           # display R/G and B/G of white paint after balancing
WB_LIMITS = ((3500.0, 14000.0), (-30.0, 35.0))
# Stops whose only white paint is lit by the room's own warm materials: the auto balance would cancel the room's
# colour, so they get a fixed balance (the shared bath's wood-look wall and Spanish-cream stone tint its ceiling).
WB_NODE = {'A1': (5000.0, 0.0)}
WB_MATERIALS = ('M_paint_wall', 'M_paint_ceiling', 'M_paint_trim', 'M_plaster_white', 'M_door_slab', 'M_stucco')
WB_PASS_INDEX = 7


def parse():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--nodes', default='all')
    ap.add_argument('--width', type=int, default=4096)
    ap.add_argument('--samples', type=int, default=768)
    ap.add_argument('--out', default=os.path.join(CACHE_DIR, 'panos'))
    ap.add_argument('--preview', action='store_true', help='also render a rectilinear preview at the node yaw')
    ap.add_argument('--preview-only', action='store_true')
    ap.add_argument('--preview-width', type=int, default=1600)
    ap.add_argument('--fov', type=float, default=90.0)
    ap.add_argument('--yaw', type=float, default=None, help='override preview yaw (radians)')
    ap.add_argument('--exposure', default='auto')
    ap.add_argument('--look', default='AgX - Base Contrast')
    ap.add_argument('--wb', default='auto', help="'auto' or '<kelvin>[,<tint>]'")
    ap.add_argument('--interior-gain', type=float, default=None, help='scale all fixtures (default lighting.INTERIOR_GAIN)')
    ap.add_argument('--sky-gain', type=float, default=None)
    ap.add_argument('--sun-gain', type=float, default=None)
    ap.add_argument('--emission-gain', type=float, default=None)
    ap.add_argument('--pins', default=None,
                    help='JSON {id: {ev, kelvin, tint}} (smooth_exposure.py): per-stop exposure / white balance; '
                         'wins over the automatic values, WB_NODE, --exposure and --wb')
    ap.add_argument('--skip-existing', '--resume', dest='skip_existing', action='store_true',
                    help='skip stops whose image and metadata already exist with the same width, samples and pins')
    ap.add_argument('--png16', action='store_true', help='write 16-bit RGB PNG (default 8-bit RGB)')
    ap.add_argument('--png-compression', type=int, default=15, help='PNG compression 0-100 (Blender default 15)')
    ap.add_argument('--probe-only', action='store_true',
                    help='mask + probe only: write render_meta.json, render no image at all')
    ap.add_argument('--adaptive-threshold', type=float, default=0.008)
    ap.add_argument('--adaptive-min', type=int, default=64)
    ap.add_argument('--no-adaptive', action='store_true')
    ap.add_argument('--tile-size', type=int, default=None,
                    help='Cycles tile size in px (default: Cycles auto tiling, 2048); 0 = render the frame as one tile')
    return ap.parse_args(argv)


def setup_cycles(samples, adaptive_threshold=0.008, adaptive_min=64, adaptive=True, tile_size=None):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    cy = sc.cycles
    cy.device = 'GPU'
    cy.samples = samples
    cy.use_adaptive_sampling = bool(adaptive)
    cy.adaptive_threshold = adaptive_threshold
    cy.adaptive_min_samples = adaptive_min
    # Large frames (8192x4096) render in tiles that are cached to disk and denoised as one frame at the
    # end, which keeps GPU memory flat (measured: see README). tile_size None keeps Cycles' default.
    if tile_size is not None:
        cy.use_auto_tile = tile_size > 0
        if tile_size > 0:
            cy.tile_size = int(tile_size)
    cy.use_denoising = True
    for den in ('OPENIMAGEDENOISE', 'OPTIX'):
        try:
            cy.denoiser = den
            break
        except TypeError:
            continue
    try:
        cy.denoising_use_gpu = True
        cy.denoising_prefilter = 'ACCURATE'
        cy.denoising_quality = 'HIGH'
    except AttributeError:
        pass
    cy.use_light_tree = True
    cy.max_bounces = 16
    cy.diffuse_bounces = 8
    cy.glossy_bounces = 6
    cy.transmission_bounces = 16
    cy.transparent_max_bounces = 16
    cy.sample_clamp_direct = 0.0
    cy.sample_clamp_indirect = 12.0
    cy.blur_glossy = 0.6
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    sc.render.film_transparent = False
    sc.render.use_persistent_data = True
    sc.view_settings.view_transform = 'AgX'
    sc.render.image_settings.color_depth = '8'
    # Neutralize the blue daylight cast like a real-estate photographer would (mixed light).
    vs = sc.view_settings
    try:
        vs.use_white_balance = True
        vs.white_balance_temperature, vs.white_balance_tint = WB_DEFAULT
    except AttributeError:
        pass


def set_look(look):
    vs = bpy.context.scene.view_settings
    try:
        vs.look = look
    except TypeError:
        try:
            vs.look = 'None'
        except TypeError:
            pass


def make_camera():
    cam = bpy.data.objects.get('TG PanoCam')
    if cam is None:
        cd = bpy.data.cameras.new('TG PanoCam')
        cam = bpy.data.objects.new('TG PanoCam', cd)
        bpy.context.scene.collection.objects.link(cam)
    cam.data.clip_start = 0.02
    cam.data.clip_end = 500
    bpy.context.scene.camera = cam
    return cam


def as_pano(cam):
    cd = cam.data
    cd.type = 'PANO'
    try:
        cd.panorama_type = 'EQUIRECTANGULAR'
    except (AttributeError, TypeError):
        cd.cycles.panorama_type = 'EQUIRECTANGULAR'
    cam.rotation_euler = (math.radians(90), 0, 0)


def as_persp(cam, yaw, pitch, fov_deg):
    cd = cam.data
    cd.type = 'PERSP'
    cd.sensor_fit = 'HORIZONTAL'
    cd.angle = math.radians(fov_deg)
    d = Vector((math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)))
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render_to(path, w, h, tries=3):
    """Render the scene camera to `path`; retries (e.g. a transient GPU out-of-memory on a shared GPU)."""
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.filepath = path
    for k in range(tries):
        if os.path.exists(path):
            os.remove(path)
        try:
            bpy.ops.render.render(write_still=True)
        except RuntimeError as e:
            print(f'[render] attempt {k + 1} failed: {e}', flush=True)
        if os.path.exists(path):
            return
        time.sleep(5 * (k + 1))
    raise RuntimeError(f'render failed after {tries} attempts: {path}')


def set_wb(temperature, tint):
    vs = bpy.context.scene.view_settings
    vs.use_white_balance = True
    vs.white_balance_temperature = float(temperature)
    vs.white_balance_tint = float(tint)


def png_output(bits16=False, compression=15):
    """Final images: PNG, RGB, 8-bit unless asked. Must be called right before the final render: the mask and
    the probe switch the file format to EXR, and switching back to PNG alone leaves the depth at 16 bit
    (and the colour mode at RGBA), which is how the panoramas used to come out as 16-bit RGBA."""
    st = bpy.context.scene.render.image_settings
    st.file_format = 'PNG'
    st.color_mode = 'RGB'
    st.color_depth = '16' if bits16 else '8'
    st.compression = max(0, min(100, int(compression)))


def png_info(path):
    """(width, height, bit depth, colour type) from a PNG header, or None if `path` is not a readable PNG."""
    import struct
    try:
        with open(path, 'rb') as f:
            head = f.read(26)
    except OSError:
        return None
    if len(head) < 26 or head[:8] != b'\x89PNG\r\n\x1a\n' or head[12:16] != b'IHDR':
        return None
    w, h, depth, ctype = struct.unpack('>IIBB', head[16:26])
    return w, h, depth, ctype


def load_pins(path):
    """{id: {'ev': stops | None, 'wb': (kelvin, tint | None) | None}} from a pins file
    {id: {ev, kelvin, tint}} (every key optional; 'exposure' / 'wb': [K, tint] are accepted too)."""
    if not path:
        return {}
    raw = json.load(open(path))
    raw = raw.get('pins', raw) if isinstance(raw.get('pins', None), dict) else raw
    pins = {}
    for nid, v in raw.items():
        if not isinstance(v, dict):
            continue
        ev = v.get('ev', v.get('exposure'))
        kelvin, tint = v.get('kelvin'), v.get('tint')
        if kelvin is None and isinstance(v.get('wb'), (list, tuple)) and v['wb']:
            kelvin = v['wb'][0]
            tint = v['wb'][1] if len(v['wb']) > 1 else tint
        if ev is None and kelvin is None:
            continue
        pins[nid] = {'ev': None if ev is None else float(ev),
                     'wb': None if kelvin is None else (float(kelvin), None if tint is None else float(tint))}
    return pins


def house_look(meta, ids=None):
    """(exposure, (kelvin, tint)) for the whole house: the upper medians of the per-stop values in a
    render_meta.json. `ids` (the tour's sweep ids) keeps stale entries of removed stops out of it.
    Shared by bake_web.py and adapt_web.py so the bake and its adaptation can never disagree."""
    rows = [v for k, v in meta.items() if isinstance(v, dict) and 'exposure' in v and (not ids or k in ids)]
    if not rows:
        rows = [v for v in meta.values() if isinstance(v, dict) and 'exposure' in v]

    def med(vals, default):
        vals = sorted(vals)
        return vals[len(vals) // 2] if vals else default
    return (med([v['exposure'] for v in rows], 0.5),
            (med([v['wb'][0] for v in rows if v.get('wb')], 6000.0), med([v['wb'][1] for v in rows if v.get('wb')], 0.0)))


def _write_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, path)


def _read_exr(path):
    """{pass name: HxWxC float array} from a multilayer EXR (channels '<layer>.<pass>.<chan>')."""
    import numpy as np
    import OpenImageIO as oiio
    inp = oiio.ImageInput.open(path)
    spec = inp.spec()
    data = np.asarray(inp.read_image(0, 0, 0, spec.nchannels, oiio.FLOAT)).reshape(spec.height, spec.width, spec.nchannels)
    inp.close()
    out = {}
    for i, name in enumerate(spec.channelnames):
        parts = name.split('.')
        key = parts[-2] if len(parts) >= 2 else 'Combined'
        out.setdefault(key, []).append(i)
    return {k: data[:, :, idx] for k, idx in out.items()}


def _display_ratios(rgb, tmpdir):
    """Display-referred (R/G, B/G) of a scene-linear colour (scaled to mid grey) under the current
    view settings: rendered through Blender's own colour pipeline so it matches the final PNGs."""
    import numpy as np
    import OpenImageIO as oiio
    sc = bpy.context.scene
    img = bpy.data.images.get('_tg_wb') or bpy.data.images.new('_tg_wb', 4, 4, float_buffer=True, alpha=False)
    try:
        img.colorspace_settings.name = 'Linear Rec.709'
    except TypeError:
        pass
    c = np.asarray(rgb, dtype=np.float64)
    c = c * (0.30 / max(1e-6, float(c @ [0.2126, 0.7152, 0.0722])))
    img.pixels.foreach_set(np.tile(np.r_[c, 1.0], 16).astype(np.float32))
    st = sc.render.image_settings
    vs = sc.view_settings
    keep = (st.file_format, st.color_depth, vs.exposure)
    st.file_format, st.color_depth, vs.exposure = 'PNG', '16', 0.0
    path = os.path.join(tmpdir, '_tg_wb.png')
    img.save_render(path, scene=sc)
    st.file_format, st.color_depth, vs.exposure = keep
    inp = oiio.ImageInput.open(path)
    px = np.asarray(inp.read_image(0, 0, 0, 3, oiio.FLOAT)).reshape(-1, 3).mean(0)
    inp.close()
    return px[0] / px[1], px[2] / px[1]


def solve_wb(rgb, tmpdir):
    """(temperature, tint) that brings the scene-linear colour `rgb` (lit white paint) to WB_TARGET."""
    import math as m
    (t_lo, t_hi), (n_lo, n_hi) = WB_LIMITS
    t_rg, t_bg = WB_TARGET
    g_target = 2.0 / (t_rg + t_bg)                       # G / mean(R, B)
    T, tint = WB_DEFAULT

    def green(Tv, nv):
        set_wb(Tv, nv)
        rg, bg = _display_ratios(rgb, tmpdir)
        return 2.0 / (rg + bg), bg
    # direction of the tint axis (Blender: +tint = magenta compensation, but measure it)
    tint_up = green(T, n_hi)[0] < green(T, n_lo)[0]          # True: raising tint lowers green
    for _ in range(3):
        lo, hi = m.log(t_lo), m.log(t_hi)                    # higher temperature -> warmer image
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            if green(m.exp(mid), tint)[1] > t_bg:
                lo = mid
            else:
                hi = mid
        T = m.exp(0.5 * (lo + hi))
        lo, hi = n_lo, n_hi
        for _ in range(12):
            mid = 0.5 * (lo + hi)
            too_green = green(T, mid)[0] > g_target
            if too_green == tint_up:
                lo = mid
            else:
                hi = mid
        tint = 0.5 * (lo + hi)
    set_wb(T, tint)
    return T, tint


def white_masks(cam, points, tmpdir, w=512, h=256):
    """{key: HxW bool} of pixels showing white painted surfaces (WB_MATERIALS) from each eye point.
    Every material's surface is temporarily swapped for a flat emission (white for WB_MATERIALS,
    black otherwise) with lights and sky off: one shader swap for all points, then restored."""
    import numpy as np
    sc = bpy.context.scene
    swapped, hidden = [], []
    for m in bpy.data.materials:
        if not m.use_nodes or not m.node_tree:
            continue
        nt = m.node_tree
        out = nt.get_output_node('CYCLES')
        if out is None:
            continue
        sock = out.inputs['Surface']
        old = sock.links[0].from_socket if sock.is_linked else None
        disp = out.inputs.get('Displacement')
        old_disp = disp.links[0].from_socket if disp is not None and disp.is_linked else None
        if old_disp is not None:
            nt.links.remove(disp.links[0])
        em = nt.nodes.new('ShaderNodeEmission')
        v = 1.0 if m.name in WB_MATERIALS else 0.0
        em.inputs['Color'].default_value = (v, v, v, 1.0)
        em.inputs['Strength'].default_value = 1.0
        nt.links.new(em.outputs[0], sock)
        swapped.append((nt, em, sock, old, disp, old_disp))
    for ob in bpy.data.objects:
        if ob.type == 'LIGHT' and not ob.hide_render:
            ob.hide_render = True
            hidden.append(ob)
    world = sc.world
    keep_bg = []
    if world is not None:
        bgs = [n for n in world.node_tree.nodes if n.type == 'BACKGROUND'] if world.use_nodes else []
        keep_bg = [(n, n.inputs['Strength'].default_value) for n in bgs]
        for n in bgs:
            n.inputs['Strength'].default_value = 0.0
    st = sc.render.image_settings
    keep = (sc.cycles.samples, sc.cycles.use_denoising, st.file_format, sc.cycles.use_adaptive_sampling)
    sc.cycles.samples, sc.cycles.use_denoising, sc.cycles.use_adaptive_sampling = 2, False, False
    st.file_format = 'OPEN_EXR'
    masks = {}
    try:
        for key, loc in points.items():
            cam.location = loc
            as_pano(cam)
            path = os.path.join(tmpdir, f'_mask_{key}.exr')
            render_to(path, w, h)
            img = _read_exr(path)['Combined']
            os.remove(path)
            masks[key] = img[:, :, 1] > 0.5
    finally:
        for nt, em, sock, old, disp, old_disp in swapped:
            nt.nodes.remove(em)
            if old is not None:
                nt.links.new(old, sock)
            if old_disp is not None:
                nt.links.new(old_disp, disp)
        for ob in hidden:
            ob.hide_render = False
        if world is not None:
            for n, v in keep_bg:
                n.inputs['Strength'].default_value = v
        (sc.cycles.samples, sc.cycles.use_denoising, st.file_format, sc.cycles.use_adaptive_sampling) = keep
    return masks


def probe(cam, node_id, tmpdir, mask=None):
    """Low-sample probe render. Returns (exposure stops mapping the median luminance of the horizon
    band to TARGET_MEDIAN, white balance (temperature, tint) or None, info dict). `mask` (from
    white_masks) marks the white painted pixels the white balance is measured on."""
    import numpy as np
    sc = bpy.context.scene
    st = sc.render.image_settings
    keep = (sc.cycles.samples, st.file_format, sc.cycles.use_denoising, sc.view_settings.exposure)
    sc.cycles.samples = 24
    sc.cycles.use_denoising = True
    sc.view_settings.exposure = 0.0
    st.file_format = 'OPEN_EXR'
    path = os.path.join(tmpdir, f'_probe_{node_id}.exr')
    render_to(path, 512, 256)
    rgb = _read_exr(path)['Combined'][:, :, :3]
    os.remove(path)
    (sc.cycles.samples, st.file_format, sc.cycles.use_denoising, sc.view_settings.exposure) = keep
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    h = lum.shape[0]
    med = max(float(np.median(lum[int(h * 0.30):int(h * 0.62), ::2])), 1e-5)
    ev = max(-4.0, min(6.0, math.log2(TARGET_MEDIAN / med)))
    info = {'median': round(med, 5)}
    wb = None
    if mask is not None and mask.shape == lum.shape:
        m = mask & (lum > 1e-5)
        info['white_px'] = int(m.sum())
        if m.sum() >= 400:
            # per-pixel chromaticity, median over the typical (mid-luminance) white pixels: weighting by
            # pixel count, not brightness, keeps hot pools under downlights from steering the balance
            sel = lum[m]
            lo, hi = np.percentile(sel, [20, 85])
            use = m & (lum >= lo) & (lum <= hi)
            px = rgb[use]
            g = np.maximum(px[:, 1], 1e-6)
            chroma = np.array([np.median(px[:, 0] / g), 1.0, np.median(px[:, 2] / g)])
            info['white_rgb'] = [round(float(v), 4) for v in chroma]
            wb = solve_wb(chroma, tmpdir)
    return ev, wb, info


def auto_exposure(cam, node_id, tmpdir):
    """Exposure only (older callers)."""
    return probe(cam, node_id, tmpdir)[0]


def scene_stamp():
    """[file name, modification time] of the open .blend: a render of an older build is never taken for done."""
    path = bpy.data.filepath
    return [os.path.basename(path), int(os.path.getmtime(path))] if path and os.path.exists(path) else None


def _done(n, a, meta, pin):
    """(True, '') when stop `n` needs no work under --skip-existing, else (False, reason)."""
    nid = n['id']
    e = meta.get(nid)
    if not isinstance(e, dict) or 'exposure' not in e:
        return False, 'no metadata'
    if e.get('blend') != scene_stamp():
        return False, 'the scene file changed since it was rendered'
    if a.probe_only:
        return True, ''
    if a.preview_only:
        return (True, '') if png_info(os.path.join(a.out, f'{nid}_view.png')) else (False, 'no preview image')
    info = png_info(os.path.join(a.out, f'{nid}.png'))
    if info is None:
        return False, 'no image'
    if e.get('image') is False:
        return False, 'metadata is from a probe pass'
    if info[0] != a.width or info[1] != a.width // 2 or e.get('width') != a.width:
        return False, f'image is {info[0]}x{info[1]}'
    if e.get('samples') != a.samples:
        return False, f"rendered with {e.get('samples')} samples"
    if info[2] != (16 if a.png16 else 8):
        return False, f'image is {info[2]}-bit'
    if pin:
        if pin['ev'] is not None and abs(e['exposure'] - pin['ev']) > 0.004:
            return False, 'pinned exposure changed'
        if pin['wb'] is not None:
            wb = e.get('wb') or (0, 0)
            if abs(wb[0] - pin['wb'][0]) > 1.0 or (pin['wb'][1] is not None and abs(wb[1] - pin['wb'][1]) > 0.06):
                return False, 'pinned white balance changed'
    elif e.get('pinned'):
        return False, 'was rendered with pins'
    return True, ''


def main():
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    scene = json.load(open(os.path.join(DATA_DIR, 'scene.json')))
    nodes = scene['tour']['nodes']
    if a.nodes != 'all':
        want = a.nodes.split(',')
        missing = [w for w in want if w not in {n['id'] for n in nodes}]
        if missing:
            print(f'[render] WARNING unknown stop ids: {", ".join(missing)}', flush=True)
        nodes = [n for n in nodes if n['id'] in want]
    pins = load_pins(a.pins)
    if a.pins:
        unpinned = [n['id'] for n in nodes if n['id'] not in pins]
        print(f'[render] pins: {len(pins)} stops from {a.pins}'
              + (f'; NOT pinned (automatic values): {", ".join(unpinned)}' if unpinned else ''), flush=True)
    meta_path = os.path.join(a.out, 'render_meta.json')
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    if a.skip_existing:
        todo = []
        for n in nodes:
            ok, why = _done(n, a, meta, pins.get(n['id']))
            if ok:
                print(f'[render] {n["id"]} skipped (exists)', flush=True)
            else:
                if why not in ('no metadata', 'no image', 'no preview image'):
                    print(f'[render] {n["id"]} redo: {why}', flush=True)
                todo.append(n)
        print(f'[render] resume: {len(nodes) - len(todo)} of {len(nodes)} stops already done', flush=True)
        nodes = todo
    if not nodes:
        print('[render] nothing to do', flush=True)
        return
    setup_cycles(a.samples, a.adaptive_threshold, a.adaptive_min, not a.no_adaptive, a.tile_size)
    set_look(a.look)
    from bl import lighting
    lighting.apply_balance(a.interior_gain, a.sky_gain, a.sun_gain, a.emission_gain)
    fixed_wb = None
    if a.wb != 'auto':
        v = [float(x) for x in a.wb.split(',')]
        fixed_wb = (v[0], v[1] if len(v) > 1 else WB_DEFAULT[1])
    cam = make_camera()
    sc = bpy.context.scene
    # the white mask feeds the probe's white balance; it is skipped only when no stop can use it
    need_mask = [n for n in nodes if fixed_wb is None or n['id'] in pins]
    masks = white_masks(cam, {n['id']: ft2bl(*n['p']) for n in need_mask}, a.out) if need_mask else {}
    t_all = time.time()
    for k, n in enumerate(nodes):
        t0 = time.time()
        nid = n['id']
        x, y, z = n['p']
        cam.location = ft2bl(x, y, z)
        as_pano(cam)
        sc.render.image_settings.file_format = 'PNG'
        ev_auto, wb_auto, info = probe(cam, nid, a.out, masks.get(nid))
        pin = pins.get(nid) or {'ev': None, 'wb': None}
        ev = ev_auto if a.exposure == 'auto' else float(a.exposure)
        if fixed_wb:
            wb, src = fixed_wb, 'fixed'
        elif nid in WB_NODE:
            wb, src = WB_NODE[nid], 'node'
        elif wb_auto:
            wb, src = wb_auto, 'probe'
        else:
            wb, src = WB_DEFAULT, 'default'
        if pin['ev'] is not None:
            ev = pin['ev']
        if pin['wb'] is not None:
            wb, src = (pin['wb'][0], pin['wb'][1] if pin['wb'][1] is not None else wb[1]), 'pin'
        set_wb(*wb)
        sc.view_settings.exposure = ev
        t_probe = time.time() - t0
        t1 = time.time()
        image = not (a.preview_only or a.probe_only)
        if image:
            png_output(a.png16, a.png_compression)
            part = os.path.join(a.out, f'_part_{nid}.png')
            render_to(part, a.width, a.width // 2)
            os.replace(part, os.path.join(a.out, f'{nid}.png'))     # an <ID>.png is always a complete render
        if (a.preview or a.preview_only) and not a.probe_only:
            yaw = a.yaw if a.yaw is not None else n.get('yaw', 0.0)
            as_persp(cam, yaw, n.get('pitch', 0.0), a.fov)
            png_output(False, a.png_compression)
            render_to(os.path.join(a.out, f'{nid}_view.png'), a.preview_width, int(a.preview_width * 0.625))
            as_pano(cam)
        meta[nid] = {'exposure': ev, 'wb': [round(wb[0]), round(wb[1], 1)], 'probe': info,
                     'auto': {'exposure': round(ev_auto, 4),
                              'wb': [round(wb_auto[0]), round(wb_auto[1], 1)] if wb_auto else None},
                     'wb_source': src, 'pinned': pin['ev'] is not None or pin['wb'] is not None, 'image': image,
                     'seconds': round(time.time() - t0, 1), 'probe_s': round(t_probe, 1),
                     'render_s': round(time.time() - t1, 1), 'width': a.width, 'samples': a.samples,
                     'bits': 16 if a.png16 else 8, 'blend': scene_stamp(),
                     'adaptive': [bool(sc.cycles.use_adaptive_sampling), round(sc.cycles.adaptive_threshold, 5),
                                  sc.cycles.adaptive_min_samples]}
        _write_json(meta_path, meta)
        left = (time.time() - t_all) / (k + 1) * (len(nodes) - k - 1)
        print(f'[render] {nid} ev={ev:+.2f} wb={wb[0]:.0f}K/{wb[1]:+.1f}'
              + (f' (pinned; auto ev={ev_auto:+.2f}' + (f' wb={wb_auto[0]:.0f}K/{wb_auto[1]:+.1f})' if wb_auto else ')')
                 if meta[nid]['pinned'] else '')
              + f' {time.time() - t0:.1f}s  [{k + 1}/{len(nodes)}, about {left / 60:.0f} min left]', flush=True)


if __name__ == '__main__':
    main()
